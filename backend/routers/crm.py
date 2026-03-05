"""CRM Extraction Router – Pull data from a client's existing CRM into aLiGN."""

import json
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.account import Account, AccountType, Contact

logger = logging.getLogger("align.crm")

router = APIRouter(prefix="/crm", tags=["CRM Extraction"])

# HubSpot API base
_HS_BASE = "https://api.hubapi.com"
_HS_PAGE_SIZE = 100

# ── Helpers ───────────────────────────────────────────────────────────────────

_INDUSTRY_TYPE_MAP: list[tuple[set[str], AccountType]] = [
    ({"data center", "data centre", "colocation", "colo", "hosting"}, AccountType.operator),
    ({"hyperscaler", "cloud provider", "cloud computing", "aws", "azure", "gcp"}, AccountType.hyperscaler),
    ({"real estate", "property developer", "developer"}, AccountType.developer),
    ({"colocation"}, AccountType.colo),
]


def _map_account_type(industry: str) -> AccountType:
    """Map a HubSpot industry string to the nearest AccountType enum value."""
    lower = (industry or "").lower()
    for keywords, account_type in _INDUSTRY_TYPE_MAP:
        if any(kw in lower for kw in keywords):
            return account_type
    return AccountType.enterprise


def _hs_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}


async def _hs_get(client: httpx.AsyncClient, url: str, token: str, **params: Any) -> dict:
    """GET a HubSpot endpoint and surface a clean error on failure."""
    resp = await client.get(url, headers=_hs_headers(token), params=params)
    if resp.status_code == 401:
        raise HTTPException(401, "Invalid HubSpot access token")
    if not resp.is_success:
        raise HTTPException(502, f"HubSpot API error {resp.status_code}: {resp.text[:200]}")
    return resp.json()


# ── HubSpot import ─────────────────────────────────────────────────────────────

@router.post(
    "/hubspot/import",
    status_code=status.HTTP_200_OK,
    summary="Import Accounts + Contacts from a client's HubSpot CRM",
)
async def import_from_hubspot(
    authorization: str = Header(
        ...,
        description="HubSpot private-app access token, e.g. 'Bearer pat-na1-…'",
        alias="Authorization",
    ),
    db: Session = Depends(get_db),
):
    """Pull HubSpot Companies → Accounts and HubSpot Contacts → Contacts.

    Pass the HubSpot private-app access token in the standard `Authorization`
    header as `Bearer <token>`.  The endpoint pages through all records and
    skips anything that already exists (matched by name for accounts, email for
    contacts).

    Returns a summary of how many records were created vs skipped.
    """
    # Strip "Bearer " prefix if present
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, "Authorization header is required")

    imported_accounts = 0
    skipped_accounts = 0
    imported_contacts = 0
    skipped_contacts = 0

    # Map HubSpot company ID → local Account ID for contact association
    hs_id_to_account: dict[str, int] = {}

    # Pre-load existing names and emails for O(1) duplicate checks during import
    existing_account_names: set[str] = {
        row[0].lower() for row in db.query(Account.name).all()
    }
    existing_contact_emails: set[str] = {
        row[0] for row in db.query(Contact.email).filter(Contact.email.isnot(None)).all()
    }

    async with httpx.AsyncClient(timeout=30.0) as client:

        # ── 1. Pull Companies (paginated) ─────────────────────────────────
        props = "name,industry,city,country,website,description,phone,annualrevenue"
        after: str | None = None

        while True:
            params: dict[str, Any] = {"limit": _HS_PAGE_SIZE, "properties": props}
            if after:
                params["after"] = after

            data = await _hs_get(client, f"{_HS_BASE}/crm/v3/objects/companies", token, **params)

            for company in data.get("results", []):
                hs_company_id: str = company.get("id", "")
                p = company.get("properties", {})
                name = (p.get("name") or "").strip()
                if not name:
                    skipped_accounts += 1
                    continue

                if name.lower() in existing_account_names:
                    # Try to map the HubSpot ID to the existing local account
                    existing = db.query(Account).filter(Account.name.ilike(name)).first()
                    if existing:
                        hs_id_to_account[hs_company_id] = existing.id
                    skipped_accounts += 1
                    continue

                revenue_raw = p.get("annualrevenue")
                try:
                    annual_revenue: float | None = float(revenue_raw) if revenue_raw else None
                except (TypeError, ValueError):
                    annual_revenue = None

                account = Account(
                    name=name[:255],
                    type=_map_account_type(p.get("industry", "")),
                    stage="Target",
                    location=(
                        ", ".join(filter(None, [p.get("city"), p.get("country")]))[:255] or None
                    ),
                    website=(p.get("website") or None),
                    annual_revenue=annual_revenue,
                    notes=(p.get("description") or None),
                    tags="hubspot-import",
                )
                db.add(account)
                db.flush()  # get account.id before commit

                hs_id_to_account[hs_company_id] = account.id
                imported_accounts += 1

            paging = data.get("paging", {})
            after = paging.get("next", {}).get("after")
            if not after:
                break

        # ── 2. Pull Contacts (paginated) ──────────────────────────────────
        contact_props = "firstname,lastname,email,phone,jobtitle,associatedcompanyid"
        after = None

        while True:
            params = {"limit": _HS_PAGE_SIZE, "properties": contact_props}
            if after:
                params["after"] = after

            data = await _hs_get(client, f"{_HS_BASE}/crm/v3/objects/contacts", token, **params)

            for contact_obj in data.get("results", []):
                hs_contact_id: str = contact_obj.get("id", "")
                p = contact_obj.get("properties", {})

                first = (p.get("firstname") or "").strip()
                last = (p.get("lastname") or "").strip()
                full_name = " ".join(filter(None, [first, last])).strip()
                email = (p.get("email") or "").strip() or None

                if not full_name:
                    skipped_contacts += 1
                    continue

                # Skip if a contact with this email already exists (O(1) set lookup)
                if email and email in existing_contact_emails:
                    skipped_contacts += 1
                    continue

                # Associate with local Account via HubSpot associations API
                # Look up company association via HubSpot's associations API
                account_id: int | None = None
                try:
                    assoc = await _hs_get(
                        client,
                        f"{_HS_BASE}/crm/v3/objects/contacts/{hs_contact_id}/associations/companies",
                        token,
                    )
                    for result in assoc.get("results", []):
                                cid = str(result.get("id", ""))
                                if cid in hs_id_to_account:
                                    account_id = hs_id_to_account[cid]
                                    break
                except HTTPException:
                    pass

                if account_id is None:
                    skipped_contacts += 1
                    continue

                contact = Contact(
                    account_id=account_id,
                    name=full_name[:255],
                    role=(p.get("jobtitle") or None),
                    email=email,
                    phone=(p.get("phone") or None),
                )
                db.add(contact)
                imported_contacts += 1

            paging = data.get("paging", {})
            after = paging.get("next", {}).get("after")
            if not after:
                break

        db.commit()

    logger.info(
        "HubSpot import complete – accounts: %d created / %d skipped; "
        "contacts: %d created / %d skipped",
        imported_accounts, skipped_accounts, imported_contacts, skipped_contacts,
    )

    return {
        "status": "success",
        "imported_accounts": imported_accounts,
        "skipped_accounts": skipped_accounts,
        "imported_contacts": imported_contacts,
        "skipped_contacts": skipped_contacts,
        "message": (
            f"HubSpot import complete: {imported_accounts} accounts and "
            f"{imported_contacts} contacts added."
        ),
    }

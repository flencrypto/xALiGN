"""Website Swoop – one-shot company URL → full Account record.

POST /api/v1/accounts/swoop
  Body: { "url": "https://company.com" }

Crawls the URL, sends content to Grok for structured extraction, then
upserts a full Account record (with Contacts and TriggerSignals).

Requires XAI_API_KEY to be configured.
"""

import json
import logging
from typing import Any

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.account import (
    Account,
    AccountType,
    Contact,
    InfluenceLevel,
    TriggerSignal,
    SignalType,
)
from backend.schemas.account import AccountRead
from backend.services import grok_client
from backend.services.crawler import _validate_url, _normalise_url
from backend.services.integration_requirements import ensure_integration_configured

logger = logging.getLogger("align.swoop")

router = APIRouter(prefix="/accounts", tags=["Website Swoop"])

# ---------------------------------------------------------------------------
# Type mapping – Grok may return various strings; normalise to our enum
# ---------------------------------------------------------------------------

_TYPE_MAP: dict[str, AccountType] = {
    "hyperscale": AccountType.hyperscaler,
    "hyperscaler": AccountType.hyperscaler,
    "operator": AccountType.operator,
    "colocation": AccountType.colo,
    "colo": AccountType.colo,
    "developer": AccountType.developer,
    "enterprise": AccountType.enterprise,
    "contractor": AccountType.operator,  # closest match
    "other": AccountType.operator,
}

_CRAWL_TIMEOUT = 15.0
_CRAWL_HEADERS = {
    "User-Agent": "aLiGN-Swoop/1.0 (institutional research; contact admin@align.com)",
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.5",
}

# Signal type best-effort mapping from trigger keyword patterns
_SIGNAL_KEYWORDS: list[tuple[list[str], SignalType]] = [
    (["fund", "invest", "rais", "capital", "£", "$", "€"], SignalType.planning),
    (["acqui", "merger", "merge", "buy", "purchase"], SignalType.land_acquisition),
    (["hire", "hiring", "recruit", "cto", "ceo", "appoint"], SignalType.hiring_spike),
    (["framework", "award", "tender", "contract", "win"], SignalType.framework_award),
    (["grid", "power", "energy", "electric", "substation"], SignalType.grid),
    (["planning", "permit", "site", "build", "expand", "launch", "rollout"], SignalType.planning),
    (["road", "access", "infra"], SignalType.roadworks),
]


def _guess_signal_type(text: str) -> SignalType:
    lower = text.lower()
    for keywords, sig_type in _SIGNAL_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return sig_type
    return SignalType.planning


# ---------------------------------------------------------------------------
# HTML fetch + text extraction
# ---------------------------------------------------------------------------

async def _fetch_page(url: str) -> tuple[str, str]:
    """
    Fetch a URL and return (title, plain_text).

    Uses BeautifulSoup for cleaner extraction than regex stripping.
    SSRF protection is enforced via _validate_url before the request is made.
    """
    import re as _re

    # Re-validate inside _fetch_page to guard against any future callers that
    # bypass the endpoint-level check (defence in depth).
    _validate_url(url)

    async with httpx.AsyncClient(
        timeout=_CRAWL_TIMEOUT,
        headers=_CRAWL_HEADERS,
        follow_redirects=False,  # Do not follow redirects to avoid SSRF via redirects
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove script / style noise
    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # Prefer main content areas for better signal density
    content_tags = soup.find_all(["main", "article", "section", "div"], limit=20)
    if content_tags:
        text = " ".join(t.get_text(separator=" ", strip=True) for t in content_tags)
    else:
        text = soup.get_text(separator=" ", strip=True)

    text = _re.sub(r"\s{2,}", " ", text).strip()

    return title, text[:8000]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

class SwoopRequest(BaseModel):
    url: str = Field(..., description="Company website URL to swoop (https://...)")


class SwoopResponse(BaseModel):
    status: str
    account_id: int
    created: bool
    intel: dict[str, Any]


@router.post(
    "/swoop",
    response_model=SwoopResponse,
    status_code=status.HTTP_200_OK,
    summary="Website Swoop – crawl a URL and auto-fill a full Account record",
)
async def website_swoop(payload: SwoopRequest, db: Session = Depends(get_db)):
    """
    Enter any company website URL. Grok crawls the page and extracts:
    company name, type, location, key personnel (with LinkedIn / X handles),
    recent news, stock ticker, trigger signals, an intel summary, and a
    suggested LinkedIn touchpoint.

    The result is immediately upserted as a full Account record with
    linked Contacts and TriggerSignals.

    Requires **XAI_API_KEY** to be configured.
    """
    ensure_integration_configured(
        integration_id="grok_ai",
        integration_name="Grok AI",
        required_env_vars=["XAI_API_KEY"],
        setup_path="/setup#grok_ai",
    )

    url = payload.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # SSRF guard
    try:
        _validate_url(url)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # 1. Crawl
    try:
        page_title, page_text = await _fetch_page(url)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not fetch {url}: HTTP {exc.response.status_code}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not fetch {url}: {exc}",
        )

    if not page_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Page returned no readable content.",
        )

    # 2. Grok extraction
    intel = await grok_client.swoop_company(url, page_title, page_text)

    # 3. Map fields
    raw_type = str(intel.get("type") or "operator").strip().lower()
    account_type = _TYPE_MAP.get(raw_type, AccountType.operator)

    company_name: str = (intel.get("company_name") or page_title or "Unknown").strip()

    # Build structured notes from all intel
    notes_parts: list[str] = []
    if intel.get("intel_summary"):
        notes_parts.append(f"INTEL SUMMARY: {intel['intel_summary']}")
    if intel.get("suggested_touchpoint"):
        notes_parts.append(f"SUGGESTED TOUCHPOINT: {intel['suggested_touchpoint']}")
    if intel.get("recent_news"):
        news_list = intel["recent_news"]
        if isinstance(news_list, list):
            notes_parts.append("RECENT NEWS:\n" + "\n".join(f"• {n}" for n in news_list))
    if intel.get("stock_ticker"):
        notes_parts.append(f"STOCK: {intel['stock_ticker']}")
    notes = "\n\n".join(notes_parts) or None

    # Tags – combine Grok tags + website-swoop marker
    raw_tags: list[str] = intel.get("tags") or []
    if isinstance(raw_tags, str):
        raw_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
    tag_set = {t.lower() for t in raw_tags} | {"website-swoop"}
    tags_str = ", ".join(sorted(tag_set)) or None

    # 4. Upsert Account (match on name)
    existing = db.query(Account).filter(Account.name == company_name).first()
    created = existing is None

    if existing:
        acc = existing
        acc.type = account_type
        acc.stage = acc.stage or "Target"
        acc.location = intel.get("location") or acc.location
        acc.website = url
        acc.tags = tags_str
        acc.notes = notes
        # clear old children so we replace with fresh data
        db.query(Contact).filter(Contact.account_id == acc.id).delete()
        db.query(TriggerSignal).filter(TriggerSignal.account_id == acc.id).delete()
    else:
        acc = Account(
            name=company_name,
            type=account_type,
            stage="Target",
            location=intel.get("location"),
            website=url,
            tags=tags_str,
            notes=notes,
        )
        db.add(acc)
        db.flush()

    # 5. Key personnel → Contacts
    for person in (intel.get("key_personnel") or []):
        if not isinstance(person, dict):
            continue
        name = (person.get("name") or "").strip()
        if not name:
            continue
        linkedin = person.get("linkedin") or None
        x_handle = person.get("x_handle") or None
        parts: list[str] = []
        if linkedin:
            parts.append(f"LinkedIn: {linkedin}")
        if x_handle:
            parts.append(f"X: {x_handle}")
        contact_notes = "  ".join(parts) or None
        db.add(Contact(
            account_id=acc.id,
            name=name,
            role=(person.get("role") or None),
            influence_level=InfluenceLevel.decision_maker,
            notes=contact_notes.strip() or None,
        ))

    # 6. Trigger signals
    for trigger_text in (intel.get("triggers") or []):
        if not isinstance(trigger_text, str) or not trigger_text.strip():
            continue
        db.add(TriggerSignal(
            account_id=acc.id,
            signal_type=_guess_signal_type(trigger_text),
            title=trigger_text[:255],
            description=trigger_text,
        ))

    db.commit()
    db.refresh(acc)

    return SwoopResponse(
        status="success",
        account_id=acc.id,
        created=created,
        intel=intel,
    )

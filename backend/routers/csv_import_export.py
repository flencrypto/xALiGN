"""CSV import and export endpoints for company (account) data.

Endpoints:
  GET  /api/v1/accounts/export/csv    – Export all accounts as a CSV download
  GET  /api/v1/accounts/template/csv  – Download a blank CSV template
  POST /api/v1/accounts/import/csv    – Bulk-import accounts from an uploaded CSV
"""

import csv
import io
import logging
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.account import Account, AccountType

logger = logging.getLogger("align.csv")

router = APIRouter(prefix="/accounts", tags=["Accounts CSV"])

# Canonical column order for the CSV (export and template)
CSV_COLUMNS = [
    "id",
    "name",
    "type",
    "stage",
    "location",
    "website",
    "logo_url",
    "tags",
    "annual_revenue",
    "tier_target",
    "notes",
    "created_at",
    "updated_at",
]

# Columns required when importing (id / timestamps are ignored on import)
IMPORT_COLUMNS = [
    "name",
    "type",
    "stage",
    "location",
    "website",
    "logo_url",
    "tags",
    "annual_revenue",
    "tier_target",
    "notes",
]

VALID_TYPES = {t.value for t in AccountType}


def _account_to_row(acc: Account) -> dict[str, Any]:
    """Convert an Account ORM object to a flat dict for CSV serialisation."""
    return {
        "id": acc.id,
        "name": acc.name,
        "type": acc.type.value if acc.type else "",
        "stage": acc.stage or "",
        "location": acc.location or "",
        "website": acc.website or "",
        "logo_url": acc.logo_url or "",
        "tags": acc.tags or "",
        "annual_revenue": acc.annual_revenue if acc.annual_revenue is not None else "",
        "tier_target": acc.tier_target or "",
        "notes": acc.notes or "",
        "created_at": acc.created_at.isoformat() if acc.created_at else "",
        "updated_at": acc.updated_at.isoformat() if acc.updated_at else "",
    }


# ── Export ────────────────────────────────────────────────────────────────────

@router.get(
    "/export/csv",
    summary="Export all accounts to CSV",
    response_class=StreamingResponse,
)
def export_accounts_csv(db: Session = Depends(get_db)):
    """Stream all accounts as a UTF-8 CSV file."""
    accounts = db.query(Account).order_by(Account.name).all()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for acc in accounts:
        writer.writerow(_account_to_row(acc))

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=accounts_export.csv"},
    )


# ── Template ──────────────────────────────────────────────────────────────────

@router.get(
    "/template/csv",
    summary="Download a blank CSV import template",
    response_class=StreamingResponse,
)
def download_accounts_template():
    """Return a CSV file with headers and one example row showing the expected format."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=IMPORT_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    # Example row so users know what format is expected
    writer.writerow({
        "name": "Example Corp Ltd",
        "type": "operator",
        "stage": "Target",
        "location": "London, UK",
        "website": "https://example.com",
        "logo_url": "https://example.com/logo.png",
        "tags": "ai, expansion, 2025",
        "annual_revenue": "50000000",
        "tier_target": "Tier 1",
        "notes": "Key target account for Q3. Intel: expanding AI estate. Next action: call CEO.",
    })
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=accounts_import_template.csv"},
    )


# ── Import ────────────────────────────────────────────────────────────────────

class ImportResult:
    def __init__(self):
        self.created: int = 0
        self.skipped: int = 0
        self.errors: list[str] = []


@router.post(
    "/import/csv",
    summary="Bulk-import accounts from a CSV file",
    status_code=status.HTTP_200_OK,
)
async def import_accounts_csv(
    file: UploadFile = File(..., description="CSV file matching the import template"),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV file to bulk-create account records.

    - Rows with a missing or empty **name** or **type** are skipped.
    - **type** must be one of: operator, hyperscaler, developer, colo, enterprise.
    - Duplicate names are allowed (the system does not deduplicate automatically).
    - Returns a summary of created, skipped, and error rows.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only .csv files are accepted.",
        )

    raw = await file.read()
    try:
        content = raw.decode("utf-8-sig")  # strip BOM if present
    except UnicodeDecodeError:
        content = raw.decode("latin-1", errors="replace")

    reader = csv.DictReader(io.StringIO(content))

    result = ImportResult()

    for line_num, row in enumerate(reader, start=2):  # line 1 is the header
        name = (row.get("name") or "").strip()
        account_type_raw = (row.get("type") or "").strip().lower()

        if not name:
            result.skipped += 1
            result.errors.append(f"Row {line_num}: 'name' is required — skipped.")
            continue

        if account_type_raw not in VALID_TYPES:
            result.skipped += 1
            result.errors.append(
                f"Row {line_num}: invalid type {account_type_raw!r}. "
                f"Must be one of {sorted(VALID_TYPES)} — skipped."
            )
            continue

        # Parse optional numeric field safely
        annual_revenue: float | None = None
        raw_rev = (row.get("annual_revenue") or "").strip()
        if raw_rev:
            try:
                annual_revenue = float(raw_rev.replace(",", ""))
            except ValueError:
                result.errors.append(
                    f"Row {line_num}: invalid annual_revenue {raw_rev!r} — "
                    "field will be left empty."
                )

        acc = Account(
            name=name,
            type=AccountType(account_type_raw),
            stage=(row.get("stage") or "").strip() or None,
            location=(row.get("location") or "").strip() or None,
            website=(row.get("website") or "").strip() or None,
            logo_url=(row.get("logo_url") or "").strip() or None,
            tags=(row.get("tags") or "").strip() or None,
            annual_revenue=annual_revenue,
            tier_target=(row.get("tier_target") or "").strip() or None,
            notes=(row.get("notes") or "").strip() or None,
        )
        db.add(acc)
        result.created += 1

    db.commit()
    logger.info("CSV import complete: %d created, %d skipped", result.created, result.skipped)

    return {
        "created": result.created,
        "skipped": result.skipped,
        "errors": result.errors,
        "message": f"Import complete. {result.created} account(s) created, {result.skipped} row(s) skipped.",
    }

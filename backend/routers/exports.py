"""Export router – generates downloadable documents for bids.

Endpoints:
  GET /api/v1/bids/{bid_id}/export/pursuit-pack-pdf    – Pursuit Pack PDF
  GET /api/v1/bids/{bid_id}/export/tender-response-docx – Tender Response Word
  GET /api/v1/bids/{bid_id}/export/compliance-matrix-xlsx – Compliance Matrix Excel
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.bid import Bid, BidDocument, ComplianceItem, RFI
from backend.models.opportunity import Opportunity
from backend.services import export_service

logger = logging.getLogger("align.exports")

router = APIRouter(prefix="/bids", tags=["Exports"])


def _get_bid_or_404(bid_id: int, db: Session) -> Bid:
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    return bid


@router.get(
    "/{bid_id}/export/pursuit-pack-pdf",
    summary="Export Pursuit Pack as PDF",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
def export_pursuit_pack_pdf(bid_id: int, db: Session = Depends(get_db)):
    """Generate and download a Pursuit Pack PDF for the given bid."""
    bid = _get_bid_or_404(bid_id, db)
    opportunity = db.get(Opportunity, bid.opportunity_id)
    compliance_items = (
        db.query(ComplianceItem).filter(ComplianceItem.bid_id == bid_id).all()
    )
    try:
        pdf_bytes = export_service.build_pursuit_pack_pdf(opportunity, bid, compliance_items)
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc))
    safe_title = "".join(c if c.isalnum() else "_" for c in (bid.title or "bid"))[:40]
    filename = f"pursuit_pack_{safe_title}_{bid_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{bid_id}/export/tender-response-docx",
    summary="Export Tender Response Pack as Word document",
    response_class=Response,
    responses={200: {"content": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document": {}}}},
)
def export_tender_response_docx(bid_id: int, db: Session = Depends(get_db)):
    """Generate and download a Tender Response Pack .docx for the given bid."""
    bid = _get_bid_or_404(bid_id, db)
    compliance_items = (
        db.query(ComplianceItem).filter(ComplianceItem.bid_id == bid_id).all()
    )
    rfis = db.query(RFI).filter(RFI.bid_id == bid_id).all()
    try:
        docx_bytes = export_service.build_tender_response_pack_docx(bid, compliance_items, rfis)
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc))
    safe_title = "".join(c if c.isalnum() else "_" for c in (bid.title or "bid"))[:40]
    filename = f"tender_response_{safe_title}_{bid_id}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{bid_id}/export/compliance-matrix-xlsx",
    summary="Export Compliance Matrix as Excel workbook",
    response_class=Response,
    responses={200: {"content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}}}},
)
def export_compliance_matrix_xlsx(bid_id: int, db: Session = Depends(get_db)):
    """Generate and download a Compliance Matrix .xlsx for the given bid."""
    bid = _get_bid_or_404(bid_id, db)
    compliance_items = (
        db.query(ComplianceItem).filter(ComplianceItem.bid_id == bid_id).all()
    )
    try:
        xlsx_bytes = export_service.build_compliance_matrix_xlsx(bid, compliance_items)
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc))
    safe_title = "".join(c if c.isalnum() else "_" for c in (bid.title or "bid"))[:40]
    filename = f"compliance_matrix_{safe_title}_{bid_id}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

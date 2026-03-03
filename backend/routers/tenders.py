"""Tender Awards router.

Endpoints:
  POST /api/v1/tenders                           – Add a tender award
  GET  /api/v1/tenders                           – List tender awards
  GET  /api/v1/tenders/{id}                      – Get a tender award
  PATCH /api/v1/tenders/{id}                     – Update a tender award
  DELETE /api/v1/tenders/{id}                    – Delete a tender award
  GET  /api/v1/tenders/{id}/pricing-model        – Compute CPI for an award
  GET  /api/v1/tenders/company/{company_intel_id} – Awards for a company
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.intel import TenderAward
from backend.schemas.intel import TenderAwardCreate, TenderAwardRead, TenderAwardUpdate
from backend.services import scoring

logger = logging.getLogger("contractghost.tenders")

router = APIRouter(prefix="/tenders", tags=["Tender Awards"])


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=TenderAwardRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a public tender award",
)
def create_tender_award(payload: TenderAwardCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    # Compute price_per_mw if contract_value and capacity_mw are provided
    if data.get("contract_value") and data.get("capacity_mw"):
        data["price_per_mw"] = scoring.price_per_mw(data["contract_value"], data["capacity_mw"])
    obj = TenderAward(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=list[TenderAwardRead], summary="List tender awards")
def list_tender_awards(
    winning_company: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(TenderAward).order_by(TenderAward.created_at.desc())
    if winning_company:
        q = q.filter(TenderAward.winning_company.ilike(f"%{winning_company}%"))
    return q.offset(skip).limit(limit).all()


@router.get(
    "/company/{company_intel_id}",
    response_model=list[TenderAwardRead],
    summary="List tender awards for a specific company intel record",
)
def list_awards_for_company(
    company_intel_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return (
        db.query(TenderAward)
        .filter(TenderAward.company_intel_id == company_intel_id)
        .order_by(TenderAward.award_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{tender_id}", response_model=TenderAwardRead, summary="Get a tender award")
def get_tender_award(tender_id: int, db: Session = Depends(get_db)):
    obj = db.get(TenderAward, tender_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Tender award not found")
    return obj


@router.patch("/{tender_id}", response_model=TenderAwardRead, summary="Update a tender award")
def update_tender_award(tender_id: int, payload: TenderAwardUpdate, db: Session = Depends(get_db)):
    obj = db.get(TenderAward, tender_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Tender award not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    # Recompute price_per_mw if relevant fields changed
    if obj.contract_value and obj.capacity_mw:
        obj.price_per_mw = scoring.price_per_mw(obj.contract_value, obj.capacity_mw)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/{tender_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tender award",
)
def delete_tender_award(tender_id: int, db: Session = Depends(get_db)):
    obj = db.get(TenderAward, tender_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Tender award not found")
    db.delete(obj)
    db.commit()


# ── Pricing Model ─────────────────────────────────────────────────────────────

@router.get(
    "/{tender_id}/pricing-model",
    summary="Compute Competitive Pricing Index for a tender award",
)
def pricing_model(
    tender_id: int,
    market_mean_ppmw: float = 1_000_000.0,
    market_std_ppmw: float = 150_000.0,
    db: Session = Depends(get_db),
):
    """Compute the CPI z-score for this award relative to market benchmarks.

    Provide market_mean_ppmw and market_std_ppmw as query parameters to
    calibrate the benchmark.  **WARNING**: the default values (£1M mean,
    £150K std) are illustrative only and are not based on real market data.
    Always supply calibrated benchmarks from your own tender database for
    production use.
    """
    obj = db.get(TenderAward, tender_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Tender award not found")
    if not obj.price_per_mw:
        raise HTTPException(
            status_code=422,
            detail="price_per_mw is not set on this award. Provide contract_value and capacity_mw.",
        )
    cpi = scoring.competitive_pricing_index(obj.price_per_mw, market_mean_ppmw, market_std_ppmw)
    return {
        "tender_id": tender_id,
        "winning_company": obj.winning_company,
        "contract_value": obj.contract_value,
        "capacity_mw": obj.capacity_mw,
        "price_per_mw": obj.price_per_mw,
        "market_mean_ppmw": market_mean_ppmw,
        "market_std_ppmw": market_std_ppmw,
        "cpi_z_score": cpi,
        "pricing_label": (
            "premium" if (cpi or 0) > 0.5
            else "aggressive" if (cpi or 0) < -0.5
            else "market-rate"
        ),
    }

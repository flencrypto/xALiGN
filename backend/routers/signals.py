"""Signal Events router.

Endpoints:
  POST /api/v1/signals                            – Add a signal event
  GET  /api/v1/signals                            – List signal events
  GET  /api/v1/signals/{id}                       – Get a signal event
  PATCH /api/v1/signals/{id}                      – Update a signal event
  DELETE /api/v1/signals/{id}                     – Delete a signal event
  GET  /api/v1/signals/company/{company_intel_id} – Signals for a company
  POST /api/v1/signals/relationship/suggest       – Relationship timing score + outreach recommendation
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.intel import SignalEvent
from backend.schemas.intel import (
    RelationshipTimingResponse,
    SignalEventCreate,
    SignalEventRead,
    SignalEventUpdate,
)
from backend.services import scoring

logger = logging.getLogger("contractghost.signals")

router = APIRouter(prefix="/signals", tags=["Signal Events"])


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=SignalEventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a signal event",
)
def create_signal_event(payload: SignalEventCreate, db: Session = Depends(get_db)):
    obj = SignalEvent(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=list[SignalEventRead], summary="List signal events")
def list_signal_events(
    signal_type: str | None = None,
    company_name: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(SignalEvent).order_by(SignalEvent.event_date.desc())
    if signal_type:
        q = q.filter(SignalEvent.signal_type == signal_type)
    if company_name:
        q = q.filter(SignalEvent.company_name.ilike(f"%{company_name}%"))
    return q.offset(skip).limit(limit).all()


@router.get(
    "/company/{company_intel_id}",
    response_model=list[SignalEventRead],
    summary="List signals for a specific company intel record",
)
def list_signals_for_company(
    company_intel_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return (
        db.query(SignalEvent)
        .filter(SignalEvent.company_intel_id == company_intel_id)
        .order_by(SignalEvent.event_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{signal_id}", response_model=SignalEventRead, summary="Get a signal event")
def get_signal_event(signal_id: int, db: Session = Depends(get_db)):
    obj = db.get(SignalEvent, signal_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Signal event not found")
    return obj


@router.patch("/{signal_id}", response_model=SignalEventRead, summary="Update a signal event")
def update_signal_event(signal_id: int, payload: SignalEventUpdate, db: Session = Depends(get_db)):
    obj = db.get(SignalEvent, signal_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Signal event not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/{signal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a signal event",
)
def delete_signal_event(signal_id: int, db: Session = Depends(get_db)):
    obj = db.get(SignalEvent, signal_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Signal event not found")
    db.delete(obj)
    db.commit()


# ── Relationship Timing Engine ────────────────────────────────────────────────

@router.post(
    "/relationship/suggest",
    response_model=RelationshipTimingResponse,
    summary="Compute relationship timing score and outreach recommendation",
)
def relationship_suggest(
    company_intel_id: int,
    db: Session = Depends(get_db),
):
    """Aggregate all signal events for a company and return a timing-scored
    outreach recommendation using the exponential-decay model.

    Weight_i = strength_i × e^(−λ_i × days_since_event_i)
    TotalScore = Σ Weight_i
    """
    signals = (
        db.query(SignalEvent)
        .filter(SignalEvent.company_intel_id == company_intel_id)
        .order_by(SignalEvent.event_date.desc())
        .all()
    )
    if not signals:
        raise HTTPException(
            status_code=404,
            detail="No signal events found for this company.",
        )

    signal_dicts = [
        {
            "strength": s.strength,
            "decay_factor": s.decay_factor,
            "event_date": s.event_date,
        }
        for s in signals
    ]

    total_score = scoring.relationship_timing_score(signal_dicts)
    recommendation = scoring.outreach_recommendation(total_score)

    # Derive context brief from top recent signal types
    top_signals = signals[:3]
    top_types = ", ".join(dict.fromkeys(s.signal_type for s in top_signals))
    company_name = signals[0].company_name if signals else None

    # Conversation angle based on dominant signal type
    dominant_type = signals[0].signal_type if signals else "general"
    angle_map = {
        "expansion": "Reference their geographic expansion plans and how your capabilities align.",
        "funding": "Acknowledge the funding milestone and discuss how you can accelerate delivery.",
        "hiring": "Note the hiring surge as a signal of growth — position yourself as a delivery partner.",
        "contract_win": "Congratulate on the contract award and explore delivery support opportunities.",
        "conference": "Reference their recent panel/keynote topic as the opening for dialogue.",
        "earnings": "Open with their positive earnings signal and discuss future capital projects.",
    }
    conversation_angle = angle_map.get(
        dominant_type,
        "Reference their recent market activity and explore alignment opportunities.",
    )

    risk_flags = []
    if total_score < 0.5:
        risk_flags.append("Low signal activity — risk of cold outreach, wait for a stronger trigger.")
    if any(s.signal_type == "risk" for s in signals):
        risk_flags.append("Risk-type signal detected — approach with caution.")

    return RelationshipTimingResponse(
        company_name=company_name,
        total_score=total_score,
        recommendation=recommendation,
        context_brief=f"Recent triggers: {top_types}. Timing score: {total_score:.2f}.",
        conversation_angle=conversation_angle,
        risk_flags=risk_flags,
        top_signals=[SignalEventRead.model_validate(s) for s in top_signals],
    )

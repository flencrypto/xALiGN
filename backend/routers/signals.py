"""Signal Events router.

Endpoints:
  POST   /api/v1/signals                        – Create a signal event
  GET    /api/v1/signals                        – List signal events (filterable)
  GET    /api/v1/signals/{id}                   – Get a single signal event
  PATCH  /api/v1/signals/{id}                   – Update a signal event
  DELETE /api/v1/signals/{id}                   – Delete a signal event
  POST   /api/v1/signals/score/expansion        – Compute Expansion Activity Score
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.intel import SignalEvent, SignalEventStatus, SignalEventType
from backend.schemas.signals import (
    ExpansionScoreRequest,
    ExpansionScoreResult,
    SignalEventCreate,
    SignalEventRead,
    SignalEventUpdate,
)
from backend.services import scoring

logger = logging.getLogger("align.signals")

router = APIRouter(prefix="/signals", tags=["Signal Events"])


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=SignalEventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a signal event",
)
def create_signal_event(payload: SignalEventCreate, db: Session = Depends(get_db)):
    """Ingest a new commercial or relationship signal event."""
    obj = SignalEvent(
        company_name=payload.company_name,
        account_id=payload.account_id,
        event_type=payload.event_type,
        title=payload.title,
        description=payload.description,
        source_url=payload.source_url,
        relevance_score=payload.relevance_score,
        status=payload.status,
        event_date=payload.event_date,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    logger.info("Signal event created – ID %s (%s)", obj.id, obj.event_type)
    return obj


@router.get(
    "",
    response_model=list[SignalEventRead],
    summary="List signal events",
)
def list_signal_events(
    company_name: str | None = None,
    account_id: int | None = None,
    event_type: SignalEventType | None = None,
    status: SignalEventStatus | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Return signal events with optional filters."""
    q = db.query(SignalEvent).order_by(SignalEvent.detected_at.desc())
    if company_name:
        q = q.filter(SignalEvent.company_name.ilike(f"%{company_name}%"))
    if account_id is not None:
        q = q.filter(SignalEvent.account_id == account_id)
    if event_type is not None:
        q = q.filter(SignalEvent.event_type == event_type)
    if status is not None:
        q = q.filter(SignalEvent.status == status)
    return q.offset(skip).limit(limit).all()


@router.get(
    "/{signal_id}",
    response_model=SignalEventRead,
    summary="Get a single signal event",
)
def get_signal_event(signal_id: int, db: Session = Depends(get_db)):
    obj = db.get(SignalEvent, signal_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Signal event not found")
    return obj


@router.patch(
    "/{signal_id}",
    response_model=SignalEventRead,
    summary="Update a signal event",
)
def update_signal_event(
    signal_id: int,
    payload: SignalEventUpdate,
    db: Session = Depends(get_db),
):
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
    logger.info("Signal event deleted – ID %s", signal_id)


# ── Scoring ───────────────────────────────────────────────────────────────────

@router.post(
    "/score/expansion",
    response_model=ExpansionScoreResult,
    summary="Compute Expansion Activity Score",
)
def compute_expansion_score(payload: ExpansionScoreRequest):
    """
    Compute the Expansion Activity Score (EAS) in [0, 1].

    EAS = 0.50 * signal_score + 0.25 * hiring_score + 0.25 * physical_score
    """
    result = scoring.compute_expansion_activity_score(
        signal_events=payload.signal_events,
        days_since_events=payload.days_since_events,
        hiring_count=payload.hiring_count,
        new_office_openings=payload.new_office_openings,
        recent_acquisitions=payload.recent_acquisitions,
    )

    breakdown = {
        "signal_contribution": result["signal_contribution"],
        "hiring_contribution": result["hiring_contribution"],
        "physical_contribution": result["physical_contribution"],
    }

    return ExpansionScoreResult(expansion_activity_score=result["score"], breakdown=breakdown)

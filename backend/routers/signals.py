"""Signal Events router.

Endpoints:
  POST   /api/v1/signals                        – Create a signal event
  GET    /api/v1/signals                        – List signal events (filterable)
  POST   /api/v1/signals/relationship/suggest   – Relationship timing suggestion
  GET    /api/v1/signals/{id}                   – Get a single signal event
  PATCH  /api/v1/signals/{id}                   – Update a signal event
  DELETE /api/v1/signals/{id}                   – Delete a signal event
  POST   /api/v1/signals/score/expansion        – Compute Expansion Activity Score
"""

import logging
import math

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.intel import SignalEvent, SignalEventStatus, SignalEventType
from backend.schemas.signals import (
    ExpansionScoreRequest,
    ExpansionScoreResult,
    RelationshipTimingResponse,
    SignalEventCreate,
    SignalEventRead,
    SignalEventUpdate,
)
from backend.services import scoring
from backend.services.scoring import (
    SIGNAL_DECAY as _SIGNAL_DECAY,
    SIGNAL_IMPORTANCE as _SIGNAL_IMPORTANCE,
)

logger = logging.getLogger("align.signals")

router = APIRouter(prefix="/signals", tags=["Signal Events"])

_STALE_THRESHOLD = 0.30  # timing score below which a signal is considered stale


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
        strength=payload.strength,
        decay_factor=payload.decay_factor,
        company_intel_id=payload.company_intel_id,
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


# ── Relationship Timing ───────────────────────────────────────────────────────

class RelationshipSuggestRequest(BaseModel):
    signal_events: list[str] = Field(default_factory=list)
    days_since_events: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_lists(self) -> "RelationshipSuggestRequest":
        if len(self.signal_events) != len(self.days_since_events):
            raise ValueError("signal_events and days_since_events must have same length")
        if any(d < 0 for d in self.days_since_events):
            raise ValueError("days_since_events values must be non-negative")
        return self


@router.post("/relationship/suggest", response_model=RelationshipTimingResponse)
def suggest_relationship_timing(payload: RelationshipSuggestRequest):
    # Compute per-event raw contributions (decay × importance) once, reuse below
    per_event: list[tuple[str, float, float]] = []  # (event_name, lam, raw_weight)
    total_score_raw = 0.0
    for event, days in zip(payload.signal_events, payload.days_since_events):
        lam = _SIGNAL_DECAY.get(event, 0.05)
        importance = _SIGNAL_IMPORTANCE.get(event, 0.5)
        w = math.exp(-lam * days) * importance
        per_event.append((event, lam, w))
        total_score_raw += w

    # Normalised timing score (matches compute_relationship_timing's /3.0 cap)
    normalised = min(total_score_raw / 3.0, 1.0)
    result = {
        "timing_score": round(normalised, 4),
        "recommend_contact": normalised >= _STALE_THRESHOLD,
    }

    # Strongest signal: event with the highest individual weighted contribution
    strongest: str | None = None
    if per_event:
        strongest = max(per_event, key=lambda t: t[2])[0]

    # Days until score decays below _STALE_THRESHOLD using effective λ (contribution-weighted).
    # total_score_raw(d) ≈ total_score_raw * exp(-λ_eff * d)
    # Solve: total_score_raw * exp(-λ_eff * d) / 3.0 = _STALE_THRESHOLD
    #   → d = -ln(_STALE_THRESHOLD * 3.0 / total_score_raw) / λ_eff
    days_until_stale: int | None = None
    threshold_raw = _STALE_THRESHOLD * 3.0
    if total_score_raw > threshold_raw and per_event:
        lambda_eff = sum(lam * w for _, lam, w in per_event) / total_score_raw
        if lambda_eff > 0:
            days_until_stale = max(0, int(-math.log(threshold_raw / total_score_raw) / lambda_eff))

    explanation = (
        "Contact recommended based on recent signal activity."
        if result["recommend_contact"]
        else "No urgent outreach needed; signals are decaying."
    )
    return RelationshipTimingResponse(
        timing_score=result["timing_score"],
        recommend_contact=result["recommend_contact"],
        strongest_signal=strongest,
        days_until_stale=days_until_stale,
        explanation=explanation,
    )


# ── CRUD (by ID) ──────────────────────────────────────────────────────────────

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

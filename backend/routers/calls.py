"""Call Intelligence router.

Endpoints:
  POST /api/v1/calls/analyse   – Submit transcript text for analysis
  GET  /api/v1/calls           – List call intelligence records
  GET  /api/v1/calls/{id}      – Get a single call intelligence record
  DELETE /api/v1/calls/{id}    – Delete a call record
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.tender import CallIntelligence
from backend.schemas.tender import CallIntelligenceCreate, CallIntelligenceRead
from backend.services.transcription import analyse_transcript

logger = logging.getLogger("contractghost.calls")

router = APIRouter(prefix="/calls", tags=["Call Intelligence"])


def _load_list(value: str | None) -> list[str] | None:
    if value is None:
        return None
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(i) for i in parsed]
    except (json.JSONDecodeError, TypeError):
        pass
    return [value] if value else None


def _call_to_read(obj: CallIntelligence) -> CallIntelligenceRead:
    return CallIntelligenceRead(
        id=obj.id,
        company_name=obj.company_name,
        executive_name=obj.executive_name,
        transcript=obj.transcript,
        sentiment_score=obj.sentiment_score,
        competitor_mentions=_load_list(obj.competitor_mentions),
        budget_signals=_load_list(obj.budget_signals),
        timeline_mentions=_load_list(obj.timeline_mentions),
        risk_language=_load_list(obj.risk_language),
        objection_categories=_load_list(obj.objection_categories),
        next_steps=obj.next_steps,
        created_at=obj.created_at,
    )


@router.post(
    "/analyse",
    response_model=CallIntelligenceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a call transcript for AI analysis",
)
async def analyse_call(payload: CallIntelligenceCreate, db: Session = Depends(get_db)):
    """
    Analyse a call transcript using Grok AI to extract structured signals:
    sentiment, competitor mentions, budget signals, timeline mentions,
    risk language, objection categories, and next steps.

    Requires XAI_API_KEY for AI-powered extraction. Without it, the transcript
    is stored with empty signal fields.
    """
    if not payload.transcript:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="transcript is required for analysis",
        )

    signals = await analyse_transcript(payload.transcript)

    obj = CallIntelligence(
        company_name=payload.company_name,
        executive_name=payload.executive_name,
        transcript=payload.transcript,
        sentiment_score=signals.get("sentiment_score"),
        competitor_mentions=json.dumps(signals.get("competitor_mentions") or []),
        budget_signals=json.dumps(signals.get("budget_signals") or []),
        timeline_mentions=json.dumps(signals.get("timeline_mentions") or []),
        risk_language=json.dumps(signals.get("risk_language") or []),
        objection_categories=json.dumps(signals.get("objection_categories") or []),
        next_steps=signals.get("next_steps"),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _call_to_read(obj)


@router.get(
    "",
    response_model=list[CallIntelligenceRead],
    summary="List call intelligence records",
)
def list_calls(
    company_name: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(CallIntelligence).order_by(CallIntelligence.created_at.desc())
    if company_name:
        q = q.filter(CallIntelligence.company_name.ilike(f"%{company_name}%"))
    return [_call_to_read(obj) for obj in q.offset(skip).limit(limit).all()]


@router.get(
    "/{call_id}",
    response_model=CallIntelligenceRead,
    summary="Get a single call intelligence record",
)
def get_call(call_id: int, db: Session = Depends(get_db)):
    obj = db.get(CallIntelligence, call_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Call intelligence record not found")
    return _call_to_read(obj)


@router.delete(
    "/{call_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a call intelligence record",
)
def delete_call(call_id: int, db: Session = Depends(get_db)):
    obj = db.get(CallIntelligence, call_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Call intelligence record not found")
    db.delete(obj)
    db.commit()

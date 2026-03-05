"""Call Intelligence router – now with direct audio upload + Grok transcription + analysis."""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.tender import CallIntelligence
from backend.schemas.tender import CallIntelligenceCreate, CallIntelligenceRead
from backend.services.ai_workers import CallIntelWorker
from backend.core.config import settings

logger = logging.getLogger("align.calls")

router = APIRouter(prefix="/calls", tags=["Call Intelligence"])

_call_intel_worker = CallIntelWorker()

# Supported audio formats
_AUDIO_ALLOWED_TYPES = {
    "audio/mpeg", "audio/mp3",
    "audio/wav",
    "audio/x-m4a", "audio/m4a",
    "audio/ogg",
}
_AUDIO_MAX_BYTES = 50 * 1024 * 1024  # 50 MB


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


def _serialise_next_steps(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return json.dumps(value)
    return str(value)


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


# ── ANALYSE (now accepts audio OR text) ───────────────────────────────────────
@router.post(
    "/analyse",
    response_model=CallIntelligenceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload audio OR paste transcript → Grok transcribes + analyses",
)
async def analyse_call(
    file: UploadFile | None = File(None),
    company_name: str | None = None,
    executive_name: str | None = None,
    transcript: str | None = None,   # fallback for text-only
    db: Session = Depends(get_db),
):
    """Upload audio file (mp3/wav/m4a) OR send transcript text.
    Grok transcribes audio automatically, then extracts sentiment, signals, next steps, etc."""
    
    # ── 1. Get transcript (audio or text) ─────────────────────────────────
    if file:
        if file.content_type not in _AUDIO_ALLOWED_TYPES:
            raise HTTPException(415, f"Unsupported audio type: {file.content_type}. Use mp3/wav/m4a.")

        audio_data = await file.read()
        if len(audio_data) > _AUDIO_MAX_BYTES:
            raise HTTPException(413, "Audio file too large (max 50 MB)")

        logger.info(f"Transcribing audio file: {file.filename} ({len(audio_data)/1024/1024:.1f} MB)")

        # Grok native audio transcription
        transcript_text = await _call_intel_worker.transcribe_audio(audio_data, file.filename)

    elif transcript and transcript.strip():
        transcript_text = transcript.strip()
    else:
        raise HTTPException(422, "Either upload an audio file OR provide transcript text")

    if not transcript_text:
        raise HTTPException(422, "Could not extract any transcript from the audio")

    # ── 2. Run full analysis ───────────────────────────────────────────────
    logger.info(f"Running Grok analysis on {len(transcript_text)} characters")
    signals = await _call_intel_worker.run(transcript_text)

    # ── 3. Save to database ───────────────────────────────────────────────
    obj = CallIntelligence(
        company_name=company_name,
        executive_name=executive_name,
        transcript=transcript_text,
        sentiment_score=signals.get("sentiment_score"),
        competitor_mentions=json.dumps(signals.get("competitor_mentions") or []),
        budget_signals=json.dumps(signals.get("budget_signals") or []),
        timeline_mentions=json.dumps(signals.get("timeline_mentions") or []),
        risk_language=json.dumps(signals.get("risk_flags") or signals.get("risk_language") or []),
        objection_categories=json.dumps(signals.get("objections") or signals.get("objection_categories") or []),
        next_steps=_serialise_next_steps(signals.get("recommended_next_steps")),
    )

    db.add(obj)
    db.commit()
    db.refresh(obj)

    logger.info(f"Call intelligence record created – ID {obj.id} (sentiment: {obj.sentiment_score})")
    return _call_to_read(obj)


# ── List, Get, Delete (unchanged but cleaned) ────────────────────────────────
@router.get("", response_model=list[CallIntelligenceRead])
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


@router.get("/{call_id}", response_model=CallIntelligenceRead)
def get_call(call_id: int, db: Session = Depends(get_db)):
    obj = db.get(CallIntelligence, call_id)
    if not obj:
        raise HTTPException(404, "Call intelligence record not found")
    return _call_to_read(obj)


@router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_call(call_id: int, db: Session = Depends(get_db)):
    obj = db.get(CallIntelligence, call_id)
    if not obj:
        raise HTTPException(404, "Call intelligence record not found")
    db.delete(obj)
    db.commit()
    logger.info(f"Deleted call intelligence record {call_id}")

"""Call Intelligence router.

Endpoints:
  POST /api/v1/calls                     – Create a call record (with optional transcript)
  POST /api/v1/calls/{id}/analyze        – Analyse transcript via Grok
  GET  /api/v1/calls                     – List call records
  GET  /api/v1/calls/{id}                – Get a call record
  DELETE /api/v1/calls/{id}              – Delete a call record
  GET  /api/v1/calls/company/{company_intel_id} – Calls for a company
"""

import json
import logging
import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.intel import CallIntelligence
from backend.schemas.intel import CallAnalyzeRequest, CallCreate, CallRead
from backend.services import grok_client

logger = logging.getLogger("contractghost.calls")

router = APIRouter(prefix="/calls", tags=["Call Intelligence"])

_UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads")) / "calls"
_MAX_AUDIO_SIZE = 100 * 1024 * 1024  # 100 MB
_ALLOWED_AUDIO_EXTS = {".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".webm"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialise(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return str(value)


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=CallRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a call intelligence record",
)
def create_call(payload: CallCreate, db: Session = Depends(get_db)):
    """Create a call record, optionally including a raw transcript for later analysis."""
    obj = CallIntelligence(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.post(
    "/upload",
    response_model=CallRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an audio file for a call record",
)
async def upload_call_audio(
    file: UploadFile = File(...),
    title: str = Form(...),
    company_intel_id: int | None = Form(None),
    executive_profile_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    """Upload an audio recording. File is stored locally; transcript can be submitted via /analyze."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in _ALLOWED_AUDIO_EXTS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported audio format. Allowed: {', '.join(_ALLOWED_AUDIO_EXTS)}",
        )

    content = await file.read()
    if len(content) > _MAX_AUDIO_SIZE:
        raise HTTPException(status_code=413, detail="Audio file exceeds 100 MB limit.")

    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = _UPLOAD_DIR / safe_name

    async with aiofiles.open(dest, "wb") as f:
        await f.write(content)

    obj = CallIntelligence(
        title=title,
        company_intel_id=company_intel_id,
        executive_profile_id=executive_profile_id,
        audio_filename=Path(file.filename or safe_name).name,
        audio_path=str(dest),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.post(
    "/{call_id}/analyze",
    response_model=CallRead,
    summary="Analyse a call transcript with Grok AI",
)
async def analyze_call(
    call_id: int,
    payload: CallAnalyzeRequest,
    db: Session = Depends(get_db),
):
    """Submit or update the transcript and run Grok analysis to extract:
    sentiment score, competitor mentions, budget signals, risk phrases,
    next steps, and a CRM-ready summary.
    """
    if not grok_client.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Grok AI is not configured. Set XAI_API_KEY in the environment.",
        )

    obj = db.get(CallIntelligence, call_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Call record not found")

    result = await grok_client.analyze_call_transcript(payload.transcript)

    obj.transcript = payload.transcript
    obj.sentiment_score = result.get("sentiment_score")
    obj.competitor_mentions = _serialise(result.get("competitor_mentions"))
    obj.budget_signals = _serialise(result.get("budget_signals"))
    obj.risk_phrases = _serialise(result.get("risk_phrases"))
    obj.next_steps = result.get("next_steps")
    obj.crm_summary = result.get("crm_summary")

    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=list[CallRead], summary="List call intelligence records")
def list_calls(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return (
        db.query(CallIntelligence)
        .order_by(CallIntelligence.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/company/{company_intel_id}",
    response_model=list[CallRead],
    summary="List calls for a company intel record",
)
def list_calls_for_company(
    company_intel_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return (
        db.query(CallIntelligence)
        .filter(CallIntelligence.company_intel_id == company_intel_id)
        .order_by(CallIntelligence.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{call_id}", response_model=CallRead, summary="Get a call intelligence record")
def get_call(call_id: int, db: Session = Depends(get_db)):
    obj = db.get(CallIntelligence, call_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Call record not found")
    return obj


@router.delete(
    "/{call_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a call intelligence record",
)
def delete_call(call_id: int, db: Session = Depends(get_db)):
    obj = db.get(CallIntelligence, call_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Call record not found")
    if obj.audio_path:
        audio_file = Path(obj.audio_path)
        if audio_file.exists():
            audio_file.unlink(missing_ok=True)
    db.delete(obj)
    db.commit()

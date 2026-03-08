"""Call Intelligence router – Audio/Text + Smart Key-Point Linking with fuzzy suggest."""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Body, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.account import Account, AccountType
from backend.models.opportunity import Opportunity, OpportunityStage
from backend.models.tender import CallIntelligence
from backend.schemas.tender import CallIntelligenceCreate, CallIntelligenceRead
from backend.services.ai_workers import CallIntelWorker

logger = logging.getLogger("align.calls")

router = APIRouter(prefix="/calls", tags=["Call Intelligence"])

_call_intel_worker = CallIntelWorker()

_AUDIO_ALLOWED_TYPES = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/x-m4a", "audio/m4a", "audio/ogg"}
_AUDIO_MAX_BYTES = 50 * 1024 * 1024  # 50 MB
_AUDIO_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads")) / "audio"


# ── Helpers ───────────────────────────────────────────────────────────────────

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
        account_id=obj.account_id,
        account_name=obj.account.name if obj.account else None,
        company_name=obj.company_name,
        executive_name=obj.executive_name,
        audio_file_url=obj.audio_file_url,
        call_date=obj.call_date,
        transcript=obj.transcript,
        sentiment_score=obj.sentiment_score,
        competitor_mentions=_load_list(obj.competitor_mentions),
        budget_signals=_load_list(obj.budget_signals),
        timeline_mentions=_load_list(obj.timeline_mentions),
        risk_language=_load_list(obj.risk_language),
        objection_categories=_load_list(obj.objection_categories),
        next_steps=obj.next_steps,
        key_points=json.loads(obj.key_points) if obj.key_points else [],
        created_at=obj.created_at,
    )


def _opportunity_confidence(opp: Opportunity, keyword: str, company: str) -> int:
    """Return a 0-100 confidence score for how well an Opportunity matches a key point.

    Scoring breakdown:
    - Title token overlap: up to 40 pts
    - Title sequence similarity: up to 20 pts
    - Company name match (account or description): up to 40 pts
    """
    score = 0

    # Title keyword overlap (token-based)
    kw_tokens = set(keyword.lower().split())
    title_tokens = set(opp.title.lower().split())
    if kw_tokens and title_tokens:
        overlap = len(kw_tokens & title_tokens) / len(kw_tokens)
        score += int(overlap * 40)

    # Sequence similarity between keyword and title (catches partial words)
    seq_ratio = SequenceMatcher(None, keyword.lower(), opp.title.lower()).ratio()
    score += int(seq_ratio * 20)

    # Company name match against linked account or description
    if company:
        company_lc = company.lower()
        account_name = (opp.account.name if opp.account else "").lower()
        desc = (opp.description or "").lower()
        if company_lc in account_name or account_name in company_lc:
            score += 40
        elif company_lc in desc:
            score += 20

    return min(score, 99)


def _match_reason(opp: Opportunity, keyword: str, company: str) -> str:
    reasons = []
    kw_tokens = set(keyword.lower().split())
    title_tokens = set(opp.title.lower().split())
    if kw_tokens & title_tokens:
        reasons.append("title keyword match")
    if company and opp.account and company.lower() in opp.account.name.lower():
        reasons.append("same company")
    elif company and company.lower() in (opp.description or "").lower():
        reasons.append("company in description")
    if not reasons:
        reasons.append("keyword similarity")
    return ", ".join(reasons)


# ── ANALYSE (audio OR text) + KEY POINTS EXTRACTION ───────────────────────────
@router.post(
    "/analyse",
    response_model=CallIntelligenceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload audio OR paste transcript → Grok transcribes, analyses + extracts key points",
)
async def analyse_call(
    file: UploadFile | None = File(None),
    company_name: str | None = Form(None),
    executive_name: str | None = Form(None),
    transcript: str | None = Form(None),
    account_id: int | None = Form(None),
    call_date: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """Full pipeline: audio transcription → Grok analysis → key points extraction → structured record."""

    # ── 1. Get transcript (audio or text) ─────────────────────────────────
    audio_file_url: str | None = None
    
    if file:
        if file.content_type not in _AUDIO_ALLOWED_TYPES:
            raise HTTPException(415, f"Unsupported audio type: {file.content_type}. Use mp3/wav/m4a.")
        audio_data = await file.read()
        if len(audio_data) > _AUDIO_MAX_BYTES:
            raise HTTPException(413, "Audio file too large (max 50 MB)")
        
        # Save audio file to disk
        _AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        ext = Path(file.filename or "call.mp3").suffix.lower()
        if ext not in {".mp3", ".wav", ".m4a", ".ogg"}:
            ext = ".mp3"
        safe_filename = f"{uuid.uuid4().hex}{ext}"
        dest = _AUDIO_DIR / safe_filename
        
        async with aiofiles.open(dest, "wb") as f:
            await f.write(audio_data)
        
        audio_file_url = f"/uploads/audio/{safe_filename}"
        
        logger.info(f"Transcribing audio file: {file.filename} ({len(audio_data)/1024/1024:.1f} MB)")
        transcript_text = await _call_intel_worker.transcribe_audio(audio_data, file.filename or "call")
    elif transcript and transcript.strip():
        transcript_text = transcript.strip()
    else:
        raise HTTPException(422, "Either upload an audio file OR provide transcript text")

    if not transcript_text:
        raise HTTPException(422, "Could not extract any transcript from the audio")

    # ── 2. Run full Grok analysis + key points extraction ─────────────────
    logger.info(f"Running Grok analysis on {len(transcript_text)} characters")
    signals = await _call_intel_worker.run(transcript_text)
    # Parse call_date if provided
    call_datetime: datetime | None = None
    if call_date:
        try:
            call_datetime = datetime.fromisoformat(call_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            logger.warning(f"Invalid call_date format: {call_date}")
    

    # ── 3. Save to database ───────────────────────────────────────────────
    obj = CallIntelligence(
        account_id=account_id,
        company_name=company_name,
        executive_name=executive_name,
        audio_file_url=audio_file_url,
        call_date=call_datetime,
        transcript=transcript_text,
        sentiment_score=signals.get("sentiment_score"),
        competitor_mentions=json.dumps(signals.get("competitor_mentions") or []),
        budget_signals=json.dumps(signals.get("budget_signals") or []),
        timeline_mentions=json.dumps(signals.get("timeline_mentions") or []),
        risk_language=json.dumps(signals.get("risk_flags") or signals.get("risk_language") or []),
        objection_categories=json.dumps(signals.get("objections") or signals.get("objection_categories") or []),
        next_steps=_serialise_next_steps(signals.get("recommended_next_steps")),
        key_points=json.dumps(signals.get("key_points") or []),
    )

    db.add(obj)
    db.commit()
    db.refresh(obj)

    kp_count = len(signals.get("key_points") or [])
    logger.info(f"Call record created – ID {obj.id} with {kp_count} key points")
    return _call_to_read(obj)


# ── SMART SUGGEST: fuzzy-match existing Opportunities for a key point ─────────
@router.get(
    "/{call_id}/key-points/{point_index}/suggest",
    summary="Get smart linking suggestions (fuzzy match on company + job title)",
)
def suggest_opportunity_links(
    call_id: int,
    point_index: int,
    db: Session = Depends(get_db),
):
    """Return the top-3 existing Opportunities that best match a key point, plus an
    auto-create payload pre-filled with the key point data.

    Confidence is a 0-99 integer computed from title-token overlap,
    sequence similarity, and company-name match.
    """
    call = db.get(CallIntelligence, call_id)
    if not call:
        raise HTTPException(404, "Call record not found")

    if point_index < 0:
        raise HTTPException(422, "point_index must be a non-negative integer")

    try:
        key_points: list[dict] = json.loads(call.key_points or "[]")
        point = key_points[point_index]
    except (IndexError, json.JSONDecodeError, TypeError):
        raise HTTPException(404, "Key point not found")

    if not isinstance(point, dict):
        raise HTTPException(422, f"Key point {point_index} is not a valid object (got {type(point).__name__})")

    keyword = (point.get("mentioned_job_title") or point.get("text") or "")[:80]
    company = point.get("mentioned_company") or call.company_name or ""

    # Escape SQL wildcards so user-provided text doesn't alter the LIKE pattern
    safe_keyword = keyword[:40].replace("%", r"\%").replace("_", r"\_")

    # Fetch candidates: filter by either title or description keyword match
    candidates = (
        db.query(Opportunity)
        .filter(
            Opportunity.title.ilike(f"%{safe_keyword}%", escape="\\")
            | Opportunity.description.ilike(f"%{safe_keyword}%", escape="\\")
        )
        .limit(20)
        .all()
    )

    # Score and rank candidates
    scored = sorted(
        [
            {
                "id": opp.id,
                "title": opp.title,
                "stage": opp.stage.value if hasattr(opp.stage, "value") else opp.stage,
                "account_name": opp.account.name if opp.account else None,
                "confidence": _opportunity_confidence(opp, keyword, company),
                "match_reason": _match_reason(opp, keyword, company),
            }
            for opp in candidates
        ],
        key=lambda x: x["confidence"],
        reverse=True,
    )[:3]

    context_quote = point.get("context") or point.get("text") or ""
    call_date = call.created_at.date().isoformat() if call.created_at else "unknown date"

    return {
        "key_point": point,
        "suggestions": scored,
        "auto_create_payload": {
            "title": keyword or "Discussed opportunity",
            "description": (
                f"Discussed by {call.executive_name or 'unknown'} in call on {call_date}.\n\n"
                f"Quote: {context_quote}"
            ),
            "stage": "target",
            "mentioned_company": company or None,
            "type": point.get("type", "general"),
        },
    }


# ── LINK OR CREATE FROM KEY POINT ─────────────────────────────────────────────
@router.post(
    "/{call_id}/key-points/{point_index}/link",
    response_model=CallIntelligenceRead,
    summary="Link to existing Opportunity or auto-create one from a key point",
)
async def link_key_point(
    call_id: int,
    point_index: int,
    opportunity_id: int | None = Query(None, description="ID of an existing Opportunity to link"),
    db: Session = Depends(get_db),
):
    """Link a key point to an existing Opportunity (pass `opportunity_id` query param)
    or auto-create one (omit it).

    Either way a full audit trail is written back to the key point:
    - who mentioned it (executive_name)
    - exact quote / context
    - date, action type (linked_existing | created_new)
    - type classification (job_discussion, competitor_mention, etc.)
    """
    call = db.get(CallIntelligence, call_id)
    if not call:
        raise HTTPException(404, "Call record not found")

    if point_index < 0:
        raise HTTPException(422, "point_index must be a non-negative integer")

    try:
        key_points: list[dict] = json.loads(call.key_points or "[]")
        point = key_points[point_index]
    except (IndexError, json.JSONDecodeError, TypeError):
        raise HTTPException(404, "Key point not found")

    if not isinstance(point, dict):
        raise HTTPException(422, f"Key point {point_index} is not a valid object (got {type(point).__name__})")

    if opportunity_id is not None:
        # Link to an existing Opportunity
        opp = db.get(Opportunity, opportunity_id)
        if not opp:
            raise HTTPException(404, f"Opportunity {opportunity_id} not found")
        action = "linked_existing"
    else:
        # Auto-create: find or create Account for the mentioned company, then Opportunity
        mentioned_company = point.get("mentioned_company") or call.company_name or "Unknown"
        # Escape SQL wildcards in user-provided value
        safe_company = mentioned_company.replace("%", r"\%").replace("_", r"\_")

        account = (
            db.query(Account)
            .filter(Account.name.ilike(f"%{safe_company}%", escape="\\"))
            .first()
        )
        if not account:
            account = Account(
                name=mentioned_company,
                type=AccountType.enterprise,
            )
            db.add(account)
            db.flush()  # get account.id before committing

        title_raw = point.get("mentioned_job_title") or point.get("text") or "Discussed opportunity"
        context_quote = point.get("context") or point.get("text") or ""
        call_date = call.created_at.date().isoformat() if call.created_at else "unknown date"

        opp = Opportunity(
            account_id=account.id,
            title=str(title_raw)[:255],
            stage=OpportunityStage.target,
            description=(
                f"Discussed by {call.executive_name or 'unknown'} in call on {call_date}.\n\n"
                f"Quote: {context_quote}"
            ),
        )
        db.add(opp)
        db.commit()
        db.refresh(opp)
        action = "created_new"

    # Write full audit trail back into the key point
    key_points[point_index].update({
        "linked_opportunity_id": opp.id,
        "linked_by": call.executive_name or "unknown",
        "linked_at": datetime.now(timezone.utc).isoformat(),
        "what_was_said": point.get("context") or point.get("text", ""),
        "action": action,
    })

    call.key_points = json.dumps(key_points)
    db.commit()
    db.refresh(call)

    logger.info(f"Key point {point_index} from call {call_id} → Opportunity {opp.id} ({action})")
    return _call_to_read(call)


# ── List, Get, Delete ─────────────────────────────────────────────────────────
@router.get("", response_model=list[CallIntelligenceRead])
def list_calls(
    company_name: str | None = None,
        account_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(CallIntelligence).order_by(CallIntelligence.created_at.desc())
    if company_name:
        q = q.filter(CallIntelligence.company_name.ilike(f"%{company_name}%"))
        if account_id is not None:
            q = q.filter(CallIntelligence.account_id == account_id)
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


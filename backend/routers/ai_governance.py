"""AI Governance endpoints – audit log and human review queue."""

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.intel import AIInvocationLog, HumanReviewItem
from backend.services import grok_client

logger = logging.getLogger("contractghost.ai_governance_router")

router = APIRouter(prefix="/ai-governance", tags=["AI Governance"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class InvocationLogOut(BaseModel):
    id: int
    prompt_hash: str
    model_version: str
    task_type: str
    temperature: float
    top_p: float
    input_tokens: int
    output_tokens: int
    confidence_score: float
    validation_outcome: str
    needs_review: bool
    review_reasons: str | None
    anomalies: str | None
    created_at: str

    model_config = {"from_attributes": True}


class ReviewItemOut(BaseModel):
    id: int
    source_type: str
    source_id: str | None
    task_type: str
    confidence_score: float
    reasons: str
    payload: str | None
    resolved: bool
    resolved_by: str | None
    created_at: str
    resolved_at: str | None

    model_config = {"from_attributes": True}


class ResolveReviewIn(BaseModel):
    resolved_by: str


# ---------------------------------------------------------------------------
# Audit Log endpoints
# ---------------------------------------------------------------------------


@router.get("/invocation-log", response_model=list[InvocationLogOut], summary="List AI invocation audit log")
def list_invocation_log(db: Session = Depends(get_db)) -> list[Any]:
    """Return the persisted AI invocation audit log (most recent first)."""
    return (
        db.query(AIInvocationLog)
        .order_by(AIInvocationLog.created_at.desc())
        .limit(200)
        .all()
    )


@router.post("/invocation-log/flush", summary="Flush in-memory log to database")
def flush_invocation_log(db: Session = Depends(get_db)) -> dict[str, int]:
    """
    Persist all in-memory invocation records to the database and clear the buffer.
    Call this endpoint periodically or after batch operations.
    """
    records = grok_client.get_invocation_log()
    count = 0
    for rec in records:
        db_record = AIInvocationLog(
            prompt_hash=rec.get("prompt_hash", ""),
            model_version=rec.get("model_version", "unknown"),
            task_type=rec.get("task_type", "unknown"),
            temperature=rec.get("temperature", 0.0),
            top_p=rec.get("top_p", 0.9),
            input_tokens=rec.get("input_tokens", 0),
            output_tokens=rec.get("output_tokens", 0),
            confidence_score=rec.get("confidence_score", 0.0),
            validation_outcome=rec.get("validation_outcome", "pass"),
            needs_review=rec.get("needs_review", False),
            review_reasons=json.dumps(rec.get("review_reasons", [])),
            anomalies=json.dumps(rec.get("anomalies", [])),
        )
        db.add(db_record)
        count += 1
    db.commit()
    grok_client.clear_invocation_log()
    logger.info("Flushed %d invocation records to database", count)
    return {"flushed": count}


# ---------------------------------------------------------------------------
# Human Review Queue endpoints
# ---------------------------------------------------------------------------


@router.get("/review-queue", response_model=list[ReviewItemOut], summary="List pending human review items")
def list_review_queue(db: Session = Depends(get_db)) -> list[Any]:
    """Return AI outputs that require human review."""
    return (
        db.query(HumanReviewItem)
        .filter(HumanReviewItem.resolved.is_(False))  # noqa: E712
        .order_by(HumanReviewItem.created_at.desc())
        .all()
    )


@router.post("/review-queue/{item_id}/resolve", response_model=ReviewItemOut, summary="Resolve a review item")
def resolve_review_item(
    item_id: int, body: ResolveReviewIn, db: Session = Depends(get_db)
) -> Any:
    """Mark a human review item as resolved."""
    from datetime import datetime, timezone

    item = db.get(HumanReviewItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    item.resolved = True
    item.resolved_by = body.resolved_by
    item.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    return item

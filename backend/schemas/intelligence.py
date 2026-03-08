"""Pydantic v2 schemas for Intelligence Briefing ingestion."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Request ───────────────────────────────────────────────────────────────────

class BriefingIngestRequest(BaseModel):
    """JSON body for POST /api/v1/intelligence/briefing."""

    briefing_text: str = Field(..., min_length=1, description="Full briefing text (markdown/plain)")


# ── Response ──────────────────────────────────────────────────────────────────

class BriefingIngestResponse(BaseModel):
    """Summary returned after processing a daily intelligence briefing."""

    processed_at: datetime
    accounts_updated: int
    opportunities_created: int
    trigger_signals_created: int
    briefing_doc_id: str
    suggested_touchpoints: list[str]


# ── DailyBriefing read ────────────────────────────────────────────────────────

class DailyBriefingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    briefing_type: str
    briefing_date: str | None
    accounts_updated: int
    opportunities_created: int
    trigger_signals_created: int
    created_at: datetime

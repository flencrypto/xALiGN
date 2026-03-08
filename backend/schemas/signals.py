"""Pydantic v2 schemas for SignalEvent."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.models.intel import SignalEventStatus, SignalEventType


class SignalEventCreate(BaseModel):
    company_name: str = Field(..., max_length=500)
    account_id: int | None = None
    event_type: SignalEventType = SignalEventType.general
    title: str = Field(..., max_length=500)
    description: str | None = None
    source_url: str | None = Field(None, max_length=2048)
    relevance_score: float | None = Field(None, ge=0.0, le=1.0)
    status: SignalEventStatus = SignalEventStatus.active
    event_date: datetime | None = None


class SignalEventUpdate(BaseModel):
    event_type: SignalEventType | None = None
    title: str | None = Field(None, max_length=500)
    description: str | None = None
    source_url: str | None = Field(None, max_length=2048)
    relevance_score: float | None = Field(None, ge=0.0, le=1.0)
    status: SignalEventStatus | None = None
    event_date: datetime | None = None


class SignalEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    account_id: int | None = None
    event_type: SignalEventType
    title: str
    description: str | None = None
    source_url: str | None = None
    relevance_score: float | None = None
    status: SignalEventStatus
    event_date: datetime | None = None
    detected_at: datetime


class ExpansionScoreRequest(BaseModel):
    signal_events: list[str] = Field(
        default_factory=list,
        description="List of signal event types (e.g. 'expansion', 'hiring_spike')",
    )
    days_since_events: list[int] = Field(
        default_factory=list,
        description="Days elapsed since each corresponding event",
    )
    hiring_count: int = Field(0, ge=0, description="Number of recent job postings detected")
    new_office_openings: int = Field(0, ge=0, description="Number of new office/facility openings")
    recent_acquisitions: int = Field(0, ge=0, description="Number of recent acquisitions")


class ExpansionScoreResult(BaseModel):
    expansion_activity_score: float
    breakdown: dict

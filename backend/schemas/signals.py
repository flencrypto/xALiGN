"""Pydantic v2 schemas for SignalEvent."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.models.intel import SignalEventStatus, SignalEventType


class SignalEventCreate(BaseModel):
    company_name: str = Field(..., max_length=500)
    account_id: int | None = None
    event_type: SignalEventType = SignalEventType.general
    title: str = Field(..., max_length=500)
    description: str | None = None
    source_url: str | None = Field(None, max_length=2048)
    relevance_score: float | None = Field(None, ge=0.0, le=1.0)
    strength: float = Field(1.0, ge=0.0, le=10.0)
    decay_factor: float = Field(0.05, ge=0.0, le=1.0)
    company_intel_id: int | None = None
    status: SignalEventStatus = SignalEventStatus.active
    event_date: datetime | None = None


class SignalEventUpdate(BaseModel):
    event_type: SignalEventType | None = None
    title: str | None = Field(None, max_length=500)
    description: str | None = None
    source_url: str | None = Field(None, max_length=2048)
    relevance_score: float | None = Field(None, ge=0.0, le=1.0)
    strength: float | None = Field(None, ge=0.0, le=10.0)
    decay_factor: float | None = Field(None, ge=0.0, le=1.0)
    company_intel_id: int | None = None
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
    strength: float
    decay_factor: float
    company_intel_id: int | None = None
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

    @model_validator(mode="after")
    def check_lists_same_length(self) -> "ExpansionScoreRequest":
        if len(self.signal_events) != len(self.days_since_events):
            raise ValueError(
                "signal_events and days_since_events must have the same length "
                f"(got {len(self.signal_events)} and {len(self.days_since_events)})"
            )
        return self


class ExpansionScoreResult(BaseModel):
    expansion_activity_score: float
    breakdown: dict


class RelationshipTimingResponse(BaseModel):
    timing_score: float
    recommend_contact: bool
    strongest_signal: str | None = None
    days_until_stale: int | None = None
    explanation: str | None = None

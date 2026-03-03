"""Pydantic v2 schemas for Tender Award, Call Intelligence, and Scoring."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Tender Awards ─────────────────────────────────────────────────────────────

class TenderAwardCreate(BaseModel):
    authority_name: str = Field(..., max_length=500)
    winning_company: str = Field(..., max_length=500)
    contract_value: float | None = None
    contract_currency: str | None = Field(None, max_length=10)
    scope_summary: str | None = None
    cpv_codes: list[str] | None = None
    award_date: str | None = None
    duration_months: int | None = None
    source_url: str | None = Field(None, max_length=2048)
    framework: bool = False
    region: str | None = Field(None, max_length=255)
    competitors: list[str] | None = None
    mw_capacity: float | None = None


class TenderAwardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    authority_name: str
    winning_company: str
    contract_value: float | None = None
    contract_currency: str | None = None
    scope_summary: str | None = None
    cpv_codes: list[str] | None = None
    award_date: str | None = None
    duration_months: int | None = None
    source_url: str | None = None
    framework: bool = False
    region: str | None = None
    competitors: list[str] | None = None
    mw_capacity: float | None = None
    created_at: datetime


# ── Call Intelligence ─────────────────────────────────────────────────────────

class CallIntelligenceCreate(BaseModel):
    company_name: str | None = Field(None, max_length=500)
    executive_name: str | None = Field(None, max_length=255)
    transcript: str | None = None


class CallIntelligenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str | None = None
    executive_name: str | None = None
    transcript: str | None = None
    sentiment_score: float | None = None
    competitor_mentions: list[str] | None = None
    budget_signals: list[str] | None = None
    timeline_mentions: list[str] | None = None
    risk_language: list[str] | None = None
    objection_categories: list[str] | None = None
    next_steps: str | None = None
    created_at: datetime


# ── Scoring ───────────────────────────────────────────────────────────────────

class CPIRequest(BaseModel):
    company: str = Field(..., description="Company name to compute CPI for")
    region_factor: float = Field(1.0, ge=0.1, le=5.0, description="Regional cost adjustment factor")


class CPIResult(BaseModel):
    company: str
    award_count: int
    total_value: float
    avg_price_per_mw: float | None
    cpi: float | None
    interpretation: str


class WinScoreRequest(BaseModel):
    company: str = Field(..., description="Company to score")
    historical_win_rate: float = Field(..., ge=0.0, le=1.0)
    expansion_activity_score: float = Field(..., ge=0.0, le=1.0)
    hiring_velocity: float = Field(..., ge=0.0, le=1.0)
    risk_score: float = Field(..., ge=0.0, le=1.0)
    region_factor: float = Field(1.0, ge=0.1, le=5.0)


class WinScoreResult(BaseModel):
    company: str
    win_probability: float
    cpi: float | None
    breakdown: dict


class RelationshipSuggestRequest(BaseModel):
    company_name: str = Field(..., description="Target company name")
    company_intel_id: int | None = None
    recent_events: list[str] = Field(
        default_factory=list,
        description="List of recent signal events (e.g. 'contract_win', 'new_role')"
    )
    days_since_events: list[int] = Field(
        default_factory=list,
        description="Days elapsed since each corresponding event"
    )


class RelationshipSuggestResult(BaseModel):
    company_name: str
    timing_score: float
    recommend_contact: bool
    suggested_angle: str
    why_now: str
    what_to_mention: str
    what_to_avoid: str
    risk_flags: str

"""Pydantic v2 schemas for Intelligence, Blog, and Upload models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from backend.models.intel import BlogStatus, NewsCategory


# ── Company Intel ─────────────────────────────────────────────────────────────

class CompanyIntelRequest(BaseModel):
    website: str = Field(..., description="Company website URL to research")


class ExecutiveProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_intel_id: int
    name: str
    role: str | None = None
    professional_focus: str | None = None
    public_interests: str | None = None
    recent_interviews: str | None = None
    conference_appearances: str | None = None
    charity_involvement: str | None = None
    communication_style: str | None = None
    conversation_angles: str | None = None
    created_at: datetime


class NewsItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_intel_id: int | None = None
    title: str
    summary: str | None = None
    source_url: str | None = None
    category: NewsCategory
    company_name: str | None = None
    published_at: str | None = None
    detected_at: datetime


class CompanyIntelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    website: str
    company_name: str | None = None
    business_model: str | None = None
    locations: str | None = None
    expansion_signals: str | None = None
    technology_indicators: str | None = None
    financial_summary: str | None = None
    earnings_highlights: str | None = None
    competitor_mentions: str | None = None
    strategic_risks: str | None = None
    bid_opportunities: str | None = None
    created_at: datetime
    executives: list[ExecutiveProfileRead] = []
    news_items: list[NewsItemRead] = []


class CompanyIntelSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    website: str
    company_name: str | None = None
    created_at: datetime


# ── News ──────────────────────────────────────────────────────────────────────

class NewsItemCreate(BaseModel):
    title: str = Field(..., max_length=500)
    summary: str | None = None
    source_url: str | None = Field(None, max_length=2048)
    category: NewsCategory = NewsCategory.general
    company_name: str | None = Field(None, max_length=255)
    published_at: str | None = None
    company_intel_id: int | None = None


# ── Blog ──────────────────────────────────────────────────────────────────────

class BlogGenerateRequest(BaseModel):
    company_intel_id: int | None = None
    topic: str = Field(..., description="Blog topic or title hint")
    tone: str = Field("institutional", description="Writing tone: institutional, conversational, technical")
    target_persona: str = Field("infrastructure decision-maker", description="Target reader persona")
    word_count: int = Field(800, ge=300, le=3000)
    seo_keywords: str | None = None
    cta: str | None = None


class BlogPostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_intel_id: int | None = None
    title: str
    slug: str
    body_markdown: str
    meta_description: str | None = None
    seo_keywords: str | None = None
    linkedin_variant: str | None = None
    x_variant: str | None = None
    status: BlogStatus
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class BlogPostSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    status: BlogStatus
    created_at: datetime


class BlogPostUpdate(BaseModel):
    title: str | None = None
    body_markdown: str | None = None
    meta_description: str | None = Field(None, max_length=500)
    seo_keywords: str | None = None
    linkedin_variant: str | None = None
    x_variant: str | None = None
    status: BlogStatus | None = None


# ── Photo Upload ──────────────────────────────────────────────────────────────

class UploadedPhotoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    original_filename: str
    storage_path: str
    content_type: str | None = None
    size_bytes: int | None = None
    alt_text: str | None = None
    ai_description: str | None = None
    company_intel_id: int | None = None
    bid_id: int | None = None
    uploaded_at: datetime


# ── Tender Award ──────────────────────────────────────────────────────────────

class TenderAwardCreate(BaseModel):
    authority_name: str = Field(..., max_length=500)
    winning_company: str = Field(..., max_length=500)
    contract_value: float | None = None
    currency: str = Field("GBP", max_length=3)
    cpv_codes: str | None = None
    duration_months: int | None = None
    award_date: datetime | None = None
    scope_summary: str | None = None
    source_url: str | None = Field(None, max_length=2048)
    capacity_mw: float | None = None
    company_intel_id: int | None = None


class TenderAwardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_intel_id: int | None = None
    authority_name: str
    winning_company: str
    contract_value: float | None = None
    currency: str
    cpv_codes: str | None = None
    duration_months: int | None = None
    award_date: datetime | None = None
    scope_summary: str | None = None
    source_url: str | None = None
    capacity_mw: float | None = None
    price_per_mw: float | None = None
    created_at: datetime


class TenderAwardUpdate(BaseModel):
    authority_name: str | None = Field(None, max_length=500)
    winning_company: str | None = Field(None, max_length=500)
    contract_value: float | None = None
    currency: str | None = Field(None, max_length=3)
    cpv_codes: str | None = None
    duration_months: int | None = None
    award_date: datetime | None = None
    scope_summary: str | None = None
    source_url: str | None = Field(None, max_length=2048)
    capacity_mw: float | None = None


# ── Signal Event ──────────────────────────────────────────────────────────────

class SignalEventCreate(BaseModel):
    company_intel_id: int | None = None
    company_name: str | None = Field(None, max_length=255)
    signal_type: str = Field(..., max_length=100)
    strength: float = Field(1.0, ge=0.0, le=10.0)
    decay_factor: float = Field(0.1, ge=0.0, le=1.0)
    event_date: datetime
    source_url: str | None = Field(None, max_length=2048)
    description: str | None = None


class SignalEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_intel_id: int | None = None
    company_name: str | None = None
    signal_type: str
    strength: float
    decay_factor: float
    event_date: datetime
    source_url: str | None = None
    description: str | None = None
    created_at: datetime


class SignalEventUpdate(BaseModel):
    signal_type: str | None = Field(None, max_length=100)
    strength: float | None = Field(None, ge=0.0, le=10.0)
    decay_factor: float | None = Field(None, ge=0.0, le=1.0)
    event_date: datetime | None = None
    source_url: str | None = Field(None, max_length=2048)
    description: str | None = None


class RelationshipTimingResponse(BaseModel):
    company_name: str | None
    total_score: float
    recommendation: str
    context_brief: str
    conversation_angle: str
    risk_flags: list[str]
    top_signals: list[SignalEventRead]


# ── Call Intelligence ─────────────────────────────────────────────────────────

class CallCreate(BaseModel):
    title: str = Field(..., max_length=500)
    company_intel_id: int | None = None
    executive_profile_id: int | None = None
    transcript: str | None = None


class CallRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_intel_id: int | None = None
    executive_profile_id: int | None = None
    title: str
    audio_filename: str | None = None
    transcript: str | None = None
    sentiment_score: float | None = None
    competitor_mentions: str | None = None
    budget_signals: str | None = None
    risk_phrases: str | None = None
    next_steps: str | None = None
    crm_summary: str | None = None
    created_at: datetime


class CallAnalyzeRequest(BaseModel):
    transcript: str = Field(..., min_length=20)

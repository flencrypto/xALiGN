"""Pydantic v2 schemas for the AI Intelligence Layer."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── ExecutiveProfile ──────────────────────────────────────────────────────────

class ExecutiveProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    intelligence_id: int
    account_id: int | None = None
    name: str
    role: str | None = None
    professional_focus: str | None = None
    public_interests: str | None = None
    recent_interviews: str | None = None
    conference_appearances: str | None = None
    public_charity_involvement: str | None = None
    communication_style: str | None = None
    conversation_angles: str | None = None
    source_urls: str | None = None
    created_at: datetime
    updated_at: datetime


# ── NewsSignal ────────────────────────────────────────────────────────────────

class NewsSignalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    intelligence_id: int | None = None
    account_id: int | None = None
    headline: str
    url: str | None = None
    source: str | None = None
    published_at: datetime | None = None
    tags: str | None = None
    summary: str | None = None
    sentiment: str | None = None
    created_at: datetime


# ── CompanyIntelligence ───────────────────────────────────────────────────────

class CompanyIntelligenceCreate(BaseModel):
    website_url: str = Field(..., max_length=2048)
    account_id: int | None = None


class CompanyIntelligenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int | None = None
    website_url: str
    company_name: str | None = None
    business_model: str | None = None
    locations: str | None = None
    leadership_team: str | None = None
    expansion_signals: str | None = None
    technology_growth_indicators: str | None = None
    financial_health_summary: str | None = None
    recent_earnings_highlights: str | None = None
    competitor_mentions: str | None = None
    strategic_risk_factors: str | None = None
    potential_bid_opportunities: str | None = None
    raw_crawl_data: str | None = None
    status: str
    error_message: str | None = None
    sources_cited: str | None = None
    created_at: datetime
    updated_at: datetime
    executive_profiles: list[ExecutiveProfileRead] = []
    news_signals: list[NewsSignalRead] = []


# ── BlogDraft ─────────────────────────────────────────────────────────────────

class BlogDraftCreate(BaseModel):
    title: str = Field(..., max_length=512)
    body_markdown: str
    target_persona: str | None = Field(None, max_length=255)
    seo_keywords: str | None = None


class BlogDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    intelligence_id: int | None = None
    title: str
    slug: str
    body_markdown: str
    seo_meta_description: str | None = None
    linkedin_variant: str | None = None
    x_variant: str | None = None
    target_persona: str | None = None
    seo_keywords: str | None = None
    status: str
    published_at: datetime | None = None
    published_url: str | None = None
    created_at: datetime
    updated_at: datetime


class BlogDraftApprove(BaseModel):
    status: str = Field(..., max_length=50)


# ── IntelPhoto ────────────────────────────────────────────────────────────────

class IntelPhotoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    intelligence_id: int | None = None
    account_id: int | None = None
    filename: str
    s3_key: str | None = None
    s3_url: str | None = None
    local_path: str | None = None
    photo_type: str | None = None
    ai_analysis: str | None = None
    uploaded_at: datetime


# ── Composite Response ────────────────────────────────────────────────────────

class IntelResearchResponse(BaseModel):
    company_summary: CompanyIntelligenceRead
    executive_profiles: list[ExecutiveProfileRead] = []
    expansion_signals: list = []
    news_feed: list[NewsSignalRead] = []

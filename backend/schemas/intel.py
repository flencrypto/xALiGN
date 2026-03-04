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
    stock_ticker: str | None = None
    stock_price: str | None = None
    linkedin_posts: str | None = None
    x_posts: str | None = None
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

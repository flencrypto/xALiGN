"""Intelligence, Blog, and Upload SQLAlchemy models."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class BlogStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    published = "published"


class NewsCategory(str, enum.Enum):
    expansion = "expansion"
    earnings = "earnings"
    technology = "technology"
    competitor = "competitor"
    hiring = "hiring"
    funding = "funding"
    general = "general"


# ── Company Intelligence ──────────────────────────────────────────────────────

class CompanyIntel(Base):
    """Stores a structured intelligence snapshot for a company."""

    __tablename__ = "company_intel"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    website: Mapped[str] = mapped_column(String(2048), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255))
    business_model: Mapped[str | None] = mapped_column(Text)
    locations: Mapped[str | None] = mapped_column(Text)
    expansion_signals: Mapped[str | None] = mapped_column(Text)
    technology_indicators: Mapped[str | None] = mapped_column(Text)
    financial_summary: Mapped[str | None] = mapped_column(Text)
    earnings_highlights: Mapped[str | None] = mapped_column(Text)
    competitor_mentions: Mapped[str | None] = mapped_column(Text)
    strategic_risks: Mapped[str | None] = mapped_column(Text)
    bid_opportunities: Mapped[str | None] = mapped_column(Text)
    raw_response: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    executives: Mapped[list["ExecutiveProfile"]] = relationship(
        "ExecutiveProfile", back_populates="company_intel", cascade="all, delete-orphan"
    )
    news_items: Mapped[list["NewsItem"]] = relationship(
        "NewsItem", back_populates="company_intel", cascade="all, delete-orphan"
    )
    blog_posts: Mapped[list["BlogPost"]] = relationship(
        "BlogPost", back_populates="company_intel", cascade="all, delete-orphan"
    )
    tender_awards: Mapped[list["TenderAward"]] = relationship(
        "TenderAward", back_populates="company_intel", cascade="all, delete-orphan"
    )
    signal_events: Mapped[list["SignalEvent"]] = relationship(
        "SignalEvent", back_populates="company_intel", cascade="all, delete-orphan"
    )
    calls: Mapped[list["CallIntelligence"]] = relationship(
        "CallIntelligence", back_populates="company_intel", cascade="all, delete-orphan"
    )


class ExecutiveProfile(Base):
    """Public professional profile for a company executive."""

    __tablename__ = "executive_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_intel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("company_intel.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(255))
    professional_focus: Mapped[str | None] = mapped_column(Text)
    public_interests: Mapped[str | None] = mapped_column(Text)
    recent_interviews: Mapped[str | None] = mapped_column(Text)
    conference_appearances: Mapped[str | None] = mapped_column(Text)
    charity_involvement: Mapped[str | None] = mapped_column(Text)
    communication_style: Mapped[str | None] = mapped_column(String(255))
    conversation_angles: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    company_intel: Mapped["CompanyIntel"] = relationship(
        "CompanyIntel", back_populates="executives"
    )


class NewsItem(Base):
    """A tracked news article or signal for a company."""

    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_intel_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("company_intel.id", ondelete="CASCADE"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    category: Mapped[NewsCategory] = mapped_column(
        Enum(NewsCategory), default=NewsCategory.general, server_default="general"
    )
    company_name: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[str | None] = mapped_column(String(100))
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    company_intel: Mapped["CompanyIntel | None"] = relationship(
        "CompanyIntel", back_populates="news_items"
    )


# ── Blog ──────────────────────────────────────────────────────────────────────

class BlogPost(Base):
    """An AI-generated blog post."""

    __tablename__ = "blog_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_intel_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("company_intel.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    body_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    meta_description: Mapped[str | None] = mapped_column(String(500))
    seo_keywords: Mapped[str | None] = mapped_column(Text)
    linkedin_variant: Mapped[str | None] = mapped_column(Text)
    x_variant: Mapped[str | None] = mapped_column(Text)
    status: Mapped[BlogStatus] = mapped_column(
        Enum(BlogStatus), default=BlogStatus.draft, server_default="draft"
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )

    company_intel: Mapped["CompanyIntel | None"] = relationship(
        "CompanyIntel", back_populates="blog_posts"
    )


# ── Tender Award ──────────────────────────────────────────────────────────────

class TenderAward(Base):
    """A public procurement contract award from tendering authority records."""

    __tablename__ = "tender_awards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_intel_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("company_intel.id", ondelete="SET NULL"), nullable=True
    )
    authority_name: Mapped[str] = mapped_column(String(500), nullable=False)
    winning_company: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    contract_value: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="GBP", server_default="GBP")
    cpv_codes: Mapped[str | None] = mapped_column(Text)  # JSON array string
    duration_months: Mapped[int | None] = mapped_column(Integer)
    award_date: Mapped[datetime | None] = mapped_column(DateTime)
    scope_summary: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    capacity_mw: Mapped[float | None] = mapped_column(Float)  # for CPI calculation
    price_per_mw: Mapped[float | None] = mapped_column(Float)  # derived CPI field
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    company_intel: Mapped["CompanyIntel | None"] = relationship(
        "CompanyIntel", back_populates="tender_awards"
    )


# ── Signal Event ──────────────────────────────────────────────────────────────

class SignalEvent(Base):
    """A tracked market signal with exponential-decay scoring for relationship timing."""

    __tablename__ = "signal_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_intel_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("company_intel.id", ondelete="CASCADE"), nullable=True
    )
    company_name: Mapped[str | None] = mapped_column(String(255))
    signal_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    strength: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0")
    decay_factor: Mapped[float] = mapped_column(Float, default=0.1, server_default="0.1")
    event_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    company_intel: Mapped["CompanyIntel | None"] = relationship(
        "CompanyIntel", back_populates="signal_events"
    )


# ── Call Intelligence ─────────────────────────────────────────────────────────

class CallIntelligence(Base):
    """Analysed sales call or meeting — transcript + AI-extracted signals."""

    __tablename__ = "call_intelligence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_intel_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("company_intel.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    audio_filename: Mapped[str | None] = mapped_column(String(500))
    audio_path: Mapped[str | None] = mapped_column(String(2048))
    transcript: Mapped[str | None] = mapped_column(Text)
    sentiment_score: Mapped[float | None] = mapped_column(Float)
    competitor_mentions: Mapped[str | None] = mapped_column(Text)  # JSON array
    budget_signals: Mapped[str | None] = mapped_column(Text)  # JSON array
    risk_phrases: Mapped[str | None] = mapped_column(Text)  # JSON array
    next_steps: Mapped[str | None] = mapped_column(Text)
    crm_summary: Mapped[str | None] = mapped_column(Text)
    executive_profile_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("executive_profiles.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    company_intel: Mapped["CompanyIntel | None"] = relationship(
        "CompanyIntel", back_populates="calls"
    )


# ── Photo / File Upload ───────────────────────────────────────────────────────

class UploadedPhoto(Base):
    """Metadata for an uploaded photo or file."""

    __tablename__ = "uploaded_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    alt_text: Mapped[str | None] = mapped_column(String(500))
    ai_description: Mapped[str | None] = mapped_column(Text)
    company_intel_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("company_intel.id", ondelete="SET NULL"), nullable=True
    )
    bid_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("bids.id", ondelete="SET NULL"), nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

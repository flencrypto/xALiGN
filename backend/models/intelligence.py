"""SQLAlchemy models for the AI Intelligence Layer."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class CompanyIntelligence(Base):
    """Aggregated AI intelligence record for a target company."""

    __tablename__ = "company_intelligence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    website_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255))
    business_model: Mapped[str | None] = mapped_column(Text)
    locations: Mapped[str | None] = mapped_column(Text)  # JSON
    leadership_team: Mapped[str | None] = mapped_column(Text)  # JSON
    expansion_signals: Mapped[str | None] = mapped_column(Text)  # JSON
    technology_growth_indicators: Mapped[str | None] = mapped_column(Text)  # JSON
    financial_health_summary: Mapped[str | None] = mapped_column(Text)
    recent_earnings_highlights: Mapped[str | None] = mapped_column(Text)  # JSON
    competitor_mentions: Mapped[str | None] = mapped_column(Text)  # JSON
    strategic_risk_factors: Mapped[str | None] = mapped_column(Text)  # JSON
    potential_bid_opportunities: Mapped[str | None] = mapped_column(Text)  # JSON
    raw_crawl_data: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="pending", server_default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
    sources_cited: Mapped[str | None] = mapped_column(Text)  # JSON
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )

    executive_profiles: Mapped[list["ExecutiveProfile"]] = relationship(
        "ExecutiveProfile", back_populates="intelligence", cascade="all, delete-orphan"
    )
    news_signals: Mapped[list["NewsSignal"]] = relationship(
        "NewsSignal", back_populates="intelligence", cascade="all, delete-orphan"
    )
    blog_drafts: Mapped[list["BlogDraft"]] = relationship(
        "BlogDraft", back_populates="intelligence", cascade="all, delete-orphan"
    )
    intel_photos: Mapped[list["IntelPhoto"]] = relationship(
        "IntelPhoto", back_populates="intelligence", cascade="all, delete-orphan"
    )


class ExecutiveProfile(Base):
    """Public-data executive profile extracted from intelligence research."""

    __tablename__ = "executive_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    intelligence_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("company_intelligence.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(255))
    professional_focus: Mapped[str | None] = mapped_column(Text)  # JSON
    public_interests: Mapped[str | None] = mapped_column(Text)  # JSON
    recent_interviews: Mapped[str | None] = mapped_column(Text)  # JSON
    conference_appearances: Mapped[str | None] = mapped_column(Text)  # JSON
    public_charity_involvement: Mapped[str | None] = mapped_column(Text)  # JSON
    communication_style: Mapped[str | None] = mapped_column(String(255))
    conversation_angles: Mapped[str | None] = mapped_column(Text)  # JSON
    source_urls: Mapped[str | None] = mapped_column(Text)  # JSON
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )

    intelligence: Mapped["CompanyIntelligence"] = relationship(
        "CompanyIntelligence", back_populates="executive_profiles"
    )


class NewsSignal(Base):
    """A news item or signal linked to a company intelligence record."""

    __tablename__ = "news_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    intelligence_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("company_intelligence.id", ondelete="SET NULL"), nullable=True, index=True
    )
    account_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    headline: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048))
    source: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    tags: Mapped[str | None] = mapped_column(Text)  # JSON
    summary: Mapped[str | None] = mapped_column(Text)
    sentiment: Mapped[str | None] = mapped_column(String(50))  # positive, negative, neutral
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    intelligence: Mapped["CompanyIntelligence | None"] = relationship(
        "CompanyIntelligence", back_populates="news_signals"
    )


class BlogDraft(Base):
    """AI-generated blog post draft pending editorial approval."""

    __tablename__ = "blog_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    intelligence_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("company_intelligence.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    slug: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    body_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    seo_meta_description: Mapped[str | None] = mapped_column(String(512))
    linkedin_variant: Mapped[str | None] = mapped_column(Text)
    x_variant: Mapped[str | None] = mapped_column(String(280))
    target_persona: Mapped[str | None] = mapped_column(String(255))
    seo_keywords: Mapped[str | None] = mapped_column(Text)  # JSON
    status: Mapped[str] = mapped_column(String(50), default="draft", server_default="draft")
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    published_url: Mapped[str | None] = mapped_column(String(2048))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )

    intelligence: Mapped["CompanyIntelligence | None"] = relationship(
        "CompanyIntelligence", back_populates="blog_drafts"
    )


class IntelPhoto(Base):
    """Photo asset associated with a company intelligence record."""

    __tablename__ = "intel_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    intelligence_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("company_intelligence.id", ondelete="SET NULL"), nullable=True, index=True
    )
    account_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    s3_key: Mapped[str | None] = mapped_column(String(1024))
    s3_url: Mapped[str | None] = mapped_column(String(2048))
    local_path: Mapped[str | None] = mapped_column(String(1024))
    photo_type: Mapped[str | None] = mapped_column(String(50))  # headshot, facility, project, brand
    ai_analysis: Mapped[str | None] = mapped_column(Text)  # JSON
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    intelligence: Mapped["CompanyIntelligence | None"] = relationship(
        "CompanyIntelligence", back_populates="intel_photos"
    )

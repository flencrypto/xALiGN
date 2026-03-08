"""Intelligence Collection Layer – SQLAlchemy models for BATCH 1 data stores."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class DailyBriefing(Base):
    """Stores the full raw text of a daily intelligence briefing for auditability."""

    __tablename__ = "daily_briefings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    briefing_type: Mapped[str] = mapped_column(
        String(100), default="daily_intelligence_briefing", server_default="daily_intelligence_briefing"
    )
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    briefing_date: Mapped[str | None] = mapped_column(String(50))  # ISO date string
    accounts_updated: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    opportunities_created: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    trigger_signals_created: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )


class NewsArticleCategory(str, enum.Enum):
    data_centre = "data_centre"
    hyperscaler = "hyperscaler"
    supplier = "supplier"
    ai_infrastructure = "ai_infrastructure"
    power_infrastructure = "power_infrastructure"
    chips = "chips"
    general = "general"


class NewsSourceType(str, enum.Enum):
    rss = "rss"
    api = "api"
    scrape = "scrape"


class PlanningApplicationStatus(str, enum.Enum):
    submitted = "submitted"
    pending = "pending"
    approved = "approved"
    refused = "refused"
    withdrawn = "withdrawn"


class AnnouncementType(str, enum.Enum):
    power_grid = "power_grid"
    fibre = "fibre"
    energy_deal = "energy_deal"
    substation = "substation"
    data_centre = "data_centre"
    general = "general"


class NewsArticle(Base):
    """Raw news article collected by the News Intelligence Aggregator."""

    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048))
    source_name: Mapped[str | None] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)
    full_text: Mapped[str | None] = mapped_column(Text)
    category: Mapped[NewsArticleCategory] = mapped_column(
        Enum(NewsArticleCategory),
        default=NewsArticleCategory.general,
        server_default="general",
    )
    keywords_matched: Mapped[str | None] = mapped_column(Text)  # JSON list
    published_at: Mapped[str | None] = mapped_column(String(100))
    source_type: Mapped[NewsSourceType] = mapped_column(
        Enum(NewsSourceType),
        default=NewsSourceType.rss,
        server_default="rss",
    )
    confidence_score: Mapped[float | None] = mapped_column(Float)
    signal_type: Mapped[str | None] = mapped_column(String(100))
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )


class PlanningApplication(Base):
    """Planning application detected by the Planning Portal Scraper."""

    __tablename__ = "planning_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reference: Mapped[str | None] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    applicant: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(500))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    portal_name: Mapped[str | None] = mapped_column(String(255))
    portal_url: Mapped[str | None] = mapped_column(String(2048))
    status: Mapped[PlanningApplicationStatus] = mapped_column(
        Enum(PlanningApplicationStatus),
        default=PlanningApplicationStatus.pending,
        server_default="pending",
    )
    application_date: Mapped[str | None] = mapped_column(String(100))
    decision_date: Mapped[str | None] = mapped_column(String(100))
    is_data_centre: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    documents: Mapped[str | None] = mapped_column(Text)  # JSON list of doc URLs/names
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )


class VendorPressRelease(Base):
    """Vendor press release collected by the Vendor Press Release Harvester."""

    __tablename__ = "vendor_press_releases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048))
    summary: Mapped[str | None] = mapped_column(Text)
    full_text: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[str | None] = mapped_column(String(100))
    extracted_entities: Mapped[str | None] = mapped_column(Text)  # JSON: companies, locations, products
    related_suppliers: Mapped[str | None] = mapped_column(Text)  # JSON: supplier names
    project_signals: Mapped[str | None] = mapped_column(Text)  # JSON: detected project references
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )


class JobPostingSignal(Base):
    """Hiring spike detected by the Job Posting Signal Detector."""

    __tablename__ = "job_posting_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(500))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    job_count: Mapped[int] = mapped_column(Integer, default=1)
    posting_url: Mapped[str | None] = mapped_column(String(2048))
    source_board: Mapped[str | None] = mapped_column(String(100))  # linkedin, indeed, etc.
    is_spike: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    spike_factor: Mapped[float | None] = mapped_column(Float)
    is_expansion_signal: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    posted_at: Mapped[str | None] = mapped_column(String(100))


class InfrastructureAnnouncement(Base):
    """Infrastructure announcement detected by the Infrastructure Announcement Monitor."""

    __tablename__ = "infrastructure_announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(255))
    source_url: Mapped[str | None] = mapped_column(String(2048))
    summary: Mapped[str | None] = mapped_column(Text)
    announcement_type: Mapped[AnnouncementType] = mapped_column(
        Enum(AnnouncementType),
        default=AnnouncementType.general,
        server_default="general",
    )
    location: Mapped[str | None] = mapped_column(String(500))
    operator: Mapped[str | None] = mapped_column(String(255))
    capacity_mw: Mapped[float | None] = mapped_column(Float)
    project_value_gbp: Mapped[float | None] = mapped_column(Float)
    keywords_matched: Mapped[str | None] = mapped_column(Text)  # JSON list
    published_at: Mapped[str | None] = mapped_column(String(100))
    confidence_score: Mapped[float | None] = mapped_column(Float)
    signal_type: Mapped[str | None] = mapped_column(String(100))
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

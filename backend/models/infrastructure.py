"""Infrastructure Intelligence SQLAlchemy models.

Three tables covering:
  - infrastructure_projects  – individual data-centre / campus projects
  - dc_companies             – company reference data
  - opportunity_signals      – actionable BD signals derived from project data
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class ProjectStage(str, enum.Enum):
    planning      = "planning"
    permitted     = "permitted"
    construction  = "construction"
    operational   = "operational"
    announced     = "announced"
    cancelled     = "cancelled"


class IndustrySegment(str, enum.Enum):
    hyperscaler   = "hyperscaler"
    colocation    = "colocation"
    sovereign_ai  = "sovereign_ai"
    enterprise    = "enterprise"
    edge          = "edge"
    other         = "other"


class ConfidenceLevel(str, enum.Enum):
    high   = "high"
    medium = "medium"
    low    = "low"


class CompanyCategory(str, enum.Enum):
    hyperscaler  = "hyperscaler"
    operator     = "operator"
    supplier     = "supplier"
    contractor   = "contractor"
    other        = "other"


class SignalType(str, enum.Enum):
    planning = "planning"
    tender   = "tender"
    land     = "land"
    power    = "power"
    other    = "other"


class SignalLikelihood(str, enum.Enum):
    high   = "high"
    medium = "medium"
    low    = "low"


# ── Infrastructure Projects ───────────────────────────────────────────────────

class InfrastructureProject(Base):
    """A tracked data-centre or AI-campus infrastructure project."""

    __tablename__ = "infrastructure_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Core identity
    company: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    project_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)

    # Location
    location_city: Mapped[str | None] = mapped_column(String(255))
    location_country: Mapped[str | None] = mapped_column(String(255), index=True)
    region: Mapped[str | None] = mapped_column(String(255), index=True)

    # Classification
    project_type: Mapped[str | None] = mapped_column(String(255))
    industry_segment: Mapped[IndustrySegment] = mapped_column(
        Enum(IndustrySegment),
        default=IndustrySegment.other,
        server_default="other",
        index=True,
    )

    # Financials / capacity
    investment_value: Mapped[float | None] = mapped_column(Numeric(20, 2))
    capacity_mw: Mapped[float | None] = mapped_column(Float)

    # Lifecycle
    project_stage: Mapped[ProjectStage] = mapped_column(
        Enum(ProjectStage),
        default=ProjectStage.announced,
        server_default="announced",
        index=True,
    )

    # Partners stored as a JSON-encoded list of strings
    partners: Mapped[str | None] = mapped_column(Text)  # JSON array string

    # Source metadata
    date_announced: Mapped[datetime | None] = mapped_column(Date)
    source: Mapped[str | None] = mapped_column(String(500))
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        Enum(ConfidenceLevel),
        default=ConfidenceLevel.medium,
        server_default="medium",
    )
    summary: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )

    opportunity_signals: Mapped[list["OpportunitySignal"]] = relationship(
        "OpportunitySignal",
        back_populates="project",
        cascade="all, delete-orphan",
    )


# ── DC Companies ─────────────────────────────────────────────────────────────

class DCCompany(Base):
    """Reference data for a company active in the data-centre sector."""

    __tablename__ = "dc_companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    category: Mapped[CompanyCategory] = mapped_column(
        Enum(CompanyCategory),
        default=CompanyCategory.other,
        server_default="other",
        index=True,
    )
    hq_country: Mapped[str | None] = mapped_column(String(255))
    stock_ticker: Mapped[str | None] = mapped_column(String(20))
    website: Mapped[str | None] = mapped_column(String(2048))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )


# ── Opportunity Signals ───────────────────────────────────────────────────────

class OpportunitySignal(Base):
    """An actionable BD signal derived from a specific infrastructure project."""

    __tablename__ = "opportunity_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("infrastructure_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signal_type: Mapped[SignalType] = mapped_column(
        Enum(SignalType),
        default=SignalType.other,
        server_default="other",
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text)
    likelihood: Mapped[SignalLikelihood] = mapped_column(
        Enum(SignalLikelihood),
        default=SignalLikelihood.medium,
        server_default="medium",
    )
    recommended_action: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    project: Mapped["InfrastructureProject"] = relationship(
        "InfrastructureProject",
        back_populates="opportunity_signals",
    )

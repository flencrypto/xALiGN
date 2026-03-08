"""Intelligence Database Layer – SQLAlchemy models for BATCH 3.

Stores structured infrastructure intelligence:
- InfrastructureProject: detected data centre / power projects
- CompanyProfile: enriched company intelligence records
- OpportunitySignal: commercial opportunities derived from signals
"""

import enum
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class ProjectStage(str, enum.Enum):
    announced = "announced"
    planning = "planning"
    approved = "approved"
    construction = "construction"
    operational = "operational"
    cancelled = "cancelled"


class ProjectType(str, enum.Enum):
    new_build = "new_build"
    expansion = "expansion"
    upgrade = "upgrade"
    energy_deal = "energy_deal"
    acquisition = "acquisition"
    general = "general"


class CompanyCategory(str, enum.Enum):
    hyperscaler = "hyperscaler"
    colocation = "colocation"
    enterprise = "enterprise"
    developer = "developer"
    operator = "operator"
    supplier = "supplier"
    contractor = "contractor"
    utility = "utility"


class OpportunityType(str, enum.Enum):
    new_build = "new_build"
    expansion = "expansion"
    m_and_e_fit_out = "m_and_e_fit_out"
    energy_deal = "energy_deal"
    maintenance = "maintenance"
    upgrade = "upgrade"
    decommission = "decommission"


class InfrastructureProject(Base):
    """A detected infrastructure project (data centre, power, fibre, etc.)."""

    __tablename__ = "infrastructure_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    company: Mapped[str | None] = mapped_column(String(255), index=True)
    location: Mapped[str | None] = mapped_column(String(500))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    capacity_mw: Mapped[float | None] = mapped_column(Float)
    capex_millions: Mapped[float | None] = mapped_column(Float)
    capex_currency: Mapped[str | None] = mapped_column(String(10), default="GBP")
    stage: Mapped[ProjectStage] = mapped_column(
        Enum(ProjectStage), default=ProjectStage.announced, server_default="announced"
    )
    project_type: Mapped[ProjectType] = mapped_column(
        Enum(ProjectType, name="infrastructure_project_type"),
        default=ProjectType.general,
        server_default="general",
    )
    partners: Mapped[str | None] = mapped_column(Text)  # JSON list of partner names
    source_url: Mapped[str | None] = mapped_column(String(2048))
    source_name: Mapped[str | None] = mapped_column(String(255))
    confidence_score: Mapped[float | None] = mapped_column(Float)
    signal_type: Mapped[str | None] = mapped_column(String(100))
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    canonical_project_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )


class CompanyProfile(Base):
    """Enriched company intelligence record."""

    __tablename__ = "company_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[CompanyCategory] = mapped_column(
        Enum(CompanyCategory), default=CompanyCategory.operator, server_default="operator"
    )
    headquarters: Mapped[str | None] = mapped_column(String(255))
    stock_ticker: Mapped[str | None] = mapped_column(String(20))
    website: Mapped[str | None] = mapped_column(String(2048))
    known_partners: Mapped[str | None] = mapped_column(Text)  # JSON list
    total_capacity_mw: Mapped[float | None] = mapped_column(Float)
    total_capex_millions: Mapped[float | None] = mapped_column(Float)
    active_projects: Mapped[int | None] = mapped_column(Integer, default=0)
    regions_active: Mapped[str | None] = mapped_column(Text)  # JSON list of regions
    description: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )


class OpportunitySignal(Base):
    """A commercial opportunity derived from infrastructure signals."""

    __tablename__ = "opportunity_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    opportunity_type: Mapped[OpportunityType] = mapped_column(
        Enum(OpportunityType), default=OpportunityType.new_build, server_default="new_build"
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(500))
    potential_suppliers: Mapped[str | None] = mapped_column(Text)  # JSON list
    likelihood_score: Mapped[float | None] = mapped_column(Float)  # 0.0-1.0
    estimated_value_millions: Mapped[float | None] = mapped_column(Float)
    estimated_tender_date: Mapped[str | None] = mapped_column(String(100))
    source_signal_url: Mapped[str | None] = mapped_column(String(2048))
    notes: Mapped[str | None] = mapped_column(Text)
    is_actioned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )

"""Data Center Briefing SQLAlchemy models."""

import enum
from datetime import datetime
from typing import List

from sqlalchemy import (
    DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, func, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class ProjectType(str, enum.Enum):
    """Data center project types"""
    new_build = "new_build"
    expansion = "expansion"
    acquisition = "acquisition"
    retrofit = "retrofit"
    decommission = "decommission"


class ProjectStage(str, enum.Enum):
    """Project development stages"""
    announced = "announced"
    planning = "planning"
    construction = "construction"
    operational = "operational"
    cancelled = "cancelled"


class CompanyRoleType(str, enum.Enum):
    """Company roles in projects"""
    operator = "operator"
    tenant = "tenant"
    acquirer = "acquirer"
    partner = "partner"
    developer = "developer"
    supplier = "supplier"


class ConfidenceLevel(str, enum.Enum):
    """Confidence in data accuracy"""
    high = "high"
    medium = "medium"
    low = "low"


class DailyBriefing(Base):
    """Daily intelligence briefing on data center market"""
    
    __tablename__ = "daily_briefings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    briefing_date: Mapped[datetime] = mapped_column(DateTime, unique=True, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "data_center_daily"
    overview: Mapped[str] = mapped_column(Text, nullable=False)
    market_signals: Mapped[dict] = mapped_column(JSON, nullable=False)
    regional_hotspots: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    raw_json: Mapped[dict] = mapped_column(JSON, nullable=False)  # Store complete payload
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    news_items: Mapped[List["NewsItem"]] = relationship(
        "NewsItem", back_populates="briefing", cascade="all, delete-orphan"
    )
    projects: Mapped[List["DataCenterProject"]] = relationship(
        "DataCenterProject", back_populates="briefing", cascade="all, delete-orphan"
    )
    opportunities: Mapped[List["InfrastructureOpportunity"]] = relationship(
        "InfrastructureOpportunity", back_populates="briefing", cascade="all, delete-orphan"
    )


class NewsItem(Base):
    """News article from daily briefing"""
    
    __tablename__ = "news_items"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    published_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    strategic_insight: Mapped[str] = mapped_column(Text, nullable=False)
    companies: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    tags: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    
    briefing_id: Mapped[int] = mapped_column(Integer, ForeignKey("daily_briefings.id"), nullable=False)
    briefing: Mapped["DailyBriefing"] = relationship("DailyBriefing", back_populates="news_items")


class Company(Base):
    """Company master data"""
    
    __tablename__ = "companies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    ticker: Mapped[str | None] = mapped_column(String(20))
    type: Mapped[str | None] = mapped_column(String(100))  # hyperscaler | supplier | operator
    last_active: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    projects: Mapped[List["ProjectCompany"]] = relationship(
        "ProjectCompany", back_populates="company", cascade="all, delete-orphan"
    )


class DataCenterProject(Base):
    """Data center project from intelligence feed"""
    
    __tablename__ = "dc_projects"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Location
    city: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Project details
    project_type: Mapped[str] = mapped_column(String(100), nullable=False)
    stage: Mapped[str] = mapped_column(String(100), nullable=False)
    investment_usd_m: Mapped[float | None] = mapped_column(Float)
    capacity_mw: Mapped[float | None] = mapped_column(Float)
    energy_type: Mapped[str | None] = mapped_column(String(100))
    
    # Metadata
    reported_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Foreign keys
    briefing_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("daily_briefings.id"))
    briefing: Mapped["DailyBriefing"] = relationship("DailyBriefing", back_populates="projects")
    
    # Relationships
    companies: Mapped[List["ProjectCompany"]] = relationship(
        "ProjectCompany", back_populates="project", cascade="all, delete-orphan"
    )


class ProjectCompany(Base):
    """Junction table linking projects to companies with roles"""
    
    __tablename__ = "project_companies"
    __table_args__ = (
        UniqueConstraint('project_id', 'company_id', name='uq_project_company'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("dc_projects.id"), nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)  # operator | tenant | acquirer | partner
    
    # Relationships
    project: Mapped["DataCenterProject"] = relationship("DataCenterProject", back_populates="companies")
    company: Mapped["Company"] = relationship("Company", back_populates="projects")


class InfrastructureOpportunity(Base):
    """Infrastructure opportunity identified in briefing"""
    
    __tablename__ = "infrastructure_opportunities"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    companies: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    briefing_id: Mapped[int] = mapped_column(Integer, ForeignKey("daily_briefings.id"), nullable=False)
    briefing: Mapped["DailyBriefing"] = relationship("DailyBriefing", back_populates="opportunities")

"""Pydantic v2 schemas for the Infrastructure Intelligence module."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.models.infrastructure import (
    CompanyCategory,
    ConfidenceLevel,
    IndustrySegment,
    ProjectStage,
    SignalLikelihood,
    SignalType,
)


# ── Opportunity Signals ───────────────────────────────────────────────────────

class OpportunitySignalBase(BaseModel):
    signal_type: SignalType = SignalType.other
    description: str | None = None
    likelihood: SignalLikelihood = SignalLikelihood.medium
    recommended_action: str | None = None


class OpportunitySignalCreate(OpportunitySignalBase):
    project_id: int


class OpportunitySignalRead(OpportunitySignalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    created_at: datetime


class OpportunitySignalUpdate(BaseModel):
    signal_type: SignalType | None = None
    description: str | None = None
    likelihood: SignalLikelihood | None = None
    recommended_action: str | None = None


# ── Infrastructure Projects ───────────────────────────────────────────────────

class InfrastructureProjectBase(BaseModel):
    company: str = Field(..., max_length=255)
    project_name: str = Field(..., max_length=500)
    location_city: str | None = Field(None, max_length=255)
    location_country: str | None = Field(None, max_length=255)
    region: str | None = Field(None, max_length=255)
    project_type: str | None = Field(None, max_length=255)
    industry_segment: IndustrySegment = IndustrySegment.other
    investment_value: float | None = None
    capacity_mw: float | None = None
    project_stage: ProjectStage = ProjectStage.announced
    partners: list[str] = Field(default_factory=list)
    date_announced: date | None = None
    source: str | None = Field(None, max_length=500)
    confidence_level: ConfidenceLevel = ConfidenceLevel.medium
    summary: str | None = None


class InfrastructureProjectCreate(InfrastructureProjectBase):
    pass


class InfrastructureProjectUpdate(BaseModel):
    company: str | None = Field(None, max_length=255)
    project_name: str | None = Field(None, max_length=500)
    location_city: str | None = Field(None, max_length=255)
    location_country: str | None = Field(None, max_length=255)
    region: str | None = Field(None, max_length=255)
    project_type: str | None = Field(None, max_length=255)
    industry_segment: IndustrySegment | None = None
    investment_value: float | None = None
    capacity_mw: float | None = None
    project_stage: ProjectStage | None = None
    partners: list[str] | None = None
    date_announced: date | None = None
    source: str | None = Field(None, max_length=500)
    confidence_level: ConfidenceLevel | None = None
    summary: str | None = None


class InfrastructureProjectRead(InfrastructureProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    partners: list[str] = []
    created_at: datetime
    updated_at: datetime
    opportunity_signals: list[OpportunitySignalRead] = []


class InfrastructureProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    project_name: str
    location_city: str | None = None
    location_country: str | None = None
    region: str | None = None
    industry_segment: IndustrySegment
    project_stage: ProjectStage
    capacity_mw: float | None = None
    investment_value: float | None = None
    confidence_level: ConfidenceLevel
    date_announced: date | None = None
    created_at: datetime


# ── Import Payload (webhook / Grok task) ─────────────────────────────────────

class IntelligenceImportPayload(BaseModel):
    """Payload accepted by POST /api/intelligence/import (Grok webhook)."""

    company: str = Field(..., max_length=255)
    project: str = Field(..., max_length=500, alias="project_name",
                         description="Project name (also accepted as 'project')")
    location: str | None = Field(None, max_length=500,
                                  description="Free-text location; parsed into city/country/region")
    location_city: str | None = Field(None, max_length=255)
    location_country: str | None = Field(None, max_length=255)
    region: str | None = Field(None, max_length=255)
    project_type: str | None = Field(None, max_length=255)
    industry_segment: IndustrySegment = IndustrySegment.other
    capacity_mw: float | None = None
    investment_value: float | None = None
    stage: ProjectStage = Field(ProjectStage.announced, alias="project_stage",
                                 description="Stage (also accepted as 'stage')")
    partners: list[str] = Field(default_factory=list)
    date_announced: date | None = None
    source: str | None = Field(None, max_length=500)
    confidence: ConfidenceLevel = Field(ConfidenceLevel.medium, alias="confidence_level",
                                        description="Confidence (also accepted as 'confidence')")
    summary: str | None = None

    model_config = ConfigDict(populate_by_name=True)


# ── DC Companies ─────────────────────────────────────────────────────────────

class DCCompanyBase(BaseModel):
    company_name: str = Field(..., max_length=255)
    category: CompanyCategory = CompanyCategory.other
    hq_country: str | None = Field(None, max_length=255)
    stock_ticker: str | None = Field(None, max_length=20)
    website: str | None = Field(None, max_length=2048)


class DCCompanyCreate(DCCompanyBase):
    pass


class DCCompanyUpdate(BaseModel):
    category: CompanyCategory | None = None
    hq_country: str | None = Field(None, max_length=255)
    stock_ticker: str | None = Field(None, max_length=20)
    website: str | None = Field(None, max_length=2048)


class DCCompanyRead(DCCompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ── Analytics Schemas ─────────────────────────────────────────────────────────

class LeaderboardEntry(BaseModel):
    company: str
    project_count: int
    total_mw: float | None = None
    total_investment: float | None = None


class ContractorEntry(BaseModel):
    contractor: str
    project_count: int


class MomentumEntry(BaseModel):
    region: str
    score: float
    project_count: int
    total_mw: float | None = None
    total_investment: float | None = None

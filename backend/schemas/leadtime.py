"""Pydantic v2 schemas for LeadTimeItem."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.models.leadtime import EquipmentCategory

_no_ns = ConfigDict(protected_namespaces=())


class LeadTimeItemBase(BaseModel):
    model_config = _no_ns

    category: EquipmentCategory
    manufacturer: str | None = Field(None, max_length=200)
    model_ref: str | None = Field(None, max_length=200)
    description: str
    lead_weeks_min: int = Field(..., ge=0)
    lead_weeks_max: int = Field(..., ge=0)
    lead_weeks_typical: float | None = Field(None, ge=0)
    region: str | None = Field(None, max_length=100)
    notes: str | None = None
    source: str | None = Field(None, max_length=500)
    last_verified: datetime | None = None


class LeadTimeItemCreate(LeadTimeItemBase):
    model_config = _no_ns


class LeadTimeItemUpdate(BaseModel):
    model_config = _no_ns

    category: EquipmentCategory | None = None
    manufacturer: str | None = Field(None, max_length=200)
    model_ref: str | None = Field(None, max_length=200)
    description: str | None = None
    lead_weeks_min: int | None = Field(None, ge=0)
    lead_weeks_max: int | None = Field(None, ge=0)
    lead_weeks_typical: float | None = Field(None, ge=0)
    region: str | None = Field(None, max_length=100)
    notes: str | None = None
    source: str | None = Field(None, max_length=500)
    last_verified: datetime | None = None


class LeadTimeItemRead(LeadTimeItemBase):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    created_at: datetime
    updated_at: datetime

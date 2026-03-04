"""Pydantic v2 schemas for ProcurementFramework."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.models.framework import FrameworkStatus


class ProcurementFrameworkBase(BaseModel):
    name: str = Field(..., max_length=500)
    authority: str = Field(..., max_length=500)
    reference: str | None = Field(None, max_length=200)
    categories: str | None = None  # JSON list
    status: FrameworkStatus = FrameworkStatus.active
    start_date: date | None = None
    expiry_date: date | None = None
    url: str | None = Field(None, max_length=1000)
    region: str | None = Field(None, max_length=200)
    notes: str | None = None
    we_are_listed: bool = False
    lot_numbers: str | None = None  # JSON list


class ProcurementFrameworkCreate(ProcurementFrameworkBase):
    pass


class ProcurementFrameworkUpdate(BaseModel):
    name: str | None = Field(None, max_length=500)
    authority: str | None = Field(None, max_length=500)
    reference: str | None = Field(None, max_length=200)
    categories: str | None = None
    status: FrameworkStatus | None = None
    start_date: date | None = None
    expiry_date: date | None = None
    url: str | None = Field(None, max_length=1000)
    region: str | None = Field(None, max_length=200)
    notes: str | None = None
    we_are_listed: bool | None = None
    lot_numbers: str | None = None


class ProcurementFrameworkRead(ProcurementFrameworkBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

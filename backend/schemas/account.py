"""Pydantic v2 schemas for Account, Contact, and TriggerSignal."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.models.account import AccountType, InfluenceLevel, SignalStatus, SignalType


# ── Account ──────────────────────────────────────────────────────────────────

class AccountBase(BaseModel):
    name: str = Field(..., max_length=255)
    type: AccountType
    stage: str | None = Field(None, max_length=100)
    tier_target: str | None = Field(None, max_length=50)
    location: str | None = Field(None, max_length=255)
    website: str | None = Field(None, max_length=2048)
    logo_url: str | None = Field(None, max_length=2048)
    tags: str | None = Field(None, max_length=500)
    annual_revenue: float | None = None
    notes: str | None = None


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    type: AccountType | None = None
    stage: str | None = Field(None, max_length=100)
    tier_target: str | None = Field(None, max_length=50)
    location: str | None = Field(None, max_length=255)
    website: str | None = Field(None, max_length=2048)
    logo_url: str | None = Field(None, max_length=2048)
    tags: str | None = Field(None, max_length=500)
    annual_revenue: float | None = None
    notes: str | None = None


class AccountRead(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ── Contact ───────────────────────────────────────────────────────────────────

class ContactBase(BaseModel):
    account_id: int
    name: str = Field(..., max_length=255)
    role: str | None = Field(None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    influence_level: InfluenceLevel | None = None
    notes: str | None = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    role: str | None = Field(None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    influence_level: InfluenceLevel | None = None
    notes: str | None = None


class ContactRead(ContactBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ── TriggerSignal ─────────────────────────────────────────────────────────────

class TriggerSignalBase(BaseModel):
    account_id: int
    signal_type: SignalType
    title: str = Field(..., max_length=255)
    description: str | None = None
    source_url: str | None = Field(None, max_length=2048)
    status: SignalStatus = SignalStatus.new


class TriggerSignalCreate(TriggerSignalBase):
    pass


class TriggerSignalUpdate(BaseModel):
    signal_type: SignalType | None = None
    title: str | None = Field(None, max_length=255)
    description: str | None = None
    source_url: str | None = Field(None, max_length=2048)
    status: SignalStatus | None = None


class TriggerSignalRead(TriggerSignalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    detected_at: datetime

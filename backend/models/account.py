"""Account, Contact, and TriggerSignal SQLAlchemy models."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class AccountType(str, enum.Enum):
    operator = "operator"
    hyperscaler = "hyperscaler"
    developer = "developer"
    colo = "colo"
    enterprise = "enterprise"


class InfluenceLevel(str, enum.Enum):
    decision_maker = "decision_maker"
    influencer = "influencer"
    gatekeeper = "gatekeeper"


class SignalType(str, enum.Enum):
    planning = "planning"
    grid = "grid"
    land_acquisition = "land_acquisition"
    hiring_spike = "hiring_spike"
    framework_award = "framework_award"
    roadworks = "roadworks"
    new_build = "new_build"
    expansion = "expansion"
    cancellation = "cancellation"
    acquisition = "acquisition"
    energy_deal = "energy_deal"
    supply_chain_risk = "supply_chain_risk"


class SignalStatus(str, enum.Enum):
    new = "new"
    actioned = "actioned"
    dismissed = "dismissed"


class Account(Base):
    """Represents a target client organisation."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[AccountType] = mapped_column(Enum(AccountType), nullable=False)
    stage: Mapped[str | None] = mapped_column(String(100))
    tier_target: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(2048))
    logo_url: Mapped[str | None] = mapped_column(String(2048))
    tags: Mapped[str | None] = mapped_column(String(500))
    annual_revenue: Mapped[float | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )

    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", back_populates="account", cascade="all, delete-orphan"
    )
    trigger_signals: Mapped[list["TriggerSignal"]] = relationship(
        "TriggerSignal", back_populates="account", cascade="all, delete-orphan"
    )
    opportunities: Mapped[list] = relationship(
        "Opportunity", back_populates="account", cascade="all, delete-orphan"
    )
    call_intelligence_records: Mapped[list] = relationship(
        "CallIntelligence", back_populates="account"
    )
    signal_events: Mapped[list] = relationship(
        "SignalEvent", back_populates="account"
    )


class Contact(Base):
    """A stakeholder contact linked to an account."""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    influence_level: Mapped[InfluenceLevel | None] = mapped_column(Enum(InfluenceLevel))
    notes: Mapped[str | None] = mapped_column(Text)

    account: Mapped["Account"] = relationship("Account", back_populates="contacts")


class TriggerSignal(Base):
    """An intelligence signal that may indicate an opportunity."""

    __tablename__ = "trigger_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    signal_type: Mapped[SignalType] = mapped_column(Enum(SignalType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    status: Mapped[SignalStatus] = mapped_column(
        Enum(SignalStatus), default=SignalStatus.new, server_default="new"
    )

    account: Mapped["Account"] = relationship("Account", back_populates="trigger_signals")

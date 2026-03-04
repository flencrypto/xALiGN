"""ProcurementFramework SQLAlchemy model – framework & procurement tracker."""

import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class FrameworkStatus(str, enum.Enum):
    active = "active"
    expiring_soon = "expiring_soon"
    expired = "expired"
    pending = "pending"
    not_listed = "not_listed"


class ProcurementFramework(Base):
    """A public procurement framework or dynamic purchasing system (DPS)."""

    __tablename__ = "procurement_frameworks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    authority: Mapped[str] = mapped_column(String(500), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(200), index=True)
    categories: Mapped[str | None] = mapped_column(Text)  # JSON list of category strings
    status: Mapped[FrameworkStatus] = mapped_column(
        Enum(FrameworkStatus), default=FrameworkStatus.active, server_default="active"
    )
    start_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    url: Mapped[str | None] = mapped_column(String(1000))
    region: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    we_are_listed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    lot_numbers: Mapped[str | None] = mapped_column(Text)  # JSON list of lot strings
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )

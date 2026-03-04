"""LeadTimeItem SQLAlchemy model – equipment lead-time intelligence database."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class EquipmentCategory(str, enum.Enum):
    switchgear = "switchgear"
    ups = "ups"
    chiller = "chiller"
    generator = "generator"
    pdu = "pdu"
    crac = "crac"
    transformer = "transformer"
    busbar = "busbar"
    battery = "battery"
    other = "other"


class LeadTimeItem(Base):
    """Equipment lead-time intelligence entry."""

    __tablename__ = "lead_time_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category: Mapped[EquipmentCategory] = mapped_column(
        Enum(EquipmentCategory), nullable=False, index=True
    )
    manufacturer: Mapped[str | None] = mapped_column(String(200))
    model_ref: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    lead_weeks_min: Mapped[int] = mapped_column(Integer, nullable=False)
    lead_weeks_max: Mapped[int] = mapped_column(Integer, nullable=False)
    lead_weeks_typical: Mapped[float | None] = mapped_column(Float)
    region: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(500))
    last_verified: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )

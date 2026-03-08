"""Tender Award and Call Intelligence SQLAlchemy models."""

from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class TenderAward(Base):
    """Stores a structured tender award intelligence record."""

    __tablename__ = "tender_awards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    authority_name: Mapped[str] = mapped_column(String(500), nullable=False)
    winning_company: Mapped[str] = mapped_column(String(500), nullable=False)
    contract_value: Mapped[float | None] = mapped_column(Numeric(20, 2))
    contract_currency: Mapped[str | None] = mapped_column(String(10))
    scope_summary: Mapped[str | None] = mapped_column(Text)
    cpv_codes: Mapped[str | None] = mapped_column(Text)          # stored as JSON array string
    award_date: Mapped[str | None] = mapped_column(String(50))
    duration_months: Mapped[int | None] = mapped_column(Integer)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    framework: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    region: Mapped[str | None] = mapped_column(String(255))
    competitors: Mapped[str | None] = mapped_column(Text)        # stored as JSON array string
    mw_capacity: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )


class CallIntelligence(Base):
    """Stores transcription and extracted signals from a recorded call."""

    __tablename__ = "call_intelligence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    company_name: Mapped[str | None] = mapped_column(String(500))
    executive_name: Mapped[str | None] = mapped_column(String(255))
    audio_file_url: Mapped[str | None] = mapped_column(String(2048))
    call_date: Mapped[datetime | None] = mapped_column(DateTime)
    transcript: Mapped[str | None] = mapped_column(Text)
    sentiment_score: Mapped[float | None] = mapped_column(Float)
    competitor_mentions: Mapped[str | None] = mapped_column(Text)  # JSON array string
    budget_signals: Mapped[str | None] = mapped_column(Text)       # JSON array string
    timeline_mentions: Mapped[str | None] = mapped_column(Text)    # JSON array string
    risk_language: Mapped[str | None] = mapped_column(Text)        # JSON array string
    objection_categories: Mapped[str | None] = mapped_column(Text) # JSON array string
    next_steps: Mapped[str | None] = mapped_column(Text)
    key_points: Mapped[str | None] = mapped_column(Text)            # JSON array of key-point dicts
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    account: Mapped["Account"] = relationship("Account", back_populates="call_intelligence_records")

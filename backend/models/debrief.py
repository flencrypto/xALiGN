"""BidDebrief SQLAlchemy model – captures post-bid outcome data for learning."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class DebriefOutcome(str, enum.Enum):
    won = "won"
    lost = "lost"
    withdrawn = "withdrawn"
    no_award = "no_award"


class BidDebrief(Base):
    """Post-bid debrief capturing lessons learned and competitive intelligence."""

    __tablename__ = "bid_debriefs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bid_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bids.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    outcome: Mapped[DebriefOutcome] = mapped_column(Enum(DebriefOutcome), nullable=False)

    # Scoring
    our_score: Mapped[float | None] = mapped_column(Float)
    winner_score: Mapped[float | None] = mapped_column(Float)
    our_price: Mapped[float | None] = mapped_column(Float)
    winner_price: Mapped[float | None] = mapped_column(Float)
    evaluation_criteria: Mapped[str | None] = mapped_column(Text)  # JSON list

    # Feedback
    client_feedback: Mapped[str | None] = mapped_column(Text)
    strengths: Mapped[str | None] = mapped_column(Text)
    weaknesses: Mapped[str | None] = mapped_column(Text)
    winning_company: Mapped[str | None] = mapped_column(String(255))

    # Learning loop
    lessons_learned: Mapped[str | None] = mapped_column(Text)
    process_improvements: Mapped[str | None] = mapped_column(Text)
    bid_manager: Mapped[str | None] = mapped_column(String(255))

    debrief_date: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )

    bid: Mapped["Bid"] = relationship("Bid", back_populates="debrief")  # type: ignore[name-defined]

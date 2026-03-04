"""Pydantic v2 schemas for BidDebrief."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.models.debrief import DebriefOutcome


class BidDebriefBase(BaseModel):
    bid_id: int
    outcome: DebriefOutcome
    our_score: float | None = None
    winner_score: float | None = None
    our_price: float | None = None
    winner_price: float | None = None
    evaluation_criteria: str | None = None
    client_feedback: str | None = None
    strengths: str | None = None
    weaknesses: str | None = None
    winning_company: str | None = Field(None, max_length=255)
    lessons_learned: str | None = None
    process_improvements: str | None = None
    bid_manager: str | None = Field(None, max_length=255)
    debrief_date: datetime | None = None


class BidDebriefCreate(BidDebriefBase):
    pass


class BidDebriefUpdate(BaseModel):
    outcome: DebriefOutcome | None = None
    our_score: float | None = None
    winner_score: float | None = None
    our_price: float | None = None
    winner_price: float | None = None
    evaluation_criteria: str | None = None
    client_feedback: str | None = None
    strengths: str | None = None
    weaknesses: str | None = None
    winning_company: str | None = Field(None, max_length=255)
    lessons_learned: str | None = None
    process_improvements: str | None = None
    bid_manager: str | None = Field(None, max_length=255)
    debrief_date: datetime | None = None


class BidDebriefRead(BidDebriefBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class LearningInsight(BaseModel):
    """Aggregated insight from multiple bid debriefs."""
    total_bids_debriefed: int
    wins: int
    losses: int
    win_rate_pct: float
    avg_our_score: float | None
    avg_winner_score: float | None
    avg_price_gap_pct: float | None
    top_strengths: list[str]
    top_weaknesses: list[str]
    common_winners: list[str]

"""Bid debrief capture + learning loop router.

Endpoints:
  POST   /api/v1/bids/{bid_id}/debrief           – Create debrief for a bid
  GET    /api/v1/bids/{bid_id}/debrief           – Get debrief for a bid
  PATCH  /api/v1/bids/{bid_id}/debrief           – Update debrief
  DELETE /api/v1/bids/{bid_id}/debrief           – Delete debrief
  GET    /api/v1/debriefs                        – List all debriefs
  GET    /api/v1/debriefs/insights               – Learning loop insights
"""

import logging
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.bid import Bid
from backend.models.debrief import BidDebrief, DebriefOutcome
from backend.schemas.debrief import (
    BidDebriefCreate,
    BidDebriefRead,
    BidDebriefUpdate,
    LearningInsight,
)

logger = logging.getLogger("align.debriefs")

router = APIRouter(tags=["Bid Debriefs"])


# ── Per-bid debrief endpoints ──────────────────────────────────────────────────

@router.post(
    "/bids/{bid_id}/debrief",
    response_model=BidDebriefRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a bid debrief",
)
def create_debrief(bid_id: int, payload: BidDebriefCreate, db: Session = Depends(get_db)):
    """Create a post-bid debrief record. Only one debrief per bid is allowed."""
    if not db.get(Bid, bid_id):
        raise HTTPException(status_code=404, detail="Bid not found")
    existing = db.query(BidDebrief).filter(BidDebrief.bid_id == bid_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Debrief already exists for this bid")
    data = payload.model_dump()
    data["bid_id"] = bid_id
    obj = BidDebrief(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get(
    "/bids/{bid_id}/debrief",
    response_model=BidDebriefRead,
    summary="Get the debrief for a bid",
)
def get_debrief(bid_id: int, db: Session = Depends(get_db)):
    if not db.get(Bid, bid_id):
        raise HTTPException(status_code=404, detail="Bid not found")
    obj = db.query(BidDebrief).filter(BidDebrief.bid_id == bid_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Debrief not found")
    return obj


@router.patch(
    "/bids/{bid_id}/debrief",
    response_model=BidDebriefRead,
    summary="Update a bid debrief",
)
def update_debrief(bid_id: int, payload: BidDebriefUpdate, db: Session = Depends(get_db)):
    if not db.get(Bid, bid_id):
        raise HTTPException(status_code=404, detail="Bid not found")
    obj = db.query(BidDebrief).filter(BidDebrief.bid_id == bid_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Debrief not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete(
    "/bids/{bid_id}/debrief",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a bid debrief",
)
def delete_debrief(bid_id: int, db: Session = Depends(get_db)):
    if not db.get(Bid, bid_id):
        raise HTTPException(status_code=404, detail="Bid not found")
    obj = db.query(BidDebrief).filter(BidDebrief.bid_id == bid_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Debrief not found")
    db.delete(obj)
    db.commit()


# ── Global debrief list ────────────────────────────────────────────────────────

@router.get(
    "/debriefs",
    response_model=list[BidDebriefRead],
    summary="List all bid debriefs",
)
def list_debriefs(
    outcome: DebriefOutcome | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(BidDebrief)
    if outcome is not None:
        q = q.filter(BidDebrief.outcome == outcome)
    return q.order_by(BidDebrief.created_at.desc()).offset(skip).limit(limit).all()


# ── Learning loop insights ────────────────────────────────────────────────────

@router.get(
    "/debriefs/insights",
    response_model=LearningInsight,
    summary="Learning loop – aggregated insights from all debriefs",
)
def debrief_insights(db: Session = Depends(get_db)):
    """
    Aggregate debrief data into actionable learning insights.

    Reports win rate, average score / price gaps, common strengths/weaknesses,
    and frequent winning competitors.
    """
    debriefs: list[BidDebrief] = db.query(BidDebrief).all()

    total = len(debriefs)
    wins = sum(1 for d in debriefs if d.outcome == DebriefOutcome.won)
    losses = sum(1 for d in debriefs if d.outcome == DebriefOutcome.lost)
    win_rate = round((wins / total * 100), 1) if total else 0.0

    # Average scores
    scores_ours = [d.our_score for d in debriefs if d.our_score is not None]
    scores_winner = [d.winner_score for d in debriefs if d.winner_score is not None]
    avg_our = round(sum(scores_ours) / len(scores_ours), 2) if scores_ours else None
    avg_win = round(sum(scores_winner) / len(scores_winner), 2) if scores_winner else None

    # Price gap
    price_gaps: list[float] = []
    for d in debriefs:
        if d.our_price and d.winner_price and d.winner_price > 0:
            gap = (d.our_price - d.winner_price) / d.winner_price * 100
            price_gaps.append(gap)
    avg_price_gap = round(sum(price_gaps) / len(price_gaps), 1) if price_gaps else None

    # Top strengths / weaknesses (simple word frequency)
    def _top_terms(texts: list[str | None], n: int = 5) -> list[str]:
        words: list[str] = []
        for t in texts:
            if t:
                words.extend(t.lower().split())
        counter = Counter(words)
        stopwords = {"the", "a", "an", "of", "and", "to", "in", "our", "was", "is", "for", "on"}
        filtered = [(w, c) for w, c in counter.most_common(50) if w not in stopwords and len(w) > 3]
        return [w for w, _ in filtered[:n]]

    top_strengths = _top_terms([d.strengths for d in debriefs])
    top_weaknesses = _top_terms([d.weaknesses for d in debriefs])

    # Common winning competitors
    winners_counter: Counter = Counter(
        d.winning_company for d in debriefs if d.winning_company and d.outcome == DebriefOutcome.lost
    )
    common_winners = [w for w, _ in winners_counter.most_common(5)]

    return LearningInsight(
        total_bids_debriefed=total,
        wins=wins,
        losses=losses,
        win_rate_pct=win_rate,
        avg_our_score=avg_our,
        avg_winner_score=avg_win,
        avg_price_gap_pct=avg_price_gap,
        top_strengths=top_strengths,
        top_weaknesses=top_weaknesses,
        common_winners=common_winners,
    )

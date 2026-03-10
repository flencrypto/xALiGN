"""
Mathematical scoring engine for Bid Intelligence.

Implements:
  - Competitive Pricing Index (CPI)
  - Win Probability Score
  - Relationship Timing Score
  - Expansion Activity Score
"""

import math
import statistics
from typing import Optional

from sqlalchemy.orm import Session

from backend.models.tender import TenderAward


# ── Competitive Pricing Index ─────────────────────────────────────────────────

def compute_cpi(
    db: Session,
    company: str,
    region_factor: float = 1.0,
) -> dict:
    """
    Compute the Competitive Pricing Index (CPI) for a company.

    CPI = (AdjPPMW - MarketMean) / MarketStdDev
      where AdjPPMW = (contract_value / mw_capacity) / region_factor

    Returns dict with cpi, avg_price_per_mw, award_count, total_value, interpretation.
    """
    # Company awards with MW data
    company_awards = (
        db.query(TenderAward)
        .filter(
            TenderAward.winning_company.ilike(f"%{company}%"),
            TenderAward.mw_capacity.isnot(None),
            TenderAward.mw_capacity > 0,
            TenderAward.contract_value.isnot(None),
        )
        .all()
    )

    # All awards with MW data for market baseline
    all_awards = (
        db.query(TenderAward)
        .filter(
            TenderAward.mw_capacity.isnot(None),
            TenderAward.mw_capacity > 0,
            TenderAward.contract_value.isnot(None),
        )
        .all()
    )

    total_value = sum(float(a.contract_value) for a in company_awards)
    award_count = len(company_awards)

    # Compute per-MW prices for company
    company_ppmw_list = [
        float(a.contract_value) / float(a.mw_capacity)
        for a in company_awards
    ]

    avg_ppmw = statistics.mean(company_ppmw_list) if company_ppmw_list else None
    adj_ppmw = (avg_ppmw / region_factor) if avg_ppmw is not None else None

    # Market baseline
    all_ppmw_list = [
        float(a.contract_value) / float(a.mw_capacity)
        for a in all_awards
    ]

    cpi = None
    interpretation = "Insufficient data"

    if adj_ppmw is not None and len(all_ppmw_list) >= 2:
        market_mean = statistics.mean(all_ppmw_list)
        market_std = statistics.stdev(all_ppmw_list)
        if market_std > 0:
            cpi = (adj_ppmw - market_mean) / market_std
            if cpi < -0.5:
                interpretation = "Aggressive pricing (below market)"
            elif cpi > 0.5:
                interpretation = "Premium pricing (above market)"
            else:
                interpretation = "Market-rate pricing"
        else:
            cpi = 0.0
            interpretation = "Market-rate pricing (insufficient variance)"

    return {
        "company": company,
        "award_count": award_count,
        "total_value": total_value,
        "avg_price_per_mw": avg_ppmw,
        "cpi": cpi,
        "interpretation": interpretation,
    }


# ── Win Probability Score ─────────────────────────────────────────────────────

def compute_win_probability(
    historical_win_rate: float,
    cpi: float | None,
    expansion_activity_score: float,
    hiring_velocity: float,
    risk_score: float,
) -> float:
    """
    WinScore = 0.30*W + 0.20*(1 - |CPI_norm|) + 0.20*E + 0.15*H + 0.15*R

    All inputs normalised to [0, 1]. Returns float in [0, 1].
    """
    # Normalise CPI: clamp |CPI| to [0, 3], then invert
    cpi_norm = _cpi_norm(cpi)

    score = (
        0.30 * historical_win_rate
        + 0.20 * cpi_norm
        + 0.20 * expansion_activity_score
        + 0.15 * hiring_velocity
        + 0.15 * risk_score
    )
    return round(min(max(score, 0.0), 1.0), 4)


def _cpi_norm(cpi: float | None) -> float:
    """Normalise CPI to [0, 1] contribution (1 = market-rate, 0 = extreme outlier)."""
    if cpi is None:
        return 0.5
    return 1.0 - min(abs(cpi) / 3.0, 1.0)


# ── Relationship Timing Score ─────────────────────────────────────────────────

# Decay constants (λ) per signal type – higher = faster decay.
# Exported so callers (e.g. routers) can use the same values without duplication.
SIGNAL_DECAY: dict[str, float] = {
    "contract_win": 0.05,
    "expansion": 0.04,
    "charity_event": 0.07,
    "conference": 0.06,
    "executive_post": 0.10,
    "new_role": 0.03,
    "funding_round": 0.04,
}
# Keep private alias for backward compatibility inside this module
_SIGNAL_DECAY = SIGNAL_DECAY

# Importance weights per signal type.
# Exported so callers can use the same values without duplication.
SIGNAL_IMPORTANCE: dict[str, float] = {
    "contract_win": 1.0,
    "expansion": 0.9,
    "charity_event": 0.5,
    "conference": 0.6,
    "executive_post": 0.4,
    "new_role": 0.8,
    "funding_round": 0.9,
}
_SIGNAL_IMPORTANCE = SIGNAL_IMPORTANCE

_CONTACT_THRESHOLD = 0.30


def compute_relationship_timing(
    events: list[str],
    days_since: list[int],
) -> dict:
    """
    Compute total touchpoint score using exponential decay.

    SignalWeight(t) = e^(-λ * days_since_event)
    TotalScore = Σ (SignalWeight_i × Importance_i)

    Returns score and whether to recommend contact.
    """
    total_score = 0.0
    for event, days in zip(events, days_since):
        lam = _SIGNAL_DECAY.get(event, 0.05)
        importance = _SIGNAL_IMPORTANCE.get(event, 0.5)
        weight = math.exp(-lam * days) * importance
        total_score += weight

    # Normalise loosely: cap at 3.0 → scale to [0, 1]
    normalised = min(total_score / 3.0, 1.0)
    return {
        "timing_score": round(normalised, 4),
        "recommend_contact": normalised >= _CONTACT_THRESHOLD,
    }


# ── Expansion Activity Score ──────────────────────────────────────────────────

def compute_expansion_activity_score(
    signal_events: list[str],
    days_since_events: list[int],
    hiring_count: int = 0,
    new_office_openings: int = 0,
    recent_acquisitions: int = 0,
) -> dict:
    """
    Compute a normalised Expansion Activity Score (EAS) in [0, 1].

    EAS combines:
      - Time-decayed signal events (expansion-type signals weighted higher)
      - Hiring velocity proxy (hiring_count clamped to 50)
      - Physical expansion indicators (office openings, acquisitions)

    Returns a dict with keys:
      - ``score``: float in [0, 1]
      - ``signal_contribution``: weighted signal timing component
      - ``hiring_contribution``: weighted hiring component
      - ``physical_contribution``: weighted physical expansion component
    """
    # Time-decayed signal contribution (reuse relationship timing logic)
    timing = compute_relationship_timing(signal_events, days_since_events)
    signal_contribution = round(timing["timing_score"] * 0.50, 4)

    # Hiring contribution: 50+ roles ≈ maximum signal (cap at 1.0)
    hiring_contribution = round(min(hiring_count / 50.0, 1.0) * 0.25, 4)

    # Physical expansion contribution: each opening/acquisition scores 0.1 (cap at 1.0)
    expansion_events = new_office_openings + recent_acquisitions
    physical_contribution = round(min(expansion_events * 0.10, 1.0) * 0.25, 4)

    score = round(min(max(signal_contribution + hiring_contribution + physical_contribution, 0.0), 1.0), 4)

    return {
        "score": score,
        "signal_contribution": signal_contribution,
        "hiring_contribution": hiring_contribution,
        "physical_contribution": physical_contribution,
    }



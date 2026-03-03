"""Scoring engine for ContractGHOST.

Implements:
  - Competitive Pricing Index (CPI)
  - Expansion Activity Score
  - Relationship Timing Score (exponential decay)
  - Win Probability Model
"""

import math
from datetime import datetime, timezone


# ── Competitive Pricing Index (CPI) ──────────────────────────────────────────

def price_per_mw(contract_value: float, capacity_mw: float) -> float | None:
    """Return price-per-MW (PPMW) for a contract award.

    Returns None if capacity_mw is zero or negative.
    """
    if capacity_mw <= 0:
        return None
    return contract_value / capacity_mw


def competitive_pricing_index(
    ppmw: float,
    market_mean: float,
    market_std: float,
) -> float | None:
    """Return a z-score CPI: (PPMW - mean) / std.

    Negative values → below market (aggressive pricing).
    Positive values → above market (premium pricing).
    Returns None if std is zero.
    """
    if market_std <= 0:
        return None
    return (ppmw - market_mean) / market_std


# ── Expansion Activity Score ──────────────────────────────────────────────────

# Default weights for expansion signals (sum to 1.0)
_EXPANSION_WEIGHTS = {
    "capex_change": 0.30,
    "new_regions": 0.25,
    "hiring_growth": 0.20,
    "facility_expansion": 0.15,
    "ai_investment": 0.10,
}


def expansion_activity_score(
    capex_change: float = 0.0,
    new_regions: float = 0.0,
    hiring_growth: float = 0.0,
    facility_expansion: float = 0.0,
    ai_investment: float = 0.0,
) -> float:
    """Return a 0–10 weighted expansion activity score.

    Each input should be in the range 0–10 representing signal intensity.
    """
    w = _EXPANSION_WEIGHTS
    raw = (
        w["capex_change"] * capex_change
        + w["new_regions"] * new_regions
        + w["hiring_growth"] * hiring_growth
        + w["facility_expansion"] * facility_expansion
        + w["ai_investment"] * ai_investment
    )
    return min(max(raw, 0.0), 10.0)


# ── Relationship Timing Score ─────────────────────────────────────────────────

def signal_decayed_weight(
    strength: float,
    decay_factor: float,
    event_date: datetime,
    reference_date: datetime | None = None,
) -> float:
    """Compute the decayed weight for a single signal.

    Weight = strength × e^(−λ × days_since_event)
    """
    if reference_date is None:
        reference_date = datetime.now(timezone.utc)

    # Normalise both to UTC-aware datetimes
    if event_date.tzinfo is None:
        event_date = event_date.replace(tzinfo=timezone.utc)
    if reference_date.tzinfo is None:
        reference_date = reference_date.replace(tzinfo=timezone.utc)

    days = max((reference_date - event_date).total_seconds() / 86400, 0)
    return strength * math.exp(-decay_factor * days)


def relationship_timing_score(signals: list[dict]) -> float:
    """Aggregate decayed signal weights into a relationship timing score.

    Each dict must have keys: strength, decay_factor, event_date (datetime).
    Returns a non-negative float; higher values indicate better timing.
    """
    total = 0.0
    for s in signals:
        total += signal_decayed_weight(
            strength=float(s.get("strength", 1.0)),
            decay_factor=float(s.get("decay_factor", 0.1)),
            event_date=s["event_date"],
        )
    return round(total, 4)


def outreach_recommendation(score: float) -> str:
    """Return a plain-English recommendation based on the timing score."""
    if score >= 5.0:
        return "IMMEDIATE – Multiple strong recent signals. Contact now."
    if score >= 2.0:
        return "SOON – Moderate signal activity. Initiate contact within the week."
    if score >= 0.5:
        return "MONITOR – Signals present but decaying. Stay watchful."
    return "LOW – Signal activity is minimal. Continue monitoring."


# ── Win Probability Model ─────────────────────────────────────────────────────

def win_probability_score(
    historical_win_rate: float = 0.0,
    expansion_score: float = 0.0,
    hiring_velocity: float = 0.0,
    price_alignment: float = 0.0,
    risk_score: float = 0.0,
) -> float:
    """Return a 0–100 win probability score.

    Weights from spec:
      0.30 HistoricalWinRate
      0.20 ExpansionScore
      0.15 HiringVelocity
      0.15 PriceAlignment
      0.20 RiskScore (inverted – lower risk = higher score)
    """
    # Normalise inputs to 0–100 range
    score = (
        0.30 * min(max(historical_win_rate, 0.0), 100.0)
        + 0.20 * min(max(expansion_score * 10, 0.0), 100.0)  # expansion_score is 0-10, normalise to 0-100
        + 0.15 * min(max(hiring_velocity, 0.0), 100.0)
        + 0.15 * min(max(price_alignment, 0.0), 100.0)
        + 0.20 * min(max(100.0 - risk_score, 0.0), 100.0)  # lower risk → higher score
    )
    return round(min(max(score, 0.0), 100.0), 2)

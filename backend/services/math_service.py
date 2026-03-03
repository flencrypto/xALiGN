"""Deterministic math service for pricing and competitive analysis.

All calculations are performed without any LLM involvement.
"""

import statistics


def calculate_price_per_mw(contract_value: float, capacity_mw: float) -> float:
    """Return price per MW; raises ValueError if capacity is zero or negative."""
    if capacity_mw <= 0:
        raise ValueError("capacity_mw must be greater than zero")
    return contract_value / capacity_mw


def calculate_average_contract_value(values: list[float]) -> float:
    """Return the arithmetic mean of a list of contract values."""
    if not values:
        raise ValueError("values list must not be empty")
    return statistics.mean(values)


def calculate_competitive_pricing_index(price: float, market_avg: float) -> float:
    """Return CPI = price / market_avg.

    1.0 means at market price, <1 means below market (aggressive), >1 means above market (premium).
    """
    if market_avg <= 0:
        raise ValueError("market_avg must be greater than zero")
    return price / market_avg


def calculate_percentile_position(value: float, benchmark_values: list[float]) -> float:
    """Return the percentile position (0.0–1.0) of *value* within *benchmark_values*.

    Uses linear interpolation over the sorted benchmark list.
    """
    if not benchmark_values:
        raise ValueError("benchmark_values must not be empty")
    sorted_benchmarks = sorted(benchmark_values)
    n = len(sorted_benchmarks)
    below = sum(1 for v in sorted_benchmarks if v < value)
    equal = sum(1 for v in sorted_benchmarks if v == value)
    # mid-point convention: count all below plus half of equal
    return (below + 0.5 * equal) / n


def normalize_price(price: float, regional_factor: float) -> float:
    """Return price normalized by a regional cost factor.

    A factor > 1 indicates a more expensive region; < 1 a cheaper region.
    """
    if regional_factor <= 0:
        raise ValueError("regional_factor must be greater than zero")
    return price / regional_factor

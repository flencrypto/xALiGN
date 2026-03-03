"""AI Governance Logger and validation utilities.

Captures every AI worker invocation for audit, confidence scoring,
hallucination detection, and human-review gating.
Uses only Python stdlib – no external dependencies.
"""

import hashlib
import logging
import os
from collections import deque
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("contractghost.governance")

# In-memory circular buffer (last 1 000 entries)
_LOG_BUFFER: deque[dict[str, Any]] = deque(maxlen=1000)

# ── Configurable thresholds (overridable via env) ─────────────────────────────
_CONFIDENCE_THRESHOLD = float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.65"))
_REVIEW_THRESHOLD = float(os.getenv("AI_REVIEW_THRESHOLD", "0.5"))
_MAX_CONTRACT_VALUE = float(os.getenv("AI_MAX_CONTRACT_VALUE_GBP", "10000000000"))
_MAX_CAPEX_GROWTH_PCT = float(os.getenv("AI_MAX_CAPEX_GROWTH_PCT", "500"))


# ── Prompt hashing ────────────────────────────────────────────────────────────

def prompt_version_hash(system_prompt: str) -> str:
    """Return the first 16 hex chars of the SHA-256 digest of a system prompt."""
    return hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()[:16]


# ── Composite confidence scoring ──────────────────────────────────────────────

def composite_confidence(
    evidence_strength: float,
    source_credibility: float,
    cross_model_agreement: float,
    data_completeness: float,
) -> float:
    """Weighted composite: 0.4*evidence + 0.2*credibility + 0.2*agreement + 0.2*completeness."""
    score = (
        0.4 * evidence_strength
        + 0.2 * source_credibility
        + 0.2 * cross_model_agreement
        + 0.2 * data_completeness
    )
    return round(min(max(score, 0.0), 1.0), 4)


# Alias for backward compatibility
compute_composite_confidence = composite_confidence


# ── Hallucination / anomaly detection ────────────────────────────────────────

def check_numeric_anomalies(result: dict[str, Any]) -> list[str]:
    """Return a list of anomaly flag strings for any suspicious numeric values."""
    flags: list[str] = []
    cv = result.get("average_contract_value") or result.get("contract_value")
    if cv is not None:
        try:
            if float(cv) > _MAX_CONTRACT_VALUE:
                flags.append(
                    f"contract_value {cv} exceeds anomaly threshold £{_MAX_CONTRACT_VALUE:,.0f}"
                )
        except (TypeError, ValueError):
            pass

    capex = result.get("capex_growth_pct")
    if capex is not None:
        try:
            if float(capex) > _MAX_CAPEX_GROWTH_PCT:
                flags.append(
                    f"capex_growth_pct {capex} exceeds anomaly threshold {_MAX_CAPEX_GROWTH_PCT}%"
                )
        except (TypeError, ValueError):
            pass

    return flags


# Alias for backward compatibility
check_numeric_sanity = check_numeric_anomalies


# ── Human review gateway ──────────────────────────────────────────────────────

def needs_human_review(confidence: float, anomaly_flags: list[str] | None = None) -> bool:
    """Return True when confidence is below the review threshold or anomalies exist."""
    if confidence < _REVIEW_THRESHOLD:
        return True
    if anomaly_flags:
        return True
    return False


# ── Citation consistency validator ────────────────────────────────────────────

def validate_citations(claimed_values: list[str], source_text: str) -> dict[str, bool]:
    """Check whether each claimed value string appears verbatim in the source text."""
    results: dict[str, bool] = {}
    for value in claimed_values:
        results[value] = str(value).lower() in source_text.lower()
    return results


# Alias for backward compatibility
validate_citation = validate_citations


# ── Governance logger ─────────────────────────────────────────────────────────

class GovernanceLogger:
    """Log every AI worker invocation to the in-memory buffer and Python logger."""

    @staticmethod
    def log(
        worker_name: str,
        model: str,
        temperature: float,
        input_tokens: int,
        output_tokens: int,
        confidence: float,
        validation_outcome: str,
        system_prompt: str = "",
        prompt_hash: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record an invocation and return the log entry dict."""
        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "worker_name": worker_name,
            "model": model,
            "temperature": temperature,
            "prompt_version_hash": prompt_hash or prompt_version_hash(system_prompt),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "confidence": confidence,
            "validation_outcome": validation_outcome,
        }
        if extra:
            entry.update(extra)

        _LOG_BUFFER.append(entry)
        logger.info(
            "AI_GOV worker=%s model=%s temp=%.2f conf=%.3f outcome=%s phash=%s",
            worker_name,
            model,
            temperature,
            confidence,
            validation_outcome,
            entry["prompt_version_hash"],
        )
        return entry

    @staticmethod
    def recent(n: int = 100) -> list[dict[str, Any]]:
        """Return the last *n* log entries (most-recent first)."""
        entries = list(_LOG_BUFFER)
        return list(reversed(entries))[:n]

    @staticmethod
    def get_recent(n: int = 100) -> list[dict[str, Any]]:
        """Alias for recent() for backward compatibility."""
        return GovernanceLogger.recent(n)

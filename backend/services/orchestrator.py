"""Master orchestrator – routes events to the appropriate AI worker.

Accepted event types:
  new_company   → Worker 1 (CompanyResearchWorker)
  new_tender    → Worker 2 (TenderAwardWorker)
  new_earnings  → Worker 4 (EarningsCallWorker)
  new_call      → Worker 7 (CallIntelWorker)
  new_signal    → Worker 9 (TrendDetectionWorker)
  new_image     → Worker 10 (ImageIntelWorker)

Duplicate suppression: processed IDs are tracked in a per-event-type
in-memory dict.  For persistent deduplication the caller should pass
a unique event_id.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from services.ai_workers import (
    CallIntelWorker,
    CompanyResearchWorker,
    EarningsCallWorker,
    ImageIntelWorker,
    TenderAwardWorker,
    TrendDetectionWorker,
)

logger = logging.getLogger("contractghost.orchestrator")

# ── In-memory duplicate tracker ───────────────────────────────────────────────
# Structure: {event_type: set_of_processed_ids}
_processed: dict[str, set[str]] = {}

_SUPPORTED_EVENTS = {
    "new_company",
    "new_tender",
    "new_earnings",
    "new_call",
    "new_signal",
    "new_image",
}


class Orchestrator:
    """Route inbound events to the correct AI worker and return an execution plan."""

    # Worker singletons (stateless – safe to share)
    _company_worker = CompanyResearchWorker()
    _tender_worker = TenderAwardWorker()
    _earnings_worker = EarningsCallWorker()
    _call_worker = CallIntelWorker()
    _trend_worker = TrendDetectionWorker()
    _image_worker = ImageIntelWorker()

    async def dispatch(
        self,
        event_type: str,
        context: dict[str, Any],
        event_id: str | None = None,
    ) -> dict[str, Any]:
        """Dispatch *event_type* with *context* to the matching worker.

        Args:
            event_type: One of the supported event type strings.
            context: Arbitrary payload forwarded to the worker.
            event_id: Optional stable ID for duplicate suppression.

        Returns:
            Execution plan dict with: event_type, worker_triggered, status,
            confidence, needs_review, timestamp, result.
        """
        if event_type not in _SUPPORTED_EVENTS:
            return self._plan(
                event_type=event_type,
                worker="none",
                status="rejected",
                confidence=0.0,
                needs_review=False,
                error=f"Unsupported event_type '{event_type}'",
            )

        # Duplicate suppression
        if event_id is not None:
            seen = _processed.setdefault(event_type, set())
            if event_id in seen:
                logger.info("Orchestrator: duplicate event_id=%s type=%s – skipped", event_id, event_type)
                return self._plan(
                    event_type=event_type,
                    worker="none",
                    status="duplicate_skipped",
                    confidence=0.0,
                    needs_review=False,
                )
            seen.add(event_id)

        worker_name, result = await self._route(event_type, context)

        confidence_keys = ("confidence", "overall_confidence", "confidence_level")
        confidence = 0.0
        for key in confidence_keys:
            val = result.get(key)
            if val is not None:
                try:
                    confidence = float(val)
                except (TypeError, ValueError):
                    continue
                break
        needs_review = bool(result.get("needs_human_review", False))

        return self._plan(
            event_type=event_type,
            worker=worker_name,
            status="completed",
            confidence=confidence,
            needs_review=needs_review,
            result=result,
        )

    def build_execution_plan(
        self,
        event_type: str,
        context: dict[str, Any],
        event_id: str | None = None,
    ) -> dict[str, Any]:
        """Synchronous wrapper for building an execution plan (without calling workers).
        
        This is a lightweight sync method that returns a plan structure without
        actually invoking async workers. Useful for testing and validation.
        """
        if event_type not in _SUPPORTED_EVENTS:
            return self._plan(
                event_type=event_type,
                worker="none",
                status="rejected",
                confidence=0.0,
                needs_review=False,
                error=f"Unsupported event_type '{event_type}'",
            )

        # Duplicate suppression
        if event_id is not None:
            seen = _processed.setdefault(event_type, set())
            if event_id in seen:
                logger.info("Orchestrator: duplicate event_id=%s type=%s – skipped", event_id, event_type)
                return self._plan(
                    event_type=event_type,
                    worker="none",
                    status="duplicate_skipped",
                    confidence=0.0,
                    needs_review=False,
                )
            seen.add(event_id)

        # Return a minimal plan without executing the worker
        worker_map = {
            "new_company": "company_deep_research",
            "new_tender": "tender_award_analysis",
            "new_earnings": "earnings_call_extraction",
            "new_call": "call_intelligence",
            "new_signal": "trend_detection",
            "new_image": "image_intelligence",
        }
        
        return self._plan(
            event_type=event_type,
            worker=worker_map.get(event_type, "none"),
            status="plan_built",
            confidence=0.0,
            needs_review=False,
        )

    async def _route(self, event_type: str, context: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Invoke the appropriate worker and return (worker_name, result)."""
        if event_type == "new_company":
            result = await self._company_worker.run(
                company_name=context.get("company_name", ""),
                context=context.get("content", ""),
            )
            return "company_deep_research", result

        if event_type == "new_tender":
            tender_data = context.get("tender_data", [context])
            result = await self._tender_worker.run(tender_data=tender_data)
            return "tender_award_analysis", result

        if event_type == "new_earnings":
            result = await self._earnings_worker.run(
                transcript=context.get("transcript", "")
            )
            return "earnings_call_extraction", result

        if event_type == "new_call":
            result = await self._call_worker.run(
                transcript=context.get("transcript", "")
            )
            return "call_intelligence", result

        if event_type == "new_signal":
            signals_text = context.get("signals_text") or str(context)
            result = await self._trend_worker.run(signals_context=signals_text)
            return "trend_detection", result

        if event_type == "new_image":
            result = await self._image_worker.run(
                image_description=context.get("description", "")
            )
            return "image_intelligence", result

        # Should not reach here given the guard above
        return "none", {"confidence": 0.0, "needs_human_review": False}

    @staticmethod
    def _plan(
        event_type: str,
        worker: str,
        status: str,
        confidence: float,
        needs_review: bool,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        plan: dict[str, Any] = {
            "event_type": event_type,
            "worker_triggered": worker,
            "status": status,
            "confidence": confidence,
            "needs_review": needs_review,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if result is not None:
            plan["result"] = result
        if error is not None:
            plan["error"] = error
        return plan

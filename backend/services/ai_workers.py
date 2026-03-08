"""AI Workers – structured intelligence extraction via xAI Grok.

Ten specialist workers, each with a fixed system prompt, temperature, and
output schema.  Workers call the Grok API directly (OpenAI-compatible) and
return strict JSON dicts.  All workers handle a missing API key gracefully.

Rules enforced here:
  - response_format={"type": "json_object"} requested on every call
  - Governance logging on every invocation
  - Numeric sanity checks via governance.check_numeric_anomalies
  - needs_human_review derived from governance.needs_human_review
"""

import json
import logging
import os
from typing import Any

import httpx

from backend.services.governance import GovernanceLogger, check_numeric_anomalies, needs_human_review

logger = logging.getLogger("align.ai_workers")

_BASE_URL = "https://api.x.ai/v1"
_DEFAULT_MODEL = os.getenv("AI_FALLBACK_MODEL", "grok-3-mini")
_TIMEOUT = 90.0


def _api_key() -> str | None:
    return os.getenv("XAI_API_KEY")


def _is_configured() -> bool:
    return bool(_api_key())


# ── Low-level API call ────────────────────────────────────────────────────────

def _extract_confidence(result: dict[str, Any]) -> float:
    """Extract confidence from a result dict, checking keys in priority order.

    Returns 0.5 (neutral) if no numeric confidence value is found, preventing
    a ValueError from propagating and discarding a valid parsed AI result.
    """
    for key in ("confidence", "overall_confidence", "confidence_level"):
        val = result.get(key)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                continue
    return 0.5


async def _call_worker(
    worker_name: str,
    system_prompt: str,
    user_content: str,
    temperature: float,
    top_p: float,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """Send a chat request and return parsed JSON dict."""
    key = _api_key()
    if not key:
        logger.warning("%s: XAI_API_KEY not set – returning empty result", worker_name)
        GovernanceLogger.log(
            worker_name=worker_name,
            model=_DEFAULT_MODEL,
            temperature=temperature,
            system_prompt=system_prompt,
            input_tokens=0,
            output_tokens=0,
            confidence=0.0,
            validation_outcome="skipped_no_api_key",
        )
        return {"confidence": 0.0, "needs_human_review": False}

    payload: dict[str, Any] = {
        "model": _DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "response_format": {"type": "json_object"},
    }

    raw_text = ""
    result: dict[str, Any] = {}
    validation_outcome = "ok"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        raw_text = data["choices"][0]["message"]["content"]

        result = json.loads(raw_text)

        # Anomaly detection
        flags = check_numeric_anomalies(result)
        if flags:
            result.setdefault("anomaly_flags", [])
            result["anomaly_flags"].extend(flags)
            validation_outcome = "anomaly_detected"

        confidence = _extract_confidence(result)
        result["needs_human_review"] = needs_human_review(confidence, flags)

    except json.JSONDecodeError:
        logger.warning("%s: non-JSON response – storing raw text", worker_name)
        result = {"raw_response": raw_text, "confidence": 0.0, "needs_human_review": True}
        validation_outcome = "json_parse_error"
        input_tokens = 0
        output_tokens = 0
        confidence = 0.0
    except Exception as exc:
        logger.error("%s failed: %s", worker_name, exc)
        # Sanitize: store only the exception type to avoid leaking API response
        # details (e.g., full HTTP error bodies) into the governance log or API responses.
        validation_outcome = f"error: {type(exc).__name__}"
        input_tokens = 0
        output_tokens = 0
        confidence = 0.0
        # Do not expose the raw exception message to callers; return a generic error.
        result = {
            "confidence": 0.0,
            "needs_human_review": True,
            "error": "internal_error",
            "message": "AI worker failed",
        }

    GovernanceLogger.log(
        worker_name=worker_name,
        model=_DEFAULT_MODEL,
        temperature=temperature,
        system_prompt=system_prompt,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        confidence=_extract_confidence(result),
        validation_outcome=validation_outcome,
    )
    return result


# ── Worker 1: Company Deep Research ──────────────────────────────────────────

_W1_SYSTEM = (
    "You are an institutional infrastructure intelligence analyst. "
    "You analyze publicly available company data and extract structured signals "
    "relevant to infrastructure expansion, capital allocation, competitive positioning "
    "and vendor opportunity. "
    "Rules: Use ONLY the provided context. Do not infer beyond evidence. "
    "If information is uncertain, mark confidence low. Return STRICT JSON. "
    "No markdown. No narrative. "
    "Extract: 1. Expansion signals 2. Capital expenditure indicators "
    "3. AI or technology growth signals 4. Hiring velocity indicators "
    "5. M&A activity 6. Strategic partnerships 7. Risk indicators "
    "8. Potential vendor opportunity indicators. "
    "For each signal include: description, evidence_source, confidence_score (0-1), "
    "impact_level (low/medium/high)."
)

_W1_SCHEMA = {
    "company_name": "",
    "expansion_signals": [],
    "capex_indicators": [],
    "technology_signals": [],
    "hiring_signals": [],
    "ma_activity": [],
    "partnerships": [],
    "risk_indicators": [],
    "vendor_opportunities": [],
    "overall_confidence": 0.0,
    "needs_human_review": False,
}


class CompanyResearchWorker:
    """Worker 1: Company Deep Research (temperature=0.15)."""

    async def run(self, company_name: str, context: str) -> dict[str, Any]:
        user_content = (
            f"Company: {company_name}\n\n"
            f"Context:\n{context[:8000]}\n\n"
            f"Return JSON matching this schema:\n{json.dumps(_W1_SCHEMA)}"
        )
        return await _call_worker(
            worker_name="company_deep_research",
            system_prompt=_W1_SYSTEM,
            user_content=user_content,
            temperature=0.15,
            top_p=0.9,
            max_tokens=2500,
        )


# ── Worker 2: Tender Award Analysis ──────────────────────────────────────────

_W2_SYSTEM = (
    "You are a public procurement intelligence analyst. "
    "From structured tender award data, analyze competitive pricing patterns. "
    "Rules: Use only provided data. No speculation. Output strict JSON. "
    "Calculate: average_contract_value, estimated_price_per_mw (if capacity provided), "
    "pricing_position (aggressive/neutral/premium), repeat_win_pattern (true/false), "
    "geographic_focus, sector_focus, anomaly_flags."
)

_W2_SCHEMA = {
    "average_contract_value": None,
    "estimated_price_per_mw": None,
    "pricing_position": "",
    "repeat_win_pattern": False,
    "geographic_focus": [],
    "sector_focus": [],
    "anomaly_flags": [],
    "confidence": 0.0,
    "needs_human_review": False,
}


class TenderAwardWorker:
    """Worker 2: Tender Award Analysis (temperature=0.1)."""

    async def run(self, tender_data: list[dict[str, Any]]) -> dict[str, Any]:
        user_content = (
            f"Tender award records:\n{json.dumps(tender_data, default=str)}\n\n"
            f"Return JSON matching this schema:\n{json.dumps(_W2_SCHEMA)}"
        )
        return await _call_worker(
            worker_name="tender_award_analysis",
            system_prompt=_W2_SYSTEM,
            user_content=user_content,
            temperature=0.1,
            top_p=0.8,
            max_tokens=1500,
        )


# ── Worker 3: Competitive Pricing Model ──────────────────────────────────────

_W3_SYSTEM = (
    "You are a quantitative infrastructure market analyst. "
    "Using: historical contract values, project capacity data, regional normalization "
    "factors, market benchmark averages. "
    "Compute: price_per_unit, normalized_price, competitive_pricing_index, "
    "percentile_position, volatility_index, confidence_level. "
    "Do not hallucinate missing numbers. If insufficient data, return confidence low. "
    "IMPORTANT: Only extract numbers from the data. Do not perform arithmetic yourself."
)

_W3_SCHEMA = {
    "extracted_values": [],
    "price_per_unit": None,
    "normalized_price": None,
    "competitive_pricing_index": None,
    "percentile_position": None,
    "volatility_index": None,
    "confidence_level": 0.0,
    "insufficient_data": False,
    "needs_human_review": False,
}


class CompetitivePricingWorker:
    """Worker 3: Competitive Pricing Model (temperature=0.1).

    Extracts numeric values only; arithmetic is performed by math_service.
    """

    async def run(
        self,
        contract_values: list[float],
        mw_capacities: list[float],
        regional_factor: float,
        market_avg: float,
    ) -> dict[str, Any]:
        user_content = (
            f"Contract values: {contract_values}\n"
            f"MW capacities: {mw_capacities}\n"
            f"Regional factor: {regional_factor}\n"
            f"Market average: {market_avg}\n\n"
            f"Return JSON matching this schema:\n{json.dumps(_W3_SCHEMA)}"
        )
        return await _call_worker(
            worker_name="competitive_pricing_model",
            system_prompt=_W3_SYSTEM,
            user_content=user_content,
            temperature=0.1,
            top_p=0.7,
            max_tokens=1000,
        )


# ── Worker 4: Earnings Call Signal Extraction ─────────────────────────────────

_W4_SYSTEM = (
    "You are analyzing an earnings call transcript. "
    "Extract references to: capital expenditure changes, infrastructure expansion, "
    "geographic expansion, AI or compute investment, sustainability initiatives, "
    "vendor mentions, risk language. "
    "For each: quote_excerpt, topic_category, signal_strength (0-1), strategic_implication."
)

_W4_SCHEMA = {
    "signals": [
        {
            "quote_excerpt": "",
            "topic_category": "",
            "signal_strength": 0.0,
            "strategic_implication": "",
        }
    ],
    "overall_confidence": 0.0,
    "needs_human_review": False,
}


class EarningsCallWorker:
    """Worker 4: Earnings Call Signal Extraction (temperature=0.1)."""

    async def run(self, transcript: str) -> dict[str, Any]:
        user_content = (
            f"Earnings call transcript:\n{transcript[:8000]}\n\n"
            f"Return JSON matching this schema:\n{json.dumps(_W4_SCHEMA)}"
        )
        return await _call_worker(
            worker_name="earnings_call_extraction",
            system_prompt=_W4_SYSTEM,
            user_content=user_content,
            temperature=0.1,
            top_p=0.8,
            max_tokens=2000,
        )


# ── Worker 5: Executive Public Intelligence ───────────────────────────────────

_W5_SYSTEM = (
    "You are a professional relationship intelligence analyst. "
    "Using ONLY public information provided, extract: professional focus areas, "
    "recurring strategic themes, public speaking topics, communication tone "
    "(analytical/visionary/operational), industry priorities, publicly disclosed "
    "charity involvement. "
    "Generate: conversation_angles (max 5), suggested_touchpoints, risk_sensitivities. "
    "Do NOT include private family or personal data."
)

_W5_SCHEMA = {
    "professional_focus": [],
    "strategic_themes": [],
    "speaking_topics": [],
    "communication_tone": "",
    "industry_priorities": [],
    "charity_involvement": [],
    "conversation_angles": [],
    "suggested_touchpoints": [],
    "risk_sensitivities": [],
    "confidence": 0.0,
    "needs_human_review": False,
}


class ExecutiveIntelWorker:
    """Worker 5: Executive Public Intelligence (temperature=0.2)."""

    async def run(self, executive_name: str, public_context: str) -> dict[str, Any]:
        user_content = (
            f"Executive: {executive_name}\n\n"
            f"Public information:\n{public_context[:6000]}\n\n"
            f"Return JSON matching this schema:\n{json.dumps(_W5_SCHEMA)}"
        )
        return await _call_worker(
            worker_name="executive_public_intel",
            system_prompt=_W5_SYSTEM,
            user_content=user_content,
            temperature=0.2,
            top_p=0.9,
            max_tokens=1500,
        )


# ── Worker 6: Relationship Timing Engine ─────────────────────────────────────

_W6_SYSTEM = (
    "You are a strategic relationship timing engine. "
    "Using recent signal events with timestamps and importance weights: "
    "1. Calculate timing_score using decay weighting. "
    "2. Determine if outreach is recommended. "
    "3. If recommended: suggest outreach_type (call/coffee/email), suggest angle, "
    "reference specific recent event. "
    "4. If not recommended: explain why."
)

_W6_SCHEMA = {
    "timing_score": 0.0,
    "recommend_outreach": False,
    "recommended_action": "",
    "justification": "",
    "confidence": 0.0,
}


class RelationshipTimingWorker:
    """Worker 6: Relationship Timing Engine (temperature=0.15)."""

    async def run(
        self,
        company_name: str,
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        user_content = (
            f"Company: {company_name}\n\n"
            f"Signal events:\n{json.dumps(events, default=str)}\n\n"
            f"Return JSON matching this schema:\n{json.dumps(_W6_SCHEMA)}"
        )
        return await _call_worker(
            worker_name="relationship_timing",
            system_prompt=_W6_SYSTEM,
            user_content=user_content,
            temperature=0.15,
            top_p=0.9,
            max_tokens=800,
        )


# ── Worker 7: Call Intelligence Analysis ──────────────────────────────────────

_W7_SYSTEM = (
    "You are a sales intelligence analyst reviewing a call transcript. "
    "Extract: sentiment_score (-1.0 to 1.0), competitor_mentions, budget_signals, "
    "timeline_mentions, objections, buying_signals, risk_flags, "
    "recommended_next_steps. Use direct quotes when possible. "
    "Also extract key_points: any mention of other companies, job roles, "
    "job opportunities, competitor positions, or hiring discussed in the call. "
    "For each key_point include: text (what was said), type "
    "(one of: job_discussion, competitor_mention, company_mention, general), "
    "mentioned_company (company name if any), "
    "mentioned_job_title (job title if any), context (brief quote or summary)."
)

_W7_SCHEMA = {
    "sentiment_score": 0.0,
    "competitor_mentions": [],
    "budget_signals": [],
    "timeline_mentions": [],
    "objections": [],
    "buying_signals": [],
    "risk_flags": [],
    "recommended_next_steps": [],
    "key_points": [],
    "overall_confidence": 0.0,
    "needs_human_review": False,
}


class CallIntelWorker:
    """Worker 7: Call Intelligence Analysis (temperature=0.1)."""

    async def transcribe_audio(self, audio_data: bytes, filename: str) -> str:
        """Attempt to transcribe audio data via the Grok API.

        Falls back to an empty string when the API key is absent or the
        request fails (the caller is responsible for raising a suitable
        HTTP error in that case).
        """
        key = _api_key()
        if not key:
            logger.warning("transcribe_audio: XAI_API_KEY not set – cannot transcribe")
            return ""

        import base64
        audio_b64 = base64.b64encode(audio_data).decode()

        # Derive a simple MIME type from the filename extension
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "mp3"
        mime_map = {"mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/m4a", "ogg": "audio/ogg"}
        mime_type = mime_map.get(ext, "audio/mpeg")

        payload: dict[str, Any] = {
            "model": _DEFAULT_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Transcribe the following audio recording verbatim. Return only the transcript text, no commentary.",
                        },
                        {
                            "type": "audio_url",
                            "audio_url": {"url": f"data:{mime_type};base64,{audio_b64}"},
                        },
                    ],
                }
            ],
            "max_tokens": 4096,
            "temperature": 0.0,
        }

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    f"{_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"] or ""
        except Exception as exc:
            logger.error("transcribe_audio failed: %s", exc)
            return ""

    async def run(self, transcript: str) -> dict[str, Any]:
        user_content = (
            f"Call transcript:\n{transcript[:8000]}\n\n"
            f"Return JSON matching this schema:\n{json.dumps(_W7_SCHEMA)}"
        )
        return await _call_worker(
            worker_name="call_intelligence",
            system_prompt=_W7_SYSTEM,
            user_content=user_content,
            temperature=0.1,
            top_p=0.85,
            max_tokens=2048,
        )


# ── Worker 8: Blog Generation ─────────────────────────────────────────────────

_W8_SYSTEM = (
    "You are an institutional infrastructure thought leadership writer. "
    "Using structured intelligence input: Write: headline, executive_summary (150 words), "
    "main_article (800-1200 words), key_insights (bullet list), "
    "SEO_meta_description (max 160 chars), LinkedIn_version (300 words), "
    "X_version (280 chars). "
    "Tone: authoritative, structured, analytical, no hype, no exaggeration. "
    "Do not fabricate data."
)

_W8_SCHEMA = {
    "headline": "",
    "executive_summary": "",
    "main_article": "",
    "key_insights": [],
    "SEO_meta_description": "",
    "LinkedIn_version": "",
    "X_version": "",
}


class BlogGenerationWorker:
    """Worker 8: Blog Generation (temperature=0.4)."""

    async def run(self, topic: str, intelligence_context: str) -> dict[str, Any]:
        user_content = (
            f"Topic: {topic}\n\n"
            f"Intelligence context:\n{intelligence_context[:6000]}\n\n"
            f"Return JSON matching this schema:\n{json.dumps(_W8_SCHEMA)}"
        )
        return await _call_worker(
            worker_name="blog_generation",
            system_prompt=_W8_SYSTEM,
            user_content=user_content,
            temperature=0.4,
            top_p=0.95,
            max_tokens=3500,
        )


# ── Worker 9: Signal Clustering & Trend Detection ─────────────────────────────

_W9_SYSTEM = (
    "You are a semantic trend detection engine. "
    "Given: clustered document embeddings, frequency counts, time series data. "
    "Identify: emerging themes, acceleration signals, anomaly spikes, declining topics."
)

_W9_SCHEMA = {
    "emerging_themes": [],
    "accelerating_topics": [],
    "declining_topics": [],
    "anomalies": [],
    "confidence": 0.0,
}


class TrendDetectionWorker:
    """Worker 9: Signal Clustering & Trend Detection (temperature=0.1)."""

    async def run(self, signals_context: str) -> dict[str, Any]:
        user_content = (
            f"Signal data:\n{signals_context[:8000]}\n\n"
            f"Return JSON matching this schema:\n{json.dumps(_W9_SCHEMA)}"
        )
        return await _call_worker(
            worker_name="trend_detection",
            system_prompt=_W9_SYSTEM,
            user_content=user_content,
            temperature=0.1,
            top_p=0.8,
            max_tokens=1500,
        )


# ── Worker 10: Image Intelligence ─────────────────────────────────────────────

_W10_SYSTEM = (
    "You are an infrastructure visual analysis engine. "
    "Analyze the provided image description or metadata. "
    "Detect: facility type, construction stage, visible capacity indicators, "
    "brand signage, safety indicators, potential project scale."
)

_W10_SCHEMA = {
    "facility_type": "",
    "construction_stage": "",
    "capacity_indicators": [],
    "brand_signage": [],
    "safety_indicators": [],
    "project_scale": "",
    "confidence": 0.0,
    "needs_human_review": False,
}


class ImageIntelWorker:
    """Worker 10: Image Intelligence (temperature=0.15)."""

    async def run(self, image_description: str) -> dict[str, Any]:
        user_content = (
            f"Image description / metadata:\n{image_description[:4000]}\n\n"
            f"Return JSON matching this schema:\n{json.dumps(_W10_SCHEMA)}"
        )
        return await _call_worker(
            worker_name="image_intelligence",
            system_prompt=_W10_SYSTEM,
            user_content=user_content,
            temperature=0.15,
            top_p=0.9,
            max_tokens=800,
        )


# ── Worker 11: Build Captain ──────────────────────────────────────────────────

_W11_SYSTEM = (
    "You are Build Captain: product-minded staff engineer. "
    "Convert user requests into implementable plans for a Next.js + TS + Tailwind app. "
    "Output: (1) assumptions (max 3), (2) task list in order, (3) file-level plan, "
    "(4) acceptance criteria, (5) test/verification steps. "
    "Prefer small PR-sized chunks. When user provides code/screenshots, infer intent "
    "and propose the cleanest minimal change. "
    "Ask max 2 questions only if blocking; otherwise proceed with best assumptions. "
    "Return STRICT JSON. No markdown. No narrative outside JSON fields."
)

_W11_SCHEMA = {
    "assumptions": [],
    "task_list": [],
    "file_level_plan": [],
    "acceptance_criteria": [],
    "verification_steps": [],
    "confidence": 0.0,
}


class BuildCaptainWorker:
    """Worker 11: Build Captain – build planning agent (temperature=0.3)."""

    async def run(self, request: str) -> dict[str, Any]:
        user_content = (
            f"Build request:\n{request[:6000]}\n\n"
            f"Return JSON matching this schema:\n{json.dumps(_W11_SCHEMA)}"
        )
        return await _call_worker(
            worker_name="build_captain",
            system_prompt=_W11_SYSTEM,
            user_content=user_content,
            temperature=0.3,
            top_p=0.95,
            max_tokens=3000,
        )


# ── Worker 12: UI Surgeon ─────────────────────────────────────────────────────

_W12_SYSTEM = (
    "You are UI Surgeon: expert UI engineer for Next.js + Tailwind + shadcn. "
    "Given a screenshot, reference site, or UI description, you output: "
    "(1) layout anatomy (shell/sections), (2) component inventory, "
    "(3) Tailwind token suggestions, (4) shadcn components to use, "
    "(5) responsive rules, (6) exact file structure + build order. "
    "Provide code skeletons when requested. Keep designs calm, premium, data-first. "
    "Return STRICT JSON. No markdown. No narrative outside JSON fields."
)

_W12_SCHEMA = {
    "layout_anatomy": [],
    "component_inventory": [],
    "tailwind_tokens": [],
    "shadcn_components": [],
    "responsive_rules": [],
    "file_structure": [],
    "build_order": [],
    "confidence": 0.0,
}


class UiSurgeonWorker:
    """Worker 12: UI Surgeon – UI analysis and component planning agent (temperature=0.3)."""

    async def run(self, description: str) -> dict[str, Any]:
        user_content = (
            f"UI description / reference:\n{description[:6000]}\n\n"
            f"Return JSON matching this schema:\n{json.dumps(_W12_SCHEMA)}"
        )
        return await _call_worker(
            worker_name="ui_surgeon",
            system_prompt=_W12_SYSTEM,
            user_content=user_content,
            temperature=0.3,
            top_p=0.95,
            max_tokens=3000,
        )


# ── Worker 13: Test Pilot ─────────────────────────────────────────────────────

_W13_SYSTEM = (
    "You are Test Pilot: QA engineer + automation specialist. "
    "For any feature, produce: (1) risk list, (2) manual test checklist, "
    "(3) Playwright test plan and scripts, (4) data fixtures needed, "
    "(5) failure triage steps. "
    "Optimise for fast, reliable tests. "
    "Ask for app URL/routes if needed; otherwise write tests using sensible selectors and aria roles. "
    "Return STRICT JSON. No markdown. No narrative outside JSON fields."
)

_W13_SCHEMA = {
    "risk_list": [],
    "manual_checklist": [],
    "playwright_test_plan": [],
    "playwright_scripts": [],
    "data_fixtures": [],
    "failure_triage": [],
    "confidence": 0.0,
}


class TestPilotWorker:
    """Worker 13: Test Pilot – QA and Playwright automation agent (temperature=0.2)."""

    async def run(self, feature_description: str) -> dict[str, Any]:
        user_content = (
            f"Feature to test:\n{feature_description[:6000]}\n\n"
            f"Return JSON matching this schema:\n{json.dumps(_W13_SCHEMA)}"
        )
        return await _call_worker(
            worker_name="test_pilot",
            system_prompt=_W13_SYSTEM,
            user_content=user_content,
            temperature=0.2,
            top_p=0.9,
            max_tokens=3500,
        )


# ── Worker 14: Data Curator ───────────────────────────────────────────────────

_W14_SYSTEM = (
    "You are Data Curator: product data + backend engineer for pricing/valuation. "
    "Build schemas and algorithms for: variant match scoring, sold comps selection, "
    "outlier handling, confidence rating (High/Med/Low). "
    "Output: (1) data model, (2) scoring rules, (3) required inputs, "
    "(4) API shapes, (5) validation + logging, (6) quick verification queries. "
    "Prefer transparent ranges over single numbers. "
    "Return STRICT JSON. No markdown. No narrative outside JSON fields."
)

_W14_SCHEMA = {
    "data_model": [],
    "scoring_rules": [],
    "required_inputs": [],
    "api_shapes": [],
    "validation_rules": [],
    "verification_queries": [],
    "confidence": 0.0,
}


class DataCuratorWorker:
    """Worker 14: Data Curator – valuation pipeline design agent (temperature=0.15)."""

    async def run(self, context: str) -> dict[str, Any]:
        user_content = (
            f"Valuation / data context:\n{context[:6000]}\n\n"
            f"Return JSON matching this schema:\n{json.dumps(_W14_SCHEMA)}"
        )
        return await _call_worker(
            worker_name="data_curator",
            system_prompt=_W14_SYSTEM,
            user_content=user_content,
            temperature=0.15,
            top_p=0.85,
            max_tokens=3000,
        )


# ── Worker 15: Ops Boss ───────────────────────────────────────────────────────

_W15_SYSTEM = (
    "You are Ops Boss: DevOps for Next.js. "
    "Output: (1) env var matrix (dev/stage/prod), (2) secrets handling rules, "
    "(3) CI pipeline steps (lint/typecheck/test/build), (4) caching strategy, "
    "(5) security basics (no secrets client-side), (6) deploy checklist. "
    "Keep it minimal and reliable. "
    "Return STRICT JSON. No markdown. No narrative outside JSON fields."
)

_W15_SCHEMA = {
    "env_var_matrix": [],
    "secrets_handling": [],
    "ci_pipeline_steps": [],
    "caching_strategy": [],
    "security_basics": [],
    "deploy_checklist": [],
    "confidence": 0.0,
}


class OpsBossWorker:
    """Worker 15: Ops Boss – CI/CD and environment configuration agent (temperature=0.15)."""

    async def run(self, context: str) -> dict[str, Any]:
        user_content = (
            f"Deployment / CI context:\n{context[:6000]}\n\n"
            f"Return JSON matching this schema:\n{json.dumps(_W15_SCHEMA)}"
        )
        return await _call_worker(
            worker_name="ops_boss",
            system_prompt=_W15_SYSTEM,
            user_content=user_content,
            temperature=0.15,
            top_p=0.85,
            max_tokens=3000,
        )


# ── Backward compatibility aliases ────────────────────────────────────────────
TenderAnalysisWorker = TenderAwardWorker
PricingModelWorker = CompetitivePricingWorker
EarningsSignalWorker = EarningsCallWorker
BlogWorker = BlogGenerationWorker

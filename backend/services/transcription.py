"""
Call Transcription and Intelligence Extraction Service.

Uses Grok AI to extract structured signals from call transcripts.
"""

import json
import logging

from backend.services import grok_client
from backend.services.governance import GovernanceLogger, needs_human_review

logger = logging.getLogger("align.transcription")

_SYSTEM_PROMPT = "You are a sales intelligence analyst."

_EXTRACTION_USER_TEMPLATE = """
Analyse the following call transcript and extract structured signals.
Return ONLY valid JSON in this exact format:
{{
  "sentiment_score": 0.0,
  "competitor_mentions": [],
  "budget_signals": [],
  "timeline_mentions": [],
  "risk_language": [],
  "objection_categories": [],
  "next_steps": ""
}}

Rules:
- sentiment_score: float from -1.0 (very negative) to 1.0 (very positive)
- All list fields: extract direct quotes or brief paraphrases
- next_steps: single summary sentence of agreed actions
- Extract only what is explicitly stated in the transcript

TRANSCRIPT:
{transcript}
"""


async def analyse_transcript(transcript: str) -> dict:
    """
    Analyse a call transcript with Grok and extract structured intelligence.

    Returns dict with sentiment_score, competitor_mentions, budget_signals,
    timeline_mentions, risk_language, objection_categories, next_steps.
    """
    if not grok_client.is_configured():
        return {
            "sentiment_score": None,
            "competitor_mentions": [],
            "budget_signals": [],
            "timeline_mentions": [],
            "risk_language": [],
            "objection_categories": [],
            "next_steps": "AI analysis unavailable – XAI_API_KEY not configured.",
        }

    _TASK = "transcript_analysis"
    _TEMP = grok_client._TASK_TEMPERATURES[_TASK]
    user_content = _EXTRACTION_USER_TEMPLATE.format(transcript=transcript[:8000])

    result: dict = {}
    input_tokens = output_tokens = 0
    try:
        raw, input_tokens, output_tokens = await grok_client._chat(
            _SYSTEM_PROMPT,
            user_content,
            max_tokens=512,
            temperature=_TEMP,
            task=_TASK,
        )
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(raw[start:end])
    except Exception as exc:
        logger.warning("Transcript analysis failed: %s", exc)

    if not result:
        result = {
            "sentiment_score": None,
            "competitor_mentions": [],
            "budget_signals": [],
            "timeline_mentions": [],
            "risk_language": [],
            "objection_categories": [],
            "next_steps": "Analysis failed – review transcript manually.",
        }

    # Extract confidence from result; fall back to neutral 0.65
    confidence = 0.65
    for key in ("confidence", "overall_confidence", "confidence_level"):
        val = result.get(key)
        if val is not None:
            try:
                confidence = float(val)
                break
            except (TypeError, ValueError):
                continue

    GovernanceLogger.log(
        worker_name="grok_client.transcript_analysis",
        model=grok_client._TASK_MODELS.get(_TASK, grok_client._DEFAULT_MODEL),
        temperature=_TEMP,
        system_prompt=_SYSTEM_PROMPT,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        confidence=confidence,
        validation_outcome="ok",
        extra={"human_review_queued": needs_human_review(confidence)},
    )
    return result

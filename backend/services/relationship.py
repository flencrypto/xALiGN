"""
Relationship Intelligence Engine.

Generates personalised contact briefs using public signals and Grok AI.
"""

import json
import logging

from backend.services import grok_client
from backend.services.governance import GovernanceLogger, needs_human_review

logger = logging.getLogger("align.relationship")

_SYSTEM_PROMPT = "You are a strategic business development advisor."

_BRIEF_USER_TEMPLATE = """
Company: {company_name}
Recent signals: {events}

Generate a concise relationship contact brief in JSON format:
{{
  "suggested_angle": "...",
  "why_now": "...",
  "what_to_mention": "...",
  "what_to_avoid": "...",
  "risk_flags": "..."
}}

Base all advice on publicly available information only.
Be specific, actionable, and commercially focused.
"""


async def generate_contact_brief(
    company_name: str,
    events: list[str],
) -> dict:
    """
    Generate a personalised contact brief for a company using Grok AI.

    Returns a dict with keys: suggested_angle, why_now, what_to_mention,
    what_to_avoid, risk_flags.
    """
    if not grok_client.is_configured():
        return {
            "suggested_angle": "Review recent company announcements before outreach.",
            "why_now": "Manual review required – AI not configured.",
            "what_to_mention": "Relevant project experience and capability.",
            "what_to_avoid": "Unverified claims or competitor criticism.",
            "risk_flags": "XAI_API_KEY not set – AI analysis unavailable.",
        }

    _TASK = "relationship_brief"
    _TEMP = grok_client._TASK_TEMPERATURES[_TASK]
    user_content = _BRIEF_USER_TEMPLATE.format(
        company_name=company_name,
        events=", ".join(events) if events else "no recent signals",
    )

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
        logger.warning("Relationship brief generation failed: %s", exc)

    if not result:
        result = {
            "suggested_angle": "Reference recent company activity.",
            "why_now": f"Recent signals detected for {company_name}.",
            "what_to_mention": "Relevant capability and project references.",
            "what_to_avoid": "Sensitive financial speculation.",
            "risk_flags": "AI analysis incomplete – review manually.",
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
        worker_name="grok_client.relationship_brief",
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

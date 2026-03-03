"""
Relationship Intelligence Engine.

Generates personalised contact briefs using public signals and Grok AI.
"""

import logging
from typing import Optional

from backend.services import grok_client

logger = logging.getLogger("contractghost.relationship")

_BRIEF_PROMPT = """
You are a strategic business development advisor.

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

    prompt = _BRIEF_PROMPT.format(
        company_name=company_name,
        events=", ".join(events) if events else "no recent signals",
    )

    try:
        import json
        from openai import AsyncOpenAI
        import os

        client = AsyncOpenAI(
            api_key=os.environ.get("XAI_API_KEY", ""),
            base_url="https://api.x.ai/v1",
        )
        response = await client.chat.completions.create(
            model="grok-3-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        raw = response.choices[0].message.content or "{}"
        # Extract JSON from response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception as exc:
        logger.warning("Relationship brief generation failed: %s", exc)

    return {
        "suggested_angle": "Reference recent company activity.",
        "why_now": f"Recent signals detected for {company_name}.",
        "what_to_mention": "Relevant capability and project references.",
        "what_to_avoid": "Sensitive financial speculation.",
        "risk_flags": "AI analysis incomplete – review manually.",
    }

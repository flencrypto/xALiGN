"""
Call Transcription and Intelligence Extraction Service.

Uses Grok AI to extract structured signals from call transcripts.
"""

import json
import logging
import os

from backend.services import grok_client

logger = logging.getLogger("contractghost.transcription")

_EXTRACTION_PROMPT = """
You are a sales intelligence analyst.

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

    prompt = _EXTRACTION_PROMPT.format(transcript=transcript[:8000])  # cap at 8k chars

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=os.environ.get("XAI_API_KEY", ""),
            base_url="https://api.x.ai/v1",
        )
        response = await client.chat.completions.create(
            model="grok-3-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        raw = response.choices[0].message.content or "{}"
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception as exc:
        logger.warning("Transcript analysis failed: %s", exc)

    return {
        "sentiment_score": None,
        "competitor_mentions": [],
        "budget_signals": [],
        "timeline_mentions": [],
        "risk_language": [],
        "objection_categories": [],
        "next_steps": "Analysis failed – review transcript manually.",
    }

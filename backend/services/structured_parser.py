"""Structured Intelligence Parser – extracts structured fields from raw article text.

Extracts: company, location, project name, investment (£/$/€), MW capacity, project stage.
Uses the Grok LLM for extraction and falls back to regex for simple patterns.
"""

import json
import logging
import re
from typing import Any

import httpx

from backend.services.governance import GovernanceLogger

logger = logging.getLogger("align.structured_parser")
_BASE_URL = "https://api.x.ai/v1"
_TIMEOUT = 60.0
_governance = GovernanceLogger()


def _api_key():
    import os
    return os.getenv("XAI_API_KEY")


_SYSTEM_PROMPT = """You are a data extraction specialist for infrastructure intelligence.
Given a news article or press release, extract structured fields as JSON.

Return ONLY valid JSON with these fields (use null for unknown):
{
  "company": "primary company name",
  "location": "city, country or region",
  "project_name": "name of the infrastructure project if mentioned",
  "investment_value": "numeric value in millions GBP/USD if mentioned, null otherwise",
  "investment_currency": "GBP/USD/EUR",
  "capacity_mw": "numeric MW capacity if mentioned, null otherwise",
  "project_stage": "one of: announced/planning/approved/construction/operational",
  "project_type": "one of: new_build/expansion/upgrade/energy_deal/acquisition",
  "partners": ["list of partner companies mentioned"],
  "confidence": 0.0-1.0
}"""


async def parse_article(title: str, text: str) -> dict[str, Any]:
    """Extract structured intelligence fields from a single article."""
    key = _api_key()
    if not key:
        return _regex_fallback(title, text)

    user_content = f"Title: {title}\n\nText: {text[:3000]}"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": "grok-3-mini",
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.05,
                    "max_tokens": 500,
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            result = json.loads(content)
            _governance.log(
                worker="structured_parser",
                model="grok-3-mini",
                prompt_tokens=data.get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=data.get("usage", {}).get("completion_tokens", 0),
                confidence=float(result.get("confidence", 0.7)),
                needs_review=False,
            )
            return result
    except Exception as exc:
        logger.warning("structured_parser LLM failed, using regex fallback: %s", exc)
        return _regex_fallback(title, text)


def _regex_fallback(title: str, text: str) -> dict[str, Any]:
    """Simple regex-based extraction when LLM is unavailable."""
    combined = f"{title} {text}"

    # MW extraction
    mw_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:MW|megawatt)", combined, re.IGNORECASE)
    capacity_mw = float(mw_match.group(1)) if mw_match else None

    # Investment extraction
    inv_match = re.search(r"[£$€](\d+(?:\.\d+)?)\s*(?:billion|bn|million|m)\b", combined, re.IGNORECASE)
    if inv_match:
        value = float(inv_match.group(1))
        currency_char = combined[inv_match.start()]
        currency = {"£": "GBP", "$": "USD", "€": "EUR"}.get(currency_char, "USD")
        # normalise to millions
        if re.search(r"billion|bn", combined[inv_match.start():inv_match.end() + 10], re.I):
            value *= 1000
    else:
        value = None
        currency = None

    return {
        "company": None,
        "location": None,
        "project_name": None,
        "investment_value": value,
        "investment_currency": currency,
        "capacity_mw": capacity_mw,
        "project_stage": None,
        "project_type": None,
        "partners": [],
        "confidence": 0.3,
    }


async def run_structured_parser(db) -> int:
    """Process unstructured records in the database and update InfrastructureProject entries.

    Pulls from: InfrastructureAnnouncement, VendorPressRelease, NewsArticle
    Writes to: InfrastructureProject (creates or updates)
    Returns: count of records processed
    """
    from backend.models.intelligence import InfrastructureAnnouncement
    from backend.models.projects import InfrastructureProject

    count = 0

    # Process infrastructure announcements not yet linked to a project
    announcements = db.query(InfrastructureAnnouncement).filter(
        InfrastructureAnnouncement.capacity_mw.is_(None)
    ).limit(20).all()

    for ann in announcements:
        try:
            parsed = await parse_article(ann.title, ann.summary or "")
            if parsed.get("capacity_mw") or parsed.get("investment_value"):
                # Update the announcement with extracted capacity
                if parsed.get("capacity_mw") and not ann.capacity_mw:
                    ann.capacity_mw = parsed["capacity_mw"]
                if parsed.get("investment_value") and not ann.project_value_gbp:
                    ann.project_value_gbp = parsed.get("investment_value")

                # Create InfrastructureProject record
                project = InfrastructureProject(
                    name=parsed.get("project_name") or ann.title[:200],
                    company=parsed.get("company") or ann.operator,
                    location=parsed.get("location") or ann.location,
                    capacity_mw=parsed.get("capacity_mw"),
                    capex_millions=parsed.get("investment_value"),
                    capex_currency=parsed.get("investment_currency", "GBP"),
                    stage=parsed.get("project_stage") or "announced",
                    project_type=parsed.get("project_type") or "data_centre",
                    partners=json.dumps(parsed.get("partners", [])),
                    source_url=ann.source_url,
                    source_name=ann.source_name,
                )
                db.add(project)
                count += 1
        except Exception as exc:
            logger.error("parse_article failed for announcement %d: %s", ann.id, exc)

    db.commit()
    return count

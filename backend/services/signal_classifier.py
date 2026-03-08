"""Signal Classification Engine – classifies signals into defined types.

Signal types:
  new_build       – A new data centre or infrastructure build
  expansion       – Expansion or capacity increase of existing facility
  energy_deal     – Power purchase agreement or energy deal
  tender          – Active procurement / tender opportunity
  supplier_contract – Supplier or subcontractor award
  acquisition     – Corporate acquisition or M&A
  general         – Other infrastructure news

Uses keyword heuristics first, then LLM for ambiguous cases.
"""

import json
import logging
from typing import Any  # noqa: F401

import httpx

logger = logging.getLogger("align.signal_classifier")
_BASE_URL = "https://api.x.ai/v1"
_TIMEOUT = 60.0


# ── Signal taxonomy keyword rules ─────────────────────────────────────────────

_RULES: list[tuple[str, list[str]]] = [
    ("tender", [
        "tender", "rfp", "rfq", "request for proposal", "procurement",
        "bid", "invitation to tender", "itt", "framework agreement",
        "contract award", "awarded contract",
    ]),
    ("energy_deal", [
        "power purchase agreement", "ppa", "energy deal", "renewable energy",
        "solar pv", "wind farm", "battery storage", "bess", "grid connection",
        "electricity supply", "power grid", "substation upgrade",
    ]),
    ("expansion", [
        "expansion", "phase 2", "phase 3", "additional capacity",
        "increase capacity", "scaling", "extending", "new phase",
        "campus expansion", "expanding its", "adding capacity",
    ]),
    ("new_build", [
        "new data centre", "new facility", "breaking ground", "groundbreaking",
        "campus construction", "planning permission", "planning application",
        "new build", "greenfield", "brownfield development",
        "will be built", "under construction", "new campus",
    ]),
    ("supplier_contract", [
        "supplier", "equipment order", "contract awarded", "supply agreement",
        "UPS supply", "cooling system", "generator order", "switchgear",
        "fit-out", "m&e contract", "mep contract",
    ]),
    ("acquisition", [
        "acquisition", "merger", "acquires", "acquired", "takeover",
        "joint venture", "investment in", "stake in", "buys", "purchased",
    ]),
]


def classify_signal(title: str, text: str) -> str:
    """Classify a signal using keyword heuristics.

    Returns one of: new_build, expansion, energy_deal, tender,
    supplier_contract, acquisition, general
    """
    combined = f"{title} {text or ''}".lower()

    scores: dict[str, int] = {signal_type: 0 for signal_type, _ in _RULES}

    for signal_type, keywords in _RULES:
        for kw in keywords:
            if kw in combined:
                scores[signal_type] += 1

    # Return highest scoring type; default to general
    best_type = max(scores, key=lambda k: scores[k])
    return best_type if scores[best_type] > 0 else "general"


async def classify_signal_llm(title: str, text: str) -> str:
    """Use LLM to classify a signal when keyword matching is ambiguous."""
    import os
    key = os.getenv("XAI_API_KEY")
    if not key:
        return classify_signal(title, text)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": "grok-3-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Classify this infrastructure news signal into exactly ONE category. "
                                "Return JSON: {\"signal_type\": \"<type>\", \"confidence\": 0.0-1.0}\n"
                                "Categories: new_build, expansion, energy_deal, tender, "
                                "supplier_contract, acquisition, general"
                            ),
                        },
                        {"role": "user", "content": f"Title: {title}\n\nText: {text[:1000]}"},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.05,
                    "max_tokens": 100,
                },
            )
            response.raise_for_status()
            data = response.json()
            result = json.loads(data["choices"][0]["message"]["content"])
            return result.get("signal_type", "general")
    except Exception as exc:
        logger.warning("signal_classifier LLM failed: %s", exc)
        return classify_signal(title, text)


async def run_signal_classification(db) -> int:
    """Classify unclassified signals in the database.

    Updates signal_type on InfrastructureAnnouncement, VendorPressRelease, NewsArticle.
    Returns count of records classified.
    """
    from backend.models.intelligence import InfrastructureAnnouncement, NewsArticle

    count = 0

    announcements = db.query(InfrastructureAnnouncement).filter(
        InfrastructureAnnouncement.signal_type.is_(None)
    ).limit(50).all()

    for ann in announcements:
        ann.signal_type = classify_signal(ann.title, ann.summary or "")
        count += 1

    articles = db.query(NewsArticle).filter(
        NewsArticle.signal_type.is_(None)
    ).limit(50).all()

    for article in articles:
        article.signal_type = classify_signal(article.title, article.summary or "")
        count += 1

    db.commit()
    return count

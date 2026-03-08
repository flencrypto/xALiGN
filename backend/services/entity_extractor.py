"""Entity Extraction Engine – identifies companies, suppliers, contractors, technologies, regions.

Uses a combination of keyword matching against known entity lists and LLM extraction.
Stores extracted entity links in the database.
"""

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger("align.entity_extractor")
_BASE_URL = "https://api.x.ai/v1"
_TIMEOUT = 60.0

# ── Known entity lists ────────────────────────────────────────────────────────

HYPERSCALERS = [
    "Amazon Web Services", "AWS", "Google Cloud", "Microsoft Azure", "Microsoft",
    "Meta", "Apple", "Oracle", "IBM", "Alibaba Cloud", "Tencent Cloud",
    "ByteDance", "Salesforce", "SAP", "Baidu",
]

DC_OPERATORS = [
    "Equinix", "Digital Realty", "NTT", "Lumen", "CyrusOne", "QTS",
    "Iron Mountain", "Vantage Data Centers", "EdgeCore", "Compass Datacenters",
    "Colo Atl", "Flexential", "RagingWire", "Switch", "DataBank",
    "Ark Data Centres", "Virtus", "Kao Data", "TeleCity", "Global Switch",
    "Telehouse", "Pulsant", "UKCloud", "Custodian Data Centres",
]

MEP_SUPPLIERS = [
    "Schneider Electric", "Vertiv", "Eaton", "Siemens", "ABB", "Caterpillar",
    "Cummins", "Rolls-Royce", "MTU", "HIMOINSA", "Kohler", "Legrand",
    "Rittal", "nVent", "Stulz", "Airedale", "Climaveneta", "Daikin",
    "Carrier", "Trane", "Johnson Controls", "Honeywell",
]

CONTRACTORS = [
    "Turner Construction", "Mortenson", "DPR Construction", "Holder Construction",
    "Structure Tone", "Skanska", "Laing O'Rourke", "BAM Construction",
    "Mace Group", "Lendlease", "Balfour Beatty", "Kier Group",
    "Morgan Sindall", "Bouygues", "AECOM", "Jacobs", "Arcadis",
]

TECHNOLOGIES = [
    "liquid cooling", "direct liquid cooling", "DLC", "immersion cooling",
    "air cooling", "free cooling", "adiabatic cooling", "economiser",
    "UPS", "uninterruptible power supply", "generator", "PDU", "busway",
    "CRAC", "CRAH", "raised floor", "hot aisle", "cold aisle",
    "containment", "DCIM", "BMS", "PLC", "400V", "11kV", "33kV", "132kV",
    "transformer", "switchgear", "ATS", "STS", "BESS", "battery storage",
    "solar PV", "wind power", "hydrogen", "fuel cell",
    "GPU", "TPU", "NVIDIA", "AMD", "Intel", "HBM", "HPC",
]

UK_REGIONS = [
    "London", "South East", "South West", "East of England", "East Midlands",
    "West Midlands", "Yorkshire", "North West", "North East",
    "Scotland", "Wales", "Northern Ireland", "Ireland",
    "Slough", "Reading", "Didcot", "Swindon", "Bristol", "Birmingham",
    "Manchester", "Leeds", "Sheffield", "Newcastle", "Edinburgh", "Glasgow",
    "Cardiff", "Belfast", "Cambridge", "Oxford",
]

GLOBAL_REGIONS = [
    "US", "USA", "United States", "UK", "United Kingdom", "Germany",
    "Netherlands", "France", "Spain", "Italy", "Sweden", "Norway",
    "Denmark", "Finland", "Poland", "Singapore", "Japan", "Australia",
    "Canada", "Brazil", "India", "UAE", "Saudi Arabia", "South Korea",
    "Hong Kong", "Ireland",
]


def extract_entities_from_text(text: str) -> dict[str, list[str]]:
    """Extract known entities from text using keyword matching.

    Returns dict with keys: hyperscalers, dc_operators, mep_suppliers,
    contractors, technologies, regions
    """
    text_lower = text.lower()

    def find_matches(entity_list: list[str]) -> list[str]:
        found = []
        for entity in entity_list:
            if entity.lower() in text_lower:
                found.append(entity)
        return list(dict.fromkeys(found))  # deduplicate preserving order

    return {
        "hyperscalers": find_matches(HYPERSCALERS),
        "dc_operators": find_matches(DC_OPERATORS),
        "mep_suppliers": find_matches(MEP_SUPPLIERS),
        "contractors": find_matches(CONTRACTORS),
        "technologies": find_matches(TECHNOLOGIES),
        "regions": find_matches(UK_REGIONS + GLOBAL_REGIONS),
    }


async def extract_entities_llm(text: str) -> dict[str, Any]:
    """Use LLM to extract entities not captured by keyword matching."""
    import os
    key = os.getenv("XAI_API_KEY")
    if not key:
        return {}

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
                                "Extract named entities from infrastructure news text. "
                                "Return JSON with: companies (list), locations (list), "
                                "technologies (list), project_names (list). "
                                "Focus on data centres, power infrastructure, and AI hardware."
                            ),
                        },
                        {"role": "user", "content": text[:2000]},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.05,
                    "max_tokens": 400,
                },
            )
            response.raise_for_status()
            data = response.json()
            return json.loads(data["choices"][0]["message"]["content"])
    except Exception as exc:
        logger.warning("entity_extractor LLM failed: %s", exc)
        return {}


async def run_entity_extraction(db) -> int:
    """Run entity extraction over recent unprocessed articles.

    Updates keywords_matched / extracted_entities fields on source records.
    Returns count of records processed.
    """
    from backend.models.intelligence import NewsArticle, VendorPressRelease

    count = 0

    articles = db.query(NewsArticle).filter(
        NewsArticle.keywords_matched.is_(None)
    ).limit(50).all()

    for article in articles:
        text = f"{article.title} {article.summary or ''}"
        entities = extract_entities_from_text(text)
        all_keywords = (
            entities["hyperscalers"] + entities["dc_operators"] +
            entities["mep_suppliers"] + entities["technologies"]
        )
        article.keywords_matched = json.dumps(all_keywords)
        count += 1

    press_releases = db.query(VendorPressRelease).filter(
        VendorPressRelease.extracted_entities.is_(None)
    ).limit(30).all()

    for pr in press_releases:
        text = f"{pr.title} {pr.summary or ''} {pr.full_text or ''}"
        entities = extract_entities_from_text(text)
        pr.extracted_entities = json.dumps(entities)
        pr.related_suppliers = json.dumps(
            entities["mep_suppliers"] + entities["dc_operators"]
        )
        count += 1

    db.commit()
    return count

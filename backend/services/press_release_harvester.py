"""Vendor Press Release Harvester – collects vendor announcements from RSS feeds.

Fetches vendor-specific RSS feeds, extracts structured entities (supplier names,
project references), and persists results to ``vendor_press_releases``.
"""

import asyncio
import json
import logging
import re
from functools import partial
from typing import Optional

import feedparser
import httpx
from sqlalchemy.orm import Session

from backend.models.intelligence import VendorPressRelease

logger = logging.getLogger("align.press_release_harvester")

_TIMEOUT = 20.0

# ── Vendor RSS Feeds ──────────────────────────────────────────────────────────

VENDOR_RSS_FEEDS: dict[str, str] = {
    "Schneider Electric": "https://www.se.com/ww/en/press-releases/rss-press-releases.xml",
    "Vertiv": "https://www.vertiv.com/en-emea/news/press-releases/feed/",
    "Eaton": "https://www.eaton.com/us/en-us/company/news-insights/news-releases/rss.xml",
    "Siemens": "https://press.siemens.com/global/en/feed/pressreleases",
    "ABB": "https://new.abb.com/news/press-releases/rss",
    "Caterpillar": "https://www.caterpillar.com/en/news/caterpillarNews.rss.xml",
    "Cummins": "https://www.cummins.com/news/press-releases/rss",
    "Dell Technologies": "https://www.dell.com/en-us/dt/corporate/newsroom/announcements/rss.xml",
    "HPE": "https://www.hpe.com/h30261/rss.aspx?category=pressRelease",
    "Legrand": "https://www.legrand.com/en/press-releases/rss",
    "Rittal": "https://www.rittal.com/com-en/press/press-releases/rss.xml",
    "Piller Power Systems": "https://www.piller.com/en/news/rss.xml",
    "Kohler Power": "https://kohlerpower.com/en-us/rss/news",
    "Rolls-Royce Power Systems": "https://www.rolls-royce.com/media/our-stories/rss.xml",
    "Airedale International": "https://www.airedale.com/news/rss.xml",
    "Stulz": "https://www.stulz.com/en/news/rss.xml",
    "Aggreko": "https://www.aggreko.com/en-gb/news/rss",
    "Leviton": "https://www.leviton.com/en/news/press-releases/rss",
    "Panduit": "https://www.panduit.com/en/news/press-releases/rss.xml",
    "Commscope": "https://www.commscope.com/resources-and-news/press-releases/rss/",
}

# ── Known supplier / company names for entity extraction ─────────────────────

KNOWN_SUPPLIERS: list[str] = [
    "Schneider Electric", "Vertiv", "Eaton", "Siemens", "ABB", "Caterpillar",
    "Cummins", "Dell Technologies", "HPE", "Hewlett Packard", "Legrand",
    "Rittal", "Piller", "Kohler", "Rolls-Royce", "Airedale", "Stulz",
    "Aggreko", "Leviton", "Panduit", "Commscope", "Belden", "Nexans",
    "Emerson", "Carrier", "Johnson Controls", "Honeywell", "Daikin",
    "Mitsubishi Electric", "Aermec", "Turbocor", "Trane", "Climaveneta",
]

# ── Project signal keywords ───────────────────────────────────────────────────

PROJECT_SIGNAL_KEYWORDS: list[str] = [
    "new data centre", "new data center", "campus expansion", "build-out",
    "ground breaking", "groundbreaking", "fit-out", "commissioning",
    "contract awarded", "contract win", "deployment", "installation",
    "new facility", "new campus", "opening", "launched", "goes live",
    "MW", "megawatt", "colocation", "hyperscale", "edge deployment",
]


# ── Internal helpers ──────────────────────────────────────────────────────────

def _parse_feed(raw_content: bytes) -> list[dict]:
    parsed = feedparser.parse(raw_content)
    items = []
    for entry in parsed.entries:
        items.append({
            "title": entry.get("title", ""),
            "url": entry.get("link") or entry.get("id"),
            "summary": entry.get("summary") or entry.get("description", ""),
            "published_at": entry.get("published") or entry.get("updated"),
        })
    return items


def _extract_entities(text: str) -> dict:
    """Extract companies, project signals from free text using keyword matching."""
    text_lower = text.lower()

    matched_suppliers = [s for s in KNOWN_SUPPLIERS if s.lower() in text_lower]
    project_refs = [kw for kw in PROJECT_SIGNAL_KEYWORDS if kw.lower() in text_lower]

    # Simple location extraction for UK regions
    uk_locations = re.findall(
        r"\b(London|Manchester|Birmingham|Leeds|Edinburgh|Glasgow|Dublin|"
        r"Slough|Reading|Swindon|Cardiff|Bristol|Sheffield|Liverpool|"
        r"Newcastle|Belfast|Cambridge|Oxford|Milton Keynes)\b",
        text,
        flags=re.IGNORECASE,
    )

    return {
        "suppliers": list(set(matched_suppliers)),
        "locations": list(set(uk_locations)),
        "project_signals": project_refs,
    }


# ── Public async API ──────────────────────────────────────────────────────────

async def fetch_vendor_feed(vendor_name: str, rss_url: str, db: Session) -> int:
    """Fetch a single vendor RSS feed and persist new VendorPressRelease records.

    Returns the count of newly saved records.
    """
    saved = 0

    existing_urls: set[str] = {
        row[0]
        for row in db.query(VendorPressRelease.url)
        .filter(VendorPressRelease.url.isnot(None))
        .filter(VendorPressRelease.vendor_name == vendor_name)
        .all()
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(
                rss_url,
                headers={"User-Agent": "aLiGN-Intel/1.0"},
            )
            resp.raise_for_status()
            content = resp.content
    except Exception as exc:
        logger.warning("fetch_vendor_feed failed for %s (%s): %s", vendor_name, rss_url, exc)
        return 0

    loop = asyncio.get_event_loop()
    items = await loop.run_in_executor(None, partial(_parse_feed, content))

    for item in items:
        url = item.get("url")
        if not url or url in existing_urls:
            continue

        combined = f"{item.get('title', '')} {item.get('summary', '')}"
        entities = _extract_entities(combined)

        record = VendorPressRelease(
            vendor_name=vendor_name,
            title=(item.get("title") or "")[:500],
            url=url[:2048],
            summary=item.get("summary"),
            published_at=item.get("published_at"),
            extracted_entities=json.dumps(entities),
            related_suppliers=json.dumps(entities["suppliers"]) if entities["suppliers"] else None,
            project_signals=json.dumps(entities["project_signals"]) if entities["project_signals"] else None,
        )
        db.add(record)
        existing_urls.add(url)
        saved += 1

    return saved


async def run_press_release_harvester(db: Session) -> int:
    """Harvest all configured vendor press release feeds.

    Returns the total count of newly saved records.
    """
    total = 0
    for vendor_name, rss_url in VENDOR_RSS_FEEDS.items():
        try:
            count = await fetch_vendor_feed(vendor_name, rss_url, db)
            total += count
        except Exception as exc:
            logger.error("Vendor feed %s failed: %s", vendor_name, exc)

    if total:
        db.commit()

    logger.info("press_release_harvester saved %d new records", total)
    return total


async def get_press_releases(
    db: Session,
    vendor_name: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
) -> list[VendorPressRelease]:
    """Return vendor press releases, optionally filtered by vendor name."""
    q = db.query(VendorPressRelease).order_by(VendorPressRelease.fetched_at.desc())
    if vendor_name:
        q = q.filter(VendorPressRelease.vendor_name.ilike(f"%{vendor_name}%"))
    return q.offset(skip).limit(limit).all()

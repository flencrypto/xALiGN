"""Infrastructure Announcement Monitor – tracks power, fibre and grid announcements.

Fetches RSS feeds from energy, infrastructure and industry publications,
categorises articles by infrastructure type using keyword matching, and
persists new records to ``infrastructure_announcements``.
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

from backend.models.intelligence import AnnouncementType, InfrastructureAnnouncement

logger = logging.getLogger("align.infra_monitor")

_TIMEOUT = 20.0

# ── Infrastructure RSS Feeds ──────────────────────────────────────────────────

INFRASTRUCTURE_RSS_FEEDS: list[dict] = [
    # Power / energy
    {"url": "https://www.power-technology.com/feed/", "name": "Power Technology"},
    {"url": "https://www.theengineer.co.uk/feed", "name": "The Engineer"},
    {"url": "https://www.energymonitor.ai/feed/", "name": "Energy Monitor"},
    {"url": "https://www.energy-storage.news/feed/", "name": "Energy Storage News"},
    {"url": "https://www.recharge-news.com/rss/", "name": "Recharge News"},
    {"url": "https://www.current-news.co.uk/feed/", "name": "Current±"},
    {"url": "https://www.endsreport.com/rss", "name": "ENDS Report"},
    # National Grid / transmission
    {"url": "https://www.nationalgrid.com/rss.xml", "name": "National Grid"},
    {"url": "https://www.ofgem.gov.uk/rss.xml", "name": "Ofgem"},
    # Fibre / telecoms infrastructure
    {"url": "https://www.ispreview.co.uk/feed.xml", "name": "ISP Review"},
    {"url": "https://www.telecoms.com/feed/", "name": "Telecoms.com"},
    {"url": "https://www.broadbandtvnews.com/feed/", "name": "Broadband TV News"},
    # Construction / civil engineering
    {"url": "https://www.constructionenquirer.com/feed/", "name": "Construction Enquirer"},
    {"url": "https://www.newcivilengineer.com/feed/", "name": "New Civil Engineer"},
    # Data centre / digital infra (overlap with news aggregator intentional for infra signals)
    {"url": "https://www.datacenterdynamics.com/rss/", "name": "Data Center Dynamics"},
    {"url": "https://www.capacitymedia.com/rss", "name": "Capacity Media"},
]

# ── Infrastructure Keywords by Type ──────────────────────────────────────────

INFRASTRUCTURE_KEYWORDS: dict[str, list[str]] = {
    AnnouncementType.power_grid: [
        "grid connection", "national grid", "transmission network", "distribution network",
        "power grid", "electricity grid", "high voltage", "grid reinforcement",
        "grid capacity", "grid upgrade", "new substation", "transformer",
        "132kv", "33kv", "11kv", "overhead line", "underground cable",
    ],
    AnnouncementType.fibre: [
        "fibre network", "fiber network", "dark fibre", "fibre rollout",
        "full fibre", "fttp", "fttc", "fibre backbone", "subsea cable",
        "fibre optic", "isp rollout", "broadband infrastructure",
    ],
    AnnouncementType.energy_deal: [
        "power purchase agreement", "ppa", "energy contract", "renewable deal",
        "green energy deal", "corporate ppa", "long-term energy",
        "energy procurement", "electricity supply agreement",
    ],
    AnnouncementType.substation: [
        "substation", "primary substation", "grid substation", "bulk supply point",
        "33kv substation", "132kv substation", "switching station",
        "hvdc", "flexible connection",
    ],
    AnnouncementType.data_centre: [
        "data centre", "data center", "campus expansion", "hyperscale facility",
        "colocation facility", "digital infrastructure campus", "compute campus",
        "server farm", "data hall", "hyperscale build",
    ],
}

_MW_PATTERN = re.compile(r"(\d[\d,\.]*)\s*(?:MW|megawatt)", re.IGNORECASE)
_GBP_PATTERN = re.compile(r"£([\d,\.]+)\s*(billion|million|bn|m)\b", re.IGNORECASE)

_UK_LOCATIONS_PATTERN = re.compile(
    r"\b(London|Manchester|Birmingham|Leeds|Edinburgh|Glasgow|Dublin|"
    r"Slough|Reading|Swindon|Cardiff|Bristol|Sheffield|Liverpool|"
    r"Newcastle|Belfast|Cambridge|Oxford|Milton Keynes|Dartford|"
    r"Coventry|Nottingham|Leicester|Norwich|Southampton|Portsmouth|"
    r"Aberdeen|Inverness|Dundee|Motherwell|Warrington|Stockport)\b",
    re.IGNORECASE,
)


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


def _categorise(text: str) -> tuple[AnnouncementType, list[str]]:
    """Return the best matching AnnouncementType and matched keywords."""
    text_lower = text.lower()
    best_type = AnnouncementType.general
    best_count = 0
    matched: list[str] = []

    for ann_type, keywords in INFRASTRUCTURE_KEYWORDS.items():
        hits = [kw for kw in keywords if kw in text_lower]
        if len(hits) > best_count:
            best_count = len(hits)
            best_type = ann_type
            matched = hits

    return best_type, matched


def _extract_capacity_mw(text: str) -> Optional[float]:
    match = _MW_PATTERN.search(text)
    if match:
        try:
            return float(match.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


def _extract_value_gbp(text: str) -> Optional[float]:
    match = _GBP_PATTERN.search(text)
    if match:
        try:
            amount = float(match.group(1).replace(",", ""))
            multiplier = match.group(2).lower()
            if multiplier in ("billion", "bn"):
                amount *= 1_000_000_000
            elif multiplier in ("million", "m"):
                amount *= 1_000_000
            return amount
        except ValueError:
            pass
    return None


def _extract_location(text: str) -> Optional[str]:
    match = _UK_LOCATIONS_PATTERN.search(text)
    return match.group(0) if match else None


# ── Public async API ──────────────────────────────────────────────────────────

async def fetch_infrastructure_feed(url: str, db: Session) -> int:
    """Fetch a single infrastructure RSS feed and persist new announcement records.

    Returns the count of newly saved records.
    """
    saved = 0

    existing_urls: set[str] = {
        row[0]
        for row in db.query(InfrastructureAnnouncement.source_url)
        .filter(InfrastructureAnnouncement.source_url.isnot(None))
        .all()
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "aLiGN-Intel/1.0"})
            resp.raise_for_status()
            content = resp.content
    except Exception as exc:
        logger.warning("fetch_infrastructure_feed failed for %s: %s", url, exc)
        return 0

    loop = asyncio.get_event_loop()
    items = await loop.run_in_executor(None, partial(_parse_feed, content))

    # Identify the feed's source name from our config list
    source_name = next(
        (f["name"] for f in INFRASTRUCTURE_RSS_FEEDS if f["url"] == url),
        None,
    )

    for item in items:
        item_url = item.get("url")
        if not item_url or item_url in existing_urls:
            continue

        combined = f"{item.get('title', '')} {item.get('summary', '')}"
        ann_type, matched = _categorise(combined)

        # Only save if it matches at least one keyword (skip generic non-infra articles)
        if not matched:
            continue

        record = InfrastructureAnnouncement(
            title=(item.get("title") or "")[:500],
            source_name=source_name,
            source_url=item_url[:2048],
            summary=item.get("summary"),
            announcement_type=ann_type,
            location=_extract_location(combined),
            capacity_mw=_extract_capacity_mw(combined),
            project_value_gbp=_extract_value_gbp(combined),
            keywords_matched=json.dumps(matched),
            published_at=item.get("published_at"),
        )
        db.add(record)
        existing_urls.add(item_url)
        saved += 1

    return saved


async def run_infra_monitor(db: Session) -> int:
    """Run the infrastructure monitor across all configured feeds.

    Returns the total count of newly saved records.
    """
    total = 0
    for feed in INFRASTRUCTURE_RSS_FEEDS:
        try:
            count = await fetch_infrastructure_feed(feed["url"], db)
            total += count
        except Exception as exc:
            logger.error("Infra feed %s failed: %s", feed["url"], exc)

    if total:
        db.commit()

    logger.info("infra_monitor saved %d new announcements", total)
    return total


async def get_infrastructure_announcements(
    db: Session,
    announcement_type: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
) -> list[InfrastructureAnnouncement]:
    """Return infrastructure announcements, optionally filtered by type."""
    q = db.query(InfrastructureAnnouncement).order_by(
        InfrastructureAnnouncement.detected_at.desc()
    )
    if announcement_type:
        q = q.filter(InfrastructureAnnouncement.announcement_type == announcement_type)
    return q.offset(skip).limit(limit).all()

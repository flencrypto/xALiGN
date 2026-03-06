"""News Intelligence Aggregator – collects and categorises data centre / hyperscaler news.

Fetches RSS feeds from industry publications, matches articles against keyword
filters, and persists new records to the ``news_articles`` table.
"""

import asyncio
import json
import logging
from functools import partial
from typing import Optional

import feedparser
import httpx
from sqlalchemy.orm import Session

from backend.models.intelligence import NewsArticle, NewsArticleCategory, NewsSourceType

logger = logging.getLogger("align.news_aggregator")

# ── RSS Feeds ─────────────────────────────────────────────────────────────────

RSS_FEEDS: list[dict] = [
    # Data centre trade press
    {"url": "https://www.datacenterdynamics.com/rss/", "name": "Data Center Dynamics"},
    {"url": "https://www.datacenterfrontier.com/feed/", "name": "Data Center Frontier"},
    {"url": "https://www.theregister.com/data_centre/feeds/atom.xml", "name": "The Register – DC"},
    {"url": "https://www.capacitymedia.com/rss", "name": "Capacity Media"},
    {"url": "https://www.datacentreworld.com/feed/", "name": "Data Centre World"},
    # Hyperscaler / cloud
    {"url": "https://feeds.feedburner.com/TechCrunch", "name": "TechCrunch"},
    {"url": "https://www.zdnet.com/topic/cloud/rss.xml", "name": "ZDNet Cloud"},
    {"url": "https://www.computerweekly.com/rss/IT-industry-news.xml", "name": "Computer Weekly"},
    # AI infrastructure
    {"url": "https://venturebeat.com/category/ai/feed/", "name": "VentureBeat AI"},
    {"url": "https://www.siliconrepublic.com/feed/", "name": "Silicon Republic"},
    # Power / energy
    {"url": "https://www.power-technology.com/feed/", "name": "Power Technology"},
    {"url": "https://www.theengineer.co.uk/feed", "name": "The Engineer"},
    {"url": "https://www.energymonitor.ai/feed/", "name": "Energy Monitor"},
    # UK infrastructure & construction
    {"url": "https://www.constructionenquirer.com/feed/", "name": "Construction Enquirer"},
    {"url": "https://www.newcivilengineer.com/feed/", "name": "New Civil Engineer"},
]

# ── Keyword Filters by Category ───────────────────────────────────────────────

KEYWORD_FILTERS: dict[str, list[str]] = {
    NewsArticleCategory.data_centre: [
        "data centre", "data center", "hyperscale", "colocation", "colo",
        "server farm", "compute campus", "digital infrastructure",
    ],
    NewsArticleCategory.hyperscaler: [
        "amazon aws", "google cloud", "microsoft azure", "meta data",
        "apple data", "oracle cloud", "alibaba cloud", "hyperscaler",
    ],
    NewsArticleCategory.supplier: [
        "schneider electric", "vertiv", "eaton", "siemens", "abb",
        "caterpillar", "cummins", "rolls-royce", "apc", "rittal",
        "legrand", "pue", "ups system", "cooling system", "chiller",
    ],
    NewsArticleCategory.ai_infrastructure: [
        "gpu cluster", "nvidia", "ai chip", "inference", "llm",
        "large language model", "ai factory", "ai campus", "tpu",
        "accelerator", "h100", "h200", "blackwell",
    ],
    NewsArticleCategory.power_infrastructure: [
        "grid connection", "substation", "power purchase agreement", "ppa",
        "renewable energy", "wind farm", "solar farm", "battery storage",
        "bess", "national grid", "transmission", "mw capacity",
    ],
    NewsArticleCategory.chips: [
        "semiconductor", "chip", "wafer", "tsmc", "intel fab",
        "amd", "arm", "foundry", "packaging", "hbm",
    ],
}

_TIMEOUT = 20.0


# ── Internal helpers ──────────────────────────────────────────────────────────

def _categorise(text: str) -> tuple[NewsArticleCategory, list[str]]:
    """Return the best matching category and the keywords found."""
    text_lower = text.lower()
    best_cat = NewsArticleCategory.general
    best_count = 0
    matched: list[str] = []

    for cat, keywords in KEYWORD_FILTERS.items():
        hits = [kw for kw in keywords if kw in text_lower]
        if len(hits) > best_count:
            best_count = len(hits)
            best_cat = cat
            matched = hits

    return best_cat, matched


def _parse_feed(raw_content: bytes) -> list[dict]:
    """Parse RSS/Atom bytes with feedparser (synchronous)."""
    parsed = feedparser.parse(raw_content)
    articles = []
    for entry in parsed.entries:
        articles.append({
            "title": entry.get("title", ""),
            "url": entry.get("link") or entry.get("id"),
            "summary": entry.get("summary") or entry.get("description"),
            "published_at": entry.get("published") or entry.get("updated"),
        })
    return articles


# ── Public async API ──────────────────────────────────────────────────────────

async def fetch_rss_feed(url: str) -> list[dict]:
    """Fetch and parse a single RSS/Atom feed URL.

    Returns a list of raw article dicts (title, url, summary, published_at).
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "aLiGN-Intel/1.0"})
            resp.raise_for_status()
            content = resp.content

        loop = asyncio.get_event_loop()
        articles = await loop.run_in_executor(None, partial(_parse_feed, content))
        return articles
    except Exception as exc:
        logger.warning("fetch_rss_feed failed for %s: %s", url, exc)
        return []


async def run_news_aggregator(db: Session) -> int:
    """Fetch all configured RSS feeds and persist new NewsArticle records.

    Returns the count of newly saved articles.
    """
    saved = 0

    # Collect existing URLs to avoid duplicates
    existing_urls: set[str] = {
        row[0]
        for row in db.query(NewsArticle.url).filter(NewsArticle.url.isnot(None)).all()
    }

    for feed in RSS_FEEDS:
        articles = await fetch_rss_feed(feed["url"])
        for art in articles:
            url = art.get("url")
            if not url or url in existing_urls:
                continue

            combined_text = f"{art.get('title', '')} {art.get('summary', '')}"
            category, matched = _categorise(combined_text)

            record = NewsArticle(
                title=(art.get("title") or "")[:500],
                url=url[:2048] if url else None,
                source_name=feed["name"],
                summary=art.get("summary"),
                category=category,
                keywords_matched=json.dumps(matched) if matched else None,
                published_at=art.get("published_at"),
                source_type=NewsSourceType.rss,
            )
            db.add(record)
            existing_urls.add(url)
            saved += 1

    if saved:
        db.commit()

    logger.info("news_aggregator saved %d new articles", saved)
    return saved


async def get_recent_articles(
    db: Session,
    category: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
) -> list[NewsArticle]:
    """Return recent news articles, optionally filtered by category."""
    q = db.query(NewsArticle).order_by(NewsArticle.fetched_at.desc())
    if category:
        q = q.filter(NewsArticle.category == category)
    return q.offset(skip).limit(limit).all()

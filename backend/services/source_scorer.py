"""Source Confidence Scorer – rates the credibility of each collected signal.

Uses a trust list of known-reliable sources, publication recency,
and content quality indicators to assign a confidence score (0.0 – 1.0).
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("align.source_scorer")

# ── Source Trust Registry ─────────────────────────────────────────────────────
# Score: 0.0 (untrustworthy) to 1.0 (authoritative)

SOURCE_TRUST: dict[str, float] = {
    # Tier 1 – official / regulatory sources
    "planning.london.gov.uk": 1.0,
    "gov.uk": 0.95,
    "ofgem.gov.uk": 0.95,
    "nationalgrid.com": 0.90,
    # Tier 1 – major wire services
    "reuters.com": 0.90,
    "bloomberg.com": 0.90,
    "ft.com": 0.88,
    "wsj.com": 0.87,
    "bbc.co.uk": 0.85,
    # Tier 2 – specialist trade press
    "datacenterdynamics.com": 0.88,
    "datacenterknowledge.com": 0.85,
    "theregister.com": 0.82,
    "computerweekly.com": 0.80,
    "zdnet.com": 0.78,
    "techcrunch.com": 0.75,
    "wired.com": 0.75,
    "arstechnica.com": 0.75,
    "networkworld.com": 0.72,
    # Tier 2 – energy / infrastructure press
    "spglobal.com": 0.82,
    "power-technology.com": 0.78,
    "energymonitor.ai": 0.75,
    "renewableenergyworld.com": 0.72,
    "powerengineeringint.com": 0.70,
    # Tier 3 – general business press
    "businesswire.com": 0.70,
    "prnewswire.com": 0.68,
    "globenewswire.com": 0.65,
    "accesswire.com": 0.60,
    # Tier 3 – quality press
    "theguardian.com": 0.78,
    "thetimes.co.uk": 0.75,
    "telegraph.co.uk": 0.72,
}

_DEFAULT_TRUST_SCORE = 0.50  # For unknown sources


def _get_domain(url: str) -> str:
    """Extract domain from URL."""
    match = re.search(r"https?://(?:www\.)?([^/]+)", url or "")
    return match.group(1).lower() if match else ""


def _recency_score(published_at: str | None) -> float:
    """Score based on how recent the article is (0.0-1.0)."""
    if not published_at:
        return 0.5

    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            pub_date = datetime.strptime(published_at, fmt)
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - pub_date).days
            if age_days <= 1:
                return 1.0
            elif age_days <= 7:
                return 0.9
            elif age_days <= 30:
                return 0.75
            elif age_days <= 90:
                return 0.55
            else:
                return 0.35
        except ValueError:
            continue
    return 0.5


def _content_quality_score(title: str, summary: str | None) -> float:
    """Score based on content indicators (length, specificity)."""
    text = f"{title} {summary or ''}"
    score = 0.5

    # Penalise very short content
    if len(text) < 50:
        score -= 0.2
    elif len(text) > 200:
        score += 0.1

    # Reward specific technical details
    if re.search(r"\d+\s*MW|megawatt", text, re.I):
        score += 0.15
    if re.search(r"[£$€]\d+", text):
        score += 0.1
    if re.search(r"\b(planning permission|approved|construction|operational)\b", text, re.I):
        score += 0.1

    return min(max(score, 0.0), 1.0)


def score_source(
    source_url: str | None,
    source_name: str | None,  # noqa: ARG001
    published_at: str | None,
    title: str,
    summary: str | None = None,
) -> dict[str, float]:
    """Calculate a composite confidence score for a signal source.

    Returns dict with:
      trust_score: 0.0-1.0 (source reliability)
      recency_score: 0.0-1.0 (how recent)
      content_score: 0.0-1.0 (content quality)
      composite_score: weighted composite (0.0-1.0)
    """
    domain = _get_domain(source_url or "")
    trust = SOURCE_TRUST.get(domain, _DEFAULT_TRUST_SCORE)
    recency = _recency_score(published_at)
    content = _content_quality_score(title, summary)

    composite = (trust * 0.50) + (recency * 0.30) + (content * 0.20)

    return {
        "trust_score": round(trust, 3),
        "recency_score": round(recency, 3),
        "content_score": round(content, 3),
        "composite_score": round(composite, 3),
    }


async def run_source_scoring(db) -> int:
    """Score all unscored signals in the database.

    Updates confidence_score on InfrastructureAnnouncement and NewsArticle.
    Returns count of records scored.
    """
    from backend.models.intelligence import InfrastructureAnnouncement, NewsArticle

    count = 0

    announcements = db.query(InfrastructureAnnouncement).filter(
        InfrastructureAnnouncement.confidence_score.is_(None)
    ).limit(100).all()

    for ann in announcements:
        scores = score_source(ann.source_url, ann.source_name, ann.published_at, ann.title, ann.summary)
        ann.confidence_score = scores["composite_score"]
        count += 1

    news = db.query(NewsArticle).filter(
        NewsArticle.confidence_score.is_(None)
    ).limit(100).all()

    for article in news:
        scores = score_source(article.url, article.source_name, article.published_at, article.title, article.summary)
        article.confidence_score = scores["composite_score"]
        count += 1

    db.commit()
    return count

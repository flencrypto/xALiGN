"""Planning Portal Scraper – monitors UK planning portals for data centre applications.

Scrapes public planning search portals, identifies data centre / infrastructure
applications by keyword matching, and persists results to ``planning_applications``.
"""

import json
import logging
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from backend.models.intelligence import PlanningApplication, PlanningApplicationStatus

logger = logging.getLogger("align.planning_scraper")

_TIMEOUT = 30.0
_HEADERS = {
    "User-Agent": "aLiGN-Intel/1.0 (planning research; contact admin@align.com)",
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.5",
}

# ── UK Planning Portals ───────────────────────────────────────────────────────

PLANNING_PORTALS: list[dict] = [
    {
        "name": "London Borough of Slough",
        "search_url": "https://www.slough.gov.uk/planning-building-control/search-planning-applications",
        "base_url": "https://www.slough.gov.uk",
    },
    {
        "name": "South Cambridgeshire District Council",
        "search_url": "https://applications.greatercambridgeplanning.org/online-applications/search.do?action=simple&searchType=Application",
        "base_url": "https://applications.greatercambridgeplanning.org",
    },
    {
        "name": "Swindon Borough Council",
        "search_url": "https://pa.swindon.gov.uk/publicaccess/search.do?action=simple&searchType=Application",
        "base_url": "https://pa.swindon.gov.uk",
    },
    {
        "name": "Milton Keynes City Council",
        "search_url": "https://www.milton-keynes.gov.uk/planning-and-building/planning-applications",
        "base_url": "https://www.milton-keynes.gov.uk",
    },
    {
        "name": "Hounslow London Borough",
        "search_url": "https://planning.hounslow.gov.uk/online-applications/search.do?action=simple&searchType=Application",
        "base_url": "https://planning.hounslow.gov.uk",
    },
    {
        "name": "Surrey Heath Borough Council",
        "search_url": "https://www.surreyheath.gov.uk/planning/planning-applications",
        "base_url": "https://www.surreyheath.gov.uk",
    },
    {
        "name": "Spelthorne Borough Council",
        "search_url": "https://www.spelthorne.gov.uk/planning",
        "base_url": "https://www.spelthorne.gov.uk",
    },
    {
        "name": "Planning Portal England (national)",
        "search_url": "https://www.planningportal.co.uk/applications",
        "base_url": "https://www.planningportal.co.uk",
    },
]

# ── Data Centre Keywords ──────────────────────────────────────────────────────

DATA_CENTRE_KEYWORDS: list[str] = [
    "data centre", "data center", "server room", "colocation",
    "hyperscale", "computer hall", "network operations centre",
    "cooling plant", "ups room", "generator building",
    "raised floor", "computer suite", "it building",
    "data hall", "digital infrastructure",
]

_STATUS_MAP: dict[str, PlanningApplicationStatus] = {
    "approved": PlanningApplicationStatus.approved,
    "granted": PlanningApplicationStatus.approved,
    "refused": PlanningApplicationStatus.refused,
    "rejected": PlanningApplicationStatus.refused,
    "withdrawn": PlanningApplicationStatus.withdrawn,
    "pending": PlanningApplicationStatus.pending,
    "submitted": PlanningApplicationStatus.submitted,
    "received": PlanningApplicationStatus.submitted,
}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _is_data_centre(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in DATA_CENTRE_KEYWORDS)


def _detect_status(text: str) -> PlanningApplicationStatus:
    text_lower = text.lower()
    for keyword, status in _STATUS_MAP.items():
        if keyword in text_lower:
            return status
    return PlanningApplicationStatus.pending


def _extract_reference(text: str) -> str | None:
    """Try to extract a UK planning reference number from text."""
    match = re.search(r"\b\d{2}/\d{4,6}(?:/[A-Z]+)?\b", text)
    return match.group(0) if match else None


def _parse_portal_html(html: str, portal: dict) -> list[dict]:
    """Extract planning application rows from search result HTML."""
    soup = BeautifulSoup(html, "html.parser")
    applications = []

    # Generic table-based extraction (common to many UK planning portals)
    for row in soup.select("tr, .application-item, .search-result, li.result"):
        text = row.get_text(" ", strip=True)
        if len(text) < 20:
            continue

        title = ""
        link = row.find("a")
        if link:
            title = link.get_text(strip=True)[:500]

        if not title:
            title = text[:200]

        reference = _extract_reference(text)
        app_url = None
        if link and link.get("href"):
            href = link["href"]
            app_url = href if href.startswith("http") else portal["base_url"] + href

        applications.append({
            "title": title,
            "description": text[:2000],
            "reference": reference,
            "portal_url": app_url,
            "status_text": text,
        })

    return applications


# ── Public async API ──────────────────────────────────────────────────────────

async def scrape_planning_portal(portal: dict, db: Session) -> list[PlanningApplication]:
    """Scrape a single planning portal and return newly created PlanningApplication objects."""
    results: list[PlanningApplication] = []

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(portal["search_url"], headers=_HEADERS)
            resp.raise_for_status()
            html = resp.text
    except Exception as exc:
        logger.warning("scrape_planning_portal failed for %s: %s", portal["name"], exc)
        return results

    raw_apps = _parse_portal_html(html, portal)

    # Fetch existing portal URLs/references to deduplicate
    existing_refs: set[str] = {
        row[0]
        for row in db.query(PlanningApplication.reference)
        .filter(PlanningApplication.reference.isnot(None))
        .all()
    }
    existing_urls: set[str] = {
        row[0]
        for row in db.query(PlanningApplication.portal_url)
        .filter(PlanningApplication.portal_url.isnot(None))
        .all()
    }

    for raw in raw_apps:
        ref = raw.get("reference")
        url = raw.get("portal_url")

        if ref and ref in existing_refs:
            continue
        if url and url in existing_urls:
            continue

        is_dc = _is_data_centre(raw.get("description", "") + " " + raw.get("title", ""))
        status = _detect_status(raw.get("status_text", ""))

        record = PlanningApplication(
            reference=ref,
            title=raw["title"][:500],
            description=raw.get("description"),
            portal_name=portal["name"],
            portal_url=url[:2048] if url else None,
            status=status,
            is_data_centre=is_dc,
        )
        db.add(record)

        if ref:
            existing_refs.add(ref)
        if url:
            existing_urls.add(url)

        results.append(record)

    return results


async def run_planning_scraper(db: Session) -> int:
    """Run the planning scraper across all configured portals.

    Returns total count of newly saved records.
    """
    total = 0
    for portal in PLANNING_PORTALS:
        try:
            new_records = await scrape_planning_portal(portal, db)
            total += len(new_records)
        except Exception as exc:
            logger.error("Portal %s failed: %s", portal["name"], exc)

    if total:
        db.commit()

    logger.info("planning_scraper saved %d new applications", total)
    return total


async def get_planning_applications(
    db: Session,
    is_data_centre: Optional[bool] = None,
    limit: int = 50,
    skip: int = 0,
) -> list[PlanningApplication]:
    """Return planning applications, optionally filtered to data centre projects."""
    q = db.query(PlanningApplication).order_by(PlanningApplication.detected_at.desc())
    if is_data_centre is not None:
        q = q.filter(PlanningApplication.is_data_centre == is_data_centre)
    return q.offset(skip).limit(limit).all()

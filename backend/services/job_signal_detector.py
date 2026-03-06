"""Job Posting Signal Detector – identifies hiring spikes at hyperscalers / DC operators.

Scrapes public job board search pages for data centre-relevant job titles at
known hyperscaler companies, detects statistically significant hiring spikes,
and persists results to ``job_posting_signals``.
"""

import json
import logging
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.intelligence import JobPostingSignal

logger = logging.getLogger("align.job_signal_detector")

_TIMEOUT = 25.0
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; aLiGN-Intel/1.0; +https://align.com/bot)",
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.5",
}

# ── Hyperscaler / DC operator companies ──────────────────────────────────────

HYPERSCALER_COMPANIES: list[str] = [
    "Amazon Web Services", "Google Cloud", "Microsoft Azure", "Meta",
    "Apple", "Oracle", "Alibaba Cloud", "IBM Cloud", "Salesforce",
    "CyrusOne", "Equinix", "Digital Realty", "NTT Global Data Centers",
    "Lumen Technologies", "Switch", "Iron Mountain",
    "Colt Data Centre Services", "Virtus Data Centres",
    "Ark Data Centres", "TelecityGroup", "Pulsant",
    "Vantage Data Centers", "QTS Realty Trust",
    "Global Switch", "Kao Data", "Proximity Data Centres",
]

# ── Job titles indicating DC build / expansion activity ──────────────────────

DATA_CENTRE_JOB_TITLES: list[str] = [
    "Data Centre Engineer", "Data Center Engineer",
    "Critical Facilities Engineer", "Data Centre Technician",
    "Data Centre Operations Manager", "Facilities Manager Data Centre",
    "MEP Engineer Data Centre", "Electrical Engineer Data Centre",
    "Mechanical Engineer Data Centre", "Cooling Engineer",
    "Power Systems Engineer", "UPS Engineer",
    "Construction Project Manager Data Centre",
    "Data Centre Commissioning Engineer",
    "Network Operations Centre Engineer", "NOC Engineer",
    "Infrastructure Engineer", "Site Reliability Engineer",
    "Data Hall Technician", "Critical Environment Technician",
]

# ── Public job board search URLs ──────────────────────────────────────────────

JOB_BOARD_URLS: dict[str, str] = {
    "indeed_uk": "https://uk.indeed.com/jobs?q={enc_title}+{enc_company}&l=United+Kingdom",
    "reed": "https://www.reed.co.uk/jobs/{slug_title}-jobs?keywords={enc_title}+{enc_company}",
    "cwjobs": "https://www.cwjobs.co.uk/jobs/{slug_title}?keywords={enc_title}+{enc_company}",
    "jobsite": "https://www.jobsite.co.uk/jobs/{slug_title}?keywords={enc_title}+{enc_company}",
}

# Spike detection: flag if recent 30-day count is this multiple of baseline
SPIKE_THRESHOLD = 2.0


# ── Internal helpers ──────────────────────────────────────────────────────────

def _build_search_url(board: str, company: str, title: str) -> str:
    tpl = JOB_BOARD_URLS.get(board, "")
    slug_title = re.sub(r"\s+", "-", title.lower())
    enc_title = re.sub(r"\s+", "+", title)
    enc_company = re.sub(r"\s+", "+", company)
    return tpl.format(slug_title=slug_title, enc_title=enc_title, enc_company=enc_company)


def _extract_job_count(html: str) -> int:
    """Try to extract a job result count from search result HTML."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ")

    # Common patterns: "1,234 jobs", "123 results", "Found 56 jobs"
    for pattern in [
        r"([\d,]+)\s+jobs?",
        r"([\d,]+)\s+results?",
        r"Found\s+([\d,]+)",
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))

    # Count individual job listings as fallback
    listings = soup.select(".job, .result, .job-listing, article.result, div[data-jk]")
    return len(listings)


def _extract_job_titles(html: str, limit: int = 5) -> list[str]:
    """Extract job title strings from result HTML."""
    soup = BeautifulSoup(html, "html.parser")
    titles = []
    for sel in ["h2.jobTitle", "a.jobtitle", ".job-title", "h3.title", "h2.title"]:
        for el in soup.select(sel)[:limit]:
            text = el.get_text(strip=True)
            if text:
                titles.append(text)
    return titles[:limit]


# ── Public async API ──────────────────────────────────────────────────────────

async def search_job_board(company: str, db: Session) -> list[JobPostingSignal]:
    """Search Indeed UK for data centre jobs at *company* and return new signal records."""
    signals: list[JobPostingSignal] = []

    board = "indeed_uk"
    for title in DATA_CENTRE_JOB_TITLES[:5]:  # limit to top-5 titles per run to be polite
        url = _build_search_url(board, company, title)
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
                resp = await client.get(url, headers=_HEADERS)
                resp.raise_for_status()
                html = resp.text
        except Exception as exc:
            logger.warning("job board search failed (%s / %s): %s", company, title, exc)
            continue

        job_count = _extract_job_count(html)
        if job_count == 0:
            continue

        signal = JobPostingSignal(
            company_name=company,
            job_title=title,
            job_count=job_count,
            posting_url=url[:2048],
            source_board=board,
            location="United Kingdom",
        )
        db.add(signal)
        signals.append(signal)

    return signals


async def detect_hiring_spikes(db: Session) -> int:
    """Compare recent (30-day) job counts against older baseline to flag spikes.

    Marks ``is_spike=True`` and sets ``spike_factor`` on qualifying records.
    Returns count of newly flagged spikes.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import and_

    cutoff_recent = datetime.utcnow() - timedelta(days=30)
    cutoff_baseline = datetime.utcnow() - timedelta(days=90)

    flagged = 0

    # Group by company + title for both windows
    recent_q = (
        db.query(
            JobPostingSignal.company_name,
            JobPostingSignal.job_title,
            func.sum(JobPostingSignal.job_count).label("total"),
        )
        .filter(JobPostingSignal.detected_at >= cutoff_recent)
        .group_by(JobPostingSignal.company_name, JobPostingSignal.job_title)
        .all()
    )

    baseline_q = (
        db.query(
            JobPostingSignal.company_name,
            JobPostingSignal.job_title,
            func.sum(JobPostingSignal.job_count).label("total"),
        )
        .filter(
            and_(
                JobPostingSignal.detected_at >= cutoff_baseline,
                JobPostingSignal.detected_at < cutoff_recent,
            )
        )
        .group_by(JobPostingSignal.company_name, JobPostingSignal.job_title)
        .all()
    )

    baseline_map = {
        (row.company_name, row.job_title): row.total for row in baseline_q
    }

    for row in recent_q:
        baseline = baseline_map.get((row.company_name, row.job_title), 0)
        if baseline > 0:
            factor = row.total / baseline
        else:
            factor = float(row.total)  # any posting where none existed is a spike

        if factor >= SPIKE_THRESHOLD:
            # Update the most recent matching record
            record = (
                db.query(JobPostingSignal)
                .filter(
                    JobPostingSignal.company_name == row.company_name,
                    JobPostingSignal.job_title == row.job_title,
                    JobPostingSignal.detected_at >= cutoff_recent,
                )
                .order_by(JobPostingSignal.detected_at.desc())
                .first()
            )
            if record and not record.is_spike:
                record.is_spike = True
                record.spike_factor = round(factor, 2)
                record.is_expansion_signal = True
                flagged += 1

    if flagged:
        db.commit()

    logger.info("detect_hiring_spikes flagged %d spike records", flagged)
    return flagged


async def run_job_signal_detector(db: Session) -> int:
    """Run the full job signal detection cycle for all configured companies.

    Returns the total count of newly saved signal records.
    """
    total = 0
    for company in HYPERSCALER_COMPANIES:
        try:
            signals = await search_job_board(company, db)
            total += len(signals)
        except Exception as exc:
            logger.error("Job search for %s failed: %s", company, exc)

    if total:
        db.commit()

    # After saving, run spike detection
    await detect_hiring_spikes(db)

    logger.info("job_signal_detector saved %d new signal records", total)
    return total


async def get_job_signals(
    db: Session,
    company_name: Optional[str] = None,
    is_spike: Optional[bool] = None,
    limit: int = 50,
    skip: int = 0,
) -> list[JobPostingSignal]:
    """Return job posting signals, optionally filtered by company or spike status."""
    q = db.query(JobPostingSignal).order_by(JobPostingSignal.detected_at.desc())
    if company_name:
        q = q.filter(JobPostingSignal.company_name.ilike(f"%{company_name}%"))
    if is_spike is not None:
        q = q.filter(JobPostingSignal.is_spike == is_spike)
    return q.offset(skip).limit(limit).all()

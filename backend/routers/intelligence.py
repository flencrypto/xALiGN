"""Intelligence Collection Layer router.

Endpoints:
  POST /api/v1/intelligence/news/run               – Trigger news aggregator
  GET  /api/v1/intelligence/news                   – List news articles
  POST /api/v1/intelligence/planning/run           – Trigger planning scraper
  GET  /api/v1/intelligence/planning               – List planning applications
  POST /api/v1/intelligence/press-releases/run     – Trigger press release harvester
  GET  /api/v1/intelligence/press-releases         – List vendor press releases
  POST /api/v1/intelligence/jobs/run               – Trigger job signal detector
  GET  /api/v1/intelligence/jobs                   – List job signals
  POST /api/v1/intelligence/infrastructure/run     – Trigger infrastructure monitor
  GET  /api/v1/intelligence/infrastructure         – List infrastructure announcements
  GET  /api/v1/intelligence/status                 – Collector status dashboard
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.intelligence import (
    InfrastructureAnnouncement,
    JobPostingSignal,
    NewsArticle,
    PlanningApplication,
    VendorPressRelease,
)
from backend.services.infra_monitor import (
    get_infrastructure_announcements,
    run_infra_monitor,
)
from backend.services.job_signal_detector import (
    get_job_signals,
    run_job_signal_detector,
)
from backend.services.news_aggregator import get_recent_articles, run_news_aggregator
from backend.services.planning_scraper import (
    get_planning_applications,
    run_planning_scraper,
)
from backend.services.press_release_harvester import (
    get_press_releases,
    run_press_release_harvester,
)

logger = logging.getLogger("align.intelligence")

router = APIRouter(prefix="/intelligence", tags=["Intelligence Collection"])


# ── News ──────────────────────────────────────────────────────────────────────

@router.post("/news/run", summary="Trigger the News Intelligence Aggregator")
async def trigger_news_aggregator(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Manually trigger the news aggregator and return the count of new articles saved."""
    count = await run_news_aggregator(db)
    return {"status": "ok", "new_records": count, "collector": "news_aggregator"}


@router.get("/news", summary="List collected news articles")
async def list_news_articles(
    category: Optional[str] = Query(default=None, description="Filter by NewsArticleCategory"),
    limit: int = Query(default=50, ge=1, le=500),
    skip: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    articles = await get_recent_articles(db, category=category, limit=limit, skip=skip)
    return [_serialise_model(a) for a in articles]


# ── Planning ──────────────────────────────────────────────────────────────────

@router.post("/planning/run", summary="Trigger the Planning Portal Scraper")
async def trigger_planning_scraper(db: Session = Depends(get_db)) -> dict[str, Any]:
    count = await run_planning_scraper(db)
    return {"status": "ok", "new_records": count, "collector": "planning_scraper"}


@router.get("/planning", summary="List planning applications")
async def list_planning_applications(
    is_data_centre: Optional[bool] = Query(default=None, description="Filter to data centre projects only"),
    limit: int = Query(default=50, ge=1, le=500),
    skip: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    apps = await get_planning_applications(db, is_data_centre=is_data_centre, limit=limit, skip=skip)
    return [_serialise_model(a) for a in apps]


# ── Press Releases ────────────────────────────────────────────────────────────

@router.post("/press-releases/run", summary="Trigger the Vendor Press Release Harvester")
async def trigger_press_release_harvester(db: Session = Depends(get_db)) -> dict[str, Any]:
    count = await run_press_release_harvester(db)
    return {"status": "ok", "new_records": count, "collector": "press_release_harvester"}


@router.get("/press-releases", summary="List vendor press releases")
async def list_press_releases(
    vendor_name: Optional[str] = Query(default=None, description="Filter by vendor name (partial match)"),
    limit: int = Query(default=50, ge=1, le=500),
    skip: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    releases = await get_press_releases(db, vendor_name=vendor_name, limit=limit, skip=skip)
    return [_serialise_model(r) for r in releases]


# ── Job Signals ───────────────────────────────────────────────────────────────

@router.post("/jobs/run", summary="Trigger the Job Posting Signal Detector")
async def trigger_job_signal_detector(db: Session = Depends(get_db)) -> dict[str, Any]:
    count = await run_job_signal_detector(db)
    return {"status": "ok", "new_records": count, "collector": "job_signal_detector"}


@router.get("/jobs", summary="List job posting signals")
async def list_job_signals(
    company_name: Optional[str] = Query(default=None, description="Filter by company name (partial match)"),
    is_spike: Optional[bool] = Query(default=None, description="Filter to hiring spikes only"),
    limit: int = Query(default=50, ge=1, le=500),
    skip: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    signals = await get_job_signals(
        db, company_name=company_name, is_spike=is_spike, limit=limit, skip=skip
    )
    return [_serialise_model(s) for s in signals]


# ── Infrastructure ────────────────────────────────────────────────────────────

@router.post("/infrastructure/run", summary="Trigger the Infrastructure Announcement Monitor")
async def trigger_infra_monitor(db: Session = Depends(get_db)) -> dict[str, Any]:
    count = await run_infra_monitor(db)
    return {"status": "ok", "new_records": count, "collector": "infra_monitor"}


@router.get("/infrastructure", summary="List infrastructure announcements")
async def list_infrastructure_announcements(
    announcement_type: Optional[str] = Query(
        default=None, description="Filter by AnnouncementType"
    ),
    limit: int = Query(default=50, ge=1, le=500),
    skip: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    announcements = await get_infrastructure_announcements(
        db, announcement_type=announcement_type, limit=limit, skip=skip
    )
    return [_serialise_model(a) for a in announcements]


# ── Status Dashboard ──────────────────────────────────────────────────────────

@router.get("/status", summary="Intelligence collector status dashboard")
def get_collector_status(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return record counts and the timestamp of the most-recent record for each collector."""
    from sqlalchemy import func

    def _stats(model, ts_col):
        count = db.query(func.count(model.id)).scalar() or 0
        latest = db.query(func.max(ts_col)).scalar()
        return {"record_count": count, "last_collected_at": str(latest) if latest else None}

    return {
        "news_aggregator": _stats(NewsArticle, NewsArticle.fetched_at),
        "planning_scraper": _stats(PlanningApplication, PlanningApplication.detected_at),
        "press_release_harvester": _stats(VendorPressRelease, VendorPressRelease.fetched_at),
        "job_signal_detector": _stats(JobPostingSignal, JobPostingSignal.detected_at),
        "infra_monitor": _stats(InfrastructureAnnouncement, InfrastructureAnnouncement.detected_at),
    }


# ── Serialisation helper ──────────────────────────────────────────────────────

def _serialise_model(obj) -> dict[str, Any]:
    """Convert a SQLAlchemy model instance to a plain dict."""
    result = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        # Convert enum values to their string representation
        if hasattr(val, "value"):
            val = val.value
        result[col.name] = val
    return result

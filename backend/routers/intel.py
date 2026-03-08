"""Company intelligence router.

Endpoints:
  POST /api/v1/intel/company              – Trigger deep research on a company URL
  GET  /api/v1/intel/companies            – List all company intelligence snapshots
  GET  /api/v1/intel/companies/{id}       – Get a full intelligence snapshot
  DELETE /api/v1/intel/companies/{id}     – Delete a snapshot
  GET  /api/v1/intel/news                 – List tracked news items
  POST /api/v1/intel/news                 – Manually add a news item
  POST /api/v1/intel/orchestrate          – Trigger AI orchestrator for any event type
  GET  /api/v1/intel/governance/logs      – Get recent AI governance logs
  POST /api/v1/intel/earnings/analyze     – Analyze an earnings transcript (Worker 4)
  POST /api/v1/intel/relationship/timing  – Relationship timing engine (Worker 6)
  POST /api/v1/intel/trends/detect        – Signal clustering & trend detection (Worker 9)
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.intel import CompanyIntel, ExecutiveProfile, NewsItem
from backend.schemas.intel import (
    CompanyIntelRead,
    CompanyIntelRequest,
    CompanyIntelSummary,
    NewsItemCreate,
    NewsItemRead,
)
from backend.services import crawler, grok_client
from backend.services.ai_workers import (
    EarningsCallWorker,
    RelationshipTimingWorker,
    TrendDetectionWorker,
)
from backend.services.governance import GovernanceLogger
from backend.services.integration_requirements import ensure_integration_configured
from backend.services.orchestrator import Orchestrator

logger = logging.getLogger("align.intel")

router = APIRouter(prefix="/intel", tags=["Intelligence"])


def _serialise(value) -> str | None:
    """Convert list or dict to JSON string for storage, pass strings through."""
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return str(value)


# ── Company Research ──────────────────────────────────────────────────────────

@router.post(
    "/company",
    response_model=CompanyIntelRead,
    status_code=status.HTTP_201_CREATED,
    summary="Deep research a company from its website URL",
)
async def research_company(payload: CompanyIntelRequest, db: Session = Depends(get_db)):
    """
    Crawl the company website and run Grok deep research to extract structured
    intelligence signals: expansion indicators, technology growth, earnings
    highlights, competitor mentions, executive profiles, and bid opportunities.

    Requires XAI_API_KEY to be configured.
    """
    ensure_integration_configured(
        integration_id="grok_ai",
        integration_name="Grok AI",
        required_env_vars=["XAI_API_KEY"],
        setup_path="/setup#grok_ai",
    )

    # 1. Crawl public pages
    homepage_text = await crawler.crawl_homepage(payload.website)
    leadership_text = await crawler.crawl_leadership_pages(payload.website)

    if not homepage_text and not leadership_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not retrieve any content from the provided website.",
        )

    # 2. Company intelligence via Grok
    intel_data = await grok_client.research_company(payload.website, homepage_text)

    company_name = intel_data.get("company_name") or ""

    obj = CompanyIntel(
        website=payload.website,
        company_name=company_name or None,
        business_model=_serialise(intel_data.get("business_model")),
        locations=_serialise(intel_data.get("locations")),
        expansion_signals=_serialise(intel_data.get("expansion_signals")),
        technology_indicators=_serialise(intel_data.get("technology_indicators")),
        financial_summary=_serialise(intel_data.get("financial_summary")),
        earnings_highlights=_serialise(intel_data.get("earnings_highlights")),
        competitor_mentions=_serialise(intel_data.get("competitor_mentions")),
        strategic_risks=_serialise(intel_data.get("strategic_risks")),
        bid_opportunities=_serialise(intel_data.get("bid_opportunities")),
        stock_ticker=intel_data.get("stock_ticker") or None,
        stock_price=intel_data.get("stock_price") or None,
        raw_response=intel_data.get("raw_response"),
    )
    db.add(obj)
    db.flush()  # get obj.id before adding children

    # 3. Executive profiles (public professional data only)
    if leadership_text:
        try:
            exec_profiles = await grok_client.research_executives(
                company_name or payload.website, leadership_text
            )
            for ep in exec_profiles:
                profile = ExecutiveProfile(
                    company_intel_id=obj.id,
                    name=ep.get("name", "Unknown"),
                    role=ep.get("role"),
                    professional_focus=_serialise(ep.get("professional_focus")),
                    public_interests=_serialise(ep.get("public_interests")),
                    recent_interviews=_serialise(ep.get("recent_interviews")),
                    conference_appearances=_serialise(ep.get("conference_appearances")),
                    charity_involvement=_serialise(ep.get("charity_involvement")),
                    communication_style=ep.get("communication_style"),
                    conversation_angles=_serialise(ep.get("conversation_angles")),
                )
                db.add(profile)
        except Exception as exc:
            logger.warning("Executive profiling failed (non-fatal): %s", exc)

    # 4. Social media signals (LinkedIn & X posts)
    try:
        social_data = await grok_client.research_social_media(
            company_name or payload.website, homepage_text
        )
        obj.linkedin_posts = _serialise(social_data.get("linkedin_posts")) or None
        obj.x_posts = _serialise(social_data.get("x_posts")) or None
    except Exception as exc:
        logger.warning("Social media research failed (non-fatal): %s", exc)

    db.commit()
    db.refresh(obj)
    return obj


@router.get(
    "/companies",
    response_model=list[CompanyIntelSummary],
    summary="List all company intelligence snapshots",
)
def list_companies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(CompanyIntel).order_by(CompanyIntel.created_at.desc()).offset(skip).limit(limit).all()


@router.get(
    "/companies/{intel_id}",
    response_model=CompanyIntelRead,
    summary="Get a full company intelligence snapshot",
)
def get_company_intel(intel_id: int, db: Session = Depends(get_db)):
    obj = db.get(CompanyIntel, intel_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Company intel not found")
    return obj


@router.delete(
    "/companies/{intel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a company intelligence snapshot",
)
def delete_company_intel(intel_id: int, db: Session = Depends(get_db)):
    obj = db.get(CompanyIntel, intel_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Company intel not found")
    db.delete(obj)
    db.commit()


# ── News Feed ─────────────────────────────────────────────────────────────────

@router.get(
    "/news",
    response_model=list[NewsItemRead],
    summary="List tracked news items",
)
def list_news(
    company_intel_id: int | None = None,
    category: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Return news items, optionally filtered by company or category."""
    q = db.query(NewsItem).order_by(NewsItem.detected_at.desc())
    if company_intel_id is not None:
        q = q.filter(NewsItem.company_intel_id == company_intel_id)
    if category is not None:
        q = q.filter(NewsItem.category == category)
    return q.offset(skip).limit(limit).all()


@router.post(
    "/news",
    response_model=NewsItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Manually add a news item",
)
def create_news_item(payload: NewsItemCreate, db: Session = Depends(get_db)):
    obj = NewsItem(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── AI Orchestration Endpoints ────────────────────────────────────────────────

_orchestrator = Orchestrator()
_earnings_worker = EarningsCallWorker()
_timing_worker = RelationshipTimingWorker()
_trend_worker = TrendDetectionWorker()


class OrchestrateRequest(BaseModel):
    event_type: str
    context: dict[str, Any] = {}
    event_id: str | None = None


class EarningsAnalyzeRequest(BaseModel):
    transcript: str = Field(..., max_length=100_000)


class RelationshipTimingRequest(BaseModel):
    company_name: str = Field(..., max_length=500)
    events: list[dict[str, Any]] = []


class TrendDetectRequest(BaseModel):
    signals_text: str = Field(..., max_length=100_000)


@router.post(
    "/orchestrate",
    summary="Trigger the AI orchestrator for any event type",
)
async def orchestrate(payload: OrchestrateRequest):
    """
    Route an event to the matching AI worker.

    Supported event_type values: new_company, new_tender, new_earnings,
    new_call, new_signal, new_image.
    """
    return await _orchestrator.dispatch(
        event_type=payload.event_type,
        context=payload.context,
        event_id=payload.event_id,
    )


@router.get(
    "/governance/logs",
    summary="Get recent AI governance logs",
)
def get_governance_logs(n: int = Query(default=100, ge=1, le=1000)):
    """Return the last *n* AI worker invocation log entries (most-recent first)."""
    return GovernanceLogger.recent(n)


@router.post(
    "/earnings/analyze",
    summary="Analyze an earnings call transcript (Worker 4)",
)
async def analyze_earnings(payload: EarningsAnalyzeRequest):
    """Extract structured signals from an earnings call transcript using Worker 4."""
    if not payload.transcript:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="transcript is required",
        )
    return await _earnings_worker.run(transcript=payload.transcript)


@router.post(
    "/relationship/timing",
    summary="Run relationship timing engine (Worker 6)",
)
async def relationship_timing(payload: RelationshipTimingRequest):
    """Compute relationship timing score and outreach recommendation using Worker 6."""
    return await _timing_worker.run(
        company_name=payload.company_name,
        events=payload.events,
    )


@router.post(
    "/trends/detect",
    summary="Signal clustering and trend detection (Worker 9)",
)
async def detect_trends(payload: TrendDetectRequest):
    """Identify emerging themes and anomalies from signal data using Worker 9."""
    if not payload.signals_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="signals_text is required",
        )
    return await _trend_worker.run(signals_context=payload.signals_text)

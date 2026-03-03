"""FastAPI router for the AI Intelligence Layer."""

import asyncio
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.intelligence import BlogDraft, CompanyIntelligence, IntelPhoto, NewsSignal
from backend.schemas.intelligence import (
    BlogDraftApprove,
    BlogDraftRead,
    CompanyIntelligenceCreate,
    CompanyIntelligenceRead,
    IntelPhotoRead,
    IntelResearchResponse,
)
from backend.services.intelligence_service import (
    generate_blog_draft,
    research_company,
    save_photo_local,
)

logger = logging.getLogger("contractghost.intelligence")

router = APIRouter(prefix="/api/intel", tags=["Intelligence"])


# ── Background task wrapper ───────────────────────────────────────────────────

def _run_research_background(website_url: str, intelligence_id: int) -> None:
    """Run the async research_company coroutine inside a background thread."""
    from backend.database import SessionLocal

    db = SessionLocal()
    try:
        asyncio.run(research_company(website_url, db))
    except Exception as exc:
        logger.error("Background research failed for %s: %s", website_url, exc)
        intel = db.get(CompanyIntelligence, intelligence_id)
        if intel:
            intel.status = "failed"
            intel.error_message = str(exc)
            db.commit()
    finally:
        db.close()


# ── Company intelligence ──────────────────────────────────────────────────────

@router.post("/company", response_model=IntelResearchResponse, status_code=status.HTTP_202_ACCEPTED)
def create_company_intelligence(
    payload: CompanyIntelligenceCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create an intelligence record and trigger asynchronous research."""
    intel = CompanyIntelligence(
        website_url=payload.website_url,
        account_id=payload.account_id,
        status="processing",
    )
    db.add(intel)
    db.commit()
    db.refresh(intel)

    background_tasks.add_task(_run_research_background, payload.website_url, intel.id)

    return IntelResearchResponse(
        company_summary=CompanyIntelligenceRead.model_validate(intel),
        executive_profiles=[],
        expansion_signals=[],
        news_feed=[],
    )


@router.get("/company", response_model=list[CompanyIntelligenceRead])
def list_company_intelligence(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """Return a paginated list of all company intelligence records."""
    return db.query(CompanyIntelligence).offset(skip).limit(limit).all()


@router.get("/company/{intelligence_id}", response_model=CompanyIntelligenceRead)
def get_company_intelligence(intelligence_id: int, db: Session = Depends(get_db)):
    """Retrieve a single company intelligence record including profiles and signals."""
    obj = db.get(CompanyIntelligence, intelligence_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Company intelligence record not found")
    return obj


# ── Blog drafts ───────────────────────────────────────────────────────────────

@router.post("/company/{intelligence_id}/blog", response_model=BlogDraftRead, status_code=status.HTTP_201_CREATED)
def trigger_blog_generation(intelligence_id: int, db: Session = Depends(get_db)):
    """Generate a blog draft from an existing company intelligence record."""
    intel = db.get(CompanyIntelligence, intelligence_id)
    if not intel:
        raise HTTPException(status_code=404, detail="Company intelligence record not found")
    try:
        draft = asyncio.run(generate_blog_draft(intel, db))
    except Exception as exc:
        logger.error("Blog generation failed for intelligence %d: %s", intelligence_id, exc)
        raise HTTPException(status_code=500, detail=f"Blog generation failed: {exc}") from exc
    return draft


@router.get("/blogs", response_model=list[BlogDraftRead])
def list_blog_drafts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Return a paginated list of all blog drafts."""
    return db.query(BlogDraft).offset(skip).limit(limit).all()


@router.get("/blogs/{blog_id}", response_model=BlogDraftRead)
def get_blog_draft(blog_id: int, db: Session = Depends(get_db)):
    """Retrieve a single blog draft by ID."""
    obj = db.get(BlogDraft, blog_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Blog draft not found")
    return obj


@router.put("/blogs/{blog_id}/approve", response_model=BlogDraftRead)
def approve_blog_draft(blog_id: int, payload: BlogDraftApprove, db: Session = Depends(get_db)):
    """Update the status of a blog draft (e.g. approved, published)."""
    obj = db.get(BlogDraft, blog_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Blog draft not found")
    obj.status = payload.status
    obj.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj


# ── Photos ────────────────────────────────────────────────────────────────────

@router.post("/photos/upload", response_model=IntelPhotoRead, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    file: UploadFile = File(...),
    intelligence_id: int | None = Query(None),
    account_id: int | None = Query(None),
    photo_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Accept a multipart file upload and persist an IntelPhoto record."""
    try:
        file_content = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {exc}") from exc

    return save_photo_local(
        file_content=file_content,
        filename=file.filename or "upload",
        intelligence_id=intelligence_id,
        account_id=account_id,
        photo_type=photo_type,
        db=db,
    )


@router.get("/photos", response_model=list[IntelPhotoRead])
def list_photos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Return a paginated list of all intel photos."""
    return db.query(IntelPhoto).offset(skip).limit(limit).all()


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    """
    Return an aggregated intelligence dashboard feed.

    Includes expansion signals from the last 90 days, earnings insights,
    competitive activity, executive activity, and AI investment indicators.
    """
    cutoff = datetime.utcnow() - timedelta(days=90)

    expansion_signals_90d = (
        db.query(NewsSignal)
        .filter(NewsSignal.created_at >= cutoff, NewsSignal.tags.ilike("%expansion%"))
        .order_by(NewsSignal.created_at.desc())
        .limit(50)
        .all()
    )

    all_intel = db.query(CompanyIntelligence).filter(
        CompanyIntelligence.status == "completed"
    ).all()

    earnings_insights = [
        {
            "intelligence_id": i.id,
            "company_name": i.company_name,
            "recent_earnings_highlights": i.recent_earnings_highlights,
        }
        for i in all_intel
        if i.recent_earnings_highlights
    ]

    competitive_activity = [
        {
            "intelligence_id": i.id,
            "company_name": i.company_name,
            "competitor_mentions": i.competitor_mentions,
        }
        for i in all_intel
        if i.competitor_mentions
    ]

    from backend.models.intelligence import ExecutiveProfile

    executive_activity = (
        db.query(ExecutiveProfile)
        .order_by(ExecutiveProfile.created_at.desc())
        .limit(20)
        .all()
    )

    ai_investment_indicators = [
        {
            "intelligence_id": i.id,
            "company_name": i.company_name,
            "technology_growth_indicators": i.technology_growth_indicators,
        }
        for i in all_intel
        if i.technology_growth_indicators
    ]

    return {
        "expansion_signals_90d": [
            {
                "id": s.id,
                "headline": s.headline,
                "url": s.url,
                "source": s.source,
                "published_at": s.published_at,
                "tags": s.tags,
                "summary": s.summary,
                "sentiment": s.sentiment,
            }
            for s in expansion_signals_90d
        ],
        "earnings_insights": earnings_insights,
        "competitive_activity": competitive_activity,
        "executive_activity": [
            {
                "id": e.id,
                "name": e.name,
                "role": e.role,
                "intelligence_id": e.intelligence_id,
                "conversation_angles": e.conversation_angles,
            }
            for e in executive_activity
        ],
        "ai_investment_indicators": ai_investment_indicators,
    }

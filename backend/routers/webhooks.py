"""
Webhook endpoints for external integrations.
Handles incoming briefings, alerts, and data feeds.
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

from backend.core.config import settings

# ── Pydantic models matching the Grok JSON exactly ──
class Location(BaseModel):
    city: str
    state: Optional[str] = None
    country: str
    region: str

class CompanyRole(BaseModel):
    name: str
    role: str

class Project(BaseModel):
    project_key: str
    name: str
    location: Location
    companies: List[CompanyRole]
    project_type: str
    stage: str
    investment_usd_m: Optional[float] = None
    capacity_mw: Optional[float] = None
    energy_type: Optional[str] = None
    reported_date: str
    source: str
    description: str
    confidence: str

class NewsItem(BaseModel):
    headline: str
    source: str
    published_date: str
    summary: str
    strategic_insight: str
    companies: List[str]
    tags: List[str]

class InfrastructureOpportunity(BaseModel):
    type: str
    location: str
    companies: List[str]
    description: str

class BriefingPayload(BaseModel):
    type: str
    briefing_date: str
    overview: str
    market_signals: dict
    regional_hotspots: List[str]
    news_items: List[NewsItem]
    projects: List[Project]
    infrastructure_opportunities: List[InfrastructureOpportunity]

router = APIRouter(prefix="/api/v1")

# Simple secret protection (store in env)
async def verify_webhook(x_webhook_secret: str = Header(...)):
    """Verify webhook secret from X-Webhook-Secret header"""
    if x_webhook_secret != settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    return True

@router.post("/webhooks/dc-briefing")
async def receive_dc_briefing(
    payload: BriefingPayload,
    _: bool = Depends(verify_webhook)
):
    """
    Receive daily data center briefing from external source.
    
    Validates incoming JSON and prepares for database upsert.
    """
    # TODO: Call your upsert service here
    # Example:
    # from backend.services.briefing import upsert_briefing
    # result = await upsert_briefing(payload)
    
    print(f"✅ Received daily briefing for {payload.briefing_date}")
    print(f"   - {len(payload.news_items)} news items")
    print(f"   - {len(payload.projects)} projects")
    print(f"   - {len(payload.infrastructure_opportunities)} opportunities")
    
    return {
        "status": "accepted",
        "date": payload.briefing_date,
        "items_received": {
            "news": len(payload.news_items),
            "projects": len(payload.projects),
            "opportunities": len(payload.infrastructure_opportunities)
        }
    }


# ── Manual Briefing Ingestion Endpoints ──

class BriefingTextPayload(BaseModel):
    """Payload for manual briefing text ingestion"""
    briefing_text: str


@router.post("/briefing/ingest")
async def manual_briefing_ingest(payload: BriefingTextPayload):
    """
    Manually ingest a briefing from provided text.
    
    Bypasses Gmail fetch and directly processes the briefing text with Grok parser.
    Useful for testing or processing briefings from other sources.
    """
    from backend.services.briefing_ingestion import ingest_briefing_text
    
    result = await ingest_briefing_text(payload.briefing_text)
    
    return {
        "status": result["status"],
        "timestamp": result["timestamp"],
        "parse_success": result.get("parse_success", False),
        "counts": result.get("counts", {}),
        "touchpoints_generated": len(result.get("touchpoints", [])),
        "social_drafts_generated": len(result.get("social_drafts", [])),
        "error": result.get("error")
    }


@router.post("/briefing/ingest/test")
async def test_gmail_fetch():
    """
    Test endpoint to fetch the latest briefing from Gmail and process it.
    
    Triggers the same workflow as the scheduled job, but manually.
    Useful for testing Gmail integration before relying on the scheduler.
    """
    from backend.services.briefing_ingestion import run_daily_briefing_ingestion
    
    result = await run_daily_briefing_ingestion()
    
    return {
        "status": result["status"],
        "timestamp": result["timestamp"],
        "briefing_found": result.get("briefing_found", False),
        "parse_success": result.get("parse_success", False),
        "counts": result.get("counts", {}),
        "touchpoints": result.get("touchpoints", []),
        "social_drafts": result.get("social_drafts", []),
        "error": result.get("error")
    }

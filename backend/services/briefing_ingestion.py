"""Daily briefing ingestion orchestrator.

Fetches briefing email from Gmail, parses with Grok, and upserts all extracted data.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from backend.services.gmail_utils import fetch_latest_briefing_from_gmail
from backend.services.briefing_parser import GrokBriefingParser
from backend.services.notification_utils import send_fallback_notifications

logger = logging.getLogger(__name__)


async def run_daily_briefing_ingestion() -> Dict[str, Any]:
    """
    Main entry point for scheduled daily briefing ingestion.
    
    Workflow:
    1. Fetch latest briefing email from Gmail
    2. Parse with Grok to extract structured data
    3. Upsert accounts, opportunities, signals, intelligence entries
    4. Enrich with tender data
    5. Generate suggested touchpoints
    6. Generate social media drafts
    
    Returns:
        Summary dict with counts and status
    """
    logger.info(f"Starting daily briefing ingestion at {datetime.utcnow().isoformat()}")
    
    result = {
        "status": "failed",
        "timestamp": datetime.utcnow().isoformat(),
        "briefing_found": False,
        "parse_success": False,
        "counts": {},
        "touchpoints": [],
        "social_drafts": [],
        "error": None
    }
    
    try:
        # Step 1: Fetch briefing email
        briefing_text = await fetch_latest_briefing_from_gmail()
        
        if not briefing_text:
            logger.warning("No briefing email found – triggering fallback notifications")
            
            # Send fallback notifications (X DM draft + email draft)
            briefing_date = datetime.utcnow().strftime("%Y-%m-%d")
            try:
                notification_result = await send_fallback_notifications(briefing_date)
                result["fallback_notifications"] = notification_result
                logger.info(f"Fallback notifications: {len(notification_result.get('notifications_sent', []))} sent")
            except Exception as notif_error:
                logger.error(f"Fallback notification failed (non-critical): {notif_error}")
            
            result["error"] = "No new briefing email found - fallback notifications sent"
            return result
        
        result["briefing_found"] = True
        logger.info(f"Fetched briefing text ({len(briefing_text)} chars)")
        
        # Step 2: Parse with Grok
        parser = GrokBriefingParser()
        extracted = await parser.parse(briefing_text)
        
        if "error" in extracted:
            logger.error(f"Briefing parse failed: {extracted['error']}")
            result["error"] = extracted["error"]
            return result
        
        result["parse_success"] = True
        briefing_date = extracted.get("briefing_date", datetime.utcnow().strftime("%Y-%m-%d"))
        logger.info(f"Successfully parsed briefing for {briefing_date}")
        logger.info(f"  - {len(extracted.get('accounts', []))} accounts")
        logger.info(f"  - {len(extracted.get('opportunities', []))} opportunities")
        logger.info(f"  - {len(extracted.get('trigger_signals', []))} signals")
        logger.info(f"  - {len(extracted.get('intelligence_dataset', []))} intel entries")
        
        # Step 3: Upsert extracted data
        # Note: You'll need to create a briefing doc record first to get briefing_doc_id
        # For now, passing None – update this when you have the full workflow
        briefing_doc_id = None  # TODO: Create DailyBriefing record and get ID
        
        counts = await parser.upsert_extracted_data(extracted, briefing_doc_id)
        result["counts"] = counts
        logger.info(f"Upsert complete: {counts}")
        
        # Step 4: Enrich with tender data
        try:
            await parser.enrich_with_tenders(extracted, briefing_date, briefing_doc_id)
            logger.info("Tender enrichment complete")
        except Exception as e:
            logger.warning(f"Tender enrichment failed (non-critical): {e}")
        
        # Step 5: Generate touchpoint suggestions
        try:
            touchpoints = await parser.generate_suggested_touchpoints(extracted)
            result["touchpoints"] = touchpoints
            logger.info(f"Generated {len(touchpoints)} touchpoint suggestions")
        except Exception as e:
            logger.warning(f"Touchpoint generation failed (non-critical): {e}")
        
        # Step 6: Generate social media drafts
        try:
            social_drafts = await parser.generate_social_drafts_from_touchpoints(
                touchpoints=result.get("touchpoints", []),
                platform="x"
            )
            result["social_drafts"] = social_drafts
            logger.info(f"Generated {len(social_drafts)} social media drafts")
        except Exception as e:
            logger.warning(f"Social draft generation failed (non-critical): {e}")
        
        result["status"] = "success"
        logger.info("✅ Daily briefing ingestion completed successfully")
        return result
    
    except Exception as e:
        logger.error(f"Daily briefing ingestion failed: {str(e)}", exc_info=True)
        result["error"] = str(e)
        return result


async def ingest_briefing_text(briefing_text: str) -> Dict[str, Any]:
    """
    Manual ingestion endpoint (for testing or webhook use).
    
    Bypasses Gmail fetch and directly processes provided briefing text.
    
    Args:
        briefing_text: Raw briefing content to parse
    
    Returns:
        Summary dict with counts and status
    """
    logger.info(f"Manual briefing ingestion started ({len(briefing_text)} chars)")
    
    result = {
        "status": "failed",
        "timestamp": datetime.utcnow().isoformat(),
        "parse_success": False,
        "counts": {},
        "touchpoints": [],
        "social_drafts": [],
        "error": None
    }
    
    try:
        parser = GrokBriefingParser()
        extracted = await parser.parse(briefing_text)
        
        if "error" in extracted:
            logger.error(f"Parse failed: {extracted['error']}")
            result["error"] = extracted["error"]
            return result
        
        result["parse_success"] = True
        briefing_date = extracted.get("briefing_date", datetime.utcnow().strftime("%Y-%m-%d"))
        
        # Upsert data
        briefing_doc_id = None  # TODO: Create record
        counts = await parser.upsert_extracted_data(extracted, briefing_doc_id)
        result["counts"] = counts
        
        # Generate outputs
        touchpoints = await parser.generate_suggested_touchpoints(extracted)
        result["touchpoints"] = touchpoints
        
        social_drafts = await parser.generate_social_drafts_from_touchpoints(touchpoints)
        result["social_drafts"] = social_drafts
        
        # Enrich with tenders
        await parser.enrich_with_tenders(extracted, briefing_date, briefing_doc_id)
        
        result["status"] = "success"
        logger.info("✅ Manual briefing ingestion completed")
        return result
    
    except Exception as e:
        logger.error(f"Manual briefing ingestion failed: {str(e)}", exc_info=True)
        result["error"] = str(e)
        return result

"""Notification utilities for fallback alerts when briefing is missing."""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.core.config import settings

logger = logging.getLogger(__name__)


async def get_user_settings() -> Dict[str, Any]:
    """
    Fetch user notification settings and permissions.
    
    Returns default safe values if no database settings exist.
    """
    # TODO: Query UserSettings from database when implemented
    # For now, return safe defaults from config
    return {
        "permissions": {
            "social_draft": True,  # Safe - creates drafts only
            "gmail_draft": True,  # Safe - creates drafts only
            "full_autopilot": False,  # Safe - no auto-posting
        },
        "notification_email": settings.NOTIFICATION_EMAIL,
        "x_handle": settings.X_HANDLE or "TheMrFlen",
        "timezone": "Europe/London",
    }


async def social_create_draft(
    platform: str,
    post_text: str,
    reason: str,
    auto_post: bool = False
) -> Dict[str, Any]:
    """
    Create a social media draft (X/Twitter).
    
    Args:
        platform: "x" (Twitter/X)
        post_text: Content of the post/DM
        reason: Why this draft was created (for logging)
        auto_post: Whether to auto-post (requires full_autopilot permission)
    
    Returns:
        Dict with draft_id, status, and platform
    """
    logger.info(f"Creating {platform} draft: {reason}")
    logger.info(f"Draft content: {post_text[:100]}...")
    
    # TODO: Integrate with X API to create actual DM draft
    # For now, log the draft content
    draft_id = f"draft_{platform}_{datetime.utcnow().timestamp()}"
    
    draft = {
        "draft_id": draft_id,
        "platform": platform,
        "post_text": post_text,
        "reason": reason,
        "auto_post": auto_post,
        "status": "draft_created",
        "created_at": datetime.utcnow().isoformat(),
    }
    
    # In production, save to database and queue for review
    logger.info(f"✅ {platform.upper()} draft created: {draft_id}")
    
    return draft


async def gmail_draft_email(
    to: List[str],
    subject: str,
    body_plaintext: str,
    suggested_send_time_local: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a Gmail draft email using Gmail API.
    
    Args:
        to: List of recipient email addresses
        subject: Email subject
        body_plaintext: Plain text email body
        suggested_send_time_local: Suggested send time (ISO format)
    
    Returns:
        Dict with draft_id, status, and message_id
    """
    from email.mime.text import MIMEText
    import base64
    
    logger.info(f"Creating Gmail draft: {subject}")
    logger.info(f"Recipients: {', '.join(to)}")
    
    try:
        from backend.services.gmail_utils import get_gmail_service
        
        # Create MIME message
        message = MIMEText(body_plaintext)
        message['to'] = ', '.join(to)
        message['subject'] = subject
        
        # Encode message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Create draft via Gmail API
        service = await get_gmail_service()
        draft = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw}}
        ).execute()
        
        draft_id = draft['id']
        message_id = draft.get('message', {}).get('id', 'unknown')
        
        logger.info(f"✅ Gmail draft created: {draft_id}")
        
        return {
            "draft_id": draft_id,
            "message_id": message_id,
            "status": "draft_created",
            "recipients": to,
            "subject": subject,
            "suggested_send_time": suggested_send_time_local,
            "created_at": datetime.utcnow().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Failed to create Gmail draft: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "created_at": datetime.utcnow().isoformat(),
        }


async def send_fallback_notifications(briefing_date: str) -> Dict[str, Any]:
    """
    Send fallback notifications when daily briefing email is missing.
    
    Creates X DM draft and/or email draft based on user permissions.
    
    Args:
        briefing_date: Date of missing briefing (YYYY-MM-DD format)
    
    Returns:
        Dict with notification results
    """
    logger.warning(f"No briefing email found for {briefing_date} – triggering fallback notifications")
    
    result = {
        "briefing_date": briefing_date,
        "notifications_sent": [],
        "errors": [],
    }
    
    try:
        # Get user settings
        user_settings = await get_user_settings()
        permissions = user_settings.get("permissions", {})
        
        # Fallback 1: X DM draft
        if permissions.get("social_draft", False):
            try:
                x_handle = user_settings.get("x_handle", "TheMrFlen")
                post_text = (
                    f"@{x_handle} Daily DC briefing email missing today ({briefing_date}). "
                    f"No new intel pulled – check inbox or manual upload? #alignapp"
                )
                
                x_draft = await social_create_draft(
                    platform="x",
                    post_text=post_text,
                    reason=f"No briefing email detected for {briefing_date}",
                    auto_post=False  # Always draft first
                )
                
                result["notifications_sent"].append({
                    "type": "x_draft",
                    "status": "success",
                    "draft_id": x_draft.get("draft_id"),
                })
                logger.info(f"✅ Fallback X draft created for @{x_handle}")
            
            except Exception as e:
                logger.error(f"X draft creation failed: {str(e)}")
                result["errors"].append({
                    "type": "x_draft",
                    "error": str(e),
                })
        
        # Fallback 2: Email draft
        if permissions.get("gmail_draft", False):
            try:
                notification_email = user_settings.get("notification_email")
                if not notification_email:
                    logger.warning("No notification email configured – skipping email draft")
                else:
                    subject = f"aLiGN Daily Briefing Missing - {briefing_date}"
                    body = (
                        f"Ben,\n\n"
                        f"No new GLOBAL DATA CENTRE INTELLIGENCE BRIEFING email found today ({briefing_date}).\n\n"
                        f"The automated ingestion task ran but skipped processing.\n\n"
                        f"Possible actions:\n"
                        f"• Check inbox for the briefing email\n"
                        f"• Check spam/junk folders\n"
                        f"• Run manual upload if needed\n"
                        f"• Verify Gmail OAuth token is still valid\n\n"
                        f"GHOST 👻\n"
                    )
                    
                    email_draft = await gmail_draft_email(
                        to=[notification_email],
                        subject=subject,
                        body_plaintext=body,
                        suggested_send_time_local=datetime.utcnow().isoformat()
                    )
                    
                    if email_draft.get("status") == "draft_created":
                        result["notifications_sent"].append({
                            "type": "gmail_draft",
                            "status": "success",
                            "draft_id": email_draft.get("draft_id"),
                        })
                        logger.info(f"✅ Fallback email draft created to {notification_email}")
                    else:
                        result["errors"].append({
                            "type": "gmail_draft",
                            "error": email_draft.get("error", "Unknown error"),
                        })
            
            except Exception as e:
                logger.error(f"Email draft creation failed: {str(e)}")
                result["errors"].append({
                    "type": "gmail_draft",
                    "error": str(e),
                })
        
        # Log summary
        notifications_count = len(result["notifications_sent"])
        errors_count = len(result["errors"])
        logger.info(f"Fallback notifications complete: {notifications_count} sent, {errors_count} errors")
        
        return result
    
    except Exception as e:
        logger.error(f"Fallback notification system failed: {str(e)}", exc_info=True)
        result["errors"].append({
            "type": "system",
            "error": str(e),
        })
        return result

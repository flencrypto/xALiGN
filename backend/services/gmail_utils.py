"""Gmail integration for fetching daily briefing emails."""

import base64
import logging
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.core.config import settings

logger = logging.getLogger(__name__)


async def get_gmail_service():
    """
    Build Gmail API service using stored OAuth credentials.
    
    Requires GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN
    in environment variables.
    """
    if not all([settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET, settings.GOOGLE_REFRESH_TOKEN]):
        raise ValueError("Gmail OAuth credentials not configured. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN in .env")
    
    from google.auth.transport.requests import Request
    
    # Create credentials object with refresh token
    creds = Credentials(
        token=None,  # Will be auto-refreshed
        refresh_token=settings.GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/gmail.modify"]
    )
    
    # Refresh token if needed
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    return build("gmail", "v1", credentials=creds)


async def fetch_latest_briefing_from_gmail() -> Optional[str]:
    """
    Search Gmail for the most recent unread email with subject containing
    the briefing subject pattern and return its body text.
    
    Marks the email as read after successful fetch.
    
    Returns:
        Email body text, or None if no matching email found
    """
    try:
        service = await get_gmail_service()
        
        # Search query – unread emails with briefing subject from the last 7 days
        subject_pattern = settings.BRIEFING_EMAIL_SUBJECT
        query = f'subject:"{subject_pattern}" is:unread newer_than:7d'
        
        logger.info(f"Searching Gmail with query: {query}")
        
        results = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=1
        ).execute()
        
        messages = results.get("messages", [])
        if not messages:
            logger.info(f"No new briefing email found matching '{subject_pattern}'")
            return None
        
        msg_id = messages[0]["id"]
        logger.info(f"Found briefing email: {msg_id}")
        
        # Fetch full message
        msg = service.users().messages().get(
            userId="me",
            id=msg_id,
            format="full"
        ).execute()
        
        # Extract body text
        body_text = _extract_email_body(msg)
        
        if body_text:
            # Mark as read
            service.users().messages().modify(
                userId="me",
                id=msg_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            logger.info(f"Successfully fetched and marked briefing email as read: {msg_id}")
            return body_text
        else:
            logger.warning(f"No readable body found in briefing email {msg_id}")
            return None
    
    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching briefing: {str(e)}", exc_info=True)
        return None


def _extract_email_body(msg: dict) -> Optional[str]:
    """
    Extract body text from Gmail message payload.
    
    Handles both plain text and HTML multipart messages.
    Strips HTML tags from HTML content.
    """
    payload = msg.get("payload", {})
    
    # Check if message has parts (multipart)
    if "parts" in payload:
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")
            body_data = part.get("body", {}).get("data")
            
            if not body_data:
                continue
            
            # Decode base64
            decoded = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")
            
            # Prefer plain text
            if mime_type == "text/plain":
                return decoded
            
            # Fall back to HTML (strip tags)
            elif mime_type == "text/html":
                soup = BeautifulSoup(decoded, "html.parser")
                return soup.get_text(separator="\n", strip=True)
    
    # Single part message
    elif "body" in payload and "data" in payload["body"]:
        body_data = payload["body"]["data"]
        decoded = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")
        
        # Check if it's HTML
        if payload.get("mimeType") == "text/html":
            soup = BeautifulSoup(decoded, "html.parser")
            return soup.get_text(separator="\n", strip=True)
        
        return decoded
    
    return None

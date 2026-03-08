"""User settings and preferences model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON
from backend.database import Base


class UserSettings(Base):
    """User preferences and notification settings."""
    
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)  # Clerk user ID or email
    
    # Notification permissions
    social_draft = Column(Boolean, default=True, nullable=False)  # Allow X/Twitter draft creation
    gmail_draft = Column(Boolean, default=True, nullable=False)  # Allow Gmail draft creation
    full_autopilot = Column(Boolean, default=False, nullable=False)  # Allow auto-posting without approval
    
    # Contact details
    notification_email = Column(String, nullable=True)  # Email for notifications
    x_handle = Column(String, nullable=True)  # X/Twitter handle (e.g., "TheMrFlen")
    slack_webhook = Column(String, nullable=True)  # Slack webhook URL
    
    # Additional preferences
    timezone = Column(String, default="UTC", nullable=False)
    preferences = Column(JSON, default=dict, nullable=False)  # Extended preferences
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id}, social_draft={self.social_draft}, gmail_draft={self.gmail_draft})>"

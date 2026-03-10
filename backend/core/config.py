"""Application settings loaded from environment variables."""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # AI / LLM
    XAI_API_KEY: str = ""

    # CORS – comma-separated list of allowed origins.
    # Example: "https://app.example.com,https://preview.example.com"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    # Database
    DATABASE_URL: str = "sqlite:///./align.db"

    # Webhooks
    WEBHOOK_SECRET: str = "your-super-secret-key-here"  # Change in production!

    # Authentication  (none | clerk | auth0)
    AUTH_PROVIDER: str = "clerk"
    CLERK_ISSUER: str = ""
    CLERK_JWKS_URL: str = ""
    AUTH0_DOMAIN: str = ""
    AUTH0_AUDIENCE: str = ""

    # File storage  (local | s3)
    STORAGE_BACKEND: str = "local"
    UPLOAD_DIR: str = "./uploads"
    S3_BUCKET: str = ""
    S3_REGION: str = "eu-west-2"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # Scheduler – set to False when a dedicated worker pod manages scheduling
    ENABLE_SCHEDULER: bool = True
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REFRESH_TOKEN: str = ""  # Generate via OAuth flow
    BRIEFING_EMAIL_SUBJECT: str = "GLOBAL DATA CENTRE INTELLIGENCE BRIEFING"

    # Fallback Notifications (when briefing email is missing)
    NOTIFICATION_EMAIL: str = ""  # Email for fallback notifications
    X_HANDLE: str = "TheMrFlen"  # X/Twitter handle for DM notifications

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

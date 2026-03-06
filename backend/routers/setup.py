"""Setup / integration status endpoint.

GET /api/v1/setup/status
  Returns which integrations are configured (boolean flags only – never
  exposes key values or secrets).

Integrations reported:
  grok_ai    – xAI Grok (XAI_API_KEY)
  aws_s3     – Amazon S3 file storage (S3_BUCKET + AWS credentials)
  auth_clerk – Clerk SSO (CLERK_ISSUER or CLERK_JWKS_URL)
  auth_auth0 – Auth0 SSO (AUTH0_DOMAIN)
"""

import os
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/setup", tags=["Setup"])


def _check_grok_ai() -> dict[str, Any]:
    configured = bool(os.getenv("XAI_API_KEY", "").strip())
    return {
        "configured": configured,
        "missing_vars": [] if configured else ["XAI_API_KEY"],
        "required_for": [
            "company_research",
            "website_swoop",
            "blog_generation",
            "intelligence_collectors",
            "call_transcription",
            "agents",
        ],
        "optional": False,
        "setup_path": "/setup#grok_ai",
        "docs_url": "https://x.ai/api",
    }


def _check_aws_s3() -> dict[str, Any]:
    bucket = os.getenv("S3_BUCKET", "").strip()
    backend = os.getenv("STORAGE_BACKEND", "local").lower()
    # S3 is optional; only "broken" if STORAGE_BACKEND=s3 but bucket is missing
    s3_requested = backend == "s3"
    configured = (not s3_requested) or bool(bucket)
    missing = []
    if s3_requested and not bucket:
        missing.append("S3_BUCKET")
    return {
        "configured": configured,
        "active_backend": backend,
        "missing_vars": missing,
        "required_for": ["file_uploads_s3"],
        "optional": True,
        "note": "Local filesystem storage is used by default. S3 is only required when STORAGE_BACKEND=s3.",
        "setup_path": "/setup#aws_s3",
        "docs_url": "https://docs.aws.amazon.com/s3/",
    }


def _check_auth_clerk() -> dict[str, Any]:
    provider = os.getenv("AUTH_PROVIDER", "none").lower()
    issuer = os.getenv("CLERK_ISSUER", "").strip()
    jwks = os.getenv("CLERK_JWKS_URL", "").strip()
    configured = provider != "clerk" or bool(issuer or jwks)
    return {
        "configured": configured,
        "active_provider": provider,
        "missing_vars": (["CLERK_ISSUER"] if not (issuer or jwks) and provider == "clerk" else []),
        "required_for": ["authentication"],
        "optional": True,
        "note": "Only required when AUTH_PROVIDER=clerk. Authentication is disabled by default (AUTH_PROVIDER=none).",
        "setup_path": "/setup#auth_clerk",
        "docs_url": "https://clerk.com/docs",
    }


def _check_auth_auth0() -> dict[str, Any]:
    provider = os.getenv("AUTH_PROVIDER", "none").lower()
    domain = os.getenv("AUTH0_DOMAIN", "").strip()
    configured = provider != "auth0" or bool(domain)
    return {
        "configured": configured,
        "active_provider": provider,
        "missing_vars": (["AUTH0_DOMAIN"] if not domain and provider == "auth0" else []),
        "required_for": ["authentication"],
        "optional": True,
        "note": "Only required when AUTH_PROVIDER=auth0. Authentication is disabled by default (AUTH_PROVIDER=none).",
        "setup_path": "/setup#auth_auth0",
        "docs_url": "https://auth0.com/docs",
    }


@router.get("/status", summary="Integration configuration status (no secrets exposed)")
def get_setup_status() -> dict[str, Any]:
    """
    Returns whether each integration is configured.
    Only boolean flags and missing env var **names** are returned – never the actual values.
    Safe to call from the frontend.
    """
    integrations = {
        "grok_ai": _check_grok_ai(),
        "aws_s3": _check_aws_s3(),
        "auth_clerk": _check_auth_clerk(),
        "auth_auth0": _check_auth_auth0(),
    }

    all_required_configured = all(
        info["configured"]
        for info in integrations.values()
        if not info.get("optional", True)
    )

    return {
        "integrations": integrations,
        "all_required_configured": all_required_configured,
        "auth_provider": os.getenv("AUTH_PROVIDER", "none"),
        "storage_backend": os.getenv("STORAGE_BACKEND", "local"),
    }

"""Helpers for integration configuration checks and fail-closed API responses."""

import os

from fastapi import HTTPException, status


def get_missing_env_vars(required: list[str]) -> list[str]:
    """Return names of required env vars that are missing or blank."""
    return [name for name in required if not os.getenv(name, "").strip()]


def ensure_integration_configured(
    *,
    integration_id: str,
    integration_name: str,
    required_env_vars: list[str],
    setup_path: str = "/setup",
) -> None:
    """Raise an actionable 501 response when an integration is not configured."""
    missing = get_missing_env_vars(required_env_vars)
    if not missing:
        return

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": f"{integration_name} is not configured.",
            "missing": missing,
            "setupPath": setup_path,
            "integrationId": integration_id,
        },
    )

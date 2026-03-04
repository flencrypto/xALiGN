"""Authentication service – JWT verification for Clerk and Auth0.

Supports two modes (selected by environment variables):

  AUTH_PROVIDER=clerk
    • Validates JWTs against Clerk's JWKS endpoint (requires CLERK_JWKS_URL or
      derived from CLERK_ISSUER).
    • Header: Authorization: Bearer <session_token>

  AUTH_PROVIDER=auth0
    • Validates JWTs against Auth0's JWKS endpoint (requires AUTH0_DOMAIN).
    • Header: Authorization: Bearer <access_token>

  AUTH_PROVIDER=none (default / unset)
    • Auth is disabled; all endpoints are open.  Safe for local development.

Usage in routers:
    from backend.services.auth import get_current_user, UserClaims
    ...
    @router.get("/protected")
    def protected(user: UserClaims = Depends(get_current_user)):
        return {"user_id": user.sub}
"""

import logging
import os
from functools import lru_cache
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger("align.auth")

_bearer = HTTPBearer(auto_error=False)

_AUTH_PROVIDER = os.getenv("AUTH_PROVIDER", "none").lower()


# ── User claims dataclass ─────────────────────────────────────────────────────

class UserClaims:
    """Decoded JWT claims for the authenticated user."""

    def __init__(self, claims: dict[str, Any]):
        self._claims = claims
        self.sub: str = claims.get("sub", "")
        self.email: str = claims.get("email", "") or claims.get(
            "https://align.app/email", ""
        )
        self.roles: list[str] = claims.get("roles", []) or claims.get(
            "https://align.app/roles", []
        )

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def __repr__(self) -> str:
        return f"UserClaims(sub={self.sub!r}, email={self.email!r})"


# ── JWKS helpers ──────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_jwks_client(jwks_uri: str):
    """Return a cached PyJWKClient for the given JWKS URI."""
    try:
        from jose import jwt  # noqa: F401 – ensure library available
        import jwt as pyjwt
        return pyjwt.PyJWKClient(jwks_uri)
    except ImportError:
        raise RuntimeError(
            "python-jose and/or PyJWT are required for JWT verification. "
            "Run: pip install python-jose[cryptography] PyJWT"
        )


def _verify_jwt_clerk(token: str) -> dict[str, Any]:
    """Verify a Clerk session JWT and return decoded claims."""
    issuer = os.getenv("CLERK_ISSUER", "")
    jwks_url = os.getenv("CLERK_JWKS_URL", "") or (f"{issuer.rstrip('/')}/.well-known/jwks.json" if issuer else "")
    if not jwks_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CLERK_ISSUER or CLERK_JWKS_URL must be configured.",
        )
    try:
        import jwt as pyjwt
        jwks_client = _get_jwks_client(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        claims = pyjwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return claims
    except Exception as exc:
        logger.warning("Clerk JWT verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _verify_jwt_auth0(token: str) -> dict[str, Any]:
    """Verify an Auth0 access JWT and return decoded claims."""
    domain = os.getenv("AUTH0_DOMAIN", "")
    audience = os.getenv("AUTH0_AUDIENCE", "")
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AUTH0_DOMAIN must be configured.",
        )
    jwks_url = f"https://{domain}/.well-known/jwks.json"
    try:
        import jwt as pyjwt
        jwks_client = _get_jwks_client(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        decode_kwargs: dict[str, Any] = {
            "algorithms": ["RS256"],
            "issuer": f"https://{domain}/",
        }
        if audience:
            decode_kwargs["audience"] = audience
        else:
            decode_kwargs["options"] = {"verify_aud": False}
        claims = pyjwt.decode(token, signing_key.key, **decode_kwargs)
        return claims
    except Exception as exc:
        logger.warning("Auth0 JWT verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI dependency ────────────────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UserClaims | None:
    """
    FastAPI dependency that verifies the Bearer token and returns UserClaims.

    When AUTH_PROVIDER=none (default), returns None without checking the token,
    making all endpoints publicly accessible.  Set AUTH_PROVIDER=clerk or
    AUTH_PROVIDER=auth0 to enforce authentication.
    """
    if _AUTH_PROVIDER == "none":
        return None

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    if _AUTH_PROVIDER == "clerk":
        claims = _verify_jwt_clerk(token)
    elif _AUTH_PROVIDER == "auth0":
        claims = _verify_jwt_auth0(token)
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unknown AUTH_PROVIDER: {_AUTH_PROVIDER!r}. Use 'clerk', 'auth0', or 'none'.",
        )

    return UserClaims(claims)


def require_auth(
    user: UserClaims | None = Depends(get_current_user),
) -> UserClaims:
    """
    Stricter dependency – raises 401 if auth is disabled or token is missing.

    Use this on endpoints that must always be authenticated.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

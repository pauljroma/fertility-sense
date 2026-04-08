"""API key authentication dependency for FastAPI."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fertility_sense.config import FertilitySenseConfig

_bearer_scheme = HTTPBearer(auto_error=False)

_config: FertilitySenseConfig | None = None


def _get_config() -> FertilitySenseConfig:
    global _config
    if _config is None:
        _config = FertilitySenseConfig()
    return _config


def set_config(config: FertilitySenseConfig) -> None:
    """Override the module-level config (useful for testing)."""
    global _config
    _config = config


async def require_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    """FastAPI dependency that validates Bearer token against config.api_key.

    Bypasses authentication for the /health endpoint.
    Returns the validated API key string on success.
    """
    # Allow /health without auth
    if request.url.path == "/health":
        return ""

    config = _get_config()

    # If no API key is configured, auth is effectively disabled
    if not config.api_key:
        return ""

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "missing_token", "message": "Authorization header is required"},
        )

    if credentials.credentials != config.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token", "message": "Invalid API key"},
        )

    return credentials.credentials

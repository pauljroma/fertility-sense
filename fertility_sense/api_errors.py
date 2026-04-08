"""FastAPI exception handlers and error response models."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from fertility_sense.errors import FertilitySenseError

_STATUS_CODE_MAP: dict[str, int] = {
    "FEED_INGESTION_ERROR": 502,
    "GOVERNANCE_VIOLATION": 422,
    "AGENT_DISPATCH_ERROR": 502,
    "BUDGET_EXCEEDED": 429,
    "CONFIGURATION_ERROR": 500,
}


async def fertility_sense_error_handler(
    request: Request,
    exc: FertilitySenseError,
) -> JSONResponse:
    """Convert FertilitySenseError into a structured JSON response."""
    return JSONResponse(
        status_code=_status_code(exc.code),
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


def _status_code(code: str) -> int:
    return _STATUS_CODE_MAP.get(code, 500)

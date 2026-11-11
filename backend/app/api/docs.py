from typing import Any

from app.schemas.common import ErrorResponse, ValidationErrorResponse

_RESPONSE_DOCUMENTATION: dict[int, dict[str, Any]] = {
    400: {
        "model": ErrorResponse,
        "description": "The request is invalid or contains an unusable token.",
    },
    401: {
        "model": ErrorResponse,
        "description": (
            "Authentication credentials are missing, invalid, expired, or revoked."
        ),
    },
    403: {
        "model": ErrorResponse,
        "description": "The authenticated user is not allowed to perform this action.",
    },
    404: {
        "model": ErrorResponse,
        "description": "The requested resource was not found.",
    },
    409: {
        "model": ErrorResponse,
        "description": "The request conflicts with the current resource state.",
    },
    422: {
        "model": ValidationErrorResponse,
        "description": "The request contains invalid path, query, or body values.",
    },
    429: {
        "model": ErrorResponse,
        "description": "Too many requests; retry after the period in Retry-After.",
        "headers": {
            "Retry-After": {
                "description": "Number of seconds to wait before retrying.",
                "schema": {"type": "integer", "minimum": 0},
            }
        },
    },
    503: {
        "model": ErrorResponse,
        "description": "A required service is temporarily unavailable.",
    },
}


def documented_responses(*status_codes: int) -> dict[int, dict[str, Any]]:
    """Return reusable OpenAPI response metadata for documented error statuses."""

    return {
        status_code: dict(_RESPONSE_DOCUMENTATION[status_code])
        for status_code in status_codes
    }

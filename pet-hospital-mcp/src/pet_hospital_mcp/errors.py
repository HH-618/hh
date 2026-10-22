"""Structured error types and codes for Pet Hospital MCP."""

from __future__ import annotations

from typing import Any


ERROR_VALIDATION = "VALIDATION_ERROR"
ERROR_BACKEND_TIMEOUT = "BACKEND_TIMEOUT"
ERROR_BACKEND_UNAVAILABLE = "BACKEND_UNAVAILABLE"
ERROR_BACKEND_API = "BACKEND_API_ERROR"
ERROR_BACKEND_INVALID_RESPONSE = "BACKEND_INVALID_RESPONSE"
ERROR_INTERNAL = "INTERNAL_ERROR"


class McpToolError(Exception):
    """Base structured error for tool calls."""

    code: str = ERROR_INTERNAL
    message: str = "Internal error"
    details: dict[str, Any]

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
        code: str | None = None,
    ) -> None:
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class ValidationError(McpToolError):
    code = ERROR_VALIDATION
    message = "Invalid input parameters"


class BackendTimeoutError(McpToolError):
    code = ERROR_BACKEND_TIMEOUT
    message = "Backend request timed out"


class BackendUnavailableError(McpToolError):
    code = ERROR_BACKEND_UNAVAILABLE
    message = "Backend service is unavailable"


class BackendApiError(McpToolError):
    code = ERROR_BACKEND_API
    message = "Backend returned an error"


class BackendInvalidResponseError(McpToolError):
    code = ERROR_BACKEND_INVALID_RESPONSE
    message = "Backend returned an invalid response"

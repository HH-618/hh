"""HTTP client for the Go Pet Hospital REST API, with timeout and retry."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from .config import Settings
from .errors import (
    BackendApiError,
    BackendInvalidResponseError,
    BackendTimeoutError,
    BackendUnavailableError,
)

logger = logging.getLogger("pet_hospital_mcp.rest_client")


class PetHospitalRestClient:
    """Thin async httpx wrapper around the Go REST API with timeout + bounded retries."""

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.pet_hospital_base_url
        self._timeout = settings.backend_timeout_seconds
        self._max_retries = settings.backend_max_retries
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
            follow_redirects=False,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_pets(self, params: dict[str, Any]) -> dict[str, Any]:
        """Call GET /api/v1/pets and return the parsed `data` object.

        Raises:
            BackendTimeoutError: on timeout.
            BackendUnavailableError: on connection error.
            BackendApiError: on non-2xx HTTP status.
            BackendInvalidResponseError: on malformed JSON or unexpected envelope.
        """
        # Drop None values so we don't forward "?q=" etc.
        clean_params = {k: v for k, v in params.items() if v is not None}

        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = await self._client.get("/api/v1/pets", params=clean_params)
            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt >= self._max_retries:
                    raise BackendTimeoutError(
                        f"Request timed out after {self._timeout}s",
                        details={"attempts": attempt + 1},
                    ) from exc
                await asyncio.sleep(0.1 * (attempt + 1))
                continue
            except httpx.ConnectError as exc:
                last_exc = exc
                if attempt >= self._max_retries:
                    raise BackendUnavailableError(
                        "Could not connect to backend service",
                        details={"base_url": self._base_url},
                    ) from exc
                await asyncio.sleep(0.1 * (attempt + 1))
                continue
            except httpx.HTTPError as exc:
                last_exc = exc
                raise BackendUnavailableError(
                    f"HTTP error: {exc}", details={"attempt": attempt + 1}
                ) from exc

            # Non-2xx: do not retry (4xx won't fix themselves; 5xx we retry once).
            if resp.status_code >= 500 and attempt < self._max_retries:
                await asyncio.sleep(0.1 * (attempt + 1))
                continue

            if resp.status_code >= 400:
                detail_body: Any
                try:
                    detail_body = resp.json()
                except Exception:
                    detail_body = resp.text[:500]
                raise BackendApiError(
                    f"Backend returned HTTP {resp.status_code}",
                    details={"status_code": resp.status_code, "body": detail_body},
                )

            # Parse JSON envelope
            try:
                envelope = resp.json()
            except ValueError as exc:
                raise BackendInvalidResponseError(
                    "Backend returned non-JSON response",
                    details={"content_type": resp.headers.get("content-type"), "body_prefix": resp.text[:200]},
                ) from exc

            if not isinstance(envelope, dict) or "data" not in envelope:
                raise BackendInvalidResponseError(
                    "Backend response missing `data` field",
                    details={"keys": list(envelope.keys()) if isinstance(envelope, dict) else None},
                )

            data = envelope["data"]
            if not isinstance(data, dict):
                raise BackendInvalidResponseError(
                    "Backend `data` is not an object",
                    details={"data_type": type(data).__name__},
                )

            return data

        # Should not reach here, but type guard
        raise BackendUnavailableError(
            "Failed after retries", details={"last_error": str(last_exc)}
        )

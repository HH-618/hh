"""Tests for PetHospitalRestClient."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

from pet_hospital_mcp.config import Settings
from pet_hospital_mcp.errors import (
    BackendApiError,
    BackendInvalidResponseError,
    BackendTimeoutError,
    BackendUnavailableError,
)
from pet_hospital_mcp.rest_client import PetHospitalRestClient


def _make_settings(**overrides: Any) -> Settings:
    defaults = dict(
        mcp_host="127.0.0.1",
        mcp_port=9100,
        pet_hospital_base_url="http://backend.test",
        backend_timeout_seconds=1.0,
        backend_max_retries=1,
    )
    defaults.update(overrides)
    return Settings(**defaults)


def _ok_envelope(items: list[dict] | None = None, **extra: Any) -> dict:
    data: dict[str, Any] = {
        "items": items or [],
        "total": len(items or []),
        "page": 1,
        "pageSize": 10,
        "totalPages": 1,
        "totalCost": 0.0,
    }
    data.update(extra)
    return {"code": 200, "message": "ok", "data": data, "time": "2026-01-01T00:00:00+08:00"}


class TestGetPetsSuccess:
    @pytest.mark.asyncio
    async def test_forwards_all_query_params(self):
        seen_params: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen_params.update(dict(request.url.params))
            return httpx.Response(200, json=_ok_envelope(items=[{"id": "PET-1", "name": "A"}]))

        settings = _make_settings()
        transport = httpx.MockTransport(handler)
        client = PetHospitalRestClient(settings)
        client._client = httpx.AsyncClient(
            base_url=settings.pet_hospital_base_url,
            transport=transport,
            timeout=1.0,
        )

        await client.get_pets(
            {
                "q": "cat",
                "name": "Tom",
                "ownerName": "Alice",
                "ownerPhone": "13800000000",
                "species": "猫",
                "doctor": "Dr. Li",
                "disease": "cold",
                "status": "待就诊",
                "min": 100,
                "max": 500,
                "sortBy": "totalCost",
                "order": "desc",
                "page": 2,
                "pageSize": 20,
            }
        )

        assert seen_params["q"] == "cat"
        assert seen_params["name"] == "Tom"
        assert seen_params["ownerName"] == "Alice"
        assert seen_params["ownerPhone"] == "13800000000"
        assert seen_params["species"] == "猫"
        assert seen_params["doctor"] == "Dr. Li"
        assert seen_params["disease"] == "cold"
        assert seen_params["status"] == "待就诊"
        assert seen_params["min"] == "100"
        assert seen_params["max"] == "500"
        assert seen_params["sortBy"] == "totalCost"
        assert seen_params["order"] == "desc"
        assert seen_params["page"] == "2"
        assert seen_params["pageSize"] == "20"

    @pytest.mark.asyncio
    async def test_drops_none_values(self):
        seen_params: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen_params.update(dict(request.url.params))
            return httpx.Response(200, json=_ok_envelope())

        settings = _make_settings()
        transport = httpx.MockTransport(handler)
        client = PetHospitalRestClient(settings)
        client._client = httpx.AsyncClient(
            base_url=settings.pet_hospital_base_url,
            transport=transport,
            timeout=1.0,
        )

        await client.get_pets({"name": "Tom", "species": None, "page": 1})

        assert "name" in seen_params
        assert "species" not in seen_params
        assert "page" in seen_params

    @pytest.mark.asyncio
    async def test_returns_data_field(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json=_ok_envelope(
                    items=[{"id": "PET-1", "name": "A"}],
                    total=42,
                    totalCost=1234.5,
                ),
            )

        settings = _make_settings()
        transport = httpx.MockTransport(handler)
        client = PetHospitalRestClient(settings)
        client._client = httpx.AsyncClient(
            base_url=settings.pet_hospital_base_url,
            transport=transport,
            timeout=1.0,
        )

        data = await client.get_pets({})
        assert data["total"] == 42
        assert data["totalCost"] == 1234.5
        assert data["items"][0]["name"] == "A"


class TestGetPetsErrors:
    @pytest.mark.asyncio
    async def test_timeout_raises_backend_timeout(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("timed out")

        settings = _make_settings(backend_max_retries=0)
        transport = httpx.MockTransport(handler)
        client = PetHospitalRestClient(settings)
        client._client = httpx.AsyncClient(
            base_url=settings.pet_hospital_base_url,
            transport=transport,
            timeout=0.1,
        )

        with pytest.raises(BackendTimeoutError):
            await client.get_pets({})

    @pytest.mark.asyncio
    async def test_connect_error_raises_backend_unavailable(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        settings = _make_settings(backend_max_retries=0)
        transport = httpx.MockTransport(handler)
        client = PetHospitalRestClient(settings)
        client._client = httpx.AsyncClient(
            base_url=settings.pet_hospital_base_url,
            transport=transport,
            timeout=1.0,
        )

        with pytest.raises(BackendUnavailableError):
            await client.get_pets({})

    @pytest.mark.asyncio
    async def test_4xx_raises_backend_api_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"code": 404, "message": "not found"})

        settings = _make_settings(backend_max_retries=0)
        transport = httpx.MockTransport(handler)
        client = PetHospitalRestClient(settings)
        client._client = httpx.AsyncClient(
            base_url=settings.pet_hospital_base_url,
            transport=transport,
            timeout=1.0,
        )

        with pytest.raises(BackendApiError) as exc_info:
            await client.get_pets({})
        assert exc_info.value.details["status_code"] == 404

    @pytest.mark.asyncio
    async def test_5xx_retries_then_raises(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(500, json={"code": 500, "message": "boom"})

        settings = _make_settings(backend_max_retries=2)
        transport = httpx.MockTransport(handler)
        client = PetHospitalRestClient(settings)
        client._client = httpx.AsyncClient(
            base_url=settings.pet_hospital_base_url,
            transport=transport,
            timeout=1.0,
        )

        with pytest.raises(BackendApiError):
            await client.get_pets({})
        assert call_count == 3  # initial + 2 retries

    @pytest.mark.asyncio
    async def test_non_json_response_raises_invalid(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content="not json", headers={"content-type": "text/html"})

        settings = _make_settings(backend_max_retries=0)
        transport = httpx.MockTransport(handler)
        client = PetHospitalRestClient(settings)
        client._client = httpx.AsyncClient(
            base_url=settings.pet_hospital_base_url,
            transport=transport,
            timeout=1.0,
        )

        with pytest.raises(BackendInvalidResponseError):
            await client.get_pets({})

    @pytest.mark.asyncio
    async def test_missing_data_field_raises_invalid(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"code": 200, "message": "ok"})

        settings = _make_settings(backend_max_retries=0)
        transport = httpx.MockTransport(handler)
        client = PetHospitalRestClient(settings)
        client._client = httpx.AsyncClient(
            base_url=settings.pet_hospital_base_url,
            transport=transport,
            timeout=1.0,
        )

        with pytest.raises(BackendInvalidResponseError):
            await client.get_pets({})

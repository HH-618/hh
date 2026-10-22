"""Tests for the MCP server: tool registration, input validation, error shapes.

We test the MCPServer layer directly (list_tools / call_tool) rather than
spinning up the full Streamable HTTP ASGI stack, which requires a running
event-loop task group and is covered by the live-run smoke test.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from starlette.testclient import TestClient

from pet_hospital_mcp.config import Settings
from pet_hospital_mcp.server import build_server, build_starlette_app
from pet_hospital_mcp.rest_client import PetHospitalRestClient


def _settings(**overrides: Any) -> Settings:
    defaults = dict(
        mcp_host="127.0.0.1",
        mcp_port=9100,
        pet_hospital_base_url="http://backend.test",
        backend_timeout_seconds=1.0,
        backend_max_retries=0,
    )
    defaults.update(overrides)
    return Settings(**defaults)


@pytest.fixture
def rest_client() -> PetHospitalRestClient:
    return PetHospitalRestClient(_settings())


@pytest.fixture
def server(rest_client: PetHospitalRestClient):
    return build_server(_settings(), rest_client)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        app = build_starlette_app(_settings())
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service"] == "pet-hospital-mcp"
        assert "backend" in body


class TestToolRegistration:
    @pytest.mark.asyncio
    async def test_list_tools_returns_exactly_one(self, server):
        tools = await server.list_tools()
        assert len(tools) == 1
        assert tools[0].name == "list_pets"

    @pytest.mark.asyncio
    async def test_tool_input_schema_has_all_params(self, server):
        tools = await server.list_tools()
        schema = tools[0].input_schema
        props = schema["properties"]
        expected_keys = {
            "q", "name", "ownerName", "ownerPhone", "species", "doctor",
            "disease", "status", "min", "max", "sortBy", "order", "page", "pageSize",
        }
        assert expected_keys <= set(props.keys())

    @pytest.mark.asyncio
    async def test_tool_description_present(self, server):
        tools = await server.list_tools()
        assert tools[0].description
        assert "pet" in tools[0].description.lower() or "宠物" in tools[0].description


class TestToolCallValidation:
    """Tool-call validation errors must surface as is_error=True with our
    structured error envelope, not as raw Pydantic / SDK stack traces."""

    @pytest.mark.asyncio
    async def test_invalid_species_returns_validation_error(self, server):
        result = await server.call_tool("list_pets", {"species": "恐龙"})
        assert result.is_error is True
        sc = result.structured_content
        assert sc["error"]["code"] == "VALIDATION_ERROR"
        assert "errors" in sc["error"]["details"]

    @pytest.mark.asyncio
    async def test_min_greater_than_max_returns_error(self, server):
        result = await server.call_tool("list_pets", {"min": 5000, "max": 1000})
        assert result.is_error is True
        assert result.structured_content["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_pageSize_out_of_range_returns_error(self, server):
        result = await server.call_tool("list_pets", {"pageSize": 9999})
        assert result.is_error is True
        assert result.structured_content["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_invalid_sortBy_returns_error(self, server):
        result = await server.call_tool("list_pets", {"sortBy": "notAField"})
        assert result.is_error is True
        assert result.structured_content["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_invalid_order_returns_error(self, server):
        result = await server.call_tool("list_pets", {"order": "sideways"})
        assert result.is_error is True
        assert result.structured_content["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_page_zero_returns_error(self, server):
        result = await server.call_tool("list_pets", {"page": 0})
        assert result.is_error is True
        assert result.structured_content["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_negative_min_returns_error(self, server):
        result = await server.call_tool("list_pets", {"min": -5})
        assert result.is_error is True
        assert result.structured_content["error"]["code"] == "VALIDATION_ERROR"


class TestToolCallBackendErrors:
    """Backend URL points to http://backend.test which won't resolve; verify
    we wrap it into a structured backend error rather than leaking httpx."""

    @pytest.mark.asyncio
    async def test_backend_unreachable_returns_structured_error(self, server):
        result = await server.call_tool("list_pets", {"pageSize": 1})
        assert result.is_error is True
        sc = result.structured_content
        assert "error" in sc
        assert sc["error"]["code"] in (
            "BACKEND_UNAVAILABLE",
            "BACKEND_TIMEOUT",
            "BACKEND_API_ERROR",
            "INTERNAL_ERROR",
        )
        # Must not leak raw httpx exception text into the public message
        assert "httpx" not in sc["error"]["message"].lower()
        assert "Traceback" not in sc["error"]["message"]

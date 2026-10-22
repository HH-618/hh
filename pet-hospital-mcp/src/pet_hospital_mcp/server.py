"""MCPServer assembly for Pet Hospital (stateless Streamable HTTP)."""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp_types import CallToolResult, TextContent
from pydantic import ValidationError as PydanticValidationError
from starlette.responses import JSONResponse
from starlette.routing import Route

from .config import Settings
from .errors import McpToolError, ValidationError as McpValidationError
from .logging_config import configure_logging
from .rest_client import PetHospitalRestClient
from .tools.list_pets import ListPetsInput, list_pets

logger = logging.getLogger("pet_hospital_mcp.server")


def _make_error_result(exc: McpToolError) -> CallToolResult:
    """Build a CallToolResult carrying our unified structured error body."""
    body = exc.to_dict()
    text = json.dumps(body, ensure_ascii=False)
    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content=body,
        is_error=True,
    )


def _make_success_result(data: Any) -> CallToolResult:
    """Build a CallToolResult with JSON text + structured content on success."""
    text = json.dumps(data, ensure_ascii=False, default=str)
    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content=data,
        is_error=False,
    )


def build_server(settings: Settings, rest_client: PetHospitalRestClient) -> MCPServer:
    """Create the MCPServer instance with tools registered.

    The server itself is stateless: every tool call carries its full input,
    and no Mcp-Session-Id / SSE recovery is used.
    """
    server = MCPServer(
        name="pet-hospital",
        title="Pet Hospital MCP",
        description=(
            "MCP adapter for the Pet Hospital REST API. "
            "Exposes read-only pet archive query capabilities to AI agents."
        ),
        version="0.1.0",
    )

    # --- list_pets tool -----------------------------------------------------
    # The function signature lists all public params (Any-typed) so the SDK
    # generates a useful JSON Schema. Strict validation — including rejecting
    # unknown fields — happens inside via ListPetsInput, using the *original*
    # arguments pulled from the Context, not the SDK-parsed subset.

    async def _list_pets_tool(
        q: Any = None,
        name: Any = None,
        ownerName: Any = None,
        ownerPhone: Any = None,
        species: Any = None,
        doctor: Any = None,
        disease: Any = None,
        status: Any = None,
        min: Any = None,
        max: Any = None,
        sortBy: Any = None,
        order: Any = None,
        page: Any = None,
        pageSize: Any = None,
    ) -> CallToolResult:
        """Search and list pet records from the hospital.

        Use this tool when the user asks to browse, filter, search, sort or paginate
        pet archives — e.g. "show all dogs waiting for treatment", "find pets owned by
        张三", "top 10 highest spending cats", or "page 2 of chronic-follow-up cases".

        All filtering / sorting / pagination parameters are optional; omit the ones
        you don't need.

        Args:
            q: Full-text keyword search (AND across space-separated terms, e.g. "肠胃炎 犬").
            name: Filter by pet name (partial match, e.g. "旺财").
            ownerName: Filter by owner name (partial match, e.g. "张").
            ownerPhone: Filter by owner phone (exact match, e.g. "13800001111").
            species: Filter by species. Allowed values: 犬, 猫, 兔, 鸟, 仓鼠, 爬宠, 其他.
            doctor: Filter by attending doctor (e.g. "李医生").
            disease: Filter by disease / diagnosis (e.g. "肠胃炎").
            status: Filter by visit status. Allowed values: 待就诊, 就诊中, 住院中, 已康复, 慢性病随访.
            min: Minimum total cost in yuan (non-negative integer).
            max: Maximum total cost in yuan (non-negative integer); must be >= min.
            sortBy: Sort field. Allowed values: id, name, ownerName, species, doctor, disease, status, totalCost, visitCount, createdAt, updatedAt.
            order: Sort direction. Allowed values: "asc" (default), "desc".
            page: Page number, starts at 1 (default 1).
            pageSize: Items per page, 1..500 (default 20).

        Returns:
            On success: a page of pet items plus totals (total, page, pageSize,
            totalPages, totalCost). On failure: a structured error body with
            code / message / details.
        """
        # Build the argument dict from the named parameters. The SDK filters
        # out unknown fields before invoking the tool, so we only validate
        # the known set here; unknown fields are silently ignored upstream.
        raw_args: dict[str, Any] = {
            "q": q,
            "name": name,
            "ownerName": ownerName,
            "ownerPhone": ownerPhone,
            "species": species,
            "doctor": doctor,
            "disease": disease,
            "status": status,
            "min": min,
            "max": max,
            "sortBy": sortBy,
            "order": order,
            "page": page,
            "pageSize": pageSize,
        }
        clean_args = {k: v for k, v in raw_args.items() if v is not None}

        try:
            params = ListPetsInput.model_validate(clean_args)
        except PydanticValidationError as exc:
            err_details = {
                "errors": [
                    {
                        "field": ".".join(str(loc) for loc in e["loc"]),
                        "message": e["msg"],
                        "type": e["type"],
                    }
                    for e in exc.errors()
                ]
            }
            return _make_error_result(
                McpValidationError("Invalid input parameters", details=err_details)
            )

        try:
            output = await list_pets(params, rest_client)
            return _make_success_result(output.model_dump(mode="json"))
        except McpToolError as exc:
            return _make_error_result(exc)
        except Exception as exc:  # pragma: no cover - safety net
            from .errors import INTERNAL_ERROR

            return _make_error_result(
                McpToolError(
                    f"Unexpected internal error: {type(exc).__name__}",
                    details={"error": str(exc)},
                    code=INTERNAL_ERROR,
                )
            )

    server.add_tool(
        _list_pets_tool,
        name="list_pets",
        title="List Pets",
        description=(
            "List / search pet archives from the Pet Hospital backend. "
            "Supports keyword search, filters (species, doctor, status, disease, owner, "
            "cost range), sorting and pagination."
        ),
        structured_output=False,
    )

    return server


def build_starlette_app(settings: Settings) -> Any:
    """Build the Starlette app for stateless Streamable HTTP transport.

    Adds a custom `/health` route alongside the `/mcp` endpoint.
    """
    configure_logging()

    rest_client = PetHospitalRestClient(settings)
    server = build_server(settings, rest_client)

    app = server.streamable_http_app(
        stateless_http=True,
        streamable_http_path="/mcp",
        json_response=True,
    )

    # Inject /health route.
    async def health(_request: Any) -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "service": "pet-hospital-mcp",
                "backend": settings.pet_hospital_base_url,
            }
        )

    app.routes.insert(0, Route("/health", health, methods=["GET"]))

    app.state.rest_client = rest_client
    app.state.settings = settings

    return app

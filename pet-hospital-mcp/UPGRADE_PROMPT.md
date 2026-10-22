# UPGRADE_PROMPT — Phase 2 Prompt

## Goal

Add more MCP tools to the Pet Hospital MCP server, one per iteration, following the same patterns established in Phase 1.

## Phase 1 status (already shipped)

- Transport: stateless Streamable HTTP (`stateless_http=True`), MCP 2026-07-28.
- Framework: `MCPServer` from `mcp.server.mcpserver` (not FastMCP).
- Config: `Settings.from_env()` with `MCP_HOST`, `MCP_PORT`, `PET_HOSPITAL_BASE_URL`, timeout and retries.
- REST client: `PetHospitalRestClient` (httpx.AsyncClient, timeout + bounded retries, unified error mapping).
- Error envelope: `{"error": {"code", "message", "details"}}` — codes already defined in `errors.py`.
- Logging: JSON logs via `logging_config.py`, with recursive PII masking of `ownerPhone` / `ownerAddr` / `chipNo`.
- Tool pattern: each tool lives under `tools/`, has Pydantic input + output models, is registered in `server.py` via `server.add_tool(...)`, and returns a `CallToolResult` we build ourselves (success → structured data; failure → unified error envelope, `is_error=True`).

## How to add a new tool (checklist)

1. **Create `tools/<name>.py`**:
   - Define `XxxInput(BaseModel)` with `model_config = {"extra": "forbid"}`.
   - Use `Literal[...]` for enum fields that mirror the backend's allowed values.
   - Add `model_validator(mode="after")` for cross-field rules.
   - Define `XxxOutput(BaseModel)` matching the Go API `data` field.
   - Implement `async def xxx(params: XxxInput, rest_client: PetHospitalRestClient) -> XxxOutput`.
   - Wrap backend calls in try/except; let `McpToolError` subclasses propagate.
   - Log via `log_tool_call(...)` so duration / status / params are captured.

2. **Add a method on `PetHospitalRestClient`** (or reuse existing GET/POST helpers):
   - Map httpx exceptions to `BACKEND_TIMEOUT` / `BACKEND_UNAVAILABLE`.
   - Map non-2xx to `BACKEND_API_ERROR` with status code + body in details.
   - Map malformed JSON / missing envelope to `BACKEND_INVALID_RESPONSE`.

3. **Register the tool in `server.py`**:
   - Add a thin async wrapper that:
     - builds the raw dict from named `Any = None` parameters (so SDK generates a clean JSON Schema),
     - validates with `XxxInput.model_validate(clean_args)`,
     - on PydanticValidationError → `_make_error_result(McpValidationError(...))`,
     - on `McpToolError` → `_make_error_result(exc)`,
     - on success → `_make_success_result(output.model_dump(mode="json"))`.
   - Call `server.add_tool(wrapper, name="<snake_case_name>", title=..., description=..., structured_output=False)`.

4. **Tests**:
   - Unit test the Pydantic input model (valid + invalid cases).
   - Unit test the REST client method (success, 4xx, 5xx, timeout, bad JSON) using `httpx.MockTransport`.
   - Unit test tool registration (name present in `server.list_tools()`, schema has all params).
   - Unit test tool call validation errors return `isError=True` + correct error code.
   - Do **not** hit the real Go service in tests.

## Suggested Phase 2 tools (in priority order)

1. `get_pet` — `GET /api/v1/pets/{id}` — fetch a single pet with full records + charges.
2. `list_pets_by_owner` — `GET /api/v1/pets/by-owner` — find pets by owner name / phone.
3. `list_pets_by_doctor` — `GET /api/v1/pets/by-doctor` — find pets under a given doctor.
4. `get_pet_summary` — `GET /api/v1/pets/{id}/summary` — cost + visit aggregates for one pet.
5. `list_top_spenders` — `GET /api/v1/pets/top-spenders` — leaderboard by total cost.

## Hard rules for every phase

- Never modify the Go backend.
- Never introduce stateful sessions, `Mcp-Session-Id`, or SSE recovery.
- Never leak httpx / Pydantic / Python stack traces into tool results.
- Mask PII in logs (`ownerPhone`, `ownerAddr`, `chipNo` and their snake_case variants).
- All tools must be `snake_case`.
- Run `pytest -q` and keep it green.

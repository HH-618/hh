# Pet Hospital MCP Server

A stateless [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that exposes the Pet Hospital Go REST API to AI agents.

- **SDK**: `mcp==2.0.0` (official Python SDK 2.x)
- **Protocol**: MCP `2026-07-28`
- **Transport**: Stateless Streamable HTTP (no `initialize`, no `Mcp-Session-Id`, no SSE recovery)
- **Framework**: `MCPServer` (not FastMCP)

## Prerequisites

1. Python 3.11+
2. The Go Pet Hospital REST API must be running first.

   ```bash
   # From the pet-hospital-windows-amd64 directory:
   pethospital.exe
   # API listens on http://127.0.0.1:8080 by default
   ```

## Install & Run

```bash
cd pet-hospital-mcp
python -m pip install -e .

# Start with defaults (127.0.0.1:9100, backend at 127.0.0.1:8080)
python -m pet_hospital_mcp
```

### Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `MCP_HOST` | `127.0.0.1` | Host to bind |
| `MCP_PORT` | `9100` | Port to listen on |
| `PET_HOSPITAL_BASE_URL` | `http://127.0.0.1:8080` | Go REST API base URL |
| `BACKEND_TIMEOUT_SECONDS` | `10.0` | Per-request timeout to backend |
| `BACKEND_MAX_RETRIES` | `2` | Number of retries on 5xx / timeout |

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `POST` | `/mcp` | MCP Streamable HTTP endpoint (stateless) |

### Health check

```bash
curl http://127.0.0.1:9100/health
# {"status":"ok","service":"pet-hospital-mcp","backend":"http://127.0.0.1:8080"}
```

## Available Tools

### `list_pets`

Search and list pet archives from the hospital. Supports keyword search, filters, sorting, and pagination.

**Parameters** (all optional):

| Parameter | Type | Description |
| --- | --- | --- |
| `q` | string | Full-text keyword search (AND across space-separated terms) |
| `name` | string | Filter by pet name (partial match) |
| `ownerName` | string | Filter by owner name (partial match) |
| `ownerPhone` | string | Filter by owner phone (exact match) |
| `species` | string | One of: 犬, 猫, 兔, 鸟, 仓鼠, 爬宠, 其他 |
| `doctor` | string | Filter by attending doctor |
| `disease` | string | Filter by disease / diagnosis |
| `status` | string | One of: 待就诊, 就诊中, 住院中, 已康复, 慢性病随访 |
| `min` | int | Minimum total cost (non-negative) |
| `max` | int | Maximum total cost (non-negative, must be ≥ min) |
| `sortBy` | string | One of: id, name, ownerName, species, doctor, disease, status, totalCost, visitCount, createdAt, updatedAt |
| `order` | string | `asc` (default) or `desc` |
| `page` | int | Page number, starts at 1 (default 1) |
| `pageSize` | int | Items per page, 1..500 (default 20) |

**Returns**: A page of pet items plus `total`, `page`, `pageSize`, `totalPages`, and aggregate `totalCost`.

## Verify with MCP Inspector or SDK 2.x Client

Because the server is **stateless**, you do **not** need to send `initialize` first. A client can POST directly to `/mcp`.

### Example: list tools

```bash
curl -X POST http://127.0.0.1:9100/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

### Example: call `list_pets`

```bash
curl -X POST http://127.0.0.1:9100/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "list_pets",
      "arguments": {
        "species": "猫",
        "status": "待就诊",
        "pageSize": 5,
        "sortBy": "totalCost",
        "order": "desc"
      }
    }
  }'
```

### Expected behavior

- No `Mcp-Session-Id` header is returned (stateless).
- Every request is independent; no session state is stored.
- Errors return `isError: true` with a structured `structuredContent.error` envelope:
  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR | BACKEND_TIMEOUT | BACKEND_UNAVAILABLE | BACKEND_API_ERROR | BACKEND_INVALID_RESPONSE | INTERNAL_ERROR",
      "message": "human-readable message",
      "details": {}
    }
  }
  ```

## Running Tests

```bash
cd pet-hospital-mcp
pytest -q
```

Expected result: **42 passed** in ~2–3 seconds.

Tests use `httpx.MockTransport` and never hit the real Go backend.

## Project Structure

```text
pet-hospital-mcp/
├── pyproject.toml
├── README.md
├── UPGRADE_PROMPT.md
├── src/
│   └── pet_hospital_mcp/
│       ├── __init__.py
│       ├── __main__.py
│       ├── config.py
│       ├── server.py
│       ├── rest_client.py
│       ├── errors.py
│       ├── logging_config.py
│       └── tools/
│           ├── __init__.py
│           └── list_pets.py
└── tests/
    ├── test_list_pets.py
    ├── test_rest_client.py
    └── test_server.py
```

## Notes

- Teaching scenario: no auth, no CORS, no Origin checking — do not expose to the public internet.
- Sensitive fields (`ownerPhone`, `ownerAddr`, `chipNo`) are recursively masked in logs.
- Only the `list_pets` tool is implemented in this phase. Phase 2 tools are intentionally not included.

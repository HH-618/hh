"""Entry point: python -m pet_hospital_mcp"""

from __future__ import annotations

import uvicorn

from .config import Settings
from .server import build_starlette_app


def main() -> None:
    settings = Settings.from_env()
    app = build_starlette_app(settings)

    print(f"🐾 Pet Hospital MCP starting on http://{settings.mcp_host}:{settings.mcp_port}")
    print(f"   MCP endpoint:    http://{settings.mcp_host}:{settings.mcp_port}/mcp")
    print(f"   Health check:    http://{settings.mcp_host}:{settings.mcp_port}/health")
    print(f"   Backend:         {settings.pet_hospital_base_url}")
    print(f"   Transport:       stateless Streamable HTTP (MCP 2026-07-28)")

    uvicorn.run(
        app,
        host=settings.mcp_host,
        port=settings.mcp_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()

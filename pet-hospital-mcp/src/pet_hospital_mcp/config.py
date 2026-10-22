"""Configuration for Pet Hospital MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    mcp_host: str
    mcp_port: int
    pet_hospital_base_url: str
    backend_timeout_seconds: float
    backend_max_retries: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            mcp_host=os.getenv("MCP_HOST", "127.0.0.1"),
            mcp_port=int(os.getenv("MCP_PORT", "9100")),
            pet_hospital_base_url=os.getenv(
                "PET_HOSPITAL_BASE_URL", "http://127.0.0.1:8080"
            ).rstrip("/"),
            backend_timeout_seconds=float(os.getenv("BACKEND_TIMEOUT_SECONDS", "10.0")),
            backend_max_retries=int(os.getenv("BACKEND_MAX_RETRIES", "2")),
        )

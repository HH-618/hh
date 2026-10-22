"""JSON logging with recursive PII masking."""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Iterable

SENSITIVE_KEYS = {
    "ownerphone",
    "owneraddr",
    "chipno",
    "owner_phone",
    "owner_addr",
    "chip_no",
}

_MASK = "***MASKED***"


def _mask_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _mask_dict(k, v) for k, v in value.items()}
    if isinstance(value, list):
        return [_mask_value(v) for v in value]
    return value


def _mask_dict(key: str, value: Any) -> Any:
    key_lower = key.strip().lower().replace("-", "_")
    if key_lower in SENSITIVE_KEYS:
        return _MASK
    return _mask_value(value)


def mask_sensitive(data: Any) -> Any:
    """Recursively mask ownerPhone / ownerAddr / chipNo and snake_case variants."""
    return _mask_value(data)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(mask_sensitive(extra))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def log_tool_call(
    tool_name: str,
    params: dict[str, Any],
    status: str,
    duration_ms: float,
    extra: dict[str, Any] | None = None,
) -> None:
    logger = logging.getLogger("pet_hospital_mcp.tools")
    fields: dict[str, Any] = {
        "tool_name": tool_name,
        "params": params,
        "status": status,
        "duration_ms": round(duration_ms, 2),
    }
    if extra:
        fields.update(extra)
    logger.info("tool_call", extra={"extra_fields": fields})

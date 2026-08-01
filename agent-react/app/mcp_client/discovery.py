"""Discovery das tools remotas do mcp-server."""

from __future__ import annotations

from typing import Any

import httpx

from .config import HTTP_TIMEOUT, MCP_API_BASE_URL


def discover_tools() -> list[dict[str, Any]]:
    resp = httpx.get(f"{MCP_API_BASE_URL}/tools", timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()["tools"]


def schema_to_arg_types(schema: dict[str, Any]) -> dict[str, type]:
    props = (schema or {}).get("properties", {}) or {}
    mapping = {"string": str, "integer": int, "number": float, "boolean": bool}
    return {name: mapping.get(spec.get("type"), str) for name, spec in props.items()}

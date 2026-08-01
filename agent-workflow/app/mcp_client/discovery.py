"""Discovery filtrado das tools do mcp-server.

Permite filtrar por prefixo de nome — o workflow só usa `simular_*`,
`executar_*` e tools read-only relevantes.
"""

from __future__ import annotations

from typing import Any, Callable

import httpx

from .config import HTTP_TIMEOUT, MCP_API_BASE_URL


def discover_tools(filter_fn: Callable[[dict[str, Any]], bool] | None = None) -> list[dict[str, Any]]:
    resp = httpx.get(f"{MCP_API_BASE_URL}/tools", timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    tools = resp.json()["tools"]
    if filter_fn is not None:
        tools = [t for t in tools if filter_fn(t)]
    return tools


def schema_to_arg_types(schema: dict[str, Any]) -> dict[str, type]:
    props = (schema or {}).get("properties", {}) or {}
    mapping = {"string": str, "integer": int, "number": float, "boolean": bool}
    return {name: mapping.get(spec.get("type"), str) for name, spec in props.items()}

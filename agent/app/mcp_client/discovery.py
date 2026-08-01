"""Discovery das tools remotas expostas pela API HTTP do `mcp-server`.

Responsável por chamar `GET /tools` e devolver a lista de specs (nome,
descrição, JSON Schema de entrada).
"""

from __future__ import annotations

from typing import Any

import httpx

from .config import HTTP_TIMEOUT, MCP_API_BASE_URL


def discover_tools() -> list[dict[str, Any]]:
    """Retorna a lista de tools publicadas pela API remota."""
    resp = httpx.get(f"{MCP_API_BASE_URL}/tools", timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()["tools"]


def schema_to_arg_types(schema: dict[str, Any]) -> dict[str, type]:
    """Converte o JSON Schema retornado pela API em tipos aceitos pelo `@tool`."""
    props = (schema or {}).get("properties", {}) or {}
    mapping = {"string": str, "integer": int, "number": float, "boolean": bool}
    return {name: mapping.get(spec.get("type"), str) for name, spec in props.items()}

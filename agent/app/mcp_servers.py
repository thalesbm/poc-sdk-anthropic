"""Servidor MCP in-process cujas tools proxyam a API HTTP do `mcp-server`.

O agente não fala MCP diretamente com o `mcp-server/api.py` (que expõe REST,
não MCP). Em vez disso, no boot fazemos discovery em `GET /tools` e criamos
dinamicamente uma tool MCP local para cada tool remota; cada invocação vira
um `POST /tools/{name}/invoke`.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from claude_agent_sdk import create_sdk_mcp_server, tool

__all__ = ["ALLOWED_TOOLS", "SERVER_NAME", "build_assistant_server"]

SERVER_NAME = "banco"
MCP_API_BASE_URL = os.getenv("MCP_API_BASE_URL", "http://localhost:8000").rstrip("/")
_HTTP_TIMEOUT = float(os.getenv("MCP_API_TIMEOUT", "10"))


def _discover_tools() -> list[dict[str, Any]]:
    resp = httpx.get(f"{MCP_API_BASE_URL}/tools", timeout=_HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()["tools"]


def _make_proxy(tool_name: str):
    async def _handler(args: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
                resp = await client.post(
                    f"{MCP_API_BASE_URL}/tools/{tool_name}/invoke",
                    json={"arguments": args},
                )
        except httpx.HTTPError as exc:
            return {
                "content": [{"type": "text", "text": f"Falha de rede ao chamar '{tool_name}': {exc}"}],
                "is_error": True,
            }

        if resp.status_code >= 400:
            return {
                "content": [
                    {"type": "text", "text": f"Erro HTTP {resp.status_code}: {resp.text}"}
                ],
                "is_error": True,
            }

        payload = resp.json()
        return {"content": [{"type": "text", "text": str(payload.get("result", payload))}]}

    return _handler


def _schema_to_arg_types(schema: dict[str, Any]) -> dict[str, type]:
    """Converte o JSON Schema retornado pela API em tipos aceitos pelo `@tool`."""
    props = (schema or {}).get("properties", {}) or {}
    mapping = {"string": str, "integer": int, "number": float, "boolean": bool}
    return {name: mapping.get(spec.get("type"), str) for name, spec in props.items()}


_discovered = _discover_tools()

_MCP_TOOLS = [
    tool(
        spec["name"],
        spec.get("description", ""),
        _schema_to_arg_types(spec.get("input_schema", {})),
    )(_make_proxy(spec["name"]))
    for spec in _discovered
]

ALLOWED_TOOLS = [f"mcp__{SERVER_NAME}__{spec['name']}" for spec in _discovered]


def build_assistant_server():
    return create_sdk_mcp_server(
        name=SERVER_NAME,
        version="1.0.0",
        tools=_MCP_TOOLS,
    )

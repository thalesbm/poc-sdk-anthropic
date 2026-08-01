"""Monta o MCP server in-process com apenas as tools relevantes ao workflow."""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from .config import SERVER_NAME
from .discovery import discover_tools, schema_to_arg_types
from .invoker import invoke_tool

# O workflow só precisa de simular/executar PIX (ferramentas de escrita).
# Outras tools do banco (saldo, fatura, etc.) ficam de fora deste agente.
_ALLOWED_PREFIXES = ("simular_transferencia_", "executar_transferencia_", "buscar_saldo")


def _keep(t: dict[str, Any]) -> bool:
    return any(t["name"].startswith(p) for p in _ALLOWED_PREFIXES)


def _make_proxy(tool_name: str):
    async def _handler(args: dict[str, Any]) -> dict[str, Any]:
        return await invoke_tool(tool_name, args)

    return _handler


DISCOVERED_TOOLS: list[dict[str, Any]] = discover_tools(filter_fn=_keep)

_MCP_TOOLS = [
    tool(
        spec["name"],
        spec.get("description", ""),
        schema_to_arg_types(spec.get("input_schema", {})),
    )(_make_proxy(spec["name"]))
    for spec in DISCOVERED_TOOLS
]

ALLOWED_TOOLS = [f"mcp__{SERVER_NAME}__{spec['name']}" for spec in DISCOVERED_TOOLS]

SENSITIVE_TOOL_NAMES = {spec["name"] for spec in DISCOVERED_TOOLS if spec["name"].startswith("executar_")}


def build_assistant_server():
    return create_sdk_mcp_server(
        name=SERVER_NAME,
        version="1.0.0",
        tools=_MCP_TOOLS,
    )

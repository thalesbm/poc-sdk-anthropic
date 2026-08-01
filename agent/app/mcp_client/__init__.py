"""Camada cliente MCP do agente: discovery + invocação HTTP + build do server.

Nomeada `mcp_client` (e não `mcp`) para não colidir com o pacote `mcp` do
PyPI, usado internamente pelo `claude_agent_sdk`.
"""

from __future__ import annotations

from .config import SERVER_NAME
from .server import ALLOWED_TOOLS, DISCOVERED_TOOLS, build_assistant_server

__all__ = [
    "ALLOWED_TOOLS",
    "DISCOVERED_TOOLS",
    "SERVER_NAME",
    "build_assistant_server",
]

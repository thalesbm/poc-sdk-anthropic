"""Monta o servidor MCP in-process com todas as ferramentas do assistente."""

from __future__ import annotations

from claude_agent_sdk import create_sdk_mcp_server

from tools.add_note import add_note
from tools.calculator import calculator
from tools.list_notes import list_notes

__all__ = ["ALLOWED_TOOLS", "build_assistant_server"]


def build_assistant_server():
    return create_sdk_mcp_server(
        name="assistant-tools",
        version="1.0.0",
        tools=[calculator, add_note, list_notes],
    )


ALLOWED_TOOLS = [
    "mcp__assistant__calculator",
    "mcp__assistant__add_note",
    "mcp__assistant__list_notes",
]

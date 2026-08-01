"""Ferramenta `list_notes`: lista todas as notas salvas."""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import tool

from _state import NOTES


@tool(
    "list_notes",
    "Lista todas as notas atualmente salvas no bloco de notas.",
    {},
)
async def list_notes(_args: dict[str, Any]) -> dict[str, Any]:
    if not NOTES:
        return {"content": [{"type": "text", "text": "Você ainda não tem notas."}]}
    formatted = "\n".join(f"{i}. {n}" for i, n in enumerate(NOTES, start=1))
    return {"content": [{"type": "text", "text": formatted}]}

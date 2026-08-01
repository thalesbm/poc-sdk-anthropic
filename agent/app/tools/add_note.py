"""Ferramenta `add_note`: adiciona uma nota ao bloco compartilhado."""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import tool

from _state import NOTES


@tool(
    "add_note",
    "Adiciona uma nota curta ao bloco de notas do usuário (armazenado em memória).",
    {"note": str},
)
async def add_note(args: dict[str, Any]) -> dict[str, Any]:
    note = args["note"].strip()
    if not note:
        return {
            "content": [{"type": "text", "text": "Nota vazia, nada foi salvo."}],
            "is_error": True,
        }
    NOTES.append(note)
    return {
        "content": [
            {"type": "text", "text": f"Nota #{len(NOTES)} salva: {note!r}"}
        ]
    }

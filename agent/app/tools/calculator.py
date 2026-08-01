"""Ferramenta `calculator`: avalia expressões aritméticas simples."""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import tool

_ALLOWED_CHARS = set("0123456789+-*/(). ")


@tool(
    "calculator",
    "Avalia uma expressão aritmética simples (+, -, *, /, **, parênteses).",
    {"expression": str},
)
async def calculator(args: dict[str, Any]) -> dict[str, Any]:
    expression = args["expression"]

    if not set(expression).issubset(_ALLOWED_CHARS):
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Expressão inválida: apenas dígitos, espaços, parênteses "
                        "e os operadores + - * / ** são permitidos."
                    ),
                }
            ],
            "is_error": True,
        }

    try:
        result = eval(expression, {"__builtins__": {}}, {})
    except Exception as exc:  # noqa: BLE001 - queremos reportar qualquer erro ao LLM
        return {
            "content": [{"type": "text", "text": f"Erro ao calcular: {exc}"}],
            "is_error": True,
        }

    return {"content": [{"type": "text", "text": f"{expression} = {result}"}]}

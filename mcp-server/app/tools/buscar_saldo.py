"""Tool `buscar_saldo`: retorna o saldo atual mockado de uma conta."""

from __future__ import annotations

from datetime import date
from typing import Any

from ._spec import ToolSpec


def buscar_saldo(conta: str = "00012345-6") -> dict[str, Any]:
    return {
        "conta": conta,
        "moeda": "BRL",
        "saldo_disponivel": 5234.87,
        "saldo_bloqueado": 120.00,
        "atualizado_em": date.today().isoformat(),
    }


SPEC = ToolSpec(
    name="buscar_saldo",
    description="Retorna o saldo atual mockado de uma conta.",
    handler=buscar_saldo,
    input_schema={
        "type": "object",
        "properties": {
            "conta": {
                "type": "string",
                "description": "Identificador da conta (opcional).",
                "default": "00012345-6",
            }
        },
        "required": [],
    },
)

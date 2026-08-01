"""Tool `buscar_total_investimentos`: retorna o total investido mockado."""

from __future__ import annotations

from datetime import date
from typing import Any

from ._spec import ToolSpec


def buscar_total_investimentos(cliente_id: str = "cli-0001") -> dict[str, Any]:
    return {
        "cliente_id": cliente_id,
        "moeda": "BRL",
        "total": 87450.35,
        "distribuicao": {
            "renda_fixa": 52300.10,
            "renda_variavel": 21050.25,
            "fundos": 9100.00,
            "cripto": 5000.00,
        },
        "atualizado_em": date.today().isoformat(),
    }


SPEC = ToolSpec(
    name="buscar_total_investimentos",
    description="Retorna o total de investimentos mockado do cliente.",
    handler=buscar_total_investimentos,
    input_schema={
        "type": "object",
        "properties": {
            "cliente_id": {
                "type": "string",
                "description": "Identificador do cliente (opcional).",
                "default": "cli-0001",
            }
        },
        "required": [],
    },
)

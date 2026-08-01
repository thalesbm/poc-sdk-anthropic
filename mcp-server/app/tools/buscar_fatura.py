"""Tool `buscar_fatura`: retorna a fatura atual mockada do cartão."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from ._spec import ToolSpec


def buscar_fatura(cartao_final: str = "1234") -> dict[str, Any]:
    vencimento = date.today() + timedelta(days=10)
    return {
        "cartao_final": cartao_final,
        "moeda": "BRL",
        "valor_total": 1875.42,
        "valor_minimo": 375.08,
        "data_vencimento": vencimento.isoformat(),
        "status": "aberta",
    }


SPEC = ToolSpec(
    name="buscar_fatura",
    description="Retorna o valor da fatura atual mockada do cartão de crédito.",
    handler=buscar_fatura,
    input_schema={
        "type": "object",
        "properties": {
            "cartao_final": {
                "type": "string",
                "description": "Últimos 4 dígitos do cartão (opcional).",
                "default": "1234",
            }
        },
        "required": [],
    },
)

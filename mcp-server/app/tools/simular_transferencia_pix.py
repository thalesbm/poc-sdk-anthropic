"""Tool `simular_transferencia_pix`: preview de uma transferência (não executa)."""

from __future__ import annotations

from datetime import date
from typing import Any

from ._spec import ToolSpec


def simular_transferencia_pix(chave_destino: str, valor: float) -> dict[str, Any]:
    return {
        "chave_destino": chave_destino,
        "titular_destino": "MARIA DA SILVA",
        "banco_destino": "Banco Fake S.A.",
        "valor": valor,
        "moeda": "BRL",
        "tarifa": 0.0,
        "previsao_liquidacao": date.today().isoformat(),
        "status": "simulado",
    }


SPEC = ToolSpec(
    name="simular_transferencia_pix",
    description=(
        "Simula uma transferência PIX (SEM executar). Retorna o titular do "
        "destinatário, banco, tarifa e previsão de liquidação. Use SEMPRE antes "
        "de executar_transferencia_pix para o cliente confirmar."
    ),
    handler=simular_transferencia_pix,
    input_schema={
        "type": "object",
        "properties": {
            "chave_destino": {"type": "string", "description": "Chave PIX de destino."},
            "valor": {"type": "number", "description": "Valor em reais."},
        },
        "required": ["chave_destino", "valor"],
    },
)

"""Tool `executar_transferencia_pix`: executa uma transferência PIX (mockada)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from ._spec import ToolSpec


def executar_transferencia_pix(chave_destino: str, valor: float) -> dict[str, Any]:
    return {
        "id_transacao": str(uuid4()),
        "chave_destino": chave_destino,
        "valor": valor,
        "moeda": "BRL",
        "status": "confirmada",
        "liquidada_em": datetime.now(timezone.utc).isoformat(),
        "comprovante_url": f"https://banco-mock.example.com/comprovantes/{uuid4()}.pdf",
    }


SPEC = ToolSpec(
    name="executar_transferencia_pix",
    description=(
        "EXECUTA uma transferência PIX de fato (movimenta dinheiro). NUNCA chame "
        "sem antes ter simulado com simular_transferencia_pix E ter a confirmação "
        "explícita do cliente na conversa."
    ),
    handler=executar_transferencia_pix,
    input_schema={
        "type": "object",
        "properties": {
            "chave_destino": {"type": "string", "description": "Chave PIX de destino."},
            "valor": {"type": "number", "description": "Valor em reais."},
        },
        "required": ["chave_destino", "valor"],
    },
)

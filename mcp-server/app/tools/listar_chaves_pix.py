"""Tool `listar_chaves_pix`: lista as chaves PIX mockadas do cliente."""

from __future__ import annotations

from datetime import date
from typing import Any

from ._spec import ToolSpec


_CHAVES_MOCK: list[dict[str, Any]] = [
    {
        "tipo": "cpf",
        "chave": "123.456.789-00",
        "banco": "Banco Mock",
        "agencia": "0001",
        "conta": "00012345-6",
        "criada_em": "2023-04-10",
    },
    {
        "tipo": "email",
        "chave": "cliente@exemplo.com",
        "banco": "Banco Mock",
        "agencia": "0001",
        "conta": "00012345-6",
        "criada_em": "2023-06-22",
    },
    {
        "tipo": "celular",
        "chave": "+55 11 99999-0000",
        "banco": "Banco Mock",
        "agencia": "0001",
        "conta": "00012345-6",
        "criada_em": "2024-01-15",
    },
    {
        "tipo": "aleatoria",
        "chave": "3f9c2b8a-1e4d-4a77-9c1b-8a5f2c1e9b77",
        "banco": "Banco Mock",
        "agencia": "0001",
        "conta": "00012345-6",
        "criada_em": "2024-09-03",
    },
]


def listar_chaves_pix(
    cliente_id: str = "cli-0001",
    tipo: str | None = None,
) -> dict[str, Any]:
    """Lista as chaves PIX mockadas do cliente, opcionalmente filtrando por tipo."""
    chaves = _CHAVES_MOCK
    if tipo:
        chaves = [c for c in chaves if c["tipo"].lower() == tipo.lower()]

    return {
        "cliente_id": cliente_id,
        "total": len(chaves),
        "chaves": chaves,
        "consultado_em": date.today().isoformat(),
    }


SPEC = ToolSpec(
    name="listar_chaves_pix",
    description=(
        "Lista as chaves PIX mockadas do cliente. Aceita filtro opcional por "
        "tipo (cpf, email, celular, aleatoria)."
    ),
    handler=listar_chaves_pix,
    input_schema={
        "type": "object",
        "properties": {
            "cliente_id": {
                "type": "string",
                "description": "Identificador do cliente (opcional).",
                "default": "cli-0001",
            },
            "tipo": {
                "type": "string",
                "description": "Filtrar por tipo de chave.",
                "enum": ["cpf", "email", "celular", "aleatoria"],
            },
        },
        "required": [],
    },
)

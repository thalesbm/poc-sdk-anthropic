"""Servidor MCP com ferramentas mockadas de dados bancários.

Executa via stdio usando o Python SDK oficial de MCP (`mcp`).

Uso:
    python server.py
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("banco-mock")


@mcp.tool()
def buscar_saldo(conta: str = "00012345-6") -> dict[str, Any]:
    """Retorna o saldo atual mockado de uma conta.

    Args:
        conta: Identificador da conta (opcional, usado apenas para exibição).
    """
    return {
        "conta": conta,
        "moeda": "BRL",
        "saldo_disponivel": 5234.87,
        "saldo_bloqueado": 120.00,
        "atualizado_em": date.today().isoformat(),
    }


@mcp.tool()
def buscar_fatura(cartao_final: str = "1234") -> dict[str, Any]:
    """Retorna o valor da fatura atual mockada do cartão de crédito.

    Args:
        cartao_final: Últimos 4 dígitos do cartão (opcional, apenas exibição).
    """
    hoje = date.today()
    vencimento = hoje + timedelta(days=10)
    return {
        "cartao_final": cartao_final,
        "moeda": "BRL",
        "valor_total": 1875.42,
        "valor_minimo": 375.08,
        "data_vencimento": vencimento.isoformat(),
        "status": "aberta",
    }


@mcp.tool()
def buscar_total_investimentos(cliente_id: str = "cli-0001") -> dict[str, Any]:
    """Retorna o total de investimentos mockado do cliente.

    Args:
        cliente_id: Identificador do cliente (opcional, apenas exibição).
    """
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


if __name__ == "__main__":
    mcp.run()

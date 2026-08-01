"""Tool `buscar_documentos_faq`: retriever mockado sobre uma base de FAQ.

POC de RAG: sem embeddings de verdade, faz matching por palavras-chave e
devolve trechos "cited" com id, título e trecho.
"""

from __future__ import annotations

from typing import Any

from ._spec import ToolSpec


_KB: list[dict[str, Any]] = [
    {
        "id": "faq-001",
        "titulo": "Limite diário do PIX",
        "trecho": (
            "O limite diário padrão para transferências PIX é de R$ 20.000 durante "
            "o dia (06h às 20h) e R$ 1.000 no período noturno. O cliente pode "
            "solicitar alteração pelo app na seção Segurança > Limites."
        ),
        "categoria": "pix",
    },
    {
        "id": "faq-002",
        "titulo": "Como bloquear o cartão",
        "trecho": (
            "Para bloquear o cartão, acesse Cartões > Meus Cartões > Bloquear no app. "
            "O bloqueio é imediato e reversível. Em caso de perda ou roubo, use "
            "'Bloqueio definitivo' para gerar uma nova via automaticamente."
        ),
        "categoria": "cartao",
    },
    {
        "id": "faq-003",
        "titulo": "Segunda via da fatura",
        "trecho": (
            "A segunda via da fatura fica disponível em Cartão > Faturas > Baixar PDF. "
            "Faturas dos últimos 24 meses ficam acessíveis. Para períodos anteriores "
            "abra um chamado no atendimento."
        ),
        "categoria": "cartao",
    },
    {
        "id": "faq-004",
        "titulo": "Rendimento da conta",
        "trecho": (
            "O saldo em conta rende automaticamente 100% do CDI a partir do primeiro "
            "dia útil após o depósito. Não há valor mínimo. O rendimento é creditado "
            "todos os dias úteis e reflete no extrato."
        ),
        "categoria": "conta",
    },
    {
        "id": "faq-005",
        "titulo": "Tarifa do PIX",
        "trecho": (
            "Transferências PIX para pessoas físicas são gratuitas. Para pessoas "
            "jurídicas há tarifa de R$ 0,50 por transação. Recebimentos são sempre "
            "gratuitos."
        ),
        "categoria": "pix",
    },
    {
        "id": "faq-006",
        "titulo": "Investimentos disponíveis",
        "trecho": (
            "O app oferece renda fixa (CDB, LCI, LCA, Tesouro Direto), fundos de "
            "investimento e cripto. Renda variável (ações e ETFs) exige conta "
            "adicional em corretora parceira, aberta em 2 cliques."
        ),
        "categoria": "investimentos",
    },
]


def _score(doc: dict[str, Any], query_terms: set[str]) -> int:
    text = f"{doc['titulo']} {doc['trecho']} {doc['categoria']}".lower()
    return sum(1 for t in query_terms if t in text)


def buscar_documentos_faq(query: str, top_k: int = 3) -> dict[str, Any]:
    """Busca semântica MOCKADA (matching por palavras-chave) na base de FAQ."""
    terms = {t.lower() for t in query.split() if len(t) >= 3}
    scored = [(d, _score(d, terms)) for d in _KB]
    scored.sort(key=lambda x: x[1], reverse=True)
    hits = [d for d, s in scored[:top_k] if s > 0]
    if not hits:
        hits = _KB[:top_k]
    return {
        "query": query,
        "total_encontrados": len(hits),
        "resultados": hits,
    }


SPEC = ToolSpec(
    name="buscar_documentos_faq",
    description=(
        "Retriever da base de FAQ do banco. Devolve os trechos mais relevantes "
        "com id, título e texto. USE quando o cliente perguntar sobre políticas, "
        "limites, tarifas, procedimentos, produtos, etc."
    ),
    handler=buscar_documentos_faq,
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Pergunta ou termos de busca."},
            "top_k": {"type": "integer", "description": "Nº de resultados (default 3).", "default": 3},
        },
        "required": ["query"],
    },
)

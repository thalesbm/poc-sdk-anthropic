"""AgentCard estático do especialista ReAct."""

from __future__ import annotations

import os

from a2a_common.models import AgentCard, AgentCapabilities, AgentSkill

BASE_URL = os.getenv("AGENT_REACT_URL", "http://localhost:8100")

CARD = AgentCard(
    name="agent-react-banco",
    description=(
        "Especialista ReAct para consultas bancárias mockadas (saldo, fatura, "
        "investimentos, chaves PIX). Decide dinamicamente quais tools chamar."
    ),
    url=BASE_URL,
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=False, push_notifications=False),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    skills=[
        AgentSkill(
            id="banking-queries",
            name="Consultas bancárias mockadas",
            description=(
                "Responde perguntas sobre saldo, fatura do cartão, "
                "total de investimentos e chaves PIX do cliente."
            ),
            tags=["banking", "read-only", "mocked"],
            examples=[
                "qual meu saldo?",
                "quanto tenho de fatura no cartão?",
                "liste minhas chaves pix do tipo email",
                "quanto eu tenho investido?",
            ],
        ),
    ],
)

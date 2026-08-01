"""AgentCard estático do especialista Workflow."""

from __future__ import annotations

import os

from a2a_common.models import AgentCard, AgentCapabilities, AgentSkill

BASE_URL = os.getenv("AGENT_WORKFLOW_URL", "http://localhost:8200")

CARD = AgentCard(
    name="agent-workflow-pix",
    description=(
        "Especialista em fluxos com confirmação humana (HITL) para operações "
        "sensíveis. Hoje suporta transferências PIX: simula, apresenta preview, "
        "aguarda confirmação explícita do cliente e só então executa."
    ),
    url=BASE_URL,
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=False, push_notifications=False),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    skills=[
        AgentSkill(
            id="pix-transfer",
            name="Transferência PIX com confirmação",
            description=(
                "Executa transferências PIX em duas etapas: (1) simula e mostra "
                "preview com destinatário/tarifa; (2) após 'sim/confirmo' do "
                "cliente, executa e devolve comprovante."
            ),
            tags=["banking", "pix", "hitl", "write"],
            examples=[
                "transferir 100 reais para cliente@exemplo.com",
                "manda 50 pix pra 11999990000",
                "quero enviar 25,50 pro +5511999990000",
            ],
        ),
    ],
)

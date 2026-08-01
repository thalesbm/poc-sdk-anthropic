"""AgentCard estático do especialista RAG."""

from __future__ import annotations

import os

from a2a_common.models import AgentCard, AgentCapabilities, AgentSkill

BASE_URL = os.getenv("AGENT_RAG_URL", "http://localhost:8300")

CARD = AgentCard(
    name="agent-rag-faq",
    description=(
        "Especialista em respostas com base em FAQ/base de conhecimento do banco. "
        "Sempre busca em documentos antes de responder e cita fontes."
    ),
    url=BASE_URL,
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=False, push_notifications=False),
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    skills=[
        AgentSkill(
            id="faq-search",
            name="Perguntas sobre políticas, tarifas e produtos",
            description=(
                "Responde perguntas gerais sobre limites, tarifas, procedimentos "
                "e produtos do banco (PIX, cartão, conta, investimentos), sempre "
                "citando os documentos consultados."
            ),
            tags=["knowledge", "rag", "read-only"],
            examples=[
                "qual o limite diário do pix?",
                "como bloqueio meu cartão?",
                "quanto rende minha conta?",
                "quais investimentos vocês oferecem?",
                "o pix cobra tarifa?",
            ],
        ),
    ],
)

"""Exemplo mínimo: Claude Agent SDK conectado ao Claude via Amazon Bedrock.

Requer no .env (raiz do repo):
    CLAUDE_CODE_USE_BEDROCK=1
    AWS_REGION=us-east-1
    AWS_ACCESS_KEY_ID=...
    AWS_SECRET_ACCESS_KEY=...
    # (opcional) AWS_SESSION_TOKEN=...   ← se usar credenciais temporárias
    # (alternativa) AWS_PROFILE=<perfil> ← se usa aws configure/SSO

    # ID do modelo Bedrock (ex.):
    ANTHROPIC_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
    # ou um cross-region inference profile:
    # ANTHROPIC_MODEL=us.anthropic.claude-haiku-4-5-20260930-v1:0

Descubra os IDs disponíveis na sua conta+região:
    aws bedrock list-foundation-models --by-provider anthropic \\
        --region us-east-1 \\
        --query "modelSummaries[?contains(modelId, 'claude')].modelId" \\
        --output table

Uso:
    python bedrock.py
    python bedrock.py "qual a capital do Japão?"

O código do agente é IDÊNTICO ao anthropic_api.py — só muda o .env.
"""

from __future__ import annotations

import asyncio
import os
import sys

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
)
from dotenv import find_dotenv, load_dotenv

DEFAULT_QUESTION = (
    "Em uma frase, qual a diferença entre Bedrock e a API direta da Anthropic?"
)


async def run(question: str) -> None:
    model = os.getenv("ANTHROPIC_MODEL", "anthropic.claude-3-5-haiku-20241022-v1:0")
    region = os.getenv("AWS_REGION", "us-east-1")
    print(f"[provider] Amazon Bedrock ({region})")
    print(f"[model]    {model}")
    print(f"[pergunta] {question}\n")

    options = ClaudeAgentOptions(
        system_prompt="Você responde em português do Brasil, sempre objetivo.",
        model=model,
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query(question)
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock) and block.text.strip():
                        print(block.text)
            elif isinstance(msg, ResultMessage):
                cost = getattr(msg, "total_cost_usd", None)
                duration = getattr(msg, "duration_ms", None)
                print()
                # Nota: pela Anthropic API, cost_usd vem populado.
                # Via Bedrock, cobrança é AWS — pode vir None ou zero aqui.
                if cost is not None:
                    print(f"[custo]    US$ {cost:.6f} (via SDK — cobrança real é AWS)")
                else:
                    print("[custo]    n/d (via Bedrock, veja o AWS bill)")
                if duration is not None:
                    print(f"[duração]  {duration} ms")


def _check_env() -> str | None:
    if os.getenv("CLAUDE_CODE_USE_BEDROCK") != "1":
        return (
            "CLAUDE_CODE_USE_BEDROCK não está setado como '1'. "
            "Defina no .env da raiz."
        )
    have_keys = os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")
    have_profile = os.getenv("AWS_PROFILE")
    if not (have_keys or have_profile):
        return (
            "Credenciais AWS não encontradas. Configure AWS_ACCESS_KEY_ID+"
            "AWS_SECRET_ACCESS_KEY ou AWS_PROFILE no .env da raiz."
        )
    return None


def main() -> int:
    load_dotenv(find_dotenv())
    err = _check_env()
    if err:
        print(f"ERRO: {err}", file=sys.stderr)
        return 1

    question = " ".join(sys.argv[1:]) or DEFAULT_QUESTION
    asyncio.run(run(question))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

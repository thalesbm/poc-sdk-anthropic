"""Exemplo mínimo: Claude Agent SDK conectado à Anthropic API (default).

Requer no .env (raiz do repo):
    ANTHROPIC_API_KEY=sk-ant-...

Uso:
    python anthropic_api.py
    python anthropic_api.py "qual a capital da França?"
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
    "Em uma frase, o que é o Model Context Protocol (MCP)?"
)


async def run(question: str) -> None:
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
    print(f"[provider] Anthropic API")
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
                print(
                    f"[custo]    US$ {cost:.6f}"
                    if cost is not None
                    else "[custo]    (n/d)"
                )
                if duration is not None:
                    print(f"[duração]  {duration} ms")


def main() -> int:
    load_dotenv(find_dotenv())
    if not os.getenv("ANTHROPIC_API_KEY"):
        print(
            "ERRO: ANTHROPIC_API_KEY não definida no .env da raiz.",
            file=sys.stderr,
        )
        return 1

    question = " ".join(sys.argv[1:]) or DEFAULT_QUESTION
    asyncio.run(run(question))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

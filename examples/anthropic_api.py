from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import Sequence
from datetime import datetime
from typing import TextIO

from claude_agent_sdk import (
    query,
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
)
from claude_agent_sdk.types import (
    HookContext,
    HookInput,
    HookJSONOutput,
    HookMatcher,
)
from dotenv import find_dotenv, load_dotenv

DEFAULT_QUESTIONS = (
    "Qual a capital do Brasil?",
    "Qual a capital da França?",
    "Qual a capital do Japão?",
    "Qual a capital da China?",
    "Qual a capital da Alemanha?",
    "Qual a capital da Itália?",
    "Qual a capital da Espanha?",
    "Qual a capital da Inglaterra?",
    "Qual a capital da França?",
)


def log(message: str, *, file: TextIO = sys.stdout) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"{timestamp} {message}", file=file)


async def on_user_prompt_submit(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    """Adiciona instruções sempre que o usuário envia um prompt."""
    log("[hook] UserPromptSubmit acionado")
    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": (
                "Responda em português do Brasil de forma objetiva e didática."
            ),
        }
    }


async def run(questions: Sequence[str]) -> None:
    options = ClaudeAgentOptions(
        system_prompt="Você responde em português do Brasil, sempre objetivo.",
        # model=model,
        hooks={
            "UserPromptSubmit": [
                HookMatcher(matcher=None, hooks=[on_user_prompt_submit]),
            ]
        },
    )

    for question in questions:
        log(f"[pergunta] {question}")
        log("[query] iniciando query...")
        async for msg in query(
            prompt=question,
            options=options,
        ):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock) and block.text.strip():
                        print(block.text)
            elif isinstance(msg, ResultMessage):
                cost = getattr(msg, "total_cost_usd", None)
                duration = getattr(msg, "duration_ms", None)
                log(
                    f"[custo]    US$ {cost:.6f}"
                    if cost is not None
                    else "[custo]    (n/d)"
                )
                if duration is not None:
                    log(f"[duração]  {duration} ms")
        print()


def main() -> int:
    load_dotenv(find_dotenv())
    if not os.getenv("ANTHROPIC_API_KEY"):
        log(
            "ERRO: ANTHROPIC_API_KEY não definida no .env da raiz.",
            file=sys.stderr,
        )
        return 1

    questions = tuple(sys.argv[1:]) or DEFAULT_QUESTIONS
    asyncio.run(run(questions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

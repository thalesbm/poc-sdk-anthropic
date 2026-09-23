from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import Sequence
from datetime import datetime
from typing import TextIO

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    query,
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
    # model = os.getenv("ANTHROPIC_MODEL", "anthropic.claude-3-5-haiku-20241022-v1:0")
    # region = os.getenv("AWS_REGION", "us-east-1")
    # print(f"[provider] Amazon Bedrock ({region})")
    # print(f"[model]    {model}")
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
                print()
                # Nota: pela Anthropic API, cost_usd vem populado.
                # Via Bedrock, cobrança é AWS — pode vir None ou zero aqui.
                if cost is not None:
                    log(
                        f"[custo]    US$ {cost:.6f} "
                        "(via SDK — cobrança real é AWS)"
                    )
                else:
                    log("[custo]    n/d (via Bedrock, veja o AWS bill)")
                if duration is not None:
                    log(f"[duração]  {duration} ms")
        print()


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
        log(f"ERRO: {err}", file=sys.stderr)
        return 1

    questions = tuple(sys.argv[1:]) or DEFAULT_QUESTIONS
    asyncio.run(run(questions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

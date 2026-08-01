"""Entrypoint do orquestrador — chat CLI que roteia via A2A.

Uso (a partir de `agent-orchestrator/`):
    python main.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv

from app.chat import run_chat


def main() -> int:
    load_dotenv()
    if not os.getenv("ANTHROPIC_API_KEY"):
        print(
            "ERRO: variável ANTHROPIC_API_KEY não definida. "
            "Copie .env.example para .env e configure sua chave.",
            file=sys.stderr,
        )
        return 1

    asyncio.run(run_chat())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

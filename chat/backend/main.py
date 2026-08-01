"""Entrypoint HTTP da API do chat — sobe uvicorn.

Uso (a partir de `chat/backend/`):
    python main.py            # http://localhost:8400
    CHAT_API_PORT=9000 python main.py
"""

from __future__ import annotations

import os
import sys

import uvicorn
from dotenv import load_dotenv


def main() -> int:
    load_dotenv()
    if not os.getenv("ANTHROPIC_API_KEY"):
        print(
            "ERRO: variável ANTHROPIC_API_KEY não definida. "
            "Copie .env.example para .env e configure sua chave.",
            file=sys.stderr,
        )
        return 1

    port = int(os.getenv("CHAT_API_PORT", "8400"))
    uvicorn.run("app.api:app", host="0.0.0.0", port=port, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

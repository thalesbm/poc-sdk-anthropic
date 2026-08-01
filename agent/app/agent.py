"""Assistente pessoal usando o Claude Agent SDK.

Uso:

    python agent.py

Abre um chat interativo com `ClaudeSDKClient`, mantendo o contexto entre as
perguntas. As tools do agente são geradas dinamicamente a partir do endpoint
de discovery da API HTTP em `mcp-server/api.py` (`GET /tools`) e cada chamada
é proxyada via `POST /tools/{name}/invoke`.
"""

from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    TextBlock,
)

from mcp_client.config import SERVER_NAME
from mcp_client.server import (
    ALLOWED_TOOLS,
    DISCOVERED_TOOLS,
    build_assistant_server,
)
from prompt import build_system_prompt


def build_options() -> ClaudeAgentOptions:
    """Configura o agente: system prompt (com catálogo dinâmico), MCP server e tools."""
    return ClaudeAgentOptions(
        system_prompt=build_system_prompt(DISCOVERED_TOOLS),
        mcp_servers={SERVER_NAME: build_assistant_server()},
        allowed_tools=ALLOWED_TOOLS,
        permission_mode="acceptEdits",
        model="claude-haiku-4-5",
    )


def _print_assistant_text(message: AssistantMessage) -> None:
    for block in message.content:
        if isinstance(block, TextBlock) and block.text.strip():
            print(block.text)


async def run_chat() -> None:
    """Loop interativo mantendo a mesma sessão via `ClaudeSDKClient`."""
    options = build_options()
    tool_names = [t["name"] for t in DISCOVERED_TOOLS]
    print(
        f"Chat iniciado. {len(tool_names)} tool(s) descoberta(s) no mcp-server: "
        f"{', '.join(tool_names) or '(nenhuma)'}."
    )
    print("Digite 'sair' (ou Ctrl+D) para encerrar.\n")

    async with ClaudeSDKClient(options=options) as client:
        while True:
            try:
                user_input = input("você > ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not user_input:
                continue
            if user_input.lower() in {"sair", "exit", "quit"}:
                break

            await client.query(user_input)
            print("assistente > ", end="", flush=True)
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    _print_assistant_text(message)
            print()


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

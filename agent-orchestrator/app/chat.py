"""Loop de chat interativo do orquestrador."""

from __future__ import annotations

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
)

from .a2a_tools import SERVER_NAME, build_a2a_tools_server
from .prompt import build_system_prompt
from .registry import discover_agents


def _print_assistant_text(message: AssistantMessage) -> None:
    for block in message.content:
        if isinstance(block, TextBlock) and block.text.strip():
            print(block.text)


def _print_cost(message: ResultMessage) -> None:
    cost = getattr(message, "total_cost_usd", None)
    if cost is not None:
        print(f"\n[custo total: US$ {cost:.6f}]")


async def run_chat() -> None:
    agents = await discover_agents()
    slugs = [a.slug for a in agents]
    print(f"Orquestrador iniciado. {len(agents)} agente(s) A2A descoberto(s): {', '.join(slugs) or '(nenhum)'}.")
    print("Digite 'sair' (ou Ctrl+D) para encerrar.\n")

    server, allowed = build_a2a_tools_server(agents)
    options = ClaudeAgentOptions(
        system_prompt=build_system_prompt(agents),
        mcp_servers={SERVER_NAME: server},
        allowed_tools=allowed,
        permission_mode="acceptEdits",
        model="claude-haiku-4-5",
    )

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
            print("orquestrador > ", end="", flush=True)
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    _print_assistant_text(msg)
                elif isinstance(msg, ResultMessage):
                    _print_cost(msg)
            print()

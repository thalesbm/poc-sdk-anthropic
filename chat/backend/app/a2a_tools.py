"""Converte AgentCards descobertos em tools MCP in-process.

Cada agente remoto vira uma tool `call_<slug>(message)` que dispara um
`message/send` A2A e devolve o texto da resposta. O modelo orquestrador
decide qual chamar.
"""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from a2a_common.client import A2AClient, extract_text

from .registry import RemoteAgent

SERVER_NAME = "a2a"


def _make_tool_handler(agent: RemoteAgent):
    async def _handler(args: dict[str, Any]) -> dict[str, Any]:
        message = (args.get("message") or "").strip()
        if not message:
            return {
                "content": [{"type": "text", "text": "Mensagem vazia."}],
                "is_error": True,
            }
        client = A2AClient(agent.url)
        try:
            task = await client.send_text(message)
        except Exception as exc:  # noqa: BLE001
            return {
                "content": [{"type": "text", "text": f"Falha ao chamar {agent.slug}: {exc}"}],
                "is_error": True,
            }
        return {"content": [{"type": "text", "text": extract_text(task)}]}

    return _handler


def build_a2a_tools_server(agents: list[RemoteAgent]):
    tools = []
    allowed: list[str] = []

    for agent in agents:
        skill_lines = "; ".join(
            f"{s.name}: {s.description}" for s in agent.card.skills
        ) or "(sem skills declaradas)"
        tool_name = f"call_{agent.slug}"
        description = (
            f"Encaminha uma mensagem em texto para o agente remoto "
            f"'{agent.card.name}' via A2A e retorna a resposta. "
            f"Skills declaradas: {skill_lines}"
        )
        decorated = tool(tool_name, description, {"message": str})(
            _make_tool_handler(agent)
        )
        tools.append(decorated)
        allowed.append(f"mcp__{SERVER_NAME}__{tool_name}")

    server = create_sdk_mcp_server(name=SERVER_NAME, version="1.0.0", tools=tools)
    return server, allowed

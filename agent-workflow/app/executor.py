"""Bridge A2A → Claude SDK com HITL.

Fluxo:
    1. Cada task_id tem um estado in-memory: `{"confirmed": bool}`.
    2. Ao receber uma mensagem, se o texto parece uma confirmação
       ("sim", "confirmo", "ok", ...), marcamos `confirmed = True`.
    3. Rebuild do `ClaudeSDKClient` com o histórico da task replicado como
       contexto no user prompt (POC não persiste sessão do SDK).
    4. `can_use_tool` bloqueia toda `executar_*` enquanto `confirmed` for
       False. Também levanta uma flag `needs_hitl` que é usada para marcar a
       task como `input-required` no final.
    5. Após confirmar e executar, `confirmed` volta a `False` para o próximo
       ciclo.
"""

from __future__ import annotations

import re
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    TextBlock,
)

from a2a_common.models import Artifact, Message, Task, TaskState, TextPart
from a2a_common.server import HandlerResult

from .mcp_client.config import SERVER_NAME
from .mcp_client.server import (
    ALLOWED_TOOLS,
    DISCOVERED_TOOLS,
    SENSITIVE_TOOL_NAMES,
    build_assistant_server,
)
from .prompt import build_system_prompt


# task_id → estado do workflow
_TASK_STATE: dict[str, dict[str, Any]] = {}

_CONFIRM_PATTERN = re.compile(
    r"\b(sim|confirmo|confirmar|ok|pode(?:\s+ir)?|aprovo|manda|beleza|vamos)\b",
    re.IGNORECASE,
)
_CANCEL_PATTERN = re.compile(
    r"\b(n[ãa]o|cancel(?:a|ar)|para|desiste)\b",
    re.IGNORECASE,
)


def _extract_text(message: Message) -> str:
    return "\n".join(p.text for p in message.parts if isinstance(p, TextPart)).strip()


def _serialize_history(task: Task | None) -> str:
    """Serializa histórico da task como contexto de texto."""
    if not task or not task.history:
        return ""
    lines = ["[Contexto da conversa anterior:]"]
    for msg in task.history:
        text = "\n".join(p.text for p in msg.parts if isinstance(p, TextPart)).strip()
        if text:
            lines.append(f"{msg.role}: {text}")
    lines.append("[Fim do contexto]\n")
    return "\n".join(lines)


def _get_state(task_id: str) -> dict[str, Any]:
    if task_id not in _TASK_STATE:
        _TASK_STATE[task_id] = {"confirmed": False}
    return _TASK_STATE[task_id]


async def handle_message(message: Message, existing_task: Task | None) -> HandlerResult:
    user_text = _extract_text(message)
    if not user_text:
        return HandlerResult(
            message=Message(role="agent", parts=[TextPart(text="(mensagem vazia)")]),
            state=TaskState.FAILED,
        )

    task_id = message.task_id or "no-task"
    state = _get_state(task_id)

    if _CANCEL_PATTERN.search(user_text) and not _CONFIRM_PATTERN.search(user_text):
        state["confirmed"] = False
    elif _CONFIRM_PATTERN.search(user_text):
        state["confirmed"] = True

    needs_hitl = False

    async def can_use_tool(tool_name: str, tool_input: dict[str, Any], _ctx) -> dict[str, Any]:
        # Remove o prefixo "mcp__<server>__" que o SDK adiciona ao nome da tool
        bare = tool_name.split("__")[-1]
        if bare in SENSITIVE_TOOL_NAMES and not state["confirmed"]:
            nonlocal needs_hitl
            needs_hitl = True
            return {
                "behavior": "deny",
                "message": (
                    f"Bloqueado por política HITL: '{bare}' requer confirmação "
                    "explícita do cliente. Simule a operação (se ainda não fez), "
                    "apresente o preview e pergunte ao cliente se confirma."
                ),
            }
        return {"behavior": "allow", "updatedInput": tool_input}

    options = ClaudeAgentOptions(
        system_prompt=build_system_prompt(DISCOVERED_TOOLS),
        mcp_servers={SERVER_NAME: build_assistant_server()},
        allowed_tools=ALLOWED_TOOLS,
        permission_mode="acceptEdits",
        can_use_tool=can_use_tool,
        model="claude-haiku-4-5",
    )

    prompt_with_history = f"{_serialize_history(existing_task)}\nNova mensagem do usuário: {user_text}".strip()

    chunks: list[str] = []
    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt_with_history)
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock) and block.text.strip():
                        chunks.append(block.text)

    answer = "\n".join(chunks).strip() or "(sem resposta)"

    if needs_hitl:
        # Não completou; aguardando confirmação do cliente.
        final_state = TaskState.INPUT_REQUIRED
    else:
        final_state = TaskState.COMPLETED
        # Reset — próxima operação começa exigindo nova confirmação
        state["confirmed"] = False

    return HandlerResult(
        message=Message(role="agent", parts=[TextPart(text=answer)]),
        artifacts=[Artifact(name="reply", parts=[TextPart(text=answer)])],
        state=final_state,
    )

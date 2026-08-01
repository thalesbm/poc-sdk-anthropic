"""Bridge A2A → Claude SDK para o especialista ReAct."""

from __future__ import annotations

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
    build_assistant_server,
)
from .prompt import build_system_prompt


def _build_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=build_system_prompt(DISCOVERED_TOOLS),
        mcp_servers={SERVER_NAME: build_assistant_server()},
        allowed_tools=ALLOWED_TOOLS,
        permission_mode="acceptEdits",
        model="claude-haiku-4-5",
    )


def _extract_user_text(message: Message) -> str:
    parts = [p.text for p in message.parts if isinstance(p, TextPart)]
    return "\n".join(parts).strip()


async def handle_message(message: Message, _existing_task: Task | None) -> HandlerResult:
    user_text = _extract_user_text(message)
    if not user_text:
        return HandlerResult(
            message=Message(role="agent", parts=[TextPart(text="(mensagem vazia)")]),
            state=TaskState.FAILED,
        )

    chunks: list[str] = []
    async with ClaudeSDKClient(options=_build_options()) as client:
        await client.query(user_text)
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock) and block.text.strip():
                        chunks.append(block.text)

    answer = "\n".join(chunks).strip() or "(sem resposta)"
    return HandlerResult(
        message=Message(role="agent", parts=[TextPart(text=answer)]),
        artifacts=[Artifact(name="reply", parts=[TextPart(text=answer)])],
        state=TaskState.COMPLETED,
    )

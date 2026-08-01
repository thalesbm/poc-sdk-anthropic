"""Cliente A2A async (httpx)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx

from .models import AgentCard, Message, Task, TextPart


class A2AClientError(RuntimeError):
    pass


class A2AClient:
    """Cliente mínimo A2A: descoberta de card + message/send + tasks/get."""

    def __init__(self, base_url: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get_card(self) -> AgentCard:
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            r = await c.get(f"{self.base_url}/.well-known/agent.json")
            r.raise_for_status()
            return AgentCard.model_validate(r.json())

    async def _rpc(self, method: str, params: dict[str, Any]) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid4()),
            "method": method,
            "params": params,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            r = await c.post(f"{self.base_url}/", json=payload)
            r.raise_for_status()
            body = r.json()

        if body.get("error"):
            raise A2AClientError(f"{method} → {body['error']}")
        return body["result"]

    async def send_text(self, text: str, task_id: str | None = None) -> Task:
        msg = Message(role="user", parts=[TextPart(text=text)], task_id=task_id)
        result = await self._rpc(
            "message/send",
            {"message": msg.model_dump(by_alias=True, exclude_none=True)},
        )
        return Task.model_validate(result)

    async def get_task(self, task_id: str) -> Task:
        result = await self._rpc("tasks/get", {"id": task_id})
        return Task.model_validate(result)


def extract_text(task: Task) -> str:
    """Concatena o texto de todos os artifacts + última mensagem do agente."""
    chunks: list[str] = []
    for art in task.artifacts:
        for part in art.parts:
            if isinstance(part, TextPart):
                chunks.append(part.text)
    for msg in reversed(task.history):
        if msg.role == "agent":
            for part in msg.parts:
                if isinstance(part, TextPart) and part.text not in chunks:
                    chunks.append(part.text)
            break
    return "\n".join(chunks).strip()

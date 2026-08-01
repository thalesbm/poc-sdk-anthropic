"""Factory de servidor A2A genérico.

O handler recebe a mensagem do usuário e (opcionalmente) a task existente, e
devolve um `HandlerResult` com artifacts, mensagem de resposta e o estado
final da task (COMPLETED, INPUT_REQUIRED, FAILED). Estado das tasks é
mantido em memória.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Awaitable, Callable

from fastapi import FastAPI, Request

from .jsonrpc import (
    ERROR_INTERNAL,
    ERROR_INVALID_PARAMS,
    ERROR_METHOD_NOT_FOUND,
    ERROR_TASK_NOT_FOUND,
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
)
from .models import (
    AgentCard,
    Artifact,
    Message,
    MessageSendParams,
    Task,
    TaskQueryParams,
    TaskState,
    TaskStatus,
)


@dataclass
class HandlerResult:
    """Resultado devolvido por um handler A2A."""

    message: Message
    artifacts: list[Artifact] = field(default_factory=list)
    state: TaskState = TaskState.COMPLETED


Handler = Callable[[Message, "Task | None"], Awaitable[HandlerResult]]


def create_a2a_app(card: AgentCard, handler: Handler) -> FastAPI:
    app = FastAPI(title=card.name, description=card.description, version=card.version)
    tasks: dict[str, Task] = {}

    @app.get("/.well-known/agent.json")
    def agent_card() -> dict:
        return card.model_dump(by_alias=True, exclude_none=True)

    async def _handle_message_send(params_raw: dict, rpc_id) -> JSONRPCResponse:
        try:
            params = MessageSendParams(**params_raw)
        except Exception as exc:
            return JSONRPCResponse(
                id=rpc_id,
                error=JSONRPCError(code=ERROR_INVALID_PARAMS, message=str(exc)),
            )

        incoming = params.message
        existing = tasks.get(incoming.task_id) if incoming.task_id else None

        if existing is None:
            task = Task(status=TaskStatus(state=TaskState.WORKING), history=[incoming])
            incoming.task_id = task.id
            incoming.context_id = task.context_id
        else:
            task = existing
            incoming.task_id = task.id
            incoming.context_id = task.context_id
            task.history.append(incoming)
            task.status = TaskStatus(state=TaskState.WORKING)

        tasks[task.id] = task

        try:
            result = await handler(incoming, existing)
        except Exception as exc:
            task.status = TaskStatus(state=TaskState.FAILED)
            return JSONRPCResponse(
                id=rpc_id,
                error=JSONRPCError(code=ERROR_INTERNAL, message=f"Handler error: {exc}"),
            )

        result.message.task_id = task.id
        result.message.context_id = task.context_id
        task.history.append(result.message)
        task.artifacts.extend(result.artifacts)
        task.status = TaskStatus(state=result.state)

        return JSONRPCResponse(id=rpc_id, result=task.model_dump(by_alias=True, exclude_none=True))

    async def _handle_tasks_get(params_raw: dict, rpc_id) -> JSONRPCResponse:
        try:
            params = TaskQueryParams(**params_raw)
        except Exception as exc:
            return JSONRPCResponse(
                id=rpc_id,
                error=JSONRPCError(code=ERROR_INVALID_PARAMS, message=str(exc)),
            )
        task = tasks.get(params.id)
        if task is None:
            return JSONRPCResponse(
                id=rpc_id,
                error=JSONRPCError(code=ERROR_TASK_NOT_FOUND, message=f"Task {params.id} não encontrada"),
            )
        return JSONRPCResponse(id=rpc_id, result=task.model_dump(by_alias=True, exclude_none=True))

    @app.post("/")
    async def rpc(req: Request) -> dict:
        try:
            payload = await req.json()
            rpc_req = JSONRPCRequest(**payload)
        except Exception as exc:
            return JSONRPCResponse(
                id=None,
                error=JSONRPCError(code=ERROR_INVALID_PARAMS, message=str(exc)),
            ).model_dump(exclude_none=True)

        if rpc_req.method == "message/send":
            resp = await _handle_message_send(rpc_req.params, rpc_req.id)
        elif rpc_req.method == "tasks/get":
            resp = await _handle_tasks_get(rpc_req.params, rpc_req.id)
        else:
            resp = JSONRPCResponse(
                id=rpc_req.id,
                error=JSONRPCError(code=ERROR_METHOD_NOT_FOUND, message=rpc_req.method),
            )

        return resp.model_dump(exclude_none=True)

    return app

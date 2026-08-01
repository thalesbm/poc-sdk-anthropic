"""API REST do chat — orquestra chamadas A2A para os agentes especialistas.

Contrato mínimo:
    GET  /api/agents      → lista de agentes A2A descobertos
    POST /api/chat        → { "message": str } → { "reply": str, "cost_usd": float | None }
    POST /api/reset       → reinicia a sessão (novo ClaudeSDKClient)

Sessão única (POC single-user). Um `ClaudeSDKClient` é mantido em memória
durante o lifespan do processo.

O frontend HTML vive em `chat/frontend/` e é servido separadamente.
CORS liberado (`*`) porque é POC — restrinja em produção com CORS_ALLOW_ORIGINS.
"""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .a2a_tools import SERVER_NAME, build_a2a_tools_server
from .prompt import build_system_prompt
from .registry import RemoteAgent, discover_agents


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    cost_usd: float | None = None


class AgentInfo(BaseModel):
    slug: str
    name: str
    description: str
    url: str


class _Session:
    """Encapsula o ClaudeSDKClient + lock para acesso serializado."""

    def __init__(self, agents: list[RemoteAgent]) -> None:
        self.agents = agents
        self._client: ClaudeSDKClient | None = None
        self._lock = asyncio.Lock()

    async def _ensure_client(self) -> ClaudeSDKClient:
        if self._client is None:
            server, allowed = build_a2a_tools_server(self.agents)
            options = ClaudeAgentOptions(
                system_prompt=build_system_prompt(self.agents),
                mcp_servers={SERVER_NAME: server},
                allowed_tools=allowed,
                permission_mode="acceptEdits",
                model="claude-haiku-4-5",
            )
            self._client = ClaudeSDKClient(options=options)
            await self._client.__aenter__()
        return self._client

    async def send(self, text: str) -> ChatResponse:
        async with self._lock:
            client = await self._ensure_client()
            await client.query(text)
            reply_parts: list[str] = []
            cost: float | None = None
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock) and block.text.strip():
                            reply_parts.append(block.text)
                elif isinstance(msg, ResultMessage):
                    cost = getattr(msg, "total_cost_usd", None)
            return ChatResponse(reply="\n\n".join(reply_parts).strip(), cost_usd=cost)

    async def reset(self) -> None:
        async with self._lock:
            if self._client is not None:
                await self._client.__aexit__(None, None, None)
                self._client = None

    async def aclose(self) -> None:
        await self.reset()


@asynccontextmanager
async def _lifespan(app: FastAPI):
    agents = await discover_agents()
    session = _Session(agents)
    app.state.session = session
    app.state.agents = agents
    try:
        yield
    finally:
        await session.aclose()


app = FastAPI(title="chat backend", lifespan=_lifespan)

_allowed_origins = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/agents", response_model=list[AgentInfo])
async def list_agents() -> list[AgentInfo]:
    return [
        AgentInfo(
            slug=a.slug,
            name=a.card.name,
            description=a.card.description or "",
            url=a.url,
        )
        for a in app.state.agents
    ]


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    text = req.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="mensagem vazia")
    session: _Session = app.state.session
    return await session.send(text)


@app.post("/api/reset")
async def reset() -> dict[str, Any]:
    session: _Session = app.state.session
    await session.reset()
    return {"status": "ok"}

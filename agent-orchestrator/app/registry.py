"""Registro de agentes remotos conhecidos.

Lê a env var `A2A_AGENT_URLS` (URLs separadas por vírgula) e descobre o
AgentCard de cada uma. Fallback default: só o agent-react local.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from a2a_common.client import A2AClient
from a2a_common.models import AgentCard

_DEFAULT_URLS = "http://localhost:8100"


@dataclass(frozen=True)
class RemoteAgent:
    slug: str
    url: str
    card: AgentCard


def _slugify(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")


async def _discover_one(url: str) -> RemoteAgent:
    client = A2AClient(url)
    card = await client.get_card()
    return RemoteAgent(slug=_slugify(card.name), url=url, card=card)


async def discover_agents() -> list[RemoteAgent]:
    urls = [u.strip() for u in os.getenv("A2A_AGENT_URLS", _DEFAULT_URLS).split(",") if u.strip()]
    return await asyncio.gather(*(_discover_one(u) for u in urls))

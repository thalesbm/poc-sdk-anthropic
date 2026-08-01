"""Invocação de tools remotas via `POST /tools/{name}/invoke`.

Devolve o payload já formatado no formato esperado pelo MCP (`content` +
`is_error`), pronto para ser retornado por um handler `@tool`.
"""

from __future__ import annotations

from typing import Any

import httpx

from .config import HTTP_TIMEOUT, MCP_API_BASE_URL


async def invoke_tool(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Chama a tool remota e traduz a resposta para o formato MCP."""
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.post(
                f"{MCP_API_BASE_URL}/tools/{tool_name}/invoke",
                json={"arguments": args},
            )
    except httpx.HTTPError as exc:
        return _error(f"Falha de rede ao chamar '{tool_name}': {exc}")

    if resp.status_code >= 400:
        return _error(f"Erro HTTP {resp.status_code}: {resp.text}")

    payload = resp.json()
    return {
        "content": [{"type": "text", "text": str(payload.get("result", payload))}]
    }


def _error(msg: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": msg}], "is_error": True}

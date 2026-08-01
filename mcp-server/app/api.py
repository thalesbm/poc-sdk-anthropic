"""API HTTP para descoberta e execução das ferramentas mockadas.

Endpoints:
    GET  /health                → status
    GET  /tools                 → discovery (lista tools com schemas)
    GET  /tools/{name}          → metadata de uma tool específica
    POST /tools/{name}/invoke   → executa uma tool com argumentos JSON

Uso (a partir de `mcp-server/`):
    python -m app.api
    # ou:
    uvicorn app.api:app --reload --port 8000
"""

from __future__ import annotations

import inspect
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .tools import TOOLS, TOOLS_BY_NAME, ToolSpec

app = FastAPI(
    title="Banco Mock - HTTP API",
    description="API HTTP para as tools bancárias mockadas.",
    version="1.0.0",
)


class InvokeRequest(BaseModel):
    arguments: dict[str, Any] = {}


class InvokeResponse(BaseModel):
    tool: str
    result: Any


def _serialize_tool(spec: ToolSpec) -> dict[str, Any]:
    return {
        "name": spec.name,
        "description": spec.description,
        "input_schema": spec.input_schema,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tools", summary="Discovery: lista todas as tools disponíveis")
def list_tools() -> dict[str, Any]:
    return {"tools": [_serialize_tool(t) for t in TOOLS]}


@app.get("/tools/{name}", summary="Metadata de uma tool específica")
def get_tool(name: str) -> dict[str, Any]:
    spec = TOOLS_BY_NAME.get(name)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"Tool '{name}' não encontrada.")
    return _serialize_tool(spec)


@app.post(
    "/tools/{name}/invoke",
    response_model=InvokeResponse,
    summary="Executa uma tool com os argumentos fornecidos",
)
def invoke_tool(name: str, payload: InvokeRequest) -> InvokeResponse:
    spec = TOOLS_BY_NAME.get(name)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"Tool '{name}' não encontrada.")

    valid_params = set(inspect.signature(spec.handler).parameters)
    unknown = set(payload.arguments) - valid_params
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Argumento(s) desconhecido(s) para '{name}': {sorted(unknown)}",
        )

    try:
        result = spec.handler(**payload.arguments)
    except TypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Erro ao executar '{name}': {exc}") from exc

    return InvokeResponse(tool=name, result=result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.api:app", host="0.0.0.0", port=8000)

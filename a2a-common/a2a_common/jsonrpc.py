"""Envelopes JSON-RPC 2.0."""

from __future__ import annotations

from typing import Any, Optional, Union

from pydantic import BaseModel


class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Any = None


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    method: str
    params: dict[str, Any] = {}


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Any = None
    error: Optional[JSONRPCError] = None


# Códigos padrão JSON-RPC + estendidos A2A
ERROR_PARSE = -32700
ERROR_INVALID_REQUEST = -32600
ERROR_METHOD_NOT_FOUND = -32601
ERROR_INVALID_PARAMS = -32602
ERROR_INTERNAL = -32603

ERROR_TASK_NOT_FOUND = -32001
ERROR_TASK_NOT_CANCELABLE = -32002

"""Dataclass usada para descrever cada tool exposta pela API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    handler: Callable[..., dict[str, Any]]
    input_schema: dict[str, Any]

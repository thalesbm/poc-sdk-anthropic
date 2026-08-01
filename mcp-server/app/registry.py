"""Registro central de tools.

Faz varredura automática dos módulos em `app/tools/` (ignorando os que começam
com `_`) e coleta o atributo `SPEC` de cada um. Assim, adicionar uma nova
tool exige apenas criar o arquivo `app/tools/nova_tool.py` com um `SPEC` —
nenhum registro manual é necessário.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

from . import tools as _tools_pkg
from .tools._spec import ToolSpec

__all__ = ["TOOLS", "TOOLS_BY_NAME", "ToolSpec"]


def _load_specs() -> list[ToolSpec]:
    specs: list[ToolSpec] = []
    for module_info in pkgutil.iter_modules(_tools_pkg.__path__):
        if module_info.name.startswith("_"):
            continue
        module: Any = importlib.import_module(f"{_tools_pkg.__name__}.{module_info.name}")
        spec = getattr(module, "SPEC", None)
        if isinstance(spec, ToolSpec):
            specs.append(spec)
    specs.sort(key=lambda s: s.name)
    return specs


TOOLS: list[ToolSpec] = _load_specs()
TOOLS_BY_NAME: dict[str, ToolSpec] = {t.name: t for t in TOOLS}

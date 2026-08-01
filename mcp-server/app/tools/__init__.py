"""Registro central das tools expostas pela API.

Cada módulo irmão define uma função handler + um `SPEC: ToolSpec`. Para
adicionar uma tool nova, crie o módulo e adicione o `SPEC` na lista `TOOLS`
abaixo.
"""

from __future__ import annotations

from ._spec import ToolSpec
from .buscar_fatura import SPEC as _BUSCAR_FATURA
from .buscar_saldo import SPEC as _BUSCAR_SALDO
from .buscar_total_investimentos import SPEC as _BUSCAR_TOTAL_INVESTIMENTOS

__all__ = ["TOOLS", "TOOLS_BY_NAME", "ToolSpec"]

TOOLS: list[ToolSpec] = [
    _BUSCAR_SALDO,
    _BUSCAR_FATURA,
    _BUSCAR_TOTAL_INVESTIMENTOS,
]

TOOLS_BY_NAME: dict[str, ToolSpec] = {t.name: t for t in TOOLS}

"""System prompt do especialista ReAct."""

from __future__ import annotations

import json
from typing import Any

_BASE_PROMPT = (
    "Você é um especialista bancário ReAct em português do Brasil. Para "
    "qualquer pergunta sobre dados do cliente (saldo, fatura, investimentos, "
    "chaves PIX, etc.), use SEMPRE as tools MCP listadas abaixo em vez de "
    "responder de memória. Os dados são mockados; apresente-os de forma clara "
    "e concisa, formatando valores monetários em reais (R$) quando fizer sentido."
)


def _format_tool(spec: dict[str, Any]) -> str:
    name = spec["name"]
    description = (spec.get("description") or "").strip() or "(sem descrição)"
    props = ((spec.get("input_schema") or {}).get("properties")) or {}
    required = set((spec.get("input_schema") or {}).get("required") or [])

    if not props:
        args_line = "  args: (nenhum)"
    else:
        lines = []
        for arg, meta in props.items():
            extras = ["obrigatório" if arg in required else "opcional"]
            if meta.get("default") is not None:
                extras.append(f"default={json.dumps(meta['default'], ensure_ascii=False)}")
            if meta.get("enum"):
                extras.append(f"valores={meta['enum']}")
            line = f"    - {arg} ({meta.get('type','any')}, {', '.join(extras)})"
            if meta.get("description"):
                line += f": {meta['description']}"
            lines.append(line)
        args_line = "  args:\n" + "\n".join(lines)

    return f"- {name}: {description}\n{args_line}"


def build_system_prompt(discovered_tools: list[dict[str, Any]]) -> str:
    if not discovered_tools:
        catalog = "(nenhuma tool disponível)"
    else:
        catalog = "\n".join(_format_tool(t) for t in discovered_tools)
    return (
        f"{_BASE_PROMPT}\n\n"
        f"## Ferramentas disponíveis ({len(discovered_tools)})\n\n"
        f"{catalog}"
    )

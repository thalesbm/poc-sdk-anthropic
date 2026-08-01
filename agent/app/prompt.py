"""Composição do system prompt.

O prompt é montado dinamicamente: uma base fixa + o catálogo de tools
retornado pelo discovery da API do `mcp-server`. Assim, o modelo sabe
exatamente quais tools existem sem precisarmos manter uma lista hardcoded.
"""

from __future__ import annotations

import json
from typing import Any

_BASE_PROMPT = (
    "Você é um assistente financeiro em português do Brasil. Seja conciso e direto."
)


def _format_tool(spec: dict[str, Any]) -> str:
    name = spec["name"]
    description = spec.get("description", "").strip() or "(sem descrição)"

    schema = spec.get("input_schema") or {}
    props = schema.get("properties") or {}
    required = set(schema.get("required") or [])

    if not props:
        args_line = "  args: (nenhum)"
    else:
        lines = []
        for arg_name, arg_spec in props.items():
            arg_type = arg_spec.get("type", "any")
            is_required = "obrigatório" if arg_name in required else "opcional"
            default = arg_spec.get("default")
            enum = arg_spec.get("enum")
            arg_desc = (arg_spec.get("description") or "").strip()

            extras = [is_required]
            if default is not None:
                extras.append(f"default={json.dumps(default, ensure_ascii=False)}")
            if enum:
                extras.append(f"valores={enum}")

            line = f"    - {arg_name} ({arg_type}, {', '.join(extras)})"
            if arg_desc:
                line += f": {arg_desc}"
            lines.append(line)
        args_line = "  args:\n" + "\n".join(lines)

    return f"- {name}: {description}\n{args_line}"


def build_system_prompt(discovered_tools: list[dict[str, Any]]) -> str:
    """Monta o system prompt final combinando a base com o catálogo de tools."""
    if not discovered_tools:
        catalog = "(nenhuma tool disponível — o mcp-server não retornou nada.)"
    else:
        catalog = "\n".join(_format_tool(t) for t in discovered_tools)

    return (
        f"{_BASE_PROMPT}\n\n"
        f"## Ferramentas disponíveis ({len(discovered_tools)})\n\n"
        f"{catalog}"
    )

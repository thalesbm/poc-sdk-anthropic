"""System prompt do especialista Workflow."""

from __future__ import annotations

import json
from typing import Any

_BASE_PROMPT = (
    "Você é um especialista bancário em fluxos que exigem CONFIRMAÇÃO HUMANA "
    "(HITL), operando em português do Brasil. Sua responsabilidade principal é "
    "conduzir transferências PIX em duas etapas SEMPRE:\n"
    "1. SIMULAR primeiro (tool `simular_transferencia_pix`). Apresente o "
    "preview ao cliente com destinatário, valor e tarifa, e PERGUNTE se "
    "confirma. Não chame `executar_*` neste momento.\n"
    "2. EXECUTAR (tool `executar_transferencia_pix`) SOMENTE após o cliente "
    "responder algo como 'sim', 'confirmo', 'ok', 'pode ir', 'aprovo'. Se ele "
    "cancelar ou pedir mudança, NÃO execute; refaça a simulação se preciso.\n\n"
    "Regras importantes:\n"
    "- NUNCA chame `executar_transferencia_pix` sem prévia confirmação explícita "
    "do cliente. Se tentar, será bloqueado.\n"
    "- Após executar, apresente o comprovante retornado (id, valor, URL).\n"
    "- Se faltarem dados (chave ou valor), pergunte de forma direta.\n"
    "- Seja conciso; formate valores em R$ e não invente dados."
)


def _format_tool(spec: dict[str, Any]) -> str:
    name = spec["name"]
    description = (spec.get("description") or "").strip() or "(sem descrição)"
    props = ((spec.get("input_schema") or {}).get("properties")) or {}
    required = set((spec.get("input_schema") or {}).get("required") or [])
    lines = []
    for arg, meta in props.items():
        extras = ["obrigatório" if arg in required else "opcional"]
        if meta.get("default") is not None:
            extras.append(f"default={json.dumps(meta['default'], ensure_ascii=False)}")
        lines.append(f"    - {arg} ({meta.get('type','any')}, {', '.join(extras)})")
    args_block = "  args:\n" + "\n".join(lines) if lines else "  args: (nenhum)"
    return f"- {name}: {description}\n{args_block}"


def build_system_prompt(discovered_tools: list[dict[str, Any]]) -> str:
    catalog = "\n".join(_format_tool(t) for t in discovered_tools) or "(nenhuma)"
    return f"{_BASE_PROMPT}\n\n## Ferramentas disponíveis\n\n{catalog}"

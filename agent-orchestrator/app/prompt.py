"""System prompt do orquestrador."""

from __future__ import annotations

from .registry import RemoteAgent

_BASE = (
    "Você é um agente ORQUESTRADOR em português do Brasil. Você NÃO responde "
    "perguntas diretamente. Para cada mensagem do usuário, escolha o agente "
    "remoto mais adequado abaixo e chame a tool `call_<slug>` correspondente "
    "com a pergunta do usuário. Depois, apresente a resposta do agente de "
    "forma clara ao usuário. Se nenhum agente for adequado, avise o usuário."
)


def build_system_prompt(agents: list[RemoteAgent]) -> str:
    if not agents:
        return _BASE + "\n\n(Nenhum agente remoto disponível.)"

    lines = []
    for a in agents:
        skills = "\n".join(
            f"    - {s.name}: {s.description} (exemplos: {', '.join(s.examples) or '—'})"
            for s in a.card.skills
        )
        lines.append(
            f"- **call_{a.slug}** → {a.card.name}\n"
            f"  {a.card.description}\n"
            f"  Skills:\n{skills}"
        )
    catalog = "\n\n".join(lines)
    return f"{_BASE}\n\n## Agentes disponíveis ({len(agents)})\n\n{catalog}"

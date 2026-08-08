"""Agent Loop com **tool calling nativo** da Anthropic — pronto para produção.

Diferenças-chave vs. o ReAct textual (`react_agent.py`):

    ┌──────────────────────┬──────────────────────┬──────────────────────────┐
    │                      │ ReAct (texto)        │ Agent Loop (tools nat.)  │
    ├──────────────────────┼──────────────────────┼──────────────────────────┤
    │ Formato da ação      │ "Action: foo(...)"   │ tool_use block + JSON    │
    │ Validação de args    │ regex/parsing manual │ JSON Schema da API       │
    │ Paralelismo          │ 1 ação por turno     │ N tool_use por turno     │
    │ Tokens de raciocínio │ altos (Thought:)     │ baixos (opcional)        │
    │ Robustez             │ frágil (formato)     │ alta (contrato tipado)   │
    │ Debug                │ ótimo (texto legível)│ requer inspeção estrutur.│
    └──────────────────────┴──────────────────────┴──────────────────────────┘

Loop: enquanto `stop_reason == "tool_use"`, executa TODOS os `tool_use` do
turno (potencialmente em paralelo) e devolve os `tool_result` na próxima
mensagem. Termina quando o modelo para com `stop_reason == "end_turn"`.

Requer no .env da raiz:
    ANTHROPIC_API_KEY=sk-ant-...

Uso:
    python agent_loop.py
    python agent_loop.py "some 12+30 e me diga que horas são"
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from typing import Any, Callable

from anthropic import Anthropic
from anthropic.types import Message
from dotenv import find_dotenv, load_dotenv

SYSTEM_PROMPT = """Você é um assistente objetivo que responde em português do Brasil.

Uso das ferramentas:
- Use `calculator` para QUALQUER conta aritmética — nunca calcule de cabeça.
- Use `now` sempre que a pergunta envolver data/hora atual.
- Se puder resolver múltiplas sub-tarefas em paralelo, emita várias
  chamadas de ferramenta no mesmo turno.
- Se não precisar de ferramenta, responda direto.

Resposta final: uma frase curta, sem preâmbulo, sem repetir a pergunta.
"""


TOOLS_SCHEMA: list[dict[str, Any]] = [
    {
        "name": "calculator",
        "description": "Avalia uma expressão aritmética simples (apenas + - * / e parênteses).",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Expressão a avaliar, ex: '(23*7)+10'.",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "now",
        "description": "Retorna a data e hora atual no formato ISO 8601.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


class ToolLoopAgent:
    """Agent loop usando a Tools API nativa da Anthropic."""

    def __init__(
        self,
        model: str | None = None,
        max_steps: int = 6,
        verbose: bool = True,
    ) -> None:
        self.client = Anthropic()
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
        self.max_steps = max_steps
        self.verbose = verbose
        self.tools: dict[str, Callable[..., str]] = {
            "calculator": self._tool_calculator,
            "now": self._tool_now,
        }
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def chat(self, message: str) -> str:
        """Recebe uma mensagem e roda o loop até `end_turn`."""
        messages: list[dict[str, Any]] = [{"role": "user", "content": message}]

        for step in range(1, self.max_steps + 1):
            self._log(f"\n╭─── passo {step} ─────────────────────────────")
            response = self._call_model(messages)
            self._log(
                f"│ 📊 stop_reason={response.stop_reason} "
                f"tokens: in={response.usage.input_tokens} "
                f"out={response.usage.output_tokens}"
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                text = self._extract_text(response)
                self._log(f"│ ✅ Final: {text}")
                self._log("╰──────────────────────────────────────────────")
                self._log_totals()
                return text

            tool_results = []
            for block in response.content:
                if block.type == "text" and block.text.strip():
                    self._log(f"│ 💬 texto:   {block.text.strip()}")
                elif block.type == "tool_use":
                    self._log(f"│ 🔧 tool_use {block.name}({block.input})")
                    result = self._run_tool(block.name, block.input)
                    self._log(f"│ 👁  result:  {result}")
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )
            self._log("╰──────────────────────────────────────────────")
            messages.append({"role": "user", "content": tool_results})

        self._log_totals()
        return "Não foi possível concluir dentro do limite de passos."

    def _call_model(self, messages: list[dict[str, Any]]) -> Message:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS_SCHEMA,
            messages=messages,
        )
        self.total_input_tokens += response.usage.input_tokens
        self.total_output_tokens += response.usage.output_tokens
        return response

    def _run_tool(self, name: str, args: dict[str, Any]) -> str:
        tool = self.tools.get(name)
        if tool is None:
            return f"tool '{name}' não existe."
        try:
            return str(tool(**args))
        except Exception as exc:  # noqa: BLE001
            return f"erro ao executar {name}: {exc}"

    @staticmethod
    def _extract_text(response: Message) -> str:
        return "".join(
            b.text for b in response.content if b.type == "text"
        ).strip()

    @staticmethod
    def _tool_calculator(expression: str) -> str:
        if not re.fullmatch(r"[\d\s+\-*/().]+", expression):
            raise ValueError("expressão contém caracteres não permitidos")
        return str(eval(expression, {"__builtins__": {}}, {}))  # noqa: S307

    @staticmethod
    def _tool_now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg)

    def _log_totals(self) -> None:
        self._log(
            f"\n[totais] input={self.total_input_tokens} "
            f"output={self.total_output_tokens} tokens"
        )


def main() -> int:
    load_dotenv(find_dotenv())
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERRO: ANTHROPIC_API_KEY não definida no .env.", file=sys.stderr)
        return 1

    question = " ".join(sys.argv[1:]) or "Quanto é (23 * 7) + 10? Que horas são agora?"
    agent = ToolLoopAgent()
    print(f"[pergunta] {question}")
    final = agent.chat(question)
    print(f"\n=== resposta final ===\n{final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

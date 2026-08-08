"""Agente ReAct — didático e debugável, em uma única classe.

Foco desta versão: **você lê cada passo do raciocínio**. O agente separa e
imprime `Thought`, `Action` e `Observation` isoladamente, junto com contagem
de tokens por passo — útil para prototipar e para modelos sem function
calling nativo forte.

Formato ReAct (Yao et al., 2022 — https://arxiv.org/abs/2210.03629):

    Thought: <raciocínio verbalizado>
    Action: <tool_name>(<json_args>)
    Observation: <preenchido pelo runtime>
    ...
    Final Answer: <resposta>

Tools didáticas:
    - calculator(expression): avalia expressão aritmética simples.
    - now(): retorna data/hora atual (ISO 8601).

Requer no .env da raiz:
    ANTHROPIC_API_KEY=sk-ant-...

Uso:
    python react_agent.py
    python react_agent.py "quanto é (23*7) + 10? e que horas são?"
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from typing import Any, Callable

from anthropic import Anthropic
from dotenv import find_dotenv, load_dotenv

SYSTEM_PROMPT = """Você é um agente que segue ESTRITAMENTE a arquitetura ReAct.

Ferramentas disponíveis:
- calculator(expression: str) -> str  # avalia expressão aritmética
- now() -> str                        # data/hora atual em ISO 8601

Formato OBRIGATÓRIO por passo (cada label em uma linha):
Thought: <seu raciocínio explicando por que a próxima ação é necessária>
Action: <nome_da_tool>(<json_com_argumentos>)

Após "Action:", PARE. O runtime devolverá:
Observation: <resultado>

Repita Thought/Action/Observation quantas vezes precisar. Quando tiver a
resposta, responda APENAS:
Final Answer: <resposta objetiva em português>

Regras:
- Sempre em português do Brasil.
- Nunca invente Observations — espere o runtime.
- Se não precisar de tool, vá direto para "Final Answer:".
"""


class ReActAgent:
    """Agente ReAct minimalista, com trace verboso para inspeção."""

    THOUGHT_RE = re.compile(r"Thought:\s*(.+?)(?=\n(?:Action|Final Answer):|\Z)", re.DOTALL)
    ACTION_RE = re.compile(r"Action:\s*(\w+)\((.*?)\)\s*$", re.MULTILINE)
    FINAL_RE = re.compile(r"Final Answer:\s*(.+)", re.DOTALL)

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
        """Recebe uma mensagem e devolve a resposta final do ciclo ReAct."""
        transcript = f"Question: {message}\n"

        for step in range(1, self.max_steps + 1):
            self._log(f"\n╭─── passo {step} ─────────────────────────────")
            completion, usage = self._call_model(transcript)
            transcript += completion.rstrip() + "\n"

            thought = self._extract(self.THOUGHT_RE, completion)
            if thought:
                self._log(f"│ 💭 Thought:  {thought.strip()}")

            final = self._extract(self.FINAL_RE, completion)
            if final:
                self._log(f"│ ✅ Final:    {final.strip()}")
                self._log(f"│ 📊 tokens:   in={usage[0]} out={usage[1]}")
                self._log("╰──────────────────────────────────────────────")
                self._log_totals()
                return final.strip()

            match = self.ACTION_RE.search(completion)
            if not match:
                self._log("│ ⚠️  formato inválido — pedindo correção")
                transcript += (
                    "Observation: formato inválido. Use 'Action: tool(args)' "
                    "ou 'Final Answer: ...'.\n"
                )
                self._log("╰──────────────────────────────────────────────")
                continue

            tool_name, raw_args = match.group(1), match.group(2).strip()
            self._log(f"│ 🔧 Action:   {tool_name}({raw_args})")
            observation = self._run_tool(tool_name, raw_args)
            self._log(f"│ 👁  Observation: {observation}")
            self._log(f"│ 📊 tokens:   in={usage[0]} out={usage[1]}")
            self._log("╰──────────────────────────────────────────────")
            transcript += f"Observation: {observation}\n"

        self._log_totals()
        return "Não foi possível concluir dentro do limite de passos."

    def _call_model(self, transcript: str) -> tuple[str, tuple[int, int]]:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            stop_sequences=["Observation:"],
            messages=[{"role": "user", "content": transcript}],
        )
        text = "".join(
            b.text for b in response.content if b.type == "text"
        ).strip()
        usage = (response.usage.input_tokens, response.usage.output_tokens)
        self.total_input_tokens += usage[0]
        self.total_output_tokens += usage[1]
        return text, usage

    def _run_tool(self, name: str, raw_args: str) -> str:
        tool = self.tools.get(name)
        if tool is None:
            return f"tool '{name}' não existe."
        try:
            args = self._parse_args(raw_args)
            return str(tool(**args))
        except Exception as exc:  # noqa: BLE001
            return f"erro ao executar {name}: {exc}"

    @staticmethod
    def _parse_args(raw: str) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {"expression": parsed}
        except json.JSONDecodeError:
            return {"expression": raw.strip().strip('"').strip("'")}

    @staticmethod
    def _extract(pattern: re.Pattern[str], text: str) -> str | None:
        match = pattern.search(text)
        return match.group(1) if match else None

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
    agent = ReActAgent()
    print(f"[pergunta] {question}")
    final = agent.chat(question)
    print(f"\n=== resposta final ===\n{final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

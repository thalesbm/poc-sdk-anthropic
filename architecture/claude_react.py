#!/usr/bin/env python3
"""
Exemplo simples do fluxo ReAct (Reasoning + Acting).

Este script simula, de forma didática, como um agente ReAct funciona:
    1. O modelo gera um "Thought" (raciocínio em texto livre).
    2. O modelo gera uma "Action" (chamada de ferramenta em texto,
       no formato Action: nome_da_tool[argumento]).
    3. O agente faz o PARSING desse texto com regex para extrair
       o nome da ferramenta e o argumento.
    4. O agente EXECUTA a ferramenta de verdade (fora do modelo).
    5. O resultado vira uma "Observation", que é concatenada ao
       histórico de texto e reenviada ao modelo na próxima chamada.
    6. O loop se repete até o modelo gerar "Action: Finish[...]".

Aqui o "modelo" é simulado por uma função Python (fake_llm) que
segue um roteiro fixo, só para deixar visível a mecânica do loop
sem precisar de uma chamada real de API.
"""

import os
import re
from typing import Callable, Dict

from anthropic import Anthropic
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

_client = Anthropic()
_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

SYSTEM_PROMPT = """Você é um agente que segue ESTRITAMENTE a arquitetura ReAct.

Ferramentas disponíveis:
- Search[query]  -> busca uma informação e retorna texto.
- Finish[resposta] -> encerra e devolve a resposta final ao usuário.

Formato OBRIGATÓRIO por passo (cada label em UMA linha, nesta ordem):
Thought: <seu raciocínio em uma linha>
Action: <NomeDaTool>[<argumento em texto livre, sem aspas>]

Após emitir "Action:", PARE. O runtime devolverá:
Observation: <resultado da tool>

Repita Thought/Action/Observation quantas vezes precisar. Quando tiver a
resposta, use Action: Finish[<resposta>].

Regras:
- Sempre em português do Brasil.
- Use colchetes [ ] no argumento (não parênteses).
- Nunca invente Observations — espere o runtime devolver.
"""


# ---------------------------------------------------------------------------
# 1. Ferramentas disponíveis para o agente
# ---------------------------------------------------------------------------

def search_tool(query: str) -> str:
    """
    Simula uma ferramenta de busca.

    Em um agente real, isso chamaria uma API de busca de verdade.
    Aqui, devolvemos uma resposta fixa só para ilustrar o fluxo.
    """
    fake_knowledge_base = {
        "população da islândia": "A população da Islândia é de aproximadamente 380 mil habitantes.",
        "capital da islândia": "A capital da Islândia é Reykjavík.",
    }
    return fake_knowledge_base.get(
        query.strip().lower(),
        f"Nenhum resultado encontrado para '{query}'.",
    )


# Registro de ferramentas: nome (como aparece no texto) -> função Python real
TOOLS: Dict[str, Callable[[str], str]] = {
    "Search": search_tool,
}


# ---------------------------------------------------------------------------
# 2. "Modelo" simulado
# ---------------------------------------------------------------------------

def call_llm(prompt: str, step: int) -> str:
    """
    Faz a chamada real à Anthropic API para gerar um passo do ReAct.

    - `system` ensina o formato Thought/Action[...] e as tools disponíveis.
    - `stop_sequences=["Observation:"]` força o modelo a parar assim que
      terminar a Action, evitando que ele invente a própria Observation.
    - O `prompt` é o histórico acumulado (Question + Thought/Action/Observation
      anteriores) — LLMs não têm memória entre chamadas, então mandamos tudo.
    """
    response = _client.messages.create(
        model=_MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        stop_sequences=["Observation:"],
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()


# ---------------------------------------------------------------------------
# 3. Parsing do texto gerado (Thought + Action)
# ---------------------------------------------------------------------------

# Regex que captura:
#   - o texto do Thought (tudo entre "Thought:" e a linha "Action:")
#   - o nome da ferramenta chamada na Action (ex.: Search, Finish)
#   - o argumento entre colchetes (ex.: população da Islândia)
THOUGHT_ACTION_PATTERN = re.compile(
    r"Thought:\s*(?P<thought>.*?)\s*\n"
    r"Action:\s*(?P<tool>\w+)\[(?P<arg>.*?)\]",
    re.DOTALL,
)


def parse_model_output(text: str):
    """
    Extrai (thought, tool_name, tool_arg) do texto gerado pelo modelo.

    Isso ilustra o ponto frágil do ReAct: se o modelo fugir do
    formato esperado (colchetes errados, "Ação:" em vez de "Action:",
    etc.), esse regex simplesmente não encontra match e o loop quebra.
    """
    match = THOUGHT_ACTION_PATTERN.search(text)
    if not match:
        raise ValueError(f"Não foi possível fazer o parsing da saída do modelo:\n{text}")
    return match.group("thought"), match.group("tool"), match.group("arg")


# ---------------------------------------------------------------------------
# 4. O loop ReAct em si
# ---------------------------------------------------------------------------

def run_react_agent(question: str, max_steps: int = 5) -> str:
    """
    Executa o loop ReAct: Thought -> Action -> Observation -> repete.

    O prompt cresce a cada iteração porque o histórico completo de
    Thought/Action/Observation é reenviado ao modelo a cada passo
    (LLMs não têm memória entre chamadas).
    """
    # Prompt inicial: só a pergunta do usuário.
    # Em um agente real, aqui também entrariam os exemplos few-shot
    # que ensinam o modelo a seguir o formato Thought/Action/Observation.
    history = f"Question: {question}\n"

    for step in range(1, max_steps + 1):
        print(f"\n--- Passo {step} ---")
        print("Prompt enviado ao modelo (histórico acumulado):")
        print(history)

        # 1) O "modelo" gera Thought + Action como texto livre
        model_output = call_llm(history, step)
        print("Saída do modelo:")
        print(model_output)

        # 2) Parsing manual do texto para extrair a ação
        thought, tool_name, tool_arg = parse_model_output(model_output)

        print(f"\nRaciocínio final: {thought}")
        print(f"\nFerramenta chamada: {tool_name}")
        print(f"\nArgumento da ferramenta: {tool_arg}")

        # 3) Caso especial: Finish encerra o loop sem chamar ferramenta real
        if tool_name == "Finish":
            print(f"\nRaciocínio final: {thought}")
            return tool_arg

        # 4) Executa a ferramenta de verdade, fora do modelo
        if tool_name not in TOOLS:
            raise ValueError(f"Ferramenta desconhecida: {tool_name}")
        observation = TOOLS[tool_name](tool_arg)

        # 5) A Observation é concatenada como texto ao histórico,
        #    para ser reenviada ao modelo no próximo passo
        history += f"{model_output}\nObservation: {observation}\n"

    raise RuntimeError("Número máximo de passos atingido sem uma resposta final.")


# ---------------------------------------------------------------------------
# 5. Execução de exemplo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    resposta = run_react_agent("Qual é a população da Islândia?")
    print(f"\n=== Resposta final ===\n{resposta}")
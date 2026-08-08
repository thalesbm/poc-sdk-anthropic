#!/usr/bin/env python3
"""
Exemplo simples do agent loop com tool calling ESTRUTURADO.

Este script simula, de forma didática, como um agente moderno
(estilo Anthropic/OpenAI tool use) funciona:

    1. O agente monta uma lista de mensagens (histórico) + um
       schema JSON descrevendo as ferramentas disponíveis.
    2. O "modelo" retorna um objeto estruturado: ou texto final,
       ou um bloco tool_use com nome da função e argumentos já
       tipados (nada de parsear string com regex).
    3. O agente executa a função Python correspondente de verdade.
    4. O resultado vira uma mensagem de "tool_result", anexada ao
       histórico como uma mensagem própria (não como texto solto).
    5. O loop se repete até o modelo responder sem nenhum tool_call
       -- ou seja, quando ele decide que já tem a resposta final.

Aqui o "modelo" é simulado por uma função Python (fake_llm) que
segue um roteiro fixo, só para deixar visível a mecânica do loop
sem precisar de uma chamada real de API.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from anthropic import Anthropic
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

_client = Anthropic()
_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

SYSTEM_PROMPT = """Você é um assistente objetivo que responde em português do Brasil.

Uso das ferramentas:
- Sempre que a pergunta pedir um fato específico, use `search` em vez
  de responder de memória.
- Se `search` retornar "Nenhum resultado encontrado", diga isso ao
  usuário — não invente.
- Quando tiver a resposta, responda direto, sem preâmbulo.
"""


# ---------------------------------------------------------------------------
# 1. Ferramentas disponíveis, descritas como schema (não como texto de exemplo)
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


# Registro de ferramentas: nome (como aparece no schema) -> função Python real
TOOLS: Dict[str, Callable[..., str]] = {
    "search": search_tool,
}

# Schema JSON das ferramentas, enviado à API junto com as mensagens.
# É isso que permite ao modelo gerar argumentos já tipados e validados,
# em vez de aprender o formato só por exemplos de texto (como no ReAct).
TOOL_SCHEMAS = [
    {
        "name": "search",
        "description": "Busca uma informação factual em uma base de conhecimento.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "O termo a ser buscado."}
            },
            "required": ["query"],
        },
    }
]


# ---------------------------------------------------------------------------
# 2. Estruturas de dados que representam a resposta do modelo
# ---------------------------------------------------------------------------

@dataclass
class ToolCall:
    """Representa uma chamada de ferramenta já estruturada e tipada."""
    id: str
    name: str
    input: Dict[str, Any]


@dataclass
class ModelResponse:
    """
    Representa a resposta do modelo em uma chamada de API real.

    text: texto final da resposta (pode vir vazio se o modelo só chamou ferramenta)
    tool_calls: lista de chamadas estruturadas (vazia quando o modelo já terminou)
    """
    text: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 3. "Modelo" simulado
# ---------------------------------------------------------------------------

def call_llm(messages: List[dict], step: int) -> ModelResponse:
    """
    Faz a chamada real à Anthropic API usando tool calling nativo.

    A API já devolve blocos estruturados:
        - block.type == "text"      -> parte textual da resposta
        - block.type == "tool_use"  -> chamada de ferramenta com args tipados

    Nenhum parsing manual é necessário — os argumentos chegam validados
    pelo `input_schema` declarado em TOOL_SCHEMAS.
    """
    response = _client.messages.create(
        model=_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=TOOL_SCHEMAS,
        messages=messages,
    )

    text_parts: List[str] = []
    tool_calls: List[ToolCall] = []
    for block in response.content:
        if block.type == "text":
            text_parts.append(block.text)
        elif block.type == "tool_use":
            tool_calls.append(ToolCall(id=block.id, name=block.name, input=block.input))

    return ModelResponse(text="".join(text_parts).strip(), tool_calls=tool_calls)


# ---------------------------------------------------------------------------
# 4. O agent loop em si
# ---------------------------------------------------------------------------

def run_agent_loop(question: str, max_steps: int = 5) -> str:
    """
    Executa o agent loop: model call -> tool execution -> tool result -> repete.

    Diferente do ReAct, cada Observation aqui NÃO é texto colado ao
    prompt -- é uma mensagem própria no histórico, com role "user"
    e content_type "tool_result", vinculada ao tool_call pelo campo id.
    """
    # Histórico de mensagens, no formato usado por APIs de chat.
    # Note que isso é uma LISTA DE OBJETOS estruturados, não uma
    # string de texto crescendo como no ReAct.
    messages: List[dict] = [
        {"role": "user", "content": question}
    ]

    for step in range(1, max_steps + 1):
        print(f"\n--- Passo {step} ---")
        print("Mensagens enviadas ao modelo (histórico estruturado):")
        for m in messages:
            print(f"  {m}")

        # 1) Chama o "modelo" passando o histórico + o schema das ferramentas
        response = call_llm(messages, step)

        # 2) Sem tool_calls significa que o modelo já decidiu que terminou
        if not response.tool_calls:
            print(f"\nResposta final do modelo (sem tool_calls): {response.text}")
            return response.text

        # 3) Registra a resposta do modelo (com os tool_calls) no histórico
        messages.append({
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": tc.id, "name": tc.name, "input": tc.input}
                for tc in response.tool_calls
            ],
        })

        # 4) Executa cada ferramenta chamada, de verdade, fora do modelo
        tool_result_blocks = []
        for tc in response.tool_calls:
            print(f"Executando tool estruturada: {tc.name}(**{tc.input})")

            if tc.name not in TOOLS:
                raise ValueError(f"Ferramenta desconhecida: {tc.name}")

            # Os argumentos já chegam tipados (dict), sem precisar de regex
            result = TOOLS[tc.name](**tc.input)

            # 5) O resultado vira um bloco "tool_result" vinculado ao id da call
            tool_result_blocks.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": result,
            })

        # O resultado entra como uma mensagem própria (role "user"),
        # não como texto concatenado ao prompt
        messages.append({"role": "user", "content": tool_result_blocks})

    raise RuntimeError("Número máximo de passos atingido sem uma resposta final.")


# ---------------------------------------------------------------------------
# 5. Execução de exemplo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    resposta = run_agent_loop("Qual é a população da Islândia?")
    print(f"\n=== Resposta final ===\n{resposta}")
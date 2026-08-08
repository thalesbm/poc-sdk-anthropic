# architecture/

Exemplos didáticos de arquiteturas de agentes de IA — cada arquivo é
auto-contido e focado em **uma única classe**, para deixar o padrão evidente.

## 1. ReAct textual (`react_agent.py`) — didático

Agente que segue **Reason → Act → Observe** usando prompting puro
(Yao et al., 2022 — https://arxiv.org/abs/2210.03629):

- O modelo emite `Thought: ...` (raciocínio verbalizado) e `Action: tool(args)`.
- `stop_sequences=["Observation:"]` para o modelo; a classe executa a tool.
- O resultado volta como `Observation: ...` no próximo turno.
- Termina em `Final Answer: ...`.

**Quando usar:** prototipagem rápida, depuração (você lê o `Thought:`),
modelos sem tool calling nativo forte.

```bash
python react_agent.py "quanto é (23*7) + 10? e que horas são?"
```

## 2. Agent Loop com tools nativas (`agent_loop.py`) — produção

Mesmo esqueleto (`while not done: model → tools → observe`), mas usando a
**Tools API nativa** da Anthropic:

- O modelo devolve blocos `tool_use` com JSON validado por `input_schema`.
- A classe executa todos os `tool_use` do turno (pode ser em paralelo) e
  devolve `tool_result` na mensagem seguinte.
- Termina quando `stop_reason == "end_turn"`.

**Quando usar:** produção. Menos tokens (sem `Thought:` obrigatório), args
validados por JSON Schema, paralelismo de tools, resposta mais robusta.

```bash
python agent_loop.py "some 12+30 e me diga que horas são"
```

## Diferenças em uma tabela

|                      | ReAct textual              | Agent Loop (tools nat.)   |
|----------------------|----------------------------|---------------------------|
| Formato da ação      | `Action: foo(...)`         | `tool_use` block + JSON   |
| Validação de args    | regex/parsing manual       | JSON Schema da API        |
| Paralelismo          | 1 ação por turno           | N `tool_use` por turno    |
| Tokens de raciocínio | altos (`Thought:`)         | baixos (opcional)         |
| Robustez             | frágil (formato textual)   | alta (contrato tipado)    |
| Debug                | ótimo (texto legível)      | requer inspeção estrutur. |

## Setup

```bash
pip install -r requirements.txt
```

Requer `ANTHROPIC_API_KEY` no `.env` da raiz do repo (já carregado via
`find_dotenv()` — pode rodar de qualquer subpasta).

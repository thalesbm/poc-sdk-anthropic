# Assistente com Claude Agent SDK

Assistente financeiro em Python usando o [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview). As tools disponíveis para o modelo são **descobertas dinamicamente** a partir da API HTTP do [`../mcp-server`](../mcp-server) (`GET /tools`), e cada invocação é proxyada via `POST /tools/{name}/invoke`.

## Requisitos

- Python 3.10+
- Node.js 18+ (o SDK embute o binário do Claude Code CLI)
- `ANTHROPIC_API_KEY` — [crie aqui](https://platform.claude.com/)
- API do `mcp-server` rodando (default: `http://localhost:8000`)

## Setup

```bash
# 1) suba a API do mcp-server (em outro terminal)
cd ../mcp-server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python api.py

# 2) agente
cd ../agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edite .env e cole sua chave
```

Variáveis de ambiente opcionais:

- `MCP_API_BASE_URL` — URL base da API (default `http://localhost:8000`)
- `MCP_API_TIMEOUT` — timeout HTTP em segundos (default `10`)

## Uso

```bash
python app/agent.py
```

O boot faz um `GET /tools` na API e monta um MCP server in-process com uma tool proxy para cada tool remota. Digite `sair` (ou `Ctrl+D`) para encerrar.

## Estrutura

```
.
├── app/
│   ├── agent.py             # loop de chat interativo
│   ├── mcp_servers.py       # discovery + tools-proxy HTTP → API do mcp-server
│   └── prompt.py            # SYSTEM_PROMPT
├── requirements.txt
├── .env.example
└── README.md
```

## Como adicionar uma tool nova

Basta adicionar a tool em `../mcp-server/tools.py` (com seu `ToolSpec`). Reinicie o agente e ela aparece automaticamente via discovery — **não é necessário mexer no código do agente**.

## Notas

- Nenhuma ferramenta nativa (Read/Edit/Bash) é liberada — só as descobertas dinamicamente.
- Todos os dados retornados são mockados.
- Custo por turno é impresso via `ResultMessage.total_cost_usd`.

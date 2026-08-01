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
python main.py

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
│   ├── prompt.py            # SYSTEM_PROMPT
│   └── mcp_client/          # camada cliente MCP → API do mcp-server
│       ├── __init__.py      # fachada (build_assistant_server, ALLOWED_TOOLS, SERVER_NAME)
│       ├── config.py        # MCP_API_BASE_URL, HTTP_TIMEOUT, SERVER_NAME
│       ├── discovery.py     # GET /tools
│       ├── invoker.py       # POST /tools/{name}/invoke
│       └── server.py        # monta o sdk_mcp_server com tools-proxy
├── requirements.txt
├── .env.example
└── README.md
```

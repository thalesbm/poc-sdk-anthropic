# Assistente com Claude Agent SDK

Projeto mínimo em Python usando o [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview) da Anthropic. Um assistente pessoal com duas ferramentas customizadas (`calculator` e um bloco de notas em memória) expostas ao modelo via um servidor MCP in-process.

## Requisitos

- Python 3.10+ (o projeto foi testado em 3.12)
- Node.js 18+ (o SDK embute o binário do Claude Code CLI e o executa como subprocesso)
- Uma `ANTHROPIC_API_KEY` — [crie aqui](https://platform.claude.com/)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edite .env e cole sua chave
```

## Uso

Chat interativo (usa `ClaudeSDKClient` — mantém contexto entre as perguntas):

```bash
python app/agent.py
```

Digite `sair` (ou `Ctrl+D`) para encerrar. Rode a partir da raiz do projeto — o `.env` é lido do diretório atual.

## Estrutura

```
.
├── app/
│   ├── agent.py             # loop de chat interativo
│   ├── mcp_servers.py       # build_assistant_server + ALLOWED_TOOLS
│   ├── prompt.py            # SYSTEM_PROMPT do assistente
│   ├── _state.py            # estado compartilhado (bloco de notas em memória)
│   └── tools/
│       ├── __init__.py      # vazio (marcador de pacote)
│       ├── calculator.py    # @tool calculator
│       ├── add_note.py      # @tool add_note
│       └── list_notes.py    # @tool list_notes
├── requirements.txt
├── .env.example
└── README.md
```

Cada `@tool` fica em seu próprio arquivo dentro de `app/tools/`. Para adicionar uma nova ferramenta, crie `app/tools/minha_tool.py` e registre-a em `app/mcp_servers.py` (adicione ao `create_sdk_mcp_server(tools=[...])` e ao `ALLOWED_TOOLS`).

## O que o projeto demonstra

1. **`ClaudeSDKClient`** — sessão persistente para conversas multi-turno.
2. **`@tool` + `create_sdk_mcp_server`** — expõe funções Python como ferramentas MCP sem processo externo.
3. **`ClaudeAgentOptions`** — configura `system_prompt`, `mcp_servers`, `allowed_tools` e `permission_mode`.

## Notas

- Nenhuma ferramenta nativa (Read/Edit/Bash) é liberada — apenas as três ferramentas MCP definidas em `app/tools/`. Para expandir, adicione-as em `allowed_tools`.
- O bloco de notas vive em memória; se você reiniciar o processo, elas somem. Para persistir, troque `NOTES` em `app/_state.py` por leitura/escrita em arquivo.
- Custo aproximado por turno é impresso ao fim (`ResultMessage.total_cost_usd`).

# poc-sdk-anthropic

POC de um assistente financeiro em Python usando o [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview), consumindo ferramentas expostas por um MCP server local via **HTTP API**.

O repositório tem duas partes independentes:

- **`mcp-server/`** — serviço FastAPI com tools bancárias mockadas (saldo, fatura, investimentos, chaves PIX). Cada tool é um arquivo em `app/tools/`; o registro é automático.
- **`agent/`** — assistente Claude que, no boot, faz discovery na API e monta as tools MCP dinamicamente. Também injeta o catálogo descoberto no system prompt.

Todos os dados retornados são **mockados** — nada chama sistemas reais.

## Arquitetura

```
┌────────────────┐   HTTP    ┌───────────────────────┐
│   agent/       │──────────▶│   mcp-server/         │
│  (Claude SDK)  │  GET /tools│  FastAPI + tools/    │
│                │  POST /invoke                     │
└────────────────┘           └───────────────────────┘
        ▲
        │ chat
        ▼
      usuário
```

O agente **nunca fala com o mcp-server fora da API HTTP**. As tools ficam em processos separados.

## Requisitos

- Python 3.10+
- Node.js 18+ (o Claude Agent SDK embute o binário do Claude Code CLI)
- Uma `ANTHROPIC_API_KEY` — crie em <https://console.anthropic.com/settings/keys> (precisa de crédito na conta)

## Setup

Cada componente tem sua própria venv.

### 1) mcp-server (terminal 1)

```bash
cd mcp-server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Sobe em `http://localhost:8000`. Swagger UI em <http://localhost:8000/docs>.

### 2) agent (terminal 2)

```bash
cd agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edite .env e cole sua chave ANTHROPIC_API_KEY

python app/agent.py
```

Ao iniciar, o agente imprime as tools descobertas na API. Digite `sair` (ou `Ctrl+D`) para encerrar.

Variáveis de ambiente opcionais no agente:

- `MCP_API_BASE_URL` — default `http://localhost:8000`
- `MCP_API_TIMEOUT` — default `10` (segundos)

## Estrutura

```
.
├── mcp-server/
│   ├── main.py                                 # entrypoint (uvicorn.run)
│   ├── app/
│   │   ├── api.py                              # FastAPI + rotas
│   │   ├── registry.py                         # auto-discovery de tools (varre app/tools/*)
│   │   └── tools/
│   │       ├── __init__.py                     # vazio
│   │       ├── _spec.py                        # dataclass ToolSpec
│   │       ├── buscar_saldo.py                 # handler + SPEC
│   │       ├── buscar_fatura.py
│   │       ├── buscar_total_investimentos.py
│   │       └── listar_chaves_pix.py
│   └── requirements.txt                        # fastapi, uvicorn, pydantic
│
├── agent/
│   ├── app/
│   │   ├── agent.py                            # loop de chat interativo
│   │   ├── prompt.py                           # build_system_prompt(discovered_tools)
│   │   └── mcp_client/                         # camada cliente MCP → API do mcp-server
│   │       ├── __init__.py                     # fachada pública
│   │       ├── config.py                       # MCP_API_BASE_URL, HTTP_TIMEOUT, SERVER_NAME
│   │       ├── discovery.py                    # GET /tools
│   │       ├── invoker.py                      # POST /tools/{name}/invoke
│   │       └── server.py                       # monta sdk_mcp_server com tools-proxy
│   ├── requirements.txt                        # claude-agent-sdk, httpx, python-dotenv
│   └── .env.example
│
├── .gitignore
└── README.md
```

## mcp-server — HTTP API

### Ferramentas atuais

| Tool | Descrição | Args (todos opcionais) |
|------|-----------|------------------------|
| `buscar_saldo` | Saldo disponível/bloqueado de uma conta. | `conta: str` |
| `buscar_fatura` | Valor total, mínimo, vencimento e status da fatura do cartão. | `cartao_final: str` |
| `buscar_total_investimentos` | Total investido + distribuição por classe de ativo. | `cliente_id: str` |
| `listar_chaves_pix` | Lista as chaves PIX do cliente (filtro por tipo opcional). | `cliente_id: str`, `tipo: cpf\|email\|celular\|aleatoria` |

### Endpoints

| Método | Rota                      | Descrição                                      |
|--------|---------------------------|------------------------------------------------|
| GET    | `/health`                 | status simples (`{"status":"ok"}`)             |
| GET    | `/tools`                  | **discovery** — lista tools com `input_schema` |
| GET    | `/tools/{name}`           | metadata de uma tool específica                |
| POST   | `/tools/{name}/invoke`    | executa a tool com `{"arguments": {...}}`      |

### Formatos

`GET /tools`:

```json
{
  "tools": [
    {
      "name": "buscar_saldo",
      "description": "Retorna o saldo atual mockado de uma conta.",
      "input_schema": {
        "type": "object",
        "properties": { "conta": { "type": "string", "default": "00012345-6" } },
        "required": []
      }
    }
  ]
}
```

`POST /tools/{name}/invoke`:

```jsonc
// request
{ "arguments": { "conta": "99988877-6" } }

// response
{
  "tool": "buscar_saldo",
  "result": { "conta": "99988877-6", "moeda": "BRL", "saldo_disponivel": 5234.87, "...": "..." }
}
```

Erros: `404` (tool inexistente), `400` (arg desconhecido), `500` (exceção no handler).

### Exemplos com curl

```bash
curl -s http://localhost:8000/health | jq
curl -s http://localhost:8000/tools | jq

curl -s -X POST http://localhost:8000/tools/buscar_saldo/invoke \
  -H 'content-type: application/json' \
  -d '{"arguments": {"conta": "99988877-6"}}' | jq

curl -s -X POST http://localhost:8000/tools/listar_chaves_pix/invoke \
  -H 'content-type: application/json' \
  -d '{"arguments": {"tipo": "email"}}' | jq
```

### Adicionar uma tool nova

1. Crie `mcp-server/app/tools/minha_tool.py`:

   ```python
   from datetime import date
   from ._spec import ToolSpec


   def minha_tool(param: str = "default") -> dict:
       return {"param": param, "consultado_em": date.today().isoformat()}


   SPEC = ToolSpec(
       name="minha_tool",
       description="O que a tool faz, em uma frase.",
       handler=minha_tool,
       input_schema={
           "type": "object",
           "properties": {
               "param": {"type": "string", "default": "default"}
           },
           "required": [],
       },
   )
   ```

2. Reinicie o mcp-server. A tool aparece em `GET /tools` automaticamente (o `registry.py` varre a pasta). Módulos que começam com `_` são ignorados.

3. Reinicie o agente. Ele descobre a nova tool e injeta no system prompt — **sem tocar em código do agente**.

## agent — fluxo

1. **Boot**: `mcp_client/discovery.py` faz `GET /tools`.
2. Cada tool remota vira uma tool MCP local (`claude_agent_sdk.tool`) cujo handler é `mcp_client/invoker.py` (`POST /tools/{name}/invoke`).
3. `prompt.py` recebe o catálogo descoberto e monta o system prompt final com a lista de tools + schemas.
4. Um `ClaudeSDKClient` roda um loop de chat mantendo a sessão. O custo por turno é impresso via `ResultMessage.total_cost_usd`.

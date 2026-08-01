# MCP Server - Banco Mock (HTTP API)

Servidor com 3 ferramentas bancárias **mockadas**, exposto via **HTTP API**. É o único transporte suportado — o agente em `../agent` consome essa API.

Handlers em `tools.py`; API REST em `api.py`.

## Ferramentas

| Tool | Descrição |
|------|-----------|
| `buscar_saldo` | Retorna saldo disponível/bloqueado de uma conta. |
| `buscar_fatura` | Retorna valor total, mínimo e vencimento da fatura do cartão. |
| `buscar_total_investimentos` | Retorna o total investido e a distribuição por classe de ativo. |

## Instalação

```bash
cd mcp-server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Rodar

A partir de `mcp-server/`:

```bash
python -m app.api
# ou:
uvicorn app.api:app --reload --port 8000
```

Swagger UI em <http://localhost:8000/docs>.

## Endpoints

| Método | Rota                       | Descrição                                        |
|--------|----------------------------|--------------------------------------------------|
| GET    | `/health`                  | status                                           |
| GET    | `/tools`                   | **discovery** — lista tools com `input_schema`   |
| GET    | `/tools/{name}`            | metadata de uma tool específica                  |
| POST   | `/tools/{name}/invoke`     | executa a tool com `{"arguments": {...}}`        |

## Exemplos

```bash
curl -s http://localhost:8000/tools | jq

curl -s -X POST http://localhost:8000/tools/buscar_saldo/invoke \
  -H 'content-type: application/json' \
  -d '{"arguments": {"conta": "99988877-6"}}' | jq

curl -s -X POST http://localhost:8000/tools/buscar_fatura/invoke \
  -H 'content-type: application/json' \
  -d '{"arguments": {}}' | jq
```

Resposta do `invoke`:

```json
{
  "tool": "buscar_saldo",
  "result": { "conta": "...", "moeda": "BRL", "saldo_disponivel": 5234.87, ... }
}
```

## Estrutura

```
mcp-server/
├── app/
│   ├── __init__.py
│   ├── api.py                          # API HTTP (FastAPI)
│   └── tools/
│       ├── __init__.py                 # registro central (TOOLS, TOOLS_BY_NAME)
│       ├── _spec.py                    # dataclass ToolSpec
│       ├── buscar_saldo.py             # handler + SPEC
│       ├── buscar_fatura.py            # handler + SPEC
│       └── buscar_total_investimentos.py
├── requirements.txt
└── README.md
```

Para adicionar uma tool: crie `app/tools/minha_tool.py` com `def minha_tool(...)` e um `SPEC = ToolSpec(...)`; depois importe e adicione o `SPEC` na lista `TOOLS` em `app/tools/__init__.py`. A API a expõe automaticamente e o agente a descobre no próximo boot.

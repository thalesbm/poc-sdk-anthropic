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
python main.py
# ou:
python -m app.api
# ou (com reload):
uvicorn app.api:app --reload --port 8000
```

> `python app/api.py` **não funciona** — o Python não trata `app/` como pacote e os imports relativos quebram. Use uma das formas acima.

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
├── main.py                             # entrypoint (`python main.py`)
├── app/
│   ├── __init__.py
│   ├── api.py                          # API HTTP (FastAPI)
│   ├── registry.py                     # auto-discovery de tools (varre app/tools/*)
│   └── tools/
│       ├── __init__.py                 # vazio (só marca o pacote)
│       ├── _spec.py                    # dataclass ToolSpec
│       ├── buscar_saldo.py             # handler + SPEC
│       ├── buscar_fatura.py            # handler + SPEC
│       ├── buscar_total_investimentos.py
│       └── listar_chaves_pix.py
├── requirements.txt
└── README.md
```

Para adicionar uma tool: crie `app/tools/minha_tool.py` com `def minha_tool(...)` e um `SPEC = ToolSpec(...)`. Só isso — `app/registry.py` varre a pasta automaticamente e a nova tool aparece na API. Módulos que começam com `_` (ex.: `_spec.py`) são ignorados.

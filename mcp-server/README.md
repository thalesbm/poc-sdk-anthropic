# MCP Server - Banco Mock (HTTP API)

Servidor Python com ferramentas bancárias **mockadas**, exposto via **HTTP API** (FastAPI). É o único transporte suportado — o agente em [`../agent`](../agent) consome essa API através dos endpoints de discovery e invocação.

Cada tool vive em seu próprio arquivo dentro de `app/tools/` e é **descoberta automaticamente** por `app/registry.py` — não há registro manual.

## Ferramentas atuais

| Tool | Descrição | Args (todos opcionais) |
|------|-----------|------------------------|
| `buscar_saldo` | Saldo disponível/bloqueado de uma conta. | `conta: str` |
| `buscar_fatura` | Valor total, mínimo, vencimento e status da fatura do cartão. | `cartao_final: str` |
| `buscar_total_investimentos` | Total investido + distribuição por classe de ativo. | `cliente_id: str` |
| `listar_chaves_pix` | Lista as chaves PIX do cliente (filtro por tipo opcional). | `cliente_id: str`, `tipo: cpf\|email\|celular\|aleatoria` |

Todos os retornos são estáticos/mockados — nada chama sistemas reais.

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
# ou (com reload em dev):
uvicorn app.api:app --reload --port 8000
```

> `python app/api.py` **não funciona** — nesse modo o Python não trata `app/` como pacote e os imports relativos quebram. Use uma das formas acima.

Servidor sobe em `http://0.0.0.0:8000`. Docs interativas (Swagger UI) em <http://localhost:8000/docs>.

Se a porta 8000 já estiver ocupada:

```bash
lsof -ti:8000 | xargs kill -9
```

## Endpoints

| Método | Rota                      | Descrição                                      |
|--------|---------------------------|------------------------------------------------|
| GET    | `/health`                 | status simples (`{"status":"ok"}`)             |
| GET    | `/tools`                  | **discovery** — lista tools com `input_schema` |
| GET    | `/tools/{name}`           | metadata de uma tool específica                |
| POST   | `/tools/{name}/invoke`    | executa a tool com `{"arguments": {...}}`      |

### Formato do `/tools`

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

### Formato do `/invoke`

Request:

```json
{ "arguments": { "conta": "99988877-6" } }
```

Response:

```json
{
  "tool": "buscar_saldo",
  "result": { "conta": "99988877-6", "moeda": "BRL", "saldo_disponivel": 5234.87, "...": "..." }
}
```

Erros:

- `404` — tool inexistente
- `400` — argumento desconhecido para a tool
- `500` — exceção interna no handler

## Exemplos com curl

```bash
curl -s http://localhost:8000/health | jq
curl -s http://localhost:8000/tools | jq

curl -s -X POST http://localhost:8000/tools/buscar_saldo/invoke \
  -H 'content-type: application/json' \
  -d '{"arguments": {"conta": "99988877-6"}}' | jq

curl -s -X POST http://localhost:8000/tools/buscar_fatura/invoke \
  -H 'content-type: application/json' \
  -d '{"arguments": {}}' | jq

curl -s -X POST http://localhost:8000/tools/buscar_total_investimentos/invoke \
  -H 'content-type: application/json' \
  -d '{"arguments": {"cliente_id": "cli-42"}}' | jq

curl -s -X POST http://localhost:8000/tools/listar_chaves_pix/invoke \
  -H 'content-type: application/json' \
  -d '{"arguments": {"tipo": "email"}}' | jq
```

## Estrutura

```
mcp-server/
├── main.py                             # entrypoint (uvicorn.run)
├── app/
│   ├── __init__.py
│   ├── api.py                          # FastAPI + rotas
│   ├── registry.py                     # auto-discovery de tools
│   └── tools/
│       ├── __init__.py                 # vazio (só marca o pacote)
│       ├── _spec.py                    # dataclass ToolSpec
│       ├── buscar_saldo.py             # handler + SPEC
│       ├── buscar_fatura.py            # handler + SPEC
│       ├── buscar_total_investimentos.py
│       └── listar_chaves_pix.py
├── requirements.txt                    # fastapi, uvicorn, pydantic
├── .gitignore
└── README.md
```

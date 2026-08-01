# chat

UI web completa: frontend HTML + backend REST. Backend faz o papel de orquestrador (descobre agentes A2A, escolhe qual chamar via LLM).

```
chat/
├── frontend/          servidor estático + index.html
│   ├── index.html
│   └── serve.py       (http.server da stdlib, zero deps)
└── backend/           FastAPI + ClaudeSDKClient
    ├── main.py        entrypoint uvicorn
    ├── requirements.txt
    └── app/
        ├── api.py     rotas REST + sessão
        ├── registry.py    descoberta A2A
        ├── a2a_tools.py   AgentCard → tools MCP
        └── prompt.py      system prompt do roteador
```

## Rodar

Duas coisas em terminais separados:

```bash
# 1) backend (porta 8400) — usa .env da raiz do repo
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py

# 2) frontend (porta 3000)
cd ../frontend
python serve.py              # sem venv, sem deps
```

Abra <http://localhost:3000>.

## Contrato REST

| Método | Rota | Payload | Resposta |
|---|---|---|---|
| GET  | `/api/agents` | — | `[{slug, name, description, url}]` |
| POST | `/api/chat`   | `{"message": "..."}` | `{"reply": "...", "cost_usd": 0.03}` |
| POST | `/api/reset`  | — | `{"status": "ok"}` |

## Configurar URL da API no frontend

Ordem de prioridade:

1. Query string: `?api=http://outro-host:8400`
2. `window.ORCHESTRATOR_API` (defina antes do `<script>` inline)
3. Default `http://localhost:8400`

## CORS

O backend libera `*` por padrão. Restrinja com:

```bash
CORS_ALLOW_ORIGINS=http://meudominio.com,http://localhost:3000
```

## Sessão

Instância única de `ClaudeSDKClient` em memória (POC single-user). Contexto multi-turn preservado. `POST /api/reset` recria o client (novo contexto). Reiniciar o processo tem o mesmo efeito.

## Depende de

- `../a2a-common` — protocolo A2A (instalado editável)
- Agentes especialistas A2A rodando nos endpoints declarados em `A2A_AGENT_URLS`
- MCP-server rodando (transitivamente, via especialistas)

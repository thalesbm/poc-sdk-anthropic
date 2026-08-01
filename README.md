# poc-sdk-anthropic

POC de um sistema multi-agente com **1 orquestrador + 3 especialistas** (ReAct, Workflow, RAG) conectados via **A2A** (Google Agent2Agent, JSON-RPC 2.0). Cada especialista usa o Claude Agent SDK internamente e consome suas próprias tools **MCP** (HTTP) de um servidor central mockado.

## Arquitetura

```
   ┌────────────────────┐         ┌───────────────────────────┐
   │ chat/frontend      │ ──REST─▶│ chat/backend              │
   │ :3000 (HTML)       │ ◀──────│ :8400 (FastAPI)           │
   └────────────────────┘         │ Claude SDK + A2A client   │
                                  └────┬──────────┬───────────┘
                                       │          │
                   ┌───────────────────┼──────────┼────────────────────┐
                   │ A2A               │ A2A      │ A2A                │
                   ▼                   ▼          ▼                    ▼
            ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
            │ agent-react    │ │ agent-workflow │ │ agent-rag      │
            │ :8100          │ │ :8200 (HITL)   │ │ :8300          │
            │ ReAct puro     │ │ can_use_tool + │ │ retriever +    │
            │                │ │ input-required │ │ citation       │
            └───────┬────────┘ └───────┬────────┘ └───────┬────────┘
                    │ HTTP             │ HTTP             │ HTTP
                    └────────────┬─────┴──────────┬───────┘
                                 ▼                ▼
                         ┌───────────────────────────┐
                         │ mcp-server (:8000)        │
                         │ 7 tools bancárias mockadas│
                         └───────────────────────────┘

  Alternativa: agent-orchestrator (CLI) usa a mesma lógica sem passar pelo web.
```

## Papéis

| Serviço | Porta | Arquitetura | Tools MCP visíveis | Diferencial |
|---------|------:|-------------|--------------------|-------------|
| `mcp-server` | 8000 | REST | — (expõe as 7) | Auto-discovery de tools |
| `agent-react` | 8100 | ReAct (loop nativo do Claude SDK) | todas as 7 | Zero fluxo hardcoded |
| `agent-workflow` | 8200 | Workflow com HITL | 3 (`simular_*`, `executar_*`, `buscar_saldo`) | `can_use_tool` bloqueia `executar_*` sem confirmação → task vai pra `input-required` |
| `agent-rag` | 8300 | RAG (retrieval + citation) | 1 (`buscar_documentos_faq`) | Prompt força busca + citação de fontes |
| `chat/backend` | 8400 | Roteador (LLM-driven) via REST | uma tool `call_<slug>` por especialista | Discovery A2A automático + sessão persistente |
| `chat/frontend` | 3000 | UI HTML estática | — | Zero deps (http.server stdlib) |
| `agent-orchestrator` | — | CLI equivalente ao backend | idem | Alternativa terminal-only |

## Requisitos

- Python 3.10+
- Node.js 18+ (Claude Agent SDK embute o CLI do Claude Code)
- `ANTHROPIC_API_KEY` — <https://console.anthropic.com/settings/keys>

## Setup

Cada serviço tem sua venv independente. `a2a-common` é instalado editável (`pip install -e ../a2a-common`).

**Um único `.env` na raiz do repo** é lido por todos os serviços via `find_dotenv()` (sobe a árvore até achar). Comece por:

```bash
cp .env.example .env    # preencha ANTHROPIC_API_KEY
```

### T1 — mcp-server

```bash
cd mcp-server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py                       # :8000
```

### T2 — agent-react

```bash
cd agent-react
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py                       # :8100
```

### T3 — agent-workflow

```bash
cd agent-workflow
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py                       # :8200
```

### T4 — agent-rag

```bash
cd agent-rag
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py                       # :8300
```

### T5 — agent-orchestrator (CLI opcional)

Chat via terminal. Útil pra testar rápido sem UI web.

```bash
cd agent-orchestrator
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### T6 — chat/backend (API REST)

Backend do chat web. Faz o papel de orquestrador (descobre agentes A2A + roteia via LLM) e expõe REST.

```bash
cd chat/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py                       # http://localhost:8400
```

Rotas:

- `GET  /api/agents`   → agentes A2A descobertos
- `POST /api/chat`     → `{ "message": str }` → `{ "reply": str, "cost_usd": float }`
- `POST /api/reset`    → reinicia a sessão

CORS liberado (`*`) por default; restrinja com `CORS_ALLOW_ORIGINS`.

### T7 — chat/frontend (HTML estático)

```bash
cd chat/frontend
python serve.py                      # http://localhost:3000
```

Zero deps (`http.server` da stdlib). Aponta pra `http://localhost:8400` por default; override com `?api=...` na URL.

## Setup alternativo — Docker Compose

Um único stack, uma rede compartilhada, uma API key só. Boa pra rodar/debugar tudo junto sem 5 terminais.

### Subir o stack

```bash
cp .env.example .env         # coloque ANTHROPIC_API_KEY
docker compose up -d --build # mcp + 3 especialistas + chat-backend + chat-frontend
```

Portas expostas: `8000` (mcp), `8100/8200/8300` (especialistas), `8400` (chat-backend), `3000` (chat-frontend).
Abra <http://localhost:3000>.

### CLI (alternativa sem UI web)

```bash
docker compose --profile cli run --rm agent-orchestrator
```

Sobe as dependências, roda o chat CLI interativo e sai.

### Modo debug (breakpoints no Cursor/VSCode)

O override `docker-compose.debug.yml` faz três coisas:

1. Roda cada serviço dentro de `python -m debugpy --listen 0.0.0.0:<porta>`.
2. Expõe as portas de debug no host (`5678`–`5682`).
3. Monta o código-fonte como volume — edita `app/` e reinicia só o processo (`docker compose restart agent-react`), sem rebuild da imagem.

```bash
docker compose -f docker-compose.yml -f docker-compose.debug.yml up -d --build
```

No Cursor: **Run & Debug → 🐳 Attach: Todos os serviços** (compound em `.vscode/launch.json`). Ou attach individual por serviço.

| Serviço | Porta HTTP | Porta debug |
|---|---:|---:|
| `mcp-server` | 8000 | 5678 |
| `agent-react` | 8100 | 5679 |
| `agent-workflow` | 8200 | 5680 |
| `agent-rag` | 8300 | 5681 |
| `chat-backend` | 8400 | 5682 |

Sem `--wait-for-client`: o processo sobe normal e você anexa quando quiser. Se preferir "trava até o debugger conectar", adicione `--wait-for-client` no `command` do serviço.

### Derrubar

```bash
docker compose down                     # stack normal
docker compose -f docker-compose.yml -f docker-compose.debug.yml down   # stack debug
```

## Exemplos de conversa

Digite no orquestrador e ele roteia sozinho para o especialista certo (o LLM escolhe com base nos AgentCards).

```
você > qual meu saldo?
→ roteia para agent-react (banking-queries)
orquestrador > Seu saldo disponível é R$ 5.234,87.

você > qual o limite diário do pix?
→ roteia para agent-rag (faq-search)
orquestrador > O limite diário do PIX é de R$ 20.000 durante o dia e R$ 1.000 no
período noturno. Fontes: [faq-001 — Limite diário do PIX].

você > transferir 100 reais para cliente@exemplo.com
→ roteia para agent-workflow (pix-transfer)
orquestrador > Simulei a transferência: R$ 100,00 para MARIA DA SILVA (Banco Fake S.A.),
sem tarifa, liquidação hoje. Confirma?
[task fica em estado input-required]

você > sim, confirmo
orquestrador > Transferência realizada. Comprovante:
  ID: <uuid>, valor R$ 100,00, status confirmada.
```

## HITL — como o `input-required` funciona

No `agent-workflow`, o `can_use_tool` do Claude SDK bloqueia `executar_transferencia_pix` sempre que o estado do task (`_TASK_STATE[task_id]["confirmed"]`) for `False`. O estado só vira `True` quando o texto do usuário casa com o regex de confirmação (`sim|confirmo|ok|pode|aprovo|...`).

Quando `can_use_tool` retorna `deny`, o `executor` marca a flag `needs_hitl` e devolve a task com `state=INPUT_REQUIRED` para o A2A. O orquestrador recebe essa task, apresenta a resposta e o cliente responde no MESMO `task_id` na próxima interação — o `agent-workflow` recupera o histórico da task e continua o fluxo.

## Estrutura do repo

```
.
├── a2a-common/                     # lib compartilhada A2A (installed as -e)
│   └── a2a_common/
│       ├── models.py               # AgentCard, Task, Message, TaskState...
│       ├── jsonrpc.py              # envelope + códigos de erro
│       ├── server.py               # create_a2a_app(card, handler) → FastAPI
│       └── client.py               # A2AClient async
│
├── chat/                           # UI web (frontend + backend)
│   ├── frontend/
│   │   ├── index.html
│   │   └── serve.py                # http.server stdlib (:3000)
│   └── backend/                    # FastAPI + roteador A2A (:8400)
│       ├── main.py
│       └── app/
│           ├── api.py              # /api/agents, /api/chat, /api/reset
│           ├── registry.py         # discovery via A2A_AGENT_URLS
│           ├── a2a_tools.py        # cada AgentCard → tool MCP call_<slug>
│           └── prompt.py
│
├── agent-orchestrator/             # CLI equivalente ao chat/backend (opcional)
│   ├── main.py
│   └── app/{chat.py, registry.py, a2a_tools.py, prompt.py}
│
├── agent-react/                    # especialista ReAct (loop nativo)
│   └── app/{card.py, executor.py, prompt.py, server.py, mcp_client/}
│
├── agent-workflow/                 # especialista HITL
│   └── app/
│       ├── executor.py             # can_use_tool + input-required
│       └── (idem estrutura acima)
│
├── agent-rag/                      # especialista RAG
│   └── app/
│       ├── prompt.py               # força retrieval + citation
│       └── (idem)
│
├── mcp-server/                     # API HTTP com tools mockadas
│   └── app/
│       ├── api.py
│       ├── registry.py             # auto-discovery de app/tools/*
│       └── tools/
│           ├── buscar_saldo.py
│           ├── buscar_fatura.py
│           ├── buscar_total_investimentos.py
│           ├── listar_chaves_pix.py
│           ├── simular_transferencia_pix.py
│           ├── executar_transferencia_pix.py    ← sensitive (HITL)
│           └── buscar_documentos_faq.py         ← retriever RAG
│
├── examples/                       # scripts didáticos independentes
│   ├── anthropic_api.py            # SDK → Anthropic API
│   └── bedrock.py                  # SDK → Amazon Bedrock (mesmo código, provider diferente)
│
├── .gitignore
└── README.md
```

## Contrato A2A (JSON-RPC 2.0)

Cada especialista expõe:

| Método | Descrição |
|--------|-----------|
| `GET /.well-known/agent.json` | AgentCard (metadata + skills) |
| `POST /` `{"method": "message/send"}` | Envia mensagem, cria/continua Task |
| `POST /` `{"method": "tasks/get"}` | Recupera estado de uma Task |

Estados de task usados nesta POC:
- `working` — task em processamento (transitório)
- `completed` — resposta final; conversa encerrada
- `input-required` — task pausada; cliente precisa responder (HITL)
- `failed` — erro no handler

## Contrato MCP (HTTP REST — `mcp-server`)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | status |
| GET | `/tools` | discovery — lista tools com JSON Schema |
| GET | `/tools/{name}` | metadata |
| POST | `/tools/{name}/invoke` | executa a tool |

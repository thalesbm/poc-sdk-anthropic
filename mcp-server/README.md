# MCP Server - Banco Mock

Servidor MCP em Python que expõe 3 ferramentas com dados bancários mockados.

## Ferramentas

| Tool | Descrição |
|------|-----------|
| `buscar_saldo` | Retorna saldo disponível/bloqueado de uma conta. |
| `buscar_fatura` | Retorna valor total, mínimo e vencimento da fatura do cartão. |
| `buscar_total_investimentos` | Retorna o total investido e a distribuição por classe de ativo. |

Todos os dados são **mockados** — não há integração real com nenhum sistema bancário.

## Instalação

```bash
cd mcp-server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Execução (stdio)

```bash
python server.py
```

O processo fica escutando via stdio, pronto para ser conectado por qualquer cliente MCP (Claude Desktop, agente customizado, etc).

## Configuração no Claude Desktop

Adicione ao `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "banco-mock": {
      "command": "python",
      "args": ["/caminho/absoluto/para/mcp-server/server.py"]
    }
  }
}
```

## Configuração no agente `claude-agent-sdk`

```python
from claude_agent_sdk import ClaudeAgentOptions

options = ClaudeAgentOptions(
    mcp_servers={
        "banco": {
            "type": "stdio",
            "command": "python",
            "args": ["/caminho/absoluto/para/mcp-server/server.py"],
        }
    },
    allowed_tools=[
        "mcp__banco__buscar_saldo",
        "mcp__banco__buscar_fatura",
        "mcp__banco__buscar_total_investimentos",
    ],
)
```

# examples

Exemplos mínimos e autocontidos do `claude-agent-sdk` conectando em provedores diferentes.
Cada script faz a mesma coisa (pergunta uma pergunta simples e imprime a resposta + custo)
pra você comparar 1-para-1 o que muda entre os dois provedores.

## Setup

```bash
cd examples
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

O `.env` é lido da raiz do repo via `find_dotenv()` — o mesmo já usado pelos serviços.

## 1. Anthropic API (default)

```bash
python anthropic_api.py
```

Requer no `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

Modelo default do script: `claude-haiku-4-5` (barato pra teste). Sobrescreva via
`ANTHROPIC_MODEL=claude-sonnet-4-5` (ou qualquer outro slug da Anthropic).

## 2. Amazon Bedrock

```bash
python bedrock.py
```

Requer no `.env`:

```bash
CLAUDE_CODE_USE_BEDROCK=1
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
# opcional: sessão temporária
# AWS_SESSION_TOKEN=...

# ID do modelo no Bedrock (varia por região; peça acesso no console AWS)
ANTHROPIC_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
# ou use um inference profile cross-region:
# ANTHROPIC_MODEL=us.anthropic.claude-haiku-4-5-20260930-v1:0
```

Alternativa a `AWS_ACCESS_KEY_ID/SECRET`: se você já rodou `aws configure` ou usa
`aws sso login`, o SDK também aceita `AWS_PROFILE=<seu-perfil>`.

Descubra quais Claude sua conta tem liberados:

```bash
aws bedrock list-foundation-models --by-provider anthropic --region us-east-1 \
  --query "modelSummaries[?contains(modelId, 'claude')].modelId" --output table
```

Se der `AccessDeniedException`, entre no console AWS Bedrock → Model access → Manage
model access e habilite os modelos Anthropic desejados (leva ~1 min pra aprovar).

## O que os dois têm em comum

Os dois scripts usam **exatamente o mesmo código de agente**:

```python
async with ClaudeSDKClient(options=ClaudeAgentOptions(model=...)) as client:
    await client.query("...")
    async for msg in client.receive_response():
        ...
```

A **única** diferença é o `.env`: setar (ou não) `CLAUDE_CODE_USE_BEDROCK=1`
e as credenciais AWS. O SDK detecta e roteia automaticamente. Isso prova o ponto:
Bedrock não desbloqueia modelos de outros vendors — só troca a infra onde o mesmo
Claude está rodando.

## Comparação prática

| Aspecto | Anthropic API | Amazon Bedrock |
|---|---|---|
| Setup | 1 env var | 4 env vars + Model access no console |
| Cobrança | Cartão Anthropic | AWS bill (com IAM/tags/quotas) |
| Regiões | Global (Anthropic hospedado) | Region-specific AWS |
| Latência | Baixa (geralmente) | Depende da região AWS |
| PrivateLink/VPC | Não | Sim (via VPC Endpoints) |
| SSO / IAM | N/A | Nativo |
| Cache/prompt caching | Sim | Sim |
| Guardrails Bedrock | Não | Sim (nativo) |

# Dockerfile genérico usado por todos os serviços.
# Build context: raiz do repo. Selecione o serviço via build arg SERVICE_DIR:
#   docker build --build-arg SERVICE_DIR=agent-react -t agent-react .

FROM python:3.12-slim

ARG SERVICE_DIR
ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Node.js (necessário para o claude-agent-sdk, que embute o Claude Code CLI).
# Nem todos os serviços usam (mcp-server não), mas colocar no base simplifica.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 1) Lib compartilhada (poucas mudanças → cache eficiente)
COPY a2a-common /a2a-common
RUN pip install -e /a2a-common

# 2) debugpy para modo debug (idempotente, poucos MB)
RUN pip install debugpy

# 3) Serviço-alvo
COPY ${SERVICE_DIR}/ /app/
# Remove a referência a "-e ../a2a-common" do requirements (já instalada acima)
RUN grep -v -E '^-e[[:space:]]+.*a2a-common' requirements.txt > /tmp/reqs.txt || true \
    && pip install -r /tmp/reqs.txt

CMD ["python", "main.py"]

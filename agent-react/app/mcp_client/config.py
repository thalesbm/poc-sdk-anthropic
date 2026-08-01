"""Configuração da conexão com a API HTTP do `mcp-server`."""

from __future__ import annotations

import os

SERVER_NAME = "banco"
MCP_API_BASE_URL = os.getenv("MCP_API_BASE_URL", "http://localhost:8000").rstrip("/")
HTTP_TIMEOUT = float(os.getenv("MCP_API_TIMEOUT", "10"))

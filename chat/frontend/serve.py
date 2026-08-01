"""Servidor estático mínimo para o chat.

Uso:
    python serve.py                # http://localhost:3000
    CHAT_PORT=4000 python serve.py # porta custom

Zero dependências externas — só `http.server` da stdlib.
"""

from __future__ import annotations

import http.server
import os
import socketserver
from pathlib import Path

_DIR = Path(__file__).parent


class _Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(_DIR), **kwargs)

    def end_headers(self) -> None:
        # Sem cache pra facilitar hot-reload durante dev
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main() -> None:
    port = int(os.getenv("CHAT_PORT", "3000"))
    with socketserver.TCPServer(("0.0.0.0", port), _Handler) as httpd:
        print(f"chat servido em http://localhost:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()

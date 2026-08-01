"""Estado compartilhado entre ferramentas do mesmo domínio.

Isolado num módulo próprio para que cada `@tool` possa viver em seu próprio
arquivo sem introduzir dependências cíclicas.
"""

from __future__ import annotations

NOTES: list[str] = []

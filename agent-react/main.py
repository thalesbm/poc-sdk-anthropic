"""Entrypoint do especialista ReAct — servidor A2A.

Uso (a partir de `agent-react/`):
    python main.py
"""

from __future__ import annotations

import uvicorn
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    uvicorn.run("app.server:app", host="0.0.0.0", port=8100, reload=False)


if __name__ == "__main__":
    main()

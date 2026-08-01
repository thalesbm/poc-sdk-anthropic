"""Servidor A2A do especialista Workflow (HITL)."""

from __future__ import annotations

from a2a_common.server import create_a2a_app

from .card import CARD
from .executor import handle_message

app = create_a2a_app(CARD, handle_message)

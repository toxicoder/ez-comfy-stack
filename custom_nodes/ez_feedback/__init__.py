"""Feedback pack: shared bug-report / feature-request chrome for the stack.

JS buttons plus fail-soft HTTP routes. No canvas nodes. Every surface (App,
media, film board, watch, model check) calls the same ``js/ez_feedback_core.js``
exports, and ``context.py`` is the single source of truth for title, labels,
body, and issue URL.
"""

from __future__ import annotations

from typing import Any

from .context import REPO
from .routes import register_routes

NODE_CLASS_MAPPINGS: dict[str, type[Any]] = {}
"""Comfy registry (empty - JS + routes only)."""

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}
"""Comfy display-name registry (empty - no canvas nodes)."""

WEB_DIRECTORY = "./js"
"""Comfy extra web assets (feedback buttons, dialog, banner under ``js/``)."""

register_routes()

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
    "REPO",
    "register_routes",
]

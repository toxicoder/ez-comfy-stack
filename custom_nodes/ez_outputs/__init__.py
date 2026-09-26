"""Outputs sidebar: durable generation files that survive stack restart.

JS chrome plus fail-soft HTTP routes. No canvas nodes.
"""

from __future__ import annotations

from typing import Any

from .routes import register_routes

NODE_CLASS_MAPPINGS: dict[str, type[Any]] = {}
"""Comfy registry (empty - JS + routes only)."""

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}
"""Comfy display-name registry (empty - no canvas nodes)."""

WEB_DIRECTORY = "./js"
"""Comfy extra web assets (Outputs sidebar under ``js/``)."""

register_routes()

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
    "register_routes",
]

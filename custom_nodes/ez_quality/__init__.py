"""ez-comfy global Quality combo plus an isolated Check models node."""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from .routes import register_routes

WEB_DIRECTORY = "./js"
"""Comfy frontend extension directory (relative to this pack)."""

register_routes()

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
    "register_routes",
]

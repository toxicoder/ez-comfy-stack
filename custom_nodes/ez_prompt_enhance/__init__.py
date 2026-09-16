"""ez-comfy model-specific prompt enhance nodes (Klein, Wan, LTX, opt-in)."""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./js"
"""Comfy extra web assets (App Mode sample JS under ``js/``)."""

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

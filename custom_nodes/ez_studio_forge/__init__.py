"""ez-comfy App Forge (clone lab graphs into live _user/).

Import is hermetic: stdlib only at pack load. Optional llama.cpp is lazy
inside pipeline._complete() via ez_prompt_enhance.client.complete().
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./js"
"""Comfy frontend extension directory (relative to this pack)."""

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

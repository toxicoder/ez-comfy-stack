"""ez-comfy creative research chat (CPU GGUF + SSRF-safe web search).

Import is hermetic: stdlib only at pack load. Optional llama.cpp is lazy
inside pipeline._complete() via ez_prompt_enhance.client.complete().
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

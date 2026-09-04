"""ez-comfy US-safe rap lyric helper (ACE-Step tags stay on the encoder).

Import is hermetic: stdlib only at pack load. Optional llama.cpp is lazy
inside node ``run()`` via ez_prompt_enhance.client.complete().
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

"""ez-comfy US-safe podcast nodes (script, disclosure, Kokoro TTS).

Import is hermetic: stdlib only at pack load. Optional kokoro-onnx /
chatterbox / qwen3tts backends are lazy inside node ``run()``.
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

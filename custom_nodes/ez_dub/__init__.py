"""ez-comfy US-safe multi-speaker dub (clone + translate).

Import is hermetic: stdlib only at pack load. Optional faster-whisper,
Chatterbox, Qwen3-TTS, and yt-dlp backends are lazy inside node ``run()``.
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

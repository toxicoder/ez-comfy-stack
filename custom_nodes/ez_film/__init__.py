"""ez-comfy 90s film helpers (unload between Klein/LTX, stitch 18 shots).

Import is hermetic: stdlib only at pack load. ffmpeg is resolved inside
``EZFilmConcat.run``. Optional ``comfy.model_management`` is lazy in
``EZUnloadModels``.
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

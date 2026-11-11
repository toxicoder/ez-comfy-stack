"""ez-comfy DCC desk: load host Blender guide packs on the Comfy canvas.

Import is hermetic: stdlib only at pack load. Torch is lazy inside
``pack.decode_png``. No Blender, no ``WEB_DIRECTORY`` in v1.
"""

from .nodes import NODE_CLASS_MAPPINGS as _NODE_MAPPINGS
from .nodes import NODE_DISPLAY_NAME_MAPPINGS as _NODE_DISPLAY
from .scene import NODE_CLASS_MAPPINGS as _SCENE_MAPPINGS
from .scene import NODE_DISPLAY_NAME_MAPPINGS as _SCENE_DISPLAY

NODE_CLASS_MAPPINGS = {**_NODE_MAPPINGS, **_SCENE_MAPPINGS}
"""Comfy class-name registry."""
NODE_DISPLAY_NAME_MAPPINGS = {**_NODE_DISPLAY, **_SCENE_DISPLAY}
"""Comfy display-name registry."""

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

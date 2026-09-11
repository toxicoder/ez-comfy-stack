"""ez-comfy DCC desk: load host Blender guide packs on the Comfy canvas.

Import is hermetic: stdlib only at pack load. Torch is lazy inside
``pack.decode_png``. No Blender, no ``WEB_DIRECTORY`` in v1.
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

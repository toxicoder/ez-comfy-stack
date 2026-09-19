"""ez-comfy image size helpers and still / video format pickers."""

from .modes import NODE_CLASS_MAPPINGS as _MODE_MAPPINGS
from .modes import NODE_DISPLAY_NAME_MAPPINGS as _MODE_DISPLAY
from .nodes import (
    NODE_CLASS_MAPPINGS as _SIZE_MAPPINGS,
)
from .nodes import (
    NODE_DISPLAY_NAME_MAPPINGS as _SIZE_DISPLAY,
)
from .refs import NODE_CLASS_MAPPINGS as _REF_MAPPINGS
from .refs import NODE_DISPLAY_NAME_MAPPINGS as _REF_DISPLAY

NODE_CLASS_MAPPINGS = {**_SIZE_MAPPINGS, **_REF_MAPPINGS, **_MODE_MAPPINGS}
"""Comfy class-name registry."""
NODE_DISPLAY_NAME_MAPPINGS = {**_SIZE_DISPLAY, **_REF_DISPLAY, **_MODE_DISPLAY}
"""Comfy display-name registry."""

WEB_DIRECTORY = "./js"
"""Comfy frontend extension directory (relative to this pack)."""

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

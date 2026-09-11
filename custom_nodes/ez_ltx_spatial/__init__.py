"""Lab pack: snap LTX spatial dims to the video VAE 32× grid and length to 1+8n.

No extra canvas nodes. Import wraps Comfy ``LTXVImgToVideo``,
``EmptyLTXVLatentVideo``, ``LTXVEmptyLatentAudio``, and ``VideoVAE.encode``
when those modules exist.
"""

from .patch import apply_patches

NODE_CLASS_MAPPINGS: dict[str, type] = {}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}

apply_patches()

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

"""NVIDIA lab opt-in tier: catalog cards, preflight, and the operator job node.

Import is hermetic: stdlib only at pack load, because Comfy auto-loads every
pack under ``custom_nodes/`` on every boot. ``ez_common`` is lazy-imported
inside the node methods after ``ensure_custom_nodes_path()``, the catalog is
read with the pack's own stdlib ``json`` reader, and a missing or malformed
catalog is a node error string rather than an exception. No routes and no
frontend assets, so there is no ``WEB_DIRECTORY`` here.
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]

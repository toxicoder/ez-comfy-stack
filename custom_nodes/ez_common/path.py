"""sys.path helper so sibling ez_* packs import under ComfyUI 0.34+."""

from __future__ import annotations

import sys
from pathlib import Path

_PACK_ROOT = Path(__file__).resolve().parent.parent
"""``custom_nodes/`` directory that contains ``ez_common``."""


def ensure_custom_nodes_path(*, anchor: Path | str | None = None) -> Path:
    """Prepend the lab ``custom_nodes`` directory to ``sys.path``.

    Comfy 0.34 registers directory packs as the filesystem path, not the
    folder name, and does not put ``custom_nodes`` on ``sys.path``. Packs
    that still boot without this helper should call it before importing a
    sibling (``ez_common``, ``ez_prompt_enhance``, ...).

    Args:
        anchor: File or directory under ``custom_nodes/``. ``None`` uses
            this pack (``ez_common``), which resolves to ``custom_nodes/``.

    Returns:
        The ``custom_nodes`` directory that was ensured.
    """
    if anchor is None:
        root = _PACK_ROOT
    else:
        path = Path(anchor).resolve()
        if path.is_file():
            path = path.parent
        root = path if path.name == "custom_nodes" else path.parent
        if root.name != "custom_nodes":
            root = _PACK_ROOT
    text = str(root)
    if text not in sys.path:
        sys.path.insert(0, text)
    return root

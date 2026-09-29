"""Output-dir, audio-suffix, and JSON sidecar plumbing for the music pack.

One owner for the pieces the node, tagger, and packer all used to hand-roll.
Hermetic at import: stdlib only. ``ez_common`` is lazy inside
:func:`output_dir` because Comfy 0.34 does not register sibling folder names
at pack load.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

FLAC_SUFFIXES = (".flac",)
"""Masters the Vorbis tagger writes."""

ID3_SUFFIXES = (".mp3", ".wav")
"""Masters the ID3 tagger writes."""

AUDIO_SUFFIXES = FLAC_SUFFIXES + ID3_SUFFIXES
"""Masters the pack globs, tags, and zips, in tagger order."""

ENV_OUTPUT_DIR = "COMFY_OUTPUT_DIR"
"""Compose sets this to the durable mount that holds masters and ``albums/``."""


def output_dir(*, default: str | Path) -> Path:
    """Resolve the directory holding SaveAudio masters and ``albums/``.

    Prefers the shared :func:`ez_common.output_root`. When that pack is
    unreachable (pytest, or Comfy 0.34 sibling load), falls back to
    ``COMFY_OUTPUT_DIR``, then Comfy ``folder_paths``, then ``default``.

    Args:
        default: Last-resort directory when nothing else is set.

    Returns:
        Directory path (may not exist yet).
    """
    try:
        from ez_common import output_root

        return output_root(default=str(default))
    except Exception:  # noqa: BLE001 - pytest / missing Comfy
        pass
    env = (os.environ.get(ENV_OUTPUT_DIR) or "").strip()
    if env:
        return Path(env)
    try:
        import folder_paths  # type: ignore[import-not-found]

        return Path(folder_paths.get_output_directory())
    except Exception:  # noqa: BLE001 - pytest / missing Comfy
        return Path(default)


def write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    """Write a JSON document in the pack's sidecar formatting.

    Args:
        path: Destination file.
        payload: JSON-serializable mapping.

    Returns:
        ``path``.
    """
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path

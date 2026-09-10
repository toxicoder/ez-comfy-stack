"""File-backed dub job directory under COMFY_OUTPUT_DIR/dubs/<slug>."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

STAGES = ("ingest", "analyze", "translate", "render", "export")
SLUG_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def sanitize_slug(slug: object, default: str = "episode") -> str:
    """Keep job folder names host-safe.

    Arguments:
        slug: Operator widget text.
        default: Fallback when empty after sanitizing.
    Returns:
        Non-empty slug.
    """
    raw = slug if isinstance(slug, str) else str(slug or "")
    cleaned = SLUG_RE.sub("-", raw.strip()).strip(".-")
    return cleaned or default


def output_root() -> Path:
    """Resolve COMFY_OUTPUT_DIR (container or host)."""
    for key in ("COMFY_OUTPUT_DIR", "COMFY_OUTPUT"):
        value = (os.environ.get(key) or "").strip()
        if value:
            return Path(value)
    return Path("/mnt/comfy-output")


def dub_dir(slug: object, root: Path | None = None) -> Path:
    """``${COMFY_OUTPUT_DIR}/dubs/<slug>``."""
    base = root if root is not None else output_root()
    return Path(base) / "dubs" / sanitize_slug(slug)


def state_path(dest: Path) -> Path:
    """Path to state.json."""
    return dest / "state.json"


def new_state(slug: str) -> dict[str, Any]:
    """Fresh pending job."""
    return {
        "slug": slug,
        "stage": "ingest",
        "status": "pending",
        "source_language": "auto",
        "target_language": "es",
        "error": None,
        "flags": [],
    }


def load_state(dest: Path) -> dict[str, Any]:
    """Read state.json or return a new pending state."""
    path = state_path(dest)
    if not path.is_file():
        return new_state(dest.name)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"invalid jobstore {path}")
    return data


def save_state(dest: Path, state: dict[str, Any]) -> None:
    """Write state.json atomically enough for a single operator."""
    dest.mkdir(parents=True, exist_ok=True)
    path = state_path(dest)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def write_json(path: Path, payload: object) -> None:
    """Write UTF-8 JSON with a trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    """Load JSON from path.

    Raises:
        FileNotFoundError: missing file.
    """
    return json.loads(path.read_text(encoding="utf-8"))

"""Fail-closed guide-pack QC. Prefer ``scripts/lib/guide_pack``; vendor if missing."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


def _load_from_path(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_guide_pack() -> ModuleType:
    try:
        import guide_pack as gp  # type: ignore[import-not-found]

        return gp
    except ImportError:
        pass
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "scripts" / "lib" / "guide_pack.py"
        if candidate.is_file():
            return _load_from_path(candidate, "ez_dcc_guide_pack")
    vendored = here.parent / "_guide_pack.py"
    if vendored.is_file():
        return _load_from_path(vendored, "ez_dcc_guide_pack_vendor")
    raise ImportError("guide_pack is unavailable (scripts/lib and vendor miss)")


_GP = _load_guide_pack()
GuidePackError = _GP.GuidePackError


def validate_shot(data: dict[str, Any]) -> list[str]:
    """Return shot-yaml defect strings (empty means ok)."""
    return list(_GP.validate_shot(data))


def validate_pack(pack_dir: Path, *, require_full_seq: bool = True) -> list[str]:
    """Fail-closed QC for a dumped shot pack directory."""
    return list(_GP.validate_pack(pack_dir, require_full_seq=require_full_seq))


def validate_still(data: dict[str, Any]) -> list[str]:
    """Return still-yaml defect strings (empty means ok)."""
    return list(_GP.validate_still(data))


def validate_still_pack(pack_dir: Path) -> list[str]:
    """Fail-closed QC for a single-frame still pack."""
    return list(_GP.validate_still_pack(pack_dir))


def load_shot(path: Path) -> dict[str, Any]:
    """Read shot.yaml from a pack directory or file."""
    return dict(_GP.load_shot(path))


def load_still(path: Path) -> dict[str, Any]:
    """Read still.yaml from a pack directory or file."""
    return dict(_GP.load_still(path))


def raise_defects(defects: list[str]) -> None:
    """Raise GuidePackError when QC found defects.

    Args:
        defects: Messages from validate_*.

    Raises:
        GuidePackError: non-empty defect list.
    """
    if defects:
        raise GuidePackError("; ".join(defects))


def require_file(path: Path, *, label: str) -> Path:
    """Fail-closed existence check.

    Args:
        path: Expected file.
        label: Human name for the error.

    Returns:
        The same path.

    Raises:
        GuidePackError: missing file.
    """
    if not path.is_file():
        raise GuidePackError(f"missing {label} at {path}")
    return path


# Keep a stable alias for tests that inspect sys.modules.
sys.modules.setdefault("ez_dcc._qc_guide_pack", _GP)

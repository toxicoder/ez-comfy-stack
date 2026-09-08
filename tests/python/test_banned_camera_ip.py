"""First-person body-cam grammar must not name commercial camera IP.

Hermetic: stdlib only. The needles live only in this file.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

NEEDLES = (
    "Hardcore Henry",
    "Hardcore Harry",
    "Ilya Naishuller",
    "Adventure Mask",
    "Biting Elbows",
)

SCAN_DIRS = (
    ROOT / "workflows",
    ROOT / "docs",
    ROOT / "custom_nodes",
    ROOT / "scripts",
    ROOT / "schemas",
)
SCAN_FILES = (ROOT / "README.md",)
SKIP_SUFFIXES = {".pyc", ".png", ".jpg", ".webp", ".mp4", ".wav"}


def _iter_text_files() -> list[Path]:
    found: list[Path] = []
    for folder in SCAN_DIRS:
        if not folder.is_dir():
            continue
        for path in folder.rglob("*"):
            if not path.is_file() or path.suffix.lower() in SKIP_SUFFIXES:
                continue
            found.append(path)
    for path in SCAN_FILES:
        if path.is_file():
            found.append(path)
    return found


def test_camera_ip_names_stay_out_of_the_tree() -> None:
    hits: list[str] = []
    for path in _iter_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for needle in NEEDLES:
            if needle in text:
                hits.append(f"{path.relative_to(ROOT)}:{needle}")
    assert hits == []

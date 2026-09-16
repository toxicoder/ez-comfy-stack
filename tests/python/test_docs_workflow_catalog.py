"""Catalog docs must name every shipped _lab graph.

Hermetic: stdlib + JSON. No MkDocs, network, Docker, or GPU.
"""

from __future__ import annotations

import json
from pathlib import Path

from _lab_paths import load_lab_graph

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "workflows" / "_lab"
DOCS = ROOT / "docs"

CATALOG_PAGES = (
    DOCS / "studio-workflows.md",
    DOCS / "create" / "workflows-stills.md",
    DOCS / "create" / "workflows-motion.md",
    DOCS / "create" / "workflows-film.md",
    DOCS / "create" / "workflows-audio.md",
)

SKIP_NAMES = frozenset({"album.json", "cover.json"})


def _graph_id(path: Path) -> str:
    """Return extra.lab_rel when set, else the _lab-relative stem.

    Args:
        path: Shipped lab JSON path under workflows/_lab.

    Returns:
        Catalog id such as ``klein/still-draft``.
    """
    extra = load_lab_graph(path).get("extra") or {}
    lab_rel = extra.get("lab_rel")
    if isinstance(lab_rel, str) and lab_rel.strip():
        return lab_rel.strip()
    return path.relative_to(LAB).with_suffix("").as_posix()


def test_catalog_pages_exist() -> None:
    """Index and the four catalog children are present."""
    missing = [str(path.relative_to(ROOT)) for path in CATALOG_PAGES if not path.is_file()]
    assert missing == [], "catalog pages missing:\n" + "\n".join(missing)


def test_catalog_docs_name_every_lab_graph() -> None:
    """Every _lab graph except album.json / cover.json appears in the catalog."""
    catalog = "\n".join(path.read_text(encoding="utf-8") for path in CATALOG_PAGES)
    graphs = sorted(
        path
        for path in LAB.rglob("*.json")
        if path.is_file() and path.name not in SKIP_NAMES
    )
    assert graphs, f"no lab graphs under {LAB}"
    missing = [gid for gid in (_graph_id(path) for path in graphs) if gid not in catalog]
    assert missing == [], "lab graphs missing from catalog docs:\n" + "\n".join(missing)

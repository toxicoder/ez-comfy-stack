"""Lab graphs may only use EZ class names that a pack actually exports.

Hermetic: stdlib + JSON + in-tree pack imports. No Comfy, Docker, or GPU.
Catches restamping `_lab` JSON with class names that are not in
``NODE_CLASS_MAPPINGS`` (Comfy Errors tab: Missing Node Packs / Unknown pack).
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from _docs_paths import docs_file
from _lab_paths import cached_lab_graph_rows

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
CATALOG = docs_file(ROOT / "docs" / "reference" / "custom-nodes.md")


def _pack_class_names() -> set[str]:
    """Union of ``NODE_CLASS_MAPPINGS`` keys from every ``ez_*`` pack.

    Returns:
        Class names Comfy would register from in-tree packs.
    """
    names: set[str] = set()
    for path in sorted(CUSTOM.glob("ez_*")):
        if not path.is_dir() or not (path / "__init__.py").is_file():
            continue
        module = importlib.import_module(path.name)
        mapping = getattr(module, "NODE_CLASS_MAPPINGS", {})
        assert isinstance(mapping, dict), path.name
        names.update(str(key) for key in mapping)
    return names


def _graph_ez_types(data: dict[str, Any]) -> set[str]:
    """Return EZ* node types on a graph, including nested subgraphs.

    Args:
        data: Parsed lab graph JSON.

    Returns:
        Class names that start with ``EZ``.
    """
    types: set[str] = set()
    nodes = list(data.get("nodes") or [])
    for sub in ((data.get("definitions") or {}).get("subgraphs") or []):
        if isinstance(sub, dict):
            nodes.extend(sub.get("nodes") or [])
    for node in nodes:
        if not isinstance(node, dict):
            continue
        ntype = str(node.get("type") or "")
        if ntype.startswith("EZ"):
            types.add(ntype)
    return types


def test_lab_ez_types_are_exported_by_a_pack() -> None:
    """Every EZ* type in ``workflows/_lab`` is in some pack mapping."""
    exported = _pack_class_names()
    assert "EZImageUpscale" in exported
    assert "EZImageDescribe" in exported
    missing: list[str] = []
    seen: set[str] = set()
    for rel, path, data in cached_lab_graph_rows():
        for ntype in sorted(_graph_ez_types(data)):
            if ntype in exported or ntype in seen:
                continue
            seen.add(ntype)
            missing.append(f"{ntype} ({path.relative_to(ROOT).as_posix()} / {rel})")
    assert missing == [], "lab EZ types missing from pack NODE_CLASS_MAPPINGS:\n" + "\n".join(
        missing
    )


def test_custom_nodes_catalog_names_pack_classes() -> None:
    """``docs/reference/custom-nodes`` lists every exported EZ class."""
    catalog = CATALOG.read_text(encoding="utf-8")
    missing = [
        name
        for name in sorted(_pack_class_names())
        if f"`{name}`" not in catalog
    ]
    assert missing == [], "pack classes missing from custom-nodes catalog:\n" + "\n".join(
        missing
    )

"""Every _lab graph has generated node/parameter docs.

Hermetic: stdlib + JSON + the generator module. No MkDocs, network, Docker, or GPU.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "workflows" / "_lab"
DOCS = ROOT / "docs"
GEN_PY = DOCS / "generate_workflow_docs.py"
NODES_PY = DOCS / "workflow_nodes.py"
MANIFEST = DOCS / "generated" / "workflows" / "manifest.json"


def _load_gen() -> Any:
    """Load docs/generate_workflow_docs.py.

    Returns:
        Generator module.
    """
    docs_dir = str(DOCS)
    if docs_dir not in sys.path:
        sys.path.insert(0, docs_dir)
    spec = importlib.util.spec_from_file_location("ez_generate_workflow_docs", GEN_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["ez_generate_workflow_docs"] = module
    spec.loader.exec_module(module)
    return module


def _load_nodes() -> Any:
    """Load docs/workflow_nodes.py.

    Returns:
        Encyclopedia module.
    """
    docs_dir = str(DOCS)
    if docs_dir not in sys.path:
        sys.path.insert(0, docs_dir)
    spec = importlib.util.spec_from_file_location("ez_workflow_nodes", NODES_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["ez_workflow_nodes"] = module
    spec.loader.exec_module(module)
    return module


def _lab_graphs() -> list[tuple[str, Path, dict[str, Any]]]:
    """Return every JSON graph under workflows/_lab.

    Returns:
        (lab_rel, path, data) rows.
    """
    gen = _load_gen()
    return gen.iter_lab_graphs(LAB)


def test_encyclopedia_covers_every_lab_node_type() -> None:
    """Union of node.type in _lab is a subset of encyclopedia keys."""
    enc = _load_nodes().encyclopedia()
    missing: list[str] = []
    seen: set[str] = set()
    for _rel, path, data in _lab_graphs():
        for node in data.get("nodes") or []:
            ntype = str(node.get("type") or "")
            if ntype and ntype not in enc and ntype not in seen:
                seen.add(ntype)
                missing.append(f"{ntype} ({path.relative_to(ROOT).as_posix()})")
    assert missing == [], "node types missing from encyclopedia:\n" + "\n".join(missing)


def test_widget_schema_matches_lab_json() -> None:
    """Every instance's widgets_values matches an encyclopedia layout."""
    gen = _load_gen()
    enc = _load_nodes().encyclopedia()
    hits: list[str] = []
    for lab_rel, path, data in _lab_graphs():
        for node in data.get("nodes") or []:
            ntype = str(node.get("type") or "")
            spec = enc.get(ntype)
            if not spec:
                continue
            values = node.get("widgets_values")
            layout = gen.match_layout(spec, values)
            if layout is None:
                hits.append(
                    f"{lab_rel} node {node.get('id')} type {ntype}: "
                    f"no layout for {values!r:.180}"
                )
    assert hits == [], "widget layout mismatches:\n" + "\n".join(hits[:40])


def test_combo_values_are_documented() -> None:
    """Stored combo ids appear in encyclopedia choices when choices exist."""
    gen = _load_gen()
    nodes_mod = _load_nodes()
    enc = nodes_mod.encyclopedia()
    styles = gen.load_styles()
    hits: list[str] = []
    for lab_rel, _path, data in _lab_graphs():
        for node in data.get("nodes") or []:
            ntype = str(node.get("type") or "")
            spec = enc.get(ntype) or {}
            layout = gen.match_layout(spec, node.get("widgets_values"))
            if layout is None:
                continue
            for widget in layout:
                choices = gen.expand_choices(
                    widget,
                    styles=styles,
                    ace_language=nodes_mod.ACE_LANGUAGE_CHOICES,
                    ace_keyscale=nodes_mod.ACE_KEYSCALE_CHOICES,
                )
                if not choices:
                    continue
                allowed = {row["id"] for row in choices}
                val = gen.read_widget_value(node.get("widgets_values"), widget)
                if val is None or isinstance(val, (int, float, bool)):
                    continue
                text = str(val)
                if text not in allowed:
                    hits.append(
                        f"{lab_rel} {ntype}.{widget.get('name')}={text!r} "
                        f"not in {sorted(allowed)[:12]}"
                    )
    assert hits == [], "undocumented combo values:\n" + "\n".join(hits[:40])


def test_every_lab_graph_has_details_coverage() -> None:
    """Every _lab JSON id appears on a generated details page."""
    gen = _load_gen()
    pages = gen.generate(ROOT, write=False)
    blob = "\n".join(pages.values())
    missing: list[str] = []
    for lab_rel, path, _data in _lab_graphs():
        rel_file = path.relative_to(LAB).as_posix()
        album = gen.album_key_of(rel_file)
        if album:
            if album not in blob or Path(lab_rel).name not in blob:
                missing.append(lab_rel)
        elif lab_rel not in blob:
            missing.append(lab_rel)
    assert missing == [], "lab graphs missing from generated docs:\n" + "\n".join(missing)


def test_details_page_lists_every_node_id() -> None:
    """Non-album pages name every node id from that JSON."""
    gen = _load_gen()
    pages = gen.generate(ROOT, write=False)
    missing: list[str] = []
    for lab_rel, path, data in _lab_graphs():
        rel_file = path.relative_to(LAB).as_posix()
        if gen.album_key_of(rel_file):
            continue
        rel = f"generated/workflows/{lab_rel}.md"
        text = pages.get(rel, "")
        for node in data.get("nodes") or []:
            nid = str(node.get("id"))
            if f"| {nid} |" not in text:
                missing.append(f"{lab_rel} missing node id {nid}")
                break
    assert missing == [], "node ids missing from details pages:\n" + "\n".join(missing[:40])


def test_parameter_section_names_every_widget() -> None:
    """Bottom section includes every encyclopedia widget name for types used."""
    gen = _load_gen()
    enc = _load_nodes().encyclopedia()
    pages = gen.generate(ROOT, write=False)
    missing: list[str] = []
    for lab_rel, path, data in _lab_graphs():
        rel_file = path.relative_to(LAB).as_posix()
        if gen.album_key_of(rel_file):
            rel = f"generated/workflows/{gen.album_key_of(rel_file)}.md"
        else:
            rel = f"generated/workflows/{lab_rel}.md"
        text = pages.get(rel, "")
        for node in data.get("nodes") or []:
            ntype = str(node.get("type") or "")
            spec = enc.get(ntype) or {}
            layout = gen.match_layout(spec, node.get("widgets_values"))
            if layout is None:
                layout = list(spec.get("widgets") or [])
            for widget in layout:
                name = str(widget.get("name") or "")
                if name and f"`{name}`" not in text:
                    missing.append(f"{rel} missing widget {ntype}.{name}")
                    break
            if missing and missing[-1].startswith(rel):
                break
        if len(missing) > 40:
            break
    assert missing == [], "widgets missing from parameter sections:\n" + "\n".join(missing)


def test_manifest_lists_generated_pages_when_written(tmp_path: Path) -> None:
    """write=True produces a manifest whose pages exist."""
    gen = _load_gen()
    out = tmp_path / "generated" / "workflows"
    enc_page = tmp_path / "reference" / "workflow-nodes.md"
    gen.generate(
        ROOT,
        out_dir=out,
        encyclopedia_page=enc_page,
        write=True,
    )
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["graph_count"] >= 300
    assert (tmp_path / "generated" / "workflows" / "index.md").is_file()
    assert (tmp_path / "reference" / "workflow-nodes.md").is_file()
    klein = tmp_path / "generated" / "workflows" / "klein" / "still-draft.md"
    assert klein.is_file()
    text = klein.read_text(encoding="utf-8")
    assert "Node parameter reference" in text
    assert "`KSampler`" in text
    assert "seed" in text

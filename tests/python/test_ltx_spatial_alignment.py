"""LTX video VAE requires spatial dims divisible by 32.

Hermetic: stdlib only. 720 and 1080 look like broadcast sizes but fail
inside the LTX encoder (einops cannot split H=45 after 16× downsample).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"

LTX_SPATIAL_TYPES = ("LTXVImgToVideo", "EmptyLTXVLatentVideo")
BROADCAST_ILLEGAL = {720, 1080}
PORTRAIT_SHORTS = "ltx-shorts-i2v-lab-example"
LANDSCAPE_SIZE = (1280, 704)
PORTRAIT_SIZE = (768, 1280)


def _workflow_json() -> list[Path]:
    files = sorted(WF.rglob("*-lab-example.json"))
    assert files, "expected lab-example workflows"
    return files


def _spatial_nodes(graph: dict) -> list[dict]:
    return [n for n in graph["nodes"] if n.get("type") in LTX_SPATIAL_TYPES]


def test_ltx_spatial_dims_are_vae_aligned() -> None:
    hits: list[str] = []
    found = 0
    for path in _workflow_json():
        graph = json.loads(path.read_text(encoding="utf-8"))
        rel = path.relative_to(ROOT)
        for node in _spatial_nodes(graph):
            found += 1
            values = node.get("widgets_values") or []
            assert len(values) >= 2, (rel, node.get("type"), values)
            width, height = int(values[0]), int(values[1])
            if width % 32 != 0 or height % 32 != 0:
                hits.append(f"{rel} {node['type']} {width}x{height} not ÷32")
            if width in BROADCAST_ILLEGAL or height in BROADCAST_ILLEGAL:
                hits.append(f"{rel} {node['type']} {width}x{height} uses 720/1080")
    assert found >= 10, found
    assert hits == [], hits


def test_ltx_lab_defaults_are_1280x704_or_portrait_768x1280() -> None:
    seen_portrait = False
    seen_landscape = False
    for path in _workflow_json():
        graph = json.loads(path.read_text(encoding="utf-8"))
        for node in _spatial_nodes(graph):
            size = (int(node["widgets_values"][0]), int(node["widgets_values"][1]))
            if path.stem == PORTRAIT_SHORTS:
                assert size == PORTRAIT_SIZE, (path.name, size)
                seen_portrait = True
            else:
                assert size == LANDSCAPE_SIZE, (path.name, node.get("type"), size)
                seen_landscape = True
    assert seen_portrait
    assert seen_landscape


def test_ltx_operator_notes_state_div32_canvas() -> None:
    missing: list[str] = []
    for path in _workflow_json():
        graph = json.loads(path.read_text(encoding="utf-8"))
        if not _spatial_nodes(graph):
            continue
        note = graph.get("extra", {}).get("lab_note") or ""
        if "divisible by 32" not in note:
            missing.append(f"{path.name}: lab_note missing ÷32 rule")
        if path.stem == PORTRAIT_SHORTS:
            if "768x1280" not in note and "768×1280" not in note:
                missing.append(f"{path.name}: lab_note missing 768x1280")
        else:
            if "1280x704" not in note and "1280×704" not in note:
                missing.append(f"{path.name}: lab_note missing 1280x704")
    assert missing == [], missing

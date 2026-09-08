"""ez_studio_blocks subgraph blueprints: shape, occupancy, US-safe weights."""

from __future__ import annotations

import json
from pathlib import Path

from _stamp_app_mode import BANNED

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "custom_nodes" / "ez_studio_blocks"
SUBS = PACK / "subgraphs"

EXPECTED = (
    "klein-t2i-backbone.json",
    "wan-i2v-5s.json",
    "ltx-av-5s.json",
    "ltx-film-shot.json",
)
OCCUPANCY = {
    "klein-t2i-backbone": "klein",
    "wan-i2v-5s": "wan",
    "ltx-av-5s": "ltx",
    "ltx-film-shot": "film",
}


def test_pack_has_init_and_blueprints() -> None:
    assert (PACK / "__init__.py").is_file()
    text = (PACK / "__init__.py").read_text(encoding="utf-8")
    assert "NODE_CLASS_MAPPINGS" in text
    for name in EXPECTED:
        assert (SUBS / name).is_file(), name


def test_blueprints_are_valid_subgraph_json() -> None:
    for name in EXPECTED:
        path = SUBS / name
        graph = json.loads(path.read_text(encoding="utf-8"))
        blob = json.dumps(graph)
        for needle in BANNED:
            assert needle not in blob, (name, needle)
        defs = graph["definitions"]["subgraphs"]
        assert defs
        sub = defs[0]
        assert sub["id"]
        assert sub["name"] == path.stem
        assert sub["inputs"]
        assert sub["outputs"]
        assert sub["nodes"]
        occ = OCCUPANCY[path.stem]
        assert any(
            n.get("type") == "Note"
            and "Occupancy:" in str((n.get("widgets_values") or [""])[0])
            for n in sub["nodes"]
        ), name
        assert occ in json.dumps(sub.get("extra") or {})
        root = graph["nodes"][0]
        assert root["type"] == sub["id"]
        if path.stem.startswith("ltx"):
            assert "1280" in blob
            assert "720" not in blob or "1280x704" in blob
            assert "klein-9b" not in blob


def test_ltx_film_shot_is_concat_safe() -> None:
    graph = json.loads((SUBS / "ltx-film-shot.json").read_text(encoding="utf-8"))
    sub = graph["definitions"]["subgraphs"][0]
    assert any(n.get("type") == "VHS_VideoCombine" for n in sub["nodes"])
    assert any(
        n.get("title") == "Save last frame"
        and str((n.get("widgets_values") or [""])[0]).endswith("_last")
        for n in sub["nodes"]
    )

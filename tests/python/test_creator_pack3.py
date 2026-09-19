"""Creator pack 3: 100 content-creator lab Apps."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from _creator_pack3 import PACK3, pack3_pin_off, pack3_stamp_rows
from _lab_paths import LAB_ROOT, lab_json, load_lab_graph
from _stamp_app_mode import STAMP_SPECS, linear_input_node_id

BANNED = (
    "MiniMax",
    "MiniMaxH3",
    "minimax_h3",
    "klein-9b",
    "FLUX.2-dev",
    "Seedance",
    "Kling",
    "z_image_turbo",
)


def test_pack3_count_and_unique_ids() -> None:
    assert len(PACK3) == 100
    rels = [spec.rel for spec in PACK3]
    assert len(set(rels)) == 100
    stems = [spec.rel.rsplit("/", 1)[-1] for spec in PACK3]
    assert len(set(stems)) == 100
    prefixes: list[str] = []
    for spec in PACK3:
        prefixes.extend(spec.prefixes or (spec.prefix,))
    dupes = [name for name, count in Counter(prefixes).items() if count > 1]
    assert dupes == []
    counts = Counter(spec.occupancy for spec in PACK3)
    assert counts == {"klein": 57, "wan": 25, "ltx": 18}


def test_pack3_files_identity_and_prefixes() -> None:
    for spec in PACK3:
        path = lab_json(spec.rel)
        assert path.is_file(), spec.rel
        graph = load_lab_graph(path)
        extra = graph.get("extra") or {}
        assert graph.get("id") == spec.rel.rsplit("/", 1)[-1]
        assert extra.get("lab_rel") == spec.rel
        assert extra.get("lab_note", "").strip()
        assert extra.get("lab_description", "").strip()
        blob = json.dumps(graph)
        for needle in BANNED:
            assert needle not in blob, (spec.rel, needle)
        for prefix in spec.prefixes or (spec.prefix,):
            assert prefix in blob, (spec.rel, prefix)
        mode = extra.get("lab_app_mode") or {}
        assert mode.get("enabled") is True
        assert mode.get("occupancy") == spec.occupancy
        assert mode.get("lane") == "produce"
        linear = extra.get("linearData") or {}
        live = {int(node["id"]) for node in graph.get("nodes") or []}
        for entry in linear.get("inputs") or []:
            assert linear_input_node_id(entry) in live
            assert isinstance(entry[0], int)
        for node_id in linear.get("outputs") or []:
            assert int(node_id) in live


def test_pack3_sizes_and_video_outputs() -> None:
    for spec in PACK3:
        graph = load_lab_graph(lab_json(spec.rel))
        if spec.kind in {"klein_single", "klein_pack"}:
            latent = next(
                node
                for node in graph["nodes"]
                if node.get("type") == "EmptyFlux2LatentImage"
            )
            assert latent["widgets_values"][0] == spec.size[0], spec.rel
            assert latent["widgets_values"][1] == spec.size[1], spec.rel
            continue
        vhs = [node for node in graph["nodes"] if node.get("type") == "VHS_VideoCombine"]
        assert vhs, spec.rel
        for node in vhs:
            widgets = node["widgets_values"]
            assert widgets["save_output"] is True
            assert str(widgets["filename_prefix"]).startswith("ez_")
        if spec.kind == "wan_i2v" or spec.kind == "wan_loop":
            lat = next(
                node
                for node in graph["nodes"]
                if node.get("type") == "Wan22ImageToVideoLatent"
            )
            assert lat["widgets_values"][0] == spec.size[0], spec.rel
            assert lat["widgets_values"][1] == spec.size[1], spec.rel
        if spec.kind == "ltx_av":
            assert spec.size[0] % 32 == 0 and spec.size[1] % 32 == 0, spec.rel
            img = next(
                (
                    node
                    for node in graph["nodes"]
                    if node.get("type") in {"LTXVImgToVideo", "EmptyLTXVLatentVideo"}
                ),
                None,
            )
            assert img is not None, spec.rel
            assert img["widgets_values"][0] == spec.size[0], spec.rel
            assert img["widgets_values"][1] == spec.size[1], spec.rel


def test_pack3_registered_in_stamp_specs() -> None:
    rows = pack3_stamp_rows()
    assert len(rows) == 100
    for rel, occupancy, _handoff, pin in rows:
        spec = STAMP_SPECS[rel]
        assert spec["occupancy"] == occupancy
        assert spec["lane"] == "produce"
        assert spec["enhance_off_identity"] is pin
    assert pack3_pin_off() == frozenset(spec.rel for spec in PACK3 if spec.enhance_pin)
    assert Path(LAB_ROOT / "creator" / "stills").is_dir()

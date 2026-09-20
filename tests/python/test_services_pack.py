"""Services pack: 200 content-creation lab Apps."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from _lab_paths import LAB_ROOT, lab_json, load_lab_graph
from _services_pack import SERVICES, services_pin_off, services_stamp_rows
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
CATALOG_PAGE = Path(__file__).resolve().parents[2] / "docs" / "create" / "workflows-services.md"


def test_services_count_and_unique_ids() -> None:
    assert len(SERVICES) == 200
    rels = [spec.rel for spec in SERVICES]
    assert len(set(rels)) == 200
    stems = [spec.rel.rsplit("/", 1)[-1] for spec in SERVICES]
    assert len(set(stems)) == 200
    prefixes = [spec.prefix for spec in SERVICES]
    dupes = [name for name, count in Counter(prefixes).items() if count > 1]
    assert dupes == []
    kinds = {spec.kind for spec in SERVICES}
    assert kinds <= {"klein_single", "wan_i2v", "wan_loop", "ltx_av"}
    assert "klein_pack" not in kinds
    counts = Counter(spec.occupancy for spec in SERVICES)
    assert set(counts) <= {"klein", "wan", "ltx"}
    assert 85 <= counts["klein"] <= 95
    assert 45 <= counts["wan"] <= 55
    assert 55 <= counts["ltx"] <= 65
    assert sum(counts.values()) == 200
    for spec in SERVICES:
        assert spec.rel.startswith("services/")
        assert spec.rel.split("/")[1] == spec.group
        assert spec.prefix.startswith("ez_svc_")
        assert spec.occupancy in {"klein", "wan", "ltx"}


def test_services_files_identity_and_prefixes() -> None:
    for spec in SERVICES:
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
        assert spec.prefix in blob, (spec.rel, spec.prefix)
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


def test_services_sizes_and_video_outputs() -> None:
    for spec in SERVICES:
        graph = load_lab_graph(lab_json(spec.rel))
        if spec.kind == "klein_single":
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
        if spec.kind in {"wan_i2v", "wan_loop"}:
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


def test_services_registered_in_stamp_specs() -> None:
    rows = services_stamp_rows()
    assert len(rows) == 200
    for rel, occupancy, _handoff, pin in rows:
        spec = STAMP_SPECS[rel]
        assert spec["occupancy"] == occupancy
        assert spec["lane"] == "produce"
        assert spec["enhance_off_identity"] is pin
    assert services_pin_off() == frozenset(
        spec.rel for spec in SERVICES if spec.enhance_pin
    )
    assert Path(LAB_ROOT / "services" / "ecommerce").is_dir()


def test_services_catalog_names_every_lab_rel() -> None:
    text = CATALOG_PAGE.read_text(encoding="utf-8")
    missing = [spec.rel for spec in SERVICES if spec.rel not in text]
    assert missing == []

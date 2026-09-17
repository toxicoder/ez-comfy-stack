"""Stage and prompt mapper for Cinema Rack illustration clips."""

from __future__ import annotations

import importlib.util
import json
import re
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
GEN_PY = ROOT / "docs" / "cinema_clip_prompts.py"
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_prompt_enhance import cinema  # noqa: E402

_BANNED = (
    "kodak",
    "portra",
    "sony",
    "canon",
    "leica",
    "hasselblad",
    "pixar",
    "unreal",
    "lumen",
    "ghibli",
    "panavision",
    "arriflex",
    "arri ",
    "red komodo",
    "imax",
    "dolby",
    "technicolor",
    "nolan",
    "fincher",
    "tarantino",
    "spielberg",
    "scorsese",
    "villeneuve",
    "blade runner",
    "mad max",
    "tiktok",
    "instagram",
    "youtube",
)


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("ez_cinema_clip_prompts", GEN_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["ez_cinema_clip_prompts"] = module
    spec.loader.exec_module(module)
    return module


def test_stages_are_the_eight_locks() -> None:
    """Illustration stages stay a closed 8-member lock set."""
    mod = _load()
    assert mod.STAGES == (
        "face_close",
        "portrait_mcu",
        "medium_person",
        "full_body",
        "street_wide",
        "interior_room",
        "night_neon",
        "tabletop_hands",
    )
    assert mod.DURATION_S == 5
    assert mod.ASPECT_RATIO == "16:9"
    assert "zoom_in" in mod.MOTION_KINDS
    assert "whip_left" in mod.MOTION_KINDS


def test_every_shipped_row_maps_to_a_known_stage() -> None:
    """Every catalog technique gets a stage, duration, and aspect."""
    mod = _load()
    known = set(mod.STAGES)
    count = 0
    for axis_id in cinema.axis_ids():
        for row in cinema.load_axis(axis_id):
            spec = mod.clip_spec(axis_id, row)
            assert spec["stage"] in known, f"{axis_id} {row.get('id')}"
            assert spec["technique_id"] == str(row["id"])
            assert spec["duration_s"] == 5
            assert spec["aspect_ratio"] == "16:9"
            assert spec["still_prompt"]
            assert spec["motion_prompt"]
            assert spec["motion_kind"] in set(mod.MOTION_KINDS)
            count += 1
    assert count >= 13 * 100


def test_editing_rows_request_two_plates() -> None:
    """Editing techniques ask for a join; other axes do not."""
    mod = _load()
    kinds = {"cut", "dissolve", "wipe", "match"}
    for row in cinema.load_axis("editing_transitions"):
        spec = mod.clip_spec("editing_transitions", row)
        assert spec["edit_kind"] in kinds, spec["technique_id"]
        assert spec["second_stage"] in set(mod.STAGES)
        assert spec["second_stage"] != spec["stage"] or spec["edit_kind"]
    for axis_id in cinema.axis_ids():
        if axis_id == "editing_transitions":
            continue
        spec = mod.clip_spec(axis_id, cinema.load_axis(axis_id)[0])
        assert spec["edit_kind"] == ""
        assert spec["second_stage"] == ""


def test_camera_movement_motion_includes_wan_token() -> None:
    """Camera-move clips name the Wan token in the motion prompt."""
    mod = _load()
    found = False
    for row in cinema.load_axis("camera_movement"):
        token = str(row.get("wan_token") or "").strip()
        if not token:
            continue
        spec = mod.clip_spec("camera_movement", row)
        assert token in spec["motion_prompt"], row["id"]
        found = True
    assert found


def test_prompts_omit_banned_needles() -> None:
    """Lock copy and generated prompts stay brand-scan clean."""
    mod = _load()
    blobs = list(mod._STAGE_LOCK.values())
    for axis_id in cinema.axis_ids():
        for row in cinema.load_axis(axis_id):
            spec = mod.clip_spec(axis_id, row)
            blobs.append(spec["still_prompt"])
            blobs.append(spec["motion_prompt"])
    haystack = "\n".join(blobs).lower()
    for needle in _BANNED:
        assert not re.search(rf"\b{re.escape(needle)}\b", haystack), needle


def test_unknown_axis_defaults_to_medium_person() -> None:
    """Unlisted axes still produce a usable lock."""
    mod = _load()
    spec = mod.clip_spec("not_an_axis", {"id": "x", "label": "X", "clause": "Hold."})
    assert spec["stage"] == "medium_person"
    assert spec["edit_kind"] == ""
    empty = mod.clip_spec("lighting", {"id": "", "clause": "", "still": "Frozen window."})
    assert "Frozen window." in empty["still_prompt"]


def test_stage_heuristics_for_face_and_tabletop() -> None:
    """ECU face vs hand inserts pick different stages."""
    mod = _load()
    assert (
        mod.stage_for("framing_shot_size", {"id": "size_ecu_iris", "tags": ["ecu"]})
        == "face_close"
    )
    assert (
        mod.stage_for(
            "framing_shot_size", {"id": "size_ecu_hands", "tags": ["ecu", "insert"]}
        )
        == "tabletop_hands"
    )
    assert (
        mod.stage_for("camera_movement", {"id": "move_drone_orbit", "tags": ["drone"]})
        == "street_wide"
    )
    kind, second = mod.edit_join("lighting", {"id": "lit_loop"})
    assert kind == ""
    assert second == ""
    kind, _second = mod.edit_join(
        "editing_transitions", {"id": "edt_hard_cut", "tags": ["cut"]}
    )
    assert kind == "cut"
    assert (
        mod.edit_join("editing_transitions", {"id": "edt_x", "tags": ["dissolve"]})[0]
        == "dissolve"
    )
    assert (
        mod.edit_join("editing_transitions", {"id": "edt_wipe_left", "tags": ["wipe"]})[0]
        == "wipe"
    )
    assert (
        mod.edit_join("editing_transitions", {"id": "edt_x", "tags": ["match"]})[0]
        == "match"
    )
    assert "cream knit" in mod.still_prompt("lighting", {"id": "x", "clause": "Hold."}, "nope")
    spec = mod.clip_spec("lighting", {"id": "lit_loop", "label": "Loop", "clause": "Key."})
    assert "breathes" in spec["motion_prompt"]
    assert spec["motion_kind"] == "hold"
    assert (
        mod.motion_kind(
            "camera_movement",
            {"id": "move_pan_left", "wan_token": "pan left", "tags": ["support"]},
        )
        == "pan_left"
    )
    assert (
        mod.motion_kind(
            "camera_movement",
            {"id": "move_dolly_in", "wan_token": "dolly in", "tags": ["support"]},
        )
        == "zoom_in"
    )
    assert (
        mod.motion_kind(
            "camera_movement",
            {"id": "move_whip_pan_right", "wan_token": "whip pan right", "tags": ["energy"]},
        )
        == "whip_right"
    )
    assert (
        mod.motion_kind(
            "camera_movement",
            {"id": "move_locked_off", "wan_token": "fixed camera", "tags": ["locked"]},
        )
        == "hold"
    )
    assert (
        mod.motion_kind(
            "camera_movement",
            {"id": "move_handheld_walk", "wan_token": "handheld", "tags": ["handheld"]},
        )
        == "jitter"
    )
    assert (
        mod.motion_kind(
            "camera_movement",
            {"id": "move_crane_up", "wan_token": "crane up", "tags": ["support"]},
        )
        == "rise"
    )
    assert (
        mod.motion_kind(
            "camera_movement",
            {"id": "move_drone_descend", "wan_token": "crane down", "tags": ["drone"]},
        )
        == "drop"
    )
    assert (
        mod.motion_kind(
            "camera_movement",
            {"id": "move_orbit_left", "wan_token": "orbit", "tags": ["support"]},
        )
        == "orbit"
    )
    assert (
        mod.motion_kind(
            "camera_movement",
            {"id": "move_tilt_up", "wan_token": "tilt up", "tags": ["support"]},
        )
        == "tilt_up"
    )
    assert (
        mod.motion_kind(
            "camera_movement",
            {"id": "move_slow_tilt_down", "wan_token": "slow tilt down", "tags": ["support"]},
        )
        == "tilt_down"
    )
    assert (
        mod.motion_kind(
            "camera_movement",
            {"id": "move_dolly_out", "wan_token": "dolly out", "tags": ["support"]},
        )
        == "zoom_out"
    )
    assert (
        mod.motion_kind(
            "camera_movement",
            {"id": "move_tracking_left", "wan_token": "tracking", "tags": ["support"]},
        )
        == "pan_left"
    )
    assert (
        mod.motion_kind(
            "camera_movement",
            {"id": "move_search_pan", "wan_token": "pan", "tags": ["support"]},
        )
        == "zoom_in"
    )
    assert (
        mod.motion_kind(
            "camera_movement",
            {"id": "move_bay_left", "wan_token": "", "tags": []},
        )
        == "pan_left"
    )
    assert (
        mod.motion_kind(
            "camera_movement",
            {"id": "move_bay_right", "wan_token": "", "tags": []},
        )
        == "pan_right"
    )


def test_specs_for_axis_and_cli_json() -> None:
    """CLI prints JSON for a real axis and rejects bad argv."""
    mod = _load()
    specs = mod.specs_for_axis("camera_movement")
    assert len(specs) == len(cinema.load_axis("camera_movement"))
    assert specs[0]["axis_id"] == "camera_movement"
    assert mod.main(["--axis", "camera_movement"]) == 0
    with pytest.raises(SystemExit):
        mod.main([])
    with pytest.raises(SystemExit):
        mod.main(["--axis"])
    with pytest.raises(SystemExit):
        mod.main(["--nope"])
    with pytest.raises(SystemExit):
        mod.load_axis_rows("not_an_axis")


def test_load_axis_rows_rejects_bad_payloads(tmp_path: Path, monkeypatch: Any) -> None:
    """Malformed axes.json fails closed."""
    mod = _load()
    cinema_dir = tmp_path / "cinema"
    cinema_dir.mkdir()
    monkeypatch.setattr(mod, "CINEMA", cinema_dir)
    (cinema_dir / "axes.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        mod.load_axis_rows("camera_movement")
    (cinema_dir / "axes.json").write_text(
        json.dumps({"camera_movement": "nope"}), encoding="utf-8"
    )
    with pytest.raises(SystemExit):
        mod.load_axis_rows("camera_movement")
    (cinema_dir / "axes.json").write_text(
        json.dumps({"camera_movement": {"file": "camera_movement.json"}}),
        encoding="utf-8",
    )
    (cinema_dir / "camera_movement.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        mod.load_axis_rows("camera_movement")
    (cinema_dir / "camera_movement.json").write_text(
        json.dumps([{"id": "move_dolly_in"}, "skip"]), encoding="utf-8"
    )
    rows = mod.load_axis_rows("camera_movement")
    assert len(rows) == 1


def test_cinema_clip_prompts_main_guard(monkeypatch: Any) -> None:
    """``python3 docs/cinema_clip_prompts.py --axis`` exits 0."""
    monkeypatch.setattr("sys.argv", ["cinema_clip_prompts.py", "--axis", "camera_movement"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(GEN_PY), run_name="__main__")
    assert exc.value.code == 0

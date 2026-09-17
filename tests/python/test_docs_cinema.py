"""Cinema Rack docs generator."""

from __future__ import annotations

import importlib.util
import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
GEN_PY = ROOT / "docs" / "generate_cinema_docs.py"


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("ez_generate_cinema_docs", GEN_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["ez_generate_cinema_docs"] = module
    spec.loader.exec_module(module)
    return module


def test_generate_cinema_docs_writes_axis_pages(tmp_path: Path) -> None:
    mod = _load()
    assert mod._cell("a | b", 20) == "a \\| b"
    assert "…" in mod._cell("x" * 200, 20)
    assert mod._flags({"still_ok": True, "motion_ok": False, "av_ok": True}) == "still, av"
    assert mod._flags({"still_ok": False, "motion_ok": False, "av_ok": False}) == "—"
    assert mod._yaml_str('say "hi"') == '"say \\"hi\\""'
    original_out = mod.OUT
    original_root = mod.ROOT
    original_cinema = mod.CINEMA
    original_assets = mod.ASSETS
    try:
        mod.OUT = tmp_path
        mod.ROOT = tmp_path
        mod.ASSETS = tmp_path / "assets"
        cinema = tmp_path / "custom_nodes" / "ez_prompt_enhance" / "cinema"
        cinema.mkdir(parents=True)
        axes = {
            "camera_movement": {
                "id": "camera_movement",
                "label": "Camera Movement",
                "file": "camera_movement.json",
                "splice_order": 1,
                "still_mode": "freeze",
                "i2v_include": True,
            }
        }
        rows = [
            {
                "id": "move_dolly_in",
                "label": "Dolly in",
                "clause": "The camera dollies in.",
                "still_ok": True,
                "motion_ok": True,
                "av_ok": True,
                "conflicts": ["fx_crash_zoom"],
            }
        ]
        (cinema / "axes.json").write_text(json.dumps(axes), encoding="utf-8")
        (cinema / "camera_movement.json").write_text(json.dumps(rows), encoding="utf-8")
        mod.CINEMA = cinema
        assert mod.main() == 0
        page = tmp_path / "camera_movement.md"
        assert page.is_file()
        text = page.read_text(encoding="utf-8")
        assert "Dolly in" in text
        assert "What's on this page" in text
        assert "| Id | Label | Example | Clause | Use on | Conflicts |" in text
        assert "| `move_dolly_in` |" in text
        assert "—" in text
        assert not (tmp_path / "camera_movement" / "move_dolly_in.md").is_file()
        manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
        assert len(manifest["pages"]) == 2
        assert manifest["pages"][1]["clips"] == "0"
        index = (tmp_path / "index.md").read_text(encoding="utf-8")
        assert "| Axis | Techniques | Clips | Page |" in index
    finally:
        mod.OUT = original_out
        mod.ROOT = original_root
        mod.CINEMA = original_cinema
        mod.ASSETS = original_assets


def test_generate_cinema_docs_rejects_bad_payloads(tmp_path: Path) -> None:
    mod = _load()
    original_cinema = mod.CINEMA
    original_out = mod.OUT
    original_root = mod.ROOT
    try:
        mod.CINEMA = tmp_path
        mod.OUT = tmp_path / "out"
        mod.ROOT = tmp_path
        (tmp_path / "out").mkdir()
        (tmp_path / "axes.json").write_text("[]", encoding="utf-8")
        try:
            mod.main()
            raise AssertionError("expected SystemExit")
        except SystemExit:
            pass
        (tmp_path / "axes.json").write_text(
            json.dumps(
                {
                    "camera_movement": {
                        "id": "camera_movement",
                        "label": "Move",
                        "file": "camera_movement.json",
                        "splice_order": 1,
                    },
                    "skip_me": "not-a-dict",
                }
            ),
            encoding="utf-8",
        )
        (tmp_path / "camera_movement.json").write_text("{}", encoding="utf-8")
        try:
            mod.main()
            raise AssertionError("expected SystemExit")
        except SystemExit:
            pass
    finally:
        mod.CINEMA = original_cinema
        mod.OUT = original_out
        mod.ROOT = original_root


def _hooks() -> Any:
    spec = importlib.util.spec_from_file_location(
        "ez_docs_hooks_cinema", ROOT / "docs" / "hooks.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["ez_docs_hooks_cinema"] = module
    spec.loader.exec_module(module)
    return module


def test_inject_cinema_nav_nests_under_start(monkeypatch: Any) -> None:
    hooks = _hooks()
    nav = [
        {
            "Start": [
                {"Cinema Rack": "create/cinema-rack.md"},
                {"Prompting": "prompting.md"},
            ]
        }
    ]
    out = hooks.inject_cinema_nav({"nav": nav})
    rack = out["nav"][0]["Start"][0]["Cinema Rack"]
    assert isinstance(rack, list)
    assert rack[0] == {"Playbook": "create/cinema-rack.md"}
    assert any("Camera Movement" in row for row in rack if isinstance(row, dict))
    assert out["nav"][0]["Start"][1] == {"Prompting": "prompting.md"}
    assert hooks.inject_cinema_nav({"nav": "nope"})["nav"] == "nope"


def test_inject_cinema_nav_fail_soft(monkeypatch: Any) -> None:
    hooks = _hooks()
    monkeypatch.setattr(hooks.Path, "is_file", lambda self: False)
    cfg = {"nav": [{"Cinema Rack": "create/cinema-rack.md"}]}
    assert hooks.inject_cinema_nav(cfg) is cfg
    monkeypatch.setattr(hooks.Path, "is_file", lambda self: True)
    monkeypatch.setattr(hooks.Path, "read_text", lambda self, encoding="utf-8": "{")
    assert hooks.inject_cinema_nav({"nav": []})["nav"] == []
    monkeypatch.setattr(
        hooks.Path, "read_text", lambda self, encoding="utf-8": '{"pages": 1}'
    )
    assert hooks.inject_cinema_nav({"nav": []})["nav"] == []
    monkeypatch.setattr(
        hooks.Path,
        "read_text",
        lambda self, encoding="utf-8": json.dumps(
            {
                "pages": [
                    {"kind": "axis", "id": "x", "label": "X", "path": ""},
                    "skip",
                    {"kind": "axis", "id": "y", "label": "Y", "path": "generated/cinema/y.md"},
                ]
            }
        ),
    )
    out = hooks.inject_cinema_nav(
        {"nav": ["keep", {"Cinema Rack": "create/cinema-rack.md"}]}
    )
    rack = out["nav"][1]["Cinema Rack"]
    assert out["nav"][0] == "keep"
    assert {"Y": "generated/cinema/y.md"} in rack


def test_generate_cinema_docs_writes_technique_page_when_clip_exists(
    tmp_path: Path,
) -> None:
    """Shipped mp4+poster become an Example thumb and a technique page."""
    mod = _load()
    original_out = mod.OUT
    original_cinema = mod.CINEMA
    original_assets = mod.ASSETS
    try:
        mod.OUT = tmp_path / "out"
        mod.ASSETS = tmp_path / "assets"
        cinema = tmp_path / "cinema"
        cinema.mkdir()
        (tmp_path / "out").mkdir()
        axes = {
            "camera_movement": {
                "id": "camera_movement",
                "label": "Camera Movement",
                "file": "camera_movement.json",
                "splice_order": 1,
                "still_mode": "freeze",
                "i2v_include": True,
            },
            "skip_me": "not-a-dict",
        }
        rows = [
            {
                "id": "move_dolly_in",
                "label": "Dolly in",
                "clause": "The camera dollies in.",
                "still_ok": True,
                "motion_ok": True,
                "av_ok": True,
                "conflicts": [],
            },
            "skip-row",
            {
                "id": "move_pan_left",
                "label": "Pan left",
                "clause": "The camera pans left.",
            },
        ]
        (cinema / "axes.json").write_text(json.dumps(axes), encoding="utf-8")
        (cinema / "camera_movement.json").write_text(json.dumps(rows), encoding="utf-8")
        clip_dir = tmp_path / "assets" / "camera_movement"
        clip_dir.mkdir(parents=True)
        (clip_dir / "move_dolly_in.mp4").write_bytes(b"mp4")
        (clip_dir / "move_dolly_in.jpg").write_bytes(b"jpg")
        mod.CINEMA = cinema
        mp4, jpg = mod.clip_files("camera_movement", "move_dolly_in")
        assert mp4.is_file() and jpg.is_file()
        assert mod.has_clip("camera_movement", "move_dolly_in")
        assert not mod.has_clip("camera_movement", "move_pan_left")
        assert mod.main() == 0
        axis = (tmp_path / "out" / "camera_movement.md").read_text(encoding="utf-8")
        assert "ez-cinema-thumb" in axis
        assert "move_dolly_in.md" in axis
        tech = tmp_path / "out" / "camera_movement" / "move_dolly_in.md"
        assert tech.is_file()
        text = tech.read_text(encoding="utf-8")
        assert "ez-cinema-clip" in text
        assert "preload=\"none\"" in text
        assert "What's on this page" in text
        assert "What this enables" in text
        assert not (tmp_path / "out" / "camera_movement" / "move_pan_left.md").is_file()
        manifest = json.loads((tmp_path / "out" / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["pages"][1]["clips"] == "1"
    finally:
        mod.OUT = original_out
        mod.CINEMA = original_cinema
        mod.ASSETS = original_assets


def test_generate_cinema_docs_shipped_tree() -> None:
    mod = _load()
    assert mod.main() == 0
    out = ROOT / "docs" / "generated" / "cinema"
    assert (out / "index.md").is_file()
    assert (out / "camera_movement.md").is_file()
    axis = (out / "camera_movement.md").read_text(encoding="utf-8")
    assert "| Id | Label | Example | Clause | Use on | Conflicts |" in axis
    index = (out / "index.md").read_text(encoding="utf-8")
    assert "| Axis | Techniques | Clips | Page |" in index
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    axes = [p for p in manifest["pages"] if p.get("kind") == "axis"]
    assert len(axes) == 13
    for page in axes:
        assert int(page["count"]) >= 100
        assert "clips" in page
    movement = next(p for p in axes if p["id"] == "camera_movement")
    assert int(movement["clips"]) >= 100
    tech = out / "camera_movement" / "move_dolly_in.md"
    assert tech.is_file()
    clip_page = tech.read_text(encoding="utf-8")
    assert "ez-cinema-clip" in clip_page
    assert "move_dolly_in.mp4" in clip_page


def test_inject_cinema_nav_ignores_technique_pages() -> None:
    """Nav stays playbook + 13 axes even after clip pages exist."""
    hooks = _hooks()
    nav = [{"Start": [{"Cinema Rack": "create/cinema-rack.md"}]}]
    out = hooks.inject_cinema_nav({"nav": nav})
    rack = out["nav"][0]["Start"][0]["Cinema Rack"]
    labels = [next(iter(row)) for row in rack if isinstance(row, dict)]
    assert labels[0] == "Playbook"
    assert "All axes" in labels
    assert "Camera Movement" in labels
    assert len(labels) == 15


def test_generate_cinema_docs_main_guard(monkeypatch: Any) -> None:
    monkeypatch.setattr("sys.argv", ["generate_cinema_docs.py"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(GEN_PY), run_name="__main__")
    assert exc.value.code == 0


def test_shipped_cinema_playbook_exists() -> None:
    page = ROOT / "docs" / "create" / "cinema-rack.md"
    text = page.read_text(encoding="utf-8")
    assert "What's on this page" in text
    assert "What this enables" in text
    assert "Safety impact" in text
    assert "5s" in text
    assert "docs/assets/cinema" in text

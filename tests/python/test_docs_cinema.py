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
    assert "..." in mod._cell("x" * 200, 20)
    assert mod._flags({"still_ok": True, "motion_ok": False, "av_ok": True}) == "still, av"
    assert mod._flags({"still_ok": False, "motion_ok": False, "av_ok": False}) == "-"
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
        assert "-" in text
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


def test_nav_ts_injects_cinema_rack_from_manifest() -> None:
    """Fumadocs nav.ts nests Playbook + axes under Cinema Rack from the manifest."""
    ts = (ROOT / "docs-site" / "lib" / "nav.ts").read_text(encoding="utf-8")
    assert "function cinemaChildren" in ts
    assert "injectGenerated" in ts
    assert 'title === "Cinema Rack"' in ts
    assert 'page.kind === "index" || !page.path' in ts
    assert "if (!file) return []" in ts
    payload = json.loads(
        (ROOT / "docs" / "generated" / "cinema" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    labels = ["Playbook", "All axes"]
    for page in payload.get("pages") or []:
        if not isinstance(page, dict) or page.get("kind") == "index":
            continue
        if str(page.get("path") or ""):
            labels.append(str(page.get("label") or page.get("id") or "axis"))
    assert labels[0] == "Playbook"
    assert "All axes" in labels
    assert "Camera Movement" in labels
    assert len(labels) == 15


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


def test_cinema_manifest_omits_technique_pages_from_nav() -> None:
    """Clip technique pages stay off the sidebar; nav is playbook + 13 axes."""
    payload = json.loads(
        (ROOT / "docs" / "generated" / "cinema" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    kinds = {page.get("kind") for page in payload.get("pages") or [] if isinstance(page, dict)}
    assert kinds <= {"index", "axis"}
    axes = [
        page
        for page in payload.get("pages") or []
        if isinstance(page, dict) and page.get("kind") == "axis" and page.get("path")
    ]
    assert len(axes) == 13


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

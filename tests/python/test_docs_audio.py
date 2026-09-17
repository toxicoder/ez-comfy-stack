"""Audio Rack docs generator."""

from __future__ import annotations

import importlib.util
import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
GEN_PY = ROOT / "docs" / "generate_audio_docs.py"


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("ez_generate_audio_docs", GEN_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["ez_generate_audio_docs"] = module
    spec.loader.exec_module(module)
    return module


def test_generate_audio_docs_writes_axis_pages(tmp_path: Path) -> None:
    mod = _load()
    assert mod._cell("a | b", 20) == "a \\| b"
    assert "…" in mod._cell("x" * 200, 20)
    assert mod._flags({"vocal_ok": True, "instrumental_ok": False, "podcast_ok": True}) == (
        "vocal, podcast"
    )
    assert mod._flags({"vocal_ok": False, "instrumental_ok": False, "podcast_ok": False}) == "—"
    original_out = mod.OUT
    original_root = mod.ROOT
    try:
        mod.OUT = tmp_path
        mod.ROOT = tmp_path
        audio_dir = tmp_path / "custom_nodes" / "ez_prompt_enhance" / "audio"
        audio_dir.mkdir(parents=True)
        axes = {
            "genre_style": {
                "id": "genre_style",
                "label": "Genre",
                "file": "genre_style.json",
                "splice_order": 1,
                "vocal_include": True,
                "instrumental_include": True,
            }
        }
        rows = [
            {
                "id": "gen_boom_bap",
                "label": "Boom bap",
                "clause": "Dusty pocket.",
                "tags": "boom bap, hip-hop",
                "vocal_ok": True,
                "instrumental_ok": True,
                "podcast_ok": True,
                "conflicts": ["gen_four_on_floor"],
            }
        ]
        (audio_dir / "axes.json").write_text(json.dumps(axes), encoding="utf-8")
        (audio_dir / "genre_style.json").write_text(json.dumps(rows), encoding="utf-8")
        mod.AUDIO = audio_dir
        assert mod.main() == 0
        page = tmp_path / "genre_style.md"
        assert page.is_file()
        text = page.read_text(encoding="utf-8")
        assert "Boom bap" in text
        assert "What's on this page" in text
        manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
        assert len(manifest["pages"]) == 2
    finally:
        mod.OUT = original_out
        mod.ROOT = original_root


def test_generate_audio_docs_rejects_bad_payloads(tmp_path: Path) -> None:
    mod = _load()
    original_audio = mod.AUDIO
    original_out = mod.OUT
    original_root = mod.ROOT
    try:
        mod.AUDIO = tmp_path
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
                    "genre_style": {
                        "id": "genre_style",
                        "label": "Genre",
                        "file": "genre_style.json",
                        "splice_order": 1,
                    },
                    "skip_me": "not-a-dict",
                }
            ),
            encoding="utf-8",
        )
        (tmp_path / "genre_style.json").write_text("{}", encoding="utf-8")
        try:
            mod.main()
            raise AssertionError("expected SystemExit")
        except SystemExit:
            pass
        (tmp_path / "genre_style.json").unlink()
        (tmp_path / "axes.json").write_text(
            json.dumps(
                {
                    "genre_style": {
                        "id": "genre_style",
                        "label": "Genre",
                        "file": "genre_style.json",
                        "splice_order": 1,
                    }
                }
            ),
            encoding="utf-8",
        )
        assert mod.main() == 0
    finally:
        mod.AUDIO = original_audio
        mod.OUT = original_out
        mod.ROOT = original_root


def _hooks() -> Any:
    spec = importlib.util.spec_from_file_location(
        "ez_docs_hooks_audio", ROOT / "docs" / "hooks.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["ez_docs_hooks_audio"] = module
    spec.loader.exec_module(module)
    return module


def test_inject_audio_nav_nests_under_start(monkeypatch: Any) -> None:
    hooks = _hooks()
    nav = [
        {
            "Start": [
                {"Audio Rack": "create/audio-rack.md"},
                {"Prompting": "prompting.md"},
            ]
        }
    ]
    out = hooks.inject_audio_nav({"nav": nav})
    rack = out["nav"][0]["Start"][0]["Audio Rack"]
    assert isinstance(rack, list)
    assert rack[0] == {"Playbook": "create/audio-rack.md"}
    assert any("Genre" in row for row in rack if isinstance(row, dict))
    assert out["nav"][0]["Start"][1] == {"Prompting": "prompting.md"}
    assert hooks.inject_audio_nav({"nav": "nope"})["nav"] == "nope"


def test_inject_audio_nav_fail_soft(monkeypatch: Any) -> None:
    hooks = _hooks()
    monkeypatch.setattr(hooks.Path, "is_file", lambda self: False)
    cfg = {"nav": [{"Audio Rack": "create/audio-rack.md"}]}
    assert hooks.inject_audio_nav(cfg) is cfg
    monkeypatch.setattr(hooks.Path, "is_file", lambda self: True)
    monkeypatch.setattr(hooks.Path, "read_text", lambda self, encoding="utf-8": "{")
    assert hooks.inject_audio_nav({"nav": []})["nav"] == []
    monkeypatch.setattr(
        hooks.Path, "read_text", lambda self, encoding="utf-8": '{"pages": 1}'
    )
    assert hooks.inject_audio_nav({"nav": []})["nav"] == []
    monkeypatch.setattr(
        hooks.Path,
        "read_text",
        lambda self, encoding="utf-8": json.dumps(
            {
                "pages": [
                    {"kind": "axis", "id": "x", "label": "X", "path": ""},
                    "skip",
                    {"kind": "axis", "id": "y", "label": "Y", "path": "generated/audio/y.md"},
                ]
            }
        ),
    )
    out = hooks.inject_audio_nav(
        {"nav": ["keep", {"Audio Rack": "create/audio-rack.md"}]}
    )
    rack = out["nav"][1]["Audio Rack"]
    assert out["nav"][0] == "keep"
    assert {"Y": "generated/audio/y.md"} in rack


def test_generate_audio_docs_shipped_tree() -> None:
    mod = _load()
    assert mod.main() == 0
    out = ROOT / "docs" / "generated" / "audio"
    assert (out / "index.md").is_file()
    assert (out / "genre_style.md").is_file()
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    axes = [p for p in manifest["pages"] if p.get("kind") == "axis"]
    assert len(axes) == 13
    for page in axes:
        assert int(page["count"]) >= 100


def test_generate_audio_docs_main_guard(monkeypatch: Any) -> None:
    monkeypatch.setattr("sys.argv", ["generate_audio_docs.py"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(GEN_PY), run_name="__main__")
    assert exc.value.code == 0


def test_shipped_audio_playbook_exists() -> None:
    page = ROOT / "docs" / "create" / "audio-rack.md"
    text = page.read_text(encoding="utf-8")
    assert "What's on this page" in text
    assert "What this enables" in text
    assert "Safety impact" in text

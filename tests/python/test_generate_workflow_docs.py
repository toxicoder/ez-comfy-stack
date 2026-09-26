"""Hermetic tests for docs/generate_workflow_docs.py.

Stdlib + the generator module. No MkDocs, Docker, or network.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
GEN_PY = ROOT / "docs" / "generate_workflow_docs.py"


def _load() -> Any:
    """Load docs/generate_workflow_docs.py as a module.

    Returns:
        Loaded generator module.
    """
    docs_dir = str(ROOT / "docs")
    if docs_dir not in sys.path:
        sys.path.insert(0, docs_dir)
    spec = importlib.util.spec_from_file_location("ez_generate_workflow_docs_unit", GEN_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _mini_graph() -> dict[str, Any]:
    """Return a tiny Klein-like graph for unit tests.

    Returns:
        Comfy workflow dict.
    """
    return {
        "id": "still-draft",
        "nodes": [
            {
                "id": 1,
                "type": "UNETLoader",
                "title": "Klein 4B",
                "pos": [40, 80],
                "widgets_values": ["flux-2-klein-4b-fp8.safetensors", "default"],
                "inputs": [],
                "outputs": [{"name": "MODEL", "links": [1]}],
            },
            {
                "id": 7,
                "type": "KSampler",
                "title": "KSampler",
                "pos": [400, 80],
                "widgets_values": [42, "fixed", 4, 1.0, "euler", "simple", 1.0],
                "inputs": [{"name": "model", "link": 1}],
                "outputs": [{"name": "LATENT", "links": []}],
            },
            {
                "id": 10,
                "type": "Note",
                "title": "Operator note",
                "pos": [40, 400],
                "widgets_values": ["## stills/still-draft\n\nOccupancy: klein.\n"],
                "inputs": [],
                "outputs": [],
            },
        ],
        "groups": [],
        "extra": {
            "lab_rel": "stills/still-draft",
            "lab_description": "Draft still",
            "lab_app_mode": {"occupancy": "klein"},
        },
    }


def test_extract_note() -> None:
    """Note widget text is the purpose body."""
    gen = _load()
    note = gen.extract_note(_mini_graph()["nodes"])
    assert "Occupancy: klein" in note


def test_vhs_dict_layout() -> None:
    """VHS dict widgets match the full key layout."""
    gen = _load()
    from workflow_nodes import encyclopedia

    spec = encyclopedia()["VHS_VideoCombine"]
    values = {
        "frame_rate": 24,
        "loop_count": 0,
        "filename_prefix": "ez_wan_draft_video",
        "format": "video/h264-mp4",
        "pix_fmt": "yuv420p",
        "crf": 18,
        "save_metadata": True,
        "trim_to_audio": False,
        "pingpong": False,
        "save_output": True,
    }
    layout = gen.match_layout(spec, values)
    assert layout is not None
    names = [str(item.get("name")) for item in layout]
    assert "frame_rate" in names
    assert "save_output" in names
    assert gen.read_widget_value(values, layout[0]) == 24


def test_vhs_short_variant() -> None:
    """Podcast bumper VHS dict matches the short variant."""
    gen = _load()
    from workflow_nodes import encyclopedia

    spec = encyclopedia()["VHS_VideoCombine"]
    values = {
        "frame_rate": 16,
        "loop_count": 0,
        "filename_prefix": "ez_radio_bumper",
        "format": "video/h264-mp4",
        "pingpong": True,
        "save_output": True,
    }
    layout = gen.match_layout(spec, values)
    assert layout is not None
    assert len(layout) == 6


def test_group_mermaid() -> None:
    """Large grouped graphs emit a group mermaid, not 239 node boxes."""
    gen = _load()
    data = {
        "nodes": [{"id": i, "type": "Note", "title": f"n{i}", "pos": [10, 10 * i]} for i in range(30)],
        "groups": [{"title": "1. Identity (Klein)", "bounding": [0, 0, 800, 400]}],
    }
    text = gen.mermaid_for_graph(data)
    assert "flowchart TB" in text
    assert "Identity" in text


def test_render_graph_page_chrome_and_params() -> None:
    """A mini graph page has required chrome and KSampler widgets."""
    gen = _load()
    from workflow_nodes import ACE_KEYSCALE_CHOICES, ACE_LANGUAGE_CHOICES, encyclopedia

    page = gen.render_graph_page(
        "stills/still-draft",
        _mini_graph(),
        encyclopedia(),
        styles={},
        ace_language=ACE_LANGUAGE_CHOICES,
        ace_keyscale=ACE_KEYSCALE_CHOICES,
    )
    assert page.startswith("---\n")
    assert "# stills/still-draft\n" in page
    assert "**What's on this page**" in page
    assert "**What this enables**" in page
    assert "## Node parameter reference" in page
    assert "`seed`" in page
    assert "`control_after_generate`" in page
    assert "euler" in page
    assert "| 1 |" in page
    assert "| 7 |" in page
    assert page.endswith("\n")
    assert "\n\n\n" not in page


def test_inject_nav_nests_workflow_details() -> None:
    """Workflow details nav entry expands to a nested tree."""
    gen = _load()
    nav = [
        {"Home": "index.md"},
        {
            "Create": [
                {"Workflow catalog": "studio-workflows.md"},
                {"Workflow details": "create/workflows-index.md"},
            ]
        },
    ]
    out = gen.inject_nav(
        nav,
        [
            {"id": "index", "path": "generated/workflows/index.md", "lane": "index", "kind": "index"},
            {"id": "stills/still-draft", "path": "generated/workflows/stills/still-draft.md", "lane": "klein", "kind": "graph"},
        ],
    )
    create = out[1]["Create"]
    details = next(item for item in create if "Workflow details" in item)
    children = details["Workflow details"]
    assert any("Overview" in item for item in children if isinstance(item, dict))
    klein = next(item for item in children if isinstance(item, dict) and "klein" in item)
    assert klein["klein"][0]["still-draft"] == "generated/workflows/stills/still-draft.md"


def test_main_calls_generate(monkeypatch: Any) -> None:
    """CLI main parses --force and writes via generate()."""
    gen = _load()
    called: dict[str, bool] = {"hit": False}

    def fake_generate(**kwargs: Any) -> dict[str, str]:
        del kwargs
        called["hit"] = True
        return {"generated/workflows/index.md": "# x\n"}

    monkeypatch.setattr(gen, "generate", fake_generate)
    assert gen.main(["--force"]) == 0
    assert called["hit"] is True


def test_expand_choices_image_formats_and_cinema_recipes() -> None:
    gen = _load()
    formats = gen.expand_choices(
        {"choices_from": "image_formats"},
        styles={},
        ace_language=[],
        ace_keyscale=[],
    )
    ids = {row["id"] for row in formats}
    assert "Custom" in ids
    assert "16:9 LTX feeder (1280x704)" in ids
    video = gen.expand_choices(
        {"choices_from": "video_formats"},
        styles={},
        ace_language=[],
        ace_keyscale=[],
    )
    video_ids = {row["id"] for row in video}
    assert "Custom" in video_ids
    assert "LTX - 16:9 YouTube (1280x704)" in video_ids
    families = gen.expand_choices(
        {"choices_from": "video_families"},
        styles={},
        ace_language=[],
        ace_keyscale=[],
    )
    family_ids = {row["id"] for row in families}
    assert "Wan 5B" in family_ids
    assert "LTX-2.5" in family_ids
    recipes = gen.expand_choices(
        {"choices_from": "cinema_recipes"},
        styles={},
        ace_language=[],
        ace_keyscale=[],
    )
    assert recipes[0]["id"] == "none"
    assert any(row["id"] == "Golden wide" for row in recipes)
    modes = gen.expand_choices(
        {"choices_from": "image_modes"},
        styles={},
        ace_language=[],
        ace_keyscale=[],
    )
    mode_ids = {row["id"] for row in modes}
    assert "Photoreal still" in mode_ids
    assert "Background swap" in mode_ids
    assert len(modes) == 100
    cats = gen.expand_choices(
        {"choices_from": "image_mode_categories"},
        styles={},
        ace_language=[],
        ace_keyscale=[],
    )
    cat_ids = {row["id"] for row in cats}
    assert "Generate" in cat_ids
    assert "Scene" in cat_ids


def test_format_choice_helpers_missing_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gen = _load()
    monkeypatch.setattr(gen, "FORMATS_FILE", tmp_path / "no-formats.json")
    monkeypatch.setattr(gen, "VIDEO_FORMATS_FILE", tmp_path / "no-video.json")
    monkeypatch.setattr(gen, "RECIPES_FILE", tmp_path / "no-recipes.json")
    monkeypatch.setattr(gen, "MODES_FILE", tmp_path / "no-modes.json")
    assert gen._image_mode_choices() == []
    assert gen._image_mode_category_choices() == []
    assert gen._image_format_choices() == []
    assert gen._video_format_choices() == []
    assert gen._video_family_choices() == []
    assert gen._cinema_recipe_choices() == [
        {"id": "none", "description": "Off. Style + Prompt own look."}
    ]
    (tmp_path / "no-formats.json").write_text("[]", encoding="utf-8")
    (tmp_path / "no-video.json").write_text("[]", encoding="utf-8")
    (tmp_path / "no-recipes.json").write_text("{}", encoding="utf-8")
    assert gen._image_format_choices() == []
    assert gen._video_format_choices() == []
    assert gen._video_family_choices() == []
    assert gen._cinema_recipe_choices()[0]["id"] == "none"
    (tmp_path / "no-formats.json").write_text('{"formats": [1, {"id": ""}]}', encoding="utf-8")
    (tmp_path / "no-video.json").write_text(
        '{"formats": [1, {"id": ""}], "families": {"wan": 1}}', encoding="utf-8"
    )
    (tmp_path / "no-recipes.json").write_text("[1, {\"id\": \"rec_x\", \"label\": \"X\"}]", encoding="utf-8")
    assert gen._image_format_choices() == []
    assert gen._video_format_choices() == []
    assert gen._video_family_choices() == []
    rows = gen._cinema_recipe_choices()
    assert {"id": "X", "description": "rec_x"} in rows
    (tmp_path / "no-video.json").write_text(
        '{"formats": [{"id": "custom", "label": "Custom", "width": 0, "height": 0}, '
        '{"id": "wan_16_9", "label": "Wan 16:9", "family": "wan", "width": 832, '
        '"height": 480}], "families": {"wan": {"label": "Wan 5B", "grid": 16}}}',
        encoding="utf-8",
    )
    video_rows = gen._video_format_choices()
    assert video_rows[0]["id"] == "Custom"
    assert "832x480" in video_rows[1]["description"]
    family_rows = gen._video_family_choices()
    assert family_rows[0]["id"] == "Wan 5B"
    (tmp_path / "no-modes.json").write_text("[]", encoding="utf-8")
    assert gen._image_mode_choices() == []
    assert gen._image_mode_category_choices() == []
    (tmp_path / "no-modes.json").write_text("1", encoding="utf-8")
    assert gen._modes_payload() == {"modes": [], "categories": []}
    (tmp_path / "no-modes.json").write_text(
        '[1, {"id": "a", "label": "A", "category": ""}, '
        '{"id": "b", "label": "B", "category": "one"}, '
        '{"id": "c", "label": "C", "category": "one"}]',
        encoding="utf-8",
    )
    assert gen._image_mode_choices()[0]["id"] == "A"
    cats = gen._image_mode_category_choices()
    assert cats[0]["id"] == "One"
    assert len(cats) == 1
    (tmp_path / "no-modes.json").write_text(
        '{"categories": [1, {"id": "one", "label": "One"}], '
        '"modes": [1, {"id": "", "label": ""}, {"id": "a", "label": "A", '
        '"category": "one", "instruction": ""}]}',
        encoding="utf-8",
    )
    assert gen._image_mode_choices()[0]["id"] == "A"
    assert gen._image_mode_category_choices()[0]["id"] == "One"
    (tmp_path / "no-modes.json").write_text('{"modes": {}}', encoding="utf-8")
    assert gen._image_mode_choices() == []
    assert gen._image_mode_category_choices() == []

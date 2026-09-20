"""Hermetic tests for ez_image creator-mode catalog and EZImageMode."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_image  # noqa: E402
from ez_image import modes as md  # noqa: E402
from ez_image.modes import (  # noqa: E402
    DEFAULT_MODE_ID,
    ENHANCE_MODE_COMBO,
    ENHANCE_MODES,
    EZImageMode,
    catalog_payload,
    category_combo_labels,
    default_category_label,
    default_mode_id,
    default_mode_label,
    get_category,
    get_mode,
    load_categories,
    load_modes,
    mode_combo_labels,
    modes_for_category,
    resolve_mode,
    splice_mode_context,
)

_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,47}$")


@pytest.fixture(autouse=True)
def _reset_mode_cache() -> Iterator[None]:
    md.reset_mode_cache_for_tests()
    yield
    md.reset_mode_cache_for_tests()


def test_pack_exports_image_mode() -> None:
    assert ez_image.NODE_CLASS_MAPPINGS["EZImageMode"] is EZImageMode
    assert ez_image.NODE_DISPLAY_NAME_MAPPINGS["EZImageMode"] == "Creator mode"
    assert EZImageMode.CATEGORY == "ez-comfy/image"
    assert EZImageMode.RETURN_NAMES == ("context", "enhance_mode", "prefix")
    assert EZImageMode.RETURN_TYPES[1] == ENHANCE_MODE_COMBO


def test_enhance_mode_output_matches_klein_combo() -> None:
    from ez_prompt_enhance.nodes import EZKleinPromptEnhance

    klein_modes = EZKleinPromptEnhance.INPUT_TYPES()["required"]["mode"][0]
    assert EZImageMode.RETURN_TYPES[1] == klein_modes
    assert klein_modes == ["t2i", "edit", "identity", "text_swap"]


def test_mode_catalog_is_one_hundred_unique_creator_modes() -> None:
    rows = load_modes()
    assert len(rows) == 100
    ids = [row.id for row in rows]
    labels = [row.label for row in rows]
    assert len(ids) == len(set(ids))
    assert len({label.casefold() for label in labels}) == len(labels)
    assert mode_combo_labels() == labels
    cats = [row.id for row in load_categories()]
    assert len(cats) == 10
    assert cats[0] == "generate"
    assert cats[-1] == "fix"
    by_cat: dict[str, int] = {}
    for row in rows:
        assert _ID_RE.match(row.id), row.id
        assert row.label
        assert row.category in cats
        assert row.enhance_mode in ENHANCE_MODES
        assert row.needs_ref in {0, 1, 2}
        assert row.instruction
        assert row.prefix.startswith("ez_")
        by_cat[row.category] = by_cat.get(row.category, 0) + 1
    assert by_cat == {cid: 10 for cid in cats}
    face = get_mode("Face swap (best effort)")
    assert face.id == "ref_face_swap"
    assert face.needs_ref == 2
    assert "original character" in face.instruction.casefold()
    assert "real-person" in face.instruction.casefold()


def test_default_mode_is_photoreal_generate() -> None:
    assert default_mode_id() == DEFAULT_MODE_ID
    assert default_mode_label() == "Photoreal still"
    assert default_category_label() == "Generate"
    spec = get_mode(default_mode_label())
    assert spec.id == "gen_photoreal"
    assert spec.enhance_mode == "t2i"
    assert spec.needs_ref == 0
    unknown = get_mode("not-a-real-mode")
    assert unknown.id == "gen_photoreal"


def test_unknown_mode_falls_back_to_category_then_default() -> None:
    sky = get_mode("not-a-real-mode", category="Scene")
    assert sky.category == "edit_scene"
    assert sky.id == "edit_bg_swap"
    assert get_category("").id == "generate"
    assert get_category("edit_scene").id == "edit_scene"
    assert get_category("Text").id == "text"
    assert get_category("nope").id == "generate"
    scene_modes = modes_for_category("edit_scene")
    assert len(scene_modes) == 10
    assert scene_modes[0].id == "edit_bg_swap"


def test_resolve_mode_splices_instruction_and_look_context() -> None:
    none = resolve_mode("Photoreal still")
    assert none.context.startswith("Generate a photoreal still")
    assert none.enhance_mode == "t2i"
    assert none.prefix == "ez_gen_photoreal"
    assert none.needs_ref == 0
    swapped = resolve_mode("Background swap", extra_context="Golden wide splice")
    assert "Keep the subject" in swapped.context
    assert "Golden wide splice" in swapped.context
    assert swapped.enhance_mode == "edit"
    assert swapped.prefix == "ez_edit_bg_swap"
    assert splice_mode_context("", "") == ""
    assert splice_mode_context("A", "") == "A"


def test_ez_image_mode_run_packs_ui_and_result() -> None:
    types = EZImageMode.INPUT_TYPES()
    required = types["required"]
    assert required["category"][1]["default"] == default_category_label()
    assert required["mode"][1]["default"] == default_mode_label()
    assert "Photoreal still" in required["mode"][0]
    assert len(required["mode"][0]) == 100
    packed = EZImageMode().run("Generate", "Change text", context="look splice")
    assert packed["result"][1] == "text_swap"
    assert packed["result"][2] == "ez_edit_change_text"
    assert "look splice" in packed["result"][0]
    assert "Change text" in packed["ui"]["text"][0]


def test_mode_helpers_cover_remaining_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert md._as_str(None) == ""
    assert md._as_str(12) == "12"
    assert md._as_int(True, 4) == 4
    assert md._as_int(2.8, 0) == 2
    assert md._as_int("", 5) == 5
    assert md._as_int("zz", 5) == 5
    assert md._clamp_needs_ref(-1) == 0
    assert md._clamp_needs_ref(9) == 2
    assert md._normalize_enhance_mode("EDIT") == "edit"
    assert md._normalize_enhance_mode("nope") == "t2i"
    assert catalog_payload()["default_id"] == "gen_photoreal"
    assert category_combo_labels()[0] == "Generate"
    assert md.category_label("generate") == "Generate"
    assert md.category_label("missing_cat") == "Missing Cat"
    assert md.category_label("") == "Generate"
    monkeypatch.setattr(md, "default_mode_id", lambda: "missing-id")
    assert default_mode_label() == load_modes()[0].label
    import ez_image.modes as mode_mod

    monkeypatch.setattr(mode_mod, "default_category_label", lambda: "not-in-list")
    monkeypatch.setattr(mode_mod, "default_mode_label", lambda: "not-in-list")
    types = EZImageMode.INPUT_TYPES()
    assert types["required"]["category"][1]["default"] == category_combo_labels()[0]
    assert types["required"]["mode"][1]["default"] == mode_combo_labels()[0]


def test_mode_catalog_file_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(md, "MODES_PATH", missing)
    md.reset_mode_cache_for_tests()
    with pytest.raises(ValueError, match="missing"):
        load_modes()
    missing.write_text("[]", encoding="utf-8")
    md.reset_mode_cache_for_tests()
    with pytest.raises(ValueError, match="nonempty list"):
        load_modes()
    missing.write_text("1", encoding="utf-8")
    md.reset_mode_cache_for_tests()
    with pytest.raises(ValueError, match="object or a list"):
        md._catalog_payload()
    missing.write_text('{"modes": []}', encoding="utf-8")
    md.reset_mode_cache_for_tests()
    with pytest.raises(ValueError, match="nonempty"):
        load_modes()
    missing.write_text('{"modes": [1]}', encoding="utf-8")
    md.reset_mode_cache_for_tests()
    with pytest.raises(ValueError, match="objects"):
        load_modes()
    missing.write_text(
        '{"modes": [{"id": "", "label": "x", "category": "g"}]}',
        encoding="utf-8",
    )
    md.reset_mode_cache_for_tests()
    with pytest.raises(ValueError, match="id, label, and category"):
        load_modes()
    missing.write_text(
        '{"default_id": "", "modes": [{"id": "ok", "label": "Ok", '
        '"category": "g", "prefix": ""}]}',
        encoding="utf-8",
    )
    md.reset_mode_cache_for_tests()
    row = load_modes()[0]
    assert row.prefix == "ez_image_studio"
    assert default_mode_id() == DEFAULT_MODE_ID
    cats = load_categories()
    assert cats[0].id == "g"
    assert catalog_payload()["modes"][0]["id"] == "ok"


def test_list_payload_and_empty_categories(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    listed = tmp_path / "listed.json"
    listed.write_text(
        '[{"id": "a", "label": "A", "category": "one", '
        '"enhance_mode": "t2i", "needs_ref": 0, "instruction": "do a", '
        '"prefix": "ez_a"}, '
        '{"id": "c", "label": "C", "category": "one", '
        '"enhance_mode": "t2i", "needs_ref": 0, "instruction": "do c", '
        '"prefix": "ez_c"}, '
        '{"id": "b", "label": "B", "category": "two", '
        '"enhance_mode": "edit", "needs_ref": 1, "instruction": "do b", '
        '"prefix": "ez_b"}]',
        encoding="utf-8",
    )
    monkeypatch.setattr(md, "MODES_PATH", listed)
    md.reset_mode_cache_for_tests()
    rows = load_modes()
    assert len(rows) == 3
    cats = load_categories()
    assert [row.id for row in cats] == ["one", "two"]
    assert get_category("").id == "one"
    empty_cats = tmp_path / "empty_cats.json"
    empty_cats.write_text(
        '{"categories": [1, {"id": "", "label": "x"}, '
        '{"id": "one", "label": "One"}, {"id": "one", "label": "Dup"}], '
        '"modes": [{"id": "a", "label": "A", "category": "one", '
        '"instruction": "x", "prefix": "ez_a"}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(md, "MODES_PATH", empty_cats)
    md.reset_mode_cache_for_tests()
    assert [row.id for row in load_categories()] == ["one"]
    monkeypatch.setattr(md, "load_categories", lambda: ())
    assert md.category_label("") == "Generate"
    assert get_category("whatever").id == "one"
    assert category_combo_labels() == ["One"]

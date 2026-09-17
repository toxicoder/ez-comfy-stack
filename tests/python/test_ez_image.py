"""Hermetic tests for ez_image snap and match nodes.

Stdlib only. No Comfy, torch, Docker, or GPU.
"""

from __future__ import annotations

import inspect
import re
import sys
import types
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_image  # noqa: E402
from ez_image import formats as fmt  # noqa: E402
from ez_image.formats import (  # noqa: E402
    CUSTOM_ID,
    LOOK_NONE,
    MAX_DIM,
    MIN_DIM,
    FormatSpec,
    clamp_dim,
    default_format_id,
    default_format_label,
    format_combo_labels,
    get_format,
    load_formats,
    look_combo_labels,
    resolve_canvas,
    splice_look,
)
from ez_image.nodes import (  # noqa: E402
    GRID,
    EZImageFormat,
    EZMatchImageSize,
    EZSnapImage,
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
    _resize_bhwc,
    snap_dim,
)


@pytest.fixture(autouse=True)
def _reset_format_cache() -> Iterator[None]:
    fmt.reset_format_cache_for_tests()
    yield
    fmt.reset_format_cache_for_tests()


class _FakeImg:
    """Stand-in for a Comfy IMAGE tensor (BHWC)."""

    def __init__(self, height: int, width: int) -> None:
        self.shape = (1, height, width, 3)
        self.ops: list[tuple[int, int]] = []

    def movedim(self, src: int, dest: int) -> _FakeImg:
        self.ops.append((src, dest))
        return self


def test_pack_mappings_and_category() -> None:
    assert set(NODE_CLASS_MAPPINGS) == {
        "EZSnapImage",
        "EZMatchImageSize",
        "EZImageFormat",
    }
    assert ez_image.NODE_CLASS_MAPPINGS == NODE_CLASS_MAPPINGS
    assert ez_image.WEB_DIRECTORY == "./js"
    assert NODE_DISPLAY_NAME_MAPPINGS["EZSnapImage"] == "Snap image (div 16)"
    assert NODE_DISPLAY_NAME_MAPPINGS["EZMatchImageSize"] == "Match image size"
    assert NODE_DISPLAY_NAME_MAPPINGS["EZImageFormat"] == "Format / platform"
    for cls in NODE_CLASS_MAPPINGS.values():
        assert getattr(cls, "CATEGORY") == "ez-comfy/image"


def test_snap_dim_floors_to_klein_grid() -> None:
    assert GRID == 16
    assert snap_dim(15) == 16
    assert snap_dim(16) == 16
    assert snap_dim(17) == 16
    assert snap_dim(1080) == 1072
    assert snap_dim(1920) == 1920
    assert snap_dim(0) == 16
    assert snap_dim(-4) == 16


def test_input_types_are_image_only() -> None:
    snap = EZSnapImage.INPUT_TYPES()
    assert snap["required"]["image"][0] == "IMAGE"
    match = EZMatchImageSize.INPUT_TYPES()
    assert match["required"]["image"][0] == "IMAGE"
    assert match["required"]["size_src"][0] == "IMAGE"
    assert EZSnapImage.RETURN_TYPES == ("IMAGE",)
    assert EZMatchImageSize.RETURN_TYPES == ("IMAGE",)
    assert EZMatchImageSize.RETURN_NAMES == ("image",)


def test_torch_is_lazy_inside_run() -> None:
    resize_src = inspect.getsource(_resize_bhwc)
    assert "import torch" in resize_src
    assert "common_upscale" in resize_src
    nodes_path = Path(inspect.getfile(EZSnapImage))
    head, _, _ = nodes_path.read_text(encoding="utf-8").partition("def snap_dim")
    assert "import torch" not in head


def test_snap_and_match_noop_when_aligned() -> None:
    aligned = _FakeImg(1024, 1920)
    assert EZSnapImage().run(aligned)[0] is aligned
    odd = _FakeImg(1080, 1920)
    assert EZMatchImageSize().run(odd, odd)[0] is odd


def test_resize_prefers_comfy_upscale(monkeypatch: pytest.MonkeyPatch) -> None:
    img = _FakeImg(32, 32)
    seen: dict[str, object] = {}

    def upscale(
        nchw: _FakeImg,
        width: int,
        height: int,
        method: str,
        crop: str,
    ) -> _FakeImg:
        seen["args"] = (width, height, method, crop)
        return nchw

    utils = types.SimpleNamespace(common_upscale=upscale)
    monkeypatch.setitem(sys.modules, "comfy", types.SimpleNamespace(utils=utils))
    monkeypatch.setitem(sys.modules, "comfy.utils", utils)
    out = _resize_bhwc(img, 16, 16)
    assert out is img
    assert seen["args"] == (16, 16, "lanczos", "disabled")
    assert img.ops == [(-1, 1), (1, -1)]


def test_resize_falls_back_to_torch(monkeypatch: pytest.MonkeyPatch) -> None:
    img = _FakeImg(32, 48)
    seen: dict[str, object] = {}

    def interpolate(
        nchw: _FakeImg,
        size: tuple[int, int],
        mode: str,
        align_corners: bool,
    ) -> _FakeImg:
        seen["args"] = (size, mode, align_corners)
        return nchw

    functional = types.SimpleNamespace(interpolate=interpolate)
    nn = types.SimpleNamespace(functional=functional)
    monkeypatch.setitem(sys.modules, "comfy.utils", None)
    monkeypatch.setitem(sys.modules, "torch", types.SimpleNamespace(nn=nn))
    monkeypatch.setitem(sys.modules, "torch.nn", nn)
    monkeypatch.setitem(sys.modules, "torch.nn.functional", functional)
    out = _resize_bhwc(img, 16, 32)
    assert out is img
    assert seen["args"] == ((16, 32), "bicubic", False)


def test_resize_fails_without_comfy_or_torch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "comfy.utils", None)
    monkeypatch.setitem(sys.modules, "torch", None)
    monkeypatch.setitem(sys.modules, "torch.nn", None)
    monkeypatch.setitem(sys.modules, "torch.nn.functional", None)
    with pytest.raises(RuntimeError, match="common_upscale or torch"):
        _resize_bhwc(_FakeImg(8, 8), 16, 16)


def test_snap_and_match_run_resize_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[int, int]] = []

    def upscale(
        nchw: _FakeImg,
        width: int,
        height: int,
        method: str,
        crop: str,
    ) -> _FakeImg:
        del method, crop
        seen.append((height, width))
        return nchw

    utils = types.SimpleNamespace(common_upscale=upscale)
    monkeypatch.setitem(sys.modules, "comfy", types.SimpleNamespace(utils=utils))
    monkeypatch.setitem(sys.modules, "comfy.utils", utils)
    src = _FakeImg(1080, 1920)
    EZSnapImage().run(src)
    assert seen[-1] == (1072, 1920)
    edited = _FakeImg(1072, 1920)
    EZMatchImageSize().run(edited, src)
    assert seen[-1] == (1080, 1920)


_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,47}$")
_BANNED_LOOK = (
    "kodak",
    "pixar",
    "ghibli",
    "leica",
    "hasselblad",
    "unreal engine",
)


def test_format_catalog_ids_and_sizes_are_unique_and_on_grid() -> None:
    rows = load_formats()
    assert rows[0].id == CUSTOM_ID
    ids = [row.id for row in rows]
    labels = [row.label for row in rows]
    assert len(ids) == len(set(ids))
    assert len({label.casefold() for label in labels}) == len(labels)
    assert format_combo_labels() == labels
    for row in rows:
        assert _ID_RE.match(row.id), row.id
        assert row.label
        assert row.prefix.startswith("ez_")
        if row.id == CUSTOM_ID:
            assert row.width == 0 and row.height == 0
            continue
        assert row.width % GRID == 0
        assert row.height % GRID == 0
        assert MIN_DIM <= row.width <= MAX_DIM
        assert MIN_DIM <= row.height <= MAX_DIM


def test_default_format_is_ltx_feeder() -> None:
    assert default_format_id() == "aspect_16_9_ltx"
    spec = get_format(default_format_label())
    assert spec.id == "aspect_16_9_ltx"
    assert spec.width == 1280
    assert spec.height == 704
    unknown = get_format("not-a-real-format")
    assert unknown.id == "aspect_16_9_ltx"


def test_custom_snaps_1920x1080_and_unknown_falls_back() -> None:
    custom = resolve_canvas("Custom", width=1920, height=1080, batch=8)
    assert custom.format_id == CUSTOM_ID
    assert custom.width == 1920
    assert custom.height == 1072
    assert custom.batch == 4
    assert custom.prefix == "ez_still_studio"
    assert "1920×1072" in custom.hint
    preset = resolve_canvas("YouTube · thumbnail (1280×720)", width=16, height=16)
    assert preset.width == 1280
    assert preset.height == 720
    assert preset.prefix == "ez_thumbnail"
    assert clamp_dim(17) == snap_dim(17)


def test_look_none_is_empty_and_recipe_splices_klein() -> None:
    none = resolve_canvas(default_format_label(), look=LOOK_NONE)
    assert none.context == ""
    labels = look_combo_labels()
    assert labels[0] == LOOK_NONE
    assert "Golden wide" in labels
    text = splice_look("Golden wide")
    assert text
    blob = text.casefold()
    for needle in _BANNED_LOOK:
        assert needle not in blob, needle
    assert splice_look("not-a-recipe") == ""


def test_ez_image_format_run_packs_ui_and_result() -> None:
    types = EZImageFormat.INPUT_TYPES()
    required = types["required"]
    assert required["format"][1]["default"] == default_format_label()
    assert LOOK_NONE in required["look"][0]
    packed = EZImageFormat().run(
        "Instagram · 4:5 portrait (1024×1280)",
        look=LOOK_NONE,
        width=1,
        height=1,
        batch_size=2,
    )
    assert packed["result"][0] == 1024
    assert packed["result"][1] == 1280
    assert packed["result"][2] == 2
    assert packed["result"][4] == "ez_ig_portrait"
    assert "1024×1280" in packed["ui"]["text"][0]


def test_format_helpers_cover_remaining_branches(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    assert fmt._as_str(None) == ""
    assert fmt._as_str(12) == "12"
    assert fmt._as_int(True, 4) == 4
    assert fmt._as_int(2.8, 0) == 2
    assert fmt._as_int("", 5) == 5
    assert fmt._as_int("zz", 5) == 5
    assert fmt.clamp_dim(8) == MIN_DIM
    assert fmt.clamp_dim(3000) == MAX_DIM
    assert fmt.clamp_batch(0) == 1
    assert fmt.get_format("").id == "aspect_16_9_ltx"
    assert fmt.get_format("aspect_16_9_ltx").id == "aspect_16_9_ltx"
    assert fmt.resolve_look("rec_golden_wide") == "rec_golden_wide"
    assert fmt.resolve_look(None) == LOOK_NONE
    assert fmt.catalog_payload()["default_id"] == "aspect_16_9_ltx"
    fmt.reset_format_cache_for_tests()

    monkeypatch.setattr(fmt, "_cinema_recipes", lambda: None)
    assert fmt.look_combo_labels() == [LOOK_NONE]
    assert fmt.resolve_look("Golden wide") == LOOK_NONE
    monkeypatch.setattr(
        fmt,
        "_cinema_recipes",
        lambda: {
            "none": {"label": "none"},
            "rec_x": "skip",
            "rec_y": {"id": "rec_y"},
            "rec_z": {"label": "Zed"},
            "rec_dup": {"label": "Zed"},
        },
    )
    labels = fmt.look_combo_labels()
    assert "rec_y" in labels
    assert labels.count("Zed") == 1
    assert fmt.resolve_look("rec_x") == "rec_x"
    assert fmt.resolve_look("zed") == "rec_z"
    monkeypatch.setattr(fmt, "_cinema_splice", lambda _rid: "")
    assert splice_look("Zed") == ""
    monkeypatch.setattr(fmt, "default_format_id", lambda: "missing-id")
    assert default_format_label() == load_formats()[0].label
    empty = FormatSpec(
        id="aspect_16_9_ltx",
        label="x",
        group="aspect",
        width=1280,
        height=704,
        prefix="",
        hint="h",
        lock="",
    )
    monkeypatch.setattr(fmt, "get_format", lambda _value: empty)
    resolved = resolve_canvas("whatever")
    assert resolved.prefix == "ez_still_studio"
    import ez_image.nodes as image_nodes

    monkeypatch.setattr(image_nodes, "default_format_label", lambda: "not-in-list")
    types = EZImageFormat.INPUT_TYPES()
    assert types["required"]["format"][1]["default"] == format_combo_labels()[0]


def test_format_catalog_file_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(fmt, "FORMATS_PATH", missing)
    fmt.reset_format_cache_for_tests()
    with pytest.raises(ValueError, match="missing"):
        load_formats()
    missing.write_text("[]", encoding="utf-8")
    fmt.reset_format_cache_for_tests()
    with pytest.raises(ValueError, match="must be an object"):
        load_formats()
    assert fmt.default_format_id() == "aspect_16_9_ltx"
    assert fmt.custom_prefix() == "ez_still_studio"
    with pytest.raises(ValueError, match="must be an object"):
        fmt.catalog_payload()
    missing.write_text('{"formats": []}', encoding="utf-8")
    fmt.reset_format_cache_for_tests()
    with pytest.raises(ValueError, match="nonempty"):
        load_formats()
    missing.write_text(
        '{"default_id": "", "custom_prefix": "", "formats": [1]}',
        encoding="utf-8",
    )
    fmt.reset_format_cache_for_tests()
    assert fmt.default_format_id() == "aspect_16_9_ltx"
    assert fmt.custom_prefix() == "ez_still_studio"
    with pytest.raises(ValueError, match="objects"):
        load_formats()
    missing.write_text(
        '{"formats": [{"id": "", "label": "x", "group": "g", "width": 16, '
        '"height": 16, "prefix": "", "hint": "", "lock": ""}]}',
        encoding="utf-8",
    )
    fmt.reset_format_cache_for_tests()
    with pytest.raises(ValueError, match="id and label"):
        load_formats()
    missing.write_text(
        '{"formats": [{"id": "ok", "label": "Ok", "group": "g", "width": 16, '
        '"height": 16, "prefix": "", "hint": "", "lock": ""}]}',
        encoding="utf-8",
    )
    fmt.reset_format_cache_for_tests()
    row = load_formats()[0]
    assert row.prefix == "ez_still_studio"
    monkeypatch.setitem(sys.modules, "ez_prompt_enhance.cinema", None)
    assert fmt._cinema_recipes() is None
    assert fmt._cinema_splice("rec_golden_wide") == ""


def test_format_catalog_covers_klein_single_creator_prefixes() -> None:
    sys.path.insert(0, str(ROOT / "tests" / "python"))
    from _creator_pack3 import PACK3

    prefixes = {row.prefix for row in load_formats()}
    missing: list[str] = []
    for spec in PACK3:
        if spec.kind != "klein_single":
            continue
        if spec.prefix not in prefixes:
            missing.append(f"{spec.rel} {spec.prefix}")
            continue
        row = next(item for item in load_formats() if item.prefix == spec.prefix)
        assert (row.width, row.height) == spec.size, spec.rel
    assert missing == []

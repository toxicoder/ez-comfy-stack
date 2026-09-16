"""Hermetic tests for ez_image snap and match nodes.

Stdlib only. No Comfy, torch, Docker, or GPU.
"""

from __future__ import annotations

import inspect
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_image  # noqa: E402
from ez_image.nodes import (  # noqa: E402
    GRID,
    EZMatchImageSize,
    EZSnapImage,
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
    _resize_bhwc,
    snap_dim,
)


class _FakeImg:
    """Stand-in for a Comfy IMAGE tensor (BHWC)."""

    def __init__(self, height: int, width: int) -> None:
        self.shape = (1, height, width, 3)
        self.ops: list[tuple[int, int]] = []

    def movedim(self, src: int, dest: int) -> _FakeImg:
        self.ops.append((src, dest))
        return self


def test_pack_mappings_and_category() -> None:
    assert set(NODE_CLASS_MAPPINGS) == {"EZSnapImage", "EZMatchImageSize"}
    assert ez_image.NODE_CLASS_MAPPINGS == NODE_CLASS_MAPPINGS
    assert NODE_DISPLAY_NAME_MAPPINGS["EZSnapImage"] == "Snap image (div 16)"
    assert NODE_DISPLAY_NAME_MAPPINGS["EZMatchImageSize"] == "Match image size"
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

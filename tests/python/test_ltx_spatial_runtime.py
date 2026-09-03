"""Hermetic tests for ez_ltx_spatial (no Comfy, no GPU, no network)."""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest

from ez_ltx_spatial import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from ez_ltx_spatial.align import center_crop_bcthw, snap_dim, snap_hw
from ez_ltx_spatial.patch import (
    apply_patches,
    snap_width_height_in_call,
    _wrap_classmethod_wh,
    _wrap_video_vae_encode,
)


class FakeBCTHW:
    """Minimal ``…,H,W`` object: shape plus spatial slicing."""

    def __init__(self, shape: tuple[int, ...], origin: tuple[int, int] = (0, 0)) -> None:
        self.shape = shape
        self.origin = origin

    def __getitem__(self, idx: Any) -> FakeBCTHW:
        ys, xs = idx[-2], idx[-1]
        y0 = 0 if ys.start is None else ys.start
        x0 = 0 if xs.start is None else xs.start
        y1 = ys.stop
        x1 = xs.stop
        new_shape = self.shape[:-2] + (y1 - y0, x1 - x0)
        return FakeBCTHW(new_shape, origin=(self.origin[0] + y0, self.origin[1] + x0))


def test_pack_registers_no_canvas_nodes() -> None:
    assert NODE_CLASS_MAPPINGS == {}
    assert NODE_DISPLAY_NAME_MAPPINGS == {}


def test_snap_dim_broadcast_and_aligned() -> None:
    assert snap_dim(720) == 704
    assert snap_dim(1080) == 1056
    assert snap_dim(1280) == 1280
    assert snap_dim(768) == 768
    assert snap_dim(704) == 704
    assert snap_dim(45) == 32
    assert snap_dim(16) == 0
    assert snap_dim(33, minimum=64) == 64
    assert snap_dim(0, minimum=64) == 64
    assert snap_hw(1280, 720) == (1280, 704)
    assert snap_hw(1920, 1080) == (1920, 1056)
    assert snap_hw(768, 1280) == (768, 1280)


def test_center_crop_720p_drops_8px_top_and_bottom() -> None:
    x = FakeBCTHW((1, 3, 1, 720, 1280))
    out = center_crop_bcthw(x)
    assert out.shape == (1, 3, 1, 704, 1280)
    assert out.origin == (8, 0)


def test_center_crop_1080p_height_only() -> None:
    x = FakeBCTHW((1, 3, 1, 1080, 1920))
    out = center_crop_bcthw(x)
    assert out.shape == (1, 3, 1, 1056, 1920)
    assert out.origin == (12, 0)


def test_center_crop_identity_and_undersize() -> None:
    aligned = FakeBCTHW((1, 3, 1, 704, 1280))
    assert center_crop_bcthw(aligned) is aligned
    tiny = FakeBCTHW((1, 3, 1, 16, 1280))
    assert center_crop_bcthw(tiny) is tiny
    obj = object()
    assert center_crop_bcthw(obj) is obj
    short = FakeBCTHW((8,))
    assert center_crop_bcthw(short) is short
    narrow = FakeBCTHW((1, 3, 1, 704, 16))
    assert center_crop_bcthw(narrow) is narrow


def test_snap_call_positional_and_kwargs() -> None:
    args, kwargs = snap_width_height_in_call((1280, 720, 121), {}, 0)
    assert args == (1280, 704, 121)
    assert kwargs == {}
    args, kwargs = snap_width_height_in_call((), {"width": 1280, "height": 720}, 0)
    assert kwargs["width"] == 1280
    assert kwargs["height"] == 704
    mixed_args, mixed_kwargs = snap_width_height_in_call(
        (1280,), {"height": 720}, 0
    )
    assert mixed_args == (1280,)
    assert mixed_kwargs["height"] == 704
    passthrough = snap_width_height_in_call((1,), {}, 4)
    assert passthrough == ((1,), {})
    no_h = snap_width_height_in_call((), {"width": 1280}, 0)
    assert no_h == ((), {"width": 1280})
    kw_w, kw_h = snap_width_height_in_call((999, 720), {"width": 1280}, 0)
    assert kw_w == (999, 704)
    assert kw_h["width"] == 1280


def _install_ltx_stubs(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    def ensure(name: str) -> types.ModuleType:
        mod = sys.modules.get(name)
        if not isinstance(mod, types.ModuleType) or not name.startswith("comfy"):
            mod = types.ModuleType(name)
        monkeypatch.setitem(sys.modules, name, mod)
        if "." in name:
            parent_name, child = name.rsplit(".", 1)
            parent = ensure(parent_name)
            setattr(parent, child, mod)
        return mod

    for name in (
        "comfy",
        "comfy_extras",
        "comfy_extras.nodes_lt",
        "comfy.ldm",
        "comfy.ldm.lightricks",
        "comfy.ldm.lightricks.vae",
        "comfy.ldm.lightricks.vae.causal_video_autoencoder",
    ):
        ensure(name)

    class LTXVImgToVideo:
        @classmethod
        def execute(
            cls,
            positive: Any,
            negative: Any,
            image: Any,
            vae: Any,
            width: int,
            height: int,
            length: int,
            batch_size: int,
            strength: float = 1.0,
        ) -> dict[str, Any]:
            return {"width": width, "height": height, "length": length}

        generate = execute

    class EmptyLTXVLatentVideo:
        @classmethod
        def execute(
            cls, width: int, height: int, length: int, batch_size: int = 1
        ) -> dict[str, int]:
            return {"width": width, "height": height}

    class VideoVAE:
        def encode(self, x: Any, device: Any = None) -> Any:
            return (x, device)

    nodes_lt = sys.modules["comfy_extras.nodes_lt"]
    nodes_lt.LTXVImgToVideo = LTXVImgToVideo
    nodes_lt.EmptyLTXVLatentVideo = EmptyLTXVLatentVideo
    vae_mod = sys.modules["comfy.ldm.lightricks.vae.causal_video_autoencoder"]
    vae_mod.VideoVAE = VideoVAE
    return {
        "LTXVImgToVideo": LTXVImgToVideo,
        "EmptyLTXVLatentVideo": EmptyLTXVLatentVideo,
        "VideoVAE": VideoVAE,
    }


def test_apply_patches_fail_soft_without_comfy(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for name in list(sys.modules):
        if name == "comfy" or name.startswith("comfy.") or name.startswith("comfy_extras"):
            monkeypatch.setitem(sys.modules, name, None)
    results = apply_patches()
    assert results == {
        "LTXVImgToVideo": False,
        "EmptyLTXVLatentVideo": False,
        "VideoVAE": False,
    }
    err = capsys.readouterr().err
    assert "LTX nodes not wrapped" in err
    assert "VideoVAE.encode not wrapped" in err


def test_apply_patches_snaps_widgets_and_encode(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    stubs = _install_ltx_stubs(monkeypatch)
    results = apply_patches()
    assert results["LTXVImgToVideo"] is True
    assert results["EmptyLTXVLatentVideo"] is True
    assert results["VideoVAE"] is True

    img = stubs["LTXVImgToVideo"]
    out = img.execute(None, None, None, None, 1280, 720, 121, 1, 1.0)
    assert out == {"width": 1280, "height": 704, "length": 121}
    gen = img.generate(None, None, None, None, 1920, 1080, 97, 1)
    assert gen["height"] == 1056
    empty = stubs["EmptyLTXVLatentVideo"].execute(1280, 720, 97)
    assert empty == {"width": 1280, "height": 704}

    pixels = FakeBCTHW((1, 3, 1, 720, 1280))
    cropped, device = stubs["VideoVAE"]().encode(pixels, device="cpu")
    assert cropped.shape[-2] == 704
    assert device == "cpu"
    aligned = FakeBCTHW((1, 3, 1, 704, 1280))
    same, _ = stubs["VideoVAE"]().encode(aligned)
    assert same is aligned

    err = capsys.readouterr().err
    assert "1280x720 -> 1280x704" in err
    assert "encode 1280x720 -> 1280x704" in err

    again = apply_patches()
    assert again == {
        "LTXVImgToVideo": False,
        "EmptyLTXVLatentVideo": False,
        "VideoVAE": False,
    }


def test_apply_patches_keyword_width_height(monkeypatch: pytest.MonkeyPatch) -> None:
    stubs = _install_ltx_stubs(monkeypatch)
    apply_patches()
    out = stubs["LTXVImgToVideo"].execute(
        None,
        None,
        None,
        None,
        width=1280,
        height=720,
        length=121,
        batch_size=1,
        strength=1.0,
    )
    assert out["height"] == 704


def test_wrap_skips_missing_methods() -> None:
    class NoExecute:
        pass

    class NoEncode:
        pass

    assert _wrap_classmethod_wh(NoExecute, "execute", 0) is False
    assert _wrap_video_vae_encode(NoEncode) is False

    class OnlyGenerate:
        @classmethod
        def generate(cls, width: int, height: int) -> tuple[int, int]:
            return width, height

    assert _wrap_classmethod_wh(OnlyGenerate, "generate", 0) is True
    assert OnlyGenerate.generate(1280, 720) == (1280, 704)


def test_encode_crop_exception_passthrough(
    capsys: pytest.CaptureFixture[str],
) -> None:
    class Boom:
        @property
        def shape(self) -> tuple[int, ...]:
            raise RuntimeError("no shape")

    class VAE:
        def encode(self, x: Any, device: Any = None) -> Any:
            return ("orig", x, device)

    assert _wrap_video_vae_encode(VAE) is True
    payload = Boom()
    assert VAE().encode(payload, "dev") == ("orig", payload, "dev")
    assert "encode crop skipped" in capsys.readouterr().err


def test_encode_log_shape_failure_still_forwards(
    capsys: pytest.CaptureFixture[str],
) -> None:
    class Sliced:
        pass

    class Partial:
        shape = (1, 3, 1, 720, 1280)

        def __getitem__(self, idx: Any) -> Sliced:
            return Sliced()

    class VAE:
        def encode(self, x: Any, device: Any = None) -> Any:
            return x

    assert _wrap_video_vae_encode(VAE) is True
    assert isinstance(VAE().encode(Partial()), Sliced)
    assert "encode cropped to a ÷32 spatial window" in capsys.readouterr().err

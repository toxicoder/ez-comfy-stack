"""Hermetic tests for optional Klein reference nodes."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_image  # noqa: E402
from ez_image.refs import (  # noqa: E402
    EZDescribeImage,
    EZKleinRefCanvas,
    EZOptionalImage,
    _image_present,
)


class _FakeImg:
    """Minimal BHWC-shaped image for presence checks."""

    def __init__(self, height: int, width: int) -> None:
        self.shape = (1, height, width, 3)


def test_pack_exports_ref_nodes() -> None:
    assert ez_image.NODE_CLASS_MAPPINGS["EZOptionalImage"] is EZOptionalImage
    assert ez_image.NODE_CLASS_MAPPINGS["EZKleinRefCanvas"] is EZKleinRefCanvas
    assert ez_image.NODE_CLASS_MAPPINGS["EZDescribeImage"] is EZDescribeImage


def test_optional_image_empty_is_ok() -> None:
    out = EZOptionalImage().run()
    assert out["result"][1] == 0
    assert out["result"][2] is False
    assert out["result"][0] is None


def test_optional_image_counts_present_tensors() -> None:
    first = _FakeImg(64, 64)
    out = EZOptionalImage().run(image=first, image_2=_FakeImg(1, 1))
    assert out["result"][0] is first
    assert out["result"][1] == 1
    assert out["result"][2] is True


def test_tiny_tensor_is_not_a_still() -> None:
    assert _image_present(_FakeImg(1, 1)) is False
    assert _image_present(None) is False
    assert _image_present(_FakeImg(32, 48)) is True


def test_ref_canvas_passthrough_without_image() -> None:
    latent = {"samples": "empty"}
    vae = SimpleNamespace()
    out = EZKleinRefCanvas().run(latent, vae)
    assert out[0] is latent
    out2 = EZKleinRefCanvas().run(latent, vae, image=_FakeImg(64, 64), has_image=False)
    assert out2[0] is latent


def test_ref_canvas_attaches_when_vae_encodes() -> None:
    latent = {"samples": "empty"}
    encoded = {"samples": "ref"}
    vae = SimpleNamespace(encode=lambda _img: encoded)
    image = _FakeImg(32, 32)
    out = EZKleinRefCanvas().run(latent, vae, image=image, has_image=True)
    assert out[0]["reference"] is encoded
    assert out[0]["samples"] == "empty"
    assert out[1] is image


def test_describe_image_fail_soft() -> None:
    empty = EZDescribeImage().run()
    assert empty["result"] == ("",)
    present = EZDescribeImage().run(image=_FakeImg(64, 64), has_image=True)
    assert present["result"] == ("",)
    assert "VL" in present["ui"]["text"][0] or "no VL" in present["ui"]["text"][0]

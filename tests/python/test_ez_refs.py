"""Hermetic tests for optional Klein reference nodes."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_image  # noqa: E402
from ez_image.refs import (  # noqa: E402
    EZDescribeImage,
    EZKleinRefCanvas,
    EZOptionalImage,
    _as_bool,
    _encode_ref,
    _image_present,
    _reference_latent,
    input_still_choices,
    load_input_still,
)


class _FakeImg:
    """Minimal BHWC-shaped image for presence checks."""

    def __init__(self, height: int, width: int) -> None:
        self.shape = (1, height, width, 3)


def test_pack_exports_ref_nodes() -> None:
    assert ez_image.NODE_CLASS_MAPPINGS["EZOptionalImage"] is EZOptionalImage
    assert ez_image.NODE_CLASS_MAPPINGS["EZKleinRefCanvas"] is EZKleinRefCanvas
    assert ez_image.NODE_CLASS_MAPPINGS["EZDescribeImage"] is EZDescribeImage


def test_filename_str_and_input_choices(monkeypatch: pytest.MonkeyPatch) -> None:
    from ez_image.refs import _filename_str

    assert _filename_str(None) == ""
    assert _filename_str(12) == "12"
    assert _filename_str("  hero.png  ") == "hero.png"

    class _Folder:
        @staticmethod
        def get_filename_list(_kind: str) -> list[str]:
            return ["a.png", " ", "b.png"]

    monkeypatch.setitem(__import__("sys").modules, "folder_paths", _Folder)
    names = input_still_choices()
    assert names[0] == ""
    assert "a.png" in names
    assert "b.png" in names


def test_load_input_still_success_and_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import sys
    import types

    class _Arr:
        ndim = 3

        def astype(self, _kind: object) -> "_Arr":
            return self

        def __truediv__(self, _n: object) -> "_Arr":
            return self

        def __getitem__(self, _idx: object) -> "_Arr":
            return "batched"

    class _Img:
        def convert(self, _mode: str) -> "_Img":
            return self

        def __enter__(self) -> "_Img":
            return self

        def __exit__(self, *_exc: object) -> bool:
            return False

    class _Folder:
        @staticmethod
        def get_annotated_filepath(_name: str) -> str:
            return str(tmp_path / "ok.png")

    fake_np = types.SimpleNamespace(asarray=lambda _img: _Arr(), float32="f32")
    fake_pil = types.ModuleType("PIL")
    fake_image = types.ModuleType("PIL.Image")
    fake_image.open = lambda _path: _Img()
    fake_pil.Image = fake_image
    monkeypatch.setitem(sys.modules, "folder_paths", _Folder)
    monkeypatch.setitem(sys.modules, "numpy", fake_np)
    monkeypatch.setitem(sys.modules, "PIL", fake_pil)
    monkeypatch.setitem(sys.modules, "PIL.Image", fake_image)
    if "numpy" in sys.modules:
        monkeypatch.setattr(sys.modules["numpy"], "asarray", lambda _img: _Arr(), raising=False)
    loaded = load_input_still("ok.png")
    assert loaded == "batched"

    class _Flat:
        ndim = 2

        def astype(self, _kind: object) -> "_Flat":
            return self

        def __truediv__(self, _n: object) -> "_Flat":
            return self

    monkeypatch.setattr(sys.modules["numpy"], "asarray", lambda _img: _Flat(), raising=False)
    fake_np.asarray = lambda _img: _Flat()
    assert load_input_still("ok.png") is None

    class _BoomFolder:
        @staticmethod
        def get_annotated_filepath(_name: str) -> str:
            raise RuntimeError("nope")

    monkeypatch.setitem(sys.modules, "folder_paths", _BoomFolder)
    assert load_input_still("ok.png") is None

    class _EmptyPath:
        @staticmethod
        def get_annotated_filepath(_name: str) -> str:
            return ""

    monkeypatch.setitem(sys.modules, "folder_paths", _EmptyPath)
    assert load_input_still("ok.png") is None

    class _Unreadable:
        @staticmethod
        def get_annotated_filepath(_name: str) -> str:
            return str(tmp_path / "missing.png")

    def _open_fail(_path: object) -> _Img:
        raise OSError("bad")

    monkeypatch.setitem(sys.modules, "folder_paths", _Unreadable)
    fake_image.open = _open_fail
    assert load_input_still("ok.png") is None


def test_optional_image_combo_allows_empty_upload() -> None:
    spec = EZOptionalImage.INPUT_TYPES()["required"]["filename"]
    assert spec[0][0] == ""
    assert spec[1]["image_upload"] is True
    assert spec[1]["default"] == ""
    assert input_still_choices()[0] == ""
    assert load_input_still("") is None
    assert load_input_still("missing.png") is None


def test_optional_image_loads_filename_when_no_tensor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeImg(64, 80)
    monkeypatch.setattr("ez_image.refs.load_input_still", lambda _name: fake)
    out = EZOptionalImage().run(filename="hero.png")
    assert out["result"][0] is fake
    assert out["result"][1] == 1
    assert out["result"][2] is True


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


def test_input_types_are_optional() -> None:
    opt = EZOptionalImage.INPUT_TYPES()
    assert opt["required"]["filename"][1]["default"] == ""
    assert "image" in opt["optional"]
    canvas = EZKleinRefCanvas.INPUT_TYPES()
    assert canvas["required"]["latent"][0] == "LATENT"
    assert canvas["optional"]["has_image"][1]["default"] is False
    describe = EZDescribeImage.INPUT_TYPES()
    assert describe["required"]["has_image"][1]["default"] is False


def test_as_bool_and_presence_edges() -> None:
    assert _as_bool(True) is True
    assert _as_bool(0) is False
    assert _as_bool(2) is True
    assert _as_bool("yes") is True
    assert _as_bool("no") is False
    assert _as_bool(None) is False
    assert _image_present(object()) is False
    assert _image_present(_FakeImg(8, 8)) is True

    class _BadShape:
        shape = "nope"

    assert _image_present(_BadShape()) is False

    class _ShortShape:
        shape = (1,)

    assert _image_present(_ShortShape()) is False


def test_encode_ref_fail_soft_and_resize(monkeypatch: pytest.MonkeyPatch) -> None:
    latent = {"samples": "empty"}
    vae_missing = SimpleNamespace()
    image = _FakeImg(32, 32)
    assert EZKleinRefCanvas().run(latent, vae_missing, image=image, has_image=True)[0] is latent
    assert _encode_ref(image, vae_missing) is None

    def boom(_img: object) -> object:
        raise RuntimeError("encode failed")

    assert _encode_ref(image, SimpleNamespace(encode=boom)) is None

    seen: list[tuple[int, int]] = []

    def fake_resize(img: object, height: int, width: int) -> object:
        seen.append((height, width))
        return img

    monkeypatch.setattr("ez_image.nodes._resize_bhwc", fake_resize)
    odd = _FakeImg(18, 20)
    encoded = {"ok": True}
    out = _encode_ref(odd, SimpleNamespace(encode=lambda img: encoded))
    assert out is encoded
    assert seen == [(16, 16)]
    assert EZKleinRefCanvas().run(latent, SimpleNamespace(encode=boom), image=image, has_image="on")[0] is latent


def test_reference_latent_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    encoded = {"samples": "ref"}
    merged = _reference_latent({"samples": "empty"}, encoded)
    assert merged["reference"] is encoded
    assert _reference_latent("not-a-dict", encoded) == "not-a-dict"

    class _Ref:
        def append(self, empty: object, encoded_lat: object) -> object:
            return {"attached": encoded_lat, "empty": empty}

    extras = SimpleNamespace(ReferenceLatent=_Ref)
    monkeypatch.setitem(sys.modules, "comfy_extras", extras)
    monkeypatch.setitem(sys.modules, "comfy_extras.nodes_flux", extras)
    attached = _reference_latent({"samples": "empty"}, encoded)
    assert attached["attached"] is encoded

    class _TupleRef:
        def append(self, empty: object, encoded_lat: object) -> tuple[object]:
            del empty
            return ({"tuple": encoded_lat},)

    extras.ReferenceLatent = _TupleRef
    tupled = _reference_latent({"samples": "empty"}, encoded)
    assert tupled["tuple"] is encoded

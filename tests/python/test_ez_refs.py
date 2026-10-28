"""Hermetic tests for optional Klein reference nodes."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_image  # noqa: E402
from ez_image.nodes import CATEGORY  # noqa: E402
from ez_image.refs import (  # noqa: E402
    EZDescribeImage,
    EZKleinRefCanvas,
    EZOptionalImage,
    _as_bool,
    _batch_len,
    _encode_ref,
    _encoded_frames,
    _image_present,
    _ref_limit,
    _reference_latent,
    input_still_choices,
    load_input_still,
)


class _FakeImg:
    """Minimal BHWC-shaped image for presence checks."""

    def __init__(self, height: int, width: int, batch: int = 1) -> None:
        self.shape = (batch, height, width, 3)


class _FakeBatch:
    """Latent ``samples`` batch that slices on the leading axis."""

    def __init__(self, frames: list[Any]) -> None:
        self.frames = frames
        self.shape = (len(frames), 128, 4, 4)

    def __getitem__(self, index: slice) -> "_FakeBatch":
        return _FakeBatch(self.frames[index])


class _NoSlice:
    """Batch-shaped object that refuses to slice."""

    shape = (3, 128, 4, 4)


_SOCKET_TYPES = frozenset(
    {"IMAGE", "LATENT", "VAE", "MASK", "CONDITIONING", "MODEL", "CLIP", "AUDIO"}
)


def _widget_names(node: Any) -> list[str]:
    """Return the positional widget names a saved graph stores.

    Args:
        node: Node class to inspect.

    Returns:
        Widget keys in INPUT_TYPES key order, sockets left out.
    """
    spec: dict[str, dict[str, Any]] = node.INPUT_TYPES()
    names: list[str] = []
    for section in ("required", "optional"):
        for key, value in spec.get(section, {}).items():
            kind = value[0]
            if isinstance(kind, str) and kind in _SOCKET_TYPES:
                continue
            names.append(key)
    return names


def _three_stills() -> dict[str, _FakeImg]:
    """Return one distinct still per picker name.

    Returns:
        Mapping of picker filename to fake image.
    """
    return {
        "a.png": _FakeImg(64, 64),
        "b.png": _FakeImg(64, 80),
        "c.png": _FakeImg(80, 64),
    }


def _patch_stills(monkeypatch: pytest.MonkeyPatch, stills: dict[str, _FakeImg]) -> list[str]:
    """Swap ``load_input_still`` for a picker lookup that records calls.

    Args:
        monkeypatch: Pytest monkeypatch.
        stills: Filename to still map served by the fake loader.

    Returns:
        List collecting each requested filename, in call order.
    """
    calls: list[str] = []

    def _load(name: object) -> object | None:
        calls.append(str(name))
        return stills.get(str(name))

    monkeypatch.setattr("ez_image.refs.load_input_still", _load)
    return calls


def _patch_torch(monkeypatch: pytest.MonkeyPatch, cat: object) -> None:
    """Install a torch stand-in so concat paths run without torch.

    Args:
        monkeypatch: Pytest monkeypatch.
        cat: Value exposed as ``torch.cat``; None keeps the module attribute-less.
    """
    if cat is None:
        monkeypatch.setitem(sys.modules, "torch", SimpleNamespace())
        return
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cat=cat))


def _patch_no_torch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``import torch`` fail inside the node.

    Args:
        monkeypatch: Pytest monkeypatch.
    """
    monkeypatch.setitem(sys.modules, "torch", None)


def _patch_reference_latent(
    monkeypatch: pytest.MonkeyPatch, fail_at: int = 0
) -> list[Any]:
    """Install a ``comfy_extras.nodes_flux.ReferenceLatent`` fake.

    Args:
        monkeypatch: Pytest monkeypatch.
        fail_at: Raise on this 1-based append call; 0 never raises.

    Returns:
        List collecting the piece of each successful append, in call order.
    """
    seen: list[Any] = []
    state = {"calls": 0}

    class _Ref:
        def append(self, empty: object, piece: object) -> tuple[object]:
            state["calls"] += 1
            if fail_at and state["calls"] == fail_at:
                raise RuntimeError("append failed")
            seen.append(piece)
            merged = dict(empty) if isinstance(empty, dict) else {}
            merged.setdefault("references", []).append(piece)
            return (merged,)

    extras = SimpleNamespace(ReferenceLatent=_Ref)
    monkeypatch.setitem(sys.modules, "comfy_extras", extras)
    monkeypatch.setitem(sys.modules, "comfy_extras.nodes_flux", extras)
    return seen


def _canvas_vae(encoded: object, seen_images: list[object]) -> SimpleNamespace:
    """Build a VAE stub that encodes the batch once.

    Args:
        encoded: Value handed back by ``encode``.
        seen_images: List collecting every image passed to ``encode``.

    Returns:
        Object with an ``encode`` callable.
    """

    def _encode(image: object) -> object:
        seen_images.append(image)
        return encoded

    return SimpleNamespace(encode=_encode)


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
            return self

    class _Img:
        def convert(self, _mode: str) -> "_Img":
            return self

        def __enter__(self) -> "_Img":
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

    class _Folder:
        @staticmethod
        def get_annotated_filepath(_name: str) -> str:
            return str(tmp_path / "ok.png")

    fake_np = types.SimpleNamespace(asarray=lambda _img: _Arr(), float32="f32")
    fake_pil = types.ModuleType("PIL")
    fake_image = types.ModuleType("PIL.Image")
    fake_image.open = lambda _path: _Img()  # type: ignore[attr-defined]
    fake_pil.Image = fake_image  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "folder_paths", _Folder)
    monkeypatch.setitem(sys.modules, "numpy", fake_np)
    monkeypatch.setitem(sys.modules, "PIL", fake_pil)
    monkeypatch.setitem(sys.modules, "PIL.Image", fake_image)
    if "numpy" in sys.modules:
        monkeypatch.setattr(sys.modules["numpy"], "asarray", lambda _img: _Arr(), raising=False)
    loaded = load_input_still("ok.png")
    assert loaded is not None

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
    fake_image.open = _open_fail  # type: ignore[attr-defined]
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
    assert out["result"][0] is None
    assert out["result"][1] == 0
    assert out["result"][2] is False
    assert out["ui"]["text"] == ("no reference still",)


def test_optional_image_counts_present_tensors() -> None:
    first = _FakeImg(64, 64)
    out = EZOptionalImage().run(image=first)
    assert out["result"][0] is first
    assert out["result"][1] == 1
    assert out["result"][2] is True
    assert out["ui"]["text"] == ("1 reference still",)


def test_optional_image_keeps_the_frozen_contract() -> None:
    assert EZOptionalImage.RETURN_TYPES == ("IMAGE", "INT", "BOOLEAN")
    assert EZOptionalImage.RETURN_NAMES == ("image", "count", "has_image")
    assert EZOptionalImage.FUNCTION == "run"
    assert EZOptionalImage.CATEGORY == CATEGORY
    assert EZOptionalImage.OUTPUT_NODE is True
    text = EZOptionalImage.DESCRIPTION.lower()
    assert "use_references" in text
    assert "empty" in text


def test_optional_image_optional_keys_are_exact() -> None:
    spec = EZOptionalImage.INPUT_TYPES()
    assert list(spec["required"]) == ["filename"]
    assert list(spec["optional"]) == [
        "use_references",
        "filename_2",
        "filename_3",
        "image",
    ]


def test_optional_image_widget_order_is_positional() -> None:
    assert _widget_names(EZOptionalImage) == [
        "filename",
        "use_references",
        "filename_2",
        "filename_3",
    ]


def test_optional_image_mute_widget_defaults_on() -> None:
    mute = EZOptionalImage.INPUT_TYPES()["optional"]["use_references"]
    assert mute[0] == "BOOLEAN"
    assert mute[1] == {
        "default": True,
        "label_on": "Use references",
        "label_off": "References off",
    }


def test_optional_image_extra_pickers_are_upload_combos() -> None:
    spec = EZOptionalImage.INPUT_TYPES()
    for name in ("filename", "filename_2", "filename_3"):
        picker = spec["required"][name] if name in spec["required"] else spec["optional"][name]
        assert picker[0][0] == ""
        assert picker[1] == {"default": "", "image_upload": True}


def test_optional_image_drops_the_dead_pair_widgets() -> None:
    spec = EZOptionalImage.INPUT_TYPES()
    keys = set(spec["required"]) | set(spec["optional"])
    assert "image_2" not in keys
    assert "image_3" not in keys
    assert spec["optional"]["filename_2"][0] != "STRING"
    assert spec["optional"]["filename_3"][0] != "STRING"
    params = list(inspect.signature(EZOptionalImage.run).parameters)
    assert params == [
        "self",
        "filename",
        "use_references",
        "filename_2",
        "filename_3",
        "image",
    ]


def test_use_references_false_mutes_without_clearing_pickers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stills = _three_stills()
    calls = _patch_stills(monkeypatch, stills)
    node = EZOptionalImage()
    muted = node.run(filename="a.png", filename_2="b.png", use_references=False)
    assert muted["result"][0] is None
    assert muted["result"][1] == 0
    assert muted["result"][2] is False
    assert muted["ui"]["text"] == ("references off",)
    assert calls == []
    back_on = node.run(filename="a.png", filename_2="b.png", use_references=True)
    assert calls == ["a.png", "b.png"]
    assert back_on["result"][1] == 2
    assert back_on["result"][2] is True


def test_use_references_accepts_a_falsy_string() -> None:
    out = EZOptionalImage().run(filename="a.png", use_references="off")
    assert out["result"] == (None, 0, False)
    assert out["ui"]["text"] == ("references off",)


def test_pickers_load_through_load_input_still(monkeypatch: pytest.MonkeyPatch) -> None:
    stills = _three_stills()
    calls = _patch_stills(monkeypatch, stills)
    _patch_torch(monkeypatch, lambda frames, dim=0: SimpleNamespace(frames=list(frames)))
    out = EZOptionalImage().run(filename="a.png", filename_2="b.png", filename_3="c.png")
    assert calls == ["a.png", "b.png", "c.png"]
    assert out["result"][1] == 3
    assert out["result"][2] is True
    assert out["ui"]["text"] == ("3 reference stills",)


def test_pickers_dedupe_by_normalized_filename(monkeypatch: pytest.MonkeyPatch) -> None:
    stills = _three_stills()
    calls = _patch_stills(monkeypatch, stills)
    _patch_torch(monkeypatch, lambda frames, dim=0: SimpleNamespace(frames=list(frames)))
    out = EZOptionalImage().run(filename=" a.png ", filename_2="a.png", filename_3="b.png")
    assert calls == ["a.png", "b.png"]
    assert out["result"][1] == 2
    assert out["result"][2] is True


def test_unreadable_pickers_are_not_stills(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ez_image.refs.load_input_still", lambda _name: None)
    out = EZOptionalImage().run(filename="gone.png", filename_2="also-gone.png")
    assert out["result"] == (None, 0, False)
    assert out["ui"]["text"] == ("no reference still",)


def test_wired_batch_counts_its_batch_dimension() -> None:
    batch = _FakeImg(48, 64, batch=4)
    out = EZOptionalImage().run(image=batch)
    assert out["result"][0] is batch
    assert out["result"][1] == 4
    assert out["result"][2] is True
    assert out["ui"]["text"] == ("4 reference stills",)


def test_single_still_passes_through_without_torch(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_no_torch(monkeypatch)
    fake = _FakeImg(64, 64)
    monkeypatch.setattr("ez_image.refs.load_input_still", lambda _name: fake)
    out = EZOptionalImage().run(filename="hero.png")
    assert out["result"][0] is fake
    assert out["result"][1] == 1


def test_multi_still_concatenates_on_batch_axis(monkeypatch: pytest.MonkeyPatch) -> None:
    stills = _three_stills()
    _patch_stills(monkeypatch, stills)
    joined: list[tuple[int, int]] = []

    def _cat(frames: list[object], dim: int = 0) -> object:
        joined.append((len(frames), dim))
        return SimpleNamespace(frames=list(frames))

    _patch_torch(monkeypatch, _cat)
    batch = _FakeImg(64, 64, batch=2)
    out = EZOptionalImage().run(
        filename="a.png", filename_2="b.png", filename_3="c.png", image=batch
    )
    assert out["result"][1] == 5
    assert out["result"][2] is True
    assert joined == [(4, 0)]
    assert out["result"][0].frames == [
        batch,
        stills["a.png"],
        stills["b.png"],
        stills["c.png"],
    ]


def test_multi_still_falls_back_when_cat_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    stills = _three_stills()
    _patch_stills(monkeypatch, stills)

    def _cat(_frames: list[object], _dim: int = 0) -> object:
        raise RuntimeError("shape mismatch")

    _patch_torch(monkeypatch, _cat)
    out = EZOptionalImage().run(filename="a.png", filename_2="b.png")
    assert out["result"][0] is stills["a.png"]
    assert out["result"][1] == 2
    assert out["result"][2] is True


def test_multi_still_without_torch_keeps_the_first_still(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stills = _three_stills()
    _patch_stills(monkeypatch, stills)
    _patch_no_torch(monkeypatch)
    out = EZOptionalImage().run(filename="a.png", filename_2="b.png")
    assert out["result"][0] is stills["a.png"]
    assert out["result"][1] == 2


def test_multi_still_without_cat_attribute_keeps_the_first_still(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stills = _three_stills()
    _patch_stills(monkeypatch, stills)
    _patch_torch(monkeypatch, None)
    out = EZOptionalImage().run(filename="a.png", filename_2="b.png")
    assert out["result"][0] is stills["a.png"]
    assert out["result"][1] == 2


def test_batch_len_edges() -> None:
    assert _batch_len(_FakeImg(8, 8, batch=3)) == 3
    assert _batch_len(_FakeImg(8, 8, batch=0)) == 1
    assert _batch_len(object()) == 1
    assert _batch_len(SimpleNamespace(shape="nope")) == 1
    assert _batch_len(None) == 1


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


def test_ref_canvas_optional_keys_are_exact() -> None:
    spec = EZKleinRefCanvas.INPUT_TYPES()
    assert list(spec["required"]) == ["latent", "vae"]
    assert list(spec["optional"]) == ["image", "has_image", "max_refs"]
    assert spec["optional"]["image"] == ("IMAGE",)
    assert spec["optional"]["has_image"] == ("BOOLEAN", {"default": False})
    assert spec["optional"]["max_refs"] == (
        "INT",
        {"default": 3, "min": 1, "max": 4, "step": 1},
    )
    assert _widget_names(EZKleinRefCanvas) == ["has_image", "max_refs"]
    assert EZKleinRefCanvas.RETURN_TYPES == ("LATENT", "IMAGE")
    assert EZKleinRefCanvas.RETURN_NAMES == ("latent", "image")


def test_ref_canvas_chains_append_per_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _patch_reference_latent(monkeypatch)
    latent = {"samples": "empty"}
    image = _FakeImg(64, 64, batch=3)
    encoded = {"samples": _FakeBatch(["f0", "f1", "f2"])}
    encoded_calls: list[object] = []
    vae = _canvas_vae(encoded, encoded_calls)
    out = EZKleinRefCanvas().run(latent, vae, image=image, has_image=True, max_refs=3)
    assert encoded_calls == [image]
    assert [piece["samples"].frames for piece in seen] == [["f0"], ["f1"], ["f2"]]
    assert out[0]["samples"] == "empty"
    assert len(out[0]["references"]) == 3
    assert out[1] is image


def test_ref_canvas_caps_frames_at_max_refs(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _patch_reference_latent(monkeypatch)
    latent = {"samples": "empty"}
    encoded = {"samples": _FakeBatch(["f0", "f1", "f2"])}
    vae = _canvas_vae(encoded, [])
    EZKleinRefCanvas().run(
        latent, vae, image=_FakeImg(64, 64, batch=3), has_image=True, max_refs=2
    )
    assert [piece["samples"].frames for piece in seen] == [["f0"], ["f1"]]


def test_ref_canvas_one_frame_one_append(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _patch_reference_latent(monkeypatch)
    latent = {"samples": "empty"}
    encoded = {"samples": _FakeBatch(["f0"])}
    vae = _canvas_vae(encoded, [])
    out = EZKleinRefCanvas().run(
        latent, vae, image=_FakeImg(64, 64), has_image=True, max_refs=4
    )
    assert seen == [encoded]
    assert out[0]["references"] == [encoded]
    assert out[0]["samples"] == "empty"


def test_ref_canvas_clamps_the_max_refs_widget(monkeypatch: pytest.MonkeyPatch) -> None:
    latent = {"samples": "empty"}
    encoded = {"samples": _FakeBatch(["f0", "f1", "f2", "f3", "f4"])}
    vae = _canvas_vae(encoded, [])
    image = _FakeImg(64, 64, batch=5)

    low = _patch_reference_latent(monkeypatch)
    EZKleinRefCanvas().run(latent, vae, image=image, has_image=True, max_refs=0)
    assert len(low) == 1

    high = _patch_reference_latent(monkeypatch)
    EZKleinRefCanvas().run(latent, vae, image=image, has_image=True, max_refs=9)
    assert len(high) == 4

    junk = _patch_reference_latent(monkeypatch)
    EZKleinRefCanvas().run(latent, vae, image=image, has_image=True, max_refs="nope")
    assert len(junk) == 3

    missing = _patch_reference_latent(monkeypatch)
    EZKleinRefCanvas().run(latent, vae, image=image, has_image=True, max_refs=None)
    assert len(missing) == 3


def test_ref_canvas_slices_a_bare_encoded_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _patch_reference_latent(monkeypatch)
    latent = {"samples": "empty"}
    encoded = _FakeBatch(["f0", "f1"])
    vae = _canvas_vae(encoded, [])
    EZKleinRefCanvas().run(
        latent, vae, image=_FakeImg(64, 64, batch=2), has_image=True, max_refs=3
    )
    assert [piece.frames for piece in seen] == [["f0"], ["f1"]]


def test_ref_canvas_keeps_one_reference_when_the_batch_wont_slice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _patch_reference_latent(monkeypatch)
    latent = {"samples": "empty"}
    encoded = {"samples": _NoSlice()}
    vae = _canvas_vae(encoded, [])
    EZKleinRefCanvas().run(
        latent, vae, image=_FakeImg(64, 64, batch=3), has_image=True, max_refs=3
    )
    assert len(seen) == 1
    assert seen[0] is encoded


def test_ref_canvas_fails_soft_when_a_late_append_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _patch_reference_latent(monkeypatch, fail_at=2)
    latent = {"samples": "empty"}
    encoded = {"samples": _FakeBatch(["f0", "f1", "f2"])}
    vae = _canvas_vae(encoded, [])
    image = _FakeImg(64, 64, batch=3)
    out = EZKleinRefCanvas().run(latent, vae, image=image, has_image=True, max_refs=3)
    assert len(seen) == 1
    assert len(out[0]["references"]) == 1
    assert out[1] is image


def test_ref_canvas_fails_soft_when_the_first_append_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_reference_latent(monkeypatch, fail_at=1)
    latent = {"samples": "empty"}
    encoded = {"samples": "ref"}
    vae = _canvas_vae(encoded, [])
    out = EZKleinRefCanvas().run(latent, vae, image=_FakeImg(64, 64), has_image=True)
    assert out[0] is latent


def test_encoded_frames_edges() -> None:
    assert _encoded_frames({"samples": "ref"}, 3) == [{"samples": "ref"}]
    assert _encoded_frames(None, 3) == [None]
    batch = _FakeBatch(["f0", "f1", "f2"])
    pieces = _encoded_frames({"samples": batch, "other": 1}, 2)
    assert [piece["samples"].frames for piece in pieces] == [["f0"], ["f1"]]
    assert all(piece["other"] == 1 for piece in pieces)
    assert [piece.frames for piece in _encoded_frames(batch, 2)] == [["f0"], ["f1"]]
    unsliceable = {"samples": _NoSlice()}
    assert _encoded_frames(unsliceable, 3) == [unsliceable]


def test_ref_limit_widget_values() -> None:
    assert _ref_limit(2) == 2
    assert _ref_limit(True) == 1
    assert _ref_limit(0) == 1
    assert _ref_limit(9) == 4
    assert _ref_limit("nope") == 3
    assert _ref_limit(None) == 3


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

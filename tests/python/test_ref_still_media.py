"""Real-world stills on the input side: EXIF orientation and honest reasons.

Hermetic: numpy, Pillow, and folder_paths are faked here, so the lane runs on a
host with none of the image stack installed.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_image.refs import (  # noqa: E402
    HEIC_STILL_HINT,
    EZOptionalImage,
    load_input_still,
    load_input_still_with_reason,
    still_failure_reason,
)


class _Arr:
    """ndarray stand-in that records ndim, channel count, and the batch index."""

    def __init__(self, ndim: int, channels: int, index: object = None) -> None:
        self.ndim = ndim
        self.channels = channels
        self.index = index

    def astype(self, _kind: object) -> "_Arr":
        return self

    def __truediv__(self, _n: object) -> "_Arr":
        return self

    def __getitem__(self, index: object) -> "_Arr":
        return _Arr(self.ndim + 1, self.channels, index)


class _Image:
    """PIL image stand-in that reports the mode it was last converted to."""

    def __init__(self, mode: str = "RGBA", label: str = "stored") -> None:
        self.mode = mode
        self.label = label

    def convert(self, mode: str) -> "_Image":
        self.mode = mode
        return self

    def __enter__(self) -> "_Image":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None


class _Stage:
    """Fakes for ``numpy``, ``PIL``, and ``folder_paths``, with calls recorded."""

    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        root: Path,
        image: _Image | None = None,
        *,
        with_image_ops: bool = True,
        transpose_raises: bool = False,
        open_raises: bool = False,
        ndim: int = 3,
    ) -> None:
        self.root = root
        self.image = image or _Image()
        self.opened: list[str] = []
        self.transposed: list[object] = []
        self.asarrayed: list[object] = []
        self.transposed_out = _Image("RGB", "transposed")
        self._ndim = ndim

        def _open(path: object) -> _Image:
            text = str(path)
            if not Path(text).is_file():
                raise FileNotFoundError(text)
            if open_raises or Path(text).suffix.lower() in {".heic", ".heif"}:
                raise OSError("cannot identify image file")
            self.opened.append(text)
            return self.image

        def _transpose(presented: object) -> _Image:
            self.transposed.append(presented)
            if transpose_raises:
                raise OSError("no exif")
            return self.transposed_out

        def _asarray(presented: object) -> _Arr:
            self.asarrayed.append(presented)
            mode = getattr(presented, "mode", "RGB")
            return _Arr(self._ndim, 3 if mode == "RGB" else 4)

        image_module = types.ModuleType("PIL.Image")
        image_module.open = _open  # type: ignore[attr-defined]
        package = types.ModuleType("PIL")
        package.Image = image_module  # type: ignore[attr-defined]
        if with_image_ops:
            ops = types.ModuleType("PIL.ImageOps")
            ops.exif_transpose = _transpose  # type: ignore[attr-defined]
            package.ImageOps = ops  # type: ignore[attr-defined]
        folder = types.SimpleNamespace(
            get_annotated_filepath=lambda name: str(root / str(name))
        )
        monkeypatch.setitem(sys.modules, "PIL", package)
        monkeypatch.setitem(sys.modules, "PIL.Image", image_module)
        if with_image_ops:
            monkeypatch.setitem(
                sys.modules, "PIL.ImageOps", sys.modules["PIL"].ImageOps
            )
        else:
            monkeypatch.delitem(sys.modules, "PIL.ImageOps", raising=False)
        monkeypatch.setitem(
            sys.modules, "numpy", types.SimpleNamespace(asarray=_asarray, float32="f32")
        )
        monkeypatch.setitem(sys.modules, "folder_paths", folder)


def test_exif_orientation_applied_before_the_rgb_convert(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The stored pixels are transposed first, then converted, then batched."""
    stored = _Image("RGBA", "stored")
    stage = _Stage(monkeypatch, tmp_path, stored)
    (tmp_path / "phone.jpg").write_bytes(b"jpeg")

    loaded = load_input_still("phone.jpg")

    assert stage.transposed == [stored]
    assert stage.asarrayed == [stage.transposed_out]
    assert loaded is not None
    assert loaded.ndim == 4
    assert loaded.channels == 3
    assert loaded.index == (None, Ellipsis)


def test_still_loads_when_pillow_has_no_imageops(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A Pillow build without ImageOps still yields the BHWC batch."""
    stored = _Image("RGBA", "stored")
    stage = _Stage(monkeypatch, tmp_path, stored, with_image_ops=False)
    (tmp_path / "phone.jpg").write_bytes(b"jpeg")

    loaded = load_input_still("phone.jpg")

    assert stage.transposed == []
    assert stage.asarrayed == [stored]
    assert loaded is not None
    assert loaded.ndim == 4
    assert loaded.channels == 3


def test_still_loads_when_exif_transpose_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Odd or missing EXIF keeps the pixels as stored instead of failing."""
    stored = _Image("RGB", "stored")
    stage = _Stage(monkeypatch, tmp_path, stored, transpose_raises=True)
    (tmp_path / "phone.jpg").write_bytes(b"jpeg")

    loaded = load_input_still("phone.jpg")

    assert stage.asarrayed == [stored]
    assert loaded is not None
    assert loaded.channels == 3


def test_heic_pick_reports_an_export_hint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A phone HEIC is named back to the operator with what to do about it."""
    _Stage(monkeypatch, tmp_path)
    (tmp_path / "beach.heic").write_bytes(b"ftypheic")

    loaded, reason = load_input_still_with_reason("beach.heic")

    assert loaded is None
    assert "beach.heic" in reason
    assert "JPG" in reason and "PNG" in reason
    assert HEIC_STILL_HINT in reason


def test_unreadable_pick_names_the_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A corrupt pick is not reported as "no pick"."""
    _Stage(monkeypatch, tmp_path, open_raises=True)
    (tmp_path / "broken.png").write_bytes(b"\x00\x00")

    loaded, reason = load_input_still_with_reason("broken.png")

    assert loaded is None
    assert "broken.png" in reason
    assert "HEIC" not in reason


def test_flat_pixels_are_not_a_still(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A decodable file whose pixels are not HWC is refused with a reason."""
    _Stage(monkeypatch, tmp_path, ndim=2)
    (tmp_path / "strange.png").write_bytes(b"png")

    loaded, reason = load_input_still_with_reason("strange.png")

    assert loaded is None
    assert "strange.png" in reason


def test_empty_and_unresolved_picks_stay_silent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An empty picker or an unresolvable name keeps the plain no-pick line."""
    stage = _Stage(monkeypatch, tmp_path)

    assert load_input_still_with_reason("") == (None, "")
    assert load_input_still_with_reason("   ") == (None, "")

    monkeypatch.setitem(sys.modules, "folder_paths", None)
    assert load_input_still_with_reason("anything.png") == (None, "")
    assert load_input_still("anything.png") is None

    monkeypatch.setitem(sys.modules, "folder_paths", types.SimpleNamespace())
    assert load_input_still_with_reason("anything.png") == (None, "")

    monkeypatch.setitem(sys.modules, "numpy", None)
    (tmp_path / "beach.heic").write_bytes(b"ftypheic")
    assert load_input_still_with_reason("beach.heic") == (None, "")
    assert stage.opened == []


def test_pick_with_no_file_behind_it_names_the_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A picker left pointing at a deleted plate is not an empty node."""
    _Stage(monkeypatch, tmp_path)

    loaded, reason = load_input_still_with_reason("gone.png")

    assert loaded is None
    assert "gone.png" in reason
    assert "HEIC" not in reason


def test_still_failure_reason_agrees_with_the_loader(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The node's reason line and the loader's second slot are the same text."""
    _Stage(monkeypatch, tmp_path)
    (tmp_path / "beach.heic").write_bytes(b"ftypheic")

    assert (
        still_failure_reason("beach.heic")
        == load_input_still_with_reason("beach.heic")[1]
    )
    assert still_failure_reason("") == ""


class _FakeImg:
    """Batch stand-in that satisfies ``_image_present`` and ``_batch_len``."""

    def __init__(self, height: int = 64, width: int = 64, batch: int = 1) -> None:
        self.shape = (batch, height, width, 3)


def test_node_line_names_the_unreadable_pick(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """One good still plus one HEIC keeps the count and adds the reason."""
    _Stage(monkeypatch, tmp_path)
    (tmp_path / "beach.heic").write_bytes(b"ftypheic")
    good = _FakeImg()
    monkeypatch.setattr(
        "ez_image.refs.load_input_still",
        lambda name: good if str(name) == "good.png" else None,
    )

    out = EZOptionalImage().run(filename="good.png", filename_2="beach.heic")

    text = out["ui"]["text"][0]
    assert len(out["ui"]["text"]) == 1
    assert text.startswith("1 reference still; ")
    assert "beach.heic" in text and "JPG" in text


def test_node_line_says_no_still_and_why(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A lone HEIC is not reported as an empty picker."""
    _Stage(monkeypatch, tmp_path)
    (tmp_path / "beach.heic").write_bytes(b"ftypheic")
    monkeypatch.setattr("ez_image.refs.load_input_still", lambda _name: None)

    out = EZOptionalImage().run(filename="beach.heic")

    text = out["ui"]["text"][0]
    assert text.startswith("no reference still; ")
    assert "beach.heic" in text
    assert out["result"] == (None, 0, False)


def test_node_line_untouched_without_a_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The existing count lines stay byte-identical when nothing failed."""
    fake = _FakeImg()
    monkeypatch.setattr("ez_image.refs.load_input_still", lambda _name: fake)
    monkeypatch.setattr("ez_image.refs.still_failure_reason", lambda _name: "unused")

    out: dict[str, Any] = EZOptionalImage().run(filename="hero.png")
    assert out["ui"]["text"] == ("1 reference still",)

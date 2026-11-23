"""Real-world stills on the input side: EXIF, alpha, and honest reasons.

Hermetic: numpy, Pillow, and folder_paths are faked here, so the lane runs on a
host with none of the image stack installed.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_image.refs import (  # noqa: E402
    HEIC_STILL_HINT,
    EZOptionalImage,
    flatten_alpha,
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


WHITE = (255, 255, 255)
"""The flat backdrop the loader promises to composite a stored alpha onto."""

TRANSPARENT_ALPHA = (0, 255)
"""Alpha extrema with see-through pixels stored under the RGB."""

OPAQUE_ALPHA = (255, 255)
"""Alpha extrema with nothing transparent left to flatten."""

PALETTE_T_TRNS = 1
"""Palette index a ``P`` image marks see-through with its ``tRNS`` chunk."""


class _Alpha:
    """Alpha band stand-in that reports the extrema the loader probes."""

    def __init__(self, extrema: tuple[int, int]) -> None:
        self.extrema = extrema

    def getextrema(self) -> tuple[int, int]:
        return self.extrema


class _Image:
    """PIL image stand-in that reports its bands and records what was done.

    ``convert`` drops an alpha band the way Pillow does and says so through
    ``dropped_alpha``, so a test can tell a flattened composite apart from the
    silent drop that feeds the model the RGB stored under the alpha. A ``P``
    image carrying ``info["transparency"]`` converts to an RGBA stand-in the
    way Pillow honours a ``tRNS`` chunk, and records it in ``rgba_views``.
    """

    def __init__(
        self,
        mode: str = "RGBA",
        label: str = "stored",
        alpha: tuple[int, int] = OPAQUE_ALPHA,
        *,
        paste_raises: bool = False,
        info: dict[str, object] | None = None,
        convert_raises: bool = False,
    ) -> None:
        self.mode = mode
        self.label = label
        self.alpha = alpha
        self.paste_raises = paste_raises
        self.convert_raises = convert_raises
        self.info: dict[str, object] = {} if info is None else dict(info)
        self.size = (8, 6)
        self.channel_reads: list[str] = []
        self.converted: list[str] = []
        self.rgba_views: list["_Image"] = []
        self.dropped_alpha = False
        self.pasted: list[tuple["_Image", "_Alpha"]] = []

    def getbands(self) -> tuple[str, ...]:
        return tuple(self.mode)

    def getchannel(self, band: str) -> _Alpha:
        self.channel_reads.append(band)
        if band not in self.getbands():
            raise ValueError(f"no {band} band in {self.mode}")
        return _Alpha(self.alpha)

    def convert(self, mode: str) -> "_Image":
        self.converted.append(mode)
        if self.convert_raises:
            raise OSError("this Pillow cannot expand the palette")
        if (
            mode == "RGBA"
            and self.mode == "P"
            and self.info.get("transparency") is not None
        ):
            view = _Image("RGBA", f"{self.label} as RGBA", self.alpha)
            self.rgba_views.append(view)
            return view
        if "A" in self.getbands() and "A" not in tuple(mode):
            self.dropped_alpha = True
        self.mode = mode
        return self

    def paste(self, source: "_Image", box: object, mask: "_Alpha") -> None:
        if self.paste_raises:
            raise OSError("paste refused")
        self.pasted.append((source, mask))

    def __enter__(self) -> "_Image":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None


class _OddPalette:
    """Palette image whose ``info`` is not the table the probe reads.

    Real Pillow hands back a dict here; this is the shape a stubbed or forked
    build could hand back instead, and the flatten must read it as "nothing
    transparent" rather than lose the still.
    """

    mode = "P"
    info: object = "not a table"

    def getbands(self) -> tuple[str, ...]:
        return ("P",)


class _Stage:
    """Fakes for ``numpy``, ``PIL``, and ``folder_paths``, with calls recorded."""

    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        root: Path,
        image: _Image | None = None,
        *,
        with_image_ops: bool = True,
        with_image: bool = True,
        transpose_raises: bool = False,
        open_raises: bool = False,
        paste_raises: bool = False,
        ndim: int = 3,
    ) -> None:
        self.root = root
        self.image = image or _Image()
        self.opened: list[str] = []
        self.transposed: list[object] = []
        self.asarrayed: list[object] = []
        self.new_backdrops: list[tuple[str, object, object]] = []
        self.transposed_out = _Image(
            self.image.mode, "transposed", self.image.alpha, info=self.image.info
        )
        self.flat_out = _Image("RGB", "flat", paste_raises=paste_raises)
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

        def _new(mode: str, size: object, color: object) -> _Image:
            self.new_backdrops.append((mode, size, color))
            return self.flat_out

        image_module = types.ModuleType("PIL.Image")
        image_module.open = _open  # type: ignore[attr-defined]
        image_module.new = _new  # type: ignore[attr-defined]
        package = types.ModuleType("PIL")
        if with_image:
            package.Image = image_module  # type: ignore[attr-defined]
        if with_image_ops:
            ops = types.ModuleType("PIL.ImageOps")
            ops.exif_transpose = _transpose  # type: ignore[attr-defined]
            package.ImageOps = ops  # type: ignore[attr-defined]
        folder = types.SimpleNamespace(
            get_annotated_filepath=lambda name: str(root / str(name))
        )
        monkeypatch.setitem(sys.modules, "PIL", package)
        if with_image:
            monkeypatch.setitem(sys.modules, "PIL.Image", image_module)
        else:
            monkeypatch.delitem(sys.modules, "PIL.Image", raising=False)
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


def test_cutout_png_flattens_its_alpha_onto_white(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A transparent PNG loads as the flat white plate, not the stored RGB."""
    stored = _Image("RGBA", "stored", TRANSPARENT_ALPHA)
    stage = _Stage(monkeypatch, tmp_path, stored)
    (tmp_path / "cutout.png").write_bytes(b"png")

    loaded = load_input_still("cutout.png")

    assert stage.new_backdrops == [("RGB", stage.transposed_out.size, WHITE)]
    assert [source for source, _mask in stage.flat_out.pasted] == [stage.transposed_out]
    assert [mask.extrema for _source, mask in stage.flat_out.pasted] == [
        TRANSPARENT_ALPHA
    ]
    assert stage.transposed_out.dropped_alpha is False
    assert stage.flat_out.converted == ["RGB"]
    assert stage.asarrayed == [stage.flat_out]
    assert loaded is not None
    assert loaded.ndim == 4
    assert loaded.channels == 3


def test_fully_opaque_alpha_keeps_the_plain_convert_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An alpha band with nothing transparent in it earns no composite."""
    stored = _Image("RGBA", "stored", OPAQUE_ALPHA)
    stage = _Stage(monkeypatch, tmp_path, stored)
    (tmp_path / "flat.png").write_bytes(b"png")

    loaded = load_input_still("flat.png")

    assert stage.transposed_out.channel_reads == ["A"]
    assert stage.new_backdrops == []
    assert stage.flat_out.pasted == []
    assert stage.transposed_out.converted == ["RGB"]
    assert stage.transposed_out.dropped_alpha is True
    assert stage.asarrayed == [stage.transposed_out]
    assert loaded is not None
    assert loaded.channels == 3


def test_rgb_still_never_reaches_the_composite(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An ordinary JPG is not probed for a band it cannot carry."""
    stored = _Image("RGB", "stored")
    stage = _Stage(monkeypatch, tmp_path, stored)
    (tmp_path / "hero.jpg").write_bytes(b"jpeg")

    loaded = load_input_still("hero.jpg")

    assert stage.transposed_out.channel_reads == []
    assert stage.new_backdrops == []
    assert stage.flat_out.pasted == []
    assert stage.transposed_out.converted == ["RGB"]
    assert stage.transposed_out.dropped_alpha is False
    assert stage.asarrayed == [stage.transposed_out]
    assert loaded is not None
    assert loaded.channels == 3


def test_a_failed_composite_still_loads_the_still(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A composite this Pillow cannot run keeps the still instead of failing."""
    stored = _Image("RGBA", "stored", TRANSPARENT_ALPHA)
    stage = _Stage(monkeypatch, tmp_path, stored, paste_raises=True)
    (tmp_path / "cutout.png").write_bytes(b"png")

    loaded, reason = load_input_still_with_reason("cutout.png")

    assert reason == ""
    assert stage.transposed_out.converted == ["RGB"]
    assert stage.asarrayed == [stage.transposed_out]
    assert loaded is not None
    assert loaded.channels == 3


def test_alpha_flattens_without_imageops(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The flatten does not ride on the EXIF step: no ImageOps still flattens."""
    stored = _Image("RGBA", "stored", TRANSPARENT_ALPHA)
    stage = _Stage(monkeypatch, tmp_path, stored, with_image_ops=False)
    (tmp_path / "cutout.png").write_bytes(b"png")

    loaded = load_input_still("cutout.png")

    assert stage.transposed == []
    assert stage.new_backdrops == [("RGB", stored.size, WHITE)]
    assert [source for source, _mask in stage.flat_out.pasted] == [stored]
    assert stage.asarrayed == [stage.flat_out]
    assert loaded is not None
    assert loaded.channels == 3


def test_alpha_survives_a_pillow_build_without_the_image_module(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A Pillow that cannot hand back ``Image`` keeps the stored pixels.

    The composite needs ``Image.new`` to lay the backdrop down. When that
    import fails the flatten is a no-op and the operator still gets a still,
    exactly as :func:`_exif_transpose` falls back on junk EXIF.
    """
    stored = _Image("RGBA", "stored", TRANSPARENT_ALPHA)
    stage = _Stage(monkeypatch, tmp_path, stored, with_image=False)

    assert flatten_alpha(stored, WHITE) is stored
    assert stage.new_backdrops == []


def test_palette_png_with_a_transparent_index_flattens_onto_white(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A sticker saved as palette PNG flattens even though it has no alpha band.

    A ``P`` image that declares its see-through index in a ``tRNS`` chunk still
    reports ``getbands() == ("P",)``, so the band probe alone cannot see the
    transparency and the palette colour stored under it reaches the model.
    """
    stored = _Image(
        "P", "sticker", TRANSPARENT_ALPHA, info={"transparency": PALETTE_T_TRNS}
    )
    stage = _Stage(monkeypatch, tmp_path, stored)
    (tmp_path / "sticker.png").write_bytes(b"png")

    loaded = load_input_still("sticker.png")

    assert stage.transposed_out.converted == ["RGBA"]
    assert stage.new_backdrops == [("RGB", stage.transposed_out.size, WHITE)]
    assert [source for source, _mask in stage.flat_out.pasted] == [
        stage.transposed_out.rgba_views[0]
    ]
    assert [mask.extrema for _source, mask in stage.flat_out.pasted] == [
        TRANSPARENT_ALPHA
    ]
    assert stage.flat_out.converted == ["RGB"]
    assert stage.asarrayed == [stage.flat_out]
    assert loaded is not None
    assert loaded.channels == 3


def test_opaque_palette_png_keeps_the_plain_convert_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A palette PNG whose declared index is not transparent earns no composite."""
    stage = _Stage(monkeypatch, tmp_path)
    indexed = _Image("P", "poster", OPAQUE_ALPHA, info={"transparency": PALETTE_T_TRNS})

    assert flatten_alpha(indexed, WHITE) is indexed
    assert indexed.converted == ["RGBA"]
    assert stage.new_backdrops == []
    assert stage.flat_out.pasted == []


def test_palette_png_without_a_transparency_chunk_is_returned_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An indexed PNG that stores no transparency keeps the single convert."""
    stage = _Stage(monkeypatch, tmp_path)
    indexed = _Image("P", "poster")

    assert flatten_alpha(indexed, WHITE) is indexed
    assert indexed.converted == []
    assert indexed.channel_reads == []
    assert stage.new_backdrops == []
    assert stage.flat_out.pasted == []


def test_a_palette_whose_info_is_no_table_is_left_alone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An ``info`` that is not a dict reads as no transparency, not a broken still."""
    stage = _Stage(monkeypatch, tmp_path)
    odd = _OddPalette()

    assert flatten_alpha(odd, WHITE) is odd
    assert stage.new_backdrops == []
    assert stage.flat_out.pasted == []


def test_a_palette_that_cannot_expand_keeps_the_stored_pixels(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A Pillow that refuses the RGBA view is a no-op, not a lost still."""
    stage = _Stage(monkeypatch, tmp_path)
    indexed = _Image(
        "P",
        "sticker",
        TRANSPARENT_ALPHA,
        info={"transparency": PALETTE_T_TRNS},
        convert_raises=True,
    )

    assert flatten_alpha(indexed, WHITE) is indexed
    assert indexed.converted == ["RGBA"]
    assert stage.new_backdrops == []
    assert stage.flat_out.pasted == []


def test_a_grayscale_png_that_declares_transparency_flattens_onto_white(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A gray PNG with a ``tRNS`` value is a cutout too, not a solid tile.

    Such a file reports ``mode == "L"`` and ``getbands() == ("L",)``: the
    see-through value lives in ``info`` alone. Real Pillow gives its RGBA view
    alpha 0 wherever a pixel equals that value, so an un-flattened pick hands
    the model the gray stored under transparency instead of the white the
    operator saw.
    """
    stored = _Image("L", "ghost", TRANSPARENT_ALPHA, info={"transparency": 60})
    stage = _Stage(monkeypatch, tmp_path, stored)
    (tmp_path / "ghost.png").write_bytes(b"png")

    loaded = load_input_still("ghost.png")

    assert stage.transposed_out.converted == ["RGBA"]
    assert stage.transposed_out.channel_reads == ["A"]
    assert stage.new_backdrops == [("RGB", stage.transposed_out.size, WHITE)]
    assert [mask.extrema for _source, mask in stage.flat_out.pasted] == [
        TRANSPARENT_ALPHA
    ]
    assert stage.asarrayed == [stage.flat_out]
    assert loaded is not None
    assert loaded.channels == 3


def test_a_lab_still_is_never_composited_through_its_colour(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A CIELAB TIFF keeps its pixels: the ``A`` in ``LAB`` is a colour axis.

    ``getbands()`` names the green-red axis ``"A"``, so a band probe reads a Lab
    still as alpha-bearing and pastes it onto the backdrop through its colour.
    The mode names the alpha band instead, and ``LAB`` ends on its ``"B"``.
    """
    stored = _Image("LAB", "lab", TRANSPARENT_ALPHA)
    stage = _Stage(monkeypatch, tmp_path, stored)
    (tmp_path / "swatch.tif").write_bytes(b"tif")

    loaded = load_input_still("swatch.tif")

    assert stage.transposed_out.channel_reads == []
    assert stage.new_backdrops == []
    assert stage.flat_out.pasted == []
    assert stage.transposed_out.converted == ["RGB"]
    assert stage.asarrayed == [stage.transposed_out]
    assert loaded is not None
    assert loaded.channels == 3


def test_a_premultiplied_still_flattens_from_its_rgba_view(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``RGBa`` is alpha-bearing too, and its stored pixels need un-premultiplying.

    Pillow spells that band a lower-case ``"a"``, which a band probe looking for
    ``"A"`` misses entirely, and the values are pre-multiplied, so the composite
    takes the RGBA view Pillow builds rather than the raw band.
    """
    stored = _Image("RGBa", "premultiplied", TRANSPARENT_ALPHA)
    stage = _Stage(monkeypatch, tmp_path, stored)
    (tmp_path / "premult.png").write_bytes(b"png")

    loaded = load_input_still("premult.png")

    assert stage.transposed_out.converted == ["RGBA"]
    assert stage.transposed_out.channel_reads == ["A"]
    assert stage.new_backdrops == [("RGB", stage.transposed_out.size, WHITE)]
    assert [source for source, _mask in stage.flat_out.pasted] == [
        stage.transposed_out
    ]
    assert [mask.extrema for _source, mask in stage.flat_out.pasted] == [
        TRANSPARENT_ALPHA
    ]
    assert stage.asarrayed == [stage.flat_out]
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

    out = EZOptionalImage().run(filename="hero.png")
    assert out["ui"]["text"] == ("1 reference still",)

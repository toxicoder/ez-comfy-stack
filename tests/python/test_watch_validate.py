"""Hermetic tests for the Watch Face Format compliance gate.

Each case starts from a real generated project, breaks exactly one artefact in
it, and asserts the exact finding codes the gate reports, so a rule that went
quiet fails here rather than in a Play review round. The PNG path is driven with
hand-built chunks so every scanline filter, the Paeth predictor, and every
malformed-stream exit run for real. Nothing here touches Docker, Gradle, or the
network: the tree lives under pytest's temporary directories.
"""

from __future__ import annotations

import json
import shutil
import struct
import sys
import zlib
from collections.abc import Sequence
from pathlib import Path
from xml.etree import ElementTree

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_watch import validate  # noqa: E402
from ez_watch.catalog import MAX_COLOR_OPTIONS, MAX_COMPLICATION_SLOTS, by_slug  # noqa: E402
from ez_watch.project import MIN_PREVIEW_EDGE, build_face  # noqa: E402

BASELINE_SLUG = "meridian-analog"
"""Round two-slot analog face: the cheapest build that clears the gate clean."""

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
"""First eight bytes of every PNG, used to build files the gate has to sniff."""

BULK_XML_BYTES = validate.MAX_XML_SOURCE_BYTES + 1
"""Smallest XML payload that tips the WO-G11 source budget over."""

TRANSPARENT_SAMPLE = 4
"""Alpha value below the gate's threshold, so a pixel counts as transparent."""

DISC = (
    '<PartDraw x="0" y="0" width="450" height="450" name="disc">'
    '<Ellipse x="3" y="3" width="444" height="444">'
    '<Stroke color="#FFFFFFFF" thickness="6" />'
    "</Ellipse>"
    '<Variant mode="AMBIENT" target="alpha" value="96" />'
    "</PartDraw>"
)
"""Smallest scene body that satisfies the element, ambient, and memory rules."""

COLOR_CONFIGURATION = (
    '<ColorConfiguration defaultValue="0" displayName="@string/theme_color_display_name"'
    ' id="themeColor">'
    '<ColorOption colors="#E0B155FF #F7E0A8FF #FFFBF0FF"'
    ' displayName="@string/theme_color_0_display_name" id="0" />'
    "</ColorConfiguration>"
)
"""One legal colourway, which keeps the face configurable for the Editable check."""

AMBIENT_VARIANT = '<Variant mode="AMBIENT" target="alpha" value="255" />'
"""Ambient variant a drawing layer needs to avoid the WO-P7 family warning."""

PREVIEW_ELEMENT = '<Preview value="@drawable/preview" />'
"""The one required child of ``watch_face_info.xml``."""

CATEGORY_ELEMENT = '<Category value="Classic" />'
"""Optional child whose absence costs a warning."""

EDITABLE_ELEMENT = '<Editable value="true" />'
"""Declaration that must agree with the face's user configurations."""

WATCH_FEATURE_ELEMENT = '<uses-feature android:name="android.hardware.type.watch" />'
"""The watch hardware declaration."""

STANDALONE_ELEMENT = (
    '<meta-data android:name="com.google.android.wearable.standalone" android:value="true" />'
)
"""Standalone app meta-data Play requires on a code-free face."""

FORMAT_VERSION_ELEMENT = (
    '<property android:name="com.google.wear.watchface.format.version" android:value="4" />'
)
"""Watch Face Format version property Play requires."""

APPLICATION_ELEMENT = '<application android:hasCode="false" android:label="@string/watch_face_name">'
"""Opening tag of a code-free application element."""

COMPLIANT_APPLICATION: tuple[str, ...] = (
    APPLICATION_ELEMENT,
    STANDALONE_ELEMENT,
    FORMAT_VERSION_ELEMENT,
    "</application>",
)
"""Markup of a manifest application block that raises no finding."""

LIT_PIXEL = (255, 255, 255, 255)
"""Opaque white pixel: bright enough to count as illuminated."""

DIM_PIXEL = (5, 5, 5, 255)
"""Opaque near-black pixel: too dark to count as illuminated."""

DARK_PIXEL = (10, 0, 20, 255)
"""Opaque deep blue pixel: weighted luma keeps it below the lit threshold."""

MID_PIXEL = (200, 128, 64, 255)
"""Opaque amber pixel whose channels differ enough to expose a bad filter."""

CHECKER_PIXELS = bytes((*LIT_PIXEL, *MID_PIXEL, *DIM_PIXEL, *DARK_PIXEL))
"""Two lit and two unlit opaque pixels, the reference image for the filter tests."""


# --------------------------------------------------------------------------
# fixtures and helpers that need no build
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the baseline face once for the whole module.

    Args:
        tmp_path_factory: pytest's session-wide temporary directories.

    Returns:
        The pristine project folder the gate accepts untouched.
    """
    out = tmp_path_factory.mktemp("validate")
    build_face(by_slug(BASELINE_SLUG), out, preview_edge=MIN_PREVIEW_EDGE)
    return out / BASELINE_SLUG


@pytest.fixture
def tree(tmp_path: Path, built: Path) -> Path:
    """Copy the pristine build so each test may break one file in peace.

    Args:
        tmp_path: pytest's per-test temporary directory.
        built: The pristine project folder.

    Returns:
        A writable copy of the project.
    """
    target = tmp_path / BASELINE_SLUG
    shutil.copytree(built, target)
    return target


def _codes(findings: Sequence[validate.Finding]) -> list[str]:
    """Collect the codes the gate reported.

    Args:
        findings: Findings from one run.

    Returns:
        Sorted code list, so a test compares against the exact set it expects.
    """
    return sorted(finding.code for finding in findings)


def _write(root: Path, relative: str, data: str | bytes) -> Path:
    """Write one file inside the project tree.

    Args:
        root: Project folder.
        relative: Project-relative path.
        data: Text or bytes to store.

    Returns:
        The path written.
    """
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
    return path


def _delete(root: Path, relative: str) -> None:
    """Remove one file from the project tree.

    Args:
        root: Project folder.
        relative: Project-relative path.
    """
    (root / relative).unlink()


def _second_copy(name: str, built: Path, tmp_path: Path) -> Path:
    """Copy the pristine build into a second folder.

    Args:
        name: Folder name to create.
        built: The pristine project folder.
        tmp_path: pytest's per-test temporary directory.

    Returns:
        The copy, so one test can score two independent variants.
    """
    target = tmp_path / name
    shutil.copytree(built, target)
    return target


def _face_xml(
    body: str = DISC,
    *,
    width: str = "450",
    height: str = "450",
    configurations: str = COLOR_CONFIGURATION,
    scene_count: int = 1,
) -> str:
    """Return a complete face document carrying the pieces a test asks for.

    Args:
        body: Markup placed inside every ``<Scene>``.
        width: Value of the root ``width`` attribute.
        height: Value of the root ``height`` attribute.
        configurations: Markup placed inside ``<UserConfigurations>``; the
            default keeps the face configurable so the generated ``Editable``
            declaration still agrees with it.
        scene_count: How many ``<Scene>`` elements to emit.

    Returns:
        Text ready to write over ``res/raw/watchface.xml``.
    """
    scenes = f'<Scene backgroundColor="#000000FF">{body}</Scene>' * scene_count
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<WatchFace clipShape="CIRCLE" height="{height}" width="{width}">'
        f"<UserConfigurations>{configurations}</UserConfigurations>"
        f"{scenes}</WatchFace>\n"
    )


def _slot_xml(
    *,
    slot_id: str = "1",
    supported: str = "SHORT_TEXT EMPTY",
    bounds: Sequence[str] = ('<BoundingOval x="0" y="0" width="78" height="34" />',),
    complications: Sequence[str] = ("SHORT_TEXT", "EMPTY"),
    provider: bool = False,
    width: str = "78",
    height: str = "34",
) -> str:
    """Return one ``ComplicationSlot`` element.

    Args:
        slot_id: Value of the ``slotId`` attribute.
        supported: Value of ``supportedTypes``, space separated.
        bounds: Bounding-shape elements to declare inside the slot.
        complications: ``Complication type`` values to declare.
        provider: Whether to declare a ``DefaultProviderPolicy``.
        width: Value of the ``width`` attribute.
        height: Value of the ``height`` attribute.

    Returns:
        Markup for a slot that is otherwise legal.
    """
    declared = [f'<Complication type="{kind}" />' for kind in complications]
    provider_element = "<DefaultProviderPolicy />" if provider else ""
    return (
        f'<ComplicationSlot displayName="@string/slot_1_display_name" height="{height}"'
        f' slotId="{slot_id}" supportedTypes="{supported}" width="{width}" x="186" y="150">'
        f"{''.join(bounds)}{''.join(declared)}{provider_element}{AMBIENT_VARIANT}"
        "</ComplicationSlot>"
    )


def _info_document(children: Sequence[str]) -> str:
    """Return a ``watch_face_info.xml`` with the children a test asks for.

    Args:
        children: Elements to place inside ``<WatchFaceInfo>``.

    Returns:
        Text ready to write over ``res/xml/watch_face_info.xml``.
    """
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f"<WatchFaceInfo>{''.join(children)}</WatchFaceInfo>\n"
    )


def _manifest_document(children: Sequence[str], *, watch_feature: bool = True) -> str:
    """Return an ``AndroidManifest.xml`` with the markup a test asks for.

    Args:
        children: Markup placed inside ``<manifest>``, application shell included.
        watch_feature: Whether to declare the watch uses-feature.

    Returns:
        Text ready to write over ``AndroidManifest.xml``.
    """
    features = WATCH_FEATURE_ELEMENT if watch_feature else ""
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<manifest xmlns:android="{validate.ANDROID_NAMESPACE}">'
        f"{features}{''.join(children)}</manifest>\n"
    )


def _listing_json(root: Path, **overrides: object) -> None:
    """Rewrite ``manifest.json`` with its listing block patched.

    Args:
        root: Project folder.
        **overrides: Listing keys to replace; a None value drops the key.
    """
    path = root / validate.MANIFEST_JSON
    document = json.loads(path.read_text(encoding="utf-8"))
    listing = document["listing"]
    for key, value in overrides.items():
        if value is None:
            listing.pop(key, None)
        else:
            listing[key] = value
    path.write_text(json.dumps(document), encoding="utf-8")


def _info_element(document: str) -> ElementTree.Element:
    """Parse a face-info document so a predicate can be scored directly.

    Args:
        document: Text of a ``watch_face_info.xml``.

    Returns:
        The root element.
    """
    return ElementTree.fromstring(document)



def _chunk(kind: bytes, payload: bytes) -> bytes:
    """Wrap a payload in a PNG chunk.

    Args:
        kind: Four-byte chunk type.
        payload: Chunk body.

    Returns:
        Length, type, body, and CRC.
    """
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _png_from_chunks(
    chunks: Sequence[tuple[bytes, bytes]], *, signature: bytes = PNG_SIGNATURE
) -> bytes:
    """Assemble a PNG file from chunk pairs.

    Args:
        chunks: Chunk type and payload pairs, in file order.
        signature: Bytes in front of the first chunk; junk fails the sniff.

    Returns:
        Complete file bytes.
    """
    return signature + b"".join(_chunk(kind, payload) for kind, payload in chunks)


def _reference_paeth(left: int, up: int, corner: int) -> int:
    """Predict a sample from its three neighbours, per the PNG specification.

    Written from the published algorithm so the filter tests do not reuse the
    predictor they measure.

    Args:
        left: Sample to the left.
        up: Sample above.
        corner: Sample above and to the left.

    Returns:
        The neighbour closest to the plane estimate.
    """
    plane = left + up - corner
    distances = (abs(plane - left), abs(plane - up), abs(plane - corner))
    return (left, up, corner)[distances.index(min(distances))]


def _filter_scanline(kind: int, line: bytes, above: bytes | None, channels: int) -> bytes:
    """Encode one scanline with one of the five PNG filters.

    Args:
        kind: Filter type, 0 through 4.
        line: Raw samples of the row.
        above: Raw samples of the row above, or None for the first row.
        channels: Bytes per pixel.

    Returns:
        The filter byte followed by the encoded samples.
    """
    encoded = bytearray()
    for index, value in enumerate(line):
        left = line[index - channels] if index >= channels else 0
        up = above[index] if above is not None else 0
        corner = above[index - channels] if above is not None and index >= channels else 0
        predictor = (0, left, up, (left + up) >> 1, _reference_paeth(left, up, corner))[kind]
        encoded.append((value - predictor) & 0xFF)
    return bytes([kind]) + bytes(encoded)


def _png_image(
    width: int,
    height: int,
    pixels: bytes,
    *,
    channels: int = 4,
    color_type: int = 6,
    bit_depth: int = 8,
    filters: Sequence[int] = (0,),
    extra_chunks: Sequence[tuple[bytes, bytes]] = (),
    tail: bytes = b"",
) -> bytes:
    """Encode raw samples as a PNG.

    Args:
        width: Image width; 0 exercises the empty-image exit.
        height: Image height.
        pixels: ``width * height * channels`` samples, row after row.
        channels: Bytes per pixel.
        color_type: PNG colour type declared in the header.
        bit_depth: Bits per channel declared in the header.
        filters: Filter type per scanline; the last entry repeats.
        extra_chunks: Chunks inserted after ``IHDR``, such as a ``tRNS`` block
            or the private block that pushes a file past a byte budget.
        tail: Bytes appended after ``IEND``, such as a truncated chunk.

    Returns:
        Complete file bytes.
    """
    stride = width * channels
    rows = bytearray()
    for row in range(height):
        start, stop = row * stride, (row + 1) * stride
        above = pixels[start - stride : start] if row else None
        kind = filters[row] if row < len(filters) else filters[-1]
        rows += _filter_scanline(kind, pixels[start:stop], above, channels)
    header = struct.pack(">IIBBBBB", width, height, bit_depth, color_type, 0, 0, 0)
    chunks: list[tuple[bytes, bytes]] = [(b"IHDR", header), *extra_chunks]
    chunks.append((b"IDAT", zlib.compress(bytes(rows))))
    chunks.append((b"IEND", b""))
    return _png_from_chunks(chunks, signature=PNG_SIGNATURE) + tail


def _solid(width: int, height: int, channels: int, color: Sequence[int]) -> bytes:
    """Repeat one pixel across a whole image.

    Args:
        width: Image width.
        height: Image height.
        channels: Bytes per pixel.
        color: Samples, at most ``channels`` long; missing ones read 0.

    Returns:
        Raw sample bytes.
    """
    padded = tuple(color[:channels]) + (0,) * max(0, channels - len(color))
    return bytes(bytes(padded) * (width * height))


# --------------------------------------------------------------------------
# findings and the memory model
# --------------------------------------------------------------------------


def test_finding_is_error_separates_errors_from_warnings() -> None:
    """Only the error severity blocks submission."""
    error = validate.Finding(validate.SEVERITY_ERROR, "code", "message", "path")
    warning = validate.Finding(validate.SEVERITY_WARNING, "code", "message", "path")
    assert error.is_error is True
    assert warning.is_error is False
    assert (error.severity, error.code, error.message, error.path) == (
        "error",
        "code",
        "message",
        "path",
    )


def test_memory_constants_match_the_published_model() -> None:
    """The numbers the module advertises are the numbers it scores with."""
    assert validate.BYTES_PER_PIXEL_RGBA == 4
    assert validate.BYTES_PER_PIXEL_RGB565 == 2
    assert validate.BYTES_PER_PIXEL_ALPHA_8 == 1
    assert validate.FULL_SCREEN_LAYER_BYTES == 7
    assert validate.AMBIENT_LAYER_COUNT == 3
    assert validate.AMBIENT_MEMORY_LIMIT_BYTES == 10 * 1024 * 1024
    assert validate.INTERACTIVE_MEMORY_LIMIT_BYTES == 100 * 1024 * 1024
    assert validate.HAND_LAYER_EDGE == 96
    assert validate.HAND_LAYER_COUNT == 3
    assert validate.ILLUMINATED_LIMIT == 0.15
    assert validate.MIN_DESIGN_EDGE_PX == 192
    assert validate.MAX_SHAPE_FILE_FACES == 10
    assert validate.MAX_XML_SOURCE_BYTES == 10 * 1024 * 1024
    assert validate.MIN_SCREENSHOT_EDGE_PX == 384
    assert validate.MAX_SCREENSHOT_EDGE_PX == 3840
    assert validate.PLAY_ICON_EDGE_PX == 512
    assert validate.PLAY_ICON_MAX_BYTES == 1024 * 1024
    assert validate.PLAY_FEATURE_GRAPHIC_SIZE == (1024, 500)
    assert validate.LISTING_TITLE_LIMIT == 30
    assert validate.LISTING_SHORT_LIMIT == 80
    assert validate.LISTING_FULL_LIMIT == 4000


def test_memory_estimate_charges_screen_slots_and_hands() -> None:
    """Each complication layer and the three hand layers are added on."""
    estimate = validate.memory_estimate(450, hands=True, slot_boxes=((78, 34), (78, 34)))
    assert estimate.design_edge == 450
    assert estimate.ambient_bytes == 3 * 4 * 450 * 450
    assert estimate.interactive_bytes == 7 * 450 * 450 + 2 * 4 * 78 * 34 + 3 * 4 * 96 * 96


def test_memory_estimate_without_hands_or_slots_charges_only_the_screen() -> None:
    """A bare digital face pays for the surface layers and nothing else."""
    estimate = validate.memory_estimate(192, hands=False, slot_boxes=())
    assert estimate.ambient_bytes == 3 * 4 * 192 * 192
    assert estimate.interactive_bytes == 7 * 192 * 192
    assert estimate.interactive_bytes < estimate.ambient_bytes


# --------------------------------------------------------------------------
# the hand-rolled PNG reader
# --------------------------------------------------------------------------


def test_decode_png_rejects_a_file_that_is_not_a_png(tmp_path: Path) -> None:
    """A missing signature is not a judgement about the image, it is no image."""
    path = _write(tmp_path, "banner.png", b"GIF89a" + bytes(64))
    assert validate.decode_png(path) is None


def test_decode_png_returns_none_without_a_header_chunk(tmp_path: Path) -> None:
    """A PNG with no ``IHDR`` says nothing about the image."""
    path = _write(tmp_path, "empty.png", _png_from_chunks([(b"IEND", b"")]))
    assert validate.decode_png(path) is None


def test_decode_png_reports_a_header_it_cannot_measure(tmp_path: Path) -> None:
    """An unsupported depth or colour type is reported rather than guessed at."""
    grey = _write(tmp_path, "grey.png", _png_image(2, 2, bytes(8), channels=2, color_type=0))
    shallow = _write(
        tmp_path, "shallow.png", _png_image(2, 2, bytes(12), channels=3, color_type=2, bit_depth=4)
    )
    grey_info = validate.decode_png(grey)
    shallow_info = validate.decode_png(shallow)
    assert grey_info is not None and shallow_info is not None
    assert (grey_info.width, grey_info.height, grey_info.bit_depth) == (2, 2, 8)
    assert (grey_info.color_type, grey_info.opaque, grey_info.illuminated_ratio) == (
        0,
        True,
        0.0,
    )
    assert (shallow_info.color_type, shallow_info.bit_depth) == (2, 4)
    assert (shallow_info.opaque, shallow_info.illuminated_ratio) == (True, 0.0)


def test_decode_png_notes_a_trns_chunk(tmp_path: Path) -> None:
    """A palette transparency block is a transparency declaration, opaque or not."""
    data = _png_image(
        2,
        2,
        _solid(2, 2, 3, LIT_PIXEL[:3]),
        channels=3,
        color_type=2,
        extra_chunks=[(b"tRNS", b"\x00\x00\x00")],
    )
    info = validate.decode_png(_write(tmp_path, "trns.png", data))
    assert info is not None
    assert (info.has_trns, info.opaque, info.color_type) == (True, True, 2)
    assert info.illuminated_ratio == pytest.approx(1.0)


def test_decode_png_returns_none_when_the_image_data_is_not_deflate(tmp_path: Path) -> None:
    """An IDAT payload that is not a zlib stream cannot be decoded."""
    chunks = [
        (b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 6, 0, 0, 0)),
        (b"IDAT", b"the quick brown fox"),
        (b"IEND", b""),
    ]
    info = validate.decode_png(_write(tmp_path, "broken.png", _png_from_chunks(chunks)))
    assert info is None


def test_decode_png_returns_none_when_the_scanlines_are_the_wrong_length(tmp_path: Path) -> None:
    """A stream that decodes to the wrong byte count is refused, not padded."""
    chunks = [
        (b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 6, 0, 0, 0)),
        (b"IDAT", zlib.compress(b"\x00" * 5)),
        (b"IEND", b""),
    ]
    info = validate.decode_png(_write(tmp_path, "short.png", _png_from_chunks(chunks)))
    assert info is None


def test_decode_png_rejects_an_unknown_filter_type(tmp_path: Path) -> None:
    """A filter byte outside 0 through 4 is refused rather than treated as none."""
    stride = 2 * 4
    raw = b"\x07" + CHECKER_PIXELS[:stride] + b"\x00" + CHECKER_PIXELS[stride:]
    chunks = [
        (b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 6, 0, 0, 0)),
        (b"IDAT", zlib.compress(raw)),
        (b"IEND", b""),
    ]
    assert validate.decode_png(_write(tmp_path, "filter.png", _png_from_chunks(chunks))) is None


def test_decode_png_ignores_a_truncated_chunk_after_the_image(tmp_path: Path) -> None:
    """A chunk cut off at the end of the file stops the walk without losing data."""
    data = _png_image(
        2,
        2,
        CHECKER_PIXELS,
        filters=(0, 1),
        tail=b"\x00\x00\x00\x08tEXtab",
    )
    info = validate.decode_png(_write(tmp_path, "tail.png", data))
    assert info is not None
    assert (info.width, info.height, info.opaque) == (2, 2, True)
    assert info.illuminated_ratio == pytest.approx(0.5)


@pytest.mark.parametrize("kind", [0, 1, 2, 3, 4])
def test_decode_png_recovers_every_scanline_filter(kind: int, tmp_path: Path) -> None:
    """Each of the five filters round-trips to the same measured pixels."""
    data = _png_image(2, 2, CHECKER_PIXELS, filters=(kind, kind))
    info = validate.decode_png(_write(tmp_path, f"filter-{kind}.png", data))
    assert info is not None
    assert (info.width, info.height, info.has_trns) == (2, 2, False)
    assert info.opaque is True
    assert info.illuminated_ratio == pytest.approx(0.5)


def test_decode_png_scores_a_fully_opaque_image_as_opaque(tmp_path: Path) -> None:
    """An RGB image has no alpha channel, so nothing can be transparent."""
    data = _png_image(3, 2, _solid(3, 2, 3, (0, 0, 0)), channels=3, color_type=2, filters=(1, 4))
    info = validate.decode_png(_write(tmp_path, "rgb.png", data))
    assert info is not None
    assert (info.color_type, info.opaque) == (2, True)
    assert info.illuminated_ratio == pytest.approx(0.0)


def test_decode_png_skips_transparent_pixels_when_it_scores_illumination(tmp_path: Path) -> None:
    """A bright pixel with no alpha lights nothing and breaks opacity."""
    pixels = bytearray(_solid(2, 2, 4, LIT_PIXEL))
    pixels[3] = TRANSPARENT_SAMPLE
    info = validate.decode_png(_write(tmp_path, "holes.png", _png_image(2, 2, bytes(pixels))))
    assert info is not None
    assert info.opaque is False
    assert info.illuminated_ratio == pytest.approx(0.75)


def test_decode_png_scores_an_empty_image_as_unlit(tmp_path: Path) -> None:
    """Zero width is measured as nothing lit instead of dividing by zero."""
    data = _png_image(0, 3, b"", filters=(0, 0, 0))
    info = validate.decode_png(_write(tmp_path, "empty.png", data))
    assert info is not None
    assert (info.width, info.height, info.bit_depth) == (0, 3, 8)
    assert (info.opaque, info.illuminated_ratio) == (True, 0.0)


def test_paeth_predictor_picks_the_closest_neighbour() -> None:
    """Each documented distance ordering selects its own neighbour."""
    assert validate._paeth(20, 21, 22) == 20
    assert validate._paeth(20, 23, 21) == 23
    assert validate._paeth(20, 22, 21) == 21
    assert validate._paeth(0, 0, 255) == 0
    assert validate._paeth(255, 0, 0) == 255


def test_all_opaque_and_argb_helpers_answer_for_their_inputs() -> None:
    """The two small predicates agree with the rules they document."""
    assert validate._all_opaque(bytes(_solid(2, 2, 3, (0, 0, 0))), 3) is True
    assert validate._all_opaque(bytes(_solid(2, 2, 4, LIT_PIXEL)), 4) is True
    assert validate._all_opaque(bytes(_solid(2, 2, 4, (255, 255, 255, 4))), 4) is False
    assert validate._is_argb_hex("#E0B155FF") is True
    assert validate._is_argb_hex("#e0b155ff") is True
    assert validate._is_argb_hex("#FFFFFF") is False
    assert validate._is_argb_hex("E0B155FF") is False
    assert validate._is_argb_hex("#E0B155FG") is False


# --------------------------------------------------------------------------
# tree-level rules
# --------------------------------------------------------------------------


def test_validate_project_passes_the_generated_tree_clean(tree: Path) -> None:
    """The control: a build off the generator reports nothing at all."""
    assert validate.validate_project(tree) == ()


def test_validate_project_rewrites_hand_written_markup_as_clean(tree: Path) -> None:
    """The templates the negative tests reuse are themselves compliant."""
    _write(tree, validate.WATCH_FACE_XML, _face_xml())
    _write(tree, validate.WATCH_FACE_INFO_XML, _info_document([PREVIEW_ELEMENT, CATEGORY_ELEMENT, EDITABLE_ELEMENT]))
    _write(tree, validate.ANDROID_MANIFEST_XML, _manifest_document(COMPLIANT_APPLICATION))
    assert validate.validate_project(tree) == ()


def test_validate_project_reports_a_missing_folder(tmp_path: Path) -> None:
    """A folder that is not there is one finding naming the folder."""
    missing = tmp_path / "never-built"
    findings = validate.validate_project(missing)
    assert _codes(findings) == ["project-missing"]
    assert findings[0].path == str(missing)
    assert findings[0].is_error is True


def test_validate_project_reports_every_required_file_that_is_absent(tree: Path) -> None:
    """The three required XML resources each report themselves."""
    for relative in (
        validate.WATCH_FACE_XML,
        validate.WATCH_FACE_INFO_XML,
        validate.ANDROID_MANIFEST_XML,
    ):
        _delete(tree, relative)
    findings = validate.validate_project(tree)
    assert _codes(findings) == ["file-missing"] * 3
    assert {finding.path for finding in findings} == {
        validate.WATCH_FACE_XML,
        validate.WATCH_FACE_INFO_XML,
        validate.ANDROID_MANIFEST_XML,
    }
    assert all(finding.is_error for finding in findings)


def test_validate_project_reports_markup_it_cannot_parse(tree: Path) -> None:
    """A truncated document is an error naming the file it choked on."""
    _write(tree, validate.WATCH_FACE_XML, "<WatchFace width='450'")
    _write(tree, validate.WATCH_FACE_INFO_XML, "<WatchFaceInfo><Preview")
    findings = validate.validate_project(tree)
    assert _codes(findings) == ["xml-unparsable"] * 2
    assert {finding.path for finding in findings} == {
        validate.WATCH_FACE_XML,
        validate.WATCH_FACE_INFO_XML,
    }


def test_validate_project_reports_a_missing_strings_file(tree: Path) -> None:
    """The editor labels the manifest references have to exist."""
    _delete(tree, validate.STRINGS_XML)
    assert [(finding.code, finding.path) for finding in validate.validate_project(tree)] == [
        ("file-missing", validate.STRINGS_XML)
    ]


def test_validate_project_reports_oversized_xml_source(tree: Path) -> None:
    """WO-G11 budgets the whole tree, so one huge resource tips it."""
    _write(tree, "res/values/bulk.xml", "<resources>" + "x" * BULK_XML_BYTES + "</resources>")
    findings = validate.validate_project(tree)
    assert _codes(findings) == ["xml-source-too-large"]
    assert findings[0].path == "."


def test_validate_project_reports_wear_logic_next_to_the_face(tree: Path) -> None:
    """Source or binary artefacts mean the bundle is no longer code-free."""
    _write(tree, "res/raw/Tracker.kt", "class Tracker")
    _write(tree, "jniLibs/arm64-v8a/libwear.so", bytes(16))
    findings = validate.validate_project(tree)
    assert _codes(findings) == ["wear-logic-present"] * 2
    assert {finding.path for finding in findings} == {
        "res/raw/Tracker.kt",
        "jniLibs/arm64-v8a/libwear.so",
    }


def test_validate_project_sorts_findings_by_path_then_code(tree: Path) -> None:
    """An operator reads the list top to bottom, so it arrives ordered."""
    _delete(tree, validate.PREVIEW_PNG)
    _write(tree, "res/raw/Tracker.kt", "class Tracker")
    _listing_json(tree, title="x" * (validate.LISTING_TITLE_LIMIT + 1))
    findings = validate.validate_project(tree)
    assert [(finding.path, finding.code) for finding in findings] == sorted(
        (finding.path, finding.code) for finding in findings
    )
    assert _codes(findings) == ["asset-missing", "listing-title-long", "wear-logic-present"]


# --------------------------------------------------------------------------
# the face document: vocabulary, scene, ambient, memory
# --------------------------------------------------------------------------


def test_validate_project_reports_a_missing_required_attribute(tree: Path) -> None:
    """A layer without its geometry is rejected before it reaches the device."""
    _write(
        tree,
        validate.WATCH_FACE_XML,
        _face_xml(
            '<PartDraw x="0" y="0" width="450">' + AMBIENT_VARIANT + "</PartDraw>"
        ),
    )
    findings = validate.validate_project(tree)
    assert _codes(findings) == ["attribute-missing"]
    assert findings[0].path == validate.WATCH_FACE_XML


def test_validate_project_reports_an_element_outside_the_vocabulary(tree: Path) -> None:
    """An invented element is the fastest way to fail the renderer."""
    _write(tree, validate.WATCH_FACE_XML, _face_xml(f"{DISC}<Hologram x=\"0\" />"))
    assert _codes(validate.validate_project(tree)) == ["element-unknown"]


def test_validate_project_reports_an_unknown_variant_mode(tree: Path) -> None:
    """Only the documented variant modes may be named."""
    _write(
        tree,
        validate.WATCH_FACE_XML,
        _face_xml(
            '<PartDraw x="0" y="0" width="450" height="450">'
            '<Ellipse x="3" y="3" width="444" height="444">'
            '<Stroke color="#FFFFFFFF" thickness="6" /></Ellipse>'
            + AMBIENT_VARIANT
            + '<Variant mode="DAY" target="alpha" value="128" />'
            "</PartDraw>"
        ),
    )
    assert _codes(validate.validate_project(tree)) == ["variant-mode-unknown"]


def test_validate_project_reports_a_face_without_a_scene(tree: Path) -> None:
    """A face with no scene has nothing to render, so nothing else is scored."""
    _write(tree, validate.WATCH_FACE_XML, _face_xml(scene_count=0))
    assert _codes(validate.validate_project(tree)) == ["scene-missing"]


def test_validate_project_reports_a_face_with_two_scenes(tree: Path) -> None:
    """Exactly one scene is allowed, and the first one still gets scored."""
    _write(tree, validate.WATCH_FACE_XML, _face_xml(scene_count=2))
    assert _codes(validate.validate_project(tree)) == ["scene-duplicate"]


def test_validate_project_warns_about_a_small_design_edge(tree: Path) -> None:
    """WO-V16 tests at 192 dp, so a smaller design is a warning."""
    _write(tree, validate.WATCH_FACE_XML, _face_xml(width="128", height="128"))
    findings = validate.validate_project(tree)
    assert _codes(findings) == ["design-edge-small"]
    assert findings[0].severity == validate.SEVERITY_WARNING
    assert findings[0].is_error is False


def test_validate_project_treats_a_malformed_edge_as_zero(tree: Path) -> None:
    """Unparseable geometry scores nothing instead of raising."""
    _write(tree, validate.WATCH_FACE_XML, _face_xml(width="wide", height="tall"))
    assert validate.validate_project(tree) == ()
    assert validate._int_or_zero("450") == 450
    assert validate._int_or_zero("wide") == 0
    assert validate._int_or_zero(None) == 0


def test_validate_project_warns_when_a_layer_has_no_ambient_variant(tree: Path) -> None:
    """A drop-able layer needs an ambient variant of its own or on an ancestor."""
    _write(
        tree,
        validate.WATCH_FACE_XML,
        _face_xml(
            '<PartDraw x="0" y="0" width="450" height="450">'
            '<Ellipse x="3" y="3" width="444" height="444">'
            '<Stroke color="#FFFFFFFF" thickness="6" /></Ellipse>'
            "</PartDraw>"
        ),
    )
    findings = validate.validate_project(tree)
    assert _codes(findings) == ["ambient-variant-missing"]
    assert findings[0].severity == validate.SEVERITY_WARNING


def test_validate_project_scores_the_ambient_and_interactive_ceilings(
    built: Path, tmp_path: Path
) -> None:
    """WO-P8 passes a normal face and reports either ceiling when it is broken."""
    ambient = _second_copy("ambient", built, tmp_path)
    _write(ambient, validate.WATCH_FACE_XML, _face_xml(width="1200", height="1200"))
    assert _codes(validate.validate_project(ambient)) == ["memory-ambient-over"]
    interactive = _second_copy("interactive", built, tmp_path)
    _write(
        interactive,
        validate.WATCH_FACE_XML,
        _face_xml(
            DISC + _slot_xml(width="6000", height="6000"),
            width="900",
            height="900",
        ),
    )
    assert _codes(validate.validate_project(interactive)) == ["memory-interactive-over"]


def test_validate_project_reports_a_color_configuration_outside_the_option_range(tree: Path) -> None:
    """A colourway list has to hold between one and one hundred options."""
    empty = '<ColorConfiguration defaultValue="0" displayName="@string/a" id="empty" />'
    crowded = (
        '<ColorConfiguration defaultValue="0" displayName="@string/b" id="crowded">'
        + "".join(
            f'<ColorOption colors="#FFFFFFFF" displayName="@string/opt{i}" id="{i}" />'
            for i in range(MAX_COLOR_OPTIONS + 1)
        )
        + "</ColorConfiguration>"
    )
    _write(
        tree,
        validate.WATCH_FACE_XML,
        _face_xml(configurations=f"{empty}{crowded}{COLOR_CONFIGURATION}"),
    )
    assert _codes(validate.validate_project(tree)) == ["color-option-count"] * 2


def test_validate_project_reports_a_color_option_that_is_not_argb_hex(tree: Path) -> None:
    """Colours are read as space-separated ARGB, and nothing else."""
    _write(
        tree,
        validate.WATCH_FACE_XML,
        _face_xml(
            configurations=(
                '<ColorConfiguration defaultValue="0" displayName="@string/a" id="bad">'
                '<ColorOption colors="#FFFFFF" displayName="@string/opt" id="0" />'
                "</ColorConfiguration>"
            )
        ),
    )
    findings = validate.validate_project(tree)
    assert _codes(findings) == ["color-option-format"]
    assert findings[0].path == validate.WATCH_FACE_XML


# --------------------------------------------------------------------------
# complication slots
# --------------------------------------------------------------------------


def test_validate_project_reports_too_many_complication_slots(tree: Path) -> None:
    """WO-P10 caps the slots, and the extra ones are counted."""
    body = DISC + "".join(_slot_xml(slot_id=str(index)) for index in range(1, MAX_COMPLICATION_SLOTS + 2))
    _write(tree, validate.WATCH_FACE_XML, _face_xml(body))
    assert _codes(validate.validate_project(tree)) == ["complication-slot-count"]


def test_validate_project_reports_an_unsupported_complication_type(tree: Path) -> None:
    """A slot may only declare the types the platform publishes."""
    _write(
        tree,
        validate.WATCH_FACE_XML,
        _face_xml(DISC + _slot_xml(supported="SUNRISE", complications=("SUNRISE",), provider=True)),
    )
    findings = validate.validate_project(tree)
    assert _codes(findings) == ["complication-type-unknown"]
    assert "SUNRISE" in findings[0].message


def test_validate_project_reports_a_slot_without_one_bounding_shape(tree: Path) -> None:
    """A slot declares exactly one bounding area, no more and no less."""
    body = DISC + _slot_xml(slot_id="1", bounds=()) + _slot_xml(
        slot_id="2",
        bounds=(
            '<BoundingOval x="0" y="0" width="78" height="34" />',
            '<BoundingBox x="0" y="0" width="78" height="34" />',
        ),
    )
    _write(tree, validate.WATCH_FACE_XML, _face_xml(body))
    assert _codes(validate.validate_project(tree)) == ["complication-bounding-shape"] * 2


def test_validate_project_reports_a_slot_missing_a_complication(tree: Path) -> None:
    """Every declared type needs a Complication to render it."""
    _write(tree, validate.WATCH_FACE_XML, _face_xml(DISC + _slot_xml(complications=())))
    findings = validate.validate_project(tree)
    assert _codes(findings) == ["complication-type-missing"]
    assert "EMPTY" in findings[0].message


def test_validate_project_reports_a_slot_without_a_default_provider(tree: Path) -> None:
    """A slot that never falls back to EMPTY must name a default provider."""
    _write(
        tree,
        validate.WATCH_FACE_XML,
        _face_xml(DISC + _slot_xml(supported="SHORT_TEXT", complications=("SHORT_TEXT",))),
    )
    assert _codes(validate.validate_project(tree)) == ["complication-provider-missing"]


# --------------------------------------------------------------------------
# watch_face_info.xml
# --------------------------------------------------------------------------


def test_validate_project_reports_a_missing_preview_and_category(tree: Path) -> None:
    """The preview is required and the category is expected."""
    _write(tree, validate.WATCH_FACE_INFO_XML, _info_document([EDITABLE_ELEMENT]))
    assert _codes(validate.validate_project(tree)) == ["category-missing", "preview-missing"]


def test_validate_project_reports_a_preview_without_a_value(tree: Path) -> None:
    """A preview that points at nothing cannot be listed."""
    _write(
        tree,
        validate.WATCH_FACE_INFO_XML,
        _info_document(["<Preview />", CATEGORY_ELEMENT, EDITABLE_ELEMENT]),
    )
    findings = validate.validate_project(tree)
    assert _codes(findings) == ["preview-value-missing"]
    assert findings[0].path == validate.WATCH_FACE_INFO_XML


def test_validate_project_reports_an_editable_flag_that_disagrees(tree: Path) -> None:
    """Editable must be true exactly when the face exposes configurations."""
    _write(tree, validate.WATCH_FACE_INFO_XML, _info_document([PREVIEW_ELEMENT, CATEGORY_ELEMENT]))
    assert _codes(validate.validate_project(tree)) == ["editable-mismatch"]
    assert validate._is_editable(_info_element(_info_document([PREVIEW_ELEMENT]))) is False


def test_validate_project_reads_an_android_namespaced_editable(tree: Path) -> None:
    """Either spelling of the value attribute counts as a declaration."""
    _write(
        tree,
        validate.WATCH_FACE_INFO_XML,
        _info_document(
            [
                PREVIEW_ELEMENT,
                CATEGORY_ELEMENT,
                f'<Editable android:value="true" xmlns:android="{validate.ANDROID_NAMESPACE}" />',
            ]
        ),
    )
    assert validate.validate_project(tree) == ()


# --------------------------------------------------------------------------
# watch_face_shapes.xml
# --------------------------------------------------------------------------


def test_validate_project_reports_too_many_shapes_file_entries(tree: Path) -> None:
    """WO-G10 allows ten face entries and the eleventh is reported."""
    entry = '<WatchFace file="@raw/watchface" height="300" shape="CIRCLE" width="300" />'
    shapes = (
        '<?xml version="1.0" encoding="utf-8"?>\n<WatchFaces>'
        + entry * (validate.MAX_SHAPE_FILE_FACES + 1)
        + "</WatchFaces>\n"
    )
    _write(tree, validate.WATCH_FACE_SHAPES_XML, shapes)
    assert _codes(validate.validate_project(tree)) == ["shapes-face-count"]
    _write(
        tree,
        validate.WATCH_FACE_SHAPES_XML,
        shapes.replace(entry * (validate.MAX_SHAPE_FILE_FACES + 1), entry * validate.MAX_SHAPE_FILE_FACES),
    )
    assert validate.validate_project(tree) == ()


# --------------------------------------------------------------------------
# AndroidManifest.xml
# --------------------------------------------------------------------------


def test_validate_project_reports_a_manifest_without_the_watch_feature(tree: Path) -> None:
    """A watch face package has to say it is for a watch."""
    _write(tree, validate.ANDROID_MANIFEST_XML, _manifest_document(COMPLIANT_APPLICATION, watch_feature=False))
    assert _codes(validate.validate_project(tree)) == ["watch-feature-missing"]


def test_validate_project_reports_a_manifest_without_an_application(tree: Path) -> None:
    """With no application element the remaining rules are skipped."""
    _write(tree, validate.ANDROID_MANIFEST_XML, _manifest_document([]))
    findings = validate.validate_project(tree)
    assert _codes(findings) == ["application-missing"]
    assert findings[0].path == validate.ANDROID_MANIFEST_XML


def test_validate_project_reports_an_application_that_carries_code(tree: Path) -> None:
    """A Watch Face Format bundle declares hasCode false or it is not one."""
    _write(
        tree,
        validate.ANDROID_MANIFEST_XML,
        _manifest_document(
            [
                '<application android:hasCode="true" android:label="@string/watch_face_name">',
                STANDALONE_ELEMENT,
                FORMAT_VERSION_ELEMENT,
                "</application>",
            ]
        ),
    )
    assert _codes(validate.validate_project(tree)) == ["has-code-true"]


def test_validate_project_reports_missing_standalone_and_version_metadata(tree: Path) -> None:
    """Both declarations are required and each reports on its own."""
    _write(
        tree,
        validate.ANDROID_MANIFEST_XML,
        _manifest_document([APPLICATION_ELEMENT, "</application>"]),
    )
    assert _codes(validate.validate_project(tree)) == [
        "format-version-missing",
        "standalone-missing",
    ]


def test_validate_project_reports_a_declared_component(tree: Path) -> None:
    """A code-free face may not declare an activity or a service."""
    _write(
        tree,
        validate.ANDROID_MANIFEST_XML,
        _manifest_document(
            [
                APPLICATION_ELEMENT,
                STANDALONE_ELEMENT,
                FORMAT_VERSION_ELEMENT,
                '<activity android:name=".FaceActivity" />',
                '<service android:name=".FaceService" />',
                "</application>",
            ]
        ),
    )
    assert _codes(validate.validate_project(tree)) == ["component-declared"] * 2


# --------------------------------------------------------------------------
# image assets
# --------------------------------------------------------------------------


def test_validate_project_reports_a_missing_preview(tree: Path) -> None:
    """The preview is the one image Play always lists."""
    _delete(tree, validate.PREVIEW_PNG)
    findings = validate.validate_project(tree)
    assert [(finding.code, finding.path) for finding in findings] == [
        ("asset-missing", validate.PREVIEW_PNG)
    ]


def test_validate_project_reports_a_missing_icon(tree: Path) -> None:
    """A missing icon is reported once, by the asset pass."""
    _delete(tree, validate.ICON_PNG)
    findings = validate.validate_project(tree)
    assert [(finding.code, finding.path) for finding in findings] == [
        ("asset-missing", validate.ICON_PNG)
    ]


def test_validate_project_reports_a_missing_feature_graphic(tree: Path) -> None:
    """The store banner is scored on its own and reported on its own."""
    _delete(tree, validate.FEATURE_GRAPHIC_PNG)
    findings = validate.validate_project(tree)
    assert [(finding.code, finding.path) for finding in findings] == [
        ("asset-missing", validate.FEATURE_GRAPHIC_PNG)
    ]


def test_validate_project_reports_an_asset_that_is_not_a_png(tree: Path) -> None:
    """A JPEG renamed to png is unreadable to this gate."""
    _write(tree, validate.PREVIEW_PNG, b"\xff\xd8\xff\xe0not a png")
    findings = validate.validate_project(tree)
    assert [(finding.code, finding.path) for finding in findings] == [
        ("asset-unreadable", validate.PREVIEW_PNG)
    ]


def test_validate_project_reports_an_asset_with_the_wrong_depth_or_type(tree: Path) -> None:
    """Only 8-bit RGB and RGBA are accepted, so greyscale is refused."""
    _write(
        tree,
        validate.PREVIEW_PNG,
        _png_image(384, 384, bytes(384 * 384), channels=1, color_type=0),
    )
    findings = validate.validate_project(tree)
    assert [(finding.code, finding.path) for finding in findings] == [
        ("asset-unreadable", validate.PREVIEW_PNG)
    ]
    assert "colour type 0" in findings[0].message


def test_validate_project_reports_an_asset_outside_the_shape_bounds(tree: Path) -> None:
    """One banner-shaped preview breaks the square, minimum, and maximum rules."""
    _write(tree, validate.PREVIEW_PNG, _png_image(4000, 1, _solid(4000, 1, 4, LIT_PIXEL)))
    findings = validate.validate_project(tree)
    assert _codes(findings) == ["asset-not-square", "asset-too-large", "asset-too-small"]
    assert {finding.path for finding in findings} == {validate.PREVIEW_PNG}


def test_validate_project_reports_a_transparent_screenshot(tree: Path) -> None:
    """Play wants the watch face only, so a screenshot carries no alpha."""
    shot = f"{validate.SCREENSHOT_DIR}/{BASELINE_SLUG}-theme-0.png"
    pixels = bytearray(_solid(384, 384, 4, LIT_PIXEL))
    pixels[3] = TRANSPARENT_SAMPLE
    _write(tree, shot, _png_image(384, 384, bytes(pixels)))
    findings = validate.validate_project(tree)
    assert [(finding.code, finding.path) for finding in findings] == [
        ("asset-transparent", shot)
    ]


def test_validate_project_reports_a_feature_graphic_of_the_wrong_size(tree: Path) -> None:
    """The store banner is 1024x500 or it is not the banner."""
    _write(
        tree,
        validate.FEATURE_GRAPHIC_PNG,
        _png_image(800, 400, _solid(800, 400, 3, LIT_PIXEL[:3]), channels=3, color_type=2),
    )
    findings = validate.validate_project(tree)
    assert [(finding.code, finding.path) for finding in findings] == [
        ("feature-graphic-size", validate.FEATURE_GRAPHIC_PNG)
    ]


def test_validate_project_reports_a_feature_graphic_with_alpha(
    built: Path, tmp_path: Path
) -> None:
    """An RGBA channel or a tRNS block both disqualify the banner."""
    rgba = _second_copy("rgba", built, tmp_path)
    _write(rgba, validate.FEATURE_GRAPHIC_PNG, _png_image(1024, 500, _solid(1024, 500, 4, LIT_PIXEL)))
    assert [(f.code, f.path) for f in validate.validate_project(rgba)] == [
        ("feature-graphic-alpha", validate.FEATURE_GRAPHIC_PNG)
    ]
    trns = _second_copy("trns", built, tmp_path)
    _write(
        trns,
        validate.FEATURE_GRAPHIC_PNG,
        _png_image(
            1024,
            500,
            _solid(1024, 500, 3, LIT_PIXEL[:3]),
            channels=3,
            color_type=2,
            extra_chunks=[(b"tRNS", b"\x00\x00\x00")],
        ),
    )
    assert _codes(validate.validate_project(trns)) == ["feature-graphic-alpha"]


def test_validate_project_reports_no_screenshots(tree: Path) -> None:
    """An empty screenshot folder is one finding naming the folder."""
    folder = tree / validate.SCREENSHOT_DIR
    for path in sorted(folder.glob("*.png")):
        path.unlink()
    findings = validate.validate_project(tree)
    assert [(finding.code, finding.path) for finding in findings] == [
        ("asset-missing", validate.SCREENSHOT_DIR)
    ]


def test_validate_project_warns_about_a_single_screenshot(tree: Path) -> None:
    """A customisable face should show more than one permutation."""
    folder = tree / validate.SCREENSHOT_DIR
    for path in sorted(folder.glob("*.png"))[1:]:
        path.unlink()
    findings = validate.validate_project(tree)
    assert [(finding.code, finding.path) for finding in findings] == [
        ("screenshot-permutations", validate.SCREENSHOT_DIR)
    ]
    assert findings[0].severity == validate.SEVERITY_WARNING


def test_validate_project_reports_an_icon_over_the_size_budget(tree: Path) -> None:
    """A 512 square icon past 1024 KB is refused on bytes alone."""
    edge = validate.PLAY_ICON_EDGE_PX
    _write(
        tree,
        validate.ICON_PNG,
        _png_image(
            edge,
            edge,
            _solid(edge, edge, 4, LIT_PIXEL),
            extra_chunks=[(b"prIv", bytes(validate.PLAY_ICON_MAX_BYTES))],
        ),
    )
    findings = validate.validate_project(tree)
    assert (tree / validate.ICON_PNG).stat().st_size > validate.PLAY_ICON_MAX_BYTES
    assert [(finding.code, finding.path) for finding in findings] == [
        ("icon-too-large", validate.ICON_PNG)
    ]


def test_validate_project_reports_an_icon_of_the_wrong_edge(tree: Path) -> None:
    """Play wants exactly 512 square, and 400 is legal nowhere else."""
    _write(tree, validate.ICON_PNG, _png_image(400, 400, _solid(400, 400, 4, LIT_PIXEL)))
    findings = validate.validate_project(tree)
    assert [(finding.code, finding.path) for finding in findings] == [
        ("icon-size", validate.ICON_PNG)
    ]


# --------------------------------------------------------------------------
# the Play listing package
# --------------------------------------------------------------------------


def test_validate_project_reports_both_missing_listing_documents(tree: Path) -> None:
    """The markdown listing and the README both have to ship."""
    _delete(tree, validate.STORE_LISTING_MD)
    _delete(tree, validate.README_MD)
    findings = validate.validate_project(tree)
    assert _codes(findings) == ["listing-file-missing"] * 2
    assert {finding.path for finding in findings} == {
        validate.STORE_LISTING_MD,
        validate.README_MD,
    }


def test_validate_project_reports_an_absent_manifest_json(tree: Path) -> None:
    """Without the generator's record there is no listing to score."""
    _delete(tree, validate.MANIFEST_JSON)
    findings = validate.validate_project(tree)
    assert [(finding.code, finding.path) for finding in findings] == [
        ("listing-file-missing", validate.MANIFEST_JSON)
    ]


def test_validate_project_reports_an_unparsable_manifest_json(tree: Path) -> None:
    """A half-written JSON record is an error, not a missing listing."""
    _write(tree, validate.MANIFEST_JSON, '{"listing": ')
    assert _codes(validate.validate_project(tree)) == ["json-unparsable"]


def test_validate_project_reports_a_manifest_json_of_the_wrong_shape(tree: Path) -> None:
    """The record has to be an object, not a list."""
    _write(tree, validate.MANIFEST_JSON, "[]")
    assert _codes(validate.validate_project(tree)) == ["json-shape"]


def test_validate_project_reports_a_manifest_without_a_listing_block(tree: Path) -> None:
    """An object with no listing text stops the pass after one finding."""
    _write(tree, validate.MANIFEST_JSON, '{"package": "com.example.face"}')
    findings = validate.validate_project(tree)
    assert [(finding.code, finding.path) for finding in findings] == [
        ("listing-missing", validate.MANIFEST_JSON)
    ]


def test_validate_project_reports_listing_text_over_budget(tree: Path) -> None:
    """Each of the three text fields reports its own overrun."""
    _listing_json(
        tree,
        title="Wear OS " + "x" * validate.LISTING_TITLE_LIMIT,
        short_description="Wear OS " + "y" * validate.LISTING_SHORT_LIMIT,
        full_description="Wear OS " + "z" * validate.LISTING_FULL_LIMIT,
    )
    assert _codes(validate.validate_project(tree)) == [
        "listing-full-long",
        "listing-short-long",
        "listing-title-long",
    ]


def test_validate_project_reports_a_listing_that_never_says_wear_os(tree: Path) -> None:
    """The wording rule is a hard requirement, not a style note."""
    _listing_json(
        tree,
        title="Meridian Analog",
        short_description="Analog face with two slots",
        full_description="An analog dial with two complication slots.",
    )
    assert _codes(validate.validate_project(tree)) == ["listing-wording-missing"]


def test_validate_project_reports_a_listing_without_its_declarations(tree: Path) -> None:
    """Data safety and the ads statement have to be filled in."""
    _listing_json(tree, data_safety=None, ads="")
    assert _codes(validate.validate_project(tree)) == [
        "listing-ads-missing",
        "listing-data-safety-missing",
    ]

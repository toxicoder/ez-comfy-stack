"""Pre-submission compliance gate for an emitted watch face project.

:func:`validate_project` walks a written project tree and returns
:class:`Finding` records instead of raising, so an operator sees every rule the
face breaks in one pass, before the bundle goes to Play. The rules are the
published Wear quality guidelines and Play listing requirements collected in
the research digest:

``WO-P8``
    Interactive and ambient memory ceilings, scored from the documented bitmap
    model (4 bytes per pixel RGBA_8888, 2 RGB_565, 1 ALPHA_8) with ambient
    assumed to hold three full-screen layers.
``WO-P7``
    An always-on face should keep the illuminated pixel fraction low; the
    digest quotes fifteen percent as the figure to stay under.
``WO-P10``
    Complication slots are capped.
``WO-G10`` / ``WO-G11``
    At most ten ``<WatchFace>`` entries in the shapes file, and XML source
    within ten megabytes.
``WO-V16``
    The design minimum is a 192 dp circle, tested at 192 dp and 227 dp round.

Play's own asset and text limits are checked here too: 512 square icon within
1024 KB, a 1024x500 feature graphic carrying no alpha, 1:1 screenshots of at
least 384 pixels with no device frame and no transparency, and listing text
inside 30, 80, and 4000 characters.

Hermetic at import: stdlib plus ``ez_common.json_value`` and the sibling
:mod:`ez_watch` modules.
"""

from __future__ import annotations

import json
import struct
import zlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from ez_common.json_value import Json, JsonList, JsonMap
from ez_watch.catalog import MAX_COLOR_OPTIONS, MAX_COMPLICATION_SLOTS
from ez_watch.scene import (
    COMPLICATION_TYPE_SET,
    ELEMENT_VOCABULARY,
    REQUIRED_ELEMENT_ATTRIBUTES,
    VARIANT_MODES,
)

SEVERITY_ERROR = "error"
"""A finding Play or the renderer rejects the face for."""

SEVERITY_WARNING = "warning"
"""A finding that costs a review round trip or polish points."""

ANDROID_NAMESPACE = "http://schemas.android.com/apk/res/android"
"""Namespace the manifest and the resource files qualify their attributes with."""

WATCH_FACE_XML = "res/raw/watchface.xml"
"""The one required raw resource: the whole face."""

WATCH_FACE_INFO_XML = "res/xml/watch_face_info.xml"
"""Play Store metadata for the face."""

WATCH_FACE_SHAPES_XML = "res/xml/watch_face_shapes.xml"
"""Optional size-variant file, capped at ten face entries."""

ANDROID_MANIFEST_XML = "AndroidManifest.xml"
"""The code-free package shell."""

STRINGS_XML = "res/values/strings.xml"
"""Editor labels referenced by the face."""

MANIFEST_JSON = "manifest.json"
"""The generator's own record of what it emitted, listing text included."""

STORE_LISTING_MD = "store-listing.md"
"""The Play listing package an operator pastes into Play Console."""

README_MD = "README.md"
"""Project instructions that ship with the emitted tree."""

PREVIEW_PNG = "res/drawable/preview.png"
"""The face preview Play lists."""

ICON_PNG = "store-assets/icon.png"
"""The 512 square launcher icon."""

FEATURE_GRAPHIC_PNG = "store-assets/feature-graphic.png"
"""The 1024x500 store banner."""

SCREENSHOT_DIR = "store-assets/screenshots"
"""Folder the 1:1 watch face screenshots are written into."""

BYTES_PER_PIXEL_RGBA = 4
"""RGBA_8888, the interactive surface format the memory model starts from."""

BYTES_PER_PIXEL_RGB565 = 2
"""RGB_565, the second buffer the model charges a face for."""

BYTES_PER_PIXEL_ALPHA_8 = 1
"""ALPHA_8, the alpha-only buffer the model charges a face for."""

FULL_SCREEN_LAYER_BYTES = (
    BYTES_PER_PIXEL_RGBA + BYTES_PER_PIXEL_RGB565 + BYTES_PER_PIXEL_ALPHA_8
)
"""Bytes the documented model charges for one full-screen layer set."""

AMBIENT_LAYER_COUNT = 3
"""Ambient is assumed to hold three full-screen layers."""

AMBIENT_MEMORY_LIMIT_BYTES = 10 * 1024 * 1024
"""WO-P8 ambient ceiling."""

INTERACTIVE_MEMORY_LIMIT_BYTES = 100 * 1024 * 1024
"""WO-P8 interactive ceiling."""

HAND_LAYER_EDGE = 96
"""Edge of the square layer each rendered hand is charged against."""

HAND_LAYER_COUNT = 3
"""Hour, minute, and second hands."""

ILLUMINATED_LIMIT = 0.15
"""WO-P7: share of pixels an always-on face should stay under.

This is a design budget, not a gate rule. A Watch Face Format face built here
is vector-only and dims through ``Variant`` alpha, so there is no ambient
bitmap for the gate to measure; :mod:`ez_watch.project` records the measured
share of the default preview beside this number in ``manifest.json`` for a
listing reviewer to read.
"""

MIN_DESIGN_EDGE_PX = 192
"""WO-V16 minimum design circle, in density-independent pixels."""

MAX_SHAPE_FILE_FACES = 10
"""WO-G10: ``<WatchFace>`` entries allowed in the shapes file."""

MAX_XML_SOURCE_BYTES = 10 * 1024 * 1024
"""WO-G11: XML source budget for the whole face."""

MIN_SCREENSHOT_EDGE_PX = 384
"""Smallest 1:1 watch face screenshot Play accepts."""

MAX_SCREENSHOT_EDGE_PX = 3840
"""Largest watch face screenshot dimension Play accepts."""

PLAY_ICON_EDGE_PX = 512
"""Launcher icon edge Play requires."""

PLAY_ICON_MAX_BYTES = 1024 * 1024
"""Launcher icon size budget."""

PLAY_FEATURE_GRAPHIC_SIZE: tuple[int, int] = (1024, 500)
"""Exact feature graphic Play expects, width then height."""

LISTING_TITLE_LIMIT = 30
"""Character budget for the Play listing title."""

LISTING_SHORT_LIMIT = 80
"""Character budget for the short description."""

LISTING_FULL_LIMIT = 4000
"""Character budget for the full description."""

WEAR_LOGIC_SUFFIXES: tuple[str, ...] = (".java", ".kt", ".jar", ".aar", ".dex", ".so")
"""Source or binary artefacts that mean the bundle carries Wear OS logic."""

_BOUNDING_SHAPES: frozenset[str] = frozenset(
    {"BoundingBox", "BoundingRoundBox", "BoundingOval", "BoundingRect", "BoundingArc"}
)
"""The one area element every ``ComplicationSlot`` must declare."""

_DRAWING_ELEMENTS: frozenset[str] = frozenset(
    {
        "AnalogClock",
        "ComplicationSlot",
        "DigitalClock",
        "Group",
        "PartAnimatedImage",
        "PartDraw",
        "PartImage",
        "PartText",
    }
)
"""Layers the ambient model can drop, so each needs an ambient ``Variant``."""

_HAND_TAGS: frozenset[str] = frozenset({"HourHand", "MinuteHand", "SecondHand"})
"""Elements whose presence means the face draws hands."""

_CONFIGURATION_TAGS: frozenset[str] = frozenset(
    {"BooleanConfiguration", "ColorConfiguration", "ListConfiguration", "PhotosConfiguration"}
)
"""``UserConfigurations`` children that make a face editable."""

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
"""First eight bytes of every PNG."""

_IHDR_BYTES = 13
"""Width, height, bit depth, colour type, compression, filter, interlace."""

_CHANNEL_COUNTS: Mapping[int, int] = {2: 3, 6: 4}
"""Colour types this gate decodes, mapped to their channel count."""

_COLOR_TYPE_RGB = 2
"""RGB with no alpha channel, the only type a feature graphic may use."""

_FILTER_NONE = 0
"""Filter type 0: the scanline is stored as written."""

_FILTER_SUB = 1
"""Filter type 1: differences from the pixel to the left."""

_FILTER_UP = 2
"""Filter type 2: differences from the pixel above."""

_FILTER_AVERAGE = 3
"""Filter type 3: differences from the mean of left and above."""

_FILTER_PAETH = 4
"""Filter type 4: differences from the Paeth predictor."""

_LUMA_SCALE = 1000
"""Denominator of the integer luma weights."""

_LUMA_THRESHOLD = 255 * 40
"""Brightness a pixel must reach to count as illuminated."""

_ALPHA_THRESHOLD = 8
"""Alpha below this counts as transparent, matching :mod:`ez_raster`."""


@dataclass(frozen=True)
class Finding:
    """One rule the emitted project breaks.

    Attributes:
        severity: ``error`` or ``warning``.
        code: Stable rule identifier an operator can look up.
        message: What is wrong, in one sentence.
        path: Project-relative file the finding points at, or the folder when
            the finding is about the tree as a whole.
    """

    severity: str
    code: str
    message: str
    path: str

    @property
    def is_error(self) -> bool:
        """Whether this finding blocks submission.

        Returns:
            True for an error severity.
        """
        return self.severity == SEVERITY_ERROR


@dataclass(frozen=True)
class MemoryEstimate:
    """Estimated memory a face costs the renderer.

    Attributes:
        design_edge: Square design edge the estimate was scored at.
        ambient_bytes: Ambient footprint, three full-screen layers.
        interactive_bytes: Interactive footprint, surface plus element layers.
    """

    design_edge: int
    ambient_bytes: int
    interactive_bytes: int


@dataclass(frozen=True)
class PngInfo:
    """What the gate learned from a PNG without any third-party decoder.

    Attributes:
        width: Width in pixels.
        height: Height in pixels.
        bit_depth: Bits per channel from the header.
        color_type: PNG colour type from the header.
        has_trns: Whether a ``tRNS`` chunk is present.
        opaque: Whether every decoded pixel is fully opaque.
        illuminated_ratio: Share of pixels bright enough to count as lit.
    """

    width: int
    height: int
    bit_depth: int
    color_type: int
    has_trns: bool
    opaque: bool
    illuminated_ratio: float


def memory_estimate(
    design_edge: int,
    *,
    hands: bool,
    slot_boxes: Sequence[tuple[int, int]],
) -> MemoryEstimate:
    """Score a face against the documented Wear memory model.

    Args:
        design_edge: Square design edge of the face, in pixels.
        hands: Whether the face draws hour, minute, and second hands.
        slot_boxes: Width and height of every complication slot layer.

    Returns:
        The ambient and interactive footprints, in bytes.
    """
    pixels = design_edge * design_edge
    interactive = FULL_SCREEN_LAYER_BYTES * pixels
    for width, height in slot_boxes:
        interactive += BYTES_PER_PIXEL_RGBA * width * height
    if hands:
        interactive += (
            BYTES_PER_PIXEL_RGBA * HAND_LAYER_EDGE * HAND_LAYER_EDGE * HAND_LAYER_COUNT
        )
    ambient = AMBIENT_LAYER_COUNT * BYTES_PER_PIXEL_RGBA * pixels
    return MemoryEstimate(design_edge=design_edge, ambient_bytes=ambient, interactive_bytes=interactive)


def decode_png(path: Path) -> PngInfo | None:
    """Read a PNG well enough to judge Play's asset rules.

    Supports the 8-bit greyscale-free types a screenshot or icon is written as:
    colour type 2 (RGB) and 6 (RGBA), non-interlaced, with any of the five
    scanline filters.

    Args:
        path: File to read.

    Returns:
        The header plus the opacity and illumination measurements, or None when
        the file is not a PNG this gate can read.
    """
    header = _png_chunks(path.read_bytes())
    if header is None:
        return None
    width, height, bit_depth, color_type, has_trns, idat = header
    channels = _CHANNEL_COUNTS.get(color_type, 0)
    if bit_depth != 8 or channels == 0:
        return PngInfo(width, height, bit_depth, color_type, has_trns, True, 0.0)
    pixels = _unfilter(idat, width, height, channels)
    if pixels is None:
        return None
    return PngInfo(
        width=width,
        height=height,
        bit_depth=bit_depth,
        color_type=color_type,
        has_trns=has_trns,
        opaque=_all_opaque(pixels, channels),
        illuminated_ratio=_illuminated_ratio(pixels, width, height, channels),
    )


def validate_project(root: Path) -> tuple[Finding, ...]:
    """Run every published Wear and Play rule over one emitted project.

    Args:
        root: Folder that holds ``AndroidManifest.xml`` and ``res/``.

    Returns:
        Findings sorted by path then code, empty when the face is clean.
    """
    root = Path(root)
    if not root.is_dir():
        return (Finding(SEVERITY_ERROR, "project-missing", "project folder not found", str(root)),)
    findings: list[Finding] = []
    face = _parse(root, WATCH_FACE_XML, findings)
    info = _parse(root, WATCH_FACE_INFO_XML, findings)
    shapes = _parse(root, WATCH_FACE_SHAPES_XML, findings, optional=True)
    application = _parse(root, ANDROID_MANIFEST_XML, findings)
    _check_strings(root, findings)
    if face is not None:
        _check_face(root, face, findings)
    if info is not None:
        _check_info(root, face, info, findings)
    if shapes is not None:
        _check_shapes(root, shapes, findings)
    if application is not None:
        _check_manifest(root, application, findings)
    _check_source_size(root, findings)
    _check_wear_logic(root, application, findings)
    _check_assets(root, face, info, findings)
    _check_listing(root, info, findings)
    return tuple(sorted(findings, key=lambda item: (item.path, item.code, item.message)))


def _parse(root: Path, relative: str, findings: list[Finding], *, optional: bool = False) -> ElementTree.Element | None:
    """Parse one XML resource, recording what went wrong.

    Args:
        root: Project folder.
        relative: Project-relative path to parse.
        findings: Findings to append to.
        optional: When True, a missing file is fine.

    Returns:
        The root element, or None when the file is absent or does not parse.
    """
    path = root / relative
    if not path.is_file():
        if not optional:
            findings.append(Finding(SEVERITY_ERROR, "file-missing", f"required file {relative} is absent", relative))
        return None
    try:
        return ElementTree.fromstring(path.read_text(encoding="utf-8"))
    except ElementTree.ParseError as error:
        findings.append(Finding(SEVERITY_ERROR, "xml-unparsable", f"{relative} does not parse: {error}", relative))
        return None


def _tag_of(element: ElementTree.Element) -> str:
    """Element name with any namespace stripped.

    Args:
        element: Element to name.

    Returns:
        The local name.
    """
    return element.tag.rsplit("}", 1)[-1]


def _android(element: ElementTree.Element, name: str) -> str | None:
    """Read an ``android:`` namespaced attribute.

    Args:
        element: Element to read.
        name: Attribute name without the prefix.

    Returns:
        The value, or None when absent.
    """
    return element.get(f"{{{ANDROID_NAMESPACE}}}{name}")


def _check_face(root: Path, face: ElementTree.Element, findings: list[Finding]) -> None:
    """Apply the element vocabulary, scene, ambient, and memory rules.

    Args:
        root: Project folder, for the path a finding reports.
        face: ``<WatchFace>`` root element.
        findings: Findings to append to.
    """
    for element in face.iter():
        name = _tag_of(element)
        if name in ELEMENT_VOCABULARY:
            for required in REQUIRED_ELEMENT_ATTRIBUTES.get(name, ()):
                if element.get(required) is None:
                    findings.append(
                        Finding(SEVERITY_ERROR, "attribute-missing", f"<{name}> is missing {required}", WATCH_FACE_XML)
                    )
        else:
            findings.append(Finding(SEVERITY_ERROR, "element-unknown", f"<{name}> is outside the documented Watch Face Format vocabulary", WATCH_FACE_XML))
        if name == "Variant" and element.get("mode") not in VARIANT_MODES:
            findings.append(Finding(SEVERITY_ERROR, "variant-mode-unknown", f'Variant mode "{element.get("mode")}" is not one of the documented values', WATCH_FACE_XML))
    scenes = [child for child in face if _tag_of(child) == "Scene"]
    if not scenes:
        findings.append(Finding(SEVERITY_ERROR, "scene-missing", "the face declares no <Scene>", WATCH_FACE_XML))
        return
    if len(scenes) > 1:
        findings.append(Finding(SEVERITY_ERROR, "scene-duplicate", f"the face declares {len(scenes)} <Scene> elements; exactly one is allowed", WATCH_FACE_XML))
    scene = scenes[0]
    _check_design_edge(face, findings)
    _check_ambient(scene, findings)
    _check_configurations(face, info=None, findings=findings)
    _check_complications(scene, findings)
    _check_memory(face, scene, findings)


def _check_design_edge(face: ElementTree.Element, findings: list[Finding]) -> None:
    """Warn when the design edge is below the 192 dp minimum.

    Args:
        face: ``<WatchFace>`` root element.
        findings: Findings to append to.
    """
    width = _int_or_zero(face.get("width"))
    height = _int_or_zero(face.get("height"))
    if width and min(width, height) < MIN_DESIGN_EDGE_PX:
        findings.append(
            Finding(
                SEVERITY_WARNING,
                "design-edge-small",
                f"design edge {min(width, height)} px is below the {MIN_DESIGN_EDGE_PX} dp minimum",
                WATCH_FACE_XML,
            )
        )


def _int_or_zero(value: str | None) -> int:
    """Parse an attribute as an integer.

    Args:
        value: Attribute text or None.

    Returns:
        The integer, or 0 when absent or malformed.
    """
    try:
        return int(str(value))
    except ValueError:
        return 0


def _check_ambient(scene: ElementTree.Element, findings: list[Finding]) -> None:
    """Require an ambient variant on every layer the ambient model may drop.

    Args:
        scene: The single ``<Scene>``.
        findings: Findings to append to.
    """
    _walk_ambient(scene, [], findings)


def _walk_ambient(
    element: ElementTree.Element,
    ancestors: list[ElementTree.Element],
    findings: list[Finding],
) -> None:
    """Visit one element and its subtree looking for ambient variants.

    Args:
        element: Element being visited.
        ancestors: Elements above it, outermost first.
        findings: Findings to append to.
    """
    name = _tag_of(element)
    if name in _DRAWING_ELEMENTS and not _has_ambient_variant(element) and not any(
        _has_ambient_variant(ancestor) for ancestor in ancestors
    ):
        findings.append(
            Finding(
                SEVERITY_WARNING,
                "ambient-variant-missing",
                f"<{name}> has no ambient Variant of its own or on an ancestor",
                WATCH_FACE_XML,
            )
        )
    ancestors.append(element)
    for child in list(element):
        _walk_ambient(child, ancestors, findings)
    ancestors.pop()


def _has_ambient_variant(element: ElementTree.Element) -> bool:
    """Whether an element carries the ambient variant directly.

    Args:
        element: Element to inspect.

    Returns:
        True when a child ``Variant`` is in ambient mode.
    """
    return any(
        _tag_of(child) == "Variant" and child.get("mode") in VARIANT_MODES for child in element
    )


def _check_configurations(
    face: ElementTree.Element,
    *,
    info: ElementTree.Element | None,
    findings: list[Finding],
) -> None:
    """Score every ``ColorConfiguration`` against the one-to-hundred option rule.

    Args:
        face: ``<WatchFace>`` root element.
        info: ``<WatchFaceInfo>`` root when it is already parsed.
        findings: Findings to append to.
    """
    for configuration in face.iter():
        if _tag_of(configuration) != "ColorConfiguration":
            continue
        options = [child for child in configuration if _tag_of(child) == "ColorOption"]
        if not 1 <= len(options) <= MAX_COLOR_OPTIONS:
            findings.append(
                Finding(
                    SEVERITY_ERROR,
                    "color-option-count",
                    f"ColorConfiguration {configuration.get('id') or ''} declares {len(options)} "
                    f"ColorOption entries; between 1 and {MAX_COLOR_OPTIONS} are allowed",
                    WATCH_FACE_XML,
                )
            )
        for option in options:
            colors = (option.get("colors") or "").split()
            if not colors or any(not _is_argb_hex(color) for color in colors):
                findings.append(
                    Finding(
                        SEVERITY_ERROR,
                        "color-option-format",
                        f"ColorOption {option.get('id') or ''} must list space-separated ARGB hex colors",
                        WATCH_FACE_XML,
                    )
                )


def _is_argb_hex(value: str) -> bool:
    """Whether a colour is written as ARGB hex.

    Args:
        value: Candidate colour.

    Returns:
        True when it is ``#`` plus eight hex digits.
    """
    if len(value) != 9 or not value.startswith("#"):
        return False
    return all(character in "0123456789abcdefABCDEF" for character in value[1:])


def _check_complications(scene: ElementTree.Element, findings: list[Finding]) -> None:
    """Score every ``ComplicationSlot`` against the documented requirements.

    Args:
        scene: The single ``<Scene>``.
        findings: Findings to append to.
    """
    slots = [element for element in scene.iter() if _tag_of(element) == "ComplicationSlot"]
    if len(slots) > MAX_COMPLICATION_SLOTS:
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "complication-slot-count",
                f"{len(slots)} complication slots; WO-P10 allows at most {MAX_COMPLICATION_SLOTS}",
                WATCH_FACE_XML,
            )
        )
    for slot in slots:
        _check_slot(slot, findings)


def _check_slot(slot: ElementTree.Element, findings: list[Finding]) -> None:
    """Score one complication slot.

    Args:
        slot: The ``ComplicationSlot`` element.
        findings: Findings to append to.
    """
    declared = (slot.get("supportedTypes") or "").split()
    unknown = sorted(set(declared) - set(COMPLICATION_TYPE_SET))
    if unknown:
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "complication-type-unknown",
                f"slot {slot.get('slotId') or ''} declares unsupported types: {', '.join(unknown)}",
                WATCH_FACE_XML,
            )
        )
    shapes = [child for child in slot if _tag_of(child) in _BOUNDING_SHAPES]
    if len(shapes) != 1:
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "complication-bounding-shape",
                f"slot {slot.get('slotId') or ''} declares {len(shapes)} bounding shapes; exactly one is required",
                WATCH_FACE_XML,
            )
        )
    covered = {_tag_of(child) and child.get("type") for child in slot if _tag_of(child) == "Complication"}
    missing = sorted(set(declared) - covered - {None})
    if missing:
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "complication-type-missing",
                f"slot {slot.get('slotId') or ''} has no Complication for: {', '.join(missing)}",
                WATCH_FACE_XML,
            )
        )
    if declared and "EMPTY" not in declared and not any(
        _tag_of(child) == "DefaultProviderPolicy" for child in slot
    ):
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "complication-provider-missing",
                f"slot {slot.get('slotId') or ''} declares no DefaultProviderPolicy",
                WATCH_FACE_XML,
            )
        )


def _check_memory(face: ElementTree.Element, scene: ElementTree.Element, findings: list[Finding]) -> None:
    """Score the face against the WO-P8 ceilings and the WO-P7 pixel cap.

    Args:
        face: ``<WatchFace>`` root element.
        scene: The single ``<Scene>``.
        findings: Findings to append to.
    """
    edge = _int_or_zero(face.get("width"))
    if edge <= 0:
        return
    boxes = tuple(
        (_int_or_zero(slot.get("width")), _int_or_zero(slot.get("height")))
        for slot in scene.iter()
        if _tag_of(slot) == "ComplicationSlot"
    )
    estimate = memory_estimate(edge, hands=_draws_hands(scene), slot_boxes=boxes)
    if estimate.ambient_bytes > AMBIENT_MEMORY_LIMIT_BYTES:
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "memory-ambient-over",
                f"ambient estimate {estimate.ambient_bytes} bytes exceeds the WO-P8 limit "
                f"of {AMBIENT_MEMORY_LIMIT_BYTES} bytes",
                WATCH_FACE_XML,
            )
        )
    if estimate.interactive_bytes > INTERACTIVE_MEMORY_LIMIT_BYTES:
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "memory-interactive-over",
                f"interactive estimate {estimate.interactive_bytes} bytes exceeds the WO-P8 limit "
                f"of {INTERACTIVE_MEMORY_LIMIT_BYTES} bytes",
                WATCH_FACE_XML,
            )
        )


def _draws_hands(scene: ElementTree.Element) -> bool:
    """Whether the face draws clock hands.

    Args:
        scene: The single ``<Scene>``.

    Returns:
        True when any hand element is present.
    """
    return any(_tag_of(element) in _HAND_TAGS for element in scene.iter())


def _check_info(
    root: Path,
    face: ElementTree.Element | None,
    info: ElementTree.Element,
    findings: list[Finding],
) -> None:
    """Score ``watch_face_info.xml``, including the Editable consistency.

    Args:
        root: Project folder, for the path a finding reports.
        face: Parsed face root, or None when it failed to parse.
        info: ``<WatchFaceInfo>`` root element.
        findings: Findings to append to.
    """
    names = [_tag_of(child) for child in info]
    if "Preview" not in names:
        findings.append(Finding(SEVERITY_ERROR, "preview-missing", "watch_face_info.xml declares no Preview", WATCH_FACE_INFO_XML))
    if "Category" not in names:
        findings.append(Finding(SEVERITY_WARNING, "category-missing", "watch_face_info.xml declares no Category", WATCH_FACE_INFO_XML))
    for required in ("Preview",):
        if required in names and any(
            _tag_of(child) == required and _android(child, "value") is None and child.get("value") is None
            for child in info
        ):
            findings.append(Finding(SEVERITY_ERROR, "preview-value-missing", f"{required} has no value attribute", WATCH_FACE_INFO_XML))
    if face is not None and _is_editable(info) != _is_configurable(face):
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "editable-mismatch",
                "Editable must be true exactly when the face exposes user configurations",
                WATCH_FACE_INFO_XML,
            )
        )


def _is_editable(info: ElementTree.Element) -> bool:
    """Whether the face tells Play it is editable.

    Args:
        info: ``<WatchFaceInfo>`` root element.

    Returns:
        True when an ``Editable`` child says true.
    """
    for child in info:
        if _tag_of(child) == "Editable":
            return (child.get("value") or _android(child, "value") or "").lower() == "true"
    return False


def _is_configurable(face: ElementTree.Element) -> bool:
    """Whether the face exposes any user configuration.

    Args:
        face: ``<WatchFace>`` root element.

    Returns:
        True when a configuration element is present.
    """
    return any(_tag_of(element) in _CONFIGURATION_TAGS for element in face.iter())


def _check_shapes(root: Path, shapes: ElementTree.Element, findings: list[Finding]) -> None:
    """Score the optional shapes file against WO-G10.

    Args:
        root: Project folder, for the path a finding reports.
        shapes: Shapes file root element.
        findings: Findings to append to.
    """
    entries = [element for element in shapes.iter() if _tag_of(element) == "WatchFace"]
    if len(entries) > MAX_SHAPE_FILE_FACES:
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "shapes-face-count",
                f"the shapes file declares {len(entries)} <WatchFace> entries; WO-G10 allows "
                f"at most {MAX_SHAPE_FILE_FACES}",
                WATCH_FACE_SHAPES_XML,
            )
        )


def _check_manifest(root: Path, application_manifest: ElementTree.Element, findings: list[Finding]) -> None:
    """Score ``AndroidManifest.xml`` for the code-free package shape.

    Args:
        root: Project folder, for the path a finding reports.
        application_manifest: ``<manifest>`` root element.
        findings: Findings to append to.
    """
    features = [
        element
        for element in application_manifest.iter()
        if _tag_of(element) == "uses-feature" and _android(element, "name") == "android.hardware.type.watch"
    ]
    if not features:
        findings.append(Finding(SEVERITY_ERROR, "watch-feature-missing", "AndroidManifest.xml declares no watch uses-feature", ANDROID_MANIFEST_XML))
    application = next((element for element in application_manifest.iter() if _tag_of(element) == "application"), None)
    if application is None:
        findings.append(Finding(SEVERITY_ERROR, "application-missing", "AndroidManifest.xml declares no application", ANDROID_MANIFEST_XML))
        return
    if (_android(application, "hasCode") or "").lower() != "false":
        findings.append(Finding(SEVERITY_ERROR, "has-code-true", "application must carry hasCode=false for a Watch Face Format face", ANDROID_MANIFEST_XML))
    names = {
        _android(element, "name")
        for element in application
        if _tag_of(element) in {"meta-data", "property"}
    }
    if "com.google.android.wearable.standalone" not in names:
        findings.append(Finding(SEVERITY_ERROR, "standalone-missing", "application declares no standalone meta-data", ANDROID_MANIFEST_XML))
    if "com.google.wear.watchface.format.version" not in names:
        findings.append(Finding(SEVERITY_ERROR, "format-version-missing", "application declares no Watch Face Format version property", ANDROID_MANIFEST_XML))
    for element in application:
        if _tag_of(element) in {"activity", "service", "receiver", "provider"}:
            findings.append(
                Finding(
                    SEVERITY_ERROR,
                    "component-declared",
                    f"a code-free face may not declare a {_tag_of(element)}",
                    ANDROID_MANIFEST_XML,
                )
            )


def _check_strings(root: Path, findings: list[Finding]) -> None:
    """Require the string resources the manifest and the editor reference.

    Args:
        root: Project folder.
        findings: Findings to append to.
    """
    path = root / STRINGS_XML
    if not path.is_file():
        findings.append(Finding(SEVERITY_ERROR, "file-missing", f"required file {STRINGS_XML} is absent", STRINGS_XML))


def _check_source_size(root: Path, findings: list[Finding]) -> None:
    """Enforce the WO-G11 XML source budget across the whole tree.

    Args:
        root: Project folder.
        findings: Findings to append to.
    """
    total = sum(path.stat().st_size for path in sorted(root.rglob("*.xml")) if path.is_file())
    if total > MAX_XML_SOURCE_BYTES:
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "xml-source-too-large",
                f"XML source is {total} bytes; WO-G11 allows at most {MAX_XML_SOURCE_BYTES}",
                ".",
            )
        )


def _check_wear_logic(
    root: Path,
    application_manifest: ElementTree.Element | None,
    findings: list[Finding],
) -> None:
    """Fail the bundle when it carries Wear OS logic next to the face.

    Args:
        root: Project folder.
        application_manifest: Parsed manifest, or None when unavailable.
        findings: Findings to append to.
    """
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in WEAR_LOGIC_SUFFIXES:
            findings.append(
                Finding(
                    SEVERITY_ERROR,
                    "wear-logic-present",
                    "a watch face bundle must stay separate from any bundle carrying Wear OS logic",
                    str(path.relative_to(root)),
                )
            )


def _check_assets(
    root: Path,
    face: ElementTree.Element | None,
    info: ElementTree.Element | None,
    findings: list[Finding],
) -> None:
    """Score every generated image against Play's asset rules.

    Args:
        root: Project folder.
        face: Parsed face root, or None when it failed to parse.
        info: Parsed face-info root, or None when it failed to parse.
        findings: Findings to append to.
    """
    _check_one_asset(root, PREVIEW_PNG, findings, square=True, opaque=True)
    _check_one_asset(root, ICON_PNG, findings, square=True, opaque=False)
    _check_feature_graphic(root, findings)
    _check_screenshots(root, info, findings)


def _check_one_asset(
    root: Path,
    relative: str,
    findings: list[Finding],
    *,
    square: bool,
    opaque: bool,
) -> None:
    """Score one image asset.

    Args:
        root: Project folder.
        relative: Project-relative path of the image.
        findings: Findings to append to.
        square: Whether the image has to be 1:1.
        opaque: Whether transparency is forbidden.
    """
    info = _asset_info(root, relative, findings)
    if info is None:
        return
    if square and info.width != info.height:
        findings.append(Finding(SEVERITY_ERROR, "asset-not-square", f"{relative} is {info.width}x{info.height}; a 1:1 image is required", relative))
    if min(info.width, info.height) < MIN_SCREENSHOT_EDGE_PX:
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "asset-too-small",
                f"{relative} is {min(info.width, info.height)} px on the short edge; {MIN_SCREENSHOT_EDGE_PX} is the minimum",
                relative,
            )
        )
    if max(info.width, info.height) > MAX_SCREENSHOT_EDGE_PX:
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "asset-too-large",
                f"{relative} is {max(info.width, info.height)} px; {MAX_SCREENSHOT_EDGE_PX} is the maximum",
                relative,
            )
        )
    if opaque and not info.opaque:
        findings.append(Finding(SEVERITY_ERROR, "asset-transparent", f"{relative} carries transparency; screenshots may not", relative))


def _asset_info(root: Path, relative: str, findings: list[Finding]) -> PngInfo | None:
    """Decode one image asset, reporting what stopped it.

    Args:
        root: Project folder.
        relative: Project-relative path.
        findings: Findings to append to.

    Returns:
        The decoded image, or None when it is missing or unreadable.
    """
    path = root / relative
    if not path.is_file():
        findings.append(Finding(SEVERITY_ERROR, "asset-missing", f"{relative} is absent", relative))
        return None
    info = decode_png(path)
    if info is None:
        findings.append(Finding(SEVERITY_ERROR, "asset-unreadable", f"{relative} is not a PNG this gate can read", relative))
        return None
    if info.bit_depth != 8 or info.color_type not in _CHANNEL_COUNTS:
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "asset-unreadable",
                f"{relative} uses bit depth {info.bit_depth} and colour type {info.color_type}; 8-bit RGB or RGBA is required",
                relative,
            )
        )
        return None
    return info


def _check_feature_graphic(root: Path, findings: list[Finding]) -> None:
    """Score the store banner: exact size and no alpha anywhere.

    Args:
        root: Project folder.
        findings: Findings to append to.
    """
    info = _asset_info(root, FEATURE_GRAPHIC_PNG, findings)
    if info is None:
        return
    if (info.width, info.height) != PLAY_FEATURE_GRAPHIC_SIZE:
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "feature-graphic-size",
                f"feature graphic is {info.width}x{info.height}; {PLAY_FEATURE_GRAPHIC_SIZE[0]}x{PLAY_FEATURE_GRAPHIC_SIZE[1]} is required",
                FEATURE_GRAPHIC_PNG,
            )
        )
    if info.color_type != _COLOR_TYPE_RGB or info.has_trns or not info.opaque:
        findings.append(Finding(SEVERITY_ERROR, "feature-graphic-alpha", "feature graphic must be written without an alpha channel", FEATURE_GRAPHIC_PNG))


def _check_screenshots(root: Path, info: ElementTree.Element | None, findings: list[Finding]) -> None:
    """Score every 1:1 screenshot and require the customisable permutations.

    Args:
        root: Project folder.
        info: Parsed face-info root, or None when it failed to parse.
        findings: Findings to append to.
    """
    folder = root / SCREENSHOT_DIR
    shots = sorted(path for path in folder.glob("*.png") if path.is_file()) if folder.is_dir() else []
    if not shots:
        findings.append(Finding(SEVERITY_ERROR, "asset-missing", f"no screenshots found in {SCREENSHOT_DIR}", SCREENSHOT_DIR))
        return
    if info is not None and _is_editable(info) and len(shots) < 2:
        findings.append(
            Finding(
                SEVERITY_WARNING,
                "screenshot-permutations",
                "a customisable face should ship more than one screenshot permutation",
                SCREENSHOT_DIR,
            )
        )
    for path in shots:
        _check_one_asset(root, str(path.relative_to(root)), findings, square=True, opaque=True)


def _check_icon_size(root: Path, findings: list[Finding]) -> None:
    """Score the launcher icon against Play's 512 square and 1024 KB limits.

    Args:
        root: Project folder.
        findings: Findings to append to.
    """
    path = root / ICON_PNG
    if not path.is_file():
        return
    size = path.stat().st_size
    if size > PLAY_ICON_MAX_BYTES:
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "icon-too-large",
                f"icon is {size} bytes; {PLAY_ICON_MAX_BYTES} is the maximum",
                ICON_PNG,
            )
        )
    info = decode_png(path)
    if info is not None and (info.width, info.height) != (PLAY_ICON_EDGE_PX, PLAY_ICON_EDGE_PX):
        findings.append(
            Finding(
                SEVERITY_ERROR,
                "icon-size",
                f"icon is {info.width}x{info.height}; {PLAY_ICON_EDGE_PX}x{PLAY_ICON_EDGE_PX} is required",
                ICON_PNG,
            )
        )


def _check_listing(root: Path, info: ElementTree.Element | None, findings: list[Finding]) -> None:
    """Score the Play listing package: text budgets, wording, and declarations.

    Args:
        root: Project folder.
        info: Parsed face-info root, or None when it failed to parse.
        findings: Findings to append to.
    """
    for relative in (STORE_LISTING_MD, README_MD):
        if not (root / relative).is_file():
            findings.append(Finding(SEVERITY_ERROR, "listing-file-missing", f"{relative} is absent", relative))
    _check_icon_size(root, findings)
    document = _read_json(root / MANIFEST_JSON, findings)
    if document is None:
        return
    listing = document.get("listing")
    if not isinstance(listing, dict):
        findings.append(Finding(SEVERITY_ERROR, "listing-missing", "manifest.json carries no listing block", MANIFEST_JSON))
        return
    for key, limit, code in (
        ("title", LISTING_TITLE_LIMIT, "listing-title-long"),
        ("short_description", LISTING_SHORT_LIMIT, "listing-short-long"),
        ("full_description", LISTING_FULL_LIMIT, "listing-full-long"),
    ):
        text = listing.get(key)
        value = text if isinstance(text, str) else ""
        if len(value) > limit:
            findings.append(
                Finding(SEVERITY_ERROR, code, f"{key} is {len(value)} characters; {limit} is the maximum", MANIFEST_JSON)
            )
    wording = " ".join(
        value
        for key in ("title", "short_description", "full_description")
        for value in [listing.get(key)]
        if isinstance(value, str)
    )
    if "Wear OS" not in wording:
        findings.append(Finding(SEVERITY_ERROR, "listing-wording-missing", "the listing must say Wear OS", MANIFEST_JSON))
    for key, code in (("data_safety", "listing-data-safety-missing"), ("ads", "listing-ads-missing")):
        declaration = listing.get(key)
        if not isinstance(declaration, str) or not declaration:
            findings.append(Finding(SEVERITY_ERROR, code, f"the listing must state its {key.replace('_', ' ')} declaration", MANIFEST_JSON))


def _read_json(path: Path, findings: list[Finding]) -> JsonMap | None:
    """Read one JSON document the gate scores.

    Args:
        path: File to read.
        findings: Findings to append to.

    Returns:
        The decoded object, or None when it is missing or malformed.
    """
    if not path.is_file():
        findings.append(Finding(SEVERITY_ERROR, "listing-file-missing", f"{path.name} is absent", path.name))
        return None
    try:
        parsed: Json = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as error:
        findings.append(Finding(SEVERITY_ERROR, "json-unparsable", f"{path.name} does not parse: {error}", path.name))
        return None
    if not isinstance(parsed, dict):
        findings.append(Finding(SEVERITY_ERROR, "json-shape", f"{path.name} must hold a JSON object", path.name))
        return None
    return parsed


def _png_chunks(data: bytes) -> tuple[int, int, int, int, bool, bytes] | None:
    """Pull the header, the transparency flag, and the image data out of a PNG.

    Args:
        data: Complete file bytes.

    Returns:
        Width, height, bit depth, colour type, whether ``tRNS`` is present, and
        the concatenated IDAT payload, or None when the file is not a PNG.
    """
    if not data.startswith(_PNG_SIGNATURE):
        return None
    width = height = bit_depth = color_type = 0
    has_trns = False
    idat = bytearray()
    seen_header = False
    for kind, payload in _iter_chunks(data):
        if kind == b"IHDR" and len(payload) >= _IHDR_BYTES and not seen_header:
            width, height, bit_depth, color_type, _compression, _filter, _interlace = struct.unpack(
                ">IIBBBBB", payload[:_IHDR_BYTES]
            )
            seen_header = True
        elif kind == b"tRNS":
            has_trns = True
        elif kind == b"IDAT":
            idat.extend(payload)
    if not seen_header:
        return None
    return width, height, bit_depth, color_type, has_trns, bytes(idat)


def _iter_chunks(data: bytes) -> tuple[tuple[bytes, bytes], ...]:
    """Walk the chunk list of a PNG file.

    Args:
        data: Complete file bytes, signature included.

    Returns:
        Chunk type and payload pairs, stopping at the first truncated chunk.
    """
    chunks: list[tuple[bytes, bytes]] = []
    cursor = len(_PNG_SIGNATURE)
    while cursor + 8 <= len(data):
        length = int.from_bytes(data[cursor : cursor + 4], "big")
        kind = data[cursor + 4 : cursor + 8]
        start = cursor + 8
        stop = start + length
        if stop + 4 > len(data):
            break
        chunks.append((kind, data[start:stop]))
        cursor = stop + 4
    return tuple(chunks)


def _unfilter(idat: bytes, width: int, height: int, channels: int) -> bytearray | None:
    """Undo the PNG scanline filters.

    Args:
        idat: Concatenated IDAT payload.
        width: Image width in pixels.
        height: Image height in pixels.
        channels: Bytes per pixel.

    Returns:
        Raw sample bytes, row after row, or None when the stream is malformed.
    """
    try:
        raw = zlib.decompress(idat)
    except zlib.error:
        return None
    stride = width * channels
    if height <= 0 or len(raw) != height * (stride + 1):
        return None
    out = bytearray(height * stride)
    cursor = 0
    for row in range(height):
        kind = raw[cursor]
        line = raw[cursor + 1 : cursor + 1 + stride]
        cursor += stride + 1
        base = row * stride
        above = base - stride
        has_above = row > 0
        if kind == _FILTER_NONE:
            out[base : base + stride] = line
        elif kind == _FILTER_SUB:
            for index in range(stride):
                left = out[base + index - channels] if index >= channels else 0
                out[base + index] = (line[index] + left) & 0xFF
        elif kind == _FILTER_UP:
            for index in range(stride):
                up = out[above + index] if has_above else 0
                out[base + index] = (line[index] + up) & 0xFF
        elif kind == _FILTER_AVERAGE:
            for index in range(stride):
                left = out[base + index - channels] if index >= channels else 0
                up = out[above + index] if has_above else 0
                out[base + index] = (line[index] + ((left + up) >> 1)) & 0xFF
        elif kind == _FILTER_PAETH:
            for index in range(stride):
                left = out[base + index - channels] if index >= channels else 0
                up = out[above + index] if has_above else 0
                up_left = out[above + index - channels] if has_above and index >= channels else 0
                out[base + index] = (line[index] + _paeth(left, up, up_left)) & 0xFF
        else:
            return None
    return out


def _paeth(left: int, above: int, above_left: int) -> int:
    """Predict a sample from its three neighbours.

    Args:
        left: Sample to the left.
        above: Sample above.
        above_left: Sample above and to the left.

    Returns:
        The neighbour whose value is closest to the plane estimate.
    """
    estimate = left + above - above_left
    delta_left = abs(estimate - left)
    delta_above = abs(estimate - above)
    delta_corner = abs(estimate - above_left)
    if delta_left <= delta_above:
        if delta_left <= delta_corner:
            return left
    if delta_above <= delta_corner:
        return above
    return above_left


def _all_opaque(pixels: bytes | bytearray, channels: int) -> bool:
    """Whether every pixel is fully opaque.

    Args:
        pixels: Raw sample bytes.
        channels: Bytes per pixel.

    Returns:
        True when no sample alpha falls below the threshold, and when the image
        carries no alpha channel at all.
    """
    if channels < 4:
        return True
    return all(pixels[index] >= _ALPHA_THRESHOLD for index in range(3, len(pixels), channels))


def _illuminated_ratio(
    pixels: bytes | bytearray, width: int, height: int, channels: int
) -> float:
    """Measure how much of an image a watch face lights up.

    Args:
        pixels: Raw sample bytes.
        width: Image width in pixels.
        height: Image height in pixels.
        channels: Bytes per pixel.

    Returns:
        Share of pixels that are visible and bright, between 0.0 and 1.0.
    """
    total = width * height
    if total <= 0:
        return 0.0
    lit = 0
    for index in range(total):
        offset = index * channels
        if channels >= 4 and pixels[offset + 3] < _ALPHA_THRESHOLD:
            continue
        red = pixels[offset]
        green = pixels[offset + 1] if channels >= 3 else red
        blue = pixels[offset + 2] if channels >= 3 else red
        if red * 299 + green * 587 + blue * 114 >= _LUMA_THRESHOLD * _LUMA_SCALE // 1000 * 1000 // _LUMA_SCALE:
            lit += 1
    return lit / total

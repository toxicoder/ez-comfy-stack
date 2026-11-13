"""Play and launcher compliance gate for a built icon pack.

Nothing here raises: a build that half-succeeds is worth more reported than
aborted, so every check appends a :class:`Finding` with a stable, greppable
code. The codes below are the contract an operator scripts against.

The rules come from the verified requirements digest: the 108 dp sheet with
its 66 dp safe zone and 48 dp artwork floor, the five mipmap buckets, the
512 px / 1024 KB Play icon, the 1024 x 500 feature graphic that must carry no
transparency, and the ``<monochrome>`` child AEP-TI-GAA demands with no
exemption.
"""

from __future__ import annotations

import json
import re
import struct
import xml.etree.ElementTree as ElementTree
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

from ez_common.json_value import JsonMap
from ez_raster import ADAPTIVE_CANVAS_DP, RasterError, decode_rgba

from .adaptive import (
    ADAPTIVE_LADDER,
    FEATURE_GRAPHIC_HEIGHT,
    FEATURE_GRAPHIC_WIDTH,
    LAUNCHER_BASE,
    LEGACY_LADDER,
    PLAY_ICON_MAX_BYTES,
    PLAY_ICON_PX,
)
from .catalog import IconSpec
from .glyphs import GLYPH_RECIPES, ARTWORK_MAX_DP, ARTWORK_MIN_DP, artwork_bounds

Severity: TypeAlias = Literal["error", "warning"]
"""``error`` blocks a submission; ``warning`` asks for a look."""

RESERVED_DP = (ADAPTIVE_CANVAS_DP - ARTWORK_MAX_DP) // 2
"""Per-side margin a launcher mask may consume on the 108 dp sheet."""

MEASURE_TOLERANCE_DP = 2
"""Antialiasing slack, so a rim pixel is not reported as a bleed."""

PNG_HEADER_BYTES = 26
"""Bytes of a PNG this reader needs: 8-byte signature, the 8-byte IHDR chunk
head, then width, height, bit depth, and colour type."""

ADAPTIVE_XML_REL = "app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml"
"""Where the launcher reads the adaptive-icon definition."""

MONOCHROME_ELEMENT_TAG = "monochrome"
"""Element name the AEP themed-icon rule is written about."""

MONOCHROME_MISSING = "MONOCHROME_MISSING"
"""No ``<monochrome>`` layer, or one that carries no artwork: no themed icons."""

SAFE_ZONE_BLED = "SAFE_ZONE_BLED"
"""Artwork reaches past the 66 dp safe zone into the masked margin."""

GLYPH_TOO_SMALL = "GLYPH_TOO_SMALL"
"""Artwork is under the 48 dp minimum, or absent entirely."""

DENSITY_MISSING = "DENSITY_MISSING"
"""A density bucket of the ladder was not written."""

REQUIRED_FILE_MISSING = "REQUIRED_FILE_MISSING"
"""A file ``manifest.json`` declares is not on disk."""

PLAY_ICON_SIZE = "PLAY_ICON_SIZE"
"""Play app icon is not the 512 x 512 square Play asks for."""

PLAY_ICON_BYTES = "PLAY_ICON_BYTES"
"""Play app icon is past the 1024 KB ceiling."""

FEATURE_GRAPHIC_SHAPE = "FEATURE_GRAPHIC_SHAPE"
"""Feature graphic is not 1024 x 500."""

FEATURE_GRAPHIC_ALPHA = "FEATURE_GRAPHIC_ALPHA"
"""Feature graphic carries a translucent pixel."""

APPFILTER_MALFORMED = "APPFILTER_MALFORMED"
"""``appfilter.xml`` does not parse or is not rooted at ``resources``."""

COMPONENT_INVALID = "COMPONENT_INVALID"
"""A ``component=`` or ``package=`` key does not parse."""

XML_MALFORMED = "XML_MALFORMED"
"""Another XML asset of the project does not parse."""

MANIFEST_MALFORMED = "MANIFEST_MALFORMED"
"""The pack ``manifest.json`` is absent or does not parse."""

DUPLICATE_SLUG = "DUPLICATE_SLUG"
"""Two entries share a slug."""

DRAWABLE_COLLISION = "DRAWABLE_COLLISION"
"""Two entries collapse onto one resource name."""

BRAND_NAME_SUSPECT = "BRAND_NAME_SUSPECT"
"""A catalog name looks like a vendor's own mark rather than a neutral label."""

GLYPH_UNKNOWN = "GLYPH_UNKNOWN"
"""An entry names a recipe no painter registered."""

ARTWORK_UNREADABLE = "ARTWORK_UNREADABLE"
"""A layer could not be decoded, so its artwork could not be measured."""

FINDING_CODES: tuple[str, ...] = (
    APPFILTER_MALFORMED,
    ARTWORK_UNREADABLE,
    BRAND_NAME_SUSPECT,
    COMPONENT_INVALID,
    DENSITY_MISSING,
    DRAWABLE_COLLISION,
    DUPLICATE_SLUG,
    FEATURE_GRAPHIC_ALPHA,
    FEATURE_GRAPHIC_SHAPE,
    GLYPH_TOO_SMALL,
    GLYPH_UNKNOWN,
    MANIFEST_MALFORMED,
    MONOCHROME_MISSING,
    PLAY_ICON_BYTES,
    PLAY_ICON_SIZE,
    REQUIRED_FILE_MISSING,
    SAFE_ZONE_BLED,
    XML_MALFORMED,
)
"""Every code this gate can emit, sorted, for docs and tests to pin."""

_PACKAGE_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+")
"""Shape of a Java-style dotted package name."""

_COMPONENT_RE = re.compile(r"ComponentInfo\{([^/{}]+)/([^/{}]+)\}")
"""The ``ComponentInfo{package/class}`` appfilter key."""

_INTERNAL_CAPS_RE = re.compile(r"[a-z][A-Z]")
"""Vendor-style capitalisation inside one word."""

_TOKEN_RE = re.compile(r"[^A-Za-z0-9]+")
"""Splitter for the words of a catalog name."""

_BRAND_PUNCTUATION_RE = re.compile(r"[+!~]|\b(?:official|brand)\b", re.IGNORECASE)
"""Marketing punctuation and filler words a vendor name tends to carry."""

_LEGAL_SUFFIXES = frozenset({"co", "corp", "gmbh", "inc", "limited", "llc", "lp", "ltd", "plc"})
"""Legal-entity tokens; a neutral label has no reason to carry one."""

_GENERIC_NOUNS = frozenset(
    {
        "alarm",
        "album",
        "bank",
        "browser",
        "calendar",
        "camera",
        "clock",
        "cloud",
        "contacts",
        "dictionary",
        "files",
        "fitness",
        "gallery",
        "games",
        "health",
        "mail",
        "messenger",
        "music",
        "news",
        "notes",
        "phone",
        "photos",
        "podcast",
        "radio",
        "reading",
        "scanner",
        "settings",
        "shield",
        "shopping",
        "tasks",
        "terminal",
        "translate",
        "tv",
        "vault",
        "video",
        "wallet",
        "weather",
    }
)
"""Launcher-generic nouns: a package's last segment that is one of these is a
product category, so a name repeating it is descriptive rather than a mark."""

_MONO_ATTR = "{http://schemas.android.com/apk/res/android}drawable"
"""Namespaced ``android:drawable`` attribute the adaptive layers carry."""

_APPFILTER_REL = "app/src/main/res/xml/appfilter.xml"
"""The mapping file every launcher reads."""

_XML_ASSETS: tuple[str, ...] = (
    "app/src/main/AndroidManifest.xml",
    "app/src/main/res/values/colors.xml",
    "app/src/main/res/values/strings.xml",
    "app/src/main/res/xml/drawable.xml",
    "app/src/main/res/xml/grayscale_icon_map.xml",
)
"""XML assets parsed for well-formedness; each reports XML_MALFORMED."""

_LAYER_SUFFIXES: tuple[str, ...] = ("_foreground", "_background", "_themed")
"""Adaptive layers every entry must carry in every bucket."""


@dataclass(frozen=True)
class Finding:
    """One compliance problem.

    Args:
        severity: ``error`` blocks a submission; ``warning`` is advisory.
        code: Stable string an operator can grep and script against.
        message: What is wrong, in one sentence.
        path: Project-relative file the finding points at, or an empty string
            for a whole-pack observation.
    """

    severity: Severity
    code: str
    message: str
    path: str = ""


def validate_catalog(catalog: Sequence[IconSpec]) -> list[Finding]:
    """Check a catalog for the problems only a cross-entry view can see.

    Args:
        catalog: Entries to check.

    Returns:
        Findings, in catalog order with the duplicate report last.
    """
    findings: list[Finding] = []
    counts: dict[str, int] = {}
    drawables: dict[str, str] = {}
    for spec in catalog:
        counts[spec.slug] = counts.get(spec.slug, 0) + 1
        for name in (spec.drawable, spec.themed_drawable):
            if name in drawables:
                findings.append(
                    Finding(
                        "error",
                        DRAWABLE_COLLISION,
                        f"{spec.slug!r} and {drawables[name]!r} both publish as {name!r}",
                        spec.slug,
                    )
                )
            drawables[name] = spec.slug
        if spec.glyph not in GLYPH_RECIPES:
            findings.append(
                Finding(
                    "error",
                    GLYPH_UNKNOWN,
                    f"glyph {spec.glyph!r} is not a registered recipe",
                    spec.slug,
                )
            )
        reason = suspect_brand(spec)
        if reason:
            findings.append(Finding("warning", BRAND_NAME_SUSPECT, reason, spec.slug))
    for slug, count in sorted(counts.items()):
        if count > 1:
            findings.append(
                Finding("error", DUPLICATE_SLUG, f"slug {slug!r} appears {count} times", slug)
            )
    return findings


def suspect_brand(spec: IconSpec) -> str:
    """Report why a name looks like a vendor mark rather than a neutral label.

    The check is deliberately brand-blind: a generator that ships a list of
    trademarks is a liability of its own. It looks instead for the shapes a
    pasted vendor name leaves behind.

    Args:
        spec: Entry to inspect.

    Returns:
        A one-line reason, or an empty string when the name reads neutral.
    """
    tokens = {token for token in _TOKEN_RE.split(spec.name.lower()) if token}
    legal = sorted(tokens & _LEGAL_SUFFIXES)
    if legal:
        return f"name carries the legal-entity token {legal[0]!r}"
    if _BRAND_PUNCTUATION_RE.search(spec.name):
        return "name carries brand punctuation or a marketing suffix"
    if _INTERNAL_CAPS_RE.search(spec.name):
        return "name uses vendor-style internal capitals"
    last = spec.package.rsplit(".", 1)[-1].lower()
    if len(last) >= 3 and last not in _GENERIC_NOUNS and spec.name.strip().lower() == last:
        return f"name repeats the package segment {last!r} verbatim"
    return ""


def validate_pack(root: Path | str) -> list[Finding]:
    """Check a built pack against the Play and launcher rules.

    Args:
        root: Project directory the pack verb wrote.

    Returns:
        Findings, grouped by asset and then by entry.
    """
    base = Path(root)
    findings: list[Finding] = []
    payload = _read_manifest(base, findings)
    _check_xml_assets(base, findings)
    _check_adaptive_xml(base, findings)
    _check_play_icon(base, findings)
    _check_feature_graphic(base, findings)
    _check_artwork(base, f"mipmap-mdpi/{LAUNCHER_BASE}_monochrome.png", findings)
    icons = payload.get("icons")
    if isinstance(icons, list):
        for record in icons:
            if isinstance(record, dict):
                _check_entry(base, record, findings)
            else:
                findings.append(
                    Finding("error", MANIFEST_MALFORMED, f"icon row {record!r} is not an object",
                            "manifest.json")
                )
    return findings


def _read_manifest(base: Path, findings: list[Finding]) -> JsonMap:
    """Load the pack inventory, reporting a problem instead of raising.

    Args:
        base: Project directory.
        findings: Accumulator the problem is appended to.

    Returns:
        The parsed object, or an empty mapping when it is unusable.
    """
    rel = "manifest.json"
    path = base / rel
    if not path.is_file():
        findings.append(Finding("error", MANIFEST_MALFORMED, f"{rel} is missing", rel))
        return {}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        findings.append(
            Finding("error", MANIFEST_MALFORMED, f"{rel} does not parse: {exc}", rel)
        )
        return {}
    if not isinstance(document, dict):
        findings.append(
            Finding("error", MANIFEST_MALFORMED, f"{rel} is not an object", rel)
        )
        return {}
    if not isinstance(document.get("icons"), list):
        findings.append(
            Finding("error", MANIFEST_MALFORMED, f"{rel} carries no 'icons' array", rel)
        )
        return {}
    return document


def _check_xml_assets(base: Path, findings: list[Finding]) -> None:
    """Parse every XML asset, ``appfilter.xml`` included.

    Args:
        base: Project directory.
        findings: Accumulator.
    """
    for rel in _XML_ASSETS:
        parse_xml(base / rel, rel, XML_MALFORMED, findings)
    root = parse_xml(base / _APPFILTER_REL, _APPFILTER_REL, APPFILTER_MALFORMED, findings)
    if root is None:
        return
    if root.tag != "resources":
        findings.append(
            Finding(
                "error",
                APPFILTER_MALFORMED,
                f"root element is {root.tag!r}, expected 'resources'",
                _APPFILTER_REL,
            )
        )
        return
    _check_appfilter_items(root, findings)


def parse_xml(
    path: Path, rel: str, code: str, findings: list[Finding]
) -> ElementTree.Element | None:
    """Parse one XML file, appending a finding when it will not parse.

    Args:
        path: File to read.
        rel: Project-relative path for the finding.
        code: Code to report.
        findings: Accumulator.

    Returns:
        The root element, or None when the file is absent or malformed.
    """
    if not path.is_file():
        findings.append(Finding("error", code, f"{rel} is missing", rel))
        return None
    try:
        return ElementTree.fromstring(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ElementTree.ParseError) as exc:
        findings.append(Finding("error", code, f"{rel} does not parse: {exc}", rel))
        return None


def _check_appfilter_items(root: ElementTree.Element, findings: list[Finding]) -> None:
    """Validate every ``<item>`` mapping in an appfilter tree.

    Args:
        root: The ``resources`` root element.
        findings: Accumulator.
    """
    for item in root.findall("item"):
        drawable = item.get("drawable", "").strip()
        component = item.get("component", "").strip()
        package = item.get("package", "").strip()
        if not drawable:
            findings.append(
                Finding("error", COMPONENT_INVALID, "item carries no drawable name", _APPFILTER_REL)
            )
        if not component and not package:
            findings.append(
                Finding(
                    "error",
                    COMPONENT_INVALID,
                    f"item for drawable {drawable!r} names neither component nor package",
                    _APPFILTER_REL,
                )
            )
        if component:
            match = _COMPONENT_RE.fullmatch(component)
            if match is None:
                findings.append(
                    Finding(
                        "error",
                        COMPONENT_INVALID,
                        f"component {component!r} does not parse",
                        _APPFILTER_REL,
                    )
                )
            elif _PACKAGE_RE.fullmatch(match.group(1)) is None:
                findings.append(
                    Finding(
                        "error",
                        COMPONENT_INVALID,
                        f"component {component!r} carries a package that does not parse",
                        _APPFILTER_REL,
                    )
                )
        elif package and _PACKAGE_RE.fullmatch(package) is None:
            findings.append(
                Finding(
                    "error", COMPONENT_INVALID, f"package {package!r} does not parse", _APPFILTER_REL
                )
            )


def _check_adaptive_xml(base: Path, findings: list[Finding]) -> None:
    """Require the adaptive XML, its root element, and its monochrome child.

    Args:
        base: Project directory.
        findings: Accumulator.
    """
    root = parse_xml(base / ADAPTIVE_XML_REL, ADAPTIVE_XML_REL, XML_MALFORMED, findings)
    if root is None:
        findings.append(
            Finding(
                "error",
                MONOCHROME_MISSING,
                "adaptive icon XML is unreadable, so no monochrome layer can qualify"
                " the pack for themed icons",
                ADAPTIVE_XML_REL,
            )
        )
        return
    if root.tag != "adaptive-icon":
        findings.append(Finding("error", XML_MALFORMED, f"root element is {root.tag!r}", ADAPTIVE_XML_REL))
    monochrome = root.find(MONOCHROME_ELEMENT_TAG)
    if monochrome is None or not (monochrome.get(_MONO_ATTR) or "").strip():
        findings.append(
            Finding(
                "error",
                MONOCHROME_MISSING,
                "adaptive icon XML has no monochrome layer, so the pack cannot qualify"
                " for themed icons",
                ADAPTIVE_XML_REL,
            )
        )


def _check_play_icon(base: Path, findings: list[Finding]) -> None:
    """Check the Play app icon shape and byte ceiling.

    Args:
        base: Project directory.
        findings: Accumulator.
    """
    rel = "store/play-icon.png"
    path = base / rel
    header = _png_header(path)
    if header is None:
        findings.append(Finding("error", PLAY_ICON_SIZE, f"{rel} is not a readable PNG", rel))
        return
    width, height = header[0], header[1]
    if width != PLAY_ICON_PX or height != PLAY_ICON_PX:
        findings.append(
            Finding(
                "error",
                PLAY_ICON_SIZE,
                f"Play icon is {width}x{height}, expected {PLAY_ICON_PX}x{PLAY_ICON_PX}",
                rel,
            )
        )
    size = path.stat().st_size
    if size > PLAY_ICON_MAX_BYTES:
        findings.append(
            Finding(
                "error",
                PLAY_ICON_BYTES,
                f"Play icon is {size} bytes, over the {PLAY_ICON_MAX_BYTES} ceiling",
                rel,
            )
        )


def _check_feature_graphic(base: Path, findings: list[Finding]) -> None:
    """Check the feature graphic shape and its alpha.

    Args:
        base: Project directory.
        findings: Accumulator.
    """
    rel = "store/feature-graphic.png"
    path = base / rel
    header = _png_header(path)
    if header is None:
        findings.append(
            Finding("error", FEATURE_GRAPHIC_SHAPE, f"{rel} is not a readable PNG", rel)
        )
        return
    width, height = header[0], header[1]
    if width != FEATURE_GRAPHIC_WIDTH or height != FEATURE_GRAPHIC_HEIGHT:
        findings.append(
            Finding(
                "error",
                FEATURE_GRAPHIC_SHAPE,
                f"feature graphic is {width}x{height}, expected"
                f" {FEATURE_GRAPHIC_WIDTH}x{FEATURE_GRAPHIC_HEIGHT}",
                rel,
            )
        )
    try:
        sheet = decode_rgba(str(path), FEATURE_GRAPHIC_HEIGHT)
    except RasterError as exc:
        findings.append(Finding("warning", ARTWORK_UNREADABLE, f"feature graphic: {exc}", rel))
        return
    alpha = min(sheet.pixels[3::4])
    if alpha < 255:
        findings.append(
            Finding(
                "error",
                FEATURE_GRAPHIC_ALPHA,
                f"feature graphic carries alpha down to {alpha}; Play wants none",
                rel,
            )
        )


def _check_entry(base: Path, record: JsonMap, findings: list[Finding]) -> None:
    """Check one published entry against the ladder and the safe zone.

    Args:
        base: Project directory.
        record: Its ``manifest.json`` row.
        findings: Accumulator.
    """
    slug = record.get("slug")
    label = slug if isinstance(slug, str) else ""
    drawable_value = record.get("drawable")
    drawable = drawable_value if isinstance(drawable_value, str) else ""
    if not drawable:
        findings.append(
            Finding("error", DENSITY_MISSING, "entry carries no drawable name", label)
        )
        return
    for declared in _declared_files(record):
        if not (base / "app/src/main/res" / declared).is_file():
            findings.append(
                Finding("error", REQUIRED_FILE_MISSING, f"{declared} is not on disk", declared)
            )
    for density, _ in ADAPTIVE_LADDER:
        for suffix in _LAYER_SUFFIXES:
            _expect_layer(base, f"drawable-{density}/{drawable}{suffix}.png", findings)
    for density, _ in LEGACY_LADDER:
        _expect_layer(base, f"drawable-{density}/{drawable}.png", findings)
    _check_artwork(base, f"drawable-mdpi/{drawable}_foreground.png", findings)
    _check_artwork(base, f"drawable-mdpi/{drawable}_themed.png", findings)


def _expect_layer(base: Path, rel: str, findings: list[Finding]) -> None:
    """Require one rung of the density ladder.

    Args:
        base: Project directory.
        rel: Layer path relative to ``res``.
        findings: Accumulator.
    """
    if not (base / "app/src/main/res" / rel).is_file():
        findings.append(Finding("error", DENSITY_MISSING, f"{rel} is missing", rel))


def _declared_files(record: JsonMap) -> tuple[str, ...]:
    """Read the ``files`` list of one manifest row.

    Args:
        record: The row.

    Returns:
        Declared resource paths, sorted; empty when the row has none.
    """
    files = record.get("files")
    if not isinstance(files, list):
        return ()
    return tuple(sorted(str(item) for item in files if isinstance(item, str)))


def _check_artwork(base: Path, rel: str, findings: list[Finding]) -> None:
    """Measure one layer against the safe zone and the 48 dp floor.

    Args:
        base: Project directory.
        rel: Layer path relative to ``res``.
        findings: Accumulator.
    """
    path = base / "app/src/main/res" / rel
    if not path.is_file():
        return
    try:
        sheet = decode_rgba(str(path), ADAPTIVE_CANVAS_DP)
    except RasterError as exc:
        findings.append(Finding("warning", ARTWORK_UNREADABLE, f"{rel}: {exc}", rel))
        return
    bounds = artwork_bounds(sheet)
    if bounds is None:
        monochrome = rel.endswith(("_themed.png", "_monochrome.png"))
        code = MONOCHROME_MISSING if monochrome else GLYPH_TOO_SMALL
        findings.append(Finding("error", code, f"{rel} carries no artwork", rel))
        return
    left, top, right, bottom = bounds
    edge = max(right - left + 1, bottom - top + 1)
    limit = sheet.width - 1 - RESERVED_DP + MEASURE_TOLERANCE_DP
    if (
        left < RESERVED_DP - MEASURE_TOLERANCE_DP
        or top < RESERVED_DP - MEASURE_TOLERANCE_DP
        or right > limit
        or bottom > limit
    ):
        findings.append(
            Finding(
                "error",
                SAFE_ZONE_BLED,
                f"{rel} artwork spans columns {left}..{right} and rows {top}..{bottom},"
                f" outside the {ARTWORK_MAX_DP} dp safe zone",
                rel,
            )
        )
    if edge < ARTWORK_MIN_DP - MEASURE_TOLERANCE_DP:
        findings.append(
            Finding(
                "error",
                GLYPH_TOO_SMALL,
                f"{rel} artwork is {edge} dp across, under the {ARTWORK_MIN_DP} dp minimum",
                rel,
            )
        )


def _png_header(path: Path) -> tuple[int, int, int, int] | None:
    """Read the IHDR of a PNG without decoding it.

    Args:
        path: File to inspect.

    Returns:
        ``(width, height, bit_depth, color_type)``, or None when the file is
        absent, short, or not a PNG.
    """
    try:
        with path.open("rb") as handle:
            head = handle.read(PNG_HEADER_BYTES)
    except OSError:
        return None
    if len(head) < PNG_HEADER_BYTES or head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    width, height, depth, color = struct.unpack(">IIBB", head[16:26])
    return (width, height, depth, color)

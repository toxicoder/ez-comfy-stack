"""Hermetic tests for the Play and launcher compliance gate."""

from __future__ import annotations

import json
import shutil
import sys
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_icons import validate as validate_module  # noqa: E402
from ez_icons.catalog import ICON_CATALOG, IconSpec, by_slug  # noqa: E402
from ez_icons.glyphs import ARTWORK_MAX_DP, ARTWORK_MIN_DP  # noqa: E402
from ez_icons.pack import Theme, build_pack  # noqa: E402
from ez_icons.validate import (  # noqa: E402
    ADAPTIVE_XML_REL,
    APPFILTER_MALFORMED,
    ARTWORK_UNREADABLE,
    BRAND_NAME_SUSPECT,
    COMPONENT_INVALID,
    DENSITY_MISSING,
    DUPLICATE_SLUG,
    DRAWABLE_COLLISION,
    FEATURE_GRAPHIC_ALPHA,
    FEATURE_GRAPHIC_SHAPE,
    FINDING_CODES,
    GLYPH_TOO_SMALL,
    GLYPH_UNKNOWN,
    MANIFEST_MALFORMED,
    MEASURE_TOLERANCE_DP,
    MONOCHROME_MISSING,
    PNG_HEADER_BYTES,
    PLAY_ICON_BYTES,
    PLAY_ICON_SIZE,
    RESERVED_DP,
    REQUIRED_FILE_MISSING,
    SAFE_ZONE_BLED,
    XML_MALFORMED,
    Finding,
    parse_xml,
    suspect_brand,
    validate_catalog,
    validate_pack,
)
from ez_raster import Canvas, Rgba, TRANSPARENT, WHITE  # noqa: E402

SLUGS = ("chat-bubble", "weather-sun")
ENTRIES = tuple(found for slug in SLUGS if (found := by_slug(slug)) is not None)
APPFILTER_REL = "app/src/main/res/xml/appfilter.xml"
PLAY_REL = "store/play-icon.png"
FEATURE_REL = "store/feature-graphic.png"
FRONT_REL = "app/src/main/res/drawable-mdpi/chat_bubble_foreground.png"
THEMED_REL = "app/src/main/res/drawable-mdpi/chat_bubble_themed.png"


def spec(**overrides: object) -> IconSpec:
    """Build one entry for a catalog check.

    Args:
        overrides: Field values to replace.

    Returns:
        A validated spec.
    """
    fields: dict[str, object] = {
        "slug": "probe-icon",
        "name": "Probe Icon",
        "package": "com.probe.app",
        "glyph": "star",
    }
    fields.update(overrides)
    return IconSpec(**fields)  # type: ignore[arg-type]


def codes(findings: Iterable[Finding]) -> set[str]:
    """Collect the codes a finding list reports.

    Args:
        findings: Findings to read.

    Returns:
        The distinct codes.
    """
    return {finding.code for finding in findings}


@pytest.fixture(scope="module")
def healthy(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build one small pack that is expected to pass every check.

    Args:
        tmp_path_factory: Pytest temporary directory factory.

    Returns:
        The project root.
    """
    out = tmp_path_factory.mktemp("healthy") / "pack"
    build_pack(ENTRIES, out, theme=Theme(name="Healthy Pack"))
    return out


@pytest.fixture
def pack_dir(tmp_path: Path, healthy: Path) -> Path:
    """Copy the healthy pack into a scratch directory.

    Args:
        tmp_path: Per-test temporary directory.
        healthy: The module-scoped healthy pack.

    Returns:
        The copy to mutate.
    """
    target = tmp_path / "pack"
    shutil.copytree(healthy, target)
    return target


def write_layer(root: Path, rel: str, canvas: Canvas) -> None:
    """Overwrite one layer with caller-supplied pixels.

    Args:
        root: Project root.
        rel: Path relative to the project root.
        canvas: Pixels to write.
    """
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.write_png(str(path))


def test_constant_block_is_sourced_from_the_digest() -> None:
    assert RESERVED_DP == (108 - ARTWORK_MAX_DP) // 2
    assert MEASURE_TOLERANCE_DP == 2
    assert PNG_HEADER_BYTES == 26
    assert ADAPTIVE_XML_REL == "app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml"
    assert ARTWORK_MIN_DP == 48
    assert FINDING_CODES == tuple(sorted(FINDING_CODES))
    assert len(set(FINDING_CODES)) == len(FINDING_CODES)
    for code in FINDING_CODES:
        assert code.isupper() and code.replace("_", "").isalnum()


def test_finding_defaults() -> None:
    finding = Finding("error", "X", "message")
    assert finding.path == ""
    assert finding.severity == "error"


def test_healthy_pack_is_clean(healthy: Path) -> None:
    assert validate_pack(healthy) == []
    assert validate_catalog(ICON_CATALOG) == []


def test_missing_everything_is_reported(tmp_path: Path) -> None:
    findings = validate_pack(tmp_path / "absent")
    assert MANIFEST_MALFORMED in codes(findings)
    assert {APPFILTER_MALFORMED, XML_MALFORMED, PLAY_ICON_SIZE, FEATURE_GRAPHIC_SHAPE} <= codes(
        findings
    )
    assert MONOCHROME_MISSING in codes(findings)


@pytest.mark.parametrize(
    "body", ["not json at all", "[]", '{"icons": "nope"}', '{"icons": ["not an object"]}']
)
def test_manifest_problems(pack_dir: Path, body: str) -> None:
    (pack_dir / "manifest.json").write_text(body, encoding="utf-8")
    assert MANIFEST_MALFORMED in codes(validate_pack(pack_dir))


def test_manifest_without_an_icons_key(pack_dir: Path) -> None:
    (pack_dir / "manifest.json").write_text(json.dumps({"pack_name": "x"}), encoding="utf-8")
    findings = validate_pack(pack_dir)
    assert MANIFEST_MALFORMED in codes(findings)
    assert any("no 'icons' array" in finding.message for finding in findings)


def test_entry_without_a_drawable(pack_dir: Path) -> None:
    payload = json.loads((pack_dir / "manifest.json").read_text(encoding="utf-8"))
    del payload["icons"][0]["drawable"]
    (pack_dir / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    findings = validate_pack(pack_dir)
    assert DENSITY_MISSING in codes(findings)
    assert any("no drawable name" in finding.message for finding in findings)


def test_declared_file_missing_and_density_missing(pack_dir: Path) -> None:
    payload = json.loads((pack_dir / "manifest.json").read_text(encoding="utf-8"))
    payload["icons"][0]["files"].append("drawable-mdpi/invented.png")
    (pack_dir / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    (pack_dir / "app/src/main/res/drawable-xxxhdpi/chat_bubble_themed.png").unlink()
    findings = validate_pack(pack_dir)
    assert REQUIRED_FILE_MISSING in codes(findings)
    assert DENSITY_MISSING in codes(findings)
    assert any("invented.png" in finding.path for finding in findings)


def test_declared_files_may_be_absent_or_ragged(pack_dir: Path) -> None:
    payload = json.loads((pack_dir / "manifest.json").read_text(encoding="utf-8"))
    payload["icons"][0]["files"] = ["ok.png", 7]
    del payload["icons"][1]["files"]
    (pack_dir / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    assert REQUIRED_FILE_MISSING in codes(validate_pack(pack_dir))


def write_solid(root: Path, rel: str, colour: Rgba, side: int = 108) -> None:
    """Write one opaque layer of a single colour.

    Args:
        root: Project root.
        rel: Path relative to the project root.
        colour: Fill colour.
        side: Layer edge.
    """
    write_layer(root, rel, Canvas(side, side, colour))


def test_monochrome_layer_without_artwork(pack_dir: Path) -> None:
    write_layer(pack_dir, THEMED_REL, Canvas(108, 108, TRANSPARENT))
    findings = validate_pack(pack_dir)
    assert MONOCHROME_MISSING in codes(findings)


def test_launcher_monochrome_layer_without_artwork(pack_dir: Path) -> None:
    write_layer(pack_dir, "app/src/main/res/mipmap-mdpi/ic_launcher_monochrome.png", Canvas(108, 108, TRANSPARENT))
    assert MONOCHROME_MISSING in codes(validate_pack(pack_dir))


def test_glyph_under_the_minimum(pack_dir: Path) -> None:
    tiny = Canvas(108, 108, TRANSPARENT)
    tiny.fill_rect(52, 52, 4, 4, WHITE)
    write_layer(pack_dir, FRONT_REL, tiny)
    findings = validate_pack(pack_dir)
    assert GLYPH_TOO_SMALL in codes(findings)


def test_foreground_without_artwork(pack_dir: Path) -> None:
    write_layer(pack_dir, FRONT_REL, Canvas(108, 108, TRANSPARENT))
    findings = validate_pack(pack_dir)
    assert GLYPH_TOO_SMALL in codes(findings)
    assert MONOCHROME_MISSING not in codes(
        {finding for finding in findings if finding.path == FRONT_REL}
    )


def test_artwork_outside_the_safe_zone(pack_dir: Path) -> None:
    write_solid(pack_dir, FRONT_REL, WHITE)
    findings = validate_pack(pack_dir)
    assert SAFE_ZONE_BLED in codes(findings)
    assert any("safe zone" in finding.message for finding in findings)


def test_unreadable_layer_is_a_warning(pack_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from ez_raster import RasterError

    def refuse(path: str, side: int | None = None) -> Canvas:
        del path, side
        raise RasterError("ffmpeg refused")

    monkeypatch.setattr(validate_module, "decode_rgba", refuse)
    findings = validate_pack(pack_dir)
    assert ARTWORK_UNREADABLE in codes(findings)
    assert all(finding.severity == "warning" for finding in findings if finding.code == ARTWORK_UNREADABLE)


def test_play_icon_shape_and_bytes(pack_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_layer(pack_dir, PLAY_REL, Canvas(256, 256, WHITE))
    assert PLAY_ICON_SIZE in codes(validate_pack(pack_dir))
    (pack_dir / PLAY_REL).write_bytes(b"not a png")
    assert PLAY_ICON_SIZE in codes(validate_pack(pack_dir))
    write_solid(pack_dir, PLAY_REL, WHITE, 512)
    monkeypatch.setattr(validate_module, "PLAY_ICON_MAX_BYTES", 128)
    assert PLAY_ICON_BYTES in codes(validate_pack(pack_dir))


def test_feature_graphic_shape_and_alpha(pack_dir: Path) -> None:
    write_layer(pack_dir, FEATURE_REL, Canvas(500, 500, WHITE))
    assert FEATURE_GRAPHIC_SHAPE in codes(validate_pack(pack_dir))
    (pack_dir / FEATURE_REL).write_bytes(b"not a png")
    assert FEATURE_GRAPHIC_SHAPE in codes(validate_pack(pack_dir))
    translucent = Canvas(1024, 500, TRANSPARENT)
    translucent.fill_rect(0, 0, 512, 500, WHITE)
    write_layer(pack_dir, FEATURE_REL, translucent)
    assert FEATURE_GRAPHIC_ALPHA in codes(validate_pack(pack_dir))


def test_feature_graphic_unreadable_is_a_warning(
    pack_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ez_raster import RasterError

    def refuse(path: str, side: int | None = None) -> Canvas:
        del path, side
        raise RasterError("ffmpeg refused")

    monkeypatch.setattr(validate_module, "decode_rgba", refuse)
    findings = validate_pack(pack_dir)
    unreadable = [finding for finding in findings if finding.code == ARTWORK_UNREADABLE]
    assert unreadable
    assert all(finding.severity == "warning" for finding in unreadable)
    assert any("feature graphic" in finding.message for finding in unreadable)


def test_adaptive_xml_problems(pack_dir: Path) -> None:
    path = pack_dir / ADAPTIVE_XML_REL
    path.write_text("<resources />", encoding="utf-8")
    assert XML_MALFORMED in codes(validate_pack(pack_dir))
    path.write_text("<adaptive-icon />", encoding="utf-8")
    assert MONOCHROME_MISSING in codes(validate_pack(pack_dir))
    path.write_text(
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">'
        "<monochrome /></adaptive-icon>",
        encoding="utf-8",
    )
    assert MONOCHROME_MISSING in codes(validate_pack(pack_dir))
    path.write_text("<broken>", encoding="utf-8")
    assert XML_MALFORMED in codes(validate_pack(pack_dir))
    path.unlink()
    assert XML_MALFORMED in codes(validate_pack(pack_dir))


def test_appfilter_problems(pack_dir: Path) -> None:
    path = pack_dir / APPFILTER_REL
    path.write_text("<resources><item", encoding="utf-8")
    assert APPFILTER_MALFORMED in codes(validate_pack(pack_dir))
    path.write_text("<icons />", encoding="utf-8")
    findings = validate_pack(pack_dir)
    assert APPFILTER_MALFORMED in codes(findings)
    assert any("root element" in finding.message for finding in findings)


@pytest.mark.parametrize(
    ("attributes", "needle"),
    [
        ('drawable="" package="com.a.b"', "no drawable name"),
        ('drawable="ok"', "names neither component nor package"),
        ('drawable="ok" component="ComponentInfo{nonsense}"', "does not parse"),
        (
            'drawable="ok" component="ComponentInfo{1bad/.Main}"',
            "package that does not parse",
        ),
        ('drawable="ok" package="1bad"', "package '1bad' does not parse"),
    ],
)
def test_appfilter_items(pack_dir: Path, attributes: str, needle: str) -> None:
    body = (
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        f"    <item {attributes} />\n</resources>\n"
    )
    (pack_dir / APPFILTER_REL).write_text(body, encoding="utf-8")
    findings = validate_pack(pack_dir)
    assert COMPONENT_INVALID in codes(findings)
    assert any(needle in finding.message for finding in findings)


def test_appfilter_accepts_a_valid_pair(pack_dir: Path) -> None:
    body = (
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        '    <item component="ComponentInfo{com.a.b/.Main}" drawable="one" />\n'
        '    <item package="com.a.c" drawable="two" />\n'
        "</resources>\n"
    )
    (pack_dir / APPFILTER_REL).write_text(body, encoding="utf-8")
    findings = validate_pack(pack_dir)
    assert COMPONENT_INVALID not in codes(findings)


def test_parse_xml_reports_a_read_failure(tmp_path: Path) -> None:
    findings: list[Finding] = []
    assert parse_xml(tmp_path / "gone.xml", "gone.xml", XML_MALFORMED, findings) is None
    target = tmp_path / "binary.xml"
    target.write_bytes(b"\xff\xfe\x00broken")
    assert parse_xml(target, "binary.xml", XML_MALFORMED, findings) is None
    assert all(finding.code == XML_MALFORMED for finding in findings)
    good = tmp_path / "good.xml"
    good.write_text("<resources />", encoding="utf-8")
    assert parse_xml(good, "good.xml", XML_MALFORMED, findings) is not None


def test_catalog_unknown_glyph_and_duplicates() -> None:
    findings = validate_catalog([spec(glyph="nope"), spec(slug="probe-icon", name="Probe Two")])
    assert GLYPH_UNKNOWN in codes(findings)
    assert DUPLICATE_SLUG in codes(findings)


def test_catalog_drawable_collision() -> None:
    first = spec(slug="star", name="Star Mark")
    second = spec(slug="star-themed", name="Star Themed")
    findings = validate_catalog([first, second])
    assert DRAWABLE_COLLISION in codes(findings)
    assert any("star_themed" in finding.message for finding in findings)


@pytest.mark.parametrize(
    ("name", "package", "needle"),
    [
        ("Wallet Co", "com.probe.app", "legal-entity token"),
        ("Wallet Inc", "com.probe.app", "legal-entity token"),
        ("Wallet+ Plus", "com.probe.app", "brand punctuation"),
        ("Wallet Official", "com.probe.app", "marketing suffix"),
        ("ProWallet", "com.probe.app", "internal capitals"),
        ("Ledger", "com.probe.ledger", "verbatim"),
    ],
)
def test_suspect_brand_shapes(name: str, package: str, needle: str) -> None:
    entry = spec(name=name, package=package)
    assert needle in suspect_brand(entry)
    assert BRAND_NAME_SUSPECT in codes(validate_catalog([entry]))


def test_suspect_brand_accepts_a_neutral_label() -> None:
    assert suspect_brand(spec()) == ""
    assert suspect_brand(spec(name="Wallet", package="com.ledgerbook.wallet")) == ""
    assert suspect_brand(spec(name="Io", package="com.probe.io")) == ""


def test_main_reports_a_failing_pack(
    pack_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from ez_icons.pack import main

    (pack_dir / THEMED_REL).unlink()
    assert main(["--out", str(pack_dir), "--validate-only"]) == 1
    printed = capsys.readouterr().out
    assert "error: DENSITY_MISSING" in printed

"""Build a sellable Android icon-pack project from the catalog.

One call writes an installable ADW/Nova/Lawnchair icon pack: the manifest with
every discovery intent filter, ``res/xml/appfilter.xml`` mapping each entry by
``ComponentInfo{package/component}`` (or by package alone), ``drawable.xml``
for the manual picker, ``grayscale_icon_map.xml`` for themed icons, the
``iconback`` / ``iconmask`` / ``iconupon`` / ``iconunavailable`` sheets, the
adaptive layer ladder, the Play Store icon and feature graphic, and the
listing paperwork an operator ships with.

Output is deterministic: identical inputs produce identical bytes. Nothing
here reads a clock, no dictionary is iterated in insertion order where a sort
would do, and every file list is sorted before it is written or reported.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from ez_raster import BLACK, TRANSPARENT, WHITE, Canvas, Rgba, hex_to_rgba

from .adaptive import (
    ADAPTIVE_LADDER,
    FEATURE_GRAPHIC_HEIGHT,
    FEATURE_GRAPHIC_WIDTH,
    LEGACY_LADDER,
    PLAY_ICON_PX,
    IconLayers,
    icon_layer_paths,
    write_feature_graphic,
    write_icon_set,
    write_launcher_icon_set,
    write_launcher_xml,
    write_play_icon,
)
from .catalog import ICON_CATALOG, IconSpec, load_catalog, new_icon_scaffold, select
from .validate import Finding, validate_catalog, validate_pack

GENERATOR_NAME = "ez_icons"
"""Identity written into ``manifest.json`` so a pack is traceable."""

DEFAULT_PACK_NAME = "Studio Adaptive Icons"
"""Pack name a build uses when the operator supplies none."""

DEFAULT_PACK_VERSION = "1.0.0"
"""Version a build uses when the operator supplies none."""

PACK_CATEGORY = "Art & Design"
"""Play Store category an icon pack belongs to.

The policy pages name no icon-pack category, so this is the closest published
one; the listing page carries it as a suggestion the operator confirms.
"""

SHEET_SIDE = 512
"""Edge of the iconback / iconmask / iconupon / iconunavailable sheets."""

NODPI_DIR = "drawable-nodpi"
"""Qualifier the fallback sheets live in, so no density rescales them."""

SHEET_NAMES: tuple[str, ...] = (
    "iconback",
    "iconmask",
    "iconupon",
    "iconunavailable",
)
"""The four fallback sheets an ADW launcher composites behind an unmapped app.

``iconunavailable`` is the launcher-specific extra the vendor docs do not
name; it ships because packs that carry it render a tidy placeholder instead
of a raw app icon.
"""

SHORT_DESCRIPTION_LIMIT = 80
"""Short description ceiling from the Play preview-assets page."""

DEFAULT_SHORT_DESCRIPTION = (
    "Adaptive icon pack with themed icons for launchers that support them"
)
"""Fallback short description, kept under :data:`SHORT_DESCRIPTION_LIMIT`."""

DATA_SAFETY_STATEMENT = (
    "This app collects no user data. It requests no account, sends no network"
    " traffic, and stores nothing beyond the icon pack itself on the device,"
    " so there is no data to share, encrypt in transit, or delete on request."
)
"""What the Play Console data-safety form can honestly be answered with."""

ADS_STATEMENT = (
    "This pack displays no advertising of any kind: no ad SDK, no banner, no"
    " interstitial, and no native ad. The honest answer to the Play ads"
    ' declaration is "No", so the listing carries no "Contains ads" label.'
)
"""Ads declaration for a pack that serves nothing."""

PRIVACY_STATEMENT = (
    "Play requires a public https privacy policy on the store listing and"
    " inside the app, even for an app that handles no personal data. Publish"
    " a stable page and point both the listing and the in-app settings entry"
    " at it."
)
"""Privacy-policy obligation Play places on every listing."""

_MANIFEST_HEAD = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    "<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\""
    ' package="{package}">\n'
)
"""Opening of ``AndroidManifest.xml``, with the application id filled in."""

_ACTIVITY_OPEN = (
    '    <activity\n'
    '        android:name=".IconPackActivity"\n'
    '        android:label="@string/app_name"\n'
    '        android:icon="@mipmap/ic_launcher"\n'
    '        android:exported="true"\n'
    '        android:theme="@android:style/Theme.Material.Light">\n'
)
"""Activity the launchers bind to; every discovery filter hangs off it."""

_INTENT_ACTIONS: tuple[str, ...] = (
    "org.adw.launcher.THEMES",
    "org.adw.ActivityStarter.THEMES",
    "com.novalauncher.THEME",
    "app.lawnchair.icons.THEMED_ICON",
)
"""Every discovery action a third-party launcher looks for."""

_THEMED_ICON_META = (
    '        <meta-data android:name="app.lawnchair.icons.THEMED_ICON"'
    ' android:value="res/xml/grayscale_icon_map.xml" />\n'
)
"""Lawnchair pointer at the themed-icon map."""

_SMART_LAUNCHER_META: tuple[tuple[str, str], ...] = (
    ("org.icontheme.CHANGES_WITH_MATERIAL_YOU_COLORS", "1"),
    ("org.icontheme.CHANGES_WITH_DARK_MODE", "1"),
    ("org.icontheme.FALLBACK_TO_THEMED_ICON", "0"),
    ("org.icontheme.icon_background_color", "@color/org_icontheme_icon_background_color"),
    ("org.icontheme.icon_color", "@color/org_icontheme_icon_color"),
)
"""Smart Launcher flags and tint colours, as name / value pairs.

The vendor documents the two tint keys as ``org.icontheme.*`` dotted names;
the resource itself has to be a legal Android name, so the colour is declared
underscored and reached through the dotted meta-data name.
"""


@dataclass(frozen=True)
class Theme:
    """Pack-level look and listing identity.

    Args:
        name: Pack name, used for ``app_name`` and the listing title.
        version: Dotted version string.
        package: Android application id.
        accent: Backing colour of the feature graphic.
        icon_background_color: Smart Launcher fallback field colour.
        icon_color: Smart Launcher fallback glyph colour.
        short_description: Play short description, 80 characters or fewer.
        background_override: When set, every entry is built with this
            background instead of its own.
    """

    name: str = DEFAULT_PACK_NAME
    version: str = DEFAULT_PACK_VERSION
    package: str = "com.studio.adaptiveicons"
    accent: str = "#16212B"
    icon_background_color: str = "#101820"
    icon_color: str = "#F2F5F7"
    short_description: str = DEFAULT_SHORT_DESCRIPTION
    background_override: str = ""


@dataclass(frozen=True)
class PackResult:
    """What one build produced.

    Args:
        out_dir: Directory the project was written to.
        pack_name: Theme name it was built under.
        pack_version: Theme version it was built under.
        icon_count: Entries published.
        files: Project-relative paths written, sorted.
        total_bytes: Bytes on disk; a dry run reports what it would write.
        dry_run: True when nothing touched the filesystem.
    """

    out_dir: str
    pack_name: str
    pack_version: str
    icon_count: int
    files: tuple[str, ...]
    total_bytes: int
    dry_run: bool


def _xml_escape(text: str) -> str:
    """Escape text headed for an XML attribute.

    Args:
        text: Raw value.

    Returns:
        The value with the five XML predefined entities applied.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _apply_theme(catalog: Sequence[IconSpec], theme: Theme) -> tuple[IconSpec, ...]:
    """Apply the theme's background override across a catalog.

    Args:
        catalog: Entries to adjust.
        theme: Pack theme in force.

    Returns:
        The entries, re-backgrounded when the theme asked for it.
    """
    if not theme.background_override:
        return tuple(catalog)
    return tuple(replace(spec, background=theme.background_override) for spec in catalog)


def appfilter_xml(entries: Sequence[IconSpec], pack_name: str) -> str:
    """Render ``res/xml/appfilter.xml``.

    Mapping is by ``component=`` when the entry names an activity and by
    ``package=`` otherwise, which is what the launchers actually resolve; no
    launcher looks an icon up by a filename convention.

    Args:
        entries: Entries to map, in catalog order.
        pack_name: Name for the header comment.

    Returns:
        The XML document.
    """
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        f"<!-- {pack_name}: generated by {GENERATOR_NAME} -->",
        "<resources>",
        '    <iconback img1="iconback" />',
        '    <iconmask img1="iconmask" />',
        '    <iconupon img1="iconupon" />',
        '    <scale factor="1.0" />',
    ]
    for spec in entries:
        if spec.component_info:
            key = f'component="{_xml_escape(spec.component_info)}"'
        else:
            key = f'package="{_xml_escape(spec.package)}"'
        lines.append(f'    <item {key} drawable="{spec.drawable}" />')
    lines.append("</resources>")
    return "\n".join(lines) + "\n"


def drawable_xml(entries: Sequence[IconSpec], pack_name: str) -> str:
    """Render ``res/xml/drawable.xml`` grouped into picker categories.

    Args:
        entries: Entries to list; order is picker order.
        pack_name: Name for the header comment.

    Returns:
        The XML document.
    """
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        f"<!-- {pack_name}: generated by {GENERATOR_NAME} -->",
        "<resources>",
    ]
    seen: set[str] = set()
    for spec in entries:
        if spec.category not in seen:
            seen.add(spec.category)
            lines.append(f'    <category title="{_xml_escape(spec.category)}" />')
        lines.append(f'    <item drawable="{spec.drawable}" />')
    lines.append("</resources>")
    return "\n".join(lines) + "\n"


def grayscale_icon_map_xml(entries: Sequence[IconSpec], pack_name: str) -> str:
    """Render ``res/xml/grayscale_icon_map.xml`` for themed icons.

    The map is per-package: the launcher takes no component here.

    Args:
        entries: Entries to map.
        pack_name: Name for the header comment.

    Returns:
        The XML document.
    """
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        f"<!-- {pack_name}: themed icon map generated by {GENERATOR_NAME} -->",
        "<resources>",
        "    <icons>",
    ]
    for spec in entries:
        lines.append(
            f'        <icon package="{_xml_escape(spec.package)}"'
            f' drawable="@drawable/{spec.themed_drawable}"'
            f' name="{_xml_escape(spec.name)}" />'
        )
    lines.extend(("    </icons>", "</resources>"))
    return "\n".join(lines) + "\n"


def strings_xml(entries: Sequence[IconSpec], theme: Theme) -> str:
    """Render ``res/values/strings.xml`` with a label per icon.

    Args:
        entries: Entries whose names become labels.
        theme: Pack theme carrying the app name.

    Returns:
        The XML document.
    """
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        "<resources>",
        f'    <string name="app_name">{_xml_escape(theme.name)}</string>',
    ]
    for spec in entries:
        lines.append(f'    <string name="{spec.drawable}">{_xml_escape(spec.name)}</string>')
    lines.append("</resources>")
    return "\n".join(lines) + "\n"


def colors_xml(theme: Theme) -> str:
    """Render ``res/values/colors.xml`` with the Smart Launcher tints.

    Args:
        theme: Pack theme carrying the two colours.

    Returns:
        The XML document.
    """
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<resources>\n"
        f'    <color name="org_icontheme_icon_background_color">'
        f'{_xml_escape(theme.icon_background_color)}</color>\n'
        f'    <color name="org_icontheme_icon_color">'
        f"{_xml_escape(theme.icon_color)}</color>\n"
        "</resources>\n"
    )


def android_manifest_xml(theme: Theme) -> str:
    """Render ``app/src/main/AndroidManifest.xml``.

    Args:
        theme: Pack theme carrying the package id and name.

    Returns:
        The XML document.
    """
    lines = [_MANIFEST_HEAD.format(package=_xml_escape(theme.package))]
    lines.append('    <application')
    lines.append('        android:label="@string/app_name"')
    lines.append('        android:icon="@mipmap/ic_launcher"')
    lines.append('        android:roundIcon="@mipmap/ic_launcher_round"')
    lines.append('        android:allowBackup="false">')
    lines.append(_ACTIVITY_OPEN.rstrip("\n"))
    for action in _INTENT_ACTIONS:
        lines.append("        <intent-filter>")
        lines.append(f'            <action android:name="{action}" />')
        lines.append('            <category android:name="android.intent.category.DEFAULT" />')
        lines.append("        </intent-filter>")
    lines.append(_THEMED_ICON_META.rstrip("\n"))
    for name, value in _SMART_LAUNCHER_META:
        if value.startswith("@"):
            lines.append(f'        <meta-data android:name="{name}" android:resource="{value}" />')
        else:
            lines.append(f'        <meta-data android:name="{name}" android:value="{value}" />')
    lines.extend(("    </activity>", "    </application>", "</manifest>"))
    return "\n".join(lines) + "\n"


def manifest_json(entries: Sequence[IconSpec], layers: Sequence[IconLayers], theme: Theme) -> str:
    """Render the pack's own ``manifest.json`` inventory.

    This is the machine-readable half of the pack: every icon with its files,
    densities, sizes, category, tags, and status, so a pack can be inspected
    and diffed without opening a single PNG.

    Args:
        entries: Entries published.
        layers: Layer records, one per entry.
        theme: Pack theme.

    Returns:
        Deterministic JSON text with a trailing newline.
    """
    by_slug = {record.slug: record for record in layers}
    icons = []
    for spec in entries:
        record = by_slug[spec.slug]
        icons.append(
            {
                "adaptive_sizes": list(record.adaptive_sizes),
                "category": spec.category,
                "component": spec.component_info,
                "densities": list(record.densities),
                "drawable": record.drawable,
                "files": list(record.files),
                "keywords": list(spec.search_terms),
                "legacy_sizes": list(record.legacy_sizes),
                "master": record.master,
                "name": spec.name,
                "package": spec.package,
                "slug": spec.slug,
                "status": spec.status,
                "tags": list(spec.tags),
                "themed_drawable": record.themed_drawable,
            }
        )
    payload = {
        "generator": GENERATOR_NAME,
        "icon_count": len(entries),
        "icons": icons,
        "pack_categories": sorted({spec.category for spec in entries}),
        "pack_name": theme.name,
        "pack_version": theme.version,
        "play": {
            "feature_graphic": {"height": FEATURE_GRAPHIC_HEIGHT, "width": FEATURE_GRAPHIC_WIDTH},
            "icon": {"edge_px": PLAY_ICON_PX, "path": "store/play-icon.png"},
        },
        "protocol": {
            "appfilter": "res/xml/appfilter.xml",
            "drawable": "res/xml/drawable.xml",
            "grayscale_icon_map": "res/xml/grayscale_icon_map.xml",
            "intent_actions": list(_INTENT_ACTIONS),
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def store_listing_markdown(entries: Sequence[IconSpec], theme: Theme) -> str:
    """Render ``store-listing.md``: the Play copy an operator pastes.

    Args:
        entries: Entries published.
        theme: Pack theme.

    Returns:
        Markdown text.
    """
    categories = sorted({spec.category for spec in entries})
    keywords = sorted({token for spec in entries for token in spec.search_terms})[:40]
    lines = [
        f"# {theme.name}",
        "",
        f"Version {theme.version}. Generated by {GENERATOR_NAME}.",
        "",
        "## Title",
        "",
        f"{theme.name}",
        "",
        "## Short description",
        "",
        f"{theme.short_description}",
        "",
        f"({len(theme.short_description)} characters; Play limits this field to"
        f" {SHORT_DESCRIPTION_LIMIT}, with no emojis, line breaks, or call to action.)",
        "",
        "## Full description",
        "",
        f"{theme.name} is a complete adaptive icon pack for launchers that read",
        "the ADW, Nova, Smart Launcher, and Lawnchair icon-pack protocols.",
        "",
        f"- {len(entries)} icons across {len(categories)} categories.",
        "- Adaptive layers on the 108dp sheet with artwork inside the 66dp safe zone.",
        "- A monochrome layer for every icon, so themed icons work.",
        "- Legacy mipmap tiles at 48, 72, 96, 144, and 192 px.",
        "- Manual icon picker through ``drawable.xml``.",
        "- Fallback sheets for apps the pack does not map.",
        "",
        "Categories: " + ", ".join(categories) + ".",
        "",
        "## Category",
        "",
        f"{PACK_CATEGORY}",
        "",
        "## Keywords",
        "",
        ", ".join(keywords),
        "",
        "## Ads declaration",
        "",
        ADS_STATEMENT,
        "",
        "## Data safety",
        "",
        DATA_SAFETY_STATEMENT,
        "",
        "## Privacy policy",
        "",
        PRIVACY_STATEMENT,
        "",
    ]
    return "\n".join(lines)


def readme_markdown(theme: Theme) -> str:
    """Render ``README.md``: how to add or update one icon.

    Args:
        theme: Pack theme.

    Returns:
        Markdown text.
    """
    return (
        f"# {theme.name}\n"
        "\n"
        "Generated project. Do not edit the resources by hand; edit the catalog\n"
        "and rebuild.\n"
        "\n"
        "## Add one icon\n"
        "\n"
        f"1. Print a starter row for the app: run the scaffold of the {GENERATOR_NAME}\n"
        "   pack verb with the new slug, the neutral name, and the Android package.\n"
        "2. Append that row to your override file under ``icons``. The row merges\n"
        "   with the built-in catalog by slug, so reusing a slug updates an icon\n"
        "   in place.\n"
        "3. Pick a ``glyph`` from the recipe list, or leave the generated default.\n"
        "4. Optional: drop a master PNG named ``<slug>.png`` in your art directory.\n"
        "   It is fitted into the 66dp safe zone for you, so an oversized drop-in\n"
        "   cannot bleed.\n"
        "5. Rebuild the pack, then run the validator over the output. A clean run\n"
        "   means the monochrome layer, the density ladder, and the Play assets\n"
        "   all hold.\n"
        "\n"
        "## Update one icon\n"
        "\n"
        "Change the row (``status`` to ``redesign``, a new palette, a new glyph)\n"
        "and rebuild. Bytes that did not change stay byte-identical, so a diff of\n"
        "the output tree is the review.\n"
        "\n"
        "## Layout\n"
        "\n"
        "- ``app/src/main/AndroidManifest.xml`` - ADW, Nova, and Lawnchair filters.\n"
        "- ``app/src/main/res/xml/`` - ``appfilter.xml``, ``drawable.xml``,\n"
        "  ``grayscale_icon_map.xml``.\n"
        "- ``app/src/main/res/drawable-*dpi/`` - per-icon layers.\n"
        "- ``app/src/main/res/mipmap-*dpi/`` - the pack's own launcher icon.\n"
        "- ``app/src/main/res/mipmap-anydpi-v26/`` - adaptive icon XML.\n"
        "- ``store/`` - the Play icon and feature graphic.\n"
        f"- ``manifest.json`` - the machine-readable inventory.\n"
    )


def changelog_markdown(theme: Theme, previous: str = "") -> str:
    """Render ``CHANGELOG.md`` seeded with the pack version.

    Args:
        theme: Pack theme.
        previous: Prior version to list underneath, when there was one.

    Returns:
        Markdown text.
    """
    lines = [
        "# Changelog",
        "",
        f"## {theme.version}",
        "",
        f"- {theme.name} generated by {GENERATOR_NAME}.",
        "- Adaptive, legacy, and monochrome layer ladders for every entry.",
        "- ADW, Nova, Smart Launcher, and Lawnchair protocol files.",
        "- Play app icon and feature graphic.",
    ]
    if previous:
        lines.extend(("", f"## {previous}", "", "- Previous published pack."))
    return "\n".join(lines) + "\n"


def _fallback_sheet(name: str, accent: str) -> Canvas:
    """Render one ADW fallback sheet.

    Args:
        name: Sheet name, one of :data:`SHEET_NAMES`.
        accent: Hex field colour for ``iconback``.

    Returns:
        A 512 px sheet.
    """
    canvas = Canvas(SHEET_SIDE, SHEET_SIDE, TRANSPARENT)
    if name == "iconback":
        canvas.fill(hex_to_rgba(accent))
    elif name == "iconmask":
        canvas.fill(WHITE)
        canvas.fill_circle(SHEET_SIDE / 2.0, SHEET_SIDE / 2.0, SHEET_SIDE * 0.42, BLACK)
    elif name == "iconupon":
        canvas.fill_circle(SHEET_SIDE / 2.0, SHEET_SIDE / 2.0, SHEET_SIDE * 0.47, Rgba(255, 255, 255, 26))
        canvas.fill_circle(SHEET_SIDE / 2.0, SHEET_SIDE / 2.0, SHEET_SIDE * 0.44, TRANSPARENT)
    else:
        canvas.fill(Rgba(96, 104, 112, 255))
        quarter = SHEET_SIDE // 4
        canvas.draw_line(quarter, quarter, quarter * 3, quarter * 3, WHITE, SHEET_SIDE // 16)
        canvas.draw_line(quarter * 3, quarter, quarter, quarter * 3, WHITE, SHEET_SIDE // 16)
    return canvas


def build_pack(
    catalog: Sequence[IconSpec],
    out_dir: Path | str,
    only_slugs: Sequence[str] | None = None,
    categories: Sequence[str] | None = None,
    theme: Theme | None = None,
    dry_run: bool = False,
    art_dir: Path | str | None = None,
    round_variants: bool = True,
) -> PackResult:
    """Write a complete icon-pack Android project.

    Args:
        catalog: Entries to publish.
        out_dir: Project directory.
        only_slugs: When given, publish only these slugs in this order.
        categories: When given, publish only these categories.
        theme: Pack identity and colours; a fresh :class:`Theme` by default.
        dry_run: Report the file list and byte total without writing anything.
        art_dir: Directory of operator master art, named ``<slug>.png``.
        round_variants: Also write the round legacy launcher tiles.

    Returns:
        A :class:`PackResult` describing what was (or would be) written.

    Raises:
        ValueError: a requested slug is missing, the filters match nothing, or
            two entries collapse onto one drawable name.
    """
    active_theme = theme or Theme()
    entries = _apply_theme(select(catalog, only_slugs, categories), active_theme)
    _check_drawables(entries)
    root = Path(out_dir)
    res_dir = root / "app" / "src" / "main" / "res"
    art_root = Path(art_dir) if art_dir is not None else None
    written: list[tuple[str, int]] = []

    layers: list[IconLayers] = []
    for spec in entries:
        master = _master_path(spec, art_root)
        if dry_run:
            paths = icon_layer_paths(spec.drawable, "drawable", False, "_themed")
            layers.append(_dry_layers(spec, paths, master))
            written.extend((f"app/src/main/res/{name}", 0) for name in paths)
            continue
        record = write_icon_set(spec, res_dir, spec.drawable, "drawable", master, False, "_themed")
        layers.append(record)
        written.extend((f"app/src/main/res/{name}", _size(res_dir / name)) for name in record.files)

    if dry_run:
        launcher_paths = icon_layer_paths("ic_launcher", "mipmap", round_variants, "_monochrome")
        written.extend((f"app/src/main/res/{name}", 0) for name in launcher_paths)
        written.extend(
            (f"app/src/main/res/{name}", 0) for name in _launcher_xml_names(round_variants)
        )
        written.extend((f"app/src/main/res/{NODPI_DIR}/{name}.png", 0) for name in SHEET_NAMES)
        for name, text in _text_assets(entries, active_theme, layers):
            written.append((name, len(text.encode("utf-8"))))
        for name, text in _document_assets(entries, active_theme):
            written.append((name, len(text.encode("utf-8"))))
        written.append(("store/play-icon.png", 0))
        written.append(("store/feature-graphic.png", 0))
        return PackResult(
            out_dir=str(root),
            pack_name=active_theme.name,
            pack_version=active_theme.version,
            icon_count=len(entries),
            files=tuple(sorted(name for name, _ in written)),
            total_bytes=sum(size for _, size in written),
            dry_run=True,
        )

    launcher_spec = entries[0]
    launcher = write_launcher_icon_set(launcher_spec, res_dir, None, round_variants)
    written.extend((f"app/src/main/res/{name}", _size(res_dir / name)) for name in launcher.files)
    for name in write_launcher_xml(res_dir, round_variants):
        written.append((f"app/src/main/res/{name}", _size(res_dir / name)))
    for name in _write_fallback_sheets(res_dir, active_theme):
        written.append((f"app/src/main/res/{name}", _size(res_dir / name)))
    for name, text in _text_assets(entries, active_theme, layers):
        _write_text(root / name, text)
        written.append((name, len(text.encode("utf-8"))))
    written.append(("store/play-icon.png", write_play_icon(launcher_spec, root / "store" / "play-icon.png")))
    feature = write_feature_graphic(
        entries, root / "store" / "feature-graphic.png", active_theme.accent
    )
    written.append(("store/feature-graphic.png", feature))
    for name, text in _document_assets(entries, active_theme):
        _write_text(root / name, text)
        written.append((name, len(text.encode("utf-8"))))
    return PackResult(
        out_dir=str(root),
        pack_name=active_theme.name,
        pack_version=active_theme.version,
        icon_count=len(entries),
        files=tuple(sorted(name for name, _ in written)),
        total_bytes=sum(size for _, size in written),
        dry_run=False,
    )


def _dry_layers(spec: IconSpec, paths: tuple[str, ...], master: str | None) -> IconLayers:
    """Build the layer record a dry run reports.

    Args:
        spec: Entry being reported.
        paths: Res-relative paths the writer would produce.
        master: Master art path, when one exists.

    Returns:
        The record ``manifest.json`` would carry for this entry.
    """
    return IconLayers(
        slug=spec.slug,
        drawable=spec.drawable,
        themed_drawable=spec.themed_drawable,
        files=paths,
        densities=tuple(name for name, _ in ADAPTIVE_LADDER),
        adaptive_sizes=tuple(edge for _, edge in ADAPTIVE_LADDER),
        legacy_sizes=tuple(edge for _, edge in LEGACY_LADDER),
        master=master,
    )


def _check_drawables(entries: Sequence[IconSpec]) -> None:
    """Reject entries that would publish under one resource name.

    The launcher tile and its themed layer share the drawable namespace, so
    ``star`` and ``star-themed`` collide even though their slugs differ.

    Args:
        entries: Entries about to be built.

    Raises:
        ValueError: two slugs collapse onto the same resource name.
    """
    seen: dict[str, str] = {}
    for spec in entries:
        for name in (spec.drawable, spec.themed_drawable):
            if name in seen:
                raise ValueError(
                    f"drawable collision: {seen[name]!r} and {spec.slug!r}"
                    f" both map to {name!r}"
                )
            seen[name] = spec.slug


def _master_path(spec: IconSpec, art_root: Path | None) -> str | None:
    """Find operator master art for one entry.

    Args:
        spec: Entry to look up.
        art_root: Art directory, or None when the operator passed none.

    Returns:
        Path text when a PNG exists for the slug, else None.
    """
    if art_root is None:
        return None
    for suffix in (".png", ".webp", ".jpg"):
        candidate = art_root / f"{spec.slug}{suffix}"
        if candidate.is_file():
            return str(candidate)
    return None


def _text_assets(
    entries: Sequence[IconSpec], theme: Theme, layers: Sequence[IconLayers]
) -> tuple[tuple[str, str], ...]:
    """Every XML and JSON text asset of the project.

    Args:
        entries: Entries published.
        theme: Pack theme.
        layers: Layer records, one per entry.

    Returns:
        ``(project-relative path, text)`` pairs, sorted by path.
    """
    assets = {
        "app/src/main/AndroidManifest.xml": android_manifest_xml(theme),
        "app/src/main/assets/appfilter.xml": appfilter_xml(entries, theme.name),
        "app/src/main/res/values/colors.xml": colors_xml(theme),
        "app/src/main/res/values/strings.xml": strings_xml(entries, theme),
        "app/src/main/res/xml/appfilter.xml": appfilter_xml(entries, theme.name),
        "app/src/main/res/xml/drawable.xml": drawable_xml(entries, theme.name),
        "app/src/main/res/xml/grayscale_icon_map.xml": grayscale_icon_map_xml(entries, theme.name),
        "manifest.json": manifest_json(entries, layers, theme),
    }
    return tuple(sorted(assets.items()))


def _document_assets(entries: Sequence[IconSpec], theme: Theme) -> tuple[tuple[str, str], ...]:
    """The operator-facing prose assets of the project.

    Args:
        entries: Entries published.
        theme: Pack theme.

    Returns:
        ``(project-relative path, text)`` pairs, sorted by path.
    """
    assets = {
        "CHANGELOG.md": changelog_markdown(theme),
        "README.md": readme_markdown(theme),
        "store-listing.md": store_listing_markdown(entries, theme),
    }
    return tuple(sorted(assets.items()))


def _write_fallback_sheets(res_dir: Path, theme: Theme) -> tuple[str, ...]:
    """Write the four ADW fallback sheets.

    Args:
        res_dir: The ``app/src/main/res`` directory.
        theme: Pack theme carrying the field colour.

    Returns:
        Written paths relative to ``res_dir``, sorted.
    """
    folder = res_dir / NODPI_DIR
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for name in SHEET_NAMES:
        canvas = _fallback_sheet(name, theme.accent)
        canvas.write_png(str(folder / f"{name}.png"))
        written.append(f"{NODPI_DIR}/{name}.png")
    return tuple(sorted(written))


def _write_text(path: Path, text: str) -> None:
    """Write a text asset, creating parents.

    Args:
        path: Destination file.
        text: Document body.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _size(path: Path) -> int:
    """Byte size of a file just written.

    Args:
        path: File on disk.

    Returns:
        Size in bytes.
    """
    return path.stat().st_size


def _launcher_xml_names(round_variants: bool) -> tuple[str, ...]:
    """Adaptive XML names a dry run reports.

    Args:
        round_variants: Whether the round variant is written too.

    Returns:
        Names relative to ``res``.
    """
    names = ["mipmap-anydpi-v26/ic_launcher.xml"]
    if round_variants:
        names.append("mipmap-anydpi-v26/ic_launcher_round.xml")
    return tuple(names)


def _print_findings(findings: Sequence[Finding]) -> int:
    """Print validator findings the way an operator wants to read them.

    Args:
        findings: Findings to report.

    Returns:
        Number of error-severity findings.
    """
    errors = 0
    for finding in findings:
        if finding.severity == "error":
            errors += 1
        print(f"{finding.severity}: {finding.code}: {finding.path}: {finding.message}")
    if not findings:
        print("clean: no findings")
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry for the pack verb.

    Args:
        argv: Arguments after the program name; ``sys.argv[1:]`` by default.

    Returns:
        Process exit code: 0 on success, 1 when validation reports an error.
    """
    parser = argparse.ArgumentParser(
        prog="ez_icons.pack",
        description="Build a sellable Android adaptive icon pack from the catalog.",
    )
    parser.add_argument("--out", default="out/icon-pack", help="Project directory to write.")
    parser.add_argument("--catalog", default="", help="Operator JSON override file.")
    parser.add_argument(
        "--icon", action="append", default=[], help="Publish only this slug (repeatable)."
    )
    parser.add_argument(
        "--category", action="append", default=[], help="Publish only this category (repeatable)."
    )
    parser.add_argument("--art-dir", default="", help="Directory of <slug>.png master art.")
    parser.add_argument("--pack-name", default="", help="Pack name for the listing and strings.")
    parser.add_argument("--pack-version", default="", help="Pack version for the manifest.")
    parser.add_argument("--validate-only", action="store_true", help="Validate a built pack only.")
    parser.add_argument("--scaffold", default="", help="Print an override row for a new slug.")
    parser.add_argument("--dry-run", action="store_true", help="Report the file list, write nothing.")
    parser.add_argument("--name", default="", help="Neutral label for --scaffold.")
    parser.add_argument("--package", dest="package_id", default="", help="Package for --scaffold.")
    parser.add_argument("--glyph", default="disc", help="Recipe id for --scaffold.")
    args = parser.parse_args(argv)

    if args.scaffold:
        print(
            new_icon_scaffold(
                slug=args.scaffold,
                name=args.name or args.scaffold.replace("-", " ").title(),
                package=args.package_id,
                glyph=args.glyph,
                category=(args.category or ["utilities"])[0],
            )
        )
        return 0

    if args.validate_only:
        catalog = load_catalog(args.catalog) if args.catalog else ICON_CATALOG
        errors = _print_findings(validate_catalog(catalog))
        errors += _print_findings(validate_pack(args.out))
        return 1 if errors else 0

    try:
        catalog = load_catalog(args.catalog) if args.catalog else ICON_CATALOG
        theme = Theme(
            name=args.pack_name or DEFAULT_PACK_NAME,
            version=args.pack_version or DEFAULT_PACK_VERSION,
        )
        result = build_pack(
            catalog,
            args.out,
            only_slugs=args.icon or None,
            categories=args.category or None,
            theme=theme,
            dry_run=args.dry_run,
            art_dir=args.art_dir or None,
        )
    except (ValueError, OSError) as exc:
        print(f"error: {exc}")
        return 2
    verb = "would write" if result.dry_run else "wrote"
    print(f"{verb} {result.icon_count} icons, {len(result.files)} files")
    print(f"pack: {result.pack_name} {result.pack_version} at {result.out_dir}")
    print(f"bytes: {result.total_bytes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

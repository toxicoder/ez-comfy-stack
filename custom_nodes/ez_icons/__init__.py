"""ez-comfy generated Android icon pack (adaptive, themed, Play-ready).

No nodes: this is a library and an operator CLI, so nothing here touches
Comfy. Import is hermetic - stdlib plus :mod:`ez_raster` and
:mod:`ez_common.json_value`, no Pillow, no numpy - and every pixel is
drawn from primitives, so a build needs no model and no assets on disk.

Add an app by editing catalog JSON, never Python: the scaffold verb prints
a ready-to-paste row (:func:`new_icon_scaffold`) and the loader merges an
operator file back over the built-ins by slug (:func:`load_catalog`). The
exporter stays a submodule (:mod:`ez_icons.pack`) so running it as a module
needs no package import.

The numbers here come from the verified launcher/Play digest: a 108 dp
adaptive sheet, a 66 dp artwork ceiling with 48 dp as the floor, the five
mipmap buckets, a 512x512 Play icon under 1024 KB, and a 1024x500 feature
graphic with no alpha.
"""

from __future__ import annotations

from .adaptive import (
    ADAPTIVE_LADDER,
    FEATURE_GRAPHIC_HEIGHT,
    FEATURE_GRAPHIC_WIDTH,
    LEGACY_LADDER,
    PLAY_ICON_MAX_BYTES,
    PLAY_ICON_PX,
    IconLayers,
    adaptive_icon_xml,
    feature_graphic,
    play_icon_canvas,
    write_feature_graphic,
    write_icon_set,
    write_launcher_icon_set,
    write_launcher_xml,
    write_play_icon,
)
from .catalog import (
    BACKGROUND_STYLES,
    ICON_CATALOG,
    ICON_STATUSES,
    Background,
    IconSpec,
    IconStatus,
    by_slug,
    categories,
    glyph_names,
    icons_for,
    load_catalog,
    new_icon_scaffold,
    parse_background,
    select,
    write_catalog_template,
)
from .glyphs import (
    ARTWORK_MAX_DP,
    ARTWORK_MIN_DP,
    ARTWORK_TARGET_DP,
    SAFE_ZONE_RATIO,
    artwork_bounds,
    colors_for,
    fit_to_safe_zone,
    glyph_recipes,
    render_background,
    render_foreground,
    render_legacy,
    render_monochrome,
)
from .validate import FINDING_CODES, Finding, suspect_brand, validate_catalog, validate_pack

__all__ = [
    "ADAPTIVE_LADDER",
    "ARTWORK_MAX_DP",
    "ARTWORK_MIN_DP",
    "ARTWORK_TARGET_DP",
    "BACKGROUND_STYLES",
    "FINDING_CODES",
    "FEATURE_GRAPHIC_HEIGHT",
    "FEATURE_GRAPHIC_WIDTH",
    "ICON_CATALOG",
    "ICON_STATUSES",
    "LEGACY_LADDER",
    "PLAY_ICON_MAX_BYTES",
    "PLAY_ICON_PX",
    "SAFE_ZONE_RATIO",
    "Background",
    "Finding",
    "IconLayers",
    "IconSpec",
    "IconStatus",
    "adaptive_icon_xml",
    "artwork_bounds",
    "by_slug",
    "categories",
    "colors_for",
    "feature_graphic",
    "fit_to_safe_zone",
    "glyph_names",
    "glyph_recipes",
    "icons_for",
    "load_catalog",
    "new_icon_scaffold",
    "parse_background",
    "play_icon_canvas",
    "render_background",
    "render_foreground",
    "render_legacy",
    "render_monochrome",
    "select",
    "suspect_brand",
    "validate_catalog",
    "validate_pack",
    "write_catalog_template",
    "write_feature_graphic",
    "write_icon_set",
    "write_launcher_icon_set",
    "write_launcher_xml",
    "write_play_icon",
]

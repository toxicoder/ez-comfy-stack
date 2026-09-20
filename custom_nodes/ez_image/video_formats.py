"""Wan / LTX clip canvas catalog: Spark-safe aspect and platform presets.

Hermetic stdlib. JSON lives under ``js/video_formats.json`` so the frontend
can fetch the same file from WEB_DIRECTORY. Length is not in this catalog —
graphs keep authored frame counts (121 smoke, 49 GIF, 120 shot).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .formats import (
    CUSTOM_ID,
    CUSTOM_LABEL,
    SIZE_MODE_MATCH,
    _as_int,
    _as_str,
    image_hw,
    is_match_input,
)

# Catalog path, family ids/labels, default family for INPUT_TYPES.
VIDEO_FORMATS_PATH = Path(__file__).resolve().parent / "js" / "video_formats.json"
FAMILY_WAN = "wan"
FAMILY_LTX = "ltx"
FAMILY_WAN_LABEL = "Wan 5B"
FAMILY_LTX_LABEL = "LTX-2.5"
DEFAULT_FAMILY = FAMILY_WAN
DURATION_CHOICES = ("5 seconds", "8 seconds", "10 seconds", "12 seconds")
DURATION_DEFAULT = "10 seconds"
DURATION_SECONDS = {
    "5 seconds": 5.00,
    "8 seconds": 8.00,
    "10 seconds": 10.00,
    "12 seconds": 12.00,
}


@dataclass(frozen=True)
class FamilySpec:
    """One video family (Wan 5B or LTX-2.5).

    Attributes:
        id: ``wan`` or ``ltx``.
        label: Combo value shown in the graph.
        grid: VAE spatial multiple (16 or 32).
        min_dim: Smallest legal side.
        max_dim: Largest legal side (Spark-safe).
        default_id: Default format id for this family.
        custom_prefix: Save / VHS prefix for Custom.
        custom_width: Default Custom width.
        custom_height: Default Custom height.
    """

    id: str
    label: str
    grid: int
    min_dim: int
    max_dim: int
    default_id: str
    custom_prefix: str
    custom_width: int
    custom_height: int


@dataclass(frozen=True)
class VideoFormatSpec:
    """One clip canvas preset.

    Attributes:
        id: Stable snake_case id.
        label: Combo value shown in the App.
        family: ``wan``, ``ltx``, or empty for Custom.
        group: Catalog section.
        width: Latent width, or 0 for Custom.
        height: Latent height, or 0 for Custom.
        prefix: Optional filename prefix.
        hint: Enhance duration_hint framing line.
        lock: Job-specific safe-area clause.
    """

    id: str
    label: str
    family: str
    group: str
    width: int
    height: int
    prefix: str
    hint: str
    lock: str


@dataclass(frozen=True)
class VideoFormatResult:
    """Resolved clip canvas for one Queue.

    Attributes:
        width: Snapped latent width.
        height: Snapped latent height.
        hint: Enhance framing string (hint + lock).
        prefix: Filename prefix.
        format_id: Catalog id used.
        label: Combo label used.
        family: Family id used for snap.
    """

    width: int
    height: int
    hint: str
    prefix: str
    format_id: str
    label: str
    family: str


def clamp_video_dim(n: int, *, grid: int, min_dim: int, max_dim: int) -> int:
    """Snap to ``grid`` and clamp to ``min_dim``…``max_dim``.

    Args:
        n: Requested pixel count.
        grid: VAE multiple.
        min_dim: Inclusive lower bound (already on-grid).
        max_dim: Inclusive upper bound.

    Returns:
        Legal latent dimension.
    """
    step = max(int(grid), 1)
    low = max(int(min_dim), step)
    high = max(int(max_dim), low)
    value = int(n)
    if value < low:
        snapped = low
    else:
        snapped = (value // step) * step
        if snapped < low:
            snapped = low
    if snapped > high:
        return (high // step) * step
    return snapped


@lru_cache(maxsize=1)
def load_families() -> dict[str, FamilySpec]:
    """Load Wan / LTX family rows.

    Returns:
        Family id → spec.

    Raises:
        ValueError: catalog missing or malformed.
    """
    raw = _load_payload()
    rows = raw.get("families")
    if not isinstance(rows, dict) or not rows:
        raise ValueError("video_formats.json families must be a nonempty object")
    out: dict[str, FamilySpec] = {}
    for key, item in rows.items():
        if not isinstance(item, dict):
            raise ValueError("video_formats.json family rows must be objects")
        fid = str(key).strip()
        spec = FamilySpec(
            id=fid,
            label=str(item.get("label") or "").strip(),
            grid=int(item.get("grid") or 0),
            min_dim=int(item.get("min") or 0),
            max_dim=int(item.get("max") or 0),
            default_id=str(item.get("default_id") or "").strip(),
            custom_prefix=str(item.get("custom_prefix") or "").strip(),
            custom_width=int(item.get("custom_width") or 0),
            custom_height=int(item.get("custom_height") or 0),
        )
        if not spec.id or not spec.label or spec.grid < 1:
            raise ValueError("video family needs id, label, and grid")
        out[spec.id] = spec
    if FAMILY_WAN not in out or FAMILY_LTX not in out:
        raise ValueError("video_formats.json needs wan and ltx families")
    return out


@lru_cache(maxsize=1)
def load_video_formats() -> tuple[VideoFormatSpec, ...]:
    """Load clip presets in file order.

    Returns:
        Format rows (Custom first in the JSON file).

    Raises:
        ValueError: catalog missing or malformed.
    """
    raw = _load_payload()
    rows = raw.get("formats")
    if not isinstance(rows, list) or not rows:
        raise ValueError("video_formats.json formats must be a nonempty list")
    out: list[VideoFormatSpec] = []
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError("video_formats.json entries must be objects")
        spec = VideoFormatSpec(
            id=str(item.get("id") or "").strip(),
            label=str(item.get("label") or "").strip(),
            family=str(item.get("family") or "").strip(),
            group=str(item.get("group") or "").strip(),
            width=int(item.get("width") or 0),
            height=int(item.get("height") or 0),
            prefix=str(item.get("prefix") or "").strip(),
            hint=str(item.get("hint") or "").strip(),
            lock=str(item.get("lock") or "").strip(),
        )
        if not spec.id or not spec.label:
            raise ValueError("video format row needs id and label")
        out.append(spec)
    return tuple(out)


def _load_payload() -> dict[str, Any]:
    """Read and parse the video catalog object.

    Returns:
        Parsed JSON object.

    Raises:
        ValueError: missing file or non-object JSON.
    """
    if not VIDEO_FORMATS_PATH.is_file():
        raise ValueError(f"missing video format catalog {VIDEO_FORMATS_PATH}")
    raw = json.loads(VIDEO_FORMATS_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("video_formats.json must be an object")
    return raw


def family_combo_labels() -> list[str]:
    """Combo choices for the family widget.

    Returns:
        Wan then LTX labels.
    """
    families = load_families()
    return [families[FAMILY_WAN].label, families[FAMILY_LTX].label]


def video_format_combo_labels() -> list[str]:
    """All format labels in file order (Python INPUT_TYPES union).

    Returns:
        Label strings.
    """
    return [row.label for row in load_video_formats()]


def family_format_labels(family: object) -> list[str]:
    """Format labels visible for one family (Custom + that family's rows).

    Args:
        family: Family id or label.

    Returns:
        Label strings.
    """
    fid = resolve_family(family)
    labels: list[str] = []
    for row in load_video_formats():
        if row.id == CUSTOM_ID or row.family == fid:
            labels.append(row.label)
    return labels


def resolve_family(value: object) -> str:
    """Resolve a family combo to ``wan`` or ``ltx``.

    Args:
        value: Family id or label.

    Returns:
        Family id. Unknown values become ``wan``.
    """
    raw = _as_str(value)
    families = load_families()
    if raw in families:
        return raw
    folded = raw.casefold()
    for fid, spec in families.items():
        if spec.label.casefold() == folded:
            return fid
    return DEFAULT_FAMILY


def get_family(value: object) -> FamilySpec:
    """Return the family spec for a combo value.

    Args:
        value: Family id or label.

    Returns:
        Family row.
    """
    return load_families()[resolve_family(value)]


def default_video_format_id(family: object = DEFAULT_FAMILY) -> str:
    """Default format id for a family.

    Args:
        family: Family id or label.

    Returns:
        Format id.
    """
    spec = get_family(family)
    if spec.default_id:
        return spec.default_id
    for row in load_video_formats():
        if row.family == spec.id:
            return row.id
    return CUSTOM_ID


def default_video_format_label(family: object = DEFAULT_FAMILY) -> str:
    """Default format label for a family.

    Args:
        family: Family id or label.

    Returns:
        Combo label.
    """
    wanted = default_video_format_id(family)
    for row in load_video_formats():
        if row.id == wanted:
            return row.label
    labels = family_format_labels(family)
    return labels[0] if labels else CUSTOM_LABEL


def get_video_format(value: object, *, family: object = DEFAULT_FAMILY) -> VideoFormatSpec:
    """Resolve a combo value to a catalog row for ``family``.

    Args:
        value: Format id or label.
        family: Family id or label (Custom snap + mismatch fallback).

    Returns:
        Matching spec in this family, Custom, or the family default when the
        value belongs to the other family or is unknown.
    """
    fid = resolve_family(family)
    rows = load_video_formats()
    by_id = {row.id: row for row in rows}
    raw = _as_str(value)
    folded = raw.casefold()
    if not raw or folded in {CUSTOM_ID, CUSTOM_LABEL.casefold()}:
        return by_id[CUSTOM_ID]
    match: VideoFormatSpec | None = None
    if raw in by_id:
        match = by_id[raw]
    else:
        for row in rows:
            if row.label.casefold() == folded:
                match = row
                break
    if match is None:
        return by_id.get(default_video_format_id(fid), by_id[CUSTOM_ID])
    if match.family and match.family != fid:
        return by_id.get(default_video_format_id(fid), by_id[CUSTOM_ID])
    return match


def _compose_hint(spec: VideoFormatSpec, width: int, height: int) -> str:
    """Build the Enhance duration_hint from a spec and resolved size.

    Args:
        spec: Catalog row.
        width: Resolved width.
        height: Resolved height.

    Returns:
        Hint plus lock, joined with a period.
    """
    hint = spec.hint.strip()
    if spec.id == CUSTOM_ID:
        hint = f"Custom clip {width}×{height}"
    lock = spec.lock.strip()
    parts = [part for part in (hint, lock) if part]
    return ". ".join(parts)


def nearest_video_format(
    src_w: int, src_h: int, current: VideoFormatSpec, family: str
) -> VideoFormatSpec:
    """Pick the family aspect row closest to the source ratio.

    Args:
        src_w: Source width.
        src_h: Source height.
        current: Format already resolved from the combo.
        family: ``wan`` or ``ltx``.

    Returns:
        Nearest non-custom spec for ``family``.
    """
    rows = [
        row
        for row in load_video_formats()
        if row.family == family and row.width > 0 and row.height > 0
    ]
    if not rows:
        return current
    src_ratio = float(src_w) / float(max(src_h, 1))
    current_area = max(int(current.width) * int(current.height), 1)
    ranked: list[tuple[tuple[float, float], VideoFormatSpec]] = []
    for row in rows:
        ratio_err = abs(float(row.width) / float(max(row.height, 1)) - src_ratio)
        area_err = abs(row.width * row.height - current_area) / float(current_area)
        ranked.append(((ratio_err, area_err), row))
    ranked.sort(key=lambda item: item[0])
    return ranked[0][1]


def resolve_video_canvas(
    family: object,
    format_value: object,
    *,
    width: object = 0,
    height: object = 0,
    size_mode: object = SIZE_MODE_MATCH,
    image: object = None,
) -> VideoFormatResult:
    """Resolve widgets to a Queue clip canvas.

    Args:
        family: Family combo (id or label).
        format_value: Format combo (id or label).
        width: Custom width widget (used when format is Custom).
        height: Custom height widget.
        size_mode: Match input or Force format.
        image: Optional IMAGE tensor used when matching input ratio.

    Returns:
        Snapped canvas, hint, and prefix.
    """
    family_spec = get_family(family)
    spec = get_video_format(format_value, family=family_spec.id)
    hw = image_hw(image)
    if is_match_input(size_mode) and hw is not None:
        spec = nearest_video_format(hw[0], hw[1], spec, family_spec.id)
    if spec.id == CUSTOM_ID:
        resolved_w = clamp_video_dim(
            _as_int(width, family_spec.custom_width),
            grid=family_spec.grid,
            min_dim=family_spec.min_dim,
            max_dim=family_spec.max_dim,
        )
        resolved_h = clamp_video_dim(
            _as_int(height, family_spec.custom_height),
            grid=family_spec.grid,
            min_dim=family_spec.min_dim,
            max_dim=family_spec.max_dim,
        )
        prefix = family_spec.custom_prefix
    else:
        resolved_w = clamp_video_dim(
            spec.width,
            grid=family_spec.grid,
            min_dim=family_spec.min_dim,
            max_dim=family_spec.max_dim,
        )
        resolved_h = clamp_video_dim(
            spec.height,
            grid=family_spec.grid,
            min_dim=family_spec.min_dim,
            max_dim=family_spec.max_dim,
        )
        prefix = spec.prefix or family_spec.custom_prefix
    return VideoFormatResult(
        width=resolved_w,
        height=resolved_h,
        hint=_compose_hint(spec, resolved_w, resolved_h),
        prefix=prefix,
        format_id=spec.id,
        label=spec.label,
        family=family_spec.id,
    )


def catalog_payload() -> dict[str, Any]:
    """Return the raw JSON object (docs / tests).

    Returns:
        Parsed video_formats.json mapping.
    """
    return _load_payload()


def reset_video_format_cache_for_tests() -> None:
    """Drop loaded families and formats so tests can swap files."""
    load_families.cache_clear()
    load_video_formats.cache_clear()

"""List, resolve, delete, and copy durable Comfy generation files.

Hermetic: stdlib only. Comfy ``folder_paths`` is optional. Never walks
``MODELS_DIR``. Skip Comfy user trees that share the output bind.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import TypedDict

LIST_CAP = 500
"""Newest-first cap for :func:`list_outputs`."""

SKIP_DIR_NAMES = frozenset(
    {
        "comfy-user",
        "custom-nodes-user",
        "input",
        "temp",
    }
)
"""Directory names that are never listed or deleted."""

IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})
"""Still suffixes listed in the Outputs sidebar."""

VIDEO_SUFFIXES = frozenset({".mp4", ".webm", ".mkv"})
"""Video suffixes listed in the Outputs sidebar."""

AUDIO_SUFFIXES = frozenset({".wav", ".flac", ".mp3", ".m4a", ".ogg"})
"""Audio suffixes listed in the Outputs sidebar."""

MEDIA_SUFFIXES = IMAGE_SUFFIXES | VIDEO_SUFFIXES | AUDIO_SUFFIXES
"""Union of still, video, and audio suffixes."""


class OutputRow(TypedDict):
    """One media file under the output root.

    Attributes:
        rel: Path relative to the output root using ``/``.
        name: File name.
        kind: ``image``, ``video``, or ``audio``.
        size: Byte length.
        mtime: Unix mtime (seconds).
        suffix: Lowercase suffix including the dot.
        parent: Parent directory relative to the root, or ``""`` at root.
    """

    rel: str
    name: str
    kind: str
    size: int
    mtime: float
    suffix: str
    parent: str


class BatchError(TypedDict):
    """One refused path in a bulk delete or copy.

    Attributes:
        rel: Relative path that failed.
        error: Operator-facing reason.
    """

    rel: str
    error: str


class CopyRow(TypedDict):
    """One successful copy into the LoadImage input directory.

    Attributes:
        rel: Source path relative to the output root.
        name: Destination file name (LoadImage combo value).
    """

    rel: str
    name: str


class CatalogError(ValueError):
    """Operator-facing refuse (traversal, skip dir, non-media)."""


def output_directory() -> Path:
    """Operator output dir: folder_paths, then ``/outputs``, then env.

    Returns:
        Directory path (may not exist yet).
    """
    try:
        from ez_common import output_root

        return output_root(default="/outputs")
    except Exception:  # noqa: BLE001 - Comfy optional in unit tests
        env = (os.environ.get("COMFY_OUTPUT_DIR") or "").strip()
        if env:
            return Path(env)
        try:
            import folder_paths  # type: ignore[import-not-found]

            return Path(folder_paths.get_output_directory())
        except Exception:  # noqa: BLE001 - Comfy optional in unit tests
            return Path("/outputs")


def input_root(*, default: Path | None = None) -> Path:
    """Resolve the LoadImage input directory.

    Args:
        default: Fallback when Comfy and ``<output>/input`` are unset.

    Returns:
        Input directory (may not exist yet).
    """
    try:
        import folder_paths  # type: ignore[import-not-found]

        raw = folder_paths.get_input_directory()
        if raw:
            return Path(raw)
    except Exception:  # noqa: BLE001 - Comfy optional in unit tests
        pass
    if default is not None:
        return Path(default)
    return output_directory() / "input"


def kind_of(suffix: str) -> str | None:
    """Return ``image`` / ``video`` / ``audio`` for a media suffix.

    Args:
        suffix: File suffix including the dot.

    Returns:
        Kind token, or ``None`` when the suffix is not media.
    """
    text = suffix.lower()
    if text in IMAGE_SUFFIXES:
        return "image"
    if text in VIDEO_SUFFIXES:
        return "video"
    if text in AUDIO_SUFFIXES:
        return "audio"
    return None


def _skip_parts(path: Path, root: Path) -> bool:
    """True when ``path`` sits under a skipped directory name.

    Args:
        path: Candidate file path.
        root: Output root.

    Returns:
        True when the relative parts include a skip name or a dot-dir.
    """
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return True
    return any(part in SKIP_DIR_NAMES or part.startswith(".") for part in rel.parts)


def list_outputs(
    root: Path,
    *,
    kind: str = "all",
    query: str = "",
    limit: int = LIST_CAP,
) -> list[OutputRow]:
    """Return newest media files under ``root``.

    Args:
        root: Output directory (``COMFY_OUTPUT_DIR`` / ``/outputs``).
        kind: ``all``, ``image``, ``video``, or ``audio``.
        query: Case-insensitive substring on the relative path.
        limit: Max rows; values below 1 clamp to 1.

    Returns:
        Rows sorted by mtime descending.
    """
    cap = int(limit) if limit else LIST_CAP
    if cap < 1:
        cap = 1
    want = (kind or "all").strip().lower()
    needle = (query or "").strip().lower()
    base = Path(root)
    if not base.is_dir():
        return []
    rows: list[OutputRow] = []
    for path in base.rglob("*"):
        try:
            is_file = path.is_file()
        except OSError:
            continue
        if not is_file:
            continue
        if _skip_parts(path, base):
            continue
        suffix = path.suffix.lower()
        media_kind = kind_of(suffix)
        if media_kind is None:
            continue
        if want != "all" and media_kind != want:
            continue
        rel_path = path.resolve().relative_to(base.resolve())
        rel = rel_path.as_posix()
        if needle and needle not in rel.lower():
            continue
        parent = rel_path.parent.as_posix()
        if parent == ".":
            parent = ""
        try:
            stat = path.stat()
        except OSError:
            continue
        rows.append(
            {
                "rel": rel,
                "name": path.name,
                "kind": media_kind,
                "size": int(stat.st_size),
                "mtime": float(stat.st_mtime),
                "suffix": suffix,
                "parent": parent,
            }
        )
    rows.sort(key=lambda row: row["mtime"], reverse=True)
    return rows[:cap]


def resolve_under(root: Path, rel: str) -> Path:
    """Return a media file under ``root``, or raise :class:`CatalogError`.

    Args:
        root: Output directory.
        rel: Relative path using ``/`` or the OS separator.

    Returns:
        Resolved file path.

    Raises:
        CatalogError: traversal, skip dir, missing file, or non-media.
    """
    base = Path(root).resolve()
    text = str(rel or "").replace("\\", "/").strip().lstrip("/")
    if not text or text in {".", ".."} or ".." in Path(text).parts:
        raise CatalogError("invalid output path")
    path = (base / text).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise CatalogError("path escapes output root") from exc
    if _skip_parts(path, base):
        raise CatalogError("refusing skipped directory")
    if not path.is_file():
        raise CatalogError("missing output file")
    if kind_of(path.suffix) is None:
        raise CatalogError("not a media file")
    return path


def bounded_rels(rels: list[str]) -> list[str]:
    """Return a non-empty, de-duplicated, cap-sliced list of relative paths.

    Args:
        rels: Candidate relative paths.

    Returns:
        Cleaned paths in first-seen order, at most :data:`LIST_CAP`.

    Raises:
        CatalogError: when no usable path remains.
    """
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in rels:
        text = str(raw or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
        if len(cleaned) >= LIST_CAP:
            break
    if not cleaned:
        raise CatalogError("invalid output path")
    return cleaned


def delete_output(root: Path, rel: str) -> Path:
    """Unlink one media file under ``root``.

    Args:
        root: Output directory.
        rel: Relative path.

    Returns:
        The path that was removed.

    Raises:
        CatalogError: same refuses as :func:`resolve_under`.
    """
    path = resolve_under(root, rel)
    path.unlink()
    return path


def delete_many(root: Path, rels: list[str]) -> tuple[list[str], list[BatchError]]:
    """Delete many media files under ``root``.

    Each path still goes through :func:`resolve_under`. One refuse does not
    abort the rest of the batch.

    Args:
        root: Output directory.
        rels: Relative paths.

    Returns:
        ``(deleted, errors)`` where errors are ``{rel, error}``.

    Raises:
        CatalogError: when ``rels`` is empty after cleaning.
    """
    deleted: list[str] = []
    errors: list[BatchError] = []
    for rel in bounded_rels(rels):
        try:
            delete_output(root, rel)
        except CatalogError as exc:
            errors.append({"rel": rel, "error": str(exc)})
            continue
        deleted.append(rel)
    return deleted, errors


def copy_to_input(
    output_dir: Path,
    rel: str,
    *,
    input_dir: Path | None = None,
) -> Path:
    """Copy a media file into the LoadImage input directory.

    Args:
        output_dir: Output root.
        rel: Relative path under ``output_dir``.
        input_dir: Destination directory; default :func:`input_root`.

    Returns:
        Destination path.

    Raises:
        CatalogError: same refuses as :func:`resolve_under`.
    """
    src = resolve_under(output_dir, rel)
    dest_dir = Path(input_dir) if input_dir is not None else input_root()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    return dest


def copy_many_to_input(
    output_dir: Path,
    rels: list[str],
    *,
    input_dir: Path | None = None,
) -> tuple[list[CopyRow], list[BatchError]]:
    """Copy many media files into the LoadImage input directory.

    Args:
        output_dir: Output root.
        rels: Relative paths under ``output_dir``.
        input_dir: Destination directory; default :func:`input_root`.

    Returns:
        ``(copied, errors)`` where copied rows have ``rel`` and ``name``.

    Raises:
        CatalogError: when ``rels`` is empty after cleaning.
    """
    copied: list[CopyRow] = []
    errors: list[BatchError] = []
    dest_root = Path(input_dir) if input_dir is not None else input_root()
    for rel in bounded_rels(rels):
        try:
            dest = copy_to_input(output_dir, rel, input_dir=dest_root)
        except CatalogError as exc:
            errors.append({"rel": rel, "error": str(exc)})
            continue
        copied.append({"rel": rel, "name": dest.name})
    return copied, errors

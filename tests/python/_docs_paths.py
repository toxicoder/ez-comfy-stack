"""Resolve docs pages after the MkDocs-to-MDX rename.

Not collected by pytest (leading underscore). Authored pages that needed JSX
were renamed to ``.mdx``; callers that still name the MkDocs ``.md`` path
should go through ``docs_file``.
"""

from __future__ import annotations

from pathlib import Path


def docs_file(path: Path) -> Path:
    """Return ``path`` if it exists, else the ``.mdx`` sibling.

    Args:
        path: Docs path, usually ending in ``.md``.

    Returns:
        An existing file path when either suffix is on disk, otherwise ``path``.
    """
    if path.is_file():
        return path
    if path.suffix == ".md":
        alt = path.with_suffix(".mdx")
        if alt.is_file():
            return alt
    return path

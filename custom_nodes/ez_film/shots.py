"""Parse workflows/shorts/*.shots.yaml without PyYAML."""

from __future__ import annotations

import re
from typing import Any

FILM_SLUGS = {
    "go-see": "gosee",
    "still-here": "stillhere",
    "switchyard": "switchyard",
}
FILM_CHOICES = tuple(FILM_SLUGS)
SHOT_COUNT = 18
DEFAULT_CAP_SECONDS = 90.0
META_KEYS = (
    "film",
    "slug",
    "frames",
    "fps",
    "duration_s",
    "beats",
    "shots_per_beat",
    "total_shots",
    "publish_cap_s",
)


def film_slug(film: str) -> str:
    """Map film id to output prefix slug.

    Arguments:
        film: go-see, still-here, or switchyard.
    Returns:
        Slug string (gosee, stillhere, switchyard).
    Raises:
        ValueError: unknown film id.
    """
    slug = FILM_SLUGS.get(film)
    if slug is None:
        raise ValueError(f"unknown film: {film} (go-see|still-here|switchyard)")
    return slug


def _block_field(body: str, name: str) -> str:
    match = re.search(rf"^[ \t]*{name}:[ \t]*\|[ \t]*\n", body, re.M)
    if not match:
        raise ValueError(f"missing block {name}")
    lines: list[str] = []
    for line in body[match.end() :].splitlines():
        if re.match(r"^    \S", line):
            break
        if not line.strip():
            break
        if re.match(r"^      \S", line) or re.match(r"^        \S", line):
            lines.append(line.strip())
        else:
            break
    if not lines:
        raise ValueError(f"empty block {name}")
    return " ".join(lines)


def _scalar(body: str, name: str) -> str:
    match = re.search(rf"^\s*{name}:\s*(.+)$", body, re.M)
    if not match:
        raise ValueError(f"missing {name}")
    return match.group(1).strip()


def parse_shots_yaml(text: str) -> dict[str, Any]:
    """Parse a film bible YAML subset.

    Arguments:
        text: File contents of ``{film}.shots.yaml``.
    Returns:
        Dict with ``meta``, ``identity``, and ``shots`` (18 dicts).
    Raises:
        ValueError: missing required keys or empty prompt blocks.
    """
    meta: dict[str, str] = {}
    for key in META_KEYS:
        match = re.search(rf"^{key}:\s*(.+)$", text, re.M)
        if not match:
            raise ValueError(f"missing meta {key}")
        meta[key] = match.group(1).strip()

    ident_m = re.search(r"^identity_look:\s*\|\s*\n((?:  .*\n)+)", text, re.M)
    if not ident_m:
        raise ValueError("missing identity_look")
    identity = " ".join(
        line.strip() for line in ident_m.group(1).splitlines() if line.strip()
    )

    shots: list[dict[str, str]] = []
    blocks = re.split(r"\n  - beat:", text)[1:]
    for block in blocks:
        body = "beat:" + block
        shot = {
            "beat": _scalar(body, "beat"),
            "shot": _scalar(body, "shot"),
            "prefix": _scalar(body, "prefix"),
            "load_from": _scalar(body, "load_from"),
            "ltx_i2v": _block_field(body, "ltx_i2v"),
            "wan_i2v": _block_field(body, "wan_i2v"),
        }
        shots.append(shot)
    return {"meta": meta, "identity": identity, "shots": shots}

"""Resolve shipped lab JSON under workflows/_lab/<lane>/.

Not collected by pytest (leading underscore). Builders and tests import
``lab_json`` instead of hardcoding a folder.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"
LAB_ROOT = WF / "_lab"
SHORTS_YAML = WF / "shorts"
ALLOWED_LANES = (
    "klein",
    "wan",
    "ltx",
    "shorts",
    "dcc",
    "optional",
    "audio",
    "inspire",
)


def lab_example_paths(root: Path | None = None) -> list[Path]:
    """Every ``*-lab-example.json`` under ``workflows/_lab``."""
    base = LAB_ROOT if root is None else Path(root) / "_lab"
    if not base.is_dir():
        base = Path(root) if root is not None else LAB_ROOT
    return sorted(base.rglob("*-lab-example.json"))


def lab_json(stem: str, *, root: Path | None = None) -> Path:
    """Return the unique ``_lab/**/<stem>.json`` path.

    ``stem`` may be a basename, ``name.json``, or a leftover relative path
    such as ``shorts/film-go-see-90s-run-lab-example.json``.
    """
    name = Path(stem).name
    if not name.endswith(".json"):
        name = f"{name}.json"
    base = LAB_ROOT if root is None else Path(root) / "_lab"
    if not base.is_dir() and root is not None:
        base = Path(root)
    hits = sorted(p for p in base.rglob(name) if p.is_file())
    if not hits:
        raise FileNotFoundError(f"no lab json named {name} under {base}")
    if len(hits) > 1:
        rel = ", ".join(str(p.relative_to(base)) for p in hits)
        raise FileNotFoundError(f"ambiguous lab json {name}: {rel}")
    return hits[0]


def lab_dest(stem: str, *, lane: str | None = None, subdir: str | None = None) -> Path:
    """Path to write a lab graph. Creates the lane directory.

    ``subdir`` is an optional single path component under the lane
    (for example ``nill-bye`` → ``_lab/audio/nill-bye/``).
    """
    name = Path(stem).name
    if not name.endswith(".json"):
        name = f"{name}.json"
    chosen = lane or lane_for_stem(name)
    if chosen not in ALLOWED_LANES:
        raise ValueError(f"invalid lab lane {chosen!r}")
    dest_dir = LAB_ROOT / chosen
    if subdir is not None and str(subdir).strip() != "":
        extra = Path(str(subdir).strip())
        if extra.is_absolute() or extra.name != extra.as_posix() or extra.name in {".", ".."}:
            raise ValueError(f"invalid lab subdir {subdir!r}")
        dest_dir = dest_dir / extra.name
    dest = dest_dir / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def lane_for_stem(stem: str) -> str:
    """Sidebar lane for a lab filename or relative path."""
    rel = str(stem).replace("\\", "/").lstrip("./")
    name = Path(rel).name
    if rel.startswith("_lab/"):
        rest = rel[len("_lab/") :]
        lane = rest.split("/", 1)[0]
        if lane in ALLOWED_LANES:
            return lane
    if rel.startswith("shorts/") or name.startswith("film-"):
        return "shorts"
    if rel.startswith("dcc/"):
        return "dcc"
    if rel.startswith("optional/"):
        return "optional"
    if name.startswith("klein-"):
        return "klein"
    if name.startswith("wan-"):
        return "wan"
    if name.startswith("ltx-"):
        return "ltx"
    if name.startswith("podcast-") or name.startswith("music-") or name.startswith("dub-") or name.startswith("audio-"):
        return "audio"
    if name.startswith("prompt-forge-") or name.startswith("beat-sheet-"):
        return "inspire"
    raise ValueError(f"cannot map {stem!r} to a lab lane")

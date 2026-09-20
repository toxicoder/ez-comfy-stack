"""Download-tiers docs and command-builder match public pack ids.

Hermetic: stdlib + JSON. No MkDocs, network, Docker, or GPU.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
DOWNLOAD_TIERS = DOCS / "download-tiers.md"
UTIL = ROOT / "scripts" / "utilities"
BUILDER = ROOT / "includes" / "command-builder.json"
GLOSSARY = ROOT / "includes" / "glossary.json"
MODELS_PACKS = DOCS / "operate" / "models-packs.md"
SHORTS = DOCS / "shorts.md"

# Usage echo lines list operator-facing pack ids. Companion-only ids (te/vae)
# stay off this set on purpose. Ignore comment prose ("not in --tier all.").
_USAGE_TIER_RE = re.compile(r"--tier ([a-z0-9.|-]+)")
_TIER_TOKEN_RE = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
_DOWNLOAD_SH = sorted(UTIL.glob("download-*.sh"))

# Wan --tier all is 5b+a14b+fun-inp only.
WAN_ALL_EXCLUDED = ("vace", "s2v")
# LTX --tier all is 2.5 + 2.3 + gemma (not iclora, not quality).
LTX_ALL_INCLUDED = ("2.5", "2.3", "gemma")
LTX_ALL_EXCLUDED = ("iclora",)
LTX_BUILDER_CHOICES = (
    "2.5",
    "2.3",
    "balanced",
    "quality",
    "iclora",
    "gemma",
    "all",
)


def _read(path: Path) -> str:
    """Return UTF-8 file text.

    Args:
        path: Existing file.

    Returns:
        Entire file contents.
    """
    if not path.is_file() and path.suffix == ".md":
        path = path.with_suffix(".mdx")
    assert path.is_file(), path
    return path.read_text(encoding="utf-8")


def public_tiers_from_script(text: str) -> set[str]:
    """Parse public --tier ids from a downloader Usage line.

    Args:
        text: Script source.

    Returns:
        Pack ids listed after ``--tier`` in Usage.
    """
    ids: set[str] = set()
    for line in text.splitlines():
        if "Usage:" not in line:
            continue
        match = _USAGE_TIER_RE.search(line)
        if match is None:
            continue
        for part in match.group(1).split("|"):
            token = part.strip()
            if _TIER_TOKEN_RE.fullmatch(token):
                ids.add(token)
    return ids


def test_download_scripts_are_present() -> None:
    """The pack-id utilities this page documents still exist."""
    names = {p.name for p in _DOWNLOAD_SH}
    for expected in (
        "download-image.sh",
        "download-wan.sh",
        "download-ltx.sh",
        "download-podcast.sh",
        "download-dub.sh",
        "download-music.sh",
        "download-3d.sh",
        "download-longcat.sh",
        "download-dreamx.sh",
        "download-restore.sh",
        "download-llm.sh",
    ):
        assert expected in names, expected


def test_download_tiers_page_lists_every_public_pack_id() -> None:
    """Every Usage --tier id appears on the operator download-tiers page."""
    page = _read(DOWNLOAD_TIERS)
    missing: list[str] = []
    for script in _DOWNLOAD_SH:
        text = _read(script)
        for tier in sorted(public_tiers_from_script(text)):
            if tier not in page:
                missing.append(f"{script.name}: {tier}")
    assert missing == [], "download-tiers.md missing public pack ids:\n" + "\n".join(
        missing
    )


def test_download_tiers_chrome_and_pack_not_quality() -> None:
    """Page keeps scan chrome and the pack-id / Mbps contract."""
    text = _read(DOWNLOAD_TIERS)
    for needle in (
        "title:",
        "description:",
        "tags:",
        "**What's on this page**",
        "**What this enables**",
        "download-models",
        "--limit",
        "Mbps",
        "Klein 4B",
        "Wan 2.2",
        "LTX-2.5",
    ):
        assert needle in text, f"download-tiers.md missing {needle!r}"
    lower = text.lower()
    assert "pack id" in lower or "which **pack**" in lower or "pack selector" in lower
    assert "not a" in lower and "quality" in lower


def test_wan_all_excludes_vace_and_s2v() -> None:
    """Wan --tier all documentation matches download-wan.sh."""
    text = _read(DOWNLOAD_TIERS)
    lower = text.lower()
    assert "vace" in lower
    assert "s2v" in lower
    assert "does not include" in lower or "not in `--tier all`" in lower or "not vace" in lower
    for excluded in WAN_ALL_EXCLUDED:
        assert excluded in text


def test_ltx_all_is_25_23_gemma_not_iclora() -> None:
    """LTX --tier all is 2.5 + 2.3 + gemma; iclora stays opt-in."""
    text = _read(DOWNLOAD_TIERS)
    for included in LTX_ALL_INCLUDED:
        assert included in text
    assert "iclora" in text.lower() or "IC-LoRA" in text
    assert "balanced" in text
    assert "quality" in text
    lower = text.lower()
    assert "not iclora" in lower or "not `iclora`" in lower or "does not include `iclora`" in lower


def test_command_builder_ltx_choices_cover_aliases_and_all() -> None:
    """The LTX ezcmd widget lists every public pack id including aliases."""
    data = json.loads(_read(BUILDER))
    commands = {row["id"]: row for row in data["commands"]}
    assert "download-ltx" in commands
    flags = commands["download-ltx"]["flags"]
    tier_flag = next(flag for flag in flags if flag["name"] == "tier")
    values = [choice["value"] for choice in tier_flag["choices"]]
    for expected in LTX_BUILDER_CHOICES:
        assert expected in values, f"download-ltx widget missing {expected}"


def test_fun_inp_operator_size_is_about_47gb() -> None:
    """Fun InP is advertised as ~47 GB; 40 is the status floor only."""
    builder = _read(BUILDER)
    assert "~47 GB" in builder
    page = _read(DOWNLOAD_TIERS)
    assert "47" in page
    packs = _read(MODELS_PACKS)
    assert "~47 GB" in packs
    shorts = _read(SHORTS)
    assert "~47 GB" in shorts
    glossary = _read(GLOSSARY)
    assert "~47 GB" in glossary


def test_dreamx_selective_vs_full_repo_size() -> None:
    """DreamX-Creator selective payload vs full-repo size are both named."""
    text = _read(DOWNLOAD_TIERS)
    assert re.search(r"~?\s*8\s*GB", text)
    assert re.search(r"~?\s*54\s*GB", text)
    lower = text.lower()
    assert "selective" in lower or "min_gb" in lower or "status floor" in lower
    assert "full" in lower


def test_download_models_has_no_tier() -> None:
    """Default pack is not a --tier selector."""
    text = _read(DOWNLOAD_TIERS)
    assert "no `--tier`" in text or "has **no** `--tier`" in text or "has no `--tier`" in text

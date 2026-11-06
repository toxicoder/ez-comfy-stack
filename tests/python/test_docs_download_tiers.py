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
TROUBLESHOOTING_DOWNLOADS = DOCS / "operate" / "troubleshooting-downloads.md"

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
# FLUX 3 Image Klein: opt-in Kommunity packs, never in image --tier all.
FLUX3_IMAGE_TIERS = (
    "flux3",
    "flux3-base",
    "flux3-nvfp4",
    "flux3-bf16",
    "flux3-te",
    "flux3-pup",
)
# Qwen-Image 2.1: opt-in research-licensed stills plus their two companions.
# Never a default, never in image --tier all, never in download-models.
QWEN_IMAGE_TIERS = (
    "qwen-image",
    "qwen-image-turbo",
    "qwen-image-nvfp4",
    "qwen-image-turbo-nvfp4",
    "qwen-image-te",
    "qwen-image-vae",
)
# Weight basenames the six tiers pull, from the Comfy-Org repack and the two
# BennyDaBall NVFP4 conversions.
QWEN_IMAGE_WEIGHTS = (
    "qwen_image_2.1_int8_convrot.safetensors",
    "qwen_image_2.1_turbo_int8_convrot.safetensors",
    "qwen_image_2.1_nvfp4.safetensors",
    "qwen_image_2.1_turbo_nvfp4.safetensors",
    "qwen3vl_8b_int8_convrot.safetensors",
    "qwen3vl_8b_nvfp4.safetensors",
    "qwen3vl_8b_turbo_nvfp4.safetensors",
    "qwen_image_2.1_vae_bf16.safetensors",
)
# Source repos with their pinned HF revisions. The official Qwen/* repos are
# diffusers trees the stack never pulls.
QWEN_IMAGE_SOURCES = (
    "Comfy-Org/Qwen-Image-2.1",
    "aacf31a6d48e707f352ecba714cee0680da3479b",
    "BennyDaBall/Qwen-Image-2.1-NVFP4",
    "b0e954a1ba86f00e30f76bac2494f45b0a221948",
    "BennyDaBall/Qwen-Image-2.1-Turbo-NVFP4",
    "82226d8cadaf20a678338f8faf5e5a0cfc3e1dfd",
)
# Per-weight sizes on disk, as advertised on the tiers page.
QWEN_IMAGE_SIZES = (
    "7.26 GB",
    "4.20 GB",
    "7.55 GB",
    "5.69 GB",
    "9.33 GB",
    "9.35 GB",
    "0.68 GB",
)
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


def _flat(path: Path) -> str:
    """Return file text lowercased with every run of whitespace collapsed.

    Prose needles are matched against this so a page can rewrap a sentence
    without breaking the assertion.

    Args:
        path: Existing file.

    Returns:
        Lowercased, single-spaced whole-file text.
    """
    return " ".join(_read(path).lower().split())


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


def test_flux3_image_tiers_are_documented_and_not_in_all() -> None:
    """FLUX 3 Image Klein packs are opt-in, gated, and absent from image `all`."""
    text = _read(DOWNLOAD_TIERS)
    for tier in FLUX3_IMAGE_TIERS:
        assert f"`{tier}`" in text, f"download-tiers.md missing {tier}"
        # The page names the pull by its Bazel target; the tier flag is what the
        # row has to prove, so assert that and accept either documented door.
        assert f"run --tier {tier}" in text, tier
        assert "download-image" in text, tier
    lower = text.lower()
    assert "kommunity" in lower, "FLUX 3 must be named as Kommunity, not Apache"
    assert "hf_token" in lower, "gated packs must name HF_TOKEN"
    assert "license acceptance" in lower or "accept" in lower
    assert "not in `--tier all`" in lower or "does not include `flux3`" in lower
    for excluded in FLUX3_IMAGE_TIERS:
        assert excluded in text


def test_command_builder_download_image_choices_cover_flux3() -> None:
    """The download-image ezcmd widget lists every FLUX 3 pack id."""
    data = json.loads(_read(BUILDER))
    commands = {row["id"]: row for row in data["commands"]}
    assert "download-image" in commands
    flags = commands["download-image"]["flags"]
    tier_flag = next(flag for flag in flags if flag["name"] == "tier")
    values = [choice["value"] for choice in tier_flag["choices"]]
    for expected in (*FLUX3_IMAGE_TIERS, "all", "fast"):
        assert expected in values, f"download-image widget missing {expected}"
    assert "all" not in FLUX3_IMAGE_TIERS


def test_qwen_image_tiers_are_documented_and_not_in_all() -> None:
    """Qwen-Image 2.1 packs are opt-in, ungated, and absent from image `all`."""
    text = _read(DOWNLOAD_TIERS)
    for tier in QWEN_IMAGE_TIERS:
        assert f"`{tier}`" in text, f"download-tiers.md missing {tier}"
        assert f"run --tier {tier}" in text, tier
        assert "download-image" in text, tier
    lower = _flat(DOWNLOAD_TIERS)
    assert "not in `--tier all`" in lower
    assert "not in `download-models`" in lower or "not in download-models" in lower
    assert "auto-includes `qwen-image-te`" in lower
    assert "auto-includes `qwen-image-vae`" in lower
    for tier in QWEN_IMAGE_TIERS:
        assert tier in text


def test_qwen_image_tiers_are_research_licensed_not_apache() -> None:
    """The page names the Qwen RESEARCH LICENSE AGREEMENT, never Apache."""
    text = _read(DOWNLOAD_TIERS)
    lower = _flat(DOWNLOAD_TIERS)
    for needle in (
        "qwen research license agreement",
        "2026-09-20",
        "hangzhou tongyi laboratory",
        "section 2.b",
        "governing law",
        "china",
        "hangzhou",
        "commercial",
        "paid qwen license",
        "built with qwen",
        "qwen is licensed under the qwen research license agreement",
    ):
        assert needle in lower, f"download-tiers.md missing {needle!r}"
    assert "not apache" in lower
    assert "klein 4b" in lower
    for line in text.splitlines():
        if line.lower().startswith("| `qwen-image"):
            assert "apache" not in line.lower(), f"qwen row reads as Apache: {line}"


def test_qwen_image_weights_sources_and_sizes_are_named() -> None:
    """Each Qwen-Image row names its file, its repo pin, and its size."""
    lower = _flat(DOWNLOAD_TIERS)
    for name in QWEN_IMAGE_WEIGHTS:
        assert name in lower, f"download-tiers.md missing weight {name}"
    for source in QWEN_IMAGE_SOURCES:
        assert source.lower() in lower, f"download-tiers.md missing source {source}"
    for size in QWEN_IMAGE_SIZES:
        assert size.lower() in lower, f"download-tiers.md missing size {size}"
    assert "qwen/qwen-image-2.1" in lower, "official upstream repos must be named"
    assert "independent" in lower and "conversion" in lower


def test_qwen_image_tiers_are_ungated() -> None:
    """The Qwen-Image repos are public: no token, no license click."""
    lower = _flat(DOWNLOAD_TIERS)
    assert "ungated" in lower
    assert "no `hf_token`" in lower
    assert "license-accept" in lower or "license accept" in lower


def test_image_all_still_excludes_qwen_image_packs() -> None:
    """Image --tier all never pulls a Qwen-Image 2.1 pack."""
    text = _read(DOWNLOAD_TIERS)
    prose = [line for line in text.splitlines() if "--tier all" in line]
    assert any("qwen-image" in line.lower() for line in prose), (
        "the image --tier all sentence must name the qwen-image exclusion"
    )
    for line in text.splitlines():
        if line.startswith("| image `all`"):
            for tier in QWEN_IMAGE_TIERS:
                assert f"`{tier}`" not in line, f"image all row lists {tier}: {line}"


def test_command_builder_download_image_choices_cover_qwen_image() -> None:
    """The download-image ezcmd widget lists every Qwen-Image pack id."""
    data = json.loads(_read(BUILDER))
    commands = {row["id"]: row for row in data["commands"]}
    assert "download-image" in commands
    flags = commands["download-image"]["flags"]
    tier_flag = next(flag for flag in flags if flag["name"] == "tier")
    values = [choice["value"] for choice in tier_flag["choices"]]
    for expected in QWEN_IMAGE_TIERS:
        assert expected in values, f"download-image widget missing {expected}"
    assert "all" not in QWEN_IMAGE_TIERS


def test_models_packs_lists_qwen_image_basenames() -> None:
    """The packs page names every Qwen-Image basename and its Comfy folder."""
    lower = _flat(MODELS_PACKS)
    for name in QWEN_IMAGE_WEIGHTS:
        assert name in lower, f"models-packs.md missing basename {name}"
    for needle in (
        "qwen research license agreement",
        "commercial",
        "built with qwen",
        "klein 4b",
        "comfy-org/qwen-image-2.1",
        "bennydaball",
        "download-models",
        "diffusion_models/",
        "text_encoders/",
        "vae/",
    ):
        assert needle in lower, f"models-packs.md missing {needle!r}"


def test_troubleshooting_downloads_names_the_qwen_image_symptoms() -> None:
    """The downloads page covers the two Qwen-Image operator traps."""
    text = _read(TROUBLESHOOTING_DOWNLOADS)
    for needle in ("title:", "description:", "tags:"):
        assert needle in text, needle
    lower = _flat(TROUBLESHOOTING_DOWNLOADS)
    assert "qwen-image" in lower
    assert "run --tier qwen-image" in lower
    assert "opt-in" in lower
    assert "checkpoint" in lower
    assert "diffusers" in lower
    assert "comfy-org/qwen-image-2.1" in lower


def test_download_models_has_no_tier() -> None:
    """Default pack is not a --tier selector."""
    text = _read(DOWNLOAD_TIERS)
    assert "no `--tier`" in text or "has **no** `--tier`" in text or "has no `--tier`" in text

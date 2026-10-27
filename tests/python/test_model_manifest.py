"""Parse config/model-manifest.yaml (stdlib only)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import model_manifest as mm  # noqa: E402

MANIFEST = ROOT / "config" / "model-manifest.yaml"
LICENSE = ROOT / "LICENSE-MODELS.md"

DEFAULT_FILES = (
    "flux-2-klein-4b-fp8.safetensors",
    "qwen_3_4b.safetensors",
    "flux2-vae.safetensors",
    "wan2.2_ti2v_5B_fp16.safetensors",
    "wan2.2_vae.safetensors",
    "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
    "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors",
    "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors",
    "ltx-2.5-video-vae-bf16.safetensors",
    "ltx-2.5-audio-vae-bf16.safetensors",
    "Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
)


FLUX3_REPO_DIR = "black-forest-labs__flux-3-image-klein-comfy"

# pack name -> (min_gb, tier suffix, basenames, cmd)
FLUX3_PACKS: dict[str, tuple[int, str, list[str], str]] = {
    "flux3-klein-distilled-int8": (
        6,
        "flux3",
        ["flux3-image-klein-int8-convrot.safetensors"],
        "download-image --tier flux3",
    ),
    "flux3-klein-base-int8": (
        6,
        "flux3-base",
        ["flux3-image-klein-base-int8-convrot.safetensors"],
        "download-image --tier flux3-base",
    ),
    "flux3-klein-base-nvfp4": (
        6,
        "flux3-nvfp4",
        ["flux3-image-klein-base-nvfp4.safetensors"],
        "download-image --tier flux3-nvfp4",
    ),
    "flux3-klein-base-bf16": (
        12,
        "flux3-bf16",
        ["flux3-image-klein-base-bf16.safetensors"],
        "download-image --tier flux3-bf16",
    ),
    "flux3-qwen3vl-te": (
        5,
        "flux3-te",
        ["qwen3vl_4b_int8_convrot.safetensors"],
        "download-image --tier flux3-te",
    ),
    "flux3-prompt-upsampler": (
        10,
        "flux3-pup",
        ["qwen3.5_9b_flux3_prompt_upsampler_int8_convrot.safetensors"],
        "download-image --tier flux3-pup",
    ),
}


def test_flux3_klein_packs_are_opt_in() -> None:
    """FLUX 3 Image Klein packs exist, are opt-in, and pin their tier dir."""
    man = mm.load_manifest(MANIFEST)
    packs = man["packs"]
    for name, (min_gb, tier, files, cmd) in FLUX3_PACKS.items():
        assert name in packs, name
        pack = packs[name]
        assert pack["default"] is False, name
        assert pack["min_gb"] == min_gb, name
        assert pack["tier_dir"] == f"{FLUX3_REPO_DIR}_{tier}", name
        assert pack["files"] == files, name
        assert pack["cmd"] == cmd, name
    for name in ("flux3-klein-distilled-int8", "flux3-klein-base-int8"):
        assert "flux2-vae" in packs[name]["shares"], name
        assert "flux3-qwen3vl-te" in packs[name]["shares"], name


def test_flux3_klein_files_stay_out_of_default_keep_set() -> None:
    """Nothing FLUX 3 ships in download-models; Klein 4B stays the default."""
    man = mm.load_manifest(MANIFEST)
    default_keep = mm.default_keep_set(man)
    for _, _, files, _ in FLUX3_PACKS.values():
        for name in files:
            assert name not in default_keep, name
    assert "flux-2-klein-4b-fp8.safetensors" in default_keep
    keep = mm.keep_set(man)
    assert "flux3-image-klein-int8-convrot.safetensors" in keep


def test_default_filenames_in_keep_set() -> None:
    man = mm.load_manifest(MANIFEST)
    keep = mm.default_keep_set(man)
    for name in DEFAULT_FILES:
        assert name in keep, name
    text = LICENSE.read_text(encoding="utf-8")
    for name in DEFAULT_FILES:
        assert name in text
    refuse = " ".join(man["refuse"])
    assert "MiniMax-H3" in refuse
    assert "FLUX.2-klein-9b" not in refuse
    assert "FLUX.2-dev" not in refuse
    assert "DA3-LARGE" in refuse
    packs = man["packs"]
    assert packs["klein-9b-fp8"]["default"] is False
    assert "flux-2-klein-9b-fp8.safetensors" in packs["klein-9b-fp8"]["files"]
    assert packs["flux2-dev"]["default"] is False
    assert "Inria-3DGS" in refuse
    assert "Pixal3D-as-default" in refuse


def test_cli_keep_set() -> None:
    assert mm._cli(["--manifest", str(MANIFEST), "keep-set"]) == 0  # noqa: SLF001
    assert mm._cli(["--manifest", str(MANIFEST), "default-keep-set"]) == 0  # noqa: SLF001
    assert mm._cli(["--manifest", str(MANIFEST), "refuse"]) == 0  # noqa: SLF001
    assert mm._cli(["--manifest", str(MANIFEST), "json"]) == 0  # noqa: SLF001
    assert mm._cli(["--manifest", str(MANIFEST), "pack", "ltx-2.5"]) == 0  # noqa: SLF001
    assert mm._cli(["--manifest", str(MANIFEST), "pack", "nope"]) == 1  # noqa: SLF001


def test_load_manifest_skips_orphan_lines(tmp_path: Path) -> None:
    path = tmp_path / "man.yaml"
    path.write_text(
        "\n".join(
            [
                "schema: 1",
                "refuse:",
                "  - BannedTok",
                "  not-a-token",
                "packs:",
                "  orphan line without colon",
                "  demo:",
                "    default: true",
                "    retired: false",
                "    min_gb: 2",
                "    tier_dir: demo",
                "    cmd: 'echo'",
                "    cleanup: ''",
                "    files:",
                "      - keep-me.safetensors",
                "    shares:",
                "      - share-me.safetensors",
                "    extra: leftover",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    man = mm.load_manifest(path)
    assert man["refuse"] == ["BannedTok"]
    pack = man["packs"]["demo"]
    assert pack["default"] is True
    assert pack["min_gb"] == 2
    assert pack["files"] == ["keep-me.safetensors"]
    assert pack["shares"] == ["share-me.safetensors"]
    assert pack["cmd"] == "echo"
    assert mm.keep_set(man) == {"keep-me.safetensors"}
    assert mm.default_keep_set(man) == {"keep-me.safetensors"}

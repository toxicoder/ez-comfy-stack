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

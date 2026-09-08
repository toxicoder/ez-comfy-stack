"""Parse config/disk-catalog.yaml and rank leftover candidates (stdlib only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import disk_catalog as dc  # noqa: E402
import model_manifest as mm  # noqa: E402

CATALOG = ROOT / "config" / "disk-catalog.yaml"
MANIFEST = ROOT / "config" / "model-manifest.yaml"


def test_catalog_loads_and_validates() -> None:
    """Shipped signatures have required fields and known risk/reclaim."""
    cat = dc.load_catalog(CATALOG)
    assert cat["schema"] == 1
    sigs = cat["signatures"]
    for key in (
        "hf-incomplete",
        "dangling-symlink",
        "keep-set-weight",
        "docker-build-cache",
        "ollama-blobs",
        "vllm-sglang-cache",
    ):
        assert key in sigs, key
        assert sigs[key]["what"]
        assert sigs[key]["why"]
        assert sigs[key]["risk"] in dc.VALID_RISK
        assert sigs[key]["reclaim"] in dc.VALID_RECLAIM


def test_incomplete_outranks_keep_set() -> None:
    """Junk incomplete scores above a keep-set weight of the same size."""
    cat = dc.load_catalog(CATALOG)
    keep, refuse = mm.default_keep_set(mm.load_manifest(MANIFEST)), mm.load_manifest(MANIFEST)["refuse"]
    junk = dc.classify_path(
        "/mnt/models/foo.safetensors.incomplete",
        cat,
        keep_set=keep,
        refuse=refuse,
        size_bytes=10_000_000_000,
    )
    live = dc.classify_path(
        "/mnt/models/flux-2-klein-4b-fp8.safetensors",
        cat,
        keep_set=keep,
        refuse=refuse,
        size_bytes=10_000_000_000,
    )
    assert junk["id"] == "hf-incomplete"
    assert junk["risk"] == "safe"
    assert junk["step"] == "A"
    assert live["id"] == "keep-set-weight"
    assert live["risk"] == "dangerous"
    assert live["step"] == "C"
    ranked = dc.rank_candidates([live, junk])
    assert ranked[0]["id"] == "hf-incomplete"


def test_banned_and_ltx23() -> None:
    """Refuse-list tokens and LTX-2.3 trees are review/reap."""
    cat = dc.load_catalog(CATALOG)
    man = mm.load_manifest(MANIFEST)
    keep, refuse = mm.default_keep_set(man), man["refuse"]
    banned = dc.classify_path(
        "/mnt/models/MiniMax-H3.safetensors",
        cat,
        keep_set=keep,
        refuse=refuse,
        size_bytes=1000,
    )
    old = dc.classify_path(
        "/mnt/models/Lightricks__LTX-2.3_2.3/x.safetensors",
        cat,
        keep_set=keep,
        refuse=refuse,
        size_bytes=1000,
    )
    assert banned["id"] == "banned-weight"
    assert old["id"] == "ltx-2.3-superseded"
    assert old["reclaim"] == "reap-models"


def test_docker_and_vllm_paths() -> None:
    """Synthetic docker ids and vLLM cache paths classify."""
    cat = dc.load_catalog(CATALOG)
    docker = dc.classify_path(
        "docker://build-cache/abc",
        cat,
        size_bytes=5_000_000_000,
    )
    vllm = dc.classify_path(
        "/home/spark/.cache/vllm/torch_compile/x.bin",
        cat,
        size_bytes=2_000_000_000,
    )
    assert docker["id"] == "docker-build-cache"
    assert docker["risk"] == "safe"
    assert vllm["id"] == "vllm-sglang-cache"
    assert vllm["risk"] == "review"


def test_cli_classify_and_rank(tmp_path: Path) -> None:
    """CLI classify / rank round-trip."""
    assert (
        dc._cli(  # noqa: SLF001
            [
                "--catalog",
                str(CATALOG),
                "--manifest",
                str(MANIFEST),
                "classify",
                "--path",
                "/mnt/models/x.incomplete",
                "--size",
                "100",
            ]
        )
        == 0
    )
    assert dc._cli(["--catalog", str(CATALOG), "json"]) == 0  # noqa: SLF001


def test_expand_roots_honors_disk_wizard_home() -> None:
    """Tests can jail ~/.cache via DISK_WIZARD_HOME."""
    roots = dc.expand_roots(
        {
            "DISK_WIZARD_HOME": "/tmp/ez-home",
            "MODELS_DIR": "/tmp/models",
            "COMFY_OUTPUT_DIR": "/tmp/out",
        }
    )
    assert roots["HOME_HF"].endswith("/.cache/huggingface")
    assert "ez-home" in roots["HOME_CACHE"]
    assert roots["MODELS_DIR"].endswith("models") or "models" in roots["MODELS_DIR"]


def test_rank_score_safe_beats_review() -> None:
    """Equal size: safe junk ranks above review leftovers."""
    safe = dc.rank_score(1000, 10, "safe")
    review = dc.rank_score(1000, 10, "review")
    danger = dc.rank_score(1000, 10, "dangerous")
    assert safe > review > danger

"""Parse config/disk-catalog.yaml and rank leftover candidates (stdlib only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

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


def test_walk_prunes_nested_skip_dirs(tmp_path: Path) -> None:
    """node_modules / .venv descendants are not yielded at any depth."""
    (tmp_path / "keep.bin").write_text("ok")
    nested = tmp_path / "node_modules" / "pkg"
    nested.mkdir(parents=True)
    (nested / "x.js").write_text("no")
    venv_pkg = tmp_path / ".venv" / "lib"
    venv_pkg.mkdir(parents=True)
    (venv_pkg / "mod.py").write_text("no")
    rows = list(dc.walk_root_files(str(tmp_path), max_depth=6))
    rels = [str(Path(r["path"]).relative_to(tmp_path)) for r in rows]
    assert "keep.bin" in rels
    assert not any("node_modules" in Path(rel).parts for rel in rels)
    assert not any(".venv" in Path(rel).parts for rel in rels)


def test_walk_respects_max_depth(tmp_path: Path) -> None:
    """Files deeper than max_depth are omitted (find -maxdepth semantics)."""
    cur = tmp_path
    for i in range(8):
        cur = cur / f"d{i}"
        cur.mkdir()
        (cur / "f.bin").write_text("x")
    rows = list(dc.walk_root_files(str(tmp_path), max_depth=6))
    rels = [str(Path(r["path"]).relative_to(tmp_path)) for r in rows]
    depths = [len(Path(rel).parts) for rel in rels]
    assert depths
    assert max(depths) <= 6
    assert 6 in depths
    assert not any("d5" in Path(rel).parts for rel in rels)


def test_walk_skips_plan_basename_and_broken_symlink(tmp_path: Path) -> None:
    """Wizard logs are omitted; broken symlinks are size 0."""
    (tmp_path / ".disk-wizard-plan.json").write_text("{}")
    (tmp_path / "ok.bin").write_text("x")
    (tmp_path / "broken.lnk").symlink_to(tmp_path / "missing-target")
    rows = list(dc.walk_root_files(str(tmp_path), max_depth=6))
    by_name = {Path(r["path"]).name: r for r in rows}
    assert ".disk-wizard-plan.json" not in by_name
    assert "ok.bin" in by_name
    broken = by_name["broken.lnk"]
    assert broken["broken_symlink"] is True
    assert broken["size_bytes"] == 0


def test_cli_walk_emits_jsonl_and_progress(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """walk CLI writes JSONL on stdout and Scanning on stderr."""
    (tmp_path / "a.bin").write_text("hi")
    rc = dc._cli(  # noqa: SLF001
        [
            "--catalog",
            str(CATALOG),
            "walk",
            "--max-depth",
            "2",
            str(tmp_path),
        ]
    )
    assert rc == 0
    captured = capsys.readouterr()
    rows = [json.loads(line) for line in captured.out.splitlines() if line.strip()]
    assert any(str(r.get("path", "")).endswith("a.bin") for r in rows)
    assert "Scanning" in captured.err


def test_progress_interval_parses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """DISK_WIZARD_PROGRESS_INTERVAL=0 disables heartbeats; bad values default."""
    monkeypatch.delenv("DISK_WIZARD_PROGRESS_INTERVAL", raising=False)
    assert dc.progress_interval_s() == 2.0
    monkeypatch.setenv("DISK_WIZARD_PROGRESS_INTERVAL", "0")
    assert dc.progress_interval_s() == 0.0
    monkeypatch.setenv("DISK_WIZARD_PROGRESS_INTERVAL", "not-a-float")
    assert dc.progress_interval_s() == 2.0


def test_progress_prefix_matches_operator_log() -> None:
    assert dc.PROGRESS_PREFIX == "[ez-comfy]"


def test_emit_walk_progress_newline(capsys: pytest.CaptureFixture[str]) -> None:
    """Non-TTY progress is a full prefixed line (BATS/CI)."""
    dc.emit_walk_progress("Scanning /tmp/models (max depth 6)…")
    err = capsys.readouterr().err
    assert err.startswith("[ez-comfy] Scanning")
    assert err.endswith("\n")
    dc.emit_walk_progress("  still scanning /tmp/models: 12 paths…", rewrite=True)
    err2 = capsys.readouterr().err
    assert "still scanning" in err2
    assert err2.endswith("\n")


def test_walk_roots_to_stdout_skips_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing roots are skipped; existing roots emit JSONL."""
    (tmp_path / "a.bin").write_text("x")
    n = dc.walk_roots_to_stdout([str(tmp_path / "missing"), str(tmp_path)], 2)
    captured = capsys.readouterr()
    assert n == 1
    assert "Scanning" in captured.err
    assert json.loads(captured.out.splitlines()[0])["path"].endswith("a.bin")

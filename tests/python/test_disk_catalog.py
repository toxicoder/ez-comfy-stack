"""Parse config/disk-catalog.yaml and rank leftover candidates (stdlib only)."""

from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path
from typing import Any

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
    dc.emit_walk_progress("Scanning /tmp/models (max depth 6)...")
    err = capsys.readouterr().err
    assert err.startswith("[ez-comfy] Scanning")
    assert err.endswith("\n")
    dc.emit_walk_progress("  still scanning /tmp/models: 12 paths...", rewrite=True)
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


def test_load_catalog_skips_and_rejects(tmp_path: Path) -> None:
    good = tmp_path / "ok.yaml"
    good.write_text(
        "\n".join(
            [
                "schema: 1",
                "other:",
                "  ignored: true",
                "signatures:",
                "  stray line without colon",
                "  demo:",
                "    risk: safe",
                "    reclaim: delete",
                "    leftover_weight:",
                "    what: demo",
                "    why: test",
                "    leftover_when: always",
                "    match_suffix:",
                "      - \".tmp\"",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    cat = dc.load_catalog(good)
    assert cat["signatures"]["demo"]["leftover_weight"] == 0
    bad_risk = tmp_path / "risk.yaml"
    bad_risk.write_text(
        "schema: 1\nsignatures:\n  demo:\n    risk: exploding\n    reclaim: delete\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="bad risk"):
        dc.load_catalog(bad_risk)
    bad_reclaim = tmp_path / "reclaim.yaml"
    bad_reclaim.write_text(
        "schema: 1\nsignatures:\n  demo:\n    risk: safe\n    reclaim: shred\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="bad reclaim"):
        dc.load_catalog(bad_reclaim)


def test_rank_score_zero_penalty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(dc.RISK_PENALTY, "safe", 0)
    assert dc.rank_score(100, 10, "safe") == 250.0


def test_path_matches_keep_prefix_basename() -> None:
    keep_sig = {"match_keep_set": True}
    assert dc._path_matches("/mnt/models/keep.bin", keep_sig, {"keep.bin"}, []) is True
    assert dc._path_matches("/mnt/models/other.bin", keep_sig, {"keep.bin"}, []) is False
    cat = dc.load_catalog(CATALOG)
    core = dc.classify_path("/tmp/core", cat, size_bytes=12)
    assert core["id"] == "core-dump"
    dotted = dc.classify_path("/tmp/core.1234", cat, size_bytes=12)
    assert dotted["id"] == "core-dump"


def test_classify_dangling_and_unknown() -> None:
    cat = {
        "signatures": {
            "dangling-symlink": {
                **dc._empty_sig(),
                "match_suffix": [".lnk"],
                "match_broken_symlink": False,
            },
            "keep-set-weight": {
                **dc._empty_sig(),
                "match_suffix": [".safetensors"],
                "match_keep_set": False,
            },
        }
    }
    dangling = dc.classify_path("/x/a.lnk", cat, broken_symlink=True)
    assert dangling["id"] == "dangling-symlink"
    skipped = dc.classify_path("/x/a.lnk", cat, broken_symlink=False)
    assert skipped["id"] == "unknown"
    keep_skip = dc.classify_path("/x/foo.safetensors", cat, keep_set=set())
    assert keep_skip["id"] == "unknown"
    live = dc.load_catalog(CATALOG)
    broken = dc.classify_path("/mnt/models/missing", live, broken_symlink=True)
    assert broken["id"] == "dangling-symlink"


def test_walk_error_and_depth_edges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert list(dc.walk_root_files(str(tmp_path / "missing"), max_depth=6)) == []
    assert list(dc.walk_root_files(str(tmp_path), max_depth=0)) == []
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    (blocked / "x.bin").write_text("x", encoding="utf-8")
    real_scandir = os.scandir

    def wrapped(path: str) -> Any:
        if Path(path).name == "blocked":
            raise OSError("perm")
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", wrapped)
    rows = list(dc.walk_root_files(str(tmp_path), max_depth=3))
    assert not any("blocked" in r["path"] for r in rows)

    class Boom:
        name = "x"
        path = str(tmp_path / "x")

        def is_symlink(self) -> bool:
            raise OSError("stat")

    class CM:
        def __iter__(self) -> Any:
            return iter([Boom()])

        def __enter__(self) -> CM:
            return self

        def __exit__(self, *_a: object) -> None:
            return None

    monkeypatch.setattr(os, "scandir", lambda _p: CM())
    assert list(dc.walk_root_files(str(tmp_path), max_depth=2)) == []

    monkeypatch.setattr(os, "scandir", real_scandir)
    boom = tmp_path / "boom.bin"
    boom.write_text("x", encoding="utf-8")
    real_size = os.path.getsize

    def size_wrapped(path: str) -> int:
        if str(path).endswith("boom.bin"):
            raise OSError("size")
        return int(real_size(path))

    monkeypatch.setattr(os.path, "getsize", size_wrapped)
    row = dc._file_row(str(boom))
    assert row["size_bytes"] == 0


def test_walk_progress_interval_zero_and_heartbeat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "a.bin").write_text("a", encoding="utf-8")
    (tmp_path / "b.bin").write_text("b", encoding="utf-8")
    monkeypatch.setenv("DISK_WIZARD_PROGRESS_INTERVAL", "0")
    n = dc.walk_roots_to_stdout([str(tmp_path)], 2)
    assert n == 2
    capsys.readouterr()
    monkeypatch.setenv("DISK_WIZARD_PROGRESS_INTERVAL", "0.0001")
    monkeypatch.setattr(dc, "WALK_PROGRESS_EVERY", 1)
    n2 = dc.walk_roots_to_stdout([str(tmp_path)], 2)
    assert n2 == 2
    err = capsys.readouterr().err
    assert "still scanning" in err


def test_cli_rank_and_keep_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    lib = str(ROOT / "scripts" / "lib")
    saved = sys.path[:]
    try:
        while lib in sys.path:
            sys.path.remove(lib)
        keep, refuse = dc._load_keep_refuse(MANIFEST)
    finally:
        sys.path[:] = saved
    assert keep
    assert refuse
    payload = (
        "\n"
        + json.dumps({"path": "/mnt/models/x.incomplete", "size_bytes": 10})
        + "\n"
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(payload))
    assert dc._cli(["--catalog", str(CATALOG), "--manifest", str(MANIFEST), "rank"]) == 0
    ranked = json.loads(capsys.readouterr().out)
    assert ranked[0]["id"] == "hf-incomplete"
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(json.dumps({"path": str(tmp_path / "core"), "size_bytes": 1}) + "\n"),
    )
    assert (
        dc._cli(
            [
                "--catalog",
                str(CATALOG),
                "classify",
                "--path",
                str(tmp_path / "core"),
                "--size",
                "1",
                "--broken-symlink",
            ]
        )
        == 0
    )

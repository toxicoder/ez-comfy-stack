#!/usr/bin/env python3
"""Restricted YAML loader + classifier for config/disk-catalog.yaml."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from operator_log import PREFIX as PROGRESS_PREFIX
from operator_log import emit as _ol_emit

_LIST_KEYS = (
    "match_suffix",
    "match_contains",
    "match_basename",
    "match_prefix",
    "roots",
    "refuse_if",
)
_BOOL_KEYS = ("match_broken_symlink", "match_refuse", "match_keep_set")
_INT_KEYS = ("leftover_weight",)
_STR_KEYS = (
    "risk",
    "reclaim",
    "what",
    "why",
    "leftover_when",
    "docker_type",
)
RISK_PENALTY = {"safe": 1, "review": 4, "dangerous": 100}
VALID_RISK = frozenset(RISK_PENALTY)
VALID_RECLAIM = frozenset(
    {"delete", "quarantine", "docker-prune", "hf-prune", "reap-models", "none"}
)

# Keep in sync with disk_skip_dir_name / disk_walk_root in disk_scan.sh.
SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".tox",
        ".disk-quarantine",
        ".reap-quarantine",
    }
)
SKIP_BASENAMES = frozenset(
    {
        ".disk-wizard-plan.json",
        ".disk-wizard.log",
        ".reap-log",
        ".reap-models.log",
    }
)
WALK_PROGRESS_EVERY = 500


def _empty_sig() -> dict[str, Any]:
    """Default signature fields.

    Returns:
        Mutable signature mapping.
    """
    row: dict[str, Any] = {
        "risk": "review",
        "reclaim": "none",
        "leftover_weight": 0,
        "what": "",
        "why": "",
        "leftover_when": "",
        "docker_type": "",
        "match_broken_symlink": False,
        "match_refuse": False,
        "match_keep_set": False,
    }
    for key in _LIST_KEYS:
        row[key] = []
    return row


def load_catalog(path: Path) -> dict[str, Any]:
    """Parse the restricted disk-catalog YAML subset.

    Args:
        path: Catalog file.

    Returns:
        Mapping with schema + signatures.
    """
    text = path.read_text(encoding="utf-8")
    signatures: dict[str, dict[str, Any]] = {}
    section = ""
    sig = ""
    list_key = ""
    schema = 1
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("schema:"):
            schema = int(line.split(":", 1)[1].strip())
            continue
        if line == "signatures:":
            section = "signatures"
            sig = ""
            list_key = ""
            continue
        if section != "signatures":
            continue
        if line.startswith("  ") and not line.startswith("    ") and line.strip().endswith(":"):
            sig = line.strip()[:-1]
            signatures[sig] = _empty_sig()
            list_key = ""
            continue
        if not sig:
            continue
        stripped = line.strip()
        if stripped.endswith(":") and stripped[:-1] in _LIST_KEYS:
            list_key = stripped[:-1]
            continue
        if list_key and stripped.startswith("- "):
            signatures[sig][list_key].append(stripped[2:].strip().strip('"').strip("'"))
            continue
        if ":" in stripped and not stripped.startswith("- "):
            list_key = ""
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key in _BOOL_KEYS:
                signatures[sig][key] = val.lower() == "true"
            elif key in _INT_KEYS:
                signatures[sig][key] = int(val or "0")
            elif key in _STR_KEYS:
                signatures[sig][key] = val
    for sid, row in signatures.items():
        if row["risk"] not in VALID_RISK:
            raise ValueError(f"{sid}: bad risk {row['risk']!r}")
        if row["reclaim"] not in VALID_RECLAIM:
            raise ValueError(f"{sid}: bad reclaim {row['reclaim']!r}")
    return {"schema": schema, "signatures": signatures}


def expand_roots(env: dict[str, str] | None = None) -> dict[str, str]:
    """Resolve catalog root tokens to absolute directories.

    Args:
        env: Override environment. Default os.environ.

    Returns:
        Token → path (missing tokens omitted).
    """
    src = env if env is not None else dict(os.environ)
    home = src.get("DISK_WIZARD_HOME") or src.get("HOME") or str(Path.home())
    models = src.get("MODELS_DIR") or "/mnt/models"
    outputs = src.get("COMFY_OUTPUT_DIR") or "/mnt/comfy-output"
    mapping = {
        "MODELS_DIR": models,
        "COMFY_OUTPUT_DIR": outputs,
        "HOME_CACHE": str(Path(home) / ".cache"),
        "HOME_HF": str(Path(home) / ".cache" / "huggingface"),
        "HOME_OLLAMA": str(Path(home) / ".ollama"),
        "TMP": "/tmp",
        "VAR_TMP": "/var/tmp",
    }
    return {key: os.path.realpath(val) for key, val in mapping.items()}


def rank_score(size_bytes: int, leftover_weight: int, risk: str) -> float:
    """Size × leftover weight / risk penalty.

    Args:
        size_bytes: File or object size.
        leftover_weight: Catalog weight.
        risk: safe|review|dangerous.

    Returns:
        Rank score (higher = show first).
    """
    penalty = RISK_PENALTY.get(risk, 4)
    if penalty <= 0:
        penalty = 4
    return (max(int(size_bytes), 0) * max(int(leftover_weight), 0)) / float(penalty)


def _path_matches(path: str, sig: MappingSig, keep_set: set[str], refuse: list[str]) -> bool:
    """True when a signature applies to path.

    Args:
        path: Absolute path.
        sig: Signature mapping.
        keep_set: Default keep-set basenames.
        refuse: Refuse-list tokens.

    Returns:
        Whether this signature matches.
    """
    base = os.path.basename(path)
    if sig.get("match_keep_set") and base in keep_set:
        return True
    if sig.get("match_refuse"):
        lower = path.lower()
        for tok in refuse:
            if tok.lower() in lower:
                return True
        return False
    if sig.get("match_broken_symlink"):
        return os.path.islink(path) and not os.path.exists(path)
    for suf in sig.get("match_suffix") or []:
        if path.endswith(suf) or base.endswith(suf):
            return True
    for pre in sig.get("match_prefix") or []:
        if base.startswith(pre):
            return True
    for name in sig.get("match_basename") or []:
        if base == name:
            return True
    for needle in sig.get("match_contains") or []:
        if needle in path:
            return True
    docker_type = sig.get("docker_type") or ""
    if docker_type and path.startswith("docker://") and docker_type in path:
        return True
    return False


# Typed alias for readability in helpers.
MappingSig = dict[str, Any]


def classify_path(
    path: str,
    catalog: dict[str, Any],
    *,
    keep_set: set[str] | None = None,
    refuse: list[str] | None = None,
    size_bytes: int = 0,
    broken_symlink: bool | None = None,
) -> dict[str, Any]:
    """Classify one path against signatures (first match in file order).

    Args:
        path: Absolute path or docker:// synthetic id.
        catalog: Loaded catalog.
        keep_set: Default keep-set basenames.
        refuse: Manifest refuse tokens.
        size_bytes: Size for scoring.
        broken_symlink: Optional override (tests).

    Returns:
        Candidate mapping (id may be ``unknown``).
    """
    keep = keep_set or set()
    refuse_list = refuse or []
    real = path
    base = os.path.basename(path)
    if broken_symlink is None and not path.startswith("docker://"):
        broken_symlink = os.path.islink(path) and not os.path.exists(path)
    if base in keep:
        sig = catalog["signatures"].get("keep-set-weight") or _empty_sig()
        return _candidate("keep-set-weight", path, size_bytes, sig)
    for sid, sig in catalog["signatures"].items():
        probe = dict(sig)
        if broken_symlink and sid == "dangling-symlink":
            return _candidate(sid, real, size_bytes, probe)
        if _path_matches(real, probe, keep, refuse_list):
            if sid == "dangling-symlink" and not broken_symlink:
                continue
            if sid == "keep-set-weight":
                continue
            return _candidate(sid, real, size_bytes, probe)
    unknown = _empty_sig()
    unknown["what"] = "Unclassified path"
    unknown["why"] = "No catalog signature matched"
    unknown["leftover_when"] = "manual review"
    unknown["risk"] = "review"
    unknown["reclaim"] = "none"
    unknown["leftover_weight"] = 1
    return _candidate("unknown", real, size_bytes, unknown)


def _candidate(
    sid: str, path: str, size_bytes: int, sig: MappingSig
) -> dict[str, Any]:
    """Build a rankable candidate dict.

    Args:
        sid: Signature id.
        path: Path or docker id.
        size_bytes: Size.
        sig: Signature fields.

    Returns:
        JSON-ready mapping.
    """
    risk = str(sig.get("risk") or "review")
    weight = int(sig.get("leftover_weight") or 0)
    return {
        "id": sid,
        "path": path,
        "size_bytes": int(size_bytes),
        "risk": risk,
        "reclaim": sig.get("reclaim") or "none",
        "what": sig.get("what") or "",
        "why": sig.get("why") or "",
        "leftover_when": sig.get("leftover_when") or "",
        "docker_type": sig.get("docker_type") or "",
        "refuse_if": list(sig.get("refuse_if") or []),
        "score": rank_score(size_bytes, weight, risk),
        "step": "A"
        if risk == "safe"
        else ("C" if risk == "dangerous" else "B"),
    }


def rank_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort by score descending, then size, then path.

    Args:
        rows: Candidate mappings.

    Returns:
        New sorted list.
    """
    return sorted(
        rows,
        key=lambda r: (-float(r.get("score") or 0), -int(r.get("size_bytes") or 0), str(r.get("path") or "")),
    )


def progress_interval_s() -> float:
    """Heartbeat interval from DISK_WIZARD_PROGRESS_INTERVAL (0 disables).

    Falls back to EZ_COMFY_PROGRESS_INTERVAL, then 2.

    Returns:
        Seconds between in-root heartbeats. Default 2.
    """
    raw = os.environ.get("DISK_WIZARD_PROGRESS_INTERVAL")
    if raw is None:
        raw = os.environ.get("EZ_COMFY_PROGRESS_INTERVAL", "2")
    try:
        return float(raw)
    except ValueError:
        return 2.0


def emit_walk_progress(msg: str, *, rewrite: bool = False) -> None:
    """Write a survey progress line to stderr.

    TTY heartbeats rewrite the current line; non-TTY (pipes, CI) always
    emit a full newline so captured logs stay readable.

    Args:
        msg: Body without the ``[ez-comfy]`` prefix.
        rewrite: When True and stderr is a TTY, rewrite the current line.
    """
    _ol_emit(msg, rewrite=rewrite)


def _file_row(path: str) -> dict[str, Any]:
    """JSONL row for one walked path.

    Args:
        path: File or symlink path.

    Returns:
        Mapping with path, size_bytes, broken_symlink.
    """
    broken = os.path.islink(path) and not os.path.exists(path)
    size = 0
    if not broken:
        try:
            size = int(os.path.getsize(path))
        except OSError:
            size = 0
    return {"path": path, "size_bytes": size, "broken_symlink": broken}


def walk_root_files(
    root: str,
    max_depth: int = 6,
    *,
    skip_dirs: frozenset[str] | None = None,
    skip_basenames: frozenset[str] | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield file/symlink rows under root, depth-capped, with skip-dir prune.

    Matches ``find ROOT -maxdepth N \\( -type f -o -type l \\)`` and does not
    follow directory symlinks. Skip dir names are not descended at any depth.

    Args:
        root: Directory to walk.
        max_depth: Inclusive depth (root is 0; files in root are 1).
        skip_dirs: Directory basenames to prune. Default SKIP_DIR_NAMES.
        skip_basenames: File basenames to omit. Default SKIP_BASENAMES.

    Yields:
        JSONL-ready row mappings.
    """
    dirs = skip_dirs if skip_dirs is not None else SKIP_DIR_NAMES
    bases = skip_basenames if skip_basenames is not None else SKIP_BASENAMES
    if max_depth < 1 or not os.path.isdir(root):
        return

    def rec(dirpath: str, depth: int) -> Iterator[dict[str, Any]]:
        child_depth = depth + 1
        if child_depth > max_depth:
            return
        try:
            entries = os.scandir(dirpath)
        except OSError:
            return
        with entries:
            for entry in entries:
                name = entry.name
                try:
                    is_link = entry.is_symlink()
                    is_dir = False if is_link else entry.is_dir(follow_symlinks=False)
                    is_file = False if is_link else entry.is_file(follow_symlinks=False)
                except OSError:
                    continue
                if is_dir:
                    if name in dirs:
                        continue
                    yield from rec(entry.path, child_depth)
                    continue
                if is_link or is_file:
                    if name in bases:
                        continue
                    yield _file_row(entry.path)

    yield from rec(root, 0)


def walk_roots_to_stdout(roots: list[str], max_depth: int) -> int:
    """Walk roots, write JSONL to stdout, progress to stderr.

    Args:
        roots: Directories to scan (missing paths skipped).
        max_depth: Inclusive find-style max depth.

    Returns:
        Number of JSONL rows written.
    """
    total = 0
    interval = progress_interval_s()
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        emit_walk_progress(f"Scanning {root} (max depth {max_depth})…")
        started = time.monotonic()
        count = 0
        last_hb = started
        for row in walk_root_files(root, max_depth):
            print(json.dumps(row, sort_keys=True), flush=False)
            count += 1
            total += 1
            if interval <= 0:
                continue
            now = time.monotonic()
            if count % WALK_PROGRESS_EVERY == 0 or (now - last_hb) >= interval:
                emit_walk_progress(
                    f"  still scanning {root}: {count} paths…",
                    rewrite=True,
                )
                last_hb = now
        sys.stdout.flush()
        elapsed = time.monotonic() - started
        emit_walk_progress(f"  {root}: {count} paths ({elapsed:.1f}s)")
    return total


def _load_keep_refuse(manifest: Path) -> tuple[set[str], list[str]]:
    """Load default keep-set and refuse list from the model manifest.

    Args:
        manifest: config/model-manifest.yaml.

    Returns:
        (keep_set, refuse tokens).
    """
    lib = Path(__file__).resolve().parent
    if str(lib) not in sys.path:
        sys.path.insert(0, str(lib))
    import model_manifest as mm  # noqa: WPS433

    man = mm.load_manifest(manifest)
    return mm.default_keep_set(man), list(man.get("refuse") or [])


def _cli(argv: list[str] | None = None) -> int:
    """CLI: json | classify | rank | walk.

    Args:
        argv: Optional argument list.

    Returns:
        Process status.
    """
    parser = argparse.ArgumentParser(prog="disk_catalog")
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--manifest", default="")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("json")
    p_cl = sub.add_parser("classify")
    p_cl.add_argument("--path", required=True)
    p_cl.add_argument("--size", type=int, default=0)
    p_cl.add_argument("--broken-symlink", action="store_true")
    sub.add_parser("rank")
    p_walk = sub.add_parser("walk")
    p_walk.add_argument("roots", nargs="+")
    p_walk.add_argument("--max-depth", type=int, default=6)
    args = parser.parse_args(argv)
    if args.cmd == "walk":
        walk_roots_to_stdout(list(args.roots), int(args.max_depth))
        return 0
    cat = load_catalog(Path(args.catalog))
    keep: set[str] = set()
    refuse: list[str] = []
    if args.manifest:
        keep, refuse = _load_keep_refuse(Path(args.manifest))
    if args.cmd == "json":
        print(json.dumps(cat, sort_keys=True))
        return 0
    if args.cmd == "classify":
        row = classify_path(
            args.path,
            cat,
            keep_set=keep,
            refuse=refuse,
            size_bytes=args.size,
            broken_symlink=True if args.broken_symlink else None,
        )
        print(json.dumps(row, sort_keys=True))
        return 0
    rows: list[dict[str, Any]] = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        path = str(item.get("path") or "")
        size = int(item.get("size_bytes") or 0)
        rows.append(
            classify_path(
                path,
                cat,
                keep_set=keep,
                refuse=refuse,
                size_bytes=size,
                broken_symlink=item.get("broken_symlink"),
            )
        )
    print(json.dumps(rank_candidates(rows), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())

#!/usr/bin/env python3
"""Restricted YAML loader + classifier for config/disk-catalog.yaml."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

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
    """CLI: json | classify | rank.

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
    args = parser.parse_args(argv)
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

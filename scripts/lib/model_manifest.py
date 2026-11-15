#!/usr/bin/env python3
"""Restricted YAML loader for config/model-manifest.yaml (stdlib only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast

if TYPE_CHECKING:
    from ez_common import Json


class PackRecord(TypedDict):
    """One pack row from the restricted model-manifest schema."""

    default: bool
    """Whether its files are in the default keep-set."""

    retired: bool
    """Whether the pack is retired (still keep-set protected)."""

    superseded_by: str
    """Pack id that replaced this one, or empty."""

    min_gb: int
    """Disk the pack needs, for the download budget."""

    tier_dir: str
    """Model-dir tier the files live under."""

    files: list[str]
    """Basenames the pack owns."""

    shares: list[str]
    """Basenames shared with another pack."""

    cmd: str
    """Operator fetch command, or empty."""

    cleanup: str
    """Cleanup note, or empty."""


class ResearchRecord(TypedDict):
    """One research-lane row from the restricted model-manifest schema.

    Research rows are operator-run exploration candidates. They are never
    fetched by ``download-models`` and never enter the keep-set: only
    ``packs:`` rows feed those, so a token listed here cannot become a
    default download by construction.
    """

    upstream: str
    """Canonical upstream URL, or empty."""

    weights: str
    """Hugging Face repo for the weights, ``none``, or empty."""

    license: str
    """Governing license for the weights, as the vendor names it."""

    use: str
    """What the operator may do with outputs. Required, never empty."""

    gb10: str
    """Whether it runs on one GB10: plausible, marginal, or blocked."""


class Manifest(TypedDict):
    """Parsed config/model-manifest.yaml."""

    schema: int
    """Manifest schema version."""

    refuse: list[str]
    """Tokens that must never appear in a reap plan."""

    research: dict[str, ResearchRecord]
    """Operator-run exploration rows keyed by token."""

    packs: dict[str, PackRecord]
    """Pack rows keyed by pack id."""


def load_manifest(path: Path) -> Manifest:
    """Parse the restricted manifest schema (indent-2 YAML subset).

    Args:
        path: Path to ``config/model-manifest.yaml``.

    Returns:
        Mapping with schema, refuse tokens, research tokens, and packs.
    """
    text = path.read_text(encoding="utf-8")
    refuse: list[str] = []
    research: dict[str, ResearchRecord] = {}
    packs: dict[str, PackRecord] = {}
    section = ""
    pack = ""
    list_key = ""
    schema = 1
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("schema:"):
            schema = int(line.split(":", 1)[1].strip())
            continue
        if line == "refuse:":
            section = "refuse"
            pack = ""
            list_key = ""
            continue
        if line == "research:":
            section = "research"
            pack = ""
            list_key = ""
            continue
        if line == "packs:":
            section = "packs"
            pack = ""
            list_key = ""
            continue
        if section == "refuse" and line.strip().startswith("- "):
            refuse.append(line.strip()[2:].strip())
            continue
        if section == "research":
            if line.startswith("  ") and not line.startswith("    ") and line.strip().endswith(":"):
                pack = line.strip()[:-1]
                research[pack] = {
                    "upstream": "",
                    "weights": "",
                    "license": "",
                    "use": "",
                    "gb10": "",
                }
                continue
            if pack and ":" in line:
                key, _, val = line.strip().partition(":")
                fields = cast("dict[str, Json]", research[pack])
                if key.strip() in fields:
                    fields[key.strip()] = val.strip().strip('"').strip("'")
            continue
        if section == "packs" and line.startswith("  ") and not line.startswith("    ") and line.strip().endswith(":"):
            pack = line.strip()[:-1]
            packs[pack] = {
                "default": False,
                "retired": False,
                "superseded_by": "",
                "min_gb": 0,
                "tier_dir": "",
                "files": [],
                "shares": [],
                "cmd": "",
                "cleanup": "",
            }
            list_key = ""
            continue
        if not pack:
            continue
        stripped = line.strip()
        if stripped in {"files:", "shares:"}:
            list_key = stripped[:-1]
            continue
        if list_key and stripped.startswith("- "):
            bucket = cast("dict[str, Json]", packs[pack])[list_key]
            if isinstance(bucket, list):
                bucket.append(stripped[2:].strip())
            continue
        if ":" in stripped and not stripped.startswith("- "):
            list_key = ""
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key == "default":
                packs[pack]["default"] = val.lower() == "true"
            elif key == "retired":
                packs[pack]["retired"] = val.lower() == "true"
            elif key == "min_gb":
                packs[pack]["min_gb"] = int(val or "0")
            elif key in packs[pack]:
                fields = cast("dict[str, Json]", packs[pack])
                fields[key] = val
    return {"schema": schema, "refuse": refuse, "research": research, "packs": packs}


def research_tokens(manifest: Manifest) -> list[str]:
    """Tokens the operator may keep on disk for local exploration.

    Args:
        manifest: Parsed manifest mapping.

    Returns:
        Research tokens in manifest order.
    """
    return list(manifest.get("research") or {})


def keep_set(manifest: Manifest) -> set[str]:
    """Union of all pack files (live + shares).

    Args:
        manifest: Parsed manifest mapping.

    Returns:
        Basename set from every pack's ``files`` list.
    """
    names: set[str] = set()
    for pack in manifest["packs"].values():
        names.update(pack.get("files") or [])
    return names


def default_keep_set(manifest: Manifest) -> set[str]:
    """Filenames from packs with default: true.

    Args:
        manifest: Parsed manifest mapping.

    Returns:
        Basename set from default packs.
    """
    names: set[str] = set()
    for pack in manifest["packs"].values():
        if pack.get("default"):
            names.update(pack.get("files") or [])
    return names


def _cli(argv: list[str] | None = None) -> int:
    """CLI: keep-set | default-keep-set | refuse | research | research-detail | json | pack.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process status.
    """
    parser = argparse.ArgumentParser(prog="model_manifest")
    parser.add_argument("--manifest", required=True)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("keep-set")
    sub.add_parser("default-keep-set")
    sub.add_parser("refuse")
    sub.add_parser("research")
    sub.add_parser("research-detail")
    sub.add_parser("json")
    p_pack = sub.add_parser("pack")
    p_pack.add_argument("name")
    args = parser.parse_args(argv)
    man = load_manifest(Path(args.manifest))
    if args.cmd == "keep-set":
        for name in sorted(keep_set(man)):
            print(name)
        return 0
    if args.cmd == "default-keep-set":
        for name in sorted(default_keep_set(man)):
            print(name)
        return 0
    if args.cmd == "refuse":
        for name in man["refuse"]:
            print(name)
        return 0
    if args.cmd == "research":
        for name in research_tokens(man):
            print(name)
        return 0
    if args.cmd == "research-detail":
        for token, row in man["research"].items():
            print(f"{token}\t{row['license']}\t{row['use']}")
        return 0
    if args.cmd == "json":
        print(json.dumps(man))
        return 0
    if args.cmd == "pack":
        pack = man["packs"].get(args.name)
        if pack is None:
            print(f"unknown pack {args.name}", file=sys.stderr)
            return 1
        print(json.dumps(pack))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(_cli())

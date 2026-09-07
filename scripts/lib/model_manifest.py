#!/usr/bin/env python3
"""Restricted YAML loader for config/model-manifest.yaml (stdlib only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_manifest(path: Path) -> dict[str, Any]:
    """Parse the restricted manifest schema (indent-2 YAML subset)."""
    text = path.read_text(encoding="utf-8")
    refuse: list[str] = []
    packs: dict[str, dict[str, Any]] = {}
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
        if line == "packs:":
            section = "packs"
            pack = ""
            list_key = ""
            continue
        if section == "refuse" and line.strip().startswith("- "):
            refuse.append(line.strip()[2:].strip())
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
            packs[pack][list_key].append(stripped[2:].strip())
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
                packs[pack][key] = val
    return {"schema": schema, "refuse": refuse, "packs": packs}


def keep_set(manifest: dict[str, Any]) -> set[str]:
    """Union of all pack files (live + shares)."""
    names: set[str] = set()
    for pack in manifest["packs"].values():
        names.update(pack.get("files") or [])
    return names


def default_keep_set(manifest: dict[str, Any]) -> set[str]:
    """Filenames from packs with default: true."""
    names: set[str] = set()
    for pack in manifest["packs"].values():
        if pack.get("default"):
            names.update(pack.get("files") or [])
    return names


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="model_manifest")
    parser.add_argument("--manifest", required=True)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("keep-set")
    sub.add_parser("default-keep-set")
    sub.add_parser("refuse")
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

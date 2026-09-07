#!/usr/bin/env python3
"""Guide-pack schema and fail-closed QC (hermetic: stdlib only).

Operator dumps live under ``${COMFY_OUTPUT_DIR}/guides/<slug>/<shot_id>/``.
Comfy never opens a DCC socket. Size is the LTX VAE grid (1280x704).
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

SCHEMA = "ez.guide.shot.v1"
ENGINES = ("blender", "godot", "opentoonz", "krita", "mixed")
PRINTS = (
    "ltx-iclora-depth",
    "ltx-iclora-canny",
    "wan-vace",
    "wan-flf",
    "wan-denk-cn",
    "dcc-final",
)
PACK_WIDTH = 1280
PACK_HEIGHT = 704
PACK_FRAMES = 120
PACK_FPS = 24
LAYER_KEYS = ("rgb", "depth", "canny", "normal", "id", "pose", "motion", "first", "last")


class GuidePackError(ValueError):
    """Fail-closed guide pack defect."""


def write_solid_png(path: Path, width: int, height: int, rgb: tuple[int, int, int]) -> None:
    """Write a tiny valid RGB PNG (stdlib zlib). Used for fixtures and tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def png_size(path: Path) -> tuple[int, int] | None:
    """Read IHDR width x height, or None."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    if data[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", data[16:24])
    return int(width), int(height)


def _unquote(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1]
    return text


def parse_shot_yaml(text: str) -> dict[str, Any]:
    """Parse restricted ez.guide.shot.v1 YAML (indent-2, no PyYAML)."""
    data: dict[str, Any] = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip() or line.startswith(" "):
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if not key:
            continue
        if val == "":
            continue
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            items: list[Any] = []
            if inner:
                for part in inner.split(","):
                    token = _unquote(part.strip())
                    if not token:
                        continue
                    try:
                        items.append(int(token))
                    except ValueError:
                        items.append(token)
            data[key] = items
            continue
        if val.lower() in {"true", "false"}:
            data[key] = val.lower() == "true"
            continue
        try:
            if "." in val:
                data[key] = float(val)
            else:
                data[key] = int(val)
            continue
        except ValueError:
            data[key] = _unquote(val)
    return data


def load_shot(path: Path) -> dict[str, Any]:
    """Read shot.yaml from a pack directory or file."""
    shot_path = path / "shot.yaml" if path.is_dir() else path
    if not shot_path.is_file():
        raise GuidePackError(f"missing shot.yaml at {shot_path}")
    return parse_shot_yaml(shot_path.read_text(encoding="utf-8"))


def validate_shot(data: dict[str, Any]) -> list[str]:
    """Return defect strings (empty means ok)."""
    defects: list[str] = []
    if data.get("schema") != SCHEMA:
        defects.append(f"schema must be {SCHEMA}, got {data.get('schema')!r}")
    if not str(data.get("slug") or "").strip():
        defects.append("slug is required")
    shot_id = str(data.get("shot_id") or "").strip()
    if not shot_id:
        defects.append("shot_id is required")
    engine = data.get("engine")
    if engine not in ENGINES:
        defects.append(f"engine must be one of {ENGINES}, got {engine!r}")
    print_mode = data.get("print")
    if print_mode not in PRINTS:
        defects.append(f"print must be one of {PRINTS}, got {print_mode!r}")
    frames = data.get("frames")
    if frames != PACK_FRAMES:
        defects.append(f"frames must be {PACK_FRAMES}, got {frames!r}")
    fps = data.get("fps")
    if fps != PACK_FPS:
        defects.append(f"fps must be {PACK_FPS}, got {fps!r}")
    size = data.get("size")
    if isinstance(size, list) and len(size) == 2:
        try:
            width, height = int(size[0]), int(size[1])
        except (TypeError, ValueError):
            width, height = 0, 0
        if (width, height) != (PACK_WIDTH, PACK_HEIGHT):
            defects.append(
                f"size must be [{PACK_WIDTH}, {PACK_HEIGHT}] (not 1280x720), got {size!r}"
            )
    else:
        defects.append(f"size must be [{PACK_WIDTH}, {PACK_HEIGHT}], got {size!r}")
    layers = data.get("layers")
    if not isinstance(layers, list) or not layers:
        defects.append("layers must be a non-empty list")
    else:
        for layer in layers:
            if layer not in LAYER_KEYS:
                defects.append(f"unknown layer {layer!r}")
    return defects


def _count_frames(folder: Path) -> int:
    if not folder.is_dir():
        return 0
    return sum(1 for p in folder.iterdir() if p.suffix.lower() in {".png", ".exr"})


def validate_pack(pack_dir: Path, *, require_full_seq: bool = True) -> list[str]:
    """Fail-closed QC for a dumped pack directory."""
    defects: list[str] = []
    if not pack_dir.is_dir():
        return [f"missing pack directory {pack_dir}"]
    try:
        shot = load_shot(pack_dir)
    except GuidePackError as exc:
        return [str(exc)]
    defects.extend(validate_shot(shot))
    for name in ("first.png", "last.png"):
        path = pack_dir / name
        if not path.is_file():
            defects.append(f"missing {name}")
            continue
        size = png_size(path)
        if size != (PACK_WIDTH, PACK_HEIGHT):
            defects.append(f"{name} size {size} is not {PACK_WIDTH}x{PACK_HEIGHT}")
    layers = shot.get("layers") if isinstance(shot.get("layers"), list) else []
    if "rgb" in layers:
        rgb_n = _count_frames(pack_dir / "rgb")
        if require_full_seq and rgb_n not in {0, PACK_FRAMES}:
            defects.append(f"rgb/ frame count {rgb_n} is not {PACK_FRAMES}")
        if require_full_seq and rgb_n == 0 and not (pack_dir / "clay.mp4").is_file():
            defects.append("missing rgb/ sequence and clay.mp4")
    if "depth" in layers:
        depth_n = _count_frames(pack_dir / "depth")
        if require_full_seq and depth_n not in {0, PACK_FRAMES}:
            defects.append(f"depth/ frame count {depth_n} is not {PACK_FRAMES}")
        if require_full_seq and depth_n == 0 and not (pack_dir / "depth.mp4").is_file():
            defects.append("missing depth/ sequence and depth.mp4")
    return defects


def dump_shot_yaml(data: dict[str, Any]) -> str:
    """Serialize a validated shot dict to restricted YAML."""
    size = data.get("size") or [PACK_WIDTH, PACK_HEIGHT]
    layers = data.get("layers") or ["rgb", "depth", "canny", "first", "last"]
    layer_s = ", ".join(str(x) for x in layers)
    size_s = f"[{int(size[0])}, {int(size[1])}]"
    lines = [
        f"schema: {data.get('schema', SCHEMA)}",
        f"slug: {data.get('slug', '')}",
        f"shot_id: \"{data.get('shot_id', '')}\"",
        f"engine: {data.get('engine', 'blender')}",
        f"print: {data.get('print', 'ltx-iclora-depth')}",
        f"frames: {data.get('frames', PACK_FRAMES)}",
        f"fps: {data.get('fps', PACK_FPS)}",
        f"size: {size_s}",
        f"layers: [{layer_s}]",
    ]
    for key in ("identity_ref", "blend", "camera"):
        if data.get(key):
            lines.append(f"{key}: {data[key]}")
    return "\n".join(lines) + "\n"


def write_shot_yaml(path: Path, data: dict[str, Any]) -> None:
    """Write shot.yaml after validating fields."""
    defects = validate_shot(data)
    if defects:
        raise GuidePackError("; ".join(defects))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_shot_yaml(data), encoding="utf-8")


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="guide_pack")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_val = sub.add_parser("validate", help="validate a pack directory")
    p_val.add_argument("pack")
    p_val.add_argument(
        "--fixture",
        action="store_true",
        help="do not require a full 120-frame sequence (CI fixtures)",
    )
    args = parser.parse_args(argv)
    if args.cmd == "validate":
        defects = validate_pack(Path(args.pack), require_full_seq=not args.fixture)
        if defects:
            print(json.dumps({"ok": False, "defects": defects}))
            return 1
        print(json.dumps({"ok": True, "defects": []}))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(_cli())

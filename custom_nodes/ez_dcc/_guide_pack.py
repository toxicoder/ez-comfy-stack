#!/usr/bin/env python3
"""Vendored fallback of ``scripts/lib/guide_pack.py`` for Comfy runtime.

Used only when ``scripts/lib`` is not on ``PYTHONPATH`` (container copy of
``custom_nodes/ez_dcc``). Keep defects identical; tests compare both modules.
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
STILL_SCHEMA = "ez.guide.still.v1"
ENGINES = ("blender", "godot", "opentoonz", "krita", "mixed")
PRINTS = (
    "ltx-iclora-depth",
    "ltx-iclora-canny",
    "wan-vace",
    "wan-flf",
    "wan-denk-cn",
    "dcc-final",
)
STILL_PRINTS = ("klein-from-clay", "klein-from-canny")
PACK_WIDTH = 1280
PACK_HEIGHT = 704
PACK_FRAMES = 120
PACK_FPS = 24
LAYER_KEYS = ("rgb", "depth", "canny", "normal", "id", "pose", "motion", "first", "last")
STILL_LAYER_KEYS = ("rgb", "depth", "canny", "normal", "first")
STILL_SIZES = (
    (1280, 704),
    (768, 1280),
    (1024, 1280),
    (1024, 1024),
    (1280, 720),
)
STILL_LTX_SIZES = ((1280, 704), (768, 1280))
DEFAULT_LAYERS = ["rgb", "depth", "canny", "first", "last"]
SEQ_OR_MP4 = {
    "rgb": "clay.mp4",
    "depth": "depth.mp4",
    "canny": "canny.mp4",
    "normal": "normal.mp4",
}


def layers_for_print(print_mode: str, *, include_normal: bool = False) -> list[str]:
    """Return Path B dump layers for a named print mode.

    Args:
        print_mode: One of PRINTS.
        include_normal: Append the optional EEVEE normal pass.

    Returns:
        Layer names in dump order.
    """
    layers = list(DEFAULT_LAYERS)
    if include_normal and "normal" not in layers:
        layers.append("normal")
    if print_mode not in PRINTS:
        return layers
    return layers


class GuidePackError(ValueError):
    """Fail-closed guide pack defect."""


def write_rgb_png(path: Path, width: int, height: int, rgb: bytes) -> None:
    """Write an RGB8 PNG (stdlib zlib). Filter none, no ancillary chunks.

    Args:
        path: Destination file.
        width: Pixel width.
        height: Pixel height.
        rgb: Packed RGB bytes, length width*height*3.

    Raises:
        ValueError: Buffer length does not match width*height*3.
    """
    expected = width * height * 3
    if len(rgb) != expected:
        raise ValueError(f"rgb buffer length {len(rgb)} != {expected}")
    path.parent.mkdir(parents=True, exist_ok=True)
    row = width * 3
    raw = b"".join(b"\x00" + rgb[y * row : (y + 1) * row] for y in range(height))
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


def write_solid_png(path: Path, width: int, height: int, rgb: tuple[int, int, int]) -> None:
    """Write a tiny valid RGB PNG (stdlib zlib). Used for fixtures and tests."""
    write_rgb_png(path, width, height, bytes(rgb) * (width * height))


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
        if (width, height) not in {(PACK_WIDTH, PACK_HEIGHT), (768, 1280)}:
            defects.append(
                f"size must be [{PACK_WIDTH}, {PACK_HEIGHT}] or [768, 1280] "
                f"(not 1280x720), got {size!r}"
            )
    else:
        defects.append(
            f"size must be [{PACK_WIDTH}, {PACK_HEIGHT}] or [768, 1280], got {size!r}"
        )
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


def _pack_size(shot: dict[str, Any]) -> tuple[int, int]:
    size = shot.get("size")
    if isinstance(size, list) and len(size) == 2:
        try:
            return int(size[0]), int(size[1])
        except (TypeError, ValueError):
            return PACK_WIDTH, PACK_HEIGHT
    return PACK_WIDTH, PACK_HEIGHT


def _require_seq_or_mp4(
    pack_dir: Path,
    layer: str,
    *,
    require_full_seq: bool,
    frames: int = PACK_FRAMES,
) -> list[str]:
    """Fail-closed sequence or muxed MP4 for one video layer."""
    mp4_name = SEQ_OR_MP4.get(layer)
    if mp4_name is None:
        return []
    count = _count_frames(pack_dir / layer)
    defects: list[str] = []
    if require_full_seq and count not in {0, frames}:
        defects.append(f"{layer}/ frame count {count} is not {frames}")
    if require_full_seq and count == 0 and not (pack_dir / mp4_name).is_file():
        defects.append(f"missing {layer}/ sequence and {mp4_name}")
    return defects


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
    expect_w, expect_h = _pack_size(shot)
    if (expect_w, expect_h) not in {(PACK_WIDTH, PACK_HEIGHT), (768, 1280)}:
        expect_w, expect_h = PACK_WIDTH, PACK_HEIGHT
    for name in ("first.png", "last.png"):
        path = pack_dir / name
        if not path.is_file():
            defects.append(f"missing {name}")
            continue
        size = png_size(path)
        if size != (expect_w, expect_h):
            defects.append(f"{name} size {size} is not {expect_w}x{expect_h}")
    raw_layers = shot.get("layers")
    layers: list[Any] = raw_layers if isinstance(raw_layers, list) else []
    frames = int(shot.get("frames") or PACK_FRAMES)
    for layer in ("rgb", "depth", "canny", "normal"):
        if layer in layers:
            defects.extend(
                _require_seq_or_mp4(
                    pack_dir, layer, require_full_seq=require_full_seq, frames=frames
                )
            )
    return defects


def dump_shot_yaml(data: dict[str, Any]) -> str:
    """Serialize a validated shot dict to restricted YAML."""
    size = data.get("size") or [PACK_WIDTH, PACK_HEIGHT]
    layers = data.get("layers") or list(DEFAULT_LAYERS)
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


def dump_still_yaml(data: dict[str, Any]) -> str:
    """Serialize a validated still dict to restricted YAML."""
    size = data.get("size") or [PACK_WIDTH, PACK_HEIGHT]
    layers = data.get("layers") or ["rgb", "depth", "canny", "first"]
    layer_s = ", ".join(str(x) for x in layers)
    size_s = f"[{int(size[0])}, {int(size[1])}]"
    lines = [
        f"schema: {data.get('schema', STILL_SCHEMA)}",
        f"slug: {data.get('slug', '')}",
        f"plate: {data.get('plate', '')}",
        f"engine: {data.get('engine', 'blender')}",
        f"print: {data.get('print', 'klein-from-clay')}",
        f"size: {size_s}",
        f"layers: [{layer_s}]",
    ]
    for key in ("blend", "camera"):
        if data.get(key):
            lines.append(f"{key}: {data[key]}")
    return "\n".join(lines) + "\n"


def write_still_yaml(path: Path, data: dict[str, Any]) -> None:
    """Write still.yaml after validating fields."""
    defects = validate_still(data)
    if defects:
        raise GuidePackError("; ".join(defects))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_still_yaml(data), encoding="utf-8")


def load_still(path: Path) -> dict[str, Any]:
    """Read still.yaml from a pack directory or file."""
    still_path = path / "still.yaml" if path.is_dir() else path
    if not still_path.is_file():
        raise GuidePackError(f"missing still.yaml at {still_path}")
    return parse_shot_yaml(still_path.read_text(encoding="utf-8"))


def validate_still(data: dict[str, Any]) -> list[str]:
    """Return defect strings for ez.guide.still.v1 (empty means ok)."""
    defects: list[str] = []
    if data.get("schema") != STILL_SCHEMA:
        defects.append(f"schema must be {STILL_SCHEMA}, got {data.get('schema')!r}")
    if not str(data.get("slug") or "").strip():
        defects.append("slug is required")
    if not str(data.get("plate") or "").strip():
        defects.append("plate is required")
    engine = data.get("engine")
    if engine not in ENGINES:
        defects.append(f"engine must be one of {ENGINES}, got {engine!r}")
    print_mode = data.get("print")
    if print_mode not in STILL_PRINTS:
        defects.append(f"print must be one of {STILL_PRINTS}, got {print_mode!r}")
    size = data.get("size")
    if isinstance(size, list) and len(size) == 2:
        try:
            width, height = int(size[0]), int(size[1])
        except (TypeError, ValueError):
            width, height = 0, 0
        if (width, height) not in STILL_SIZES:
            defects.append(
                f"size must be one of {list(STILL_SIZES)} (720/1080 LTX feeders refused), "
                f"got {size!r}"
            )
    else:
        defects.append(f"size must be [W, H] one of {list(STILL_SIZES)}, got {size!r}")
    layers = data.get("layers")
    if not isinstance(layers, list) or not layers:
        defects.append("layers must be a non-empty list")
    else:
        for layer in layers:
            if layer not in STILL_LAYER_KEYS:
                defects.append(f"unknown still layer {layer!r}")
    return defects


def validate_still_pack(pack_dir: Path) -> list[str]:
    """Fail-closed QC for a single-frame still pack."""
    defects: list[str] = []
    if not pack_dir.is_dir():
        return [f"missing still pack directory {pack_dir}"]
    try:
        still = load_still(pack_dir)
    except GuidePackError as exc:
        return [str(exc)]
    defects.extend(validate_still(still))
    size = still.get("size")
    expect: tuple[int, int] | None = None
    if isinstance(size, list) and len(size) == 2:
        try:
            expect = (int(size[0]), int(size[1]))
        except (TypeError, ValueError):
            expect = None
    first = pack_dir / "first.png"
    if not first.is_file():
        defects.append("missing first.png")
    elif expect is not None:
        got = png_size(first)
        if got != expect:
            defects.append(f"first.png size {got} is not {expect[0]}x{expect[1]}")
    raw_layers = still.get("layers")
    layers: list[Any] = raw_layers if isinstance(raw_layers, list) else []
    for layer, filename in (("depth", "depth.png"), ("canny", "canny.png"), ("normal", "normal.png")):
        if layer not in layers:
            continue
        path = pack_dir / filename
        if not path.is_file():
            defects.append(f"missing {filename}")
            continue
        if expect is not None:
            got = png_size(path)
            if got != expect:
                defects.append(f"{filename} size {got} is not {expect[0]}x{expect[1]}")
    return defects


def parse_size_token(token: str) -> tuple[int, int] | None:
    """Parse ``1280x704`` into a size tuple, or None."""
    text = token.lower().replace("×", "x").strip()
    if "x" not in text:
        return None
    left, right = text.split("x", 1)
    try:
        return int(left), int(right)
    except ValueError:
        return None


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
    p_still = sub.add_parser("validate-still", help="validate a still pack directory")
    p_still.add_argument("pack")
    args = parser.parse_args(argv)
    if args.cmd == "validate":
        defects = validate_pack(Path(args.pack), require_full_seq=not args.fixture)
        if defects:
            print(json.dumps({"ok": False, "defects": defects}))
            return 1
        print(json.dumps({"ok": True, "defects": []}))
        return 0
    if args.cmd == "validate-still":
        defects = validate_still_pack(Path(args.pack))
        if defects:
            print(json.dumps({"ok": False, "defects": defects}))
            return 1
        print(json.dumps({"ok": True, "defects": []}))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(_cli())

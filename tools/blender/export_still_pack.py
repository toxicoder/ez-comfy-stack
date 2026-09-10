#!/usr/bin/env python3
"""Blender background dump of an ez.guide.still.v1 plate.

Invoked as: blender [--] scene.blend --background --python this.py -- --out DIR ...
Single-frame Workbench clay + mist depth + outline canny. No Comfy socket.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
_LIB = _REPO / "scripts" / "lib"
for _path in (_LIB, _HERE):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from guide_pack import (  # noqa: E402
    STILL_SCHEMA,
    STILL_SIZES,
    dump_still_yaml,
    parse_size_token,
    validate_still,
)
from workbench_passes import (  # noqa: E402
    camera_document,
    configure_canny,
    configure_clay,
    configure_mist_depth,
    configure_resolution,
    frame_extrinsic,
)

DEFAULT_STILL_LAYERS = ["rgb", "depth", "canny", "first"]


def parse_export_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse argv after Blender's ``--`` separator."""
    raw = list(sys.argv if argv is None else argv)
    if "--" in raw:
        raw = raw[raw.index("--") + 1 :]
    parser = argparse.ArgumentParser(prog="export_still_pack")
    parser.add_argument("--out", required=True)
    parser.add_argument("--film", required=True)
    parser.add_argument("--plate", required=True)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--size", default="", help="WxH token, overrides --width/--height")
    parser.add_argument("--camera", default="")
    parser.add_argument("--engine", default="blender")
    parser.add_argument("--print", dest="print_mode", default="klein-from-clay")
    return parser.parse_args(raw)


def resolve_size(ns: argparse.Namespace) -> tuple[int, int]:
    """Return width, height from --size or --width/--height."""
    if ns.size:
        parsed = parse_size_token(str(ns.size))
        if parsed is None:
            raise SystemExit(f"invalid --size {ns.size!r}")
        return parsed
    return int(ns.width), int(ns.height)


def still_payload(ns: argparse.Namespace, blend: str = "") -> dict[str, Any]:
    """Build ez.guide.still.v1 fields from CLI."""
    width, height = resolve_size(ns)
    data: dict[str, Any] = {
        "schema": STILL_SCHEMA,
        "slug": ns.film,
        "plate": ns.plate,
        "engine": ns.engine,
        "print": ns.print_mode,
        "size": [width, height],
        "layers": list(DEFAULT_STILL_LAYERS),
    }
    if ns.camera:
        data["camera"] = ns.camera
    if blend:
        data["blend"] = blend
    return data


def _render_still(bpy: Any, dest: Path, filename: str) -> Path:
    scene = bpy.context.scene
    dest.mkdir(parents=True, exist_ok=True)
    png = dest / filename
    scene.render.filepath = str(png)
    bpy.ops.render.render(write_still=True)
    written = Path(scene.render.filepath)
    if written.suffix.lower() != ".png":
        candidate = Path(str(scene.render.filepath) + ".png")
        if candidate.is_file():
            written = candidate
    if written != png and written.is_file():
        png.write_bytes(written.read_bytes())
    return png


def export_with_bpy(ns: argparse.Namespace) -> None:
    """Render one clay/depth/canny still using the host bpy module."""
    try:
        import bpy  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit("bpy required (run via host blender --background -P)") from exc

    width, height = resolve_size(ns)
    if (width, height) not in STILL_SIZES:
        raise SystemExit(f"still size {width}x{height} is not in {list(STILL_SIZES)}")

    dest = Path(ns.out)
    dest.mkdir(parents=True, exist_ok=True)
    payload = still_payload(ns, blend=getattr(bpy.data, "filepath", "") or "")
    defects = validate_still(payload)
    if defects:
        raise SystemExit("still.yaml invalid: " + "; ".join(defects))

    scene = bpy.context.scene
    configure_resolution(scene, width, height, 24, 1)
    if ns.camera and ns.camera in bpy.data.objects:
        scene.camera = bpy.data.objects[ns.camera]

    configure_clay(scene)
    clay = _render_still(bpy, dest, "first.png")
    rgb_dir = dest / "rgb"
    rgb_dir.mkdir(parents=True, exist_ok=True)
    (rgb_dir / "0001.png").write_bytes(clay.read_bytes())

    configure_mist_depth(scene.world)
    configure_clay(scene)
    _render_still(bpy, dest, "depth.png")

    configure_canny(scene)
    _render_still(bpy, dest, "canny.png")

    cam = scene.camera
    if cam is not None:
        extra = frame_extrinsic(scene, cam, 1)
        payload_cam = camera_document(
            name=str(getattr(cam, "name", "") or ns.camera or "Camera"),
            frames=1,
            fps=24,
            size=[width, height],
            extrinsics=[extra],
        )
        (dest / "camera.json").write_text(
            json.dumps(payload_cam, indent=2) + "\n", encoding="utf-8"
        )

    (dest / "still.yaml").write_text(dump_still_yaml(payload), encoding="utf-8")


def main() -> int:
    ns = parse_export_args()
    export_with_bpy(ns)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

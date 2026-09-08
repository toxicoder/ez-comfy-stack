#!/usr/bin/env python3
"""Blender background dump of an ez.guide.shot.v1 pack.

Invoked as: blender [--] scene.blend --background --python this.py -- --out DIR ...
Fails closed on size/frames. Workbench clay + mist-style depth. No Comfy socket.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow ``blender --python`` to import the hermetic validator.
_REPO = Path(__file__).resolve().parents[2]
_LIB = _REPO / "scripts" / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from guide_pack import (  # noqa: E402
    PACK_FPS,
    PACK_FRAMES,
    PACK_HEIGHT,
    PACK_WIDTH,
    SCHEMA,
    dump_shot_yaml,
    validate_shot,
)

DEFAULT_LAYERS = ["rgb", "depth", "canny", "first", "last"]


def parse_export_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse argv after Blender's ``--`` separator."""
    raw = list(sys.argv if argv is None else argv)
    if "--" in raw:
        raw = raw[raw.index("--") + 1 :]
    parser = argparse.ArgumentParser(prog="export_guide_pack")
    parser.add_argument("--out", required=True)
    parser.add_argument("--film", required=True)
    parser.add_argument("--shot", required=True)
    parser.add_argument("--frames", type=int, default=PACK_FRAMES)
    parser.add_argument("--width", type=int, default=PACK_WIDTH)
    parser.add_argument("--height", type=int, default=PACK_HEIGHT)
    parser.add_argument("--fps", type=int, default=PACK_FPS)
    parser.add_argument("--camera", default="")
    parser.add_argument("--engine", default="blender")
    parser.add_argument("--print", dest="print_mode", default="ltx-iclora-depth")
    return parser.parse_args(raw)


def shot_payload(ns: argparse.Namespace, blend: str = "") -> dict:
    """Build ez.guide.shot.v1 fields from CLI."""
    data = {
        "schema": SCHEMA,
        "slug": ns.film,
        "shot_id": str(ns.shot),
        "engine": ns.engine,
        "print": ns.print_mode,
        "frames": int(ns.frames),
        "fps": int(ns.fps),
        "size": [int(ns.width), int(ns.height)],
        "layers": list(DEFAULT_LAYERS),
    }
    if ns.camera:
        data["camera"] = ns.camera
    if blend:
        data["blend"] = blend
    return data


def _configure_scene(bpy: object, ns: argparse.Namespace) -> None:
    scene = bpy.context.scene  # type: ignore[attr-defined]
    scene.render.resolution_x = int(ns.width)
    scene.render.resolution_y = int(ns.height)
    scene.render.resolution_percentage = 100
    scene.render.fps = int(ns.fps)
    scene.frame_start = 1
    scene.frame_end = int(ns.frames)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.engine = "BLENDER_WORKBENCH"
    if ns.camera and ns.camera in bpy.data.objects:  # type: ignore[attr-defined]
        scene.camera = bpy.data.objects[ns.camera]  # type: ignore[attr-defined]


def _render_pass(bpy: object, dest: Path, folder: str, ns: argparse.Namespace) -> None:
    scene = bpy.context.scene  # type: ignore[attr-defined]
    out = dest / folder
    out.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(out / "")
    bpy.ops.render.render(animation=True)  # type: ignore[attr-defined]


def export_with_bpy(ns: argparse.Namespace) -> None:
    """Render clay + depth + first/last using the host bpy module."""
    try:
        import bpy  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit("bpy required (run via host blender --background -P)") from exc

    dest = Path(ns.out)
    dest.mkdir(parents=True, exist_ok=True)
    payload = shot_payload(ns, blend=getattr(bpy.data, "filepath", "") or "")
    defects = validate_shot(payload)
    if defects:
        raise SystemExit("shot.yaml invalid: " + "; ".join(defects))

    _configure_scene(bpy, ns)
    scene = bpy.context.scene
    # Clay / unshaded workbench
    _render_pass(bpy, dest, "rgb", ns)
    # Mist-style depth: world mist, near white / far black
    world = scene.world
    if world is not None and hasattr(world, "mist_settings"):
        world.mist_settings.use_mist = True
    depth_dir = dest / "depth"
    depth_dir.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(depth_dir / "")
    bpy.ops.render.render(animation=True)

    first_src = dest / "rgb" / "0001.png"
    last_src = dest / "rgb" / f"{int(ns.frames):04d}.png"
    # Blender may write 0001.png or 0001-0001.png depending on version; copy if present.
    rgb_files = sorted(p for p in (dest / "rgb").glob("*.png"))
    if rgb_files:
        first_src = rgb_files[0]
        last_src = rgb_files[-1]
    if first_src.is_file():
        (dest / "first.png").write_bytes(first_src.read_bytes())
    if last_src.is_file():
        (dest / "last.png").write_bytes(last_src.read_bytes())

    cam = scene.camera
    if cam is not None:
        loc = list(cam.location)
        camera_json = {
            "name": cam.name,
            "pos": [float(loc[0]), float(loc[1]), float(loc[2])],
            "fov": float(getattr(cam.data, "angle_y", 0.0) or getattr(cam.data, "angle", 0.0)),
            "frames": int(ns.frames),
            "fps": int(ns.fps),
            "size": [int(ns.width), int(ns.height)],
        }
        (dest / "camera.json").write_text(json.dumps(camera_json, indent=2) + "\n", encoding="utf-8")

    (dest / "shot.yaml").write_text(dump_shot_yaml(payload), encoding="utf-8")


def main() -> int:
    ns = parse_export_args()
    if ns.frames != PACK_FRAMES:
        print(f"frames must be {PACK_FRAMES}, got {ns.frames}", file=sys.stderr)
        return 1
    if (ns.width, ns.height) not in {(PACK_WIDTH, PACK_HEIGHT), (768, 1280)}:
        print(
            f"size must be {PACK_WIDTH}x{PACK_HEIGHT} (not 1280x720), got {ns.width}x{ns.height}",
            file=sys.stderr,
        )
        return 1
    export_with_bpy(ns)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Blender background dump of an ez.guide.shot.v1 pack.

Invoked as: blender [--] scene.blend --background --python this.py -- --out DIR ...
Fails closed on size/frames. Workbench clay + mist depth + outline canny.
Optional EEVEE normal. No Comfy socket.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Allow ``blender --python`` to import the hermetic validator.
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
_LIB = _REPO / "scripts" / "lib"
for _path in (_LIB, _HERE):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from operator_log import log as ol_log  # noqa: E402
from operator_log import log_step as ol_step  # noqa: E402
from guide_pack import (  # noqa: E402
    PACK_FPS,
    PACK_FRAMES,
    PACK_HEIGHT,
    PACK_WIDTH,
    SCHEMA,
    dump_shot_yaml,
    layers_for_print,
    validate_shot,
)
from workbench_passes import (  # noqa: E402
    camera_document,
    configure_canny,
    configure_clay,
    configure_eevee_normal,
    configure_mist_depth,
    configure_resolution,
    frame_extrinsic,
)

LTX_SIZES = {(PACK_WIDTH, PACK_HEIGHT), (768, 1280)}


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
    parser.add_argument(
        "--include-normal",
        action="store_true",
        help="Try an EEVEE Normal pass. Omit the layer when EEVEE is missing.",
    )
    return parser.parse_args(raw)


def shot_payload(
    ns: argparse.Namespace, blend: str = "", *, include_normal: bool = False
) -> dict[str, Any]:
    """Build ez.guide.shot.v1 fields from CLI."""
    data: dict[str, Any] = {
        "schema": SCHEMA,
        "slug": ns.film,
        "shot_id": str(ns.shot),
        "engine": ns.engine,
        "print": ns.print_mode,
        "frames": int(ns.frames),
        "fps": int(ns.fps),
        "size": [int(ns.width), int(ns.height)],
        "layers": layers_for_print(ns.print_mode, include_normal=include_normal),
    }
    if ns.camera:
        data["camera"] = ns.camera
    if blend:
        data["blend"] = blend
    return data


def _configure_scene(bpy: Any, ns: argparse.Namespace) -> None:
    scene = bpy.context.scene
    configure_resolution(scene, int(ns.width), int(ns.height), int(ns.fps), int(ns.frames))
    configure_clay(scene)
    if ns.camera and ns.camera in bpy.data.objects:
        scene.camera = bpy.data.objects[ns.camera]


def _render_pass(bpy: Any, dest: Path, folder: str) -> None:
    scene = bpy.context.scene
    out = dest / folder
    out.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(out / "")
    bpy.ops.render.render(animation=True)


def _copy_first_last(dest: Path, frames: int) -> None:
    rgb_files = sorted(p for p in (dest / "rgb").glob("*.png"))
    if not rgb_files:
        first_src = dest / "rgb" / "0001.png"
        last_src = dest / "rgb" / f"{int(frames):04d}.png"
        rgb_files = [p for p in (first_src, last_src) if p.is_file()]
    if rgb_files:
        (dest / "first.png").write_bytes(rgb_files[0].read_bytes())
        (dest / "last.png").write_bytes(rgb_files[-1].read_bytes())


def _dump_camera(bpy: Any, dest: Path, ns: argparse.Namespace) -> None:
    scene = bpy.context.scene
    cam = scene.camera
    if cam is None:
        return
    extrinsics = [frame_extrinsic(scene, cam, frame) for frame in range(1, int(ns.frames) + 1)]
    payload = camera_document(
        name=str(getattr(cam, "name", "") or ns.camera or "Camera"),
        frames=int(ns.frames),
        fps=int(ns.fps),
        size=[int(ns.width), int(ns.height)],
        extrinsics=extrinsics,
    )
    (dest / "camera.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def export_with_bpy(ns: argparse.Namespace) -> None:
    """Render clay + depth + canny + first/last using the host bpy module."""
    try:
        import bpy  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit("bpy required (run via host blender --background -P)") from exc

    dest = Path(ns.out)
    dest.mkdir(parents=True, exist_ok=True)
    want_normal = bool(getattr(ns, "include_normal", False))
    payload = shot_payload(
        ns,
        blend=getattr(bpy.data, "filepath", "") or "",
        include_normal=False,
    )
    defects = validate_shot(payload)
    if defects:
        raise SystemExit("shot.yaml invalid: " + "; ".join(defects))

    ol_log(f"guide pack {ns.film} {ns.frames}f {ns.width}x{ns.height}")
    _configure_scene(bpy, ns)
    scene = bpy.context.scene
    ol_step(1, 3, "clay rgb")
    configure_clay(scene)
    _render_pass(bpy, dest, "rgb")

    ol_step(2, 3, "depth")
    configure_mist_depth(scene.world)
    configure_clay(scene)
    _render_pass(bpy, dest, "depth")

    ol_step(3, 3, "canny")
    configure_canny(scene)
    _render_pass(bpy, dest, "canny")

    if want_normal:
        view_layer = getattr(bpy.context, "view_layer", None)
        if configure_eevee_normal(scene, view_layer):
            _render_pass(bpy, dest, "normal")
            payload["layers"] = layers_for_print(ns.print_mode, include_normal=True)
        configure_clay(scene)

    _copy_first_last(dest, int(ns.frames))
    _dump_camera(bpy, dest, ns)
    (dest / "shot.yaml").write_text(dump_shot_yaml(payload), encoding="utf-8")


def main() -> int:
    ns = parse_export_args()
    if ns.frames != PACK_FRAMES:
        print(f"frames must be {PACK_FRAMES}, got {ns.frames}", file=sys.stderr)
        return 1
    if (ns.width, ns.height) not in LTX_SIZES:
        print(
            f"size must be {PACK_WIDTH}x{PACK_HEIGHT} or 768x1280 (not 1280x720), "
            f"got {ns.width}x{ns.height}",
            file=sys.stderr,
        )
        return 1
    export_with_bpy(ns)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

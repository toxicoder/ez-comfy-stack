#!/usr/bin/env python3
"""Blender background dump of an ez.house.views.v1 clay pack.

Invoked as: blender --background --python this.py -- --out DIR --layout FILE
Constructs a Workbench greybox from ez.house.layout.v1. No Comfy socket.
Clay does not need to look good — cameras and adjacency are the product.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[2]
_LIB = _REPO / "scripts" / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from house_layout import (  # noqa: E402
    CLAY_PREFIX,
    ENGINE_BLENDER,
    PACK_HEIGHT,
    PACK_WIDTH,
    PLACE_10_IDS,
    HouseLayoutError,
    clay_copy_name,
    copy_clay_to_input_dir,
    dump_asset_yaml,
    load_layout,
    validate_views_dir,
    view_png_name,
    write_views_yaml,
)

WALL = 0.12
CLAY = (0.55, 0.52, 0.48)
PROP = (0.38, 0.36, 0.34)
GLASS = (0.62, 0.68, 0.72)


def parse_export_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse argv after Blender's ``--`` separator."""
    raw = list(sys.argv if argv is None else argv)
    if "--" in raw:
        raw = raw[raw.index("--") + 1 :]
    parser = argparse.ArgumentParser(prog="export_house_views")
    parser.add_argument("--out", required=True)
    parser.add_argument("--layout", required=True)
    parser.add_argument("--slug", default="")
    parser.add_argument("--engine", default=ENGINE_BLENDER)
    parser.add_argument("--input-dir", default="")
    parser.add_argument("--width", type=int, default=PACK_WIDTH)
    parser.add_argument("--height", type=int, default=PACK_HEIGHT)
    return parser.parse_args(raw)


def _look_at(bpy: Any, obj: Any, target: tuple[float, float, float]) -> None:
    mathutils = __import__("mathutils")
    loc = obj.location
    direction = mathutils.Vector(target) - loc
    if direction.length < 1e-6:
        return
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _new_mesh(
    bpy: Any,
    name: str,
    primitive: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    color: tuple[float, float, float],
) -> Any:
    if primitive == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(
            radius=1.0, depth=2.0, location=location
        )
    elif primitive == "plane":
        bpy.ops.mesh.primitive_plane_add(size=2.0, location=location)
    else:
        bpy.ops.mesh.primitive_cube_add(size=2.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    mat = bpy.data.materials.new(name=f"mat-{name}")
    mat.diffuse_color = (color[0], color[1], color[2], 1.0)
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    obj.color = (color[0], color[1], color[2], 1.0)
    return obj


def _wall_on(
    openings: list[str], wall: str
) -> bool:
    return wall not in openings


def _add_room(bpy: Any, room: dict[str, Any]) -> None:
    x, y, z, sx, sy, sz = room["box"]
    openings = room["openings"]
    rid = room["id"]
    cx = x + sx / 2.0
    cy = y + sy / 2.0
    cz = z + sz / 2.0
    _new_mesh(
        bpy,
        f"{rid}-floor",
        "cube",
        (cx, y + 0.04, cz),
        (sx / 2.0, 0.04, sz / 2.0),
        CLAY,
    )
    if sy > 1.5:
        _new_mesh(
            bpy,
            f"{rid}-ceil",
            "cube",
            (cx, y + sy - 0.04, cz),
            (sx / 2.0, 0.04, sz / 2.0),
            CLAY,
        )
    if _wall_on(openings, "west"):
        _new_mesh(
            bpy,
            f"{rid}-west",
            "cube",
            (x + WALL / 2.0, cy, cz),
            (WALL / 2.0, sy / 2.0, sz / 2.0),
            CLAY,
        )
    if _wall_on(openings, "east"):
        _new_mesh(
            bpy,
            f"{rid}-east",
            "cube",
            (x + sx - WALL / 2.0, cy, cz),
            (WALL / 2.0, sy / 2.0, sz / 2.0),
            CLAY,
        )
    if _wall_on(openings, "south"):
        _new_mesh(
            bpy,
            f"{rid}-south",
            "cube",
            (cx, cy, z + WALL / 2.0),
            (sx / 2.0, sy / 2.0, WALL / 2.0),
            CLAY,
        )
    if _wall_on(openings, "north"):
        color = GLASS if rid == "lounge" else CLAY
        _new_mesh(
            bpy,
            f"{rid}-north",
            "cube",
            (cx, cy, z + sz - WALL / 2.0),
            (sx / 2.0, sy / 2.0, WALL / 2.0),
            color,
        )


def construct_scene(bpy: Any, layout: dict) -> None:
    """Build greybox rooms, props, and named cameras from a layout."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for room in layout["rooms"]:
        _add_room(bpy, room)
    for prop in layout["props"]:
        pose = tuple(prop["pose"])
        size = tuple(prop["size"])
        scale = (size[0] / 2.0, size[1] / 2.0, size[2] / 2.0)
        if prop["primitive"] == "plane":
            scale = (size[0], 1.0, size[2])
        _new_mesh(
            bpy,
            prop["id"],
            prop["primitive"],
            pose,
            scale,
            PROP,
        )
    scene = bpy.context.scene
    for cam in layout["cameras"]:
        data = bpy.data.cameras.new(name=cam["id"])
        data.lens = float(cam["lens_mm"])
        data.sensor_fit = "VERTICAL"
        data.sensor_height = 24.0
        obj = bpy.data.objects.new(cam["id"], data)
        scene.collection.objects.link(obj)
        obj.location = tuple(cam["pos"])
        _look_at(bpy, obj, tuple(cam["look"]))


def _configure_workbench(bpy: Any, width: int, height: int) -> None:
    scene = bpy.context.scene
    scene.render.resolution_x = int(width)
    scene.render.resolution_y = int(height)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "SINGLE"
    shading.single_color = CLAY
    world = scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        scene.world = world
    if hasattr(world, "mist_settings"):
        world.mist_settings.use_mist = True
        world.mist_settings.start = 2.0
        world.mist_settings.depth = 90.0


def _render_camera(
    bpy: Any, camera_name: str, dest: Path, folder: str
) -> Path:
    scene = bpy.context.scene
    obj = bpy.data.objects.get(camera_name)
    if obj is None:
        raise SystemExit(f"missing camera {camera_name}")
    scene.camera = obj
    out_dir = dest / folder
    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / view_png_name(camera_name)
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
    """Construct the greybox, dump clay + depth stills, export GLB."""
    try:
        import bpy  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit("bpy required (run via host blender --background -P)") from exc

    if ns.engine != ENGINE_BLENDER:
        raise SystemExit(f"P0 house-views engine is blender, got {ns.engine}")
    if int(ns.width) != PACK_WIDTH or int(ns.height) != PACK_HEIGHT:
        raise SystemExit(
            f"size must be {PACK_WIDTH}x{PACK_HEIGHT}, got {ns.width}x{ns.height}"
        )

    layout = load_layout(ns.layout)
    slug = ns.slug.strip() or layout["id"]
    dest = Path(ns.out)
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(ns.layout, dest / "layout.yaml")

    construct_scene(bpy, layout)
    _configure_workbench(bpy, ns.width, ns.height)

    for index, cam in enumerate(layout["cameras"]):
        clay = _render_camera(bpy, cam["id"], dest, "views")
        copy_path = dest / clay_copy_name(index)
        if clay.is_file():
            copy_path.write_bytes(clay.read_bytes())
        _render_camera(bpy, cam["id"], dest, "depth")

    mesh_dir = dest / "mesh"
    mesh_dir.mkdir(parents=True, exist_ok=True)
    glb = mesh_dir / "house.glb"
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", export_cameras=True)
    if not glb.is_file():
        raise SystemExit(f"GLB export failed: {glb}")

    write_views_yaml(
        dest / "views.yaml",
        {
            "id": slug,
            "engine": ENGINE_BLENDER,
            "size": [PACK_WIDTH, PACK_HEIGHT],
            "cameras": list(PLACE_10_IDS),
            "layers": ["clay", "depth"],
        },
    )
    (dest / "asset.yaml").write_text(dump_asset_yaml(slug), encoding="utf-8")

    if ns.input_dir:
        copy_clay_to_input_dir(dest, ns.input_dir)

    validate_views_dir(dest, input_dir=ns.input_dir or None)
    print(f"{CLAY_PREFIX} pack ok: {dest}", file=sys.stderr)


def main() -> int:
    ns = parse_export_args()
    try:
        export_with_bpy(ns)
    except HouseLayoutError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

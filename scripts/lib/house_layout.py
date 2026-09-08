#!/usr/bin/env python3
"""ez.house.layout.v1 and ez.house.views.v1 — hermetic stdlib, no bpy.

Greybox floorplans and Instagram 4:5 clay still packs under
COMFY_OUTPUT_DIR/assets/sets/<slug>. Never MODELS_DIR or guides/.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any

from asset_bible import (  # noqa: E402
    KIND_DIRS,
    PIPELINES,
    _EMBEDDED_KEYS,
    _SLUG_RE,
    parse_restricted_yaml,
    refuse_models_dir,
)
from guide_pack import png_size, write_solid_png  # noqa: E402

SCHEMA_LAYOUT = "ez.house.layout.v1"
SCHEMA_VIEWS = "ez.house.views.v1"
PACK_WIDTH = 1024
PACK_HEIGHT = 1280
ENGINE_BLENDER = "blender"
ENGINES = frozenset({ENGINE_BLENDER})
PRIMITIVES = frozenset({"box", "cylinder", "plane"})
OPENING_WALLS = frozenset({"north", "south", "east", "west"})
PLACE_10_IDS = (
    "01-tower",
    "02-foyer",
    "03-lounge",
    "04-kitchen",
    "05-dining",
    "06-bedroom",
    "07-bath",
    "08-terrace",
    "09-drone",
    "10-study",
)
REQUIRED_LAYOUT = (
    "schema",
    "id",
    "kind",
    "pipeline",
    "size",
    "rooms",
    "props",
    "cameras",
)
REQUIRED_CAMERA = ("id", "pos", "look", "lens_mm")
REQUIRED_ROOM = ("id", "box")
REQUIRED_PROP = ("id", "primitive", "pose", "size")
CLAY_PREFIX = "ez_house_clay"
MAX_NUMERIC_ARRAY = 16


class HouseLayoutError(ValueError):
    """Fail-closed house layout / views contract error."""


def clay_copy_name(index: int) -> str:
    """Return ez_house_clay_NN.png for a 0-based camera index.

    Args:
        index: Camera index in PLACE_10_IDS.

    Returns:
        Filename for Comfy LoadImage.
    """
    return f"{CLAY_PREFIX}_{index + 1:02d}.png"


def copy_clay_to_input_dir(
    pack_dir: str | Path, input_dir: str | Path
) -> list[Path]:
    """Copy ez_house_clay_NN.png from a views pack into Comfy's LoadImage folder.

    LoadImage indexes COMFY_OUTPUT_DIR/input (container /inputs), not the
    output root.

    Args:
        pack_dir: assets/sets/<slug> directory that already has clay copies.
        input_dir: Host COMFY_OUTPUT_DIR/input (container /inputs).

    Returns:
        Paths written under input_dir, in place_10 order.

    Raises:
        HouseLayoutError: A pack copy is missing, or input_dir is under MODELS_DIR.
    """
    dest = Path(pack_dir)
    target = refuse_output_dir(input_dir)
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for index in range(len(PLACE_10_IDS)):
        name = clay_copy_name(index)
        src = dest / name
        if not src.is_file():
            raise HouseLayoutError(f"missing clay copy {src}")
        out = target / name
        shutil.copy2(src, out)
        written.append(out)
    return written


def view_png_name(camera_id: str) -> str:
    """Return <camera-id>.png.

    Args:
        camera_id: PLACE_10 id.

    Returns:
        Filename under views/ or depth/.
    """
    return f"{camera_id}.png"


def refuse_output_dir(path: str | Path) -> Path:
    """Refuse MODELS_DIR targets; wrap as HouseLayoutError.

    Args:
        path: Candidate dump directory.

    Returns:
        Resolved path.

    Raises:
        HouseLayoutError: Under MODELS_DIR.
    """
    try:
        return refuse_models_dir(path)
    except Exception as exc:
        raise HouseLayoutError(str(exc)) from exc


def _require_slug(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SLUG_RE.fullmatch(value):
        raise HouseLayoutError(f"{field} must be a lowercase slug, got {value!r}")
    return value


def _require_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or not value.replace("-", "").isalnum():
        raise HouseLayoutError(f"{field} must be a hyphenated id, got {value!r}")
    if value != value.lower():
        raise HouseLayoutError(f"{field} must be lowercase, got {value!r}")
    return value


def _vec(value: Any, field: str, length: int) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise HouseLayoutError(f"{field} must be a list of {length} numbers")
    out: list[float] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise HouseLayoutError(f"{field} must be numeric, got {item!r}")
        out.append(float(item))
    return out


def _refuse_embedded(value: Any, loc: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in _EMBEDDED_KEYS:
                raise HouseLayoutError(
                    f"layout must not embed {key!r} at {loc}; instance slugs only"
                )
            _refuse_embedded(item, f"{loc}.{key}")
        return
    if isinstance(value, list):
        if len(value) > MAX_NUMERIC_ARRAY and all(
            isinstance(item, (int, float)) and not isinstance(item, bool)
            for item in value
        ):
            raise HouseLayoutError(f"refusing packed numeric array at {loc}")
        for idx, item in enumerate(value):
            _refuse_embedded(item, f"{loc}[{idx}]")
        return
    if isinstance(value, str):
        lowered = value.lower()
        if value.startswith("data:") and "base64" in lowered:
            raise HouseLayoutError(f"refusing data: URI base64 mesh bytes at {loc}")
        if "base64" in lowered and len(value) > 128:
            raise HouseLayoutError(f"refusing embedded base64 at {loc}")


def _validate_room(item: Any, index: int) -> dict[str, Any]:
    loc = f"rooms[{index}]"
    if not isinstance(item, dict):
        raise HouseLayoutError(f"{loc} must be a mapping")
    missing = [field for field in REQUIRED_ROOM if field not in item]
    if missing:
        raise HouseLayoutError(f"{loc} missing {', '.join(missing)}")
    openings = item.get("openings") or []
    if not isinstance(openings, list):
        raise HouseLayoutError(f"{loc}.openings must be a list")
    walls: list[str] = []
    for wall in openings:
        if wall not in OPENING_WALLS:
            raise HouseLayoutError(f"{loc}.openings unknown wall {wall!r}")
        walls.append(str(wall))
    return {
        "id": _require_id(item["id"], f"{loc}.id"),
        "box": _vec(item["box"], f"{loc}.box", 6),
        "openings": walls,
    }


def _validate_prop(item: Any, index: int) -> dict[str, Any]:
    loc = f"props[{index}]"
    if not isinstance(item, dict):
        raise HouseLayoutError(f"{loc} must be a mapping")
    missing = [field for field in REQUIRED_PROP if field not in item]
    if missing:
        raise HouseLayoutError(f"{loc} missing {', '.join(missing)}")
    primitive = item["primitive"]
    if primitive not in PRIMITIVES:
        raise HouseLayoutError(
            f"{loc}.primitive must be one of {sorted(PRIMITIVES)}, got {primitive!r}"
        )
    ref = item.get("ref")
    if ref is not None:
        ref = _require_slug(ref, f"{loc}.ref")
    room = item.get("room")
    if room is not None:
        room = _require_id(room, f"{loc}.room")
    return {
        "id": _require_id(item["id"], f"{loc}.id"),
        "primitive": primitive,
        "pose": _vec(item["pose"], f"{loc}.pose", 3),
        "size": _vec(item["size"], f"{loc}.size", 3),
        "room": room,
        "ref": ref,
    }


def _validate_camera(item: Any, index: int, expected_id: str) -> dict[str, Any]:
    loc = f"cameras[{index}]"
    if not isinstance(item, dict):
        raise HouseLayoutError(f"{loc} must be a mapping")
    missing = [field for field in REQUIRED_CAMERA if field not in item]
    if missing:
        raise HouseLayoutError(f"{loc} missing {', '.join(missing)}")
    cam_id = _require_id(item["id"], f"{loc}.id")
    if cam_id != expected_id:
        raise HouseLayoutError(
            f"{loc}.id must be {expected_id}, got {cam_id!r} (place_10 order)"
        )
    lens = item["lens_mm"]
    if isinstance(lens, bool) or not isinstance(lens, (int, float)):
        raise HouseLayoutError(f"{loc}.lens_mm must be a number")
    lens_i = int(lens)
    if lens_i not in {24, 35}:
        raise HouseLayoutError(f"{loc}.lens_mm must be 24 or 35, got {lens!r}")
    label = item.get("label")
    if label is not None and (not isinstance(label, str) or not label.strip()):
        raise HouseLayoutError(f"{loc}.label must be a non-empty string")
    return {
        "id": cam_id,
        "pos": _vec(item["pos"], f"{loc}.pos", 3),
        "look": _vec(item["look"], f"{loc}.look", 3),
        "lens_mm": lens_i,
        "label": str(label).strip() if label else expected_id,
    }


def validate_layout(data: Any) -> dict[str, Any]:
    """Validate an ez.house.layout.v1 mapping.

    Args:
        data: Parsed YAML object.

    Returns:
        Normalized layout dict.

    Raises:
        HouseLayoutError: Missing/invalid fields.
    """
    if not isinstance(data, dict):
        raise HouseLayoutError("layout.yaml must be a mapping")
    _refuse_embedded(data, "layout")
    missing = [field for field in REQUIRED_LAYOUT if field not in data]
    if missing:
        raise HouseLayoutError(f"missing required fields: {', '.join(missing)}")
    if data["schema"] != SCHEMA_LAYOUT:
        raise HouseLayoutError(
            f"schema must be {SCHEMA_LAYOUT}, got {data['schema']!r}"
        )
    layout_id = _require_slug(data["id"], "id")
    kind = data["kind"]
    if kind != "set":
        raise HouseLayoutError(f"kind must be set, got {kind!r}")
    if kind not in KIND_DIRS:
        raise HouseLayoutError(f"unknown kind {kind!r}")
    pipeline = data["pipeline"]
    if pipeline != "bpy-primitive":
        raise HouseLayoutError(
            f"pipeline must be bpy-primitive, got {pipeline!r} "
            f"(allowed asset pipelines: {sorted(PIPELINES)})"
        )
    size = _vec(data["size"], "size", 2)
    if [int(size[0]), int(size[1])] != [PACK_WIDTH, PACK_HEIGHT]:
        raise HouseLayoutError(
            f"size must be [{PACK_WIDTH}, {PACK_HEIGHT}] (Instagram 4:5), got {size}"
        )
    rooms_raw = data["rooms"]
    if not isinstance(rooms_raw, list) or not rooms_raw:
        raise HouseLayoutError("rooms must be a non-empty list")
    rooms = [_validate_room(item, i) for i, item in enumerate(rooms_raw)]
    props_raw = data["props"]
    if not isinstance(props_raw, list):
        raise HouseLayoutError("props must be a list")
    props = [_validate_prop(item, i) for i, item in enumerate(props_raw)]
    cameras_raw = data["cameras"]
    if not isinstance(cameras_raw, list) or len(cameras_raw) != len(PLACE_10_IDS):
        raise HouseLayoutError(
            f"cameras must list all {len(PLACE_10_IDS)} place_10 ids in order"
        )
    cameras = [
        _validate_camera(item, i, PLACE_10_IDS[i])
        for i, item in enumerate(cameras_raw)
    ]
    hdri = data.get("hdri")
    if hdri is not None and not isinstance(hdri, str):
        raise HouseLayoutError("hdri must be a string or null")
    return {
        "schema": SCHEMA_LAYOUT,
        "id": layout_id,
        "kind": "set",
        "pipeline": "bpy-primitive",
        "size": [PACK_WIDTH, PACK_HEIGHT],
        "rooms": rooms,
        "props": props,
        "cameras": cameras,
        "hdri": hdri if isinstance(hdri, str) else None,
    }


def load_layout(path: str | Path) -> dict[str, Any]:
    """Parse and validate a layout YAML file.

    Args:
        path: Path to YAML.

    Returns:
        Normalized layout.

    Raises:
        HouseLayoutError: Parse/validate failure.
        OSError: Unreadable file.
    """
    text = Path(path).read_text(encoding="utf-8")
    try:
        parsed = parse_restricted_yaml(text)
    except Exception as exc:
        raise HouseLayoutError(str(exc)) from exc
    return validate_layout(parsed)


def dump_views_yaml(data: dict[str, Any]) -> str:
    """Serialize ez.house.views.v1 to restricted YAML.

    Args:
        data: Validated views mapping.

    Returns:
        YAML document text.
    """
    cameras = data.get("cameras") or list(PLACE_10_IDS)
    cam_s = ", ".join(str(item) for item in cameras)
    layers = data.get("layers") or ["clay", "depth"]
    layer_s = ", ".join(str(item) for item in layers)
    size = data.get("size") or [PACK_WIDTH, PACK_HEIGHT]
    return (
        f"schema: {data.get('schema', SCHEMA_VIEWS)}\n"
        f"id: {data['id']}\n"
        f"engine: {data.get('engine', ENGINE_BLENDER)}\n"
        f"size: [{int(size[0])}, {int(size[1])}]\n"
        f"cameras: [{cam_s}]\n"
        f"layers: [{layer_s}]\n"
    )


def validate_views(data: Any) -> dict[str, Any]:
    """Validate an ez.house.views.v1 mapping.

    Args:
        data: Parsed YAML object.

    Returns:
        Normalized views dict.

    Raises:
        HouseLayoutError: Invalid fields.
    """
    if not isinstance(data, dict):
        raise HouseLayoutError("views.yaml must be a mapping")
    if data.get("schema") != SCHEMA_VIEWS:
        raise HouseLayoutError(
            f"schema must be {SCHEMA_VIEWS}, got {data.get('schema')!r}"
        )
    views_id = _require_slug(data.get("id"), "id")
    engine = data.get("engine", ENGINE_BLENDER)
    if engine not in ENGINES:
        raise HouseLayoutError(f"engine must be blender, got {engine!r}")
    size = _vec(data.get("size"), "size", 2)
    if [int(size[0]), int(size[1])] != [PACK_WIDTH, PACK_HEIGHT]:
        raise HouseLayoutError(
            f"size must be [{PACK_WIDTH}, {PACK_HEIGHT}], got {size}"
        )
    cameras = data.get("cameras")
    if not isinstance(cameras, list) or [str(c) for c in cameras] != list(PLACE_10_IDS):
        raise HouseLayoutError("cameras must be the place_10 ids in order")
    layers = data.get("layers") or ["clay", "depth"]
    if not isinstance(layers, list) or not all(isinstance(x, str) for x in layers):
        raise HouseLayoutError("layers must be a list of strings")
    return {
        "schema": SCHEMA_VIEWS,
        "id": views_id,
        "engine": ENGINE_BLENDER,
        "size": [PACK_WIDTH, PACK_HEIGHT],
        "cameras": list(PLACE_10_IDS),
        "layers": list(layers),
    }


def load_views(path: str | Path) -> dict[str, Any]:
    """Parse and validate views.yaml.

    Args:
        path: Path to YAML.

    Returns:
        Normalized views dict.
    """
    text = Path(path).read_text(encoding="utf-8")
    try:
        parsed = parse_restricted_yaml(text)
    except Exception as exc:
        raise HouseLayoutError(str(exc)) from exc
    return validate_views(parsed)


def write_views_yaml(path: Path, data: dict[str, Any]) -> None:
    """Write views.yaml after validating.

    Args:
        path: Destination file.
        data: Views mapping.
    """
    payload = validate_views(
        {
            "schema": SCHEMA_VIEWS,
            "id": data["id"],
            "engine": data.get("engine", ENGINE_BLENDER),
            "size": data.get("size", [PACK_WIDTH, PACK_HEIGHT]),
            "cameras": data.get("cameras", list(PLACE_10_IDS)),
            "layers": data.get("layers", ["clay", "depth"]),
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_views_yaml(payload), encoding="utf-8")


def dump_asset_yaml(slug: str) -> str:
    """Minimal ez.asset.v1 record for a dumped set.

    Args:
        slug: Set id.

    Returns:
        Restricted YAML text.
    """
    return (
        "schema: ez.asset.v1\n"
        f"id: {slug}\n"
        "kind: set\n"
        'prompt: "Workbench greybox of one place (Instagram 4:5 clay views)"\n'
        "seed: 42\n"
        "pipeline: bpy-primitive\n"
        "parent: null\n"
        "takes: [v001]\n"
        "files: {preview, hero_glb, views}\n"
        "tags: [set, house, clay]\n"
        "license: operator-output\n"
        "ready: true\n"
    )


def validate_views_dir(
    pack_dir: str | Path,
    *,
    require_glb: bool = True,
    require_depth: bool = True,
    input_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Fail-closed QC of a house-views dump.

    Args:
        pack_dir: assets/sets/<slug> directory.
        require_glb: Require mesh/house.glb.
        require_depth: Require depth/<id>.png for each camera.
        input_dir: When set, require ez_house_clay_NN.png in Comfy LoadImage input/.

    Returns:
        Validated views mapping.

    Raises:
        HouseLayoutError: Size, missing files, or schema defects.
    """
    dest = Path(pack_dir)
    if not dest.is_dir():
        raise HouseLayoutError(f"not a directory: {dest}")
    views_path = dest / "views.yaml"
    if not views_path.is_file():
        raise HouseLayoutError(f"missing {views_path}")
    views = load_views(views_path)
    layout_path = dest / "layout.yaml"
    if layout_path.is_file():
        load_layout(layout_path)
    for index, cam_id in enumerate(PLACE_10_IDS):
        clay = dest / "views" / view_png_name(cam_id)
        if not clay.is_file():
            raise HouseLayoutError(f"missing clay {clay}")
        size = png_size(clay)
        if size != (PACK_WIDTH, PACK_HEIGHT):
            raise HouseLayoutError(
                f"clay {clay.name} size {size} is not {PACK_WIDTH}x{PACK_HEIGHT}"
            )
        if require_depth:
            depth = dest / "depth" / view_png_name(cam_id)
            if not depth.is_file():
                raise HouseLayoutError(f"missing depth {depth}")
            dsize = png_size(depth)
            if dsize != (PACK_WIDTH, PACK_HEIGHT):
                raise HouseLayoutError(
                    f"depth {depth.name} size {dsize} is not {PACK_WIDTH}x{PACK_HEIGHT}"
                )
        copy_name = clay_copy_name(index)
        copied = dest / copy_name
        if copied.is_file():
            csize = png_size(copied)
            if csize != (PACK_WIDTH, PACK_HEIGHT):
                raise HouseLayoutError(
                    f"{copy_name} size {csize} is not {PACK_WIDTH}x{PACK_HEIGHT}"
                )
    if input_dir is not None:
        input_root = Path(input_dir)
        if not input_root.is_dir():
            raise HouseLayoutError(f"missing LoadImage input dir {input_root}")
        for index in range(len(PLACE_10_IDS)):
            name = clay_copy_name(index)
            plate = input_root / name
            if not plate.is_file():
                raise HouseLayoutError(f"missing LoadImage input {plate}")
            isize = png_size(plate)
            if isize != (PACK_WIDTH, PACK_HEIGHT):
                raise HouseLayoutError(
                    f"{name} in input dir size {isize} is not {PACK_WIDTH}x{PACK_HEIGHT}"
                )
    if require_glb:
        glb = dest / "mesh" / "house.glb"
        if not glb.is_file() or glb.stat().st_size < 1:
            raise HouseLayoutError(f"missing mesh {glb}")
    return views


def write_fixture_pack(dest: str | Path, *, slug: str = "lab-penthouse") -> Path:
    """Write 1024x1280 solid PNGs + views.yaml for tests.

    Args:
        dest: Pack directory.
        slug: Set id.

    Returns:
        Destination path.
    """
    root = Path(dest)
    views_dir = root / "views"
    depth_dir = root / "depth"
    views_dir.mkdir(parents=True, exist_ok=True)
    depth_dir.mkdir(parents=True, exist_ok=True)
    clay_rgb = (160, 150, 140)
    depth_rgb = (200, 200, 200)
    for index, cam_id in enumerate(PLACE_10_IDS):
        name = view_png_name(cam_id)
        write_solid_png(views_dir / name, PACK_WIDTH, PACK_HEIGHT, clay_rgb)
        write_solid_png(depth_dir / name, PACK_WIDTH, PACK_HEIGHT, depth_rgb)
        write_solid_png(
            root / clay_copy_name(index), PACK_WIDTH, PACK_HEIGHT, clay_rgb
        )
    write_views_yaml(
        root / "views.yaml",
        {
            "id": slug,
            "engine": ENGINE_BLENDER,
            "size": [PACK_WIDTH, PACK_HEIGHT],
            "cameras": list(PLACE_10_IDS),
            "layers": ["clay", "depth"],
        },
    )
    return root


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="house_layout")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_val = sub.add_parser("validate", help="validate a layout YAML")
    p_val.add_argument("path")
    p_views = sub.add_parser("validate-views", help="QC a views dump directory")
    p_views.add_argument("path")
    p_views.add_argument("--fixture", action="store_true")
    p_fix = sub.add_parser("fixture", help="write solid PNG placeholders")
    p_fix.add_argument("path")
    p_fix.add_argument("--slug", default="lab-penthouse")
    p_copy = sub.add_parser(
        "copy-inputs",
        help="copy ez_house_clay_NN.png into Comfy LoadImage input/",
    )
    p_copy.add_argument("pack")
    p_copy.add_argument("input_dir")
    ns = parser.parse_args(argv)
    try:
        if ns.cmd == "validate":
            layout = load_layout(ns.path)
            print(f"ok {layout['id']} cameras={len(layout['cameras'])}")
            return 0
        if ns.cmd == "validate-views":
            validate_views_dir(
                ns.path, require_glb=not ns.fixture, require_depth=not ns.fixture
            )
            print(f"ok {ns.path}")
            return 0
        if ns.cmd == "copy-inputs":
            written = copy_clay_to_input_dir(ns.pack, ns.input_dir)
            print(f"ok {len(written)} clay plates → {ns.input_dir}")
            return 0
        write_fixture_pack(ns.path, slug=ns.slug)
        print(f"wrote fixture {ns.path}")
        return 0
    except (HouseLayoutError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli())

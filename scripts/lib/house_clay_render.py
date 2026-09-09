#!/usr/bin/env python3
"""Stdlib greybox renderer for ez.house.layout.v1 cameras.

No numpy, bpy, or Pillow. Renders thin room walls and prop AABBs from a
pinhole camera into a 1024x1280 RGB PNG for Comfy LoadImage seed plates.
"""

from __future__ import annotations

import math
from array import array
from pathlib import Path
from typing import Any, Mapping, Sequence

from guide_pack import write_rgb_png

PACK_WIDTH = 1024
PACK_HEIGHT = 1280
RENDER_WIDTH = 256
RENDER_HEIGHT = 320
NEAR = 0.08
WALL = 0.12
SENSOR_MM = 36.0
SKY_TOP = (168, 184, 198)
SKY_HORIZON = (196, 188, 178)
CLAY = (168, 158, 148)
GLASS = (176, 188, 196)
PROP = (118, 110, 104)
LIGHT = (0.35, 0.82, 0.38)
Vec3 = tuple[float, float, float]
Rgb = tuple[int, int, int]


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(a: Vec3) -> Vec3:
    length = math.sqrt(_dot(a, a))
    if length < 1e-9:
        return (0.0, 1.0, 0.0)
    return _scale(a, 1.0 / length)


def _shade(rgb: Rgb, normal: Vec3) -> Rgb:
    light = _norm(LIGHT)
    ndotl = max(0.42, min(1.0, _dot(_norm(normal), light)))
    return (
        min(255, int(rgb[0] * ndotl)),
        min(255, int(rgb[1] * ndotl)),
        min(255, int(rgb[2] * ndotl)),
    )


def _camera_basis(pos: Vec3, look: Vec3) -> tuple[Vec3, Vec3, Vec3]:
    forward = _norm(_sub(look, pos))
    world_up = (0.0, 1.0, 0.0)
    right = _cross(forward, world_up)
    if math.sqrt(_dot(right, right)) < 1e-6:
        right = _cross(forward, (1.0, 0.0, 0.0))
        if math.sqrt(_dot(right, right)) < 1e-6:
            right = (1.0, 0.0, 0.0)
        else:
            right = _norm(right)
    else:
        right = _norm(right)
    up = _norm(_cross(right, forward))
    return right, up, forward


def _project(
    point: Vec3,
    pos: Vec3,
    right: Vec3,
    up: Vec3,
    forward: Vec3,
    tan_x: float,
    tan_y: float,
    width: int,
    height: int,
) -> tuple[float, float, float] | None:
    cam = _sub(point, pos)
    z = _dot(cam, forward)
    if z <= NEAR:
        return None
    x = _dot(cam, right) / (z * tan_x)
    y = _dot(cam, up) / (z * tan_y)
    u = (x * 0.5 + 0.5) * width
    v = (0.5 - y * 0.5) * height
    return (u, v, z)


def _fill_triangle(
    pixels: bytearray,
    zbuf: array[float],
    width: int,
    height: int,
    a: tuple[float, float, float],
    b: tuple[float, float, float],
    c: tuple[float, float, float],
    color: Rgb,
) -> None:
    ax, ay, az = a
    bx, by, bz = b
    cx, cy, cz = c
    denom = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(denom) < 1e-8:
        return
    if denom < 0:
        bx, by, bz, cx, cy, cz = cx, cy, cz, bx, by, bz
        denom = -denom
    minx = max(0, int(math.floor(min(ax, bx, cx))))
    maxx = min(width - 1, int(math.ceil(max(ax, bx, cx))))
    miny = max(0, int(math.floor(min(ay, by, cy))))
    maxy = min(height - 1, int(math.ceil(max(ay, by, cy))))
    inv = 1.0 / denom
    cr, cg, cb = color
    for py in range(miny, maxy + 1):
        y = py + 0.5
        row = py * width
        for px in range(minx, maxx + 1):
            x = px + 0.5
            w0 = ((by - cy) * (x - cx) + (cx - bx) * (y - cy)) * inv
            w1 = ((cy - ay) * (x - cx) + (ax - cx) * (y - cy)) * inv
            w2 = 1.0 - w0 - w1
            if w0 < -1e-5 or w1 < -1e-5 or w2 < -1e-5:
                continue
            z = w0 * az + w1 * bz + w2 * cz
            if z <= NEAR:
                continue
            idx = row + px
            if z >= zbuf[idx]:
                continue
            zbuf[idx] = z
            off = idx * 3
            pixels[off] = cr
            pixels[off + 1] = cg
            pixels[off + 2] = cb


def _aabb_faces(mn: Vec3, mx: Vec3) -> list[tuple[tuple[Vec3, Vec3, Vec3, Vec3], Vec3]]:
    x0, y0, z0 = mn
    x1, y1, z1 = mx
    return [
        (
            ((x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)),
            (-1.0, 0.0, 0.0),
        ),
        (
            ((x1, y0, z1), (x1, y1, z1), (x1, y1, z0), (x1, y0, z0)),
            (1.0, 0.0, 0.0),
        ),
        (
            ((x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)),
            (0.0, -1.0, 0.0),
        ),
        (
            ((x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)),
            (0.0, 1.0, 0.0),
        ),
        (
            ((x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z0)),
            (0.0, 0.0, -1.0),
        ),
        (
            ((x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1)),
            (0.0, 0.0, 1.0),
        ),
    ]


def _center_size_box(center: Sequence[float], size: Sequence[float]) -> tuple[Vec3, Vec3]:
    cx, cy, cz = float(center[0]), float(center[1]), float(center[2])
    sx, sy, sz = float(size[0]), float(size[1]), float(size[2])
    return (
        (cx - sx / 2.0, cy - sy / 2.0, cz - sz / 2.0),
        (cx + sx / 2.0, cy + sy / 2.0, cz + sz / 2.0),
    )


def layout_boxes(layout: Mapping[str, Any]) -> list[tuple[Vec3, Vec3, Rgb]]:
    """Return (min, max, rgb) AABBs matching the Blender greybox (thin walls).

    Args:
        layout: Validated ez.house.layout.v1 mapping.

    Returns:
        Paintable boxes for rooms (floor/ceil/walls) and props.
    """
    boxes: list[tuple[Vec3, Vec3, Rgb]] = []
    for room in layout.get("rooms") or []:
        x, y, z, sx, sy, sz = (float(v) for v in room["box"])
        openings = {str(item) for item in (room.get("openings") or [])}
        rid = str(room.get("id") or "")
        cx = x + sx / 2.0
        cy = y + sy / 2.0
        cz = z + sz / 2.0
        boxes.append(_center_size_box((cx, y + 0.04, cz), (sx, 0.08, sz)) + (CLAY,))
        if sy > 1.5:
            boxes.append(
                _center_size_box((cx, y + sy - 0.04, cz), (sx, 0.08, sz)) + (CLAY,)
            )
        if "west" not in openings:
            boxes.append(
                _center_size_box((x + WALL / 2.0, cy, cz), (WALL, sy, sz)) + (CLAY,)
            )
        if "east" not in openings:
            boxes.append(
                _center_size_box((x + sx - WALL / 2.0, cy, cz), (WALL, sy, sz))
                + (CLAY,)
            )
        if "south" not in openings:
            boxes.append(
                _center_size_box((cx, cy, z + WALL / 2.0), (sx, sy, WALL)) + (CLAY,)
            )
        if "north" not in openings:
            color = GLASS if rid == "lounge" else CLAY
            boxes.append(
                _center_size_box((cx, cy, z + sz - WALL / 2.0), (sx, sy, WALL))
                + (color,)
            )
    for prop in layout.get("props") or []:
        boxes.append(_center_size_box(prop["pose"], prop["size"]) + (PROP,))
    return boxes


def _upsample_nearest(
    src: bytes, sw: int, sh: int, dw: int, dh: int
) -> bytes:
    out = bytearray(dw * dh * 3)
    for y in range(dh):
        sy = (y * sh) // dh
        src_row = sy * sw * 3
        dst_row = y * dw * 3
        for x in range(dw):
            sx = (x * sw) // dw
            si = src_row + sx * 3
            di = dst_row + x * 3
            out[di : di + 3] = src[si : si + 3]
    return bytes(out)


def _fill_sky(pixels: bytearray, width: int, height: int) -> None:
    denom = max(height - 1, 1)
    for y in range(height):
        t = y / denom
        r = int(SKY_TOP[0] * (1.0 - t) + SKY_HORIZON[0] * t)
        g = int(SKY_TOP[1] * (1.0 - t) + SKY_HORIZON[1] * t)
        b = int(SKY_TOP[2] * (1.0 - t) + SKY_HORIZON[2] * t)
        row = y * width * 3
        for x in range(width):
            off = row + x * 3
            pixels[off] = r
            pixels[off + 1] = g
            pixels[off + 2] = b


def render_clay_rgb(
    layout: Mapping[str, Any],
    camera_index: int,
    *,
    width: int = RENDER_WIDTH,
    height: int = RENDER_HEIGHT,
) -> bytes:
    """Rasterize one camera into packed RGB bytes.

    Args:
        layout: Validated layout (cameras, rooms, props).
        camera_index: 0-based place_10 index.
        width: Internal raster width.
        height: Internal raster height.

    Returns:
        Packed RGB buffer of length width*height*3.

    Raises:
        ValueError: Camera index out of range.
    """
    cameras = list(layout.get("cameras") or [])
    if camera_index < 0 or camera_index >= len(cameras):
        raise ValueError(f"camera_index {camera_index} out of range")
    cam = cameras[camera_index]
    pos = (float(cam["pos"][0]), float(cam["pos"][1]), float(cam["pos"][2]))
    look = (float(cam["look"][0]), float(cam["look"][1]), float(cam["look"][2]))
    lens = float(cam["lens_mm"])
    tan_x = math.tan(math.atan(SENSOR_MM / (2.0 * lens)))
    aspect = height / max(width, 1)
    tan_y = tan_x * aspect
    right, up, forward = _camera_basis(pos, look)
    pixels = bytearray(width * height * 3)
    _fill_sky(pixels, width, height)
    zbuf = array("f", [1.0e9] * (width * height))
    for mn, mx, rgb in layout_boxes(layout):
        center = _scale(_add(mn, mx), 0.5)
        for corners, normal in _aabb_faces(mn, mx):
            view = _sub(pos, center)
            if _dot(normal, view) <= 0.0:
                continue
            color = _shade(rgb, normal)
            projected: list[tuple[float, float, float]] = []
            skip = False
            for corner in corners:
                hit = _project(
                    corner, pos, right, up, forward, tan_x, tan_y, width, height
                )
                if hit is None:
                    skip = True
                    break
                projected.append(hit)
            if skip:
                continue
            _fill_triangle(
                pixels, zbuf, width, height, projected[0], projected[1], projected[2], color
            )
            _fill_triangle(
                pixels, zbuf, width, height, projected[0], projected[2], projected[3], color
            )
    return bytes(pixels)


def render_clay_plate(
    layout: Mapping[str, Any],
    camera_index: int,
    dest: str | Path,
) -> Path:
    """Write a 1024x1280 clay plate for one camera.

    Args:
        layout: Validated ez.house.layout.v1 mapping.
        camera_index: 0-based place_10 index.
        dest: Output PNG path.

    Returns:
        Destination path.

    Raises:
        ValueError: Camera index out of range.
    """
    small = render_clay_rgb(layout, camera_index)
    rgb = _upsample_nearest(
        small, RENDER_WIDTH, RENDER_HEIGHT, PACK_WIDTH, PACK_HEIGHT
    )
    path = Path(dest)
    write_rgb_png(path, PACK_WIDTH, PACK_HEIGHT, rgb)
    return path

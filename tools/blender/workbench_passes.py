#!/usr/bin/env python3
"""Workbench / EEVEE pass helpers for host Blender dumps.

No bpy import. Callers pass duck-typed scene objects. Never talks to Comfy.
"""

from __future__ import annotations

from typing import Any

CLAY_RGB = (0.55, 0.52, 0.48)
CANNY_BG = (0.02, 0.02, 0.02)
CANNY_LINE = (1.0, 1.0, 1.0)
EEVEE_IDS = ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT")


def configure_resolution(scene: Any, width: int, height: int, fps: int, frames: int) -> None:
    """Set PNG still/anim resolution and frame range."""
    scene.render.resolution_x = int(width)
    scene.render.resolution_y = int(height)
    scene.render.resolution_percentage = 100
    scene.render.fps = int(fps)
    scene.frame_start = 1
    scene.frame_end = int(frames)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"


def configure_clay(scene: Any) -> None:
    """Workbench unshaded clay (Path B). Not Cycles beauty."""
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "SINGLE"
    shading.single_color = CLAY_RGB
    if hasattr(shading, "show_object_outline"):
        shading.show_object_outline = False


def configure_canny(scene: Any) -> None:
    """Workbench flat + object outline as a line-art / canny stand-in."""
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "FLAT"
    shading.color_type = "SINGLE"
    shading.single_color = CANNY_BG
    if hasattr(shading, "show_object_outline"):
        shading.show_object_outline = True
    if hasattr(shading, "object_outline_color"):
        shading.object_outline_color = CANNY_LINE
    if hasattr(shading, "show_cavity"):
        shading.show_cavity = True
    if hasattr(scene.render, "use_freestyle"):
        scene.render.use_freestyle = True


def configure_mist_depth(world: Any | None) -> None:
    """Mist 0–1, near=white / far=black. Raw metric Z is a QC fail."""
    if world is None or not hasattr(world, "mist_settings"):
        return
    world.mist_settings.use_mist = True
    if hasattr(world.mist_settings, "start"):
        world.mist_settings.start = 0.5
    if hasattr(world.mist_settings, "depth"):
        world.mist_settings.depth = 40.0
    if hasattr(world.mist_settings, "falloff"):
        world.mist_settings.falloff = "LINEAR"


def try_set_engine(scene: Any, names: tuple[str, ...] = EEVEE_IDS) -> str | None:
    """Set the first engine id the scene accepts. Returns the id or None."""
    for name in names:
        try:
            scene.render.engine = name
        except Exception:
            continue
        if str(getattr(scene.render, "engine", "")) == name:
            return name
    return None


def configure_eevee_normal(scene: Any, view_layer: Any | None) -> bool:
    """Enable EEVEE + Normal pass when the engine exists."""
    if try_set_engine(scene) is None:
        return False
    if view_layer is not None and hasattr(view_layer, "use_pass_normal"):
        view_layer.use_pass_normal = True
        return True
    return False


def _vec3(value: Any) -> list[float]:
    if value is None:
        return [0.0, 0.0, 0.0]
    if hasattr(value, "__getitem__"):
        return [float(value[0]), float(value[1]), float(value[2])]
    return [float(getattr(value, "x", 0.0)), float(getattr(value, "y", 0.0)), float(getattr(value, "z", 0.0))]


def frame_extrinsic(scene: Any, cam: Any, frame: int) -> dict[str, Any]:
    """One camera pose at ``frame`` (pos/rot/fov)."""
    if hasattr(scene, "frame_set"):
        scene.frame_set(int(frame))
    loc: Any = getattr(cam, "location", None)
    rot: Any = getattr(cam, "rotation_euler", None)
    matrix = getattr(cam, "matrix_world", None)
    if matrix is not None:
        if hasattr(matrix, "to_translation"):
            loc = matrix.to_translation()
        if hasattr(matrix, "to_euler"):
            rot = matrix.to_euler()
    data = getattr(cam, "data", None)
    fov = 0.0
    if data is not None:
        fov = float(getattr(data, "angle_y", 0.0) or getattr(data, "angle", 0.0) or 0.0)
    return {
        "frame": int(frame),
        "pos": _vec3(loc),
        "rot": _vec3(rot),
        "fov": fov,
    }


def camera_document(
    *,
    name: str,
    frames: int,
    fps: int,
    size: list[int],
    extrinsics: list[dict[str, Any]],
) -> dict[str, Any]:
    """Per-frame camera.json payload (optional on the pack)."""
    first = extrinsics[0] if extrinsics else {}
    return {
        "name": name,
        "frames": int(frames),
        "fps": int(fps),
        "size": list(size),
        "pos": list(first.get("pos") or [0.0, 0.0, 0.0]),
        "fov": float(first.get("fov") or 0.0),
        "extrinsics": list(extrinsics),
    }

"""Hermetic tests for Workbench pass helpers (no bpy)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "blender"))
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import workbench_passes as wp  # noqa: E402
from export_guide_pack import parse_export_args, shot_payload  # noqa: E402
from export_still_pack import resolve_size, still_payload  # noqa: E402


def test_configure_clay_and_canny() -> None:
    shading = SimpleNamespace(
        light="STUDIO",
        color_type="MATERIAL",
        single_color=(1.0, 1.0, 1.0),
        show_object_outline=False,
        object_outline_color=(0.0, 0.0, 0.0),
        show_cavity=False,
    )
    render = SimpleNamespace(
        engine="",
        use_freestyle=False,
        resolution_x=0,
        resolution_y=0,
        resolution_percentage=0,
        fps=0,
        image_settings=SimpleNamespace(file_format="", color_mode=""),
    )
    scene = SimpleNamespace(display=SimpleNamespace(shading=shading), render=render, frame_start=0, frame_end=0)
    wp.configure_resolution(scene, 1280, 704, 24, 120)
    assert scene.render.resolution_x == 1280
    assert scene.frame_end == 120
    wp.configure_clay(scene)
    assert scene.render.engine == "BLENDER_WORKBENCH"
    assert shading.color_type == "SINGLE"
    wp.configure_canny(scene)
    assert shading.light == "FLAT"
    assert shading.show_object_outline is True
    assert render.use_freestyle is True


def test_mist_and_eevee_normal() -> None:
    mist = SimpleNamespace(use_mist=False, start=0.0, depth=0.0, falloff="")
    world = SimpleNamespace(mist_settings=mist)
    wp.configure_mist_depth(world)
    assert mist.use_mist is True
    wp.configure_mist_depth(None)

    render = SimpleNamespace(engine="")
    scene = SimpleNamespace(render=render)
    view = SimpleNamespace(use_pass_normal=False)
    assert wp.configure_eevee_normal(scene, view) is True
    assert render.engine in wp.EEVEE_IDS
    assert view.use_pass_normal is True
    assert wp.configure_eevee_normal(scene, None) is False


def test_camera_document_per_frame() -> None:
    cam = SimpleNamespace(
        location=(1.0, 2.0, 3.0),
        rotation_euler=(0.1, 0.2, 0.3),
        data=SimpleNamespace(angle_y=0.5, angle=0.4),
        name="CAM",
    )
    scene = SimpleNamespace(frame_set=lambda _n: None)
    extra = wp.frame_extrinsic(scene, cam, 7)
    assert extra["frame"] == 7
    assert extra["pos"] == [1.0, 2.0, 3.0]
    doc = wp.camera_document(
        name="CAM",
        frames=120,
        fps=24,
        size=[1280, 704],
        extrinsics=[extra],
    )
    assert doc["extrinsics"][0]["fov"] == 0.5
    assert doc["frames"] == 120


def test_shot_payload_print_and_layers() -> None:
    ns = parse_export_args(
        [
            "blender",
            "--",
            "--out",
            "/tmp/p",
            "--film",
            "go-see",
            "--shot",
            "12",
            "--print",
            "ltx-iclora-canny",
        ]
    )
    payload = shot_payload(ns)
    assert payload["print"] == "ltx-iclora-canny"
    assert payload["schema"] == "ez.guide.shot.v1"
    assert "canny" in payload["layers"]
    with_n = shot_payload(ns, include_normal=True)
    assert "normal" in with_n["layers"]


def test_still_payload_size_token() -> None:
    ns = SimpleNamespace(
        film="go-see",
        plate="mug",
        engine="blender",
        print_mode="klein-from-clay",
        camera="CAM",
        width=1,
        height=1,
        size="1024x1024",
    )
    assert resolve_size(ns) == (1024, 1024)
    payload = still_payload(ns, blend="/x.blend")
    assert payload["schema"] == "ez.guide.still.v1"
    assert payload["size"] == [1024, 1024]
    assert payload["plate"] == "mug"
    assert payload["blend"] == "/x.blend"


def test_try_set_engine_exception_and_mismatch() -> None:
    class _BoomRender:
        def __init__(self) -> None:
            self.engine = "BLENDER_EEVEE"

        def __setattr__(self, name: str, value: object) -> None:
            if name == "engine" and value == "BLENDER_EEVEE_NEXT":
                raise RuntimeError("no")
            object.__setattr__(self, name, value)

    scene = SimpleNamespace(render=_BoomRender())
    assert wp.try_set_engine(scene, ("BLENDER_EEVEE_NEXT",)) is None
    scene2 = SimpleNamespace(render=SimpleNamespace(engine="WORKBENCH"))

    class _Mismatch:
        def __setattr__(self, name: str, value: object) -> None:
            if name == "engine":
                object.__setattr__(self, name, "OTHER")
            else:
                object.__setattr__(self, name, value)

        def __init__(self) -> None:
            object.__setattr__(self, "engine", "WORKBENCH")

    scene3 = SimpleNamespace(render=_Mismatch())
    assert wp.try_set_engine(scene3, ("BLENDER_EEVEE",)) is None
    del scene2

    class _Reject:
        def __init__(self) -> None:
            object.__setattr__(self, "engine", "WORKBENCH")

        def __setattr__(self, name: str, value: object) -> None:
            if name == "engine":
                raise RuntimeError("no")
            object.__setattr__(self, name, value)

    assert wp.configure_eevee_normal(SimpleNamespace(render=_Reject()), None) is False


def test_frame_extrinsic_uses_matrix_world() -> None:
    class _Mat:
        def to_translation(self) -> tuple[float, float, float]:
            return (9.0, 8.0, 7.0)

        def to_euler(self) -> tuple[float, float, float]:
            return (0.5, 0.4, 0.3)

    cam = SimpleNamespace(
        location=(0.0, 0.0, 0.0),
        rotation_euler=(0.0, 0.0, 0.0),
        matrix_world=_Mat(),
        data=SimpleNamespace(angle_y=0.2, angle=0.1),
        name="CAM",
    )
    scene = SimpleNamespace(frame_set=lambda _n: None)
    extra = wp.frame_extrinsic(scene, cam, 3)
    assert extra["pos"] == [9.0, 8.0, 7.0]
    assert extra["rot"] == [0.5, 0.4, 0.3]

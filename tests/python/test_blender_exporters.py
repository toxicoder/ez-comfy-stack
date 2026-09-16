"""Hermetic bpy-faked tests for tools/blender exporters."""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools" / "blender"
LIB = ROOT / "scripts" / "lib"
for _path in (str(TOOLS), str(LIB)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import export_guide_pack as egp  # noqa: E402
import export_house_views as ehv  # noqa: E402
import export_still_pack as esp  # noqa: E402
from house_layout import HouseLayoutError  # noqa: E402


class _MatList(list):
    pass


class _Obj:
    def __init__(self, name: str = "obj") -> None:
        self.name = name
        self.scale = (1, 1, 1)
        self.location = SimpleNamespace(x=0.0, y=0.0, z=1.0)
        self.rotation_euler = None
        self.color = None
        self.data = SimpleNamespace(materials=_MatList())


class _Scene:
    def __init__(self) -> None:
        self.camera = _Obj("Camera")
        self.world = SimpleNamespace(
            mist_settings=SimpleNamespace(use_mist=False, start=0.0, depth=0.0)
        )
        self.render = SimpleNamespace(
            filepath="",
            resolution_x=0,
            resolution_y=0,
            resolution_percentage=100,
            image_settings=SimpleNamespace(file_format="", color_mode=""),
            engine="",
            fps=24,
            frame_start=1,
            frame_end=1,
        )
        self.display = SimpleNamespace(
            shading=SimpleNamespace(light="", color_type="", single_color=None)
        )
        self.collection = SimpleNamespace(objects=SimpleNamespace(link=lambda _o: None))


class _ObjMap(dict):
    def get(self, name: str, default: object = None) -> object:  # type: ignore[override]
        return super().get(name, default)

    def new(self, name: str, data: object = None) -> _Obj:
        obj = _Obj(name)
        self[name] = obj
        return obj


class _Data:
    def __init__(self) -> None:
        self.filepath = "/tmp/scene.blend"
        self.objects: _ObjMap = _ObjMap()
        self.cameras = SimpleNamespace(new=lambda name: SimpleNamespace(lens=0, sensor_fit="", sensor_height=0))
        self.materials = SimpleNamespace(
            new=lambda name: SimpleNamespace(diffuse_color=None)
        )
        self.worlds = SimpleNamespace(new=lambda name: SimpleNamespace(mist_settings=SimpleNamespace(use_mist=False, start=0, depth=0)))

    def __contains__(self, name: object) -> bool:
        return name in self.objects


class FakeBpy:
    def __init__(self, dest: Path | None = None) -> None:
        self.context = SimpleNamespace(scene=_Scene(), active_object=_Obj("active"), view_layer=None)
        self.data = _Data()
        self._dest = dest
        self.ops = SimpleNamespace(
            mesh=SimpleNamespace(
                primitive_cube_add=lambda **_k: None,
                primitive_cylinder_add=lambda **_k: None,
                primitive_plane_add=lambda **_k: None,
            ),
            object=SimpleNamespace(
                select_all=lambda **_k: None,
                delete=lambda **_k: None,
            ),
            render=SimpleNamespace(render=self._render),
            export_scene=SimpleNamespace(gltf=self._gltf),
        )

    def _render(self, **_kwargs: object) -> None:
        scene = self.context.scene
        path = Path(str(scene.render.filepath))
        if path.suffix.lower() != ".png":
            path = path / "0001.png" if path.suffix == "" else Path(str(path) + ".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == "":
            path = path / "0001.png"
        if path.suffix.lower() != ".png":
            path = Path(str(path) + ".png")
        path.write_bytes(b"png")
        scene.render.filepath = str(path)

    def _gltf(self, filepath: str, **_k: object) -> None:
        dest = Path(filepath)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"glb")


def test_guide_pack_parse_and_payload() -> None:
    ns = egp.parse_export_args(
        [
            "blender",
            "--",
            "--out",
            "/tmp/out",
            "--film",
            "go-see",
            "--shot",
            "12",
            "--include-normal",
        ]
    )
    assert ns.film == "go-see"
    data = egp.shot_payload(ns, blend="x.blend", include_normal=True)
    assert data["schema"] == egp.SCHEMA
    assert data["blend"] == "x.blend"
    assert ns.include_normal is True


def test_guide_pack_main_rejects_bad_size(capsys: pytest.CaptureFixture[str]) -> None:
    ns = SimpleNamespace(
        frames=120,
        width=1280,
        height=720,
        out="/tmp",
        film="go-see",
        shot="12",
        fps=24,
        camera="",
        engine="blender",
        print_mode="ltx-iclora-depth",
        include_normal=False,
    )
    monkey_argv = ["export_guide_pack.py", "--", "--out", "/t", "--film", "a", "--shot", "1", "--height", "720"]
    old = sys.argv
    sys.argv = monkey_argv
    try:
        rc = egp.main()
    finally:
        sys.argv = old
    assert rc == 1
    err = capsys.readouterr().err
    assert "1280x720" in err or "size must" in err
    _ = ns


def test_guide_pack_export_with_fake_bpy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeBpy()
    fake.data.objects["Camera"] = fake.context.scene.camera  # type: ignore[index]
    monkeypatch.setitem(sys.modules, "bpy", fake)
    dest = tmp_path / "pack"
    rgb = dest / "rgb"
    rgb.mkdir(parents=True)
    (rgb / "0001.png").write_bytes(b"first")
    (rgb / "0120.png").write_bytes(b"last")
    ns = egp.parse_export_args(
        [
            "--",
            "--out",
            str(dest),
            "--film",
            "go-see",
            "--shot",
            "12",
            "--camera",
            "Camera",
            "--include-normal",
        ]
    )
    egp.export_with_bpy(ns)
    assert (dest / "shot.yaml").is_file()
    assert (dest / "first.png").is_file()
    assert (dest / "last.png").is_file()
    assert (dest / "camera.json").is_file()


def test_still_pack_resolve_size_and_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ns = esp.parse_export_args(
        ["--", "--out", str(tmp_path), "--film", "go-see", "--plate", "mug", "--size", "1024x1024"]
    )
    assert esp.resolve_size(ns) == (1024, 1024)
    with pytest.raises(SystemExit, match="invalid --size"):
        esp.resolve_size(SimpleNamespace(size="nope", width=1, height=1))
    fake = FakeBpy()
    fake.data.objects["Camera"] = fake.context.scene.camera  # type: ignore[index]
    monkeypatch.setitem(sys.modules, "bpy", fake)
    ns = esp.parse_export_args(
        [
            "--",
            "--out",
            str(tmp_path / "still"),
            "--film",
            "go-see",
            "--plate",
            "mug",
            "--camera",
            "Camera",
        ]
    )
    esp.export_with_bpy(ns)
    assert (tmp_path / "still" / "still.yaml").is_file()
    assert (tmp_path / "still" / "first.png").is_file()
    with pytest.raises(SystemExit, match="bpy required"):
        monkeypatch.delitem(sys.modules, "bpy", raising=False)
        # import inside export_with_bpy
        import builtins

        real_import = builtins.__import__

        def _no_bpy(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "bpy":
                raise ImportError("no bpy")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _no_bpy)
        esp.export_with_bpy(ns)


def test_house_views_construct_and_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    layout = {
        "id": "house",
        "schema": "ez.house.layout.v1",
        "rooms": [
            {
                "id": "lounge",
                "box": [0.0, 0.0, 0.0, 4.0, 3.0, 5.0],
                "openings": ["south"],
            }
        ],
        "props": [
            {
                "id": "table",
                "primitive": "cube",
                "pose": [1.0, 0.4, 1.0],
                "size": [1.0, 0.8, 1.0],
            },
            {
                "id": "rug",
                "primitive": "plane",
                "pose": [2.0, 0.0, 2.0],
                "size": [2.0, 0.02, 2.0],
            },
        ],
        "cameras": [
            {
                "id": "cam01",
                "pos": [2.0, 1.6, 6.0],
                "look": [2.0, 1.0, 2.0],
                "lens_mm": 24,
            }
        ],
    }
    fake = FakeBpy()
    mathutils = types.ModuleType("mathutils")

    class Vector:
        def __init__(self, xyz: tuple[float, float, float]) -> None:
            self._xyz = xyz
            self.length = sum(abs(v) for v in xyz)

        def __sub__(self, other: object) -> Vector:
            if isinstance(other, SimpleNamespace):
                return Vector((self._xyz[0] - 0.0, self._xyz[1] - 0.0, self._xyz[2] - 1.0))
            loc = other
            return Vector(self._xyz) if loc is not None else Vector(self._xyz)

        def to_track_quat(self, _a: str, _b: str) -> SimpleNamespace:
            return SimpleNamespace(to_euler=lambda: (0.0, 0.0, 0.0))

    mathutils.Vector = Vector  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mathutils", mathutils)
    fake.data.objects["cam01"] = _Obj("cam01")
    ehv.construct_scene(fake, layout)
    ns = ehv.parse_export_args(
        [
            "--",
            "--out",
            str(tmp_path / "views"),
            "--layout",
            str(tmp_path / "layout.yaml"),
        ]
    )
    (tmp_path / "layout.yaml").write_text("id: house\n", encoding="utf-8")
    monkeypatch.setitem(sys.modules, "bpy", fake)

    def _load(_path: object) -> dict:
        return {
            **layout,
            "cameras": list(layout["cameras"])
            + [
                {
                    "id": cid,
                    "pos": [0, 1, 0],
                    "look": [0, 1, 1],
                    "lens_mm": 35,
                }
                for cid in ehv.PLACE_10_IDS
                if cid != "cam01"
            ],
        }

    # PLACE_10_IDS is the 10 camera ids; keep original layout cameras and stub rest
    from house_layout import PLACE_10_IDS, PACK_HEIGHT, PACK_WIDTH

    full_cams = []
    for cid in PLACE_10_IDS:
        full_cams.append(
            {"id": cid, "pos": [0.0, 1.6, 4.0], "look": [0.0, 1.0, 0.0], "lens_mm": 24}
        )
        fake.data.objects[cid] = _Obj(cid)
    monkeypatch.setattr(ehv, "load_layout", lambda _p: {**layout, "cameras": full_cams})
    monkeypatch.setattr(ehv, "validate_views_dir", lambda *_a, **_k: None)
    monkeypatch.setattr(ehv, "copy_clay_to_input_dir", lambda *_a, **_k: None)
    monkeypatch.setattr(ehv, "dump_asset_yaml", lambda slug: f"id: {slug}\n")
    monkeypatch.setattr(ehv, "write_views_yaml", lambda path, data: Path(path).write_text("ok\n"))
    monkeypatch.setattr(ehv, "clay_copy_name", lambda i: f"clay_{i:02d}.png")
    ns.width = PACK_WIDTH
    ns.height = PACK_HEIGHT
    ns.engine = "blender"
    ns.slug = "house"
    ns.input_dir = str(tmp_path / "input")
    (tmp_path / "input").mkdir()
    ehv.export_with_bpy(ns)
    assert (tmp_path / "views" / "mesh" / "house.glb").is_file()

    ns.engine = "maya"
    with pytest.raises(SystemExit, match="blender"):
        ehv.export_with_bpy(ns)
    ns.engine = "blender"
    ns.width = 1
    with pytest.raises(SystemExit, match="size must"):
        ehv.export_with_bpy(ns)

    monkeypatch.delitem(sys.modules, "bpy", raising=False)
    import builtins

    real_import = builtins.__import__

    def _no_bpy(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "bpy":
            raise ImportError("no bpy")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_bpy)
    ns.width = PACK_WIDTH
    with pytest.raises(SystemExit, match="bpy required"):
        ehv.export_with_bpy(ns)

    monkeypatch.setattr(builtins, "__import__", real_import)
    monkeypatch.setitem(sys.modules, "bpy", fake)
    monkeypatch.setattr(
        ehv,
        "export_with_bpy",
        lambda _ns: (_ for _ in ()).throw(HouseLayoutError("bad layout")),
    )
    old = sys.argv
    sys.argv = ["x", "--", "--out", str(tmp_path), "--layout", str(tmp_path / "layout.yaml")]
    try:
        assert ehv.main() == 1
    finally:
        sys.argv = old


def test_guide_pack_copy_first_last_and_no_camera(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeBpy()
    fake.context.scene.camera = None
    monkeypatch.setitem(sys.modules, "bpy", fake)
    dest = tmp_path / "pack"
    ns = egp.parse_export_args(
        ["--", "--out", str(dest), "--film", "go-see", "--shot", "12"]
    )
    egp.export_with_bpy(ns)
    assert not (dest / "camera.json").is_file()
    empty = tmp_path / "empty"
    empty.mkdir()
    (empty / "rgb").mkdir()
    egp._copy_first_last(empty, 120)
    assert not (empty / "first.png").is_file()


def test_guide_pack_validate_and_normal_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeBpy()
    fake.context.view_layer = SimpleNamespace(use_pass_normal=False)
    fake.data.objects["Camera"] = fake.context.scene.camera  # type: ignore[index]
    monkeypatch.setitem(sys.modules, "bpy", fake)
    monkeypatch.setattr(egp, "validate_shot", lambda _p: ["bad"])
    ns = egp.parse_export_args(
        ["--", "--out", str(tmp_path / "bad"), "--film", "go-see", "--shot", "12"]
    )
    with pytest.raises(SystemExit, match="shot.yaml invalid"):
        egp.export_with_bpy(ns)
    monkeypatch.setattr(egp, "validate_shot", lambda _p: [])
    monkeypatch.setattr(egp, "configure_eevee_normal", lambda *_a, **_k: True)
    ns = egp.parse_export_args(
        [
            "--",
            "--out",
            str(tmp_path / "ok"),
            "--film",
            "go-see",
            "--shot",
            "12",
            "--include-normal",
        ]
    )
    egp.export_with_bpy(ns)
    assert (tmp_path / "ok" / "shot.yaml").is_file()


def test_guide_pack_bpy_missing_and_main_frames(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import builtins

    real_import = builtins.__import__

    def _no_bpy(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "bpy":
            raise ImportError("no bpy")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_bpy)
    monkeypatch.delitem(sys.modules, "bpy", raising=False)
    ns = egp.parse_export_args(
        ["--", "--out", "/tmp/x", "--film", "a", "--shot", "1"]
    )
    with pytest.raises(SystemExit, match="bpy required"):
        egp.export_with_bpy(ns)
    monkeypatch.setattr(builtins, "__import__", real_import)
    monkeypatch.setattr(egp, "parse_export_args", lambda: SimpleNamespace(frames=1, width=1280, height=704))
    assert egp.main() == 1
    assert "frames must" in capsys.readouterr().err
    monkeypatch.setattr(
        egp,
        "parse_export_args",
        lambda: SimpleNamespace(frames=120, width=1280, height=704),
    )
    monkeypatch.setattr(egp, "export_with_bpy", lambda _ns: None)
    assert egp.main() == 0


def test_guide_pack_dunder_main(monkeypatch: pytest.MonkeyPatch) -> None:
    import runpy

    monkeypatch.setattr(
        sys,
        "argv",
        ["export_guide_pack.py", "--", "--out", "/t", "--film", "a", "--shot", "1", "--frames", "1"],
    )
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(TOOLS / "export_guide_pack.py"), run_name="__main__")
    assert exc.value.code == 1


def test_still_pack_render_suffix_and_main(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeBpy()

    def _render_plain(**_k: object) -> None:
        scene = fake.context.scene
        path = Path(str(scene.render.filepath))
        bare = path.with_suffix("") if path.suffix.lower() == ".png" else path
        scene.render.filepath = str(bare)
        candidate = Path(str(bare) + ".png")
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_bytes(b"png")

    fake.ops.render.render = _render_plain
    fake.data.objects["Camera"] = fake.context.scene.camera  # type: ignore[index]
    monkeypatch.setitem(sys.modules, "bpy", fake)
    dest = tmp_path / "still"
    ns = esp.parse_export_args(
        ["--", "--out", str(dest), "--film", "go-see", "--plate", "mug", "--camera", "Camera"]
    )
    esp.export_with_bpy(ns)
    assert (dest / "first.png").is_file()
    with pytest.raises(SystemExit, match="not in"):
        bad = SimpleNamespace(
            size="",
            width=3,
            height=3,
            out=str(tmp_path),
            film="a",
            plate="p",
            camera="",
            engine="blender",
            print_mode="klein-from-clay",
        )
        esp.export_with_bpy(bad)
    monkeypatch.setattr(esp, "validate_still", lambda _p: ["bad"])
    ns = esp.parse_export_args(
        ["--", "--out", str(tmp_path / "inv"), "--film", "go-see", "--plate", "mug"]
    )
    with pytest.raises(SystemExit, match="still.yaml invalid"):
        esp.export_with_bpy(ns)
    monkeypatch.setattr(esp, "parse_export_args", lambda: ns)
    monkeypatch.setattr(esp, "export_with_bpy", lambda _ns: None)
    assert esp.main() == 0


def test_still_pack_dunder_main(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import runpy

    monkeypatch.setattr(
        sys,
        "argv",
        ["export_still_pack.py", "--", "--out", str(tmp_path), "--film", "a", "--plate", "p", "--size", "bad"],
    )
    with pytest.raises(SystemExit):
        runpy.run_path(str(TOOLS / "export_still_pack.py"), run_name="__main__")


def test_house_views_world_none_cylinder_south_and_glb(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from house_layout import PACK_HEIGHT, PACK_WIDTH, PLACE_10_IDS

    layout = {
        "id": "house",
        "schema": "ez.house.layout.v1",
        "rooms": [
            {
                "id": "kitchen",
                "box": [0.0, 0.0, 0.0, 4.0, 3.0, 5.0],
                "openings": [],
            }
        ],
        "props": [
            {
                "id": "col",
                "primitive": "cylinder",
                "pose": [1.0, 0.4, 1.0],
                "size": [0.2, 1.0, 0.2],
            }
        ],
        "cameras": [
            {"id": cid, "pos": [0.0, 1.6, 4.0], "look": [0.0, 1.0, 0.0], "lens_mm": 24}
            for cid in PLACE_10_IDS
        ],
    }
    fake = FakeBpy()
    fake.context.scene.world = None
    mathutils = types.ModuleType("mathutils")

    class Vector:
        def __init__(self, xyz: tuple[float, float, float]) -> None:
            self._xyz = xyz
            self.length = 1.0

        def __sub__(self, other: object) -> Vector:
            del other
            return Vector(self._xyz)

        def to_track_quat(self, _a: str, _b: str) -> SimpleNamespace:
            return SimpleNamespace(to_euler=lambda: (0.0, 0.0, 0.0))

    mathutils.Vector = Vector  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mathutils", mathutils)
    for cid in PLACE_10_IDS:
        fake.data.objects[cid] = _Obj(cid)

    def _render_plain(**_k: object) -> None:
        scene = fake.context.scene
        path = Path(str(scene.render.filepath))
        candidate = Path(str(path) + ".png")
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_bytes(b"png")

    fake.ops.render.render = _render_plain
    fake.ops.export_scene.gltf = lambda **_k: None
    monkeypatch.setitem(sys.modules, "bpy", fake)
    monkeypatch.setattr(ehv, "load_layout", lambda _p: layout)
    monkeypatch.setattr(ehv, "validate_views_dir", lambda *_a, **_k: None)
    monkeypatch.setattr(ehv, "dump_asset_yaml", lambda slug: f"id: {slug}\n")
    monkeypatch.setattr(
        ehv, "write_views_yaml", lambda path, data: Path(path).write_text("ok\n")
    )
    monkeypatch.setattr(ehv, "clay_copy_name", lambda i: f"clay_{i:02d}.png")
    ns = ehv.parse_export_args(
        ["--", "--out", str(tmp_path / "views"), "--layout", str(tmp_path / "layout.yaml")]
    )
    ns.width = PACK_WIDTH
    ns.height = PACK_HEIGHT
    ns.engine = "blender"
    ns.slug = "house"
    ns.input_dir = ""
    (tmp_path / "layout.yaml").write_text("id: house\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="GLB export failed"):
        ehv.export_with_bpy(ns)
    ehv.construct_scene(fake, layout)
    ehv._configure_workbench(fake, PACK_WIDTH, PACK_HEIGHT)
    with pytest.raises(SystemExit, match="missing camera"):
        ehv._render_camera(fake, "nope", tmp_path, "views")
    monkeypatch.setattr(ehv, "export_with_bpy", lambda _ns: None)
    monkeypatch.setattr(ehv, "parse_export_args", lambda: ns)
    assert ehv.main() == 0


def test_house_views_dunder_main(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import runpy

    monkeypatch.setattr(
        sys,
        "argv",
        ["export_house_views.py", "--", "--out", str(tmp_path), "--layout", str(tmp_path / "missing.yaml")],
    )
    with pytest.raises(SystemExit):
        runpy.run_path(str(TOOLS / "export_house_views.py"), run_name="__main__")


def test_look_at_zero_length_and_alt_png(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeBpy()
    mathutils = types.ModuleType("mathutils")

    class Vector:
        def __init__(self, xyz: tuple[float, float, float]) -> None:
            self._xyz = xyz
            self.length = 0.0

        def __sub__(self, other: object) -> Vector:
            del other
            return Vector((0.0, 0.0, 0.0))

        def to_track_quat(self, _a: str, _b: str) -> SimpleNamespace:
            raise AssertionError("should not rotate")

    mathutils.Vector = Vector  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mathutils", mathutils)
    obj = _Obj("cam")
    ehv._look_at(fake, obj, (0.0, 0.0, 0.0))

    def _render_alt(**_k: object) -> None:
        scene = fake.context.scene
        path = Path(str(scene.render.filepath))
        alt = path.with_name((path.stem or "frame") + "_alt.png")
        alt.parent.mkdir(parents=True, exist_ok=True)
        alt.write_bytes(b"png")
        scene.render.filepath = str(alt)

    fake.ops.render.render = _render_alt
    fake.data.objects["Camera"] = fake.context.scene.camera  # type: ignore[index]
    monkeypatch.setitem(sys.modules, "bpy", fake)
    dest = tmp_path / "still-alt"
    ns = esp.parse_export_args(
        ["--", "--out", str(dest), "--film", "go-see", "--plate", "mug"]
    )
    esp.export_with_bpy(ns)
    assert (dest / "first.png").is_file()
    png = ehv._render_camera(fake, "Camera", tmp_path, "views")
    assert png.suffix == ".png"

    def _render_bare(**_k: object) -> None:
        scene = fake.context.scene
        path = Path(str(scene.render.filepath))
        bare = path.with_suffix("") if path.suffix else path
        candidate = Path(str(bare) + ".png")
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_bytes(b"png")
        scene.render.filepath = str(bare)

    fake.ops.render.render = _render_bare
    png = ehv._render_camera(fake, "Camera", tmp_path / "bare", "views")
    assert png.is_file()


def test_exporters_insert_lib_on_path(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib.util

    lib = str(LIB)
    here = str(TOOLS)
    for name, path in (
        ("ehv_reload", TOOLS / "export_house_views.py"),
        ("esp_reload", TOOLS / "export_still_pack.py"),
        ("egp_reload", TOOLS / "export_guide_pack.py"),
    ):
        monkeypatch.setattr(sys, "path", [p for p in sys.path if p not in {lib, here}])
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert lib in sys.path or here in sys.path

"""ez.house.layout.v1 / ez.house.views.v1 — hermetic, no Blender."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import house_layout as hl  # noqa: E402

SCHEMA_YAML = ROOT / "schemas" / "house_layout.yaml"
EXPORT_PY = ROOT / "tools" / "blender" / "export_house_views.py"


def test_shipped_layout_validates() -> None:
    layout = hl.load_layout(SCHEMA_YAML)
    assert layout["schema"] == hl.SCHEMA_LAYOUT
    assert layout["id"] == "lab-penthouse"
    assert layout["kind"] == "set"
    assert layout["pipeline"] == "bpy-primitive"
    assert layout["size"] == [1024, 1280]
    assert [cam["id"] for cam in layout["cameras"]] == list(hl.PLACE_10_IDS)
    assert {room["id"] for room in layout["rooms"]} >= {
        "foyer",
        "lounge",
        "kitchen",
        "dining",
        "bedroom",
        "bath",
        "study",
        "terrace",
    }
    assert layout["cameras"][0]["lens_mm"] == 24
    assert layout["cameras"][3]["lens_mm"] == 35


def test_missing_camera_and_bad_size_rejected() -> None:
    layout = hl.load_layout(SCHEMA_YAML)
    layout["cameras"] = layout["cameras"][:-1]
    with pytest.raises(hl.HouseLayoutError, match="cameras"):
        hl.validate_layout(layout)
    layout = hl.load_layout(SCHEMA_YAML)
    layout["size"] = [1280, 704]
    with pytest.raises(hl.HouseLayoutError, match="1024"):
        hl.validate_layout(layout)
    layout = hl.load_layout(SCHEMA_YAML)
    layout["size"] = [1280, 720]
    with pytest.raises(hl.HouseLayoutError, match="1024"):
        hl.validate_layout(layout)


def test_embedded_mesh_bytes_refused() -> None:
    layout = hl.load_layout(SCHEMA_YAML)
    layout["props"][0]["glb"] = "AAAA" + ("A" * 80)
    with pytest.raises(hl.HouseLayoutError, match="embed"):
        hl.validate_layout(layout)
    layout = hl.load_layout(SCHEMA_YAML)
    layout["props"][0]["preview"] = "data:model/gltf-binary;base64," + ("A" * 200)
    with pytest.raises(hl.HouseLayoutError, match="base64"):
        hl.validate_layout(layout)


def test_unknown_primitive_and_bad_box_rejected() -> None:
    layout = hl.load_layout(SCHEMA_YAML)
    layout["props"][0]["primitive"] = "nurbs"
    with pytest.raises(hl.HouseLayoutError, match="primitive"):
        hl.validate_layout(layout)
    layout = hl.load_layout(SCHEMA_YAML)
    layout["rooms"][0]["box"] = [0, 0, 0]
    with pytest.raises(hl.HouseLayoutError, match="box"):
        hl.validate_layout(layout)


def test_views_yaml_roundtrip_and_qc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "sets" / "lab-penthouse"
    hl.write_fixture_pack(dest, slug="lab-penthouse")
    views = hl.load_views(dest / "views.yaml")
    assert views["schema"] == hl.SCHEMA_VIEWS
    assert views["engine"] == "blender"
    assert views["size"] == [1024, 1280]
    assert views["cameras"] == list(hl.PLACE_10_IDS)
    hl.validate_views_dir(dest, require_glb=False)
    (dest / "mesh").mkdir(parents=True, exist_ok=True)
    (dest / "mesh" / "house.glb").write_bytes(b"glTF")
    hl.validate_views_dir(dest)
    clay = dest / "views" / "01-tower.png"
    clay.write_bytes(b"not-a-png")
    with pytest.raises(hl.HouseLayoutError, match="size"):
        hl.validate_views_dir(dest, require_glb=False)


def test_refuse_models_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    models = tmp_path / "models"
    models.mkdir()
    monkeypatch.setenv("MODELS_DIR", str(models))
    with pytest.raises(hl.HouseLayoutError, match="MODELS_DIR"):
        hl.refuse_output_dir(models / "sets" / "lab-penthouse")


def test_clay_copy_names_and_export_script_parses() -> None:
    assert hl.clay_copy_name(0) == "ez_house_clay_01.png"
    assert hl.clay_copy_name(9) == "ez_house_clay_10.png"
    ast.parse(EXPORT_PY.read_text(encoding="utf-8"))
    ast.parse((ROOT / "scripts" / "lib" / "house_layout.py").read_text(encoding="utf-8"))


def test_godot_engine_not_in_v1_engines() -> None:
    assert hl.ENGINE_BLENDER == "blender"
    assert "godot" not in hl.ENGINES


def test_copy_clay_to_input_dir_and_validate_input(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pack = tmp_path / "pack"
    hl.write_fixture_pack(pack, slug="lab-penthouse")
    dest = tmp_path / "input"
    written = hl.copy_clay_to_input_dir(pack, dest)
    assert [path.name for path in written] == [
        f"ez_house_clay_{i:02d}.png" for i in range(1, 11)
    ]
    assert hl.png_size(dest / "ez_house_clay_01.png") == (1024, 1280)
    views = hl.validate_views_dir(pack, require_glb=False, input_dir=dest)
    assert views["id"] == "lab-penthouse"
    (dest / "ez_house_clay_01.png").unlink()
    with pytest.raises(hl.HouseLayoutError, match="LoadImage"):
        hl.validate_views_dir(pack, require_glb=False, input_dir=dest)
    (pack / "ez_house_clay_05.png").unlink()
    with pytest.raises(hl.HouseLayoutError, match="ez_house_clay_05"):
        hl.copy_clay_to_input_dir(pack, dest)
    assert hl._cli(["copy-inputs", str(tmp_path / "missing"), str(dest)]) == 1
    capsys.readouterr()
    pack2 = tmp_path / "pack2"
    hl.write_fixture_pack(pack2)
    inp2 = tmp_path / "input2"
    assert hl._cli(["copy-inputs", str(pack2), str(inp2)]) == 0
    assert "10 clay" in capsys.readouterr().out
    assert (inp2 / "ez_house_clay_10.png").is_file()


def test_house_layout_cli_validate_and_export_helpers_named(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert hl._cli(["validate", str(SCHEMA_YAML)]) == 0
    assert "lab-penthouse" in capsys.readouterr().out
    dest = tmp_path / "pack"
    assert hl._cli(["fixture", str(dest), "--slug", "lab-penthouse"]) == 0
    assert hl._cli(["validate-views", str(dest), "--fixture"]) == 0
    assert hl._cli(["validate", str(tmp_path / "missing.yaml")]) == 1
    text = EXPORT_PY.read_text(encoding="utf-8")
    for name in (
        "parse_export_args",
        "construct_scene",
        "export_with_bpy",
        "_add_room",
        "_new_mesh",
        "_look_at",
        "_configure_workbench",
        "_render_camera",
        "_wall_on",
    ):
        assert f"def {name}(" in text
    assert "copy_clay_to_input_dir" in text
    lib_text = (ROOT / "scripts" / "lib" / "house_layout.py").read_text(
        encoding="utf-8"
    )
    assert "def copy_clay_to_input_dir(" in lib_text
    assert "def seed_clay_to_input_dir(" in lib_text
    assert "def clay_plate_valid(" in lib_text
    assert "def default_layout_path(" in lib_text
    render_text = (ROOT / "scripts" / "lib" / "house_clay_render.py").read_text(
        encoding="utf-8"
    )
    assert "def render_clay_plate(" in render_text
    assert "def layout_boxes(" in render_text
    ast.parse(render_text)


def test_seed_clay_renders_distinct_plates(tmp_path: Path) -> None:
    dest = tmp_path / "input"
    written = hl.seed_clay_to_input_dir(dest, layout_path=SCHEMA_YAML)
    names = [path.name for path in written]
    assert names == [f"ez_house_clay_{i:02d}.png" for i in range(1, 11)]
    first = dest / "ez_house_clay_01.png"
    second = dest / "ez_house_clay_02.png"
    tenth = dest / "ez_house_clay_10.png"
    assert hl.png_size(first) == (1024, 1280)
    assert hl.png_size(second) == (1024, 1280)
    assert hl.png_size(tenth) == (1024, 1280)
    assert first.read_bytes() != second.read_bytes()
    assert first.stat().st_size > 2000
    assert hl.clay_plate_valid(first)


def test_seed_clay_skips_existing_and_copies_pack(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from guide_pack import write_solid_png

    dest = tmp_path / "input"
    dest.mkdir()
    keep = dest / "ez_house_clay_01.png"
    write_solid_png(keep, 1024, 1280, (10, 20, 30))
    before = keep.read_bytes()
    pack = tmp_path / "pack"
    hl.write_fixture_pack(pack, slug="lab-penthouse")
    written = hl.seed_clay_to_input_dir(
        dest, pack_dir=pack, layout_path=SCHEMA_YAML
    )
    assert len(written) == 10
    assert keep.read_bytes() == before
    copied = dest / "ez_house_clay_02.png"
    assert copied.read_bytes() == (pack / "ez_house_clay_02.png").read_bytes()
    assert (
        hl._cli(["seed-inputs", str(tmp_path / "cli-in"), "--layout", str(SCHEMA_YAML)])
        == 0
    )
    out = capsys.readouterr().out
    assert "seeded" in out
    assert (tmp_path / "cli-in" / "ez_house_clay_10.png").is_file()


def test_seed_clay_discovers_pack_and_refuses_models_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out_root = tmp_path / "comfy-output"
    pack = out_root / "assets" / "sets" / "lab-penthouse"
    inp = out_root / "input"
    hl.write_fixture_pack(pack, slug="lab-penthouse")
    written = hl.seed_clay_to_input_dir(inp, slug="lab-penthouse")
    assert (inp / "ez_house_clay_01.png").read_bytes() == (
        pack / "ez_house_clay_01.png"
    ).read_bytes()
    assert len(written) == 10
    models = tmp_path / "models"
    models.mkdir()
    monkeypatch.setenv("MODELS_DIR", str(models))
    with pytest.raises(hl.HouseLayoutError, match="MODELS_DIR"):
        hl.seed_clay_to_input_dir(models / "input")
    assert hl.default_layout_path() == SCHEMA_YAML
    assert hl._cli(["seed-inputs", str(models / "blocked")]) == 1

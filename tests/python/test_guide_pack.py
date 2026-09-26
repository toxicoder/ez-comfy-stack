"""Guide-pack schema and QC (hermetic: stdlib only, no Blender)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import guide_pack as _lib_gp  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "dcc" / "suzanne-12"
SCHEMA = ROOT / "schemas" / "guide_pack.shot.yaml"
VENDOR = ROOT / "custom_nodes" / "ez_dcc" / "_guide_pack.py"

import ez_dcc._guide_pack as _vendor_gp  # noqa: E402,F401 - coverage alias


def _load_vendor() -> ModuleType:
    spec = importlib.util.spec_from_file_location("ez_dcc_guide_pack_vendor", VENDOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(params=["lib", "vendor"])
def gp(request: pytest.FixtureRequest) -> ModuleType:
    """Both the scripts/lib module and the Comfy-vendored copy."""
    if request.param == "lib":
        return _lib_gp
    return _load_vendor()


def test_schema_file_documents_v1() -> None:
    text = SCHEMA.read_text(encoding="utf-8")
    assert "ez.guide.shot.v1" in text
    assert "1280" in text
    assert "704" in text
    assert "1280x720" in text or "1280x720" in text or "Never 1280" in text
    still_schema = ROOT / "schemas" / "guide_pack.still.yaml"
    still_text = still_schema.read_text(encoding="utf-8")
    assert "ez.guide.still.v1" in still_text
    assert "1024x1024" in still_text or "1024, 1024" in still_text


def test_fixture_pack_validates_without_full_seq(gp: ModuleType) -> None:
    defects = gp.validate_pack(FIXTURE, require_full_seq=False)
    assert defects == [], defects


def test_fixture_shot_yaml_fields(gp: ModuleType) -> None:
    shot = gp.load_shot(FIXTURE)
    assert gp.validate_shot(shot) == []
    assert shot["schema"] == gp.SCHEMA
    assert shot["frames"] == 120
    assert shot["fps"] == 24
    assert shot["size"] == [1280, 704]
    assert shot["engine"] == "blender"
    assert "first.png" in (FIXTURE / "first.png").name


def test_refuse_720_and_wrong_frame_count(gp: ModuleType) -> None:
    bad = {
        "schema": gp.SCHEMA,
        "slug": "go-see",
        "shot_id": "12",
        "engine": "blender",
        "print": "ltx-iclora-depth",
        "frames": 121,
        "fps": 24,
        "size": [1280, 720],
        "layers": ["rgb", "first", "last"],
    }
    defects = gp.validate_shot(bad)
    assert any("704" in d for d in defects)
    assert any("120" in d for d in defects)


def test_unknown_engine_and_print(gp: ModuleType) -> None:
    data = {
        "schema": gp.SCHEMA,
        "slug": "x",
        "shot_id": "01",
        "engine": "maya",
        "print": "seedance",
        "frames": 120,
        "fps": 24,
        "size": [1280, 704],
        "layers": ["rgb"],
    }
    defects = gp.validate_shot(data)
    assert any("engine" in d for d in defects)
    assert any("print" in d for d in defects)


def test_png_size_and_write(tmp_path: Path, gp: ModuleType) -> None:
    path = tmp_path / "first.png"
    gp.write_solid_png(path, 1280, 704, (80, 80, 90))
    assert gp.png_size(path) == (1280, 704)
    gp.write_rgb_png(tmp_path / "tiny.png", 2, 2, bytes(range(12)))
    assert gp.png_size(tmp_path / "tiny.png") == (2, 2)
    with pytest.raises(ValueError, match="length"):
        gp.write_rgb_png(tmp_path / "bad.png", 2, 2, b"short")


def test_full_seq_require(tmp_path: Path, gp: ModuleType) -> None:
    pack = tmp_path / "12"
    pack.mkdir()
    gp.write_solid_png(pack / "first.png", 1280, 704, (10, 10, 10))
    gp.write_solid_png(pack / "last.png", 1280, 704, (20, 20, 20))
    gp.write_shot_yaml(
        pack / "shot.yaml",
        {
            "schema": gp.SCHEMA,
            "slug": "go-see",
            "shot_id": "12",
            "engine": "blender",
            "print": "ltx-iclora-depth",
            "frames": 120,
            "fps": 24,
            "size": [1280, 704],
            "layers": ["rgb", "depth", "first", "last"],
        },
    )
    defects = gp.validate_pack(pack, require_full_seq=True)
    assert any("clay.mp4" in d or "rgb/" in d for d in defects)
    (pack / "clay.mp4").write_bytes(b"not-a-real-mp4")
    (pack / "depth.mp4").write_bytes(b"not-a-real-mp4")
    assert gp.validate_pack(pack, require_full_seq=True) == []


def test_cli_validate_fixture(gp: ModuleType) -> None:
    assert gp._cli(["validate", str(FIXTURE), "--fixture"]) == 0  # noqa: SLF001
    assert gp._cli(["validate", str(FIXTURE / "missing")]) == 1  # noqa: SLF001


def test_cli_json_ok(gp: ModuleType, capsys: pytest.CaptureFixture[str]) -> None:
    rc = gp._cli(["validate", str(FIXTURE), "--fixture"])  # noqa: SLF001
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True


def test_portrait_size_is_ltx_safe(gp: ModuleType) -> None:
    data = {
        "schema": gp.SCHEMA,
        "slug": "go-see",
        "shot_id": "12",
        "engine": "blender",
        "print": "ltx-iclora-canny",
        "frames": 120,
        "fps": 24,
        "size": [768, 1280],
        "layers": ["rgb", "depth", "canny", "first", "last"],
    }
    assert gp.validate_shot(data) == []


def test_canny_seq_required_when_listed(tmp_path: Path, gp: ModuleType) -> None:
    pack = tmp_path / "12"
    pack.mkdir()
    gp.write_solid_png(pack / "first.png", 1280, 704, (10, 10, 10))
    gp.write_solid_png(pack / "last.png", 1280, 704, (20, 20, 20))
    gp.write_shot_yaml(
        pack / "shot.yaml",
        {
            "schema": gp.SCHEMA,
            "slug": "go-see",
            "shot_id": "12",
            "engine": "blender",
            "print": "ltx-iclora-canny",
            "frames": 120,
            "fps": 24,
            "size": [1280, 704],
            "layers": ["rgb", "depth", "canny", "first", "last"],
        },
    )
    (pack / "clay.mp4").write_bytes(b"not-a-real-mp4")
    (pack / "depth.mp4").write_bytes(b"not-a-real-mp4")
    defects = gp.validate_pack(pack, require_full_seq=True)
    assert any("canny" in d for d in defects)
    (pack / "canny.mp4").write_bytes(b"not-a-real-mp4")
    assert gp.validate_pack(pack, require_full_seq=True) == []


def test_layers_for_print_includes_canny(gp: ModuleType) -> None:
    layers = gp.layers_for_print("ltx-iclora-depth")
    assert "canny" in layers
    assert "depth" in layers
    assert "normal" not in layers
    with_n = gp.layers_for_print("ltx-iclora-canny", include_normal=True)
    assert "normal" in with_n


def test_still_schema_and_sizes(tmp_path: Path, gp: ModuleType) -> None:
    still = {
        "schema": gp.STILL_SCHEMA,
        "slug": "go-see",
        "plate": "mug",
        "engine": "blender",
        "print": "klein-from-clay",
        "size": [1024, 1024],
        "layers": ["rgb", "depth", "canny", "first"],
    }
    assert gp.validate_still(still) == []
    still["size"] = [1280, 720]
    assert gp.validate_still(still) == []
    still["size"] = [1920, 1080]
    assert any("size" in d for d in gp.validate_still(still))
    still["size"] = [1024, 1024]
    still["print"] = "seedance"
    assert any("print" in d for d in gp.validate_still(still))
    dest = tmp_path / "mug"
    dest.mkdir()
    still["print"] = "klein-from-clay"
    gp.write_still_yaml(dest / "still.yaml", still)
    gp.write_solid_png(dest / "first.png", 1024, 1024, (8, 8, 8))
    gp.write_solid_png(dest / "depth.png", 1024, 1024, (9, 9, 9))
    gp.write_solid_png(dest / "canny.png", 1024, 1024, (1, 1, 1))
    assert gp.validate_still_pack(dest) == []
    (dest / "canny.png").unlink()
    assert any("canny.png" in d for d in gp.validate_still_pack(dest))
    assert gp.parse_size_token("1024x1024") == (1024, 1024)
    assert gp.parse_size_token("1280x704") == (1280, 704)
    assert gp.parse_size_token("nope") is None


def test_cli_validate_still(
    tmp_path: Path, gp: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    dest = tmp_path / "plate"
    dest.mkdir()
    still = {
        "schema": gp.STILL_SCHEMA,
        "slug": "go-see",
        "plate": "mug",
        "engine": "blender",
        "print": "klein-from-canny",
        "size": [768, 1280],
        "layers": ["rgb", "canny", "first"],
    }
    gp.write_still_yaml(dest / "still.yaml", still)
    gp.write_solid_png(dest / "first.png", 768, 1280, (3, 3, 3))
    gp.write_solid_png(dest / "canny.png", 768, 1280, (4, 4, 4))
    rc = gp._cli(["validate-still", str(dest)])  # noqa: SLF001
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert gp._cli(["validate-still", str(tmp_path / "missing")]) == 1  # noqa: SLF001


def _shot(gp: ModuleType, **overrides: object) -> dict:
    data: dict = {
        "schema": gp.SCHEMA,
        "slug": "go-see",
        "shot_id": "12",
        "engine": "blender",
        "print": "ltx-iclora-depth",
        "frames": 120,
        "fps": 24,
        "size": [1280, 704],
        "layers": ["rgb", "depth", "canny", "first", "last"],
    }
    data.update(overrides)
    return data


def _still(gp: ModuleType, **overrides: object) -> dict:
    data: dict = {
        "schema": gp.STILL_SCHEMA,
        "slug": "go-see",
        "plate": "mug",
        "engine": "blender",
        "print": "klein-from-clay",
        "size": [1024, 1024],
        "layers": ["rgb", "depth", "canny", "first"],
    }
    data.update(overrides)
    return data


def test_layers_unknown_print_and_png_errors(tmp_path: Path, gp: ModuleType) -> None:
    layers = gp.layers_for_print("not-a-print")
    assert "rgb" in layers
    as_dir = tmp_path / "dir.png"
    as_dir.mkdir()
    assert gp.png_size(as_dir) is None
    junk = tmp_path / "junk.png"
    junk.write_bytes(b"not a png at all..............")
    assert gp.png_size(junk) is None
    ihdr = tmp_path / "ihdr.png"
    ihdr.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rNOPE" + b"\x00" * 16)
    assert gp.png_size(ihdr) is None


def test_parse_shot_yaml_skips_and_bools(gp: ModuleType) -> None:
    parsed = gp.parse_shot_yaml(
        "\n".join(
            [
                "# comment",
                "  indented: skip",
                "nocolon",
                ": emptykey",
                "emptyval:",
                "flag: true",
                "off: false",
                "nums: [1, , 2]",
                "ratio: 1.5",
            ]
        )
        + "\n"
    )
    assert parsed["flag"] is True
    assert parsed["off"] is False
    assert parsed["nums"] == [1, 2]
    assert parsed["ratio"] == 1.5
    assert "emptyval" not in parsed


def test_validate_shot_and_still_defects(gp: ModuleType) -> None:
    defects = gp.validate_shot({})
    assert any("schema" in d for d in defects)
    assert any("slug" in d for d in defects)
    assert any("shot_id" in d for d in defects)
    fps = gp.validate_shot(_shot(gp, fps=30))
    assert any("fps" in d for d in fps)
    size_bad = gp.validate_shot(_shot(gp, size=["nope", "nope"]))
    assert any("size" in d for d in size_bad)
    size_none = gp.validate_shot(_shot(gp, size="wide"))
    assert any("size" in d for d in size_none)
    empty_layers = gp.validate_shot(_shot(gp, layers=[]))
    assert any("layers" in d for d in empty_layers)
    unknown = gp.validate_shot(_shot(gp, layers=["rgb", "albedo"]))
    assert any("unknown layer" in d for d in unknown)
    still_defects = gp.validate_still({})
    assert any("schema" in d for d in still_defects)
    assert any("slug" in d for d in still_defects)
    assert any("plate" in d for d in still_defects)
    engine = gp.validate_still(_still(gp, engine="maya"))
    assert any("engine" in d for d in engine)
    still_size = gp.validate_still(_still(gp, size=["x", "y"]))
    assert any("size" in d for d in still_size)
    still_size_none = gp.validate_still(_still(gp, size=1))
    assert any("size" in d for d in still_size_none)
    still_layers = gp.validate_still(_still(gp, layers=[]))
    assert any("layers" in d for d in still_layers)
    still_unknown = gp.validate_still(_still(gp, layers=["rgb", "albedo"]))
    assert any("still layer" in d for d in still_unknown)


def test_validate_pack_missing_and_size(tmp_path: Path, gp: ModuleType) -> None:
    missing = tmp_path / "no-pack"
    assert any("missing pack" in d for d in gp.validate_pack(missing))
    pack = tmp_path / "12"
    pack.mkdir()
    assert any("shot.yaml" in d for d in gp.validate_pack(pack, require_full_seq=False))
    gp.write_shot_yaml(pack / "shot.yaml", _shot(gp))
    defects = gp.validate_pack(pack, require_full_seq=False)
    assert any("first.png" in d for d in defects)
    gp.write_solid_png(pack / "first.png", 8, 8, (1, 1, 1))
    gp.write_solid_png(pack / "last.png", 8, 8, (2, 2, 2))
    sized = gp.validate_pack(pack, require_full_seq=False)
    assert any("size" in d for d in sized)
    (pack / "shot.yaml").write_text(
        gp.dump_shot_yaml(_shot(gp, size=[100, 100])), encoding="utf-8"
    )
    gp.write_solid_png(pack / "first.png", 1280, 704, (1, 1, 1))
    gp.write_solid_png(pack / "last.png", 1280, 704, (2, 2, 2))
    reset = gp.validate_pack(pack, require_full_seq=False)
    assert any("size" in d for d in reset)
    with pytest.raises(gp.GuidePackError):
        gp.write_shot_yaml(pack / "bad.yaml", _shot(gp, frames=1))
    gp.write_shot_yaml(
        pack / "shot.yaml",
        _shot(gp, identity_ref="hero", blend="x.blend", camera="CAM"),
    )
    text = (pack / "shot.yaml").read_text(encoding="utf-8")
    assert "identity_ref" in text
    assert "blend" in text
    rgb = pack / "rgb"
    rgb.mkdir()
    for i in range(3):
        (rgb / f"{i:04d}.png").write_bytes(b"x")
    count = gp.validate_pack(pack, require_full_seq=True)
    assert any("frame count" in d for d in count)
    assert gp._require_seq_or_mp4(pack, "id", require_full_seq=True) == []
    assert gp._pack_size({"size": ["a", "b"]}) == (gp.PACK_WIDTH, gp.PACK_HEIGHT)
    assert gp._pack_size({"size": 1}) == (gp.PACK_WIDTH, gp.PACK_HEIGHT)


def test_validate_still_pack_edges(tmp_path: Path, gp: ModuleType) -> None:
    missing = tmp_path / "no-still"
    assert any("missing still pack" in d for d in gp.validate_still_pack(missing))
    dest = tmp_path / "mug"
    dest.mkdir()
    assert any("still.yaml" in d for d in gp.validate_still_pack(dest))
    with pytest.raises(gp.GuidePackError):
        gp.write_still_yaml(dest / "still.yaml", _still(gp, print="seedance"))
    gp.write_still_yaml(
        dest / "still.yaml", _still(gp, blend="x.blend", camera="CAM")
    )
    text = (dest / "still.yaml").read_text(encoding="utf-8")
    assert "blend" in text
    no_first = gp.validate_still_pack(dest)
    assert any("first.png" in d for d in no_first)
    gp.write_solid_png(dest / "first.png", 8, 8, (1, 1, 1))
    gp.write_solid_png(dest / "depth.png", 8, 8, (2, 2, 2))
    gp.write_solid_png(dest / "canny.png", 8, 8, (3, 3, 3))
    mismatch = gp.validate_still_pack(dest)
    assert any("first.png size" in d for d in mismatch)
    (dest / "still.yaml").write_text(
        "\n".join(
            [
                f"schema: {gp.STILL_SCHEMA}",
                "slug: go-see",
                "plate: mug",
                "engine: blender",
                "print: klein-from-clay",
                "size: [nope, nope]",
                "layers: [rgb, depth, canny, first]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    gp.write_solid_png(dest / "first.png", 1024, 1024, (1, 1, 1))
    parsed_bad = gp.validate_still_pack(dest)
    assert parsed_bad
    gp.write_still_yaml(dest / "still.yaml", _still(gp))
    gp.write_solid_png(dest / "first.png", 1024, 1024, (1, 1, 1))
    gp.write_solid_png(dest / "depth.png", 8, 8, (2, 2, 2))
    gp.write_solid_png(dest / "canny.png", 1024, 1024, (3, 3, 3))
    layer_mismatch = gp.validate_still_pack(dest)
    assert any("depth.png size" in d for d in layer_mismatch)
    assert gp.parse_size_token("1024") is None
    assert gp.parse_size_token("axb") is None


def test_cli_validate_defects(
    tmp_path: Path, gp: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    pack = tmp_path / "empty"
    pack.mkdir()
    assert gp._cli(["validate", str(pack)]) == 1  # noqa: SLF001
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    still = tmp_path / "still-empty"
    still.mkdir()
    assert gp._cli(["validate-still", str(still)]) == 1  # noqa: SLF001
    still_payload = json.loads(capsys.readouterr().out)
    assert still_payload["ok"] is False

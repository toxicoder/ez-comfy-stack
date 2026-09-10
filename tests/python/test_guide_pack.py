"""Guide-pack schema and QC (hermetic: stdlib only, no Blender)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import guide_pack as gp  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "dcc" / "suzanne-12"
SCHEMA = ROOT / "schemas" / "guide_pack.shot.yaml"


def test_schema_file_documents_v1() -> None:
    text = SCHEMA.read_text(encoding="utf-8")
    assert "ez.guide.shot.v1" in text
    assert "1280" in text
    assert "704" in text
    assert "1280x720" in text or "1280×720" in text or "Never 1280" in text
    still_schema = ROOT / "schemas" / "guide_pack.still.yaml"
    still_text = still_schema.read_text(encoding="utf-8")
    assert "ez.guide.still.v1" in still_text
    assert "1024x1024" in still_text or "1024, 1024" in still_text


def test_fixture_pack_validates_without_full_seq() -> None:
    defects = gp.validate_pack(FIXTURE, require_full_seq=False)
    assert defects == [], defects


def test_fixture_shot_yaml_fields() -> None:
    shot = gp.load_shot(FIXTURE)
    assert gp.validate_shot(shot) == []
    assert shot["schema"] == gp.SCHEMA
    assert shot["frames"] == 120
    assert shot["fps"] == 24
    assert shot["size"] == [1280, 704]
    assert shot["engine"] == "blender"
    assert "first.png" in (FIXTURE / "first.png").name


def test_refuse_720_and_wrong_frame_count() -> None:
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


def test_unknown_engine_and_print() -> None:
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


def test_png_size_and_write(tmp_path: Path) -> None:
    path = tmp_path / "first.png"
    gp.write_solid_png(path, 1280, 704, (80, 80, 90))
    assert gp.png_size(path) == (1280, 704)
    gp.write_rgb_png(tmp_path / "tiny.png", 2, 2, bytes(range(12)))
    assert gp.png_size(tmp_path / "tiny.png") == (2, 2)
    with pytest.raises(ValueError, match="length"):
        gp.write_rgb_png(tmp_path / "bad.png", 2, 2, b"short")


def test_full_seq_require(tmp_path: Path) -> None:
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


def test_cli_validate_fixture() -> None:
    assert gp._cli(["validate", str(FIXTURE), "--fixture"]) == 0  # noqa: SLF001
    assert gp._cli(["validate", str(FIXTURE / "missing")]) == 1  # noqa: SLF001


def test_cli_json_ok(capsys: pytest.CaptureFixture[str]) -> None:
    rc = gp._cli(["validate", str(FIXTURE), "--fixture"])  # noqa: SLF001
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True


def test_portrait_size_is_ltx_safe() -> None:
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


def test_canny_seq_required_when_listed(tmp_path: Path) -> None:
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


def test_layers_for_print_includes_canny() -> None:
    layers = gp.layers_for_print("ltx-iclora-depth")
    assert "canny" in layers
    assert "depth" in layers
    assert "normal" not in layers
    with_n = gp.layers_for_print("ltx-iclora-canny", include_normal=True)
    assert "normal" in with_n


def test_still_schema_and_sizes(tmp_path: Path) -> None:
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
    assert gp.parse_size_token("1280×704") == (1280, 704)
    assert gp.parse_size_token("nope") is None


def test_cli_validate_still(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
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

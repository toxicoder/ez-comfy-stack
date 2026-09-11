"""Hermetic tests for ez_dcc (no Comfy, no GPU, no Blender, no torch)."""

from __future__ import annotations

import inspect
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
LIB = ROOT / "scripts" / "lib"
FIXTURE = ROOT / "tests" / "fixtures" / "dcc" / "suzanne-12"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

import ez_dcc  # noqa: E402
import guide_pack as gp  # noqa: E402
from ez_dcc import occupancy_gate as og  # noqa: E402
from ez_dcc import pack as dcc_pack  # noqa: E402
from ez_dcc import qc as dcc_qc  # noqa: E402
from ez_dcc.nodes import (  # noqa: E402
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
    EZDCCCameraJson,
    EZDCCLoadGuideStill,
    EZDCCLoadGuideVideo,
    EZDCCLoadStillPack,
    EZDCCOccupancyGate,
    EZDCCPreviewGuideLayer,
)
from ez_dcc.occupancy_gate import OccupancyError  # noqa: E402
from ez_dcc.qc import GuidePackError  # noqa: E402

DUMMY_IMAGE = object()
DUMMY_MASK = object()


def _install_shot_fixture(tmp_path: Path) -> Path:
    dest = tmp_path / "guides" / "go-see" / "12"
    shutil.copytree(FIXTURE, dest)
    return dest


def _write_occupancy(tmp_path: Path, mode: str) -> None:
    payload = {
        "version": 1,
        "mode": mode,
        "compose": False,
        "parked": mode == "blender-desk",
        "blender_pid": 0,
        "mcp_pid": 0,
        "updated": "",
    }
    (tmp_path / ".occupancy.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


@pytest.fixture
def output_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    monkeypatch.delenv("MODELS_DIR", raising=False)
    return tmp_path


@pytest.fixture
def decode_stub(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    seen: list[Path] = []

    def _fake(path: Path) -> tuple[object, object]:
        seen.append(Path(path))
        return DUMMY_IMAGE, DUMMY_MASK

    monkeypatch.setattr(dcc_pack, "decode_png", _fake)
    return seen


def test_pack_imports_without_torch_bpy_comfy() -> None:
    for name in ("torch", "bpy", "comfy"):
        sys.modules.pop(name, None)
    import importlib

    importlib.reload(ez_dcc)
    importlib.reload(dcc_pack)
    for name in ("torch", "bpy", "comfy"):
        assert name not in sys.modules
    assert not hasattr(ez_dcc, "WEB_DIRECTORY")


def test_six_nodes_registered() -> None:
    expected = {
        "EZDCCLoadGuideStill",
        "EZDCCLoadGuideVideo",
        "EZDCCLoadStillPack",
        "EZDCCCameraJson",
        "EZDCCPreviewGuideLayer",
        "EZDCCOccupancyGate",
    }
    assert set(NODE_CLASS_MAPPINGS) == expected
    assert ez_dcc.NODE_CLASS_MAPPINGS == NODE_CLASS_MAPPINGS
    assert NODE_DISPLAY_NAME_MAPPINGS["EZDCCLoadGuideStill"] == "Load guide still"
    for cls in NODE_CLASS_MAPPINGS.values():
        assert getattr(cls, "CATEGORY") == "ez-comfy/dcc"


def test_decode_png_imports_torch_lazily() -> None:
    source = inspect.getsource(dcc_pack.decode_png)
    assert "import torch" in source
    module_src = Path(dcc_pack.__file__).read_text(encoding="utf-8")
    head, _, _ = module_src.partition("def decode_png")
    assert "import torch" not in head


def test_suzanne_first_loads(
    output_dir: Path, decode_stub: list[Path]
) -> None:
    _install_shot_fixture(output_dir)
    node = EZDCCLoadGuideStill()
    image, mask, meta = node.run("go-see", "12", "first")
    assert image is DUMMY_IMAGE
    assert mask is DUMMY_MASK
    payload = json.loads(meta)
    assert payload["slug"] == "go-see"
    assert payload["frames"] == 120
    assert payload["size"] == [1280, 704]
    assert decode_stub[0].name == "first.png"
    assert "12" in str(decode_stub[0])


def test_refuse_720_shot_and_wrong_frame_count(
    output_dir: Path, decode_stub: list[Path]
) -> None:
    dest = output_dir / "guides" / "go-see" / "12"
    dest.mkdir(parents=True)
    gp.write_solid_png(dest / "first.png", 1280, 720, (1, 1, 1))
    gp.write_solid_png(dest / "last.png", 1280, 720, (2, 2, 2))
    (dest / "shot.yaml").write_text(
        "\n".join(
            [
                "schema: ez.guide.shot.v1",
                "slug: go-see",
                'shot_id: "12"',
                "engine: blender",
                "print: ltx-iclora-depth",
                "frames: 121",
                "fps: 24",
                "size: [1280, 720]",
                "layers: [rgb, depth, canny, first, last]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    node = EZDCCLoadGuideStill()
    with pytest.raises(GuidePackError, match="704|120|720"):
        node.run("go-see", "12", "first")
    assert decode_stub == []


def test_refuse_1080_still(output_dir: Path, decode_stub: list[Path]) -> None:
    dest = output_dir / "guides" / "go-see" / "stills" / "mug"
    dest.mkdir(parents=True)
    (dest / "still.yaml").write_text(
        "\n".join(
            [
                "schema: ez.guide.still.v1",
                "slug: go-see",
                "plate: mug",
                "engine: blender",
                "print: klein-from-clay",
                "size: [1920, 1080]",
                "layers: [rgb, first]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    gp.write_solid_png(dest / "first.png", 1920, 1080, (3, 3, 3))
    with pytest.raises(GuidePackError, match="size|1920|1080"):
        EZDCCLoadStillPack().run("go-see", "mug", "first")
    assert decode_stub == []


def test_depth_path_never_inverts(
    output_dir: Path, decode_stub: list[Path]
) -> None:
    _install_shot_fixture(output_dir)
    pack_src = Path(dcc_pack.__file__).read_text(encoding="utf-8")
    qc_src = Path(dcc_qc.__file__).read_text(encoding="utf-8")
    from ez_dcc import nodes as dcc_nodes

    nodes_src = Path(dcc_nodes.__file__).read_text(encoding="utf-8")
    for src in (pack_src, qc_src, nodes_src):
        assert "1.0 -" not in src
        assert "255 -" not in src
        assert "np.invert" not in src
        assert "~arr" not in src
        assert "1 - rgb" not in src
        assert "1 - arr" not in src
    EZDCCLoadGuideStill().run("go-see", "12", "depth")
    assert decode_stub[-1].name == "0001.png"
    assert decode_stub[-1].parent.name == "depth"


def test_occupancy_missing_file_passes(output_dir: Path) -> None:
    image = object()
    out = EZDCCOccupancyGate().run(image, "klein")
    assert out == (image,)
    assert og.read_mode(output_dir / ".occupancy.json") == "unknown"


def test_occupancy_blender_desk_vs_trellis_raises(output_dir: Path) -> None:
    _write_occupancy(output_dir, "blender-desk")
    with pytest.raises(OccupancyError, match="blender-desk|dumps"):
        EZDCCOccupancyGate().run(object(), "trellis")


def test_occupancy_matching_klein_passes(output_dir: Path) -> None:
    _write_occupancy(output_dir, "klein")
    image = object()
    assert EZDCCOccupancyGate().run(image, "klein") == (image,)


def test_occupancy_ltx_vs_klein_raises(output_dir: Path) -> None:
    _write_occupancy(output_dir, "ltx")
    with pytest.raises(OccupancyError, match="unload"):
        EZDCCOccupancyGate().run(object(), "klein")


def test_occupancy_idle_vs_klein_raises(output_dir: Path) -> None:
    _write_occupancy(output_dir, "idle")
    with pytest.raises(OccupancyError, match="occupancy enter klein"):
        EZDCCOccupancyGate().run(object(), "klein")


def test_occupancy_llm_desk_vs_klein_raises(output_dir: Path) -> None:
    _write_occupancy(output_dir, "llm-desk")
    with pytest.raises(OccupancyError, match="llm-desk|sidecar"):
        EZDCCOccupancyGate().run(object(), "klein")


def test_occupancy_invalid_json_fail_closed(output_dir: Path) -> None:
    (output_dir / ".occupancy.json").write_text("{not-json", encoding="utf-8")
    with pytest.raises(OccupancyError):
        EZDCCOccupancyGate().run(object(), "klein")


def test_occupancy_module_does_not_spawn_or_free() -> None:
    src = Path(og.__file__).read_text(encoding="utf-8")
    assert "subprocess" not in src
    assert "/free" not in src
    assert "POST" not in src
    assert "Popen" not in src


def test_preview_is_identity() -> None:
    image = object()
    assert EZDCCPreviewGuideLayer().run(image, "depth") == (image,)


def test_qc_defects_match_guide_pack(tmp_path: Path) -> None:
    assert dcc_qc.validate_pack(FIXTURE, require_full_seq=False) == gp.validate_pack(
        FIXTURE, require_full_seq=False
    )
    bad_shot = {
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
    assert dcc_qc.validate_shot(bad_shot) == gp.validate_shot(bad_shot)
    bad_still = {
        "schema": gp.STILL_SCHEMA,
        "slug": "go-see",
        "plate": "mug",
        "engine": "blender",
        "print": "klein-from-clay",
        "size": [1920, 1080],
        "layers": ["rgb", "first"],
    }
    assert dcc_qc.validate_still(bad_still) == gp.validate_still(bad_still)
    still_dir = tmp_path / "mug"
    still_dir.mkdir()
    good_still = dict(bad_still)
    good_still["size"] = [1024, 1024]
    gp.write_still_yaml(still_dir / "still.yaml", good_still)
    gp.write_solid_png(still_dir / "first.png", 1024, 1024, (8, 8, 8))
    assert dcc_qc.validate_still_pack(still_dir) == gp.validate_still_pack(still_dir)


def test_no_write_to_models_dir(
    output_dir: Path,
    decode_stub: list[Path],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    models = tmp_path / "models-root"
    models.mkdir()
    monkeypatch.setenv("MODELS_DIR", str(models))
    _install_shot_fixture(output_dir)
    (output_dir / "guides" / "go-see" / "12" / "clay.mp4").write_bytes(b"fake")
    (output_dir / "guides" / "go-see" / "12" / "camera.json").write_text(
        '{"ok": true}\n', encoding="utf-8"
    )
    EZDCCLoadGuideStill().run("go-see", "12", "first")
    EZDCCLoadGuideVideo().run("go-see", "12", "clay")
    EZDCCCameraJson().run("go-see", "12")
    EZDCCOccupancyGate().run(DUMMY_IMAGE, "klein")
    assert list(models.rglob("*")) == []


def test_camera_json_empty_when_missing(output_dir: Path) -> None:
    _install_shot_fixture(output_dir)
    assert EZDCCCameraJson().run("go-see", "12") == ("",)


def test_camera_json_loads_when_present(output_dir: Path) -> None:
    dest = _install_shot_fixture(output_dir)
    (dest / "camera.json").write_text('{"fov": 35}\n', encoding="utf-8")
    text, = EZDCCCameraJson().run("go-see", "12")
    assert '"fov": 35' in text


def test_load_guide_video_returns_path_not_frames(
    output_dir: Path, decode_stub: list[Path]
) -> None:
    dest = _install_shot_fixture(output_dir)
    mp4 = dest / "clay.mp4"
    mp4.write_bytes(b"not-a-real-mp4")
    path, fps = EZDCCLoadGuideVideo().run("go-see", "12", "clay")
    assert Path(path) == mp4.resolve()
    assert fps == 24
    assert decode_stub == []
    from ez_dcc import nodes as dcc_nodes

    src = Path(dcc_nodes.__file__).read_text(encoding="utf-8")
    video_cls = src.split("class EZDCCLoadGuideVideo")[1].split("class ")[0]
    assert "decode_png" not in video_cls


def test_load_still_pack_first(
    output_dir: Path, decode_stub: list[Path]
) -> None:
    dest = output_dir / "guides" / "go-see" / "stills" / "mug"
    dest.mkdir(parents=True)
    still = {
        "schema": gp.STILL_SCHEMA,
        "slug": "go-see",
        "plate": "mug",
        "engine": "blender",
        "print": "klein-from-clay",
        "size": [1024, 1024],
        "layers": ["rgb", "depth", "canny", "first"],
    }
    gp.write_still_yaml(dest / "still.yaml", still)
    gp.write_solid_png(dest / "first.png", 1024, 1024, (8, 8, 8))
    gp.write_solid_png(dest / "depth.png", 1024, 1024, (9, 9, 9))
    gp.write_solid_png(dest / "canny.png", 1024, 1024, (1, 1, 1))
    image, mask, meta = EZDCCLoadStillPack().run("go-see", "mug", "first")
    assert image is DUMMY_IMAGE
    assert mask is DUMMY_MASK
    assert json.loads(meta)["plate"] == "mug"
    assert decode_stub[-1].name == "first.png"


def test_output_directory_prefers_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    assert dcc_pack.output_directory() == tmp_path
    monkeypatch.delenv("COMFY_OUTPUT_DIR")
    fallback = dcc_pack.output_directory()
    assert str(fallback) != "/mnt/comfy-output"
    assert fallback == Path("/outputs") or fallback.name in {"outputs", "output"}


def test_defaults_slug_shot_plate() -> None:
    still = EZDCCLoadGuideStill.INPUT_TYPES()["required"]
    assert still["slug"][1]["default"] == "go-see"
    assert still["shot_id"][1]["default"] == "12"
    pack = EZDCCLoadStillPack.INPUT_TYPES()["required"]
    assert pack["plate"][1]["default"] == "mug"

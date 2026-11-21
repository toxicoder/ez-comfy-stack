"""Hermetic tests for ez_dcc (no Comfy, no GPU, no Blender, no torch)."""

from __future__ import annotations

import builtins
import importlib.util
import inspect
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

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
from ez_dcc.scene import (  # noqa: E402
    NODE_CLASS_MAPPINGS as SCENE_NODE_CLASS_MAPPINGS,
    EZSceneLayout,
)

DUMMY_IMAGE = object()
DUMMY_MASK = object()


def _install_shot_fixture(tmp_path: Path) -> Path:
    dest = tmp_path / "guides" / "go-see" / "12"
    shutil.copytree(FIXTURE, dest)
    return dest


def _write_occupancy(
    tmp_path: Path,
    mode: str,
    *,
    holders: dict[str, int] | None = None,
    pids_alive: dict[str, bool] | None = None,
) -> None:
    """Write an ``.occupancy.json`` record for gate tests.

    Args:
        tmp_path: Output directory holding the record.
        mode: Recorded occupancy mode.
        holders: PID fields to record; absent fields read 0.
        pids_alive: Host-stamped liveness map; ``None`` simulates a record
            written before the field existed.
    """
    claimed = holders or {}
    payload = {
        "version": 1,
        "mode": mode,
        "compose": False,
        "parked": mode == "blender-desk",
        "blender_pid": int(claimed.get("blender_pid", 0)),
        "mcp_pid": int(claimed.get("mcp_pid", 0)),
        "llm_pid": int(claimed.get("llm_pid", 0)),
        "updated": "",
    }
    if pids_alive is not None:
        payload["pids_alive"] = dict(pids_alive)
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


def test_seven_nodes_registered() -> None:
    expected = {
        "EZDCCLoadGuideStill",
        "EZDCCLoadGuideVideo",
        "EZDCCLoadStillPack",
        "EZDCCCameraJson",
        "EZDCCPreviewGuideLayer",
        "EZDCCOccupancyGate",
        "EZSceneLayout",
    }
    assert set(NODE_CLASS_MAPPINGS) == expected - {"EZSceneLayout"}
    assert set(ez_dcc.NODE_CLASS_MAPPINGS) == expected
    assert ez_dcc.NODE_CLASS_MAPPINGS == {
        **NODE_CLASS_MAPPINGS,
        **ez_dcc.scene.NODE_CLASS_MAPPINGS,
    }
    assert NODE_DISPLAY_NAME_MAPPINGS["EZDCCLoadGuideStill"] == "Load guide still"
    for cls in ez_dcc.NODE_CLASS_MAPPINGS.values():
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


def test_occupancy_live_blender_desk_vs_trellis_raises(output_dir: Path) -> None:
    _write_occupancy(
        output_dir,
        "blender-desk",
        holders={"blender_pid": 4242},
        pids_alive={"blender_pid": True, "mcp_pid": False, "llm_pid": False},
    )
    with pytest.raises(OccupancyError, match="blender-desk|Workbench"):
        EZDCCOccupancyGate().run(object(), "trellis")


def test_occupancy_orphan_blender_desk_releases(
    output_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Issues #380 / #381: a desk nobody is sitting at must not block the Queue."""
    image = object()
    _write_occupancy(output_dir, "blender-desk")
    assert EZDCCOccupancyGate().run(image, "trellis") == (image,)
    assert "no live sidecar" in capsys.readouterr().err


def test_occupancy_dead_pid_blender_desk_releases(output_dir: Path) -> None:
    _write_occupancy(
        output_dir,
        "blender-desk",
        holders={"blender_pid": 4242, "mcp_pid": 4243},
        pids_alive={"blender_pid": False, "mcp_pid": False, "llm_pid": False},
    )
    image = object()
    assert EZDCCOccupancyGate().run(image, "trellis") == (image,)


def test_occupancy_legacy_blender_desk_fails_closed(output_dir: Path) -> None:
    """A record predating the liveness stamp keeps the fail-closed answer."""
    _write_occupancy(output_dir, "blender-desk", holders={"blender_pid": 4242})
    with pytest.raises(OccupancyError, match="blender-desk"):
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


def test_occupancy_live_llm_desk_vs_klein_raises(output_dir: Path) -> None:
    _write_occupancy(
        output_dir,
        "llm-desk",
        holders={"llm_pid": 991},
        pids_alive={"blender_pid": False, "mcp_pid": False, "llm_pid": True},
    )
    with pytest.raises(OccupancyError, match="llm-desk|sidecar"):
        EZDCCOccupancyGate().run(object(), "klein")


def test_occupancy_orphan_llm_desk_releases(output_dir: Path) -> None:
    _write_occupancy(
        output_dir,
        "llm-desk",
        holders={"llm_pid": 991},
        pids_alive={"blender_pid": False, "mcp_pid": False, "llm_pid": False},
    )
    image = object()
    assert EZDCCOccupancyGate().run(image, "klein") == (image,)


def test_occupancy_live_mcp_only_desk_raises(output_dir: Path) -> None:
    """The Blender MCP alone is a live desk claim, not just the GUI PID."""
    _write_occupancy(
        output_dir,
        "blender-desk",
        holders={"mcp_pid": 77},
        pids_alive={"blender_pid": False, "mcp_pid": True, "llm_pid": False},
    )
    with pytest.raises(OccupancyError, match="blender-desk"):
        EZDCCOccupancyGate().run(object(), "trellis")


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
    sys.modules.pop("folder_paths", None)
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/outputs":
            return False
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    assert dcc_pack.output_directory() == tmp_path
    monkeypatch.delenv("COMFY_OUTPUT_DIR")
    fallback = dcc_pack.output_directory()
    assert str(fallback) != "/mnt/comfy-output"
    assert fallback == Path("/outputs") or fallback.name in {"outputs", "output"}


def test_output_directory_prefers_container_outputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", "/mnt/comfy-output")
    sys.modules.pop("folder_paths", None)
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/outputs":
            return True
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    assert dcc_pack.output_directory() == Path("/outputs")


def test_defaults_slug_shot_plate() -> None:
    still = EZDCCLoadGuideStill.INPUT_TYPES()["required"]
    assert still["slug"][1]["default"] == "go-see"
    assert still["shot_id"][1]["default"] == "12"
    pack = EZDCCLoadStillPack.INPUT_TYPES()["required"]
    assert pack["plate"][1]["default"] == "mug"
    video = EZDCCLoadGuideVideo.INPUT_TYPES()["required"]
    assert video["layer"][1]["default"] == "clay"
    camera = EZDCCCameraJson.INPUT_TYPES()["required"]
    assert camera["slug"][1]["default"] == "go-see"
    preview = EZDCCPreviewGuideLayer.INPUT_TYPES()["required"]
    assert preview["label"][1]["default"] == "guide"
    gate = EZDCCOccupancyGate.INPUT_TYPES()["required"]
    assert gate["required_mode"][1]["default"] == "klein"


def test_occupancy_json_array_fail_closed(output_dir: Path) -> None:
    (output_dir / ".occupancy.json").write_text("[]", encoding="utf-8")
    with pytest.raises(OccupancyError, match="not a JSON object"):
        EZDCCOccupancyGate().run(object(), "klein")


def test_qc_require_file_missing(tmp_path: Path) -> None:
    with pytest.raises(GuidePackError, match="missing"):
        dcc_qc.require_file(tmp_path / "nope.png", label="first")


def test_qc_load_from_path_spec_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(importlib.util, "spec_from_file_location", lambda *_a, **_k: None)
    with pytest.raises(ImportError, match="cannot load"):
        dcc_qc._load_from_path(Path(__file__), "x")
    monkeypatch.setattr(
        importlib.util,
        "spec_from_file_location",
        lambda *_a, **_k: SimpleNamespace(loader=None),
    )
    with pytest.raises(ImportError, match="cannot load"):
        dcc_qc._load_from_path(Path(__file__), "x")


def test_qc_guide_pack_import_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    orig_import = builtins.__import__

    def fake_import(
        name: str,
        globals: object = None,
        locals: object = None,
        fromlist: object = (),
        level: int = 0,
    ) -> object:
        if name == "guide_pack":
            raise ImportError("forced")
        return orig_import(name, globals, locals, fromlist, level)  # type: ignore[arg-type]

    monkeypatch.setattr(builtins, "__import__", fake_import)
    loaded = dcc_qc._load_guide_pack()
    assert hasattr(loaded, "validate_pack")
    orig_is_file = Path.is_file

    def hide_lib(self: Path) -> bool:
        if self.name == "guide_pack.py" and "scripts" in self.as_posix():
            return False
        return orig_is_file(self)

    monkeypatch.setattr(Path, "is_file", hide_lib)
    vendored = dcc_qc._load_guide_pack()
    assert hasattr(vendored, "validate_pack")

    def hide_both(self: Path) -> bool:
        if self.name in {"guide_pack.py", "_guide_pack.py"}:
            return False
        return orig_is_file(self)

    monkeypatch.setattr(Path, "is_file", hide_both)
    with pytest.raises(ImportError, match="unavailable"):
        dcc_qc._load_guide_pack()


# Every knob the two DCC files register, pinned by name and in INPUT_TYPES
# order, so a widget dropped from a spec cannot pass the tooltip invariant by
# not existing.
DCC_WIDGETS: dict[str, tuple[str, ...]] = {
    "EZDCCLoadGuideStill": ("slug", "shot_id", "layer"),
    "EZDCCLoadGuideVideo": ("slug", "shot_id", "layer"),
    "EZDCCLoadStillPack": ("slug", "plate", "layer"),
    "EZDCCCameraJson": ("slug", "shot_id"),
    "EZDCCPreviewGuideLayer": ("label",),
    "EZDCCOccupancyGate": ("required_mode",),
    "EZSceneLayout": (
        "scene_id",
        "assets",
        "camera_pos",
        "camera_look",
        "camera_fov",
        "hdri",
        "filename",
        "overwrite",
    ),
}
"""Widget names the DCC specs must keep exposing, in INPUT_TYPES order."""

# Connection-only sockets: the 722 shipped graphs wire these names, so they
# stay bare 1-tuples and owe no tooltip (no options dict carries one).
DCC_SOCKETS: dict[str, tuple[str, ...]] = {
    "EZDCCLoadGuideStill": (),
    "EZDCCLoadGuideVideo": (),
    "EZDCCLoadStillPack": (),
    "EZDCCCameraJson": (),
    "EZDCCPreviewGuideLayer": ("image",),
    "EZDCCOccupancyGate": ("image",),
    "EZSceneLayout": (),
}
"""Wires the DCC graphs join by name, so they must never gain an options dict."""

# Every widget that names a folder or a listing verb pins the exact wording,
# so a tooltip that points the operator at the wrong place still fails.
DCC_TOOLTIP_POINTERS: dict[str, tuple[str, ...]] = {
    "EZDCCLoadGuideStill.slug": ("<output>/guides/", "export-guides"),
    "EZDCCLoadGuideStill.shot_id": ("<output>/guides/", "export-guides --shot"),
    "EZDCCLoadGuideStill.layer": ("first and last", "mist 0-1"),
    "EZDCCLoadGuideVideo.slug": ("<output>/guides/", "export-guides"),
    "EZDCCLoadGuideVideo.shot_id": ("<output>/guides/", "export-guides --shot"),
    "EZDCCLoadGuideVideo.layer": ("clay.mp4", "24 fps"),
    "EZDCCLoadStillPack.slug": ("<output>/guides/<slug>/stills/", "blender-stills"),
    "EZDCCLoadStillPack.plate": (
        "<output>/guides/<slug>/stills/",
        "blender-stills --plate",
    ),
    "EZDCCLoadStillPack.layer": ("clay render", "mist 0-1"),
    "EZDCCCameraJson.slug": ("<output>/guides/", "export-guides"),
    "EZDCCCameraJson.shot_id": ("camera.json", "12"),
    "EZDCCPreviewGuideLayer.label": ("canvas",),
    "EZDCCOccupancyGate.required_mode": (
        "klein, trellis, wan, or ltx",
        "occupancy verb",
    ),
    "EZSceneLayout.scene_id": ("dawn-rooftop",),
    "EZSceneLayout.assets": ("<output>/assets/", "asset-ls"),
    "EZSceneLayout.camera_pos": ("metres", "2.1, 1.6, 3.4"),
    "EZSceneLayout.camera_look": ("metres", "0, 1.2, 0"),
    "EZSceneLayout.camera_fov": ("degrees", "35"),
    "EZSceneLayout.hdri": ("polyhaven:", "none"),
    "EZSceneLayout.filename": ("<output>/scenes/",),
    "EZSceneLayout.overwrite": ("<output>/scenes/",),
}
"""Folder or verb each tooltip must name, keyed by Class.widget."""

# The seven classes ez_dcc/__init__.py merges out of nodes.py and scene.py.
DCC_NODE_CLASSES = (
    EZDCCLoadGuideStill,
    EZDCCLoadGuideVideo,
    EZDCCLoadStillPack,
    EZDCCCameraJson,
    EZDCCPreviewGuideLayer,
    EZDCCOccupancyGate,
    EZSceneLayout,
)
"""Every class the two DCC registries register, in canvas-menu order."""


def _tooltip(cls: Any, section: str, widget: str) -> str:
    """Return the operator tooltip one widget spec carries.

    Args:
        cls: The registered node class.
        section: ``required`` or ``optional``.
        widget: Widget name inside that section.

    Returns:
        The tooltip string the options dict carries.
    """
    spec = cls.INPUT_TYPES()
    field = spec.get(section, {})[widget]
    assert len(field) == 2, f"{cls.__name__}.{widget} has no options dict"
    options = field[1]
    assert isinstance(options, dict), f"{cls.__name__}.{widget} has no options dict"
    tooltip = options.get("tooltip")
    assert isinstance(tooltip, str), f"{cls.__name__}.{widget} has no tooltip"
    return tooltip


def test_dcc_registries_merge_into_the_pack_registry() -> None:
    """Both files export a registry and __init__ merges all seven classes."""
    merged = set(ez_dcc.NODE_CLASS_MAPPINGS)
    assert merged == set(NODE_CLASS_MAPPINGS) | set(SCENE_NODE_CLASS_MAPPINGS)
    assert {cls.__name__ for cls in DCC_NODE_CLASSES} == merged
    assert merged, "the DCC registries registered nothing"


def test_every_registered_widget_carries_an_operator_tooltip() -> None:
    """Every DCC knob says what to type, in what unit, and where it lives."""
    assert set(DCC_WIDGETS) == set(ez_dcc.NODE_CLASS_MAPPINGS)
    seen: set[str] = set()
    for cls in DCC_NODE_CLASSES:
        spec = cls.INPUT_TYPES()
        sockets = DCC_SOCKETS[cls.__name__]
        widgets: list[str] = []
        for section in ("required", "optional"):
            for widget, field in spec.get(section, {}).items():
                where = f"{cls.__name__}.{section}.{widget}"
                assert isinstance(field, tuple), where
                if widget in sockets:
                    assert field == (field[0],), f"{where} socket is not bare"
                    continue
                assert len(field) == 2, f"{where} has no options dict"
                assert isinstance(field[1], dict), where
                tooltip = field[1].get("tooltip")
                assert isinstance(tooltip, str), f"{where} has no tooltip"
                assert tooltip.strip(), f"{where} tooltip is blank"
                assert tooltip == tooltip.strip(), f"{where} tooltip is padded"
                assert tooltip.isascii(), f"{where} tooltip is not ASCII"
                assert tooltip.endswith("."), f"{where} tooltip is not a sentence"
                widgets.append(widget)
                seen.add(f"{cls.__name__}.{widget}")
        assert tuple(widgets) == DCC_WIDGETS[cls.__name__], cls.__name__
        names = list(spec.get("required", {})) + list(spec.get("optional", {}))
        pinned = DCC_WIDGETS[cls.__name__]
        extras = tuple(name for name in names if name not in pinned)
        assert extras == sockets, cls.__name__
        assert len(names) == len(widgets) + len(sockets), cls.__name__
    assert seen, "the tooltip sweep saw no widget"
    assert seen == {
        f"{name}.{widget}" for name, widgets in DCC_WIDGETS.items() for widget in widgets
    }


def test_dcc_widget_and_socket_counts_are_pinned() -> None:
    """A spec that quietly lost a widget or gained a socket fails here."""
    assert sum(len(widgets) for widgets in DCC_WIDGETS.values()) == 21
    assert sum(len(sockets) for sockets in DCC_SOCKETS.values()) == 2


def test_image_sockets_stay_bare_tuples() -> None:
    """The two IMAGE wires keep the bare form the graphs and joins expect."""
    preview = EZDCCPreviewGuideLayer.INPUT_TYPES()["required"]["image"]
    assert preview == ("IMAGE",)
    gate = EZDCCOccupancyGate.INPUT_TYPES()["required"]["image"]
    assert gate == ("IMAGE",)


def test_tooltips_name_the_right_folder_and_listing_verb() -> None:
    """A typed value says which folder holds it and which verb lists it."""
    assert set(DCC_TOOLTIP_POINTERS) == {
        f"{name}.{widget}"
        for name, widgets in DCC_WIDGETS.items()
        for widget in widgets
    }
    for where, needles in DCC_TOOLTIP_POINTERS.items():
        cls_name, widget = where.split(".")
        cls = next(c for c in DCC_NODE_CLASSES if c.__name__ == cls_name)
        spec = cls.INPUT_TYPES()
        section = "required" if widget in spec.get("required", {}) else "optional"
        tooltip = _tooltip(cls, section, widget)
        for needle in needles:
            assert needle in tooltip, f"{where} tooltip does not name {needle!r}"


def test_scene_tooltips_carry_their_units() -> None:
    """Camera numbers read in metres and the field of view in degrees."""
    optional = EZSceneLayout.INPUT_TYPES()["optional"]
    assert optional["camera_fov"][1]["step"] == 1
    assert optional["camera_fov"][1]["min"] == 10
    assert optional["camera_fov"][1]["max"] == 120
    assert "degrees" in _tooltip(EZSceneLayout, "optional", "camera_fov")
    for widget in ("camera_pos", "camera_look"):
        assert "metres" in _tooltip(EZSceneLayout, "optional", widget), widget

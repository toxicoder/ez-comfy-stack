"""Hermetic tests for EZSceneLayout (no Comfy, no torch, no GPU, no Docker).

Covers every branch of ``custom_nodes/ez_dcc/scene.py``: widget contract,
document shape, Asset Bible reuse (the real ``scripts/lib/asset_bible``),
the MODELS_DIR refusal, overwrite policy, and fail-soft summaries.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
LIB = ROOT / "scripts" / "lib"
for _extra in (str(CUSTOM), str(LIB)):
    if _extra not in sys.path:
        sys.path.insert(0, _extra)

import asset_bible  # noqa: E402
from ez_dcc import nodes as dcc_nodes  # noqa: E402
from ez_dcc import scene  # noqa: E402
from ez_dcc.scene import EZSceneLayout  # noqa: E402

HERO = "hero-olive-jacket"
MUG = "mug-cobalt-chipped"


@pytest.fixture
def out_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the pack output dir at a temp tree (no Comfy, no /outputs bind).

    Args:
        tmp_path: pytest scratch directory.
        monkeypatch: pytest monkeypatch fixture.

    Returns:
        The temp directory the pack now reports as its output root.
    """
    monkeypatch.setattr(scene.dcc_pack, "output_directory", lambda: tmp_path)
    monkeypatch.delenv("MODELS_DIR", raising=False)
    return tmp_path


def _run(**kwargs: Any) -> Any:
    """Call ``EZSceneLayout.run`` with the required widgets prefilled.

    Args:
        **kwargs: Widget overrides merged over the defaults below.

    Returns:
        The node's OUTPUT_NODE payload.
    """
    widgets: dict[str, Any] = {"scene_id": "dawn-rooftop", "assets": HERO}
    widgets.update(kwargs)
    return EZSceneLayout().run(**widgets)


def _payload_scene(payload: Any) -> str:
    """Return the ``scene`` slot of an OUTPUT_NODE payload.

    Args:
        payload: Payload from :func:`_run`.

    Returns:
        Written path, or an empty string on refusal.
    """
    result: list[str] = list(payload["result"])
    return result[0]


def _payload_summary(payload: Any) -> str:
    """Return the ``ui.text`` status line of an OUTPUT_NODE payload.

    Args:
        payload: Payload from :func:`_run`.

    Returns:
        The single status line the canvas shows.
    """
    text: list[str] = list(payload["ui"]["text"])
    return text[0]


def _read(dest: Path) -> dict[str, Any]:
    """Parse a written scene document.

    Args:
        dest: Path returned in the ``scene`` slot.

    Returns:
        Parsed JSON object.
    """
    parsed: dict[str, Any] = json.loads(dest.read_text(encoding="utf-8"))
    return parsed


def _expected(out_root: Path, *parts: str) -> Path:
    """Return the resolved path the writer should produce under ``out_root``.

    Args:
        out_root: Temp output root the pack reports.
        *parts: Path parts below the output root.

    Returns:
        Resolved path, comparable with a resolved ``scene`` slot.
    """
    return out_root.joinpath("scenes", *parts).resolve()


def test_node_contract_matches_pack_convention() -> None:
    assert EZSceneLayout.RETURN_TYPES == ("STRING", "STRING")
    assert EZSceneLayout.RETURN_NAMES == ("scene", "summary")
    assert EZSceneLayout.FUNCTION == "run"
    assert EZSceneLayout.CATEGORY == "ez-comfy/dcc"
    assert EZSceneLayout.CATEGORY == scene.CATEGORY
    assert scene.CATEGORY == dcc_nodes.CATEGORY
    assert EZSceneLayout.OUTPUT_NODE is True
    assert isinstance(EZSceneLayout.DESCRIPTION, str)
    assert EZSceneLayout.DESCRIPTION


def test_registries_are_typed_and_complete() -> None:
    assert scene.NODE_CLASS_MAPPINGS == {"EZSceneLayout": EZSceneLayout}
    assert scene.NODE_DISPLAY_NAME_MAPPINGS == {
        "EZSceneLayout": "Compose 3D scene layout"
    }


def test_input_types_sections() -> None:
    spec = EZSceneLayout.INPUT_TYPES()
    required = spec["required"]
    optional = spec["optional"]
    assert set(required) == {"scene_id", "assets"}
    assert required["scene_id"][0] == "STRING"
    assert required["assets"][0] == "STRING"
    assert required["assets"][1]["multiline"] is True
    assert set(optional) == {
        "camera_pos",
        "camera_look",
        "camera_fov",
        "hdri",
        "filename",
        "overwrite",
    }
    assert optional["camera_pos"] == ("STRING", {"default": scene.DEFAULT_CAMERA_POS})
    assert optional["camera_look"] == ("STRING", {"default": scene.DEFAULT_CAMERA_LOOK})
    fov_type, fov_opts = optional["camera_fov"]
    assert fov_type == "INT"
    assert fov_opts == {
        "default": scene.DEFAULT_FOV,
        "min": scene.FOV_MIN,
        "max": scene.FOV_MAX,
        "step": 1,
    }
    assert optional["hdri"] == ("STRING", {"default": "none"})
    assert optional["filename"] == ("STRING", {"default": "scene"})
    assert optional["overwrite"] == ("BOOLEAN", {"default": False})


def test_scene_output_dir_uses_pack_output_dir(
    out_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(scene.dcc_pack, "output_directory", lambda: out_root / "deep")
    assert scene.scene_output_dir() == out_root / "deep" / "scenes"


def test_run_writes_indent2_document_with_trailing_newline(out_root: Path) -> None:
    payload = _run(
        assets=f"{HERO}:mesh/{HERO}.glb\n\n  {MUG}  \n",
        camera_pos="2.1, 1.6, 3.4",
        camera_look="0, 1.2, 0",
        camera_fov=40,
        hdri="polyhaven:kloppenheim_06",
    )
    dest = Path(_payload_scene(payload))
    assert dest == _expected(out_root, "scene.json")
    assert dest.is_file()
    assert _payload_summary(payload) == f"wrote 2 instances to {dest}"
    text = dest.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert '\n  "id": "dawn-rooftop"' in text
    doc = _read(dest)
    assert doc["id"] == "dawn-rooftop"
    assert [row["ref"] for row in doc["instances"]] == [HERO, MUG]
    assert doc["instances"][0]["t"] == [0.0, 0.0, 0.0]
    assert doc["instances"][1]["t"] == [scene.ROW_SPACING_M, 0.0, 0.0]
    assert doc["instances"][0]["r"] == [0.0, 0.0, 0.0]
    assert doc["instances"][0]["s"] == 1.0
    assert doc["camera"] == {"pos": [2.1, 1.6, 3.4], "look": [0.0, 1.2, 0.0], "fov": 40}
    assert doc["hdri"] == "polyhaven:kloppenheim_06"
    assert "mesh" not in text
    assert set(doc) == {"id", "instances", "camera", "hdri"}


def test_run_reuses_the_asset_bible_validator(out_root: Path) -> None:
    dest = Path(_payload_scene(_run(assets=f"{HERO}\n{MUG}")))
    record = asset_bible.load_scene(dest)
    assert record["id"] == "dawn-rooftop"
    assert len(record["instances"]) == 2


def test_run_uses_singular_wording_for_one_instance(out_root: Path) -> None:
    payload = _run()
    dest = Path(_payload_scene(payload))
    assert _payload_summary(payload) == f"wrote 1 instance to {dest}"


@pytest.mark.parametrize("hdri", ["none", "NONE", "  none  ", "", "   "])
def test_run_omits_hdri_for_sentinel(out_root: Path, hdri: str) -> None:
    dest = Path(_payload_scene(_run(hdri=hdri)))
    assert set(_read(dest)) == {"id", "instances", "camera"}


def test_run_falls_back_to_the_default_camera_when_blank(out_root: Path) -> None:
    dest = Path(_payload_scene(_run(camera_pos="  ", camera_look="")))
    assert _read(dest)["camera"] == {
        "pos": [2.1, 1.6, 3.4],
        "look": [0.0, 1.2, 0.0],
        "fov": scene.DEFAULT_FOV,
    }


def test_run_accepts_boundary_fov_values(out_root: Path) -> None:
    low = Path(_payload_scene(_run(camera_fov=scene.FOV_MIN, filename="low")))
    assert _read(low)["camera"]["fov"] == scene.FOV_MIN
    high = Path(_payload_scene(_run(camera_fov=scene.FOV_MAX, filename="high")))
    assert _read(high)["camera"]["fov"] == scene.FOV_MAX


def test_run_refuses_to_overwrite_without_the_flag(out_root: Path) -> None:
    first = _run()
    payload = _run()
    assert _payload_scene(payload) == ""
    assert f"{Path(_payload_scene(first))} exists" in _payload_summary(payload)
    assert "set overwrite" in _payload_summary(payload)


def test_run_overwrites_when_the_flag_is_set(out_root: Path) -> None:
    first = Path(_payload_scene(_run(assets=HERO)))
    payload = _run(assets=MUG, overwrite=True)
    assert _payload_scene(payload) == str(first)
    assert [row["ref"] for row in _read(first)["instances"]] == [MUG]


@pytest.mark.parametrize(
    ("filename", "written"),
    [("dawn-set", "dawn-set.json"), ("dawn-set.json", "dawn-set.json")],
)
def test_run_normalises_the_filename_suffix(
    out_root: Path, filename: str, written: str
) -> None:
    dest = Path(_payload_scene(_run(filename=filename)))
    assert dest.name == written


def test_run_defaults_the_filename_when_blank(out_root: Path) -> None:
    dest = Path(_payload_scene(_run(filename="   ")))
    assert dest.name == "scene.json"


@pytest.mark.parametrize(
    "filename", ["../evil", "a/b", "a\\b", ".hidden", "/abs/scene", "scenes/one"]
)
def test_run_rejects_a_pathlike_filename(out_root: Path, filename: str) -> None:
    payload = _run(filename=filename)
    assert _payload_scene(payload) == ""
    assert "plain basename" in _payload_summary(payload)
    assert list(out_root.rglob("*.json")) == []


def test_run_writes_only_inside_the_scenes_dir(out_root: Path) -> None:
    dest = Path(_payload_scene(_run(filename="rooftop")))
    assert dest == _expected(out_root, "rooftop.json")
    assert sorted(p.name for p in dest.parent.iterdir()) == ["rooftop.json"]


def test_run_refuses_to_write_into_models_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    models = tmp_path / "models"
    monkeypatch.setenv("MODELS_DIR", str(models))
    monkeypatch.setattr(scene.dcc_pack, "output_directory", lambda: models)
    payload = _run()
    summary = _payload_summary(payload)
    assert _payload_scene(payload) == ""
    assert "AssetBibleError" in summary
    assert "MODELS_DIR" in summary or "models cache" in summary
    assert not models.exists()


def test_run_refuses_a_named_models_cache_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "models-cache" / "models"
    monkeypatch.delenv("MODELS_DIR", raising=False)
    monkeypatch.setattr(scene.dcc_pack, "output_directory", lambda: cache)
    payload = _run()
    assert _payload_scene(payload) == ""
    assert "named models cache" in _payload_summary(payload)


def test_run_reports_a_write_failure_as_a_summary(out_root: Path) -> None:
    blocker = out_root / "scenes" / "scene.json"
    blocker.mkdir(parents=True)
    payload = _run(overwrite=True)
    assert _payload_scene(payload) == ""
    assert "IsADirectoryError" in _payload_summary(payload)


def test_run_fails_soft_when_the_asset_bible_is_missing(
    out_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(sys.modules, "asset_bible", None)
    monkeypatch.setattr(scene, "_LIB_RELPATH", ("scripts", "lib", "absent_bible.py"))
    payload = _run()
    assert _payload_scene(payload) == ""
    assert "ImportError" in _payload_summary(payload)
    assert "asset_bible is unavailable" in _payload_summary(payload)
    assert not (out_root / "scenes").exists()


def test_run_fails_soft_on_a_non_string_widget(out_root: Path) -> None:
    payload = _run(assets=None)
    assert _payload_scene(payload) == ""
    assert "AttributeError" in _payload_summary(payload)


@pytest.mark.parametrize("assets", ["", "   ", "\n\n", " \n \n "])
def test_run_requires_at_least_one_asset(out_root: Path, assets: str) -> None:
    payload = _run(assets=assets)
    assert "assets must name at least one slug" in _payload_summary(payload)


@pytest.mark.parametrize("scene_id", ["", "  ", "Dawn", "dawn rooftop", "dawn_rooftop"])
def test_run_requires_a_slug_scene_id(out_root: Path, scene_id: str) -> None:
    payload = _run(scene_id=scene_id)
    assert "scene_id must be lowercase-hyphenated" in _payload_summary(payload)


@pytest.mark.parametrize(
    ("line", "fragment"),
    [
        ("Hero-Jacket", "asset slug must be lowercase-hyphenated"),
        (f"{HERO}:", "empty path after ':'"),
        (f"{HERO}:/abs/mesh.glb", "path must be relative"),
        (f"{HERO}:mesh\\bad.glb", "path must be relative"),
        (f"{HERO}:../evil.glb", "must not contain '..'"),
        (f"{HERO}:mesh/view.png", "must end .glb"),
    ],
)
def test_run_rejects_a_bad_asset_line(out_root: Path, line: str, fragment: str) -> None:
    payload = _run(assets=line)
    assert _payload_scene(payload) == ""
    assert fragment in _payload_summary(payload)


@pytest.mark.parametrize(
    ("widget", "value", "fragment"),
    [
        ("camera_pos", "1, 2", "camera_pos needs three comma-separated numbers"),
        ("camera_pos", "1, 2, x", "camera_pos has a non-numeric part"),
        ("camera_pos", "1, 2, nan", "camera_pos needs finite numbers"),
        ("camera_look", "0", "camera_look needs three comma-separated numbers"),
        ("camera_look", "0, 0, inf", "camera_look needs finite numbers"),
    ],
)
def test_run_rejects_a_bad_camera_triple(
    out_root: Path, widget: str, value: str, fragment: str
) -> None:
    widgets: dict[str, Any] = {widget: value}
    payload = _run(**widgets)
    assert _payload_scene(payload) == ""
    assert fragment in _payload_summary(payload)


@pytest.mark.parametrize(
    ("value", "fragment"),
    [
        (scene.FOV_MIN - 1, "camera_fov must be 10-120"),
        (scene.FOV_MAX + 1, "camera_fov must be 10-120"),
        ("wide", "camera_fov must be a whole number"),
        (None, "camera_fov must be a whole number"),
    ],
)
def test_run_rejects_a_bad_fov(out_root: Path, value: Any, fragment: str) -> None:
    payload = _run(camera_fov=value)
    assert _payload_scene(payload) == ""
    assert fragment in _payload_summary(payload)


def test_run_refuses_an_embedded_mesh_string(out_root: Path) -> None:
    payload = _run(hdri="polyhaven:" + "x" * 5000)
    assert _payload_scene(payload) == ""
    assert "AssetBibleError" in _payload_summary(payload)
    assert not (out_root / "scenes" / "scene.json").exists()


def test_build_scene_returns_the_schema_document() -> None:
    doc: Any = scene.build_scene(
        scene_id="dawn-rooftop",
        assets=f"{HERO}\n{MUG}:mesh/{MUG}.glb",
        camera_pos="1,2,3",
        camera_look=" 0 , 1 , 2 ",
        camera_fov=35,
        hdri="polyhaven:kloppenheim_06",
    )
    assert doc["id"] == "dawn-rooftop"
    assert doc["camera"] == {"pos": [1.0, 2.0, 3.0], "look": [0.0, 1.0, 2.0], "fov": 35}
    assert doc["hdri"] == "polyhaven:kloppenheim_06"
    assert doc["instances"][1]["ref"] == MUG


def test_clean_hdri_keeps_a_real_reference() -> None:
    assert scene._clean_hdri("  polyhaven:studio  ") == "polyhaven:studio"
    assert scene._clean_hdri("none") is None
    assert scene._clean_hdri("") is None


def test_parse_instances_lays_rows_out_along_plus_x() -> None:
    rows: Any = scene._parse_instances(f"{HERO}\n\n{MUG}")
    assert [row["t"] for row in rows] == [
        [0.0, 0.0, 0.0],
        [scene.ROW_SPACING_M, 0.0, 0.0],
    ]


def test_parse_ref_accepts_a_bare_slug_and_a_hinted_one() -> None:
    assert scene._parse_ref(HERO) == HERO
    assert scene._parse_ref(f" {HERO} : mesh/hero.glb ") == HERO


def test_parse_triple_returns_floats() -> None:
    assert scene._parse_triple(" -1.5, 0, 2 ", "camera_pos") == [-1.5, 0.0, 2.0]


def test_resolve_dest_appends_the_suffix(out_root: Path) -> None:
    assert scene._resolve_dest("rooftop") == _expected(out_root, "rooftop.json")
    assert scene._resolve_dest("rooftop.json") == _expected(out_root, "rooftop.json")


def test_resolve_dest_rejects_a_traversal(out_root: Path) -> None:
    with pytest.raises(scene.SceneLayoutError, match="plain basename"):
        scene._resolve_dest("../scene")


def test_require_slug_returns_the_slug_and_rejects_other_shapes() -> None:
    assert scene._require_slug("dawn-rooftop", "scene_id") == "dawn-rooftop"
    with pytest.raises(scene.SceneLayoutError, match="scene_id"):
        scene._require_slug("Dawn", "scene_id")


def test_require_glb_path_accepts_a_relative_glb() -> None:
    scene._require_glb_path("mesh/hero.glb", HERO)
    scene._require_glb_path("MESH/HERO.GLB", HERO)


def test_load_asset_bible_prefers_pythonpath() -> None:
    assert scene._load_asset_bible() is asset_bible


def test_load_asset_bible_falls_back_to_scripts_lib(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "asset_bible", None)
    loaded = scene._load_asset_bible()
    assert loaded is not asset_bible
    assert callable(loaded.validate_scene)
    assert loaded.MAX_SCENE_BYTES == asset_bible.MAX_SCENE_BYTES


def test_load_asset_bible_raises_when_nowhere_to_find_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "asset_bible", None)
    monkeypatch.setattr(scene, "_LIB_RELPATH", ("scripts", "lib", "absent_bible.py"))
    with pytest.raises(ImportError, match="asset_bible is unavailable"):
        scene._load_asset_bible()


def test_module_from_path_refuses_an_unloadable_file(tmp_path: Path) -> None:
    with pytest.raises(ImportError, match="cannot load"):
        scene._module_from_path(tmp_path / "no-suffix", "no_suffix")


def test_module_from_path_executes_a_real_module(tmp_path: Path) -> None:
    source = tmp_path / "written_module.py"
    source.write_text("MARKER = 7\n", encoding="utf-8")
    loaded = scene._module_from_path(source, "written_module")
    assert loaded.MARKER == 7

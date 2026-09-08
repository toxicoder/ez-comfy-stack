"""Asset Bible contract (ez.asset.v1) — hermetic, no TRELLIS/network."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import asset_bible as ab  # noqa: E402

FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "assets"
FIXTURE_YAML = FIXTURE_ROOT / "objects" / "mug-cobalt-chipped" / "asset.yaml"
SCHEMA_YAML = ROOT / "schemas" / "asset.yaml"
SCHEMA_SCENE = ROOT / "schemas" / "scene.json"


def test_fixture_yaml_validates() -> None:
    asset = ab.load_asset(FIXTURE_YAML)
    assert asset["schema"] == ab.SCHEMA
    assert asset["id"] == "mug-cobalt-chipped"
    assert asset["kind"] == "object"
    assert asset["pipeline"] == "klein-trellis2"
    assert asset["seed"] == 42
    assert asset["ready"] is True
    assert asset["parent"] is None
    assert "preview" in asset["files"]
    assert "prop" in asset["tags"]
    schema_asset = ab.load_asset(SCHEMA_YAML)
    assert schema_asset["id"] == "mug-cobalt-chipped"


def test_kinds_and_pipelines_enum() -> None:
    assert ab.SCHEMA == "ez.asset.v1"
    assert ab.KINDS == {
        "object",
        "character",
        "building",
        "set",
        "scene",
        "material",
        "hdri",
    }
    assert "klein-trellis2" in ab.PIPELINES
    assert "klein-edit" in ab.PIPELINES
    assert "bpy-primitive" in ab.PIPELINES
    assert "mcp-construct" in ab.PIPELINES
    assert "scene-assemble" in ab.PIPELINES
    assert "spaceship" not in ab.KINDS
    with pytest.raises(ab.AssetBibleError, match="kind"):
        ab.validate_asset(
            {
                "schema": ab.SCHEMA,
                "id": "nope",
                "kind": "spaceship",
                "prompt": "x",
                "seed": 1,
                "pipeline": "klein-trellis2",
                "parent": None,
                "takes": [],
                "files": {"preview": True},
                "tags": [],
                "license": "operator-output",
                "ready": False,
            }
        )


def test_scene_instances_slugs_reject_embedded_mesh() -> None:
    scene = ab.load_scene(SCHEMA_SCENE)
    assert scene["id"] == "dawn-rooftop"
    assert scene["instances"][0]["ref"] == "hero-olive-jacket"
    assert scene["instances"][1]["ref"] == "mug-cobalt-chipped"
    with pytest.raises(ab.AssetBibleError, match="ref"):
        ab.validate_scene({"id": "x", "instances": [{"t": [0, 0, 0]}]})
    with pytest.raises(ab.AssetBibleError, match="embed"):
        ab.validate_scene(
            {
                "id": "x",
                "instances": [
                    {
                        "ref": "mug-cobalt-chipped",
                        "mesh": "AAAA" + ("A" * 80),
                    }
                ],
            }
        )
    huge = "A" * 500
    with pytest.raises(ab.AssetBibleError, match="base64"):
        ab.validate_scene(
            {
                "id": "x",
                "instances": [
                    {
                        "ref": "mug-cobalt-chipped",
                        "preview": f"data:model/gltf-binary;base64,{huge}",
                    }
                ],
            }
        )
    with pytest.raises(ab.AssetBibleError, match="numeric array"):
        ab.validate_scene(
            {
                "id": "x",
                "instances": [{"ref": "mug-cobalt-chipped", "t": list(range(32))}],
            }
        )


def test_refuse_write_under_models_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    models = tmp_path / "models"
    models.mkdir()
    monkeypatch.setenv("MODELS_DIR", str(models))
    with pytest.raises(ab.AssetBibleError, match="MODELS_DIR"):
        ab.refuse_models_dir(models)
    with pytest.raises(ab.AssetBibleError, match="MODELS_DIR"):
        ab.ensure_layout(models, "object", "mug-cobalt-chipped")
    with pytest.raises(ab.AssetBibleError, match="MODELS_DIR"):
        ab.write_index(models / "stolen-assets")
    with pytest.raises(ab.AssetBibleError, match="MODELS_DIR"):
        ab.list_assets(models / "assets")
    monkeypatch.setenv("MODELS_DIR", str(tmp_path / "other-models"))
    named = tmp_path / "hf" / "models" / "cache"
    named.mkdir(parents=True)
    with pytest.raises(ab.AssetBibleError, match="models cache"):
        ab.refuse_models_dir(named)


def test_index_yaml_writer_from_tmp_tree(tmp_path: Path) -> None:
    catalog = tmp_path / "assets"
    dest = ab.ensure_layout(catalog, "object", "mug-cobalt-chipped")
    dest.joinpath("asset.yaml").write_text(
        FIXTURE_YAML.read_text(encoding="utf-8"), encoding="utf-8"
    )
    index = ab.write_index(catalog)
    assert index == catalog / "index.yaml"
    text = index.read_text(encoding="utf-8")
    assert "ez.asset-index.v1" in text
    assert "mug-cobalt-chipped" in text
    assert "klein-trellis2" in text
    assert "objects/mug-cobalt-chipped" in text
    records = ab.list_assets(catalog)
    assert len(records) == 1
    assert records[0]["path"] == "objects/mug-cobalt-chipped"
    assert (dest / "mesh").is_dir()
    assert (dest / "views").is_dir()
    assert (dest / "variants").is_dir()
    assert (dest / "prompts.jsonl").is_file()


def test_missing_required_fields_fail_closed() -> None:
    with pytest.raises(ab.AssetBibleError, match="missing required fields"):
        ab.validate_asset({"schema": ab.SCHEMA, "id": "mug-cobalt-chipped"})
    with pytest.raises(ab.AssetBibleError, match="schema"):
        ab.validate_asset(
            {
                "schema": "ez.asset.v0",
                "id": "mug-cobalt-chipped",
                "kind": "object",
                "prompt": "x",
                "seed": 1,
                "pipeline": "klein-trellis2",
                "parent": None,
                "takes": [],
                "files": {"preview": True},
                "tags": [],
                "license": "operator-output",
                "ready": True,
            }
        )
    with pytest.raises(ab.AssetBibleError, match="pipeline"):
        parsed = ab.parse_restricted_yaml(FIXTURE_YAML.read_text(encoding="utf-8"))
        parsed["pipeline"] = "city-from-sentence"
        ab.validate_asset(parsed)
    with pytest.raises(ab.AssetBibleError, match="seed"):
        parsed = ab.parse_restricted_yaml(FIXTURE_YAML.read_text(encoding="utf-8"))
        parsed["seed"] = True
        ab.validate_asset(parsed)


def test_cli_validate_and_ls(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    assert ab._cli(["validate", str(FIXTURE_YAML)]) == 0  # noqa: SLF001
    assert ab._cli(["validate", str(SCHEMA_SCENE)]) == 0  # noqa: SLF001
    out = capsys.readouterr().out
    assert "mug-cobalt-chipped" in out
    assert "dawn-rooftop" in out
    empty = tmp_path / "empty-assets"
    empty.mkdir()
    assert ab._cli(["ls", "--output-dir", str(empty), "--json"]) == 0  # noqa: SLF001
    payload = json.loads(capsys.readouterr().out)
    assert payload == []
    assert ab._cli(["ls", "--output-dir", str(FIXTURE_ROOT), "--json"]) == 0  # noqa: SLF001
    listed = json.loads(capsys.readouterr().out)
    assert listed[0]["id"] == "mug-cobalt-chipped"
    missing = tmp_path / "nope.yaml"
    assert ab._cli(["validate", str(missing)]) == 1  # noqa: SLF001

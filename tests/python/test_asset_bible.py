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


def _valid_asset(**overrides: object) -> dict:
    data: dict = {
        "schema": ab.SCHEMA,
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
        "ready": False,
    }
    data.update(overrides)
    return data


def test_kind_dirname_unknown() -> None:
    with pytest.raises(ab.AssetBibleError, match="unknown kind"):
        ab.kind_dirname("spaceship")


def test_yaml_helpers_quotes_escapes_and_flow() -> None:
    assert ab._strip_comment('a: "b # c"') == 'a: "b # c"'
    assert ab._strip_comment("a: 'b # c'") == "a: 'b # c'"
    assert ab._strip_comment('a: "b\\"c" # gone').startswith('a: "b\\"c"')
    assert ab._strip_comment("a: 1 # gone") == "a: 1 "
    assert ab._unescape_double(r"a\n\t\r\"\\\q") == "a\n\t\r\"\\q"
    assert ab._split_key("a: b") == ("a", " b")
    assert ab._split_key("'a:b': rest")[0] == "'a:b'"
    assert ab._split_key('"a:b": rest')[0] == '"a:b"'
    with pytest.raises(ab.AssetBibleError, match="expected key"):
        ab._split_key("nocolon")
    parts = ab._split_flow(r'a, "b,c", {x: 1, y: [2, 3]}, \'d,e\', "p\\,q"')
    assert parts[0] == "a"
    assert "b,c" in parts[1]
    assert parts[-1].startswith('"')
    empty, idx = ab._parse_value_block([], 0, 0)
    assert empty is None and idx == 0
    skipped, idx2 = ab._parse_value_block([(0, "a: 1")], 0, 2)
    assert skipped is None and idx2 == 0


def test_parse_restricted_yaml_branches() -> None:
    parsed = ab.parse_restricted_yaml(
        "\n".join(
            [
                "schema: ez.asset.v1",
                "id: hero-olive-jacket",
                "kind: character",
                'prompt: "line with hash"',
                "quoted: 'single'",
                r'escaped: "new\nline"',
                "flag_false: false",
                "flag_no: no",
                "flag_off: off",
                "empty_map: {}",
                "empty_list: []",
                "flow_map: {a: 1, b, c:}",
                "parent:",
                "seed: 0",
                "pipeline: klein-edit",
                "takes:",
                "  - v001",
                "  - foo: 1",
                "    bar: 2",
                "  - plain",
                "files:",
                "  - preview",
                "  - mesh",
                "tags: [prop]",
                "license: operator-output",
                "ready: false",
            ]
        )
        + "\n"
    )
    assert parsed["flag_false"] is False
    assert parsed["empty_map"] == {}
    assert parsed["empty_list"] == []
    assert parsed["flow_map"]["b"] is True
    assert parsed["parent"] is None
    assert parsed["takes"][1] == {"foo": 1, "bar": 2}
    assert parsed["takes"][2] == "plain"
    assert parsed["files"] == ["preview", "mesh"]
    with pytest.raises(ab.AssetBibleError, match="tabs"):
        ab.parse_restricted_yaml("a:\t1\n")
    with pytest.raises(ab.AssetBibleError, match="indent"):
        ab.parse_restricted_yaml(" a: 1\n")
    with pytest.raises(ab.AssetBibleError, match="unexpected indent"):
        ab.parse_restricted_yaml("a: 1\n  b: 2\n")
    with pytest.raises(ab.AssetBibleError, match="unexpected list"):
        ab.parse_restricted_yaml("a: 1\n- b\n")
    with pytest.raises(ab.AssetBibleError, match="expected list item"):
        ab.parse_restricted_yaml("items:\n  - a\n  b: 1\n")
    with pytest.raises(ab.AssetBibleError, match="empty YAML"):
        ab.parse_restricted_yaml("\n# only comment\n")
    nested, _idx = ab._parse_list([(0, "- "), (2, "nested: 1")], 0, 0)
    assert nested == [{"nested": 1}]
    empty_items, _idx2 = ab._parse_list([(0, "- ")], 0, 0)
    assert empty_items == [None]


def test_parse_unparsed_leftover(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ab, "_parse_value_block", lambda _lines, _start, _min: ({"ok": True}, 0)
    )
    with pytest.raises(ab.AssetBibleError, match="unparsed"):
        ab.parse_restricted_yaml("a: 1\nb: 2\n")


def test_validate_asset_field_branches() -> None:
    with pytest.raises(ab.AssetBibleError, match="mapping"):
        ab.validate_asset(["nope"])
    with pytest.raises(ab.AssetBibleError, match="slug"):
        ab.validate_asset(_valid_asset(id="Nope"))
    with pytest.raises(ab.AssetBibleError, match="prompt"):
        ab.validate_asset(_valid_asset(prompt="  "))
    with pytest.raises(ab.AssetBibleError, match="parent"):
        ab.validate_asset(_valid_asset(parent="Not-Slug"))
    with pytest.raises(ab.AssetBibleError, match="license"):
        ab.validate_asset(_valid_asset(license=""))
    with pytest.raises(ab.AssetBibleError, match="ready"):
        ab.validate_asset(_valid_asset(ready=1))
    with pytest.raises(ab.AssetBibleError, match="takes"):
        ab.validate_asset(_valid_asset(takes="v001"))
    with pytest.raises(ab.AssetBibleError, match="files list"):
        ab._normalize_files([])
    with pytest.raises(ab.AssetBibleError, match="files mapping"):
        ab._normalize_files({})
    with pytest.raises(ab.AssetBibleError, match="files keys"):
        ab._normalize_files({"": True})
    with pytest.raises(ab.AssetBibleError, match="files keys"):
        ab._normalize_files({1: True})
    with pytest.raises(ab.AssetBibleError, match="files must be"):
        ab._normalize_files("preview")
    ok = ab.validate_asset(_valid_asset(files=["preview", "mesh"], parent="mug-cobalt-chipped"))
    assert ok["files"] == {"preview": True, "mesh": True}
    assert ok["parent"] == "mug-cobalt-chipped"


def test_scene_and_file_validate_edges(tmp_path: Path) -> None:
    with pytest.raises(ab.AssetBibleError, match="object"):
        ab.validate_scene([])
    with pytest.raises(ab.AssetBibleError, match="id is required"):
        ab.validate_scene({"id": "", "instances": [{"ref": "x"}]})
    with pytest.raises(ab.AssetBibleError, match="non-empty list"):
        ab.validate_scene({"id": "dawn", "instances": []})
    with pytest.raises(ab.AssetBibleError, match="must be an object"):
        ab.validate_scene({"id": "dawn", "instances": ["nope"]})
    with pytest.raises(ab.AssetBibleError, match="embedded base64"):
        ab.validate_scene(
            {
                "id": "dawn",
                "instances": [{"ref": "mug-cobalt-chipped", "note": "base64" + ("A" * 200)}],
            }
        )
    with pytest.raises(ab.AssetBibleError, match="too long"):
        ab.validate_scene(
            {
                "id": "dawn",
                "instances": [{"ref": "mug-cobalt-chipped", "note": "x" * (ab.MAX_STRING_CHARS + 1)}],
            }
        )
    huge = tmp_path / "scene.json"
    huge.write_bytes(b"{" + b"x" * (ab.MAX_SCENE_BYTES + 8))
    with pytest.raises(ab.AssetBibleError, match="bytes"):
        ab.load_scene(huge)
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    with pytest.raises(ab.AssetBibleError, match="invalid scene JSON"):
        ab.load_scene(bad)
    missing = tmp_path / "missing.yaml"
    with pytest.raises(ab.AssetBibleError, match="not a file"):
        ab.validate_file(missing)
    txt = tmp_path / "note.txt"
    txt.write_text("x", encoding="utf-8")
    with pytest.raises(ab.AssetBibleError, match="unsupported"):
        ab.validate_file(txt)


def test_index_human_and_slug_mismatch(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert ab.iter_asset_yaml(tmp_path / "missing") == []
    catalog = tmp_path / "assets"
    catalog.mkdir()
    (catalog / ".hidden").mkdir()
    (catalog / ".hidden" / "ghost").mkdir()
    (catalog / ".hidden" / "ghost" / "asset.yaml").write_text("x", encoding="utf-8")
    empty_index = ab.write_index(catalog)
    assert "assets: []" in empty_index.read_text(encoding="utf-8")
    dest = ab.ensure_layout(catalog, "object", "mug-cobalt-chipped")
    dest.joinpath("asset.yaml").write_text(
        FIXTURE_YAML.read_text(encoding="utf-8"), encoding="utf-8"
    )
    ab.ensure_layout(catalog, "object", "mug-cobalt-chipped")
    assert ab._cli(["ls", "--output-dir", str(catalog)]) == 0  # noqa: SLF001
    human = capsys.readouterr().out
    assert "mug-cobalt-chipped" in human
    assert "ready" in human
    empty = tmp_path / "empty"
    empty.mkdir()
    assert ab._cli(["ls", "--output-dir", str(empty)]) == 0  # noqa: SLF001
    blank = capsys.readouterr().out
    assert "0 assets" in blank
    assert ab._format_scalar(None) == "null"
    assert ab._format_scalar(False) == "false"
    assert ab._format_scalar(3) == "3"
    assert ab._format_scalar('say "hi"') == '"say \\"hi\\""'
    ab._print_human(
        [
            {
                "id": "draft-mug",
                "kind": "object",
                "pipeline": "klein-trellis2",
                "ready": False,
                "tags": ["prop"],
            }
        ],
        Path("."),
    )
    other = ab.ensure_layout(catalog, "object", "other-mug")
    other.joinpath("asset.yaml").write_text(
        FIXTURE_YAML.read_text(encoding="utf-8"), encoding="utf-8"
    )
    with pytest.raises(ab.AssetBibleError, match="directory slug"):
        ab.list_assets(catalog)
    as_dir = tmp_path / "dir.yaml"
    as_dir.mkdir()
    assert ab._cli(["validate", str(as_dir)]) == 1  # noqa: SLF001
    capsys.readouterr()
    bad = tmp_path / "bad.yaml"
    bad.write_text("schema: nope\n", encoding="utf-8")
    assert ab._cli(["validate", str(bad)]) == 1  # noqa: SLF001
    capsys.readouterr()
    blocked = tmp_path / "blocked.yaml"
    blocked.write_text("schema: ez.asset.v1\n", encoding="utf-8")
    orig_read = Path.read_text

    def boom(
        self: Path, encoding: str | None = "utf-8", errors: str | None = None
    ) -> str:
        if self.name == "blocked.yaml":
            raise OSError("eacces")
        return orig_read(self, encoding=encoding, errors=errors)

    monkeypatch.setattr(Path, "read_text", boom)
    assert ab._cli(["validate", str(blocked)]) == 1  # noqa: SLF001

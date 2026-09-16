"""Hermetic tests for ez_studio_forge (no Comfy, no network, no GGUF)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_studio_forge  # noqa: E402
import ez_studio_forge.nodes as forge_nodes  # noqa: E402
import ez_studio_forge.pipeline as forge  # noqa: E402
from ez_studio_forge.nodes import EZAppForge, NODE_CLASS_MAPPINGS  # noqa: E402
from ez_studio_forge.pipeline import (  # noqa: E402
    ForgeError,
    apply_slots,
    clone_template,
    generate_app,
    pick_template,
    restamp_identity,
    save_workflow,
    slugify,
    validate_slug,
    validate_workflow,
)


def _prompt_of(graph: dict) -> str:
    node = next(n for n in graph["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    return str(node["widgets_values"][1])


def _prefix_of(graph: dict) -> str:
    node = next(n for n in graph["nodes"] if n.get("type") == "SaveImage")
    return str(node["widgets_values"][0])


def test_pack_exports_node() -> None:
    assert "EZAppForge" in NODE_CLASS_MAPPINGS
    assert NODE_CLASS_MAPPINGS["EZAppForge"] is EZAppForge
    assert ez_studio_forge.WEB_DIRECTORY == "./js"


def test_pick_template_heuristic() -> None:
    assert pick_template("1:1 IG still of a mug", "auto") == "klein/instagram-square"
    assert pick_template("pinterest pin of a mug", "auto") == "klein/creator/pinterest-pin"
    assert pick_template("spotify canvas loop", "auto") == "wan/creator/spotify-canvas"
    assert pick_template("silent 5s from a still", "auto") == "wan/still-to-video-5s"
    assert pick_template("hello world", "auto") == "klein/still-draft"
    assert pick_template("text swap a neon sign", "auto") == "klein/text-swap"
    assert pick_template("relabel the mug lettering", "auto") == "klein/text-swap"
    assert pick_template("anything", "klein/still-hero") == "klein/still-hero"
    with pytest.raises(ForgeError, match="unknown"):
        pick_template("x", "no-such-graph")


def test_clone_apply_slots_and_prefix() -> None:
    origin, graph = clone_template("klein/still-draft")
    assert origin == "klein/still-draft"
    apply_slots(
        graph,
        {"prompt": "a chipped cobalt mug on stone", "filename_prefix": "ez_mug"},
    )
    assert _prompt_of(graph) == "a chipped cobalt mug on stone"
    assert _prefix_of(graph) == "ez_mug"
    with pytest.raises(ForgeError, match="unknown slot"):
        apply_slots(graph, {"not_a_widget": "x"})


def test_validate_bans_minimax_and_colon_ids() -> None:
    _origin, graph = clone_template("klein/still-draft")
    apply_slots(graph, {"prompt": "MiniMax H3 rooftop"})
    errors = validate_workflow(graph)
    assert any("banned" in err for err in errors)
    extra = graph.setdefault("extra", {})
    extra["linearData"] = {"inputs": [["11:prompt", "prompt"]]}
    extra["workflowRendererVersion"] = "Vue-corrected"
    errors = validate_workflow(graph)
    assert any("colon" in err for err in errors)


def test_generate_app_writes_user_app_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    result = generate_app(
        "a chipped cobalt mug on pale stone",
        template="klein/still-draft",
        slug="mug-still",
        as_app=True,
        use_llm=False,
    )
    assert result.ok, result.error
    dest = Path(result.path)
    assert dest.is_file()
    assert dest.name == "mug-still.app.json"
    assert "_user" in dest.parts
    assert "_lab" not in dest.parts[-3:]
    data = json.loads(dest.read_text(encoding="utf-8"))
    assert data["id"] == "mug-still"
    extra = data["extra"]
    assert extra["lab_origin"] == "klein/still-draft"
    assert extra["lab_rel"] == "_user/mug-still"
    assert extra["lab_generated"] is True
    assert extra["workflowRendererVersion"] == "Vue-corrected"
    assert extra["lab_app_mode"]["occupancy"] == "klein"
    assert extra["lab_app_mode"]["default_view"] == "app"
    assert "a chipped cobalt mug" in _prompt_of(data)
    again = generate_app(
        "again",
        template="klein/still-draft",
        slug="mug-still",
        as_app=True,
        use_llm=False,
    )
    assert again.ok is False
    assert "already exists" in again.error


def test_overwrite_and_graph_suffix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    first = generate_app(
        "gif loop of palms",
        template="wan/gif-loop",
        slug="palm-loop",
        as_app=False,
        use_llm=False,
    )
    assert first.ok, first.error
    assert Path(first.path).name == "palm-loop.json"
    second = generate_app(
        "gif loop of palms at night",
        template="wan/gif-loop",
        slug="palm-loop",
        as_app=False,
        overwrite=True,
        use_llm=False,
    )
    assert second.ok, second.error
    assert Path(second.path).is_file()


def test_refuse_lab_dest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    _origin, graph = clone_template("klein/still-draft")
    restamp_identity(graph, origin="klein/still-draft", slug="x")
    lab_dest = ROOT / "workflows" / "_lab" / "inspire" / "should-not-write.json"
    errors = validate_workflow(graph, dest=lab_dest, slug="x")
    assert any("_lab" in err for err in errors)


def test_slug_rules() -> None:
    assert slugify("Mug IG Still!!") == "mug-ig-still"
    assert validate_slug("mug-ig") == "mug-ig"
    with pytest.raises(ForgeError):
        validate_slug("../etc")
    with pytest.raises(ForgeError):
        validate_slug("Klein/Still")


def test_node_run_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    packed = EZAppForge().run(
        prompt="1:1 IG still of a mug",
        template="klein/instagram-square",
        slug="node-mug",
        as_app=True,
        overwrite=False,
        sample="custom",
        catalog="",
    )
    path = packed["result"][0]
    assert Path(path).is_file()
    assert packed["ui"]["template"][0] == "klein/instagram-square"


def test_save_workflow_helper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    origin, graph = clone_template("klein/still-draft")
    restamp_identity(graph, origin=origin, slug="helper-mug")
    dest = save_workflow(graph, slug="helper-mug", as_app=True)
    assert dest.name == "helper-mug.app.json"


def test_helpers_stems_slugs_and_prompts() -> None:
    assert "JSON only" in forge.load_prompt("planner")
    forge._log("coverage")
    assert forge._as_bool(True) is True
    assert forge._as_bool(1) is True
    assert forge._as_bool("yes") is True
    assert forge._as_bool("no") is False
    assert forge._as_bool(None) is False
    assert forge.normalize_stem("_lab/klein/still-draft.app.json") == "klein/still-draft"
    assert forge.normalize_stem("./klein/still-draft.json") == "klein/still-draft"
    assert forge.slugify("!!!") == "app"
    with pytest.raises(ForgeError, match="missing slug"):
        validate_slug("")
    with pytest.raises(ForgeError, match="illegal"):
        validate_slug("Nope_underscore")
    assert forge.load_lab_graph("") is None
    assert forge.load_lab_graph("still-draft") is not None
    assert forge._brief_has("", "") is False
    assert forge._brief_has("instagram-square still", "instagram-square") is True
    assert pick_template("x", "custom") == "klein/still-draft"


def test_linear_occupancy_and_view_edges() -> None:
    assert forge._linear_labels({"linearData": "nope"}) == []
    assert forge._linear_labels(
        {"linearData": {"inputs": ["x", ["only"], ["1", "prompt", "not-dict"]]}}
    ) == ["prompt"]
    assert forge._occupancy_of({"extra": [1]}) == ""
    assert forge._occupancy_of({"extra": {"lab_app_mode": [1]}}) == ""
    assert forge._default_view({"extra": [1]}) == "graph"
    assert forge._default_view({"extra": {"lab_app_mode": [1]}}) == "graph"
    assert forge._default_view(
        {"extra": {"lab_app_mode": {"default_view": "weird"}}}
    ) == "graph"
    assert forge._widget_index({"type": "Unknown"}, "prompt") is None
    assert forge._nodes_by_id({"nodes": ["x", {"id": "nope"}]}) == {}


def test_list_templates_filters_and_bad_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lab = tmp_path / "_lab" / "inspire"
    lab.mkdir(parents=True)
    (lab / "bad.json").write_text("{", encoding="utf-8")
    (lab / "array.json").write_text("[1]", encoding="utf-8")
    (lab / "extra-list.json").write_text(
        json.dumps({"id": "x", "extra": [1]}), encoding="utf-8"
    )
    (lab / "mode-list.json").write_text(
        json.dumps(
            {
                "id": "y",
                "extra": {
                    "lab_app_mode": [1],
                    "lab_mcp": [1],
                    "lab_rel": "inspire/y",
                },
            }
        ),
        encoding="utf-8",
    )
    (lab / "ok.json").write_text(
        json.dumps(
            {
                "id": "ok",
                "extra": {
                    "lab_rel": "inspire/ok",
                    "lab_description": "desk",
                    "lab_app_mode": {"lane": "inspire", "occupancy": "llm"},
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(forge, "_lab_root", lambda: tmp_path / "_lab")
    monkeypatch.setattr(forge, "_blocks_root", lambda: tmp_path / "missing-blocks")
    rows = forge.list_templates(query="desk", occupancy="llm", lane="inspire")
    assert {r["id"] for r in rows} == {"inspire/ok"}
    assert forge.list_templates(query="desk", occupancy="klein") == []
    assert forge.list_templates(query="desk", lane="klein") == []
    assert forge.list_templates(query="zzz") == []
    odd = forge.describe_template("inspire/extra-list")
    assert odd["ok"] is True
    mode = forge.describe_template("inspire/mode-list")
    assert mode["ok"] is True
    labels = forge.template_combo_labels()
    assert labels[0] == "auto"
    assert "inspire/ok" in labels


def test_describe_template_block_and_odd_extra() -> None:
    block = forge.describe_template("klein-t2i-backbone")
    assert block["ok"] is True
    assert block["kind"] == "block"
    origin, graph = clone_template("klein/still-draft")
    graph["extra"] = [1]
    described = forge.describe_template("klein/still-draft")
    assert described["ok"] is True
    restamp_identity(graph, origin=origin, slug="list-extra")
    assert "_user/list-extra" in json.dumps(graph)
    with pytest.raises(ForgeError, match="blueprint"):
        clone_template("klein-t2i-backbone")
    with pytest.raises(ForgeError, match="unknown"):
        clone_template("no-such")


def test_apply_slots_coercion_and_edges() -> None:
    _origin, graph = clone_template("klein/still-draft")
    apply_slots(graph, None)
    apply_slots(graph, {"Prompt": "via label", "seed": "99", "enhance": "off"})
    assert _prompt_of(graph) == "via label"
    sampler = next(n for n in graph["nodes"] if n.get("type") == "KSampler")
    assert sampler["widgets_values"][0] == 99
    enh = next(n for n in graph["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    assert enh["widgets_values"][2] is False
    apply_slots(graph, {"cfg": "1.5"})
    assert sampler["widgets_values"][3] == 1.5
    apply_slots(graph, {"cfg": "nope"})
    graph["nodes"].append({"id": "bad", "type": "SaveImage", "widgets_values": {}})
    apply_slots(graph, {"filename_prefix": "ez_x"})
    graph["extra"] = {"linearData": {"inputs": "nope"}}
    apply_slots(graph, {"filename_prefix": "ez_y"})
    with pytest.raises(ForgeError, match="empty slot"):
        apply_slots(graph, {"  ": "x"})
    graph["extra"] = {
        "linearData": {
            "inputs": [
                ["nope", "prompt"],
                [99999, "prompt"],
                [11, "mystery"],
            ]
        }
    }
    with pytest.raises(ForgeError, match="unknown slot"):
        apply_slots(graph, {"mystery": "x"})
    node = {"widgets_values": "x"}
    forge._set_widget_value(node, 0, "hi")
    assert node["widgets_values"][0] == "hi"
    forge._set_widget_value({"widgets_values": {0: 1}}, 0, 2)


def test_validate_and_save_edges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    errors = validate_workflow({"extra": [1]})
    assert any("Vue-corrected" in err for err in errors)
    errors = validate_workflow(
        {
            "extra": {
                "workflowRendererVersion": "Vue-corrected",
                "linearData": {"inputs": [[], ["abc", "prompt"]]},
            }
        },
        slug="bad slug",
    )
    assert errors
    outside = tmp_path / "workflows" / "other.json"
    outside.parent.mkdir(parents=True)
    errors = validate_workflow(
        {"extra": {"workflowRendererVersion": "Vue-corrected"}},
        dest=outside,
    )
    assert any("outside" in err or "_lab" in err for err in errors)
    origin, graph = clone_template("klein/still-draft")
    restamp_identity(graph, origin=origin, slug="sib")
    first = save_workflow(graph, slug="sib", as_app=True)
    assert first.is_file()
    with pytest.raises(ForgeError, match="already exists"):
        save_workflow(graph, slug="sib", as_app=False)
    restamp_identity(graph, origin=origin, slug="sib")
    second = save_workflow(graph, slug="sib", as_app=False, overwrite=True)
    assert second.name == "sib.json"
    assert not first.exists()


def test_parse_plan_and_llm_generate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    assert forge.parse_plan("") is None
    assert forge.parse_plan("{not-json") is None
    assert forge.parse_plan("[1]") is None
    assert forge.parse_plan('{"template": }') is None
    plan = forge.parse_plan('prefix {"template":"klein/instagram-square","slug":"p","reason":"r"}')
    assert plan is not None
    monkeypatch.setattr(
        forge,
        "_complete",
        lambda _s, _u: (
            json.dumps(
                {
                    "template": "klein/instagram-square",
                    "slug": "plan-mug",
                    "as_app": True,
                    "slots": {"prompt": "planned mug"},
                    "reason": "square",
                }
            ),
            "ok",
        ),
    )
    result = generate_app("make a still", template="auto", use_llm=True)
    assert result.ok, result.error
    assert result.template == "klein/instagram-square"
    assert result.slug == "plan-mug"
    monkeypatch.setattr(forge, "_complete", lambda _s, _u: ("", "llama.cpp unavailable"))
    fallback = generate_app(
        "thumbnail of a wizard",
        template="auto",
        slug="thumb-x",
        use_llm=True,
    )
    assert fallback.ok, fallback.error
    assert fallback.template == "klein/thumbnail"
    none_app = generate_app(
        "a still of a mug",
        template="klein/still-draft",
        slug="none-app",
        as_app=None,
        use_llm=False,
    )
    assert none_app.ok
    assert none_app.as_app is True


def test_complete_fail_soft_and_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "ez_prompt_enhance.client.complete",
        lambda *_a, **_k: ("  hi  ", "ok"),
    )
    text, reason = forge._complete("sys", "user")
    assert text == "hi"
    assert reason == "ok"
    saved = sys.path[:]
    try:
        custom = str(ROOT / "custom_nodes")
        while custom in sys.path:
            sys.path.remove(custom)
        monkeypatch.setattr(
            "ez_prompt_enhance.client.complete",
            lambda *_a, **_k: ("x", ""),
        )
        text, reason = forge._complete("sys", "user")
        assert custom in sys.path
        assert text == "x"
    finally:
        sys.path[:] = saved
    monkeypatch.setattr(
        "ez_prompt_enhance.client.complete",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    text, reason = forge._complete("sys", "user")
    assert text == ""
    assert "unavailable" in reason


def test_node_input_types_and_bools(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    types = EZAppForge.INPUT_TYPES()
    assert "template" in types["required"]
    assert types["required"]["template"][1]["default"] == "auto"
    monkeypatch.setattr(forge_nodes, "template_combo_labels", lambda: ["klein/still-draft"])
    types2 = EZAppForge.INPUT_TYPES()
    assert types2["required"]["template"][0][0] == "auto"
    assert forge_nodes._as_bool(True) is True
    assert forge_nodes._as_bool(0) is False
    assert forge_nodes._as_bool("ON") is True
    assert forge_nodes._as_bool("no") is False
    assert forge_nodes._as_bool(None) is False
    packed = forge_nodes._pack(forge.ForgeResult(ok=False, error="nope"))
    assert packed["result"][0] == "nope"
    packed_ok = forge_nodes._pack(forge.ForgeResult(ok=True, path="p", widgets=[]))
    assert packed_ok["ui"]["widgets"][0] == "(none)"
    failed = EZAppForge().run(
        prompt="x",
        template="no-such",
        slug="x",
        as_app="yes",
        overwrite="no",
        sample="custom",
        catalog="",
    )
    assert "unknown" in failed["result"][0]


def test_nodes_path_insert_on_reload() -> None:
    import importlib

    saved = sys.path[:]
    try:
        while forge_nodes._root in sys.path:
            sys.path.remove(forge_nodes._root)
        importlib.reload(forge_nodes)
        assert forge_nodes._root in sys.path
    finally:
        sys.path[:] = saved


def test_generate_app_with_slots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    result = generate_app(
        "ignored brief",
        template="klein/still-draft",
        slug="slot-mug",
        slots={"prompt": "slot prompt", "filename_prefix": "ez_slot"},
        use_llm=False,
    )
    assert result.ok, result.error
    data = json.loads(Path(result.path).read_text(encoding="utf-8"))
    assert _prompt_of(data) == "slot prompt"
    assert _prefix_of(data) == "ez_slot"


def test_load_lab_graph_bad_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lab = tmp_path / "klein"
    lab.mkdir()
    (lab / "broken.json").write_text("{", encoding="utf-8")
    (lab / "list.json").write_text("[1]", encoding="utf-8")
    monkeypatch.setattr(forge, "_lab_root", lambda: tmp_path)
    assert forge.load_lab_graph("klein/broken") is None
    assert forge.load_lab_graph("klein/list") is None
    assert forge.load_lab_graph("klein/missing") is None


def test_remaining_branches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    llm_only = forge.list_templates(occupancy="llm")
    assert llm_only
    assert all(row["kind"] == "lab" for row in llm_only)
    _origin, graph = clone_template("klein/still-draft")
    apply_slots(graph, {"seed": []})
    graph["extra"] = [1]
    apply_slots(graph, {"filename_prefix": "ez_list_extra"})
    graph["nodes"] = []
    graph["extra"] = {"linearData": {"inputs": ["skip", [99999, "prompt"]]}}
    with pytest.raises(ForgeError):
        apply_slots(graph, {"prompt": "missing-node"})
    banned = clone_template("klein/still-draft")[1]
    apply_slots(banned, {"prompt": "MiniMax H3"})
    restamp_identity(banned, origin="klein/still-draft", slug="ban")
    with pytest.raises(ForgeError, match="banned"):
        save_workflow(banned, slug="ban")
    monkeypatch.setattr(
        forge,
        "_complete",
        lambda _s, _u: (
            json.dumps({"template": "klein/still-draft", "slug": "empty-reason"}),
            "",
        ),
    )
    planned = generate_app("still", template="auto", use_llm=True)
    assert planned.ok, planned.error
    monkeypatch.setattr(forge, "_complete", lambda _s, _u: ("{nope}", ""))
    passthrough = generate_app(
        "still of a mug",
        template="auto",
        slug="pass-x",
        use_llm=True,
    )
    assert passthrough.ok
    assert passthrough.status == "llm passthrough"
    monkeypatch.setattr(
        forge,
        "describe_template",
        lambda _s: {"ok": True, "kind": "lab", "id": "ghost"},
    )
    monkeypatch.setattr(forge, "load_lab_graph", lambda _s: None)
    with pytest.raises(ForgeError, match="unknown"):
        clone_template("ghost")
    monkeypatch.setattr(forge, "describe_template", lambda _s: {"ok": False})
    with pytest.raises(ForgeError, match="unknown"):
        clone_template("ghost")

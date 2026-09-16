"""Completeness auditor for shipped lab graphs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from _lab_paths import lab_example_paths, lab_json, load_lab_graph
from _stamp_app_mode import BANNED, NODE_MODE_BYPASS, linear_input_node_id

ROOT = Path(__file__).resolve().parents[2]
NOTE_TYPES = {"Note", "MarkdownNote"}
LTX_LATENT_TYPES = {
    "LTXVImgToVideo",
    "EmptyLTXVLatentVideo",
    "LTXVEmptyLatentAudio",
}


def _graphs() -> list[Path]:
    return lab_example_paths()


def _load(path: Path) -> dict:
    return load_lab_graph(path)


def _link_endpoints(graph: dict) -> tuple[set[int], set[int]]:
    """Return (link ids, node ids referenced by links)."""
    link_ids: set[int] = set()
    node_ids: set[int] = set()
    for link in graph.get("links") or []:
        if isinstance(link, dict):
            lid = int(link.get("id") or link.get("link") or 0)
            origin = int(link.get("origin_id") or link.get("from") or 0)
            target = int(link.get("target_id") or link.get("to") or 0)
        else:
            lid = int(link[0])
            origin = int(link[1])
            target = int(link[3])
        link_ids.add(lid)
        node_ids.add(origin)
        node_ids.add(target)
    return link_ids, node_ids


def _wired_node_ids(graph: dict) -> set[int]:
    wired: set[int] = set()
    link_ids, endpoints = _link_endpoints(graph)
    wired.update(endpoints)
    for node in graph.get("nodes") or []:
        nid = int(node["id"])
        for inp in node.get("inputs") or []:
            if not isinstance(inp, dict):
                continue
            link = inp.get("link")
            if link is not None:
                wired.add(nid)
                assert int(link) in link_ids, (node.get("type"), link)
        for out in node.get("outputs") or []:
            if not isinstance(out, dict):
                continue
            links = out.get("links")
            if links:
                wired.add(nid)
    return wired


@pytest.mark.parametrize("path", _graphs(), ids=lambda p: p.name)
def test_lab_graph_completeness(path: Path) -> None:
    graph = _load(path)
    extra = graph.get("extra") or {}
    if extra.get("lab_stub") is True:
        assert graph.get("id") == path.stem
        return

    assert graph.get("id") == path.stem
    assert graph.get("version") is not None
    assert graph.get("revision") is not None

    live = {int(n["id"]) for n in graph.get("nodes") or []}
    by_id = {int(n["id"]): n for n in graph.get("nodes") or []}
    _, endpoints = _link_endpoints(graph)
    missing = endpoints - live
    assert not missing, f"{path.name} dangling link nodes {missing}"

    for link in graph.get("links") or []:
        if isinstance(link, dict):
            lid = int(link.get("id") or link.get("link") or 0)
            dest = int(link.get("target_id") or link.get("to") or 0)
            slot = int(link.get("target_slot") or link.get("to_slot") or 0)
        else:
            lid = int(link[0])
            dest = int(link[3])
            slot = int(link[4])
        node = by_id.get(dest)
        assert node is not None, (path.name, lid, dest)
        inputs = node.get("inputs") or []
        assert slot < len(inputs), (path.name, node.get("type"), slot, lid)
        recorded = inputs[slot].get("link")
        assert recorded is not None and int(recorded) == lid, (
            path.name,
            node.get("type"),
            node.get("title"),
            inputs[slot].get("name"),
            recorded,
            lid,
        )

    blob = json.dumps(graph)
    for needle in BANNED:
        assert needle not in blob, (path.name, needle)

    assert any(n.get("type") in NOTE_TYPES for n in graph["nodes"]), path.name

    mode = extra.get("lab_app_mode") or {}
    occupancy = mode.get("occupancy") or extra.get("lab_occupancy")
    if mode.get("enabled") is True:
        linear = extra.get("linearData") or {}
        for entry in linear.get("inputs") or []:
            nid = linear_input_node_id(entry)
            assert nid in live, (path.name, entry[0])
        for nid in linear.get("outputs") or []:
            assert int(nid) in live, (path.name, nid)

    types = {n.get("type") for n in graph["nodes"]}
    nested: list[dict] = []
    for sub in ((graph.get("definitions") or {}).get("subgraphs") or []):
        nested.extend(sub.get("nodes") or [])
    all_nodes = list(graph["nodes"]) + nested
    all_types = {n.get("type") for n in all_nodes}

    if occupancy not in ("none", "llm") and extra.get("lab_stub") is not True:
        if occupancy == "film" or path.name.startswith("film-"):
            assert "EZFilmConcat" in types, path.name
            assert "VHS_VideoCombine" in all_types, path.name
        elif occupancy == "audio" or "SaveAudio" in types or "SaveAudioMP3" in types:
            assert "SaveAudio" in types or "SaveAudioMP3" in types, path.name
        elif occupancy in ("wan", "ltx") or "VHS_VideoCombine" in types:
            vhs = [n for n in graph["nodes"] if n.get("type") == "VHS_VideoCombine"]
            save_vid = [n for n in graph["nodes"] if n.get("type") == "SaveVideo"]
            assert vhs or save_vid, path.name
            for node in vhs:
                widgets = node.get("widgets_values") or {}
                if isinstance(widgets, dict) and "save_output" in widgets:
                    assert widgets["save_output"] is True, path.name
        elif occupancy == "trellis" or "MeshToFile3D" in types:
            assert "MeshToFile3D" in types, path.name
        elif occupancy == "klein" or "SaveImage" in types:
            assert "SaveImage" in types, path.name

    allowed = set(extra.get("lab_optional_unwired") or [])
    if occupancy in ("llm", "none"):
        allowed.update(
            {
                "EZKleinPromptEnhance",
                "EZWanPromptEnhance",
                "EZLTXPromptEnhance",
                "EZZimagePromptEnhance",
                "EZLongCatPromptEnhance",
                "EZDreamXPromptEnhance",
                "EZCreativeResearch",
                "PrimitiveNode",
                "EZAlbumPack",
            }
        )
    wired = _wired_node_ids(graph)
    isolates = [
        n
        for n in graph["nodes"]
        if n.get("type") not in NOTE_TYPES and int(n["id"]) not in wired
    ]
    unexpected = [n for n in isolates if n.get("type") not in allowed]
    assert not unexpected, (
        path.name,
        [(n["id"], n.get("type"), n.get("title")) for n in unexpected],
    )
    active_cover = [
        n
        for n in isolates
        if n.get("type") == "LoadImage"
        and str(n.get("title") or "") == "Cover image"
        and int(n.get("mode") or 0) != NODE_MODE_BYPASS
    ]
    assert not active_cover, (
        path.name,
        [(n["id"], n.get("title"), n.get("mode")) for n in active_cover],
    )

    for node in graph["nodes"]:
        if node.get("type") not in LTX_LATENT_TYPES:
            continue
        values = node.get("widgets_values") or []
        if node.get("type") == "LTXVEmptyLatentAudio":
            continue
        if len(values) < 2:
            continue
        width, height = int(values[0]), int(values[1])
        assert width % 32 == 0 and height % 32 == 0, (path.name, width, height)
        assert height != 720 and width != 1080 and height != 1080, (
            path.name,
            width,
            height,
        )

    if path.name.startswith("film-"):
        for node in all_nodes:
            if node.get("type") in ("LTXVImgToVideo", "LTXVEmptyLatentAudio"):
                values = node.get("widgets_values") or []
                length = int(
                    values[0] if node["type"] == "LTXVEmptyLatentAudio" else values[2]
                )
                assert length == 121, (path.name, node["type"], length)
            if node.get("title") == "Save last frame":
                prefix = str((node.get("widgets_values") or [""])[0])
                assert prefix.endswith("_last"), (path.name, prefix)

    for node in graph.get("nodes") or []:
        if node.get("type") != "KSampler":
            continue
        if int(node.get("mode") or 0) != 0:
            continue
        for name in ("positive", "negative"):
            inp = next(
                (i for i in node.get("inputs") or [] if i.get("name") == name),
                None,
            )
            assert inp is not None and inp.get("link") is not None, (
                path.name,
                node.get("title"),
                name,
            )


def _source_of(graph: dict, node: dict, name: str) -> dict | None:
    inp = next((i for i in node.get("inputs") or [] if i.get("name") == name), None)
    if inp is None or inp.get("link") is None:
        return None
    lid = int(inp["link"])
    by_id = {int(n["id"]): n for n in graph["nodes"]}
    for link in graph.get("links") or []:
        if int(link[0]) == lid:
            return by_id.get(int(link[1]))
    return None


def test_prompt_forge_shares_one_prompt_and_context() -> None:
    graph = _load(lab_json("inspire/prompt-forge.json"))
    extra = graph.get("extra") or {}
    assert extra.get("lab_rel") == "inspire/prompt-forge"
    prims = {
        str(n.get("title")): n
        for n in graph["nodes"]
        if n.get("type") in {"PrimitiveNode", "EZSamplePrompt"}
    }
    assert set(prims) >= {"Prompt", "Context"}
    families = [
        n
        for n in graph["nodes"]
        if n.get("type")
        in {"EZKleinPromptEnhance", "EZWanPromptEnhance", "EZLTXPromptEnhance"}
    ]
    assert len(families) == 3
    for node in families:
        prompt_src = _source_of(graph, node, "prompt")
        ctx_src = _source_of(graph, node, "context")
        assert prompt_src is prims["Prompt"], node.get("title")
        assert ctx_src is prims["Context"], node.get("title")


def test_beat_sheet_desk_reaches_every_ltx_enhance() -> None:
    graph = _load(lab_json("inspire/beat-sheet.json"))
    prims = {
        str(n.get("title")): n
        for n in graph["nodes"]
        if n.get("type") in {"PrimitiveNode", "EZSamplePrompt"}
    }
    for title in ("Logline", "Script", "Audio policy", "Score"):
        assert title in prims
        outs = prims[title].get("outputs") or []
        assert any(o.get("links") for o in outs), title
    join = next(n for n in graph["nodes"] if n.get("type") == "EZContextJoin")
    assert _source_of(graph, join, "a") is prims["Logline"]
    assert _source_of(graph, join, "b") is prims["Script"]
    assert _source_of(graph, join, "c") is prims["Audio policy"]
    assert _source_of(graph, join, "d") is prims["Score"]
    ltx = [n for n in graph["nodes"] if n.get("type") == "EZLTXPromptEnhance"]
    assert len(ltx) == 18
    for node in ltx:
        assert _source_of(graph, node, "context") is join
        audio_src = _source_of(graph, node, "audio_notes")
        assert audio_src is prims["Audio policy"]


def test_film_identity_is_context_for_every_ltx_shot() -> None:
    for rel in ("shorts/go-see.json", "shorts/still-here.json", "shorts/switchyard.json"):
        graph = _load(lab_json(rel))
        klein = next(n for n in graph["nodes"] if n.get("type") == "EZKleinPromptEnhance")
        ltx = [n for n in graph["nodes"] if n.get("type") == "EZLTXPromptEnhance"]
        assert len(ltx) == 18, rel
        for node in ltx:
            assert _source_of(graph, node, "context") is klein, (rel, node.get("title"))


def test_rap_draft_and_full_wire_lyrics_writer() -> None:
    for rel in ("audio/music/rap-draft.json", "audio/music/rap-full.json"):
        graph = _load(lab_json(rel))
        rap = next(n for n in graph["nodes"] if n.get("type") == "EZRapLyrics")
        ace = next(n for n in graph["nodes"] if n.get("type") == "EZAceStepPromptEnhance")
        assert _source_of(graph, ace, "lyrics") is rap, rel


def test_podcast_ace_bed_reads_script_context() -> None:
    for rel in (
        "audio/podcast/audio-first.json",
        "audio/podcast/radio-drama.json",
    ):
        graph = _load(lab_json(rel))
        script = next(n for n in graph["nodes"] if n.get("type") == "EZPodcastScript")
        aces = [n for n in graph["nodes"] if n.get("type") == "EZAceStepPromptEnhance"]
        assert aces, rel
        for ace in aces:
            assert _source_of(graph, ace, "context") is script, (rel, ace.get("title"))

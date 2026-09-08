"""Completeness auditor for shipped *-lab-example graphs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from _lab_paths import lab_example_paths
from _stamp_app_mode import BANNED, linear_input_node_id

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
    return json.loads(path.read_text(encoding="utf-8"))


def _link_endpoints(graph: dict) -> tuple[set[int], set[int]]:
    """Return (link ids, node ids referenced by links)."""
    link_ids: set[int] = set()
    node_ids: set[int] = set()
    for link in graph.get("links") or []:
        if isinstance(link, dict):
            lid = int(link.get("id") or link.get("link") or 0)
            origin = int(link.get("origin_id") or link.get("from"))
            target = int(link.get("target_id") or link.get("to"))
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

    assert json.loads(path.read_text(encoding="utf-8"))
    assert graph.get("id") == path.stem
    assert graph.get("version") is not None
    assert graph.get("revision") is not None

    live = {int(n["id"]) for n in graph.get("nodes") or []}
    _, endpoints = _link_endpoints(graph)
    missing = endpoints - live
    assert not missing, f"{path.name} dangling link nodes {missing}"

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
        elif occupancy == "klein" or "SaveImage" in types:
            assert "SaveImage" in types, path.name

    allowed = set(extra.get("lab_optional_unwired") or [])
    if occupancy in ("llm", "none"):
        allowed.update(
            {
                "EZKleinPromptEnhance",
                "EZWanPromptEnhance",
                "EZLTXPromptEnhance",
                "PrimitiveNode",
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
                assert length == 120, (path.name, node["type"], length)
            if node.get("title") == "Save last frame":
                prefix = str((node.get("widgets_values") or [""])[0])
                assert prefix.endswith("_last"), (path.name, prefix)

"""Hermetic tests for :mod:`ez_edit.generate_clip` (no socket, no sleep).

The transport, the sleeper, the clock, the occupancy reader, and the graph
file are all injected; one test drives the real ``urlopen`` indirection by
monkeypatching ``urllib.request.urlopen``.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Literal, override

import pytest
from ez_common import Json, JsonObject, JsonMap
from ez_edit import generate_clip, render_server
from ez_edit.generate_clip import (
    GenerateClipError,
    GraphUnavailable,
    comfy_base,
    graph_path,
    load_graph,
    new_generate_row,
    patch_graph,
    poll_history,
    queue_prompt,
)

PROMPT = "a brass desk lamp turning slowly on a concrete plinth"


class _Response:
    """``urlopen`` response stand-in (context manager plus ``read``)."""

    def __init__(self, body: str) -> None:
        """Store the body.

        Args:
            body: Text body ``read`` returns.
        """
        self._body = body

    def __enter__(self) -> "_Response":
        """Enter the context.

        Returns:
            Self.
        """
        return self

    def __exit__(self, *args: object) -> Literal[False]:
        """Leave the context.

        Args:
            *args: Exception detail (ignored).

        Returns:
            False (never swallow).
        """
        return False

    def read(self) -> bytes:
        """Return the body.

        Returns:
            Encoded body bytes.
        """
        return self._body.encode("utf-8")


class FakeTransport:
    """Queue of JSON replies standing in for the ComfyUI queue."""

    def __init__(self, replies: list[Any]) -> None:
        """Seed the reply queue.

        Args:
            replies: Parsed JSON values, or exceptions to raise.
        """
        self.replies = list(replies)
        self.calls: list[tuple[str, Any]] = []

    def __call__(self, request: urllib.request.Request, timeout: float) -> Any:
        """Answer one request from the queue.

        Args:
            request: Prepared request.
            timeout: Socket timeout (recorded by the caller's assertion).

        Returns:
            Response carrying the next reply.
        """
        del timeout
        self.calls.append((request.full_url, request.data))
        reply = self.replies.pop(0) if self.replies else {}
        if isinstance(reply, Exception):
            raise reply
        return _Response(json.dumps(reply))


def _graph() -> JsonObject:
    """Minimal frontend graph with title-less nodes (heuristic branch).

    Returns:
        Graph dict with a prompt node, a latent node, and no mux node.
    """
    return {
        "nodes": [
            {"id": 1, "type": "CLIPTextEncode", "widgets_values": ["old prompt"]},
            {"id": 2, "type": "CLIPTextEncode", "title": "Negative", "widgets_values": ["bad"]},
            {"id": 3, "type": "EmptyLatentVideo", "widgets_values": [832, 480, 121, 1]},
            {"id": 4, "type": "KSampler", "widgets_values": [42, "fixed", 20]},
        ]
    }


def _write_graph(tmp_path: Path, payload: Any) -> Path:
    """Write a graph file for ``graph_file`` overrides.

    Args:
        tmp_path: Test directory.
        payload: JSON-serialisable graph payload.

    Returns:
        Written path.
    """
    target = tmp_path / "graph.json"
    if isinstance(payload, str):
        target.write_text(payload, encoding="utf-8")
    else:
        target.write_text(json.dumps(payload), encoding="utf-8")
    return target


def _node_rows(graph: JsonMap) -> list[JsonObject]:
    """Narrow a graph's node list to the rows the patcher reads.

    Args:
        graph: Graph object under test.

    Returns:
        Node rows in the order the graph lists them.

    Raises:
        AssertionError: The graph carries no node list or a row is not an object.
    """
    nodes = graph["nodes"]
    assert isinstance(nodes, list)
    rows: list[JsonObject] = []
    for row in nodes:
        assert isinstance(row, dict)
        rows.append(row)
    return rows


def _node_at(graph: JsonMap, index: int) -> JsonObject:
    """Pick one node row by position in the graph.

    Args:
        graph: Graph object under test.
        index: Position in the node list.

    Returns:
        The node row at that position.
    """
    return _node_rows(graph)[index]


def _nodes_by_id(graph: JsonMap) -> dict[int, JsonObject]:
    """Index a graph's node rows by node id.

    Args:
        graph: Graph object under test.

    Returns:
        Node id to node row.

    Raises:
        AssertionError: A row carries no integer id.
    """
    indexed: dict[int, JsonObject] = {}
    for row in _node_rows(graph):
        node_id = row["id"]
        assert isinstance(node_id, int)
        indexed[node_id] = row
    return indexed


def _list_widgets(node: JsonMap) -> list[Json]:
    """Narrow a node's positional widget list.

    Args:
        node: Node row.

    Returns:
        Widgets in saved order.

    Raises:
        AssertionError: The node carries a non-list widget container.
    """
    widgets = node["widgets_values"]
    assert isinstance(widgets, list)
    return widgets


def _dict_widgets(node: JsonMap) -> JsonObject:
    """Narrow a node's named widget object.

    Args:
        node: Node row.

    Returns:
        Widgets keyed by widget name.

    Raises:
        AssertionError: The node carries a non-object widget container.
    """
    widgets = node["widgets_values"]
    assert isinstance(widgets, dict)
    return widgets


def _text(value: Json) -> str:
    """Narrow one parsed value to the text the test expects.

    Args:
        value: Value read out of a patched graph.

    Returns:
        The value as text.

    Raises:
        AssertionError: The value is not a string.
    """
    assert isinstance(value, str)
    return value


def test_comfy_base_defaults_and_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    """Origin follows EZ_EDIT_COMFY_URL, then the port, then the default."""
    monkeypatch.delenv("EZ_EDIT_COMFY_URL", raising=False)
    monkeypatch.delenv("COMFY_PORT", raising=False)
    assert comfy_base() == "http://host.docker.internal:8188"
    assert comfy_base({"COMFY_PORT": "8199"}) == "http://host.docker.internal:8199"
    assert comfy_base({"COMFY_PORT": "  "}) == "http://host.docker.internal:8188"
    assert (
        comfy_base({"EZ_EDIT_COMFY_URL": "http://127.0.0.1:8188///"})
        == "http://127.0.0.1:8188"
    )


def test_graph_path_points_at_the_package_graph() -> None:
    """The packaged cutaway graph is the default queue target."""
    target = graph_path()
    assert target.name == "generate-cutaway.json"
    assert target.parent.name == "graphs"
    assert target.is_file()


def test_patch_graph_patches_the_shipped_graph_from_the_lab_edit_map() -> None:
    """``extra.lab_edit.widgets`` decides the widgets, not the node titles.

    The repo invariant is that ``EZWanPromptEnhance`` feeds the positive
    ``CLIPTextEncode``, so the live prompt text is that node's ``prompt``
    widget (``widgets_values[1]`` on node 13); node 5 is a frontend mirror.
    """
    graph = load_graph()
    patched = patch_graph(graph, prompt_text=PROMPT, duration_s=5.0, fps=30.0)
    nodes = _nodes_by_id(patched)
    enhance = _list_widgets(nodes[13])
    assert enhance[1] == PROMPT
    assert enhance[0] == "custom" and enhance[2] is True and enhance[3] == "t2v"
    assert _list_widgets(nodes[5])[0] == _list_widgets(_node_at(graph, 4))[0]
    assert _text(_list_widgets(nodes[14])[0]).startswith("morphing")
    assert _list_widgets(nodes[7])[2] == 150
    assert _dict_widgets(nodes[12])["frame_rate"] == 30.0


def test_patch_graph_writes_every_widget_the_map_names() -> None:
    """A map-present graph is patched through the map only, never the titles.

    Dict widgets take the named key; list widgets the index the node type's
    schema gives the widget name.
    """
    graph: JsonObject = {
        "nodes": [
            {
                "id": 1,
                "type": "EZWanPromptEnhance",
                "widgets_values": ["custom", "authored", True, "t2v", "5 seconds, 24 fps", "none", "x"],
            },
            {"id": 2, "type": "Wan22ImageToVideoLatent", "widgets_values": [832, 480, 121, 1]},
            {"id": 3, "type": "VHS_VideoCombine", "widgets_values": {"frame_rate": 24, "loop_count": 0}},
            {"id": 4, "type": "VHS_VideoCombine", "widgets_values": [24.0, 0, "prefix"]},
            {"id": 5, "type": "CLIPTextEncode", "title": "Prompt (cutaway)", "widgets_values": ["mirror"]},
            {"id": 6, "type": "Wan22ImageToVideoLatent", "title": "Video size & length", "widgets_values": [832, 480, 121, 1]},
        ],
        "extra": {
            "lab_edit": {
                "widgets": {
                    "prompt": {"node": 1, "widget": "prompt"},
                    "length": {"node": 2, "widget": "length"},
                    "fps": {"node": 3, "widget": "frame_rate"},
                    "seed": {"node": 9, "widget": "seed"},
                }
            }
        },
    }
    patched = patch_graph(graph, prompt_text=PROMPT, duration_s=4.0, fps=30.0)
    nodes = _nodes_by_id(patched)
    assert _list_widgets(nodes[1])[1] == PROMPT
    assert _list_widgets(nodes[1])[0] == "custom"
    assert _list_widgets(nodes[1])[2] is True
    assert _list_widgets(nodes[2]) == [832, 480, 120, 1]
    assert _dict_widgets(nodes[3]) == {"frame_rate": 30.0, "loop_count": 0}
    assert _list_widgets(nodes[4]) == [24.0, 0, "prefix"]
    assert _list_widgets(nodes[5]) == ["mirror"]
    assert _list_widgets(nodes[6]) == [832, 480, 121, 1]


def test_patch_graph_writes_a_list_frame_rate_through_the_schema() -> None:
    """A mux node saved with list widgets still gets its named rate widget."""
    graph: JsonObject = {
        "nodes": [
            {"id": 1, "type": "VHS_VideoCombine", "widgets_values": [24.0, 0, "ez_edit_cutaway"]},
            {"id": 2, "type": "CLIPTextEncode", "title": "Prompt", "widgets_values": ["mirror"]},
        ],
        "extra": {"lab_edit": {"widgets": {"fps": {"node": 1, "widget": "frame_rate"}}}},
    }
    patched = patch_graph(graph, prompt_text=PROMPT, duration_s=2.0, fps=25.0)
    assert _list_widgets(_node_at(patched, 0)) == [25.0, 0, "ez_edit_cutaway"]
    assert _list_widgets(_node_at(patched, 1)) == ["mirror"]


def test_patch_graph_ignores_map_entries_it_cannot_resolve() -> None:
    """An entry that names no node or no writable widget patches nothing."""
    graph: JsonObject = {
        "nodes": [
            {
                "id": 1,
                "type": "EZWanPromptEnhance",
                "widgets_values": ["custom", "authored", True, "t2v", "5 seconds, 24 fps", "none", "x"],
            },
            {"id": 2, "type": "Wan22ImageToVideoLatent", "widgets_values": [832, 480]},
            {"id": 3, "type": "VHS_VideoCombine", "widgets_values": {"loop_count": 0}},
            {"id": 4, "type": "EZWanPromptEnhance", "widgets_values": "not-a-container"},
            {"id": 5, "type": "SomeOtherNode", "widgets_values": ["a", "b"]},
            {"id": 6, "type": "CLIPTextEncode", "title": "Prompt (cutaway)", "widgets_values": ["mirror"]},
            {"id": 7, "type": "Wan22ImageToVideoLatent", "title": "Video size & length", "widgets_values": [832, 480, 121, 1]},
            {"id": 8, "type": "VHS_VideoCombine", "title": "Save cutaway (MP4)", "widgets_values": {"frame_rate": 24}},
        ],
        "extra": {
            "lab_edit": {
                "widgets": {
                    "prompt": {"node": 99, "widget": "prompt"},
                    "length": {"node": 2, "widget": "length"},
                    "fps": {"node": 3, "widget": "frame_rate"},
                }
            }
        },
    }
    patched = patch_graph(graph, prompt_text=PROMPT, duration_s=5.0, fps=30.0)
    nodes = _nodes_by_id(patched)
    assert _list_widgets(nodes[1])[1] == "authored"
    assert _list_widgets(nodes[2]) == [832, 480]
    assert _dict_widgets(nodes[3]) == {"loop_count": 0}
    for nid in (4, 5, 6, 7, 8):
        assert nodes[nid]["widgets_values"] == _node_at(graph, nid - 1)["widgets_values"]


@pytest.mark.parametrize(
    ("key", "entry", "node"),
    [
        (
            "prompt",
            {"node": 1, "widget": "prompt"},
            {"id": 1, "type": "EZWanPromptEnhance", "widgets_values": "not-a-container"},
        ),
        (
            "length",
            {"node": 1, "widget": "length"},
            {"id": 1, "type": "SomeOtherNode", "widgets_values": ["a", "b"]},
        ),
        (
            "fps",
            {"node": 1, "widget": "nope"},
            {"id": 1, "type": "EZWanPromptEnhance", "widgets_values": ["custom", "authored", True]},
        ),
        (
            "fps",
            {"node": 1, "widget": "   "},
            {"id": 1, "type": "VHS_VideoCombine", "widgets_values": [24.0]},
        ),
        (
            "length",
            {"node": 1, "widget": "length"},
            {"id": 1, "type": "Note", "widgets_values": None},
        ),
        (
            "prompt",
            {"widget": "prompt"},
            {"id": 1, "type": "EZWanPromptEnhance", "widgets_values": ["custom", "authored", True]},
        ),
    ],
    ids=[
        "widgets-not-a-container",
        "node-type-outside-the-schema",
        "widget-name-outside-the-schema",
        "widget-name-blank",
        "widgets-absent",
        "node-id-absent",
    ],
)
def test_patch_graph_writes_only_widgets_the_schema_knows(
    key: str, entry: JsonObject, node: JsonObject
) -> None:
    """An unanswerable map entry patches nothing and never falls back.

    Once the generator wrote a map, the map is the contract: a bait node the
    title heuristics would have picked stays as authored.
    """
    bait: JsonObject = {"id": 9, "type": "CLIPTextEncode", "title": "Prompt (cutaway)", "widgets_values": ["mirror"]}
    widgets: JsonObject = {key: entry}
    graph: JsonObject = {
        "nodes": [node, bait],
        "extra": {"lab_edit": {"widgets": widgets}},
    }
    patched = patch_graph(graph, prompt_text=PROMPT, duration_s=5.0, fps=30.0)
    assert _node_at(patched, 0)["widgets_values"] == node["widgets_values"]
    assert _list_widgets(_node_at(patched, 1)) == ["mirror"]


def test_patch_graph_ignores_a_map_that_names_no_patch_key() -> None:
    """A map with no ``prompt``/``length``/``fps`` key patches nothing."""
    graph: JsonObject = {
        "nodes": [
            {"id": 1, "type": "CLIPTextEncode", "title": "Prompt (cutaway)", "widgets_values": ["mirror"]},
            {"id": 2, "type": "Wan22ImageToVideoLatent", "title": "Video size & length", "widgets_values": [832, 480, 121, 1]},
        ],
        "extra": {"lab_edit": {"widgets": {"seed": {"node": 2, "widget": "seed"}}}},
    }
    patched = patch_graph(graph, prompt_text=PROMPT, duration_s=2.0, fps=25.0)
    assert _list_widgets(_node_at(patched, 0)) == ["mirror"]
    assert _list_widgets(_node_at(patched, 1)) == [832, 480, 121, 1]


@pytest.mark.parametrize(
    "extra",
    [
        None,
        "not-an-object",
        {"lab_edit": "not-an-object"},
        {"lab_edit": {}},
        {"lab_edit": {"widgets": "not-an-object"}},
        {"lab_edit": {"widgets": {}}},
    ],
    ids=[
        "no-extra",
        "extra-not-an-object",
        "lab-edit-not-an-object",
        "no-widgets-key",
        "widgets-not-an-object",
        "widgets-empty",
    ],
)
def test_patch_graph_falls_back_to_the_heuristics_without_a_usable_map(
    extra: Any,
) -> None:
    """Only a graph with no usable map is patched by title and type."""
    graph: JsonObject = {
        "nodes": [
            {"id": 1, "type": "CLIPTextEncode", "title": "Prompt (cutaway)", "widgets_values": ["mirror"]},
            {"id": 2, "type": "Wan22ImageToVideoLatent", "title": "Video size & length", "widgets_values": [832, 480, 121, 1]},
            {"id": 3, "type": "VHS_VideoCombine", "title": "Save cutaway (MP4)", "widgets_values": {"frame_rate": 24}},
        ]
    }
    if extra is not None:
        graph["extra"] = extra
    patched = patch_graph(graph, prompt_text=PROMPT, duration_s=2.0, fps=25.0)
    nodes = _nodes_by_id(patched)
    assert _list_widgets(nodes[1]) == [PROMPT]
    assert _list_widgets(nodes[2])[2] == 50
    assert _dict_widgets(nodes[3])["frame_rate"] == 25.0


def test_patch_graph_falls_back_to_node_type_heuristics() -> None:
    """A re-saved graph without operator titles still patches."""
    patched = patch_graph(_graph(), prompt_text=PROMPT, duration_s=4.0, fps=24.0)
    nodes = _nodes_by_id(patched)
    assert _list_widgets(nodes[1]) == [PROMPT]
    assert _list_widgets(nodes[2]) == ["bad"]
    assert _list_widgets(nodes[3])[2] == 96
    assert _list_widgets(nodes[4]) == [42, "fixed", 20]


def test_patch_graph_handles_dict_widgets_and_absent_nodes() -> None:
    """Dict widgets patch by key; a graph with no nodes is left alone."""
    graph: JsonObject = {
        "nodes": [
            {"id": 1, "type": "PrimitiveStringMultiline", "title": "Prompt", "widgets_values": {"value": "x"}},
            {"id": 2, "type": "WanLatent", "widgets_values": {"length": 1}},
            {"id": 3, "type": "VHS_VideoCombine", "title": "Save cutaway", "widgets_values": {"fps": 8}},
            {"id": 4, "type": "Note", "widgets_values": {"text": "no keys here"}},
            {"id": 5, "type": "Note", "widgets_values": {"other": 1}},
            "not-a-node",
        ]
    }
    patched = patch_graph(graph, prompt_text=PROMPT, duration_s=2.0, fps=12.5)
    nodes = _nodes_by_id(patched)
    assert _dict_widgets(nodes[1])["value"] == PROMPT
    assert _dict_widgets(nodes[2])["length"] == 25
    assert _dict_widgets(nodes[3])["fps"] == 12.5
    assert nodes[4]["widgets_values"] == {"text": "no keys here"}
    assert nodes[5]["widgets_values"] == {"other": 1}


def test_patch_graph_tolerates_a_graph_without_nodes() -> None:
    """A graph object with no node list patches to itself."""
    assert patch_graph({"version": 1}, prompt_text=PROMPT, duration_s=1.0, fps=24.0) == {
        "version": 1,
        "nodes": [],
    }


def test_patch_graph_list_widget_frames_and_fps_boundaries() -> None:
    """Too-short widget lists and float-free lists are left alone."""
    graph: JsonObject = {
        "nodes": [
            {"id": 1, "type": "CLIPTextEncode", "title": "Prompt", "widgets_values": [1, 2]},
            {"id": 2, "type": "Latent", "widgets_values": [1]},
            {"id": 3, "type": "Mux", "title": "Save cutaway", "widgets_values": ["a", "b"]},
            {"id": 4, "type": "Mux", "title": "Video combine", "widgets_values": [24.0, 2]},
        ]
    }
    patched = patch_graph(graph, prompt_text=PROMPT, duration_s=3.0, fps=24.0)
    nodes = _nodes_by_id(patched)
    assert _list_widgets(nodes[1]) == [1, 2]
    assert _list_widgets(nodes[2]) == [1]
    assert _list_widgets(nodes[3]) == ["a", "b"]
    assert _list_widgets(nodes[4]) == [24.0, 2]


def test_patch_graph_skips_nodes_without_the_right_widgets() -> None:
    """A node that matches by type or title but lacks the widget is skipped."""
    graph: JsonObject = {
        "nodes": [
            {"id": 1, "type": "CLIPTextEncode", "title": "Negative", "widgets_values": ["bad"]},
            {"id": 2, "type": "CLIPTextEncode", "widgets_values": {"other": 1}},
            {"id": 3, "type": "LatentNode", "title": "Length", "widgets_values": {"width": 1}},
            {"id": 4, "type": "Mux", "title": "Save cutaway", "widgets_values": ["a", 24.0]},
        ]
    }
    patched = patch_graph(graph, prompt_text=PROMPT, duration_s=2.0, fps=25.0)
    nodes = _nodes_by_id(patched)
    assert _list_widgets(nodes[1]) == ["bad"]
    assert _dict_widgets(nodes[2]) == {"other": 1}
    assert _dict_widgets(nodes[3]) == {"width": 1}
    assert _list_widgets(nodes[4]) == ["a", 25.0]


def test_patch_graph_leaves_a_mux_node_without_a_rate_widget() -> None:
    """A mux node with no frame-rate widget is not invented into being."""
    graph: JsonObject = {"nodes": [{"id": 1, "type": "VHS_VideoCombine", "title": "Save cutaway", "widgets_values": {"loop_count": 0}}]}
    patched = patch_graph(graph, prompt_text=PROMPT, duration_s=1.0, fps=24.0)
    assert _dict_widgets(_node_at(patched, 0)) == {"loop_count": 0}


def test_patch_graph_writes_a_prompt_into_an_empty_widget_list() -> None:
    """A prompt node with no widgets yet receives the text."""
    graph: JsonObject = {"nodes": [{"id": 1, "type": "CLIPTextEncode", "title": "Prompt", "widgets_values": []}]}
    patched = patch_graph(graph, prompt_text=PROMPT, duration_s=1.0, fps=24.0)
    assert _list_widgets(_node_at(patched, 0)) == [PROMPT]


def test_patch_graph_refuses_a_graph_without_a_prompt_node() -> None:
    """Nothing is invented when the graph has no prompt node at all."""
    graph: JsonObject = {"nodes": [{"id": 1, "type": "KSampler", "widgets_values": [1]}]}
    patched = patch_graph(graph, prompt_text=PROMPT, duration_s=1.0, fps=24.0)
    assert _list_widgets(_node_at(patched, 0)) == [1]


@pytest.mark.parametrize(
    "payload",
    ["not json at all", "[]", '{"links": []}'],
    ids=["broken-json", "not-an-object", "no-node-list"],
)
def test_load_graph_refuses_unusable_files(tmp_path: Path, payload: str) -> None:
    """A graph file the lane cannot read raises, never half-queues."""
    target = _write_graph(tmp_path, payload)
    with pytest.raises(GraphUnavailable):
        load_graph(path=target)


def test_load_graph_refuses_a_missing_file(tmp_path: Path) -> None:
    """A graph file that was never written raises."""
    with pytest.raises(GraphUnavailable):
        load_graph(path=tmp_path / "nope.json")


def test_queue_prompt_posts_the_graph_and_returns_the_id() -> None:
    """The queue POST carries the graph and a client id when given one."""
    transport = FakeTransport([{"prompt_id": "abc123"}])
    prompt_id = queue_prompt(
        {"nodes": []},
        client_id="tab1",
        base_url="http://127.0.0.1:8188/",
        urlopen=transport,
    )
    assert prompt_id == "abc123"
    url, data = transport.calls[0]
    assert url == "http://127.0.0.1:8188/prompt"
    assert data is not None
    assert json.loads(data)["client_id"] == "tab1"


@pytest.mark.parametrize(
    ("reply", "needle"),
    [
        ({}, "no prompt_id"),
        ({"prompt_id": ""}, "no prompt_id"),
        (["not", "a", "dict"], "no prompt_id"),
        (GenerateClipError("boom"), "boom"),
    ],
    ids=["empty", "blank-id", "not-a-dict", "wire-error"],
)
def test_queue_prompt_refuses_a_useless_reply(reply: Any, needle: str) -> None:
    """Any queue failure surfaces as GenerateClipError with a reason."""
    transport = FakeTransport([reply])
    with pytest.raises(GenerateClipError, match=needle):
        queue_prompt({"nodes": []}, base_url="http://h:1", urlopen=transport)


def test_queue_prompt_reports_a_non_json_body() -> None:
    """An HTML error page from ComfyUI is reported, not parsed."""

    class _Html(_Response):
        @override
        def read(self) -> bytes:
            """Return a non-JSON body.

            Returns:
                HTML bytes.
            """
            return b"<html>502</html>"

    def opener(request: urllib.request.Request, timeout: float) -> Any:
        """Answer with HTML.

        Args:
            request: Prepared request.
            timeout: Socket timeout.

        Returns:
            HTML response.
        """
        del request, timeout
        return _Html("")

    with pytest.raises(GenerateClipError, match="invalid JSON"):
        queue_prompt({"nodes": []}, base_url="http://h:1", urlopen=opener)


def test_poll_history_returns_the_entry_after_a_wait() -> None:
    """The poll sleeps between tries and returns the entry when it lands."""
    waits: list[float] = []

    transport = FakeTransport([{}, {"pid": {"outputs": {}}}])
    entry = poll_history(
        "pid",
        base_url="http://h:1",
        urlopen=transport,
        sleeper=waits.append,
        poll_s=0.5,
        timeout_s=2.0,
    )
    assert entry == {"outputs": {}}
    assert waits == [0.5]


def test_poll_history_times_out_quietly() -> None:
    """A prompt that never lands reports no entry rather than raising."""
    transport = FakeTransport([{}, {}, {}])
    assert (
        poll_history(
            "pid",
            base_url="http://h:1",
            urlopen=transport,
            sleeper=lambda _s: None,
            poll_s=0.001,
            timeout_s=0.003,
        )
        == {}
    )


def test_poll_history_survives_a_broken_history_endpoint() -> None:
    """Repeated wire errors read as "not finished yet", never a crash."""
    transport = FakeTransport([urllib.error.URLError("down"), {"pid": {"status": {}}}] )
    entry = poll_history(
        "pid",
        base_url="http://h:1",
        urlopen=transport,
        sleeper=lambda _s: None,
        poll_s=0.001,
        timeout_s=1.0,
    )
    assert entry == {"status": {}}


def test_poll_history_uses_the_default_sleeper() -> None:
    """No sleeper means the module's own sleep is used (still microseconds)."""
    transport = FakeTransport([{}, {"pid": {"outputs": {}}}])
    assert poll_history(
        "pid",
        base_url="http://h:1",
        urlopen=transport,
        poll_s=0.001,
        timeout_s=0.5,
    ) == {"outputs": {}}


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        ({"outputs": {"10": {"images": [{"filename": "still.png"}]}}}, "still.png"),
        ({"outputs": {"10": {"videos": [{"filename": "v.mp4", "subfolder": "/x/"}]}}}, "x/v.mp4"),
        ({"outputs": {"10": {"gifs": [{"filename": ""}]}}}, ""),
        ({"outputs": {"10": {"gifs": ["junk"]}}}, ""),
        ({"outputs": {"10": {"gifs": "junk"}}}, ""),
        ({"outputs": "junk"}, ""),
        ({}, ""),
    ],
    ids=[
        "images",
        "videos-subfolder",
        "blank-name",
        "junk-row",
        "junk-list",
        "junk-outputs",
        "no-outputs",
    ],
)
def test_artefact_name_reads_what_history_reports(
    entry: dict[str, Any], expected: str
) -> None:
    """The first saved file wins, and junk never invents a path."""
    assert generate_clip._artefact_name(entry) == expected


def test_queue_prompt_uses_the_real_urlopen_indirection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no injected transport the module opens the socket itself."""
    captured: list[str] = []

    def fake_urlopen(request: urllib.request.Request, timeout: float) -> Any:
        """Record the URL and answer with a prompt id.

        Args:
            request: Prepared request.
            timeout: Socket timeout.

        Returns:
            Response stand-in.
        """
        del timeout
        captured.append(request.full_url)
        return _Response('{"prompt_id": "zz"}')

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert queue_prompt({"nodes": []}, base_url="http://h:1") == "zz"
    assert captured == ["http://h:1/prompt"]


def test_generate_row_is_pending_and_typed() -> None:
    """A fresh row is pending, ``generate_clip`` kind, and message-carrying."""
    row = new_generate_row(project_id="p1", prompt="   ", now=lambda: "2026-01-01T00:00:00+00:00")
    assert row["kind"] == "generate_clip"
    assert row["state"] == "pending"
    assert row["mode"] == "server"
    assert row["message"] == "generate cutaway"
    assert row["created_at"] == "2026-01-01T00:00:00+00:00"


def _deps_dir(tmp_path: Path) -> Path:
    """Edit dir under a tmp output root.

    Args:
        tmp_path: pytest tmp directory.

    Returns:
        ``<tmp>/edit`` (created).
    """
    folder = tmp_path / "edit"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def test_generate_clip_lands_an_ok_row(tmp_path: Path) -> None:
    """Happy path: pending row, queue, history, ok row with the artefact."""
    edit_dir = _deps_dir(tmp_path)
    transport = FakeTransport(
        [{"prompt_id": "pid-1"}, {"pid-1": {"outputs": {"12": {"gifs": [{"filename": "a.mp4", "subfolder": "ez_edit"}]}}}}]
    )
    row = generate_clip.generate_clip(
        edit_dir,
        prompt=PROMPT,
        duration_s=5.0,
        fps=24.0,
        project_id="p1",
        client_id="tab1",
        base_url="http://127.0.0.1:8188",
        urlopen=transport,
        sleeper=lambda _s: None,
        occupancy=lambda: "idle",
        graph_file=graph_path(),
        now=lambda: "2026-01-01T00:00:00+00:00",
    )
    assert row["state"] == "ok"
    assert row["kind"] == "generate_clip"
    assert row["project_id"] == "p1"
    assert row["client_id"] == "tab1"
    assert row["out_path"] == "ez_edit/a.mp4"
    assert "a.mp4" in row["message"]
    stored = render_server.read_job(edit_dir, row["id"])
    assert stored["state"] == "ok"
    assert transport.calls[0][0] == "http://127.0.0.1:8188/prompt"


def test_generate_clip_reports_history_without_an_artefact(tmp_path: Path) -> None:
    """A graph that saved nothing still lands an ok row naming the prompt."""
    edit_dir = _deps_dir(tmp_path)
    transport = FakeTransport([{"prompt_id": "pid-2"}, {"pid-2": {"outputs": {"1": "junk"}}}])
    row = generate_clip.generate_clip(
        edit_dir,
        prompt=PROMPT,
        base_url="http://h:1",
        urlopen=transport,
        sleeper=lambda _s: None,
        occupancy=lambda: "unknown",
        graph_file=graph_path(),
    )
    assert row["state"] == "ok"
    assert row["out_path"] == ""
    assert "pid-2" in row["message"]


def test_generate_clip_refuses_a_heavy_occupancy_without_queuing(tmp_path: Path) -> None:
    """A heavy GPU tenant gets an ok-false row and zero sockets."""
    edit_dir = _deps_dir(tmp_path)
    transport = FakeTransport([])
    row = generate_clip.generate_clip(
        edit_dir,
        prompt=PROMPT,
        base_url="http://h:1",
        urlopen=transport,
        occupancy=lambda: "wan",
        graph_file=graph_path(),
    )
    assert row["state"] == "failed"
    assert "occupancy is wan" in row["message"]
    assert transport.calls == []


def test_generate_clip_reads_occupancy_from_the_state_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No occupancy seam means the occupancy file decides (blank is unknown)."""
    edit_dir = _deps_dir(tmp_path)
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text(json.dumps({"mode": ""}), encoding="utf-8")
    transport = FakeTransport([{"prompt_id": "pid-3"}, {"pid-3": {"outputs": {}}}])
    row = generate_clip.generate_clip(
        edit_dir,
        prompt=PROMPT,
        base_url="http://h:1",
        urlopen=transport,
        sleeper=lambda _s: None,
        graph_file=graph_path(),
    )
    assert row["state"] == "ok"


def test_generate_clip_degrades_when_the_graph_is_missing(tmp_path: Path) -> None:
    """A missing graph file is an ok-false row, not a traceback."""
    edit_dir = _deps_dir(tmp_path)
    transport = FakeTransport([])
    row = generate_clip.generate_clip(
        edit_dir,
        prompt=PROMPT,
        base_url="http://h:1",
        urlopen=transport,
        occupancy=lambda: "llm-desk",
        graph_file=tmp_path / "graphs" / "generate-cutaway.json",
    )
    assert row["state"] == "failed"
    assert "generate-cutaway graph is missing" in row["message"]
    assert transport.calls == []


def test_generate_clip_degrades_on_an_unreadable_graph(tmp_path: Path) -> None:
    """Half-written graph JSON is reported as unusable."""
    edit_dir = _deps_dir(tmp_path)
    row = generate_clip.generate_clip(
        edit_dir,
        prompt=PROMPT,
        base_url="http://h:1",
        urlopen=FakeTransport([]),
        occupancy=lambda: "idle",
        graph_file=_write_graph(tmp_path, "{oops"),
    )
    assert row["state"] == "failed"
    assert "not a graph object" in row["message"]


def test_generate_clip_refuses_an_empty_prompt(tmp_path: Path) -> None:
    """No prompt text means nothing to queue."""
    edit_dir = _deps_dir(tmp_path)
    row = generate_clip.generate_clip(
        edit_dir,
        prompt="   ",
        base_url="http://h:1",
        urlopen=FakeTransport([]),
        occupancy=lambda: "idle",
        graph_file=graph_path(),
    )
    assert row["state"] == "failed"
    assert "needs a prompt" in row["message"]


def test_generate_clip_reports_a_queue_failure(tmp_path: Path) -> None:
    """A ComfyUI that refuses the queue fails the row with its reason."""
    edit_dir = _deps_dir(tmp_path)
    row = generate_clip.generate_clip(
        edit_dir,
        prompt=PROMPT,
        base_url="http://h:1",
        urlopen=FakeTransport([urllib.error.URLError("connection refused")]),
        occupancy=lambda: "idle",
        graph_file=graph_path(),
    )
    assert row["state"] == "failed"
    assert row["message"].startswith("queue failed:")
    assert "connection refused" in row["message"]


def test_generate_clip_reports_a_history_timeout(tmp_path: Path) -> None:
    """A queue that never finishes fails the row with the prompt id."""
    edit_dir = _deps_dir(tmp_path)
    row = generate_clip.generate_clip(
        edit_dir,
        prompt=PROMPT,
        base_url="http://h:1",
        urlopen=FakeTransport([{"prompt_id": "slow"}, {}, {}]),
        sleeper=lambda _s: None,
        occupancy=lambda: "idle",
        graph_file=graph_path(),
        poll_s=0.001,
        timeout_s=0.003,
    )
    assert row["state"] == "failed"
    assert "timed out waiting for prompt slow" in row["message"]


def test_generate_clip_uses_the_default_origin(tmp_path: Path) -> None:
    """With no base_url the ComfyUI origin comes from the environ."""
    edit_dir = _deps_dir(tmp_path)
    transport = FakeTransport([{"prompt_id": "pid-9"}, {"pid-9": {"outputs": {}}}])
    row = generate_clip.generate_clip(
        edit_dir,
        prompt=PROMPT,
        urlopen=transport,
        sleeper=lambda _s: None,
        occupancy=lambda: "idle",
        environ={"EZ_EDIT_COMFY_URL": "http://127.0.0.1:8188"},
        graph_file=graph_path(),
    )
    assert row["state"] == "ok"
    assert transport.calls[0][0] == "http://127.0.0.1:8188/prompt"

"""The lane browser reads the real ``_lab`` tree and never drifts from it.

The console is the only place an operator browses 596 graphs on a headless box,
so a lane that silently reads as empty is a real bug: these tests build a
throwaway tree and pin the parse, the ordering, the search, and the fact that a
broken graph file degrades one row instead of the whole lane.
"""

from __future__ import annotations

import json
from pathlib import Path

from _lab_paths import LANE_REGISTRY
from tui import lanes as L


def _write_graph(
    root: Path,
    lane: str,
    stem: str,
    *,
    rel: str | None = None,
    description: str = "",
    occupancy: str = "klein",
    handoff: list[object] | None = None,
    raw: str | None = None,
) -> Path:
    """Drop one graph file into a throwaway ``_lab`` tree.

    Args:
        root: Fake repo root.
        lane: Lane directory.
        stem: Filename stem.
        rel: ``extra.lab_rel`` value; derived from lane and stem when None.
        description: ``extra.lab_description``.
        occupancy: ``extra.lab_app_mode.occupancy``.
        handoff: ``extra.lab_app_mode.handoff``.
        raw: Literal file text, for malformed fixtures.

    Returns:
        The path written.
    """
    directory = root / "workflows" / "_lab" / lane
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{stem}.json"
    if raw is not None:
        path.write_text(raw, encoding="utf-8")
        return path
    extra: dict[str, object] = {"lab_rel": rel or f"{lane}/{stem}"}
    if description:
        extra["lab_description"] = description
    app_mode: dict[str, object] = {"occupancy": occupancy, "default_view": "app"}
    if handoff is not None:
        app_mode["handoff"] = handoff
    extra["lab_app_mode"] = app_mode
    path.write_text(json.dumps({"nodes": [], "extra": extra}), encoding="utf-8")
    return path


def test_lane_titles_match_the_single_definition() -> None:
    """The console may not invent, drop, or reorder a lane."""
    mirrored = [(row[0], row[1], row[2], row[3]) for row in L._LANE_ROWS]
    expected = [(spec.id, spec.order, spec.title, spec.description) for spec in LANE_REGISTRY]
    assert mirrored == expected


def test_lane_ids_and_order() -> None:
    """The browse order an operator sees is the registry order."""
    assert L.lane_ids() == (
        "photos",
        "video",
        "social",
        "business",
        "film",
        "audio",
        "3d",
        "guides",
        "labs",
    )


def test_lab_root_and_user_folder_are_named_from_the_repo(tmp_path: Path) -> None:
    """The hand-off pane points at the folder the operator actually loads."""
    assert L.lab_root(tmp_path) == tmp_path / "workflows" / "_lab"
    assert L.user_folder_hint().endswith("workflows/_user")


def test_lanes_count_graphs_recursively(tmp_path: Path) -> None:
    """Nested subdirs (audio albums, business verticals) count once each."""
    _write_graph(tmp_path, "audio", "rap-draft")
    _write_graph(tmp_path, "audio", "01-brake-fade", rel="audio/albums/x/01-brake-fade")
    rows = {lane.lane_id: lane.graph_count for lane in L.lanes(tmp_path)}
    assert rows["audio"] == 2
    assert rows["photos"] == 0


def test_lanes_survive_a_missing_tree(tmp_path: Path) -> None:
    """A partial checkout still shows all nine lanes."""
    rows = L.lanes(tmp_path)
    assert len(rows) == 9
    assert all(lane.graph_count == 0 for lane in rows)


def test_graphs_sort_by_rel_id_and_skip_other_lanes(tmp_path: Path) -> None:
    """Selection order is stable, and one lane never leaks another's graphs."""
    _write_graph(tmp_path, "photos", "zulu", rel="photos/zulu")
    _write_graph(tmp_path, "photos", "alpha", rel="photos/alpha")
    _write_graph(tmp_path, "video", "clip", rel="video/clip")
    ids = [graph.rel_id for graph in L.graphs(tmp_path, "photos")]
    assert ids == ["photos/alpha", "photos/zulu"]
    assert L.graphs(tmp_path, "nope") == ()


def test_graph_fields_come_from_the_extra_block(tmp_path: Path) -> None:
    """The console shows what the graph author wrote, not a filename guess."""
    path = _write_graph(
        tmp_path,
        "photos",
        "background-edit",
        description="Klein 4B background edit.  ",
        occupancy="klein",
        handoff=["photos/background-swap", 7],
    )
    graph = L.graphs(tmp_path, "photos")[0]
    assert graph.title == "background-edit"
    assert graph.description == "Klein 4B background edit."
    assert graph.occupancy == "klein"
    assert graph.default_view == "app"
    assert graph.handoff == ("photos/background-swap",)
    assert graph.path == path


def test_graph_falls_back_when_extra_is_missing(tmp_path: Path) -> None:
    """A bare graph still browses with a derived id and empty blurb."""
    directory = tmp_path / "workflows" / "_lab" / "3d"
    directory.mkdir(parents=True)
    (directory / "blockout-mesh.json").write_text('{"nodes": []}', encoding="utf-8")
    graph = L.graphs(tmp_path, "3d")[0]
    assert graph.rel_id == "3d/blockout-mesh"
    assert graph.description == ""
    assert graph.occupancy == ""
    assert graph.handoff == ()


def test_unreadable_graphs_are_skipped_not_fatal(tmp_path: Path) -> None:
    """One broken file costs one row; the lane stays browsable."""
    _write_graph(tmp_path, "guides", "good")
    _write_graph(tmp_path, "guides", "half-written", raw="{not json")
    _write_graph(tmp_path, "guides", "array", raw="[1, 2]")
    _write_graph(tmp_path, "guides", "empty", raw="")
    base = tmp_path / "workflows" / "_lab" / "guides"
    locked = base / "locked.json"
    locked.write_text('{"extra": {}}', encoding="utf-8")
    locked.chmod(0o000)
    (base / "directory.json").mkdir()
    ids = [graph.rel_id for graph in L.graphs(tmp_path, "guides")]
    assert ids == ["guides/good"]


def test_all_graphs_and_find_by_rel_id(tmp_path: Path) -> None:
    """The palette and the hand-off path address a graph by its unique id."""
    _write_graph(tmp_path, "photos", "alpha")
    _write_graph(tmp_path, "film", "act-01", rel="film/breakwater/act-01")
    assert len(L.all_graphs(tmp_path)) == 2
    found = L.find_graph(tmp_path, "film/breakwater/act-01")
    assert found is not None
    assert found.lane_id == "film"
    assert L.find_graph(tmp_path, "film/nope") is None


def test_search_matches_id_title_and_blurb_case_insensitively(
    tmp_path: Path,
) -> None:
    """One query box has to find a graph by any of its three labels."""
    _write_graph(tmp_path, "photos", "thumbnail", description="YouTube endcard")
    _write_graph(tmp_path, "photos", "banner-wide", description="Channel art")
    assert [g.rel_id for g in L.search_graphs(tmp_path, "ENDCARD")] == [
        "photos/thumbnail"
    ]
    assert [g.rel_id for g in L.search_graphs(tmp_path, "banner")] == [
        "photos/banner-wide"
    ]
    assert len(L.search_graphs(tmp_path, "   ")) == 2
    assert L.search_graphs(tmp_path, "nothing-matches") == ()


def test_is_lane_accepts_only_registry_ids() -> None:
    """A typo in a lane id is caught before it reaches a command."""
    assert L.is_lane("photos")
    assert L.is_lane("3d")
    assert not L.is_lane("Photos")
    assert not L.is_lane("photos/")
    assert not L.is_lane("")


def test_text_coercion_covers_the_scalar_shapes() -> None:
    """Scalars trim, booleans and containers read as empty."""
    assert L._text("  hi  ") == "hi"
    assert L._text(12) == "12"
    assert L._text(1.5) == "1.5"
    assert L._text(True) == ""
    assert L._text(None) == ""
    assert L._text(["a"]) == ""


def test_real_repo_still_has_graphs_in_every_lane() -> None:
    """Guard against a tree move that would blank the console for everyone."""
    root = Path(__file__).resolve().parents[2]
    rows = L.lanes(root)
    assert len(rows) == 9
    assert sum(lane.graph_count for lane in rows) > 500
    assert all(lane.graph_count > 0 for lane in rows)

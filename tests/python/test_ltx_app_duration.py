"""Standalone LTX Apps default to 8.00 s / 193 frames; films stay 5.00 s."""

from __future__ import annotations

import json
import sys

from _lab_paths import ROOT, lab_graph_paths, lab_json, lab_rel_of
from _ltx_app_duration import (
    APP_REL_RENAMES,
    FILM_KEEP_RELS,
    FRAMES_APP,
    FRAMES_DEFAULT,
    is_film_rel,
    is_standalone_ltx_app,
    iter_nodes,
    ltx_length,
)

CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_film.ltx_timing import (  # noqa: E402
    DURATION_APP_S,
    DURATION_DEFAULT_S,
    ltx_frames_for_duration,
)
from ez_film.shots import ICLORA_TEMPLATE, LTX_PRINT_TEMPLATE  # noqa: E402
from ez_prompt_enhance.nodes import EZLTXPromptEnhance  # noqa: E402

SUBS = ROOT / "custom_nodes" / "ez_studio_blocks" / "subgraphs"


def test_app_and_film_frame_constants_match_duration_math() -> None:
    assert DURATION_APP_S == 8.00
    assert DURATION_DEFAULT_S == 5.00
    assert FRAMES_APP == ltx_frames_for_duration(DURATION_APP_S) == 193
    assert FRAMES_DEFAULT == ltx_frames_for_duration(DURATION_DEFAULT_S) == 121


def test_ltx_enhance_defaults_to_eight_seconds() -> None:
    hint = EZLTXPromptEnhance.INPUT_TYPES()["required"]["duration_hint"][1]["default"]
    assert hint == "8 seconds, 24 fps"


def test_film_print_template_stays_concat_safe_five_seconds() -> None:
    assert LTX_PRINT_TEMPLATE == "motion/av/still-to-shot.json"
    assert ICLORA_TEMPLATE == "dcc/depth-control-8s.json"
    shot = json.loads(lab_json("motion/av/still-to-shot.json").read_text(encoding="utf-8"))
    lengths = [ltx_length(n) for n in iter_nodes(shot)]
    assert FRAMES_DEFAULT in lengths
    assert FRAMES_APP not in {v for v in lengths if v is not None}


def test_standalone_ltx_apps_are_eight_seconds() -> None:
    apps: list[str] = []
    for path in lab_graph_paths():
        rel = lab_rel_of(path)
        graph = json.loads(path.read_text(encoding="utf-8"))
        if not is_standalone_ltx_app(graph, rel):
            continue
        apps.append(rel)
        for node in iter_nodes(graph):
            length = ltx_length(node)
            if length is None:
                continue
            assert length == FRAMES_APP, (rel, node.get("type"), length)
        blob = json.dumps(graph)
        assert "8 seconds, 24 fps" in blob or "Eight seconds." in blob or rel.endswith(
            "-8s"
        )
    assert "stills/talking-head" in apps
    assert "motion/av/still-to-video-8s" in apps
    assert "motion/av/still-to-shot" not in apps
    assert not any(rel.startswith("films/") for rel in apps)
    assert len(apps) >= 30


def test_film_graphs_stay_five_seconds() -> None:
    for path in lab_graph_paths():
        rel = lab_rel_of(path)
        if not is_film_rel(rel) and rel not in FILM_KEEP_RELS:
            continue
        graph = json.loads(path.read_text(encoding="utf-8"))
        for node in iter_nodes(graph):
            length = ltx_length(node)
            if length is None:
                continue
            assert length == FRAMES_DEFAULT, (rel, node.get("type"), length)


def test_renamed_ltx_app_files_exist_and_old_stems_are_gone() -> None:
    from _lab_paths import LAB_ROOT

    for old, new in APP_REL_RENAMES.items():
        assert (LAB_ROOT / f"{new}.json").is_file(), new
        assert not (LAB_ROOT / f"{old}.json").is_file(), old
        extra = json.loads((LAB_ROOT / f"{new}.json").read_text(encoding="utf-8")).get(
            "extra"
        ) or {}
        assert extra.get("lab_rel") == new


def test_ltx_av_subgraph_is_eight_seconds() -> None:
    path = SUBS / "ltx-av-8s.json"
    assert path.is_file()
    assert not (SUBS / "ltx-av-12s.json").is_file()
    assert not (SUBS / "ltx-av-5s.json").is_file()
    graph = json.loads(path.read_text(encoding="utf-8"))
    lengths = [ltx_length(n) for n in iter_nodes(graph)]
    assert FRAMES_APP in {v for v in lengths if v is not None}
    film = json.loads((SUBS / "ltx-film-shot.json").read_text(encoding="utf-8"))
    film_lengths = [ltx_length(n) for n in iter_nodes(film)]
    assert FRAMES_DEFAULT in {v for v in film_lengths if v is not None}
    assert FRAMES_APP not in {v for v in film_lengths if v is not None}

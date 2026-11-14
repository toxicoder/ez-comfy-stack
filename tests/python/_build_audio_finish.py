#!/usr/bin/env python3
"""Build the picture-lock audio-finish App (no UNET; occupancy audio).

The canvas is a hand-off desk: the mix itself is the host verb
``bazelisk run //:manage -- stem-mix``, so there is no denoise chain and no fake
audio source here. Every App row this graph exposes is bound to a widget the graph
actually reads - a row that changes nothing is a defect, not a placeholder.

Run from repo root:
  python3 tests/python/_build_audio_finish.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from _lab_layout import (
    GROUP_TITLE_INSET,
    LAB_GROUP_Y0,
    LAB_NODE_Y0,
    finalize_layout,
    group as _group,
)
from _lab_paths import apply_lab_identity
from _stamp_app_mode import stamp_suite_graph
from _build_inspire_apps import _node

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))
from ez_film.catalog import film_slug  # noqa: E402

FILM_ID = "go-see"
"""Film id the shipped graph is authored against (``stem-mix --film``)."""

SHOT_ID = "01"
"""Shot id the shipped graph is authored against (``stem-mix --shot``)."""

LAB_REL = "audio/stem-mix"
"""``_lab``-relative id: the graph id the stamper keys its App spec on."""

PREFIX_ROOT = "ez_stem_mix"
"""Leading token of the save prefix, so the master sorts with the other ez_ writes."""

PREFIX_TITLE = "Save prefix"
"""Title of the one PrimitiveNode the App panel exposes."""

PREFIX_SAFE = re.compile(r"^[a-z0-9_][a-z0-9_\-/.]*$")
"""Shape the catalog audit requires of every authored save prefix."""

_PREFIX_JUNK = re.compile(r"[^a-z0-9_\-/.]+")
"""Characters a save prefix may not carry, anywhere but the first position."""

_PREFIX_LEAD_JUNK = re.compile(r"^[^a-z0-9_]+")
"""Characters a save prefix may not carry in the first position."""

_PREFIX_BLANK = re.compile(r"\s+")
"""Whitespace runs, folded to a single underscore before the junk pass."""

NOTE = """## audio/stem-mix

Picture-lock stem mix. Occupancy **audio** - stop Klein / Wan / LTX first. ACE-Step
score is a later session if `score: acestep-instrumental`.

This canvas has no audio source: SaveAudio's audio slot stays empty on purpose, so
Queue is not how this App is run and an empty Queue writes nothing. The mix is a host
ffmpeg verb. Run it from a repo shell:

  bazelisk run //:manage -- stem-mix --film go-see --shot 01 --bg PATH [--dx PATH] [--fx PATH] [--mx PATH] [--video PATH]

`--film` and `--shot` are required (the verb stops without them) and `--bg` is the bed
its usage line asks for. The stems are file paths the verb opens, not switches on this
canvas: --bg is the demuxed LTX world bed, --dx is Kokoro / Qwen3-TTS dialogue, --fx is
the optional Templates LTX-2.5 T2A pass (same distilled transformer; not a vendored
subgraph), and --mx is the ACE-Step instrumental. There is no Include DX / FX / MX row
any more - a yes/no box cannot name a path, so those rows could only ever have lied.

The one row the App panel shows, Save prefix, is wired into SaveAudio's filename_prefix
and ships as ez_stem_mix_gosee_01: the film slug and the shot id, lowercase and
path-safe. Keep it matching --film / --shot so the canvas master and the host mix at
films/<slug>/stems/<id>/mix.m4a (mix.mp4 with --video) name the same cut. Duck beds
-15 dB under DX. YouTube loudnorm I=-14.

A2V lock (talking-head): mix DX first, then Templates -> LTX-2.5 A2V freeze. Mouths will
not match (banned lip-sync OSS stays out). Foley V2A LoRA is not in v1.

Do not start Docker. Do not co-resident ACE-Step with LTX.
"""


def _safe_prefix_fragment(text: str) -> str:
    """Fold one operator entry into text a save prefix may carry.

    The catalog audit refuses a prefix that is not ``[a-z0-9_][a-z0-9_\\-/.]*``, so
    an operator entry is sanitized rather than passed through raw.

    Globals:
        _PREFIX_BLANK: Whitespace runs to fold.
        _PREFIX_JUNK: Characters illegal outside the first position.
        _PREFIX_LEAD_JUNK: Characters illegal in the first position.

    Arguments:
        text: Raw operator entry (a film id, a shot id).

    Returns:
        Lowercased text with whitespace runs replaced by ``_`` and every other
        illegal character dropped; empty when nothing path-safe survives.
    """
    lowered = str(text).strip().lower()
    return _PREFIX_LEAD_JUNK.sub("", _PREFIX_JUNK.sub("", _PREFIX_BLANK.sub("_", lowered)))


def stem_mix_prefix(film_id: str = FILM_ID, shot_id: str = SHOT_ID) -> str:
    """Compose the SaveAudio prefix for one shot card.

    The film id goes through the same catalog the host verb uses, so the canvas
    names the cut ``stem-mix`` writes to ``films/<slug>/stems/<id>/``.

    Globals:
        PREFIX_ROOT: Leading token of the composed prefix.

    Arguments:
        film_id: Film id the operator passes to ``--film``.
        shot_id: Shot id the operator passes to ``--shot``.

    Returns:
        ``ez_stem_mix_<slug>_<shot>``, sanitized for the save prefix audit.

    Raises:
        ValueError: unknown film id, so the canvas would name a cut no film owns.
    """
    try:
        slug = film_slug(film_id)
    except ValueError as exc:
        raise ValueError(f"unknown film id: {film_id}") from exc
    parts = [PREFIX_ROOT, _safe_prefix_fragment(slug), _safe_prefix_fragment(shot_id)]
    return "_".join(part for part in parts if part)


def _wire_prefix(
    graph: dict[str, Any],
    source: dict[str, Any],
    save: dict[str, Any],
    prefix: str,
) -> None:
    """Bind the prefix primitive to the save node's ``filename_prefix`` widget.

    The primitive keeps a real widget (the App panel edits it) and its STRING
    output carries that value into the widget the writer reads, so the row is a
    control the graph sees instead of a box that changes nothing.

    Globals:
        None.

    Arguments:
        graph: Graph under construction; mutated for ``last_link_id`` / ``links``.
        source: PrimitiveNode whose ``value`` holds the prefix.
        save: SaveAudio node; slot 0 stays the unwired ``audio`` input.
        prefix: Value kept on the save widget so the authored JSON agrees.

    Returns:
        None.

    Raises:
        ValueError: the primitive has no output slot to carry the wire.
    """
    outputs = list(source.get("outputs") or [])
    if not outputs:
        raise ValueError(f"primitive {source.get('id')} has no output slot")
    link_id = int(graph.get("last_link_id") or 0) + 1
    graph["last_link_id"] = link_id
    graph["links"] = list(graph.get("links") or []) + [
        [link_id, int(source["id"]), 0, int(save["id"]), 1, "STRING"]
    ]
    outputs[0] = {**outputs[0], "links": [link_id], "slot_index": 0}
    source["outputs"] = outputs
    save["inputs"] = [
        {"name": "audio", "type": "AUDIO", "link": None},
        {
            "name": "filename_prefix",
            "type": "STRING",
            "link": link_id,
            "widget": {"name": "filename_prefix"},
        },
    ]
    save["widgets_values"] = [prefix]


def build_audio_finish() -> dict[str, Any]:
    note_h = 460.0
    card_w, card_h = 320.0, 120.0
    gap = 48.0
    desk_y = LAB_NODE_Y0 + note_h + GROUP_TITLE_INSET + 20.0
    prefix = stem_mix_prefix()
    nodes = [
        _node(
            1,
            "Note",
            [40, LAB_NODE_Y0],
            [1340, note_h],
            "Operator note",
            [NOTE],
            0,
        )
    ]
    prefix_node = _node(
        2,
        "PrimitiveNode",
        [40, desk_y],
        [card_w, card_h],
        PREFIX_TITLE,
        [prefix, "fixed"],
        1,
        [
            {
                "name": "STRING",
                "type": "STRING",
                "links": None,
                "widget": {"name": "value"},
                "slot_index": 0,
            }
        ],
    )
    nodes.append(prefix_node)
    save_id = 3
    save_node = {
        "id": save_id,
        "type": "SaveAudio",
        "pos": [40 + card_w + gap, desk_y],
        "size": [320, 100],
        "flags": {},
        "order": 2,
        "mode": 0,
        "inputs": [{"name": "audio", "type": "AUDIO", "link": None}],
        "outputs": [],
        "properties": {"Node name for S&R": "SaveAudio"},
        "widgets_values": [prefix],
        "title": "Save stem mix (host stem-mix.sh)",
    }
    nodes.append(save_node)
    graph = {
        "id": "stem-mix",
        "revision": 1,
        "last_node_id": save_id,
        "last_link_id": 0,
        "nodes": nodes,
        "links": [],
        "groups": [
            _group(1, "NOTE", 20, LAB_GROUP_Y0, 1380, note_h + GROUP_TITLE_INSET, "#3f789e"),
            _group(
                2,
                "STEMS",
                20,
                desk_y - GROUP_TITLE_INSET,
                card_w * 2 + gap + 40,
                card_h + GROUP_TITLE_INSET + 20,
                "#3f789e",
            ),
        ],
        "config": {},
        "extra": {
            "lab_profile": LAB_REL,
            "lab_note": NOTE,
            "lab_description": (
                "Picture-lock stem mix desk. Occupancy audio. Mix via stem-mix.sh; "
                "the Save prefix row names the master."
            ),
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }
    apply_lab_identity(graph, LAB_REL)
    _wire_prefix(graph, prefix_node, save_node, prefix)
    return graph


def main() -> None:
    graph = build_audio_finish()
    stamp_suite_graph(graph)
    finalize_layout(graph)
    dest = Path(__file__).resolve().parents[2] / "workflows" / "_lab" / "audio" / "stem-mix.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(__import__("json").dumps(graph, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {dest.relative_to(Path(__file__).resolve().parents[2])}")


if __name__ == "__main__":
    main()

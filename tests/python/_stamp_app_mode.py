"""Reusable ComfyUI App Mode stamp for lab graphs.

Not imported by pytest collection (leading underscore). Tests import
``stamp_app_mode``. Builders call it after writing extra.lab_profile /
lab_note / lab_description.

Official persist: extra.linearData = {inputs, outputs}
  LinearInput = [widgetId, widgetName, config?]
  widgetId = "{node.id}:{widgetName}" when the node exists
Lab contract: extra.lab_app_mode
Do not require extra.linearMode (upstream does not write it; lab sugar only).
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

FRONTEND_MIN = "1.41.13"
LANES = ("inspire", "produce", "audio", "film", "dcc")
OCCUPANCIES = ("llm", "klein", "wan", "ltx", "audio", "film", "none")
DEFAULT_VIEWS = ("app", "graph")
BANNED = (
    "MiniMax",
    "MiniMaxH3",
    "minimax_h3",
    "klein-9b",
    "FLUX.2-dev",
    "Seedance",
    "Kling",
    "z_image_turbo",
)

NodeRef = int | str
InputSpec = tuple[NodeRef, str] | tuple[NodeRef, str, Mapping[str, Any] | None]


def _banned_hit(blob: str) -> str | None:
    for needle in BANNED:
        if needle in blob:
            return needle
    return None


def _assert_clean(payload: Any, *, where: str) -> None:
    hit = _banned_hit(json.dumps(payload, default=str))
    if hit is not None:
        raise ValueError(f"banned string {hit!r} in {where}")


def _find_nodes(graph: dict, ref: NodeRef) -> list[dict]:
    nodes = list(graph.get("nodes") or [])
    if isinstance(ref, int) or (isinstance(ref, str) and ref.isdigit()):
        nid = int(ref)
        return [n for n in nodes if int(n["id"]) == nid]
    titled = [n for n in nodes if n.get("title") == ref]
    if titled:
        return titled
    return [n for n in nodes if n.get("type") == ref]


def _resolve_node(graph: dict, ref: NodeRef, *, kind: str) -> dict:
    hits = _find_nodes(graph, ref)
    if not hits:
        raise ValueError(f"missing {kind} node {ref!r}")
    if len(hits) > 1:
        raise ValueError(f"ambiguous {kind} node {ref!r} ({len(hits)} matches)")
    return hits[0]


def _parse_input(spec: InputSpec) -> tuple[NodeRef, str, Mapping[str, Any] | None]:
    if not isinstance(spec, (tuple, list)) or len(spec) < 2:
        raise ValueError(f"invalid input spec {spec!r}")
    node_ref, widget_name = spec[0], spec[1]
    if not isinstance(widget_name, str) or not widget_name:
        raise ValueError(f"missing widget name for node {node_ref!r}")
    config = spec[2] if len(spec) > 2 else None
    return node_ref, widget_name, config


def stamp_app_mode(
    graph: dict,
    *,
    inputs: Sequence[InputSpec],
    outputs: Sequence[NodeRef],
    lane: str,
    occupancy: str,
    handoff: Sequence[str] = (),
    default_view: str = "app",
    enhance_off_identity: bool = False,
) -> dict:
    """Write extra.lab_app_mode and extra.linearData. Preserve other extra keys.

    Args:
        graph: Serialized Comfy graph (mutated in place).
        inputs: (node title|id|unique type, widgetName[, config]).
        outputs: Node title|id|unique type for SaveImage / VHS_VideoCombine.
        lane: inspire | produce | audio | film | dcc.
        occupancy: llm | klein | wan | ltx | audio | film | none.
        handoff: Downstream app ids (workflow stems).
        default_view: app | graph.
        enhance_off_identity: True when the identity/bible enhance toggle is off.

    Returns:
        The same graph dict.

    Raises:
        ValueError: missing/ambiguous node, bad lane/occupancy, or banned string.
    """
    if lane not in LANES:
        raise ValueError(f"invalid lane {lane!r}")
    if occupancy not in OCCUPANCIES:
        raise ValueError(f"invalid occupancy {occupancy!r}")
    if default_view not in DEFAULT_VIEWS:
        raise ValueError(f"invalid default_view {default_view!r}")

    _assert_clean(
        {
            "lane": lane,
            "occupancy": occupancy,
            "default_view": default_view,
            "handoff": list(handoff),
            "inputs": list(inputs),
            "outputs": list(outputs),
        },
        where="stamp labels",
    )

    linear_inputs: list[list] = []
    for spec in inputs:
        node_ref, widget_name, config = _parse_input(spec)
        node = _resolve_node(graph, node_ref, kind="input")
        widget_id = f"{node['id']}:{widget_name}"
        entry: list = [widget_id, widget_name]
        if config:
            entry.append(dict(config))
        linear_inputs.append(entry)

    linear_outputs: list[int] = []
    for ref in outputs:
        node = _resolve_node(graph, ref, kind="output")
        linear_outputs.append(int(node["id"]))

    extra = graph.setdefault("extra", {})
    extra["lab_app_mode"] = {
        "enabled": True,
        "default_view": default_view,
        "frontend_min": FRONTEND_MIN,
        "lane": lane,
        "occupancy": occupancy,
        "enhance_off_identity": bool(enhance_off_identity),
        "handoff": [str(item) for item in handoff],
    }
    extra["linearData"] = {
        "inputs": linear_inputs,
        "outputs": linear_outputs,
    }
    if default_view == "app":
        extra["linearMode"] = True
    else:
        extra.pop("linearMode", None)

    _assert_clean(extra["lab_app_mode"], where="lab_app_mode")
    _assert_clean(extra["linearData"], where="linearData")
    return graph


OCCUPANCY_STOP = {
    "none": "nothing GPU",
    "llm": "nothing GPU",
    "klein": "Wan, LTX, podcast, music",
    "wan": "LTX, podcast, music",
    "ltx": "Wan, podcast, music, other LTX",
    "film": "everything else on that Spark",
    "audio": "Klein / Wan / LTX session",
}

OUTPUT_TYPES = (
    "SaveImage",
    "VHS_VideoCombine",
    "SaveAudio",
    "SaveAudioMP3",
)

ENHANCE_TYPES = (
    "EZKleinPromptEnhance",
    "EZWanPromptEnhance",
    "EZLTXPromptEnhance",
    "EZAceStepPromptEnhance",
    "EZRapLyrics",
    "EZPodcastScript",
)


def _spec(
    lane: str,
    occupancy: str,
    *handoff: str,
    default_view: str = "app",
    enhance_off_identity: bool = False,
    expose_unet: bool = False,
    sampler_steps_cfg: bool = False,
    film_minimal: bool = False,
    forge_widgets: bool = False,
    primitive_strings: bool = False,
) -> dict[str, Any]:
    return {
        "lane": lane,
        "occupancy": occupancy,
        "handoff": handoff,
        "default_view": default_view,
        "enhance_off_identity": enhance_off_identity,
        "expose_unet": expose_unet,
        "sampler_steps_cfg": sampler_steps_cfg,
        "film_minimal": film_minimal,
        "forge_widgets": forge_widgets,
        "primitive_strings": primitive_strings,
    }


STAMP_SPECS: dict[str, dict[str, Any]] = {
    "klein-still-draft-lab-example": _spec(
        "inspire",
        "klein",
        "klein-still-hero-lab-example",
        "wan-i2v-5s-lab-example",
        "klein-platform-pack-lab-example",
    ),
    "klein-identity-sheet-lab-example": _spec(
        "inspire", "klein"
    ),
    "klein-storyboard-6up-lab-example": _spec(
        "inspire",
        "klein",
        "wan-i2v-shot-lab-example",
        "ltx-i2v-shot-lab-example",
    ),
    "klein-dream-house-lab-example": _spec(
        "inspire",
        "klein",
        "wan-gif-loop-lab-example",
        "wan-bumper-loop-lab-example",
        "wan-sticker-loop-lab-example",
    ),
    "klein-style-lock-lab-example": _spec(
        "inspire", "klein"
    ),
    "klein-lighting-trio-lab-example": _spec("inspire", "klein"),
    "klein-camera-angles-lab-example": _spec("inspire", "klein"),
    "klein-color-moods-lab-example": _spec("inspire", "klein"),
    "klein-time-of-day-lab-example": _spec("inspire", "klein"),
    "klein-hook-still-lab-example": _spec(
        "inspire", "klein", "wan-shorts-i2v-lab-example"
    ),
    "prompt-forge-lab-example": _spec(
        "inspire",
        "llm",
        "klein-still-draft-lab-example",
        forge_widgets=True,
    ),
    "beat-sheet-lab-example": _spec(
        "inspire",
        "none",
        "film-go-see-90s-run-lab-example",
        "film-still-here-90s-lab-example",
        "film-switchyard-90s-lab-example",
        primitive_strings=True,
    ),
    "klein-still-daily-lab-example": _spec(
        "produce", "klein", expose_unet=True, sampler_steps_cfg=True
    ),
    "klein-still-hero-lab-example": _spec(
        "produce",
        "klein",
        "wan-i2v-5s-lab-example",
        "ltx-i2v-5s-lab-example",
    ),
    "klein-thumbnail-lab-example": _spec("produce", "klein"),
    "klein-product-packshot-lab-example": _spec("produce", "klein"),
    "klein-ig-square-lab-example": _spec("produce", "klein"),
    "klein-og-blog-lab-example": _spec("produce", "klein"),
    "klein-banner-wide-lab-example": _spec("produce", "klein"),
    "klein-podcast-cover-lab-example": _spec("produce", "klein"),
    "klein-endcard-cta-lab-example": _spec("produce", "klein"),
    "klein-quote-bg-lab-example": _spec("produce", "klein"),
    "klein-lower-third-bg-lab-example": _spec("produce", "klein"),
    "klein-food-tabletop-lab-example": _spec("produce", "klein"),
    "klein-shorts-still-lab-example": _spec("produce", "klein"),
    "klein-before-after-lab-example": _spec("produce", "klein"),
    "klein-platform-pack-lab-example": _spec(
        "produce",
        "klein",
        "wan-i2v-5s-lab-example",
        "ltx-hook-av-lab-example",
    ),
    "klein-talking-head-lab-example": _spec("produce", "ltx"),
    "wan-i2v-5s-lab-example": _spec(
        "produce", "wan", "ltx-i2v-5s-lab-example"
    ),
    "wan-i2v-shot-lab-example": _spec("produce", "wan"),
    "wan-gif-loop-lab-example": _spec("produce", "wan"),
    "wan-bumper-loop-lab-example": _spec("produce", "wan"),
    "wan-sticker-loop-lab-example": _spec("produce", "wan"),
    "wan-shorts-i2v-lab-example": _spec(
        "produce", "wan", "ltx-shorts-i2v-lab-example"
    ),
    "wan-orbit-i2v-lab-example": _spec("produce", "wan"),
    "wan-push-in-i2v-lab-example": _spec("produce", "wan"),
    "wan-parallax-i2v-lab-example": _spec("produce", "wan"),
    "ltx-i2v-5s-lab-example": _spec("produce", "ltx"),
    "ltx-i2v-shot-lab-example": _spec("produce", "ltx"),
    "ltx-shorts-i2v-lab-example": _spec("produce", "ltx"),
    "ltx-hook-av-lab-example": _spec("produce", "ltx"),
    "ltx-broll-ambient-lab-example": _spec("produce", "ltx"),
    "ltx-weather-broll-lab-example": _spec("produce", "ltx"),
    "ltx-interior-ambience-lab-example": _spec("produce", "ltx"),
    "film-go-see-90s-run-lab-example": _spec(
        "film", "film", default_view="graph", film_minimal=True
    ),
    "film-still-here-90s-lab-example": _spec(
        "film", "film", default_view="graph", film_minimal=True
    ),
    "film-switchyard-90s-lab-example": _spec(
        "film", "film", default_view="graph", film_minimal=True
    ),
    "podcast-audio-first-lab-example": _spec("audio", "audio"),
    "podcast-radio-drama-lab-example": _spec("audio", "audio"),
    "music-rap-draft-lab-example": _spec("audio", "audio"),
    "music-rap-full-lab-example": _spec("audio", "audio"),
    "klein-from-clay-lab-example": _spec(
        "dcc", "klein"
    ),
    "ltx-iclora-depth-5s-lab-example": _spec("dcc", "ltx"),
}


def occupancy_stanza(occupancy: str) -> str:
    stop = OCCUPANCY_STOP[occupancy]
    return f"Occupancy: {occupancy} — stop {stop}. One GB10 job."


def ensure_occupancy_note(graph: dict, occupancy: str) -> None:
    stanza = occupancy_stanza(occupancy)
    extra = graph.setdefault("extra", {})
    note = str(extra.get("lab_note") or "")
    if "Occupancy:" not in note:
        extra["lab_note"] = f"{note.rstrip()}\n\n{stanza}\n" if note.strip() else f"{stanza}\n"
    for node in graph.get("nodes") or []:
        if node.get("type") != "Note":
            continue
        values = node.get("widgets_values") or [""]
        text = str(values[0])
        if "Occupancy:" not in text:
            node["widgets_values"] = [f"{text.rstrip()}\n\n{stanza}\n"]
        break


def infer_suite_inputs(graph: dict, spec: Mapping[str, Any]) -> list[InputSpec]:
    inputs: list[InputSpec] = []
    if spec.get("film_minimal"):
        for node in graph.get("nodes") or []:
            if node.get("type") == "EZKleinPromptEnhance":
                nid = node["id"]
                inputs.extend(
                    ((nid, "prompt"), (nid, "enhance"), (nid, "style"))
                )
        sampler = next(
            (n for n in graph.get("nodes") or [] if n.get("type") == "KSampler"),
            None,
        )
        if sampler is not None:
            inputs.append((sampler["id"], "seed"))
        return inputs

    saw_seed = False
    for node in graph.get("nodes") or []:
        ntype = node.get("type")
        nid = node["id"]
        if ntype in ("EZAceStepPromptEnhance",):
            inputs.extend(((nid, "tags"), (nid, "lyrics"), (nid, "enhance")))
        elif ntype in ("EZRapLyrics", "EZPodcastScript"):
            widget = "lyrics" if ntype == "EZRapLyrics" else "prompt"
            inputs.extend(((nid, widget), (nid, "enhance")))
        elif ntype in ENHANCE_TYPES:
            inputs.extend(((nid, "prompt"), (nid, "enhance"), (nid, "style")))
            if spec.get("forge_widgets"):
                inputs.extend(((nid, "mode"), (nid, "duration_hint")))
        elif ntype == "PrimitiveNode" and spec.get("primitive_strings"):
            inputs.append((nid, "value"))
        elif ntype == "EZPromptJoin":
            inputs.append((nid, "shot"))
        elif ntype == "EZPodcastScript":
            inputs.extend(((nid, "prompt"), (nid, "enhance")))
        elif ntype == "EZRapLyrics":
            inputs.extend(((nid, "lyrics"), (nid, "enhance")))
        elif ntype == "EmptyFlux2LatentImage":
            inputs.extend(((nid, "width"), (nid, "height"), (nid, "batch_size")))
        elif ntype == "KSampler" and not saw_seed:
            inputs.append((nid, "seed"))
            if spec.get("sampler_steps_cfg"):
                inputs.extend(((nid, "steps"), (nid, "cfg")))
            saw_seed = True
        elif ntype == "LoadImage":
            inputs.append((nid, "image"))
        elif ntype == "UNETLoader" and spec.get("expose_unet"):
            inputs.append((nid, "unet_name"))
    return inputs


def infer_suite_outputs(graph: dict, spec: Mapping[str, Any] | None = None) -> list[int]:
    spec = spec or {}
    found = [
        int(node["id"])
        for node in graph.get("nodes") or []
        if node.get("type") in OUTPUT_TYPES
    ]
    if found:
        return found
    if spec.get("forge_widgets"):
        return [
            int(node["id"])
            for node in graph.get("nodes") or []
            if node.get("type") in ENHANCE_TYPES
        ]
    if spec.get("primitive_strings"):
        return [
            int(node["id"])
            for node in graph.get("nodes") or []
            if node.get("type") == "PrimitiveNode"
        ]
    return []


def stamp_suite_graph(graph: dict) -> dict:
    """Stamp a known suite graph. No-op when graph id is not in STAMP_SPECS."""
    spec = STAMP_SPECS.get(str(graph.get("id") or ""))
    if spec is None:
        return graph
    outputs = infer_suite_outputs(graph, spec)
    if not outputs:
        raise ValueError(f"missing output node on {graph.get('id')}")
    inputs = infer_suite_inputs(graph, spec)
    if not inputs:
        raise ValueError(f"missing creator input on {graph.get('id')}")
    ensure_occupancy_note(graph, spec["occupancy"])
    return stamp_app_mode(
        graph,
        inputs=inputs,
        outputs=outputs,
        lane=spec["lane"],
        occupancy=spec["occupancy"],
        handoff=spec["handoff"],
        default_view=spec["default_view"],
        enhance_off_identity=spec["enhance_off_identity"],
    )


def suite_json_paths(root: Any) -> list[Any]:
    """Return existing JSON paths for every STAMP_SPECS id under workflows/."""
    from pathlib import Path

    wf = Path(root)
    found: list[Path] = []
    for stem in STAMP_SPECS:
        for folder in (wf, wf / "shorts", wf / "dcc"):
            path = folder / f"{stem}.json"
            if path.is_file():
                found.append(path)
                break
    return found


def stamp_all_suite_files(root: Any | None = None) -> None:
    from pathlib import Path

    wf = Path(root) if root is not None else Path(__file__).resolve().parents[2] / "workflows"
    for path in suite_json_paths(wf):
        graph = json.loads(path.read_text(encoding="utf-8"))
        stamp_suite_graph(graph)
        path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        print(f"stamped {path}")


if __name__ == "__main__":
    stamp_all_suite_files()


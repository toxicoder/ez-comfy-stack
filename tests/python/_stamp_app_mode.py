"""Reusable ComfyUI App Mode stamp for lab graphs.

Not imported by pytest collection (leading underscore). Tests import
``stamp_app_mode``. Builders call it after writing extra.lab_profile /
lab_note / lab_description.

Official persist: extra.linearData = {inputs, outputs}
  LinearInput = [nodeId, widgetName, config?]
  nodeId = integer node.id (Comfy SerializedNodeId). Frontend 1.49.6+
  upgrades this to a live WidgetId (graphId:nodeId:name) at load.
  Do not persist "nodeId:widgetName" — the frontend treats a colon as a
  subgraph locator and drops the input.
Lab contract: extra.lab_app_mode
Do not require extra.linearMode (upstream does not write it; lab sugar only).
"""

from __future__ import annotations

import json
from collections import Counter
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


def linear_input_node_id(entry: Sequence[Any]) -> int:
    """Return the persisted node id from a linearData input tuple.

    ComfyUI frontend 1.49.6+ accepts SerializedNodeId (int, or a digit
    string with no colon) and upgrades it to a live WidgetId at load.
    Two-part ``nodeId:widgetName`` strings are dropped by the frontend.

    Args:
        entry: ``[nodeId, widgetName, config?]``.

    Returns:
        Integer node id.

    Raises:
        ValueError: missing entry, or a colon-joined / non-numeric id.
    """
    if not isinstance(entry, (list, tuple)) or not entry:
        raise ValueError(f"invalid linear input {entry!r}")
    stored = entry[0]
    if isinstance(stored, bool) or stored is None:
        raise ValueError(f"invalid linear input id {stored!r}")
    if isinstance(stored, int):
        return stored
    if isinstance(stored, str) and ":" not in stored and stored.lstrip("-").isdigit():
        return int(stored)
    raise ValueError(f"legacy or invalid linear input id {stored!r}")


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
            Persisted as [int(node.id), widgetName, config?].
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
        entry: list = [int(node["id"]), widget_name]
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


# App Mode widget order: the thing the user types first, then look, then Run knobs.
WIDGET_ORDER = (
    "source",
    "upload",
    "source_url",
    "have_rights",
    "job_slug",
    "prompt",
    "tags",
    "lyrics",
    "value",
    "style",
    "enhance",
    "mode",
    "duration_hint",
    "audio_notes",
    "seconds",
    "target_language",
    "source_language",
    "max_speakers",
    "stage",
    "engine",
    "keep_bed",
    "spoken_disclosure",
    "speaker_a_voice",
    "speaker_b_voice",
    "announcer_voice",
    "include_announcer",
    "speed",
    "image",
    "seed",
    "width",
    "height",
    "batch_size",
    "steps",
    "cfg",
    "unet_name",
)
HIDDEN_APP_WIDGETS = frozenset({"shot", "inventory", "lock"})
STYLE_IGNORED_MODES = frozenset({"i2v", "flf", "vace"})
NODE_MODE_ALWAYS = 0
WIDGET_HEIGHTS = {
    "prompt": 140,
    "lyrics": 140,
    "tags": 80,
    "audio_notes": 80,
    "value": 72,
}
GENERIC_LABELS = {
    "prompt": "Prompt",
    "style": "Style",
    "enhance": "Rewrite prompt",
    "seed": "Seed",
    "image": "Start image",
    "tags": "Tags",
    "lyrics": "Lyrics",
    "audio_notes": "Audio notes",
    "width": "Width",
    "height": "Height",
    "batch_size": "Batch",
    "steps": "Steps",
    "cfg": "CFG",
    "unet_name": "Image model",
    "mode": "Mode",
    "duration_hint": "Duration / framing",
    "value": "Shot card",
    "seconds": "Duration (seconds)",
    "speaker_a_voice": "Speaker A",
    "speaker_b_voice": "Speaker B",
    "announcer_voice": "Announcer",
    "include_announcer": "Include announcer",
    "speed": "Speaking speed",
    "source": "Source file",
    "upload": "Upload media",
    "source_url": "Source URL",
    "have_rights": "I have rights",
    "job_slug": "Job slug",
    "target_language": "Target language",
    "source_language": "Source language",
    "max_speakers": "Max speakers",
    "stage": "Stage",
    "engine": "Clone engine",
    "keep_bed": "Keep original bed",
    "spoken_disclosure": "Spoken disclosure",
}
DEFAULT_WIDGET_DESCRIPTIONS = {
    "prompt": "What to generate. Rewrite prompt expands this for the model.",
    "style": "Optional look. Hidden on I2V — the start image owns look.",
    "enhance": (
        "On: on-box Qwen3-4B rewrites for this model. Off: use your text as-is."
    ),
    "seed": "Fix to iterate; randomize to explore.",
    "image": "Start frame or reference still. Only shown when the LoadImage is wired.",
    "tags": "Genre-first ACE-Step tags.",
    "lyrics": "Lyrics, or [inst] for instrumental.",
    "audio_notes": "World SFX to interleave. No score unless you asked for music.",
    "width": "Latent width in pixels.",
    "height": "Latent height in pixels.",
    "batch_size": "How many stills in one Run.",
    "steps": "Sampler steps. Distilled Klein stays at 4 unless you swapped to base.",
    "cfg": "Guidance. Distilled Klein stays at 1.0 unless you swapped to base.",
    "unet_name": "Click to swap Klein 4B distilled / NVFP4 / base.",
    "mode": "Rewrite family for this encoder.",
    "duration_hint": "Aspect or duration the rewriter should target.",
    "value": "Shot card. Paste into workflows/shorts/<slug>.shots.yaml.",
    "seconds": "Length in seconds. Music draft stays ~32 s; full track is 96 s.",
    "speaker_a_voice": "Kokoro built-in for Speaker A. Voice-clone refs stay graph-only.",
    "speaker_b_voice": "Kokoro built-in for Speaker B.",
    "announcer_voice": "Kokoro built-in for Announcer: lines.",
    "include_announcer": "On: speak Announcer: lines. Off: skip them.",
    "speed": "TTS speed. 1.0 is the Kokoro default.",
    "source": (
        "Audio or video already in COMFY_OUTPUT_DIR/input (container /inputs). "
        "Default (none)."
    ),
    "upload": "Upload wav/mp3/mp4/mkv into input/. Requires I have rights on Queue.",
    "source_url": (
        "Optional http(s) URL you have rights to fetch. Overrides Source file when set."
    ),
    "have_rights": "Required. Off refuses Queue. No celebrity refs.",
    "job_slug": "Job folder under COMFY_OUTPUT_DIR/dubs/<slug>.",
    "target_language": "Language to speak. Spanish is the soccer-podcast default.",
    "source_language": "auto detects from ASR. Pin when the show is mixed-language.",
    "max_speakers": "0 = auto (cap 8). Hint when you know the cast size.",
    "stage": "all = analyze+render. analyze writes JSON. render clones the widget.",
    "engine": "chatterbox-ml (MIT, 23 langs, PerTh on) or qwen3tts (Apache).",
    "keep_bed": "On: keep original ambience in gaps. Off: speech-only mix.",
    "spoken_disclosure": "On: overlay a 3 s spoken bumper. Sidecar is always written.",
}


def _enhance_mode(node: Mapping[str, Any]) -> str:
    """Return the enhance node's mode widget (t2i / i2v / vocal / …)."""
    ntype = node.get("type")
    values = list(node.get("widgets_values") or [])
    if ntype in (
        "EZKleinPromptEnhance",
        "EZWanPromptEnhance",
        "EZLTXPromptEnhance",
    ):
        return str(values[2]) if len(values) > 2 else ""
    if ntype == "EZAceStepPromptEnhance":
        return str(values[3]) if len(values) > 3 else ""
    return ""


def _node_always(node: Mapping[str, Any]) -> bool:
    return int(node.get("mode") or 0) == NODE_MODE_ALWAYS


def _image_output_linked(node: Mapping[str, Any]) -> bool:
    for out in node.get("outputs") or []:
        if str(out.get("name") or "").upper() == "IMAGE" and out.get("links"):
            return True
    return False


def _input_linked(node: Mapping[str, Any], name: str) -> bool:
    for inp in node.get("inputs") or []:
        if not isinstance(inp, dict):
            continue
        if inp.get("name") == name and inp.get("link") is not None:
            return True
        widget = inp.get("widget") or {}
        if widget.get("name") == name and inp.get("link") is not None:
            return True
    return False


def _primitive_widget_name(node: Mapping[str, Any]) -> str | None:
    for out in node.get("outputs") or []:
        widget = out.get("widget") or {}
        name = widget.get("name")
        if name:
            return str(name)
    return None


def display_label(
    node: Mapping[str, Any] | None,
    name: str,
    *,
    collide: bool = False,
) -> str:
    """Human App Mode title. Unique when ``collide`` or the node already names it."""
    generic = GENERIC_LABELS.get(name, name.replace("_", " ").capitalize())
    if node is None:
        return generic
    ntype = str(node.get("type") or "")
    title = str(node.get("title") or "").strip()
    title_l = title.lower()
    if ntype == "LoadImage" and name == "image":
        return title or generic
    if ntype == "PrimitiveNode" and name in {"value", "seconds"}:
        if name == "seconds" or "duration" in title_l:
            return "Duration (seconds)"
        return title or generic
    if ntype == "EmptyAceStep1.5LatentAudio" and name == "seconds":
        return title or "Duration (seconds)"
    if ntype == "EZPodcastScript":
        return {"prompt": "Script", "enhance": "Rewrite script"}.get(name, generic)
    if ntype == "EZDubIngest":
        return {
            "source": "Source file",
            "upload": "Upload media",
            "source_url": "Source URL",
            "have_rights": "I have rights",
            "job_slug": "Job slug",
        }.get(name, generic)
    if ntype == "EZDubScript":
        return {
            "prompt": "Translation",
            "enhance": "Rewrite translation",
            "target_language": "Target language",
            "source_language": "Source language",
            "max_speakers": "Max speakers",
            "stage": "Stage",
        }.get(name, generic)
    if ntype == "EZDubRender":
        return {
            "engine": "Clone engine",
            "keep_bed": "Keep original bed",
            "spoken_disclosure": "Spoken disclosure",
            "speed": "Speaking speed",
        }.get(name, generic)
    if ntype == "EZKokoroTTS":
        return {
            "speaker_a_voice": "Speaker A",
            "speaker_b_voice": "Speaker B",
            "announcer_voice": "Announcer",
            "include_announcer": "Include announcer",
            "speed": "Speaking speed",
        }.get(name, generic)
    if ntype == "EZAceStepPromptEnhance":
        kind = ""
        if "sting" in title_l:
            kind = "Sting"
        elif "bed" in title_l:
            kind = "Bed"
        if kind:
            return {
                "tags": f"{kind} tags",
                "lyrics": f"{kind} lyrics",
                "enhance": f"Rewrite {kind.lower()}",
                "mode": f"{kind} mode",
            }.get(name, generic)
        if name == "mode":
            return "Vocal / instrumental"
    if collide and ntype in ENHANCE_TYPES:
        family = None
        for token in ("Klein", "Wan", "LTX"):
            if token.lower() in title_l:
                family = token
                break
        if family:
            return {
                "prompt": f"{family} prompt",
                "style": f"{family} style",
                "enhance": f"Rewrite {family}",
                "mode": f"{family} mode",
                "duration_hint": f"{family} duration / framing",
                "audio_notes": f"{family} audio notes",
            }.get(name, generic)
        if title:
            return f"{title} — {generic}"
    if collide and title:
        return f"{title} — {generic}"
    return generic


def widget_description(name: str, node: Mapping[str, Any] | None = None) -> str | None:
    """Help text for one App Mode widget."""
    ntype = (node or {}).get("type")
    if name == "mode" and ntype == "EZAceStepPromptEnhance":
        return (
            "Vocal vs instrumental. Instrumental forces no-vocals tags and "
            "[inst] lyrics."
        )
    if name == "seconds" and ntype == "EmptyAceStep1.5LatentAudio":
        return "Bed or sting length in seconds."
    if name == "prompt" and ntype == "EZPodcastScript":
        return "Speaker A/B lines. Disclosure prepends the spoken bumper."
    if name == "prompt" and ntype == "EZDubScript":
        return "Editable turns JSON. Rewrite translation fills text_target."
    if name == "enhance" and ntype == "EZDubScript":
        return "On: diarize + ASR + GGUF translate. Off: pin this JSON."
    return DEFAULT_WIDGET_DESCRIPTIONS.get(name)


def widget_config(
    name: str,
    spec: Mapping[str, Any] | None = None,
    node: Mapping[str, Any] | None = None,
    collide: bool = False,
) -> dict[str, Any] | None:
    """Return linearData InputWidgetConfig (description / label / height)."""
    overrides = (spec or {}).get("descriptions") or {}
    text = overrides.get(name) or widget_description(name, node)
    label = display_label(node, name, collide=collide)
    height = WIDGET_HEIGHTS.get(name)
    config: dict[str, Any] = {}
    if text:
        config["description"] = str(text)
    if label:
        config["label"] = str(label)
    if height:
        config["height"] = int(height)
    return config or None


def _input_spec(
    nid: NodeRef,
    name: str,
    spec: Mapping[str, Any] | None = None,
    node: Mapping[str, Any] | None = None,
    collide: bool = False,
) -> InputSpec:
    config = widget_config(name, spec, node=node, collide=collide)
    if config:
        return (nid, name, config)
    return (nid, name)


def _widget_rank(name: str, node: Mapping[str, Any] | None = None) -> int:
    if name == "value" and node is not None:
        title = str(node.get("title") or "").lower()
        if "duration" in title:
            name = "seconds"
    try:
        return WIDGET_ORDER.index(name)
    except ValueError:
        return len(WIDGET_ORDER)


def order_app_inputs(
    inputs: Sequence[InputSpec], graph: Mapping[str, Any] | None = None
) -> list[InputSpec]:
    """Prompt / tags first. Stable for equal ranks (node order)."""

    def _rank(spec: InputSpec) -> int:
        ref, name, _config = _parse_input(spec)
        node = None
        if graph is not None:
            hits = _find_nodes(dict(graph), ref)
            if len(hits) == 1:
                node = hits[0]
        return _widget_rank(name, node)

    return sorted(inputs, key=_rank)


def _spec(
    lane: str,
    occupancy: str,
    *handoff: str,
    default_view: str = "app",
    enhance_off_identity: bool = False,
    expose_unet: bool = False,
    expose_latent: bool = False,
    sampler_steps_cfg: bool = False,
    film_minimal: bool = False,
    forge_widgets: bool = False,
    primitive_strings: bool = False,
    hide_images: bool = False,
    ace_instrumental_score: bool = False,
) -> dict[str, Any]:
    return {
        "lane": lane,
        "occupancy": occupancy,
        "handoff": handoff,
        "default_view": default_view,
        "enhance_off_identity": enhance_off_identity,
        "expose_unet": expose_unet,
        "expose_latent": expose_latent,
        "sampler_steps_cfg": sampler_steps_cfg,
        "film_minimal": film_minimal,
        "forge_widgets": forge_widgets,
        "primitive_strings": primitive_strings,
        "hide_images": hide_images,
        "ace_instrumental_score": ace_instrumental_score,
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
    "klein-dream-house-clay-lab-example": _spec(
        "inspire",
        "klein",
        "wan-gif-loop-lab-example",
        "wan-bumper-loop-lab-example",
        "wan-sticker-loop-lab-example",
        hide_images=True,
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
    "klein-character-draft-lab-example": _spec(
        "inspire",
        "klein",
        "klein-character-tweak-lab-example",
        "klein-identity-sheet-lab-example",
        "wan-i2v-5s-lab-example",
    ),
    "klein-character-tweak-lab-example": _spec(
        "inspire",
        "klein",
        "klein-identity-sheet-lab-example",
        "wan-i2v-5s-lab-example",
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
        "klein-identity-sheet-lab-example",
        "klein-from-clay-lab-example",
        "film-go-see-90s-run-lab-example",
        primitive_strings=True,
    ),
    "klein-still-daily-lab-example": _spec(
        "produce",
        "klein",
        expose_unet=True,
        expose_latent=True,
        sampler_steps_cfg=True,
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
    "wan-t2v-5s-lab-example": _spec("produce", "wan"),
    "wan-flf-5s-lab-example": _spec("produce", "wan"),
    "wan-vace-join-lab-example": _spec("produce", "wan"),
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
    "ltx-t2v-5s-lab-example": _spec("produce", "ltx"),
    "ltx-i2v-shot-lab-example": _spec("produce", "ltx"),
    "ltx-shorts-i2v-lab-example": _spec("produce", "ltx"),
    "ltx-hook-av-lab-example": _spec("produce", "ltx"),
    "ltx-broll-ambient-lab-example": _spec("produce", "ltx"),
    "ltx-weather-broll-lab-example": _spec("produce", "ltx"),
    "ltx-interior-ambience-lab-example": _spec("produce", "ltx"),
    "film-go-see-90s-run-lab-example": _spec(
        "film",
        "film",
        default_view="graph",
        film_minimal=True,
        enhance_off_identity=True,
    ),
    "film-still-here-90s-lab-example": _spec(
        "film",
        "film",
        default_view="graph",
        film_minimal=True,
        enhance_off_identity=True,
    ),
    "film-switchyard-90s-lab-example": _spec(
        "film",
        "film",
        default_view="graph",
        film_minimal=True,
        enhance_off_identity=True,
    ),
    "podcast-audio-first-lab-example": _spec("audio", "audio"),
    "podcast-radio-drama-lab-example": _spec("audio", "audio"),
    "dub-localize-lab-example": _spec("audio", "audio"),
    "music-rap-draft-lab-example": _spec("audio", "audio"),
    "music-rap-full-lab-example": _spec("audio", "audio"),
    "klein-from-clay-lab-example": _spec(
        "dcc",
        "klein",
        "ltx-iclora-depth-5s-lab-example",
    ),
    "ltx-iclora-depth-5s-lab-example": _spec(
        "dcc",
        "ltx",
        "audio-finish-lab-example",
    ),
    "audio-finish-lab-example": _spec(
        "audio",
        "audio",
        primitive_strings=True,
    ),
    "wan-i2v-a14b-lab-example": _spec("produce", "wan", default_view="graph"),
}

def _nill_bye_stems() -> tuple[str, ...]:
    import sys
    from pathlib import Path

    custom = Path(__file__).resolve().parents[2] / "custom_nodes"
    if str(custom) not in sys.path:
        sys.path.insert(0, str(custom))
    from ez_music.diss_examples import DISS_EXAMPLES

    return tuple(ex["stem"] for ex in DISS_EXAMPLES)


NILL_BYE_STAMP_STEMS = _nill_bye_stems()
for _nill_bye_stem in NILL_BYE_STAMP_STEMS:
    STAMP_SPECS[_nill_bye_stem] = _spec("audio", "audio")


def _drive_through_stems() -> tuple[str, ...]:
    import sys
    from pathlib import Path

    custom = Path(__file__).resolve().parents[2] / "custom_nodes"
    if str(custom) not in sys.path:
        sys.path.insert(0, str(custom))
    from ez_music.edm_examples import EDM_EXAMPLES

    return tuple(ex["stem"] for ex in EDM_EXAMPLES)


DRIVE_THROUGH_STAMP_STEMS = _drive_through_stems()
for _drive_through_stem in DRIVE_THROUGH_STAMP_STEMS:
    STAMP_SPECS[_drive_through_stem] = _spec(
        "audio", "audio", ace_instrumental_score=True
    )

STUB_IDS = frozenset({"longcat-video-lab-example"})
OPTIONAL_UNWIRED: dict[str, tuple[str, ...]] = {
    "ltx-iclora-depth-5s-lab-example": ("EZFilmDisclosure",),
    "audio-finish-lab-example": ("SaveAudio", "PrimitiveNode"),
    "wan-i2v-a14b-lab-example": ("UNETLoader",),
    "podcast-radio-drama-lab-example": ("UNETLoader", "VHS_VideoCombine"),
    "prompt-forge-lab-example": (
        "EZKleinPromptEnhance",
        "EZWanPromptEnhance",
        "EZLTXPromptEnhance",
    ),
    "wan-flf-5s-lab-example": ("LoadImage",),
    "wan-vace-join-lab-example": ("LoadImage",),
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


def _collect_raw_inputs(
    graph: dict, spec: Mapping[str, Any]
) -> list[tuple[NodeRef, str, dict]]:
    """(node id, widget name, node) in graph order. No labels yet."""
    raw: list[tuple[NodeRef, str, dict]] = []
    if spec.get("film_minimal"):
        for node in graph.get("nodes") or []:
            if node.get("type") == "EZKleinPromptEnhance":
                nid = node["id"]
                raw.extend(
                    (
                        (nid, "prompt", node),
                        (nid, "style", node),
                        (nid, "enhance", node),
                    )
                )
        sampler = next(
            (n for n in graph.get("nodes") or [] if n.get("type") == "KSampler"),
            None,
        )
        if sampler is not None:
            raw.append((sampler["id"], "seed", sampler))
        return raw

    if spec.get("primitive_strings"):
        for node in graph.get("nodes") or []:
            if node.get("type") == "PrimitiveNode":
                raw.append((node["id"], "value", node))
        return raw

    saw_seed = False
    saw_primary_enhance = False
    for node in graph.get("nodes") or []:
        ntype = node.get("type")
        nid = node["id"]
        if ntype == "EZAceStepPromptEnhance":
            mode = _enhance_mode(node)
            show_score = mode != "instrumental" or spec.get("ace_instrumental_score")
            raw.append((nid, "tags", node))
            if show_score:
                raw.append((nid, "lyrics", node))
            raw.append((nid, "enhance", node))
            if show_score:
                raw.append((nid, "mode", node))
        elif ntype in ("EZRapLyrics", "EZPodcastScript"):
            widget = "lyrics" if ntype == "EZRapLyrics" else "prompt"
            raw.extend(
                (
                    (nid, widget, node),
                    (nid, "enhance", node),
                )
            )
        elif ntype in ENHANCE_TYPES:
            if not spec.get("forge_widgets") and saw_primary_enhance:
                continue
            saw_primary_enhance = True
            mode = _enhance_mode(node)
            skip_style = (not spec.get("forge_widgets")) and mode in STYLE_IGNORED_MODES
            raw.append((nid, "prompt", node))
            if not skip_style:
                raw.append((nid, "style", node))
            raw.append((nid, "enhance", node))
            if ntype == "EZLTXPromptEnhance":
                raw.append((nid, "audio_notes", node))
        elif ntype == "EmptyFlux2LatentImage" and spec.get("expose_latent"):
            if any(name == "width" for _nid, name, _node in raw):
                continue
            raw.extend(
                (
                    (nid, "width", node),
                    (nid, "height", node),
                    (nid, "batch_size", node),
                )
            )
        elif ntype == "KSampler" and not saw_seed:
            raw.append((nid, "seed", node))
            if spec.get("sampler_steps_cfg"):
                raw.extend(
                    (
                        (nid, "steps", node),
                        (nid, "cfg", node),
                    )
                )
            saw_seed = True
        elif ntype == "LoadImage":
            if spec.get("hide_images"):
                continue
            if _node_always(node) and _image_output_linked(node):
                raw.append((nid, "image", node))
        elif ntype == "UNETLoader" and spec.get("expose_unet"):
            raw.append((nid, "unet_name", node))
        elif ntype == "EZDubIngest":
            raw.extend(
                (
                    (nid, "source", node),
                    (nid, "upload", node),
                    (nid, "source_url", node),
                    (nid, "have_rights", node),
                    (nid, "job_slug", node),
                )
            )
        elif ntype == "EZDubScript":
            raw.extend(
                (
                    (nid, "prompt", node),
                    (nid, "enhance", node),
                    (nid, "target_language", node),
                    (nid, "source_language", node),
                    (nid, "max_speakers", node),
                    (nid, "stage", node),
                )
            )
        elif ntype == "EZDubRender":
            raw.extend(
                (
                    (nid, "engine", node),
                    (nid, "keep_bed", node),
                    (nid, "spoken_disclosure", node),
                    (nid, "speed", node),
                )
            )
        elif ntype == "EZKokoroTTS":
            raw.extend(
                (
                    (nid, "speaker_a_voice", node),
                    (nid, "speaker_b_voice", node),
                    (nid, "include_announcer", node),
                )
            )
            values = list(node.get("widgets_values") or [])
            include = bool(values[3]) if len(values) > 3 else False
            if include:
                raw.append((nid, "announcer_voice", node))
            raw.append((nid, "speed", node))
        elif ntype == "EmptyAceStep1.5LatentAudio":
            if not _input_linked(node, "seconds"):
                raw.append((nid, "seconds", node))
        elif ntype == "PrimitiveNode":
            widget = _primitive_widget_name(node) or "value"
            title_l = str(node.get("title") or "").lower()
            if widget == "seconds" or "duration" in title_l:
                raw.append((nid, widget, node))
    return [
        item
        for item in raw
        if item[1] not in HIDDEN_APP_WIDGETS
    ]


def infer_suite_inputs(graph: dict, spec: Mapping[str, Any]) -> list[InputSpec]:
    """Creator widgets only: prompt first, no join-shot cards, no latent size except daily."""
    raw = _collect_raw_inputs(graph, spec)
    counts = Counter(name for _nid, name, _node in raw)
    inputs: list[InputSpec] = []
    for nid, name, node in raw:
        collide = counts[name] > 1
        inputs.append(
            _input_spec(nid, name, spec, node=node, collide=collide)
        )
    return order_app_inputs(inputs, graph)


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


def apply_lab_completeness_flags(graph: dict) -> dict:
    """Write lab_stub / lab_optional_unwired. Preserve other extra keys."""
    extra = graph.setdefault("extra", {})
    gid = str(graph.get("id") or "")
    if gid in STUB_IDS:
        extra["lab_stub"] = True
    types = list(OPTIONAL_UNWIRED.get(gid, ()))
    occupancy = (extra.get("lab_app_mode") or {}).get("occupancy")
    if occupancy == "klein" and any(
        n.get("type") == "LoadImage" for n in graph.get("nodes") or []
    ):
        if "LoadImage" not in types:
            types.append("LoadImage")
    if types:
        extra["lab_optional_unwired"] = sorted(set(types))
    return graph


def stamp_suite_graph(graph: dict) -> dict:
    """Stamp a known suite graph. No-op when graph id is not in STAMP_SPECS."""
    spec = STAMP_SPECS.get(str(graph.get("id") or ""))
    if spec is None:
        from _wire_prompt_enhance import apply_enhance_policy

        apply_enhance_policy(graph)
        return apply_lab_completeness_flags(graph)
    outputs = infer_suite_outputs(graph, spec)
    if not outputs:
        raise ValueError(f"missing output node on {graph.get('id')}")
    inputs = infer_suite_inputs(graph, spec)
    if not inputs:
        raise ValueError(f"missing creator input on {graph.get('id')}")
    ensure_occupancy_note(graph, spec["occupancy"])
    stamp_app_mode(
        graph,
        inputs=inputs,
        outputs=outputs,
        lane=spec["lane"],
        occupancy=spec["occupancy"],
        handoff=spec["handoff"],
        default_view=spec["default_view"],
        enhance_off_identity=spec["enhance_off_identity"],
    )
    from _wire_prompt_enhance import apply_enhance_policy

    apply_enhance_policy(graph)
    return apply_lab_completeness_flags(graph)


def suite_json_paths(root: Any) -> list[Any]:
    """Return existing JSON paths for every STAMP_SPECS id under workflows/_lab."""
    from pathlib import Path

    from _lab_paths import lab_json

    wf = Path(root)
    found: list[Path] = []
    for stem in STAMP_SPECS:
        try:
            found.append(lab_json(stem, root=wf))
        except FileNotFoundError:
            continue
    return found


def stamp_all_suite_files(root: Any | None = None) -> None:
    from pathlib import Path

    from _lab_paths import lab_example_paths

    wf = Path(root) if root is not None else Path(__file__).resolve().parents[2] / "workflows"
    stamped = {p.resolve() for p in suite_json_paths(wf)}
    for path in lab_example_paths(wf if wf.name == "_lab" else wf):
        graph = json.loads(path.read_text(encoding="utf-8"))
        if path.resolve() in stamped:
            stamp_suite_graph(graph)
            label = "stamped"
        else:
            apply_lab_completeness_flags(graph)
            label = "flagged"
        path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        print(f"{label} {path}")


if __name__ == "__main__":
    stamp_all_suite_files()


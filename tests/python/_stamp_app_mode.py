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

from _enhance_schema import enhance_mode

FRONTEND_MIN = "1.41.13"
LANES = ("inspire", "produce", "audio", "film", "dcc", "optional")
OCCUPANCIES = ("llm", "klein", "wan", "ltx", "trellis", "audio", "film", "none")
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
    "trellis": "Blender desk, LTX, Wan, Klein denoise",
    "film": "everything else on that Spark",
    "audio": "Klein / Wan / LTX session",
}

OUTPUT_TYPES = (
    "SaveImage",
    "VHS_VideoCombine",
    "SaveAudio",
    "SaveAudioMP3",
    "EZDubRender",
    "EZAlbumPack",
    "EZAudioMetadata",
    "MeshToFile3D",
)

ENHANCE_TYPES = (
    "EZKleinPromptEnhance",
    "EZWanPromptEnhance",
    "EZLTXPromptEnhance",
    "EZZimagePromptEnhance",
    "EZLongCatPromptEnhance",
    "EZDreamXPromptEnhance",
    "EZAceStepPromptEnhance",
    "EZRapLyrics",
    "EZPodcastScript",
    "EZPodcastLearn",
    "EZSamplePrompt",
    "EZCreativeResearch",
    "EZAppForge",
)


def _graph_hides_sample(graph: Mapping[str, Any]) -> bool:
    extra = graph.get("extra") or {}
    rel = str(extra.get("lab_rel") or "")
    from ez_prompt_enhance.samples import album_hides_sample

    return album_hides_sample(rel)


# App Mode widget order: the thing the user types first, then look, then Run knobs.
# EZDubIngest: ``upload`` is an App button label only. Serialized node
# widgets_values stay source, have_rights, job_slug, source_url (4-wide).
WIDGET_ORDER = (
    "quality",
    "source",
    "upload",
    "source_url",
    "have_rights",
    "job_slug",
    "slug",
    "shot_id",
    "plate",
    "layer",
    "required_mode",
    "sample",
    "sources",
    "prompt",
    "format",
    "duration",
    "fetch_links",
    "template",
    "as_app",
    "overwrite",
    "subject",
    "brief",
    "recipe",
    "flavor",
    "framing_shot_size",
    "camera_angles",
    "camera_movement",
    "lenses_optics",
    "composition",
    "lighting",
    "color_film_look",
    "time_motion",
    "in_camera_optical",
    "editing_transitions",
    "atmosphere_weather",
    "genre_looks",
    "viral_looks",
    "genre_style",
    "tempo_groove",
    "drums_rhythm",
    "bass_low_end",
    "harmony_mode",
    "instruments_texture",
    "vocal_identity",
    "arrangement_form",
    "mix_production",
    "space_ambience",
    "sound_design_fx",
    "mood_energy",
    "use_case",
    "web_search",
    "subagents",
    "history",
    "tags",
    "lyrics",
    "value",
    "style",
    "enhance",
    "look",
    "mode",
    "duration_hint",
    "audio_notes",
    "seconds",
    "artist",
    "album",
    "title",
    "track",
    "tracktotal",
    "year",
    "art_mode",
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
    "cfg_weight",
    "exaggeration",
    "audio",
    "image",
    "seed",
    "width",
    "height",
    "batch_size",
    "steps",
    "cfg",
    "unet_name",
)
HIDDEN_APP_WIDGETS = frozenset({"shot", "inventory", "lock", "catalog"})
STYLE_IGNORED_MODES = frozenset({"i2v", "flf", "vace", "text_swap"})
NODE_MODE_ALWAYS = 0
NODE_MODE_BYPASS = 4
WIDGET_HEIGHTS = {
    "prompt": 140,
    "sources": 140,
    "subject": 140,
    "brief": 140,
    "lyrics": 140,
    "tags": 80,
    "audio_notes": 80,
    "value": 72,
    "history": 80,
}
GENERIC_LABELS = {
    "quality": "Quality",
    "sample": "Sample prompt",
    "prompt": "Prompt",
    "template": "Template",
    "as_app": "As app",
    "overwrite": "Overwrite",
    "subject": "Subject",
    "brief": "Brief",
    "recipe": "Recipe",
    "flavor": "Family",
    "framing_shot_size": "Shot size",
    "camera_angles": "Angle",
    "camera_movement": "Camera move",
    "lenses_optics": "Lens",
    "composition": "Composition",
    "lighting": "Lighting",
    "color_film_look": "Color",
    "time_motion": "Time",
    "in_camera_optical": "Optical FX",
    "editing_transitions": "Edit",
    "atmosphere_weather": "Weather",
    "genre_looks": "Genre",
    "viral_looks": "Viral look",
    "genre_style": "Genre",
    "tempo_groove": "Tempo",
    "drums_rhythm": "Drums",
    "bass_low_end": "Bass",
    "harmony_mode": "Harmony",
    "instruments_texture": "Instruments",
    "vocal_identity": "Vocal",
    "arrangement_form": "Form",
    "mix_production": "Mix",
    "space_ambience": "Space",
    "sound_design_fx": "Sound design",
    "mood_energy": "Mood",
    "use_case": "Use",
    "web_search": "Web search",
    "subagents": "Subagents",
    "history": "History",
    "style": "Style",
    "enhance": "Rewrite prompt",
    "look": "Look recipe",
    "seed": "Seed",
    "image": "Start image",
    "audio": "Audio file",
    "artist": "Artist",
    "album": "Album",
    "title": "Title",
    "track": "Track",
    "tracktotal": "Tracks",
    "year": "Year",
    "art_mode": "Album art",
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
    "cfg_weight": "Clone CFG",
    "exaggeration": "Exaggeration",
    "source": "Source file",
    "upload": "Upload media",
    "source_url": "Source URL",
    "have_rights": "I have rights",
    "job_slug": "Job slug",
    "slug": "Guide slug",
    "shot_id": "Shot id",
    "plate": "Plate",
    "layer": "Layer",
    "required_mode": "Occupancy",
    "target_language": "Target language",
    "source_language": "Source language",
    "max_speakers": "Max speakers",
    "stage": "Stage",
    "engine": "Clone engine",
    "keep_bed": "Keep original bed",
    "spoken_disclosure": "Spoken disclosure",
}
DEFAULT_WIDGET_DESCRIPTIONS = {
    "quality": (
        "Lab default, Draft (faster), or High (slower). "
        "Family-specific — not --tier."
    ),
    "sample": "Pick a lab recipe, or Custom to type your own.",
    "prompt": "What to generate. Rewrite prompt expands this for the model.",
    "template": "auto picks a shipped lab graph. Pin a lab_rel to skip the picker.",
    "as_app": "On: write *.app.json for the Apps sidebar. Off: graph-only *.json.",
    "overwrite": "On: replace an existing _user file with this slug.",
    "subject": "Who or what is in the shot. Cinema Rack splices technique clauses after this.",
    "brief": "Optional lyrics seed. Ignored on instrumental and podcast-bed flavors.",
    "recipe": "Named splice that fills empty axes only. Explicit dropdowns win.",
    "flavor": "klein / wan_t2v / ltx_t2v (and edit, identity, i2v). Wan emits one camera verb.",
    "framing_shot_size": "How much of the subject fills the frame.",
    "camera_angles": "Camera height and subject-relative angle.",
    "camera_movement": "The single camera verb. Wan uses this token only.",
    "lenses_optics": "Focal length, depth of field, and optic character.",
    "composition": "Where masses sit in the frame.",
    "lighting": "Key quality, direction, and motivation.",
    "color_film_look": "Grade, grain, and photochemical grammar. No stock names.",
    "time_motion": "Shutter, speed, and temporal grammar.",
    "in_camera_optical": "Flare, zoom, and in-camera tricks.",
    "editing_transitions": "Named cuts. Omitted on Klein stills.",
    "atmosphere_weather": "Air, precip, and ground. LTX interleaves foley.",
    "genre_looks": "Genre lighting and texture grammar, not a titled film.",
    "viral_looks": "Short-form hook grammar. I2V drops look axes.",
    "web_search": "On: Wikipedia + DuckDuckGo snippets. Off: on-box GGUF only.",
    "subagents": "Planner search count (1–3). Sequential CPU workers.",
    "history": "Optional prior turns. One Queue per message — not a streaming chat.",
    "style": "Optional look. Hidden on I2V — the start image owns look.",
    "enhance": (
        "On: on-box Qwen3-4B rewrites for this model. Off: use your text as-is."
    ),
    "look": (
        "Optional Cinema Rack starter spliced into Rewrite prompt context. "
        "none leaves look to Style + Prompt."
    ),
    "seed": "Fix to iterate; randomize to explore.",
    "image": "Start frame or reference still. Only shown when the LoadImage is wired.",
    "audio": (
        "Wav/mp3 already in COMFY_OUTPUT_DIR/input (container /inputs). "
        "~5 s. Original waveform is muxed into the MP4."
    ),
    "artist": "Album artist written into FLAC/MP3 tags.",
    "album": "Album title written into FLAC/MP3 tags.",
    "title": "Track title written into FLAC/MP3 tags.",
    "track": "Track number on the album.",
    "tracktotal": "Number of tracks on the album.",
    "year": "Album year.",
    "art_mode": (
        "skip (default). upload: graph view, Ctrl+B Cover image, then wire. "
        "generate: Queue cover.json first."
    ),
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
    "cfg_weight": (
        "-1 auto: 0.3 for EN→ES (CFG 0 often moans). 0.5 same-language clone."
    ),
    "exaggeration": "0.5 is neutral. Higher is more intense and faster.",
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
    "stage": "Default all. all = analyze+render. analyze writes JSON only. render clones the widget.",
    "engine": "chatterbox-ml (MIT, 23 langs, PerTh on) or qwen3tts (Apache).",
    "keep_bed": "On: keep original ambience in gaps. Off: speech-only mix.",
    "spoken_disclosure": (
        "Default off. On: localized bumper on ez_dub_mix only, not the YT wav. "
        "Off: mix starts on speech (no reserved hush). Sidecar is always written."
    ),
}


def _enhance_mode(node: Mapping[str, Any]) -> str:
    """Return the enhance node's mode widget (t2i / i2v / vocal / …)."""
    return enhance_mode(node)


def _node_always(node: Mapping[str, Any]) -> bool:
    return int(node.get("mode") or 0) == NODE_MODE_ALWAYS


def _image_output_linked(node: Mapping[str, Any]) -> bool:
    for out in node.get("outputs") or []:
        if str(out.get("name") or "").upper() == "IMAGE" and out.get("links"):
            return True
    return False


def _audio_output_linked(node: Mapping[str, Any]) -> bool:
    for out in node.get("outputs") or []:
        name = str(out.get("name") or "").upper()
        if name in {"AUDIO", "AUDIO_OUTPUT"} and out.get("links"):
            return True
        if str(out.get("type") or "").upper() == "AUDIO" and out.get("links"):
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
    if ntype == "EZKleinPromptEnhance" and name == "prompt":
        if _enhance_mode(node) == "text_swap":
            return "New lettering"
    if ntype == "EZImageFormat":
        return {
            "format": "Format / platform",
            "look": "Look recipe",
            "width": "Width",
            "height": "Height",
            "batch_size": "Batch",
        }.get(name, generic)
    if ntype == "EZVideoFormat":
        return {
            "format": "Format / platform",
            "width": "Width",
            "height": "Height",
        }.get(name, generic)
    if ntype == "LoadImage" and name == "image":
        return title or generic
    if ntype == "LoadAudio" and name == "audio":
        return title or generic
    if ntype == "PrimitiveNode" and name in {"value", "seconds"}:
        if name == "seconds" or "duration" in title_l:
            return "Duration (seconds)"
        return title or generic
    if ntype == "EmptyAceStep1.5LatentAudio" and name == "seconds":
        return title or "Duration (seconds)"
    if ntype == "EZCreativeResearch":
        return {
            "sample": "Sample prompt",
            "prompt": "Message",
            "mode": "Mode",
            "web_search": "Web search",
            "subagents": "Subagents",
            "history": "History",
        }.get(name, generic)
    if ntype == "EZAppForge":
        return {
            "sample": "Sample prompt",
            "prompt": "Brief",
            "template": "Template",
            "slug": "Slug",
            "as_app": "As app",
            "overwrite": "Overwrite",
        }.get(name, generic)
    if ntype == "EZSamplePrompt":
        if name == "prompt":
            return title or generic
        if name == "sample":
            return generic
    if ntype == "EZRapLyrics":
        return {
            "sample": "Lyrics sample",
            "lyrics": "Lyrics",
            "enhance": "Rewrite lyrics",
        }.get(name, generic)
    if ntype == "EZPodcastScript":
        return {
            "sample": "Script sample",
            "prompt": "Script",
            "enhance": "Rewrite script",
        }.get(name, generic)
    if ntype == "EZPodcastLearn":
        return {
            "sample": "Sample prompt",
            "sources": "Sources",
            "format": "Format",
            "duration": "Duration",
            "fetch_links": "Fetch links",
            "enhance": "Rewrite",
        }.get(name, generic)
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
            "cfg_weight": "Clone CFG",
            "exaggeration": "Exaggeration",
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
        elif "vocal" in title_l:
            kind = "Vocal"
        elif "instrumental" in title_l:
            kind = "Instrumental"
        if kind:
            return {
                "sample": f"{kind} sample",
                "tags": f"{kind} tags",
                "lyrics": f"{kind} lyrics",
                "enhance": f"Rewrite {kind.lower()}",
                "mode": f"{kind} mode",
            }.get(name, generic)
        if name == "sample":
            return "Sample prompt"
        if name == "mode":
            return "Vocal / instrumental"
    if collide and ntype in ENHANCE_TYPES:
        family = None
        for token in ("Klein", "Wan", "LTX", "Z-Image", "LongCat", "DreamX"):
            if token.lower() in title_l:
                family = token
                break
        if family:
            return {
                "sample": f"{family} sample",
                "prompt": f"{family} prompt",
                "style": f"{family} style",
                "enhance": f"Rewrite {family}",
                "mode": f"{family} mode",
                "duration_hint": f"{family} duration / framing",
                "audio_notes": f"{family} audio notes",
            }.get(name, generic)
        if title:
            return f"{title} — {generic}"
    if collide and name == "sample" and title:
        return f"{title} — Sample prompt"
    if collide and title:
        return f"{title} — {generic}"
    return generic


def widget_description(name: str, node: Mapping[str, Any] | None = None) -> str | None:
    """Help text for one App Mode widget."""
    ntype = (node or {}).get("type")
    if ntype == "EZAudioRack":
        return {
            "brief": (
                "Optional lyrics seed. Ignored on instrumental and podcast-bed "
                "flavors so ACE does not sing free text."
            ),
            "recipe": (
                "Named splice that fills empty axes only. Explicit dropdowns win."
            ),
            "flavor": (
                "ace_vocal / ace_instrumental / podcast_bed. Instrumental omits "
                "vocal identity and forces no-vocals tags."
            ),
            "genre_style": "Genre-first ACE tags. Catalog under generated/audio.",
            "tempo_groove": "Pocket and BPM token. Match the ACE encoder BPM.",
            "drums_rhythm": "Kit, hats, and groove language.",
            "bass_low_end": "Upright, 808, sub, walking.",
            "harmony_mode": "Mode and harmonic color in tags, not ACE keyscale.",
            "instruments_texture": "Specific instruments and timbre.",
            "vocal_identity": "One vocal identity. Omitted on instrumental/podcast.",
            "arrangement_form": "Lyrics skeleton. Instrumental uses [inst]/[drop].",
            "mix_production": "Vinyl dirt, dry booth, club loudness, duck.",
            "space_ambience": "Booth dry, hall, mono drums, width.",
            "sound_design_fx": "Tape stop, riser, reverse cymbal. Bed-safe skips drops.",
            "mood_energy": "Menace, laid-back, civic-serious, triumphant.",
            "use_case": "Draft, album take, 30 s bed, bumper, sting.",
        }.get(name)
    if ntype == "EZCreativeResearch":
        return {
            "prompt": "Question or note for the creative-process desk.",
            "mode": "chat is one turn. research runs planner + search subagents.",
            "web_search": (
                "On: Wikipedia + DuckDuckGo snippets. Off: on-box GGUF only."
            ),
            "subagents": "Planner search count (1–3). Sequential CPU workers.",
            "history": (
                "Optional prior turns. One Queue per message — not a streaming chat."
            ),
        }.get(name)
    if ntype == "EZAppForge":
        return {
            "prompt": "What the new App should make. Template auto picks a lab graph.",
            "template": "auto picks a shipped lab graph. Pin a lab_rel to skip the picker.",
            "slug": "Live _user filename stem. Lowercase letters, digits, hyphen.",
            "as_app": "On: write *.app.json for the Apps sidebar. Off: graph-only *.json.",
            "overwrite": "On: replace an existing _user file with this slug.",
        }.get(name)
    if name == "mode" and ntype == "EZAceStepPromptEnhance":
        return (
            "Vocal vs instrumental. Instrumental forces no-vocals tags and "
            "[inst] lyrics."
        )
    if name == "seconds" and ntype == "EmptyAceStep1.5LatentAudio":
        return "Bed or sting length in seconds."
    if ntype == "EZImageFormat":
        return {
            "format": (
                "Aspect or named platform job. Sets pixels, save prefix, and "
                "Rewrite prompt framing. Custom uses Width × Height (÷16)."
            ),
            "look": (
                "Optional Cinema Rack starter. none leaves look to Style + Prompt. "
                "Full 13-axis desk is inspire/cinema-rack."
            ),
            "width": "Latent width in pixels. Used when Format is Custom; otherwise the preset wins.",
            "height": "Latent height in pixels. Used when Format is Custom; otherwise the preset wins.",
            "batch_size": "How many stills in one Run. Large canvases stay at 1.",
        }.get(name)
    if ntype == "EZVideoFormat":
        return {
            "format": (
                "Aspect or named platform job. Sets clip width and height on the "
                "Wan ÷16 or LTX ÷32 grid. Custom uses Width × Height. Length stays "
                "on the latent node."
            ),
            "width": "Latent width in pixels. Used when Format is Custom; otherwise the preset wins.",
            "height": "Latent height in pixels. Used when Format is Custom; otherwise the preset wins.",
        }.get(name)
    if name == "prompt" and ntype == "EZKleinPromptEnhance" and node is not None:
        if _enhance_mode(node) == "text_swap":
            return (
                "Replacement lettering, or Replace SALE with OPEN. "
                "Rewrite prompt expands this into a glyph-lock instruction."
            )
    if name == "prompt" and ntype == "EZPodcastScript":
        return "Speaker A/B lines. Disclosure prepends the spoken bumper."
    if ntype == "EZPodcastLearn":
        return {
            "sources": (
                "Paste notes, HTTPS links, captioned video URLs, or local "
                ".txt/.md/.srt/.vtt paths. Custom keeps this box."
            ),
            "format": (
                "Quick recap, deep dive, explainer, quiz, solo lecture, or debate."
            ),
            "duration": (
                "Spoken length. 8 min briefing is the default. 25 min is slow CPU TTS. "
                "ACE bed stays 30 s and loops under the speech."
            ),
            "fetch_links": (
                "On: HTTPS pages + video captions (no media download). "
                "Off: pasted prose and local text files only."
            ),
            "enhance": (
                "On: digest + script from the on-box GGUF. Off: concatenate sources "
                "and wrap Speaker A lines."
            ),
        }.get(name)
    if name == "prompt" and ntype == "EZDubScript":
        return "Editable turns JSON. Rewrite translation fills text_target."
    if name == "enhance" and ntype == "EZDubScript":
        return "On: diarize + ASR + GGUF translate. Off: pin this JSON."
    if ntype == "PrimitiveNode" and name == "value":
        title = str((node or {}).get("title") or "")
        if title == "Prompt":
            return "Lazy sentence. All three family rewriters read this."
        if title == "Context":
            return "Optional research brief or bible. Empty is fine."
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
    if name == "value" and str((node or {}).get("title") or "") == "Prompt":
        height = WIDGET_HEIGHTS.get("prompt")
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
    cinema_widgets: bool = False,
    audio_widgets: bool = False,
    research_widgets: bool = False,
    app_forge_widgets: bool = False,
    primitive_strings: bool = False,
    hide_images: bool = False,
    ace_instrumental_score: bool = False,
    expose_look: bool = False,
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
        "cinema_widgets": cinema_widgets,
        "audio_widgets": audio_widgets,
        "research_widgets": research_widgets,
        "app_forge_widgets": app_forge_widgets,
        "primitive_strings": primitive_strings,
        "hide_images": hide_images,
        "ace_instrumental_score": ace_instrumental_score,
        "expose_look": expose_look,
    }


STAMP_SPECS: dict[str, dict[str, Any]] = {
    "klein/still-draft": _spec(
        "inspire",
        "klein",
        "klein/still-hero",
        "wan/still-to-video-5s",
        "klein/platform-pack",
    ),
    "klein/identity-sheet": _spec(
        "inspire", "klein"
    ),
    "klein/storyboard-6up": _spec(
        "inspire",
        "klein",
        "wan/still-to-shot",
        "ltx/still-to-shot",
    ),
    "klein/dream-house": _spec(
        "inspire",
        "klein",
        "wan/gif-loop",
        "wan/bumper-loop",
        "wan/sticker-loop",
    ),
    "klein/dream-house-clay": _spec(
        "inspire",
        "klein",
        "wan/gif-loop",
        "wan/bumper-loop",
        "wan/sticker-loop",
        hide_images=True,
    ),
    "klein/style-lock": _spec(
        "inspire", "klein"
    ),
    "klein/lighting-trio": _spec("inspire", "klein"),
    "klein/camera-angles": _spec("inspire", "klein"),
    "klein/color-moods": _spec("inspire", "klein"),
    "klein/time-of-day": _spec("inspire", "klein"),
    "klein/hook-still": _spec(
        "inspire", "klein", "wan/shorts-still-5s"
    ),
    "klein/character-draft": _spec(
        "inspire",
        "klein",
        "klein/character-tweak",
        "klein/identity-sheet",
        "wan/still-to-video-5s",
    ),
    "klein/character-tweak": _spec(
        "inspire",
        "klein",
        "klein/identity-sheet",
        "wan/still-to-video-5s",
    ),
    "inspire/prompt-forge": _spec(
        "inspire",
        "llm",
        "klein/still-draft",
        forge_widgets=True,
    ),
    "inspire/cinema-rack": _spec(
        "inspire",
        "llm",
        "inspire/prompt-forge",
        "klein/still-draft",
        cinema_widgets=True,
    ),
    "inspire/audio-rack": _spec(
        "inspire",
        "llm",
        "audio/music/rap-draft",
        "audio/podcast/learn-episode",
        audio_widgets=True,
    ),
    "inspire/research-chat": _spec(
        "inspire",
        "llm",
        "inspire/prompt-forge",
        "klein/still-draft",
        research_widgets=True,
    ),
    "inspire/app-forge": _spec(
        "inspire",
        "llm",
        "inspire/prompt-forge",
        "klein/still-draft",
        app_forge_widgets=True,
    ),
    "inspire/beat-sheet": _spec(
        "inspire",
        "none",
        "klein/identity-sheet",
        "dcc/klein/clay-hero",
        "shorts/go-see",
        primitive_strings=True,
    ),
    "klein/still-daily": _spec(
        "produce",
        "klein",
        expose_unet=True,
        sampler_steps_cfg=True,
    ),
    "klein/still-studio": _spec(
        "produce",
        "klein",
        "wan/still-to-video-5s",
        "ltx/still-to-video-5s",
        "klein/text-swap",
        expose_unet=True,
        expose_look=True,
    ),
    "klein/still-hero": _spec(
        "produce",
        "klein",
        "wan/still-to-video-5s",
        "ltx/still-to-video-5s",
        "ltx/first-last-5s",
    ),
    "klein/thumbnail": _spec("produce", "klein"),
    "klein/text-swap": _spec(
        "produce",
        "klein",
        "wan/still-to-video-5s",
    ),
    "klein/product-packshot": _spec("produce", "klein", "ltx/product-hero"),
    "klein/instagram-square": _spec("produce", "klein"),
    "klein/open-graph": _spec("produce", "klein"),
    "klein/banner-wide": _spec("produce", "klein"),
    "klein/podcast-cover": _spec("produce", "klein"),
    "klein/endcard-cta": _spec("produce", "klein"),
    "klein/quote-bg": _spec("produce", "klein"),
    "klein/lower-third-bg": _spec("produce", "klein"),
    "klein/food-tabletop": _spec("produce", "klein"),
    "klein/shorts-still": _spec("produce", "klein"),
    "klein/before-after": _spec("produce", "klein"),
    "klein/platform-pack": _spec(
        "produce",
        "klein",
        "wan/still-to-video-5s",
        "ltx/hook-av",
    ),
    "klein/talking-head": _spec("produce", "ltx", "ltx/audio-to-video-5s"),
    "wan/still-to-video-5s": _spec(
        "produce", "wan", "ltx/still-to-video-5s"
    ),
    "wan/text-to-video-5s": _spec("produce", "wan"),
    "wan/first-last-5s": _spec("produce", "wan"),
    "wan/vace-join": _spec("produce", "wan"),
    "wan/still-to-shot": _spec("produce", "wan"),
    "wan/gif-loop": _spec("produce", "wan"),
    "wan/bumper-loop": _spec("produce", "wan"),
    "wan/sticker-loop": _spec("produce", "wan"),
    "wan/shorts-still-5s": _spec(
        "produce", "wan", "ltx/shorts-still-5s"
    ),
    "wan/orbit-still-5s": _spec("produce", "wan"),
    "wan/push-in-still-5s": _spec("produce", "wan"),
    "wan/parallax-still-5s": _spec("produce", "wan"),
    "ltx/still-to-video-5s": _spec("produce", "ltx"),
    "ltx/text-to-video-5s": _spec("produce", "ltx"),
    "ltx/still-to-shot": _spec("produce", "ltx"),
    "ltx/shorts-still-5s": _spec("produce", "ltx"),
    "ltx/hook-av": _spec("produce", "ltx"),
    "ltx/broll-ambient": _spec("produce", "ltx"),
    "ltx/weather-broll": _spec("produce", "ltx"),
    "ltx/interior-ambience": _spec("produce", "ltx"),
    "ltx/dialogue-5s": _spec("produce", "ltx"),
    "ltx/multishot-5s": _spec("produce", "ltx"),
    "ltx/product-hero": _spec("produce", "ltx"),
    "ltx/first-last-5s": _spec("produce", "ltx"),
    "ltx/audio-to-video-5s": _spec("produce", "ltx"),
    "shorts/go-see": _spec(
        "film",
        "film",
        default_view="graph",
        film_minimal=True,
        enhance_off_identity=True,
    ),
    "shorts/still-here": _spec(
        "film",
        "film",
        default_view="graph",
        film_minimal=True,
        enhance_off_identity=True,
    ),
    "shorts/switchyard": _spec(
        "film",
        "film",
        default_view="graph",
        film_minimal=True,
        enhance_off_identity=True,
    ),
    **{
        f"shorts/{film}/act-0{act}": _spec(
            "film",
            "film",
            default_view="graph",
            film_minimal=True,
            enhance_off_identity=True,
        )
        for film in (
            "tide-table",
            "night-oven",
            "glasshouse",
            "last-lane",
            "breakwater",
        )
        for act in range(1, 6)
    },
    "audio/podcast/two-host-episode": _spec("audio", "audio"),
    "audio/podcast/radio-drama": _spec("audio", "audio"),
    "audio/podcast/learn-episode": _spec("audio", "audio"),
    "audio/dub/clone-translate": _spec("audio", "audio"),
    "audio/music/rap-draft": _spec("audio", "audio"),
    "audio/music/rap-full": _spec("audio", "audio"),
    "dcc/klein/clay-hero": _spec(
        "dcc",
        "klein",
        "dcc/ltx/depth-control-5s",
        "wan/still-to-video-5s",
    ),
    "dcc/klein/canny-hero": _spec(
        "dcc",
        "klein",
        "dcc/ltx/canny-control-5s",
    ),
    "dcc/klein/clay-plates": _spec(
        "dcc",
        "klein",
        "wan/still-to-video-5s",
        "wan/shorts-still-5s",
        "dcc/ltx/depth-control-shorts",
    ),
    "dcc/ltx/depth-control-5s": _spec(
        "dcc",
        "ltx",
        "audio/stem-mix",
    ),
    "dcc/ltx/canny-control-5s": _spec(
        "dcc",
        "ltx",
        "audio/stem-mix",
    ),
    "dcc/ltx/depth-control-shorts": _spec(
        "dcc",
        "ltx",
        "audio/stem-mix",
    ),
    "dcc/wan/first-last-from-guide": _spec(
        "dcc",
        "wan",
        "dcc/ltx/depth-control-5s",
    ),
    "dcc/klein/guide-still": _spec(
        "dcc",
        "klein",
        "dcc/ltx/depth-from-loader",
        "dcc/trellis/still-to-mesh",
    ),
    "dcc/ltx/depth-from-loader": _spec(
        "dcc",
        "ltx",
        "audio/stem-mix",
    ),
    "dcc/trellis/still-to-mesh": _spec(
        "dcc",
        "trellis",
        default_view="graph",
    ),
    "audio/stem-mix": _spec(
        "audio",
        "audio",
        primitive_strings=True,
    ),
    "optional/wan/still-to-video-a14b": _spec("produce", "wan", default_view="graph"),
}

def _nill_bye_stems() -> tuple[str, ...]:
    import sys
    from pathlib import Path

    custom = Path(__file__).resolve().parents[2] / "custom_nodes"
    if str(custom) not in sys.path:
        sys.path.insert(0, str(custom))
    from ez_music.diss_examples import DISS_EXAMPLES

    return tuple(ex["rel"] for ex in DISS_EXAMPLES)


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

    return tuple(ex["rel"] for ex in EDM_EXAMPLES)


DRIVE_THROUGH_STAMP_STEMS = _drive_through_stems()
for _drive_through_stem in DRIVE_THROUGH_STAMP_STEMS:
    STAMP_SPECS[_drive_through_stem] = _spec(
        "audio", "audio", ace_instrumental_score=True
    )

STUB_IDS = frozenset({"optional/longcat-video"})
OPTIONAL_UNWIRED: dict[str, tuple[str, ...]] = {
    "dcc/ltx/depth-control-5s": ("EZFilmDisclosure",),
    "dcc/ltx/canny-control-5s": ("EZFilmDisclosure",),
    "dcc/ltx/depth-control-shorts": ("EZFilmDisclosure",),
    "dcc/ltx/depth-from-loader": (
        "EZFilmDisclosure",
        "EZDCCLoadGuideVideo",
    ),
    "audio/stem-mix": ("SaveAudio", "PrimitiveNode"),
    "optional/wan/still-to-video-a14b": ("UNETLoader",),
    "audio/podcast/radio-drama": ("UNETLoader", "VHS_VideoCombine"),
    "inspire/prompt-forge": (
        "EZKleinPromptEnhance",
        "EZWanPromptEnhance",
        "EZLTXPromptEnhance",
        "EZZimagePromptEnhance",
        "EZLongCatPromptEnhance",
        "EZDreamXPromptEnhance",
    ),
    "inspire/cinema-rack": (
        "EZKleinPromptEnhance",
        "EZWanPromptEnhance",
        "EZLTXPromptEnhance",
    ),
    "inspire/audio-rack": (
        "EZAceStepPromptEnhance",
    ),
    "inspire/research-chat": ("EZCreativeResearch",),
    "inspire/app-forge": ("EZAppForge",),
    "wan/first-last-5s": ("LoadImage",),
    "wan/vace-join": ("LoadImage",),
}


def _migrate_stamp_keys() -> None:
    """Rewrite STAMP_SPECS / stubs from *-lab-example stems to lab-relative ids."""
    from _lab_ids import rel_id

    converted: dict[str, dict[str, Any]] = {}
    for key, spec in STAMP_SPECS.items():
        new_key = rel_id(key)
        handoff = tuple(rel_id(str(item)) for item in spec.get("handoff") or ())
        converted[new_key] = {**spec, "handoff": handoff}
    STAMP_SPECS.clear()
    STAMP_SPECS.update(converted)
    global STUB_IDS, OPTIONAL_UNWIRED
    STUB_IDS = frozenset(rel_id(item) for item in STUB_IDS)
    OPTIONAL_UNWIRED = {rel_id(key): value for key, value in OPTIONAL_UNWIRED.items()}


_migrate_stamp_keys()


def _register_album_stamps() -> None:
    import sys
    from pathlib import Path

    custom = Path(__file__).resolve().parents[2] / "custom_nodes"
    if str(custom) not in sys.path:
        sys.path.insert(0, str(custom))
    from ez_music.albums import album_rel, shipped_albums

    for info in shipped_albums():
        cover = album_rel(info["artist_slug"], info["slug"], "cover")
        album = album_rel(info["artist_slug"], info["slug"], "album")
        STAMP_SPECS[cover] = _spec("produce", "klein")
        STAMP_SPECS[album] = _spec("audio", "none")


_register_album_stamps()


def _register_pack3_stamps() -> None:
    from _creator_pack3 import pack3_stamp_rows

    for rel, occupancy, handoff, pin in pack3_stamp_rows():
        STAMP_SPECS[rel] = _spec(
            "produce",
            occupancy,
            *handoff,
            enhance_off_identity=pin,
        )


_register_pack3_stamps()


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


def _collect_film_minimal(
    graph: dict, hide_sample: bool
) -> list[tuple[NodeRef, str, dict]]:
    raw: list[tuple[NodeRef, str, dict]] = []
    for node in graph.get("nodes") or []:
        if node.get("type") == "EZKleinPromptEnhance":
            nid = node["id"]
            if not hide_sample:
                raw.append((nid, "sample", node))
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


def _collect_primitive_strings(
    graph: dict, hide_sample: bool
) -> list[tuple[NodeRef, str, dict]]:
    raw: list[tuple[NodeRef, str, dict]] = []
    for node in graph.get("nodes") or []:
        if node.get("type") == "EZSamplePrompt":
            nid = node["id"]
            if not hide_sample:
                raw.append((nid, "sample", node))
            raw.append((nid, "prompt", node))
        elif node.get("type") == "PrimitiveNode":
            raw.append((node["id"], "value", node))
    return raw


def _collect_cinema_widgets(graph: dict) -> list[tuple[NodeRef, str, dict]]:
    raw: list[tuple[NodeRef, str, dict]] = []
    axis_names = (
        "framing_shot_size",
        "camera_angles",
        "camera_movement",
        "lenses_optics",
        "composition",
        "lighting",
        "color_film_look",
        "time_motion",
        "in_camera_optical",
        "editing_transitions",
        "atmosphere_weather",
        "genre_looks",
        "viral_looks",
    )
    for node in graph.get("nodes") or []:
        if node.get("type") != "EZCinemaRack":
            continue
        nid = node["id"]
        raw.append((nid, "subject", node))
        raw.append((nid, "recipe", node))
        raw.append((nid, "flavor", node))
        for axis_id in axis_names:
            raw.append((nid, axis_id, node))
    for node in graph.get("nodes") or []:
        ntype = node.get("type")
        nid = node["id"]
        if ntype not in (
            "EZKleinPromptEnhance",
            "EZWanPromptEnhance",
            "EZLTXPromptEnhance",
        ):
            continue
        raw.extend(
            (
                (nid, "style", node),
                (nid, "enhance", node),
            )
        )
        if ntype == "EZLTXPromptEnhance":
            raw.append((nid, "audio_notes", node))
    return raw


def _collect_audio_widgets(graph: dict) -> list[tuple[NodeRef, str, dict]]:
    raw: list[tuple[NodeRef, str, dict]] = []
    axis_names = (
        "genre_style",
        "tempo_groove",
        "drums_rhythm",
        "bass_low_end",
        "harmony_mode",
        "instruments_texture",
        "vocal_identity",
        "arrangement_form",
        "mix_production",
        "space_ambience",
        "sound_design_fx",
        "mood_energy",
        "use_case",
    )
    for node in graph.get("nodes") or []:
        if node.get("type") != "EZAudioRack":
            continue
        nid = node["id"]
        raw.append((nid, "brief", node))
        raw.append((nid, "recipe", node))
        raw.append((nid, "flavor", node))
        for axis_id in axis_names:
            raw.append((nid, axis_id, node))
    for node in graph.get("nodes") or []:
        if node.get("type") != "EZAceStepPromptEnhance":
            continue
        nid = node["id"]
        raw.append((nid, "enhance", node))
    return raw


def _collect_forge_widgets(
    graph: dict, hide_sample: bool
) -> list[tuple[NodeRef, str, dict]]:
    raw: list[tuple[NodeRef, str, dict]] = []
    for node in graph.get("nodes") or []:
        if node.get("type") == "EZSamplePrompt":
            nid = node["id"]
            if not hide_sample:
                raw.append((nid, "sample", node))
            raw.append((nid, "prompt", node))
        elif node.get("type") == "PrimitiveNode":
            raw.append((node["id"], "value", node))
    for node in graph.get("nodes") or []:
        ntype = node.get("type")
        nid = node["id"]
        if ntype not in (
            "EZKleinPromptEnhance",
            "EZWanPromptEnhance",
            "EZLTXPromptEnhance",
            "EZZimagePromptEnhance",
            "EZLongCatPromptEnhance",
            "EZDreamXPromptEnhance",
        ):
            continue
        raw.extend(
            (
                (nid, "style", node),
                (nid, "enhance", node),
            )
        )
        if ntype in ("EZLTXPromptEnhance", "EZDreamXPromptEnhance"):
            raw.append((nid, "audio_notes", node))
    return raw


def _collect_research_widgets(
    graph: dict, hide_sample: bool
) -> list[tuple[NodeRef, str, dict]]:
    raw: list[tuple[NodeRef, str, dict]] = []
    for node in graph.get("nodes") or []:
        if node.get("type") == "EZCreativeResearch":
            nid = node["id"]
            if not hide_sample:
                raw.append((nid, "sample", node))
            raw.extend(
                (
                    (nid, "prompt", node),
                    (nid, "mode", node),
                    (nid, "web_search", node),
                    (nid, "subagents", node),
                    (nid, "history", node),
                )
            )
    return raw


def _collect_app_forge_widgets(
    graph: dict, hide_sample: bool
) -> list[tuple[NodeRef, str, dict]]:
    raw: list[tuple[NodeRef, str, dict]] = []
    for node in graph.get("nodes") or []:
        if node.get("type") == "EZAppForge":
            nid = node["id"]
            if not hide_sample:
                raw.append((nid, "sample", node))
            raw.extend(
                (
                    (nid, "prompt", node),
                    (nid, "template", node),
                    (nid, "slug", node),
                    (nid, "as_app", node),
                    (nid, "overwrite", node),
                )
            )
    return raw


def _collect_raw_inputs(
    graph: dict, spec: Mapping[str, Any]
) -> list[tuple[NodeRef, str, dict]]:
    """(node id, widget name, node) in graph order. No labels yet."""
    raw: list[tuple[NodeRef, str, dict]] = []
    hide_sample = _graph_hides_sample(graph)
    if spec.get("film_minimal"):
        return _collect_film_minimal(graph, hide_sample)

    if spec.get("primitive_strings"):
        return _collect_primitive_strings(graph, hide_sample)

    if spec.get("cinema_widgets"):
        return _collect_cinema_widgets(graph)

    if spec.get("audio_widgets"):
        return _collect_audio_widgets(graph)

    if spec.get("forge_widgets"):
        return _collect_forge_widgets(graph, hide_sample)

    if spec.get("research_widgets"):
        return _collect_research_widgets(graph, hide_sample)

    if spec.get("app_forge_widgets"):
        return _collect_app_forge_widgets(graph, hide_sample)

    saw_seed = False
    saw_primary_enhance = False
    for node in graph.get("nodes") or []:
        ntype = node.get("type")
        nid = node["id"]
        if ntype == "EZAceStepPromptEnhance":
            has_rap = any(
                other.get("type") == "EZRapLyrics" for other in graph.get("nodes") or []
            )
            has_learn = any(
                other.get("type") == "EZPodcastLearn"
                for other in graph.get("nodes") or []
            )
            mode = _enhance_mode(node)
            show_score = mode != "instrumental" or spec.get("ace_instrumental_score")
            if not hide_sample and not has_learn:
                raw.append((nid, "sample", node))
            raw.append((nid, "tags", node))
            if show_score and not has_rap:
                raw.append((nid, "lyrics", node))
            if not has_rap and not has_learn:
                raw.append((nid, "enhance", node))
            if show_score:
                raw.append((nid, "mode", node))
        elif ntype in ("EZRapLyrics", "EZPodcastScript"):
            widget = "lyrics" if ntype == "EZRapLyrics" else "prompt"
            if not hide_sample:
                raw.append((nid, "sample", node))
            raw.extend(
                (
                    (nid, widget, node),
                    (nid, "enhance", node),
                )
            )
        elif ntype == "EZPodcastLearn":
            if not hide_sample:
                raw.append((nid, "sample", node))
            raw.extend(
                (
                    (nid, "sources", node),
                    (nid, "format", node),
                    (nid, "duration", node),
                    (nid, "fetch_links", node),
                    (nid, "enhance", node),
                )
            )
        elif ntype == "EZSamplePrompt":
            if not hide_sample:
                raw.append((nid, "sample", node))
            raw.append((nid, "prompt", node))
        elif ntype in ENHANCE_TYPES:
            if not spec.get("forge_widgets") and saw_primary_enhance:
                continue
            saw_primary_enhance = True
            mode = _enhance_mode(node)
            skip_style = (not spec.get("forge_widgets")) and mode in STYLE_IGNORED_MODES
            if not hide_sample:
                raw.append((nid, "sample", node))
            raw.append((nid, "prompt", node))
            if not skip_style:
                raw.append((nid, "style", node))
            raw.append((nid, "enhance", node))
            if ntype in ("EZLTXPromptEnhance", "EZDreamXPromptEnhance"):
                raw.append((nid, "audio_notes", node))
        elif ntype == "EZImageFormat":
            raw.append((nid, "format", node))
            if spec.get("expose_look"):
                raw.append((nid, "look", node))
            raw.extend(
                (
                    (nid, "width", node),
                    (nid, "height", node),
                    (nid, "batch_size", node),
                )
            )
        elif ntype == "EZVideoFormat":
            raw.extend(
                (
                    (nid, "format", node),
                    (nid, "width", node),
                    (nid, "height", node),
                )
            )
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
        elif ntype == "EZDCCLoadGuideStill":
            raw.extend(
                (
                    (nid, "slug", node),
                    (nid, "shot_id", node),
                    (nid, "layer", node),
                )
            )
        elif ntype == "EZDCCLoadStillPack":
            raw.extend(
                (
                    (nid, "slug", node),
                    (nid, "plate", node),
                    (nid, "layer", node),
                )
            )
        elif ntype == "EZDCCOccupancyGate":
            raw.append((nid, "required_mode", node))
        elif ntype == "LoadImage":
            if spec.get("hide_images"):
                continue
            if _node_always(node) and _image_output_linked(node):
                raw.append((nid, "image", node))
        elif ntype == "LoadAudio":
            if _node_always(node) and _audio_output_linked(node):
                raw.append((nid, "audio", node))
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
                    (nid, "cfg_weight", node),
                    (nid, "exaggeration", node),
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
        elif ntype == "EZAudioMetadata":
            raw.extend(
                (
                    (nid, "artist", node),
                    (nid, "album", node),
                    (nid, "title", node),
                    (nid, "track", node),
                    (nid, "tracktotal", node),
                    (nid, "year", node),
                    (nid, "art_mode", node),
                )
            )
        elif ntype == "EZAlbumPack":
            raw.extend(
                (
                    (nid, "artist", node),
                    (nid, "album", node),
                )
            )
        elif ntype == "EmptyAceStep1.5LatentAudio":
            has_learn = any(
                other.get("type") == "EZPodcastLearn"
                for other in graph.get("nodes") or []
            )
            if not has_learn and not _input_linked(node, "seconds"):
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


def _quality_input_specs(graph: dict, spec: Mapping[str, Any]) -> list[InputSpec]:
    """App Mode Quality combo, when EZQuality is on the graph."""
    specs: list[InputSpec] = []
    for node in graph.get("nodes") or []:
        if node.get("type") != "EZQuality":
            continue
        specs.append(_input_spec(node["id"], "quality", spec, node=node))
    return specs


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
    quality = _quality_input_specs(graph, spec)
    if quality:
        inputs = quality + [item for item in inputs if _parse_input(item)[1] != "quality"]
    if spec.get("research_widgets") or spec.get("app_forge_widgets"):
        return inputs
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
    if spec.get("research_widgets"):
        return [
            int(node["id"])
            for node in graph.get("nodes") or []
            if node.get("type") == "EZCreativeResearch"
        ]
    if spec.get("app_forge_widgets"):
        return [
            int(node["id"])
            for node in graph.get("nodes") or []
            if node.get("type") == "EZAppForge"
        ]
    if spec.get("forge_widgets") or spec.get("cinema_widgets") or spec.get(
        "audio_widgets"
    ):
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
    from _wire_quality import ensure_quality_node

    ensure_quality_node(graph)
    extra = graph.setdefault("extra", {})
    gid = str((graph.get("extra") or {}).get("lab_rel") or graph.get("id") or "")
    from _lab_ids import rel_id

    gid = rel_id(gid)
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
    from _lab_ids import rel_id
    from _wire_quality import ensure_quality_node

    ensure_quality_node(graph)
    extra = graph.get("extra") or {}
    key = rel_id(str(extra.get("lab_rel") or graph.get("id") or ""))
    spec = STAMP_SPECS.get(key)
    if spec is None:
        spec = STAMP_SPECS.get(str(graph.get("id") or ""))
    if spec is None:
        from _wire_prompt_enhance import apply_enhance_policy, normalize_enhance_widgets

        normalize_enhance_widgets(graph)
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
    from _wire_prompt_enhance import apply_enhance_policy, normalize_enhance_widgets

    normalize_enhance_widgets(graph)
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


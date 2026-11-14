"""Hermetic tests for the Detail ladder: presets, node, stamp, and JS mirror.

``custom_nodes/ez_quality/presets.py`` is the one definition of what each rung
asks for, so every expectation here is read off that module or off the table it
generates - no step count, CFG, or weight filename is hardcoded from prose. The
contract this file pins: three selectable rungs (``draft`` / ``standard`` /
``final``, default ``standard``); retired tier ids stay accepted input and
normalize onto a rung; ``standard`` writes nothing on every family; a named rung
is write-or-refuse; a rung never changes size, never leaves its own family, and
never reaches a Klein 9B or FLUX.2-dev weight; the caption is derived from the
live widgets; and the frontend reads a table generated from this module rather
than keeping numbers of its own.

The per-graph stamping checks are the same invariant ``_wire_quality`` stamps:
one Detail node where a rung can write, none where none can.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import _build_quality_js
from _lab_paths import lab_graph_paths, lab_json
from _wire_quality import (
    QUALITY_TITLE,
    QUALITY_TYPE,
    QUALITY_WIDGET,
    ensure_quality_node,
    family_honors_tiers,
    find_quality_node,
    strip_quality_node,
)

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_quality import nodes as quality_nodes  # noqa: E402
from ez_quality.check import (  # noqa: E402
    hints_from_args,
    requirements_for,
    run_check,
    rung_family,
    rung_needs,
)
from ez_quality.nodes import EZQuality  # noqa: E402
from ez_quality.presets import (  # noqa: E402
    AUDIO_DRAFT_STEPS,
    AUDIO_FINAL_STEPS,
    BANNED_UNET_NEEDLES,
    CLIP_4B,
    CLIP_8B,
    CLIP_MISTRAL,
    CLIP_NAME_INDEX,
    CLIP_TYPE_FLUX2,
    EDITED_PREFIX,
    FIELD_WIDGET_NAMES,
    FLUX2_DEV,
    FLUX3_QUALITY_CHOICES,
    KLEIN3_DISTILLED,
    KLEIN3_DRAFT_CFG,
    KLEIN3_DRAFT_STEPS,
    KLEIN3_FINAL_CFG,
    KLEIN3_FINAL_STEPS,
    KLEIN3_NVFP4,
    KLEIN3_TE,
    KLEIN_9B,
    KLEIN_9B_BASE,
    KLEIN_9B_NVFP4,
    KLEIN_BASE,
    KLEIN_DISTILLED,
    KLEIN_DRAFT_CFG,
    KLEIN_DRAFT_STEPS,
    KLEIN_FINAL_CFG,
    KLEIN_FINAL_STEPS,
    KLEIN_NVFP4,
    KSAMPLER_CFG_INDEX,
    KSAMPLER_STEPS_INDEX,
    LICENSE_LABEL,
    LTX_DRAFT_STEPS,
    LTX_FINAL_STEPS,
    LTX_UNET,
    NAMED_QUALITY_CHOICES,
    OVERLAY_FIELDS,
    OVERLAY_NODE_TYPES,
    QUALITY_CHOICES,
    QUALITY_CUSTOM,
    QUALITY_DEFAULT,
    QUALITY_DRAFT,
    QUALITY_FAMILIES,
    QUALITY_FAMILY_KLEIN3,
    QUALITY_FAMILY_QWEN,
    QUALITY_FINAL,
    QUALITY_FLUX3_FAST,
    QUALITY_FLUX3_NVFP4,
    QUALITY_FLUX3_QUALITY,
    QUALITY_FREE_COMMERCIAL,
    QUALITY_FREE_COMMERCIAL_ALIAS,
    QUALITY_HIGH,
    QUALITY_LAB,
    QUALITY_MAX,
    QUALITY_QWEN_IMAGE,
    QUALITY_QWEN_IMAGE_NVFP4,
    QUALITY_QWEN_IMAGE_TURBO,
    QUALITY_QWEN_IMAGE_TURBO_NVFP4,
    QUALITY_STANDARD,
    QUALITY_ULTRA,
    QWEN_DRAFT_CFG,
    QWEN_DRAFT_STEPS,
    QWEN_FINAL_CFG,
    QWEN_FINAL_STEPS,
    QWEN_IMAGE_INT8,
    QWEN_IMAGE_NVFP4,
    QWEN_IMAGE_TURBO_INT8,
    QWEN_IMAGE_TURBO_NVFP4,
    QWEN_QUALITY_CHOICES,
    QWEN_TE,
    QWEN_VAE,
    RUNG_LABEL,
    STACK_LABEL,
    TRELLIS_DRAFT_STEPS,
    TRELLIS_FINAL_STEPS,
    TRELLIS_GUIDANCE_FREE_CFG,
    TRELLIS_UNET,
    UNET_NAME_INDEX,
    UNET_STACK_LABEL,
    VAE_FULL,
    VAE_NAME_INDEX,
    VAE_SMALL,
    WAN_DRAFT_STEPS,
    WAN_FINAL_STEPS,
    WAN_5B_UNET,
    _pick_unet,
    _RUNG_ROWS,
    _stack_text,
    apply_to_graph,
    caption_for,
    export_table,
    family_for,
    family_owned_fields,
    graph_family,
    graph_has_wan14,
    infer_occupancy,
    is_banned_unet,
    is_flux2_clip,
    is_flux2_dev_unet,
    is_flux2_vae,
    is_klein3_clip,
    is_klein3_unet,
    is_klein3_upsampler,
    is_klein_4b_unet,
    is_klein_9b_unet,
    is_qwen_image_clip,
    is_qwen_image_unet,
    is_qwen_image_vae,
    is_trellis_guidance_free_stage,
    is_wan_14b_unet,
    normalize_quality,
    plan_rung_writes,
    resolve_overlay,
    rung_label,
    rung_refusal_reasons,
    tier_is_honored,
    tier_label,
    tier_profile,
    tiers_for_family,
)

JS = CUSTOM / "ez_quality" / "js" / "ez_quality.js"
QUALITY_PRESETS_JS = CUSTOM / "ez_quality" / "js" / "ez_quality_presets.js"
MODEL_CHECK_JS = CUSTOM / "ez_quality" / "js" / "ez_model_check.js"

# The families a ladder exists for, in table order, and the ones that own no
# rung at all, whose row and node are stripped.
LADDER_FAMILIES: tuple[str, ...] = tuple(
    family for family in QUALITY_FAMILIES if family_owned_fields(family)
)
NO_RUNG_FAMILIES: tuple[str, ...] = tuple(
    family for family in QUALITY_FAMILIES if not family_owned_fields(family)
)

# Families whose rung writes steps and nothing else: no CFG, no weight.
STEPS_ONLY_FAMILIES: tuple[str, ...] = ("wan", "ltx", "film", "audio", "trellis")

# Every id the ladder retired: accepted input for the normalizer, never a
# selectable rung, never a value a graph records.
RETIRED_IDS: tuple[str, ...] = (
    QUALITY_LAB,
    QUALITY_CUSTOM,
    QUALITY_HIGH,
    QUALITY_FREE_COMMERCIAL,
    QUALITY_FREE_COMMERCIAL_ALIAS,
    QUALITY_ULTRA,
    QUALITY_MAX,
    *FLUX3_QUALITY_CHOICES,
    *QWEN_QUALITY_CHOICES,
)

# The contract's accepted-id table: each retired spelling and the rung it has to
# land on. Anything the table does not name (including "") lands on standard.
NORMALIZE_TABLE: tuple[tuple[str, str], ...] = (
    (QUALITY_DRAFT, QUALITY_DRAFT),
    (QUALITY_STANDARD, QUALITY_STANDARD),
    (QUALITY_FINAL, QUALITY_FINAL),
    (QUALITY_LAB, QUALITY_STANDARD),
    (QUALITY_CUSTOM, QUALITY_STANDARD),
    ("", QUALITY_STANDARD),
    (QUALITY_HIGH, QUALITY_FINAL),
    (QUALITY_ULTRA, QUALITY_FINAL),
    (QUALITY_MAX, QUALITY_FINAL),
    (QUALITY_FREE_COMMERCIAL, QUALITY_FINAL),
    (QUALITY_FREE_COMMERCIAL_ALIAS, QUALITY_FINAL),
    (QUALITY_FLUX3_FAST, QUALITY_DRAFT),
    (QUALITY_FLUX3_QUALITY, QUALITY_STANDARD),
    (QUALITY_FLUX3_NVFP4, QUALITY_FINAL),
    (QUALITY_QWEN_IMAGE, QUALITY_STANDARD),
    (QUALITY_QWEN_IMAGE_TURBO, QUALITY_DRAFT),
    (QUALITY_QWEN_IMAGE_NVFP4, QUALITY_FINAL),
    (QUALITY_QWEN_IMAGE_TURBO_NVFP4, QUALITY_DRAFT),
)

# Weights no rung may name on any family: the ladder stops at the App's own
# stack, and the detectors for these names stay only for the checker and the
# safety lane.
UNREACHABLE_WEIGHTS: frozenset[str] = frozenset(
    {KLEIN_9B, KLEIN_9B_BASE, KLEIN_9B_NVFP4, FLUX2_DEV, CLIP_8B, CLIP_MISTRAL}
)

# The loader fields a missing file can refuse an apply over; steps and CFG have
# no file behind them.
FILE_FIELDS: tuple[str, ...] = ("unet_name", "clip_name", "vae_name")

# A loader option list needs one file in it to be a real catalog: both sides
# read an empty list as "the catalog is unknown, skip the presence check".
_UNRELATED_FILE = "unrelated-weight.safetensors"

# A VAE that is a legal swap source but not what any rung asks for.
_KLEIN_OFF_RUNG_VAE = "flux2-vae-fp16.safetensors"

# One loader fixture per family: weights that classify the graph as that family
# while differing from every value its rungs request, so a rung write is always
# a real swap. Branch fixtures only; they never appear in a shipped graph.
_FAMILY_FIXTURES: dict[str, dict[str, str]] = {
    "klein": {
        "occupancy": "klein",
        "unet_name": KLEIN_DISTILLED,
        "clip_name": CLIP_MISTRAL,
        "vae_name": _KLEIN_OFF_RUNG_VAE,
    },
    QUALITY_FAMILY_KLEIN3: {
        "occupancy": "klein",
        "unet_name": KLEIN3_NVFP4,
        "clip_name": KLEIN3_TE,
        "vae_name": VAE_FULL,
    },
    QUALITY_FAMILY_QWEN: {
        "occupancy": "klein",
        "unet_name": QWEN_IMAGE_NVFP4,
        "clip_name": QWEN_TE,
        "vae_name": QWEN_VAE,
    },
    "wan": {"occupancy": "wan", "unet_name": WAN_5B_UNET, "clip_name": "", "vae_name": ""},
    "ltx": {"occupancy": "ltx", "unet_name": LTX_UNET, "clip_name": "", "vae_name": ""},
    "film": {"occupancy": "film", "unet_name": LTX_UNET, "clip_name": "", "vae_name": ""},
    "audio": {"occupancy": "audio", "unet_name": "", "clip_name": "", "vae_name": ""},
    "trellis": {
        "occupancy": "trellis",
        "unet_name": TRELLIS_UNET,
        "clip_name": "",
        "vae_name": "",
    },
    "none": {"occupancy": "none", "unet_name": "", "clip_name": "", "vae_name": ""},
    "llm": {"occupancy": "llm", "unet_name": "", "clip_name": "", "vae_name": ""},
}

# Authored sampler values, deliberately off both rungs of every family, so
# "standard leaves it alone" is a claim about values no rung asks for.
_AUTHORED_STEPS = 21
_AUTHORED_CFG = 7.5

_EXPORT_RE = re.compile(r"^export const EZ_QUALITY_([A-Z_]+) = ", re.MULTILINE)
_ALIAS_ENTRY_RE = re.compile(
    r'^\s*(?:"(?P<quoted>[^"]*)"|(?P<bare>[A-Za-z_][A-Za-z0-9_]*))'
    r"\s*:\s*RUNG_(?P<rung>DRAFT|STANDARD|FINAL)",
    re.MULTILINE,
)
_JSON_DECODER = json.JSONDecoder()


def _presets_payload() -> dict[str, Any]:
    """Decode every JSON payload the generated frontend module exports.

    Args:
        None.

    Returns:
        Mapping of export name (``table``, ``owned``, ...) to its decoded value.
    """
    body = QUALITY_PRESETS_JS.read_text(encoding="utf-8")
    payload: dict[str, Any] = {}
    for match in _EXPORT_RE.finditer(body):
        value, end = _JSON_DECODER.raw_decode(body, match.end())
        assert body[end:].lstrip().startswith(";"), match.group(0)
        payload[match.group(1).lower()] = value
    return payload


def _js_blob() -> str:
    """Frontend sources the Detail node ships with, main module plus table.

    Args:
        None.

    Returns:
        Concatenated source text.
    """
    return JS.read_text(encoding="utf-8") + QUALITY_PRESETS_JS.read_text(encoding="utf-8")


def _js_alias_map() -> dict[str, str]:
    """The accepted-id map in ``ez_quality.js``, as rung ids.

    Args:
        None.

    Returns:
        Mapping of casefolded accepted id to the rung id that module folds it
        onto, or an empty map when the module carries no alias block.
    """
    body = JS.read_text(encoding="utf-8")
    block = re.search(r"const RUNG_ALIASES = \{(?P<body>[\s\S]*?)\n\};", body)
    if block is None:
        return {}
    found: dict[str, str] = {}
    for match in _ALIAS_ENTRY_RE.finditer(block.group("body")):
        quoted = match.group("quoted")
        key = quoted if quoted is not None else match.group("bare")
        rung = match.group("rung")
        assert key is not None and rung is not None, match.group(0)
        found[key.casefold()] = rung.lower()
    return found


def _load(name: str) -> dict[str, Any]:
    """Parse one shipped lab graph by id.

    Args:
        name: ``_lab``-relative id or basename.

    Returns:
        The parsed graph (fresh copy; callers may mutate it).
    """
    return copy.deepcopy(json.loads(lab_json(name).read_text(encoding="utf-8")))


def _node_nodes(graph: dict[str, Any], node_type: str) -> list[dict[str, Any]]:
    """Every node of one type, in file order.

    Args:
        graph: Serialized Comfy graph.
        node_type: Node type to collect.

    Returns:
        Matching node dicts.
    """
    return [node for node in graph.get("nodes") or [] if node.get("type") == node_type]


def _values(node: dict[str, Any]) -> list[Any]:
    """Widgets of a node, asserted to be a list.

    Args:
        node: One graph node.

    Returns:
        Its ``widgets_values`` list.
    """
    raw = node.get("widgets_values")
    assert isinstance(raw, list)
    return raw


def _rung_row(family: str, rung: str) -> dict[str, Any]:
    """One row of the generated table.

    Args:
        family: A family that owns a ladder.
        rung: A named rung id.

    Returns:
        Requested value per overlay field.
    """
    table = export_table()["table"]
    assert isinstance(table, dict)
    rows = table[family]
    assert isinstance(rows, dict)
    row = rows[rung]
    assert isinstance(row, dict)
    return row


def _rung_files(family: str, rung: str) -> list[str]:
    """Files one rung asks a loader to select.

    Args:
        family: A family that owns a ladder.
        rung: A named rung id.

    Returns:
        Filenames the row requests, in table order.
    """
    return [
        value
        for field, value in _rung_row(family, rung).items()
        if field in FILE_FIELDS and isinstance(value, str) and value
    ]


def _graph(
    family: str,
    *,
    rung: str = QUALITY_STANDARD,
    instances: int = 1,
    muted: tuple[str, ...] = (),
    with_size_widgets: bool = True,
) -> dict[str, Any]:
    """Build one graph that classifies as ``family`` and owns its loaders.

    Args:
        family: A ``QUALITY_FAMILIES`` id.
        rung: Value to record on the Detail widget.
        instances: How many samplers and loaders to wire, for the multi-instance
            claim that a rung writes every instance of a field.
        muted: Node types to mute (LiteGraph mode 4).
        with_size_widgets: Add an ``EZImageFormat`` and a latent-size node, so
            an apply that touches size is caught.

    Returns:
        A serialized-graph mapping.
    """
    fixture = _FAMILY_FIXTURES[family]
    nodes: list[dict[str, Any]] = [
        {
            "id": 1,
            "type": QUALITY_TYPE,
            "title": QUALITY_TITLE,
            "widgets_values": [rung],
            "mode": 0 if QUALITY_TYPE not in muted else 4,
        },
    ]
    node_id = 2
    for _round in range(instances):
        nodes.append(
            {
                "id": node_id,
                "type": "KSampler",
                "widgets_values": [7, "fixed", _AUTHORED_STEPS, _AUTHORED_CFG],
                "mode": 0 if "KSampler" not in muted else 4,
            }
        )
        node_id += 1
    if fixture["unet_name"]:
        for _round in range(instances):
            nodes.append(
                {
                    "id": node_id,
                    "type": "UNETLoader",
                    "widgets_values": [fixture["unet_name"]],
                    "mode": 0 if "UNETLoader" not in muted else 4,
                }
            )
            node_id += 1
    if fixture["clip_name"]:
        nodes.append(
            {
                "id": node_id,
                "type": "CLIPLoader",
                # Authored off the rung's clip_type, so that write is real too.
                "widgets_values": [fixture["clip_name"], "stable_diffusion"],
                "mode": 0 if "CLIPLoader" not in muted else 4,
            }
        )
        node_id += 1
    if fixture["vae_name"]:
        nodes.append(
            {
                "id": node_id,
                "type": "VAELoader",
                "widgets_values": [fixture["vae_name"]],
                "mode": 0 if "VAELoader" not in muted else 4,
            }
        )
        node_id += 1
    if with_size_widgets:
        nodes.append(
            {
                "id": node_id,
                "type": "EZImageFormat",
                "widgets_values": ["16:9 draft (768x432)", "none", 768, 432, 2, "Match input"],
            }
        )
        node_id += 1
        nodes.append(
            {
                "id": node_id,
                "type": "EmptyLatentImage",
                "widgets_values": [768, 432, 2],
            }
        )
    return {
        "nodes": nodes,
        "extra": {"lab_app_mode": {"occupancy": fixture["occupancy"], "enabled": True}},
    }


def _catalog(family: str, rung: str, *, starve: bool = False) -> dict[str, list[str]]:
    """Loader combo options for one apply.

    Args:
        family: A family that owns a ladder.
        rung: A named rung id.
        starve: Offer only an unrelated file, so every file the rung names is
            really absent from its loader's options.

    Returns:
        Keyword arguments for ``apply_to_graph`` / ``rung_refusal_reasons``.
    """
    if starve:
        return {
            "available_unets": [_UNRELATED_FILE],
            "available_clips": [_UNRELATED_FILE],
            "available_vaes": [_UNRELATED_FILE],
        }
    options: dict[str, list[str]] = {
        "available_unets": [_UNRELATED_FILE],
        "available_clips": [_UNRELATED_FILE],
        "available_vaes": [_UNRELATED_FILE],
    }
    slot = {"unet_name": "available_unets", "clip_name": "available_clips", "vae_name": "available_vaes"}
    for field, value in _rung_row(family, rung).items():
        if field in slot and isinstance(value, str) and value:
            options[slot[field]].append(value)
    return options


def _widget(graph: dict[str, Any], node_type: str, index: int, which: int = 0) -> Any:
    """One widget slot of the ``which``-th node of a type.

    Args:
        graph: Serialized Comfy graph.
        node_type: Node type to read.
        index: ``widgets_values`` slot.
        which: Which matching node to read.

    Returns:
        The widget value.
    """
    nodes = _node_nodes(graph, node_type)
    assert len(nodes) > which, (node_type, which)
    values = _values(nodes[which])
    assert len(values) > index, (node_type, index)
    return values[index]


def _snapshot(graph: dict[str, Any]) -> str:
    """Canonical text of a whole graph, for byte-for-byte no-change claims.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        Sorted JSON text.
    """
    return json.dumps(graph, sort_keys=True)


# ---------------------------------------------------------------------------
# The node and its combo.
# ---------------------------------------------------------------------------


def test_pack_mappings() -> None:
    """The node is the Detail row, and its combo offers exactly three rungs."""
    assert quality_nodes.NODE_CLASS_MAPPINGS["EZQuality"] is EZQuality
    assert quality_nodes.NODE_DISPLAY_NAME_MAPPINGS["EZQuality"] == QUALITY_TITLE
    assert QUALITY_TITLE == "Detail"
    assert EZQuality.OUTPUT_NODE is True
    types = EZQuality.INPUT_TYPES()
    combo = types["required"]["quality"][0]
    spec = types["required"]["quality"][1]
    assert list(combo) == list(QUALITY_CHOICES)
    assert QUALITY_DEFAULT == QUALITY_STANDARD
    assert spec["default"] == QUALITY_DEFAULT
    for retired in RETIRED_IDS:
        assert retired not in combo, retired
    description = EZQuality.DESCRIPTION.lower()
    assert "standard writes nothing" in description
    assert "never changes size" in description


def test_report_normalizes_every_accepted_id() -> None:
    """The STRING output is a rung, whatever the widget or CLI handed in."""
    for raw, expected in NORMALIZE_TABLE:
        out = EZQuality().report(raw)
        assert out["result"] == (expected,), raw
        assert out["ui"]["text"] == (expected,), raw
    assert EZQuality().report("FINAL")["result"] == (QUALITY_FINAL,)
    assert EZQuality().report("  Free Commercial Use (<$10M)  ")["result"] == (
        QUALITY_FINAL,
    )
    assert EZQuality().report(None)["result"] == (QUALITY_STANDARD,)
    assert EZQuality().report("nope")["result"] == (QUALITY_STANDARD,)


# ---------------------------------------------------------------------------
# Accepted legacy ids: the normalization table.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("accepted", "expected"), NORMALIZE_TABLE)
def test_normalize_quality_lands_every_accepted_id(accepted: str, expected: str) -> None:
    """Each accepted spelling resolves onto the rung the contract pins."""
    assert normalize_quality(accepted) == expected


def test_normalize_quality_is_total_and_caseless() -> None:
    """Anything unrecognized is the rung that writes nothing, never an error."""
    assert normalize_quality(None) == QUALITY_STANDARD
    assert normalize_quality("") == QUALITY_STANDARD
    assert normalize_quality("   ") == QUALITY_STANDARD
    assert normalize_quality("weird") == QUALITY_STANDARD
    assert normalize_quality(3) == QUALITY_STANDARD
    for raw, expected in NORMALIZE_TABLE:
        assert normalize_quality(f"  {raw.upper()}  ") == expected, raw
    assert set(QUALITY_CHOICES) == {"draft", "standard", "final"}
    assert QUALITY_DEFAULT == QUALITY_STANDARD


def test_retired_ids_are_never_selectable() -> None:
    """No retired id survives as a rung, a label, or a tier list entry."""
    for retired in RETIRED_IDS:
        assert retired not in QUALITY_CHOICES, retired
        assert retired not in NAMED_QUALITY_CHOICES, retired
        assert normalize_quality(retired) in QUALITY_CHOICES, retired
    for family in QUALITY_FAMILIES:
        offered = tiers_for_family(family)
        assert set(offered) <= set(QUALITY_CHOICES), family
        for retired in RETIRED_IDS:
            assert retired not in offered, (family, retired)


# ---------------------------------------------------------------------------
# Filename detectors and catalog policy.
# ---------------------------------------------------------------------------


def test_banned_unet_needles() -> None:
    """The banned needles are the non-catalog models, not the Apache stack."""
    assert BANNED_UNET_NEEDLES == ("MiniMax", "Seedance", "Kling", "z_image_turbo")
    for needle in BANNED_UNET_NEEDLES:
        assert is_banned_unet(f"{needle}-H3.safetensors") is True
        assert is_banned_unet(f"{needle.lower()}-H3.safetensors") is True
    for allowed in (KLEIN_DISTILLED, KLEIN_NVFP4, KLEIN_BASE, KLEIN_9B, FLUX2_DEV):
        assert is_banned_unet(allowed) is False


def test_klein_9b_and_flux2_dev_are_detectors_only() -> None:
    """The 9B / dev detectors stay for the checker, and name nothing a rung writes."""
    assert is_klein_9b_unet(KLEIN_9B) is True
    assert is_klein_9b_unet(KLEIN_9B_BASE) is True
    assert is_klein_4b_unet(KLEIN_9B) is False
    assert is_klein_4b_unet(KLEIN_DISTILLED) is True
    assert is_flux2_dev_unet(FLUX2_DEV) is True
    assert is_flux2_dev_unet(KLEIN_BASE) is False
    table = export_table()["table"]
    assert isinstance(table, dict)
    named = {
        value
        for rows in table.values()
        if isinstance(rows, dict)
        for row in rows.values()
        if isinstance(row, dict)
        for value in row.values()
        if isinstance(value, str)
    }
    assert not named & UNREACHABLE_WEIGHTS, named & UNREACHABLE_WEIGHTS


def test_family_weight_predicates() -> None:
    """Each opt-in family is recognised by its own filenames, both spellings."""
    assert is_klein3_unet(KLEIN3_DISTILLED) is True
    assert is_klein3_unet("flux3-image-klein-base-nvfp4") is True
    assert is_klein3_clip(KLEIN3_TE) is True
    assert is_klein3_upsampler("qwen3.5_9b_flux3_prompt_upsampler_int8_convrot.safetensors")
    assert is_klein3_unet(KLEIN_DISTILLED) is False
    assert is_qwen_image_unet(QWEN_IMAGE_INT8) is True
    assert is_qwen_image_unet(QWEN_IMAGE_TURBO_NVFP4) is True
    assert is_qwen_image_clip(QWEN_TE) is True
    assert is_qwen_image_vae(QWEN_VAE) is True
    assert is_qwen_image_unet(KLEIN_NVFP4) is False
    assert is_flux2_clip(CLIP_4B) is True
    assert is_flux2_clip(CLIP_MISTRAL) is True
    assert is_flux2_vae(VAE_FULL) is True
    assert is_flux2_vae(VAE_SMALL) is True
    assert is_flux2_vae(QWEN_VAE) is False
    assert is_wan_14b_unet("wan2.2_t2v_14B_fp16.safetensors") is True
    assert is_wan_14b_unet(WAN_5B_UNET) is False


def test_pick_unet_refuses_banned_and_missing() -> None:
    """A weight the table asks for must be allowed and actually installed."""
    assert _pick_unet("MiniMax-H3.safetensors", {"MiniMax-H3.safetensors"}) is None
    assert _pick_unet(KLEIN_BASE, {KLEIN_DISTILLED}) is None
    assert _pick_unet(KLEIN_BASE, {KLEIN_BASE}) == KLEIN_BASE
    assert _pick_unet(KLEIN_BASE, set()) is None, "an unknown catalog swaps nothing"


# ---------------------------------------------------------------------------
# Per-family rung values.
# ---------------------------------------------------------------------------


def test_table_shape_is_three_rungs_per_family() -> None:
    """The ladder is exactly three rows per family and six fields per row."""
    payload = export_table()
    table = payload["table"]
    assert isinstance(table, dict)
    assert set(table) == set(QUALITY_FAMILIES)
    assert payload["choices"] == list(QUALITY_CHOICES)
    assert payload["default"] == QUALITY_DEFAULT
    assert payload["named"] == list(NAMED_QUALITY_CHOICES)
    assert payload["fields"] == list(OVERLAY_FIELDS)
    for family, rows in table.items():
        assert isinstance(rows, dict)
        assert set(rows) == set(QUALITY_CHOICES), family
        for rung, row in rows.items():
            assert isinstance(row, dict), (family, rung)
            assert set(row) == set(OVERLAY_FIELDS), (family, rung)


def test_standard_writes_nothing_on_every_family() -> None:
    """The default rung is an empty row everywhere: it cannot drift.

    This single rule is what deleted the ``lab`` / ``custom`` state machine, so
    it is checked straight off both the table and ``tier_profile``.
    """
    for family in QUALITY_FAMILIES:
        for field in OVERLAY_FIELDS:
            assert getattr(tier_profile(family, QUALITY_STANDARD), field) is None, family
            assert _rung_row(family, QUALITY_STANDARD)[field] is None, family
        plan = plan_rung_writes(_graph(family, rung=QUALITY_FINAL), QUALITY_STANDARD)
        assert plan.writes == () and plan.reasons == (), family


@pytest.mark.parametrize(
    ("family", "rung", "steps", "cfg"),
    [
        ("klein", QUALITY_DRAFT, KLEIN_DRAFT_STEPS, KLEIN_DRAFT_CFG),
        ("klein", QUALITY_FINAL, KLEIN_FINAL_STEPS, KLEIN_FINAL_CFG),
        (QUALITY_FAMILY_KLEIN3, QUALITY_DRAFT, KLEIN3_DRAFT_STEPS, KLEIN3_DRAFT_CFG),
        (QUALITY_FAMILY_KLEIN3, QUALITY_FINAL, KLEIN3_FINAL_STEPS, KLEIN3_FINAL_CFG),
        (QUALITY_FAMILY_QWEN, QUALITY_DRAFT, QWEN_DRAFT_STEPS, QWEN_DRAFT_CFG),
        (QUALITY_FAMILY_QWEN, QUALITY_FINAL, QWEN_FINAL_STEPS, QWEN_FINAL_CFG),
    ],
)
def test_weight_families_pin_steps_cfg_and_their_own_unet(
    family: str,
    rung: str,
    steps: int,
    cfg: float,
) -> None:
    """The three weight families name a transformer and a recipe per rung."""
    profile = tier_profile(family, rung)
    assert profile.steps == steps, (family, rung)
    assert profile.cfg == cfg, (family, rung)
    assert profile.unet_name, (family, rung)
    row = _rung_row(family, rung)
    assert row["steps"] == steps and row["cfg"] == cfg, (family, rung)
    assert row["unet_name"] == profile.unet_name, (family, rung)


def test_klein_rung_rows_bind_the_klein_stack() -> None:
    """Klein draft is the NVFP4 quick look; final is the base FP8 recipe."""
    draft = tier_profile("klein", QUALITY_DRAFT)
    final = tier_profile("klein", QUALITY_FINAL)
    assert (draft.unet_name, draft.clip_name, draft.vae_name) == (
        KLEIN_NVFP4,
        CLIP_4B,
        VAE_SMALL,
    )
    assert (final.unet_name, final.clip_name, final.vae_name) == (
        KLEIN_BASE,
        CLIP_4B,
        VAE_FULL,
    )
    assert draft.clip_type == CLIP_TYPE_FLUX2
    assert final.clip_type == CLIP_TYPE_FLUX2


def test_opt_in_weight_rows_bind_their_own_weights() -> None:
    """FLUX 3 and Qwen rungs swap inside their own stack, never Klein's."""
    assert tier_profile(QUALITY_FAMILY_KLEIN3, QUALITY_DRAFT).unet_name == KLEIN3_DISTILLED
    assert tier_profile(QUALITY_FAMILY_KLEIN3, QUALITY_FINAL).unet_name == KLEIN3_NVFP4
    assert tier_profile(QUALITY_FAMILY_QWEN, QUALITY_DRAFT).unet_name == QWEN_IMAGE_TURBO_INT8
    assert tier_profile(QUALITY_FAMILY_QWEN, QUALITY_FINAL).unet_name == QWEN_IMAGE_INT8
    for family in (QUALITY_FAMILY_KLEIN3, QUALITY_FAMILY_QWEN):
        for rung in NAMED_QUALITY_CHOICES:
            row = _rung_row(family, rung)
            assert row["clip_name"] is None and row["vae_name"] is None, (family, rung)
            assert row["clip_type"] is None, (family, rung)


@pytest.mark.parametrize(
    ("family", "draft_steps", "final_steps"),
    [
        ("wan", WAN_DRAFT_STEPS, WAN_FINAL_STEPS),
        ("ltx", LTX_DRAFT_STEPS, LTX_FINAL_STEPS),
        ("film", LTX_DRAFT_STEPS, LTX_FINAL_STEPS),
        ("audio", AUDIO_DRAFT_STEPS, AUDIO_FINAL_STEPS),
        ("trellis", TRELLIS_DRAFT_STEPS, TRELLIS_FINAL_STEPS),
    ],
)
def test_steps_only_families_write_steps_and_nothing_else(
    family: str,
    draft_steps: int,
    final_steps: int,
) -> None:
    """A steps-only family never gets a CFG or a weight from a rung.

    The contract is explicit: a rung writes no CFG on a family whose table has
    none, so an authored CFG is always the author's own.
    """
    assert family_owned_fields(family) == ("steps",)
    for rung, steps in ((QUALITY_DRAFT, draft_steps), (QUALITY_FINAL, final_steps)):
        profile = tier_profile(family, rung)
        assert profile.steps == steps, (family, rung)
        assert profile.cfg is None, (family, rung)
        assert profile.unet_name is None, (family, rung)
        assert profile.clip_name is None and profile.vae_name is None, (family, rung)
        assert profile.clip_type is None, (family, rung)
    assert _rung_row("film", QUALITY_FINAL)["steps"] == _rung_row("ltx", QUALITY_FINAL)["steps"]


def test_a_rung_never_owns_a_size_field() -> None:
    """The overlay's field set holds no width, height, frames, or format widget."""
    assert set(OVERLAY_FIELDS) == {"steps", "cfg", "unet_name", "clip_name", "vae_name", "clip_type"}
    assert set(FIELD_WIDGET_NAMES) == set(OVERLAY_FIELDS)
    for field in OVERLAY_FIELDS:
        assert "width" not in field and "height" not in field
        assert "format" not in field and "frames" not in field
    assert "EZImageFormat" not in JS.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Apply is write-or-refuse.
# ---------------------------------------------------------------------------


def test_apply_writes_every_owned_field_on_every_instance() -> None:
    """A rung that lands writes its whole row, on every instance of each field."""
    graph = _graph("klein", instances=2)
    before = _snapshot(graph)

    plan = plan_rung_writes(graph, QUALITY_FINAL, **_catalog("klein", QUALITY_FINAL))
    assert plan.reasons == (), plan.reasons
    apply_to_graph(graph, QUALITY_FINAL, **_catalog("klein", QUALITY_FINAL))

    assert _snapshot(graph) != before
    assert _widget(graph, "UNETLoader", UNET_NAME_INDEX, 0) == KLEIN_BASE
    assert _widget(graph, "UNETLoader", UNET_NAME_INDEX, 1) == KLEIN_BASE
    assert _widget(graph, "KSampler", KSAMPLER_STEPS_INDEX, 0) == KLEIN_FINAL_STEPS
    assert _widget(graph, "KSampler", KSAMPLER_STEPS_INDEX, 1) == KLEIN_FINAL_STEPS
    assert _widget(graph, "KSampler", KSAMPLER_CFG_INDEX, 0) == KLEIN_FINAL_CFG
    assert _widget(graph, "CLIPLoader", CLIP_NAME_INDEX) == CLIP_4B
    assert _widget(graph, "CLIPLoader", 1) == CLIP_TYPE_FLUX2
    assert _widget(graph, "VAELoader", VAE_NAME_INDEX) == VAE_FULL


def test_apply_standard_is_a_no_op_that_cannot_be_refused() -> None:
    """standard always succeeds and writes nothing, even with no catalog at all."""
    for family in LADDER_FAMILIES:
        graph = _graph(family, rung=QUALITY_FINAL)
        before = _snapshot(graph)
        apply_to_graph(graph, QUALITY_STANDARD, **_catalog(family, QUALITY_DRAFT, starve=True))
        assert _snapshot(graph) == before, family
        assert rung_refusal_reasons(graph, QUALITY_STANDARD) == (), family


def test_apply_refuses_whole_when_one_file_is_missing() -> None:
    """One write that cannot land cancels the apply: nothing is renamed or staged."""
    for family in LADDER_FAMILIES:
        for rung in (QUALITY_DRAFT, QUALITY_FINAL):
            graph = _graph(family)
            before = _snapshot(graph)
            catalog = _catalog(family, rung, starve=True)
            reasons = rung_refusal_reasons(graph, rung, **catalog)
            apply_to_graph(graph, rung, **catalog)
            authored = set(_FAMILY_FIXTURES[family].values())
            asked = [f for f in _rung_files(family, rung) if f not in authored]
            for wanted in asked:
                assert any(wanted in reason for reason in reasons), (family, rung, wanted)
            if reasons:
                assert _snapshot(graph) == before, (family, rung, reasons)
            else:
                # Nothing was refused, which is only honest when the rung asked
                # for no file the graph did not already hold.
                assert asked == [], (family, rung, reasons)


def test_apply_refuses_a_rung_a_family_cannot_honor() -> None:
    """A family mismatch is a refusal, not a silent no-op that keeps the label."""
    for family in NO_RUNG_FAMILIES:
        graph = _graph(family)
        before = _snapshot(graph)
        reasons = rung_refusal_reasons(graph, QUALITY_FINAL)
        assert reasons, family
        assert family in reasons[0], (family, reasons)
        apply_to_graph(graph, QUALITY_FINAL)
        assert _snapshot(graph) == before, family
    assert not tier_is_honored("llm", QUALITY_FINAL)
    assert not tier_is_honored("none", QUALITY_DRAFT)


def test_apply_skips_a_muted_lane_and_refuses() -> None:
    """A muted loader holds no live widget, so its field has no target to write."""
    graph = _graph("klein", muted=("UNETLoader",))
    before = _snapshot(graph)
    reasons = rung_refusal_reasons(graph, QUALITY_FINAL, **_catalog("klein", QUALITY_FINAL))
    assert any("unet_name" in reason for reason in reasons), reasons
    apply_to_graph(graph, QUALITY_FINAL, **_catalog("klein", QUALITY_FINAL))
    assert _snapshot(graph) == before, "a refused apply writes no partial row"


def test_apply_never_touches_a_size_widget() -> None:
    """No rung changes width, height, batch, frames, or the format selector."""
    for family in LADDER_FAMILIES:
        for rung in NAMED_QUALITY_CHOICES:
            graph = _graph(family, rung=QUALITY_STANDARD, instances=2)
            catalog = _catalog(family, rung)
            format_before = _values(_node_nodes(graph, "EZImageFormat")[0])
            latent_before = _values(_node_nodes(graph, "EmptyLatentImage")[0])
            apply_to_graph(graph, rung, **catalog)
            assert _values(_node_nodes(graph, "EZImageFormat")[0]) == format_before, (family, rung)
            assert _values(_node_nodes(graph, "EmptyLatentImage")[0]) == latent_before, (
                family,
                rung,
            )


def test_wan_14b_graph_is_never_overlaid() -> None:
    """A 14B pin is not the App's own stack, so every rung that writes refuses it."""
    graph = _graph("wan")
    _values(_node_nodes(graph, "UNETLoader")[0])[0] = "wan2.2_t2v_14B_fp16.safetensors"
    assert graph_has_wan14(graph) is True
    before = _snapshot(graph)
    # standard asks for no write, so it has nothing to be refused over.
    assert rung_refusal_reasons(graph, QUALITY_STANDARD, **_catalog("wan", QUALITY_STANDARD)) == ()
    for rung in (QUALITY_DRAFT, QUALITY_FINAL):
        catalog = _catalog("wan", rung)
        reasons = rung_refusal_reasons(graph, rung, **catalog)
        assert reasons == ("Wan 14B is not overlaid",), (rung, reasons)
        apply_to_graph(graph, rung, **catalog)
    assert _snapshot(graph) == before


def test_trellis_rung_writes_only_the_guided_stages() -> None:
    """Four TRELLIS stages share one graph; the CFG 1.0 pass is its own recipe."""
    graph = _load("3d/trellis2")
    guided = [n for n in _node_nodes(graph, "KSampler") if n.get("id") != 18]
    texture = next(n for n in _node_nodes(graph, "KSampler") if n.get("id") == 18)
    assert texture.get("title") == "KSampler (texture)"
    for node in guided:
        _values(node)[KSAMPLER_STEPS_INDEX] = 12
    _values(texture)[KSAMPLER_STEPS_INDEX] = 12

    apply_to_graph(graph, QUALITY_FINAL)

    for node in guided:
        assert _values(node)[KSAMPLER_STEPS_INDEX] == TRELLIS_FINAL_STEPS
    assert _values(texture)[KSAMPLER_STEPS_INDEX] == 12, (
        "the unguided stage keeps the steps its author set"
    )


def test_is_trellis_guidance_free_stage_reads_only_the_trellis_recipe() -> None:
    """The exemption belongs to TRELLIS samplers and to CFG 1.0 alone."""
    stage: dict[str, Any] = {"type": "KSampler", "widgets_values": [0, "fixed", 12, 1.0]}
    guided: dict[str, Any] = {"type": "KSampler", "widgets_values": [0, "fixed", 12, 7.5]}
    assert is_trellis_guidance_free_stage(stage, "trellis") is True
    assert is_trellis_guidance_free_stage(guided, "trellis") is False
    assert is_trellis_guidance_free_stage(stage, "wan") is False
    assert (
        is_trellis_guidance_free_stage(
            {"type": "VAELoader", "widgets_values": ["x", 1]}, "trellis"
        )
        is False
    )
    assert is_trellis_guidance_free_stage({"type": "KSampler"}, "trellis") is False
    assert (
        is_trellis_guidance_free_stage(
            {"type": "KSampler", "widgets_values": [0, "fixed", 12, "warm"]}, "trellis"
        )
        is False
    )
    assert TRELLIS_GUIDANCE_FREE_CFG == 1.0


def test_apply_refuses_a_banned_weight(monkeypatch: pytest.MonkeyPatch) -> None:
    """A banned weight in a rung row is refused by name, never written."""
    banned = "MiniMax-H3.safetensors"
    # One field of the shipped row is poisoned, so everything the guard reads
    # beside it stays the table's own answer.
    monkeypatch.setitem(
        _RUNG_ROWS["klein"],
        QUALITY_FINAL,
        replace(_RUNG_ROWS["klein"][QUALITY_FINAL], unet_name=banned),
    )
    graph = _graph("klein")
    before = _snapshot(graph)
    reasons = rung_refusal_reasons(graph, QUALITY_FINAL)
    assert reasons == (f"{banned} is not allowed",), reasons
    apply_to_graph(graph, QUALITY_FINAL)
    assert _snapshot(graph) == before


# ---------------------------------------------------------------------------
# Family detection and the honor tables.
# ---------------------------------------------------------------------------


def test_family_for_and_graph_family_pull_the_opt_in_weights() -> None:
    """A FLUX 3 or Qwen loader pulls the graph into its own family.

    Both opt-in stacks stamp the klein occupancy, so the loaders a live lane
    pins are what keeps one vendor's ladder off the other's graph.
    """
    assert family_for("klein") == "klein"
    assert family_for("klein", unet_name=KLEIN3_NVFP4) == QUALITY_FAMILY_KLEIN3
    assert family_for("klein", clip_name=KLEIN3_TE) == QUALITY_FAMILY_KLEIN3
    assert family_for("klein", unet_name=QWEN_IMAGE_NVFP4) == QUALITY_FAMILY_QWEN
    assert family_for("klein", clip_name=QWEN_TE) == QUALITY_FAMILY_QWEN
    assert family_for("wan", unet_name=WAN_5B_UNET) == "wan"
    assert family_for("dub") == "none"
    assert family_for("llm") == "llm"
    assert family_for("none") == "none"
    assert family_for("") == "none"
    for family in LADDER_FAMILIES:
        assert graph_family(_graph(family)) == family
    assert graph_family(_graph("none")) == "none"
    # An empty canvas infers no occupancy at all, which reads as a no-rung family.
    assert infer_occupancy({"nodes": []}) == ""
    assert graph_family({"nodes": []}) == "none"


def test_infer_occupancy_reads_the_stamp_then_the_nodes() -> None:
    """Occupancy comes from the App stamp, else from the sink the graph ends in."""
    assert infer_occupancy(_graph("wan")) == "wan"
    assert infer_occupancy({"nodes": [{"type": "SaveImage"}]}) == "klein"
    assert infer_occupancy({"nodes": [{"type": "SaveAudio"}]}) == "audio"
    assert infer_occupancy({"nodes": [{"type": "EZFilmConcat"}]}) == "film"
    assert infer_occupancy({"nodes": [{"type": "MeshToFile3D"}]}) == "trellis"
    assert infer_occupancy({"nodes": [{"type": "Note"}]}) == ""
    video = {
        "nodes": [
            {"type": "VHS_VideoCombine"},
            {"type": "UNETLoader", "widgets_values": [LTX_UNET]},
        ]
    }
    assert infer_occupancy(video) == "ltx"


def test_tiers_for_family_offers_the_three_rungs_or_none() -> None:
    """Every ladder family offers exactly the three rungs, in combo order."""
    assert LADDER_FAMILIES == (
        "klein",
        QUALITY_FAMILY_KLEIN3,
        QUALITY_FAMILY_QWEN,
        "wan",
        "ltx",
        "film",
        "audio",
        "trellis",
    )
    for family in LADDER_FAMILIES:
        assert tiers_for_family(family) == QUALITY_CHOICES, family
    for family in NO_RUNG_FAMILIES:
        assert tiers_for_family(family) == (), family
    assert tiers_for_family("") == ()
    assert tiers_for_family("longcat") == ()


def test_tiers_for_family_offers_only_rungs_that_write() -> None:
    """A rung the family lists writes something; a rung it drops writes nothing."""
    for family in QUALITY_FAMILIES:
        offered = tiers_for_family(family)
        for rung in offered:
            if rung == QUALITY_STANDARD:
                continue
            profile = tier_profile(family, rung)
            assert any(
                getattr(profile, field) is not None for field in OVERLAY_FIELDS
            ), (family, rung)
        for rung in NAMED_QUALITY_CHOICES:
            if rung in offered:
                continue
            profile = tier_profile(family, rung)
            assert all(
                getattr(profile, field) is None for field in OVERLAY_FIELDS
            ), (family, rung)


def test_tier_is_honored_refuses_a_rung_the_family_cannot_write() -> None:
    """There is no fallback rung: an unhonorable rung is refused, not stamped.

    Before the combo was scoped, a rung that wrote no widget still stamped as
    applied, so the row named a level the graph never reached. An id the table
    does not know folds onto ``standard``, so an unknown input lands by writing
    nothing rather than by substituting a weight.
    """
    assert tier_is_honored("klein", QUALITY_FINAL)
    assert tier_is_honored("wan", "FINAL")
    assert normalize_quality("longcat") == QUALITY_DEFAULT
    assert tier_is_honored("wan", "longcat")
    for family in NO_RUNG_FAMILIES + ("", "longcat"):
        assert tiers_for_family(family) == (), family
        assert not tier_is_honored(family, QUALITY_DRAFT), family
        assert not tier_is_honored(family, QUALITY_FINAL), family
        # A family with no ladder has no combo at all, so even the rung that
        # writes nothing is off it: there is nothing to label.
        assert not tier_is_honored(family, QUALITY_STANDARD), family
    offered = tiers_for_family("wan")
    for accepted, expected in NORMALIZE_TABLE:
        assert tier_is_honored("wan", accepted) is (expected in offered), accepted


def test_family_owned_fields_is_the_footprint_of_the_family_rungs() -> None:
    """Fields no rung ever sets stay authored, so an edit there is not a drift."""
    assert family_owned_fields("klein") == tuple(OVERLAY_FIELDS)
    assert family_owned_fields(QUALITY_FAMILY_KLEIN3) == ("steps", "cfg", "unet_name")
    assert family_owned_fields(QUALITY_FAMILY_QWEN) == ("steps", "cfg", "unet_name")
    for family in STEPS_ONLY_FAMILIES:
        assert family_owned_fields(family) == ("steps",), family
    for family in NO_RUNG_FAMILIES:
        assert family_owned_fields(family) == (), family
    payload = export_table()["owned"]
    assert isinstance(payload, dict)
    assert payload == {family: list(family_owned_fields(family)) for family in QUALITY_FAMILIES}


def test_tier_label_names_the_swap_and_stays_silent_for_standard() -> None:
    """The tooltip names what a rung pins; the rung that writes nothing says nothing."""
    assert tier_label("klein", QUALITY_STANDARD) == ""
    assert tier_label("wan", QUALITY_DRAFT) == f"{WAN_DRAFT_STEPS} steps"
    assert tier_label("wan", QUALITY_FINAL) == f"{WAN_FINAL_STEPS} steps"
    klein_draft = tier_label("klein", QUALITY_DRAFT)
    assert klein_draft.startswith(KLEIN_NVFP4.rsplit(".", 1)[0]), klein_draft
    assert f"{KLEIN_DRAFT_STEPS} steps" in klein_draft
    assert f"CFG {KLEIN_DRAFT_CFG}" in klein_draft
    for family in QUALITY_FAMILIES:
        assert tier_label(family, QUALITY_LAB) == "", family
        assert tier_label(family, QUALITY_CUSTOM) == "", family


def test_rung_label_capitalizes_and_follows_the_normalizer() -> None:
    """The caption names a rung the same way whatever spelling arrives."""
    for rung in QUALITY_CHOICES:
        assert rung_label(rung) == RUNG_LABEL[rung]
    assert rung_label("HIGH") == RUNG_LABEL[QUALITY_FINAL]
    assert rung_label("qwen-image-turbo") == RUNG_LABEL[QUALITY_DRAFT]
    assert rung_label("nope") == RUNG_LABEL[QUALITY_STANDARD]


# ---------------------------------------------------------------------------
# Cross-family guards.
# ---------------------------------------------------------------------------


def test_the_klein_ladder_never_drops_onto_an_opt_in_graph() -> None:
    """An opt-in graph keeps its own weights: the Klein row is not its row."""
    for family, foreign in (
        (QUALITY_FAMILY_KLEIN3, (KLEIN_BASE, KLEIN_NVFP4)),
        (QUALITY_FAMILY_QWEN, (KLEIN_BASE, KLEIN_NVFP4)),
    ):
        for rung in NAMED_QUALITY_CHOICES:
            plan = plan_rung_writes(_graph(family), rung, **_catalog(family, rung))
            written = {str(write.value) for write in plan.writes}
            assert not written & set(foreign), (family, rung, written)
            profile = resolve_overlay(
                occupancy="klein",
                quality=rung,
                authored_steps=_AUTHORED_STEPS,
                authored_cfg=_AUTHORED_CFG,
                unet_name=_FAMILY_FIXTURES[family]["unet_name"],
                available_unets=[*foreign, str(_rung_row(family, rung)["unet_name"])],
            )
            assert profile.unet_name not in foreign, (family, rung)


def test_the_two_opt_in_ladders_never_share_a_weight() -> None:
    """FLUX 3 and Qwen are separate families, not two rows of one ladder."""
    klein3_files = {
        value
        for rung in NAMED_QUALITY_CHOICES
        for value in _rung_files(QUALITY_FAMILY_KLEIN3, rung)
    }
    qwen_files = {
        value
        for rung in NAMED_QUALITY_CHOICES
        for value in _rung_files(QUALITY_FAMILY_QWEN, rung)
    }
    assert klein3_files and qwen_files
    assert not klein3_files & qwen_files
    for family, foreign in (
        (QUALITY_FAMILY_KLEIN3, qwen_files),
        (QUALITY_FAMILY_QWEN, klein3_files),
    ):
        for rung in NAMED_QUALITY_CHOICES:
            plan = plan_rung_writes(_graph(family), rung, **_catalog(family, rung))
            written = {str(write.value) for write in plan.writes}
            assert not written & foreign, (family, rung, written)


def test_a_rung_writes_only_its_own_family_files() -> None:
    """Each family's rung rows name only files that family's own stack owns."""
    own: dict[str, set[str]] = {
        "klein": {KLEIN_NVFP4, KLEIN_BASE, KLEIN_DISTILLED, CLIP_4B, VAE_SMALL, VAE_FULL},
        QUALITY_FAMILY_KLEIN3: {KLEIN3_DISTILLED, KLEIN3_NVFP4},
        QUALITY_FAMILY_QWEN: {QWEN_IMAGE_TURBO_INT8, QWEN_IMAGE_INT8},
    }
    for family, allowed in own.items():
        for rung in NAMED_QUALITY_CHOICES:
            named = set(_rung_files(family, rung))
            assert named <= allowed, (family, rung, named - allowed)
    for family in STEPS_ONLY_FAMILIES:
        for rung in NAMED_QUALITY_CHOICES:
            assert _rung_files(family, rung) == [], (family, rung)


def test_foreign_weight_is_not_swappable_and_refuses_the_apply() -> None:
    """A loader holding a weight the overlay may not replace blocks the apply."""
    graph = _graph("klein")
    _values(_node_nodes(graph, "UNETLoader")[0])[0] = "ltx-2.5-22b-distilled-transformer.safetensors"
    before = _snapshot(graph)
    reasons = rung_refusal_reasons(graph, QUALITY_FINAL, **_catalog("klein", QUALITY_FINAL))
    assert any("cannot swap" in reason for reason in reasons), reasons
    apply_to_graph(graph, QUALITY_FINAL, **_catalog("klein", QUALITY_FINAL))
    assert _snapshot(graph) == before


# ---------------------------------------------------------------------------
# The caption is the only place truth lives.
# ---------------------------------------------------------------------------


def test_caption_is_the_one_line_read_off_the_live_widgets() -> None:
    """``<stack> - <steps> steps - CFG <cfg> - <license>``, derived, never stamped."""
    caption = caption_for(
        "klein",
        QUALITY_FINAL,
        {
            "unet_name": KLEIN_BASE,
            "steps": KLEIN_FINAL_STEPS,
            "cfg": KLEIN_FINAL_CFG,
            "clip_name": CLIP_4B,
            "vae_name": VAE_FULL,
            "clip_type": CLIP_TYPE_FLUX2,
        },
    )
    assert caption == (
        f"{STACK_LABEL['klein']} base - {KLEIN_FINAL_STEPS} steps - "
        f"CFG {_text(KLEIN_FINAL_CFG)} - {LICENSE_LABEL['klein']}"
    )
    assert not caption.startswith(EDITED_PREFIX)


def test_caption_names_the_license_where_the_choice_is_made() -> None:
    """Every family states its own license word, opt-in stacks included.

    The two opt-in families must never read as an Apache one: that is the whole
    point of putting licensing in the caption instead of in prose.
    """
    assert LICENSE_LABEL[QUALITY_FAMILY_KLEIN3] == "FLUX Non-Commercial"
    assert LICENSE_LABEL[QUALITY_FAMILY_QWEN] == "Qwen Research license"
    for family in LADDER_FAMILIES:
        word = LICENSE_LABEL[family]
        assert word, family
        caption = caption_for(family, QUALITY_STANDARD)
        assert caption.endswith(word), (family, caption)
        assert caption.split(" - ")[0], family
    for family in NO_RUNG_FAMILIES:
        assert caption_for(family, QUALITY_FINAL) == "", family


def test_caption_omits_cfg_for_a_family_that_writes_no_cfg() -> None:
    """A steps-only family has no CFG term: the authored CFG is the author's."""
    for family in STEPS_ONLY_FAMILIES:
        caption = caption_for(family, QUALITY_FINAL, {"steps": 99, "cfg": 7.5})
        assert "CFG" not in caption, (family, caption)
        assert "99 steps" in caption, (family, caption)
    assert "CFG" in caption_for("klein", QUALITY_STANDARD, {"steps": 4, "cfg": 1.0})


def test_caption_marks_a_hand_edit_and_names_what_the_rung_sets() -> None:
    """The Edited line is the label and the wire agreeing, in the contract's words."""
    live: dict[str, Any] = {
        "unet_name": KLEIN_BASE,
        "steps": 20,
        "cfg": KLEIN_FINAL_CFG,
        "clip_name": CLIP_4B,
        "vae_name": VAE_FULL,
        "clip_type": CLIP_TYPE_FLUX2,
    }
    caption = caption_for("klein", QUALITY_FINAL, live)
    assert caption == (
        f"{EDITED_PREFIX}{STACK_LABEL['klein']} base - 20 steps "
        f"({RUNG_LABEL[QUALITY_FINAL]} sets {KLEIN_FINAL_STEPS}) - "
        f"CFG {_text(KLEIN_FINAL_CFG)} - {LICENSE_LABEL['klein']}"
    )


def test_caption_names_every_divergence_and_reads_the_rung_off_the_widgets() -> None:
    """The full reason list is written, and the rung name never replaces a value."""
    live: dict[str, Any] = {
        "unet_name": KLEIN_DISTILLED,
        "steps": 20,
        "cfg": 1.0,
        "clip_name": CLIP_MISTRAL,
        "vae_name": VAE_SMALL,
        "clip_type": "stable_diffusion",
    }
    caption = caption_for("klein", QUALITY_FINAL, live)
    assert caption.startswith(EDITED_PREFIX)
    for needle in (
        f"20 steps ({RUNG_LABEL[QUALITY_FINAL]} sets {KLEIN_FINAL_STEPS})",
        f"CFG {_text(1.0)} ({RUNG_LABEL[QUALITY_FINAL]} sets {_text(KLEIN_FINAL_CFG)})",
        f"{FIELD_WIDGET_NAMES['clip_name']} {CLIP_MISTRAL.rsplit('.', 1)[0]}",
        f"{FIELD_WIDGET_NAMES['vae_name']} {VAE_SMALL.rsplit('.', 1)[0]}",
        f"{FIELD_WIDGET_NAMES['clip_type']} stable_diffusion",
    ):
        assert needle in caption, needle
    # The rung name never stands in for what the widgets actually hold: the
    # stack term is the one presets.py owns for the weight in the loader.
    assert caption.endswith(LICENSE_LABEL["klein"])
    assert caption.startswith(f"{EDITED_PREFIX}{UNET_STACK_LABEL[KLEIN_DISTILLED]}")
    assert f"({RUNG_LABEL[QUALITY_FINAL]} sets {UNET_STACK_LABEL[KLEIN_BASE]})" in caption


def test_a_field_the_caller_does_not_report_is_not_a_disagreement() -> None:
    """Partial knowledge earns no term of its own, and no Edited prefix."""
    assert caption_for("klein", QUALITY_FINAL, {"steps": KLEIN_FINAL_STEPS}) == (
        f"{STACK_LABEL['klein']} - {KLEIN_FINAL_STEPS} steps - {LICENSE_LABEL['klein']}"
    )
    assert not caption_for("klein", QUALITY_FINAL, {}).startswith(EDITED_PREFIX)
    assert caption_for("klein", QUALITY_STANDARD) == (
        f"{STACK_LABEL['klein']} - {LICENSE_LABEL['klein']}"
    )


def _text(value: float) -> str:
    """Render a number the way the caption does, for expected strings.

    Args:
        value: Steps or CFG value.

    Returns:
        The value as text, with a trailing ``.0`` dropped.
    """
    return str(int(value)) if float(value).is_integer() else str(value)


# ---------------------------------------------------------------------------
# The frontend reads this module, not its own numbers.
# ---------------------------------------------------------------------------


def test_generated_presets_module_is_the_preset_table() -> None:
    """The shipped frontend table is ``export_table()``, so JS cannot drift."""
    payload = _presets_payload()
    assert payload == export_table()
    assert payload["choices"] == list(QUALITY_CHOICES)
    assert payload["default"] == QUALITY_DEFAULT
    assert payload["named"] == list(NAMED_QUALITY_CHOICES)
    assert payload["families"] == list(QUALITY_FAMILIES)
    assert payload["fields"] == list(OVERLAY_FIELDS)
    assert payload["edited_prefix"] == EDITED_PREFIX
    assert payload["rung_labels"] == dict(RUNG_LABEL)
    assert payload["licenses"] == dict(LICENSE_LABEL)
    assert payload["owned"] == {
        family: list(family_owned_fields(family)) for family in QUALITY_FAMILIES
    }
    assert payload["tiers"] == {
        family: list(tiers_for_family(family)) for family in QUALITY_FAMILIES
    }


def test_generated_presets_module_is_up_to_date() -> None:
    """The committed generated module is a no-op rewrite of what presets renders."""
    assert _build_quality_js.render() == QUALITY_PRESETS_JS.read_text(encoding="utf-8")


def test_generated_table_names_no_reachable_weight_and_no_size_field() -> None:
    """The table the browser reads holds no 9B, no dev, and no size widget."""
    table = _presets_payload()["table"]
    assert isinstance(table, dict)
    values = {
        value
        for rows in table.values()
        if isinstance(rows, dict)
        for row in rows.values()
        if isinstance(row, dict)
        for value in row.values()
        if isinstance(value, str)
    }
    assert not values & UNREACHABLE_WEIGHTS, values & UNREACHABLE_WEIGHTS
    for family, rows in table.items():
        assert isinstance(rows, dict)
        assert rows[QUALITY_STANDARD] == {field: None for field in OVERLAY_FIELDS}, family


@pytest.mark.parametrize("choice", QUALITY_CHOICES)
def test_js_mirrors_every_rung(choice: str) -> None:
    """Every selectable rung reaches the browser, from either module."""
    assert choice in _js_blob()
    assert RUNG_LABEL[choice].lower() in _js_blob().lower()


def test_js_alias_map_mirrors_the_normalization_table() -> None:
    """The browser folds the same accepted ids onto the same rungs.

    The frontend and the submit path must agree on what a saved graph means, or
    an old graph reads as one rung in the row and sends another to the queue.
    """
    aliases = _js_alias_map()
    assert aliases, "ez_quality.js keeps an accepted-id alias map"
    # The two live weight rungs need no alias entry: normalizeRung reads them
    # off RUNGS. Every other accepted id, the empty value included, has to be
    # listed on both sides of the wire.
    expected = {
        accepted.casefold(): target
        for accepted, target in NORMALIZE_TABLE
        if accepted not in (QUALITY_DRAFT, QUALITY_FINAL)
    }
    assert set(aliases) == set(expected), sorted(set(aliases) ^ set(expected))
    for accepted, target in aliases.items():
        assert target == normalize_quality(accepted), accepted


def test_js_keeps_the_ladder_and_the_family_gates() -> None:
    """The overlay names the Detail row, three rungs, and both opt-in gates."""
    body = JS.read_text(encoding="utf-8")
    blob = _js_blob()
    for needle in (
        'const DETAIL_LABEL = "Detail"',
        "const RUNGS = [RUNG_DRAFT, RUNG_STANDARD, RUNG_FINAL]",
        "function normalizeRung",
        "function graphFamily",
        "function ownedFields",
        "function rungIsHonored",
        "function planRungApply",
        "function applyQuality",
        "function deriveQualityCaption",
        "function stampQualityCaption",
        "function isKlein3Unet",
        "function isKlein3Clip",
        "function isQwenImageUnet",
        "function isQwenImageClip",
        "function isQwenImageVae",
        "lab_quality_caption",
        "widget.value",
        "widgets_values[idx]",
    ):
        assert needle in body, needle
    for family in QUALITY_FAMILIES:
        assert family in blob, family
    for weight in (
        KLEIN_NVFP4,
        KLEIN_BASE,
        CLIP_4B,
        VAE_FULL,
        VAE_SMALL,
        KLEIN3_DISTILLED,
        KLEIN3_NVFP4,
        QWEN_IMAGE_INT8,
        QWEN_IMAGE_TURBO_INT8,
    ):
        assert weight in blob, weight


def test_js_holds_no_stale_state_or_retired_row() -> None:
    """No browser-global carries a rung, and no retired id is a selectable row.

    Retired ids may appear only as keys of the alias map that folds them onto a
    rung: anywhere else they would be a row, a derivation, or a stamp.
    """
    body = JS.read_text(encoding="utf-8")
    for gone in (
        "localStorage",
        "ez-comfy.quality.last",
        "EZImageFormat",
        "freezeQualityToCustom",
        "node_widget",
        "onResize",
        '"lab"',
        '"custom"',
    ):
        assert gone not in body, gone
    outside = body.replace(re.search(r"const RUNG_ALIASES = \{[\s\S]*?\n\};", body).group(0), "")  # type: ignore[union-attr]
    for retired in RETIRED_IDS:
        assert f'"{retired}"' not in outside, retired


def test_model_check_js_reports_the_check_payload_identities() -> None:
    """The Check models report forwards what ``run_check`` emits, ASCII-clean."""
    body = MODEL_CHECK_JS.read_text(encoding="utf-8")
    assert 'addWidget("button", "Report failure", "report"' in body
    assert "window.EzFeedback" in body
    assert "node._ezLastCheck" in body
    assert "node._ezLastHints" in body
    for key in ("lab_rel", "occupancy", "quality", "missing", "present", "enhance_on"):
        assert key in body, key
    assert "result.commands" not in body
    assert body.isascii()


def test_check_model_asks_for_the_rung_its_own_row_names() -> None:
    """The disk check walks the rung table, so Check models cannot disagree.

    The pack ids come from the Needs the table generates, and the report labels
    the rung the disk was actually asked about.
    """
    args: dict[str, Any] = {
        "lab_rel": "photos/x",
        "occupancy": "klein",
        "quality": QUALITY_HIGH,
    }
    hints = hints_from_args(args)
    assert hints.quality == QUALITY_FINAL, "a retired id reaches the disk check normalized"
    assert rung_family(hints) == "klein"
    rung_packs = {need.pack for need in rung_needs("klein", QUALITY_FINAL)}
    assert len(rung_packs) == len(_rung_files("klein", QUALITY_FINAL))
    assert {need.pack for need in requirements_for(hints)} >= rung_packs
    assert rung_needs("klein", QUALITY_STANDARD) == []
    payload = run_check(args, roots=[])
    assert payload["ok"] is False
    assert payload["quality"] == QUALITY_FINAL
    # An empty root reports every file the rung names, each with the command
    # that stages it. A file two packs share is named once, never twice.
    missing = {(str(row["name"]), str(row["cmd"])) for row in payload["missing"]}
    wanted = {
        (str(spec.name or ""), need.cmd)
        for need in rung_needs("klein", QUALITY_FINAL)
        for spec in need.files
    }
    assert wanted <= missing, sorted(wanted - missing)
    assert all(name for name, _cmd in wanted)


# ---------------------------------------------------------------------------
# The stamp, and the per-graph invariant.
# ---------------------------------------------------------------------------


def test_ensure_quality_node_is_idempotent() -> None:
    """Stamping twice keeps one node, one row, and its position."""
    graph = _load("photos/still-draft")
    ensure_quality_node(graph)
    first = find_quality_node(graph)
    assert first is not None
    node_id = first["id"]
    count = len(_node_nodes(graph, QUALITY_TYPE))
    ensure_quality_node(graph)
    again = find_quality_node(graph)
    assert again is not None
    assert len(_node_nodes(graph, QUALITY_TYPE)) == count == 1
    assert again["id"] == node_id
    assert again["title"] == QUALITY_TITLE
    assert _values(again) == [QUALITY_STANDARD]
    assert graph["extra"]["lab_quality"] == {"default": QUALITY_STANDARD}
    linear = graph["extra"]["linearData"]["inputs"]
    rows = [row for row in linear if row[1] == QUALITY_WIDGET]
    assert len(rows) == 1
    assert linear[0][1] == QUALITY_WIDGET
    assert linear[0][0] == node_id


def test_ensure_quality_relabels_a_retired_stamp() -> None:
    """A graph authored before the ladder is pulled onto it, never refused.

    The recorded value goes through the normalizer, so a retired id lands on its
    rung and an unknown value on the default, and the stamp agrees with the row.
    """
    graph = _load("photos/still-draft")
    node = find_quality_node(graph)
    assert node is not None
    node["title"] = "Quality"
    node["widgets_values"] = [QUALITY_FREE_COMMERCIAL]
    graph["extra"]["lab_quality"] = {"default": QUALITY_FREE_COMMERCIAL}

    ensure_quality_node(graph)

    moved = find_quality_node(graph)
    assert moved is not None
    assert moved["title"] == QUALITY_TITLE
    assert _values(moved) == [QUALITY_FINAL]
    assert graph["extra"]["lab_quality"] == {"default": QUALITY_FINAL}

    node["widgets_values"] = ["no-such-tier"]
    ensure_quality_node(graph)
    reset = find_quality_node(graph)
    assert reset is not None and _values(reset) == [QUALITY_STANDARD]


def test_ensure_quality_keeps_required_still_first() -> None:
    """The row follows the required still pickers, so Queue cannot hide a file."""
    graph = _load("video/av/talking-head")
    ensure_quality_node(graph)
    names = [row[1] for row in graph["extra"]["linearData"]["inputs"]]
    assert names[0] == "image"
    assert names[1] == QUALITY_WIDGET
    quality = find_quality_node(graph)
    assert quality is not None
    assert graph["extra"]["linearData"]["inputs"][1][0] == quality["id"]


def test_ensure_quality_places_without_overlap() -> None:
    """The row lands clear of every node it is stamped next to."""
    busiest = max(
        lab_graph_paths(),
        key=lambda path: len(json.loads(path.read_text(encoding="utf-8")).get("nodes") or []),
    )
    graph = copy.deepcopy(json.loads(busiest.read_text(encoding="utf-8")))
    ensure_quality_node(graph)
    quality = find_quality_node(graph)
    assert quality is not None
    qx, qy = float(quality["pos"][0]), float(quality["pos"][1])
    qw, qh = 320.0, 82.0
    pad = 20.0
    qa_box = (qx - pad, qy - pad, qx + qw + pad, qy + qh + pad)
    for node in graph["nodes"]:
        if node is quality:
            continue
        pos = node.get("pos") or [0, 0]
        size = node.get("size", [200, 100])
        if isinstance(size, dict):
            width, height = float(size.get("0", 200)), float(size.get("1", 100))
        else:
            width, height = float(size[0]), float(size[1])
        box = (
            float(pos[0]) - pad,
            float(pos[1]) - pad,
            float(pos[0]) + width + pad,
            float(pos[1]) + height + pad,
        )
        hit = qa_box[0] < box[2] and qa_box[2] > box[0] and qa_box[1] < box[3] and qa_box[3] > box[1]
        assert not hit, (node.get("id"), node.get("type"))


def test_family_honors_tiers_needs_a_writable_node() -> None:
    """A combo belongs only where a rung has a widget to write.

    The family ladder is one half of the answer: an audio graph with no sampler
    and no loader infers a family that owns a ladder, yet every rung on it
    queues the graph unchanged.
    """
    sampler: dict[str, Any] = {
        "id": 1,
        "type": "KSampler",
        "pos": [0, 0],
        "size": [300, 200],
        "widgets_values": [0, "fixed", 20, 3.5, "eps", None, None],
    }
    audio_graph: dict[str, Any] = {
        "nodes": [{"id": 2, "type": "SaveAudio", "pos": [0, 0], "size": [200, 80]}, sampler],
        "extra": {"lab_app_mode": {"occupancy": "audio"}},
    }
    assert family_honors_tiers(audio_graph) is True

    no_host: dict[str, Any] = {
        "nodes": [{"id": 2, "type": "SaveAudio", "pos": [0, 0], "size": [200, 80]}],
        "extra": {"lab_app_mode": {"occupancy": "audio"}},
    }
    assert family_honors_tiers(no_host) is False

    ladderless: dict[str, Any] = {
        "nodes": [sampler],
        "extra": {"lab_app_mode": {"occupancy": "llm"}},
    }
    assert family_honors_tiers(ladderless) is False

    texture_only: dict[str, Any] = {
        "nodes": [
            {
                "id": 3,
                "type": "KSampler",
                "pos": [0, 0],
                "size": [300, 200],
                "widgets_values": [0, "fixed", 12, TRELLIS_GUIDANCE_FREE_CFG],
            }
        ],
        "extra": {"lab_app_mode": {"occupancy": "trellis"}},
    }
    assert family_honors_tiers(texture_only) is False
    assert set(OVERLAY_NODE_TYPES) == {"KSampler", "UNETLoader", "CLIPLoader", "VAELoader"}


def test_strip_quality_node_clears_the_widget_and_its_row() -> None:
    """Stripping removes the node, its App widget row, and its default stamp."""
    graph = _load("photos/still-draft")
    ensure_quality_node(graph)
    assert find_quality_node(graph) is not None
    assert graph["extra"]["lab_quality"] == {"default": QUALITY_STANDARD}

    assert strip_quality_node(graph) is True
    assert _node_nodes(graph, QUALITY_TYPE) == []
    assert "lab_quality" not in graph["extra"]
    rows = graph["extra"]["linearData"]["inputs"]
    assert QUALITY_WIDGET not in [row[1] for row in rows]
    assert find_quality_node(graph) is None
    assert strip_quality_node(graph) is False


def test_ensure_quality_strips_a_combo_no_rung_can_move() -> None:
    """An audio graph with no loader or sampler ships without a Detail row."""
    graph: dict[str, Any] = {
        "nodes": [
            {"id": 2, "type": "SaveAudio", "pos": [0, 0], "size": [200, 80]},
            {"id": 3, "type": "Note", "pos": [0, 0], "size": [200, 80]},
        ],
        "extra": {"lab_app_mode": {"occupancy": "audio", "enabled": True}},
    }
    ensure_quality_node(graph)
    assert _node_nodes(graph, QUALITY_TYPE) == []
    assert "lab_quality" not in graph["extra"]
    assert (graph["extra"].get("linearData") or {}).get("inputs", []) == []


@pytest.mark.parametrize("path", lab_graph_paths(), ids=lambda p: p.name)
def test_every_lab_graph_has_exactly_one_detail_node(path: Path) -> None:
    """One Detail node where a rung can write; none where no rung can.

    A graph whose family owns no ladder, or that holds no node the overlay can
    write, ships without the row: ``_wire_quality`` strips it so the App never
    offers a rung that queues the graph unchanged. The recorded rung is always
    selectable and always agrees with the App stamp.
    """
    graph = json.loads(path.read_text(encoding="utf-8"))
    hits = [n for n in graph.get("nodes") or [] if n.get("type") == QUALITY_TYPE]
    if not family_honors_tiers(graph):
        assert hits == [], path
        return
    assert len(hits) == 1, path
    node = hits[0]
    assert node.get("title") == QUALITY_TITLE, path
    recorded = _values(node)
    assert recorded and recorded[0] in QUALITY_CHOICES, path
    assert normalize_quality(recorded[0]) == recorded[0], path
    extra = graph.get("extra") or {}
    assert extra.get("lab_quality", {}).get("default") == recorded[0], path
    mode = extra.get("lab_app_mode") or {}
    if mode.get("enabled") is True:
        linear = extra.get("linearData") or {}
        inputs = linear.get("inputs") or []
        assert inputs, path
        names = [entry[1] for entry in inputs]
        idx = 0
        while idx < len(names) and names[idx] in {"image", "iterate", "run_summary"}:
            idx += 1
        assert names[idx] == QUALITY_WIDGET, path
        assert int(inputs[idx][0]) == int(node["id"]), path

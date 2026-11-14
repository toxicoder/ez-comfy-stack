"""Shipped-graph drift check for the Detail rung table.

Every ``workflows/_lab`` graph that a rung could actually change carries one
EZQuality combo, and a graph no rung could change carries none. The rung table
in custom_nodes/ez_quality/presets.py is what that combo writes, so a graph can
drift three ways: it holds a combo no rung can move, it records a value the node
no longer offers, or its live widgets read back as a rung the graph is not
actually on. This walks the tree once (parsed a single time per process) and
checks which graphs carry the combo, the recorded rung, the family the node
infers, and the loaders the family's rungs write.

The last checks here are the write-or-refuse contract between Python and the
browser: ``apply_to_graph`` and ``applyQuality`` read the one generated table, so
the set of applies that must refuse is a property of that table, and both sides
are held to the same list.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from _lab_paths import lab_graph_paths, lab_rel_of
from _wire_quality import QUALITY_TYPE, family_honors_tiers

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_quality.check import command_for_filename, rung_needs  # noqa: E402
from ez_quality.presets import (  # noqa: E402
    CLIP_MISTRAL,
    CLIP_NAME_INDEX,
    CLIP_TYPE_FLUX2,
    KLEIN3_BASE,
    KLEIN3_TE,
    KLEIN_DISTILLED,
    KSAMPLER_CFG_INDEX,
    KSAMPLER_STEPS_INDEX,
    LICENSE_LABEL,
    LTX_UNET,
    QUALITY_CHOICES,
    QUALITY_DRAFT,
    QUALITY_FAMILIES,
    QUALITY_FAMILY_KLEIN3,
    QUALITY_FAMILY_QWEN,
    QUALITY_FINAL,
    QUALITY_STANDARD,
    QWEN_IMAGE_NVFP4,
    QWEN_TE,
    QWEN_VAE,
    TRELLIS_UNET,
    UNET_NAME_INDEX,
    VAE_FULL,
    VAE_NAME_INDEX,
    WAN_5B_UNET,
    apply_to_graph,
    export_table,
    family_owned_fields,
    infer_occupancy,
    is_klein3_clip,
    is_klein3_unet,
    normalize_quality,
    plan_rung_writes,
    rung_refusal_reasons,
)

# presets.py indexes the name widgets; CLIPLoader[1] is the clip type slot that
# the klein rungs pin to flux2, and it has no named constant of its own.
CLIP_TYPE_WIDGET_INDEX = 1

# Per overlay field: the node type holding the widget and its widgets_values
# slot. A rung that writes a field needs that widget present to write it.
FIELD_HOSTS: dict[str, tuple[str, int]] = {
    "steps": ("KSampler", KSAMPLER_STEPS_INDEX),
    "cfg": ("KSampler", KSAMPLER_CFG_INDEX),
    "unet_name": ("UNETLoader", UNET_NAME_INDEX),
    "clip_name": ("CLIPLoader", CLIP_NAME_INDEX),
    "clip_type": ("CLIPLoader", CLIP_TYPE_WIDGET_INDEX),
    "vae_name": ("VAELoader", VAE_NAME_INDEX),
}

# The loader fields a missing file can refuse an apply over. Steps and CFG have
# no file behind them, so they cannot be the thing that is not on disk.
FILE_FIELDS: tuple[str, ...] = ("unet_name", "clip_name", "vae_name")

# The only option a refusal-test loader is offered. An empty combo list means
# "catalog unknown" to both the Python table and ez_quality.js, which skips the
# presence check; one unrelated file makes the list real so a rung file really
# is absent from it. No rung names this weight, so it never satisfies a write.
_UNRELATED_FILE = "unrelated-weight.safetensors"

# The loader fixture each family's graph is built from: weights that classify
# the graph as that family while differing from every value its rungs request,
# so a rung file is always a real swap the loader must offer. These names are
# branch fixtures only and never appear in a shipped graph.
_KLEIN_OFF_RUNG_VAE = "flux2-vae-fp16.safetensors"
_FAMILY_FIXTURES: dict[str, dict[str, str]] = {
    "klein": {
        "occupancy": "klein",
        "unet_name": KLEIN_DISTILLED,
        "clip_name": CLIP_MISTRAL,
        "vae_name": _KLEIN_OFF_RUNG_VAE,
    },
    QUALITY_FAMILY_KLEIN3: {
        "occupancy": "klein",
        "unet_name": KLEIN3_BASE,
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

_ROWS: list[tuple[str, Path, dict[str, Any]]] | None = None

_EXPORT_RE = re.compile(r"^export const EZ_QUALITY_([A-Z_]+) = ", re.MULTILINE)
_JSON_DECODER = json.JSONDecoder()
_PRESETS_JS = CUSTOM / "ez_quality" / "js" / "ez_quality_presets.js"


def _rung_table() -> dict[str, dict[str, dict[str, Any]]]:
    """The one rung table both sides read, straight off presets.py.

    Args:
        None.

    Returns:
        Mapping of family to rung to requested value per overlay field.
    """
    table = export_table()["table"]
    assert isinstance(table, dict)
    per_family: dict[str, dict[str, dict[str, Any]]] = {}
    for family, rows in table.items():
        assert isinstance(rows, dict)
        rungs: dict[str, dict[str, Any]] = {}
        for rung, row in rows.items():
            assert isinstance(row, dict)
            rungs[rung] = dict(row)
        per_family[family] = rungs
    return per_family


def _rung_files(family: str, rung: str) -> list[str]:
    """Files one rung asks a loader to select.

    Args:
        family: A QUALITY_FAMILIES id.
        rung: A QUALITY_CHOICES id.

    Returns:
        Filenames the row requests, in table order.
    """
    row = _rung_table()[family][rung]
    return [
        value
        for field, value in row.items()
        if field in FILE_FIELDS and isinstance(value, str) and value
    ]


def _js_payload() -> dict[str, Any]:
    """Decode every JSON payload the generated frontend module exports.

    Args:
        None.

    Returns:
        Mapping of export name (``table``, ``owned``, ...) to its decoded value.
    """
    body = _PRESETS_JS.read_text(encoding="utf-8")
    payload: dict[str, Any] = {}
    for match in _EXPORT_RE.finditer(body):
        value, end = _JSON_DECODER.raw_decode(body, match.end())
        assert body[end:].lstrip().startswith(";"), match.group(0)
        payload[match.group(1).lower()] = value
    return payload


def _family_graph(family: str) -> dict[str, Any]:
    """Build one graph that classifies as ``family`` and owns its loaders.

    Args:
        family: A QUALITY_FAMILIES id.

    Returns:
        A serialized-graph mapping with loaders, one KSampler, and the combo.
    """
    fixture = _FAMILY_FIXTURES[family]
    nodes: list[dict[str, Any]] = [
        {"id": 1, "type": "EZQuality", "widgets_values": [QUALITY_STANDARD]},
        {"id": 2, "type": "KSampler", "widgets_values": [7, "fixed", 20, 7.5]},
    ]
    node_id = 3
    if fixture["unet_name"]:
        nodes.append(
            {"id": node_id, "type": "UNETLoader", "widgets_values": [fixture["unet_name"]]}
        )
        node_id += 1
    if fixture["clip_name"]:
        nodes.append(
            {
                "id": node_id,
                "type": "CLIPLoader",
                "widgets_values": [fixture["clip_name"], CLIP_TYPE_FLUX2],
            }
        )
        node_id += 1
    if fixture["vae_name"]:
        nodes.append(
            {"id": node_id, "type": "VAELoader", "widgets_values": [fixture["vae_name"]]}
        )
    return {
        "nodes": nodes,
        "extra": {"lab_app_mode": {"occupancy": fixture["occupancy"]}},
    }


def _refusal(graph: dict[str, Any], rung: str) -> str | None:
    """Apply one rung with every loader file missing; report a refusal.

    The contract pins that an apply refuses when a file it must write is not in
    that loader's options, and that the row keeps its previous rung while
    nothing is renamed. It does not pin the *carrier*, so a refusal is read from
    whichever channel reports it: the reason list, a raised refusal, a returned
    status, or the caption the apply stamps onto the graph.

    The loaders are offered one option each, never an empty list: both sides
    read an empty list as "the catalog is unknown, skip the presence check", so
    "this file is not installed" only says that with another file in the list.

    Args:
        graph: Graph to mutate.
        rung: Rung id to apply.

    Returns:
        The refusal text naming every reason, or None when the apply landed.
    """
    before = json.dumps(graph, sort_keys=True)
    extra = graph.get("extra") if isinstance(graph.get("extra"), dict) else {}
    stamp_before = extra.get("lab_quality_caption") if isinstance(extra, dict) else None
    channels: list[str] = []
    catalogs: dict[str, list[str]] = {
        "available_unets": [_UNRELATED_FILE],
        "available_clips": [_UNRELATED_FILE],
        "available_vaes": [_UNRELATED_FILE],
    }
    try:
        channels.extend(rung_refusal_reasons(graph, rung, **catalogs))
    except (TypeError, AttributeError, NameError) as exc:
        raise AssertionError(f"rung_refusal_reasons broke instead of refusing: {exc!r}") from exc
    except Exception as exc:  # any carrier the table raises to refuse
        channels.append(str(exc))
    try:
        apply_to_graph(graph, rung, **catalogs)
    except (TypeError, AttributeError, NameError) as exc:
        raise AssertionError(f"apply_to_graph broke instead of refusing: {exc!r}") from exc
    except Exception as exc:  # the apply may carry the refusal itself
        channels.append(str(exc))
    else:
        live_extra = graph.get("extra") if isinstance(graph.get("extra"), dict) else {}
        stamp = live_extra.get("lab_quality_caption") if isinstance(live_extra, dict) else None
        if isinstance(stamp, str) and stamp and stamp != stamp_before:
            channels.append(stamp)
    text = " | ".join(channel for channel in channels if channel)
    if not text:
        return None
    assert json.dumps(graph, sort_keys=True) == before, (
        f"{rung} refused after it had already written widgets"
    )
    return text


def _lab_rows() -> list[tuple[str, Path, dict[str, Any]]]:
    """Return ``(lab_rel, path, graph)`` for every shipped graph, parsed once.

    Undecodable or non-object JSON is skipped the way the other lab walkers
    skip it; other tests own what the tree must contain.

    Args:
        None.

    Returns:
        Rows sorted by path.
    """
    global _ROWS
    if _ROWS is None:
        rows: list[tuple[str, Path, dict[str, Any]]] = []
        for path in lab_graph_paths():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(data, dict):
                continue
            rows.append((lab_rel_of(path), path, data))
        rows.sort(key=lambda row: row[1].as_posix())
        _ROWS = rows
    return _ROWS


def _nodes(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Node dicts of a graph, ignoring malformed entries.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        Node dicts in file order.
    """
    raw = graph.get("nodes")
    if not isinstance(raw, list):
        return []
    return [node for node in raw if isinstance(node, dict)]


def _widget(nodes: list[dict[str, Any]], node_type: str, index: int) -> Any:
    """First widget value for ``node_type`` at ``index``.

    Args:
        nodes: Graph nodes.
        node_type: Node type to read.
        index: widgets_values slot.

    Returns:
        Widget value, or None when the node or slot is absent.
    """
    for node in nodes:
        if node.get("type") != node_type:
            continue
        values = node.get("widgets_values")
        if isinstance(values, list) and len(values) > index:
            return values[index]
    return None


def _has_widget(nodes: list[dict[str, Any]], node_type: str, index: int) -> bool:
    """True when a node of ``node_type`` carries a slot at ``index``.

    A null value still counts: the overlay writes into the slot whatever it
    holds, so the slot existing is what the rung row needs.

    Args:
        nodes: Graph nodes.
        node_type: Node type to look for.
        index: widgets_values slot.

    Returns:
        True when the overlay could write that field.
    """
    for node in nodes:
        if node.get("type") != node_type:
            continue
        values = node.get("widgets_values")
        if isinstance(values, list) and len(values) > index:
            return True
    return False


def _family(nodes: list[dict[str, Any]], graph: dict[str, Any]) -> str:
    """Family the Detail node uses: occupancy, upgraded by the FLUX 3 needles.

    Args:
        nodes: Graph nodes.
        graph: Serialized Comfy graph.

    Returns:
        A QUALITY_FAMILIES id, or an unknown id the rungs treat as a no-op.
    """
    extra = graph.get("extra") if isinstance(graph.get("extra"), dict) else {}
    mode = extra.get("lab_app_mode") if isinstance(extra, dict) else None
    occupancy = str((mode or {}).get("occupancy") or "").strip()
    if is_klein3_unet(str(_widget(nodes, "UNETLoader", UNET_NAME_INDEX) or "")) or (
        is_klein3_clip(str(_widget(nodes, "CLIPLoader", CLIP_NAME_INDEX) or ""))
    ):
        return QUALITY_FAMILY_KLEIN3
    return occupancy or infer_occupancy(graph)


def _observed(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Overlay fields as the shipped widgets hold them.

    Args:
        nodes: Graph nodes.

    Returns:
        Mapping of overlay field to widget value, None when no loader is wired.
    """
    return {
        field: _widget(nodes, host, index)
        for field, (host, index) in FIELD_HOSTS.items()
    }


def test_lab_tree_is_populated() -> None:
    """The drift checks below must iterate a real tree, never an empty glob."""
    assert len(_lab_rows()) >= 600


def test_every_graph_records_a_legal_rung() -> None:
    """Each rung-movable graph carries one combo, and it records a legal rung.

    A graph whose family owns no ladder, or that holds no node the overlay can
    write, ships without a combo at all; ``_wire_quality`` strips it so the App
    never offers rows that queue unchanged.
    """
    misses: list[str] = []
    for rel, _path, graph in _lab_rows():
        nodes = _nodes(graph)
        hits = [node for node in nodes if node.get("type") == QUALITY_TYPE]
        if not family_honors_tiers(graph):
            if hits:
                misses.append(
                    f"{rel}: {len(hits)} {QUALITY_TYPE} nodes on a graph "
                    "no rung can change"
                )
            continue
        if len(hits) != 1:
            misses.append(f"{rel}: {len(hits)} {QUALITY_TYPE} nodes")
            continue
        recorded = _widget(hits, QUALITY_TYPE, 0)
        if recorded not in QUALITY_CHOICES:
            misses.append(f"{rel}: recorded rung {recorded!r}")
    assert not misses


def test_the_recorded_rung_is_the_default_everywhere() -> None:
    """No shipped graph remembers a hand-picked rung: every combo reads standard."""
    misses: list[str] = []
    for rel, _path, graph in _lab_rows():
        hits = [node for node in _nodes(graph) if node.get("type") == QUALITY_TYPE]
        if not hits:
            continue
        if _widget(hits, QUALITY_TYPE, 0) != QUALITY_STANDARD:
            misses.append(f"{rel}: records {_widget(hits, QUALITY_TYPE, 0)!r}")
    assert not misses


def test_every_graph_reads_back_as_standard() -> None:
    """Shipped widgets read back as ``standard``: the rung that writes nothing.

    ``standard`` means "leave the graph exactly as this App ships it", so every
    shipped graph sits on it and applying it there is a no-op that cannot be
    refused. A graph whose live widgets land on ``draft`` or ``final`` instead is
    a graph an author moved off the shipped recipe.
    """
    misses: list[str] = []
    for rel, _path, graph in _lab_rows():
        nodes = _nodes(graph)
        family = _family(nodes, graph)
        if not family_owned_fields(family):
            continue
        hits = [node for node in nodes if node.get("type") == QUALITY_TYPE]
        if hits:
            recorded = _widget(hits, QUALITY_TYPE, 0)
            if normalize_quality(recorded) != QUALITY_STANDARD:
                misses.append(f"{rel}: combo reads {recorded!r}")
                continue
        plan = plan_rung_writes(graph, QUALITY_STANDARD)
        observed = _observed(nodes)
        if plan.writes or plan.reasons:
            misses.append(
                f"{rel}: family {family!r} is not on standard: "
                f"writes={[w.field for w in plan.writes]} reasons={list(plan.reasons)} {observed}"
            )
    assert not misses


def test_every_sampler_ships_the_loaders_its_family_writes() -> None:
    """Every field a family rung writes has a widget to write into."""
    misses: list[str] = []
    for rel, _path, graph in _lab_rows():
        nodes = _nodes(graph)
        if not any(node.get("type") == "KSampler" for node in nodes):
            continue
        family = _family(nodes, graph)
        for field in family_owned_fields(family):
            host, index = FIELD_HOSTS[field]
            if not _has_widget(nodes, host, index):
                misses.append(f"{rel}: {family!r} writes {field}, no {host}[{index}]")
    assert not misses


def test_the_table_offers_exactly_the_three_rungs() -> None:
    """The ladder has three rows per family and no leftover legacy row."""
    table = _rung_table()
    assert set(table) == set(QUALITY_FAMILIES)
    for family, rows in table.items():
        assert set(rows) == set(QUALITY_CHOICES), family


def test_the_middle_rung_writes_nothing_on_every_family() -> None:
    """``standard`` is an empty row everywhere, so the default cannot drift."""
    for family, rows in _rung_table().items():
        row = rows[QUALITY_STANDARD]
        assert all(value is None for value in row.values()), (family, row)


def test_the_ladder_is_the_one_table_the_browser_reads() -> None:
    """The generated frontend module is presets.py rendered, so JS cannot drift."""
    payload = _js_payload()
    assert payload["table"] == _rung_table()
    assert payload["choices"] == list(QUALITY_CHOICES)


def _must_refuse(family: str, rung: str) -> bool:
    """Decide, from the table alone, whether one apply has to be refused.

    Args:
        family: A QUALITY_FAMILIES id.
        rung: A QUALITY_CHOICES id.

    Returns:
        True when the rung names a file a loader cannot offer, or when the
        family carries no ladder at all for a named rung to write.
    """
    if rung == QUALITY_STANDARD:
        return False
    return bool(_rung_files(family, rung)) or not family_owned_fields(family)


def test_the_shared_refusal_set_is_the_rungs_that_name_a_file() -> None:
    """Python and JS read one table, so the set that must refuse is a property of it.

    A rung that asks a loader to select a file the loader does not offer refuses,
    and so does a named rung on a family that carries no ladder: that combo is
    stripped from the App, so asking for it is the contract's family mismatch. A
    rung with no file behind it (every steps-only family, and ``standard``)
    cannot refuse. ``applyQuality`` reads the same generated rows, so this is the
    list both sides are held to.
    """
    expected = {
        (family, rung)
        for family in QUALITY_FAMILIES
        for rung in QUALITY_CHOICES
        if _must_refuse(family, rung)
    }
    refused: set[tuple[str, str]] = set()
    for family in QUALITY_FAMILIES:
        for rung in QUALITY_CHOICES:
            if _refusal(_family_graph(family), rung) is not None:
                refused.add((family, rung))
    assert refused == expected


def test_a_refusal_names_the_missing_file_and_the_host_command() -> None:
    """Every file a refusal names is one the checker can hand a command for.

    The Detail row and the Check models card answer two halves of one question:
    the row refuses and says which weight it could not write, the card names the
    verb that stages it. "Which command owns this filename" lives exactly once,
    in ``ez_quality.check.command_for_filename``, and it reads the catalog's own
    file names; a refusal string that re-listed commands would be a second copy
    free to drift from the card the operator is looking at. So the pair is
    asserted here instead: the refusal must name the file, and that same file
    must resolve to a real host command, never to the catch-all answer.
    """
    reason = _refusal(_family_graph("klein"), QUALITY_FINAL)
    assert reason is not None, "klein final names weights, so it must refuse"
    staged = {
        spec.name: need.cmd for need in rung_needs("klein", QUALITY_FINAL) for spec in need.files
    }
    for wanted in _rung_files("klein", QUALITY_FINAL):
        assert wanted in reason, (wanted, reason)
        command = staged.get(wanted, "")
        assert command.startswith("bazelisk run //"), (wanted, command)


def test_a_refusal_never_touches_a_weight_it_could_not_verify() -> None:
    """A refused apply leaves every loader and sampler exactly as authored."""
    graph = _family_graph("klein")
    before = json.loads(json.dumps(graph))
    assert _refusal(graph, QUALITY_DRAFT) is not None
    assert graph == before


def test_a_rung_with_no_files_behind_it_never_refuses() -> None:
    """Steps-only rungs and the middle rung have nothing missing, so they land."""
    steps_only: list[tuple[str, str]] = []
    for family in ("wan", "ltx", "film", "audio", "trellis"):
        for rung in (QUALITY_DRAFT, QUALITY_FINAL):
            if not _rung_files(family, rung):
                steps_only.append((family, rung))
    assert steps_only, "the table has no steps-only rung to check"
    for family, rung in steps_only:
        assert _refusal(_family_graph(family), rung) is None, (family, rung)
    for family in QUALITY_FAMILIES:
        assert _refusal(_family_graph(family), QUALITY_STANDARD) is None, family


def test_every_rung_file_is_one_this_app_can_stage() -> None:
    """No rung points at a weight the staging story cannot name."""
    for family in QUALITY_FAMILIES:
        for rung in QUALITY_CHOICES:
            for wanted in _rung_files(family, rung):
                assert command_for_filename(wanted), (family, rung, wanted)
    for family in QUALITY_FAMILIES:
        if family_owned_fields(family):
            assert LICENSE_LABEL[family], family

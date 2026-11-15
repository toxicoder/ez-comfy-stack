"""Operator copy and App panel rows for the NVIDIA lab graphs.

Not collected by pytest (leading underscore). ``_build_nvidia_lab_apps`` emits
from this table and ``test_nvidia_lab_graphs`` asserts against it, so the
sentence an App shows and the sentence a test checks cannot drift.

The catalog (``custom_nodes/ez_nvidia_lab/catalog.json``, read through
``nvidia_lab.load_catalog``) is the only source of a row's facts: status,
licenses, artifact, footprint, commands. Nothing here repeats one. What lives
here is only what the catalog does not carry - the one-line App description,
the shape of the on-canvas note, the canvas titles, and which widgets the App
panel surfaces.

Occupancy is ``none`` for every row in this tier on purpose: the GPU work runs
outside the Comfy process through the operator CLI, so the one-heavy-job XOR is
the CLI's rule to enforce (``require_heavy_confirm`` plus the occupancy refusal
in ``scripts/utilities/nvidia-lab.sh``), not a graph-level gate.
"""

from __future__ import annotations

from dataclasses import dataclass

from nvidia_lab import Catalog, Tool, opt_in

LANE = "labs"
SUBDIR = "nvidia"
OCCUPANCY = "none"
CLI_VERB = "nvidia-lab"

NOTE_TYPE = "Note"
NOTE_TITLE = "Operator note"
CATALOG_TYPE = "EZNvidiaLabCatalog"
PREFLIGHT_TYPE = "EZNvidiaLabPreflight"
JOB_TYPE = "EZNvidiaLabJob"
VERDICT_TYPE = "EZNvidiaLabVerdict"

CANVAS_TITLES: dict[str, str] = {
    NOTE_TYPE: NOTE_TITLE,
    PREFLIGHT_TYPE: "Preflight",
    JOB_TYPE: "Run the row",
    VERDICT_TYPE: "Verdict",
    CATALOG_TYPE: "Tier table",
}

TIER_DETAIL_LABEL = "Tier detail"
TIER_DETAIL_DESCRIPTION = (
    "table prints one aligned line per row. list prints a block per row with "
    "arm64, GB10, install, and footprint."
)
ROW_ID_LABEL = "Row id"


@dataclass(frozen=True)
class PanelRow:
    """One ``linearData.inputs`` row the App panel renders.

    Attributes:
        node_type: Canvas node class the row binds.
        widget: Widget name on that node.
        label: App panel label.
        description: App panel help text.
    """

    node_type: str
    widget: str
    label: str
    description: str

    def as_input_spec(self) -> tuple[str, str, dict[str, str]]:
        """Return the ``(node ref, widget, config)`` tuple ``stamp_app_mode`` takes.

        Returns:
            The spec tuple with the label and description config.
        """
        return (
            self.node_type,
            self.widget,
            {"label": self.label, "description": self.description},
        )


@dataclass(frozen=True)
class GraphSpec:
    """Everything one NVIDIA lab graph needs beyond the catalog row itself.

    Attributes:
        tool: The catalog row this graph is the card for.
        node_types: Canvas node classes, in read order, note first.
        description: ``extra.lab_description`` - the browsed-list line.
        note: ``extra.lab_note`` and the operator note body, same text.
        panel_rows: The App panel's input rows.
        output_types: Node classes listed in ``linearData.outputs``.
    """

    tool: Tool
    node_types: tuple[str, ...]
    description: str
    note: str
    panel_rows: tuple[PanelRow, ...]
    output_types: tuple[str, ...]

    @property
    def graph_rel(self) -> str:
        """Return the ``_lab``-relative id the catalog pins for this row.

        Returns:
            ``labs/nvidia/<id>``.
        """
        return self.tool.graph

    @property
    def canvas_title(self) -> str:
        """Return the canvas title for this row's card node.

        Returns:
            The title from :data:`CANVAS_TITLES`.
        """
        if JOB_TYPE in self.node_types:
            return CANVAS_TITLES[JOB_TYPE]
        return CANVAS_TITLES[VERDICT_TYPE]

    @property
    def runs_a_job(self) -> bool:
        """Return whether this graph carries the CLI job card.

        Returns:
            True when the row's ``nodes`` list names the job node.
        """
        return JOB_TYPE in self.node_types


def node_types_for(catalog: Catalog, tool: Tool) -> tuple[str, ...]:
    """Return the canvas node classes for one row, note first.

    The row's own ``nodes`` list decides the card: a row that names the job node
    gets it, every other row gets the verdict card. The preflight and the tier
    table are on every graph, whichever card the catalog authored.

    Args:
        catalog: The parsed catalog, used for the opt-in cross-check.
        tool: The row to build for.

    Returns:
        Node classes in read order: preflight, card, table.

    Raises:
        ValueError: the row names neither card, or names the job node while its
            status is not ``opt-in``.
    """
    named = list(tool.nodes)
    has_job = JOB_TYPE in named
    has_verdict = VERDICT_TYPE in named
    if has_job == has_verdict:
        raise ValueError(
            f"{tool.id}.nodes: expected exactly one of {JOB_TYPE} or "
            f"{VERDICT_TYPE}, got {named}"
        )
    if has_job and tool.id not in {row.id for row in opt_in(catalog)}:
        raise ValueError(f"{tool.id}: {JOB_TYPE} is reserved for opt-in rows")
    card = JOB_TYPE if has_job else VERDICT_TYPE
    return (PREFLIGHT_TYPE, card, CATALOG_TYPE)


def optional_unwired_for(node_types: tuple[str, ...]) -> tuple[str, ...]:
    """Return the card classes this tier ships unwired on purpose.

    Every card in the tier is a terminal informational ``OUTPUT_NODE``: it prints
    into the Queue log and offers no socket another node could read, so nothing
    on these graphs is wired to anything. The auditor's unwired-node rule still
    applies, so the generator declares each card it emits through
    ``extra.lab_optional_unwired`` (the same mechanism the ``3d`` lane declares
    ``EZSceneLayout`` with). The operator note is exempt on its own, as is the
    disk check the stamper adds after this list is taken.

    Args:
        node_types: The row's canvas classes, as :func:`node_types_for` returns
            them (note first is not part of this list).

    Returns:
        Sorted node class names for ``extra.lab_optional_unwired``.
    """
    return tuple(sorted({ntype for ntype in node_types if ntype != NOTE_TYPE}))


def _weights_text(tool: Tool) -> str:
    """Render the row's weight list for the note.

    Args:
        tool: The catalog row.

    Returns:
        Comma-joined ``repo/file@GB`` labels, or ``none``.
    """
    if not tool.weights:
        return "none"
    return ", ".join(weight.label() for weight in tool.weights)


def _verb_lines(tool: Tool, *, has_job: bool) -> list[str]:
    """Return the operator CLI lines the note lists.

    Args:
        tool: The catalog row.
        has_job: Whether the graph carries the job card.

    Returns:
        Indented ``bazelisk run //:manage -- nvidia-lab ...`` lines.
    """
    lines = [
        f"  bazelisk run //:manage -- {CLI_VERB} status",
        f"  bazelisk run //:manage -- {CLI_VERB} plan {tool.id}",
    ]
    if tool.status == "opt-in":
        lines.append(f"  bazelisk run //:manage -- {CLI_VERB} install {tool.id}")
    if has_job and tool.cmd:
        lines.append(f"  {tool.cmd}")
    if has_job:
        lines.append(
            f"  bazelisk run //:manage -- {CLI_VERB} run {tool.id} "
            "--input <path> [--params <json>]"
        )
    return lines


def note_text(tool: Tool, *, tier_size: int) -> str:
    """Build ``extra.lab_note`` for one row.

    Args:
        tool: The catalog row.
        tier_size: How many rows the catalog ships, quoted in the note.

    Returns:
        The markdown note body, ASCII only.
    """
    has_job = JOB_TYPE in tool.nodes
    card_step = (
        "2. Set the input path and the params JSON on the job card in graph "
        "view, then Queue to hand the row to the CLI. The card refuses a row "
        "whose status is not opt-in before anything runs."
        if has_job
        else (
            "2. The verdict card prints the blocking reason and the sentence "
            "that would reopen the row."
        )
    )
    lines: list[str] = [
        f"## {tool.graph}",
        "",
        f"{tool.title} - {tool.task}",
        "",
        (
            f"Status: {tool.status}. Install: {tool.install}. Artifact: "
            f"{tool.artifact}. Arm64: {tool.arm64}. GB10: {tool.gb10}. "
            f"Comfy shape: {tool.comfy_shape}."
        ),
        f"Input: {tool.input}",
        f"Output: {tool.output}",
        (
            f"Licenses: code {tool.code_license}. Weights "
            f"{tool.weights_license}. Commercial use {tool.commercial_use}."
        ),
        (
            f"Footprint: {tool.vram_gb} GB VRAM, {tool.disk_gb} GB disk. "
            f"Weights: {_weights_text(tool)}."
        ),
        f"Artifact ref: {tool.artifact_ref or 'none published'}",
        f"Upstream: {tool.upstream}",
        f"Also: {', '.join(tool.see_also) or 'none'}",
        f"Sources: {', '.join(tool.sources) or 'none'}",
        "",
        (
            "Nothing in this graph touches the GPU. The row's work runs "
            "outside the Comfy process through the operator CLI, so the App "
            "claims no occupancy and stops no heavy job: the one-heavy-job "
            "rule is the CLI's to enforce, next to the heavy confirm and the "
            "headroom preflight."
        ),
        "",
        "Operator verbs (host shell):",
        *_verb_lines(tool, has_job=has_job),
        "",
        "Canvas:",
        (
            "1. Preflight prints whether this Spark could run the row today - "
            "the catalog row, an aarch64 host, the binary that row's install "
            "kind needs, and the artifact ref."
        ),
        card_step,
        (
            f"3. The tier table prints all {tier_size} rows with their status "
            "and licenses."
        ),
        "",
        f"Gate notes: {tool.gate_notes}",
        f"Reopen: {tool.reopen}",
        f"Verify: {tool.verify}",
    ]
    return "\n".join(lines)


def description_text(tool: Tool) -> str:
    """Build ``extra.lab_description`` for one row.

    Args:
        tool: The catalog row.

    Returns:
        The one-line browsed-list description.
    """
    card = (
        "the CLI job card"
        if JOB_TYPE in tool.nodes
        else "the verdict card"
    )
    return (
        f"{tool.title} ({tool.status}) - {tool.task} NVIDIA lab card: "
        f"preflight, {card}, and the whole tier table on one canvas."
    )


def panel_rows_for(tool: Tool) -> tuple[PanelRow, ...]:
    """Return the App panel rows for one row.

    Only ``OUTPUT_NODE`` classes are surfaced: the preflight and the job card
    report into nothing, so a panel row on one would be a control the graph
    never reads. The job card's widgets stay graph-view only, which the note
    says.

    Args:
        tool: The catalog row.

    Returns:
        Panel rows in panel order.
    """
    rows = [
        PanelRow(
            node_type=CATALOG_TYPE,
            widget="detail",
            label=TIER_DETAIL_LABEL,
            description=TIER_DETAIL_DESCRIPTION,
        )
    ]
    if VERDICT_TYPE in tool.nodes:
        rows.append(
            PanelRow(
                node_type=VERDICT_TYPE,
                widget="tool_id",
                label=ROW_ID_LABEL,
                description=(
                    f"Catalog row this card answers for. Pinned to {tool.id}; "
                    "another id prints that row's verdict instead."
                ),
            )
        )
    return tuple(rows)


def spec_for(catalog: Catalog, tool: Tool) -> GraphSpec:
    """Return the graph spec for one catalog row.

    Args:
        catalog: The parsed catalog, for the tier size and the opt-in check.
        tool: The row to build for.

    Returns:
        The spec the generator assembles from.
    """
    node_types = node_types_for(catalog, tool)
    outputs = tuple(
        ntype for ntype in node_types if ntype in {CATALOG_TYPE, VERDICT_TYPE}
    )
    return GraphSpec(
        tool=tool,
        node_types=node_types,
        description=description_text(tool),
        note=note_text(tool, tier_size=len(catalog.tools)),
        panel_rows=panel_rows_for(tool),
        output_types=outputs,
    )


def specs(catalog: Catalog) -> list[GraphSpec]:
    """Return one spec per catalog row, in catalog order.

    Args:
        catalog: The parsed catalog.

    Returns:
        One :class:`GraphSpec` per row.
    """
    return [spec_for(catalog, tool) for tool in catalog.tools]

"""ComfyUI graph-document vocabulary (UI format and API prompt format).

Two shapes of the same graph circulate in this repo and they are not
interchangeable:

``ComfyUiGraph``
    What ships in ``workflows/_lab/<lane>/<id>.json`` and what the
    LiteGraph frontend edits. ``nodes`` is a list; edges live in ``links``
    as ``[link_id, origin_id, origin_slot, target_id, target_slot, type]``.
    Readers find a node by scanning ``nodes`` or by using
    :func:`ui_nodes_by_id`.

``ComfyApiGraph``
    What ``POST /prompt`` accepts, and what the quality, forge, and clip
    builders rewrite in place. Nodes are keyed by node id string, and every
    entry of ``inputs`` is either a literal widget value or a link written
    as ``[node_id, slot]``.

:data:`WidgetValue` is a closed union over JSON scalars plus nested lists
because a widget can only carry what a graph file can hold. Node ids are a
``NewType``: the UI format keys nodes by a string while several builders
carry ``int`` ids, and confusing the two silently misses a node. Build one
with :func:`as_node_id` when it comes from ``int`` or from parsed JSON.
"""

from __future__ import annotations

from typing import NewType, NotRequired, TypedDict, TypeAlias

from .json_value import Json, JsonObject, JsonScalar

NodeId = NewType("NodeId", str)
"""Node id as it appears in a graph file (always the string form)."""

NodeClass = NewType("NodeClass", str)
"""``class_type`` / UI ``type`` - the registered Comfy node class name."""

SocketName = NewType("SocketName", str)
"""Named input or output socket on a node."""

SlotIndex: TypeAlias = int
"""Zero-based socket index within a node's inputs or outputs."""

WidgetIndex: TypeAlias = int
"""Index into a node's ``widgets_values`` list."""

WidgetValue: TypeAlias = "JsonScalar | list[WidgetValue]"
"""One ``widgets_values`` entry (scalars nest for combo-of-list widgets)."""

WidgetsValues: TypeAlias = list[WidgetValue]
"""A node's whole ``widgets_values`` list, in widget order."""

NodeInput: TypeAlias = "WidgetValue | list[NodeInput]"
"""An API-graph input: a literal widget value, or a ``[node_id, slot]`` link."""

LinkRef: TypeAlias = tuple[NodeId, SlotIndex]
"""A resolved link: source node plus source slot."""

ComfyUiLink: TypeAlias = list[int | str]
"""One UI-graph link row: ``[link_id, origin_id, origin_slot, target_id,
target_slot, type]``."""


class ComfyNodeMeta(TypedDict, total=False):
    """API-graph ``_meta`` block (frontend-only hints Comfy ignores)."""

    title: str
    """Canvas title shown instead of the class name."""


class ComfyApiNode(TypedDict):
    """One node of an API prompt graph (``POST /prompt`` payload)."""

    class_type: NodeClass
    """Registered node class, e.g. ``KSampler``."""

    inputs: dict[SocketName, NodeInput]
    """Socket name to literal widget value or ``[node_id, slot]`` link."""

    _meta: NotRequired[ComfyNodeMeta]
    """Frontend hints; Comfy does not read them at queue time."""


ComfyApiGraph: TypeAlias = dict[NodeId, ComfyApiNode]
"""An API prompt graph: node id string to node."""


class ComfyUiSocket(TypedDict, total=False):
    """One entry of a UI node's ``inputs`` or ``outputs`` list.

    Input rows carry ``link`` (one id or ``None``); output rows carry
    ``links`` (a list) plus ``slot_index``. Both share this record because
    a serialized node mixes them.
    """

    name: str
    """Socket label."""

    type: str
    """Comfy type string, e.g. ``MODEL``."""

    link: int | None
    """Single incoming link id (input rows)."""

    links: list[int] | None
    """Outgoing link ids (output rows)."""

    slot_index: int
    """Slot position when the frontend records it."""

    widget: JsonObject
    """Inline widget descriptor for converted input-widget slots."""


class ComfyUiNode(TypedDict, total=False):
    """One node of a shipped ``_lab`` graph (LiteGraph serialization)."""

    id: int
    """Numeric node id; stringify with :func:`as_node_id` for a map key."""

    type: str
    """Registered node class name."""

    title: str
    """Canvas title."""

    mode: int
    """LiteGraph node mode (0 always, 2 muted, 4 bypass)."""

    order: int
    """Execution order hint the frontend recomputes."""

    pos: list[float]
    """``[x, y]`` canvas position."""

    size: list[float]
    """``[width, height]`` canvas size."""

    flags: JsonObject
    """LiteGraph boolean flags."""

    properties: JsonObject
    """LiteGraph node properties."""

    inputs: list[ComfyUiSocket]
    """Input socket rows."""

    outputs: list[ComfyUiSocket]
    """Output socket rows."""

    widgets_values: WidgetsValues
    """Widget values in widget order."""


class ComfyUiGroup(TypedDict, total=False):
    """One named group box in a shipped graph."""

    id: int
    """Group id."""

    title: str
    """Group title (named SHOT / Beat / RACK groups shift as blocks)."""

    bounding: list[float]
    """``[x, y, width, height]``."""

    color: str
    """Canvas colour."""

    font_size: int
    """Title font size."""

    flags: JsonObject
    """LiteGraph group flags."""


class ComfyGraphExtra(TypedDict, total=False):
    """Lab metadata under ``extra`` in a shipped graph.

    ``lab_rel`` is the unique ``_lab``-relative id and ``workflowRenderer-
    Version`` must stay ``Vue-corrected``; both are load-bearing for the
    docs generators and the lab catalog.
    """

    lab_rel: str
    """Unique ``_lab``-relative graph id."""

    lab_note: str
    """Operator note rendered on the header node."""

    lab_description: str
    """One-paragraph graph description for the catalog."""

    lab_quality: str
    """Quality preset id the graph ships with."""

    lab_profile: str
    """Resource profile id."""

    lab_app_mode: str
    """Studio App mode id when the graph is an App."""

    lab_flux_tier: str
    """Klein tier pin for stills Apps."""

    lab_optional_unwired: str
    """Marker for intentionally unwired optional inputs."""

    linearData: Json
    """linearData widget payload written by the clip builders."""

    linearMode: Json
    """linearData mode marker."""

    workflowRendererVersion: str
    """Renderer stamp; ``Vue-corrected`` is the canonical value."""

    ds: Json
    """Designer state blob the frontend round-trips."""


class ComfyUiGraph(TypedDict, total=False):
    """A shipped ``workflows/_lab/<lane>/<id>.json`` document."""

    id: str
    """Graph id (the file stem)."""

    revision: int
    """Document revision counter."""

    version: int
    """LiteGraph serialization version."""

    last_node_id: int
    """Highest node id the frontend has issued."""

    last_link_id: int
    """Highest link id the frontend has issued."""

    nodes: list[ComfyUiNode]
    """Nodes in file order."""

    links: list[ComfyUiLink]
    """Edge rows; empty when nothing is wired."""

    groups: list[ComfyUiGroup]
    """Named group boxes."""

    config: JsonObject
    """Frontend per-graph config."""

    extra: ComfyGraphExtra
    """Lab metadata."""


ComfyReturn: TypeAlias = tuple[object, ...]
"""A node ``FUNCTION`` return: one slot per entry of ``RETURN_TYPES``."""


class ComfyUiResult(TypedDict):
    """An ``OUTPUT_NODE`` payload (preview images, text, audio)."""

    ui: list[JsonObject]
    """Frontend display blocks."""

    result: ComfyReturn
    """The ordinary return tuple that continues the graph."""


WidgetConstraint: TypeAlias = (
    str | int | float | bool | list[str] | list[int] | JsonObject
)
"""One widget's constraint map or combo list, per Comfy's widget tuple."""

WidgetSpec: TypeAlias = tuple[str, WidgetConstraint]
"""``INPUT_TYPES`` entry: ``(Comfy type, constraint)``."""

WidgetMap: TypeAlias = dict[SocketName, WidgetSpec]
"""One ``required`` / ``optional`` section of an ``INPUT_TYPES`` payload."""


class InputTypeSections(TypedDict, total=False):
    """The section map a node's ``INPUT_TYPES`` builds.

    Producers may annotate the dict they assemble with this; the returned
    payload stays :data:`ez_common.protocols.ComfyInputTypes`, which is the
    open map Comfy itself documents.
    """

    required: WidgetMap
    """Widgets the user must supply."""

    optional: WidgetMap
    """Widgets Comfy fills with a default."""

    hidden: dict[str, tuple[str, ...]]
    """Frontend-injected values such as ``prompt`` and ``unique_id``."""


def as_node_id(value: object) -> NodeId:
    """Coerce a node id from JSON or an ``int`` literal into a :data:`NodeId`.

    The UI format keys nodes by string while builders carry ``int`` ids; this
    is the one place that difference is allowed to collapse.

    Args:
        value: ``int``, ``str``, or a parsed JSON scalar.

    Returns:
        The string form of the id.
    """
    return NodeId(str(value))


def ui_nodes_by_id(graph: ComfyUiGraph) -> dict[NodeId, ComfyUiNode]:
    """Index a UI graph's node list by id.

    Args:
        graph: Parsed ``_lab`` graph document.

    Returns:
        Node id to node; a node without an ``id`` key is skipped.
    """
    indexed: dict[NodeId, ComfyUiNode] = {}
    for node in graph.get("nodes", []):
        if "id" in node:
            indexed[as_node_id(node["id"])] = node
    return indexed


def api_link_ref(source_node: NodeId, slot: SlotIndex) -> list[NodeId | SlotIndex]:
    """Build the ``[node_id, slot]`` link form an API graph expects.

    Args:
        source_node: Node that produces the value.
        slot: Output slot on that node.

    Returns:
        A two-element list, ready for an ``inputs`` value.
    """
    return [source_node, slot]


def api_link_parts(value: NodeInput) -> LinkRef | None:
    """Read a ``[node_id, slot]`` link out of an API-graph input.

    Args:
        value: The value stored under an ``inputs`` key.

    Returns:
        Source node and slot, or ``None`` when the value is a literal
        widget value rather than a link.
    """
    if (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[0], str)
        and isinstance(value[1], int)
    ):
        return (NodeId(value[0]), value[1])
    return None


NodeRegistry: TypeAlias = dict[str, type[object]]
"""``NODE_CLASS_MAPPINGS``: registry name to node class."""

__all__ = [
    "ComfyApiGraph",
    "ComfyApiNode",
    "ComfyGraphExtra",
    "ComfyNodeMeta",
    "ComfyReturn",
    "ComfyUiGraph",
    "ComfyUiLink",
    "ComfyUiNode",
    "ComfyUiResult",
    "ComfyUiSocket",
    "InputTypeSections",
    "LinkRef",
    "NodeClass",
    "NodeInput",
    "NodeId",
    "NodeRegistry",
    "SocketName",
    "WidgetConstraint",
    "WidgetIndex",
    "WidgetMap",
    "WidgetSpec",
    "WidgetsValues",
    "api_link_parts",
    "api_link_ref",
    "as_node_id",
    "ui_nodes_by_id",
]

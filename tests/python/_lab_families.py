"""One model stack per lab graph: the shared vocabulary for the stack gate.

Hermetic: stdlib only. A lab graph is one App on the canvas, and an App may
drive exactly one model stack. Within a stack the Quality combo swaps weights
(Klein 4B -> Klein 9B, Qwen-Image -> Qwen-Image turbo); across stacks the answer
is a second App with the same job, never a combo that reaches both. This module
names the stacks and reads the ones a graph really pins, so the auditor, the
pytest gate, and the docs table all agree on what "one stack" means.

The stack of a graph comes from what it loads, not from what its note claims:
the loader widgets are the truth and ``extra.lab_app_mode.occupancy`` is the
claim under test.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

# ---------------------------------------------------------------------------
# Stacks
# ---------------------------------------------------------------------------

FAMILY_KLEIN = "klein"
FAMILY_KLEIN3 = "klein3"
FAMILY_QWEN = "qwen"
FAMILY_WAN = "wan"
FAMILY_LTX = "ltx"
FAMILY_TRELLIS = "trellis"
FAMILY_AUDIO = "audio"

# Stacks an App can own. Order is the order a report lists them in.
FAMILIES: tuple[str, ...] = (
    FAMILY_KLEIN,
    FAMILY_KLEIN3,
    FAMILY_QWEN,
    FAMILY_WAN,
    FAMILY_LTX,
    FAMILY_TRELLIS,
    FAMILY_AUDIO,
)

# A graph with no stack pin at all: a writers'-room desk, a dub, an album zip.
FAMILY_NONE = "none"

# Loader node types that carry a weight filename in their widgets. Comfy core
# loaders plus the vision-encoder loader the TRELLIS chain uses.
LOADER_TYPES: tuple[str, ...] = (
    "UNETLoader",
    "CLIPLoader",
    "VAELoader",
    "CheckpointLoaderSimple",
    "CLIPVisionLoader",
)

# Filename needles per stack, most specific first so a shared substring cannot
# steal a pin from the stack that owns it. Matched case-insensitively.
_STACK_NEEDLES: tuple[tuple[str, tuple[str, ...]], ...] = (
    # Qwen-Image 2.1 stills: its own transformer, its Qwen3VL-8B encoder, its VAE.
    (FAMILY_QWEN, ("qwen_image_2.1", "qwen3vl_8b")),
    # FLUX 3 Image Klein: its own transformer plus the Qwen3VL-4B encoder it ships with.
    (FAMILY_KLEIN3, ("flux3-image-klein", "qwen3vl_4b")),
    # FLUX.2 Klein (4B and 9B) with the Qwen3 / Mistral encoders and the FLUX.2 VAE.
    (
        FAMILY_KLEIN,
        ("flux-2-klein", "flux2_dev", "qwen_3_4b", "qwen_3_8b", "mistral_3_small_flux2"),
    ),
    (FAMILY_WAN, ("wan2.2", "wan2.1", "wan_2.1", "wan22", "vace", "umt5_xxl")),
    (FAMILY_LTX, ("ltx-2.5", "ltx_2.5", "ltxv", "gemma4-12b-with-proj-ltx")),
    (FAMILY_TRELLIS, ("trellis_2", "trellis-2", "dino_v3")),
    (FAMILY_AUDIO, ("ace_step", "ace-step", "kokoro")),
)

# Weights more than one stack legitimately loads. They name no stack on their
# own, so they never create a second stack in an otherwise single-stack graph.
# flux2-vae and the small-decoder VAE serve both FLUX.2 Klein and FLUX 3 Klein.
_SHARED_NEEDLES: tuple[str, ...] = (
    "flux2-vae",
    "flux2_vae",
    "full_encoder_small_decoder",
)

# A filename too generic to name a stack on its own (a Comfy-repackaged VACE
# drop lands as diffusion_pytorch_model.safetensors). It is reported as a pin
# but cannot decide a stack; the graph still has to resolve to one stack.
_AMBIGUOUS_NAMES: frozenset[str] = frozenset({"diffusion_pytorch_model.safetensors"})

# Weight extensions a loader widget can hold.
_WEIGHT_SUFFIXES: tuple[str, ...] = (
    ".safetensors",
    ".ckpt",
    ".pt",
    ".pth",
    ".bin",
    ".gguf",
)

# Occupancy (extra.lab_app_mode.occupancy) -> the stacks it may host. The three
# still stacks share the klein occupancy slot, which is exactly why the stack is
# read from the pinned weights and not from occupancy.
OCCUPANCY_STACKS: Mapping[str, frozenset[str]] = {
    "klein": frozenset({FAMILY_KLEIN, FAMILY_KLEIN3, FAMILY_QWEN}),
    "wan": frozenset({FAMILY_WAN}),
    "ltx": frozenset({FAMILY_LTX}),
    "film": frozenset({FAMILY_LTX}),
    "audio": frozenset({FAMILY_AUDIO}),
    "trellis": frozenset({FAMILY_TRELLIS}),
    "none": frozenset(),
    "llm": frozenset(),
}

# Stacks whose Quality ladder swaps weights, so their graphs carry loaders.
# wan / ltx / film / audio / trellis ladder on steps only, which is why a loader
# is expected there too but a weight swap is not.
_WEIGHT_SWAP_STACKS: frozenset[str] = frozenset(
    {FAMILY_KLEIN, FAMILY_KLEIN3, FAMILY_QWEN}
)


# ---------------------------------------------------------------------------
# Reading a pin
# ---------------------------------------------------------------------------


def weight_files(values: Iterable[Any]) -> list[str]:
    """Return the weight filenames in one loader's widget list.

    Args:
        values: ``widgets_values`` from a node dict.

    Returns:
        Widget strings that look like model files, in widget order.
    """
    found: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        name = value.strip().replace("\\", "/").rsplit("/", 1)[-1]
        if name.lower().endswith(_WEIGHT_SUFFIXES):
            found.append(name)
    return found


def stack_of_pin(name: str) -> str | None:
    """Return the stack one weight filename belongs to.

    Args:
        name: Weight filename as a loader widget holds it.

    Returns:
        A name from FAMILIES, FAMILY_NONE for a shared or ambiguous weight, or
        None when no stack claims the name at all.
    """
    blob = name.lower()
    if blob in _AMBIGUOUS_NAMES:
        return FAMILY_NONE
    for family, needles in _STACK_NEEDLES:
        if any(needle in blob for needle in needles):
            return family
    if any(needle in blob for needle in _SHARED_NEEDLES):
        return FAMILY_NONE
    return None


def graph_pins(graph: Mapping[str, Any]) -> list[tuple[str, str, str]]:
    """Return every (node_id, node_type, filename) loader pin in a graph.

    Args:
        graph: Parsed lab JSON.

    Returns:
        One tuple per weight widget, in node order.
    """
    pins: list[tuple[str, str, str]] = []
    for node in graph.get("nodes") or []:
        ntype = str(node.get("type") or "")
        if ntype not in LOADER_TYPES:
            continue
        node_id = str(node.get("id"))
        for name in weight_files(node.get("widgets_values") or []):
            pins.append((node_id, ntype, name))
    return pins


def graph_stacks(graph: Mapping[str, Any]) -> set[str]:
    """Return the distinct stacks a graph's loader pins name.

    Shared weights (flux2-vae) and ambiguous names contribute no stack, so a
    FLUX 3 graph that also loads flux2-vae stays a one-stack graph.

    Args:
        graph: Parsed lab JSON.

    Returns:
        A subset of FAMILIES; empty for a graph with no stack-bearing pin.
    """
    stacks: set[str] = set()
    for _, _, name in graph_pins(graph):
        stack = stack_of_pin(name)
        if stack and stack != FAMILY_NONE:
            stacks.add(stack)
    return stacks


def graph_occupancy(graph: Mapping[str, Any]) -> str:
    """Return the occupancy the graph claims, or "" when it claims none.

    Args:
        graph: Parsed lab JSON.

    Returns:
        ``extra.lab_app_mode.occupancy`` as a lowercase string.
    """
    extra = graph.get("extra") or {}
    app = extra.get("lab_app_mode") or {}
    return str(app.get("occupancy") or "").strip().lower()


def unclaimed_pins(graph: Mapping[str, Any]) -> list[tuple[str, str, str]]:
    """Return loader pins no stack claims, which no App should ship.

    Args:
        graph: Parsed lab JSON.

    Returns:
        (node_id, node_type, filename) for every pin that names no stack.
    """
    unknown: list[tuple[str, str, str]] = []
    for node_id, ntype, name in graph_pins(graph):
        if stack_of_pin(name) is None:
            unknown.append((node_id, ntype, name))
    return unknown


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------


def stack_violations(graph: Mapping[str, Any]) -> list[str]:
    """Return the reasons this graph is not a single-stack App.

    An empty list means: every loader pin belongs to one stack, and the
    occupancy the graph claims is an occupancy that stack is allowed to hold.

    Args:
        graph: Parsed lab JSON.

    Returns:
        One human-readable sentence per violation, empty when the graph is clean.
    """
    problems: list[str] = []
    stacks = graph_stacks(graph)
    if len(stacks) > 1:
        problems.append(
            "pins "
            + " + ".join(sorted(stacks))
            + "; an App drives one stack - split it into one App per stack"
        )
    unknown = unclaimed_pins(graph)
    if unknown:
        names = ", ".join(sorted({f"{ntype}:{name}" for _, ntype, name in unknown}))
        problems.append(f"pins a weight no stack claims: {names}")

    occupancy = graph_occupancy(graph)
    allowed = OCCUPANCY_STACKS.get(occupancy)
    if allowed is None:
        if stacks or unknown:
            problems.append(f"occupancy {occupancy!r} is not a known stack slot")
        return problems
    if len(stacks) == 1:
        stack = next(iter(stacks))
        if stack not in allowed:
            problems.append(
                f"pins the {stack} stack under occupancy {occupancy!r}; "
                f"that occupancy hosts {'/'.join(sorted(allowed)) or 'no stack'}"
            )
    elif not stacks and not unknown:
        if occupancy not in ("none", "llm") and _claims_loaders(graph):
            problems.append(
                f"occupancy {occupancy!r} claims a heavy job but loads no weight"
            )
    return problems


def _claims_loaders(graph: Mapping[str, Any]) -> bool:
    """True when the graph carries a loader node at all.

    Args:
        graph: Parsed lab JSON.

    Returns:
        Whether any loader-typed node is present.
    """
    return any(
        str(node.get("type") or "") in LOADER_TYPES for node in (graph.get("nodes") or [])
    )


def describe_stacks(stacks: Iterable[str]) -> str:
    """Render a stack set for a report line.

    Args:
        stacks: Any iterable of stack names.

    Returns:
        A slash-joined sorted list, or ``none`` for an empty set.
    """
    ordered = sorted(set(stacks))
    return "/".join(ordered) if ordered else FAMILY_NONE


def stacks_in_order(stacks: Iterable[str]) -> Sequence[str]:
    """Sort a stack set into FAMILIES order for stable report text.

    Args:
        stacks: Any iterable of stack names.

    Returns:
        The names that appear, in FAMILIES order, unknown names last.
    """
    present = set(stacks)
    known = [family for family in FAMILIES if family in present]
    extra = sorted(present.difference(FAMILIES))
    return [*known, *extra]

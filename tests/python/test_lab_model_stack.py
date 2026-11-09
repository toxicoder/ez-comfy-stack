"""One model stack per App: the gate that keeps the Quality selector narrow.

An App drives one model stack. Within a stack the Quality combo swaps weights
(Klein 4B -> Klein 9B, Qwen-Image -> Qwen-Image turbo); across stacks the answer
is a second App that does the same job on the other stack. A combo that reaches
two stacks is what made the selector unreliable, so the rule is checked against
every shipped graph rather than left to review.
"""

from __future__ import annotations

from typing import Any

import pytest

from _lab_families import (
    FAMILIES,
    FAMILY_AUDIO,
    FAMILY_KLEIN,
    FAMILY_KLEIN3,
    FAMILY_LTX,
    FAMILY_NONE,
    FAMILY_QWEN,
    FAMILY_TRELLIS,
    FAMILY_WAN,
    LOADER_TYPES,
    OCCUPANCY_STACKS,
    describe_stacks,
    graph_occupancy,
    graph_pins,
    graph_stacks,
    stack_of_pin,
    stacks_in_order,
    stack_violations,
    weight_files,
)
from _lab_paths import cached_lab_graph_rows, lab_graph_paths


def _graph(nodes: list[dict[str, Any]], occupancy: str = "klein") -> dict[str, Any]:
    """Build a minimal graph dict with loader nodes and an occupancy claim.

    Args:
        nodes: Node dicts to place in the graph.
        occupancy: ``extra.lab_app_mode.occupancy`` value to claim.

    Returns:
        A graph dict shaped the way the gate reads it.
    """
    return {
        "nodes": nodes,
        "extra": {"lab_app_mode": {"occupancy": occupancy}},
    }


def _loader(node_id: int, ntype: str, *widgets: Any) -> dict[str, Any]:
    """Build one loader node.

    Args:
        node_id: LiteGraph node id.
        ntype: Loader node type.
        *widgets: Widget values in widget order.

    Returns:
        A node dict.
    """
    return {"id": node_id, "type": ntype, "widgets_values": list(widgets)}


# ---------------------------------------------------------------------------
# Naming a pin
# ---------------------------------------------------------------------------


def test_weight_files_reads_only_weight_widgets() -> None:
    assert weight_files(["flux-2-klein-4b-fp8.safetensors", "default"]) == [
        "flux-2-klein-4b-fp8.safetensors"
    ]
    assert weight_files([1024, None, True, "wan2.2_vae.safetensors"]) == [
        "wan2.2_vae.safetensors"
    ]
    assert weight_files([]) == []
    assert weight_files(["note text", "flux2"]) == []


def test_weight_files_takes_the_basename() -> None:
    assert weight_files(["unet/flux-2-klein-4b-fp8.safetensors"]) == [
        "flux-2-klein-4b-fp8.safetensors"
    ]
    assert weight_files(["unet\\flux-2-klein-4b-fp8.safetensors"]) == [
        "flux-2-klein-4b-fp8.safetensors"
    ]


@pytest.mark.parametrize(
    ("name", "stack"),
    [
        ("flux-2-klein-4b-fp8.safetensors", FAMILY_KLEIN),
        ("flux-2-klein-base-9b-fp8.safetensors", FAMILY_KLEIN),
        ("flux2_dev_fp8mixed.safetensors", FAMILY_KLEIN),
        ("qwen_3_4b.safetensors", FAMILY_KLEIN),
        ("mistral_3_small_flux2_bf16.safetensors", FAMILY_KLEIN),
        ("flux3-image-klein-int8-convrot.safetensors", FAMILY_KLEIN3),
        ("qwen3vl_4b_int8_convrot.safetensors", FAMILY_KLEIN3),
        ("qwen_image_2.1_int8_convrot.safetensors", FAMILY_QWEN),
        ("qwen3vl_8b_int8_convrot.safetensors", FAMILY_QWEN),
        ("qwen_image_2.1_vae_bf16.safetensors", FAMILY_QWEN),
        ("wan2.2_ti2v_5B_fp16.safetensors", FAMILY_WAN),
        ("umt5_xxl_fp8_e4m3fn_scaled.safetensors", FAMILY_WAN),
        ("wan2.2_vae.safetensors", FAMILY_WAN),
        ("ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors", FAMILY_LTX),
        ("gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors", FAMILY_LTX),
        ("ltx-2.5-audio-vae-bf16.safetensors", FAMILY_LTX),
        ("trellis_2_int8_convrot.safetensors", FAMILY_TRELLIS),
        ("dino_v3_vit_l.safetensors", FAMILY_TRELLIS),
        ("ace_step_1.5_turbo_aio.safetensors", FAMILY_AUDIO),
    ],
)
def test_stack_of_pin_names_the_stack(name: str, stack: str) -> None:
    assert stack_of_pin(name) == stack


@pytest.mark.parametrize(
    "name",
    [
        # The FLUX.2 VAE serves Klein and FLUX 3 Klein alike.
        "flux2-vae.safetensors",
        "full_encoder_small_decoder.safetensors",
        # A repackaged VACE drop carries no stack-bearing name.
        "diffusion_pytorch_model.safetensors",
    ],
)
def test_stack_of_pin_declines_shared_and_ambiguous_names(name: str) -> None:
    assert stack_of_pin(name) == FAMILY_NONE


def test_stack_of_pin_rejects_an_unknown_weight() -> None:
    assert stack_of_pin("minimax_video_v1.safetensors") is None


# ---------------------------------------------------------------------------
# Reading a graph
# ---------------------------------------------------------------------------


def test_graph_pins_lists_every_loader_weight() -> None:
    graph = _graph(
        [
            _loader(1, "UNETLoader", "flux-2-klein-4b-fp8.safetensors", "default"),
            _loader(2, "CLIPLoader", "qwen_3_4b.safetensors", "flux2", "default"),
            _loader(3, "VAELoader", "flux2-vae.safetensors"),
            _loader(4, "LoadImage", "example.png"),
        ]
    )
    assert graph_pins(graph) == [
        ("1", "UNETLoader", "flux-2-klein-4b-fp8.safetensors"),
        ("2", "CLIPLoader", "qwen_3_4b.safetensors"),
        ("3", "VAELoader", "flux2-vae.safetensors"),
    ]


def test_graph_stacks_ignores_the_shared_vae() -> None:
    graph = _graph(
        [
            _loader(1, "UNETLoader", "flux3-image-klein-int8-convrot.safetensors", "default"),
            _loader(2, "CLIPLoader", "qwen3vl_4b_int8_convrot.safetensors", "flux2", "d"),
            _loader(3, "VAELoader", "flux2-vae.safetensors"),
        ]
    )
    assert graph_stacks(graph) == {FAMILY_KLEIN3}


def test_graph_stacks_is_empty_for_a_desk_graph() -> None:
    assert graph_stacks(_graph([_loader(1, "LoadImage", "example.png")])) == set()


def test_graph_occupancy_defaults_to_empty() -> None:
    assert graph_occupancy(_graph([])) == "klein"
    assert graph_occupancy({"nodes": []}) == ""
    assert graph_occupancy({"nodes": [], "extra": {"lab_app_mode": {"occupancy": "LTX"}}}) == "ltx"


# ---------------------------------------------------------------------------
# The verdict
# ---------------------------------------------------------------------------


def test_clean_single_stack_graph_has_no_violations() -> None:
    graph = _graph(
        [
            _loader(1, "UNETLoader", "flux-2-klein-4b-fp8.safetensors", "default"),
            _loader(2, "CLIPLoader", "qwen_3_4b.safetensors", "flux2", "default"),
            _loader(3, "VAELoader", "flux2-vae.safetensors"),
        ]
    )
    assert stack_violations(graph) == []


def test_two_stacks_in_one_graph_is_a_split() -> None:
    graph = _graph(
        [
            _loader(1, "UNETLoader", "flux-2-klein-4b-fp8.safetensors", "default"),
            _loader(2, "UNETLoader", "qwen_image_2.1_int8_convrot.safetensors", "default"),
        ]
    )
    problems = stack_violations(graph)
    assert len(problems) == 1
    assert "pins klein + qwen" in problems[0]
    assert "split it into one App per stack" in problems[0]


def test_a_pin_no_stack_claims_is_reported() -> None:
    graph = _graph([_loader(7, "UNETLoader", "seedance_video_v2.safetensors", "default")])
    problems = stack_violations(graph)
    assert any("no stack claims" in problem for problem in problems)


def test_occupancy_that_does_not_host_the_stack_is_reported() -> None:
    graph = _graph(
        [_loader(1, "UNETLoader", "qwen_image_2.1_int8_convrot.safetensors", "default")],
        occupancy="wan",
    )
    problems = stack_violations(graph)
    assert any("pins the qwen stack under occupancy 'wan'" in problem for problem in problems)


def test_unknown_occupancy_with_pins_is_reported() -> None:
    graph = _graph(
        [_loader(1, "UNETLoader", "flux-2-klein-4b-fp8.safetensors", "default")],
        occupancy="flux2-dev",
    )
    assert any("not a known stack slot" in p for p in stack_violations(graph))


def test_unknown_occupancy_on_a_desk_graph_is_fine() -> None:
    assert stack_violations(_graph([], occupancy="prompt-forge")) == []


def test_heavy_occupancy_with_no_weight_is_reported() -> None:
    graph = _graph([_loader(1, "VAELoader", "flux2-vae.safetensors")], occupancy="ltx")
    assert any("claims a heavy job but loads no weight" in p for p in stack_violations(graph))


def test_llm_occupancy_loads_no_weight() -> None:
    assert stack_violations(_graph([], occupancy="llm")) == []
    assert stack_violations(_graph([], occupancy="none")) == []


# ---------------------------------------------------------------------------
# Report helpers
# ---------------------------------------------------------------------------


def test_describe_stacks_and_order() -> None:
    assert describe_stacks([]) == FAMILY_NONE
    assert describe_stacks([FAMILY_QWEN, FAMILY_KLEIN]) == "klein/qwen"
    assert stacks_in_order([FAMILY_WAN, FAMILY_KLEIN, "zzz"]) == ["klein", "wan", "zzz"]


def test_families_table_covers_every_occupancy_slot() -> None:
    hosted = {stack for stacks in OCCUPANCY_STACKS.values() for stack in stacks}
    assert hosted == set(FAMILIES)


# ---------------------------------------------------------------------------
# The shipped catalog
# ---------------------------------------------------------------------------


def test_loader_types_cover_the_core_loaders() -> None:
    for ntype in ("UNETLoader", "CLIPLoader", "VAELoader", "CheckpointLoaderSimple"):
        assert ntype in LOADER_TYPES


def test_every_shipped_graph_drives_one_stack() -> None:
    rows = cached_lab_graph_rows()
    assert len(rows) >= 8, "expected the shipped lab catalog"
    for rel, _path, graph in rows:
        problems = stack_violations(graph)
        assert not problems, f"{rel}: {'; '.join(problems)}"


def test_catalog_covers_every_stack() -> None:
    seen: set[str] = set()
    for _rel, _path, graph in cached_lab_graph_rows():
        seen.update(graph_stacks(graph))
    assert seen == set(FAMILIES), f"catalog stacks {sorted(seen)}"


def test_every_graph_with_a_loader_names_a_known_occupancy() -> None:
    for rel, path, graph in cached_lab_graph_rows():
        if not graph_pins(graph):
            continue
        occupancy = graph_occupancy(graph)
        assert occupancy in OCCUPANCY_STACKS, f"{rel}: occupancy {occupancy!r}"
        assert path.is_file()


def test_lab_graph_paths_still_walks_the_tree() -> None:
    assert len(lab_graph_paths()) >= 8

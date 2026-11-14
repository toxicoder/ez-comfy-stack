"""Cover scripts/lib/quality_apply.py (CLI Detail rung seam, 100% coverage).

The contract this file pins is the submit-path half of
/tmp/contract-detail-ladder.md: ``--quality`` names a rung (``draft``,
``standard``, ``final``), a legacy tier id resolves onto a rung through
``ez_quality.presets.normalize_quality`` rather than being refused, a rung the
graph's family cannot honor is *stated* and leaves the graph byte-identical,
and a Wan 14B graph is never touched.
"""

from __future__ import annotations

import copy
import json
import runpy
import sys
import urllib.error
from pathlib import Path
from typing import Any

import pytest

from ez_quality.presets import (
    CLIP_4B,
    CLIP_MISTRAL,
    KLEIN_BASE,
    KLEIN_DISTILLED,
    KLEIN_DRAFT_CFG,
    KLEIN_DRAFT_STEPS,
    KLEIN_NVFP4,
    KSAMPLER_CFG_INDEX,
    KSAMPLER_STEPS_INDEX,
    LTX_FINAL_STEPS,
    LTX_UNET,
    QUALITY_DRAFT,
    QUALITY_FINAL,
    QUALITY_STANDARD,
    VAE_FULL,
    VAE_SMALL,
    WAN_FINAL_STEPS,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import quality_apply as qa  # noqa: E402

WAN_14B_UNET = "wan2.2_t2v_14B_fp16.safetensors"
WAN_5B_UNET = "wan2.2_ti2v_5B_fp16.safetensors"

# Authored sampler steps for a Wan graph. Deliberately off both rungs (12/32)
# so "standard leaves it alone" is a claim about a value no rung asks for.
_WAN_AUTHORED_STEPS = 21

# Every file the klein rungs ask a loader to select, so an object_info fixture
# that advertises them lets an apply land instead of refusing.
_KLEIN_RUNG_UNETS: tuple[str, ...] = (KLEIN_NVFP4, KLEIN_BASE)
_KLEIN_RUNG_CLIPS: tuple[str, ...] = (CLIP_4B,)
_KLEIN_RUNG_VAES: tuple[str, ...] = (VAE_SMALL, VAE_FULL)

# Every legacy tier id in the contract's normalize table, with the rung it has
# to land on. The CLI takes the same table, so an old graph or a remembered
# habit never dies at the argument parser.
_LEGACY_TO_RUNG: tuple[tuple[str, str], ...] = (
    ("lab", QUALITY_STANDARD),
    ("custom", QUALITY_STANDARD),
    ("flux3-quality", QUALITY_STANDARD),
    ("qwen-image", QUALITY_STANDARD),
    ("high", QUALITY_FINAL),
    ("ultra", QUALITY_FINAL),
    ("max", QUALITY_FINAL),
    ("Free Commercial Use (<$10M)", QUALITY_FINAL),
    ("free_commercial", QUALITY_FINAL),
    ("flux3-nvfp4", QUALITY_FINAL),
    ("qwen-image-nvfp4", QUALITY_FINAL),
    ("flux3-fast", QUALITY_DRAFT),
    ("qwen-image-turbo", QUALITY_DRAFT),
    ("qwen-image-turbo-nvfp4", QUALITY_DRAFT),
)


def _graph(
    quality: str = QUALITY_STANDARD,
    *,
    occupancy: str = "klein",
    unet: str = KLEIN_DISTILLED,
) -> dict[str, Any]:
    """Family-shaped graph with one Detail widget, loaders, and a KSampler.

    Args:
        quality: Value to record on the EZQuality widget.
        occupancy: extra.lab_app_mode.occupancy value.
        unet: UNETLoader filename the graph pins (the table branches on it).

    Returns:
        A serialized-graph mapping.
    """
    return {
        "nodes": [
            {"id": 1, "type": "EZQuality", "widgets_values": [quality]},
            {"id": 2, "type": "UNETLoader", "widgets_values": [unet]},
            {"id": 3, "type": "CLIPLoader", "widgets_values": [CLIP_MISTRAL, "flux2"]},
            {"id": 4, "type": "VAELoader", "widgets_values": [VAE_FULL]},
            {"id": 5, "type": "KSampler", "widgets_values": [7, "fixed", 20, 3.5]},
        ],
        "extra": {"lab_app_mode": {"occupancy": occupancy}},
    }


def _write(path: Path, graph: dict[str, Any]) -> Path:
    """Write a graph fixture.

    Args:
        path: Destination file.
        graph: Graph mapping.

    Returns:
        The written path.
    """
    path.write_text(json.dumps(graph) + "\n", encoding="utf-8")
    return path


def _post(json_path: Path) -> dict[str, Any]:
    """Parse what the CLI wrote.

    Args:
        json_path: The --out file.

    Returns:
        The posted graph mapping.
    """
    posted = json.loads(json_path.read_text(encoding="utf-8"))
    assert isinstance(posted, dict)
    return posted


class _FakeResponse:
    """Stand-in for the urllib response object."""

    def __init__(self, payload: bytes) -> None:
        """Store the body.

        Args:
            payload: Raw response bytes.
        """
        self._payload = payload

    def read(self) -> bytes:
        """Return the body.

        Returns:
            Raw bytes.
        """
        return self._payload

    def __enter__(self) -> _FakeResponse:
        """Enter the context manager.

        Returns:
            Self.
        """
        return self

    def __exit__(self, *_exc: object) -> None:
        """Exit the context manager.

        Args:
            _exc: Ignored exception detail.
        """
        return None


def _object_info(
    unets: list[str],
    clips: list[str] | None = None,
    vaes: list[str] | None = None,
) -> dict[str, Any]:
    """Minimal object_info body for the three loaders.

    Args:
        unets: UNET combo options to advertise.
        clips: CLIP combo options to advertise.
        vaes: VAE combo options to advertise.

    Returns:
        object_info mapping.
    """
    return {
        "UNETLoader": {"input": {"required": {"unet_name": [unets]}}},
        "CLIPLoader": {"input": {"required": {"clip_name": [clips or []]}}},
        "VAELoader": {"input": {"required": {"vae_name": [vaes or []]}}},
    }


def test_explicit_rung_wins_over_the_graph(tmp_path: Path) -> None:
    """--quality overlays the requested rung, not the recorded one."""
    graph = _write(tmp_path / "g.json", _graph(QUALITY_DRAFT))
    out = tmp_path / "out.json"
    assert qa._cli(["--graph", str(graph), "--out", str(out), "--quality", "final"]) == 0  # noqa: SLF001
    posted = _post(out)
    sampler = posted["nodes"][4]["widgets_values"]
    assert sampler[KSAMPLER_STEPS_INDEX] == 24
    assert sampler[KSAMPLER_CFG_INDEX] == 3.5


def test_falls_back_to_the_recorded_rung(tmp_path: Path) -> None:
    """With no --quality the graph's own Detail widget decides."""
    graph = _write(
        tmp_path / "g.json",
        _graph(QUALITY_FINAL, occupancy="ltx", unet=LTX_UNET),
    )
    out = tmp_path / "out.json"
    assert qa._cli(["--graph", str(graph), "--out", str(out)]) == 0  # noqa: SLF001
    posted = _post(out)
    assert posted["nodes"][4]["widgets_values"][KSAMPLER_STEPS_INDEX] == LTX_FINAL_STEPS


def test_standard_writes_nothing_through_the_cli(tmp_path: Path) -> None:
    """The middle rung means leave the graph exactly as this App ships it."""
    graph = _graph(QUALITY_DRAFT)
    authored = copy.deepcopy(graph)
    src = _write(tmp_path / "g.json", graph)
    out = tmp_path / "out.json"
    assert (
        qa._cli(["--graph", str(src), "--out", str(out), "--quality", "standard"])  # noqa: SLF001
        == 0
    )
    assert _post(out) == authored


def test_defaults_to_the_standard_rung(tmp_path: Path) -> None:
    """No --quality and no usable Detail widget leaves the graph alone."""
    graph = _graph(QUALITY_DRAFT)
    graph["nodes"][0]["widgets_values"] = []
    authored_steps = copy.deepcopy(graph)["nodes"][4]["widgets_values"]
    src = _write(tmp_path / "g.json", graph)
    out = tmp_path / "out.json"
    assert qa._cli(["--graph", str(src), "--out", str(out)]) == 0  # noqa: SLF001
    posted = _post(out)
    assert posted["nodes"][4]["widgets_values"] == authored_steps
    assert qa.recorded_quality(graph) == ""
    assert qa.DEFAULT_RUNG == QUALITY_STANDARD
    assert qa.resolve_quality(graph, "") == QUALITY_STANDARD


def test_rung_choices_are_the_three_ladder_rows() -> None:
    """The CLI accepts exactly the ladder, so a typo is never a silent rung."""
    assert qa.LEGACY_TIER_IDS
    for rung in (QUALITY_DRAFT, QUALITY_STANDARD, QUALITY_FINAL):
        assert qa.canonical_tier(rung) == rung
        assert qa.canonical_tier(rung.upper()) == rung


@pytest.mark.parametrize(("legacy", "rung"), _LEGACY_TO_RUNG)
def test_legacy_tier_id_resolves_onto_its_rung(legacy: str, rung: str) -> None:
    """An old saved graph or an operator's habit is accepted input, not an error."""
    assert qa.canonical_tier(legacy) == rung
    assert qa.canonical_tier(f"  {legacy.upper()} ") == rung


@pytest.mark.parametrize("legacy", ["ultra", "lab", "final", "draft"])
def test_every_requested_quality_spelling_resolves(
    tmp_path: Path, legacy: str
) -> None:
    """--quality ultra / lab / final / draft all resolve and all write a graph."""
    src = _write(tmp_path / "g.json", _graph(QUALITY_STANDARD))
    out = tmp_path / f"out-{legacy}.json"
    assert (
        qa._cli(["--graph", str(src), "--out", str(out), "--quality", legacy])  # noqa: SLF001
        == 0
    )
    assert out.exists()


def test_legacy_spelling_and_its_rung_write_the_same_bytes(tmp_path: Path) -> None:
    """``--quality ultra`` is ``--quality final``, byte for byte, on this graph."""
    src = _write(tmp_path / "g.json", _graph(QUALITY_DRAFT))
    legacy_out = tmp_path / "legacy.json"
    rung_out = tmp_path / "rung.json"
    assert (
        qa._cli(["--graph", str(src), "--out", str(legacy_out), "--quality", "ultra"])  # noqa: SLF001
        == 0
    )
    assert (
        qa._cli(["--graph", str(src), "--out", str(rung_out), "--quality", "final"])  # noqa: SLF001
        == 0
    )
    assert legacy_out.read_bytes() == rung_out.read_bytes()


def test_unknown_tier_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """An unknown --quality is refused with one stderr line and no output."""
    src = _write(tmp_path / "g.json", _graph(QUALITY_STANDARD))
    out = tmp_path / "out.json"
    status = qa._cli(  # noqa: SLF001
        ["--graph", str(src), "--out", str(out), "--quality", "ultra-max"]
    )
    assert status == 1
    assert not out.exists()
    err = capsys.readouterr().err
    assert "ultra-max" in err
    assert len(err.strip().splitlines()) == 1


def test_missing_graph_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A missing --graph is a one-line error."""
    out = tmp_path / "out.json"
    assert qa._cli(["--graph", str(tmp_path / "nope.json"), "--out", str(out)]) == 1  # noqa: SLF001
    assert not out.exists()
    assert len(capsys.readouterr().err.strip().splitlines()) == 1


def test_graph_that_is_not_an_object_errors(tmp_path: Path) -> None:
    """A JSON array is not a graph."""
    src = tmp_path / "list.json"
    src.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(qa.QualityApplyError, match="JSON object"):
        qa.load_graph(src)


def test_graph_that_is_not_json_errors(tmp_path: Path) -> None:
    """Unparseable JSON is refused."""
    src = tmp_path / "bad.json"
    src.write_text("{oops", encoding="utf-8")
    with pytest.raises(qa.QualityApplyError, match="not valid JSON"):
        qa.load_graph(src)


def test_unwritable_output_errors(tmp_path: Path) -> None:
    """An impossible --out is reported, not raised."""
    src = _write(tmp_path / "g.json", _graph(QUALITY_DRAFT))
    with pytest.raises(qa.QualityApplyError, match="cannot write"):
        qa.apply_quality_file(
            graph_path=src,
            out_path=tmp_path / "missing-dir" / "out.json",
            quality="draft",
            comfy_url="",
        )


def test_object_info_unreachable_skips_the_availability_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A dead ComfyUI degrades to None availability and still overlays the rung."""

    def _boom(*_a: object, **_k: object) -> _FakeResponse:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(qa.urllib.request, "urlopen", _boom)
    assert qa.resolve_availability("http://127.0.0.1:1") == qa.Availability()
    src = _write(tmp_path / "g.json", _graph(QUALITY_DRAFT))
    out = tmp_path / "out.json"
    assert qa._cli(["--graph", str(src), "--out", str(out), "--comfy-url", "http://x"]) == 0  # noqa: SLF001
    posted = _post(out)
    # Unknown combo options are the "catalog unknown" answer both sides read as
    # "skip the presence check", so the whole draft row lands rather than the
    # apply refusing over a file nobody could verify.
    assert posted["nodes"][1]["widgets_values"] == [KLEIN_NVFP4]
    assert posted["nodes"][2]["widgets_values"][0] == CLIP_4B
    assert posted["nodes"][3]["widgets_values"] == [VAE_SMALL]
    assert posted["nodes"][4]["widgets_values"][KSAMPLER_STEPS_INDEX] == KLEIN_DRAFT_STEPS
    assert posted["nodes"][4]["widgets_values"][KSAMPLER_CFG_INDEX] == KLEIN_DRAFT_CFG


def test_object_info_reachable_allows_the_loader_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live combo options let the rung table swap UNET / CLIP / VAE names."""
    monkeypatch.setattr(
        qa.urllib.request,
        "urlopen",
        lambda *_a, **_k: _FakeResponse(
            json.dumps(
                _object_info(
                    list(_KLEIN_RUNG_UNETS),
                    list(_KLEIN_RUNG_CLIPS),
                    list(_KLEIN_RUNG_VAES),
                )
            ).encode()
        ),
    )
    availability = qa.resolve_availability("http://127.0.0.1:8188/")
    assert availability.unets == list(_KLEIN_RUNG_UNETS)
    assert availability.clips == list(_KLEIN_RUNG_CLIPS)
    src = _write(tmp_path / "g.json", _graph(QUALITY_STANDARD))
    out = tmp_path / "out.json"
    assert qa._cli([  # noqa: SLF001
        "--graph",
        str(src),
        "--out",
        str(out),
        "--quality",
        "final",
        "--comfy-url",
        "http://127.0.0.1:8188",
    ]) == 0
    posted = _post(out)
    assert posted["nodes"][1]["widgets_values"] == [KLEIN_BASE]
    assert posted["nodes"][2]["widgets_values"][0] == CLIP_4B
    assert posted["nodes"][3]["widgets_values"] == [VAE_FULL]
    assert posted["nodes"][4]["widgets_values"][KSAMPLER_STEPS_INDEX] == 24


def test_loader_options_ignore_undocumented_combos() -> None:
    """Missing or malformed object_info entries mean no presence check."""
    assert qa._loader_options({}, "UNETLoader", "unet_name") is None  # noqa: SLF001
    assert qa._loader_options({"UNETLoader": {}}, "UNETLoader", "unet_name") is None  # noqa: SLF001
    assert (  # noqa: SLF001
        qa._loader_options({"UNETLoader": {"input": {"required": {"unet_name": []}}}}, "UNETLoader", "unet_name")
        is None
    )
    assert (  # noqa: SLF001
        qa._loader_options(
            {"UNETLoader": {"input": {"required": {"unet_name": ["nope"]}}}},
            "UNETLoader",
            "unet_name",
        )
        is None
    )


def test_object_info_that_is_not_a_mapping_is_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-object body is treated as unreachable."""
    monkeypatch.setattr(
        qa.urllib.request, "urlopen", lambda *_a, **_k: _FakeResponse(b"[1, 2]")
    )
    assert qa._fetch_object_info("http://127.0.0.1:8188") is None  # noqa: SLF001
    assert qa.resolve_availability("http://127.0.0.1:8188") == qa.Availability()


def test_wan_14b_graph_is_left_untouched(tmp_path: Path) -> None:
    """Wan 14B graphs refuse the overlay, exactly like the table."""
    graph = _graph(QUALITY_FINAL, occupancy="wan", unet=WAN_14B_UNET)
    src = _write(tmp_path / "g.json", graph)
    out = tmp_path / "out.json"
    assert qa._cli(["--graph", str(src), "--out", str(out), "--quality", "final"]) == 0  # noqa: SLF001
    assert out.read_bytes() == src.read_bytes()


# Spellings the CLI has to swallow on a graph no rung can move.
_ACCEPTED_SPELLINGS: tuple[str, ...] = (
    QUALITY_DRAFT,
    QUALITY_STANDARD,
    QUALITY_FINAL,
    "ultra",
    "max",
    "high",
    "free_commercial",
)


@pytest.mark.parametrize("spelling", _ACCEPTED_SPELLINGS)
def test_wan_14b_stays_untouched_under_every_spelling(
    tmp_path: Path, spelling: str
) -> None:
    """No rung and no legacy spelling reaches a 14B graph, byte for byte."""
    graph = _graph(QUALITY_STANDARD, occupancy="wan", unet=WAN_14B_UNET)
    src = _write(tmp_path / "g.json", graph)
    out = tmp_path / "out.json"
    assert (
        qa._cli(["--graph", str(src), "--out", str(out), "--quality", spelling])  # noqa: SLF001
        == 0
    )
    assert out.read_bytes() == src.read_bytes()


def test_a_rung_the_family_cannot_honor_is_stated(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI says so instead of writing a graph that never changed."""
    graph = _graph(QUALITY_STANDARD, occupancy="llm")
    src = _write(tmp_path / "g.json", graph)
    out = tmp_path / "out.json"
    assert (
        qa._cli(["--graph", str(src), "--out", str(out), "--quality", "final"])  # noqa: SLF001
        == 0
    )
    err = capsys.readouterr().err
    assert "cannot honor" in err, err
    assert "llm" in err, err
    assert "final" in err, err
    assert out.read_bytes() == src.read_bytes()


def test_a_rung_the_family_can_honor_stays_quiet(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An honored rung still prints nothing, so scripts can chain on it."""
    graph = _graph(QUALITY_STANDARD, occupancy="wan", unet=WAN_5B_UNET)
    src = _write(tmp_path / "g.json", graph)
    out = tmp_path / "out.json"
    assert (
        qa._cli(["--graph", str(src), "--out", str(out), "--quality", "final"])  # noqa: SLF001
        == 0
    )
    assert capsys.readouterr().err == ""
    assert _post(out)["nodes"][4]["widgets_values"][KSAMPLER_STEPS_INDEX] == WAN_FINAL_STEPS


def test_the_authored_wan_steps_survive_the_middle_rung(tmp_path: Path) -> None:
    """``standard`` on a Wan graph keeps the steps this App ships with."""
    graph = _graph(QUALITY_FINAL, occupancy="wan", unet=WAN_5B_UNET)
    graph["nodes"][4]["widgets_values"][KSAMPLER_STEPS_INDEX] = _WAN_AUTHORED_STEPS
    authored = copy.deepcopy(graph)
    src = _write(tmp_path / "g.json", graph)
    out = tmp_path / "out.json"
    assert (
        qa._cli(["--graph", str(src), "--out", str(out), "--quality", "standard"])  # noqa: SLF001
        == 0
    )
    assert _post(out) == authored


def test_recorded_quality_skips_foreign_nodes() -> None:
    """Non-mapping nodes and other node types never decide the rung."""
    graph = {"nodes": ["junk", {"type": "KSampler", "widgets_values": ["final"]}]}
    assert qa.recorded_quality(graph) == ""
    assert qa.resolve_quality(graph, "") == QUALITY_STANDARD
    assert qa.canonical_tier("FREE_COMMERCIAL") == QUALITY_FINAL
    assert qa.canonical_tier("") is None
    assert qa.canonical_tier("not-a-rung") is None


def test_cli_main_guard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The module runs as a script and exits 0 on success."""
    src = _write(tmp_path / "g.json", _graph(QUALITY_DRAFT))
    out = tmp_path / "out.json"
    monkeypatch.setattr(
        sys, "argv", ["quality_apply.py", "--graph", str(src), "--out", str(out)]
    )
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(
            str(ROOT / "scripts" / "lib" / "quality_apply.py"), run_name="__main__"
        )
    assert exc.value.code in {0, None}
    assert _post(out)["nodes"][4]["widgets_values"][KSAMPLER_STEPS_INDEX] == 4

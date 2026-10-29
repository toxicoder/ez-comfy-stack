"""Cover scripts/lib/quality_apply.py (CLI Quality seam, 100% coverage)."""

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
    CLIP_MISTRAL,
    KLEIN_DISTILLED,
    KLEIN_NVFP4,
    LTX_UNET,
    QUALITY_HIGH,
    QUALITY_LAB,
    VAE_FULL,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import quality_apply as qa  # noqa: E402

WAN_14B_UNET = "wan2.2_t2v_14B_fp16.safetensors"


def _graph(
    quality: str = QUALITY_LAB,
    *,
    occupancy: str = "klein",
    unet: str = KLEIN_DISTILLED,
) -> dict[str, Any]:
    """Family-shaped graph with one EZQuality widget, loaders, and a KSampler.

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
    path.write_text(json.dumps(graph), encoding="utf-8")
    return path


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


def _object_info(unets: list[str]) -> dict[str, Any]:
    """Minimal object_info body for the three loaders.

    Args:
        unets: UNET combo options to advertise.

    Returns:
        object_info mapping.
    """
    return {
        "UNETLoader": {"input": {"required": {"unet_name": [unets]}}},
        "CLIPLoader": {"input": {"required": {"clip_name": [[CLIP_MISTRAL]]}}},
        "VAELoader": {"input": {"required": {"vae_name": [[VAE_FULL]]}}},
    }


def test_explicit_quality_wins_over_the_graph(tmp_path: Path) -> None:
    """--quality overlays the requested tier, not the recorded one."""
    graph = _write(tmp_path / "g.json", _graph("lab"))
    out = tmp_path / "out.json"
    assert qa._cli(["--graph", str(graph), "--out", str(out), "--quality", "draft"]) == 0  # noqa: SLF001
    posted = json.loads(out.read_text(encoding="utf-8"))
    assert posted["nodes"][4]["widgets_values"][2] == 4
    assert posted["nodes"][4]["widgets_values"][3] == 1.0
    assert posted["nodes"][0]["widgets_values"] == ["lab"]


def test_falls_back_to_the_recorded_tier(tmp_path: Path) -> None:
    """With no --quality the graph's own EZQuality widget decides."""
    graph = _write(
        tmp_path / "g.json",
        _graph(QUALITY_HIGH, occupancy="ltx", unet=LTX_UNET),
    )
    out = tmp_path / "out.json"
    assert qa._cli(["--graph", str(graph), "--out", str(out)]) == 0  # noqa: SLF001
    posted = json.loads(out.read_text(encoding="utf-8"))
    assert posted["nodes"][4]["widgets_values"][2] == 28


def test_defaults_to_lab_when_the_graph_records_nothing(tmp_path: Path) -> None:
    """No --quality and no usable EZQuality widget leaves the graph alone."""
    graph = _graph("lab")
    graph["nodes"][0]["widgets_values"] = []
    authored_steps = copy.deepcopy(graph)["nodes"][4]["widgets_values"]
    src = _write(tmp_path / "g.json", graph)
    out = tmp_path / "out.json"
    assert qa._cli(["--graph", str(src), "--out", str(out)]) == 0  # noqa: SLF001
    posted = json.loads(out.read_text(encoding="utf-8"))
    assert posted["nodes"][4]["widgets_values"] == authored_steps
    assert qa.recorded_quality(graph) == ""


def test_unknown_tier_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """An unknown --quality is refused with one stderr line and no output."""
    src = _write(tmp_path / "g.json", _graph("lab"))
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
    src = _write(tmp_path / "g.json", _graph("draft"))
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
    """A dead ComfyUI degrades to None availability instead of failing."""

    def _boom(*_a: object, **_k: object) -> _FakeResponse:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(qa.urllib.request, "urlopen", _boom)
    assert qa.resolve_availability("http://127.0.0.1:1") == qa.Availability()
    src = _write(tmp_path / "g.json", _graph("draft"))
    out = tmp_path / "out.json"
    assert qa._cli(["--graph", str(src), "--out", str(out), "--comfy-url", "http://x"]) == 0  # noqa: SLF001
    posted = json.loads(out.read_text(encoding="utf-8"))
    assert posted["nodes"][1]["widgets_values"] == [KLEIN_DISTILLED]
    assert posted["nodes"][4]["widgets_values"][2] == 4


def test_object_info_reachable_allows_the_loader_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live combo options let the tier table swap UNET / CLIP / VAE names."""
    monkeypatch.setattr(
        qa.urllib.request,
        "urlopen",
        lambda *_a, **_k: _FakeResponse(json.dumps(_object_info([KLEIN_NVFP4])).encode()),
    )
    availability = qa.resolve_availability("http://127.0.0.1:8188/")
    assert availability.unets == [KLEIN_NVFP4]
    assert availability.clips == [CLIP_MISTRAL]
    src = _write(tmp_path / "g.json", _graph("draft"))
    out = tmp_path / "out.json"
    assert qa._cli([  # noqa: SLF001
        "--graph",
        str(src),
        "--out",
        str(out),
        "--quality",
        "draft",
        "--comfy-url",
        "http://127.0.0.1:8188",
    ]) == 0
    posted = json.loads(out.read_text(encoding="utf-8"))
    assert posted["nodes"][1]["widgets_values"] == [KLEIN_NVFP4]


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
    graph = _graph("max", occupancy="wan", unet=WAN_14B_UNET)
    before = copy.deepcopy(graph)
    src = _write(tmp_path / "g.json", graph)
    out = tmp_path / "out.json"
    assert qa._cli(["--graph", str(src), "--out", str(out), "--quality", "max"]) == 0  # noqa: SLF001
    assert json.loads(out.read_text(encoding="utf-8")) == before


def test_recorded_quality_skips_foreign_nodes() -> None:
    """Non-mapping nodes and other node types never decide the tier."""
    graph = {"nodes": ["junk", {"type": "KSampler", "widgets_values": ["max"]}]}
    assert qa.recorded_quality(graph) == ""
    assert qa.resolve_quality(graph, "") == QUALITY_LAB
    assert qa.canonical_tier("FREE_COMMERCIAL") == "Free Commercial Use (<$10M)"
    assert qa.canonical_tier("") is None


def test_cli_main_guard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The module runs as a script and exits 0 on success."""
    src = _write(tmp_path / "g.json", _graph("draft"))
    out = tmp_path / "out.json"
    monkeypatch.setattr(
        sys, "argv", ["quality_apply.py", "--graph", str(src), "--out", str(out)]
    )
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(
            str(ROOT / "scripts" / "lib" / "quality_apply.py"), run_name="__main__"
        )
    assert exc.value.code in {0, None}
    assert json.loads(out.read_text(encoding="utf-8"))["nodes"][4]["widgets_values"][2] == 4

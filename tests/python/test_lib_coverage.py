"""Hermetic leftovers: clay raster edges, lib __main__, argparse fallbacks."""

from __future__ import annotations

import argparse
import runpy
import sys
from array import array
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import house_clay_render as hcr  # noqa: E402
import house_layout as hl  # noqa: E402
import model_manifest as mm  # noqa: E402

MANIFEST = ROOT / "config" / "model-manifest.yaml"
SCHEMA_YAML = ROOT / "schemas" / "house_layout.yaml"

_LIB_MAINS = (
    "scripts/lib/asset_bible.py",
    "scripts/lib/blender_mcp.py",
    "scripts/lib/disk_catalog.py",
    "scripts/lib/guide_pack.py",
    "scripts/lib/house_layout.py",
    "scripts/lib/model_manifest.py",
    "scripts/lib/research_mcp.py",
    "custom_nodes/ez_dcc/_guide_pack.py",
)


@pytest.mark.parametrize("rel", list(_LIB_MAINS))
def test_lib_module_main_help(rel: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", [Path(rel).name, "--help"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(ROOT / rel), run_name="__main__")
    assert exc.value.code in {0, None}


def test_argparse_unknown_cmd_returns_1(monkeypatch: pytest.MonkeyPatch) -> None:
    import asset_bible as ab
    import guide_pack as gp

    monkeypatch.setattr(
        argparse.ArgumentParser,
        "parse_args",
        lambda self, argv=None, namespace=None: argparse.Namespace(
            cmd="__nope__",
            manifest=str(MANIFEST),
            file="x.yaml",
            output_dir=".",
            json=False,
            pack=".",
            fixture=False,
            name="x",
        ),
    )
    assert ab._cli(["validate", "x.yaml"]) == 1
    assert gp._cli(["validate", "."]) == 1
    assert mm._cli(["--manifest", str(MANIFEST), "json"]) == 1
    import ez_dcc._guide_pack as vendor_gp

    assert vendor_gp._cli(["validate", "."]) == 1


def test_clay_norm_zero_and_up_camera() -> None:
    assert hcr._norm((0.0, 0.0, 0.0)) == (0.0, 1.0, 0.0)
    right, up, forward = hcr._camera_basis((0.0, 0.0, 0.0), (0.0, 4.0, 0.0))
    assert abs(forward[1]) == pytest.approx(1.0)
    assert abs(hcr._dot(right, right) - 1.0) < 1e-5
    assert abs(hcr._dot(up, up) - 1.0) < 1e-5


def test_clay_camera_basis_double_degenerate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(hcr, "_cross", lambda _a, _b: (0.0, 0.0, 0.0))
    right, _up, _fwd = hcr._camera_basis((0.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    assert right == (1.0, 0.0, 0.0)


def test_clay_fill_triangle_near_and_bad_camera() -> None:
    pixels = bytearray(3)
    zbuf = array("f", [1.0e9])
    hcr._fill_triangle(
        pixels,
        zbuf,
        1,
        1,
        (0.5, 0.5, 0.01),
        (0.6, 0.5, 0.01),
        (0.5, 0.6, 0.01),
        (10, 20, 30),
    )
    assert pixels == bytearray(3)
    with pytest.raises(ValueError, match="camera_index"):
        hcr.render_clay_rgb({"cameras": []}, 0)
    with pytest.raises(ValueError, match="camera_index"):
        hcr.render_clay_rgb({"cameras": [{}]}, -1)


def test_clay_zero_look_renders(tmp_path: Path) -> None:
    layout = hl.load_layout(SCHEMA_YAML)
    layout["cameras"][0]["pos"] = [0.0, 0.0, 0.0]
    layout["cameras"][0]["look"] = [0.0, 0.0, 0.0]
    rgb = hcr.render_clay_rgb(layout, 0, width=8, height=10)
    assert len(rgb) == 8 * 10 * 3
    dest = tmp_path / "zero.png"
    hcr.render_clay_plate(layout, 1, dest)
    assert dest.is_file()

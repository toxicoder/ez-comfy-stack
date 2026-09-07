"""Wave 3 contracts: native TRELLIS.2, DA3-BASE, VACE join, host sidecars."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"
DOCKERFILE = ROOT / "docker" / "Dockerfile"


def test_dockerfile_has_no_nvdiffrast_blender_or_supersplat() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8").lower()
    for needle in ("nvdiffrast", "nvdiffrec", "supersplat", "blender"):
        assert needle not in text, needle


def test_vace_join_graph_is_17_frames_magcache_off() -> None:
    path = WF / "wan-vace-join-lab-example.json"
    graph = json.loads(path.read_text(encoding="utf-8"))
    assert graph["id"] == "wan-vace-join-lab-example"
    extra = graph["extra"]
    assert extra["lab_vace"]["frames"] == 17
    assert extra["lab_vace"]["rule"] == "1+8n"
    assert extra["lab_vace"]["magcache"] is False
    assert "lab_magcache" not in extra
    assert not any(n.get("type") == "MagCache" for n in graph["nodes"])
    latent = next(n for n in graph["nodes"] if n.get("type") == "Wan22ImageToVideoLatent")
    assert int(latent["widgets_values"][2]) == 17
    titles = [n.get("title") for n in graph["nodes"]]
    assert "Shot A last frame" in titles
    assert "Shot B first frame (join)" in titles
    assert "diffusion_pytorch_model.safetensors" in json.dumps(graph)
    assert "vace" in extra["lab_note"].lower()


def test_sidecar_docs_exist() -> None:
    for name in (
        "studio-sidecars.md",
        "blender-gb10-sidecar.md",
        "splat-sidecar.md",
    ):
        path = ROOT / "docs" / name
        text = path.read_text(encoding="utf-8")
        assert "What's on this page" in text
        assert "What this enables" in text
        assert "occupancy" in text.lower() or "compose" in text.lower()
        assert "Dockerfile" in text


def test_manifest_3d_packs_are_opt_in() -> None:
    text = (ROOT / "config" / "model-manifest.yaml").read_text(encoding="utf-8")
    for pack in ("trellis2:", "da3-base:", "wan-vace:"):
        assert pack in text
    assert "download-3d --tier trellis2" in text
    assert "download-wan --tier vace" in text
    assert "DA3-LARGE" in text
    assert "Pixal3D-as-default" in text

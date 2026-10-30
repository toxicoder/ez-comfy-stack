"""Editor contract: no in-browser editor ships in the image; Vlo is documented."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: Every file that used to carry the retired COMFYUI_OPENCUT_REF pin.
PIN_CARRIERS = (
    Path(".env.example"),
    Path("docker") / "Dockerfile",
    Path("docker") / "docker-compose.yml",
    Path("docker") / "install-comfy.sh",
    Path("docker") / "install-comfy" / "common.sh",
    Path("docker") / "install-comfy" / "phase-nodes.sh",
)


def test_opencut_pin_fully_retired() -> None:
    """Neither the env var nor the upstream repo survives anywhere in the build."""
    for rel in PIN_CARRIERS:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "OPENCUT" not in text.upper(), rel
        assert "opencut" not in text.lower(), rel


def test_vlo_documented_as_host_editor() -> None:
    """The docs name Vlo, its host port, and the ComfyUI URL it dials."""
    doc = ROOT / "docs" / "vlo.mdx"
    assert doc.is_file(), "docs/vlo.mdx must document the recommended editor"
    text = doc.read_text(encoding="utf-8")
    assert "PxTicks/vlo" in text
    assert "http://127.0.0.1:6332" in text
    assert "http://127.0.0.1:8188" in text


def test_vlo_reachable_from_sidecars_index() -> None:
    """The sidecars page - where host editors live - links the Vlo guide."""
    text = (ROOT / "docs" / "studio-sidecars.mdx").read_text(encoding="utf-8")
    assert "vlo.md" in text

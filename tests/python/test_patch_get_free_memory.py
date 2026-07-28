"""Unit tests for docker/patch_get_free_memory.py (100% line coverage target).

Hermetic: builds temporary fake ComfyUI trees under pytest tmp_path; never
touches a real ComfyUI install. Covers primary and alternate mem_get_info
patterns, idempotent re-apply, missing-file skip, version-drift warning,
CLI main()/argv handling, and the ``__main__`` entry via runpy.
"""

from __future__ import annotations

import sys
from pathlib import Path

import patch_get_free_memory as patch_mod
import pytest


def test_skip_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """When model_management.py is absent, apply_patch skips with a stderr note."""
    rc = patch_mod.apply_patch(tmp_path)
    assert rc == 0
    assert "skip" in capsys.readouterr().err


def test_apply_primary_pattern(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Primary mem_free_cuda, _ = torch.cuda.mem_get_info(dev) pattern is rewritten."""
    comfy = tmp_path / "comfy"
    comfy.mkdir()
    target = comfy / "model_management.py"
    target.write_text(
        "def get_free_memory(dev):\n"
        "    mem_free_cuda, _ = torch.cuda.mem_get_info(dev)\n"
        "    return mem_free_cuda\n",
        encoding="utf-8",
    )
    rc = patch_mod.apply_patch(tmp_path)
    assert rc == 0
    text = target.read_text(encoding="utf-8")
    assert patch_mod.MARKER in text
    assert "psutil" in text
    assert "applied" in capsys.readouterr().out


def test_idempotent(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Second apply with MARKER already present is a no-op success."""
    comfy = tmp_path / "comfy"
    comfy.mkdir()
    target = comfy / "model_management.py"
    target.write_text(
        f"mem_free_cuda = 1  # {patch_mod.MARKER}\n",
        encoding="utf-8",
    )
    rc = patch_mod.apply_patch(tmp_path)
    assert rc == 0
    assert "already applied" in capsys.readouterr().out


def test_alternate_pattern(tmp_path: Path) -> None:
    """Alternate mem_free_total, mem_free_torch assignment shape is patched."""
    comfy = tmp_path / "comfy"
    comfy.mkdir()
    target = comfy / "model_management.py"
    target.write_text(
        "mem_free_total, mem_free_torch = torch.cuda.mem_get_info(dev)\n",
        encoding="utf-8",
    )
    assert patch_mod.apply_patch(tmp_path) == 0
    assert patch_mod.MARKER in target.read_text(encoding="utf-8")


def test_second_alternate_pattern(tmp_path: Path) -> None:
    """free_memory, total_memory = torch.cuda.mem_get_info(device) shape is patched."""
    comfy = tmp_path / "comfy"
    comfy.mkdir()
    target = comfy / "model_management.py"
    target.write_text(
        "free_memory, total_memory = torch.cuda.mem_get_info(device)\n",
        encoding="utf-8",
    )
    assert patch_mod.apply_patch(tmp_path) == 0
    assert patch_mod.MARKER in target.read_text(encoding="utf-8")


def test_no_pattern_warns(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Unknown file content yields a WARNING and exit 0 (fail-soft)."""
    comfy = tmp_path / "comfy"
    comfy.mkdir()
    (comfy / "model_management.py").write_text("print('nope')\n", encoding="utf-8")
    assert patch_mod.apply_patch(tmp_path) == 0
    assert "WARNING" in capsys.readouterr().err


def test_main_default_and_arg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """main([root]) and main() with argv both apply the patch successfully."""
    comfy = tmp_path / "comfy"
    comfy.mkdir()
    (comfy / "model_management.py").write_text(
        "mem_free_cuda, _ = torch.cuda.mem_get_info(dev)\n",
        encoding="utf-8",
    )
    assert patch_mod.main([str(tmp_path)]) == 0
    monkeypatch.setattr(sys, "argv", ["patch", str(tmp_path)])
    assert patch_mod.main() == 0


def test_main_no_args_default_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """main([]) uses the default Comfy path and still returns 0 when missing."""
    monkeypatch.setattr(sys, "argv", ["patch"])
    assert patch_mod.main([]) == 0


def test_module_main_entrypoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Cover ``if __name__ == "__main__"`` via runpy.run_path."""
    import runpy

    comfy = tmp_path / "comfy"
    comfy.mkdir()
    (comfy / "model_management.py").write_text(
        "mem_free_cuda, _ = torch.cuda.mem_get_info(dev)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "argv", ["patch_get_free_memory.py", str(tmp_path)])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(
            str(Path(__file__).resolve().parents[2] / "docker" / "patch_get_free_memory.py"),
            run_name="__main__",
        )
    assert exc.value.code == 0

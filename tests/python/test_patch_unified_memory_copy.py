"""Unit tests for docker/patch_unified_memory_copy.py (100% line coverage).

Hermetic: fake ComfyUI trees under pytest tmp_path. No GPU, network, or
real ComfyUI install.
"""

from __future__ import annotations

import sys
from pathlib import Path

import patch_unified_memory_copy as patch_mod
import pytest

SAMPLE = (
    "def load_torch_file(ckpt, device=None):\n"
    "    if DISABLE_MMAP:\n"
    "        tensor = tensor.to(device=device, copy=True)\n"
    "    return tensor\n"
)


def _write_utils(tmp_path: Path, text: str, newline: str = "\n") -> Path:
    comfy = tmp_path / "comfy"
    comfy.mkdir(exist_ok=True)
    target = comfy / "utils.py"
    target.write_text(text.replace("\n", newline), encoding="utf-8", newline="")
    return target


def test_skip_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = patch_mod.apply_patch(tmp_path)
    assert rc == 0
    assert "skip" in capsys.readouterr().err


def test_apply_copy_true_pattern(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = _write_utils(tmp_path, SAMPLE)
    assert patch_mod.apply_patch(tmp_path) == 0
    text = target.read_text(encoding="utf-8")
    assert patch_mod.MARKER in text
    assert "copy=False" in text
    assert "copy=True" not in text
    compile(text, str(target), "exec")
    assert "applied" in capsys.readouterr().out


def test_idempotent(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_utils(tmp_path, SAMPLE)
    assert patch_mod.apply_patch(tmp_path) == 0
    capsys.readouterr()
    assert patch_mod.apply_patch(tmp_path) == 0
    assert "already applied" in capsys.readouterr().out


def test_no_pattern_warns(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_utils(tmp_path, "print('nope')\n")
    assert patch_mod.apply_patch(tmp_path) == 0
    assert "WARNING" in capsys.readouterr().err


def test_already_copy_false_upstream(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_utils(
        tmp_path,
        "tensor = tensor.to(device=device, copy=False)\n",
    )
    assert patch_mod.apply_patch(tmp_path) == 0
    out = capsys.readouterr()
    assert "already copy=False" in out.out


def test_would_not_compile_aborts_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = _write_utils(tmp_path, SAMPLE)
    original = target.read_text(encoding="utf-8")
    monkeypatch.setattr(patch_mod, "_compiles", lambda *a, **k: False)
    assert patch_mod.apply_patch(tmp_path) == 0
    assert target.read_text(encoding="utf-8") == original
    assert "would not compile" in capsys.readouterr().err


def test_crlf_line_endings(tmp_path: Path) -> None:
    target = _write_utils(tmp_path, SAMPLE, newline="\r\n")
    assert patch_mod.apply_patch(tmp_path) == 0
    raw = target.read_bytes()
    assert b"\r\n" in raw
    assert patch_mod.MARKER.encode() in raw


def test_compiles_helper() -> None:
    assert patch_mod._compiles("x = 1\n") is True  # noqa: SLF001
    assert patch_mod._compiles("def broken(:\n") is False  # noqa: SLF001


def test_main_default_and_arg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_utils(tmp_path, SAMPLE)
    assert patch_mod.main([str(tmp_path)]) == 0
    monkeypatch.setattr(sys, "argv", ["patch", str(tmp_path)])
    assert patch_mod.main() == 0


def test_main_no_args_default_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", ["patch"])
    assert patch_mod.main([]) == 0


def test_module_main_entrypoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import runpy

    _write_utils(tmp_path, SAMPLE)
    monkeypatch.setattr(sys, "argv", ["patch_unified_memory_copy.py", str(tmp_path)])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(
            str(
                Path(__file__).resolve().parents[2]
                / "docker"
                / "patch_unified_memory_copy.py"
            ),
            run_name="__main__",
        )
    assert exc.value.code == 0

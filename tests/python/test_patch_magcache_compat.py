"""Unit tests for docker/patch_magcache_compat.py (100% line coverage).

Hermetic: fake ComfyUI trees under pytest tmp_path. No GPU, network, or
real MagCache clone.
"""

from __future__ import annotations

import sys
from pathlib import Path

import patch_magcache_compat as patch_mod
import pytest

SAMPLE = (
    "from comfy.ldm.flux.layers import timestep_embedding, apply_mod\n"
    "from comfy.ldm.lightricks.model import precompute_freqs_cis\n"
    "from comfy.ldm.lightricks.symmetric_patchifier import latent_to_pixel_coords\n"
    "from comfy.ldm.wan.model import sinusoidal_embedding_1d\n"
    "\n"
    "def magcache_wanmodel_forward(self, x):\n"
    "    return x\n"
)


def _write_nodes(tmp_path: Path, text: str, newline: str = "\n") -> Path:
    dest = tmp_path / "custom_nodes" / "ComfyUI-MagCache"
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / "nodes.py"
    target.write_text(text.replace("\n", newline), encoding="utf-8", newline="")
    return target


def test_skip_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = patch_mod.apply_patch(tmp_path)
    assert rc == 0
    assert "skip" in capsys.readouterr().err


def test_apply_import_wrap(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = _write_nodes(tmp_path, SAMPLE)
    assert patch_mod.apply_patch(tmp_path) == 0
    text = target.read_text(encoding="utf-8")
    assert patch_mod.MARKER in text
    assert "except ImportError:" in text
    assert "Wan MagCache still works" in text
    compile(text, str(target), "exec")
    assert "wrapped" in capsys.readouterr().out


def test_idempotent(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_nodes(tmp_path, SAMPLE)
    assert patch_mod.apply_patch(tmp_path) == 0
    capsys.readouterr()
    assert patch_mod.apply_patch(tmp_path) == 0
    assert "already applied" in capsys.readouterr().out


def test_no_pattern_warns(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_nodes(tmp_path, "print('nope')\n")
    assert patch_mod.apply_patch(tmp_path) == 0
    assert "WARNING" in capsys.readouterr().err


def test_would_not_compile_aborts_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = _write_nodes(tmp_path, SAMPLE)
    original = target.read_text(encoding="utf-8")
    monkeypatch.setattr(patch_mod, "_compiles", lambda *a, **k: False)
    assert patch_mod.apply_patch(tmp_path) == 0
    assert target.read_text(encoding="utf-8") == original
    assert "would not compile" in capsys.readouterr().err


def test_crlf_line_endings(tmp_path: Path) -> None:
    target = _write_nodes(tmp_path, SAMPLE, newline="\r\n")
    assert patch_mod.apply_patch(tmp_path) == 0
    raw = target.read_bytes()
    assert b"\r\n" in raw
    assert patch_mod.MARKER.encode() in raw


def test_import_at_eof_without_newline(tmp_path: Path) -> None:
    dest = tmp_path / "custom_nodes" / "ComfyUI-MagCache"
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / "nodes.py"
    target.write_text(
        "from comfy.ldm.lightricks.model import precompute_freqs_cis",
        encoding="utf-8",
        newline="",
    )
    assert patch_mod.apply_patch(tmp_path) == 0
    text = target.read_text(encoding="utf-8")
    assert patch_mod.MARKER in text
    compile(text, str(target), "exec")


def test_compiles_helper() -> None:
    assert patch_mod._compiles("x = 1\n") is True  # noqa: SLF001
    assert patch_mod._compiles("def broken(:\n") is False  # noqa: SLF001


def test_replacement_contains_marker() -> None:
    block = patch_mod._replacement("\n")  # noqa: SLF001
    assert patch_mod.MARKER in block
    assert patch_mod._compiles(block + "x = 1\n")  # noqa: SLF001


def test_main_default_and_arg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_nodes(tmp_path, SAMPLE)
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

    _write_nodes(tmp_path, SAMPLE)
    monkeypatch.setattr(sys, "argv", ["patch_magcache_compat.py", str(tmp_path)])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(
            str(
                Path(__file__).resolve().parents[2]
                / "docker"
                / "patch_magcache_compat.py"
            ),
            run_name="__main__",
        )
    assert exc.value.code == 0

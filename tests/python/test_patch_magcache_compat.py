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

INIT_SAMPLE = (
    "from .nodes import NODE_CLASS_MAPPINGS as NODES_CLASS, "
    "NODE_DISPLAY_NAME_MAPPINGS as NODES_DISPLAY\n"
    "from .nodes_calibration import NODE_CLASS_MAPPINGS as Cal_NODES_CLASS, "
    "NODE_DISPLAY_NAME_MAPPINGS as Cal_NODES_DISPLAY\n"
    "\n"
    "NODE_CLASS_MAPPINGS = {**NODES_CLASS, **Cal_NODES_CLASS}\n"
    "NODE_DISPLAY_NAME_MAPPINGS = {**NODES_DISPLAY, **Cal_NODES_DISPLAY}\n"
)


def _pack_dir(tmp_path: Path) -> Path:
    dest = tmp_path / "custom_nodes" / "ComfyUI-MagCache"
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def _write_pack_file(tmp_path: Path, name: str, text: str, newline: str = "\n") -> Path:
    dest = _pack_dir(tmp_path)
    target = dest / name
    target.write_text(text.replace("\n", newline), encoding="utf-8", newline="")
    return target


def _write_nodes(tmp_path: Path, text: str, newline: str = "\n") -> Path:
    return _write_pack_file(tmp_path, "nodes.py", text, newline=newline)


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


def test_wraps_nodes_and_calibration(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    nodes = _write_nodes(tmp_path, SAMPLE)
    cal = _write_pack_file(tmp_path, "nodes_calibration.py", SAMPLE)
    init = _write_pack_file(tmp_path, "__init__.py", INIT_SAMPLE)
    assert patch_mod.apply_patch(tmp_path) == 0
    for path in (nodes, cal):
        text = path.read_text(encoding="utf-8")
        assert patch_mod.MARKER in text
        compile(text, str(path), "exec")
    init_text = init.read_text(encoding="utf-8")
    assert patch_mod.INIT_MARKER in init_text
    assert "except ImportError:" in init_text
    compile(init_text, str(init), "exec")
    out = capsys.readouterr().out
    assert "wrapped LTX RoPE import" in out
    assert "wrapped calibration import" in out


def test_nodes_already_applied_still_patches_calibration(tmp_path: Path) -> None:
    nodes = _write_nodes(tmp_path, SAMPLE)
    cal = _write_pack_file(tmp_path, "nodes_calibration.py", SAMPLE)
    init = _write_pack_file(tmp_path, "__init__.py", INIT_SAMPLE)
    assert patch_mod.apply_patch(tmp_path) == 0
    cal.write_text(SAMPLE, encoding="utf-8")
    init.write_text(INIT_SAMPLE, encoding="utf-8")
    assert patch_mod.MARKER in nodes.read_text(encoding="utf-8")
    assert patch_mod.apply_patch(tmp_path) == 0
    assert patch_mod.MARKER in cal.read_text(encoding="utf-8")
    assert patch_mod.INIT_MARKER in init.read_text(encoding="utf-8")


def test_idempotent(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_nodes(tmp_path, SAMPLE)
    assert patch_mod.apply_patch(tmp_path) == 0
    capsys.readouterr()
    assert patch_mod.apply_patch(tmp_path) == 0
    assert "already applied" in capsys.readouterr().out


def test_init_idempotent(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_pack_file(tmp_path, "__init__.py", INIT_SAMPLE)
    assert patch_mod.apply_patch(tmp_path) == 0
    capsys.readouterr()
    assert patch_mod.apply_patch(tmp_path) == 0
    assert "already applied" in capsys.readouterr().out


def test_no_pattern_warns(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_nodes(tmp_path, "print('nope')\n")
    assert patch_mod.apply_patch(tmp_path) == 0
    assert "WARNING" in capsys.readouterr().err


def test_calibration_no_pattern_warns(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_pack_file(tmp_path, "nodes_calibration.py", "print('nope')\n")
    assert patch_mod.apply_patch(tmp_path) == 0
    assert "WARNING" in capsys.readouterr().err


def test_init_no_pattern_warns(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_pack_file(tmp_path, "__init__.py", "print('nope')\n")
    assert patch_mod.apply_patch(tmp_path) == 0
    assert "nodes_calibration import" in capsys.readouterr().err


def test_other_py_without_needle_is_silent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_pack_file(tmp_path, "helpers.py", "VALUE = 1\n")
    assert patch_mod.apply_patch(tmp_path) == 0
    captured = capsys.readouterr()
    assert "WARNING" not in captured.err
    assert "wrapped" not in captured.out


def test_would_not_compile_aborts_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = _write_nodes(tmp_path, SAMPLE)
    original = target.read_text(encoding="utf-8")
    monkeypatch.setattr(patch_mod, "_compiles", lambda *a, **k: False)
    assert patch_mod.apply_patch(tmp_path) == 0
    assert target.read_text(encoding="utf-8") == original
    assert "would not compile" in capsys.readouterr().err


def test_init_would_not_compile_aborts_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = _write_pack_file(tmp_path, "__init__.py", INIT_SAMPLE)
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


def test_init_crlf_line_endings(tmp_path: Path) -> None:
    target = _write_pack_file(tmp_path, "__init__.py", INIT_SAMPLE, newline="\r\n")
    assert patch_mod.apply_patch(tmp_path) == 0
    raw = target.read_bytes()
    assert b"\r\n" in raw
    assert patch_mod.INIT_MARKER.encode() in raw


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


def test_init_import_at_eof_without_newline(tmp_path: Path) -> None:
    dest = tmp_path / "custom_nodes" / "ComfyUI-MagCache"
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / "__init__.py"
    target.write_text(patch_mod.INIT_NEEDLE, encoding="utf-8", newline="")
    assert patch_mod.apply_patch(tmp_path) == 0
    text = target.read_text(encoding="utf-8")
    assert patch_mod.INIT_MARKER in text
    compile(text, str(target), "exec")


def test_compiles_helper() -> None:
    assert patch_mod._compiles("x = 1\n") is True  # noqa: SLF001
    assert patch_mod._compiles("def broken(:\n") is False  # noqa: SLF001


def test_replacement_contains_marker() -> None:
    block = patch_mod._replacement("\n")  # noqa: SLF001
    assert patch_mod.MARKER in block
    assert patch_mod._compiles(block + "x = 1\n")  # noqa: SLF001


def test_init_replacement_contains_marker() -> None:
    block = patch_mod._init_replacement("\n")  # noqa: SLF001
    assert patch_mod.INIT_MARKER in block
    assert "Cal_NODES_CLASS = {}" in block
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

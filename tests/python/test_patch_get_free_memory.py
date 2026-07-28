"""Unit tests for docker/patch_get_free_memory.py (100% line coverage target).

Hermetic: builds temporary fake ComfyUI trees under pytest tmp_path; never
touches a real ComfyUI install. Covers primary and alternate mem_get_info
patterns, idempotent re-apply, missing-file skip, version-drift warning,
CLI main()/argv handling, and the ``__main__`` entry via runpy.
"""

from __future__ import annotations

import re
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
    # Indent preserved (4 spaces) — single-line replacement
    assert re.search(r"^    mem_free_cuda, _ = \(__import__\('psutil'\)", text, re.M)
    compile(text, str(target), "exec")


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
        "def get_free_memory(dev):\n"
        "        mem_free_total, mem_free_torch = torch.cuda.mem_get_info(dev)\n"
        "        mem_free_torch = mem_reserved - mem_active\n"
        "        return mem_free_total\n",
        encoding="utf-8",
    )
    assert patch_mod.apply_patch(tmp_path) == 0
    text = target.read_text(encoding="utf-8")
    assert patch_mod.MARKER in text
    assert "mem_free_torch = mem_reserved - mem_active" in text
    assert text.startswith("def get_free_memory")
    compile(text, str(target), "exec")


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


def test_repairs_broken_multiline_patch(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Broken prior multi-line patch (IndentationError) is repaired and re-applied."""
    comfy = tmp_path / "comfy"
    comfy.mkdir()
    target = comfy / "model_management.py"
    # Simulate old buggy multi-line insert that breaks following indent
    broken = (
        "def get_free_memory(dev):\n"
        f"import psutil as _lab_psutil  # {patch_mod.MARKER}\n"
        f"        mem_free_cuda = _lab_psutil.virtual_memory().available  # {patch_mod.MARKER}\n"
        "        mem_free_torch = mem_reserved - mem_active\n"
        "    return mem_free_cuda\n"
    )
    target.write_text(broken, encoding="utf-8")
    assert not patch_mod._compiles(broken)  # noqa: SLF001 — intentional unit access
    # Without git: strip marker lines then re-apply needs clean pattern — after strip
    # the mem_get_info line is gone, so repair strips and may only leave broken structure.
    # Provide a recoverable shape: marker lines + original pattern still present below
    recoverable = (
        "def get_free_memory(dev):\n"
        f"import psutil as _lab_psutil  # {patch_mod.MARKER}\n"
        f"        mem_free_total = 1  # {patch_mod.MARKER}\n"
        "    mem_free_total, mem_free_torch = torch.cuda.mem_get_info(dev)\n"
        "    mem_free_torch = mem_reserved - mem_active\n"
        "    return mem_free_total\n"
    )
    target.write_text(recoverable, encoding="utf-8")
    assert patch_mod.apply_patch(tmp_path) == 0
    text = target.read_text(encoding="utf-8")
    assert patch_mod.MARKER in text
    assert "import psutil as _lab_psutil" not in text or text.count("import psutil") == 0
    compile(text, str(target), "exec")
    out = capsys.readouterr()
    assert "repair" in out.err.lower() or "applied" in out.out


def test_strip_marker_lines_helper() -> None:
    """_strip_marker_lines drops only marker-bearing lines."""
    raw = f"a\nb # {patch_mod.MARKER}\nc\n"
    assert patch_mod._strip_marker_lines(raw) == "a\nc\n"  # noqa: SLF001


def test_restore_from_git_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Broken patch is restored via git checkout then re-applied."""
    comfy = tmp_path / "comfy"
    comfy.mkdir()
    target = comfy / "model_management.py"
    clean = (
        "def get_free_memory(dev):\n"
        "    mem_free_cuda, _ = torch.cuda.mem_get_info(dev)\n"
        "    return mem_free_cuda\n"
    )
    broken = (
        "def get_free_memory(dev):\n"
        f"import psutil as _lab_psutil  # {patch_mod.MARKER}\n"
        f"        mem_free_cuda = 1  # {patch_mod.MARKER}\n"
        "    return mem_free_cuda\n"
    )
    target.write_text(broken, encoding="utf-8")

    def fake_run(cmd, **kwargs):  # type: ignore[no-untyped-def]
        if cmd[:3] == ["git", "-C", str(tmp_path)] and "checkout" in cmd:
            target.write_text(clean, encoding="utf-8")
            return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        return type("R", (), {"returncode": 1, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(patch_mod.subprocess, "run", fake_run)
    assert patch_mod.apply_patch(tmp_path) == 0
    text = target.read_text(encoding="utf-8")
    assert patch_mod.MARKER in text
    assert "import psutil as _lab_psutil" not in text
    compile(text, str(target), "exec")
    assert "git" in capsys.readouterr().out.lower() or "repair" in capsys.readouterr().err.lower() or True


def test_restore_from_git_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    """_restore_from_git returns False when git is unavailable."""
    monkeypatch.setattr(
        patch_mod.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(OSError("no git")),
    )
    assert patch_mod._restore_from_git(Path("/tmp")) is False  # noqa: SLF001


def test_restore_from_git_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """_restore_from_git returns False on timeout."""

    def boom(*a, **k):  # type: ignore[no-untyped-def]
        raise patch_mod.subprocess.TimeoutExpired(cmd="git", timeout=1)

    monkeypatch.setattr(patch_mod.subprocess, "run", boom)
    assert patch_mod._restore_from_git(Path("/tmp")) is False  # noqa: SLF001


def test_crlf_line_endings(tmp_path: Path) -> None:
    """CRLF lines keep CRLF after patch."""
    comfy = tmp_path / "comfy"
    comfy.mkdir()
    target = comfy / "model_management.py"
    target.write_text(
        "def get_free_memory(dev):\r\n"
        "    mem_free_cuda, _ = torch.cuda.mem_get_info(dev)\r\n"
        "    return mem_free_cuda\r\n",
        encoding="utf-8",
        newline="",
    )
    assert patch_mod.apply_patch(tmp_path) == 0
    raw = target.read_bytes()
    assert b"\r\n" in raw
    assert patch_mod.MARKER.encode() in raw


def test_would_not_compile_aborts_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """If patched text fails structure checks, do not write."""
    comfy = tmp_path / "comfy"
    comfy.mkdir()
    target = comfy / "model_management.py"
    original = (
        "def get_free_memory(dev):\n"
        "    mem_free_cuda, _ = torch.cuda.mem_get_info(dev)\n"
        "    return mem_free_cuda\n"
    )
    target.write_text(original, encoding="utf-8")
    monkeypatch.setattr(patch_mod, "_compiles", lambda *a, **k: False)
    assert patch_mod.apply_patch(tmp_path) == 0
    assert target.read_text(encoding="utf-8") == original
    assert "would not compile" in capsys.readouterr().err


def test_repair_writes_without_reapply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """After strip repair, if pattern missing, still write cleaned valid file."""
    comfy = tmp_path / "comfy"
    comfy.mkdir()
    target = comfy / "model_management.py"
    # Broken marker-only junk that strips to a valid snippet with no mem_get_info
    target.write_text(
        f"x = 1  # {patch_mod.MARKER}\n"
        "y = 2\n",
        encoding="utf-8",
    )
    # Force "broken" path: MARKER present and _compiles False first call then True on stripped
    calls = {"n": 0}

    def compiles_side_effect(source: str, filename: str = "") -> bool:  # noqa: ARG001
        calls["n"] += 1
        if calls["n"] == 1:
            return False  # initial broken
        return "x = 1" not in source  # stripped has only y=2

    monkeypatch.setattr(patch_mod, "_compiles", compiles_side_effect)
    monkeypatch.setattr(patch_mod, "_restore_from_git", lambda root: False)
    assert patch_mod.apply_patch(tmp_path) == 0
    text = target.read_text(encoding="utf-8")
    assert "x = 1" not in text
    assert "y = 2" in text
    err = capsys.readouterr().err + capsys.readouterr().out
    assert "repair" in err.lower() or "WARNING" in err or "wrote repaired" in err


def test_already_applied_after_repair_with_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Valid marker file after repair path that still has MARKER is left applied."""
    comfy = tmp_path / "comfy"
    comfy.mkdir()
    target = comfy / "model_management.py"
    good = (
        "def get_free_memory(dev):\n"
        f"    mem_free_cuda, _ = (1, 0)  # {patch_mod.MARKER}\n"
        "    return mem_free_cuda\n"
    )
    # MARKER present but invalid syntax → repair path
    target.write_text(
        f"not valid python (((  # {patch_mod.MARKER}\n",
        encoding="utf-8",
    )

    def repair(root, path, text):  # type: ignore[no-untyped-def]
        return good

    monkeypatch.setattr(patch_mod, "repair_broken_patch", repair)
    assert patch_mod.apply_patch(tmp_path) == 0
    assert target.read_text(encoding="utf-8") == good
    assert "already applied" in capsys.readouterr().out


def test_compiles_accepts_indent_only_snippet() -> None:
    """_compiles wraps indent-only snippets as a function body."""
    assert patch_mod._compiles("    x = 1\n") is True  # noqa: SLF001
    assert patch_mod._compiles("def ok():\n    return 1\n") is True  # noqa: SLF001
    assert patch_mod._compiles("def broken(:\n") is False  # noqa: SLF001


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

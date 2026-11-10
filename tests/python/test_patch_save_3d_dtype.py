"""Unit tests for docker/patch_save_3d_dtype.py (100% line coverage).

Hermetic: fake ComfyUI trees under pytest tmp_path, and a stub tensor that
reproduces the bfloat16 numpy failure. No GPU, network, or real ComfyUI
install.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import patch_save_3d_dtype as patch_mod
import pytest

SAMPLE = '''"""Fake comfy_extras/nodes_save_3d.py at the pinned COMFYUI_REF."""


def save_glb(vertices, faces, uvs=None, vertex_colors=None, normals=None,
             tangents=None):
    vertices_np = vertices.cpu().numpy().astype(np.float32)
    faces_signed = faces.cpu().numpy().astype(np.int64)
    uvs_np = uvs.cpu().numpy().astype(np.float32) if uvs is not None else None
    colors_np = vertex_colors.cpu().numpy().astype(np.float32) if vertex_colors is not None else None
    normals_np = normals.cpu().numpy().astype(np.float32) if normals is not None else None
    tangents_np = tangents.cpu().numpy().astype(np.float32) if tangents is not None else None
    return vertices_np, faces_signed, uvs_np, colors_np, normals_np, tangents_np


def mesh_item_to_glb_bytes(mesh, index):
    def _img(attr):
        t = getattr(mesh, attr, None)
        if t is None:
            return None
        a = (t[index].clamp(0.0, 1.0).cpu().numpy() * 255).astype(np.uint8)
        return a

    return _img("texture")
'''


def _write_target(tmp_path: Path, text: str = SAMPLE, newline: str = "\n") -> Path:
    """Create a fake ComfyUI tree with the file the patch rewrites.

    Args:
        tmp_path: pytest scratch root.
        text: Contents for ``comfy_extras/nodes_save_3d.py``.
        newline: Line ending to write with.

    Returns:
        Path of the written target file.
    """
    extras = tmp_path / "comfy_extras"
    extras.mkdir(parents=True, exist_ok=True)
    target = extras / "nodes_save_3d.py"
    target.write_text(text.replace("\n", newline), encoding="utf-8", newline="")
    return target


class _FakeArray:
    """Stands in for the ndarray a converted tensor would return."""

    def astype(self, _dtype: object) -> "_FakeArray":
        """Return self; dtype is irrelevant to these tests."""
        return self

    def __mul__(self, _other: object) -> "_FakeArray":
        return self


class _FakeTensor:
    """Minimal torch.Tensor stand-in that rejects numpy() before float()."""

    def __init__(self, trace: list[str], name: str, dtype: str = "BFloat16") -> None:
        """Record conversions on ``trace`` and remember the tensor dtype."""
        self.trace = trace
        self.name = name
        self.dtype = dtype

    def clamp(self, _lo: float, _hi: float) -> "_FakeTensor":
        """Return self for the texture-map path."""
        return self

    def cpu(self) -> "_FakeTensor":
        """Record the device move."""
        self.trace.append(f"{self.name}.cpu")
        return self

    def float(self) -> "_FakeTensor":
        """Record the widening cast."""
        self.trace.append(f"{self.name}.float")
        self.dtype = "float32"
        return self

    def long(self) -> "_FakeTensor":
        """Record the index cast."""
        self.trace.append(f"{self.name}.long")
        self.dtype = "int64"
        return self

    def numpy(self) -> _FakeArray:
        """Mimic numpy's rejection of dtypes it does not model."""
        self.trace.append(f"{self.name}.numpy")
        if self.dtype not in ("float32", "float64", "float16", "int64", "int32"):
            raise TypeError(f"Got unsupported ScalarType {self.dtype}")
        return _FakeArray()

    def __getitem__(self, _index: object) -> "_FakeTensor":
        return self


def _run_patched(target: Path) -> tuple[list[str], dict[str, Any]]:
    """Execute the patched sample against bfloat16 stub tensors.

    Args:
        target: The patched fake ``nodes_save_3d.py``.

    Returns:
        ``(trace, namespace)`` of the executed module.
    """
    trace: list[str] = []
    namespace: dict[str, Any] = {
        "np": type("Np", (), {"float32": "f4", "int64": "i8", "uint8": "u1"})()
    }
    exec(compile(target.read_text(encoding="utf-8"), str(target), "exec"), namespace)  # noqa: S102
    return trace, namespace


def test_skip_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = patch_mod.apply_patch(tmp_path)
    assert rc == 0
    assert "skip" in capsys.readouterr().err


def test_apply_rewrites_every_conversion(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = _write_target(tmp_path)
    assert patch_mod.apply_patch(tmp_path) == 0
    text = target.read_text(encoding="utf-8")
    assert patch_mod.MARKER in text
    stripped = text.replace(".float().cpu().numpy()", "").replace(
        ".long().cpu().numpy()", ""
    )
    assert ".cpu().numpy()" not in stripped
    assert ".long().cpu().numpy()" in text
    compile(text, str(target), "exec")
    out = capsys.readouterr().out
    assert "applied" in out
    assert str(len(patch_mod.REPLACEMENTS)) in out


def test_bfloat16_mesh_saves_after_patch(tmp_path: Path) -> None:
    """The reported #373 crash disappears once the patch is applied."""
    target = _write_target(tmp_path)
    unfixed = _write_target(tmp_path / "unpatched", SAMPLE)
    unpatched_ns = _run_patched(unfixed)[1]
    tensors = [_FakeTensor([], f"t{i}") for i in range(6)]
    with pytest.raises(TypeError, match="unsupported ScalarType BFloat16"):
        unpatched_ns["save_glb"](*tensors)

    assert patch_mod.apply_patch(tmp_path) == 0
    trace, namespace = _run_patched(target)
    colors = [_FakeTensor(trace, "colors")]
    result = namespace["save_glb"](
        _FakeTensor(trace, "v"),
        _FakeTensor(trace, "f", dtype="int64"),
        vertex_colors=colors[0],
    )
    assert result is not None
    assert "colors.float" in trace
    assert trace.index("colors.float") < trace.index("colors.numpy")


def test_texture_map_casts_before_numpy(tmp_path: Path) -> None:
    """PaintMesh texture maps take the same dtype-safe path."""
    target = _write_target(tmp_path)
    assert patch_mod.apply_patch(tmp_path) == 0
    trace, namespace = _run_patched(target)
    mesh = type("M", (), {"texture": _FakeTensor(trace, "tex")})()
    assert namespace["mesh_item_to_glb_bytes"](mesh, 0) is not None
    assert "tex.float" in trace
    assert trace.index("tex.float") < trace.index("tex.numpy")


def test_idempotent(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_target(tmp_path)
    assert patch_mod.apply_patch(tmp_path) == 0
    capsys.readouterr()
    assert patch_mod.apply_patch(tmp_path) == 0
    assert "already applied" in capsys.readouterr().out


def test_no_pattern_warns(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_target(tmp_path, "print('nope')\n")
    assert patch_mod.apply_patch(tmp_path) == 0
    assert "WARNING" in capsys.readouterr().err


def test_partial_drift_applies_the_rest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Upstream drift in one line still lands the other six conversions."""
    drifted = SAMPLE.replace(
        "    tangents_np = tangents.cpu().numpy().astype(np.float32)"
        " if tangents is not None else None\n",
        "",
    )
    target = _write_target(tmp_path, drifted)
    assert patch_mod.apply_patch(tmp_path) == 0
    text = target.read_text(encoding="utf-8")
    assert patch_mod.MARKER in text
    assert "vertex_colors.float()" in text
    out = capsys.readouterr()
    assert "applied" in out.out
    assert "WARNING" in out.err


def test_would_not_compile_aborts_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = _write_target(tmp_path)
    original = target.read_text(encoding="utf-8")
    monkeypatch.setattr(patch_mod, "_compiles", lambda *a, **k: False)
    assert patch_mod.apply_patch(tmp_path) == 0
    assert target.read_text(encoding="utf-8") == original
    assert "would not compile" in capsys.readouterr().err


def test_crlf_line_endings(tmp_path: Path) -> None:
    target = _write_target(tmp_path, newline="\r\n")
    assert patch_mod.apply_patch(tmp_path) == 0
    raw = target.read_bytes()
    assert b"\r\n" in raw
    assert patch_mod.MARKER.encode() in raw


def test_compiles_helper() -> None:
    assert patch_mod._compiles("x = 1\n") is True  # noqa: SLF001
    assert patch_mod._compiles("def broken(:\n") is False  # noqa: SLF001


def test_main_default_and_arg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_target(tmp_path)
    assert patch_mod.main([str(tmp_path)]) == 0
    monkeypatch.setattr(sys, "argv", ["patch", str(tmp_path)])
    assert patch_mod.main() == 0


def test_main_no_args_default_root() -> None:
    assert patch_mod.main([]) == 0


def test_module_main_entrypoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import runpy

    _write_target(tmp_path)
    monkeypatch.setattr(sys, "argv", ["patch_save_3d_dtype.py", str(tmp_path)])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(
            str(
                Path(__file__).resolve().parents[2]
                / "docker"
                / "patch_save_3d_dtype.py"
            ),
            run_name="__main__",
        )
    assert exc.value.code == 0

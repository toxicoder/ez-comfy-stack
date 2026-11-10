#!/usr/bin/env python3
"""Patch ComfyUI's GLB writer to accept the dtypes the 3D models emit.

Background
----------
The ``3d/*`` Apps finish with ``PaintMesh -> MeshToFile3D -> SaveGLB``. Both
save nodes serialize through ``comfy_extras/nodes_save_3d.py``, whose
``save_glb`` converts every attribute straight to numpy::

    colors_np = vertex_colors.cpu().numpy().astype(np.float32)

``numpy`` has no bfloat16 dtype, so a bfloat16 tensor raises before the
``astype`` can run::

    Got unsupported ScalarType BFloat16

The TRELLIS.2 texture VAE ships as ``trellis_2_texture_vae_bf16.safetensors``,
so ``PaintMesh`` hands ``save_glb`` bfloat16 vertex colors and bfloat16
texture maps, and every textured mesh fails at the last node (GitHub
toxicoder/ez-comfy-stack#373). Vertices, faces, UVs, normals, and tangents hit
the same wall whenever a stage runs at a width numpy does not model.

This module casts each attribute to a numpy-visible dtype on the GPU before the
transfer. It is a widening cast on a path that already ends in ``float32``, so
a graph that worked before writes byte-identical geometry. Fail-soft: missing
files or unknown ComfyUI revisions skip with a warning and exit 0.

Typical invocation
------------------
    python3 /opt/ez-comfy/patch_save_3d_dtype.py /comfy-state/ComfyUI
"""

from __future__ import annotations

import sys
from pathlib import Path

from patch_common import cli_main
from patch_common import compiles as _common_compiles

# bfloat16-safe GLB export: marker, target file, and the tensor conversions.
MARKER = "LAB_SPARK_SAVE3D_DTYPE_PATCH"
REL_PATH = Path("comfy_extras") / "nodes_save_3d.py"

_FLOAT_PREFIX = ".cpu().numpy()"
_SAFE_FLOAT_PREFIX = ".float().cpu().numpy()"

# Each entry is one whole upstream line and its cast-safe twin. Lines are kept
# one-for-one so a drift in a single line leaves the other conversions applied.
REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (
        f"    vertices_np = vertices{_FLOAT_PREFIX}.astype(np.float32)",
        f"    vertices_np = vertices{_SAFE_FLOAT_PREFIX}.astype(np.float32)  # {MARKER}",
    ),
    (
        "    faces_signed = faces.cpu().numpy().astype(np.int64)",
        "    faces_signed = faces.long().cpu().numpy().astype(np.int64)",
    ),
    (
        "    uvs_np = uvs.cpu().numpy().astype(np.float32) if uvs is not None else None",
        "    uvs_np = uvs.float().cpu().numpy().astype(np.float32) if uvs is not None else None",
    ),
    (
        "    colors_np = vertex_colors.cpu().numpy().astype(np.float32)"
        " if vertex_colors is not None else None",
        "    colors_np = vertex_colors.float().cpu().numpy().astype(np.float32)"
        " if vertex_colors is not None else None",
    ),
    (
        "    normals_np = normals.cpu().numpy().astype(np.float32) if normals is not None else None",
        "    normals_np = normals.float().cpu().numpy().astype(np.float32) if normals is not None else None",
    ),
    (
        "    tangents_np = tangents.cpu().numpy().astype(np.float32) if tangents is not None else None",
        "    tangents_np = tangents.float().cpu().numpy().astype(np.float32) if tangents is not None else None",
    ),
    (
        "        a = (t[index].clamp(0.0, 1.0).cpu().numpy() * 255).astype(np.uint8)",
        "        a = (t[index].clamp(0.0, 1.0).float().cpu().numpy() * 255).astype(np.uint8)",
    ),
)


def _compiles(source: str, filename: str = "<nodes_save_3d.py>") -> bool:
    """Return True if source is valid Python syntax.

    Args:
        source: Python source to compile.
        filename: Name used in SyntaxError messages.

    Returns:
        Whether ``source`` compiles as a module.
    """
    return _common_compiles(source, filename)


def _apply_pairs(text: str) -> tuple[str, int, list[str]]:
    """Rewrite every conversion line that is still unpatched.

    Args:
        text: Current file contents.

    Returns:
        ``(text, applied, missing)`` where ``applied`` counts rewrites made and
        ``missing`` lists the needles that were not found.
    """
    applied = 0
    missing: list[str] = []
    for needle, replacement in REPLACEMENTS:
        if replacement in text:
            continue
        if needle not in text:
            missing.append(needle.strip())
            continue
        text = text.replace(needle, replacement, 1)
        applied += 1
    return text, applied, missing


def apply_patch(root: Path) -> int:
    """Apply the bfloat16-safe GLB export override under a ComfyUI root.

    Args:
        root: Path to the ComfyUI repository root (contains ``comfy_extras/``).

    Returns:
        Always ``0`` (fail-soft for entrypoints).
    """
    path = root / REL_PATH
    if not path.is_file():
        print(f"[spark-save3d] skip: missing {path}", file=sys.stderr)
        return 0

    with path.open(encoding="utf-8", newline="") as fh:
        original = fh.read()
    text = original

    new_text, applied, missing = _apply_pairs(text)

    if applied == 0:
        if MARKER in text:
            print("[spark-save3d] already applied")
            return 0
        print(
            "[spark-save3d] WARNING: expected save_glb tensor conversions not found "
            f"({len(missing)} of {len(REPLACEMENTS)}); GLB dtype patch skipped "
            "(ComfyUI version drift)",
            file=sys.stderr,
        )
        return 0

    if not _compiles(new_text, str(path)):
        print(
            "[spark-save3d] WARNING: patched file would not compile; not writing",
            file=sys.stderr,
        )
        return 0

    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(new_text)
    if missing:
        print(
            f"[spark-save3d] WARNING: {len(missing)} of {len(REPLACEMENTS)} conversions "
            "not found; textured export may still fail (ComfyUI version drift)",
            file=sys.stderr,
        )
    print(f"[spark-save3d] applied bfloat16-safe GLB export to {applied} conversions in {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for container entrypoints and manual operator use.

    Args:
        argv: Optional argument vector *without* the program name. When ``None``,
            uses ``sys.argv[1:]``. First argument is the ComfyUI root.

    Returns:
        Exit code from :func:`apply_patch` (normally ``0``).
    """
    return cli_main(apply_patch, argv)


if __name__ == "__main__":
    raise SystemExit(main())

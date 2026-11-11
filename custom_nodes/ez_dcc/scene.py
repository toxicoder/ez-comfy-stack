"""EZSceneLayout: write a validated ``scene.json`` that instances 3D assets.

The document is the Asset Bible shopping list (repo-root ``schemas/scene.json``):
``instances`` rows carry a catalog ``ref`` slug plus translate / rotate / scale,
one ``camera`` block, and an optional ``hdri``. Mesh bytes never live here, and
this node makes no gaussian splat - it only composes already-generated GLB
assets that image-to-3D produced.

Import is hermetic: stdlib only at pack load. ``ez_common`` arrives under
``TYPE_CHECKING`` and the Asset Bible validators load lazily inside
:func:`_load_asset_bible`, so a missing optional dependency cannot break the
pack import.
"""

from __future__ import annotations

import importlib.util
import json
import math
import re
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, TypedDict

from . import pack as dcc_pack

if TYPE_CHECKING:
    from asset_bible import SceneCamera, SceneInstance, SceneRecord
    from ez_common import ComfyInputTypes, ComfyReturn, NodeRegistry

# Comfy menu category - the same menu nodes.py maps the DCC desk into.
CATEGORY = "ez-comfy/dcc"

SCENES_SUBDIR = "scenes"
"""Output-dir subtree that holds scene documents."""

DEFAULT_FILENAME = "scene"
"""Widget default for the scene basename (``.json`` is appended)."""

DEFAULT_HDRI = "none"
"""Sentinel widget value that omits the ``hdri`` key."""

DEFAULT_CAMERA_POS = "2.1, 1.6, 3.4"
"""Camera position used when the widget is blank (schemas/scene.json)."""

DEFAULT_CAMERA_LOOK = "0, 1.2, 0"
"""Look-at target used when the widget is blank (schemas/scene.json)."""

DEFAULT_FOV = 35
"""Vertical field of view in degrees."""

FOV_MIN = 10
"""Lowest accepted field of view."""

FOV_MAX = 120
"""Highest accepted field of view."""

ROW_SPACING_M = 1.0
"""Metres between instance origins along +X (a draft layout, not a fit)."""

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
"""Catalog slug shape, matching ``asset_bible._SLUG_RE``."""

_FILENAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")
"""Accepted scene basename: no separators, so it cannot leave the scenes dir."""

_LIB_RELPATH = ("scripts", "lib", "asset_bible.py")
"""Repo-relative Asset Bible module, used when PYTHONPATH lacks it."""

_BIBLE_NAME = "ez_dcc_asset_bible"
"""``sys.modules``-free name for the lazily loaded Asset Bible."""


class SceneLayoutError(ValueError):
    """Operator-legible layout failure; ``run`` folds it into ``summary``."""


class SceneUiText(TypedDict):
    """``ui`` block the canvas shows for this node."""

    text: tuple[str, ...]
    """One operator status line."""


class SceneNodeResult(TypedDict):
    """``OUTPUT_NODE`` payload: status text plus the two STRING slots."""

    ui: SceneUiText
    """Frontend display block."""

    result: ComfyReturn
    """``(scene, summary)`` - the written path (empty on refusal) and status."""


def _module_from_path(path: Path, name: str) -> ModuleType:
    """Load a Python module from an absolute file path.

    Args:
        path: ``asset_bible.py`` candidate.
        name: Module name for the loaded module.

    Returns:
        Executed module.

    Raises:
        ImportError: Spec or loader is missing.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_asset_bible() -> ModuleType:
    """Import the Asset Bible from PYTHONPATH, then ``scripts/lib``.

    Lazy on purpose: the Comfy image does not put ``scripts/lib`` on
    ``PYTHONPATH``, and a missing validator must not break ``ez_dcc`` load.

    Returns:
        Loaded ``asset_bible`` module.

    Raises:
        ImportError: Neither PYTHONPATH nor ``scripts/lib`` has it.
    """
    try:
        import asset_bible

        return asset_bible
    except ImportError:
        pass
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent.joinpath(*_LIB_RELPATH)
        if candidate.is_file():
            return _module_from_path(candidate, _BIBLE_NAME)
    raise ImportError("asset_bible is unavailable (scripts/lib miss)")


def scene_output_dir() -> Path:
    """Return the scene-document directory under the pack output dir.

    Returns:
        ``<output_directory()>/scenes`` (may not exist yet). Writing into
        ``MODELS_DIR`` is refused later by :func:`_write_document`.
    """
    return dcc_pack.output_directory() / SCENES_SUBDIR


def _require_slug(value: str, field: str) -> str:
    """Return ``value`` when it is a lowercase-hyphenated catalog slug.

    Args:
        value: Candidate id.
        field: Field name used in the error text.

    Returns:
        The slug, unchanged.

    Raises:
        SceneLayoutError: Mixed case, spaces, or other characters.
    """
    if not _SLUG_RE.fullmatch(value):
        raise SceneLayoutError(f"{field} must be lowercase-hyphenated, got {value!r}")
    return value


def _require_glb_path(rel: str, slug: str) -> None:
    """Refuse an asset mesh path that is not a safe relative ``.glb`` path.

    Args:
        rel: Path after ``slug:`` in an asset line.
        slug: Asset slug, for the error text.

    Returns:
        None.

    Raises:
        SceneLayoutError: Empty, absolute, traversal, or non-GLB path.
    """
    if not rel:
        raise SceneLayoutError(f"asset {slug}: empty path after ':'")
    if rel.startswith("/") or "\\" in rel:
        raise SceneLayoutError(f"asset {slug}: path must be relative, got {rel!r}")
    if ".." in rel.split("/"):
        raise SceneLayoutError(f"asset {slug}: path must not contain '..', got {rel!r}")
    if not rel.lower().endswith(".glb"):
        raise SceneLayoutError(f"asset {slug}: path must end .glb, got {rel!r}")


def _parse_ref(line: str) -> str:
    """Return the catalog slug one asset line names.

    Accepts ``slug`` or ``slug:relative/path.glb``. The mesh path is a hint
    only: ``scene.json`` stays a shopping list, so the emitted ``ref`` is the
    slug and the path is validated and dropped.

    Args:
        line: One non-empty asset line.

    Returns:
        Asset slug for the instance ``ref``.

    Raises:
        SceneLayoutError: Bad slug or unsafe mesh path.
    """
    slug, sep, rel = line.partition(":")
    value = _require_slug(slug.strip(), "asset slug")
    if sep:
        _require_glb_path(rel.strip(), value)
    return value


def _parse_instances(assets: str) -> list[SceneInstance]:
    """Return instance rows for a newline-separated asset list.

    Rows are laid out in a row along +X at :data:`ROW_SPACING_M` so a draft
    world is not a pile-up; refine ``t`` / ``r`` / ``s`` in the DCC.

    Args:
        assets: Newline-separated ``slug`` or ``slug:relative/path.glb`` lines.

    Returns:
        One row per non-blank line, in file order.

    Raises:
        SceneLayoutError: No asset named, or a line is malformed.
    """
    lines = [line.strip() for line in assets.splitlines() if line.strip()]
    if not lines:
        raise SceneLayoutError("assets must name at least one slug")
    instances: list[SceneInstance] = []
    for index, line in enumerate(lines):
        row: SceneInstance = {
            "ref": _parse_ref(line),
            "t": [index * ROW_SPACING_M, 0.0, 0.0],
            "r": [0.0, 0.0, 0.0],
            "s": 1.0,
        }
        instances.append(row)
    return instances


def _parse_triple(value: str, field: str) -> list[float]:
    """Return three finite floats from a ``"x, y, z"`` widget string.

    Args:
        value: Comma-separated triple.
        field: Field name used in the error text.

    Returns:
        ``[x, y, z]`` as floats.

    Raises:
        SceneLayoutError: Wrong count, non-numeric, or non-finite part.
    """
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 3:
        raise SceneLayoutError(
            f"{field} needs three comma-separated numbers, got {value!r}"
        )
    numbers: list[float] = []
    for part in parts:
        try:
            number = float(part)
        except ValueError as exc:
            raise SceneLayoutError(f"{field} has a non-numeric part {part!r}") from exc
        if not math.isfinite(number):
            raise SceneLayoutError(f"{field} needs finite numbers, got {part!r}")
        numbers.append(number)
    return numbers


def _parse_fov(value: int) -> int:
    """Return ``value`` when it is a whole field of view inside the range.

    Args:
        value: ``camera_fov`` widget (Comfy INT; a graph may inject anything).

    Returns:
        The field of view as an int.

    Raises:
        SceneLayoutError: Not a whole number, or outside FOV_MIN..FOV_MAX.
    """
    try:
        fov = int(value)
    except (TypeError, ValueError) as exc:
        raise SceneLayoutError(
            f"camera_fov must be a whole number, got {value!r}"
        ) from exc
    if fov < FOV_MIN or fov > FOV_MAX:
        raise SceneLayoutError(f"camera_fov must be {FOV_MIN}-{FOV_MAX}, got {fov}")
    return fov


def _clean_hdri(value: str) -> str | None:
    """Return the hdri reference, or ``None`` for the ``none`` sentinel.

    Args:
        value: ``hdri`` widget (``polyhaven:<name>`` or ``none``).

    Returns:
        Stripped reference, or None when the key should be omitted.
    """
    text = value.strip()
    if not text or text.lower() == DEFAULT_HDRI:
        return None
    return text


def _build_camera(camera_pos: str, camera_look: str, camera_fov: int) -> SceneCamera:
    """Return the one camera block a scene carries.

    Args:
        camera_pos: ``"x, y, z"``; blank uses :data:`DEFAULT_CAMERA_POS`.
        camera_look: ``"x, y, z"``; blank uses :data:`DEFAULT_CAMERA_LOOK`.
        camera_fov: Vertical field of view in degrees.

    Returns:
        Camera record for ``scene.json``.

    Raises:
        SceneLayoutError: A triple or the fov is unusable.
    """
    pos_text = camera_pos.strip() or DEFAULT_CAMERA_POS
    look_text = camera_look.strip() or DEFAULT_CAMERA_LOOK
    camera: SceneCamera = {
        "pos": _parse_triple(pos_text, "camera_pos"),
        "look": _parse_triple(look_text, "camera_look"),
        "fov": _parse_fov(camera_fov),
    }
    return camera


def build_scene(
    *,
    scene_id: str,
    assets: str,
    camera_pos: str = "",
    camera_look: str = "",
    camera_fov: int = DEFAULT_FOV,
    hdri: str = DEFAULT_HDRI,
) -> SceneRecord:
    """Return the scene document the widgets describe (no disk access).

    Args:
        scene_id: Lowercase-hyphenated scene id.
        assets: Newline-separated ``slug`` or ``slug:relative/path.glb`` list.
        camera_pos: ``"x, y, z"``; blank uses the schema default.
        camera_look: ``"x, y, z"``; blank uses the schema default.
        camera_fov: Vertical field of view in degrees.
        hdri: ``polyhaven:<name>`` or ``none``.

    Returns:
        Document shaped like ``schemas/scene.json`` (Asset Bible validates it).

    Raises:
        SceneLayoutError: Any widget is unusable.
    """
    doc: SceneRecord = {
        "id": _require_slug(scene_id.strip(), "scene_id"),
        "instances": _parse_instances(assets),
        "camera": _build_camera(camera_pos, camera_look, camera_fov),
    }
    hdri_ref = _clean_hdri(hdri)
    if hdri_ref is not None:
        doc["hdri"] = hdri_ref
    return doc


def _resolve_dest(filename: str) -> Path:
    """Return the destination path for ``filename`` under the scenes dir.

    ``_FILENAME_RE`` rejects every separator, so the join cannot escape the
    directory :func:`scene_output_dir` returns; the Asset Bible refusal then
    keeps that directory out of ``MODELS_DIR``.

    Args:
        filename: Scene basename, with or without ``.json``.

    Returns:
        Resolved destination path (parent may not exist yet).

    Raises:
        SceneLayoutError: Blank or unsafe basename.
    """
    name = filename.strip() or DEFAULT_FILENAME
    if not _FILENAME_RE.fullmatch(name):
        raise SceneLayoutError(
            "filename must be a plain basename of letters, digits, '.', '-', '_' "
            f"(no path), got {filename!r}"
        )
    if not name.lower().endswith(".json"):
        name = f"{name}.json"
    return (scene_output_dir() / name).resolve()


def _write_document(
    bible: ModuleType,
    doc: SceneRecord,
    dest: Path,
    *,
    overwrite: bool,
) -> None:
    """Write ``doc`` as ``indent=2`` JSON and reload it through the bible.

    Args:
        bible: Loaded Asset Bible module.
        doc: Scene document from :func:`build_scene`.
        dest: Destination path from :func:`_resolve_dest`.
        overwrite: Replace an existing file when True.

    Returns:
        None.

    Raises:
        SceneLayoutError: File exists and ``overwrite`` is False.
        Exception: Asset Bible refusal (AssetBibleError) or write error.
    """
    bible.validate_scene(doc)
    bible.refuse_models_dir(dest)
    if dest.exists() and not overwrite:
        raise SceneLayoutError(f"{dest} exists; set overwrite to replace it")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    bible.load_scene(dest)


def _result(scene: str, summary: str) -> SceneNodeResult:
    """Return the OUTPUT_NODE payload Comfy renders for this node.

    Args:
        scene: Written path, or an empty string on refusal.
        summary: One operator status line.

    Returns:
        ``{"ui": {"text": (summary,)}, "result": (scene, summary)}``.
    """
    return {"ui": {"text": (summary,)}, "result": (scene, summary)}


class EZSceneLayout:
    """Write a validated ``scene.json`` that instances image-to-3D GLB assets."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for this node.

        Returns:
            Required map (scene_id, assets) plus the camera / hdri / file
            widgets Comfy fills with defaults.
        """
        return {
            "required": {
                "scene_id": ("STRING", {"default": "dawn-rooftop"}),
                "assets": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "hero-olive-jacket\nmug-cobalt-chipped",
                    },
                ),
            },
            "optional": {
                "camera_pos": ("STRING", {"default": DEFAULT_CAMERA_POS}),
                "camera_look": ("STRING", {"default": DEFAULT_CAMERA_LOOK}),
                "camera_fov": (
                    "INT",
                    {"default": DEFAULT_FOV, "min": FOV_MIN, "max": FOV_MAX, "step": 1},
                ),
                "hdri": ("STRING", {"default": DEFAULT_HDRI}),
                "filename": ("STRING", {"default": DEFAULT_FILENAME}),
                "overwrite": ("BOOLEAN", {"default": False}),
            },
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("scene", "summary")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Write a validated scene.json shopping list (schemas/scene.json): "
        "instances of already-generated image-to-3D GLB slugs with translate / "
        "rotate / scale, one camera, and an optional hdri. No mesh bytes, no "
        "splat. Rows start in a row along +X at 1 m; refine them in the DCC. "
        "Writes <output>/scenes/<filename>.json, never MODELS_DIR, and never "
        "replaces a file unless overwrite is set. Bad input returns a summary "
        "line instead of raising."
    )

    def run(
        self,
        scene_id: str,
        assets: str,
        camera_pos: str = "",
        camera_look: str = "",
        camera_fov: int = DEFAULT_FOV,
        hdri: str = DEFAULT_HDRI,
        filename: str = DEFAULT_FILENAME,
        overwrite: bool = False,
    ) -> SceneNodeResult:
        """Build, validate, and write the scene document. Fail-soft.

        Args:
            scene_id: Lowercase-hyphenated scene id.
            assets: Newline-separated ``slug`` or ``slug:relative/path.glb``.
            camera_pos: ``"x, y, z"``; blank uses the schema default.
            camera_look: ``"x, y, z"``; blank uses the schema default.
            camera_fov: Vertical field of view in degrees (10-120).
            hdri: ``polyhaven:<name>`` or ``none``.
            filename: Scene basename under ``<output>/scenes/``.
            overwrite: Replace an existing scene file when True.

        Returns:
            OUTPUT_NODE payload. ``result`` is ``(path, summary)``; ``path`` is
            empty when the write was refused. ``ui.text`` is the status line.
        """
        try:
            doc = build_scene(
                scene_id=scene_id,
                assets=assets,
                camera_pos=camera_pos,
                camera_look=camera_look,
                camera_fov=camera_fov,
                hdri=hdri,
            )
            dest = _resolve_dest(filename)
            bible = _load_asset_bible()
            _write_document(bible, doc, dest, overwrite=overwrite)
            count = len(doc["instances"])
            noun = "instance" if count == 1 else "instances"
            return _result(str(dest), f"wrote {count} {noun} to {dest}")
        except Exception as exc:  # noqa: BLE001 - fail soft for the canvas
            return _result("", f"scene not written ({type(exc).__name__}): {exc}")


# Comfy custom-node registries for the scene-layout writer.
NODE_CLASS_MAPPINGS: NodeRegistry = {
    "EZSceneLayout": EZSceneLayout,
}
"""Comfy class-name registry for the scene-layout writer."""

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {
    "EZSceneLayout": "Compose 3D scene layout",
}
"""Comfy display-name registry for the scene-layout writer."""

__all__ = [
    "CATEGORY",
    "DEFAULT_CAMERA_LOOK",
    "DEFAULT_CAMERA_POS",
    "DEFAULT_FILENAME",
    "DEFAULT_FOV",
    "DEFAULT_HDRI",
    "EZSceneLayout",
    "FOV_MAX",
    "FOV_MIN",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "ROW_SPACING_M",
    "SCENES_SUBDIR",
    "SceneLayoutError",
    "SceneNodeResult",
    "SceneUiText",
    "build_scene",
    "scene_output_dir",
]

#!/usr/bin/env python3
"""Asset Bible contract (ez.asset.v1) — hermetic stdlib, no PyYAML.

Assets are operator outputs under COMFY_OUTPUT_DIR/assets, never MODELS_DIR.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "ez.asset.v1"
INDEX_SCHEMA = "ez.asset-index.v1"

KINDS = frozenset(
    {"object", "character", "building", "set", "scene", "material", "hdri"}
)
PIPELINES = frozenset(
    {
        "klein-trellis2",
        "klein-edit",
        "bpy-primitive",
        "mcp-construct",
        "scene-assemble",
    }
)
KIND_DIRS = {
    "object": "objects",
    "character": "characters",
    "building": "buildings",
    "set": "sets",
    "scene": "scenes",
    "material": "materials",
    "hdri": "hdris",
}

REQUIRED_ASSET_FIELDS = (
    "schema",
    "id",
    "kind",
    "prompt",
    "seed",
    "pipeline",
    "parent",
    "takes",
    "files",
    "tags",
    "license",
    "ready",
)

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_EMBEDDED_KEYS = frozenset(
    {
        "mesh",
        "meshes",
        "glb",
        "gltf",
        "bin",
        "buffer",
        "buffers",
        "bufferviews",
        "accessors",
        "primitives",
        "vertices",
        "positions",
        "base64",
        "bytes",
        "blob",
        "payload",
    }
)
MAX_SCENE_BYTES = 256_000
MAX_STRING_CHARS = 4096
MAX_NUMERIC_ARRAY = 16


class AssetBibleError(ValueError):
    """Fail-closed Asset Bible contract error."""


def kind_dirname(kind: str) -> str:
    """Return the catalog directory name for a kind.

    Args:
        kind: Asset kind enum value.

    Returns:
        Plural directory name (e.g. object → objects).

    Raises:
        AssetBibleError: Unknown kind.
    """
    if kind not in KIND_DIRS:
        raise AssetBibleError(f"unknown kind {kind!r}")
    return KIND_DIRS[kind]


def asset_dir(output_dir: str | Path, kind: str, slug: str) -> Path:
    """Return <output_dir>/<kind-dir>/<slug>.

    Args:
        output_dir: Asset catalog root (COMFY_OUTPUT_DIR/assets).
        kind: Kind enum.
        slug: Asset id / directory name.

    Returns:
        Absolute-or-relative Path for the slug directory.
    """
    return Path(output_dir) / kind_dirname(kind) / slug


def index_path(output_dir: str | Path) -> Path:
    """Return the catalog index.yaml path.

    Args:
        output_dir: Asset catalog root.

    Returns:
        Path to index.yaml.
    """
    return Path(output_dir) / "index.yaml"


def refuse_models_dir(path: str | Path) -> Path:
    """Refuse MODELS_DIR / named models-cache paths.

    Args:
        path: Candidate output or asset path.

    Returns:
        Resolved path when allowed.

    Raises:
        AssetBibleError: Path is under MODELS_DIR or a models cache.
    """
    resolved = Path(path).expanduser().resolve()
    models_raw = os.environ.get("MODELS_DIR", "/mnt/models")
    models = Path(models_raw).expanduser().resolve()
    try:
        resolved.relative_to(models)
    except ValueError:
        pass
    else:
        raise AssetBibleError(
            f"assets must not live under MODELS_DIR ({models}); "
            "use COMFY_OUTPUT_DIR/assets"
        )
    if any(part.lower() == "models" for part in resolved.parts):
        raise AssetBibleError(
            "refusing named models cache path; assets live under "
            "COMFY_OUTPUT_DIR/assets, never MODELS_DIR"
        )
    return resolved


def _strip_comment(line: str) -> str:
    """Drop unquoted # comments."""
    in_single = False
    in_double = False
    escaped = False
    for i, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_double:
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:i]
    return line


def _split_key(content: str) -> tuple[str, str]:
    """Split a mapping line on the first unquoted colon."""
    in_single = False
    in_double = False
    for i, char in enumerate(content):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == ":" and not in_single and not in_double:
            return content[:i].strip(), content[i + 1 :]
    raise AssetBibleError(f"expected key: value, got {content!r}")


def _unescape_double(text: str) -> str:
    """Unescape a double-quoted YAML scalar (minimal)."""
    out: list[str] = []
    escaped = False
    for char in text:
        if escaped:
            mapping = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}
            out.append(mapping.get(char, char))
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        out.append(char)
    return "".join(out)


def _split_flow(inner: str) -> list[str]:
    """Split a flow collection on top-level commas."""
    parts: list[str] = []
    buf: list[str] = []
    depth_sq = 0
    depth_br = 0
    in_single = False
    in_double = False
    escaped = False
    for char in inner:
        if escaped:
            buf.append(char)
            escaped = False
            continue
        if char == "\\" and in_double:
            buf.append(char)
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            buf.append(char)
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            buf.append(char)
            continue
        if in_single or in_double:
            buf.append(char)
            continue
        if char == "[":
            depth_sq += 1
        elif char == "]":
            depth_sq -= 1
        elif char == "{":
            depth_br += 1
        elif char == "}":
            depth_br -= 1
        if char == "," and depth_sq == 0 and depth_br == 0:
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(char)
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _parse_scalar(text: str) -> Any:
    """Parse a restricted YAML scalar / flow collection."""
    text = text.strip()
    if text in {"", "null", "~", "None"}:
        return None
    lowered = text.lower()
    if lowered in {"true", "yes", "on"}:
        return True
    if lowered in {"false", "no", "off"}:
        return False
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        return _unescape_double(text[1:-1])
    if len(text) >= 2 and text[0] == "'" and text[-1] == "'":
        return text[1:-1]
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?\d+\.\d+", text):
        return float(text)
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part) for part in _split_flow(inner)]
    if text.startswith("{") and text.endswith("}"):
        inner = text[1:-1].strip()
        if not inner:
            return {}
        mapping: dict[str, Any] = {}
        for part in _split_flow(inner):
            if ":" in part:
                key, rest = _split_key(part)
                mapping[key] = _parse_scalar(rest.strip()) if rest.strip() else True
            else:
                mapping[part] = True
        return mapping
    return text


def _tokenize(text: str) -> list[tuple[int, str]]:
    """Turn restricted YAML into (indent, content) rows."""
    rows: list[tuple[int, str]] = []
    for raw in text.splitlines():
        stripped_nl = _strip_comment(raw).rstrip()
        if not stripped_nl.strip():
            continue
        if "\t" in stripped_nl:
            raise AssetBibleError("tabs are not allowed in asset YAML")
        indent = len(stripped_nl) - len(stripped_nl.lstrip(" "))
        if indent % 2 != 0:
            raise AssetBibleError("indent must be multiples of 2 spaces")
        rows.append((indent, stripped_nl.strip()))
    return rows


def _parse_mapping(
    lines: list[tuple[int, str]], start: int, min_indent: int
) -> tuple[dict[str, Any], int]:
    """Parse a block mapping starting at min_indent."""
    result: dict[str, Any] = {}
    i = start
    while i < len(lines):
        indent, content = lines[i]
        if indent < min_indent:
            break
        if indent > min_indent:
            raise AssetBibleError(f"unexpected indent at {content!r}")
        if content.startswith("- "):
            raise AssetBibleError(f"unexpected list item in mapping: {content!r}")
        key, rest = _split_key(content)
        rest = rest.strip()
        if rest == "":
            if i + 1 < len(lines) and lines[i + 1][0] > indent:
                nested, i = _parse_value_block(lines, i + 1, indent + 2)
                result[key] = nested
            else:
                result[key] = None
                i += 1
        else:
            result[key] = _parse_scalar(rest)
            i += 1
    return result, i


def _parse_list(
    lines: list[tuple[int, str]], start: int, min_indent: int
) -> tuple[list[Any], int]:
    """Parse a block list starting at min_indent."""
    result: list[Any] = []
    i = start
    while i < len(lines):
        indent, content = lines[i]
        if indent < min_indent:
            break
        if indent != min_indent or not content.startswith("- "):
            raise AssetBibleError(f"expected list item at indent {min_indent}: {content!r}")
        item_text = content[2:].strip()
        if item_text == "":
            if i + 1 < len(lines) and lines[i + 1][0] > indent:
                nested, i = _parse_value_block(lines, i + 1, indent + 2)
                result.append(nested)
            else:
                result.append(None)
                i += 1
            continue
        if (
            ":" in item_text
            and not item_text.startswith(("{", "[", '"', "'"))
            and not (item_text.startswith("'") or item_text[0] == '"')
        ):
            first_key, rest = _split_key(item_text)
            mapping: dict[str, Any] = {}
            rest = rest.strip()
            mapping[first_key] = _parse_scalar(rest) if rest else None
            i += 1
            if i < len(lines) and lines[i][0] > indent:
                extra, i = _parse_mapping(lines, i, indent + 2)
                mapping.update(extra)
            result.append(mapping)
            continue
        result.append(_parse_scalar(item_text))
        i += 1
    return result, i


def _parse_value_block(
    lines: list[tuple[int, str]], start: int, min_indent: int
) -> tuple[Any, int]:
    """Parse a nested mapping or list at or above min_indent."""
    if start >= len(lines):
        return None, start
    indent, content = lines[start]
    if indent < min_indent:
        return None, start
    if content.startswith("- "):
        return _parse_list(lines, start, indent)
    return _parse_mapping(lines, start, indent)


def parse_restricted_yaml(text: str) -> Any:
    """Parse the Asset Bible YAML subset (indent-2, flow collections, comments).

    Args:
        text: YAML document text.

    Returns:
        Mapping, list, or scalar.

    Raises:
        AssetBibleError: On syntax the subset does not accept.
    """
    lines = _tokenize(text)
    if not lines:
        raise AssetBibleError("empty YAML document")
    value, idx = _parse_value_block(lines, 0, 0)
    if idx != len(lines):
        raise AssetBibleError(f"unparsed YAML starting at {lines[idx][1]!r}")
    return value


def _require_slug(value: Any, field: str) -> str:
    """Require a slug string."""
    if not isinstance(value, str) or not _SLUG_RE.fullmatch(value):
        raise AssetBibleError(f"{field} must be a lowercase slug, got {value!r}")
    return value


def _as_str_list(value: Any, field: str) -> list[str]:
    """Require a list of strings."""
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise AssetBibleError(f"{field} must be a list of strings")
    return list(value)


def _normalize_files(value: Any) -> dict[str, Any]:
    """Accept a file-role mapping or list of role names."""
    if isinstance(value, list):
        if not value or not all(isinstance(item, str) and item for item in value):
            raise AssetBibleError("files list must be non-empty role names")
        return {item: True for item in value}
    if isinstance(value, dict):
        if not value:
            raise AssetBibleError("files mapping must not be empty")
        out: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise AssetBibleError("files keys must be non-empty strings")
            out[key] = item
        return out
    raise AssetBibleError("files must be a mapping or list of roles")


def validate_asset(data: Any) -> dict[str, Any]:
    """Validate an ez.asset.v1 mapping (fail closed).

    Args:
        data: Parsed YAML object.

    Returns:
        Normalized asset dict.

    Raises:
        AssetBibleError: Missing/invalid fields.
    """
    if not isinstance(data, dict):
        raise AssetBibleError("asset.yaml must be a mapping")
    missing = [field for field in REQUIRED_ASSET_FIELDS if field not in data]
    if missing:
        raise AssetBibleError(f"missing required fields: {', '.join(missing)}")
    if data["schema"] != SCHEMA:
        raise AssetBibleError(f"schema must be {SCHEMA}, got {data['schema']!r}")
    asset_id = _require_slug(data["id"], "id")
    kind = data["kind"]
    if kind not in KINDS:
        raise AssetBibleError(f"kind must be one of {sorted(KINDS)}, got {kind!r}")
    prompt = data["prompt"]
    if not isinstance(prompt, str) or not prompt.strip():
        raise AssetBibleError("prompt must be a non-empty string")
    seed = data["seed"]
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise AssetBibleError("seed must be a non-negative integer")
    pipeline = data["pipeline"]
    if pipeline not in PIPELINES:
        raise AssetBibleError(
            f"pipeline must be one of {sorted(PIPELINES)}, got {pipeline!r}"
        )
    parent = data["parent"]
    if parent is not None:
        parent = _require_slug(parent, "parent")
    takes = _as_str_list(data["takes"], "takes")
    files = _normalize_files(data["files"])
    tags = _as_str_list(data["tags"], "tags")
    license_id = data["license"]
    if not isinstance(license_id, str) or not license_id.strip():
        raise AssetBibleError("license must be a non-empty string")
    ready = data["ready"]
    if not isinstance(ready, bool):
        raise AssetBibleError("ready must be a boolean")
    return {
        "schema": SCHEMA,
        "id": asset_id,
        "kind": kind,
        "prompt": prompt,
        "seed": seed,
        "pipeline": pipeline,
        "parent": parent,
        "takes": takes,
        "files": files,
        "tags": tags,
        "license": license_id,
        "ready": ready,
    }


def load_asset(path: str | Path) -> dict[str, Any]:
    """Parse and validate an asset.yaml file.

    Args:
        path: Path to YAML.

    Returns:
        Normalized asset dict.

    Raises:
        AssetBibleError: Parse/validate failure.
        OSError: Unreadable file.
    """
    text = Path(path).read_text(encoding="utf-8")
    parsed = parse_restricted_yaml(text)
    return validate_asset(parsed)


def _refuse_embedded(value: Any, loc: str) -> None:
    """Walk a scene document and refuse mesh bytes / giant base64."""
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in _EMBEDDED_KEYS:
                raise AssetBibleError(
                    f"scene must instance slugs, not embed {key!r} at {loc}"
                )
            _refuse_embedded(item, f"{loc}.{key}")
        return
    if isinstance(value, list):
        if len(value) > MAX_NUMERIC_ARRAY and all(
            isinstance(item, (int, float)) and not isinstance(item, bool)
            for item in value
        ):
            raise AssetBibleError(
                f"refusing packed numeric array at {loc}; instance slugs only"
            )
        for idx, item in enumerate(value):
            _refuse_embedded(item, f"{loc}[{idx}]")
        return
    if isinstance(value, str):
        lowered = value.lower()
        if value.startswith("data:") and "base64" in lowered:
            raise AssetBibleError(f"refusing data: URI base64 mesh bytes at {loc}")
        if "base64" in lowered and len(value) > 128:
            raise AssetBibleError(f"refusing embedded base64 at {loc}")
        if len(value) > MAX_STRING_CHARS:
            raise AssetBibleError(
                f"string too long at {loc} (meshes do not belong in scene.json)"
            )


def validate_scene(data: Any) -> dict[str, Any]:
    """Validate a scene.json that instances slugs (no embedded meshes).

    Args:
        data: Parsed JSON object.

    Returns:
        The same mapping after checks.

    Raises:
        AssetBibleError: Contract violation.
    """
    if not isinstance(data, dict):
        raise AssetBibleError("scene.json must be an object")
    scene_id = data.get("id")
    if not isinstance(scene_id, str) or not scene_id.strip():
        raise AssetBibleError("scene id is required")
    instances = data.get("instances")
    if not isinstance(instances, list) or not instances:
        raise AssetBibleError("scene instances must be a non-empty list")
    for idx, inst in enumerate(instances):
        if not isinstance(inst, dict):
            raise AssetBibleError(f"instances[{idx}] must be an object")
        ref = inst.get("ref")
        if not isinstance(ref, str) or not ref.strip():
            raise AssetBibleError(f"instances[{idx}].ref is required")
    _refuse_embedded(data, "$")
    return data


def load_scene(path: str | Path) -> dict[str, Any]:
    """Load and validate scene.json.

    Args:
        path: JSON path.

    Returns:
        Scene mapping.

    Raises:
        AssetBibleError: Size, JSON, or contract failure.
    """
    scene_path = Path(path)
    size = scene_path.stat().st_size
    if size > MAX_SCENE_BYTES:
        raise AssetBibleError(
            f"scene.json is {size} bytes; refuse embedded meshes "
            f"(limit {MAX_SCENE_BYTES})"
        )
    try:
        data = json.loads(scene_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssetBibleError(f"invalid scene JSON: {exc}") from exc
    return validate_scene(data)


def validate_file(path: str | Path) -> dict[str, Any]:
    """Validate an asset.yaml or scene.json by suffix.

    Args:
        path: File path.

    Returns:
        Normalized asset or scene dict.

    Raises:
        AssetBibleError: Unsupported type or contract failure.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise AssetBibleError(f"not a file: {file_path}")
    suffix = file_path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return load_asset(file_path)
    if suffix == ".json":
        return load_scene(file_path)
    raise AssetBibleError(f"unsupported file type {suffix} (want .yaml or .json)")


def iter_asset_yaml(output_dir: str | Path) -> list[Path]:
    """List asset.yaml files as <output_dir>/<kind>/<slug>/asset.yaml.

    Args:
        output_dir: Catalog root.

    Returns:
        Sorted paths.
    """
    root = Path(output_dir)
    if not root.is_dir():
        return []
    found: list[Path] = []
    for kind_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        if kind_dir.name.startswith("."):
            continue
        for slug_dir in sorted(p for p in kind_dir.iterdir() if p.is_dir()):
            yaml_path = slug_dir / "asset.yaml"
            if yaml_path.is_file():
                found.append(yaml_path)
    return found


def list_assets(output_dir: str | Path) -> list[dict[str, Any]]:
    """Load every asset.yaml under the catalog (fail closed on defects).

    Args:
        output_dir: Catalog root (…/assets).

    Returns:
        List of normalized asset dicts with path/slug.

    Raises:
        AssetBibleError: Invalid record or MODELS_DIR target.
    """
    root = Path(output_dir)
    refuse_models_dir(root)
    records: list[dict[str, Any]] = []
    for yaml_path in iter_asset_yaml(root):
        asset = load_asset(yaml_path)
        slug = yaml_path.parent.name
        if slug != asset["id"]:
            raise AssetBibleError(
                f"{yaml_path}: directory slug {slug!r} != id {asset['id']!r}"
            )
        rel = yaml_path.parent.relative_to(root).as_posix()
        rec = dict(asset)
        rec["slug"] = slug
        rec["path"] = rel
        records.append(rec)
    records.sort(key=lambda item: item["id"])
    return records


def _format_scalar(value: Any) -> str:
    """Format a YAML scalar for index.yaml."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = str(value)
    if _SLUG_RE.fullmatch(text) or re.fullmatch(r"[A-Za-z0-9_./:-]+", text):
        return text
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def write_index(output_dir: str | Path) -> Path:
    """Scan the catalog and write index.yaml.

    Args:
        output_dir: Catalog root.

    Returns:
        Path to the written index.

    Raises:
        AssetBibleError: MODELS_DIR or invalid assets.
    """
    root = Path(output_dir)
    refuse_models_dir(root)
    root.mkdir(parents=True, exist_ok=True)
    records = list_assets(root)
    lines = [f"schema: {INDEX_SCHEMA}"]
    if not records:
        lines.append("assets: []")
    else:
        lines.append("assets:")
    for rec in records:
        lines.append(f"  - id: {rec['id']}")
        lines.append(f"    kind: {rec['kind']}")
        lines.append(f"    slug: {rec['slug']}")
        lines.append(f"    path: {rec['path']}")
        lines.append(f"    pipeline: {rec['pipeline']}")
        lines.append(f"    ready: {_format_scalar(rec['ready'])}")
        tags = rec.get("tags") or []
        tag_flow = ", ".join(_format_scalar(tag) for tag in tags)
        lines.append(f"    tags: [{tag_flow}]")
    dest = index_path(root)
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest


def ensure_layout(output_dir: str | Path, kind: str, slug: str) -> Path:
    """Create mesh/, views/, variants/, and prompts.jsonl for a slug.

    Does not write asset.yaml (that is P-A1 asset-new).

    Args:
        output_dir: Catalog root.
        kind: Kind enum.
        slug: Asset id.

    Returns:
        Slug directory path.

    Raises:
        AssetBibleError: MODELS_DIR, unknown kind, or bad slug.
    """
    _require_slug(slug, "slug")
    dest = asset_dir(output_dir, kind, slug)
    refuse_models_dir(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("mesh", "views", "variants"):
        (dest / name).mkdir(exist_ok=True)
    prompts = dest / "prompts.jsonl"
    if not prompts.exists():
        prompts.write_text("", encoding="utf-8")
    return dest


def _print_human(records: list[dict[str, Any]], output_dir: Path) -> None:
    """Print a status-like catalog listing."""
    if not records:
        print(f"Asset Bible: 0 assets in {output_dir}")
        print("Catalog is empty. Expected <dir>/<kind>/<slug>/asset.yaml")
        print("Assets are outputs under COMFY_OUTPUT_DIR/assets, never MODELS_DIR.")
        print(
            "Operator verb today: asset-ls. "
            "Coming later: asset-new / asset-iterate / asset-promote."
        )
        return
    print(f"Asset Bible: {len(records)} asset(s) in {output_dir}")
    for rec in records:
        tags = ",".join(rec.get("tags") or [])
        ready = "ready" if rec.get("ready") else "draft"
        print(
            f"{rec['id']}\tkind={rec['kind']}\tpipeline={rec['pipeline']}\t"
            f"{ready}\ttags={tags}"
        )


def _json_ready(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop non-JSON-friendly values (already primitives)."""
    out: list[dict[str, Any]] = []
    for rec in records:
        item = dict(rec)
        files = item.get("files")
        if isinstance(files, dict):
            item["files"] = {
                key: (True if value is True else value) for key, value in files.items()
            }
        out.append(item)
    return out


def _cli(argv: list[str] | None = None) -> int:
    """CLI: validate FILE | ls --output-dir DIR [--json]."""
    parser = argparse.ArgumentParser(prog="asset_bible")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_val = sub.add_parser("validate", help="validate asset.yaml or scene.json")
    p_val.add_argument("file")
    p_ls = sub.add_parser("ls", help="list catalog (read-only)")
    p_ls.add_argument("--output-dir", required=True)
    p_ls.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "validate":
            result = validate_file(args.file)
            ident = result.get("id", "?")
            print(f"OK {ident}")
            return 0
        if args.cmd == "ls":
            output_dir = Path(args.output_dir)
            records = list_assets(output_dir)
            if args.json:
                print(json.dumps(_json_ready(records)))
            else:
                _print_human(records, output_dir)
            return 0
    except AssetBibleError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(_cli())

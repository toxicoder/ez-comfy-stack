"""Parse workflows/shorts/*.shots.yaml without PyYAML."""

from __future__ import annotations

import re
from typing import Any

FILM_SLUGS = {
    "go-see": "gosee",
    "still-here": "stillhere",
    "switchyard": "switchyard",
}
FILM_CHOICES = tuple(FILM_SLUGS)
SHOT_COUNT = 18
DEFAULT_CAP_SECONDS = 90.0
META_KEYS = (
    "film",
    "slug",
    "frames",
    "fps",
    "duration_s",
    "beats",
    "shots_per_beat",
    "total_shots",
    "publish_cap_s",
    "print",
    "identity_seed",
    "identity_enhance",
)
PRINT_MODES = ("ltx", "dfr", "ltx-iclora-depth", "wan-flf", "dcc-final")
IDENTITY_SEED = "42"
LTX_PRINT_TEMPLATE = "ltx-i2v-5s-lab-example.json"
DFR_TEMPLATE = "templates/ltx-2.5/t2v-i2v-two-stage-distilled"
ICLORA_TEMPLATE = "ltx-iclora-depth-5s-lab-example.json"
WAN_FLF_TEMPLATE = "wan-flf-5s-lab-example.json"
DCC_FINAL_TEMPLATE = "dcc-final"
AUDIO_POLICIES = ("world-only", "stems", "a2v-lock")
SCORE_MODES = ("none", "acestep-instrumental")
CLAY_MODES = ("skip", "required")
AUDIO_LOCKS = ("none", "a2v")
DEFAULT_AUDIO_POLICY = "world-only"
DEFAULT_SCORE = "none"
DEFAULT_CLAY = "skip"
DEFAULT_AUDIO_LOCK = "none"
OPTIONAL_META_KEYS = ("audio_policy", "score")
OPTIONAL_SHOT_KEYS = (
    "script",
    "dialogue",
    "audio_world",
    "camera",
    "clay",
    "look",
    "print_mode",
    "audio_lock",
    "end_state",
)


def print_template(mode: str) -> str:
    """Map YAML ``print:`` to a lab graph or official Templates path.

    ``dfr`` is not a vendored JSON blob (UUID subgraphs). The stub records
    the Templates SoT path from ``workflows/quality/ltx-2.5/NOTICE.md``.
    ``dcc-final`` is Path A (engine beauty) and is not a lab printer yet.
    """
    if mode == "dfr":
        return DFR_TEMPLATE
    if mode == "ltx":
        return LTX_PRINT_TEMPLATE
    if mode == "ltx-iclora-depth":
        return ICLORA_TEMPLATE
    if mode == "wan-flf":
        return WAN_FLF_TEMPLATE
    if mode == "dcc-final":
        return DCC_FINAL_TEMPLATE
    raise ValueError(
        "print must be ltx|dfr|ltx-iclora-depth|wan-flf|dcc-final, got "
        f"{mode!r}"
    )


def film_slug(film: str) -> str:
    """Map film id to output prefix slug.

    Arguments:
        film: go-see, still-here, or switchyard.
    Returns:
        Slug string (gosee, stillhere, switchyard).
    Raises:
        ValueError: unknown film id.
    """
    slug = FILM_SLUGS.get(film)
    if slug is None:
        raise ValueError(f"unknown film: {film} (go-see|still-here|switchyard)")
    return slug


def _block_field(body: str, name: str) -> str:
    match = re.search(rf"^[ \t]*{name}:[ \t]*\|[ \t]*\n", body, re.M)
    if not match:
        raise ValueError(f"missing block {name}")
    lines: list[str] = []
    for line in body[match.end() :].splitlines():
        if re.match(r"^    \S", line):
            break
        if not line.strip():
            break
        if re.match(r"^      \S", line) or re.match(r"^        \S", line):
            lines.append(line.strip())
        else:
            break
    if not lines:
        raise ValueError(f"empty block {name}")
    return " ".join(lines)


def _unquote(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1]
    return text


def _scalar(body: str, name: str) -> str:
    match = re.search(rf"^\s*{name}:\s*(.+)$", body, re.M)
    if not match:
        raise ValueError(f"missing {name}")
    return _unquote(match.group(1))


def _optional_scalar(body: str, name: str, default: str = "") -> str:
    match = re.search(rf"^\s*{name}:\s*(.*)$", body, re.M)
    if not match:
        return default
    return _unquote(match.group(1))


def _optional_meta(text: str, name: str, default: str) -> str:
    match = re.search(rf"^{name}:\s*(.*)$", text, re.M)
    if not match:
        return default
    return _unquote(match.group(1))


def _norm_token(token: str) -> str:
    return " ".join(str(token).strip().lower().split())


def _validate_choice(name: str, value: str, allowed: tuple[str, ...]) -> str:
    key = _norm_token(value)
    for item in allowed:
        if key == item:
            return item
    raise ValueError(f"{name} must be {'|'.join(allowed)}, got {value!r}")


def normalize_camera(token: str) -> str:
    """Return a canonical camera verb, or empty when unset.

    ``fixed`` is accepted as ``fixed camera`` (enum in prompt_enums).
    """
    if not token.strip():
        return ""
    key = _norm_token(token)
    if key == "fixed":
        key = "fixed camera"
    from .prompt_enums import CAMERAS

    for item in CAMERAS:
        if key == item:
            return item
    raise ValueError(f"unknown camera {token!r}; allowed: {', '.join(CAMERAS)}")


def apply_shot_card_defaults(parsed: dict[str, Any]) -> dict[str, Any]:
    """Fill fail-closed defaults for optional shot-card keys (mutates parsed)."""
    meta = parsed["meta"]
    meta["audio_policy"] = _validate_choice(
        "audio_policy",
        str(meta.get("audio_policy") or DEFAULT_AUDIO_POLICY),
        AUDIO_POLICIES,
    )
    meta["score"] = _validate_choice(
        "score", str(meta.get("score") or DEFAULT_SCORE), SCORE_MODES
    )
    for shot in parsed["shots"]:
        shot["script"] = str(shot.get("script") or "")
        shot["dialogue"] = str(shot.get("dialogue") or "")
        shot["audio_world"] = str(shot.get("audio_world") or "")
        shot["end_state"] = str(shot.get("end_state") or "")
        shot["look"] = str(shot.get("look") or "")
        shot["print_mode"] = str(shot.get("print_mode") or "")
        shot["camera"] = normalize_camera(str(shot.get("camera") or ""))
        shot["clay"] = _validate_choice(
            "clay", str(shot.get("clay") or DEFAULT_CLAY), CLAY_MODES
        )
        shot["audio_lock"] = _validate_choice(
            "audio_lock",
            str(shot.get("audio_lock") or DEFAULT_AUDIO_LOCK),
            AUDIO_LOCKS,
        )
        if shot["print_mode"] and shot["print_mode"] not in PRINT_MODES:
            raise ValueError(
                f"print_mode must be {'|'.join(PRINT_MODES)}, got "
                f"{shot['print_mode']!r}"
            )
    return parsed


def parse_shots_yaml(text: str) -> dict[str, Any]:
    """Parse a film bible YAML subset.

    Arguments:
        text: File contents of ``{film}.shots.yaml``.
    Returns:
        Dict with ``meta``, ``identity``, and ``shots`` (18 dicts).
    Raises:
        ValueError: missing required keys or empty prompt blocks.
    """
    meta: dict[str, str] = {}
    for key in META_KEYS:
        match = re.search(rf"^{key}:\s*(.+)$", text, re.M)
        if not match:
            raise ValueError(f"missing meta {key}")
        meta[key] = match.group(1).strip()
    if meta["print"] not in PRINT_MODES:
        raise ValueError(
            "print must be ltx|dfr|ltx-iclora-depth|wan-flf|dcc-final, got "
            f"{meta['print']!r}"
        )
    if meta["identity_seed"] != IDENTITY_SEED:
        raise ValueError("identity_seed must be frozen 42")
    enh = meta["identity_enhance"].lower()
    if enh not in ("true", "false", "1", "0", "on", "off", "yes", "no"):
        raise ValueError("identity_enhance must be true or false")
    meta["audio_policy"] = _optional_meta(
        text, "audio_policy", DEFAULT_AUDIO_POLICY
    )
    meta["score"] = _optional_meta(text, "score", DEFAULT_SCORE)

    ident_m = re.search(r"^identity_look:\s*\|\s*\n((?:  .*\n)+)", text, re.M)
    if not ident_m:
        raise ValueError("missing identity_look")
    identity = " ".join(
        line.strip() for line in ident_m.group(1).splitlines() if line.strip()
    )

    shots: list[dict[str, str]] = []
    blocks = re.split(r"\n  - beat:", text)[1:]
    for block in blocks:
        body = "beat:" + block
        shot = {
            "beat": _scalar(body, "beat"),
            "shot": _scalar(body, "shot"),
            "prefix": _scalar(body, "prefix"),
            "load_from": _scalar(body, "load_from"),
            "ltx_i2v": _block_field(body, "ltx_i2v"),
            "wan_i2v": _block_field(body, "wan_i2v"),
            "script": _optional_scalar(body, "script"),
            "dialogue": _optional_scalar(body, "dialogue"),
            "audio_world": _optional_scalar(body, "audio_world"),
            "end_state": _optional_scalar(body, "end_state"),
            "camera": _optional_scalar(body, "camera"),
            "clay": _optional_scalar(body, "clay", DEFAULT_CLAY),
            "look": _optional_scalar(body, "look"),
            "print_mode": _optional_scalar(body, "print_mode"),
            "audio_lock": _optional_scalar(body, "audio_lock", DEFAULT_AUDIO_LOCK),
        }
        shots.append(shot)
    parsed = {"meta": meta, "identity": identity, "shots": shots}
    return apply_shot_card_defaults(parsed)


def _yaml_quote(value: str) -> str:
    if value == "":
        return '""'
    if any(ch in value for ch in (":", "#", "{", "}", "[", "]", ",", "&", "*")):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def _emit_block(name: str, text: str, indent: str) -> str:
    lines = [f"{indent}{name}: |"]
    words = text.split()
    if not words:
        lines.append(f"{indent}  (empty)")
        return "\n".join(lines)
    row: list[str] = []
    for word in words:
        trial = " ".join(row + [word])
        if row and len(trial) > 88:
            lines.append(f"{indent}  {' '.join(row)}")
            row = [word]
        else:
            row.append(word)
    if row:
        lines.append(f"{indent}  {' '.join(row)}")
    return "\n".join(lines)


def write_shots_yaml(parsed: dict[str, Any]) -> str:
    """Serialize a parsed film bible including shot-card defaults."""
    apply_shot_card_defaults(parsed)
    meta = parsed["meta"]
    lines = [
        f"film: {meta['film']}",
        f"slug: {meta['slug']}",
        f"frames: {meta['frames']}",
        f"fps: {meta['fps']}",
        f"duration_s: {meta['duration_s']}",
        f"beats: {meta['beats']}",
        f"shots_per_beat: {meta['shots_per_beat']}",
        f"total_shots: {meta['total_shots']}",
        f"publish_cap_s: {meta['publish_cap_s']}",
        f"print: {meta['print']}",
        f"audio_policy: {meta['audio_policy']}",
        f"score: {meta['score']}",
        f"identity_seed: {meta['identity_seed']}",
        f"identity_enhance: {meta['identity_enhance']}",
        _emit_block("identity_look", parsed["identity"], ""),
        "shots:",
    ]
    for shot in parsed["shots"]:
        lines.append(f"  - beat: {shot['beat']}")
        lines.append(f"    shot: {shot['shot']}")
        lines.append(f"    prefix: {shot['prefix']}")
        lines.append(f"    load_from: {shot['load_from']}")
        lines.append(f"    clay: {shot['clay']}")
        lines.append(f"    audio_lock: {shot['audio_lock']}")
        if shot.get("print_mode"):
            lines.append(f"    print_mode: {shot['print_mode']}")
        if shot.get("camera"):
            lines.append(f"    camera: {shot['camera']}")
        if shot.get("look"):
            lines.append(f"    look: {_yaml_quote(shot['look'])}")
        lines.append(f"    script: {_yaml_quote(shot.get('script') or '')}")
        lines.append(f"    dialogue: {_yaml_quote(shot.get('dialogue') or '')}")
        if shot.get("audio_world"):
            lines.append(f"    audio_world: {_yaml_quote(shot['audio_world'])}")
        if shot.get("end_state"):
            lines.append(f"    end_state: {_yaml_quote(shot['end_state'])}")
        lines.append(_emit_block("ltx_i2v", shot["ltx_i2v"], "    "))
        lines.append(_emit_block("wan_i2v", shot["wan_i2v"], "    "))
    return "\n".join(lines) + "\n"


def scaffold_shot_sheet(src_text: str) -> str:
    """Parse a lab bible and emit a shot-card YAML with defaults filled."""
    return write_shots_yaml(parse_shots_yaml(src_text))

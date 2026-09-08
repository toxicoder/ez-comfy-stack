"""Interactive command builder: JSON recipes, ezcmd fences, copy-text spec.

Hermetic pytest uses this module as the substitution spec. ``commands.js``
must match ``substitute_vars`` / ``render_command``. Stdlib only (no PyYAML).
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Mapping

DEFAULT_BUILDER_PATH = (
    Path(__file__).resolve().parents[1] / "includes" / "command-builder.json"
)

SESSION_VAR_IDS = (
    "SPARK_HOST",
    "SPARK_USER",
    "MODELS_DIR",
    "COMFY_OUTPUT_DIR",
    "COMFY_PORT",
    "DOWNLOAD_LIMIT",
)

FLAG_KINDS = frozenset({"bool", "choice", "choice-or-int"})
_ID_RE = re.compile(r"^[a-z0-9-]+$")
_VAR_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_VAR_TOKEN_RE = re.compile(r"\$\{([A-Z][A-Z0-9_]*)\}")
_EZCMD_FENCE_RE = re.compile(
    r"^```ezcmd[^\n]*\n(.*?)(?:\n)?^```[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
_CMD_ID_LINE_RE = re.compile(r"^id:\s*([a-z0-9-]+)\s*$", re.MULTILINE)
_UNSAFE_SHELL_RE = re.compile(r"[^\w./:=@+-]")

_BUILDER_CACHE: dict[str, dict[str, Any]] = {}


def load_builder(path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate ``includes/command-builder.json``.

    Args:
        path: Override path. Default is the shipped recipes file.

    Returns:
        Mapping with ``variables`` (list) and ``commands`` (list).

    Raises:
        ValueError: Schema errors.
        OSError: Unreadable file.
    """
    resolved = Path(path) if path is not None else DEFAULT_BUILDER_PATH
    cache_key = str(resolved)
    cached = _BUILDER_CACHE.get(cache_key)
    if cached is not None:
        return cached
    raw = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("command-builder JSON must be an object")
    validate_builder(raw)
    _BUILDER_CACHE[cache_key] = raw
    return raw


def validate_builder(data: Mapping[str, Any]) -> None:
    """Raise ValueError when the recipe file is not operator-safe.

    Args:
        data: Parsed JSON object.

    Raises:
        ValueError: Duplicate ids, missing session vars, bad flag kinds.
    """
    variables = data.get("variables")
    commands = data.get("commands")
    if not isinstance(variables, list) or not variables:
        raise ValueError("command-builder.variables must be a non-empty list")
    if not isinstance(commands, list) or not commands:
        raise ValueError("command-builder.commands must be a non-empty list")

    var_ids: list[str] = []
    for i, row in enumerate(variables):
        if not isinstance(row, dict):
            raise ValueError(f"variables[{i}] must be an object")
        vid = row.get("id")
        if not isinstance(vid, str) or not _VAR_ID_RE.fullmatch(vid):
            raise ValueError(f"variables[{i}].id is not an env-style name")
        if vid in var_ids:
            raise ValueError(f"duplicate variable id {vid!r}")
        if not isinstance(row.get("label"), str) or not row["label"].strip():
            raise ValueError(f"variables[{i}].label is required")
        if not isinstance(row.get("default"), str):
            raise ValueError(f"variables[{i}].default must be a string")
        var_ids.append(vid)
    missing = [name for name in SESSION_VAR_IDS if name not in var_ids]
    extra = [name for name in var_ids if name not in SESSION_VAR_IDS]
    if missing:
        raise ValueError(f"command-builder missing session variables: {missing}")
    if extra:
        raise ValueError(f"command-builder unknown session variables: {extra}")

    cmd_ids: list[str] = []
    for i, cmd in enumerate(commands):
        if not isinstance(cmd, dict):
            raise ValueError(f"commands[{i}] must be an object")
        cid = cmd.get("id")
        if not isinstance(cid, str) or not _ID_RE.fullmatch(cid):
            raise ValueError(f"commands[{i}].id must match [a-z0-9-]+")
        if cid in cmd_ids:
            raise ValueError(f"duplicate command id {cid!r}")
        cmd_ids.append(cid)
        argv = cmd.get("argv")
        if not isinstance(argv, list) or not argv or not all(
            isinstance(p, str) and p for p in argv
        ):
            raise ValueError(f"commands[{i}].argv must be a non-empty string list")
        flags = cmd.get("flags") or []
        if not isinstance(flags, list):
            raise ValueError(f"commands[{i}].flags must be a list")
        flag_names: list[str] = []
        for j, flag in enumerate(flags):
            _validate_flag(cid, j, flag, flag_names)


def _validate_flag(
    cmd_id: str, index: int, flag: Any, seen: list[str]
) -> None:
    """Validate one flag recipe.

    Args:
        cmd_id: Parent command id (for error text).
        index: Flag index.
        flag: Flag mapping.
        seen: Names already used on this command (mutated).

    Raises:
        ValueError: Invalid flag schema.
    """
    loc = f"{cmd_id}.flags[{index}]"
    if not isinstance(flag, dict):
        raise ValueError(f"{loc} must be an object")
    name = flag.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9-]+", name):
        raise ValueError(f"{loc}.name must match [a-z0-9-]+")
    if name in seen:
        raise ValueError(f"duplicate flag {name!r} on {cmd_id}")
    seen.append(name)
    kind = flag.get("kind")
    if kind not in FLAG_KINDS:
        raise ValueError(f"{loc}.kind must be one of {sorted(FLAG_KINDS)}")
    if kind == "bool":
        default = flag.get("default", False)
        if not isinstance(default, bool):
            raise ValueError(f"{loc}.default must be a bool")
        return
    choices = flag.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError(f"{loc}.choices must be a non-empty list")
    values: list[str] = []
    for k, choice in enumerate(choices):
        if not isinstance(choice, dict):
            raise ValueError(f"{loc}.choices[{k}] must be an object")
        value = choice.get("value")
        label = choice.get("label")
        if not isinstance(value, str) or value == "":
            raise ValueError(f"{loc}.choices[{k}].value is required")
        if value in values:
            raise ValueError(f"{loc} duplicate choice {value!r}")
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"{loc}.choices[{k}].label is required")
        values.append(value)
    default = flag.get("default")
    if not isinstance(default, str) or default not in values:
        raise ValueError(f"{loc}.default must be one of the choice values")
    bind_var = flag.get("bind_var")
    if bind_var is not None and bind_var not in SESSION_VAR_IDS:
        raise ValueError(f"{loc}.bind_var is not a session variable")


def default_var_values(builder: Mapping[str, Any] | None = None) -> dict[str, str]:
    """Return id → default string for every session variable.

    Args:
        builder: Optional preloaded builder. Default loads the shipped file.

    Returns:
        Copy of default values.
    """
    data = builder if builder is not None else load_builder()
    return {row["id"]: str(row["default"]) for row in data["variables"]}


def command_by_id(
    cmd_id: str, builder: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Return one command recipe.

    Args:
        cmd_id: Recipe id.
        builder: Optional preloaded builder.

    Returns:
        Command mapping.

    Raises:
        KeyError: Unknown id.
    """
    data = builder if builder is not None else load_builder()
    for cmd in data["commands"]:
        if cmd["id"] == cmd_id:
            return cmd
    raise KeyError(cmd_id)


def substitute_vars(template: str, values: Mapping[str, str]) -> str:
    """Replace ``${NAME}`` tokens when NAME is in values. Unknown tokens stay.

    Not recursive: a value that contains ``${OTHER}`` is copied literally so
    stored Spark IPs cannot rewrite the template.

    Args:
        template: Source command or fence text.
        values: Variable id → replacement.

    Returns:
        Substituted string.
    """

    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in values:
            return values[name]
        return match.group(0)

    return _VAR_TOKEN_RE.sub(repl, template)


def template_has_vars(template: str, var_ids: tuple[str, ...] | None = None) -> bool:
    """True when template contains at least one known ``${VAR}``.

    Args:
        template: Fence text.
        var_ids: Variable ids. Default is the session set.

    Returns:
        Whether auto-bind should attach.
    """
    names = set(var_ids if var_ids is not None else SESSION_VAR_IDS)
    return any(name in names for name in _VAR_TOKEN_RE.findall(template))


def _shell_quote(token: str) -> str:
    """Quote a argv token for a single shell line.

    Args:
        token: Raw argument.

    Returns:
        Token, possibly single-quoted.
    """
    if token == "":
        return "''"
    if _UNSAFE_SHELL_RE.search(token):
        return "'" + token.replace("'", "'\\''") + "'"
    return token


def _flag_value(
    flag: Mapping[str, Any],
    flags: Mapping[str, Any],
    values: Mapping[str, str],
) -> Any:
    """Resolve the stored flag value, applying bind_var then default.

    Args:
        flag: Flag recipe.
        flags: Operator-selected flag state (may omit keys).
        values: Session variables.

    Returns:
        Resolved value (bool, str, or None).
    """
    name = flag["name"]
    if name in flags:
        return flags[name]
    bind_var = flag.get("bind_var")
    if isinstance(bind_var, str) and bind_var in values:
        return values[bind_var]
    return flag.get("default")


def render_command(
    recipe: Mapping[str, Any],
    flags: Mapping[str, Any] | None = None,
    values: Mapping[str, str] | None = None,
) -> str:
    """Build the copyable shell line for a recipe.

    Unchecked optional bools and optional empty choices are omitted.
    ``choice-or-int`` emits ``--limit 80`` or ``--limit auto``.

    Args:
        recipe: Command object from the builder JSON.
        flags: Selected flag values keyed by flag name.
        values: Session variables for ``${VAR}`` substitution.

    Returns:
        A single shell line.
    """
    selected = dict(flags or {})
    vars_map = dict(values or {})
    parts = [substitute_vars(str(p), vars_map) for p in recipe["argv"]]
    for flag in recipe.get("flags") or []:
        name = flag["name"]
        kind = flag["kind"]
        required = bool(flag.get("required"))
        current = _flag_value(flag, selected, vars_map)
        if kind == "bool":
            if current is True:
                parts.append(f"--{name}")
            continue
        if current is None or current is False or current == "":
            if required:
                current = flag.get("default")
            else:
                continue
        token = str(current)
        if not token:
            continue
        parts.append(f"--{name}")
        parts.append(token)
    return " ".join(_shell_quote(p) for p in parts)


def _builder_widget_html(cmd_id: str, builder: Mapping[str, Any]) -> str:
    """HTML placeholder JS hydrates; noscript shows the default command.

    Args:
        cmd_id: Recipe id.
        builder: Validated builder.

    Returns:
        HTML block (not markdown).
    """
    recipe = command_by_id(cmd_id, builder)
    default_line = render_command(recipe, {}, default_var_values(builder))
    safe_id = html.escape(cmd_id, quote=True)
    safe_line = html.escape(default_line)
    return (
        f'<div class="ez-cmd-builder" data-ez-cmd="{safe_id}">\n'
        f'<noscript><pre><code>{safe_line}</code></pre></noscript>\n'
        f"</div>\n"
    )


def expand_ezcmd(
    markdown: str, builder: Mapping[str, Any] | None = None
) -> str:
    """Replace `` ```ezcmd `` fences with builder widgets.

    Args:
        markdown: Page source.
        builder: Optional preloaded builder.

    Returns:
        Markdown with fences expanded.

    Raises:
        ValueError: Fence without ``id:`` or unknown command id.
    """
    data = builder if builder is not None else load_builder()

    def repl(match: re.Match[str]) -> str:
        body = match.group(1)
        found = _CMD_ID_LINE_RE.search(body)
        if found is None:
            raise ValueError("ezcmd fence requires a line 'id: <command-id>'")
        cmd_id = found.group(1)
        try:
            command_by_id(cmd_id, data)
        except KeyError as exc:
            raise ValueError(f"unknown ezcmd id {cmd_id!r}") from exc
        return _builder_widget_html(cmd_id, data)

    return _EZCMD_FENCE_RE.sub(repl, markdown)


def inject_command_assets(
    document: str, builder: Mapping[str, Any] | None = None
) -> str:
    """Append the command-builder JSON blob once (before ``</body>``).

    Args:
        document: Rendered HTML.
        builder: Optional preloaded builder.

    Returns:
        HTML with ``#ez-cmd-data`` injected.
    """
    if 'id="ez-cmd-data"' in document:
        return document
    data = builder if builder is not None else load_builder()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c")
    blob = (
        '<script type="application/json" id="ez-cmd-data">'
        f"{payload}</script>\n"
    )
    lower = document.lower()
    idx = lower.rfind("</body>")
    if idx == -1:
        return document + blob
    return document[:idx] + blob + document[idx:]

"""Shared VS Code workspace files stay generic and secret-free.

Hermetic: stdlib JSON. Does not launch VS Code or read the user profile.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VSCODE = ROOT / ".vscode"
DEVCONTAINER = ROOT / ".devcontainer" / "devcontainer.json"
TRACKED = (
    "extensions.json",
    "launch.json",
    "settings.json",
    "tasks.json",
)
FORBIDDEN_SETTING_KEYS = frozenset(
    {
        "python.defaultInterpreterPath",
        "python.envFile",
    }
)
LEAK_RE = re.compile(
    r"(/Users/|/home/|\$\{env:|SPARK_HOST|SPARK_USER|API_KEY|"
    r"HF_TOKEN|\.pem\b|(?<![A-Za-z])SECRET(?![A-Za-z]))"
)
GITIGNORE_ALLOW = (
    "!.vscode/extensions.json",
    "!.vscode/settings.json",
    "!.vscode/tasks.json",
    "!.vscode/launch.json",
)


def _load_json(path: Path) -> Any:
    """Parse a committed JSON file.

    Args:
        path: File under the repo.

    Returns:
        Decoded JSON value.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_strings(value: Any) -> list[str]:
    """Collect string leaves from a JSON value.

    Args:
        value: Decoded JSON.

    Returns:
        String leaves in walk order.
    """
    found: list[str] = []
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, list):
        for item in value:
            found.extend(_walk_strings(item))
    elif isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                found.append(key)
            found.extend(_walk_strings(item))
    return found


def _walk_keys(value: Any) -> list[str]:
    """Collect object keys from a JSON value.

    Args:
        value: Decoded JSON.

    Returns:
        Object keys in walk order.
    """
    found: list[str] = []
    if isinstance(value, list):
        for item in value:
            found.extend(_walk_keys(item))
    elif isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                found.append(key)
            found.extend(_walk_keys(item))
    return found


def test_tracked_vscode_files_are_strict_json() -> None:
    """The four shared workspace files parse without comments."""
    missing = [name for name in TRACKED if not (VSCODE / name).is_file()]
    assert missing == [], f"missing .vscode files: {missing}"
    for name in TRACKED:
        parsed = _load_json(VSCODE / name)
        assert parsed is not None


def test_gitignore_allowlists_shared_vscode_files() -> None:
    """Local VS Code state stays ignored; the four shared files are re-included."""
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".vscode/*" in text
    missing = [line for line in GITIGNORE_ALLOW if line not in text]
    assert missing == [], f"gitignore missing allowlist lines: {missing}"


def test_recommendations_cover_devcontainer_extensions() -> None:
    """Laptop recommendations are a superset of the devcontainer list."""
    workspace = _load_json(VSCODE / "extensions.json")
    recommended = workspace.get("recommendations")
    assert isinstance(recommended, list)
    rec_ids = {item for item in recommended if isinstance(item, str)}
    dev = _load_json(DEVCONTAINER)
    custom = dev.get("customizations")
    assert isinstance(custom, dict)
    vscode = custom.get("vscode")
    assert isinstance(vscode, dict)
    container_ext = vscode.get("extensions")
    assert isinstance(container_ext, list)
    missing = [
        item
        for item in container_ext
        if isinstance(item, str) and item not in rec_ids
    ]
    assert missing == [], f"devcontainer extensions missing from .vscode: {missing}"


def test_settings_do_not_pin_interpreter_or_env_file() -> None:
    """Workspace settings must not point at a machine interpreter or .env."""
    settings = _load_json(VSCODE / "settings.json")
    assert isinstance(settings, dict)
    present = sorted(FORBIDDEN_SETTING_KEYS & set(settings))
    assert present == []


def test_launch_configs_do_not_use_env_file() -> None:
    """Debug configs use an explicit env allow-list, not envFile."""
    launch = _load_json(VSCODE / "launch.json")
    keys = set(_walk_keys(launch))
    assert "envFile" not in keys
    configs = launch.get("configurations")
    assert isinstance(configs, list)
    assert configs
    for config in configs:
        assert isinstance(config, dict)
        env = config.get("env")
        assert isinstance(env, dict)
        assert "PYTHONPATH" in env
        assert "${workspaceFolder}" in str(env["PYTHONPATH"])
        assert env.get("LAB_HERMETIC") == "1"


def test_vscode_json_has_no_machine_or_secret_strings() -> None:
    """Committed workspace JSON has no home paths, host vars, or secret keys."""
    leaks: list[str] = []
    for name in TRACKED:
        payload = _load_json(VSCODE / name)
        for raw in _walk_strings(payload):
            match = LEAK_RE.search(raw)
            if match:
                leaks.append(f"{name}: {raw!r} ({match.group(0)!r})")
    assert leaks == [], "secret or machine-local strings in .vscode:\n" + "\n".join(
        leaks
    )


def test_tasks_wrap_bazelisk_entry_points() -> None:
    """Run Task labels call the same bazelisk commands as CONTRIBUTING."""
    tasks = _load_json(VSCODE / "tasks.json")
    assert isinstance(tasks, dict)
    items = tasks.get("tasks")
    assert isinstance(items, list)
    by_label = {
        item["label"]: item["command"]
        for item in items
        if isinstance(item, dict) and "label" in item and "command" in item
    }
    assert by_label["validate"] == "bazelisk run //:validate"
    assert by_label["test-fast"] == "bazelisk test //:test-fast"
    assert "bazelisk test //tests:pytest" in by_label["pytest"]
    assert by_label["typecheck"] == "bazelisk test //tests:typecheck"
    assert "bazelisk test //:lint" in by_label["lint"]
    assert by_label["fix"] == "bazelisk run //:fix"
    assert by_label["docs"] == "bazelisk run //docs:docs"

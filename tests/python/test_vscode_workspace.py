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
        "python.analysis.extraPaths",
        "python.analysis.typeCheckingMode",
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
REQUIRED_RECS = (
    "bazelbuild.vscode-bazel",
    "bradlc.vscode-tailwindcss",
    "github.vscode-github-actions",
    "mkhl.shfmt",
    "ms-azuretools.vscode-containers",
    "ms-python.debugpy",
    "ms-python.mypy-type-checker",
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-vscode-remote.remote-containers",
    "redhat.vscode-yaml",
    "timonwong.shellcheck",
    "unifiedjs.vscode-mdx",
)
REQUIRED_UNWANTED = (
    "charliermarsh.ruff",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "foxundermoon.shell-format",
    "ms-azuretools.vscode-docker",
    "ms-python.autopep8",
    "ms-python.black-formatter",
    "ms-python.flake8",
    "ms-python.isort",
    "ms-python.pylint",
    "ms-vscode.makefile-tools",
)
EXPLORER_HIDE = (
    "coverage",
    "docs-site/.next",
    "docs-site/node_modules",
    "docs-site/out",
    "docs-site/out-linux",
    "site",
)
WATCHER_HIDE = (
    "docs-site/public/assets/**",
    "docs/assets/**",
)
READONLY_EXTRA = (
    "docs-site/out/**",
    "site/**",
)
NO_FORMAT_ON_SAVE = (
    "[css]",
    "[github-actions-workflow]",
    "[javascript]",
    "[json]",
    "[jsonc]",
    "[markdown]",
    "[mdx]",
    "[python]",
    "[yaml]",
)
FORMAT_ON_SAVE = (
    "[shellscript]",
    "[starlark]",
)
TASK_ENV = {
    "EZ_COMFY_PROGRESS": "0",
    "HF_PROGRESS": "0",
    "LAB_HERMETIC": "1",
}


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


def _extension_ids(payload: Any, key: str) -> set[str]:
    """Collect string extension IDs from an extensions.json list.

    Args:
        payload: Parsed extensions.json.
        key: ``recommendations`` or ``unwantedRecommendations``.

    Returns:
        Extension IDs.
    """
    assert isinstance(payload, dict)
    items = payload.get(key)
    assert isinstance(items, list)
    return {item for item in items if isinstance(item, str)}


def test_recommendations_cover_devcontainer_extensions() -> None:
    """Laptop recommendations are a superset of the devcontainer list."""
    rec_ids = _extension_ids(_load_json(VSCODE / "extensions.json"), "recommendations")
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


def test_recommendations_cover_repo_languages() -> None:
    """Laptop recs cover Bazel, Python, shell, YAML, MDX, Tailwind, Actions, containers."""
    rec_ids = _extension_ids(_load_json(VSCODE / "extensions.json"), "recommendations")
    missing = [item for item in REQUIRED_RECS if item not in rec_ids]
    assert missing == [], f"missing recommendations: {missing}"
    assert "ms-azuretools.vscode-docker" not in rec_ids
    assert "ms-playwright.playwright" not in rec_ids


def test_unwanted_recommendations_hide_non_gates() -> None:
    """Unwanted list hides formatters and the archived Docker pack."""
    payload = _load_json(VSCODE / "extensions.json")
    rec_ids = _extension_ids(payload, "recommendations")
    unwanted = _extension_ids(payload, "unwantedRecommendations")
    missing = [item for item in REQUIRED_UNWANTED if item not in unwanted]
    assert missing == [], f"missing unwantedRecommendations: {missing}"
    overlap = sorted(rec_ids & unwanted)
    assert overlap == [], f"extension in both lists: {overlap}"


def test_settings_do_not_pin_interpreter_or_env_file() -> None:
    """Workspace settings must not pin interpreter, .env, or Pyright extras."""
    settings = _load_json(VSCODE / "settings.json")
    assert isinstance(settings, dict)
    present = sorted(FORBIDDEN_SETTING_KEYS & set(settings))
    assert present == []


def test_settings_hide_generated_trees_and_keep_format_on_save_narrow() -> None:
    """Explorer hides generated trees; format-on-save is shell and Starlark only."""
    settings = _load_json(VSCODE / "settings.json")
    assert isinstance(settings, dict)
    exclude = settings.get("files.exclude")
    assert isinstance(exclude, dict)
    missing_exclude = [key for key in EXPLORER_HIDE if key not in exclude]
    assert missing_exclude == [], f"files.exclude missing: {missing_exclude}"
    watcher = settings.get("files.watcherExclude")
    assert isinstance(watcher, dict)
    missing_watch = [key for key in WATCHER_HIDE if key not in watcher]
    assert missing_watch == [], f"files.watcherExclude missing: {missing_watch}"
    readonly = settings.get("files.readonlyInclude")
    assert isinstance(readonly, dict)
    missing_ro = [key for key in READONLY_EXTRA if key not in readonly]
    assert missing_ro == [], f"files.readonlyInclude missing: {missing_ro}"
    assert settings.get("editor.formatOnSave") is False
    assert settings.get("typescript.enablePromptUseWorkspaceTsdk") is True
    assert settings.get("typescript.tsdk") == "docs-site/node_modules/typescript/lib"
    assert settings.get("mypy-type-checker.cwd") == "${workspaceFolder}"
    assert settings.get("css.lint.unknownAtRules") == "ignore"
    tailwind_langs = settings.get("tailwindCSS.includeLanguages")
    assert isinstance(tailwind_langs, dict)
    assert tailwind_langs.get("mdx") == "html"
    assert settings.get("tailwindCSS.experimental.configFile") == (
        "docs-site/app/global.css"
    )
    associations = settings.get("files.associations")
    assert isinstance(associations, dict)
    assert associations.get("*.bats") == "shellscript"
    assert associations.get("docker-compose*.yml") == "dockercompose"
    assert associations.get("compose*.yml") == "dockercompose"
    for lang in NO_FORMAT_ON_SAVE:
        block = settings.get(lang)
        assert isinstance(block, dict), f"{lang} settings missing"
        assert block.get("editor.formatOnSave") is False, lang
    for lang in FORMAT_ON_SAVE:
        block = settings.get(lang)
        assert isinstance(block, dict), f"{lang} settings missing"
        assert block.get("editor.formatOnSave") is True, lang
    markdown = settings.get("[markdown]")
    assert isinstance(markdown, dict)
    assert markdown.get("files.trimTrailingWhitespace") is False
    mdx = settings.get("[mdx]")
    assert isinstance(mdx, dict)
    assert mdx.get("files.trimTrailingWhitespace") is False


def test_launch_configs_do_not_use_env_file() -> None:
    """Debug configs use an explicit env allow-list, not envFile."""
    launch = _load_json(VSCODE / "launch.json")
    keys = set(_walk_keys(launch))
    assert "envFile" not in keys
    configs = launch.get("configurations")
    assert isinstance(configs, list)
    assert configs
    purposes: list[str] = []
    for config in configs:
        assert isinstance(config, dict)
        env = config.get("env")
        assert isinstance(env, dict)
        assert "PYTHONPATH" in env
        assert "${workspaceFolder}" in str(env["PYTHONPATH"])
        assert env.get("LAB_HERMETIC") == "1"
        purpose = config.get("purpose")
        if isinstance(purpose, list):
            purposes.extend(item for item in purpose if isinstance(item, str))
    assert "debug-test" in purposes


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
    options = tasks.get("options")
    assert isinstance(options, dict)
    env = options.get("env")
    assert isinstance(env, dict)
    for key, value in TASK_ENV.items():
        assert env.get(key) == value, key
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
    assert by_label["doctor"] == "bazelisk run //:manage -- doctor"
    assert by_label["docs-serve"] == "bazelisk run //docs:serve"
    background = [
        item.get("isBackground")
        for item in items
        if isinstance(item, dict) and item.get("label") == "docs-serve"
    ]
    assert background == [None] or background == [False]


def test_bazel_core_path_filters_include_vscode() -> None:
    """Workspace-only edits still run the core test slice."""
    validate = (ROOT / "scripts" / "validate.sh").read_text(encoding="utf-8")
    assert "[[ ${path} == .vscode/* ]]" in validate
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "'.vscode/**'" in ci

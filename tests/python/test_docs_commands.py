"""Command-builder JSON, substitution spec, ezcmd fences, MkDocs wiring.

Hermetic: stdlib + docs/commands.py. No MkDocs, network, or browser.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMMANDS_PY = ROOT / "docs" / "commands.py"
BUILDER_JSON = ROOT / "includes" / "command-builder.json"
MKDOCS_YML = ROOT / "mkdocs.yml"
HOOKS_PY = ROOT / "docs" / "hooks.py"
COMMANDS_JS = ROOT / "docs" / "javascripts" / "commands.js"
EXTRA_CSS = ROOT / "docs" / "stylesheets" / "extra.css"
CONVENTIONS = ROOT / "docs" / "project-conventions.md"
DOWNLOAD_TIERS = ROOT / "docs" / "download-tiers.md"
DOCS = ROOT / "docs"

SESSION_IDS = (
    "SPARK_HOST",
    "SPARK_USER",
    "MODELS_DIR",
    "COMFY_OUTPUT_DIR",
    "COMFY_PORT",
    "DOWNLOAD_LIMIT",
)


def _load_commands():
    """Load docs/commands.py as a module.

    Returns:
        Loaded module.
    """
    spec = importlib.util.spec_from_file_location("ez_docs_commands", COMMANDS_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["ez_docs_commands"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def cmd():
    """Loaded commands module."""
    return _load_commands()


@pytest.fixture
def builder(cmd):
    """Shipped builder JSON (validated)."""
    return cmd.load_builder(BUILDER_JSON)


def test_shipped_builder_validates(cmd) -> None:
    """includes/command-builder.json matches the session-var contract."""
    data = cmd.load_builder(BUILDER_JSON)
    ids = [row["id"] for row in data["variables"]]
    assert tuple(ids) == SESSION_IDS
    cmd_ids = [row["id"] for row in data["commands"]]
    assert "download-models" in cmd_ids
    assert "download-music" in cmd_ids
    assert "download-wan" in cmd_ids
    assert "disk-wizard-plan" in cmd_ids
    assert len(cmd_ids) == len(set(cmd_ids))


def test_validate_builder_rejects_missing_session_var(cmd) -> None:
    """Dropping SPARK_HOST fails closed."""
    raw = json.loads(BUILDER_JSON.read_text(encoding="utf-8"))
    raw["variables"] = [v for v in raw["variables"] if v["id"] != "SPARK_HOST"]
    with pytest.raises(ValueError, match="missing session"):
        cmd.validate_builder(raw)


def test_validate_builder_rejects_duplicate_command(cmd, builder) -> None:
    """Duplicate command ids are a schema error."""
    data = json.loads(json.dumps(builder))
    data["commands"].append(data["commands"][0])
    with pytest.raises(ValueError, match="duplicate command"):
        cmd.validate_builder(data)


def test_substitute_vars_replaces_known_only(cmd) -> None:
    """Known tokens change; unknown ${FOO} stays; not recursive."""
    values = {"SPARK_HOST": "10.1.2.3", "COMFY_PORT": "9000"}
    text = "open http://${SPARK_HOST}:${COMFY_PORT} and ${FOO}"
    out = cmd.substitute_vars(text, values)
    assert out == "open http://10.1.2.3:9000 and ${FOO}"
    nested = cmd.substitute_vars("host=${SPARK_HOST}", {"SPARK_HOST": "${COMFY_PORT}"})
    assert nested == "host=${COMFY_PORT}"


def test_template_has_vars(cmd) -> None:
    """Auto-bind only when a session ${VAR} is present."""
    assert cmd.template_has_vars("ssh ${SPARK_USER}@${SPARK_HOST}")
    assert not cmd.template_has_vars("./scripts/manage.sh doctor")
    assert not cmd.template_has_vars("echo ${NOT_A_SESSION}")


def test_render_command_omits_unchecked_bool(cmd, builder) -> None:
    """--drop-incomplete is absent until checked."""
    recipe = cmd.command_by_id("download-models", builder)
    defaults = cmd.default_var_values(builder)
    plain = cmd.render_command(recipe, {"limit": "auto"}, defaults)
    assert plain == "./scripts/manage.sh download-models --limit auto"
    assert "--drop-incomplete" not in plain
    dropped = cmd.render_command(
        recipe, {"limit": "auto", "drop-incomplete": True}, defaults
    )
    assert dropped == (
        "./scripts/manage.sh download-models --limit auto --drop-incomplete"
    )


def test_render_command_choice_or_int_emits_mbps(cmd, builder) -> None:
    """choice-or-int copies --limit 80, not a 'custom' token."""
    recipe = cmd.command_by_id("download-music", builder)
    defaults = cmd.default_var_values(builder)
    auto = cmd.render_command(
        recipe, {"tier": "turbo", "limit": "auto"}, defaults
    )
    assert auto == "./scripts/manage.sh download-music --tier turbo --limit auto"
    mbps = cmd.render_command(
        recipe, {"tier": "xl", "limit": "80"}, defaults
    )
    assert mbps == "./scripts/manage.sh download-music --tier xl --limit 80"
    off = cmd.render_command(
        recipe, {"tier": "turbo", "limit": "off"}, defaults
    )
    assert off.endswith("--limit off")


def test_render_command_bind_var_uses_session_limit(cmd, builder) -> None:
    """Unset --limit follows DOWNLOAD_LIMIT from Your Spark."""
    recipe = cmd.command_by_id("download-models", builder)
    values = cmd.default_var_values(builder)
    values["DOWNLOAD_LIMIT"] = "200"
    line = cmd.render_command(recipe, {}, values)
    assert "--limit 200" in line


def test_render_command_required_tier(cmd, builder) -> None:
    """Required --tier uses the recipe default when flags omit it."""
    recipe = cmd.command_by_id("download-wan", builder)
    line = cmd.render_command(recipe, {}, cmd.default_var_values(builder))
    assert line == "./scripts/utilities/download-wan.sh run --tier 5b"


def test_render_ssh_forward_substitutes_host(cmd, builder) -> None:
    """Port-forward recipe copies the operator's Spark IP."""
    recipe = cmd.command_by_id("ssh-forward", builder)
    values = cmd.default_var_values(builder)
    values["SPARK_HOST"] = "spark.lan"
    values["SPARK_USER"] = "alx"
    values["COMFY_PORT"] = "8188"
    line = cmd.render_command(recipe, {}, values)
    assert line == "ssh -L 8188:127.0.0.1:8188 alx@spark.lan"


def test_expand_ezcmd_widget_and_unknown(cmd, builder) -> None:
    """Known id becomes a widget; unknown id fails the strict build."""
    md = "before\n\n```ezcmd\nid: download-music\n```\n\nafter\n"
    out = cmd.expand_ezcmd(md, builder)
    assert "```ezcmd" not in out
    assert 'data-ez-cmd="download-music"' in out
    assert "download-music --tier turbo" in out
    with pytest.raises(ValueError, match="unknown ezcmd"):
        cmd.expand_ezcmd("```ezcmd\nid: not-a-command\n```\n", builder)
    with pytest.raises(ValueError, match="id:"):
        cmd.expand_ezcmd("```ezcmd\nfoo: bar\n```\n", builder)


def test_inject_command_assets_once(cmd, builder) -> None:
    """JSON blob lands before </body> and is not duplicated."""
    html = "<html><body><p>hi</p></body></html>"
    once = cmd.inject_command_assets(html, builder)
    assert 'id="ez-cmd-data"' in once
    assert "download-models" in once
    assert "\\u003c" in json.dumps(builder).replace("<", "\\u003c") or "<" not in (
        once.split('id="ez-cmd-data">')[1].split("</script>")[0]
        if "<" in once.split('id="ez-cmd-data">')[1].split("</script>")[0]
        else ""
    )
    twice = cmd.inject_command_assets(once, builder)
    assert twice.count('id="ez-cmd-data"') == 1


def test_mkdocs_wires_commands_js(cmd) -> None:
    """extra_javascript lists commands.js; hooks expand ezcmd."""
    del cmd
    yml = MKDOCS_YML.read_text(encoding="utf-8")
    assert "javascripts/commands.js" in yml
    assert "javascripts/glossary.js" in yml
    hooks = HOOKS_PY.read_text(encoding="utf-8")
    assert "expand_ezcmd" in hooks
    assert "inject_command_assets" in hooks
    assert COMMANDS_JS.is_file()
    js = COMMANDS_JS.read_text(encoding="utf-8")
    assert "ez-comfy.cmdvars" in js
    assert "data-clipboard-text" in js
    assert "document$.subscribe" in js
    css = EXTRA_CSS.read_text(encoding="utf-8")
    assert ".ez-spark-panel" in css
    assert ".ez-cmd-builder" in css
    assert CONVENTIONS.read_text(encoding="utf-8").find("ezcmd") != -1


def test_download_tiers_page_states_pack_not_quality() -> None:
    """Tier page exists and says --tier is a pack id."""
    text = DOWNLOAD_TIERS.read_text(encoding="utf-8")
    assert "What's on this page" in text
    assert "What this enables" in text
    assert "Klein 4B" in text
    assert "Wan 2.2" in text
    assert "LTX-2.5" in text
    assert "pack" in text.lower()
    assert "download-models" in text
    assert "--limit" in text
    assert "not a quality" in text.lower() or "not “better”" in text or "not a universal" in text.lower()
    assert "vace" in text
    assert "does not include" in text.lower() or "not in `--tier all`" in text or "not in all" in text.lower()
    assert "```ezcmd" in text
    assert "id: download-music" in text


def test_operator_download_pages_use_ezcmd_or_session_vars() -> None:
    """Flagged download examples on Operate pages are live widgets or ${VAR}."""
    pages = [
        DOCS / "download-tiers.md",
        DOCS / "getting-started.md",
        DOCS / "manage-cli.md",
        DOCS / "models-and-cache.md",
    ]
    for path in pages:
        text = path.read_text(encoding="utf-8")
        assert "${SPARK_HOST}" in text or "```ezcmd" in text, path.name

"""Every public manage.sh verb has comments, catalog copy, and an ezcmd id.

Hermetic: stdlib + JSON. No MkDocs, Docker, or network.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANAGE = ROOT / "scripts" / "manage.sh"
MANAGE_CLI = ROOT / "docs" / "manage-cli.md"
GENERATED = ROOT / "docs" / "generated" / "shell" / "reference.md"
BUILDER = ROOT / "includes" / "command-builder.json"

BANNED = frozenset({"download-h3", "queue-h3", "farm-h3", "stitch-h3"})
BUILDER_ALIASES = {
    "reap-models": frozenset({"reap-models", "reap-models-plan"}),
    "disk-wizard": frozenset({"disk-wizard", "disk-wizard-plan"}),
}


def manage_case_verbs(text: str) -> list[str]:
    """Parse public verbs from manage.sh ``case`` (skip banned H3 aliases).

    Args:
        text: manage.sh source.

    Returns:
        Unique verb names in case order.
    """
    verbs: list[str] = []
    in_case = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("case ") and "${cmd}" in stripped:
            in_case = True
            continue
        if not in_case:
            continue
        if stripped.startswith("esac"):
            break
        if ")" not in stripped or stripped.startswith("*"):
            continue
        left = stripped.split(")", 1)[0]
        for part in left.split("|"):
            token = part.strip()
            if token in {"-h", "--help"} or token in BANNED:
                continue
            if token and token not in verbs:
                verbs.append(token)
    return verbs


def test_manage_verbs_have_command_comments_catalog_and_ezcmd() -> None:
    """Public verbs are documented in comments, manage-cli.md, generated page, builder."""
    manage = MANAGE.read_text(encoding="utf-8")
    catalog = MANAGE_CLI.read_text(encoding="utf-8")
    generated = GENERATED.read_text(encoding="utf-8")
    builder = json.loads(BUILDER.read_text(encoding="utf-8"))
    builder_ids = {row["id"] for row in builder["commands"]}
    verbs = manage_case_verbs(manage)
    assert "doctor" in verbs
    assert "start" in verbs
    assert "promote-workflow" in verbs
    missing_cmd: list[str] = []
    missing_catalog: list[str] = []
    missing_generated: list[str] = []
    missing_builder: list[str] = []
    for verb in verbs:
        if f"# @command {verb}" not in manage:
            missing_cmd.append(verb)
        if verb not in catalog:
            missing_catalog.append(verb)
        if f"Command: {verb}" not in generated:
            missing_generated.append(verb)
        aliases = BUILDER_ALIASES.get(verb, frozenset({verb}))
        if builder_ids.isdisjoint(aliases):
            missing_builder.append(verb)
    assert missing_cmd == [], "missing # @command:\n" + "\n".join(missing_cmd)
    assert missing_catalog == [], "missing from manage-cli.md:\n" + "\n".join(missing_catalog)
    assert missing_generated == [], "missing from generated reference:\n" + "\n".join(
        missing_generated
    )
    assert missing_builder == [], "missing command-builder id:\n" + "\n".join(missing_builder)


def test_banned_h3_aliases_are_not_ezcmd_recipes() -> None:
    """MiniMax H3 aliases must not appear as pasteable command-builder ids."""
    builder = json.loads(BUILDER.read_text(encoding="utf-8"))
    ids = {row["id"] for row in builder["commands"]}
    assert ids.isdisjoint(BANNED)

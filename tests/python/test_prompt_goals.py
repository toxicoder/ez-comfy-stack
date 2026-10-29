"""Tests for the goal layer: lane -> goal resolution and system composition.

The family templates in ``prompts/`` optimize for the model. The goal layer
optimizes for the job the lane exists to do, so these tests assert both halves:
that a lane resolves to the right goal, and that the goal language actually
reaches the composed system prompt.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from ez_prompt_enhance import _styles, client, samples
from ez_prompt_enhance.nodes import EZKleinPromptEnhance

GOALS = samples.load_goals()


def _system_for(
    catalog: str,
    *,
    goal: object = samples.GOAL_AUTO,
    mode: str = "t2i",
    duration_hint: str = "16:9",
) -> str:
    """Return the composed system prompt one Klein run would send.

    Arguments:
        catalog: Value stamped into the hidden ``catalog`` widget.
        goal: Explicit ``goal`` combo widget.
        mode: Klein mode widget.
        duration_hint: Framing line.

    Returns:
        The system string handed to the LLM.
    """
    klein = EZKleinPromptEnhance()
    with patch.object(client, "complete", return_value=("out", None)) as mock:
        klein.run(
            "a mug on a table",
            True,
            mode,
            duration_hint,
            catalog=catalog,
            goal=goal,
        )
    return str(mock.call_args[0][0])


def test_goal_registry_shape() -> None:
    assert GOALS, "goals.json must register at least one goal"
    for gid, entry in GOALS.items():
        assert gid == gid.strip().lower().replace(" ", "_"), gid
        assert entry.get("label"), gid
        assert len(str(entry.get("llm_block", "")).split()) >= 20, gid
        assert entry.get("sample_clause"), gid


def test_goal_registry_is_ascii() -> None:
    raw = (samples.PACKAGE_DIR / samples.GOALS_NAME).read_text(encoding="utf-8")
    assert raw.isascii(), "goal text must stay free of confusable unicode"


def test_goal_index_points_at_registered_goals() -> None:
    index = samples.load_goal_index()
    assert index, "goal_index.json must map lanes"
    unknown = {rel: gid for rel, gid in index.items() if gid not in GOALS}
    assert unknown == {}, unknown


def test_goal_ids_leads_with_auto_then_none() -> None:
    ids = samples.goal_ids()
    assert ids[0] == samples.GOAL_AUTO
    assert ids[1] == samples.GOAL_NONE
    assert ids[2:] == list(GOALS.keys())


def test_goal_for_resolves_the_named_deliverables() -> None:
    cases = {
        "stills/thumbnail": "thumbnail_cover_hero",
        "creator/stills/youtube-shorts-thumb": "vertical_caption_headroom",
        "creator/stills/pinterest-pin": "vertical_caption_headroom",
        "services/ecommerce/pdp-on-white": "packshot_conversion",
        "services/b2b-saas/webinar-thumb": "thumbnail_cover_hero",
        "services/real-estate/listing-hero": "place_credibility",
    }
    for rel, want in cases.items():
        assert samples.goal_for_rel(rel) == want, rel


def test_goal_for_leaves_tools_and_motion_goalless() -> None:
    for rel in ("", "motion/av/hook-av", "audio/music/rap-draft", "nope/nope"):
        assert samples.goal_for_rel(rel) == samples.GOAL_NONE, rel


def test_goal_for_normalises_separators() -> None:
    assert samples.goal_for_rel("stills\\thumbnail") == "thumbnail_cover_hero"


def test_goal_label_variants() -> None:
    assert samples.goal_label("thumbnail_cover_hero") == GOALS[
        "thumbnail_cover_hero"
    ]["label"]
    assert samples.goal_label(samples.GOAL_AUTO) == "Auto (from lane)"
    assert samples.goal_label(samples.GOAL_NONE) == "None"
    assert samples.goal_label("not-a-goal") == ""


def test_goal_field_variants() -> None:
    assert samples.goal_field("thumbnail_cover_hero", "sample_clause")
    assert samples.goal_field("thumbnail_cover_hero", "missing_field") == ""
    assert samples.goal_field(samples.GOAL_AUTO, "sample_clause") == ""
    assert samples.goal_field(samples.GOAL_NONE, "sample_clause") == ""
    assert samples.goal_field("", "sample_clause") == ""
    assert samples.goal_field("not-a-goal", "sample_clause") == ""


def test_resolve_goal_prefers_the_explicit_pick() -> None:
    assert (
        samples.resolve_goal(
            "packshot_conversion", catalog="stills/thumbnail"
        )
        == "packshot_conversion"
    )


def test_resolve_goal_falls_back_to_the_stamped_lane() -> None:
    assert (
        samples.resolve_goal("", catalog="stills/thumbnail")
        == "thumbnail_cover_hero"
    )
    assert (
        samples.resolve_goal("", catalog="", lab_rel="stills/thumbnail")
        == "thumbnail_cover_hero"
    )


def test_resolve_goal_ignores_an_unknown_pick() -> None:
    assert (
        samples.resolve_goal("invented-goal", catalog="stills/thumbnail")
        == "thumbnail_cover_hero"
    )


def test_resolve_goal_defaults_to_none() -> None:
    assert samples.resolve_goal("") == samples.GOAL_NONE
    assert samples.resolve_goal("", catalog="motion/av/hook-av") == samples.GOAL_NONE


def test_resolve_goal_auto_derives_and_none_opts_out() -> None:
    """The two sentinels must not collapse onto each other.

    ``auto`` is what every shipped graph carries, so it has to derive or the
    goal layer would never fire. ``none`` has to refuse, or an operator has no
    way back to a model-only prompt on a lane that carries a deliverable.
    """
    lane = "stills/thumbnail"
    assert samples.goal_for_rel(lane) == "thumbnail_cover_hero"
    assert samples.resolve_goal(samples.GOAL_AUTO, catalog=lane) == (
        "thumbnail_cover_hero"
    )
    assert samples.resolve_goal("", catalog=lane) == "thumbnail_cover_hero"
    assert samples.resolve_goal(samples.GOAL_NONE, catalog=lane) == samples.GOAL_NONE
    assert samples.resolve_goal(samples.GOAL_AUTO) == samples.GOAL_NONE


def test_goal_llm_block_empty_and_set() -> None:
    assert _styles.goal_llm_block(samples.GOAL_NONE) == ""
    assert _styles.goal_llm_block("not-a-goal") == ""
    block = _styles.goal_llm_block("thumbnail_cover_hero")
    assert block.startswith("Goal: ")
    assert "read at that size" in block


def test_with_goal_system_appends_and_passthrough() -> None:
    assert _styles.with_goal_system("BASE", samples.GOAL_NONE) == "BASE"
    assert _styles.with_goal_system("BASE", "not-a-goal") == "BASE"
    assert _styles.with_goal_system("BASE", "") == "BASE"
    out = _styles.with_goal_system("BASE\n", "thumbnail_cover_hero")
    assert out.startswith("BASE\n\nGoal: ")


def test_thumbnail_lane_gets_readable_at_small_language() -> None:
    system = _system_for("stills/thumbnail")
    lowered = system.lower()
    assert "read at that size" in lowered
    assert "title can sit later" in lowered


def test_vertical_lane_gets_caption_headroom_language() -> None:
    system = _system_for("creator/stills/pinterest-pin")
    lowered = system.lower()
    assert "middle third" in lowered
    assert "captions" in lowered


def test_goalless_lane_stays_model_only() -> None:
    system = _system_for("stills/still-draft")
    assert "Deliverable goal" not in system


def test_goal_block_sits_after_template_and_before_style() -> None:
    klein = EZKleinPromptEnhance()
    with patch.object(client, "complete", return_value=("out", None)) as mock:
        klein.run(
            "a mug",
            True,
            "t2i",
            "16:9",
            style="photorealistic",
            catalog="stills/thumbnail",
        )
    system = str(mock.call_args[0][0])
    assert system.index("Qwen3-4B") < system.index("Deliverable goal")
    assert system.index("Deliverable goal") < system.index("That style is the only look")


def test_explicit_goal_widget_overrides_the_lane() -> None:
    system = _system_for("stills/thumbnail", goal="packshot_conversion")
    assert "seamless field" in system.lower()


def test_missing_goal_files_degrade_to_model_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(samples, "PACKAGE_DIR", tmp_path)
    assert samples.load_goals() == {}
    assert samples.load_goal_index() == {}
    assert samples.goal_for_rel("stills/thumbnail") == samples.GOAL_NONE


def test_non_object_goal_json_is_treated_as_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / samples.GOALS_NAME).write_text("[]", encoding="utf-8")
    (tmp_path / samples.GOAL_INDEX_NAME).write_text("[]", encoding="utf-8")
    monkeypatch.setattr(samples, "PACKAGE_DIR", tmp_path)
    assert samples.load_goals() == {}
    assert samples.load_goal_index() == {}


def test_every_goal_reaches_a_real_system_prompt() -> None:
    for gid in GOALS:
        system = _system_for("", goal=gid)
        assert "Deliverable goal" in system, gid


def test_goal_files_are_tracked_and_next_to_the_style_registry() -> None:
    assert (samples.PACKAGE_DIR / samples.GOALS_NAME).is_file()
    assert (samples.PACKAGE_DIR / samples.GOAL_INDEX_NAME).is_file()
    assert (samples.PACKAGE_DIR / "styles.json").is_file()


def test_client_reexports_the_goal_helpers() -> None:
    assert client.with_goal_system is _styles.with_goal_system
    assert client.goal_llm_block is _styles.goal_llm_block


def test_goal_widget_is_optional_so_graphs_need_no_rewrite() -> None:
    types: dict[str, Any] = EZKleinPromptEnhance.INPUT_TYPES()
    assert "goal" not in types["required"]
    assert "goal" in types["optional"]
    values, spec = types["optional"]["goal"]
    assert values[0] == samples.GOAL_AUTO
    assert spec["default"] == samples.GOAL_AUTO


def test_none_widget_reaches_a_model_only_prompt_end_to_end() -> None:
    """The documented opt-out has to survive the whole node path."""
    with_goal = _system_for("stills/thumbnail")
    without_goal = _system_for("stills/thumbnail", goal=samples.GOAL_NONE)
    assert "Deliverable goal" in with_goal
    assert "Deliverable goal" not in without_goal

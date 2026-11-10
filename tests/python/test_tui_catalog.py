"""The action catalog stays complete, honest, and impossible to talk into a run.

``scripts/lib/tui/catalog.py`` is the console's whole allowlist: whatever it
lists is what an operator can reach. These tests hold it to that job. They
parse the real ``scripts/manage.sh`` dispatcher and demand an entry for every
verb, walk every utility target onto the disk, check that the risk tiers and
guards match what the shell source actually does, and confirm that no entry
carries a baked-in confirmation.

The dispatcher text is injected into :func:`tui.catalog.manage_verbs_in` rather
than read through a helper, so the suite controls the input: one test proves the
real file is covered while the others prove the parser on synthetic dispatchers.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tui import catalog as k
from tui.contract import (
    ActionSpec,
    ConfirmKind,
    Guard,
    Group,
    ParamKind,
    RiskTier,
    RunnerKind,
    build_argv,
)

ROOT = Path(__file__).resolve().parents[2]
"""Repository root, used to read the dispatcher and the utility scripts."""

MANAGE_SH = ROOT / "scripts" / "manage.sh"
"""The operator CLI whose dispatcher defines the verb surface."""

UTILITIES_DIR = ROOT / "scripts" / "utilities"
"""Directory that holds one ``<basename>.sh`` per utility target."""

_EXPECTED_UNMANAGED: tuple[str, ...] = (
    "compile-film",
    "compress-cinema-clip",
    "concat-shots",
    "dub-fetch",
    "nvenc-preview",
    "pack-frames",
    "podcast-loudnorm",
    "spark-farm",
)
"""The utilities with no verb, which the console must reach directly."""

_BANNED_ARGV_MARKERS: tuple[str, ...] = (
    "--yes",
    "LAB_NON_INTERACTIVE",
    "LAB_CONFIRM_TOKEN",
)
"""Nothing an entry may bake into ``fixed_args``: the operator decides, not the
catalog."""

_EXPECTED_PACK_PROBES: tuple[str, ...] = (
    "download-podcast",
    "download-dub",
    "download-music",
    "download-llm",
    "download-restore",
    "download-3d",
    "download-longcat",
    "download-dreamx",
)
"""The per-pack ``status`` probes the models desk offers."""


def _dispatcher_text() -> str:
    """Read the real dispatcher text.

    Returns:
        The full text of ``scripts/manage.sh``.
    """
    return MANAGE_SH.read_text(encoding="utf-8")


def _synthetic_dispatcher(extra: str = "") -> str:
    """Build a small dispatcher text for the parser tests.

    Args:
        extra: Extra rows inserted before the default arm.

    Returns:
        Text shaped like the real ``main()`` case block.
    """
    rows = [
        "main() {",
        '  case "${cmd}" in',
        "    help | -h | --help) cmd_help ;;",
        "    doctor) cmd_doctor ;;",
        "    download-h3 | queue-h3 | farm-h3 | stitch-h3)",
        "      refuse_minimax_h3",
        "      exit 1",
        "      ;;",
        "    # a comment row that is not a pattern",
        '    status) cmd_status "$@" ;;',
    ]
    if extra:
        rows.append(extra)
    rows.extend(
        [
            "    *)",
            '      err "Unknown command: ${cmd}"',
            "      exit 1",
            "      ;;",
            "  esac",
            "}",
        ]
    )
    return "\n".join(rows)


def _haystack(action: ActionSpec) -> str:
    """The text the palette actually matches a query against.

    Args:
        action: One catalog entry.

    Returns:
        Its searchable text, case-folded.
    """
    return " ".join(
        (
            action.action_id,
            action.title,
            action.summary,
            action.target,
            action.group.value,
            " ".join(action.keywords),
        )
    ).casefold()


@pytest.mark.parametrize("action", k.all_actions(), ids=lambda a: a.action_id)
def test_every_entry_is_presentable(action: ActionSpec) -> None:
    """No row in the console can render as a blank or an orphan.

    Args:
        action: One catalog entry.
    """
    assert action.action_id
    assert action.title
    assert action.title[0].isupper()
    assert action.summary.strip()
    assert action.docs_target
    assert action.target or action.runner is RunnerKind.INTERNAL


@pytest.mark.parametrize("action", k.all_actions(), ids=lambda a: a.action_id)
def test_every_entry_declares_its_argv_honestly(action: ActionSpec) -> None:
    """A MANAGE entry runs its own verb and a UTILITY entry names a basename.

    Args:
        action: One catalog entry.
    """
    if action.runner is RunnerKind.MANAGE:
        assert action.fixed_args[0] == action.target
    else:
        assert "/" not in action.target
        assert not action.target.endswith(".sh")


@pytest.mark.parametrize("action", k.all_actions(), ids=lambda a: a.action_id)
def test_no_entry_bakes_in_a_confirmation(action: ActionSpec) -> None:
    """The operator's typed token and the automation pair stay out of argv.

    Args:
        action: One catalog entry.
    """
    for arg in action.fixed_args:
        for marker in _BANNED_ARGV_MARKERS:
            assert marker not in arg, action.action_id


@pytest.mark.parametrize("action", k.all_actions(), ids=lambda a: a.action_id)
def test_parameters_are_complete_enough_to_build(action: ActionSpec) -> None:
    """Every declared parameter can be prompted for and joined into argv.

    Args:
        action: One catalog entry.
    """
    seen: set[str] = set()
    for param in action.params:
        assert param.name not in seen, action.action_id
        seen.add(param.name)
        assert param.label, action.action_id
        positional = param.argv_style.value == "positional"
        if not positional:
            assert param.flag, action.action_id
        if param.kind is ParamKind.CHOICE:
            assert param.choices, action.action_id
            for choice in param.choices:
                assert choice.value and choice.label, action.action_id
        if param.kind is ParamKind.INT:
            assert param.low <= param.high, action.action_id


def test_action_ids_are_unique() -> None:
    """Two entries sharing an id would make the palette ambiguous."""
    ids = [action.action_id for action in k.all_actions()]
    assert len(ids) == len(set(ids))


def test_the_catalog_covers_the_whole_surface() -> None:
    """Every dispatcher verb and every unmanaged utility has an entry."""
    actions = k.all_actions()
    assert len(actions) > 90
    manage_targets = {
        action.target for action in actions if action.runner is RunnerKind.MANAGE
    }
    assert set(k.manage_verbs_in(_dispatcher_text())) <= manage_targets


def test_missing_verbs_is_empty_against_the_real_dispatcher() -> None:
    """Every label ``manage.sh`` accepts is something the console offers."""
    assert k.missing_verbs(_dispatcher_text()) == ()


def test_manage_verbs_in_reads_the_real_dispatcher_surface() -> None:
    """The parser names the 57 verbs the CLI will actually accept."""
    verbs = k.manage_verbs_in(_dispatcher_text())
    assert len(verbs) == 57
    assert len(verbs) == len(set(verbs))
    for expected in (
        "help",
        "start",
        "stop",
        "download-models",
        "download-h3",
        "reap-models",
        "cleanup",
    ):
        assert expected in verbs
    assert "*" not in verbs
    assert "-h" not in verbs
    assert "--help" not in verbs


def test_manage_verbs_in_normalises_alternates_and_drops_the_default() -> None:
    """One pattern row is one entry, and the ``*`` arm is not a verb."""
    assert k.manage_verbs_in(_synthetic_dispatcher()) == (
        "help",
        "doctor",
        "download-h3",
        "status",
    )


def test_manage_verbs_in_skips_comment_and_flag_only_rows() -> None:
    """A comment row and a flag-only pattern add no verb."""
    text = _synthetic_dispatcher("    # another comment")
    assert k.manage_verbs_in(text) == ("help", "doctor", "download-h3", "status")
    flags = _synthetic_dispatcher("    --yes | -y) SETUP_YES=1 ;;")
    assert k.manage_verbs_in(flags) == ("help", "doctor", "download-h3", "status")


def test_manage_verbs_in_without_a_dispatcher_is_empty() -> None:
    """A file with no ``case "${cmd}"`` block describes no verbs."""
    assert k.manage_verbs_in("#!/usr/bin/env bash\nmain() { echo hi; }\n") == ()


def test_missing_verbs_reports_only_the_gap() -> None:
    """A verb the catalog never learned about fails the completeness gate."""
    text = _synthetic_dispatcher("    brand-new-verb) cmd_brand_new ;;")
    assert k.missing_verbs(text) == ("brand-new-verb",)


def test_unmanaged_utilities_are_exactly_the_eight() -> None:
    """The utilities with no verb are named, and only those."""
    assert k.UNMANAGED_UTILITIES == _EXPECTED_UNMANAGED


@pytest.mark.parametrize("utility", k.UNMANAGED_UTILITIES)
def test_every_unmanaged_utility_exists_on_disk(utility: str) -> None:
    """Each named utility is a real script the runner can invoke.

    Args:
        utility: One name from :data:`tui.catalog.UNMANAGED_UTILITIES`.
    """
    assert (UTILITIES_DIR / f"{utility}.sh").is_file()


def test_every_unmanaged_utility_is_offered() -> None:
    """None of the eight is reachable only by leaving the console."""
    offered = {
        action.target
        for action in k.all_actions()
        if action.runner is RunnerKind.UTILITY
    }
    assert set(_EXPECTED_UNMANAGED) <= offered


def test_every_utility_action_target_resolves_to_a_script() -> None:
    """The disk check covers the pack probes, not just the unmanaged eight."""
    for action in k.all_actions():
        if action.runner is RunnerKind.UTILITY:
            assert (UTILITIES_DIR / f"{action.target}.sh").is_file(), action.action_id


def test_action_by_id_finds_one_entry_and_misses_cleanly() -> None:
    """The app looks actions up by id and gets ``None`` for a bad id."""
    start = k.action_by_id("stack.start")
    assert start is not None
    assert start.title == "Start the studio stack"
    assert k.action_by_id("stack.does-not-exist") is None


def test_group_actions_filters_in_catalog_order() -> None:
    """A left-rail section is a filter, not a re-sorted copy."""
    disk = k.group_actions(Group.DISK)
    assert disk
    assert all(action.group is Group.DISK for action in disk)
    expected = [
        action.action_id
        for action in k.all_actions()
        if action.group is Group.DISK
    ]
    assert [action.action_id for action in disk] == expected
    assert k.group_actions(Group.AUDIT) == ()


def test_every_section_has_something_to_show() -> None:
    """No hotkey leads an operator to an empty pane."""
    for group in Group:
        if group is Group.AUDIT:
            continue
        assert k.group_actions(group), group.value


def test_search_matches_title_summary_and_keywords() -> None:
    """The palette finds an entry by any of the words that describe it."""
    assert "stack.start" in [a.action_id for a in k.search("start the studio")]
    assert "models.download_limit_clear" in [
        a.action_id for a in k.search("unthrottle")
    ]
    assert "occupancy.enter_blender_desk" in [
        a.action_id for a in k.search("park blender")
    ]


def test_search_terms_narrow_rather_than_widen() -> None:
    """Every term has to match, so a second word can only cut the list."""
    broad = k.search("download")
    narrow = k.search("download music")
    assert len(narrow) < len(broad)
    assert narrow
    assert {a.action_id for a in narrow} <= {a.action_id for a in broad}


def test_search_is_case_insensitive_and_blank_matches_everything() -> None:
    """The palette matches before the operator finishes typing."""
    assert k.search("") == k.all_actions()
    assert k.search("   ") == k.all_actions()
    assert k.search("CLEANUP") == k.search("cleanup")
    assert k.search("no-such-thing-anywhere") == ()


def test_search_agrees_with_the_matching_rule() -> None:
    """The result set is exactly the entries whose text holds every term."""
    terms = ("shot", "qc")
    hits = k.search(" ".join(terms))
    for action in k.all_actions():
        expected = all(term in _haystack(action) for term in terms)
        assert (action in hits) is expected, action.action_id


def test_refused_entries_are_policy_blocked_and_distinct() -> None:
    """The H3 family is visible, explained, and never runnable."""
    refused = [a for a in k.all_actions() if a.tier is RiskTier.REFUSED]
    assert [a.target for a in refused] == [
        "download-h3",
        "queue-h3",
        "farm-h3",
        "stitch-h3",
    ]
    assert len({a.action_id for a in refused}) == 4
    assert sum(1 for a in k.all_actions() if not a.is_runnable()) == len(refused)
    for action in refused:
        assert not action.is_runnable()
        assert "MiniMax H3" in action.refuse_reason
        assert action.confirm is ConfirmKind.NONE
        assert action.params == ()
        assert action.guards == ()


def test_only_the_refused_entries_carry_a_refuse_reason() -> None:
    """A reason with no refusal, or a refusal with no reason, is a defect."""
    for action in k.all_actions():
        if action.tier is RiskTier.REFUSED:
            assert action.refuse_reason, action.action_id
        else:
            assert not action.refuse_reason, action.action_id


def test_only_the_token_tiers_ask_for_a_literal() -> None:
    """HEAVY and DESTRUCTIVE carry a token; nothing else does."""
    for action in k.all_actions():
        if action.tier.requires_token():
            assert action.confirm is not ConfirmKind.NONE, action.action_id
            assert action.confirm.token()
        else:
            assert action.confirm is ConfirmKind.NONE, action.action_id


def test_the_verbs_that_call_require_heavy_confirm_are_heavy() -> None:
    """The source prompts for ``yes`` on exactly these catalog entries."""
    for action_id in (
        "stack.start",
        "stack.restart",
        "stack.setup",
        "stack.update_stack",
        "sidecars.blender_install",
        "models.reset_hf_partials",
        "sidecars.agent_model_run",
    ):
        action = k.action_by_id(action_id)
        assert action is not None
        assert action.tier is RiskTier.HEAVY, action_id
        assert action.confirm is ConfirmKind.YES, action_id


@pytest.mark.parametrize("verb", ["download-models", "download-music", "download-llm"])
def test_every_download_is_heavy_because_it_egresses_the_link(verb: str) -> None:
    """A pack pull needs the typed token before any bytes move.

    Args:
        verb: The download verb to check.
    """
    action = next(
        a
        for a in k.all_actions()
        if a.target == verb and a.runner is RunnerKind.MANAGE
    )
    assert action.tier is RiskTier.HEAVY
    assert action.confirm is ConfirmKind.YES


def test_the_gpu_and_bulk_launches_are_guarded_by_the_headroom_floor() -> None:
    """The heaviest launches block on the floors the CLI blocks on."""
    for action_id in ("stack.start", "stack.restart", "models.download_models"):
        action = k.action_by_id(action_id)
        assert action is not None
        assert Guard.HEADROOM_OK in action.guards, action_id


def test_cleanup_is_the_volume_delete() -> None:
    """``cleanup`` needs the DELETE literal and keeps the output dir."""
    action = k.action_by_id("disk.cleanup")
    assert action is not None
    assert action.tier is RiskTier.DESTRUCTIVE
    assert action.confirm is ConfirmKind.DELETE
    assert action.confirm.token() == "DELETE"


def test_reclaim_plan_and_apply_are_separate_entries() -> None:
    """The plan twin reports; the apply twin deletes behind the DELETE token."""
    plan = k.action_by_id("disk.reap_plan")
    apply_plan = k.action_by_id("disk.reap_apply")
    assert plan is not None and apply_plan is not None
    assert plan.tier is RiskTier.READ
    assert Guard.DISK_PLAN_ONLY in plan.guards
    assert plan.confirm is ConfirmKind.NONE
    assert "--plan" in plan.fixed_args
    assert apply_plan.tier is RiskTier.DESTRUCTIVE
    assert apply_plan.confirm is ConfirmKind.DELETE
    assert Guard.NO_HF_DOWNLOAD in apply_plan.guards
    assert "--plan" not in apply_plan.fixed_args
    assert "--apply" in apply_plan.fixed_args
    wizard_plan = k.action_by_id("disk.wizard_plan")
    wizard_json = k.action_by_id("disk.wizard_json")
    wizard_apply = k.action_by_id("disk.wizard_apply")
    assert wizard_plan is not None and wizard_json is not None
    assert wizard_apply is not None
    assert Guard.DISK_PLAN_ONLY in wizard_plan.guards
    assert Guard.DISK_PLAN_ONLY in wizard_json.guards
    assert Guard.NO_HF_DOWNLOAD in wizard_apply.guards
    assert wizard_apply.tier is RiskTier.DESTRUCTIVE


def test_deletes_under_the_model_cache_wait_for_the_download_to_end() -> None:
    """Nothing removes files under MODELS_DIR while a pull is live."""
    for action_id in (
        "models.clear_hf_locks",
        "models.reset_hf_partials",
        "disk.reap_apply",
        "disk.wizard_apply",
    ):
        action = k.action_by_id(action_id)
        assert action is not None
        assert Guard.NO_HF_DOWNLOAD in action.guards, action_id


def test_every_comfyui_queue_needs_a_running_idle_stack() -> None:
    """An action that POSTs to ComfyUI waits for the stack, queue, and desk."""
    for action_id in (
        "film.print_shot",
        "film.film_resume",
        "lanes.album_render",
        "occupancy.enter_klein",
    ):
        action = k.action_by_id(action_id)
        assert action is not None
        assert Guard.STACK_RUNNING in action.guards, action_id
        assert Guard.QUEUE_IDLE in action.guards, action_id
        assert Guard.OCCUPANCY_IDLE in action.guards, action_id


def test_nvenc_and_blender_work_refuse_while_compose_is_up() -> None:
    """The XOR rule is a guard, not a surprise failure mid-run."""
    for action_id in (
        "film.film_proxies",
        "film.nvenc_preview",
        "sidecars.export_guides",
        "sidecars.blender_stills",
        "sidecars.house_views",
    ):
        action = k.action_by_id(action_id)
        assert action is not None
        assert Guard.STACK_STOPPED in action.guards, action_id


def test_gpu_sidecar_work_waits_for_the_desk_or_the_queue() -> None:
    """The one GPU is claimed by one workload at a time."""
    for action_id in (
        "sidecars.agent_model_run",
        "sidecars.blender",
        "sidecars.blender_mcp_tools",
    ):
        action = k.action_by_id(action_id)
        assert action is not None
        claimed = (
            Guard.QUEUE_IDLE in action.guards
            or Guard.OCCUPANCY_PARKED in action.guards
        )
        assert claimed, action_id


def test_a_child_that_wants_a_yes_flag_declares_it_as_an_answer() -> None:
    """``--yes`` is an operator answer, never a baked-in argument."""
    for action_id in (
        "occupancy.enter_blender_desk",
        "film.concat_shots",
        "stack.update_stack",
        "film.nvenc_preview",
        "film.film_proxies",
        "disk.reap_apply",
    ):
        action = k.action_by_id(action_id)
        assert action is not None
        param = next(p for p in action.params if p.name == "confirm_yes")
        assert param.kind is ParamKind.FLAG, action_id
        assert param.flag == "--yes", action_id
        assert param.required is False, action_id
        assert "--yes" not in action.fixed_args, action_id


def test_read_only_entries_never_change_state() -> None:
    """The read tier carries no token and no apply flag."""
    for action in k.all_actions():
        if action.tier is RiskTier.READ:
            assert action.confirm is ConfirmKind.NONE, action.action_id
            assert "--apply" not in action.fixed_args, action.action_id


def test_pack_status_probes_are_read_only_utility_calls() -> None:
    """Every model pack can be asked what it has, without pulling anything."""
    probes = [
        action
        for action in k.all_actions()
        if action.runner is RunnerKind.UTILITY
        and action.target.startswith("download-")
    ]
    assert {action.target for action in probes} == set(_EXPECTED_PACK_PROBES)
    for action in probes:
        assert action.tier is RiskTier.READ, action.action_id
        assert action.fixed_args == ("status",), action.action_id


def test_the_console_never_offers_the_arbitrary_command_wrapper() -> None:
    """``download-limit wrap`` takes a command line, so it stays internal."""
    for action in k.all_actions():
        assert "wrap" not in action.fixed_args, action.action_id
        assert "bash -c" not in " ".join(action.fixed_args), action.action_id


def test_build_argv_composes_the_command_the_operator_reviewed() -> None:
    """A catalog entry plus answers is the exact argv the runner will exec."""
    action = k.action_by_id("film.print_shot")
    assert action is not None
    argv = build_argv(action, {"film": "go-see", "shot_id": "07", "quality": "high"})
    assert argv == ("print-shot", "go-see", "07", "--quality", "high")


def test_build_argv_appends_the_typed_yes_only_when_answered() -> None:
    """The optional confirm flag appears only after the operator ticks it."""
    action = k.action_by_id("occupancy.enter_wan")
    assert action is not None
    assert build_argv(action, {"confirm_yes": "no"}) == ("occupancy", "enter", "wan")
    assert build_argv(action, {"confirm_yes": "yes"}) == (
        "occupancy",
        "enter",
        "wan",
        "--yes",
    )


def test_choice_parameters_cannot_be_smuggled_past_the_menu() -> None:
    """A promoted graph lands in a real lane or nowhere."""
    action = k.action_by_id("lanes.promote_workflow")
    assert action is not None
    answers = {
        "source": "workflows/_user/scratch.json",
        "lane": "film",
        "graph_id": "opening-beat",
    }
    assert build_argv(action, answers) == (
        "promote-workflow",
        "--from",
        "workflows/_user/scratch.json",
        "--lane",
        "film",
        "--id",
        "opening-beat",
    )
    with pytest.raises(ValueError, match="not one of"):
        build_argv(action, {**answers, "lane": "../etc"})


def test_int_parameters_are_bounded() -> None:
    """A log tail cannot be typed into absurdity."""
    logs = k.action_by_id("stack.logs")
    assert logs is not None
    assert build_argv(logs, {"tail": "50"}) == ("logs", "--tail", "50")
    with pytest.raises(ValueError, match="outside 1..100000"):
        build_argv(logs, {"tail": "9999999"})

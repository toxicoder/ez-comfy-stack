"""The guard fails closed, so a remote operator cannot take the box down.

These tests drive :func:`tui.guard.evaluate` branch by branch from a snapshot
they build themselves: the guard reads nothing, so a :class:`Health` literal is
the whole input. The behaviour that matters is that an unknown reading blocks
with ``stale`` set, that the machine floors match ``scripts/lib/safety.sh``,
and that a refused or headroom-bound action never reaches the runner.
"""

from __future__ import annotations

import pytest

from tui import guard
from tui.contract import (
    UNMEASURED,
    ActionSpec,
    ConfirmKind,
    Group,
    Guard,
    Health,
    MIN_DISK_FREE_GIB,
    MIN_HOST_FREE_GIB,
    RiskTier,
    RunnerKind,
)

HEAVY_GUARDS: tuple[Guard, ...] = (
    Guard.STACK_RUNNING,
    Guard.HEADROOM_OK,
    Guard.QUEUE_IDLE,
    Guard.OCCUPANCY_IDLE,
    Guard.NO_HF_DOWNLOAD,
    Guard.NO_LLM_SIDECAR,
    Guard.PACKS_READY,
)
"""The guards a heavy stack start has to prove, in the order the detail pane lists them."""


def _healthy() -> Health:
    """Build the snapshot of a machine that is ready for a heavy job.

    Returns:
        A :class:`Health` where every reading is known and every floor is clear.
    """
    return Health(
        stack_state="running",
        attention="kitchen",
        host_free_gib=64,
        disk_free_gib=120,
        occupancy_mode="idle",
        occupancy_orphaned=False,
        parked=True,
        queue="idle",
        llm_live=False,
        shaping=True,
        shaping_mbps=850,
        downloads_running=False,
        packs=(("image", True), ("wan", True), ("music", True)),
        errors=(),
    )


def _action(
    guards: tuple[Guard, ...] = HEAVY_GUARDS,
    **overrides: object,
) -> ActionSpec:
    """Build an action, overriding only what a test cares about.

    Args:
        guards: Preconditions the action declares.
        **overrides: Fields to replace on the default action.

    Returns:
        A catalog entry for guard tests.
    """
    base: dict[str, object] = {
        "action_id": "stack.start",
        "title": "Start the studio stack",
        "group": Group.STACK,
        "summary": "Start ComfyUI detached.",
        "runner": RunnerKind.MANAGE,
        "target": "start",
        "tier": RiskTier.HEAVY,
        "confirm": ConfirmKind.YES,
        "guards": guards,
    }
    base.update(overrides)
    return ActionSpec(**base)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# The happy path and the machine floors
# ---------------------------------------------------------------------------


def test_a_healthy_machine_allows_a_heavy_launch() -> None:
    """Every guard green means the console offers the heavy verb with no note."""
    verdict = guard.evaluate(_action(), _healthy())
    assert verdict.allowed
    assert verdict.reasons == ()
    assert verdict.guards_failed == ()
    assert not verdict.stale


@pytest.mark.parametrize("free_ram", [MIN_HOST_FREE_GIB, MIN_HOST_FREE_GIB + 1])
def test_free_ram_at_or_above_the_floor_is_green(free_ram: int) -> None:
    """The console blocks at the same number ``manage.sh start`` blocks at."""
    health = _healthy()
    health["host_free_gib"] = free_ram
    assert guard.evaluate(_action(), health).allowed


def test_one_gib_of_host_ram_below_the_floor_blocks_a_heavy_launch() -> None:
    """27 GiB free is a refusal, and the reason quotes the number the operator sees."""
    health = _healthy()
    health["host_free_gib"] = MIN_HOST_FREE_GIB - 1
    verdict = guard.evaluate(_action(), health)
    assert not verdict.allowed
    assert verdict.guards_failed == (Guard.HEADROOM_OK,)
    assert not verdict.stale
    assert len(verdict.reasons) == 1
    assert str(MIN_HOST_FREE_GIB - 1) in verdict.reasons[0]
    assert str(MIN_HOST_FREE_GIB) in verdict.reasons[0]


@pytest.mark.parametrize("free_disk", [MIN_DISK_FREE_GIB, MIN_DISK_FREE_GIB + 1])
def test_free_disk_at_or_above_the_floor_is_green(free_disk: int) -> None:
    """The models volume floor matches the shell's ``MIN_DISK_FREE_GIB``."""
    health = _healthy()
    health["disk_free_gib"] = free_disk
    assert guard.evaluate(_action(), health).allowed


def test_one_gib_of_disk_below_the_floor_blocks_a_heavy_launch() -> None:
    """39 GiB free on the models volume is a refusal, not a warning."""
    health = _healthy()
    health["disk_free_gib"] = MIN_DISK_FREE_GIB - 1
    verdict = guard.evaluate(_action(), health)
    assert not verdict.allowed
    assert verdict.guards_failed == (Guard.HEADROOM_OK,)
    assert not verdict.stale
    assert str(MIN_DISK_FREE_GIB - 1) in verdict.reasons[0]


def test_both_floors_broken_reports_the_memory_shortfall_first() -> None:
    """One guard is one sentence: RAM is the lockout risk, so it leads."""
    health = _healthy()
    health["host_free_gib"] = MIN_HOST_FREE_GIB - 1
    health["disk_free_gib"] = MIN_DISK_FREE_GIB - 1
    verdict = guard.evaluate(_action(), health)
    assert len(verdict.reasons) == 1
    assert verdict.guards_failed == (Guard.HEADROOM_OK,)
    assert "host RAM" in verdict.reasons[0]


# ---------------------------------------------------------------------------
# Unknown readings fail closed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("sentinel", [UNMEASURED, -1, -99])
def test_an_unmeasurable_ram_reading_blocks_and_is_stale(sentinel: int) -> None:
    """Unknown RAM is never read as zero GiB, and never as enough."""
    health = _healthy()
    health["host_free_gib"] = sentinel
    verdict = guard.evaluate(_action(), health)
    assert not verdict.allowed
    assert verdict.stale
    assert verdict.guards_failed == (Guard.HEADROOM_OK,)
    assert "could not be read" in verdict.reasons[0]


@pytest.mark.parametrize("sentinel", [UNMEASURED, -1, -99])
def test_an_unmeasurable_disk_reading_blocks_and_is_stale(sentinel: int) -> None:
    """An unmounted models volume blocks a start rather than implying free space."""
    health = _healthy()
    health["disk_free_gib"] = sentinel
    verdict = guard.evaluate(_action(), health)
    assert not verdict.allowed
    assert verdict.stale
    assert verdict.guards_failed == (Guard.HEADROOM_OK,)


@pytest.mark.parametrize("state", ["unknown", "unmeasured", "", "  ", "BOGUS"])
def test_an_unreadable_stack_state_blocks_both_stack_guards(state: str) -> None:
    """A compose state nobody could read proves neither up nor down."""
    health = _healthy()
    health["stack_state"] = state
    running = guard.evaluate(_action(guards=(Guard.STACK_RUNNING,)), health)
    stopped = guard.evaluate(_action(guards=(Guard.STACK_STOPPED,)), health)
    assert not running.allowed and running.stale
    assert not stopped.allowed and stopped.stale
    assert running.guards_failed == (Guard.STACK_RUNNING,)
    assert stopped.guards_failed == (Guard.STACK_STOPPED,)


def test_a_stopped_stack_satisfies_only_the_stopped_guard() -> None:
    """One state string satisfies exactly one of the two stack guards."""
    health = _healthy()
    health["stack_state"] = "stopped"
    assert not guard.evaluate(_action(guards=(Guard.STACK_RUNNING,)), health).allowed
    assert guard.evaluate(_action(guards=(Guard.STACK_STOPPED,)), health).allowed


def test_a_present_stack_is_not_running_but_is_down() -> None:
    """Containers that exist without running count as down, not unknown."""
    health = _healthy()
    health["stack_state"] = "present"
    assert guard.evaluate(_action(guards=(Guard.STACK_STOPPED,)), health).allowed
    running = guard.evaluate(_action(guards=(Guard.STACK_RUNNING,)), health)
    assert not running.allowed
    assert not running.stale


@pytest.mark.parametrize("mode", ["unknown", "unmeasured", "", " Unknown "])
def test_an_unreadable_occupancy_mode_blocks_the_desk_guards(mode: str) -> None:
    """An unreadable desk is not idle and is not parked."""
    health = _healthy()
    health["occupancy_mode"] = mode
    health["parked"] = False
    idle = guard.evaluate(_action(guards=(Guard.OCCUPANCY_IDLE,)), health)
    parked = guard.evaluate(_action(guards=(Guard.OCCUPANCY_PARKED,)), health)
    assert not idle.allowed and idle.stale
    assert not parked.allowed and parked.stale
    assert parked.guards_failed == (Guard.OCCUPANCY_PARKED,)


def test_a_occupied_desk_blocks_without_being_stale() -> None:
    """A desk in a heavy mode is a real reading, so the verdict is fresh."""
    health = _healthy()
    health["occupancy_mode"] = "wan"
    verdict = guard.evaluate(_action(guards=(Guard.OCCUPANCY_IDLE,)), health)
    assert not verdict.allowed
    assert not verdict.stale
    assert verdict.guards_failed == (Guard.OCCUPANCY_IDLE,)


def _desk(
    mode: str,
    *,
    orphaned: bool,
    stack_state: str = "stopped",
    parked: bool = False,
    llm_live: bool = False,
) -> Health:
    """Build the snapshot of a machine holding one desk record.

    Args:
        mode: Recorded occupancy mode.
        orphaned: Whether the read model found no live sidecar behind it.
        stack_state: Compose state to report.
        parked: Whether the record says Comfy was parked for the desk.
        llm_live: What the sidecar reading says.

    Returns:
        A :class:`Health` carrying that desk record and nothing else odd.
    """
    health = _healthy()
    health["occupancy_mode"] = mode
    health["occupancy_orphaned"] = orphaned
    health["stack_state"] = stack_state
    health["parked"] = parked
    health["llm_live"] = llm_live
    return health


@pytest.mark.parametrize("mode", ["blender-desk", "llm-desk"])
def test_an_orphaned_desk_record_does_not_block_a_verb(mode: str) -> None:
    """Issues #380 / #381 for the console: nobody is at that desk.

    A sidecar killed outright, or a host reboot, leaves ``blender-desk`` or
    ``llm-desk`` on disk with dead PIDs. The recorded mode alone must not keep
    the operator from starting a heavy job or a sidecar dump.
    """
    health = _desk(mode, orphaned=True)
    for member in (Guard.OCCUPANCY_IDLE, Guard.OCCUPANCY_PARKED, Guard.NO_LLM_SIDECAR):
        verdict = guard.evaluate(_action(guards=(member,)), health)
        assert verdict.allowed, f"{member} blocked an orphaned {mode}: {verdict.reasons}"


@pytest.mark.parametrize("mode", ["blender-desk", "llm-desk"])
def test_a_live_desk_record_still_blocks(mode: str) -> None:
    """The same record with a live sidecar is a real GPU claim."""
    health = _desk(mode, orphaned=False)
    verdict = guard.evaluate(_action(guards=(Guard.OCCUPANCY_IDLE,)), health)
    assert not verdict.allowed
    assert not verdict.stale
    assert verdict.guards_failed == (Guard.OCCUPANCY_IDLE,)
    parked = guard.evaluate(_action(guards=(Guard.OCCUPANCY_PARKED,)), health)
    assert not parked.allowed and not parked.stale


def test_a_live_llm_sidecar_blocks_after_the_desk_releases() -> None:
    """Releasing an orphan is not the same as waving a running sidecar through."""
    orphaned = _desk("llm-desk", orphaned=True, llm_live=True)
    assert guard.evaluate(
        _action(guards=(Guard.NO_LLM_SIDECAR,)), orphaned
    ).allowed
    live = _desk("llm-desk", orphaned=False, llm_live=True)
    verdict = guard.evaluate(_action(guards=(Guard.NO_LLM_SIDECAR,)), live)
    assert not verdict.allowed and not verdict.stale
    assert verdict.guards_failed == (Guard.NO_LLM_SIDECAR,)


def test_the_orphan_flag_only_releases_a_desk_mode() -> None:
    """A heavy mode, or a sidecar reported live under another mode, still holds."""
    heavy = _desk("klein", orphaned=True)
    verdict = guard.evaluate(_action(guards=(Guard.OCCUPANCY_IDLE,)), heavy)
    assert not verdict.allowed and not verdict.stale
    assert verdict.guards_failed == (Guard.OCCUPANCY_IDLE,)

    other = _desk("blender-desk", orphaned=True, llm_live=True)
    blocked = guard.evaluate(_action(guards=(Guard.NO_LLM_SIDECAR,)), other)
    assert not blocked.allowed
    assert blocked.guards_failed == (Guard.NO_LLM_SIDECAR,)


def test_an_orphaned_desk_keeps_the_park_guard_while_comfy_runs() -> None:
    """The release is about the dead sidecar, not about parking a running Comfy."""
    health = _desk("blender-desk", orphaned=True, stack_state="running")
    verdict = guard.evaluate(_action(guards=(Guard.OCCUPANCY_PARKED,)), health)
    assert not verdict.allowed
    assert not verdict.stale
    assert verdict.guards_failed == (Guard.OCCUPANCY_PARKED,)


@pytest.mark.parametrize("queue", ["unmeasured", "unknown", "", "weird"])
def test_an_unreadable_queue_blocks_while_the_stack_is_up(queue: str) -> None:
    """With Comfy running, an unreachable queue is not assumed idle."""
    health = _healthy()
    health["queue"] = queue
    verdict = guard.evaluate(_action(guards=(Guard.QUEUE_IDLE,)), health)
    assert not verdict.allowed
    assert verdict.stale
    assert verdict.guards_failed == (Guard.QUEUE_IDLE,)


@pytest.mark.parametrize("state", ["stopped", "present"])
def test_an_unreadable_queue_is_idle_while_the_stack_is_down(state: str) -> None:
    """Nothing can be queued against a stack that is not running."""
    health = _healthy()
    health["stack_state"] = state
    health["queue"] = "unmeasured"
    assert guard.evaluate(_action(guards=(Guard.QUEUE_IDLE,)), health).allowed


def test_a_busy_queue_blocks_without_being_stale() -> None:
    """A job in flight is a fact, and it blocks the occupancy desk changing mode."""
    health = _healthy()
    health["queue"] = "busy"
    verdict = guard.evaluate(_action(guards=(Guard.QUEUE_IDLE,)), health)
    assert not verdict.allowed
    assert not verdict.stale
    assert Guard.QUEUE_IDLE in verdict.guards_failed


def test_an_empty_pack_table_is_unknown() -> None:
    """No pack reported anything, so readiness cannot be claimed."""
    health = _healthy()
    health["packs"] = ()
    verdict = guard.evaluate(_action(guards=(Guard.PACKS_READY,)), health)
    assert not verdict.allowed
    assert verdict.stale
    assert verdict.guards_failed == (Guard.PACKS_READY,)


def test_a_pack_that_is_not_downloaded_names_itself() -> None:
    """The operator is told which pack is missing, not just that one is."""
    health = _healthy()
    health["packs"] = (("image", True), ("wan", False), ("music", False))
    verdict = guard.evaluate(_action(guards=(Guard.PACKS_READY,)), health)
    assert not verdict.allowed
    assert not verdict.stale
    assert "wan" in verdict.reasons[0]
    assert "music" in verdict.reasons[0]
    assert "image" not in verdict.reasons[0]


def test_a_live_download_or_sidecar_blocks_freshly() -> None:
    """A running hf pull and a GPU-holding sidecar are both real readings."""
    downloading = _healthy()
    downloading["downloads_running"] = True
    verdict = guard.evaluate(_action(guards=(Guard.NO_HF_DOWNLOAD,)), downloading)
    assert not verdict.allowed and not verdict.stale
    assert verdict.guards_failed == (Guard.NO_HF_DOWNLOAD,)

    busy = _healthy()
    busy["llm_live"] = True
    verdict = guard.evaluate(_action(guards=(Guard.NO_LLM_SIDECAR,)), busy)
    assert not verdict.allowed and not verdict.stale
    assert verdict.guards_failed == (Guard.NO_LLM_SIDECAR,)


def test_parked_satisfies_the_park_guard() -> None:
    """A parked stack is what lets a sidecar take the GPU."""
    health = _healthy()
    assert guard.evaluate(_action(guards=(Guard.OCCUPANCY_PARKED,)), health).allowed
    health["parked"] = False
    verdict = guard.evaluate(_action(guards=(Guard.OCCUPANCY_PARKED,)), health)
    assert not verdict.allowed
    assert not verdict.stale


def test_disk_plan_only_is_a_policy_statement_not_a_reading() -> None:
    """Plan mode is carried by the tier and the token, so this guard is always green."""
    verdict = guard.evaluate(_action(guards=(Guard.DISK_PLAN_ONLY,)), _healthy())
    assert verdict.allowed
    assert verdict.reasons == ()


@pytest.mark.parametrize("member", list(Guard))
def test_every_guard_can_be_evaluated_on_a_healthy_machine(member: Guard) -> None:
    """No guard raises, and every one of them explains a refusal in a sentence."""
    health = _healthy()
    health["packs"] = (("image", False),)
    verdict = guard.evaluate(_action(guards=(member,)), health)
    assert verdict.allowed or verdict.reasons
    for reason in verdict.reasons:
        assert reason[0].islower()
        assert len(reason) > 12
    if verdict.stale:
        assert not verdict.allowed


# ---------------------------------------------------------------------------
# Tier and policy behaviour
# ---------------------------------------------------------------------------


def test_a_read_is_never_held_to_the_machine_floors() -> None:
    """A starved box is still browsable: a read is blocked by guards only."""
    starving = _healthy()
    starving["host_free_gib"] = MIN_HOST_FREE_GIB - 1
    starving["disk_free_gib"] = MIN_DISK_FREE_GIB - 1
    read = _action(
        guards=(Guard.HEADROOM_OK, Guard.STACK_RUNNING),
        action_id="stack.status",
        title="Show status",
        tier=RiskTier.READ,
        confirm=ConfirmKind.NONE,
    )
    verdict = guard.evaluate(read, starving)
    assert verdict.allowed
    assert Guard.HEADROOM_OK not in verdict.guards_failed
    heavy = _action(guards=(Guard.HEADROOM_OK,), tier=RiskTier.HEAVY)
    assert not guard.evaluate(heavy, starving).allowed


def test_a_read_still_answers_to_its_own_guards() -> None:
    """Exempting the floors does not exempt a real precondition."""
    health = _healthy()
    health["stack_state"] = "stopped"
    read = _action(
        guards=(Guard.STACK_RUNNING,),
        action_id="studio.logs",
        title="Tail the log",
        tier=RiskTier.READ,
        confirm=ConfirmKind.NONE,
    )
    verdict = guard.evaluate(read, health)
    assert not verdict.allowed
    assert verdict.guards_failed == (Guard.STACK_RUNNING,)


def test_a_refused_action_is_blocked_by_policy_whatever_the_machine_says() -> None:
    """A catalogued refusal never becomes runnable because the box is healthy."""
    refused = _action(
        guards=(),
        action_id="models.download_h3",
        title="Download MiniMax H3",
        group=Group.MODELS,
        tier=RiskTier.REFUSED,
        refuse_reason="MiniMax H3 is outside the US-safe catalog",
    )
    verdict = guard.evaluate(refused, _healthy())
    assert not verdict.allowed
    assert verdict.reasons == ("MiniMax H3 is outside the US-safe catalog",)
    assert verdict.guards_failed == ()
    assert not verdict.stale


def test_a_refusal_without_a_reason_still_says_why() -> None:
    """A misconfigured entry cannot produce a bare, unexplained no."""
    refused = _action(
        guards=(),
        tier=RiskTier.REFUSED,
        refuse_reason="",
    )
    verdict = guard.evaluate(refused, _healthy())
    assert not verdict.allowed
    assert len(verdict.reasons) == 1
    assert verdict.reasons[0]


def test_an_action_with_no_guards_is_allowed() -> None:
    """A plain write action needs no proof beyond being runnable."""
    write = _action(guards=(), tier=RiskTier.WRITE, confirm=ConfirmKind.NONE)
    verdict = guard.evaluate(write, _healthy())
    assert verdict.allowed
    assert not verdict.stale


def test_blockers_come_back_in_declaration_order() -> None:
    """The detail pane lists what to fix in the order the action declared it."""
    health = _healthy()
    health["stack_state"] = "stopped"
    health["host_free_gib"] = 1
    health["queue"] = "busy"
    health["downloads_running"] = True
    verdict = guard.evaluate(_action(), health)
    assert verdict.guards_failed == (
        Guard.STACK_RUNNING,
        Guard.HEADROOM_OK,
        Guard.QUEUE_IDLE,
        Guard.NO_HF_DOWNLOAD,
    )
    assert len(verdict.reasons) == 4
    assert not verdict.stale


def test_a_mixed_verdict_is_stale_when_any_blocker_was_unknown() -> None:
    """One unreadable reading among several makes the whole verdict suspect."""
    health = _healthy()
    health["queue"] = "busy"
    health["host_free_gib"] = UNMEASURED
    verdict = guard.evaluate(_action(), health)
    assert not verdict.allowed
    assert verdict.stale
    assert Guard.HEADROOM_OK in verdict.guards_failed


# ---------------------------------------------------------------------------
# Batch evaluation and the dashboard summary
# ---------------------------------------------------------------------------


def test_evaluate_many_keeps_the_order_it_was_given() -> None:
    """A list view renders verdicts in catalog order, not sorted by allowed."""
    actions = (
        _action(action_id="stack.stop", title="Stop"),
        _action(action_id="stack.start", title="Start"),
        _action(action_id="stack.restart", title="Restart"),
    )
    verdicts = guard.evaluate_many(actions, _healthy())
    assert list(verdicts) == ["stack.stop", "stack.start", "stack.restart"]
    assert all(verdict.allowed for verdict in verdicts.values())


def test_evaluate_many_marks_only_the_blocked_rows() -> None:
    """Each row is judged on its own guards."""
    health = _healthy()
    health["stack_state"] = "stopped"
    actions = (
        _action(action_id="stack.stop", title="Stop", guards=(Guard.STACK_RUNNING,)),
        _action(
            action_id="stack.update",
            title="Update",
            guards=(Guard.STACK_STOPPED,),
        ),
    )
    verdicts = guard.evaluate_many(actions, health)
    assert not verdicts["stack.stop"].allowed
    assert verdicts["stack.update"].allowed


def test_evaluate_many_over_an_empty_list_is_empty() -> None:
    """A filtered group with no rows yields no verdicts."""
    assert guard.evaluate_many((), _healthy()) == {}


def test_blocking_reasons_is_empty_on_a_ready_machine() -> None:
    """Nothing on the dashboard banner when the box is ready for heavy work."""
    assert guard.blocking_reasons(_healthy()) == ()


def test_blocking_reasons_names_every_machine_blocker() -> None:
    """The banner lists one sentence per machine-level guard that is not green."""
    health = _healthy()
    health["host_free_gib"] = 4
    health["queue"] = "busy"
    health["occupancy_mode"] = "klein"
    health["downloads_running"] = True
    health["llm_live"] = True
    health["packs"] = (("image", False),)
    reasons = guard.blocking_reasons(health)
    assert len(reasons) == 6
    assert all(reason[0].islower() for reason in reasons)


def test_blocking_reasons_survives_a_snapshot_that_knows_nothing() -> None:
    """A cold console shows a banner instead of an empty, reassuring dashboard."""
    cold = _healthy()
    cold["host_free_gib"] = UNMEASURED
    cold["disk_free_gib"] = UNMEASURED
    cold["queue"] = "unmeasured"
    cold["occupancy_mode"] = "unknown"
    cold["packs"] = ()
    reasons = guard.blocking_reasons(cold)
    assert len(reasons) == 4
    assert all(
        "could not be read" in reason or "no model pack" in reason
        for reason in reasons
    )

"""GO / BLOCK for one action, decided from one health snapshot.

This is the layer that stands between a remote operator's keystroke and a
command that can lock them out of the box. It reads nothing: every input is
already in the :class:`~tui.contract.Health` snapshot the read model produced,
which makes the whole gate a pure function the suite can drive branch by
branch.

The rule it is built on is fail closed. :data:`~tui.contract.UNMEASURED`,
``"unknown"``, and ``"unmeasured"`` all mean "nobody could read this", and a
guard that cannot read its input returns a blocking verdict marked ``stale``
rather than defaulting to green. That mirrors the shell layer, where
``host_free_mem_gib`` reports 0 rather than guessing and
``comfy_queue_busy`` refuses to call a queue it cannot reach idle.

Machine floors match ``check_host_headroom`` in ``scripts/lib/safety.sh``:
free RAM against :data:`~tui.contract.MIN_HOST_FREE_GIB`, free disk on the
models volume against :data:`~tui.contract.MIN_DISK_FREE_GIB`. The console
never invents a softer number than the CLI enforces.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import NamedTuple

from tui.contract import (
    UNMEASURED,
    ActionSpec,
    Guard,
    GuardVerdict,
    Health,
    MIN_DISK_FREE_GIB,
    MIN_HOST_FREE_GIB,
    RiskTier,
)

_IDLE = "idle"
"""Mode and queue value that mean nothing heavy is in flight."""

_BUSY = "busy"
"""Queue value that means a job is in flight."""

_RUNNING = "running"
"""Stack state that means Compose is up."""

_DOWN_STATES: frozenset[str] = frozenset({"stopped", "present"})
"""Stack states that prove the stack is not running."""

_UNKNOWN_STRINGS: frozenset[str] = frozenset({"", "unknown", "unmeasured"})
"""Text readings that mean the probe could not establish a value."""

_READ_EXEMPT_GUARDS: frozenset[Guard] = frozenset({Guard.HEADROOM_OK})
"""Guards a :attr:`~tui.contract.RiskTier.READ` action is never held to.

Observing something never needs headroom: a read that is refused because a
download filled the disk teaches the operator nothing about the disk.
"""

_MACHINE_GUARDS: tuple[Guard, ...] = (
    Guard.HEADROOM_OK,
    Guard.QUEUE_IDLE,
    Guard.OCCUPANCY_IDLE,
    Guard.NO_HF_DOWNLOAD,
    Guard.NO_LLM_SIDECAR,
    Guard.PACKS_READY,
)
"""The guards that describe the machine rather than one action, in dashboard order."""

_RAM_UNKNOWN = "free host RAM could not be read, so headroom cannot be proven"
"""Block sentence for an unmeasurable free-RAM reading."""

_DISK_UNKNOWN = (
    "free disk on the models volume could not be read, so headroom cannot be proven"
)
"""Block sentence for an unmeasurable free-disk reading."""

_PACKS_UNKNOWN = "no model pack reported a reading, so readiness is unknown"
"""Block sentence for a pack table with nothing in it."""

_UNKNOWN_REASONS: dict[Guard, str] = {
    Guard.STACK_RUNNING: "the compose state could not be read",
    Guard.STACK_STOPPED: "the compose state could not be read",
    Guard.QUEUE_IDLE: "the ComfyUI queue could not be read",
    Guard.OCCUPANCY_IDLE: "the occupancy desk mode could not be read",
    Guard.OCCUPANCY_PARKED: "the occupancy desk mode could not be read",
    Guard.PACKS_READY: _PACKS_UNKNOWN,
}
"""Block sentence per guard, used when the reading is unknown rather than bad."""


class _Check(NamedTuple):
    """Outcome of one guard against one snapshot.

    Attributes:
        blocked: True when the guard refuses.
        stale: True when the refusal came from a reading that could not be taken.
        reason: Operator-facing sentence; empty when the guard is green.
    """

    blocked: bool
    stale: bool
    reason: str


_CLEAN = _Check(blocked=False, stale=False, reason="")
"""The verdict every satisfied guard returns."""


def _unknown_int(value: int) -> bool:
    """Whether an integer reading is one nobody could take.

    Args:
        value: The reading.

    Returns:
        True for :data:`~tui.contract.UNMEASURED` and for any other negative,
        which no real measurement can produce.
    """
    return value <= UNMEASURED


def _unknown_text(value: str) -> bool:
    """Whether a text reading is one nobody could take.

    Args:
        value: The reading.

    Returns:
        True when the text is empty or names the unknown sentinel.
    """
    return value.strip().lower() in _UNKNOWN_STRINGS


def _check_headroom(health: Health) -> _Check:
    """Compare free RAM and free disk against the shell's floors.

    Args:
        health: The snapshot.

    Returns:
        A blocking verdict when either reading is unknown or sits under its
        floor, matching ``check_host_headroom``.
    """
    free_ram = health["host_free_gib"]
    free_disk = health["disk_free_gib"]
    if _unknown_int(free_ram):
        return _Check(blocked=True, stale=True, reason=_RAM_UNKNOWN)
    if _unknown_int(free_disk):
        return _Check(blocked=True, stale=True, reason=_DISK_UNKNOWN)
    if free_ram < MIN_HOST_FREE_GIB:
        return _Check(
            blocked=True,
            stale=False,
            reason=(
                f"only {free_ram} GiB of host RAM is free; "
                f"{MIN_HOST_FREE_GIB} GiB is needed before a heavy job starts"
            ),
        )
    if free_disk < MIN_DISK_FREE_GIB:
        return _Check(
            blocked=True,
            stale=False,
            reason=(
                f"only {free_disk} GiB is free on the models volume; "
                f"{MIN_DISK_FREE_GIB} GiB must stay free"
            ),
        )
    return _CLEAN


def _check_queue(health: Health) -> _Check:
    """Decide whether the ComfyUI queue is idle.

    An unreadable queue counts as idle only when the stack is provably not
    running, because then nothing can be queued; that is the allowance
    :attr:`~tui.contract.Guard.QUEUE_IDLE` documents. With the stack up or its
    state unknown, an unreadable queue blocks.

    Args:
        health: The snapshot.

    Returns:
        The verdict for this guard.
    """
    queue = health["queue"]
    if queue == _IDLE:
        return _CLEAN
    if queue == _BUSY:
        return _Check(blocked=True, stale=False, reason=Guard.QUEUE_IDLE.explain())
    if _unknown_text(queue) and health["stack_state"] in _DOWN_STATES:
        return _CLEAN
    return _Check(
        blocked=True,
        stale=True,
        reason=_UNKNOWN_REASONS[Guard.QUEUE_IDLE],
    )


def _check_packs(health: Health) -> _Check:
    """Decide whether every reported model pack is downloaded.

    Args:
        health: The snapshot.

    Returns:
        A blocking verdict when a pack is missing, or a stale verdict when the
        probe never produced a table at all.
    """
    packs = health["packs"]
    if not packs:
        return _Check(blocked=True, stale=True, reason=_PACKS_UNKNOWN)
    missing = tuple(name for name, ready in packs if not ready)
    if missing:
        return _Check(
            blocked=True,
            stale=False,
            reason=f"{Guard.PACKS_READY.explain()}: {', '.join(missing)}",
        )
    return _CLEAN


def _check(guard: Guard, health: Health) -> _Check:
    """Evaluate one guard against one snapshot.

    Args:
        guard: The precondition to prove.
        health: The snapshot to prove it from.

    Returns:
        The guard's outcome; green only when the reading is known and good.
    """
    if guard is Guard.HEADROOM_OK:
        return _check_headroom(health)
    if guard is Guard.QUEUE_IDLE:
        return _check_queue(health)
    if guard is Guard.PACKS_READY:
        return _check_packs(health)
    if guard is Guard.STACK_RUNNING:
        state = health["stack_state"]
        if state == _RUNNING:
            return _CLEAN
        if state in _DOWN_STATES:
            return _Check(blocked=True, stale=False, reason=guard.explain())
        return _Check(blocked=True, stale=True, reason=_UNKNOWN_REASONS[guard])
    if guard is Guard.STACK_STOPPED:
        state = health["stack_state"]
        if state in _DOWN_STATES:
            return _CLEAN
        if state == _RUNNING:
            return _Check(blocked=True, stale=False, reason=guard.explain())
        return _Check(blocked=True, stale=True, reason=_UNKNOWN_REASONS[guard])
    if guard is Guard.OCCUPANCY_IDLE:
        mode = health["occupancy_mode"]
        if _unknown_text(mode):
            return _Check(blocked=True, stale=True, reason=_UNKNOWN_REASONS[guard])
        if mode != _IDLE:
            return _Check(blocked=True, stale=False, reason=guard.explain())
        return _CLEAN
    if guard is Guard.OCCUPANCY_PARKED:
        if health["parked"]:
            return _CLEAN
        if _unknown_text(health["occupancy_mode"]):
            return _Check(blocked=True, stale=True, reason=_UNKNOWN_REASONS[guard])
        return _Check(blocked=True, stale=False, reason=guard.explain())
    if guard is Guard.NO_HF_DOWNLOAD:
        if health["downloads_running"]:
            return _Check(blocked=True, stale=False, reason=guard.explain())
        return _CLEAN
    if guard is Guard.NO_LLM_SIDECAR:
        if health["llm_live"]:
            return _Check(blocked=True, stale=False, reason=guard.explain())
        return _CLEAN
    # Guard.DISK_PLAN_ONLY is a catalog statement about which tier the apply
    # path belongs to, not a machine reading: Health carries no plan-mode
    # field, and the destructive tier plus the DELETE token carry the gate.
    return _CLEAN


def evaluate(action: ActionSpec, health: Health) -> GuardVerdict:
    """Decide whether one action may be dispatched right now.

    A refused action is blocked by policy whatever the machine says. A
    :attr:`~tui.contract.RiskTier.READ` action is held to its guards only, and
    never to the machine floors: observing the box is always allowed. Every
    other tier must prove each guard it declares, and a guard whose reading is
    unknown blocks with ``stale`` set.

    Args:
        action: The catalog entry.
        health: The snapshot taken by :func:`tui.readmodel.probe_health`.

    Returns:
        The verdict: allowed, the blockers in guard order, which guards failed,
        and whether any of them failed on an unreadable input.
    """
    if not action.is_runnable():
        reason = action.refuse_reason or f"{action.title} is refused by policy"
        return GuardVerdict(allowed=False, reasons=(reason,), guards_failed=())
    reasons: list[str] = []
    failed: list[Guard] = []
    stale = False
    for guard in action.guards:
        if action.tier is RiskTier.READ and guard in _READ_EXEMPT_GUARDS:
            continue
        outcome = _check(guard, health)
        if not outcome.blocked:
            continue
        reasons.append(outcome.reason)
        failed.append(guard)
        stale = stale or outcome.stale
    return GuardVerdict(
        allowed=not failed,
        reasons=tuple(reasons),
        guards_failed=tuple(failed),
        stale=stale,
    )


def evaluate_many(actions: Sequence[ActionSpec], health: Health) -> dict[str, GuardVerdict]:
    """Decide a whole action list in one pass.

    Args:
        actions: Catalog entries to vet, in display order.
        health: The snapshot every action is judged against.

    Returns:
        Verdicts keyed by ``action_id``, in the order the actions were given,
        so a list view can render rows without re-sorting.
    """
    return {action.action_id: evaluate(action, health) for action in actions}


def blocking_reasons(health: Health) -> tuple[str, ...]:
    """Summarise what the machine itself is refusing, for the dashboard banner.

    Args:
        health: The snapshot.

    Returns:
        One sentence per machine-level guard that is not green, in
        :data:`_MACHINE_GUARDS` order; empty when the box is ready.
    """
    reasons: list[str] = []
    for guard in _MACHINE_GUARDS:
        outcome = _check(guard, health)
        if outcome.blocked:
            reasons.append(outcome.reason)
    return tuple(reasons)

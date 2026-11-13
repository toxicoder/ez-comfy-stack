"""Canonical read-side occupancy policy shared by every Python reader.

The GPU is a single-tenant XOR. ``${COMFY_OUTPUT_DIR}/.occupancy.json`` is the
one record of who holds it, and :mod:`scripts.lib.occupancy` (shell) is the only
writer. Before this module each pack re-implemented the mode machine and drifted
from the shell rule, so the same record produced contradictory answers: an
orphaned desk record (sidecar long dead) blocked healthy graphs, while
``generate_clip`` queued a heavy render next to a live 35B sidecar.

Rule this module encodes, mirroring the shell:

* A heavy mode (``klein`` / ``trellis`` / ``wan`` / ``ltx``) is a claim.
* A desk mode (``blender-desk`` / ``llm-desk``) is a claim only while its
  sidecar process is alive. A desk record whose sidecars are all gone is an
  orphan: it names no GPU work and must not block anything.

Liveness is read from ``pids_alive``, which the host writes with ``kill -0``.
Custom nodes run in the Compose container, which has no ``pid: host`` share, so
a PID probe here would test the wrong namespace; a record written by an older
host falls back to "any non-zero PID is live" and stays fail-closed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Mapping

from .json_value import Json, JsonMap

STATE_FILENAME: Final = ".occupancy.json"
"""Occupancy record name inside the operator output directory."""

HEAVY_MODES: Final[tuple[str, ...]] = ("klein", "trellis", "wan", "ltx")
"""Graph families that own the GPU outright."""

DESK_MODES: Final[tuple[str, ...]] = ("blender-desk", "llm-desk")
"""Modes that park Comfy for a host sidecar."""

VALID_MODES: Final[tuple[str, ...]] = ("idle", *DESK_MODES, *HEAVY_MODES)
"""Every mode id the host ``occupancy enter`` accepts."""

UNKNOWN_MODE: Final = "unknown"
"""Effective mode when no record exists yet (first run, pytest)."""

RELEASED_MODE: Final = "idle"
"""Mode an orphaned desk record collapses to for policy purposes."""

HOLDER_PID_KEYS: Final[Mapping[str, tuple[str, ...]]] = {
    "blender-desk": ("blender_pid", "mcp_pid"),
    "llm-desk": ("llm_pid",),
}
"""Which recorded PIDs constitute each desk mode's claim."""

PIDS_ALIVE_KEY: Final = "pids_alive"
"""Host-written per-PID liveness map, keyed by the PID field names."""

MANAGE_TARGET: Final = "bazelisk run //:manage --"
"""Command form docs and operator strings use for a host verb."""


class OccupancyStateError(RuntimeError):
    """An occupancy record exists but cannot be trusted."""


def state_path() -> Path:
    """Locate the occupancy record, the same way the Comfy packs resolve it.

    This is ``ez_common.output_root(default="/outputs")``, which is what
    :func:`ez_dcc.pack.output_directory` resolves to, so the in-canvas gate and
    the host readers cannot end up watching two different files.

    Returns:
        Path to ``.occupancy.json`` (may not exist yet).
    """
    # Deferred: ez_common/__init__ imports this module, so a top-level
    # ``from . import output_root`` would be a cycle.
    from . import output_root

    return output_root(default="/outputs") / STATE_FILENAME


@dataclass(frozen=True)
class Occupancy:
    """One immutable read of the occupancy record.

    Attributes:
        present: Whether a record existed on disk.
        mode: Recorded mode, or ``unknown`` when absent or blank.
        parked: Whether Compose was parked (``POST /free``) for the desk.
        compose: Whether Compose was up when the host wrote the record.
        holder_pids: PIDs that would constitute this mode's claim.
        pids_alive: Host-computed liveness map, or ``None`` when the record
            predates the field and liveness must be assumed from the PIDs.
    """

    present: bool = False
    mode: str = UNKNOWN_MODE
    parked: bool = False
    compose: bool = False
    holder_pids: tuple[tuple[str, int], ...] = field(default_factory=tuple)
    pids_alive: Mapping[str, bool] | None = None

    @property
    def is_desk(self) -> bool:
        """Whether this mode is a host-sidecar desk mode.

        Returns:
            Whether the mode is ``blender-desk`` or ``llm-desk``.
        """
        return self.mode in DESK_MODES

    @property
    def is_heavy(self) -> bool:
        """Whether this mode is a heavy GPU graph family.

        Returns:
            Whether the mode is one of :data:`HEAVY_MODES`.
        """
        return self.mode in HEAVY_MODES

    @property
    def holder_live(self) -> bool:
        """Whether a live process actually backs the recorded claim.

        A zero PID is never alive in any namespace. A non-zero PID is alive
        when the host said so, or - for a record written before ``pids_alive``
        existed - assumed alive so the gate stays fail-closed.

        Returns:
            Whether the recorded holder is live.
        """
        if not self.holder_pids:
            return False
        for name, pid in self.holder_pids:
            if pid <= 0:
                continue
            if self.pids_alive is None:
                return True
            if self.pids_alive.get(name, True):
                return True
        return False

    @property
    def orphaned(self) -> bool:
        """Whether this is a desk record whose sidecars are all gone.

        Returns:
            Whether the record names a desk nobody is sitting at.
        """
        return self.is_desk and not self.holder_live

    @property
    def effective_mode(self) -> str:
        """Mode to policy against: an orphaned desk reads as released.

        Returns:
            The recorded mode, or ``idle`` when the desk is orphaned.
        """
        return RELEASED_MODE if self.orphaned else self.mode


def _as_pid(value: Json) -> int:
    """Coerce a JSON PID value to a non-negative int.

    Args:
        value: Raw JSON value for a PID field.

    Returns:
        The PID, or ``0`` when absent or not a number.
    """
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value if value > 0 else 0
    if isinstance(value, str) and value.strip().isdigit():
        pid = int(value.strip())
        return pid if pid > 0 else 0
    return 0


def _as_flag(value: Json) -> bool:
    """Coerce a JSON boolean-ish field.

    Args:
        value: Raw JSON value.

    Returns:
        Whether the flag reads true.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def _pids_alive(data: JsonMap) -> Mapping[str, bool] | None:
    """Extract the host-written liveness map.

    Args:
        data: Parsed occupancy record.

    Returns:
        The liveness map, or ``None`` when the record predates the field.
    """
    raw = data.get(PIDS_ALIVE_KEY)
    if not isinstance(raw, dict):
        return None
    return {str(key): _as_flag(value) for key, value in raw.items()}


def parse_state(data: JsonMap) -> Occupancy:
    """Build an :class:`Occupancy` from an already-parsed record.

    Args:
        data: Parsed ``.occupancy.json`` object.

    Returns:
        The immutable read.
    """
    mode = str(data.get("mode") or "").strip()
    keys = HOLDER_PID_KEYS.get(mode, ())
    holders = tuple((name, _as_pid(data.get(name))) for name in keys)
    return Occupancy(
        present=True,
        mode=mode or UNKNOWN_MODE,
        parked=_as_flag(data.get("parked")),
        compose=_as_flag(data.get("compose")),
        holder_pids=holders,
        pids_alive=_pids_alive(data),
    )


def read_state(path: Path | None = None) -> Occupancy:
    """Read the occupancy record without mutating anything.

    A missing file is not an error: it reads as ``unknown`` so first run and
    pytest pass. A file that exists but cannot be parsed raises, because
    silently treating a corrupt lock as free would hand the GPU to two jobs.

    Args:
        path: State file. Default: :func:`state_path`.

    Returns:
        The immutable read.

    Raises:
        OccupancyStateError: File exists but is unreadable or not an object.
    """
    state = state_path() if path is None else path
    if not state.is_file():
        return Occupancy()
    try:
        data = json.loads(state.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        raise OccupancyStateError(f"unreadable occupancy state at {state}: {exc}") from exc
    if not isinstance(data, dict):
        raise OccupancyStateError(f"occupancy state at {state} is not a JSON object")
    return parse_state(data)


def recovery_command(mode: str, *, yes: bool = True) -> str:
    """Build the operator command that takes the GPU.

    Args:
        mode: Mode the caller needs, e.g. ``trellis``.
        yes: Append ``--yes`` so a live desk is stopped in one step.

    Returns:
        A copy-pasteable host command.
    """
    flag = " --yes" if yes else ""
    return f"{MANAGE_TARGET} occupancy enter {mode}{flag}"


def decide_heavy_queue(required_mode: str, state: Occupancy | None = None) -> tuple[bool, str]:
    """Decide whether a heavy graph may run against the current record.

    The XOR this enforces is against a *live* GPU job, which is what the mode
    machine is for:

    * a desk mode whose sidecar died names no job, so it never blocks a Queue;
    * a live ``llm-desk`` is the GPU job itself, so it always blocks;
    * a live ``blender-desk`` blocks on unified memory, per the desk doc;
    * a different heavy mode still blocks (LTX next to TRELLIS stays XOR);
    * ``idle`` blocks, because declaring the mode is the documented procedure.

    Args:
        required_mode: Heavy mode the graph needs.
        state: Occupancy read. Default: :func:`read_state`.

    Returns:
        ``(allowed, operator_hint)``. The hint is empty when allowed, a warning
        when an orphaned desk was released, and the exact host command when
        refused.

    Raises:
        OccupancyStateError: The record is unreadable.
    """
    occ = read_state() if state is None else state
    required = str(required_mode or "").strip()
    if occ.orphaned:
        return True, (
            f"occupancy {occ.mode} has no live sidecar "
            f"(pids {', '.join(f'{name}={pid}' for name, pid in occ.holder_pids) or 'none'}); "
            "released for this Queue"
        )
    mode = occ.effective_mode
    if mode == required or mode == UNKNOWN_MODE:
        return True, ""
    if mode == RELEASED_MODE:
        return False, (
            f"occupancy is idle; {recovery_command(required, yes=False)} then start"
        )
    if occ.is_heavy:
        return False, (
            f"occupancy is {mode}, required {required}; "
            f"{recovery_command(required)} unloads it first"
        )
    if occ.mode == "blender-desk":
        return False, (
            "occupancy is blender-desk (Workbench Blender holds the GPU); "
            f"{recovery_command(required)} stops the desk first"
        )
    if occ.mode == "llm-desk":
        return False, (
            "occupancy is llm-desk (the 35B sidecar is the GPU job); "
            f"{recovery_command(required)} stops the sidecar first"
        )
    return False, f"occupancy is {mode}, required {required}; {recovery_command(required)}"

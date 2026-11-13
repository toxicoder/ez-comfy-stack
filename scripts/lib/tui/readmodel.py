"""Machine readings for the console, taken from the CLI that already owns them.

The console does not reimplement a probe. It runs the same machine-readable
verbs the operator runs (``manage.sh status --json``,
``manage.sh occupancy status --json``, ``manage.sh download-limit status
--json``, and one ``<download-*.sh> status --json`` per model pack) and folds
their output into a single :class:`~tui.contract.Health` snapshot. Three rules
keep this layer honest on a box nobody is standing next to:

* Nothing here spawns a process or touches a terminal. Every command goes
  through the injected :data:`Probe` callable, so the suite can drive each
  branch and the runner stays the only place an ``execve`` happens.
* A probe that fails is reported, never guessed. The field keeps its unknown
  sentinel (:data:`~tui.contract.UNMEASURED`, ``"unknown"``, ``"unmeasured"``)
  and the failure lands in ``Health["errors"]``, which is what makes
  :mod:`tui.guard` block instead of waving the operator through.
* A desk mode is judged on its sidecar, never on the mode string. The holder
  PIDs and the host-stamped ``pids_alive`` map are kept, and the one
  :mod:`ez_common.occupancy` reader decides whether the desk is still held, so
  an orphaned record cannot block the console forever.

The argv lives in :data:`PROBE_COMMANDS` as plain argument lists, so there is
no shell string anywhere near an operator answer.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

from tui.contract import (
    UNMEASURED,
    Health,
    LimitStatusJson,
    OccupancyJson,
    PackJson,
    SpeedCacheJson,
    StackStatusJson,
    empty_health,
)

if TYPE_CHECKING:
    from ez_common import Json, JsonMap, Occupancy

Probe: TypeAlias = Callable[[tuple[str, ...]], str]
"""One machine probe: takes the argv to run, returns its captured stdout."""


def _ensure_custom_nodes_path() -> None:
    """Prepend ``custom_nodes/`` so the shared occupancy reader resolves.

    The console dispatches from the checkout, and the occupancy policy lives
    with the Comfy packs that own it, so the path is anchored at this module
    rather than at the working directory.
    """
    custom = str(Path(__file__).resolve().parents[3] / "custom_nodes")
    if custom not in sys.path:
        sys.path.insert(0, custom)


def _occupancy_view(obj: JsonMap) -> Occupancy:
    """Read one parsed record through the shared occupancy policy.

    Args:
        obj: Parsed ``.occupancy.json`` object.

    Returns:
        The shared immutable read, which knows the holder PIDs and the
        host-stamped liveness map.
    """
    _ensure_custom_nodes_path()
    from ez_common import occupancy

    return occupancy.parse_state(obj)


HF_PID_FILENAME = ".hf-download.pid"
"""Pid file the download layer leaves under ``MODELS_DIR``.

Read by ``disk_hf_pid_present`` in ``scripts/lib/disk_scan.sh`` and by
``reap-models.sh`` before it will apply anything.
"""

OCCUPANCY_FILENAME = ".occupancy.json"
"""State file the occupancy desk keeps under ``COMFY_OUTPUT_DIR``."""

_LLM_DESK_MODE = "llm-desk"
"""Desk mode whose claim is the host llama-server holding the GPU."""

STACK_PROBE = "stack"
"""Probe key for the Compose status payload."""

OCCUPANCY_PROBE = "occupancy"
"""Probe key for the occupancy desk payload."""

LIMIT_PROBE = "limit"
"""Probe key for the download-limit payload."""

_SCALAR_PROBE_KEYS: frozenset[str] = frozenset(
    {STACK_PROBE, OCCUPANCY_PROBE, LIMIT_PROBE}
)
"""Probe keys that fill single fields rather than the model-pack table."""

PROBE_COMMANDS: dict[str, tuple[str, ...]] = {
    STACK_PROBE: ("scripts/manage.sh", "status", "--json"),
    OCCUPANCY_PROBE: ("scripts/manage.sh", "occupancy", "status", "--json"),
    LIMIT_PROBE: ("scripts/manage.sh", "download-limit", "status", "--json"),
    "image": (
        "scripts/utilities/download-image.sh",
        "status",
        "--tier",
        "fast",
        "--json",
    ),
    "wan": ("scripts/utilities/download-wan.sh", "status", "--tier", "5b", "--json"),
    "ltx": ("scripts/utilities/download-ltx.sh", "status", "--tier", "2.5", "--json"),
    "llm": ("scripts/utilities/download-llm.sh", "status", "--json"),
    "podcast": (
        "scripts/utilities/download-podcast.sh",
        "status",
        "--tier",
        "analog",
        "--json",
    ),
    "dub": ("scripts/utilities/download-dub.sh", "status", "--tier", "asr", "--json"),
    "dub-clone": (
        "scripts/utilities/download-dub.sh",
        "status",
        "--tier",
        "clone",
        "--json",
    ),
    "music": (
        "scripts/utilities/download-music.sh",
        "status",
        "--tier",
        "turbo",
        "--json",
    ),
}
"""argv for every probe, relative to the repo root, one entry per probe name.

The three :data:`_SCALAR_PROBE_KEYS` entries carry the machine readings; every
other key is one model pack the dashboard reports readiness for. The argv is
anchored at ``repo_root`` by :func:`probe_health` so a probe runs the script
from this checkout, and never through a shell.
"""

PACK_PROBES: tuple[str, ...] = tuple(
    name for name in PROBE_COMMANDS if name not in _SCALAR_PROBE_KEYS
)
"""Model pack ids the console tracks, in the order they are probed."""

def _json_object(text: str) -> JsonMap | None:
    """Parse probe text into a JSON object.

    Args:
        text: Captured stdout of one probe.

    Returns:
        The decoded object, or None when the text is empty, is not JSON, or is
        JSON that is not an object.
    """
    if not text.strip():
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    obj: JsonMap = parsed
    return obj


def _as_int(value: Json) -> int | None:
    """Read a JSON value as an integer, refusing booleans and strings.

    Args:
        value: Value pulled out of a parsed payload.

    Returns:
        The integer, or None when the value is not numeric.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    return None


def _as_float(value: Json) -> float | None:
    """Read a JSON value as a float, refusing booleans and strings.

    Args:
        value: Value pulled out of a parsed payload.

    Returns:
        The float, or None when the value is not numeric.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _probe(
    run: Probe,
    repo_root: Path,
    name: str,
    errors: list[str],
) -> str | None:
    """Run one probe and hand back what it printed.

    Any failure is turned into a sentence in ``errors`` rather than an
    exception: the console has to keep rendering on a box where Docker or a
    download utility is misbehaving.

    Args:
        run: Injected probe callable.
        repo_root: Checkout the probe command is anchored at.
        name: Key into :data:`PROBE_COMMANDS`.
        errors: Accumulator that receives an operator-facing sentence.

    Returns:
        The captured text, or None when the probe raised or printed nothing.
    """
    argv = PROBE_COMMANDS[name]
    command = (str(repo_root / argv[0]),) + argv[1:]
    try:
        text = run(command)
    except Exception as exc:  # noqa: BLE001 - any probe failure degrades to unknown
        errors.append(f"{name}: probe failed ({type(exc).__name__}): {exc}")
        return None
    if not text.strip():
        errors.append(f"{name}: probe returned no output")
        return None
    return text


def parse_stack_status(text: str) -> StackStatusJson | None:
    """Parse ``manage.sh status --json`` output.

    Args:
        text: Captured stdout of the stack probe.

    Returns:
        The payload, or None when it cannot be read at all. A payload that
        omits a field simply leaves that field out, so the caller can tell a
        missing reading from a healthy zero.
    """
    obj = _json_object(text)
    if obj is None:
        return None
    state = obj.get("state")
    if not isinstance(state, str) or not state:
        return None
    payload = StackStatusJson(state=state)
    attention = obj.get("attention")
    if isinstance(attention, str) and attention:
        payload["attention"] = attention
    stack = obj.get("stack")
    if isinstance(stack, str) and stack:
        payload["stack"] = stack
    free_gib = _as_int(obj.get("host_free_gib"))
    if free_gib is not None:
        payload["host_free_gib"] = free_gib
    return payload


def parse_occupancy(text: str) -> OccupancyJson | None:
    """Parse ``manage.sh occupancy status --json`` or the state file.

    The three sidecar PIDs and the host-stamped ``pids_alive`` map are kept so
    a desk record can be judged on liveness rather than on its mode string
    alone, and :class:`~ez_common.occupancy.Occupancy` turns that pair into the
    ``orphaned`` verdict the guard policies against. A record that predates the
    liveness map keeps the fail-closed answer.

    Args:
        text: Occupancy payload as JSON text.

    Returns:
        The payload, or None when it cannot be read. Optional fields the shell
        did not report are left out so the caller keeps its unknown sentinel.
    """
    obj = _json_object(text)
    if obj is None:
        return None
    mode = obj.get("mode")
    if not isinstance(mode, str) or not mode:
        return None
    payload = OccupancyJson(mode=mode)
    parked = obj.get("parked")
    if isinstance(parked, bool):
        payload["parked"] = parked
    queue = obj.get("queue")
    if isinstance(queue, str) and queue:
        payload["queue"] = queue
    llm_live = obj.get("llm_live")
    if isinstance(llm_live, bool):
        payload["llm_live"] = llm_live
    blender_pid = _as_int(obj.get("blender_pid"))
    if blender_pid is not None:
        payload["blender_pid"] = blender_pid
    mcp_pid = _as_int(obj.get("mcp_pid"))
    if mcp_pid is not None:
        payload["mcp_pid"] = mcp_pid
    llm_pid = _as_int(obj.get("llm_pid"))
    if llm_pid is not None:
        payload["llm_pid"] = llm_pid
    state = _occupancy_view(obj)
    if state.pids_alive is not None:
        payload["pids_alive"] = dict(state.pids_alive)
    payload["orphaned"] = state.orphaned
    if llm_live is None and state.mode == _LLM_DESK_MODE:
        payload["llm_live"] = state.holder_live
    return payload


def parse_limit_status(text: str) -> LimitStatusJson | None:
    """Parse ``manage.sh download-limit status --json`` output.

    Args:
        text: Captured stdout of the download-limit probe.

    Returns:
        The payload, or None when it cannot be read. The nested speed cache is
        kept only when it is an object; the shell always prints one.
    """
    obj = _json_object(text)
    if obj is None:
        return None
    interface = obj.get("interface")
    if not isinstance(interface, str) or not interface:
        return None
    payload = LimitStatusJson(interface=interface)
    tool = obj.get("tool")
    if isinstance(tool, str) and tool:
        payload["tool"] = tool
    shaping = obj.get("shaping_supported")
    if isinstance(shaping, bool):
        payload["shaping_supported"] = shaping
    raw_cache = obj.get("speed_cache")
    if isinstance(raw_cache, dict):
        cache: JsonMap = raw_cache
        entry = SpeedCacheJson()
        valid = cache.get("valid")
        if isinstance(valid, bool):
            entry["valid"] = valid
        measured = _as_float(cache.get("measured_mbps"))
        if measured is not None:
            entry["measured_mbps"] = measured
        payload["speed_cache"] = entry
    return payload


def parse_pack(text: str) -> PackJson | None:
    """Parse one ``<download-*.sh> status --json`` payload.

    The utilities print a wrapper object whose ``tiers`` list holds one entry
    per requested tier; a bare tier object is accepted too, which is what the
    single-tier callers emit.

    Args:
        text: Captured stdout of one pack probe.

    Returns:
        The tier reading, or None when readiness cannot be established. A pack
        that reports ``ready`` false is a valid reading, not a parse failure.
    """
    obj = _json_object(text)
    if obj is None:
        return None
    tiers = obj.get("tiers")
    entry: JsonMap = obj
    if isinstance(tiers, list):
        first: JsonMap | None = None
        for candidate in tiers:
            if isinstance(candidate, dict):
                first = candidate
                break
        if first is None:
            return None
        entry = first
    tier = entry.get("tier")
    ready = entry.get("ready")
    if not isinstance(tier, str) or not tier or not isinstance(ready, bool):
        return None
    payload = PackJson(tier=tier, ready=ready)
    path = entry.get("path")
    if isinstance(path, str) and path:
        payload["path"] = path
    size_gb = _as_float(entry.get("size_gb"))
    if size_gb is not None:
        payload["size_gb"] = size_gb
    min_gb = _as_float(entry.get("min_gb"))
    if min_gb is not None:
        payload["min_gb"] = min_gb
    return payload


def read_occupancy_file(path: Path) -> OccupancyJson | None:
    """Read the occupancy state file straight off disk.

    Used when the occupancy verb is unavailable but the desk still left its
    state behind. It carries no live queue reading, and its sidecar readings
    are the host's last stamped verdict rather than a fresh probe, so a caller
    must not treat them as taken just now.

    Args:
        path: Usually ``COMFY_OUTPUT_DIR/.occupancy.json``.

    Returns:
        The payload, or None when the file is missing, unreadable, or not
        parsable occupancy JSON.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    return parse_occupancy(text)


def disk_free_gib(path: Path) -> int:
    """Report free disk on the filesystem holding ``path``, in whole GiB.

    Mirrors ``host_disk_free_gib`` in ``scripts/lib/safety.sh``, which reads
    the available-block column of ``df -Pk``. The console takes the reading
    with :func:`os.statvfs` instead of shelling out, and unlike the shell
    helper it does not fall back to ``/``: measuring the wrong filesystem on a
    remote box is worse than not knowing.

    Args:
        path: Usually ``MODELS_DIR``.

    Returns:
        Whole GiB available to an unprivileged caller, or
        :data:`~tui.contract.UNMEASURED` when the path is missing or the
        filesystem cannot be queried.
    """
    try:
        stats = os.statvfs(path)
    except OSError:
        return UNMEASURED
    block_size = stats.f_frsize or stats.f_bsize
    if block_size <= 0:
        return UNMEASURED
    return int(stats.f_bavail * block_size // 1024**3)


def _pid_is_alive(pid: int) -> bool:
    """Ask the kernel whether one pid still exists.

    Args:
        pid: Candidate process id.

    Returns:
        True when the process exists (including one owned by another user),
        False when it is gone or the number is not a usable pid.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except (OverflowError, ValueError):
        return False
    return True


def hf_download_running(models_dir: Path) -> bool:
    """Whether a Hugging Face download is live under ``models_dir``.

    Mirrors ``disk_hf_pid_present`` in ``scripts/lib/disk_scan.sh``, with one
    tightening: a pid file that names a process which no longer exists is a
    leftover from an interrupted pull, not a running download, so it does not
    hold the guard open. Unreadable or garbage pid files are likewise not
    proof of a live download.

    Args:
        models_dir: The ``MODELS_DIR`` the download layer writes into.

    Returns:
        True only when ``.hf-download.pid`` names a live process.
    """
    pid_file = models_dir / HF_PID_FILENAME
    try:
        raw = pid_file.read_text(encoding="utf-8")
    except OSError:
        return False
    candidate = raw.strip()
    if not candidate.isdigit():
        return False
    pid = int(candidate)
    if pid <= 0:
        return False
    return _pid_is_alive(pid)


def _merge_occupancy(health: Health, source: OccupancyJson) -> None:
    """Copy the readings one occupancy source reports into the snapshot.

    Args:
        health: Snapshot to update in place.
        source: Parsed occupancy payload; fields it omits are left alone.
    """
    mode = source.get("mode")
    if isinstance(mode, str) and mode:
        health["occupancy_mode"] = mode
    parked = source.get("parked")
    if isinstance(parked, bool):
        health["parked"] = parked
    queue = source.get("queue")
    if isinstance(queue, str) and queue:
        health["queue"] = queue
    llm_live = source.get("llm_live")
    if isinstance(llm_live, bool):
        health["llm_live"] = llm_live
    orphaned = source.get("orphaned")
    if isinstance(orphaned, bool):
        health["occupancy_orphaned"] = orphaned


def _probe_stack(
    run: Probe,
    repo_root: Path,
    health: Health,
    errors: list[str],
) -> None:
    """Fill the stack state, attention backend, and free-RAM readings.

    Args:
        run: Injected probe callable.
        repo_root: Checkout the probe command is anchored at.
        health: Snapshot to update in place.
        errors: Accumulator for probe failures.
    """
    text = _probe(run, repo_root, STACK_PROBE, errors)
    payload = parse_stack_status(text) if text is not None else None
    if payload is None:
        errors.append("stack: the compose status probe gave no usable reading")
        return
    health["stack_state"] = payload.get("state", "unknown")
    health["attention"] = payload.get("attention", "unknown")
    free_gib = payload.get("host_free_gib")
    if free_gib is None:
        errors.append("stack: free host RAM was not reported")
        return
    health["host_free_gib"] = free_gib


def _probe_occupancy(
    run: Probe,
    repo_root: Path,
    comfy_output_dir: Path,
    health: Health,
    errors: list[str],
) -> None:
    """Fill the occupancy desk readings, falling back to the state file.

    Args:
        run: Injected probe callable.
        repo_root: Checkout the probe command is anchored at.
        comfy_output_dir: Outputs tree that holds ``.occupancy.json``.
        health: Snapshot to update in place.
        errors: Accumulator for probe failures.
    """
    text = _probe(run, repo_root, OCCUPANCY_PROBE, errors)
    payload = parse_occupancy(text) if text is not None else None
    if payload is not None:
        _merge_occupancy(health, payload)
        if "queue" not in payload:
            errors.append("occupancy: the ComfyUI queue was not reported")
        return
    on_disk = read_occupancy_file(comfy_output_dir / OCCUPANCY_FILENAME)
    if on_disk is None:
        errors.append("occupancy: neither the verb nor the state file answered")
        return
    _merge_occupancy(health, on_disk)
    errors.append(
        "occupancy: read from the state file, so the queue is unknown and the "
        "sidecar reading is the last one the host stamped"
    )


def _probe_limit(
    run: Probe,
    repo_root: Path,
    health: Health,
    errors: list[str],
) -> None:
    """Fill the bandwidth-cap readings.

    Args:
        run: Injected probe callable.
        repo_root: Checkout the probe command is anchored at.
        health: Snapshot to update in place.
        errors: Accumulator for probe failures.
    """
    text = _probe(run, repo_root, LIMIT_PROBE, errors)
    payload = parse_limit_status(text) if text is not None else None
    if payload is None:
        errors.append("download-limit: the cap probe gave no usable reading")
        return
    health["shaping"] = payload.get("shaping_supported", False)
    cache = payload.get("speed_cache")
    measured = cache.get("measured_mbps") if cache is not None else None
    valid = cache.get("valid", False) if cache is not None else False
    if valid and measured is not None:
        health["shaping_mbps"] = int(measured)
    else:
        errors.append("download-limit: no fresh measured link rate")


def _probe_packs(
    run: Probe,
    repo_root: Path,
    health: Health,
    errors: list[str],
) -> None:
    """Fill the model-pack readiness table.

    A pack whose probe failed is recorded as not ready and called out in
    ``errors``: the guard blocks either way, and the dashboard gets to say
    which pack it could not read rather than claiming it is missing.

    Args:
        run: Injected probe callable.
        repo_root: Checkout the probe command is anchored at.
        health: Snapshot to update in place.
        errors: Accumulator for probe failures.
    """
    reported: list[tuple[str, bool]] = []
    for name in PACK_PROBES:
        text = _probe(run, repo_root, name, errors)
        payload = parse_pack(text) if text is not None else None
        if payload is None:
            errors.append(f"model pack {name}: no readiness report")
            reported.append((name, False))
            continue
        reported.append((name, bool(payload.get("ready", False))))
    health["packs"] = tuple(reported)


def probe_health(
    run: Probe,
    *,
    repo_root: Path,
    models_dir: Path,
    comfy_output_dir: Path,
) -> Health:
    """Take one full snapshot of the machine.

    Every probe runs through ``run`` and every parse is defensive: this
    function never raises. A probe that throws, prints nothing, or prints
    something unparsable adds a sentence to ``Health["errors"]`` and leaves its
    fields at the unknown sentinel, which is exactly what makes
    :func:`tui.guard.evaluate` refuse the heavy verbs.

    Args:
        run: Callable that executes one argv and returns its captured stdout.
        repo_root: Checkout whose ``scripts/`` tree the probes run from.
        models_dir: ``MODELS_DIR``; measured for free space and hf pid files.
        comfy_output_dir: ``COMFY_OUTPUT_DIR``; holds the occupancy state file.

    Returns:
        A :class:`~tui.contract.Health` snapshot, complete or degraded, never
        partial-and-silent.
    """
    errors: list[str] = []
    health = empty_health()
    health["errors"] = ()
    _probe_stack(run, repo_root, health, errors)
    _probe_occupancy(run, repo_root, comfy_output_dir, health, errors)
    _probe_limit(run, repo_root, health, errors)
    health["disk_free_gib"] = disk_free_gib(models_dir)
    if health["disk_free_gib"] < 0:
        errors.append(f"disk: free space under {models_dir} could not be read")
    health["downloads_running"] = hf_download_running(models_dir)
    _probe_packs(run, repo_root, health, errors)
    health["errors"] = tuple(errors)
    return health

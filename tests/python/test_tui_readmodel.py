"""The read model turns CLI output into one honest health snapshot.

Nothing here spawns a process: every command is handed to an injected probe, so
the suite can make each probe answer, stay silent, print rubbish, or raise.
The behaviour that matters is that a failed probe leaves its field at the
unknown sentinel and says so in ``Health["errors"]``, because :mod:`tui.guard`
blocks on exactly those sentinels.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import NamedTuple

import pytest

from tui import readmodel
from tui.contract import UNMEASURED, Health

STACK_JSON = json.dumps(
    {
        "stack": "studio",
        "state": "running",
        "attention": "kitchen",
        "host_free_gib": 64,
    }
)
"""A complete ``manage.sh status --json`` payload."""

OCCUPANCY_JSON = json.dumps(
    {
        "version": 1,
        "mode": "idle",
        "compose": True,
        "parked": False,
        "blender_pid": 0,
        "mcp_pid": 0,
        "llm_pid": 0,
        "updated": "2026-01-01T00:00:00Z",
        "compose_live": True,
        "queue": "idle",
        "llm_live": False,
    }
)
"""A complete ``occupancy status --json`` payload."""

LIMIT_JSON = json.dumps(
    {
        "interface": "eth0",
        "tool": "wondershaper",
        "auto_fraction": 0.85,
        "shaping_supported": True,
        "speed_cache": {
            "path": "/tmp/speed.json",
            "ttl_sec": 900,
            "valid": True,
            "measured_mbps": 940.5,
            "age_sec": 12,
            "source": "speedtest",
            "iface": "eth0",
        },
    }
)
"""A complete ``download-limit status --json`` payload."""

PACK_JSON = json.dumps(
    {
        "tiers": [
            {
                "tier": "turbo",
                "repo": "audioshell/acestep",
                "path": "/mnt/models/checkpoints",
                "size_gb": 10.4,
                "min_gb": 8.0,
                "ready": True,
            }
        ],
        "models_dir": "/mnt/models",
    }
)
"""A complete ``<download-*.sh> status --json`` payload."""

ALL_GOOD: dict[str, str | Exception] = {
    readmodel.STACK_PROBE: STACK_JSON,
    readmodel.OCCUPANCY_PROBE: OCCUPANCY_JSON,
    readmodel.LIMIT_PROBE: LIMIT_JSON,
    **{name: PACK_JSON for name in readmodel.PACK_PROBES},
}
"""What every probe answers when the machine is healthy."""


class _UnexpectedArgv(BaseException):
    """Raised when the console asks for an argv the probe table does not name.

    Subclasses :class:`BaseException` so the read model's defensive
    ``except Exception`` cannot swallow it into an error sentence.
    """


class FakeProbe:
    """Injected probe that answers from a table and records the argv it saw.

    Attributes:
        commands: Every argv the read model asked it to run, in order.
    """

    def __init__(
        self,
        repo_root: Path,
        payloads: dict[str, str | Exception],
        *,
        default: str = "",
    ) -> None:
        """Store the checkout to anchor commands at and the per-probe answers.

        Args:
            repo_root: Checkout the read model anchors probe argv at.
            payloads: Probe name to the text it returns, or the error it raises.
            default: What a probe with no entry returns.
        """
        self.repo_root = repo_root
        self.payloads = payloads
        self.default = default
        self.commands: list[tuple[str, ...]] = []

    def anchored(self, name: str) -> tuple[str, ...]:
        """Return the argv the read model should run for one probe.

        Args:
            name: Key into :data:`tui.readmodel.PROBE_COMMANDS`.

        Returns:
            The table entry with ``argv[0]`` anchored at the repo root.
        """
        argv = readmodel.PROBE_COMMANDS[name]
        return (str(self.repo_root / argv[0]),) + argv[1:]

    def __call__(self, command: tuple[str, ...]) -> str:
        """Answer one probe call from the table.

        Args:
            command: The argv the read model built.

        Returns:
            The payload the table holds for that probe.

        Raises:
            _UnexpectedArgv: The argv matches no entry in the table.
        """
        self.commands.append(command)
        for name in readmodel.PROBE_COMMANDS:
            if command == self.anchored(name):
                answer = self.payloads.get(name, self.default)
                if isinstance(answer, BaseException):
                    raise answer
                return answer
        raise _UnexpectedArgv(f"unexpected probe argv: {command}")


def _write_pid_file(models_dir: Path, content: str) -> Path:
    """Drop a hf pid file into ``models_dir``.

    Args:
        models_dir: The directory the read model inspects.
        content: Exact file content, whitespace included.

    Returns:
        The path written.
    """
    pid_file = models_dir / readmodel.HF_PID_FILENAME
    pid_file.write_text(content, encoding="utf-8")
    return pid_file


class _Vfs(NamedTuple):
    """The three statvfs fields the read model reads.

    Attributes:
        f_frsize: Fragment size in bytes.
        f_bsize: Block size in bytes.
        f_bavail: Blocks available to an unprivileged caller.
    """

    f_frsize: int
    f_bsize: int
    f_bavail: int


def _dead_pid() -> int:
    """Find a pid the kernel says does not exist.

    Returns:
        A pid that names no live process on this host.

    Raises:
        AssertionError: Every candidate pid is taken, which would be remarkable.
    """
    for candidate in range(400_000, 400_050):
        try:
            os.kill(candidate, 0)
        except ProcessLookupError:
            return candidate
        except PermissionError:
            continue
    raise AssertionError("no unused pid found")


def _statvfs_result(f_frsize: int, f_bsize: int, f_bavail: int) -> _Vfs:
    """Build a statvfs stand-in with only the fields the read model reads.

    Args:
        f_frsize: Fragment size in bytes.
        f_bsize: Block size in bytes.
        f_bavail: Blocks available to an unprivileged caller.

    Returns:
        An object ``os.statvfs`` can be replaced with.
    """
    return _Vfs(f_frsize=f_frsize, f_bsize=f_bsize, f_bavail=f_bavail)


# ---------------------------------------------------------------------------
# The probe table
# ---------------------------------------------------------------------------


def test_probe_table_names_the_cli_that_already_owns_each_answer() -> None:
    """Every probe is a real argv from this checkout, never a shell string."""
    table = readmodel.PROBE_COMMANDS
    assert table[readmodel.STACK_PROBE] == ("scripts/manage.sh", "status", "--json")
    assert table[readmodel.OCCUPANCY_PROBE] == (
        "scripts/manage.sh",
        "occupancy",
        "status",
        "--json",
    )
    assert table[readmodel.LIMIT_PROBE] == (
        "scripts/manage.sh",
        "download-limit",
        "status",
        "--json",
    )
    for name, argv in table.items():
        assert argv, name
        assert all(" " not in part for part in argv), name
        assert argv[-1] == "--json", name
        assert argv[0].startswith("scripts/"), name


def test_probe_table_splits_machine_probes_from_pack_probes() -> None:
    """The three scalar probes and one key per model pack are all accounted for."""
    scalar = {readmodel.STACK_PROBE, readmodel.OCCUPANCY_PROBE, readmodel.LIMIT_PROBE}
    assert set(readmodel.PROBE_COMMANDS) == scalar | set(readmodel.PACK_PROBES)
    assert set(readmodel.PACK_PROBES).isdisjoint(scalar)
    assert "music" in readmodel.PACK_PROBES
    assert "wan" in readmodel.PACK_PROBES


def test_probe_health_asks_for_the_anchored_argv_of_every_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Commands run from this checkout, so a stale tree cannot answer for it."""
    monkeypatch.setattr(readmodel, "disk_free_gib", lambda _path: 500)
    repo = tmp_path / "checkout"
    probe = FakeProbe(repo, ALL_GOOD)
    readmodel.probe_health(
        probe,
        repo_root=repo,
        models_dir=tmp_path,
        comfy_output_dir=tmp_path,
    )
    assert probe.commands == [
        probe.anchored(name) for name in readmodel.PROBE_COMMANDS
    ]


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def test_parse_stack_status_reads_every_field() -> None:
    """The compose payload becomes the stack fields of the snapshot."""
    payload = readmodel.parse_stack_status(STACK_JSON)
    assert payload is not None
    assert payload == {
        "stack": "studio",
        "state": "running",
        "attention": "kitchen",
        "host_free_gib": 64,
    }


def test_parse_stack_status_leaves_out_what_the_shell_omitted() -> None:
    """A payload without a field is a missing reading, not a healthy zero."""
    payload = readmodel.parse_stack_status('{"state":"stopped"}')
    assert payload is not None
    assert payload == {"state": "stopped"}


def test_parse_stack_status_ignores_fields_that_are_not_typed_right() -> None:
    """A payload that puts a number or a bool where a value belongs is not trusted."""
    payload = readmodel.parse_stack_status(
        '{"state":"present","attention":7,"stack":false,"host_free_gib":"plenty"}'
    )
    assert payload is not None
    assert payload == {"state": "present"}
    bools = readmodel.parse_stack_status('{"state":"present","host_free_gib":true}')
    assert bools is not None
    assert bools == {"state": "present"}


@pytest.mark.parametrize("junk", ["", "   ", "not json", "[1, 2]", "null", "{}"])
def test_parse_stack_status_refuses_text_it_cannot_read(junk: str) -> None:
    """Unparsable or non-object output is None, so the caller says unknown."""
    assert readmodel.parse_stack_status(junk) is None


@pytest.mark.parametrize("bad", ['{"state":123}', '{"state":""}'])
def test_parse_stack_status_needs_a_usable_state(bad: str) -> None:
    """Without the state there is no stack reading at all."""
    assert readmodel.parse_stack_status(bad) is None


def test_parse_occupancy_reads_the_live_payload() -> None:
    """The desk reports mode, parked, queue, and the sidecar together."""
    payload = readmodel.parse_occupancy(OCCUPANCY_JSON)
    assert payload is not None
    assert payload == {
        "mode": "idle",
        "parked": False,
        "queue": "idle",
        "llm_live": False,
    }


def test_parse_occupancy_keeps_only_fields_that_are_typed_right() -> None:
    """A string standing in for a bool is dropped, not coerced."""
    payload = readmodel.parse_occupancy(
        '{"mode":"wan","parked":"yes","queue":0,"llm_live":1}'
    )
    assert payload is not None
    assert payload == {"mode": "wan"}


@pytest.mark.parametrize("junk", ["", "not json", "[]", '{"parked":true}'])
def test_parse_occupancy_needs_a_mode(junk: str) -> None:
    """Without a mode the desk says nothing the guard can trust."""
    assert readmodel.parse_occupancy(junk) is None


def test_parse_limit_status_reads_the_cap_payload() -> None:
    """Shaping support and the cached link rate both land in the snapshot."""
    payload = readmodel.parse_limit_status(LIMIT_JSON)
    assert payload is not None
    assert payload == {
        "interface": "eth0",
        "tool": "wondershaper",
        "shaping_supported": True,
        "speed_cache": {"valid": True, "measured_mbps": 940.5},
    }


def test_parse_limit_status_keeps_only_fields_that_are_typed_right() -> None:
    """Wrong-typed optional fields are dropped rather than guessed."""
    payload = readmodel.parse_limit_status(
        '{"interface":"eth0","tool":9,"shaping_supported":"yes",'
        '"speed_cache":{"valid":"true","measured_mbps":"fast"}}'
    )
    assert payload is not None
    assert payload == {"interface": "eth0", "speed_cache": {}}


def test_parse_limit_status_ignores_a_cache_that_is_not_an_object() -> None:
    """A cache the shell rendered as a scalar carries no reading."""
    payload = readmodel.parse_limit_status('{"interface":"eth0","speed_cache":null}')
    assert payload is not None
    assert payload == {"interface": "eth0"}


@pytest.mark.parametrize("junk", ["", "not json", "{}", '{"interface":""}'])
def test_parse_limit_status_needs_an_interface(junk: str) -> None:
    """No interface means the cap probe never really answered."""
    assert readmodel.parse_limit_status(junk) is None


def test_parse_pack_reads_the_wrapper_the_utilities_print() -> None:
    """The first tier entry of the wrapper is the readiness report."""
    payload = readmodel.parse_pack(PACK_JSON)
    assert payload is not None
    assert payload == {
        "tier": "turbo",
        "ready": True,
        "path": "/mnt/models/checkpoints",
        "size_gb": 10.4,
        "min_gb": 8.0,
    }


def test_parse_pack_accepts_a_bare_tier_object() -> None:
    """A caller that prints one tier without the wrapper still reads fine."""
    payload = readmodel.parse_pack('{"tier":"5b","ready":false}')
    assert payload is not None
    assert payload == {"tier": "5b", "ready": False}


def test_parse_pack_drops_tier_fields_that_are_not_typed_right() -> None:
    """A size the utility rendered as text is not a number the console can use."""
    payload = readmodel.parse_pack(
        '{"tier":"fast","ready":true,"path":null,"size_gb":"big","min_gb":true}'
    )
    assert payload is not None
    assert payload == {"tier": "fast", "ready": True}


@pytest.mark.parametrize(
    "junk",
    [
        "",
        "not json",
        "[]",
        "{}",
        '{"tiers":[]}',
        '{"tiers":["turbo"]}',
        '{"tier":"turbo"}',
        '{"ready":true}',
        '{"tier":"","ready":true}',
        '{"tier":"turbo","ready":"yes"}',
    ],
)
def test_parse_pack_refuses_a_report_that_cannot_answer_for_itself(junk: str) -> None:
    """Readiness that is missing or wrong-typed is unknown, not false-safe."""
    assert readmodel.parse_pack(junk) is None


# ---------------------------------------------------------------------------
# The occupancy state file, disk free space, and the hf pid file
# ---------------------------------------------------------------------------


def test_read_occupancy_file_reads_the_desk_state(tmp_path: Path) -> None:
    """The state file is the same record the verb prints, minus the overlay."""
    path = tmp_path / readmodel.OCCUPANCY_FILENAME
    path.write_text(OCCUPANCY_JSON, encoding="utf-8")
    payload = readmodel.read_occupancy_file(path)
    assert payload == {
        "mode": "idle",
        "parked": False,
        "queue": "idle",
        "llm_live": False,
    }


def test_read_occupancy_file_survives_a_missing_or_rubbish_file(tmp_path: Path) -> None:
    """No file, an unreadable path, and rubbish all read as unknown."""
    missing = tmp_path / "nope.json"
    assert readmodel.read_occupancy_file(missing) is None
    garbage = tmp_path / ".occupancy.json"
    garbage.write_text("{oh no", encoding="utf-8")
    assert readmodel.read_occupancy_file(garbage) is None
    assert readmodel.read_occupancy_file(tmp_path) is None


def test_disk_free_gib_matches_the_available_blocks(tmp_path: Path) -> None:
    """The reading is the ``df -Pk`` available-block column in GiB."""
    stats = os.statvfs(tmp_path)
    block = stats.f_frsize or stats.f_bsize
    expected = stats.f_bavail * block // 1024**3
    assert readmodel.disk_free_gib(tmp_path) == expected


def test_disk_free_gib_is_unmeasured_when_the_path_is_missing(tmp_path: Path) -> None:
    """A models dir that is not mounted does not read as an empty disk."""
    assert readmodel.disk_free_gib(tmp_path / "not-mounted") == UNMEASURED


def test_disk_free_gib_falls_back_to_the_block_size(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Some filesystems report a zero fragment size; the block size still works."""
    monkeypatch.setattr(
        readmodel.os,
        "statvfs",
        lambda _path: _statvfs_result(0, 4096, 40 * 1024**3 // 4096),
    )
    assert readmodel.disk_free_gib(tmp_path) == 40


def test_disk_free_gib_is_unmeasured_under_a_broken_filesystem(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A filesystem that reports no block size cannot be measured."""
    monkeypatch.setattr(
        readmodel.os, "statvfs", lambda _path: _statvfs_result(0, 0, 100)
    )
    assert readmodel.disk_free_gib(tmp_path) == UNMEASURED


def test_hf_download_running_is_false_without_a_pid_file(tmp_path: Path) -> None:
    """No pid file means no download the console has to wait for."""
    assert readmodel.hf_download_running(tmp_path) is False


def test_hf_download_running_is_true_for_a_live_pid(tmp_path: Path) -> None:
    """The console's own pid is a process that certainly exists."""
    _write_pid_file(tmp_path, f"  {os.getpid()}  \n")
    assert readmodel.hf_download_running(tmp_path) is True


def test_hf_download_running_ignores_a_dead_pid(tmp_path: Path) -> None:
    """A leftover file from an interrupted pull is not a running download."""
    _write_pid_file(tmp_path, f"{_dead_pid()}\n")
    assert readmodel.hf_download_running(tmp_path) is False


@pytest.mark.parametrize("junk", ["", "  \n", "not-a-pid", "12 34", "0", "-7"])
def test_hf_download_running_ignores_a_garbage_pid_file(
    tmp_path: Path, junk: str
) -> None:
    """Content that is not a positive pid proves nothing."""
    _write_pid_file(tmp_path, junk)
    assert readmodel.hf_download_running(tmp_path) is False


def test_hf_download_running_ignores_an_unreadable_pid_file(tmp_path: Path) -> None:
    """A pid file that cannot be read is not proof of a live download."""
    directory = tmp_path / readmodel.HF_PID_FILENAME
    directory.mkdir()
    assert readmodel.hf_download_running(tmp_path) is False


def test_hf_download_running_treats_another_users_pid_as_alive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """EPERM means the process exists; refusing to signal it is not absence."""
    _write_pid_file(tmp_path, "4")

    def _eperm(_pid: int, _sig: int) -> None:
        raise PermissionError

    monkeypatch.setattr(readmodel.os, "kill", _eperm)
    assert readmodel.hf_download_running(tmp_path) is True


def test_hf_download_running_ignores_a_pid_too_large_for_the_kernel(
    tmp_path: Path,
) -> None:
    """An absurd pid raises OverflowError at the syscall; that is not running."""
    _write_pid_file(tmp_path, "9" * 30)
    assert readmodel.hf_download_running(tmp_path) is False


# ---------------------------------------------------------------------------
# probe_health
# ---------------------------------------------------------------------------


def _snapshot(
    tmp_path: Path,
    payloads: dict[str, str | Exception],
    monkeypatch: pytest.MonkeyPatch,
    *,
    disk_gib: int | None = 412,
    models_dir: Path | None = None,
    comfy_output_dir: Path | None = None,
) -> Health:
    """Take one health snapshot through a fake probe.

    Args:
        tmp_path: Scratch directory used as the repo root by default.
        payloads: Per-probe answers; a probe with no entry answers with "".
        monkeypatch: Fixture used to pin the disk reading unless asked not to.
        disk_gib: Free-disk GiB the disk probe reports, or None to measure for
            real, which is what the missing-directory case needs.
        models_dir: Override for the models directory.
        comfy_output_dir: Override for the outputs directory.

    Returns:
        The resulting health snapshot.
    """
    if disk_gib is not None:
        monkeypatch.setattr(readmodel, "disk_free_gib", lambda _path: disk_gib)
    probe = FakeProbe(tmp_path, payloads)
    return readmodel.probe_health(
        probe,
        repo_root=tmp_path,
        models_dir=models_dir or tmp_path,
        comfy_output_dir=comfy_output_dir or tmp_path,
    )


def test_probe_health_is_complete_when_every_probe_answers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A healthy machine yields a snapshot with nothing missing and nothing to say."""
    health = _snapshot(tmp_path, ALL_GOOD, monkeypatch)
    assert health["errors"] == ()
    assert health["stack_state"] == "running"
    assert health["attention"] == "kitchen"
    assert health["host_free_gib"] == 64
    assert health["disk_free_gib"] == 412
    assert health["occupancy_mode"] == "idle"
    assert health["parked"] is False
    assert health["queue"] == "idle"
    assert health["llm_live"] is False
    assert health["shaping"] is True
    assert health["shaping_mbps"] == 940
    assert health["downloads_running"] is False
    assert health["packs"] == tuple((name, True) for name in readmodel.PACK_PROBES)


def test_probe_health_never_raises_when_a_probe_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Docker being down is an error sentence, not a traceback on a remote box."""
    payloads = dict(ALL_GOOD)
    payloads[readmodel.STACK_PROBE] = RuntimeError("docker daemon not running")
    health = _snapshot(tmp_path, payloads, monkeypatch)
    assert health["stack_state"] == "unknown"
    assert health["attention"] == "unknown"
    assert health["host_free_gib"] == UNMEASURED
    assert any("docker daemon not running" in line for line in health["errors"])
    assert any(line.startswith("stack:") for line in health["errors"])


def test_probe_health_treats_silence_as_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A probe that prints nothing has not answered, whatever it exited with."""
    payloads = dict(ALL_GOOD)
    payloads[readmodel.OCCUPANCY_PROBE] = "   \n"
    health = _snapshot(tmp_path, payloads, monkeypatch)
    assert health["occupancy_mode"] == "unknown"
    assert health["queue"] == "unmeasured"
    assert any("occupancy" in line for line in health["errors"])


def test_probe_health_treats_rubbish_as_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-JSON from the cap probe leaves the cap unknown rather than off."""
    payloads = dict(ALL_GOOD)
    payloads[readmodel.LIMIT_PROBE] = "not json"
    health = _snapshot(tmp_path, payloads, monkeypatch)
    assert health["shaping"] is False
    assert health["shaping_mbps"] == UNMEASURED
    assert any("download-limit" in line for line in health["errors"])


def test_probe_health_reports_a_stack_payload_without_free_ram(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A state without the RAM reading blocks headroom rather than implying 0 GiB."""
    payloads = dict(ALL_GOOD)
    payloads[readmodel.STACK_PROBE] = '{"state":"running"}'
    health = _snapshot(tmp_path, payloads, monkeypatch)
    assert health["stack_state"] == "running"
    assert health["attention"] == "unknown"
    assert health["host_free_gib"] == UNMEASURED
    assert any("free host RAM" in line for line in health["errors"])


def test_probe_health_reports_an_occupancy_payload_without_the_queue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A desk that answers without the queue leaves the queue unmeasured."""
    payloads = dict(ALL_GOOD)
    payloads[readmodel.OCCUPANCY_PROBE] = '{"mode":"idle","parked":true}'
    health = _snapshot(tmp_path, payloads, monkeypatch)
    assert health["occupancy_mode"] == "idle"
    assert health["parked"] is True
    assert health["queue"] == "unmeasured"
    assert any("queue" in line for line in health["errors"])


def test_probe_health_falls_back_to_the_occupancy_state_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the verb is down the desk state on disk is still worth showing."""
    outputs = tmp_path / "out"
    outputs.mkdir()
    (outputs / readmodel.OCCUPANCY_FILENAME).write_text(
        '{"mode":"wan","parked":false}', encoding="utf-8"
    )
    payloads = dict(ALL_GOOD)
    payloads[readmodel.OCCUPANCY_PROBE] = "not json"
    health = _snapshot(tmp_path, payloads, monkeypatch, comfy_output_dir=outputs)
    assert health["occupancy_mode"] == "wan"
    assert health["queue"] == "unmeasured"
    assert any("state file" in line for line in health["errors"])


def test_probe_health_says_so_when_neither_occupancy_source_answers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No verb and no state file leaves the desk unknown."""
    payloads = dict(ALL_GOOD)
    payloads[readmodel.OCCUPANCY_PROBE] = ""
    health = _snapshot(tmp_path, payloads, monkeypatch)
    assert health["occupancy_mode"] == "unknown"
    assert any("state file" in line for line in health["errors"])


def test_probe_health_reports_a_stale_speed_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An expired measurement is not a cap the operator is under."""
    payloads = dict(ALL_GOOD)
    payloads[readmodel.LIMIT_PROBE] = json.dumps(
        {
            "interface": "eth0",
            "tool": "wondershaper",
            "shaping_supported": False,
            "speed_cache": {"valid": False, "measured_mbps": 800.0},
        }
    )
    health = _snapshot(tmp_path, payloads, monkeypatch)
    assert health["shaping"] is False
    assert health["shaping_mbps"] == UNMEASURED
    assert any("measured link rate" in line for line in health["errors"])


def test_probe_health_reports_a_limit_payload_without_a_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A cap payload with no speed cache at all still cannot report Mbps."""
    payloads = dict(ALL_GOOD)
    payloads[readmodel.LIMIT_PROBE] = '{"interface":"eth0"}'
    health = _snapshot(tmp_path, payloads, monkeypatch)
    assert health["shaping_mbps"] == UNMEASURED
    assert any("measured link rate" in line for line in health["errors"])


def test_probe_health_marks_the_disk_unknown_when_models_dir_is_gone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unmounted models volume is unknown, never a full or empty disk."""
    health = _snapshot(
        tmp_path,
        dict(ALL_GOOD),
        monkeypatch,
        disk_gib=None,
        models_dir=tmp_path / "unmounted",
    )
    assert health["disk_free_gib"] == UNMEASURED
    assert any("free space" in line for line in health["errors"])


def test_probe_health_sees_a_live_download(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A hf pid file for a live process holds the download guard open."""
    _write_pid_file(tmp_path, str(os.getpid()))
    health = _snapshot(tmp_path, dict(ALL_GOOD), monkeypatch)
    assert health["downloads_running"] is True


def test_probe_health_records_a_pack_that_cannot_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A pack probe that will not answer is called out and not counted ready."""
    payloads = dict(ALL_GOOD)
    payloads["wan"] = "not json"
    health = _snapshot(tmp_path, payloads, monkeypatch)
    assert ("wan", False) in health["packs"]
    assert ("music", True) in health["packs"]
    assert any("model pack wan" in line for line in health["errors"])


def test_probe_health_counts_a_bare_tier_payload_as_a_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A utility that prints the tier without the wrapper is still believed."""
    payloads = dict(ALL_GOOD)
    payloads["music"] = '{"tier":"turbo","ready":false}'
    health = _snapshot(tmp_path, payloads, monkeypatch)
    assert ("music", False) in health["packs"]
    assert not any("model pack music" in line for line in health["errors"])

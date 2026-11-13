"""The shared occupancy reader: one record, one policy, every Python side.

GitHub #380 and #381: a ``blender-desk`` record whose Blender had already died
made the in-canvas gate refuse a TRELLIS Queue with an instruction the operator
could not carry out ("stop Blender, occupancy enter trellis --yes") while the
GPU sat idle. Every rule that keeps that from recurring is pinned here, at the
one module that now owns the mode machine for Python readers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "custom_nodes"))

from ez_common import occupancy as occ  # noqa: E402


def _record(**fields: Any) -> str:
    """One occupancy JSON document with the usual operator-written fields.

    Args:
        **fields: Keys to override on the baseline record.

    Returns:
        Serialized JSON.
    """
    payload: dict[str, Any] = {"version": 1, "mode": "idle", "parked": False, "compose": True}
    payload.update(fields)
    return json.dumps(payload)


def _write(tmp_path: Path, **fields: Any) -> Path:
    """Write ``.occupancy.json`` into ``tmp_path`` the way the host would.

    Args:
        tmp_path: Directory that stands in for the operator output dir.
        **fields: Keys to override on the baseline record.

    Returns:
        The written path.
    """
    path = tmp_path / occ.STATE_FILENAME
    path.write_text(_record(**fields), encoding="utf-8")
    return path


def _point_at(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Send the resolver's default path at a scratch directory.

    Args:
        tmp_path: Directory holding the record.
        monkeypatch: Fixture that restores the environment.
    """
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    monkeypatch.delenv("COMFY_OUTPUT", raising=False)


def test_mode_tables_match_the_shell() -> None:
    assert occ.HEAVY_MODES == ("klein", "trellis", "wan", "ltx")
    assert occ.DESK_MODES == ("blender-desk", "llm-desk")
    assert occ.VALID_MODES == ("idle", "blender-desk", "llm-desk", *occ.HEAVY_MODES)
    assert occ.STATE_FILENAME == ".occupancy.json"
    assert occ.PIDS_ALIVE_KEY == "pids_alive"
    assert occ.MANAGE_TARGET == "bazelisk run //:manage --"
    for mode, keys in occ.HOLDER_PID_KEYS.items():
        assert mode in occ.DESK_MODES
        assert keys


def test_state_path_follows_the_pack_output_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ez_common

    monkeypatch.setattr(ez_common, "output_root", lambda *, default: tmp_path)
    assert occ.state_path() == tmp_path / occ.STATE_FILENAME


def test_missing_record_reads_unknown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _point_at(tmp_path, monkeypatch)
    state = occ.read_state()
    assert state == occ.Occupancy()
    assert state.present is False
    assert state.mode == occ.UNKNOWN_MODE
    assert state.effective_mode == occ.UNKNOWN_MODE
    assert state.is_desk is False
    assert state.is_heavy is False
    assert state.holder_live is False
    assert state.orphaned is False


def test_read_state_uses_the_default_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _point_at(tmp_path, monkeypatch)
    _write(tmp_path, mode="trellis")
    assert occ.read_state().mode == "trellis"


def test_read_state_accepts_an_explicit_path(tmp_path: Path) -> None:
    path = _write(tmp_path, mode="wan", parked=True)
    state = occ.read_state(path)
    assert state.present is True
    assert state.mode == "wan"
    assert state.parked is True
    assert state.compose is True


def test_read_state_fails_closed_on_an_untrusted_record(tmp_path: Path) -> None:
    corrupt = tmp_path / occ.STATE_FILENAME
    corrupt.write_text("{not json", encoding="utf-8")
    with pytest.raises(occ.OccupancyStateError, match="unreadable occupancy state"):
        occ.read_state(corrupt)

    scalar = tmp_path / "scalar.json"
    scalar.write_text("[]", encoding="utf-8")
    with pytest.raises(occ.OccupancyStateError, match="not a JSON object"):
        occ.read_state(scalar)


def test_read_state_reports_an_undecodable_record(tmp_path: Path) -> None:
    path = tmp_path / occ.STATE_FILENAME
    path.write_bytes(b"\xff\xfe m o d e\x00")
    with pytest.raises(occ.OccupancyStateError, match="unreadable occupancy state"):
        occ.read_state(path)


def test_heavy_mode_is_a_claim_regardless_of_pids(tmp_path: Path) -> None:
    state = occ.parse_state(json.loads(_record(mode="klein", blender_pid=4242)))
    assert state.is_heavy is True
    assert state.is_desk is False
    assert state.orphaned is False
    assert state.effective_mode == "klein"
    assert state.holder_pids == ()
    assert state.holder_live is False


def test_blank_mode_reads_unknown(tmp_path: Path) -> None:
    assert occ.parse_state({"mode": "   "}).mode == occ.UNKNOWN_MODE
    assert occ.parse_state({}).mode == occ.UNKNOWN_MODE


def test_blender_desk_is_live_only_while_a_sidecar_pid_lives() -> None:
    live = occ.parse_state(
        {
            "mode": "blender-desk",
            "blender_pid": 4242,
            "mcp_pid": 0,
            "pids_alive": {"blender_pid": True, "mcp_pid": False},
        }
    )
    assert live.holder_pids == (("blender_pid", 4242), ("mcp_pid", 0))
    assert live.holder_live is True
    assert live.orphaned is False
    assert live.effective_mode == "blender-desk"

    dead = occ.parse_state(
        {
            "mode": "blender-desk",
            "blender_pid": 4242,
            "mcp_pid": 4243,
            "pids_alive": {"blender_pid": False, "mcp_pid": False},
        }
    )
    assert dead.holder_live is False
    assert dead.orphaned is True
    assert dead.effective_mode == occ.RELEASED_MODE

    # A record written by a host that predates pids_alive stays fail-closed.
    legacy = occ.parse_state({"mode": "blender-desk", "blender_pid": 4242})
    assert legacy.pids_alive is None
    assert legacy.holder_live is True
    assert legacy.orphaned is False


def test_llm_desk_claim_is_the_single_llm_pid() -> None:
    live = occ.parse_state({"mode": "llm-desk", "llm_pid": 9911, "pids_alive": {"llm_pid": True}})
    assert live.is_desk is True
    assert live.holder_live is True
    dead = occ.parse_state({"mode": "llm-desk", "llm_pid": 9911, "pids_alive": {"llm_pid": False}})
    assert dead.orphaned is True
    assert dead.effective_mode == occ.RELEASED_MODE


def test_zero_pid_is_never_alive_even_when_the_host_says_so() -> None:
    state = occ.parse_state({"mode": "llm-desk", "llm_pid": 0, "pids_alive": {"llm_pid": True}})
    assert state.holder_live is False
    assert state.orphaned is True


def test_liveness_map_missing_a_key_assumes_alive() -> None:
    state = occ.parse_state(
        {
            "mode": "blender-desk",
            "blender_pid": 4242,
            "mcp_pid": 0,
            "pids_alive": {"mcp_pid": False},
        }
    )
    assert state.holder_live is True


def test_holder_live_is_false_without_any_holder_pid() -> None:
    assert occ.Occupancy(present=True, mode="klein").holder_live is False
    assert occ.Occupancy(present=True, mode="blender-desk").holder_live is False


def test_pid_fields_are_coerced_defensively() -> None:
    state = occ.parse_state(
        {
            "mode": "blender-desk",
            "blender_pid": "  4242 ",
            "mcp_pid": True,
        }
    )
    assert state.holder_pids == (("blender_pid", 4242), ("mcp_pid", 0))

    junk = occ.parse_state(
        {"mode": "blender-desk", "blender_pid": -7, "mcp_pid": "12a", "pids_alive": {}}
    )
    assert junk.holder_pids == (("blender_pid", 0), ("mcp_pid", 0))
    assert junk.pids_alive == {}

    absent = occ.parse_state({"mode": "llm-desk"})
    assert absent.holder_pids == (("llm_pid", 0),)


def test_flag_fields_are_coerced_defensively() -> None:
    assert occ.parse_state({"mode": "idle", "parked": "TRUE", "compose": " yes "}).parked is True
    assert occ.parse_state({"mode": "idle", "parked": "TRUE", "compose": " yes "}).compose is False
    assert occ.parse_state({"mode": "idle", "parked": 1, "compose": None}).parked is True
    assert occ.parse_state({"mode": "idle", "parked": 1, "compose": None}).compose is False
    assert occ.parse_state({"mode": "idle", "parked": "false"}).parked is False
    assert occ.parse_state({"mode": "idle", "pids_alive": {"llm_pid": "true"}}).pids_alive == {
        "llm_pid": True
    }


def test_a_non_object_liveness_map_reads_as_legacy() -> None:
    assert occ.parse_state({"mode": "llm-desk", "pids_alive": "yes"}).pids_alive is None
    assert occ.parse_state({"mode": "llm-desk", "pids_alive": [True]}).pids_alive is None


def test_recovery_command_is_the_documented_host_verb() -> None:
    assert (
        occ.recovery_command("trellis") == "bazelisk run //:manage -- occupancy enter trellis --yes"
    )
    assert (
        occ.recovery_command("idle", yes=False)
        == "bazelisk run //:manage -- occupancy enter idle"
    )


def test_decide_allows_the_matching_heavy_mode() -> None:
    state = occ.Occupancy(present=True, mode="trellis")
    assert occ.decide_heavy_queue("trellis", state) == (True, "")


def test_decide_allows_a_heavy_graph_when_no_record_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _point_at(tmp_path, monkeypatch)
    assert occ.decide_heavy_queue("trellis") == (True, "")


def test_decide_releases_an_orphaned_desk_with_a_warning() -> None:
    state = occ.parse_state(
        {
            "mode": "blender-desk",
            "blender_pid": 4242,
            "mcp_pid": 4243,
            "pids_alive": {"blender_pid": False, "mcp_pid": False},
        }
    )
    allowed, hint = occ.decide_heavy_queue("trellis", state)
    assert allowed is True
    assert "no live sidecar" in hint
    assert "blender_pid=4242" in hint
    assert "mcp_pid=4243" in hint


def test_decide_releases_an_orphaned_desk_that_recorded_no_pid() -> None:
    state = occ.Occupancy(present=True, mode="llm-desk")
    allowed, hint = occ.decide_heavy_queue("wan", state)
    assert allowed is True
    assert "pids none" in hint


def test_decide_refuses_idle_because_declaring_the_mode_is_the_procedure() -> None:
    allowed, hint = occ.decide_heavy_queue("trellis", occ.Occupancy(present=True, mode="idle"))
    assert allowed is False
    assert "occupancy is idle" in hint
    assert "occupancy enter trellis then start" in hint


def test_decide_refuses_a_different_heavy_mode() -> None:
    state = occ.Occupancy(present=True, mode="ltx")
    allowed, hint = occ.decide_heavy_queue("trellis", state)
    assert allowed is False
    assert "occupancy is ltx, required trellis" in hint
    assert "occupancy enter trellis --yes unloads it first" in hint


def test_decide_refuses_a_live_blender_desk() -> None:
    state = occ.parse_state(
        {"mode": "blender-desk", "blender_pid": 4242, "pids_alive": {"blender_pid": True}}
    )
    allowed, hint = occ.decide_heavy_queue("trellis", state)
    assert allowed is False
    assert "Workbench Blender holds the GPU" in hint
    assert "occupancy enter trellis --yes stops the desk first" in hint


def test_decide_refuses_a_live_llm_desk() -> None:
    state = occ.parse_state(
        {"mode": "llm-desk", "llm_pid": 9911, "pids_alive": {"llm_pid": True}}
    )
    allowed, hint = occ.decide_heavy_queue("wan", state)
    assert allowed is False
    assert "the 35B sidecar is the GPU job" in hint
    assert "stops the sidecar first" in hint


def test_decide_refuses_a_mode_label_the_shell_does_not_know() -> None:
    state = occ.Occupancy(present=True, mode="bogus")
    allowed, hint = occ.decide_heavy_queue("trellis", state)
    assert allowed is False
    assert "occupancy is bogus, required trellis" in hint
    assert hint.endswith("occupancy enter trellis --yes")

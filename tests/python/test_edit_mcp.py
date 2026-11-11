"""Host editing MCP: typed thin client of the ComfyUI /ez_edit routes.

Hermetic: every route call goes through the ``_urlopen`` seam (no sockets),
and the pinned tool surface is compared against
``custom_nodes/ez_edit/protocol.py`` by parsing that file with ``ast``.
"""

from __future__ import annotations

import ast
import io
import json
import runpy
import sys
import urllib.error
import urllib.request
from email.message import Message
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "scripts" / "lib"
PROTOCOL_PATH = ROOT / "custom_nodes" / "ez_edit" / "protocol.py"

sys.path.insert(0, str(LIB))

import edit_mcp as mcp  # noqa: E402

# Pinned by /tmp/CONTRACTS.md (Host MCP) and the routes table in that file.
PINNED_ROUTES: dict[str, tuple[str, str]] = {
    "edit_get_state": ("GET", "/ez_edit/state"),
    "edit_list_projects": ("GET", "/ez_edit/projects"),
    "edit_import": ("POST", "/ez_edit/import"),
    "edit_apply_ops": ("POST", "/ez_edit/ops"),
    "edit_render": ("POST", "/ez_edit/render"),
    "edit_job_status": ("GET", "/ez_edit/job"),
    "edit_generate_clip": ("POST", "/ez_edit/generate_clip"),
    "edit_export_edl": ("POST", "/ez_edit/export_edl"),
}

CATALOG_NAMES = [
    "edit_get_state",
    "edit_list_projects",
    "edit_import",
    "edit_apply_ops",
    "edit_render",
    "edit_job_status",
    "edit_generate_clip",
    "edit_export_edl",
    "occupancy_status",
]


class _Response:
    """Minimal stand-in for one urllib HTTP response."""

    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        """Return the canned body.

        Returns:
            UTF-8 body bytes.
        """
        return self._body

    def __enter__(self) -> "_Response":
        """Enter the context manager.

        Returns:
            This response.
        """
        return self

    def __exit__(self, *_exc: object) -> None:
        """Exit the context manager.

        Returns:
            None.
        """
        return None


class _RaisingBody:
    """File-like fp whose read always fails (a dead error stream)."""

    def read(self) -> bytes:
        """Read the error body.

        Raises:
            OSError: always, to exercise the fallback.
        """
        raise OSError("body gone")

    def close(self) -> None:
        """Close the stream.

        Returns:
            None.
        """
        return None


class _Open:
    """Callable stub for ``edit_mcp._urlopen``."""

    def __init__(self, reply: object) -> None:
        self.reply = reply
        self.requests: list[urllib.request.Request] = []
        self.timeouts: list[float] = []

    def __call__(self, request: urllib.request.Request, timeout: float) -> Any:
        """Record the request and return (or raise) the canned reply.

        Args:
            request: Prepared request.
            timeout: Socket timeout handed to urlopen.

        Returns:
            Stub response, unless the reply is an exception.
        """
        self.requests.append(request)
        self.timeouts.append(timeout)
        if isinstance(self.reply, BaseException):
            raise self.reply
        return _Response(str(self.reply))


def _install(monkeypatch: pytest.MonkeyPatch, reply: object) -> _Open:
    """Point the module's urlopen seam at a canned reply.

    Args:
        monkeypatch: pytest monkeypatch fixture.
        reply: Body text, or an exception to raise.

    Returns:
        The recording stub.
    """
    stub = _Open(reply)
    monkeypatch.setattr(mcp, "_urlopen", stub)
    return stub


def _body(request: urllib.request.Request) -> dict[str, Any]:
    """Decode the JSON body of a recorded request.

    Args:
        request: Recorded request.

    Returns:
        Parsed POST body.
    """
    assert request.data is not None
    assert isinstance(request.data, bytes)
    parsed = json.loads(request.data.decode("utf-8"))
    assert isinstance(parsed, dict)
    return parsed


def _http_error(
    code: int, body: object, reason: str = "Error"
) -> urllib.error.HTTPError:
    """Build an HTTPError carrying an optional readable body.

    Args:
        code: HTTP status.
        body: Body text, or a file-like object.
        reason: Reason phrase.

    Returns:
        HTTPError for the urlopen seam to raise.
    """
    fp: Any = body if hasattr(body, "read") else io.BytesIO(str(body).encode("utf-8"))
    return urllib.error.HTTPError(
        "http://127.0.0.1:8188/ez_edit/x", code, reason, Message(), fp
    )


@pytest.fixture(autouse=True)
def _hermetic_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Pin origin and output dir so no test can touch a real host state."""
    monkeypatch.setenv("EZ_EDIT_COMFY_URL", "http://127.0.0.1:8188")
    monkeypatch.delenv("COMFY_PORT", raising=False)
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))


def test_tool_surface_is_the_pinned_catalog() -> None:
    assert [row["name"] for row in mcp.list_tools()] == CATALOG_NAMES
    assert list(mcp.TOOLS) == CATALOG_NAMES
    assert mcp.SERVER_NAME == "ez-edit"
    blob = json.dumps(mcp.list_tools())
    for forbidden in ("execute_code", "telemetry", "fetch_url"):
        assert forbidden not in blob
    for name, spec in mcp.TOOLS.items():
        assert spec["description"] == mcp._TOOL_CATALOG[name]["description"]
        assert spec["inputSchema"] == mcp._TOOL_CATALOG[name]["parameters"]


def _protocol_catalog() -> dict[str, dict[str, Any]]:
    """Parse TOOL_CATALOG out of the pinned protocol file.

    Returns:
        The catalog literal.
    """
    tree = ast.parse(PROTOCOL_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        target = getattr(node, "target", None)
        if target is None and isinstance(node, ast.Assign) and node.targets:
            target = node.targets[0]
        if getattr(target, "id", "") == "TOOL_CATALOG":
            assert isinstance(node, (ast.Assign, ast.AnnAssign))
            return ast.literal_eval(node.value)  # type: ignore[arg-type]
    raise AssertionError("TOOL_CATALOG not found in protocol.py")


def test_catalog_mirror_has_no_drift_against_protocol_file() -> None:
    catalog = _protocol_catalog()
    assert catalog == mcp._TOOL_CATALOG
    assert list(catalog) == CATALOG_NAMES


def test_route_table_matches_contract_and_covers_the_catalog() -> None:
    assert mcp.ROUTES == PINNED_ROUTES
    assert set(mcp.ROUTES) == set(CATALOG_NAMES) - {"occupancy_status"}


def test_occupancy_tool_reports_mode(tmp_path: Path) -> None:
    (tmp_path / ".occupancy.json").write_text(
        json.dumps({"mode": "klein", "parked": False}), encoding="utf-8"
    )
    assert mcp.call_tool("occupancy_status", {}) == {"ok": True, "mode": "klein"}


def test_occupancy_missing_file_is_unknown(tmp_path: Path) -> None:
    assert not (tmp_path / ".occupancy.json").exists()
    assert mcp.occupancy_mode() == "unknown"


def test_occupancy_invalid_json_is_unknown(tmp_path: Path) -> None:
    (tmp_path / ".occupancy.json").write_text("not-json", encoding="utf-8")
    assert mcp.occupancy_mode() == "unknown"


def test_occupancy_non_object_is_unknown(tmp_path: Path) -> None:
    (tmp_path / ".occupancy.json").write_text("[1, 2]", encoding="utf-8")
    assert mcp.occupancy_mode() == "unknown"


def test_occupancy_blank_mode_is_unknown(tmp_path: Path) -> None:
    (tmp_path / ".occupancy.json").write_text('{"mode": "  "}', encoding="utf-8")
    assert mcp.occupancy_mode() == "unknown"


def test_occupancy_unreadable_file_is_unknown(tmp_path: Path) -> None:
    (tmp_path / ".occupancy.json").mkdir()
    assert mcp.occupancy_mode() == "unknown"


def test_occupancy_tool_reflects_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    monkeypatch.setattr(mcp, "occupancy_mode", lambda: "unknown")
    assert mcp.tool_occupancy_status({}) == {"ok": True, "mode": "unknown"}


def test_output_dir_defaults_to_host_bind(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    assert mcp._output_dir() == Path("/mnt/comfy-output")


def test_comfy_base_defaults_to_loopback_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EZ_EDIT_COMFY_URL", raising=False)
    monkeypatch.delenv("COMFY_PORT", raising=False)
    assert mcp._comfy_base() == "http://127.0.0.1:8188"


def test_comfy_base_honours_comfy_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EZ_EDIT_COMFY_URL", raising=False)
    monkeypatch.setenv("COMFY_PORT", "8199")
    assert mcp._comfy_base() == "http://127.0.0.1:8199"


def test_comfy_base_blank_port_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EZ_EDIT_COMFY_URL", raising=False)
    monkeypatch.setenv("COMFY_PORT", "  ")
    assert mcp._comfy_base() == "http://127.0.0.1:8188"


def test_comfy_base_override_trims(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EZ_EDIT_COMFY_URL", "  http://spark.local:8188/  ")
    assert mcp._comfy_base() == "http://spark.local:8188"


def test_comfy_base_blank_override_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EZ_EDIT_COMFY_URL", "   ")
    assert mcp._comfy_base() == "http://127.0.0.1:8188"


def test_get_state_calls_one_route(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true, "project": null, "enabled": true}')
    result = mcp.call_tool("edit_get_state", {"project_id": "p1"})
    assert result["ok"] is True
    assert result["enabled"] is True
    assert len(stub.requests) == 1
    request = stub.requests[0]
    assert request.full_url == "http://127.0.0.1:8188/ez_edit/state?project_id=p1"
    assert request.get_method() == "GET"
    assert request.data is None
    assert request.get_header("Accept") == "application/json"
    assert stub.timeouts == [mcp.REQUEST_TIMEOUT_S]


def test_get_state_without_query_string(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true}')
    assert mcp._call_route("edit_get_state", {}) == {"ok": True}
    assert stub.requests[0].full_url == "http://127.0.0.1:8188/ez_edit/state"


def test_job_status_gets_row(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true, "job": {"id": "j1"}}')
    result = mcp.call_tool("edit_job_status", {"job_id": "j1"})
    assert result["job"]["id"] == "j1"
    assert stub.requests[0].full_url == "http://127.0.0.1:8188/ez_edit/job?job_id=j1"


def test_job_status_requires_job_id(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true}')
    result = mcp.call_tool("edit_job_status", {"job_id": "  "})
    assert result["ok"] is False
    assert "missing required job_id" in result["error"]
    assert stub.requests == []


def test_import_posts_body(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true, "clip": {"id": "c1"}}')
    result = mcp.call_tool(
        "edit_import", {"path": "videos/a.mp4", "label": "A", "track": "2"}
    )
    assert result["clip"]["id"] == "c1"
    request = stub.requests[0]
    assert request.full_url == "http://127.0.0.1:8188/ez_edit/import"
    assert request.get_method() == "POST"
    assert request.get_header("Content-type") == "application/json"
    assert _body(request) == {"path": "videos/a.mp4", "label": "A", "track": 2}


def test_import_bad_track_uses_default(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true}')
    mcp.call_tool("edit_import", {"path": "a", "track": None})
    assert _body(stub.requests[0])["track"] == 0
    mcp.call_tool("edit_import", {"path": "a", "track": "nope"})
    assert _body(stub.requests[1])["track"] == 0


def test_import_requires_path(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true}')
    result = mcp.call_tool("edit_import", {})
    assert result["ok"] is False
    assert "missing required path" in result["error"]
    assert stub.requests == []


def test_apply_ops_posts_ops_list(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true, "project": {"id": "p1"}}')
    ops = [{"op": "set_title", "args": {"title": "T"}}]
    result = mcp.call_tool("edit_apply_ops", {"project_id": "p1", "ops": ops})
    assert result["project"]["id"] == "p1"
    assert _body(stub.requests[0]) == {"project_id": "p1", "ops": ops}


def test_apply_ops_rejects_non_list(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true}')
    result = mcp.call_tool("edit_apply_ops", {"ops": "nope"})
    assert result["ok"] is False
    assert "missing required ops" in result["error"]
    assert stub.requests == []


def test_apply_ops_requires_ops(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true}')
    result = mcp.call_tool("edit_apply_ops", {"ops": []})
    assert result["ok"] is False
    assert "missing required ops" in result["error"]
    assert stub.requests == []


def test_render_posts_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true, "job": {"state": "pending"}}')
    result = mcp.call_tool(
        "edit_render", {"mode": "server", "project_id": "p1", "client_id": "c"}
    )
    assert result["job"]["state"] == "pending"
    assert _body(stub.requests[0]) == {
        "project_id": "p1",
        "mode": "server",
        "client_id": "c",
    }


def test_render_requires_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true}')
    result = mcp.call_tool("edit_render", {})
    assert result["ok"] is False
    assert "missing required mode" in result["error"]
    assert stub.requests == []


def test_generate_clip_posts_numbers(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true, "job": {"id": "j2"}}')
    result = mcp.call_tool("edit_generate_clip", {"prompt": "a cat", "fps": 30})
    assert result["job"]["id"] == "j2"
    assert _body(stub.requests[0]) == {
        "prompt": "a cat",
        "duration_s": 5.0,
        "fps": 30.0,
    }


def test_generate_clip_bad_numbers_use_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true}')
    mcp.call_tool("edit_generate_clip", {"prompt": "p", "duration_s": "x", "fps": None})
    body = _body(stub.requests[0])
    assert body["duration_s"] == 5.0
    assert body["fps"] == 24.0


def test_generate_clip_requires_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true}')
    result = mcp.call_tool("edit_generate_clip", {})
    assert result["ok"] is False
    assert "missing required prompt" in result["error"]
    assert stub.requests == []


def test_export_edl_posts(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true, "path": "edit/p1.edl.json"}')
    result = mcp.call_tool("edit_export_edl", {"project_id": "p1"})
    assert result["path"] == "edit/p1.edl.json"
    assert _body(stub.requests[0]) == {"project_id": "p1", "format": "json"}


def test_export_edl_passes_the_cmx_format(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true, "path": "edit/p1.edl"}')
    result = mcp.call_tool("edit_export_edl", {"project_id": "p1", "format": "cmx"})
    assert result["path"] == "edit/p1.edl"
    assert _body(stub.requests[0]) == {"project_id": "p1", "format": "cmx"}


def test_list_projects_gets_the_index(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _install(monkeypatch, '{"ok": true, "projects": [{"id": "p1"}]}')
    result = mcp.call_tool("edit_list_projects", {})
    rows = result["projects"]
    assert isinstance(rows, list)
    row = rows[0]
    assert isinstance(row, dict)
    assert row["id"] == "p1"
    assert stub.requests[0].full_url == "http://127.0.0.1:8188/ez_edit/projects"


def test_unreachable_comfy_is_an_error_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, urllib.error.URLError("connection refused"))
    result = mcp.call_tool("edit_export_edl", {})
    assert result["ok"] is False
    assert result["error"].startswith(mcp.UNREACHABLE_PREFIX)


def test_timeout_is_an_error_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, TimeoutError("slow"))
    assert mcp.call_tool("edit_export_edl", {})["ok"] is False


def test_oserror_is_an_error_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, OSError("no route to host"))
    assert mcp.call_tool("edit_export_edl", {})["ok"] is False


def test_read_value_error_is_an_error_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, ValueError("bad read"))
    assert mcp.call_tool("edit_export_edl", {})["ok"] is False


def test_invalid_json_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, "<html>nope</html>")
    result = mcp.call_tool("edit_export_edl", {})
    assert result == {"ok": False, "error": mcp.INVALID_JSON_ERROR}


def test_non_object_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, "[1, 2]")
    result = mcp.call_tool("edit_export_edl", {})
    assert result == {"ok": False, "error": mcp.NON_OBJECT_ERROR}


def test_http_error_keeps_route_error_text(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _http_error(403, '{"ok": true, "error": "disabled"}'))
    result = mcp.call_tool("edit_export_edl", {})
    assert result["ok"] is False
    assert result["error"] == "disabled"


def test_http_error_without_error_key_uses_status(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _http_error(404, '{"detail": "no project"}'))
    result = mcp.call_tool("edit_export_edl", {})
    assert result["ok"] is False
    assert result["error"] == "/ez_edit/export_edl -> HTTP 404"
    assert result["detail"] == "no project"


def test_http_error_without_json_body(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _http_error(500, "boom", reason="Server Error"))
    result = mcp.call_tool("edit_export_edl", {})
    assert result == {
        "ok": False,
        "error": "/ez_edit/export_edl -> HTTP 500 Server Error",
    }


def test_http_error_with_empty_object_body(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _http_error(502, "{}", reason="Bad Gateway"))
    result = mcp.call_tool("edit_export_edl", {})
    assert result["error"] == "/ez_edit/export_edl -> HTTP 502 Bad Gateway"


def test_http_error_with_dead_body(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, _http_error(503, _RaisingBody(), reason="Unavailable"))
    result = mcp.call_tool("edit_export_edl", {})
    assert result["error"] == "/ez_edit/export_edl -> HTTP 503 Unavailable"


def test_urlopen_seam_delegates_to_urllib(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, float]] = []
    request = urllib.request.Request("http://127.0.0.1:8188/ez_edit/state")

    def fake(request_arg: urllib.request.Request, timeout: float) -> str:
        calls.append((request_arg.full_url, timeout))
        return "opened"

    monkeypatch.setattr("urllib.request.urlopen", fake)
    assert mcp._urlopen(request, 1.5) == "opened"
    assert calls == [("http://127.0.0.1:8188/ez_edit/state", 1.5)]


def test_is_empty_branches() -> None:
    assert mcp._is_empty(None) is True
    assert mcp._is_empty("   ") is True
    assert mcp._is_empty([]) is True
    assert mcp._is_empty({}) is True
    assert mcp._is_empty("x") is False
    assert mcp._is_empty(0) is False
    assert mcp._is_empty([{}]) is False


def test_missing_required_for_unknown_tool_is_silent() -> None:
    assert mcp._missing_required("nope", {}) == []
    assert mcp.call_tool("execute_code", {"code": "1"})["ok"] is False
    assert "unknown" in mcp.call_tool("execute_code")["error"]


def test_missing_required_empty_parameters() -> None:
    saved = dict(mcp._TOOL_CATALOG)
    try:
        mcp._TOOL_CATALOG["probe"] = {"description": "x", "parameters": {}}
        assert mcp._missing_required("probe", {}) == []
    finally:
        mcp._TOOL_CATALOG.clear()
        mcp._TOOL_CATALOG.update(saved)


def test_handle_rpc_identity_and_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    init = mcp.handle_rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init is not None
    assert init["result"]["serverInfo"]["name"] == "ez-edit"
    ping = mcp.handle_rpc({"jsonrpc": "2.0", "id": 2, "method": "ping"})
    assert ping is not None
    assert ping["result"] == {}
    listed = mcp.handle_rpc({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
    assert listed is not None
    assert [row["name"] for row in listed["result"]["tools"]] == CATALOG_NAMES
    assert mcp.handle_rpc({"method": "notifications/initialized"}) is None
    assert mcp.handle_rpc({"method": "nope"}) is None
    missing = mcp.handle_rpc({"jsonrpc": "2.0", "id": 4, "method": "nope"})
    assert missing is not None
    assert missing["error"]["code"] == -32601

    stub = _install(monkeypatch, '{"ok": true, "job": {"id": "j9"}}')
    called = mcp.handle_rpc(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "edit_job_status", "arguments": {"job_id": "j9"}},
        }
    )
    assert called is not None
    assert called["result"]["isError"] is False
    text = json.loads(called["result"]["content"][0]["text"])
    assert text["job"]["id"] == "j9"
    assert len(stub.requests) == 1

    refused = mcp.handle_rpc(
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {"name": "edit_render", "arguments": {}},
        }
    )
    assert refused is not None
    assert refused["result"]["isError"] is True


def test_serve_stdio_replies_to_ping(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        sys, "stdin", io.StringIO('{"jsonrpc":"2.0","id":1,"method":"ping"}\n\nbad\n')
    )
    mcp.serve_stdio()
    out = capsys.readouterr().out.strip()
    assert json.loads(out)["id"] == 1


def test_main_help_and_list_tools(capsys: pytest.CaptureFixture[str]) -> None:
    assert mcp.main(["--help"]) == 0
    err = capsys.readouterr().err
    assert "edit_mcp.py" in err
    assert "no execute_code" in err
    assert mcp.main(["--list-tools"]) == 0
    out = capsys.readouterr().out
    assert "edit_get_state" in out
    assert "edit_export_edl" in out


def test_main_call_paths(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install(monkeypatch, '{"ok": true, "job": {"id": "j1"}}')
    assert mcp.main(["--call", "edit_job_status", '{"job_id":"j1"}']) == 0
    assert json.loads(capsys.readouterr().out)["job"]["id"] == "j1"
    assert mcp.main(["--call"]) == 1
    assert mcp.main(["--call", "edit_import"]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False
    assert mcp.main(["--nope"]) == 1


def test_main_stdio_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert mcp.main([]) == 0
    monkeypatch.setattr(sys, "argv", ["edit_mcp.py", "--stdio"])
    assert mcp.main(None) == 0
    assert mcp.main(["stdio"]) == 0


def test_main_guard_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["edit_mcp.py", "--list-tools"])
    with pytest.raises(SystemExit) as caught:
        runpy.run_path(str(LIB / "edit_mcp.py"), run_name="__main__")
    assert caught.value.code == 0
    assert "occupancy_status" in capsys.readouterr().out

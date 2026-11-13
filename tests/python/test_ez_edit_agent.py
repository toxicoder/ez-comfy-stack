"""Hermetic tests for the ez_edit editing agent (no network, no GPU, no Comfy).

Every socket call goes through the injectable ``AgentLLM._urlopen`` seam and
every completion through the scripted :class:`FakeLLM`, so the OpenAI wire
shape, the occupancy XOR gate, the tool loop, the trace rows, and the step
budget are all asserted offline. ``COMFY_OUTPUT_DIR`` is pinned to ``tmp_path``
by an autouse fixture, so the sidecar reads never touch a real output dir.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from ez_common import Json, JsonMap, JsonObject
from ez_edit import agent, protocol
from ez_edit.agent import AgentLLM, AgentRefused
from ez_edit.protocol import ChatMessage


@pytest.fixture(autouse=True)
def _isolated_agent_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Pin the module to tmp: cached prompt reset, idle sidecar, clean env.

    Args:
        tmp_path: pytest temp dir used as ``COMFY_OUTPUT_DIR``.
        monkeypatch: pytest env mutator.
    """
    agent.reset_agent_state_for_tests()
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    _write_occupancy(tmp_path, "idle")
    for key in (
        protocol.ENV_LLM_URL,
        protocol.ENV_MODEL,
        protocol.ENV_TIMEOUT_S,
        protocol.ENV_MAX_STEPS,
        "MODELS_ROOT",
    ):
        monkeypatch.delenv(key, raising=False)
    yield
    agent.reset_agent_state_for_tests()


# --- test doubles -----------------------------------------------------------


def _write_occupancy(
    root: Path,
    mode: str | None,
    *,
    holders: dict[str, int] | None = None,
    pids_alive: dict[str, bool] | None = None,
) -> Path:
    """Write (or remove) ``${COMFY_OUTPUT_DIR}/.occupancy.json``.

    Args:
        root: Value for ``COMFY_OUTPUT_DIR``.
        mode: Occupancy mode, or None to leave the file absent.
        holders: Holder PID fields to record (``blender_pid`` / ``mcp_pid`` /
            ``llm_pid``); a desk with none of them names no live claim.
        pids_alive: Host-stamped liveness map; ``None`` simulates a record
            written before the field existed (fail-closed).

    Returns:
        The sidecar path (it may not exist when mode is None).
    """
    path = root / agent.OCCUPANCY_FILE_NAME
    if mode is None:
        path.unlink(missing_ok=True)
        return path
    payload: dict[str, object] = {"mode": mode}
    payload.update(holders or {})
    if pids_alive is not None:
        payload["pids_alive"] = dict(pids_alive)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _env(root: Path, mode: str = "idle", **extra: str) -> dict[str, str]:
    """Build an injected environ with a sidecar under ``root``.

    Args:
        root: Value for ``COMFY_OUTPUT_DIR``.
        mode: Occupancy mode written into the sidecar.
        **extra: Additional environment keys.

    Returns:
        Mapping for the injectable ``environ`` parameters.
    """
    _write_occupancy(root, mode)
    env: dict[str, str] = {"COMFY_OUTPUT_DIR": str(root)}
    env.update(extra)
    return env


def _assistant(
    content: str = "", tool_calls: list[dict[str, Any]] | None = None
) -> ChatMessage:
    """Build one assistant message for the scripted queue.

    Args:
        content: Assistant text.
        tool_calls: Raw tool_call objects, omitted when None.

    Returns:
        Chat message shaped like the OpenAI wire.
    """
    message = ChatMessage(role="assistant", content=content)
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    return message


def _tool_call(call_id: str, name: str, arguments: Any) -> dict[str, Any]:
    """Build one OpenAI tool_call object.

    Args:
        call_id: Tool call id (threaded back in the tool message).
        name: Function name.
        arguments: Dict (JSON-encoded) or a pre-encoded string.

    Returns:
        Tool call dict.
    """
    args = arguments if isinstance(arguments, str) else json.dumps(arguments)
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": args},
    }


def _raw(value: object) -> Any:
    """Loosen one value's static type so tests can feed malformed shapes.

    Args:
        value: Value to hand to the module as ``Any``.

    Returns:
        The same value.
    """
    return value


def _function(spec: JsonMap) -> JsonObject:
    """Narrow one tool spec's ``function`` block.

    Args:
        spec: OpenAI-shaped tool payload the loop built.

    Returns:
        The function object.

    Raises:
        AssertionError: The spec has no function object.
    """
    block = spec["function"]
    assert isinstance(block, dict)
    return block


def _function_name(spec: JsonMap) -> str:
    """Read one tool spec's function name.

    Args:
        spec: OpenAI-shaped tool payload the loop built.

    Returns:
        The ``function.name`` field.

    Raises:
        AssertionError: The name is missing or not a string.
    """
    name = _function(spec)["name"]
    assert isinstance(name, str)
    return name


def _parameters(spec: JsonMap) -> Json:
    """Read one tool spec's JSON-schema block.

    Args:
        spec: OpenAI-shaped tool payload the loop built.

    Returns:
        The ``function.parameters`` value.
    """
    return _function(spec)["parameters"]


class FakeLLM:
    """Scripted :class:`~ez_edit.agent.CompletionClient` that never dials out."""

    def __init__(self, answers: list[ChatMessage], *, repeat_last: bool = False) -> None:
        """Load the queue.

        Args:
            answers: Messages returned in order.
            repeat_last: Keep returning the final answer once the queue drains
                (used to walk the loop into budget exhaustion).
        """
        self._answers = list(answers)
        self._repeat_last = repeat_last
        self._last: ChatMessage | None = None
        self.seen: list[list[dict[str, Any]]] = []
        self.tool_payloads: list[list[dict[str, Any]] | None] = []

    def chat(
        self, messages: list[ChatMessage], tools: list[dict[str, Any]] | None = None
    ) -> ChatMessage:
        """Return the next scripted answer, recording what the loop sent.

        Args:
            messages: Transcript the loop built (system prompt first).
            tools: Tool payload the loop built.

        Returns:
            Next assistant message, or a sentinel once the queue is drained.
        """
        self.seen.append([dict(row) for row in messages])
        self.tool_payloads.append(tools)
        if self._answers:
            self._last = self._answers.pop(0)
            return self._last
        if self._repeat_last and self._last is not None:
            return self._last
        return _assistant("(queue exhausted)")


class _Response:
    """Context-managed stand-in for an ``urllib`` HTTP response."""

    def __init__(self, payload: bytes) -> None:
        """Hold the body.

        Args:
            payload: Response bytes.
        """
        self._payload = payload

    def read(self) -> bytes:
        """Return the whole body.

        Returns:
            Response bytes.
        """
        return self._payload

    def __enter__(self) -> _Response:
        """Enter the context manager.

        Returns:
            This response.
        """
        return self

    def __exit__(self, *_exc: object) -> None:
        """Leave the context manager (nothing to close)."""
        return None


def _completion_body(
    content: str | None = "", tool_calls: list[dict[str, Any]] | None = None
) -> bytes:
    """Encode one ``/chat/completions`` body for the urlopen spy.

    Args:
        content: Assistant text, or None to omit the field entirely.
        tool_calls: Raw tool_call objects, omitted when None.

    Returns:
        UTF-8 JSON bytes.
    """
    message: dict[str, Any] = {"role": "assistant"}
    if content is not None:
        message["content"] = content
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    return json.dumps({"choices": [{"message": message}]}).encode("utf-8")


class UrlopenSpy:
    """Stand-in for :meth:`ez_edit.agent.AgentLLM._urlopen`.

    Installed with ``monkeypatch.setattr(AgentLLM, "_urlopen", spy)``; a plain
    object is not a descriptor, so the client instance is not passed in.
    """

    def __init__(self, *replies: bytes | Exception) -> None:
        """Load the replay queue.

        Args:
            *replies: Response bodies, or exceptions to raise.
        """
        self._replies: list[bytes | Exception] = list(replies)
        self.requests: list[urllib.request.Request] = []
        self.timeouts: list[float] = []

    def __call__(
        self, request: urllib.request.Request, timeout: float
    ) -> _Response:
        """Record the request and replay the next body.

        Args:
            request: Prepared POST request.
            timeout: Socket timeout the client asked for.

        Returns:
            Fake response carrying the next body.

        Raises:
            Exception: Whatever the queue held for this call.
        """
        self.requests.append(request)
        self.timeouts.append(timeout)
        reply = self._replies.pop(0) if self._replies else b'{"choices": []}'
        if isinstance(reply, BaseException):
            raise reply
        return _Response(reply)


# --- config readers ---------------------------------------------------------


def test_in_container_and_agent_base_url(tmp_path: Path) -> None:
    """Container markers pick the host gateway; the env url wins and is trimmed."""
    marker = tmp_path / ".dockerenv"
    marker.write_text("", encoding="utf-8")
    absent = tmp_path / "no-dockerenv"
    assert agent.in_container({}, marker) is True
    assert agent.in_container({"MODELS_ROOT": " /models "}, absent) is True
    assert agent.in_container({"MODELS_ROOT": "models"}, absent) is False
    assert agent.in_container({}, absent) is False

    inside = agent.agent_base_url({}, marker)
    outside = agent.agent_base_url({"MODELS_ROOT": "models"}, absent)
    assert inside == f"http://host.docker.internal:{protocol.DEFAULT_LLM_URL_PORT}/v1"
    assert outside == f"http://127.0.0.1:{protocol.DEFAULT_LLM_URL_PORT}/v1"
    assert (
        agent.agent_base_url({protocol.ENV_LLM_URL: "http://gpu:1/v1//"}, marker)
        == "http://gpu:1/v1"
    )


def test_agent_base_url_reads_process_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No injected mapping falls back to ``os.environ``."""
    monkeypatch.setenv(protocol.ENV_LLM_URL, "http://from-process:30001/v1")
    assert agent.agent_base_url() == "http://from-process:30001/v1"


def test_model_id_timeout_and_max_steps_env(tmp_path: Path) -> None:
    """Env overrides win; garbage and non-positive values fall back."""
    assert agent.model_id(_env(tmp_path)) == protocol.DEFAULT_MODEL
    assert agent.model_id({"EZ_AGENT_MODEL": " Qwen-Pinned "}) == "Qwen-Pinned"

    default_timeout = float(protocol.DEFAULT_TIMEOUT_S)
    assert agent.timeout_s(_env(tmp_path)) == default_timeout
    assert agent.timeout_s({protocol.ENV_TIMEOUT_S: "2.5"}) == 2.5
    assert agent.timeout_s({protocol.ENV_TIMEOUT_S: "soon"}) == default_timeout
    assert agent.timeout_s({protocol.ENV_TIMEOUT_S: "0"}) == default_timeout
    assert agent.timeout_s({protocol.ENV_TIMEOUT_S: "-3"}) == default_timeout

    assert agent.max_steps(_env(tmp_path)) == int(protocol.DEFAULT_MAX_STEPS)
    assert agent.max_steps({protocol.ENV_MAX_STEPS: "3"}) == 3
    assert agent.max_steps({protocol.ENV_MAX_STEPS: "many"}) == int(
        protocol.DEFAULT_MAX_STEPS
    )
    assert agent.max_steps({protocol.ENV_MAX_STEPS: "-1"}) == int(
        protocol.DEFAULT_MAX_STEPS
    )


def test_occupancy_path(tmp_path: Path) -> None:
    """The sidecar path follows ``COMFY_OUTPUT_DIR`` and the container default."""
    assert agent.occupancy_path(_env(tmp_path)) == tmp_path / ".occupancy.json"
    assert agent.occupancy_path({}) == Path(agent.DEFAULT_OUTPUT_DIR) / (
        ".occupancy.json"
    )
    assert agent.occupancy_path(_env(tmp_path), filename="other.json") == (
        tmp_path / "other.json"
    )


# --- occupancy gate ---------------------------------------------------------


def test_read_occupancy_mode_from_file(tmp_path: Path) -> None:
    """Missing, corrupt, and non-object files all read as ``unknown``."""
    _write_occupancy(
        tmp_path, "llm-desk", holders={"llm_pid": 4242}, pids_alive={"llm_pid": True}
    )
    assert agent.read_occupancy_mode() == "llm-desk"
    assert agent.read_occupancy_mode(environ=_env(tmp_path, "idle")) == "idle"

    sidecar = _write_occupancy(tmp_path, None)
    assert agent.read_occupancy_mode(sidecar) == "unknown"
    sidecar.write_text("{not json", encoding="utf-8")
    assert agent.read_occupancy_mode(sidecar) == "unknown"
    sidecar.write_text('["mode"]', encoding="utf-8")
    assert agent.read_occupancy_mode(sidecar) == "unknown"
    sidecar.write_text(json.dumps({"mode": "   "}), encoding="utf-8")
    assert agent.read_occupancy_mode(sidecar) == "unknown"


def test_read_occupancy_mode_collapses_an_orphaned_desk(tmp_path: Path) -> None:
    """A desk whose sidecars all died is no claim; a live one keeps its mode."""
    _write_occupancy(
        tmp_path,
        "blender-desk",
        holders={"blender_pid": 4242, "mcp_pid": 4243},
        pids_alive={"blender_pid": False, "mcp_pid": False},
    )
    assert agent.read_occupancy_mode() == "idle"
    _write_occupancy(
        tmp_path,
        "blender-desk",
        holders={"blender_pid": 4242, "mcp_pid": 0},
        pids_alive={"blender_pid": True, "mcp_pid": False},
    )
    assert agent.read_occupancy_mode() == "blender-desk"


def test_read_occupancy_mode_injected_reader() -> None:
    """The reader seam wins over the file and blanks normalize to unknown."""
    calls: list[Path] = []

    def _reader(path: Path) -> str:
        calls.append(path)
        return " wan "

    assert agent.read_occupancy_mode(Path("/unused/x.json"), reader=_reader) == "wan"
    assert calls == [Path("/unused/x.json")]
    assert (
        agent.read_occupancy_mode(Path("/unused/x.json"), reader=lambda _p: "")
        == "unknown"
    )


@pytest.mark.parametrize("mode", sorted(protocol.SIDECAR_OK_OCCUPANCY))
def test_require_occupancy_allows_sidecar_modes(
    tmp_path: Path, mode: str
) -> None:
    """Desk, idle, and unknown modes let the co-tenant run.

    A PID-less desk record is an orphan the resolver releases to ``idle``, so
    the assertion is membership of the allow-set rather than the raw mode.
    """
    assert agent.require_occupancy(_write_occupancy(tmp_path, mode)) in (
        protocol.SIDECAR_OK_OCCUPANCY
    )


@pytest.mark.parametrize(
    ("mode", "pid_key"), [("blender-desk", "blender_pid"), ("llm-desk", "llm_pid")]
)
def test_require_occupancy_allows_a_live_desk(
    tmp_path: Path, mode: str, pid_key: str
) -> None:
    """A desk with its sidecar still running keeps its mode and stays allowed."""
    sidecar = _write_occupancy(
        tmp_path, mode, holders={pid_key: 4242}, pids_alive={pid_key: True}
    )
    assert agent.require_occupancy(sidecar) == mode


@pytest.mark.parametrize("mode", ["wan", "ltx", "trellis", "klein", "busy"])
def test_require_occupancy_refuses_heavy_modes(
    tmp_path: Path, mode: str
) -> None:
    """A heavy GPU job refuses the agent with :class:`AgentRefused`."""
    with pytest.raises(AgentRefused) as caught:
        agent.require_occupancy(_write_occupancy(tmp_path, mode))
    assert f"occupancy is {mode}" in str(caught.value)
    assert "bazelisk run //:manage -- occupancy enter idle --yes" in str(caught.value)


def test_require_occupancy_missing_file_passes(tmp_path: Path) -> None:
    """First run (no sidecar yet) reads unknown and is allowed."""
    sidecar = _write_occupancy(tmp_path, None)
    assert agent.require_occupancy(sidecar) == "unknown"


# --- tool payload -----------------------------------------------------------


def test_build_tools_uses_openai_function_shape() -> None:
    """Every catalog entry is a deduped ``{"type":"function", ...}`` spec."""
    tools = agent.build_tools()
    names = {_function_name(spec) for spec in tools}
    assert names == set(protocol.TOOL_CATALOG)
    for spec in tools:
        assert spec["type"] == "function"
        assert set(_function(spec)) == {"name", "description", "parameters"}
        assert isinstance(_parameters(spec), dict)


def test_build_tools_merges_extras_and_drops_junk() -> None:
    """Extras accept catalog-shaped and OpenAI-shaped entries; junk is dropped."""
    tools = agent.build_tools(
        _raw(
            [
                {"name": "local__desk__open", "description": "open"},
                {
                    "type": "function",
                    "function": {
                        "name": "local__desk__save",
                        "description": "save",
                        "parameters": {"type": "object"},
                    },
                },
                {"name": "edit_get_state", "description": "shadow"},
                {"name": "   ", "description": "blank"},
                "not-a-tool",
            ]
        )
    )
    names = [_function_name(spec) for spec in tools]
    assert "local__desk__open" in names
    assert "local__desk__save" in names
    assert names.count("edit_get_state") == 1
    assert "" not in names
    open_spec = next(s for s in tools if _function_name(s) == "local__desk__open")
    assert _parameters(open_spec) == {}
    save_spec = next(s for s in tools if _function_name(s) == "local__desk__save")
    assert _parameters(save_spec) == {"type": "object"}


def test_tool_names_skips_malformed_specs() -> None:
    """Specs without a usable function block contribute no name."""
    names = agent.tool_names(
        _raw(
            [
                {"type": "function", "function": {"name": " edit_get_state "}},
                {"type": "function", "function": {"name": "  "}},
                {"type": "function", "function": "nope"},
                {"type": "function"},
            ]
        )
    )
    assert names == {"edit_get_state"}


# --- system prompt ----------------------------------------------------------


def test_system_prompt_comes_from_the_pack_file() -> None:
    """The prompt file is ASCII, non-empty, and cached across calls."""
    text = agent.system_prompt_path().read_text(encoding="utf-8")
    assert agent.system_prompt_path().name == "agent_system.txt"
    assert agent.system_prompt() == text.strip()
    assert agent.system_prompt() is agent.system_prompt()
    assert all(ord(char) < 128 for char in text)


def test_system_prompt_falls_back_when_file_is_gone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing or blank prompt file keeps the pack usable."""
    missing = tmp_path / "nope.txt"
    monkeypatch.setattr(agent, "system_prompt_path", lambda: missing)
    agent.reset_agent_state_for_tests()
    assert agent.system_prompt() == agent.FALLBACK_SYSTEM_PROMPT

    blank = tmp_path / "blank.txt"
    blank.write_text("   \n", encoding="utf-8")
    monkeypatch.setattr(agent, "system_prompt_path", lambda: blank)
    agent.reset_agent_state_for_tests()
    assert agent.system_prompt() == agent.FALLBACK_SYSTEM_PROMPT


# --- AgentLLM wire ----------------------------------------------------------


def test_agent_llm_resolves_url_model_and_timeout(tmp_path: Path) -> None:
    """Overrides win over the environment; the default client follows env keys."""
    env = _env(tmp_path, **{protocol.ENV_MODEL: " Qwen-Env "})
    llm = AgentLLM(base_url="http://a.test:9/v1//", model="Qwen-X", timeout=1.25, environ=env)
    assert llm._url() == "http://a.test:9/v1/chat/completions"
    assert llm._model() == "Qwen-X"
    assert llm._timeout() == 1.25

    bare = AgentLLM(environ={**env, protocol.ENV_LLM_URL: "http://b.test/v1"})
    assert bare._url() == "http://b.test/v1/chat/completions"
    assert bare._model() == "Qwen-Env"
    assert bare._timeout() == float(protocol.DEFAULT_TIMEOUT_S)
    timed = AgentLLM(environ={**env, protocol.ENV_TIMEOUT_S: "4"})
    assert timed._timeout() == 4.0


def test_urlopen_indirection_delegates_to_urllib(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The house seam is the only place a socket would open."""
    seen: dict[str, object] = {}

    def _open(request: urllib.request.Request, timeout: float) -> _Response:
        seen["request"] = request
        seen["timeout"] = timeout
        return _Response(b'{"ok": true}')

    monkeypatch.setattr(urllib.request, "urlopen", _open)
    request = urllib.request.Request(
        "http://x.test/v1/chat/completions", data=b"{}", method="POST"
    )
    response = AgentLLM()._urlopen(request, 3.5)
    assert isinstance(response, _Response)
    assert response.read() == b'{"ok": true}'
    assert seen["request"] is request
    assert seen["timeout"] == 3.5


def test_chat_posts_openai_shaped_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """URL, headers, and body match the pinned completion contract."""
    monkeypatch.delenv(protocol.ENV_MODEL, raising=False)
    env = _env(tmp_path, **{protocol.ENV_MODEL: "Qwen-Test"})
    spy = UrlopenSpy(_completion_body(content="hello"))
    monkeypatch.setattr(AgentLLM, "_urlopen", spy)
    llm = AgentLLM(base_url="http://agent.test:30001/v1/", environ=env)

    messages: list[ChatMessage] = [
        ChatMessage(role="system", content=agent.system_prompt()),
        ChatMessage(role="user", content="trim clip c1"),
    ]
    answer = llm.chat(messages, agent.build_tools())

    assert answer.get("content") == "hello"
    assert answer.get("tool_calls") == []
    request = spy.requests[0]
    assert spy.timeouts == [float(protocol.DEFAULT_TIMEOUT_S)]
    assert request.full_url == "http://agent.test:30001/v1/chat/completions"
    assert request.get_method() == "POST"
    assert request.get_header("Content-type") == "application/json"
    assert request.get_header("Accept") == "application/json"
    body = json.loads((cast("bytes | None", request.data) or b"").decode("utf-8"))
    assert body["model"] == "Qwen-Test"
    assert body["tool_choice"] == "auto"
    assert body["stream"] is False
    assert body["messages"] == messages
    assert body["messages"][0]["content"] == agent.system_prompt()
    assert {spec["function"]["name"] for spec in body["tools"]} == set(
        protocol.TOOL_CATALOG
    )


def test_chat_refuses_before_opening_a_socket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The occupancy gate runs ahead of ``_urlopen``."""
    spy = UrlopenSpy(_completion_body(content="never"))
    monkeypatch.setattr(AgentLLM, "_urlopen", spy)
    llm = AgentLLM(
        base_url="http://agent.test:30001/v1", environ=_env(tmp_path, "wan")
    )
    with pytest.raises(AgentRefused):
        llm.chat([ChatMessage(role="user", content="hi")], None)
    assert spy.requests == []


def test_chat_wire_failure_becomes_a_reply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A refused connection comes back as an assistant message, not an raise."""
    spy = UrlopenSpy(urllib.error.URLError("connection refused"))
    monkeypatch.setattr(AgentLLM, "_urlopen", spy)
    llm = AgentLLM(base_url="http://agent.test:30001/v1", environ=_env(tmp_path))
    answer = llm.chat([ChatMessage(role="user", content="hi")])
    unreachable = answer.get("content") or ""
    assert unreachable.startswith(agent.UNREACHABLE_PREFIX)
    assert "connection refused" in unreachable
    assert answer.get("tool_calls") == []


@pytest.mark.parametrize(
    ("raw", "content", "calls"),
    [
        (b'{"choices":[{"message":{"content":"hi"}}]}', "hi", []),
        (b"not json", "agent LLM returned invalid JSON", []),
        (b"[1, 2]", "agent LLM returned no choices", []),
        (b'{"choices": "nope"}', "agent LLM returned no choices", []),
        (b'{"choices": []}', "agent LLM returned no choices", []),
        (b'{"choices": ["nope"]}', "agent LLM returned no choices", []),
        (b'{"choices": [{"message": "hi"}]}', "", []),
        (b'{"choices": [{"message": {}}]}', "", []),
        (
            b'{"choices":[{"message":{"content":null,"tool_calls":"nope"}}]}',
            "",
            [],
        ),
    ],
)
def test_parse_completion_shapes(
    raw: bytes, content: str, calls: list[dict[str, Any]]
) -> None:
    """Every malformed completion body degrades to a readable assistant row."""
    parsed = agent._parse_completion(raw)
    assert parsed.get("role") == "assistant"
    assert parsed.get("content") == content
    assert parsed.get("tool_calls") == calls


def test_parse_completion_keeps_tool_calls() -> None:
    """A well-formed tool_call list survives untouched for the loop."""
    call = _tool_call("call_1", "edit_get_state", {"project_id": "p"})
    parsed = agent._parse_completion(_completion_body("one sec", [call]))
    assert parsed.get("content") == "one sec"
    assert parsed.get("tool_calls") == [call]


# --- argument parsing -------------------------------------------------------


def test_parse_call_accepts_every_arguments_shape() -> None:
    """Dict args, JSON strings, empty strings, and missing args all parse."""
    dict_call = agent._parse_call(
        {"id": "a", "function": {"name": "edit_get_state", "arguments": {"x": 1}}},
        1,
        0,
    )
    assert (dict_call.call_id, dict_call.name, dict_call.args, dict_call.error) == (
        "a",
        "edit_get_state",
        {"x": 1},
        "",
    )
    str_call = agent._parse_call(
        {"id": "b", "function": {"name": "n", "arguments": '{"y": 2}'}}, 2, 1
    )
    assert (str_call.call_id, str_call.args, str_call.error) == ("b", {"y": 2}, "")
    empty_call = agent._parse_call(
        {"id": "c", "function": {"name": "n", "arguments": ""}}, 3, 2
    )
    assert (empty_call.args, empty_call.error) == ({}, "")
    missing_call = agent._parse_call({"name": "n", "args": {"z": 3}}, 4, 0)
    assert (missing_call.call_id, missing_call.name, missing_call.args) == (
        "call_4_0",
        "n",
        {"z": 3},
    )


@pytest.mark.parametrize(
    ("arguments", "error"),
    [
        ("{oops", "arguments are not valid JSON"),
        ("[1, 2]", "arguments must be a JSON object"),
        (5, "arguments must be a JSON object"),
    ],
)
def test_parse_call_reports_bad_arguments(arguments: Any, error: str) -> None:
    """Unusable arguments carry an error string instead of crashing the loop."""
    call = agent._parse_call(
        _raw({"id": "x", "function": {"name": "n", "arguments": arguments}}), 1, 0
    )
    assert call.args == {}
    assert call.error == error


# --- run_turn ---------------------------------------------------------------


def test_run_turn_plain_reply_builds_transcript() -> None:
    """One answer with no tool calls ends the turn with the system prompt first."""
    llm = FakeLLM([_assistant("trimmed c1")])
    out = agent.run_turn("trim clip c1", llm=llm)

    assert out["reply"] == "trimmed c1"
    assert out["trace"] == []
    assert [row.get("role") for row in out["history"]] == ["user", "assistant"]
    assert out["history"][1].get("content") == "trimmed c1"
    first = llm.seen[0]
    assert first[0] == {"role": "system", "content": agent.system_prompt()}
    assert first[1] == {"role": "user", "content": "trim clip c1"}
    assert first[0]["content"] == agent.system_prompt_path().read_text(
        encoding="utf-8"
    ).strip()


def test_run_turn_falls_back_when_content_is_empty_or_none() -> None:
    """A contentless answer still returns a readable reply."""
    empty = agent.run_turn("hi", llm=FakeLLM([_assistant("")]))
    assert empty["reply"] == agent.EMPTY_REPLY
    assert empty["history"][-1].get("content") == agent.EMPTY_REPLY

    missing = agent.run_turn("hi", llm=FakeLLM([ChatMessage(role="assistant")]))
    assert missing["reply"] == agent.EMPTY_REPLY


def test_run_turn_non_string_user_text_is_coerced() -> None:
    """The panel may hand over a number; the transcript stays text."""
    out = agent.run_turn(_raw(7), llm=FakeLLM([_assistant("ok")]))
    assert out["history"][0] == {"role": "user", "content": "7"}


def test_run_turn_threads_tool_call_ids_across_steps() -> None:
    """Multi-step loop: ids, order, trace rows, and tool messages line up."""
    llm = FakeLLM(
        [
            _assistant(
                "looking",
                tool_calls=cast(
                    "list[dict[str, Any]]",
                    [
                        "not-a-dict",
                        _tool_call("call_a", "edit_get_state", {"project_id": "p1"}),
                        _tool_call("call_b", "occupancy_status", {}),
                    ],
                ),
            ),
            _assistant("done", tool_calls=[_tool_call("call_c", "edit_job_status", {"job_id": "j1"})]),
            _assistant("all set"),
        ]
    )
    dispatched: list[tuple[str, JsonMap]] = []

    def _dispatch(name: str, args: JsonMap) -> JsonObject:
        dispatched.append((name, args))
        return {"ok": True, "text": f"{name} said hi"}

    out = agent.run_turn("go", llm=llm, dispatch=_dispatch)

    assert out["reply"] == "all set"
    assert len(llm.seen) == 3
    assert [row["name"] for row in out["trace"]] == [
        "edit_get_state",
        "occupancy_status",
        "edit_job_status",
    ]
    assert all(row["ok"] for row in out["trace"])
    assert out["trace"][0]["args"] == {"project_id": "p1"}
    assert out["trace"][0]["summary"] == "edit_get_state said hi"
    tool_rows = [row for row in out["history"] if row.get("role") == "tool"]
    assert [row.get("tool_call_id") for row in tool_rows] == ["call_a", "call_b", "call_c"]
    assert [row.get("content") for row in tool_rows] == [
        "edit_get_state said hi",
        "occupancy_status said hi",
        "edit_job_status said hi",
    ]
    assert dispatched == [
        ("edit_get_state", {"project_id": "p1"}),
        ("occupancy_status", {}),
        ("edit_job_status", {"job_id": "j1"}),
    ]
    assert [row["role"] for row in llm.seen[1]] == [
        "system",
        "user",
        "assistant",
        "tool",
        "tool",
    ]
    assistant_rows = [row for row in out["history"] if row.get("tool_calls")]
    assert [len(row.get("tool_calls") or []) for row in assistant_rows] == [2, 1]


def test_run_turn_local_tool_names_pass_through() -> None:
    """``local__`` tools are not in the catalog but still dispatch."""
    seen: list[str] = []

    def _dispatch(name: str, args: JsonMap) -> JsonObject:
        del args
        seen.append(name)
        return {"ok": True, "text": "opened"}

    out = agent.run_turn(
        "open it",
        llm=FakeLLM(
            [
                _assistant(tool_calls=[_tool_call("l1", "local__desk__open", {"p": 1})]),
                _assistant("opened the file"),
            ]
        ),
        dispatch=_dispatch,
    )
    assert seen == ["local__desk__open"]
    assert out["trace"][0]["ok"] is True
    assert out["reply"] == "opened the file"


def test_run_turn_unknown_tool_records_a_failed_trace() -> None:
    """A tool the model invented never reaches dispatch."""
    def _dispatch(name: str, args: JsonMap) -> JsonObject:
        raise AssertionError(f"must not dispatch {name}")

    out = agent.run_turn(
        "do it",
        llm=FakeLLM(
            [
                _assistant(tool_calls=[_tool_call("u1", "rm_rf_everything", {})]),
                _assistant("no such tool"),
            ]
        ),
        dispatch=_dispatch,
    )
    assert out["trace"] == [
        {
            "name": "rm_rf_everything",
            "args": {},
            "ok": False,
            "summary": "unknown tool: rm_rf_everything",
        }
    ]
    assert out["reply"] == "no such tool"


def test_run_turn_without_dispatch_refuses_every_call() -> None:
    """No dispatcher wired means every call fails soft and the turn ends."""
    out = agent.run_turn(
        "go",
        llm=FakeLLM(
            [
                _assistant(tool_calls=[_tool_call("d1", "edit_get_state", {})]),
                _assistant("nothing wired"),
            ]
        ),
    )
    assert out["trace"][0]["ok"] is False
    assert out["trace"][0]["summary"] == (
        "unknown tool: edit_get_state (no dispatcher wired)"
    )
    assert out["reply"] == "nothing wired"


def test_run_turn_dispatch_crash_does_not_kill_the_turn() -> None:
    """A raising tool becomes an ok=False trace row and the loop continues."""
    calls: list[str] = []

    def _dispatch(name: str, args: JsonMap) -> JsonObject:
        del args
        calls.append(name)
        raise RuntimeError("tool exploded")

    out = agent.run_turn(
        "go",
        llm=FakeLLM(
            [
                _assistant(tool_calls=[_tool_call("e1", "edit_get_state", {})]),
                _assistant("recovered"),
            ]
        ),
        dispatch=_dispatch,
    )
    assert calls == ["edit_get_state"]
    assert out["trace"][0]["ok"] is False
    assert out["trace"][0]["summary"] == "tool edit_get_state failed: tool exploded"
    assert out["reply"] == "recovered"


def test_run_turn_non_dict_dispatch_result_is_a_failure() -> None:
    """A dispatcher that ignores the contract reads as ok False."""
    def _dispatch(name: str, args: JsonMap) -> Any:
        del name, args
        return _raw("just a string")

    out = agent.run_turn(
        "go",
        llm=FakeLLM(
            [
                _assistant(tool_calls=[_tool_call("n1", "edit_get_state", {})]),
                _assistant("done"),
            ]
        ),
        dispatch=_dispatch,
    )
    assert out["trace"][0]["ok"] is False
    assert out["trace"][0]["summary"] == "tool dispatcher must return {ok, text}"


def test_run_turn_ok_false_from_dispatch_continues_the_loop() -> None:
    """A failed tool result is fed back so the model can correct itself."""
    def _dispatch(name: str, args: JsonMap) -> JsonObject:
        del name, args
        return {"ok": False}

    out = agent.run_turn(
        "go",
        llm=FakeLLM(
            [
                _assistant(tool_calls=[_tool_call("f1", "edit_apply_ops", {"ops": []})]),
                _assistant("that op failed"),
            ]
        ),
        dispatch=_dispatch,
    )
    assert out["trace"][0]["ok"] is False
    assert out["trace"][0]["summary"] == ""
    tool_row = next(r for r in out["history"] if r.get("role") == "tool")
    assert tool_row.get("content") == ""
    assert out["reply"] == "that op failed"


def test_run_turn_reports_bad_tool_arguments() -> None:
    """Unparsable arguments never reach dispatch and name the problem."""
    def _dispatch(name: str, args: JsonMap) -> JsonObject:
        raise AssertionError(f"must not dispatch {name}")

    out = agent.run_turn(
        "go",
        llm=FakeLLM(
            [
                _assistant(tool_calls=[_tool_call("b1", "edit_get_state", "{bad")]),
                _assistant("try again"),
            ]
        ),
        dispatch=_dispatch,
    )
    assert out["trace"][0]["ok"] is False
    assert out["trace"][0]["summary"] == "bad tool call: arguments are not valid JSON"
    assert out["reply"] == "try again"


def test_run_turn_budget_exhaustion_gives_up() -> None:
    """A model that never stops calling tools hits the forced reply."""
    stuck = _assistant(tool_calls=[_tool_call("s1", "edit_get_state", {})])
    out = agent.run_turn(
        "go", llm=FakeLLM([stuck], repeat_last=True), dispatch=None, max_steps=2
    )
    assert out["reply"] == "gave up after 2 steps"
    assert out["history"][-1] == {
        "role": "assistant",
        "content": "gave up after 2 steps",
    }
    assert [row["name"] for row in out["trace"]] == ["edit_get_state"] * 2


def test_run_turn_budget_defaults_to_the_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``EZ_AGENT_MAX_STEPS`` caps a turn that passes no explicit budget."""
    monkeypatch.setenv(protocol.ENV_MAX_STEPS, "2")
    stuck = _assistant(tool_calls=[_tool_call("s1", "edit_get_state", {})])
    out = agent.run_turn("go", llm=FakeLLM([stuck], repeat_last=True))
    assert out["reply"] == "gave up after 2 steps"

    monkeypatch.setenv(protocol.ENV_MAX_STEPS, "nonsense")
    llm = FakeLLM([_assistant("fine")])
    assert agent.run_turn("go", llm=llm)["reply"] == "fine"


def test_run_turn_non_positive_budget_falls_back_to_the_default() -> None:
    """max_steps <= 0 is a caller mistake, not a free pass to loop forever."""
    stuck = _assistant(tool_calls=[_tool_call("s1", "edit_get_state", {})])
    llm = FakeLLM([stuck], repeat_last=True)
    out = agent.run_turn("go", llm=llm, max_steps=0)
    assert out["reply"] == f"gave up after {protocol.DEFAULT_MAX_STEPS} steps"
    assert len(llm.seen) == int(protocol.DEFAULT_MAX_STEPS)


def test_run_turn_merges_extra_tools_into_the_payload() -> None:
    """Caller tools ride along with the static catalog on every request."""
    extra: list[dict[str, Any]] = [
        {"name": "local__desk__open", "description": "open a file"}
    ]
    llm = FakeLLM([_assistant("ok")])
    out = agent.run_turn("hi", tools=extra, llm=llm)

    payload = llm.tool_payloads[0]
    assert payload is not None
    names = [spec["function"]["name"] for spec in payload]
    assert names[0] == "edit_get_state"
    assert names[-1] == "local__desk__open"
    assert out["reply"] == "ok"


def test_run_turn_continues_a_round_tripped_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """History comes back verbatim, normalized, and copied."""
    monkeypatch.setattr(agent, "in_container", lambda *_a, **_k: False)
    spy = UrlopenSpy(
        _completion_body(content="second answer"),
    )
    monkeypatch.setattr(AgentLLM, "_urlopen", spy)
    prior: list[ChatMessage] = [
        {"role": "user", "content": "first"},
        {
            "role": "assistant",
            "content": "earlier",
            "tool_calls": cast(
                "list[dict[str, Any]]", [{"id": "c0", "junk": 1}, "not-a-dict"]
            ),
        },
        {"role": "tool", "tool_call_id": "c0", "content": "state"},
        _raw({"content": None, "tool_calls": "junk", "tool_call_id": ""}),
    ]
    out = agent.run_turn("and now?", history=prior)

    assert out["reply"] == "second answer"
    roles = [row.get("role") for row in out["history"]]
    assert roles == ["user", "assistant", "tool", "", "user", "assistant"]
    copied = out["history"][1]
    assert copied.get("tool_calls") == [{"id": "c0", "junk": 1}]
    assert copied is not prior[1]
    assert out["history"][3] == {"role": "", "content": ""}
    assert prior[0] == {"role": "user", "content": "first"}
    sent = json.loads((cast("bytes | None", spy.requests[0].data) or b"").decode("utf-8"))["messages"]
    assert [row["role"] for row in sent] == ["system", *roles[:-1]]
    assert sent[0]["content"] == agent.system_prompt()


def test_run_turn_refuses_heavy_occupancy_before_any_completion(
    tmp_path: Path,
) -> None:
    """The XOR gate stops the loop, not just the client."""
    _write_occupancy(tmp_path, "ltx")
    llm = FakeLLM([_assistant("never")])
    with pytest.raises(AgentRefused):
        agent.run_turn("go", llm=llm)
    assert llm.seen == []


def test_run_turn_runs_while_an_orphaned_blender_desk_record_remains(
    tmp_path: Path,
) -> None:
    """A dead Blender desk no longer dead-ends the chat path."""
    _write_occupancy(
        tmp_path,
        "blender-desk",
        holders={"blender_pid": 4242, "mcp_pid": 4243},
        pids_alive={"blender_pid": False, "mcp_pid": False},
    )
    llm = FakeLLM([_assistant("cut to the B roll")])
    out = agent.run_turn("go", llm=llm)
    assert out["reply"] == "cut to the B roll"
    assert llm.seen != []


def test_run_turn_refuses_a_live_heavy_mode_with_a_runnable_command(
    tmp_path: Path,
) -> None:
    """The refusal names the host command that releases the GPU."""
    _write_occupancy(
        tmp_path, "wan", holders={"llm_pid": 4242}, pids_alive={"llm_pid": True}
    )
    llm = FakeLLM([_assistant("never")])
    with pytest.raises(AgentRefused) as caught:
        agent.run_turn("go", llm=llm)
    assert llm.seen == []
    assert "occupancy is wan" in str(caught.value)
    assert "bazelisk run //:manage -- occupancy enter idle --yes" in str(caught.value)


def test_run_turn_uses_agent_llm_when_no_client_is_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The default client is a real :class:`AgentLLM` behind the urlopen seam."""
    monkeypatch.setattr(agent, "in_container", lambda *_a, **_k: False)
    monkeypatch.setenv(protocol.ENV_MODEL, "Qwen-Injected")
    spy = UrlopenSpy(_completion_body(content="agent answered"))
    monkeypatch.setattr(AgentLLM, "_urlopen", spy)
    out = agent.run_turn("hi")
    assert out["reply"] == "agent answered"
    assert spy.requests[0].full_url.endswith("/chat/completions")
    body = json.loads((cast("bytes | None", spy.requests[0].data) or b"").decode("utf-8"))
    assert body["model"] == "Qwen-Injected"
    assert (tmp_path / agent.OCCUPANCY_FILE_NAME).is_file()

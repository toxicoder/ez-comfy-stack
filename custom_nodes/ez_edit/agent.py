"""Built-in editing agent: an OpenAI-compatible tool loop (stdlib only).

The panel chat box and ``POST /ez_edit/chat`` call :func:`run_turn`. The loop
talks to the agent model (``scripts/utilities/agent-model.sh``) through
``{EZ_AGENT_LLM_URL}/chat/completions`` and hands every tool call the model
asks for to the caller's ``dispatch`` (``routes.py`` wires the static
:data:`~ez_edit.protocol.TOOL_CATALOG` handlers plus browser-relayed
``local__`` tools).

House rules for this module: stdlib only (no Comfy, no requests), the HTTP
call sits behind the :meth:`AgentLLM._urlopen` indirection so pytest can stub
it, and every completion is refused before any socket is opened unless
``.occupancy.json`` allows a GPU co-tenant (:data:`protocol.SIDECAR_OK_OCCUPANCY`).

The returned ``history`` is the transcript *without* the system prompt; the
system prompt is re-prepended on every turn, so a caller may round-trip
``history`` straight back in.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import (
    Any,
    Callable,
    Mapping,
    NamedTuple,
    Protocol,
    Sequence,
    TypedDict,
    TypeAlias,
)

from . import protocol
from .protocol import ChatMessage, ToolCallTrace

DispatchFn: TypeAlias = Callable[[str, dict[str, Any]], dict[str, Any]]
"""``(name, args) -> {"ok": bool, "text": str}`` tool executor (injected)."""

OccupancyReader: TypeAlias = Callable[[Path], str]
"""``(path) -> mode`` reader injected by tests in place of the file."""

OCCUPANCY_FILE_NAME = ".occupancy.json"
"""Occupancy state file name under the Comfy output dir."""

DEFAULT_OUTPUT_DIR = "/outputs"
"""Container output bind used when ``COMFY_OUTPUT_DIR`` is unset."""

EMPTY_REPLY = "the model returned no reply"
"""Fallback reply text when the model ends a turn with no content."""

UNREACHABLE_PREFIX = "agent LLM unreachable:"
"""Reply prefix when the completion call failed on the wire."""

_PROMPT_RELPATH = ("prompts", "agent_system.txt")
"""Pack-relative path of the system prompt."""

FALLBACK_SYSTEM_PROMPT = (
    "You are the ez-comfy editing agent. Edit timelines with the editing "
    "tools, read state before you change it, and keep replies short."
)
"""Used only when the prompt file is missing or empty (pack stays usable)."""

class AgentRefused(RuntimeError):
    """Occupancy XOR refused an agent completion."""


class AgentTurn(TypedDict):
    """Result of one :func:`run_turn` call (JSON-ready)."""

    reply: str
    """Final assistant text for the panel."""
    trace: list[ToolCallTrace]
    """One row per tool call the loop made, in order."""
    history: list[ChatMessage]
    """Transcript for the next turn (system prompt excluded)."""


class CompletionClient(Protocol):
    """Anything that can complete a chat turn (``AgentLLM`` or a double)."""

    def chat(
        self, messages: list[ChatMessage], tools: list[dict[str, Any]] | None = None
    ) -> ChatMessage:
        """Return the next assistant message.

        Args:
            messages: Chat transcript (system prompt first).
            tools: OpenAI function-shaped tool specs.

        Returns:
            Assistant message: ``content`` and/or ``tool_calls``.
        """
        ...


class _Call(NamedTuple):
    """One parsed tool_call plus the parse error (empty when clean)."""

    call_id: str
    name: str
    args: dict[str, Any]
    error: str


_SYSTEM_PROMPT_CACHE: str | None = None
"""Cached pack system prompt; None until first read (test-resettable)."""


# --- Environment helpers ----------------------------------------------------


def _environ(environ: Mapping[str, str] | None) -> Mapping[str, str]:
    """Return the caller's environ or the process environment.

    Args:
        environ: Injected mapping (pytest), or None for ``os.environ``.

    Returns:
        Mapping to read config keys from.
    """
    return os.environ if environ is None else environ


def in_container(
    environ: Mapping[str, str] | None = None, dockerenv: Path | None = None
) -> bool:
    """Whether the pack runs inside the Comfy container (host naming).

    Args:
        environ: Injected environ; None reads ``os.environ``.
        dockerenv: Marker file path; None uses ``/.dockerenv``.

    Returns:
        True when the container markers are present.
    """
    env = _environ(environ)
    marker = Path("/.dockerenv") if dockerenv is None else dockerenv
    return marker.is_file() or env.get("MODELS_ROOT", "").strip() == "/models"


def agent_base_url(
    environ: Mapping[str, str] | None = None, dockerenv: Path | None = None
) -> str:
    """OpenAI-compatible base for the agent model (already carries ``/v1``).

    Args:
        environ: Injected environ; None reads ``os.environ``.
        dockerenv: Marker file for the container heuristic.

    Returns:
        ``http://host:port/v1`` with no trailing slash.
    """
    env = _environ(environ)
    explicit = env.get(protocol.ENV_LLM_URL, "").strip().rstrip("/")
    if explicit:
        return explicit
    host = "host.docker.internal" if in_container(env, dockerenv) else "127.0.0.1"
    return f"http://{host}:{protocol.DEFAULT_LLM_URL_PORT}/v1"


def model_id(environ: Mapping[str, str] | None = None) -> str:
    """Model id served by the agent sidecar.

    Args:
        environ: Injected environ; None reads ``os.environ``.

    Returns:
        ``EZ_AGENT_MODEL`` or :data:`protocol.DEFAULT_MODEL`.
    """
    env = _environ(environ)
    return env.get(protocol.ENV_MODEL, "").strip() or protocol.DEFAULT_MODEL


def timeout_s(environ: Mapping[str, str] | None = None) -> float:
    """Per-completion HTTP timeout.

    Args:
        environ: Injected environ; None reads ``os.environ``.

    Returns:
        Positive timeout in seconds (default on garbage).
    """
    raw = _environ(environ).get(protocol.ENV_TIMEOUT_S, "").strip()
    try:
        value = float(raw)
    except ValueError:
        return float(protocol.DEFAULT_TIMEOUT_S)
    return value if value > 0.0 else float(protocol.DEFAULT_TIMEOUT_S)


def max_steps(environ: Mapping[str, str] | None = None) -> int:
    """Tool-loop budget per user turn.

    Args:
        environ: Injected environ; None reads ``os.environ``.

    Returns:
        Positive step count (``EZ_AGENT_MAX_STEPS`` or the default).
    """
    raw = _environ(environ).get(protocol.ENV_MAX_STEPS, "").strip()
    try:
        value = int(raw)
    except ValueError:
        return int(protocol.DEFAULT_MAX_STEPS)
    return value if value > 0 else int(protocol.DEFAULT_MAX_STEPS)


def _default_budget() -> int:
    """Tool-loop budget for a turn that did not pass one.

    A module-level call site: :func:`run_turn` shadows :func:`max_steps` with
    its own keyword argument, so the env-reading helper is reached here.

    Returns:
        Positive step count from ``EZ_AGENT_MAX_STEPS``.
    """
    return max_steps()


# --- Occupancy gate ---------------------------------------------------------


def occupancy_path(
    environ: Mapping[str, str] | None = None, *, filename: str = OCCUPANCY_FILE_NAME
) -> Path:
    """``${COMFY_OUTPUT_DIR}/.occupancy.json``.

    Args:
        environ: Injected environ; None reads ``os.environ``.
        filename: State file name (tests use a tmp name).

    Returns:
        Occupancy state path (may not exist yet).
    """
    root = _environ(environ).get("COMFY_OUTPUT_DIR", "").strip() or DEFAULT_OUTPUT_DIR
    return Path(root) / filename


def read_occupancy_mode(
    path: Path | None = None,
    *,
    reader: OccupancyReader | None = None,
    environ: Mapping[str, str] | None = None,
) -> str:
    """Occupancy mode string, ``unknown`` when unreadable or missing.

    Mirrors ``ez_prompt_enhance.client.occupancy_mode``: a missing or corrupt
    file is first-run/pytest and reads as ``unknown`` (allowed).

    Args:
        path: State file; None uses :func:`occupancy_path`.
        reader: Injectable reader (tests); None reads the file.
        environ: Injected environ for the default path.

    Returns:
        Mode id, or ``unknown``.
    """
    state = occupancy_path(environ) if path is None else path
    if reader is not None:
        mode = str(reader(state) or "").strip()
        return mode or "unknown"
    try:
        data = json.loads(state.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return "unknown"
    if not isinstance(data, dict):
        return "unknown"
    mode = str(data.get("mode") or "").strip()
    return mode or "unknown"


def require_occupancy(
    path: Path | None = None,
    *,
    reader: OccupancyReader | None = None,
    environ: Mapping[str, str] | None = None,
) -> str:
    """Refuse an agent completion while a heavy GPU job holds the Spark.

    Args:
        path: State file; None uses :func:`occupancy_path`.
        reader: Injectable reader (tests).
        environ: Injected environ for the default path.

    Returns:
        The allowed occupancy mode.

    Raises:
        AgentRefused: mode is not in :data:`protocol.SIDECAR_OK_OCCUPANCY`.
    """
    mode = read_occupancy_mode(path, reader=reader, environ=environ)
    if mode not in protocol.SIDECAR_OK_OCCUPANCY:
        raise AgentRefused(
            f"occupancy is {mode}; the agent model is a co-tenant, stop the "
            "heavy job (occupancy enter idle) before chatting"
        )
    return mode


# --- Tool specs -------------------------------------------------------------


def _add_tool(
    tools: list[dict[str, Any]],
    seen: set[str],
    name: object,
    description: object,
    parameters: object,
) -> None:
    """Append one OpenAI function tool when its name is new and non-empty.

    Args:
        tools: Accumulator of OpenAI-shaped tool specs.
        seen: Names already added (dedupe across catalog + extras).
        name: Tool name.
        description: Tool description.
        parameters: JSON Schema object (non-dict becomes ``{}``).
    """
    clean = str(name or "").strip()
    if not clean or clean in seen:
        return
    schema = dict(parameters) if isinstance(parameters, dict) else {}
    seen.add(clean)
    tools.append(
        {
            "type": "function",
            "function": {
                "name": clean,
                "description": str(description or ""),
                "parameters": schema,
            },
        }
    )


def build_tools(
    extra: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """OpenAI ``tools`` payload: the static catalog plus any extra tools.

    Extras may be catalog-shaped (``{name, description, parameters}``) or
    already OpenAI-shaped (``{type, function}``); anything else is dropped.

    Args:
        extra: Additional tool dicts (browser-relayed ``local__`` tools).

    Returns:
        Deduplicated list of ``{"type": "function", "function": {...}}``.
    """
    tools: list[dict[str, Any]] = []
    seen: set[str] = set()
    for name, entry in protocol.TOOL_CATALOG.items():
        _add_tool(
            tools,
            seen,
            name,
            entry.get("description"),
            entry.get("parameters"),
        )
    for candidate in extra or ():
        if not isinstance(candidate, dict):
            continue
        inner = candidate.get("function")
        source = inner if isinstance(inner, dict) else candidate
        _add_tool(
            tools,
            seen,
            source.get("name"),
            source.get("description"),
            source.get("parameters"),
        )
    return tools


def tool_names(tools: list[dict[str, Any]]) -> set[str]:
    """Names the loop may dispatch without the ``local__`` pass-through.

    Args:
        tools: OpenAI-shaped tool specs from :func:`build_tools`.

    Returns:
        Set of tool names present in the payload.
    """
    names: set[str] = set()
    for spec in tools:
        inner = spec.get("function")
        if isinstance(inner, dict):
            clean = str(inner.get("name") or "").strip()
            if clean:
                names.add(clean)
    return names


# --- System prompt ----------------------------------------------------------


def system_prompt_path() -> Path:
    """Pack-relative path of the agent system prompt.

    Returns:
        ``<pack>/prompts/agent_system.txt``.
    """
    return Path(__file__).resolve().parent.joinpath(*_PROMPT_RELPATH)


def system_prompt() -> str:
    """System prompt text, read once and cached at module level.

    Returns:
        Prompt file contents, or :data:`FALLBACK_SYSTEM_PROMPT` when the file
        is missing or blank (the pack must stay importable).
    """
    global _SYSTEM_PROMPT_CACHE  # noqa: PLW0603 - module-level lazy read
    if _SYSTEM_PROMPT_CACHE is None:
        try:
            text = system_prompt_path().read_text(encoding="utf-8").strip()
        except OSError:
            text = ""
        _SYSTEM_PROMPT_CACHE = text or FALLBACK_SYSTEM_PROMPT
    return _SYSTEM_PROMPT_CACHE


def reset_agent_state_for_tests() -> None:
    """Drop the cached system prompt (pytest isolation)."""
    global _SYSTEM_PROMPT_CACHE  # noqa: PLW0603 - test hook
    _SYSTEM_PROMPT_CACHE = None


# --- LLM client -------------------------------------------------------------


class AgentLLM:
    """OpenAI-compatible chat client for the agent model sidecar."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        """Bind the client to a base url, model id, and timeout.

        Args:
            base_url: Override for ``EZ_AGENT_LLM_URL`` (ends in ``/v1``).
            model: Override for ``EZ_AGENT_MODEL``.
            timeout: Override for ``EZ_AGENT_TIMEOUT_S``.
            environ: Injected environ; None reads ``os.environ``.
        """
        self._environ = environ
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    def _url(self) -> str:
        """Completion endpoint for this client.

        Returns:
            ``{base}/chat/completions``.
        """
        base = self.base_url or agent_base_url(self._environ)
        return f"{base.rstrip('/')}/chat/completions"

    def _model(self) -> str:
        """Model id for this client.

        Returns:
            Override or ``EZ_AGENT_MODEL`` default.
        """
        return self.model or model_id(self._environ)

    def _timeout(self) -> float:
        """Timeout seconds for this client.

        Returns:
            Override or ``EZ_AGENT_TIMEOUT_S`` default.
        """
        if self.timeout is not None:
            return float(self.timeout)
        return timeout_s(self._environ)

    def _urlopen(self, request: urllib.request.Request, timeout: float) -> Any:
        """Indirection so pytest can stub HTTP (mirrors ``_urlopen_sidecar``).

        Args:
            request: Prepared POST request for ``/chat/completions``.
            timeout: Socket timeout in seconds.

        Returns:
            Opened HTTP response (caller closes it).
        """
        return urllib.request.urlopen(request, timeout=timeout)

    def chat(
        self, messages: list[ChatMessage], tools: list[dict[str, Any]] | None = None
    ) -> ChatMessage:
        """One completion: occupancy gate, POST, parse ``choices[0].message``.

        Args:
            messages: Chat transcript (system prompt first).
            tools: OpenAI function-shaped tool specs.

        Returns:
            Assistant message. Wire or JSON failures come back as an
            assistant message carrying the reason, so the loop terminates
            with a readable reply instead of raising.

        Raises:
            AgentRefused: occupancy does not allow a co-tenant completion.
        """
        require_occupancy(environ=self._environ)
        payload: dict[str, Any] = {
            "model": self._model(),
            "messages": [dict(message) for message in messages],
            "tools": list(tools or []),
            "tool_choice": "auto",
            "stream": False,
        }
        request = urllib.request.Request(
            self._url(),
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            with self._urlopen(request, self._timeout()) as response:
                raw = response.read()
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            return ChatMessage(
                role="assistant", content=f"{UNREACHABLE_PREFIX} {exc}", tool_calls=[]
            )
        return _parse_completion(raw)


def _parse_completion(raw: bytes | str) -> ChatMessage:
    """Turn a ``/chat/completions`` body into a :class:`ChatMessage`.

    Args:
        raw: Response body.

    Returns:
        Assistant message; empty content when the body carries none.
    """
    try:
        data = json.loads(raw)
    except ValueError:
        return ChatMessage(
            role="assistant", content="agent LLM returned invalid JSON", tool_calls=[]
        )
    message = None
    if isinstance(data, dict):
        choices = data.get("choices")
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            first = choices[0].get("message")
            message = first if isinstance(first, dict) else {}
    if message is None:
        return ChatMessage(
            role="assistant", content="agent LLM returned no choices", tool_calls=[]
        )
    content = str(message.get("content") or "")
    calls = message.get("tool_calls")
    return ChatMessage(
        role="assistant",
        content=content,
        tool_calls=calls if isinstance(calls, list) else [],
    )


# --- Tool loop --------------------------------------------------------------


def _parse_call(entry: Mapping[str, Any], step: int, index: int) -> _Call:
    """Normalize one raw tool_call object.

    Args:
        entry: Tool call as the model sent it (``function.arguments`` JSON
        string, or a provider that already parsed it).
        step: Loop step (1-based) - seeds a synthetic call id.
        index: Position within the step (seeds a synthetic call id).

    Returns:
        Parsed call; ``error`` is non-empty when the arguments did not parse.
    """
    inner = entry.get("function")
    fn = inner if isinstance(inner, dict) else {}
    name = str(fn.get("name") or entry.get("name") or "").strip()
    call_id = str(entry.get("id") or f"call_{step}_{index}")
    fn_args = fn.get("arguments")
    raw_args: Any = fn_args if fn_args is not None else entry.get("args")
    if raw_args is None or raw_args == "":
        return _Call(call_id, name, {}, "")
    if isinstance(raw_args, dict):
        return _Call(call_id, name, dict(raw_args), "")
    if isinstance(raw_args, str):
        try:
            parsed = json.loads(raw_args)
        except ValueError:
            return _Call(call_id, name, {}, "arguments are not valid JSON")
        if isinstance(parsed, dict):
            return _Call(call_id, name, parsed, "")
        return _Call(call_id, name, {}, "arguments must be a JSON object")
    return _Call(call_id, name, {}, "arguments must be a JSON object")


def _copy_message(row: Mapping[str, Any]) -> ChatMessage:
    """Copy one caller-supplied transcript row into a fresh message record.

    History round-trips through JSON in the panel, so rows may be plain dicts
    (or carry junk tool fields); only the pinned keys survive the copy.

    Args:
        row: Transcript entry from a previous :func:`run_turn`.

    Returns:
        New :class:`~ez_edit.protocol.ChatMessage` carrying role, content, and
        whichever tool fields the row had.
    """
    message = ChatMessage(
        role=str(row.get("role") or ""), content=str(row.get("content") or "")
    )
    calls = row.get("tool_calls")
    if isinstance(calls, list):
        message["tool_calls"] = [
            dict(entry) for entry in calls if isinstance(entry, dict)
        ]
    call_id = row.get("tool_call_id")
    if call_id:
        message["tool_call_id"] = str(call_id)
    return message


def _unknown_dispatch(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Dispatch used when the caller supplies none.

    Args:
        name: Tool name the model asked for.
        args: Parsed tool arguments.

    Returns:
        Refusal result (no handler is wired).
    """
    del args
    return {"ok": False, "text": f"unknown tool: {name} (no dispatcher wired)"}


def _normalize_result(result: Any) -> tuple[bool, str]:
    """Coerce a dispatch result into ``(ok, text)``.

    Args:
        result: Whatever the dispatcher returned.

    Returns:
        Ok flag and the text handed back to the model.
    """
    if not isinstance(result, dict):
        return False, "tool dispatcher must return {ok, text}"
    return bool(result.get("ok")), str(result.get("text") or "")


def _run_call(
    call: _Call,
    *,
    known: set[str],
    dispatch: DispatchFn,
) -> tuple[bool, str]:
    """Execute one parsed tool call.

    Args:
        call: Parsed tool call.
        known: Names present in the tool payload.
        dispatch: Injected executor.

    Returns:
        ``(ok, text)`` for the tool message and trace row.
    """
    if call.error:
        return False, f"bad tool call: {call.error}"
    if not (call.name in known or call.name.startswith(protocol.LOCAL_TOOL_PREFIX)):
        return False, f"unknown tool: {call.name}"
    try:
        result = dispatch(call.name, call.args)
    except Exception as exc:  # noqa: BLE001 - a tool crash must not kill the turn
        return False, f"tool {call.name} failed: {exc}"
    return _normalize_result(result)


def run_turn(
    user_text: str,
    *,
    history: list[ChatMessage] | None = None,
    tools: list[dict[str, Any]] | None = None,
    llm: CompletionClient | None = None,
    dispatch: DispatchFn | None = None,
    max_steps: int | None = None,
) -> AgentTurn:
    """Run one user turn through the tool loop.

    Appends ``user_text`` to ``history`` (system prompt first), calls the LLM,
    dispatches every tool call it asks for, feeds the results back as ``tool``
    messages, and repeats until the model answers without tool calls or the
    step budget runs out.

    Args:
        user_text: The operator's message.
        history: Prior transcript (system prompt excluded); None starts fresh.
        tools: Extra tool dicts merged over the static catalog.
        llm: Completion client; None builds :class:`AgentLLM`.
        dispatch: ``(name, args) -> {"ok", "text"}``; None refuses every call.
        max_steps: Round-trip budget; None reads ``EZ_AGENT_MAX_STEPS``.

    Returns:
        :class:`AgentTurn` with the final reply, one trace row per tool call,
        and the transcript to send back on the next turn.

    Raises:
        AgentRefused: occupancy does not allow an agent completion.
    """
    require_occupancy()
    budget = _default_budget() if max_steps is None else int(max_steps)
    if budget <= 0:
        budget = int(protocol.DEFAULT_MAX_STEPS)
    client: CompletionClient = AgentLLM() if llm is None else llm
    executor: DispatchFn = _unknown_dispatch if dispatch is None else dispatch
    specs = build_tools(tools)
    known = tool_names(specs)
    transcript: list[ChatMessage] = [_copy_message(row) for row in (history or [])]
    transcript.append(ChatMessage(role="user", content=str(user_text or "")))
    trace: list[ToolCallTrace] = []
    for step in range(1, budget + 1):
        messages: list[ChatMessage] = [
            ChatMessage(role="system", content=system_prompt()),
            *transcript,
        ]
        answer = client.chat(messages, specs)
        raw_calls = answer.get("tool_calls") or []
        entries = [row for row in raw_calls if isinstance(row, dict)]
        content = str(answer.get("content") or "")
        if not entries:
            reply = content or EMPTY_REPLY
            transcript.append(ChatMessage(role="assistant", content=reply))
            return {"reply": reply, "trace": trace, "history": transcript}
        transcript.append(
            ChatMessage(role="assistant", content=content, tool_calls=entries)
        )
        for index, entry in enumerate(entries):
            call = _parse_call(entry, step, index)
            ok, text = _run_call(call, known=known, dispatch=executor)
            transcript.append(
                ChatMessage(role="tool", tool_call_id=call.call_id, content=text)
            )
            trace.append(
                {"name": call.name, "args": call.args, "ok": ok, "summary": text}
            )
    reply = f"gave up after {budget} steps"
    transcript.append(ChatMessage(role="assistant", content=reply))
    return {"reply": reply, "trace": trace, "history": transcript}

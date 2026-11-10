"""Pure view layer for the guarded operator console.

Every function here takes data and returns data: a :class:`~tui.contract.ViewModel`
for one screen, or the rows and lines that build one. Nothing in this module
imports curses, opens a file, or spawns a process, which is what lets the suite
assert on rendered content without a terminal and keeps the view layer decoupled
from the catalog, the guard, and the runner.

A view may show a decision; it may never make one. Selectability and blockers
come from the :class:`~tui.contract.GuardVerdict` records the app hands in, an
action with no verdict is treated as blocked (the same fail-closed rule the
guard layer uses), and the confirm token comes only from the action's own
``ConfirmKind.token()``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from tui.contract import (
    MIN_DISK_FREE_GIB,
    MIN_HOST_FREE_GIB,
    UNMEASURED,
    ActionSpec,
    CommandResult,
    ConfirmKind,
    Frame,
    Group,
    GuardVerdict,
    Health,
    Line,
    ParamKind,
    ParamSpec,
    RiskTier,
    Row,
    ScreenId,
    Style,
    ViewModel,
    build_argv,
)
from tui.lanes import Graph, Lane, user_folder_hint

WARN_MARGIN_GIB = 4
"""How close to a headroom floor, in GiB, still counts as a warning not a block."""

_STATUS_KEYS: tuple[str, ...] = ("stack", "ram", "disk", "occ", "queue", "cap")
"""The six readings the status bar leads with, in display order."""

_KNOWN_STACK: frozenset[str] = frozenset({"running", "present", "stopped"})
"""Compose states that are real readings; anything else means the probe failed."""

_GOOD_ATTENTION: frozenset[str] = frozenset({"kitchen", "sage"})
"""Attention backends that mean the accelerated path is live."""

_STYLE_RANK: dict[Style, int] = {Style.OK: 0, Style.WARN: 1, Style.BAD: 2}
"""Severity order for the status-bar colour: the worst reading wins."""

_NO_READING = "no reading"
"""What a row says when its probe never answered."""

_MAX_TAIL = 40
"""Output lines a progress or result screen repeats back at the operator."""

_ACTION_FOOTER = "enter run  esc back  / palette  q quit"
"""Key strip shared by the action lists."""


@dataclass(frozen=True)
class _Reading:
    """One machine measurement reduced to what the console can show.

    Attributes:
        key: Short id used for the row key and the status bar.
        label: Field name the operator reads.
        value: Formatted reading, or :data:`_NO_READING`.
        badge: ``ok``, ``warn``, ``bad``, or ``?``.
        style: Drawing intent for the value.
        readable: False when the probe never answered, so the row is disabled.
    """

    key: str
    label: str
    value: str
    badge: str
    style: Style
    readable: bool


def _word(value: str) -> str:
    """Normalise a state token out of a probe payload.

    Args:
        value: Raw token, possibly blank or mixed case.

    Returns:
        Trimmed lower-case text.
    """
    return value.strip().lower()


def _clip(text: str, width: int) -> str:
    """Cut text to the terminal width, marking that it was cut.

    Args:
        text: Content to draw.
        width: Columns available.

    Returns:
        At most ``width`` characters, ending in ``>`` when something was dropped.
    """
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width == 1:
        return ">"
    return f"{text[: width - 1]}>"


def _first(reasons: Sequence[str]) -> str:
    """Take the leading blocker out of a verdict's reasons.

    Args:
        reasons: Blockers in the order the guard found them.

    Returns:
        The first reason, or empty when there are none.
    """
    return reasons[0] if reasons else ""


def _clamp(selected: int, count: int) -> int:
    """Keep a focus index inside a list.

    Args:
        selected: Index the app wants focused.
        count: Number of rows.

    Returns:
        An index between 0 and ``count - 1``, or 0 for an empty list.
    """
    if count <= 0:
        return 0
    return min(max(selected, 0), count - 1)


def _worst(styles: Iterable[Style]) -> Style:
    """Pick the most severe style, so one bad reading colours the bar.

    Args:
        styles: Styles to rank.

    Returns:
        :attr:`Style.BAD` if present, then WARN, else OK.
    """
    worst = Style.OK
    for style in styles:
        if _STYLE_RANK.get(style, 0) > _STYLE_RANK.get(worst, 0):
            worst = style
    return worst


def _graded(
    key: str,
    label: str,
    value: str,
    badge: str,
    *,
    readable: bool = True,
) -> _Reading:
    """Build one graded reading.

    Args:
        key: Short id for the row key and the status bar.
        label: Field name the operator reads.
        value: Formatted reading.
        badge: ``ok``, ``warn``, ``bad``, or ``?``.
        readable: False to force the row disabled.

    Returns:
        The reading, disabled whenever the badge is the unknown mark.
    """
    styles = {"ok": Style.OK, "warn": Style.WARN, "bad": Style.BAD, "?": Style.BAD}
    return _Reading(
        key=key,
        label=label,
        value=value,
        badge=badge,
        style=styles[badge],
        readable=readable and badge != "?",
    )


def _unknown(key: str, label: str) -> _Reading:
    """Build the reading a failed probe produces.

    Args:
        key: Short id for the row key and the status bar.
        label: Field name the operator reads.

    Returns:
        A disabled row badged ``?``.
    """
    return _graded(key, label, _NO_READING, "?")


def _floor_reading(key: str, label: str, gib: int, floor: int) -> _Reading:
    """Grade a headroom reading against the floor the CLI blocks on.

    Args:
        key: Short id for the row key and the status bar.
        label: Field name the operator reads.
        gib: Measured GiB, or :data:`~tui.contract.UNMEASURED`.
        floor: The floor the stack start refuses below.

    Returns:
        ok at or above the margin, warn inside it, bad under the floor, ``?``
        when the reading could not be taken.
    """
    if gib == UNMEASURED:
        return _unknown(key, label)
    text = f"{gib}/{floor} GiB"
    if gib < floor:
        return _graded(key, label, text, "bad")
    if gib < floor + WARN_MARGIN_GIB:
        return _graded(key, label, text, "warn")
    return _graded(key, label, text, "ok")


def _attention_reading(health: Health) -> _Reading:
    """Grade the attention backend, which only means anything while Comfy runs.

    Args:
        health: The snapshot the poll layer took.

    Returns:
        The attention row; ``n/a`` while the stack is down, ``?`` when the stack
        state itself is unknown.
    """
    stack = _word(health["stack_state"])
    attention = _word(health["attention"])
    if stack == "running":
        if attention in _GOOD_ATTENTION:
            return _graded("attn", "attn", attention, "ok")
        if attention == "pytorch-fallback":
            return _graded("attn", "attn", attention, "warn")
        return _unknown("attn", "attn")
    if stack in _KNOWN_STACK:
        return _graded("attn", "attn", "n/a", "ok")
    return _unknown("attn", "attn")


def _occupancy_readings(health: Health) -> tuple[_Reading, ...]:
    """Grade the GPU-occupancy fields, which are the XOR desk's whole story.

    Args:
        health: The snapshot the poll layer took.

    Returns:
        Readings for mode, parked, queue, and the LLM sidecar.
    """
    mode = _word(health["occupancy_mode"])
    if mode in ("", "unknown", "unmeasured"):
        mode_reading = _unknown("occ", "occ")
    else:
        mode_reading = _graded("occ", "occ", mode, "ok" if mode == "idle" else "warn")
    parked = "parked" if health["parked"] else "loaded"
    queue = _word(health["queue"])
    if queue == "idle":
        queue_reading = _graded("queue", "queue", queue, "ok")
    elif queue == "busy":
        queue_reading = _graded("queue", "queue", queue, "warn")
    else:
        queue_reading = _unknown("queue", "queue")
    llm = "up" if health["llm_live"] else "down"
    return (
        mode_reading,
        _graded("parked", "parked", parked, "ok"),
        queue_reading,
        _graded("llm", "llm", llm, "warn" if health["llm_live"] else "ok"),
    )


def _network_readings(health: Health) -> tuple[_Reading, ...]:
    """Grade the bandwidth cap and the download probe.

    Args:
        health: The snapshot the poll layer took.

    Returns:
        Readings for the cap and for running downloads.
    """
    if not health["shaping"]:
        cap = _graded("cap", "cap", "uncapped", "warn")
    elif health["shaping_mbps"] == UNMEASURED:
        cap = _unknown("cap", "cap")
    else:
        cap = _graded("cap", "cap", f"{health['shaping_mbps']} Mbps", "ok")
    running = health["downloads_running"]
    return (
        cap,
        _graded("dl", "dl", "running" if running else "idle", "warn" if running else "ok"),
    )


def _pack_reading(health: Health) -> _Reading:
    """Grade the model packs the catalog can offer.

    Args:
        health: The snapshot the poll layer took.

    Returns:
        A ready-count reading, or ``?`` when no pack reported at all.
    """
    total = len(health["packs"])
    if total == 0:
        return _unknown("packs", "packs")
    ready = sum(1 for _, is_ready in health["packs"] if is_ready)
    return _graded("packs", "packs", f"{ready}/{total} ready", "ok" if ready == total else "warn")


def _readings(health: Health) -> tuple[_Reading, ...]:
    """Reduce a health snapshot to one graded reading per field.

    Args:
        health: The snapshot the poll layer took.

    Returns:
        Readings in display order, one per probe, plus one per probe error.
    """
    stack = _word(health["stack_state"])
    if stack in _KNOWN_STACK:
        stack_reading = _graded("stack", "stack", stack, "warn" if stack == "present" else "ok")
    else:
        stack_reading = _unknown("stack", "stack")
    rows: list[_Reading] = [
        stack_reading,
        _attention_reading(health),
        _floor_reading("ram", "ram", health["host_free_gib"], MIN_HOST_FREE_GIB),
        _floor_reading("disk", "disk", health["disk_free_gib"], MIN_DISK_FREE_GIB),
        *_occupancy_readings(health),
        *_network_readings(health),
        _pack_reading(health),
    ]
    for index, message in enumerate(health["errors"]):
        rows.append(_graded(f"error-{index}", f"probe {index + 1}", message, "bad", readable=False))
    return tuple(rows)


def _reading_row(reading: _Reading) -> Row:
    """Turn one reading into a dashboard row.

    Args:
        reading: The graded reading.

    Returns:
        A row that is selectable only when the reading was actually taken.
    """
    return Row(
        key=f"health.{reading.key}",
        label=reading.label,
        badge=reading.badge,
        note=reading.value,
        enabled=reading.readable,
        style=reading.style,
    )


def _action_row(action: ActionSpec, verdict: GuardVerdict | None) -> Row:
    """Render one catalog action as a list row.

    A missing verdict means the guard never spoke, which blocks the action the
    same way a failed guard does: the console fails closed.

    Args:
        action: The catalog entry.
        verdict: The guard outcome, or None when there is none.

    Returns:
        A row that is selectable only when the action is runnable and allowed.
    """
    reasons = () if verdict is None else verdict.reasons
    refused = action.tier is RiskTier.REFUSED
    allowed = action.is_runnable() and verdict is not None and verdict.allowed
    if refused:
        note = action.refuse_reason or _first(reasons) or "policy blocked"
        style = Style.BAD
    elif allowed:
        note = action.summary
        style = Style.NORMAL
    else:
        note = _first(reasons) or "waiting on a guard"
        style = Style.DIM
    return Row(
        key=action.action_id,
        label=action.title,
        badge=action.tier.label(),
        note=note,
        enabled=allowed,
        style=style,
    )


def _action_rows(
    actions: Sequence[ActionSpec],
    verdicts: Mapping[str, GuardVerdict],
) -> tuple[Row, ...]:
    """Render a list of actions against the guard's verdicts.

    Args:
        actions: Catalog entries in display order.
        verdicts: Guard outcomes keyed by ``action_id``.

    Returns:
        One row per action, blocked ones disabled and dimmed.
    """
    return tuple(_action_row(action, verdicts.get(action.action_id)) for action in actions)


def _haystack(action: ActionSpec) -> str:
    """Lower-case everything the palette matches on.

    Args:
        action: The catalog entry.

    Returns:
        Id, title, summary, keywords, and group, lower-cased, ready for a
        substring match.
    """
    keywords = " ".join(action.keywords)
    return (
        f"{action.action_id} {action.title} {action.summary} "
        f"{keywords} {action.group.value}"
    ).lower()


def _tier_style(tier: RiskTier) -> Style:
    """Colour a risk tier the way the confirm screen needs it.

    Args:
        tier: The action's tier.

    Returns:
        BAD for destructive and refused, WARN for heavy, ACCENT otherwise.
    """
    if tier in (RiskTier.DESTRUCTIVE, RiskTier.REFUSED):
        return Style.BAD
    if tier is RiskTier.HEAVY:
        return Style.WARN
    return Style.ACCENT


def _output_lines(output: str) -> tuple[Line, ...]:
    """Repeat captured child output as body lines.

    Args:
        output: Merged stdout and stderr, already decoded.

    Returns:
        The last :data:`_MAX_TAIL` non-blank lines.
    """
    kept = [entry for entry in output.splitlines() if entry.strip()]
    return tuple(Line(entry, Style.NORMAL) for entry in kept[-_MAX_TAIL:])


def _row_text(row: Row) -> str:
    """Compose the label, badge, and note of one row.

    Args:
        row: The row to draw.

    Returns:
        Single-line text for the list.
    """
    parts = [row.label]
    if row.badge:
        parts.append(f"[{row.badge}]")
    if row.note:
        parts.append(f"- {row.note}")
    return "  ".join(parts)


def _row_line(row: Row, selected: int, index: int, width: int) -> Line:
    """Draw one list row at its position.

    Args:
        row: The row.
        selected: Focused index.
        index: This row's position in the list.
        width: Columns available.

    Returns:
        Reverse when focused, dimmed when disabled, the row's own style otherwise.
    """
    if index == selected:
        style = Style.REVERSE
    elif not row.enabled:
        style = Style.DIM
    else:
        style = row.style
    return Line(_clip(_row_text(row), width), style)


def _param_note(param: ParamSpec, value: str) -> str:
    """Build the trailing hint for one parameter row.

    Args:
        param: The parameter being collected.
        value: The answer on file, possibly the default.

    Returns:
        The answer, the offered menu, the help text, or a required marker.
    """
    if param.kind is ParamKind.CHOICE:
        offered = ", ".join(choice.label for choice in param.choices)
        return f"{value} [{offered}]" if value else f"[{offered}]"
    if value:
        return value
    return param.help_text or ("required" if param.required else "optional")


def health_rows(health: Health) -> tuple[Row, ...]:
    """One row per machine reading, with unknowns surfaced rather than hidden.

    Args:
        health: The snapshot the poll layer took.

    Returns:
        A row per reading; a reading the probe could not take is badged ``?``
        and disabled so nothing can select past it.
    """
    return tuple(_reading_row(reading) for reading in _readings(health))


def status_bar(health: Health, width: int) -> Line:
    """The safety headline: stack, headroom, occupancy, queue, cap.

    The bar is the operator's first look at whether a heavy job is even
    permitted, so it colours itself by the worst reading it carries.

    Args:
        health: The snapshot the poll layer took.
        width: Columns available.

    Returns:
        One clipped line: BAD when a reading is blocked or unknown, WARN while
        anything sits inside the margin, OK otherwise.
    """
    readings = _readings(health)
    by_key = {reading.key: reading for reading in readings}
    parts = [f"{key} {by_key[key].value}" for key in _STATUS_KEYS]
    return Line(_clip("  ".join(parts), width), _worst(reading.style for reading in readings))


def dashboard(
    health: Health,
    verdicts: Mapping[str, GuardVerdict],
    quick: Sequence[ActionSpec],
) -> ViewModel:
    """Build the landing screen: every reading plus the quick actions.

    Args:
        health: The snapshot the poll layer took.
        verdicts: Guard outcomes keyed by ``action_id``.
        quick: The actions the app offers up front.

    Returns:
        Health rows followed by the quick actions, focused on the first quick
        action the guards permit.
    """
    readings = _readings(health)
    health_row_list = tuple(_reading_row(reading) for reading in readings)
    quick_rows = _action_rows(quick, verdicts)
    rows = health_row_list + quick_rows
    ready = sum(1 for row in quick_rows if row.enabled)
    unknown = sum(1 for reading in readings if not reading.readable)
    ready_index = next((index for index, row in enumerate(quick_rows) if row.enabled), -1)
    focus = len(health_row_list) + ready_index if ready_index >= 0 else 0
    detail = (
        Line(
            f"quick actions ready {ready}/{len(quick_rows)}",
            Style.OK if ready == len(quick_rows) else Style.WARN,
        ),
        Line(
            f"readings unknown {unknown}/{len(readings)}",
            Style.BAD if unknown else Style.DIM,
        ),
        Line(f"guard verdicts on file {len(verdicts)}", Style.DIM),
    )
    return ViewModel(
        screen=ScreenId.DASHBOARD,
        title="Studio dashboard",
        rows=rows,
        detail=detail,
        footer="1-9 sections  / palette  enter run  q quit",
        selected=focus,
    )


def group_list(
    group: Group,
    actions: Sequence[ActionSpec],
    verdicts: Mapping[str, GuardVerdict],
    selected: int = 0,
) -> ViewModel:
    """Build one left-rail section's action list.

    Args:
        group: The section being shown.
        actions: That section's catalog entries, in display order.
        verdicts: Guard outcomes keyed by ``action_id``.
        selected: Row the app wants focused.

    Returns:
        A list in which a blocked action is dimmed and cannot be selected.
    """
    rows = _action_rows(actions, verdicts)
    runnable = sum(1 for row in rows if row.enabled)
    detail = (
        Line(
            f"{group.value}  hotkey {group.hotkey}  {runnable}/{len(rows)} runnable",
            Style.OK if runnable else Style.WARN,
        ),
    )
    return ViewModel(
        screen=ScreenId.GROUP,
        title=f"{group.value.capitalize()} actions",
        rows=rows,
        detail=detail,
        footer=_ACTION_FOOTER,
        selected=_clamp(selected, len(rows)),
    )


def palette(
    query: str,
    actions: Sequence[ActionSpec],
    verdicts: Mapping[str, GuardVerdict],
    selected: int = 0,
) -> ViewModel:
    """Build the fuzzy action palette over every catalog entry.

    Args:
        query: What the operator typed; blank matches everything.
        actions: The whole catalog, in display order.
        verdicts: Guard outcomes keyed by ``action_id``.
        selected: Row the app wants focused.

    Returns:
        The matching actions, blocked ones dimmed and unselectable.
    """
    needle = query.strip().lower()
    found = tuple(
        action for action in actions if not needle or needle in _haystack(action)
    )
    rows = _action_rows(found, verdicts)
    if found:
        detail = (Line(f"query '{query}'  matches {len(found)}/{len(actions)}", Style.DIM),)
    else:
        detail = (Line(f"query '{query}'  matches 0/{len(actions)}", Style.WARN),)
    return ViewModel(
        screen=ScreenId.PALETTE,
        title="Action palette",
        rows=rows,
        detail=detail,
        footer=_ACTION_FOOTER,
        selected=_clamp(selected, len(rows)),
    )


def param_form(
    action: ActionSpec,
    answers: Mapping[str, str],
    selected: int = 0,
) -> ViewModel:
    """Build the parameter collector for one action.

    Args:
        action: The catalog entry whose parameters are being filled.
        answers: Answers so far, keyed by :attr:`~tui.contract.ParamSpec.name`.
        selected: The field the app wants focused.

    Returns:
        One row per parameter plus a live preview of the argv the runner would
        receive, or what is still missing.
    """
    rows = tuple(
        Row(
            key=param.name,
            label=param.label,
            badge=param.kind.value,
            note=_param_note(param, answers.get(param.name, param.default)),
            enabled=True,
            style=Style.NORMAL,
        )
        for param in action.params
    )
    detail = [
        Line(f"action {action.action_id}  group {action.group.value}", Style.ACCENT),
        Line(
            f"tier {action.tier.label()}  confirm {action.confirm.value}",
            _tier_style(action.tier),
        ),
        Line(action.summary, Style.DIM),
    ]
    try:
        detail.append(Line(f"argv {' '.join(build_argv(action, answers))}", Style.ACCENT))
    except ValueError as exc:
        detail.append(Line(f"not ready: {exc}", Style.WARN))
    return ViewModel(
        screen=ScreenId.PARAM_FORM,
        title=f"Parameters: {action.title}",
        rows=rows,
        detail=tuple(detail),
        footer="up/down field  enter edit  esc back",
        selected=_clamp(selected, len(rows)),
    )


def confirm_view(action: ActionSpec, argv: Sequence[str], typed: str = "") -> ViewModel:
    """Build the last line of defence before anything is spawned.

    The token shown here is only ever ``action.confirm.token()``: the view
    invents no literal and answers no prompt, so the real child script still
    reads stdin itself.

    Args:
        action: The catalog entry about to run.
        argv: The exact argument list the runner would exec.
        typed: What the operator has typed so far.

    Returns:
        A screen naming the command, the token to retype, and what a destructive
        run costs.
    """
    token = action.confirm.token()
    detail = [
        Line(f"action {action.action_id}", Style.ACCENT),
        Line(
            f"tier {action.tier.label()}  confirm {action.confirm.value}",
            _tier_style(action.tier),
        ),
        Line(action.summary, Style.DIM),
        Line("command", Style.BOLD),
        Line(" ".join(argv), Style.ACCENT),
    ]
    if action.tier is RiskTier.DESTRUCTIVE or action.confirm is ConfirmKind.DELETE:
        detail.append(
            Line(f"DESTRUCTIVE: {action.title} erases data ({action.summary})", Style.BAD)
        )
        detail.append(Line("deleted models and cleared state cannot be restored", Style.BAD))
    if token:
        token_style = Style.BAD if action.confirm is ConfirmKind.DELETE else Style.WARN
        detail.append(Line(f"type exactly: {token}", token_style))
        typed_style = Style.OK if typed == token else Style.DIM
        detail.append(Line(f"typed: {typed}", typed_style))
    else:
        detail.append(Line("just press enter", Style.OK))
    return ViewModel(
        screen=ScreenId.CONFIRM,
        title=f"Confirm: {action.title}",
        detail=tuple(detail),
        footer="type the token  enter run  esc cancel",
    )


def progress_view(action: ActionSpec, tail: Sequence[str]) -> ViewModel:
    """Build the screen an operator watches while a command runs.

    Args:
        action: The action that was dispatched.
        tail: The most recent output lines, oldest first.

    Returns:
        A non-selectable screen repeating the tail under the action's identity.
    """
    detail = [
        Line(f"running {action.action_id}  tier {action.tier.label()}", _tier_style(action.tier)),
        Line(f"{len(tail)} output lines", Style.DIM),
        *_output_lines("\n".join(tail)),
        Line("the command runs in its own process; wait for it to finish", Style.DIM),
    ]
    return ViewModel(
        screen=ScreenId.PROGRESS,
        title=f"Running: {action.title}",
        detail=tuple(detail),
        footer="esc detaches the view, not the command",
    )


def result_view(result: CommandResult) -> ViewModel:
    """Build the outcome screen for one dispatch.

    Args:
        result: What came back from the runner.

    Returns:
        Exit status, the argv that ran, any note explaining a block, and the tail.
    """
    exit_text = "?" if result.returncode == UNMEASURED else str(result.returncode)
    headline = f"ran {'yes' if result.ran else 'no'}  exit {exit_text}  {result.duration_s:.1f}s"
    if not result.ran or result.returncode != 0:
        headline_style = Style.BAD
    else:
        headline_style = Style.OK
    detail = [
        Line(f"{result.action_id}", Style.ACCENT),
        Line(headline, headline_style),
        Line(f"argv {' '.join(result.argv)}", Style.DIM),
    ]
    if result.note:
        detail.append(Line(f"note {result.note}", Style.WARN))
    detail.extend(_output_lines(result.output))
    return ViewModel(
        screen=ScreenId.RESULT,
        title=f"Result: {result.action_id}",
        detail=tuple(detail),
        footer="enter back to where you came from  q quit",
    )


def lane_list(lanes: Sequence[Lane], selected: int = 0) -> ViewModel:
    """Build the lane browser.

    Args:
        lanes: Lanes in browse order.
        selected: Row the app wants focused.

    Returns:
        One row per lane with its graph count; browsing never mutates anything.
    """
    rows = tuple(
        Row(
            key=lane.lane_id,
            label=lane.title,
            badge=str(lane.graph_count),
            note=lane.description,
            enabled=True,
            style=Style.NORMAL,
        )
        for lane in lanes
    )
    if rows:
        detail = (Line("promoted graphs: read only, never edited here", Style.DIM),)
    else:
        detail = (Line("no lanes found under workflows/_lab", Style.WARN),)
    return ViewModel(
        screen=ScreenId.LANES,
        title="Lanes",
        rows=rows,
        detail=detail,
        footer="enter open lane  esc back  q quit",
        selected=_clamp(selected, len(rows)),
    )


def graph_list(lane: Lane, graphs: Sequence[Graph], selected: int = 0) -> ViewModel:
    """Build the graph list for one lane.

    Args:
        lane: The lane being browsed.
        graphs: Graphs in that lane, sorted by id.
        selected: Row the app wants focused.

    Returns:
        One row per graph, with the lane's blurb above them.
    """
    rows = tuple(
        Row(
            key=graph.rel_id,
            label=graph.title,
            badge=graph.occupancy or "-",
            note=graph.description,
            enabled=True,
            style=Style.NORMAL,
        )
        for graph in graphs
    )
    detail = (
        Line(f"lane {lane.lane_id}  {lane.graph_count} graphs on disk", Style.ACCENT),
        Line(lane.description, Style.DIM),
    )
    return ViewModel(
        screen=ScreenId.LANE_GRAPHS,
        title=f"Lane: {lane.title}",
        rows=rows,
        detail=detail,
        footer="enter open graph  esc back  q quit",
        selected=_clamp(selected, len(rows)),
    )


def graph_detail(graph: Graph) -> ViewModel:
    """Build the read-only pane for one promoted graph.

    Args:
        graph: The graph the operator picked.

    Returns:
        Lane, id, occupancy, blurb, hand-off ids, and where a live copy would be
        loaded from; the console edits nothing.
    """
    detail = (
        Line(f"lane {graph.lane_id}", Style.ACCENT),
        Line(f"id {graph.rel_id}", Style.ACCENT),
        Line(f"occupancy {graph.occupancy or 'unspecified'}", Style.NORMAL),
        Line(f"view {graph.default_view or 'default'}", Style.DIM),
        Line(f"blurb {graph.description or 'none recorded'}", Style.NORMAL),
        Line(f"hand-off {', '.join(graph.handoff) or 'none offered'}", Style.NORMAL),
        Line(f"file {graph.path}", Style.DIM),
        Line(f"load live copies from {user_folder_hint()}", Style.DIM),
    )
    return ViewModel(
        screen=ScreenId.GRAPH_DETAIL,
        title=f"Graph: {graph.title}",
        detail=detail,
        footer="esc back to the lane  q quit",
    )


def audit_view(history: Sequence[CommandResult], selected: int = 0) -> ViewModel:
    """Build the operator log.

    Args:
        history: Dispatched commands, oldest first.
        selected: Row the app wants focused.

    Returns:
        One row per dispatch, coloured by how it ended.
    """
    rows: list[Row] = []
    for index, result in enumerate(history):
        if not result.ran:
            badge, style = "skipped", Style.DIM
        elif result.returncode == 0:
            badge, style = "ok", Style.OK
        else:
            badge, style = "fail", Style.BAD
        rows.append(
            Row(
                key=str(index),
                label=result.action_id,
                badge=badge,
                note=f"exit {'?' if result.returncode == UNMEASURED else result.returncode}"
                f"  {result.duration_s:.1f}s  {' '.join(result.argv)}",
                enabled=True,
                style=style,
            )
        )
    if rows:
        detail = (Line(f"{len(rows)} commands dispatched", Style.DIM),)
    else:
        detail = (Line("nothing dispatched yet this session", Style.DIM),)
    return ViewModel(
        screen=ScreenId.AUDIT,
        title="Operator log",
        rows=tuple(rows),
        detail=detail,
        footer="enter show the outcome  esc back  q quit",
        selected=_clamp(selected, len(rows)),
    )


def help_view(bindings: tuple[tuple[str, str, str], ...]) -> ViewModel:
    """Build the key reference and the safety contract in plain sentences.

    The loop hands over its own table so the reference can never advertise a
    key the loop ignores, or go quiet about one it honors.

    Args:
        bindings: ``(keys, scope, meaning)`` per row, as the loop dispatches them.

    Returns:
        A screen that states, in words, what the console will not do without a
        typed confirmation, a green guard, or the operator lock.
    """
    rows = tuple(
        Row(key=keys, label=keys, badge=scope, note=meaning, enabled=False, style=Style.NORMAL)
        for keys, scope, meaning in bindings
    )
    sentences: tuple[str, ...] = (
        "Nothing runs until every guard reports green.",
        "A reading that cannot be taken blocks the action instead of guessing.",
        "A heavy action asks you to type yes; a destructive one asks for DELETE.",
        "The child script asks again: the console never answers the prompt for you.",
        "One console holds the operator lock, so two people cannot dispatch at once.",
        "Dry run prints the argv and spawns nothing.",
    )
    detail = (
        Line("Keys", Style.BOLD),
        Line("Safety contract", Style.BOLD),
        *(Line(sentence, Style.NORMAL) for sentence in sentences),
    )
    return ViewModel(
        screen=ScreenId.HELP,
        title="Help",
        rows=rows,
        detail=detail,
        footer="esc back  q quit",
    )


def render(model: ViewModel, width: int, height: int) -> Frame:
    """Lay a view model out for one screen, clipped to the geometry.

    The focused row always draws reversed so the cursor stays visible; a
    non-focused row that is disabled draws dimmed. The frame never carries more
    than ``height`` lines and pads the body out to exactly ``height``, so a tiny
    terminal loses rows rather than crashing.

    Args:
        model: The screen to draw.
        width: Columns available.
        height: Rows available.

    Returns:
        Title row on top, detail then rows below it, key strip on the last row.
    """
    title = Line(_clip(model.title, width), Style.TITLE)
    footer = Line(_clip(model.footer, width), Style.DIM)
    if height <= 1:
        return Frame(title=model.title, lines=(title,) if height == 1 else (), footer=model.footer)
    body = [Line(_clip(line.text, width), line.style) for line in model.detail]
    body.extend(
        _row_line(row, model.selected, index, width)
        for index, row in enumerate(model.rows)
    )
    budget = height - 2
    shown = body[:budget]
    lines = [title, *shown]
    lines.extend(Line("", Style.DIM) for _ in range(budget - len(shown)))
    lines.append(footer)
    return Frame(title=model.title, lines=tuple(lines), footer=model.footer)

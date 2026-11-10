"""Shared vocabulary for the studio TUI: the seam every other module codes against.

The console is a dispatcher, not a reimplementation. Nothing in this package
builds a docker command line, writes ``.occupancy.json``, or decides on its own
what is safe: it describes actions declaratively (:class:`ActionSpec`), reads the
machine through the scripts that already own those answers, and hands a vetted
``argv`` to :mod:`tui.runner`. Keeping every cross-module type here means the
catalog, the guard, the read model, the renderer, and the app loop never import
each other for a data shape.

Design rules this file enforces by construction:

* An action is data. :class:`ActionSpec` carries the ``argv`` it runs, the risk
  tier it falls in, the confirmation token its real child script demands, and
  the guards that must be GREEN before it may run. There is no path from a
  keystroke to ``execve`` that does not pass through a catalog entry, so the
  console cannot be talked into running something the repo does not already
  expose as a verb or a utility.
* Guards fail closed. An unmeasurable reading (unreadable ``/proc/meminfo``, a
  ``/queue`` probe that will not answer) becomes a :class:`GuardVerdict` with
  ``allowed=False``, matching ``comfy_queue_busy`` in ``scripts/lib/occupancy.sh``
  and ``host_free_mem_gib`` in ``scripts/lib/safety.sh``, which returns ``0``
  rather than guessing.
* The confirmation token is collected here as data and typed by the operator in
  the TUI. The package never sets ``LAB_NON_INTERACTIVE`` or
  ``LAB_CONFIRM_TOKEN``, so ``require_heavy_confirm`` and
  ``require_delete_confirm`` stay live in the child process.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, TypedDict

# ---------------------------------------------------------------------------
# Machine floors, mirrored from scripts/lib/safety.sh.
#
# tests/python/test_tui_contract.py pins these to the shell source so a bump
# there that forgets the console fails the suite. The console blocks on the
# same floors the CLI blocks on; it never invents its own.
# ---------------------------------------------------------------------------

MIN_HOST_FREE_GIB = 28
"""Free-RAM floor in GiB below which a heavy stack start is refused.

Mirrors ``MIN_HOST_FREE_GIB`` in ``scripts/lib/safety.sh``.
"""

MIN_DISK_FREE_GIB = 40
"""Free-disk floor in GiB below which a heavy stack start is refused.

Mirrors ``MIN_DISK_FREE_GIB`` in ``scripts/lib/safety.sh``.
"""

UNMEASURED = -1
"""Sentinel for a reading that could not be taken.

Any guard that sees this value blocks: the console treats "unknown" as "not
safe", never as "probably fine".
"""


class RiskTier(enum.Enum):
    """How much an action can hurt, and therefore how hard the console gates it."""

    READ = "read"
    """T0: observes only. No confirmation, always offered."""

    WRITE = "write"
    """T1: changes state and is readily reversible. Plain selection, no retype."""

    HEAVY = "heavy"
    """T2: consumes the GPU or rewrites deployment state. Needs a typed ``yes``."""

    DESTRUCTIVE = "destructive"
    """T3: deletes data or reboots state that cannot be restored. Needs ``DELETE``."""

    REFUSED = "refused"
    """T4: policy-blocked. Rendered with its reason; never runnable."""

    def requires_token(self) -> bool:
        """Whether selecting this tier must be followed by typing a token.

        Returns:
            True for the tiers whose child script demands a typed answer.
        """
        return self in (RiskTier.HEAVY, RiskTier.DESTRUCTIVE)

    def label(self) -> str:
        """Short badge shown in the status column.

        Returns:
            Upper-case tag at most 11 characters wide.
        """
        return {
            RiskTier.READ: "read",
            RiskTier.WRITE: "write",
            RiskTier.HEAVY: "HEAVY",
            RiskTier.DESTRUCTIVE: "DELETE",
            RiskTier.REFUSED: "REFUSED",
        }[self]


class ConfirmKind(enum.Enum):
    """The literal the child script reads from stdin, per ``scripts/lib/safety.sh``."""

    NONE = "none"
    """The child asks nothing."""

    YES = "yes"
    """``require_heavy_confirm`` reads and accepts exactly ``yes``."""

    DELETE = "DELETE"
    """``require_delete_confirm`` reads and accepts exactly ``DELETE``."""

    def token(self) -> str:
        """The exact string the operator must retype, and that is piped to the child.

        Returns:
            The literal token, or the empty string when none is needed.
        """
        return "" if self is ConfirmKind.NONE else self.value


class Group(enum.Enum):
    """A left-rail section of the console."""

    DASHBOARD = "dashboard"
    """Health, guards, quick actions, recent operator log."""

    STACK = "stack"
    """Setup, start, stop, restart, update, logs, doctor."""

    LANES = "lanes"
    """The nine ``workflows/_lab`` lanes and their graphs."""

    MODELS = "models"
    """Model tier downloads, bandwidth cap, HF cache hygiene."""

    SIDECARS = "sidecars"
    """LLM, agent, Blender, and the four in-tree MCP servers."""

    OCCUPANCY = "occupancy"
    """The XOR occupancy desk: park Comfy, enter a mode."""

    FILM = "film"
    """Shot printing, film gates, proxies, concat, audio finishing."""

    DISK = "disk"
    """Model cache and disk reclaim, stack state cleanup."""

    AUDIT = "audit"
    """Operator log and command history."""

    HELP = "help"
    """Key bindings and the safety contract."""

    @property
    def hotkey(self) -> str:
        """Digit that jumps to this section.

        Returns:
            A single character, ``1`` through ``0``.
        """
        order = (
            Group.DASHBOARD,
            Group.STACK,
            Group.LANES,
            Group.MODELS,
            Group.SIDECARS,
            Group.OCCUPANCY,
            Group.FILM,
            Group.DISK,
            Group.AUDIT,
            Group.HELP,
        )
        index = order.index(self)
        return "0" if index == 9 else str(index + 1)


class RunnerKind(enum.Enum):
    """Which entry point owns the target of an action."""

    MANAGE = "manage"
    """``scripts/manage.sh <verb> ...`` (also reachable as ``//:manage``)."""

    UTILITY = "utility"
    """``scripts/utilities/<name>.sh ...`` for the utilities with no verb."""

    INTERNAL = "internal"
    """Handled inside the console; nothing is spawned (navigation and views)."""


class Guard(enum.Enum):
    """A precondition the guard layer must prove GREEN before an action runs.

    Every member is evaluated by :func:`tui.guard.evaluate`; a guard whose input
    cannot be read yields a blocking verdict, so a broken probe never silently
    green-lights a heavy job.
    """

    STACK_RUNNING = "stack_running"
    """Compose reports the studio stack running."""

    STACK_STOPPED = "stack_stopped"
    """Compose reports the studio stack stopped or absent."""

    HEADROOM_OK = "headroom_ok"
    """Free RAM and free disk both sit at or above :data:`MIN_HOST_FREE_GIB` / :data:`MIN_DISK_FREE_GIB`."""

    QUEUE_IDLE = "queue_idle"
    """The ComfyUI ``/queue`` is idle or unreachable while the stack is down."""

    OCCUPANCY_IDLE = "occupancy_idle"
    """The occupancy desk reads ``idle``."""

    OCCUPANCY_PARKED = "occupancy_parked"
    """Comfy is parked (``parked`` true) so a sidecar may take the GPU."""

    NO_HF_DOWNLOAD = "no_hf_download"
    """No live Hugging Face download pid under ``MODELS_DIR``."""

    NO_LLM_SIDECAR = "no_llm_sidecar"
    """The host llama-server is not holding the GPU."""

    DISK_PLAN_ONLY = "disk_plan_only"
    """A reclaim action is in plan mode; apply needs the destructive tier on top."""

    PACKS_READY = "packs_ready"
    """The model packs the action needs report ready."""

    def explain(self) -> str:
        """Operator-facing reason shown when this guard blocks.

        Returns:
            A short sentence naming what has to change.
        """
        return _GUARD_REASONS[self]


_GUARD_REASONS: dict[Guard, str] = {
    Guard.STACK_RUNNING: "the studio stack must be running for this",
    Guard.STACK_STOPPED: "stop the studio stack first",
    Guard.HEADROOM_OK: (
        f"free RAM or disk is under the floor ({MIN_HOST_FREE_GIB} GiB RAM / "
        f"{MIN_DISK_FREE_GIB} GiB disk)"
    ),
    Guard.QUEUE_IDLE: "the ComfyUI queue still has a job in flight",
    Guard.OCCUPANCY_IDLE: "the occupancy desk is not idle",
    Guard.OCCUPANCY_PARKED: "the stack is not parked for a sidecar",
    Guard.NO_HF_DOWNLOAD: "a model download is still running",
    Guard.NO_LLM_SIDECAR: "the LLM sidecar is holding the GPU",
    Guard.DISK_PLAN_ONLY: "this is plan mode only until you confirm apply",
    Guard.PACKS_READY: "the model pack this needs is not downloaded",
}
"""Blocking sentence per guard, shown in the detail pane and the confirm dialog."""


class ParamKind(enum.Enum):
    """How a parameter is collected from the operator."""

    CHOICE = "choice"
    """Pick one from a fixed list."""

    TEXT = "text"
    """Free text (a slug, a path, a number as text)."""

    FLAG = "flag"
    """Boolean switch appended when true."""

    INT = "int"
    """Digits only, bounded by :attr:`ParamSpec.low` / :attr:`ParamSpec.high`."""


class ArgvStyle(enum.Enum):
    """How a parameter value is joined to its flag."""

    SPACED = "spaced"
    """``--tier turbo``."""

    EQUALS = "equals"
    """``--limit=auto``."""

    POSITIONAL = "positional"
    """Bare positional argument; :attr:`ParamSpec.flag` is unused."""


@dataclass(frozen=True)
class Choice:
    """One option in a :attr:`ParamKind.CHOICE` parameter."""

    value: str
    """The string appended to the argv."""

    label: str
    """What the operator sees."""

    note: str = ""
    """Optional trailing hint (size, risk, what it pulls)."""


@dataclass(frozen=True)
class ParamSpec:
    """One operator-supplied argument of an action."""

    name: str
    """Stable key used to store the operator's answer."""

    label: str
    """Prompt text shown when collecting the answer."""

    kind: ParamKind
    """How the answer is collected."""

    flag: str = ""
    """Leading flag, empty for a positional."""

    argv_style: ArgvStyle = ArgvStyle.SPACED
    """How the flag and value are joined."""

    choices: tuple[Choice, ...] = ()
    """Options for a CHOICE parameter."""

    required: bool = True
    """Whether the action may run without an answer."""

    default: str = ""
    """Pre-filled answer."""

    low: int = 0
    """Inclusive lower bound for an INT parameter."""

    high: int = 1_000_000_000
    """Inclusive upper bound for an INT parameter."""

    help_text: str = ""
    """One-line explanation shown under the prompt."""


@dataclass(frozen=True)
class ActionSpec:
    """A runnable thing the console can offer, described entirely as data.

    The ``argv`` is built from :attr:`fixed_args` plus the operator's answers,
    then prefixed by the runner (see :mod:`tui.runner`). Nothing is passed
    through a shell, so quoting is not an operator-facing hazard.
    """

    action_id: str
    """Stable dotted id, ``group.verb`` by convention."""

    title: str
    """Imperative label shown in lists."""

    group: Group
    """Left-rail section the action belongs to."""

    summary: str
    """One line describing the effect, in operator terms."""

    runner: RunnerKind
    """Which entry point owns the target."""

    target: str
    """Verb for MANAGE, utility basename (no ``.sh``) for UTILITY, empty for INTERNAL."""

    fixed_args: tuple[str, ...] = ()
    """Arguments always appended, before any operator answer."""

    params: tuple[ParamSpec, ...] = ()
    """Operator-supplied arguments, in argv order."""

    tier: RiskTier = RiskTier.READ
    """Risk classification that drives gating."""

    confirm: ConfirmKind = ConfirmKind.NONE
    """Literal the real child script will read from stdin."""

    guards: tuple[Guard, ...] = ()
    """Preconditions that must be GREEN."""

    docs_target: str = ""
    """Bazel target or doc page that explains the action."""

    keywords: tuple[str, ...] = ()
    """Extra words the palette matches on."""

    refuse_reason: str = ""
    """Why a REFUSED action can never run; empty otherwise."""

    def is_runnable(self) -> bool:
        """Whether this action may ever be dispatched.

        Returns:
            False when policy blocks it outright.
        """
        return self.tier is not RiskTier.REFUSED


@dataclass(frozen=True)
class GuardVerdict:
    """The outcome of evaluating every guard for one action."""

    allowed: bool
    """True only when no guard blocked."""

    reasons: tuple[str, ...] = ()
    """Human-readable blockers, in the order they were found."""

    guards_failed: tuple[Guard, ...] = ()
    """Which guards blocked, for the detail pane."""

    stale: bool = False
    """True when a reading could not be taken and the verdict failed closed."""


@dataclass(frozen=True)
class CommandResult:
    """What came back from running one action."""

    action_id: str
    """The action that was dispatched."""

    argv: tuple[str, ...]
    """Exact argv that was executed."""

    returncode: int
    """Child exit status, or :data:`UNMEASURED` when it never ran."""

    output: str
    """Captured stdout and stderr, merged, already decoded."""

    duration_s: float
    """Wall-clock seconds spent in the child."""

    ran: bool
    """False when the run was blocked, refused, or a dry run."""

    note: str = ""
    """Why it did not run, or a trailing operator note."""


class Style(enum.Enum):
    """Drawing intent, mapped to real attributes by the screen implementation."""

    NORMAL = "normal"
    """Default foreground on background."""

    BOLD = "bold"
    """Emphasis for a label or heading."""

    DIM = "dim"
    """De-emphasis for a hint or a timestamp."""

    REVERSE = "reverse"
    """The focused row."""

    TITLE = "title"
    """Pane title."""

    OK = "ok"
    """Green: a guard is satisfied, a stack is up."""

    WARN = "warn"
    """Yellow: close to a floor, or a degraded backend."""

    BAD = "bad"
    """Red: a blocker, a failure, a refused action."""

    ACCENT = "accent"
    """Cyan: an identifier, a key name."""

    ALERT = "alert"
    """Red on reverse: a blocking banner."""


@dataclass(frozen=True)
class Line:
    """One rendered screen row."""

    text: str
    """Row content, at most the screen width."""

    style: Style
    """How to draw it."""


class Frame:
    """The complete picture of one screen, ready to draw.

    Attributes:
        title: Pane title drawn in the header.
        lines: Body rows, top to bottom.
        footer: Key-hint strip drawn on the last row.
    """

    __slots__ = ("title", "lines", "footer")

    def __init__(self, title: str, lines: tuple[Line, ...], footer: str) -> None:
        """Store one screen's worth of rows.

        Args:
            title: Pane title.
            lines: Body rows.
            footer: Key-hint strip.
        """
        self.title = title
        self.lines = lines
        self.footer = footer


class Key:
    """Normalized key names :meth:`Screen.read_key` returns.

    Printable characters come back as themselves; everything else is one of
    these constants so the keymap never hard-codes an escape sequence.
    """

    UP = "up"
    """Cursor up."""

    DOWN = "down"
    """Cursor down."""

    LEFT = "left"
    """Cursor left."""

    RIGHT = "right"
    """Cursor right."""

    ENTER = "enter"
    """Return / keypad enter."""

    BACKSPACE = "backspace"
    """Delete one character."""

    ESC = "esc"
    """Escape / go back."""

    PGUP = "pgup"
    """Page up."""

    PGDN = "pgdn"
    """Page down."""

    HOME = "home"
    """Jump to first."""

    END = "end"
    """Jump to last."""

    TAB = "tab"
    """Next pane or field."""

    BACKTAB = "backtab"
    """Previous pane or field."""

    RESIZE = "resize"
    """Terminal resized."""

    TIMEOUT = "timeout"
    """No key arrived before the read deadline."""

    QUIT = "quit"
    """Terminal closed under us."""


class Screen(Protocol):
    """The only drawing surface the app and views are allowed to use.

    Keeping this small (six methods) is what makes the whole console testable:
    the suite drives a fake that records rows, and the real curses adapter is a
    thin translation of these same six calls.
    """

    def size(self) -> tuple[int, int]:
        """Current geometry.

        Returns:
            ``(rows, cols)``, both at least 1.
        """
        ...

    def clear(self) -> None:
        """Erase the back buffer before a frame is drawn."""
        ...

    def draw(self, row: int, text: str, *, style: Style = Style.NORMAL) -> None:
        """Write one row.

        Args:
            row: Zero-based row index.
            text: Content; the implementation truncates to the width.
            style: Drawing intent.
        """
        ...

    def present(self) -> None:
        """Flush the drawn rows to the terminal in one update."""
        ...

    def read_key(self, timeout_s: float) -> str:
        """Wait for one keypress.

        Args:
            timeout_s: Seconds to wait before giving up.

        Returns:
            A :class:`Key` constant or a single printable character.
        """
        ...

    def bell(self) -> None:
        """Signal a refusal without moving anything on screen."""
        ...


class StackStatusJson(TypedDict, total=False):
    """Raw ``manage.sh status --json`` payload (``compose_status_json``)."""

    stack: str
    state: str
    attention: str
    host_free_gib: int


class OccupancyJson(TypedDict, total=False):
    """Raw ``manage.sh occupancy status --json`` payload."""

    version: int
    mode: str
    compose: bool
    parked: bool
    blender_pid: int
    mcp_pid: int
    llm_pid: int
    updated: str
    compose_live: bool
    queue: str
    llm_live: bool


class SpeedCacheJson(TypedDict, total=False):
    """Nested ``speed_cache`` object of the download-limit status payload."""

    path: str
    ttl_sec: int
    valid: bool
    measured_mbps: float
    age_sec: int
    source: str
    iface: str


class LimitStatusJson(TypedDict, total=False):
    """Raw ``manage.sh download-limit status --json`` payload."""

    interface: str
    tool: str
    auto_fraction: float
    shaping_supported: bool
    speed_cache: SpeedCacheJson


class PackJson(TypedDict, total=False):
    """Raw ``<download-*.sh> status --json`` payload for one model pack."""

    tier: str
    repo: str
    path: str
    size_gb: float
    min_gb: float
    ready: bool


class Health(TypedDict):
    """Everything the console knows about the machine right now.

    A missing probe is :data:`UNMEASURED` or an empty string, and the
    :mod:`tui.guard` layer turns that into a block. The keys are exactly the
    readings the status bar and the dashboard show.
    """

    stack_state: str
    """``running``, ``present``, ``stopped``, ``unknown``, or ``unmeasured``."""

    attention: str
    """Attention backend reported by the stack."""

    host_free_gib: int
    """Free RAM, or :data:`UNMEASURED`."""

    disk_free_gib: int
    """Free disk on ``MODELS_DIR``, or :data:`UNMEASURED`."""

    occupancy_mode: str
    """Occupancy desk mode, or ``unknown``."""

    parked: bool
    """Whether Comfy is parked."""

    queue: str
    """``idle``, ``busy``, or ``unmeasured``."""

    llm_live: bool
    """Whether the host LLM sidecar is up."""

    shaping: bool
    """Whether a bandwidth cap is active on the interface."""

    shaping_mbps: int
    """Active cap in Mbps, or :data:`UNMEASURED`."""

    downloads_running: bool
    """Whether a Hugging Face download pid is live."""

    packs: tuple[tuple[str, bool], ...]
    """``(pack id, ready)`` pairs for the model tiers."""

    errors: tuple[str, ...]
    """Every probe that failed, so the dashboard can say what is unknown."""


def empty_health() -> Health:
    """Build the health snapshot a cold console shows before its first poll.

    Returns:
        A :class:`Health` where every reading is unknown, which blocks all
        heavy actions until a real poll lands.
    """
    return Health(
        stack_state="unknown",
        attention="unknown",
        host_free_gib=UNMEASURED,
        disk_free_gib=UNMEASURED,
        occupancy_mode="unknown",
        parked=False,
        queue="unmeasured",
        llm_live=False,
        shaping=False,
        shaping_mbps=UNMEASURED,
        downloads_running=False,
        packs=(),
        errors=("no reading yet",),
    )


@dataclass
class SessionState:
    """Mutable per-run state the app loop threads through the views.

    Attributes:
        selected: Currently focused row in the active list.
        scroll: Top visible row of the active list.
        params: Answers collected for the action being confirmed.
        last_result: Outcome of the most recent dispatch.
        history: Dispatched commands, newest last.
        dry_run: When True, commands print their argv and do not run.
        read_only: When True, nothing but read-only actions may dispatch.
        poll_errors: Probe failures from the most recent poll.
    """

    selected: int = 0
    scroll: int = 0
    params: dict[str, str] = field(default_factory=dict)
    last_result: CommandResult | None = None
    history: list[CommandResult] = field(default_factory=list)
    dry_run: bool = False
    read_only: bool = False
    poll_errors: tuple[str, ...] = ()


class ScreenId(enum.Enum):
    """One screen the app loop can show.

    ``views`` builds a :class:`ViewModel` for each of these; ``app`` decides
    which one is on screen and how a key moves between them.
    """

    DASHBOARD = "dashboard"
    """Health, guards, quick actions."""

    GROUP = "group"
    """A filtered action list for one :class:`Group`."""

    LANES = "lanes"
    """The nine lab lanes."""

    LANE_GRAPHS = "lane_graphs"
    """Graphs inside one lane."""

    GRAPH_DETAIL = "graph_detail"
    """One graph: description, widgets, hand-off actions."""

    PARAM_FORM = "param_form"
    """Collecting the parameters an action needs."""

    CONFIRM = "confirm"
    """The typed-token gate."""

    PROGRESS = "progress"
    """A command is running; its tail streams here."""

    RESULT = "result"
    """The outcome of the last dispatch."""

    PALETTE = "palette"
    """Fuzzy search over every action."""

    AUDIT = "audit"
    """Recent dispatches."""

    LOG_TAIL = "log_tail"
    """Compose log lines."""

    HELP = "help"
    """Keys and the safety contract."""


@dataclass(frozen=True)
class Row:
    """One selectable line in a list view.

    A row is pure presentation of a decision the model already made: whether it
    is ``enabled`` comes from the guard layer, so a view can never offer a
    blocked action by accident.
    """

    key: str
    """Stable id (an ``action_id``, a lane id, a log index)."""

    label: str
    """Primary text."""

    badge: str = ""
    """Right-aligned tag: a risk tier, a state, a count."""

    note: str = ""
    """Trailing hint: the blocker, the size, the timestamp."""

    enabled: bool = True
    """False renders it dimmed and refuses selection."""

    style: Style = Style.NORMAL
    """Drawing intent for the label."""


@dataclass(frozen=True)
class ViewModel:
    """Everything one screen needs, with no reference to a terminal.

    Views return this and never touch a :class:`Screen`, which is what lets the
    suite assert on rendered content without a TTY and lets the app own the
    drawing.
    """

    screen: ScreenId
    """Which screen this is."""

    title: str
    """Header text."""

    rows: tuple[Row, ...] = ()
    """Selectable rows."""

    detail: tuple[Line, ...] = ()
    """Read-only pane above or beside the rows."""

    footer: str = ""
    """Key-hint strip."""

    selected: int = 0
    """Row index the view wants focused."""

    def row_keys(self) -> tuple[str, ...]:
        """The keys of the rows, in display order.

        Returns:
            One key per row.
        """
        return tuple(row.key for row in self.rows)


_TRUEISH: frozenset[str] = frozenset({"1", "true", "yes", "on", "y"})
"""Answers that mean a boolean flag is switched on."""


@dataclass(frozen=True)
class RunConfig:
    """Everything the app loop needs to start, resolved by :mod:`tui.cli`.

    Kept as data so the loop can be driven from a test with a fake screen and a
    temp directory, with no terminal and no real repo.

    Attributes:
        repo_root: The git checkout the console dispatches from.
        models_dir: Where model weights live; the disk guard reads it.
        comfy_output_dir: Where outputs, the occupancy file, and the console
            lock live.
        start_group: Section to open on instead of the dashboard.
        dry_run: Print the argv instead of running it.
        read_only: Refuse to dispatch anything that is not observe-only.
        use_color: False renders monochrome.
        timeout_s: Per-command wall-clock cap.
    """

    repo_root: Path
    models_dir: Path
    comfy_output_dir: Path
    start_group: Group = Group.DASHBOARD
    dry_run: bool = False
    read_only: bool = False
    use_color: bool = True
    timeout_s: float = 900.0


EXIT_OK = 0
"""Console exited cleanly, or a headless check passed."""

EXIT_USAGE = 1
"""Bad flags, or a headless check found a catalog defect."""

EXIT_NO_TTY = 2
"""Asked to draw without a terminal; ``--check`` is the headless path."""

EXIT_LOCKED = 3
"""Another console already holds the single-console flock."""


def build_argv(
    action: ActionSpec,
    answers: Mapping[str, str],
) -> tuple[str, ...]:
    """Assemble the exact argv an action will run with.

    The result is always a plain argument list: the console never builds a shell
    string, so an operator's text can only ever be one argv element.

    Args:
        action: The catalog entry.
        answers: Operator answers keyed by :attr:`ParamSpec.name`.

    Returns:
        ``fixed_args`` followed by each answered parameter in declaration order.

    Raises:
        ValueError: A required parameter is missing, a choice is not one of the
            offered values, or an integer answer falls outside its bounds.
    """
    argv: list[str] = list(action.fixed_args)
    for param in action.params:
        raw = answers.get(param.name, param.default)
        if not raw:
            if param.required:
                raise ValueError(f"{param.name}: {param.label} is required")
            continue
        if param.kind is ParamKind.FLAG:
            if raw not in _TRUEISH:
                continue
            if not param.flag:
                raise ValueError(f"{param.name}: a flag parameter needs a flag")
            argv.append(param.flag)
            continue
        if param.kind is ParamKind.CHOICE:
            allowed = tuple(choice.value for choice in param.choices)
            if raw not in allowed:
                raise ValueError(f"{param.name}: {raw!r} is not one of {allowed}")
        if param.kind is ParamKind.INT:
            if not raw.lstrip("-").isdigit():
                raise ValueError(f"{param.name}: {raw!r} is not a number")
            value = int(raw)
            if value < param.low or value > param.high:
                raise ValueError(
                    f"{param.name}: {value} is outside {param.low}..{param.high}"
                )
        if param.kind is ParamKind.TEXT and ("\x00" in raw or "\n" in raw):
            raise ValueError(f"{param.name}: no newlines or NUL bytes allowed")
        if param.kind is ParamKind.CHOICE and not param.flag:
            raise ValueError(f"{param.name}: a choice parameter needs a flag")
        if not param.flag:
            argv.append(raw)
        elif param.argv_style is ArgvStyle.EQUALS:
            argv.append(f"{param.flag}={raw}")
        else:
            argv.extend([param.flag, raw])
    return tuple(argv)

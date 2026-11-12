"""Declarative table of every action the operator console can offer.

This module is the whole allowlist. The console renders, searches, guards, and
dispatches only what appears in :data:`_ACTIONS`, so there is no route from a
keystroke to ``execve`` that does not start here: something that is not an
:class:`~tui.contract.ActionSpec` in this table cannot be selected, typed into,
or reached from the palette. Each entry carries the literal argv
(``fixed_args`` plus declared parameters), the risk tier that drives gating, the
confirmation token the real child script reads from stdin, and the guards the
guard layer must prove GREEN first.

Coverage is the contract, not a courtesy. Every ``case`` label in the
``scripts/manage.sh`` dispatcher has an entry, and so does every utility that
has no verb (:data:`UNMANAGED_UTILITIES`).
``tests/python/test_tui_catalog.py`` proves it by parsing the dispatcher text
with :func:`manage_verbs_in` and asserting :func:`missing_verbs` is empty, so a
verb added to the CLI that the console never learned about fails the suite.

An action is a name, never a reimplementation: it targets a verb or a utility
basename and lets ``scripts/manage.sh`` or ``scripts/utilities/<name>.sh`` own
the behaviour. The console builds no docker command line and reads no state.

Safety posture:

* Policy-blocked graphs (the MiniMax H3 family) are listed so the operator sees
  the refusal and the reason next to it, at :attr:`RiskTier.REFUSED`, which the
  runner will not dispatch.
* Nothing here pre-answers a confirmation. The typed token is collected by the
  console and piped to the child, where ``require_heavy_confirm`` and
  ``require_delete_confirm`` still make the decision.
* A child script that demands a ``--yes`` *flag* rather than a stdin prompt
  declares it as the optional :attr:`ParamKind.FLAG` parameter named
  ``confirm_yes``. The app sets that answer only after the operator types the
  token, so the flag is never baked into ``fixed_args``.
* Every operator answer becomes exactly one argv element; no action assembles a
  shell string. The internal bandwidth-cap wrapper (``download-limit wrap``,
  which takes an arbitrary command line) is deliberately not offered: it is a
  helper for the download verbs, not an operator action.
"""

from __future__ import annotations

import re

from tui.contract import (
    ActionSpec,
    ArgvStyle,
    Choice,
    ConfirmKind,
    Guard,
    Group,
    ParamKind,
    ParamSpec,
    RiskTier,
    RunnerKind,
)

MANAGE_DOCS_TARGET = "//:manage"
"""Bazel target that owns every dispatcher verb."""

UTILITY_DOCS_TARGET = "//scripts:run-utility"
"""Bazel target that runs an unmanaged utility by basename."""

_DISPATCHER_OPEN = re.compile(r'^\s*case\s+"\$\{cmd\}"\s+in\b')
"""Matches the dispatcher ``case`` line whose labels define the verb surface."""

_PATTERN_LINE = re.compile(r'^([A-Za-z0-9_*-]+(?:\s*\|\s*[A-Za-z0-9_*-]+)*)\)')
"""Matches one dispatcher pattern row, capturing its pipe-separated labels."""

UNMANAGED_UTILITIES: tuple[str, ...] = (
    "compile-film",
    "compress-cinema-clip",
    "concat-shots",
    "dub-fetch",
    "nvenc-preview",
    "pack-frames",
    "podcast-loudnorm",
    "spark-farm",
)
"""Utility basenames with no ``manage.sh`` verb, reachable only through a
:class:`RunnerKind.UTILITY` action."""

_H3_REFUSAL = (
    "MiniMax H3 is outside the US-safe catalog (US Excluded Territory); "
    "refused by refuse_minimax_h3"
)
"""Refusal sentence shown in place of every H3 action."""

_CONFIRM_YES_HELP = (
    "the console ticks this only after you type the confirmation token"
)
"""Help text shared by the optional ``--yes`` flag parameters."""

_JSON_HELP = "print the machine-readable payload instead of the table"
"""Help text shared by the ``--json`` flag parameters."""

_DRY_RUN_HELP = "print what would change and touch nothing"
"""Help text shared by the optional ``--dry-run`` flag parameters."""

_CORE_LANES: tuple[Choice, ...] = (
    Choice("photos", "photos"),
    Choice("video", "video"),
    Choice("social", "social"),
    Choice("business", "business"),
    Choice("film", "film"),
    Choice("audio", "audio"),
    Choice("3d", "3d"),
    Choice("guides", "guides"),
    Choice("labs", "labs"),
)
"""Promotion lanes, matching ``LANE_REGISTRY`` and :mod:`tui.lanes`."""

_FILM_CHOICES: tuple[Choice, ...] = (
    Choice("go-see", "go-see", "the shipped short"),
    Choice("still-here", "still-here", "the shipped short"),
    Choice("switchyard", "switchyard", "the shipped short"),
)
"""The shipped films, offered wherever a film slug is a flag rather than a
positional."""

_HEAVY_LAUNCH: tuple[Guard, ...] = (Guard.HEADROOM_OK,)
"""Guards for a heavy GPU launch: the console blocks under either floor."""

_GPU_WORK: tuple[Guard, ...] = (Guard.QUEUE_IDLE, Guard.OCCUPANCY_IDLE)
"""Guards for work that needs the one GB10 GPU to itself."""

_QUEUE_ON_COMFY: tuple[Guard, ...] = (
    Guard.STACK_RUNNING,
    Guard.QUEUE_IDLE,
    Guard.OCCUPANCY_IDLE,
)
"""Guards for an action that POSTs a graph into a running ComfyUI."""

_STOP_FIRST: tuple[Guard, ...] = (Guard.STACK_STOPPED,)
"""Guards for an NVENC or Blender dump that refuses while compose is up."""

_PLAN_ONLY: tuple[Guard, ...] = (Guard.DISK_PLAN_ONLY,)
"""Guards for a reclaim action that is reporting a plan, not applying one."""

_APPLY_SAFE: tuple[Guard, ...] = (Guard.NO_HF_DOWNLOAD,)
"""Guards for a delete or apply under ``MODELS_DIR``."""


def _flag(
    name: str,
    label: str,
    flag: str,
    *,
    help_text: str = "",
) -> ParamSpec:
    """Build an optional boolean switch parameter.

    Args:
        name: Stable answer key.
        label: Prompt text.
        flag: The flag appended when the operator switches it on.
        help_text: One-line explanation under the prompt.

    Returns:
        A :class:`ParamSpec` of kind :attr:`ParamKind.FLAG`.
    """
    return ParamSpec(
        name=name,
        label=label,
        kind=ParamKind.FLAG,
        flag=flag,
        required=False,
        help_text=help_text,
    )


def _yes(*, help_text: str = _CONFIRM_YES_HELP) -> ParamSpec:
    """Build the ``confirm_yes`` flag a child script demands as a flag.

    Args:
        help_text: One-line explanation under the prompt.

    Returns:
        An optional ``--yes`` flag parameter named ``confirm_yes``.
    """
    return _flag("confirm_yes", "Confirm with --yes", "--yes", help_text=help_text)


def _text(
    name: str,
    label: str,
    flag: str,
    *,
    required: bool = True,
    default: str = "",
    help_text: str = "",
) -> ParamSpec:
    """Build a free-text parameter joined to ``flag`` by a space.

    Args:
        name: Stable answer key.
        label: Prompt text.
        flag: Leading flag.
        required: Whether the action may run without an answer.
        default: Pre-filled answer.
        help_text: One-line explanation under the prompt.

    Returns:
        A :class:`ParamSpec` of kind :attr:`ParamKind.TEXT`.
    """
    return ParamSpec(
        name=name,
        label=label,
        kind=ParamKind.TEXT,
        flag=flag,
        required=required,
        default=default,
        help_text=help_text,
    )


def _pos(
    name: str,
    label: str,
    *,
    required: bool = True,
    default: str = "",
    help_text: str = "",
) -> ParamSpec:
    """Build a bare positional free-text parameter.

    Args:
        name: Stable answer key.
        label: Prompt text.
        required: Whether the action may run without an answer.
        default: Pre-filled answer.
        help_text: One-line explanation under the prompt.

    Returns:
        A :class:`ParamSpec` with no flag and
        :attr:`ArgvStyle.POSITIONAL` joining.
    """
    return ParamSpec(
        name=name,
        label=label,
        kind=ParamKind.TEXT,
        argv_style=ArgvStyle.POSITIONAL,
        required=required,
        default=default,
        help_text=help_text,
    )


def _int(
    name: str,
    label: str,
    flag: str,
    low: int,
    high: int,
    *,
    required: bool = True,
    default: str = "",
    help_text: str = "",
) -> ParamSpec:
    """Build a bounded integer parameter.

    Args:
        name: Stable answer key.
        label: Prompt text.
        flag: Leading flag.
        low: Inclusive lower bound.
        high: Inclusive upper bound.
        required: Whether the action may run without an answer.
        default: Pre-filled answer.
        help_text: One-line explanation under the prompt.

    Returns:
        A :class:`ParamSpec` of kind :attr:`ParamKind.INT`.
    """
    return ParamSpec(
        name=name,
        label=label,
        kind=ParamKind.INT,
        flag=flag,
        required=required,
        default=default,
        low=low,
        high=high,
        help_text=help_text,
    )


def _choice(
    name: str,
    label: str,
    flag: str,
    *values: str,
    required: bool = True,
    default: str = "",
    help_text: str = "",
) -> ParamSpec:
    """Build a parameter whose answer must be one of ``values``.

    Args:
        name: Stable answer key.
        label: Prompt text.
        flag: Leading flag; a choice parameter always needs one.
        *values: Offered argv values, in menu order.
        required: Whether the action may run without an answer.
        default: Pre-filled answer.
        help_text: One-line explanation under the prompt.

    Returns:
        A :class:`ParamSpec` of kind :attr:`ParamKind.CHOICE`.
    """
    return ParamSpec(
        name=name,
        label=label,
        kind=ParamKind.CHOICE,
        flag=flag,
        choices=tuple(Choice(value, value) for value in values),
        required=required,
        default=default,
        help_text=help_text,
    )


def _verb(
    action_id: str,
    title: str,
    group: Group,
    summary: str,
    verb: str,
    args: tuple[str, ...] = (),
    *,
    params: tuple[ParamSpec, ...] = (),
    tier: RiskTier = RiskTier.READ,
    confirm: ConfirmKind = ConfirmKind.NONE,
    guards: tuple[Guard, ...] = (),
    keywords: tuple[str, ...] = (),
    refuse_reason: str = "",
) -> ActionSpec:
    """Build an action dispatched as ``scripts/manage.sh <verb> ...``.

    Args:
        action_id: Stable dotted id.
        title: Imperative label shown in lists.
        group: Left-rail section.
        summary: One operator-facing line about the effect.
        verb: The dispatcher label, which is also the target.
        args: Extra arguments appended right after the verb.
        params: Operator-supplied arguments, in argv order.
        tier: Risk classification.
        confirm: Literal the child reads from stdin.
        guards: Preconditions that must be GREEN.
        keywords: Extra words the palette matches on.
        refuse_reason: Why a policy-blocked action can never run.

    Returns:
        A catalog entry with :attr:`RunnerKind.MANAGE`.
    """
    return ActionSpec(
        action_id=action_id,
        title=title,
        group=group,
        summary=summary,
        runner=RunnerKind.MANAGE,
        target=verb,
        fixed_args=(verb, *args),
        params=params,
        tier=tier,
        confirm=confirm,
        guards=guards,
        docs_target=MANAGE_DOCS_TARGET,
        keywords=keywords,
        refuse_reason=refuse_reason,
    )


def _utility(
    action_id: str,
    title: str,
    group: Group,
    summary: str,
    utility: str,
    args: tuple[str, ...] = (),
    *,
    params: tuple[ParamSpec, ...] = (),
    tier: RiskTier = RiskTier.READ,
    confirm: ConfirmKind = ConfirmKind.NONE,
    guards: tuple[Guard, ...] = (),
    keywords: tuple[str, ...] = (),
) -> ActionSpec:
    """Build an action dispatched as ``scripts/utilities/<utility>.sh ...``.

    Args:
        action_id: Stable dotted id.
        title: Imperative label shown in lists.
        group: Left-rail section.
        summary: One operator-facing line about the effect.
        utility: Utility basename without the ``.sh`` suffix.
        args: Arguments always appended, including any subcommand.
        params: Operator-supplied arguments, in argv order.
        tier: Risk classification.
        confirm: Literal the child reads from stdin.
        guards: Preconditions that must be GREEN.
        keywords: Extra words the palette matches on.

    Returns:
        A catalog entry with :attr:`RunnerKind.UTILITY`.
    """
    return ActionSpec(
        action_id=action_id,
        title=title,
        group=group,
        summary=summary,
        runner=RunnerKind.UTILITY,
        target=utility,
        fixed_args=args,
        params=params,
        tier=tier,
        confirm=confirm,
        guards=guards,
        docs_target=UTILITY_DOCS_TARGET,
        keywords=keywords,
    )


def _refused(
    action_id: str,
    title: str,
    group: Group,
    summary: str,
    verb: str,
    keywords: tuple[str, ...] = (),
) -> ActionSpec:
    """Build a policy-blocked entry that is shown but never dispatched.

    Args:
        action_id: Stable dotted id.
        title: Imperative label shown in lists.
        group: Left-rail section.
        summary: One operator-facing line about the effect.
        verb: The dispatcher label that refuses.
        keywords: Extra words the palette matches on.

    Returns:
        A catalog entry at :attr:`RiskTier.REFUSED` with its reason filled in.
    """
    return _verb(
        action_id,
        title,
        group,
        summary,
        verb,
        tier=RiskTier.REFUSED,
        keywords=keywords,
        refuse_reason=_H3_REFUSAL,
    )


_ACTIONS: tuple[ActionSpec, ...] = (
    # ------------------------------------------------------------------
    # Help: the CLI's own usage text, so the verb surface is complete.
    # ------------------------------------------------------------------
    _verb(
        "help.usage",
        "Show the CLI usage",
        Group.HELP,
        "Print the manage.sh command list, the same text the CLI prints for "
        "help, -h, and --help.",
        "help",
        keywords=("usage", "commands", "docs"),
    ),
    # ------------------------------------------------------------------
    # Dashboard: the read-only readings the health pane shows.
    # ------------------------------------------------------------------
    _verb(
        "dashboard.status",
        "Show stack status",
        Group.DASHBOARD,
        "Read the compose state, the attention backend, and free host RAM.",
        "status",
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("health", "state", "attention"),
    ),
    _verb(
        "dashboard.doctor",
        "Run doctor",
        Group.DASHBOARD,
        "Preflight docker, GPU, RAM and disk headroom, attention, models, and "
        "the output dir.",
        "doctor",
        keywords=("preflight", "diagnose", "health"),
    ),
    _verb(
        "dashboard.report_bug",
        "File a bug from a failure",
        Group.DASHBOARD,
        "Print, save, and link a bug report for a command-line or bazelisk "
        "failure. Nothing is submitted; the URL and the saved markdown are.",
        "report-bug",
        params=(
            _choice(
                "surface",
                "Surface",
                "--surface",
                "cli",
                "bazel",
                "compose",
                "download",
                "tui",
                required=False,
                default="cli",
                help_text="which part of the stack failed",
            ),
            _text(
                "command",
                "Command line",
                "--command",
                required=False,
                help_text="the failing command, quoted",
            ),
            _int(
                "exit_code",
                "Exit status",
                "--exit",
                0,
                255,
                required=False,
                default="1",
                help_text="the status it returned",
            ),
            _text(
                "log",
                "Log file",
                "--log",
                required=False,
                help_text="log whose tail is attached as ## Command output",
            ),
            _text(
                "title",
                "Summary",
                "--title",
                required=False,
                help_text="the one line the issue is filed under",
            ),
        ),
        tier=RiskTier.WRITE,
        keywords=("bug", "report", "issue", "github", "crash", "template"),
    ),
    _verb(
        "dashboard.spark_timing_show",
        "Show the kitchen timing table",
        Group.DASHBOARD,
        "Print the recorded wall-clock per graph family from spark-timing.json.",
        "spark-timing",
        ("show",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("timing", "wall clock", "kitchen"),
    ),
    _utility(
        "dashboard.spark_farm_status",
        "Probe the extra Sparks",
        Group.DASHBOARD,
        "SSH each SPARK_HOSTS worker for docker state, disk, GPU, and fabric ping.",
        "spark-farm",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("farm", "worker", "fabric"),
    ),
    # ------------------------------------------------------------------
    # Stack: host bootstrap and the compose lifecycle.
    # ------------------------------------------------------------------
    _verb(
        "stack.setup",
        "Bootstrap the host",
        Group.STACK,
        "Create .env, prepare MODELS_DIR and the output dir with sudo, install "
        "Docker CE and the hf CLI, then run doctor.",
        "setup",
        params=(
            _flag("install_docker", "Install Docker CE", "--install-docker"),
            _yes(),
        ),
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        keywords=("bootstrap", "sudo", "apt", "docker"),
    ),
    _verb(
        "stack.setup_client",
        "Set up an operator laptop",
        Group.STACK,
        "Install git, ssh, and python3, add the SSH key, and write the "
        "Host ez-spark LocalForward. Never starts Comfy.",
        "setup-client",
        params=(
            _text("host", "Spark host", "--host", required=False),
            _text("user", "SSH user", "--user", required=False),
            _int("port", "Comfy port", "--port", 1, 65535, required=False),
        ),
        tier=RiskTier.WRITE,
        keywords=("laptop", "ssh", "tunnel", "client"),
    ),
    _verb(
        "stack.onboard",
        "Onboard this machine",
        Group.STACK,
        "Run setup on a Spark, or set up the laptop and then clone, set up, and "
        "doctor the Spark over ssh. Never auto-starts.",
        "onboard",
        params=(_flag("download", "Download the core packs", "--download"),),
        tier=RiskTier.WRITE,
        keywords=("bootstrap", "clone", "remote"),
    ),
    _verb(
        "stack.spark_ui",
        "Open the forwarded ComfyUI",
        Group.STACK,
        "Print and open the ssh -N -L forwarded ComfyUI URL for Host ez-spark.",
        "spark-ui",
        tier=RiskTier.WRITE,
        keywords=("port forward", "browser", "ui"),
    ),
    _verb(
        "stack.start",
        "Start the studio stack",
        Group.STACK,
        "Start the ComfyUI stack detached. The heaviest thing the console does: "
        "it takes the unified memory and the GPU.",
        "start",
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        guards=_HEAVY_LAUNCH,
        keywords=("up", "compose up", "gpu"),
    ),
    _verb(
        "stack.stop",
        "Stop the studio stack",
        Group.STACK,
        "Stop compose and keep models, outputs, and the comfy-state volume.",
        "stop",
        tier=RiskTier.WRITE,
        keywords=("down", "compose down"),
    ),
    _verb(
        "stack.restart",
        "Restart the studio stack",
        Group.STACK,
        "Stop and start again, which re-enters the heavy confirm for the start.",
        "restart",
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        guards=_HEAVY_LAUNCH,
        keywords=("reboot", "bounce"),
    ),
    _verb(
        "stack.update_stack",
        "Redeploy from the checked-out branch",
        Group.STACK,
        "Fast-forward pull, match the image lane to the branch, then restart "
        "through start. Refuses a dirty tree and a detached HEAD.",
        "update-stack",
        params=(
            _flag("dry_run", "Dry run", "--dry-run", help_text=_DRY_RUN_HELP),
            _text("branch", "Branch", "--branch", required=False),
            _yes(),
        ),
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        keywords=("deploy", "pull", "upgrade"),
    ),
    _verb(
        "stack.logs",
        "Follow the compose logs",
        Group.STACK,
        "Tail the stack logs from compose.",
        "logs",
        params=(_int("tail", "Lines", "--tail", 1, 100_000, required=False),),
        keywords=("log", "tail"),
    ),
    # ------------------------------------------------------------------
    # Lanes: promoted lab graphs and the album queue.
    # ------------------------------------------------------------------
    _verb(
        "lanes.promote_workflow",
        "Promote a live graph into the lab",
        Group.LANES,
        "Copy one live _user graph into workflows/_lab/<lane>/ as a promoted "
        "graph. Copies only; it does not commit.",
        "promote-workflow",
        params=(
            _text("source", "Source graph", "--from"),
            ParamSpec(
                name="lane",
                label="Lane",
                kind=ParamKind.CHOICE,
                flag="--lane",
                choices=_CORE_LANES,
                help_text="the lab lane the graph lands in",
            ),
            _text("graph_id", "Graph stem", "--id", help_text="filename without .json"),
            _text("subdir", "Subdir", "--subdir", required=False),
        ),
        tier=RiskTier.WRITE,
        keywords=("lab", "graph", "promote", "_user"),
    ),
    _verb(
        "lanes.album_render_status",
        "List shipped albums",
        Group.LANES,
        "Report the shipped albums the renderer knows about.",
        "album-render",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("album", "music", "cover"),
    ),
    _verb(
        "lanes.album_render",
        "Render one shipped album",
        Group.LANES,
        "Queue every track of a shipped album and zip the result. The stack must "
        "already be running.",
        "album-render",
        ("run",),
        params=(
            _text("album", "Artist/Slug", "--album", help_text="ARTIST/SLUG"),
            ParamSpec(
                name="art",
                label="Cover art",
                kind=ParamKind.CHOICE,
                flag="--art",
                choices=(
                    Choice("skip", "skip", "keep the existing cover"),
                    Choice("upload", "upload", "use the file on disk"),
                    Choice("generate", "generate", "render a new cover"),
                ),
                required=False,
            ),
            _text("quality", "Quality tier", "--quality", required=False),
        ),
        tier=RiskTier.WRITE,
        guards=_QUEUE_ON_COMFY,
        keywords=("album", "queue", "zip"),
    ),
    _verb(
        "lanes.album_pack",
        "Zip a rendered album",
        Group.LANES,
        "Package the rendered tracks of one album without queueing anything.",
        "album-render",
        ("pack",),
        params=(
            _text("album", "Artist/Slug", "--album", help_text="ARTIST/SLUG"),
            _text("out", "Output dir", "--out", required=False),
        ),
        tier=RiskTier.WRITE,
        keywords=("album", "package", "zip"),
    ),
    _verb(
        "lanes.song_export",
        "Export a song for a DAW",
        Group.LANES,
        "Convert one master into a hand-off bundle: MIDI, MusicXML, the timeline "
        "JSON, and per-lane MIDI and WAV stems. CPU only; no queue.",
        "export-song",
        params=(
            _pos("audio", "Master audio", help_text="audio file to convert"),
            _pos("out_dir", "Output dir", help_text="bundle parent folder"),
            _text("title", "Title", "--title", required=False),
            _flag("no_stems", "Skip stems", "--no-stems", help_text="MIDI only, no WAV stems"),
        ),
        tier=RiskTier.WRITE,
        keywords=("midi", "musicxml", "daw", "stems", "transcribe"),
    ),
    _verb(
        "lanes.icon_pack",
        "Build an Android icon pack",
        Group.LANES,
        "Write a store-ready adaptive icon pack from the catalog, then run the "
        "compliance gate over it.",
        "icon-pack",
        params=(
            _text("out", "Output dir", "--out"),
            _flag("validate_only", "Validate only", "--validate-only"),
            _flag("dry_run", "Dry run", "--dry-run", help_text=_DRY_RUN_HELP),
        ),
        tier=RiskTier.WRITE,
        keywords=("icon", "android", "adaptive", "play store"),
    ),
    _verb(
        "lanes.icon_scaffold",
        "Add one app to the icon catalog",
        Group.LANES,
        "Print the override row a newly released app needs, ready to paste into "
        "the operator catalog.",
        "icon-pack",
        params=(
            _text("scaffold", "Slug", "--scaffold", help_text="new-app-slug"),
            _text("name", "Label", "--name", required=False),
            _text(
                "package",
                "Package",
                "--package",
                required=False,
                help_text="com.example.app",
            ),
            _text("glyph", "Glyph", "--glyph", required=False),
        ),
        tier=RiskTier.READ,
        keywords=("icon", "scaffold", "new app", "catalog"),
    ),
    _verb(
        "lanes.watch_face",
        "Build a Wear OS watch face",
        Group.LANES,
        "Emit a submittable Watch Face Format project and gate it on the ambient, "
        "size, and complication-slot limits.",
        "watch-face",
        params=(
            _text("out", "Output dir", "--out"),
            _text("face", "Face slug", "--face", required=False),
            _flag("validate_only", "Validate only", "--validate-only"),
            _flag("dry_run", "Dry run", "--dry-run", help_text=_DRY_RUN_HELP),
        ),
        tier=RiskTier.WRITE,
        keywords=("watch", "wear", "wff", "play store"),
    ),
    _verb(
        "lanes.tones_pack",
        "Build an Android tone pack",
        Group.LANES,
        "Render the tone catalog and package ringtones, notifications, and alarms "
        "as WAV, M4A, and OGG with the launcher manifest.",
        "tones-pack",
        params=(
            _text("out", "Output dir", "--out"),
            _text("tone", "Tone slug", "--tone", required=False),
            _flag("dry_run", "Dry run", "--dry-run", help_text=_DRY_RUN_HELP),
        ),
        tier=RiskTier.WRITE,
        keywords=("ringtone", "notification", "alarm", "tone", "play store"),
    ),
    # ------------------------------------------------------------------
    # Models: packs, the bandwidth cap, and HF cache hygiene.
    # ------------------------------------------------------------------
    _verb(
        "models.download_models",
        "Download the core packs",
        Group.MODELS,
        "Pull the Apache still pack, Wan 2.2 5B, and the LTX distilled pack "
        "under the bandwidth cap.",
        "download-models",
        params=(
            _text(
                "limit",
                "Bandwidth cap",
                "--limit",
                required=False,
                default="auto",
                help_text="auto, off, or a fixed Mbps number",
            ),
            _flag(
                "drop_incomplete",
                "Drop stuck partials first",
                "--drop-incomplete",
                help_text="deletes *.incomplete under MODELS_DIR before resuming",
            ),
        ),
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        guards=_HEAVY_LAUNCH,
        keywords=("weights", "hf", "egress", "still", "wan", "ltx"),
    ),
    _verb(
        "models.download_podcast",
        "Download the podcast pack",
        Group.MODELS,
        "Opt-in Kokoro, ACE-Step, and the optional TTS tiers under the cap. A "
        "missing pack is not a doctor failure.",
        "download-podcast",
        params=(
            _choice(
                "tier",
                "Tier",
                "--tier",
                "analog",
                "acestep",
                "chatterbox",
                "qwen3tts",
                "all",
                required=False,
                default="analog",
            ),
            _text(
                "limit",
                "Bandwidth cap",
                "--limit",
                required=False,
                default="auto",
                help_text="auto, off, or a fixed Mbps number",
            ),
        ),
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        keywords=("tts", "kokoro", "voice"),
    ),
    _verb(
        "models.download_dub",
        "Download the dub pack",
        Group.MODELS,
        "Opt-in Silero VAD, faster-whisper, and Chatterbox Multilingual V3; "
        "pip-installs into the stack while it is up.",
        "download-dub",
        params=(
            _choice(
                "tier",
                "Tier",
                "--tier",
                "asr",
                "clone",
                "all",
                required=False,
                default="asr",
            ),
            _text(
                "limit",
                "Bandwidth cap",
                "--limit",
                required=False,
                default="auto",
                help_text="auto, off, or a fixed Mbps number",
            ),
        ),
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        keywords=("asr", "whisper", "voice clone"),
    ),
    _verb(
        "models.download_music",
        "Download the music pack",
        Group.MODELS,
        "Opt-in ACE-Step 1.5 music AIO under the cap. Not part of the core pull.",
        "download-music",
        params=(
            _choice(
                "tier",
                "Tier",
                "--tier",
                "turbo",
                "xl",
                "all",
                required=False,
                default="turbo",
            ),
            _text(
                "limit",
                "Bandwidth cap",
                "--limit",
                required=False,
                default="auto",
                help_text="auto, off, or a fixed Mbps number",
            ),
        ),
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        keywords=("ace-step", "music"),
    ),
    _verb(
        "models.download_llm",
        "Download the LLM packs",
        Group.MODELS,
        "The enhance GGUF, or the opt-in ~23 GB 35B expert the occupancy "
        "llm-desk needs.",
        "download-llm",
        params=(
            _choice(
                "tier",
                "Tier",
                "--tier",
                "enhance",
                "qwen36-35b-a3b",
                "all",
                required=False,
                default="enhance",
            ),
            _text(
                "limit",
                "Bandwidth cap",
                "--limit",
                required=False,
                default="auto",
                help_text="auto, off, or a fixed Mbps number",
            ),
        ),
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        keywords=("gguf", "llama", "35b"),
    ),
    _verb(
        "models.download_restore",
        "Download the restore pack",
        Group.MODELS,
        "Opt-in SeedVR2-3B Apache restore pack used after concat.",
        "download-restore",
        params=(_choice("tier", "Tier", "--tier", "seedvr2-3b", required=False),),
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        keywords=("seedvr", "upscale", "restore"),
    ),
    _verb(
        "models.download_3d",
        "Download the 3D packs",
        Group.MODELS,
        "Opt-in Comfy-Org TRELLIS.2 INT8 and DA3-BASE.",
        "download-3d",
        params=(
            _choice(
                "tier",
                "Tier",
                "--tier",
                "trellis2",
                "da3-base",
                "all",
                required=False,
                default="trellis2",
            ),
        ),
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        keywords=("trellis", "3d", "mesh"),
    ),
    _verb(
        "models.download_longcat",
        "Download the LongCat pack",
        Group.MODELS,
        "Opt-in LongCat-Video MIT; no NCCL, the context-parallel flag only.",
        "download-longcat",
        params=(
            _choice(
                "tier",
                "Tier",
                "--tier",
                "video",
                "avatar",
                "all",
                required=False,
                default="video",
            ),
        ),
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        keywords=("longcat", "video"),
    ),
    _verb(
        "models.download_dreamx",
        "Download the DreamX pack",
        Group.MODELS,
        "Opt-in DreamX-Creator 1.0 Apache joint AV. Not DreamX-World.",
        "download-dreamx",
        params=(_choice("tier", "Tier", "--tier", "creator", required=False),),
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        keywords=("dreamx", "joint av"),
    ),
    _refused(
        "models.refuse_download_h3",
        "Download MiniMax H3",
        Group.MODELS,
        "Refused: the H3 weights are not in the US-safe catalog.",
        "download-h3",
        keywords=("minimax", "h3", "refused"),
    ),
    _verb(
        "models.download_limit_status",
        "Show the bandwidth cap",
        Group.MODELS,
        "Report the shaping interface, the active cap, and the cached measurement.",
        "download-limit",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("tc", "wondershaper", "throttle", "mbps"),
    ),
    _verb(
        "models.download_limit_run",
        "Apply the bandwidth cap",
        Group.MODELS,
        "Install kernel traffic shaping with sudo tc, in auto mode from 85 per "
        "cent of the measured link.",
        "download-limit",
        ("run",),
        params=(
            _text(
                "limit",
                "Bandwidth cap",
                "--limit",
                required=False,
                default="auto",
                help_text="auto, off, or a fixed Mbps number",
            ),
            _flag("refresh", "Re-measure", "--refresh"),
            _flag("fallback", "Soft-fail", "--fallback"),
        ),
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        keywords=("tc", "wondershaper", "sudo", "throttle"),
    ),
    _verb(
        "models.download_limit_clear",
        "Clear the bandwidth cap",
        Group.MODELS,
        "Remove the qdisc so the link runs uncapped again.",
        "download-limit",
        ("clear",),
        tier=RiskTier.WRITE,
        keywords=("tc", "unthrottle", "release"),
    ),
    _verb(
        "models.clear_hf_locks",
        "Clear stale HF locks",
        Group.MODELS,
        "Remove leftover Hugging Face .lock files under MODELS_DIR.",
        "clear-hf-locks",
        tier=RiskTier.WRITE,
        guards=_APPLY_SAFE,
        keywords=("lock", "stuck", "hf"),
    ),
    _verb(
        "models.reset_hf_partials",
        "Delete partial downloads",
        Group.MODELS,
        "Delete every *.incomplete under MODELS_DIR. Finished weights are kept.",
        "reset-hf-partials",
        params=(_yes(), _flag("force", "Force", "--force")),
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        guards=_APPLY_SAFE,
        keywords=("partial", "incomplete", "resume"),
    ),
    _utility(
        "models.podcast_status",
        "Check the podcast pack",
        Group.MODELS,
        "Ask the podcast utility which tiers are present on disk.",
        "download-podcast",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("pack", "ready", "disk"),
    ),
    _utility(
        "models.dub_status",
        "Check the dub pack",
        Group.MODELS,
        "Ask the dub utility which tiers are present on disk.",
        "download-dub",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("pack", "ready", "disk"),
    ),
    _utility(
        "models.music_status",
        "Check the music pack",
        Group.MODELS,
        "Ask the music utility which tiers are present on disk.",
        "download-music",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("pack", "ready", "disk"),
    ),
    _utility(
        "models.llm_status",
        "Check the LLM packs",
        Group.MODELS,
        "Ask the LLM utility which GGUF tiers are present on disk.",
        "download-llm",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("pack", "ready", "gguf"),
    ),
    _utility(
        "models.restore_status",
        "Check the restore pack",
        Group.MODELS,
        "Ask the restore utility whether SeedVR2-3B is present.",
        "download-restore",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("pack", "ready", "seedvr"),
    ),
    _utility(
        "models.three_d_status",
        "Check the 3D packs",
        Group.MODELS,
        "Ask the 3D utility which packs are present on disk.",
        "download-3d",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("pack", "ready", "trellis"),
    ),
    _utility(
        "models.longcat_status",
        "Check the LongCat pack",
        Group.MODELS,
        "Ask the LongCat utility which tiers are present on disk.",
        "download-longcat",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("pack", "ready", "longcat"),
    ),
    _utility(
        "models.dreamx_status",
        "Check the DreamX pack",
        Group.MODELS,
        "Ask the DreamX utility whether the creator pack is present.",
        "download-dreamx",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("pack", "ready", "dreamx"),
    ),
    # ------------------------------------------------------------------
    # Sidecars: host LLM, agent, Blender, and the in-tree MCP servers.
    # ------------------------------------------------------------------
    _verb(
        "sidecars.llm_sidecar_status",
        "Check the LLM sidecar",
        Group.SIDECARS,
        "Report whether the host llama-server is up on the loopback port.",
        "llm-sidecar",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("llama", "sidecar"),
    ),
    _verb(
        "sidecars.llm_sidecar_start",
        "Start the LLM sidecar",
        Group.SIDECARS,
        "Run the host llama-server that the occupancy llm-desk uses. Never in "
        "the container image.",
        "llm-sidecar",
        ("start",),
        tier=RiskTier.WRITE,
        guards=(Guard.OCCUPANCY_PARKED,),
        keywords=("llama", "serve"),
    ),
    _verb(
        "sidecars.llm_sidecar_stop",
        "Stop the LLM sidecar",
        Group.SIDECARS,
        "Take the host llama-server down and release the memory it holds.",
        "llm-sidecar",
        ("stop",),
        tier=RiskTier.WRITE,
        keywords=("llama", "shutdown"),
    ),
    _verb(
        "sidecars.agent_model_status",
        "Check the agent sidecar",
        Group.SIDECARS,
        "Report whether the host agent model is up and whether its weights are "
        "on disk.",
        "agent-model",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("agent", "qwen"),
    ),
    _verb(
        "sidecars.agent_model_run",
        "Run the agent sidecar",
        Group.SIDECARS,
        "Start the host agent model on its loopback port; the first run pulls "
        "about 160 GB and wants the GPU.",
        "agent-model",
        ("run",),
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        guards=_GPU_WORK,
        keywords=("agent", "qwen", "serve"),
    ),
    _verb(
        "sidecars.agent_model_stop",
        "Stop the agent sidecar",
        Group.SIDECARS,
        "Take the host agent model down and release what it holds.",
        "agent-model",
        ("stop",),
        tier=RiskTier.WRITE,
        keywords=("agent", "shutdown"),
    ),
    _verb(
        "sidecars.blender_mcp_tools",
        "List the Blender MCP tools",
        Group.SIDECARS,
        "Ask the in-tree Blender MCP server which typed tools it offers. bpy "
        "work needs the occupancy blender-desk.",
        "blender-mcp",
        ("--list-tools",),
        guards=(Guard.OCCUPANCY_PARKED,),
        keywords=("mcp", "bpy", "tools"),
    ),
    _verb(
        "sidecars.research_mcp_tools",
        "List the research MCP tools",
        Group.SIDECARS,
        "Ask the in-tree research MCP server which typed tools it offers. Runs "
        "on a CPU GGUF.",
        "research-mcp",
        ("--list-tools",),
        keywords=("mcp", "chat", "search"),
    ),
    _verb(
        "sidecars.studio_mcp_tools",
        "List the studio MCP tools",
        Group.SIDECARS,
        "Ask the in-tree studio MCP server which typed tools it offers. It "
        "clones graphs and never queues them.",
        "studio-mcp",
        ("--list-tools",),
        keywords=("mcp", "graph", "clone"),
    ),
    _verb(
        "sidecars.studio_mcp_clone",
        "Clone a lab graph into _user",
        Group.SIDECARS,
        "Ask the studio MCP server to copy one promoted lab graph into the live "
        "_user folder. The sanctioned route; the console never copies it itself.",
        "studio-mcp",
        ("--call", "clone_graph"),
        params=(_pos("payload", "Call payload", help_text="JSON object for the tool"),),
        tier=RiskTier.WRITE,
        guards=(Guard.PACKS_READY,),
        keywords=("mcp", "clone", "_user", "lab"),
    ),
    _verb(
        "sidecars.edit_mcp_status",
        "Check the editing MCP",
        Group.SIDECARS,
        "Report whether the in-tree editing MCP server reaches the /ez_edit routes.",
        "edit-mcp",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("mcp", "timeline"),
    ),
    _verb(
        "sidecars.edit_mcp_tools",
        "List the editing MCP tools",
        Group.SIDECARS,
        "Ask the in-tree editing MCP server which typed timeline tools it offers.",
        "edit-mcp",
        ("--list-tools",),
        keywords=("mcp", "timeline", "tools"),
    ),
    _verb(
        "sidecars.blender_llm",
        "Ask the Blender CPU client",
        Group.SIDECARS,
        "One-shot prompt through the optional host Qwen3-4B CPU client. Path D "
        "when llama.cpp is missing.",
        "blender-llm",
        params=(_pos("prompt", "Prompt", help_text="one-line scene description"),),
        tier=RiskTier.WRITE,
        keywords=("gguf", "prompt", "path d"),
    ),
    _verb(
        "sidecars.blender",
        "Run the host Blender sidecar",
        Group.SIDECARS,
        "Start host Blender for a Workbench dump. It dies while Comfy is heavy.",
        "blender",
        tier=RiskTier.WRITE,
        guards=(Guard.OCCUPANCY_PARKED, Guard.QUEUE_IDLE),
        keywords=("bpy", "workbench"),
    ),
    _verb(
        "sidecars.blender_install",
        "Install host Blender",
        Group.SIDECARS,
        "apt install Ubuntu Blender on the host. Never added to the image.",
        "blender-install",
        tier=RiskTier.HEAVY,
        confirm=ConfirmKind.YES,
        keywords=("apt", "sudo", "install"),
    ),
    _verb(
        "sidecars.export_guides",
        "Dump a guide pack",
        Group.SIDECARS,
        "Write a 120-frame clay, depth, and canny guide pack. Refuses while "
        "compose is up.",
        "export-guides",
        params=(
            _choice(
                "print_mode",
                "Guide family",
                "--print",
                "ltx-iclora-depth",
                "ltx-iclora-canny",
                "wan-flf",
                required=False,
            ),
        ),
        tier=RiskTier.WRITE,
        guards=_STOP_FIRST,
        keywords=("guides", "depth", "canny", "blender"),
    ),
    _verb(
        "sidecars.blender_stills",
        "Dump a Blender still pack",
        Group.SIDECARS,
        "Write single-frame clay, depth, and canny stills. Refuses while compose "
        "is up.",
        "blender-stills",
        params=(
            _text("film", "Film slug", "--film"),
            _text("plate", "Plate", "--plate"),
            _text("blend", "Blend file", "--blend", required=False),
            _choice(
                "size",
                "Frame size",
                "--size",
                "1280x704",
                "768x1280",
                "1024x1280",
                "1024x1024",
                "1280x720",
                required=False,
            ),
            _flag(
                "install_inputs",
                "Install into the input dir",
                "--install-inputs",
                help_text="copies first.png into the ComfyUI input dir",
            ),
        ),
        tier=RiskTier.WRITE,
        guards=_STOP_FIRST,
        keywords=("stills", "clay", "depth", "canny"),
    ),
    _verb(
        "sidecars.house_views",
        "Dump the house views",
        Group.SIDECARS,
        "Write 1024x1280 four-by-five clay stills plus the GLB for one set.",
        "house-views",
        params=(
            _text("slug", "Set slug", "--slug"),
            _text("layout", "Layout file", "--layout", required=False),
            _flag("install_inputs", "Install into the input dir", "--install-inputs"),
            _flag("seed_inputs", "Seed the input dir", "--seed-inputs"),
        ),
        tier=RiskTier.WRITE,
        guards=_STOP_FIRST,
        keywords=("house", "glb", "stills"),
    ),
    _utility(
        "sidecars.spark_farm_sync_models",
        "Sync models to the extra Sparks",
        Group.SIDECARS,
        "rsync the comfy model tree to each worker over the fabric IPs only.",
        "spark-farm",
        ("sync-models",),
        tier=RiskTier.WRITE,
        keywords=("farm", "rsync", "fabric"),
    ),
    _utility(
        "sidecars.spark_farm_run",
        "Run a film on the extra Sparks",
        Group.SIDECARS,
        "Queue the film graphs across the workers, then concat locally. Never "
        "starts compose on a remote node.",
        "spark-farm",
        ("run",),
        params=(
            ParamSpec(
                name="film",
                label="Film slug",
                kind=ParamKind.CHOICE,
                flag="--film",
                choices=_FILM_CHOICES,
                required=False,
                default="go-see",
                help_text="the shipped film the workers split up",
            ),
            _text(
                "seeds",
                "Seed list",
                "--seeds",
                required=False,
                help_text="comma-separated seed numbers",
            ),
        ),
        tier=RiskTier.WRITE,
        guards=_GPU_WORK,
        keywords=("farm", "queue", "seeds"),
    ),
    _utility(
        "sidecars.spark_farm_dispatch",
        "Split shots across the extra Sparks",
        Group.SIDECARS,
        "Assign shot ranges to the workers so each runs its own local print-shot.",
        "spark-farm",
        ("dispatch",),
        params=(_text("film", "Film slug", "--film", required=False),),
        tier=RiskTier.WRITE,
        guards=_GPU_WORK,
        keywords=("farm", "dispatch", "shots"),
    ),
    # ------------------------------------------------------------------
    # Occupancy: the XOR desk that hands the single GPU to one workload.
    # ------------------------------------------------------------------
    _verb(
        "occupancy.status",
        "Show the occupancy desk",
        Group.OCCUPANCY,
        "Read the desk mode, whether Comfy is parked, and what is holding the GPU.",
        "occupancy",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("desk", "parked", "xor"),
    ),
    _verb(
        "occupancy.enter_blender_desk",
        "Enter blender-desk",
        Group.OCCUPANCY,
        "Park Comfy with POST /free so host Workbench dumps can take the GPU.",
        "occupancy",
        ("enter", "blender-desk"),
        params=(_yes(),),
        tier=RiskTier.WRITE,
        guards=(Guard.STACK_RUNNING,),
        keywords=("desk", "park", "blender"),
    ),
    _verb(
        "occupancy.enter_llm_desk",
        "Enter llm-desk",
        Group.OCCUPANCY,
        "Park Comfy and bring up the host 35B sidecar on the loopback port.",
        "occupancy",
        ("enter", "llm-desk"),
        params=(_yes(),),
        tier=RiskTier.WRITE,
        guards=(Guard.STACK_RUNNING,),
        keywords=("desk", "park", "llm"),
    ),
    _verb(
        "occupancy.enter_klein",
        "Enter klein",
        Group.OCCUPANCY,
        "Claim the GPU for the stills family.",
        "occupancy",
        ("enter", "klein"),
        params=(_yes(),),
        tier=RiskTier.WRITE,
        guards=_QUEUE_ON_COMFY,
        keywords=("desk", "stills", "klein"),
    ),
    _verb(
        "occupancy.enter_trellis",
        "Enter trellis",
        Group.OCCUPANCY,
        "Claim the GPU for the 3D family.",
        "occupancy",
        ("enter", "trellis"),
        params=(_yes(),),
        tier=RiskTier.WRITE,
        guards=_QUEUE_ON_COMFY,
        keywords=("desk", "3d", "trellis"),
    ),
    _verb(
        "occupancy.enter_wan",
        "Enter wan",
        Group.OCCUPANCY,
        "Claim the GPU for the silent-motion family.",
        "occupancy",
        ("enter", "wan"),
        params=(_yes(),),
        tier=RiskTier.WRITE,
        guards=_QUEUE_ON_COMFY,
        keywords=("desk", "motion", "wan"),
    ),
    _verb(
        "occupancy.enter_ltx",
        "Enter ltx",
        Group.OCCUPANCY,
        "Claim the GPU for the distilled audio-video family.",
        "occupancy",
        ("enter", "ltx"),
        params=(_yes(),),
        tier=RiskTier.WRITE,
        guards=_QUEUE_ON_COMFY,
        keywords=("desk", "av", "ltx"),
    ),
    _verb(
        "occupancy.enter_idle",
        "Return the desk to idle",
        Group.OCCUPANCY,
        "Release the claim so the stack can take the GPU again.",
        "occupancy",
        ("enter", "idle"),
        params=(_yes(),),
        tier=RiskTier.WRITE,
        guards=(Guard.STACK_RUNNING,),
        keywords=("desk", "release", "idle"),
    ),
    # ------------------------------------------------------------------
    # Film: shot printing plus the cut and finishing tools.
    # ------------------------------------------------------------------
    _verb(
        "film.print_shot",
        "Queue one compiled shot",
        Group.FILM,
        "Queue one compiled shot into films/<slug>/shots/ through ComfyUI.",
        "print-shot",
        params=(
            _pos("film", "Film slug", help_text="the films/ directory name"),
            _pos("shot_id", "Shot id", help_text="01 through 18"),
            _text(
                "quality",
                "Quality tier",
                "--quality",
                required=False,
                help_text="draft, standard, high, ultra, or max",
            ),
        ),
        tier=RiskTier.WRITE,
        guards=_QUEUE_ON_COMFY,
        keywords=("queue", "shot", "render"),
    ),
    _verb(
        "film.film_resume",
        "Reprint the failed shots",
        Group.FILM,
        "Requeue only the failed or crashed shots of a film, skipping the ones "
        "already at five seconds.",
        "film-resume",
        params=(
            _pos("film", "Film slug"),
            _text(
                "quality",
                "Quality tier",
                "--quality",
                required=False,
                help_text="draft, standard, high, ultra, or max",
            ),
        ),
        tier=RiskTier.WRITE,
        guards=_QUEUE_ON_COMFY,
        keywords=("retry", "resume", "shots"),
    ),
    _verb(
        "film.take_promote",
        "Promote one take",
        Group.FILM,
        "Copy takes/<id>/tNNN.mp4 over shots/<id>.mp4 and mark the shot ok.",
        "take-promote",
        params=(
            _pos("film", "Film slug"),
            _pos("shot_id", "Shot id"),
            _pos("take", "Take number", help_text="NNN"),
        ),
        tier=RiskTier.WRITE,
        keywords=("take", "approve", "copy"),
    ),
    _verb(
        "film.film_accept",
        "Run the accept gate",
        Group.FILM,
        "Fail-closed check that every shot is 5.00 s at 1280x704 with LTX audio.",
        "film-accept",
        params=(
            _pos(
                "film",
                "Film slug",
                help_text="go-see, still-here, or switchyard",
            ),
        ),
        tier=RiskTier.READ,
        keywords=("gate", "verify", "qc"),
    ),
    _verb(
        "film.film_export_otio",
        "Export the OTIO timeline",
        Group.FILM,
        "Write films/<slug>/publish/<slug>.otio from the jobstore.",
        "film-export-otio",
        params=(_pos("film", "Film slug"),),
        tier=RiskTier.WRITE,
        keywords=("otio", "timeline", "publish"),
    ),
    _verb(
        "film.film_proxies",
        "Build NVENC proxies",
        Group.FILM,
        "Render 960x528 h264 proxies. Refuses while compose is up and never "
        "rewrites a master.",
        "film-proxies",
        params=(_pos("film", "Film slug"), _yes()),
        tier=RiskTier.WRITE,
        guards=_STOP_FIRST,
        keywords=("proxy", "h264", "preview"),
    ),
    _verb(
        "film.shot_sheet_status",
        "Show the shot sheet",
        Group.FILM,
        "Report the shot-card defaults recorded for a film.",
        "shot-sheet",
        ("status",),
        params=(
            _text("film", "Film slug", "--film", required=False),
            _flag("as_json", "JSON", "--json", help_text=_JSON_HELP),
        ),
        keywords=("yaml", "shot card"),
    ),
    _verb(
        "film.shot_sheet_run",
        "Write the shot sheet",
        Group.FILM,
        "Write films/<slug>/shots.yaml. Needs no docker.",
        "shot-sheet",
        ("run",),
        params=(
            _text("film", "Film slug", "--film"),
            _text("source", "Source sheet", "--from", required=False),
            _text("out", "Output path", "--out", required=False),
            _flag("lab_example", "Start from the lab example", "--lab-example"),
        ),
        tier=RiskTier.WRITE,
        keywords=("yaml", "shot card", "generate"),
    ),
    _verb(
        "film.overlay_qc",
        "Overlay a look for QC",
        Group.FILM,
        "Composite a fifty per cent clay-and-look comparison with host ffmpeg.",
        "overlay-qc",
        params=(
            _text("film", "Film slug", "--film"),
            _text("shot_id", "Shot id", "--shot"),
            _text("look", "Look clip", "--look"),
            _text("guides", "Guides dir", "--guides", required=False),
        ),
        tier=RiskTier.WRITE,
        keywords=("overlay", "ffmpeg", "qc"),
    ),
    _verb(
        "film.film_animatic",
        "Cut a cheap animatic",
        Group.FILM,
        "Build a ninety second animatic from clay.mp4 or the stills.",
        "film-animatic",
        params=(
            _text("film", "Film slug", "--film"),
            _text("yaml", "Shot sheet", "--yaml", required=False),
            _text("guides", "Guides dir", "--guides", required=False),
        ),
        tier=RiskTier.WRITE,
        keywords=("animatic", "preview", "ffmpeg"),
    ),
    _verb(
        "film.stem_mix",
        "Mix the picture-lock stems",
        Group.FILM,
        "Duck the background bed fifteen dB and loudnorm to the YouTube target.",
        "stem-mix",
        params=(
            _text("film", "Film slug", "--film"),
            _text("shot_id", "Shot id", "--shot"),
            _text("background", "Background bed", "--bg"),
            _text("dialogue", "Dialogue stem", "--dx", required=False),
            _text("effects", "Effects stem", "--fx", required=False),
            _text("mix", "Mix stem", "--mx", required=False),
            _text("video", "Video master", "--video", required=False),
        ),
        tier=RiskTier.WRITE,
        keywords=("audio", "loudnorm", "duck"),
    ),
    _verb(
        "film.audio_still_status",
        "Check the still-mux tool",
        Group.FILM,
        "Report whether the host ffmpeg muxer is ready.",
        "audio-still-video",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("mux", "ffmpeg", "readiness"),
    ),
    _verb(
        "film.audio_still_run",
        "Mux a still to a YouTube MP4",
        Group.FILM,
        "Mux one still and one audio master into a YouTube MP4 with host ffmpeg.",
        "audio-still-video",
        ("run",),
        params=(
            _text("audio", "Audio master", "--audio"),
            _text("image", "Still image", "--image"),
            _text("out", "Output file", "--out", required=False),
        ),
        tier=RiskTier.WRITE,
        keywords=("mux", "ffmpeg", "youtube"),
    ),
    _verb(
        "film.asset_ls",
        "List the Asset Bible",
        Group.FILM,
        "Read the catalog under COMFY_OUTPUT_DIR/assets. Never writes.",
        "asset-ls",
        params=(
            _flag("as_json", "JSON", "--json", help_text=_JSON_HELP),
            _text("output_dir", "Output dir", "--output-dir", required=False),
        ),
        keywords=("assets", "catalog", "bible"),
    ),
    _utility(
        "film.compile_film",
        "Compile the film",
        Group.FILM,
        "Compile the shot list of a film into the graph jobs the printer queues.",
        "compile-film",
        params=(_pos("film", "Film slug"),),
        tier=RiskTier.WRITE,
        keywords=("compile", "shots"),
    ),
    _utility(
        "film.concat_shots",
        "Concat the shots",
        Group.FILM,
        "Join the promoted shots into one master. Dry run unless you tick --yes.",
        "concat-shots",
        params=(
            _text("film", "Film slug", "--film", required=False),
            _text("shots_dir", "Shots dir", "--dir", required=False),
            _text(
                "files",
                "Explicit file list",
                "--files",
                required=False,
                help_text="comma-separated paths, used instead of a dir",
            ),
            _text("out", "Output file", "--out", required=False),
            _flag("dry_run", "Dry run", "--dry-run", help_text=_DRY_RUN_HELP),
            _yes(),
        ),
        tier=RiskTier.WRITE,
        keywords=("concat", "cut", "master"),
    ),
    _utility(
        "film.compress_cinema_clip",
        "Compress a cinema clip",
        Group.FILM,
        "Re-encode one clip under a byte budget, optionally writing a poster.",
        "compress-cinema-clip",
        params=(
            _text("source", "Input file", "--in"),
            _text("out", "Output file", "--out"),
            _text("poster", "Poster file", "--poster", required=False),
            _int("crf", "CRF", "--crf", 0, 51, required=False, default="28"),
            _int(
                "max_bytes",
                "Byte budget",
                "--max-bytes",
                1_024,
                1_073_741_824,
                required=False,
                default="524288",
            ),
            _flag("dry_run", "Dry run", "--dry-run", help_text=_DRY_RUN_HELP),
        ),
        tier=RiskTier.WRITE,
        keywords=("encode", "crf", "poster"),
    ),
    _utility(
        "film.nvenc_preview",
        "Build an NVENC preview",
        Group.FILM,
        "Fast hardware preview of one master. Refuses while compose is up and "
        "deletes nothing.",
        "nvenc-preview",
        params=(
            _text("source", "Master file", "--in"),
            _text("out", "Preview file", "--out"),
            _yes(),
        ),
        tier=RiskTier.WRITE,
        guards=_STOP_FIRST,
        keywords=("nvenc", "preview", "encode"),
    ),
    _utility(
        "film.pack_frames",
        "Pack frames into a clip",
        Group.FILM,
        "Turn a numbered frame directory into one video file.",
        "pack-frames",
        params=(
            _text("source", "Frames dir", "--in"),
            _text("out", "Output file", "--out"),
            _int(
                "fps",
                "Frames per second",
                "--fps",
                1,
                240,
                required=False,
                default="24",
            ),
            _text(
                "pattern",
                "Frame pattern",
                "--pattern",
                required=False,
                default="%04d.png",
            ),
        ),
        tier=RiskTier.WRITE,
        keywords=("frames", "encode", "sequence"),
    ),
    _utility(
        "film.dub_fetch_status",
        "Check the dub fetcher",
        Group.FILM,
        "Report what the dub fetcher has already pulled.",
        "dub-fetch",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("dub", "fetch", "source audio"),
    ),
    _utility(
        "film.dub_fetch_run",
        "Fetch dub source audio",
        Group.FILM,
        "Pull one licensed source recording into the dub working dir.",
        "dub-fetch",
        ("run",),
        params=(
            _text("url", "Source URL", "--url"),
            _text("out", "Output dir", "--out", required=False),
        ),
        tier=RiskTier.WRITE,
        keywords=("dub", "download", "source audio"),
    ),
    _utility(
        "film.podcast_loudnorm_status",
        "Check the loudnorm tool",
        Group.FILM,
        "Report whether the loudness pass is available on this host.",
        "podcast-loudnorm",
        ("status",),
        params=(_flag("as_json", "JSON", "--json", help_text=_JSON_HELP),),
        keywords=("loudnorm", "loudness", "readiness"),
    ),
    _utility(
        "film.podcast_loudnorm_run",
        "Loudness-normalise an episode",
        Group.FILM,
        "Run the two-pass loudnorm on one audio file for the podcast or the "
        "channel target.",
        "podcast-loudnorm",
        ("run",),
        params=(
            _text("source", "Input file", "--in"),
            _text("out", "Output file", "--out", required=False),
            _choice(
                "target",
                "Loudness target",
                "--target",
                "podcast",
                "youtube",
                required=False,
                default="podcast",
            ),
        ),
        tier=RiskTier.WRITE,
        keywords=("loudnorm", "loudness", "episode"),
    ),
    _refused(
        "film.refuse_queue_h3",
        "Queue a MiniMax H3 job",
        Group.FILM,
        "Refused: no H3 graph can be queued from this studio.",
        "queue-h3",
        keywords=("minimax", "h3", "refused"),
    ),
    _refused(
        "film.refuse_farm_h3",
        "Run an H3 farm job",
        Group.FILM,
        "Refused: the farm never runs H3; there is no cluster product here.",
        "farm-h3",
        keywords=("minimax", "h3", "farm", "refused"),
    ),
    _refused(
        "film.refuse_stitch_h3",
        "Stitch an H3 cut",
        Group.FILM,
        "Refused: H3 stitch is outside the catalog.",
        "stitch-h3",
        keywords=("minimax", "h3", "stitch", "refused"),
    ),
    # ------------------------------------------------------------------
    # Disk: the model cache and stack state.
    # ------------------------------------------------------------------
    _verb(
        "disk.models_status",
        "Show the disk bible",
        Group.DISK,
        "Report the keep-set and the refuse list. Deletes nothing.",
        "models-status",
        keywords=("keep set", "refuse list", "cache"),
    ),
    _verb(
        "disk.reap_plan",
        "Plan a model cache cleanup",
        Group.DISK,
        "List what the model cache reclaim would remove. Reads only.",
        "reap-models",
        ("--plan",),
        guards=_PLAN_ONLY,
        keywords=("reclaim", "plan", "cache"),
    ),
    _verb(
        "disk.reap_apply",
        "Apply a model cache cleanup",
        Group.DISK,
        "Delete or quarantine the named cache class. Finished weights the "
        "keep-set claims are never touched.",
        "reap-models",
        ("--apply",),
        params=(
            _choice(
                "weight_class",
                "Cache class",
                "--class",
                "junk",
                "superseded",
                "banned",
            ),
            _flag(
                "quarantine",
                "Quarantine instead",
                "--quarantine",
                help_text="move aside rather than delete",
            ),
            _yes(),
        ),
        tier=RiskTier.DESTRUCTIVE,
        confirm=ConfirmKind.DELETE,
        guards=_APPLY_SAFE,
        keywords=("reclaim", "delete", "cache"),
    ),
    _verb(
        "disk.wizard_plan",
        "Plan a host reclaim",
        Group.DISK,
        "Guided host reclaim report: docker disk use, big caches, and what is "
        "safe to clear. Reads only.",
        "disk-wizard",
        ("--plan",),
        guards=_PLAN_ONLY,
        keywords=("reclaim", "plan", "docker df"),
    ),
    _verb(
        "disk.wizard_json",
        "Report the host reclaim as JSON",
        Group.DISK,
        "The same plan report as JSON, for the console to tabulate.",
        "disk-wizard",
        ("--json",),
        guards=_PLAN_ONLY,
        keywords=("reclaim", "plan", "json"),
    ),
    _verb(
        "disk.wizard_apply",
        "Apply a host reclaim",
        Group.DISK,
        "Carry out the steps you approved. Never removes the comfy-state volume "
        "and never prunes every image and volume.",
        "disk-wizard",
        ("--apply",),
        params=(_yes(),),
        tier=RiskTier.DESTRUCTIVE,
        confirm=ConfirmKind.DELETE,
        guards=_APPLY_SAFE,
        keywords=("reclaim", "delete", "prune"),
    ),
    _verb(
        "disk.cleanup",
        "Delete the comfy-state volume",
        Group.DISK,
        "Remove the Comfy install state volume only. COMFY_OUTPUT_DIR is kept.",
        "cleanup",
        tier=RiskTier.DESTRUCTIVE,
        confirm=ConfirmKind.DELETE,
        keywords=("volume", "reset", "wipe"),
    ),
)
"""Every action the console offers, in the order the sections draw.

One entry per dispatcher verb, one per subcommand worth offering on its own,
and one per utility that has no verb. The order is display order, so the list
stays grouped by section and a section reads top to bottom.
"""


def all_actions() -> tuple[ActionSpec, ...]:
    """Every action the console may offer, in catalog order.

    Returns:
        The immutable catalog tuple.
    """
    return _ACTIONS


def action_by_id(action_id: str) -> ActionSpec | None:
    """Find one catalog entry by its stable id.

    Args:
        action_id: The dotted id to look up.

    Returns:
        The matching entry, or ``None`` when the console asked for something it
        does not own.
    """
    for action in _ACTIONS:
        if action.action_id == action_id:
            return action
    return None


def group_actions(group: Group) -> tuple[ActionSpec, ...]:
    """Every action that belongs to one left-rail section.

    Args:
        group: The section to filter on.

    Returns:
        Matching entries, in catalog order.
    """
    return tuple(action for action in _ACTIONS if action.group is group)


def search(query: str) -> tuple[ActionSpec, ...]:
    """Match a palette query against every catalog entry.

    Every whitespace-separated term must appear in the entry's id, title,
    summary, target, group, or keywords, so a two-word query narrows instead of
    widening. Comparison is case-insensitive and an empty query matches
    everything, which is what the palette shows before the operator types.

    Args:
        query: What the operator typed.

    Returns:
        Matching entries, in catalog order.
    """
    terms = tuple(term.casefold() for term in query.split() if term)
    if not terms:
        return _ACTIONS
    matches: list[ActionSpec] = []
    for action in _ACTIONS:
        haystack = " ".join(
            (
                action.action_id,
                action.title,
                action.summary,
                action.target,
                action.group.value,
                " ".join(action.keywords),
            )
        ).casefold()
        if all(term in haystack for term in terms):
            matches.append(action)
    return tuple(matches)


def manage_verbs_in(manage_sh_text: str) -> tuple[str, ...]:
    """Read the verb labels out of the ``manage.sh`` dispatcher text.

    Only the ``case "${cmd}"`` block is examined, so the ``case`` blocks that
    belong to individual argument parsers do not leak in. Alternates that are
    flag spellings (``help | -h | --help``) collapse to their word label, and
    the ``*`` default is dropped.

    Args:
        manage_sh_text: Full text of ``scripts/manage.sh``, injected so the
            suite controls the input.

    Returns:
        The verb labels in dispatcher order, without duplicates.
    """
    lines = manage_sh_text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if _DISPATCHER_OPEN.match(line):
            start = index + 1
            break
    if start is None:
        return ()
    verbs: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if stripped == "esac":
            break
        if stripped.startswith("#"):
            continue
        match = _PATTERN_LINE.match(stripped)
        if match is None:
            continue
        labels = [label.strip() for label in match.group(1).split("|")]
        words = [
            label for label in labels if label and not label.startswith(("-", "*"))
        ]
        if words and words[0] not in verbs:
            verbs.append(words[0])
    return tuple(verbs)


def missing_verbs(manage_sh_text: str) -> tuple[str, ...]:
    """Report dispatcher verbs the catalog has no entry for.

    The completeness gate: green means every label the CLI will accept is also
    something the console offers.

    Args:
        manage_sh_text: Full text of ``scripts/manage.sh``, injected so the
            suite controls the input.

    Returns:
        Verbs with no catalog entry, in dispatcher order.
    """
    covered = {
        action.target
        for action in _ACTIONS
        if action.runner is RunnerKind.MANAGE
    }
    return tuple(
        verb for verb in manage_verbs_in(manage_sh_text) if verb not in covered
    )

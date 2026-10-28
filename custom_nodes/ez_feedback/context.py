"""Shared bug-report / feature-request vocabulary for every ez-comfy surface.

Hermetic: stdlib only, no ComfyUI, no torch, no network. The ComfyUI pack, the
studio-ui process, and ``js/ez_feedback_core.js`` build the same title, labels,
body, and issue URL from these constants so a report from any surface looks
alike. Redaction runs here, before anything leaves the process.

Mirrors ``docs-site/lib/docs-bug.ts``: one ``clip`` helper, one ``MAX_HREF``
budget, plain markdown, and progressive degradation instead of a truncated URL.
"""

from __future__ import annotations

import os
import platform
import re
from collections.abc import Callable, Mapping, Sequence
from urllib.parse import urlencode

REPO = "toxicoder/ez-comfy-stack"
"""Repository every surface files against."""

GITHUB_URL = "https://github.com"
"""GitHub web origin used for ``/issues/new`` handoffs."""

MAX_HREF = 5500
"""New-issue URL budget; longer URLs are degraded, never truncated."""

MAX_TITLE = 140
"""Issue title cap, matching the GitHub title field."""

MAX_BODY = 60000
"""API submit body cap."""

MAX_FIELD = 300
"""Cap for one interpolated value inside a body line."""

LABELS: dict[str, str] = {"bug": "bug", "enhancement": "enhancement"}
"""``kind`` -> the GitHub label that actually exists in the repo."""

ALLOWED_LABELS: tuple[str, ...] = ("bug", "documentation", "enhancement")
"""Only these labels are ever sent; GitHub silently drops unknown ones."""

DEFAULT_SUMMARY: dict[str, str] = {
    "bug": "Bug report from {area}",
    "enhancement": "Feature request from {area}",
}
"""Summary used when the caller gives none. ``{area}`` is the title area."""

FILL_IN = "<!-- Replace this line. -->"
"""Placeholder the reporter edits in the four narrative sections."""

FILL_HEADINGS: tuple[str, ...] = (
    "## What happened",
    "## Steps",
    "## Expected",
    "## Actual",
)
"""Narrative sections, always present for ``bug`` reports."""

CONTEXT_HEADING = "## Context"
"""Surface-specific facts the caller supplies."""

ENVIRONMENT_HEADING = "## Environment"
"""Image, ComfyUI pin, Python, GPU, and output directory facts."""

ERRORS_HEADING = "## Recent errors"
"""Ring buffer of the last failed executions."""

BROWSER_HEADING = "## Browser"
"""Viewport, DPR, language, online flag, user agent, page URL."""

HEADINGS: tuple[str, ...] = FILL_HEADINGS + (
    CONTEXT_HEADING,
    ENVIRONMENT_HEADING,
    ERRORS_HEADING,
    BROWSER_HEADING,
)
"""Body section order, exactly, with a blank line after each heading."""

DEGRADE_ORDER: tuple[str, ...] = (
    BROWSER_HEADING,
    ERRORS_HEADING,
    ENVIRONMENT_HEADING,
)
"""Sections dropped, in this order, when the href busts ``MAX_HREF``."""

TRACEBACK_LABEL = "Traceback:"
"""Label of the fenced traceback block, dropped after every section."""

GLOBAL_AREA = "global"
"""Surface that renders no ``[area]`` title prefix."""

APP_AREA = "app"
"""Surface whose area is ``app:<lab_rel>``."""

SURFACES: tuple[str, ...] = (
    GLOBAL_AREA,
    APP_AREA,
    "media-explorer",
    "media-file",
    "film-board",
    "watch",
    "model-check",
)
"""Every surface allowed to file a report.

Each one owns a prefilled button and passes its id as ``surface``; the area
prefix in the title comes from it. Adding a surface here is the one edit a new
reporting surface needs, and ``studio-ui/server.py`` pins against this list so
its stdlib builder cannot drift from it.
"""

BROWSER_FIELDS: tuple[tuple[str, str], ...] = (
    ("viewport", "Viewport"),
    ("dpr", "DPR"),
    ("lang", "Language"),
    ("online", "Online"),
    ("ua", "User agent"),
    ("pageUrl", "Page URL"),
)
"""``browser`` key -> body label, in render order."""

ENV_KEYS: tuple[tuple[str, str], ...] = (
    ("comfyui_ref", "COMFYUI_REF"),
    ("image", "EZ_COMFY_IMAGE"),
    ("output_dir", "COMFY_OUTPUT_DIR"),
    ("comfy_port", "COMFY_PORT"),
)
"""``env_snapshot`` key -> environment variable."""

ENV_DEFAULTS: dict[str, str] = {"comfy_port": "8188"}
"""Fallbacks for facts the container does not always export."""

_TOKEN_RE = re.compile(r"(?:ghp|gho|github_pat|hf)_[A-Za-z0-9][A-Za-z0-9_-]{3,}")
"""Shape of the secrets that must never reach a report."""


def clip(value: str, max_len: int) -> str:
    """Collapse whitespace and cap a field so the issue URL stays openable.

    Args:
        value: Raw text.
        max_len: Maximum length, including the trailing dots when trimmed.

    Returns:
        A single-line string.
    """
    text = " ".join(str(value if value is not None else "").split())
    if len(text) <= max_len:
        return text
    if max_len < 2:
        return ""
    return f"{text[: max_len - 3]}..."


def kind_key(kind: str) -> str:
    """Normalize a caller-supplied kind.

    Args:
        kind: Anything; only ``enhancement`` is distinct from ``bug``.

    Returns:
        ``"bug"`` or ``"enhancement"``.
    """
    text = str(kind or "").strip().lower()
    return text if text in LABELS else "bug"


def labels_for(kind: str) -> list[str]:
    """GitHub labels for a kind.

    Args:
        kind: ``bug`` or ``enhancement``.

    Returns:
        One label that exists in the repo.
    """
    return [LABELS[kind_key(kind)]]


def area_for(surface: str, app: str) -> str:
    """Title area for a surface.

    Args:
        surface: One of the shared surface ids.
        app: ``extra.lab_rel`` when the surface is the running App.

    Returns:
        ``app:<lab_rel>``, the bare surface id, or ``global``.
    """
    text = str(surface or "").strip() or GLOBAL_AREA
    if text == APP_AREA:
        rel = str(app or "").strip()
        return f"{APP_AREA}:{rel}" if rel else APP_AREA
    return text


def title_for(kind: str, surface: str, app: str, summary: str) -> str:
    """Issue title ``[<area>] <summary>``, clipped to :data:`MAX_TITLE`.

    ``global`` renders no prefix. A missing summary falls back to
    :data:`DEFAULT_SUMMARY`.

    Args:
        kind: ``bug`` or ``enhancement``.
        surface: One of the shared surface ids.
        app: ``extra.lab_rel`` for the app surface.
        summary: Caller headline; may be empty.

    Returns:
        Single-line title, at most 140 chars.
    """
    key = kind_key(kind)
    area = area_for(surface, app)
    text = " ".join(str(summary or "").split()) or DEFAULT_SUMMARY[key].format(area=area)
    title = text if area == GLOBAL_AREA else f"[{area}] {text}"
    return clip(title, MAX_TITLE)


def _safe_text(produce: Callable[[], object], fallback: str) -> str:
    """Call a fact getter that must never break a report.

    Args:
        produce: Zero-arg callable.
        fallback: Value used when the call or the stringifying raises.

    Returns:
        Single-line text or ``fallback``.
    """
    try:
        return " ".join(str(produce()).split())
    except Exception:  # noqa: BLE001 - platform introspection is best effort
        return fallback


def _home_dir() -> str:
    """Process home directory, or ``""`` when it cannot be resolved.

    Returns:
        Absolute home path, possibly empty.
    """
    try:
        return str(os.path.expanduser(os.environ.get("HOME") or "~"))
    except Exception:  # noqa: BLE001 - redaction must never raise
        return ""


def redact(text: str) -> str:
    """Scrub token-like runs and the home directory from anything leaving us.

    Args:
        text: Anything; stringified.

    Returns:
        Text with secrets replaced by ``[redacted]`` and the home directory by
        ``~``.
    """
    value = str(text)
    out = _TOKEN_RE.sub("[redacted]", value)
    home = _home_dir()
    if home and home != "/" and home in out:
        out = out.replace(home, "~")
    return out


def _value_text(value: object) -> str:
    """Stringify one report value for a markdown line.

    Args:
        value: Field value; booleans render ``yes`` / ``no``.

    Returns:
        Trimmed text, empty when there is nothing to show.
    """
    if isinstance(value, bool):
        return "yes" if value else "no"
    if value is None:
        return ""
    return " ".join(str(value).split())


def context_lines(pairs: Sequence[tuple[str, object]] | None) -> list[str]:
    """Render ``- label: value`` lines for a Context or Environment block.

    Pairs with no value are omitted, values are redacted and clipped, and a
    malformed entry is skipped rather than raised.

    Args:
        pairs: ``(label, value)`` pairs; may be ``None``.

    Returns:
        Markdown bullet lines, in the caller's order.
    """
    lines: list[str] = []
    for pair in pairs or ():
        try:
            label, value = pair
        except (TypeError, ValueError):
            continue
        text = _value_text(value)
        if not text:
            continue
        name = _value_text(label) or "value"
        lines.append(f"- {redact(name)}: {clip(redact(text), MAX_FIELD)}")
    return lines


def error_lines(errors: Sequence[Mapping[str, object]] | None, surface: str) -> list[str]:
    """Render the ``## Recent errors`` block from the client ring buffer.

    Each entry becomes ``- <iso8601> [<surface>] <message>``, with the entry's
    own surface preferred and ``detail`` appended in parentheses when present.

    Args:
        errors: Ring-buffer entries; may be ``None``.
        surface: Report surface used when an entry carries none.

    Returns:
        Markdown bullet lines, newest first as supplied.
    """
    lines: list[str] = []
    for entry in errors or ():
        if not isinstance(entry, Mapping):
            continue
        message = _value_text(entry.get("message"))
        if not message:
            continue
        stamp = _value_text(entry.get("ts")) or "unknown"
        where = _value_text(entry.get("surface")) or _value_text(surface) or GLOBAL_AREA
        line = f"- {redact(stamp)} [{redact(where)}] {clip(redact(message), MAX_FIELD)}"
        detail = _value_text(entry.get("detail"))
        if detail:
            line += f" ({clip(redact(detail), MAX_FIELD)})"
        lines.append(line)
    return lines


def browser_lines(browser: Mapping[str, object] | None) -> list[str]:
    """Render the ``## Browser`` block.

    Args:
        browser: Viewport, DPR, language, online, user agent, page URL.

    Returns:
        Markdown bullet lines for the fields that carry a value.
    """
    lines: list[str] = []
    if not isinstance(browser, Mapping):
        return lines
    for key, label in BROWSER_FIELDS:
        text = _value_text(browser.get(key))
        if text:
            lines.append(f"- {label}: {clip(redact(text), MAX_FIELD)}")
    return lines


def _section(heading: str, lines: Sequence[str]) -> str:
    """One body section: heading, blank line, lines.

    Args:
        heading: ``## `` heading.
        lines: Block content.

    Returns:
        Section text, empty when there are no lines.
    """
    if not lines:
        return ""
    return f"{heading}\n\n" + "\n".join(lines)


def build_body(
    kind: str,
    surface: str,
    context: Sequence[tuple[str, object]] | None,
    environment: Sequence[tuple[str, object]] | None,
    errors: Sequence[Mapping[str, object]] | None,
    browser: Mapping[str, object] | None,
    traceback: str,
) -> str:
    """Assemble the markdown body in the canonical section order.

    The four narrative sections always appear for a ``bug``; every other block
    keeps its heading only when it has content. A traceback, when supplied, is
    a fenced block after ``## Browser``.

    Args:
        kind: ``bug`` or ``enhancement``.
        surface: One of the shared surface ids.
        context: Surface facts for ``## Context``.
        environment: Host facts for ``## Environment``.
        errors: Ring-buffer entries for ``## Recent errors``.
        browser: Browser facts for ``## Browser``.
        traceback: Optional traceback text.

    Returns:
        Markdown body, redacted, without a trailing newline.
    """
    blocks: list[str] = []
    if kind_key(kind) == "bug":
        blocks.extend(_section(heading, [FILL_IN]) for heading in FILL_HEADINGS)
    blocks.append(_section(CONTEXT_HEADING, context_lines(context)))
    blocks.append(_section(ENVIRONMENT_HEADING, context_lines(environment)))
    blocks.append(_section(ERRORS_HEADING, error_lines(errors, surface)))
    blocks.append(_section(BROWSER_HEADING, browser_lines(browser)))
    body = "\n\n".join(block for block in blocks if block)
    note = _value_text(traceback)
    if note:
        block = f"{TRACEBACK_LABEL}\n\n```\n{redact(note)}\n```"
        body = f"{body}\n\n{block}" if body else block
    return body.strip()


def _drop_section(body: str, heading: str) -> str:
    """Remove one ``## `` section (heading plus its lines) from a built body.

    Args:
        body: Body from :func:`build_body`.
        heading: Heading to drop.

    Returns:
        Body without that section.
    """
    kept: list[str] = []
    skipping = False
    for line in body.split("\n"):
        if line.strip() == heading:
            skipping = True
            continue
        if skipping and (line.startswith("## ") or line.startswith(TRACEBACK_LABEL)):
            skipping = False
        if not skipping:
            kept.append(line)
    return "\n\n".join(block for block in "\n".join(kept).split("\n\n") if block.strip())


def _drop_traceback(body: str) -> str:
    """Drop the trailing traceback block.

    Args:
        body: Body from :func:`build_body`.

    Returns:
        Body without the ``Traceback:`` block.
    """
    index = body.find(TRACEBACK_LABEL)
    return body[:index].rstrip() if index >= 0 else body


def issue_href(title: str, body: str, labels: Sequence[str], repo: str = REPO) -> str:
    """Build a ``/issues/new`` URL that stays openable.

    Past :data:`MAX_HREF` the payload degrades in the documented order:
    ``## Browser``, then ``## Recent errors``, then ``## Environment``, then
    the traceback. Title and labels never drop.

    Args:
        title: Issue title from :func:`title_for`.
        body: Markdown body from :func:`build_body`.
        labels: Labels to preselect.
        repo: ``owner/name``; defaults to :data:`REPO`.

    Returns:
        ``https://github.com/<repo>/issues/new?title=&body=&labels=``.
    """
    joined = ",".join(str(label) for label in labels)

    def encode(text: str) -> str:
        """Encode one body into the new-issue URL.

        Args:
            text: Body text.

        Returns:
            The prefilled ``/issues/new`` URL.
        """
        query = urlencode({"title": title, "body": text, "labels": joined})
        return f"{GITHUB_URL}/{repo}/issues/new?{query}"

    def degrade(sections: Sequence[str], with_traceback: bool) -> str:
        """Rebuild the href after dropping whole sections.

        Args:
            sections: Headings to remove.
            with_traceback: Whether to keep the traceback block.

        Returns:
            The degraded href.
        """
        trimmed = body
        for heading in sections:
            trimmed = _drop_section(trimmed, heading)
        if not with_traceback:
            trimmed = _drop_traceback(trimmed)
        return encode(trimmed)

    href = encode(body)
    dropped: list[str] = []
    for heading in DEGRADE_ORDER:
        if len(href) <= MAX_HREF:
            return href
        dropped.append(heading)
        href = degrade(dropped, True)
    if len(href) <= MAX_HREF:
        return href
    return degrade(dropped, False)


def _lookup(environ: Mapping[str, str], key: str) -> str:
    """Read one environment value without trusting the mapping.

    Args:
        environ: Environment mapping.
        key: Variable name.

    Returns:
        Value, or ``""`` when unset or unreadable.
    """
    try:
        return str(environ.get(key, ""))
    except Exception:  # noqa: BLE001 - env facts must never raise
        return ""


def _probe_facts(probe: Callable[[], Mapping[str, str]] | None) -> dict[str, str]:
    """Run the injected torch/GPU probe defensively.

    Args:
        probe: Callable returning extra facts, or ``None``.

    Returns:
        The probe's mapping as a dict; empty when it fails or lies.
    """
    if probe is None:
        return {}
    try:
        found = probe()
    except Exception:  # noqa: BLE001 - a broken probe must not sink the report
        return {}
    if not isinstance(found, Mapping):
        return {}
    return {str(key): value for key, value in found.items()}


def env_snapshot(
    environ: Mapping[str, str],
    probe: Callable[[], Mapping[str, str]] | None = None,
) -> dict[str, str]:
    """Environment facts for the ``## Environment`` block.

    Never raises and never imports torch: GPU and CUDA facts arrive only
    through ``probe``. Unset variables come back as empty strings so callers
    always see the same keys.

    Args:
        environ: Environment mapping (pass ``os.environ``).
        probe: Optional zero-arg callable with torch / CUDA / GPU facts.

    Returns:
        ``label -> value`` facts, at least ``comfyui_ref``, ``image``,
        ``python``, ``platform``, ``output_dir``, ``comfy_port``.
    """
    facts: dict[str, str] = {}
    for key, variable in ENV_KEYS:
        facts[key] = redact(_lookup(environ, variable) or ENV_DEFAULTS.get(key, ""))
    facts["python"] = redact(_safe_text(platform.python_version, "unknown"))
    facts["platform"] = redact(
        _safe_text(lambda: f"{platform.system()} {platform.machine()}", "unknown")
    )
    for key, value in _probe_facts(probe).items():
        text = _value_text(value)
        if text:
            facts[redact(key)] = redact(text)
    return facts

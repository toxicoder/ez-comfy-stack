#!/usr/bin/env python3
"""Static guard for "Bazel is the ingress" in committed text.

Bazel is the documented way to run anything in this repo, so a committed file
that tells a reader to invoke a repo script directly teaches the wrong door.
The guard reads every committed text file, looks only at **command position**
(a fenced block line or a backticked span, where a reader actually copies from),
and fails when such a command has a Bazel target.

Three committed formats are JSON, so the text sweep skips them as data and each
gets its own pass over the text an operator really copies: the note fields of
the lab graphs (ComfyUI renders them on the canvas), the ``argv`` of the
site's command-builder recipes (the docs-site widgets join it into the line a
reader pastes), and the ``short`` / ``long`` of the glossary entries
(``docs/glossary.py`` renders each into a published card). All three reuse the
same ``RULES``, the same host-verb exemption, and the same report shape as the
text sweep.

Two escapes exist, both explicit tables rather than a comment a reader can
forget to delete:

``_HOST_ESCAPE_HATCH``
    ``./scripts/manage.sh <verb>`` for the verbs that need Docker, ``sudo``, the
    GPU, or ``$HOME``. Those cannot run hermetically, so the raw script stays
    the documented door *in a script*, where the text is the escape hatch's own
    usage header and log lines.
``_ALLOW``
    Named exemptions for the few places the raw command is correct: the
    bootstrap that installs bazelisk before bazelisk exists, the CI docs build
    that runs after ``bazelisk shutdown``, and scripts with no target at all.
    The table is checked in both directions like the glob allowlist in
    ``tests/bazel_deps.py``: a ``path:line`` key that no longer lands on a
    flagged command, or a bare ``path`` key whose file is gone, is itself a
    failure, so an exemption cannot outlive the sentence it was written for.

Published prose gets no host-verb exemption. ``is_published_doc`` marks the text
an operator reads and pastes from - the pages under ``docs`` including the ones
``//docs:generate`` writes, plus ``README.md`` and ``CONTRIBUTING.md`` - and the
lab-graph notes, the command-builder recipes the widgets copy, and the glossary
cards ``docs/glossary.py`` renders. There the Bazel
target is the door even for a host verb: ``bazelisk run //:manage -- <verb>``
execs the same script on the host, passes the client environment through, and
keeps the interactive ``start`` confirm, so the raw form on a page teaches the
wrong door. A page that documents the raw form *as the fallback* keeps it by
carrying its own ``_ALLOW`` reason.

Deliberately not checked: a bare path in prose ("``scripts/manage.sh`` routes
operator actions") is a file reference, not an instruction to run it. In source
files the sweep reads comments, docstrings, and the strings an output helper
prints, which is the text an operator actually copies, and leaves executed code
alone. A leading ``NAME=value`` assignment is read past, so
``LAB_STACK_FORCE_BUILD=1 ./scripts/manage.sh start`` is caught and the fix
keeps the assignment in front.

Usage:
    bazelisk test //tests:bazel_docs_check
    python3 tests/bazel_docs.py                 # whole checkout
    python3 tests/bazel_docs.py --root /path/to/checkout
    python3 tests/bazel_docs.py docs/contribute/building-with-bazel.md
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

# --------------------------------------------------------------------------
# What counts as a command position
# --------------------------------------------------------------------------

_FENCE = re.compile(r"^\s*(```|~~~)")
# A backticked span, non-greedy, allowing the doubled-backtick form.
_CODE_SPAN = re.compile(r"(`+)(.+?)\1", re.S)

# Files whose comments and printed strings are operator-facing text: a `#`
# comment in a script, a docstring in Python, the body of an `echo` or a usage
# heredoc. These get read as closely as a Markdown page, because that is where
# an operator actually meets the command.
_CODE_SUFFIX = (".sh", ".bash", ".bats", ".py", ".bzl", ".mjs", ".js", ".ts", ".tsx")
# Shipped templates the operator reads before the first run: an env template, a
# restricted-YAML catalog, a compose file, a CI workflow, and the PowerShell
# client installer. None of them can hold a fenced block, so as prose they
# yielded no command position at all and the sweep passed over the raw door in
# their headers. Read them as code: their comment syntax is the shell's, so the
# rule that already covers a script's own usage header covers these too. An
# executed config value (`command: "./scripts/manage.sh start"`) is still
# implementation and stays unpoliced, because _code_line_candidates reads
# quoted strings only where an output helper prints them.
_TEMPLATE_SUFFIX = (".yml", ".yaml", ".ps1", ".env", ".example")
# A `#` or `//` comment body.
_COMMENT = re.compile(r"^\s*(?:#+|//+)\s?(.*)$")
# A string literal passed to an output helper, in either quote style.
_ECHO_STRING = re.compile(r"""["']([^"']*)["']""")
# The repo's own output helpers: echo and printf plus manage.sh's log/warn/err.
_OUTPUT_HELPER = re.compile(r"\b(?:echo|printf|log|warn|err|die|note)\b")
# The opening of a heredoc: cat <<EOF, cat <<'EOF', cat <<-'EOF'.
_HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?")
# Bullets and arrows a docstring pads a command with.
_LEAD_NOISE = re.compile(r"^[-*> \t]+")
# A metavariable like `<verb>`: documents a shape, nothing to copy.
_PLACEHOLDER = re.compile(r"<[^>]*>")
# Leading `NAME=value` assignments. `FOO=1 ./scripts/manage.sh start` is the
# same raw door as the bare form, so the matcher reads past the prefix and the
# suggestion keeps it.
_ENV_ASSIGNMENT = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)+")

# Text an operator reads and pastes from, where the Bazel target is the door
# even for a host verb. `docs/generated/` counts: //docs:generate writes it, so
# a raw door there is a generator template that still needs fixing. The lab
# graphs and the command-builder recipes are covered by their own passes.
_PUBLISHED_DOC_DIR = "docs/"
_PUBLISHED_DOC_FILES = ("README.md", "CONTRIBUTING.md")
_PUBLISHED_DOC_SUFFIX = (".md", ".mdx")

# Directories whose committed text is operator-facing documentation. Everything
# tracked is swept except what _SKIP_DIR / _SKIP_SUFFIX say below.
_SKIP_DIR = (
    "docs-site/node_modules/",
    "docs-site/out/",
    "custom_nodes/ez_music/",
)
_SKIP_SUFFIX = (".json", ".png", ".jpg", ".jpeg", ".mp4", ".gif", ".woff", ".woff2", ".ico", ".map")
_SKIP_FILES = ("docs-site/package-lock.json",)
# ComfyUI graphs are JSON, so the text sweep skips them as data. Their note
# fields are prose an operator reads on the canvas, so they get their own pass.
_LAB_DIR = "workflows/_lab"
# The command widgets are JSON too, and sweeping arbitrary JSON as prose is not
# the policy. The file is the source the site's copy buttons draw from -
# docs-site/components/command-vars.tsx imports it and
# docs-site/lib/command-vars.ts joins each recipe's argv into the line the reader
# pastes - so the recipes get their own pass over that rendered line.
_COMMAND_BUILDER_FILE = "includes/command-builder.json"
# The glossary is the third JSON the site renders as operator text:
# docs/glossary.py turns each entry's short and long into a published card. A
# card is a sentence rather than a command position, so the pass below reads
# the clause-initial run of each field, which is where an instruction starts.
_GLOSSARY_FILE = "includes/glossary.json"
_GLOSSARY_PROSE_FIELDS = ("short", "long")
# A field splits into clauses at a backtick (the shipped cards backtick their
# commands) and after the two punctuation marks that introduce an instruction.
# A sentence period is deliberately absent: "the studio. ./scripts/manage.sh
# setup copies this" is a subject mention in prose, and promoting it would have
# the gate demand an exemption for a sentence that never asked to be pasted.
_CLAUSE_BREAK = re.compile(r"(?:^|`+|(?::|;)\s+)")
_TRAILING_PROSE = ".,;:!?|)]}\"' "

# --------------------------------------------------------------------------
# The policy
# --------------------------------------------------------------------------

# manage.sh verbs that need Docker, sudo, the GPU, or $HOME. For these the raw
# script stays the documented door; see "Safety" in
# docs/contribute/building-with-bazel.md. Every other verb has to be shown in
# its `bazelisk run //:manage -- <verb>` form.
HOST_VERBS = frozenset(
    {
        "setup",
        "setup-client",
        "onboard",
        "start",
        "stop",
        "restart",
        "update-stack",
        "blender-install",
    }
)
HOST_VERB_PREFIXES = ("download-",)

# Raw command shape -> (kind, Bazel target template). The pattern is matched
# against the command text; group "rest" carries the sub-command, which the
# checker feeds back into the suggested target so the advice is copyable. "kind"
# is what the checker branches on: a substring test on ``pattern.pattern`` would
# miss, because the pattern escapes the dot.
RULES: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)?(?:\./)?scripts/manage\.sh(?:\s+(?P<rest>.*))?$"),
        "bazelisk run //:manage -- {rest}",
        "manage",
    ),
    (
        re.compile(
            r"^(?:\./|bash\s+\./?|sh\s+\./?)scripts/utilities/(?P<name>[\w-]+)\.sh(?:\s+(?P<rest>.*))?$"
        ),
        "bazelisk run //scripts:run-utility -- {name} {rest}",
        "utility",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)(?:\./)?scripts/everything\.sh\b.*$"),
        "bazelisk run //:everything",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)(?:\./)?scripts/validate\.sh\b.*$"),
        "bazelisk run //:validate",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)(?:\./)?docker/compose_config_test\.sh\b.*$"),
        "bazelisk test //docker:compose_config",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)(?:\./)?tests/bazel_deps\.py\b.*$"),
        "bazelisk test //tests:owned_files_check",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)(?:\./)?tests/run_all\.sh\b.*$"),
        "bazelisk test //:test-fast",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)(?:\./)?tests/run_pytest\.sh\b.*$"),
        "bazelisk test //tests:pytest",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)(?:\./)?tests/coverage\.sh\b.*$"),
        "bazelisk test //:coverage",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)(?:\./)?tests/typecheck\.sh\b.*$"),
        "bazelisk test //tests:typecheck",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)(?:\./)?lints/run_\w+\.sh\b.*$"),
        "bazelisk test //:lint --test_tag_filters=manual",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)?(?:\./)?docs/manage-docs\.sh\s+serve\b.*$"),
        "bazelisk run //docs:serve",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)?(?:\./)?docs/manage-docs\.sh\s+build\b.*$"),
        "bazelisk run //docs:docs",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)?(?:\./)?docs/setup-docs\.sh\b.*$"),
        "bazelisk run //docs-site:install",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)(?:\./)?docs/generate_shell_docs\.py\b.*$"),
        "bazelisk run //docs:generate_shell",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)(?:\./)?docs/generate_workflow_docs\.py\b.*$"),
        "bazelisk run //docs:generate_workflow",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)(?:\./)?docs/generate_cinema_docs\.py\b.*$"),
        "bazelisk run //docs:generate_cinema",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)(?:\./)?docs/generate_audio_docs\.py\b.*$"),
        "bazelisk run //docs:generate_audio",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)(?:\./)?docs/generate_\w+\.py\b.*$"),
        "bazelisk run //docs:generate",
        "plain",
    ),
    (
        re.compile(r"^(?:bash\s+|sh\s+|python3?\s+)(?:\./)?docs-site/scripts/visual_linux\.sh\b.*$"),
        "bazelisk run //docs-site:visual-linux",
        "plain",
    ),
    (
        re.compile(r"^(?:python3?\s+|bash\s+|sh\s+)(?:\./)?docs-site/scripts/gen_nav\.py\b.*$"),
        "bazelisk test //docs-site:nav_test",
        "plain",
    ),
    (
        # Only the JS builder has a target. The other tests/python/_build_*.py
        # scripts write straight into workflows/_lab and the Cinema/Audio Rack
        # JSON, which are the live shipped artifacts, so a target would hand
        # anyone a command that rewrites ~300 promoted graphs and a geometry
        # diff nobody asked for. They run under pytest; a graph is refreshed
        # through ./scripts/manage.sh promote-workflow. Claiming a target for
        # them here would be the guard inventing advice, so it stays silent.
        re.compile(r"^(?:python3?\s+|bash\s+|sh\s+)(?:\./)?tests/python/_build_quality_js\.py\b.*$"),
        "bazelisk run //tests:build_quality_js",
        "plain",
    ),
)

# Exempted commands, keyed by "path" or "path:line", each with the reason. An
# entry here is a decision that the raw command is the right one at this spot,
# so it has to say why.
_ALLOW: dict[str, str] = {
    # The bootstrap cannot be expressed as a Bazel target: its whole job is to
    # install bazelisk, which has to exist before any target can run.
    "scripts/setup-host.sh": "installs bazelisk itself, so no target can be the door",
    ".github/scripts/install-lint-tools.sh": "execs scripts/ci/install-lint-tools.sh; "
    "both are the CI toolchain lane, which runs outside Bazel by design",
    "scripts/ci/install-lint-tools.sh": "the CI toolchain installer; "
    "//scripts:ci_install_lint_tools is a filegroup, not runnable, so the "
    "workflow execs this source directly",
    "scripts/ci_check_only.sh": "validate.sh execs it under CI as an implementation "
    "detail; it declares no target of its own",
    "scripts/ci/publish-pages-tree.sh": "the deploy job execs it from the "
    "checkout; //scripts:ci_publish_pages_tree is a filegroup, not runnable",
    # The command is the payload of an ssh heredoc sent to a Spark that has no
    # bazelisk yet, and the other is prose explaining why the raw delegation is
    # the policy. Neither is a reader-facing instruction.
    "scripts/utilities/setup-client.sh:79": "inside the 'cat <<EOF' payload piped "
    "to ssh ez-spark: it runs on a fresh Spark with no bazelisk installed yet",
    "docs/cinema_clip_prompts.py": "author-time prompt helper with no target",
    "docs-site/scripts/gen_nav.py": "the nav generator itself; //docs-site:nav_test "
    "unit-tests this file rather than running it",
    "docs-site/scripts/codemod_mkdocs_to_mdx.py": "one-off migration helper with no "
    "target; kept for the next docs format change",
    "scripts/lib/quality_apply.py": "internal helper reached through manage.sh, not "
    "an operator entry point",
    "Makefile": "every make target is a documented shim that forwards to a Bazel "
    "target, and the shim path is what the header advertises",
    ".github/workflows/ci.yml": "the docs job runs after 'bazelisk shutdown', so it "
    "cannot consult a target at that point",
    "tests/bazel_deps.py": "the guard's own docstring shows the standalone form "
    "because a failing run has to be reproducible without a working graph",
    "tests/python/test_bazel_docs.py": "the parser's own unit test: a raw script "
    "command is the payload it feeds the classifier, not advice a reader follows",
    # Both of these sentences are about the escape hatch itself. Rewriting them
    # into the wrapper form would make the sentence describe something that no
    # longer exists.
    "docs/contribute/testing-docs.mdx:134": "CI runs the docs build after "
    "'bazelisk shutdown', so the page has to name the script it really calls",
    # The page leads with the target and puts the raw form in parentheses as the
    # fallback, which is the pattern AGENTS.md keeps for a host-mutating verb.
    "docs/contribute/host-setup.mdx:268": "names the operator escape hatch "
    "beside the documented target for 'setup --install-docker'",
    # The header leads with 'bazelisk run //docs-site:install', which is
    # run_npm.sh install and ignores QUIET. Only the script itself reads that
    # variable, so the second Usage line has to show the direct call.
    "docs/setup-docs.sh:8": "shows the QUIET knob the //docs-site:install "
    "target does not expose; the line above it names that target",
    # MIGRATION.md carries one block headed "Without Bazel". Naming the scripts
    # is the entire point of that block; the Bazel forms are documented above it.
    "MIGRATION.md:70": "inside the page's 'Without Bazel' block, which documents "
    "the fallback path by name",
    "MIGRATION.md:71": "inside the page's 'Without Bazel' block, which documents "
    "the fallback path by name",
    "MIGRATION.md:72": "inside the page's 'Without Bazel' block, which documents "
    "the fallback path by name",
}

# Commands the policy does not police, with the reason.
_IGNORED_COMMANDS: dict[str, str] = {
    "make": "make targets are documented shims over Bazel targets and the Makefile "
    "header leads with the Bazel form",
}

# --------------------------------------------------------------------------
# Reading files
# --------------------------------------------------------------------------


def repo_root() -> Path:
    """The checkout root, resolved through runfiles symlinks under bazel test."""
    here = Path(__file__).resolve()
    for candidate in (here.parent.parent, Path.cwd()):
        if (candidate / "MODULE.bazel").is_file():
            return candidate
    raise SystemExit(f"bazel_docs: cannot locate MODULE.bazel from {here}")


def tracked_files(root: Path) -> list[str]:
    """The paths `git ls-files` reports, relative to ``root``."""
    proc = subprocess.run(
        ["git", "-C", str(root), "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(line for line in proc.stdout.splitlines() if line)


def candidate_files(tracked: Iterable[str]) -> list[str]:
    """Tracked text files worth reading for command examples."""
    out: list[str] = []
    for path in tracked:
        if path.startswith(_SKIP_DIR) or path in _SKIP_FILES:
            continue
        if path.endswith(_SKIP_SUFFIX) or path.endswith((".pyc", ".tar.gz")):
            continue
        out.append(path)
    return out


def _code_line_candidates(line: str) -> list[str]:
    """The comment body and the printed strings on one line of a script.

    Globals: none.
    Arguments:
      line - one raw line from a shell, Python, or TypeScript source file.
    Outputs:
      None (pure).
    Returns:
      Zero to a few strings that a reader could copy: the text after a ``#`` or
      ``//``, and every quoted argument of an output helper. Actual executed
      code is never returned, so an internal ``bash tests/run_pytest.sh`` call
      site stays implementation and is not policed here.
    """
    if line.lstrip().startswith("#!"):
        return []
    comment = _COMMENT.match(line)
    if comment:
        body = _LEAD_NOISE.sub("", comment.group(1)).strip()
        return [body] if body else []
    if _OUTPUT_HELPER.search(line):
        return [found for found in (s.strip() for s in _ECHO_STRING.findall(line)) if found]
    return []


def docstring_positions(text: str) -> list[tuple[int, str]]:
    """Every ``(line, command)`` sitting inside a Python docstring.

    A docstring is the text ``pydoc`` and an editor tooltip show, so it is read
    exactly like a page. The line scanner above reads comments and the strings an
    output helper prints, and neither reaches a triple-quoted block: a generator
    whose own Usage paragraph says "run me with python3" teaches that door to
    everyone who opens the file.

    Globals: none.
    Arguments:
      text - the contents of a ``.py`` file.
    Outputs:
      None (pure).
    Returns:
      ``(line, stripped_line)`` pairs for each non-empty docstring line. An
      unparseable file yields nothing rather than raising, so a syntax error in a
      scratch file is not reported as a doc violation.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    found: list[tuple[int, str]] = []
    nodes: tuple[type[ast.AST], ...] = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for node in ast.walk(tree):
        if not isinstance(node, nodes) or not node.body:
            continue
        first = node.body[0]
        if not isinstance(first, ast.Expr) or not isinstance(first.value, ast.Constant):
            continue
        value = first.value.value
        if not isinstance(value, str):
            continue
        for offset, line in enumerate(value.splitlines()):
            stripped = line.strip()
            if stripped:
                found.append((int(first.lineno) + offset, stripped))
    return found


def command_positions(text: str, code: bool = False) -> list[tuple[int, str]]:
    """Every ``(line_number, command)`` a reader could copy from this text.

    Globals: none.
    Arguments:
      text - the file contents.
      code - True for a source file, where comments, docstrings, and the strings
        an output helper prints are operator-facing text next to the code.
    Outputs:
      None (pure).
    Returns:
      ``(line, command)`` pairs for fenced code blocks, backticked spans, and,
      when ``code`` is set, comment bodies, output-helper strings, and heredoc
      bodies. Line numbers start at 1. A multi-line span yields its last line so
      a report points at the command rather than the opening fence.
    """
    found: list[tuple[int, str]] = []
    fence: str | None = None
    heredoc: str | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        marker = _FENCE.match(line)
        if marker and heredoc is None:
            tick = marker.group(1)
            if fence is None:
                fence = tick
            elif tick == fence:
                fence = None
            continue
        if fence is not None:
            stripped = line.strip()
            if stripped:
                found.append((number, stripped))
            continue
        if heredoc is not None:
            if line.strip() == heredoc:
                heredoc = None
            elif line.strip():
                found.append((number, line.strip()))
            continue
        if code:
            found.extend((number, candidate) for candidate in _code_line_candidates(line))
            opened = _HEREDOC.search(line)
            if opened:
                heredoc = opened.group(1)
        for span in _CODE_SPAN.finditer(line):
            for offset, inner in enumerate(span.group(2).splitlines()):
                stripped = inner.strip()
                if stripped and any(char.isalnum() for char in stripped):
                    found.append((number + offset, stripped))
    return found


# --------------------------------------------------------------------------
# The check
# --------------------------------------------------------------------------


def is_host_verb(verb: str) -> bool:
    """True when a manage.sh verb needs Docker, sudo, the GPU, or $HOME."""
    if not verb:
        return False
    if verb in HOST_VERBS:
        return True
    return any(verb.startswith(prefix) for prefix in HOST_VERB_PREFIXES)


def is_published_doc(path: str) -> bool:
    """True when ``path`` is prose an operator reads and pastes from.

    Globals: _PUBLISHED_DOC_DIR, _PUBLISHED_DOC_FILES, _PUBLISHED_DOC_SUFFIX.
    Arguments:
      path - repo-relative tracked path.
    Outputs:
      None (pure).
    Returns:
      True for the Markdown pages under ``docs`` (generated ones included, since
      a raw door there came from a generator template) and the two repo pages.
      Source files are False: a script's own usage header is the escape hatch
      that AGENTS.md keeps raw.
    """
    if path in _PUBLISHED_DOC_FILES:
        return True
    return path.startswith(_PUBLISHED_DOC_DIR) and path.endswith(_PUBLISHED_DOC_SUFFIX)


def split_env(command: str) -> tuple[str, str]:
    """Split a command into its leading ``NAME=value`` prefix and its body.

    Globals: _ENV_ASSIGNMENT.
    Arguments:
      command - the command text from a code span or fenced block.
    Outputs:
      None (pure).
    Returns:
      ``(prefix, body)`` with the assignments that set the environment for the
      command in ``prefix`` (empty string when there are none) and the command
      itself in ``body``. An empty command yields ``("", "")``.
    """
    lead = _ENV_ASSIGNMENT.match(command)
    if lead is None:
        return "", command.strip()
    return lead.group(0).strip(), command[lead.end():].strip()


def classify(command: str, *, published: bool = False) -> tuple[str, str] | None:
    """Match one command against the policy.

    Globals: RULES, _IGNORED_COMMANDS.
    Arguments:
      command - the command text from a code span or fenced block.
      published - True for text an operator pastes from, where a host verb loses
        its escape-hatch exemption because the Bazel wrapper runs the identical
        script on the host.
    Outputs:
      None (pure).
    Returns:
      ``(violation, suggestion)`` when the command should have been written as a
      Bazel target, or None when it is a Bazel command, an ignored command, a
      host escape hatch, or not a repo entry point at all. A leading
      ``NAME=value`` prefix is read past for matching and kept in the suggestion.
    """
    head = command.split()
    if not head:
        return None
    prefix, body = split_env(command)
    if body.startswith("bazelisk ") or body.startswith("bazel "):
        return None
    if head[0] in _IGNORED_COMMANDS:
        return None
    lead = f"{prefix} " if prefix else ""
    for pattern, template, kind in RULES:
        match = pattern.match(body)
        if match is None:
            continue
        groups = match.groupdict()
        rest = (groups.get("rest") or "").strip()
        rest = rest.split(" #", 1)[0].strip()
        if kind == "manage":
            # `scripts/manage.sh` with no verb is a file reference in prose, and
            # `<verb>` documents the shape rather than asking for a copy.
            verb = rest.split()[0] if rest else ""
            if not verb or _PLACEHOLDER.fullmatch(verb):
                return None
            if is_host_verb(verb) and not published:
                return None
        if kind == "utility":
            # A download utility pulls weights into $HOME over the network, so it
            # needs the same host door as the `download-*` verbs of manage.sh.
            name = (groups.get("name") or "").strip()
            if any(name.startswith(prefix_) for prefix_ in HOST_VERB_PREFIXES) and not published:
                return None
        name = (groups.get("name") or "").strip()
        try:
            suggestion = template.format(rest=rest, name=name).strip()
        except (KeyError, IndexError):
            suggestion = template
        return (command, " ".join(f"{lead}{suggestion}".split()))
    return None


def allowed(path: str, line: int, command: str) -> bool:
    """True when an exemption in _ALLOW covers this command position.

    Matching is by exact ``path:line`` or by bare ``path`` (the whole file). A
    script is not exempt for its own file: the usage header and the strings it
    prints are the text an operator copies, so they name targets like any other
    doc, and a script that genuinely has no target is exempted by name above.

    Globals: _ALLOW.
    Arguments:
      path - repo-relative file.
      line - line number of the command position.
      command - the offending command; unused, kept so callers can report it.
    Outputs:
      None (pure).
    Returns:
      True when the position is exempt.
    """
    del command
    return f"{path}:{line}" in _ALLOW or path in _ALLOW


def findings(root: Path, paths: Sequence[str], *, use_allow: bool = True) -> list[tuple[str, int, str, str]]:
    """Every command-position hit in ``paths``, exempt or not.

    Globals: _ALLOW.
    Arguments:
      root - checkout root.
      paths - repo-relative tracked paths to read.
      use_allow - apply _ALLOW; False reports the exempt hits too.
    Outputs:
      None; returns tuples only.
    Returns:
      One ``(path, line, offending, suggestion)`` tuple per hit, in path order.
    """
    found: list[tuple[str, int, str, str]] = []
    for path in paths:
        file_path = root / path
        if not file_path.is_file():
            continue
        try:
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        code = path.endswith(_CODE_SUFFIX)
        template = path.endswith(_TEMPLATE_SUFFIX)
        # A template is pasted from the way a page is, so a host verb gets no
        # exemption in one: the raw door belongs to the script's own usage
        # header, not to a config file that only mentions the CLI.
        published = is_published_doc(path) or template
        positions = command_positions(text, code=code or template)
        if template:
            # A template header is a sentence, not a line to paste, so the
            # comment body is read the way a glossary card is: the run after a
            # clause break is where an instruction starts.
            positions = [
                (number, candidate)
                for number, raw in positions
                for candidate in prose_command_candidates(raw)
            ]
        if path.endswith(".py"):
            positions += docstring_positions(text)
        for line, command in positions:
            result = classify(command, published=published)
            if result is None:
                continue
            offending, suggestion = result
            if use_allow and allowed(path, line, offending):
                continue
            found.append((path, line, offending, suggestion))
    return found


def stale_exemptions(root: Path, paths: Sequence[str] | None = None) -> list[str]:
    """Report _ALLOW entries that no longer point at anything real.

    Two ways an exemption rots, and each gets a different question asked of it.

    A ``path:line`` key is a pointer into one sentence. When the file grows
    above that sentence the pointer aims at unrelated text, and the next person
    who reads the table learns nothing. So a line key has to sit on a command
    position the sweep actually flags with the table switched off.

    A bare ``path`` key is a standing statement that this file is a named
    exemption - the bootstrap, the CI installer, a helper with no target. It
    stays true even in a release where the file happens to be clean, so it is
    only dead once the file is gone.

    Globals: _ALLOW.
    Arguments:
      root - checkout root.
      paths - optional list to sweep; defaults to the whole checkout.
    Outputs:
      None; returns the findings only.
    Returns:
      One string per dead exemption key.
    """
    tracked = tracked_files(root) if paths is None else list(paths)
    tracked_set = set(tracked)
    hits = findings(root, tracked, use_allow=False)
    live_lines = {f"{path}:{line}" for path, line, _, _ in hits}
    dead: list[str] = []
    for key, reason in sorted(_ALLOW.items()):
        if ":" in key:
            if key not in live_lines:
                dead.append(f"{key}: {reason} (no flagged command sits on this line any more)")
            continue
        if key not in tracked_set and not (root / key).is_file():
            dead.append(f"{key}: {reason} (the file is gone)")
    return dead


def lab_note_fields(graph: Mapping[str, Any]) -> list[str]:
    """Operator-facing note text a ComfyUI graph carries.

    Globals: none.
    Arguments:
      graph - a parsed workflows/_lab graph.
    Outputs:
      None; returns the strings only.
    Returns:
      ``extra.lab_note`` plus every Note node body, in document order.
    """
    notes: list[str] = []
    lab_note = (graph.get("extra") or {}).get("lab_note")
    if isinstance(lab_note, str):
        notes.append(lab_note)
    for node in graph.get("nodes") or []:
        if not isinstance(node, Mapping):
            continue
        if str(node.get("type", "")).strip().lower() != "note":
            continue
        widgets = node.get("widgets_values") or []
        if widgets and isinstance(widgets[0], str):
            notes.append(widgets[0])
    return notes


def lab_graph_violations(root: Path, paths: Sequence[str]) -> list[str]:
    """Sweep lab-graph notes, which the doc sweep skips as binary-ish JSON.

    A graph note is operator-facing text: ComfyUI renders it on the canvas and
    ``//docs:generate_workflow`` copies it into the published workflow pages, so
    it names Bazel targets the same way prose does.

    Globals: none.
    Arguments:
      root - checkout root.
      paths - repo-relative tracked paths to consider.
    Outputs:
      None; returns the violations only.
    Returns:
      One string per command-position script reference found in a graph note.
    """
    problems: list[str] = []
    for path in paths:
        if not path.startswith(f"{_LAB_DIR}/") or not path.endswith(".json"):
            continue
        file_path = root / path
        if not file_path.is_file():
            continue
        try:
            graph = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(graph, Mapping):
            continue
        for note in lab_note_fields(graph):
            for line, command in command_positions(note, code=False):
                found = classify(command, published=True)
                if found is None:
                    continue
                offending, suggestion = found
                if allowed(path, line, offending):
                    continue
                problems.append(f"{path}: {offending} -> {suggestion}")
    return problems


def builder_recipe_commands(builder: Mapping[str, object]) -> list[tuple[str, str]]:
    """The ``(recipe id, copied line)`` pair for each command-builder recipe.

    The widget renders the argv list it is handed as ``" ".join(argv)`` plus the
    selected flags, and that is the line the reader pastes, so the join is what
    the policy reads rather than the raw JSON. Prose fields such as
    ``description`` stay out of it, and a script path sitting inside an argument
    is an argument, not the command the recipe runs.

    Globals: none.
    Arguments:
      builder - a parsed includes/command-builder.json.
    Outputs:
      None; returns the pairs only.
    Returns:
      ``(id, command)`` per recipe carrying a non-empty argv, in document order.
      A row that is not an object, or one whose argv is missing or not a list of
      strings, yields no pair rather than raising.
    """
    recipes = builder.get("commands")
    if not isinstance(recipes, list):
        return []
    out: list[tuple[str, str]] = []
    for recipe in recipes:
        if not isinstance(recipe, Mapping):
            continue
        argv = recipe.get("argv")
        if not isinstance(argv, list):
            continue
        command = " ".join(item for item in argv if isinstance(item, str)).strip()
        if not command:
            continue
        out.append((str(recipe.get("id", "")).strip(), command))
    return out


def command_builder_violations(root: Path, paths: Sequence[str]) -> list[str]:
    """Sweep the command-builder recipes, which the doc sweep skips as JSON.

    A recipe's argv is the clipboard text behind every command widget on the
    published pages, so it is operator-facing exactly like a fenced block, and it
    has to name the same targets the docs name. Host verbs are policed here as
    they are in prose: the wrapper execs the same script on the host, so a widget
    that copies the raw door is teaching the wrong one. A recipe whose argv is a
    plain shell line (an ``ssh`` tunnel, an ``echo`` of a URL, a
    ``docker compose`` call) names no repo entry point, so ``classify`` returns
    None and the recipe is legal as written; if that ever stops being true, the
    exemption belongs in ``_IGNORED_COMMANDS`` with its reason.

    Globals: _ALLOW, _COMMAND_BUILDER_FILE.
    Arguments:
      root - checkout root.
      paths - repo-relative tracked paths to consider.
    Outputs:
      None; returns the violations only.
    Returns:
      One string per recipe whose rendered line names a repo script directly.
    """
    problems: list[str] = []
    for path in paths:
        if path != _COMMAND_BUILDER_FILE:
            continue
        file_path = root / path
        if not file_path.is_file():
            continue
        try:
            builder = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(builder, Mapping):
            continue
        for recipe_id, command in builder_recipe_commands(builder):
            found = classify(command, published=True)
            if found is None:
                continue
            offending, suggestion = found
            # A recipe has no line to point at, so only a bare `path` key in
            # _ALLOW can exempt one; a line-keyed entry cannot reach this pass.
            if allowed(path, 0, offending):
                continue
            label = recipe_id or "(recipe with no id)"
            problems.append(f"{path}: recipe {label}: {offending} -> {suggestion}")
    return problems


def prose_command_candidates(text: str) -> list[str]:
    """The clause-initial runs of one prose field, as candidate commands.

    A fenced block hands ``classify`` a whole line and a code span hands it
    exactly what was quoted; a glossary card hands it a sentence, where the
    command is the tail of a clause. Splitting at a backtick or at sentence
    punctuation puts a copy-me command at the head of a run, which is the shape
    the ``RULES`` patterns are anchored to, and leaves the narrative runs for
    ``classify`` to reject. The split never trims into the middle of a
    reference: a sentence whose subject is a file ("The scripts/manage.sh file
    routes operator actions") keeps its leading words, so it stays prose.

    Globals: _CLAUSE_BREAK, _LEAD_NOISE, _TRAILING_PROSE.
    Arguments:
      text - one prose field, such as a glossary entry's long text.
    Outputs:
      None (pure).
    Returns:
      Each non-empty clause with its bullet, trailing parenthetical, and
      sentence punctuation trimmed, in document order. A parenthetical is an
      aside about the command ("...(or, by hand: cp it to .env)"), so cutting
      there keeps the suggestion a line the operator could actually paste.
      Nothing is filtered here; that is ``classify``'s job.
    """
    out: list[str] = []
    for fragment in _CLAUSE_BREAK.split(text):
        candidate = _LEAD_NOISE.sub("", fragment).strip().split(" (", 1)[0]
        candidate = candidate.strip().rstrip(_TRAILING_PROSE)
        if candidate and any(char.isalnum() for char in candidate):
            out.append(candidate)
    return out


def glossary_prose_fields(glossary: object) -> list[tuple[str, str]]:
    """The ``(entry label, field text)`` pair for each operator-facing card.

    Globals: _GLOSSARY_PROSE_FIELDS.
    Arguments:
      glossary - a parsed includes/glossary.json.
    Outputs:
      None; returns the pairs only.
    Returns:
      ``("<id>.<field>", text)`` per prose field of every entry that is an
      object, in document order. A payload that is not a list, an entry that is
      not an object, and a field that is not a string each yield nothing rather
      than raising. A field is skipped when empty.
    """
    if not isinstance(glossary, list):
        return []
    out: list[tuple[str, str]] = []
    for entry in glossary:
        if not isinstance(entry, Mapping):
            continue
        entry_id = str(entry.get("id", "")).strip() or "(entry with no id)"
        for field in _GLOSSARY_PROSE_FIELDS:
            value = entry.get(field)
            if isinstance(value, str) and value.strip():
                out.append((f"{entry_id}.{field}", value))
    return out


def glossary_violations(root: Path, paths: Sequence[str]) -> list[str]:
    """Sweep the glossary cards, which the doc sweep skips as JSON.

    Each entry's ``short`` and ``long`` reach a published page through
    ``docs/glossary.py``, so a card that tells the operator to run a repo script
    teaches the wrong door to everyone who reads it, and host verbs are policed
    here the way they are in prose. A card that only names a script, or links to
    the manage.sh reference, is a file reference and stays legal.

    Globals: _ALLOW, _GLOSSARY_FILE.
    Arguments:
      root - checkout root.
      paths - repo-relative tracked paths to consider.
    Outputs:
      None; returns the violations only.
    Returns:
      One string per card field whose text names a repo script directly.
    """
    problems: list[str] = []
    for path in paths:
        if path != _GLOSSARY_FILE:
            continue
        file_path = root / path
        if not file_path.is_file():
            continue
        try:
            glossary = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        for label, text in glossary_prose_fields(glossary):
            for candidate in prose_command_candidates(text):
                found = classify(candidate, published=True)
                if found is None:
                    continue
                offending, suggestion = found
                # A card has no line the reader can see, so only a bare `path`
                # key in _ALLOW can exempt one; a line key cannot reach this pass.
                if allowed(path, 0, offending):
                    continue
                problems.append(f"{path}: {label}: {offending} -> {suggestion}")
    return problems


def violations(root: Path, paths: Sequence[str] | None = None) -> list[str]:
    """Every command-position script reference that should name a Bazel target."""
    tracked = candidate_files(tracked_files(root)) if paths is None else list(paths)
    # The three JSON passes read files the prose sweep drops, so they see the
    # unfiltered tracked list.
    data_paths = tracked_files(root) if paths is None else list(paths)
    problems: list[str] = []
    problems += lab_graph_violations(root, data_paths)
    problems += command_builder_violations(root, data_paths)
    problems += glossary_violations(root, data_paths)
    for path, line, offending, suggestion in findings(root, tracked):
        problems.append(f"{path}:{line}: {offending} -> {suggestion}")
    return problems


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    """Command line entry point.

    Globals: none.
    Arguments:
      argv - optional argument vector: --root plus optional file paths.
    Outputs:
      One violation per line on stdout, then a count summary.
    Returns:
      0 when every command position names a Bazel target, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description="Bazel-is-the-ingress doc guards")
    parser.add_argument("--root", default=None, help="checkout root (default: this file's parent)")
    parser.add_argument("paths", nargs="*", help="limit the sweep to these paths")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else repo_root()
    problems = violations(root, args.paths or None)
    for line in problems:
        print(line)
    if not args.paths:
        for entry in stale_exemptions(root):
            print(f"stale exemption: {entry}")
            problems.append(entry)
    print(f"bazel_docs: {len(problems)} violation(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

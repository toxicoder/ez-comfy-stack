#!/usr/bin/env python3
"""Static guards for the Bazel file mapping of this repo.

Bazel is the ingress for every way to run code here, so every tracked file
must be named by a BUILD.bazel file: an unmapped file is invisible to every
target, cannot invalidate a cached action, and disappears from CI without
anyone noticing. The same holds for the payloads a script-backed target
declares, and for test targets that belong to no suite.

A nested ``bazel query`` is not available from inside a test action (it
deadlocks on the output-base lock of the outer invocation), so this module
re-derives the three facts statically by parsing the BUILD files with ``ast``:

1. ownership - every ``git ls-files`` path is named by some BUILD file, or is
   exempted by ``_ALLOW`` / the repo's own ``.bazelignore``.
2. payload - the ``data`` labels a script target declares match what its own
   source reads, in both directions (missing runfiles and stale runfiles).
3. suites - every test target is a member of at least one suite.

It is a guard, not a Bazel reimplementation: the parser understands string
lists, ``+`` concatenation, and ``glob([...])`` patterns, which is everything
this repo's BUILD files use. A BUILD file that gets cleverer than that fails
loudly here rather than silently mapping nothing.

Usage:
    python3 tests/bazel_deps.py                 # all three checks
    python3 tests/bazel_deps.py --check-ownership
    python3 tests/bazel_deps.py --root /path/to/checkout
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

# --------------------------------------------------------------------------
# Exemptions
# --------------------------------------------------------------------------

# Files Bazel itself consumes. They are inputs to the build system, not to any
# target, so no BUILD file can or should name them.
_ALLOW: dict[str, str] = {
    ".bazelignore": "read by Bazel; it is this guard's input, not a target's",
    ".bazelrc": "Bazel startup/command flags, read before any BUILD file",
    ".bazelversion": "pins bazelisk; read by bazelisk, not by a target",
    "MODULE.bazel": "the Bzlmod manifest Bazel loads before any BUILD file",
    "MODULE.bazel.lock": "resolved by Bazel itself on every fetch",
    "BUILD.bazel": "package marker: Bazel reads it, no target owns it",
}

# Paths under a directory the repo itself excludes from Bazel (parsed from
# .bazelignore) are exempt by definition; _bazelignore_patterns() supplies the
# reasons for those, so _ALLOW only carries human-written ones.

# --------------------------------------------------------------------------
# Payload expectations, re-derived from the shell sources
# --------------------------------------------------------------------------

# A data label is justified for a target when the target's own source script
# mentions one of these triggers. Same shape as tests/bats.bzl's _EXTRA_DATA:
# one module-level table, read together with the sources it describes.
_JUSTIFY: dict[str, tuple[str, ...]] = {
    "//:devcontainer": (".devcontainer", "tool-versions.env"),
    "//:fix.sh": ("fix.sh",),
    "//:mypy.ini": ("mypy.ini",),
    "//:pyrightconfig.json": ("pyright",),
    "//config:policy": ("config/", "resource-policy", "disk-catalog", "model-manifest"),
    "//custom_nodes:sources": ("custom_nodes",),
    "//docker:sources": ("docker/",),
    "//docker:docker-compose.yml": ("docker/docker-compose.yml",),
    "//docs:content": ("docs/generated", "docs/contribute", "docs/assets"),
    "//docs-site:sources": ("docs-site",),
    "//includes": ("includes/", "glossary"),
    "//schemas": ("schemas/",),
    "//scripts:ci_install_lint_tools": ("install-lint-tools",),
    "//scripts:ci_publish_pages_tree": ("publish-pages-tree",),
    "//scripts:doc_sources": (
        "lib/common.sh",
        "lib/paths.sh",
        "lib/safety.sh",
        "lib/models.sh",
        "lib/compose.sh",
        "lib/occupancy.sh",
        "utilities/",
    ),
    "//scripts:lib/check_tool.sh": ("check_tool",),
    "//scripts:utilities": ("utilities/",),
    "//scripts:validate": ("validate.sh", "scripts/validate"),
    "//studio-ui:sources": ("studio-ui",),
    "//tests:fixtures": ("tests/fixtures", "fixtures/"),
    "//tests:js_files": ("tests/js",),
    "//tests:requirements.txt": ("requirements.txt",),
    "//tools:blender": ("tools/blender", "blender_host"),
    "//workflows:lab_graphs": ("workflows/_lab", "shorts/"),
    # Same-package literals: the runner sources or reads these by name.
    "//tests:.coveragerc": ("coveragerc",),
    "//tests:repo_root.sh": ("repo_root.sh", "tests_repo_root"),
    "//tests:bats_runner.sh": ("bats_runner.sh",),
}

# The payload contract: target -> (source script, labels its data must carry).
# Same shape as tests/bats.bzl's _EXTRA_DATA: one module-level table read next
# to the sources it describes. Three ways to drift, all fatal:
#
#   missing     - BUILD dropped a label this table requires
#   stale       - BUILD declares a label neither this table nor the script mentions
#   unsupported - this table requires a label the script no longer mentions
#
# The undeclared direction is table-driven rather than text-scraped on purpose:
# these gates read the checkout through realpath (no-sandbox), so a path
# appearing in a script can mean "it reads it", "it formats it", or "it only
# mentions it in a comment". _JUSTIFY still supplies the text cross-check, which
# is what turns the table from a copy of the BUILD files into a guard.
_PAYLOAD: dict[str, tuple[str, tuple[str, ...]]] = {
    "//:setup-host": (
        "scripts/setup-host.sh",
        ("//:devcontainer", "//scripts:doc_sources", "//tests:requirements.txt"),
    ),
    "//docker:compose_config": (
        "docker/compose_config_test.sh",
        ("//docker:docker-compose.yml", "//docker:sources", "//scripts:lib/check_tool.sh"),
    ),
    "//lints:buildifier": ("lints/buildifier_check.sh", ("//scripts:lib/check_tool.sh",)),
    "//lints:mypy": (
        "lints/run_mypy.sh",
        ("//:mypy.ini", "//scripts:lib/check_tool.sh", "//tests:requirements.txt"),
    ),
    "//lints:pyright": (
        "lints/run_pyright.sh",
        ("//:pyrightconfig.json", "//scripts:lib/check_tool.sh", "//tests:requirements.txt"),
    ),
    "//lints:shell": (
        "lints/run_shellcheck.sh",
        ("//:fix.sh", "//scripts:doc_sources", "//scripts:lib/check_tool.sh"),
    ),
    "//lints:shfmt": ("lints/run_shfmt.sh", ("//scripts:lib/check_tool.sh",)),
    "//scripts:manage": (
        "scripts/manage.sh",
        ("//config:policy", "//docker:sources", "//scripts:doc_sources"),
    ),
    "//scripts:manage_help_test": (
        "scripts/manage.sh",
        ("//config:policy", "//docker:sources", "//scripts:doc_sources"),
    ),
    "//scripts:run-utility": ("scripts/utilities/runner.sh", ("//scripts:utilities",)),
    "//scripts:update-stack": (
        "scripts/utilities/update-stack.sh",
        ("//config:policy", "//docker:sources", "//scripts:doc_sources"),
    ),
    "//scripts:validate": (
        "scripts/validate.sh",
        ("//scripts:ci_check_only.sh", "//scripts:lib/paths.sh"),
    ),
    "//tests:js": (
        "tests/run_js.sh",
        (
            "//custom_nodes:sources",
            "//scripts:doc_sources",
            "//tests:js_files",
            "//tests:repo_root.sh",
        ),
    ),
    "//tests:pytest": (
        "tests/run_pytest.sh",
        (
            "//custom_nodes:sources",
            "//docker:sources",
            "//schemas",
            "//scripts:doc_sources",
            "//studio-ui:sources",
            "//tests:.coveragerc",
            "//tests:fixtures",
            "//tests:python_tests",
            "//tests:repo_root.sh",
            "//tests:requirements.txt",
            "//tools:blender",
        ),
    ),
    "//tests:shell_inventory": (
        "tests/shell_inventory.sh",
        ("//scripts:doc_sources", "//tests:repo_root.sh"),
    ),
    "//tests:typecheck": (
        "tests/typecheck.sh",
        ("//scripts:doc_sources", "//tests:repo_root.sh", "//tests:requirements.txt"),
    ),
}

# Labels a required payload or a declared payload that the script text never
# mentions, each with the reason. Filling this in is a real decision: it says
# "this runfiles entry is correct even though the source never names the path".
_ALLOW_DATA: dict[str, dict[str, str]] = {
    "//:setup-host": {
        "//:devcontainer": "setup-host.sh takes every version pin from "
        ".devcontainer/tool-versions.env through SETUP_HOST_VERSIONS_FILE, so "
        "the pin file is a payload without appearing as a path literal",
    },
    "//lints:shell": {
        "//:fix.sh": "the shellcheck gate is paired with //:fix, which formats "
        "with the same tool set; it is carried so a failing gate can be fixed",
        "//scripts:doc_sources": "shellcheck walks every first-party shell "
        "file, which is exactly the tree this filegroup carries",
    },
    "//scripts:manage": {
        "//config:policy": "the resource policy, disk catalog, and model "
        "manifest are read by scripts/lib/disk_catalog.py and model_manifest.py "
        "through the repo root, so no literal in manage.sh names them",
    },
    "//scripts:manage_help_test": {
        "//config:policy": "same payload as //scripts:manage: the policy files "
        "are reached through the scripts/lib helpers manage.sh sources",
    },
    "//scripts:validate": {
        "//scripts:ci_check_only.sh": "validate.sh execs it under CI through "
        "${ROOT}/scripts/ci_check_only.sh, built from a variable rather than a "
        "literal the trigger table can see",
        "//scripts:lib/paths.sh": "sourced by validate.sh through a helper, not "
        "by a path literal",
    },
    "//tests:js": {
        "//scripts:doc_sources": "scripts/manage.sh in runfiles is the marker "
        "tests_repo_root resolves the checkout from; the marker lives in the "
        "sourced repo_root.sh, so run_js.sh never names it",
    },
    "//tests:pytest": {
        "//schemas": "the schema-contract cases in tests/python load the house "
        "and shot schemas through the disk-catalog helpers",
        "//tests:fixtures": "pytest collects tests/python, whose cases open "
        "tests/fixtures by relative path; the runner never names it",
        "//tests:python_tests": "pytest's target directory, passed as the "
        "positional argument tests/python rather than as a label-shaped string",
        "//tests:requirements.txt": "the pinned tool set this gate needs; named "
        "only in the install hint the runner prints when an import fails",
        "//scripts:doc_sources": "coverage runs over scripts/lib and the runner "
        "resolves the checkout through the manage.sh marker in runfiles",
    },
    "//tests:shell_inventory": {
        "//scripts:doc_sources": "the inventory walks scripts/**/*.sh, which is "
        "what this filegroup carries, through grep over the checkout",
    },
    "//tests:typecheck": {
        "//tests:requirements.txt": "the pinned pyright/mypy set; named only "
        "in the two install hints the runner prints",
        "//scripts:doc_sources": "the checked set covers scripts/lib, and the "
        "runner resolves the checkout through the manage.sh marker in runfiles",
    },
}

# --------------------------------------------------------------------------
# Suite coverage
# --------------------------------------------------------------------------

# package -> suites that may claim its test targets. A test target in one of
# these packages that no listed suite names is an orphan and fails the guard.
_COVERING_SUITES: dict[str, list[str]] = {
    "": ["//:test-all", "//:test", "//:test-fast", "//:lint"],
    "docs": ["//:test", "//:test-all"],
    "docs-site": ["//docs-site:suite", "//:test-all"],
    "lints": ["//lints:shell_lint", "//lints:python", "//:test-all"],
    "scripts": ["//:test-fast", "//:test-all"],
    "tests": ["//tests:bats", "//:test-fast", "//:test-all"],
}

_TEST_RULES = ("sh_test", "py_test")
_MACRO_SUITE = "bats"


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------


class Rule:
    """One BUILD-file call: a rule, a macro, or a module-level binding."""

    def __init__(self, kind: str, pkg: str) -> None:
        self.kind = kind
        self.pkg = pkg
        self.name = ""
        self.attrs: dict[str, list[str]] = {}
        self.globs: dict[str, list[str]] = {}

    @property
    def label(self) -> str:
        return f"//{self.pkg}:{self.name}" if self.pkg else f"//:{self.name}"


def _literal(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _collect(
    value: ast.AST | None,
    files: list[str],
    globs: list[str],
    bindings: dict[str, tuple[list[str], list[str]]] | None = None,
    depth: int = 0,
) -> None:
    """Flatten a srcs/data expression into literal paths and glob patterns.

    Handles the shapes this repo's BUILD files use: a string, a list or tuple
    of either, ``+`` of such expressions, ``glob([...])``, and a reference to a
    module-level ``_FOO = [...]`` binding (which is how the root BUILD file
    builds ``_TEST_FAST`` and docs builds ``_DOCS_COMMON_DATA``).
    """
    if value is None or depth > 8:
        return
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        files.append(value.value)
    elif isinstance(value, ast.Name) and bindings is not None:
        shared = bindings.get(value.id)
        if shared is not None:
            files.extend(shared[0])
            globs.extend(shared[1])
    elif isinstance(value, (ast.List, ast.Tuple, ast.Set)):
        for element in value.elts:
            _collect(element, files, globs, bindings, depth + 1)
    elif isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add):
        _collect(value.left, files, globs, bindings, depth + 1)
        _collect(value.right, files, globs, bindings, depth + 1)
    elif isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
        if value.func.id == "glob" and value.args:
            for element in getattr(value.args[0], "elts", []):
                pattern = _literal(element)
                if pattern is not None:
                    globs.append(pattern)
        elif value.func.id == "select":
            for keyword in value.keywords:
                _collect(keyword.value, files, globs, bindings, depth + 1)
    elif isinstance(value, ast.Dict):
        # env = {"K": "1"} contributes the key; select({...}) contributes both.
        for key, item in zip(value.keys, value.values):
            _collect(key, files, globs, bindings, depth + 1)
            _collect(item, files, globs, bindings, depth + 1)
    elif isinstance(value, ast.Starred):
        _collect(value.value, files, globs, bindings, depth + 1)


def _rule_from_call(
    call: ast.Call,
    pkg: str,
    bindings: dict[str, tuple[list[str], list[str]]],
) -> Rule | None:
    if not isinstance(call.func, ast.Name):
        return None
    rule = Rule(kind=call.func.id, pkg=pkg)
    positional: list[str] = []
    positional_globs: list[str] = []
    for arg in call.args:
        _collect(arg, positional, positional_globs, bindings)
    if positional:
        rule.attrs["_args"] = positional
    if positional_globs:
        rule.globs["_args"] = positional_globs
    for keyword in call.keywords:
        if keyword.arg is None:
            continue
        files: list[str] = []
        globs: list[str] = []
        _collect(keyword.value, files, globs, bindings)
        if keyword.arg == "name":
            rule.name = files[0] if files else ""
        rule.attrs[keyword.arg] = files
        if globs:
            rule.globs[keyword.arg] = globs
    if not rule.name and call.args:
        rule.name = _literal(call.args[0]) or ""
    return rule


def parse_build(source: str, pkg: str) -> list[Rule]:
    """Parse a BUILD file into rules plus the module-level lists it defines."""
    tree = ast.parse(source, filename=f"//{pkg}:BUILD.bazel")
    bindings: dict[str, tuple[list[str], list[str]]] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id.startswith("_"):
                files: list[str] = []
                globs: list[str] = []
                _collect(node.value, files, globs, bindings)
                bindings[target.id] = (files, globs)
    rules: list[Rule] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            rule = _rule_from_call(node, pkg, bindings)
            if rule is not None:
                rules.append(rule)
    for name, (files, globs) in bindings.items():
        binding = Rule(kind="_binding", pkg=pkg)
        binding.name = name
        binding.attrs["value"] = list(files)
        if globs:
            binding.globs["value"] = list(globs)
        rules.append(binding)
    return rules


# --------------------------------------------------------------------------
# Bazel glob semantics
# --------------------------------------------------------------------------


def _segment_regex(segment: str) -> str:
    if not ("*" in segment or "?" in segment):
        return re.escape(segment)
    out: list[str] = []
    index = 0
    while index < len(segment):
        char = segment[index]
        if char == "*":
            out.append("[^/]*")
        elif char == "?":
            out.append("[^/]")
        elif char == "[":
            close = segment.find("]", index)
            if close < 0:
                out.append(re.escape(char))
            else:
                out.append(segment[index : close + 1])
                index = close
        else:
            out.append(re.escape(char))
        index += 1
    return r"(?!\.)" + "".join(out)


def glob_regex(pattern: str) -> re.Pattern[str]:
    """Translate one Bazel glob pattern into a regex over a package path."""
    segments = [_segment_regex(seg) if seg != "**" else "\x00" for seg in pattern.split("/")]
    body = "/".join(segments)
    body = body.replace("/\x00/", "/(?:[^/.][^/]*/)*")
    body = body.replace("\x00/", "(?:[^/.][^/]*/)*")
    body = body.replace("/\x00", "(?:/.+)?")
    body = body.replace("\x00", ".+")
    return re.compile(f"^{body}$")


def _hidden_is_allowed(pattern: str, relpath: str) -> bool:
    """Bazel globs never match a dotfile unless the name is spelled out."""
    spelled = set(pattern.split("/"))
    for segment in relpath.split("/"):
        if segment.startswith(".") and segment not in spelled:
            return False
    return True


def _crosses_package(candidate: str, sub_packages: set[str]) -> bool:
    """True when a strict ancestor directory of the match is its own package."""
    parts = candidate.split("/")[:-1]
    for depth in range(1, len(parts) + 1):
        if "/".join(parts[:depth]) in sub_packages:
            return True
    return False


# --------------------------------------------------------------------------
# Repo IO
# --------------------------------------------------------------------------


def repo_root() -> Path:
    """The checkout root, resolved through runfiles symlinks under bazel test."""
    here = Path(__file__).resolve()
    for candidate in (here.parent.parent, Path.cwd()):
        if (candidate / "MODULE.bazel").is_file():
            return candidate
    raise SystemExit(f"bazel_deps: cannot locate MODULE.bazel from {here}")


def tracked_files(root: Path) -> list[str]:
    """The paths `git ls-files` reports, relative to ``root``."""
    proc = subprocess.run(
        ["git", "-C", str(root), "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(line for line in proc.stdout.splitlines() if line)


def bazelignore_patterns(root: Path) -> dict[str, str]:
    """Exempted prefixes from .bazelignore, mapped to the reason for each."""
    path = root / ".bazelignore"
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if entry and not entry.startswith("#"):
            out[entry] = f"excluded by .bazelignore ({entry})"
    return out


def _is_ignored(relpath: str, ignores: Iterable[str]) -> bool:
    for entry in ignores:
        cleaned = entry.rstrip("/")
        if not cleaned:
            continue
        if relpath == cleaned or relpath.startswith(cleaned + "/"):
            return True
        if any(char in cleaned for char in "*?["):
            if glob_regex(cleaned).match(relpath):
                return True
            tail = cleaned[3:] if cleaned.startswith("**/") else cleaned
            if tail and glob_regex(tail).match(relpath.rsplit("/", 1)[-1]):
                return True
    return False


def build_files(root: Path) -> dict[str, str]:
    """Every BUILD.bazel in the checkout, keyed by package ("" is the root)."""
    out: dict[str, str] = {}
    for path in sorted(root.rglob("BUILD.bazel")):
        rel = path.relative_to(root).as_posix()
        if _is_ignored(rel, (".git", "bazel-out", "bazel-bin", "bazel-testlogs")):
            continue
        pkg = Path(rel).parent.as_posix()
        out["" if pkg == "." else pkg] = path.read_text(encoding="utf-8")
    return out


# --------------------------------------------------------------------------
# Check 1: ownership
# --------------------------------------------------------------------------


def _safe_parse(source: str, pkg: str, problems: list[str] | None = None) -> list[Rule]:
    """parse_build with a reported failure instead of a traceback.

    A BUILD file this guard cannot read is a hard finding: Bazel itself would
    refuse it too, and silently mapping nothing from it is the failure mode the
    whole module exists to prevent.
    """
    try:
        return parse_build(source, pkg)
    except SyntaxError as exc:
        if problems is not None:
            problems.append(f"//{pkg}:BUILD.bazel: unparseable ({exc.msg})")
        return []


def label_to_path(label: str, pkg: str) -> str | None:
    """Resolve a BUILD-file label to a checkout-relative path, or None."""
    if label.startswith("@"):
        return None
    if label.startswith("//"):
        head, separator, tail = label.partition(":")
        base = head[2:]
        if base == "visibility":
            return None
        if base == "":
            return tail if separator and tail else None
        return f"{base}/{tail}" if tail else f"{base}/{base.rsplit('/', 1)[-1]}"
    stripped = label[1:] if label.startswith(":") else label
    return f"{pkg}/{stripped}" if pkg else stripped


def owned_paths(rules: Sequence[Rule], tracked: Sequence[str], ignores: Iterable[str]) -> set[str]:
    """Every tracked path some BUILD file names, via a literal or a glob."""
    tracked_set = set(tracked)
    packages = {rule.pkg for rule in rules} | {""}
    owned: set[str] = set()
    for rule in rules:
        for values in rule.attrs.values():
            for value in values:
                resolved = label_to_path(value, rule.pkg)
                if resolved is not None and resolved in tracked_set:
                    owned.add(resolved)
        for patterns in rule.globs.values():
            for pattern in patterns:
                prefix = f"{rule.pkg}/" if rule.pkg else ""
                for candidate in tracked_set:
                    if _is_ignored(candidate, ignores):
                        continue
                    if not candidate.startswith(prefix):
                        continue
                    relative = candidate[len(prefix) :]
                    if _crosses_package(candidate, packages - {rule.pkg}):
                        continue
                    if glob_regex(pattern).match(relative) and _hidden_is_allowed(pattern, relative):
                        owned.add(candidate)
    return owned


def unowned_files(
    tracked: Sequence[str],
    owned: set[str],
    allow: dict[str, str],
    ignores: Iterable[str],
) -> list[str]:
    """Tracked paths no BUILD file names and no exemption covers."""
    ignored = list(ignores)
    return [
        path
        for path in tracked
        if path not in owned
        and not _is_ignored(path, ignored)
        and path not in allow
        and path.rsplit("/", 1)[-1] not in allow
    ]


def ownership_report(root: Path) -> list[str]:
    """Unmapped tracked files, each with the reason it would need to be exempt."""
    tracked = tracked_files(root)
    ignores = bazelignore_patterns(root)
    problems: list[str] = []
    files = build_files(root)
    rules = [rule for pkg, text in files.items() for rule in _safe_parse(text, pkg, problems)]
    owned = owned_paths(rules, tracked, ignores)
    return problems + [
        f"{path}: named by no BUILD file (not exempted by _ALLOW or .bazelignore)"
        for path in unowned_files(tracked, owned, _ALLOW, ignores)
    ]


# --------------------------------------------------------------------------
# Check 2: payload
# --------------------------------------------------------------------------


def derive_payload(source: str) -> set[str]:
    """The labels the text of a script's source justifies as runfiles."""
    lowered = source.lower()
    return {
        label
        for label, triggers in _JUSTIFY.items()
        if any(trigger.lower() in lowered for trigger in triggers)
    }


def payload_violations(
    required: Iterable[str],
    declared: Iterable[str],
    mentioned: Iterable[str],
    allow_extra: Iterable[str] = (),
) -> tuple[list[str], list[str], list[str]]:
    """Compare one target's contract, its BUILD data, and its script text.

    Globals: none.
    Arguments:
      required - labels the payload contract demands
      declared - labels the BUILD file's data attribute carries
      mentioned - labels the target's source text mentions
      allow_extra - labels exempted from the mention requirement, with reasons
    Outputs:
      None (pure).
    Returns:
      (missing, stale, unsupported) label lists: dropped from BUILD, present in
      BUILD without a reason, and required but no longer read by the script.
    """
    required_set, declared_set = set(required), set(declared)
    allowed = set(mentioned) | set(allow_extra)
    missing = sorted(required_set - declared_set)
    stale = sorted(declared_set - required_set - allowed)
    unsupported = sorted(required_set - allowed)
    return missing, stale, unsupported


def _canon(label: str, pkg: str) -> str:
    """Spell a data entry the way _JUSTIFY spells it: //pkg:name or //:name."""
    if label.startswith("@"):
        return label
    if label.startswith("//"):
        return label
    if label.startswith(":"):
        return f"//{pkg}:{label[1:]}"
    return f"//{pkg}:{label}"


def payload_report(root: Path) -> list[str]:
    """Drift lines for every target in _PAYLOAD."""
    problems: list[str] = []
    rules = _rules_by_label(build_files(root), problems)
    for label, (script, required) in sorted(_PAYLOAD.items()):
        rule = rules.get(label)
        if rule is None:
            problems.append(f"{label}: target not found in any BUILD file")
            continue
        source_path = root / script
        if not source_path.is_file():
            problems.append(f"{label}: contract names a missing source {script}")
            continue
        declared = [_canon(entry, rule.pkg) for entry in rule.attrs.get("data", [])]
        allow = _ALLOW_DATA.get(label, {})
        missing, stale, unsupported = payload_violations(
            required,
            declared,
            derive_payload(source_path.read_text(encoding="utf-8")),
            allow,
        )
        problems.extend(f"{label}: undeclared payload {item}" for item in missing)
        problems.extend(f"{label}: stale payload {item} (no reason in _ALLOW_DATA)" for item in stale)
        problems.extend(f"{label}: unsupported requirement {item} (not in {script})" for item in unsupported)
    return problems


def _rules_by_label(
    files: dict[str, str], problems: list[str] | None = None
) -> dict[str, Rule]:
    rules: dict[str, Rule] = {}
    for pkg, text in files.items():
        for rule in _safe_parse(text, pkg, problems):
            if rule.name and not rule.kind.startswith("_"):
                rules[rule.label] = rule
    return rules


# --------------------------------------------------------------------------
# Check 3: suite coverage
# --------------------------------------------------------------------------


def _absolute(member: str, pkg: str) -> str:
    if member.startswith("//"):
        return member
    if member.startswith(":"):
        return f"//{pkg}:{member[1:]}"
    return f"//{pkg}:{member}"


def expand_suite(
    label: str,
    rules: dict[str, Rule],
    universe: Iterable[str] = (),
    depth: int = 0,
) -> set[str]:
    """Flatten a test_suite label down to the test targets it names.

    Globals: none.
    Arguments:
      label - the suite label, e.g. //:test-fast
      rules - parsed rules by label, macro suites included
      universe - labels known to be test targets, for members a macro generated
      depth - recursion guard
    Outputs:
      None (pure).
    Returns:
      The set of test target labels the suite reaches.
    """
    if depth > 8:
        return set()
    known = set(universe)
    rule = rules.get(label)
    if rule is None:
        return {label} if label in known else set()
    if rule.kind in _TEST_RULES:
        return {label}
    out: set[str] = set()
    for member in rule.attrs.get("tests", []):
        out |= expand_suite(_absolute(member, rule.pkg), rules, known, depth + 1)
    return out


def bats_generated_tests(pkg: str, rule: Rule, tracked: Sequence[str]) -> set[str]:
    """Target names the bats_file_tests macro creates, re-derived from its glob."""
    out: set[str] = set()
    prefix = f"{pkg}/" if pkg else ""
    for pattern in rule.globs.get("srcs", []):
        for candidate in tracked:
            if not candidate.startswith(prefix):
                continue
            relative = candidate[len(prefix) :]
            if glob_regex(pattern).match(relative):
                stem = relative.rsplit("/", 1)[-1].removesuffix(".bats").replace("-", "_")
                out.add(f"//{pkg}:bats_{stem}_test")
    return out


def all_test_targets(
    files: dict[str, str], tracked: Sequence[str], problems: list[str] | None = None
) -> set[str]:
    """Every test target in the repo, including macro-generated BATS suites."""
    tests: set[str] = set()
    for pkg, text in files.items():
        for rule in _safe_parse(text, pkg, problems):
            if rule.kind in _TEST_RULES:
                tests.add(rule.label)
            elif rule.kind == "bats_file_tests":
                tests |= bats_generated_tests(pkg, rule, tracked)
    return tests


def _macro_suites(
    files: dict[str, str], tracked: Sequence[str], problems: list[str] | None = None
) -> dict[str, Rule]:
    """Synthesise the test_suite a macro declares inside its .bzl file.

    bats_file_tests creates `bats_<stem>_test` targets and a `bats` suite in
    tests/bats.bzl, so neither appears in a BUILD file. The names are re-derived
    from the macro's own glob argument, the same way the macro derives them.
    """
    out: dict[str, Rule] = {}
    for pkg, text in files.items():
        for rule in _safe_parse(text, pkg, problems):
            if rule.kind != "bats_file_tests":
                continue
            suite = Rule(kind="test_suite", pkg=pkg)
            suite.name = _MACRO_SUITE
            suite.attrs["tests"] = sorted(bats_generated_tests(pkg, rule, tracked))
            out[suite.label] = suite
    return out


def uncovered_tests(files: dict[str, str], tracked: Sequence[str]) -> list[str]:
    """Test targets that no suite in _COVERING_SUITES claims."""
    problems: list[str] = []
    rules = _rules_by_label(files, problems)
    rules.update(_macro_suites(files, tracked, problems))
    universe = all_test_targets(files, tracked, problems)
    claimed: set[str] = set()
    for suites in _COVERING_SUITES.values():
        for suite in suites:
            claimed |= expand_suite(suite, rules, universe)
    return problems + sorted(universe - claimed)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    """Command line entry point.

    Globals: none.
    Arguments:
      argv - optional argument vector: --root plus the --check-* selectors.
    Outputs:
      One violation per line on stdout, then a count summary.
    Returns:
      0 when every selected check is clean, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description="Bazel file-mapping guards")
    parser.add_argument("--root", default=None, help="checkout root (default: this file's parent)")
    parser.add_argument("--check-ownership", action="store_true")
    parser.add_argument("--check-payloads", action="store_true")
    parser.add_argument("--check-suites", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else repo_root()
    run_all = not (args.check_ownership or args.check_payloads or args.check_suites)
    files = build_files(root)
    tracked = tracked_files(root)

    problems: list[str] = []
    if run_all or args.check_ownership:
        problems += ownership_report(root)
    if run_all or args.check_payloads:
        problems += payload_report(root)
    if run_all or args.check_suites:
        problems += uncovered_tests(files, tracked)

    for line in problems:
        print(line)
    print(f"bazel_deps: {len(problems)} violation(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
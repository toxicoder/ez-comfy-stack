"""Inventory gate: broad types stay out of first-party production code.

The checkers (``mypy.ini``, ``pyrightconfig.json``) decide whether a file
typechecks. This gate decides something they cannot: whether a file was
*allowed* to be loose. ``mypy.ini`` is the single registry of declared
``Any`` boundaries, and these tests read it rather than duplicating it, so
a boundary can only exist where a human wrote a reason.

Scope is the production tree (the same roots the 100% coverage gate walks).
``tests/python`` is exempt from the ``Any`` ban because a fake that mirrors
a Comfy graph or a torch tensor is honest about being a stand-in, but it is
still held to the ban on ``Callable[..., Any]`` and on un-coded
``# type: ignore``.
"""

from __future__ import annotations

import ast
import configparser
import re
import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parents[2]
"""Repository root this gate walks."""

PRODUCTION_ROOTS: tuple[str, ...] = (
    "custom_nodes",
    "docker",
    "docs",
    "scripts/lib",
    "studio-ui",
    "tools",
)
"""Roots that must hold the strict rule (mirrors tests/run_pytest.sh)."""

CHECKED_TEST_ROOT = "tests/python"
"""Test tree held to the syntax rules but not to the ``Any`` ban."""

MYPY_PATH_ROOTS: tuple[str, ...] = (
    "custom_nodes",
    "docker",
    "docker/pythonpath",
    "scripts/lib",
    "studio-ui",
    "tests/python",
    "docs",
    "tools",
)
"""Source roots mypy resolves module names against (keep in sync with
``mypy.ini`` - the checker picks the deepest matching root)."""

PRODUCTION_ANY_BUDGET = 380
"""Highest number of explicit ``Any`` tokens allowed across production code.

The number is a ratchet: it only ever goes down, and it goes down by
deleting a boundary or narrowing a type. It goes up only with a review
conversation and a paragraph of justification in the PR.

Every token above the declared boundaries lives in a ``DEBT`` module listed at
the bottom of ``mypy.ini`` - code that should hold a ``TypedDict`` or the
:mod:`ez_common.json_value` vocabulary and does not yet. The budget is what
makes that ledger shrink instead of settle.
"""

DEBT_MODULE_BUDGET = 23
"""Highest number of ``DEBT`` modules ``mypy.ini`` may exempt from the ban.

A debt section is a to-do with a name on it, and a to-do list that only grows
is how a policy dies. Adding a module here needs the same PR conversation as
raising :data:`PRODUCTION_ANY_BUDGET`.
"""

PRODUCTION_CAST_BUDGET = 144
"""Highest number of ``cast()`` calls allowed across production code.

``Any`` is banned, so a JSON or dependency-injection payload has to be narrowed
somewhere, and the 100% line-coverage gate rules out the ``isinstance`` guard
that would do it honestly. ``cast`` is the sanctioned trade at that seam - and
this ratchet is what keeps it a boundary rather than a habit. It only ever goes
down.
"""

MYPY_INI = REPO / "mypy.ini"
"""The checker config that doubles as the boundary registry."""

TYPING_DOC = REPO / "docs/contribute/typing.md"
"""The contributor page that must name every declared boundary."""

BARE_TYPE_IGNORE_RE = re.compile(r"#\s*type:\s*ignore\s*(\[\])?\s*$")
"""A ``# type: ignore`` that names no error code."""

ANY_TOKEN_RE = re.compile(r"(?<!\w)Any(?!\w)")
"""Matches the ``Any`` name in code and inside a quoted annotation.

Tokenize splits ``typing.Any`` into ``typing`` / ``.`` / ``Any``, so the bare
name is what both spellings reduce to; the same pattern run over a string
token catches an annotation written as text.
"""


def _python_files(root: str) -> list[Path]:
    """List first-party Python files under one root.

    Args:
        root: Repository-relative directory.

    Returns:
        Sorted ``.py`` paths, ``__pycache__`` skipped.
    """
    base = REPO / root
    return sorted(
        path
        for path in base.rglob("*.py")
        if "__pycache__" not in path.parts and "node_modules" not in path.parts
    )


def _module_names(path: Path) -> set[str]:
    """Resolve the module names mypy could assign to a file.

    mypy names a module from the deepest ``mypy_path`` root that contains it,
    so ``docker/pythonpath/sitecustomize.py`` is ``sitecustomize`` and
    ``tools/blender/workbench_passes.py`` is ``blender.workbench_passes``
    (``tools`` is a root). The gate has to agree with the checker exactly: a
    pattern that matches only the repo-relative spelling looks like a declared
    boundary while mypy still reports the ``Any``.

    Args:
        path: File inside the repository.

    Returns:
        Dotted module-name candidates, the checker's own name first.
    """
    relative = path.relative_to(REPO)
    stem = ".".join(relative.with_suffix("").parts)
    deepest: str | None = None
    for root in MYPY_PATH_ROOTS:
        prefix = Path(root).parts
        if relative.parts[: len(prefix)] == prefix:
            candidate = ".".join(relative.parts[len(prefix) :]).removesuffix(".py")
            if deepest is None or len(candidate) < len(deepest):
                deepest = candidate
    names: set[str] = {stem if deepest is None else deepest}
    if relative.name == "__init__.py":
        names.add(".".join(relative.parts[:-1]))
        if deepest is not None:
            names.add(deepest.removesuffix(".__init__"))
    return names


def _section_patterns(section: str, key: str, value: str) -> set[str]:
    """Read module patterns out of ``mypy.ini`` sections that set one key.

    Args:
        section: Only sections whose name starts with this prefix are read.
        key: The option that marks the section.
        value: The option value that counts as a match (case-insensitive).

    Returns:
        Every comma-separated module pattern in a matching section.
    """
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(MYPY_INI, encoding="utf-8")
    patterns: set[str] = set()
    for name in parser.sections():
        if not name.startswith(section):
            continue
        if parser.get(name, key, fallback="").strip().lower() != value.lower():
            continue
        for part in name.removeprefix(section).split(","):
            cleaned = part.strip()
            if cleaned:
                patterns.add(cleaned)
    return patterns


def _boundary_patterns() -> set[str]:
    """Read the declared ``Any`` boundaries out of ``mypy.ini``.

    A boundary is a third-party edge the repo cannot type (torch, bpy, Comfy's
    widget registry). It carries a written reason and a row on the contributor
    page.

    Returns:
        Every module pattern whose section sets ``disallow_any_explicit`` to
        false.
    """
    return _section_patterns("mypy-", "disallow_any_explicit", "False")


def _debt_patterns() -> set[str]:
    """Read the ``DEBT`` modules out of ``mypy.ini``.

    Debt is first-party code that should be tight and is not yet. It is
    deliberately keyed on a different option than a boundary so a to-do can
    never be laundered into a documented exemption.

    Returns:
        Every module pattern whose section disables ``explicit-any``.
    """
    return _section_patterns("mypy-", "disable_error_code", "explicit-any")


def _matches(path: Path, patterns: Iterable[str]) -> bool:
    """Return whether a file's module names hit any of the patterns.

    Args:
        path: Production file to classify.
        patterns: Module patterns from ``mypy.ini``.

    Returns:
        True when any pattern matches one of the file's module names.
    """
    names = _module_names(path)
    return any(fnmatch(name, pattern) for name in names for pattern in patterns)


def _is_boundary(path: Path, patterns: Iterable[str]) -> bool:
    """Return whether a file sits inside a declared boundary.

    Args:
        path: Production file to classify.
        patterns: Module patterns from ``mypy.ini``.

    Returns:
        True when any pattern matches one of the file's module names.
    """
    return _matches(path, patterns)


def _is_debt(path: Path, patterns: Iterable[str]) -> bool:
    """Return whether a file is listed as type debt.

    Args:
        path: Production file to classify.
        patterns: Debt module patterns from ``mypy.ini``.

    Returns:
        True when any pattern matches one of the file's module names.
    """
    return _matches(path, patterns)


def _annotation_strings(tree: ast.AST) -> list[tuple[int, str]]:
    """Collect annotations that were written as text.

    Args:
        tree: Parsed module.

    Returns:
        ``(line, text)`` for each quoted annotation and each string assigned
        to a :data:`typing.TypeAlias`, which are the two places a type can
        hide from an AST walk over names.
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                found.append((node.value.lineno, node.value.value))
        children = (
            getattr(node, "annotation", None),
            getattr(node, "returns", None),
        )
        for child in children:
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                found.append((child.lineno, child.value))
        if isinstance(node, ast.arguments):
            for arg in [*node.args, *node.posonlyargs, *node.kwonlyargs]:
                if isinstance(arg.annotation, ast.Constant) and isinstance(
                    arg.annotation.value, str
                ):
                    found.append((arg.annotation.lineno, arg.annotation.value))
    return found


def _refs_in_annotation(text: str) -> bool:
    """Return whether a quoted annotation names ``Any``.

    Args:
        text: The annotation source, e.g. ``"dict[str, Any]"``.

    Returns:
        True when the parsed annotation references the name.
    """
    try:
        parsed = ast.parse(text, mode="eval")
    except SyntaxError:
        return bool(ANY_TOKEN_RE.search(text))
    return any(
        (isinstance(node, ast.Name) and node.id == "Any")
        or (isinstance(node, ast.Attribute) and node.attr == "Any")
        for node in ast.walk(parsed)
    )


def _cast_lines(path: Path) -> list[int]:
    """Find lines that assert a type with ``cast()``.

    Both spellings count: ``cast(...)`` imported from ``typing`` and
    ``typing.cast(...)``.

    Args:
        path: File to inspect.

    Returns:
        Line numbers (1-based) holding a ``cast`` call.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
        if name == "cast":
            lines.add(node.lineno)
    return sorted(lines)


def _callable_any_lines(path: Path) -> list[int]:
    """Find lines that write ``Callable[..., Any]``.

    The scan is over the syntax tree, not the text: a comment or a docstring
    that names the banned spelling (this file's own repair message does) is
    prose about the rule, not a use of it.

    Args:
        path: File to inspect.

    Returns:
        Line numbers (1-based) holding a ``Callable`` subscription whose
        parameter list is ``...`` and whose result mentions ``Any``.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript):
            continue
        base = node.value
        name = base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
        if name != "Callable" or not isinstance(node.slice, ast.Tuple):
            continue
        elements = node.slice.elts
        if not elements or not _is_ellipsis(elements[0]):
            continue
        if any(_refs_any(item) for item in elements[1:]):
            lines.add(node.lineno)
    return sorted(lines)


def _is_ellipsis(node: ast.expr) -> bool:
    """Return whether a node is the ``...`` parameter-list marker.

    Args:
        node: A slice element of a ``Callable`` subscription.

    Returns:
        True for ``...`` (parsed as ``Constant(Ellipsis)``).
    """
    return isinstance(node, ast.Constant) and node.value is Ellipsis


def _refs_any(node: ast.AST) -> bool:
    """Return whether a type expression names ``Any``.

    Args:
        node: A slice element of a ``Callable`` subscription.

    Returns:
        True for ``Any`` or ``typing.Any`` anywhere inside the expression.
    """
    return any(
        (isinstance(item, ast.Name) and item.id == "Any")
        or (isinstance(item, ast.Attribute) and item.attr == "Any")
        for item in ast.walk(node)
    )


def _any_lines(path: Path) -> list[int]:
    """Find lines that use ``typing.Any`` as a type.

    Name references, ``typing.Any`` attribute access, ``from typing import
    Any``, and ``Any`` written inside a quoted annotation all count. Docstring
    and comment prose about the type does not, so a boundary may still explain
    what it exempts.

    Args:
        path: File to inspect.

    Returns:
        Line numbers (1-based) holding an ``Any`` reference.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "Any":
            lines.add(node.lineno)
        elif isinstance(node, ast.Attribute) and node.attr == "Any":
            lines.add(node.lineno)
        elif isinstance(node, ast.ImportFrom):
            if any(
                alias.name == "Any" or alias.name.startswith("Any as ")
                for alias in node.names
            ):
                lines.add(node.lineno)
    for lineno, text in _annotation_strings(tree):
        if _refs_in_annotation(text):
            lines.add(lineno)
    return sorted(lines)


def _production_files() -> list[Path]:
    """Every production Python file the gate walks.

    Returns:
        Sorted paths across :data:`PRODUCTION_ROOTS`.
    """
    files: list[Path] = []
    for root in PRODUCTION_ROOTS:
        files.extend(_python_files(root))
    return files


def _checked_files() -> list[Path]:
    """Production files plus the pytest tree.

    Returns:
        Sorted paths.
    """
    return _production_files() + _python_files(CHECKED_TEST_ROOT)


def test_production_has_no_undeclared_any() -> None:
    """Only a module named in ``mypy.ini`` may mention ``Any``.

    Two registers qualify, and both are read from the file rather than
    duplicated here: a *boundary* (a third-party edge the repo cannot type) and
    a *debt* module (first-party code still owed a real type). A fresh ``Any``
    anywhere else is the exact defect this policy exists to stop, so it fails
    with the file, the line, and the repair hint.
    """
    allowed = _boundary_patterns() | _debt_patterns()
    offenders = [
        f"{path.relative_to(REPO)}:{line}"
        for path in _production_files()
        if not _is_boundary(path, allowed)
        for line in _any_lines(path)
    ]
    assert not offenders, (
        "explicit Any outside a declared boundary or debt module (see "
        "docs/contribute/typing.md; prefer a TypedDict, Literal, object, or a "
        "TYPE_CHECKING alias of the real third-party class):\n"
        + "\n".join(offenders)
    )


def test_debt_modules_stay_under_budget() -> None:
    """The debt ledger may shrink and may not grow.

    A new module in the ``DEBT`` block of ``mypy.ini`` is a new pocket of
    untyped code given a licence to stay that way, so the count is ratcheted
    next to the ``Any`` total.
    """
    patterns = _debt_patterns()
    assert len(patterns) <= DEBT_MODULE_BUDGET, (
        f"mypy.ini lists {len(patterns)} DEBT modules; the budget is "
        f"{DEBT_MODULE_BUDGET}. Narrow one module and delete its section "
        f"instead of adding to the ledger: {sorted(patterns)}"
    )


def test_production_any_count_stays_under_budget() -> None:
    """The ratchet: production ``Any`` never grows past the recorded budget."""
    total = sum(len(_any_lines(path)) for path in _production_files())
    assert total <= PRODUCTION_ANY_BUDGET, (
        f"production code carries {total} explicit Any tokens; the budget is "
        f"{PRODUCTION_ANY_BUDGET}. Narrow a type or justify the boundary in the PR."
    )


def test_production_cast_count_stays_under_budget() -> None:
    """The other half of the ratchet: production ``cast`` never grows either.

    A ``cast`` is a type asserted instead of proven, so it deserves the same
    scrutiny as an ``Any``. It is allowed where a value crosses a boundary the
    repo cannot type (parsed JSON, an injected dependency) and an ``isinstance``
    guard would be a branch no test reaches, which the coverage floor forbids.
    """
    counts = {
        str(path.relative_to(REPO)): len(_cast_lines(path))
        for path in _production_files()
        if _cast_lines(path)
    }
    total = sum(counts.values())
    assert total <= PRODUCTION_CAST_BUDGET, (
        f"production code carries {total} cast() calls; the budget is "
        f"{PRODUCTION_CAST_BUDGET}. Prove the type instead of asserting it "
        f"(TypedDict, isinstance, or a Protocol) - heaviest files first: "
        f"{sorted(counts.items(), key=lambda item: -item[1])[:5]}"
    )


def test_no_ellipsis_callable_any() -> None:
    """``Callable[..., Any]`` is banned outright, tests included.

    A callable with untyped parameters silently opts the whole signature out
    of checking; the repo already prefers a named ``Protocol``.
    """
    offenders = [
        f"{path.relative_to(REPO)}:{number}"
        for path in _checked_files()
        for number in _callable_any_lines(path)
    ]
    assert not offenders, (
        "Callable[..., Any] is banned - name the parameters or write a "
        "Protocol (docs/contribute/typing.md):\n" + "\n".join(offenders)
    )


def test_type_ignore_comments_name_a_code() -> None:
    """A bare ``# type: ignore`` can hide a future real error.

    ``warn_unused_ignores`` already reports these to mypy; asserting it here
    keeps the rule visible even on a host where mypy is not installed.
    """
    offenders = [
        f"{path.relative_to(REPO)}:{number}"
        for path in _checked_files()
        for number, text in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if BARE_TYPE_IGNORE_RE.search(text)
    ]
    assert not offenders, (
        'every "type: ignore" must name a code, e.g. '
        '"# type: ignore[no-any-return]":\n' + "\n".join(offenders)
    )


def test_every_boundary_is_documented() -> None:
    """``mypy.ini`` and the contributor page list the same boundaries."""
    page = TYPING_DOC.read_text(encoding="utf-8")
    missing = [
        pattern
        for pattern in sorted(_boundary_patterns())
        if f"`{pattern}`" not in page
    ]
    assert not missing, (
        "boundaries declared in mypy.ini but missing from "
        f"docs/contribute/typing.md: {', '.join(missing)}"
    )


def test_no_unused_boundary() -> None:
    """An exemption that no longer carries ``Any`` is dead weight.

    An empty exemption - a boundary or a debt module - quietly licenses the next
    ``Any`` in that module, so delete the section instead.
    """
    patterns = _boundary_patterns() | _debt_patterns()
    still_used: set[str] = set()
    for path in _production_files() + _python_files(CHECKED_TEST_ROOT):
        if _any_lines(path) and _is_boundary(path, patterns):
            still_used.update(_module_names(path))
    unused = sorted(
        pattern
        for pattern in patterns
        if not any(fnmatch(name, pattern) for name in still_used)
    )
    assert not unused, (
        "mypy.ini exempts these modules from the Any ban but none of them uses "
        f"Any any more: {', '.join(unused)} - delete the section"
    )


def test_shared_vocabulary_is_importable() -> None:
    """The shared type modules import at runtime without torch or numpy.

    These aliases are annotation-only, so an accidental unquoted
    ``torch.Tensor`` would break ``import ez_common`` inside Comfy. The gate
    also needs the modules imported for the coverage lane.
    """
    sys.path.insert(0, str(REPO / "custom_nodes"))
    import ez_common
    from ez_common import comfy_graph, json_value, tensors

    assert getattr(ez_common.ComfyInputTypes, "__origin__", None) is dict
    assert getattr(json_value.JsonArray, "__origin__", None) is list
    assert tensors.ImageTensor == "torch.Tensor"
    assert comfy_graph.NodeId.__supertype__ is str


def test_comfy_graph_helpers_behave() -> None:
    """The graph helpers collapse ``int`` and ``str`` ids the documented way."""
    from ez_common.comfy_graph import (
        api_link_parts,
        api_link_ref,
        as_node_id,
        ui_nodes_by_id,
    )

    assert as_node_id(7) == "7"
    assert as_node_id("12") == "12"

    graph = {
        "nodes": [
            {"id": 1, "type": "KSampler", "widgets_values": [1234, "dpmpp"]},
            {"type": "EmptyLatentImage"},
        ]
    }
    indexed = ui_nodes_by_id(graph)
    assert list(indexed) == ["1"]
    assert indexed["1"]["type"] == "KSampler"

    link = api_link_ref("3", 0)
    assert link == ["3", 0]
    assert api_link_parts(link) == ("3", 0)
    assert api_link_parts("flux-2-klein-4b.safetensors") is None
    assert api_link_parts([1, 2]) is None

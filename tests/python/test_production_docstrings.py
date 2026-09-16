"""Production Python must have Google-style docs and complete annotations.

Hermetic: stdlib AST only. Walks first-party production packages (not tests).
Enforces module/class/function docstrings, Args/Returns sections when the
signature has parameters or a non-None return, annotations on every def, and
a comment or attribute docstring on module-level constants.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_ROOTS: tuple[Path, ...] = (
    ROOT / "custom_nodes",
    ROOT / "docker",
    ROOT / "docs",
    ROOT / "scripts" / "lib",
    ROOT / "studio-ui",
    ROOT / "tools",
)
SKIP_PARTS = frozenset({"__pycache__", "site", ".venv", "venv"})
SKIP_DUNDER_DOC = True


def _is_dunder(name: str) -> bool:
    """True for ``__dunder__`` names.

    Args:
        name: Identifier.

    Returns:
        Whether the name is a dunder.
    """
    return name.startswith("__") and name.endswith("__")


def _iter_production_py() -> list[Path]:
    """List first-party production Python files.

    Returns:
        Sorted paths under the production roots.
    """
    files: list[Path] = []
    for root in PRODUCTION_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            files.append(path)
    return sorted(files)


def _ann_none(node: ast.expr | None) -> bool:
    """True when the annotation is missing or ``None``.

    Args:
        node: AST annotation.

    Returns:
        Whether a ``Returns:`` section is not required.
    """
    if node is None:
        return True
    if isinstance(node, ast.Constant) and node.value is None:
        return True
    return False


def _has_params(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True when the function takes arguments besides ``self`` / ``cls``.

    Args:
        node: Function AST.

    Returns:
        Whether an ``Args:`` section is required.
    """
    args = list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs)
    if node.args.vararg is not None:
        args.append(node.args.vararg)
    if node.args.kwarg is not None:
        args.append(node.args.kwarg)
    return any(arg.arg not in {"self", "cls"} for arg in args)


def _untyped_params(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Names of parameters missing annotations (not ``self`` / ``cls``).

    Args:
        node: Function AST.

    Returns:
        Untyped parameter names.
    """
    args: list[ast.arg] = list(node.args.posonlyargs) + list(node.args.args)
    args.extend(node.args.kwonlyargs)
    if node.args.vararg is not None:
        args.append(node.args.vararg)
    if node.args.kwarg is not None:
        args.append(node.args.kwarg)
    return [arg.arg for arg in args if arg.arg not in {"self", "cls"} and arg.annotation is None]


def _doc_ok_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[str]:
    """Docstring richness problems for one function.

    Args:
        node: Function AST.

    Returns:
        Human-readable problems (empty if fine).
    """
    if SKIP_DUNDER_DOC and _is_dunder(node.name):
        return []
    doc = ast.get_docstring(node)
    problems: list[str] = []
    if not doc:
        problems.append("missing docstring")
        return problems
    if _has_params(node) and "Args:" not in doc:
        problems.append("docstring missing Args:")
    if not _ann_none(node.returns) and node.name != "__init__" and "Returns:" not in doc:
        problems.append("docstring missing Returns:")
    return problems


def _constant_names(node: ast.AST) -> list[str]:
    """UPPER_SNAKE names bound by a module-level assignment.

    Args:
        node: Assign or AnnAssign.

    Returns:
        Constant identifiers.
    """
    names: list[str] = []
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                names.append(target.id)
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        if node.target.id.isupper():
            names.append(node.target.id)
    return names


def _line_is_comment(lines: list[str], lineno: int) -> bool:
    """True if the 1-based source line is a ``#`` comment.

    Args:
        lines: File lines (no newlines).
        lineno: 1-based line number.

    Returns:
        Whether that line is a comment.
    """
    if lineno < 1 or lineno > len(lines):
        return False
    return lines[lineno - 1].lstrip().startswith("#")


def _constant_block_starts(
    body: list[ast.stmt],
) -> dict[int, int]:
    """Map assignment index to the first index of its contiguous constant block.

    Args:
        body: Module body.

    Returns:
        Index → block-start index.
    """
    starts: dict[int, int] = {}
    block_start: int | None = None
    for i, stmt in enumerate(body):
        if _constant_names(stmt):
            if block_start is None:
                block_start = i
            starts[i] = block_start
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            if isinstance(stmt.value.value, str) and block_start is not None:
                continue
        block_start = None
    return starts


def _scan_constant_body(
    body: list[ast.stmt],
    *,
    rel: Path,
    lines: list[str],
    found: list[str],
    qual: str,
) -> None:
    """Append constant-documentation gaps for one statement list.

    Args:
        body: Module or class body.
        rel: Path relative to the repo root.
        lines: Source lines.
        found: Violation accumulator.
        qual: ``<module>`` or class name prefix for messages.
    """
    block_starts = _constant_block_starts(body)
    for i, stmt in enumerate(body):
        names = _constant_names(stmt)
        if not names:
            continue
        nxt = i + 1
        if nxt < len(body):
            follow = body[nxt]
            if isinstance(follow, ast.Expr) and isinstance(follow.value, ast.Constant):
                if isinstance(follow.value.value, str):
                    continue
        start = block_starts.get(i, i)
        start_stmt = body[start]
        start_line = int(getattr(start_stmt, "lineno", 1))
        if _line_is_comment(lines, start_line - 1):
            continue
        probe = start_line - 1
        while probe >= 1 and not lines[probe - 1].strip():
            probe -= 1
        if _line_is_comment(lines, probe):
            continue
        prefix = f"{qual}." if qual else ""
        for name in names:
            found.append(
                f"{rel}:{start_line}: {prefix}{name}: constant missing comment or docstring"
            )


def scan_file(path: Path) -> list[str]:
    """Return inventory violations for one production module.

    Args:
        path: Python file.

    Returns:
        ``path:line: symbol: problem`` strings.
    """
    rel = path.relative_to(ROOT)
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [f"{rel}:1: <module>: parse error: {exc}"]
    lines = source.splitlines()
    found: list[str] = []
    if not ast.get_docstring(tree):
        found.append(f"{rel}:1: <module>: missing module docstring")

    _scan_constant_body(tree.body, rel=rel, lines=lines, found=found, qual="")

    class Visitor(ast.NodeVisitor):
        """Collect class/function docstring and annotation gaps."""

        def __init__(self) -> None:
            """Start with no enclosing class."""
            self.class_stack: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            """Record class docstring gaps and walk members.

            Args:
                node: Class AST.
            """
            qual = ".".join([*self.class_stack, node.name])
            if not ast.get_docstring(node):
                found.append(f"{rel}:{node.lineno}: {qual}: missing class docstring")
            _scan_constant_body(
                node.body, rel=rel, lines=lines, found=found, qual=qual
            )
            self.class_stack.append(node.name)
            self.generic_visit(node)
            self.class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            """Record function docstring and annotation gaps.

            Args:
                node: Function AST.
            """
            self._handle(node)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            """Record async function docstring and annotation gaps.

            Args:
                node: Async function AST.
            """
            self._handle(node)
            self.generic_visit(node)

        def _handle(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            """Append violations for one function.

            Args:
                node: Function AST.
            """
            qual = ".".join([*self.class_stack, node.name])
            loc = f"{rel}:{node.lineno}: {qual}"
            for problem in _doc_ok_function(node):
                found.append(f"{loc}: {problem}")
            untyped = _untyped_params(node)
            if untyped:
                found.append(f"{loc}: untyped args {untyped}")
            if (
                node.returns is None
                and node.name != "__init__"
                and not _is_dunder(node.name)
            ):
                found.append(f"{loc}: missing return annotation")

    Visitor().visit(tree)
    return found


def all_violations() -> list[str]:
    """Scan every production Python file.

    Returns:
        Sorted violation strings.
    """
    found: list[str] = []
    for path in _iter_production_py():
        found.extend(scan_file(path))
    return found


def test_production_python_has_docs_and_annotations() -> None:
    """Fail when production Python is missing docs or type hints."""
    found = all_violations()
    if not found:
        return
    preview = "\n".join(found[:80])
    extra = "" if len(found) <= 80 else f"\n... {len(found) - 80} more ({len(found)} total)"
    raise AssertionError(f"{len(found)} production docstring/type gaps:\n{preview}{extra}")


if __name__ == "__main__":
    rows = all_violations()
    print(f"{len(rows)} violations")
    for row in rows:
        print(row)

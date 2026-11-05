"""Hermetic auditor: the 100% coverage gate is real, wired, and cannot narrow itself.

The Python floor is only as strong as the script that enforces it. Three ways it
went quiet before: a host without pytest-cov ran the suite unmeasured and called
it green, the aggregate gate was a binary so `bazelisk test //:coverage` built it
without running it, and a package could join the tree without ever joining the
measured scope. Each is pinned here so it fails as a test rather than as a
silently green lane.

Does not invoke bazelisk or coverage.py: it reads the committed runner, config,
and BUILD files, so CI and laptops agree without a cold start. The measured
verdict itself belongs to //tests:pytest.
"""

from __future__ import annotations

import configparser
import os
import re
from pathlib import Path
from typing import Final

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests" / "run_pytest.sh"
AGGREGATE = ROOT / "tests" / "coverage.sh"
COVERAGE_CONFIG = ROOT / "tests" / ".coveragerc"
TESTS_BUILD = ROOT / "tests" / "BUILD.bazel"
ROOT_BUILD = ROOT / "BUILD.bazel"
DOCS_SITE_RUNNER = ROOT / "docs-site" / "run_python_test.sh"
DOCS_SITE_BUILD = ROOT / "docs-site" / "BUILD.bazel"

# The docs-site production modules each suite has to measure.
DOCS_SITE_MODULES: Final[tuple[str, ...]] = (
    "scripts/audit_mdx_hazards.py",
    "scripts/codemod_mkdocs_to_mdx.py",
    "scripts/gen_nav.py",
    "scripts/visual_linux_image.py",
)

# Trees that hold first-party Python measured by some gate other than
# //tests:pytest, each with the target that measures it. A new top-level tree
# with production Python has to land here with a real target name, or join
# COV_SCOPE in tests/run_pytest.sh; it cannot arrive unmeasured by omission.
GATED_ELSEWHERE: Final[dict[str, str]] = {
    "docs-site": "//docs-site:nav_test, //docs-site:codemod_test, "
    "//docs-site:audit_hazards_test, //docs-site:visual_tooling_test",
    # The harness measures production Python; gating the harness on itself would
    # ask test modules for statements only reachable under a debugger.
    "tests": "//tests:pytest is this suite; tests/python/test_bazel_deps.py and "
    "test_bazel_docs.py cover the two harness modules",
}

# Not first-party code, or not a checkout artifact a gate can reason about.
_SKIP_DIRS: Final[frozenset[str]] = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".venv",
        "__pycache__",
        "coverage",
        "node_modules",
        "output",
        "site-packages",
    }
)

_RULE_RE = re.compile(r"^([a-z_]+)\((.*?)^\)", re.MULTILINE | re.DOTALL)


def _cov_scope() -> list[str]:
    """The measured trees, read from the array the runner builds --cov from."""
    block = RUNNER.read_text(encoding="utf-8").split("COV_SCOPE=(", 1)[1].split(")", 1)[0]
    return [line.strip() for line in block.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def _production_python() -> list[Path]:
    """First-party modules a coverage gate should be measuring, repo-relative."""
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS and not d.startswith("bazel-"))
        for name in sorted(filenames):
            if not name.endswith(".py") or name.startswith("test_") or name == "conftest.py":
                continue
            found.append(Path(dirpath, name).relative_to(ROOT))
    return found


def _is_measured(relpath: Path, scope: list[str]) -> bool:
    """Whether a module falls inside a tree some gate measures."""
    if relpath.parts[0] in GATED_ELSEWHERE:
        return True
    return any(str(relpath) == entry or str(relpath).startswith(f"{entry}/") for entry in scope)


def _omit_patterns() -> list[str]:
    """Every pattern tests/.coveragerc leaves unmeasured."""
    parser = configparser.ConfigParser()
    parser.read(COVERAGE_CONFIG, encoding="utf-8")
    raw = parser.get("run", "omit", fallback="")
    return [part.strip() for line in raw.splitlines() for part in line.split(",") if part.strip()]


def test_pytest_gate_never_runs_unmeasured() -> None:
    """A missing pytest or pytest-cov fails the target instead of skipping the floor."""
    runner = RUNNER.read_text(encoding="utf-8")
    assert runner.count("python3 -m pytest") == 1, "a second pytest invocation is an unmeasured fallback path"
    assert "--cov-fail-under=100" in runner
    assert "--cov-report=term-missing" in runner
    assert "require_module pytest" in runner
    assert "require_module pytest_cov" in runner
    assert "tests/requirements.txt" in runner, "the repair hint must name the pinned requirement file"
    assert "! python3 -c" in runner, "the import probe has to be a hard check, not an optional one"


def test_cov_scope_is_the_single_source_of_the_measured_trees() -> None:
    """--cov comes from COV_SCOPE, so no tree can be dropped from one place only."""
    runner = RUNNER.read_text(encoding="utf-8")
    assert '--cov="${pkg}"' in runner
    for tree in _cov_scope():
        assert f"--cov={tree}" not in runner, f"{tree} is hard-coded as well as listed in COV_SCOPE"
    assert "--cov-config=tests/.coveragerc" in runner


def test_every_first_party_package_is_measured_by_a_gate() -> None:
    """No production module sits outside every coverage gate in the repo."""
    scope = _cov_scope()
    assert scope, "COV_SCOPE is empty - the gate measures nothing"
    unmeasured = sorted(str(p) for p in _production_python() if not _is_measured(p, scope))
    assert unmeasured == [], f"unmeasured first-party Python (join COV_SCOPE or GATED_ELSEWHERE): {unmeasured}"


def test_gated_elsewhere_entries_still_hold_python() -> None:
    """A tree that moved or died loses its exemption instead of keeping it."""
    scope = _cov_scope()
    production = _production_python()
    for top, gate in GATED_ELSEWHERE.items():
        assert (ROOT / top).is_dir(), f"GATED_ELSEWHERE names {top}, which is gone"
        assert gate.startswith("//"), f"{top} must name Bazel targets, not scripts: {gate}"
        assert top not in scope, f"{top} is gated twice - drop it from GATED_ELSEWHERE or COV_SCOPE"
        assert any(p.parts[0] == top for p in production), f"{top} holds no production Python any more"


def test_measured_trees_exist_and_hold_production_python() -> None:
    """A renamed or emptied tree would let the gate report a flattering vacuum."""
    production = [str(p) for p in _production_python()]
    for tree in _cov_scope():
        assert (ROOT / tree).is_dir(), f"COV_SCOPE names {tree}, which is absent from the tree"
        assert any(path == tree or path.startswith(f"{tree}/") for path in production), (
            f"COV_SCOPE names {tree}, which holds no production Python"
        )


def test_coveragerc_omits_only_test_modules() -> None:
    """An omit rule naming production code is how the floor gets hollowed out."""
    omits = _omit_patterns()
    assert omits, "tests/.coveragerc has no omit list; keep the exemptions explicit"
    for pattern in omits:
        stem = Path(pattern.replace("*", "x")).name
        assert stem.startswith("test_"), f"tests/.coveragerc omits {pattern}, which is not a test module"


def _rules(path: Path) -> list[tuple[str, str]]:
    """Top-level ``(rule kind, body)`` pairs in a BUILD file."""
    return _RULE_RE.findall(path.read_text(encoding="utf-8"))


def test_aggregate_coverage_target_is_a_test_rule() -> None:
    """`bazelisk test //:coverage` has to be a test rule or it builds and skips."""
    covered = [(kind, body) for kind, body in _rules(TESTS_BUILD) if 'name = "coverage"' in body]
    kinds = [kind for kind, _ in covered]
    assert kinds == ["sh_test"], f"//tests:coverage must be an sh_test to gate anything, found {kinds}"
    block = covered[0][1]
    assert "coverage.sh" in block
    assert "manual" in block, "the sweep has to stay out of wildcard runs that double the suite"
    assert 'timeout = "long"' in block, "it chains pytest, mypy, pyright, the inventory, and BATS"

    exposed = [(kind, body) for kind, body in _rules(ROOT_BUILD) if 'name = "coverage"' in body]
    assert [kind for kind, _ in exposed] == ["test_suite"], (
        f"//:coverage must be a test_suite so `bazelisk test` runs it, found {[k for k, _ in exposed]}"
    )
    assert '"//tests:coverage"' in exposed[0][1], "//:coverage no longer claims the sweep"


def test_aggregate_still_chains_every_gate() -> None:
    """The sweep keeps invoking the real gates rather than a cheaper stand-in."""
    aggregate = AGGREGATE.read_text(encoding="utf-8")
    for gate in ("tests/run_pytest.sh", "tests/typecheck.sh", "tests/shell_inventory.sh", "tests/bats"):
        assert gate in aggregate, f"//:coverage no longer runs {gate}"
    assert "tests_repo_root" in aggregate, "the sweep must resolve the checkout, not bazel-bin"


def test_docs_site_python_is_gated_too() -> None:
    """The docs-site scripts are production code and carry the same floor."""
    runner = DOCS_SITE_RUNNER.read_text(encoding="utf-8")
    assert "--cov-fail-under=100" in runner
    assert "pytest_cov" in runner, "a missing plugin has to fail the target, not skip the floor"
    assert "TEST_TMPDIR" in runner, "coverage data cannot be written into a read-only sandbox"
    build = DOCS_SITE_BUILD.read_text(encoding="utf-8")
    for module in DOCS_SITE_MODULES:
        assert f"--cov={module}" in build, f"{module} is measured by no docs-site target"

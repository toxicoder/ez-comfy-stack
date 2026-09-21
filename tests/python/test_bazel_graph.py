"""Hermetic auditor: first-party trees are Bazel packages with BUILD coverage.

Does not invoke bazelisk. Reads committed BUILD files and source paths so CI
and laptops agree without a Bazel cold start.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_PACKAGES = (
    "config",
    "custom_nodes",
    "docker",
    "docs",
    "docs-site",
    "includes",
    "lints",
    "schemas",
    "scripts",
    "studio-ui",
    "tests",
    "tools",
    "workflows",
)


def test_required_packages_have_build_files() -> None:
    """Every first-party package directory ships BUILD.bazel."""
    missing = [name for name in REQUIRED_PACKAGES if not (ROOT / name / "BUILD.bazel").is_file()]
    assert missing == []


def test_schemas_build_globs_yaml_and_json() -> None:
    """schemas/ is a Bazel package whose glob covers the committed schema files."""
    text = (ROOT / "schemas" / "BUILD.bazel").read_text(encoding="utf-8")
    assert "glob(" in text
    assert 'name = "schemas"' in text
    files = sorted(p.name for p in (ROOT / "schemas").iterdir() if p.suffix in {".yaml", ".json"})
    assert files
    assert "asset.yaml" in files
    assert "house_layout.yaml" in files


def test_tests_package_declares_python_and_fixture_filegroups() -> None:
    """pytest's Bazel target lists python tests, fixtures, and production sources."""
    text = (ROOT / "tests" / "BUILD.bazel").read_text(encoding="utf-8")
    assert 'name = "python_tests"' in text
    assert 'name = "fixtures"' in text
    assert "//tests:python_tests" in text or ":python_tests" in text
    assert "//schemas" in text
    assert "//custom_nodes:sources" in text
    assert "//docker:sources" in text
    pytest_block = text.split('name = "pytest"', 1)[1].split("sh_test(", 1)[0]
    assert ":python_tests" in pytest_block
    assert ":fixtures" in pytest_block
    assert "//schemas" in pytest_block


def test_root_build_exposes_first_party_srcs() -> None:
    """Root graph rollup includes schemas, tests, and the Makefile shim."""
    text = (ROOT / "BUILD.bazel").read_text(encoding="utf-8")
    assert 'name = "first_party_srcs"' in text
    assert "//schemas" in text
    assert "//tests:python_tests" in text
    assert "Makefile" in text
    assert 'name = "vscode"' in text
    assert ":vscode" in text


def test_pytest_runner_uses_xdist_when_installed() -> None:
    """Local and CI pytest share one coverage process; xdist parallelizes it."""
    runner = (ROOT / "tests" / "run_pytest.sh").read_text(encoding="utf-8")
    assert "-n auto" in runner
    assert "--dist worksteal" in runner
    req = (ROOT / "tests" / "requirements.txt").read_text(encoding="utf-8")
    assert "pytest-xdist==" in req


def test_medium_bats_suites_use_moderate_timeout() -> None:
    """size medium must not keep timeout short (60s) or CI load flakes look like product bugs."""
    text = (ROOT / "tests" / "bats.bzl").read_text(encoding="utf-8")
    assert "bats/lib_unit.bats" in text
    assert 'timeout = "moderate" if src in _MEDIUM else "short"' in text

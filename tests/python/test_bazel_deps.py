r"""Guards for the Bazel file mapping, driven by tests/bazel_deps.py.

Three claims hold this repo together and each has a failing case here, in both
directions, so the guard cannot pass by checking nothing:

- every tracked file is named by a BUILD file (or exempted with a reason);
- every script target carries the payload its contract requires, and no more;
- every test target belongs to a suite.

The pure functions take their inputs as arguments, so the drift cases are
constructed rather than found in the tree; the repo-level tests then assert the
same functions report nothing against the real checkout.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parents[1]
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

import bazel_deps  # noqa: E402  (import after the sys.path insert above)

ROOT = _TESTS_DIR.parent


class TestOwnership:
    """A tracked file nobody names is invisible to every target."""

    def test_unowned_files_lists_only_unnamed_paths(self) -> None:
        owned = {"BUILD.bazel", "a.py", "pkg/b.py"}
        tracked = ["BUILD.bazel", "a.py", "pkg/b.py", "pkg/orphan.md"]
        assert bazel_deps.unowned_files(tracked, owned, {}, []) == ["pkg/orphan.md"]

    def test_allow_entry_exempts_a_path(self) -> None:
        allow = {"pkg/orphan.md": "operator note, never a build input"}
        assert bazel_deps.unowned_files(["pkg/orphan.md"], set(), allow, []) == []

    def test_allow_entry_exempts_a_basename(self) -> None:
        allow = {"BUILD.bazel": "package marker"}
        tracked = ["BUILD.bazel", "pkg/BUILD.bazel"]
        assert bazel_deps.unowned_files(tracked, set(), allow, []) == []

    def test_bazelignore_entry_exempts_a_directory(self) -> None:
        tracked = ["workflows/_user/.gitkeep", "workflows/_user/README.md"]
        ignores = ["workflows/_user/"]
        assert bazel_deps.unowned_files(tracked, set(), {}, ignores) == []

    def test_bazelignore_pattern_exempts_matching_files(self) -> None:
        tracked = ["pkg/__pycache__/x.pyc", "pkg/keep.py"]
        ignores = ["**/__pycache__/", "*.py[cod]"]
        assert bazel_deps.unowned_files(tracked, set(), {}, ignores) == ["pkg/keep.py"]

    def test_the_checkout_has_no_unmapped_file(self) -> None:
        assert bazel_deps.ownership_report(ROOT) == []


class TestGlobMatching:
    """The parser must read a glob the way Bazel does."""

    @pytest.mark.parametrize(
        ("pattern", "path"),
        [
            ("*.yaml", "asset.yaml"),
            ("**/*.py", "a.py"),
            ("**/*.py", "pkg/sub/a.py"),
            ("js/**", "js/a.mjs"),
            ("js/**", "js/deep/a.mjs"),
            ("lib/*.sh", "lib/common.sh"),
            ("*", "Makefile"),
        ],
    )
    def test_matching_pairs(self, pattern: str, path: str) -> None:
        assert bazel_deps.glob_regex(pattern).match(path)
        assert bazel_deps._hidden_is_allowed(pattern, path)

    @pytest.mark.parametrize(
        ("pattern", "path"),
        [
            ("*.yaml", "pkg/asset.yaml"),
            ("lib/*.sh", "lib/deep/common.sh"),
            ("js/**", "js/.hidden.mjs"),
            ("*", ".env"),
            ("**/*.py", "a.py.bak"),
        ],
    )
    def test_non_matching_pairs(self, pattern: str, path: str) -> None:
        assert not (
            bazel_deps.glob_regex(pattern).match(path)
            and bazel_deps._hidden_is_allowed(pattern, path)
        )

    def test_a_glob_owns_what_it_matches(self) -> None:
        rule = bazel_deps.Rule("filegroup", "pkg")
        rule.name = "sources"
        rule.globs["srcs"] = ["**/*.css"]
        tracked = ["pkg/a.css", "pkg/b.js", "pkg/BUILD.bazel"]
        assert bazel_deps.owned_paths([rule], tracked, []) == {"pkg/a.css"}

    def test_a_glob_stops_at_a_subpackage(self) -> None:
        outer = bazel_deps.Rule("filegroup", "")
        outer.name = "everything"
        outer.globs["srcs"] = ["**/*.py"]
        inner = bazel_deps.Rule("filegroup", "sub")
        inner.name = "own"
        tracked = ["top.py", "sub/inside.py"]
        assert bazel_deps.owned_paths([outer, inner], tracked, []) == {"top.py"}

    def test_a_literal_owns_what_it_names(self) -> None:
        rule = bazel_deps.Rule("filegroup", "pkg")
        rule.name = "meta"
        rule.attrs["srcs"] = [":dotfile", ".gitignore", "//other:thing.txt"]
        tracked = ["pkg/.gitignore", "other/thing.txt", "pkg/extra.md"]
        assert bazel_deps.owned_paths([rule], tracked, []) == {
            "pkg/.gitignore",
            "other/thing.txt",
        }


class TestLabels:
    """Label spelling must not change what a file is called."""

    @pytest.mark.parametrize(
        ("label", "pkg", "expected"),
        [
            ("a.py", "pkg", "pkg/a.py"),
            (":a.py", "pkg", "pkg/a.py"),
            ("sub/a.py", "pkg", "pkg/sub/a.py"),
            ("//other:a.py", "pkg", "other/a.py"),
            ("//other", "pkg", "other/other"),
            ("//:a.py", "pkg", "a.py"),
            ("@repo//:a.py", "pkg", None),
            ("//visibility:public", "pkg", None),
        ],
    )
    def test_label_to_path(self, label: str, pkg: str, expected: str | None) -> None:
        assert bazel_deps.label_to_path(label, pkg) == expected

    def test_canon_spells_every_entry_as_a_label(self) -> None:
        assert bazel_deps._canon(":js_files", "tests") == "//tests:js_files"
        assert bazel_deps._canon("repo_root.sh", "tests") == "//tests:repo_root.sh"
        assert bazel_deps._canon("//docker:sources", "tests") == "//docker:sources"


class TestPayload:
    """Drift in either direction is a defect, not a warning."""

    def test_clean_contract_reports_nothing(self) -> None:
        cases = bazel_deps.payload_violations(
            required=["//docker:sources"],
            declared=["//docker:sources"],
            mentioned={"//docker:sources"},
        )
        assert cases == ([], [], [])

    def test_missing_direction_fires_when_build_drops_a_label(self) -> None:
        _missing, stale, unsupported = bazel_deps.payload_violations(
            required=["//docker:sources"],
            declared=[],
            mentioned={"//docker:sources"},
        )
        assert stale == [] and unsupported == []

    def test_missing_direction_reports_the_dropped_label(self) -> None:
        missing, _stale, _unsupported = bazel_deps.payload_violations(
            required=["//docker:sources"],
            declared=[],
            mentioned={"//docker:sources"},
        )
        assert missing == ["//docker:sources"]

    def test_stale_direction_fires_for_payload_nobody_reads(self) -> None:
        _missing, stale, _unsupported = bazel_deps.payload_violations(
            required=[],
            declared=["//workflows:lab_graphs"],
            mentioned=set(),
        )
        assert stale == ["//workflows:lab_graphs"]

    def test_stale_direction_accepts_a_written_reason(self) -> None:
        cases = bazel_deps.payload_violations(
            required=[],
            declared=["//workflows:lab_graphs"],
            mentioned=set(),
            allow_extra=["//workflows:lab_graphs"],
        )
        assert cases == ([], [], [])

    def test_unsupported_direction_fires_when_the_script_stops_reading_it(self) -> None:
        _missing, _stale, unsupported = bazel_deps.payload_violations(
            required=["//scripts:doc_sources"],
            declared=["//scripts:doc_sources"],
            mentioned=set(),
        )
        assert unsupported == ["//scripts:doc_sources"]

    def test_derive_payload_reads_triggers_from_the_source(self) -> None:
        assert "//tests:js_files" in bazel_deps.derive_payload(
            'node --test "tests/js/*.test.mjs"\n'
        )
        assert "//tests:js_files" not in bazel_deps.derive_payload("echo hello\n")

    def test_the_checkout_contract_holds(self) -> None:
        assert bazel_deps.payload_report(ROOT) == []


class TestSuites:
    """A test no suite names is a test that never runs."""

    def _rules(self) -> dict[str, bazel_deps.Rule]:
        suite = bazel_deps.Rule("test_suite", "")
        suite.name = "test-fast"
        suite.attrs["tests"] = ["//tests:js", "//tests:bats_x_test"]
        js = bazel_deps.Rule("sh_test", "tests")
        js.name = "js"
        return {"//:test-fast": suite, "//tests:js": js}

    def test_a_target_in_a_suite_is_claimed(self) -> None:
        claimed = bazel_deps.expand_suite(
            "//:test-fast", self._rules(), {"//tests:js", "//tests:bats_x_test"}
        )
        assert claimed == {"//tests:js", "//tests:bats_x_test"}

    def test_a_member_a_macro_generated_is_still_claimed(self) -> None:
        universe = {"//tests:js", "//tests:bats_x_test"}
        assert "//tests:bats_x_test" in bazel_deps.expand_suite(
            "//:test-fast", self._rules(), universe
        )

    def test_a_member_that_is_not_a_test_target_is_not_claimed(self) -> None:
        assert bazel_deps.expand_suite("//:test-fast", self._rules(), set()) == {
            "//tests:js"
        }

    def test_the_checkout_has_no_orphan_test(self) -> None:
        files = bazel_deps.build_files(ROOT)
        tracked = bazel_deps.tracked_files(ROOT)
        assert bazel_deps.uncovered_tests(files, tracked) == []

    def test_bats_macro_targets_are_rederived_from_its_glob(self) -> None:
        macro = bazel_deps.Rule("bats_file_tests", "tests")
        macro.globs["srcs"] = ["bats/*.bats"]
        generated = bazel_deps.bats_generated_tests(
            "tests", macro, ["tests/bats/lib_unit.bats", "tests/bats_runner.sh"]
        )
        assert generated == {"//tests:bats_lib_unit_test"}


class TestRepoWiring:
    """The guard itself is wired into the build it guards."""

    def _root_rules(self) -> dict[str, bazel_deps.Rule]:
        return bazel_deps._rules_by_label(bazel_deps.build_files(ROOT))

    def test_the_guard_is_a_py_test_in_the_tests_package(self) -> None:
        rule = self._root_rules().get("//tests:owned_files_check")
        assert rule is not None
        assert rule.kind == "py_test"

    def test_the_guard_runs_in_the_fast_suite(self) -> None:
        files = bazel_deps.build_files(ROOT)
        tracked = bazel_deps.tracked_files(ROOT)
        claimed = bazel_deps.expand_suite(
            "//:test-fast",
            {**bazel_deps._rules_by_label(files), **bazel_deps._macro_suites(files, tracked)},
            bazel_deps.all_test_targets(files, tracked),
        )
        assert "//tests:owned_files_check" in claimed

    def test_the_js_suite_declares_the_mjs_files(self) -> None:
        rule = self._root_rules().get("//tests:js")
        assert rule is not None
        assert ":js_files" in rule.attrs.get("data", [])
        js = bazel_deps.build_files(ROOT)["tests"]
        assert '"js/**"' in js

    def test_the_lint_gates_run_strict_under_bazel(self) -> None:
        for name in ("shell", "shfmt", "buildifier", "pyright", "mypy"):
            rule = self._root_rules()[f"//lints:{name}"]
            assert "REQUIRE_LINT_TOOLS" in rule.attrs.get("env", []), name
            assert rule.attrs.get("size"), name
            assert rule.attrs.get("timeout"), name
            assert rule.attrs.get("visibility"), name

    def test_no_target_is_named_all(self) -> None:
        assert not [label for label in self._root_rules() if label.endswith(":all")]

    def test_the_checkout_root_is_this_repo(self) -> None:
        assert bazel_deps.repo_root() == ROOT

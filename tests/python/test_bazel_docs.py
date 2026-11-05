r"""Guards for the Bazel-is-the-ingress doc check, driven by tests/bazel_docs.py.

The guard fails a checkout when a reader could copy a repo script out of a
committed file while a Bazel target does the same job. Each claim here has a
failing case in both directions, so the guard cannot pass by matching nothing:

- command position is read from fenced blocks, backticked spans, script
  comments, printed strings, and heredoc bodies, and from nothing else;
- a script reference with a target is a violation, and the host-mutating verbs
  plus the named exemptions are not;
- the suggested target carries the sub-command, so the advice is copyable.

The pure functions take their inputs as arguments, so the drift cases are
constructed rather than found in the tree; the repo-level tests then assert the
same functions report nothing against the real checkout.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parents[1]
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

import bazel_docs  # noqa: E402  (import after the sys.path insert above)

ROOT = _TESTS_DIR.parent


class TestCommandPositions:
    """Only text a reader could copy counts; code that runs does not."""

    def test_fenced_block_lines_are_commands(self) -> None:
        text = "prose\n\n```bash\n./scripts/manage.sh doctor\n```\n"
        assert bazel_docs.command_positions(text) == [(4, "./scripts/manage.sh doctor")]

    def test_backticked_span_is_a_command(self) -> None:
        text = "Run `./scripts/manage.sh doctor` now.\n"
        assert bazel_docs.command_positions(text) == [(1, "./scripts/manage.sh doctor")]

    def test_prose_path_without_a_span_is_not_a_command(self) -> None:
        assert bazel_docs.command_positions("scripts/manage.sh routes operator actions.\n") == []

    def test_nested_fence_markers_do_not_leak(self) -> None:
        text = "```\n./scripts/manage.sh doctor\n```\nafter ```\n"
        assert bazel_docs.command_positions(text) == [(2, "./scripts/manage.sh doctor")]

    def test_script_comment_body_is_a_command(self) -> None:
        text = "#!/usr/bin/env bash\n#   ./scripts/manage.sh doctor\nset -e\n"
        commands = [command for _, command in bazel_docs.command_positions(text, code=True)]
        assert "./scripts/manage.sh doctor" in commands
        assert "#!/usr/bin/env bash" not in " ".join(commands)

    def test_comment_body_is_ignored_when_not_a_code_file(self) -> None:
        text = "#   ./scripts/manage.sh doctor\n"
        assert bazel_docs.command_positions(text, code=False) == []

    def test_printed_string_is_a_command(self) -> None:
        text = '  err "run ./scripts/manage.sh doctor first"\n'
        assert bazel_docs.command_positions(text, code=True) == [
            (1, "run ./scripts/manage.sh doctor first")
        ]

    def test_executed_code_is_not_read_as_text(self) -> None:
        text = 'bash "${REPO_ROOT}/scripts/utilities/download-llm.sh" link\n'
        assert bazel_docs.command_positions(text, code=True) == []

    def test_heredoc_body_is_a_command(self) -> None:
        text = "usage() {\n  cat <<'EOF'\nUsage:\n  ./scripts/manage.sh doctor\nEOF\n}\n"
        commands = [command for _, command in bazel_docs.command_positions(text, code=True)]
        assert "./scripts/manage.sh doctor" in commands

    def test_a_backtick_run_with_no_command_is_dropped(self) -> None:
        assert bazel_docs.command_positions("after ```\n") == []

    def test_two_spans_on_one_line_are_both_read(self) -> None:
        text = "run `./scripts/manage.sh doctor` then `./scripts/manage.sh status`\n"
        assert bazel_docs.command_positions(text) == [
            (1, "./scripts/manage.sh doctor"),
            (1, "./scripts/manage.sh status"),
        ]

    def test_blank_lines_are_skipped(self) -> None:
        assert bazel_docs.command_positions("```\n\n\n```\n") == []


class TestIsHostVerb:
    """The verbs that need Docker, sudo, the GPU, or $HOME keep the raw door."""

    @pytest.mark.parametrize("verb", ["setup", "start", "stop", "restart", "update-stack"])
    def test_documented_host_verbs(self, verb: str) -> None:
        assert bazel_docs.is_host_verb(verb)

    @pytest.mark.parametrize("verb", ["download-models", "download-ltx", "download-3d"])
    def test_download_prefix_is_host(self, verb: str) -> None:
        assert bazel_docs.is_host_verb(verb)

    @pytest.mark.parametrize("verb", ["doctor", "status", "logs", "occupancy", ""])
    def test_read_only_verbs_are_not_host(self, verb: str) -> None:
        assert not bazel_docs.is_host_verb(verb)


class TestClassify:
    """A script command with a target is a violation, with a copyable fix."""

    def test_read_only_manage_verb_is_flagged_with_its_target(self) -> None:
        found = bazel_docs.classify("./scripts/manage.sh doctor")
        assert found == ("./scripts/manage.sh doctor", "bazelisk run //:manage -- doctor")

    def test_host_verb_is_exempt(self) -> None:
        assert bazel_docs.classify("./scripts/manage.sh start") is None
        assert bazel_docs.classify("./scripts/manage.sh download-models --limit off") is None

    def test_manage_verb_without_arguments_is_exempt_as_host(self) -> None:
        assert bazel_docs.classify("./scripts/manage.sh setup") is None

    def test_subcommand_and_flags_survive_on_a_manage_verb(self) -> None:
        found = bazel_docs.classify("./scripts/manage.sh occupancy enter klein")
        assert found is not None
        assert found[1] == "bazelisk run //:manage -- occupancy enter klein"

    def test_utility_name_and_arguments_both_survive(self) -> None:
        found = bazel_docs.classify("./scripts/utilities/asset-ls.sh --json")
        assert found is not None
        assert found[1] == "bazelisk run //scripts:run-utility -- asset-ls --json"
        assert "asset-ls --json --json" not in found[1]

    def test_bash_prefixed_utility_is_flagged(self) -> None:
        found = bazel_docs.classify("bash ./scripts/utilities/disk-wizard.sh run")
        assert found is not None
        assert found[1] == "bazelisk run //scripts:run-utility -- disk-wizard run"

    @pytest.mark.parametrize(
        ("command", "target"),
        [
            ("bash tests/run_all.sh", "bazelisk test //:test-fast"),
            ("bash tests/run_pytest.sh", "bazelisk test //tests:pytest"),
            ("bash tests/coverage.sh", "bazelisk test //:coverage"),
            ("bash tests/typecheck.sh", "bazelisk test //tests:typecheck"),
            ("bash docker/compose_config_test.sh", "bazelisk test //docker:compose_config"),
            ("python3 tests/bazel_deps.py", "bazelisk test //tests:owned_files_check"),
            ("python3 docs/generate_shell_docs.py", "bazelisk run //docs:generate_shell"),
            ("python3 docs/generate_workflow_docs.py", "bazelisk run //docs:generate_workflow"),
            ("python3 docs/generate_cinema_docs.py", "bazelisk run //docs:generate_cinema"),
            ("python3 docs/generate_audio_docs.py", "bazelisk run //docs:generate_audio"),
            ("python3 docs/generate_pages_docs.py", "bazelisk run //docs:generate"),
            ("./docs/manage-docs.sh serve", "bazelisk run //docs:serve"),
            ("./docs/manage-docs.sh build", "bazelisk run //docs:docs"),
            ("./docs/setup-docs.sh", "bazelisk run //docs-site:install"),
            ("bash scripts/everything.sh", "bazelisk run //:everything"),
            ("bash scripts/validate.sh", "bazelisk run //:validate"),
            ("bash lints/run_shellcheck.sh", "bazelisk test //:lint --test_tag_filters=manual"),
            (
                "bash docs-site/scripts/visual_linux.sh --update",
                "bazelisk run //docs-site:visual-linux",
            ),
        ],
    )
    def test_known_entry_points_map_to_their_targets(self, command: str, target: str) -> None:
        found = bazel_docs.classify(command)
        assert found is not None
        assert found[1] == target

    def test_a_bazel_command_is_never_a_violation(self) -> None:
        assert bazel_docs.classify("bazelisk test //:test-fast") is None
        assert bazel_docs.classify("bazel test //:test-fast") is None

    def test_bare_path_with_no_verb_is_a_file_reference(self) -> None:
        assert bazel_docs.classify("scripts/manage.sh") is None
        assert bazel_docs.classify("./scripts/manage.sh") is None

    def test_a_placeholder_verb_documents_a_shape_not_a_command(self) -> None:
        assert bazel_docs.classify("./scripts/manage.sh <verb>") is None

    def test_a_download_utility_keeps_the_host_door(self) -> None:
        assert bazel_docs.classify("./scripts/utilities/download-image.sh run --tier 9b") is None

    def test_a_non_download_utility_with_no_args_is_still_flagged(self) -> None:
        found = bazel_docs.classify("./scripts/utilities/asset-ls.sh")
        assert found is not None
        assert found[1] == "bazelisk run //scripts:run-utility -- asset-ls"

    def test_a_bare_utility_path_is_a_file_reference(self) -> None:
        assert bazel_docs.classify("scripts/utilities/runner.sh may be exec'd here") is None

    def test_a_bare_builder_path_is_a_file_reference(self) -> None:
        assert bazel_docs.classify("tests/python/_build_studio_blocks.py emits it") is None

    def test_a_run_builder_path_is_flagged(self) -> None:
        found = bazel_docs.classify("python3 tests/python/_build_quality_js.py")
        assert found is not None
        assert found[1] == "bazelisk run //tests:build_quality_js"

    def test_make_is_an_ignored_documented_shim(self) -> None:
        assert bazel_docs.classify("make fmt") is None

    def test_unrelated_command_is_not_a_violation(self) -> None:
        assert bazel_docs.classify("docker compose config -q") is None
        assert bazel_docs.classify("ls -la") is None
        assert bazel_docs.classify("") is None

    def test_trailing_comment_is_not_suggested_back(self) -> None:
        found = bazel_docs.classify("./scripts/manage.sh doctor # quick")
        assert found is not None
        assert found[1] == "bazelisk run //:manage -- doctor"

    def test_whitespace_is_collapsed_in_the_suggestion(self) -> None:
        found = bazel_docs.classify("./scripts/manage.sh   status    --json")
        assert found is not None
        assert found[1] == "bazelisk run //:manage -- status --json"


class TestAllowed:
    """An exemption is a named decision, not a pattern anybody can widen."""

    def test_exact_line_is_exempt(self) -> None:
        assert bazel_docs.allowed("scripts/setup-host.sh", 5, "x") is True

    def test_bare_path_exempts_the_whole_file(self) -> None:
        assert bazel_docs.allowed("Makefile", 999, "x") is True

    def test_a_script_is_not_exempt_for_its_own_file(self) -> None:
        # manage.sh has a target, so its own usage header still has to name it.
        assert bazel_docs.allowed("scripts/manage.sh", 15, "./scripts/manage.sh doctor") is False

    def test_unlisted_position_is_not_exempt(self) -> None:
        assert bazel_docs.allowed("docs/nope.mdx", 1, "x") is False


class TestViolations:
    """End to end over a constructed tree, in both directions."""

    def _write(self, root: Path, rel: str, text: str) -> str:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return rel

    def test_flags_a_command_and_carries_the_target(self, tmp_path: Path) -> None:
        rel = self._write(tmp_path, "docs/a.mdx", "```bash\n./scripts/manage.sh doctor\n```\n")
        problems = bazel_docs.violations(tmp_path, [rel])
        assert len(problems) == 1
        assert "docs/a.mdx:2" in problems[0]
        assert "bazelisk run //:manage -- doctor" in problems[0]

    def test_clean_file_reports_nothing(self, tmp_path: Path) -> None:
        rel = self._write(tmp_path, "docs/a.mdx", "```bash\nbazelisk run //:manage -- doctor\n```\n")
        assert bazel_docs.violations(tmp_path, [rel]) == []

    def test_binary_and_missing_files_are_skipped(self, tmp_path: Path) -> None:
        (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "pixel.png").write_bytes(b"\x00\xff\x01")
        problems = bazel_docs.violations(tmp_path, ["docs/pixel.png", "docs/gone.mdx"])
        assert problems == []

    def test_undecodable_file_is_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "docs"
        path.mkdir(parents=True)
        (path / "bad.mdx").write_bytes(b"\xff\xfe\x00 not utf-8")
        assert bazel_docs.violations(tmp_path, ["docs/bad.mdx"]) == []

    def test_exempt_file_is_silent(self, tmp_path: Path) -> None:
        rel = self._write(
            tmp_path, "Makefile", "```bash\n./scripts/manage.sh doctor\n```\n"
        )
        assert bazel_docs.violations(tmp_path, [rel]) == []


class TestLabGraphNotes:
    """Graph notes are operator-facing prose, so they are swept as such."""

    def _graph(self, note: str) -> dict[str, object]:
        return {
            "extra": {"lab_note": note},
            "nodes": [{"type": "Note", "widgets_values": [note]}],
        }

    def test_note_fields_are_read_from_extra_and_note_nodes(self) -> None:
        graph = self._graph("Run `./scripts/manage.sh doctor` first.")
        assert bazel_docs.lab_note_fields(graph) == [
            "Run `./scripts/manage.sh doctor` first.",
            "Run `./scripts/manage.sh doctor` first.",
        ]

    def test_a_widget_note_node_and_a_note_type_only(self) -> None:
        graph = {
            "nodes": [
                {"type": "KSampler", "widgets_values": ["./scripts/manage.sh doctor"]},
                {"type": "note", "widgets_values": ["plain prose"]},
                {"type": "Note"},
            ]
        }
        assert bazel_docs.lab_note_fields(graph) == ["plain prose"]

    def test_a_graph_note_naming_a_script_is_a_violation(self, tmp_path: Path) -> None:
        rel = "workflows/_lab/stills/x.json"
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        graph = self._graph("Then `./scripts/manage.sh doctor` and wait.")
        path.write_text(json.dumps(graph), encoding="utf-8")
        problems = bazel_docs.violations(tmp_path, [rel])
        assert any("//:manage -- doctor" in p for p in problems), problems

    def test_a_target_in_a_graph_note_is_clean(self, tmp_path: Path) -> None:
        rel = "workflows/_lab/stills/x.json"
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        graph = self._graph("Then `bazelisk run //:manage -- doctor` and wait.")
        path.write_text(json.dumps(graph), encoding="utf-8")
        assert bazel_docs.violations(tmp_path, [rel]) == []

    def test_a_host_verb_in_a_graph_note_stays_raw(self, tmp_path: Path) -> None:
        rel = "workflows/_lab/stills/x.json"
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        graph = self._graph("Warm the cache with `./scripts/manage.sh download-models`.")
        path.write_text(json.dumps(graph), encoding="utf-8")
        assert bazel_docs.violations(tmp_path, [rel]) == []

    def test_broken_and_non_object_json_are_tolerated(self, tmp_path: Path) -> None:
        (tmp_path / "workflows" / "_lab").mkdir(parents=True, exist_ok=True)
        (tmp_path / "workflows" / "_lab" / "bad.json").write_text("{nope", encoding="utf-8")
        (tmp_path / "workflows" / "_lab" / "list.json").write_text("[]", encoding="utf-8")
        paths = ["workflows/_lab/bad.json", "workflows/_lab/list.json", "workflows/_lab/gone.json"]
        assert bazel_docs.violations(tmp_path, paths) == []

    def test_a_json_outside_the_lab_tree_is_left_alone(self, tmp_path: Path) -> None:
        rel = "config/x.json"
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._graph("`./scripts/manage.sh doctor`")), encoding="utf-8")
        assert bazel_docs.lab_graph_violations(tmp_path, [rel]) == []
        assert rel not in bazel_docs.candidate_files([rel])


class TestDocstringPositions:
    """A docstring is a page: pydoc and the editor tooltip show it verbatim."""

    def test_module_docstring_lines_are_read(self) -> None:
        text = '"""Run me.\n\n  python3 docs/generate_shell_docs.py\n"""\n'
        assert (3, "python3 docs/generate_shell_docs.py") in bazel_docs.docstring_positions(text)

    def test_function_docstring_lines_are_read(self) -> None:
        text = 'def f() -> None:\n    """Doc.\n\n      ./scripts/manage.sh doctor\n    """\n    return None\n'
        assert (4, "./scripts/manage.sh doctor") in bazel_docs.docstring_positions(text)

    def test_blank_docstring_lines_are_dropped(self) -> None:
        text = '"""\n\n\n   \nshort\n"""\n'
        assert bazel_docs.docstring_positions(text) == [(5, "short")]

    def test_a_plain_string_that_is_not_a_docstring_is_ignored(self) -> None:
        text = 'VALUE = """\n  ./scripts/manage.sh doctor\n"""\n'
        assert bazel_docs.docstring_positions(text) == []

    def test_unparseable_source_yields_nothing(self) -> None:
        assert bazel_docs.docstring_positions("def broken(:\n") == []

    def test_a_docstring_command_is_a_violation_end_to_end(self, tmp_path: Path) -> None:
        rel = "docs/generate_x_docs.py"
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('"""Usage:\n\n  python3 docs/generate_x_docs.py\n"""\n', encoding="utf-8")
        problems = bazel_docs.violations(tmp_path, [rel])
        assert any("bazelisk run //docs:generate" in p for p in problems), problems


class TestStaleExemptions:
    """The exemption table is checked in both directions, like the glob list."""

    OFFENDING = "```bash\n./scripts/manage.sh doctor\n```\n"

    def _page(self, tmp_path: Path, rel: str, text: str = OFFENDING) -> str:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return rel

    def _table(self, monkeypatch: pytest.MonkeyPatch, entries: dict[str, str]) -> None:
        # Replace the table whole: leaving the real repo's keys in place would
        # report every one of them dead against a tmp_path checkout.
        monkeypatch.setattr(bazel_docs, "_ALLOW", dict(entries))

    def test_a_line_key_on_a_flagged_command_is_live(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        rel = self._page(tmp_path, "docs/a.mdx")
        self._table(monkeypatch, {f"{rel}:2": "deliberate"})
        assert bazel_docs.stale_exemptions(tmp_path, [rel]) == []

    def test_a_line_key_that_drifted_off_is_a_finding(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        rel = self._page(tmp_path, "docs/a.mdx")
        self._table(monkeypatch, {f"{rel}:99": "moved away"})
        stale = bazel_docs.stale_exemptions(tmp_path, [rel])
        assert len(stale) == 1
        assert f"{rel}:99" in stale[0]
        assert "no flagged command" in stale[0]

    def test_a_file_key_survives_a_clean_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        rel = self._page(tmp_path, "docs/a.mdx", "nothing to flag here\n")
        self._table(monkeypatch, {rel: "standing exemption"})
        assert bazel_docs.stale_exemptions(tmp_path, [rel]) == []

    def test_a_file_key_whose_file_is_gone_is_a_finding(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self._table(monkeypatch, {"docs/gone.mdx": "the file went away"})
        stale = bazel_docs.stale_exemptions(tmp_path, [])
        assert len(stale) == 1
        assert "the file is gone" in stale[0]

    def test_findings_reports_exempt_hits_when_asked(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        rel = self._page(tmp_path, "docs/a.mdx")
        self._table(monkeypatch, {f"{rel}:2": "deliberate"})
        assert bazel_docs.violations(tmp_path, [rel]) == []
        hits = bazel_docs.findings(tmp_path, [rel], use_allow=False)
        assert len(hits) == 1
        assert hits[0][0] == rel and hits[0][1] == 2

    def test_this_checkout_carries_no_dead_exemption(self) -> None:
        assert bazel_docs.stale_exemptions(ROOT) == []


class TestCandidateFiles:
    """Generated pages and media are not the operator's text."""

    def test_generated_and_media_paths_are_dropped(self) -> None:
        tracked = [
            "docs/generated/shell/reference.md",
            "docs/getting-started.mdx",
            "docs/assets/shot.jpg",
            "docs-site/package-lock.json",
            "docs-site/node_modules/x/index.js",
        ]
        assert bazel_docs.candidate_files(tracked) == ["docs/getting-started.mdx"]


class TestAgainstTheRealCheckout:
    """The guard is not vacuous: it fires above, and is silent on this repo."""

    def test_the_repo_has_no_raw_command_references(self) -> None:
        assert bazel_docs.violations(ROOT) == []

    def test_the_policy_tables_are_populated(self) -> None:
        assert len(bazel_docs.RULES) > 10
        assert bazel_docs.HOST_VERBS
        assert bazel_docs._ALLOW


class TestRepoRoot:
    """repo_root finds the checkout through a runfiles symlink."""

    def test_locates_module_bazel(self) -> None:
        assert (bazel_docs.repo_root() / "MODULE.bazel").is_file()

    def test_main_reports_a_clean_checkout(self) -> None:
        assert bazel_docs.main(["--root", str(ROOT)]) == 0

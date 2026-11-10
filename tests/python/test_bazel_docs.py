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


class TestPublishedProseNamesTheTarget:
    """A page an operator copies from names the target, even for a host verb.

    ``scripts/manage.sh`` is the operator escape hatch, so a script's own usage
    header and log lines may print the raw door. Published prose does not get
    that latitude: ``bazelisk run //:manage -- <verb>`` runs the identical
    script on the host (it passes the client environment through and keeps the
    interactive ``start`` confirm), so the raw form on a page is a defect and
    the raw form the page *documents as the fallback* needs its own ``_ALLOW``
    reason.
    """

    def test_a_host_verb_in_a_page_is_a_violation(self) -> None:
        found = bazel_docs.classify("./scripts/manage.sh start", published=True)
        assert found == ("./scripts/manage.sh start", "bazelisk run //:manage -- start")

    def test_a_download_verb_carries_its_flags(self) -> None:
        found = bazel_docs.classify("./scripts/manage.sh download-models --limit 1000", published=True)
        assert found is not None
        assert found[1] == "bazelisk run //:manage -- download-models --limit 1000"

    def test_a_download_utility_in_a_page_is_a_violation(self) -> None:
        found = bazel_docs.classify("./scripts/utilities/download-wan.sh run --tier 5b", published=True)
        assert found is not None
        assert found[1] == "bazelisk run //scripts:run-utility -- download-wan run --tier 5b"

    def test_a_script_keeps_the_host_door(self) -> None:
        # The default stays exempt: manage.sh's help text is the escape hatch.
        assert bazel_docs.classify("./scripts/manage.sh start") is None
        assert bazel_docs.classify("./scripts/utilities/download-wan.sh run") is None

    def test_an_env_prefix_is_read_past_and_kept_in_the_fix(self) -> None:
        # `FOO=1 ./scripts/manage.sh ...` is a raw door a reader copies too.
        found = bazel_docs.classify("HF_LOCK_CLEAR_FORCE=1 ./scripts/manage.sh clear-hf-locks")
        assert found is not None
        assert found[1] == "HF_LOCK_CLEAR_FORCE=1 bazelisk run //:manage -- clear-hf-locks"

    def test_an_env_prefix_still_loses_the_host_exemption_in_a_page(self) -> None:
        found = bazel_docs.classify("LAB_ENABLE_LTX_DIRECTOR=1 ./scripts/manage.sh start", published=True)
        assert found is not None
        assert found[1] == "LAB_ENABLE_LTX_DIRECTOR=1 bazelisk run //:manage -- start"

    def test_an_env_prefixed_bazel_command_is_still_silent(self) -> None:
        assert bazel_docs.classify("LAB_STACK_FORCE_BUILD=1 bazelisk run //:manage -- start") is None

    @pytest.mark.parametrize(
        ("path", "published"),
        [
            ("docs/getting-started.mdx", True),
            ("docs/operate/daily.mdx", True),
            ("docs/generated/workflows/photos/thumbnail.md", True),
            ("README.md", True),
            ("CONTRIBUTING.md", True),
            ("scripts/manage.sh", False),
            ("scripts/lib/common.sh", False),
            ("tests/python/_build_music_workflows.py", False),
            ("docs/commands.py", False),
            ("docs-site/lib/nav.ts", False),
        ],
    )
    def test_only_published_prose_gets_the_rule(self, path: str, published: bool) -> None:
        assert bazel_docs.is_published_doc(path) is published

    def test_a_page_is_policed_and_a_script_is_not(self, tmp_path: Path) -> None:
        raw = "./scripts/manage.sh start\n"
        page = tmp_path / "docs" / "a.mdx"
        page.parent.mkdir(parents=True)
        page.write_text(f"```bash\n{raw}```\n", encoding="utf-8")
        script = tmp_path / "scripts" / "a.sh"
        script.parent.mkdir(parents=True)
        script.write_text(f'# say it: {raw.strip()}\necho "{raw.strip()}"\n', encoding="utf-8")
        problems = bazel_docs.violations(tmp_path, ["docs/a.mdx", "scripts/a.sh"])
        assert [p for p in problems if p.startswith("docs/")]
        assert not [p for p in problems if p.startswith("scripts/")]

    def test_an_allowlisted_page_line_keeps_the_raw_door(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        page = tmp_path / "docs" / "fallback.mdx"
        page.parent.mkdir(parents=True)
        page.write_text("```bash\n./scripts/manage.sh start\n```\n", encoding="utf-8")
        monkeypatch.setattr(bazel_docs, "_ALLOW", {"docs/fallback.mdx:2": "the page documents the fallback"})
        assert bazel_docs.violations(tmp_path, ["docs/fallback.mdx"]) == []


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

    def test_a_host_verb_in_a_graph_note_names_the_target(self, tmp_path: Path) -> None:
        # ComfyUI renders the note on the canvas, so it is published prose and
        # the host escape hatch does not exempt it.
        rel = "workflows/_lab/stills/x.json"
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        graph = self._graph("Warm the cache with `./scripts/manage.sh download-models`.")
        path.write_text(json.dumps(graph), encoding="utf-8")
        problems = bazel_docs.violations(tmp_path, [rel])
        # The fixture carries the sentence in both `extra.lab_note` and a Note
        # node, so the sweep reports the one command once per field.
        assert len(set(problems)) == 1, problems
        assert "bazelisk run //:manage -- download-models" in problems[0], problems

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


class TestCommandBuilderRecipes:
    """The command widgets copy straight out of JSON the text sweep skips.

    ``docs-site/components/command-vars.tsx`` imports ``includes/command-builder.json``
    and ``docs-site/lib/command-vars.ts`` joins each ``recipe.argv`` into the line the
    reader pastes, so a raw script in a recipe teaches the wrong door to everyone who
    clicks Copy. The file carries ``.json``, so ``_SKIP_SUFFIX`` keeps it out of the
    prose sweep: like the lab graphs, it gets its own pass over the rendered text.
    """

    BUILDER_REL = "includes/command-builder.json"

    def _recipe(self, recipe_id: str, argv: list[str], **extra: object) -> dict[str, object]:
        """One recipe in the shipped shape: id, title, description, argv, flags."""
        row: dict[str, object] = {
            "id": recipe_id,
            "title": recipe_id,
            "description": f"{recipe_id} fixture recipe",
            "argv": list(argv),
            "flags": [],
        }
        row.update(extra)
        return row

    def _builder(self, *recipes: dict[str, object]) -> dict[str, object]:
        """A builder payload with the shipped file's two top-level keys."""
        return {
            "variables": [{"id": "SPARK_HOST", "label": "Spark IP / DNS", "default": "127.0.0.1"}],
            "commands": [dict(recipe) for recipe in recipes],
        }

    def _write(self, root: Path, payload: object, rel: str | None = None) -> str:
        """Write a builder payload at its shipped path; return that path."""
        target = rel or self.BUILDER_REL
        path = root / target
        path.parent.mkdir(parents=True, exist_ok=True)
        text = payload if isinstance(payload, str) else json.dumps(payload)
        path.write_text(text, encoding="utf-8")
        return target

    def test_argv_is_read_as_the_rendered_line(self) -> None:
        builder = self._builder(self._recipe("doctor", ["./scripts/manage.sh", "doctor"]))
        assert bazel_docs.builder_recipe_commands(builder) == [
            ("doctor", "./scripts/manage.sh doctor")
        ]

    def test_a_raw_manage_recipe_is_reported_with_its_target(self, tmp_path: Path) -> None:
        rel = self._write(tmp_path, self._builder(self._recipe("doctor", ["./scripts/manage.sh", "doctor"])))
        problems = bazel_docs.command_builder_violations(tmp_path, [rel])
        assert len(problems) == 1, problems
        assert "bazelisk run //:manage -- doctor" in problems[0]
        assert rel in problems[0]

    def test_the_report_names_the_recipe_id(self, tmp_path: Path) -> None:
        argv = ["./scripts/manage.sh", "agent-model", "status"]
        rel = self._write(tmp_path, self._builder(self._recipe("agent-model", argv)))
        problems = bazel_docs.command_builder_violations(tmp_path, [rel])
        assert len(problems) == 1, problems
        assert "agent-model" in problems[0]
        assert "bazelisk run //:manage -- agent-model status" in problems[0]

    def test_violations_reports_a_raw_recipe_end_to_end(self, tmp_path: Path) -> None:
        rel = self._write(tmp_path, self._builder(self._recipe("doctor", ["./scripts/manage.sh", "doctor"])))
        problems = bazel_docs.violations(tmp_path, [rel])
        assert len(problems) == 1, problems
        assert "bazelisk run //:manage -- doctor" in problems[0]

    @pytest.mark.parametrize("verb", ["download-models", "download-podcast", "start", "stop", "setup", "onboard"])
    def test_a_host_verb_recipe_names_the_target(self, tmp_path: Path, verb: str) -> None:
        # The widget's clipboard text is published prose, so the host escape
        # hatch that a script's own usage header keeps does not apply here.
        rel = self._write(tmp_path, self._builder(self._recipe(verb, ["./scripts/manage.sh", verb])))
        problems = bazel_docs.command_builder_violations(tmp_path, [rel])
        assert len(problems) == 1, problems
        assert f"bazelisk run //:manage -- {verb}" in problems[0], problems

    def test_a_raw_download_utility_recipe_names_the_target(self, tmp_path: Path) -> None:
        recipe = self._recipe("download-wan", ["./scripts/utilities/download-wan.sh", "run"])
        rel = self._write(tmp_path, self._builder(recipe))
        problems = bazel_docs.command_builder_violations(tmp_path, [rel])
        assert len(problems) == 1, problems
        assert "bazelisk run //scripts:run-utility -- download-wan run" in problems[0], problems

    @pytest.mark.parametrize(
        "argv",
        [
            ["ssh", "-L", "${COMFY_PORT}:127.0.0.1:${COMFY_PORT}", "${SPARK_USER}@${SPARK_HOST}"],
            ["echo", "http://${SPARK_HOST}:${COMFY_PORT}"],
            ["docker", "compose", "-f", "docker/docker-compose.yml", "ps"],
        ],
    )
    def test_a_recipe_with_no_target_at_all_passes(self, tmp_path: Path, argv: list[str]) -> None:
        rel = self._write(tmp_path, self._builder(self._recipe("plain", argv)))
        assert bazel_docs.command_builder_violations(tmp_path, [rel]) == []

    def test_a_target_recipe_is_clean(self, tmp_path: Path) -> None:
        recipe = self._recipe("doctor", ["bazelisk", "run", "//:manage", "--", "doctor"])
        rel = self._write(tmp_path, self._builder(recipe))
        assert bazel_docs.command_builder_violations(tmp_path, [rel]) == []

    def test_only_argv_is_matched_not_the_whole_json(self, tmp_path: Path) -> None:
        """Prose fields and argv arguments are not the copied line."""
        quoted = self._recipe(
            "echo-it",
            ["echo", "run ./scripts/manage.sh doctor"],
            description="Older pages said `./scripts/manage.sh doctor` here.",
        )
        rel = self._write(tmp_path, self._builder(quoted))
        assert bazel_docs.command_builder_violations(tmp_path, [rel]) == []

    def test_a_file_level_allow_entry_silences_the_pass(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        recipe = self._recipe("doctor", ["./scripts/manage.sh", "doctor"])
        rel = self._write(tmp_path, self._builder(recipe))
        monkeypatch.setattr(bazel_docs, "_ALLOW", {rel: "the widget is the documented door"})
        assert bazel_docs.command_builder_violations(tmp_path, [rel]) == []

    def test_only_the_builder_file_gets_this_pass(self, tmp_path: Path) -> None:
        recipe = self._recipe("doctor", ["./scripts/manage.sh", "doctor"])
        rel = self._write(tmp_path, self._builder(recipe), rel="config/other.json")
        assert bazel_docs.command_builder_violations(tmp_path, [rel]) == []

    def test_broken_shapes_and_missing_files_are_tolerated(self, tmp_path: Path) -> None:
        """A payload the guard cannot read is not a doc violation."""
        payloads: list[object] = [
            "{nope",
            "[]",
            {"variables": []},
            {"commands": {}},
            {
                "variables": [],
                "commands": [
                    "scalar",
                    {"id": "no-argv"},
                    {"id": "argv-not-a-list", "argv": "not-a-list"},
                    {"id": "argv-all-blank", "argv": ["", "  "]},
                ],
            },
        ]
        for index, payload in enumerate(payloads):
            root = tmp_path / f"case{index}"
            rel = self._write(root, payload)
            assert bazel_docs.command_builder_violations(root, [rel]) == [], payload
        # A checkout that carries no builder file at all is silent too.
        assert bazel_docs.command_builder_violations(tmp_path / "empty", [self.BUILDER_REL]) == []

    def test_a_recipe_without_argv_is_skipped(self) -> None:
        builder = {"variables": [], "commands": [{"id": "empty"}, {"id": "ok", "argv": ["ls", "-la"]}]}
        assert bazel_docs.builder_recipe_commands(builder) == [("ok", "ls -la")]

    def test_the_shipped_builder_passes_the_pass_today(self) -> None:
        """Regression net: every copied line in the shipped file names a target."""
        payload = json.loads((ROOT / self.BUILDER_REL).read_text(encoding="utf-8"))
        recipes = bazel_docs.builder_recipe_commands(payload)
        # Non-vacuous: a loader that silently matched nothing would also pass
        # the assert below, so pin that the real file really yields recipes.
        assert len(recipes) >= 50, recipes
        assert all(recipe_id and command for recipe_id, command in recipes), recipes
        assert bazel_docs.command_builder_violations(ROOT, [self.BUILDER_REL]) == []


class TestTemplateComments:
    """Shipped templates are operator text too, and none of them can be fenced.

    ``.env.example``, ``config/*.yaml`` and ``scripts/utilities/*.ps1`` are read
    by the operator before the first run, and a ``#`` header line is the only
    place a usage note can go in them. As prose they yield no command position,
    so the sweep passed straight over the raw door in their headers. They are
    read as code instead, which reuses the comment rule that already covers a
    shell script's own usage header.
    """

    def test_a_template_comment_that_tells_the_operator_to_run_a_script(self, tmp_path: Path) -> None:
        rel = ".env.example"
        (tmp_path / rel).write_text(
            "# Copy and edit: ./scripts/manage.sh setup   (or, by hand: cp it to .env)\n",
            encoding="utf-8",
        )
        problems = bazel_docs.violations(tmp_path, [rel])
        assert len(problems) == 1, problems
        assert "bazelisk run //:manage -- setup" in problems[0]

    def test_a_yaml_header_is_read_the_same_way(self, tmp_path: Path) -> None:
        rel = "config/disk-catalog.yaml"
        page = tmp_path / rel
        page.parent.mkdir(parents=True)
        page.write_text(
            "# Remeasure the disk budget with\n"
            "#   ./scripts/manage.sh disk-wizard --refresh\n",
            encoding="utf-8",
        )
        problems = bazel_docs.violations(tmp_path, [rel])
        assert len(problems) == 1, problems
        assert "bazelisk run //:manage -- disk-wizard --refresh" in problems[0]

    def test_a_pointer_that_names_the_script_stays_prose(self, tmp_path: Path) -> None:
        # "operator entry via X" and "the studio. ./scripts/manage.sh setup
        # copies this" name the door as a sentence subject. Promoting them
        # would have the gate demand an exemption for prose, so the split sits
        # on the marks that introduce an instruction only.
        rel = "config/disk-catalog.yaml"
        page = tmp_path / rel
        page.parent.mkdir(parents=True)
        page.write_text(
            "# Source of truth: this file (operator entry via "
            "./scripts/manage.sh disk-wizard)\n"
            "# read for the one-box studio. ./scripts/manage.sh setup copies this\n",
            encoding="utf-8",
        )
        assert bazel_docs.violations(tmp_path, [rel]) == []

    def test_a_powershell_usage_line_names_the_target_that_exists(self, tmp_path: Path) -> None:
        # No target dispatches a .ps1, so the raw line is legal here; the test
        # pins that the pass *sees* the line, which is what forces the named
        # exemption below rather than silence.
        rel = "scripts/utilities/setup-client.ps1"
        page = tmp_path / rel
        page.parent.mkdir(parents=True)
        page.write_text("#   ./scripts/manage.sh setup-client\n", encoding="utf-8")
        assert len(bazel_docs.violations(tmp_path, [rel])) == 1

    def test_an_executed_config_value_stays_implementation(self, tmp_path: Path) -> None:
        # A compose `command:` is what the container runs, not what a reader
        # pastes, and reading templates as code must not turn config into prose.
        rel = "docker/docker-compose.yml"
        page = tmp_path / rel
        page.parent.mkdir(parents=True)
        page.write_text('  command: "./scripts/manage.sh start"\n', encoding="utf-8")
        assert bazel_docs.violations(tmp_path, [rel]) == []

    def test_a_template_that_only_names_a_script_is_not_a_command(self, tmp_path: Path) -> None:
        rel = ".env.example"
        (tmp_path / rel).write_text(
            "# What this is: every host-side knob ./scripts/manage.sh and docker\n"
            "#   compose read for the one-box US-safe studio.\n",
            encoding="utf-8",
        )
        assert bazel_docs.violations(tmp_path, [rel]) == []

    def test_the_shipped_templates_name_the_targets(self) -> None:
        shipped = [
            ".env.example",
            "config/spark-farm.example.env",
            "config/disk-catalog.yaml",
            "docker/docker-compose.yml",
            ".github/workflows/ci.yml",
        ]
        assert bazel_docs.violations(ROOT, shipped) == []


class TestGlossaryProse:
    """The glossary cards are prose the JSON sweep skips.

    ``docs/glossary.py`` renders each entry's ``short`` and ``long`` onto a
    published card, so a raw script in a field is the same defect as a raw
    script in a fenced block. The file carries ``.json``, so ``_SKIP_SUFFIX``
    keeps it out of the text sweep, and a field is a sentence rather than a
    command position: the pass reads the clause-initial run of each field,
    which is where an instruction starts, and lets ``classify`` reject the
    rest. A field that only names a script stays a file reference.
    """

    GLOSSARY_REL = "includes/glossary.json"

    def _entry(self, entry_id: str, **fields: object) -> dict[str, object]:
        """One entry in the shipped shape: id, title, category, short, long."""
        row: dict[str, object] = {
            "id": entry_id,
            "title": entry_id.replace("-", " ").title(),
            "category": "Ops",
            "short": f"{entry_id} fixture short",
            "long": f"{entry_id} fixture long",
        }
        row.update(fields)
        return row

    def _write(self, root: Path, *entries: object) -> str:
        """Write a glossary payload at its shipped path; return that path."""
        path = root / self.GLOSSARY_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(list(entries)), encoding="utf-8")
        return self.GLOSSARY_REL

    def test_a_backticked_command_in_a_field_is_reported_with_its_target(
        self, tmp_path: Path
    ) -> None:
        rel = self._write(
            tmp_path,
            self._entry("research-mcp", long="Typed stdio MCP (`./scripts/manage.sh research-mcp`)."),
        )
        problems = bazel_docs.glossary_violations(tmp_path, [rel])
        assert len(problems) == 1, problems
        assert "bazelisk run //:manage -- research-mcp" in problems[0]
        assert rel in problems[0]

    def test_a_bare_command_after_a_clause_break_is_reported(self, tmp_path: Path) -> None:
        # The shipped app-forge card runs the command without backticks, so the
        # pass cannot read backticked spans alone.
        rel = self._write(
            tmp_path,
            self._entry("app-forge", long="Writes the app. Path D: ./scripts/manage.sh studio-mcp --stdio."),
        )
        problems = bazel_docs.glossary_violations(tmp_path, [rel])
        assert len(problems) == 1, problems
        assert "bazelisk run //:manage -- studio-mcp --stdio" in problems[0]

    def test_a_host_verb_loses_its_escape_hatch_in_a_field(self, tmp_path: Path) -> None:
        # The wrapper execs the identical script on the host, so a card that
        # tells the operator to start the stack by hand teaches the wrong door.
        rel = self._write(tmp_path, self._entry("studio", long="Bring the stack up: ./scripts/manage.sh start."))
        problems = bazel_docs.glossary_violations(tmp_path, [rel])
        assert len(problems) == 1, problems
        assert "bazelisk run //:manage -- start" in problems[0]

    def test_a_download_utility_field_names_the_run_utility_target(self, tmp_path: Path) -> None:
        rel = self._write(
            tmp_path,
            self._entry("wan", long="Weights: ./scripts/utilities/download-wan.sh run --tier 5b."),
        )
        problems = bazel_docs.glossary_violations(tmp_path, [rel])
        assert len(problems) == 1, problems
        assert "bazelisk run //scripts:run-utility -- download-wan run --tier 5b" in problems[0]

    def test_a_field_that_only_names_a_script_is_not_a_command(self, tmp_path: Path) -> None:
        # Both halves of the drift case: a link label, and a sentence whose
        # subject is the file. Trimming to the command must not reach these.
        rel = self._write(
            tmp_path,
            self._entry("manage", long="See [manage.sh reference](manage-cli.md) for the verbs."),
            self._entry("router", long="The scripts/manage.sh file routes operator actions."),
        )
        assert bazel_docs.glossary_violations(tmp_path, [rel]) == []

    def test_only_the_prose_fields_are_read(self, tmp_path: Path) -> None:
        # A title or an alias is a name a reader searches for, never a line to
        # paste; policing them would push a target into a term heading.
        rel = self._write(
            tmp_path,
            self._entry("odd", title="./scripts/manage.sh start", aliases=["./scripts/manage.sh stop"]),
        )
        assert bazel_docs.glossary_violations(tmp_path, [rel]) == []

    def test_a_malformed_payload_is_ignored_rather_than_raising(self, tmp_path: Path) -> None:
        rel = self._write(tmp_path, "not an entry", 7, {"long": 3})
        assert bazel_docs.glossary_violations(tmp_path, [rel]) == []

    def test_a_payload_that_is_not_a_list_is_ignored(self) -> None:
        # A future edit could make the file an object of categories, and the
        # pass must fall silent rather than crash the whole gate.
        assert bazel_docs.glossary_prose_fields({"klein": {"long": "x"}}) == []
        assert bazel_docs.glossary_prose_fields("klein") == []

    def test_an_absent_or_unparseable_glossary_is_ignored(self, tmp_path: Path) -> None:
        # The pass is handed the whole tracked list, so it has to shrug at a
        # path it was pointed at that is not there, and at a half-written file.
        absent = self.GLOSSARY_REL
        assert bazel_docs.glossary_violations(tmp_path, [absent]) == []
        rel = absent
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('[{"long": ', encoding="utf-8")
        assert bazel_docs.glossary_violations(tmp_path, [rel]) == []

    def test_the_report_names_the_entry_and_field(self, tmp_path: Path) -> None:
        rel = self._write(tmp_path, self._entry("blender-mcp", long="`./scripts/manage.sh blender-mcp`"))
        problems = bazel_docs.glossary_violations(tmp_path, [rel])
        assert len(problems) == 1, problems
        assert "blender-mcp" in problems[0]
        assert "long" in problems[0]

    def test_a_line_keyed_exemption_cannot_reach_a_field(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # A card has no line the reader sees, so only a bare path key can exempt
        # one; a line key would rot the moment the JSON reflows.
        rel = self._write(tmp_path, self._entry("research-mcp", long="`./scripts/manage.sh research-mcp`"))
        monkeypatch.setitem(bazel_docs._ALLOW, f"{self.GLOSSARY_REL}:5", "wrong shape of key")
        assert len(bazel_docs.glossary_violations(tmp_path, [rel])) == 1

    def test_a_bare_path_key_exempts_a_card(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        rel = self._write(tmp_path, self._entry("research-mcp", long="`./scripts/manage.sh research-mcp`"))
        monkeypatch.setitem(bazel_docs._ALLOW, self.GLOSSARY_REL, "named exemption")
        assert bazel_docs.glossary_violations(tmp_path, [rel]) == []

    def test_the_shipped_glossary_names_the_targets(self) -> None:
        assert bazel_docs.glossary_violations(ROOT, [self.GLOSSARY_REL]) == []


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
    """Media and lockfiles are not the operator's text; generated pages are."""

    def test_media_and_lockfiles_are_dropped(self) -> None:
        tracked = [
            "docs/generated/shell/reference.md",
            "docs/getting-started.mdx",
            "docs/assets/shot.jpg",
            "docs-site/package-lock.json",
            "docs-site/node_modules/x/index.js",
        ]
        assert bazel_docs.candidate_files(tracked) == [
            "docs/generated/shell/reference.md",
            "docs/getting-started.mdx",
        ]

    def test_a_generated_page_is_policed_like_a_hand_written_one(self, tmp_path: Path) -> None:
        # //docs:generate writes these, so a raw door here came from a
        # generator template and has to fail the same way a page does.
        rel = "docs/generated/workflows/photos/thumbnail.md"
        page = tmp_path / rel
        page.parent.mkdir(parents=True)
        page.write_text("```bash\n./scripts/manage.sh start\n```\n", encoding="utf-8")
        problems = bazel_docs.violations(tmp_path, [rel])
        assert any("bazelisk run //:manage -- start" in p for p in problems), problems


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

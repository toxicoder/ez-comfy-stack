#!/usr/bin/env python3
"""Unit tests for the MDX hazard audit (docs-site/scripts/audit_mdx_hazards.py).

Run: bazelisk test //docs-site:audit_hazards_test
 (or: python3 -m unittest -v test_audit_hazards.py)

The auditor is the migration's sight line: it names the lines the MDX compiler would read as
a JSX element or a JS expression rather than as the prose the author wrote. A missed line is
a page that fails to compile; a false line is an author escaping a character that never
needed it. Both directions are pinned here - what is reported, and what fenced blocks,
inline code spans, autolinks, HTML comments, and backslash escapes keep out of the report.
"""

from __future__ import annotations

import contextlib
import io
import json
import pathlib
import runpy
import sys
import tempfile
import unittest
from collections.abc import Iterator

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "scripts"))

import audit_mdx_hazards as hazards  # noqa: E402

AUDIT_SCRIPT = pathlib.Path(hazards.__file__).resolve()

#: One page with each kind of hazard on its own line, so a report row names both.
HAZARD_PAGE = (
    "# Album export\n"
    "\n"
    "Write <Album>.m3u under albums/.\n"
    "\n"
    "Set {this} up first.\n"
)

CLEAN_PAGE = "# Daily\n\nNothing here needs escaping.\n"


def _write_pages(root: pathlib.Path, pages: dict[str, str]) -> None:
    """Lay out ``<root>/docs`` with the given pages, creating any folder between."""
    for relative, body in pages.items():
        page = root / "docs" / relative
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(body, encoding="utf-8")


def _run_cli(root: pathlib.Path, *args: str) -> str:
    """Run the CLI over a fixture checkout and hand back everything it printed.

    Both report modes are read-only and always exit 0, so a non-zero code is a defect and
    not a test outcome; it raises instead of returning text a later assertion would misread.
    """
    buffer = io.StringIO()
    with _point_at(root), contextlib.redirect_stdout(buffer):
        code = hazards.main([str(root / "docs"), *args])
    if code != 0:
        raise AssertionError(f"main({list(args)!r}) exited {code}")
    return buffer.getvalue()


def _rows(printed: str) -> list[str]:
    """The report's printed rows, with the column padding collapsed for readability."""
    return [" ".join(line.split()) for line in printed.splitlines()]


class AuditTests(unittest.TestCase):
    """``audit()`` reports one row per hostile line, in file order."""

    def test_plain_prose_is_clean(self) -> None:
        self.assertEqual([], hazards.audit("Never reboot during a run.\n"))

    def test_literal_brace_is_reported_as_brace(self) -> None:
        self.assertEqual(
            [(1, "brace", "Set {this} up first.")],
            hazards.audit("Set {this} up first.\n"),
        )

    def test_closing_brace_alone_counts(self) -> None:
        self.assertEqual([(2, "brace", "  }")], hazards.audit("\n  }\n"))

    def test_opening_tag_is_reported_as_jsxish(self) -> None:
        self.assertEqual(
            [(1, "jsxish", "Write <Album>.m3u under albums/.")],
            hazards.audit("Write <Album>.m3u under albums/.\n"),
        )

    def test_closing_tag_and_dotted_component_are_jsxish(self) -> None:
        self.assertEqual(
            [(1, "jsxish", "<Foo.Bar />"), (2, "jsxish", "</div>")],
            hazards.audit("<Foo.Bar />\n</div>\n"),
        )

    def test_a_lone_angle_bracket_is_not_jsxish(self) -> None:
        """``a < b`` is prose: only ``<`` followed by a name reads as JSX."""
        self.assertEqual([], hazards.audit("Keep the run under 60 < 90 minutes.\n"))

    def test_brace_outranks_jsxish_on_one_line(self) -> None:
        """One line yields one row, and the expression hazard is the one named."""
        self.assertEqual(
            [(1, "brace", "Render <Card> for {value}")],
            hazards.audit("Render <Card> for {value}\n"),
        )

    def test_hits_keep_file_order_and_the_original_text(self) -> None:
        self.assertEqual(
            [(1, "jsxish", "<Alpha>"), (3, "brace", "{beta}"), (5, "jsxish", "</gamma>")],
            hazards.audit("<Alpha>\n\n{beta}\n\n</gamma>\n"),
        )


class ExemptionTests(unittest.TestCase):
    """What MDX accepts verbatim must not reach the report."""

    def test_fenced_block_content_is_exempt(self) -> None:
        source = "Before.\n\n```text\n{not_a_binding}\n<div></div>\n```\n\nAfter.\n"
        self.assertEqual([], hazards.audit(source))

    def test_fence_markers_and_the_lines_around_them_are_exempt(self) -> None:
        """The fence lines belong to the block, and only the prose outside is probed."""
        source = "```json\n{}\n```\n\n{reported}\n"
        self.assertEqual([(5, "brace", "{reported}")], hazards.audit(source))

    def test_indented_fence_is_recognised(self) -> None:
        source = "- Step:\n\n    ```bash\n    echo {literal}\n    ```\n"
        self.assertEqual([], hazards.audit(source))

    def test_tilde_fence_is_recognised(self) -> None:
        source = "~~~\n{literal}\n~~~\n"
        self.assertEqual([], hazards.audit(source))

    def test_closing_fence_must_use_the_same_marker(self) -> None:
        """A ``~~~`` inside a backtick block is literal, so the block still shields line 4."""
        source = "```\n~~~\n{still_inside}\n```\n{reported}\n"
        self.assertEqual([(5, "brace", "{reported}")], hazards.audit(source))

    def test_closing_fence_may_be_longer_than_the_opener(self) -> None:
        source = "```\n{inside}\n````\n{reported}\n"
        self.assertEqual([(4, "brace", "{reported}")], hazards.audit(source))

    def test_shorter_closing_fence_does_not_end_the_block(self) -> None:
        source = "````\n{inside}\n```\n{also_inside}\n````\n"
        self.assertEqual([], hazards.audit(source))

    def test_unterminated_fence_shields_the_rest_of_the_file(self) -> None:
        source = "Prose.\n\n```\n{never_closed}\n<div></div>\n"
        self.assertEqual([], hazards.audit(source))

    def test_inline_code_span_is_exempt(self) -> None:
        self.assertEqual([], hazards.audit("Run `{x}` and `echo <b>`. \n"))

    def test_double_backtick_span_holds_a_literal_backtick(self) -> None:
        self.assertEqual([], hazards.audit("Use `` {x} `` and `` ` `` verbatim.\n"))

    def test_autolink_is_exempt(self) -> None:
        self.assertEqual([], hazards.audit("See <https://example.com/a_b> for more.\n"))

    def test_html_comment_is_exempt(self) -> None:
        self.assertEqual([], hazards.audit("Prose. <!-- TODO <div> {x} --> more.\n"))

    def test_backslash_escaped_brace_and_tag_are_exempt(self) -> None:
        self.assertEqual([], hazards.audit("Literal \\{braces\\} and \\<div\\> here.\n"))

    def test_one_escape_does_not_blind_the_probe_to_the_next_hazard(self) -> None:
        self.assertEqual(
            [(1, "brace", "Literal \\{x\\} plus {real}")],
            hazards.audit("Literal \\{x\\} plus {real}\n"),
        )


class MainReportTests(unittest.TestCase):
    """The human-readable report the migration is driven off."""

    def test_summary_counts_files_scanned_and_both_reasons(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_pages(root, {"index.md": HAZARD_PAGE, "operate/daily.md": CLEAN_PAGE})
            printed = _run_cli(root)
        self.assertIn("1 of 2 files, 2 hostile lines (1 brace, 1 jsxish)", _rows(printed))

    def test_hits_are_listed_with_line_number_reason_and_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_pages(root, {"index.md": HAZARD_PAGE})
            printed = _run_cli(root)
        rows = _rows(printed)
        self.assertIn("docs/index.md (2)", rows)
        self.assertIn("3 jsxish Write <Album>.m3u under albums/.", rows)
        self.assertIn("5 brace Set {this} up first.", rows)

    def test_paths_are_reported_relative_to_the_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_pages(root, {"operate/nested/deep.md": HAZARD_PAGE})
            printed = _run_cli(root)
        self.assertIn("docs/operate/nested/deep.md (2)", _rows(printed))

    def test_a_clean_tree_reports_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_pages(root, {"index.md": CLEAN_PAGE, "other.md": CLEAN_PAGE})
            printed = _run_cli(root)
        self.assertIn("0 of 2 files, 0 hostile lines (0 brace, 0 jsxish)", _rows(printed))
        self.assertEqual(["0 of 2 files, 0 hostile lines (0 brace, 0 jsxish)"], _rows(printed))

    def test_limit_truncates_the_listing_and_reports_the_remainder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            body = "".join(f"<Tag{number}>\n" for number in range(5))
            _write_pages(root, {"index.md": body})
            printed = _run_cli(root, "--limit", "2")
        rows = _rows(printed)
        self.assertIn("1 of 1 files, 5 hostile lines (0 brace, 5 jsxish)", rows)
        self.assertIn("1 jsxish <Tag0>", rows)
        self.assertIn("2 jsxish <Tag1>", rows)
        self.assertNotIn("3 jsxish <Tag2>", rows)
        self.assertIn("... 3 more", rows)

    def test_zero_limit_counts_the_file_without_listing_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_pages(root, {"index.md": HAZARD_PAGE})
            printed = _run_cli(root, "--limit", "0")
        rows = _rows(printed)
        self.assertIn("docs/index.md (2)", rows)
        self.assertIn("... 2 more", rows)
        self.assertNotIn("5 brace Set {this} up first.", rows)

    def test_long_lines_are_truncated_in_the_listing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_pages(root, {"index.md": "<div " + "x" * 200 + ">\n"})
            printed = _run_cli(root)
        listed = [row for row in _rows(printed) if row.startswith("1 jsxish")]
        self.assertEqual(1, len(listed))
        self.assertEqual(100, len(listed[0].removeprefix("1 jsxish ")))


class MainScopeTests(unittest.TestCase):
    """``--scope`` separates authored pages from generator output.

    The summary denominator is the scoped file set, not every page on disk: a run over the
    authored pages reads "1 of 1", because the pages it left out are not candidates.
    """

    PAGES = {
        "index.md": HAZARD_PAGE,
        "generated/shell/reference.md": HAZARD_PAGE,
    }

    def test_default_scope_reports_both_kinds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_pages(root, self.PAGES)
            printed = _run_cli(root)
        self.assertIn("2 of 2 files, 4 hostile lines (2 brace, 2 jsxish)", _rows(printed))

    def test_hand_scope_skips_generated_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_pages(root, self.PAGES)
            printed = _run_cli(root, "--scope", "hand")
        self.assertIn("1 of 1 files, 2 hostile lines (1 brace, 1 jsxish)", _rows(printed))
        self.assertIn("docs/index.md (2)", _rows(printed))
        self.assertNotIn("generated", printed)

    def test_generated_scope_keeps_only_generated_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_pages(root, self.PAGES)
            printed = _run_cli(root, "--scope", "generated")
        self.assertIn("1 of 1 files, 2 hostile lines (1 brace, 1 jsxish)", _rows(printed))
        self.assertIn("docs/generated/shell/reference.md (2)", _rows(printed))
        self.assertNotIn("docs/index.md", printed)

    def test_generated_folder_only_counts_below_the_scanned_root(self) -> None:
        """A page named ``generated.md`` is authored prose, not generator output."""
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_pages(root, {"generated.md": HAZARD_PAGE})
            printed = _run_cli(root, "--scope", "hand")
        self.assertIn("1 of 1 files, 2 hostile lines (1 brace, 1 jsxish)", _rows(printed))

    def test_vendor_directories_are_never_audited(self) -> None:
        for excluded in sorted(hazards.EXCLUDED):
            with self.subTest(excluded=excluded), tempfile.TemporaryDirectory() as tmp:
                root = pathlib.Path(tmp)
                _write_pages(
                    root,
                    {"index.md": HAZARD_PAGE, f"{excluded}/pkg/README.md": HAZARD_PAGE},
                )
                printed = _run_cli(root)
                self.assertIn("1 of 1 files, 2 hostile lines (1 brace, 1 jsxish)", _rows(printed))
                self.assertNotIn(excluded, printed)


class MainJsonTests(unittest.TestCase):
    """``--json`` is the machine-readable form another gate can diff."""

    def test_json_mode_emits_relative_paths_and_hit_tuples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_pages(root, {"index.md": HAZARD_PAGE, "operate/daily.md": CLEAN_PAGE})
            printed = _run_cli(root, "--json")
        self.assertEqual(
            {
                "docs/index.md": [
                    [3, "jsxish", "Write <Album>.m3u under albums/."],
                    [5, "brace", "Set {this} up first."],
                ]
            },
            json.loads(printed),
        )

    def test_json_mode_emits_an_empty_object_for_a_clean_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_pages(root, {"index.md": CLEAN_PAGE})
            printed = _run_cli(root, "--json")
        self.assertEqual({}, json.loads(printed))

    def test_json_mode_reports_nothing_but_zero_for_an_empty_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "docs").mkdir()
            printed = _run_cli(root, "--json")
        self.assertEqual({}, json.loads(printed))


class MainDefaultRootTests(unittest.TestCase):
    """With no path argument the audit runs over the checkout's ``docs/``."""

    def test_default_root_is_the_docs_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_pages(root, {"index.md": HAZARD_PAGE})
            buffer = io.StringIO()
            with _point_at(root), contextlib.redirect_stdout(buffer):
                self.assertEqual(0, hazards.main([]))
            self.assertIn("1 of 1 files, 2 hostile lines (1 brace, 1 jsxish)", _rows(buffer.getvalue()))

    def test_markdown_only_tree_is_scanned(self) -> None:
        """The audit reads ``*.md``; an ``.mdx`` page is already past the migration."""
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            _write_pages(root, {"index.md": HAZARD_PAGE})
            (root / "docs" / "already.mdx").write_text(HAZARD_PAGE, encoding="utf-8")
            printed = _run_cli(root)
        self.assertIn("1 of 1 files, 2 hostile lines (1 brace, 1 jsxish)", _rows(printed))


class MainGuardTests(unittest.TestCase):
    """The script form the docs gate invokes has to behave like ``main()``."""

    def test_main_module_guard(self) -> None:
        """Re-executing the module as ``__main__`` audits the real tree and exits 0.

        Re-executing re-reads its paths from its own file location, so the fixture patching
        above cannot apply here. ``--scope hand`` keeps it to the authored pages.
        """
        buffer = io.StringIO()
        with _captured_args([str(hazards.DOCS_DIR), "--scope", "hand", "--json"]), (
            contextlib.redirect_stdout(buffer)
        ):
            with self.assertRaises(SystemExit) as raised:
                runpy.run_path(str(AUDIT_SCRIPT), run_name="__main__")
        self.assertEqual(0, raised.exception.code, "the audit CLI must exit cleanly")
        self.assertIsInstance(json.loads(buffer.getvalue()), dict)


@contextlib.contextmanager
def _captured_args(argv: list[str]) -> Iterator[None]:
    """Pin ``sys.argv`` so a module run as ``__main__`` sees a known command line."""
    original = sys.argv
    sys.argv = ["audit_mdx_hazards.py", *argv]
    try:
        yield
    finally:
        sys.argv = original


class _point_at:
    """Temporarily repoint the auditor's module-level paths at a fixture root.

    ``REPO_ROOT`` decides how a hit is named in the report, so an unpatched value would make
    a check-out temporary directory relative to nothing and raise.
    """

    def __init__(self, root: pathlib.Path) -> None:
        self._paths = {
            "REPO_ROOT": root,
            "DOCS_DIR": root / "docs",
        }
        self._saved: dict[str, pathlib.Path] = {}

    def __enter__(self) -> "_point_at":
        for name, value in self._paths.items():
            self._saved[name] = getattr(hazards, name)
            setattr(hazards, name, value)
        return self

    def __exit__(self, *_exc: object) -> None:
        for name, value in self._saved.items():
            setattr(hazards, name, value)


if __name__ == "__main__":
    unittest.main(verbosity=2)

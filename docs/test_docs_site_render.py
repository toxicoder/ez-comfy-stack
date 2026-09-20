#!/usr/bin/env python3
"""Render-oriented checks for the Fumadocs documentation site.

Source-level checks always run. Export checks skip when docs-site/out/ is missing.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
DOCS_DIR = REPO_ROOT / "docs"
SITE_DIR = REPO_ROOT / "docs-site"
EXPORT_DIR = SITE_DIR / "out"
NAV_JSON = SITE_DIR / "lib" / "nav.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(?P<body>.*?)\n---\s*\n", re.S)
TITLE_RE = re.compile(r"^title:\s*.+$", re.M)
DESCRIPTION_RE = re.compile(r"^description:\s*.+$", re.M)
TAGS_RE = re.compile(r"^tags:\s*\[", re.M)
BAD_PROSE_LIST_RE = re.compile(r"[^\n]:[ \t]*\n-\s")
BAD_MERMAID_LABEL_RE = re.compile(r'\[[^"\]]*\{\{')
MERMAID_FENCE_RE = re.compile(r"^```mermaid\b", re.M)
FENCE_OPEN_RE = re.compile(r"^(`{3,}|~{3,})(\S*)")
INDIGO_RE = re.compile(r"indigo", re.I)


def _flatten_nav(nodes: list[object]) -> list[str]:
    """Collect page paths from nested nav.json nodes.

    Args:
        nodes: Tab or group page lists.

    Returns:
        Relative docs paths.
    """
    out: list[str] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        path = node.get("path")
        if isinstance(path, str) and path:
            out.append(path)
        pages = node.get("pages")
        if isinstance(pages, list):
            out.extend(_flatten_nav(pages))
    return out


def load_nav_pages() -> list[str]:
    """Return content paths listed in the static navigation.

    Returns:
        POSIX paths relative to ``docs/``.
    """
    tree = json.loads(NAV_JSON.read_text(encoding="utf-8"))
    pages = _flatten_nav(tree)
    assert pages, f"{NAV_JSON} lists no pages; run python3 docs-site/scripts/gen_nav.py"
    return pages


def hand_written_nav_pages() -> list[str]:
    """Navigable authored pages (not generated trees).

    Returns:
        Paths relative to docs/.
    """
    return [p for p in load_nav_pages() if not p.startswith("generated/")]


def page_source(rel: str) -> str:
    """Read a content page, accepting either extension.

    Args:
        rel: Path relative to docs/ as recorded in the navigation.

    Returns:
        Page text.
    """
    stem = rel[: rel.rfind(".")] if "." in rel else rel
    for candidate in (DOCS_DIR / f"{stem}.mdx", DOCS_DIR / f"{stem}.md"):
        if candidate.exists():
            return candidate.read_text(encoding="utf-8", errors="replace")
    raise AssertionError(f"Missing content page for nav entry {rel!r}")


class NavContractTests(unittest.TestCase):
    """Every static nav path exists on disk."""

    def test_nav_json_exists(self) -> None:
        """The transcribed navigation is committed."""
        self.assertTrue(NAV_JSON.is_file(), NAV_JSON)

    def test_nav_pages_exist(self) -> None:
        """Each nav path has a .md or .mdx file."""
        missing: list[str] = []
        for rel in load_nav_pages():
            stem = rel[: rel.rfind(".")] if "." in rel else rel
            if not (DOCS_DIR / f"{stem}.md").is_file() and not (DOCS_DIR / f"{stem}.mdx").is_file():
                missing.append(rel)
        self.assertEqual([], missing)

    def test_tabs_are_the_mkdocs_groups(self) -> None:
        """Top-level tabs were not flattened."""
        tree = json.loads(NAV_JSON.read_text(encoding="utf-8"))
        titles = [tab["title"] for tab in tree]
        self.assertEqual(
            ["Home", "Learn", "Get started", "Studio", "Operate", "Reference", "Contribute"],
            titles,
        )


class LeftoverMkdocsTests(unittest.TestCase):
    """MkDocs-only syntax that Fumadocs prints as text must not remain."""

    def test_authored_pages_have_no_grid_cards(self) -> None:
        """``<div class="grid cards">`` (escaped or not) is not a Fumadocs component."""
        leftover: list[str] = []
        for path in sorted(DOCS_DIR.rglob("*")):
            if path.suffix not in {".md", ".mdx"}:
                continue
            if "generated" in path.parts:
                continue
            if "grid cards" in path.read_text(encoding="utf-8"):
                leftover.append(path.relative_to(DOCS_DIR).as_posix())
        self.assertEqual([], leftover)


class FrontmatterTests(unittest.TestCase):
    """Authored navigable pages keep title, description, tags, and scan lists."""

    def test_hand_written_pages_have_chrome(self) -> None:
        """Frontmatter + What's on this page / What this enables."""
        missing: list[str] = []
        for rel in hand_written_nav_pages():
            text = page_source(rel)
            if not FRONTMATTER_RE.match(text):
                missing.append(f"{rel}: missing YAML frontmatter")
                continue
            for needle in (
                TITLE_RE,
                DESCRIPTION_RE,
                TAGS_RE,
            ):
                if not needle.search(text):
                    missing.append(f"{rel}: missing {needle.pattern}")
            if "**What's on this page**" not in text:
                missing.append(f"{rel}: missing What's on this page")
            if "**What this enables**" not in text:
                missing.append(f"{rel}: missing What this enables")
        self.assertEqual([], missing)


class FenceTests(unittest.TestCase):
    """Fences keep a language tag; mermaid labels stay quoted."""

    def test_fences_have_languages(self) -> None:
        """Every fence on authored pages names a language (or mermaid/ezcmd)."""
        missing: list[str] = []
        for rel in hand_written_nav_pages():
            text = page_source(rel)
            in_fence = False
            marker = ""
            marker_len = 0
            for i, line in enumerate(text.splitlines(), start=1):
                match = FENCE_OPEN_RE.match(line)
                if not match:
                    continue
                fence = match.group(1)
                info = match.group(2) or ""
                if not in_fence:
                    in_fence = True
                    marker = fence[0]
                    marker_len = len(fence)
                    if not info.strip() and len(fence) <= 3:
                        missing.append(f"{rel}:{i}: fence with no language")
                elif fence[0] == marker and len(fence) >= marker_len:
                    in_fence = False
        self.assertEqual([], missing)

    def test_mermaid_labels_do_not_use_unquoted_braces(self) -> None:
        """Unquoted {{ in a mermaid node label fails in the browser."""
        bad: list[str] = []
        for rel in hand_written_nav_pages():
            text = page_source(rel)
            if MERMAID_FENCE_RE.search(text) and BAD_MERMAID_LABEL_RE.search(text):
                bad.append(rel)
        self.assertEqual([], bad)


class NextExportMemoryTests(unittest.TestCase):
    """Production export uses webpack and one static-generation worker."""

    def test_package_json_build_scripts_use_webpack(self) -> None:
        """Turbopack static generation OOMs GitHub's 7 GB runner (~850 pages)."""
        manifest = json.loads((SITE_DIR / "package.json").read_text(encoding="utf-8"))
        for name in ("build", "build:latest", "build:development"):
            script = manifest["scripts"][name]
            self.assertIn("next build --webpack", script, name)

    def test_next_config_limits_static_generation_workers(self) -> None:
        """One worker plus webpack memory opts keep the export under 7 GB."""
        text = (SITE_DIR / "next.config.ts").read_text(encoding="utf-8")
        self.assertIn("cpus: 1", text)
        self.assertIn("staticGenerationMaxConcurrency: 1", text)
        self.assertIn("webpackBuildWorker: false", text)
        self.assertIn("webpackMemoryOptimizations: true", text)
        self.assertIn("enablePrerenderSourceMaps: false", text)
        self.assertIn('serverExternalPackages: ["fumadocs-mdx", "shiki"]', text)

    def test_mdx_collection_compiles_on_demand(self) -> None:
        """Webpack must not bundle ~850 MDX files; the Config API compiles per page."""
        config = (SITE_DIR / "source.config.ts").read_text(encoding="utf-8")
        self.assertIn("defineDocs", config)
        self.assertIn("dynamic: true", config)
        self.assertNotRegex(config, r'''from ["']fumadocs-mdx/macro["']''')
        content = (SITE_DIR / "lib" / "content.ts").read_text(encoding="utf-8")
        self.assertNotRegex(content, r'''from ["']fumadocs-mdx/macro["']''')
        source = (SITE_DIR / "lib" / "source.ts").read_text(encoding="utf-8")
        self.assertIn(".source/dynamic", source)
        page = (SITE_DIR / "app" / "[[...slug]]" / "page.tsx").read_text(encoding="utf-8")
        self.assertRegex(page, r"await[\s\S]*\.load\(")


class ThemeTests(unittest.TestCase):
    """Voltage tokens, no Material indigo."""

    def test_global_css_uses_voltage_not_indigo(self) -> None:
        """Overeazy Voltage tokens are present; Material primary is not used."""
        css = (SITE_DIR / "app" / "global.css").read_text(encoding="utf-8")
        self.assertIn("--color-fd-background: #f5f2ee", css)
        self.assertIn("--color-fd-primary: #c46e16", css)
        self.assertIn("#e89424", css)
        self.assertIn(".ez-table-pin", css)
        self.assertNotIn("--md-primary-fg-color", css)


class ExportTests(unittest.TestCase):
    """Optional checks against docs-site/out/."""

    def test_export_has_index_when_built(self) -> None:
        """If an export exists, the home page is there."""
        if not EXPORT_DIR.is_dir():
            self.skipTest("docs-site/out/ not built")
        self.assertTrue((EXPORT_DIR / "index.html").is_file())


def main() -> int:
    """Run the suite.

    Returns:
        unittest status.
    """
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

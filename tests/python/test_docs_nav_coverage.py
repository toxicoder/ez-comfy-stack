"""Every public docs page is listed in mkdocs.yml nav.

Hermetic: stdlib. No MkDocs build.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MKDOCS = ROOT / "mkdocs.yml"
DOCS = ROOT / "docs"
WORKFLOW_MANIFEST = DOCS / "generated" / "workflows" / "manifest.json"
CINEMA_MANIFEST = DOCS / "generated" / "cinema" / "manifest.json"

# Python / JS / CSS / hooks are not nav pages.
SKIP_SUFFIXES = {".py", ".js", ".css"}
SKIP_NAMES = {"requirements.txt"}


def _nav_targets(nav_text: str) -> set[str]:
    """Collect ``path.md`` entries from the MkDocs nav block.

    Args:
        nav_text: mkdocs.yml contents.

    Returns:
        Relative paths as written in nav (posix).
    """
    targets: set[str] = set()
    in_nav = False
    for line in nav_text.splitlines():
        if line.startswith("nav:"):
            in_nav = True
            continue
        if in_nav and line and not line.startswith((" ", "\t", "-")):
            break
        if not in_nav:
            continue
        if ".md" not in line:
            continue
        _, _, rest = line.partition(":")
        path = rest.strip()
        if path.endswith(".md"):
            targets.add(path)
    return targets


def _workflow_manifest_paths() -> set[str]:
    """Return generated workflow page paths from the generator manifest.

    Returns:
        Repo-relative docs paths listed in the manifest. Empty when the
        generator has not been run yet.
    """
    if not WORKFLOW_MANIFEST.is_file():
        return set()
    payload = json.loads(WORKFLOW_MANIFEST.read_text(encoding="utf-8"))
    paths: set[str] = set()
    for row in payload.get("pages") or []:
        if isinstance(row, dict):
            path = row.get("path")
            if isinstance(path, str) and path.endswith(".md"):
                paths.add(path)
    return paths


def _cinema_manifest_paths() -> set[str]:
    """Return generated cinema catalog page paths.

    Returns:
        Docs-relative paths listed in the cinema manifest.
    """
    if not CINEMA_MANIFEST.is_file():
        return set()
    payload = json.loads(CINEMA_MANIFEST.read_text(encoding="utf-8"))
    paths: set[str] = set()
    for row in payload.get("pages") or []:
        if isinstance(row, dict):
            path = row.get("path")
            if isinstance(path, str) and path.endswith(".md"):
                paths.add(path)
    return paths


def test_mkdocs_nav_lists_every_docs_markdown_page() -> None:
    """Every docs/**/*.md page appears in nav (no orphan pages).

    Generated workflow-details pages are injected at MkDocs ``on_config``
    from ``docs/generated/workflows/manifest.json`` rather than 90+
    hand-listed nav lines. Cinema catalogs inject from
    ``docs/generated/cinema/manifest.json``.
    """
    nav = MKDOCS.read_text(encoding="utf-8")
    listed = _nav_targets(nav) | _workflow_manifest_paths() | _cinema_manifest_paths()
    pages = sorted(
        p.relative_to(DOCS).as_posix()
        for p in DOCS.rglob("*.md")
        if p.name not in SKIP_NAMES
    )
    missing = [p for p in pages if p not in listed]
    extra = sorted(listed - set(pages))
    assert missing == [], "docs pages missing from mkdocs.yml nav:\n" + "\n".join(missing)
    assert extra == [], "nav entries with no markdown file:\n" + "\n".join(extra)


def test_nav_includes_planned_homes() -> None:
    """Coverage homes from the docs enhancement plan are in nav."""
    nav = MKDOCS.read_text(encoding="utf-8")
    listed = _nav_targets(nav)
    required = (
        "learn/architecture.md",
        "start/faq.md",
        "start/when-to-use-vs-spark-lab.md",
        "create/workflows-stills.md",
        "create/workflows-motion.md",
        "create/workflows-creator.md",
        "create/workflows-film.md",
        "create/workflows-audio.md",
        "create/workflows-index.md",
        "reference/workflow-nodes.md",
        "create/music-rap.md",
        "create/music-edm.md",
        "create/music-disclosure.md",
        "reference/custom-nodes.md",
        "reference/config-and-schemas.md",
        "reference/studio-ui.md",
        "operate/occupancy-matrix.md",
        "operate/mcp.md",
        "operate/backup-restore.md",
        "operate/models-tokens.md",
        "operate/models-sharing.md",
        "operate/models-packs.md",
        "operate/troubleshooting-docs-site.md",
        "operate/troubleshooting-canvas.md",
        "operate/troubleshooting-host-docker.md",
        "operate/troubleshooting-downloads.md",
        "operate/troubleshooting-start-runtime.md",
        "operate/troubleshooting-models-workflows.md",
        "generated/shell/reference.md",
        "contribute/docs-style.md",
        "contribute/testing-docs.md",
        "contribute/contributing.md",
        "contribute/security.md",
    )
    missing = [p for p in required if p not in listed]
    assert missing == [], "planned pages missing from nav:\n" + "\n".join(missing)

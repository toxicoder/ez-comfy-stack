"""Every public docs page is listed in docs-site/lib/nav.json.

Hermetic: stdlib. No Next build.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAV_JSON = ROOT / "docs-site" / "lib" / "nav.json"
DOCS = ROOT / "docs"
WORKFLOW_MANIFEST = DOCS / "generated" / "workflows" / "manifest.json"
CINEMA_MANIFEST = DOCS / "generated" / "cinema" / "manifest.json"
AUDIO_MANIFEST = DOCS / "generated" / "audio" / "manifest.json"

# Python / JS / CSS / hooks are not nav pages.
SKIP_SUFFIXES = {".py", ".js", ".css"}
SKIP_NAMES = {"requirements.txt"}


def _nav_targets_from_json(payload: object) -> set[str]:
    """Collect page paths from nested nav.json nodes.

    Args:
        payload: Parsed nav.json (list of tabs).

    Returns:
        Relative paths as written in nav (posix), including ``.mdx``.
    """
    targets: set[str] = set()

    def walk(nodes: object) -> None:
        if isinstance(nodes, list):
            for node in nodes:
                walk(node)
            return
        if not isinstance(nodes, dict):
            return
        path = nodes.get("path")
        if isinstance(path, str) and path.endswith((".md", ".mdx")):
            targets.add(path)
        pages = nodes.get("pages")
        if isinstance(pages, list):
            walk(pages)

    walk(payload)
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


def _audio_manifest_paths() -> set[str]:
    """Return generated audio catalog page paths.

    Returns:
        Docs-relative paths listed in the audio manifest.
    """
    if not AUDIO_MANIFEST.is_file():
        return set()
    payload = json.loads(AUDIO_MANIFEST.read_text(encoding="utf-8"))
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
    ``docs/generated/cinema/manifest.json``. Audio catalogs inject from
    ``docs/generated/audio/manifest.json``. Cinema technique clip pages are
    linked from axis tables and stay off nav.
    """
    nav = json.loads(NAV_JSON.read_text(encoding="utf-8"))
    listed = (
        {p.replace(".mdx", ".md") for p in _nav_targets_from_json(nav)}
        | _workflow_manifest_paths()
        | _cinema_manifest_paths()
        | _audio_manifest_paths()
    )
    pages = sorted(
        p.relative_to(DOCS).as_posix().replace(".mdx", ".md")
        for p in list(DOCS.rglob("*.md")) + list(DOCS.rglob("*.mdx"))
        if p.name not in SKIP_NAMES
        # Technique clip pages live under generated/cinema/<axis>/<id>.md
        # and are linked from axis tables, not the sidebar.
        and not (p.parent.parent.name == "cinema" and p.parent.name != "cinema")
    )
    missing = [p for p in pages if p not in listed]
    extra = sorted(listed - set(pages))
    assert missing == [], "docs pages missing from nav.json:\n" + "\n".join(missing)
    assert extra == [], "nav entries with no markdown file:\n" + "\n".join(extra)


def test_nav_includes_planned_homes() -> None:
    """Coverage homes from the docs enhancement plan are in nav."""
    nav = json.loads(NAV_JSON.read_text(encoding="utf-8"))
    listed = {p.replace(".mdx", ".md") for p in _nav_targets_from_json(nav)}
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

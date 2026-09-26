"""Operator docs must match the current Klein 4B / Wan 5B / LTX-2.5 CLI.

Hermetic: stdlib only. No MkDocs, network, Docker, or GPU.
Catches the Flux-9B / LTX-2.3 / download-flux.sh drift that survived the
US-safe studio cutover.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
README = ROOT / "README.md"

# Stale CLI / graph / encoder names that are not the lab default.
# licenses.md and conventions.md may still mention Klein 9B or frozen
# flux-to-ltx* tags as banned/historical - those files are excluded from
# the full GHCR-tag ban below.
FORBIDDEN_EVERYWHERE = (
    "download-flux.sh",
    "qwen_3_8b_fp4mixed",
    "flux-draft-lab-example",
    "flux-hero-lab-example",
    "flux-studio-lab-example",
    "--tier companions",
    "still-studio-lab-example",
    "still-app-lab-example",
    "wan-shot-lab-example",
    "wan-i2v-draft-lab-example",
    "wan-t2v-draft-lab-example",
    "bridge-wan-lab-example",
    "bridge-ltx-lab-example",
    "ltx-i2v-hero-lab-example",
    "ltx-t2v-hero-lab-example",
)

# Current-tag form only. "Old flux-to-ltx* tags freeze" in conventions is allowed.
FORBIDDEN_CURRENT_IMAGE_TAG = "ghcr.io/toxicoder/ez-comfy:flux-to-ltx"

# Pages that describe the default stack (not the license ban list).
DEFAULT_STACK_PAGES = (
    DOCS / "index.md",
    DOCS / "getting-started.md",
    DOCS / "visual-generative-ai.md",
    DOCS / "models-and-cache.md",
    DOCS / "learn" / "index.md",
    DOCS / "learn" / "pipeline.md",
    README,
)

REQUIRED_DEFAULT_SNIPPETS = (
    "Klein 4B",
    "Wan 2.2",
    "LTX-2.5",
)


def _operator_doc_paths() -> list[Path]:
    paths = sorted(list(DOCS.rglob("*.md")) + list(DOCS.rglob("*.mdx")))
    paths.append(README)
    return paths


def _read(path: Path) -> str:
    if not path.is_file():
        alt = path.with_suffix(".mdx") if path.suffix == ".md" else path.with_suffix(".md")
        if alt.is_file():
            path = alt
    assert path.is_file(), path
    return path.read_text(encoding="utf-8")


def test_operator_docs_drop_stale_cli_and_graph_names() -> None:
    hits: list[str] = []
    for path in _operator_doc_paths():
        text = _read(path)
        rel = path.relative_to(ROOT)
        for needle in FORBIDDEN_EVERYWHERE:
            if needle in text:
                hits.append(f"{rel}: {needle!r}")
        if FORBIDDEN_CURRENT_IMAGE_TAG in text:
            # Allow an explicit "frozen / old" sentence, not a current-tag table.
            for line in text.splitlines():
                if FORBIDDEN_CURRENT_IMAGE_TAG not in line:
                    continue
                lower = line.lower()
                if "freeze" in lower or "frozen" in lower or "old " in lower:
                    continue
                hits.append(f"{rel}: current-tag {FORBIDDEN_CURRENT_IMAGE_TAG!r} in {line.strip()!r}")
    assert hits == [], "stale operator-doc strings:\n" + "\n".join(hits)


def test_default_stack_pages_name_klein_wan_ltx() -> None:
    for path in DEFAULT_STACK_PAGES:
        text = _read(path)
        for snippet in REQUIRED_DEFAULT_SNIPPETS:
            assert snippet in text, f"{path.name} missing default-stack snippet {snippet!r}"


def test_index_default_table_is_not_klein_9b() -> None:
    text = _read(DOCS / "index.md")
    # The home "Default stack" table must not advertise 9B / LTX-2.3 as the profile.
    assert "Klein 9B NVFP4" not in text
    assert "LTX-2.3 distilled FP8" not in text or "not a default" in text.lower()


def test_models_and_cache_uses_download_image_not_flux() -> None:
    text = _read(DOCS / "models-and-cache.md")
    assert "download-image.sh" in text
    assert "download-wan.sh" in text
    assert "download-ltx.sh" in text
    assert "download-llm.sh" in text
    assert "--tier 2.5" in text
    assert "us-safe-studio" in text


def test_getting_started_session_vars_and_port_forward() -> None:
    text = _read(DOCS / "getting-started.md")
    for var in (
        "SPARK_HOST",
        "MODELS_DIR",
        "COMFY_OUTPUT_DIR",
        "COMFY_PORT",
        "ssh -L",
    ):
        assert var in text, f"getting-started.md missing {var!r}"
    assert "<spark-ip>" not in text


def test_mkdocs_nav_is_grouped_journey() -> None:
    nav = json.loads((ROOT / "docs-site" / "lib" / "nav.json").read_text(encoding="utf-8"))
    titles = [tab["title"] for tab in nav]
    for heading in ("Learn", "Get started", "Studio", "Operate", "Reference", "Contribute"):
        assert heading in titles, f"nav.json missing grouped tab {heading!r}"
    assert (
        titles.index("Learn")
        < titles.index("Get started")
        < titles.index("Studio")
        < titles.index("Operate")
        < titles.index("Reference")
        < titles.index("Contribute")
    )
    blob = json.dumps(nav)
    assert blob.index("getting-started.md") < blob.index("shorts.md")
    assert blob.index("licenses.md") < blob.index("shorts.md")
    assert blob.index("visual-generative-ai.md") < blob.index("prompting.md")
    assert blob.index("visual-generative-ai.md") < blob.index("studio-workflows.md")
    assert blob.index("glossary.md") < blob.index("getting-started.md")
    assert blob.index('"path": "operate/daily.md"') < blob.index('"path": "occupancy.md"')
    assert blob.index("models-and-cache.md") < blob.index("download-tiers.md")
    assert blob.index("download-tiers.md") < blob.index("download-limit.md")
    assert blob.index("download-limit.md") < blob.index("operate/models-packs.md")
    assert blob.index("operate/models-packs.md") < blob.index("operate/models-tokens.md")
    assert blob.index("manage-cli.md") > blob.index("operate/daily.md")
    assert "learn/occupancy.md" in blob


def test_fun_inp_pages_do_not_advertise_40gb_alone() -> None:
    """Fun InP operator size is ~47 GB; 40 GB is only the status floor."""
    hits: list[str] = []
    for path in _operator_doc_paths():
        text = _read(path)
        if "Fun InP" not in text and "fun-inp" not in text:
            continue
        if "47" in text:
            continue
        if re.search(r"~?\s*40\s*GB", text):
            hits.append(str(path.relative_to(ROOT)))
    assert hits == [], "Fun InP ~40 GB without 47 GB:\n" + "\n".join(hits)

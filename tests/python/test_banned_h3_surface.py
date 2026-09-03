"""MiniMax H3 must not remain as a download, graph, or operator command.

Hermetic: stdlib only. License docs may mention H3 as banned.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

GONE_FILES = (
    ROOT / "scripts" / "utilities" / "download-h3.sh",
    ROOT / "scripts" / "utilities" / "queue-h3-film.sh",
    ROOT / "docs" / "h3-films.md",
    ROOT / "tests" / "bats" / "download-h3.bats",
    ROOT / "tests" / "bats" / "queue-h3-film.bats",
    ROOT / "tests" / "python" / "test_h3_workflows.py",
    ROOT / "workflows" / "h3-go-see-90s-lab-example.json",
    ROOT / "workflows" / "h3-still-here-90s-lab-example.json",
    ROOT / "workflows" / "h3-switchyard-90s-lab-example.json",
    ROOT / "workflows" / "api" / "h3-shot-column.api.json",
)

BANNED_IN_WORKFLOWS = (
    "MiniMaxH3",
    "minimax_h3",
    "h3-go-see",
    "GO_SEE_90s_H3",
)


def test_h3_scripts_and_graphs_are_gone() -> None:
    missing = [str(p) for p in GONE_FILES if p.exists()]
    assert missing == [], missing


def test_workflow_json_has_no_h3_nodes() -> None:
    wf_root = ROOT / "workflows"
    hits: list[str] = []
    for path in wf_root.rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        for needle in BANNED_IN_WORKFLOWS:
            if needle in text:
                hits.append(f"{path.relative_to(ROOT)}:{needle}")
    assert hits == [], hits


def test_dockerfile_does_not_pin_for_minimax() -> None:
    text = (ROOT / "docker" / "Dockerfile").read_text(encoding="utf-8")
    assert "MiniMaxH3AddGuide" not in text
    assert "native H3" not in text

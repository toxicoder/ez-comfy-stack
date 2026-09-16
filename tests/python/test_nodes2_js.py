"""ez_* frontend JS is safe under ComfyUI Nodes 2.0 (Vue widgets)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"

PREVIEW_JS = (
    CUSTOM / "ez_prompt_enhance" / "js" / "ez_prompt_enhance.js",
    CUSTOM / "ez_research" / "js" / "ez_research.js",
    CUSTOM / "ez_dub" / "js" / "ez_dub_status.js",
)
INGEST_JS = CUSTOM / "ez_dub" / "js" / "ez_dub_ingest.js"


def test_preview_js_sets_widget_value_without_requiring_input_el() -> None:
    for path in PREVIEW_JS:
        body = path.read_text(encoding="utf-8")
        assert "widget.value = text" in body, path
        assert "if (widget.inputEl)" in body, path
        assert "onResize" not in body, path


def test_ingest_js_drops_litegraph_node_widget() -> None:
    body = INGEST_JS.read_text(encoding="utf-8")
    assert "node_widget" not in body
    assert 'addWidget("button"' in body
    assert "Upload media" in body

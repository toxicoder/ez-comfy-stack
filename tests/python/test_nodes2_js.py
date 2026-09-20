"""ez_* frontend JS is safe under ComfyUI Nodes 2.0 (Vue widgets)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"

PREVIEW_JS = (
    CUSTOM / "ez_prompt_enhance" / "js" / "ez_prompt_enhance.js",
    CUSTOM / "ez_research" / "js" / "ez_research.js",
    CUSTOM / "ez_studio_forge" / "js" / "ez_studio_forge.js",
    CUSTOM / "ez_dub" / "js" / "ez_dub_status.js",
)
INGEST_JS = CUSTOM / "ez_dub" / "js" / "ez_dub_ingest.js"


def test_preview_js_sets_widget_value_without_requiring_input_el() -> None:
    for path in PREVIEW_JS:
        body = path.read_text(encoding="utf-8")
        assert "widget.value = text" in body, path
        assert "if (widget.inputEl)" in body, path
        assert "onResize" not in body, path


def test_sample_picker_js_is_nodes2_safe() -> None:
    body = (
        CUSTOM / "ez_prompt_enhance" / "js" / "ez_prompt_enhance.js"
    ).read_text(encoding="utf-8")
    assert "bindSamplePicker" in body
    assert "widget.value = text" in body
    assert "if (widget.inputEl)" in body
    assert "onResize" not in body
    assert "node_widget" not in body


def test_sample_picker_js_filters_to_graph_catalog() -> None:
    """Visible combo is this graph's catalog; Python union must not leak back."""
    body = (
        CUSTOM / "ez_prompt_enhance" / "js" / "ez_prompt_enhance.js"
    ).read_text(encoding="utf-8")
    assert "_ezSampleLabels" in body
    assert "Object.defineProperty" in body
    assert "refreshComboInNodes" in body
    assert "syncAllSamplePickers" in body
    assert 'addEventListener("configured"' in body
    assert "FAMILY_FOR_MODE" in body
    assert "EZAppForge" in body
    assert "PREVIEW_SKIP" in body
    assert "if (!sampleWidget._ezSampleBound)" in body
    assert body.count("syncSample(node)") >= 2


def test_ingest_js_drops_litegraph_node_widget() -> None:
    body = INGEST_JS.read_text(encoding="utf-8")
    assert "node_widget" not in body
    assert 'addWidget("button"' in body
    assert "Upload media" in body


def test_every_frontend_js_file_is_nodes2_safe() -> None:
    files = sorted(CUSTOM.rglob("js/*.js")) + sorted(
        (ROOT / "docs" / "javascripts").glob("*.js")
    )
    assert files, "expected custom-node and docs JS"
    for path in files:
        body = path.read_text(encoding="utf-8")
        assert "node_widget" not in body, path
        assert "onResize" not in body, path


QUALITY_JS = CUSTOM / "ez_quality" / "js" / "ez_quality.js"
FORMAT_JS = (
    CUSTOM / "ez_image" / "js" / "ez_image_format.js",
    CUSTOM / "ez_image" / "js" / "ez_video_format.js",
)
STUDIO_APP_JS = CUSTOM / "ez_studio_app" / "js" / "ez_studio_app.js"


def test_quality_js_writes_vue_safe_widget_values_on_the_node_graph() -> None:
    body = QUALITY_JS.read_text(encoding="utf-8")
    assert "function setWidgetValue(node, widget, value)" in body
    assert "node.widgets_values" in body
    assert "setDirtyCanvas" in body
    assert "qualityNode.graph" in body or "node.graph" in body
    assert "ez-comfy.quality.last" in body
    assert "defaulted.set(graph" in body or "defaulted.set(" in body
    assert "lab_quality_caption" in body
    assert "applyQuality(value, node)" in body
    assert "localStorage.setItem" in body
    assert "localStorage.getItem" in body


def test_format_js_uses_vue_safe_widget_writes() -> None:
    for path in FORMAT_JS:
        body = path.read_text(encoding="utf-8")
        assert "function setWidgetValue(node, widget, value)" in body, path
        assert "node.widgets_values" in body, path
        assert "setDirtyCanvas" in body, path


def test_studio_app_banner_shows_description_and_wraps_help() -> None:
    body = STUDIO_APP_JS.read_text(encoding="utf-8")
    assert "lab_description" in body
    assert "lab_quality_caption" in body
    assert "white-space: normal" in body
    assert "text-overflow: unset" in body
    assert "overflow: visible" in body
    assert "height: auto" in body
    assert "ez-studio-app-desc-wrap" in body

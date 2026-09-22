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
    files = sorted(CUSTOM.rglob("js/*.js"))
    assert files, "expected custom-node JS"
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
    assert "node.widgets.map((item) => item.value)" not in body
    assert "widgets_values[idx]" in body


def test_quality_js_freezes_to_custom_on_overlay_edits() -> None:
    """User Steps/CFG/UNET edits select custom; overlay writes do not."""
    body = QUALITY_JS.read_text(encoding="utf-8")
    assert "function freezeQualityToCustom" in body
    assert "function bindOverlayWidget" in body
    assert "_ezQualityWatch" in body
    assert "nodeCreated" in body
    for name in ("steps", "cfg", "unet_name", "clip_name", "vae_name"):
        assert f'"{name}"' in body
    assert "CLIPLoader" in body
    assert "persistLastQuality" in body
    assert "applyingByGraph" in body
    assert "seedingByGraph" in body


def test_sample_picker_js_freezes_to_custom_on_prompt_edits() -> None:
    """Typed prompt/tags/lyrics/sources select Sample custom before Queue."""
    body = (
        CUSTOM / "ez_prompt_enhance" / "js" / "ez_prompt_enhance.js"
    ).read_text(encoding="utf-8")
    assert "function freezeSampleToCustom" in body
    assert "function freezeSampleIfPromptDiverged" in body
    assert "function bindTextWatchers" in body
    assert "_ezApplyingSample" in body
    assert "_ezPromptWatch" in body
    assert "beforeQueued" in body
    for name in ("prompt", "tags", "lyrics", "sources"):
        assert f'"{name}"' in body


def test_prompt_enhance_js_syncs_linked_clip_preview() -> None:
    """CLIPTextEncode Positive follows Prompt / Rewrite prompt and Queue."""
    body = (
        CUSTOM / "ez_prompt_enhance" / "js" / "ez_prompt_enhance.js"
    ).read_text(encoding="utf-8")
    assert "function linkedDestinations" in body
    assert "function setLinkedClipWidget" in body
    assert "function pushClipPreview" in body
    assert "function pushClipPreviewFromMessage" in body
    assert "function syncLinkedClipFromWidgets" in body
    assert "function bindClipPreview" in body
    assert "function bindEnhanceWatcher" in body
    assert "CLIPTextEncode" in body
    assert "TextEncodeAceStepAudio1.5" in body
    assert "widget.serialize = false" in body
    start = body.index("function setLinkedClipWidget")
    linked = body[start : body.index("\nfunction pushClipPreview")]
    assert "widget.options = widget.options || {}" in linked
    assert "widget.options.serialize = false" in linked
    assert "widget.serialize" not in linked
    assert "serializeValue" not in linked
    assert "widgets_values[idx]" in body
    assert "node.widgets.map((item) => item.value)" not in body
    assert "syncLinkedClipFromWidgets(node)" in body
    assert "pushClipPreviewFromMessage(this, message)" in body
    assert "enhance off" in body
    assert "bindClipPreview(this)" in body
    assert "if (widget.inputEl)" in body


def test_format_js_uses_vue_safe_widget_writes() -> None:
    for path in FORMAT_JS:
        body = path.read_text(encoding="utf-8")
        assert "function setWidgetValue(node, widget, value)" in body, path
        assert "node.widgets_values" in body, path
        assert "setDirtyCanvas" in body, path


def test_media_pick_js_is_nodes2_safe() -> None:
    body = (CUSTOM / "ez_image" / "js" / "ez_media_pick.js").read_text(encoding="utf-8")
    assert "Upload media" in body
    assert "Choose from outputs" in body
    assert "/ez_outputs/to-input" in body
    assert "EZOptionalImage" in body
    assert "LoadImage" in body
    assert "LoadAudio" in body
    assert "addWidget(\"button\"" in body
    assert "node_widget" not in body
    assert "onResize" not in body


def test_format_js_matches_input_ratio() -> None:
    body = (CUSTOM / "ez_image" / "js" / "ez_image_format.js").read_text(encoding="utf-8")
    assert "Match input" in body
    assert "size_mode" in body
    assert "applyMatchInput" in body


def test_video_format_js_writes_ltx_duration() -> None:
    body = (CUSTOM / "ez_image" / "js" / "ez_video_format.js").read_text(encoding="utf-8")
    assert "duration_s" in body
    assert "applyDuration" in body
    assert "ltxFramesForDuration" in body


def test_studio_app_banner_shows_description_and_wraps_help() -> None:
    body = STUDIO_APP_JS.read_text(encoding="utf-8")
    assert "lab_description" in body
    assert "lab_quality_caption" in body
    assert "white-space: normal" in body
    assert "text-overflow: unset" in body
    assert "overflow: visible" in body
    assert "height: auto" in body
    assert "ez-studio-app-desc-wrap" in body


def test_studio_app_banner_is_dismissable_and_minimizable() -> None:
    """Occupancy chip can collapse to a pill or close, and remembers that."""
    body = STUDIO_APP_JS.read_text(encoding="utf-8")
    assert "data-ez-chip-min" in body
    assert "data-ez-chip-close" in body
    assert "data-ez-chip-pill" in body
    assert "ez-comfy.studio-app-chip" in body
    assert "localStorage.setItem" in body
    assert "localStorage.getItem" in body
    assert 'data-state="min"' in body
    assert 'chipState === "closed"' in body

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
MODEL_CHECK_JS = CUSTOM / "ez_quality" / "js" / "ez_model_check.js"
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


def test_queue_hooks_are_synchronous_widget_level_only() -> None:
    """Frontend 1.52.7 invokes only widget.beforeQueued, synchronously.

    An extension-level beforeQueued never fires, and an async body suspends
    past serialization, so a queue-time decision made by either is dead code.
    """
    for path in sorted(CUSTOM.rglob("js/*.js")):
        body = path.read_text(encoding="utf-8")
        assert "async beforeQueued(" not in body, path
        assert "beforeQueued = async" not in body, path


def test_sample_picker_queue_freeze_is_synchronous_with_applied_row() -> None:
    """The queue freeze must not await a fetch; it uses the row syncSample applied."""
    body = (
        CUSTOM / "ez_prompt_enhance" / "js" / "ez_prompt_enhance.js"
    ).read_text(encoding="utf-8")
    assert "function freezeSampleIfPromptDivergedSync" in body
    assert "sampleWidget.beforeQueued = function ()" in body
    assert "freezeSampleIfPromptDivergedSync(node)" in body
    assert "node._ezSampleRow = row" in body
    assert "node._ezSampleCatalog = catalogId" in body


def test_prompt_enhance_queue_hook_resyncs_enhance_off_text() -> None:
    """Toggle Rewrite off without a callback and Queue still sends the source text."""
    body = (
        CUSTOM / "ez_prompt_enhance" / "js" / "ez_prompt_enhance.js"
    ).read_text(encoding="utf-8")
    assert "widget.beforeQueued = function ()" in body
    start = body.index("widget.beforeQueued = function ()")
    hook = body[start : body.index("\n}", start)]
    assert "syncLinkedClipFromWidgets(node)" in hook
    assert "restoreUnlinkedClipWidgets(node)" in hook
    assert "function restoreUnlinkedClipWidgets" in body
    assert "_ezClipPreviewDests" in body
    restore = body[body.index("function restoreUnlinkedClipWidgets") :]
    restore = restore[: restore.index("\n}\n")]
    assert "widget.options.serialize = true" in restore


def test_set_linked_clip_widget_positional_write_is_cliptextencode_only() -> None:
    """The ACE encoder restores widgets_values positionally; slot 0 is tags."""
    body = (
        CUSTOM / "ez_prompt_enhance" / "js" / "ez_prompt_enhance.js"
    ).read_text(encoding="utf-8")
    start = body.index("function setLinkedClipWidget")
    linked = body[start : body.index("\nfunction ", start + 1)]
    assert 'widgetName === "text"' in linked
    assert "CLIPTextEncode" in linked
    assert "widget.options.serialize = false" in linked
    assert "widget.serialize = false" not in linked
    assert "serializeValue" not in linked


def test_sync_negative_family_writes_widgets_values_slot() -> None:
    """Sibling Rewrite-negative copies must reach the App Mode widget store."""
    body = (
        CUSTOM / "ez_prompt_enhance" / "js" / "ez_prompt_enhance.js"
    ).read_text(encoding="utf-8")
    assert "function setNodeWidgetValue" in body
    start = body.index("function syncNegativeFamily")
    family = body[start : body.index("\n}\n", start)]
    assert "setNodeWidgetValue(other, widget, on)" in family
    assert "widget.callback()" not in family


def test_quality_js_keeps_queue_time_user_edits() -> None:
    """Overlay drift at Queue freezes Quality custom; nothing re-overwrites it."""
    body = QUALITY_JS.read_text(encoding="utf-8")
    assert "const overlayWrites = new WeakMap()" in body
    assert "function recordOverlayWrite" in body
    assert "function hasOverlayEdits" in body
    assert "function hasSnapshotEdits" in body
    assert "function applyOverlayWrite" in body
    assert "custom - kept your edits" in body
    start = body.index("widget.beforeQueued = function ()")
    hook = body[start : body.index("\n  };", start)]
    assert "applyQuality(widget.value, node)" in hook
    assert "freezeQualityToCustom(graph)" in hook
    assert "async" not in hook


def test_quality_js_overlay_writes_are_node_type_bound() -> None:
    """Mirror presets.apply_to_graph: KSampler steps/cfg, loaders by type.

    The tier table is imported from the generated module; the frontend must
    not re-declare a step, a CFG, or a weight filename of its own.
    """
    body = QUALITY_JS.read_text(encoding="utf-8")
    assert 'from "./ez_quality_presets.js"' in body
    for name in (
        "EZ_QUALITY_TABLE",
        "EZ_QUALITY_OWNED",
        "EZ_QUALITY_LABELS",
        "EZ_QUALITY_NAMED",
        "EZ_QUALITY_FIELDS",
    ):
        assert name in body, name
    assert "OVERLAY_FIELDS_BY_TYPE" in body
    assert "KSampler: [" in body
    assert "UNETLoader: [" in body
    assert "CLIPLoader: [" in body
    assert "VAELoader: [" in body
    assert "OVERLAY_WIDGETS_BY_TYPE" not in body
    assert "function resolveOverlay" not in body
    assert ".safetensors" not in body
    assert "_STEPS" not in body
    assert "_CFG" not in body
    # isFlux2Dev must match the underscore filename Python matches
    # (flux2_dev_fp8mixed.safetensors).
    start = body.index("function isFlux2Dev")
    pred = body[start : body.index("\n}\n", start)]
    assert "flux2_dev" in pred


def test_quality_js_combo_matches_the_queued_prompt() -> None:
    """Reverse derivation, no silent drops, and one value on every combo."""
    body = QUALITY_JS.read_text(encoding="utf-8")
    # the tier is read back out of the live widgets, per instance
    assert "function deriveQualityTier(graph, family)" in body
    assert "function collectOverlayInstances(graph)" in body
    assert "function agreeOn(entries, read)" in body
    assert "function overlayValues(graph, family, instances)" in body
    assert "function planTierWrites(graph, family, tier)" in body
    assert "function writeBlockReason(" in body
    # instances of one class that disagree match no tier and are not lab
    assert "DIVERGENT" in body
    for reason in ("not installed", "cannot swap", "widget not on graph"):
        assert reason in body, reason
    assert "Wan 14B is not overlaid" in body
    # a write with no prompt slot is a failed apply, never a shown value
    assert "function widgetSlotIndex(node, widget)" in body
    assert "has no prompt slot" in body
    # a widget that was missing retries once on the next configure
    assert "pendingApplies" in body
    assert "retryPendingApply(graph)" in body
    # every combo moves together, and muted lanes drive nothing
    assert "function setQualityOnAll(graph, value)" in body
    assert "setQualityOnAll(graph, EZ_QUALITY_CUSTOM)" in body
    assert "function isLiveNode(node)" in body
    assert "node.mode === 0" in body
    # captions name the swap the applied row performs
    assert "function tierCaption(family, tier)" in body
    start = body.index("function tierLabelFor(family, tier)")
    label = body[start : body.index("\n}\n", start)]
    assert "EZ_QUALITY_LABELS[family]" in label
    # re-derived on configure, on graph change, on widget edits, and at Queue
    assert "graphChanged(graph)" in body
    assert "syncQualityFromGraph(graph)" in body
    start = body.index("widget.beforeQueued = function ()")
    hook = body[start : body.index("\n  };", start)]
    assert "deriveQualityTier(graph, graphFamily(graph))" in hook
    assert "setQualityOnAll(graph, derived)" in hook
    assert "freezeQualityToCustom(graph)" in hook
    assert "applyQuality(widget.value, node)" in hook
    assert "async" not in hook
    assert "node.widgets.map((item) => item.value)" not in body


def test_format_js_queue_sync_keeps_user_size_and_single_slots() -> None:
    """Hand-edited width/height under a named Format freeze it to Custom."""
    for path in FORMAT_JS:
        body = path.read_text(encoding="utf-8")
        assert "function queueTimeFormatSync" in body, path
        assert "formatWidget.beforeQueued = function ()" in body, path
        assert "queueTimeFormatSync(node)" in body, path
        assert "_ezFormatApplied" in body, path
        assert "CUSTOM_LABEL" in body, path
        assert "node.widgets.map((item) => item.value)" not in body, path
        assert "widgets_values[idx]" in body, path
    video = (CUSTOM / "ez_image" / "js" / "ez_video_format.js").read_text(
        encoding="utf-8"
    )
    assert "applyDuration(node)" in video


def test_image_mode_queue_hook_stays_sync_and_skips_preview() -> None:
    """applyCategory moves to the category widget hook; preview never runs at Queue."""
    body = (CUSTOM / "ez_image" / "js" / "ez_image_mode.js").read_text(
        encoding="utf-8"
    )
    assert "categoryWidget.beforeQueued = function ()" in body
    start = body.index("categoryWidget.beforeQueued = function ()")
    hook = body[start : body.index("\n    };", start)]
    assert "applyCategory(node)" in hook
    assert "refreshPreview" not in hook
    assert "await" not in hook


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


def test_media_pick_js_mounts_every_reference_still_slot() -> None:
    """EZOptionalImage has three picker slots; each gets its own pair of buttons."""
    body = (CUSTOM / "ez_image" / "js" / "ez_media_pick.js").read_text(encoding="utf-8")
    assert 'widgets: ["filename", "filename_2", "filename_3"]' in body
    assert "spec.widgets || [spec.widget]" in body
    assert "named.length > 1" in body
    assert "upload:${widget.name}" in body
    assert "outputs:${widget.name}" in body
    assert "node_widget" not in body
    assert "onResize" not in body


def test_reference_input_js_is_nodes2_safe() -> None:
    """The reference card obeys the same widget-write and banned-token rules."""
    body = (
        CUSTOM / "ez_image" / "js" / "ez_reference_input.js"
    ).read_text(encoding="utf-8")
    assert "function setWidgetValue(node, widget, value)" in body
    assert "node.widgets_values" in body
    assert "setDirtyCanvas" in body
    assert 'addWidget("button"' in body
    assert "EZOptionalImage" in body
    assert "onRemoved" in body
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


def _model_check_fn(name: str) -> str:
    """Slice one top-level function out of the model-check frontend.

    Args:
        name: Function name.

    Returns:
        Source from its ``function`` keyword up to (not including) the
        closing brace at column zero.
    """
    body = MODEL_CHECK_JS.read_text(encoding="utf-8")
    start = body.index(f"function {name}(")
    return body[start : body.index("\n}\n", start)]


def test_model_check_js_mounts_the_report_failure_button() -> None:
    """Second button widget files the last verdict; both use the same idiom."""
    body = MODEL_CHECK_JS.read_text(encoding="utf-8")
    assert 'addWidget("button", "Check models", "check", () => {' in body
    assert 'addWidget("button", "Report failure", "report", () => {' in body
    assert "runOnNode(this)" in body
    assert "reportFailure(this)" in body
    assert body.count('addWidget("button", ') == 2
    assert "node_widget" not in body
    assert "onResize" not in body
    assert "window.alert" not in body
    assert "focus(" not in body


def test_model_check_js_caches_the_last_verdict_for_the_report() -> None:
    """The report reads a snapshot the check cached; it never re-fetches."""
    check = _model_check_fn("runOnNode")
    assert 'collectHints(app.graph)' in check
    assert "node._ezLastHints = hints;" in check
    assert "node._ezLastCheck = payload;" in check
    assert "node._ezLastCheck = { ok: false" in check
    assert "fetch(" not in check
    assert 'setStatus(node, "Checking models...")' in check
    assert 'payload.ok ? "Ready." : "Missing models."' in check
    assert "Check failed: ${err" in check


def test_model_check_js_reads_the_tier_off_the_visible_quality_node() -> None:
    """The check reports the combo the overlay acts on, not the first copy."""
    check = _model_check_fn("collectHints")
    assert "tierFromGraph(g)" in check
    assert 'ntype === "EZQuality"' not in check
    reader = _model_check_fn("tierFromGraph")
    assert "EZQuality" in reader
    assert "node.mode === 0" in reader


def test_model_check_js_reports_on_the_model_check_surface() -> None:
    """window.EzFeedback is reached lazily at click time, with an issues fallback."""
    body = MODEL_CHECK_JS.read_text(encoding="utf-8")
    assert 'const REPORT_SURFACE = "model-check";' in body
    assert 'const REPORT_KIND = "bug";' in body
    assert "kind: REPORT_KIND" in body
    assert "surface: REPORT_SURFACE" in body
    lazy = _model_check_fn("feedbackApi")
    assert "window.EzFeedback" in lazy
    assert "typeof window" in lazy
    report = _model_check_fn("reportFailure")
    assert "feedbackApi()" in report
    assert "fb.openReport(partial)" in report
    assert "openIssuesFallback(partial)" in report
    assert "await" not in report
    fallback = _model_check_fn("openIssuesFallback")
    assert "issues/new" in fallback
    assert "[${REPORT_SURFACE}]" in fallback
    assert "toxicoder/ez-comfy-stack" in body


def test_model_check_js_context_carries_identities_not_commands() -> None:
    """Missing packs are named by Need.pack; download commands never ship."""
    ctx = _model_check_fn("reportContext")
    assert "commands" not in ctx
    assert "cmd" not in ctx
    for label in (
        '"App"',
        '"Occupancy"',
        '"Quality preset"',
        '"Missing packs"',
        '"Present count"',
        '"Missing count"',
        '"Rewrite on"',
        '"Describe on"',
    ):
        assert label in ctx
    assert "hints.enhance_on" in ctx
    assert "hints.describe_on" in ctx
    assert "result.lab_rel" in ctx
    assert "result.quality" in ctx
    assert "row.pack" in _model_check_fn("missingPacks")
    assert "result.commands" not in MODEL_CHECK_JS.read_text(encoding="utf-8")


def test_model_check_js_summaries_tell_the_truth_about_a_pass() -> None:
    """A passed check still files, and says it passed."""
    summary = _model_check_fn("reportSummary")
    assert "Model check passed for" in summary
    assert "Model check failed for" in summary
    assert "Model check has not run for" in summary
    assert "!node._ezLastCheck" in summary


def test_model_check_js_records_every_check_failure_into_the_ring() -> None:
    """Three failure paths log to ez_feedback with the endpoint in detail."""
    body = MODEL_CHECK_JS.read_text(encoding="utf-8")
    assert body.count("recordCheckError(") == 4
    assert "ts: new Date().toISOString()" in body
    posted = _model_check_fn("postCheckHints")
    assert 'recordCheckError(empty.message, `POST ${CHECK_ENDPOINT}' in posted
    assert "fetch(apiUrl(CHECK_ENDPOINT)" in posted
    assert 'const CHECK_ENDPOINT = "/ez_quality/check";' in body
    assert body.count('"/ez_quality/check"') == 1
    assert "recordCheckError(text," in _model_check_fn("runOnNode")


def test_model_check_js_ring_entries_stay_one_line_and_command_free() -> None:
    """format_report is multiline and ends with Run: commands; the ring is not."""
    line = _model_check_fn("oneLine")
    assert 'split("\\n", 1)[0]' in line
    assert "replace(/\\s+/g, \" \")" in line
    assert "slice(0, limit - 3)" in line
    rec = _model_check_fn("recordCheckError")
    assert "oneLine(message, 160)" in rec
    assert "oneLine(detail ||" in rec
    assert "surface: REPORT_SURFACE" in rec
    assert "fb.recordError({" in rec

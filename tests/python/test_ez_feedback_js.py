"""Structure tests for the ez_feedback frontends.

No browser harness exists in this repo, so the JS is pinned by string and
structure assertions the way ``test_ez_outputs.py`` does it: the exports the
other packs call, the global, the class prefix, the mount strategy, the error
listeners, and the graph prefill.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "custom_nodes" / "ez_feedback" / "js"
CORE_JS = PACK / "ez_feedback_core.js"
CHROME_JS = PACK / "ez_feedback.js"
CSS = PACK / "ez_feedback.css"

EXPORTS = (
    "REPO",
    "MAX_HREF",
    "clip",
    "labelsFor",
    "buildTitle",
    "buildBody",
    "issueHref",
    "reportPayload",
    "recordError",
    "recentErrors",
    "configure",
    "getConfig",
    "openHandoff",
    "fileDirect",
    "openReport",
    "showBanner",
    "dismissBanner",
    "button",
)


def _core() -> str:
    """Core module source.

    Returns:
        ``ez_feedback_core.js`` contents.
    """
    return CORE_JS.read_text(encoding="utf-8")


def _chrome() -> str:
    """Chrome module source.

    Returns:
        ``ez_feedback.js`` contents.
    """
    return CHROME_JS.read_text(encoding="utf-8")


def _sheet() -> str:
    """Stylesheet source.

    Returns:
        ``ez_feedback.css`` contents.
    """
    return CSS.read_text(encoding="utf-8")


def test_pack_js_files_exist_and_are_banners_first() -> None:
    for path in (CORE_JS, CHROME_JS, CSS):
        assert path.is_file(), path
        assert path.read_text(encoding="utf-8").lstrip().startswith(("/*", "/**")), path


def test_core_exports_the_whole_contract() -> None:
    body = _core()
    for name in EXPORTS:
        exported = (
            f"export const {name}" in body
            or f"export function {name}" in body
            or f"export async function {name}" in body
        )
        assert exported, name
        assert f"{name}," in body, f"{name} missing from window.EzFeedback"


def test_core_sets_the_global_at_top_level() -> None:
    body = _core()
    assert "window.EzFeedback" in body
    assert body.rstrip().endswith("}")
    setup = body.rindex("window.EzFeedback")
    assert "function openReport" in body[:setup]


def test_core_has_zero_comfyui_imports() -> None:
    body = _core()
    assert "import " not in body
    assert "scripts/app.js" not in body
    assert "scripts/api.js" not in body
    assert "scripts/ui.js" not in body
    assert "registerExtension" not in body
    assert "extensionManager" not in body


def test_core_reuses_the_shared_vocabulary() -> None:
    body = _core()
    assert 'export const REPO = "toxicoder/ez-comfy-stack"' in body
    assert "export const MAX_HREF = 5500" in body
    assert '"## What happened"' in body
    assert '"## Steps"' in body
    assert '"## Expected"' in body
    assert '"## Actual"' in body
    assert '"## Context"' in body
    assert '"## Environment"' in body
    assert '"## Recent errors"' in body
    assert '"## Browser"' in body
    assert '"<!-- Replace this line. -->"' in body
    assert 'const LABELS = { bug: "bug", enhancement: "enhancement" };' in body
    assert "Bug report from " in body
    assert "Feature request from " in body


def test_core_degrades_in_the_pinned_order() -> None:
    body = _core()
    order = body.index("DEGRADE_ORDER = [")
    block = body[order : body.index("];", order)]
    assert block.index("BROWSER_HEADING") < block.index("ERRORS_HEADING") < block.index(
        "ENVIRONMENT_HEADING"
    )
    assert "dropTraceback" in body
    assert "Traceback:" in body


def test_core_dialog_is_hand_rolled_and_accessibility_shaped() -> None:
    body = _core()
    for needle in (
        'setAttribute("role", "dialog")',
        'setAttribute("aria-modal", "true")',
        '"Escape"',
        "ez-fb-backdrop",
        "ez-fb-dialog",
        "ez-fb-textarea",
        "body.focus()",
    ):
        assert needle in body, needle
    assert "window.alert" not in body


def test_core_file_directly_is_token_gated() -> None:
    body = _core()
    assert '"File directly"' in body
    assert "direct.hidden = true" in body
    assert "cfg.tokenPresent" in body
    assert body.index("direct.hidden = true") < body.index("cfg.tokenPresent")
    assert '"Open on GitHub"' in body
    assert '"Copy markdown"' in body


def test_core_fetches_server_config_once_and_degrades() -> None:
    body = _core()
    assert '"/ez_feedback/config"' in body
    assert '"/ez_feedback/submit"' in body
    assert "if (!configPromise)" in body
    assert "async function fetchConfig" in body
    assert "catch" in body
    assert "__ezFeedbackApi" in body


def test_core_banner_is_dismissible_and_the_ring_is_five() -> None:
    body = _core()
    assert "ez-fb-banner" in body
    assert '"Dismiss"' in body
    assert '"Report"' in body
    assert "export function dismissBanner" in body
    assert "const RING_MAX = 5" in body
    assert "ring.unshift(row)" in body
    assert "return ring.slice()" in body


def test_core_writes_the_canonical_error_line_and_report_button() -> None:
    body = _core()
    assert 'const stamp = valueText(entry.ts) || "unknown";' in body
    assert 'const where = valueText(entry.surface) || valueText(surface) || "global";' in body
    assert '" [" +' in body
    assert "export function button(partial, label)" in body
    assert "openReport(partial)" in body


def test_chrome_imports_app_only_and_registers_the_extension() -> None:
    body = _chrome()
    assert 'import { app } from "../../scripts/app.js";' in body
    assert body.count("\nimport ") == 1
    assert 'name: "ez.feedback.chrome"' in body
    assert "async setup()" in body
    assert "scripts/ui.js" not in body


def test_chrome_mounts_both_header_buttons_and_keeps_them_mounted() -> None:
    body = _chrome()
    assert '"Report a bug"' in body
    assert '"Request a feature"' in body
    assert "[data-testid=linear-widgets]" in body
    assert "function ensureBar()" in body
    assert "function mountBar(el)" in body
    assert "new MutationObserver(" in body
    assert "observer.observe(document.body" in body
    assert "position: fixed" in _sheet() or "ez-fb-bar-fixed" in body


def test_chrome_prefills_from_the_live_graph() -> None:
    body = _chrome()
    for needle in (
        "lab_rel",
        "lab_app_mode",
        "lab_description",
        "lab_note",
        "lab_quality_caption",
        "lab_album",
        "lane",
        "occupancy",
        "default_view",
        "activeWorkflow",
        "graph.nodes",
    ):
        assert needle in body, needle
    assert 'addEventListener("configured"' in body
    assert "clip(" in body


def test_chrome_captures_errors_without_blocking() -> None:
    body = _chrome()
    assert 'addEventListener("execution_error"' in body
    assert 'addEventListener("execution_interrupted"' in body
    for key in (
        "prompt_id",
        "node_id",
        "node_type",
        "exception_message",
        "exception_type",
        "traceback",
        "current_inputs",
        "current_outputs",
    ):
        assert key in body, key
    assert ".detail" in body
    assert "recordError(" in body
    assert "showBanner(" in body
    assert "window.EzFeedback" in body
    assert "window.alert" not in body
    assert "app.extensionManager && app.extensionManager.toast" in body
    assert "typeof toast.addToast === \"function\"" in body


def test_chrome_reads_system_stats_best_effort() -> None:
    body = _chrome()
    assert "/system_stats" in body
    assert "torch_version" in body
    assert "cuda_version" in body
    assert '"GPU"' in body or "GPU" in body
    assert '"OS"' in body or "OS" in body


def test_chrome_and_core_are_nodes2_and_queue_safe() -> None:
    for body in (_core(), _chrome()):
        assert "node_widget" not in body
        assert "onResize" not in body
        assert "async beforeQueued(" not in body
        assert "beforeQueued = async" not in body


def test_css_is_class_prefixed_and_theme_safe() -> None:
    sheet = _sheet()
    assert ".ez-fb-bar" in sheet
    assert ".ez-fb-btn" in sheet
    assert ".ez-fb-dialog" in sheet
    assert ".ez-fb-banner" in sheet
    assert ".ez-fb-textarea" in sheet
    assert "ez-out-" not in sheet
    assert "focus-visible" in sheet
    assert "outline:" in sheet
    assert "z-index: 1081" in sheet
    assert "z-index: 1080" in sheet
    assert "z-index: 1070" in sheet
    assert "z-index: 40" in sheet
    assert "var(--comfy-menu-bg" in sheet
    assert "var(--fg-color" in sheet
    assert "var(--border-color" in sheet


def test_secrets_are_scrubbed_before_leaving_the_page() -> None:
    """Every report value is client-redacted, not just the server path.

    Report fields are operator- or graph-controlled, including a captured
    ``current_inputs``, so a token can arrive through a widget value or a
    traceback. The browser has no notion of a home directory, so only the
    secret-shaped runs are client-side; ``context.py`` still does both.
    """
    body = CORE_JS.read_text(encoding="utf-8")
    assert "(?:ghp|gho|github_pat|hf)_[A-Za-z0-9][A-Za-z0-9_-]{3,}" in body
    assert "export function redact(" in body
    assert '"[redacted]"' in body
    # The two choke points every report string passes through.
    assert "const text = redact(value)" in body
    assert "return redact(String(value))" in body


def test_href_never_outruns_the_github_url_limit() -> None:
    """A fat Context must not ship a 414 URI Too Long link.

    The section ladder cannot bound the URL on its own, so the tail is cut.
    """
    body = CORE_JS.read_text(encoding="utf-8")
    assert "[report trimmed to fit the GitHub URL limit]" in body
    assert "function fit(build, body)" in body
    assert "return build(fit(build, trimmed));" in body
    assert "if (build(body).length <= MAX_HREF)" in body


def test_file_direct_never_claims_a_link_it_does_not_have() -> None:
    """A 200 without a URL is not a filed issue."""
    body = CORE_JS.read_text(encoding="utf-8")
    assert "data.ok !== true" in body
    assert "!data.url" in body

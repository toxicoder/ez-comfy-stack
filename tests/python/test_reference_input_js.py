r"""The EZOptionalImage reference-still card ships preview, drop, reveal, mute.

Hermetic: stdlib text assertions. Does not execute JavaScript or need a browser.
The card is the only place a slot is revealed or cleared, so these tokens are
the operator-visible contract for the reference picker.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CARD_JS = ROOT / "custom_nodes" / "ez_image" / "js" / "ez_reference_input.js"
PICK_JS = ROOT / "custom_nodes" / "ez_image" / "js" / "ez_media_pick.js"


def _card() -> str:
    """Reference card frontend source.

    Returns:
        File contents.
    """
    return CARD_JS.read_text(encoding="utf-8")


def _pick() -> str:
    """Media picker frontend source.

    Returns:
        File contents.
    """
    return PICK_JS.read_text(encoding="utf-8")


def test_card_is_ascii_only() -> None:
    """Repo rule: committed text stays free of confusable Unicode."""
    assert _card().isascii()
    assert _pick().isascii()


def test_card_file_exists_and_registers() -> None:
    """The card is a registered frontend bound to the reference node."""
    body = _card()
    assert 'import { app } from "../../scripts/app.js"' in body
    assert 'import { api } from "../../scripts/api.js"' in body
    assert "app.registerExtension" in body
    assert 'name: "ez_image.referenceInput"' in body
    assert 'const NODE_CLASS = "EZOptionalImage"' in body
    assert "beforeRegisterNodeDef" in body
    assert "nodeCreated" in body
    assert "afterConfigureGraph" in body
    assert "nodeData?.name !== NODE_CLASS" in body


def test_card_imports_stay_inside_the_comfy_front_end() -> None:
    """No new dependency: only app.js and api.js, as every other card does."""
    imports = [
        line for line in _card().splitlines() if line.startswith("import ")
    ]
    assert imports == [
        'import { app } from "../../scripts/app.js";',
        'import { api } from "../../scripts/api.js";',
    ]


def test_card_covers_all_three_slots_and_the_toggle() -> None:
    """Every picker slot and the mute toggle are driven by the card."""
    body = _card()
    for slot in ('"filename"', '"filename_2"', '"filename_3"', '"use_references"'):
        assert slot in body, slot
    assert 'const MUTE_WIDGET = "use_references"' in body


def test_card_uploads_and_previews_through_comfy_routes() -> None:
    """Picks reach input/ through /upload/image and draw through /view."""
    body = _card()
    assert 'api.fetchApi("/upload/image"' in body
    assert 'body.append("image", file)' in body
    assert 'data.subfolder}/${path}' in body
    assert "/view?filename=" in body
    assert "type=input" in body
    assert "Date.now()" in body


def test_card_previews_each_slot_or_shows_a_placeholder() -> None:
    """An empty slot says so instead of showing a broken image."""
    body = _card()
    assert "function renderThumb(thumb, name)" in body
    assert 'img.src = inputViewUrl(name)' in body
    assert '"no reference still"' in body
    assert "querySelectorAll(\"[data-ez-ref-row]\")" in body


def test_card_supports_drag_and_drop() -> None:
    """Each slot is a drop target for an OS image file."""
    body = _card()
    for token in (
        "dragover",
        "dragenter",
        "dragleave",
        '"drop"',
        "DataTransfer",
        "event.dataTransfer",
        'startsWith("image/")',
    ):
        assert token in body, token
    assert 'event.dataTransfer.dropEffect = "copy"' in body
    assert "DROP_CLASS" in body
    assert "ez-ref-drop" in body
    assert "classList.add(DROP_CLASS)" in body


def test_card_progressive_disclosure_and_readout() -> None:
    """Unused slots hide, an add control reveals, and a status line reports."""
    body = _card()
    assert "function revealNext(node)" in body
    assert "function refreshCard(node)" in body
    assert "+ Add reference" in body
    assert 'addWidget("button"' in body
    assert "data-ez-ref-remove" in body
    assert "data-ez-ref-status" in body
    assert "row.hidden = !show" in body
    assert "computeSize" in body
    assert '"no reference still"' in body
    assert "Reference stills: ${filled} of ${slots.length}" in body
    assert "No reference still - Queue as is" in body
    assert "Reference stills muted" in body


def test_card_mute_only_mutes_and_a_pick_un_mutes() -> None:
    """use_references is the single mute; clearing picks stays an explicit act."""
    body = _card()
    assert "function isMuted(node)" in body
    assert "setWidgetValue(node, mute, true)" in body
    assert "function clearSlot(node, name)" in body
    assert 'setSlotValue(node, widgetByName(node, name), "")' in body
    assert body.count('setSlotValue(node, widgetByName(node, name), "")') == 1
    assert "clearSlot(node, name)" in body


def test_card_cleans_up_after_itself() -> None:
    """Per-node DOM is dropped when the node is removed and on a graph swap."""
    body = _card()
    assert "node._ezReferenceInputBound" in body
    assert "onRemoved" in body
    assert "document.getElementById(cardId(node))?.remove()" in body
    assert "function pruneCards()" in body
    assert "pruneCards()" in body
    assert "requestAnimationFrame" in body


def test_card_degrades_to_one_slot_on_an_older_graph() -> None:
    """A graph saved against the old definition has only the first widget."""
    body = _card()
    assert "function existingSlots(node)" in body
    assert "if (!widgetByName(node, SLOT_NAMES[0])) {" in body
    assert "slots.includes(name)" in body
    assert "slots.length === 0 || revealed >= slots.length" in body


def test_card_avoids_litegraph_canvas_apis() -> None:
    """Nodes 2.0 rule: no LiteGraph node_widget and no onResize hooks."""
    body = _card()
    for banned in ("node_widget", "onResize", "onDrawForeground", "LGraphWidget"):
        assert banned not in body, banned


def test_card_writes_widgets_the_vue_safe_way() -> None:
    """Widget writes go through the shared setWidgetValue shape."""
    body = _card()
    assert "function setWidgetValue(node, widget, value)" in body
    assert "node.widgets_values = node.widgets.map((item) => item.value)" in body
    assert "setDirtyCanvas" in body
    assert "widget.callback" in body
    assert "node.title =" not in body


def test_media_pick_mounts_buttons_on_every_reference_slot() -> None:
    """Each of the three slots gets its own upload and outputs control."""
    body = _pick()
    assert 'widgets: ["filename", "filename_2", "filename_3"]' in body
    assert "spec.widgets || [spec.widget]" in body
    assert "const named = slots.map((name) => widgetByName(node, name)).filter(Boolean)" in body
    assert "await uploadToInput(node, target, file)" in body
    assert "await chooseOutput(node, widget, picked)" in body
    assert "`Upload media${suffix}`" in body
    assert "`Choose from outputs${suffix}`" in body
    assert "upload:${widget.name}" in body
    assert "outputs:${widget.name}" in body


def test_media_pick_keeps_its_pinned_affordances() -> None:
    """The generalization must not drop the buttons other tests pin."""
    body = _pick()
    for token in (
        "Upload media",
        "Choose from outputs",
        "/ez_outputs/to-input",
        "EZOptionalImage",
        "LoadImage",
        "LoadAudio",
        'addWidget("button"',
    ):
        assert token in body, token
    assert "node_widget" not in body
    assert "onResize" not in body

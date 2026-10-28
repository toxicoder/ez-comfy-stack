/**
 * Reference stills card for EZOptionalImage: previews, drops, reveal, readout.
 *
 * Nodes 2.0: DOM card plus addWidget("button") and widget.value writes. Does
 * not touch LiteGraph canvas drawing and treats widget.inputEl as optional.
 * The use_references toggle stays the only mute; this card never clears a pick
 * by itself, it only reveals slots and clears the one slot the operator asks.
 */
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const NODE_CLASS = "EZOptionalImage";
const SLOT_NAMES = ["filename", "filename_2", "filename_3"];
const MUTE_WIDGET = "use_references";
const BATCH_INPUT = "image";
const STYLE_ID = "ez-reference-input-style";
const CARD_PREFIX = "ez-reference-input-";
const CARD_ATTR = "data-ez-ref-card";
const HOST_SELECTOR = "[data-testid=linear-widgets]";
const DROP_CLASS = "ez-ref-drop";
const NAME_LIMIT = 30;

const CARD_CSS = `
[data-ez-ref-card] {
  margin: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.16));
  background: var(--comfy-menu-bg, rgba(12, 16, 24, 0.92));
  color: var(--p-text-color, #e8eef7);
  font: 12px/1.45 ui-sans-serif, system-ui, sans-serif;
}
[data-ez-ref-card] [data-ez-ref-status] {
  display: block;
  margin-bottom: 6px;
}
[data-ez-ref-card] [data-ez-ref-note] {
  display: block;
  margin: 0 0 6px;
  color: #f2b8a8;
}
[data-ez-ref-card] [data-ez-ref-note][hidden] {
  display: none;
}
[data-ez-ref-card] [data-ez-ref-row] {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  margin-bottom: 6px;
  border-radius: 8px;
  border: 1px dashed rgba(255, 255, 255, 0.14);
}
[data-ez-ref-card] [data-ez-ref-row][hidden] {
  display: none;
}
[data-ez-ref-card] [data-ez-ref-row].ez-ref-drop {
  border-color: #6ea8fe;
  background: rgba(110, 168, 254, 0.16);
}
[data-ez-ref-card] [data-ez-ref-thumb] {
  flex: 0 0 56px;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.06);
  color: #9ab;
  text-align: center;
  cursor: pointer;
}
[data-ez-ref-card] [data-ez-ref-thumb] img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
[data-ez-ref-card] [data-ez-ref-name] {
  flex: 1 1 auto;
  min-width: 0;
  overflow-wrap: anywhere;
}
[data-ez-ref-card] button {
  flex: 0 0 auto;
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.18));
  background: var(--comfy-menu-bg, rgba(255, 255, 255, 0.08));
  color: inherit;
  font: inherit;
  cursor: pointer;
}
[data-ez-ref-card] [data-ez-ref-remove][hidden] {
  display: none;
}
`;

let remountScheduled = false;

/**
 * Escape text for the one innerHTML line this card renders.
 * @param {*} value
 * @returns {string}
 */
function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

/**
 * Find a widget by name on a node.
 * @param {object|undefined} node
 * @param {string} name
 * @returns {object|undefined}
 */
function widgetByName(node, name) {
  return node?.widgets?.find((item) => item.name === name);
}

/**
 * Set a combo value and notify Vue / App Mode.
 * @param {object} node
 * @param {object|undefined} widget
 * @param {*} value
 * @returns {void}
 */
function setWidgetValue(node, widget, value) {
  if (!widget) {
    return;
  }
  const values = widget.options?.values;
  if (Array.isArray(values) && value && !values.includes(value)) {
    values.push(value);
  }
  widget.value = value;
  if (node?.widgets) {
    node.widgets_values = node.widgets.map((item) => item.value);
  }
  if (typeof widget.callback === "function") {
    widget.callback(value, app.canvas, node);
  }
  const graph = node?.graph;
  if (graph && typeof graph.setDirtyCanvas === "function") {
    graph.setDirtyCanvas(true, true);
  }
}

/**
 * Trimmed pick for one slot, or "" when the slot is empty or missing.
 * @param {object|undefined} node
 * @param {string} name
 * @returns {string}
 */
function slotValue(node, name) {
  return String(widgetByName(node, name)?.value ?? "").trim();
}

/**
 * Slots this node actually has; an older saved graph has only the first.
 * @param {object|undefined} node
 * @returns {string[]}
 */
function existingSlots(node) {
  return SLOT_NAMES.filter((name) => Boolean(widgetByName(node, name)));
}

/**
 * How many slots the card shows: filled slots plus any the operator revealed.
 * @param {object} node
 * @param {string[]} slots
 * @returns {number}
 */
function revealCount(node, slots) {
  let needed = 0;
  slots.forEach((name, index) => {
    if (slotValue(node, name)) {
      needed = index + 1;
    }
  });
  const stored = Number(node._ezRefRevealed) || 0;
  return Math.min(slots.length, Math.max(needed, stored, 1));
}

/**
 * use_references is the single mute; an absent toggle is never muted.
 * @param {object} node
 * @returns {boolean}
 */
function isMuted(node) {
  const widget = widgetByName(node, MUTE_WIDGET);
  if (!widget) {
    return false;
  }
  const value = widget.value;
  return value === false || value === 0 || value === "false";
}

/**
 * True when the batch socket carries a link, so the readout stays honest.
 * @param {object} node
 * @returns {boolean}
 */
function hasWiredBatch(node) {
  const input = node?.inputs?.find((item) => item.name === BATCH_INPUT);
  if (!input) {
    return false;
  }
  // LiteGraph stores a single link id on inputs; some callers carry a list.
  return input.link != null || Boolean(input.links?.length);
}

/**
 * One-line state readout for the operator.
 * @param {object} node
 * @param {string[]} slots
 * @returns {string}
 */
function statusLine(node, slots) {
  if (isMuted(node)) {
    return "Reference stills muted";
  }
  const filled = SLOT_NAMES.filter((name) => Boolean(slotValue(node, name))).length;
  const wired = hasWiredBatch(node);
  if (!filled) {
    return wired
      ? "No reference still - queue the wired batch as is"
      : "No reference still - Queue as is";
  }
  const base = `Reference stills: ${filled} of ${slots.length}`;
  return wired ? `${base} plus a wired batch` : base;
}

/**
 * Shorten a long input path for the row label.
 * @param {string} value
 * @returns {string}
 */
function shorten(value) {
  return value.length > NAME_LIMIT ? `${value.slice(0, NAME_LIMIT)}...` : value;
}

/**
 * Input-folder preview URL with a cache-buster for a re-uploaded name.
 * @param {string} name
 * @returns {string}
 */
function inputViewUrl(name) {
  return (
    "/view?filename=" + encodeURIComponent(name) + "&type=input&_=" + Date.now()
  );
}

/**
 * Image files carried by a DataTransfer drop, filtered to image files only.
 * @param {DataTransfer|null|undefined} transfer
 * @returns {File[]}
 */
function transferImages(transfer) {
  const files = transfer?.files;
  if (!files || !files.length) {
    return [];
  }
  return Array.from(files).filter((file) =>
    String(file.type || "").startsWith("image/"),
  );
}

/**
 * Stable DOM id for one node's card.
 * @param {object|undefined} node
 * @returns {string}
 */
function cardId(node) {
  return CARD_PREFIX + String(node?.id ?? "x").replace(/[^A-Za-z0-9_-]/g, "-");
}

/**
 * Every EZOptionalImage on the live graph.
 * @returns {object[]}
 */
function refNodes() {
  return (app.graph?.nodes || []).filter(
    (node) => (node.comfyClass || node.type) === NODE_CLASS,
  );
}

/**
 * Reuse or inject the card stylesheet once per document.
 * @returns {void}
 */
function ensureStyle() {
  if (document.getElementById(STYLE_ID)) {
    return;
  }
  const style = document.createElement("style");
  style.id = STYLE_ID;
  style.textContent = CARD_CSS;
  document.head.appendChild(style);
}

/**
 * Keep the card in the App Mode linear panel, else in the document body.
 * @param {HTMLElement} card
 * @returns {void}
 */
function mountCard(card) {
  const host = document.querySelector(HOST_SELECTOR) || document.body;
  if (card.parentElement !== host) {
    host.appendChild(card);
  }
}

/**
 * Queue one cheap re-parent pass after a Vue re-render of the panel.
 * @returns {void}
 */
function scheduleRemount() {
  if (remountScheduled) {
    return;
  }
  remountScheduled = true;
  /**
   * Re-parent any card that lost its host; appends only, so it stays quiet.
   * @returns {void}
   */
  const run = function () {
    remountScheduled = false;
    for (const node of refNodes()) {
      const el = document.getElementById(cardId(node));
      if (el) {
        mountCard(el);
      }
    }
  };
  if (typeof window !== "undefined" && typeof window.requestAnimationFrame === "function") {
    window.requestAnimationFrame(run);
  } else {
    setTimeout(run, 100);
  }
}

/**
 * Repaint one slot thumbnail, or the no-still placeholder.
 * @param {HTMLElement} thumb
 * @param {string} name
 * @returns {void}
 */
function renderThumb(thumb, name) {
  if (thumb.dataset.ezRefName === name) {
    return;
  }
  thumb.dataset.ezRefName = name;
  while (thumb.firstChild) {
    thumb.removeChild(thumb.firstChild);
  }
  if (!name) {
    const gap = document.createElement("span");
    gap.textContent = "no reference still";
    thumb.appendChild(gap);
    thumb.removeAttribute("title");
    return;
  }
  const img = document.createElement("img");
  img.alt = name;
  img.src = inputViewUrl(name);
  thumb.appendChild(img);
  thumb.title = name;
}

/**
 * Collapse one widget on the canvas path while its slot stays unrevealed.
 * @param {object} widget
 * @param {boolean} show
 * @returns {void}
 */
function collapseWidget(widget, show) {
  const held = Object.prototype.hasOwnProperty.call(widget, "_ezRefComputeSize");
  if (show) {
    if (!held) {
      return;
    }
    if (widget._ezRefComputeSize) {
      widget.computeSize = widget._ezRefComputeSize;
    } else {
      delete widget.computeSize;
    }
    delete widget._ezRefComputeSize;
    return;
  }
  if (held) {
    return;
  }
  widget._ezRefComputeSize = Object.prototype.hasOwnProperty.call(widget, "computeSize")
    ? widget.computeSize
    : null;
  /**
   * Take the hidden slot out of the node's canvas layout.
   * @returns {number[]}
   */
  widget.computeSize = function () {
    return [0, -4];
  };
}

/**
 * Hide the widget for a slot the operator has not revealed; never a filled one.
 * @param {object} node
 * @param {string[]} slots
 * @param {number} revealed
 * @returns {void}
 */
function applyRevealToWidgets(node, slots, revealed) {
  slots.forEach((name, index) => {
    const widget = widgetByName(node, name);
    if (!widget) {
      return;
    }
    const show = index < revealed || Boolean(slotValue(node, name));
    widget.options = widget.options || {};
    widget.options.hidden = !show;
    collapseWidget(widget, show);
    const el = widget.inputEl || widget.parentEl;
    if (el?.style) {
      el.style.display = show ? "" : "none";
    }
  });
}

/**
 * Redraw the card for one node from the current widget values.
 * @param {object|undefined} node
 * @returns {void}
 */
function refreshCard(node) {
  if (!node) {
    return;
  }
  const card = document.getElementById(cardId(node));
  if (!card) {
    return;
  }
  mountCard(card);
  const slots = existingSlots(node);
  const revealed = revealCount(node, slots);
  const status = card.querySelector("[data-ez-ref-status]");
  if (status) {
    const html = `<strong>${escapeHtml(statusLine(node, slots))}</strong>`;
    if (status.innerHTML !== html) {
      status.innerHTML = html;
    }
  }
  const noteEl = card.querySelector("[data-ez-ref-note]");
  if (noteEl) {
    const text = String(node._ezRefNote || "");
    if (noteEl.textContent !== text) {
      noteEl.textContent = text;
    }
    noteEl.hidden = !text;
  }
  for (const row of card.querySelectorAll("[data-ez-ref-row]")) {
    const name = row.getAttribute("data-ez-ref-row") || "";
    const index = SLOT_NAMES.indexOf(name);
    const value = slotValue(node, name);
    const show = index >= 0 && index < revealed && slots.includes(name);
    if (row.hidden !== !show) {
      row.hidden = !show;
    }
    const thumb = row.querySelector("[data-ez-ref-thumb]");
    if (thumb) {
      renderThumb(thumb, value);
    }
    const nameEl = row.querySelector("[data-ez-ref-name]");
    if (nameEl) {
      const label = value ? shorten(value) : `Slot ${index + 1} - drop a still here`;
      if (nameEl.textContent !== label) {
        nameEl.textContent = label;
      }
    }
    const clear = row.querySelector("[data-ez-ref-remove]");
    if (clear) {
      clear.hidden = !value;
    }
  }
  const add = card.querySelector("[data-ez-ref-add]");
  if (add) {
    add.hidden = slots.length === 0 || revealed >= slots.length;
  }
  applyRevealToWidgets(node, slots, revealed);
}

/**
 * Repaint or lazily bind every reference node on the graph.
 * @returns {void}
 */
function refreshAll() {
  for (const node of refNodes()) {
    bindReferenceCard(node);
    refreshCard(node);
  }
}

/**
 * Drop cards whose node is gone, so a graph swap leaves nothing detached.
 * @returns {void}
 */
function pruneCards() {
  const keep = new Set(refNodes().map((node) => cardId(node)));
  for (const el of document.querySelectorAll(`[${CARD_ATTR}]`)) {
    if (!keep.has(el.id)) {
      el.remove();
    }
  }
}

/**
 * Show the next empty slot; a filled slot is never left hidden.
 * @param {object} node
 * @returns {void}
 */
function revealNext(node) {
  const slots = existingSlots(node);
  if (!slots.length) {
    return;
  }
  node._ezRefRevealed = Math.min(slots.length, revealCount(node, slots) + 1);
  node._ezRefNote = "";
  refreshCard(node);
}

/**
 * One-line operator note shown until the next pick, clear, or reveal.
 * @param {object} node
 * @param {string} text
 * @returns {void}
 */
function note(node, text) {
  node._ezRefNote = String(text || "");
  refreshCard(node);
}

/**
 * Write a slot; a pick always un-mutes so the readout stays honest.
 * @param {object} node
 * @param {object|undefined} widget
 * @param {string} value
 * @returns {void}
 */
function setSlotValue(node, widget, value) {
  if (!widget) {
    return;
  }
  setWidgetValue(node, widget, value);
  if (value && isMuted(node)) {
    const mute = widgetByName(node, MUTE_WIDGET);
    if (mute) {
      setWidgetValue(node, mute, true);
    }
  }
  node._ezRefNote = "";
  refreshCard(node);
}

/**
 * Clear one slot back to empty. The mute control never calls this.
 * @param {object} node
 * @param {string} name
 * @returns {void}
 */
function clearSlot(node, name) {
  setSlotValue(node, widgetByName(node, name), "");
}

/**
 * POST a local file to Comfy /upload/image and select the returned path.
 * @param {object} node
 * @param {object} widget
 * @param {File} file
 * @returns {Promise<void>}
 */
async function uploadToInput(node, widget, file) {
  const body = new FormData();
  body.append("image", file);
  const resp = await api.fetchApi("/upload/image", { method: "POST", body });
  if (resp.status !== 200) {
    throw new Error(`upload failed: ${resp.status}`);
  }
  const data = await resp.json();
  let path = data.name;
  if (data.subfolder) {
    path = `${data.subfolder}/${path}`;
  }
  setSlotValue(node, widget, path);
}

/**
 * Fill consecutive slots from a multi-file drop, skipping absent slots.
 * @param {object} node
 * @param {string} fromName
 * @param {File[]} files
 * @returns {Promise<void>}
 */
async function uploadIntoSlots(node, fromName, files) {
  const start = Math.max(0, SLOT_NAMES.indexOf(fromName));
  let index = start;
  for (const file of files.slice(0, SLOT_NAMES.length - start)) {
    const widget = widgetByName(node, SLOT_NAMES[index]);
    if (widget) {
      await uploadToInput(node, widget, file);
    }
    index += 1;
  }
}

/**
 * Wire drop, open, and remove on one slot row.
 * @param {object} node
 * @param {HTMLElement} row
 * @param {HTMLElement} thumb
 * @param {string} name
 * @returns {void}
 */
function bindRow(node, row, thumb, name) {
  row.addEventListener("dragenter", (event) => {
    if (!transferImages(event.dataTransfer).length) {
      return;
    }
    event.preventDefault();
    row.classList.add(DROP_CLASS);
  });
  row.addEventListener("dragover", (event) => {
    if (!transferImages(event.dataTransfer).length) {
      return;
    }
    event.preventDefault();
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = "copy";
    }
    row.classList.add(DROP_CLASS);
  });
  row.addEventListener("dragleave", () => {
    row.classList.remove(DROP_CLASS);
  });
  row.addEventListener("drop", async (event) => {
    event.preventDefault();
    row.classList.remove(DROP_CLASS);
    const files = transferImages(event.dataTransfer);
    if (!files.length) {
      note(node, "Drop an image file onto a reference slot");
      return;
    }
    try {
      await uploadIntoSlots(node, name, files);
    } catch (err) {
      note(node, `Drop failed: ${err && err.message ? err.message : err}`);
    }
  });
  thumb.addEventListener("click", () => {
    const value = slotValue(node, name);
    if (value) {
      window.open(inputViewUrl(value), "_blank", "noopener");
    }
  });
  thumb.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      thumb.click();
    }
  });
  const clear = row.querySelector("[data-ez-ref-remove]");
  if (clear) {
    clear.addEventListener("click", () => {
      clearSlot(node, name);
    });
  }
}

/**
 * Build one card row: thumbnail, filename, and a Remove control.
 * @param {object} node
 * @param {string} name
 * @returns {HTMLElement}
 */
function buildRow(node, name) {
  const row = document.createElement("div");
  row.dataset.ezRefRow = name;
  const thumb = document.createElement("div");
  thumb.dataset.ezRefThumb = "";
  thumb.setAttribute("role", "button");
  thumb.tabIndex = 0;
  thumb.setAttribute("aria-label", `Open reference still ${SLOT_NAMES.indexOf(name) + 1}`);
  const nameEl = document.createElement("span");
  nameEl.dataset.ezRefName = "";
  const clear = document.createElement("button");
  clear.type = "button";
  clear.dataset.ezRefRemove = "";
  clear.textContent = "Remove";
  row.append(thumb, nameEl, clear);
  bindRow(node, row, thumb, name);
  return row;
}

/**
 * Build and mount the card for one node, replacing any stale copy first.
 * @param {object} node
 * @returns {HTMLElement}
 */
function ensureCard(node) {
  ensureStyle();
  document.getElementById(cardId(node))?.remove();
  const card = document.createElement("div");
  card.id = cardId(node);
  card.setAttribute(CARD_ATTR, String(node?.id ?? ""));
  card.setAttribute("role", "group");
  card.setAttribute("aria-label", "Reference stills");
  const status = document.createElement("div");
  status.dataset.ezRefStatus = "";
  const noteEl = document.createElement("div");
  noteEl.dataset.ezRefNote = "";
  noteEl.hidden = true;
  const rows = document.createElement("div");
  rows.dataset.ezRefRows = "";
  for (const name of SLOT_NAMES) {
    rows.appendChild(buildRow(node, name));
  }
  const add = document.createElement("button");
  add.type = "button";
  add.dataset.ezRefAdd = "";
  add.textContent = "+ Add reference";
  add.addEventListener("click", () => {
    revealNext(node);
  });
  card.append(status, noteEl, rows, add);
  mountCard(card);
  return card;
}

/**
 * Watch widget callbacks so canvas and ez_outputs writes repaint the card.
 * @param {object} node
 * @returns {void}
 */
function bindWidgetWatchers(node) {
  for (const name of [MUTE_WIDGET, ...SLOT_NAMES]) {
    const widget = widgetByName(node, name);
    if (!widget || widget._ezRefWatched) {
      continue;
    }
    widget._ezRefWatched = true;
    const inner = widget.callback;
    /**
     * Pass the widget callback on, then repaint the readout.
     * @param {*} value
     * @param {object} canvas
     * @param {object} target
     * @returns {void}
     */
    widget.callback = function (value, canvas, target) {
      inner?.apply(this, [value, canvas, target]);
      refreshCard(node);
    };
  }
}

/**
 * Add the node-level reveal control once. Buttons stay out of widgets_values.
 * @param {object} node
 * @returns {void}
 */
function addRevealButton(node) {
  if (typeof node.addWidget !== "function" || node._ezReferenceAddWidget) {
    return;
  }
  const button = node.addWidget("button", "+ Add reference", "ezAddReference", () => {
    revealNext(node);
  });
  if (button) {
    button.serialize = false;
    node._ezReferenceAddWidget = button;
  }
}

/**
 * Bind the reference card once per node instance; safe on older graphs.
 * @param {object} node
 * @returns {void}
 */
function bindReferenceCard(node) {
  if (!node || node._ezReferenceInputBound) {
    return;
  }
  if (!widgetByName(node, SLOT_NAMES[0])) {
    return;
  }
  node._ezReferenceInputBound = true;
  node._ezRefRevealed = 0;
  node._ezRefNote = "";
  bindWidgetWatchers(node);
  addRevealButton(node);
  ensureCard(node);
  refreshCard(node);
  const onRemoved = node.onRemoved;
  /**
   * Drop the card and the bind flag when the node leaves the graph.
   * @returns {void}
   */
  node.onRemoved = function () {
    document.getElementById(cardId(node))?.remove();
    node._ezReferenceInputBound = false;
    node._ezReferenceAddWidget = null;
    node._ezRefNote = "";
    onRemoved?.apply(this, arguments);
  };
}

app.registerExtension({
  name: "ez_image.referenceInput",
  /**
   * Wrap EZOptionalImage so every created node gets the reference card.
   * @param {object} nodeType
   * @param {object} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData?.name !== NODE_CLASS) {
      return;
    }
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    /**
     * Bind the card after the node builds its widgets.
     * @returns {void}
     */
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      bindReferenceCard(this);
    };
  },
  /**
   * Bind nodes that appear after a load without a reload.
   * @param {object} node
   * @returns {void}
   */
  nodeCreated(node) {
    if ((node?.comfyClass || node?.type) === NODE_CLASS) {
      bindReferenceCard(node);
    }
  },
  /**
   * Show saved picks after a graph load and drop cards for nodes that are gone.
   * @returns {Promise<void>}
   */
  async afterConfigureGraph() {
    pruneCards();
    refreshAll();
  },
  /**
   * Repaint on execution and keep cards parented through Vue re-renders.
   * @returns {void}
   */
  setup() {
    pruneCards();
    if (api && typeof api.addEventListener === "function") {
      api.addEventListener("executed", () => {
        refreshAll();
      });
    }
    if (typeof MutationObserver !== "undefined" && document?.body) {
      const observer = new MutationObserver(scheduleRemount);
      observer.observe(document.body, { childList: true, subtree: true });
    }
  },
});

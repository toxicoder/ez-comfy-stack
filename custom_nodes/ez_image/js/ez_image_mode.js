/**
 * EZImageMode frontend: filter the Mode combo by Category.
 *
 * Nodes 2.0: writes widget.value. Python run() is the Queue source of truth
 * for Enhance context / mode / SaveImage prefix. An unknown mode falls back
 * in Python; this script only narrows the visible combo.
 */
import { app } from "../../scripts/app.js";

/**
 * One mode from the modes half of modes.json. The file reads every field
 * defensively with String(), so all of them stay optional.
 * @typedef {{id?: string, label?: string, category?: string}} EzModeRow
 */

/**
 * One category from the categories half of modes.json.
 * @typedef {{id?: string, label?: string}} EzCategoryRow
 */

/**
 * Widget on a desk node. ComfyUI invokes callback with the widget as ``this``
 * and beforeQueued right before the queue payload is serialized.
 * @typedef {{
 *   name: string,
 *   value?: string|number|null|undefined,
 *   options?: {values?: unknown[]},
 *   callback?: (
 *     this: EzWidget,
 *     value: unknown,
 *     canvas?: unknown,
 *     node?: EzNode
 *   ) => unknown,
 *   beforeQueued?: (this: EzWidget) => void,
 *   inputEl?: {readOnly?: boolean},
 *   _ezModeValuesBound?: boolean,
 *   _ezStudioWatch?: boolean
 * }} EzWidget
 */

/**
 * Graph handle used to walk nodes and dirty the canvas.
 * @typedef {{
 *   nodes?: EzNode[],
 *   setDirtyCanvas?: (dirtyCanvas: boolean, dirty: boolean) => void
 * }} EzGraph
 */

/**
 * Node on the still desk. --noResolve leaves the ComfyUI frontend untyped, so
 * only the members this file reads or writes are named.
 * @typedef {{
 *   type?: string,
 *   comfyClass?: string,
 *   widgets?: EzWidget[],
 *   widgets_values?: unknown[],
 *   graph?: EzGraph,
 *   _ezModeBound?: boolean,
 *   _ezModeLabels?: string[],
 *   _ezPreviewWrite?: boolean
 * }} EzNode
 */

/**
 * Widget values the preview route resolves, sent as the request body.
 * @typedef {{
 *   category: string|number|null|undefined,
 *   mode: string|number|null|undefined,
 *   iterate: string|number|null|undefined,
 *   filename: string|number|null|undefined,
 *   format: string|number|null|undefined,
 *   width: string|number|null|undefined,
 *   height: string|number|null|undefined,
 *   batch: string|number|null|undefined,
 *   size_mode: string|number|null|undefined,
 *   look: string|number|null|undefined,
 *   prompt: string|number|null|undefined,
 *   sample: string|number|null|undefined,
 *   style: string|number|null|undefined,
 *   rewrite: string|number|null|undefined,
 *   steps: string|number|null|undefined,
 *   cfg: string|number|null|undefined,
 *   unet: string|number|null|undefined,
 *   seed: string|number|null|undefined,
 *   seed_control: string|number|null|undefined,
 *   lab_rel: string
 * }} EzPreviewBody
 */

/**
 * Reply from /ez_image/studio-preview, or the local unavailable stub.
 * @typedef {{
 *   ok?: boolean,
 *   summary?: string,
 *   format_label?: string|number|null,
 *   width?: string|number|null,
 *   height?: string|number|null,
 *   batch?: string|number|null,
 *   enhance_mode?: string|number|null,
 *   hint?: string|number|null,
 *   prefix?: string|number|null
 * }} EzPreviewPayload
 */

/**
 * One file SaveImage reported in its execution message.
 * @typedef {{
 *   filename?: string,
 *   subfolder?: string,
 *   type?: string
 * }} EzSavedImage
 */

/**
 * Execution message handed to SaveImage's onExecuted hook.
 * @typedef {{images?: EzSavedImage[]}} EzExecutedMessage
 */

/**
 * Registered node definition, seen before ComfyUI registers it.
 * @typedef {{
 *   prototype: {
 *     onNodeCreated?: (this: EzNode, ...args: unknown[]) => void;
 *     onExecuted?: (this: EzNode, message: EzExecutedMessage) => void;
 *   }
 * }} EzNodeType
 */

/**
 * Node definition metadata; only the class name is read here.
 * @typedef {{name: string}} EzNodeDef
 */

let catalog = null;

/**
 * Find a widget by name on a node. A missing node is a miss, not a throw:
 * LiteGraph creates nodes one at a time, so a class this file walks can be
 * absent from the graph (or not built yet) while these bindings run.
 * @param {EzNode|undefined} node
 * @param {string} name
 * @returns {EzWidget|undefined}
 */
function widgetByName(node, name) {
  return node?.widgets?.find((w) => w.name === name);
}

/**
 * Catalog mode rows from the last successful fetch, or an empty list.
 * @returns {EzModeRow[]}
 */
function modeRows() {
  const rows = catalog?.modes;
  return Array.isArray(rows) ? rows : [];
}

/**
 * Catalog category rows, or an empty list.
 * @returns {EzCategoryRow[]}
 */
function categoryRows() {
  const rows = catalog?.categories;
  return Array.isArray(rows) ? rows : [];
}

/**
 * Resolve a combo value to a category id.
 * @param {string|number|null|undefined} value
 * @returns {string}
 */
function categoryId(value) {
  const raw = String(value || "").trim();
  const folded = raw.toLowerCase();
  for (const row of categoryRows()) {
    if (String(row.id) === raw || String(row.label).toLowerCase() === folded) {
      return String(row.id);
    }
  }
  const modes = modeRows();
  const hit = modes.find(
    (row) =>
      String(row.category) === raw ||
      String(row.category).split("_").join(" ").toLowerCase() === folded,
  );
  return hit ? String(hit.category) : String(modes[0]?.category || "");
}

/**
 * Mode labels in one category, file order.
 * @param {string|number|null|undefined} category
 * @returns {string[]}
 */
function labelsForCategory(category) {
  const cid = categoryId(category);
  return modeRows()
    .filter((row) => String(row.category) === cid)
    .map((row) => String(row.label));
}

/**
 * Bind a getter-only values list so refreshComboInNodes cannot restore the union.
 * @param {EzWidget} widget
 * @param {EzNode} node
 * @returns {void}
 */
function bindModeValues(widget, node) {
  if (!widget?.options) {
    widget.options = {};
  }
  if (widget._ezModeValuesBound) {
    return;
  }
  widget._ezModeValuesBound = true;
  try {
    delete widget.options.values;
  } catch {
    // NodeDef values may be non-configurable; defineProperty still wins.
  }
  Object.defineProperty(widget.options, "values", {
    configurable: true,
    enumerable: true,
    /**
     * Visible Mode labels for the current Category.
     * @returns {string[]}
     */
    get() {
      return node._ezModeLabels || [];
    },
    /**
     * Ignore refreshComboInNodes restoring the Python union.
     * @returns {void}
     */
    set() {},
  });
}

/**
 * Filter Mode to the selected Category; pick the first row when the current
 * value is not in that category.
 * @param {EzNode} node
 * @returns {void}
 */
function applyCategory(node) {
  const categoryWidget = widgetByName(node, "category");
  const modeWidget = widgetByName(node, "mode");
  if (!categoryWidget || !modeWidget) {
    return;
  }
  const labels = labelsForCategory(categoryWidget.value);
  node._ezModeLabels = labels.length ? labels : modeRows().map((row) => String(row.label));
  bindModeValues(modeWidget, node);
  const current = String(modeWidget.value || "");
  if (node._ezModeLabels.includes(current)) {
    return;
  }
  const next = node._ezModeLabels[0];
  if (!next || current === next) {
    return;
  }
  modeWidget.value = next;
  if (typeof modeWidget.callback === "function") {
    modeWidget.callback(next);
  }
}

/**
 * Bind category/mode callbacks on one EZImageMode node.
 * @param {EzNode} node
 * @returns {void}
 */
function bindModeNode(node) {
  const ntype = node?.comfyClass || node?.type || "";
  if (!node || ntype !== "EZImageMode") {
    return;
  }
  if (node._ezModeBound) {
    applyCategory(node);
    return;
  }
  node._ezModeBound = true;
  const categoryWidget = widgetByName(node, "category");
  const categoryCb = categoryWidget?.callback;
  if (categoryWidget) {
    /**
     * Filter Mode when Category changes.
     * @param {string|number|null|undefined} value
     * @returns {string|number|null|undefined}
     */
    categoryWidget.callback = function (value) {
      categoryCb?.apply(this, arguments);
      applyCategory(node);
      return value;
    };
    /**
     * Re-apply the Mode filter right before the queue payload is serialized.
     * Must stay synchronous: the pinned frontend calls widget.beforeQueued
     * inline and never invokes extension-level async beforeQueued hooks.
     * Reads only the cached catalog; never fetches, never refreshes preview.
     * @returns {void}
     */
    categoryWidget.beforeQueued = function () {
      if (!catalog || (!modeRows().length && !categoryRows().length)) {
        return;
      }
      applyCategory(node);
    };
  }
  applyCategory(node);
}

/**
 * Bind every EZImageMode node on the current graph.
 * @returns {void}
 */
function bindAll() {
  for (const node of app.graph?.nodes || []) {
    bindModeNode(node);
  }
}

/**
 * Load js/modes.json from this pack's WEB_DIRECTORY.
 * @returns {Promise<void>}
 */
async function loadCatalog() {
  if (catalog) {
    return;
  }
  try {
    const response = await fetch("/extensions/ez_image/modes.json");
    if (!response.ok) {
      catalog = { modes: [], categories: [] };
      return;
    }
    const payload = await response.json();
    if (Array.isArray(payload)) {
      catalog = { modes: payload, categories: [] };
      return;
    }
    if (payload && Array.isArray(payload.modes)) {
      catalog = payload;
      return;
    }
    catalog = { modes: [], categories: [] };
  } catch {
    catalog = { modes: [], categories: [] };
  }
}

const PREVIEW_UNAVAILABLE =
  "Preview unavailable - Queue still uses the nodes. Reload the App after pull if this stays.";
const PREVIEW_MS = 200;
let previewTimer = 0;

/**
 * Backend URL, honoring Comfy's api prefix when present.
 * @param {string} path
 * @returns {string}
 */
function apiUrl(path) {
  if (app.api && typeof app.api.apiURL === "function") {
    return app.api.apiURL(path);
  }
  return path;
}

/**
 * First node of a Comfy class on the open graph.
 * @param {string} typeName
 * @returns {EzNode|undefined}
 */
function nodeByType(typeName) {
  return (app.graph?.nodes || []).find((node) => {
    const ntype = node?.comfyClass || node?.type || "";
    return ntype === typeName;
  });
}

/**
 * True for Comfy booleans and yes/on strings.
 * @param {unknown} value
 * @returns {boolean}
 */
function isOn(value) {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    return Boolean(value);
  }
  if (typeof value === "string") {
    return ["1", "true", "yes", "on"].includes(value.trim().toLowerCase());
  }
  return Boolean(value);
}

/**
 * Write one widget slot. Does not rebuild the whole widgets_values list.
 * @param {EzNode|undefined} node
 * @param {EzWidget|undefined} widget
 * @param {string|number|null|undefined} value
 * @returns {void}
 */
function slotWrite(node, widget, value) {
  if (!node || !widget) {
    return;
  }
  const choices = widget.options?.values;
  if (Array.isArray(choices) && value && !choices.includes(value)) {
    choices.push(value);
  }
  if (widget.value === value) {
    return;
  }
  widget.value = value;
  if (Array.isArray(node.widgets_values) && node.widgets) {
    const idx = node.widgets.indexOf(widget);
    if (idx >= 0) {
      node.widgets_values[idx] = value;
    }
  }
  node._ezPreviewWrite = true;
  try {
    if (typeof widget.callback === "function") {
      widget.callback(value, app.canvas, node);
    }
  } finally {
    node._ezPreviewWrite = false;
  }
  const graph = node.graph || app.graph;
  if (graph && typeof graph.setDirtyCanvas === "function") {
    graph.setDirtyCanvas(true, true);
  }
}

/**
 * Widget value by node class and widget name.
 * @param {string} typeName
 * @param {string} widgetName
 * @returns {string|number|null|undefined}
 */
function widgetValue(typeName, widgetName) {
  const node = nodeByType(typeName);
  return widgetByName(node, widgetName)?.value;
}

/**
 * True when this graph is the universal still desk.
 * @returns {boolean}
 */
function isImageStudio() {
  if ((app.graph?.extra?.lab_rel || "") === "photos/image-studio") {
    return true;
  }
  return Boolean(nodeByType("EZImageMode"));
}

/**
 * Snapshot of the widgets the preview route resolves.
 * @returns {EzPreviewBody}
 */
function previewBody() {
  return {
    category: widgetValue("EZImageMode", "category"),
    mode: widgetValue("EZImageMode", "mode"),
    iterate: widgetValue("EZImageMode", "iterate"),
    filename: widgetValue("EZOptionalImage", "filename"),
    format: widgetValue("EZImageFormat", "format"),
    width: widgetValue("EZImageFormat", "width"),
    height: widgetValue("EZImageFormat", "height"),
    batch: widgetValue("EZImageFormat", "batch_size"),
    size_mode: widgetValue("EZImageFormat", "size_mode"),
    look: widgetValue("EZImageFormat", "look"),
    prompt: widgetValue("EZKleinPromptEnhance", "prompt"),
    sample: widgetValue("EZKleinPromptEnhance", "sample"),
    style: widgetValue("EZKleinPromptEnhance", "style"),
    rewrite: widgetValue("EZKleinPromptEnhance", "enhance"),
    steps: widgetValue("KSampler", "steps"),
    cfg: widgetValue("KSampler", "cfg"),
    unet: widgetValue("UNETLoader", "unet_name"),
    seed: widgetValue("KSampler", "seed"),
    seed_control: widgetValue("KSampler", "control_after_generate"),
    lab_rel: app.graph?.extra?.lab_rel || "photos/image-studio",
  };
}

/**
 * Copy resolved values onto the widgets Queue's links would otherwise hide.
 * @param {EzPreviewPayload} payload
 * @returns {void}
 */
function applyPreview(payload) {
  const modeNode = nodeByType("EZImageMode");
  const summary = widgetByName(modeNode, "run_summary");
  if (summary?.inputEl) {
    summary.inputEl.readOnly = true;
  }
  slotWrite(modeNode, summary, String(payload?.summary || PREVIEW_UNAVAILABLE));
  if (!payload?.ok) {
    return;
  }
  const formatNode = nodeByType("EZImageFormat");
  slotWrite(formatNode, widgetByName(formatNode, "format"), payload.format_label);
  slotWrite(formatNode, widgetByName(formatNode, "width"), payload.width);
  slotWrite(formatNode, widgetByName(formatNode, "height"), payload.height);
  const enhance = nodeByType("EZKleinPromptEnhance");
  slotWrite(enhance, widgetByName(enhance, "mode"), payload.enhance_mode);
  slotWrite(enhance, widgetByName(enhance, "duration_hint"), payload.hint);
  const save = nodeByType("SaveImage");
  slotWrite(save, widgetByName(save, "filename_prefix"), payload.prefix);
  const latent = nodeByType("EmptyFlux2LatentImage");
  slotWrite(latent, widgetByName(latent, "width"), payload.width);
  slotWrite(latent, widgetByName(latent, "height"), payload.height);
  slotWrite(latent, widgetByName(latent, "batch_size"), payload.batch);
}

/**
 * Ask Python what the next Queue will send and show it.
 * @returns {Promise<void>}
 */
async function refreshPreview() {
  if (!isImageStudio()) {
    return;
  }
  const modeNode = nodeByType("EZImageMode");
  if (modeNode?._ezPreviewWrite) {
    return;
  }
  try {
    const response = await fetch(apiUrl("/ez_image/studio-preview"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(previewBody()),
    });
    const payload = await response.json();
    if (!response.ok || !payload?.ok) {
      applyPreview({
        ok: false,
        summary: payload?.summary || PREVIEW_UNAVAILABLE,
      });
      return;
    }
    applyPreview(payload);
  } catch {
    applyPreview({ ok: false, summary: PREVIEW_UNAVAILABLE });
  }
}

/**
 * Debounce preview refreshes from widget edits.
 * @returns {void}
 */
function schedulePreview() {
  if (previewTimer) {
    clearTimeout(previewTimer);
  }
  previewTimer = setTimeout(() => {
    previewTimer = 0;
    void refreshPreview();
  }, PREVIEW_MS);
}

/**
 * Chain a widget callback so edits refresh This run. A missing node is a
 * no-op taken before the closure captures anything, so the chained callback
 * can never run against a class that is not on the graph.
 * @param {EzNode|undefined} node
 * @param {string} widgetName
 * @returns {void}
 */
function watchWidget(node, widgetName) {
  if (!node) {
    return;
  }
  const widget = widgetByName(node, widgetName);
  if (!widget || widget._ezStudioWatch) {
    return;
  }
  widget._ezStudioWatch = true;
  const prior = widget.callback;
  /**
   * Chain the prior callback, then refresh unless a preview write caused it.
   * @returns {unknown}
   */
  widget.callback = function () {
    const value = prior?.apply(this, arguments);
    if (!node._ezPreviewWrite) {
      schedulePreview();
    }
    return value;
  };
}

/**
 * Watch every widget that changes what Queue will send.
 * @returns {void}
 */
function bindPreviewWatchers() {
  if (!isImageStudio()) {
    return;
  }
  const pairs = [
    ["EZImageMode", "category"],
    ["EZImageMode", "mode"],
    ["EZImageMode", "iterate"],
    ["EZOptionalImage", "filename"],
    ["EZImageFormat", "format"],
    ["EZImageFormat", "size_mode"],
    ["EZImageFormat", "look"],
    ["EZImageFormat", "width"],
    ["EZImageFormat", "height"],
    ["EZImageFormat", "batch_size"],
    ["EZKleinPromptEnhance", "prompt"],
    ["EZKleinPromptEnhance", "sample"],
    ["EZKleinPromptEnhance", "style"],
    ["EZKleinPromptEnhance", "enhance"],
    ["KSampler", "seed"],
    ["KSampler", "steps"],
    ["KSampler", "cfg"],
    ["KSampler", "control_after_generate"],
    ["UNETLoader", "unet_name"],
  ];
  for (const [typeName, widgetName] of pairs) {
    watchWidget(nodeByType(typeName), widgetName);
  }
  const summary = widgetByName(nodeByType("EZImageMode"), "run_summary");
  if (summary?.inputEl) {
    summary.inputEl.readOnly = true;
  }
}

let studioBindTimer = 0;

/**
 * Bind the desk watchers once the current LiteGraph pass returns.
 * onNodeCreated runs inside LGraph.configure, where the desk classes that
 * come after the Mode node in the graph are not built yet, so binding there
 * skipped them and asked widgetByName for classes that did not exist. A
 * timer also keeps one bind pass per graph load however many Mode nodes
 * there are.
 * @returns {void}
 */
function deferStudioBindings() {
  if (studioBindTimer) {
    return;
  }
  studioBindTimer = setTimeout(() => {
    studioBindTimer = 0;
    bindPreviewWatchers();
    void refreshPreview();
  }, 0);
}

/**
 * Copy the first saved still into the reference when Iterate is on.
 * @param {EzExecutedMessage|undefined} message
 * @returns {Promise<void>}
 */
async function feedLastStill(message) {
  if (!isImageStudio()) {
    return;
  }
  const modeNode = nodeByType("EZImageMode");
  if (!isOn(widgetByName(modeNode, "iterate")?.value)) {
    return;
  }
  const images = message?.images || [];
  const first = images[0];
  if (!first?.filename || (first.type && first.type !== "output")) {
    return;
  }
  const rel = first.subfolder
    ? `${first.subfolder}/${first.filename}`
    : first.filename;
  try {
    const response = await fetch(apiUrl("/ez_outputs/to-input"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rel }),
    });
    const data = await response.json();
    if (!isOn(widgetByName(modeNode, "iterate")?.value)) {
      return;
    }
    if (!response.ok || !data?.name) {
      slotWrite(
        modeNode,
        widgetByName(modeNode, "run_summary"),
        "Could not copy the still into the reference. Pick it from Outputs.",
      );
      return;
    }
    const optional = nodeByType("EZOptionalImage");
    slotWrite(optional, widgetByName(optional, "filename"), data.name);
    await refreshPreview();
  } catch {
    slotWrite(
      modeNode,
      widgetByName(modeNode, "run_summary"),
      "Could not copy the still into the reference. Pick it from Outputs.",
    );
  }
}

app.registerExtension({
  name: "ez_image.mode",
  /**
   * Wrap EZImageMode so Category filters Mode on create.
   * @param {EzNodeType} nodeType
   * @param {EzNodeDef} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name === "SaveImage") {
      const onExecuted = nodeType.prototype.onExecuted;
      /**
       * After a save, feed the still back when Iterate is on.
       * @param {EzExecutedMessage} message
       * @returns {void}
       */
      nodeType.prototype.onExecuted = function (message) {
        onExecuted?.apply(this, arguments);
        void feedLastStill(message);
      };
      return;
    }
    if (nodeData.name !== "EZImageMode") {
      return;
    }
    await loadCatalog();
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    /**
     * Bind the category combo when the node is created.
     * @returns {void}
     */
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      bindModeNode(this);
      // LiteGraph is still inside LGraph.configure here, so the other desk
      // classes may not exist yet. Defer the graph-wide walk to the next
      // macrotask, when the configure pass has finished.
      deferStudioBindings();
    };
  },
  /**
   * Re-bind after a graph load.
   * @returns {Promise<void>}
   */
  async afterConfigureGraph() {
    await loadCatalog();
    bindAll();
    bindPreviewWatchers();
    await refreshPreview();
  },
  /**
   * Re-bind after the graph extra lands.
   * @returns {void}
   */
  setup() {
    const graph = app.graph;
    if (graph?.addEventListener) {
      graph.addEventListener("configured", () => {
        bindPreviewWatchers();
        void refreshPreview();
      });
    }
  },
});

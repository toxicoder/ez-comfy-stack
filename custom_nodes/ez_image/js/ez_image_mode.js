/**
 * EZImageMode frontend: filter the Mode combo by Category.
 *
 * Nodes 2.0: writes widget.value. Python run() is the Queue source of truth
 * for Enhance context / mode / SaveImage prefix. An unknown mode falls back
 * in Python; this script only narrows the visible combo.
 */
import { app } from "../../scripts/app.js";

let catalog = null;

/**
 * Find a widget by name on a node.
 * @param {object} node
 * @param {string} name
 * @returns {object|undefined}
 */
function widgetByName(node, name) {
  return node.widgets?.find((w) => w.name === name);
}

/**
 * Catalog mode rows from the last successful fetch, or an empty list.
 * @returns {object[]}
 */
function modeRows() {
  const rows = catalog?.modes;
  return Array.isArray(rows) ? rows : [];
}

/**
 * Catalog category rows, or an empty list.
 * @returns {object[]}
 */
function categoryRows() {
  const rows = catalog?.categories;
  return Array.isArray(rows) ? rows : [];
}

/**
 * Resolve a combo value to a category id.
 * @param {string} value
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
 * @param {string} category
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
 * @param {object} widget
 * @param {object} node
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
 * @param {object} node
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
 * @param {object} node
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
     * @param {*} value
     * @returns {*}
     */
    categoryWidget.callback = function (value) {
      categoryCb?.apply(this, arguments);
      applyCategory(node);
      return value;
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
  "Preview unavailable — Queue still uses the nodes. Reload the App after pull if this stays.";
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
 * @returns {object|undefined}
 */
function nodeByType(typeName) {
  return (app.graph?.nodes || []).find((node) => {
    const ntype = node?.comfyClass || node?.type || "";
    return ntype === typeName;
  });
}

/**
 * True for Comfy booleans and yes/on strings.
 * @param {*} value
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
 * @param {object|undefined} node
 * @param {object|undefined} widget
 * @param {*} value
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
 * @returns {*}
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
  if ((app.graph?.extra?.lab_rel || "") === "stills/image-studio") {
    return true;
  }
  return Boolean(nodeByType("EZImageMode"));
}

/**
 * Snapshot of the widgets the preview route resolves.
 * @returns {object}
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
    lab_rel: app.graph?.extra?.lab_rel || "stills/image-studio",
  };
}

/**
 * Copy resolved values onto the widgets Queue's links would otherwise hide.
 * @param {object} payload
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
 * Chain a widget callback so edits refresh This run.
 * @param {object|undefined} node
 * @param {string} widgetName
 * @returns {void}
 */
function watchWidget(node, widgetName) {
  const widget = widgetByName(node, widgetName);
  if (!widget || widget._ezStudioWatch) {
    return;
  }
  widget._ezStudioWatch = true;
  const prior = widget.callback;
  /**
   * Chain the prior callback, then refresh unless a preview write caused it.
   * @returns {*}
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

/**
 * Copy the first saved still into the reference when Iterate is on.
 * @param {object|undefined} message
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
   * @param {object} nodeType
   * @param {object} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name === "SaveImage") {
      const onExecuted = nodeType.prototype.onExecuted;
      /**
       * After a save, feed the still back when Iterate is on.
       * @param {object} message
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
      bindPreviewWatchers();
      void refreshPreview();
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
  /**
   * Re-apply the category filter and the run preview immediately before Queue.
   * @returns {Promise<void>}
   */
  async beforeQueued() {
    await loadCatalog();
    bindAll();
    for (const node of app.graph?.nodes || []) {
      if (node?.comfyClass === "EZImageMode" || node?.type === "EZImageMode") {
        applyCategory(node);
      }
    }
    await refreshPreview();
  },
});

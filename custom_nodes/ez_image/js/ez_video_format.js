/**
 * EZVideoFormat frontend: filter format rows by family and sync width/height.
 *
 * Nodes 2.0: writes widget.value. Python run() is the Queue source of truth
 * for linked latent / hint outputs. Custom uses the INT widgets. Family is
 * graph-authored (Wan vs LTX); App Mode hides it.
 */
import { app } from "../../scripts/app.js";

const CUSTOM_LABEL = "Custom";
const CUSTOM_ID = "custom";
let catalog = null;
let applying = false;

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
 * Set a widget value and notify Vue / App Mode (Nodes 2.0).
 * @param {object|undefined} node
 * @param {object|undefined} widget
 * @param {*} value
 * @returns {void}
 */
function setWidgetValue(node, widget, value) {
  if (!widget || widget.value === value) {
    return;
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
  if (graph && typeof graph.change === "function") {
    graph.change();
  }
}

/**
 * Catalog rows from the last successful fetch, or an empty list.
 * @returns {object[]}
 */
function formatRows() {
  const rows = catalog?.formats;
  return Array.isArray(rows) ? rows : [];
}

/**
 * Family specs from the last successful fetch.
 * @returns {object}
 */
function families() {
  const rows = catalog?.families;
  return rows && typeof rows === "object" ? rows : {};
}

/**
 * Resolve a family combo value to a catalog id.
 * @param {string} value
 * @returns {string}
 */
function familyId(value) {
  const raw = String(value || "").trim();
  const folded = raw.toLowerCase();
  const specs = families();
  if (raw && specs[raw]) {
    return raw;
  }
  for (const [id, spec] of Object.entries(specs)) {
    if (String(spec?.label || "").toLowerCase() === folded) {
      return id;
    }
  }
  return "wan";
}

/**
 * Visible format labels for a family (Custom plus that family's rows).
 * @param {string} family
 * @returns {string[]}
 */
function labelsForFamily(family) {
  const fid = familyId(family);
  const labels = [];
  for (const row of formatRows()) {
    const id = String(row.id || "");
    const fam = String(row.family || "");
    if (id === CUSTOM_ID || fam === fid) {
      labels.push(String(row.label || id));
    }
  }
  return labels;
}

/**
 * Default format label for a family.
 * @param {string} family
 * @returns {string}
 */
function defaultLabelForFamily(family) {
  const fid = familyId(family);
  const spec = families()[fid];
  const wanted = String(spec?.default_id || "");
  for (const row of formatRows()) {
    if (String(row.id) === wanted) {
      return String(row.label || wanted);
    }
  }
  const labels = labelsForFamily(fid);
  return labels[0] || CUSTOM_LABEL;
}

/**
 * Resolve a combo value to a catalog row.
 * @param {string} value
 * @returns {object|null}
 */
function findFormat(value) {
  const raw = String(value || "").trim();
  const folded = raw.toLowerCase();
  if (!raw || folded === CUSTOM_ID || folded === CUSTOM_LABEL.toLowerCase()) {
    return formatRows().find((row) => String(row.id) === CUSTOM_ID) || null;
  }
  for (const row of formatRows()) {
    if (String(row.id) === raw || String(row.label).toLowerCase() === folded) {
      return row;
    }
  }
  return null;
}

/**
 * True when the row is the Custom sentinel.
 * @param {object|null} row
 * @returns {boolean}
 */
function isCustom(row) {
  return !row || String(row.id) === CUSTOM_ID;
}

/**
 * Restrict the format combo to the current family.
 * @param {object} node
 * @returns {void}
 */
function syncFormatOptions(node) {
  const familyWidget = widgetByName(node, "family");
  const formatWidget = widgetByName(node, "format");
  if (!familyWidget || !formatWidget) {
    return;
  }
  const labels = labelsForFamily(familyWidget.value);
  if (!formatWidget.options) {
    formatWidget.options = {};
  }
  formatWidget.options.values = labels;
  const current = String(formatWidget.value || "");
  if (!labels.includes(current)) {
    setWidgetValue(node, formatWidget, defaultLabelForFamily(familyWidget.value));
  }
}

/**
 * Write width/height from a non-custom format row.
 * @param {object} node
 * @returns {void}
 */
function applyFormat(node) {
  syncFormatOptions(node);
  const formatWidget = widgetByName(node, "format");
  const widthWidget = widgetByName(node, "width");
  const heightWidget = widgetByName(node, "height");
  if (!formatWidget || !widthWidget || !heightWidget) {
    return;
  }
  const row = findFormat(formatWidget.value);
  if (isCustom(row)) {
    return;
  }
  applying = true;
  setWidgetValue(node, widthWidget, Number(row.width));
  setWidgetValue(node, heightWidget, Number(row.height));
  applying = false;
}

/**
 * If width/height no longer match the preset, switch Format to Custom.
 * @param {object} node
 * @returns {void}
 */
function maybeMarkCustom(node) {
  if (applying) {
    return;
  }
  const formatWidget = widgetByName(node, "format");
  const widthWidget = widgetByName(node, "width");
  const heightWidget = widgetByName(node, "height");
  if (!formatWidget || !widthWidget || !heightWidget) {
    return;
  }
  const row = findFormat(formatWidget.value);
  if (isCustom(row)) {
    return;
  }
  const width = Number(widthWidget.value);
  const height = Number(heightWidget.value);
  if (width === Number(row.width) && height === Number(row.height)) {
    return;
  }
  applying = true;
  setWidgetValue(node, formatWidget, CUSTOM_LABEL);
  applying = false;
}

/**
 * Bind family/format/width/height callbacks on one EZVideoFormat node.
 * @param {object} node
 * @returns {void}
 */
function bindFormatNode(node) {
  const ntype = node?.comfyClass || node?.type || "";
  if (!node || ntype !== "EZVideoFormat") {
    return;
  }
  if (node._ezVideoFormatBound) {
    return;
  }
  node._ezVideoFormatBound = true;
  const familyWidget = widgetByName(node, "family");
  const formatWidget = widgetByName(node, "format");
  const widthWidget = widgetByName(node, "width");
  const heightWidget = widgetByName(node, "height");
  const familyCb = familyWidget?.callback;
  const formatCb = formatWidget?.callback;
  const widthCb = widthWidget?.callback;
  const heightCb = heightWidget?.callback;
  if (familyWidget) {
    /**
     * Filter Format when Family changes.
     * @param {*} value
     * @returns {void}
     */
    familyWidget.callback = function (value) {
      familyCb?.apply(this, arguments);
      if (!applying) {
        applyFormat(node);
      }
      return value;
    };
  }
  if (formatWidget) {
    /**
     * Apply catalog size when Format changes.
     * @param {*} value
     * @returns {void}
     */
    formatWidget.callback = function (value) {
      formatCb?.apply(this, arguments);
      if (!applying) {
        applyFormat(node);
      }
      return value;
    };
  }
  if (widthWidget) {
    /**
     * Mark Custom when Width leaves the preset.
     * @param {*} value
     * @returns {void}
     */
    widthWidget.callback = function (value) {
      widthCb?.apply(this, arguments);
      maybeMarkCustom(node);
      return value;
    };
  }
  if (heightWidget) {
    /**
     * Mark Custom when Height leaves the preset.
     * @param {*} value
     * @returns {void}
     */
    heightWidget.callback = function (value) {
      heightCb?.apply(this, arguments);
      maybeMarkCustom(node);
      return value;
    };
  }
  applyFormat(node);
}

/**
 * Bind every EZVideoFormat node on the current graph.
 * @returns {void}
 */
function bindAll() {
  for (const node of app.graph?.nodes || []) {
    bindFormatNode(node);
  }
}

/**
 * Load js/video_formats.json from this pack's WEB_DIRECTORY.
 * @returns {Promise<void>}
 */
async function loadCatalog() {
  if (catalog) {
    return;
  }
  try {
    const response = await fetch("/extensions/ez_image/video_formats.json");
    if (!response.ok) {
      return;
    }
    const payload = await response.json();
    if (payload && Array.isArray(payload.formats)) {
      catalog = payload;
    }
  } catch {
    catalog = { formats: [], families: {} };
  }
}

app.registerExtension({
  name: "ez_image.video_format",
  /**
   * Wrap EZVideoFormat so Family filters Format on create.
   * @param {object} nodeType
   * @param {object} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "EZVideoFormat") {
      return;
    }
    await loadCatalog();
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    /**
     * Bind the family/format combos when the node is created.
     * @returns {void}
     */
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      bindFormatNode(this);
    };
  },
  /**
   * Re-bind after a graph load.
   * @returns {Promise<void>}
   */
  async afterConfigureGraph() {
    await loadCatalog();
    bindAll();
  },
  /**
   * Re-apply preset size immediately before Queue.
   * @returns {Promise<void>}
   */
  async beforeQueued() {
    bindAll();
    for (const node of app.graph?.nodes || []) {
      if (node?.comfyClass === "EZVideoFormat" || node?.type === "EZVideoFormat") {
        applyFormat(node);
      }
    }
  },
});

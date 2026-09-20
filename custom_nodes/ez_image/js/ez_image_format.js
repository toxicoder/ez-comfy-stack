/**
 * EZImageFormat frontend: sync width/height widgets from the format catalog.
 *
 * Nodes 2.0: writes widget.value. Python run() is the Queue source of truth
 * for linked latent / hint / prefix outputs. Custom uses the INT widgets.
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

const SIZE_MATCH = "Match input";

/**
 * True when Output size is Match input (default).
 * @param {*} value
 * @returns {boolean}
 */
function isMatchInput(value) {
  const folded = String(value || SIZE_MATCH)
    .trim()
    .toLowerCase()
    .replaceAll("_", " ");
  return !folded || folded === "match input" || folded === "match";
}

/**
 * Nearest aspect catalog row for a source size, preferring current area.
 * @param {number} srcW
 * @param {number} srcH
 * @param {object|null} current
 * @returns {object|null}
 */
function nearestAspectRow(srcW, srcH, current) {
  const rows = formatRows().filter(
    (row) => String(row.group) === "aspect" && Number(row.width) > 0 && Number(row.height) > 0,
  );
  if (!rows.length) {
    return current;
  }
  const srcRatio = srcW / Math.max(srcH, 1);
  const currentArea = Math.max(
    Number(current?.width || 0) * Number(current?.height || 0),
    1,
  );
  let best = rows[0];
  let bestScore = [Infinity, Infinity];
  for (const row of rows) {
    const ratioErr = Math.abs(Number(row.width) / Math.max(Number(row.height), 1) - srcRatio);
    const areaErr = Math.abs(Number(row.width) * Number(row.height) - currentArea) / currentArea;
    if (ratioErr < bestScore[0] || (ratioErr === bestScore[0] && areaErr < bestScore[1])) {
      best = row;
      bestScore = [ratioErr, areaErr];
    }
  }
  return best;
}

/**
 * First LoadImage / EZOptionalImage filename on the graph.
 * @param {object|undefined} graph
 * @returns {string}
 */
function firstImageName(graph) {
  for (const node of graph?.nodes || []) {
    const ntype = node?.comfyClass || node?.type || "";
    if (ntype === "LoadImage") {
      const widget = widgetByName(node, "image");
      const name = String(widget?.value || "").trim();
      if (name) {
        return name;
      }
    }
    if (ntype === "EZOptionalImage") {
      const widget = widgetByName(node, "filename");
      const name = String(widget?.value || "").trim();
      if (name) {
        return name;
      }
    }
  }
  return "";
}

/**
 * Probe natural size of an input-folder still.
 * @param {string} name
 * @param {function(number, number): void} onSize
 * @returns {void}
 */
function probeInputSize(name, onSize) {
  if (!name || typeof Image === "undefined") {
    return;
  }
  const img = new Image();
  img.onload = () => {
    if (img.naturalWidth > 1 && img.naturalHeight > 1) {
      onSize(img.naturalWidth, img.naturalHeight);
    }
  };
  img.src =
    "/view?filename=" + encodeURIComponent(name) + "&type=input";
}

/**
 * When Output size is Match input, snap Format to the loaded still's aspect.
 * @param {object} node
 * @returns {void}
 */
function applyMatchInput(node) {
  const modeWidget = widgetByName(node, "size_mode");
  if (!isMatchInput(modeWidget?.value)) {
    applyFormat(node);
    return;
  }
  const name = firstImageName(node.graph || app.graph);
  if (!name) {
    applyFormat(node);
    return;
  }
  probeInputSize(name, (width, height) => {
    const formatWidget = widgetByName(node, "format");
    const current = findFormat(formatWidget?.value);
    const row = nearestAspectRow(width, height, current);
    if (!row || isCustom(row)) {
      return;
    }
    applying = true;
    setWidgetValue(node, formatWidget, String(row.label));
    setWidgetValue(node, widgetByName(node, "width"), Number(row.width));
    setWidgetValue(node, widgetByName(node, "height"), Number(row.height));
    applying = false;
  });
}

/**
 * Write width/height from a non-custom format row.
 * @param {object} node
 * @returns {void}
 */
function applyFormat(node) {
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
 * Bind format/width/height callbacks on one EZImageFormat node.
 * @param {object} node
 * @returns {void}
 */
function bindFormatNode(node) {
  const ntype = node?.comfyClass || node?.type || "";
  if (!node || ntype !== "EZImageFormat") {
    return;
  }
  if (node._ezFormatBound) {
    return;
  }
  node._ezFormatBound = true;
  const formatWidget = widgetByName(node, "format");
  const modeWidget = widgetByName(node, "size_mode");
  const widthWidget = widgetByName(node, "width");
  const heightWidget = widgetByName(node, "height");
  const formatCb = formatWidget?.callback;
  const modeCb = modeWidget?.callback;
  const widthCb = widthWidget?.callback;
  const heightCb = heightWidget?.callback;
  if (formatWidget) {
    /**
     * Apply catalog size when Format changes.
     * @param {*} value
     * @returns {void}
     */
    formatWidget.callback = function (value) {
      formatCb?.apply(this, arguments);
      if (!applying && !isMatchInput(modeWidget?.value)) {
        applyFormat(node);
      }
      return value;
    };
  }
  if (modeWidget) {
    /**
     * Re-apply Match input or Force format.
     * @param {*} value
     * @returns {void}
     */
    modeWidget.callback = function (value) {
      modeCb?.apply(this, arguments);
      if (!applying) {
        applyMatchInput(node);
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
  applyMatchInput(node);
}

/**
 * Bind every EZImageFormat node on the current graph.
 * @returns {void}
 */
function bindAll() {
  for (const node of app.graph?.nodes || []) {
    bindFormatNode(node);
  }
}

/**
 * Load js/formats.json from this pack's WEB_DIRECTORY.
 * @returns {Promise<void>}
 */
async function loadCatalog() {
  if (catalog) {
    return;
  }
  try {
    const response = await fetch("/extensions/ez_image/formats.json");
    if (!response.ok) {
      return;
    }
    const payload = await response.json();
    if (payload && Array.isArray(payload.formats)) {
      catalog = payload;
    }
  } catch {
    catalog = { formats: [] };
  }
}

app.registerExtension({
  name: "ez_image.format",
  /**
   * Wrap EZImageFormat so Format writes width/height on create.
   * @param {object} nodeType
   * @param {object} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "EZImageFormat") {
      return;
    }
    await loadCatalog();
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    /**
     * Bind the format combo when the node is created.
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
      if (node?.comfyClass === "EZImageFormat" || node?.type === "EZImageFormat") {
        applyFormat(node);
      }
    }
  },
});

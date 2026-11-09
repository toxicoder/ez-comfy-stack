/**
 * EZImageFormat frontend: sync width/height widgets from the format catalog.
 *
 * Nodes 2.0: writes widget.value. Python run() is the Queue source of truth
 * for linked latent / hint / prefix outputs. Custom uses the INT widgets.
 */
import { app } from "../../scripts/app.js";

/**
 * One row from formats.json. The file reads every field defensively with
 * String() / Number(), so all of them stay optional.
 * @typedef {{
 *   id?: string,
 *   label?: string,
 *   group?: string,
 *   width?: number,
 *   height?: number
 * }} EzFormatRow
 */

/**
 * Preset size a named format row last applied to a node.
 * @typedef {{width: number, height: number}} EzAppliedSize
 */

/**
 * Format/size widget. ComfyUI invokes callback with the widget as ``this``.
 * @typedef {{
 *   name: string,
 *   value?: string|number|null,
 *   callback?: (
 *     this: EzWidget,
 *     value: unknown,
 *     canvas?: unknown,
 *     node?: EzFormatNode
 *   ) => unknown,
 *   beforeQueued?: (this: EzWidget) => void
 * }} EzWidget
 */

/**
 * Graph handle used to walk nodes and dirty the canvas.
 * @typedef {{
 *   nodes?: EzFormatNode[],
 *   setDirtyCanvas?: (dirtyCanvas: boolean, dirty: boolean) => void,
 *   change?: () => void
 * }} EzGraph
 */

/**
 * EZImageFormat node. --noResolve leaves the ComfyUI frontend untyped, so only
 * the members this file reads or writes are named.
 * @typedef {{
 *   type?: string,
 *   comfyClass?: string,
 *   widgets?: EzWidget[],
 *   widgets_values?: unknown[],
 *   graph?: EzGraph,
 *   _ezFormatBound?: boolean,
 *   _ezFormatApplied?: EzAppliedSize|null
 * }} EzFormatNode
 */

/**
 * Registered node definition, seen before ComfyUI registers it.
 * @typedef {{
 *   prototype: {
 *     onNodeCreated?: (this: EzFormatNode, ...args: unknown[]) => void;
 *   }
 * }} EzNodeType
 */

/**
 * Node definition metadata; only the class name is read here.
 * @typedef {{name: string}} EzNodeDef
 */

const CUSTOM_LABEL = "Custom";
const CUSTOM_ID = "custom";
let catalog = null;
let applying = false;

/**
 * Find a widget by name on a node.
 * @param {EzFormatNode} node
 * @param {string} name
 * @returns {EzWidget|undefined}
 */
function widgetByName(node, name) {
  return node.widgets?.find((w) => w.name === name);
}

/**
 * Set a widget value and notify Vue / App Mode (Nodes 2.0).
 * @param {EzFormatNode|undefined} node
 * @param {EzWidget|undefined} widget
 * @param {string|number} value
 * @returns {void}
 */
function setWidgetValue(node, widget, value) {
  if (!widget || widget.value === value) {
    return;
  }
  widget.value = value;
  if (Array.isArray(node?.widgets_values) && node.widgets) {
    const idx = node.widgets.indexOf(widget);
    if (idx >= 0) {
      node.widgets_values[idx] = value;
    }
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
 * @returns {EzFormatRow[]}
 */
function formatRows() {
  const rows = catalog?.formats;
  return Array.isArray(rows) ? rows : [];
}

/**
 * Resolve a combo value to a catalog row.
 * @param {string|number|null|undefined} value
 * @returns {EzFormatRow|null}
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
 * @param {EzFormatRow|null} row
 * @returns {boolean}
 */
function isCustom(row) {
  return !row || String(row.id) === CUSTOM_ID;
}

const SIZE_MATCH = "Match input";

/**
 * True when Output size is Match input (default).
 * @param {string|number|null|undefined} value
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
 * @param {EzFormatRow|null} current
 * @returns {EzFormatRow|null}
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
 * @param {EzGraph|undefined} graph
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
 * @param {(width: number, height: number) => void} onSize
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
 * @param {EzFormatNode} node
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
    recordAppliedFormat(node, row);
    applying = false;
  });
}

/**
 * Remember the preset size a named format row applied to a node.
 *
 * The snapshot is the baseline the queue-time check compares against; Custom
 * clears it because the INT widgets are then the user's own.
 * @param {EzFormatNode|undefined} node
 * @param {EzFormatRow|null} row
 * @returns {void}
 */
function recordAppliedFormat(node, row) {
  if (!node) {
    return;
  }
  node._ezFormatApplied = isCustom(row)
    ? null
    : { width: Number(row.width), height: Number(row.height) };
}

/**
 * Write width/height from a non-custom format row.
 * @param {EzFormatNode} node
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
    recordAppliedFormat(node, null);
    return;
  }
  applying = true;
  setWidgetValue(node, widthWidget, Number(row.width));
  setWidgetValue(node, heightWidget, Number(row.height));
  recordAppliedFormat(node, row);
  applying = false;
}

/**
 * If width/height no longer match the preset, switch Format to Custom.
 * @param {EzFormatNode} node
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
  recordAppliedFormat(node, null);
  applying = false;
}

/**
 * Reconcile Format with the size widgets synchronously before Queue.
 *
 * Runs from the Format widget's ``beforeQueued`` hook, which the pinned
 * frontend invokes synchronously for every widget right before serializing the
 * prompt, so it must stay synchronous and must not fetch (the catalog may be
 * unfetched for a graph bound before loadCatalog resolved). Hand-edited sizes
 * that match neither the selected row nor the last applied preset switch
 * Format to Custom so Python encodes the user's numbers; untouched sizes
 * re-apply the preset, which is what the never-invoked extension-level hook
 * used to promise.
 * @param {EzFormatNode|undefined} node
 * @returns {void}
 */
function queueTimeFormatSync(node) {
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
  const applied = node._ezFormatApplied;
  const width = Number(widthWidget.value);
  const height = Number(heightWidget.value);
  const rowMatch = width === Number(row.width) && height === Number(row.height);
  const appliedMatch =
    !!applied && width === Number(applied.width) && height === Number(applied.height);
  applying = true;
  if (!rowMatch && !appliedMatch) {
    setWidgetValue(node, formatWidget, CUSTOM_LABEL);
    node._ezFormatApplied = null;
  } else {
    setWidgetValue(node, widthWidget, Number(row.width));
    setWidgetValue(node, heightWidget, Number(row.height));
    recordAppliedFormat(node, row);
  }
  applying = false;
}

/**
 * Bind format/width/height callbacks on one EZImageFormat node.
 * @param {EzFormatNode} node
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
     * @param {string|number|null|undefined} value
     * @returns {string|number|null|undefined}
     */
    formatWidget.callback = function (value) {
      formatCb?.apply(this, arguments);
      if (!applying && !isMatchInput(modeWidget?.value)) {
        applyFormat(node);
      }
      return value;
    };
    /**
     * Reconcile Format with the size widgets at Queue.
     * @returns {void}
     */
    formatWidget.beforeQueued = function () {
      queueTimeFormatSync(node);
    };
  }
  if (modeWidget) {
    /**
     * Re-apply Match input or Force format.
     * @param {string|number|null|undefined} value
     * @returns {string|number|null|undefined}
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
     * @param {string|number|null|undefined} value
     * @returns {string|number|null|undefined}
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
     * @param {string|number|null|undefined} value
     * @returns {string|number|null|undefined}
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
   * @param {EzNodeType} nodeType
   * @param {EzNodeDef} nodeData
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
});

/**
 * EZVideoFormat frontend: filter format rows by family and sync width/height.
 *
 * Nodes 2.0: writes widget.value. Python run() is the Queue source of truth
 * for linked latent / hint outputs. Custom uses the INT widgets. Family is
 * graph-authored (Wan vs LTX); App Mode hides it.
 */
import { app } from "../../scripts/app.js";

/**
 * One row from video_formats.json. The file reads every field defensively with
 * String() / Number(), so all of them stay optional.
 * @typedef {{
 *   id?: string,
 *   label?: string,
 *   family?: string,
 *   width?: number,
 *   height?: number
 * }} EzFormatRow
 */

/**
 * One families entry from video_formats.json, keyed by family id.
 * @typedef {{label?: string, default_id?: string}} EzFamilySpec
 */

/**
 * Preset values a named format row last applied to a node.
 * @typedef {{
 *   width: number,
 *   height: number,
 *   duration_s: string,
 *   frames: string
 * }} EzAppliedSize
 */

/**
 * Family/format/size widget. ComfyUI invokes callback with the widget as
 * ``this`` and beforeQueued at Queue time.
 * @typedef {{
 *   name: string,
 *   value?: string|number|null,
 *   options?: {values?: string[]},
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
 * Graph handle used to walk nodes, read App Mode occupancy, and dirty the
 * canvas.
 * @typedef {{
 *   nodes?: EzFormatNode[],
 *   extra?: {lab_app_mode?: {occupancy?: string}},
 *   setDirtyCanvas?: (dirtyCanvas: boolean, dirty: boolean) => void,
 *   change?: () => void
 * }} EzGraph
 */

/**
 * EZVideoFormat node. --noResolve leaves the ComfyUI frontend untyped, so only
 * the members this file reads or writes are named.
 * @typedef {{
 *   type?: string,
 *   comfyClass?: string,
 *   widgets?: EzWidget[],
 *   widgets_values?: unknown[],
 *   graph?: EzGraph,
 *   _ezVideoFormatBound?: boolean,
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
 * Family specs from the last successful fetch, keyed by family id.
 * @returns {Record<string, EzFamilySpec>}
 */
function families() {
  const rows = catalog?.families;
  return rows && typeof rows === "object" ? rows : {};
}

/**
 * Resolve a family combo value to a catalog id.
 * @param {string|number|null|undefined} value
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
 * @param {string|number|null|undefined} family
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
 * @param {string|number|null|undefined} family
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

/**
 * Restrict the format combo to the current family.
 * @param {EzFormatNode} node
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
 * Remember the preset values a named format row applied to a node.
 *
 * The snapshot is the baseline the queue-time check compares against and is
 * keyed by widget name, so it covers the duration field this pack also
 * manages. Custom clears it because the widgets are then the user's own.
 * @param {EzFormatNode|undefined} node
 * @param {EzFormatRow|null} row
 * @returns {void}
 */
function recordAppliedFormat(node, row) {
  if (!node) {
    return;
  }
  if (isCustom(row)) {
    node._ezFormatApplied = null;
    return;
  }
  const durationWidget = widgetByName(node, "duration_s");
  node._ezFormatApplied = {
    width: Number(row.width),
    height: Number(row.height),
    duration_s: String(durationWidget?.value ?? ""),
    frames: String(ltxFramesForDuration(durationWidget?.value) ?? ""),
  };
}

/**
 * Write width/height from a non-custom format row.
 * @param {EzFormatNode} node
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
 * Reconcile Format with the size/duration widgets synchronously before Queue.
 *
 * Runs from the Format widget's ``beforeQueued`` hook, which the pinned
 * frontend invokes for every widget right before serializing the prompt, so
 * it must stay synchronous and must not fetch (the catalog may be unfetched
 * for a graph bound before loadCatalog resolved). Hand-edited sizes that match
 * neither the selected row nor the last applied preset switch Format to Custom
 * so Python encodes the user's numbers; untouched sizes re-apply the preset.
 * A Duration move re-runs applyDuration instead of leaving the LTX latents on
 * the old length, because Python keeps using duration_s whatever Format says.
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
  const durationWidget = widgetByName(node, "duration_s");
  const duration = String(durationWidget?.value ?? "");
  const frames = String(ltxFramesForDuration(duration) ?? "");
  const durationMoved =
    !!applied &&
    (duration !== String(applied.duration_s ?? "") || frames !== String(applied.frames ?? ""));
  applying = true;
  if (!rowMatch && !appliedMatch) {
    setWidgetValue(node, formatWidget, CUSTOM_LABEL);
    node._ezFormatApplied = null;
  } else {
    setWidgetValue(node, widthWidget, Number(row.width));
    setWidgetValue(node, heightWidget, Number(row.height));
    recordAppliedFormat(node, row);
  }
  if (durationMoved) {
    applyDuration(node);
  }
  applying = false;
}

/**
 * Bind family/format/width/height callbacks on one EZVideoFormat node.
 * @param {EzFormatNode} node
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
     * @param {string|number|null|undefined} value
     * @returns {string|number|null|undefined}
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
     * @param {string|number|null|undefined} value
     * @returns {string|number|null|undefined}
     */
    formatWidget.callback = function (value) {
      formatCb?.apply(this, arguments);
      if (!applying) {
        applyFormat(node);
      }
      return value;
    };
    /**
     * Reconcile Format with the size/duration widgets at Queue.
     * @returns {void}
     */
    formatWidget.beforeQueued = function () {
      queueTimeFormatSync(node);
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
  const durationWidget = widgetByName(node, "duration_s");
  const durationCb = durationWidget?.callback;
  if (durationWidget) {
    /**
     * Write LTX latent length when Duration changes.
     * @param {string|number|null|undefined} value
     * @returns {string|number|null|undefined}
     */
    durationWidget.callback = function (value) {
      durationCb?.apply(this, arguments);
      applyDuration(node);
      return value;
    };
  }
  applyFormat(node);
  applyDuration(node);
}

/**
 * Legal LTX frame count for a duration combo (1+8n).
 * @param {string|number|null|undefined} value
 * @returns {number|null}
 */
function ltxFramesForDuration(value) {
  const folded = String(value || "").toLowerCase();
  const seconds = Number.parseFloat(folded);
  if (!(seconds > 0)) {
    return null;
  }
  const target = Math.round(seconds * 24);
  const k = Math.max(0, Math.round((target - 1) / 8));
  return 1 + 8 * k;
}

/**
 * True when this graph is LTX occupancy / family.
 * @param {EzFormatNode} node
 * @returns {boolean}
 */
function isLtxGraph(node) {
  const family = widgetByName(node, "family")?.value;
  if (String(family || "").toLowerCase().includes("ltx")) {
    return true;
  }
  const occ = node.graph?.extra?.lab_app_mode?.occupancy || app.graph?.extra?.lab_app_mode?.occupancy;
  return String(occ || "") === "ltx";
}

/**
 * Write Duration onto LTX length widgets. Wan stays put.
 * @param {EzFormatNode} node
 * @returns {void}
 */
function applyDuration(node) {
  if (!isLtxGraph(node)) {
    return;
  }
  const frames = ltxFramesForDuration(widgetByName(node, "duration_s")?.value);
  if (!frames) {
    return;
  }
  const graph = node.graph || app.graph;
  for (const item of graph?.nodes || []) {
    const ntype = item?.comfyClass || item?.type || "";
    const lengthName = ntype === "LTXVEmptyLatentAudio" ? "length" : "length";
    if (
      ntype !== "LTXVImgToVideo" &&
      ntype !== "EmptyLTXVLatentVideo" &&
      ntype !== "LTXVEmptyLatentAudio"
    ) {
      continue;
    }
    const widget = widgetByName(item, lengthName) || item.widgets?.[2] || item.widgets?.[0];
    if (ntype === "LTXVEmptyLatentAudio") {
      setWidgetValue(item, item.widgets?.[0], frames);
    } else {
      setWidgetValue(item, item.widgets?.[2] || widget, frames);
    }
  }
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
   * @param {EzNodeType} nodeType
   * @param {EzNodeDef} nodeData
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
});

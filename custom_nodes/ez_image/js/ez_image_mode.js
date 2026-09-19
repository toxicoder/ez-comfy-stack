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

app.registerExtension({
  name: "ez_image.mode",
  /**
   * Wrap EZImageMode so Category filters Mode on create.
   * @param {object} nodeType
   * @param {object} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeType, nodeData) {
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
   * Re-apply the category filter immediately before Queue.
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
  },
});

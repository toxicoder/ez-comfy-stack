/**
 * Prompt-enhance / sample-picker frontend: catalog samples plus CLIP preview.
 *
 * Nodes 2.0: set widget.value; treat inputEl as optional (Vue STRING widgets
 * have no canvas textarea). Sample combo uses a getter on widget.options.values
 * so App Mode (Vue) and refreshComboInNodes cannot restore the Python union.
 * Typing prompt/tags/lyrics/sources selects Sample custom so Queue uses the box
 * at any Quality. Named samples still copy the recipe into the box.
 */
import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

const NODE_CLASSES = new Set([
  "EZKleinPromptEnhance",
  "EZWanPromptEnhance",
  "EZLTXPromptEnhance",
  "EZZimagePromptEnhance",
  "EZLongCatPromptEnhance",
  "EZDreamXPromptEnhance",
  "EZNegativePromptEnhance",
  "EZAceStepPromptEnhance",
  "EZRapLyrics",
  "EZPodcastScript",
  "EZPodcastLearn",
  "EZSamplePrompt",
  "EZCreativeResearch",
  "EZAppForge",
]);

const PREVIEW_SKIP = new Set([
  "EZSamplePrompt",
  "EZCreativeResearch",
  "EZAppForge",
  "EZPodcastLearn",
]);

const SAMPLE_CUSTOM = "custom";
const TEXT_WIDGET_NAMES = ["prompt", "tags", "lyrics", "sources"];
const catalogCache = new Map();

/** Node type + mode/flavor → catalog stem. Mirrors samples.py _FAMILY_FOR_MODE. */
const FAMILY_FOR_MODE = {
  EZKleinPromptEnhance: {
    t2i: "klein_t2i",
    edit: "klein_clay_edit",
    identity: "klein_identity",
    text_swap: "klein_text_swap",
  },
  EZWanPromptEnhance: {
    t2v: "wan_t2v",
    i2v: "wan_i2v",
    flf: "wan_flf",
    vace: "wan_vace",
    s2v: "wan_i2v",
  },
  EZLTXPromptEnhance: {
    t2v: "ltx_t2v",
    i2v: "ltx_i2v",
    iclora: "ltx_iclora",
  },
  EZZimagePromptEnhance: { t2i: "klein_t2i" },
  EZLongCatPromptEnhance: {
    t2v: "wan_t2v",
    i2v: "wan_i2v",
    vc: "wan_i2v",
  },
  EZDreamXPromptEnhance: { i2v: "ltx_i2v" },
  EZAceStepPromptEnhance: {
    vocal: "rap_draft",
    instrumental: "rap_draft",
  },
  EZPodcastScript: {
    podcast_two_host: "podcast_two_host",
    radio_drama: "podcast_radio",
  },
  EZPodcastLearn: { "": "podcast_learn" },
  EZRapLyrics: { "": "rap_draft" },
  EZCreativeResearch: { "": "research_chat" },
  EZAppForge: { "": "app_forge" },
  EZSamplePrompt: { "": "forge_lazy" },
};

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
 * Write text onto a STRING widget and optionally lock the textarea.
 * @param {object|undefined} widget
 * @param {string} text
 * @param {boolean} readOnly
 * @returns {void}
 */
function setTextWidget(widget, text, readOnly) {
  if (!widget) {
    return;
  }
  widget.value = text;
  if (widget.inputEl) {
    widget.inputEl.readOnly = Boolean(readOnly);
    widget.inputEl.style.opacity = readOnly ? "0.75" : "1";
  }
}

/**
 * Family catalog stem from node type and mode/flavor widgets.
 * @param {object} node
 * @returns {string}
 */
function familyCatalog(node) {
  const ntype = node?.comfyClass || node?.type || "";
  const table = FAMILY_FOR_MODE[ntype];
  if (!table) {
    return "";
  }
  const modeWidget =
    widgetByName(node, "mode") || widgetByName(node, "flavor");
  const kind = String(modeWidget?.value || "").trim();
  if (kind && table[kind]) {
    return table[kind];
  }
  return table[""] || "";
}

/**
 * Catalog id from the catalog widget, extra.lab_rel, or node family.
 * @param {object} node
 * @returns {string}
 */
function catalogIdFromNode(node) {
  const catalog = widgetByName(node, "catalog");
  const raw = catalog?.value;
  if (raw) {
    return String(raw);
  }
  const rel = app.graph?.extra?.lab_rel || "";
  if (rel) {
    return String(rel);
  }
  return familyCatalog(node);
}

/**
 * Combo labels for one catalog: row labels then Custom.
 * @param {object[]} rows
 * @returns {string[]}
 */
function catalogLabels(rows) {
  const labels = [];
  const seen = new Set();
  for (const row of rows || []) {
    const label = String(row?.label || "").trim();
    const key = label.toLowerCase();
    if (!label || key === SAMPLE_CUSTOM || seen.has(key)) {
      continue;
    }
    seen.add(key);
    labels.push(label);
  }
  labels.push(SAMPLE_CUSTOM);
  return labels;
}

/**
 * Bind options.values to this node's catalog labels (ignore union overwrites).
 * @param {object} widget
 * @param {object} node
 * @returns {void}
 */
function installValuesGetter(widget, node) {
  if (!widget) {
    return;
  }
  if (!widget.options) {
    widget.options = {};
  }
  if (!Array.isArray(node._ezSampleLabels)) {
    node._ezSampleLabels = [SAMPLE_CUSTOM];
  }
  if (widget._ezValuesBound) {
    return;
  }
  widget._ezValuesBound = true;
  try {
    delete widget.options.values;
  } catch {
    // NodeDef values may be non-configurable; defineProperty still wins.
  }
  Object.defineProperty(widget.options, "values", {
    configurable: true,
    enumerable: true,
    /**
     * Visible Sample prompt labels for this graph.
     * @returns {string[]}
     */
    get() {
      return node._ezSampleLabels || [SAMPLE_CUSTOM];
    },
    /**
     * Ignore refreshComboInNodes restoring the Python union.
     * @returns {void}
     */
    set() {},
  });
}

/**
 * WEB_DIRECTORY URL for a sample JSON file.
 * @param {string} name
 * @returns {string}
 */
function samplesUrl(name) {
  return `/extensions/ez_prompt_enhance/samples/${name}`;
}

/**
 * Fetch JSON or return null on HTTP error.
 * @param {string} url
 * @returns {Promise<object|null>}
 */
async function loadJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    return null;
  }
  return response.json();
}

/**
 * Load and cache sample rows for a catalog id (index.json then stem.json).
 * @param {string} catalogId
 * @returns {Promise<object[]>}
 */
async function loadCatalog(catalogId) {
  if (!catalogId) {
    return [];
  }
  if (catalogCache.has(catalogId)) {
    return catalogCache.get(catalogId);
  }
  const index = await loadJson(samplesUrl("index.json"));
  let stem = catalogId;
  if (index && index[catalogId]) {
    stem = index[catalogId];
  }
  const rows = (await loadJson(samplesUrl(`${stem}.json`))) || [];
  catalogCache.set(catalogId, rows);
  catalogCache.set(stem, rows);
  return rows;
}

/**
 * Match a sample combo value to a catalog row, or null for custom.
 * @param {object[]} rows
 * @param {string} sample
 * @returns {object|null}
 */
function lookupSample(rows, sample) {
  const key = String(sample || "").trim().toLowerCase();
  if (!key || key === SAMPLE_CUSTOM) {
    return null;
  }
  return (
    rows.find(
      (row) =>
        String(row.label || "").toLowerCase() === key ||
        String(row.id || "").toLowerCase() === key,
    ) || null
  );
}

/**
 * Copy prompt/tags/lyrics from a sample row onto matching widgets.
 * @param {object} node
 * @param {object} row
 * @param {boolean} readOnly
 * @returns {void}
 */
function applySampleRow(node, row, readOnly) {
  if (row.prompt != null && widgetByName(node, "prompt")) {
    setTextWidget(widgetByName(node, "prompt"), row.prompt, readOnly);
  }
  if (row.prompt != null && widgetByName(node, "sources")) {
    setTextWidget(widgetByName(node, "sources"), row.prompt, readOnly);
  }
  if (row.tags != null && widgetByName(node, "tags")) {
    setTextWidget(widgetByName(node, "tags"), row.tags, readOnly);
  }
  if (row.lyrics != null && widgetByName(node, "lyrics")) {
    setTextWidget(widgetByName(node, "lyrics"), row.lyrics, readOnly);
  }
}

/**
 * True when the live widget text differs from the catalog field.
 * @param {object|undefined} widget
 * @param {*} catalogText
 * @returns {boolean}
 */
function textDiverged(widget, catalogText) {
  if (!widget || catalogText == null) {
    return false;
  }
  return String(widget.value ?? "") !== String(catalogText);
}

/**
 * Unlock prompt-like textareas on a node.
 * @param {object} node
 * @returns {void}
 */
function unlockTextWidgets(node) {
  for (const name of TEXT_WIDGET_NAMES) {
    const widget = widgetByName(node, name);
    if (widget?.inputEl) {
      widget.inputEl.readOnly = false;
      widget.inputEl.style.opacity = "1";
    }
  }
}

/**
 * Select Sample custom so Queue encodes the textarea, not the catalog row.
 * @param {object} node
 * @returns {void}
 */
function freezeSampleToCustom(node) {
  if (node?._ezApplyingSample) {
    return;
  }
  const sampleWidget = widgetByName(node, "sample");
  if (!sampleWidget) {
    return;
  }
  const choice = String(sampleWidget.value || "")
    .trim()
    .toLowerCase();
  if (!choice || choice === SAMPLE_CUSTOM) {
    return;
  }
  node._ezApplyingSample = true;
  try {
    sampleWidget.value = SAMPLE_CUSTOM;
    if (Array.isArray(node.widgets_values) && node.widgets) {
      const idx = node.widgets.indexOf(sampleWidget);
      if (idx >= 0) {
        node.widgets_values[idx] = SAMPLE_CUSTOM;
      }
    }
    if (typeof sampleWidget.callback === "function") {
      sampleWidget.callback(SAMPLE_CUSTOM, app.canvas, node);
    }
    const graph = node.graph;
    if (graph && typeof graph.setDirtyCanvas === "function") {
      graph.setDirtyCanvas(true, true);
    }
  } finally {
    node._ezApplyingSample = false;
  }
  unlockTextWidgets(node);
}

/**
 * Chain prompt/tags/lyrics/sources callbacks so typing selects Sample custom.
 * @param {object} node
 * @returns {void}
 */
function bindTextWatchers(node) {
  for (const name of TEXT_WIDGET_NAMES) {
    const widget = widgetByName(node, name);
    if (!widget || widget._ezPromptWatch) {
      continue;
    }
    widget._ezPromptWatch = true;
    const prior = widget.callback;
    /**
     * Chain the prior callback then freeze Sample at custom.
     * @returns {void}
     */
    widget.callback = function () {
      if (typeof prior === "function") {
        prior.apply(this, arguments);
      }
      freezeSampleToCustom(node);
    };
  }
}

/**
 * If live text diverged from the selected sample, select Sample custom.
 * @param {object} node
 * @returns {Promise<void>}
 */
async function freezeSampleIfPromptDiverged(node) {
  const sampleWidget = widgetByName(node, "sample");
  if (!sampleWidget) {
    return;
  }
  const choice = sampleWidget.value;
  const isCustom =
    !choice || String(choice).trim().toLowerCase() === SAMPLE_CUSTOM;
  if (isCustom) {
    return;
  }
  const rows = await loadCatalog(catalogIdFromNode(node));
  const row = lookupSample(rows, choice);
  if (!row) {
    return;
  }
  if (
    textDiverged(widgetByName(node, "prompt"), row.prompt) ||
    textDiverged(widgetByName(node, "sources"), row.prompt) ||
    textDiverged(widgetByName(node, "tags"), row.tags) ||
    textDiverged(widgetByName(node, "lyrics"), row.lyrics)
  ) {
    freezeSampleToCustom(node);
  }
}

/**
 * Refresh sample combo values and apply or unlock the chosen sample.
 * @param {object} node
 * @returns {Promise<void>}
 */
async function syncSample(node) {
  const sampleWidget = widgetByName(node, "sample");
  if (!sampleWidget) {
    return;
  }
  installValuesGetter(sampleWidget, node);
  const rows = await loadCatalog(catalogIdFromNode(node));
  node._ezSampleLabels = catalogLabels(rows);
  const choice = sampleWidget.value;
  const isCustom =
    !choice || String(choice).trim().toLowerCase() === SAMPLE_CUSTOM;
  const row = lookupSample(rows, choice);
  if (!isCustom && row) {
    node._ezApplyingSample = true;
    try {
      applySampleRow(node, row, true);
    } finally {
      node._ezApplyingSample = false;
    }
    return;
  }
  unlockTextWidgets(node);
}

/**
 * Bind the sample combo; re-sync after graph load even if already bound.
 * @param {object} node
 * @returns {void}
 */
function bindSamplePicker(node) {
  const sampleWidget = widgetByName(node, "sample");
  if (!sampleWidget) {
    return;
  }
  installValuesGetter(sampleWidget, node);
  bindTextWatchers(node);
  if (!sampleWidget._ezSampleBound) {
    sampleWidget._ezSampleBound = true;
    const prior = sampleWidget.callback;
    /**
     * Chain the prior callback then apply the selected sample.
     * @returns {void}
     */
    sampleWidget.callback = function () {
      if (typeof prior === "function") {
        prior.apply(this, arguments);
      }
      syncSample(node);
    };
    /**
     * Use the textarea when it diverged from the selected sample.
     * @returns {Promise<void>}
     */
    sampleWidget.beforeQueued = async function () {
      await freezeSampleIfPromptDiverged(node);
    };
  }
  syncSample(node);
}

/**
 * Bind or refresh Sample prompt combos on every enhance/sample node.
 * @returns {void}
 */
function syncAllSamplePickers() {
  for (const node of app.graph?.nodes || []) {
    const ntype = node?.comfyClass || node?.type;
    if (NODE_CLASSES.has(ntype)) {
      bindSamplePicker(node);
    }
  }
}

const PREVIEW = "CLIP prompt";
const STATUS = "Enhance status";

/**
 * Join a UI message field into a display string.
 * @param {object} message
 * @param {string} key
 * @returns {string}
 */
function textFromMessage(message, key) {
  const raw = message?.[key];
  if (raw == null) {
    return "";
  }
  if (Array.isArray(raw)) {
    return raw.filter(Boolean).join("\n");
  }
  return String(raw);
}

/**
 * Create or update a non-serialized STRING widget.
 * @param {object} node
 * @param {string} name
 * @param {string} text
 * @param {boolean} multiline
 * @returns {void}
 */
function upsertWidget(node, name, text, multiline) {
  if (!node.widgets) {
    return;
  }
  let widget = node.widgets.find((w) => w.name === name);
  if (!widget) {
    const made = ComfyWidgets.STRING(
      node,
      name,
      ["STRING", { multiline }],
      app,
    );
    widget = made.widget;
    widget.serialize = false;
    widget.serializeValue = async () => undefined;
    if (widget.inputEl) {
      widget.inputEl.readOnly = true;
      widget.inputEl.style.opacity = "0.75";
    }
  }
  widget.value = text;
}

/**
 * Fill CLIP prompt and enhance-status widgets.
 * @param {object} node
 * @param {string} text
 * @param {string} status
 * @returns {void}
 */
function populate(node, text, status) {
  upsertWidget(node, PREVIEW, text, true);
  upsertWidget(node, STATUS, status, false);
}

app.registerExtension({
  name: "ez_prompt_enhance.preview",
  /**
   * Wrap enhance/sample nodes with preview widgets and the sample picker.
   * @param {object} nodeType
   * @param {object} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (!NODE_CLASSES.has(nodeData.name)) {
      return;
    }
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    /**
     * Seed preview widgets (except sample/research) and bind the sample combo.
     * @returns {void}
     */
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      if (!PREVIEW_SKIP.has(nodeData.name)) {
        populate(this, "", "Queue to rewrite");
      }
      bindSamplePicker(this);
    };
    const onConfigure = nodeType.prototype.onConfigure;
    /**
     * Re-bind the sample picker after a graph load.
     * @returns {void}
     */
    nodeType.prototype.onConfigure = function () {
      onConfigure?.apply(this, arguments);
      bindSamplePicker(this);
    };
    const onExecuted = nodeType.prototype.onExecuted;
    /**
     * Refresh CLIP preview widgets from the last execution payload.
     * @param {object} message
     * @returns {void}
     */
    nodeType.prototype.onExecuted = function (message) {
      onExecuted?.apply(this, arguments);
      if (nodeData.name === "EZAppForge") {
        return;
      }
      populate(
        this,
        textFromMessage(message, "text"),
        textFromMessage(message, "passthrough"),
      );
    };
  },
  /**
   * Re-filter Sample prompt combos after the graph extra/catalog widgets land.
   * @returns {Promise<void>}
   */
  async setup() {
    const graph = app.graph;
    if (graph?.addEventListener) {
      graph.addEventListener("configured", () => {
        syncAllSamplePickers();
      });
    }
  },
  /**
   * Prefer the typed prompt over a stale sample combo at Queue.
   * @returns {Promise<void>}
   */
  async beforeQueued() {
    for (const node of app.graph?.nodes || []) {
      const ntype = node?.comfyClass || node?.type;
      if (NODE_CLASSES.has(ntype)) {
        await freezeSampleIfPromptDiverged(node);
      }
    }
  },
});

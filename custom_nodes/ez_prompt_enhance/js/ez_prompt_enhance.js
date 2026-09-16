/**
 * Prompt-enhance / sample-picker frontend: catalog samples plus CLIP preview.
 *
 * Nodes 2.0: set widget.value; treat inputEl as optional (Vue STRING widgets
 * have no canvas textarea). Sample combo uses widget.options.values.
 */
import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

const NODE_CLASSES = new Set([
  "EZKleinPromptEnhance",
  "EZWanPromptEnhance",
  "EZLTXPromptEnhance",
  "EZNegativePromptEnhance",
  "EZAceStepPromptEnhance",
  "EZRapLyrics",
  "EZPodcastScript",
  "EZSamplePrompt",
  "EZCreativeResearch",
]);

const SAMPLE_CUSTOM = "custom";
const catalogCache = new Map();

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
 * Catalog id from the catalog widget, else extra.lab_rel.
 * @param {object} node
 * @returns {string}
 */
function catalogIdFromNode(node) {
  const catalog = widgetByName(node, "catalog");
  const raw = catalog?.value;
  if (raw) {
    return String(raw);
  }
  return app.graph?.extra?.lab_rel || "";
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
  if (row.tags != null && widgetByName(node, "tags")) {
    setTextWidget(widgetByName(node, "tags"), row.tags, readOnly);
  }
  if (row.lyrics != null && widgetByName(node, "lyrics")) {
    setTextWidget(widgetByName(node, "lyrics"), row.lyrics, readOnly);
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
  const rows = await loadCatalog(catalogIdFromNode(node));
  if (rows.length && sampleWidget.options) {
    const labels = rows.map((row) => row.label);
    if (!labels.includes(SAMPLE_CUSTOM)) {
      labels.push(SAMPLE_CUSTOM);
    }
    sampleWidget.options.values = labels;
  }
  const choice = sampleWidget.value;
  const isCustom =
    !choice || String(choice).trim().toLowerCase() === SAMPLE_CUSTOM;
  const row = lookupSample(rows, choice);
  if (!isCustom && row) {
    applySampleRow(node, row, true);
    return;
  }
  for (const name of ["prompt", "tags", "lyrics"]) {
    const widget = widgetByName(node, name);
    if (widget?.inputEl) {
      widget.inputEl.readOnly = false;
      widget.inputEl.style.opacity = "1";
    }
  }
}

/**
 * Bind the sample combo once so changes reload catalog text.
 * @param {object} node
 * @returns {void}
 */
function bindSamplePicker(node) {
  const sampleWidget = widgetByName(node, "sample");
  if (!sampleWidget || sampleWidget._ezSampleBound) {
    return;
  }
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
  syncSample(node);
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
      if (nodeData.name !== "EZSamplePrompt" && nodeData.name !== "EZCreativeResearch") {
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
      populate(
        this,
        textFromMessage(message, "text"),
        textFromMessage(message, "passthrough"),
      );
    };
  },
});

/**
 * Prompt-enhance / sample-picker frontend: catalog samples plus CLIP preview.
 *
 * Nodes 2.0: set widget.value; treat inputEl as optional (Vue STRING widgets
 * have no canvas textarea). Sample combo uses a getter on widget.options.values
 * so App Mode (Vue) and refreshComboInNodes cannot restore the Python union.
 * Typing prompt/tags/lyrics/sources selects Sample custom so Queue uses the box
 * at any Quality. Named samples still copy the recipe into the box.
 * Linked CLIPTextEncode (Positive / Motion) and ACE encoder widgets are a
 * preview: they follow Prompt / Rewrite prompt, then the rewritten string
 * after Queue. Queue still uses the STRING link, not the preview widget.
 * That preview sets options.serialize (prompt inclusion) only. widget.serialize
 * is persistence; clearing it before the encoder configures skips tags/lyrics
 * and shifts seed, BPM, meter, language, key, and cfg.
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

const CLIP_DEST_TYPES = new Set([
  "CLIPTextEncode",
  "TextEncodeAceStepAudio1.5",
]);

const SAMPLE_CUSTOM = "custom";
const TEXT_WIDGET_NAMES = ["prompt", "tags", "lyrics", "sources"];
const catalogCache = new Map();

/** Node type + mode/flavor -> catalog stem. Mirrors samples.py _FAMILY_FOR_MODE. */
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
      syncLinkedClipFromWidgets(node);
    };
  }
}

/**
 * Sample custom when live text diverged from the last applied row.
 * Runs inside widget.beforeQueued, so it must stay synchronous: an async body
 * suspends and its effect lands after graphToPrompt has serialized the payload.
 * @param {object} node
 * @returns {void}
 */
function freezeSampleIfPromptDivergedSync(node) {
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
  if (!node._ezSampleRow && !node._ezSampleCatalog) {
    return;
  }
  const row = node._ezSampleRow || {};
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
 * If live text diverged from the selected sample, select Sample custom.
 * Uses the row syncSample applied when available; otherwise fetches the catalog.
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
  if (node._ezSampleRow) {
    freezeSampleIfPromptDivergedSync(node);
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
  const catalogId = catalogIdFromNode(node);
  const rows = await loadCatalog(catalogId);
  node._ezSampleLabels = catalogLabels(rows);
  const choice = sampleWidget.value;
  const isCustom =
    !choice || String(choice).trim().toLowerCase() === SAMPLE_CUSTOM;
  const row = lookupSample(rows, choice);
  if (!isCustom && row) {
    node._ezSampleRow = row;
    node._ezSampleCatalog = catalogId;
    node._ezApplyingSample = true;
    try {
      applySampleRow(node, row, true);
    } finally {
      node._ezApplyingSample = false;
    }
    syncLinkedClipFromWidgets(node);
    return;
  }
  node._ezSampleRow = null;
  unlockTextWidgets(node);
  syncLinkedClipFromWidgets(node);
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
     * Use the textarea when it diverged from the selected sample. Synchronous:
     * the frontend awaits nothing here, so an async body would land too late.
     * @returns {void}
     */
    sampleWidget.beforeQueued = function () {
      freezeSampleIfPromptDivergedSync(node);
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

/**
 * Resolve a graph link by id (array, map, or object keyed by id).
 * @param {object|undefined} graph
 * @param {*} lid
 * @returns {object|Array|null}
 */
function linkById(graph, lid) {
  const links = graph?.links;
  if (!links) {
    return null;
  }
  if (typeof links.get === "function") {
    return links.get(lid) || links.get(Number(lid)) || links.get(String(lid)) || null;
  }
  if (Array.isArray(links)) {
    return (
      links.find((item) => {
        const id = Array.isArray(item) ? item[0] : item?.id;
        return Number(id) === Number(lid);
      }) || null
    );
  }
  return links[lid] ?? links[Number(lid)] ?? links[String(lid)] ?? null;
}

/**
 * Destination node id and slot from a serialized or live link.
 * @param {object|Array|null} link
 * @returns {{nodeId: *, slot: number}|null}
 */
function linkDest(link) {
  if (!link) {
    return null;
  }
  if (Array.isArray(link)) {
    return { nodeId: link[3], slot: Number(link[4]) };
  }
  const nodeId = link.target_id ?? link.targetId;
  const slot = link.target_slot ?? link.targetSlot;
  if (nodeId == null) {
    return null;
  }
  return { nodeId, slot: Number(slot) };
}

/**
 * Live graph node by id.
 * @param {object|undefined} graph
 * @param {*} nid
 * @returns {object|undefined}
 */
function nodeById(graph, nid) {
  if (graph && typeof graph.getNodeById === "function") {
    return graph.getNodeById(nid) || graph.getNodeById(Number(nid));
  }
  return (graph?.nodes || []).find((item) => Number(item.id) === Number(nid));
}

/**
 * CLIP / ACE encoder nodes wired from one STRING output slot.
 * @param {object} node
 * @param {number} slot
 * @returns {{node: object, widgetName: string}[]}
 */
function linkedDestinations(node, slot) {
  const output = node.outputs?.[slot];
  const ids = output?.links || [];
  const graph = node.graph || app.graph;
  const found = [];
  for (const lid of ids) {
    const destInfo = linkDest(linkById(graph, lid));
    if (!destInfo) {
      continue;
    }
    const dest = nodeById(graph, destInfo.nodeId);
    if (!dest) {
      continue;
    }
    const ntype = dest.comfyClass || dest.type;
    if (!CLIP_DEST_TYPES.has(ntype)) {
      continue;
    }
    const inp = dest.inputs?.[destInfo.slot];
    const widgetName = inp?.widget?.name || inp?.name || "text";
    found.push({ node: dest, widgetName });
  }
  return found;
}

/**
 * Write a linked CLIP/ACE preview widget. Queue uses the STRING link.
 * @param {object} dest
 * @param {string} widgetName
 * @param {string} text
 * @returns {void}
 */
function setLinkedClipWidget(dest, widgetName, text) {
  const widget = widgetByName(dest, widgetName);
  if (!widget) {
    const destType = dest.comfyClass || dest.type;
    if (
      widgetName === "text" &&
      destType === "CLIPTextEncode" &&
      Array.isArray(dest.widgets_values)
    ) {
      dest.widgets_values[0] = text;
    }
    return;
  }
  widget.options = widget.options || {};
  widget.options.serialize = false;
  setTextWidget(widget, text, true);
  if (Array.isArray(dest.widgets_values) && dest.widgets) {
    const idx = dest.widgets.indexOf(widget);
    if (idx >= 0) {
      dest.widgets_values[idx] = text;
    }
  }
  const graph = dest.graph || app.graph;
  if (graph && typeof graph.setDirtyCanvas === "function") {
    graph.setDirtyCanvas(true, true);
  }
}

/**
 * Copy slot text onto linked CLIPTextEncode / ACE encoder widgets and record
 * the destinations so an unlink can un-pin the widget afterwards.
 * @param {object} node
 * @param {Object<number, string>} slotTexts
 * @returns {void}
 */
function pushClipPreview(node, slotTexts) {
  if (!Array.isArray(node._ezClipPreviewDests)) {
    node._ezClipPreviewDests = [];
  }
  const tracked = node._ezClipPreviewDests;
  for (const [slot, text] of Object.entries(slotTexts || {})) {
    if (text == null) {
      continue;
    }
    for (const dest of linkedDestinations(node, Number(slot))) {
      const nodeId = dest.node.id;
      if (
        !tracked.some(
          (item) =>
            Number(item.nodeId) === Number(nodeId) &&
            item.widgetName === dest.widgetName,
        )
      ) {
        tracked.push({ nodeId, widgetName: dest.widgetName });
      }
      setLinkedClipWidget(dest.node, dest.widgetName, text);
    }
  }
}

/**
 * Source text this node pushes into an encoder widget of this name.
 * Mirrors the tag/lyrics/prompt selection in syncLinkedClipFromWidgets.
 * @param {object} node
 * @param {string} widgetName
 * @returns {string}
 */
function sourceTextForWidget(node, widgetName) {
  const slotTexts = slotTextsFromWidgets(node);
  if (widgetName === "lyrics") {
    return slotTexts[1] ?? slotTexts[0] ?? "";
  }
  return slotTexts[0] ?? "";
}

/**
 * Un-pin encoder widgets whose link the user deleted: a widget left with
 * options.serialize false is dropped from the queue payload entirely, so it
 * goes back to serializing and carries the current source text.
 * @param {object} node
 * @returns {void}
 */
function restoreUnlinkedClipWidgets(node) {
  const tracked = node._ezClipPreviewDests;
  if (!Array.isArray(tracked) || !tracked.length) {
    return;
  }
  const graph = node.graph || app.graph;
  const linked = [];
  const slotCount = Math.max(node.outputs?.length || 0, 1);
  for (let slot = 0; slot < slotCount; slot += 1) {
    linked.push(...linkedDestinations(node, slot));
  }
  let restored = false;
  for (const entry of tracked) {
    const stillLinked = linked.some(
      (item) =>
        Number(item.node.id) === Number(entry.nodeId) &&
        item.widgetName === entry.widgetName,
    );
    if (stillLinked) {
      continue;
    }
    const dest = nodeById(graph, entry.nodeId);
    const widget = dest ? widgetByName(dest, entry.widgetName) : undefined;
    if (!widget) {
      continue;
    }
    widget.options = widget.options || {};
    widget.options.serialize = true;
    setTextWidget(widget, sourceTextForWidget(node, entry.widgetName), false);
    if (Array.isArray(dest.widgets_values) && dest.widgets) {
      const idx = dest.widgets.indexOf(widget);
      if (idx >= 0) {
        dest.widgets_values[idx] = String(widget.value ?? "");
      }
    }
    restored = true;
  }
  if (restored && typeof graph?.setDirtyCanvas === "function") {
    graph.setDirtyCanvas(true, true);
  }
}

/**
 * After Queue, copy the rewritten CLIP string onto linked encoder widgets.
 * @param {object} node
 * @param {object} message
 * @returns {void}
 */
function pushClipPreviewFromMessage(node, message) {
  const blob = textFromMessage(message, "text");
  const ntype = node?.comfyClass || node?.type || "";
  if (ntype === "EZAceStepPromptEnhance") {
    const parts = blob.split("\n---\n");
    const slotTexts = { 0: parts[0] || "" };
    if (parts.length > 1) {
      slotTexts[1] = parts.slice(1).join("\n---\n");
    }
    pushClipPreview(node, slotTexts);
    return;
  }
  pushClipPreview(node, { 0: blob });
}

/**
 * True when the Enhance / Rewrite prompt widget is on.
 * @param {object} node
 * @returns {boolean}
 */
function enhanceIsOn(node) {
  const widget = widgetByName(node, "enhance");
  if (!widget) {
    return true;
  }
  const value = widget.value;
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
 * Prompt / tags / lyrics text this node feeds into the encoder slots.
 * @param {object} node
 * @returns {Object<number, string>}
 */
function slotTextsFromWidgets(node) {
  const tags = widgetByName(node, "tags");
  const lyrics = widgetByName(node, "lyrics");
  const prompt = widgetByName(node, "prompt");
  /** @type {Object<number, string>} */
  const slotTexts = {};
  if (tags) {
    slotTexts[0] = String(tags.value ?? "");
    if (lyrics) {
      slotTexts[1] = String(lyrics.value ?? "");
    }
  } else if (lyrics && !prompt) {
    slotTexts[0] = String(lyrics.value ?? "");
  } else if (prompt) {
    slotTexts[0] = String(prompt.value ?? "");
  }
  return slotTexts;
}

/**
 * Push current prompt/tags/lyrics onto linked CLIP widgets.
 * @param {object} node
 * @returns {void}
 */
function syncLinkedClipFromWidgets(node) {
  const ntype = node?.comfyClass || node?.type || "";
  if (PREVIEW_SKIP.has(ntype)) {
    return;
  }
  const slotTexts = slotTextsFromWidgets(node);
  if (!Object.keys(slotTexts).length) {
    return;
  }
  pushClipPreview(node, slotTexts);
  if (!widgetByName(node, "enhance")) {
    return;
  }
  const preview = slotTexts[1]
    ? `${slotTexts[0]}\n---\n${slotTexts[1]}`
    : slotTexts[0] || "";
  if (!enhanceIsOn(node)) {
    populate(node, preview, "enhance off");
    return;
  }
  populate(node, "", "Queue to rewrite");
}

/**
 * Family id on a Negative Prompt Enhance node.
 * @param {object} node
 * @returns {string}
 */
function negativeFamily(node) {
  const widget = widgetByName(node, "family");
  return String(widget?.value || "klein");
}

/**
 * Set one widget and sync only its own widgets_values slot.
 * Mirrors ez_quality.js setWidgetValue so App Mode sees the new state.
 * @param {object} node
 * @param {object} widget
 * @param {*} value
 * @returns {void}
 */
function setNodeWidgetValue(node, widget, value) {
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
}

/**
 * Copy Rewrite negative onto the other nodes of the same family.
 * One App toggle drives every shot. The guard stops the callback loop.
 * @param {object} source
 * @returns {void}
 */
function syncNegativeFamily(source) {
  const ntype = source?.comfyClass || source?.type || "";
  if (ntype !== "EZNegativePromptEnhance" || source._ezNegSync) {
    return;
  }
  const family = negativeFamily(source);
  const on = enhanceIsOn(source);
  const nodes = source.graph?.nodes || app.graph?.nodes || [];
  for (const other of nodes) {
    if (other === source) {
      continue;
    }
    if ((other.comfyClass || other.type) !== "EZNegativePromptEnhance") {
      continue;
    }
    if (negativeFamily(other) !== family) {
      continue;
    }
    const widget = widgetByName(other, "enhance");
    if (!widget || widget.value === on) {
      continue;
    }
    other._ezNegSync = true;
    setNodeWidgetValue(other, widget, on);
    other._ezNegSync = false;
  }
}

/**
 * Chain the Enhance / Rewrite prompt widget onto the CLIP preview.
 * Rewrite negative also copies across the same family.
 * @param {object} node
 * @returns {void}
 */
function bindEnhanceWatcher(node) {
  const widget = widgetByName(node, "enhance");
  if (!widget || widget._ezClipWatch) {
    return;
  }
  widget._ezClipWatch = true;
  const prior = widget.callback;
  /**
   * Chain the prior callback then refresh CLIP from the toggle.
   * @returns {void}
   */
  widget.callback = function () {
    if (typeof prior === "function") {
      prior.apply(this, arguments);
    }
    syncLinkedClipFromWidgets(node);
    syncNegativeFamily(node);
  };
  /**
   * Re-sync linked encoders at Queue so the payload matches the UI, whatever
   * changed the toggle (App Mode panel, canvas, graph load). Body stays
   * synchronous: the frontend serializes right after this returns.
   * @returns {void}
   */
  widget.beforeQueued = function () {
    syncLinkedClipFromWidgets(node);
    restoreUnlinkedClipWidgets(node);
  };
}

/**
 * Bind prompt/enhance watchers and seed the linked CLIP preview.
 * @param {object} node
 * @returns {void}
 */
function bindClipPreview(node) {
  const ntype = node?.comfyClass || node?.type || "";
  if (!NODE_CLASSES.has(ntype) || PREVIEW_SKIP.has(ntype)) {
    return;
  }
  bindTextWatchers(node);
  bindEnhanceWatcher(node);
  syncLinkedClipFromWidgets(node);
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
      bindClipPreview(this);
    };
    const onConfigure = nodeType.prototype.onConfigure;
    /**
     * Re-bind the sample picker after a graph load.
     * @returns {void}
     */
    nodeType.prototype.onConfigure = function () {
      onConfigure?.apply(this, arguments);
      bindSamplePicker(this);
      bindClipPreview(this);
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
      pushClipPreviewFromMessage(this, message);
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
        for (const node of app.graph?.nodes || []) {
          bindClipPreview(node);
          restoreUnlinkedClipWidgets(node);
        }
      });
    }
  },
});

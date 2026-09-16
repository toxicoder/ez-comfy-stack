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

function widgetByName(node, name) {
  return node.widgets?.find((w) => w.name === name);
}

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

function catalogIdFromNode(node) {
  const catalog = widgetByName(node, "catalog");
  const raw = catalog?.value;
  if (raw) {
    return String(raw);
  }
  return app.graph?.extra?.lab_rel || "";
}

function samplesUrl(name) {
  return `/extensions/ez_prompt_enhance/samples/${name}`;
}

async function loadJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    return null;
  }
  return response.json();
}

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

function bindSamplePicker(node) {
  const sampleWidget = widgetByName(node, "sample");
  if (!sampleWidget || sampleWidget._ezSampleBound) {
    return;
  }
  sampleWidget._ezSampleBound = true;
  const prior = sampleWidget.callback;
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

function populate(node, text, status) {
  upsertWidget(node, PREVIEW, text, true);
  upsertWidget(node, STATUS, status, false);
}

app.registerExtension({
  name: "ez_prompt_enhance.preview",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (!NODE_CLASSES.has(nodeData.name)) {
      return;
    }
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      if (nodeData.name !== "EZSamplePrompt" && nodeData.name !== "EZCreativeResearch") {
        populate(this, "", "Queue to rewrite");
      }
      bindSamplePicker(this);
    };
    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      onConfigure?.apply(this, arguments);
      bindSamplePicker(this);
    };
    const onExecuted = nodeType.prototype.onExecuted;
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

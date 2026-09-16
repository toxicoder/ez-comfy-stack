import { app } from "../../scripts/app.js";

const QUALITY_LAB = "lab";
const QUALITY_DRAFT = "draft";
const QUALITY_HIGH = "high";

const KLEIN_DISTILLED = "flux-2-klein-4b-fp8.safetensors";
const KLEIN_BASE = "flux-2-klein-base-4b-fp8.safetensors";
const KLEIN_DRAFT_STEPS = 4;
const KLEIN_DRAFT_CFG = 1.0;
const KLEIN_HIGH_DISTILLED_STEPS = 8;
const KLEIN_HIGH_DISTILLED_CFG = 1.0;
const KLEIN_HIGH_BASE_STEPS = 24;
const KLEIN_HIGH_BASE_CFG = 3.5;
const WAN_DRAFT_STEPS = 12;
const WAN_HIGH_STEPS = 28;
const LTX_DRAFT_STEPS = 12;
const LTX_HIGH_STEPS = 28;
const AUDIO_DRAFT_STEPS = 4;
const AUDIO_HIGH_STEPS = 16;
const TRELLIS_DRAFT_STEPS = 8;
const TRELLIS_HIGH_STEPS = 20;

const BANNED = [
  "flux.2-dev",
  "flux-2-dev",
  "flux2-dev",
  "klein-9b",
  "flux-2-klein-9b",
  "minimax",
  "seedance",
  "kling",
  "z_image_turbo",
];

const snapshots = new WeakMap();
let applying = false;

function widgetByName(node, name) {
  return node.widgets?.find((w) => w.name === name);
}

function comboValues(widget) {
  const raw = widget?.options?.values;
  if (typeof raw === "function") {
    try {
      const got = raw();
      return Array.isArray(got) ? got.map(String) : [];
    } catch {
      return [];
    }
  }
  if (Array.isArray(raw)) {
    return raw.map(String);
  }
  return [];
}

function isBannedUnet(name) {
  const blob = String(name || "").toLowerCase();
  return BANNED.some((needle) => blob.includes(needle));
}

function isKlein4b(name) {
  const blob = String(name || "").toLowerCase();
  if (blob.includes("9b")) {
    return false;
  }
  return blob.includes("klein") && blob.includes("4b");
}

function isWan14(name) {
  return String(name || "")
    .toLowerCase()
    .includes("14b");
}

function occupancy() {
  const mode = app.graph?.extra?.lab_app_mode?.occupancy;
  if (mode) {
    return String(mode);
  }
  const types = new Set((app.graph?.nodes || []).map((n) => n.type));
  if (types.has("EZFilmConcat")) {
    return "film";
  }
  if (types.has("MeshToFile3D")) {
    return "trellis";
  }
  if (types.has("SaveAudio") || types.has("SaveAudioMP3")) {
    return "audio";
  }
  if (types.has("VHS_VideoCombine") || types.has("SaveVideo")) {
    for (const node of app.graph?.nodes || []) {
      if (node.type !== "UNETLoader") {
        continue;
      }
      const unet = widgetByName(node, "unet_name")?.value;
      const blob = String(unet || "").toLowerCase();
      if (blob.includes("ltx")) {
        return "ltx";
      }
      if (blob.includes("wan")) {
        return "wan";
      }
    }
    return "wan";
  }
  if (types.has("SaveImage")) {
    return "klein";
  }
  return "";
}

function firstUnetName() {
  for (const node of app.graph?.nodes || []) {
    if (node.type !== "UNETLoader") {
      continue;
    }
    const widget = widgetByName(node, "unet_name");
    if (widget?.value) {
      return String(widget.value);
    }
  }
  return "";
}

function graphHasWan14() {
  for (const node of app.graph?.nodes || []) {
    if (node.type !== "UNETLoader") {
      continue;
    }
    const widget = widgetByName(node, "unet_name");
    if (isWan14(widget?.value)) {
      return true;
    }
  }
  return false;
}

function pickUnet(name, available) {
  if (!name || isBannedUnet(name)) {
    return null;
  }
  if (available.length && !available.includes(name)) {
    return null;
  }
  return name;
}

function resolveOverlay(choice, authoredSteps, unetName, available) {
  const occ = occupancy();
  if (choice === QUALITY_LAB || occ === "llm" || occ === "none") {
    return {};
  }
  if (isWan14(unetName) || graphHasWan14()) {
    return {};
  }
  if (occ === "klein" || isKlein4b(unetName)) {
    if (choice === QUALITY_DRAFT) {
      const unet =
        isKlein4b(unetName) && unetName === KLEIN_BASE
          ? pickUnet(KLEIN_DISTILLED, available)
          : null;
      return {
        steps: KLEIN_DRAFT_STEPS,
        cfg: KLEIN_DRAFT_CFG,
        unet_name: unet,
      };
    }
    const base = pickUnet(KLEIN_BASE, available);
    if (base && isKlein4b(unetName)) {
      return {
        steps: KLEIN_HIGH_BASE_STEPS,
        cfg: KLEIN_HIGH_BASE_CFG,
        unet_name: base,
      };
    }
    return {
      steps: Math.max(authoredSteps, KLEIN_HIGH_DISTILLED_STEPS),
      cfg: KLEIN_HIGH_DISTILLED_CFG,
    };
  }
  if (occ === "wan") {
    return { steps: choice === QUALITY_DRAFT ? WAN_DRAFT_STEPS : WAN_HIGH_STEPS };
  }
  if (occ === "ltx" || occ === "film") {
    return { steps: choice === QUALITY_DRAFT ? LTX_DRAFT_STEPS : LTX_HIGH_STEPS };
  }
  if (occ === "audio") {
    return {
      steps: choice === QUALITY_DRAFT ? AUDIO_DRAFT_STEPS : AUDIO_HIGH_STEPS,
    };
  }
  if (occ === "trellis") {
    return {
      steps: choice === QUALITY_DRAFT ? TRELLIS_DRAFT_STEPS : TRELLIS_HIGH_STEPS,
    };
  }
  return {};
}

function setWidget(widget, value) {
  if (!widget || widget.value === value) {
    return;
  }
  widget.value = value;
  if (typeof widget.callback === "function") {
    widget.callback(value);
  }
}

function snapshotGraph() {
  const snap = [];
  for (const node of app.graph?.nodes || []) {
    if (!node?.widgets) {
      continue;
    }
    for (const widget of node.widgets) {
      if (
        widget.name === "steps" ||
        widget.name === "cfg" ||
        widget.name === "unet_name"
      ) {
        snap.push({ node, name: widget.name, value: widget.value });
      }
    }
  }
  snapshots.set(app.graph, snap);
}

function restoreSnapshot() {
  const snap = snapshots.get(app.graph);
  if (!snap) {
    return;
  }
  for (const row of snap) {
    const widget = widgetByName(row.node, row.name);
    setWidget(widget, row.value);
  }
}

function applyQuality(choice) {
  if (applying) {
    return;
  }
  applying = true;
  try {
    const normalized = String(choice || QUALITY_LAB)
      .trim()
      .toLowerCase();
    if (normalized === QUALITY_LAB) {
      restoreSnapshot();
      return;
    }
    const unetName = firstUnetName();
    const unetNode = (app.graph?.nodes || []).find((n) => n.type === "UNETLoader");
    const available = comboValues(widgetByName(unetNode || {}, "unet_name"));
    for (const node of app.graph?.nodes || []) {
      const stepsWidget = widgetByName(node, "steps");
      const cfgWidget = widgetByName(node, "cfg");
      const unetWidget = widgetByName(node, "unet_name");
      const authoredSteps = Number(stepsWidget?.value) || 0;
      const overlay = resolveOverlay(
        normalized,
        authoredSteps,
        unetWidget?.value ? String(unetWidget.value) : unetName,
        available,
      );
      if (stepsWidget && overlay.steps != null) {
        setWidget(stepsWidget, overlay.steps);
      }
      if (cfgWidget && overlay.cfg != null) {
        setWidget(cfgWidget, overlay.cfg);
      }
      if (
        unetWidget &&
        overlay.unet_name &&
        isKlein4b(String(unetWidget.value || "")) &&
        !isBannedUnet(overlay.unet_name)
      ) {
        setWidget(unetWidget, overlay.unet_name);
      }
    }
  } finally {
    applying = false;
  }
}

function bindQualityNode(node) {
  const widget = widgetByName(node, "quality");
  if (!widget || widget._ezQualityBound) {
    return;
  }
  widget._ezQualityBound = true;
  widget.label = "Quality";
  const prior = widget.callback;
  widget.callback = function (value) {
    if (typeof prior === "function") {
      prior.apply(this, arguments);
    }
    applyQuality(value);
  };
  widget.beforeQueued = function () {
    applyQuality(widget.value);
  };
}

function bindAll() {
  snapshotGraph();
  for (const node of app.graph?.nodes || []) {
    if (node.type === "EZQuality" || node.comfyClass === "EZQuality") {
      bindQualityNode(node);
      const widget = widgetByName(node, "quality");
      if (widget && widget.value && widget.value !== QUALITY_LAB) {
        applyQuality(widget.value);
      }
    }
  }
}

app.registerExtension({
  name: "ez_quality.overlay",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "EZQuality") {
      return;
    }
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      bindQualityNode(this);
    };
  },
  async afterConfigureGraph() {
    bindAll();
  },
});

/**
 * EZQuality frontend: overlay sampler + UNET/CLIP/VAE on named qualities.
 *
 * Nodes 2.0: writes widget.value (and widget.callback). Does not change size
 * or length. Custom freezes the last overlay. Lab restores the authored snapshot.
 */
import { app } from "../../scripts/app.js";

const QUALITY_CUSTOM = "custom";
const QUALITY_DRAFT = "draft";
const QUALITY_LAB = "lab";
const QUALITY_STANDARD = "standard";
const QUALITY_HIGH = "high";
const QUALITY_ULTRA = "ultra";
const QUALITY_MAX = "max";

const KLEIN_DISTILLED = "flux-2-klein-4b-fp8.safetensors";
const KLEIN_NVFP4 = "flux-2-klein-4b-nvfp4.safetensors";
const KLEIN_BASE = "flux-2-klein-base-4b-fp8.safetensors";
const KLEIN_9B = "flux-2-klein-9b-fp8.safetensors";
const KLEIN_9B_BASE = "flux-2-klein-base-9b-fp8.safetensors";
const KLEIN_9B_NVFP4 = "flux-2-klein-9b-nvfp4.safetensors";
const FLUX2_DEV = "flux2_dev_fp8mixed.safetensors";
const CLIP_4B = "qwen_3_4b.safetensors";
const CLIP_8B = "qwen_3_8b_fp8mixed.safetensors";
const CLIP_MISTRAL = "mistral_3_small_flux2_bf16.safetensors";
const CLIP_TYPE_FLUX2 = "flux2";
const VAE_FULL = "flux2-vae.safetensors";
const VAE_SMALL = "full_encoder_small_decoder.safetensors";

const KLEIN_DRAFT_STEPS = 4;
const KLEIN_DRAFT_CFG = 1.0;
const KLEIN_STANDARD_STEPS = 8;
const KLEIN_STANDARD_CFG = 1.0;
const KLEIN_HIGH_DISTILLED_STEPS = 8;
const KLEIN_HIGH_DISTILLED_CFG = 1.0;
const KLEIN_HIGH_BASE_STEPS = 24;
const KLEIN_HIGH_BASE_CFG = 3.5;
const KLEIN_9B_STEPS = 4;
const KLEIN_9B_CFG = 1.0;
const KLEIN_9B_BASE_STEPS = 20;
const KLEIN_9B_BASE_CFG = 5.0;
const FLUX2_DEV_STEPS = 20;
const FLUX2_DEV_CFG = 4.0;
const WAN_DRAFT_STEPS = 12;
const WAN_STANDARD_STEPS = 20;
const WAN_HIGH_STEPS = 28;
const WAN_MAX_STEPS = 32;
const LTX_DRAFT_STEPS = 12;
const LTX_STANDARD_STEPS = 20;
const LTX_HIGH_STEPS = 28;
const LTX_MAX_STEPS = 32;
const AUDIO_DRAFT_STEPS = 4;
const AUDIO_STANDARD_STEPS = 8;
const AUDIO_HIGH_STEPS = 16;
const AUDIO_MAX_STEPS = 24;
const TRELLIS_DRAFT_STEPS = 8;
const TRELLIS_STANDARD_STEPS = 12;
const TRELLIS_HIGH_STEPS = 20;
const TRELLIS_MAX_STEPS = 28;

const BANNED = ["minimax", "seedance", "kling", "z_image_turbo"];

const snapshots = new WeakMap();
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
 * Combo option strings from widget.options.values (array or getter).
 * @param {object|undefined} widget
 * @returns {string[]}
 */
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

/**
 * True when a UNET filename matches a banned family.
 * @param {string} name
 * @returns {boolean}
 */
function isBannedUnet(name) {
  const blob = String(name || "").toLowerCase();
  return BANNED.some((needle) => blob.includes(needle));
}

/**
 * True when a UNET filename is Klein 4B (not 9B).
 * @param {string} name
 * @returns {boolean}
 */
function isKlein4b(name) {
  const blob = String(name || "").toLowerCase();
  if (blob.includes("9b")) {
    return false;
  }
  return blob.includes("klein") && blob.includes("4b");
}

/**
 * True when a UNET filename is Klein 9B.
 * @param {string} name
 * @returns {boolean}
 */
function isKlein9b(name) {
  const blob = String(name || "").toLowerCase();
  return blob.includes("klein") && blob.includes("9b");
}

/**
 * True when a UNET filename looks like Wan 14B.
 * @param {string} name
 * @returns {boolean}
 */
function isWan14(name) {
  return String(name || "")
    .toLowerCase()
    .includes("14b");
}

/**
 * True when a CLIP filename is a Flux.2 text encoder.
 * @param {string} name
 * @returns {boolean}
 */
function isFlux2Clip(name) {
  const blob = String(name || "").toLowerCase();
  return blob.includes("qwen_3_") || (blob.includes("mistral") && blob.includes("flux2"));
}

/**
 * True when a VAE filename is a Flux.2 VAE.
 * @param {string} name
 * @returns {boolean}
 */
function isFlux2Vae(name) {
  const blob = String(name || "").toLowerCase();
  return blob.includes("flux2-vae") || blob.includes("small_decoder");
}

/**
 * Infer graph occupancy from extra.lab_app_mode or node types.
 * @returns {string}
 */
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

/**
 * First UNETLoader unet_name on the graph, or empty.
 * @returns {string}
 */
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

/**
 * True when any UNETLoader is Wan 14B (overlay is a no-op then).
 * @returns {boolean}
 */
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

/**
 * Return name when it is present and not banned; otherwise null.
 * @param {string} name
 * @param {string[]} available
 * @returns {string|null}
 */
function pickUnet(name, available) {
  if (!name || isBannedUnet(name)) {
    return null;
  }
  if (available.length && !available.includes(name)) {
    return null;
  }
  return name;
}

/**
 * Return name when present in the combo (empty combo = no check).
 * @param {string} name
 * @param {string[]} available
 * @returns {string|null}
 */
function pickFile(name, available) {
  if (!name) {
    return null;
  }
  if (available.length && !available.includes(name)) {
    return null;
  }
  return name;
}

/**
 * Wan 5B step overlay.
 * @param {string} choice
 * @returns {number}
 */
function wanSteps(choice) {
  if (choice === QUALITY_DRAFT) {
    return WAN_DRAFT_STEPS;
  }
  if (choice === QUALITY_STANDARD) {
    return WAN_STANDARD_STEPS;
  }
  if (choice === QUALITY_MAX) {
    return WAN_MAX_STEPS;
  }
  return WAN_HIGH_STEPS;
}

/**
 * LTX step overlay.
 * @param {string} choice
 * @returns {number}
 */
function ltxSteps(choice) {
  if (choice === QUALITY_DRAFT) {
    return LTX_DRAFT_STEPS;
  }
  if (choice === QUALITY_STANDARD) {
    return LTX_STANDARD_STEPS;
  }
  if (choice === QUALITY_MAX) {
    return LTX_MAX_STEPS;
  }
  return LTX_HIGH_STEPS;
}

/**
 * Apache high overlay (4B base if present).
 * @param {number} authoredSteps
 * @param {string} unetName
 * @param {string[]} available
 * @param {string[]} clips
 * @param {string[]} vaes
 * @returns {object}
 */
function kleinHigh(authoredSteps, unetName, available, clips, vaes) {
  const base = pickUnet(KLEIN_BASE, available);
  const clip = pickFile(CLIP_4B, clips);
  const vae = pickFile(VAE_SMALL, vaes) || pickFile(VAE_FULL, vaes);
  if (base && (isKlein4b(unetName) || isKlein9b(unetName) || !unetName)) {
    return {
      steps: KLEIN_HIGH_BASE_STEPS,
      cfg: KLEIN_HIGH_BASE_CFG,
      unet_name: base,
      clip_name: clip,
      vae_name: vae,
      clip_type: CLIP_TYPE_FLUX2,
    };
  }
  return {
    steps: Math.max(authoredSteps, KLEIN_HIGH_DISTILLED_STEPS),
    cfg: KLEIN_HIGH_DISTILLED_CFG,
    unet_name: pickUnet(KLEIN_DISTILLED, available),
    clip_name: clip,
    vae_name: vae,
    clip_type: CLIP_TYPE_FLUX2,
  };
}

/**
 * Steps/CFG/UNET/CLIP/VAE overlay for a quality choice, or {} for freeze / no-op.
 * @param {string} choice
 * @param {number} authoredSteps
 * @param {string} unetName
 * @param {string[]} available
 * @param {string[]} clips
 * @param {string[]} vaes
 * @returns {object}
 */
function resolveOverlay(choice, authoredSteps, unetName, available, clips, vaes) {
  const occ = occupancy();
  if (
    choice === QUALITY_LAB ||
    choice === QUALITY_CUSTOM ||
    occ === "llm" ||
    occ === "none"
  ) {
    return {};
  }
  if (isWan14(unetName) || graphHasWan14()) {
    return {};
  }
  if (occ === "klein" || isKlein4b(unetName) || isKlein9b(unetName)) {
    const clip4 = pickFile(CLIP_4B, clips);
    const clip8 = pickFile(CLIP_8B, clips);
    const vae = pickFile(VAE_SMALL, vaes) || pickFile(VAE_FULL, vaes);
    if (choice === QUALITY_DRAFT) {
      let unet = null;
      if (isKlein4b(unetName) || isKlein9b(unetName)) {
        unet = pickUnet(KLEIN_NVFP4, available) || pickUnet(KLEIN_DISTILLED, available);
      }
      return {
        steps: KLEIN_DRAFT_STEPS,
        cfg: KLEIN_DRAFT_CFG,
        unet_name: unet,
        clip_name: clip4,
        vae_name: vae,
        clip_type: CLIP_TYPE_FLUX2,
      };
    }
    if (choice === QUALITY_STANDARD) {
      return {
        steps: KLEIN_STANDARD_STEPS,
        cfg: KLEIN_STANDARD_CFG,
        unet_name: pickUnet(KLEIN_DISTILLED, available),
        clip_name: clip4,
        vae_name: vae,
        clip_type: CLIP_TYPE_FLUX2,
      };
    }
    if (choice === QUALITY_ULTRA) {
      const nine = pickUnet(KLEIN_9B, available) || pickUnet(KLEIN_9B_NVFP4, available);
      if (nine) {
        return {
          steps: KLEIN_9B_STEPS,
          cfg: KLEIN_9B_CFG,
          unet_name: nine,
          clip_name: clip8,
          vae_name: vae,
          clip_type: CLIP_TYPE_FLUX2,
        };
      }
      return kleinHigh(authoredSteps, unetName, available, clips, vaes);
    }
    if (choice === QUALITY_MAX) {
      const nineBase = pickUnet(KLEIN_9B_BASE, available);
      if (nineBase) {
        return {
          steps: KLEIN_9B_BASE_STEPS,
          cfg: KLEIN_9B_BASE_CFG,
          unet_name: nineBase,
          clip_name: clip8,
          vae_name: vae,
          clip_type: CLIP_TYPE_FLUX2,
        };
      }
      const dev = pickUnet(FLUX2_DEV, available);
      if (dev) {
        return {
          steps: FLUX2_DEV_STEPS,
          cfg: FLUX2_DEV_CFG,
          unet_name: dev,
          clip_name: pickFile(CLIP_MISTRAL, clips),
          vae_name: vae,
          clip_type: CLIP_TYPE_FLUX2,
        };
      }
      return kleinHigh(authoredSteps, unetName, available, clips, vaes);
    }
    return kleinHigh(authoredSteps, unetName, available, clips, vaes);
  }
  if (occ === "wan") {
    return { steps: wanSteps(choice) };
  }
  if (occ === "ltx" || occ === "film") {
    return { steps: ltxSteps(choice) };
  }
  if (occ === "audio") {
    if (choice === QUALITY_DRAFT) {
      return { steps: AUDIO_DRAFT_STEPS };
    }
    if (choice === QUALITY_STANDARD) {
      return { steps: AUDIO_STANDARD_STEPS };
    }
    if (choice === QUALITY_MAX) {
      return { steps: AUDIO_MAX_STEPS };
    }
    return { steps: AUDIO_HIGH_STEPS };
  }
  if (occ === "trellis") {
    if (choice === QUALITY_DRAFT) {
      return { steps: TRELLIS_DRAFT_STEPS };
    }
    if (choice === QUALITY_STANDARD) {
      return { steps: TRELLIS_STANDARD_STEPS };
    }
    if (choice === QUALITY_MAX) {
      return { steps: TRELLIS_MAX_STEPS };
    }
    return { steps: TRELLIS_HIGH_STEPS };
  }
  return {};
}

/**
 * Set a widget value and fire its callback when the value actually changes.
 * @param {object|undefined} widget
 * @param {*} value
 * @returns {void}
 */
function setWidget(widget, value) {
  if (!widget || widget.value === value) {
    return;
  }
  widget.value = value;
  if (typeof widget.callback === "function") {
    widget.callback(value);
  }
}

/**
 * Snapshot authored steps/cfg/loader names so lab can restore them.
 * @returns {void}
 */
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
        widget.name === "unet_name" ||
        widget.name === "clip_name" ||
        widget.name === "vae_name" ||
        widget.name === "type"
      ) {
        snap.push({ node, name: widget.name, value: widget.value });
      }
    }
  }
  snapshots.set(app.graph, snap);
}

/**
 * Restore the last authored snapshot onto the live graph.
 * @returns {void}
 */
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

/**
 * Apply or restore a quality overlay across sampler/loader widgets.
 * @param {string} choice
 * @returns {void}
 */
function applyQuality(choice) {
  if (applying) {
    return;
  }
  applying = true;
  try {
    const normalized = String(choice || QUALITY_LAB)
      .trim()
      .toLowerCase();
    if (normalized === QUALITY_CUSTOM) {
      return;
    }
    if (normalized === QUALITY_LAB) {
      restoreSnapshot();
      return;
    }
    const unetName = firstUnetName();
    const unetNode = (app.graph?.nodes || []).find((n) => n.type === "UNETLoader");
    const clipNode = (app.graph?.nodes || []).find((n) => n.type === "CLIPLoader");
    const vaeNode = (app.graph?.nodes || []).find((n) => n.type === "VAELoader");
    const available = comboValues(widgetByName(unetNode || {}, "unet_name"));
    const clips = comboValues(widgetByName(clipNode || {}, "clip_name"));
    const vaes = comboValues(widgetByName(vaeNode || {}, "vae_name"));
    for (const node of app.graph?.nodes || []) {
      const stepsWidget = widgetByName(node, "steps");
      const cfgWidget = widgetByName(node, "cfg");
      const unetWidget = widgetByName(node, "unet_name");
      const clipWidget = widgetByName(node, "clip_name");
      const typeWidget = widgetByName(node, "type");
      const vaeWidget = widgetByName(node, "vae_name");
      const authoredSteps = Number(stepsWidget?.value) || 0;
      const overlay = resolveOverlay(
        normalized,
        authoredSteps,
        unetWidget?.value ? String(unetWidget.value) : unetName,
        available,
        clips,
        vaes,
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
        !isWan14(String(unetWidget.value || "")) &&
        !isBannedUnet(overlay.unet_name)
      ) {
        setWidget(unetWidget, overlay.unet_name);
      }
      if (
        clipWidget &&
        overlay.clip_name &&
        (!clipWidget.value || isFlux2Clip(String(clipWidget.value)))
      ) {
        setWidget(clipWidget, overlay.clip_name);
      }
      if (typeWidget && overlay.clip_type && node.type === "CLIPLoader") {
        setWidget(typeWidget, overlay.clip_type);
      }
      if (
        vaeWidget &&
        overlay.vae_name &&
        (!vaeWidget.value || isFlux2Vae(String(vaeWidget.value)))
      ) {
        setWidget(vaeWidget, overlay.vae_name);
      }
    }
  } finally {
    applying = false;
  }
}

/**
 * Bind the quality combo once so changes and Queue apply the overlay.
 * @param {object} node
 * @returns {void}
 */
function bindQualityNode(node) {
  const widget = widgetByName(node, "quality");
  if (!widget || widget._ezQualityBound) {
    return;
  }
  widget._ezQualityBound = true;
  widget.label = "Quality";
  const prior = widget.callback;
  /**
   * Chain the prior callback then overlay the chosen quality.
   * @param {*} value
   * @returns {void}
   */
  widget.callback = function (value) {
    if (typeof prior === "function") {
      prior.apply(this, arguments);
    }
    applyQuality(value);
  };
  /**
   * Re-apply the current quality immediately before Queue.
   * @returns {void}
   */
  widget.beforeQueued = function () {
    applyQuality(widget.value);
  };
}

/**
 * Snapshot the graph and bind every EZQuality node.
 * @returns {void}
 */
function bindAll() {
  snapshotGraph();
  for (const node of app.graph?.nodes || []) {
    if (node.type === "EZQuality" || node.comfyClass === "EZQuality") {
      bindQualityNode(node);
      const widget = widgetByName(node, "quality");
      if (
        widget &&
        widget.value &&
        widget.value !== QUALITY_LAB &&
        widget.value !== QUALITY_CUSTOM
      ) {
        applyQuality(widget.value);
      }
    }
  }
}

app.registerExtension({
  name: "ez_quality.overlay",
  /**
   * Wrap EZQuality so the combo applies overlays on create.
   * @param {object} nodeType
   * @param {object} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "EZQuality") {
      return;
    }
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    /**
     * Bind the quality combo when the node is created.
     * @returns {void}
     */
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      bindQualityNode(this);
    };
  },
  /**
   * Re-bind overlays after a graph load.
   * @returns {Promise<void>}
   */
  async afterConfigureGraph() {
    bindAll();
  },
});

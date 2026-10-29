/**
 * EZQuality frontend: overlay sampler + UNET/CLIP/VAE on named qualities.
 *
 * Nodes 2.0: writes widget.value plus the matching widgets_values slot, and
 * fires widget.callback. Every step count, CFG, and weight name comes from
 * ez_quality_presets.js, which presets.py generates; this file holds no tier
 * number and no weight filename of its own.
 *
 * The rule the whole file serves: the combo shows what the queued prompt
 * holds. applyQuality names a tier only when every write it asked for landed,
 * and deriveQualityTier reads the tier back out of the live widgets, so a
 * dropped write, a missing widget, or a hand-edited value cannot leave a tier
 * name painted on the combo. Custom keeps the live values; lab restores the
 * authored snapshot. Prompt widgets are never overlaid.
 */
import { app } from "../../scripts/app.js";
import {
  EZ_QUALITY_CHOICES,
  EZ_QUALITY_CUSTOM,
  EZ_QUALITY_FAMILIES,
  EZ_QUALITY_FIELDS,
  EZ_QUALITY_LABELS,
  EZ_QUALITY_LAB,
  EZ_QUALITY_NAMED,
  EZ_QUALITY_OWNED,
  EZ_QUALITY_TABLE,
} from "./ez_quality_presets.js";

// Combo ids this build still has to accept from saved graphs. The option list
// itself and every value behind it come from the generated table.
const QUALITY_FREE_COMMERCIAL = "Free Commercial Use (<$10M)";
const QUALITY_FREE_COMMERCIAL_ALIAS = "free_commercial";

// Family ids that carry no tier at all, so an unknown occupancy is a no-op.
const FAMILY_NOOP = "none";
const FAMILY_LLM = "llm";
const FAMILY_KLEIN3 = "klein3";

const CLIP_16_9_LABEL = "16:9 LTX feeder (1280x704)";
const CLIP_9_16_LABEL = "9:16 LTX feeder (768x1280)";
const GENERIC_16_9 = [
  "aspect_16_9_draft",
  "16:9 draft (768x432)",
  "aspect_16_9",
  "16:9 (1280x720)",
  "aspect_16_9_mid",
  "16:9 mid (1024x576)",
];
const GENERIC_9_16 = [
  "aspect_9_16_draft",
  "9:16 draft (432x768)",
  "aspect_9_16",
  "9:16 (576x1024)",
];

// Catalog policy, not tier data: these families are never lawful on this box.
const BANNED = ["minimax", "seedance", "kling", "z_image_turbo"];

/**
 * Overlay field -> widget name on its owning node type. The overlay field
 * clip_type is the CLIPLoader widget literally named "type".
 */
const FIELD_WIDGET_NAMES = {
  steps: "steps",
  cfg: "cfg",
  unet_name: "unet_name",
  clip_name: "clip_name",
  vae_name: "vae_name",
  clip_type: "type",
};

/**
 * Overlay fields each node type owns, mirroring presets.apply_to_graph:
 * steps/CFG only on KSampler, each loader name only on its own loader.
 */
const OVERLAY_FIELDS_BY_TYPE = {
  KSampler: ["steps", "cfg"],
  UNETLoader: ["unet_name"],
  CLIPLoader: ["clip_name", "clip_type"],
  VAELoader: ["vae_name"],
};

// Value no field comparison accepts: the targeted instances of one field
// disagree, so the graph holds no single value for it.
const DIVERGENT = Symbol("ez-quality-divergent");

const snapshots = new WeakMap();
const applyingByGraph = new WeakMap();
const syncingByGraph = new WeakMap();
const defaulted = new WeakMap();
const seedingByGraph = new WeakMap();
// graph -> Map(widget -> value the overlay last wrote); lets Queue spot user edits.
const overlayWrites = new WeakMap();
// graph -> {choice, fields, attempts}; a tier a missing widget blocked, retried once.
const pendingApplies = new WeakMap();
const LAST_QUALITY_KEY = "ez-comfy.quality.last";

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
 * Node type, honoring the Nodes 2.0 comfyClass alias.
 * @param {object|undefined} node
 * @returns {string}
 */
function nodeType(node) {
  return String(node?.comfyClass || node?.type || "");
}

/**
 * True for the Quality combo node.
 * @param {object|undefined} node
 * @returns {boolean}
 */
function isQualityNode(node) {
  return nodeType(node) === "EZQuality";
}

/**
 * True when a node is mode 0. Muted and bypassed lanes are not in the queued
 * prompt, so they neither drive the overlay nor wear its caption.
 * @param {object|undefined} node
 * @returns {boolean}
 */
function isLiveNode(node) {
  return !node || node.mode == null || node.mode === 0;
}

/**
 * First Quality combo the overlay should act on, ignoring muted copies.
 * @param {object|undefined} graph
 * @returns {object|null}
 */
function firstLiveQualityNode(graph) {
  for (const node of graph?.nodes || []) {
    if (isQualityNode(node) && isLiveNode(node) && widgetByName(node, "quality")) {
      return node;
    }
  }
  return null;
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
 * Fold separators so the KLEIN3 needles match either filename style.
 * @param {string} name
 * @returns {string}
 */
function klein3Blob(name) {
  return String(name || "").toLowerCase().replaceAll(".", "-").replaceAll("_", "-");
}

/**
 * True when a UNET filename is FLUX 3 Image Klein (distilled, base, NVFP4).
 * @param {string} name
 * @returns {boolean}
 */
function isKlein3Unet(name) {
  const blob = klein3Blob(name);
  return blob.includes("flux3-image-klein") || blob.includes("flux-3-image-klein");
}

/**
 * True when a CLIP filename is the KLEIN3 Qwen3-VL text encoder.
 * @param {string} name
 * @returns {boolean}
 */
function isKlein3Clip(name) {
  return klein3Blob(name).includes("qwen3vl-4b");
}

/**
 * True when a UNET filename looks like Wan 14B.
 * @param {*} name
 * @returns {boolean}
 */
function isWan14(name) {
  return String(name || "")
    .toLowerCase()
    .includes("14b");
}

/**
 * True when any live UNETLoader holds Wan 14B, which the overlay never touches.
 * @param {object|undefined} graph
 * @returns {boolean}
 */
function graphHasWan14(graph) {
  for (const node of graph?.nodes || []) {
    if (nodeType(node) !== "UNETLoader" || !isLiveNode(node)) {
      continue;
    }
    if (isWan14(widgetByName(node, "unet_name")?.value)) {
      return true;
    }
  }
  return false;
}

/**
 * True when a UNET filename looks like FLUX.2-dev.
 * @param {string} name
 * @returns {boolean}
 */
function isFlux2Dev(name) {
  const lower = String(name || "").toLowerCase();
  const blob = lower.replaceAll(".", "-");
  return (
    blob.includes("flux2-dev") ||
    blob.includes("flux-2-dev") ||
    lower.includes("flux2_dev")
  );
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
 * True when a loader still holds a weight the overlay may replace, the same
 * swap guard presets.apply_to_graph applies server-side.
 * @param {string} field
 * @param {*} current
 * @returns {boolean}
 */
function isSwappableTarget(field, current) {
  const name = String(current || "");
  if (!name) {
    return true;
  }
  if (field === "unet_name") {
    return isKlein4b(name) || isKlein9b(name) || isFlux2Dev(name) || isKlein3Unet(name);
  }
  if (field === "clip_name") {
    return isFlux2Clip(name) || isKlein3Clip(name);
  }
  if (field === "vae_name") {
    return isFlux2Vae(name);
  }
  return true;
}

/**
 * True when any live loader pins FLUX 3 Image Klein weights.
 * @param {object|undefined} graph
 * @returns {boolean}
 */
function graphHasKlein3Weights(graph) {
  for (const node of graph?.nodes || []) {
    if (!isLiveNode(node)) {
      continue;
    }
    const ntype = nodeType(node);
    if (ntype === "UNETLoader" && isKlein3Unet(widgetByName(node, "unet_name")?.value)) {
      return true;
    }
    if (ntype === "CLIPLoader" && isKlein3Clip(widgetByName(node, "clip_name")?.value)) {
      return true;
    }
  }
  return false;
}

/**
 * Return a combo value this build knows, defaulting to lab.
 * @param {*} value
 * @returns {string}
 */
function normalizeQuality(value) {
  const folded = String(value || EZ_QUALITY_LAB)
    .trim()
    .toLowerCase();
  if (folded === QUALITY_FREE_COMMERCIAL_ALIAS) {
    return QUALITY_FREE_COMMERCIAL;
  }
  const known = EZ_QUALITY_CHOICES.find((item) => item.toLowerCase() === folded);
  return known || EZ_QUALITY_LAB;
}

/**
 * True when a format combo value is in a generic aspect list.
 * @param {string} value
 * @param {string[]} ids
 * @returns {boolean}
 */
function formatMatches(value, ids) {
  const folded = String(value || "")
    .trim()
    .toLowerCase();
  return ids.some((item) => item.toLowerCase() === folded);
}

/**
 * Snap generic 16:9 / 9:16 still formats to LTX feeder sizes.
 * Named platform jobs, Custom, and already-feeder rows stay put.
 * @param {object|undefined} graph
 * @returns {void}
 */
function retargetClipFormat(graph) {
  const g = graph || app.graph;
  if (occupancy(g) !== "klein") {
    return;
  }
  for (const node of g?.nodes || []) {
    if (nodeType(node) !== "EZImageFormat") {
      continue;
    }
    const widget = widgetByName(node, "format");
    if (!widget) {
      continue;
    }
    if (formatMatches(widget.value, GENERIC_16_9)) {
      setWidgetValue(node, widget, CLIP_16_9_LABEL);
    } else if (formatMatches(widget.value, GENERIC_9_16)) {
      setWidgetValue(node, widget, CLIP_9_16_LABEL);
    }
  }
}

/**
 * Infer graph occupancy from extra.lab_app_mode or node types.
 * @param {object|undefined} graph
 * @returns {string}
 */
function occupancy(graph) {
  const g = graph || app.graph;
  const mode = g?.extra?.lab_app_mode?.occupancy;
  if (mode) {
    return String(mode);
  }
  const types = new Set((g?.nodes || []).map((n) => n.type));
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
    for (const node of g?.nodes || []) {
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
 * Tier family the graph belongs to: its occupancy, Klein 3 when its weights
 * say so, and a no-op family for anything this table does not cover.
 * @param {object|undefined} graph
 * @returns {string}
 */
function graphFamily(graph) {
  const occ = String(occupancy(graph) || "");
  if (!EZ_QUALITY_FAMILIES.includes(occ)) {
    return FAMILY_NOOP;
  }
  const noOverlay = occ === FAMILY_NOOP || occ === FAMILY_LLM;
  if (!noOverlay && graphHasKlein3Weights(graph)) {
    return FAMILY_KLEIN3;
  }
  return occ;
}

/**
 * Fields one family's tiers ever set; an edit outside this list keeps the level.
 * @param {string} family
 * @returns {string[]}
 */
function ownedFields(family) {
  const owned = EZ_QUALITY_OWNED[family];
  return Array.isArray(owned) ? owned : [];
}

/**
 * Requested value per overlay field for one tier, or null for an unknown row.
 * @param {string} family
 * @param {string} tier
 * @returns {object|null}
 */
function tierRow(family, tier) {
  return EZ_QUALITY_TABLE[family]?.[tier] || null;
}

/**
 * Caption naming the swap a tier performs, empty when it changes nothing.
 * @param {string} family
 * @param {string} tier
 * @returns {string}
 */
function tierLabelFor(family, tier) {
  return String(EZ_QUALITY_LABELS[family]?.[tier] || "");
}

/**
 * String form of a widget value for edit detection (numbers compare as text).
 * @param {*} value
 * @returns {string}
 */
function widgetValueText(value) {
  return String(value == null ? "" : value);
}

/**
 * True when two widget values are the same text.
 * @param {*} a
 * @param {*} b
 * @returns {boolean}
 */
function sameWidgetValue(a, b) {
  return widgetValueText(a) === widgetValueText(b);
}

/**
 * Compare an observed widget value with a tier value the way presets.match_tier
 * does: numbers numerically, everything else as text, null equal only to null.
 * @param {*} left
 * @param {*} right
 * @returns {boolean}
 */
function sameTierValue(left, right) {
  if (left === DIVERGENT || right === DIVERGENT) {
    return false;
  }
  if (left == null || right == null) {
    return left == null && right == null;
  }
  if (typeof left === "number" || typeof right === "number") {
    const a = Number(left);
    const b = Number(right);
    return Number.isFinite(a) && Number.isFinite(b) && a === b;
  }
  return String(left) === String(right);
}

/**
 * Live widget per targeted instance of each overlay field, muted nodes skipped.
 * @param {object|undefined} graph
 * @returns {object} field -> Array of {node, widget}
 */
function collectOverlayInstances(graph) {
  const out = {};
  for (const field of EZ_QUALITY_FIELDS) {
    out[field] = [];
  }
  for (const node of graph?.nodes || []) {
    if (!isLiveNode(node)) {
      continue;
    }
    const ntype = nodeType(node);
    const fields = OVERLAY_FIELDS_BY_TYPE[ntype];
    if (!fields) {
      continue;
    }
    for (const field of fields) {
      const widget = widgetByName(node, FIELD_WIDGET_NAMES[field]);
      if (widget) {
        out[field].push({ node, widget });
      }
    }
  }
  return out;
}

/**
 * Collapse one field's instances to the single value they agree on.
 * @param {object[]} entries
 * @param {function} read reads one entry; undefined when it knows nothing
 * @returns {*} the shared value, null when the graph holds none, DIVERGENT
 * when the instances of the class hold different values
 */
function agreeOn(entries, read) {
  let shared = null;
  let seen = false;
  for (const entry of entries || []) {
    const value = read(entry);
    if (value === undefined) {
      continue;
    }
    if (!seen) {
      shared = value;
      seen = true;
      continue;
    }
    if (!sameTierValue(shared, value)) {
      return DIVERGENT;
    }
  }
  return shared;
}

/**
 * observed / authored pair per owned field, the two maps presets.match_tier
 * compares. A field its instances disagree on matches nothing, so a graph
 * whose samplers contradict each other is custom rather than a tier.
 * @param {object} graph
 * @param {string} family
 * @param {object} instances
 * @returns {object} {observed, authored}
 */
function overlayValues(graph, family, instances) {
  const snap = snapshots.get(graph);
  const observed = {};
  const authored = {};
  for (const field of ownedFields(family)) {
    const name = FIELD_WIDGET_NAMES[field];
    observed[field] = agreeOn(instances[field], (entry) => entry.widget.value);
    authored[field] = snap
      ? agreeOn(instances[field], (entry) => snapshotValueOf(snap, entry.node, name))
      : undefined;
  }
  return { observed, authored };
}

/**
 * Derive the quality the widgets actually hold.
 *
 * Named tiers win in table order, because the tier names what Queue would send.
 * Widgets still at their authored values read as lab; anything else, including
 * instances that contradict each other, is custom, so a graph that never
 * matched a tier cannot keep displaying one.
 * @param {object|undefined} graph
 * @param {string} family
 * @returns {string}
 */
function deriveQualityTier(graph, family) {
  if (!graph) {
    return EZ_QUALITY_LAB;
  }
  const owned = ownedFields(family);
  if (!owned.length) {
    return EZ_QUALITY_LAB;
  }
  const instances = collectOverlayInstances(graph);
  const seen = overlayValues(graph, family, instances);
  for (const tier of EZ_QUALITY_NAMED) {
    const row = tierRow(family, tier);
    if (row && owned.every((field) => sameTierValue(seen.observed[field], row[field]))) {
      return tier;
    }
  }
  if (
    snapHasValues(seen.authored) &&
    owned.every((field) => sameTierValue(seen.observed[field], seen.authored[field]))
  ) {
    return EZ_QUALITY_LAB;
  }
  return EZ_QUALITY_CUSTOM;
}

/**
 * True when the load-time snapshot covers every field it was asked about.
 * @param {object} authored
 * @returns {boolean}
 */
function snapHasValues(authored) {
  return Object.values(authored).every((value) => value !== undefined);
}

/**
 * Why one write cannot land, or empty when it can. An empty answer means the
 * queued prompt will really hold the tier value.
 * @param {string} field
 * @param {object} entry
 * @param {*} wanted
 * @param {boolean} refused true when a Wan 14B loader pins the graph
 * @returns {string}
 */
function writeBlockReason(field, entry, wanted, refused) {
  if (refused) {
    return "Wan 14B is not overlaid";
  }
  if (field === "unet_name" && isBannedUnet(String(wanted))) {
    return `${wanted} is not allowed`;
  }
  if (!isSwappableTarget(field, entry.widget.value)) {
    return `cannot swap ${widgetValueText(entry.widget.value)}`;
  }
  const available = comboValues(entry.widget);
  if (available.length && !available.includes(String(wanted))) {
    return `${wanted} not installed`;
  }
  if (widgetSlotIndex(entry.node, entry.widget) < 0) {
    return `${FIELD_WIDGET_NAMES[field]} has no prompt slot`;
  }
  return "";
}

/**
 * Decide every write one tier asks for, and record what cannot land.
 * @param {object} graph
 * @param {string} family
 * @param {string} tier
 * @returns {object} {writes, failures, missing}
 */
function planTierWrites(graph, family, tier) {
  const row = tierRow(family, tier);
  const instances = collectOverlayInstances(graph);
  const refused = graphHasWan14(graph);
  const writes = [];
  const failures = [];
  const missing = [];
  for (const field of ownedFields(family)) {
    const wanted = row ? row[field] : null;
    if (wanted == null) {
      continue;
    }
    const targets = instances[field] || [];
    if (!targets.length) {
      missing.push(field);
      continue;
    }
    for (const entry of targets) {
      if (sameTierValue(entry.widget.value, wanted)) {
        continue;
      }
      const reason = writeBlockReason(field, entry, wanted, refused);
      if (reason) {
        if (!failures.includes(reason)) {
          failures.push(reason);
        }
        continue;
      }
      writes.push({ node: entry.node, widget: entry.widget, field, value: wanted });
    }
  }
  return { writes, failures, missing };
}

/**
 * True when LiteGraph serializes this widget into widgets_values.
 * @param {object|undefined} widget
 * @returns {boolean}
 */
function isSerializedWidget(widget) {
  if (!widget || widget.type === "button") {
    return false;
  }
  return widget.serialize !== false && widget.options?.serialize !== false;
}

/**
 * widgets_values slot a widget serializes into. LiteGraph skips widgets it does
 * not serialize, so count only those; fall back to the raw position. -1 when no
 * slot can be trusted, which fails the write instead of diverging the prompt.
 * @param {object|undefined} node
 * @param {object|undefined} widget
 * @returns {number}
 */
function widgetSlotIndex(node, widget) {
  if (!node || !widget) {
    return -1;
  }
  if (!Array.isArray(node.widgets) || !Array.isArray(node.widgets_values)) {
    return -1;
  }
  let slot = 0;
  let found = -1;
  for (const item of node.widgets) {
    if (item === widget) {
      found = slot;
      break;
    }
    if (isSerializedWidget(item)) {
      slot += 1;
    }
  }
  if (found < 0) {
    found = node.widgets.indexOf(widget);
  }
  if (found < 0 || found >= node.widgets_values.length) {
    return -1;
  }
  return found;
}

/**
 * Write the value and that widget's own widgets_values slot, so the shown value
 * and the serialized prompt can never disagree.
 * @param {object|undefined} node
 * @param {object|undefined} widget
 * @param {*} value
 * @returns {void}
 */
function writeWidgetSlot(node, widget, value) {
  widget.value = value;
  if (Array.isArray(node?.widgets_values) && node.widgets) {
    const idx = widgetSlotIndex(node, widget);
    if (idx >= 0) {
      node.widgets_values[idx] = value;
    }
  }
}

/**
 * Notify Vue / App Mode that a graph moved.
 * @param {object|undefined} graph
 * @returns {void}
 */
function markGraphDirty(graph) {
  if (!graph) {
    return;
  }
  if (typeof graph.setDirtyCanvas === "function") {
    graph.setDirtyCanvas(true, true);
  }
  if (typeof graph.change === "function") {
    graph.change();
  }
}

/**
 * Set a widget value, its prompt slot, and notify Vue / App Mode (Nodes 2.0).
 * @param {object|undefined} node
 * @param {object|undefined} widget
 * @param {*} value
 * @returns {void}
 */
function setWidgetValue(node, widget, value) {
  if (!widget || widget.value === value) {
    return;
  }
  writeWidgetSlot(node, widget, value);
  if (typeof widget.callback === "function") {
    widget.callback(value, app.canvas, node);
  }
  markGraphDirty(node?.graph);
}

/**
 * Remember the value the overlay wrote so Queue can spot later user edits.
 * @param {object|undefined} graph
 * @param {object|undefined} widget
 * @param {*} value
 * @returns {void}
 */
function recordOverlayWrite(graph, widget, value) {
  if (!graph || !widget) {
    return;
  }
  let map = overlayWrites.get(graph);
  if (!map) {
    map = new Map();
    overlayWrites.set(graph, map);
  }
  map.set(widget, value);
}

/**
 * Forget overlay-write records for widgets being (re)written or restored.
 * @param {object|undefined} graph
 * @param {object[]} widgets
 * @returns {void}
 */
function clearOverlayWrites(graph, widgets) {
  const map = graph && overlayWrites.get(graph);
  if (!map) {
    return;
  }
  for (const widget of widgets) {
    map.delete(widget);
  }
}

/**
 * True when any overlay-written widget now holds a different (user-edited) value.
 * @param {object|undefined} graph
 * @returns {boolean}
 */
function hasOverlayEdits(graph) {
  const map = graph && overlayWrites.get(graph);
  if (!map || !map.size) {
    return false;
  }
  for (const entry of map.entries()) {
    if (!sameWidgetValue(entry[0].value, entry[1])) {
      return true;
    }
  }
  return false;
}

/**
 * Write one overlay value and record it as overlay-authored for this graph.
 * @param {object|undefined} graph
 * @param {object} node
 * @param {object} widget
 * @param {*} value
 * @returns {void}
 */
function applyOverlayWrite(graph, node, widget, value) {
  setWidgetValue(node, widget, value);
  recordOverlayWrite(graph, widget, value);
}

/**
 * Authored value for one widget of one node, or undefined when unrecorded.
 * @param {object[]|undefined} snap
 * @param {object} node
 * @param {string} name
 * @returns {*}
 */
function snapshotValueOf(snap, node, name) {
  for (const row of snap || []) {
    if (row.node === node && row.name === name) {
      return row.value;
    }
  }
  return undefined;
}

/**
 * True when a widget now holds a value the user typed over the authored one.
 * Lab restores this snapshot at Queue, so an edit that skipped the widget
 * callback (App Mode panel writes) must freeze Quality instead.
 * @param {object|undefined} graph
 * @returns {boolean}
 */
function hasSnapshotEdits(graph) {
  const snap = graph && snapshots.get(graph);
  if (!snap || !snap.length) {
    return false;
  }
  for (const row of snap) {
    const widget = widgetByName(row.node, row.name);
    if (widget && !sameWidgetValue(widget.value, row.value)) {
      return true;
    }
  }
  return false;
}

/**
 * Owned fields whose live widgets no longer hold what the overlay or the author
 * last put there. Names what diverged, for the custom caption.
 * @param {object|undefined} graph
 * @param {string} family
 * @returns {string[]}
 */
function divergedFields(graph, family) {
  const out = [];
  if (!graph) {
    return out;
  }
  const snap = snapshots.get(graph);
  const writes = overlayWrites.get(graph);
  const instances = collectOverlayInstances(graph);
  for (const field of ownedFields(family)) {
    const name = FIELD_WIDGET_NAMES[field];
    const dirty = (instances[field] || []).some((entry) => {
      if (writes && writes.has(entry.widget)) {
        // Overlay-authored: only a value past the last write is a user edit.
        return !sameWidgetValue(entry.widget.value, writes.get(entry.widget));
      }
      const authored = snapshotValueOf(snap, entry.node, name);
      return authored !== undefined && !sameWidgetValue(entry.widget.value, authored);
    });
    if (dirty) {
      out.push(field);
    }
  }
  return out;
}

/**
 * Caption for a tier whose writes all landed: the swap its table row performs.
 * @param {string} family
 * @param {string} tier
 * @returns {string}
 */
function tierCaption(family, tier) {
  if (tier === EZ_QUALITY_LAB) {
    return `${EZ_QUALITY_LAB} - authored defaults`;
  }
  const label = tierLabelFor(family, tier);
  return label ? `${tier} - ${label}` : String(tier);
}

/**
 * Caption for a custom state, naming what stopped the overlay. Never a tier
 * name: nothing here claims a write that did not land.
 * @param {string[]} reasons
 * @returns {string}
 */
function customCaption(reasons) {
  const bits = (reasons || []).filter(Boolean).slice(0, 2);
  if (!bits.length) {
    return `${EZ_QUALITY_CUSTOM} - last overlay frozen`;
  }
  return `${EZ_QUALITY_CUSTOM} - ${bits.join("; ")}`;
}

/**
 * Caption for custom chosen because the widgets left the tier behind.
 * @param {object|undefined} graph
 * @param {string} family
 * @returns {string}
 */
function keptEditsCaption(graph, family) {
  const fields = divergedFields(graph, family);
  const tail = fields.length ? ` (${fields.join(", ")})` : "";
  return `custom - kept your edits${tail}`;
}

/**
 * Remember a tier that missed a widget so the next graph configure retries once.
 * @param {object|undefined} graph
 * @param {string} choice
 * @param {string[]} fields
 * @returns {void}
 */
function recordPendingApply(graph, choice, fields) {
  if (!graph) {
    return;
  }
  const prior = pendingApplies.get(graph);
  const attempts = prior && prior.choice === choice ? prior.attempts : 0;
  pendingApplies.set(graph, { choice, fields: fields.slice(), attempts });
}

/**
 * Drop the retry record once a tier has fully landed.
 * @param {object|undefined} graph
 * @returns {void}
 */
function clearPendingApply(graph) {
  if (graph) {
    pendingApplies.delete(graph);
  }
}

/**
 * Retry once a tier that was blocked by a widget that did not exist yet.
 * @param {object|undefined} graph
 * @returns {boolean} true when a retry ran
 */
function retryPendingApply(graph) {
  const pending = graph && pendingApplies.get(graph);
  if (!pending || pending.attempts > 0 || !pending.fields.length) {
    return false;
  }
  const node = firstLiveQualityNode(graph);
  if (!node) {
    return false;
  }
  pending.attempts = 1;
  applyQuality(pending.choice, node);
  return true;
}

/**
 * Stamp a live Quality caption onto the graph extra and every visible combo.
 * With no visible Quality combo there is nothing to caption, so a muted lane
 * cannot leave a stamp on the graph either.
 * @param {object|undefined} graph
 * @param {string} caption
 * @returns {void}
 */
function stampQualityCaption(graph, caption) {
  if (!graph || !firstLiveQualityNode(graph)) {
    return;
  }
  graph.extra = graph.extra || {};
  graph.extra.lab_quality_caption = caption;
  for (const node of graph.nodes || []) {
    if (!isQualityNode(node) || !isLiveNode(node)) {
      continue;
    }
    const widget = widgetByName(node, "quality");
    if (widget) {
      widget.label = caption ? `Quality - ${caption}` : "Quality";
    }
  }
}

/**
 * Put one value on every Quality combo, so a second combo cannot keep showing a
 * tier another one dropped. The combo callback stays quiet; the caller decides
 * whether to apply, so setting the value cannot re-enter the overlay.
 * @param {object|undefined} graph
 * @param {string} value
 * @returns {void}
 */
function setQualityOnAll(graph, value) {
  if (!graph) {
    return;
  }
  let moved = false;
  for (const node of graph.nodes || []) {
    if (!isQualityNode(node)) {
      continue;
    }
    const widget = widgetByName(node, "quality");
    if (!widget || widget.value === value) {
      continue;
    }
    writeWidgetSlot(node, widget, value);
    moved = true;
  }
  if (moved) {
    markGraphDirty(graph);
  }
}

/**
 * Snapshot authored steps/cfg/loader names so lab can restore them.
 * @param {object|undefined} graph
 * @returns {void}
 */
function snapshotGraph(graph) {
  const g = graph || app.graph;
  const snap = [];
  for (const node of g?.nodes || []) {
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
  snapshots.set(g, snap);
  overlayWrites.set(g, new Map());
}

/**
 * Restore the last authored snapshot onto one graph.
 * @param {object|undefined} graph
 * @returns {void}
 */
function restoreSnapshot(graph) {
  const snap = snapshots.get(graph);
  if (!snap) {
    return;
  }
  const restored = [];
  for (const row of snap) {
    const widget = widgetByName(row.node, row.name);
    setWidgetValue(row.node, widget, row.value);
    if (widget) {
      restored.push(widget);
    }
  }
  // Lab restores authored values; those are not user edits.
  clearOverlayWrites(graph, restored);
}

/**
 * Apply or restore a quality overlay across sampler/loader widgets.
 *
 * A tier is named on the combo only when every write it asked for landed. Any
 * field it cannot write (widget not on the graph, weight not installed, a
 * loader holding a weight the overlay may not replace, a Wan 14B graph, no
 * prompt slot) fails the apply to custom with a caption saying what diverged.
 * @param {string} choice
 * @param {object|undefined} qualityNode
 * @returns {void}
 */
function applyQuality(choice, qualityNode) {
  const graph = qualityNode?.graph || app.graph;
  if (!graph || applyingByGraph.get(graph)) {
    return;
  }
  if (qualityNode && !isLiveNode(qualityNode)) {
    // A muted Quality lane is not in the queued prompt; it drives nothing.
    return;
  }
  applyingByGraph.set(graph, true);
  try {
    const normalized = normalizeQuality(choice);
    const family = graphFamily(graph);
    if (normalized === EZ_QUALITY_CUSTOM) {
      stampQualityCaption(graph, customCaption([]));
      return;
    }
    if (normalized === EZ_QUALITY_LAB) {
      restoreSnapshot(graph);
      clearPendingApply(graph);
      stampQualityCaption(graph, `${EZ_QUALITY_LAB} - authored defaults`);
      return;
    }
    const plan = planTierWrites(graph, family, normalized);
    if (plan.missing.length) {
      recordPendingApply(graph, normalized, plan.missing);
    } else {
      clearPendingApply(graph);
    }
    if (plan.failures.length || plan.missing.length) {
      const reasons = plan.failures.slice();
      for (const field of plan.missing) {
        reasons.push(`${FIELD_WIDGET_NAMES[field]} widget not on graph`);
      }
      setQualityOnAll(graph, EZ_QUALITY_CUSTOM);
      stampQualityCaption(graph, customCaption(reasons));
      return;
    }
    clearOverlayWrites(
      graph,
      plan.writes.map((write) => write.widget),
    );
    for (const write of plan.writes) {
      applyOverlayWrite(graph, write.node, write.widget, write.value);
    }
    if (normalized === QUALITY_FREE_COMMERCIAL) {
      retargetClipFormat(graph);
    }
    setQualityOnAll(graph, normalized);
    stampQualityCaption(graph, tierCaption(family, normalized));
  } finally {
    applyingByGraph.set(graph, false);
  }
}

/**
 * Read the tier back out of the live widgets and show it on every combo.
 * @param {object|undefined} graph
 * @returns {void}
 */
function syncQualityFromGraph(graph) {
  if (!graph || applyingByGraph.get(graph) || seedingByGraph.get(graph)) {
    return;
  }
  if (syncingByGraph.get(graph)) {
    return;
  }
  syncingByGraph.set(graph, true);
  try {
    const family = graphFamily(graph);
    const tier = deriveQualityTier(graph, family);
    setQualityOnAll(graph, tier);
    if (tier === EZ_QUALITY_CUSTOM) {
      stampQualityCaption(graph, customEditCaption(graph));
      return;
    }
    stampQualityCaption(graph, tierCaption(family, tier));
  } finally {
    syncingByGraph.set(graph, false);
  }
}

/**
 * Caption for a freeze: name the fields the operator moved, else say plainly
 * that no tier describes this graph.
 * @param {object|undefined} graph
 * @returns {string}
 */
function customEditCaption(graph) {
  const edited = hasOverlayEdits(graph) || hasSnapshotEdits(graph);
  if (!edited) {
    return `${EZ_QUALITY_CUSTOM} - no tier matches this graph`;
  }
  return keptEditsCaption(graph, graphFamily(graph));
}

/**
 * True when the graph carries a Quality combo at all.
 * @param {object|undefined} graph
 * @returns {boolean}
 */
function hasQualityNode(graph) {
  for (const node of graph?.nodes || []) {
    if (isQualityNode(node) && widgetByName(node, "quality")) {
      return true;
    }
  }
  return false;
}

/**
 * Select Quality custom on every combo so Queue keeps live overlay-widget
 * values. Skips overlay/seed writes. Does not persist custom as last named.
 * @param {object|undefined} graph
 * @param {string[]} [reasons] what stopped the overlay, for the caption
 * @returns {void}
 */
function freezeQualityToCustom(graph, reasons) {
  if (!graph || applyingByGraph.get(graph) || seedingByGraph.get(graph)) {
    return;
  }
  if (!hasQualityNode(graph)) {
    return;
  }
  setQualityOnAll(graph, EZ_QUALITY_CUSTOM);
  if (reasons && reasons.length) {
    stampQualityCaption(graph, customCaption(reasons));
    return;
  }
  stampQualityCaption(graph, customEditCaption(graph));
}

/**
 * True when this widget is a Quality overlay field on this node.
 * @param {object} node
 * @param {object|undefined} widget
 * @returns {boolean}
 */
function isOverlayWidget(node, widget) {
  const name = widget?.name;
  if (!name) {
    return false;
  }
  const fields = OVERLAY_FIELDS_BY_TYPE[nodeType(node)];
  if (!fields) {
    return false;
  }
  return fields.some((field) => FIELD_WIDGET_NAMES[field] === name);
}

/**
 * Chain a user-edit callback so an overlay-widget edit re-reads the tier.
 * @param {object} node
 * @param {object|undefined} widget
 * @returns {void}
 */
function bindOverlayWidget(node, widget) {
  if (!widget || widget._ezQualityWatch || !isOverlayWidget(node, widget)) {
    return;
  }
  widget._ezQualityWatch = true;
  const prior = widget.callback;
  /**
   * Chain the prior callback then derive the tier the widgets now hold.
   * @returns {void}
   */
  widget.callback = function () {
    if (typeof prior === "function") {
      prior.apply(this, arguments);
    }
    syncQualityFromGraph(node.graph);
  };
}

/**
 * Bind overlay-widget watchers on one node.
 * @param {object|undefined} node
 * @returns {void}
 */
function bindOverlayWatchersForNode(node) {
  if (!node?.widgets) {
    return;
  }
  for (const widget of node.widgets) {
    bindOverlayWidget(node, widget);
  }
}

/**
 * Bind overlay-widget watchers on every node of a graph.
 * @param {object|undefined} graph
 * @returns {void}
 */
function bindOverlayWatchers(graph) {
  for (const node of graph?.nodes || []) {
    bindOverlayWatchersForNode(node);
  }
}

/**
 * Bind the quality combo once so changes and Queue keep it in step with the
 * widgets.
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
    if (!seedingByGraph.get(node.graph)) {
      persistLastQuality(value);
    }
    applyQuality(value, node);
  };
  /**
   * Before Queue: the combo must say what the prompt holds. Custom re-reads the
   * widgets (they may have been moved back onto a tier by hand); a named tier
   * re-applies, because the App Mode panel can write the combo without firing
   * its callback and leave the widgets authored. Only widget.beforeQueued fires
   * in the pinned frontend, and only synchronously, so this is the last line.
   * @returns {void}
   */
  widget.beforeQueued = function () {
    const graph = node.graph || app.graph;
    const choice = normalizeQuality(widget.value);
    if (choice === EZ_QUALITY_CUSTOM) {
      const derived = deriveQualityTier(graph, graphFamily(graph));
      if (derived === EZ_QUALITY_LAB) {
        syncQualityFromGraph(graph);
        return;
      }
      if (derived !== EZ_QUALITY_CUSTOM) {
        setQualityOnAll(graph, derived);
        applyQuality(derived, node);
        return;
      }
      freezeQualityToCustom(graph);
      return;
    }
    const diverged =
      choice === EZ_QUALITY_LAB ? hasSnapshotEdits(graph) : hasOverlayEdits(graph);
    if (diverged) {
      freezeQualityToCustom(graph);
      return;
    }
    applyQuality(widget.value, node);
  };
}

/**
 * Persist the last named quality for newly opened Apps.
 * @param {*} value
 * @returns {void}
 */
function persistLastQuality(value) {
  const normalized = normalizeQuality(value);
  if (normalized === EZ_QUALITY_CUSTOM) {
    return;
  }
  try {
    localStorage.setItem(LAST_QUALITY_KEY, normalized);
  } catch {
    // private mode / blocked storage
  }
}

/**
 * Last named quality chosen in this browser, or empty.
 * @returns {string}
 */
function readLastQuality() {
  try {
    return String(localStorage.getItem(LAST_QUALITY_KEY) || "");
  } catch {
    return "";
  }
}

/**
 * True when this graph object is a newly opened App (or a different lab_rel).
 * @param {object} graph
 * @returns {boolean}
 */
function isNewlyOpenedGraph(graph) {
  const rel = String(graph?.extra?.lab_rel || graph?.id || "");
  const prev = defaulted.get(graph);
  if (prev === rel) {
    return false;
  }
  defaulted.set(graph, rel);
  snapshots.delete(graph);
  return true;
}

/**
 * Apply last-chosen quality to a newly opened App still at lab, else current.
 * @param {object} graph
 * @param {object} node
 * @param {object|undefined} widget
 * @returns {boolean} true when an overlay ran
 */
function applyDefaultOrCurrent(graph, node, widget) {
  if (!widget) {
    return false;
  }
  const last = readLastQuality();
  const current = normalizeQuality(widget.value);
  if (
    current === EZ_QUALITY_LAB &&
    last &&
    last !== EZ_QUALITY_LAB &&
    last !== EZ_QUALITY_CUSTOM
  ) {
    seedingByGraph.set(graph, true);
    try {
      setWidgetValue(node, widget, last);
    } finally {
      seedingByGraph.set(graph, false);
    }
    return true;
  }
  if (current !== EZ_QUALITY_LAB && current !== EZ_QUALITY_CUSTOM) {
    applyQuality(current, node);
    return true;
  }
  return false;
}

/**
 * Snapshot the graph and bind every Quality combo.
 * @returns {void}
 */
function bindAll() {
  const graph = app.graph;
  if (!graph) {
    return;
  }
  const fresh = isNewlyOpenedGraph(graph);
  if (fresh || !snapshots.has(graph)) {
    snapshotGraph(graph);
  }
  bindOverlayWatchers(graph);
  for (const node of graph.nodes || []) {
    if (isQualityNode(node)) {
      bindQualityNode(node);
    }
  }
  const driver = firstLiveQualityNode(graph);
  if (!driver) {
    return;
  }
  if (fresh) {
    if (!applyDefaultOrCurrent(graph, driver, widgetByName(driver, "quality"))) {
      syncQualityFromGraph(graph);
    }
    return;
  }
  if (!retryPendingApply(graph)) {
    syncQualityFromGraph(graph);
  }
}

app.registerExtension({
  name: "ez_quality.overlay",
  /**
   * Wrap EZQuality so the combo applies overlays on create.
   * @param {object} nodeTypeArg
   * @param {object} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeTypeArg, nodeData) {
    if (nodeData.name !== "EZQuality") {
      return;
    }
    const onNodeCreated = nodeTypeArg.prototype.onNodeCreated;
    /**
     * Bind the quality combo when the node is created.
     * @returns {void}
     */
    nodeTypeArg.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      bindQualityNode(this);
      bindOverlayWatchers(this.graph);
    };
  },
  /**
   * Re-read the tier after a graph load, retrying a tier a lazy widget blocked.
   * @returns {Promise<void>}
   */
  async afterConfigureGraph() {
    bindAll();
  },
  /**
   * Watch overlay widgets when a node is created after graph load.
   * @param {object} node
   * @returns {void}
   */
  nodeCreated(node) {
    bindOverlayWatchersForNode(node);
    syncQualityFromGraph(node?.graph);
  },
  /**
   * Keep the combo honest while the operator edits the graph.
   * @param {object} graph
   * @returns {void}
   */
  graphChanged(graph) {
    syncQualityFromGraph(graph || app.graph);
  },
});

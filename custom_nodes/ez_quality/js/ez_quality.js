/**
 * EZQuality frontend: overlay sampler + UNET/CLIP/VAE on the Detail ladder.
 *
 * Nodes 2.0: writes widget.value plus the matching widgets_values slot, and
 * fires widget.callback. Every step count, CFG, and weight name comes from
 * ez_quality_presets.js, which presets.py generates; this file holds no tier
 * number and no weight filename of its own.
 *
 * The ladder is three rungs: draft, standard, final. standard writes nothing
 * and always succeeds (it means "leave the graph exactly as this App ships
 * it"), so draft and final are write-or-refuse: one write that cannot land
 * cancels the whole apply, keeps the rung already in force on the row, and
 * leaves every reason in the caption. There is no fallback substitution of any
 * kind, and a rung the family cannot honor is refused before a single widget
 * moves, so the row can never name a rung that did nothing.
 *
 * The caption is the only place truth lives. It is derived from the live
 * widgets on every pass - never from the rung name - and prefixed ``Edited: ``
 * when those widgets diverge from what the selected rung wrote. Every App
 * opens on standard: no browser-global carries a rung from one App to the next.
 */
import { app } from "../../scripts/app.js";
import {
  EZ_QUALITY_CHOICES,
  EZ_QUALITY_EDITED_PREFIX,
  EZ_QUALITY_FAMILIES,
  EZ_QUALITY_FIELDS,
  EZ_QUALITY_LABELS,
  EZ_QUALITY_OWNED,
  EZ_QUALITY_TABLE,
  EZ_QUALITY_TIERS,
} from "./ez_quality_presets.js";
// The ladder above is imported by name; the namespace import reaches only
// optional tables (the per-family license words) so a presets build that has
// not grown one yet still links.
import * as EZ_PRESETS from "./ez_quality_presets.js";

/**
 * Value a widget can hold: combo text, a seeded number, a toggle, or the
 * DIVERGENT sentinel the agree-on helpers use when instances of one class
 * contradict each other.
 * @typedef {string|number|boolean|null|undefined|symbol|Object} EzWidgetValue
 */

/**
 * One overlay field on one live node: the widget a write lands on.
 * @typedef {Object} EzOverlayEntry
 * @property {EzNode=} node Node the field belongs to.
 * @property {EzWidget=} widget Widget that carries the field.
 */

/**
 * Overlay fields mapped to their live instances, keyed by field id.
 * @typedef {Object<string, Array<EzOverlayEntry>>} EzOverlayInstances
 */

/**
 * One row of the generated ladder table: field id to the value the rung pins.
 * @typedef {Object<string, EzWidgetValue>} EzRungRow
 */

/**
 * Value per owned field, undefined for a field the read knows nothing about.
 * @typedef {Object<string, EzWidgetValue|undefined>} EzFieldValues
 */

/**
 * The two maps the rung comparison reads for one graph.
 * @typedef {Object} EzOverlayValuePair
 * @property {EzFieldValues=} observed Values the graph holds now.
 * @property {EzFieldValues=} authored Values the graph shipped with.
 */

/**
 * The values one successful apply wrote, kept so the caption can spot a later
 * hand edit and Queue can tell a moved row from a settled one.
 * @typedef {Object} EzAppliedRung
 * @property {string=} rung Rung those writes carry.
 * @property {Map<EzWidget, EzWidgetValue>=} writes Widget to value written.
 */

/**
 * One value the overlay wrote, kept so the caption can spot a later edit.
 * @typedef {Object} EzSnapshotRow
 * @property {EzNode=} node Node the write landed on.
 * @property {string=} name Widget name the write targeted.
 * @property {EzWidgetValue=} value Value the graph shipped with.
 */

/**
 * One write a rung asks for, resolved to its node and widget.
 * @typedef {Object} EzOverlayWrite
 * @property {EzNode=} node Node to write.
 * @property {EzWidget=} widget Widget to write.
 * @property {string=} field Field id the write carries.
 * @property {EzWidgetValue=} value Value the rung pins.
 */

/**
 * A file a rung wants that the loader cannot offer, with the field that owns
 * it, so the caption can name the command that stages it.
 * @typedef {Object} EzBlockedFile
 * @property {string=} field Field id the loader holds.
 * @property {EzWidgetValue=} value Filename the rung wants.
 */

/**
 * Everything one rung apply decides: writes plus what stood in the way.
 * @typedef {Object} EzWritePlan
 * @property {Array<EzOverlayWrite>=} writes Writes the overlay performs.
 * @property {Array<string>=} failures Reasons a write cannot land.
 * @property {Array<string>=} missing Fields with no live instance.
 * @property {Array<EzBlockedFile>=} blockedFiles Files a loader cannot offer.
 * @property {Array<{widget: EzWidget, value: EzWidgetValue}>=} pinned Every
 * widget the rung pins, written or already equal, which is what the caption
 * compares the live values against.
 */

/**
 * Outcome of one rung apply: refuses, or carries the writes to perform.
 * @typedef {Object} EzRungApply
 * @property {boolean=} ok False when the apply is refused outright.
 * @property {Array<string>=} reasons Every reason, in full, for the caption.
 * @property {Array<string>=} commands Host commands that stage what is absent.
 * @property {EzWritePlan=} plan The planned writes.
 */

/**
 * Terms of one truth line, already annotated where they diverge.
 * @typedef {Object} EzCaptionTerms
 * @property {string=} stack Readable name of the stack the loaders hold.
 * @property {string=} steps Steps term, empty for a family with no steps.
 * @property {string=} cfg CFG term, empty for a family with no CFG.
 * @property {Array<string>=} extra Divergences the base line cannot carry.
 * @property {boolean=} edited True when a live widget left what was written.
 */

/**
 * LiteGraph node class handed to beforeRegisterNodeDef; the overlay only
 * touches the prototype, so LiteGraph owns the rest of the shape.
 * @typedef {Object<string, *>} EzNodeType
 */

/**
 * Comfy node definition the registerExtension hook filters by class name.
 * @typedef {Object} EzNodeDef
 * @property {string=} name Node class the hook matches.
 */

// The three rungs, in the order the row lists them. standard is the rung that
// writes nothing and the one every App opens on.
const RUNG_DRAFT = "draft";
const RUNG_STANDARD = "standard";
const RUNG_FINAL = "final";
const RUNGS = [RUNG_DRAFT, RUNG_STANDARD, RUNG_FINAL];
// Row label and caption prefix for the ladder (was Quality).
const DETAIL_LABEL = "Detail";

// Saved graphs, --quality, EZ_QUALITY, and the TUI still send retired ids.
// This mirrors presets._QUALITY_NORMALIZE so the row and the submit path fold
// the same input onto the same rung.
const RUNG_ALIASES = {
  "": RUNG_STANDARD,
  custom: RUNG_STANDARD,
  lab: RUNG_STANDARD,
  standard: RUNG_STANDARD,
  high: RUNG_FINAL,
  ultra: RUNG_FINAL,
  max: RUNG_FINAL,
  free_commercial: RUNG_FINAL,
  "free commercial use (<$10m)": RUNG_FINAL,
  "flux3-quality": RUNG_STANDARD,
  "qwen-image": RUNG_STANDARD,
  "flux3-fast": RUNG_DRAFT,
  "qwen-image-turbo": RUNG_DRAFT,
  "qwen-image-turbo-nvfp4": RUNG_DRAFT,
  "flux3-nvfp4": RUNG_FINAL,
  "qwen-image-nvfp4": RUNG_FINAL,
};

// Family ids that carry no rung at all, so an unknown occupancy is a no-op.
const FAMILY_NOOP = "none";
const FAMILY_LLM = "llm";
const FAMILY_KLEIN3 = "klein3";
// Opt-in Qwen-Image 2.1 stills: own family, so the Klein ladder and the FLUX 3
// profiles cannot drop their weights onto a Qwen graph. Never a default.
const FAMILY_QWEN = "qwen";

// Catalog policy, not rung data: these families are never lawful on this box.
const BANNED = ["minimax", "seedance", "kling", "z_image_turbo"];

// License word per family: the caption states it where the choice is made, so
// a Non-Commercial or Research stack cannot read as an Apache one. Used only
// when the generated table carries no license table of its own.
const LICENSE_WORDS = {
  klein: "Apache-2.0",
  klein3: "FLUX Non-Commercial",
  qwen: "Qwen Research license",
  wan: "Apache-2.0",
  ltx: "Apache-2.0",
  film: "Apache-2.0",
  audio: "Apache-2.0",
  trellis: "Apache-2.0",
};

// Readable stack names for a graph whose loaders hold nothing to read. Same
// policy-not-tier-data rule as the license words: no filename appears here.
const FAMILY_STACK_NAMES = {
  klein: "Klein 4B",
  klein3: "FLUX 3 Klein",
  qwen: "Qwen-Image 2.1",
  wan: "Wan 2.2",
  ltx: "LTX-2.5",
  film: "LTX-2.5 film",
  audio: "Ace Step",
  trellis: "TRELLIS 2",
};

// Host command that stages the weights one family's ladder selects, by rung
// and loader field. Operator command text, not tier data: the filenames
// themselves stay in the generated table, and check.py prints the same
// commands per file under Check models.
const CMD_DOWNLOAD_MODELS = "bazelisk run //:manage -- download-models";
const STAGING_COMMANDS = {
  klein: {
    draft: { unet_name: CMD_DOWNLOAD_MODELS, clip_name: CMD_DOWNLOAD_MODELS, vae_name: CMD_DOWNLOAD_MODELS },
    final: { unet_name: CMD_DOWNLOAD_MODELS, clip_name: CMD_DOWNLOAD_MODELS, vae_name: CMD_DOWNLOAD_MODELS },
  },
  klein3: {
    draft: { unet_name: "bazelisk run //scripts:run-utility -- download-image run --tier flux3", clip_name: "bazelisk run //scripts:run-utility -- download-image run --tier flux3-te", vae_name: CMD_DOWNLOAD_MODELS },
    final: { unet_name: "bazelisk run //scripts:run-utility -- download-image run --tier flux3-nvfp4", clip_name: "bazelisk run //scripts:run-utility -- download-image run --tier flux3-te", vae_name: CMD_DOWNLOAD_MODELS },
  },
  qwen: {
    draft: { unet_name: "bazelisk run //scripts:run-utility -- download-image run --tier qwen-image-turbo", clip_name: "bazelisk run //scripts:run-utility -- download-image run --tier qwen-image-te", vae_name: "bazelisk run //scripts:run-utility -- download-image run --tier qwen-image-vae" },
    final: { unet_name: "bazelisk run //scripts:run-utility -- download-image run --tier qwen-image", clip_name: "bazelisk run //scripts:run-utility -- download-image run --tier qwen-image-te", vae_name: "bazelisk run //scripts:run-utility -- download-image run --tier qwen-image-vae" },
  },
};

// File fields, in the order the caption appends their divergences.
const FILE_FIELDS = ["unet_name", "clip_name", "vae_name", "clip_type"];

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

// Human term each file field carries in a caption divergence.
const FIELD_CAPTION_TERMS = {
  unet_name: "UNET",
  clip_name: "CLIP",
  vae_name: "VAE",
  clip_type: "CLIP type",
};

// Value no field comparison accepts: the targeted instances of one field
// disagree, so the graph holds no single value for it.
const DIVERGENT = Symbol("ez-quality-divergent");

const snapshots = new WeakMap();
const applyingByGraph = new WeakMap();
const syncingByGraph = new WeakMap();
const defaulted = new WeakMap();
const seedingByGraph = new WeakMap();
// graph -> Map(widget -> value the rung in force wrote); the caption compares
// the live widgets against exactly this record.
const overlayWrites = new WeakMap();
// graph -> EzAppliedRung; the last apply that landed whole.
const appliedRungs = new WeakMap();
// graph -> true once the operator moves the row past the last successful write.
const rowMoved = new WeakMap();
// graph -> {rung, fields, attempts}; a rung a missing widget blocked, retried once.
const pendingApplies = new WeakMap();

/**
 * Find a widget by name on a node.
 * @param {EzNode} node
 * @param {string} name
 * @returns {EzWidget|undefined}
 */
function widgetByName(node, name) {
  return node.widgets?.find((w) => w.name === name);
}

/**
 * Node type, honoring the Nodes 2.0 comfyClass alias.
 * @param {EzNode|undefined} node
 * @returns {string}
 */
function nodeType(node) {
  return String(node?.comfyClass || node?.type || "");
}

/**
 * True for the Detail combo node.
 * @param {EzNode|undefined} node
 * @returns {boolean}
 */
function isQualityNode(node) {
  return nodeType(node) === "EZQuality";
}

/**
 * True when a node is mode 0. Muted and bypassed lanes are not in the queued
 * prompt, so they neither drive the overlay nor wear its caption.
 * @param {EzNode|undefined} node
 * @returns {boolean}
 */
function isLiveNode(node) {
  return !node || node.mode == null || node.mode === 0;
}

/**
 * First Detail combo the overlay should act on, ignoring muted copies.
 * @param {EzGraph|undefined} graph
 * @returns {EzNode|null}
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
 * @param {EzWidget|undefined} widget
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
 * Fold separators so the Qwen-Image needles match either filename style.
 * @param {string} name
 * @returns {string}
 */
function qwenBlob(name) {
  return String(name || "").toLowerCase().replaceAll(".", "-").replaceAll("_", "-");
}

/**
 * True when a UNET filename is an opt-in Qwen-Image 2.1 weight (INT8/NVFP4,
 * both twins). Qwen research-licensed, so no rung here is ever a default.
 * @param {string} name
 * @returns {boolean}
 */
function isQwenImageUnet(name) {
  const blob = qwenBlob(name);
  const quantized = blob.includes("convrot") || blob.includes("nvfp4");
  return blob.includes("qwen-image-2-1") && quantized;
}

/**
 * True when a CLIP filename is a Qwen-Image 2.1 Qwen3VL-8B text encoder.
 * @param {string} name
 * @returns {boolean}
 */
function isQwenImageClip(name) {
  return qwenBlob(name).includes("qwen3vl-8b");
}

/**
 * True when a VAE filename is the Qwen-Image 2.1 VAE.
 * @param {string} name
 * @returns {boolean}
 */
function isQwenImageVae(name) {
  return qwenBlob(name).includes("qwen-image-2-1-vae");
}

/**
 * True when a UNET filename looks like Wan 14B.
 * @param {EzWidgetValue} name
 * @returns {boolean}
 */
function isWan14(name) {
  return String(name || "")
    .toLowerCase()
    .includes("14b");
}

/**
 * True when any live UNETLoader holds Wan 14B, which the overlay never touches.
 * @param {EzGraph|undefined} graph
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
 * swap guard presets.apply_to_graph applies server-side. It is also what keeps
 * a rung from writing over a weight its family does not own.
 * @param {string} field
 * @param {EzWidgetValue} current
 * @returns {boolean}
 */
function isSwappableTarget(field, current) {
  const name = String(current || "");
  if (!name) {
    return true;
  }
  if (field === "unet_name") {
    return (
      isKlein4b(name) ||
      isKlein9b(name) ||
      isFlux2Dev(name) ||
      isKlein3Unet(name) ||
      isQwenImageUnet(name)
    );
  }
  if (field === "clip_name") {
    return isFlux2Clip(name) || isKlein3Clip(name) || isQwenImageClip(name);
  }
  if (field === "vae_name") {
    return isFlux2Vae(name) || isQwenImageVae(name);
  }
  return true;
}

/**
 * True when any live loader pins FLUX 3 Image Klein weights.
 * @param {EzGraph|undefined} graph
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
 * Widget as the family pins read it. LiteGraph owns the whole shape at runtime,
 * so the pin only claims the value it compares.
 * @typedef {Object<string, *>} EzWidget
 */

/**
 * Node as the family pins read it: class, type, and loader widgets.
 * @typedef {Object<string, *>} EzNode
 * @property {Array<EzWidget>=} widgets Widgets LiteGraph carries on the node.
 */

/**
 * Graph as the family pins read it, muted lanes included.
 * @typedef {Object<string, *>} EzGraph
 * @property {Array<EzNode>=} nodes Nodes on the graph.
 */

/**
 * True when any live loader pins opt-in Qwen-Image 2.1 weights.
 * @param {EzGraph|undefined} graph
 * @returns {boolean}
 */
function graphHasQwenWeights(graph) {
  for (const node of graph?.nodes || []) {
    if (!isLiveNode(node)) {
      continue;
    }
    const ntype = nodeType(node);
    const unetWidget = /** @type {EzWidget|undefined} */ (
      widgetByName(node, "unet_name")
    );
    if (ntype === "UNETLoader" && isQwenImageUnet(unetWidget?.value)) {
      return true;
    }
    const clipWidget = /** @type {EzWidget|undefined} */ (
      widgetByName(node, "clip_name")
    );
    if (ntype === "CLIPLoader" && isQwenImageClip(clipWidget?.value)) {
      return true;
    }
  }
  return false;
}

/**
 * Fold any accepted input onto one of the three rungs. Retired ids land on the
 * rung the contract maps them to; anything unknown, including a frozen custom
 * or lab left by an old graph, lands on the rung that writes nothing.
 * @param {EzWidgetValue} value
 * @returns {string}
 */
function normalizeRung(value) {
  const folded = String(value || "").trim().toLowerCase();
  if (RUNGS.includes(folded)) {
    return folded;
  }
  if (Object.prototype.hasOwnProperty.call(RUNG_ALIASES, folded)) {
    return RUNG_ALIASES[folded];
  }
  const known = (Array.isArray(EZ_QUALITY_CHOICES) ? EZ_QUALITY_CHOICES : []).find(
    (item) => String(item).toLowerCase() === folded,
  );
  return known && RUNGS.includes(String(known).toLowerCase())
    ? String(known).toLowerCase()
    : RUNG_STANDARD;
}

/**
 * Rung name as the caption writes it: capitalized, so a note reads
 * "(Final sets 24)" rather than "(final sets 24)".
 * @param {string} rung
 * @returns {string}
 */
function rungLabel(rung) {
  const text = String(rung || "");
  return text ? `${text.charAt(0).toUpperCase()}${text.slice(1)}` : "";
}

/**
 * Infer graph occupancy from extra.lab_app_mode or node types.
 * @param {EzGraph|undefined} graph
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
 * Rung family the graph belongs to: its occupancy, Klein 3 or opt-in Qwen when
 * its weights say so, and a no-op family for anything this table does not
 * cover.
 * @param {EzGraph|undefined} graph
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
  if (!noOverlay && graphHasQwenWeights(graph)) {
    return FAMILY_QWEN;
  }
  return occ;
}

/**
 * Fields one family's rungs ever set; an edit outside this list cannot make a
 * rung claim a widget it never owns.
 * @param {string} family
 * @returns {string[]}
 */
function ownedFields(family) {
  const owned = EZ_QUALITY_OWNED[family];
  return Array.isArray(owned) ? owned : [];
}

/**
 * The three-rung ladder one family offers, in table order.
 *
 * A family whose rungs own no writable field gets no ladder at all: the lab
 * wiring strips its node and row (tests/python/_wire_quality.py), and a combo
 * left behind here must not offer a rung that queues unchanged.
 * @param {string} family
 * @returns {string[]}
 */
function rungsForFamily(family) {
  const honored = (Array.isArray(EZ_QUALITY_TIERS[family]) ? EZ_QUALITY_TIERS[family] : []).map(
    String,
  );
  if (!honored.length && !ownedFields(family).length) {
    return [];
  }
  const listed = (Array.isArray(EZ_QUALITY_CHOICES) ? EZ_QUALITY_CHOICES : [])
    .map(String)
    .filter((choice) => RUNGS.includes(choice.toLowerCase()));
  return listed.length === RUNGS.length ? listed : RUNGS.slice();
}

/**
 * Requested value per overlay field for one rung, or null for an unknown row.
 * @param {string} family
 * @param {string} rung
 * @returns {EzRungRow|null}
 */
function tierRow(family, rung) {
  return EZ_QUALITY_TABLE[family]?.[rung] || null;
}

/**
 * True when one family can actually carry one rung.
 *
 * standard is honored on every ladder family because writing nothing is what
 * it means. Any other rung must have at least one field the family writes: a
 * rung whose row is all-null for this family would stamp its name on the row
 * while changing no widget, which is the failure this guard closes.
 * @param {string} family
 * @param {string} rung
 * @returns {boolean}
 */
function rungIsHonored(family, rung) {
  if (!rungsForFamily(family).map((item) => item.toLowerCase()).includes(rung)) {
    return false;
  }
  if (rung === RUNG_STANDARD) {
    return true;
  }
  const row = tierRow(family, rung);
  const owned = ownedFields(family);
  return !!row && owned.some((field) => row[field] != null);
}

/**
 * Caption naming the swap a rung performs, for the row tooltip only. The truth
 * line is derived from the live widgets, never from this text.
 * @param {string} family
 * @param {string} rung
 * @returns {string}
 */
function tierLabelFor(family, rung) {
  return String(EZ_QUALITY_LABELS[family]?.[rung] || "");
}

/**
 * License word for one family, from the generated table when it carries one.
 * @param {string} family
 * @returns {string}
 */
function licenseWord(family) {
  for (const key of ["EZ_QUALITY_LICENSE_LABELS", "EZ_QUALITY_LICENSES", "EZ_QUALITY_LICENSE"]) {
    const table = EZ_PRESETS[key];
    const word = table && table[family];
    if (typeof word === "string" && word) {
      return word;
    }
  }
  return String(LICENSE_WORDS[family] || "");
}

/**
 * Host command that stages the file one rung's loader field wants.
 * @param {string} family
 * @param {string} rung
 * @param {string} field
 * @returns {string}
 */
function stagingCommand(family, rung, field) {
  if (!FILE_FIELDS.includes(field)) {
    return "";
  }
  const byField = STAGING_COMMANDS[family]?.[rung];
  return String((byField && byField[field]) || "");
}

/**
 * Basename without its extension, for a caption that names a weight without
 * quoting the whole filename.
 * @param {EzWidgetValue} value
 * @returns {string}
 */
function fileStem(value) {
  const text = String(value == null ? "" : value).split("/").pop() || "";
  const cut = text.lastIndexOf(".");
  return cut > 0 ? text.slice(0, cut) : text;
}

/**
 * Readable name for the stack the loaders actually hold, read off the live
 * UNET filename and falling back to the family when the graph has none.
 * @param {string} family
 * @param {EzWidgetValue} unetName
 * @returns {string}
 */
function stackLabel(family, unetName) {
  const raw = String(unetName == null ? "" : unetName).trim();
  if (!raw) {
    return String(FAMILY_STACK_NAMES[family] || family || "");
  }
  const stem = fileStem(raw);
  const blob = klein3Blob(stem);
  const base = blob.includes("base") ? " base" : "";
  const quant = blob.includes("nvfp4")
    ? " NVFP4"
    : blob.includes("int8") || blob.includes("convrot")
      ? " INT8"
      : "";
  if (isKlein3Unet(stem)) {
    return `FLUX 3 Klein${base}${quant}`;
  }
  if (isQwenImageUnet(stem)) {
    return `Qwen-Image 2.1${blob.includes("turbo") ? " turbo" : ""}${quant}`;
  }
  if (isKlein9b(stem)) {
    return `Klein 9B${base}${quant}`;
  }
  if (isKlein4b(stem)) {
    return `Klein 4B${base}${quant}`;
  }
  if (isFlux2Dev(stem)) {
    return "FLUX.2-dev";
  }
  if (blob.includes("wan")) {
    return `Wan${base}${quant}`;
  }
  if (blob.includes("ltx")) {
    return `LTX-2.5${quant}`;
  }
  if (blob.includes("trellis")) {
    return "TRELLIS 2";
  }
  if (blob.includes("ace")) {
    return "Ace Step";
  }
  return stem;
}

/**
 * String form of a widget value for edit detection (numbers compare as text).
 * @param {EzWidgetValue} value
 * @returns {string}
 */
function widgetValueText(value) {
  return String(value == null ? "" : value);
}

/**
 * True when two widget values are the same text.
 * @param {EzWidgetValue} a
 * @param {EzWidgetValue} b
 * @returns {boolean}
 */
function sameWidgetValue(a, b) {
  return widgetValueText(a) === widgetValueText(b);
}

/**
 * Compare an observed widget value with a rung value the way presets.match_tier
 * does: numbers numerically, everything else as text, null equal only to null.
 * @param {EzWidgetValue} left
 * @param {EzWidgetValue} right
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
 * True when one TRELLIS KSampler is the unguided texture pass.
 *
 * A TRELLIS graph runs three guided stages at CFG 7.5 plus one texture stage
 * at CFG 1.0. The step ladder is tuned against the guided stages and the
 * texture stage's step count belongs to its own recipe, so the overlay leaves
 * that sampler alone. Mirrors presets.is_trellis_guidance_free_stage.
 * @param {EzNode} node
 * @param {string} family
 * @returns {boolean}
 */
function isTrellisGuidanceFreeStage(node, family) {
  if (family !== "trellis" || nodeType(node) !== "KSampler") {
    return false;
  }
  const cfg = /** @type {EzWidget} */ (widgetByName(node, "cfg"));
  const values = Array.isArray(node.widgets_values) ? node.widgets_values : [];
  const held = cfg ? cfg.value : values[3];
  return held !== undefined && Number(held) === 1;
}

/**
 * Live widget per targeted instance of each overlay field, muted nodes skipped.
 * @param {EzGraph|undefined} graph
 * @param {string} [family] When given, the family whose overlay is being read.
 * @returns {EzOverlayInstances} field -> entries per live instance
 */
function collectOverlayInstances(graph, family) {
  const out = {};
  for (const field of EZ_QUALITY_FIELDS) {
    out[field] = [];
  }
  for (const node of graph?.nodes || []) {
    if (!isLiveNode(node)) {
      continue;
    }
    if (family && isTrellisGuidanceFreeStage(node, family)) {
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
 * @param {Array<EzOverlayEntry>} entries
 * @param {function} read reads one entry; undefined when it knows nothing
 * @returns {EzWidgetValue} the shared value, null when the graph holds none,
 * DIVERGENT when the instances of the class hold different values
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
 * observed / authored pair per owned field, the two maps the rung comparison
 * reads. A field its instances disagree on matches nothing, so a graph whose
 * samplers contradict each other belongs to no rung.
 * @param {EzGraph} graph
 * @param {string} family
 * @param {EzOverlayInstances} instances
 * @returns {EzOverlayValuePair} observed and authored maps
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
 * The rung the live widgets actually hold: the rung whose row every owned field
 * matches. Empty when no rung describes the graph, which is the honest answer
 * for a hand-edited one; the row keeps what the operator picked and the caption
 * says Edited.
 * @param {EzGraph|undefined} graph
 * @param {string} family
 * @returns {string} rung id, or "" when none matches
 */
function deriveQualityTier(graph, family) {
  if (!graph) {
    return "";
  }
  const owned = ownedFields(family);
  if (!owned.length) {
    return "";
  }
  const instances = collectOverlayInstances(graph, family);
  const seen = overlayValues(graph, family, instances);
  for (const rung of rungsForFamily(family)) {
    // standard writes nothing, so it can never be read back off the widgets.
    if (rung === RUNG_STANDARD) {
      continue;
    }
    const row = tierRow(family, rung);
    if (row && owned.every((field) => sameTierValue(seen.observed[field], row[field]))) {
      return rung;
    }
  }
  return "";
}

/**
 * Value the rung in force last wrote on one widget, or undefined when it wrote
 * nothing there.
 * @param {EzGraph|undefined} graph
 * @param {string} rung
 * @param {EzWidget|undefined} widget
 * @returns {EzWidgetValue|undefined}
 */
function writtenValueOf(graph, rung, widget) {
  const applied = graph && appliedRungs.get(graph);
  if (!applied || applied.rung !== rung || !widget || !(applied.writes instanceof Map)) {
    return undefined;
  }
  return applied.writes.get(widget);
}

/**
 * Why one write cannot land, or empty when it can. An empty answer means the
 * queued prompt will really hold the rung value.
 * @param {string} field
 * @param {EzOverlayEntry} entry
 * @param {EzWidgetValue} wanted
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
 * Decide every write one rung asks for, and record what cannot land.
 * @param {EzGraph} graph
 * @param {string} family
 * @param {string} rung
 * @returns {EzWritePlan} writes, failures, missing fields, blocked files
 */
function planTierWrites(graph, family, rung) {
  const row = tierRow(family, rung);
  const instances = collectOverlayInstances(graph, family);
  const refused = graphHasWan14(graph);
  const writes = [];
  const failures = [];
  const missing = [];
  const blockedFiles = [];
  const pinned = [];
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
      // A field the rung pins counts as rung-authored even when the widget
      // already held the value, so the caption compares against the rung.
      pinned.push({ widget: entry.widget, value: wanted });
      if (sameTierValue(entry.widget.value, wanted)) {
        continue;
      }
      const reason = writeBlockReason(field, entry, wanted, refused);
      if (reason) {
        if (!failures.includes(reason)) {
          failures.push(reason);
        }
        if (reason.endsWith("not installed")) {
          blockedFiles.push({ field, value: wanted });
        }
        continue;
      }
      writes.push({ node: entry.node, widget: entry.widget, field, value: wanted });
    }
  }
  return { writes, failures, missing, blockedFiles, pinned };
}

/**
 * Plan one rung apply: the writes it performs, or every reason it is refused.
 * @param {EzGraph} graph
 * @param {string} family
 * @param {string} rung
 * @returns {EzRungApply}
 */
function planRungApply(graph, family, rung) {
  if (rung === RUNG_STANDARD) {
    return { ok: true, reasons: [], commands: [], plan: { writes: [] } };
  }
  if (!rungIsHonored(family, rung)) {
    return {
      ok: false,
      reasons: [`${rungLabel(rung)} writes nothing on a ${family} graph`],
      commands: [],
      plan: { writes: [] },
    };
  }
  const plan = planTierWrites(graph, family, rung);
  const reasons = plan.failures.slice();
  for (const field of plan.missing) {
    reasons.push(`${FIELD_WIDGET_NAMES[field]} widget not on graph`);
  }
  const commands = [];
  for (const blocked of plan.blockedFiles) {
    const cmd = stagingCommand(family, rung, blocked.field);
    if (cmd && !commands.includes(cmd)) {
      commands.push(cmd);
    }
  }
  return {
    ok: !reasons.length,
    reasons,
    commands,
    plan,
  };
}

/**
 * True when LiteGraph serializes this widget into widgets_values.
 * @param {EzWidget|undefined} widget
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
 * @param {EzNode|undefined} node
 * @param {EzWidget|undefined} widget
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
 * @param {EzNode|undefined} node
 * @param {EzWidget|undefined} widget
 * @param {EzWidgetValue} value
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
 * @param {EzGraph|undefined} graph
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
 * @param {EzNode|undefined} node
 * @param {EzWidget|undefined} widget
 * @param {EzWidgetValue} value
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
 * Remember the value the overlay wrote so the caption can spot a later edit.
 * @param {EzGraph|undefined} graph
 * @param {EzWidget|undefined} widget
 * @param {EzWidgetValue} value
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
 * Forget overlay-write records for widgets being (re)written.
 * @param {EzGraph|undefined} graph
 * @param {Array<EzWidget>} widgets
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
 * @param {EzGraph|undefined} graph
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
 * @param {EzGraph|undefined} graph
 * @param {EzNode} node
 * @param {EzWidget} widget
 * @param {EzWidgetValue} value
 * @returns {void}
 */
function applyOverlayWrite(graph, node, widget, value) {
  setWidgetValue(node, widget, value);
  recordOverlayWrite(graph, widget, value);
}

/**
 * Authored value for one widget of one node, or undefined when unrecorded.
 * @param {Array<EzSnapshotRow>|undefined} snap
 * @param {EzNode} node
 * @param {string} name
 * @returns {EzWidgetValue|undefined}
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
 * True when a widget now holds a value the user typed over what the graph
 * shipped with. App Mode panel writes can skip the widget callback, so the
 * caption compares the live values as well as the overlay's own records. A
 * value the rung in force wrote itself is not a hand edit.
 * @param {EzGraph|undefined} graph
 * @returns {boolean}
 */
function hasSnapshotEdits(graph) {
  const snap = graph && snapshots.get(graph);
  if (!snap || !snap.length) {
    return false;
  }
  const applied = graph && appliedRungs.get(graph);
  for (const row of snap) {
    const widget = widgetByName(row.node, row.name);
    if (!widget) {
      continue;
    }
    if (applied && applied.writes instanceof Map && applied.writes.has(widget)) {
      continue;
    }
    if (!sameWidgetValue(widget.value, row.value)) {
      return true;
    }
  }
  return false;
}

/**
 * Expected value per owned field: what the selected rung wrote where it wrote,
 * otherwise what the graph shipped with. Undefined means no baseline exists, so
 * the field cannot be called edited.
 * @param {EzGraph} graph
 * @param {string} family
 * @param {string} rung
 * @param {EzOverlayInstances} instances
 * @returns {EzFieldValues} field -> expected value
 */
function expectedValues(graph, family, rung, instances) {
  const snap = snapshots.get(graph);
  const out = {};
  for (const field of ownedFields(family)) {
    const name = FIELD_WIDGET_NAMES[field];
    const entries = instances[field] || [];
    const written = agreeOn(
      entries.filter((entry) => writtenValueOf(graph, rung, entry.widget) !== undefined),
      (entry) => writtenValueOf(graph, rung, entry.widget),
    );
    if (written !== null) {
      out[field] = written;
      continue;
    }
    out[field] = snap
      ? agreeOn(entries, (entry) => snapshotValueOf(snap, entry.node, name))
      : undefined;
  }
  return out;
}

/**
 * Build the truth line's terms from the live widgets, annotating every term
 * whose widget left what the selected rung wrote.
 * @param {EzGraph} graph
 * @param {string} family
 * @param {string} rung
 * @returns {EzCaptionTerms}
 */
function rungTerms(graph, family, rung) {
  const owned = ownedFields(family);
  const instances = collectOverlayInstances(graph, family);
  const observed = overlayValues(graph, family, instances).observed;
  const expected = expectedValues(graph, family, rung, instances);
  const who = rungLabel(rung);
  let edited = false;

  /**
   * True when the instances of one class contradict each other, so the graph
   * holds no single value to print.
   * @param {EzWidgetValue} value
   * @returns {boolean}
   */
  const mixed = (value) => value === DIVERGENT;
  /**
   * Printable form of a live value that may be the DIVERGENT sentinel.
   * @param {EzWidgetValue} value
   * @returns {string}
   */
  const text = (value) => (mixed(value) ? "mixed" : widgetValueText(value));
  /**
   * Printable stem of a live filename that may be the DIVERGENT sentinel.
   * @param {EzWidgetValue} value
   * @returns {string}
   */
  const stem = (value) => (mixed(value) ? "mixed" : fileStem(value));

  /**
   * Annotate one term with what the rung wanted where the live value differs.
   * @param {string} field
   * @param {string} term
   * @param {function} render renders the wanted value for the note
   * @returns {string}
   */
  const note = (field, term, render) => {
    if (expected[field] === undefined || sameTierValue(observed[field], expected[field])) {
      return term;
    }
    edited = true;
    // standard writes nothing, so its baseline is what the App ships, not
    // something the rung set.
    const says = rung === RUNG_STANDARD ? `App ships ${render(expected[field])}` : `${who} sets ${render(expected[field])}`;
    return `${term} (${says})`;
  };

  const stackTerm = mixed(observed.unet_name) ? "mixed UNET" : stackLabel(family, observed.unet_name);
  const stack = note("unet_name", stackTerm, fileStem);
  const steps =
    owned.includes("steps") && observed.steps != null
      ? note("steps", mixed(observed.steps) ? "mixed steps" : `${text(observed.steps)} steps`, widgetValueText)
      : "";
  const cfg =
    owned.includes("cfg") && observed.cfg != null
      ? note("cfg", mixed(observed.cfg) ? "CFG mixed" : `CFG ${text(observed.cfg)}`, widgetValueText)
      : "";
  const extra = [];
  for (const field of FILE_FIELDS) {
    if (field === "unet_name" || !owned.includes(field)) {
      continue;
    }
    // No baseline for the field means nothing was ever written there, so it
    // cannot be called a divergence; a field that still holds its value is not
    // one either.
    if (expected[field] === undefined || sameTierValue(observed[field], expected[field])) {
      continue;
    }
    extra.push(note(field, `${FIELD_CAPTION_TERMS[field] || field} ${stem(observed[field])}`, fileStem));
  }
  return { stack, steps, cfg, extra, edited };
}

/**
 * The one-line caption: the truth line read off the live widgets, prefixed
 * Edited: where they left what the rung wrote, and followed by the full reason
 * list plus the command that stages what is absent when an apply was refused.
 * @param {EzGraph} graph
 * @param {string} family
 * @param {string} rung
 * @param {EzRungApply=} refusal refused apply whose reasons and commands to print
 * @returns {string}
 */
function deriveQualityCaption(graph, family, rung, refusal) {
  const terms = rungTerms(graph, family, rung);
  const bits = [terms.stack, terms.steps, terms.cfg];
  for (const term of terms.extra) {
    bits.push(term);
  }
  const license = licenseWord(family);
  if (license) {
    bits.push(license);
  }
  let text = bits.filter(Boolean).join(" - ");
  if (terms.edited) {
    text = `${EZ_QUALITY_EDITED_PREFIX}${text}`;
  }
  const reasons = (refusal && refusal.reasons) || [];
  if (reasons.length) {
    text += ` - ${reasons.join("; ")}`;
  }
  const commands = (refusal && refusal.commands) || [];
  if (commands.length) {
    text += ` - Run: ${commands.join(" && ")}`;
  }
  return text;
}

/**
 * Rung currently in force: the last apply that landed whole, else the rung
 * every App opens on.
 * @param {EzGraph|undefined} graph
 * @returns {string}
 */
function rungInForce(graph) {
  const applied = graph && appliedRungs.get(graph);
  const rung = String((applied && applied.rung) || RUNG_STANDARD);
  return RUNGS.includes(rung) ? rung : RUNG_STANDARD;
}

/**
 * Stamp a live Detail caption onto the graph extra and every visible combo.
 * With no visible Detail combo there is nothing to caption, so a muted lane
 * cannot leave a stamp on the graph either.
 * @param {EzGraph|undefined} graph
 * @param {string} caption
 * @param {string} [tooltip] what the selected rung would do, for the hover text
 * @returns {void}
 */
function stampQualityCaption(graph, caption, tooltip) {
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
      widget.label = caption ? `${DETAIL_LABEL} - ${caption}` : DETAIL_LABEL;
      if (tooltip) {
        widget.title = tooltip;
      }
    }
  }
}

/**
 * Put one value on every Detail combo, so a second combo cannot keep showing a
 * rung another one refused. The combo callback stays quiet; the caller decides
 * whether to apply, so setting the value cannot re-enter the overlay.
 * @param {EzGraph|undefined} graph
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
 * Narrow every Detail combo in the graph to the ladder this family can honor.
 *
 * The combo is built once from the global rung list, so without this a Klein
 * rung sits in the dropdown of a Wan graph and reading it across writes
 * nothing. A combo left holding a retired id is folded onto the rung in force.
 * @param {EzGraph|undefined} graph
 * @param {string} family
 * @returns {void}
 */
function scopeComboToFamily(graph, family) {
  if (!graph) {
    return;
  }
  const allowed = rungsForFamily(family);
  const settled = rungInForce(graph);
  for (const node of graph.nodes || []) {
    if (!isQualityNode(node)) {
      continue;
    }
    const widget = /** @type {EzWidget} */ (widgetByName(node, "quality"));
    if (!widget?.options) {
      continue;
    }
    const current = comboValues(widget);
    if (
      !(current.length === allowed.length && current.every((value, index) => value === allowed[index]))
    ) {
      widget.options.values = [...allowed];
    }
    if (allowed.length && !allowed.map((value) => value.toLowerCase()).includes(normalizeRung(widget.value))) {
      writeWidgetSlot(node, widget, settled);
    }
  }
}

/**
 * Perform the writes one apply planned and record them as that rung's.
 * @param {EzGraph} graph
 * @param {string} family
 * @param {string} rung
 * @param {EzRungApply} apply
 * @returns {void}
 */
function performApply(graph, family, rung, apply) {
  const writes = (apply.plan && apply.plan.writes) || [];
  // A fresh record: a widget this rung does not write is not its business, so
  // it must not carry an edit record from the rung that was in force before.
  clearOverlayWrites(
    graph,
    Array.from((overlayWrites.get(graph) || new Map()).keys()),
  );
  const wrote = new Map();
  for (const write of writes) {
    applyOverlayWrite(graph, write.node, write.widget, write.value);
    wrote.set(write.widget, write.value);
  }
  // A pinned field the widget already held needs no write but still belongs to
  // this rung, so the caption measures it against the rung, not the author.
  for (const entry of (apply.plan && apply.plan.pinned) || []) {
    if (entry && entry.widget) {
      wrote.set(entry.widget, entry.value);
      recordOverlayWrite(graph, entry.widget, entry.value);
    }
  }
  appliedRungs.set(graph, { rung, writes: wrote });
  rowMoved.set(graph, false);
  clearPendingApply(graph);
  setQualityOnAll(graph, rung);
  stampQualityCaption(
    graph,
    deriveQualityCaption(graph, family, rung),
    tierLabelFor(family, rung),
  );
}

/**
 * Refuse an apply: change no widget, keep the rung already in force on every
 * combo, and put the whole reason list in the caption.
 * @param {EzGraph} graph
 * @param {string} family
 * @param {EzRungApply} apply
 * @returns {string} the caption the refusal left behind
 */
function refuseApply(graph, family, apply) {
  const settled = rungInForce(graph);
  setQualityOnAll(graph, settled);
  const caption = deriveQualityCaption(graph, family, settled, apply);
  stampQualityCaption(graph, caption, tierLabelFor(family, settled));
  return caption;
}

/**
 * Apply a rung across sampler/loader widgets, write-or-refuse.
 *
 * standard writes nothing and always succeeds. draft and final attempt every
 * write their table row asks for; if any single write cannot land (widget not
 * on the graph, weight not installed, a loader holding a weight the overlay may
 * not replace, a Wan 14B graph, no prompt slot) the apply is refused whole:
 * nothing is renamed and the row keeps the rung already in force. A rung the
 * family cannot honor is refused the same way before a widget moves, so the
 * row can never name a rung that performed no write.
 * @param {string} choice
 * @param {EzNode|undefined} qualityNode
 * @returns {void}
 */
function applyQuality(choice, qualityNode) {
  const graph = qualityNode?.graph || app.graph;
  if (!graph || applyingByGraph.get(graph)) {
    return;
  }
  if (qualityNode && !isLiveNode(qualityNode)) {
    // A muted Detail lane is not in the queued prompt; it drives nothing.
    return;
  }
  applyingByGraph.set(graph, true);
  try {
    const family = graphFamily(graph);
    const rung = normalizeRung(choice);
    const apply = planRungApply(graph, family, rung);
    if (!apply.ok) {
      const missing = (apply.plan && apply.plan.missing) || [];
      if (missing.length) {
        recordPendingApply(graph, rung, missing);
      }
      refuseApply(graph, family, apply);
      return;
    }
    const pending = pendingApplies.get(graph);
    if (!(pending && pending.rung === rung)) {
      clearPendingApply(graph);
    }
    performApply(graph, family, rung, apply);
  } finally {
    applyingByGraph.set(graph, false);
  }
}

/**
 * Read the rung back off the live widgets and caption it on every combo.
 *
 * The row is the operator's selection, so this never moves it: a graph whose
 * widgets drifted says so in the caption instead of silently renaming the row.
 * @param {EzGraph|undefined} graph
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
    scopeComboToFamily(graph, family);
    if (!rungsForFamily(family).length) {
      // No ladder family, no truth to state: the lab wiring strips this row.
      stampQualityCaption(graph, "");
      return;
    }
    const rung = rungInForce(graph);
    stampQualityCaption(graph, deriveQualityCaption(graph, family, rung), tierLabelFor(family, rung));
  } finally {
    syncingByGraph.set(graph, false);
  }
}

/**
 * Remember a rung that missed a widget so the next graph configure retries once.
 * @param {EzGraph|undefined} graph
 * @param {string} choice
 * @param {string[]} fields
 * @returns {void}
 */
function recordPendingApply(graph, choice, fields) {
  if (!graph) {
    return;
  }
  const prior = pendingApplies.get(graph);
  const attempts = prior && prior.rung === choice ? prior.attempts : 0;
  pendingApplies.set(graph, { rung: choice, fields: fields.slice(), attempts });
}

/**
 * Drop the retry record once a rung has fully landed.
 * @param {EzGraph|undefined} graph
 * @returns {void}
 */
function clearPendingApply(graph) {
  if (graph) {
    pendingApplies.delete(graph);
  }
}

/**
 * Retry once a rung that was blocked by a widget that did not exist yet.
 * @param {EzGraph|undefined} graph
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
  applyQuality(pending.rung, node);
  return true;
}

/**
 * True when this widget is a Detail overlay field on this node.
 * @param {EzNode} node
 * @param {EzWidget|undefined} widget
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
 * Chain a user-edit callback so an overlay-widget edit re-derives the caption.
 * The row keeps the operator's rung; only the truth line moves.
 * @param {EzNode} node
 * @param {EzWidget|undefined} widget
 * @returns {void}
 */
function bindOverlayWidget(node, widget) {
  if (!widget || widget._ezQualityWatch || !isOverlayWidget(node, widget)) {
    return;
  }
  widget._ezQualityWatch = true;
  const prior = widget.callback;
  /**
   * Chain the prior callback then re-read the live widgets for the caption.
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
 * @param {EzNode|undefined} node
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
 * @param {EzGraph|undefined} graph
 * @returns {void}
 */
function bindOverlayWatchers(graph) {
  for (const node of graph?.nodes || []) {
    bindOverlayWatchersForNode(node);
  }
}

/**
 * Bind the Detail combo once so changes and Queue keep the caption honest.
 * @param {EzNode} node
 * @returns {void}
 */
function bindQualityNode(node) {
  const widget = widgetByName(node, "quality");
  if (!widget || widget._ezQualityBound) {
    return;
  }
  widget._ezQualityBound = true;
  widget.label = DETAIL_LABEL;
  const prior = widget.callback;
  /**
   * Chain the prior callback then overlay the chosen rung. A seed write is not
   * an operator pick, so it must not mark the row moved or run an apply.
   * @param {EzWidgetValue} value
   * @returns {void}
   */
  widget.callback = function (value) {
    if (typeof prior === "function") {
      prior.apply(this, arguments);
    }
    if (seedingByGraph.get(node.graph)) {
      return;
    }
    rowMoved.set(node.graph, true);
    applyQuality(value, node);
  };
  /**
   * Before Queue: the prompt must hold the rung the row names. The rung is
   * re-applied only after the operator moved the row, a hand edit is never
   * overwritten, and a re-apply that would be refused stops Queue with the
   * caption text. Only widget.beforeQueued fires in the pinned frontend, and
   * only synchronously, so this is the last line.
   * @returns {void}
   */
  widget.beforeQueued = function () {
    const graph = node.graph || app.graph;
    if (!graph) {
      return;
    }
    const family = graphFamily(graph);
    const rung = normalizeRung(widget.value);
    const moved = rowMoved.get(graph) || rungInForce(graph) !== rung;
    if (!moved) {
      // Nothing moved since the last write that landed: send what is on the box.
      syncQualityFromGraph(graph);
      return;
    }
    if (
      deriveQualityTier(graph, graphFamily(graph)) === rung &&
      !hasOverlayEdits(graph) &&
      !hasSnapshotEdits(graph)
    ) {
      rowMoved.set(graph, false);
      syncQualityFromGraph(graph);
      return;
    }
    const apply = planRungApply(graph, family, rung);
    if (!apply.ok) {
      const caption = refuseApply(graph, family, apply);
      throw new Error(`Detail ${rungLabel(rung)} cannot be applied: ${caption}`);
    }
    applyQuality(widget.value, node);
  };
}

/**
 * True when this graph object is a newly opened App (or a different lab_rel).
 * @param {EzGraph} graph
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
 * Open a newly loaded App on standard: the rung that writes nothing, so the
 * graph queues exactly as this App ships it. No browser-global selects a rung.
 * @param {EzGraph} graph
 * @param {EzWidget|undefined} widget
 * @returns {boolean} true when the row was seeded
 */
function seedStandardOnOpen(graph, widget) {
  if (!widget) {
    return false;
  }
  const family = graphFamily(graph);
  const ladder = rungsForFamily(family);
  const rung = ladder.map((item) => item.toLowerCase()).includes(RUNG_STANDARD)
    ? RUNG_STANDARD
    : String(ladder[0] || "");
  appliedRungs.set(graph, { rung: rung || RUNG_STANDARD, writes: new Map() });
  overlayWrites.set(graph, new Map());
  rowMoved.set(graph, false);
  if (!rung) {
    return false;
  }
  seedingByGraph.set(graph, true);
  try {
    setQualityOnAll(graph, rung);
  } finally {
    seedingByGraph.set(graph, false);
  }
  return true;
}

/**
 * Snapshot the graph and bind every Detail combo.
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
    seedStandardOnOpen(graph, widgetByName(driver, "quality"));
  } else {
    retryPendingApply(graph);
  }
  syncQualityFromGraph(graph);
}

/**
 * Snapshot what the graph shipped with, so the caption can tell an authored
 * widget from a hand-edited one under the rung that writes nothing.
 * @param {EzGraph|undefined} graph
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
  appliedRungs.delete(g);
  rowMoved.set(g, false);
  pendingApplies.delete(g);
}

app.registerExtension({
  name: "ez_quality.overlay",
  /**
   * Wrap EZQuality so the combo applies overlays on create.
   * @param {EzNodeType} nodeTypeArg
   * @param {EzNodeDef} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeTypeArg, nodeData) {
    if (nodeData.name !== "EZQuality") {
      return;
    }
    const onNodeCreated = nodeTypeArg.prototype.onNodeCreated;
    /**
     * Bind the Detail combo when the node is created.
     * @returns {void}
     */
    nodeTypeArg.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      bindQualityNode(this);
      bindOverlayWatchers(this.graph);
    };
  },
  /**
   * Re-read the graph after a load, retrying a rung a lazy widget blocked.
   * @returns {Promise<void>}
   */
  async afterConfigureGraph() {
    bindAll();
  },
  /**
   * Watch overlay widgets when a node is created after graph load.
   * @param {EzNode} node
   * @returns {void}
   */
  nodeCreated(node) {
    bindOverlayWatchersForNode(node);
    syncQualityFromGraph(node?.graph);
  },
  /**
   * Keep the caption honest while the operator edits the graph.
   * @param {EzGraph} graph
   * @returns {void}
   */
  graphChanged(graph) {
    syncQualityFromGraph(graph || app.graph);
  },
});

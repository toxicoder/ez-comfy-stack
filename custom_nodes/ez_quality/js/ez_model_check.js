/**
 * EZModelCheck: button POSTs /ez_quality/check. Queue does not run this node.
 *
 * Nodes 2.0: addWidget("button") plus widget.value. No LiteGraph hooks.
 *
 * A second button files the last verdict through the ez_feedback pack
 * (window.EzFeedback), reached lazily at click time so extension load order
 * cannot break this node. Reports carry pack/preset identities only: the
 * payload's operator commands hold host paths and never leave the page.
 */
import { app } from "../../scripts/app.js";

const CHECK_ENDPOINT = "/ez_quality/check";
const REPORT_SURFACE = "model-check";
const REPORT_KIND = "bug";
const FALLBACK_REPO = "toxicoder/ez-comfy-stack";

const ENHANCE = new Set([
  "EZKleinPromptEnhance",
  "EZWanPromptEnhance",
  "EZLTXPromptEnhance",
  "EZZimagePromptEnhance",
  "EZLongCatPromptEnhance",
  "EZDreamXPromptEnhance",
  "EZAceStepPromptEnhance",
  "EZNegativePromptEnhance",
]);

/**
 * One slot in widgets_values: a scalar, or a record the widget owns.
 * @typedef {string|number|boolean|null|Object} EzSlotValue
 */

/**
 * Widget as this file reads it: a name to match and a value to post.
 * @typedef {Object} EzWidget
 * @property {string=} name Name widgetValue and setStatus match on.
 * @property {string|number|boolean|null=} value Value the node carries.
 * @property {(text: string) => void=} callback Fired after a value write.
 */

/**
 * Graph node as this file reads it, muted lanes and the EZModelCheck node
 * itself included. LiteGraph owns the rest of the shape.
 * @typedef {Object} EzNode
 * @property {string=} type Node class as LiteGraph names it.
 * @property {string=} comfyClass Nodes 2.0 alias for type.
 * @property {number=} mode 0 runs; any other mode is muted or bypassed.
 * @property {Array<EzWidget>=} widgets Widgets LiteGraph carries.
 * @property {Array<EzSlotValue>=} widgets_values Values in widget order.
 * @property {EzCheckPayload=} _ezLastCheck Last verdict, cached by runOnNode.
 * @property {EzCheckHints=} _ezLastHints Hints that check posted.
 */

/**
 * Per-graph extras bag Comfy carries beside the node list.
 * @typedef {Object} EzGraphExtra
 * @property {string=} lab_rel App folder the graph belongs to.
 * @property {boolean=} lab_iclora Iclora hint collectHints forwards.
 * @property {boolean=} lab_vace Vace hint collectHints forwards.
 * @property {EzAppMode=} lab_app_mode Studio app mode block.
 */

/**
 * Studio app mode block inside graph extra; only occupancy is read here.
 * @typedef {Object} EzAppMode
 * @property {string=} occupancy Heavy job the host holds, or "".
 */

/**
 * Graph as this file reads it: the node list plus the extras bag.
 * @typedef {Object} EzGraph
 * @property {Array<EzNode>=} nodes Nodes on the graph.
 * @property {EzGraphExtra=} extra Comfy's per-graph extras bag.
 */

/**
 * Snapshot POSTed to /ez_quality/check; mirrors CheckHints in check.py.
 * @typedef {Object} EzCheckHints
 * @property {string=} lab_rel App folder the graph belongs to.
 * @property {string=} occupancy Occupancy the overlay reports.
 * @property {string=} quality Quality tier the overlay reports.
 * @property {Array<string>=} types Every node class on the graph.
 * @property {Array<string>=} unets UNETLoader filenames.
 * @property {Array<string>=} clips CLIPLoader filenames.
 * @property {Array<string>=} vaes VAELoader filenames.
 * @property {Array<string>=} loras LoraLoader filenames.
 * @property {Array<string>=} checkpoints CheckpointLoaderSimple filenames.
 * @property {boolean=} enhance_on A prompt enhancer runs on this graph.
 * @property {boolean=} describe_on EZImageDescribe runs on this graph.
 * @property {Array<string>=} flags Extra hints: iclora and vace.
 */

/**
 * One scanned file row of the check payload; mirrors FileRow in check.py.
 * @typedef {Object} EzCheckRow
 * @property {string=} name Filename the scan looked for.
 * @property {string=} pack Pack that owns the file.
 * @property {string=} cmd Operator command that fetches it.
 * @property {string=} state Scan verdict for the row.
 */

/**
 * Verdict POST /ez_quality/check returns, cached on the node.
 * @typedef {Object} EzCheckPayload
 * @property {boolean=} ok True when every named pack is on disk.
 * @property {string=} message Report head, painted on the status widget.
 * @property {string=} lab_rel App the scan ran against.
 * @property {string=} occupancy Occupancy the hints carried.
 * @property {string=} quality Quality tier the hints carried.
 * @property {Array<EzCheckRow>=} present Rows the box has.
 * @property {Array<EzCheckRow>=} missing Rows the box lacks.
 * @property {Array<string>=} commands Operator commands to run.
 * @property {boolean=} _ezRecorded Set when the failure is already logged.
 */

/**
 * Report draft reportFailure hands ez_feedback, or the issues URL.
 * @typedef {Object} EzReportDraft
 * @property {string=} kind Issue kind the repo labels the issue with.
 * @property {string=} surface Surface that filed it, model-check here.
 * @property {string=} summary One-line verdict shown at the top.
 * @property {Array<Array<string>>=} context [label, value] rows.
 */

/**
 * One line pushed into the ez_feedback ring buffer.
 * @typedef {Object} EzErrorRecord
 * @property {string=} ts ISO timestamp of the failure.
 * @property {string=} surface Surface that failed.
 * @property {string=} message Status line, first line only.
 * @property {string=} detail Command hint, first line only.
 */

/**
 * The ez_feedback client off window, reached lazily at click time.
 * @typedef {Object} EzFeedbackClient
 * @property {(draft: EzReportDraft) => void=} openReport Open the dialog.
 * @property {(record: EzErrorRecord) => void=} recordError Push one line.
 * @property {string=} REPO Repo the direct-to-GitHub link points at.
 */

/**
 * Node class LiteGraph is registering. LiteGraph owns the whole shape, so the
 * button mount only reaches through its prototype at runtime.
 * @typedef {Object} EzNodeType
 */

/**
 * Node definition beforeRegisterNodeDef is called with.
 * @typedef {Object} EzNodeDef
 * @property {string=} name Class name the registry keys the node under.
 */

/**
 * Backend URL, honoring Comfy's api prefix when present.
 * @param {string} path
 * @returns {string}
 */
function apiUrl(path) {
  if (app.api && typeof app.api.apiURL === "function") {
    return app.api.apiURL(path);
  }
  return path;
}

/**
 * Widget value by name, else widgets_values[index].
 * @param {EzNode} node
 * @param {string} name
 * @param {number} [index]
 * @returns {string|number|boolean|null|undefined} Live value, else the slot.
 */
function widgetValue(node, name, index) {
  const widgets = node.widgets || [];
  const hit = widgets.find((item) => item && item.name === name);
  if (hit && hit.value !== undefined && hit.value !== null) {
    return hit.value;
  }
  const values = node.widgets_values || [];
  if (index != null && index < values.length) {
    return values[index];
  }
  return undefined;
}

/**
 * First string widget (loader filename).
 * @param {EzNode} node
 * @returns {string}
 */
function firstName(node) {
  const widgets = node.widgets || [];
  if (widgets.length && widgets[0] && widgets[0].value) {
    return String(widgets[0].value);
  }
  const values = node.widgets_values || [];
  if (values.length && values[0] && typeof values[0] !== "object") {
    return String(values[0]);
  }
  return "";
}

/**
 * Tier the overlay reports, read off the same combo the overlay acts on: the
 * first visible EZQuality. A muted copy drives nothing, so it reports nothing.
 * @param {EzGraph} [graph]
 * @returns {string}
 */
function tierFromGraph(graph) {
  let fallback = "";
  for (const node of graph?.nodes || []) {
    if ((node.type || node.comfyClass || "") !== "EZQuality") {
      continue;
    }
    const value = String(widgetValue(node, "quality", 0) || "");
    if (!value) {
      continue;
    }
    if (node.mode == null || node.mode === 0) {
      return value;
    }
    if (!fallback) {
      fallback = value;
    }
  }
  return fallback || "lab";
}

/**
 * Compact graph snapshot for POST /ez_quality/check.
 * @param {EzGraph} [graph]
 * @returns {EzCheckHints}
 */
function collectHints(graph) {
  const g = graph || app.graph || {};
  const extra = g.extra || {};
  const occupancy = extra.lab_app_mode?.occupancy || "";
  const labRel = extra.lab_rel || "";
  const types = [];
  const unets = [];
  const clips = [];
  const vaes = [];
  const loras = [];
  const checkpoints = [];
  let enhanceOn = false;
  let describeOn = false;
  for (const node of g.nodes || []) {
    const ntype = node.type || node.comfyClass || "";
    if (!ntype) {
      continue;
    }
    types.push(ntype);
    const name = firstName(node);
    if (ntype === "UNETLoader" && name) {
      unets.push(name);
    } else if (ntype === "CLIPLoader" && name) {
      clips.push(name);
    } else if (ntype === "VAELoader" && name) {
      vaes.push(name);
    } else if ((ntype === "LoraLoader" || ntype === "LoraLoaderModelOnly") && name) {
      loras.push(name);
    } else if (ntype === "CheckpointLoaderSimple" && name) {
      checkpoints.push(name);
    }
    if (ENHANCE.has(ntype) && widgetValue(node, "enhance") === true) {
      enhanceOn = true;
    }
    if (ntype === "EZImageDescribe" && widgetValue(node, "enable", 0) === true) {
      describeOn = true;
    }
  }
  const quality = tierFromGraph(g);
  const flags = [];
  if (extra.lab_iclora) {
    flags.push("iclora");
  }
  if (extra.lab_vace) {
    flags.push("vace");
  }
  return {
    lab_rel: labRel,
    occupancy,
    quality,
    types,
    unets,
    clips,
    vaes,
    loras,
    checkpoints,
    enhance_on: enhanceOn,
    describe_on: describeOn,
    flags,
  };
}

/**
 * Reach the ez_feedback client lazily; extension load order cannot break this.
 * @returns {EzFeedbackClient|null} window.EzFeedback when it can file a report.
 */
function feedbackApi() {
  const fb = typeof window === "undefined" ? null : window.EzFeedback;
  return fb && typeof fb.openReport === "function" ? fb : null;
}

/**
 * Collapse a status line for the ring buffer: first line only, so the
 * operator commands format_report appends after "Run:" never leave the page.
 * @param {string} text
 * @param {number} [max]
 * @returns {string}
 */
function oneLine(text, max) {
  const limit = typeof max === "number" ? max : 160;
  const head = String(text || "")
    .split("\n", 1)[0]
    .replace(/\s+/g, " ")
    .trim();
  return head.length > limit ? `${head.slice(0, limit - 3)}...` : head;
}

/**
 * Push one check failure into the ez_feedback ring buffer. Best effort.
 * @param {string} message
 * @param {string} detail
 * @returns {void}
 */
function recordCheckError(message, detail) {
  const fb = feedbackApi();
  if (!fb || typeof fb.recordError !== "function") {
    return;
  }
  try {
    fb.recordError({
      ts: new Date().toISOString(),
      surface: REPORT_SURFACE,
      message: oneLine(message, 160) || "Model check failed.",
      detail: oneLine(detail || `POST ${CHECK_ENDPOINT}`, 120),
    });
  } catch (err) {
    // A dead ring buffer must not swallow the status paint below it.
  }
}

/**
 * Pack ids the last check could not satisfy, payload order, de-duplicated.
 * @param {EzCheckPayload} result Cached /ez_quality/check payload.
 * @returns {string[]} Need.pack values from check.py.
 */
function missingPacks(result) {
  const packs = [];
  for (const row of (result && result.missing) || []) {
    const pack = String((row && row.pack) || "").trim();
    if (pack && !packs.includes(pack)) {
      packs.push(pack);
    }
  }
  return packs;
}

/**
 * Context rows for the report. The operator commands stay out of it because
 * they are host paths; the pack names carry the same identity safely.
 * @param {EzNode} node
 * @returns {Array<Array<string>>} [label, value] pairs for ez_feedback.
 */
function reportContext(node) {
  const result = node._ezLastCheck || {};
  const hints = node._ezLastHints || {};
  const packs = missingPacks(result).join(", ");
  return [
    ["App", String(result.lab_rel || hints.lab_rel || "")],
    ["Occupancy", String(result.occupancy || hints.occupancy || "")],
    ["Quality preset", String(result.quality || hints.quality || "")],
    ["Missing packs", packs || "none"],
    ["Present count", String((result.present || []).length)],
    ["Missing count", String((result.missing || []).length)],
    ["Rewrite on", String(hints.enhance_on === true)],
    ["Describe on", String(hints.describe_on === true)],
  ];
}

/**
 * One-line summary that states the last verdict, ready or not.
 * @param {EzNode} node
 * @returns {string}
 */
function reportSummary(node) {
  const result = node._ezLastCheck || {};
  const hints = node._ezLastHints || {};
  const label = String(result.lab_rel || hints.lab_rel || "this App");
  const quality = String(result.quality || hints.quality || "lab");
  if (!node._ezLastCheck) {
    return `Model check has not run for ${label} @ ${quality}`;
  }
  if (result.ok === true) {
    return `Model check passed for ${label} @ ${quality}`;
  }
  const packs = missingPacks(result).join(", ");
  return `Model check failed for ${label} @ ${quality}: ${packs || "missing models"}`;
}

/**
 * Open the repo issues page when the ez_feedback pack is not loaded.
 * @param {EzReportDraft} partial Report fields built by reportFailure.
 * @returns {void}
 */
function openIssuesFallback(partial) {
  const fb = typeof window === "undefined" ? null : window.EzFeedback;
  const repo = (fb && fb.REPO) || FALLBACK_REPO;
  const params = new URLSearchParams({
    title: `[${REPORT_SURFACE}] ${String((partial && partial.summary) || "")}`,
    labels: REPORT_KIND,
  });
  window.open(
    `https://github.com/${repo}/issues/new?${params.toString()}`,
    "_blank",
    "noopener",
  );
}

/**
 * File the last verdict. Fire and forget: no await, no focus, no alert.
 * @param {EzNode} node
 * @returns {void}
 */
function reportFailure(node) {
  const partial = {
    kind: REPORT_KIND,
    surface: REPORT_SURFACE,
    summary: reportSummary(node),
    context: reportContext(node),
  };
  const fb = feedbackApi();
  if (!fb) {
    openIssuesFallback(partial);
    return;
  }
  try {
    fb.openReport(partial);
  } catch (err) {
    openIssuesFallback(partial);
  }
}

/**
 * POST a hints snapshot and return the JSON payload.
 * @param {EzCheckHints} hints Snapshot built by collectHints.
 * @returns {Promise<EzCheckPayload>}
 */
async function postCheckHints(hints) {
  const response = await fetch(apiUrl(CHECK_ENDPOINT), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(hints),
  });
  const payload = await response.json();
  if (payload && typeof payload === "object") {
    return payload;
  }
  // _ezRecorded keeps runOnNode from logging this same failure twice.
  const empty = { ok: false, message: "Check failed.", _ezRecorded: true };
  recordCheckError(empty.message, `POST ${CHECK_ENDPOINT} returned no JSON`);
  return empty;
}

/**
 * POST hints and return the JSON payload.
 * @param {EzGraph} [graph]
 * @returns {Promise<EzCheckPayload>}
 */
function postCheck(graph) {
  return postCheckHints(collectHints(graph));
}

/**
 * Write the status STRING on an EZModelCheck node.
 * @param {EzNode} node
 * @param {string} text
 * @returns {void}
 */
function setStatus(node, text) {
  const widget = (node.widgets || []).find((item) => item && item.name === "status");
  if (widget) {
    widget.value = text;
    if (typeof widget.callback === "function") {
      widget.callback(text);
    }
  }
  if (node.widgets_values && node.widgets_values.length) {
    node.widgets_values[0] = text;
  }
  app.graph?.setDirtyCanvas?.(true);
}

/**
 * Run the check, cache the verdict + hints on the node, paint the node.
 * @param {EzNode} node
 * @returns {Promise<void>}
 */
async function runOnNode(node) {
  setStatus(node, "Checking models...");
  try {
    const hints = collectHints(app.graph);
    node._ezLastHints = hints;
    const payload = await postCheckHints(hints);
    node._ezLastCheck = payload;
    const text = String(payload.message || (payload.ok ? "Ready." : "Missing models."));
    setStatus(node, text);
    if (payload.ok !== true && payload._ezRecorded !== true) {
      recordCheckError(text, `POST ${CHECK_ENDPOINT}`);
    }
  } catch (err) {
    const text = `Check failed: ${err && err.message ? err.message : err}`;
    node._ezLastCheck = { ok: false, message: text };
    setStatus(node, text);
    recordCheckError(text, `POST ${CHECK_ENDPOINT} threw`);
  }
}

window.ezComfyModelCheck = {
  collectHints,
  postCheck,
  postCheckHints,
  runOnNode,
  reportFailure,
  reportSummary,
  reportContext,
  missingPacks,
};

app.registerExtension({
  name: "ez_quality.model_check",
  /**
   * Add the Check models button on create.
   * @param {EzNodeType} nodeType
   * @param {EzNodeDef} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "EZModelCheck") {
      return;
    }
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    /**
     * Mount the native button widgets: re-check, then file the last verdict.
     * @returns {void}
     */
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      this.addWidget("button", "Check models", "check", () => {
        runOnNode(this);
      });
      this.addWidget("button", "Report failure", "report", () => {
        reportFailure(this);
      });
    };
  },
});

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
 * @param {object} node
 * @param {string} name
 * @param {number} [index]
 * @returns {*}
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
 * @param {object} node
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
 * Compact graph snapshot for POST /ez_quality/check.
 * @param {object} [graph]
 * @returns {object}
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
  let quality = "lab";
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
    } else if (ntype === "EZQuality") {
      quality = String(widgetValue(node, "quality", 0) || "lab");
    }
    if (ENHANCE.has(ntype) && widgetValue(node, "enhance") === true) {
      enhanceOn = true;
    }
    if (ntype === "EZImageDescribe" && widgetValue(node, "enable", 0) === true) {
      describeOn = true;
    }
  }
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
 * @returns {object|null} window.EzFeedback when it can file a report.
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
 * @param {object} result Cached /ez_quality/check payload.
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
 * @param {object} node
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
 * @param {object} node
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
 * @param {object} partial Report fields built by reportFailure.
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
 * @param {object} node
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
 * @param {object} hints Snapshot built by collectHints.
 * @returns {Promise<object>}
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
 * @param {object} [graph]
 * @returns {Promise<object>}
 */
function postCheck(graph) {
  return postCheckHints(collectHints(graph));
}

/**
 * Write the status STRING on an EZModelCheck node.
 * @param {object} node
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
 * @param {object} node
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
   * @param {object} nodeType
   * @param {object} nodeData
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

/**
 * Header chrome for ez-comfy reports: two buttons, error capture, no blocking.
 *
 * Mounts "Report a bug" and "Request a feature" into the App widgets host
 * (`[data-testid=linear-widgets]`), or a fixed-position fallback, and keeps
 * them mounted through a MutationObserver on `document.body` the way the
 * occupancy chip does. Prefill comes from the live graph (`extra.lab_*`),
 * failures go into the shared ring buffer, and every dialog/banner lives in
 * `ez_feedback_core.js`, reached through `window.EzFeedback` at click time so
 * extension load order cannot break this file.
 *
 * Nodes 2.0 safe: no LiteGraph widget hooks, no canvas resize, no queue hook,
 * and nothing here can delay a run.
 */
import { app } from "../../scripts/app.js";

const BAR_ID = "ez-fb-bar";
const HOST_SELECTOR = "[data-testid=linear-widgets]";
const SYSTEM_PATH = "/system_stats";
const NOTE_MAX = 240;
const MESSAGE_MAX = 220;
const DETAIL_MAX = 240;
const ERROR_KEYS = [
  "prompt_id",
  "node_id",
  "node_type",
  "exception_type",
  "exception_message",
];

/**
 * The shared machinery, resolved lazily so load order cannot break us.
 * @returns {object|null} `window.EzFeedback`, or null before it loads.
 */
function core() {
  return (typeof window !== "undefined" && window.EzFeedback) || null;
}

/**
 * Comfy API client when the frontend exposes one.
 * @returns {object|null} `app.api`.
 */
function apiClient() {
  return (app && app.api) || null;
}

/**
 * Backend URL, honoring Comfy's api prefix when present.
 * @param {string} path Route path.
 * @param {string} unprefixed Fallback when there is no api client.
 * @returns {string} Fetchable path.
 */
function apiUrl(path, unprefixed) {
  const client = apiClient();
  if (client && typeof client.apiURL === "function") {
    return client.apiURL(path);
  }
  return unprefixed;
}

/**
 * Collapse whitespace and cap a field so a report line stays short.
 * @param {*} value Raw text.
 * @param {number} max Maximum length, including the trailing dots when trimmed.
 * @returns {string} Single-line text.
 */
function clip(value, max) {
  const text = String(value === undefined || value === null ? "" : value)
    .split(/\s+/)
    .join(" ")
    .trim();
  if (text.length <= max) {
    return text;
  }
  if (max < 2) {
    return "";
  }
  return text.slice(0, max - 3) + "...";
}

/**
 * `extra` of the graph that is open right now.
 * @returns {object} Graph extra, or `{}`.
 */
function graphExtra() {
  return (app && app.graph && app.graph.extra) || {};
}

/**
 * Name of the workflow the workflow manager has active.
 * @returns {string} Workflow name, or `""`.
 */
function activeWorkflowName() {
  return (app && app.workflowManager && app.workflowManager.activeWorkflow
    && app.workflowManager.activeWorkflow.name) || "";
}

/**
 * Count of nodes on the current graph.
 * @returns {number} Node count.
 */
function nodeCount() {
  const nodes = (app && app.graph && app.graph.nodes) || [];
  return Array.isArray(nodes) ? nodes.length : 0;
}

/**
 * The App Mode block stamped on the graph.
 * @returns {object} `{lane, occupancy, default_view}` shaped data.
 */
function appMode() {
  const mode = graphExtra().lab_app_mode;
  return mode && typeof mode === "object" ? mode : {};
}

let systemFacts = {};
let lastFailure = null;

/**
 * Pick the torch / CUDA / GPU / OS facts a report should carry.
 * @param {object} data Parsed `/system_stats` payload.
 * @returns {object} Fact map; empty keys are dropped later.
 */
function pickSystemFacts(data) {
  const payload = data && typeof data === "object" ? data : {};
  const system = payload.system && typeof payload.system === "object" ? payload.system : {};
  const devices = Array.isArray(payload.devices) ? payload.devices : [];
  const device = devices[0] || {};
  return {
    comfyui: payload.comfyui_version || system.comfyui_version || "",
    os: system.os || "",
    python: system.python_version || "",
    gpu: device.name || "",
    device_type: device.type || "",
    torch: device.torch_version || "",
    cuda: device.cuda_version || "",
  };
}

/**
 * Environment pairs from the last best-effort `/system_stats` read.
 * @returns {Array<Array<string>>} Pairs; empty when the route was absent.
 */
function systemPairs() {
  const labels = {
    comfyui: "ComfyUI",
    os: "OS",
    python: "Python",
    gpu: "GPU",
    device_type: "Device",
    torch: "torch",
    cuda: "CUDA",
  };
  const pairs = [];
  Object.keys(labels).forEach((key) => {
    const value = String(systemFacts[key] || "").trim();
    if (value) {
      pairs.push([labels[key], value]);
    }
  });
  return pairs;
}

/**
 * Fetch `/system_stats` once per setup; absent or offline degrades silently.
 * @returns {Promise<object>} The facts that resolved.
 */
async function loadSystemStats() {
  try {
    const response = await fetch(apiUrl(SYSTEM_PATH, "/api" + SYSTEM_PATH), {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      return systemFacts;
    }
    const data = await response.json();
    systemFacts = pickSystemFacts(data);
  } catch (_err) {
    systemFacts = {};
  }
  return systemFacts;
}

/**
 * Surface id for a report: the App when a lab graph is open, else global.
 * @returns {string} "app" or "global".
 */
function currentSurface() {
  return String(graphExtra().lab_rel || "").trim() ? "app" : "global";
}

/**
 * Context pairs describing the graph behind the report.
 *
 * Reads `extra.lab_rel`, `lab_app_mode` (lane, occupancy, default_view),
 * `lab_description`, `lab_note` (clipped), `lab_quality_caption`,
 * `lab_album`, the node count, and the active workflow name. Everything is
 * behind optional access so a bare graph is fine.
 * @returns {Array<Array<string>>} Label/value pairs for `## Context`.
 */
function graphContext() {
  const extra = graphExtra();
  const mode = appMode();
  const pairs = [];
  const push = (label, value) => {
    const text = String(value === undefined || value === null ? "" : value).trim();
    if (text) {
      pairs.push([label, text]);
    }
  };
  push("App", extra.lab_rel);
  push("Workflow", activeWorkflowName());
  push("Lane", mode.lane);
  push("Occupancy", mode.occupancy);
  push("Default view", mode.default_view);
  push("Description", clip(extra.lab_description, NOTE_MAX));
  push("Note", clip(extra.lab_note, NOTE_MAX));
  push("Quality", extra.lab_quality_caption);
  push("Album", extra.lab_album);
  push("Nodes", nodeCount());
  return pairs;
}

/**
 * Build the partial report a click should open.
 * @param {string} kind "bug" or "enhancement".
 * @param {object} [extra] `{summary, context, traceback}` overrides.
 * @returns {object} Partial report for the core dialog.
 */
function reportFor(kind, extra) {
  const options = extra && typeof extra === "object" ? extra : {};
  const rel = String(graphExtra().lab_rel || "").trim();
  const context = Array.isArray(options.context) ? options.context : graphContext();
  return {
    kind,
    surface: rel ? "app" : "global",
    app: rel,
    summary: options.summary || "",
    context,
    environment: systemPairs(),
    traceback: options.traceback || "",
  };
}

/**
 * Pull the fields the frontend sends on an execution event.
 * @param {object} event Comfy event, or its `detail`.
 * @returns {object} Normalized failure detail.
 */
function failureDetail(event) {
  const raw = (event && event.detail) || event || {};
  const detail = {};
  ERROR_KEYS.forEach((key) => {
    if (raw[key] !== undefined && raw[key] !== null && raw[key] !== "") {
      detail[key] = raw[key];
    }
  });
  detail.traceback = raw.traceback;
  detail.current_inputs = raw.current_inputs;
  detail.current_outputs = raw.current_outputs;
  return detail;
}

/**
 * One-line detail for the ring buffer entry.
 * @param {object} detail Normalized failure detail.
 * @returns {string} Compact text.
 */
function failureLine(detail) {
  const bits = [];
  if (detail.prompt_id) {
    bits.push("prompt " + detail.prompt_id);
  }
  if (detail.node_id !== undefined) {
    bits.push("node " + detail.node_id);
  }
  if (detail.node_type) {
    bits.push("type " + detail.node_type);
  }
  if (detail.exception_type) {
    bits.push(String(detail.exception_type));
  }
  return clip(bits.join(" "), DETAIL_MAX);
}

/**
 * Textual traceback for the report, from the event's `traceback` field.
 * @param {object} detail Normalized failure detail.
 * @returns {string} Traceback text, or `""`.
 */
function failureTraceback(detail) {
  const raw = detail.traceback;
  if (Array.isArray(raw)) {
    return raw.map((line) => String(line)).join("\n").trim();
  }
  return String(raw || "").trim();
}

/**
 * JSON dump of the failing node inputs and outputs for `## Context`.
 * @param {object} detail Normalized failure detail.
 * @returns {Array<Array<string>>} Context pairs from the event.
 */
function failureContext(detail) {
  const pairs = graphContext();
  const dump = (value) => {
    try {
      return clip(JSON.stringify(value), DETAIL_MAX);
    } catch (_err) {
      return String(value);
    }
  };
  if (detail.current_inputs) {
    pairs.push(["Failing inputs", dump(detail.current_inputs)]);
  }
  if (detail.current_outputs) {
    pairs.push(["Produced outputs", dump(detail.current_outputs)]);
  }
  return pairs;
}

/**
 * Record a failed or interrupted execution and offer the report banner.
 *
 * Additive only: this never throws into the frontend and never touches the
 * queue path, so a run cannot be blocked by report machinery.
 * @param {string} kind Report kind, "bug" for both failure events.
 * @param {string} headline Banner line.
 * @param {object} event Comfy execution event.
 * @returns {void}
 */
function captureFailure(kind, headline, event) {
  try {
    const detail = failureDetail(event);
    const message = clip(
      detail.exception_message || detail.exception_type || headline,
      MESSAGE_MAX
    );
    const entry = {
      ts: new Date().toISOString(),
      surface: currentSurface(),
      message,
      detail: failureLine(detail),
    };
    const fb = core();
    if (!fb) {
      return;
    }
    fb.recordError(entry);
    lastFailure = {
      headline,
      summary: message,
      context: failureContext(detail),
      traceback: failureTraceback(detail),
    };
    fb.showBanner(reportFor(kind, lastFailure), { message: headline });
    const toast = app && app.extensionManager && app.extensionManager.toast;
    if (toast && typeof toast.addToast === "function") {
      toast.addToast({ title: "ez-comfy", detail: headline, type: "error", timeout: 6000 });
    }
  } catch (_err) {
    // Report chrome must never break a run.
  }
}

/**
 * Reuse or create the header button bar.
 * @returns {HTMLElement} The bar element.
 */
function ensureBar() {
  let el = document.getElementById(BAR_ID);
  if (el) {
    return el;
  }
  el = document.createElement("div");
  el.id = BAR_ID;
  el.setAttribute("role", "toolbar");
  el.setAttribute("aria-label", "ez-comfy feedback");
  document.body.appendChild(el);
  return el;
}

/**
 * One labelled report button for the bar.
 * @param {string} label Button text.
 * @param {string} kind "bug" or "enhancement".
 * @returns {HTMLButtonElement} The button.
 */
function makeReportButton(label, kind) {
  const node = document.createElement("button");
  node.type = "button";
  node.className = "ez-fb-btn";
  node.setAttribute("data-ez-fb-kind", kind);
  node.textContent = label;
  node.addEventListener("click", () => {
    const fb = core();
    if (fb && typeof fb.openReport === "function") {
      fb.openReport(reportFor(kind));
      return;
    }
    const surface = currentSurface();
    const rel = String(graphExtra().lab_rel || "").trim();
    const params = new URLSearchParams({
      title: clip((kind === "enhancement" ? "Feature request" : "Bug report") + " from " + (rel || surface), 140),
      labels: kind === "enhancement" ? "enhancement" : "bug",
    });
    window.open("https://github.com/toxicoder/ez-comfy-stack/issues/new?" + params.toString(), "_blank", "noopener");
  });
  return node;
}

/**
 * Fill the bar with the two buttons (re-rendered on every graph change).
 * @param {HTMLElement} el The bar element.
 * @returns {void}
 */
function renderBar(el) {
  el.innerHTML = "";
  el.append(makeReportButton("Report a bug", "bug"), makeReportButton("Request a feature", "enhancement"));
}

/**
 * Stick the bar into the App widgets host, else pin it under the header.
 * @param {HTMLElement} el The bar element.
 * @returns {void}
 */
function mountBar(el) {
  const host = document.querySelector(HOST_SELECTOR);
  if (host) {
    el.className = "ez-fb-bar ez-fb-bar-inline";
    if (el.parentElement !== host) {
      host.appendChild(el);
    }
    return;
  }
  el.className = "ez-fb-bar ez-fb-bar-fixed";
  if (el.parentElement !== document.body) {
    document.body.appendChild(el);
  }
}

/**
 * Re-render and re-mount the bar after the graph or the DOM changed.
 * @returns {void}
 */
function refreshChrome() {
  const el = ensureBar();
  renderBar(el);
  mountBar(el);
}

app.registerExtension({
  name: "ez.feedback.chrome",
  /**
   * Mount the buttons, watch the graph and the DOM, and start error capture.
   * @returns {Promise<void>}
   */
  async setup() {
    const client = apiClient();
    if (client && typeof window !== "undefined") {
      // Core resolves the api prefix through this handle without importing
      // anything ComfyUI-owned.
      window.__ezFeedbackApi = client;
    }
    refreshChrome();
    if (app.graph && typeof app.graph.addEventListener === "function") {
      app.graph.addEventListener("configured", () => {
        refreshChrome();
      });
    }
    const observer = new MutationObserver(() => {
      const el = document.getElementById(BAR_ID);
      if (el) {
        mountBar(el);
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
    if (client && typeof client.addEventListener === "function") {
      client.addEventListener("execution_error", (event) => {
        captureFailure("bug", "Run failed - report it with the graph context attached.", event);
      });
      client.addEventListener("execution_interrupted", (event) => {
        captureFailure("bug", "Run interrupted - report it if that was not you.", event);
      });
    }
    loadSystemStats();
  },
});

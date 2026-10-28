/**
 * Shared bug-report / feature-request machinery for every ez-comfy surface.
 *
 * Zero ComfyUI imports: this file is safe to auto-inject as a bare module and
 * it sets `window.EzFeedback` at top level, so other packs reach it lazily at
 * click time and extension load order cannot break them. The dialog and the
 * banner are hand-rolled DOM (position fixed, explicit z-index), the way the
 * ez_film preview overlay and the ez_outputs lightbox already are: no
 * deprecated frontend UI module, no toast dependency, nothing that can block
 * a run.
 *
 * Title, label, body, and URL rules mirror `ez_feedback/context.py`, which is
 * the canonical source. Filing is token-optional: with a server token the
 * dialog offers "File directly"; without one every button is a prefilled
 * `/issues/new` handoff.
 */

export const REPO = "toxicoder/ez-comfy-stack";
/** Repository reports are filed against. */

const GITHUB_URL = "https://github.com";
const ISSUES_NEW = GITHUB_URL + "/" + REPO + "/issues/new";
const CONFIG_PATH = "/ez_feedback/config";
const SUBMIT_PATH = "/ez_feedback/submit";
const API_GLOBAL = "__ezFeedbackApi";

export const MAX_HREF = 5500;
/** New-issue URL budget; past it the body degrades, the URL is never cut. */

const MAX_TITLE = 140;
const MAX_FIELD = 300;
const RING_MAX = 5;
const STYLE_ID = "ez-feedback-css";
const DIALOG_ID = "ez-fb-dialog";
const BACKDROP_ID = "ez-fb-backdrop";
const BANNER_ID = "ez-fb-banner";

const LABELS = { bug: "bug", enhancement: "enhancement" };
const DEFAULT_SUMMARY = {
  bug: (area) => "Bug report from " + area,
  enhancement: (area) => "Feature request from " + area,
};

const FILL_IN = "<!-- Replace this line. -->";
const FILL_HEADINGS = ["## What happened", "## Steps", "## Expected", "## Actual"];
const CONTEXT_HEADING = "## Context";
const ENVIRONMENT_HEADING = "## Environment";
const ERRORS_HEADING = "## Recent errors";
const BROWSER_HEADING = "## Browser";
const DEGRADE_ORDER = [BROWSER_HEADING, ERRORS_HEADING, ENVIRONMENT_HEADING];
const TRACEBACK_LABEL = "Traceback:";
const BROWSER_FIELDS = [
  ["viewport", "Viewport"],
  ["dpr", "DPR"],
  ["lang", "Language"],
  ["online", "Online"],
  ["ua", "User agent"],
  ["pageUrl", "Page URL"],
];

const FALLBACK_CSS = `
.ez-fb-bar { display:flex; gap:6px; align-items:center; font:12px/1.4 ui-sans-serif,system-ui,sans-serif; }
.ez-fb-bar-fixed { position:fixed; left:12px; top:56px; z-index:40; }
.ez-fb-btn { padding:4px 10px; border-radius:8px; cursor:pointer;
  border:1px solid var(--border-color,rgba(255,255,255,0.16));
  background:var(--comfy-menu-bg,#24272e); color:var(--fg-color,#e8e8e8); }
.ez-fb-backdrop { position:fixed; inset:0; z-index:1080; background:rgba(0,0,0,0.55); }
.ez-fb-dialog { position:fixed; z-index:1081; left:50%; top:50%; transform:translate(-50%,-50%);
  width:min(720px,calc(100vw - 32px)); max-height:min(80vh,720px); overflow:auto; display:flex;
  flex-direction:column; gap:8px; padding:14px; border-radius:12px; box-sizing:border-box;
  background:var(--comfy-menu-bg,#14161b); color:var(--fg-color,#e8e8e8);
  border:1px solid var(--border-color,rgba(255,255,255,0.14));
  box-shadow:0 18px 48px rgba(0,0,0,0.5); font:12px/1.45 ui-sans-serif,system-ui,sans-serif; }
.ez-fb-banner { position:fixed; z-index:1070; right:16px; bottom:16px;
  max-width:min(420px,calc(100vw - 32px)); display:flex; gap:8px; align-items:center;
  padding:10px 12px; border-radius:10px; box-sizing:border-box;
  background:var(--comfy-menu-bg,#14161b); color:var(--fg-color,#e8e8e8);
  border:1px solid var(--border-color,rgba(255,255,255,0.14));
  box-shadow:0 12px 32px rgba(0,0,0,0.45); font:12px/1.45 ui-sans-serif,system-ui,sans-serif; }
.ez-fb-textarea { flex:1; min-height:220px; resize:vertical; box-sizing:border-box;
  font:12px/1.45 ui-monospace,monospace; }
`;

let config = {};
let configPromise = null;
const ring = [];

const TOKEN_RE = /(?:ghp|gho|github_pat|hf)_[A-Za-z0-9][A-Za-z0-9_-]{3,}/g;
/** Shape of the secrets that must never reach a report; mirrors `context.py`. */

/**
 * Scrub secret-shaped runs before anything leaves the page.
 *
 * Every report field is operator- or graph-controlled, including captured
 * `current_inputs`, so a token can arrive through a widget value or a
 * traceback. The server redacts its own path; this closes the client path.
 * @param {*} value Raw text; stringified.
 * @returns {string} Text with secret-shaped runs replaced by `[redacted]`.
 */
export function redact(value) {
  return String(value === undefined || value === null ? "" : value).replace(
    TOKEN_RE,
    "[redacted]",
  );
}

/**
 * Collapse whitespace and cap a field so the issue URL stays openable.
 * @param {*} value Raw text.
 * @param {number} max Maximum length, including the trailing dots when trimmed.
 * @returns {string} A single-line string.
 */
export function clip(value, max) {
  const text = redact(value)
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
 * Normalize a caller-supplied kind.
 * @param {*} value Anything; only "enhancement" is distinct.
 * @returns {string} "bug" or "enhancement".
 */
function kindKey(value) {
  const text = String(value || "").trim().toLowerCase();
  return text === "enhancement" ? "enhancement" : "bug";
}

/**
 * GitHub labels for a kind - only labels that exist in the repo.
 * @param {*} value "bug" or "enhancement".
 * @returns {string[]} One label.
 */
export function labelsFor(value) {
  return [LABELS[kindKey(value)]];
}

/**
 * Title area for a surface: `app:<lab_rel>`, the bare surface id, or global.
 * @param {*} surface One of the shared surface ids.
 * @param {*} app `extra.lab_rel` when the surface is the running App.
 * @returns {string} The area token.
 */
function areaFor(surface, app) {
  const surfaceText = String(surface || "").trim() || "global";
  if (surfaceText === "app") {
    const rel = String(app || "").trim();
    return rel ? "app:" + rel : "app";
  }
  return surfaceText;
}

/**
 * Stringify one report value for a markdown line; booleans render yes / no.
 * @param {*} value Field value.
 * @returns {string} Single-line text, empty when there is nothing to show.
 */
function valueText(value) {
  if (typeof value === "boolean") {
    return value ? "yes" : "no";
  }
  if (value === undefined || value === null) {
    return "";
  }
  return redact(String(value)).split(/\s+/).join(" ").trim();
}

/**
 * Backend URL for a pack route, honoring Comfy's api prefix when the chrome
 * pack published `app.api` on `window.__ezFeedbackApi`.
 * @param {string} path Route path.
 * @returns {string} Fetchable path.
 */
function apiUrl(path) {
  const api = typeof window !== "undefined" ? window[API_GLOBAL] : null;
  if (api && typeof api.apiURL === "function") {
    try {
      return api.apiURL(path);
    } catch (_err) {
      return path;
    }
  }
  return path;
}

/**
 * Browser facts for the `## Browser` block.
 * @returns {{ua: string, viewport: string, dpr: string, lang: string,
 *   online: boolean, pageUrl: string}} Report-shaped facts.
 */
function browserFacts() {
  if (typeof window === "undefined" || typeof navigator === "undefined") {
    return { ua: "", viewport: "", dpr: "", lang: "", online: false, pageUrl: "" };
  }
  return {
    ua: navigator.userAgent || "",
    viewport: window.innerWidth + "x" + window.innerHeight,
    dpr: String(window.devicePixelRatio || 1),
    lang: navigator.language || "",
    online: navigator.onLine !== false,
    pageUrl: typeof location !== "undefined" ? location.href : "",
  };
}

/**
 * Accept `[[label, value], ...]` or a plain object as label/value pairs.
 * @param {*} value Pairs array or object.
 * @returns {Array<Array<string>>} Well-formed pairs only.
 */
function toPairs(value) {
  const pairs = [];
  if (Array.isArray(value)) {
    value.forEach((item) => {
      if (Array.isArray(item) && item.length >= 1) {
        pairs.push([String(item[0] ?? ""), item[1]]);
      }
    });
    return pairs;
  }
  if (value && typeof value === "object") {
    Object.keys(value).forEach((key) => pairs.push([key, value[key]]));
  }
  return pairs;
}

/**
 * Render `- label: value` lines for a Context or Environment block.
 * @param {Array<Array<*>>|null} pairs Pairs; may be missing.
 * @returns {string[]} Markdown bullets, values redacted and clipped.
 */
function contextLines(pairs) {
  const lines = [];
  toPairs(pairs).forEach((pair) => {
    const text = valueText(pair[1]);
    if (!text) {
      return;
    }
    const label = valueText(pair[0]) || "value";
    lines.push("- " + clip(label, MAX_FIELD) + ": " + clip(text, MAX_FIELD));
  });
  return lines;
}

/**
 * Render the `## Recent errors` block from the client ring buffer.
 * @param {Array<object>|null} entries Ring-buffer entries.
 * @param {string} surface Report surface used when an entry carries none.
 * @returns {string[]} Markdown bullets, newest first as supplied.
 */
function errorLines(entries, surface) {
  const lines = [];
  (Array.isArray(entries) ? entries : []).forEach((entry) => {
    if (!entry || typeof entry !== "object") {
      return;
    }
    const message = valueText(entry.message);
    if (!message) {
      return;
    }
    const stamp = valueText(entry.ts) || "unknown";
    const where = valueText(entry.surface) || valueText(surface) || "global";
    let line = "- " + stamp + " [" + where + "] " + clip(message, MAX_FIELD);
    const detail = valueText(entry.detail);
    if (detail) {
      line += " (" + clip(detail, MAX_FIELD) + ")";
    }
    lines.push(line);
  });
  return lines;
}

/**
 * Render the `## Browser` block.
 * @param {object|null} browser Browser facts.
 * @returns {string[]} Markdown bullets for the fields that carry a value.
 */
function browserLines(browser) {
  const lines = [];
  BROWSER_FIELDS.forEach((field) => {
    const text = valueText(browser && browser[field[0]]);
    if (text) {
      lines.push("- " + field[1] + ": " + clip(text, MAX_FIELD));
    }
  });
  return lines;
}

/**
 * One body section: heading, blank line, lines.
 * @param {string} heading `## ` heading.
 * @param {string[]} lines Block content.
 * @returns {string} Section text, empty when there are no lines.
 */
function section(heading, lines) {
  if (!lines || !lines.length) {
    return "";
  }
  return heading + "\n\n" + lines.join("\n");
}

/**
 * Merge caller context with server-reported environment facts.
 * @param {Array<Array<*>>|object|null} own Caller-supplied pairs.
 * @returns {Array<Array<*>>} Caller pairs first, server env filling the rest.
 */
function mergeEnvironment(own) {
  const pairs = toPairs(own);
  const seen = new Set(pairs.map((pair) => valueText(pair[0])));
  toPairs(config && config.env).forEach((pair) => {
    if (!seen.has(valueText(pair[0]))) {
      pairs.push(pair);
    }
  });
  return pairs;
}

/**
 * Normalize a partial report into the full report shape.
 *
 * Everything is optional except `kind` and `surface`. Missing browser facts,
 * environment pairs, and errors are filled from this page, the server config,
 * and the ring buffer.
 * @param {object} partial Partial report.
 * @returns {object} `{kind, surface, app, summary, context, environment,
 *   errors, browser, traceback, blanks}`.
 */
export function reportPayload(partial) {
  const input = partial && typeof partial === "object" ? partial : {};
  return {
    kind: kindKey(input.kind),
    surface: String(input.surface || "").trim() || "global",
    app: String(input.app || "").trim(),
    summary: valueText(input.summary),
    context: toPairs(input.context),
    environment: mergeEnvironment(input.environment),
    errors: Array.isArray(input.errors) && input.errors.length ? input.errors : recentErrors(),
    browser: input.browser && typeof input.browser === "object" ? input.browser : browserFacts(),
    traceback: valueText(input.traceback),
    blanks: input.blanks !== false,
  };
}

/**
 * Issue title `[<area>] <summary>`, clipped to 140 chars, no prefix for global.
 * @param {object} report `{kind, surface, app, summary}`.
 * @returns {string} Single-line title.
 */
export function buildTitle(report) {
  const input = report || {};
  const kind = kindKey(input.kind);
  const area = areaFor(input.surface, input.app);
  const summary = valueText(input.summary) || DEFAULT_SUMMARY[kind](area);
  const title = area === "global" ? summary : "[" + area + "] " + summary;
  return clip(title, MAX_TITLE);
}

/**
 * Assemble the markdown body in the canonical section order.
 *
 * The four narrative sections always appear for a `bug` (unless `blanks` is
 * explicitly false); every other block keeps its heading only when it carries
 * content. A traceback, when supplied, is a fenced block after `## Browser`.
 * @param {object} report Full or partial report.
 * @returns {string} Markdown body without a trailing newline.
 */
export function buildBody(report) {
  const input = report || {};
  const kind = kindKey(input.kind);
  const surface = String(input.surface || "").trim() || "global";
  const blocks = [];
  if (kind === "bug" && input.blanks !== false) {
    FILL_HEADINGS.forEach((heading) => blocks.push(section(heading, [FILL_IN])));
  }
  blocks.push(section(CONTEXT_HEADING, contextLines(input.context)));
  blocks.push(section(ENVIRONMENT_HEADING, contextLines(input.environment)));
  blocks.push(section(ERRORS_HEADING, errorLines(input.errors, surface)));
  blocks.push(section(BROWSER_HEADING, browserLines(input.browser)));
  let body = blocks.filter(Boolean).join("\n\n");
  const note = valueText(input.traceback);
  if (note) {
    const block = TRACEBACK_LABEL + "\n\n```\n" + note + "\n```";
    body = body ? body + "\n\n" + block : block;
  }
  return body.trim();
}

/**
 * Remove one `## ` section (heading plus its lines) from a built body.
 * @param {string} body Body from `buildBody`.
 * @param {string} heading Heading to drop.
 * @returns {string} Body without that section.
 */
function dropSection(body, heading) {
  const kept = [];
  let skipping = false;
  body.split("\n").forEach((line) => {
    if (line.trim() === heading) {
      skipping = true;
      return;
    }
    if (skipping && (line.indexOf("## ") === 0 || line.indexOf(TRACEBACK_LABEL) === 0)) {
      skipping = false;
    }
    if (!skipping) {
      kept.push(line);
    }
  });
  return kept
    .join("\n")
    .split("\n\n")
    .filter((block) => block.trim())
    .join("\n\n");
}

/**
 * Drop the trailing traceback block.
 * @param {string} body Body from `buildBody`.
 * @returns {string} Body without the `Traceback:` block.
 */
function dropTraceback(body) {
  const index = body.indexOf(TRACEBACK_LABEL);
  return index >= 0 ? body.slice(0, index).trimEnd() : body;
}

/**
 * Build the `/issues/new` URL, degrading whole sections past `MAX_HREF`.
 *
 * Drop order is `## Browser`, then `## Recent errors`, then `## Environment`,
 * then the traceback. Title and labels never drop.
 * @param {object} payload Full report shape.
 * @param {string} body Body text to encode.
 * @returns {string} Prefilled new-issue URL.
 */
function hrefFor(payload, body) {
  const title = buildTitle(payload);
  const labels = labelsFor(payload.kind).join(",");
  const build = (text) => {
    const params = new URLSearchParams({ title, body: text, labels });
    return ISSUES_NEW + "?" + params.toString();
  };
  const dropped = [];
  let href = build(body);
  for (const heading of DEGRADE_ORDER) {
    if (href.length <= MAX_HREF) {
      return href;
    }
    dropped.push(heading);
    href = build(dropped.reduce((text, gone) => dropSection(text, gone), body));
  }
  if (href.length <= MAX_HREF) {
    return href;
  }
  const trimmed = dropTraceback(
    dropped.reduce((text, gone) => dropSection(text, gone), body),
  );
  return build(fit(build, trimmed));
}

const TRUNCATION_NOTE = "\n\n[report trimmed to fit the GitHub URL limit]";

/**
 * Longest prefix of `body` whose encoded href still fits `MAX_HREF`.
 *
 * The section ladder alone cannot bound the URL when Context carries many long
 * pairs, and GitHub answers a too-long URL with 414 URI Too Long rather than
 * truncating it, so the tail gets cut here instead of shipping a dead link.
 * @param {function(string): string} build Encoder from body text to href.
 * @param {string} body Candidate body.
 * @returns {string} A body that fits, noting when it was cut.
 */
function fit(build, body) {
  if (build(body).length <= MAX_HREF) {
    return body;
  }
  let low = 0;
  let high = body.length;
  while (low < high) {
    const mid = Math.ceil((low + high) / 2);
    if (build(body.slice(0, mid) + TRUNCATION_NOTE).length <= MAX_HREF) {
      low = mid;
    } else {
      high = mid - 1;
    }
  }
  return body.slice(0, low) + TRUNCATION_NOTE;
}

/**
 * Prefilled GitHub issue URL for a report.
 * @param {object} partial Report or partial report.
 * @returns {string} `https://github.com/<repo>/issues/new?title=&body=&labels=`.
 */
export function issueHref(partial) {
  const payload = reportPayload(partial);
  return hrefFor(payload, buildBody(payload));
}

/**
 * Record one execution failure in the newest-first ring buffer of five.
 * @param {object} entry `{ts, surface, message, detail}`; message is required.
 * @returns {object|null} The stored row, or null when there was no message.
 */
export function recordError(entry) {
  const input = entry && typeof entry === "object" ? entry : {};
  const message = valueText(input.message);
  if (!message) {
    return null;
  }
  const row = {
    ts: valueText(input.ts) || new Date().toISOString(),
    surface: valueText(input.surface) || "global",
    message: clip(message, MAX_FIELD),
    detail: clip(valueText(input.detail), MAX_FIELD),
  };
  ring.unshift(row);
  if (ring.length > RING_MAX) {
    ring.length = RING_MAX;
  }
  return row;
}

/**
 * Copy of the ring buffer, newest first.
 * @returns {Array<object>} Recorded errors.
 */
export function recentErrors() {
  return ring.slice();
}

/**
 * Store the server config from `GET /ez_feedback/config`.
 * @param {object} cfg `{repoUrl, tokenPresent, env, labels}`.
 * @returns {object} The stored config.
 */
export function configure(cfg) {
  config = cfg && typeof cfg === "object" ? Object.assign({}, cfg) : {};
  return config;
}

/**
 * Current server config.
 * @returns {object} The config, or `{}` before the first fetch.
 */
export function getConfig() {
  return config ? Object.assign({}, config) : {};
}

/**
 * Fetch the server config once, lazily; every failure path resolves `{}` so
 * the GitHub handoff keeps working with no server at all.
 * @returns {Promise<object>} The config.
 */
function loadConfig() {
  if (!configPromise) {
    configPromise = fetchConfig();
  }
  return configPromise;
}

/**
 * One attempt at the config route; never rejects.
 * @returns {Promise<object>} The config, or `{}`.
 */
async function fetchConfig() {
  try {
    const response = await fetch(apiUrl(CONFIG_PATH), {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      return {};
    }
    const data = await response.json();
    if (data && typeof data === "object") {
      return configure(data);
    }
  } catch (_err) {
    // No server, no route, no network: the handoff button still works.
    return {};
  }
  return {};
}

/**
 * Open the prefilled GitHub issue in a new tab.
 * @param {object} partial Report or partial report.
 * @returns {boolean} True when the tab opened.
 */
export function openHandoff(partial) {
  const payload = reportPayload(partial);
  const href = hrefFor(payload, buildBody(payload));
  if (typeof window === "undefined") {
    return false;
  }
  return Boolean(window.open(href, "_blank", "noopener"));
}

/**
 * File the report through the server when it holds a token.
 * @param {object} partial Report or partial report.
 * @returns {Promise<object>} `{ok, url?, error?}`.
 */
export async function fileDirect(partial) {
  const payload = reportPayload(partial);
  try {
    await loadConfig();
    const response = await fetch(apiUrl(SUBMIT_PATH), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        kind: payload.kind,
        title: buildTitle(payload),
        body: buildBody(payload),
        labels: labelsFor(payload.kind),
      }),
    });
    const data = await response.json().catch(() => ({}));
    // A 200 without a URL is not a filed issue: never claim a link we do not have.
    if (!response.ok || !data || data.ok !== true || !data.url) {
      const reason = data && data.error ? data.error : "HTTP " + response.status;
      return { ok: false, error: clip(reason, MAX_FIELD) };
    }
    return { ok: true, url: data.url || "" };
  } catch (err) {
    const reason = err && err.message ? err.message : "submit failed";
    return { ok: false, error: clip(reason, MAX_FIELD) };
  }
}

/**
 * Create a labelled button and set its type and class.
 * @param {string} label Button text.
 * @param {string} className `ez-fb-*` class list.
 * @returns {HTMLButtonElement} The button.
 */
function makeButton(label, className) {
  const node = document.createElement("button");
  node.type = "button";
  node.className = className;
  node.textContent = label;
  return node;
}

/**
 * Attach the stylesheet once, with an inline fallback when the link 404s.
 * @returns {void}
 */
function ensureCss() {
  if (typeof document === "undefined" || !document.head) {
    return;
  }
  if (document.getElementById(STYLE_ID)) {
    return;
  }
  const link = document.createElement("link");
  link.id = STYLE_ID;
  link.rel = "stylesheet";
  try {
    link.href = new URL("./ez_feedback.css", import.meta.url).href;
  } catch (_err) {
    link.href = "";
  }
  link.addEventListener("error", () => {
    if (document.getElementById(STYLE_ID + "-inline")) {
      return;
    }
    const style = document.createElement("style");
    style.id = STYLE_ID + "-inline";
    style.textContent = FALLBACK_CSS;
    document.head.appendChild(style);
  });
  document.head.appendChild(link);
}

/**
 * Close and remove the dialog and its backdrop.
 * @returns {void}
 */
function closeDialog() {
  if (typeof document === "undefined") {
    return;
  }
  [DIALOG_ID, BACKDROP_ID].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.remove();
    }
  });
}

/**
 * Close the dialog on Escape.
 * @param {KeyboardEvent} event Key event.
 * @returns {void}
 */
function onDialogKeydown(event) {
  if (event.key === "Escape") {
    closeDialog();
  }
}

/**
 * Open the report dialog: editable body, primary handoff, copy, and the
 * "File directly" button only when the server reports `tokenPresent`.
 *
 * The dialog opens synchronously so a click is never blocked on the network;
 * the token-gated button is added when the lazy config resolves.
 * @param {object} partial Report or partial report.
 * @returns {boolean} True when the dialog opened.
 */
export function openReport(partial) {
  if (typeof document === "undefined") {
    return false;
  }
  const payload = reportPayload(partial);
  ensureCss();
  closeDialog();
  document.removeEventListener("keydown", onDialogKeydown);

  const backdrop = document.createElement("div");
  backdrop.id = BACKDROP_ID;
  backdrop.className = "ez-fb-backdrop";
  backdrop.addEventListener("click", closeDialog);

  const dialog = document.createElement("div");
  dialog.id = DIALOG_ID;
  dialog.className = "ez-fb-dialog";
  dialog.setAttribute("role", "dialog");
  dialog.setAttribute("aria-modal", "true");
  dialog.setAttribute("aria-label", buildTitle(payload));

  const heading = document.createElement("div");
  heading.className = "ez-fb-title";
  heading.textContent = buildTitle(payload);

  const body = document.createElement("textarea");
  body.className = "ez-fb-textarea";
  body.spellcheck = false;
  body.setAttribute("aria-label", "Issue body");
  body.value = buildBody(payload);

  const status = document.createElement("div");
  status.className = "ez-fb-status";
  status.setAttribute("role", "status");

  const footer = document.createElement("div");
  footer.className = "ez-fb-footer";

  const handoff = makeButton("Open on GitHub", "ez-fb-btn ez-fb-btn-primary");
  handoff.addEventListener("click", () => {
    const href = hrefFor(payload, body.value);
    if (typeof window !== "undefined" && window.open(href, "_blank", "noopener")) {
      closeDialog();
    }
  });

  const copy = makeButton("Copy markdown", "ez-fb-btn");
  copy.addEventListener("click", () => {
    body.select();
    const clipper = typeof navigator !== "undefined" ? navigator.clipboard : null;
    if (clipper && typeof clipper.writeText === "function") {
      clipper.writeText(body.value).then(
        () => {
          status.textContent = "Markdown copied.";
        },
        () => {
          status.textContent = "Copy blocked; the body is selected.";
        }
      );
      return;
    }
    status.textContent = "Copy blocked; the body is selected.";
  });

  const close = makeButton("Close", "ez-fb-btn ez-fb-btn-quiet");
  close.addEventListener("click", closeDialog);

  const direct = makeButton("File directly", "ez-fb-btn ez-fb-btn-direct");
  direct.hidden = true;
  direct.addEventListener("click", () => {
    direct.disabled = true;
    status.textContent = "Filing...";
    fileDirect(payload).then((result) => {
      direct.disabled = false;
      if (result && result.ok) {
        status.textContent = "Filed: " + (result.url || "ok");
        return;
      }
      status.textContent = (result && result.error) || "Filing failed.";
    });
  });

  footer.append(handoff, direct, copy, close);
  dialog.append(heading, body, status, footer);
  document.body.append(backdrop, dialog);
  document.addEventListener("keydown", onDialogKeydown);
  window.setTimeout(() => body.focus(), 0);

  loadConfig().then((cfg) => {
    const stillOpen = document.getElementById(DIALOG_ID);
    if (stillOpen && cfg && cfg.tokenPresent) {
      direct.hidden = false;
    }
  });
  return true;
}

/**
 * Report button wired to `openReport`, for any surface to drop in.
 * @param {object} partial Report or partial report.
 * @param {string} label Button text; defaults from the kind.
 * @returns {HTMLButtonElement} The button.
 */
export function button(partial, label) {
  const kind = kindKey(partial && partial.kind);
  const text = label || (kind === "enhancement" ? "Request a feature" : "Report a bug");
  const node = makeButton(text, "ez-fb-btn");
  node.setAttribute("data-ez-fb-kind", kind);
  node.addEventListener("click", () => {
    openReport(partial);
  });
  return node;
}

/**
 * Show the non-blocking, dismissible banner with a Report button.
 *
 * Additive only: it never blocks or delays a queue, and one banner element is
 * reused so repeated failures cannot stack.
 * @param {object} partial Report or partial report used by the Report button.
 * @param {object} [opts] `{message}` override for the banner line.
 * @returns {HTMLElement|null} The banner element.
 */
export function showBanner(partial, opts) {
  if (typeof document === "undefined") {
    return null;
  }
  const payload = reportPayload(partial);
  const options = opts && typeof opts === "object" ? opts : {};
  ensureCss();
  let el = document.getElementById(BANNER_ID);
  if (!el) {
    el = document.createElement("div");
    el.id = BANNER_ID;
    el.setAttribute("role", "status");
    document.body.appendChild(el);
  }
  el.className = "ez-fb-banner";
  el.innerHTML = "";
  const text = document.createElement("span");
  text.className = "ez-fb-banner-text";
  text.textContent =
    valueText(options.message) || payload.summary || "Something failed in this run.";
  const report = makeButton("Report", "ez-fb-btn ez-fb-btn-report");
  report.addEventListener("click", () => {
    openReport(partial);
  });
  const dismiss = makeButton("Dismiss", "ez-fb-btn ez-fb-btn-quiet");
  dismiss.setAttribute("data-ez-fb-dismiss", "1");
  dismiss.addEventListener("click", dismissBanner);
  el.append(text, report, dismiss);
  return el;
}

/**
 * Remove the banner.
 * @returns {void}
 */
export function dismissBanner() {
  if (typeof document === "undefined") {
    return;
  }
  const el = document.getElementById(BANNER_ID);
  if (el) {
    el.remove();
  }
}

const EZ_FEEDBACK = {
  REPO,
  MAX_HREF,
  clip,
  labelsFor,
  buildTitle,
  buildBody,
  issueHref,
  reportPayload,
  recordError,
  recentErrors,
  configure,
  getConfig,
  openHandoff,
  fileDirect,
  openReport,
  showBanner,
  dismissBanner,
  button,
};

ensureCss();

if (typeof window !== "undefined") {
  window.EzFeedback = EZ_FEEDBACK;
}

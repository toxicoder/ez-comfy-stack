/**
 * Outputs sidebar: browse media that survives stack restart.
 *
 * Adaptive explorer: width tiers (compact / cozy / wide) drive a folder rail,
 * a pinned toolbar and footer, auto-fit tiles, list columns, skeletons, and a
 * keyboard cursor. Thumbnail grid / list, multi-select, bulk delete / copy /
 * download. Comfy History is in-memory. Files on COMFY_OUTPUT_DIR persist.
 * Nodes 2.0 safe: no LiteGraph widget hooks, no canvas resize. Treat inputEl as
 * optional. Report buttons reach window.EzFeedback lazily at click time and
 * fall back to a prefilled GitHub issues tab when the ez_feedback core is not
 * loaded.
 */
import { app } from "../../scripts/app.js";

const TAB_ID = "ez-outputs";
const STYLE_ID = "ez-outputs-css";
const PREFS_VIEW = "ez-comfy.outputs.view";
const PREFS_THUMB = "ez-comfy.outputs.thumb";
const PREFS_SORT = "ez-comfy.outputs.sort";
const PREFS_KIND = "ez-comfy.outputs.kind";
const PREFS_FOLDER = "ez-comfy.outputs.folder";
const PREFS_META = "ez-comfy.outputs.meta";
const PREFS_HINT = "ez-comfy.outputs.hint";
const THUMB_MIN = 80;
const THUMB_MAX = 280;
const THUMB_DEFAULT = 128;
const SEARCH_MS = 150;
const EXECUTED_MS = 1000;
const ROOT_FOLDER = "__root__";
// Progressive page sizes: the list route caps itself, so the pane starts small
// and grows in place instead of pulling the whole tree on first paint.
const PAGE_START = 200;
const PAGE_MAX = 2000;
// Panel width tiers. The same two numbers drive the CSS @container rules.
const TIER_COZY = 380;
const TIER_WIDE = 560;
const AUTO_THUMB = { compact: 96, cozy: 128, wide: 160 };
const SIZE_STEPS = ["auto", "96", "128", "160", "220"];
const SKELETON_CARDS = 8;
const SHORTCUTS = [
  ["/", "Filter box"],
  ["Arrows", "Move cursor"],
  ["Shift + Arrows", "Extend selection"],
  ["Home / End", "First / last file"],
  ["Enter", "Open preview"],
  ["Space", "Toggle select"],
  ["Ctrl/Cmd + A", "Select all"],
  ["Delete", "Delete selected"],
  ["+ / - / 0", "Size up / down / auto"],
  ["G / L", "Grid / list"],
  ["F", "Folder list"],
  ["Esc", "Close / clear"],
  ["?", "This list"],
];
const ISSUES_URL = "https://github.com/toxicoder/ez-comfy-stack/issues/new";
const REPORT_HREF_MAX = 5500;
const REPORT_REL_CAP = 10;
const SVG_NS = "http://www.w3.org/2000/svg";
// Canonical primer/octicons mark-github-16 path, same mark the ez_feedback
// pack puts on its report buttons.
const GITHUB_MARK_PATH = "M6.766 11.328c-2.063-.25-3.516-1.734-3.516-3.656 0-.781.281-1.625.75-2.188-.203-.515-.172-1.609.063-2.062.625-.078 1.468.25 1.968.703.594-.187 1.219-.281 1.985-.281.765 0 1.39.094 1.953.265.484-.437 1.344-.765 1.969-.687.218.422.25 1.515.046 2.047.5.593.766 1.39.766 2.203 0 1.922-1.453 3.375-3.547 3.64.531.344.89 1.094.89 1.954v1.625c0 .468.391.734.86.547C13.781 14.359 16 11.53 16 8.03 16 3.61 12.406 0 7.984 0 3.563 0 0 3.61 0 8.031a7.88 7.88 0 0 0 5.172 7.422c.422.156.828-.125.828-.547v-1.25c-.219.094-.5.156-.75.156-1.031 0-1.64-.562-2.078-1.609-.172-.422-.36-.672-.719-.719-.187-.015-.25-.093-.25-.187 0-.188.313-.328.625-.328.453 0 .844.281 1.25.86.313.452.64.655 1.031.655s.641-.14 1-.5c.266-.265.47-.5.657-.656";
const KIND_LABELS = {
  image: "Still",
  video: "Video",
  audio: "Audio",
};

const FALLBACK_CSS = `
.ez-out { --ez-out-thumb: 128px; display:flex; flex-direction:column; height:100%; gap:8px; padding:8px; position:relative; box-sizing:border-box; font:12px/1.4 ui-sans-serif,system-ui,sans-serif; }
.ez-out [hidden] { display:none; }
.ez-out button { font:inherit; cursor:pointer; }
.ez-out-head { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
.ez-out-crumb { display:flex; align-items:center; gap:4px; flex:1; min-width:0; }
.ez-out-crumb-item { background:none; border:0; padding:2px 4px; text-decoration:underline; }
.ez-out-summary { color:inherit; opacity:.7; font-size:11px; }
.ez-out-toolbar { display:flex; flex-direction:column; gap:6px; }
.ez-out-row { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
.ez-out-more { display:flex; gap:6px; flex-wrap:wrap; }
.ez-out-active .ez-out-pill { display:inline-flex; gap:4px; align-items:center; border:1px solid currentColor; border-radius:999px; padding:2px 6px; background:none; }
.ez-out-body { display:flex; gap:8px; flex:1; min-height:0; }
.ez-out-tree { display:flex; flex-direction:column; gap:2px; width:9rem; flex:0 0 auto; overflow:auto; }
.ez-out-tree-item { display:flex; justify-content:space-between; gap:6px; text-align:left; }
.ez-out-scroll { flex:1; min-height:0; overflow:auto; }
.ez-out-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(var(--ez-out-thumb),1fr)); gap:8px; }
.ez-out-list { display:flex; flex-direction:column; }
.ez-out-card { display:flex; flex-direction:column; gap:4px; position:relative; }
.ez-out-thumb-wrap { position:relative; }
.ez-out-thumb { width:100%; height:auto; display:block; object-fit:cover; }
.ez-out-skeleton { display:grid; grid-template-columns:repeat(auto-fill,minmax(var(--ez-out-thumb),1fr)); gap:8px; }
.ez-out-skeleton-card { aspect-ratio:1/1; background:rgba(128,128,128,.18); border-radius:6px; }
.ez-out-bulk { display:none; gap:6px; flex-wrap:wrap; align-items:center; }
.ez-out-bulk.is-open { display:flex; }
.ez-out-status { margin:0; font-size:11px; opacity:.8; }
.ez-out-lightbox, .ez-out-help { position:absolute; inset:0; display:none; flex-direction:column; gap:8px; padding:12px; background:rgba(0,0,0,.72); }
.ez-out-lightbox.is-open, .ez-out-help.is-open { display:flex; }
.ez-out-lightbox-media { flex:1; min-height:0; display:flex; align-items:center; justify-content:center; }
.ez-out-lightbox-media img, .ez-out-lightbox-media video { max-width:100%; max-height:100%; }
.ez-out-lightbox-bar { display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
.ez-out-sr { position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); }
.ez-out-clipboard { position:absolute; left:-9999px; top:0; }
`;

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
 * Comfy /view URL for a relative output path.
 * @param {string} rel
 * @param {{preview?: string}} [extra]
 * @returns {string}
 */
function viewUrl(rel, extra) {
  const parts = String(rel || "").replace(/\\/g, "/").split("/");
  const filename = parts.pop() || "";
  const subfolder = parts.join("/");
  const query = new URLSearchParams();
  query.set("filename", filename);
  query.set("type", "output");
  query.set("subfolder", subfolder);
  if (extra && extra.preview) {
    query.set("preview", extra.preview);
  }
  return apiUrl("/view?" + query.toString());
}

/**
 * Thumbnail URL. Stills use Comfy preview=webp;80; video/audio use /view.
 * @param {string} rel
 * @param {string} kind
 * @returns {string}
 */
function thumbUrl(rel, kind) {
  if (kind === "image") {
    // Comfy /view?preview=webp;80 shrinks stills for the grid.
    return viewUrl(rel, { preview: "webp;80" });
  }
  return viewUrl(rel);
}

/**
 * Persist a localStorage string; ignore quota / private-mode failures.
 * @param {string} key
 * @param {string} value
 * @returns {void}
 */
function storePref(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch (_err) {
    /* ignore */
  }
}

/**
 * Read a localStorage string.
 * @param {string} key
 * @returns {string}
 */
function readPref(key) {
  try {
    return String(localStorage.getItem(key) || "");
  } catch (_err) {
    return "";
  }
}

/**
 * Saved view mode: grid or list.
 * @returns {string}
 */
function loadView() {
  return readPref(PREFS_VIEW) === "list" ? "list" : "grid";
}

/**
 * Saved thumbnail size in px.
 * @returns {number}
 */
function loadThumb() {
  const raw = Number(readPref(PREFS_THUMB));
  if (!Number.isFinite(raw)) {
    return THUMB_DEFAULT;
  }
  return Math.min(THUMB_MAX, Math.max(THUMB_MIN, Math.round(raw)));
}

/**
 * Saved sort token.
 * @returns {string}
 */
function loadSort() {
  const raw = readPref(PREFS_SORT);
  if (raw === "oldest" || raw === "name" || raw === "size") {
    return raw;
  }
  return "newest";
}

/**
 * Attach the Outputs stylesheet once.
 * @returns {void}
 */
function ensureCss() {
  if (document.getElementById(STYLE_ID)) {
    return;
  }
  const link = document.createElement("link");
  link.id = STYLE_ID;
  link.rel = "stylesheet";
  try {
    link.href = new URL("./ez_outputs.css", import.meta.url).href;
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
 * Human file size.
 * @param {number} bytes
 * @returns {string}
 */
function formatSize(bytes) {
  const n = Number(bytes) || 0;
  if (n < 1024) {
    return n + " B";
  }
  if (n < 1048576) {
    return (n / 1024).toFixed(1) + " KB";
  }
  if (n < 1073741824) {
    return (n / 1048576).toFixed(1) + " MB";
  }
  return (n / 1073741824).toFixed(1) + " GB";
}

/**
 * Relative or locale timestamp from a unix mtime.
 * @param {number} mtime
 * @returns {string}
 */
function formatTime(mtime) {
  const ms = Number(mtime) * 1000;
  if (!Number.isFinite(ms) || ms <= 0) {
    return "";
  }
  const delta = Date.now() - ms;
  if (delta < 60000) {
    return "just now";
  }
  if (delta < 3600000) {
    return Math.floor(delta / 60000) + "m ago";
  }
  if (delta < 86400000) {
    return Math.floor(delta / 3600000) + "h ago";
  }
  try {
    return new Date(ms).toLocaleString();
  } catch (_err) {
    return "";
  }
}

/**
 * Comfy SaveImage stem (ez_still_draft_00001_.png -> ez_still_draft).
 * @param {string} name
 * @returns {string}
 */
function prefixOf(name) {
  const match = String(name || "").match(/^(.*)_\d{3,}_/);
  return match ? match[1] : "";
}

/**
 * Parent directory of a list row.
 * @param {object} row
 * @returns {string}
 */
function parentOf(row) {
  if (row && row.parent != null && row.parent !== ".") {
    return String(row.parent);
  }
  const parts = String((row && row.rel) || "").split("/").filter(Boolean);
  if (parts.length < 2) {
    return "";
  }
  return parts.slice(0, -1).join("/");
}

/**
 * Sort rows by the saved mode.
 * @param {object[]} rows
 * @param {string} mode
 * @returns {object[]}
 */
function sortItems(rows, mode) {
  const out = rows.slice();
  out.sort((a, b) => {
    if (mode === "oldest") {
      return (a.mtime || 0) - (b.mtime || 0);
    }
    if (mode === "name") {
      return String(a.rel || "").localeCompare(String(b.rel || ""), undefined, {
        numeric: true,
        sensitivity: "base",
      });
    }
    if (mode === "size") {
      return (b.size || 0) - (a.size || 0);
    }
    return (b.mtime || 0) - (a.mtime || 0);
  });
  return out;
}

/**
 * Vue-safe widget write (Nodes 2.0). Treats inputEl as optional.
 * @param {object} node
 * @param {object|undefined} widget
 * @param {*} value
 * @returns {void}
 */
function setWidgetValue(node, widget, value) {
  if (!widget) {
    return;
  }
  const values = widget.options?.values;
  if (Array.isArray(values) && value && !values.includes(value)) {
    values.push(value);
  }
  widget.value = value;
  if (node?.widgets) {
    node.widgets_values = node.widgets.map((item) => item.value);
  }
  if (typeof widget.callback === "function") {
    widget.callback(value, app.canvas, node);
  }
  const graph = node?.graph;
  if (graph && typeof graph.setDirtyCanvas === "function") {
    graph.setDirtyCanvas(true, true);
  }
}

/**
 * Set a named widget on the first node of a given type.
 * @param {string} typeName
 * @param {string} widgetName
 * @param {string} filename
 * @returns {boolean}
 */
function setNamedWidget(typeName, widgetName, filename) {
  const nodes = app.graph?.nodes || [];
  const node = nodes.find((item) => item.type === typeName);
  if (!node?.widgets) {
    return false;
  }
  const widget = node.widgets.find((item) => item.name === widgetName);
  if (!widget) {
    return false;
  }
  setWidgetValue(node, widget, filename);
  return true;
}

/**
 * Copy dest name onto LoadImage / EZOptionalImage / LoadAudio when present.
 * @param {string} kind
 * @param {string} filename
 * @returns {boolean}
 */
function applyToGraph(kind, filename) {
  if (kind === "image") {
    if (setNamedWidget("LoadImage", "image", filename)) {
      return true;
    }
    return setNamedWidget("EZOptionalImage", "filename", filename);
  }
  if (kind === "audio") {
    return setNamedWidget("LoadAudio", "audio", filename);
  }
  return false;
}

/**
 * Fetch JSON from an ez_outputs route.
 * @param {string} path
 * @param {RequestInit} [init]
 * @returns {Promise<object>}
 */
async function fetchJson(path, init) {
  const response = await fetch(apiUrl(path), init);
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error || response.statusText);
    // Carry route + status so every catch can report them.
    error.endpoint = path;
    error.status = response.status;
    throw error;
  }
  return data;
}

/**
 * POST JSON with rel or rels.
 * @param {string} path
 * @param {object} body
 * @returns {Promise<object>}
 */
async function postJson(path, body) {
  return fetchJson(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

/**
 * Confirm a bulk (or single) delete.
 * @param {string[]} rels
 * @returns {boolean}
 */
function confirmDelete(rels) {
  const preview = rels.slice(0, 5).join("\n");
  const extra = rels.length > 5 ? "\n..." : "";
  return window.confirm("Delete " + rels.length + " file(s)?\n" + preview + extra);
}

/**
 * Trigger browser downloads for each relative path.
 * @param {string[]} rels
 * @returns {void}
 */
function downloadRels(rels) {
  rels.forEach((rel, index) => {
    window.setTimeout(() => {
      const link = document.createElement("a");
      link.href = viewUrl(rel);
      link.download = String(rel).split("/").pop() || rel;
      link.rel = "noopener";
      document.body.appendChild(link);
      link.click();
      link.remove();
    }, index * 120);
  });
}

/**
 * Build the GitHub mark shown on report buttons.
 * @returns {SVGElement} The octicon svg element.
 */
function githubIconSvg() {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", "0 0 16 16");
  svg.setAttribute("width", "14");
  svg.setAttribute("height", "14");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("class", "ez-out-icon");
  const path = document.createElementNS(SVG_NS, "path");
  path.setAttribute("fill", "currentColor");
  path.setAttribute("d", GITHUB_MARK_PATH);
  svg.appendChild(path);
  return svg;
}

/**
 * Create a button.
 * @param {string} label
 * @param {string} className
 * @param {function(Event=): void} onClick
 * @param {{icon?: boolean}=} opts icon prepends the GitHub mark
 * @returns {HTMLButtonElement}
 */
function makeButton(label, className, onClick, opts) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.className = className;
  button.addEventListener("click", onClick);
  if (opts && opts.icon) {
    button.insertBefore(document.createTextNode(" "), button.firstChild);
    button.insertBefore(githubIconSvg(), button.firstChild);
  }
  return button;
}

/**
 * Collapse whitespace and cap text so a handoff URL stays openable.
 * @param {*} value
 * @param {number} max
 * @returns {string}
 */
function clipText(value, max) {
  const text = String(value == null ? "" : value).replace(/\s+/g, " ").trim();
  if (text.length <= max) {
    return text;
  }
  if (max < 2) {
    return "";
  }
  return text.slice(0, max - 1) + "...";
}

/**
 * Reach the ez_feedback core lazily so extension load order cannot break us.
 * @param {string} method Member the caller needs, e.g. "openReport"
 * @returns {object|null} The core, or null when it is absent or too old
 */
function feedbackCore(method) {
  const fb = window.EzFeedback;
  if (!fb || typeof fb[method] !== "function") {
    return null;
  }
  return fb;
}

/**
 * Prefilled /issues/new URL for the no-core fallback (same builder shape the
 * core uses: title prefix is the bare surface id, context is `- label: value`).
 * @param {object} report {kind, surface, summary, context}
 * @returns {string}
 */
function issuesHandoffUrl(report) {
  const area = report.surface || "global";
  const isFeature = report.kind === "enhancement";
  const title = clipText(
    "[" +
      area +
      "] " +
      (report.summary || (isFeature ? "Feature request from " : "Bug report from ") + area),
    140,
  );
  const pairs = Array.isArray(report.context) ? report.context : [];
  const head = [
    "Reported from the Outputs sidebar. Edit the blanks, then submit.",
    "",
    "## What happened",
    "<!-- Replace this line. -->",
    "",
    "## Context",
  ];
  const tail = ["", "## Browser", "- ua: " + clipText(navigator.userAgent, 160)];
  const build = (keepBrowser, contextLimit) => {
    const lines = head.slice();
    pairs.slice(0, contextLimit).forEach((pair) => {
      lines.push("- " + pair[0] + ": " + clipText(pair[1], 200));
    });
    if (keepBrowser) {
      lines.push.apply(lines, tail);
    }
    const query = new URLSearchParams();
    query.set("title", title);
    query.set("labels", isFeature ? "enhancement" : "bug");
    query.set("body", lines.join("\n"));
    return ISSUES_URL + "?" + query.toString();
  };
  let href = build(true, pairs.length);
  if (href.length > REPORT_HREF_MAX) {
    href = build(false, pairs.length);
  }
  if (href.length > REPORT_HREF_MAX) {
    href = build(false, 5);
  }
  return href;
}

/**
 * Open the core report dialog, falling back to the prefilled issues tab.
 * @param {object} report {kind, surface, summary, context}
 * @returns {void}
 */
function openFeedbackReport(report) {
  const fb = feedbackCore("openReport");
  if (fb) {
    try {
      fb.openReport(report);
      return;
    } catch (_err) {
      /* fall through to the handoff */
    }
  }
  try {
    window.open(issuesHandoffUrl(report), "_blank", "noopener");
  } catch (_err) {
    /* a blocked pop-up must never break the explorer */
  }
}

/**
 * Compact one-line summary of route-level per-file rejections.
 * @param {object[]} errors Rows from the route, shape {rel, error}
 * @returns {string}
 */
function errorDetail(errors) {
  const rows = Array.isArray(errors) ? errors : [];
  return rows
    .slice(0, 5)
    .map((row) => String((row && row.rel) || "?") + ": " + String((row && row.error) || "failed"))
    .join(" | ");
}

/**
 * Push one caught failure into the core ring buffer; never throws.
 * @param {string} surface
 * @param {string} message
 * @param {string} detail
 * @returns {void}
 */
function recordFeedbackError(surface, message, detail) {
  const fb = feedbackCore("recordError");
  if (!fb) {
    return;
  }
  try {
    fb.recordError({
      ts: new Date().toISOString(),
      surface,
      message: clipText(message, 200),
      detail: clipText(detail, 500),
    });
  } catch (_err) {
    /* error capture is additive */
  }
}

/**
 * Name the layout tier for a measured panel width.
 * @param {number} width Panel inline size in px
 * @returns {string} "compact" | "cozy" | "wide"
 */
function tierFor(width) {
  const px = Number(width) || 0;
  if (px < TIER_COZY) {
    return "compact";
  }
  return px >= TIER_WIDE ? "wide" : "cozy";
}

/**
 * Whether the visitor asked the OS to cut animation.
 * @returns {boolean} True when motion should stay off
 */
function prefersReducedMotion() {
  if (typeof window.matchMedia !== "function") {
    return false;
  }
  try {
    return Boolean(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  } catch (_err) {
    return false;
  }
}

/**
 * Read a stored on/off preference.
 * @param {string} key localStorage key
 * @param {boolean} fallback Value to use when nothing is stored
 * @returns {boolean} The stored flag
 */
function readBoolPref(key, fallback) {
  const raw = readPref(key);
  if (raw === "on") {
    return true;
  }
  if (raw === "off") {
    return false;
  }
  return fallback;
}

/**
 * Human label for the density control.
 * @param {boolean} auto True when width picks the size
 * @param {number} px Effective thumbnail size
 * @returns {string} Label text for the Size button
 */
function sizeLabelFor(auto, px) {
  return "Size: " + (auto ? "Auto " + px : String(px));
}

/**
 * Build the loading pane shown while a list call is in flight.
 * @param {number} count Number of placeholder cards
 * @returns {HTMLElement} Skeleton pane element
 */
function skeletonPane(count) {
  const wrap = document.createElement("div");
  wrap.className = "ez-out-skeleton";
  const total = Math.max(1, Number(count) || SKELETON_CARDS);
  for (let i = 0; i < total; i += 1) {
    const card = document.createElement("div");
    card.className = "ez-out-skeleton-card";
    card.setAttribute("aria-hidden", "true");
    wrap.appendChild(card);
  }
  return wrap;
}

/**
 * Render the sidebar into el.
 * @param {HTMLElement} el
 * @returns {void}
 */
function mount(el) {
  ensureCss();
  el.replaceChildren();
  el.classList.add("ez-out");
  el.tabIndex = 0;

  const storedKind = readPref(PREFS_KIND);
  /** @type {string} */
  let kind =
    storedKind === "image" || storedKind === "video" || storedKind === "audio"
      ? storedKind
      : "all";
  /** @type {string} */
  let query = "";
  /** @type {string} */
  let view = loadView();
  /** @type {number} */
  let thumbSize = THUMB_DEFAULT;
  /** @type {string} */
  let sortMode = loadSort();
  /** @type {string} */
  let folder = readPref(PREFS_FOLDER) || "";
  /** @type {string} */
  let prefix = "";
  /** @type {object[]} */
  let items = [];
  /** @type {Set<string>} */
  let selected = new Set();
  /** @type {string} */
  let anchorRel = "";
  /** @type {string} */
  let highlightRel = "";
  /** @type {boolean} */
  let truncated = false;
  /** @type {string} */
  let lightboxRel = "";
  /** @type {number} */
  let searchTimer = 0;
  /** @type {number} */
  let execTimer = 0;
  /** @type {IntersectionObserver|null} */
  let lazyVideo = null;
  /** Width tier name, kept in sync with the CSS container rules. */
  /** @type {string} */
  let tier = tierFor(el.clientWidth || el.offsetWidth || 0);
  /** @type {boolean} */
  let autoSize = true;
  /** @type {boolean} */
  let loading = false;
  /** @type {boolean} */
  let failed = false;
  /** @type {number} */
  let pageSize = PAGE_START;
  /** @type {boolean} */
  let metaOn = readBoolPref(PREFS_META, true);
  /** @type {boolean} */
  let helpOpen = false;
  /** @type {boolean} */
  let moreOpen = false;
  /** @type {boolean} */
  let showHint = readBoolPref(PREFS_HINT, true);
  /** @type {string} */
  let lastFocusRel = "";
  /** @type {HTMLElement|null} */
  let lightboxReturn = null;

  // Auto is the default; only an explicit stored number pins a fixed size.
  const storedThumb = readPref(PREFS_THUMB);
  if (storedThumb !== "" && storedThumb !== "auto") {
    autoSize = false;
    thumbSize = loadThumb();
  }

  /**
   * Effective thumbnail size for the current tier and density mode.
   * @returns {number} Pixels per tile edge
   */
  function effectiveThumb() {
    if (!autoSize) {
      return thumbSize;
    }
    return AUTO_THUMB[tier] || THUMB_DEFAULT;
  }

  /**
   * Push the density choice into the sheet variable and the control label.
   * @returns {void}
   */
  function applyThumb() {
    const px = effectiveThumb();
    el.style.setProperty("--ez-out-thumb", px + "px");
    sizeLabel.textContent = sizeLabelFor(autoSize, px);
    sizeInput.value = String(px);
    sizeInput.disabled = view === "list";
    gridBtn.classList.toggle("is-active", view === "grid");
    listBtn.classList.toggle("is-active", view === "list");
    sizeBtn.textContent = sizeLabelFor(autoSize, px);
  }

  /**
   * Publish the measured width tier so CSS and JS agree on one layout.
   * @returns {void}
   */
  function applyTier() {
    const next = tierFor(el.clientWidth || el.offsetWidth || 0);
    if (next !== tier) {
      tier = next;
      el.dataset.tier = tier;
      if (autoSize) {
        applyThumb();
      }
    }
  }

  el.dataset.tier = tier;

  const hint = document.createElement("p");
  hint.className = "ez-out-hint";
  hint.textContent =
    "Files on the output disk survive restart. History does not.";
  const hintClose = makeButton("Dismiss", "ez-out-btn", () => {
    showHint = false;
    storePref(PREFS_HINT, "off");
    hint.classList.remove("is-open");
    hint.setAttribute("hidden", "");
    renderStatus();
  });
  hint.appendChild(document.createTextNode(" "));
  hint.appendChild(hintClose);
  if (!showHint) {
    hint.classList.remove("is-open");
    hint.setAttribute("hidden", "");
  } else {
    hint.classList.add("is-open");
  }

  const kindRow = document.createElement("div");
  kindRow.className = "ez-out-row";
  const kinds = [
    ["all", "All"],
    ["image", "Stills"],
    ["video", "Video"],
    ["audio", "Audio"],
  ];
  const kindButtons = kinds.map(([id, label]) => {
    const button = makeButton(label, "ez-out-chip", () => {
      kind = id;
      storePref(PREFS_KIND, kind);
      pageSize = PAGE_START;
      refresh();
    });
    button.dataset.kind = id;
    button.setAttribute("aria-pressed", kind === id ? "true" : "false");
    kindRow.appendChild(button);
    return button;
  });

  const search = document.createElement("input");
  search.type = "search";
  search.className = "ez-out-search";
  search.placeholder = "Filter files (type to search)";
  search.setAttribute("aria-label", "Filter files by name or folder");
  search.value = "";
  search.addEventListener("input", () => {
    query = search.value || "";
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => {
      pageSize = PAGE_START;
      refresh();
    }, SEARCH_MS);
  });
  kindRow.appendChild(search);

  const refreshBtn = makeButton("Refresh", "ez-out-btn", () => {
    refresh();
  });
  kindRow.appendChild(refreshBtn);

  const reportBtn = makeButton("Report a problem", "ez-out-btn", () => {
    openFeedbackReport(explorerReport("bug"));
  }, { icon: true });
  reportBtn.title = "Open a prefilled GitHub issue for this explorer state";
  reportBtn.setAttribute("aria-label", "Report a problem on GitHub");
  kindRow.appendChild(reportBtn);

  const featureBtn = makeButton("Suggest a feature", "ez-out-btn", () => {
    openFeedbackReport(explorerReport("enhancement"));
  }, { icon: true });
  featureBtn.title = "Open a prefilled GitHub feature request for this explorer";
  featureBtn.setAttribute("aria-label", "Suggest a feature on GitHub");
  kindRow.appendChild(featureBtn);

  const viewRow = document.createElement("div");
  viewRow.className = "ez-out-row";
  viewRow.setAttribute("role", "toolbar");
  viewRow.setAttribute("aria-label", "View, density, and sort");
  const gridBtn = makeButton("Grid", "ez-out-btn", () => {
    setView("grid");
  });
  const listBtn = makeButton("List", "ez-out-btn", () => {
    setView("list");
  });
  const sizeLabel = document.createElement("span");
  sizeLabel.className = "ez-out-size-label";
  sizeLabel.textContent = "Size";
  const sizeBtn = makeButton("Size: Auto", "ez-out-btn", () => {
    cycleSize();
  });
  sizeBtn.title = "Cycle thumbnail size, or press 0 for auto";
  const sizeInput = document.createElement("input");
  sizeInput.type = "range";
  sizeInput.className = "ez-out-range";
  sizeInput.min = String(THUMB_MIN);
  sizeInput.max = String(THUMB_MAX);
  sizeInput.step = "8";
  sizeInput.value = String(thumbSize);
  sizeInput.title = "Thumbnail size";
  sizeInput.setAttribute("aria-label", "Thumbnail size in pixels");
  sizeInput.addEventListener("input", () => {
    autoSize = false;
    thumbSize = Number(sizeInput.value) || THUMB_DEFAULT;
    storePref(PREFS_THUMB, String(thumbSize));
    applyThumb();
  });
  const sortSelect = document.createElement("select");
  sortSelect.className = "ez-out-select";
  sortSelect.setAttribute("aria-label", "Sort files by");
  [
    ["newest", "Newest"],
    ["oldest", "Oldest"],
    ["name", "Name"],
    ["size", "Size"],
  ].forEach(([id, label]) => {
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = label;
    sortSelect.appendChild(opt);
  });
  sortSelect.value = sortMode;
  sortSelect.addEventListener("change", () => {
    sortMode = sortSelect.value || "newest";
    storePref(PREFS_SORT, sortMode);
    paint();
  });
  const selectAllBtn = makeButton("Select all", "ez-out-btn", () => {
    selectAllVisible();
  });
  const moreBtn = makeButton("More", "ez-out-btn ez-out-more-btn", () => {
    moreOpen = !moreOpen;
    moreBtn.setAttribute("aria-expanded", moreOpen ? "true" : "false");
    more.classList.toggle("is-open", moreOpen);
    if (moreOpen) {
      more.removeAttribute("hidden");
    } else {
      more.setAttribute("hidden", "");
    }
  });
  moreBtn.setAttribute("aria-expanded", "false");
  moreBtn.title = "Density, metadata, and view reset";
  viewRow.appendChild(gridBtn);
  viewRow.appendChild(listBtn);
  viewRow.appendChild(sizeBtn);
  viewRow.appendChild(sizeLabel);
  viewRow.appendChild(sizeInput);
  viewRow.appendChild(sortSelect);
  viewRow.appendChild(selectAllBtn);
  viewRow.appendChild(moreBtn);

  const more = document.createElement("div");
  more.className = "ez-out-more";
  more.setAttribute("hidden", "");
  const metaBtn = makeButton("Show details", "ez-out-btn", () => {
    metaOn = !metaOn;
    storePref(PREFS_META, metaOn ? "on" : "off");
    metaBtn.setAttribute("aria-pressed", metaOn ? "true" : "false");
    paint();
  });
  metaBtn.setAttribute("aria-pressed", metaOn ? "true" : "false");
  more.appendChild(metaBtn);
  more.appendChild(
    makeButton("Reset view", "ez-out-btn", () => {
      autoSize = true;
      storePref(PREFS_THUMB, "auto");
      kind = "all";
      storePref(PREFS_KIND, kind);
      query = "";
      search.value = "";
      folder = "";
      storePref(PREFS_FOLDER, "");
      prefix = "";
      pageSize = PAGE_START;
      applyThumb();
      refresh();
    }),
  );
  more.appendChild(
    makeButton("Show intro", "ez-out-btn", () => {
      showHint = true;
      storePref(PREFS_HINT, "on");
      hint.removeAttribute("hidden");
      hint.classList.add("is-open");
    }),
  );

  const head = document.createElement("div");
  head.className = "ez-out-head";
  const crumb = document.createElement("nav");
  crumb.className = "ez-out-crumb";
  crumb.setAttribute("aria-label", "Output folder path");
  const summary = document.createElement("span");
  summary.className = "ez-out-summary";
  const helpBtn = makeButton("Shortcuts", "ez-out-btn ez-out-help-btn", () => {
    toggleHelp();
  });
  helpBtn.setAttribute("aria-expanded", "false");
  helpBtn.title = "Keyboard shortcuts";
  head.appendChild(crumb);
  head.appendChild(summary);
  head.appendChild(helpBtn);

  const active = document.createElement("div");
  active.className = "ez-out-row ez-out-active";
  active.setAttribute("hidden", "");
  const clearBtn = makeButton("Clear filters", "ez-out-btn ez-out-clear", () => {
    clearFilters();
  });

  const tree = document.createElement("aside");
  tree.className = "ez-out-tree";
  tree.setAttribute("aria-label", "Folders");

  const bodyRow = document.createElement("div");
  bodyRow.className = "ez-out-body";

  const folderRow = document.createElement("div");
  folderRow.className = "ez-out-row ez-out-chips";
  const prefixRow = document.createElement("div");
  prefixRow.className = "ez-out-row ez-out-chips";

  const bulk = document.createElement("div");
  bulk.className = "ez-out-bulk";
  const bulkCount = document.createElement("span");
  bulkCount.className = "ez-out-bulk-count";
  bulk.appendChild(bulkCount);
  bulk.appendChild(
    makeButton("Select none", "ez-out-btn", () => {
      selected = new Set();
      paintSelection();
    }),
  );
  bulk.appendChild(
    makeButton("Delete", "ez-out-btn", () => {
      deleteRels([...selected]);
    }),
  );
  bulk.appendChild(
    makeButton("Copy to input", "ez-out-btn", () => {
      copyRels([...selected]);
    }),
  );
  bulk.appendChild(
    makeButton("Download", "ez-out-btn", () => {
      downloadRels([...selected]);
    }),
  );
  bulk.appendChild(
    makeButton("Copy paths", "ez-out-btn", () => {
      copyPaths([...selected]);
    }),
  );

  const scroll = document.createElement("div");
  scroll.className = "ez-out-scroll";
  scroll.setAttribute("tabindex", "-1");

  const paneLabel = document.createElement("div");
  paneLabel.className = "ez-out-sr";

  const status = document.createElement("p");
  status.className = "ez-out-status";
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");

  const loadMoreBtn = makeButton("Load more", "ez-out-btn ez-out-load-more", () => {
    loadMore();
  });
  loadMoreBtn.setAttribute("hidden", "");

  const listhead = document.createElement("div");
  listhead.className = "ez-out-listhead";
  listhead.setAttribute("hidden", "");
  [
    ["name", "Name"],
    ["size", "Size"],
    ["newest", "Modified"],
  ].forEach(([key, label]) => {
    const col = makeButton(label, "ez-out-col", () => {
      sortMode = key === "newest" ? (sortMode === "newest" ? "oldest" : "newest") : key;
      sortSelect.value = sortMode;
      storePref(PREFS_SORT, sortMode);
      paint();
    });
    col.dataset.sort = key;
    listhead.appendChild(col);
  });

  const lightbox = document.createElement("div");
  lightbox.className = "ez-out-lightbox";
  lightbox.setAttribute("role", "dialog");
  lightbox.setAttribute("aria-modal", "true");
  lightbox.setAttribute("aria-label", "File preview");
  lightbox.setAttribute("hidden", "");

  const help = document.createElement("div");
  help.className = "ez-out-help";
  help.tabIndex = -1;
  help.setAttribute("role", "dialog");
  help.setAttribute("aria-modal", "true");
  help.setAttribute("aria-label", "Keyboard shortcuts");
  help.setAttribute("hidden", "");
  const helpTitle = document.createElement("p");
  helpTitle.className = "ez-out-help-title";
  helpTitle.textContent = "Explorer shortcuts";
  help.appendChild(helpTitle);
  const helpList = document.createElement("div");
  helpList.className = "ez-out-help-list";
  SHORTCUTS.forEach((pair) => {
    const line = document.createElement("div");
    line.className = "ez-out-help-row";
    const kbd = document.createElement("kbd");
    kbd.className = "ez-out-kbd";
    kbd.textContent = pair[0];
    const what = document.createElement("span");
    what.className = "ez-out-help-what";
    what.textContent = pair[1];
    line.appendChild(kbd);
    line.appendChild(what);
    helpList.appendChild(line);
  });
  help.appendChild(helpList);
  help.appendChild(
    makeButton("Done", "ez-out-btn", () => {
      toggleHelp(false);
    }),
  );

  const clipboard = document.createElement("textarea");
  clipboard.className = "ez-out-clipboard";
  clipboard.setAttribute("aria-hidden", "true");
  clipboard.setAttribute("tabindex", "-1");

  /**
   * Switch grid vs list and persist.
   * @param {string} next
   * @returns {void}
   */
  function setView(next) {
    view = next === "list" ? "list" : "grid";
    storePref(PREFS_VIEW, view);
    applyThumb();
    paint();
  }

  /**
   * Step the density control through auto and the fixed sizes.
   * @returns {void}
   */
  function cycleSize() {
    const current = autoSize ? "auto" : String(thumbSize);
    const at = SIZE_STEPS.indexOf(current);
    const next = SIZE_STEPS[(at + 1 + SIZE_STEPS.length) % SIZE_STEPS.length];
    if (next === "auto") {
      autoSize = true;
      storePref(PREFS_THUMB, "auto");
    } else {
      autoSize = false;
      thumbSize = Number(next) || THUMB_DEFAULT;
      storePref(PREFS_THUMB, String(thumbSize));
    }
    applyThumb();
    announce("Thumbnail size " + next);
  }

  /**
   * Resize the tile grid by a fixed step, leaving auto mode.
   * @param {number} delta Pixels to add to the tile edge
   * @returns {void}
   */
  function nudgeSize(delta) {
    // Step from what the user actually sees, not the stored default.
    const base = autoSize ? effectiveThumb() : thumbSize;
    autoSize = false;
    thumbSize = Math.min(THUMB_MAX, Math.max(THUMB_MIN, base + delta));
    storePref(PREFS_THUMB, String(thumbSize));
    applyThumb();
  }

  /**
   * Open or close the shortcut sheet.
   * @param {boolean=} force True opens, false closes, omitted toggles
   * @returns {void}
   */
  function toggleHelp(force) {
    helpOpen = force === undefined ? !helpOpen : Boolean(force);
    help.classList.toggle("is-open", helpOpen);
    helpBtn.setAttribute("aria-expanded", helpOpen ? "true" : "false");
    if (helpOpen) {
      help.removeAttribute("hidden");
      help.focus();
    } else {
      help.setAttribute("hidden", "");
      el.focus();
    }
  }

  /**
   * Drop every active filter and reload.
   * @returns {void}
   */
  function clearFilters() {
    kind = "all";
    storePref(PREFS_KIND, kind);
    folder = "";
    storePref(PREFS_FOLDER, "");
    prefix = "";
    query = "";
    search.value = "";
    pageSize = PAGE_START;
    refresh();
  }

  /**
   * Ask the list route for a bigger page without resetting the pane.
   * @returns {void}
   */
  function loadMore() {
    if (pageSize >= PAGE_MAX) {
      announce("Everything loaded");
      return;
    }
    pageSize = Math.min(PAGE_MAX, pageSize * 2);
    refresh();
  }

  /**
   * Write a line into the live status region with a tone class.
   * @param {string} text Message to announce
   * @param {string=} tone "ok", "warn", or "bad"
   * @returns {void}
   */
  function announce(text, tone) {
    status.textContent = text;
    status.classList.toggle("is-ok", tone === "ok");
    status.classList.toggle("is-warn", tone === "warn");
    status.classList.toggle("is-bad", tone === "bad");
  }

  /**
   * Folder rail with per-folder counts, driven by the loaded page.
   * @returns {void}
   */
  function paintTree() {
    tree.replaceChildren();
    /** @type {Map<string, number>} */
    const counts = new Map();
    let rootCount = 0;
    items.forEach((row) => {
      const parent = parentOf(row);
      if (parent) {
        counts.set(parent, (counts.get(parent) || 0) + 1);
      } else {
        rootCount += 1;
      }
    });
    /**
     * One rail entry.
     * @param {string} label Shown name
     * @param {string} token Folder value to select
     * @param {number} count Files in that folder
     * @returns {HTMLButtonElement} The rail button
     */
    const row = (label, token, count) => {
      const button = makeButton(label, "ez-out-tree-item", () => {
        folder = token;
        storePref(PREFS_FOLDER, token);
        highlightRel = "";
        paint();
      });
      button.textContent = "";
      const name = document.createElement("span");
      name.className = "ez-out-tree-label";
      name.textContent = label;
      button.appendChild(name);
      const badge = document.createElement("span");
      badge.className = "ez-out-tree-count";
      badge.textContent = String(count);
      button.appendChild(badge);
      button.setAttribute("aria-current", folder === token ? "true" : "false");
      return button;
    };
    tree.appendChild(row("All files", "", items.length));
    if (rootCount) {
      tree.appendChild(row("root", ROOT_FOLDER, rootCount));
    }
    [...counts.keys()].sort().forEach((name) => {
      tree.appendChild(row(name, name, counts.get(name) || 0));
    });
  }

  /**
   * Breadcrumb above the pane: all files then the folder path.
   * @returns {void}
   */
  function paintCrumb() {
    crumb.replaceChildren();
    const rootBtn = makeButton("All files", "ez-out-crumb-item", () => {
      folder = "";
      storePref(PREFS_FOLDER, "");
      paint();
    });
    rootBtn.setAttribute("aria-current", folder === "" ? "page" : "false");
    crumb.appendChild(rootBtn);
    const parts = folder && folder !== ROOT_FOLDER ? folder.split("/") : [];
    if (folder === ROOT_FOLDER) {
      parts.push("root");
    }
    let walk = "";
    parts.forEach((part, index) => {
      const sep = document.createElement("span");
      sep.className = "ez-out-crumb-sep";
      sep.setAttribute("aria-hidden", "true");
      sep.textContent = "/";
      crumb.appendChild(sep);
      walk = index === 0 ? part : walk + "/" + part;
      const token = folder === ROOT_FOLDER && index === parts.length - 1
        ? ROOT_FOLDER
        : walk;
      const last = index === parts.length - 1;
      const crumbBtn = makeButton(part, "ez-out-crumb-item", () => {
        folder = token;
        storePref(PREFS_FOLDER, token);
        paint();
      });
      crumbBtn.setAttribute("aria-current", last ? "page" : "false");
      crumb.appendChild(crumbBtn);
    });
  }

  /**
   * Removable pills for every filter that is on.
   * @returns {void}
   */
  function paintActive() {
    active.replaceChildren();
    /** @type {Array<Array<any>>} */
    const pills = [];
    if (kind !== "all") {
      pills.push([
        "Type: " + (KIND_LABELS[kind] || kind),
        () => {
          kind = "all";
          storePref(PREFS_KIND, kind);
          pageSize = PAGE_START;
          refresh();
        },
      ]);
    }
    if (folder) {
      pills.push([
        "Folder: " + folderToken(),
        () => {
          folder = "";
          storePref(PREFS_FOLDER, "");
          paint();
        },
      ]);
    }
    if (prefix) {
      pills.push([
        "Prefix: " + prefix,
        () => {
          prefix = "";
          paint();
        },
      ]);
    }
    if (query) {
      pills.push([
        "Search: " + query,
        () => {
          query = "";
          search.value = "";
          pageSize = PAGE_START;
          refresh();
        },
      ]);
    }
    if (!pills.length) {
      active.setAttribute("hidden", "");
      active.classList.remove("is-open");
      return;
    }
    active.removeAttribute("hidden");
    active.classList.add("is-open");
    pills.forEach((pill) => {
      const node = document.createElement("button");
      node.type = "button";
      node.className = "ez-out-pill";
      node.setAttribute("aria-label", "Remove filter " + pill[0]);
      const label = document.createElement("span");
      label.className = "ez-out-pill-label";
      label.textContent = pill[0];
      const mark = document.createElement("span");
      mark.className = "ez-out-pill-x";
      mark.setAttribute("aria-hidden", "true");
      mark.textContent = "x";
      node.appendChild(label);
      node.appendChild(mark);
      node.addEventListener("click", pill[1]);
      active.appendChild(node);
    });
    active.appendChild(clearBtn);
  }

  /**
   * Give the highlighted card the only tab stop in the pane.
   * @returns {void}
   */
  function paintRovingFocus() {
    const nodes = scroll.querySelectorAll("[data-rel]");
    let found = false;
    nodes.forEach((node) => {
      const rel = node.getAttribute("data-rel") || "";
      const on = Boolean(rel) && rel === highlightRel;
      node.tabIndex = on ? 0 : -1;
      node.classList.toggle("is-focus", on);
      if (on) {
        found = true;
      }
    });
    if (!found && nodes.length) {
      const first = nodes[0];
      first.tabIndex = 0;
      highlightRel = first.getAttribute("data-rel") || "";
      first.classList.add("is-focus");
    }
  }

  /**
   * Move the keyboard cursor to a rel and repaint the cursor only.
   * @param {string} rel Row to highlight
   * @returns {void}
   */
  function focusRel(rel) {
    highlightRel = rel;
    anchorRel = rel;
    paintSelection();
    paintRovingFocus();
    const node = scroll.querySelector("[data-rel=\"" + rel + "\"]");
    if (node && typeof node.focus === "function") {
      node.focus();
    }
  }

  /**
   * Rows after folder / prefix filters, sorted.
   * @returns {object[]}
   */
  function visibleItems() {
    let out = items.slice();
    if (folder === ROOT_FOLDER) {
      out = out.filter((row) => !parentOf(row));
    } else if (folder) {
      out = out.filter((row) => parentOf(row) === folder);
    }
    if (prefix) {
      out = out.filter((row) => prefixOf(row.name) === prefix);
    }
    return sortItems(out, sortMode);
  }

  /**
   * Apply exclusive / toggle / shift-click range selection.
   * @param {string} rel
   * @param {MouseEvent} event
   * @returns {void}
   */
  function applyClickSelect(rel, event) {
    if (event.shiftKey) {
      extendTo(rel);
      return;
    }
    if (event.metaKey || event.ctrlKey) {
      if (selected.has(rel)) {
        selected.delete(rel);
      } else {
        selected.add(rel);
      }
      anchorRel = rel;
      highlightRel = rel;
      paintSelection();
      return;
    }
    selected = new Set([rel]);
    anchorRel = rel;
    highlightRel = rel;
    paintSelection();
  }

  /**
   * Select every visible row.
   * @returns {void}
   */
  function selectAllVisible() {
    selected = new Set(visibleItems().map((row) => row.rel));
    paintSelection();
  }

  /**
   * Update aria-selected / checkboxes / bulk bar without rebuilding cards.
   * @returns {void}
   */
  function paintSelection() {
    scroll.querySelectorAll("[data-rel]").forEach((node) => {
      const rel = node.getAttribute("data-rel") || "";
      const on = selected.has(rel);
      node.setAttribute("aria-selected", on ? "true" : "false");
      node.classList.toggle("is-highlight", rel === highlightRel);
      const box = node.querySelector("input[type=\"checkbox\"]");
      if (box) {
        box.checked = on;
      }
    });
    const n = selected.size;
    bulk.classList.toggle("is-open", n > 0);
    bulk.setAttribute("aria-hidden", n > 0 ? "false" : "true");
    bulkCount.textContent = n === 1 ? "1 file selected" : n + " files selected";
    renderStatus();
    paintRovingFocus();
  }

  /**
   * Status line: counts, selection, bytes, and the page cap.
   * @returns {void}
   */
  function renderStatus() {
    const vis = visibleItems();
    const chosen = vis.filter((row) => selected.has(row.rel));
    const pool = chosen.length ? chosen : vis;
    const bytes = pool.reduce((sum, row) => sum + (Number(row.size) || 0), 0);
    let text = vis.length + " files";
    if (truncated) {
      text = "Showing " + items.length + " of more files";
    }
    if (selected.size) {
      text += " - " + selected.size + " selected";
    }
    text += " - " + formatSize(bytes);
    if (loading) {
      text += " - loading";
    }
    status.textContent = text;
    summary.textContent = truncated
      ? "Showing " + items.length + ", page size " + pageSize
      : items.length + " loaded";
    paneLabel.textContent =
      view === "list" ? "File list, " + vis.length + " rows" : "File grid, " + vis.length + " tiles";
  }

  /**
   * Folder filter as a relative label; never an absolute host path.
   * @returns {string}
   */
  function folderToken() {
    if (folder === ROOT_FOLDER) {
      return "root";
    }
    return folder || "all";
  }

  /**
   * Context pairs that describe the explorer as filed: every filter plus the
   * list shape and up to REPORT_REL_CAP selected rels.
   * @returns {Array<Array<string>>}
   */
  function explorerContext() {
    const vis = visibleItems();
    const chosen = [...selected].slice(0, REPORT_REL_CAP);
    if (selected.size > chosen.length) {
      chosen.push("... " + (selected.size - chosen.length) + " more");
    }
    return [
      ["folder", folderToken()],
      ["prefix", prefix || "-"],
      ["kind", kind],
      ["search", query || "-"],
      ["view", view],
      ["sort", sortMode],
      ["items", String(vis.length)],
      ["loaded", String(items.length)],
      ["truncated", truncated ? "yes - page " + pageSize : "no"],
      ["selected", chosen.length ? chosen.join(", ") : "-"],
    ];
  }

  /**
   * Prefilled report for the toolbar: kind/surface/summary/context only.
   * @param {string} reportKind "bug" or "enhancement"
   * @returns {object}
   */
  function explorerReport(reportKind) {
    const isFeature = reportKind === "enhancement";
    const vis = visibleItems();
    return {
      kind: isFeature ? "enhancement" : "bug",
      surface: "media-explorer",
      summary: clipText(
        "Outputs " +
          (isFeature ? "feature request" : "problem") +
          " - folder " +
          folderToken() +
          ", kind " +
          kind +
          ", " +
          vis.length +
          " files",
        120,
      ),
      context: explorerContext(),
    };
  }

  /**
   * Context pairs for one file: only the relative fields the catalog returns.
   * @param {object} row
   * @returns {Array<Array<string>>}
   */
  function fileContext(row) {
    const item = row || {};
    return [
      ["rel", String(item.rel || "")],
      ["kind", String(item.kind || "")],
      ["size", String(item.size == null ? "" : item.size)],
      ["mtime", String(item.mtime == null ? "" : item.mtime)],
      ["suffix", String(item.suffix || "")],
      ["parent", String(item.parent == null ? parentOf(item) : item.parent)],
    ];
  }

  /**
   * Record a caught route failure with endpoint, status, and active filters.
   * @param {string} endpoint Route that failed
   * @param {object} err Caught error, maybe carrying status/endpoint
   * @param {string} message Human summary
   * @returns {void}
   */
  function noteFailure(endpoint, err, message) {
    const httpStatus = err && err.status != null ? String(err.status) : "n/a";
    recordFeedbackError(
      "media-explorer",
      message,
      [
        "endpoint=" + endpoint,
        "status=" + httpStatus,
        "folder=" + folderToken(),
        "prefix=" + (prefix || "-"),
        "kind=" + kind,
        "query=" + (query || "-"),
        "loaded=" + items.length,
      ].join(" "),
    );
  }

  /**
   * Report button for the failure pane: one click from a broken list to an issue.
   * @param {string} endpoint Route that failed
   * @param {string} message Human summary
   * @param {string} httpStatus Status text, or "n/a"
   * @returns {HTMLButtonElement}
   */
  function failReportButton(endpoint, message, httpStatus) {
    const button = makeButton("Report this problem", "ez-out-btn", () => {
      openFeedbackReport({
        kind: "bug",
        surface: "media-explorer",
        summary: clipText("Outputs " + endpoint + " failed: " + message, 120),
        context: explorerContext().concat([
          ["endpoint", endpoint],
          ["status", httpStatus],
          ["error", message],
        ]),
      });
    }, { icon: true });
    button.setAttribute("aria-label", "Report this problem on GitHub");
    return button;
  }

  /**
   * Folder and prefix chip rows from the current list.
   * @returns {void}
   */
  function paintChips() {
    folderRow.replaceChildren();
    prefixRow.replaceChildren();
    const folders = new Set();
    const prefixes = new Set();
    let hasRoot = false;
    items.forEach((row) => {
      const parent = parentOf(row);
      if (parent) {
        folders.add(parent);
      } else {
        hasRoot = true;
      }
      const stem = prefixOf(row.name);
      if (stem) {
        prefixes.add(stem);
      }
    });
    if (folders.size || hasRoot) {
      const label = document.createElement("span");
      label.className = "ez-out-chip-label";
      label.textContent = "Folder";
      folderRow.appendChild(label);
      folderRow.appendChild(
        makeButton("All", "ez-out-chip", () => {
          folder = "";
          paint();
        }),
      );
      if (hasRoot) {
        const rootBtn = makeButton("root", "ez-out-chip", () => {
          folder = ROOT_FOLDER;
          paint();
        });
        rootBtn.setAttribute("aria-pressed", folder === ROOT_FOLDER ? "true" : "false");
        folderRow.appendChild(rootBtn);
      }
      [...folders].sort().forEach((name) => {
        const btn = makeButton(name, "ez-out-chip", () => {
          folder = name;
          paint();
        });
        btn.setAttribute("aria-pressed", folder === name ? "true" : "false");
        folderRow.appendChild(btn);
      });
      folderRow.firstChild &&
        folderRow.querySelectorAll(".ez-out-chip")[0]?.setAttribute(
          "aria-pressed",
          folder === "" ? "true" : "false",
        );
    }
    if (prefixes.size > 1) {
      const label = document.createElement("span");
      label.className = "ez-out-chip-label";
      label.textContent = "Prefix";
      prefixRow.appendChild(label);
      const allBtn = makeButton("All", "ez-out-chip", () => {
        prefix = "";
        paint();
      });
      allBtn.setAttribute("aria-pressed", prefix === "" ? "true" : "false");
      prefixRow.appendChild(allBtn);
      [...prefixes].sort().forEach((name) => {
        const btn = makeButton(name, "ez-out-chip", () => {
          prefix = name;
          paint();
        });
        btn.setAttribute("aria-pressed", prefix === name ? "true" : "false");
        prefixRow.appendChild(btn);
      });
    }
  }

  /**
   * Media element for a row (img / video / audio placeholder).
   * @param {object} row
   * @param {boolean} forThumb
   * @returns {HTMLElement}
   */
  function mediaEl(row, forThumb) {
    if (row.kind === "audio") {
      const ph = document.createElement("div");
      ph.className = "ez-out-audio-ph";
      ph.textContent = "♪";
      ph.setAttribute("aria-hidden", "true");
      return ph;
    }
    if (row.kind === "video") {
      const video = document.createElement("video");
      video.className = "ez-out-thumb";
      video.muted = true;
      video.playsInline = true;
      video.preload = "metadata";
      video.dataset.src = viewUrl(row.rel);
      if (!forThumb) {
        video.controls = true;
        video.src = video.dataset.src;
      }
      video.addEventListener("mouseenter", () => {
        if (prefersReducedMotion()) {
          return;
        }
        if (!video.src && video.dataset.src) {
          video.src = video.dataset.src;
        }
        const play = video.play();
        if (play && typeof play.catch === "function") {
          play.catch(() => {});
        }
      });
      video.addEventListener("mouseleave", () => {
        video.pause();
      });
      return video;
    }
    const img = document.createElement("img");
    img.className = "ez-out-thumb";
    img.alt = row.name || "";
    img.loading = "lazy";
    img.decoding = "async";
    const full = viewUrl(row.rel);
    img.src = forThumb ? thumbUrl(row.rel, row.kind) : full;
    img.addEventListener("error", function onErr() {
      img.removeEventListener("error", onErr);
      if (img.src !== full) {
        img.src = full;
      }
    });
    return img;
  }

  /**
   * One grid card or list row.
   * @param {object} row
   * @returns {HTMLElement}
   */
  function itemEl(row) {
    const isList = view === "list";
    const wrap = document.createElement("div");
    wrap.className = isList ? "ez-out-row-item" : "ez-out-card";
    wrap.dataset.rel = row.rel;
    wrap.setAttribute("role", isList ? "listitem" : "gridcell");
    wrap.setAttribute("aria-selected", selected.has(row.rel) ? "true" : "false");
    wrap.tabIndex = highlightRel === row.rel ? 0 : -1;
    wrap.title = row.rel;

    const check = document.createElement("input");
    check.type = "checkbox";
    check.className = "ez-out-check";
    check.checked = selected.has(row.rel);
    check.title = "Select";
    check.setAttribute("aria-label", "Select " + (row.name || row.rel));
    check.addEventListener("click", (event) => {
      event.stopPropagation();
      if (selected.has(row.rel)) {
        selected.delete(row.rel);
      } else {
        selected.add(row.rel);
      }
      anchorRel = row.rel;
      highlightRel = row.rel;
      paintSelection();
    });

    const thumbWrap = document.createElement("div");
    thumbWrap.className = "ez-out-thumb-wrap";
    thumbWrap.appendChild(mediaEl(row, true));
    const badge = document.createElement("span");
    badge.className = "ez-out-badge ez-out-badge-" + (row.kind || "image");
    badge.textContent = KIND_LABELS[row.kind] || row.kind || "";
    thumbWrap.appendChild(badge);
    if (!isList) {
      thumbWrap.appendChild(check);
    }

    const meta = document.createElement("div");
    meta.className = "ez-out-card-meta";
    const name = document.createElement("span");
    name.className = "ez-out-name";
    name.textContent = row.name || row.rel;
    name.title = row.rel;
    const sub = document.createElement("span");
    sub.className = "ez-out-sub";
    sub.textContent = (metaOn
      ? [formatSize(row.size), formatTime(row.mtime), row.rel]
      : [formatSize(row.size)]
    )
      .filter(Boolean)
      .join(" - ");
    meta.appendChild(name);
    meta.appendChild(sub);
    if (!metaOn) {
      meta.classList.add("is-compact");
    }

    wrap.addEventListener("click", (event) => {
      if (event.target === check) {
        return;
      }
      lastFocusRel = row.rel;
      applyClickSelect(row.rel, event);
    });
    wrap.addEventListener("dblclick", (event) => {
      event.preventDefault();
      openLightbox(row.rel);
    });

    if (isList) {
      wrap.appendChild(check);
      wrap.appendChild(thumbWrap);
      wrap.appendChild(meta);
      const actions = document.createElement("div");
      actions.className = "ez-out-row-actions";
      const useLabel =
        row.kind === "audio"
          ? "Use as start audio"
          : row.kind === "video"
            ? "Copy to input"
            : "Use as start image";
      actions.appendChild(
        makeButton(useLabel, "ez-out-btn", (event) => {
          event.stopPropagation();
          copyRels([row.rel]);
        }),
      );
      actions.appendChild(
        makeButton("Delete", "ez-out-btn", (event) => {
          event.stopPropagation();
          deleteRels([row.rel]);
        }),
      );
      wrap.appendChild(actions);
    } else {
      wrap.appendChild(thumbWrap);
      wrap.appendChild(meta);
    }
    return wrap;
  }

  /**
   * Observe lazy video thumbs in the scroll pane.
   * @returns {void}
   */
  function bindLazyVideos() {
    if (lazyVideo) {
      lazyVideo.disconnect();
    }
    if (typeof IntersectionObserver !== "function") {
      scroll.querySelectorAll("video[data-src]").forEach((node) => {
        if (!node.getAttribute("src")) {
          node.src = node.dataset.src;
        }
      });
      return;
    }
    lazyVideo = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const media = entry.target;
          if (!entry.isIntersecting) {
            // Release decoded video memory for tiles that scrolled away.
            if (media.getAttribute("src")) {
              media.pause();
              media.removeAttribute("src");
              media.load();
            }
            return;
          }
          if (media.dataset.src && !media.getAttribute("src")) {
            media.src = media.dataset.src;
          }
        });
      },
      { root: scroll, rootMargin: "80px" },
    );
    scroll.querySelectorAll("video[data-src]").forEach((node) => {
      lazyVideo.observe(node);
    });
    el._ezOutIo = lazyVideo;
  }

  /**
   * Rebuild the scroll pane from visible items.
   * @returns {void}
   */
  function paint() {
    if (lazyVideo) {
      lazyVideo.disconnect();
      lazyVideo = null;
    }
    kindButtons.forEach((button) => {
      button.setAttribute(
        "aria-pressed",
        button.dataset.kind === kind ? "true" : "false",
      );
    });
    applyThumb();
    paintCrumb();
    paintTree();
    paintActive();
    paintChips();
    const filtering = Boolean(folder || prefix || query) || kind !== "all";
    if (view === "list") {
      listhead.removeAttribute("hidden");
    } else {
      listhead.setAttribute("hidden", "");
    }
    listhead.querySelectorAll(".ez-out-col").forEach((col) => {
      const key = col.dataset.sort || "";
      const on = key === sortMode || (key === "newest" && sortMode === "oldest");
      col.classList.toggle("is-active", on);
      col.setAttribute(
        "aria-sort",
        on ? (sortMode === "oldest" && key === "newest" ? "descending" : "ascending") : "none",
      );
    });
    const vis = visibleItems();
    scroll.replaceChildren();
    if (loading && !items.length) {
      scroll.appendChild(skeletonPane(pageSize > PAGE_START ? 12 : SKELETON_CARDS));
      renderStatus();
      return;
    }
    if (!vis.length) {
      const empty = document.createElement("p");
      empty.className = "ez-out-empty";
      let variant = "nofiles";
      if (!items.length && !filtering) {
        empty.textContent =
          "Queue an App - files stay on the output disk after restart. History does not.";
      } else if (filtering) {
        variant = folder ? "folder" : "filtered";
        empty.textContent = folder
          ? "No files in " + folderToken() + "."
          : "No files match the current filters.";
      } else {
        empty.textContent = "No media files on the output disk yet.";
      }
      empty.dataset.variant = variant;
      if (filtering) {
        empty.appendChild(document.createTextNode(" "));
        empty.appendChild(
          makeButton("Clear filters", "ez-out-btn", () => {
            clearFilters();
          }),
        );
      }
      scroll.appendChild(empty);
      renderStatus();
      return;
    }
    if (view === "list") {
      scroll.appendChild(listhead);
    }
    const paneText = view === "list"
      ? "File list, " + vis.length + " rows"
      : "File grid, " + vis.length + " tiles";
    paneLabel.textContent = paneText;
    const pane = document.createElement("div");
    pane.className = view === "list" ? "ez-out-list" : "ez-out-grid";
    pane.setAttribute("role", view === "list" ? "list" : "grid");
    pane.setAttribute("aria-label", paneText);
    vis.forEach((row) => {
      pane.appendChild(itemEl(row));
    });
    scroll.appendChild(pane);
    if (truncated) {
      loadMoreBtn.removeAttribute("hidden");
      scroll.appendChild(loadMoreBtn);
    } else {
      loadMoreBtn.setAttribute("hidden", "");
    }
    bindLazyVideos();
    paintSelection();
    paintRovingFocus();
    if (lightboxRel) {
      openLightbox(lightboxRel);
    }
  }

  /**
   * Lightbox overlay for one file.
   * @param {string} rel
   * @returns {void}
   */
  function openLightbox(rel) {
    const row = items.find((item) => item.rel === rel);
    if (!row) {
      closeLightbox();
      return;
    }
    lightboxRel = rel;
    highlightRel = rel;
    lightbox.replaceChildren();
    const media = document.createElement("div");
    media.className = "ez-out-lightbox-media";
    if (row.kind === "image") {
      const img = document.createElement("img");
      img.src = viewUrl(row.rel);
      img.alt = row.name || "";
      media.appendChild(img);
    } else if (row.kind === "audio") {
      const audio = document.createElement("audio");
      audio.controls = true;
      audio.src = viewUrl(row.rel);
      media.appendChild(audio);
    } else {
      const video = document.createElement("video");
      video.controls = true;
      video.src = viewUrl(row.rel);
      media.appendChild(video);
    }
    const bar = document.createElement("div");
    bar.className = "ez-out-lightbox-bar";
    const title = document.createElement("span");
    title.className = "ez-out-lightbox-title";
    title.textContent = row.rel;
    title.title = row.rel;
    bar.appendChild(title);
    bar.appendChild(
      makeButton("Prev", "ez-out-btn", () => {
        stepLightbox(-1);
      }),
    );
    bar.appendChild(
      makeButton("Next", "ez-out-btn", () => {
        stepLightbox(1);
      }),
    );
    bar.appendChild(
      makeButton("Download", "ez-out-btn", () => {
        downloadRels([row.rel]);
      }),
    );
    bar.appendChild(
      makeButton("Copy path", "ez-out-btn", () => {
        copyPaths([row.rel]);
      }),
    );
    const useLabel =
      row.kind === "audio"
        ? "Use as start audio"
        : row.kind === "video"
          ? "Copy to input"
          : "Use as start image";
    bar.appendChild(
      makeButton(useLabel, "ez-out-btn", () => {
        copyRels([row.rel]);
      }),
    );
    bar.appendChild(
      makeButton("Delete", "ez-out-btn", () => {
        deleteRels([row.rel]);
      }),
    );
    const fileReportBtn = makeButton("Report", "ez-out-btn", () => {
      openFeedbackReport({
        kind: "bug",
        surface: "media-file",
        summary: clipText("Problem with " + row.rel, 120),
        context: fileContext(row),
      });
    }, { icon: true });
    fileReportBtn.setAttribute(
      "aria-label",
      "Report a problem with this file on GitHub",
    );
    bar.appendChild(fileReportBtn);
    bar.appendChild(
      makeButton("Close", "ez-out-btn", () => {
        closeLightbox();
      }),
    );
    lightbox.appendChild(media);
    lightbox.appendChild(bar);
    lightbox.classList.add("is-open");
    lightbox.removeAttribute("hidden");
    lightbox.setAttribute("aria-label", "Preview " + (row.name || row.rel));
    if (!lightboxRel || !lightbox.contains(document.activeElement)) {
      const prior = document.activeElement;
      lightboxReturn =
        prior && prior !== el && el.contains(prior)
          ? prior
          : scroll.querySelector("[data-rel=\"" + rel + "\"]") || null;
    }
    const first = bar.querySelector("button");
    if (first && typeof first.focus === "function") {
      first.focus();
    } else if (typeof lightbox.focus === "function") {
      lightbox.tabIndex = -1;
      lightbox.focus();
    }
    paintSelection();
  }

  /**
   * Hide the lightbox.
   * @returns {void}
   */
  function closeLightbox() {
    lightboxRel = "";
    lightbox.classList.remove("is-open");
    lightbox.setAttribute("hidden", "");
    lightbox.replaceChildren();
    const back = lightboxReturn;
    lightboxReturn = null;
    if (back && typeof back.focus === "function" && el.contains(back)) {
      back.focus();
    } else {
      el.focus();
    }
  }

  /**
   * Keep Tab inside the open preview dialog.
   * @param {KeyboardEvent} event Key event under the single panel handler
   * @returns {boolean} True when the key was handled
   */
  function trapLightboxFocus(event) {
    if (!lightboxRel || event.key !== "Tab") {
      return false;
    }
    const stops = lightbox.querySelectorAll("button, audio, video, [tabindex]");
    if (!stops.length) {
      return false;
    }
    const list = [...stops];
    const at = list.indexOf(document.activeElement);
    const step = event.shiftKey ? -1 : 1;
    const nextNode = list[(at + step + list.length) % list.length] || list[0];
    if (nextNode && typeof nextNode.focus === "function") {
      nextNode.focus();
    }
    event.preventDefault();
    return true;
  }

  /**
   * Move the lightbox to a neighbor in the visible list.
   * @param {number} delta
   * @returns {void}
   */
  function stepLightbox(delta) {
    const vis = visibleItems();
    const idx = vis.findIndex((row) => row.rel === lightboxRel);
    if (idx < 0 || !vis.length) {
      return;
    }
    const next = vis[(idx + delta + vis.length) % vis.length];
    openLightbox(next.rel);
  }

  /**
   * Copy relative paths to the clipboard.
   * @param {string[]} rels
   * @returns {Promise<void>}
   */
  async function copyPaths(rels) {
    const text = rels.join("\n");
    if (!text) {
      announce("Nothing selected", "warn");
      return;
    }
    try {
      if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
        await navigator.clipboard.writeText(text);
        announce("Copied " + rels.length + " path(s)", "ok");
        return;
      }
      throw new Error("clipboard unavailable");
    } catch (err) {
      // No clipboard permission or a plain-http origin: fall back to a
      // selectable offscreen textarea so the paths still reach the user.
      clipboard.value = text;
      el.appendChild(clipboard);
      clipboard.select();
      let copied = false;
      try {
        copied = Boolean(document.execCommand && document.execCommand("copy"));
      } catch (_err) {
        copied = false;
      }
      if (copied) {
        announce("Copied " + rels.length + " path(s)", "ok");
      } else {
        clipboard.focus();
        announce("Clipboard blocked - paths are selected, press Ctrl/Cmd+C", "warn");
      }
      if (clipboard.parentNode) {
        clipboard.parentNode.removeChild(clipboard);
      }
    }
  }

  /**
   * Delete one or many files after confirm.
   * @param {string[]} rels
   * @returns {Promise<void>}
   */
  async function deleteRels(rels) {
    const unique = [...new Set(rels.filter(Boolean))];
    if (!unique.length) {
      return;
    }
    if (!confirmDelete(unique)) {
      return;
    }
    try {
      const body = unique.length === 1 ? { rel: unique[0] } : { rels: unique };
      const data = await postJson("/ez_outputs/delete", body);
      const failed = (data.errors || []).length;
      const gone = (data.deleted || []).length;
      if (failed) {
        announce("Deleted " + gone + ", " + failed + " failed", "warn");
        recordFeedbackError(
          "media-explorer",
          "Delete rejected " + failed + " of " + unique.length + " file(s)",
          "endpoint=/ez_outputs/delete " + errorDetail(data.errors),
        );
      }
      if (!failed) {
        announce("Deleted " + gone + " file(s)", "ok");
      }
      if (lightboxRel && unique.includes(lightboxRel)) {
        closeLightbox();
      }
      unique.forEach((rel) => selected.delete(rel));
      await refresh();
    } catch (err) {
      const message = String(err && err.message ? err.message : err);
      announce(message, "bad");
      noteFailure("/ez_outputs/delete", err, "Delete failed: " + message);
    }
  }

  /**
   * Copy files into /inputs and set matching graph widgets.
   * @param {string[]} rels
   * @returns {Promise<void>}
   */
  async function copyRels(rels) {
    const unique = [...new Set(rels.filter(Boolean))];
    if (!unique.length) {
      return;
    }
    try {
      const body = unique.length === 1 ? { rel: unique[0] } : { rels: unique };
      const data = await postJson("/ez_outputs/to-input", body);
      const byRel = new Map(items.map((row) => [row.rel, row]));
      if (Array.isArray(data.copied) && data.copied.length) {
        let lastImage = "";
        let lastAudio = "";
        data.copied.forEach((row) => {
          const src = byRel.get(row.rel);
          const srcKind = src?.kind || "image";
          if (srcKind === "image") {
            lastImage = row.name;
          }
          if (srcKind === "audio") {
            lastAudio = row.name;
          }
        });
        if (lastImage) {
          applyToGraph("image", lastImage);
        }
        if (lastAudio) {
          applyToGraph("audio", lastAudio);
        }
        const failed = (data.errors || []).length;
        status.textContent =
          "Copied " +
          data.copied.length +
          (failed ? ", " + failed + " failed" : "") +
          " to input";
        if (failed) {
          recordFeedbackError(
            "media-explorer",
            "Copy to input rejected " + failed + " of " + unique.length + " file(s)",
            "endpoint=/ez_outputs/to-input " + errorDetail(data.errors),
          );
        }
        return;
      }
      if (data.name) {
        const src = byRel.get(unique[0]);
        applyToGraph(src?.kind || "image", data.name);
        status.textContent = "Copied " + data.name + " to input";
      }
    } catch (err) {
      const message = String(err && err.message ? err.message : err);
      announce(message, "bad");
      noteFailure("/ez_outputs/to-input", err, "Copy to input failed: " + message);
    }
  }

  /**
   * Reload the file list from GET /ez_outputs/list.
   * @param {boolean=} background Keep the current pane while refetching
   * @returns {Promise<void>}
   */
  async function refresh(background) {
    const quiet = Boolean(background) && items.length > 0;
    loading = !quiet;
    failed = false;
    refreshBtn.setAttribute("aria-busy", loading ? "true" : "false");
    if (loading) {
      paint();
    }
    try {
      const data = await fetchJson(
        "/ez_outputs/list?kind=" +
          encodeURIComponent(kind) +
          "&q=" +
          encodeURIComponent(query) +
          "&limit=" +
          encodeURIComponent(String(pageSize)),
      );
      items = Array.isArray(data.items) ? data.items : [];
      truncated = Boolean(data.truncated);
      const live = new Set(items.map((row) => row.rel));
      selected.forEach((rel) => {
        if (!live.has(rel)) {
          selected.delete(rel);
        }
      });
      if (highlightRel && !live.has(highlightRel)) {
        highlightRel = items[0]?.rel || "";
      }
      // Clear the flag before painting or an empty result keeps the skeleton.
      loading = false;
      paint();
    } catch (err) {
      const message = String(err && err.message ? err.message : err);
      const httpStatus = err && err.status != null ? String(err.status) : "n/a";
      noteFailure("/ez_outputs/list", err, "List failed: " + message);
      // A dead list must not leave a pane of rows that no longer exist.
      items = [];
      truncated = false;
      failed = true;
      scroll.replaceChildren();
      const fail = document.createElement("p");
      fail.className = "ez-out-fail";
      fail.textContent = message;
      fail.appendChild(document.createTextNode(" "));
      fail.appendChild(
        makeButton("Retry", "ez-out-btn", () => {
          refresh();
        }),
      );
      fail.appendChild(document.createTextNode(" "));
      fail.appendChild(failReportButton("/ez_outputs/list", message, httpStatus));
      scroll.appendChild(fail);
      announce("Could not list outputs - " + message, "bad");
      renderStatus();
    } finally {
      loading = false;
      refreshBtn.setAttribute("aria-busy", "false");
    }
  }

  /**
   * Add the range from the anchor to a rel into the current selection.
   * @param {string} rel Row to extend to
   * @returns {void}
   */
  function extendTo(rel) {
    const rels = visibleItems().map((row) => row.rel);
    const a = rels.indexOf(anchorRel);
    const b = rels.indexOf(rel);
    if (a < 0 || b < 0) {
      selected.add(rel);
    } else {
      const lo = Math.min(a, b);
      const hi = Math.max(a, b);
      rels.slice(lo, hi + 1).forEach((one) => selected.add(one));
    }
    anchorRel = anchorRel || rel;
    highlightRel = rel;
    paintSelection();
    paintRovingFocus();
  }

  /**
   * Columns in the grid so Up and Down jump a whole row.
   * @returns {number} Column count, at least one
   */
  function gridColumns() {
    if (view !== "grid") {
      return 1;
    }
    const edge = effectiveThumb() + 8;
    const width = Number(scroll.clientWidth) || Number(el.clientWidth) || edge;
    return Math.max(1, Math.floor(width / edge) || 1);
  }

  /**
   * Keyboard: arrows, space, enter, delete, escape, ctrl+a, size, view, help.
   * @param {KeyboardEvent} event
   * @returns {void}
   */
  function onKey(event) {
    const tag = (event.target && event.target.tagName) || "";
    if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") {
      if (event.key === "Escape") {
        if (lightboxRel) {
          closeLightbox();
        } else {
          event.target.blur();
          el.focus();
        }
        event.preventDefault();
      }
      return;
    }
    if (trapLightboxFocus(event)) {
      return;
    }
    const vis = visibleItems();
    const idx = vis.findIndex((row) => row.rel === highlightRel);
    if (event.key === "Escape") {
      if (lightboxRel) {
        closeLightbox();
        event.preventDefault();
        return;
      }
      if (helpOpen) {
        toggleHelp(false);
        event.preventDefault();
        return;
      }
      if (selected.size) {
        selected = new Set();
        paintSelection();
        event.preventDefault();
        return;
      }
      if (folder || prefix || query || kind !== "all") {
        clearFilters();
        event.preventDefault();
      }
      return;
    }
    if (event.key === "?") {
      toggleHelp();
      event.preventDefault();
      return;
    }
    if (event.key === "/") {
      search.focus();
      if (typeof search.select === "function") {
        search.select();
      }
      event.preventDefault();
      return;
    }
    if (event.key === "f" || event.key === "F") {
      // Below the wide tier the rail is hidden, so reach the folder chips instead.
      const target = tier === "wide"
        ? tree.querySelector(".ez-out-tree-item")
        : folderRow.querySelector(".ez-out-chip");
      if (target && typeof target.focus === "function") {
        target.focus();
      }
      event.preventDefault();
      return;
    }
    if (event.key === "g" || event.key === "G") {
      setView("grid");
      event.preventDefault();
      return;
    }
    if (event.key === "l" || event.key === "L") {
      setView("list");
      event.preventDefault();
      return;
    }
    if ((event.key === "+" || event.key === "=") && view === "grid") {
      nudgeSize(8);
      event.preventDefault();
      return;
    }
    if (event.key === "-" && view === "grid") {
      nudgeSize(-8);
      event.preventDefault();
      return;
    }
    if (event.key === "0" && view === "grid") {
      autoSize = true;
      storePref(PREFS_THUMB, "auto");
      applyThumb();
      announce("Thumbnail size auto", "ok");
      event.preventDefault();
      return;
    }
    if ((event.key === "a" || event.key === "A") && (event.metaKey || event.ctrlKey)) {
      selectAllVisible();
      event.preventDefault();
      return;
    }
    if (event.key === "Enter" && highlightRel) {
      openLightbox(highlightRel);
      event.preventDefault();
      return;
    }
    if ((event.key === "Delete" || event.key === "Backspace") && selected.size) {
      deleteRels([...selected]);
      event.preventDefault();
      return;
    }
    if (event.key === " " && highlightRel) {
      if (selected.has(highlightRel)) {
        selected.delete(highlightRel);
      } else {
        selected.add(highlightRel);
      }
      anchorRel = highlightRel;
      paintSelection();
      event.preventDefault();
      return;
    }
    if (event.key === "Home" || event.key === "End") {
      if (!vis.length) {
        return;
      }
      const target = event.key === "Home" ? vis[0] : vis[vis.length - 1];
      if (event.shiftKey) {
        extendTo(target.rel);
      } else {
        focusRel(target.rel);
      }
      if (lightboxRel) {
        openLightbox(target.rel);
      }
      event.preventDefault();
      return;
    }
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      if (!vis.length) {
        return;
      }
      const step = event.key === "ArrowDown" ? gridColumns() : 1;
      const from = idx < 0 ? -1 : idx;
      const next = vis[Math.min(vis.length - 1, from + step)] || vis[0];
      highlightRel = next.rel;
      if (event.shiftKey) {
        extendTo(next.rel);
      } else {
        focusRel(next.rel);
      }
      if (lightboxRel) {
        openLightbox(highlightRel);
      }
      event.preventDefault();
      return;
    }
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      if (!vis.length) {
        return;
      }
      const step = event.key === "ArrowUp" ? gridColumns() : 1;
      const from = idx < 0 ? 0 : idx;
      const next = vis[Math.max(0, from - step)] || vis[0];
      highlightRel = next.rel;
      if (event.shiftKey) {
        extendTo(next.rel);
      } else {
        focusRel(next.rel);
      }
      if (lightboxRel) {
        openLightbox(highlightRel);
      }
      event.preventDefault();
    }
  }

  if (el._ezOutKey) {
    el.removeEventListener("keydown", el._ezOutKey);
  }
  el._ezOutKey = onKey;
  el.addEventListener("keydown", onKey);

  const api = app.api;
  /**
   * Debounced background refresh after a Queue step so new files appear.
   * @returns {void}
   */
  function onExecuted() {
    window.clearTimeout(execTimer);
    execTimer = window.setTimeout(() => {
      refresh(true);
    }, EXECUTED_MS);
  }
  if (api && typeof api.addEventListener === "function") {
    if (mount._onExecuted && typeof api.removeEventListener === "function") {
      api.removeEventListener("executed", mount._onExecuted);
    }
    mount._onExecuted = onExecuted;
    api.addEventListener("executed", onExecuted);
  }
  if (el._ezOutIo && typeof el._ezOutIo.disconnect === "function") {
    el._ezOutIo.disconnect();
  }

  kindRow.setAttribute("role", "toolbar");
  kindRow.setAttribute("aria-label", "Filter by type, search, refresh, report");
  const toolbar = document.createElement("div");
  toolbar.className = "ez-out-toolbar";
  toolbar.appendChild(kindRow);
  toolbar.appendChild(viewRow);
  toolbar.appendChild(more);

  bodyRow.appendChild(tree);
  bodyRow.appendChild(scroll);

  el.appendChild(head);
  el.appendChild(hint);
  el.appendChild(toolbar);
  el.appendChild(active);
  el.appendChild(folderRow);
  el.appendChild(prefixRow);
  el.appendChild(bulk);
  el.appendChild(bodyRow);
  el.appendChild(status);
  el.appendChild(lightbox);
  el.appendChild(help);

  if (el._ezOutRo && typeof el._ezOutRo.disconnect === "function") {
    el._ezOutRo.disconnect();
  }
  if (typeof ResizeObserver === "function") {
    const observer = new ResizeObserver(() => {
      applyTier();
    });
    observer.observe(el);
    el._ezOutRo = observer;
  }

  applyThumb();
  refresh();
}

app.registerExtension({
  name: "ez.outputs",
  /**
   * Register the Outputs sidebar tab when the frontend supports it.
   * @returns {Promise<void>}
   */
  async setup() {
    const mgr = app.extensionManager;
    if (!mgr || typeof mgr.registerSidebarTab !== "function") {
      return;
    }
    mgr.registerSidebarTab({
      id: TAB_ID,
      icon: "pi pi-images",
      title: "Outputs",
      tooltip: "Browse saved generations",
      type: "custom",
      render: mount,
    });
  },
});

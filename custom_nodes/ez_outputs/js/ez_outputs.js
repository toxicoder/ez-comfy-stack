/**
 * Outputs sidebar: browse media that survives stack restart.
 *
 * Thumbnail grid / list, multi-select, bulk delete / copy / download.
 * Comfy History is in-memory. Files on COMFY_OUTPUT_DIR persist. Nodes 2.0
 * safe: no LiteGraph widget hooks, no canvas resize. Treat inputEl as optional.
 */
import { app } from "../../scripts/app.js";

const TAB_ID = "ez-outputs";
const STYLE_ID = "ez-outputs-css";
const PREFS_VIEW = "ez-comfy.outputs.view";
const PREFS_THUMB = "ez-comfy.outputs.thumb";
const PREFS_SORT = "ez-comfy.outputs.sort";
const THUMB_MIN = 80;
const THUMB_MAX = 280;
const THUMB_DEFAULT = 128;
const SEARCH_MS = 150;
const EXECUTED_MS = 1000;
const ROOT_FOLDER = "__root__";
const KIND_LABELS = {
  image: "Still",
  video: "Video",
  audio: "Audio",
};

const FALLBACK_CSS = `
.ez-out { --ez-out-thumb: 128px; display:flex; flex-direction:column; height:100%; gap:8px; padding:8px; position:relative; box-sizing:border-box; font:12px/1.4 ui-sans-serif,system-ui,sans-serif; }
.ez-out-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(var(--ez-out-thumb),1fr)); gap:8px; }
.ez-out-list { display:flex; flex-direction:column; }
.ez-out-scroll { flex:1; min-height:0; overflow:auto; }
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
 * Comfy SaveImage stem (ez_still_draft_00001_.png → ez_still_draft).
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
    throw new Error(data.error || response.statusText);
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
  const extra = rels.length > 5 ? "\n…" : "";
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
 * Create a button.
 * @param {string} label
 * @param {string} className
 * @param {function(Event=): void} onClick
 * @returns {HTMLButtonElement}
 */
function makeButton(label, className, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.className = className;
  button.addEventListener("click", onClick);
  return button;
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

  /** @type {string} */
  let kind = "all";
  /** @type {string} */
  let query = "";
  /** @type {string} */
  let view = loadView();
  /** @type {number} */
  let thumbSize = loadThumb();
  /** @type {string} */
  let sortMode = loadSort();
  /** @type {string} */
  let folder = "";
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

  el.style.setProperty("--ez-out-thumb", thumbSize + "px");

  const hint = document.createElement("p");
  hint.className = "ez-out-hint";
  hint.textContent =
    "Files on the output disk survive restart. History does not.";

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
      refresh();
    });
    button.dataset.kind = id;
    kindRow.appendChild(button);
    return button;
  });

  const search = document.createElement("input");
  search.type = "search";
  search.className = "ez-out-search";
  search.placeholder = "Filter prefix (ez_still_draft)";
  search.addEventListener("input", () => {
    query = search.value || "";
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(refresh, SEARCH_MS);
  });
  kindRow.appendChild(search);

  const refreshBtn = makeButton("Refresh", "ez-out-btn", () => {
    refresh();
  });
  kindRow.appendChild(refreshBtn);

  const viewRow = document.createElement("div");
  viewRow.className = "ez-out-row";
  const gridBtn = makeButton("Grid", "ez-out-btn", () => {
    setView("grid");
  });
  const listBtn = makeButton("List", "ez-out-btn", () => {
    setView("list");
  });
  const sizeLabel = document.createElement("span");
  sizeLabel.className = "ez-out-size-label";
  sizeLabel.textContent = "Size";
  const sizeInput = document.createElement("input");
  sizeInput.type = "range";
  sizeInput.className = "ez-out-range";
  sizeInput.min = String(THUMB_MIN);
  sizeInput.max = String(THUMB_MAX);
  sizeInput.step = "8";
  sizeInput.value = String(thumbSize);
  sizeInput.title = "Thumbnail size";
  sizeInput.addEventListener("input", () => {
    thumbSize = Number(sizeInput.value) || THUMB_DEFAULT;
    el.style.setProperty("--ez-out-thumb", thumbSize + "px");
    storePref(PREFS_THUMB, String(thumbSize));
  });
  const sortSelect = document.createElement("select");
  sortSelect.className = "ez-out-select";
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
  viewRow.appendChild(gridBtn);
  viewRow.appendChild(listBtn);
  viewRow.appendChild(sizeLabel);
  viewRow.appendChild(sizeInput);
  viewRow.appendChild(sortSelect);
  viewRow.appendChild(selectAllBtn);

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

  const status = document.createElement("p");
  status.className = "ez-out-status";

  const lightbox = document.createElement("div");
  lightbox.className = "ez-out-lightbox";
  lightbox.setAttribute("hidden", "");

  /**
   * Switch grid vs list and persist.
   * @param {string} next
   * @returns {void}
   */
  function setView(next) {
    view = next === "list" ? "list" : "grid";
    storePref(PREFS_VIEW, view);
    paint();
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
      const vis = visibleItems();
      const rels = vis.map((row) => row.rel);
      const a = rels.indexOf(anchorRel);
      const b = rels.indexOf(rel);
      if (a < 0 || b < 0) {
        selected = new Set([rel]);
      } else {
        const lo = Math.min(a, b);
        const hi = Math.max(a, b);
        selected = new Set(rels.slice(lo, hi + 1));
      }
      highlightRel = rel;
      paintSelection();
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
    const vis = new Set(visibleItems().map((row) => row.rel));
    selected.forEach((rel) => {
      if (!vis.has(rel)) {
        selected.delete(rel);
      }
    });
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
    bulkCount.textContent = n + " selected";
    renderStatus();
  }

  /**
   * Status line: counts, selection, bytes, truncated cap.
   * @returns {void}
   */
  function renderStatus() {
    const vis = visibleItems();
    const chosen = vis.filter((row) => selected.has(row.rel));
    const pool = chosen.length ? chosen : vis;
    const bytes = pool.reduce((sum, row) => sum + (Number(row.size) || 0), 0);
    let text = vis.length + " files";
    if (chosen.length) {
      text += " · " + chosen.length + " selected";
    }
    text += " · " + formatSize(bytes);
    if (truncated && !folder && !prefix && !query) {
      text += " · newest 500";
    }
    status.textContent = text;
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

    const check = document.createElement("input");
    check.type = "checkbox";
    check.className = "ez-out-check";
    check.checked = selected.has(row.rel);
    check.title = "Select";
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
    sub.textContent = [formatSize(row.size), formatTime(row.mtime), row.rel]
      .filter(Boolean)
      .join(" · ");
    meta.appendChild(name);
    meta.appendChild(sub);

    wrap.addEventListener("click", (event) => {
      if (event.target === check) {
        return;
      }
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
    lazyVideo = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) {
            return;
          }
          const media = entry.target;
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
    gridBtn.classList.toggle("is-active", view === "grid");
    listBtn.classList.toggle("is-active", view === "list");
    sizeInput.disabled = view === "list";
    paintChips();
    const vis = visibleItems();
    scroll.replaceChildren();
    if (!vis.length) {
      const empty = document.createElement("p");
      empty.className = "ez-out-empty";
      empty.textContent =
        "Queue an App — files stay on the output disk after restart. History does not.";
      scroll.appendChild(empty);
      renderStatus();
      return;
    }
    const pane = document.createElement("div");
    pane.className = view === "list" ? "ez-out-list" : "ez-out-grid";
    pane.setAttribute("role", view === "list" ? "list" : "grid");
    vis.forEach((row) => {
      pane.appendChild(itemEl(row));
    });
    scroll.appendChild(pane);
    bindLazyVideos();
    paintSelection();
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
    bar.appendChild(
      makeButton("Close", "ez-out-btn", () => {
        closeLightbox();
      }),
    );
    lightbox.appendChild(media);
    lightbox.appendChild(bar);
    lightbox.classList.add("is-open");
    lightbox.removeAttribute("hidden");
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
    try {
      if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
        await navigator.clipboard.writeText(text);
        status.textContent = "Copied " + rels.length + " path(s)";
      }
    } catch (err) {
      status.textContent = String(err && err.message ? err.message : err);
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
      if (failed) {
        status.textContent =
          "Deleted " + (data.deleted || []).length + ", " + failed + " failed";
      }
      if (lightboxRel && unique.includes(lightboxRel)) {
        closeLightbox();
      }
      unique.forEach((rel) => selected.delete(rel));
      await refresh();
    } catch (err) {
      status.textContent = String(err && err.message ? err.message : err);
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
        return;
      }
      if (data.name) {
        const src = byRel.get(unique[0]);
        applyToGraph(src?.kind || "image", data.name);
        status.textContent = "Copied " + data.name + " to input";
      }
    } catch (err) {
      status.textContent = String(err && err.message ? err.message : err);
    }
  }

  /**
   * Reload the file list from GET /ez_outputs/list.
   * @returns {Promise<void>}
   */
  async function refresh() {
    try {
      const data = await fetchJson(
        "/ez_outputs/list?kind=" +
          encodeURIComponent(kind) +
          "&q=" +
          encodeURIComponent(query),
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
      paint();
    } catch (err) {
      scroll.replaceChildren();
      const fail = document.createElement("p");
      fail.className = "ez-out-fail";
      fail.textContent = String(err && err.message ? err.message : err);
      scroll.appendChild(fail);
    }
  }

  /**
   * Keyboard: arrows, space, enter, delete, escape, ctrl+a, +/-.
   * @param {KeyboardEvent} event
   * @returns {void}
   */
  function onKey(event) {
    const tag = (event.target && event.target.tagName) || "";
    if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") {
      if (event.key === "Escape") {
        event.target.blur();
        el.focus();
      }
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
      selected = new Set();
      paintSelection();
      event.preventDefault();
      return;
    }
    if ((event.key === "+" || event.key === "=") && view === "grid") {
      thumbSize = Math.min(THUMB_MAX, thumbSize + 8);
      sizeInput.value = String(thumbSize);
      el.style.setProperty("--ez-out-thumb", thumbSize + "px");
      storePref(PREFS_THUMB, String(thumbSize));
      event.preventDefault();
      return;
    }
    if (event.key === "-" && view === "grid") {
      thumbSize = Math.max(THUMB_MIN, thumbSize - 8);
      sizeInput.value = String(thumbSize);
      el.style.setProperty("--ez-out-thumb", thumbSize + "px");
      storePref(PREFS_THUMB, String(thumbSize));
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
      paintSelection();
      event.preventDefault();
      return;
    }
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      if (!vis.length) {
        return;
      }
      const next = vis[Math.min(vis.length - 1, Math.max(0, idx) + 1)] || vis[0];
      highlightRel = next.rel;
      if (event.shiftKey) {
        applyClickSelect(next.rel, event);
      } else {
        paintSelection();
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
      const next = vis[Math.max(0, (idx < 0 ? 0 : idx) - 1)] || vis[0];
      highlightRel = next.rel;
      if (event.shiftKey) {
        applyClickSelect(next.rel, event);
      } else {
        paintSelection();
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
   * Debounced refresh after a Queue step so new files appear.
   * @returns {void}
   */
  function onExecuted() {
    window.clearTimeout(execTimer);
    execTimer = window.setTimeout(refresh, EXECUTED_MS);
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

  el.appendChild(hint);
  el.appendChild(kindRow);
  el.appendChild(viewRow);
  el.appendChild(folderRow);
  el.appendChild(prefixRow);
  el.appendChild(bulk);
  el.appendChild(scroll);
  el.appendChild(status);
  el.appendChild(lightbox);
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

/**
 * Outputs sidebar: browse media that survives stack restart.
 *
 * Comfy History is in-memory. Files on COMFY_OUTPUT_DIR persist. Nodes 2.0
 * safe: no LiteGraph widget hooks, no canvas resize. Treat inputEl as optional.
 */
import { app } from "../../scripts/app.js";

const TAB_ID = "ez-outputs";

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
 * @returns {string}
 */
function viewUrl(rel) {
  const parts = String(rel || "").replace(/\\/g, "/").split("/");
  const filename = parts.pop() || "";
  const subfolder = parts.join("/");
  const query =
    "filename=" +
    encodeURIComponent(filename) +
    "&type=output&subfolder=" +
    encodeURIComponent(subfolder);
  return apiUrl("/view?" + query);
}

/**
 * Set LoadImage.image on the open graph when that node exists.
 * @param {string} filename
 * @returns {boolean}
 */
function setLoadImage(filename) {
  const nodes = app.graph?.nodes || [];
  const node = nodes.find((item) => item.type === "LoadImage");
  if (!node?.widgets) {
    return false;
  }
  const widget = node.widgets.find((item) => item.name === "image");
  if (!widget) {
    return false;
  }
  widget.value = filename;
  if (typeof widget.callback === "function") {
    widget.callback(filename);
  }
  return true;
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
 * Render the sidebar into el.
 * @param {HTMLElement} el
 * @returns {void}
 */
function mount(el) {
  el.replaceChildren();
  el.style.display = "flex";
  el.style.flexDirection = "column";
  el.style.height = "100%";
  el.style.gap = "8px";
  el.style.padding = "8px";
  el.style.font = "12px/1.4 ui-sans-serif,system-ui,sans-serif";

  const hint = document.createElement("p");
  hint.textContent =
    "Files on the output disk survive restart. History does not.";
  hint.style.margin = "0";
  hint.style.opacity = "0.8";

  const filters = document.createElement("div");
  filters.style.display = "flex";
  filters.style.gap = "4px";
  filters.style.flexWrap = "wrap";

  const kinds = [
    ["all", "All"],
    ["image", "Stills"],
    ["video", "Video"],
    ["audio", "Audio"],
  ];
  /** @type {string} */
  let kind = "all";
  /** @type {string} */
  let query = "";
  const buttons = kinds.map(([id, label]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.dataset.kind = id;
    button.addEventListener("click", () => {
      kind = id;
      refresh();
    });
    filters.appendChild(button);
    return button;
  });

  const search = document.createElement("input");
  search.type = "search";
  search.placeholder = "Filter prefix (ez_still_draft)";
  search.addEventListener("input", () => {
    query = search.value || "";
    refresh();
  });

  const preview = document.createElement("div");
  preview.style.minHeight = "120px";

  const list = document.createElement("div");
  list.style.overflow = "auto";
  list.style.flex = "1";

  const empty = document.createElement("p");
  empty.textContent =
    "Queue an App — files stay on the output disk after restart. History does not.";
  empty.style.opacity = "0.8";

  /**
   * Paint the preview pane for one row.
   * @param {object} row
   * @returns {void}
   */
  function showPreview(row) {
    preview.replaceChildren();
    const src = viewUrl(row.rel);
    if (row.kind === "image") {
      const img = document.createElement("img");
      img.src = src;
      img.alt = row.name;
      img.style.maxWidth = "100%";
      preview.appendChild(img);
      return;
    }
    const media = document.createElement(row.kind === "audio" ? "audio" : "video");
    media.controls = true;
    media.src = src;
    media.style.maxWidth = "100%";
    preview.appendChild(media);
  }

  /**
   * One list row with preview / use / delete.
   * @param {object} row
   * @returns {HTMLElement}
   */
  function rowEl(row) {
    const wrap = document.createElement("div");
    wrap.style.display = "flex";
    wrap.style.flexDirection = "column";
    wrap.style.gap = "4px";
    wrap.style.padding = "6px 0";
    wrap.style.borderBottom = "1px solid rgba(255,255,255,0.08)";
    const title = document.createElement("button");
    title.type = "button";
    title.textContent = row.rel;
    title.style.textAlign = "left";
    title.addEventListener("click", () => {
      showPreview(row);
    });
    const actions = document.createElement("div");
    actions.style.display = "flex";
    actions.style.gap = "4px";
    const useBtn = document.createElement("button");
    useBtn.type = "button";
    useBtn.textContent = "Use as start image";
    useBtn.addEventListener("click", async () => {
      const data = await fetchJson("/ez_outputs/to-input", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rel: row.rel }),
      });
      setLoadImage(data.name);
    });
    const delBtn = document.createElement("button");
    delBtn.type = "button";
    delBtn.textContent = "Delete";
    delBtn.addEventListener("click", async () => {
      if (!window.confirm("Delete " + row.rel + "?")) {
        return;
      }
      await fetchJson("/ez_outputs/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rel: row.rel }),
      });
      refresh();
    });
    actions.appendChild(useBtn);
    actions.appendChild(delBtn);
    wrap.appendChild(title);
    wrap.appendChild(actions);
    return wrap;
  }

  /**
   * Reload the file list.
   * @returns {Promise<void>}
   */
  async function refresh() {
    buttons.forEach((button) => {
      button.style.fontWeight = button.dataset.kind === kind ? "700" : "400";
    });
    list.replaceChildren();
    try {
      const data = await fetchJson(
        "/ez_outputs/list?kind=" +
          encodeURIComponent(kind) +
          "&q=" +
          encodeURIComponent(query)
      );
      const items = data.items || [];
      if (!items.length) {
        list.appendChild(empty);
        return;
      }
      items.forEach((row) => {
        list.appendChild(rowEl(row));
      });
      showPreview(items[0]);
    } catch (err) {
      const fail = document.createElement("p");
      fail.textContent = String(err && err.message ? err.message : err);
      list.appendChild(fail);
    }
  }

  el.appendChild(hint);
  el.appendChild(filters);
  el.appendChild(search);
  el.appendChild(preview);
  el.appendChild(list);
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

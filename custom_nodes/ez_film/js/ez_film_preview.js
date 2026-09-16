/**
 * EZFilmConcat frontend: overlay a downloadable 90s MP4 after Queue.
 *
 * Nodes 2.0: DOM overlay via document.createElement. Does not touch LiteGraph
 * canvas drawing or require inputEl.
 */
import { app } from "../../scripts/app.js";

const OVERLAY_ID = "ez-film-preview-overlay";

/**
 * First VHS gif payload with a filename, or null.
 * @param {object} message
 * @returns {object|null}
 */
function firstGif(message) {
  const gifs = message?.gifs;
  if (!Array.isArray(gifs) || !gifs.length) {
    return null;
  }
  const item = gifs[0];
  if (!item || typeof item.filename !== "string" || !item.filename) {
    return null;
  }
  return item;
}

/**
 * Comfy /view URL for a saved gif/mp4 payload.
 * @param {object} item
 * @returns {string}
 */
function viewUrl(item) {
  const params = new URLSearchParams({
    filename: item.filename,
    type: item.type || "output",
    subfolder: item.subfolder || "",
  });
  return `/view?${params.toString()}`;
}

/**
 * Reuse or create the fixed film-ready overlay element.
 * @returns {HTMLElement}
 */
function ensureOverlay() {
  let el = document.getElementById(OVERLAY_ID);
  if (el) {
    return el;
  }
  el = document.createElement("div");
  el.id = OVERLAY_ID;
  el.setAttribute("role", "dialog");
  el.setAttribute("aria-label", "90s film ready");
  el.style.cssText = [
    "position:fixed",
    "right:16px",
    "bottom:16px",
    "z-index:80",
    "width:min(420px,calc(100vw - 32px))",
    "padding:12px",
    "border-radius:12px",
    "background:rgba(12,16,24,0.96)",
    "color:#e8eef7",
    "font:13px/1.4 ui-sans-serif,system-ui,sans-serif",
    "box-shadow:0 12px 32px rgba(0,0,0,0.45)",
  ].join(";");
  document.body.appendChild(el);
  return el;
}

/**
 * Fill the overlay with a video player and download link.
 * @param {object} item
 * @returns {void}
 */
function renderOverlay(item) {
  const el = ensureOverlay();
  const src = viewUrl(item);
  const name = item.filename;
  el.innerHTML = "";
  const title = document.createElement("div");
  title.textContent = "90s film ready";
  title.style.cssText = "font-weight:600;margin-bottom:8px";
  const video = document.createElement("video");
  video.controls = true;
  video.setAttribute("playsinline", "");
  video.src = src;
  video.style.cssText = "width:100%;height:auto;background:#000;border-radius:8px";
  const row = document.createElement("p");
  row.style.cssText = "margin:8px 0 0;display:flex;gap:12px;flex-wrap:wrap";
  const download = document.createElement("a");
  download.href = src;
  download.setAttribute("download", name);
  download.textContent = "Download MP4";
  download.style.cssText = "color:#8cf";
  const close = document.createElement("button");
  close.type = "button";
  close.textContent = "Hide";
  close.style.cssText =
    "margin-left:auto;background:transparent;color:#9ab;border:0;cursor:pointer";
  close.addEventListener("click", () => {
    el.remove();
  });
  row.append(download, close);
  el.append(title, video, row);
}

app.registerExtension({
  name: "ez_film.preview",
  /**
   * Wrap EZFilmConcat so Queue shows a 90s film overlay.
   * @param {object} nodeType
   * @param {object} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "EZFilmConcat") {
      return;
    }
    const onExecuted = nodeType.prototype.onExecuted;
    /**
     * Show the overlay when the concat node returns a gif payload.
     * @param {object} message
     * @returns {void}
     */
    nodeType.prototype.onExecuted = function (message) {
      onExecuted?.apply(this, arguments);
      const item = firstGif(message);
      if (item) {
        renderOverlay(item);
      }
    };
  },
});

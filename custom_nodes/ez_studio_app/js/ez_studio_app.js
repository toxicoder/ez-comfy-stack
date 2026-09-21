/**
 * App Mode chrome: friendlier widget labels plus an occupancy status chip.
 *
 * Nodes 2.0: writes widget.label and a DOM banner. Does not use LiteGraph
 * canvas drawing. Treat inputEl as optional.
 */
import { app } from "../../scripts/app.js";

const LABELS = {
  quality: "Quality",
  sample: "Sample prompt",
  prompt: "Prompt",
  web_search: "Web search",
  subagents: "Subagents",
  history: "History",
  style: "Style",
  enhance: "Rewrite prompt",
  look: "Look recipe",
  seed: "Seed",
  image: "Start image",
  tags: "Tags",
  lyrics: "Lyrics",
  artist: "Artist",
  album: "Album",
  title: "Title",
  track: "Track",
  tracktotal: "Tracks",
  year: "Year",
  art_mode: "Album art",
  audio_notes: "Audio notes",
  width: "Width",
  height: "Height",
  batch_size: "Batch",
  steps: "Steps",
  cfg: "CFG",
  unet_name: "Image model",
  mode: "Mode",
  duration_hint: "Duration / framing",
  value: "Shot card",
  logline: "Logline",
  seconds: "Duration (seconds)",
  speaker_a_voice: "Speaker A",
  speaker_b_voice: "Speaker B",
  announcer_voice: "Announcer",
  include_announcer: "Include announcer",
  speed: "Speaking speed",
  source: "Source file",
  upload: "Upload media",
  source_url: "Source URL",
  have_rights: "I have rights",
  job_slug: "Job slug",
  target_language: "Target language",
  source_language: "Source language",
  max_speakers: "Max speakers",
  stage: "Stage",
  engine: "Clone engine",
  keep_bed: "Keep original bed",
  spoken_disclosure: "Spoken disclosure",
};

const OCCUPANCY_STOP = {
  none: "nothing GPU",
  llm: "nothing GPU",
  klein: "Wan, LTX, podcast, music",
  wan: "LTX, podcast, music",
  ltx: "Wan, podcast, music, other LTX",
  film: "everything else on that Spark",
  audio: "Klein / Wan / LTX session",
};

const SAVE_TYPES = new Set([
  "SaveImage",
  "VHS_VideoCombine",
  "SaveAudio",
  "SaveAudioMP3",
  "EZFilmConcat",
  "EZClipConcat",
  "EZAlbumPack",
  "EZAudioMetadata",
]);

const BANNER_ID = "ez-studio-app-banner";
const DESC_STYLE_ID = "ez-studio-app-desc-wrap";
const CHIP = [
  "padding:10px 12px",
  "border-radius:10px",
  "background:rgba(12,16,24,0.92)",
  "color:#e8eef7",
  "font:12px/1.4 ui-sans-serif,system-ui,sans-serif",
  "box-shadow:0 8px 24px rgba(0,0,0,0.35)",
  "pointer-events:auto",
  "white-space:normal",
].join(";");

/**
 * extra.lab_app_mode from the loaded graph, or null.
 * @returns {object|null}
 */
function labAppMode() {
  return app.graph?.extra?.lab_app_mode || null;
}

/**
 * Widget labels stamped in extra.linearData.inputs (nodeId:widgetName).
 * @returns {Map<string, string>}
 */
function stampedLabels() {
  // Persist is [nodeId, widgetName, config]. App panel titles use widget.label.
  const labels = new Map();
  const inputs = app.graph?.extra?.linearData?.inputs || [];
  for (const entry of inputs) {
    const nodeId = entry?.[0];
    const widgetName = entry?.[1];
    const config = entry?.[2];
    if (nodeId == null || !widgetName || !config?.label) {
      continue;
    }
    labels.set(`${nodeId}:${widgetName}`, config.label);
  }
  return labels;
}

/**
 * Apply stamped or generic labels onto a node's widgets.
 * @param {object} node
 * @returns {void}
 */
function relabelWidgets(node) {
  if (!node?.widgets) {
    return;
  }
  const labels = stampedLabels();
  for (const widget of node.widgets) {
    const stamped = labels.get(`${node.id}:${widget.name}`);
    if (stamped) {
      widget.label = stamped;
      continue;
    }
    const generic = LABELS[widget.name];
    if (generic) {
      widget.label = generic;
    }
  }
}

/**
 * Relabel every node on the live graph.
 * @returns {void}
 */
function relabelGraph() {
  for (const node of app.graph?.nodes || []) {
    relabelWidgets(node);
  }
}

/**
 * Count save/output nodes used for the occupancy chip progress line.
 * @returns {number}
 */
function countSaveNodes() {
  const nodes = app.graph?.nodes || [];
  return nodes.filter((n) => SAVE_TYPES.has(n.type)).length;
}

/**
 * Reuse or create the occupancy chip element.
 * @returns {HTMLElement}
 */
function ensureBanner() {
  let el = document.getElementById(BANNER_ID);
  if (el) {
    return el;
  }
  el = document.createElement("div");
  el.id = BANNER_ID;
  el.setAttribute("role", "status");
  document.body.appendChild(el);
  return el;
}

/**
 * Stick the chip into the App widgets host, else pin it under the header.
 * @param {HTMLElement} el
 * @returns {void}
 */
function mountBanner(el) {
  const host = document.querySelector("[data-testid=linear-widgets]");
  if (host) {
    el.style.cssText = [
      "position:sticky",
      "top:0",
      "z-index:5",
      "margin:8px 8px 4px",
      CHIP,
    ].join(";");
    if (el.parentElement !== host) {
      host.insertBefore(el, host.firstChild);
    }
    return;
  }
  el.style.cssText = [
    "position:fixed",
    "left:12px",
    "top:56px",
    "z-index:40",
    "max-width:min(420px,calc(100vw - 24px))",
    CHIP,
  ].join(";");
  if (el.parentElement !== document.body) {
    document.body.appendChild(el);
  }
}

/**
 * Escape text for innerHTML banner lines.
 * @param {*} value
 * @returns {string}
 */
function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

/**
 * Inject CSS so App Mode widget descriptions wrap instead of truncating.
 * @returns {void}
 */
function ensureDescriptionCss() {
  if (document.getElementById(DESC_STYLE_ID)) {
    return;
  }
  const style = document.createElement("style");
  style.id = DESC_STYLE_ID;
  style.textContent = `
[data-testid="linear-widgets"] .p-form-helper-text,
[data-testid="linear-widgets"] [class*="description"],
[data-testid="linear-widgets"] .widget-info,
[data-testid="linear-widgets"] small {
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: unset !important;
  height: auto !important;
  max-height: none !important;
}
`;
  document.head.appendChild(style);
}

/**
 * Show occupancy, run status, and handoff copy when App Mode is enabled.
 * @param {string} status
 * @returns {void}
 */
function renderBanner(status) {
  const mode = labAppMode();
  const el = ensureBanner();
  if (!mode?.enabled) {
    el.style.display = "none";
    return;
  }
  el.style.display = "block";
  mountBanner(el);
  const occupancy = mode.occupancy || "none";
  const stop = OCCUPANCY_STOP[occupancy] || "check the Note";
  const handoff = (mode.handoff || []).slice(0, 3).join(" · ");
  const extra = app.graph?.extra || {};
  const summary = String(extra.lab_description || "").trim();
  const qualityCaption = String(extra.lab_quality_caption || "").trim();
  const lines = [
    `<strong>${escapeHtml(occupancy)}</strong> — stop ${escapeHtml(stop)}. One GB10 job.`,
  ];
  if (summary) {
    lines.push(escapeHtml(summary));
  }
  if (qualityCaption) {
    lines.push(escapeHtml(qualityCaption));
  }
  if (status) {
    lines.push(escapeHtml(status));
  }
  if (handoff) {
    lines.push(`Next: ${escapeHtml(handoff)}`);
  }
  const album = extra.lab_album;
  if (album?.role === "album" && album.artist_slug && album.album_slug) {
    lines.push(
      `Full album: ./scripts/manage.sh album-render --album ${escapeHtml(album.artist_slug)}/${escapeHtml(album.album_slug)} --art skip|upload|generate`,
    );
  }
  el.title = summary || qualityCaption || "";
  el.innerHTML = lines.join("<br>");
}

app.registerExtension({
  name: "ez_studio_app.chrome",
  /**
   * Relabel widgets as each node is created.
   * @param {object} node
   * @returns {Promise<void>}
   */
  async nodeCreated(node) {
    relabelWidgets(node);
  },
  /**
   * Mount the occupancy chip and subscribe to graph/execution events.
   * @returns {Promise<void>}
   */
  async setup() {
    ensureDescriptionCss();
    let done = 0;
    const api = app.api;
    const graph = app.graph;
    if (graph?.addEventListener) {
      graph.addEventListener("configured", () => {
        relabelGraph();
        renderBanner("");
      });
    }
    const observer = new MutationObserver(() => {
      const el = document.getElementById(BANNER_ID);
      if (el && el.style.display !== "none") {
        mountBanner(el);
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
    if (!api?.addEventListener) {
      renderBanner("");
      return;
    }
    api.addEventListener("execution_start", () => {
      done = 0;
      const total = countSaveNodes();
      renderBanner(total ? `Running — 0 of ${total} outputs` : "Running…");
    });
    api.addEventListener("executed", ({ detail }) => {
      const node = app.graph?.getNodeById?.(detail?.node);
      if (node && SAVE_TYPES.has(node.type)) {
        done += 1;
      }
      const total = countSaveNodes();
      if (total) {
        renderBanner(`Still ${Math.min(done, total)} of ${total}`);
      }
    });
    api.addEventListener("execution_success", () => {
      const total = countSaveNodes();
      renderBanner(total ? `Done — ${total} of ${total}` : "Done");
    });
    api.addEventListener("execution_error", () => {
      renderBanner("Run failed — open the graph Note for occupancy and next steps.");
    });
    relabelGraph();
    renderBanner("");
  },
});

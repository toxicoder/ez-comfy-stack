import { app } from "../../scripts/app.js";

const LABELS = {
  prompt: "Prompt",
  style: "Style",
  enhance: "Rewrite prompt",
  seed: "Seed",
  image: "Start image",
  tags: "Tags",
  lyrics: "Lyrics",
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
]);

const BANNER_ID = "ez-studio-app-banner";
const CHIP = [
  "padding:10px 12px",
  "border-radius:10px",
  "background:rgba(12,16,24,0.92)",
  "color:#e8eef7",
  "font:12px/1.4 ui-sans-serif,system-ui,sans-serif",
  "box-shadow:0 8px 24px rgba(0,0,0,0.35)",
  "pointer-events:none",
].join(";");

function labAppMode() {
  return app.graph?.extra?.lab_app_mode || null;
}

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

function relabelGraph() {
  for (const node of app.graph?.nodes || []) {
    relabelWidgets(node);
  }
}

function countSaveNodes() {
  const nodes = app.graph?.nodes || [];
  return nodes.filter((n) => SAVE_TYPES.has(n.type)).length;
}

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
  const lines = [
    `<strong>${occupancy}</strong> — stop ${stop}. One GB10 job.`,
  ];
  if (status) {
    lines.push(status);
  }
  if (handoff) {
    lines.push(`Next: ${handoff}`);
  }
  el.innerHTML = lines.join("<br>");
}

app.registerExtension({
  name: "ez_studio_app.chrome",
  async nodeCreated(node) {
    relabelWidgets(node);
  },
  async setup() {
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

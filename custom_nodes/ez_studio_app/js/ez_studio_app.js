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

const SAVE_TYPES = new Set(["SaveImage", "VHS_VideoCombine", "SaveAudio", "SaveAudioMP3"]);

function labAppMode() {
  return app.graph?.extra?.lab_app_mode || null;
}

function relabelWidgets(node) {
  if (!node?.widgets) {
    return;
  }
  for (const widget of node.widgets) {
    const label = LABELS[widget.name];
    if (label) {
      widget.label = label;
    }
  }
}

function countSaveNodes() {
  const nodes = app.graph?.nodes || [];
  return nodes.filter((n) => SAVE_TYPES.has(n.type)).length;
}

function ensureBanner() {
  let el = document.getElementById("ez-studio-app-banner");
  if (el) {
    return el;
  }
  el = document.createElement("div");
  el.id = "ez-studio-app-banner";
  el.style.cssText = [
    "position:fixed",
    "left:12px",
    "bottom:12px",
    "z-index:40",
    "max-width:min(420px,calc(100vw - 24px))",
    "padding:10px 12px",
    "border-radius:10px",
    "background:rgba(12,16,24,0.88)",
    "color:#e8eef7",
    "font:12px/1.4 ui-sans-serif,system-ui,sans-serif",
    "box-shadow:0 8px 24px rgba(0,0,0,0.35)",
    "pointer-events:none",
  ].join(";");
  document.body.appendChild(el);
  return el;
}

function renderBanner(status) {
  const mode = labAppMode();
  const el = ensureBanner();
  if (!mode?.enabled) {
    el.style.display = "none";
    return;
  }
  el.style.display = "block";
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
    renderBanner("");
  },
});

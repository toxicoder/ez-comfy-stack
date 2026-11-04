/**
 * Editing lane panel: agent chat, timeline, browser renderer, laptop MCP.
 *
 * Hand-rolled DOM only (the way the Outputs and Feedback sidebars are): no
 * component library, nothing that can block a queue. Every class is
 * `.ez-edit*`; the stylesheet is `ez_edit.css` with an inline fallback when the
 * static file 404s. The panel docks into the right sidebar through
 * `app.extensionManager` when the frontend offers it and falls back to a
 * right-docked floating aside otherwise, so it survives older frontends.
 *
 * Contract: only the pinned routes are called (/ez_edit/state, /ops, /import,
 * /render, /chat, /exec/pending, /exec/result, /local_tools/*). Every fetch is
 * relative, so it hits the same origin as ComfyUI. Server text is rendered with
 * textContent only - never innerHTML, never eval.
 *
 * The client executor draws the timeline onto a canvas (track stacking,
 * fade/wipe transitions, text/image overlays, captions) and records it with
 * MediaRecorder. The laptop-local MCP section speaks Streamable-HTTP MCP
 * straight from the browser and refuses any endpoint that is not loopback.
 */
import { app } from "../../scripts/app.js";

const TAB_ID = "ez-edit";
const STYLE_ID = "ez-edit-css";
const FLOAT_ID = "ez-edit-floating";
const PREF_MODE = "ez-comfy.edit.mode.";
const PREF_SERVERS = "ez-comfy.edit.mcp";
const KEY_CLIENT = "ez-comfy.edit.client_id";
const POLL_MS = 1000;
const STATE_EVERY = 5;
const LOAD_WAIT_MS = 4000;
const DEFAULT_FPS = 24;
const MAX_RENDER_MS = 300000;
const MCP_PROTOCOL_VERSION = "2024-11-05";
const MCP_ACCEPT = "application/json, text/event-stream";
const LOOPBACK_HOSTS = ["127.0.0.1", "localhost", "::1"];
const RECORDER_MIMES = [
  "video/webm;codecs=vp9,opus",
  "video/webm;codecs=vp8,opus",
  "video/webm;codecs=vp9",
  "video/webm;codecs=vp8",
  "video/webm",
];

const FALLBACK_CSS = `
.ez-edit { display:flex; flex-direction:column; gap:8px; padding:8px; height:100%; overflow:auto; box-sizing:border-box; font:12px/1.45 ui-sans-serif,system-ui,sans-serif; }
.ez-edit [hidden] { display:none; }
.ez-edit h3 { margin:0 0 4px; font-size:12px; }
.ez-edit button, .ez-edit input, .ez-edit textarea { font:inherit; }
.ez-edit-row { display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
.ez-edit-btn { padding:3px 8px; border-radius:6px; border:1px solid rgba(255,255,255,.16); background:rgba(255,255,255,.06); cursor:pointer; }
.ez-edit-chip.is-active { outline:1px solid currentColor; }
.ez-edit-chat { display:flex; flex-direction:column; gap:4px; max-height:220px; overflow:auto; }
.ez-edit-msg { padding:4px 6px; border-radius:6px; background:rgba(255,255,255,.05); white-space:pre-wrap; }
.ez-edit-msg.is-error { color:#f0a0a0; }
.ez-edit-msg.is-tool { opacity:.8; }
.ez-edit-stage { position:relative; background:#000; }
.ez-edit-video, .ez-edit-canvas { display:block; width:100%; height:auto; }
.ez-edit-canvas { position:absolute; inset:0; pointer-events:none; }
.ez-edit-table { width:100%; border-collapse:collapse; }
.ez-edit-table td { padding:2px 4px; border-bottom:1px solid rgba(255,255,255,.08); }
.ez-edit-floating { position:fixed; top:0; right:0; height:100vh; width:min(420px,100vw); z-index:9999; overflow:auto; background:var(--comfy-menu-bg,#1e1e1e); border-left:1px solid rgba(255,255,255,.14); }
.ez-edit-topbar { position:fixed; top:8px; right:8px; z-index:9998; }
`;

/**
 * Panel state, shared by every mounted copy of the panel.
 * @type {object}
 */
const state = {
  projectId: "",
  project: null,
  jobs: [],
  enabled: true,
  mode: "server",
  history: [],
  thread: [],
  chatBusy: false,
  busy: "",
  note: "",
  execConnected: false,
  execBusy: false,
  relayOn: false,
  relayBusy: false,
  servers: [],
  playing: false,
  playToken: 0,
  docked: false,
  tick: 0,
  timer: 0,
  clientId: "",
};

/**
 * The mounted UI references, or null while unmounted.
 * @type {object|null}
 */
let ui = null;

/** Pool of one detached <video> per clip id, reused across plays. */
const videoPool = new Map();

/** Cache of decoded overlay images by source. */
const imagePool = new Map();

/**
 * Backend URL, honoring Comfy's api prefix when present.
 * @param {string} path Root-relative route path.
 * @returns {string} The fetchable URL.
 */
function apiUrl(path) {
  if (app && app.api && typeof app.api.apiURL === "function") {
    return app.api.apiURL(path);
  }
  return path;
}

/**
 * Comfy /view URL for a path under the output dir.
 * @param {string} rel Output-relative path.
 * @returns {string} The view URL.
 */
function viewUrl(rel) {
  const parts = String(rel || "").replace(/\\/g, "/").split("/").filter(Boolean);
  const filename = parts.pop() || "";
  const subfolder = parts.join("/");
  const query = new URLSearchParams();
  query.set("filename", filename);
  query.set("type", "output");
  query.set("subfolder", subfolder);
  return apiUrl("/view?" + query.toString());
}

/**
 * Playable URL for a clip or overlay source (path under COMFY_OUTPUT_DIR).
 * @param {string} source Clip/overlay source path.
 * @returns {string} A URL, or "" when there is nothing to play.
 */
function mediaUrl(source) {
  const raw = String(source || "").trim();
  if (!raw) {
    return "";
  }
  if (/^(https?:|blob:|data:)/i.test(raw)) {
    return raw;
  }
  const slashed = raw.replace(/\\/g, "/");
  const marker = "/outputs/";
  const at = slashed.lastIndexOf(marker);
  const rel = at >= 0 ? slashed.slice(at + marker.length) : slashed.replace(/^\/+/, "");
  return viewUrl(rel);
}

/**
 * Persist a localStorage string; ignore quota / private-mode failures.
 * @param {string} key Storage key.
 * @param {string} value Stored value.
 * @returns {void}
 */
function storePref(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch (_err) {
    /* private mode must not break the panel */
  }
}

/**
 * Read a localStorage string.
 * @param {string} key Storage key.
 * @returns {string} The stored value, or "".
 */
function readPref(key) {
  try {
    return String(localStorage.getItem(key) || "");
  } catch (_err) {
    return "";
  }
}

/**
 * Read a JSON preference with a fallback.
 * @param {string} key Storage key.
 * @param {*} fallback Value when absent or unparsable.
 * @returns {*} The parsed value.
 */
function readJsonPref(key, fallback) {
  const raw = readPref(key);
  if (!raw) {
    return fallback;
  }
  try {
    const parsed = JSON.parse(raw);
    return parsed == null ? fallback : parsed;
  } catch (_err) {
    return fallback;
  }
}

/**
 * Write a JSON preference.
 * @param {string} key Storage key.
 * @param {*} value Value to serialize.
 * @returns {void}
 */
function writeJsonPref(key, value) {
  try {
    storePref(key, JSON.stringify(value));
  } catch (_err) {
    /* ignore */
  }
}

/**
 * Fresh random id (crypto when present, Math.random otherwise).
 * @returns {string} An id string.
 */
function newId() {
  try {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      return String(crypto.randomUUID());
    }
  } catch (_err) {
    /* fall through */
  }
  return "c-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
}

/**
 * Stable per-tab client id (sessionStorage, so reloads keep it).
 * @returns {string} The client id.
 */
function clientId() {
  if (state.clientId) {
    return state.clientId;
  }
  let id = "";
  try {
    id = String(sessionStorage.getItem(KEY_CLIENT) || "");
  } catch (_err) {
    id = "";
  }
  if (!id) {
    id = newId();
    try {
      sessionStorage.setItem(KEY_CLIENT, id);
    } catch (_err) {
      /* in-memory only for this tab */
    }
  }
  state.clientId = id;
  return id;
}

/**
 * localStorage key that pins the render mode for one project.
 * @param {string} projectId Project id.
 * @returns {string} Storage key.
 */
function modeKey(projectId) {
  return PREF_MODE + String(projectId || "default");
}

/**
 * Stored render mode for a project.
 * @param {string} projectId Project id.
 * @returns {string} "server" or "client".
 */
function loadMode(projectId) {
  return readPref(modeKey(projectId)) === "client" ? "client" : "server";
}

/**
 * Persist the render mode for a project.
 * @param {string} projectId Project id.
 * @param {string} mode "server" or "client".
 * @returns {void}
 */
function saveMode(projectId, mode) {
  storePref(modeKey(projectId), mode === "client" ? "client" : "server");
}

/**
 * Seconds as "12.3s".
 * @param {*} value Seconds.
 * @returns {string} Display text.
 */
function formatSeconds(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) {
    return "-";
  }
  return num.toFixed(1) + "s";
}

/**
 * Clamp a size read from user input.
 * @param {*} value Requested size.
 * @param {number} min Lower bound.
 * @param {number} max Upper bound.
 * @param {number} fallback Value when unusable.
 * @returns {number} The clamped integer.
 */
function clampSize(value, min, max, fallback) {
  const num = Math.round(Number(value));
  if (!Number.isFinite(num) || num <= 0) {
    return fallback;
  }
  return Math.min(max, Math.max(min, num));
}

/**
 * Monotonic-ish wall clock in ms, safe without performance.now.
 * @returns {number} Milliseconds.
 */
function nowMs() {
  try {
    if (typeof performance !== "undefined" && typeof performance.now === "function") {
      return performance.now();
    }
  } catch (_err) {
    /* fall through */
  }
  return Date.now();
}

/**
 * Await a bounded sleep.
 * @param {number} ms Milliseconds.
 * @returns {Promise<void>} Resolves after the delay.
 */
function sleep(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, Math.max(0, Number(ms) || 0));
  });
}

/**
 * Await roughly one frame at the project frame rate.
 * @param {number} fps Target frames per second.
 * @returns {Promise<void>} Resolves on the next frame or the frame budget.
 */
function nextFrame(fps) {
  const frameMs = 1000 / (Number(fps) > 0 ? Number(fps) : DEFAULT_FPS);
  return new Promise((resolve) => {
    let done = false;
    const finish = () => {
      if (done) {
        return;
      }
      done = true;
      resolve();
    };
    window.setTimeout(finish, frameMs);
    if (typeof requestAnimationFrame === "function") {
      requestAnimationFrame(finish);
    }
  });
}

/**
 * Attach the stylesheet once, with an inline fallback on 404.
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
    link.href = new URL("./ez_edit.css", import.meta.url).href;
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
 * Create a panel button.
 * @param {string} label Button text.
 * @param {string} className Class list.
 * @param {function(Event=): void} onClick Click handler.
 * @returns {HTMLButtonElement} The button.
 */
function makeButton(label, className, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.textContent = label;
  if (typeof onClick === "function") {
    button.addEventListener("click", onClick);
  }
  return button;
}

/**
 * Create an element with a class and optional text.
 * @param {string} tag Tag name.
 * @param {string} className Class list.
 * @param {string} [text] textContent to set.
 * @returns {HTMLElement} The element.
 */
function makeEl(tag, className, text) {
  const el = document.createElement(tag);
  if (className) {
    el.className = className;
  }
  if (text != null) {
    el.textContent = String(text);
  }
  return el;
}

/**
 * Create a labelled input row.
 * @param {string} label Field label.
 * @param {string} type Input type.
 * @param {string} value Initial value.
 * @param {string} placeholder Placeholder text.
 * @returns {object} `{row, input}` elements.
 */
function makeField(label, type, value, placeholder) {
  const row = makeEl("div", "ez-edit-row");
  if (label) {
    row.appendChild(makeEl("span", "ez-edit-label", label));
  }
  const input = document.createElement("input");
  input.type = type || "text";
  input.className = "ez-edit-input";
  input.value = value == null ? "" : String(value);
  if (placeholder) {
    input.placeholder = placeholder;
  }
  input.setAttribute("aria-label", label || placeholder || "input");
  row.appendChild(input);
  return { row, input };
}

/**
 * Create a titled section.
 * @param {string} title Heading text.
 * @returns {object} `{section, body}` elements.
 */
function makeSection(title) {
  const section = makeEl("section", "ez-edit-section");
  const head = makeEl("h3", "ez-edit-heading", title);
  const body = makeEl("div", "ez-edit-body");
  section.appendChild(head);
  section.appendChild(body);
  return { section, body };
}

/**
 * Normalize a route failure into an Error with the endpoint attached.
 * @param {object} data Parsed body.
 * @param {string} path Route path.
 * @param {number} [status] HTTP status.
 * @returns {Error} The error to throw.
 */
function apiError(data, path, status) {
  const message = (data && data.error) || "request failed";
  const error = new Error(String(message));
  error.endpoint = path;
  error.status = Number(status) || 0;
  return error;
}

/**
 * Fetch JSON from an ez_edit route.
 * @param {string} path Root-relative route.
 * @param {RequestInit} [init] Fetch init.
 * @returns {Promise<object>} The parsed body.
 */
async function fetchJson(path, init) {
  const response = await fetch(apiUrl(path), init);
  let data = {};
  try {
    data = await response.json();
  } catch (_err) {
    data = {};
  }
  if (!response.ok) {
    throw apiError(data, path, response.status);
  }
  return data;
}

/**
 * POST a JSON body to an ez_edit route.
 * @param {string} path Root-relative route.
 * @param {object} body Request body.
 * @returns {Promise<object>} The parsed body.
 */
function postJson(path, body) {
  return fetchJson(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
}

/**
 * One-line rendering of a caught error.
 * @param {*} err The caught value.
 * @returns {string} Display text.
 */
function errLine(err) {
  const base = String((err && err.message) || err || "failed");
  const endpoint = err && err.endpoint ? " (" + err.endpoint + ")" : "";
  const status = err && err.status ? " HTTP " + err.status : "";
  return base + status + endpoint;
}

/**
 * One tool-trace line from the agent loop.
 * @param {object} trace A ToolCallTrace.
 * @returns {string} Display text.
 */
function traceLine(trace) {
  const name = String((trace && trace.name) || "?");
  const ok = trace && trace.ok ? "ok" : "FAILED";
  const summary = String((trace && trace.summary) || "").replace(/\s+/g, " ").slice(0, 300);
  return name + " [" + ok + "] " + summary;
}

/**
 * Post a status note and repaint.
 * @param {string} text Status text.
 * @returns {void}
 */
function setStatus(text) {
  state.note = String(text || "");
  renderStatus();
}

/**
 * Lay the clips out sequentially for preview and client render.
 *
 * One lane, array order; `track` is the compositing order (0 = base plane).
 * @param {object} project The edit project.
 * @returns {object[]} Segments `{clip, inS, outS, dur, start, track, gain}`.
 */
function buildPlan(project) {
  const clips = project && Array.isArray(project.clips) ? project.clips : [];
  const out = [];
  let cursor = 0;
  clips.forEach((clip) => {
    const inS = Math.max(0, Number(clip && clip.in_s) || 0);
    const outS = Math.max(inS, Number(clip && clip.out_s) || 0);
    const span = outS - inS;
    const dur = span > 0 ? span : 0.2;
    out.push({
      clip,
      inS,
      outS,
      dur,
      start: cursor,
      track: Number(clip && clip.track) || 0,
      gain: Number.isFinite(Number(clip && clip.gain)) ? Number(clip.gain) : 1,
    });
    cursor += dur;
  });
  return out;
}

/**
 * Transition entering a clip, normalized.
 * @param {object} seg A plan segment.
 * @returns {object} `{kind, duration_s}`.
 */
function transitionOf(seg) {
  const raw = (seg && seg.clip && seg.clip.transition) || {};
  const kind = String(raw.kind || "cut");
  const duration = Number(raw.duration_s);
  return { kind, duration_s: Number.isFinite(duration) ? Math.max(0, duration) : 0 };
}

/**
 * Segments visible at a timeline second, base plane first.
 * @param {object[]} plan Segments from buildPlan.
 * @param {number} t Timeline seconds.
 * @returns {object[]} Active segments, ascending track.
 */
function activeSegments(plan, t) {
  const active = plan.filter((seg) => t >= seg.start && t < seg.start + seg.dur);
  const first = active[0];
  const index = first ? plan.indexOf(first) : -1;
  if (first && index > 0) {
    const entering = t - first.start < transitionOf(first).duration_s;
    const kind = transitionOf(first).kind;
    if (entering && (kind === "fade" || kind === "wipe")) {
      const prev = plan[index - 1];
      if (prev && active.indexOf(prev) < 0) {
        active.unshift(prev);
      }
    }
  }
  return active.slice().sort((a, b) => a.track - b.track);
}

/**
 * The pooled <video> for a segment, created once per clip id.
 * @param {object} seg A plan segment.
 * @returns {HTMLVideoElement|null} The element, or null without a source.
 */
function videoFor(seg) {
  const source = seg && seg.clip ? seg.clip.source : "";
  const id = String((seg && seg.clip && seg.clip.id) || source || "");
  if (!id) {
    return null;
  }
  const existing = videoPool.get(id);
  const url = mediaUrl(source);
  if (existing && existing._ezEditSrc === url) {
    return existing;
  }
  const video = document.createElement("video");
  video.className = "ez-edit-video";
  video.preload = "auto";
  video.muted = true;
  video.playsInline = true;
  video.crossOrigin = "anonymous";
  video._ezEditSrc = url;
  video._ezEditSeg = seg;
  if (url) {
    video.src = url;
  }
  videoPool.set(id, video);
  return video;
}

/**
 * Pause and detach every pooled video.
 * @returns {void}
 */
function pauseAllVideos() {
  videoPool.forEach((video) => {
    try {
      video.pause();
    } catch (_err) {
      /* detached elements are fine */
    }
    if (video.parentNode) {
      video.parentNode.removeChild(video);
    }
  });
}

/**
 * Wait for a clip to have playable data; never rejects.
 * @param {HTMLVideoElement|null} video The element.
 * @param {number} timeoutMs Upper bound in ms.
 * @returns {Promise<boolean>} True when readyState reached HAVE_CURRENT_DATA.
 */
function waitReady(video, timeoutMs) {
  return new Promise((resolve) => {
    if (!video) {
      resolve(false);
      return;
    }
    if (Number(video.readyState) >= 2) {
      resolve(true);
      return;
    }
    let done = false;
    const finish = (ready) => {
      if (done) {
        return;
      }
      done = true;
      clearTimeout(timer);
      video.removeEventListener("loadeddata", onReady);
      resolve(Boolean(ready));
    };
    const onReady = () => finish(true);
    const timer = window.setTimeout(() => finish(false), Math.max(0, Number(timeoutMs) || 0));
    video.addEventListener("loadeddata", onReady);
  });
}

/**
 * Seek a clip and wait for the seek to land.
 * @param {HTMLVideoElement} video The element.
 * @param {number} seconds Source seconds.
 * @returns {Promise<void>} Resolves when seeked (or after the grace period).
 */
function seekTo(video, seconds) {
  return new Promise((resolve) => {
    let done = false;
    const finish = () => {
      if (done) {
        return;
      }
      done = true;
      clearTimeout(timer);
      video.removeEventListener("seeked", finish);
      resolve();
    };
    const timer = window.setTimeout(finish, 500);
    video.addEventListener("seeked", finish);
    try {
      video.currentTime = Math.max(0, Number(seconds) || 0);
    } catch (_err) {
      finish();
    }
  });
}

/**
 * Play a clip without ever throwing.
 * @param {HTMLVideoElement|null} video The element.
 * @returns {void}
 */
function safePlay(video) {
  if (!video) {
    return;
  }
  try {
    const started = video.play();
    if (started && typeof started.catch === "function") {
      started.catch(() => undefined);
    }
  } catch (_err) {
    /* autoplay policy: preview simply shows the canvas */
  }
}

/**
 * Pause a clip without ever throwing.
 * @param {HTMLVideoElement|null} video The element.
 * @returns {void}
 */
function safePause(video) {
  if (!video) {
    return;
  }
  try {
    video.pause();
  } catch (_err) {
    /* ignore */
  }
}

/**
 * Cached decoded image for an image overlay.
 * @param {string} source Overlay source path.
 * @returns {HTMLImageElement|null} The image once decoded, else null.
 */
function imageFor(source) {
  const url = mediaUrl(source);
  if (!url) {
    return null;
  }
  let image = imagePool.get(url);
  if (!image) {
    image = new Image();
    image.crossOrigin = "anonymous";
    image.decoding = "async";
    image.src = url;
    imagePool.set(url, image);
  }
  return image.complete && Number(image.naturalWidth) > 0 ? image : null;
}

/**
 * Draw media letterboxed into the frame.
 * @param {CanvasRenderingContext2D} ctx The context.
 * @param {object} media A video or image with videoWidth/naturalWidth.
 * @param {number} w Frame width.
 * @param {number} h Frame height.
 * @returns {void}
 */
function drawCover(ctx, media, w, h) {
  const mw = Number(media.videoWidth || media.naturalWidth || 0);
  const mh = Number(media.videoHeight || media.naturalHeight || 0);
  if (!mw || !mh) {
    return;
  }
  const scale = Math.min(w / mw, h / mh);
  const dw = mw * scale;
  const dh = mh * scale;
  try {
    ctx.drawImage(media, (w - dw) / 2, (h - dh) / 2, dw, dh);
  } catch (_err) {
    /* a clip still loading must not throw the whole frame */
  }
}

/**
 * Build the painter closure for a run.
 * @param {CanvasRenderingContext2D} ctx The context.
 * @param {object} project The edit project.
 * @param {object[]} plan Segments from buildPlan.
 * @returns {function(number): void} Painter taking timeline seconds.
 */
function makePainter(ctx, project, plan) {
  return (t) => paintTime(ctx, project, plan, t);
}

/**
 * Draw a single frame of the timeline.
 * @param {CanvasRenderingContext2D} ctx The context.
 * @param {object} project The edit project.
 * @param {object[]} plan Segments from buildPlan.
 * @param {number} t Timeline seconds.
 * @returns {void}
 */
function paintTime(ctx, project, plan, t) {
  const w = Number(ctx.canvas.width) || 0;
  const h = Number(ctx.canvas.height) || 0;
  if (!w || !h) {
    return;
  }
  ctx.save();
  ctx.globalAlpha = 1;
  ctx.fillStyle = "#000000";
  ctx.fillRect(0, 0, w, h);
  activeSegments(plan, t).forEach((seg) => {
    const video = videoFor(seg);
    if (!video || Number(video.readyState) < 2) {
      return;
    }
    const local = Math.max(0, t - seg.start);
    const kind = String((seg.clip && seg.clip.transition && seg.clip.transition.kind) || "cut");
    const span = Math.min(
      Number((seg.clip && seg.clip.transition && seg.clip.transition.duration_s) || 0),
      seg.dur,
    );
    const entering = span > 0 && local < span;
    ctx.save();
    if (kind === "wipe" && entering) {
      const progress = Math.min(1, Math.max(0, local / span));
      ctx.beginPath();
      ctx.rect(0, 0, Math.round(w * progress), h);
      ctx.clip();
      drawCover(ctx, video, w, h);
    } else {
      ctx.globalAlpha = kind === "fade" && entering ? Math.min(1, Math.max(0, local / span)) : 1;
      drawCover(ctx, video, w, h);
    }
    ctx.restore();
  });
  drawOverlays(ctx, project, t, w, h);
  drawCaptions(ctx, project, t, w, h);
  ctx.restore();
}

/**
 * Draw the text/image overlays visible at a timeline second.
 * @param {CanvasRenderingContext2D} ctx The context.
 * @param {object} project The edit project.
 * @param {number} t Timeline seconds.
 * @param {number} w Frame width.
 * @param {number} h Frame height.
 * @returns {void}
 */
function drawOverlays(ctx, project, t, w, h) {
  const overlays = project && Array.isArray(project.overlays) ? project.overlays : [];
  overlays.forEach((overlay) => {
    const at = Number(overlay && overlay.at_s) || 0;
    const dur = Number(overlay && overlay.dur_s) || 0;
    if (t < at || t > at + dur) {
      return;
    }
    const kind = String((overlay && overlay.kind) || "text");
    const x = (Number(overlay && overlay.x) || 0) * w;
    const y = (Number(overlay && overlay.y) || 0) * h;
    const size = Number(overlay && overlay.size) || 0.08;
    try {
      if (kind === "image") {
        const image = imageFor(overlay.source);
        if (image) {
          const iw = Math.max(1, size * w);
          const ih = Math.max(1, iw * (image.naturalHeight / image.naturalWidth || 0.5));
          ctx.drawImage(image, x, y, iw, ih);
        }
        return;
      }
      const text = String((overlay && overlay.text) || "");
      if (!text) {
        return;
      }
      const px = Math.max(8, Math.round(size * h));
      ctx.font = px + "px ui-sans-serif, system-ui, sans-serif";
      ctx.textBaseline = "top";
      ctx.textAlign = "left";
      ctx.fillStyle = "#ffffff";
      ctx.shadowColor = "rgba(0,0,0,0.8)";
      ctx.shadowBlur = Math.max(2, Math.round(px / 8));
      ctx.fillText(text, x, y);
      ctx.shadowBlur = 0;
    } catch (_err) {
      /* a bad overlay must not stop the frame */
    }
  });
}

/**
 * Draw the caption band visible at a timeline second.
 * @param {CanvasRenderingContext2D} ctx The context.
 * @param {object} project The edit project.
 * @param {number} t Timeline seconds.
 * @param {number} w Frame width.
 * @param {number} h Frame height.
 * @returns {void}
 */
function drawCaptions(ctx, project, t, w, h) {
  const captions = project && Array.isArray(project.captions) ? project.captions : [];
  captions.forEach((caption) => {
    const at = Number(caption && caption.at_s) || 0;
    const dur = Number(caption && caption.dur_s) || 0;
    const text = String((caption && caption.text) || "");
    if (t < at || t > at + dur || !text) {
      return;
    }
    try {
      const px = Math.max(12, Math.round(h * 0.05));
      ctx.font = px + "px ui-sans-serif, system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "alphabetic";
      const y = Math.round(h * 0.9);
      const box = ctx.measureText(text);
      const pad = Math.round(px * 0.4);
      ctx.fillStyle = "rgba(0,0,0,0.55)";
      ctx.fillRect(w / 2 - box.width / 2 - pad, y - px, box.width + pad * 2, px + pad);
      ctx.fillStyle = "#ffffff";
      ctx.fillText(text, w / 2, y);
    } catch (_err) {
      /* captions are decorative */
    }
  });
}

/**
 * The shared AudioContext, created on demand.
 * @returns {AudioContext|null} The context, or null without Web Audio.
 */
function audioCtx() {
  if (state.audioCtx && state.audioCtx.state !== "closed") {
    return state.audioCtx;
  }
  const Ctor = typeof window !== "undefined" && (window.AudioContext || window.webkitAudioContext);
  if (!Ctor) {
    return null;
  }
  try {
    state.audioCtx = new Ctor();
    return state.audioCtx;
  } catch (_err) {
    return null;
  }
}

/**
 * MediaElementSource for a clip, created at most once per element.
 * @param {HTMLVideoElement} video The element.
 * @param {AudioContext} ctx The audio context.
 * @returns {object|null} The source node, or null on failure.
 */
function elementSource(video, ctx) {
  if (video._ezEditSource && video._ezEditSourceCtx === ctx) {
    return video._ezEditSource;
  }
  if (video._ezEditSource) {
    return null;
  }
  try {
    video._ezEditSource = ctx.createMediaElementSource(video);
    video._ezEditSourceCtx = ctx;
    return video._ezEditSource;
  } catch (_err) {
    return null;
  }
}

/**
 * Route clip audio through per-clip gains into the recorder and the speakers.
 * @param {object[]} plan Segments from buildPlan.
 * @param {MediaStream|null} stream Recorder stream to add audio tracks to.
 * @returns {object|null} `{ctx, dest, gains}` for later gain changes.
 */
function attachAudio(plan, stream) {
  const ctx = audioCtx();
  if (!ctx) {
    return null;
  }
  try {
    if (typeof ctx.resume === "function") {
      ctx.resume().catch(() => undefined);
    }
    const dest = ctx.createMediaStreamDestination();
    const gains = [];
    plan.forEach((seg) => {
      const video = videoFor(seg);
      if (!video) {
        return;
      }
      const source = elementSource(video, ctx);
      if (!source) {
        return;
      }
      const gain = ctx.createGain();
      gain.gain.value = 0;
      source.connect(gain);
      gain.connect(dest);
      try {
        gain.connect(ctx.destination);
      } catch (_err) {
        /* monitoring is optional */
      }
      gains.push({ seg, gain });
    });
    if (stream && dest.stream && typeof stream.addTrack === "function") {
      dest.stream.getAudioTracks().forEach((track) => {
        try {
          stream.addTrack(track);
        } catch (_err) {
          /* a missing audio track still yields video */
        }
      });
    }
    return { ctx, dest, gains };
  } catch (_err) {
    return null;
  }
}

/**
 * Silence every clip but the one now playing.
 * @param {object|null} rig The rig from attachAudio.
 * @param {object} seg The active segment.
 * @returns {void}
 */
function setSegmentGain(rig, seg) {
  if (!rig || !Array.isArray(rig.gains)) {
    return;
  }
  rig.gains.forEach((entry) => {
    const same = entry.seg === seg;
    const value = same ? Math.max(0, Number(entry.seg.gain) || 0) : 0;
    try {
      entry.gain.gain.value = value;
    } catch (_err) {
      /* ignore */
    }
  });
}

/**
 * Tear down the gain nodes of a finished run.
 * @param {object|null} rig The rig from attachAudio.
 * @returns {void}
 */
function detachAudio(rig) {
  if (!rig || !Array.isArray(rig.gains)) {
    return;
  }
  rig.gains.forEach((entry) => {
    try {
      entry.gain.disconnect();
    } catch (_err) {
      /* ignore */
    }
  });
  try {
    if (rig.dest && typeof rig.dest.disconnect === "function") {
      rig.dest.disconnect();
    }
  } catch (_err) {
    /* ignore */
  }
}

/**
 * First MediaRecorder container/codec the browser supports.
 * @returns {string} A mimeType for MediaRecorder.
 */
function pickMime() {
  if (typeof MediaRecorder === "undefined" || typeof MediaRecorder.isTypeSupported !== "function") {
    return RECORDER_MIMES[RECORDER_MIMES.length - 1];
  }
  for (let i = 0; i < RECORDER_MIMES.length; i += 1) {
    try {
      if (MediaRecorder.isTypeSupported(RECORDER_MIMES[i])) {
        return RECORDER_MIMES[i];
      }
    } catch (_err) {
      /* keep probing */
    }
  }
  return RECORDER_MIMES[RECORDER_MIMES.length - 1];
}

/**
 * Size the stage canvas to the project and return its context.
 * @param {object} project The edit project.
 * @returns {CanvasRenderingContext2D|null} The 2d context, or null.
 */
function ensureStage(project) {
  if (!ui || !ui.canvas) {
    return null;
  }
  const w = clampSize(project && project.width, 16, 3840, 1280);
  const h = clampSize(project && project.height, 16, 2160, 720);
  const canvas = ui.canvas;
  if (canvas.width !== w) {
    canvas.width = w;
  }
  if (canvas.height !== h) {
    canvas.height = h;
  }
  if (!canvas.parentNode && ui.stage) {
    ui.stage.appendChild(canvas);
  }
  try {
    return canvas.getContext("2d");
  } catch (_err) {
    return null;
  }
}

/**
 * Step every clip in order, painting each frame, driven by the wall clock.
 *
 * Clips that never load are skipped after the wait window: the frame keeps
 * painting (black plane plus overlays) so preview and render never throw.
 * @param {object[]} plan Segments from buildPlan.
 * @param {object} project The edit project.
 * @param {function(number): void} paint Draws one timeline second.
 * @param {object} opts `{token, onSegment, fps}`.
 * @returns {Promise<boolean>} False when cancelled or over budget.
 */
async function stepTimeline(plan, project, paint, opts) {
  const token = Number(opts && opts.token);
  const fps = Number(opts && opts.fps) > 0 ? Number(opts.fps) : DEFAULT_FPS;
  const onSegment = opts && typeof opts.onSegment === "function" ? opts.onSegment : null;
  const runStart = nowMs();
  for (let i = 0; i < plan.length; i += 1) {
    if (token !== state.playToken) {
      return false;
    }
    const seg = plan[i];
    const video = videoFor(seg);
    showStageVideo(video);
    const ready = await waitReady(video, LOAD_WAIT_MS);
    if (ready) {
      await seekTo(video, seg.inS);
      try {
        video.playbackRate = 1;
      } catch (_err) {
        /* read-only on some engines */
      }
      safePlay(video);
    }
    if (onSegment) {
      onSegment(seg);
    }
    const segStart = nowMs();
    for (;;) {
      if (token !== state.playToken) {
        safePause(video);
        return false;
      }
      const elapsed = (nowMs() - segStart) / 1000;
      paint(Math.min(seg.start + elapsed, seg.start + seg.dur));
      const played = (nowMs() - runStart) / 1000;
      if (played > MAX_RENDER_MS / 1000) {
        safePause(video);
        return false;
      }
      const mediaDone =
        ready && elapsed > 0.2 && (Number(video.currentTime) >= seg.outS - 0.03 || video.ended);
      if (elapsed >= seg.dur || mediaDone) {
        break;
      }
      await nextFrame(fps);
    }
    safePause(video);
  }
  return true;
}

/**
 * Record the timeline to a webm Blob using canvas + MediaRecorder.
 * @param {object[]} plan Segments from buildPlan.
 * @param {object} project The edit project.
 * @returns {Promise<Blob>} The recorded blob.
 */
async function recordTimeline(plan, project) {
  const canvas = ui && ui.canvas ? ui.canvas : null;
  if (!canvas || typeof canvas.captureStream !== "function") {
    throw new Error("canvas.captureStream is unavailable in this browser");
  }
  if (typeof MediaRecorder === "undefined") {
    throw new Error("MediaRecorder is unavailable in this browser");
  }
  const ctx = ensureStage(project);
  if (!ctx) {
    throw new Error("the preview canvas could not be created");
  }
  const fps = Number(project && project.fps) > 0 ? Number(project.fps) : DEFAULT_FPS;
  const stream = canvas.captureStream(fps);
  const rig = attachAudio(plan, stream);
  const mimeType = pickMime();
  let recorder = null;
  try {
    recorder = new MediaRecorder(stream, { mimeType });
  } catch (_err) {
    recorder = new MediaRecorder(stream);
  }
  const chunks = [];
  recorder.ondataavailable = (event) => {
    if (event && event.data && event.data.size > 0) {
      chunks.push(event.data);
    }
  };
  const stopped = new Promise((resolve) => {
    recorder.onstop = () => resolve();
    recorder.onerror = () => resolve();
  });
  const token = ++state.playToken;
  const paint = makePainter(ctx, project, plan);
  try {
    recorder.start(250);
    await stepTimeline(plan, project, paint, {
      token,
      fps,
      onSegment: (seg) => setSegmentGain(rig, seg),
    });
    await sleep(150);
  } finally {
    try {
      if (recorder.state !== "inactive") {
        recorder.stop();
      }
    } catch (_err) {
      /* the blob may still hold frames */
    }
    await stopped;
    pauseAllVideos();
    detachAudio(rig);
  }
  const type = String(recorder.mimeType || mimeType).split(";")[0];
  return new Blob(chunks, { type: type || "video/webm" });
}

/**
 * Hand a blob to the browser as a download.
 * @param {Blob} blob The recorded media.
 * @param {string} name File name.
 * @returns {void}
 */
function downloadBlob(blob, name) {
  try {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = name || "ez-edit.webm";
    link.rel = "noopener";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => {
      try {
        URL.revokeObjectURL(url);
      } catch (_err) {
        /* the tab close frees it */
      }
    }, 5000);
  } catch (_err) {
    /* a blocked download must not fail the job report */
  }
}

/**
 * Filesystem-safe stem for a project title.
 * @param {object} project The edit project.
 * @returns {string} A slug.
 */
function slugFor(project) {
  const raw = String((project && project.title) || (project && project.id) || "edit");
  const slug = raw
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug || "edit";
}

/* ------------------------------------------------------------------ MCP --- */

/**
 * Loopback host of a URL, or "" when the endpoint is not laptop-local.
 * @param {string} raw An http(s) URL as typed.
 * @returns {string} The hostname when allowed, else "".
 */
function loopbackHost(raw) {
  try {
    const parsed = new URL(String(raw || "").trim());
    if (parsed.protocol !== "http:") {
      return "";
    }
    const host = String(parsed.hostname || "").replace(/^\[|\]$/g, "").toLowerCase();
    return LOOPBACK_HOSTS.indexOf(host) >= 0 ? host : "";
  } catch (_err) {
    return "";
  }
}

/**
 * Stable short id for a local MCP endpoint (host + port).
 * @param {string} raw An http(s) URL.
 * @returns {string} The server_id sent in LocalToolDef.
 */
function serverIdFromUrl(raw) {
  try {
    const parsed = new URL(String(raw || "").trim());
    const host = String(parsed.hostname || "").replace(/^\[|\]$/g, "").toLowerCase();
    const port = parsed.port || (parsed.protocol === "https:" ? "443" : "80");
    return (host + "-" + port).replace(/[^a-z0-9.-]+/g, "-");
  } catch (_err) {
    return "local-" + newId().slice(0, 8);
  }
}

/**
 * Split an SSE body into its JSON payloads.
 * @param {string} text Raw response text.
 * @returns {object[]} Parsed payloads, in arrival order.
 */
function parseSse(text) {
  const payloads = [];
  String(text || "")
    .split(/\r?\n/)
    .forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data:")) {
        return;
      }
      const chunk = trimmed.slice(5).trim();
      if (!chunk || chunk === "[DONE]") {
        return;
      }
      try {
        payloads.push(JSON.parse(chunk));
      } catch (_err) {
        /* ignore keep-alive and comment lines */
      }
    });
  return payloads;
}

/**
 * Pull the JSON-RPC answer for one id out of a JSON or SSE body.
 * @param {string} text Raw response text.
 * @param {string} contentType Content-Type header.
 * @param {number|string} id Request id to match.
 * @returns {object} The matching payload, or `{}`.
 */
function parseMcpBody(text, contentType, id) {
  const raw = String(text || "");
  const isSse = /text\/event-stream/i.test(String(contentType || "")) || /^\s*(event:|data:)/m.test(raw);
  if (isSse) {
    const payloads = parseSse(raw);
    const match = payloads.filter((row) => row && (row.id === id || String(row.id) === String(id)));
    if (match.length) {
      return match[match.length - 1];
    }
    const answered = payloads.filter((row) => row && (row.result || row.error));
    return answered.length ? answered[answered.length - 1] : {};
  }
  if (!raw.trim()) {
    return {};
  }
  try {
    return JSON.parse(raw) || {};
  } catch (_err) {
    return {};
  }
}

/**
 * POST one JSON-RPC message to a local MCP endpoint.
 * @param {string} url The Streamable-HTTP endpoint.
 * @param {object} payload The JSON-RPC message.
 * @param {string} sessionId Mcp-Session-Id from initialize, when any.
 * @returns {Promise<object>} `{body, sessionId}`.
 */
async function mcpPost(url, payload, sessionId) {
  const headers = {
    "Content-Type": "application/json",
    Accept: MCP_ACCEPT,
  };
  if (sessionId) {
    headers["Mcp-Session-Id"] = sessionId;
  }
  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  let text = "";
  try {
    text = await response.text();
  } catch (_err) {
    text = "";
  }
  if (!response.ok) {
    throw apiError({ error: "MCP HTTP " + response.status + " from " + url }, url, response.status);
  }
  const contentType = response.headers ? response.headers.get("content-type") || "" : "";
  let returned = "";
  try {
    returned = (response.headers && response.headers.get("mcp-session-id")) || "";
  } catch (_err) {
    returned = "";
  }
  return {
    body: parseMcpBody(text, contentType, payload.id),
    sessionId: returned || sessionId || "",
  };
}

/**
 * The Streamable-HTTP handshake: initialize, then notifications/initialized.
 * @param {string} url The MCP endpoint (must already be loopback-checked).
 * @returns {Promise<string>} The session id, or "".
 */
async function mcpInitialize(url) {
  const first = await mcpPost(
    url,
    {
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: MCP_PROTOCOL_VERSION,
        capabilities: {},
        clientInfo: { name: "ez-edit-panel", version: "1" },
      },
    },
    "",
  );
  if (first.body && first.body.error) {
    throw apiError({ error: String(first.body.error.message || "initialize failed") }, url);
  }
  try {
    await mcpPost(url, { jsonrpc: "2.0", method: "notifications/initialized" }, first.sessionId);
  } catch (_err) {
    /* some servers close the stream after initialize */
  }
  return first.sessionId;
}

/**
 * tools/list against a local MCP endpoint.
 * @param {string} url The MCP endpoint.
 * @param {string} sessionId Session id from initialize.
 * @returns {Promise<object[]>} The tool descriptors.
 */
async function mcpListTools(url, sessionId) {
  const reply = await mcpPost(url, { jsonrpc: "2.0", id: 2, method: "tools/list", params: {} }, sessionId);
  if (reply.body && reply.body.error) {
    throw apiError({ error: String(reply.body.error.message || "tools/list failed") }, url);
  }
  const tools = reply.body && reply.body.result ? reply.body.result.tools : null;
  return Array.isArray(tools) ? tools : [];
}

/**
 * tools/call against a local MCP endpoint and flatten the answer to text.
 * @param {string} url The MCP endpoint.
 * @param {string} name Tool name.
 * @param {object} args Tool arguments.
 * @returns {Promise<string>} The tool output as text.
 */
async function mcpCallTool(url, name, args) {
  const reply = await mcpPost(
    url,
    { jsonrpc: "2.0", id: 3, method: "tools/call", params: { name, arguments: args || {} } },
    "",
  );
  if (reply.body && reply.body.error) {
    throw apiError({ error: String(reply.body.error.message || "tools/call failed") }, url);
  }
  const result = (reply.body && reply.body.result) || {};
  const content = Array.isArray(result.content) ? result.content : [];
  const texts = content
    .filter((part) => part && typeof part.text === "string")
    .map((part) => part.text);
  if (texts.length) {
    return texts.join("\n");
  }
  if (typeof result.text === "string") {
    return result.text;
  }
  try {
    return JSON.stringify(result);
  } catch (_err) {
    return "";
  }
}

/**
 * Stored local MCP servers.
 * @returns {object[]} Rows of `{url, id, enabled, tools, error, updated_at}`.
 */
function loadServers() {
  const rows = readJsonPref(PREF_SERVERS, []);
  if (!Array.isArray(rows)) {
    return [];
  }
  return rows
    .filter((row) => row && typeof row.url === "string")
    .map((row) => ({
      url: row.url,
      id: String(row.id || serverIdFromUrl(row.url)),
      enabled: row.enabled !== false,
      tools: Array.isArray(row.tools) ? row.tools : [],
      error: String(row.error || ""),
      updated_at: String(row.updated_at || ""),
    }));
}

/**
 * Persist the local MCP server list.
 * @returns {void}
 */
function saveServers() {
  writeJsonPref(PREF_SERVERS, state.servers);
}

/* ---------------------------------------------------------------- render --- */

/**
 * Repaint the status line (busy text wins, then the note, then state).
 * @returns {void}
 */
function renderStatus() {
  if (!ui || !ui.status) {
    return;
  }
  const bits = [];
  if (state.enabled === false) {
    bits.push("editing lane disabled (EZ_EDIT_ENABLED=0)");
  }
  if (state.project) {
    bits.push(String(state.project.title || state.project.id) + " / " + state.mode);
    bits.push(
      (Array.isArray(state.project.clips) ? state.project.clips.length : 0) + " clips",
    );
  } else {
    bits.push("no project loaded");
  }
  if (state.execConnected) {
    bits.push("executor on");
  }
  if (state.relayOn) {
    bits.push("mcp relay on");
  }
  if (state.chatBusy || state.execBusy || state.relayBusy || state.busy) {
    bits.push("busy: " + (state.chatBusy ? "chat" : state.execBusy ? "render" : state.relayBusy ? "relay" : state.busy));
  }
  if (state.note) {
    bits.push(state.note);
  }
  ui.status.textContent = bits.join(" | ");
}

/**
 * Repaint the transcript.
 * @returns {void}
 */
function renderChat() {
  if (!ui || !ui.chatList) {
    return;
  }
  ui.chatList.replaceChildren();
  state.thread.forEach((row) => {
    const line = makeEl("div", "ez-edit-msg is-" + row.kind, row.text);
    ui.chatList.appendChild(line);
  });
  ui.chatList.scrollTop = ui.chatList.scrollHeight;
}

/**
 * Repaint the server/client mode chips.
 * @returns {void}
 */
function renderMode() {
  if (!ui || !Array.isArray(ui.modeButtons)) {
    return;
  }
  ui.modeButtons.forEach((button) => {
    const on = button.dataset.mode === state.mode;
    button.classList.toggle("is-active", on);
    button.setAttribute("aria-pressed", on ? "true" : "false");
  });
}

/**
 * Add one transcript row.
 * @param {string} kind "user" | "assistant" | "tool" | "error".
 * @param {string} text Row text.
 * @returns {void}
 */
function pushThread(kind, text) {
  state.thread.push({ kind: String(kind || "assistant"), text: String(text || "") });
  if (state.thread.length > 200) {
    state.thread.splice(0, state.thread.length - 200);
  }
  renderChat();
}

/**
 * Append a table row of plain text cells.
 * @param {HTMLElement} body The tbody.
 * @param {string[]} cells Cell texts.
 * @param {string} [className] Extra class.
 * @returns {void}
 */
function appendRow(body, cells, className) {
  const tr = document.createElement("tr");
  if (className) {
    tr.className = className;
  }
  cells.forEach((cell) => {
    const td = document.createElement("td");
    td.textContent = String(cell == null ? "" : cell);
    tr.appendChild(td);
  });
  body.appendChild(tr);
}

/**
 * Repaint the clips, overlays, and captions tables.
 * @returns {void}
 */
function renderTimeline() {
  if (!ui) {
    return;
  }
  const project = state.project;
  const clips = project && Array.isArray(project.clips) ? project.clips : [];
  ui.clipsBody.replaceChildren();
  if (!clips.length) {
    appendRow(ui.clipsBody, ["no clips yet"], "is-empty");
  }
  clips.forEach((clip, index) => {
    const transition = clip.transition
      ? String(clip.transition.kind || "cut") + " " + formatSeconds(clip.transition.duration_s)
      : "cut";
    appendRow(ui.clipsBody, [
      index + 1,
      clip.label || clip.id || "clip",
      formatSeconds(clip.in_s) + " - " + formatSeconds(clip.out_s),
      "T" + (Number(clip.track) || 0),
      transition,
    ]);
  });

  const overlays = project && Array.isArray(project.overlays) ? project.overlays : [];
  ui.overlaysBody.replaceChildren();
  if (!overlays.length) {
    appendRow(ui.overlaysBody, ["none"], "is-empty");
  }
  overlays.forEach((overlay) => {
    appendRow(ui.overlaysBody, [
      overlay.kind || "text",
      overlay.text || overlay.source || "",
      "@" + formatSeconds(overlay.at_s) + " for " + formatSeconds(overlay.dur_s),
    ]);
  });

  const captions = project && Array.isArray(project.captions) ? project.captions : [];
  ui.captionsBody.replaceChildren();
  if (!captions.length) {
    appendRow(ui.captionsBody, ["none"], "is-empty");
  }
  captions.forEach((caption) => {
    appendRow(ui.captionsBody, [
      caption.text || "",
      "@" + formatSeconds(caption.at_s) + " for " + formatSeconds(caption.dur_s),
    ]);
  });
}

/**
 * Repaint the jobs table.
 * @returns {void}
 */
function renderJobs() {
  if (!ui) {
    return;
  }
  const jobs = Array.isArray(state.jobs) ? state.jobs : [];
  ui.jobsBody.replaceChildren();
  if (!jobs.length) {
    appendRow(ui.jobsBody, ["no jobs"], "is-empty");
    return;
  }
  jobs
    .slice()
    .reverse()
    .slice(0, 25)
    .forEach((job) => {
      appendRow(
        ui.jobsBody,
        [job.kind || "?", job.state || "?", job.mode || "", String(job.message || "").slice(0, 120)],
        job.state === "failed" ? "is-bad" : job.state === "ok" ? "is-ok" : "",
      );
    });
}

/**
 * Repaint the laptop-local MCP server list.
 * @returns {void}
 */
function renderMcp() {
  if (!ui || !ui.mcpList) {
    return;
  }
  ui.mcpList.replaceChildren();
  const rows = Array.isArray(state.servers) ? state.servers : [];
  if (!rows.length) {
    ui.mcpList.appendChild(
      makeEl("p", "ez-edit-hint", "Add a laptop-local MCP endpoint (http://127.0.0.1:<port>/<path>)."),
    );
  }
  rows.forEach((server) => {
    const row = makeEl("div", "ez-edit-mcp-row" + (server.error ? " is-bad" : ""));
    const label = makeEl(
      "span",
      "ez-edit-mcp-url",
      server.url + " (" + (server.tools ? server.tools.length : 0) + " tools)",
    );
    row.appendChild(label);
    const enable = document.createElement("input");
    enable.type = "checkbox";
    enable.checked = server.enabled !== false;
    enable.setAttribute("aria-label", "Enable " + server.url);
    enable.addEventListener("change", () => {
      server.enabled = enable.checked;
      saveServers();
      renderStatus();
    });
    row.appendChild(enable);
    row.appendChild(makeButton("Discover", "ez-edit-btn ez-edit-btn-sm", () => {
      discoverServer(server);
    }));
    row.appendChild(makeButton("Remove", "ez-edit-btn ez-edit-btn-sm", () => {
      state.servers = state.servers.filter((item) => item !== server);
      saveServers();
      renderMcp();
      renderStatus();
    }));
    row.appendChild(makeEl("span", "ez-edit-mcp-note", server.error || server.updated_at || ""));
    ui.mcpList.appendChild(row);
  });
}

/**
 * Repaint every section.
 * @returns {void}
 */
function renderAll() {
  renderStatus();
  renderChat();
  renderMode();
  renderTimeline();
  renderJobs();
  renderMcp();
}

/* --------------------------------------------------------------- actions --- */

/**
 * Refuse an action while the lane is disabled or a run is in flight.
 * @param {string} label Action name for the status line.
 * @returns {boolean} True when the caller may proceed.
 */
function allowAction(label) {
  if (state.enabled === false) {
    setStatus("Editing lane is disabled (EZ_EDIT_ENABLED=0)");
    return false;
  }
  if (state.busy) {
    setStatus("Busy: " + state.busy);
    return false;
  }
  state.busy = label;
  renderStatus();
  return true;
}

/**
 * Clear the busy flag and repaint.
 * @returns {void}
 */
function endAction() {
  state.busy = "";
  renderStatus();
}

/**
 * Load state for the current (or most recent) project.
 * @param {object} [opts] `{quiet: true}` keeps the status line untouched.
 * @returns {Promise<void>} Resolves once painted.
 */
async function refreshState(opts) {
  const quiet = Boolean(opts && opts.quiet);
  try {
    const query = "?project_id=" + encodeURIComponent(state.projectId || "");
    const data = await fetchJson("/ez_edit/state" + query);
    if (data && data.ok === false) {
      state.enabled = false;
      if (!quiet) {
        setStatus(String(data.error || "route refused"));
      }
      return;
    }
    state.enabled = true;
    state.project = data.project || null;
    state.jobs = Array.isArray(data.jobs) ? data.jobs : [];
    if (state.project && state.project.id) {
      state.projectId = state.project.id;
      state.mode = loadMode(state.projectId);
    }
    if (!quiet) {
      state.note = "";
    }
    renderAll();
  } catch (err) {
    state.enabled = Number(err && err.status) === 403 ? false : state.enabled;
    if (!quiet) {
      setStatus(errLine(err));
    }
    renderAll();
  }
}

/**
 * Send one chat turn (or a canned instruction) to the agent.
 * @param {string} message The user message.
 * @returns {Promise<void>} Resolves when the reply is painted.
 */
async function sendChatTurn(message) {
  const text = String(message || "").trim();
  if (!text || state.chatBusy) {
    return;
  }
  pushThread("user", text);
  state.chatBusy = true;
  renderStatus();
  try {
    const data = await postJson("/ez_edit/chat", {
      message: text,
      history: Array.isArray(state.history) ? state.history : [],
      client_id: clientId(),
    });
    if (!data || data.ok === false) {
      throw apiError(data || {}, "/ez_edit/chat");
    }
    const trace = Array.isArray(data.trace) ? data.trace : [];
    trace.forEach((item) => pushThread("tool", traceLine(item)));
    const reply = String(data.reply == null ? "(no reply)" : data.reply);
    pushThread("assistant", reply);
    if (Array.isArray(data.history)) {
      state.history = data.history;
    } else {
      state.history = state.history.concat([
        { role: "user", content: text },
        { role: "assistant", content: reply },
      ]);
    }
  } catch (err) {
    pushThread("error", errLine(err));
  } finally {
    state.chatBusy = false;
  }
  await refreshState({ quiet: true });
  renderStatus();
}

/**
 * Ask for a title/fps/size and create a project through the ops route.
 * @returns {Promise<void>} Resolves when the project is loaded.
 */
async function newProject() {
  if (!allowAction("new project")) {
    return;
  }
  let title = "";
  let fps = "";
  let width = "";
  let height = "";
  try {
    title = window.prompt("Project title", "Untitled edit");
    if (title == null) {
      endAction();
      return;
    }
    fps = window.prompt("Frames per second", String(DEFAULT_FPS));
    width = window.prompt("Frame width", "1280");
    height = window.prompt("Frame height", "720");
  } catch (_err) {
    endAction();
    setStatus("This browser blocked the prompt dialog");
    return;
  }
  const ops = [
    {
      op: "project_create",
      args: {
        title: String(title || "Untitled edit"),
        fps: Number(fps) > 0 ? Number(fps) : DEFAULT_FPS,
        width: clampSize(width, 16, 3840, 1280),
        height: clampSize(height, 16, 2160, 720),
      },
    },
  ];
  try {
    const data = await postJson("/ez_edit/ops", { project_id: "", ops });
    if (!data || data.ok === false) {
      throw apiError(data || {}, "/ez_edit/ops");
    }
    state.project = data.project || null;
    state.projectId = (data.project && data.project.id) || "";
    state.mode = loadMode(state.projectId);
    setStatus("Project created");
  } catch (err) {
    setStatus(errLine(err));
  }
  endAction();
  await refreshState({ quiet: true });
}

/**
 * Import a media file under the output dir as a clip.
 * @param {string} rawPath Path as typed.
 * @returns {Promise<void>} Resolves when the state refreshed.
 */
async function importClip(rawPath) {
  const path = String(rawPath || "").trim();
  if (!path) {
    setStatus("Type a media path under the Comfy output dir first");
    return;
  }
  if (!allowAction("import")) {
    return;
  }
  try {
    const data = await postJson("/ez_edit/import", { path, label: "", track: 0 });
    if (!data || data.ok === false) {
      throw apiError(data || {}, "/ez_edit/import");
    }
    setStatus("Imported " + String((data.clip && data.clip.label) || path));
  } catch (err) {
    setStatus(errLine(err));
  }
  endAction();
  await refreshState({ quiet: true });
}

/**
 * Queue a render on the Spark or for the browser executor.
 * @param {string} mode "server" or "client".
 * @returns {Promise<void>} Resolves when the job row is queued.
 */
async function startRender(mode) {
  const kind = mode === "client" ? "client" : "server";
  if (!allowAction("render " + kind)) {
    return;
  }
  const body = { project_id: state.projectId, mode: kind };
  if (kind === "client") {
    body.client_id = clientId();
  }
  try {
    const data = await postJson("/ez_edit/render", body);
    if (!data || data.ok === false) {
      throw apiError(data || {}, "/ez_edit/render");
    }
    const job = data.job || {};
    setStatus(
      kind === "client"
        ? "Client job " + String(job.id || "?") + " queued - connect the executor to run it"
        : "Server job " + String(job.id || "?") + " queued",
    );
  } catch (err) {
    setStatus(errLine(err));
  }
  endAction();
  await refreshState({ quiet: true });
}

/**
 * Ask the agent to export the EDL (the EDL handoff lives behind the chat tool).
 * @returns {Promise<void>} Resolves when the agent answers.
 */
async function exportEdl() {
  const name = state.projectId || "the current project";
  await sendChatTurn("Export the EDL for project " + name + " and tell me the file path.");
}

/**
 * Put one clip in the visible stage, keeping the overlay canvas on top.
 * @param {HTMLVideoElement|null} video The clip element to show.
 * @returns {void}
 */
function showStageVideo(video) {
  if (!ui || !ui.stage) {
    return;
  }
  try {
    ui.stage.replaceChildren();
    if (video) {
      ui.stage.appendChild(video);
    }
    if (ui.canvas && ui.canvas.parentNode !== ui.stage) {
      ui.stage.appendChild(ui.canvas);
    }
  } catch (_err) {
    /* the stage is decorative */
  }
}

/* ------------------------------------------------------- client executor --- */

/**
 * Render one exec_client job in this browser and report it back.
 * @param {object} job The JobRecord claimed from /ez_edit/exec/pending.
 * @returns {Promise<void>} Resolves once the result is posted.
 */
async function runClientJob(job) {
  state.execBusy = true;
  setStatus("Rendering " + String(job.id || "?") + " in the browser");
  const jobId = String(job.id || "");
  let ok = false;
  let outPath = "";
  let message = "";
  try {
    if (job.project_id && job.project_id !== state.projectId) {
      state.projectId = String(job.project_id);
      await refreshState({ quiet: true });
    }
    const plan = buildPlan(state.project);
    if (!plan.length) {
      throw new Error("the project has no clips to render");
    }
    const blob = await recordTimeline(plan, state.project);
    if (!blob || blob.size <= 0) {
      throw new Error("MediaRecorder produced no data");
    }
    downloadBlob(blob, slugFor(state.project) + "-" + (jobId || newId().slice(0, 8)) + ".webm");
    ok = true;
    message = "webm recorded in browser (download)";
  } catch (err) {
    message = errLine(err);
  }
  try {
    await postJson("/ez_edit/exec/result", {
      job_id: jobId,
      ok,
      out_path: outPath,
      message,
    });
  } catch (err) {
    setStatus("Could not report the job: " + errLine(err));
  }
  state.execBusy = false;
  await refreshState({ quiet: true });
  setStatus((ok ? "Client render done: " : "Client render failed: ") + message);
}

/**
 * Claim and run any pending browser jobs for this tab.
 * @returns {Promise<void>} Resolves when the queue is drained.
 */
async function handleExecJobs() {
  if (state.execBusy) {
    return;
  }
  state.execBusy = true;
  try {
    const data = await fetchJson(
      "/ez_edit/exec/pending?client_id=" + encodeURIComponent(clientId()),
    );
    const jobs = data && Array.isArray(data.jobs) ? data.jobs : [];
    state.seenJobs = state.seenJobs || new Set();
    for (let i = 0; i < jobs.length; i += 1) {
      const job = jobs[i];
      const id = String((job && job.id) || "");
      if (!id || state.seenJobs.has(id)) {
        continue;
      }
      state.seenJobs.add(id);
      state.execBusy = false;
      await runClientJob(job);
      state.execBusy = true;
    }
  } catch (_err) {
    /* a dropped poll tick is not worth surfacing */
  } finally {
    state.execBusy = false;
  }
}

/* ------------------------------------------------------------ local MCP --- */

/**
 * Run the handshake + tools/list for one server, then sync the tool list.
 * @param {object} server The server row.
 * @returns {Promise<void>} Resolves when synced or refused.
 */
async function discoverServer(server) {
  if (!loopbackHost(server.url)) {
    server.error = "refused: only loopback hosts (127.0.0.1, localhost, ::1) are allowed";
    server.tools = [];
    saveServers();
    renderMcp();
    setStatus("Refused a non-loopback MCP endpoint");
    return;
  }
  try {
    const sessionId = await mcpInitialize(server.url);
    const tools = await mcpListTools(server.url, sessionId);
    server.tools = tools.map((tool) => ({
      server_id: serverIdFromUrl(server.url),
      server_url: server.url,
      name: String((tool && tool.name) || ""),
      description: String((tool && tool.description) || ""),
      input_schema: (tool && tool.inputSchema) || {},
    }));
    server.error = "";
    server.updated_at = new Date().toISOString();
    saveServers();
    const data = await postJson("/ez_edit/local_tools/sync", {
      client_id: clientId(),
      tools: server.tools,
    });
    if (!data || data.ok === false) {
      throw apiError(data || {}, "/ez_edit/local_tools/sync");
    }
    setStatus("Synced " + server.tools.length + " tool(s) from " + server.id);
    if (server.enabled !== false) {
      state.relayOn = true;
      ensurePolling();
    }
  } catch (err) {
    server.error = errLine(err);
    saveServers();
    setStatus("MCP discover failed: " + server.error);
  }
  renderMcp();
  renderStatus();
}

/**
 * Add a local MCP endpoint after the loopback guardrail.
 * @param {string} raw URL as typed.
 * @returns {void}
 */
function addServer(raw) {
  const url = String(raw || "").trim();
  if (!url) {
    setStatus("Type an MCP endpoint URL first");
    return;
  }
  if (!loopbackHost(url)) {
    setStatus("Refused " + url + ": only 127.0.0.1, localhost, and ::1 are allowed");
    state.servers = state.servers.concat([
      {
        url,
        id: serverIdFromUrl(url),
        enabled: false,
        tools: [],
        error: "refused: host is not loopback",
        updated_at: new Date().toISOString(),
      },
    ]);
    saveServers();
    renderMcp();
    return;
  }
  const id = serverIdFromUrl(url);
  if (state.servers.filter((row) => row.url === url).length) {
    setStatus("Already listed: " + id);
    return;
  }
  state.servers = state.servers.concat([
    { url, id, enabled: true, tools: [], error: "", updated_at: "" },
  ]);
  saveServers();
  renderMcp();
  setStatus("Added " + id + " - press Discover to sync its tools");
}

/**
 * Execute queued local tool calls on behalf of the agent.
 * @returns {Promise<void>} Resolves when the batch is answered.
 */
async function handleRelayCalls() {
  state.relayBusy = true;
  renderStatus();
  try {
    const data = await fetchJson(
      "/ez_edit/local_tools/pending?client_id=" + encodeURIComponent(clientId()),
    );
    const calls = data && Array.isArray(data.calls) ? data.calls : [];
    for (let i = 0; i < calls.length; i += 1) {
      const call = calls[i] || {};
      const callId = String(call.call_id || "");
      let ok = false;
      let text = "";
      try {
        if (!loopbackHost(call.server_url)) {
          throw new Error("refused: server_url host is not loopback");
        }
        text = await mcpCallTool(call.server_url, String(call.name || ""), call.args || {});
        ok = true;
      } catch (err) {
        text = errLine(err);
      }
      try {
        await postJson("/ez_edit/local_tools/result", {
          call_id: callId,
          ok,
          text: String(text || "").slice(0, 20000),
        });
      } catch (err) {
        setStatus("Could not report a local tool call: " + errLine(err));
      }
    }
  } catch (_err) {
    /* the agent may simply have nothing queued */
  } finally {
    state.relayBusy = false;
    renderStatus();
  }
}

/* ------------------------------------------------------------- poll loop --- */

/**
 * One poll tick: browser jobs, relay calls, and a slow state refresh.
 * @returns {Promise<void>} Resolves when the tick is done.
 */
async function tick() {
  state.tick += 1;
  if (state.execConnected) {
    await handleExecJobs();
  }
  if (state.relayOn) {
    await handleRelayCalls();
  }
  if (state.enabled !== false && state.tick % STATE_EVERY === 0) {
    await refreshState({ quiet: true });
  }
}

/**
 * Start the 1s poll loop unless it is already running.
 * @returns {void}
 */
function ensurePolling() {
  if (state.timer) {
    return;
  }
  state.timer = window.setInterval(() => {
    tick().catch(() => undefined);
  }, POLL_MS);
}

/**
 * Toggle the browser executor that claims exec_client jobs.
 * @returns {void}
 */
function toggleExecutor() {
  state.execConnected = !state.execConnected;
  if (state.execConnected) {
    state.seenJobs = new Set();
    ensurePolling();
    handleExecJobs().catch(() => undefined);
    setStatus("Executor connected as " + clientId().slice(0, 8));
  } else {
    setStatus("Executor disconnected");
  }
  renderStatus();
}

/**
 * Toggle the relay that answers agent-dispatched local tool calls.
 * @returns {void}
 */
function toggleRelay() {
  state.relayOn = !state.relayOn;
  if (state.relayOn) {
    ensurePolling();
    handleRelayCalls().catch(() => undefined);
  }
  renderStatus();
}

/**
 * Play or stop the timeline preview.
 * @returns {Promise<void>} Resolves when playback ends.
 */
async function previewToggle() {
  if (state.playing) {
    state.playToken += 1;
    state.playing = false;
    pauseAllVideos();
    showStageVideo(null);
    renderStatus();
    return;
  }
  const plan = buildPlan(state.project);
  if (!plan.length) {
    setStatus("Nothing to play: import a clip or create a project first");
    return;
  }
  const ctx = ensureStage(state.project);
  if (!ctx) {
    setStatus("This browser has no canvas 2d context");
    return;
  }
  const fps =
    Number(state.project && state.project.fps) > 0 ? Number(state.project.fps) : DEFAULT_FPS;
  const token = ++state.playToken;
  state.playing = true;
  setStatus("Preview running - press Play again to stop");
  const rig = attachAudio(plan, null);
  const paint = makePainter(ctx, state.project, plan);
  try {
    await stepTimeline(plan, state.project, paint, {
      token,
      fps,
      onSegment: (seg) => setSegmentGain(rig, seg),
    });
  } catch (err) {
    setStatus("Preview stopped: " + errLine(err));
  } finally {
    pauseAllVideos();
    detachAudio(rig);
    state.playing = false;
    showStageVideo(null);
    renderStatus();
  }
}

/**
 * Switch render mode for the current project.
 * @param {string} mode "server" or "client".
 * @returns {void}
 */
function setMode(mode) {
  state.mode = mode === "client" ? "client" : "server";
  saveMode(state.projectId, state.mode);
  renderMode();
  renderStatus();
}

/* ---------------------------------------------------------------- mount --- */

/**
 * Build a small key/value table with a caption.
 * @param {string} caption Heading shown above the table.
 * @param {string[]} heads Column headers.
 * @returns {object} `{wrap, body}` where body is the tbody.
 */
function makeTable(caption, heads) {
  const wrap = makeEl("div", "ez-edit-table-wrap");
  wrap.appendChild(makeEl("h4", "ez-edit-subhead", caption));
  const table = document.createElement("table");
  table.className = "ez-edit-table";
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  heads.forEach((head) => {
    const th = document.createElement("th");
    th.textContent = head;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  const body = document.createElement("tbody");
  table.appendChild(thead);
  table.appendChild(body);
  wrap.appendChild(table);
  return { wrap, body };
}

/**
 * Render the editing panel into el.
 * @param {HTMLElement} el Host element (sidebar tab or floating aside body).
 * @returns {void}
 */
function mount(el) {
  if (!el) {
    return;
  }
  ensureCss();
  el.replaceChildren();
  el.classList.add("ez-edit");
  el.tabIndex = 0;

  /** @type {object} */
  const local = { root: el };

  local.status = makeEl("p", "ez-edit-status", "loading...");
  el.appendChild(local.status);

  // --- chat ---
  const chat = makeSection("Agent chat");
  local.chatList = makeEl("div", "ez-edit-chat");
  local.chatList.setAttribute("aria-live", "polite");
  chat.body.appendChild(local.chatList);
  const chatRow = makeEl("div", "ez-edit-row");
  local.chatInput = document.createElement("textarea");
  local.chatInput.className = "ez-edit-input ez-edit-chat-input";
  local.chatInput.rows = 2;
  local.chatInput.placeholder = "Ask the editing agent to cut, trim, caption...";
  local.chatInput.setAttribute("aria-label", "Message for the editing agent");
  local.chatInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      const text = local.chatInput.value;
      local.chatInput.value = "";
      sendChatTurn(text);
    }
  });
  chatRow.appendChild(local.chatInput);
  chatRow.appendChild(
    makeButton("Send", "ez-edit-btn", () => {
      const text = local.chatInput.value;
      local.chatInput.value = "";
      sendChatTurn(text);
    }),
  );
  chatRow.appendChild(
    makeButton("Clear", "ez-edit-btn", () => {
      state.thread = [];
      state.history = [];
      renderChat();
    }),
  );
  chat.body.appendChild(chatRow);
  el.appendChild(chat.section);

  // --- timeline ---
  const timeline = makeSection("Timeline");
  const modeRow = makeEl("div", "ez-edit-row");
  modeRow.appendChild(makeEl("span", "ez-edit-label", "Render"));
  local.modeButtons = ["server", "client"].map((mode) => {
    const chip = makeButton(mode === "server" ? "Server" : "Client", "ez-edit-btn ez-edit-chip", () => {
      setMode(mode);
    });
    chip.dataset.mode = mode;
    modeRow.appendChild(chip);
    return chip;
  });
  modeRow.appendChild(
    makeButton("Refresh", "ez-edit-btn", () => {
      refreshState();
    }),
  );
  modeRow.appendChild(
    makeButton("New project", "ez-edit-btn", () => {
      newProject();
    }),
  );
  timeline.body.appendChild(modeRow);

  const importField = makeField("Media path", "text", "", "edit/imports/clip01.mp4");
  timeline.body.appendChild(importField.row);
  const importRow = makeEl("div", "ez-edit-row");
  importRow.appendChild(
    makeButton("Import", "ez-edit-btn", () => {
      importClip(importField.input.value);
    }),
  );
  importRow.appendChild(
    makeButton("Play", "ez-edit-btn", () => {
      previewToggle();
    }),
  );
  importRow.appendChild(
    makeButton("Render server", "ez-edit-btn", () => {
      startRender("server");
    }),
  );
  importRow.appendChild(
    makeButton("Render client", "ez-edit-btn", () => {
      startRender("client");
    }),
  );
  importRow.appendChild(
    makeButton("Export EDL", "ez-edit-btn", () => {
      exportEdl();
    }),
  );
  timeline.body.appendChild(importRow);

  local.stage = makeEl("div", "ez-edit-stage");
  local.canvas = document.createElement("canvas");
  local.canvas.className = "ez-edit-canvas";
  local.canvas.width = 1280;
  local.canvas.height = 720;
  local.stage.appendChild(local.canvas);
  timeline.body.appendChild(local.stage);

  const clips = makeTable("Clips", ["#", "Label", "In / Out", "Track", "Transition"]);
  local.clipsBody = clips.body;
  timeline.body.appendChild(clips.wrap);
  const overlays = makeTable("Overlays", ["Kind", "Text / Source", "Timing"]);
  local.overlaysBody = overlays.body;
  timeline.body.appendChild(overlays.wrap);
  const captions = makeTable("Captions", ["Text", "Timing"]);
  local.captionsBody = captions.body;
  timeline.body.appendChild(captions.wrap);
  const jobs = makeTable("Jobs", ["Kind", "State", "Mode", "Message"]);
  local.jobsBody = jobs.body;
  timeline.body.appendChild(jobs.wrap);
  el.appendChild(timeline.section);

  // --- client render + local MCP ---
  const client = makeSection("This browser");
  const execRow = makeEl("div", "ez-edit-row");
  execRow.appendChild(
    makeButton("Connect executor", "ez-edit-btn", () => {
      toggleExecutor();
    }),
  );
  execRow.appendChild(
    makeButton("Relay local tools", "ez-edit-btn", () => {
      toggleRelay();
    }),
  );
  execRow.appendChild(makeEl("span", "ez-edit-hint", "client id " + clientId().slice(0, 8)));
  client.body.appendChild(execRow);

  const mcpField = makeField(
    "MCP endpoint",
    "text",
    "",
    "http://127.0.0.1:3000/mcp",
  );
  client.body.appendChild(mcpField.row);
  const mcpRow = makeEl("div", "ez-edit-row");
  mcpRow.appendChild(
    makeButton("Add", "ez-edit-btn", () => {
      addServer(mcpField.input.value);
      mcpField.input.value = "";
    }),
  );
  mcpRow.appendChild(
    makeButton("Discover all", "ez-edit-btn", () => {
      state.servers
        .filter((row) => row.enabled !== false)
        .forEach((row) => {
          discoverServer(row);
        });
    }),
  );
  client.body.appendChild(mcpRow);
  local.mcpList = makeEl("div", "ez-edit-mcp");
  client.body.appendChild(local.mcpList);
  client.body.appendChild(
    makeEl(
      "p",
      "ez-edit-hint",
      "Only loopback endpoints (127.0.0.1, localhost, ::1) are contacted from the browser.",
    ),
  );
  el.appendChild(client.section);

  ui = local;
  renderAll();
  refreshState({ quiet: true });
}

/**
 * Create (once) the right-docked floating panel used without an extension host.
 * @returns {HTMLElement} The floating host element.
 */
function ensureFloating() {
  const existing = document.getElementById(FLOAT_ID);
  if (existing) {
    return existing;
  }
  const host = makeEl("aside", "ez-edit-floating");
  host.id = FLOAT_ID;
  host.setAttribute("hidden", "");
  host.setAttribute("role", "complementary");
  host.setAttribute("aria-label", "EZ editing lane");
  const bar = makeEl("div", "ez-edit-row ez-edit-float-bar");
  bar.appendChild(makeEl("strong", "ez-edit-title", "EZ Edit"));
  bar.appendChild(
    makeButton("Close", "ez-edit-btn", () => {
      host.setAttribute("hidden", "");
    }),
  );
  host.appendChild(bar);
  const inner = makeEl("div", "ez-edit-inner");
  host.appendChild(inner);
  document.body.appendChild(host);
  mount(inner);
  return host;
}

/**
 * Show or hide the floating panel.
 * @returns {void}
 */
function toggleFloating() {
  const host = ensureFloating();
  if (host.hasAttribute("hidden")) {
    host.removeAttribute("hidden");
  } else {
    host.setAttribute("hidden", "");
  }
}

/**
 * Open the panel: the docked sidebar tab when available, else the floating one.
 * @returns {void}
 */
function openPanel() {
  const mgr = app && app.extensionManager;
  if (state.docked && mgr) {
    const names = ["toggleSidebarTab", "activateSidebarTab", "setActiveSidebarTab"];
    for (let i = 0; i < names.length; i += 1) {
      if (typeof mgr[names[i]] === "function") {
        try {
          mgr[names[i]](TAB_ID);
          return;
        } catch (_err) {
          /* try the next shape */
        }
      }
    }
  }
  toggleFloating();
}

/**
 * Register the topbar command, trying every command API the frontend offers.
 * @returns {string} The API used, or "" when the caller must add a button.
 */
function registerTopbarCommand() {
  const store = app && app.commandStore;
  if (store && typeof store.registerCommand === "function") {
    try {
      store.registerCommand({
        id: "ez.edit.toggle",
        title: "Toggle EZ Edit panel",
        category: "ez-comfy",
        description: "Agent chat, timeline, browser render, laptop MCP",
        icon: "pi pi-video",
        execute: openPanel,
      });
      return "commandStore";
    } catch (_err) {
      /* fall through to the legacy API */
    }
  }
  if (app && typeof app.registerCommand === "function") {
    try {
      app.registerCommand({
        id: "ez.edit.toggle",
        title: "Toggle EZ Edit panel",
        handler: openPanel,
      });
      return "registerCommand";
    } catch (_err) {
      /* fall through to the header button */
    }
  }
  return "";
}

/**
 * Add a header button when no command API exists.
 * @returns {void}
 */
function addHeaderButton() {
  const menu = document.querySelector(".comfy-menu") || document.querySelector(".comfy-menu-holder");
  const host = menu || document.body;
  const button = makeButton("EZ Edit", "ez-edit-btn ez-edit-topbar-btn", openPanel);
  button.title = "Open the EZ editing lane panel";
  if (menu) {
    menu.appendChild(button);
    return;
  }
  button.classList.add("ez-edit-topbar");
  document.body.appendChild(button);
}

app.registerExtension({
  name: "ez_edit.panel",
  /**
   * Dock the panel in the right sidebar and wire the topbar entry point.
   * @returns {Promise<void>} Resolves once registered.
   */
  async setup() {
    state.servers = loadServers();
    const mgr = app && app.extensionManager;
    if (mgr && typeof mgr.registerSidebarTab === "function") {
      try {
        mgr.registerSidebarTab({
          id: TAB_ID,
          icon: "pi pi-video",
          title: "Edit",
          tooltip: "Agent chat, timeline, browser render, laptop MCP",
          type: "custom",
          render: mount,
          desktopSettings: { defaultLocation: "right" },
        });
        state.docked = true;
      } catch (_err) {
        state.docked = false;
      }
    }
    if (!registerTopbarCommand()) {
      addHeaderButton();
    }
    refreshState({ quiet: true });
  },
});

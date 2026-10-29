/**
 * @file Minimal LiteGraph-shaped world for exercising the EZQuality overlay
 * under `node --test`, with no ComfyUI frontend and no npm dependency.
 *
 * loadOverlay() reads custom_nodes/ez_quality/js/ez_quality.js, rewrites only
 * its bare frontend import specifiers to this harness's stub, and imports the
 * copy from os.tmpdir(). Everything else (the generated presets sibling) is
 * rewritten to an absolute file URL so the real module is used.
 *
 * The graph model is deliberately literal: nodes are plain objects carrying
 * `widgets_values` next to `widgets`, and graphToPrompt() serialises
 * `widgets_values` after running every widget's beforeQueued hook. That output
 * is the body the server would receive, so tests assert against it.
 */

import { existsSync } from "node:fs";
import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import {
  EZ_QUALITY_CHOICES,
  EZ_QUALITY_TABLE,
} from "../../custom_nodes/ez_quality/js/ez_quality_presets.js";
import { app, getExtensions, resetFrontend } from "./ez_frontend_stub.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const REPO_ROOT = path.resolve(HERE, "..", "..");
export const EXTENSION_JS = path.join(
  REPO_ROOT,
  "custom_nodes",
  "ez_quality",
  "js",
  "ez_quality.js",
);
const STUB_URL = new URL("./ez_frontend_stub.mjs", import.meta.url).href;

/** Overlay field -> the widget it writes, per the overlay-target map. */
export const FIELD_WIDGET = {
  steps: "steps",
  cfg: "cfg",
  unet_name: "unet_name",
  clip_name: "clip_name",
  vae_name: "vae_name",
  clip_type: "type",
};

/** Overlay field -> the node class that owns that widget. */
export const FIELD_NODE_TYPE = {
  steps: "KSampler",
  cfg: "KSampler",
  unet_name: "UNETLoader",
  clip_name: "CLIPLoader",
  vae_name: "VAELoader",
  clip_type: "CLIPLoader",
};

const IMPORT_SPEC_RE = /(\bfrom\s*|\bimport\s*)(['"])([^'"\n]+)\2/g;

/**
 * Point every import specifier at a loadable absolute URL.
 * Arguments:
 *   source - module source text
 *   sourceDir - directory the relative specifiers resolve against
 * Outputs:
 *   Returns rewritten source; frontend specifiers map to the stub.
 */
function rewriteImports(source, sourceDir) {
  return source.replace(IMPORT_SPEC_RE, (whole, head, quote, spec) => {
    if (/scripts\/(app|api)\.js$/.test(spec) || spec === "comfyui-frontend") {
      return `${head}${quote}${STUB_URL}${quote}`;
    }
    if (!spec.startsWith(".")) {
      return whole;
    }
    const resolved = path.resolve(sourceDir, spec);
    const url = existsSync(resolved)
      ? pathToFileURL(resolved).href
      : STUB_URL;
    return `${head}${quote}${url}${quote}`;
  });
}

const tmpRootPromise = mkdtemp(path.join(tmpdir(), "ez-quality-js-"));
let moduleSeq = 0;

/**
 * Load any ez_* extension fresh against a clean frontend stub.
 * Arguments:
 *   sourcePath - absolute path to the extension .js under custom_nodes/
 *   extensionName - the name it passes to app.registerExtension
 * Returns:
 *   {ext, app} - the registered extension object and the app shim.
 */
export async function loadExtension(sourcePath, extensionName) {
  const source = await readFile(sourcePath, "utf8");
  const tmpRoot = await tmpRootPromise;
  const base = path.basename(sourcePath, ".js");
  const file = path.join(tmpRoot, `${base}_under_test_${moduleSeq++}.mjs`);
  await writeFile(file, rewriteImports(source, path.dirname(sourcePath)), "utf8");
  resetFrontend();
  await import(pathToFileURL(file).href);
  const registered = getExtensions();
  const ext = registered.find((e) => e?.name === extensionName) || registered[0];
  if (!ext) {
    throw new Error(`${sourcePath} did not call app.registerExtension`);
  }
  return { ext, app };
}

/**
 * Load the overlay extension fresh against a clean frontend stub.
 * Returns:
 *   {ext, app} - the registered extension object and the app shim.
 */
export async function loadOverlay() {
  return loadExtension(EXTENSION_JS, "ez_quality.overlay");
}

/**
 * Build one widget the way LiteGraph hands it to the canvas.
 * Arguments:
 *   name, value, options - combo lists live in options.values
 */
export function makeWidget(name, value, options = {}) {
  return { name, value, options, callback: undefined };
}

/**
 * Build one LiteGraph-shaped node.
 * Arguments:
 *   type - class name (also mirrored to comfyClass, which the extension reads)
 *   widgets - makeWidget() list; widgets_values is kept parallel to it
 *   opts - {mode, title}
 */
export function makeNode(type, widgets, opts = {}) {
  return {
    id: 0,
    type,
    comfyClass: type,
    title: opts.title || type,
    mode: opts.mode ?? 0,
    widgets,
    widgets_values: widgets.map((widget) => widget.value),
    graph: null,
    setDirtyCanvas() {
      this.graph?.setDirtyCanvas?.(true, true);
    },
    change() {
      this.graph?.change?.();
    },
    getPropertyPosition: () => [0, 0],
  };
}

let graphSeq = 0;

/**
 * Wrap nodes in a graph that serialises like LiteGraph.
 * Arguments:
 *   opts - {occupancy, nodes, lab_rel}
 * Returns:
 *   The graph; each node gets an id and a .graph back-reference. addNode()
 *   appends later (a class created after the first pass) and dispatchEvent()
 *   fires the "configured" listeners the real frontend fires on the graph.
 */
export function makeGraph(opts = {}) {
  const nodes = opts.nodes || [];
  const listeners = new Map();
  /** Give a node the id + graph back-reference LiteGraph sets on add. */
  const adopt = (node, index) => {
    node.id = index + 1;
    node.graph = graph;
  };
  const graph = {
    id: `g${graphSeq++}`,
    nodes,
    extra: {
      lab_app_mode: { occupancy: opts.occupancy ?? "" },
      lab_rel: opts.lab_rel || `apps/harness_${graphSeq}.json`,
    },
    dirty: false,
    changes: 0,
    setDirtyCanvas() {
      graph.dirty = true;
    },
    change() {
      graph.changes += 1;
    },
    addEventListener(type, handler) {
      if (!listeners.has(type)) {
        listeners.set(type, []);
      }
      listeners.get(type).push(handler);
    },
    dispatchEvent(event) {
      for (const handler of listeners.get(event?.type) || []) {
        handler(event);
      }
    },
    addNode(node) {
      nodes.push(node);
      adopt(node, nodes.length - 1);
      return node;
    },
    getNodeById(id) {
      return nodes.find((n) => String(n.id) === String(id));
    },
    findNodesByType: (type) => nodes.filter((n) => n.type === type),
    graphToPrompt() {
      // LiteGraph fires beforeQueued on every widget while serialising.
      for (const node of nodes) {
        for (const widget of node.widgets || []) {
          if (typeof widget.beforeQueued === "function") {
            widget.beforeQueued();
          }
        }
      }
      const output = {};
      for (const node of nodes) {
        const inputs = {};
        (node.widgets || []).forEach((widget, index) => {
          const values = node.widgets_values;
          inputs[widget.name] =
            Array.isArray(values) && values.length === node.widgets.length
              ? values[index]
              : widget.value;
        });
        output[String(node.id)] = { class_type: node.type, inputs };
      }
      return { prompt: {}, output };
    },
  };
  nodes.forEach(adopt);
  return graph;
}

/**
 * Replay a graph load: attach to app.graph, fire nodeCreated then
 * afterConfigureGraph, which is the order the real frontend uses.
 */
export function mountGraph(graph, ext) {
  app.graph = graph;
  for (const node of graph.nodes) {
    ext.nodeCreated?.(node);
  }
  return ext.afterConfigureGraph?.();
}

/**
 * Simulate a user editing a widget in the canvas (or the App Mode panel):
 * the value lands on the widget and widgets_values, then the callback runs.
 */
export function editWidget(node, name, value) {
  const widget = node.widgets?.find((w) => w.name === name);
  if (!widget) {
    throw new Error(`no widget "${name}" on ${node.type}`);
  }
  widget.value = value;
  const index = node.widgets.indexOf(widget);
  if (index >= 0 && Array.isArray(node.widgets_values)) {
    node.widgets_values[index] = value;
  }
  if (typeof widget.callback === "function") {
    widget.callback(value, app.canvas, node);
  }
  node.change?.();
  return widget;
}

/** Pick a tier in a Quality combo the way a combo click does. */
export function pickTier(qualityNode, value) {
  return editWidget(qualityNode, "quality", value);
}

/** Current value shown by a Quality combo. */
export function comboValue(qualityNode) {
  return qualityNode.widgets?.find((w) => w.name === "quality")?.value;
}

/**
 * The live quality caption, from the graph stamp or the combo label.
 * Returns:
 *   "" when the extension stamped no caption at all.
 */
export function qualityCaption(graph, qualityNode) {
  const stamp = graph?.extra?.lab_quality_caption;
  if (typeof stamp === "string" && stamp) {
    return stamp;
  }
  const label = qualityNode?.widgets?.find((w) => w.name === "quality")?.label;
  const prefix = "Quality - ";
  if (typeof label === "string" && label.startsWith(prefix)) {
    return label.slice(prefix.length);
  }
  return "";
}

/** Widgets of one class on the graph. */
export function nodesOfType(graph, type) {
  return graph.nodes.filter((n) => n.type === type);
}

/** Read a widget value straight off the node (what the combo/panel shows). */
export function widgetValue(node, name) {
  return node.widgets?.find((w) => w.name === name)?.value;
}

/** Requested value for one overlay field of a tier, or null. */
export function tierField(family, tier, field) {
  return EZ_QUALITY_TABLE?.[family]?.[tier]?.[field] ?? null;
}

/** Every non-null file a family's tiers can ask a loader to select. */
export function familyCatalog(family) {
  const out = new Set();
  for (const tier of Object.values(EZ_QUALITY_TABLE?.[family] || {})) {
    for (const value of Object.values(tier || {})) {
      if (typeof value === "string" && value.endsWith(".safetensors")) {
        out.add(value);
      }
    }
  }
  return Array.from(out);
}

function without(list, drop) {
  const gone = new Set([].concat(drop || []));
  return list.filter((value) => !gone.has(value));
}

/**
 * Build a studio graph: Quality combo(s), N KSamplers, and one loader of each
 * class, authored from an explicit field map.
 * Arguments:
 *   spec - {occupancy, family, authored, samplers, loaders, qualities,
 *          qualityMode, drop, lab_rel}
 *     authored  - {steps, cfg, unet_name, clip_name, vae_name, clip_type}
 *     drop      - {field: value|[values]} removed from that loader's combo list
 */
export function makeStudioGraph(spec = {}) {
  const family = spec.family || spec.occupancy || "klein";
  const authored = spec.authored || {};
  const samplers = spec.samplers ?? 1;
  const loaders = spec.loaders ?? 1;
  const qualities = spec.qualities || ["lab"];
  const drop = spec.drop || {};

  const unetCatalog = without(
    Array.from(new Set([...familyCatalog(family), authored.unet_name].filter(Boolean))),
    drop.unet_name,
  );
  const clipCatalog = without(
    Array.from(new Set([...familyCatalog(family), authored.clip_name].filter(Boolean))),
    drop.clip_name,
  );
  const vaeCatalog = without(
    Array.from(new Set([...familyCatalog(family), authored.vae_name].filter(Boolean))),
    drop.vae_name,
  );

  const nodes = qualities.map((value, index) =>
    makeNode(
      "EZQuality",
      [
        makeWidget("quality", value, {
          values: Array.from(new Set([value, ...EZ_QUALITY_CHOICES].filter(Boolean))),
        }),
      ],
      { mode: spec.qualityMode ?? 0, title: `Quality ${index + 1}` },
    ),
  );

  for (let i = 0; i < samplers; i += 1) {
    nodes.push(
      makeNode("KSampler", [
        makeWidget("seed", 1234),
        makeWidget("steps", authored.steps ?? 20),
        makeWidget("cfg", authored.cfg ?? 3.5),
        makeWidget("sampler_name", "euler"),
        makeWidget("scheduler", "simple"),
        makeWidget("denoise", 1.0),
      ], { title: `KSampler ${i + 1}` }),
    );
  }
  for (let i = 0; i < loaders; i += 1) {
    nodes.push(
      makeNode("UNETLoader", [
        makeWidget("unet_name", authored.unet_name || "", { values: unetCatalog }),
      ], { title: `UNETLoader ${i + 1}` }),
    );
    nodes.push(
      makeNode("CLIPLoader", [
        makeWidget("clip_name", authored.clip_name || "", { values: clipCatalog }),
        makeWidget("type", authored.clip_type || "flux2", {
          values: ["flux2", "ltx", "stable_diffusion", "wan"],
        }),
      ], { title: `CLIPLoader ${i + 1}` }),
    );
    nodes.push(
      makeNode("VAELoader", [
        makeWidget("vae_name", authored.vae_name || "", { values: vaeCatalog }),
      ], { title: `VAELoader ${i + 1}` }),
    );
  }

  const graph = makeGraph({
    occupancy: spec.occupancy ?? "",
    nodes,
    lab_rel: spec.lab_rel,
  });
  graph.qualityNodes = nodesOfType(graph, "EZQuality");
  return graph;
}

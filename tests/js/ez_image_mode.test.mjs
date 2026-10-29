/**
 * @file Client contract for the EZImageMode stills-desk extension, run under
 * `node --test`.
 *
 * LiteGraph builds a graph one node at a time inside LGraph.configure(), so
 * the node classes bindPreviewWatchers() walks can still be missing while the
 * EZImageMode node is being created (and can be absent from the graph for
 * good on a plain text-to-image workflow). A missing class is a no-op: the
 * desk must load, and the watchers must still land on the classes that do
 * exist. A throw here aborts the whole load with the frontend's
 * "Loading aborted due to error reloading workflow data" banner.
 */

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { describe, test } from "node:test";

import {
  REPO_ROOT,
  editWidget,
  loadExtension,
  makeGraph,
  makeNode,
  makeWidget,
  widgetValue,
} from "./harness.mjs";

const MODE_JS = path.join(
  REPO_ROOT,
  "custom_nodes",
  "ez_image",
  "js",
  "ez_image_mode.js",
);
const MODES_JSON = path.join(
  REPO_ROOT,
  "custom_nodes",
  "ez_image",
  "js",
  "modes.json",
);

const STUDIO_LAB = "stills/image-studio";
const PREVIEW_ROUTE = "/ez_image/studio-preview";
/** Longer than the extension's 200ms preview debounce. */
const DEBOUNCE_WAIT_MS = 400;

/** Make a widget callback observable without changing what it returns. */
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Serve the pack catalog and record every preview POST.
 * Arguments:
 *   preview - payload answered for the preview route (default: failure, so
 *             nothing is written back onto the widgets under test)
 * Returns:
 *   {previewBodies, restore} - recorded request bodies and the fetch restorer.
 */
async function stubFetch(preview = { ok: false }) {
  const catalog = JSON.parse(await readFile(MODES_JSON, "utf8"));
  const previewBodies = [];
  const original = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    if (String(url).includes(PREVIEW_ROUTE)) {
      previewBodies.push(JSON.parse(init.body));
      return { ok: true, json: async () => preview };
    }
    return { ok: true, json: async () => catalog };
  };
  return { previewBodies, restore: () => { globalThis.fetch = original; } };
}

/** The stills-desk Mode node, as the seeded graph authors it. */
function makeModeNode() {
  return makeNode("EZImageMode", [
    makeWidget("category", "generate", { values: ["generate", "edit_scene"] }),
    makeWidget("mode", "Photoreal still", { values: ["Photoreal still"] }),
    makeWidget("iterate", false),
    makeWidget("run_summary", ""),
  ]);
}

/** The other classes watchWidget() walks, each with one watched widget. */
function makeFormatNode() {
  return makeNode("EZImageFormat", [
    makeWidget("format", "square"),
    makeWidget("size_mode", "preset"),
    makeWidget("look", "none"),
    makeWidget("width", 1024),
    makeWidget("height", 1024),
    makeWidget("batch_size", 1),
  ]);
}

function makeOptionalImageNode() {
  return makeNode("EZOptionalImage", [makeWidget("filename", "")]);
}

function makeEnhanceNode() {  return makeNode("EZKleinPromptEnhance", [
    makeWidget("prompt", "a fennec fox at dusk"),
    makeWidget("sample", "custom"),
    makeWidget("style", "none"),
    makeWidget("enhance", "auto"),
  ]);
}

function makeSampler() {
  return makeNode("KSampler", [
    makeWidget("seed", 42),
    makeWidget("control_after_generate", "fixed"),
    makeWidget("steps", 8),
    makeWidget("cfg", 1),
  ]);
}

function makeUnetLoader() {
  return makeNode("UNETLoader", [
    makeWidget("unet_name", "z_image_turbo_bf16.safetensors"),
  ]);
}

/**
 * Run the frontend's node-creation path for EZImageMode: beforeRegisterNodeDef
 * wraps the class, then LiteGraph calls onNodeCreated while the node is still
 * the only one of its kind the graph can see.
 */
async function createModeNode(ext, node) {
  const nodeType = { prototype: {} };
  await ext.beforeRegisterNodeDef(nodeType, { name: "EZImageMode" });
  nodeType.prototype.onNodeCreated.call(node);
}

describe("ez_image_mode graph load", () => {
  test("creating the Mode node on a half-built desk does not abort the load", async () => {
    const { restore } = await stubFetch();
    try {
      const { ext, app } = await loadExtension(MODE_JS, "ez_image.mode");
      const mode = makeModeNode();
      // Mid-configure: EZOptionalImage / EZImageFormat / the Enhance node have
      // not been created yet, so nodeByType() answers undefined for them.
      const graph = makeGraph({
        lab_rel: STUDIO_LAB,
        nodes: [mode, makeUnetLoader(), makeSampler()],
      });
      app.graph = graph;

      await createModeNode(ext, mode);

      const sampler = graph.nodes.find((n) => n.type === "KSampler");
      assert.equal(sampler.widgets[0]._ezStudioWatch, true);
      const unet = graph.nodes.find((n) => n.type === "UNETLoader");
      assert.equal(unet.widgets[0]._ezStudioWatch, true);
    } finally {
      restore();
    }
  });

  test("watchers land on the classes that appear after the Mode node", async () => {
    const { previewBodies, restore } = await stubFetch();
    try {
      const { ext, app } = await loadExtension(MODE_JS, "ez_image.mode");
      const mode = makeModeNode();
      const graph = makeGraph({
        lab_rel: STUDIO_LAB,
        nodes: [
          mode,
          makeFormatNode(),
          makeOptionalImageNode(),
          makeEnhanceNode(),
          makeUnetLoader(),
          makeSampler(),
        ],
      });
      app.graph = graph;
      await ext.afterConfigureGraph();

      const optional = graph.nodes.find((n) => n.type === "EZOptionalImage");
      assert.equal(optional.widgets[0]._ezStudioWatch, true);

      const format = graph.nodes.find((n) => n.type === "EZImageFormat");
      editWidget(format, "width", 1152);
      await wait(DEBOUNCE_WAIT_MS);

      const last = previewBodies.at(-1);
      assert.equal(last.width, 1152);
      assert.equal(last.lab_rel, STUDIO_LAB);
      assert.equal(last.unet, "z_image_turbo_bf16.safetensors");
      assert.equal(last.steps, 8);
      assert.ok(
        widgetValue(mode, "run_summary").startsWith("Preview unavailable"),
        "the Mode node still reports what Queue will send",
      );
    } finally {
      restore();
    }
  });

  test("a plain text-to-image graph binds nothing and previews nothing", async () => {
    const { previewBodies, restore } = await stubFetch();
    try {
      const { ext, app } = await loadExtension(MODE_JS, "ez_image.mode");
      // The reported bare z-image workflow: no EZImageMode, no desk stamp.
      const graph = makeGraph({
        lab_rel: "stills/z-image-turbo.json",
        nodes: [makeUnetLoader(), makeSampler()],
      });
      app.graph = graph;

      await ext.afterConfigureGraph();
      await wait(DEBOUNCE_WAIT_MS);

      assert.deepEqual(previewBodies, []);
      const sampler = graph.nodes.find((n) => n.type === "KSampler");
      assert.equal(sampler.widgets[0]._ezStudioWatch, undefined);
    } finally {
      restore();
    }
  });
});

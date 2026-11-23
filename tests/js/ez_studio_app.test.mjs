/**
 * @file Behavioural tests for the App Mode chrome (custom_nodes/ez_studio_app).
 *
 * The chrome has one operator-visible job: turn the raw widget names and raw
 * class names a graph carries into words an operator can act on. It is loaded
 * here through the shared frontend stub, then handed LiteGraph-shaped nodes the
 * way the canvas does, and every assertion is about the string the operator
 * actually reads on the node card or in the App panel.
 *
 * makeNode leaves `title` equal to the class name when none is authored, which
 * is the same thing LiteGraph shows an operator for an untitled node, so the
 * "wears its class name" case covers both.
 */

import { describe, test } from "node:test";
import assert from "node:assert/strict";
import path from "node:path";

import { loadExtension, makeNode, makeWidget, REPO_ROOT } from "./harness.mjs";

const CHROME_JS = path.join(
  REPO_ROOT,
  "custom_nodes",
  "ez_studio_app",
  "js",
  "ez_studio_app.js",
);

/**
 * Load the chrome fresh and put one graph in front of it.
 * Arguments:
 *   nodes - makeNode() list; extra - graph extra (linearData lives here)
 * Returns:
 *   {ext, app} with app.graph set to the graph the chrome will read.
 */
async function chrome(nodes, extra) {
  const loaded = await loadExtension(CHROME_JS, "ez_studio_app.chrome");
  loaded.app.graph = { nodes, extra };
  return loaded;
}

describe("widget labels", () => {
  test("a first-party widget the graph left in snake_case reads as a word", async () => {
    const node = makeNode("EZNvidiaLabJob", [
      makeWidget("tool_id", ""),
      makeWidget("input_path", ""),
      makeWidget("params_json", "{}"),
    ]);
    const { ext } = await chrome([node]);
    await ext.nodeCreated(node);
    assert.equal(node.widgets[0].label, "Tool");
    assert.equal(node.widgets[1].label, "Input file");
    assert.equal(node.widgets[2].label, "Parameters (JSON)");
  });

  test("an output widget says what it writes", async () => {
    const node = makeNode("VHS_VideoCombine", [
      makeWidget("frame_rate", 24),
      makeWidget("filename_prefix", "ez_svc_offbr"),
      makeWidget("loop_count", 0),
    ]);
    const { ext } = await chrome([node]);
    await ext.nodeCreated(node);
    assert.equal(node.widgets[0].label, "Frame rate");
    assert.equal(node.widgets[1].label, "Output filename");
    assert.equal(node.widgets[2].label, "Loop count");
  });

  test("a label stamped in linearData still beats the generic one", async () => {
    const node = makeNode("EZSamplePrompt", [makeWidget("prompt", "a still")]);
    const { ext } = await chrome([node], {
      linearData: { inputs: [[0, "prompt", { label: "Shot prompt" }]] },
    });
    await ext.nodeCreated(node);
    assert.equal(node.widgets[0].label, "Shot prompt");
  });

  test("an authored widget label is not lost when the chrome repaints", async () => {
    const node = makeNode("EZImageMode", [makeWidget("iterate", 1)]);
    const { ext } = await chrome([node]);
    await ext.nodeCreated(node);
    await ext.nodeCreated(node);
    assert.equal(node.widgets[0].label, "Repeat");
  });

  test("a selector or input socket the graph left in snake_case reads as a word", async () => {
    // LABELS is class-agnostic, so one node carries the widget names the
    // shipped graphs use across several first-party classes, plus one entry
    // the map has covered all along.
    const node = makeNode("EZPromptJoin", [
      makeWidget("family", "klein"),
      makeWidget("filename_2", ""),
      makeWidget("bed", ""),
      makeWidget("lock", "view"),
      makeWidget("backend", "kokoro"),
      makeWidget("layer", "clay"),
      makeWidget("size_src", ""),
      makeWidget("duration_hint", "wide 8s"),
    ]);
    const { ext } = await chrome([node]);
    await ext.nodeCreated(node);
    const labels = Object.fromEntries(
      node.widgets.map((widget) => [widget.name, widget.label]),
    );
    assert.deepEqual(labels, {
      family: "Model family",
      filename_2: "Choose image 2",
      bed: "Music bed",
      lock: "Keep constant",
      backend: "Voice engine",
      layer: "Render layer",
      size_src: "Size reference",
      duration_hint: "Duration / framing",
    });
  });

  test("a widget name two classes share is labelled by class", async () => {
    // flavor names the script form on the podcast writer and the target
    // model on the cinema rack, so it stays out of the class-agnostic map:
    // only the writer gets a word, the rack keeps its raw name.
    const writer = makeNode("EZPodcastScript", [
      makeWidget("flavor", "podcast_two_host"),
    ]);
    const cinema = makeNode("EZCinemaRack", [makeWidget("flavor", "klein")]);
    const music = makeNode("EZAudioRack", [makeWidget("flavor", "ace_vocal")]);
    const stranger = makeNode("EZSomeOtherNode", [makeWidget("flavor", "x")]);
    const { ext } = await chrome([writer, cinema, music, stranger]);
    for (const node of [writer, cinema, music, stranger]) {
      await ext.nodeCreated(node);
    }
    assert.equal(writer.widgets[0].label, "Script format");
    assert.equal(cinema.widgets[0].label, "Prompt model");
    assert.equal(music.widgets[0].label, "Track type");
    assert.equal(
      stranger.widgets[0].label,
      undefined,
      "a class with no case of its own keeps its raw name rather than wear another's word",
    );
  });
});

describe("node titles", () => {
  test("a sampler wearing its class name gets a human one", async () => {
    const sampler = makeNode("KSampler", [makeWidget("seed", 0)]);
    const { ext } = await chrome([sampler]);
    await ext.nodeCreated(sampler);
    assert.equal(sampler.title, "Sampling");
  });

  test("a second sampler on the same graph is numbered, not duplicated", async () => {
    const first = makeNode("KSampler", [makeWidget("seed", 0)]);
    const second = makeNode("KSampler", [makeWidget("seed", 0)]);
    const { ext } = await chrome([first, second]);
    await ext.nodeCreated(first);
    await ext.nodeCreated(second);
    assert.equal(first.title, "Sampling");
    assert.equal(second.title, "Sampling - pass 2");
  });

  test("a title the graph authored always wins", async () => {
    const loader = makeNode("UNETLoader", [makeWidget("unet_name", "flux-2-klein-4b-fp8.safetensors")], {
      title: "Klein 4B distilled FP8",
    });
    const { ext } = await chrome([loader]);
    await ext.nodeCreated(loader);
    assert.equal(loader.title, "Klein 4B distilled FP8");
  });

  test("an authored title wins even on a class this chrome has a fallback for", async () => {
    // The case above uses a class with no fallback, so it still passes when the
    // authored-title check is deleted: nothing would have been written anyway.
    // KSampler is in NODE_TITLES, so a graph that titled one keeps its words
    // only because relabelTitle looks before it writes.
    const sampler = makeNode("KSampler", [makeWidget("seed", 0)], {
      title: "Pass A - 30 steps",
    });
    const { ext } = await chrome([sampler]);
    await ext.nodeCreated(sampler);
    assert.equal(sampler.title, "Pass A - 30 steps");
  });

  test("repainting never escalates a fallback into pass 2", async () => {
    const sampler = makeNode("KSampler", [makeWidget("seed", 0)]);
    const { ext } = await chrome([sampler]);
    await ext.nodeCreated(sampler);
    await ext.nodeCreated(sampler);
    await ext.nodeCreated(sampler);
    assert.equal(sampler.title, "Sampling");
  });

  test("an operator rename survives the next repaint", async () => {
    const sampler = makeNode("KSampler", [makeWidget("seed", 0)]);
    const { ext } = await chrome([sampler]);
    await ext.nodeCreated(sampler);
    sampler.title = "My own knob";
    await ext.nodeCreated(sampler);
    assert.equal(sampler.title, "My own knob");
  });

  test("a class with no fallback keeps the frontend default", async () => {
    const latent = makeNode("EmptyLatentImage", [makeWidget("width", 1024)]);
    const { ext } = await chrome([latent]);
    await ext.nodeCreated(latent);
    assert.equal(latent.title, "EmptyLatentImage");
  });
});

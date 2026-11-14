/**
 * @file Client contract for the Detail combo, run under `node --test`.
 *
 * Every expectation is derived from the generated rung table
 * (custom_nodes/ez_quality/js/ez_quality_presets.js), not from the overlay
 * source, so the suite pins the user-visible behaviour: picking a rung writes
 * every affected widget on every instance, `standard` writes nothing at all, a
 * write that cannot land refuses the whole apply and leaves the row on its
 * previous rung, and the caption is derived from the live widgets every time.
 *
 * The refusal set asserted here is the same set tests/python/test_quality_parity
 * asserts for apply_to_graph: both sides read the one generated table, so the
 * list of rungs that name a file is the list that must refuse.
 */

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { describe, test } from "node:test";

import {
  EZ_QUALITY_CHOICES,
  EZ_QUALITY_LICENSES,
  EZ_QUALITY_OWNED,
  EZ_QUALITY_TABLE,
  EZ_QUALITY_TIERS,
} from "../../custom_nodes/ez_quality/js/ez_quality_presets.js";
import {
  FIELD_NODE_TYPE,
  FIELD_WIDGET,
  REPO_ROOT,
  comboOptions,
  comboValue,
  editWidget,
  loadExtension,
  loadOverlay,
  makeNode,
  makeStudioGraph,
  makeWidget,
  mountGraph,
  nodesOfType,
  pickTier,
  qualityCaption,
  tierField,
  widgetValue,
} from "./harness.mjs";

const MODEL_CHECK_JS = path.join(
  REPO_ROOT,
  "custom_nodes",
  "ez_quality",
  "js",
  "ez_model_check.js",
);
const OVERLAY_JS = path.join(
  REPO_ROOT,
  "custom_nodes",
  "ez_quality",
  "js",
  "ez_quality.js",
);

/** The three ladder rows, in the order the combo lists them. */
const RUNGS = ["draft", "standard", "final"];

/** Families that own a ladder, so their combo offers it. */
const LADDER_FAMILIES = ["klein", "klein3", "qwen", "wan", "ltx", "film", "audio", "trellis"];

/** Ids the contract retired: never offered, never derived, never stamped. */
const RETIRED_IDS = [
  "lab",
  "custom",
  "high",
  "ultra",
  "max",
  "Free Commercial Use (<$10M)",
  "free_commercial",
  "flux3-fast",
  "flux3-quality",
  "flux3-nvfp4",
  "qwen-image",
  "qwen-image-turbo",
  "qwen-image-nvfp4",
  "qwen-image-turbo-nvfp4",
];

/**
 * Caption license word pinned by hand for the families whose word carries the
 * licensing story: the two Apache defaults the App ships, and the two opt-in
 * stacks that must never read as an Apache one. Every other family's word is
 * read back from the generated table (EZ_QUALITY_LICENSES), which presets.py
 * generates from LICENSE_LABEL, kept honest against docs/licenses.mdx.
 */
const LICENSE_WORD = {
  klein: "Apache-2.0",
  klein3: "FLUX Non-Commercial",
  qwen: "Qwen Research license",
  wan: "Apache-2.0",
};

/** Families whose weights are not Apache, so their caption may not say so. */
const NOT_APACHE_FAMILIES = ["ltx", "film", "audio", "trellis"];

// Authored klein graph parked off every rung, so a rung pick is a real write on
// every owned widget, including the loader combos.
const KLEIN_AUTHORED = {
  steps: 20,
  cfg: 3.5,
  unet_name: "flux-2-klein-9b-fp8.safetensors",
  clip_name: "qwen_3_8b_fp8mixed.safetensors",
  vae_name: "full_encoder_small_decoder.safetensors",
  clip_type: "stable_diffusion",
};

// Wan 5B (never 14B) so the overlay is live; Wan rungs own steps only.
const WAN_AUTHORED = {
  steps: 15,
  cfg: 3.5,
  unet_name: "wan22_5b_t2v.safetensors",
  clip_name: "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
  vae_name: "wan_2.1_vae.safetensors",
  clip_type: "wan",
};

const KLEIN3_AUTHORED = {
  steps: 21,
  cfg: 2.5,
  unet_name: "flux3-image-klein-base-int8-convrot.safetensors",
  clip_name: "qwen3vl_8b_int8_convrot.safetensors",
  vae_name: "flux2-vae.safetensors",
  clip_type: "flux2",
};

const QWEN_AUTHORED = {
  steps: 22,
  cfg: 2.5,
  unet_name: "qwen_image_2.1_nvfp4.safetensors",
  clip_name: "qwen3vl_8b_nvfp4.safetensors",
  vae_name: "qwen_image_2.1_vae_bf16.safetensors",
  clip_type: "qwen3vl",
};

const AUTHORED_BY_FAMILY = {
  klein: KLEIN_AUTHORED,
  klein3: KLEIN3_AUTHORED,
  qwen: QWEN_AUTHORED,
  wan: WAN_AUTHORED,
  ltx: WAN_AUTHORED,
  film: WAN_AUTHORED,
  audio: WAN_AUTHORED,
  trellis: WAN_AUTHORED,
};

/**
 * Owned fields a rung actually requests (null = leave the authored widget).
 * Returns:
 *   Array of field names from EZ_QUALITY_OWNED[family].
 */
function requestedFields(family, rung) {
  const owned = EZ_QUALITY_OWNED[family] || [];
  return owned.filter((field) => tierField(family, rung, field) != null);
}

/**
 * Files one rung asks a loader to select; empty for a steps-only rung.
 * Returns:
 *   Array of filenames.
 */
function rungFiles(family, rung) {
  const row = EZ_QUALITY_TABLE?.[family]?.[rung] || {};
  return ["unet_name", "clip_name", "vae_name"]
    .map((field) => row[field])
    .filter((value) => typeof value === "string" && value.length > 0);
}

/**
 * Assert one widget shows a value in the panel and in widgets_values.
 * Arguments:
 *   node, name, expected, label
 */
function assertWidget(node, name, expected, label) {
  const index = node.widgets.findIndex((w) => w.name === name);
  assert.ok(index >= 0, `${node.type} has no ${name} widget (${label})`);
  assert.equal(
    node.widgets[index].value,
    expected,
    `${node.title}.${name} widget value (${label})`,
  );
  assert.equal(
    node.widgets_values[index],
    expected,
    `${node.title}.${name} widgets_values slot (${label})`,
  );
}

/**
 * Assert every instance of every overlay-target class carries the rung.
 * Arguments:
 *   graph, family, rung, label
 */
function assertTierApplied(graph, family, rung, label) {
  for (const field of requestedFields(family, rung)) {
    const expected = tierField(family, rung, field);
    for (const node of nodesOfType(graph, FIELD_NODE_TYPE[field])) {
      assertWidget(node, FIELD_WIDGET[field], expected, `${label}: ${field}`);
    }
  }
}

/**
 * Snapshot every widget value on the graph, keyed by node id and widget name.
 * Returns:
 *   Map-like plain object.
 */
function snapshotWidgets(graph) {
  const snap = {};
  for (const node of graph.nodes) {
    for (const widget of node.widgets || []) {
      snap[`${node.id}:${widget.name}`] = widget.value;
    }
  }
  return snap;
}

/**
 * The caption's terms, with a leading "Edited: " stripped off.
 * Returns:
 *   Array of " - " separated terms.
 */
function captionTerms(caption) {
  return caption.replace(/^Edited: /, "").split(" - ");
}

/** Keys the browser stub currently holds. */
function storedKeys() {
  const store = globalThis.localStorage;
  if (!store) {
    return [];
  }
  const keys = [];
  for (let i = 0; i < (store.length || 0); i += 1) {
    keys.push(String(store.key(i)));
  }
  return keys;
}

describe("Detail combo", () => {
  test("the combo lists exactly the three rungs and nothing else", async () => {
    const { ext } = await loadOverlay();
    for (const family of LADDER_FAMILIES) {
      const graph = makeStudioGraph({ occupancy: family, qualities: ["standard"] });
      await mountGraph(graph, ext);
      const options = comboOptions(graph.qualityNodes[0]);
      assert.deepEqual(options, RUNGS, `${family} combo lists the ladder`);
      assert.deepEqual(options, EZ_QUALITY_CHOICES, `${family} matches the table order`);
      for (const retired of RETIRED_IDS) {
        assert.ok(!options.includes(retired), `${family} still offers the retired ${retired}`);
      }
    }
  });

  test("standard is the rung every combo opens on", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({ occupancy: "klein", authored: KLEIN_AUTHORED });
    await mountGraph(graph, ext);
    assert.equal(comboValue(graph.qualityNodes[0]), "standard", "App opens on standard");
    assert.ok(RUNGS.includes("standard"), "standard is a rung");
  });

  test("picking a named rung writes every owned widget on every instance", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      samplers: 2,
      loaders: 2,
      qualities: ["standard"],
    });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];

    pickTier(combo, "final");

    assert.equal(comboValue(combo), "final", "combo shows the picked rung");
    assert.equal(nodesOfType(graph, "KSampler").length, 2, "two samplers built");
    assert.equal(nodesOfType(graph, "UNETLoader").length, 2, "two UNETLoaders built");
    assertTierApplied(graph, "klein", "final", "final pick");
  });

  test("standard writes nothing on every family", async () => {
    const { ext } = await loadOverlay();
    for (const family of LADDER_FAMILIES) {
      const graph = makeStudioGraph({
        occupancy: family,
        family,
        authored: AUTHORED_BY_FAMILY[family],
        qualities: ["draft"],
      });
      await mountGraph(graph, ext);
      const before = snapshotWidgets(graph);
      const combo = graph.qualityNodes[0];

      pickTier(combo, "standard");

      assert.equal(comboValue(combo), "standard", `${family} shows standard`);
      assert.deepEqual(
        snapshotWidgets(graph),
        before,
        `${family} standard must write no widget at all`,
      );
    }
  });

  test("graphToPrompt submits exactly what the combo shows", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      samplers: 2,
      loaders: 2,
      qualities: ["standard"],
    });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];

    pickTier(combo, "final");
    const { output } = graph.graphToPrompt();

    assert.equal(comboValue(combo), "final", "combo shows the picked rung");
    for (const field of requestedFields("klein", "final")) {
      const expected = tierField("klein", "final", field);
      for (const node of nodesOfType(graph, FIELD_NODE_TYPE[field])) {
        const submitted = output[String(node.id)].inputs[FIELD_WIDGET[field]];
        assert.equal(
          submitted,
          expected,
          `submitted ${node.title}.${FIELD_WIDGET[field]} (${field})`,
        );
        assert.equal(
          submitted,
          widgetValue(node, FIELD_WIDGET[field]),
          `submitted value matches the widget the user sees (${field})`,
        );
      }
    }
  });

  test("no rung writes a size on any family", async () => {
    const { ext } = await loadOverlay();
    for (const family of LADDER_FAMILIES) {
      const graph = makeStudioGraph({
        occupancy: family,
        family,
        authored: AUTHORED_BY_FAMILY[family],
        qualities: ["standard"],
      });
      const formatNode = graph.addNode(
        makeNode("EZImageFormat", [
          makeWidget("format", "16:9 draft (768x432)", {
            values: ["16:9 draft (768x432)", "16:9 LTX feeder (1280x704)"],
          }),
          makeWidget("size_mode", "none"),
          makeWidget("width", 768),
          makeWidget("height", 432),
          makeWidget("batch_size", 2),
          makeWidget("look", "Match input"),
        ]),
      );
      const latent = graph.addNode(
        makeNode("EmptyFlux2LatentImage", [
          makeWidget("width", 768),
          makeWidget("height", 432),
          makeWidget("batch_size", 2),
        ]),
      );
      await mountGraph(graph, ext);
      const combo = graph.qualityNodes[0];

      for (const rung of RUNGS) {
        pickTier(combo, "standard");
        pickTier(combo, rung);
        assertWidget(formatNode, "format", "16:9 draft (768x432)", `${family} ${rung} format`);
        assertWidget(formatNode, "size_mode", "none", `${family} ${rung} size_mode`);
        assertWidget(formatNode, "width", 768, `${family} ${rung} width`);
        assertWidget(formatNode, "height", 432, `${family} ${rung} height`);
        assertWidget(formatNode, "batch_size", 2, `${family} ${rung} batch`);
        assertWidget(formatNode, "look", "Match input", `${family} ${rung} look`);
        assertWidget(latent, "width", 768, `${family} ${rung} latent width`);
        assertWidget(latent, "height", 432, `${family} ${rung} latent height`);
      }
    }
  });

  test("the FCU size retarget path is gone from the overlay", async () => {
    const source = await readFile(OVERLAY_JS, "utf8");
    assert.ok(!/EZImageFormat/.test(source), "the overlay must not touch EZImageFormat");
    assert.ok(!/retargetClipFormat/.test(source), "the size retarget helper is deleted");
    assert.ok(!/LTX feeder \(1280x704\)/.test(source), "the feeder size labels are deleted");
  });

  test("a rung never writes a weight outside its own family", async () => {
    const { ext } = await loadOverlay();
    for (const family of LADDER_FAMILIES) {
      const own = new Set(
        ["draft", "final"]
          .map((rung) => tierField(family, rung, "unet_name"))
          .filter((value) => typeof value === "string" && value.length > 0),
      );
      for (const rung of ["draft", "final"]) {
        const graph = makeStudioGraph({
          occupancy: family,
          family,
          authored: AUTHORED_BY_FAMILY[family],
          loaders: 2,
          qualities: ["standard"],
        });
        await mountGraph(graph, ext);
        const combo = graph.qualityNodes[0];
        const allowed = new Set([AUTHORED_BY_FAMILY[family].unet_name, ...own]);

        pickTier(combo, rung);

        for (const node of nodesOfType(graph, "UNETLoader")) {
          const value = widgetValue(node, "unet_name");
          assert.ok(
            allowed.has(value),
            `${family} ${rung} wrote ${value}; this family writes ` +
              `${Array.from(own).join(", ") || "no weight"}`,
          );
        }
        if (own.size) {
          assertTierApplied(graph, family, rung, `${family} ${rung}`);
        }
      }
    }
  });

  test("a rung never offers a Klein 9B or FLUX.2-dev weight", async () => {
    for (const family of Object.keys(EZ_QUALITY_TABLE)) {
      for (const rung of RUNGS) {
        const row = EZ_QUALITY_TABLE[family][rung] || {};
        const unet = row.unet_name;
        if (typeof unet !== "string" || !unet) {
          continue;
        }
        const lower = unet.toLowerCase();
        assert.ok(!lower.includes("9b"), `${family} ${rung} writes a 9B weight: ${unet}`);
        assert.ok(
          !lower.includes("flux2_dev") && !lower.includes("flux2-dev"),
          `${family} ${rung} writes FLUX.2-dev: ${unet}`,
        );
      }
    }
  });

  test("an EZQuality node at mode 4 is ignored", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      qualities: ["final"],
      qualityMode: 4,
    });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];

    assert.equal(
      widgetValue(nodesOfType(graph, "KSampler")[0], "steps"),
      KLEIN_AUTHORED.steps,
      "muted combo wrote no steps",
    );
    assert.equal(
      widgetValue(nodesOfType(graph, "KSampler")[0], "cfg"),
      KLEIN_AUTHORED.cfg,
      "muted combo wrote no cfg",
    );
    assert.equal(
      widgetValue(nodesOfType(graph, "UNETLoader")[0], "unet_name"),
      KLEIN_AUTHORED.unet_name,
      "muted combo wrote no unet_name",
    );
    assert.equal(qualityCaption(graph, combo), "", "muted combo stamped no caption");
  });

  test("a TRELLIS rung leaves the unguided texture stage authored", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({
      occupancy: "trellis",
      samplers: 4,
      loaders: 0,
      qualities: ["standard"],
      authored: { steps: 19, cfg: 7.5 },
    });
    // Three guided stages at CFG 7.5 plus the texture stage at CFG 1, the way
    // the shipped TRELLIS graph is authored.
    const samplers = nodesOfType(graph, "KSampler");
    for (const sampler of samplers.slice(0, 3)) {
      editWidget(sampler, "cfg", 7.5);
    }
    editWidget(samplers[3], "cfg", 1);
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];

    pickTier(combo, "final");

    const wanted = tierField("trellis", "final", "steps");
    assert.ok(wanted, "the table gives TRELLIS a final step count");
    for (const sampler of samplers.slice(0, 3)) {
      assert.equal(widgetValue(sampler, "steps"), wanted);
      assert.equal(widgetValue(sampler, "cfg"), 7.5, "CFG stays authored");
    }
    assert.equal(
      widgetValue(samplers[3], "steps"),
      19,
      "the unguided stage keeps its authored steps",
    );
    assert.equal(comboValue(combo), "final", "the rung still reads back off the guided stages");
  });
});

describe("Detail caption", () => {
  test("the caption is stack - steps - CFG - license", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      qualities: ["standard"],
    });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];

    pickTier(combo, "final");
    const caption = qualityCaption(graph, combo);

    assert.ok(caption, "the combo stamped a caption");
    assert.ok(!caption.startsWith("Edited: "), `clean apply is not edited: ${caption}`);
    const terms = captionTerms(caption);
    assert.equal(terms.at(-1), "Apache-2.0", `caption ends with the license: ${caption}`);
    assert.ok(
      terms.some((term) => term === `${tierField("klein", "final", "steps")} steps`),
      `caption names the live steps: ${caption}`,
    );
    assert.ok(
      terms.some((term) => term === `CFG ${tierField("klein", "final", "cfg")}`),
      `caption names the live CFG: ${caption}`,
    );
    assert.ok(terms.length >= 3, `stack, steps, CFG, license: ${caption}`);
    assert.equal(
      combo.widgets.find((w) => w.name === "quality").label,
      `Detail - ${caption}`,
      "the row label mirrors the caption with the Detail prefix",
    );
  });

  test("the CFG term is omitted where the rung writes no CFG", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({
      occupancy: "wan",
      authored: WAN_AUTHORED,
      qualities: ["standard"],
    });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];

    pickTier(combo, "final");
    const caption = qualityCaption(graph, combo);

    assert.ok(caption.includes(`${tierField("wan", "final", "steps")} steps`), caption);
    assert.ok(!caption.includes("CFG"), `steps-only family omits CFG: ${caption}`);
    assert.equal(captionTerms(caption).at(-1), "Apache-2.0", caption);
  });

  test("the caption names the family's license", async () => {
    const { ext } = await loadOverlay();
    for (const family of LADDER_FAMILIES) {
      const graph = makeStudioGraph({
        occupancy: family,
        family,
        authored: AUTHORED_BY_FAMILY[family],
        qualities: ["standard"],
      });
      await mountGraph(graph, ext);
      pickTier(graph.qualityNodes[0], "final");
      const caption = qualityCaption(graph, graph.qualityNodes[0]);
      const word = EZ_QUALITY_LICENSES?.[family];
      assert.ok(typeof word === "string" && word, `${family} table names a license`);
      assert.ok(caption.endsWith(word), `${family} caption ends with its license, got "${caption}"`);
      if (LICENSE_WORD[family]) {
        assert.ok(
          caption.endsWith(LICENSE_WORD[family]),
          `${family} caption states "${LICENSE_WORD[family]}", got "${caption}"`,
        );
      }
      if (NOT_APACHE_FAMILIES.includes(family)) {
        assert.ok(!caption.includes("Apache"), `${family} is not Apache: "${caption}"`);
      }
    }
  });

  test("a hand edit prefixes Edited: and names the diverging field", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      qualities: ["standard"],
    });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];
    const sampler = nodesOfType(graph, "KSampler")[0];

    pickTier(combo, "final");
    editWidget(sampler, "steps", 20);

    const caption = qualityCaption(graph, combo);
    assert.ok(caption.startsWith("Edited: "), `hand edit is marked: ${caption}`);
    assert.ok(caption.includes("20 steps"), `caption shows the live steps: ${caption}`);
    assert.ok(/steps/.test(caption), `caption names the field: ${caption}`);
    assert.ok(
      caption.includes(String(tierField("klein", "final", "steps"))),
      `caption says what the rung sets: ${caption}`,
    );
    assert.equal(comboValue(combo), "final", "the row keeps the rung the user chose");
  });

  test("an edit outside the owned set keeps the rung and is not an edit", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({
      occupancy: "wan",
      authored: WAN_AUTHORED,
      qualities: ["standard"],
    });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];
    const sampler = nodesOfType(graph, "KSampler")[0];

    assert.ok(!(EZ_QUALITY_OWNED.wan || []).includes("cfg"), "wan rungs do not own cfg");
    pickTier(combo, "final");
    editWidget(sampler, "cfg", 9.5);

    assert.equal(comboValue(combo), "final", "a cfg edit is outside the owned set");
    assertWidget(sampler, "cfg", 9.5, "cfg edit kept");
    assertWidget(sampler, "steps", tierField("wan", "final", "steps"), "rung steps kept");
    assert.ok(
      !qualityCaption(graph, combo).startsWith("Edited: "),
      "an edit the rung does not own is not a divergence",
    );
  });

  test("every reason is written, not the first two", async () => {
    const { ext } = await loadOverlay();
    const missing = rungFiles("klein", "final");
    assert.equal(missing.length, 3, "klein final names a unet, a clip, and a vae");
    const graph = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      qualities: ["standard"],
      drop: {
        unet_name: missing[0],
        clip_name: missing[1],
        vae_name: missing[2],
      },
    });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];

    pickTier(combo, "final");
    const caption = qualityCaption(graph, combo);

    for (const file of missing) {
      assert.ok(caption.includes(file), `caption names ${file}, got "${caption}"`);
    }
  });
});

describe("Write-or-refuse", () => {
  test("a weight absent from the loader list refuses the apply and changes nothing", async () => {
    const { ext } = await loadOverlay();
    const missing = rungFiles("klein", "final");
    const graph = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      qualities: ["standard"],
      drop: { unet_name: missing[0] },
    });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];
    const unet = nodesOfType(graph, "UNETLoader")[0];
    const sampler = nodesOfType(graph, "KSampler")[0];
    const before = snapshotWidgets(graph);

    pickTier(combo, "final");

    assert.equal(comboValue(combo), "standard", "the row keeps its previous rung");
    assertWidget(unet, "unet_name", KLEIN_AUTHORED.unet_name, "missing weight");
    assertWidget(sampler, "steps", KLEIN_AUTHORED.steps, "no partial write");
    assert.deepEqual(snapshotWidgets(graph), before, "the refusal changed nothing");
    const caption = qualityCaption(graph, combo);
    assert.ok(
      caption.includes(missing[0]),
      `caption must name the missing file, got "${caption}"`,
    );
  });

  test("the refusal set is exactly the rungs that name a file", async () => {
    const { ext } = await loadOverlay();
    for (const family of LADDER_FAMILIES) {
      for (const rung of ["draft", "final"]) {
        const files = rungFiles(family, rung);
        const drop = {};
        for (const file of files) {
          drop.unet_name = drop.unet_name || [];
          drop.clip_name = drop.clip_name || [];
          drop.vae_name = drop.vae_name || [];
        }
        const row = EZ_QUALITY_TABLE?.[family]?.[rung] || {};
        const spec = {
          occupancy: family,
          family,
          authored: AUTHORED_BY_FAMILY[family],
          qualities: ["standard"],
        };
        if (typeof row.unet_name === "string" && row.unet_name) {
          spec.drop = { ...spec.drop, unet_name: row.unet_name };
        }
        if (typeof row.clip_name === "string" && row.clip_name) {
          spec.drop = { ...spec.drop, clip_name: row.clip_name };
        }
        if (typeof row.vae_name === "string" && row.vae_name) {
          spec.drop = { ...spec.drop, vae_name: row.vae_name };
        }
        const graph = makeStudioGraph(spec);
        await mountGraph(graph, ext);
        const combo = graph.qualityNodes[0];
        const before = snapshotWidgets(graph);

        pickTier(combo, rung);

        if (files.length) {
          assert.equal(
            comboValue(combo),
            "standard",
            `${family} ${rung} names files, so it must refuse`,
          );
          assert.deepEqual(
            snapshotWidgets(graph),
            before,
            `${family} ${rung} refused after writing`,
          );
        } else {
          assert.equal(comboValue(combo), rung, `${family} ${rung} must land`);
          assertTierApplied(graph, family, rung, `${family} ${rung}`);
        }
      }
    }
  });

  test("standard always succeeds even when every loader list is empty", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      qualities: ["final"],
      drop: {
        unet_name: KLEIN_AUTHORED.unet_name,
        clip_name: KLEIN_AUTHORED.clip_name,
        vae_name: KLEIN_AUTHORED.vae_name,
      },
    });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];

    pickTier(combo, "standard");

    assert.equal(comboValue(combo), "standard", "standard cannot be refused");
  });
});

describe("No browser-global memory", () => {
  test("a newly opened App opens on standard, not on the last rung picked", async () => {
    const { ext } = await loadOverlay();
    const first = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      qualities: ["standard"],
    });
    await mountGraph(first, ext);
    pickTier(first.qualityNodes[0], "final");
    assert.equal(comboValue(first.qualityNodes[0]), "final", "first App picked final");

    const second = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      qualities: ["standard"],
    });
    await mountGraph(second, ext);

    assert.equal(
      comboValue(second.qualityNodes[0]),
      "standard",
      "the second App did not inherit the rung the first one picked",
    );
    assertWidget(
      nodesOfType(second, "UNETLoader")[0],
      "unet_name",
      KLEIN_AUTHORED.unet_name,
      "new App wrote no weight",
    );
    assert.equal(
      storedKeys().filter((key) => /quality/i.test(key)).length,
      0,
      `nothing persisted the last rung: ${storedKeys().join(",")}`,
    );
  });

  test("a freshly loaded App does not seed a previously chosen rung", async () => {
    const first = await loadOverlay();
    const graphA = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      qualities: ["standard"],
    });
    await mountGraph(graphA, first.ext);
    pickTier(graphA.qualityNodes[0], "final");

    const second = await loadOverlay();
    const graphB = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      qualities: ["standard"],
    });
    await mountGraph(graphB, second.ext);

    assert.equal(comboValue(graphB.qualityNodes[0]), "standard", "fresh App opens on standard");
  });

  test("the overlay keeps no last-rung key in storage", async () => {
    const source = await readFile(OVERLAY_JS, "utf8");
    assert.ok(!/ez-comfy\.quality\.last/.test(source), "the last-rung key is gone");
    assert.ok(!/localStorage/.test(source), "the overlay no longer reads browser storage");
    // Retired ids stay accepted input, so they may appear only as keys of the
    // alias map that folds them onto a rung. Anywhere else they would be a
    // selectable value, a derivation, or a stamp.
    const aliasBlock = /const RUNG_ALIASES = \{[\s\S]*?\n\};/u.exec(source)?.[0] ?? "";
    assert.ok(aliasBlock, "the overlay keeps the accepted-input alias map");
    const outsideAliases = source.replace(aliasBlock, "");
    assert.ok(
      !RETIRED_IDS.some((id) => outsideAliases.includes(`"${id}"`)),
      "no retired id is listed outside the alias map",
    );
  });
});

describe("EZModelCheck tier read", () => {
  /**
   * Load the Check models node with the globals it expects.
   * Returns:
   *   The `window.ezComfyModelCheck` surface the node publishes.
   */
  async function loadModelCheck() {
    Object.defineProperty(globalThis, "window", {
      configurable: true,
      writable: true,
      value: globalThis,
    });
    await loadExtension(MODEL_CHECK_JS, "ez_quality.model_check");
    return globalThis.window.ezComfyModelCheck;
  }

  test("it reads the live combo and ignores a muted one", async () => {
    const modelCheck = await loadModelCheck();
    assert.ok(modelCheck?.collectHints, "the node publishes its hints builder");
    const graph = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      qualities: ["final", "standard"],
    });
    const [muted, live] = graph.qualityNodes;
    muted.mode = 4;

    assert.equal(modelCheck.collectHints(graph).quality, "standard", "the live combo decides");

    const only = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      qualities: ["final"],
      qualityMode: 4,
    });
    assert.notEqual(
      modelCheck.collectHints(only).quality,
      "final",
      "a muted combo's stale rung is not reported",
    );
    assert.equal(
      modelCheck.collectHints(only).quality,
      "standard",
      "a graph with no live combo reports the default rung",
    );
  });
});

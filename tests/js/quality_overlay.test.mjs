/**
 * @file Client contract for the EZQuality combo, run under `node --test`.
 *
 * Every expectation is derived from the generated table
 * (custom_nodes/ez_quality/js/ez_quality_presets.js), not from the overlay
 * source, so the suite pins the user-visible behaviour: picking a tier writes
 * every affected widget on every instance, and an edit that breaks the tier
 * flips the combo to custom.
 */

import assert from "node:assert/strict";
import { describe, test } from "node:test";

import {
  EZ_QUALITY_CUSTOM,
  EZ_QUALITY_LAB,
  EZ_QUALITY_NAMED,
  EZ_QUALITY_OWNED,
  EZ_QUALITY_TABLE,
} from "../../custom_nodes/ez_quality/js/ez_quality_presets.js";
import {
  FIELD_NODE_TYPE,
  FIELD_WIDGET,
  comboValue,
  editWidget,
  loadOverlay,
  makeStudioGraph,
  mountGraph,
  nodesOfType,
  pickTier,
  qualityCaption,
  tierField,
  widgetValue,
} from "./harness.mjs";

// Authored klein graph parked at "high"-ish values so a "standard" pick is a
// real write on every owned widget, including the loader combos.
const KLEIN_AUTHORED = {
  steps: 20,
  cfg: 3.5,
  unet_name: "flux-2-klein-base-4b-fp8.safetensors",
  clip_name: "qwen_3_8b_fp8mixed.safetensors",
  vae_name: "flux2-vae.safetensors",
  clip_type: "stable_diffusion",
};

// Wan 5B (never 14B) so the overlay is live; Wan tiers own steps only.
const WAN_AUTHORED = {
  steps: 12,
  cfg: 3.5,
  unet_name: "wan22_5b_t2v.safetensors",
  clip_name: "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
  vae_name: "wan_2.1_vae.safetensors",
  clip_type: "wan",
};

const KLEIN3_AUTHORED = {
  steps: 20,
  cfg: 3.5,
  unet_name: "flux3-image-klein-base-int8-convrot.safetensors",
  clip_name: "qwen3vl_4b_int8_convrot.safetensors",
  vae_name: "full_encoder_small_decoder.safetensors",
  clip_type: "flux2",
};

/**
 * Owned fields a tier actually requests (null = leave the authored widget).
 * Returns:
 *   Array of field names from EZ_QUALITY_OWNED[family].
 */
function requestedFields(family, tier) {
  const owned = EZ_QUALITY_OWNED[family] || [];
  return owned.filter((field) => tierField(family, tier, field) != null);
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
 * Assert every instance of every overlay-target class carries the tier.
 * Arguments:
 *   graph, family, tier, label
 */
function assertTierApplied(graph, family, tier, label) {
  for (const field of requestedFields(family, tier)) {
    const expected = tierField(family, tier, field);
    for (const node of nodesOfType(graph, FIELD_NODE_TYPE[field])) {
      assertWidget(node, FIELD_WIDGET[field], expected, `${label}: ${field}`);
    }
  }
}

describe("EZQuality overlay", () => {
  test("picking a named tier writes every owned widget on every instance", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      samplers: 2,
      loaders: 2,
    });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];

    pickTier(combo, "standard");

    assert.equal(comboValue(combo), "standard", "combo shows the picked tier");
    assert.equal(nodesOfType(graph, "KSampler").length, 2, "two samplers built");
    assert.equal(nodesOfType(graph, "UNETLoader").length, 2, "two UNETLoaders built");
    assertTierApplied(graph, "klein", "standard", "standard pick");
  });

  test("graphToPrompt submits exactly what the combo shows", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      samplers: 2,
      loaders: 2,
    });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];

    pickTier(combo, "standard");
    const { output } = graph.graphToPrompt();

    assert.equal(comboValue(combo), "standard", "combo shows the picked tier");
    for (const field of requestedFields("klein", "standard")) {
      const expected = tierField("klein", "standard", field);
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

  test("a weight absent from the loader list lands nowhere and forces custom", async () => {
    const { ext } = await loadOverlay();
    const missing = tierField("klein", "standard", "unet_name");
    const graph = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      drop: { unet_name: missing },
    });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];
    const unet = nodesOfType(graph, "UNETLoader")[0];

    pickTier(combo, "standard");

    assert.equal(
      comboValue(combo),
      EZ_QUALITY_CUSTOM,
      "combo falls back to custom when the tier is not applicable",
    );
    assert.notEqual(
      comboValue(combo),
      "standard",
      "combo must not display a tier it could not apply",
    );
    assertWidget(unet, "unet_name", KLEIN_AUTHORED.unet_name, "missing weight");
    assert.ok(
      qualityCaption(graph, combo).includes(missing),
      `caption must name the missing file, got "${qualityCaption(graph, combo)}"`,
    );
  });

  test("editing an owned widget flips the combo to custom", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({ occupancy: "klein", authored: KLEIN_AUTHORED });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];
    const sampler = nodesOfType(graph, "KSampler")[0];

    pickTier(combo, "high");
    assert.equal(comboValue(combo), "high", "tier applied first");

    editWidget(sampler, "steps", 99);

    assert.equal(comboValue(combo), EZ_QUALITY_CUSTOM, "steps edit breaks the tier");
    assertWidget(sampler, "steps", 99, "user edit kept");
  });

  test("editing a widget outside the owned set keeps the level", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({ occupancy: "wan", authored: WAN_AUTHORED });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];
    const sampler = nodesOfType(graph, "KSampler")[0];

    pickTier(combo, "high");
    assert.ok(
      !(EZ_QUALITY_OWNED.wan || []).includes("cfg"),
      "wan tiers do not own cfg",
    );
    assert.equal(comboValue(combo), "high", "wan tier applied");

    editWidget(sampler, "cfg", 9.5);

    assert.equal(
      comboValue(combo),
      "high",
      "a cfg edit is outside EZ_QUALITY_OWNED.wan and must keep the level",
    );
    assertWidget(sampler, "cfg", 9.5, "cfg edit kept");
    assertWidget(sampler, "steps", tierField("wan", "high", "steps"), "tier steps kept");
  });

  test("two combos in one graph always agree", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      qualities: [EZ_QUALITY_LAB, EZ_QUALITY_LAB],
    });
    await mountGraph(graph, ext);
    const [first, second] = graph.qualityNodes;
    assert.equal(graph.qualityNodes.length, 2, "two combos built");

    pickTier(first, "standard");
    assert.equal(comboValue(second), "standard", "second combo follows the first");
    assertTierApplied(graph, "klein", "standard", "first combo picked");

    pickTier(second, "high");
    assert.equal(comboValue(first), "high", "first combo follows the second");
    assertTierApplied(graph, "klein", "high", "second combo picked");
  });

  test("an EZQuality node at mode 4 is ignored", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      qualities: ["standard"],
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

  test("instances of the same class that disagree resolve to custom", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({
      occupancy: "klein",
      authored: KLEIN_AUTHORED,
      samplers: 2,
    });
    const [a, b] = nodesOfType(graph, "KSampler");
    for (const field of requestedFields("klein", "standard")) {
      const value = tierField("klein", "standard", field);
      for (const node of nodesOfType(graph, FIELD_NODE_TYPE[field])) {
        const widget = node.widgets.find((w) => w.name === FIELD_WIDGET[field]);
        node.widgets_values[node.widgets.indexOf(widget)] = value;
        widget.value = value;
      }
    }
    // Second sampler disagrees with the first on one owned field.
    const index = a.widgets.findIndex((w) => w.name === "steps");
    b.widgets[index].value = b.widgets_values[index] + 1;
    b.widgets_values[index] = b.widgets[index].value;
    await mountGraph(graph, ext);

    assert.notEqual(
      widgetValue(a, "steps"),
      widgetValue(b, "steps"),
      "the two samplers really do disagree",
    );
    assert.equal(
      comboValue(graph.qualityNodes[0]),
      EZ_QUALITY_CUSTOM,
      "conflicting instances cannot be a named tier",
    );
  });

  test("authored values equal to a named tier derive that tier, not lab", async () => {
    const { ext } = await loadOverlay();
    const family = "klein";
    const tier = EZ_QUALITY_NAMED.find((name) => {
      const fields = requestedFields(family, name);
      return fields.length === (EZ_QUALITY_OWNED[family] || []).length;
    });
    assert.ok(tier, `no fully specified named tier for ${family}`);
    const authored = {};
    for (const field of EZ_QUALITY_OWNED[family]) {
      authored[field] = tierField(family, tier, field);
    }
    const graph = makeStudioGraph({ occupancy: family, authored });
    await mountGraph(graph, ext);

    assert.equal(
      comboValue(graph.qualityNodes[0]),
      tier,
      `authored widgets match ${tier} exactly, so the combo must show it`,
    );
  });

  test("custom is not absorbing: restoring the owned widgets re-derives the tier", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({ occupancy: "klein", authored: KLEIN_AUTHORED });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];
    const sampler = nodesOfType(graph, "KSampler")[0];
    const tierSteps = tierField("klein", "high", "steps");

    pickTier(combo, "high");
    editWidget(sampler, "steps", tierSteps + 3);
    assert.equal(comboValue(combo), EZ_QUALITY_CUSTOM, "edit broke the tier");

    editWidget(sampler, "steps", tierSteps);

    assert.equal(
      comboValue(combo),
      "high",
      "putting the tier value back must re-derive the tier, not stay custom",
    );
  });

  test("klein3 needles upgrade the family so the flux3 tiers write", async () => {
    const { ext } = await loadOverlay();
    const graph = makeStudioGraph({
      occupancy: "klein",
      family: "klein3",
      authored: KLEIN3_AUTHORED,
    });
    await mountGraph(graph, ext);
    const combo = graph.qualityNodes[0];
    assert.ok(
      EZ_QUALITY_TABLE.klein3["flux3-fast"].steps,
      "klein3 flux3-fast is a real tier",
    );

    pickTier(combo, "flux3-fast");

    assert.equal(comboValue(combo), "flux3-fast", "combo shows the flux3 tier");
    assertTierApplied(graph, "klein3", "flux3-fast", "flux3-fast pick");
  });
});

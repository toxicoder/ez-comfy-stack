/**
 * EZModelCheck: button POSTs /ez_quality/check. Queue does not run this node.
 *
 * Nodes 2.0: addWidget("button") plus widget.value. No LiteGraph hooks.
 */
import { app } from "../../scripts/app.js";

const ENHANCE = new Set([
  "EZKleinPromptEnhance",
  "EZWanPromptEnhance",
  "EZLTXPromptEnhance",
  "EZZimagePromptEnhance",
  "EZLongCatPromptEnhance",
  "EZDreamXPromptEnhance",
  "EZAceStepPromptEnhance",
  "EZNegativePromptEnhance",
]);

/**
 * Backend URL, honoring Comfy's api prefix when present.
 * @param {string} path
 * @returns {string}
 */
function apiUrl(path) {
  if (app.api && typeof app.api.apiURL === "function") {
    return app.api.apiURL(path);
  }
  return path;
}

/**
 * Widget value by name, else widgets_values[index].
 * @param {object} node
 * @param {string} name
 * @param {number} [index]
 * @returns {*}
 */
function widgetValue(node, name, index) {
  const widgets = node.widgets || [];
  const hit = widgets.find((item) => item && item.name === name);
  if (hit && hit.value !== undefined && hit.value !== null) {
    return hit.value;
  }
  const values = node.widgets_values || [];
  if (index != null && index < values.length) {
    return values[index];
  }
  return undefined;
}

/**
 * First string widget (loader filename).
 * @param {object} node
 * @returns {string}
 */
function firstName(node) {
  const widgets = node.widgets || [];
  if (widgets.length && widgets[0] && widgets[0].value) {
    return String(widgets[0].value);
  }
  const values = node.widgets_values || [];
  if (values.length && values[0] && typeof values[0] !== "object") {
    return String(values[0]);
  }
  return "";
}

/**
 * Compact graph snapshot for POST /ez_quality/check.
 * @param {object} [graph]
 * @returns {object}
 */
function collectHints(graph) {
  const g = graph || app.graph || {};
  const extra = g.extra || {};
  const occupancy = extra.lab_app_mode?.occupancy || "";
  const labRel = extra.lab_rel || "";
  const types = [];
  const unets = [];
  const clips = [];
  const vaes = [];
  const loras = [];
  const checkpoints = [];
  let quality = "lab";
  let enhanceOn = false;
  let describeOn = false;
  for (const node of g.nodes || []) {
    const ntype = node.type || node.comfyClass || "";
    if (!ntype) {
      continue;
    }
    types.push(ntype);
    const name = firstName(node);
    if (ntype === "UNETLoader" && name) {
      unets.push(name);
    } else if (ntype === "CLIPLoader" && name) {
      clips.push(name);
    } else if (ntype === "VAELoader" && name) {
      vaes.push(name);
    } else if ((ntype === "LoraLoader" || ntype === "LoraLoaderModelOnly") && name) {
      loras.push(name);
    } else if (ntype === "CheckpointLoaderSimple" && name) {
      checkpoints.push(name);
    } else if (ntype === "EZQuality") {
      quality = String(widgetValue(node, "quality", 0) || "lab");
    }
    if (ENHANCE.has(ntype) && widgetValue(node, "enhance") === true) {
      enhanceOn = true;
    }
    if (ntype === "EZImageDescribe" && widgetValue(node, "enable", 0) === true) {
      describeOn = true;
    }
  }
  const flags = [];
  if (extra.lab_iclora) {
    flags.push("iclora");
  }
  if (extra.lab_vace) {
    flags.push("vace");
  }
  return {
    lab_rel: labRel,
    occupancy,
    quality,
    types,
    unets,
    clips,
    vaes,
    loras,
    checkpoints,
    enhance_on: enhanceOn,
    describe_on: describeOn,
    flags,
  };
}

/**
 * POST hints and return the JSON payload.
 * @param {object} [graph]
 * @returns {Promise<object>}
 */
async function postCheck(graph) {
  const response = await fetch(apiUrl("/ez_quality/check"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(collectHints(graph)),
  });
  const payload = await response.json();
  return payload && typeof payload === "object" ? payload : { ok: false, message: "Check failed." };
}

/**
 * Write the status STRING on an EZModelCheck node.
 * @param {object} node
 * @param {string} text
 * @returns {void}
 */
function setStatus(node, text) {
  const widget = (node.widgets || []).find((item) => item && item.name === "status");
  if (widget) {
    widget.value = text;
    if (typeof widget.callback === "function") {
      widget.callback(text);
    }
  }
  if (node.widgets_values && node.widgets_values.length) {
    node.widgets_values[0] = text;
  }
  app.graph?.setDirtyCanvas?.(true);
}

/**
 * Run the check and paint the node.
 * @param {object} node
 * @returns {Promise<void>}
 */
async function runOnNode(node) {
  setStatus(node, "Checking models...");
  try {
    const payload = await postCheck(app.graph);
    setStatus(node, String(payload.message || (payload.ok ? "Ready." : "Missing models.")));
  } catch (err) {
    setStatus(node, `Check failed: ${err && err.message ? err.message : err}`);
  }
}

window.ezComfyModelCheck = { collectHints, postCheck, runOnNode };

app.registerExtension({
  name: "ez_quality.model_check",
  /**
   * Add the Check models button on create.
   * @param {object} nodeType
   * @param {object} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "EZModelCheck") {
      return;
    }
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    /**
     * Mount a native button widget.
     * @returns {void}
     */
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      this.addWidget("button", "Check models", "check", () => {
        runOnNode(this);
      });
    };
  },
});

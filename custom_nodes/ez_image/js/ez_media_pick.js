/**
 * App Mode media picker: upload or choose files already on the output drive.
 *
 * Nodes 2.0: addWidget("button") plus widget.value. Treat inputEl as optional.
 * Copies Outputs into Comfy input/ via ez_outputs (no path traversal).
 */
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

/**
 * Widget on a load node; only the members this picker reads or writes.
 * @typedef {{
 *   name: string,
 *   value?: unknown,
 *   options?: {values?: unknown[]},
 *   callback?: (value: unknown, canvas: unknown, node: unknown) => void
 * }} EzWidget
 */

/**
 * Graph handle used only to mark the node dirty.
 * @typedef {{
 *   setDirtyCanvas?: (dirtyCanvas: boolean, dirty: boolean) => void
 * }} EzGraph
 */

/**
 * ComfyUI node handle. --noResolve leaves the frontend untyped, so only the
 * members this file touches are named.
 * @typedef {{
 *   widgets?: EzWidget[],
 *   widgets_values?: unknown[],
 *   graph?: EzGraph,
 *   _ezMediaPickBound?: boolean,
 *   addWidget?: (
 *     type: string,
 *     name: string,
 *     value: unknown,
 *     callback: () => void
 *   ) => void
 * }} EzNode
 */

/**
 * One row from the outputs listing, as returned by /ez_outputs/list.
 * @typedef {{rel?: string, name?: string}} EzOutputRow
 */

/**
 * Registered node definition, seen before ComfyUI registers it.
 * @typedef {{
 *   prototype: {
 *     onNodeCreated?: (this: EzNode, ...args: unknown[]) => void;
 *   }
 * }} EzNodeType
 */

/**
 * Node definition metadata; only the class name is read here.
 * @typedef {{name?: string}} EzNodeDef
 */

const TARGETS = {
  EZOptionalImage: {
    widgets: ["filename", "filename_2", "filename_3"],
    kind: "image",
    accept: "image/*",
  },
  LoadImage: { widget: "image", kind: "image", accept: "image/*" },
  LoadAudio: { widget: "audio", kind: "audio", accept: "audio/*" },
};

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
 * Find a widget by name on a node.
 * @param {EzNode} node
 * @param {string} name
 * @returns {EzWidget|undefined}
 */
function widgetByName(node, name) {
  return node.widgets?.find((item) => item.name === name);
}

/**
 * Set a combo value and notify Vue / App Mode.
 * @param {EzNode} node
 * @param {EzWidget|undefined} widget
 * @param {string} value
 * @returns {void}
 */
function setWidgetValue(node, widget, value) {
  if (!widget) {
    return;
  }
  const values = widget.options?.values;
  if (Array.isArray(values) && value && !values.includes(value)) {
    values.push(value);
  }
  widget.value = value;
  if (node?.widgets) {
    node.widgets_values = node.widgets.map((item) => item.value);
  }
  if (typeof widget.callback === "function") {
    widget.callback(value, app.canvas, node);
  }
  const graph = node?.graph;
  if (graph && typeof graph.setDirtyCanvas === "function") {
    graph.setDirtyCanvas(true, true);
  }
}

/**
 * POST a local file to Comfy /upload/image and select it on the combo.
 * @param {EzNode} node
 * @param {EzWidget} widget
 * @param {File} file
 * @returns {Promise<void>}
 */
async function uploadToInput(node, widget, file) {
  const body = new FormData();
  body.append("image", file);
  const resp = await api.fetchApi("/upload/image", {
    method: "POST",
    body,
  });
  if (resp.status !== 200) {
    throw new Error(`upload failed: ${resp.status}`);
  }
  const data = await resp.json();
  let path = data.name;
  if (data.subfolder) {
    path = `${data.subfolder}/${path}`;
  }
  setWidgetValue(node, widget, path);
}

/**
 * Copy an output-disk file into input/ and select it.
 * @param {EzNode} node
 * @param {EzWidget} widget
 * @param {string} rel
 * @returns {Promise<void>}
 */
async function chooseOutput(node, widget, rel) {
  const resp = await fetch(apiUrl("/ez_outputs/to-input"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rel }),
  });
  const data = await resp.json();
  if (!resp.ok) {
    throw new Error(data.error || resp.statusText);
  }
  setWidgetValue(node, widget, data.name || rel);
}

/**
 * List recent output-disk media of one kind.
 * @param {string} kind
 * @returns {Promise<EzOutputRow[]>}
 */
async function listOutputs(kind) {
  const resp = await fetch(
    apiUrl(`/ez_outputs/list?kind=${encodeURIComponent(kind)}&limit=40`),
  );
  const data = await resp.json();
  if (!resp.ok) {
    throw new Error(data.error || resp.statusText);
  }
  return Array.isArray(data.items) ? data.items : [];
}

/**
 * Mount upload + choose-from-outputs buttons on one or more load slots.
 * @param {EzNode} node
 * @param {{widget?: string, widgets?: string[], kind: string, accept: string}} spec
 * @returns {void}
 */
function bindPicker(node, spec) {
  if (node._ezMediaPickBound) {
    return;
  }
  const slots = spec.widgets || [spec.widget];
  const named = slots.map((name) => widgetByName(node, name)).filter(Boolean);
  if (!named.length) {
    return;
  }
  node._ezMediaPickBound = true;
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = spec.accept;
  fileInput.style.display = "none";
  document.body.appendChild(fileInput);
  let target = named[0];
  fileInput.onchange = async () => {
    const file = fileInput.files?.[0];
    fileInput.value = "";
    if (!file) {
      return;
    }
    try {
      await uploadToInput(node, target, file);
    } catch (err) {
      console.error("[ez_image] upload failed", err);
    }
  };
  named.forEach((widget, index) => {
    const suffix = named.length > 1 ? ` ${index + 1}` : "";
    node.addWidget("button", `Upload media${suffix}`, `upload:${widget.name}`, () => {
      target = widget;
      fileInput.click();
    });
    node.addWidget(
      "button",
      `Choose from outputs${suffix}`,
      `outputs:${widget.name}`,
      async () => {
        let items = [];
        try {
          items = await listOutputs(spec.kind);
        } catch (err) {
          console.error("[ez_image] outputs list failed", err);
          return;
        }
        const names = items
          .map((row) => String(row.rel || row.name || ""))
          .filter(Boolean);
        if (!names.length) {
          window.alert("No matching files on the output disk yet.");
          return;
        }
        const picked = window.prompt(
          `Choose an output file for ${widget.name} (paste a relative path):\n` +
            names.slice(0, 12).join("\n"),
          names[0],
        );
        if (!picked) {
          return;
        }
        try {
          await chooseOutput(node, widget, picked);
        } catch (err) {
          console.error("[ez_image] choose output failed", err);
        }
      },
    );
  });
}

app.registerExtension({
  name: "ez_image.mediaPick",
  /**
   * Wrap load/filename nodes with upload + outputs browse.
   * @param {EzNodeType} nodeType
   * @param {EzNodeDef} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeType, nodeData) {
    const spec = TARGETS[nodeData?.name];
    if (!spec) {
      return;
    }
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    /**
     * Bind the media picker after the node is created.
     * @returns {void}
     */
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      bindPicker(this, spec);
    };
  },
});

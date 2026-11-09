/**
 * EZDubIngest frontend: native Upload media button next to the source combo.
 *
 * Nodes 2.0: uses addWidget("button") and widget.value. Vue STRING widgets
 * have no canvas textarea - treat inputEl as optional.
 */
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const ACCEPT =
  "audio/*,video/*,.wav,.mp3,.flac,.ogg,.m4a,.aac,.mp4,.mkv,.mov,.webm";

/**
 * Widget on an EZDubIngest node, as this file touches it: the source combo it
 * selects into, and the button widget it inserts beside it. LiteGraph owns the
 * rest of the shape, so every field stays optional.
 * @typedef {Object} EzWidget
 * @property {string=} name Widget name as the node lists it.
 * @property {string=} value Media path the combo has selected.
 * @property {string=} label Text shown on the button widget.
 * @property {boolean=} serialize Kept out of the saved graph.
 * @property {(() => Promise<undefined>)=} serializeValue Empty saved value.
 * @property {{values?: string[]}=} options Combo choices; push appends one.
 * @property {((value: string) => unknown)=} callback Fired on a value change.
 */

/**
 * EZDubIngest node while it is being created. Only the members this file
 * touches are named; the LiteGraph node class owns the rest.
 * @typedef {Object} EzNode
 * @property {EzWidget[]=} widgets Widgets on the node, in graph order.
 * @property {((kind: string, label: string, value: string,
 *   onClick: () => void) => EzWidget)} addWidget Adds one widget.
 * @property {(() => void)=} onRemoved Hook wrapped to drop the file input.
 */

/**
 * Node definition Comfy hands to beforeRegisterNodeDef.
 * @typedef {Object} EzNodeDef
 * @property {string=} name Class name this file matches on.
 */

/**
 * Node class handed to beforeRegisterNodeDef; only the hook this file wraps
 * is named, LiteGraph owns the class itself.
 * @typedef {Object} EzNodeType
 * @property {{onNodeCreated?: (this: EzNode) => void}} prototype
 *   Per-instance hooks.
 */

/**
 * POST a local file to Comfy /upload/image and select it on the source combo.
 * @param {EzWidget} sourceWidget
 * @param {File} file
 * @returns {Promise<void>}
 */
async function uploadToInput(sourceWidget, file) {
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
  const values = sourceWidget.options?.values;
  if (Array.isArray(values) && !values.includes(path)) {
    values.push(path);
  }
  sourceWidget.value = path;
  sourceWidget.callback?.(path);
}

app.registerExtension({
  name: "ez_dub.ingestUpload",
  /**
   * Wrap EZDubIngest so the source combo gets an Upload media button.
   * @param {EzNodeType} nodeType
   * @param {EzNodeDef} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData?.name !== "EZDubIngest") {
      return;
    }
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    /**
     * Mount a hidden file input and a native button widget after source.
     * @returns {void}
     */
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      const sourceWidget = this.widgets?.find((w) => w.name === "source");
      if (!sourceWidget) {
        return;
      }
      const fileInput = document.createElement("input");
      fileInput.type = "file";
      fileInput.accept = ACCEPT;
      fileInput.style.display = "none";
      document.body.appendChild(fileInput);
      fileInput.onchange = async () => {
        const file = fileInput.files?.[0];
        fileInput.value = "";
        if (!file) {
          return;
        }
        try {
          await uploadToInput(sourceWidget, file);
        } catch (err) {
          console.error("[ez_dub] upload failed", err);
        }
      };
      const uploadWidget = this.addWidget("button", "upload", "", () => {
        fileInput.click();
      });
      uploadWidget.label = "Upload media";
      uploadWidget.serialize = false;
      uploadWidget.serializeValue = async () => undefined;
      const widgets = this.widgets;
      const from = widgets.indexOf(uploadWidget);
      const after = widgets.indexOf(sourceWidget);
      if (from > 0 && after >= 0 && from !== after + 1) {
        widgets.splice(from, 1);
        widgets.splice(after + 1, 0, uploadWidget);
      }
      const onRemoved = this.onRemoved;
      /**
       * Remove the hidden file input when the node is deleted.
       * @returns {void}
       */
      this.onRemoved = function () {
        fileInput.remove();
        onRemoved?.apply(this, arguments);
      };
    };
  },
});

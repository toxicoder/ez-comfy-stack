/**
 * EZDubIngest frontend: native Upload media button next to the source combo.
 *
 * Nodes 2.0: uses addWidget("button") and widget.value. Vue STRING widgets
 * have no canvas textarea — treat inputEl as optional.
 */
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const ACCEPT =
  "audio/*,video/*,.wav,.mp3,.flac,.ogg,.m4a,.aac,.mp4,.mkv,.mov,.webm";

/**
 * POST a local file to Comfy /upload/image and select it on the source combo.
 * @param {object} sourceWidget
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
   * @param {object} nodeType
   * @param {object} nodeData
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

import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

const NODE_CLASSES = new Set([
  "EZKleinPromptEnhance",
  "EZWanPromptEnhance",
  "EZLTXPromptEnhance",
]);

const PREVIEW = "CLIP prompt";

function textFromMessage(message) {
  const raw = message?.text;
  if (raw == null) {
    return "";
  }
  if (Array.isArray(raw)) {
    return raw.filter(Boolean).join("\n");
  }
  return String(raw);
}

function populate(node, text) {
  if (!node.widgets) {
    return;
  }
  let widget = node.widgets.find((w) => w.name === PREVIEW);
  if (!widget) {
    const made = ComfyWidgets.STRING(
      node,
      PREVIEW,
      ["STRING", { multiline: true }],
      app,
    );
    widget = made.widget;
    widget.serialize = false;
    widget.serializeValue = async () => undefined;
    if (widget.inputEl) {
      widget.inputEl.readOnly = true;
      widget.inputEl.style.opacity = "0.75";
    }
  }
  widget.value = text;
  requestAnimationFrame(() => {
    node.onResize?.(node.size);
  });
}

app.registerExtension({
  name: "ez_prompt_enhance.preview",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (!NODE_CLASSES.has(nodeData.name)) {
      return;
    }
    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      onExecuted?.apply(this, arguments);
      populate(this, textFromMessage(message));
    };
  },
});

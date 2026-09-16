import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

const NODE_CLASSES = new Set(["EZAppForge"]);

const PATH = "Path";
const TEMPLATE = "Picked template";
const OCCUPANCY = "Result occupancy";
const WIDGETS = "Widgets";
const STATUS = "Forge status";

function textFromMessage(message, key) {
  const raw = message?.[key];
  if (raw == null) {
    return "";
  }
  if (Array.isArray(raw)) {
    return raw.filter(Boolean).join("\n");
  }
  return String(raw);
}

function upsertWidget(node, name, text, multiline) {
  if (!node.widgets) {
    return;
  }
  let widget = node.widgets.find((w) => w.name === name);
  if (!widget) {
    const made = ComfyWidgets.STRING(
      node,
      name,
      ["STRING", { multiline }],
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
}

function populate(node, path, template, occupancy, widgets, status) {
  upsertWidget(node, PATH, path, true);
  upsertWidget(node, TEMPLATE, template, false);
  upsertWidget(node, OCCUPANCY, occupancy, false);
  upsertWidget(node, WIDGETS, widgets, true);
  upsertWidget(node, STATUS, status, false);
}

app.registerExtension({
  name: "ez_studio_forge.preview",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (!NODE_CLASSES.has(nodeData.name)) {
      return;
    }
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      populate(this, "", "", "", "", "Queue to forge an App");
    };
    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      onExecuted?.apply(this, arguments);
      populate(
        this,
        textFromMessage(message, "text"),
        textFromMessage(message, "template"),
        textFromMessage(message, "occupancy"),
        textFromMessage(message, "widgets"),
        textFromMessage(message, "passthrough"),
      );
    };
  },
});

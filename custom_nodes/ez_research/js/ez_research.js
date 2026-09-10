import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

const NODE_CLASSES = new Set(["EZCreativeResearch"]);

const REPLY = "Reply";
const SOURCES = "Sources";
const STATUS = "Research status";

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

function populate(node, text, sources, status) {
  upsertWidget(node, REPLY, text, true);
  upsertWidget(node, SOURCES, sources, true);
  upsertWidget(node, STATUS, status, false);
  requestAnimationFrame(() => {
    node.onResize?.(node.size);
  });
}

app.registerExtension({
  name: "ez_research.preview",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (!NODE_CLASSES.has(nodeData.name)) {
      return;
    }
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      populate(this, "", "", "Queue to research");
    };
    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      onExecuted?.apply(this, arguments);
      populate(
        this,
        textFromMessage(message, "text"),
        textFromMessage(message, "sources"),
        textFromMessage(message, "passthrough"),
      );
    };
  },
});

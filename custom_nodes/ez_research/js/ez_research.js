/**
 * EZCreativeResearch frontend: read-only reply, sources, and status widgets.
 *
 * Nodes 2.0: set widget.value; treat inputEl as optional (Vue STRING widgets
 * have no canvas textarea).
 */
import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

const NODE_CLASSES = new Set(["EZCreativeResearch"]);

const REPLY = "Reply";
const SOURCES = "Sources";
const STATUS = "Research status";

/**
 * Join a UI message field into a display string.
 * @param {object} message
 * @param {string} key
 * @returns {string}
 */
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

/**
 * Create or update a non-serialized STRING widget.
 * @param {object} node
 * @param {string} name
 * @param {string} text
 * @param {boolean} multiline
 * @returns {void}
 */
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

/**
 * Fill reply, sources, and status widgets on a research node.
 * @param {object} node
 * @param {string} text
 * @param {string} sources
 * @param {string} status
 * @returns {void}
 */
function populate(node, text, sources, status) {
  upsertWidget(node, REPLY, text, true);
  upsertWidget(node, SOURCES, sources, true);
  upsertWidget(node, STATUS, status, false);
}

app.registerExtension({
  name: "ez_research.preview",
  /**
   * Wrap EZCreativeResearch with preview widgets.
   * @param {object} nodeType
   * @param {object} nodeData
   * @returns {Promise<void>}
   */
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (!NODE_CLASSES.has(nodeData.name)) {
      return;
    }
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    /**
     * Seed empty preview widgets before the first queue.
     * @returns {void}
     */
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);
      populate(this, "", "", "Queue to research");
    };
    const onExecuted = nodeType.prototype.onExecuted;
    /**
     * Refresh preview widgets from the last execution payload.
     * @param {object} message
     * @returns {void}
     */
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

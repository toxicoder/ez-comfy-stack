/**
 * EZAppForge frontend: read-only path, template, occupancy, and status widgets.
 *
 * Nodes 2.0: set widget.value; treat inputEl as optional (Vue STRING widgets
 * have no canvas textarea).
 */
import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

const NODE_CLASSES = new Set(["EZAppForge"]);

const PATH = "Path";
const TEMPLATE = "Picked template";
const OCCUPANCY = "Result occupancy";
const WIDGETS = "Widgets";
const STATUS = "Forge status";

/**
 * Canvas textarea a STRING widget owns; absent on the Vue STRING widgets
 * Nodes 2.0 renders.
 * @typedef {Object} EzInputEl
 * @property {boolean=} readOnly Locks the field; the text is output only.
 * @property {{opacity?: string}=} style Inline style, dimmed when read-only.
 */

/**
 * Widget on a forge node, as this file touches it. LiteGraph owns the rest of
 * the shape, so every field stays optional.
 * @typedef {Object} EzWidget
 * @property {string=} name Widget name upsertWidget matches on.
 * @property {string=} value Text painted into the widget.
 * @property {boolean=} serialize Kept out of the saved graph.
 * @property {(() => Promise<undefined>)=} serializeValue Empty saved value.
 * @property {EzInputEl=} inputEl Canvas textarea, only on legacy widgets.
 */

/**
 * Node this file paints. LiteGraph owns everything the file never reads.
 * @typedef {Object} EzNode
 * @property {EzWidget[]=} widgets Widgets on the node, in graph order.
 */

/**
 * Node definition Comfy hands to beforeRegisterNodeDef.
 * @typedef {Object} EzNodeDef
 * @property {string=} name Class name this file matches on.
 */

/**
 * Node class handed to beforeRegisterNodeDef; only the hooks this file wraps
 * are named, LiteGraph owns the class itself.
 * @typedef {Object} EzNodeType
 * @property {{
 *   onNodeCreated?: (this: EzNode) => void,
 *   onExecuted?: (this: EzNode, message: EzExecutedMessage) => void
 * }} prototype Per-instance hooks.
 */

/**
 * Payload Comfy hands onExecuted: the node's UI fields, each one text or a
 * list of lines this file joins.
 * @typedef {Object<string, string|string[]>} EzExecutedMessage
 */

/**
 * Join a UI message field into a display string.
 * @param {EzExecutedMessage} message
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
 * @param {EzNode} node
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
 * Fill path, template, occupancy, widgets, and status on a forge node.
 * @param {EzNode} node
 * @param {string} path
 * @param {string} template
 * @param {string} occupancy
 * @param {string} widgets
 * @param {string} status
 * @returns {void}
 */
function populate(node, path, template, occupancy, widgets, status) {
  upsertWidget(node, PATH, path, true);
  upsertWidget(node, TEMPLATE, template, false);
  upsertWidget(node, OCCUPANCY, occupancy, false);
  upsertWidget(node, WIDGETS, widgets, true);
  upsertWidget(node, STATUS, status, false);
}

app.registerExtension({
  name: "ez_studio_forge.preview",
  /**
   * Wrap EZAppForge with preview widgets.
   * @param {EzNodeType} nodeType
   * @param {EzNodeDef} nodeData
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
      populate(this, "", "", "", "", "Queue to forge an App");
    };
    const onExecuted = nodeType.prototype.onExecuted;
    /**
     * Refresh preview widgets from the last execution payload.
     * @param {EzExecutedMessage} message
     * @returns {void}
     */
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

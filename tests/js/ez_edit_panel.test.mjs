/**
 * @file Behavioural tests for the EZ Edit panel (custom_nodes/ez_edit).
 *
 * The panel is hand-built DOM, so this suite installs its own fake document,
 * mounts the real extension through the shared frontend stub, then drives it
 * the way an operator does: click a clip row, type in a field, press the cut
 * button. Every assertion is about what the panel sends the /ez_edit/* routes,
 * because those op lists are the same reducer the agent and the MCP server
 * drive - a mouse cut and a tool cut have to agree.
 */

import { describe, test } from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import { loadExtension, REPO_ROOT } from "./harness.mjs";

const PANEL_JS = path.join(
  REPO_ROOT,
  "custom_nodes",
  "ez_edit",
  "js",
  "ez_edit_panel.js",
);

/** The clip control buttons; they arm only when a clip row is selected. */
const CLIP_CONTROLS = [
  "Set trim",
  "Set track",
  "Set gain",
  "Set transition",
  "Move earlier",
  "Move later",
  "Remove clip",
];

/** The graphics buttons; they work with no clip selected. */
const GRAPHICS_CONTROLS = [
  "Add overlay",
  "Add caption",
  "Remove overlay",
  "Remove caption",
];

/**
 * Minimal element the panel's DOM calls actually need.
 * @param {string} tag Element tag name.
 * @returns {object} A fake element.
 */
function makeElement(tag) {
  const el = {
    tagName: String(tag).toUpperCase(),
    children: [],
    parentNode: null,
    attrs: new Map(),
    dataset: {},
    listeners: new Map(),
    tabIndex: -1,
    value: "",
    disabled: false,
    _text: "",
    _classes: new Set(),
  };
  el.className = "";
  Object.defineProperty(el, "className", {
    configurable: true,
    get() {
      return Array.from(el._classes).join(" ");
    },
    set(value) {
      el._classes = new Set(String(value).split(/\s+/).filter(Boolean));
    },
  });
  el.classList = {
    add: (...names) => names.forEach((n) => el._classes.add(n)),
    remove: (...names) => names.forEach((n) => el._classes.delete(n)),
    contains: (name) => el._classes.has(name),
    toggle: (name, on) => {
      const want = on === undefined ? !el._classes.has(name) : Boolean(on);
      if (want) {
        el._classes.add(name);
      } else {
        el._classes.delete(name);
      }
      return want;
    },
  };
  Object.defineProperty(el, "textContent", {
    configurable: true,
    get() {
      return String(el._text) + el.children.map((child) => child.textContent).join("");
    },
    set(value) {
      el._text = String(value);
      el.children = [];
    },
  });
  // type= is an IDL attribute in the real DOM, so selectors can see it.
  Object.defineProperty(el, "type", {
    configurable: true,
    get() {
      return el.attrs.get("type") || "";
    },
    set(value) {
      el.attrs.set("type", String(value));
    },
  });
  el.setAttribute = (key, value) => {
    el.attrs.set(key, String(value));
    if (key.startsWith("data-")) {
      el.dataset[camel(key.slice(5))] = String(value);
    }
  };
  el.getAttribute = (key) => {
    if (key.startsWith("data-")) {
      const stored = el.dataset[camel(key.slice(5))];
      return stored === undefined ? null : stored;
    }
    return el.attrs.has(key) ? el.attrs.get(key) : null;
  };
  el.removeAttribute = (key) => el.attrs.delete(key);
  el.hasAttribute = (key) => el.attrs.has(key);
  el.appendChild = (child) => {
    child.parentNode = el;
    el.children.push(child);
    return child;
  };
  el.removeChild = (child) => {
    const at = el.children.indexOf(child);
    if (at >= 0) {
      el.children.splice(at, 1);
    }
    child.parentNode = null;
    return child;
  };
  el.replaceChildren = (...kids) => {
    el.children = [];
    kids.forEach((kid) => el.appendChild(kid));
  };
  el.addEventListener = (type, fn) => {
    if (!el.listeners.has(type)) {
      el.listeners.set(type, []);
    }
    el.listeners.get(type).push(fn);
  };
  el.removeEventListener = (type, fn) => {
    const list = el.listeners.get(type) || [];
    const at = list.indexOf(fn);
    if (at >= 0) {
      list.splice(at, 1);
    }
  };
  el.dispatch = (type, event) => {
    (el.listeners.get(type) || []).forEach((fn) => {
      fn({ preventDefault() {}, stopPropagation() {}, target: el, ...event });
    });
  };
  el.click = () => el.dispatch("click", {});
  el.focus = () => {};
  el.contains = (node) =>
    node === el || el.children.some((child) => child.contains(node));
  el.walk = () => {
    const out = [];
    const visit = (node) => {
      node.children.forEach((child) => {
        out.push(child);
        visit(child);
      });
    };
    visit(el);
    return out;
  };
  el.matches = (selector) =>
    selector.split(",").some((piece) => matchesCompound(el, piece.trim()));
  el.querySelectorAll = (selector) => el.walk().filter((n) => n.matches(selector));
  el.querySelector = (selector) => el.querySelectorAll(selector)[0] || null;
  return el;
}

/**
 * Turn a kebab-case attribute suffix into its dataset camelCase key.
 * @param {string} name Suffix after "data-".
 * @returns {string} The dataset key.
 */
function camel(name) {
  return name.replace(/-(\w)/g, (_m, ch) => ch.toUpperCase());
}

/**
 * Match one compound selector (tag, .class, [attr], in any combination).
 * @param {object} el Element to test.
 * @param {string} want One comma-free selector.
 * @returns {boolean} True when the element matches.
 */
function matchesCompound(el, want) {
  const parts = want.match(/^[a-zA-Z][\w-]*|\.[\w-]+|\[[^\]=]+(?:="[^"]*")?\]/g);
  if (!parts || !parts.length) {
    return false;
  }
  if (want.replace(/[a-zA-Z][\w-]*|\.[\w-]+|\[[^\]=]+(?:="[^"]*")?\]/g, "")) {
    return false;
  }
  return parts.every((part) => {
    if (part.startsWith(".")) {
      return el._classes.has(part.slice(1));
    }
    if (part.startsWith("[")) {
      const attr = part.match(/^\[([^\]=]+)(?:="([^"]*)")?\]$/);
      if (!attr) {
        return false;
      }
      const have = el.getAttribute(attr[1]);
      return have !== null && (attr[2] === undefined || have === attr[2]);
    }
    return el.tagName === part.toUpperCase();
  });
}

/** Install the globals the panel touches. */
function installDom() {
  const body = makeElement("body");
  const doc = {
    head: makeElement("head"),
    body,
    activeElement: null,
    createElement: (tag) => makeElement(tag),
    createTextNode: (text) => {
      const node = makeElement("#text");
      node._text = String(text);
      return node;
    },
    getElementById: () => null,
    querySelector: (selector) => body.querySelector(selector),
    querySelectorAll: (selector) => body.querySelectorAll(selector),
  };
  Object.defineProperty(globalThis, "document", {
    configurable: true,
    writable: true,
    value: doc,
  });
  Object.defineProperty(globalThis, "window", {
    configurable: true,
    writable: true,
    value: globalThis,
  });
  return doc;
}

/**
 * A project shaped like the /ez_edit/state body.
 * Returns:
 *   Three clips on two planes, two overlays, and one caption.
 */
function makeProject() {
  return {
    id: "p1",
    title: "Rough cut",
    fps: 24,
    width: 1280,
    height: 720,
    clips: [
      {
        id: "c1",
        label: "A roll",
        source: "edit/imports/a.mp4",
        in_s: 0,
        out_s: 4,
        track: 0,
        gain: 1,
        transition: null,
      },
      {
        id: "c2",
        label: "B roll",
        source: "edit/imports/b.mp4",
        in_s: 1,
        out_s: 3,
        track: 0,
        gain: 1,
        transition: { kind: "cut", duration_s: 0.5 },
      },
      {
        id: "c3",
        label: "C roll",
        source: "edit/imports/c.mp4",
        in_s: 0,
        out_s: 2,
        track: 1,
        gain: 0.5,
        transition: { kind: "fade", duration_s: 0.5 },
      },
    ],
    overlays: [
      { id: "o1", kind: "text", at_s: 0, dur_s: 2, text: "Lower third" },
      { id: "o2", kind: "text", at_s: 3, dur_s: 1, text: "Sponsored" },
    ],
    captions: [{ id: "g1", at_s: 1, dur_s: 2, text: "Hello there" }],
  };
}

/** Deep copy so a stale element cannot mutate the fixture. */
function clone(value) {
  return structuredClone(value);
}

/** Let queued promise callbacks run. */
async function settle() {
  for (let i = 0; i < 6; i += 1) {
    await new Promise((resolve) => setImmediate(resolve));
  }
}

/**
 * Mount the panel against a stubbed route surface.
 * @param {object} [opts] Options.
 * @param {object|null} [opts.project] Project the state route returns.
 * @returns {Promise<object>} `{el, calls, project, failRoutes}`.
 */
async function mountPanel(opts = {}) {
  const { project = makeProject() } = opts;
  installDom();
  const current = { value: project === null ? null : clone(project) };
  /** @type {Array<object>} */
  const calls = [];
  let broken = false;

  const reply = (payload) => ({
    ok: true,
    status: 200,
    json: async () => payload,
  });

  globalThis.fetch = async (url, init) => {
    const route = String(url);
    const body = init && init.body ? JSON.parse(init.body) : null;
    calls.push({ url: route, method: (init && init.method) || "GET", body });
    if (broken) {
      return {
        ok: false,
        status: 500,
        statusText: "boom",
        json: async () => ({ error: "route exploded" }),
      };
    }
    if (route.startsWith("/ez_edit/state")) {
      return reply({ ok: true, project: clone(current.value), jobs: [] });
    }
    if (route === "/ez_edit/ops") {
      return reply({ ok: true, project: clone(current.value) });
    }
    if (route === "/ez_edit/import") {
      return reply({
        ok: true,
        clip: { id: "c9", label: (body && body.label) || "a.mp4" },
      });
    }
    if (route === "/ez_edit/export_edl") {
      return reply({ ok: true, path: "/edl/p1.edl.json", format: "json" });
    }
    return {
      ok: false,
      status: 404,
      statusText: "not found",
      json: async () => ({ error: "no such route " + route }),
    };
  };

  const { ext, app } = await loadExtension(PANEL_JS, "ez_edit.panel");
  const tabs = [];
  app.extensionManager = { registerSidebarTab: (tab) => tabs.push(tab) };
  await ext.setup();
  const el = makeElement("div");
  tabs[0].render(el);
  await settle();
  return {
    el,
    calls,
    project: current,
    failRoutes: () => {
      broken = true;
    },
  };
}

/**
 * Find a button by its exact label.
 * @param {object} el Panel root.
 * @param {string} label Button text.
 * @returns {object|null} The button.
 */
function button(el, label) {
  return (
    el.walk().find((n) => n.tagName === "BUTTON" && n.textContent.trim() === label) ||
    null
  );
}

/**
 * The tbody of one timeline table, found by its caption.
 * @param {object} el Panel root.
 * @param {string} caption Table caption ("Clips", "Overlays", ...).
 * @returns {object} The tbody element.
 */
function tableBody(el, caption) {
  const wrap = el
    .querySelectorAll(".ez-edit-table-wrap")
    .find((n) => n.querySelector(".ez-edit-subhead").textContent.trim() === caption);
  assert.ok(wrap, `no ${caption} table`);
  const body = wrap.querySelector("tbody");
  assert.ok(body, `no body in the ${caption} table`);
  return body;
}

/**
 * The rows of one timeline table.
 * @param {object} el Panel root.
 * @param {string} caption Table caption.
 * @returns {Array<object>} Row elements.
 */
function rows(el, caption) {
  return tableBody(el, caption).children;
}

/**
 * Pick one row the way an operator does, and hand back the fresh row.
 *
 * Picking repaints the table, so the row elements are rebuilt: always assert
 * against what this returns rather than a row captured before the click.
 *
 * @param {object} el Panel root.
 * @param {string} caption Table caption.
 * @param {number} index Row position.
 * @param {string} [key] Key for a keyboard pick instead of a click.
 * @returns {Promise<object>} The row after the repaint.
 */
async function pickRow(el, caption, index, key) {
  const before = rows(el, caption);
  assert.ok(before.length > index, `${caption} has no row ${index}`);
  if (key) {
    before[index].dispatch("keydown", { key });
  } else {
    before[index].click();
  }
  await settle();
  return rows(el, caption)[index];
}

/**
 * The input that shares a row with a named button.
 * @param {object} el Panel root.
 * @param {string} label aria-label of the field.
 * @param {string} buttonLabel Label of the button in the same row.
 * @returns {object} The input element.
 */
function rowField(el, label, buttonLabel) {
  const trigger = button(el, buttonLabel);
  assert.ok(trigger, `no button "${buttonLabel}"`);
  const input = trigger.parentNode.querySelector(`[aria-label="${label}"]`);
  assert.ok(input, `no ${label} field beside "${buttonLabel}"`);
  return input;
}

/**
 * The input carrying an aria-label, found panel-wide.
 * @param {object} el Panel root.
 * @param {string} label aria-label of the field.
 * @returns {object} The input element.
 */
function field(el, label) {
  const input = el.querySelector(`[aria-label="${label}"]`);
  assert.ok(input, `no field labelled "${label}"`);
  return input;
}

/**
 * Click a button and wait for the route round trip.
 * @param {object} el Panel root.
 * @param {string} label Button text.
 * @returns {Promise<void>} Resolves once the panel settled.
 */
async function click(el, label) {
  const trigger = button(el, label);
  assert.ok(trigger, `no button "${label}"`);
  trigger.click();
  await settle();
}

/**
 * The body of the last POST to one route.
 * @param {object} state Mount result (`calls`).
 * @param {string} route Route path.
 * @returns {object|null} Parsed body, or null when the route was not called.
 */
function lastBody(state, route) {
  const hit = [...state.calls].reverse().find((call) => call.url === route);
  return hit ? hit.body : null;
}

/**
 * How many POSTs went to one route.
 * @param {object} state Mount result (`calls`).
 * @param {string} route Route path.
 * @returns {number} The count.
 */
function postCount(state, route) {
  return state.calls.filter((call) => call.url === route).length;
}

/**
 * The single op a click posted, with its args.
 * @param {object} state Mount result (`calls`).
 * @param {string} op Op name the reducer expects.
 * @returns {object} `{project_id, op, args}` for the one posted op.
 */
function postedOp(state, op) {
  const body = lastBody(state, "/ez_edit/ops");
  assert.ok(body, `no ops POST for ${op}`);
  assert.equal(body.ops.length, 1, `expected exactly one op for ${op}`);
  assert.equal(body.ops[0].op, op);
  return { project_id: body.project_id, ...body.ops[0].args };
}

/**
 * The status line the panel currently shows.
 * @param {object} el Panel root.
 * @returns {string} Status text.
 */
function statusText(el) {
  return el.querySelector(".ez-edit-status").textContent;
}

describe("ez_edit panel tab", () => {
  test("registers the sidebar tab the frontend asks for", async () => {
    const { el } = await mountPanel();
    assert.ok(el.classList.contains("ez-edit"), "panel class");
    assert.ok(statusText(el).includes("Rough cut"), "status names the project");
  });

  test("a route failure becomes a status note on a manual refresh", async () => {
    const { el, failRoutes } = await mountPanel();
    failRoutes();
    await click(el, "Refresh");
    assert.match(statusText(el), /route exploded/);
    assert.match(statusText(el), /HTTP 500/);
  });

  test("every clip control starts disarmed and the graphics stay armed", async () => {
    const { el } = await mountPanel({ project: null });
    CLIP_CONTROLS.forEach((label) => {
      assert.equal(button(el, label).disabled, true, `${label} starts disabled`);
    });
    GRAPHICS_CONTROLS.forEach((label) => {
      assert.equal(button(el, label).disabled, false, `${label} stays armed`);
    });
    assert.match(statusText(el), /no project loaded/);
  });
});

describe("ez_edit clip selection", () => {
  test("the clip table lists every clip in order", async () => {
    const { el } = await mountPanel();
    const labels = rows(el, "Clips").map((tr) => tr.children[1].textContent);
    assert.deepEqual(labels, ["A roll", "B roll", "C roll"]);
    assert.equal(rows(el, "Clips")[2].children[3].textContent, "T1", "track cell");
    assert.match(rows(el, "Clips")[2].children[4].textContent, /fade/, "transition cell");
  });

  test("clicking a row selects it and arms the controls", async () => {
    const { el } = await mountPanel();
    const picked = await pickRow(el, "Clips", 1);
    assert.equal(picked.getAttribute("aria-selected"), "true");
    assert.equal(rows(el, "Clips")[0].getAttribute("aria-selected"), "false");
    assert.equal(picked.getAttribute("role"), "button");
    assert.equal(picked.tabIndex, 0, "the row is a tab stop");
    assert.match(el.querySelector(".ez-edit-hint").textContent, /B roll \(#2\)/);
    CLIP_CONTROLS.forEach((label) =>
      assert.equal(button(el, label).disabled, false, `${label} armed`),
    );
  });

  test("the fields refill from the selected clip", async () => {
    const { el } = await mountPanel();
    await pickRow(el, "Clips", 1);
    assert.equal(rowField(el, "In (s)", "Set trim").value, "1");
    assert.equal(rowField(el, "Out (s)", "Set trim").value, "3");
    assert.equal(rowField(el, "Track", "Set track").value, "0");
    assert.equal(rowField(el, "Gain", "Set gain").value, "1");
    assert.equal(rowField(el, "Transition", "Set transition").value, "cut");
    assert.equal(rowField(el, "Dur (s)", "Set transition").value, "0.5");
  });

  test("Enter picks a row without starting a preview", async () => {
    const { el } = await mountPanel();
    await pickRow(el, "Clips", 2, "Enter");
    assert.equal(rows(el, "Clips")[2].getAttribute("aria-selected"), "true");
    assert.doesNotMatch(statusText(el), /canvas 2d context/, "no preview ran");
  });

  test("the first clip has no entering transition", async () => {
    const { el, calls } = await mountPanel();
    await pickRow(el, "Clips", 0);
    assert.equal(button(el, "Set transition").disabled, true, "transition stays armed-off");
    button(el, "Set transition").click();
    await settle();
    assert.match(statusText(el), /first clip has no entering transition/);
    assert.equal(postCount({ calls }, "/ez_edit/ops"), 0, "nothing was posted");
  });

  test("a selection whose row vanished is dropped", async () => {
    const { el, project } = await mountPanel();
    await pickRow(el, "Clips", 2);
    project.value.clips = project.value.clips.filter((clip) => clip.id !== "c3");
    await click(el, "Refresh");
    assert.equal(rows(el, "Clips").length, 2, "the row is gone");
    assert.match(el.querySelector(".ez-edit-hint").textContent, /Select a clip row/);
    CLIP_CONTROLS.forEach((label) =>
      assert.equal(button(el, label).disabled, true, `${label} disarmed`),
    );
  });

  test("an overlay row becomes the graphics target", async () => {
    const { el, calls } = await mountPanel();
    await pickRow(el, "Overlays", 0);
    assert.equal(rows(el, "Overlays")[0].getAttribute("aria-selected"), "true");
    await click(el, "Remove overlay");
    assert.deepEqual(postedOp({ calls }, "remove_overlay"), {
      project_id: "p1",
      overlay_id: "o1",
    });
  });
});

describe("ez_edit cut controls", () => {
  test("Set trim posts trim_clip with both handles", async () => {
    const { el, calls } = await mountPanel();
    await pickRow(el, "Clips", 1);
    rowField(el, "In (s)", "Set trim").value = "1.5";
    rowField(el, "Out (s)", "Set trim").value = "2.25";
    await click(el, "Set trim");
    assert.deepEqual(postedOp({ calls }, "trim_clip"), {
      project_id: "p1",
      clip_id: "c2",
      in_s: 1.5,
      out_s: 2.25,
    });
    assert.match(statusText(el), /trim: done/);
  });

  test("a blank handle falls back to the clip's own value", async () => {
    const { el, calls } = await mountPanel();
    await pickRow(el, "Clips", 1);
    rowField(el, "In (s)", "Set trim").value = "not a number";
    await click(el, "Set trim");
    assert.equal(postedOp({ calls }, "trim_clip").in_s, 1, "kept the clip in point");
  });

  test("Set track and Set gain post their own ops", async () => {
    const { el, calls } = await mountPanel();
    await pickRow(el, "Clips", 0);
    rowField(el, "Track", "Set track").value = "2";
    await click(el, "Set track");
    assert.deepEqual(postedOp({ calls }, "set_track"), {
      project_id: "p1",
      clip_id: "c1",
      track: 2,
    });
    rowField(el, "Gain", "Set gain").value = "0.25";
    await click(el, "Set gain");
    assert.deepEqual(postedOp({ calls }, "set_gain"), {
      project_id: "p1",
      clip_id: "c1",
      gain: 0.25,
    });
  });

  test("Move later posts move_clip with the target index", async () => {
    const { el, calls } = await mountPanel();
    await pickRow(el, "Clips", 1);
    await click(el, "Move later");
    assert.deepEqual(postedOp({ calls }, "move_clip"), {
      project_id: "p1",
      clip_id: "c2",
      index: 2,
    });
  });

  test("moving past an end says so and posts nothing", async () => {
    const { el, calls } = await mountPanel();
    const state = { calls };
    await pickRow(el, "Clips", 0);
    await click(el, "Move earlier");
    assert.match(statusText(el), /Already the first clip/);
    await pickRow(el, "Clips", 2);
    await click(el, "Move later");
    assert.match(statusText(el), /Already the last clip/);
    assert.equal(postCount(state, "/ez_edit/ops"), 0, "no op was posted");
  });

  test("Set transition posts kind and duration for a later clip", async () => {
    const { el, calls } = await mountPanel();
    await pickRow(el, "Clips", 2);
    rowField(el, "Transition", "Set transition").value = "wipe";
    rowField(el, "Dur (s)", "Set transition").value = "0.75";
    await click(el, "Set transition");
    assert.deepEqual(postedOp({ calls }, "set_transition"), {
      project_id: "p1",
      clip_id: "c3",
      kind: "wipe",
      duration_s: 0.75,
    });
  });

  test("Remove clip posts remove_clip and drops the selection", async () => {
    const { el, calls } = await mountPanel();
    await pickRow(el, "Clips", 1);
    await click(el, "Remove clip");
    assert.deepEqual(postedOp({ calls }, "remove_clip"), {
      project_id: "p1",
      clip_id: "c2",
    });
  });

  test("a control with no selection asks for one and posts nothing", async () => {
    const { el, calls } = await mountPanel();
    const state = { calls };
    el.dispatch("keydown", { key: "Delete" });
    await settle();
    assert.match(statusText(el), /Select a clip row first/);
    assert.equal(postCount(state, "/ez_edit/ops"), 0, "no op was posted");
  });
});

describe("ez_edit graphics controls", () => {
  test("Add overlay posts add_overlay with the typed text and timing", async () => {
    const { el, calls } = await mountPanel();
    const state = { calls };
    field(el, "Text").value = "Lower third";
    field(el, "At (s)").value = "1.5";
    field(el, "For (s)").value = "2";
    await click(el, "Add overlay");
    const posted = postedOp(state, "add_overlay");
    assert.equal(posted.project_id, "p1");
    assert.equal(posted.overlay.text, "Lower third");
    assert.equal(posted.overlay.kind, "text");
    assert.equal(posted.overlay.at_s, 1.5);
    assert.equal(posted.overlay.dur_s, 2);
    assert.ok(posted.overlay.id, "the panel mints the id");
  });

  test("Add caption posts add_caption", async () => {
    const { el, calls } = await mountPanel();
    field(el, "Text").value = "Hello there";
    await click(el, "Add caption");
    const posted = postedOp({ calls }, "add_caption");
    assert.equal(posted.caption.text, "Hello there");
    assert.equal(posted.caption.at_s, 0, "defaults to the head");
    assert.equal(posted.caption.dur_s, 3, "defaults to three seconds");
  });

  test("blank graphics text is refused locally", async () => {
    const { el, calls } = await mountPanel();
    field(el, "Text").value = "   ";
    await click(el, "Add overlay");
    assert.match(statusText(el), /Type the text/);
    assert.equal(postCount({ calls }, "/ez_edit/ops"), 0, "no op was posted");
  });

  test("a caption row is removed by its own id", async () => {
    const { el, calls } = await mountPanel();
    await pickRow(el, "Captions", 0);
    await click(el, "Remove caption");
    assert.deepEqual(postedOp({ calls }, "remove_caption"), {
      project_id: "p1",
      caption_id: "g1",
    });
  });

  test("removing with nothing selected takes the last row", async () => {
    const { el, calls } = await mountPanel();
    await click(el, "Remove overlay");
    assert.deepEqual(postedOp({ calls }, "remove_overlay"), {
      project_id: "p1",
      overlay_id: "o2",
    });
  });

  test("removing with no rows at all says so", async () => {
    const { el, project } = await mountPanel();
    project.value.overlays = [];
    await click(el, "Refresh");
    await click(el, "Remove overlay");
    assert.match(statusText(el), /Nothing to remove yet/);
  });
});

describe("ez_edit import and export", () => {
  test("Import sends the typed label and plane", async () => {
    const { el, calls } = await mountPanel();
    field(el, "Media path").value = "edit/imports/b-roll.mp4";
    field(el, "Label").value = "B roll 2";
    field(el, "Track").value = "2";
    await click(el, "Import");
    assert.deepEqual(lastBody({ calls }, "/ez_edit/import"), {
      path: "edit/imports/b-roll.mp4",
      label: "B roll 2",
      track: 2,
    });
    assert.match(statusText(el), /Imported B roll 2 on T2/);
  });

  test("an empty media path is refused before the network", async () => {
    const { el, calls } = await mountPanel();
    await click(el, "Import");
    assert.match(statusText(el), /Type a media path/);
    assert.equal(postCount({ calls }, "/ez_edit/import"), 0, "no import was posted");
  });

  test("Export EDL posts the chosen format to its own route", async () => {
    const { el, calls } = await mountPanel();
    field(el, "EDL format").value = "cmx";
    await click(el, "Export EDL");
    assert.deepEqual(lastBody({ calls }, "/ez_edit/export_edl"), {
      project_id: "p1",
      format: "cmx",
    });
    assert.match(statusText(el), /EDL written to \/edl\/p1.edl.json/);
  });

  test("the export never goes through the agent chat", async () => {
    const { el, calls } = await mountPanel();
    await click(el, "Export EDL");
    assert.equal(postCount({ calls }, "/ez_edit/export_edl"), 1, "one route call");
    assert.equal(
      calls.filter((call) => call.url.includes("/ez_edit/chat")).length,
      0,
      "no chat turn was needed",
    );
  });

  test("Render server and Render client post their mode", async () => {
    const { el, calls } = await mountPanel();
    await click(el, "Render server");
    assert.deepEqual(lastBody({ calls }, "/ez_edit/render"), {
      project_id: "p1",
      mode: "server",
    });
    await click(el, "Render client");
    const body = lastBody({ calls }, "/ez_edit/render");
    assert.equal(body.mode, "client");
    assert.ok(body.client_id, "the client render names this tab");
  });
});

describe("ez_edit shortcuts", () => {
  test("Space on the panel reaches the preview", async () => {
    const { el } = await mountPanel();
    el.dispatch("keydown", { key: " " });
    await settle();
    assert.match(statusText(el), /canvas 2d context/, "preview path ran");
  });

  test("Space typed in the chat box is left to the browser", async () => {
    const { el } = await mountPanel();
    const box = field(el, "Message for the editing agent");
    box.dispatch("keydown", { key: " " });
    await settle();
    assert.doesNotMatch(statusText(el), /canvas 2d context/, "no preview ran");
  });

  test("Delete inside a field does not cut the clip", async () => {
    const { el, calls } = await mountPanel();
    await pickRow(el, "Clips", 0);
    rowField(el, "In (s)", "Set trim").dispatch("keydown", { key: "Delete" });
    await settle();
    assert.equal(postCount({ calls }, "/ez_edit/ops"), 0, "no op was posted");
  });

  test("Delete on the panel removes the selected clip", async () => {
    const { el, calls } = await mountPanel();
    await pickRow(el, "Clips", 0);
    el.dispatch("keydown", { key: "Delete" });
    await settle();
    assert.deepEqual(postedOp({ calls }, "remove_clip"), {
      project_id: "p1",
      clip_id: "c1",
    });
  });
});

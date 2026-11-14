/**
 * @file 3D mesh rows in the Outputs sidebar (ez_outputs).
 *
 * The mesh lane must list, filter, preview as plain text, and download. It must
 * never reach for an img/video/audio tag (a GLB has no browser tag) and never
 * offer the LoadImage staging button the still/audio lanes show. This suite
 * mounts the real panel over a fake document and drives it the way an operator
 * does: chip click, list toggle, download click, double click.
 */

import { describe, test } from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import { loadExtension, REPO_ROOT } from "./harness.mjs";

const PANEL_JS = path.join(
  REPO_ROOT,
  "custom_nodes",
  "ez_outputs",
  "js",
  "ez_outputs.js",
);

/** Rows the list route returns: two meshes plus one still for contrast. */
const ROWS = [
  {
    rel: "trellis/mug_00001_.glb",
    name: "mug_00001_.glb",
    kind: "model3d",
    size: 20480,
    mtime: 1700000002,
    suffix: ".glb",
    parent: "trellis",
  },
  {
    rel: "handle.gltf",
    name: "handle.gltf",
    kind: "model3d",
    size: 1024,
    mtime: 1700000001,
    suffix: ".gltf",
    parent: "",
  },
  {
    rel: "still.png",
    name: "still.png",
    kind: "image",
    size: 2048,
    mtime: 1700000000,
    suffix: ".png",
    parent: "",
  },
];

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

/**
 * Minimal element the explorer's DOM calls actually need.
 * @param {string} tag Element tag name.
 * @param {string=} ns Namespace for SVG creation.
 * @returns {object} A fake element.
 */
function makeElement(tag, ns) {
  const el = {
    tagName: String(tag).toUpperCase(),
    namespace: ns || null,
    children: [],
    parentNode: null,
    attrs: new Map(),
    dataset: {},
    style: {
      props: new Map(),
      setProperty(key, value) {
        this.props.set(key, String(value));
      },
      getPropertyValue(key) {
        return this.props.get(key) || "";
      },
    },
    listeners: new Map(),
    tabIndex: -1,
    checked: false,
    value: "",
    disabled: false,
    clientWidth: 800,
    offsetWidth: 800,
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
  el.insertBefore = (child, ref) => {
    const at = el.children.indexOf(ref);
    el.children.splice(at < 0 ? el.children.length : at, 0, child);
    child.parentNode = el;
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
  el.remove = () => {
    if (el.parentNode) {
      el.parentNode.removeChild(el);
    }
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
  el.focus = () => {
    globalThis.document.activeElement = el;
  };
  el.blur = () => {};
  el.select = () => {};
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

/** Every element the panel asked the document to build since the last mount. */
let built = [];

/** Install the globals the panel touches. */
function installDom() {
  built = [];
  const doc = {
    head: makeElement("head"),
    body: makeElement("body"),
    activeElement: null,
    createElement: (tag) => {
      const el = makeElement(tag);
      built.push(el);
      return el;
    },
    createElementNS: (ns, tag) => makeElement(tag, ns),
    createTextNode: (text) => {
      const node = makeElement("#text");
      node._text = String(text);
      return node;
    },
    getElementById: () => null,
    execCommand: () => false,
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
  Object.defineProperty(globalThis, "navigator", {
    configurable: true,
    writable: true,
    value: {},
  });
  globalThis.matchMedia = () => ({ matches: false });
  globalThis.IntersectionObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
  globalThis.ResizeObserver = class {
    constructor(cb) {
      this.cb = cb;
    }
    observe() {}
    disconnect() {}
  };
  globalThis.confirm = () => true;
  globalThis.open = () => null;
  return doc;
}

/** Let queued promise callbacks and the download timer run. */
async function settle() {
  for (let i = 0; i < 5; i += 1) {
    await new Promise((resolve) => setImmediate(resolve));
  }
  await new Promise((resolve) => setTimeout(resolve, 250));
}

/**
 * Mount the explorer over the mesh fixture rows.
 * @param {object} [opts] Options.
 * @param {Array<object>} [opts.items] Rows the first page returns.
 * @param {number} [opts.width] Panel width in px, which picks the tier.
 * @returns {Promise<object>} `{el, urls}` plus the mount plumbing.
 */
async function mountOutputs(opts = {}) {
  const { items = ROWS, width = 800 } = opts;
  installDom();
  const doc = globalThis.document;
  const urls = [];
  const pages = [{ items, truncated: false, count: items.length }];
  let responseIndex = 0;

  globalThis.fetch = async (url) => {
    urls.push(String(url));
    const payload = pages[Math.min(responseIndex, pages.length - 1)];
    responseIndex += 1;
    return { ok: true, status: 200, json: async () => payload };
  };

  const { ext, app } = await loadExtension(PANEL_JS, "ez.outputs");
  const tabs = [];
  app.extensionManager = { registerSidebarTab: (tab) => tabs.push(tab) };
  await ext.setup();
  const tab = tabs[0];
  const el = makeElement("div");
  el.clientWidth = width;
  el.offsetWidth = width;
  tab.render(el);
  await settle();
  return { el, tab, doc, urls };
}

/**
 * Find a button by its exact label inside a subtree.
 * @param {object} root Subtree root.
 * @param {string} label Button text.
 * @returns {object|null} The button.
 */
function button(root, label) {
  return (
    root.walk().find((n) => n.tagName === "BUTTON" && n.textContent.trim() === label) ||
    null
  );
}

/**
 * The card or list row rendered for one rel.
 * @param {object} el Panel root.
 * @param {string} rel Relative path of the file.
 * @returns {object} The rendered item element.
 */
function itemFor(el, rel) {
  const found = el
    .querySelectorAll(".ez-out-card, .ez-out-row-item")
    .find((node) => node.dataset.rel === rel);
  assert.ok(found, `no pane item rendered for ${rel}`);
  return found;
}

describe("ez_outputs 3D mesh rows", () => {
  test("the 3D chip filters the pane and asks the route for meshes", async () => {
    const { el, urls } = await mountOutputs();
    const chip = button(el, "3D");
    assert.ok(chip, "no 3D filter chip in the toolbar");
    assert.equal(chip.dataset.kind, "model3d");
    chip.click();
    await settle();
    assert.match(urls[urls.length - 1], /kind=model3d/);
  });

  test("a mesh card carries the badge and never a media tag", async () => {
    const { el } = await mountOutputs();
    const card = itemFor(el, "trellis/mug_00001_.glb");
    const tags = card.walk().map((node) => node.tagName);
    for (const tag of ["IMG", "VIDEO", "AUDIO", "SOURCE"]) {
      assert.equal(tags.includes(tag), false, `mesh card built a <${tag.toLowerCase()}>`);
    }
    assert.equal(card.querySelectorAll(".ez-out-mesh-ph").length, 1);
    const badge = card.querySelector(".ez-out-badge-model3d");
    assert.ok(badge, "mesh card has no model3d badge");
    assert.equal(badge.textContent.trim(), "3D");
  });

  test("the still lane is untouched: it still renders an img", async () => {
    const { el } = await mountOutputs();
    const card = itemFor(el, "still.png");
    assert.equal(card.querySelectorAll("img").length, 1);
    assert.equal(card.querySelectorAll(".ez-out-mesh-ph").length, 0);
  });

  test("list view offers a mesh Download and no LoadImage staging", async () => {
    const { el } = await mountOutputs();
    button(el, "List").click();
    await settle();
    const row = itemFor(el, "trellis/mug_00001_.glb");
    const labels = row.querySelectorAll("button").map((b) => b.textContent.trim());
    assert.deepEqual(labels, ["Download", "Copy path", "Delete"]);
    row.querySelector("button").click();
    await settle();
    const anchor = built.find(
      (node) => node.tagName === "A" && node.download === "mug_00001_.glb",
    );
    assert.ok(anchor, "Download did not anchor the mesh file");
    assert.match(anchor.href, /^\/view\?filename=mug_00001_\.glb/);
    assert.match(anchor.href, /type=output/);
    assert.match(anchor.href, /subfolder=trellis/);
    const imageRow = itemFor(el, "still.png");
    const imageLabels = imageRow
      .querySelectorAll("button")
      .map((b) => b.textContent.trim());
    assert.deepEqual(imageLabels, ["Use as start image", "Copy path", "Delete"]);
  });

  test("the mesh lightbox shows a note, no tag, and no staging button", async () => {
    const { el } = await mountOutputs();
    itemFor(el, "trellis/mug_00001_.glb").dispatch("dblclick", {});
    await settle();
    const lightbox = el.querySelector(".ez-out-lightbox");
    assert.ok(lightbox, "no lightbox element");
    assert.equal(lightbox.classList.contains("is-open"), true);
    const tags = lightbox.walk().map((node) => node.tagName);
    for (const tag of ["IMG", "VIDEO", "AUDIO", "SOURCE"]) {
      assert.equal(tags.includes(tag), false, `mesh lightbox built a <${tag.toLowerCase()}>`);
    }
    assert.equal(lightbox.querySelectorAll(".ez-out-mesh-note").length, 1);
    const labels = lightbox.querySelectorAll("button").map((b) => b.textContent.trim());
    assert.equal(labels.includes("Download"), true);
    for (const absent of ["Copy to input", "Use as start image", "Use as start audio"]) {
      assert.equal(labels.includes(absent), false, `mesh lightbox offered ${absent}`);
    }
    button(lightbox, "Download").click();
    await settle();
    const anchor = built.find(
      (node) => node.tagName === "A" && node.download === "mug_00001_.glb",
    );
    assert.ok(anchor, "the lightbox Download did not anchor the mesh file");
  });

  test("the still lightbox still opens a playable tag", async () => {
    const { el } = await mountOutputs();
    itemFor(el, "still.png").dispatch("dblclick", {});
    await settle();
    const lightbox = el.querySelector(".ez-out-lightbox");
    assert.equal(lightbox.querySelectorAll("img").length, 1);
    const labels = lightbox.querySelectorAll("button").map((b) => b.textContent.trim());
    assert.equal(labels.includes("Use as start image"), true);
  });
});

/**
 * Rows whose kind has no browser preview at all: a mesh, a MIDI sequence, and
 * a dub QC report. Each carries the server-probed lines the card renders.
 */
const DETAIL_ROWS = [
  {
    rel: "assets/ez_cup_00001_.glb",
    name: "ez_cup_00001_.glb",
    kind: "model3d",
    size: 4096,
    mtime: 1700000006,
    suffix: ".glb",
    parent: "assets",
    lines: ["GLB - opens in Blender, no in-browser preview", "from plate.png"],
  },
  {
    rel: "songs/ez_breakwater_theme_00001_.mid",
    name: "ez_breakwater_theme_00001_.mid",
    kind: "midi",
    size: 512,
    mtime: 1700000005,
    suffix: ".mid",
    parent: "songs",
    lines: ["MIDI sequence - opens in a DAW", "4 tracks"],
  },
  {
    rel: "dubs/ep1/qc.json",
    name: "qc.json",
    kind: "report",
    size: 320,
    mtime: 1700000004,
    suffix: ".json",
    parent: "dubs/ep1",
    lines: ["QC fail", "mix is not speech-like (drone, hush, or tone)"],
  },
];

/**
 * The rendered text of one card's detail lines.
 * @param {object} el Panel root.
 * @param {string} rel Relative path of the file.
 * @returns {string[]} Line texts.
 */
function cardLines(el, rel) {
  return itemFor(el, rel)
    .querySelectorAll(".ez-out-line")
    .map((node) => node.textContent.trim());
}

describe("ez_outputs kinds without a browser preview", () => {
  test("the MIDI and Reports chips ask the route for those kinds", async () => {
    const { el, urls } = await mountOutputs({ items: DETAIL_ROWS });
    button(el, "MIDI").click();
    await settle();
    assert.match(urls[urls.length - 1], /kind=midi/);
    button(el, "Reports").click();
    await settle();
    assert.match(urls[urls.length - 1], /kind=report/);
  });

  test("a MIDI card badges, says what it is, and never builds a media tag", async () => {
    const { el } = await mountOutputs({ items: DETAIL_ROWS });
    const card = itemFor(el, "songs/ez_breakwater_theme_00001_.mid");
    const tags = card.walk().map((node) => node.tagName);
    for (const tag of ["IMG", "VIDEO", "AUDIO", "SOURCE"]) {
      assert.equal(tags.includes(tag), false, `MIDI card built a <${tag.toLowerCase()}>`);
    }
    assert.equal(card.querySelector(".ez-out-badge-midi").textContent.trim(), "MIDI");
    assert.equal(card.querySelectorAll(".ez-out-midi-ph").length, 1);
    assert.deepEqual(cardLines(el, "songs/ez_breakwater_theme_00001_.mid"), [
      "MIDI sequence - opens in a DAW",
      "4 tracks",
    ]);
  });

  test("a QC report card renders the verdict text under a Report badge", async () => {
    const { el } = await mountOutputs({ items: DETAIL_ROWS });
    const card = itemFor(el, "dubs/ep1/qc.json");
    assert.equal(card.querySelector(".ez-out-badge-report").textContent.trim(), "Report");
    assert.equal(card.querySelectorAll(".ez-out-report-ph").length, 1);
    assert.deepEqual(cardLines(el, "dubs/ep1/qc.json"), [
      "QC fail",
      "mix is not speech-like (drone, hush, or tone)",
    ]);
  });

  test("the mesh card names Blender instead of an in-browser preview", async () => {
    const { el } = await mountOutputs({ items: DETAIL_ROWS });
    assert.deepEqual(cardLines(el, "assets/ez_cup_00001_.glb"), [
      "GLB - opens in Blender, no in-browser preview",
      "from plate.png",
    ]);
  });

  test("list view downloads the unstageable kinds and always offers Copy path", async () => {
    const { el } = await mountOutputs({ items: DETAIL_ROWS });
    button(el, "List").click();
    await settle();
    for (const rel of [
      "assets/ez_cup_00001_.glb",
      "songs/ez_breakwater_theme_00001_.mid",
      "dubs/ep1/qc.json",
    ]) {
      const labels = itemFor(el, rel)
        .querySelectorAll("button")
        .map((b) => b.textContent.trim());
      assert.deepEqual(labels, ["Download", "Copy path", "Delete"], rel);
    }
  });

  test("the MIDI and report lightboxes print a note instead of a dead tag", async () => {
    const { el } = await mountOutputs({ items: DETAIL_ROWS });
    itemFor(el, "songs/ez_breakwater_theme_00001_.mid").dispatch("dblclick", {});
    await settle();
    let box = el.querySelector(".ez-out-lightbox");
    let tags = box.walk().map((node) => node.tagName);
    for (const tag of ["IMG", "VIDEO", "AUDIO", "SOURCE"]) {
      assert.equal(tags.includes(tag), false, `MIDI lightbox built a <${tag.toLowerCase()}>`);
    }
    assert.equal(box.querySelectorAll(".ez-out-mesh-note").length, 1);
    assert.match(box.textContent, /opens in a DAW/);
    const labels = box.querySelectorAll("button").map((b) => b.textContent.trim());
    assert.equal(labels.includes("Use as start audio"), false);
    assert.equal(labels.includes("Download"), true);
  });
});

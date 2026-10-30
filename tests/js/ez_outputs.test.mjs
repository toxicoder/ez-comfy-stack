/**
 * @file Behavioural tests for the Outputs sidebar explorer (ez_outputs).
 *
 * The panel is hand-built DOM, so this suite installs a small fake document,
 * mounts the real extension through the shared frontend stub, then drives it
 * the way an operator does: clicks, keystrokes, and resize.
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
    document.activeElement = el;
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
  const doc = {
    head: makeElement("head"),
    body: makeElement("body"),
    activeElement: null,
    createElement: (tag) => makeElement(tag),
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

/**
 * Build deterministic OutputRow fixtures.
 * @param {number} count Number of files.
 * @returns {Array<object>} Catalog-shaped rows.
 */
function makeRows(count) {
  return Array.from({ length: count }, (_unused, index) => ({
    rel: index % 3 === 0 ? `film/shot${index}.png` : `still${index}.png`,
    name: `img${index}.png`,
    kind: index % 5 === 0 ? "video" : index % 7 === 0 ? "audio" : "image",
    size: 1024 * (index + 1),
    mtime: 1700000000 + index,
    suffix: ".png",
    parent: index % 3 === 0 ? "film" : "",
  }));
}

/** Let queued promise callbacks run. */
async function settle() {
  for (let i = 0; i < 5; i += 1) {
    await new Promise((resolve) => setImmediate(resolve));
  }
}

/**
 * Mount the explorer with a stubbed list route.
 * @param {object} [opts] Options.
 * @param {Array<object>} [opts.items] Rows the first page returns.
 * @param {boolean} [opts.truncated] Whether the page was clipped.
 * @param {number} [opts.width] Panel width in px, which picks the tier.
 * @param {boolean} [opts.fail] Answer every request with a 500.
 * @param {boolean} [opts.defer] Hold the response until `release()`.
 * @returns {Promise<object>} `{el, tab, urls, release, setResponse}`.
 */
async function mountOutputs(opts = {}) {
  const {
    items = makeRows(12),
    truncated = false,
    width = 800,
    fail = false,
    defer = false,
  } = opts;
  installDom();
  const doc = globalThis.document;
  Object.defineProperty(globalThis, "navigator", {
    configurable: true,
    writable: true,
    value: {},
  });
  const urls = [];
  /** @type {Array<object>} */
  const pages = [{ items, truncated, count: items.length }];
  let responseIndex = 0;
  /** @type {Array<Function>} */
  const waiting = [];

  globalThis.fetch = async (url) => {
    urls.push(String(url));
    if (fail) {
      return {
        ok: false,
        status: 500,
        statusText: "boom",
        json: async () => ({ error: "outputs exploded" }),
      };
    }
    let payload = pages[Math.min(responseIndex, pages.length - 1)];
    responseIndex += 1;
    if (defer) {
      await new Promise((resolve) => waiting.push(resolve));
    }
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
  return {
    el,
    tab,
    doc,
    urls,
    release: () => waiting.splice(0).forEach((resolve) => resolve()),
    setResponse: (page) => {
      pages.push(page);
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
    el.walk().find((n) => n.tagName === "BUTTON" && n.textContent.trim() === label) || null
  );
}

/** Send one keystroke through the single panel keydown handler.
 * @param {object} el Panel root.
 * @param {string} key Key value.
 * @param {object} [extra] Extra event fields.
 */
function key(el, key, extra = {}) {
  el.dispatch("keydown", { key, ...extra });
}

/**
 * The rows the pane currently renders.
 * @param {object} el Panel root.
 * @returns {Array<object>} Card or row elements.
 */
function cards(el) {
  return el.querySelectorAll(".ez-out-card").length
    ? el.querySelectorAll(".ez-out-card")
    : el.querySelectorAll(".ez-out-row-item");
}

describe("ez_outputs tab", () => {
  test("registers the sidebar tab the frontend asks for", async () => {
    const { tab } = await mountOutputs();
    assert.equal(tab.id, "ez-outputs");
    assert.equal(tab.title, "Outputs");
    assert.equal(tab.type, "custom");
    assert.equal(typeof tab.render, "function");
  });

  test("a frontend without the sidebar API is not an error", async () => {
    installDom();
    const { ext, app } = await loadExtension(PANEL_JS, "ez.outputs");
    app.extensionManager = {};
    await ext.setup();
  });
});

describe("ez_outputs layout", () => {
  test("pins chrome around one scrolling pane", async () => {
    const { el } = await mountOutputs();
    assert.ok(el.querySelector(".ez-out-head"), "header");
    assert.ok(el.querySelector(".ez-out-toolbar"), "toolbar");
    assert.ok(el.querySelector(".ez-out-body"), "body row");
    const body = el.querySelector(".ez-out-body");
    assert.ok(body.querySelector(".ez-out-tree"), "folder rail inside body");
    assert.ok(body.querySelector(".ez-out-scroll"), "scroll pane inside body");
    assert.equal(
      el.children.indexOf(el.querySelector(".ez-out-status")),
      el.children.length - 3,
      "footer sits above the two dialogs",
    );
  });

  test("publishes the width tier it measured", async () => {
    assert.equal((await mountOutputs({ width: 320 })).el.dataset.tier, "compact");
    assert.equal((await mountOutputs({ width: 460 })).el.dataset.tier, "cozy");
    assert.equal((await mountOutputs({ width: 800 })).el.dataset.tier, "wide");
  });

  test("the status footer is a live region", async () => {
    const { el } = await mountOutputs();
    const status = el.querySelector(".ez-out-status");
    assert.equal(status.getAttribute("role"), "status");
    assert.equal(status.getAttribute("aria-live"), "polite");
  });

  test("breadcrumb, summary, and shortcut trigger are in the header", async () => {
    const { el } = await mountOutputs();
    const head = el.querySelector(".ez-out-head");
    assert.ok(head.querySelector(".ez-out-crumb"));
    assert.ok(head.querySelector(".ez-out-summary"));
    assert.ok(button(el, "Shortcuts"));
  });
});

describe("ez_outputs first page", () => {
  test("asks for the first page only", async () => {
    const { urls } = await mountOutputs();
    assert.match(urls[0], /\/ez_outputs\/list/);
    assert.match(urls[0], /limit=200/);
    assert.match(urls[0], /kind=all/);
  });

  test("shows skeletons while the page is in flight", async () => {
    const { el, release } = await mountOutputs({ defer: true });
    assert.equal(el.querySelectorAll(".ez-out-skeleton").length, 1);
    assert.ok(el.querySelectorAll(".ez-out-skeleton-card").length > 0);
    release();
    await settle();
    assert.equal(el.querySelectorAll(".ez-out-skeleton").length, 0);
    assert.equal(el.querySelectorAll(".ez-out-grid").length, 1);
  });

  test("renders one accessible card per file", async () => {
    const { el } = await mountOutputs({ items: makeRows(6) });
    const tiles = el.querySelectorAll(".ez-out-card");
    assert.equal(tiles.length, 6);
    tiles.forEach((tile) => {
      assert.equal(tile.getAttribute("role"), "gridcell");
      const box = tile.querySelector("input[type=\"checkbox\"]");
      assert.equal(box.type, "checkbox");
      assert.match(box.getAttribute("aria-label"), /Select /);
    });
    assert.match(el.querySelector(".ez-out-grid").getAttribute("aria-label"), /6 tiles/);
  });

  test("a clipped page grows on Load more", async () => {
    const { el, urls } = await mountOutputs({ items: makeRows(20), truncated: true });
    const more = el.querySelector(".ez-out-load-more");
    assert.ok(more, "load more button");
    more.click();
    await settle();
    assert.equal(urls.length, 2);
    assert.match(urls[1], /limit=400/);
  });

  test("list view shows sortable columns and grid hides them", async () => {
    const { el } = await mountOutputs({ items: makeRows(4) });
    assert.equal(el.querySelector(".ez-out-listhead"), null, "no header in grid view");
    key(el, "l");
    assert.equal(el.querySelectorAll(".ez-out-row-item").length, 4);
    const cols = el.querySelectorAll(".ez-out-col");
    assert.equal(cols.length, 3);
    cols.forEach((col) => assert.ok(col.hasAttribute("aria-sort")));
    key(el, "g");
    assert.equal(el.querySelectorAll(".ez-out-card").length, 4);
  });
});

describe("ez_outputs folders", () => {
  test("the rail lists every folder with a count", async () => {
    const { el } = await mountOutputs({ items: makeRows(9) });
    const items = el.querySelectorAll(".ez-out-tree-item");
    const labels = items.map((n) => n.querySelector(".ez-out-tree-label").textContent);
    assert.deepEqual(labels, ["All files", "root", "film"]);
    items.forEach((item) =>
      assert.match(item.querySelector(".ez-out-tree-count").textContent, /^\d+$/),
    );
  });

  test("picking a folder filters and remembers it", async () => {
    const { el } = await mountOutputs({ items: makeRows(9) });
    const film = el
      .querySelectorAll(".ez-out-tree-item")
      .find((n) => n.querySelector(".ez-out-tree-label").textContent === "film");
    film.click();
    assert.equal(localStorage.getItem("ez-comfy.outputs.folder"), "film");
    assert.equal(el.querySelectorAll(".ez-out-card").length, 3);
    assert.match(el.querySelector(".ez-out-crumb").textContent, /film/);
  });

  test("active filters become removable pills", async () => {
    const { el } = await mountOutputs({ items: makeRows(6) });
    assert.equal(el.querySelector(".ez-out-active").hasAttribute("hidden"), true);
    button(el, "Stills").click();
    await settle();
    const pills = el.querySelectorAll(".ez-out-pill");
    assert.equal(pills.length, 1);
    assert.match(pills[0].textContent, /Type: Still/);
  });
});

describe("ez_outputs selection", () => {
  test("click selects one file and owns the only tab stop", async () => {
    const { el } = await mountOutputs({ items: makeRows(5) });
    const tiles = el.querySelectorAll(".ez-out-card");
    tiles[1].click();
    const stops = el.querySelectorAll("[data-rel]").filter((n) => n.tabIndex === 0);
    assert.equal(stops.length, 1);
    assert.equal(stops[0], tiles[1]);
    assert.equal(tiles[1].getAttribute("aria-selected"), "true");
  });

  test("shift and arrow extends the selection instead of replacing it", async () => {
    const { el } = await mountOutputs({ items: makeRows(6) });
    const tiles = el.querySelectorAll(".ez-out-card");
    tiles[0].click();
    key(el, "ArrowRight");
    key(el, "ArrowRight", { shiftKey: true });
    key(el, "ArrowRight", { shiftKey: true });
    const chosen = el.querySelectorAll("[aria-selected=\"true\"]").length;
    assert.ok(chosen >= 3, `expected a growing range, got ${chosen}`);
  });

  test("selection survives a kind, folder, and view change", async () => {
    const { el } = await mountOutputs({ items: makeRows(9) });
    const tiles = el.querySelectorAll(".ez-out-card");
    tiles[0].click();
    tiles[3].dispatch("click", { ctrlKey: true });
    key(el, "l");
    key(el, "g");
    assert.equal(el.querySelectorAll("[aria-selected=\"true\"]").length, 2);
    assert.equal(el.querySelector(".ez-out-bulk-count").textContent, "2 files selected");
  });

  test("Select all takes the visible files and opens the bulk bar", async () => {
    const { el } = await mountOutputs({ items: makeRows(5) });
    button(el, "Select all").click();
    assert.equal(el.querySelectorAll("[aria-selected=\"true\"]").length, 5);
    assert.ok(el.querySelector(".ez-out-bulk").classList.contains("is-open"));
    assert.match(el.querySelector(".ez-out-bulk-count").textContent, /5 files selected/);
  });
});

describe("ez_outputs keyboard", () => {
  test("slash jumps to the filter box", async () => {
    const { el, doc } = await mountOutputs();
    doc.activeElement = null;
    key(el, "/");
    assert.equal(doc.activeElement, el.querySelector(".ez-out-search"));
  });

  test("? opens the shortcut sheet and Escape closes it", async () => {
    const { el } = await mountOutputs();
    key(el, "?");
    const help = el.querySelector(".ez-out-help");
    assert.equal(help.getAttribute("role"), "dialog");
    assert.ok(help.classList.contains("is-open"));
    assert.ok(help.querySelectorAll(".ez-out-kbd").length >= 10);
    key(el, "Escape");
    assert.ok(!help.classList.contains("is-open"));
  });

  test("g and l switch the view and persist it", async () => {
    const { el } = await mountOutputs({ items: makeRows(3) });
    key(el, "l");
    assert.equal(localStorage.getItem("ez-comfy.outputs.view"), "list");
    key(el, "g");
    assert.equal(localStorage.getItem("ez-comfy.outputs.view"), "grid");
  });

  test("Home and End jump to the ends", async () => {
    const { el } = await mountOutputs({ items: makeRows(6) });
    key(el, "End");
    const stops = el.querySelectorAll("[data-rel]").filter((n) => n.tabIndex === 0);
    assert.equal(stops[0], el.querySelectorAll(".ez-out-card")[5]);
    key(el, "Home");
    const back = el.querySelectorAll("[data-rel]").filter((n) => n.tabIndex === 0);
    assert.equal(back[0], el.querySelectorAll(".ez-out-card")[0]);
  });

  test("Escape clears the selection before it clears filters", async () => {
    const { el } = await mountOutputs({ items: makeRows(4) });
    el.querySelectorAll(".ez-out-card")[0].click();
    key(el, "Escape");
    assert.equal(el.querySelectorAll("[aria-selected=\"true\"]").length, 0);
    assert.ok(button(el, "Stills"), "filters survive while nothing is selected");
  });

  test("a keystroke inside the filter box is left alone", async () => {
    const { el } = await mountOutputs({ items: makeRows(3) });
    const search = el.querySelector(".ez-out-search");
    search.dispatch("keydown", { key: "g" });
    assert.equal(el.querySelectorAll(".ez-out-row-item").length, 0, "view did not flip");
  });
});

describe("ez_outputs density", () => {
  test("auto is the default and follows the tier", async () => {
    const { el } = await mountOutputs({ width: 800 });
    assert.match(el.style.getPropertyValue("--ez-out-thumb"), /^160px$/);
    assert.equal(button(el, "Size: Auto 160") !== null, true);
  });

  test("the Size button cycles and stores the choice", async () => {
    const { el } = await mountOutputs({ width: 800 });
    const sizeBtn = el
      .walk()
      .find((n) => n.tagName === "BUTTON" && n.textContent.startsWith("Size:"));
    sizeBtn.click();
    assert.equal(localStorage.getItem("ez-comfy.outputs.thumb"), "96");
    assert.equal(el.style.getPropertyValue("--ez-out-thumb"), "96px");
    sizeBtn.click();
    assert.equal(localStorage.getItem("ez-comfy.outputs.thumb"), "128");
  });

  test("plus, minus, and zero adjust and reset the density", async () => {
    const { el } = await mountOutputs({ width: 800 });
    key(el, "-");
    assert.equal(el.style.getPropertyValue("--ez-out-thumb"), "152px");
    key(el, "0");
    assert.equal(localStorage.getItem("ez-comfy.outputs.thumb"), "auto");
    assert.equal(el.style.getPropertyValue("--ez-out-thumb"), "160px");
  });
});

describe("ez_outputs preview", () => {
  test("double click opens a modal preview and moves focus in", async () => {
    const { el, doc } = await mountOutputs({ items: makeRows(3) });
    el.querySelectorAll(".ez-out-card")[0].dispatch("dblclick", {});
    const lightbox = el.querySelector(".ez-out-lightbox");
    assert.ok(lightbox.classList.contains("is-open"));
    assert.equal(lightbox.getAttribute("role"), "dialog");
    assert.equal(lightbox.getAttribute("aria-modal"), "true");
    assert.ok(lightbox.contains(doc.activeElement), "focus is inside the dialog");
  });

  test("Tab stays inside the preview and Escape restores focus", async () => {
    const { el, doc } = await mountOutputs({ items: makeRows(3) });
    const card = el.querySelectorAll(".ez-out-card")[1];
    card.dispatch("dblclick", {});
    const lightbox = el.querySelector(".ez-out-lightbox");
    key(el, "Tab");
    assert.ok(lightbox.contains(doc.activeElement), "tab is trapped");
    key(el, "Tab", { shiftKey: true });
    assert.ok(lightbox.contains(doc.activeElement), "shift-tab is trapped");
    key(el, "Escape");
    assert.ok(!lightbox.classList.contains("is-open"));
    assert.equal(doc.activeElement, card, "focus returned to the card");
  });

  test("arrows step through the preview", async () => {
    const { el } = await mountOutputs({ items: makeRows(3) });
    el.querySelectorAll(".ez-out-card")[0].dispatch("dblclick", {});
    const first = el.querySelector(".ez-out-lightbox-title").textContent;
    key(el, "ArrowRight");
    const second = el.querySelector(".ez-out-lightbox-title").textContent;
    assert.notEqual(first, second);
  });
});

describe("ez_outputs states", () => {
  test("a failed list drops stale rows and offers Retry", async () => {
    const { el, urls } = await mountOutputs({ items: makeRows(4) });
    assert.equal(cards(el).length, 4);
    globalThis.fetch = async (url) => {
      urls.push(String(url));
      return {
        ok: false,
        status: 500,
        statusText: "boom",
        json: async () => ({ error: "outputs exploded" }),
      };
    };
    button(el, "Refresh").click();
    await settle();
    assert.equal(cards(el).length, 0, "no stale rows");
    const fail = el.querySelector(".ez-out-fail");
    assert.ok(fail, "failure pane");
    assert.match(fail.textContent, /Retry/);
    assert.match(fail.textContent, /Report this problem/);
  });

  test("no files and filtered-nothing read differently", async () => {
    const empty = await mountOutputs({ items: [] });
    assert.equal(empty.el.querySelector(".ez-out-empty").dataset.variant, "nofiles");
    assert.match(empty.el.querySelector(".ez-out-empty").textContent, /History does not/);

    const filtered = await mountOutputs({ items: [] });
    button(filtered.el, "Video").click();
    await settle();
    const pane = filtered.el.querySelector(".ez-out-empty");
    assert.equal(pane.dataset.variant, "filtered");
    assert.match(pane.textContent, /No files match/);
    const clear = button(filtered.el, "Clear filters");
    assert.ok(clear, "clear affordance");
    clear.click();
    await settle();
    assert.equal(
      filtered.el.querySelector(".ez-out-empty").dataset.variant,
      "nofiles",
      "filters were reset",
    );
  });

  test("copy paths still reports when the clipboard is blocked", async () => {
    const { el } = await mountOutputs({ items: makeRows(2) });
    el.querySelectorAll(".ez-out-card")[0].click();
    button(el, "Copy paths").click();
    await settle();
    assert.match(el.querySelector(".ez-out-status").textContent, /[Cc]lipboard/);
  });

  test("the details preference tightens the card meta", async () => {
    const { el } = await mountOutputs({ items: makeRows(2) });
    button(el, "More").click();
    button(el, "Show details").click();
    assert.equal(localStorage.getItem("ez-comfy.outputs.meta"), "off");
    assert.ok(el.querySelector(".ez-out-card-meta.is-compact"));
  });
});

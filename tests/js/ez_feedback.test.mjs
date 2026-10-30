/**
 * @file Client contract for the ez_feedback core, run under `node --test`.
 *
 * Two operator-visible bugs live here. Both filed reports that said less than
 * the operator had typed.
 *
 * 1. A captured execution error was clipped at MAX_FIELD (300), so the ring
 *    buffer line - often the only copy of `exception_message` that survives
 *    the console - lost the failing op name, and the dialog's `## Recent
 *    errors` block quoted a truncated half sentence. `MAX_ERROR_TEXT` (2000)
 *    now covers message and detail, and the same cap renders them.
 * 2. "File directly" rebuilt the body from the payload, and the handoff link
 *    rebuilt it too, so everything the operator typed into the dialog
 *    textarea was dropped before GitHub ever saw it. Both paths now take the
 *    edited text (`fileDirect(partial, editedBody)`, `issueHrefFor(payload,
 *    editedBody)`), and when the URL ladder still has to cut the tail the
 *    core says so (`trimmed`) instead of silently shipping a short body.
 *
 * The narrative fields are the third leg of the same complaint: the four
 * headings used to be four copies of one placeholder. Filled fields now
 * render verbatim (no collapse, no clip) and an empty enhancement heading is
 * omitted rather than daring the operator to delete a comment.
 *
 * The core is imported as the real module: it sets no globals and guards every
 * DOM touch, so this file needs no jsdom and no npm dependency.
 */

import assert from "node:assert/strict";
import path from "node:path";
import { describe, test } from "node:test";

import {
  MAX_ERROR_TEXT,
  MAX_HREF,
  buildBody,
  buildTitle,
  enhanceText,
  fileDirect,
  githubIcon,
  issueHrefFor,
  recordError,
  recentErrors,
  reportPayload,
} from "../../custom_nodes/ez_feedback/js/ez_feedback_core.js";
import { REPO_ROOT, loadExtension } from "./harness.mjs";

const PANEL_JS = path.join(REPO_ROOT, "custom_nodes", "ez_feedback", "js", "ez_feedback_panel.js");

const CONFIG_ROUTE = "/ez_feedback/config";
const SUBMIT_ROUTE = "/ez_feedback/submit";
const ENHANCE_ROUTE = "/ez_feedback/enhance";

/**
 * Answer the three routes the core fetches, and record what was posted.
 * @param {object} [opts] `{submit, enhance}` - payloads to answer with; a
 *   value of `Error` makes that route reject instead.
 * @returns {Promise<object>} `{posts, restore}`.
 */
async function stubFetch(opts = {}) {
  const posts = { submit: [], enhance: [] };
  const original = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    const path = String(url);
    if (path.includes(CONFIG_ROUTE)) {
      return { ok: true, status: 200, json: async () => ({ tokenPresent: true, env: [] }) };
    }
    if (path.includes(SUBMIT_ROUTE)) {
      posts.submit.push(JSON.parse(init.body));
      if (opts.submit instanceof Error) {
        throw opts.submit;
      }
      const answer = opts.submit || { ok: true, url: "https://github.com/x/issues/1" };
      return { ok: answer.ok !== false, status: 200, json: async () => answer };
    }
    if (path.includes(ENHANCE_ROUTE)) {
      posts.enhance.push(JSON.parse(init.body));
      if (opts.enhance instanceof Error) {
        throw opts.enhance;
      }
      if (opts.enhanceStatus) {
        return {
          ok: false,
          status: opts.enhanceStatus,
          json: async () => (opts.enhance || { ok: false, error: "llm unavailable" }),
        };
      }
      const answer = opts.enhance || { ok: true, text: "## What happened\n\nbetter" };
      return { ok: answer.ok !== false, status: 200, json: async () => answer };
    }
    return { ok: false, status: 404, json: async () => ({}) };
  };
  return { posts, restore: () => { globalThis.fetch = original; } };
}

/** A payload whose `## Recent errors` block stays empty despite the ring. */
function noErrors() {
  return [{ surface: "test", message: "", detail: "" }];
}

describe("ez_feedback core error capture", () => {
  test("a 2500-char exception head survives the ring and the body", () => {
    const message = "RuntimeError: expected all " + "x".repeat(2400) + " END";
    const row = recordError({ surface: "load-error", message, detail: "y".repeat(2400) });

    assert.equal(row.message.length, MAX_ERROR_TEXT);
    assert.equal(row.detail.length, MAX_ERROR_TEXT);
    assert.equal(MAX_ERROR_TEXT, 2000);
    // The half of it a 300-char clip used to keep is not the useful half.
    assert.ok(recentErrors()[0].message.includes("expected all"));
    assert.equal(row.surface, "load-error");

    const body = buildBody({
      kind: "bug",
      surface: "load-error",
      blanks: false,
      errors: recentErrors(),
    });
    assert.ok(body.includes("## Recent errors"), body.slice(0, 120));
    assert.ok(body.includes("x".repeat(1500)), "the error line is not clipped to 300");
    assert.ok(body.includes("[load-error]"));
  });

  test("an entry without a message is still refused", () => {
    assert.equal(recordError({ surface: "global", message: "   " }), null);
  });
});

describe("ez_feedback core narrative", () => {
  test("filled bug fields replace the four placeholders, unfilled keep them", () => {
    const body = buildBody({
      kind: "bug",
      surface: "global",
      errors: noErrors(),
      narrative: {
        what_happened: "line one\n\nline two",
        expected: "   padded   ",
        actual: "z".repeat(5000),
      },
    });
    assert.ok(body.includes("## What happened\n\nline one\n\nline two"), body);
    assert.ok(body.includes("## Steps\n\n<!-- Replace this line. -->"), body);
    assert.ok(body.includes("## Expected\n\npadded"), body);
    assert.ok(body.includes("z".repeat(5000)), "narrative is never clipped");
    assert.ok(!body.includes("<!-- Replace this line. -->\n\n## Steps\n\n<!-- Replace"), body);
  });

  test("an enhancement omits the headings it has nothing for", () => {
    const body = buildBody({
      kind: "enhancement",
      surface: "global",
      errors: noErrors(),
      narrative: { problem: "the problem", alternatives: "tried X" },
    });
    assert.ok(body.includes("## Problem\n\nthe problem"), body);
    assert.ok(body.includes("## Alternatives\n\ntried X"), body);
    assert.ok(!body.includes("## Proposed solution"), body);
    assert.ok(!body.includes("## What it unlocks"), body);
    assert.ok(!body.includes("<!-- Replace this line. -->"), "no placeholders for a request");
  });

  test("reportPayload keeps the narrative and drops the blank fields", () => {
    const payload = reportPayload({ kind: "bug", narrative: { steps: " 1 ", problem: "x" } });
    assert.deepEqual(payload.narrative, { steps: " 1 " });
    assert.equal(reportPayload({ kind: "bug" }).narrative, null);
    assert.equal(reportPayload({ kind: "bug", narrative: { steps: "  " } }).narrative, null);
  });
});

describe("ez_feedback core handoff and filing", () => {
  test("issueHrefFor uses the edited body and reports when it cut the tail", () => {
    const partial = { kind: "bug", surface: "global", summary: "KSampler died", errors: noErrors() };

    const typed = "Typed by the operator: 4090 OOM on the second sampler.";
    const small = issueHrefFor(partial, typed);
    assert.equal(small.trimmed, false);
    assert.ok(small.href.startsWith("https://github.com/toxicoder/ez-comfy-stack/issues/new?"));
    assert.ok(small.href.includes("4090") && small.href.includes("OOM"), small.href.slice(0, 200));
    assert.ok(small.href.includes("labels=bug"));

    const fat = issueHrefFor(partial, "q".repeat(9000));
    assert.equal(fat.trimmed, true);
    assert.ok(fat.href.length <= MAX_HREF, `href ${fat.href.length} exceeds ${MAX_HREF}`);
    const note = new URLSearchParams({ body: "[report trimmed to fit the GitHub URL limit]" })
      .toString()
      .slice("body=".length);
    assert.ok(fat.href.includes(note), "the cut is stated in the body");

    // A blank edit falls back to the built body rather than filing nothing.
    const blank = issueHrefFor(partial, "   ");
    assert.ok(blank.href.includes("KSampler"), blank.href.slice(0, 200));
  });

  test("fileDirect posts the edited textarea, not a rebuilt body", async () => {
    const { posts, restore } = await stubFetch();
    try {
      const partial = { kind: "bug", surface: "global", summary: "KSampler died", errors: noErrors() };
      const edited = "## What happened\n\noperator words that rebuild would lose";
      const result = await fileDirect(partial, edited);

      assert.deepEqual(result, { ok: true, url: "https://github.com/x/issues/1" });
      assert.equal(posts.submit.length, 1);
      assert.equal(posts.submit[0].body, edited, "typed text reached the server verbatim");
      assert.equal(posts.submit[0].kind, "bug");
      assert.equal(posts.submit[0].title, buildTitle(partial));

      await fileDirect(partial, "  ");
      assert.notEqual(posts.submit[1].body, "  ");
      assert.ok(posts.submit[1].body.includes("## What happened"));
    } finally {
      restore();
    }
  });

  test("fileDirect never claims a link it does not have", async () => {
    const { restore } = await stubFetch({ submit: { ok: true } });
    try {
      const result = await fileDirect({ kind: "bug", surface: "global" }, "body");
      assert.equal(result.ok, false);
      assert.ok(result.error, result.error);
    } finally {
      restore();
    }
  });
});

describe("ez_feedback core enhance", () => {
  test("enhanceText posts kind and text and resolves the answer", async () => {
    const { posts, restore } = await stubFetch({ enhance: { ok: true, text: "## Problem\n\nsharp" } });
    try {
      const result = await enhanceText({ kind: "Enhancement ", text: "rough notes" });
      assert.deepEqual(result, { ok: true, text: "## Problem\n\nsharp" });
      assert.equal(posts.enhance[0].kind, "enhancement");
      assert.equal(posts.enhance[0].text, "rough notes");
    } finally {
      restore();
    }
  });

  test("enhanceText resolves, never rejects, on a dead route or a 503", async () => {
    const down = await stubFetch({ enhance: new Error("boom") });
    try {
      const result = await enhanceText({ kind: "bug", text: "notes" });
      assert.equal(result.ok, false);
      assert.ok(result.error.includes("boom"), result.error);
    } finally {
      down.restore();
    }

    const busy = await stubFetch({ enhanceStatus: 503, enhance: { ok: false, error: "llm unavailable" } });
    try {
      const result = await enhanceText({ kind: "bug", text: "notes" });
      assert.deepEqual(result, { ok: false, error: "llm unavailable" });
    } finally {
      busy.restore();
    }

    const empty = await enhanceText(null);
    assert.equal(empty.ok, false);
  });
});

describe("ez_feedback core without a DOM", () => {
  test("githubIcon is a clean no-op outside a browser", () => {
    assert.equal(githubIcon(), null);
  });
});

/**
 * Build one element of the throwaway DOM the panel renders into.
 *
 * Only the members `mountPanel` actually touches exist, so nothing in the
 * panel can lean on a browser feature this file has not modelled: children,
 * attributes (with the `data-*` to dataset mapping the kind toggle reads),
 * listeners, and the input fields.
 * @param {string} tag Element name, for failure messages only.
 * @returns {object} The fake element.
 */
function makeElement(tag) {
  const el = {
    tagName: tag,
    children: [],
    attrs: {},
    dataset: {},
    style: {},
    listeners: {},
    className: "",
    ownText: "",
    value: "",
    type: "",
    checked: false,
    disabled: false,
    rows: 0,
    spellcheck: true,
    placeholder: "",
    tabIndex: 0,
    classList: { add() {}, remove() {}, toggle() {} },
    append(...nodes) {
      el.children.push(...nodes);
    },
    appendChild(node) {
      el.children.push(node);
      return node;
    },
    replaceChildren(...nodes) {
      el.children = [...nodes];
    },
    setAttribute(key, value) {
      el.attrs[key] = String(value);
      if (key.startsWith("data-")) {
        el.dataset[key.slice(5).replace(/-([a-z])/g, (_m, c) => c.toUpperCase())] = String(value);
      }
    },
    getAttribute(key) {
      return key in el.attrs ? el.attrs[key] : null;
    },
    addEventListener(type, handler) {
      (el.listeners[type] = el.listeners[type] || []).push(handler);
    },
    click() {
      (el.listeners.click || []).forEach((handler) => handler({ type: "click" }));
    },
    input() {
      (el.listeners.input || []).forEach((handler) => handler({ type: "input" }));
    },
    change() {
      (el.listeners.change || []).forEach((handler) => handler({ type: "change" }));
    },
  };
  // textContent mirrors what the panel does with it: a set is the node's own
  // text (the preview, the status line), otherwise it reads its children.
  Object.defineProperty(el, "textContent", {
    configurable: true,
    get() {
      if (el.children.length) {
        return el.children.map((child) => (child && child.textContent) || "").join("");
      }
      return el.ownText;
    },
    set(value) {
      el.ownText = String(value === undefined || value === null ? "" : value);
    },
  });
  return el;
}

/** Depth-first list of every element below a root. */
function every(el, out = []) {
  (el.children || []).forEach((child) => {
    if (child && child.tagName) {
      out.push(child);
      every(child, out);
    }
  });
  return out;
}

/** First element below `root` matching `pred`. */
function find(root, pred) {
  return every(root).find(pred);
}

/** Elements below `root` matching `pred`. */
function findAll(root, pred) {
  return every(root).filter(pred);
}

/** The panel's stand-in core: it records what the form would file. */
function fakeCore(overrides = {}) {
  const reports = [];
  const enhancements = [];
  return Object.assign(
    {
      reports,
      enhancements,
      recentErrors: () => [
        { surface: "app", message: "boom" },
        { surface: "app", message: "bang" },
      ],
      buildTitle: (partial) =>
        "[" + (partial.surface || "global") + "] " + (partial.summary || "Untitled"),
      buildBody: (partial) =>
        [
          "KIND " + partial.kind,
          "NARRATIVE " + Object.keys(partial.narrative || {}).join(","),
          "ERRORS " + JSON.stringify(partial.errors === undefined ? "ring" : partial.errors),
          "ENV " + JSON.stringify(partial.environment),
          "BROWSER " + JSON.stringify(partial.browser),
          "BLANKS " + String(partial.blanks),
          "CTX " + JSON.stringify(partial.context),
        ].join("\n"),
      getConfig: () => ({ env: [["COMFYUI_REF", "abcdef"], ["EZ_COMFY_IMAGE", "img"]] }),
      githubIcon: () => null,
      openReport: (partial) => {
        reports.push(partial);
        return true;
      },
      enhanceText: async (input) => {
        enhancements.push(input);
        return {
          ok: true,
          text:
            "## What happened\n\nmuch clearer\n\n## Steps\n\n1. queue\n\n" +
            "a stray paragraph the model added",
        };
      },
    },
    overrides,
  );
}

/**
 * Mount the real panel against the real frontend stub and a fake core.
 * @param {object} core The object published as `window.EzFeedback`.
 * @param {Array<Array<*>>|null} [pairs] Context pairs the chrome pack gives.
 * @returns {Promise<object>} `{el, tab, core}`.
 */
async function mountPanel(core, pairs) {
  Object.defineProperty(globalThis, "document", {
    configurable: true,
    value: {
      createElement: makeElement,
      createTextNode: (text) => ({ nodeType: 3, textContent: text }),
    },
  });
  Object.defineProperty(globalThis, "window", { configurable: true, value: globalThis });
  Object.defineProperty(globalThis, "navigator", {
    configurable: true,
    writable: true,
    value: { clipboard: { writeText: async () => undefined } },
  });
  globalThis.EzFeedback = core;
  globalThis.__ezFeedbackGraphContext = () => (pairs === undefined ? null : pairs);

  const { ext, app } = await loadExtension(PANEL_JS, "ez.feedback.panel");
  const tabs = [];
  app.extensionManager = { registerSidebarTab: (tab) => tabs.push(tab) };
  await ext.setup();
  const tab = tabs[0];
  const el = makeElement("div");
  tab.render(el);
  return { el, tab, core };
}

const STUDIO_PAIRS = [
  ["App", "stills/image-studio.json"],
  ["Workflow", "image-studio"],
  ["Nodes", 9],
];

describe("ez_feedback panel tab", () => {
  test("registers the sidebar tab the frontend asks for", async () => {
    const { tab } = await mountPanel(fakeCore(), STUDIO_PAIRS);
    assert.equal(tab.id, "ez-feedback");
    assert.equal(tab.icon, "pi pi-github");
    assert.equal(tab.title, "Feedback");
    assert.equal(tab.tooltip, "File bugs and feature requests");
    assert.equal(tab.type, "custom");
    assert.equal(typeof tab.render, "function");
  });

  test("a frontend without the sidebar API is not an error", async () => {
    const { ext, app } = await loadExtension(PANEL_JS, "ez.feedback.panel");
    app.extensionManager = {};
    await ext.setup();
  });
});

describe("ez_feedback panel form", () => {
  test("renders the guided bug form and previews the title", async () => {
    const { el } = await mountPanel(fakeCore(), STUDIO_PAIRS);

    const chips = findAll(el, (n) => n.attrs["data-ez-fb-kind"]);
    assert.deepEqual(
      chips.map((chip) => chip.attrs["data-ez-fb-kind"]),
      ["bug", "enhancement"],
    );
    assert.equal(chips[0].attrs["aria-pressed"], "true");

    const areas = findAll(el, (n) => n.tagName === "textarea");
    assert.equal(areas.length, 4);
    assert.ok(areas[0].placeholder.length > 10, "each field carries its guidance");

    const tips = findAll(el, (n) => n.tagName === "li");
    assert.ok(tips.length >= 4);
    assert.ok(every(el).some((n) => n.textContent === "What makes a good report"));

    const boxes = findAll(el, (n) => n.type === "checkbox");
    assert.equal(boxes.length, 2);
    assert.equal(boxes[0].disabled, false, "the ring has entries, so attach is offered");
    assert.ok(
      every(el).some((n) => n.textContent === "Attach recent errors (2)"),
      "the ring count is shown",
    );
    assert.ok(every(el).some((n) => n.textContent === "Attach environment and browser facts"));
    assert.ok(find(el, (n) => n.className === "ez-fb-preview"));

    const title = find(el, (n) => n.className === "ez-fb-panel-title-preview");
    assert.equal(title.textContent, "[app] Untitled", "the core renders the title line");
  });

  test("an empty ring disables the attach-errors box", async () => {
    const { el } = await mountPanel(fakeCore({ recentErrors: () => [] }), STUDIO_PAIRS);
    const box = find(el, (n) => n.type === "checkbox");
    assert.equal(box.disabled, true);
    assert.equal(box.checked, false);
  });

  test("filing sends the filled narrative, unclipped, and honours the boxes", async () => {
    const core = fakeCore();
    const { el } = await mountPanel(core, STUDIO_PAIRS);

    const areas = findAll(el, (n) => n.tagName === "textarea");
    areas[0].value = "KSampler died at step 12";
    areas[0].input();
    areas[1].value = "1. open the App\n2. press Queue";
    areas[1].input();

    const summary = find(el, (n) => n.type === "text");
    summary.value = "KSampler dies on the second pass";
    summary.input();

    const file = find(el, (n) => n.textContent === "File on GitHub");
    file.click();

    assert.equal(core.reports.length, 1);
    const report = core.reports[0];
    assert.equal(report.kind, "bug");
    assert.equal(report.surface, "app");
    assert.equal(report.app, "stills/image-studio.json");
    assert.equal(report.blanks, false, "a filled form files no placeholders");
    assert.equal(report.summary, "KSampler dies on the second pass");
    assert.deepEqual(report.narrative, {
      what_happened: "KSampler died at step 12",
      steps: "1. open the App\n2. press Queue",
    });
    assert.equal(report.errors, undefined, "attach keeps the core's ring buffer");
    assert.deepEqual(report.context, STUDIO_PAIRS);

    const preview = find(el, (n) => n.className === "ez-fb-preview");
    assert.ok(preview.textContent.includes("NARRATIVE what_happened,steps"), preview.textContent);

    // Uncheck both boxes: the environment labels are answered empty, and the
    // browser block is handed an object with nothing in it.
    const boxes = findAll(el, (n) => n.type === "checkbox");
    boxes[1].checked = false;
    boxes[1].change();
    file.click();
    const second = core.reports[1];
    assert.deepEqual(second.environment, [
      ["COMFYUI_REF", ""],
      ["EZ_COMFY_IMAGE", ""],
    ]);
    assert.deepEqual(second.browser, {});

    const enhance = find(el, (n) => n.textContent === "Enhance with LLM");
    assert.equal(enhance.disabled, false);
  });

  test("enhance replaces only the fields the model answered", async () => {
    const core = fakeCore();
    const { el } = await mountPanel(core, STUDIO_PAIRS);

    const areas = findAll(el, (n) => n.tagName === "textarea");
    areas[0].value = "rough notes";
    areas[0].input();
    areas[2].value = "keep me";
    areas[2].input();

    find(el, (n) => n.textContent === "Enhance with LLM").click();
    await new Promise((resolve) => setTimeout(resolve, 0));

    assert.equal(core.enhancements.length, 1);
    assert.equal(core.enhancements[0].kind, "bug");
    assert.ok(core.enhancements[0].text.includes("## What happened"));
    assert.equal(areas[0].value, "much clearer");
    assert.equal(areas[1].value, "1. queue\n\na stray paragraph the model added");
    assert.equal(areas[2].value, "keep me", "an unanswered field keeps the operator's words");
    const status = find(el, (n) => n.attrs.role === "status");
    assert.equal(status.textContent, "Enhanced text applied.");
  });

  test("a failed enhance keeps the text and says why", async () => {
    const core = fakeCore({ enhanceText: async () => ({ ok: false, error: "llm unavailable" }) });
    const { el } = await mountPanel(core, STUDIO_PAIRS);
    const areas = findAll(el, (n) => n.tagName === "textarea");
    areas[0].value = "rough notes";
    areas[0].input();
    find(el, (n) => n.textContent === "Enhance with LLM").click();
    await new Promise((resolve) => setTimeout(resolve, 0));
    assert.equal(areas[0].value, "rough notes");
    const status = find(el, (n) => n.attrs.role === "status");
    assert.equal(status.textContent, "Enhance unavailable: llm unavailable");
  });

  test("flipping the kind keeps both drafts and re-guides the fields", async () => {
    const core = fakeCore();
    const { el } = await mountPanel(core, STUDIO_PAIRS);

    const bugArea = find(el, (n) => n.tagName === "textarea");
    bugArea.value = "the bug words";
    bugArea.input();

    const chips = findAll(el, (n) => n.attrs["data-ez-fb-kind"]);
    chips[1].click();
    const enhAreas = findAll(el, (n) => n.tagName === "textarea");
    assert.ok(enhAreas[0].placeholder.includes("hard or impossible"), "enhancement guidance");
    enhAreas[0].value = "the request words";
    enhAreas[0].input();

    const file = find(el, (n) => n.textContent === "File on GitHub");
    file.click();
    assert.equal(core.reports[0].kind, "enhancement");
    assert.deepEqual(core.reports[0].narrative, { problem: "the request words" });

    chips[0].click();
    file.click();
    assert.equal(core.reports[1].kind, "bug");
    assert.deepEqual(core.reports[1].narrative, { what_happened: "the bug words" });
  });

  test("a plain workflow files against the global surface", async () => {
    const core = fakeCore();
    const { el } = await mountPanel(core, [["Nodes", 3]]);
    find(el, (n) => n.textContent === "File on GitHub").click();
    assert.equal(core.reports[0].surface, "global");
    assert.equal(core.reports[0].app, "");
    const title = find(el, (n) => n.className === "ez-fb-panel-title-preview");
    assert.equal(title.textContent, "[global] Untitled");
  });

  test("with the core absent the tab still renders and says so", async () => {
    const { el } = await mountPanel(null, STUDIO_PAIRS);
    assert.ok(find(el, (n) => n.tagName === "textarea"));
    find(el, (n) => n.textContent === "File on GitHub").click();
    const status = find(el, (n) => n.attrs.role === "status");
    assert.equal(status.textContent, "Feedback core not loaded yet.");
  });
});

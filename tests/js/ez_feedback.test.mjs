/**
 * @file Client contract for the ez_feedback core, run under `node --test`.
 *
 * Four operator-visible bugs live here. Every one of them filed a report that
 * said less than the operator had typed.
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
 * The URL ladder is the fourth. Past MAX_HREF it dropped `## Recent errors`
 * ahead of `## Environment`, deleted sections without saying so, cut the tail
 * mid-line or mid-code-fence, and promised a clipboard copy that does not exist
 * on the `http://<LAN address>:8188` origin this studio is normally opened on.
 * The body GitHub receives is now what the ladder decided, named in the body
 * itself, and the complete markdown is one paste away on every path.
 *
 * The core is imported as the real module: it sets no globals and guards every
 * DOM touch, so this file needs no jsdom and no npm dependency.
 */

import assert from "node:assert/strict";
import path from "node:path";
import { describe, test } from "node:test";

import {
  ERROR_TEXT_FIT,
  MAX_ERROR_TEXT,
  MAX_HREF,
  buildBody,
  buildTitle,
  enhanceText,
  fileDirect,
  githubIcon,
  issueHrefFor,
  openHandoff,
  openReport,
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
 * Only the members the panel and the dialog actually touch exist, so nothing can
 * lean on a browser feature this file has not modelled: children (with the
 * parent link `remove()` needs), attributes (with the `data-*` to dataset mapping
 * the kind toggle reads), listeners, the input fields, and selection.
 * @param {string} tag Element name, for failure messages only.
 * @returns {object} The fake element.
 */
function makeElement(tag) {
  const el = {
    tagName: tag,
    children: [],
    parent: null,
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
      nodes.forEach((node) => {
        if (node) {
          node.parent = el;
        }
      });
      el.children.push(...nodes);
    },
    appendChild(node) {
      if (node) {
        node.parent = el;
      }
      el.children.push(node);
      return node;
    },
    replaceChildren(...nodes) {
      el.children = [...nodes];
    },
    remove() {
      if (el.parent) {
        el.parent.children = el.parent.children.filter((node) => node !== el);
        el.parent = null;
      }
    },
    select() {
      el.selected = true;
    },
    focus() {
      el.focused = true;
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
  ["App", "photos/image-studio.json"],
  ["Workflow", "image-studio"],
  ["Nodes", 9],
];

/** The marker `fit` appends when it cut the tail; mirrors the core's constant. */
const CUT_NOTE = "\n\n[report trimmed to fit the GitHub URL limit]";

/**
 * Body text the operator would be offered, decoded back out of the href.
 * @param {{href: string}} result Result from `issueHrefFor`.
 * @returns {string} The body GitHub would be prefilled with.
 */
function bodyOf(result) {
  return new URL(result.href).searchParams.get("body") || "";
}

/** The body with the omission note cut off, so a named heading reads as kept. */
function keptOf(result) {
  return bodyOf(result).split("\n\n[left out of this URL:")[0];
}

/** True when `heading` is still a section of the body the URL carries. */
function keeps(result, heading) {
  return new RegExp("^" + heading + "$", "m").test(keptOf(result));
}

/** The headings the body admits it left out, or "" when it left out nothing. */
function leftOut(result) {
  const note = bodyOf(result).split("\n\n[left out of this URL:")[1];
  return note ? note.split("]")[0] : "";
}

describe("ez_feedback core URL budget", () => {
  const BUG = { kind: "bug", surface: "app", summary: "KSampler died" };

  test("five long tracebacks are clipped to fit, never dropped whole", () => {
    const errors = Array.from({ length: 5 }, (_x, i) => ({
      ts: "2026-11-11T0" + i + ":00:00Z",
      surface: "app",
      message: "m".repeat(MAX_ERROR_TEXT),
    }));

    const result = issueHrefFor({ ...BUG, errors });

    assert.ok(result.href.length <= MAX_HREF, `href ${result.href.length} exceeds ${MAX_HREF}`);
    assert.equal(result.trimmed, false, "nothing had to be left out, only clipped");
    assert.ok(keeps(result, "## Recent errors"), "the block that names the failing op survives");
    assert.ok(
      !keptOf(result).includes("m".repeat(ERROR_TEXT_FIT + 1)),
      "each entry came in at the tighter tier instead of the full 2000",
    );
  });

  test("the ladder gives up machine trivia first and says what it left out", () => {
    const huge = "a".repeat(2500);
    const result = issueHrefFor({
      ...BUG,
      narrative: {
        what_happened: huge,
        steps: huge,
        expected: "it should finish",
        actual: "it died",
      },
      context: [["App", "photos/image-studio.json"]],
      environment: [["GPU", "RTX 4090"], ["VRAM", "24 GiB"], ["Torch", "2.6.0"]],
      errors: [{ ts: "t", surface: "app", message: "boom", detail: "cuda oom" }],
      browser: {
        viewport: "1920x1080",
        dpr: "2",
        lang: "en-US",
        online: "true",
        ua: "Mozilla/5.0 (X11; Linux x86_64)",
      },
    });

    assert.ok(result.href.length <= MAX_HREF, `href ${result.href.length} exceeds ${MAX_HREF}`);
    assert.equal(result.trimmed, true, "a shortened handoff is never silent");
    assert.ok(keeps(result, "## Recent errors"), "the traceback outranks the viewport line");
    assert.ok(keeps(result, "## Context"), "the operator's own pairs outrank it too");
    assert.ok(!keeps(result, "## Browser"), "the trivia went first");
    assert.match(leftOut(result), /## Browser/, "and the filed issue admits it");
  });

  test("a section too small to pay for its own omission note is kept", () => {
    // This `## Browser` is a third the size of the line that would announce its
    // absence: dropping it would shorten the URL by less than the note costs.
    const result = issueHrefFor({
      ...BUG,
      narrative: { what_happened: "the sampler stopped", steps: "1. queue" },
      environment: Array.from({ length: 30 }, (_x, i) => ["Layer " + i, "v".repeat(300)]),
      browser: { viewport: "1920x1080" },
    });

    assert.ok(result.href.length <= MAX_HREF, `href ${result.href.length} exceeds ${MAX_HREF}`);
    assert.ok(keeps(result, "## Browser"), "kept: the note cost more than the section");
    assert.ok(!keeps(result, "## Environment"), "the fat block is the one that pays");
    assert.match(leftOut(result), /## Environment/);
  });

  test("the tail cut lands on a whole line, not mid-bullet", () => {
    const typed = [
      "## What happened",
      "",
      "the disk wizard divided by zero",
      "",
      "Traceback (most recent call last):",
      "  File \"disk_wizard.py\", line 1, in <module>",
      "ZeroDivisionError: division by zero",
      "- step " + "q".repeat(6000),
    ].join("\n");

    const result = issueHrefFor({ ...BUG }, typed);
    const body = bodyOf(result);

    assert.ok(result.href.length <= MAX_HREF, `href ${result.href.length} exceeds ${MAX_HREF}`);
    assert.equal(result.trimmed, true);
    assert.ok(body.endsWith(CUT_NOTE), "the cut is stated where GitHub will show it");
    const keptText = body.slice(0, body.length - CUT_NOTE.length);
    assert.equal(typed.slice(0, keptText.length), keptText, "what survived is a prefix");
    assert.equal(typed.charAt(keptText.length), "\n", "and it stopped at a line boundary");
    assert.ok(keptText.includes("ZeroDivisionError"), "the head of the traceback made the cut");
  });

  test("a tail that would leave a code fence open goes whole", () => {
    // An unterminated fence is the one cut that eats the rest of the issue once
    // GitHub renders it, so the block is dropped rather than split.
    const typed = [
      "## What happened",
      "",
      "the disk wizard divided by zero",
      "",
      "```",
      "Traceback (most recent call last):",
      "q".repeat(6000),
      "```",
    ].join("\n");

    const result = issueHrefFor({ ...BUG }, typed);
    const body = bodyOf(result);
    const keptText = body.slice(0, body.length - CUT_NOTE.length);

    assert.ok(result.href.length <= MAX_HREF, `href ${result.href.length} exceeds ${MAX_HREF}`);
    assert.equal((keptText.match(/^```/gm) || []).length % 2, 0, "no fence left open");
    assert.equal(typed.slice(0, keptText.length), keptText, "what survived is still a prefix");
    assert.ok(keptText.includes("the disk wizard divided by zero"), "the prose before it stayed");
  });
});

/**
 * Install the browser surface the real dialog needs.
 *
 * The dialog is mounted against the real core, not `fakeCore`: when the URL
 * could not carry the report, the copy the status line promises is the thing
 * the operator actually gets, and that promise has to be tested where it is made.
 * @param {object} [opts] `{open, clipboard, execCommand}` - what the browser
 *   offers. `clipboard: false` models an insecure origin, where
 *   `navigator.clipboard` does not exist at all; `open` answers `window.open`.
 * @returns {object} `{doc, copies, restore}`; `copies` is what reached the clipboard.
 */
function mountDialog(opts = {}) {
  const options = opts || {};
  const copies = [];
  const doc = {
    head: makeElement("head"),
    body: makeElement("body"),
    createElement: makeElement,
    createTextNode: (text) => ({ nodeType: 3, textContent: text }),
    createElementNS: (_ns, tag) => makeElement(tag),
    addEventListener() {},
    removeEventListener() {},
    getElementById(id) {
      const all = [doc.head, doc.body].concat(every(doc.head), every(doc.body));
      return all.find((node) => node && node.id === id) || null;
    },
  };
  if (typeof options.execCommand === "function") {
    doc.execCommand = (name) => {
      const picked = every(doc.body).filter((node) => node.selected).pop();
      copies.push(picked ? picked.value : "");
      return options.execCommand(name);
    };
  }

  const keys = ["document", "window", "navigator", "open", "fetch"];
  const saved = keys.map((key) => [key, Object.getOwnPropertyDescriptor(globalThis, key)]);
  Object.defineProperty(globalThis, "document", { configurable: true, writable: true, value: doc });
  Object.defineProperty(globalThis, "window", { configurable: true, writable: true, value: globalThis });
  Object.defineProperty(globalThis, "navigator", {
    configurable: true,
    writable: true,
    value: options.clipboard === false
      ? { userAgent: "node" }
      : { clipboard: { writeText: async (text) => { copies.push(text); } } },
  });
  globalThis.open = typeof options.open === "function" ? options.open : () => ({});
  globalThis.fetch = async () => ({ ok: false, status: 404, json: async () => ({}) });

  return {
    doc,
    copies,
    restore() {
      saved.forEach(([key, descriptor]) => {
        if (descriptor) {
          Object.defineProperty(globalThis, key, descriptor);
        } else {
          delete globalThis[key];
        }
      });
    },
  };
}

/** Let the clipboard promise chains the dialog started settle. */
function flush() {
  return new Promise((resolve) => {
    setTimeout(resolve, 0);
  });
}

/** What the dialog's status line currently says. */
function statusText(doc) {
  const node = find(doc.body, (n) => n.className === "ez-fb-status");
  return node ? node.textContent : "";
}

describe("ez_feedback core dialog clipboard", () => {
  const BUG = { kind: "bug", surface: "app", summary: "KSampler died" };

  test("a handoff the URL had to shorten copies the whole markdown", async () => {
    const { doc, copies, restore } = mountDialog();
    try {
      assert.equal(openReport(BUG), true);
      const area = find(doc.body, (n) => n.tagName === "textarea");
      area.value = "q".repeat(9000);
      find(doc.body, (n) => n.className.includes("ez-fb-btn-primary")).click();
      await flush();

      assert.equal(copies.length, 1, "the copy the status line promises actually happened");
      assert.equal(copies[0], area.value, "the whole body, not the one the URL carried");
      assert.equal(
        statusText(doc),
        "Full markdown copied - paste it on GitHub if the prefill was shortened.",
      );
    } finally {
      restore();
    }
  });

  test("a blocked popup no longer loses the report", async () => {
    const { doc, copies, restore } = mountDialog({ open: () => null });
    try {
      openReport(BUG);
      const area = find(doc.body, (n) => n.tagName === "textarea");
      area.value = "typed words the popup would have eaten";
      find(doc.body, (n) => n.className.includes("ez-fb-btn-primary")).click();
      await flush();

      assert.deepEqual(copies, [area.value]);
      assert.match(statusText(doc), /^Popup blocked - full markdown copied\./);
    } finally {
      restore();
    }
  });

  test("an insecure origin copies through the selection fallback", async () => {
    const { doc, copies, restore } = mountDialog({ clipboard: false, execCommand: () => true });
    try {
      openReport(BUG);
      const area = find(doc.body, (n) => n.tagName === "textarea");
      area.value = "words copied over http://192.168.1.20:8188";
      find(doc.body, (n) => n.textContent === "Copy markdown").click();
      await flush();

      assert.deepEqual(copies, [area.value], "execCommand copied the selected text");
      assert.equal(statusText(doc), "Markdown copied.");
    } finally {
      restore();
    }
  });

  test("with no clipboard at all the dialog says so and selects the text", async () => {
    const { doc, copies, restore } = mountDialog({ clipboard: false });
    try {
      openReport(BUG);
      const area = find(doc.body, (n) => n.tagName === "textarea");
      area.value = "unsendable";
      find(doc.body, (n) => n.textContent === "Copy markdown").click();
      await flush();

      assert.equal(copies.length, 0);
      assert.equal(area.selected, true, "selected for a manual Ctrl+C");
      assert.equal(statusText(doc), "Copy blocked; the body is selected.");
    } finally {
      restore();
    }
  });

  test("openHandoff copies the report the URL could not carry", async () => {
    let href = "";
    const { copies, restore } = mountDialog({
      open: (url) => {
        href = url;
        return {};
      },
    });
    try {
      const opened = openHandoff({
        ...BUG,
        narrative: { what_happened: "a".repeat(3400), steps: "b".repeat(3400) },
      });
      await flush();

      assert.equal(opened, true);
      assert.ok(href.length <= MAX_HREF, `href ${href.length} exceeds ${MAX_HREF}`);
      const tail = "b".repeat(3400);
      assert.ok(!bodyOf({ href }).includes(tail), "the URL had to leave the tail behind");
      assert.equal(copies.length, 1);
      assert.ok(copies[0].includes(tail), "the clipboard got the whole report");
    } finally {
      restore();
    }
  });
});

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
    assert.equal(report.app, "photos/image-studio.json");
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

/**
 * Feedback sidebar: a guided bug / feature form that files through the core.
 *
 * Hand-rolled DOM only, the way the Outputs sidebar is: no frontend UI module,
 * no component library, nothing that can block a queue. Every class is
 * `.ez-fb-panel*` (plus the shared `.ez-fb-preview` block) and the stylesheet
 * is the one `ez_feedback_core.js` already injects, so this file adds no
 * second style tag and no new stacking level.
 *
 * The core is reached lazily through `window.EzFeedback` at click and render
 * time, so extension load order cannot break the tab: with the core absent the
 * panel still renders and says so. The graph description comes from
 * `window.__ezFeedbackGraphContext`, which the chrome pack publishes in setup.
 */
import { app } from "../../scripts/app.js";

const TAB_ID = "ez-feedback";
const TIPS_TITLE = "What makes a good report";

const NARRATIVE_KEYS = {
  bug: ["what_happened", "steps", "expected", "actual"],
  enhancement: ["problem", "solution", "alternatives", "unlocks"],
};
const NARRATIVE_HEADINGS = {
  bug: ["## What happened", "## Steps", "## Expected", "## Actual"],
  enhancement: ["## Problem", "## Proposed solution", "## Alternatives", "## What it unlocks"],
};
/** Per-kind prompt shown as the textarea placeholder: guidance lives here. */
const NARRATIVE_GUIDANCE = {
  bug: {
    what_happened: "What happened, in one or two sentences. Include the exact error text.",
    steps: "1. Open the App\n2. Set these widgets\n3. Press Queue",
    expected: "What you expected to happen instead.",
    actual: "What actually happened, including any red node or console line.",
  },
  enhancement: {
    problem: "What is hard or impossible today, and how often you hit it.",
    solution: "What you would like the App, panel, or workflow to do.",
    alternatives: "Workarounds you already tried, and why they fall short.",
    unlocks: "What this makes possible afterwards.",
  },
};
const TIPS = {
  bug: [
    "Paste the exact error text, not a paraphrase.",
    "Say which App and workflow was open, and what the widgets held.",
    "Give the shortest steps that reproduce it every time.",
    "Separate what you expected from what actually happened.",
    "Say what you already tried, so the fix is not guessed twice.",
  ],
  enhancement: [
    "Lead with the problem you hit, not the button you want.",
    "Say how often it costs you time or a wasted run.",
    "Describe the behaviour you expect, in one sentence.",
    "List the workarounds you tried and where they broke.",
    "One request per report keeps the labels honest.",
  ],
};

/**
 * The shared machinery, resolved lazily so load order cannot break the tab.
 * @returns {object|null} `window.EzFeedback`, or null before it loads.
 */
function core() {
  return (typeof window !== "undefined" && window.EzFeedback) || null;
}

/**
 * Graph description pairs from the chrome pack, best effort.
 * @returns {Array<Array<string>>} Context pairs, or `[]`.
 */
function graphContext() {
  const provider = typeof window !== "undefined" ? window.__ezFeedbackGraphContext : null;
  if (typeof provider !== "function") {
    return [];
  }
  try {
    const pairs = provider();
    return Array.isArray(pairs) ? pairs : [];
  } catch (_err) {
    return [];
  }
}

/**
 * The open App's `lab_rel`, read back out of the context pairs.
 * @param {Array<Array<string>>} pairs Context pairs from the chrome pack.
 * @returns {string} `lab_rel`, or `""` for a plain workflow.
 */
function appRelFrom(pairs) {
  const found = pairs.filter(
    (pair) => Array.isArray(pair) && String(pair[0]).trim() === "App",
  )[0];
  return found ? String(found[1] || "").trim() : "";
}

/**
 * Create a button, optionally led by the core's GitHub mark.
 * @param {string} label Button text.
 * @param {string} className `ez-fb-panel*` class list.
 * @param {object} [opts] `{icon: true}` prepends the core's GitHub mark.
 * @returns {HTMLButtonElement} The button.
 */
function makeButton(label, className, opts) {
  const options = opts && typeof opts === "object" ? opts : {};
  const node = document.createElement("button");
  node.type = "button";
  node.className = className;
  if (options.icon) {
    const fb = core();
    const icon = fb && typeof fb.githubIcon === "function" ? fb.githubIcon() : null;
    if (icon) {
      node.appendChild(icon);
      node.appendChild(document.createTextNode(" "));
    }
  }
  node.appendChild(document.createTextNode(label));
  return node;
}

/**
 * One labelled block: heading, then the nodes.
 * @param {string} label Heading text.
 * @param {string} className `ez-fb-panel*` class list for the block.
 * @returns {object} `{block, heading}` elements to append children to.
 */
function makeBlock(label, className) {
  const block = document.createElement("div");
  block.className = className;
  const heading = document.createElement("div");
  heading.className = "ez-fb-panel-heading";
  heading.textContent = label;
  block.appendChild(heading);
  return { block, heading };
}

/**
 * Narrative as the operator filled it, trimmed to the kind's non-empty keys.
 * @param {object} values Field elements by narrative key.
 * @param {string[]} keys The kind's narrative keys.
 * @returns {object|null} `{key: text}`, or null when every field is blank.
 */
function filledNarrative(values, keys) {
  const out = {};
  let any = false;
  keys.forEach((key) => {
    const text = String((values[key] && values[key].value) || "");
    if (text.trim()) {
      out[key] = text;
      any = true;
    }
  });
  return any ? out : null;
}

/**
 * Text sent to the LLM: the filled narrative, marked up by its own headings.
 * @param {object} narrative Filled narrative, or null.
 * @param {string[]} keys The kind's narrative keys.
 * @param {string[]} headings The kind's headings, same order as keys.
 * @returns {string} Markdown text, empty when there is nothing filled.
 */
function narrativeText(narrative, keys, headings) {
  if (!narrative) {
    return "";
  }
  const parts = [];
  keys.forEach((key, index) => {
    if (narrative[key]) {
      parts.push(headings[index] + "\n" + narrative[key]);
    }
  });
  return parts.join("\n\n");
}

/**
 * Read an LLM answer back into the fields, keyed by its `## ` headings.
 * @param {object} values Field elements by narrative key.
 * @param {string[]} keys The kind's narrative keys.
 * @param {string[]} headings The kind's headings, same order as keys.
 * @param {string} text Enhanced markdown.
 * @returns {boolean} True when at least one field changed.
 */
function applyNarrativeText(values, keys, headings, text) {
  const buckets = {};
  let current = keys[0];
  String(text || "").split("\n").forEach((line) => {
    const index = headings.indexOf(line.trim());
    if (index >= 0) {
      current = keys[index];
      return;
    }
    (buckets[current] = buckets[current] || []).push(line);
  });
  let applied = false;
  keys.forEach((key) => {
    const value = (buckets[key] || []).join("\n").trim();
    if (value) {
      values[key].value = value;
      applied = true;
    }
  });
  return applied;
}

/**
 * Environment pairs for a payload.
 *
 * Unchecking the box has to beat `reportPayload`, which fills any label the
 * caller leaves out from the server config, so every config label is handed
 * back as an empty pair: seen, and rendered as nothing.
 * @param {object|null} fb The core.
 * @param {boolean} attach Whether the operator asked for environment facts.
 * @returns {Array<Array<string>>} Pairs for the payload.
 */
function environmentPairs(fb, attach) {
  if (attach) {
    return [];
  }
  const cfg = fb && typeof fb.getConfig === "function" ? fb.getConfig() : {};
  const env = (cfg && cfg.env) || {};
  const pairs = Array.isArray(env) ? env : Object.keys(env).map((key) => [key, env[key]]);
  return pairs
    .filter((pair) => Array.isArray(pair) && pair.length)
    .map((pair) => [String(pair[0]), ""]);
}

/**
 * A row the core's error block skips, used to say "attach no errors".
 *
 * `reportPayload` refills an empty `errors` array from the ring buffer, so the
 * panel passes one message-less row: `errorLines` drops it and the block never
 * appears.
 * @returns {Array<object>} Payload `errors` value meaning none.
 */
function noErrors() {
  return [{ surface: TAB_ID, message: "", detail: "" }];
}

/**
 * Render the Feedback tab into the sidebar slot.
 * @param {HTMLElement} el The sidebar container the frontend owns.
 * @returns {void}
 */
function mountPanel(el) {
  el.replaceChildren();
  el.classList.add("ez-fb-panel");
  el.tabIndex = 0;

  /** @type {"bug"|"enhancement"} */
  let kind = "bug";
  /** @type {object} Field elements for the current kind, by narrative key. */
  let values = {};
  /** Entered text is kept per kind so flipping the toggle loses nothing. */
  const drafts = { bug: {}, enhancement: {} };
  let busy = false;

  const context = graphContext();
  const rel = appRelFrom(context);
  const surface = rel ? "app" : "global";

  const intro = document.createElement("p");
  intro.className = "ez-fb-panel-intro";
  intro.textContent =
    "Reports go to the ez-comfy-stack repository. Nothing leaves this page " +
    "until you press File on GitHub.";

  const kindRow = document.createElement("div");
  kindRow.className = "ez-fb-panel-kinds";
  kindRow.setAttribute("role", "group");
  kindRow.setAttribute("aria-label", "Report kind");
  const kinds = [
    ["bug", "Bug report"],
    ["enhancement", "Feature request"],
  ];
  const kindButtons = kinds.map(([id, label]) => {
    const button = makeButton(label, "ez-fb-panel-chip");
    button.setAttribute("data-ez-fb-kind", id);
    button.setAttribute("aria-pressed", id === kind ? "true" : "false");
    button.addEventListener("click", () => {
      if (kind === id) {
        return;
      }
      captureDraft();
      kind = id;
      kindButtons.forEach((other) => {
        other.setAttribute("aria-pressed", other.dataset.ezFbKind === kind ? "true" : "false");
      });
      renderFields();
      refresh();
    });
    kindRow.appendChild(button);
    return button;
  });

  const summaryBlock = makeBlock("Title", "ez-fb-panel-block");
  const summary = document.createElement("input");
  summary.type = "text";
  summary.className = "ez-fb-panel-input";
  summary.placeholder = "One line: what broke, or what you want";
  summary.setAttribute("aria-label", "Report summary");
  summary.addEventListener("input", refresh);
  summaryBlock.block.appendChild(summary);
  const titlePreview = document.createElement("div");
  titlePreview.className = "ez-fb-panel-title-preview";
  summaryBlock.block.appendChild(titlePreview);

  const fieldsBlock = makeBlock("Tell the story", "ez-fb-panel-block");
  const fields = document.createElement("div");
  fields.className = "ez-fb-panel-fields";
  fieldsBlock.block.appendChild(fields);

  const tipsBlock = makeBlock(TIPS_TITLE, "ez-fb-panel-block");
  const tips = document.createElement("ul");
  tips.className = "ez-fb-panel-tips";
  tipsBlock.block.appendChild(tips);

  const attachBlock = document.createElement("div");
  attachBlock.className = "ez-fb-panel-attach";
  const errorsBox = document.createElement("input");
  errorsBox.type = "checkbox";
  errorsBox.className = "ez-fb-panel-check";
  errorsBox.checked = true;
  const errorsLabel = document.createElement("label");
  errorsLabel.className = "ez-fb-panel-check-row";
  const errorsText = document.createElement("span");
  errorsText.className = "ez-fb-panel-check-text";
  errorsLabel.append(errorsBox, errorsText);
  const envBox = document.createElement("input");
  envBox.type = "checkbox";
  envBox.className = "ez-fb-panel-check";
  envBox.checked = true;
  const envLabel = document.createElement("label");
  envLabel.className = "ez-fb-panel-check-row";
  const envText = document.createElement("span");
  envText.className = "ez-fb-panel-check-text";
  envText.textContent = "Attach environment and browser facts";
  envLabel.append(envBox, envText);
  attachBlock.append(errorsLabel, envLabel);
  errorsBox.addEventListener("change", refresh);
  envBox.addEventListener("change", refresh);

  const previewBlock = makeBlock("Markdown preview", "ez-fb-panel-block");
  const preview = document.createElement("pre");
  preview.className = "ez-fb-preview";
  preview.setAttribute("aria-live", "polite");
  previewBlock.block.appendChild(preview);

  const status = document.createElement("div");
  status.className = "ez-fb-panel-status";
  status.setAttribute("role", "status");

  const footer = document.createElement("div");
  footer.className = "ez-fb-panel-footer";
  const enhanceBtn = makeButton("Enhance with LLM", "ez-fb-panel-btn");
  const copyBtn = makeButton("Copy markdown", "ez-fb-panel-btn");
  const fileBtn = makeButton("File on GitHub", "ez-fb-panel-btn ez-fb-panel-btn-primary", {
    icon: true,
  });
  footer.append(enhanceBtn, copyBtn, fileBtn);

  /**
   * Park the current kind's textarea text in its draft store.
   * @returns {void}
   */
  function captureDraft() {
    NARRATIVE_KEYS[kind].forEach((key) => {
      drafts[kind][key] = String((values[key] && values[key].value) || "");
    });
  }

  /**
   * (Re)build the guided textareas for the current kind.
   * @returns {void}
   */
  function renderFields() {
    values = {};
    fields.replaceChildren();
    NARRATIVE_KEYS[kind].forEach((key, index) => {
      const wrap = document.createElement("div");
      wrap.className = "ez-fb-panel-field";
      const label = document.createElement("label");
      label.className = "ez-fb-panel-field-label";
      label.textContent = NARRATIVE_HEADINGS[kind][index].replace(/^##\s+/, "");
      const area = document.createElement("textarea");
      area.className = "ez-fb-panel-area";
      area.rows = key === "steps" ? 4 : 3;
      area.spellcheck = false;
      area.placeholder = NARRATIVE_GUIDANCE[kind][key];
      area.setAttribute("aria-label", label.textContent);
      area.value = drafts[kind][key] || "";
      area.addEventListener("input", () => {
        drafts[kind][key] = area.value;
        refresh();
      });
      values[key] = area;
      wrap.append(label, area);
      fields.appendChild(wrap);
    });
    tips.replaceChildren();
    TIPS[kind].forEach((tip) => {
      const item = document.createElement("li");
      item.textContent = tip;
      tips.appendChild(item);
    });
  }

  /**
   * The partial report the current form describes.
   * @returns {object} Partial report for the core dialog.
   */
  function reportPartial() {
    const fb = core();
    const narrative = filledNarrative(values, NARRATIVE_KEYS[kind]);
    const attachErrors = errorsBox.checked && !errorsBox.disabled;
    const partial = {
      kind,
      surface,
      app: rel,
      summary: summary.value,
      narrative,
      blanks: false,
      context,
      environment: environmentPairs(fb, envBox.checked),
      browser: envBox.checked ? undefined : {},
      errors: attachErrors ? undefined : noErrors(),
    };
    return partial;
  }

  /**
   * Refresh the title line, the ring count, and the markdown preview.
   * @returns {void}
   */
  function refresh() {
    const fb = core();
    const ring = fb && typeof fb.recentErrors === "function" ? fb.recentErrors() : [];
    errorsText.textContent = ring.length
      ? "Attach recent errors (" + ring.length + ")"
      : "Attach recent errors";
    errorsBox.disabled = ring.length === 0;
    if (errorsBox.disabled) {
      errorsBox.checked = false;
    }
    if (!fb || typeof fb.buildBody !== "function") {
      titlePreview.textContent = "";
      preview.textContent = "Feedback core not loaded yet.";
      return;
    }
    const partial = reportPartial();
    if (typeof fb.buildTitle === "function") {
      titlePreview.textContent = fb.buildTitle(partial);
    }
    preview.textContent = fb.buildBody(partial) || "Fill a field to see the issue body.";
  }

  enhanceBtn.addEventListener("click", () => {
    const fb = core();
    if (busy || !fb || typeof fb.enhanceText !== "function") {
      status.textContent = "Feedback core not loaded yet.";
      return;
    }
    const keys = NARRATIVE_KEYS[kind];
    const headings = NARRATIVE_HEADINGS[kind];
    const text = narrativeText(filledNarrative(values, keys), keys, headings);
    if (!text) {
      status.textContent = "Fill at least one field to enhance.";
      return;
    }
    busy = true;
    enhanceBtn.disabled = true;
    status.textContent = "Enhancing with the local model...";
    const done = (result) => {
      busy = false;
      enhanceBtn.disabled = false;
      if (!result || result.ok !== true || typeof result.text !== "string") {
        status.textContent = "Enhance unavailable: " + ((result && result.error) || "no answer");
        return;
      }
      const changed = applyNarrativeText(values, keys, headings, result.text);
      captureDraft();
      status.textContent = changed ? "Enhanced text applied." : "The model returned no text.";
      refresh();
    };
    fb.enhanceText({ kind, text }).then(done, () => {
      busy = false;
      enhanceBtn.disabled = false;
      status.textContent = "Enhance unavailable: request failed.";
    });
  });

  copyBtn.addEventListener("click", () => {
    const text = preview.textContent || "";
    const clipper = typeof navigator !== "undefined" ? navigator.clipboard : null;
    const fallback = () => {
      const selection = typeof window !== "undefined" && window.getSelection
        ? window.getSelection()
        : null;
      if (!selection || typeof document.createRange !== "function") {
        return "Copy blocked; select the preview yourself.";
      }
      const range = document.createRange();
      range.selectNodeContents(preview);
      selection.removeAllRanges();
      selection.addRange(range);
      return "Copy blocked; the preview is selected.";
    };
    if (!clipper || typeof clipper.writeText !== "function") {
      status.textContent = fallback();
      return;
    }
    clipper.writeText(text).then(
      () => {
        status.textContent = "Markdown copied.";
      },
      () => {
        status.textContent = fallback();
      }
    );
  });

  fileBtn.addEventListener("click", () => {
    const fb = core();
    if (!fb || typeof fb.openReport !== "function") {
      status.textContent = "Feedback core not loaded yet.";
      return;
    }
    const opened = fb.openReport(reportPartial());
    status.textContent = opened
      ? "Report dialog opened - edit the body, then file."
      : "Could not open the report dialog.";
  });

  renderFields();
  el.append(
    intro,
    kindRow,
    summaryBlock.block,
    fieldsBlock.block,
    tipsBlock.block,
    attachBlock,
    previewBlock.block,
    status,
    footer,
  );
  refresh();
}

app.registerExtension({
  name: "ez.feedback.panel",
  /**
   * Register the Feedback sidebar tab when the frontend supports it.
   * @returns {Promise<void>}
   */
  async setup() {
    const mgr = app.extensionManager;
    if (!mgr || typeof mgr.registerSidebarTab !== "function") {
      return;
    }
    mgr.registerSidebarTab({
      id: TAB_ID,
      icon: "pi pi-github",
      title: "Feedback",
      tooltip: "File bugs and feature requests",
      type: "custom",
      render: mountPanel,
    });
  },
});

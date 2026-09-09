/**
 * Your Spark variables + ezcmd flag builders (localStorage).
 * Copy uses data-clipboard-text so Material Clipboard.js gets substituted text.
 * Token split matches docs/commands.py split_var_template — keep in sync.
 */
(function () {
  "use strict";

  var VARS_KEY = "ez-comfy.cmdvars";
  var FLAGS_PREFIX = "ez-comfy.cmdflags.";
  var PANEL_KEY = "ez-comfy.cmdpanel";
  // Keep in sync with docs/commands.py _VAR_TOKEN_RE.
  var VAR_TOKEN = /\$\{([A-Z][A-Z0-9_]*)(?::-([^}]*))?\}/g;

  var currentData = null;
  var currentValues = {};
  var currentDefaults = {};
  var chipDelegated = false;

  /**
   * Run fn on Material document$ or DOM ready (same pattern as glossary.js).
   * @param {function(): void} fn
   */
  function boot(fn) {
    if (typeof document$ !== "undefined" && document$.subscribe) {
      document$.subscribe(fn);
    } else if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  /**
   * Parse the site-wide command-builder JSON blob.
   * @returns {object|null}
   */
  function payload() {
    var el = document.getElementById("ez-cmd-data");
    if (!el) {
      return null;
    }
    try {
      return JSON.parse(el.textContent);
    } catch (err) {
      return null;
    }
  }

  /**
   * @param {object} data
   * @returns {object}
   */
  function defaultVars(data) {
    var out = {};
    (data.variables || []).forEach(function (row) {
      out[row.id] = row.default;
    });
    return out;
  }

  /**
   * @param {object} data
   * @returns {object}
   */
  function loadVars(data) {
    var merged = defaultVars(data);
    try {
      var raw = localStorage.getItem(VARS_KEY);
      if (!raw) {
        return merged;
      }
      var stored = JSON.parse(raw);
      Object.keys(merged).forEach(function (id) {
        if (typeof stored[id] === "string" && stored[id] !== "") {
          merged[id] = stored[id];
        }
      });
    } catch (err) {
      return defaultVars(data);
    }
    return merged;
  }

  /**
   * @param {object} values
   */
  function saveVars(values) {
    try {
      localStorage.setItem(VARS_KEY, JSON.stringify(values));
    } catch (err) {
      /* private mode */
    }
  }

  /**
   * @param {string} cmdId
   * @returns {object}
   */
  function loadFlags(cmdId) {
    try {
      var raw = localStorage.getItem(FLAGS_PREFIX + cmdId);
      if (!raw) {
        return {};
      }
      var parsed = JSON.parse(raw);
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch (err) {
      return {};
    }
  }

  /**
   * @param {string} cmdId
   * @param {object} flags
   */
  function saveFlags(cmdId, flags) {
    try {
      localStorage.setItem(FLAGS_PREFIX + cmdId, JSON.stringify(flags));
    } catch (err) {
      /* private mode */
    }
  }

  /**
   * Spec: docs/commands.py split_var_template (not recursive).
   * @param {string} template
   * @param {object} values
   * @returns {Array<{text: string, id: string|null}>}
   */
  function splitVarTemplate(template, values) {
    var parts = [];
    var last = 0;
    VAR_TOKEN.lastIndex = 0;
    var match;
    while ((match = VAR_TOKEN.exec(template)) !== null) {
      var name = match[1];
      if (!Object.prototype.hasOwnProperty.call(values, name)) {
        continue;
      }
      if (match.index > last) {
        parts.push({ text: template.slice(last, match.index), id: null });
      }
      parts.push({ text: values[name], id: name });
      last = match.index + match[0].length;
    }
    var tail = template.slice(last);
    if (tail) {
      parts.push({ text: tail, id: null });
    } else if (!parts.length) {
      parts.push({ text: template, id: null });
    }
    return parts;
  }

  /**
   * Spec: docs/commands.py substitute_vars (not recursive).
   * @param {string} template
   * @param {object} values
   * @returns {string}
   */
  function substituteVars(template, values) {
    var parts = splitVarTemplate(template, values);
    var out = "";
    var i;
    for (i = 0; i < parts.length; i += 1) {
      out += parts[i].text;
    }
    return out;
  }

  /**
   * @param {string} template
   * @param {object} values
   * @returns {boolean}
   */
  function templateHasVars(template, values) {
    var parts = splitVarTemplate(template, values);
    var i;
    for (i = 0; i < parts.length; i += 1) {
      if (parts[i].id) {
        return true;
      }
    }
    return false;
  }

  /**
   * @param {string} token
   * @returns {string}
   */
  function shellQuote(token) {
    if (token === "") {
      return "''";
    }
    if (/[^\w./:=@+-]/.test(token)) {
      return "'" + token.replace(/'/g, "'\\''") + "'";
    }
    return token;
  }

  /**
   * @param {object} flag
   * @param {object} flags
   * @param {object} values
   * @returns {*}
   */
  function flagValue(flag, flags, values) {
    if (Object.prototype.hasOwnProperty.call(flags, flag.name)) {
      return flags[flag.name];
    }
    if (flag.bind_var && Object.prototype.hasOwnProperty.call(values, flag.bind_var)) {
      return values[flag.bind_var];
    }
    return flag.default;
  }

  /**
   * Spec: docs/commands.py render_command.
   * @param {object} recipe
   * @param {object} flags
   * @param {object} values
   * @returns {string}
   */
  function renderCommand(recipe, flags, values) {
    var parts = (recipe.argv || []).map(function (p) {
      return substituteVars(String(p), values);
    });
    (recipe.flags || []).forEach(function (flag) {
      var current = flagValue(flag, flags, values);
      if (flag.kind === "bool") {
        if (current === true) {
          parts.push("--" + flag.name);
        }
        return;
      }
      if (current === null || current === false || current === "" || typeof current === "undefined") {
        if (flag.required) {
          current = flag.default;
        } else {
          return;
        }
      }
      var token = String(current);
      if (!token) {
        return;
      }
      parts.push("--" + flag.name);
      parts.push(token);
    });
    return parts.map(shellQuote).join(" ");
  }

  /**
   * @param {object} data
   * @param {string} cmdId
   * @returns {object|null}
   */
  function commandById(data, cmdId) {
    var list = data.commands || [];
    for (var i = 0; i < list.length; i += 1) {
      if (list[i].id === cmdId) {
        return list[i];
      }
    }
    return null;
  }

  /**
   * @param {Element} code
   * @param {string} text
   */
  function setClipboardText(code, text) {
    var root = code.closest(".highlight") || code.closest("pre") || code.parentElement;
    if (!root) {
      return;
    }
    var buttons = root.querySelectorAll(".md-clipboard");
    for (var i = 0; i < buttons.length; i += 1) {
      buttons[i].setAttribute("data-clipboard-text", text);
    }
  }

  /**
   * @param {Element} code
   * @returns {boolean}
   */
  function shouldSkipCode(code) {
    if (code.closest(".ez-cmd-builder")) {
      return true;
    }
    if (code.closest(".ez-spark-panel")) {
      return true;
    }
    if (code.closest(".ez-glossary-dialog")) {
      return true;
    }
    if (code.closest(".mermaid")) {
      return true;
    }
    return false;
  }

  /**
   * @param {string} name
   * @param {string} value
   * @returns {HTMLElement}
   */
  function makeVarChip(name, value) {
    var span = document.createElement("span");
    span.className = "ez-var";
    span.setAttribute("data-ez-var", name);
    span.setAttribute("contenteditable", "true");
    span.setAttribute("spellcheck", "false");
    span.setAttribute("role", "textbox");
    span.setAttribute(
      "aria-label",
      name + ", session variable, click to edit"
    );
    span.title = name + " — session variable, click to edit";
    span.textContent = value;
    return span;
  }

  /**
   * @param {Element} code
   * @param {string} template
   * @param {object} values
   */
  function renderTemplateInto(code, template, values) {
    var parts = splitVarTemplate(template, values);
    var frag = document.createDocumentFragment();
    parts.forEach(function (part) {
      if (part.id) {
        frag.appendChild(makeVarChip(part.id, part.text));
      } else if (part.text) {
        frag.appendChild(document.createTextNode(part.text));
      }
    });
    code.replaceChildren(frag);
  }

  /**
   * Bind one existing code node: snapshot template, chips, copy text.
   * @param {Element} code
   * @param {object} values
   */
  function bindCode(code, values) {
    if (shouldSkipCode(code)) {
      return;
    }
    var template = code.getAttribute("data-ez-src");
    if (!template) {
      template = code.textContent || "";
      if (!templateHasVars(template, values)) {
        return;
      }
      code.setAttribute("data-ez-src", template);
      code.setAttribute("data-ez-bound", "1");
    }
    renderTemplateInto(code, template, values);
    setClipboardText(code, substituteVars(template, values));
  }

  /**
   * Auto-bind every article code node that contains session tokens.
   * @param {object} values
   */
  function rebindCodes(values) {
    var article = document.querySelector("article.md-content__inner");
    var root = article || document;
    var nodes = root.querySelectorAll("code");
    var i;
    for (i = 0; i < nodes.length; i += 1) {
      bindCode(nodes[i], values);
    }
  }

  /**
   * Push currentValues to panel inputs, chips, clipboards, and ezcmd.
   * @param {Element|null} exceptEl
   */
  function applyValues(exceptEl) {
    var panel = document.querySelector(".ez-spark-panel");
    var i;
    if (panel) {
      var inputs = panel.querySelectorAll("input[name]");
      for (i = 0; i < inputs.length; i += 1) {
        if (inputs[i] === exceptEl) {
          continue;
        }
        var id = inputs[i].name;
        if (Object.prototype.hasOwnProperty.call(currentValues, id)) {
          inputs[i].value = currentValues[id];
        }
      }
    }
    var chips = document.querySelectorAll("span.ez-var[data-ez-var]");
    for (i = 0; i < chips.length; i += 1) {
      if (chips[i] === exceptEl) {
        continue;
      }
      var vid = chips[i].getAttribute("data-ez-var");
      var want = Object.prototype.hasOwnProperty.call(currentValues, vid)
        ? currentValues[vid]
        : "";
      if (chips[i].textContent !== want) {
        chips[i].textContent = want;
      }
    }
    var bound = document.querySelectorAll("code[data-ez-src]");
    for (i = 0; i < bound.length; i += 1) {
      setClipboardText(
        bound[i],
        substituteVars(bound[i].getAttribute("data-ez-src") || "", currentValues)
      );
    }
    if (currentData) {
      hydrateAll(currentData, currentValues);
    }
  }

  /**
   * @param {EventTarget|null} target
   * @returns {Element|null}
   */
  function closestChip(target) {
    if (!target || !target.closest) {
      return null;
    }
    return target.closest("span.ez-var[data-ez-var]");
  }

  /**
   * @param {Element} chip
   * @returns {string}
   */
  function stripChipText(chip) {
    return (chip.textContent || "").replace(/\n/g, "");
  }

  /**
   * @param {Element} chip
   */
  function selectAll(chip) {
    var range = document.createRange();
    range.selectNodeContents(chip);
    var sel = window.getSelection();
    if (!sel) {
      return;
    }
    sel.removeAllRanges();
    sel.addRange(range);
  }

  /**
   * @param {string} name
   * @param {string} raw
   * @param {Element|null} exceptEl
   * @param {boolean} persist
   */
  function commitVar(name, raw, exceptEl, persist) {
    if (!Object.prototype.hasOwnProperty.call(currentDefaults, name)) {
      return;
    }
    currentValues[name] = raw;
    if (persist) {
      saveVars(currentValues);
    }
    applyValues(exceptEl);
  }

  /**
   * Delegate chip edit + just-in-time clipboard (once per page JS lifetime).
   */
  function ensureChipDelegation() {
    if (chipDelegated) {
      return;
    }
    chipDelegated = true;

    document.addEventListener("focusin", function (ev) {
      var chip = closestChip(ev.target);
      if (!chip) {
        return;
      }
      chip.setAttribute("data-ez-draft", chip.textContent || "");
      window.setTimeout(function () {
        if (document.activeElement === chip) {
          selectAll(chip);
        }
      }, 0);
    });

    document.addEventListener("input", function (ev) {
      var chip = closestChip(ev.target);
      if (!chip) {
        return;
      }
      var name = chip.getAttribute("data-ez-var");
      var text = stripChipText(chip);
      if (chip.textContent !== text) {
        chip.textContent = text;
      }
      commitVar(name, text, chip, true);
    });

    document.addEventListener("keydown", function (ev) {
      var chip = closestChip(ev.target);
      if (!chip) {
        return;
      }
      if (ev.key === "Enter") {
        ev.preventDefault();
        chip.blur();
      }
      if (ev.key === "Escape") {
        ev.preventDefault();
        var name = chip.getAttribute("data-ez-var");
        var draft = chip.getAttribute("data-ez-draft");
        var revert = draft;
        if (revert === null || typeof revert === "undefined") {
          revert = currentDefaults[name] || "";
        }
        chip.textContent = revert;
        commitVar(name, revert, null, true);
        chip.blur();
      }
    });

    document.addEventListener("focusout", function (ev) {
      var chip = closestChip(ev.target);
      if (!chip) {
        return;
      }
      var name = chip.getAttribute("data-ez-var");
      var next = stripChipText(chip).trim() || currentDefaults[name] || "";
      chip.textContent = next;
      commitVar(name, next, null, true);
    });

    document.addEventListener(
      "paste",
      function (ev) {
        var chip = closestChip(ev.target);
        if (!chip) {
          return;
        }
        ev.preventDefault();
        var pasted = "";
        if (ev.clipboardData) {
          pasted = ev.clipboardData.getData("text/plain") || "";
        }
        pasted = pasted.replace(/\s+/g, " ").trim();
        if (document.queryCommandSupported && document.queryCommandSupported("insertText")) {
          document.execCommand("insertText", false, pasted);
        } else {
          chip.textContent = pasted;
          commitVar(chip.getAttribute("data-ez-var"), pasted, chip, true);
        }
      },
      true
    );

    function stampClipboardButton(ev) {
      var btn = ev.target && ev.target.closest ? ev.target.closest(".md-clipboard") : null;
      if (!btn) {
        return;
      }
      var root = btn.closest(".highlight") || btn.closest("pre") || btn.parentElement;
      if (!root) {
        return;
      }
      var code = root.querySelector("code[data-ez-src]");
      if (!code) {
        return;
      }
      btn.setAttribute(
        "data-clipboard-text",
        substituteVars(code.getAttribute("data-ez-src") || "", currentValues)
      );
    }
    document.addEventListener("pointerdown", stampClipboardButton, true);
    document.addEventListener("click", stampClipboardButton, true);
  }

  /**
   * @param {string} tag
   * @param {string} className
   * @returns {HTMLElement}
   */
  function el(tag, className) {
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    return node;
  }

  /**
   * Inject the Your Spark panel once per article.
   * @param {object} data
   */
  function injectPanel(data) {
    var article = document.querySelector("article.md-content__inner");
    if (!article || article.getAttribute("data-ez-spark") === "1") {
      return;
    }
    article.setAttribute("data-ez-spark", "1");
    var panel = el("details", "ez-spark-panel");
    var collapsed = false;
    try {
      collapsed = localStorage.getItem(PANEL_KEY) === "collapsed";
    } catch (err) {
      collapsed = false;
    }
    panel.open = !collapsed;
    panel.addEventListener("toggle", function () {
      try {
        localStorage.setItem(PANEL_KEY, panel.open ? "open" : "collapsed");
      } catch (e2) {
        /* ignore */
      }
    });

    var summary = el("summary", "ez-spark-panel__summary");
    summary.textContent = "Your Spark — edit IP and paths (saved in this browser)";
    panel.appendChild(summary);

    var hint = el("p", "ez-spark-panel__hint");
    hint.textContent =
      "Values replace ${SPARK_HOST} (and friends) in copyable commands on every docs page. Highlighted chips are the same fields — click to edit. Not sent to any server. Never put HF_TOKEN here.";
    panel.appendChild(hint);

    var grid = el("div", "ez-spark-panel__grid");
    (data.variables || []).forEach(function (row) {
      var label = el("label", "ez-spark-panel__field");
      var caption = el("span", "ez-spark-panel__label");
      caption.textContent = row.label;
      var input = document.createElement("input");
      input.type = "text";
      input.autocomplete = "off";
      input.spellcheck = false;
      input.name = row.id;
      input.value = currentValues[row.id] || row.default;
      input.setAttribute("aria-label", row.label);
      input.addEventListener("input", function () {
        currentValues[row.id] = input.value;
        saveVars(currentValues);
        applyValues(input);
      });
      input.addEventListener("change", function () {
        var next = input.value.trim() || row.default;
        currentValues[row.id] = next;
        input.value = next;
        saveVars(currentValues);
        applyValues(input);
      });
      label.appendChild(caption);
      label.appendChild(input);
      grid.appendChild(label);
    });
    panel.appendChild(grid);

    var actions = el("p", "ez-spark-panel__actions");
    var reset = document.createElement("button");
    reset.type = "button";
    reset.className = "ez-spark-panel__reset";
    reset.textContent = "Reset to defaults";
    reset.addEventListener("click", function () {
      var fresh = defaultVars(data);
      Object.keys(fresh).forEach(function (id) {
        currentValues[id] = fresh[id];
      });
      try {
        localStorage.removeItem(VARS_KEY);
      } catch (err) {
        /* ignore */
      }
      applyValues(null);
    });
    actions.appendChild(reset);
    panel.appendChild(actions);

    var banner = article.querySelector(".ez-docs-dev-banner");
    if (banner && banner.nextSibling) {
      article.insertBefore(panel, banner.nextSibling);
    } else if (banner) {
      article.appendChild(panel);
    } else {
      var heading = article.querySelector("h1");
      if (heading && heading.nextSibling) {
        article.insertBefore(panel, heading.nextSibling);
      } else {
        article.insertBefore(panel, article.firstChild);
      }
    }
  }

  /**
   * @param {object} flag
   * @param {object} flags
   * @param {object} values
   * @param {function(): void} onChange
   * @returns {HTMLElement}
   */
  function flagControl(flag, flags, values, onChange) {
    var wrap = el("label", "ez-cmd-builder__flag");
    if (flag.kind === "bool") {
      var box = document.createElement("input");
      box.type = "checkbox";
      box.checked = flagValue(flag, flags, values) === true;
      box.addEventListener("change", function () {
        flags[flag.name] = box.checked;
        onChange();
      });
      wrap.appendChild(box);
      wrap.appendChild(
        document.createTextNode(" --" + flag.name + (flag.label ? " (" + flag.label + ")" : ""))
      );
      return wrap;
    }

    var caption = el("span", "ez-cmd-builder__flag-label");
    caption.textContent = "--" + flag.name;
    wrap.appendChild(caption);
    var select = document.createElement("select");
    var current = String(flagValue(flag, flags, values));
    var known = {};
    (flag.choices || []).forEach(function (choice) {
      known[choice.value] = true;
      var opt = document.createElement("option");
      opt.value = choice.value;
      opt.textContent = choice.label;
      select.appendChild(opt);
    });
    var customOpt = null;
    if (flag.kind === "choice-or-int") {
      customOpt = document.createElement("option");
      customOpt.value = "__custom__";
      customOpt.textContent = (flag.int_label || "custom") + "…";
      select.appendChild(customOpt);
    }
    var isCustom = flag.kind === "choice-or-int" && current !== "" && !known[current];
    select.value = isCustom ? "__custom__" : current;
    wrap.appendChild(select);

    var number = null;
    if (flag.kind === "choice-or-int") {
      number = document.createElement("input");
      number.type = "number";
      number.min = "1";
      number.step = "1";
      number.setAttribute("aria-label", flag.int_label || "Mbps");
      number.placeholder = flag.int_label || "Mbps";
      if (isCustom) {
        number.value = current;
        number.hidden = false;
      } else {
        number.hidden = true;
      }
      wrap.appendChild(number);
    }

    function commit() {
      if (flag.kind === "choice-or-int" && select.value === "__custom__") {
        var n = parseInt(number.value, 10);
        if (!n || n < 1) {
          return;
        }
        flags[flag.name] = String(n);
        number.hidden = false;
      } else {
        flags[flag.name] = select.value;
        if (number) {
          number.hidden = true;
        }
      }
      onChange();
    }
    select.addEventListener("change", commit);
    if (number) {
      number.addEventListener("change", commit);
    }
    return wrap;
  }

  /**
   * Hydrate one .ez-cmd-builder placeholder.
   * @param {Element} root
   * @param {object} data
   * @param {object} values
   */
  function hydrateBuilder(root, data, values) {
    if (root.getAttribute("data-ez-ready") === "1") {
      var code = root.querySelector("pre code");
      var recipe = commandById(data, root.getAttribute("data-ez-cmd") || "");
      if (code && recipe) {
        var flags = loadFlags(recipe.id);
        var line = renderCommand(recipe, flags, values);
        code.textContent = line;
        var copyBtn = root.querySelector(".ez-cmd-builder__copy");
        if (copyBtn) {
          copyBtn.setAttribute("data-clipboard-text", line);
        }
      }
      return;
    }
    var cmdId = root.getAttribute("data-ez-cmd");
    var recipe = commandById(data, cmdId || "");
    if (!recipe) {
      return;
    }
    root.setAttribute("data-ez-ready", "1");
    var flags = loadFlags(recipe.id);
    root.replaceChildren();

    if (recipe.title || recipe.description) {
      var intro = el("div", "ez-cmd-builder__intro");
      if (recipe.title) {
        var title = el("p", "ez-cmd-builder__title");
        title.textContent = recipe.title;
        intro.appendChild(title);
      }
      if (recipe.description) {
        var desc = el("p", "ez-cmd-builder__desc");
        desc.textContent = recipe.description;
        intro.appendChild(desc);
      }
      root.appendChild(intro);
    }

    var form = el("div", "ez-cmd-builder__controls");
    function redraw() {
      saveFlags(recipe.id, flags);
      var line = renderCommand(recipe, flags, values);
      preCode.textContent = line;
      copy.setAttribute("data-clipboard-text", line);
    }
    (recipe.flags || []).forEach(function (flag) {
      form.appendChild(flagControl(flag, flags, values, redraw));
    });
    if ((recipe.flags || []).length) {
      root.appendChild(form);
    }

    var preWrap = el("div", "highlight ez-cmd-builder__code");
    var pre = document.createElement("pre");
    var preCode = document.createElement("code");
    preCode.className = "language-bash";
    var copy = document.createElement("button");
    copy.type = "button";
    copy.className = "ez-cmd-builder__copy md-clipboard";
    copy.title = "Copy to clipboard";
    copy.setAttribute("aria-label", "Copy command");
    copy.addEventListener("click", function () {
      var text = copy.getAttribute("data-clipboard-text") || preCode.textContent || "";
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text);
      }
    });
    pre.appendChild(preCode);
    pre.appendChild(copy);
    preWrap.appendChild(pre);
    root.appendChild(preWrap);
    redraw();
  }

  /**
   * @param {object} data
   * @param {object} values
   */
  function hydrateAll(data, values) {
    var nodes = document.querySelectorAll(".ez-cmd-builder[data-ez-cmd]");
    for (var i = 0; i < nodes.length; i += 1) {
      hydrateBuilder(nodes[i], data, values);
    }
  }

  /**
   * Page boot: panel, auto-bind code, hydrate recipes.
   */
  function init() {
    var data = payload();
    if (!data) {
      return;
    }
    currentData = data;
    currentDefaults = defaultVars(data);
    currentValues = loadVars(data);
    ensureChipDelegation();
    injectPanel(data);
    rebindCodes(currentValues);
    hydrateAll(data, currentValues);
  }

  boot(init);
})();

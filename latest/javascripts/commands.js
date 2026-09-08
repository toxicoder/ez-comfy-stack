/**
 * Your Spark variables + ezcmd flag builders (localStorage).
 * Copy uses data-clipboard-text so Material Clipboard.js gets substituted text.
 */
(function () {
  "use strict";

  var VARS_KEY = "ez-comfy.cmdvars";
  var FLAGS_PREFIX = "ez-comfy.cmdflags.";
  var PANEL_KEY = "ez-comfy.cmdpanel";
  var VAR_TOKEN = /\$\{([A-Z][A-Z0-9_]*)\}/g;

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
   * Spec: docs/commands.py substitute_vars (not recursive).
   * @param {string} template
   * @param {object} values
   * @returns {string}
   */
  function substituteVars(template, values) {
    return template.replace(VAR_TOKEN, function (match, name) {
      if (Object.prototype.hasOwnProperty.call(values, name)) {
        return values[name];
      }
      return match;
    });
  }

  /**
   * @param {string} template
   * @param {object} values
   * @returns {boolean}
   */
  function templateHasVars(template, values) {
    VAR_TOKEN.lastIndex = 0;
    var match;
    while ((match = VAR_TOKEN.exec(template)) !== null) {
      if (Object.prototype.hasOwnProperty.call(values, match[1])) {
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
   * Replace ${VAR} inside a single text node when the whole token is there.
   * @param {Element} code
   * @param {object} values
   * @returns {boolean} false when a fallback full-text rewrite is needed
   */
  function replaceTokensInTextNodes(code, values) {
    var walker = document.createTreeWalker(code, NodeFilter.SHOW_TEXT, null);
    var nodes = [];
    var node;
    while ((node = walker.nextNode())) {
      nodes.push(node);
    }
    var changed = false;
    var failed = false;
    nodes.forEach(function (textNode) {
      var src = textNode.nodeValue || "";
      if (!src.includes("${")) {
        return;
      }
      VAR_TOKEN.lastIndex = 0;
      if (!VAR_TOKEN.test(src)) {
        if (src.indexOf("${") >= 0) {
          failed = true;
        }
        return;
      }
      VAR_TOKEN.lastIndex = 0;
      var next = src.replace(VAR_TOKEN, function (match, name) {
        if (Object.prototype.hasOwnProperty.call(values, name)) {
          changed = true;
          return values[name];
        }
        return match;
      });
      if (next !== src) {
        textNode.nodeValue = next;
      }
    });
    return changed && !failed;
  }

  /**
   * Bind one existing fence: snapshot template, substitute, copy text.
   * @param {Element} code
   * @param {object} values
   */
  function bindFence(code, values) {
    var template = code.getAttribute("data-ez-src");
    if (template) {
      var again = substituteVars(template, values);
      code.textContent = again;
      setClipboardText(code, again);
      return;
    }
    template = code.textContent || "";
    if (!templateHasVars(template, values)) {
      return;
    }
    code.setAttribute("data-ez-src", template);
    code.setAttribute("data-ez-bound", "1");
    var rendered = substituteVars(template, values);
    if (!replaceTokensInTextNodes(code, values)) {
      code.textContent = rendered;
    }
    setClipboardText(code, rendered);
  }

  /**
   * Re-apply substitution to every auto-bound fence.
   * @param {object} values
   */
  function rebindFences(values) {
    var nodes = document.querySelectorAll("pre code");
    for (var i = 0; i < nodes.length; i += 1) {
      var code = nodes[i];
      if (code.closest(".ez-cmd-builder")) {
        continue;
      }
      bindFence(code, values);
    }
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
   * @param {object} values
   * @param {function(object): void} onChange
   */
  function injectPanel(data, values, onChange) {
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
      "Values replace ${SPARK_HOST} (and friends) in copyable commands on every docs page. Not sent to any server. Never put HF_TOKEN here.";
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
      input.value = values[row.id] || row.default;
      input.setAttribute("aria-label", row.label);
      input.addEventListener("change", function () {
        values[row.id] = input.value.trim() || row.default;
        input.value = values[row.id];
        saveVars(values);
        onChange(values);
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
        values[id] = fresh[id];
      });
      try {
        localStorage.removeItem(VARS_KEY);
      } catch (err) {
        /* ignore */
      }
      var inputs = grid.querySelectorAll("input");
      for (var i = 0; i < inputs.length; i += 1) {
        inputs[i].value = values[inputs[i].name];
      }
      onChange(values);
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
   * Page boot: panel, auto-bind fences, hydrate recipes.
   */
  function init() {
    var data = payload();
    if (!data) {
      return;
    }
    var values = loadVars(data);
    function refresh(next) {
      values = next;
      rebindFences(values);
      hydrateAll(data, values);
    }
    injectPanel(data, values, refresh);
    rebindFences(values);
    hydrateAll(data, values);
  }

  boot(init);
})();

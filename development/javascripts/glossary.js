/**
 * Definition modal for first-party glossary terms (span.ez-term).
 * Progressive enhancement: title= tooltips work without this script.
 */
(function () {
  "use strict";

  /**
   * Run fn on Material instant navigations, or on DOM ready.
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
   * Parse the per-page glossary JSON blob.
   * @returns {object|null}
   */
  function payload() {
    var el = document.getElementById("ez-glossary-data");
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
   * Split an href into the glossary path (no fragment).
   * @param {string} href
   * @returns {string}
   */
  function glossaryBase(href) {
    var value = href || "glossary/";
    var hash = value.indexOf("#");
    if (hash >= 0) {
      value = value.slice(0, hash);
    }
    return value || "glossary/";
  }

  /**
   * Bind one dialog to all .ez-term triggers on the page.
   */
  function init() {
    var data = payload();
    var dialog = document.getElementById("ez-glossary-dialog");
    if (!data || !dialog || dialog.getAttribute("data-ez-bound") === "1") {
      return;
    }
    dialog.setAttribute("data-ez-bound", "1");

    var titleEl = document.getElementById("ez-glossary-title");
    var bodyEl = document.getElementById("ez-glossary-body");
    var seeEl = document.getElementById("ez-glossary-see");
    var linkEl = document.getElementById("ez-glossary-link");
    var closeEl = document.getElementById("ez-glossary-close");
    var lastTrigger = null;

    /**
     * Fill dialog fields for a term id.
     * @param {string} id
     * @param {string} href
     * @returns {boolean}
     */
    function fill(id, href) {
      var term = data[id];
      if (!term || !titleEl || !bodyEl || !seeEl || !linkEl) {
        return false;
      }
      titleEl.textContent = term.title;
      bodyEl.textContent = term.short;
      var base = glossaryBase(href || linkEl.getAttribute("href") || "");
      linkEl.setAttribute("href", base + "#" + id);
      seeEl.replaceChildren();
      var see = term.see_also || [];
      if (!see.length) {
        seeEl.hidden = true;
        return true;
      }
      seeEl.hidden = false;
      seeEl.appendChild(document.createTextNode("See also: "));
      var wrote = 0;
      see.forEach(function (ref) {
        var other = data[ref];
        if (!other) {
          return;
        }
        if (wrote) {
          seeEl.appendChild(document.createTextNode(" · "));
        }
        wrote += 1;
        var chip = document.createElement("button");
        chip.type = "button";
        chip.className = "ez-glossary-dialog__chip";
        chip.textContent = other.title;
        chip.addEventListener("click", function () {
          fill(ref, linkEl.getAttribute("href"));
        });
        seeEl.appendChild(chip);
      });
      if (!wrote) {
        seeEl.hidden = true;
      }
      return true;
    }

    /**
     * Open the dialog from a trigger element.
     * @param {Event} ev
     * @param {Element} trigger
     */
    function openFrom(ev, trigger) {
      var id = trigger.getAttribute("data-term");
      var href = trigger.getAttribute("data-href") || "glossary/";
      if (!fill(id, href)) {
        return;
      }
      ev.preventDefault();
      lastTrigger = trigger;
      trigger.setAttribute("aria-expanded", "true");
      if (typeof dialog.showModal === "function") {
        dialog.showModal();
      }
    }

    /**
     * Close the dialog and restore focus.
     */
    function close() {
      if (typeof dialog.close === "function" && dialog.open) {
        dialog.close();
      }
      if (lastTrigger) {
        lastTrigger.setAttribute("aria-expanded", "false");
        lastTrigger.focus();
      }
    }

    document.addEventListener("click", function (ev) {
      var trigger = ev.target.closest ? ev.target.closest(".ez-term") : null;
      if (trigger) {
        openFrom(ev, trigger);
      }
    });
    document.addEventListener("keydown", function (ev) {
      if (ev.key !== "Enter" && ev.key !== " ") {
        return;
      }
      var target = ev.target;
      if (!target || !target.classList || !target.classList.contains("ez-term")) {
        return;
      }
      openFrom(ev, target);
    });
    if (closeEl) {
      closeEl.addEventListener("click", close);
    }
    dialog.addEventListener("click", function (ev) {
      if (ev.target === dialog) {
        close();
      }
    });
    dialog.addEventListener("close", function () {
      if (lastTrigger) {
        lastTrigger.setAttribute("aria-expanded", "false");
      }
    });
  }

  boot(init);
})();

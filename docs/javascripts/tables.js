/**
 * Pin markdown table headers under the Material navbar, then release so
 * the last body row and 25% of the previous row stay visible.
 *
 * CSS position:sticky on thead/th does not pin in Chromium here: Material
 * sets html { overflow-x: hidden } and tables start as display:inline-block.
 * Transform on thead/th also loses the stacking fight with tbody. A cloned
 * overlay (position:fixed, not the thead) paints above rows. Do not
 * position:fixed the thead itself (column widths collapse).
 */
(function () {
  "use strict";

  var TAIL_PREV_FRACTION = 0.25;
  var TABLE_SEL = ".md-typeset table:not([class])";
  var frame = 0;
  var bound = false;
  var overlays = new WeakMap();

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
   * Bottom of the persistent header (title + tabs when tabs are shown).
   * @returns {number}
   */
  function navBottom() {
    var header = document.querySelector(".md-header");
    if (!header) {
      return 0;
    }
    return header.getBoundingClientRect().bottom;
  }

  /**
   * Viewport Y for the overlay top: navbar bottom, clamped so tail rows
   * stay clear.
   * @param {HTMLTableElement} table
   * @param {HTMLTableSectionElement} thead
   * @param {number} pin
   * @returns {number}
   */
  function clampTop(table, thead, pin) {
    var bodies = table.tBodies;
    if (!bodies.length) {
      return pin;
    }
    var rows = bodies[bodies.length - 1].rows;
    if (!rows.length) {
      return pin;
    }
    var last = rows[rows.length - 1];
    var prev = rows.length > 1 ? rows[rows.length - 2] : last;
    var tail =
      last.getBoundingClientRect().height +
      TAIL_PREV_FRACTION * prev.getBoundingClientRect().height;
    var theadH = thead.getBoundingClientRect().height;
    var maxTop = table.getBoundingClientRect().bottom - tail - theadH;
    return Math.min(pin, maxTop);
  }

  /**
   * Overlay host for one table (cloned thead, aria-hidden).
   * @param {HTMLTableElement} table
   * @returns {HTMLDivElement}
   */
  function overlayFor(table) {
    var el = overlays.get(table);
    if (el && el.isConnected) {
      return el;
    }
    el = document.createElement("div");
    el.className = "ez-table-pin";
    el.setAttribute("aria-hidden", "true");
    var host = table.closest(".md-typeset") || document.body;
    host.appendChild(el);
    overlays.set(table, el);
    var wrap = table.closest(".md-typeset__scrollwrap");
    if (wrap && !wrap.getAttribute("data-ez-pin-scroll")) {
      wrap.setAttribute("data-ez-pin-scroll", "1");
      wrap.addEventListener("scroll", schedule, { passive: true });
    }
    return el;
  }

  /**
   * Copy header cells into the overlay and match on-screen column widths.
   * @param {HTMLDivElement} overlay
   * @param {HTMLTableSectionElement} thead
   */
  function fillOverlay(overlay, thead) {
    var cloneTable = document.createElement("table");
    var cloneHead = thead.cloneNode(true);
    cloneHead.style.visibility = "";
    cloneTable.appendChild(cloneHead);
    overlay.replaceChildren(cloneTable);
    var src = thead.rows[0] ? thead.rows[0].cells : [];
    var dstTable = overlay.querySelector("table");
    var dstHead = dstTable ? dstTable.tHead : null;
    var dst = dstHead && dstHead.rows[0] ? dstHead.rows[0].cells : [];
    var i;
    var n = Math.min(src.length, dst.length);
    for (i = 0; i < n; i++) {
      dst[i].style.width = src[i].getBoundingClientRect().width + "px";
    }
  }

  /**
   * Show or hide the cloned header for one table.
   * @param {HTMLTableElement} table
   * @param {number} pin
   */
  function pinTable(table, pin) {
    var thead = table.tHead;
    var overlay = overlayFor(table);
    if (!thead || !thead.rows.length) {
      overlay.hidden = true;
      return;
    }
    var naturalTop = thead.getBoundingClientRect().top;
    var desired = clampTop(table, thead, pin);
    var dy = desired - naturalTop;
    if (dy <= 0.5) {
      overlay.hidden = true;
      overlay.replaceChildren();
      return;
    }
    var wrap = table.closest(".md-typeset__scrollwrap") || table;
    var wrapRect = wrap.getBoundingClientRect();
    var tableRect = table.getBoundingClientRect();
    var left = Math.max(wrapRect.left, tableRect.left);
    var right = Math.min(wrapRect.right, tableRect.right);
    overlay.hidden = false;
    overlay.style.top = desired + "px";
    overlay.style.left = left + "px";
    overlay.style.width = Math.max(0, right - left) + "px";
    overlay.style.height = thead.getBoundingClientRect().height + 1 + "px";
    fillOverlay(overlay, thead);
    var inner = overlay.querySelector("table");
    if (inner) {
      inner.style.marginLeft = tableRect.left - left + "px";
    }
  }

  /**
   * Pin every typeset markdown table on this frame.
   */
  function update() {
    frame = 0;
    var pin = navBottom();
    var tables = document.querySelectorAll(TABLE_SEL);
    var i;
    for (i = 0; i < tables.length; i++) {
      pinTable(tables[i], pin);
    }
  }

  /**
   * Coalesce scroll/resize into one layout pass.
   */
  function schedule() {
    if (frame) {
      return;
    }
    frame = window.requestAnimationFrame(update);
  }

  /**
   * Bind listeners once; re-run update on Material document$ ticks.
   */
  function init() {
    update();
    if (bound) {
      return;
    }
    bound = true;
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    window.addEventListener("orientationchange", schedule);
    var header = document.querySelector(".md-header");
    if (header && typeof MutationObserver !== "undefined") {
      var obs = new MutationObserver(schedule);
      obs.observe(header, {
        attributes: true,
        subtree: true,
        attributeFilter: ["class"],
      });
    }
  }

  boot(init);
})();

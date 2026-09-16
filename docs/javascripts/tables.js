/**
 * Pin markdown table headers under the Material navbar, then release so
 * the last body row and 25% of the previous row stay visible. Hide the pin
 * (and the h-scroll mirror) once the table is fully above the navbar or
 * below the viewport — a position:fixed clone with a negative top can be
 * clamped back into view under html { overflow-x: hidden }.
 *
 * When a table is wider than the article and taller than the viewport,
 * the native wrap scrollbar sits off-screen at the wrap bottom. A cloned
 * .ez-table-hscroll bar (position:fixed, not sticky) stays on screen and
 * mirrors wrap.scrollLeft. The pinned header pans with the same scrollLeft
 * via translateX.
 *
 * CSS position:sticky on thead/th (or a sticky scrollbar) does not pin in
 * Chromium here: Material sets html { overflow-x: hidden } and tables start
 * as display:inline-block. Transform on thead/th also loses the stacking
 * fight with tbody. A cloned overlay (position:fixed, not the thead) paints
 * above rows. Do not position:fixed the thead itself (column widths collapse).
 */
(function () {
  "use strict";

  var TAIL_PREV_FRACTION = 0.25;
  var TABLE_SEL = ".md-typeset table:not([class])";
  var frame = 0;
  var bound = false;
  var syncing = false;
  var overlays = new WeakMap();
  var bars = new WeakMap();

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
   * Material wrap (the real overflow-x scrollport) or the table itself.
   * @param {HTMLTableElement} table
   * @returns {Element}
   */
  function scrollWrap(table) {
    return table.closest(".md-typeset__scrollwrap") || table;
  }

  /**
   * Whether a table or wrap still intersects the band below the navbar.
   * @param {DOMRect} rect
   * @param {number} pin
   * @returns {boolean}
   */
  function inStickyBand(rect, pin) {
    return rect.bottom > pin && rect.top < window.innerHeight;
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
   * Rounded source header cell widths, used to skip clone rebuilds.
   * @param {HTMLTableSectionElement} thead
   * @returns {string}
   */
  function widthKey(thead) {
    var cells = thead.rows[0] ? thead.rows[0].cells : [];
    var parts = [];
    var i;
    for (i = 0; i < cells.length; i++) {
      parts.push(Math.round(cells[i].getBoundingClientRect().width));
    }
    return parts.join(",");
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
    bindWrapScroll(table);
    return el;
  }

  /**
   * Listen to wrap scroll once so the pin and h-scroll bar stay in sync.
   * @param {HTMLTableElement} table
   */
  function bindWrapScroll(table) {
    var wrap = scrollWrap(table);
    if (wrap.getAttribute("data-ez-pin-scroll")) {
      return;
    }
    wrap.setAttribute("data-ez-pin-scroll", "1");
    wrap.addEventListener("scroll", schedule, { passive: true });
  }

  /**
   * Copy header cells into the overlay and match on-screen column widths.
   * @param {HTMLDivElement} overlay
   * @param {HTMLTableSectionElement} thead
   */
  function fillOverlay(overlay, thead) {
    var key = widthKey(thead);
    if (overlay.getAttribute("data-ez-widths") === key && overlay.querySelector("table")) {
      return;
    }
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
    overlay.setAttribute("data-ez-widths", key);
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
    var tableRect = table.getBoundingClientRect();
    if (!inStickyBand(tableRect, pin)) {
      overlay.hidden = true;
      return;
    }
    var theadRect = thead.getBoundingClientRect();
    var theadH = theadRect.height;
    var naturalTop = theadRect.top;
    var desired = clampTop(table, thead, pin);
    var dy = desired - naturalTop;
    if (dy <= 0.5) {
      overlay.hidden = true;
      return;
    }
    if (desired + theadH <= pin) {
      overlay.hidden = true;
      return;
    }
    var wrap = scrollWrap(table);
    var wrapRect = wrap.getBoundingClientRect();
    overlay.hidden = false;
    overlay.style.top = desired + "px";
    overlay.style.left = wrapRect.left + "px";
    overlay.style.width = Math.max(0, wrapRect.width) + "px";
    overlay.style.height = theadH + 1 + "px";
    fillOverlay(overlay, thead);
    var inner = overlay.querySelector("table");
    if (inner) {
      // tableRect.left tracks wrap.scrollLeft (plus wrap padding).
      inner.style.transform = "translateX(" + (tableRect.left - wrapRect.left) + "px)";
    }
  }

  /**
   * Floating h-scroll host for one table (aria-hidden mirror of wrap).
   * @param {HTMLTableElement} table
   * @returns {HTMLDivElement}
   */
  function barFor(table) {
    var el = bars.get(table);
    if (el && el.isConnected) {
      return el;
    }
    el = document.createElement("div");
    el.className = "ez-table-hscroll";
    el.setAttribute("aria-hidden", "true");
    var inner = document.createElement("div");
    inner.className = "ez-table-hscroll__inner";
    el.appendChild(inner);
    var host = table.closest(".md-typeset") || document.body;
    host.appendChild(el);
    bars.set(table, el);
    bindWrapScroll(table);
    el.addEventListener(
      "scroll",
      function () {
        if (syncing) {
          return;
        }
        var wrap = scrollWrap(table);
        syncing = true;
        wrap.scrollLeft = el.scrollLeft;
        syncing = false;
      },
      { passive: true }
    );
    return el;
  }

  /**
   * Whether wrap overflows X and the native bar at wrap.bottom is off-screen.
   * @param {Element} wrap
   * @param {number} pin
   * @returns {boolean}
   */
  function needsHScroll(wrap, pin) {
    if (wrap.scrollWidth <= wrap.clientWidth + 1) {
      return false;
    }
    var rect = wrap.getBoundingClientRect();
    if (!inStickyBand(rect, pin)) {
      return false;
    }
    var vh = window.innerHeight;
    if (rect.bottom <= vh && rect.bottom > 0) {
      return false;
    }
    return true;
  }

  /**
   * Pin a wrap.scrollLeft mirror to the viewport bottom when the native bar
   * would sit below the fold.
   * @param {HTMLTableElement} table
   * @param {number} pin
   */
  function placeHScroll(table, pin) {
    var wrap = scrollWrap(table);
    var bar = barFor(table);
    if (!needsHScroll(wrap, pin)) {
      bar.hidden = true;
      return;
    }
    var wrapRect = wrap.getBoundingClientRect();
    var inner = bar.firstElementChild;
    bar.hidden = false;
    bar.style.left = wrapRect.left + "px";
    bar.style.width = wrap.clientWidth + "px";
    bar.style.bottom = "0px";
    if (inner) {
      inner.style.width = wrap.scrollWidth + "px";
    }
    if (!syncing && bar.scrollLeft !== wrap.scrollLeft) {
      syncing = true;
      bar.scrollLeft = wrap.scrollLeft;
      syncing = false;
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
      placeHScroll(tables[i], pin);
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

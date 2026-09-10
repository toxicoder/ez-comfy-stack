/**
 * Relative label for the last-published chip.
 * Build stamps absolute UTC on <time datetime>; this only rewrites text.
 */
(function () {
  "use strict";

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
   * English relative label, or fallback when older than 14 days.
   * @param {string} iso
   * @param {string} fallback
   * @returns {string}
   */
  function relativeLabel(iso, fallback) {
    var then = Date.parse(iso);
    if (isNaN(then)) {
      return fallback;
    }
    var delta = Date.now() - then;
    if (delta < 0) {
      delta = 0;
    }
    var minute = 60 * 1000;
    var hour = 60 * minute;
    var day = 24 * hour;
    if (delta < minute) {
      return "just now";
    }
    if (delta < hour) {
      var mins = Math.floor(delta / minute);
      return mins === 1 ? "1 minute ago" : mins + " minutes ago";
    }
    if (delta < day) {
      var hours = Math.floor(delta / hour);
      return hours === 1 ? "1 hour ago" : hours + " hours ago";
    }
    if (delta < 14 * day) {
      var days = Math.floor(delta / day);
      return days === 1 ? "1 day ago" : days + " days ago";
    }
    return fallback;
  }

  /**
   * Rewrite chip <time> text; leave datetime and title absolute.
   */
  function apply() {
    var nodes = document.querySelectorAll(".ez-published-chip time[datetime]");
    var i;
    for (i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var iso = el.getAttribute("datetime");
      if (!iso) {
        continue;
      }
      var fallback = el.textContent || "";
      el.textContent = relativeLabel(iso, fallback);
    }
  }

  boot(apply);
})();

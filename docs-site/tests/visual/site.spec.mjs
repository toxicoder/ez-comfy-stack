/*
 * Visual regression for the documentation site.
 *
 * Replaces the screenshot half of `docs/test_mkdocs_render.py`.  Pages are captured from the
 * static export served by `scripts/serve_static.mjs`, so what is compared is exactly what
 * GitHub Pages publishes.
 *
 * Goldens are produced on the CI image.  Font metrics differ per platform, so a screenshot
 * taken on a laptop never matches one taken on Linux: refresh baselines in the container
 * that matches CI (`bazelisk run //docs-site:visual-linux -- --update`), never from a
 * workstation, and review the resulting diffs before committing them.
 *
 * A page with no baseline yet gets one written on the spot, so the set bootstraps itself on
 * the first green run instead of failing until somebody remembers to capture it.  That is a
 * convenience for a local run only: under CI it would commit a screenshot nobody reviewed, so
 * there a missing baseline is a hard failure (see `test_visual_tooling.py`).
 */
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

import { expect, test } from "@playwright/test";

const GOLDENS_DIR = join(import.meta.dirname, "goldens");
/** CI must never invent a baseline; only a local run may bootstrap one. */
const CI = Boolean(process.env.CI);

/**
 * Pages whose rendering is worth a baseline, chosen to cover each surface the site draws:
 * the home hero, long prose, a Mermaid architecture diagram, callouts, wide tables, a
 * generated reference page.  Every route here is cross-checked against the `docs/` tree by
 * `//docs-site:visual_tooling_test`, because this list was ported from the MkDocs site and
 * six of its ten entries had rotted into routes that no longer exist.
 */
const KEY_PAGES = [
  ["index", "/"],
  ["getting-started", "/getting-started/"],
  ["architecture", "/learn/architecture/"],
  ["models-and-cache", "/models-and-cache/"],
  ["troubleshooting", "/troubleshooting/"],
  ["reboot-safety", "/reboot-safety/"],
  ["manage-cli", "/manage-cli/"],
  ["download-tiers", "/download-tiers/"],
  ["studio-apps", "/studio-apps/"],
  ["generated-audio", "/generated/audio/"]
];

/** Wait for hydration and for the widgets that paint after the first render. */
async function settle(page) {
  await page.waitForSelector("h1", { state: "visible" });
  // Mermaid diagrams are drawn client-side; wait for the SVG rather than a fixed pause.
  await page
    .waitForFunction(
      () =>
        Array.from(document.querySelectorAll('[aria-label="Mermaid diagram"]')).every((host) =>
          host.querySelector("svg")
        ),
      undefined,
      { timeout: 30000 }
    )
    .catch(() => undefined);

  // Enter transitions are still running when the screenshot starts, and
  // `animations: "disabled"` freezes them mid-flight instead of completing them, so a
  // baseline taken a moment earlier would be permanently faded.  Drive every animation
  // and transition to its end state first, then let the layout settle.
  await page.evaluate(() => {
    for (const animation of document.getAnimations()) {
      try {
        animation.finish();
      } catch {
        // Infinite animations (spinners) cannot be finished; leave them alone.
      }
    }
  });
  // The last-published chip rewrites itself from Date.now() once it hydrates, so its visible
  // text is a relative phrase that changes between the day a baseline is captured and any day
  // it is later compared.  Restore the absolute label from the baked datetime attribute, which
  // the pinned visual build fixes, so the wall clock cannot move a baseline.
  await page.evaluate(() => {
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    for (const time of document.querySelectorAll(".ez-published-chip time[datetime]")) {
      const stamp = new Date(time.getAttribute("datetime") ?? "");
      if (Number.isNaN(stamp.getTime())) continue;
      time.textContent = `${stamp.getUTCDate()} ${months[stamp.getUTCMonth()]} ${stamp.getUTCFullYear()}`;
    }
  });

  // Animations are finished above, so only the paint after the last DOM change is pending.
  await page.waitForTimeout(400);
}

for (const [slug, route] of KEY_PAGES) {
  test(slug, async ({ page }, testInfo) => {
    const response = await page.goto(route, { waitUntil: "commit" });
    // A route the export no longer has is served as the 404 page, which carries an h1 and a
    // short body, so every wait below still passes and the suite happily baselines a blank
    // frame.  This is how six of the ten original entries went unnoticed.
    if (!response?.ok()) {
      throw new Error(
        `${slug}: ${route} returned ${response?.status() ?? "no response"}; the page list points at a route the export does not have`,
      );
    }
    await settle(page);

    // Mirrors snapshotPathTemplate in playwright.config.mjs: goldens/<project>/<name>.png.
    const golden = join(GOLDENS_DIR, testInfo.project?.name ?? "desktop", `${slug}.png`);
    if (!existsSync(golden)) {
      if (CI) {
        await testInfo.fail(
          `no committed baseline at ${golden}; capture it with \`npm run visual:linux\` ` +
            "(the Linux container that matches the CI renderer) and review the diff before committing"
        );
        return;
      }
      mkdirSync(dirname(golden), { recursive: true });
      writeFileSync(golden, await page.screenshot({ fullPage: true, animations: "disabled" }));
      expect(true, `no baseline for ${slug} yet; created ${golden} - review and commit it`).toBe(true);
      return;
    }

    await expect(page).toHaveScreenshot(`${slug}.png`, {
      animations: "disabled",
      fullPage: true,
      // Small tolerance for font-hinting differences between CI images; 0 otherwise.
      maxDiffPixelRatio: 0.005,
      // Compared against the path derived above, so the self-bootstrap and the diff agree.
      snapshotPath: golden
    });
  });
}

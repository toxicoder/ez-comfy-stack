/**
 * Docs pages must render a single prev/next pager.
 *
 * `DocsPage` already draws a footer. Nesting `<PageFooter>` inside `DocsBody`
 * duplicated Previous Page / Next Page at the bottom of every article.
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const pageSrc = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "../../app/[[...slug]]/page.tsx"),
  "utf8"
);

describe("docs page footer", () => {
  it("passes neighbors into DocsPage footer and does not nest PageFooter", () => {
    expect(pageSrc).toMatch(/footer=\{\{\s*items:\s*neighborsOf/);
    expect(pageSrc).not.toMatch(/<PageFooter/);
    expect(pageSrc).toMatch(/<EditOnGitHub/);
  });
});

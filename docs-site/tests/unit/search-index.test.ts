/**
 * Tests for search-index slimming.
 *
 * Generated table-heavy pages must not dump every cell into Orama: the
 * unslimmed export was 379 MiB and GitHub rejected the gh-pages push.
 */

import { describe, expect, it } from "vitest";

import {
  SEARCH_AUTHORED_CONTENTS_MAX,
  SEARCH_HEADINGS_MAX,
  isHeavySearchPath,
  slimSearchStructuredData,
  type SearchStructuredData
} from "../../lib/search-index";

function bulky(count: number): SearchStructuredData {
  return {
    headings: Array.from({ length: count }, (_, i) => ({
      id: `h-${i}`,
      content: `Heading ${i}`
    })),
    contents: Array.from({ length: count }, (_, i) => ({
      heading: `h-${i}`,
      content: `Cell ${i}`
    }))
  };
}

describe("isHeavySearchPath", () => {
  it("treats generated encyclopedias as heavy", () => {
    expect(isHeavySearchPath("generated/workflows/films/breakwater/act-01.md")).toBe(true);
    expect(isHeavySearchPath("generated/cinema/camera_movement.md")).toBe(true);
  });

  it("treats the workflow-nodes dump as heavy", () => {
    expect(isHeavySearchPath("reference/workflow-nodes.md")).toBe(true);
    expect(isHeavySearchPath("reference/workflow-nodes.mdx")).toBe(true);
  });

  it("leaves authored pages as full-text", () => {
    expect(isHeavySearchPath("getting-started.md")).toBe(false);
    expect(isHeavySearchPath("contribute/testing-docs.mdx")).toBe(false);
  });
});

describe("slimSearchStructuredData", () => {
  it("drops body blocks on generated pages and caps headings", () => {
    const slim = slimSearchStructuredData(
      "generated/workflows/films/breakwater/act-01.md",
      bulky(200)
    );
    expect(slim.contents).toEqual([]);
    expect(slim.headings).toHaveLength(SEARCH_HEADINGS_MAX);
  });

  it("keeps a bounded body on authored pages", () => {
    const slim = slimSearchStructuredData("getting-started.md", bulky(200));
    expect(slim.contents).toHaveLength(SEARCH_AUTHORED_CONTENTS_MAX);
    expect(slim.headings).toHaveLength(SEARCH_HEADINGS_MAX);
  });
});

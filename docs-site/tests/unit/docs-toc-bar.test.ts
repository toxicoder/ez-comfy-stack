/**
 * Tests for the top-of-page heading row.
 *
 * The row is the reader's orientation cue, so two properties matter and neither is visible
 * in a screenshot: a chip has to exist for every heading the reader can land on, and exactly
 * one chip may claim to be the current position.
 */

import { createElement } from "react";
import { describe, expect, it } from "vitest";

import {
  tocBarActiveId,
  tocBarChips,
  tocBarTitle,
  type TocBarSourceItem
} from "../../components/docs-toc-bar";

describe("tocBarTitle", () => {
  it("reads a plain title", () => {
    expect(tocBarTitle("Getting Started")).toBe("Getting Started");
  });

  it("flattens the inline markup an authored heading can carry", () => {
    const node = createElement(
      "h2",
      null,
      "Set up ",
      createElement("code", null, "bazelisk"),
      " first"
    );
    expect(tocBarTitle(node)).toBe("Set up bazelisk first");
  });

  it("reads a numeric or arrayed title", () => {
    expect(tocBarTitle(7)).toBe("7");
    expect(tocBarTitle(["A", " ", "B"])).toBe("A B");
  });

  it("yields nothing for a node that carries no text", () => {
    expect(tocBarTitle(createElement("img", { src: "x" }))).toBe("");
    expect(tocBarTitle(undefined)).toBe("");
  });
});

function item(id: string, title: string, depth: number, active = false): TocBarSourceItem {
  return { id, title, depth, active };
}

describe("tocBarChips", () => {
  it("keeps every heading in document order", () => {
    const chips = tocBarChips([item("a", "Alpha", 2), item("b", "Beta", 3), item("c", "Gamma", 2)]);
    expect(chips.map((chip) => chip.id)).toEqual(["a", "b", "c"]);
  });

  it("collapses whitespace and trims a title, so a chip is never blank-looking", () => {
    const chips = tocBarChips([item("a", "  Set   up\nthis  computer ", 2)]);
    expect(chips[0]?.title).toBe("Set up this computer");
  });

  it("drops a heading with no usable label", () => {
    const chips = tocBarChips([item("a", "   ", 2), item("b", "Real", 2)]);
    expect(chips.map((chip) => chip.id)).toEqual(["b"]);
  });

  it("drops a repeated anchor so one position cannot light two chips", () => {
    const chips = tocBarChips([item("a", "First", 2), item("a", "Duplicate", 2)]);
    expect(chips).toHaveLength(1);
    expect(chips[0]?.title).toBe("First");
  });

  it("folds headings below the third level into the third level", () => {
    const chips = tocBarChips([item("a", "H2", 2), item("b", "H3", 3), item("c", "H5", 5)]);
    expect(chips.map((chip) => chip.depth)).toEqual([2, 3, 3]);
  });

  it("treats a heading shallower than h2 as a top-level chip", () => {
    expect(tocBarChips([item("a", "H1", 1)])[0]?.depth).toBe(2);
  });

  it("returns nothing for a page with no headings", () => {
    expect(tocBarChips([])).toEqual([]);
  });
});

describe("tocBarActiveId", () => {
  it("is undefined above the first heading", () => {
    expect(tocBarActiveId([item("a", "Alpha", 2), item("b", "Beta", 3)])).toBeUndefined();
  });

  it("names the deepest latest active heading while nested headings overlap", () => {
    const items = [item("a", "Alpha", 2, true), item("b", "Beta", 3, true), item("c", "Gamma", 2)];
    expect(tocBarActiveId(items)).toBe("b");
  });

  it("ignores an active heading that has no id", () => {
    expect(tocBarActiveId([item("", "Orphan", 2, true), item("b", "Beta", 2, true)])).toBe("b");
  });
});

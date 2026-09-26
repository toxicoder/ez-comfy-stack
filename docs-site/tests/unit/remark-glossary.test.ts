/**
 * Tests for the glossary tooltip transformer.
 *
 * The MkDocs site auto-appended `docs/includes/abbreviations.md` and wrapped each known
 * term in a tooltip.  The port has to keep doing that, and it has to keep working when the
 * compiler's working directory is the docs package rather than the repository - which is
 * the case that silently produced zero tooltips once.
 */

import { describe, expect, it } from "vitest";

import { remarkGlossaryTooltips } from "../../lib/remark-glossary";

/** A node loose enough to inspect: the transformer works on unstructured mdast nodes. */
interface Node {
  type: string;
  name?: string;
  value?: string;
  children?: Node[];
  attributes?: { name: string; value: string }[];
}

/** Build a root holding one paragraph of the given text and run the transformer over it. */
function applyTo(text: string, parentType = "paragraph"): Node {
  const tree: Node = {
    type: "root",
    children: [{ type: parentType, children: [{ type: "text", value: text }] }]
  };
  (remarkGlossaryTooltips() as (tree: unknown) => void)(tree);
  return tree;
}

const childrenOf = (node: Node, index = 0) => node.children?.[index]?.children ?? [];

describe("remarkGlossaryTooltips", () => {
  it("loads glossary.json terms", () => {
    const children = childrenOf(applyTo("Klein 4B is the default still engine."));
    expect(children.filter((child) => child.type === "mdxJsxTextElement").length).toBeGreaterThan(0);
  });

  it("wraps a known term with EzTerm", () => {
    const children = childrenOf(applyTo("Klein 4B is the default still engine."));
    const term = children.find((child) => child.name === "EzTerm");
    expect(term?.type).toBe("mdxJsxTextElement");
    expect(term?.attributes?.some((attr) => attr.name === "termId" && attr.value === "klein")).toBe(true);
  });

  it("leaves unknown terms untouched", () => {
    const children = childrenOf(applyTo("Nothing exotic zzznotaterm here at all."));
    expect(children.every((child) => child.type === "text")).toBe(true);
  });

  it("does not touch text inside a heading", () => {
    const children = childrenOf(applyTo("Klein and Wan", "heading"));
    expect(children.every((child) => child.type === "text")).toBe(true);
  });
});

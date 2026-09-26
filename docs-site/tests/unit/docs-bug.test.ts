/**
 * Prefilled GitHub issue URLs for the heading bug button.
 */

import { describe, expect, it } from "vitest";

import { docsBugHref, type DocsBugReport } from "../../lib/docs-bug";

function report(overrides: Partial<DocsBugReport> = {}): DocsBugReport {
  return {
    pageUrl: "https://toxicoder.github.io/ez-comfy-stack/development/operate/update/#pull-this-docs-branch",
    pageTitle: "Update the stack",
    heading: "Pull this docs branch",
    headingId: "pull-this-docs-branch",
    sourcePath: "docs/operate/update.mdx",
    sourceUrl: "https://github.com/toxicoder/ez-comfy-stack/blob/development/docs/operate/update.mdx",
    gitRef: "development",
    docsAlias: "development",
    userAgent: "TestAgent/1.0",
    viewport: "1440x950",
    colorScheme: "dark",
    selection: "",
    ...overrides
  };
}

describe("docsBugHref", () => {
  it("opens a new GitHub issue with the page, heading, alias, and blanks", () => {
    const href = docsBugHref(report());
    const url = new URL(href);
    expect(url.origin + url.pathname).toBe("https://github.com/toxicoder/ez-comfy-stack/issues/new");
    expect(url.searchParams.get("title")).toBe("Docs: Update the stack - Pull this docs branch");
    const body = url.searchParams.get("body") ?? "";
    expect(body).toContain("operate/update/#pull-this-docs-branch");
    expect(body).toContain("`#pull-this-docs-branch`");
    expect(body).toContain("Docs alias: development");
    expect(body).toContain("Git ref: development");
    expect(body).toContain("docs/operate/update.mdx");
    expect(body).toContain("## What is wrong");
    expect(body).toContain("## What it should say");
    expect(body).toContain("<!-- Replace this line. -->");
    expect(body).toContain("1440x950");
    expect(body).toContain("Color scheme: dark");
  });

  it("drops a huge selection so the URL stays openable", () => {
    const href = docsBugHref(report({ selection: "x".repeat(20_000), userAgent: "y".repeat(5_000) }));
    expect(href.length).toBeLessThanOrEqual(5500);
    expect(href).toContain("/issues/new");
  });
});
/**
 * The docs navigation is one traditional menu on the left.
 *
 * fumadocs-ui turns every `root: true` folder of the page tree into a layout tab, and the
 * docs sidebar renders those tabs as a dropdown selector (`SidebarTabsDropdown`, a dialog
 * trigger with a chevrons-up-down icon) while showing only the active tab's subtree. This
 * site wants the opposite: a plain vertical menu that lists every section as a collapsible
 * folder, so the tree must contain no root folders at all. The right-hand table of contents
 * comes from `DocsPage`'s `toc` prop and is unaffected by the tree.
 */

import { describe, expect, it } from "vitest";

import type { Folder } from "fumadocs-core/page-tree";

import navData from "../../lib/nav.json";
import { buildPageTree, injectGenerated, stripExtension } from "../../lib/nav";
import type { NavSource, NavNode, NavTab } from "../../lib/nav";

/** The seven sections the MkDocs `nav:` block was transcribed into. */
const SECTION_TITLES = ["Home", "Learn", "Get started", "Studio", "Operate", "Reference", "Contribute"];

/**
 * Content loader standing in for `lib/source.ts`.
 *
 * `buildPageTree` resolves each nav leaf against `getPages()` and copies its `url`, so the
 * stub has to answer for every path the tree names - the authored `lib/nav.json` leaves plus
 * the generated Cinema / Audio / workflow pages `injectGenerated` merges in. URLs follow
 * `keepAuthorSlugs`: extension gone, an `index` page addressed by its directory.
 */
function fakeSource(): NavSource {
  const paths = new Set<string>();
  const walk = (nodes: NavNode[]): void => {
    for (const node of nodes) {
      if ("pages" in node) walk(node.pages);
      else paths.add(node.path);
    }
  };
  for (const tab of injectGenerated(navData as NavTab[])) walk(tab.pages);

  const pages = [...paths].map((path) => {
    const stem = stripExtension(path);
    const slug = stem.endsWith("/index") ? stem.slice(0, -"/index".length) : stem;
    return { path: stem, url: slug === "" ? "/" : `/${slug}` };
  });

  return {
    getPages: () => pages as unknown as ReturnType<NavSource["getPages"]>
  };
}

/** A folder as it appears in the built tree, with how far below the root it sits. */
interface BuiltFolder {
  name: string;
  depth: number;
  root?: boolean | string;
  defaultOpen?: boolean;
}

/** Every folder in the tree, outermost first. */
function folders(node: { children?: unknown[] }): BuiltFolder[] {
  const out: BuiltFolder[] = [];
  const walk = (children: unknown[], depth: number): void => {
    for (const child of children) {
      const entry = child as BuiltFolder & { type: string; children?: unknown[] };
      if (entry.type === "folder") {
        out.push({ name: entry.name, depth, root: entry.root, defaultOpen: entry.defaultOpen });
        walk(entry.children ?? [], depth + 1);
      }
    }
  };
  walk(node.children ?? [], 1);
  return out;
}

/** Every page leaf in the tree, as `{ ref, url }`. */
function leaves(node: { children?: unknown[] }): { ref?: string; url: string }[] {
  const out: { ref?: string; url: string }[] = [];
  const walk = (children: unknown[]): void => {
    for (const child of children) {
      const entry = child as { type: string; $ref?: string; url: string; children?: unknown[] };
      if (entry.type === "page") out.push({ ref: entry.$ref, url: entry.url });
      else if (entry.type === "folder") walk(entry.children ?? []);
    }
  };
  walk(node.children ?? []);
  return out;
}

const tree = buildPageTree(fakeSource());

/** The top-level section folders, narrowed from the tree's mixed children. */
function sections(): Folder[] {
  return tree.children.filter((child): child is Folder => child.type === "folder");
}

describe("docs navigation tree", () => {
  it("files every section as a top-level folder in one tree", () => {
    expect(tree.type).toBe("root");
    expect(tree.children.map((child) => child.name)).toEqual(SECTION_TITLES);
    const top = sections();
    expect(top).toHaveLength(SECTION_TITLES.length);
    for (const section of top) {
      expect(section.children.length, `section "${section.name}" should not be empty`).toBeGreaterThan(0);
    }
  });

  it("has no root folder, so the sidebar renders no tabs dropdown selector", () => {
    // getLayoutTabs() only collects folders whose `root` is set; an empty tab list is what
    // keeps SidebarTabsDropdown out of both the sidebar header and the mobile drawer.
    const rooted = folders(tree).filter((folder) => Boolean(folder.root));
    expect(rooted.map((folder) => folder.name)).toEqual([]);
  });

  it("opens every section so the menu can be read at a glance", () => {
    for (const section of sections()) {
      expect(section.defaultOpen, `section "${section.name}" should be open by default`).toBe(true);
    }
  });

  it("keeps the groups inside a section collapsed", () => {
    for (const group of folders(tree).filter((folder) => folder.depth > 1)) {
      expect(group.defaultOpen, `group "${group.name}" should start collapsed`).toBe(false);
    }
  });

  it("files every authored nav page exactly once", () => {
    const wanted: string[] = [];
    const walk = (nodes: NavNode[]): void => {
      for (const node of nodes) {
        if ("pages" in node) walk(node.pages);
        else wanted.push(stripExtension(node.path));
      }
    };
    for (const tab of navData as NavTab[]) walk(tab.pages);

    const refs = leaves(tree).map((leaf) => stripExtension(leaf.ref ?? ""));
    for (const path of wanted) {
      expect(refs.filter((ref) => ref === path), `${path} should appear once in the menu`).toHaveLength(1);
    }
  });
});

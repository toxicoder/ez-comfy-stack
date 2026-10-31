/**
 * Sidebar and tab structure, hand-maintained in `lib/nav.json`.
 *
 * The site inherited its seven tabs from the old MkDocs `nav:` block, and
 * `scripts/gen_nav.py` transcribed that block into `lib/nav.json`. `mkdocs.yml` is long
 * gone, so `lib/nav.json` is now the single source of truth: edit it by hand and verify
 * with `npm run nav:check`. The top-level tab titles are pinned by
 * `docs/test_docs_site_render.py`, and every page under `docs/` has to appear in the tree
 * exactly once (`tests/python/test_docs_nav_coverage.py` fails an orphan or a stale entry).
 *
 * Inside a tab, pages are grouped into collapsible folders that read as a progression:
 * Learn runs concept to concept, Operate runs everyday loop to troubleshooting, and so on.
 * A group is `{ title, pages }` with no `path`; its leaves keep their order and nest to
 * any depth. Keep each folder short enough to scan in one glance - a flat list of twenty
 * siblings tells a reader nothing about where they are.
 *
 * Generated Cinema / Audio / workflow children are merged in here at build time from the
 * generator manifests, so adding a lab graph does not require a hand-edit of nav.json.
 * The injection matches leaf titles, so the "Cinema Rack", "Audio Rack", and
 * "Workflow details" entries in nav.json keep those exact titles.
 */

import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import type { Folder, Item, Node, Root } from "fumadocs-core/page-tree";
import type { ReactNode } from "react";
import type { LoaderOutput } from "fumadocs-core/source";

import navData from "./nav.json";

/**
 * The slice of the content loader the navigation needs.
 *
 * Declared structurally (rather than as a bare `LoaderOutput`) so the loader instance built
 * in `lib/source.ts` - whose page type is the specialised one from the collection schemas -
 * is accepted without a variance complaint.
 */
export type NavSource = Pick<LoaderOutput, "getPages">;

/** One leaf of the transcribed navigation. */
export interface NavPage {
  /** Label shown in the sidebar, exactly as MkDocs rendered it. */
  title: string;
  /** Path of the page relative to `docs/`, e.g. `operate/mcp.md`. */
  path: string;
}

/** A nested sidebar folder (Cinema Rack, a workflow lane, ...). */
export interface NavGroup {
  title: string;
  pages: NavNode[];
}

export type NavNode = NavPage | NavGroup;

/** One top-level tab of the transcribed navigation. */
export interface NavTab {
  title: string;
  pages: NavNode[];
}

function isGroup(node: NavNode): node is NavGroup {
  return Array.isArray((node as NavGroup).pages) && !("path" in node && typeof (node as NavPage).path === "string");
}

function isPage(node: NavNode): node is NavPage {
  return typeof (node as NavPage).path === "string";
}

const STATIC_NAV = navData as NavTab[];

interface ManifestPage {
  id?: string;
  path?: string;
  kind?: string;
  label?: string;
  lane?: string;
}

function findRepoFile(segments: string[]): string | undefined {
  const here = dirname(fileURLToPath(import.meta.url));
  for (const root of [process.cwd(), here]) {
    let dir = root;
    for (let depth = 0; depth < 7; depth += 1) {
      const candidate = resolve(dir, ...segments);
      if (existsSync(candidate)) return candidate;
      const parent = dirname(dir);
      if (parent === dir) break;
      dir = parent;
    }
  }
  return undefined;
}

function loadManifest(kind: "workflows" | "cinema" | "audio"): ManifestPage[] {
  const file = findRepoFile(["docs", "generated", kind, "manifest.json"]);
  if (!file) return [];
  try {
    const payload = JSON.parse(readFileSync(file, "utf8")) as { pages?: ManifestPage[] };
    return Array.isArray(payload.pages) ? payload.pages : [];
  } catch {
    return [];
  }
}

const WORKFLOW_LANE_ORDER = [
  "stills",
  "motion",
  "creator",
  "services",
  "films",
  "dcc",
  "optional",
  "inspire",
  "audio",
  "klein",
  "wan",
  "ltx",
  "shorts",
  "audio-albums"
];

function cinemaChildren(): NavNode[] {
  const pages = loadManifest("cinema");
  const children: NavNode[] = [
    { title: "Playbook", path: "create/cinema-rack.md" },
    { title: "All axes", path: "generated/cinema/index.md" }
  ];
  for (const page of pages) {
    if (page.kind === "index" || !page.path) continue;
    children.push({ title: String(page.label || page.id || "axis"), path: page.path });
  }
  return children;
}

function audioChildren(): NavNode[] {
  const pages = loadManifest("audio");
  const children: NavNode[] = [
    { title: "Playbook", path: "create/audio-rack.md" },
    { title: "All axes", path: "generated/audio/index.md" }
  ];
  for (const page of pages) {
    if (page.kind === "index" || !page.path) continue;
    children.push({ title: String(page.label || page.id || "axis"), path: page.path });
  }
  return children;
}

function workflowChildren(): NavNode[] {
  const pages = loadManifest("workflows");
  // Only generated pages belong here. `reference/workflow-nodes.md` is listed in
  // `nav.json` beside this folder, so repeating it would put the same page in the sidebar
  // twice under one heading.
  const children: NavNode[] = [
    { title: "Overview", path: "create/workflows-index.md" },
    { title: "All graphs", path: "generated/workflows/index.md" }
  ];
  const byLane = new Map<string, ManifestPage[]>();
  for (const page of pages) {
    if (page.kind === "index" || !page.path) continue;
    const lane = page.lane || "other";
    const list = byLane.get(lane) ?? [];
    list.push(page);
    byLane.set(lane, list);
  }
  const seen = WORKFLOW_LANE_ORDER.filter((lane) => byLane.has(lane));
  for (const lane of [...byLane.keys()].sort()) {
    if (!seen.includes(lane)) seen.push(lane);
  }
  for (const lane of seen) {
    const items = byLane.get(lane) ?? [];
    children.push({
      title: lane,
      pages: items.map((page) => ({
        title: String(page.id || page.path || "graph").split("/").pop() ?? "graph",
        path: String(page.path)
      }))
    });
  }
  return children;
}

/**
 * Expand Cinema Rack / Audio Rack / Workflow details leaves into nested folders using
 * the generator manifests. Other nodes are copied as-is. The Workflow details leaf names
 * the authored catalog page, so the folder it expands to is titled "Graphs by lane" -
 * otherwise the sidebar and the breadcrumb would print that page's name twice.
 */
export function injectGenerated(tabs: NavTab[]): NavTab[] {
  const walk = (nodes: NavNode[]): NavNode[] =>
    nodes.map((node) => {
      if (isPage(node) && node.title === "Cinema Rack") {
        return { title: "Cinema Rack", pages: cinemaChildren() };
      }
      if (isPage(node) && node.title === "Audio Rack") {
        return { title: "Audio Rack", pages: audioChildren() };
      }
      if (isPage(node) && node.title === "Workflow details") {
        return { title: "Graphs by lane", pages: workflowChildren() };
      }
      if (isGroup(node)) {
        if (node.title === "Cinema Rack") return { title: node.title, pages: cinemaChildren() };
        if (node.title === "Audio Rack") return { title: node.title, pages: audioChildren() };
        if (node.title === "Workflow details") return { title: "Graphs by lane", pages: workflowChildren() };
        return { title: node.title, pages: walk(node.pages) };
      }
      return node;
    });
  return tabs.map((tab) => ({ title: tab.title, pages: walk(tab.pages) }));
}

/** Drop the directory suffix so `foo.md` and `foo.mdx` compare equal. */
export function stripExtension(path: string): string {
  return path.replace(/\.(?:md|mdx)$/u, "");
}

function toItem(source: NavSource, tabTitle: string, path: string, title: string): Item {
  const page = source.getPages().find((candidate) => stripExtension(candidate.path) === stripExtension(path));
  if (!page) {
    throw new Error(
      `navigation references a page that is not in the content source: ${path} (tab "${tabTitle}")`
    );
  }
  return { $id: `page:${path}`, type: "page", name: title, url: page.url, $ref: page.path };
}

function toNodes(source: NavSource, tabTitle: string, nodes: NavNode[], idPrefix: string): Node[] {
  return nodes.map((node, index) => {
    if (isGroup(node)) {
      const children = toNodes(source, tabTitle, node.pages, `${idPrefix}/${index}`);
      const folder: Folder = {
        $id: `folder:${idPrefix}/${index}:${node.title}`,
        type: "folder",
        name: node.title,
        defaultOpen: false,
        children
      };
      const first = node.pages[0];
      if (first && isPage(first) && /(^|\/)index$/.test(stripExtension(first.path))) {
        folder.index = toItem(source, tabTitle, first.path, first.title);
      }
      return folder;
    }
    return toItem(source, tabTitle, node.path, node.title);
  });
}

/**
 * Build the page tree the docs layout renders.
 *
 * Every tab becomes a root folder, which is what makes it appear in the tab strip while the
 * sidebar shows only the pages of the tab the reader is currently in - the behaviour the
 * Material theme produced with `navigation.tabs`.
 */
export function buildPageTree(source: NavSource): Root {
  const nav = injectGenerated(STATIC_NAV);
  const children: Node[] = nav.map((tab, index) => {
    const pages = toNodes(source, tab.title, tab.pages, `tab:${index}`);
    const folder: Folder = {
      $id: `tab:${index}:${tab.title}`,
      type: "folder",
      name: tab.title,
      root: true,
      defaultOpen: true,
      children: pages
    };
    const first = tab.pages[0];
    if (first && isPage(first) && /(^|\/)index$/.test(stripExtension(first.path))) {
      folder.index = toItem(source, tab.title, first.path, first.title);
    }
    return folder;
  });

  return { $id: "root", type: "root", name: "Documentation", children };
}

function flattenPages(nodes: NavNode[]): NavPage[] {
  const out: NavPage[] = [];
  for (const node of nodes) {
    if (isPage(node)) out.push(node);
    else out.push(...flattenPages(node.pages));
  }
  return out;
}

/** Paths of every page in the static navigation (no generated injection), in tab order. */
export const NAVIGATED_PATHS: string[] = STATIC_NAV.flatMap((tab) => flattenPages(tab.pages).map((page) => page.path));

/**
 * Previous and next pages in reading order, after generated children are merged.
 */
export function neighborsOf(
  source: NavSource,
  path: string
): { previous?: PageNodeEntry; next?: PageNodeEntry } {
  const wanted = stripExtension(path);
  const nav = injectGenerated(STATIC_NAV);
  const flat = nav.flatMap((tab) => flattenPages(tab.pages).map((page) => ({ tab: tab.title, page })));
  const index = flat.findIndex((entry) => stripExtension(entry.page.path) === wanted);
  if (index === -1) return {};
  const at = (offset: number): PageNodeEntry | undefined => {
    const entry = flat[index + offset];
    if (!entry) return undefined;
    const item = toItem(source, entry.tab, entry.page.path, entry.page.title);
    return { name: item.name, url: item.url };
  };
  return { previous: at(-1), next: at(1) };
}

/** A prev/next footer entry shaped the way the footer slot expects. */
export interface PageNodeEntry {
  name: ReactNode;
  url: string;
}

/** Where a page sits in the sidebar: its tab, then each collapsible folder above it. */
export interface NavTrail {
  /** Title of the tab the page is filed under. */
  tab: string;
  /** Folder titles between the tab and the page, outermost first. */
  groups: string[];
  /** Label the sidebar shows for the page, so the trail and the sidebar agree. */
  label: string;
}

/**
 * Sidebar location of one page, for the breadcrumb above the title.
 *
 * fumadocs resets the trail at a `root: true` folder, which is exactly what a tab is, so
 * its own breadcrumb cannot name the tab. This walks the same tree the sidebar renders.
 *
 * Arguments: path - page path relative to `docs/`, with or without its extension.
 * Returns: the tab, folder titles, and sidebar label, or undefined when the page is not
 * filed in the tree.
 */
export function trailFor(path: string): NavTrail | undefined {
  const wanted = stripExtension(path);
  const walk = (nodes: NavNode[], groups: string[]): NavTrail | undefined => {
    for (const node of nodes) {
      if (isPage(node)) {
        if (stripExtension(node.path) === wanted) return { tab: "", groups, label: node.title };
        continue;
      }
      const found = walk(node.pages, [...groups, node.title]);
      if (found) return found;
    }
    return undefined;
  };
  for (const tab of injectGenerated(STATIC_NAV)) {
    const found = walk(tab.pages, []);
    if (found) return { tab: tab.title, groups: found.groups, label: found.label };
  }
  return undefined;
}

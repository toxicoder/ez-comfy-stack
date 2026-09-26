/**
 * Sidebar and tab structure, transcribed from the information architecture the site shipped
 * with before the migration.
 *
 * MkDocs declared the whole navigation in `mkdocs.yml` under `nav:`; `scripts/gen_nav.py`
 * transcribed it into `lib/nav.json`. Generated cinema / audio / workflow children are
 * merged here at build time from the generator manifests - the same job `docs/hooks.py`
 * used to do - so adding a lab graph does not require a hand-edit of nav.json.
 *
 * Nested groups stay nested: Cinema Rack, Audio Rack, and Workflow details are folders
 * inside their tab, not a flattened list of hundreds of siblings.
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
  const children: NavNode[] = [
    { title: "Overview", path: "create/workflows-index.md" },
    { title: "All graphs", path: "generated/workflows/index.md" },
    { title: "Node parameter encyclopedia", path: "reference/workflow-nodes.md" }
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
 * the generator manifests. Other nodes are copied as-is.
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
        return { title: "Workflow details", pages: workflowChildren() };
      }
      if (isGroup(node)) {
        if (node.title === "Cinema Rack") return { title: node.title, pages: cinemaChildren() };
        if (node.title === "Audio Rack") return { title: node.title, pages: audioChildren() };
        if (node.title === "Workflow details") return { title: node.title, pages: workflowChildren() };
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

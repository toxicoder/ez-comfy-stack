/**
 * Slim the Fumadocs structured-data payload before Orama indexes it.
 *
 * Advanced search inserts one document per heading and per content block
 * (`tableCell` is a default block type). Generated workflow/cinema/audio
 * encyclopedias are mostly tables, so the static `/api/search` export was
 * 379 MiB / 408k documents — over GitHub's 100 MiB blob limit, and too
 * large to fetch in the browser anyway.
 */

export interface SearchHeading {
  id: string;
  content: string;
}

export interface SearchContent {
  heading: string | undefined;
  content: string;
}

export interface SearchStructuredData {
  headings: SearchHeading[];
  contents: SearchContent[];
}

/** Headings kept per page (title/description/tags are always indexed). */
export const SEARCH_HEADINGS_MAX = 80;

/** Body blocks kept on authored pages. Generated pages keep none. */
export const SEARCH_AUTHORED_CONTENTS_MAX = 80;

/**
 * True when full-text indexing would explode the static search export.
 *
 * Generated encyclopedias and the workflow-nodes dump are table-heavy.
 *
 * @param path Page path relative to `docs/` (`generated/workflows/…`).
 * @returns Whether to drop body blocks from the search index.
 */
export function isHeavySearchPath(path: string): boolean {
  const normalized = path.replaceAll("\\", "/");
  return (
    /(^|\/)generated(\/|$)/.test(normalized) ||
    /(^|\/)reference\/workflow-nodes\.mdx?$/.test(normalized)
  );
}

/**
 * Cap headings and drop or trim body blocks for the Orama export.
 *
 * @param path Page path relative to `docs/`.
 * @param structured Fumadocs `structuredData` for the page.
 * @returns A smaller payload safe to insert into the static index.
 */
export function slimSearchStructuredData(
  path: string,
  structured: SearchStructuredData
): SearchStructuredData {
  const headings = structured.headings.slice(0, SEARCH_HEADINGS_MAX);
  if (isHeavySearchPath(path)) {
    return { headings, contents: [] };
  }
  return {
    headings,
    contents: structured.contents.slice(0, SEARCH_AUTHORED_CONTENTS_MAX)
  };
}

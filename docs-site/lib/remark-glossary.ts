/**
 * First-occurrence glossary wraps from `includes/glossary.json`.
 *
 * Ports `docs/glossary.py` wrap rules: unique aliases, skip code / headings / links,
 * skip the glossary page itself, first hit per term id per page. The trigger is an
 * `<EzTerm>` MDX element so the client dialog can open on click.
 */

import { visit } from "unist-util-visit";

import glossaryJson from "../../includes/glossary.json";

export interface GlossaryTerm {
  id: string;
  title: string;
  aliases: string[];
  category: string;
  short: string;
  long?: string;
}

const SKIPPED_PARENTS = new Set(["link", "heading", "inlineCode", "code", "abbr", "mdxJsxTextElement", "mdxJsxFlowElement"]);

export function loadGlossaryTerms(): GlossaryTerm[] {
  const raw = glossaryJson as GlossaryTerm[];
  return Array.isArray(raw)
    ? raw.filter((term) => term && typeof term.id === "string" && Array.isArray(term.aliases))
    : [];
}

const REGEX_METACHARACTERS = new Set([".", "*", "+", "?", "^", "$", "{", "}", "(", ")", "|", "[", "]"]);

function escapeRe(term: string): string {
  return [...term].map((char) => (REGEX_METACHARACTERS.has(char) ? `\\${char}` : char)).join("");
}

function isGlossaryPage(filePath: string | undefined): boolean {
  if (!filePath) return false;
  return /(^|\/)glossary\.(md|mdx)$/u.test(filePath.replace(/\\/g, "/"));
}

/**
 * Wrap the first occurrence of each glossary term on a page.
 *
 * @returns A remark transformer.
 */
export function remarkGlossaryTooltips() {
  return (tree: Parameters<typeof visit>[0], file?: { path?: string; history?: string[] }) => {
    const filePath = file?.path ?? file?.history?.[0];
    if (isGlossaryPage(filePath)) return;

    const terms = loadGlossaryTerms();
    if (terms.length === 0) return;

    const lookup = new Map<string, GlossaryTerm>();
    const aliases: string[] = [];
    for (const term of terms) {
      for (const alias of term.aliases) {
        lookup.set(alias.toLowerCase(), term);
        aliases.push(alias);
      }
    }
    aliases.sort((a, b) => b.length - a.length || a.localeCompare(b));
    if (aliases.length === 0) return;
    const matcher = new RegExp(`(?<![A-Za-z0-9_])(${aliases.map(escapeRe).join("|")})(?![A-Za-z0-9_])`, "gi");
    const seen = new Set<string>();

    visit(tree, "text", (node, index, rawParent) => {
      const parent = rawParent as { type: string; children: unknown[] } | undefined;
      if (!parent || typeof index !== "number") return;
      if (SKIPPED_PARENTS.has(parent.type)) return;

      const text = String((node as { value?: string }).value ?? "");
      if (text.length === 0) return;
      matcher.lastIndex = 0;
      if (!matcher.test(text)) {
        matcher.lastIndex = 0;
        return;
      }
      matcher.lastIndex = 0;

      const children: unknown[] = [];
      let cursor = 0;
      for (const match of text.matchAll(matcher)) {
        const found = match[0];
        const term = lookup.get(found.toLowerCase());
        if (!term || seen.has(term.id) || match.index === undefined) continue;
        seen.add(term.id);
        if (match.index > cursor) children.push({ type: "text", value: text.slice(cursor, match.index) });
        children.push({
          type: "mdxJsxTextElement",
          name: "EzTerm",
          attributes: [
            { type: "mdxJsxAttribute", name: "termId", value: term.id },
            { type: "mdxJsxAttribute", name: "category", value: term.category },
            { type: "mdxJsxAttribute", name: "short", value: term.short }
          ],
          children: [{ type: "text", value: found }],
          data: { _mdxExplicitJsx: true }
        });
        cursor = match.index + found.length;
      }
      if (children.length === 0) return;
      if (cursor < text.length) children.push({ type: "text", value: text.slice(cursor) });
      parent.children.splice(index, 1, ...children);
    });
  };
}

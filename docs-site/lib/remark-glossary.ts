/**
 * First-occurrence glossary wraps from `includes/glossary.json`.
 *
 * Ports `docs/glossary.py` wrap rules: unique aliases, skip code / headings / links,
 * skip the glossary page itself, first hit per term id per page. The trigger is an
 * `<EzTerm>` MDX element so the client dialog can open on click.
 */

import { visit } from "unist-util-visit";
import { z } from "zod";

import glossaryJson from "../../includes/glossary.json";

/**
 * One glossary entry, as authored in `includes/glossary.json`.
 *
 * The shape mirrors the `Term` record in `docs/glossary.py`, which validates the same file
 * and raises on a bad entry, so both halves of the site fail on the same defect instead of
 * the MDX side silently dropping the term.
 */
export const glossaryTermSchema = z.object({
  id: z.string(),
  title: z.string(),
  aliases: z.array(z.string()),
  category: z.string(),
  short: z.string(),
  long: z.string().optional(),
  see_also: z.array(z.string()).optional()
});

export type GlossaryTerm = z.infer<typeof glossaryTermSchema>;

/** The whole `includes/glossary.json` payload. */
export const glossaryTermsSchema = z.array(glossaryTermSchema);

export function loadGlossaryTerms(): GlossaryTerm[] {
  return glossaryTermsSchema.parse(glossaryJson);
}

/** Node types whose text must not be wrapped (code, headings, links, ...). */
const SKIPPED_PARENTS = new Set(["link", "heading", "inlineCode", "code", "abbr", "mdxJsxTextElement", "mdxJsxFlowElement"]);

/**
 * The mdast fields this plugin reads.
 *
 * `remark` hands the transformer an untyped tree, so each read goes through one of the
 * guards below instead of an asserted node shape: a node that does not match is skipped.
 */
interface ParentNodeLike {
  type: string;
  children: unknown[];
}

/** The `file` argument remark passes, narrowed to the two path sources it uses. */
interface RemarkFile {
  path?: string;
  history?: string[];
}

/** A node with the two fields a parent must have, or nothing when it is not a parent. */
function asParent(value: unknown): ParentNodeLike | undefined {
  if (typeof value !== "object" || value === null) return undefined;
  const candidate = value as { type?: unknown; children?: unknown };
  if (typeof candidate.type !== "string" || !Array.isArray(candidate.children)) return undefined;
  return { type: candidate.type, children: candidate.children };
}

/** The `value` of a text node, or the empty string when the node carries none. */
function textValue(node: unknown): string {
  if (typeof node !== "object" || node === null) return "";
  const value = (node as { value?: unknown }).value;
  return typeof value === "string" ? value : "";
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
export function remarkGlossaryTooltips(): (tree: Parameters<typeof visit>[0], file?: RemarkFile) => void {
  return (tree, file) => {
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
      const parent = asParent(rawParent);
      if (!parent || typeof index !== "number") return;
      if (SKIPPED_PARENTS.has(parent.type)) return;

      const text = textValue(node);
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

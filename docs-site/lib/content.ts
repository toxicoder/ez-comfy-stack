/**
 * Frontmatter schemas for authored and generated documentation pages.
 *
 * The Fumadocs collection itself lives in `source.config.ts` (`dynamic: true`) so webpack
 * does not compile every markdown file during `next build`. These schemas stay here so
 * `source.config.ts` can import them without duplicating Zod shapes.
 */

import { z } from "zod";
import { pageSchema } from "fumadocs-core/source/schema";

/**
 * Frontmatter of a hand-written page.
 *
 * `pageSchema` strips unknown keys, so `tags` has to be declared here or the contributor
 * tags that MkDocs search indexed would silently disappear from the new search index.
 */
export const docSchema = pageSchema.extend({
  tags: z.union([z.string(), z.array(z.string())]).optional()
});

/**
 * Frontmatter of a generated page.
 *
 * Generators always emit title/description/tags today, but title cannot be required in
 * case a future generated tree omits it; the page renderer falls back to the first heading.
 */
export const generatedSchema = pageSchema.extend({
  title: z.string().optional(),
  tags: z.union([z.string(), z.array(z.string())]).optional()
});

/**
 * Content source for the documentation site.
 *
 * Point the Fumadocs MDX source at the repository's existing `docs/` tree so the shell,
 * workflow, cinema, and audio generators keep writing into `docs/generated/**` and
 * contributors keep editing markdown where they always have. Nothing is copied into this
 * package.
 */

import { z } from "zod";
import { defineDocs } from "fumadocs-mdx/macro";
import { metaSchema, pageSchema } from "fumadocs-core/source/schema";

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

/**
 * Mirrors files that are not pages: Material JS/CSS, Python, Bazel, and the includes
 * tree (command-builder + glossary JSON live at repo `includes/`, not under `docs/`).
 *
 * Both extensions are listed: pages that needed MkDocs syntax rewritten to JSX were renamed
 * to `.mdx` by `scripts/codemod_mkdocs_to_mdx.py` (the MDX compiler drops literal JSX in
 * `.md`), while the rest of the corpus — including everything under `generated/` — stays `.md`.
 *
 * The list has to stay inline string literals: the bundler macro reads it statically to
 * decide which files to bundle, and rejects anything computed.
 */
export const docs = defineDocs({
  dir: "../docs",
  docs: {
    files: ["**/*.md", "**/*.mdx", "!javascripts/**", "!stylesheets/**", "!**/*.json"],
    schema({ path }) {
      return /(^|\/)generated(\/|$)/.test(path.replace(/\\/g, "/")) ? generatedSchema : docSchema;
    }
  },
  meta: {
    // Generator manifests are JSON but not Fumadocs folder meta.json files.
    files: [],
    schema: metaSchema
  }
});

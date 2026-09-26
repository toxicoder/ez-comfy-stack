/**
 * Fumadocs MDX collection + compiler configuration.
 *
 * The collection is `dynamic: true` so production webpack compiles the app shell only and
 * each page's MDX is compiled when `page.data.load()` runs during static generation.
 * Bundling ~850 markdown files through `fumadocs-mdx/macro` OOMs GitHub's 7 GB runner.
 *
 * `mdxOptions` here is merged into Fumadocs' built-in remark/rehype chain (the preset
 * appends these `remarkPlugins` after GFM, heading, image and code-tab handling). Do not
 * set collection-level `mdxOptions` - that replaces the preset, including `rehypeToc`.
 */

import { defineConfig, defineDocs } from "fumadocs-mdx/config";
import { remarkAdmonition, remarkMdxMermaid } from "fumadocs-core/mdx-plugins";
import { metaSchema } from "fumadocs-core/source/schema";

import { docSchema, generatedSchema } from "./lib/content";
import { remarkGitRef } from "./lib/remark-git-ref";
import { remarkGlossaryTooltips } from "./lib/remark-glossary";
import { remarkCinemaAssets } from "./lib/remark-media";
import { remarkPageBrief } from "./lib/remark-page-brief";

/**
 * Point the collection at the repository `docs/` tree so generators keep writing into
 * `docs/generated/**` and contributors keep editing markdown where they always have.
 *
 * Both extensions are listed: pages that needed MkDocs syntax rewritten to JSX were renamed
 * to `.mdx` by `scripts/codemod_mkdocs_to_mdx.py`, while the rest of the corpus - including
 * everything under `generated/` - stays `.md`.
 */
export const docs = defineDocs({
  dir: "../docs",
  docs: {
    dynamic: true,
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

export default defineConfig({
  mdxOptions: {
    remarkPlugins: [
      remarkAdmonition,
      remarkMdxMermaid,
      remarkGitRef,
      remarkCinemaAssets,
      remarkGlossaryTooltips,
      remarkPageBrief
    ]
  }
});

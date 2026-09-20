/**
 * Global MDX compiler configuration for the documentation site.
 *
 * `mdxOptions` here is merged into Fumadocs' built-in remark/rehype chain (the preset
 * appends these `remarkPlugins` after GFM, heading, image and code-tab handling), so the
 * MkDocs-era behaviours below are added without dropping anything the theme relies on —
 * notably `rehypeToc`, which produces the table of contents rendered by `DocsPage`.
 */

import { defineConfig } from "fumadocs-mdx/config";
import { remarkAdmonition, remarkMdxMermaid } from "fumadocs-core/mdx-plugins";

import { remarkGitRef } from "./lib/remark-git-ref";
import { remarkGlossaryTooltips } from "./lib/remark-glossary";
import { remarkCinemaAssets } from "./lib/remark-media";
import { remarkPageBrief } from "./lib/remark-page-brief";

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

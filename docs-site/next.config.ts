import path from "node:path";
import { fileURLToPath } from "node:url";

import { createMDX } from "fumadocs-mdx/next";
import type { NextConfig } from "next";

import { basePath as publishedBasePath } from "./lib/site";

/** Directory of this config file, i.e. the `docs-site/` package. */
const packageRoot = fileURLToPath(new URL(".", import.meta.url));

/**
 * Base path of the published site.
 *
 * The MkDocs deployment published two aliases under the repository's GitHub Pages root:
 * `/nvidia-dgx-spark-lab/latest/` and `/nvidia-dgx-spark-lab/development/`.  Each alias is
 * produced by its own export (`DOCS_ALIAS=latest|development`) so those URLs keep resolving
 * and asset hrefs are not host-root `/latest/_next/...` paths that 404 on project Pages.
 */
const basePath = publishedBasePath();

/**
 * Where the static export is written.
 *
 * Defaults to Next's `out`.  The Linux golden-capture container overrides this so its build
 * cannot replace the export the host's gates and browser checks were produced from; the two
 * builds are made by different toolchains and are not interchangeable.
 */
const distDir = process.env.NEXT_DIST_DIR || "out";

const withMDX = createMDX();

const nextConfig: NextConfig = {
  basePath: basePath === "/" ? "" : basePath,
  /** Static export: the site is published to GitHub Pages, so there is no Node server. */
  output: "export",
  distDir,
  /** Images are served from the same static export, so no optimisation loader is available. */
  images: { unoptimized: true },
  /**
   * Publish pages as `<slug>/index.html` rather than `<slug>.html`.
   *
   * The MkDocs site (Material's `use_directory_urls`) published every page at a directory
   * address, and the README, the badges and the published aliases all link to those
   * trailing-slash URLs.  Exporting flat files would turn each of those into a 404, so the
   * layout the old site had is kept.
   */
  trailingSlash: true,
  reactStrictMode: true,
  /**
   * GitHub-hosted runners are 7 GB. Next 16.3 Turbopack static generation
   * retains per-page memory across ~850 MDX pages and the runner is SIGKILL'd
   * (shutdown signal / exit 143). Webpack in-process (no build worker) plus
   * one export worker leave headroom when NODE_OPTIONS is 5120 and Bazel is
   * not resident during the compile.
   */
  experimental: {
    cpus: 1,
    staticGenerationMaxConcurrency: 1,
    webpackBuildWorker: false,
    webpackMemoryOptimizations: true
  },
  turbopack: {
    /**
     * Pin the bundler root to this package.
     *
     * The bundler infers the root by walking up looking for a lockfile, and a lockfile
     * belonging to something else can sit above the repository in a developer's home
     * directory.  It also cannot read content above the root it picks, and the pages live
     * in `docs/` next to this package — so the root is the repository itself.
     */
    root: path.resolve(packageRoot, "..")
  }
};

export default withMDX(nextConfig);

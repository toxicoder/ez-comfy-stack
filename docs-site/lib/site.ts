/**
 * Site-wide configuration for the documentation app.
 *
 * Values mirror what the retired `mkdocs.yml` declared so that links, edit URLs and the
 * repository button keep pointing at the same places they always did.
 */

/** Name of the project, used as the docs subtitle under the wordmark. */
export const SITE_NAME = "ez-comfy-stack";

/** Secondary brand voice shown in the wordmark. */
export const BRAND = "overeazy";

/** Repository URL, as declared by `repo_url` in `mkdocs.yml`. */
export const REPO_URL = "https://github.com/toxicoder/ez-comfy-stack";

/** Owner/repository, parsed from {@link REPO_URL} for building source links. */
export const REPO = { user: "toxicoder", repo: "ez-comfy-stack" } as const;

/** Operator-facing description, used as the root layout fallback. */
export const SITE_DESCRIPTION =
  "Simplified Visual Generative AI (ComfyUI US-safe local studio) for a single NVIDIA DGX Spark";

/**
 * Active docs version alias (`development`, `latest`, or empty).
 *
 * Prefers this repo's `EZ_DOCS_VERSION` / `MIKE_DOCS_VERSION`, then the spark-lab
 * `DGX_DOCS_VERSION` name so the same app works on either Overeazy docs site.
 */
export function docsVersion(): string {
  return (
    process.env.EZ_DOCS_VERSION ??
    process.env.MIKE_DOCS_VERSION ??
    process.env.DGX_DOCS_VERSION ??
    ""
  )
    .trim()
    .toLowerCase();
}

/**
 * Git ref that "Edit this page" and source links point at.
 *
 * Reproduces `docs/hooks.py`'s branch-aware `edit_uri`: the published docs are built per
 * alias (`latest` from `main`, `development` from `development`), and the ref has to match
 * the alias so an edit opens the file the reader is actually reading.
 */
export function gitRef(): string {
  const override = (process.env.EZ_DOCS_GIT_REF ?? process.env.DGX_DOCS_GIT_REF ?? "").trim();
  if (override) return override;
  if (docsVersion() === "development") return "development";
  return "main";
}

/** True when the current build is the development alias (drives the banner). */
export function isDevelopmentAlias(): boolean {
  return docsVersion() === "development";
}

/** Which published docs tree this build is, or `local` for `next dev`. */
export type DocsAlias = "latest" | "development" | "local";

/**
 * Alias label stamped into docs-bug reports.
 *
 * `development` builds set `EZ_DOCS_VERSION`. `latest` builds set `DOCS_ALIAS`
 * and leave the version empty. Anything else is a local preview.
 */
export function docsAlias(): DocsAlias {
  const version = docsVersion();
  if (version === "development" || version === "latest") return version;
  const alias = (process.env.DOCS_ALIAS ?? "").trim().toLowerCase();
  if (alias === "latest" || alias === "development") return alias;
  return "local";
}

/**
 * URL path of the static search index for a published base path.
 *
 * The Orama client otherwise fetches `/api/search` from the host root. On GitHub
 * project Pages that 404s; the file lives under `/<repo>/<alias>/api/search`.
 *
 * @param prefix Site base path (`""` locally). Defaults to {@link basePath}.
 * @returns Root-relative path the browser should fetch.
 */
export function searchIndexPath(prefix?: string): string {
  const base = (prefix ?? basePath()).trim().replace(/\/+$/, "");
  return `${base}/api/search`;
}

/**
 * Public base path of the deployed site, e.g. `/ez-comfy-stack/latest`.
 *
 * GitHub project Pages serves this repository at `/<repo>/`, so a published alias must
 * bake that prefix into every asset URL.  `DOCS_ALIAS=latest|development` is what the
 * alias build scripts set; `NEXT_BASE_PATH` remains an explicit override (`/` means none).
 * Local `next dev` and the unprefixed export leave both unset, so the path stays empty.
 */
export function basePath(): string {
  const explicit = (process.env.NEXT_BASE_PATH ?? "").trim();
  if (explicit === "/") return "";
  if (explicit.length > 0) return explicit.replace(/\/$/, "");
  const alias = (process.env.DOCS_ALIAS ?? "").trim();
  if (alias === "latest" || alias === "development") {
    return `/${REPO.repo}/${alias}`;
  }
  return "";
}

/** URL of a file in the repository at the active ref. */
export function repoFileUrl(path: string): string {
  return `${REPO_URL}/blob/${gitRef()}/${path.replace(/^\/+/, "")}`;
}

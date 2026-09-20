# Documentation site migration: MkDocs → Fumadocs

The documentation site moved from **Material for MkDocs** to **Fumadocs** (Next.js App Router).
The content did not move: pages still live in `docs/`, the generators still write
`docs/generated/`, and the contributor rules in `docs/project-conventions.md` still apply.

**What's on this page**

- What changed and what did not
- How to run the site locally
- How the published URLs stay stable
- Leftover MkDocs files that can go after the first green preview

**What this enables**

- Reviewing this change knowing which diffs are mechanical
- Reproducing the site build without a Python MkDocs toolchain
- Deleting leftover Material files once the GitHub Pages preview is green

## What changed

| Area | Before | After |
| --- | --- | --- |
| Renderer | `mkdocs` + Material theme | Fumadocs (`fumadocs-core`, `fumadocs-mdx`, `fumadocs-ui`) on Next.js 16, static export |
| App | none (theme + `mkdocs.yml`) | `docs-site/` (App Router, `output: "export"`) |
| Content | `docs/**/*.md` | unchanged location; pages that need JSX are `.mdx` |
| Navigation | `mkdocs.yml` `nav:` plus `docs/hooks.py` manifest inject | `docs-site/lib/nav.json` + `docs-site/lib/nav.ts` (workflow / cinema / audio children merged at build) |
| Search | Material search | Orama index at `/api/search`, searchable by title **and** `tags` |
| Publishing | `mike deploy` → `gh-pages` | two static exports (`/ez-comfy-stack/latest/`, `/ez-comfy-stack/development/`) → `gh-pages` (with `.nojekyll`) |
| Version banner | `docs/hooks.py` | `EZ_DOCS_VERSION` / `DGX_DOCS_VERSION` read by `docs-site/lib/site.ts` |
| Edit-on-GitHub | `hooks.py` `on_config` | same behaviour, branch-aware, in `docs-site/lib/site.ts` |
| Theme | Material indigo | Overeazy Voltage `--color-fd-*` in `docs-site/app/global.css` |

### Syntax mapping (mechanical, not editorial)

No operator prose was rewritten. The codemod (`docs-site/scripts/codemod_mkdocs_to_mdx.py`, guarded by
`docs-site/test_codemod.py` which asserts the projected prose is byte-identical) maps:

| MkDocs | Fumadocs |
| --- | --- |
| `!!! note "Title"` / `warning` / `danger` / `tip` | `<Callout type="info\|warning\|error" title="…">` |
| `=== "Tab"` blocks | `<Tabs groupId="…" items={[…]}>` / `<Tab value="…">` |
| fenced `ezcmd` (`id: recipe`) | `<EzCommand id="…" />` |
| `<!-- ez-glossary:render -->` | `<GlossaryBody />` |

Generated pages under `docs/generated/` stay `.md` and may still use `!!! warning`.
`source.config.ts` registers `remarkAdmonition`, so those fences still build. Do not
hand-edit generated files — regenerate with `bazelisk run //docs:docs`.

Pages that gained none of the JSX forms keep the `.md` extension; the rest are `.mdx`.
Body text is otherwise untouched.

ez-comfy never used pymdownx snippets (`--8<--`), abbreviations.md, or `{{PLACEHOLDER}}`.
Session variables stay `${VAR}` / `${VAR:-default}` via `docs-site/lib/command-vars.ts`
and `localStorage` key `ez-comfy.cmdvars`.

## Running it locally

```bash
bazelisk run //docs:serve                       # dev server, hot reload, http://localhost:3005
bazelisk run //docs:docs                        # generators + static export → docs-site/out/
bazelisk run //docs:preview                     # export + serve it
bazelisk test //docs:test_docs_site_render //docs-site:unit //docs-site:typecheck
```

Without Bazel:

```bash
./docs/setup-docs.sh                             # npm ci --legacy-peer-deps
./docs/manage-docs.sh serve
./docs/manage-docs.sh build --version development
```

Inside `docs-site/` the same steps are npm scripts: `npm run dev`, `npm run build`,
`npm run unit`, `npm run nav:check`, `npm run verify`. `nav:generate` and `codemod`
remain for a repository that still has its `mkdocs.yml`.

Dependencies: Node 22+ (the devcontainer Node feature installs it; on a host
`brew install node@22`). Python is only needed by the generators and the pytest
gates — `docs/requirements.txt` no longer installs MkDocs.

## Stable URLs

The old site published `…/latest/` and `…/development/` through mike. Each alias is a Next
export with `basePath=/ez-comfy-stack/<alias>` baked into asset URLs
(`//docs-site:build-latest`, `//docs-site:build-development`). `.github/workflows/deploy-docs.yml`
builds **one** alias per run (`main` → `/latest/`, `development` → `/development/`) and keeps
the other directory from the current `gh-pages` tree — two full 650-page exports OOM the
GitHub-hosted runner. It writes a root `.nojekyll` (legacy GitHub Pages runs Jekyll, which
would otherwise drop `_next/`) and fast-forwards `gh-pages`. Every previously published URL
keeps resolving; a root `index.html` forwards bare `…/ez-comfy-stack/` traffic to `/latest/`.

The development alias renders a banner. The branch used by “Edit on GitHub” and in-page source
links comes from `EZ_DOCS_VERSION` (override locally with `EZ_DOCS_GIT_REF` or
`DGX_DOCS_GIT_REF`).

## Leftover MkDocs files

Still on disk so hermetic pytest can keep covering `docs/*.py` (100% gate) and the
Material-era JS contracts until the first green Pages preview:

| Path | Why it is still here |
| --- | --- |
| `mkdocs.yml` | `docs-site/scripts/gen_nav.py` can still transcribe nav while it exists; `nav.json` is the live source of truth |
| `docs/hooks.py` | Hermetic tests still load branch stamping, page-brief wrap, glossary, ezcmd, published chip |
| `docs/javascripts/*.js` | Source-string contracts in `test_docs_glossary.py` / leftover Material widgets |
| `docs/stylesheets/extra.css` | `test_docs_page_brief.py` still reads page-brief CSS comments here |

The live site does **not** load those files. Chrome, widgets, and search live in `docs-site/`.
After the first green `https://toxicoder.github.io/ez-comfy-stack/development/` preview,
delete the four rows above, retarget the remaining pytest paths at `docs-site/`, and drop
`mkdocs.yml` from `scripts/validate.sh` `path_matches_docs`.

If a stale checkout still has `site/`, `.venv-docs/`, or `.mkdocs-serve-*.yml`, they are
build artefacts and can be removed — they are gitignored.

## Gates, before and after

| Purpose | Was | Now |
| --- | --- | --- |
| Content contract of navigable pages | `//docs:test_mkdocs_render` | `//docs:test_docs_site_render` (in `//:test`) |
| Same checks against the export | (same target) | `bazelisk run //docs:render-check` after `//docs:docs` |
| Widget behaviour | Material extra JS | `//docs-site:unit` (Vitest), `//docs-site:typecheck` |
| Nav ↔ pages | `mkdocs.yml` vs disk | `docs-site/lib/nav.json` vs disk (`test_docs_nav_coverage.py`, `//docs-site:nav_test`) |
| Nav transcriber / codemod units | n/a | `//docs-site:nav_test`, `//docs-site:codemod_test` |
| Python coverage | generators + `hooks.py` | same `docs/*.py` modules (100% gate unchanged) |
| Public aliases | mike `latest` / `development` | two Next exports to the same URL prefixes |

No gate was dropped: each MkDocs-era target was retargeted onto the Next app, and the CI
`docs-and-render` job runs the same checks in the same order (fast gates, then export).
Playwright visual goldens exist as a manual `//docs-site:visual-linux` path; they are not
part of `docs-and-render` until a Linux baseline set is committed.

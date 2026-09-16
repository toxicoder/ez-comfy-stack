---
title: Docs style
description: Page template, ezcmd, glossary.json, page-brief hooks, session vars, inverted pyramid. AI-drafted docs still need a human pass.
tags: [docs, contributing, mkdocs, style]
---

# Docs style

**What's on this page**

- **Required page chrome** — frontmatter, H1, What's on this page, What this enables
- **ezcmd** — `id` must exist in `includes/command-builder.json`
- **glossary.json** — do not inline a second glossary
- **`docs/hooks.py` page-brief** and session vars
- **What not to do** — fork Material templates, MkDocs 2.x, `header.autohide`
- **Code appearance** — Roboto Mono, fenced line-height from nvidia-dgx-spark-lab, inline terminal green

**What this enables**

- **Matching** the scan card every operator page already uses
- **Keeping** MkDocs 1.x + Material pins
- **Matching** nvidia-dgx-spark-lab fenced line-height and inline terminal-green `code`
- **Remembering** that **AI-drafted docs still need a human pass**

Canonical conventions (shell, Docker, testing): [Project conventions](../project-conventions.md). Workflow: [Contributing](contributing.md).

```bash
export SPARK_HOST="${SPARK_HOST:-127.0.0.1}"
export SPARK_USER="${SPARK_USER:-$USER}"
export MODELS_DIR="${MODELS_DIR:-/mnt/models}"
export COMFY_OUTPUT_DIR="${COMFY_OUTPUT_DIR:-/mnt/comfy-output}"
export COMFY_PORT="${COMFY_PORT:-8188}"
export DOWNLOAD_LIMIT="${DOWNLOAD_LIMIT:-auto}"
```

!!! warning "Human review"

    **AI-drafted docs still need a human pass** before merge. Invented product features, TBD headings, real IPs, and secrets are defects.

---

## Page template

Every `docs/**/*.md` page (including `docs/learn/`):

1. YAML frontmatter: `title`, `description`, `tags`
2. H1 **matching** `title`
3. **What's on this page** — bullet list (bold first phrase)
4. **What this enables** — bullet list (bold first phrase)

Author those two lists as **bold + bullets** in source. `docs/hooks.py` `on_post_page` wraps the first pair after the page `h1` into `.ez-page-brief` via `docs/page_brief.py`. Titles stay `<p>`, not headings (they must not enter the TOC). Do not rewrite the pair as a fence, admonition, or card grid. Trailing `**Who this is for:**` stays outside the card.

**Inverted pyramid:** outcome and commands first; theory later. Prefer relative links inside `docs/`.

**Source spacing:** no trailing whitespace, at most one blank line between blocks, a single trailing newline, and a blank line around ATX headings and column-0 fences/tables/admonitions (`tests/python/test_docs_markdown.py`).

Safety callouts: `!!! danger` / `!!! warning` for occupancy XOR, `restart: "no"`, headroom, download-limit, licenses.

Operator git clone / blob refs: write `__DOCS_GIT_REF__` (hooks stamp `main` or `development` for the published alias). Contributor workflow text (“branch from `development`”) stays literal.

---

## ezcmd

Interactive command widgets:

````markdown
```ezcmd
id: doctor
```
````

The `id` **must** exist in `includes/command-builder.json`. `docs/hooks.py` expands the fence via `docs/commands.py`. Do **not** add `mkdocs-placeholder-plugin` (`xNAMEx` tokens fight bash `${VAR}`). Keep `docs/javascripts/commands.js` aligned with `substitute_vars` / `render_command`. `--tier` is a per-utility **pack id** ([Download tiers](../download-tiers.md)), not a global quality flag.

Unknown ids fail the hermetic command tests. Do not invent recipe ids in prose.

---

## Glossary

Source of truth: **`includes/glossary.json`** only (JSON, not YAML). Unique `id` (`[a-z0-9-]+`) and unique case-insensitive `aliases`. `short` is one line; `long` is markdown on [glossary.md](../glossary.md).

Do **not** inline a second glossary on a feature page. First occurrence per term per page; skip `code` / `pre` / headings / links / the glossary page itself.

Do **not** enable Material `abbr` + snippets `auto_append`. Do **not** enable `content.instant` unless you re-test the glossary modal, `commands.js`, **and** `tables.js`.

---

## Session variables

Operator fences **and** inline `code` reuse:

`SPARK_HOST`, `SPARK_USER`, `MODELS_DIR`, `COMFY_OUTPUT_DIR`, `COMFY_PORT`, `DOWNLOAD_LIMIT`

Defaults match `.env.example`. Do not hardcode `<spark-ip>` or real IPs. `docs/javascripts/commands.js` substitutes `${VAR}` / `${VAR:-default}` from `localStorage` (`ez-comfy.cmdvars`).

---

## Code appearance

Fenced blocks and inline `code` follow [nvidia-dgx-spark-lab](https://github.com/toxicoder/nvidia-dgx-spark-lab) (`docs/stylesheets/extra.css`, `theme.font.code: Roboto Mono`, `pymdownx.highlight` `line_spans` / `pygments_lang_class`):

- Fenced `pre > code`: `line-height: 1.55`, padding `0.9em 1.05em`, radius `0.25rem`. Pygments token colors stay.
- Prose / list / table `code`: terminal green `rgb(134, 183, 55)`. Do not apply that color to `pre > code`.
- Keep this site’s `.md-typeset { font-size: 0.875rem }`, sticky table pin (`.ez-table-pin`), and floating horizontal scrollbar (`.ez-table-hscroll` in `tables.js`). Do not copy spark-lab’s `0.82rem` typeset or table `overflow: hidden`. Do not `position: sticky` the header or the h-scroll bar.

---

## Material / MkDocs — do not

| Do not | Why |
| --- | --- |
| **Fork Material `header.html` / `tabs.html`** | Sticky tabs + compact-on-scroll live in `mkdocs.yml` features + `docs/stylesheets/extra.css` |
| **Upgrade MkDocs 2.x** | Stack is MkDocs **1.x** + Material (`docs/requirements.txt`). No migration path. `NO_MKDOCS_2_WARNING=1` in `make docs` / deploy |
| **Enable `header.autohide`** | Hides the tabs row on scroll without sticky |

Keep `navigation.tabs` **and** `navigation.tabs.sticky`. Testing the docs build: [Testing docs](testing-docs.md).

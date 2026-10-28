# ez_feedback

Shared bug-report / feature-request machinery for the whole stack. No canvas
nodes: `NODE_CLASS_MAPPINGS` is empty, `WEB_DIRECTORY` is `./js`, and the pack
is JS chrome plus two fail-soft HTTP routes.

Every surface (App, media explorer, media file, film board, watch, model check,
global) files through this pack so a report looks the same wherever it started.
Repo: `toxicoder/ez-comfy-stack`.

## Filing model

Filing is token-optional and degrades, never fails:

- `EZ_GITHUB_TOKEN` set -> the dialog's "File directly" button posts through
  `POST /ez_feedback/submit` and GitHub returns the issue URL.
- No token -> that button never appears and every action is a prefilled
  `https://github.com/toxicoder/ez-comfy-stack/issues/new?title=&body=&labels=`
  handoff the reporter can edit before submitting.

Nothing is submitted without a human pressing a button, and the token never
crosses the wire: `GET /ez_feedback/config` reports `tokenPresent` as a bool
only.

## Files

| File | Purpose |
| --- | --- |
| `context.py` | Canonical title, label, body, `MAX_HREF`, and env rules. Stdlib only; `env_snapshot` never raises and never imports torch (GPU facts arrive through the injected `probe`). |
| `routes.py` | `GET /ez_feedback/config`, `POST /ez_feedback/submit`. Outbound calls use `urllib.request` and accept `api.github.com` only. |
| `js/ez_feedback_core.js` | The shared exports and `window.EzFeedback`. Zero ComfyUI imports, hand-rolled dialog and dismissible banner. |
| `js/ez_feedback.js` | `ez.feedback.chrome`: two header buttons, graph prefill, error ring buffer. |
| `js/ez_feedback.css` | `.ez-fb-*` styles, dark-theme-safe, explicit z-index, focus-visible outlines. |

## Vocabulary (do not invent new values)

- `kind`: `bug` | `enhancement`. Labels: `bug`, `enhancement`, `documentation`
  (anything else is filtered out - GitHub drops labels that do not exist).
- `surface`: `global` | `app` | `media-explorer` | `media-file` | `film-board`
  | `watch` | `model-check`.
- Title: `[<area>] <summary>` clipped to 140. `<area>` is `app:<lab_rel>` for
  the App surface, the bare surface id otherwise, and no prefix for `global`.
- Body section order: `## What happened`, `## Steps`, `## Expected`,
  `## Actual`, `## Context`, `## Environment`, `## Recent errors`,
  `## Browser`. The first four carry `<!-- Replace this line. -->` and are
  always present for `bug`. A traceback, when present, is a fenced block after
  `## Browser`.
- Past `MAX_HREF` (5500) the URL drops whole sections, in this order:
  `## Browser`, then `## Recent errors`, then `## Environment`, then the
  traceback.

`custom_nodes/ez_feedback/context.py` is the canonical source; the JS mirrors
it and `tests/python/test_ez_feedback.py` pins the rules.

## Using it from another pack

```js
const fb = window.EzFeedback;
document.body.appendChild(fb.button({ kind: "bug", surface: "film-board" }, "Report a bug"));
fb.recordError({ ts: new Date().toISOString(), surface: "film-board", message: text });
fb.showBanner({ kind: "bug", surface: "film-board" }, { message: "Render failed" });
```

Reach the core lazily at click time (`window.EzFeedback`), never with a static
import, so extension load order cannot break the caller. `ez_feedback.js`
publishes `window.__ezFeedbackApi = app.api` so the core's two fetches honor
Comfy's api prefix; without it the core falls back to the bare paths and the
handoff button still works.

## Safety notes

- `recordError` keeps the newest five failures in a ring buffer; the banner is
  additive and dismissible and cannot block a queue.
- Errors are captured from `execution_error` / `execution_interrupted` in a
  `try`/`catch` that swallows everything: report chrome never breaks a run.
- `redact()` scrubs `ghp_`, `gho_`, `github_pat_`, and `hf_` token runs and the
  home directory before anything leaves the page or the process.

Tests: `tests/python/test_ez_feedback.py` (behaviour, 100% of this pack) and
`tests/python/test_ez_feedback_js.py` (structure of the JS and CSS).

# ez_feedback

Shared bug-report / feature-request machinery for the whole stack. No canvas
nodes: `NODE_CLASS_MAPPINGS` is empty, `WEB_DIRECTORY` is `./js`, and the pack
is JS chrome plus three fail-soft HTTP routes.

Every surface (App, media explorer, media file, film board, watch, model check,
load-error, global) files through this pack so a report looks the same wherever
it started, and the **Feedback** sidebar panel files the guided, typed report.
Repo: `toxicoder/ez-comfy-stack`.

## Filing model

Filing is token-optional and degrades, never fails:

- `EZ_GITHUB_TOKEN` set -> the dialog's "File directly" button posts through
  `POST /ez_feedback/submit` and GitHub returns the issue URL.
- No token -> that button never appears and every action is a prefilled
  `https://github.com/toxicoder/ez-comfy-stack/issues/new?title=&body=&labels=`
  handoff the reporter can edit before submitting.
- **File directly** posts the body from the dialog's editor (after `redact()`),
  not a rebuilt one, so what the reporter typed is what GitHub receives.
  `issueHrefFor()` reports whether the handoff URL had to be cut; when it was,
  the dialog copies the full markdown to the clipboard and says so.

Nothing is submitted without a human pressing a button, and the token never
crosses the wire: `GET /ez_feedback/config` reports `tokenPresent` as a bool
only.

## Files

| File | Purpose |
| --- | --- |
| `context.py` | Canonical title, label, body, `MAX_HREF`, and env rules. Stdlib only; `env_snapshot` never raises and never imports torch (GPU facts arrive through the injected `probe`). |
| `routes.py` | `GET /ez_feedback/config`, `POST /ez_feedback/submit`, `POST /ez_feedback/enhance`. Outbound calls use `urllib.request` and accept `api.github.com` only. |
| `js/ez_feedback_core.js` | The shared exports on `window.EzFeedback`: `REPO`, `MAX_HREF`, `clip`, `labelsFor`, `buildTitle`, `buildBody`, `issueHref`, `issueHrefFor`, `reportPayload`, `recordError`, `recentErrors`, `configure`, `getConfig`, `openHandoff`, `fileDirect`, `openReport`, `showBanner`, `dismissBanner`, `button`, `githubIcon`, `enhanceText`. Zero ComfyUI imports, hand-rolled dialog and dismissible banner. |
| `js/ez_feedback.js` | `ez.feedback.chrome`: two header buttons, graph prefill, error ring buffer, and the **Report this error** filer on the load-abort modal. |
| `js/ez_feedback_panel.js` | `ez.feedback.panel`: the Feedback sidebar tab (left dock, `pi pi-github`) - kind toggle, guided fields per kind, live title and markdown preview, attach-recent-errors and attach-environment checkboxes, Enhance with LLM, File on GitHub, Copy markdown. Registers only when the frontend offers `registerSidebarTab`. |
| `prompts/enhance_bug.txt`, `prompts/enhance_enhancement.txt` | System prompts for the Enhance with LLM rewrite, read once at import. |
| `js/ez_feedback.css` | `.ez-fb-*` and `.ez-fb-panel*` styles, dark-theme-safe, explicit z-index, focus-visible outlines. |

## Routes

| Route | Behaviour |
| --- | --- |
| `GET /ez_feedback/config` | `200 {repoUrl, tokenPresent, labels, env}`. `tokenPresent` is a bool; the token value never leaves the process. |
| `POST /ez_feedback/submit` | Redacts the body, clips it to `MAX_BODY`, posts it to `api.github.com` with the token as an `Authorization` header only. `200 {ok, url, number}`, `409` with no token, `400` for a non-GitHub host, `502`/`500` when GitHub is unreachable. |
| `POST /ez_feedback/enhance` | `{kind, text}` -> `200 {ok: true, text}`. Rewrites the guided fields through the local GGUF with `ez_prompt_enhance.client.complete` and the same `EZ_LLM_*` knobs as prompt enhancement; the system prompt is the matching `prompts/enhance_*.txt`. `400` empty or over `ENHANCE_INPUT_MAX`, `503` when the model or sidecar is unavailable, `502` on an unexpected raise. The output is redacted and clipped to `ENHANCE_OUTPUT_MAX`. Fail-soft either way: the panel shows the reason as a status line and files without it. |

## Vocabulary (do not invent new values)

- `kind`: `bug` | `enhancement`. Labels: `bug`, `enhancement`, `documentation`
  (anything else is filtered out - GitHub drops labels that do not exist).
- `surface`: `global` | `app` | `media-explorer` | `media-file` | `film-board`
  | `watch` | `model-check` | `load-error`. The Feedback panel files on `app`
  when a lab graph is open and `global` otherwise; `load-error` is the
  `Loading aborted due to error reloading workflow data` modal.
- Title: `[<area>] <summary>` clipped to 140. `<area>` is `app:<lab_rel>` for
  the App surface, the bare surface id otherwise, and no prefix for `global`.
- `narrative` (optional, the panel's guided fields, snake_case both sides):
  `bug` -> `what_happened`, `steps`, `expected`, `actual`; `enhancement` ->
  `problem`, `solution`, `alternatives`, `unlocks`, rendered by
  `ENHANCE_HEADINGS` as `## Problem`, `## Proposed solution`,
  `## Alternatives`, `## What it unlocks`. Values render as paragraph lines
  (split, ends stripped, redacted) and are never clipped. An empty `bug` value
  keeps the `FILL_IN` line; an empty `enhancement` value omits its heading.
- Body section order: `## What happened`, `## Steps`, `## Expected`,
  `## Actual`, `## Context`, `## Environment`, `## Recent errors`,
  `## Browser`. The first four carry `<!-- Replace this line. -->` and are
  always present for `bug`. A traceback, when present, is a fenced block after
  `## Browser`.
- Caps: `MAX_ERROR_TEXT` (2000) is the ring-buffer and error-line budget, so a
  long `exception_message` survives; `MAX_FIELD` (300) stays for single context
  and environment values.
- Past `MAX_HREF` (5500) the URL drops whole sections, in this order:
  `## Browser`, then `## Recent errors`, then `## Environment`, then the
  traceback.

`custom_nodes/ez_feedback/context.py` is the canonical source; the JS mirrors
it and `tests/python/test_ez_feedback.py` pins the rules.

## Using it from another pack

```js
const fb = window.EzFeedback;
const button = fb.button({ kind: "bug", surface: "film-board" }, "Report a bug");
document.body.appendChild(button);
fb.recordError({ ts: new Date().toISOString(), surface: "film-board", message: text });
fb.showBanner({ kind: "bug", surface: "film-board" }, { message: "Render failed" });

const { href, trimmed } = fb.issueHrefFor(payload, editedBody);
await fb.fileDirect(partial, editedBody);            // the edited body, verbatim
const { ok, text, error } = await fb.enhanceText({ kind: "bug", text: notes });
button.prepend(fb.githubIcon(), " ");                // <svg class="ez-fb-icon">, null without a document
```

Reach the core lazily at click time (`window.EzFeedback`), never with a static
import, so extension load order cannot break the caller. `ez_feedback.js`
publishes `window.__ezFeedbackApi = app.api` so the core's fetches honor Comfy's
api prefix; without it the core falls back to the bare paths and the handoff
button still works. It also publishes
`window.__ezFeedbackGraphContext = graphContext`, which the Feedback panel and
the `load-error` filer share so every report carries the same graph block.
`button()` renders the GitHub mark itself, so a caller does not paste its own
`<svg>`; use `githubIcon()` directly only for a hand-rolled control.

## Safety notes

- `recordError` keeps the newest five failures in a ring buffer; the banner is
  additive and dismissible and cannot block a queue.
- Errors are captured from `execution_error` / `execution_interrupted` in a
  `try`/`catch` that swallows everything: report chrome never breaks a run.
- `redact()` scrubs `ghp_`, `gho_`, `github_pat_`, and `hf_` token runs and the
  home directory before anything leaves the page or the process.
- The `load-error` filer wraps `app.loadGraphData` once, records the failure and
  the stack, and rethrows: the button never hides a load failure.
- `/ez_feedback/enhance` is advisory and stays on-box with the rest of the local
  LLM path. Missing GGUF, dead sidecar, or an unexpected raise answers with a
  reason the panel shows as a status line; the report still files.

Tests: `tests/python/test_ez_feedback.py` (behaviour, 100% of this pack),
`tests/python/test_ez_feedback_js.py` (structure of the JS and CSS), and
`tests/js/ez_feedback.test.mjs` (`node --test`: truncation, `issueHrefFor`,
`fileDirect`, `enhanceText`).

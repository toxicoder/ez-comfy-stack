---
title: Prompting Klein, Wan, and LTX
description: Model-native prompt recipes and lazy Prompt Enhance nodes for the US-safe ComfyUI studio.
tags: [prompting, klein, wan, ltx, comfyui]
---

# Prompting Klein, Wan, and LTX

**What's on this page**

- How each lab model actually reads a prompt
- Canned lab-example text (already rewritten)
- GIF loop motion and dream-house identity plate (Prompt Join)
- Lazy path: Prompt Enhance nodes + `XAI_API_KEY`

**What this enables**

- Writing (or pasting) a prompt that matches Klein 4B, Wan 2.2, or LTX-2.5 instead of SD1.5 tag soup
- Typing a lazy sentence and letting Grok rewrite it for the model on the canvas
- Queueing offline with Enhance off — no API key required

!!! tip "Lab graphs already ship model-native prompts"

    Seeded **\*-lab-example** graphs use research-backed Positive / Motion text. Leave **Enhance** off unless you replace that text with something short.

---

## Models and text encoders

| Model | Encoder | CLIP type | Prompt shape |
| --- | --- | --- | --- |
| FLUX.2 Klein 4B distilled | Qwen3-4B | `flux2` | Sentences. Subject → place → light → camera. Under ~150 words. Positive opposites, not “no logos”. |
| Wan 2.2 TI2V-5B | UMT5-XXL | `wan` | T2V: Entity + Scene + Motion + Aesthetic + one camera move (~80–120 words). I2V: **Motion + Camera only**. Silent — do not prompt audio. |
| LTX-2.5 distilled | Gemma4-12B-with-proj | `ltxv` | One flowing present-tense paragraph, 4–8 sentences, **audio interleaved**. Dialogue in `"quotes"` only if you asked for speech. |

Comfy wraps Klein’s string in a Qwen chat template. Do **not** paste `<|im_start|>` into the widget.

Distilled Klein is **CFG 1.0 / 4 steps** — quality is almost entirely the Positive prompt. FLUX-family models do not use negatives well; put constraints in the positive (“unmarked facades, empty of signage”).

---

## Recipes

=== "Klein 4B (still)"

    Front-load the subject. Write prose.

    **Do:** `A photoreal still photograph of a small-town main street at golden hour. A single red bicycle leans against a brick storefront. Warm sidelight rakes the brick…`

    **Don’t:** `main street, bicycle, photoreal, 24mm, no logos, no text`

=== "Wan 2.2 T2V"

    Entity + scene + motion + **one** camera verb (`dolly in`, `pan`, `tracking`, `fixed camera`). About 80–120 words. No audio, no score.

=== "Wan 2.2 I2V"

    The start image owns look. Prompt only motion and camera. Keep identity locked. Lab I2V graphs no longer encode a separate look CLIP into the sampler.

=== "Looping GIF (Wan I2V)"

    Locked camera plus cyclic motion (breeze, curtains, leaves, water). Do **not** prompt a walk or a one-way dolly — **wan-gif-loop-lab-example** plays the clip forward then reverse (VHS ping-pong) so the join frame is the start image. Turn ping-pong off only when reverse playback would look wrong.

=== "Dream-house pack (Klein)"

    One identity paragraph locks **massing + materials + place** (one compact single-story rectangular cedar cabin, hip roof, two-bay glass, decks on gravel, alpine lake). Each SHOT card is only camera, room, time of day, and season of **that same cabin** — not a new building. **klein-dream-house-lab-example** uses **Prompt Join** so you edit the house once. SHOT 01 is the T2I identity plate; Queue 01 first and do not bypass it when generating 02–10 (they Klein-edit from 01 via `VAEEncode` + `ReferenceLatent`). Unused shots 02–10 may still be bypassed after 01 exists. Keep the ten Instagram 4:5 stills as photographs of one cabin.

=== "LTX-2.5 AV"

    Flowing paragraph, present tense, audio beside the action (wind, footsteps, a shop bell) — not a sound trailer at the end. Shorts: world SFX, **no score**. Do not paste a Wan or Kling shot list unchanged.

---

## Prompt Enhance nodes

In-tree pack `custom_nodes/ez_prompt_enhance` (category **ez-comfy/prompt**). Entrypoint copies it into Comfy `custom_nodes/` on start (same pattern as lab workflows).

| Node | Modes | Use on |
| --- | --- | --- |
| **Klein Prompt Enhance** | `t2i`, `edit` | klein-still-draft / klein-still-hero / klein-still-daily / klein-dream-house identity / film-*-90s identity |
| **Wan Prompt Enhance** | `t2v`, `i2v` | wan-i2v-5s / wan-t2v-5s / wan-i2v-shot / wan-gif-loop |
| **LTX Prompt Enhance** | `t2v`, `i2v` | ltx-i2v-5s / ltx-t2v-5s / ltx-i2v-shot |
| **Prompt Join** | identity + shot → one STRING | klein-dream-house shot cards |

STRING out → CLIPTextEncode `text` input.

1. Set `XAI_API_KEY` in `.env` (see `.env.example`). Optional: `XAI_MODEL` (default `grok-4.6`), `XAI_BASE_URL`, `XAI_TIMEOUT_S`.
2. Replace the canned prompt with a lazy sentence.
3. Set **Enhance** to true. Queue.

**Enhance defaults to false.** Canned text is used as-is so shorts identity locks do not drift and hermetic Queue needs no key.

Fail-soft: missing key, timeout, or HTTP error logs a warning and passes the original prompt through. Generation still runs.

!!! warning "No local LLM on the Spark"

    Do not run Gemma 4 E2B (the official LTX enhancer) or any other GPU LLM beside this stack. LTX-2.5 is already a 22B joint AV transformer; extra weights steal GB10 headroom and threaten SSH. The rewrite is **off-box** (`api.x.ai`).

Safety: `restart: "no"`, headroom preflight, and download-limit clear-on-exit are unchanged. The key is runtime env only — never baked into the image.

---

## Next steps

Queue **klein-still-draft-lab-example** first ([Getting Started](getting-started.md)), then the still → Wan 5 s → LTX 5 s loop on [Visual Generative AI](visual-generative-ai.md).

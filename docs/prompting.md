---
title: Prompting Klein, Wan, and LTX
description: Model-native prompt recipes and lazy Prompt Enhance nodes for the US-safe ComfyUI studio.
tags: [prompting, klein, wan, ltx, comfyui]
---

# Prompting Klein, Wan, and LTX

**What's on this page**

- How each lab model actually reads a prompt
- Canned lab-example text (already rewritten)
- GIF loop motion and dream-house world bible (one place prompt; one shot per room or angle; Prompt Join lock=view). Clay tour: same bible, Klein restyles Blender stills
- Character draft then tweak (style dropdown; generated still as the next reference)
- Lazy path: Prompt Enhance nodes (on-box Qwen3-4B-Instruct-2507). Seeded graphs pin Enhance **on** for lazy CLIP printers and **off** when the string is already a recipe, script, or film shot.
- Style dropdown: research-backed look references; dropdown wins over style already in the source
- After Queue, the dim **CLIP prompt** box is always visible and shows the string CLIP/ACE encoded

**What this enables**

- Writing (or pasting) a prompt that matches Klein 4B, Wan 2.2, or LTX-2.5 instead of SD1.5 tag soup
- Typing a lazy sentence and letting the on-box Qwen3 rewriter expand it for Klein / Wan / LTX
- Optional style dropdown (50 presets): the rewriter weaves research-backed medium, light, color, and texture into the CLIP prompt, and retunes any style already in the source

!!! tip "Lab graphs already ship model-native prompts"

    Seeded **\*-lab-example** graphs use research-backed Positive / Motion text. Prompt Enhance is **on** for lazy CLIP printers (Klein stills, generic 5s Wan/LTX, identity bibles you type). It is **off** for authored recipes: 90s films, talking-head freeze, ping-pong loops, camera-verb I2V, podcast Speaker A/B scripts, ACE tags/lyrics, IC-LoRA. Turn it the other way in the App if you want. **research-chat-lab-example** is a no-UNET creative desk (occupancy **llm**): chat or planner+search subagents, then copy prompt ingredients into **prompt-forge-lab-example**. Prompt Forge previews Klein / Wan / LTX rewrites with no UNET. Copy the family you need into Spark Still. The CLIP prompt box is visible before Queue (empty until rewrite) and shows the encoded string after.

```mermaid
flowchart TB
  Which{"Which graph is loaded?"} --> K["Klein still / edit"]
  Which --> W["Wan T2V or I2V"]
  Which --> L["LTX T2V or I2V"]
  K --> Kp["Sentences: subject → place → light → camera"]
  W --> Wp{"I2V?"}
  Wp -->|yes| Wi["Motion + one camera only"]
  Wp -->|no| Wt["Entity + scene + motion + aesthetic + one camera"]
  L --> Lp["Present-tense paragraph · sound interleaved"]
```

Why the three models exist: [Klein, Wan, and LTX](learn/pipeline.md).

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

    **Do:** `A photoreal still, first-person eye-level body-cam already at a dead sprint across a golden-hour tropical rooftop terrace. An original techno wizard in ink-black fitted running layers and an open short storm-cloak with warm-gold lining pumps through the lower third. Tiny warm-gold rune sparks bloom at the wrists only. Full-bleed photographic plate in YouTube 16:9 with bare frame edges and a clean unmarked lens…`

    **Don’t:** `rooftop, techno wizard, photo, 24mm, no logos, no text`

=== "Wan 2.2 T2V"

    Entity + scene + motion + **one** camera verb (`dolly in`, `pan`, `tracking`, `fixed camera`). About 80–120 words. No audio, no score.

=== "Wan 2.2 I2V"

    The start image owns look. Prompt only motion and camera. Keep identity locked. Lab I2V graphs no longer encode a separate look CLIP into the sampler.

=== "Looping GIF (Wan I2V)"

    Locked camera plus cyclic motion (breeze, curtains, leaves, water). Do **not** prompt a walk or a one-way dolly — **wan-gif-loop-lab-example** plays the clip forward then reverse (VHS ping-pong) so the join frame is the start image. Turn ping-pong off only when reverse playback would look wrong.

=== "Dream-house pack (Klein)"

    Type **one place**. Identity-mode enhance freezes only the rooms, furniture, outdoor lamps, and surroundings you named (the default placeholder is a full-floor penthouse on a tall tower in a dense unmarked city). Name lounge, kitchen, dining, bath, bedroom, terrace, study, and outdoor lamps so the tour can enter them. Hidden SHOT cards are a walkthrough — tower, foyer, lounge, kitchen, dining, bedroom, bath, terrace, drone, study — not a penthouse template. Each card is one room or angle with its own backdrop: only lounge looks out the main opening; kitchen, dining, bedroom, bath, and study keep interior walls. **Prompt Join** `lock=view` front-loads the shot, then “same building, rooms, furniture, and materials” + “this still is only the room and backdrop the shot names” + the bible, and repeats that closer after the bible. Shot cards are **not** Klein-t2i-enhanced — a per-shot rewrite would mutate the bible. Shots 02–10 are independent T2I (empty latent, same seed) — they do **not** `ReferenceLatent` shot 01. Dawn / noon / night of one camera belong on **klein-time-of-day-lab-example** (`lock=state`). `lock=state` is the other mode: same camera, change only light/grade/action (lighting-trio, before/after). Unused shots may be bypassed.

    Second door — **klein-dream-house-clay-lab-example**: same bible and shot cards, but each still `ReferenceLatent`s a clay plate (`ez_house_clay_01`…`10`). `start` seeds LoadImage; optional Workbench dump with `./scripts/manage.sh house-views` while Comfy is **down**. Prompt the **look** (style dropdown, materials); do not re-describe the floorplan — the greybox already locked cameras and adjacency. Prefix `ez_dream_house_clay_01`…`10`. Language-only (no geometry) → T2I tour. Playbook: [Dream-house tours](learn/dream-house.md).

=== "LTX-2.5 AV"

    Flowing paragraph, present tense, audio beside the action (wind, footsteps, a shop bell) — not a sound trailer at the end. Shorts: world SFX, **no score**. Do not paste a Wan or Kling shot list unchanged. 90s films bake one `ltx_i2v` paragraph per shot (I2V: motion + one camera + interleaved foley; start image owns look). All three 90s films pin Enhance **off** so the identity and each shot paragraph are encoded as written.

    First-person body-cam (go-see): one signature stunt per 5 s; eye-level; sleeves and gloves in the lower third; look at the landing before a jump; dip on impact then recover; land the last frame on a readable plant for the next I2V. Close-mic breath + surface foley beside the move. No speech. Identity still is already at a dead sprint.

    LTX audio: name the mix first (`Wordless mix: only footfalls, wind, grit, close-mic breath, silent mouth`). Put `No speech.` last for the bible contract. Do not quote dialogue. Distilled AV will talk if the clause is only a prohibition.

---

## Prompt Enhance nodes

In-tree pack `custom_nodes/ez_prompt_enhance` (category **ez-comfy/prompt**). Entrypoint copies every pack under `custom_nodes/` into Comfy on start (same pattern as lab workflows), including `ez_ltx_spatial` which snaps LTX canvases off 720/1080 so the video VAE does not einops-crash, and `ez_film` which unloads Klein before LTX and stitches the 90s MP4.

| Node | Modes | Use on |
| --- | --- | --- |
| **Klein Prompt Enhance** | `t2i`, `edit`, `identity` | every Klein still / edit / identity bible (including 90s film identity) |
| **Wan Prompt Enhance** | `t2v`, `i2v`, `flf`, `vace` | wan-i2v-5s / wan-t2v-5s / wan-flf-5s / wan-vace-join |
| **LTX Prompt Enhance** | `t2v`, `i2v` | ltx-i2v-5s / ltx-t2v-5s / each 90s film shot |
| **ACE-Step Prompt Enhance** | `vocal`, `instrumental` | music-rap-* tags+lyrics; music-edm-drive-through-* scores; podcast instrumental beds |
| **Prompt Join** | `lock=view`: shot + lock + bible + inventory + closer (camera-first walkthrough; this still is only the room and backdrop the shot names). `lock=state`: bible + inventory + lock + shot | dream-house (view) and lighting/before-after (state) |

STRING out → CLIPTextEncode `text` input.

1. `./scripts/manage.sh download-models` (includes `comfy/llm/Qwen3-4B-Instruct-2507-Q4_K_M.gguf`).
2. Type a lazy sentence (or leave the canned paragraph). **Enhance** defaults **on**.
3. Optional: pick a **style** (photorealistic, anime, cartoon, … — 50 ids, or `none`).
4. Queue. On the Enhance node, read the dim **CLIP prompt** box — that is the text CLIP encoded. The top prompt widget stays as you typed it. If the 4B rewriter was skipped, **Enhance status** says why (missing GGUF, missing llama.cpp, timeout) and generation still runs. A selected style should read as that medium (cel, watercolor, oil on canvas, …), not a 3D/photo paragraph with a style trailer.

**Enhance defaults to true on the node** (a dragged node still rewrites). Seeded JSON pins it **off** when a rewrite would mutate structured input:

| Pin Enhance **off** | Why |
| --- | --- |
| 90s films (identity + 18 LTX shots) | Baked `shots.yaml`; rewriter changes camera and foley |
| Talking-head LTX I2V | A2V freeze recipe |
| GIF / bumper / sticker loops | Ping-pong needs cyclic locked-camera motion |
| Orbit / push-in / parallax I2V | The canned camera verb **is** the param |
| IC-LoRA depth | Clay already locked camera |
| Podcast script + ACE beds | `Speaker A:` labels and instrumental tags are parser input |
| Rap tags + lyrics (draft, full, nill-bye) | `[verse]`/`[chorus]`, BPM, `language=en` vs encoder widgets |
| Drive-through EDM arrangement scores | `[inst]`/`[intro]`/`[outro]`, BPM; eighty-three takes stay instrumental; two rave-set treats add one short `[chorus]` chop (no `[verse]`) |

Lazy Klein stills, identity bibles you type, Klein edit, generic 5s Wan/LTX printers, Prompt Forge, and Beat Sheet stay **on**. Dub **Rewrite translation** stays on — that path translates turns, it does not CLIP-rewrite. Identity mode keeps the bible camera-free and still weaves a selected style (medium and texture, no camera). Style is ignored on I2V / FLF / VACE (the start image owns look). Do not Klein-t2i-enhance Prompt Join shot cards.

```mermaid
flowchart TD
  E{"Enhance on?"} -->|no| Pin["CLIP encodes the widget text as typed"]
  E -->|yes| Lazy["4B GGUF rewrites for this model's encoder"]
  Lazy --> Style{"Style dropdown?"}
  Style -->|preset| Rep["Dropdown wins over medium already in the source"]
  Style -->|none| Keep["Keep rewriter output"]
  Lazy --> Miss["Missing GGUF / llama.cpp / timeout → passthrough + status"]
```

When Enhance is **on** and a style is selected (t2i / t2v / Klein edit / identity):

- The dropdown is look authority. If the source already names a medium, lighting, grade, lens, or art style, the rewriter **replaces** those clauses so they match the dropdown. It does not stack two styles.
- Each preset is a short reference (medium, light, color, texture, camera or projection) tuned for Klein prose, Wan aesthetic+stylization, or LTX lighting/surface in the flowing paragraph.
- CLIP text stays generic: no camera/film/studio brand names. Labels such as **Pixar-like 3D** still weave as “stylized feature 3D”.
- The dropdown wins in the CLIP string even if the 4B rewriter ignores the hint or the GGUF passthroughs: conflicting medium words are dropped and the catalog medium is front-loaded.
- After Queue, the **CLIP prompt** box on the node is the preview. First deploy: restart the container so `js/` is copied, then hard-refresh the Comfy tab.

After Queue the node is an output: the **CLIP prompt** widget is the CLIP string (no `[passthrough:` prefix). **Enhance status** is empty when the rewriter ran, or a next step when it did not.

Fail-soft: missing GGUF, missing `llama-cpp-python`, timeout, or empty model output logs a warning and passes the source through (with style applied if one is selected). Generation still runs. Do not copy a GGUF by hand — `./scripts/manage.sh download-models` plus a restart heals `comfy/llm/` and `doctor`/`start` relink a snapshot that is already on disk. **Enhance status** `llama.cpp unavailable` means `from llama_cpp import Llama` failed (not that pip skipped). Queue self-heals the CPU wheel from the official extra-index, then force-reinstalls the GitHub manylinux wheel if the pin is already satisfied but Llama still will not import. If status still names a `docker exec … pip install --force-reinstall` command, run that line. Confirm: `docker exec ez-comfy-studio /comfy-state/ComfyUI/.venv/bin/python -c 'from llama_cpp import Llama'`. Pip “already satisfied” alone is not the check.

!!! warning "GPU-first local LLM"

    GPU-first: occupancy `llm` / `llm-desk` / `idle` uses the host 35B sidecar when it answers (`occupancy enter llm-desk --yes`). Prompt Enhance on Wan / LTX / TRELLIS stays **CPU 4B** so the denoise keeps unified memory (OOM-safe). `EZ_LLM_ALLOW_GPU=0` forces CPU everywhere. Do not run the 35B sidecar next to LTX. The in-image llama-cpp pin is still a CPU wheel — in-canvas 4B ngl is occupancy-ready for a later CUDA wheel.

Safety: `restart: "no"`, headroom preflight, and download-limit clear-on-exit are unchanged. No API keys. The GGUF lives under `MODELS_DIR`, never in the image.

---

## Next steps

Queue **klein-still-draft-lab-example** first ([Getting Started](getting-started.md)), or **klein-character-draft-lab-example** then **klein-character-tweak-lab-example** to iterate a still. Daily loop: still → Wan 5 s → LTX 5 s on [Visual Generative AI](visual-generative-ai.md).

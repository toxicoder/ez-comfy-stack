# LTX-2.5 official graphs (quality / control source of truth)

Upstream: [Lightricks/ComfyUI-LTXVideo `example_workflows/2.5/`](https://github.com/Lightricks/ComfyUI-LTXVideo/tree/master/example_workflows/2.5)

Those JSON files are **Comfy subgraphs** (UUID node types). Load them from Comfy **Templates → LTX-2.5**, or clone ComfyUI-LTXVideo. This tree does **not** vendor the 150–240 KB subgraph blobs (they will not Queue without the matching subgraph pack).

Lab **default printers stay 5.00 s / 121 frames / 1280×704** (`ltx-i2v-5s-lab-example.json` and the 90s one-click films). Duration-head 8 / 10 / 12 s is opt-in behind `ez_film.ltx_timing.preflight_duration_s` (`1+8n` frames; even latents refuse). Do not queue a 30/60/90 s latent on GB10.

| Official graph | Lab role |
| --- | --- |
| T2V/I2V single-stage distilled | Fast quality preview (same family as lab 5 s I2V) |
| T2V/I2V two-stage distilled | DFR / 2× spatial + refine. YAML `print: dfr` records stub template `templates/ltx-2.5/t2v-i2v-two-stage-distilled` (not vendored JSON) |
| A2V two-stage distilled | Audio freeze (talking-head / ACE-Step bed) |
| IC-LoRA Union Control | Depth / canny / pose v2v. Lab envelope: `workflows/dcc/ltx-iclora-depth-5s-lab-example.json`. Official graph stays Templates (`LTX-2.5_ICLoRA_Union_Control_Distilled.json`). LoRA: `download-ltx --tier iclora` → `ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors`. Distilled-only. Refuse 19B. |

Frame count must be `1 + 8n` (upstream README). Occupancy: do not coreside with Wan A14B / Fun InP / TRELLIS / SeedVR2.

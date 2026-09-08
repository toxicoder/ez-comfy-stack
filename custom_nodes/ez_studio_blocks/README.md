# ez_studio_blocks

Lab subgraph blueprints for the US-safe studio. Comfy scans `subgraphs/*.json`
and lists them in the subgraph / node library after `start` copies this pack
into `$COMFY_HOME/custom_nodes/ez_studio_blocks/`.

| Blueprint | Occupancy |
| --- | --- |
| `klein-t2i-backbone` | klein |
| `wan-i2v-5s` | wan |
| `ltx-av-5s` | ltx |
| `ltx-film-shot` | film |

Source of truth: `tests/python/_build_studio_blocks.py`. Do not vendor official
LTX Template blobs. US-safe weights only (Klein 4B / Wan 2.2 5B / LTX-2.5 distilled).

90s film lab graphs still expand 18 concat-safe printers on the parent so
VHS prefixes stay per-shot. Drop `ltx-film-shot` from the node library when
composing a new graph; do not unpack official LTX Templates.

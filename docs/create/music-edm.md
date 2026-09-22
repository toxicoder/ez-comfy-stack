---
title: Drive-through EDM
description: Eighty-five warped hybrid-trap EDM takes (150–480 s, short builds, fast tempos) on ACE-Step.
tags: [music, edm, ace-step, drive-through, us-safe]
---

# Drive-through EDM

**What's on this page**

- **Drive-through** live bass-set EDM (not rap over a club bed)
- **All five albums** (Hour 1, Hour 2, Headliner, Afterparty, Secret Homage)
- **Occupancy:** do not co-resident ACE-Step with Klein / Wan / LTX

**What this enables**

- **Eighty-five original Drive-through EDM takes** (150–480 s, eighty-three instrumental, two DJ-shout treats) without cloud music APIs

**Who this is for:** studio users after a RAP-FIRST draft. Overview: [Local music](../music.md). RAP-FIRST: [Nill Bye albums](music-rap.md). Disclosure: [Music disclosure](music-disclosure.md).

Do **not** load Klein + Wan + LTX + ACE-Step in one session. Cover art is a later Klein session. Files land under `${COMFY_OUTPUT_DIR}`.

## Drive-through EDM examples

Eighty-five extra full-track graphs under **`_lab/audio/albums/drive-through/<album>/`**. Same AIO, sampler, occupancy **audio**. App **Duration (seconds)** is the sum of that take's stanzas (150–480 s). The arranger does not stretch bars to hit a clock time: a short piece gains whole stanzas, a long piece loses whole stanzas. Every take opens with a short build (4 or 6 bars), then a drop. Later stanzas change role, bar length (4–12), and layer so one loop does not sit. Tempos snap to **165, 168, 170, 172, 174, or 176**. Keys walk fifths so the set still mixes. Meter stays 4/4. Queue a numbered track **on its own**, or `album-render --album drive-through/<album-slug>`. SaveAudio stem is **`NN - Song Title`**. The graph note names the form and key.

Fictional act only: **Drive-through** (hardcore, pure of heart) playing a **live bass DJ set**. Original **warped hybrid-trap EDM** spliced from [Audio Rack](audio-rack.md) catalogs (hybrid trap, riddim, tearout, brostep, wave bass, color bass, drumstep, dirty dubstep, neuro bass, chest/dirty bass, festival trap — not techno, not big room, not progressive house). Named recipes (`rec_drive_through_drop`, `rec_drive_riddim`, …) fill empty axes; each take overrides tempo, bass, and form. No living-DJ names. No famous-hook paraphrases. Eighty-three takes lock `instrumental, no vocals, no singing, no choir, no vocal chops` via `mix_drive_lock` (App **Vocal / instrumental** = instrumental; encoder language `unknown`). Two takes are sparse DJ-shout treats (`wide open`, `second wave`): App mode **vocal**, `voc_dj_shout`, one 1–2 word `[chorus]` chop, no `[verse]`. Arrangement scores are empty-body ACE markers (`[build-up - …]`, `[drop - warped bass, rapid hi-hats]`, `[inst - …]`, `[breakdown - …]`, `[outro]`) so ACE does not sing production notes. Drops stack a mono sub, a low-mid bass melody, drums, and width. No brass, horns, trumpets, or high leads. Not a Nill Bye verse/chorus loop. Cover **LoadImage** stays unwired; App **Album art** defaults to skip. Some takes add dual-action pedal bass under rolling hats. Phase2, phase3, and phase4 graphs keep that ACE topology but vary Comfy node placement across five layouts (`column`, `wide-stage`, `stacked-tower`, `prompt-left`, `output-rail`). ACE-Step timbre is invented. Human selection and edit required before any release. A longer Queue is expected: 2.5–8 min latents cost RAM and time linearly.

This is **not** the Nill Bye trap/EDM pack. Those graphs are rap **over** club beds with a dry booth. Drive-through is dance EDM (mostly instrumental).

Catalog order is the recommended live-set queue (each graph still Queues alone).

#### Hour 1 (`audio/albums/drive-through/hour-1/`)

Hour 1 of the live bass set. Full album: `./scripts/manage.sh album-render --album drive-through/hour-1`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **01-night-window** | warped hybrid-trap **168**, seed **193** | `01 - Night Window` | Hybrid trap warp |
| **02-open-lane** | riddim **170**, seed **191** | `02 - Open Lane` | Riddim warp |
| **03-exit-seven** | tearout **165**, seed **233** | `03 - Exit Seven` | Tearout warp |
| **04-skyline-pass** | brostep **168**, seed **199** | `04 - Skyline Pass` | Brostep warp |
| **05-on-ramp** | wave bass **170**, seed **197** | `05 - On-Ramp` | Wave bass warp |
| **06-tunnel-bass** | dirty bass **168**, seed **257** | `06 - Tunnel Bass` | Dirty bass warp |
| **07-wide-open** | color bass **168**, seed **239** | `07 - Wide Open` | **DJ shout treat.** Color bass warp |
| **08-overpass** | dirty dubstep **168**, seed **227** | `08 - Overpass` | Dirty dubstep warp |
| **09-second-wave** | warped hybrid-trap **168**, seed **241** | `09 - Second Wave` | **DJ shout treat.** Hybrid trap warp |
| **10-freight-pulse** | drumstep **176**, seed **211** | `10 - Freight Pulse` | Drumstep warp |
| **11-keep-going** | neuro bass **174**, seed **251** | `11 - Keep Going` | Neuro bass warp |
| **12-horizon-kick** | tearout **172**, seed **263** | `12 - Horizon Kick` | Tearout warp |
| **13-clean-wreckage** | brostep **168**, seed **269** | `13 - Clean Wreckage` | Brostep warp |
| **14-heart-lane** | wave bass **168**, seed **223** | `14 - Heart Lane` | Wave bass warp |
| **15-dawn-receipt** | chest bass **165**, seed **229** | `15 - Dawn Receipt` | Chest bass warp |

#### Hour 2 (`audio/albums/drive-through/hour-2/`)

Hour 2 of the live bass set. Full album: `./scripts/manage.sh album-render --album drive-through/hour-2`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **01-rumble-strip** | warped hybrid-trap **165**, seed **271** | `01 - Rumble Strip` | Hybrid trap warp |
| **02-low-lane** | riddim **168**, seed **277** | `02 - Low Lane` | Riddim warp |
| **03-warm-merge** | wave bass **168**, seed **281** | `03 - Warm Merge` | Wave bass warp |
| **04-colour-span** | color bass **168**, seed **283** | `04 - Colour Span` | Color bass warp |
| **05-garage-ticket** | festival trap **165**, seed **293** | `05 - Garage Ticket` | Festival trap warp |
| **06-liquid-grade** | drumstep **176**, seed **307** | `06 - Liquid Grade` | Drumstep warp |
| **07-jump-bay** | brostep **168**, seed **311** | `07 - Jump Bay` | Brostep warp |
| **08-psy-median** | neuro bass **168**, seed **313** | `08 - Psy Median` | Neuro bass warp |
| **09-groove-mile** | warped hybrid-trap **168**, seed **317** | `09 - Groove Mile` | Hybrid trap warp |
| **10-donk-ramp** | tearout **168**, seed **331** | `10 - Donk Ramp` | Tearout warp |
| **11-bounce-booth** | chest bass **165**, seed **337** | `11 - Bounce Booth` | Chest bass warp |
| **12-toll-growl** | riddim **168**, seed **347** | `12 - Toll Growl` | Riddim warp |
| **13-night-oil** | warped hybrid-trap **165**, seed **349** | `13 - Night Oil` | Hybrid trap warp |
| **14-chest-pass** | dirty bass **168**, seed **353** | `14 - Chest Pass` | Dirty bass warp |
| **15-sunrise-sub** | wave bass **165**, seed **359** | `15 - Sunrise Sub` | Wave bass warp |

#### Headliner (`audio/albums/drive-through/headliner/`)

Hour 3 headliner. Node placement varies across five layouts. Full album: `./scripts/manage.sh album-render --album drive-through/headliner`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **01-lantern-merge** | warped hybrid-trap **168**, seed **367** | `01 - Lantern Merge` | Hybrid trap warp |
| **02-firefly-lane** | color bass **170**, seed **373** | `02 - Firefly Lane` | Color bass warp |
| **03-canopy-bounce** | chest bass **168**, seed **379** | `03 - Canopy Bounce` | Chest bass warp |
| **04-grove-wreck** | riddim **168**, seed **383** | `04 - Grove Wreck` | Riddim warp |
| **05-moss-sub** | dirty bass **168**, seed **389** | `05 - Moss Sub` | Dirty bass warp |
| **06-fern-stack** | warped hybrid-trap **170**, seed **397** | `06 - Fern Stack` | Hybrid trap warp |
| **07-pollen-kick** | drumstep **176**, seed **401** | `07 - Pollen Kick` | Drumstep warp |
| **08-cedar-growl** | tearout **168**, seed **409** | `08 - Cedar Growl` | Tearout warp |
| **09-moon-ramp** | wave bass **168**, seed **419** | `09 - Moon Ramp` | Wave bass warp |
| **10-trail-bounce** | color bass **168**, seed **421** | `10 - Trail Bounce` | Color bass warp |
| **11-dew-wreck** | neuro bass **174**, seed **431** | `11 - Dew Wreck` | Neuro bass warp |
| **12-sap-stack** | brostep **172**, seed **433** | `12 - Sap Stack` | Brostep warp |
| **13-glade-split** | dirty dubstep **168**, seed **439** | `13 - Glade Split` | Dirty dubstep warp |
| **14-root-chest** | chest bass **168**, seed **443** | `14 - Root Chest` | Chest bass warp |
| **15-ember-crest** | warped hybrid-trap **172**, seed **449** | `15 - Ember Crest` | Hybrid trap warp |

#### Afterparty (`audio/albums/drive-through/afterparty/`)

Hour 4 afterparty. Node placement varies across five layouts. Full album: `./scripts/manage.sh album-render --album drive-through/afterparty`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **01-brake-fade** | dirty bass **168**, seed **457** | `01 - Brake Fade` | Dirty bass warp |
| **02-diesel-hum** | warped hybrid-trap **170**, seed **461** | `02 - Diesel Hum` | Hybrid trap warp |
| **03-axle-grind** | tearout **170**, seed **463** | `03 - Axle Grind` | Tearout warp |
| **04-weigh-station** | brostep **172**, seed **467** | `04 - Weigh Station` | Brostep warp |
| **05-black-ice** | riddim **172**, seed **479** | `05 - Black Ice` | Riddim warp |
| **06-high-beams** | color bass **172**, seed **487** | `06 - High Beams` | Color bass warp |
| **07-chain-hook** | brostep **174**, seed **491** | `07 - Chain Hook` | Brostep warp |
| **08-grit-plate** | wave bass **168**, seed **499** | `08 - Grit Plate` | Wave bass warp |
| **09-steel-grate** | drumstep **174**, seed **503** | `09 - Steel Grate` | Drumstep warp |
| **10-rest-bay** | chest bass **170**, seed **509** | `10 - Rest Bay` | Chest bass warp |
| **11-haul-crate** | warped hybrid-trap **174**, seed **521** | `11 - Haul Crate` | Hybrid trap warp |
| **12-night-splice** | wave bass **170**, seed **523** | `12 - Night Splice` | Wave bass warp |
| **13-torque-bay** | neuro bass **176**, seed **541** | `13 - Torque Bay` | Neuro bass warp |
| **14-spare-drum** | brostep **172**, seed **547** | `14 - Spare Drum` | Brostep warp |
| **15-oil-pan** | color bass **168**, seed **557** | `15 - Oil Pan` | Color bass warp |
| **16-curb-check** | drumstep **176**, seed **563** | `16 - Curb Check` | Drumstep warp |
| **17-last-exit** | dirty bass **172**, seed **569** | `17 - Last Exit` | Dirty bass warp |
| **18-asphalt-heart** | chest bass **170**, seed **571** | `18 - Asphalt Heart` | Chest bass warp |
| **19-clutch-slam** | tearout **174**, seed **577** | `19 - Clutch Slam` | Tearout warp |
| **20-trailer-hitch** | warped hybrid-trap **172**, seed **587** | `20 - Trailer Hitch` | Hybrid trap warp |

#### Secret Homage (`audio/albums/drive-through/secret-homage/`)

Secret Homage. Node placement varies across five layouts. Full album: `./scripts/manage.sh album-render --album drive-through/secret-homage`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **01-hush-lane** | dirty dubstep **165**, seed **593** | `01 - Hush Lane` | Dirty dubstep warp |
| **02-cipher-lock** | brostep **165**, seed **599** | `02 - Cipher Lock` | Brostep warp |
| **03-ghost-dock** | riddim **165**, seed **601** | `03 - Ghost Dock` | Riddim warp |
| **04-sealed-ramp** | tearout **168**, seed **607** | `04 - Sealed Ramp` | Tearout warp |
| **05-fog-vault** | color bass **165**, seed **613** | `05 - Fog Vault` | Color bass warp |
| **06-dummy-light** | warped hybrid-trap **168**, seed **617** | `06 - Dummy Light` | Hybrid trap warp |
| **07-quiet-wreck** | dirty bass **165**, seed **619** | `07 - Quiet Wreck` | Dirty bass warp |
| **08-off-ledger** | drumstep **176**, seed **631** | `08 - Off Ledger` | Drumstep warp |
| **09-back-alley** | neuro bass **174**, seed **641** | `09 - Back Alley` | Neuro bass warp |
| **10-cellar-kick** | dirty dubstep **168**, seed **643** | `10 - Cellar Kick` | Dirty dubstep warp |
| **11-hidden-booth** | warped hybrid-trap **165**, seed **647** | `11 - Hidden Booth` | Hybrid trap warp |
| **12-coded-sub** | chest bass **165**, seed **653** | `12 - Coded Sub` | Chest bass warp |
| **13-shadow-coil** | neuro bass **168**, seed **659** | `13 - Shadow Coil` | Neuro bass warp |
| **14-mute-pyro** | wave bass **168**, seed **661** | `14 - Mute Pyro` | Wave bass warp |
| **15-unlisted-row** | drumstep **176**, seed **673** | `15 - Unlisted Row` | Drumstep warp |
| **16-night-cipher** | wave bass **165**, seed **677** | `16 - Night Cipher` | Wave bass warp |
| **17-blank-stencil** | festival trap **165**, seed **683** | `17 - Blank Stencil` | Festival trap warp |
| **18-blind-stamp** | riddim **168**, seed **691** | `18 - Blind Stamp` | Riddim warp |
| **19-cold-cache** | warped hybrid-trap **165**, seed **701** | `19 - Cold Cache` | Hybrid trap warp |
| **20-secret-homage** | dirty dubstep **165**, seed **709** | `20 - Secret Homage` | Dirty dubstep warp |

Cover still in a later Klein session. Do not co-resident with LTX / Wan / Klein.

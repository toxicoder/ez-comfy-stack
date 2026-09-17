---
title: Audio catalog
description: Seeded podcast, dub, RAP-FIRST, and Drive-through EDM graphs plus every Nill Bye and Drive-through album table.
tags: [comfyui, workflows, audio, rap, edm, catalog]
---

# Audio catalog

**What's on this page**

- **Podcast, dub, and RAP-FIRST** graphs (occupancy **audio**)
- **Nine Nill Bye albums** (all track tables)
- **Five Drive-through albums** (all track tables)

**What this enables**

- **Queuing local audio** without loading Klein / Wan / LTX in the same session
- **Finding a numbered take** under `_lab/audio/albums/<artist>/<album>/`

**Who this is for:** studio users after `download-podcast` / `download-dub` / `download-music`. Index: [Workflow catalog](../studio-workflows.md). Node-by-node widgets: [Workflow details](workflows-index.md). Playbooks: [Local podcast](../podcast.md), [Local dub](../dub.md), [Local music](../music.md). Outputs under `${COMFY_OUTPUT_DIR}`.

Splice professional ACE tags on occupancy **llm** first: [Audio Rack](audio-rack.md) (`inspire/audio-rack`). Then Queue occupancy **audio** graphs below.

Occupancy **audio**. Opt-in weights (`download-podcast` / `download-dub` / `download-music`). Do not co-resident with Klein / Wan / LTX. Album art is skip (default) / upload / generate (`cover.json` is klein occupancy). Cover LoadImage is **bypassed** (and unwired) so App Queue does not require a file. Upload: graph view, **Ctrl+B** Cover image, then wire. Graphs save tagged FLAC + MP3; `album-render` zips the folder. YouTube still-image MP4 is host `audio-still-video` after Queue.

| Workflow | What it does |
| --- | --- |
| **[audio/dub/clone-translate](../generated/workflows/audio/dub/clone-translate.md)** | Multi-speaker clone-and-translate. Pick or upload source media. Rights gate. **Clone CFG** auto 0.3 on EN→ES. Duration-locked `ez_dub_yt` for YouTube Languages. Prefix `ez_dub_mix` |
| **[audio/podcast/two-host-episode](../generated/workflows/audio/podcast/two-host-episode.md)** | Two-host episode. Kokoro stock voices + ACE-Step instrumental bed. Prefix `ez_podcast_ep` |
| **[audio/podcast/radio-drama](../generated/workflows/audio/podcast/radio-drama.md)** | One-graph radio drama. Sting + bed stay instrumental. Prefix `ez_radio_ep` |
| **[audio/podcast/learn-episode](../generated/workflows/audio/podcast/learn-episode.md)** | Learning episode. Paste notes/links, pick format + duration. Prefix `ez_learn_ep` |
| **[audio/music/rap-draft](../generated/workflows/audio/music/rap-draft.md)** | ACE-Step rap draft **32 s** boom-bap 88 (`ez_rap_draft`) |
| **[audio/music/rap-full](../generated/workflows/audio/music/rap-full.md)** | ACE-Step rap full **96 s** boom-bap 88 (`ez_rap_full`). Queue draft first |

Nine Nill Bye albums under `_lab/audio/albums/nill-bye/<album>/`. Queue a numbered track, or `album-render`. RAP-FIRST playbook: [Nill Bye albums](music-rap.md).

| Album | What it does |
| --- | --- |
| **audio/albums/nill-bye/peer-review** | Fifteen tracks + `cover.json` + `album.json`. Lab catalog vs Rake. `album-render --album nill-bye/peer-review` |
| **audio/albums/nill-bye/citation-needed** | Fifteen tracks. Style pack (same dry booth; not trap/EDM). `album-render --album nill-bye/citation-needed` |
| **audio/albums/nill-bye/false-drop** | Fifteen tracks. Rap over club beds, no autotune. `album-render --album nill-bye/false-drop` |
| **audio/albums/nill-bye/frozen-ercot** | Fifteen tracks. Civic variety, punch-up satire of a public official. `album-render --album nill-bye/frozen-ercot` |
| **audio/albums/nill-bye/lone-star-tab** | Fifteen tracks. Civic club beds, same punch-up rule. `album-render --album nill-bye/lone-star-tab` |
| **audio/albums/nill-bye/thirty-four-counts** | Fifteen tracks. Federal variety. `album-render --album nill-bye/thirty-four-counts` |
| **audio/albums/nill-bye/pardon-flood** | Fifteen tracks. Federal club beds. `album-render --album nill-bye/pardon-flood` |
| **audio/albums/nill-bye/winterize-wells** | Fifteen tracks. Progress variety — methods and statutes, no roast target. `album-render --album nill-bye/winterize-wells` |
| **audio/albums/nill-bye/duty-switch** | Fifteen tracks. Progress club beds, same builder rule. `album-render --album nill-bye/duty-switch` |

Five Drive-through albums under `_lab/audio/albums/drive-through/<album>/`. Warped hybrid-trap bass set (not rap over a club bed). Drop first, hard warpy drops, trap drums, chest-sub bass. Headliner / Afterparty / Secret Homage vary Comfy node placement. EDM playbook: [Drive-through EDM](music-edm.md).

| Album | What it does |
| --- | --- |
| **audio/albums/drive-through/hour-1** | Fifteen tracks. Hour 1. `album-render --album drive-through/hour-1` |
| **audio/albums/drive-through/hour-2** | Fifteen tracks. Hour 2. `album-render --album drive-through/hour-2` |
| **audio/albums/drive-through/headliner** | Fifteen tracks. Headliner. `album-render --album drive-through/headliner` |
| **audio/albums/drive-through/afterparty** | Twenty tracks. Afterparty. `album-render --album drive-through/afterparty` |
| **audio/albums/drive-through/secret-homage** | Twenty tracks. Secret Homage. `album-render --album drive-through/secret-homage` |

Cover still in a later Klein session. Do not co-resident with LTX / Wan / Klein.

---

### 180s Nill Bye diss examples

One hundred thirty-five extra full-track graphs under **`_lab/audio/albums/nill-bye/<album>/`**. Same AIO, sampler, occupancy **audio**. App **Duration (seconds)** defaults to **180**. Queue a numbered track **on its own**, or generate the album in one go with `./scripts/manage.sh album-render --album nill-bye/<album-slug>`. SaveAudio stem is **`NN - Song Title`**. FLAC/MP3 tags include artist, album, title, and optional cover.

**Nill Bye** (science guy, mad) is a fictional MC with an invented ACE-Step vocal. Phases 0–2 roast fictional MC **Rake** (in his feels; club-talk and fake-cool as a brand). Phases 3–4 are civic satire of Texas Gov. **Greg Abbott** as a public-record target, not a vocal identity. Phases 5–6 are civic satire of **Donald Trump** as a public-record target, not a vocal identity. Phases 7–8 are **progress** takes: methods, statutes, and measurement with **no roast target** (winterize, preregister, hearings, NDCs, Article I, lead-line replacement). Original lyrics. No living-MC names. No famous-hook paraphrases. Punch **up** on diss phases; **build up** on progress phases. Do not roast disability, race, faith, children, or people at the river. Shipped bars stay short and SFW. Each take owns exclusive verses and punchlines — content bars are not reused across the one hundred thirty-five graphs; choruses stay unique hooks. Human rewrite required before any release.

Style and trap/EDM packs keep the same dry-booth voice (`male rap vocals, dry booth, no autotune`). Trap/EDM graphs are rap **over** club beds — not autotune EDM vocals. Voices, tags, BPM, and seeds stay as shipped; only the bars change per take.

A new album lands in `_lab/audio/albums/<artist>/<album-slug>/` with numbered tracks plus `cover.json` and `album.json`. Do not leave new graphs at the artist folder root.

#### Peer Review (`audio/albums/nill-bye/peer-review/`)

Lab catalog. Queue a track on its own. Full album: `./scripts/manage.sh album-render --album nill-bye/peer-review`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **[audio/albums/nill-bye/peer-review/01-lab-coat](../generated/workflows/audio/albums/nill-bye/peer-review.md)** | boom-bap **88** | `01 - Lab Coat Lecture` | Classroom lecture roast |
| **[audio/albums/nill-bye/peer-review/02-peer-review](../generated/workflows/audio/albums/nill-bye/peer-review.md)** | boom-bap **88**, `[spoken word]` intro | `02 - Peer Review` | Claims fail review |
| **[audio/albums/nill-bye/peer-review/03-feels](../generated/workflows/audio/albums/nill-bye/peer-review.md)** | lo-fi **86** | `03 - In His Feels` | Sad-boy diary as a brand |
| **[audio/albums/nill-bye/peer-review/04-fake-cool](../generated/workflows/audio/albums/nill-bye/peer-review.md)** | trap **140** | `04 - Fake Cool` | Club-talk is not a method |
| **[audio/albums/nill-bye/peer-review/05-hypothesis](../generated/workflows/audio/albums/nill-bye/peer-review.md)** | boom-bap **92**, seed **7** | `05 - Hypothesis vs Rumor` | Data vs rumor |
| **[audio/albums/nill-bye/peer-review/06-control-group](../generated/workflows/audio/albums/nill-bye/peer-review.md)** | boom-bap **88** | `06 - Control Group` | Rake is the uncontrolled variable |
| **[audio/albums/nill-bye/peer-review/07-sample-size](../generated/workflows/audio/albums/nill-bye/peer-review.md)** | boom-bap **92**, seed **11** | `07 - Sample Size` | One night is not a study |
| **[audio/albums/nill-bye/peer-review/08-placebo](../generated/workflows/audio/albums/nill-bye/peer-review.md)** | trap **140** | `08 - Placebo` | The flex is a sugar pill |
| **[audio/albums/nill-bye/peer-review/09-error-bars](../generated/workflows/audio/albums/nill-bye/peer-review.md)** | boom-bap **88**, seed **17** | `09 - Error Bars` | Confidence is a vibe, not a CI |
| **[audio/albums/nill-bye/peer-review/10-lab-notebook](../generated/workflows/audio/albums/nill-bye/peer-review.md)** | boom-bap **92**, seed **19** | `10 - Lab Notebook` | Receipts vs group-chat lore |
| **[audio/albums/nill-bye/peer-review/11-office-hours](../generated/workflows/audio/albums/nill-bye/peer-review.md)** | lo-fi **86**, seed **23** | `11 - Office Hours` | Extra help for a failing brand |
| **[audio/albums/nill-bye/peer-review/12-grant-denied](../generated/workflows/audio/albums/nill-bye/peer-review.md)** | boom-bap **88**, `[spoken word]` intro, seed **29** | `12 - Grant Denied` | No funding for feelings |
| **[audio/albums/nill-bye/peer-review/13-contamination](../generated/workflows/audio/albums/nill-bye/peer-review.md)** | trap **140**, seed **31** | `13 - Contamination` | Club talk leaked into the sample |
| **[audio/albums/nill-bye/peer-review/14-double-blind](../generated/workflows/audio/albums/nill-bye/peer-review.md)** | boom-bap **92**, seed **37** | `14 - Double Blind` | Even the booth knows you are faking |
| **[audio/albums/nill-bye/peer-review/15-replicate](../generated/workflows/audio/albums/nill-bye/peer-review.md)** | boom-bap **88**, seed **7** | `15 - Replicate or Retract` | Cannot reproduce the night |

#### Citation Needed (`audio/albums/nill-bye/citation-needed/`)

Same invented vocal. Wider beds (jazz hop through folk) and diss angles. Not trap/EDM. Full album: `./scripts/manage.sh album-render --album nill-bye/citation-needed`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **[audio/albums/nill-bye/citation-needed/01-citation-needed](../generated/workflows/audio/albums/nill-bye/citation-needed.md)** | jazz hop **90**, seed **41** | `01 - Citation Needed` | Claims with no source |
| **[audio/albums/nill-bye/citation-needed/02-p-hacking](../generated/workflows/audio/albums/nill-bye/citation-needed.md)** | g-funk **98**, seed **43** | `02 - P-Hacking` | Cherry-picked night |
| **[audio/albums/nill-bye/citation-needed/03-null-result](../generated/workflows/audio/albums/nill-bye/citation-needed.md)** | reggae **92**, seed **47** | `03 - Null Result` | Flex found nothing |
| **[audio/albums/nill-bye/citation-needed/04-expired-reagent](../generated/workflows/audio/albums/nill-bye/citation-needed.md)** | neo-soul **84**, seed **53** | `04 - Expired Reagent` | Cool past the date |
| **[audio/albums/nill-bye/citation-needed/05-lab-safety](../generated/workflows/audio/albums/nill-bye/citation-needed.md)** | rap rock **168**, seed **59** | `05 - Lab Safety` | Skipped the goggles |
| **[audio/albums/nill-bye/citation-needed/06-rumor-mill](../generated/workflows/audio/albums/nill-bye/citation-needed.md)** | industrial **108**, seed **61** | `06 - Rumor Mill` | Gossip vs measurement |
| **[audio/albums/nill-bye/citation-needed/07-gym-selfie](../generated/workflows/audio/albums/nill-bye/citation-needed.md)** | afrobeat **110**, seed **67** | `07 - Gym Selfie` | Pose vs work |
| **[audio/albums/nill-bye/citation-needed/08-rented-drip](../generated/workflows/audio/albums/nill-bye/citation-needed.md)** | synthwave **104**, seed **71** | `08 - Rented Drip` | Costume cool |
| **[audio/albums/nill-bye/citation-needed/09-clout-diet](../generated/workflows/audio/albums/nill-bye/citation-needed.md)** | trip-hop **86**, seed **73** | `09 - Clout Diet` | Likes as calories |
| **[audio/albums/nill-bye/citation-needed/10-mood-forecast](../generated/workflows/audio/albums/nill-bye/citation-needed.md)** | cinematic **76**, seed **79** | `10 - Mood Forecast` | Weather of feelings |
| **[audio/albums/nill-bye/citation-needed/11-algorithm](../generated/workflows/audio/albums/nill-bye/citation-needed.md)** | funk **114**, seed **83** | `11 - Algorithm` | Chasing the feed |
| **[audio/albums/nill-bye/citation-needed/12-story-time](../generated/workflows/audio/albums/nill-bye/citation-needed.md)** | blues **74**, `[spoken word]` intro, seed **89** | `12 - Story Time` | Bedtime rumor |
| **[audio/albums/nill-bye/citation-needed/13-caption](../generated/workflows/audio/albums/nill-bye/citation-needed.md)** | chiptune **100**, seed **97** | `13 - Caption vs Data` | Caption vs data |
| **[audio/albums/nill-bye/citation-needed/14-energy-drink](../generated/workflows/audio/albums/nill-bye/citation-needed.md)** | brass band **120**, seed **101** | `14 - Energy Drink` | Fake fuel |
| **[audio/albums/nill-bye/citation-needed/15-campfire](../generated/workflows/audio/albums/nill-bye/citation-needed.md)** | folk **82**, seed **103** | `15 - Campfire Rumor` | Campfire rumor |

#### False Drop (`audio/albums/nill-bye/false-drop/`)

Same dry booth. Rap over club beds (no autotune). Full album: `./scripts/manage.sh album-render --album nill-bye/false-drop`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **[audio/albums/nill-bye/false-drop/01-false-drop](../generated/workflows/audio/albums/nill-bye/false-drop.md)** | dark trap **140**, seed **107** | `01 - False Drop` | Fake drop, no method |
| **[audio/albums/nill-bye/false-drop/02-velvet-rope](../generated/workflows/audio/albums/nill-bye/false-drop.md)** | festival trap **150**, seed **109** | `02 - Velvet Rope` | VIP pose, empty list |
| **[audio/albums/nill-bye/false-drop/03-fog-machine](../generated/workflows/audio/albums/nill-bye/false-drop.md)** | rage **148**, seed **113** | `03 - Fog Machine` | Fog for a missing show |
| **[audio/albums/nill-bye/false-drop/04-guest-list](../generated/workflows/audio/albums/nill-bye/false-drop.md)** | phonk **132**, seed **127** | `04 - Guest List` | Name not on the list |
| **[audio/albums/nill-bye/false-drop/05-sparkler](../generated/workflows/audio/albums/nill-bye/false-drop.md)** | trap **145**, seed **131** | `05 - Sparkler Science` | Sparkler science |
| **[audio/albums/nill-bye/false-drop/06-bottle-service](../generated/workflows/audio/albums/nill-bye/false-drop.md)** | house **126**, seed **137** | `06 - Bottle Service` | Rented bottles |
| **[audio/albums/nill-bye/false-drop/07-strobe-claim](../generated/workflows/audio/albums/nill-bye/false-drop.md)** | techno **132**, seed **139** | `07 - Strobe Claim` | Strobe, no substance |
| **[audio/albums/nill-bye/false-drop/08-amen-rumor](../generated/workflows/audio/albums/nill-bye/false-drop.md)** | drum and bass **174**, seed **149** | `08 - Amen Rumor` | Fast rumor, empty bar |
| **[audio/albums/nill-bye/false-drop/09-wobble-alibi](../generated/workflows/audio/albums/nill-bye/false-drop.md)** | dubstep **140**, seed **151** | `09 - Wobble Alibi` | Alibi in the wobble |
| **[audio/albums/nill-bye/false-drop/10-supersaw-flex](../generated/workflows/audio/albums/nill-bye/false-drop.md)** | future bass **148**, seed **157** | `10 - Supersaw Flex` | Flex is a saw patch |
| **[audio/albums/nill-bye/false-drop/11-laser-show](../generated/workflows/audio/albums/nill-bye/false-drop.md)** | electro house **128**, seed **163** | `11 - Laser Show` | Lights, no paper |
| **[audio/albums/nill-bye/false-drop/12-two-step](../generated/workflows/audio/albums/nill-bye/false-drop.md)** | UK garage **130**, seed **167** | `12 - Two-Step Alibi` | Two-step alibi |
| **[audio/albums/nill-bye/false-drop/13-jersey-bounce](../generated/workflows/audio/albums/nill-bye/false-drop.md)** | jersey club **140**, seed **173** | `13 - Jersey Bounce` | Bounce with no proof |
| **[audio/albums/nill-bye/false-drop/14-kick-split](../generated/workflows/audio/albums/nill-bye/false-drop.md)** | hardstyle **150**, seed **179** | `14 - Kick-Split Myth` | Kick-split myth |
| **[audio/albums/nill-bye/false-drop/15-uplift-rumor](../generated/workflows/audio/albums/nill-bye/false-drop.md)** | trance **138**, seed **181** | `15 - Uplifting Rumor` | Uplifting rumor |

#### Frozen Ercot (`audio/albums/nill-bye/frozen-ercot/`)

Same dry booth. Non-trap, non-EDM beds. Public-record satire of Abbott (punch up; no disability, race, or faith punch-down). Full album: `./scripts/manage.sh album-render --album nill-bye/frozen-ercot`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **[audio/albums/nill-bye/frozen-ercot/01-frozen-ercot](../generated/workflows/audio/albums/nill-bye/frozen-ercot.md)** | boom-bap **88**, seed **191** | `01 - Frozen Ercot` | Uri / ERCOT blame-shift |
| **[audio/albums/nill-bye/frozen-ercot/02-abject-failure](../generated/workflows/audio/albums/nill-bye/frozen-ercot.md)** | boom-bap **86**, `[spoken word]`, seed **193** | `02 - Abject Failure` | Uvalde delay, split message |
| **[audio/albums/nill-bye/frozen-ercot/03-six-week-clock](../generated/workflows/audio/albums/nill-bye/frozen-ercot.md)** | jazz hop **90**, seed **197** | `03 - Six Week Clock` | SB 8 bounty |
| **[audio/albums/nill-bye/frozen-ercot/04-no-bid-wire](../generated/workflows/audio/albums/nill-bye/frozen-ercot.md)** | industrial hip-hop **108**, seed **199** | `04 - No-Bid Wire` | OLS emergency procurement |
| **[audio/albums/nill-bye/frozen-ercot/05-gavel-theater](../generated/workflows/audio/albums/nill-bye/frozen-ercot.md)** | brass band **112**, seed **211** | `05 - Gavel Theater` | Paxton impeachment |
| **[audio/albums/nill-bye/frozen-ercot/06-property-hymn](../generated/workflows/audio/albums/nill-bye/frozen-ercot.md)** | folk **82**, seed **223** | `06 - Property Hymn` | No-income-tax vs levy |
| **[audio/albums/nill-bye/frozen-ercot/07-voucher-raid](../generated/workflows/audio/albums/nill-bye/frozen-ercot.md)** | country **100**, seed **227** | `07 - Voucher Raid` | ESA / Yass primaries |
| **[audio/albums/nill-bye/frozen-ercot/08-uninsured-blues](../generated/workflows/audio/albums/nill-bye/frozen-ercot.md)** | blues **74**, seed **229** | `08 - Uninsured Blues` | Medicaid non-expansion |
| **[audio/albums/nill-bye/frozen-ercot/09-locked-stacks](../generated/workflows/audio/albums/nill-bye/frozen-ercot.md)** | lo-fi **86**, seed **233** | `09 - Locked Stacks` | Book / DEI pull-lists |
| **[audio/albums/nill-bye/frozen-ercot/10-mask-order](../generated/workflows/audio/albums/nill-bye/frozen-ercot.md)** | neo-soul **84**, seed **239** | `10 - Mask Order` | GA-34 preemption |
| **[audio/albums/nill-bye/frozen-ercot/11-mid-decade-map](../generated/workflows/audio/albums/nill-bye/frozen-ercot.md)** | chiptune **100**, seed **241** | `11 - Mid Decade Map` | Mid-decade remap |
| **[audio/albums/nill-bye/frozen-ercot/12-rack-tax](../generated/workflows/audio/albums/nill-bye/frozen-ercot.md)** | synthwave **104**, seed **251** | `12 - Rack Tax` | Data-center boom then brake |
| **[audio/albums/nill-bye/frozen-ercot/13-wudu-letter](../generated/workflows/audio/albums/nill-bye/frozen-ercot.md)** | gospel **78**, seed **257** | `13 - Wudu Letter` | Airport rinse smear, called out |
| **[audio/albums/nill-bye/frozen-ercot/14-fourth-term](../generated/workflows/audio/albums/nill-bye/frozen-ercot.md)** | cinematic **76**, seed **263** | `14 - Fourth Term` | Unprecedented fourth lap |
| **[audio/albums/nill-bye/frozen-ercot/15-campus-cordon](../generated/workflows/audio/albums/nill-bye/frozen-ercot.md)** | rap rock **168**, seed **269** | `15 - Campus Cordon` | UT troopers vs protest |

#### Lone Star Tab (`audio/albums/nill-bye/lone-star-tab/`)

Same dry booth. Rap over club beds (no autotune). Same punch-up rule. Full album: `./scripts/manage.sh album-render --album nill-bye/lone-star-tab`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **[audio/albums/nill-bye/lone-star-tab/01-lone-star-tab](../generated/workflows/audio/albums/nill-bye/lone-star-tab.md)** | dark trap **140**, seed **271** | `01 - Lone Star Tab` | OLS forever budget |
| **[audio/albums/nill-bye/lone-star-tab/02-river-buoy](../generated/workflows/audio/albums/nill-bye/lone-star-tab.md)** | rage **148**, seed **277** | `02 - River Buoy` | Buoys and wire as cruelty |
| **[audio/albums/nill-bye/lone-star-tab/03-bus-receipt](../generated/workflows/audio/albums/nill-bye/lone-star-tab.md)** | phonk **132**, seed **281** | `03 - Bus Receipt` | People mailed as a presser |
| **[audio/albums/nill-bye/lone-star-tab/04-guard-detail](../generated/workflows/audio/albums/nill-bye/lone-star-tab.md)** | trap **145**, seed **283** | `04 - Guard Detail` | Guard deaths on state orders |
| **[audio/albums/nill-bye/lone-star-tab/05-chase-wreck](../generated/workflows/audio/albums/nill-bye/lone-star-tab.md)** | house **126**, seed **293** | `05 - Chase Wreck` | OLS pursuit deaths |
| **[audio/albums/nill-bye/lone-star-tab/06-frequency-drop](../generated/workflows/audio/albums/nill-bye/lone-star-tab.md)** | drum and bass **174**, seed **307** | `06 - Frequency Drop` | 20,000 MW load-shed |
| **[audio/albums/nill-bye/lone-star-tab/07-permitless](../generated/workflows/audio/albums/nill-bye/lone-star-tab.md)** | jersey club **140**, seed **311** | `07 - Permitless` | HB 1927 |
| **[audio/albums/nill-bye/lone-star-tab/08-trigger-clock](../generated/workflows/audio/albums/nill-bye/lone-star-tab.md)** | future bass **148**, seed **313** | `08 - Trigger Clock` | HB 1280 felony delay |
| **[audio/albums/nill-bye/lone-star-tab/09-disaster-stamp](../generated/workflows/audio/albums/nill-bye/lone-star-tab.md)** | techno **132**, `[spoken word]`, seed **317** | `09 - Disaster Stamp` | Monthly border emergency |
| **[audio/albums/nill-bye/lone-star-tab/10-windmill-blame](../generated/workflows/audio/albums/nill-bye/lone-star-tab.md)** | dubstep **140**, seed **331** | `10 - Windmill Blame` | Fox clip vs FERC mix |
| **[audio/albums/nill-bye/lone-star-tab/11-yass-primary](../generated/workflows/audio/albums/nill-bye/lone-star-tab.md)** | electro house **128**, seed **337** | `11 - Yass Primary` | Out-of-state cash primaries |
| **[audio/albums/nill-bye/lone-star-tab/12-hold-request](../generated/workflows/audio/albums/nill-bye/lone-star-tab.md)** | UK garage **130**, seed **347** | `12 - Hold Request` | ICE extradition fight |
| **[audio/albums/nill-bye/lone-star-tab/13-sharia-plank](../generated/workflows/audio/albums/nill-bye/lone-star-tab.md)** | hardstyle **150**, seed **349** | `13 - Sharia Plank` | Convention scare, empty docket |
| **[audio/albums/nill-bye/lone-star-tab/14-invasion-hymn](../generated/workflows/audio/albums/nill-bye/lone-star-tab.md)** | trance **138**, seed **353** | `14 - Invasion Hymn` | War-word as appropriation |
| **[audio/albums/nill-bye/lone-star-tab/15-demolish-hook](../generated/workflows/audio/albums/nill-bye/lone-star-tab.md)** | festival trap **150**, seed **359** | `15 - Demolish Hook` | “Demolish” closer |

#### Thirty Four Counts (`audio/albums/nill-bye/thirty-four-counts/`)

Same dry booth. Non-trap, non-EDM beds. Public-record satire of Trump (punch up; no disability, race, faith, or children as the joke). Full album: `./scripts/manage.sh album-render --album nill-bye/thirty-four-counts`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **[audio/albums/nill-bye/thirty-four-counts/01-thirty-four-counts](../generated/workflows/audio/albums/nill-bye/thirty-four-counts.md)** | boom-bap **88**, seed **367** | `01 - Thirty Four Counts` | 34 felony records counts |
| **[audio/albums/nill-bye/thirty-four-counts/02-one-eighty-seven](../generated/workflows/audio/albums/nill-bye/thirty-four-counts.md)** | boom-bap **86**, `[spoken word]`, seed **373** | `02 - One Eighty Seven` | Jan 6 idle minutes |
| **[audio/albums/nill-bye/thirty-four-counts/03-eleven-seven-eighty](../generated/workflows/audio/albums/nill-bye/thirty-four-counts.md)** | jazz hop **90**, seed **379** | `03 - Eleven Seven Eighty` | Raffensperger tape |
| **[audio/albums/nill-bye/thirty-four-counts/04-fake-electors](../generated/workflows/audio/albums/nill-bye/thirty-four-counts.md)** | industrial hip-hop **108**, seed **383** | `04 - Fake Electors` | Seven slates |
| **[audio/albums/nill-bye/thirty-four-counts/05-bathroom-boxes](../generated/workflows/audio/albums/nill-bye/thirty-four-counts.md)** | brass band **112**, seed **389** | `05 - Bathroom Boxes` | Mar-a-Lago storage |
| **[audio/albums/nill-bye/thirty-four-counts/06-statement-of-worth](../generated/workflows/audio/albums/nill-bye/thirty-four-counts.md)** | folk **82**, seed **397** | `06 - Statement of Worth` | Inflated SFSs |
| **[audio/albums/nill-bye/thirty-four-counts/07-university-tab](../generated/workflows/audio/albums/nill-bye/thirty-four-counts.md)** | country **100**, seed **401** | `07 - University Tab` | $25M seminar settlement |
| **[audio/albums/nill-bye/thirty-four-counts/08-ukraine-hold](../generated/workflows/audio/albums/nill-bye/thirty-four-counts.md)** | blues **74**, seed **409** | `08 - Ukraine Hold` | Aid freeze, first impeachment |
| **[audio/albums/nill-bye/thirty-four-counts/09-travel-memo](../generated/workflows/audio/albums/nill-bye/thirty-four-counts.md)** | lo-fi **86**, seed **419** | `09 - Travel Memo` | EO 13769 roster |
| **[audio/albums/nill-bye/thirty-four-counts/10-zero-tolerance](../generated/workflows/audio/albums/nill-bye/thirty-four-counts.md)** | neo-soul **84**, seed **421** | `10 - Zero Tolerance` | Family-separation memo |
| **[audio/albums/nill-bye/thirty-four-counts/11-census-question](../generated/workflows/audio/albums/nill-bye/thirty-four-counts.md)** | chiptune **100**, seed **431** | `11 - Census Question` | Citizenship-box pretext |
| **[audio/albums/nill-bye/thirty-four-counts/12-paris-walkout](../generated/workflows/audio/albums/nill-bye/thirty-four-counts.md)** | synthwave **104**, seed **433** | `12 - Paris Walkout` | Paris Agreement letter |
| **[audio/albums/nill-bye/thirty-four-counts/13-emoluments-suite](../generated/workflows/audio/albums/nill-bye/thirty-four-counts.md)** | gospel **78**, seed **439** | `13 - Emoluments Suite` | DC hotel while in office |
| **[audio/albums/nill-bye/thirty-four-counts/14-seven-fifty](../generated/workflows/audio/albums/nill-bye/thirty-four-counts.md)** | cinematic **76**, seed **443** | `14 - Seven Fifty` | Reported $750 federal line |
| **[audio/albums/nill-bye/thirty-four-counts/15-carroll-tab](../generated/workflows/audio/albums/nill-bye/thirty-four-counts.md)** | rap rock **168**, seed **449** | `15 - Carroll Tab` | Defamation after a finding |

#### Pardon Flood (`audio/albums/nill-bye/pardon-flood/`)

Same dry booth. Rap over club beds (no autotune). Same punch-up rule. Full album: `./scripts/manage.sh album-render --album nill-bye/pardon-flood`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **[audio/albums/nill-bye/pardon-flood/01-pardon-flood](../generated/workflows/audio/albums/nill-bye/pardon-flood.md)** | dark trap **140**, `[spoken word]`, seed **457** | `01 - Pardon Flood` | Day-one Jan 6 clemency |
| **[audio/albums/nill-bye/pardon-flood/02-ieepa-wreck](../generated/workflows/audio/albums/nill-bye/pardon-flood.md)** | rage **148**, seed **461** | `02 - Ieepa Wreck` | IEEPA tariffs 6–3 |
| **[audio/albums/nill-bye/pardon-flood/03-gold-card](../generated/workflows/audio/albums/nill-bye/pardon-flood.md)** | phonk **132**, seed **463** | `03 - Gold Card` | $1M residency SKU |
| **[audio/albums/nill-bye/pardon-flood/04-memecoin-tab](../generated/workflows/audio/albums/nill-bye/pardon-flood.md)** | trap **145**, seed **467** | `04 - Memecoin Tab` | Pre-oath token float |
| **[audio/albums/nill-bye/pardon-flood/05-east-wing-wreck](../generated/workflows/audio/albums/nill-bye/pardon-flood.md)** | house **126**, seed **479** | `05 - East Wing Wreck` | Ballroom teardown |
| **[audio/albums/nill-bye/pardon-flood/06-metro-surge](../generated/workflows/audio/albums/nill-bye/pardon-flood.md)** | drum and bass **174**, seed **487** | `06 - Metro Surge` | 2026 enforcement wave |
| **[audio/albums/nill-bye/pardon-flood/07-due-process](../generated/workflows/audio/albums/nill-bye/pardon-flood.md)** | jersey club **140**, seed **491** | `07 - Due Process` | Withholding skipped |
| **[audio/albums/nill-bye/pardon-flood/08-kennedy-plaque](../generated/workflows/audio/albums/nill-bye/pardon-flood.md)** | future bass **148**, seed **499** | `08 - Kennedy Plaque` | Organic-statute rename |
| **[audio/albums/nill-bye/pardon-flood/09-birthright-order](../generated/workflows/audio/albums/nill-bye/pardon-flood.md)** | techno **132**, seed **503** | `09 - Birthright Order` | 14th Amendment EO |
| **[audio/albums/nill-bye/pardon-flood/10-cook-firing](../generated/workflows/audio/albums/nill-bye/pardon-flood.md)** | dubstep **140**, seed **509** | `10 - Cook Firing` | Fed-governor purge try |
| **[audio/albums/nill-bye/pardon-flood/11-inspector-purge](../generated/workflows/audio/albums/nill-bye/pardon-flood.md)** | electro house **128**, seed **521** | `11 - Inspector Purge` | IG class sweep |
| **[audio/albums/nill-bye/pardon-flood/12-law-firm-order](../generated/workflows/audio/albums/nill-bye/pardon-flood.md)** | UK garage **130**, seed **523** | `12 - Law Firm Order` | Counsel-punishment EO |
| **[audio/albums/nill-bye/pardon-flood/13-visa-ticket](../generated/workflows/audio/albums/nill-bye/pardon-flood.md)** | hardstyle **150**, seed **541** | `13 - Visa Ticket` | $100k H-1B fee |
| **[audio/albums/nill-bye/pardon-flood/14-shadow-docket](../generated/workflows/audio/albums/nill-bye/pardon-flood.md)** | trance **138**, seed **547** | `14 - Shadow Docket` | Emergency-petition pile |
| **[audio/albums/nill-bye/pardon-flood/15-immunity-hymn](../generated/workflows/audio/albums/nill-bye/pardon-flood.md)** | festival trap **150**, seed **557** | `15 - Immunity Hymn` | Official-act structure |

#### Winterize Wells (`audio/albums/nill-bye/winterize-wells/`)

Same dry booth. Non-trap, non-EDM beds. Builder bars: methods and statutes, no roast target. Full album: `./scripts/manage.sh album-render --album nill-bye/winterize-wells`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **[audio/albums/nill-bye/winterize-wells/01-winterize-wells](../generated/workflows/audio/albums/nill-bye/winterize-wells.md)** | boom-bap **88**, seed **563** | `01 - Winterize Wells` | NERC wellhead jackets |
| **[audio/albums/nill-bye/winterize-wells/02-registered-report](../generated/workflows/audio/albums/nill-bye/winterize-wells.md)** | boom-bap **86**, `[spoken word]`, seed **569** | `02 - Registered Report` | Preregister the protocol |
| **[audio/albums/nill-bye/winterize-wells/03-named-uncertainty](../generated/workflows/audio/albums/nill-bye/winterize-wells.md)** | jazz hop **90**, seed **571** | `03 - Named Uncertainty` | Print the interval |
| **[audio/albums/nill-bye/winterize-wells/04-scif-only](../generated/workflows/audio/albums/nill-bye/winterize-wells.md)** | industrial hip-hop **108**, seed **577** | `04 - Scif Only` | Compartment the paper |
| **[audio/albums/nill-bye/winterize-wells/05-hearing-first](../generated/workflows/audio/albums/nill-bye/winterize-wells.md)** | brass band **112**, seed **587** | `05 - Hearing First` | Withholding, then plane |
| **[audio/albums/nill-bye/winterize-wells/06-keep-the-match](../generated/workflows/audio/albums/nill-bye/winterize-wells.md)** | folk **82**, seed **593** | `06 - Keep the Match` | Family-unity case-id |
| **[audio/albums/nill-bye/winterize-wells/07-honest-census](../generated/workflows/audio/albums/nill-bye/winterize-wells.md)** | country **100**, seed **599** | `07 - Honest Census` | Count, do not chill |
| **[audio/albums/nill-bye/winterize-wells/08-paris-seat](../generated/workflows/audio/albums/nill-bye/winterize-wells.md)** | blues **74**, seed **601** | `08 - Paris Seat` | Stay for the NDC |
| **[audio/albums/nill-bye/winterize-wells/09-qualified-divest](../generated/workflows/audio/albums/nill-bye/winterize-wells.md)** | lo-fi **86**, seed **607** | `09 - Qualified Divest` | Till off the desk |
| **[audio/albums/nill-bye/winterize-wells/10-return-pdf](../generated/workflows/audio/albums/nill-bye/winterize-wells.md)** | neo-soul **84**, seed **613** | `10 - Return Pdf` | Disclosure stack |
| **[audio/albums/nill-bye/winterize-wells/11-casework-screen](../generated/workflows/audio/albums/nill-bye/winterize-wells.md)** | chiptune **100**, seed **617** | `11 - Casework Screen` | Person-level file |
| **[audio/albums/nill-bye/winterize-wells/12-district-door](../generated/workflows/audio/albums/nill-bye/winterize-wells.md)** | synthwave **104**, seed **619** | `12 - District Door` | Fund the public door |
| **[audio/albums/nill-bye/winterize-wells/13-levy-in-code](../generated/workflows/audio/albums/nill-bye/winterize-wells.md)** | gospel **78**, seed **631** | `13 - Levy In Code` | Cut the roll in statute |
| **[audio/albums/nill-bye/winterize-wells/14-fourteenth-clause](../generated/workflows/audio/albums/nill-bye/winterize-wells.md)** | cinematic **76**, seed **641** | `14 - Fourteenth Clause` | Keep the citizenship sentence |
| **[audio/albums/nill-bye/winterize-wells/15-one-college](../generated/workflows/audio/albums/nill-bye/winterize-wells.md)** | rap rock **168**, seed **643** | `15 - One College` | One certified slate |

#### Duty Switch (`audio/albums/nill-bye/duty-switch/`)

Same dry booth. Rap over club beds (no autotune). Same builder rule. Full album: `./scripts/manage.sh album-render --album nill-bye/duty-switch`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **[audio/albums/nill-bye/duty-switch/01-duty-switch](../generated/workflows/audio/albums/nill-bye/duty-switch.md)** | dark trap **140**, `[spoken word]`, seed **647** | `01 - Duty Switch` | Switch at minute one |
| **[audio/albums/nill-bye/duty-switch/02-article-one](../generated/workflows/audio/albums/nill-bye/duty-switch.md)** | rage **148**, seed **653** | `02 - Article One` | Tariffs via a bill |
| **[audio/albums/nill-bye/duty-switch/03-for-cause-lock](../generated/workflows/audio/albums/nill-bye/duty-switch.md)** | phonk **132**, seed **659** | `03 - For-Cause Lock` | Fed Act lock |
| **[audio/albums/nill-bye/duty-switch/04-ig-notice](../generated/workflows/audio/albums/nill-bye/duty-switch.md)** | trap **145**, seed **661** | `04 - Ig Notice` | IGA notice-and-reason |
| **[audio/albums/nill-bye/duty-switch/05-counsel-stays](../generated/workflows/audio/albums/nill-bye/duty-switch.md)** | house **126**, seed **673** | `05 - Counsel Stays` | Sixth Amendment counsel |
| **[audio/albums/nill-bye/duty-switch/06-prevailing-wage](../generated/workflows/audio/albums/nill-bye/duty-switch.md)** | drum and bass **174**, seed **677** | `06 - Prevailing Wage` | H-1B labor file |
| **[audio/albums/nill-bye/duty-switch/07-merits-syllabus](../generated/workflows/audio/albums/nill-bye/duty-switch.md)** | jersey club **140**, seed **683** | `07 - Merits Syllabus` | Day-calendar reasons |
| **[audio/albums/nill-bye/duty-switch/08-unofficial-sort](../generated/workflows/audio/albums/nill-bye/duty-switch.md)** | future bass **148**, seed **691** | `08 - Unofficial Sort` | Three-room immunity |
| **[audio/albums/nill-bye/duty-switch/09-clemency-file](../generated/workflows/audio/albums/nill-bye/duty-switch.md)** | techno **132**, seed **701** | `09 - Clemency File` | Case-by-case mercy |
| **[audio/albums/nill-bye/duty-switch/10-congress-the-wing](../generated/workflows/audio/albums/nill-bye/duty-switch.md)** | dubstep **140**, seed **709** | `10 - Congress the Wing` | Act before rubble |
| **[audio/albums/nill-bye/duty-switch/11-tie-the-island](../generated/workflows/audio/albums/nill-bye/duty-switch.md)** | electro house **128**, seed **719** | `11 - Tie the Island` | Neighbor watts |
| **[audio/albums/nill-bye/duty-switch/12-decade-lines](../generated/workflows/audio/albums/nill-bye/duty-switch.md)** | UK garage **130**, seed **727** | `12 - Decade Lines` | Map after a census |
| **[audio/albums/nill-bye/duty-switch/13-ratepayer-bus](../generated/workflows/audio/albums/nill-bye/duty-switch.md)** | hardstyle **150**, seed **733** | `13 - Ratepayer Bus` | Barns pay the draw |
| **[audio/albums/nill-bye/duty-switch/14-open-quad](../generated/workflows/audio/albums/nill-bye/duty-switch.md)** | trance **138**, seed **739** | `14 - Open Quad` | Forum first |
| **[audio/albums/nill-bye/duty-switch/15-wrench-the-tap](../generated/workflows/audio/albums/nill-bye/duty-switch.md)** | festival trap **150**, seed **743** | `15 - Wrench the Tap` | Lead-line replacement |

Cover still in a later Klein session. Do not co-resident with LTX / Wan / Klein.

---

### 180s Drive-through EDM examples

Eighty-five extra full-track graphs under **`_lab/audio/albums/drive-through/<album>/`**. Same AIO, sampler, occupancy **audio**. App **Duration (seconds)** defaults to **180**. Queue a numbered track **on its own**, or `album-render --album drive-through/<album-slug>`. SaveAudio stem is **`NN - Song Title`**.

Fictional act only: **Drive-through** (hardcore, pure of heart) playing a **live bass DJ set**. Original **warped hybrid-trap EDM** (hybrid trap, riddim, tearout, brostep, wave bass, color bass, drumstep, dirty dubstep, neuro bass, chest/dirty bass — not techno, not big room, not progressive house). No living-DJ names. No famous-hook paraphrases. Eighty-three takes lock `instrumental, no vocals, no singing, no choir, no vocal chops` (App **Vocal / instrumental** = instrumental). Two takes are sparse DJ-shout treats (`wide open`, `second wave`): App mode **vocal**, one 1–2 word `[chorus]` chop, no `[verse]`. Arrangement scores are production cues in `[inst]` blocks — drop first, hard warpy drops, trap drums, chest-sub / 808, no quiet dips, unique flow per take — not a Nill Bye verse/chorus loop and not a melody-drop-break-drop skeleton. Some takes add dual-action pedal bass under rolling hats. Phase2, phase3, and phase4 graphs keep that ACE topology but vary Comfy node placement across five layouts (`column`, `wide-stage`, `stacked-tower`, `prompt-left`, `output-rail`). ACE-Step timbre is invented. Human selection and edit required before any release.

This is **not** the Nill Bye trap/EDM pack. Those graphs are rap **over** club beds with a dry booth. Drive-through is dance EDM (mostly instrumental).

Catalog order is the recommended live-set queue (each graph still Queues alone).

#### Hour 1 (`audio/albums/drive-through/hour-1/`)

Hour 1 of the live bass set. Full album: `./scripts/manage.sh album-render --album drive-through/hour-1`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **[audio/albums/drive-through/hour-1/01-night-window](../generated/workflows/audio/albums/drive-through/hour-1.md)** | hybrid trap **145**, seed **193** | `01 - Night Window` | Drop-first hybrid trap warp |
| **[audio/albums/drive-through/hour-1/02-open-lane](../generated/workflows/audio/albums/drive-through/hour-1.md)** | riddim **152**, seed **191** | `02 - Open Lane` | Drop-first riddim warp |
| **[audio/albums/drive-through/hour-1/03-exit-seven](../generated/workflows/audio/albums/drive-through/hour-1.md)** | tearout **142**, seed **233** | `03 - Exit Seven` | Drop-first tearout warp |
| **[audio/albums/drive-through/hour-1/04-skyline-pass](../generated/workflows/audio/albums/drive-through/hour-1.md)** | brostep **145**, seed **199** | `04 - Skyline Pass` | Drop-first brostep warp |
| **[audio/albums/drive-through/hour-1/05-on-ramp](../generated/workflows/audio/albums/drive-through/hour-1.md)** | wave bass **155**, seed **197** | `05 - On-Ramp` | Drop-first wave bass warp |
| **[audio/albums/drive-through/hour-1/06-tunnel-bass](../generated/workflows/audio/albums/drive-through/hour-1.md)** | dirty bass **150**, seed **257** | `06 - Tunnel Bass` | Drop-first dirty bass warp |
| **[audio/albums/drive-through/hour-1/07-wide-open](../generated/workflows/audio/albums/drive-through/hour-1.md)** | color bass **150**, seed **239** | `07 - Wide Open` | **DJ shout treat.** Drop-first color bass warp |
| **[audio/albums/drive-through/hour-1/08-overpass](../generated/workflows/audio/albums/drive-through/hour-1.md)** | dirty dubstep **150**, seed **227** | `08 - Overpass` | Drop-first dirty dubstep warp |
| **[audio/albums/drive-through/hour-1/09-second-wave](../generated/workflows/audio/albums/drive-through/hour-1.md)** | hybrid trap **150**, seed **241** | `09 - Second Wave` | **DJ shout treat.** Drop-first hybrid trap warp |
| **[audio/albums/drive-through/hour-1/10-freight-pulse](../generated/workflows/audio/albums/drive-through/hour-1.md)** | drumstep **176**, seed **211** | `10 - Freight Pulse` | Drop-first drumstep warp |
| **[audio/albums/drive-through/hour-1/11-keep-going](../generated/workflows/audio/albums/drive-through/hour-1.md)** | neuro bass **170**, seed **251** | `11 - Keep Going` | Drop-first neuro bass warp |
| **[audio/albums/drive-through/hour-1/12-horizon-kick](../generated/workflows/audio/albums/drive-through/hour-1.md)** | tearout **165**, seed **263** | `12 - Horizon Kick` | Drop-first tearout warp |
| **[audio/albums/drive-through/hour-1/13-clean-wreckage](../generated/workflows/audio/albums/drive-through/hour-1.md)** | brostep **150**, seed **269** | `13 - Clean Wreckage` | Drop-first brostep warp |
| **[audio/albums/drive-through/hour-1/14-heart-lane](../generated/workflows/audio/albums/drive-through/hour-1.md)** | wave bass **145**, seed **223** | `14 - Heart Lane` | Drop-first wave bass warp |
| **[audio/albums/drive-through/hour-1/15-dawn-receipt](../generated/workflows/audio/albums/drive-through/hour-1.md)** | chest bass **140**, seed **229** | `15 - Dawn Receipt` | Drop-first chest bass warp |

#### Hour 2 (`audio/albums/drive-through/hour-2/`)

Hour 2 of the live bass set. Full album: `./scripts/manage.sh album-render --album drive-through/hour-2`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **[audio/albums/drive-through/hour-2/01-rumble-strip](../generated/workflows/audio/albums/drive-through/hour-2.md)** | hybrid trap **140**, seed **271** | `01 - Rumble Strip` | Drop-first hybrid trap warp |
| **[audio/albums/drive-through/hour-2/02-low-lane](../generated/workflows/audio/albums/drive-through/hour-2.md)** | riddim **144**, seed **277** | `02 - Low Lane` | Drop-first riddim warp |
| **[audio/albums/drive-through/hour-2/03-warm-merge](../generated/workflows/audio/albums/drive-through/hour-2.md)** | wave bass **148**, seed **281** | `03 - Warm Merge` | Drop-first wave bass warp |
| **[audio/albums/drive-through/hour-2/04-colour-span](../generated/workflows/audio/albums/drive-through/hour-2.md)** | color bass **150**, seed **283** | `04 - Colour Span` | Drop-first color bass warp |
| **[audio/albums/drive-through/hour-2/05-garage-ticket](../generated/workflows/audio/albums/drive-through/hour-2.md)** | festival trap **140**, seed **293** | `05 - Garage Ticket` | Drop-first festival trap warp |
| **[audio/albums/drive-through/hour-2/06-liquid-grade](../generated/workflows/audio/albums/drive-through/hour-2.md)** | drumstep **174**, seed **307** | `06 - Liquid Grade` | Drop-first drumstep warp |
| **[audio/albums/drive-through/hour-2/07-jump-bay](../generated/workflows/audio/albums/drive-through/hour-2.md)** | brostep **150**, seed **311** | `07 - Jump Bay` | Drop-first brostep warp |
| **[audio/albums/drive-through/hour-2/08-psy-median](../generated/workflows/audio/albums/drive-through/hour-2.md)** | neuro bass **145**, seed **313** | `08 - Psy Median` | Drop-first neuro bass warp |
| **[audio/albums/drive-through/hour-2/09-groove-mile](../generated/workflows/audio/albums/drive-through/hour-2.md)** | hybrid trap **144**, seed **317** | `09 - Groove Mile` | Drop-first hybrid trap warp |
| **[audio/albums/drive-through/hour-2/10-donk-ramp](../generated/workflows/audio/albums/drive-through/hour-2.md)** | tearout **150**, seed **331** | `10 - Donk Ramp` | Drop-first tearout warp |
| **[audio/albums/drive-through/hour-2/11-bounce-booth](../generated/workflows/audio/albums/drive-through/hour-2.md)** | chest bass **140**, seed **337** | `11 - Bounce Booth` | Drop-first chest bass warp |
| **[audio/albums/drive-through/hour-2/12-toll-growl](../generated/workflows/audio/albums/drive-through/hour-2.md)** | riddim **150**, seed **347** | `12 - Toll Growl` | Drop-first riddim warp |
| **[audio/albums/drive-through/hour-2/13-night-oil](../generated/workflows/audio/albums/drive-through/hour-2.md)** | hybrid trap **142**, seed **349** | `13 - Night Oil` | Drop-first hybrid trap warp |
| **[audio/albums/drive-through/hour-2/14-chest-pass](../generated/workflows/audio/albums/drive-through/hour-2.md)** | dirty bass **150**, seed **353** | `14 - Chest Pass` | Drop-first dirty bass warp |
| **[audio/albums/drive-through/hour-2/15-sunrise-sub](../generated/workflows/audio/albums/drive-through/hour-2.md)** | wave bass **140**, seed **359** | `15 - Sunrise Sub` | Drop-first wave bass warp |

#### Headliner (`audio/albums/drive-through/headliner/`)

Hour 3 headliner. Node placement varies across five layouts. Full album: `./scripts/manage.sh album-render --album drive-through/headliner`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **[audio/albums/drive-through/headliner/01-lantern-merge](../generated/workflows/audio/albums/drive-through/headliner.md)** | hybrid trap **150**, seed **367** | `01 - Lantern Merge` | Drop-first hybrid trap warp |
| **[audio/albums/drive-through/headliner/02-firefly-lane](../generated/workflows/audio/albums/drive-through/headliner.md)** | color bass **152**, seed **373** | `02 - Firefly Lane` | Drop-first color bass warp |
| **[audio/albums/drive-through/headliner/03-canopy-bounce](../generated/workflows/audio/albums/drive-through/headliner.md)** | chest bass **148**, seed **379** | `03 - Canopy Bounce` | Drop-first chest bass warp |
| **[audio/albums/drive-through/headliner/04-grove-wreck](../generated/workflows/audio/albums/drive-through/headliner.md)** | riddim **150**, seed **383** | `04 - Grove Wreck` | Drop-first riddim warp |
| **[audio/albums/drive-through/headliner/05-moss-sub](../generated/workflows/audio/albums/drive-through/headliner.md)** | dirty bass **150**, seed **389** | `05 - Moss Sub` | Drop-first dirty bass warp |
| **[audio/albums/drive-through/headliner/06-fern-stack](../generated/workflows/audio/albums/drive-through/headliner.md)** | hybrid trap **155**, seed **397** | `06 - Fern Stack` | Drop-first hybrid trap warp |
| **[audio/albums/drive-through/headliner/07-pollen-kick](../generated/workflows/audio/albums/drive-through/headliner.md)** | drumstep **174**, seed **401** | `07 - Pollen Kick` | Drop-first drumstep warp |
| **[audio/albums/drive-through/headliner/08-cedar-growl](../generated/workflows/audio/albums/drive-through/headliner.md)** | tearout **150**, seed **409** | `08 - Cedar Growl` | Drop-first tearout warp |
| **[audio/albums/drive-through/headliner/09-moon-ramp](../generated/workflows/audio/albums/drive-through/headliner.md)** | wave bass **148**, seed **419** | `09 - Moon Ramp` | Drop-first wave bass warp |
| **[audio/albums/drive-through/headliner/10-trail-bounce](../generated/workflows/audio/albums/drive-through/headliner.md)** | color bass **150**, seed **421** | `10 - Trail Bounce` | Drop-first color bass warp |
| **[audio/albums/drive-through/headliner/11-dew-wreck](../generated/workflows/audio/albums/drive-through/headliner.md)** | neuro bass **172**, seed **431** | `11 - Dew Wreck` | Drop-first neuro bass warp |
| **[audio/albums/drive-through/headliner/12-sap-stack](../generated/workflows/audio/albums/drive-through/headliner.md)** | brostep **165**, seed **433** | `12 - Sap Stack` | Drop-first brostep warp |
| **[audio/albums/drive-through/headliner/13-glade-split](../generated/workflows/audio/albums/drive-through/headliner.md)** | dirty dubstep **150**, seed **439** | `13 - Glade Split` | Drop-first dirty dubstep warp |
| **[audio/albums/drive-through/headliner/14-root-chest](../generated/workflows/audio/albums/drive-through/headliner.md)** | chest bass **148**, seed **443** | `14 - Root Chest` | Drop-first chest bass warp |
| **[audio/albums/drive-through/headliner/15-ember-crest](../generated/workflows/audio/albums/drive-through/headliner.md)** | hybrid trap **165**, seed **449** | `15 - Ember Crest` | Drop-first hybrid trap warp |

#### Afterparty (`audio/albums/drive-through/afterparty/`)

Hour 4 afterparty. Node placement varies across five layouts. Full album: `./scripts/manage.sh album-render --album drive-through/afterparty`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **[audio/albums/drive-through/afterparty/01-brake-fade](../generated/workflows/audio/albums/drive-through/afterparty.md)** | dirty bass **150**, seed **457** | `01 - Brake Fade` | Drop-first dirty bass warp |
| **[audio/albums/drive-through/afterparty/02-diesel-hum](../generated/workflows/audio/albums/drive-through/afterparty.md)** | hybrid trap **152**, seed **461** | `02 - Diesel Hum` | Drop-first hybrid trap warp |
| **[audio/albums/drive-through/afterparty/03-axle-grind](../generated/workflows/audio/albums/drive-through/afterparty.md)** | tearout **155**, seed **463** | `03 - Axle Grind` | Drop-first tearout warp |
| **[audio/albums/drive-through/afterparty/04-weigh-station](../generated/workflows/audio/albums/drive-through/afterparty.md)** | brostep **158**, seed **467** | `04 - Weigh Station` | Drop-first brostep warp |
| **[audio/albums/drive-through/afterparty/05-black-ice](../generated/workflows/audio/albums/drive-through/afterparty.md)** | riddim **160**, seed **479** | `05 - Black Ice` | Drop-first riddim warp |
| **[audio/albums/drive-through/afterparty/06-high-beams](../generated/workflows/audio/albums/drive-through/afterparty.md)** | color bass **165**, seed **487** | `06 - High Beams` | Drop-first color bass warp |
| **[audio/albums/drive-through/afterparty/07-chain-hook](../generated/workflows/audio/albums/drive-through/afterparty.md)** | brostep **168**, seed **491** | `07 - Chain Hook` | Drop-first brostep warp |
| **[audio/albums/drive-through/afterparty/08-grit-plate](../generated/workflows/audio/albums/drive-through/afterparty.md)** | wave bass **150**, seed **499** | `08 - Grit Plate` | Drop-first wave bass warp |
| **[audio/albums/drive-through/afterparty/09-steel-grate](../generated/workflows/audio/albums/drive-through/afterparty.md)** | drumstep **172**, seed **503** | `09 - Steel Grate` | Drop-first drumstep warp |
| **[audio/albums/drive-through/afterparty/10-rest-bay](../generated/workflows/audio/albums/drive-through/afterparty.md)** | chest bass **155**, seed **509** | `10 - Rest Bay` | Drop-first chest bass warp |
| **[audio/albums/drive-through/afterparty/11-haul-crate](../generated/workflows/audio/albums/drive-through/afterparty.md)** | hybrid trap **170**, seed **521** | `11 - Haul Crate` | Drop-first hybrid trap warp |
| **[audio/albums/drive-through/afterparty/12-night-splice](../generated/workflows/audio/albums/drive-through/afterparty.md)** | wave bass **152**, seed **523** | `12 - Night Splice` | Drop-first wave bass warp |
| **[audio/albums/drive-through/afterparty/13-torque-bay](../generated/workflows/audio/albums/drive-through/afterparty.md)** | neuro bass **176**, seed **541** | `13 - Torque Bay` | Drop-first neuro bass warp |
| **[audio/albums/drive-through/afterparty/14-spare-drum](../generated/workflows/audio/albums/drive-through/afterparty.md)** | brostep **165**, seed **547** | `14 - Spare Drum` | Drop-first brostep warp |
| **[audio/albums/drive-through/afterparty/15-oil-pan](../generated/workflows/audio/albums/drive-through/afterparty.md)** | color bass **150**, seed **557** | `15 - Oil Pan` | Drop-first color bass warp |
| **[audio/albums/drive-through/afterparty/16-curb-check](../generated/workflows/audio/albums/drive-through/afterparty.md)** | drumstep **174**, seed **563** | `16 - Curb Check` | Drop-first drumstep warp |
| **[audio/albums/drive-through/afterparty/17-last-exit](../generated/workflows/audio/albums/drive-through/afterparty.md)** | dirty bass **160**, seed **569** | `17 - Last Exit` | Drop-first dirty bass warp |
| **[audio/albums/drive-through/afterparty/18-asphalt-heart](../generated/workflows/audio/albums/drive-through/afterparty.md)** | chest bass **155**, seed **571** | `18 - Asphalt Heart` | Drop-first chest bass warp |
| **[audio/albums/drive-through/afterparty/19-clutch-slam](../generated/workflows/audio/albums/drive-through/afterparty.md)** | tearout **168**, seed **577** | `19 - Clutch Slam` | Drop-first tearout warp |
| **[audio/albums/drive-through/afterparty/20-trailer-hitch](../generated/workflows/audio/albums/drive-through/afterparty.md)** | hybrid trap **165**, seed **587** | `20 - Trailer Hitch` | Drop-first hybrid trap warp |

#### Secret Homage (`audio/albums/drive-through/secret-homage/`)

Secret Homage. Node placement varies across five layouts. Full album: `./scripts/manage.sh album-render --album drive-through/secret-homage`.

| Graph | Tags / bpm | Prefix | Take |
| --- | --- | --- | --- |
| **[audio/albums/drive-through/secret-homage/01-hush-lane](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | dirty dubstep **140**, seed **593** | `01 - Hush Lane` | Drop-first dirty dubstep warp |
| **[audio/albums/drive-through/secret-homage/02-cipher-lock](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | brostep **140**, seed **599** | `02 - Cipher Lock` | Drop-first brostep warp |
| **[audio/albums/drive-through/secret-homage/03-ghost-dock](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | riddim **140**, seed **601** | `03 - Ghost Dock` | Drop-first riddim warp |
| **[audio/albums/drive-through/secret-homage/04-sealed-ramp](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | tearout **145**, seed **607** | `04 - Sealed Ramp` | Drop-first tearout warp |
| **[audio/albums/drive-through/secret-homage/05-fog-vault](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | color bass **142**, seed **613** | `05 - Fog Vault` | Drop-first color bass warp |
| **[audio/albums/drive-through/secret-homage/06-dummy-light](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | hybrid trap **145**, seed **617** | `06 - Dummy Light` | Drop-first hybrid trap warp |
| **[audio/albums/drive-through/secret-homage/07-quiet-wreck](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | dirty bass **140**, seed **619** | `07 - Quiet Wreck` | Drop-first dirty bass warp |
| **[audio/albums/drive-through/secret-homage/08-off-ledger](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | drumstep **174**, seed **631** | `08 - Off Ledger` | Drop-first drumstep warp |
| **[audio/albums/drive-through/secret-homage/09-back-alley](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | neuro bass **172**, seed **641** | `09 - Back Alley` | Drop-first neuro bass warp |
| **[audio/albums/drive-through/secret-homage/10-cellar-kick](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | dirty dubstep **148**, seed **643** | `10 - Cellar Kick` | Drop-first dirty dubstep warp |
| **[audio/albums/drive-through/secret-homage/11-hidden-booth](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | hybrid trap **140**, seed **647** | `11 - Hidden Booth` | Drop-first hybrid trap warp |
| **[audio/albums/drive-through/secret-homage/12-coded-sub](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | chest bass **140**, seed **653** | `12 - Coded Sub` | Drop-first chest bass warp |
| **[audio/albums/drive-through/secret-homage/13-shadow-coil](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | neuro bass **150**, seed **659** | `13 - Shadow Coil` | Drop-first neuro bass warp |
| **[audio/albums/drive-through/secret-homage/14-mute-pyro](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | wave bass **150**, seed **661** | `14 - Mute Pyro` | Drop-first wave bass warp |
| **[audio/albums/drive-through/secret-homage/15-unlisted-row](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | drumstep **176**, seed **673** | `15 - Unlisted Row` | Drop-first drumstep warp |
| **[audio/albums/drive-through/secret-homage/16-night-cipher](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | wave bass **140**, seed **677** | `16 - Night Cipher` | Drop-first wave bass warp |
| **[audio/albums/drive-through/secret-homage/17-blank-stencil](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | festival trap **140**, seed **683** | `17 - Blank Stencil` | Drop-first festival trap warp |
| **[audio/albums/drive-through/secret-homage/18-blind-stamp](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | riddim **150**, seed **691** | `18 - Blind Stamp` | Drop-first riddim warp |
| **[audio/albums/drive-through/secret-homage/19-cold-cache](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | hybrid trap **142**, seed **701** | `19 - Cold Cache` | Drop-first hybrid trap warp |
| **[audio/albums/drive-through/secret-homage/20-secret-homage](../generated/workflows/audio/albums/drive-through/secret-homage.md)** | dirty dubstep **140**, seed **709** | `20 - Secret Homage` | Drop-first dirty dubstep warp |

Cover still in a later Klein session. Do not co-resident with LTX / Wan / Klein.

---

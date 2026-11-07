---
title: Creator pack
description: Reference table of the one hundred platform Apps for YouTube, Instagram, TikTok, X, LinkedIn, Pinterest, Twitch, Spotify, and merch.
tags: [comfyui, workflows, creator, klein, wan, ltx, catalog]
---

# Creator pack

Pick a platform job. This catalog covers named creator deliverables: channel
art, feed plates, Shorts thumbs, Canvas loops, BRB screens, merch mocks, and
the silent or AV loops that sit under them - one hundred Apps nested under
`_lab/social/<kind>/`. Generic stills are on
[Stills graphs](workflows-stills.md) and client SKUs are on
[Services pack](workflows-services.md).

**What's on this page**

- **How to read these tables** - Size, Prefix, and the Format / platform retarget
- **Platform stills** - YouTube, Instagram, TikTok, X, LinkedIn, Pinterest, Facebook and Threads, Twitch, Spotify, podcast, merch, slides, email, production plates
- **Silent motion (Wan 2.2)** - loops and I2V jobs
- **AV (LTX-2.5)** - ~5 s takes with world audio
- **Related** - what to load after the plate lands

**What this enables**

- **Queuing a job-named App** (channel art, 4:5 feed, Canvas loop, BRB screen) instead of restyling a generic still
- **Reading one table per platform** so you can find the row in seconds
- **Keeping occupancy XOR** - Klein, Wan, and LTX still do not share a GB10 session

**Who this is for:** studio users after `photos/still-draft`. Index: [Workflow catalog](../studio-workflows.md). Occupancy and widgets: [ComfyUI Apps](../studio-apps.md).

**How to read these tables.** The **Workflow** column is the lab id under
`_lab/social/`, and it links to the generated node page for that graph. **Size**
is the widget default; **Format / platform** retargets the same App, so match the
platform aspect and scale in an editor when the host wants more pixels. **Prefix**
is the filename stem the graph writes, and **What it does** names the job and its
shape. These Apps clone the printers the studio already ships, so they add no
models and the plates come out empty of lettering - composite titles later.
Spotify Canvas stays **silent**. Seeds, occupancy, sizes, and Queue rules:
[Workflow catalog](../studio-workflows.md#shared-lab-graph-rules). Safety impact:
**none**.

## YouTube

Seven channel plates: 1:1 icon and Community post, 16:9 art, chapter, subscribe,
and end-screen, plus one 9:16 Shorts thumb. Occupancy **klein**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/stills/youtube-channel-icon](../generated/workflows/social/stills/youtube-channel-icon.md)** | 768x768 | `ez_yt_icon` | YouTube channel icon, circle-safe 1:1 |
| **[social/stills/youtube-channel-art](../generated/workflows/social/stills/youtube-channel-art.md)** | 1536x864 | `ez_yt_art` | YouTube channel art 16:9 with a mobile-safe center band |
| **[social/stills/youtube-shorts-thumb](../generated/workflows/social/stills/youtube-shorts-thumb.md)** | 576x1024 | `ez_yt_shorts_thumb` | YouTube Shorts thumbnail 9:16 |
| **[social/stills/youtube-community](../generated/workflows/social/stills/youtube-community.md)** | 1024x1024 | `ez_yt_community` | YouTube Community post 1:1 |
| **[social/stills/youtube-chapter-card](../generated/workflows/social/stills/youtube-chapter-card.md)** | 1280x720 | `ez_yt_chapter` | YouTube chapter plate 16:9 |
| **[social/stills/youtube-subscribe-plate](../generated/workflows/social/stills/youtube-subscribe-plate.md)** | 1280x720 | `ez_yt_sub` | Subscribe-safe end plate 16:9 |
| **[social/stills/youtube-end-screen](../generated/workflows/social/stills/youtube-end-screen.md)** | 1280x720 | `ez_yt_endscreen` | YouTube end-screen plate, left-weighted |

## Instagram

Eight feed and profile plates: 4:5 portrait, five-slide carousel, reel cover, a 1:1 three-tile grid row, two circle-safe covers, a Story, and a ~1.91:1 landscape. Occupancy **klein**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/stills/instagram-portrait](../generated/workflows/social/stills/instagram-portrait.md)** | 1024x1280 | `ez_ig_portrait` | Instagram 4:5 feed still |
| **[social/stills/instagram-landscape](../generated/workflows/social/stills/instagram-landscape.md)** | 1216x640 | `ez_ig_land` | Instagram landscape feed ~1.91:1 |
| **[social/stills/instagram-story](../generated/workflows/social/stills/instagram-story.md)** | 576x1024 | `ez_ig_story` | Instagram Story 9:16 with UI-safe edges |
| **[social/stills/instagram-reel-cover](../generated/workflows/social/stills/instagram-reel-cover.md)** | 576x1024 | `ez_ig_reel` | Instagram Reel cover, center-weighted for the grid crop |
| **[social/stills/instagram-highlight](../generated/workflows/social/stills/instagram-highlight.md)** | 768x768 | `ez_ig_highlight` | Instagram Highlight cover, circle-safe |
| **[social/stills/instagram-profile](../generated/workflows/social/stills/instagram-profile.md)** | 768x768 | `ez_ig_profile` | Instagram profile photo, circle-safe |
| **[social/stills/instagram-carousel-5](../generated/workflows/social/stills/instagram-carousel-5.md)** | 1024x1280 | `ez_ig_c01` | Instagram 4:5 carousel, five slides |
| **[social/stills/instagram-grid-3up](../generated/workflows/social/stills/instagram-grid-3up.md)** | 1024x1024 | `ez_ig_g01` | Instagram 1:1 three-tile grid row |

## TikTok

Two plates: the 9:16 video cover and a 1:1 Shop packshot. Occupancy **klein**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/stills/tiktok-cover](../generated/workflows/social/stills/tiktok-cover.md)** | 576x1024 | `ez_tt_cover` | TikTok cover 9:16 |
| **[social/stills/tiktok-shop](../generated/workflows/social/stills/tiktok-shop.md)** | 1024x1024 | `ez_tt_shop` | TikTok Shop packshot 1:1 |

## X

Three plates: a 16:9 in-stream still, a 3:1 header, and a ~1.91:1 link card. Occupancy **klein**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/stills/x-post](../generated/workflows/social/stills/x-post.md)** | 1280x720 | `ez_x_post` | X in-stream still 16:9 |
| **[social/stills/x-header](../generated/workflows/social/stills/x-header.md)** | 1536x512 | `ez_x_header` | X header 3:1 |
| **[social/stills/x-card](../generated/workflows/social/stills/x-card.md)** | 1216x640 | `ez_x_card` | X link-card still ~1.91:1 |

## LinkedIn

Five plates: square post, landscape post, article cover, a 4:1 personal banner, and a five-square document carousel. Occupancy **klein**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/stills/linkedin-post](../generated/workflows/social/stills/linkedin-post.md)** | 1024x1024 | `ez_li_post` | LinkedIn square post 1:1 |
| **[social/stills/linkedin-landscape](../generated/workflows/social/stills/linkedin-landscape.md)** | 1216x640 | `ez_li_land` | LinkedIn landscape post ~1.91:1 |
| **[social/stills/linkedin-banner](../generated/workflows/social/stills/linkedin-banner.md)** | 1536x384 | `ez_li_banner` | LinkedIn personal banner 4:1 |
| **[social/stills/linkedin-article](../generated/workflows/social/stills/linkedin-article.md)** | 1216x640 | `ez_li_article` | LinkedIn article cover ~1.91:1 |
| **[social/stills/linkedin-carousel-5](../generated/workflows/social/stills/linkedin-carousel-5.md)** | 1024x1024 | `ez_li_c01` | LinkedIn document carousel, five squares |

## Pinterest

Two plates: the 2:3 standard pin and a 9:16 Idea Pin. Occupancy **klein**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/stills/pinterest-pin](../generated/workflows/social/stills/pinterest-pin.md)** | 768x1152 | `ez_pin` | Pinterest standard pin 2:3 |
| **[social/stills/pinterest-story](../generated/workflows/social/stills/pinterest-story.md)** | 576x1024 | `ez_pin_story` | Pinterest Idea Pin 9:16 |

## Facebook and Threads

Two plates: a ~1.91:1 shared-image still and a 4:5 Threads portrait. Occupancy **klein**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/stills/facebook-post](../generated/workflows/social/stills/facebook-post.md)** | 1216x640 | `ez_fb_post` | Facebook shared-image still ~1.91:1 |
| **[social/stills/threads-portrait](../generated/workflows/social/stills/threads-portrait.md)** | 1024x1280 | `ez_threads` | Threads 4:5 still |

## Twitch / stream

Eight stream-furniture plates: offline, starting-soon, BRB, ending, webcam-hole overlay, about panel, profile, and a ~3:1 banner. Occupancy **klein**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/stills/twitch-offline](../generated/workflows/social/stills/twitch-offline.md)** | 1280x720 | `ez_tw_off` | Twitch offline screen 16:9 |
| **[social/stills/twitch-starting](../generated/workflows/social/stills/twitch-starting.md)** | 1280x720 | `ez_tw_start` | Twitch starting-soon screen 16:9 |
| **[social/stills/twitch-brb](../generated/workflows/social/stills/twitch-brb.md)** | 1280x720 | `ez_tw_brb` | Twitch BRB screen 16:9 |
| **[social/stills/twitch-ending](../generated/workflows/social/stills/twitch-ending.md)** | 1280x720 | `ez_tw_end` | Twitch stream-ending screen 16:9 |
| **[social/stills/twitch-overlay](../generated/workflows/social/stills/twitch-overlay.md)** | 1280x720 | `ez_tw_overlay` | Twitch webcam-hole overlay 16:9 |
| **[social/stills/twitch-panel](../generated/workflows/social/stills/twitch-panel.md)** | 768x1024 | `ez_tw_panel` | Twitch about-panel art |
| **[social/stills/twitch-profile](../generated/workflows/social/stills/twitch-profile.md)** | 768x768 | `ez_tw_profile` | Twitch profile photo, circle-safe |
| **[social/stills/twitch-banner](../generated/workflows/social/stills/twitch-banner.md)** | 1536x512 | `ez_tw_banner` | Twitch channel banner ~3:1 |

## Spotify / music visual

Four covers: playlist, album, lyric card, and the 9:16 Canvas still that stands in for the silent loop. Occupancy **klein**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/stills/spotify-playlist](../generated/workflows/social/stills/spotify-playlist.md)** | 1024x1024 | `ez_spot_pl` | Spotify playlist cover 1:1 |
| **[social/stills/spotify-canvas-still](../generated/workflows/social/stills/spotify-canvas-still.md)** | 576x1024 | `ez_spot_still` | Spotify Canvas still 9:16 (silent JPG stand-in) |
| **[social/stills/album-cover](../generated/workflows/social/stills/album-cover.md)** | 1024x1024 | `ez_album` | Release / album cover 1:1 |
| **[social/stills/lyric-card](../generated/workflows/social/stills/lyric-card.md)** | 1024x1024 | `ez_lyric` | Lyric-card background 1:1 |

## Podcast visual

Three plates: wide and vertical audiogram backgrounds plus per-episode art. Occupancy **klein**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/stills/audiogram-wide](../generated/workflows/social/stills/audiogram-wide.md)** | 1280x720 | `ez_ag_wide` | Audiogram background 16:9 |
| **[social/stills/audiogram-vert](../generated/workflows/social/stills/audiogram-vert.md)** | 576x1024 | `ez_ag_vert` | Audiogram background 9:16 |
| **[social/stills/episode-art](../generated/workflows/social/stills/episode-art.md)** | 1024x1024 | `ez_episode` | Per-episode podcast art 1:1 |

## Merch / print

Three mocks: unmarked tee, mug, and a 2:3 print poster. Occupancy **klein**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/stills/merch-tee](../generated/workflows/social/stills/merch-tee.md)** | 1024x1024 | `ez_tee` | Unmarked tee mock 1:1 |
| **[social/stills/merch-mug](../generated/workflows/social/stills/merch-mug.md)** | 1024x1024 | `ez_mug_merch` | Merch mug mock 1:1 |
| **[social/stills/poster-portrait](../generated/workflows/social/stills/poster-portrait.md)** | 768x1152 | `ez_poster` | Print poster 2:3 |

## Slides / stream bg

Two 16:9 plates: a course or webinar title card and a webcam-safe background. Occupancy **klein**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/stills/slide-title](../generated/workflows/social/stills/slide-title.md)** | 1280x720 | `ez_slide` | Course / webinar title plate 16:9 |
| **[social/stills/zoom-bg](../generated/workflows/social/stills/zoom-bg.md)** | 1280x720 | `ez_zoom` | Webcam-safe Zoom / Meet background 16:9 |

## Email / web

Three plates: newsletter header, Substack hero, and a 4:5 membership post. Occupancy **klein**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/stills/email-header](../generated/workflows/social/stills/email-header.md)** | 1216x640 | `ez_email` | Newsletter / email header ~1.91:1 |
| **[social/stills/substack-hero](../generated/workflows/social/stills/substack-hero.md)** | 1216x640 | `ez_substack` | Substack / blog hero ~1.91:1 |
| **[social/stills/patreon-post](../generated/workflows/social/stills/patreon-post.md)** | 1024x1280 | `ez_patreon` | Membership post still 4:5 |

## Production plates

Five plates: lifestyle product, desk setup, a six-still moodboard, four brand plates, and a coming-soon card. Occupancy **klein**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/stills/product-lifestyle](../generated/workflows/social/stills/product-lifestyle.md)** | 1024x1280 | `ez_lifestyle` | In-use product lifestyle 4:5 |
| **[social/stills/desk-setup](../generated/workflows/social/stills/desk-setup.md)** | 1280x720 | `ez_desk` | Workspace establishing still 16:9 |
| **[social/stills/moodboard-6up](../generated/workflows/social/stills/moodboard-6up.md)** | 768x432 | `ez_mood_c01` | Six-still moodboard of one identity |
| **[social/stills/brand-kit-4](../generated/workflows/social/stills/brand-kit-4.md)** | 768x432 | `ez_brand_01` | Four brand plates, same camera, different lights |
| **[social/stills/coming-soon](../generated/workflows/social/stills/coming-soon.md)** | 1280x720 | `ez_soon` | Launch / coming-soon plate 16:9 |

## Silent motion (Wan 2.2)

Twenty-five silent loops and I2V jobs at 832x480 landscape or 480x832 vertical. Park Klein first. Occupancy **wan**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/silent/youtube-subscribe-bump](../generated/workflows/social/silent/youtube-subscribe-bump.md)** | 832x480 | `ez_yt_bump` | Silent YouTube subscribe bumper loop |
| **[social/silent/instagram-story-loop](../generated/workflows/social/silent/instagram-story-loop.md)** | 480x832 | `ez_ig_loop` | Silent Instagram Story loop 9:16 |
| **[social/silent/tiktok-hook](../generated/workflows/social/silent/tiktok-hook.md)** | 480x832 | `ez_tt_hook` | Silent TikTok hook punch 9:16 |
| **[social/silent/x-post-5s](../generated/workflows/social/silent/x-post-5s.md)** | 832x480 | `ez_x_video` | Silent X clip ~5 s 16:9 |
| **[social/silent/twitch-starting-loop](../generated/workflows/social/silent/twitch-starting-loop.md)** | 832x480 | `ez_tw_start_loop` | Silent starting-soon loop 16:9 |
| **[social/silent/twitch-brb-loop](../generated/workflows/social/silent/twitch-brb-loop.md)** | 832x480 | `ez_tw_brb_loop` | Silent BRB loop 16:9 |
| **[social/silent/spotify-canvas](../generated/workflows/social/silent/spotify-canvas.md)** | 480x832 | `ez_spot_canvas` | Silent Spotify Canvas rebound 9:16 |
| **[social/silent/lyric-bg-loop](../generated/workflows/social/silent/lyric-bg-loop.md)** | 832x480 | `ez_lyric_loop` | Silent lyric-background loop 16:9 |
| **[social/silent/product-spin](../generated/workflows/social/silent/product-spin.md)** | 832x480 | `ez_spin` | Silent product orbit ~5 s |
| **[social/silent/unbox-hands](../generated/workflows/social/silent/unbox-hands.md)** | 832x480 | `ez_unbox` | Silent unbox / hands motion ~5 s |
| **[social/silent/steam-loop](../generated/workflows/social/silent/steam-loop.md)** | 832x480 | `ez_steam` | Silent steam / kettle loop |
| **[social/silent/candle-loop](../generated/workflows/social/silent/candle-loop.md)** | 832x480 | `ez_candle` | Silent candle-flicker loop |
| **[social/silent/light-leak-loop](../generated/workflows/social/silent/light-leak-loop.md)** | 832x480 | `ez_leak` | Silent light-leak overlay loop |
| **[social/silent/logo-sting](../generated/workflows/social/silent/logo-sting.md)** | 832x480 | `ez_sting` | Silent logo sting ~5 s |
| **[social/silent/ken-burns](../generated/workflows/social/silent/ken-burns.md)** | 832x480 | `ez_kenburns` | Silent Ken Burns pan/zoom ~5 s |
| **[social/silent/tilt-reveal](../generated/workflows/social/silent/tilt-reveal.md)** | 832x480 | `ez_tilt` | Silent tilt reveal ~5 s |
| **[social/silent/handheld-vlog](../generated/workflows/social/silent/handheld-vlog.md)** | 480x832 | `ez_vlog` | Silent handheld vlog micro-shake 9:16 |
| **[social/silent/macro-product](../generated/workflows/social/silent/macro-product.md)** | 832x480 | `ez_macro` | Silent macro product crawl ~5 s |
| **[social/silent/fabric-breeze](../generated/workflows/social/silent/fabric-breeze.md)** | 832x480 | `ez_breeze` | Silent fabric/hair breeze ~5 s |
| **[social/silent/city-night](../generated/workflows/social/silent/city-night.md)** | 832x480 | `ez_night` | Silent night-drive / city-lights ~5 s |
| **[social/silent/zoom-punch](../generated/workflows/social/silent/zoom-punch.md)** | 480x832 | `ez_punch` | Silent 9:16 hook zoom punch |
| **[social/silent/screen-bg-loop](../generated/workflows/social/silent/screen-bg-loop.md)** | 832x480 | `ez_screen` | Silent desk/screen loop |
| **[social/silent/confetti-loop](../generated/workflows/social/silent/confetti-loop.md)** | 832x480 | `ez_confetti` | Silent celebration loop |
| **[social/silent/paper-flip](../generated/workflows/social/silent/paper-flip.md)** | 832x480 | `ez_flip` | Silent page / carousel flip ~5 s |
| **[social/silent/pan-left](../generated/workflows/social/silent/pan-left.md)** | 832x480 | `ez_pan` | Silent locked-identity pan ~5 s |

## AV (LTX-2.5)

Eighteen ~5 s AV takes with world audio at 1280x704 landscape or 768x1280 vertical, both on the div32 LTX grid. Park Wan first. Occupancy **ltx**.

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[social/av/youtube-outro-av](../generated/workflows/social/av/youtube-outro-av.md)** | 1280x704 | `ez_yt_outro` | YouTube outro AV ~5 s with room tone |
| **[social/av/instagram-reel-lifestyle](../generated/workflows/social/av/instagram-reel-lifestyle.md)** | 768x1280 | `ez_ig_reel_av` | Instagram lifestyle reel AV 9:16 |
| **[social/av/tiktok-broll](../generated/workflows/social/av/tiktok-broll.md)** | 768x1280 | `ez_tt_broll` | TikTok B-roll AV 9:16 |
| **[social/av/twitch-starting-av](../generated/workflows/social/av/twitch-starting-av.md)** | 1280x704 | `ez_tw_start_av` | Twitch starting-soon AV ~5 s |
| **[social/av/music-visual](../generated/workflows/social/av/music-visual.md)** | 1280x704 | `ez_music_vis` | Light / particle visualizer bed AV ~5 s |
| **[social/av/recipe-pour](../generated/workflows/social/av/recipe-pour.md)** | 768x1280 | `ez_pour` | Recipe pour AV 9:16 |
| **[social/av/product-unbox-av](../generated/workflows/social/av/product-unbox-av.md)** | 1280x704 | `ez_unbox_av` | Unbox AV with paper SFX ~5 s |
| **[social/av/desk-work](../generated/workflows/social/av/desk-work.md)** | 1280x704 | `ez_desk_av` | Desk / keyboard room-tone AV ~5 s |
| **[social/av/travel-establishing](../generated/workflows/social/av/travel-establishing.md)** | 1280x704 | `ez_travel` | Travel establishing AV ~5 s |
| **[social/av/interior-walk](../generated/workflows/social/av/interior-walk.md)** | 1280x704 | `ez_walk` | Interior walk-through AV ~5 s |
| **[social/av/fashion-turn](../generated/workflows/social/av/fashion-turn.md)** | 768x1280 | `ez_turn` | Fashion turn AV 9:16 |
| **[social/av/workout-rep](../generated/workflows/social/av/workout-rep.md)** | 768x1280 | `ez_rep` | One exercise-rep AV 9:16 |
| **[social/av/asmr-macro](../generated/workflows/social/av/asmr-macro.md)** | 1280x704 | `ez_asmr` | Quiet macro foley AV ~5 s |
| **[social/av/rain-window](../generated/workflows/social/av/rain-window.md)** | 1280x704 | `ez_rain` | Rain-on-glass AV ~5 s |
| **[social/av/fireplace](../generated/workflows/social/av/fireplace.md)** | 1280x704 | `ez_fire` | Fireplace AV ~5 s |
| **[social/av/podcast-set](../generated/workflows/social/av/podcast-set.md)** | 1280x704 | `ez_pod_set` | Podcast-set AV ~5 s |
| **[social/av/workshop-tools](../generated/workflows/social/av/workshop-tools.md)** | 1280x704 | `ez_tools` | Workshop tools AV ~5 s |
| **[social/av/crowd-ambience](../generated/workflows/social/av/crowd-ambience.md)** | 1280x704 | `ez_crowd` | Distant crowd bed AV ~5 s |

---

## Related

1. Start from a generic plate instead: [Stills graphs](workflows-stills.md)
2. Move a plate: [Motion graphs](workflows-motion.md)
3. Client SKUs instead of creator jobs: [Services pack](workflows-services.md)
4. Pick the graph for a different job: [Workflow catalog](../studio-workflows.md)
5. Write the prompt: [Prompting](../prompting.md)

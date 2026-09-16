---
title: Creator pack (platform Apps)
description: One hundred extra Klein, Wan, and LTX Apps for YouTube, Instagram, TikTok, X, LinkedIn, Pinterest, Twitch, Spotify, merch, and production plates.
tags: [comfyui, workflows, creator, klein, wan, ltx, catalog]
---

# Creator pack (platform Apps)

**What's on this page**

- **One hundred extra Apps** nested under `_lab/<lane>/creator/`
- **Platform stills** (YouTube, Instagram, TikTok, X, LinkedIn, Pinterest, Twitch, Spotify)
- **Silent Wan loops / I2V** and **LTX AV** job plates
- **Lab sizes vs upload pixels** — match aspect; scale in an editor if a platform wants more pixels

**What this enables**

- **Queuing a job-named App** (channel art, 4:5 feed, Canvas loop, BRB screen) instead of restyling a generic still
- **Keeping occupancy XOR** — Klein, Wan, and LTX still do not share a GB10 session

**Who this is for:** studio users after `klein/still-draft`. Index: [Workflow catalog](../studio-workflows.md). Occupancy and widgets: [ComfyUI Apps](../studio-apps.md).

These graphs clone the shipped Klein 4B / Wan 2.2 / LTX-2.5 printers. They do **not** add models. Empty of lettering — composite titles later. LTX feeders stay **÷32**. Spotify Canvas is **silent**.

Safety impact: **none**. `restart: "no"`, headroom, and download-limit are unchanged.

## YouTube

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[klein/creator/yt-channel-icon](../generated/workflows/klein/creator/yt-channel-icon.md)** | 768×768 | `ez_yt_icon` | YouTube channel icon, circle-safe 1:1 |
| **[klein/creator/yt-channel-art](../generated/workflows/klein/creator/yt-channel-art.md)** | 1536×864 | `ez_yt_art` | YouTube channel art 16:9 with a mobile-safe center band |
| **[klein/creator/yt-shorts-thumb](../generated/workflows/klein/creator/yt-shorts-thumb.md)** | 576×1024 | `ez_yt_shorts_thumb` | YouTube Shorts thumbnail 9:16 |
| **[klein/creator/yt-community](../generated/workflows/klein/creator/yt-community.md)** | 1024×1024 | `ez_yt_community` | YouTube Community post 1:1 |
| **[klein/creator/yt-chapter-card](../generated/workflows/klein/creator/yt-chapter-card.md)** | 1280×720 | `ez_yt_chapter` | YouTube chapter plate 16:9 |
| **[klein/creator/yt-subscribe-plate](../generated/workflows/klein/creator/yt-subscribe-plate.md)** | 1280×720 | `ez_yt_sub` | Subscribe-safe end plate 16:9 |
| **[klein/creator/yt-end-screen](../generated/workflows/klein/creator/yt-end-screen.md)** | 1280×720 | `ez_yt_endscreen` | YouTube end-screen plate, left-weighted |

## Instagram

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[klein/creator/ig-portrait](../generated/workflows/klein/creator/ig-portrait.md)** | 1024×1280 | `ez_ig_portrait` | Instagram 4:5 feed still |
| **[klein/creator/ig-landscape](../generated/workflows/klein/creator/ig-landscape.md)** | 1216×640 | `ez_ig_land` | Instagram landscape feed ~1.91:1 |
| **[klein/creator/ig-story](../generated/workflows/klein/creator/ig-story.md)** | 576×1024 | `ez_ig_story` | Instagram Story 9:16 with UI-safe edges |
| **[klein/creator/ig-reel-cover](../generated/workflows/klein/creator/ig-reel-cover.md)** | 576×1024 | `ez_ig_reel` | Instagram Reel cover, center-weighted for the grid crop |
| **[klein/creator/ig-highlight](../generated/workflows/klein/creator/ig-highlight.md)** | 768×768 | `ez_ig_highlight` | Instagram Highlight cover, circle-safe |
| **[klein/creator/ig-profile](../generated/workflows/klein/creator/ig-profile.md)** | 768×768 | `ez_ig_profile` | Instagram profile photo, circle-safe |
| **[klein/creator/ig-carousel-5](../generated/workflows/klein/creator/ig-carousel-5.md)** | 1024×1280 | `ez_ig_c01` | Instagram 4:5 carousel, five slides |
| **[klein/creator/ig-grid-3up](../generated/workflows/klein/creator/ig-grid-3up.md)** | 1024×1024 | `ez_ig_g01` | Instagram 1:1 three-tile grid row |

## TikTok

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[klein/creator/tt-cover](../generated/workflows/klein/creator/tt-cover.md)** | 576×1024 | `ez_tt_cover` | TikTok cover 9:16 |
| **[klein/creator/tt-shop](../generated/workflows/klein/creator/tt-shop.md)** | 1024×1024 | `ez_tt_shop` | TikTok Shop packshot 1:1 |

## X

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[klein/creator/x-post](../generated/workflows/klein/creator/x-post.md)** | 1280×720 | `ez_x_post` | X in-stream still 16:9 |
| **[klein/creator/x-header](../generated/workflows/klein/creator/x-header.md)** | 1536×512 | `ez_x_header` | X header 3:1 |
| **[klein/creator/x-card](../generated/workflows/klein/creator/x-card.md)** | 1216×640 | `ez_x_card` | X link-card still ~1.91:1 |

## LinkedIn

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[klein/creator/li-post](../generated/workflows/klein/creator/li-post.md)** | 1024×1024 | `ez_li_post` | LinkedIn square post 1:1 |
| **[klein/creator/li-landscape](../generated/workflows/klein/creator/li-landscape.md)** | 1216×640 | `ez_li_land` | LinkedIn landscape post ~1.91:1 |
| **[klein/creator/li-banner](../generated/workflows/klein/creator/li-banner.md)** | 1536×384 | `ez_li_banner` | LinkedIn personal banner 4:1 |
| **[klein/creator/li-article](../generated/workflows/klein/creator/li-article.md)** | 1216×640 | `ez_li_article` | LinkedIn article cover ~1.91:1 |
| **[klein/creator/li-carousel-5](../generated/workflows/klein/creator/li-carousel-5.md)** | 1024×1024 | `ez_li_c01` | LinkedIn document carousel, five squares |

## Pinterest

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[klein/creator/pin-standard](../generated/workflows/klein/creator/pin-standard.md)** | 768×1152 | `ez_pin` | Pinterest standard pin 2:3 |
| **[klein/creator/pin-story](../generated/workflows/klein/creator/pin-story.md)** | 576×1024 | `ez_pin_story` | Pinterest Idea Pin 9:16 |

## Facebook and Threads

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[klein/creator/fb-post](../generated/workflows/klein/creator/fb-post.md)** | 1216×640 | `ez_fb_post` | Facebook shared-image still ~1.91:1 |
| **[klein/creator/threads-portrait](../generated/workflows/klein/creator/threads-portrait.md)** | 1024×1280 | `ez_threads` | Threads 4:5 still |

## Twitch / stream

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[klein/creator/twitch-offline](../generated/workflows/klein/creator/twitch-offline.md)** | 1280×720 | `ez_tw_off` | Twitch offline screen 16:9 |
| **[klein/creator/twitch-starting](../generated/workflows/klein/creator/twitch-starting.md)** | 1280×720 | `ez_tw_start` | Twitch starting-soon screen 16:9 |
| **[klein/creator/twitch-brb](../generated/workflows/klein/creator/twitch-brb.md)** | 1280×720 | `ez_tw_brb` | Twitch BRB screen 16:9 |
| **[klein/creator/twitch-ending](../generated/workflows/klein/creator/twitch-ending.md)** | 1280×720 | `ez_tw_end` | Twitch stream-ending screen 16:9 |
| **[klein/creator/twitch-overlay](../generated/workflows/klein/creator/twitch-overlay.md)** | 1280×720 | `ez_tw_overlay` | Twitch webcam-hole overlay 16:9 |
| **[klein/creator/twitch-panel](../generated/workflows/klein/creator/twitch-panel.md)** | 768×1024 | `ez_tw_panel` | Twitch about-panel art |
| **[klein/creator/twitch-profile](../generated/workflows/klein/creator/twitch-profile.md)** | 768×768 | `ez_tw_profile` | Twitch profile photo, circle-safe |
| **[klein/creator/twitch-banner](../generated/workflows/klein/creator/twitch-banner.md)** | 1536×512 | `ez_tw_banner` | Twitch channel banner ~3:1 |

## Spotify / music visual

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[klein/creator/spotify-playlist](../generated/workflows/klein/creator/spotify-playlist.md)** | 1024×1024 | `ez_spot_pl` | Spotify playlist cover 1:1 |
| **[klein/creator/spotify-canvas-still](../generated/workflows/klein/creator/spotify-canvas-still.md)** | 576×1024 | `ez_spot_still` | Spotify Canvas still 9:16 (silent JPG stand-in) |
| **[klein/creator/album-cover](../generated/workflows/klein/creator/album-cover.md)** | 1024×1024 | `ez_album` | Release / album cover 1:1 |
| **[klein/creator/lyric-card](../generated/workflows/klein/creator/lyric-card.md)** | 1024×1024 | `ez_lyric` | Lyric-card background 1:1 |

## Podcast visual

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[klein/creator/audiogram-wide](../generated/workflows/klein/creator/audiogram-wide.md)** | 1280×720 | `ez_ag_wide` | Audiogram background 16:9 |
| **[klein/creator/audiogram-vert](../generated/workflows/klein/creator/audiogram-vert.md)** | 576×1024 | `ez_ag_vert` | Audiogram background 9:16 |
| **[klein/creator/episode-art](../generated/workflows/klein/creator/episode-art.md)** | 1024×1024 | `ez_episode` | Per-episode podcast art 1:1 |

## Merch / print

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[klein/creator/merch-tee](../generated/workflows/klein/creator/merch-tee.md)** | 1024×1024 | `ez_tee` | Unmarked tee mock 1:1 |
| **[klein/creator/merch-mug](../generated/workflows/klein/creator/merch-mug.md)** | 1024×1024 | `ez_mug_merch` | Merch mug mock 1:1 |
| **[klein/creator/poster-portrait](../generated/workflows/klein/creator/poster-portrait.md)** | 768×1152 | `ez_poster` | Print poster 2:3 |

## Slides / stream bg

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[klein/creator/slide-title](../generated/workflows/klein/creator/slide-title.md)** | 1280×720 | `ez_slide` | Course / webinar title plate 16:9 |
| **[klein/creator/zoom-bg](../generated/workflows/klein/creator/zoom-bg.md)** | 1280×720 | `ez_zoom` | Webcam-safe Zoom / Meet background 16:9 |

## Email / web

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[klein/creator/email-header](../generated/workflows/klein/creator/email-header.md)** | 1216×640 | `ez_email` | Newsletter / email header ~1.91:1 |
| **[klein/creator/substack-hero](../generated/workflows/klein/creator/substack-hero.md)** | 1216×640 | `ez_substack` | Substack / blog hero ~1.91:1 |
| **[klein/creator/patreon-post](../generated/workflows/klein/creator/patreon-post.md)** | 1024×1280 | `ez_patreon` | Membership post still 4:5 |

## Production plates

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[klein/creator/product-lifestyle](../generated/workflows/klein/creator/product-lifestyle.md)** | 1024×1280 | `ez_lifestyle` | In-use product lifestyle 4:5 |
| **[klein/creator/desk-setup](../generated/workflows/klein/creator/desk-setup.md)** | 1280×720 | `ez_desk` | Workspace establishing still 16:9 |
| **[klein/creator/moodboard-6up](../generated/workflows/klein/creator/moodboard-6up.md)** | 768×432 | `ez_mood_c01` | Six-still moodboard of one identity |
| **[klein/creator/brand-kit-4](../generated/workflows/klein/creator/brand-kit-4.md)** | 768×432 | `ez_brand_01` | Four brand plates, same camera, different lights |
| **[klein/creator/coming-soon](../generated/workflows/klein/creator/coming-soon.md)** | 1280×720 | `ez_soon` | Launch / coming-soon plate 16:9 |

## Silent motion (Wan 2.2)

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[wan/creator/yt-subscribe-bump](../generated/workflows/wan/creator/yt-subscribe-bump.md)** | 832×480 | `ez_yt_bump` | Silent YouTube subscribe bumper loop |
| **[wan/creator/ig-story-loop](../generated/workflows/wan/creator/ig-story-loop.md)** | 480×832 | `ez_ig_loop` | Silent Instagram Story loop 9:16 |
| **[wan/creator/tt-hook](../generated/workflows/wan/creator/tt-hook.md)** | 480×832 | `ez_tt_hook` | Silent TikTok hook punch 9:16 |
| **[wan/creator/x-post-5s](../generated/workflows/wan/creator/x-post-5s.md)** | 832×480 | `ez_x_video` | Silent X clip ~5 s 16:9 |
| **[wan/creator/twitch-starting-loop](../generated/workflows/wan/creator/twitch-starting-loop.md)** | 832×480 | `ez_tw_start_loop` | Silent starting-soon loop 16:9 |
| **[wan/creator/twitch-brb-loop](../generated/workflows/wan/creator/twitch-brb-loop.md)** | 832×480 | `ez_tw_brb_loop` | Silent BRB loop 16:9 |
| **[wan/creator/spotify-canvas](../generated/workflows/wan/creator/spotify-canvas.md)** | 480×832 | `ez_spot_canvas` | Silent Spotify Canvas rebound 9:16 |
| **[wan/creator/lyric-bg-loop](../generated/workflows/wan/creator/lyric-bg-loop.md)** | 832×480 | `ez_lyric_loop` | Silent lyric-background loop 16:9 |
| **[wan/creator/product-spin](../generated/workflows/wan/creator/product-spin.md)** | 832×480 | `ez_spin` | Silent product orbit ~5 s |
| **[wan/creator/unbox-hands](../generated/workflows/wan/creator/unbox-hands.md)** | 832×480 | `ez_unbox` | Silent unbox / hands motion ~5 s |
| **[wan/creator/steam-loop](../generated/workflows/wan/creator/steam-loop.md)** | 832×480 | `ez_steam` | Silent steam / kettle loop |
| **[wan/creator/candle-loop](../generated/workflows/wan/creator/candle-loop.md)** | 832×480 | `ez_candle` | Silent candle-flicker loop |
| **[wan/creator/light-leak-loop](../generated/workflows/wan/creator/light-leak-loop.md)** | 832×480 | `ez_leak` | Silent light-leak overlay loop |
| **[wan/creator/logo-sting](../generated/workflows/wan/creator/logo-sting.md)** | 832×480 | `ez_sting` | Silent logo sting ~5 s |
| **[wan/creator/ken-burns](../generated/workflows/wan/creator/ken-burns.md)** | 832×480 | `ez_kenburns` | Silent Ken Burns pan/zoom ~5 s |
| **[wan/creator/tilt-reveal](../generated/workflows/wan/creator/tilt-reveal.md)** | 832×480 | `ez_tilt` | Silent tilt reveal ~5 s |
| **[wan/creator/handheld-vlog](../generated/workflows/wan/creator/handheld-vlog.md)** | 480×832 | `ez_vlog` | Silent handheld vlog micro-shake 9:16 |
| **[wan/creator/macro-product](../generated/workflows/wan/creator/macro-product.md)** | 832×480 | `ez_macro` | Silent macro product crawl ~5 s |
| **[wan/creator/fabric-breeze](../generated/workflows/wan/creator/fabric-breeze.md)** | 832×480 | `ez_breeze` | Silent fabric/hair breeze ~5 s |
| **[wan/creator/city-night](../generated/workflows/wan/creator/city-night.md)** | 832×480 | `ez_night` | Silent night-drive / city-lights ~5 s |
| **[wan/creator/zoom-punch](../generated/workflows/wan/creator/zoom-punch.md)** | 480×832 | `ez_punch` | Silent 9:16 hook zoom punch |
| **[wan/creator/screen-bg-loop](../generated/workflows/wan/creator/screen-bg-loop.md)** | 832×480 | `ez_screen` | Silent desk/screen loop |
| **[wan/creator/confetti-loop](../generated/workflows/wan/creator/confetti-loop.md)** | 832×480 | `ez_confetti` | Silent celebration loop |
| **[wan/creator/paper-flip](../generated/workflows/wan/creator/paper-flip.md)** | 832×480 | `ez_flip` | Silent page / carousel flip ~5 s |
| **[wan/creator/pan-left](../generated/workflows/wan/creator/pan-left.md)** | 832×480 | `ez_pan` | Silent locked-identity pan ~5 s |

## AV (LTX-2.5)

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[ltx/creator/yt-outro-av](../generated/workflows/ltx/creator/yt-outro-av.md)** | 1280×704 | `ez_yt_outro` | YouTube outro AV ~5 s with room tone |
| **[ltx/creator/ig-reel-lifestyle](../generated/workflows/ltx/creator/ig-reel-lifestyle.md)** | 768×1280 | `ez_ig_reel_av` | Instagram lifestyle reel AV 9:16 |
| **[ltx/creator/tt-broll](../generated/workflows/ltx/creator/tt-broll.md)** | 768×1280 | `ez_tt_broll` | TikTok B-roll AV 9:16 |
| **[ltx/creator/twitch-starting-av](../generated/workflows/ltx/creator/twitch-starting-av.md)** | 1280×704 | `ez_tw_start_av` | Twitch starting-soon AV ~5 s |
| **[ltx/creator/music-visual](../generated/workflows/ltx/creator/music-visual.md)** | 1280×704 | `ez_music_vis` | Light / particle visualizer bed AV ~5 s |
| **[ltx/creator/recipe-pour](../generated/workflows/ltx/creator/recipe-pour.md)** | 768×1280 | `ez_pour` | Recipe pour AV 9:16 |
| **[ltx/creator/product-unbox-av](../generated/workflows/ltx/creator/product-unbox-av.md)** | 1280×704 | `ez_unbox_av` | Unbox AV with paper SFX ~5 s |
| **[ltx/creator/desk-work](../generated/workflows/ltx/creator/desk-work.md)** | 1280×704 | `ez_desk_av` | Desk / keyboard room-tone AV ~5 s |
| **[ltx/creator/travel-establishing](../generated/workflows/ltx/creator/travel-establishing.md)** | 1280×704 | `ez_travel` | Travel establishing AV ~5 s |
| **[ltx/creator/interior-walk](../generated/workflows/ltx/creator/interior-walk.md)** | 1280×704 | `ez_walk` | Interior walk-through AV ~5 s |
| **[ltx/creator/fashion-turn](../generated/workflows/ltx/creator/fashion-turn.md)** | 768×1280 | `ez_turn` | Fashion turn AV 9:16 |
| **[ltx/creator/workout-rep](../generated/workflows/ltx/creator/workout-rep.md)** | 768×1280 | `ez_rep` | One exercise-rep AV 9:16 |
| **[ltx/creator/asmr-macro](../generated/workflows/ltx/creator/asmr-macro.md)** | 1280×704 | `ez_asmr` | Quiet macro foley AV ~5 s |
| **[ltx/creator/rain-window](../generated/workflows/ltx/creator/rain-window.md)** | 1280×704 | `ez_rain` | Rain-on-glass AV ~5 s |
| **[ltx/creator/fireplace](../generated/workflows/ltx/creator/fireplace.md)** | 1280×704 | `ez_fire` | Fireplace AV ~5 s |
| **[ltx/creator/podcast-set](../generated/workflows/ltx/creator/podcast-set.md)** | 1280×704 | `ez_pod_set` | Podcast-set AV ~5 s |
| **[ltx/creator/workshop-tools](../generated/workflows/ltx/creator/workshop-tools.md)** | 1280×704 | `ez_tools` | Workshop tools AV ~5 s |
| **[ltx/creator/crowd-ambience](../generated/workflows/ltx/creator/crowd-ambience.md)** | 1280×704 | `ez_crowd` | Distant crowd bed AV ~5 s |

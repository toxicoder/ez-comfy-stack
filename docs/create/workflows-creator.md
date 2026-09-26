---
title: Creator pack (platform Apps)
description: One hundred extra Klein, Wan, and LTX Apps for YouTube, Instagram, TikTok, X, LinkedIn, Pinterest, Twitch, Spotify, merch, and production plates.
tags: [comfyui, workflows, creator, klein, wan, ltx, catalog]
---

# Creator pack (platform Apps)

**What's on this page**

- **One hundred extra Apps** nested under `_lab/creator/<kind>/`
- **Platform stills** (YouTube, Instagram, TikTok, X, LinkedIn, Pinterest, Twitch, Spotify)
- **Silent Wan loops / I2V** and **LTX AV** job plates
- **Lab sizes vs upload pixels** - Size column is the **default**. **Format / platform** retargets the same App (YouTube, Shorts, ...). Match aspect; scale in an editor if a platform wants more pixels

**What this enables**

- **Queuing a job-named App** (channel art, 4:5 feed, Canvas loop, BRB screen) instead of restyling a generic still
- **Keeping occupancy XOR** - Klein, Wan, and LTX still do not share a GB10 session

**Who this is for:** studio users after `stills/still-draft`. Index: [Workflow catalog](../studio-workflows.md). Occupancy and widgets: [ComfyUI Apps](../studio-apps.md).

These graphs clone the shipped Klein 4B / Wan 2.2 / LTX-2.5 printers. They do **not** add models. Empty of lettering - composite titles later. LTX feeders stay **div32**. Spotify Canvas is **silent**.

Safety impact: **none**. `restart: "no"`, headroom, and download-limit are unchanged.

## YouTube

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/stills/youtube-channel-icon](../generated/workflows/creator/stills/youtube-channel-icon.md)** | 768x768 | `ez_yt_icon` | YouTube channel icon, circle-safe 1:1 |
| **[creator/stills/youtube-channel-art](../generated/workflows/creator/stills/youtube-channel-art.md)** | 1536x864 | `ez_yt_art` | YouTube channel art 16:9 with a mobile-safe center band |
| **[creator/stills/youtube-shorts-thumb](../generated/workflows/creator/stills/youtube-shorts-thumb.md)** | 576x1024 | `ez_yt_shorts_thumb` | YouTube Shorts thumbnail 9:16 |
| **[creator/stills/youtube-community](../generated/workflows/creator/stills/youtube-community.md)** | 1024x1024 | `ez_yt_community` | YouTube Community post 1:1 |
| **[creator/stills/youtube-chapter-card](../generated/workflows/creator/stills/youtube-chapter-card.md)** | 1280x720 | `ez_yt_chapter` | YouTube chapter plate 16:9 |
| **[creator/stills/youtube-subscribe-plate](../generated/workflows/creator/stills/youtube-subscribe-plate.md)** | 1280x720 | `ez_yt_sub` | Subscribe-safe end plate 16:9 |
| **[creator/stills/youtube-end-screen](../generated/workflows/creator/stills/youtube-end-screen.md)** | 1280x720 | `ez_yt_endscreen` | YouTube end-screen plate, left-weighted |

## Instagram

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/stills/instagram-portrait](../generated/workflows/creator/stills/instagram-portrait.md)** | 1024x1280 | `ez_ig_portrait` | Instagram 4:5 feed still |
| **[creator/stills/instagram-landscape](../generated/workflows/creator/stills/instagram-landscape.md)** | 1216x640 | `ez_ig_land` | Instagram landscape feed ~1.91:1 |
| **[creator/stills/instagram-story](../generated/workflows/creator/stills/instagram-story.md)** | 576x1024 | `ez_ig_story` | Instagram Story 9:16 with UI-safe edges |
| **[creator/stills/instagram-reel-cover](../generated/workflows/creator/stills/instagram-reel-cover.md)** | 576x1024 | `ez_ig_reel` | Instagram Reel cover, center-weighted for the grid crop |
| **[creator/stills/instagram-highlight](../generated/workflows/creator/stills/instagram-highlight.md)** | 768x768 | `ez_ig_highlight` | Instagram Highlight cover, circle-safe |
| **[creator/stills/instagram-profile](../generated/workflows/creator/stills/instagram-profile.md)** | 768x768 | `ez_ig_profile` | Instagram profile photo, circle-safe |
| **[creator/stills/instagram-carousel-5](../generated/workflows/creator/stills/instagram-carousel-5.md)** | 1024x1280 | `ez_ig_c01` | Instagram 4:5 carousel, five slides |
| **[creator/stills/instagram-grid-3up](../generated/workflows/creator/stills/instagram-grid-3up.md)** | 1024x1024 | `ez_ig_g01` | Instagram 1:1 three-tile grid row |

## TikTok

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/stills/tiktok-cover](../generated/workflows/creator/stills/tiktok-cover.md)** | 576x1024 | `ez_tt_cover` | TikTok cover 9:16 |
| **[creator/stills/tiktok-shop](../generated/workflows/creator/stills/tiktok-shop.md)** | 1024x1024 | `ez_tt_shop` | TikTok Shop packshot 1:1 |

## X

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/stills/x-post](../generated/workflows/creator/stills/x-post.md)** | 1280x720 | `ez_x_post` | X in-stream still 16:9 |
| **[creator/stills/x-header](../generated/workflows/creator/stills/x-header.md)** | 1536x512 | `ez_x_header` | X header 3:1 |
| **[creator/stills/x-card](../generated/workflows/creator/stills/x-card.md)** | 1216x640 | `ez_x_card` | X link-card still ~1.91:1 |

## LinkedIn

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/stills/linkedin-post](../generated/workflows/creator/stills/linkedin-post.md)** | 1024x1024 | `ez_li_post` | LinkedIn square post 1:1 |
| **[creator/stills/linkedin-landscape](../generated/workflows/creator/stills/linkedin-landscape.md)** | 1216x640 | `ez_li_land` | LinkedIn landscape post ~1.91:1 |
| **[creator/stills/linkedin-banner](../generated/workflows/creator/stills/linkedin-banner.md)** | 1536x384 | `ez_li_banner` | LinkedIn personal banner 4:1 |
| **[creator/stills/linkedin-article](../generated/workflows/creator/stills/linkedin-article.md)** | 1216x640 | `ez_li_article` | LinkedIn article cover ~1.91:1 |
| **[creator/stills/linkedin-carousel-5](../generated/workflows/creator/stills/linkedin-carousel-5.md)** | 1024x1024 | `ez_li_c01` | LinkedIn document carousel, five squares |

## Pinterest

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/stills/pinterest-pin](../generated/workflows/creator/stills/pinterest-pin.md)** | 768x1152 | `ez_pin` | Pinterest standard pin 2:3 |
| **[creator/stills/pinterest-story](../generated/workflows/creator/stills/pinterest-story.md)** | 576x1024 | `ez_pin_story` | Pinterest Idea Pin 9:16 |

## Facebook and Threads

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/stills/facebook-post](../generated/workflows/creator/stills/facebook-post.md)** | 1216x640 | `ez_fb_post` | Facebook shared-image still ~1.91:1 |
| **[creator/stills/threads-portrait](../generated/workflows/creator/stills/threads-portrait.md)** | 1024x1280 | `ez_threads` | Threads 4:5 still |

## Twitch / stream

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/stills/twitch-offline](../generated/workflows/creator/stills/twitch-offline.md)** | 1280x720 | `ez_tw_off` | Twitch offline screen 16:9 |
| **[creator/stills/twitch-starting](../generated/workflows/creator/stills/twitch-starting.md)** | 1280x720 | `ez_tw_start` | Twitch starting-soon screen 16:9 |
| **[creator/stills/twitch-brb](../generated/workflows/creator/stills/twitch-brb.md)** | 1280x720 | `ez_tw_brb` | Twitch BRB screen 16:9 |
| **[creator/stills/twitch-ending](../generated/workflows/creator/stills/twitch-ending.md)** | 1280x720 | `ez_tw_end` | Twitch stream-ending screen 16:9 |
| **[creator/stills/twitch-overlay](../generated/workflows/creator/stills/twitch-overlay.md)** | 1280x720 | `ez_tw_overlay` | Twitch webcam-hole overlay 16:9 |
| **[creator/stills/twitch-panel](../generated/workflows/creator/stills/twitch-panel.md)** | 768x1024 | `ez_tw_panel` | Twitch about-panel art |
| **[creator/stills/twitch-profile](../generated/workflows/creator/stills/twitch-profile.md)** | 768x768 | `ez_tw_profile` | Twitch profile photo, circle-safe |
| **[creator/stills/twitch-banner](../generated/workflows/creator/stills/twitch-banner.md)** | 1536x512 | `ez_tw_banner` | Twitch channel banner ~3:1 |

## Spotify / music visual

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/stills/spotify-playlist](../generated/workflows/creator/stills/spotify-playlist.md)** | 1024x1024 | `ez_spot_pl` | Spotify playlist cover 1:1 |
| **[creator/stills/spotify-canvas-still](../generated/workflows/creator/stills/spotify-canvas-still.md)** | 576x1024 | `ez_spot_still` | Spotify Canvas still 9:16 (silent JPG stand-in) |
| **[creator/stills/album-cover](../generated/workflows/creator/stills/album-cover.md)** | 1024x1024 | `ez_album` | Release / album cover 1:1 |
| **[creator/stills/lyric-card](../generated/workflows/creator/stills/lyric-card.md)** | 1024x1024 | `ez_lyric` | Lyric-card background 1:1 |

## Podcast visual

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/stills/audiogram-wide](../generated/workflows/creator/stills/audiogram-wide.md)** | 1280x720 | `ez_ag_wide` | Audiogram background 16:9 |
| **[creator/stills/audiogram-vert](../generated/workflows/creator/stills/audiogram-vert.md)** | 576x1024 | `ez_ag_vert` | Audiogram background 9:16 |
| **[creator/stills/episode-art](../generated/workflows/creator/stills/episode-art.md)** | 1024x1024 | `ez_episode` | Per-episode podcast art 1:1 |

## Merch / print

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/stills/merch-tee](../generated/workflows/creator/stills/merch-tee.md)** | 1024x1024 | `ez_tee` | Unmarked tee mock 1:1 |
| **[creator/stills/merch-mug](../generated/workflows/creator/stills/merch-mug.md)** | 1024x1024 | `ez_mug_merch` | Merch mug mock 1:1 |
| **[creator/stills/poster-portrait](../generated/workflows/creator/stills/poster-portrait.md)** | 768x1152 | `ez_poster` | Print poster 2:3 |

## Slides / stream bg

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/stills/slide-title](../generated/workflows/creator/stills/slide-title.md)** | 1280x720 | `ez_slide` | Course / webinar title plate 16:9 |
| **[creator/stills/zoom-bg](../generated/workflows/creator/stills/zoom-bg.md)** | 1280x720 | `ez_zoom` | Webcam-safe Zoom / Meet background 16:9 |

## Email / web

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/stills/email-header](../generated/workflows/creator/stills/email-header.md)** | 1216x640 | `ez_email` | Newsletter / email header ~1.91:1 |
| **[creator/stills/substack-hero](../generated/workflows/creator/stills/substack-hero.md)** | 1216x640 | `ez_substack` | Substack / blog hero ~1.91:1 |
| **[creator/stills/patreon-post](../generated/workflows/creator/stills/patreon-post.md)** | 1024x1280 | `ez_patreon` | Membership post still 4:5 |

## Production plates

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/stills/product-lifestyle](../generated/workflows/creator/stills/product-lifestyle.md)** | 1024x1280 | `ez_lifestyle` | In-use product lifestyle 4:5 |
| **[creator/stills/desk-setup](../generated/workflows/creator/stills/desk-setup.md)** | 1280x720 | `ez_desk` | Workspace establishing still 16:9 |
| **[creator/stills/moodboard-6up](../generated/workflows/creator/stills/moodboard-6up.md)** | 768x432 | `ez_mood_c01` | Six-still moodboard of one identity |
| **[creator/stills/brand-kit-4](../generated/workflows/creator/stills/brand-kit-4.md)** | 768x432 | `ez_brand_01` | Four brand plates, same camera, different lights |
| **[creator/stills/coming-soon](../generated/workflows/creator/stills/coming-soon.md)** | 1280x720 | `ez_soon` | Launch / coming-soon plate 16:9 |

## Silent motion (Wan 2.2)

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/silent/youtube-subscribe-bump](../generated/workflows/creator/silent/youtube-subscribe-bump.md)** | 832x480 | `ez_yt_bump` | Silent YouTube subscribe bumper loop |
| **[creator/silent/instagram-story-loop](../generated/workflows/creator/silent/instagram-story-loop.md)** | 480x832 | `ez_ig_loop` | Silent Instagram Story loop 9:16 |
| **[creator/silent/tiktok-hook](../generated/workflows/creator/silent/tiktok-hook.md)** | 480x832 | `ez_tt_hook` | Silent TikTok hook punch 9:16 |
| **[creator/silent/x-post-5s](../generated/workflows/creator/silent/x-post-5s.md)** | 832x480 | `ez_x_video` | Silent X clip ~5 s 16:9 |
| **[creator/silent/twitch-starting-loop](../generated/workflows/creator/silent/twitch-starting-loop.md)** | 832x480 | `ez_tw_start_loop` | Silent starting-soon loop 16:9 |
| **[creator/silent/twitch-brb-loop](../generated/workflows/creator/silent/twitch-brb-loop.md)** | 832x480 | `ez_tw_brb_loop` | Silent BRB loop 16:9 |
| **[creator/silent/spotify-canvas](../generated/workflows/creator/silent/spotify-canvas.md)** | 480x832 | `ez_spot_canvas` | Silent Spotify Canvas rebound 9:16 |
| **[creator/silent/lyric-bg-loop](../generated/workflows/creator/silent/lyric-bg-loop.md)** | 832x480 | `ez_lyric_loop` | Silent lyric-background loop 16:9 |
| **[creator/silent/product-spin](../generated/workflows/creator/silent/product-spin.md)** | 832x480 | `ez_spin` | Silent product orbit ~5 s |
| **[creator/silent/unbox-hands](../generated/workflows/creator/silent/unbox-hands.md)** | 832x480 | `ez_unbox` | Silent unbox / hands motion ~5 s |
| **[creator/silent/steam-loop](../generated/workflows/creator/silent/steam-loop.md)** | 832x480 | `ez_steam` | Silent steam / kettle loop |
| **[creator/silent/candle-loop](../generated/workflows/creator/silent/candle-loop.md)** | 832x480 | `ez_candle` | Silent candle-flicker loop |
| **[creator/silent/light-leak-loop](../generated/workflows/creator/silent/light-leak-loop.md)** | 832x480 | `ez_leak` | Silent light-leak overlay loop |
| **[creator/silent/logo-sting](../generated/workflows/creator/silent/logo-sting.md)** | 832x480 | `ez_sting` | Silent logo sting ~5 s |
| **[creator/silent/ken-burns](../generated/workflows/creator/silent/ken-burns.md)** | 832x480 | `ez_kenburns` | Silent Ken Burns pan/zoom ~5 s |
| **[creator/silent/tilt-reveal](../generated/workflows/creator/silent/tilt-reveal.md)** | 832x480 | `ez_tilt` | Silent tilt reveal ~5 s |
| **[creator/silent/handheld-vlog](../generated/workflows/creator/silent/handheld-vlog.md)** | 480x832 | `ez_vlog` | Silent handheld vlog micro-shake 9:16 |
| **[creator/silent/macro-product](../generated/workflows/creator/silent/macro-product.md)** | 832x480 | `ez_macro` | Silent macro product crawl ~5 s |
| **[creator/silent/fabric-breeze](../generated/workflows/creator/silent/fabric-breeze.md)** | 832x480 | `ez_breeze` | Silent fabric/hair breeze ~5 s |
| **[creator/silent/city-night](../generated/workflows/creator/silent/city-night.md)** | 832x480 | `ez_night` | Silent night-drive / city-lights ~5 s |
| **[creator/silent/zoom-punch](../generated/workflows/creator/silent/zoom-punch.md)** | 480x832 | `ez_punch` | Silent 9:16 hook zoom punch |
| **[creator/silent/screen-bg-loop](../generated/workflows/creator/silent/screen-bg-loop.md)** | 832x480 | `ez_screen` | Silent desk/screen loop |
| **[creator/silent/confetti-loop](../generated/workflows/creator/silent/confetti-loop.md)** | 832x480 | `ez_confetti` | Silent celebration loop |
| **[creator/silent/paper-flip](../generated/workflows/creator/silent/paper-flip.md)** | 832x480 | `ez_flip` | Silent page / carousel flip ~5 s |
| **[creator/silent/pan-left](../generated/workflows/creator/silent/pan-left.md)** | 832x480 | `ez_pan` | Silent locked-identity pan ~5 s |

## AV (LTX-2.5)

| Workflow | Size | Prefix | What it does |
| --- | --- | --- | --- |
| **[creator/av/youtube-outro-av](../generated/workflows/creator/av/youtube-outro-av.md)** | 1280x704 | `ez_yt_outro` | YouTube outro AV ~5 s with room tone |
| **[creator/av/instagram-reel-lifestyle](../generated/workflows/creator/av/instagram-reel-lifestyle.md)** | 768x1280 | `ez_ig_reel_av` | Instagram lifestyle reel AV 9:16 |
| **[creator/av/tiktok-broll](../generated/workflows/creator/av/tiktok-broll.md)** | 768x1280 | `ez_tt_broll` | TikTok B-roll AV 9:16 |
| **[creator/av/twitch-starting-av](../generated/workflows/creator/av/twitch-starting-av.md)** | 1280x704 | `ez_tw_start_av` | Twitch starting-soon AV ~5 s |
| **[creator/av/music-visual](../generated/workflows/creator/av/music-visual.md)** | 1280x704 | `ez_music_vis` | Light / particle visualizer bed AV ~5 s |
| **[creator/av/recipe-pour](../generated/workflows/creator/av/recipe-pour.md)** | 768x1280 | `ez_pour` | Recipe pour AV 9:16 |
| **[creator/av/product-unbox-av](../generated/workflows/creator/av/product-unbox-av.md)** | 1280x704 | `ez_unbox_av` | Unbox AV with paper SFX ~5 s |
| **[creator/av/desk-work](../generated/workflows/creator/av/desk-work.md)** | 1280x704 | `ez_desk_av` | Desk / keyboard room-tone AV ~5 s |
| **[creator/av/travel-establishing](../generated/workflows/creator/av/travel-establishing.md)** | 1280x704 | `ez_travel` | Travel establishing AV ~5 s |
| **[creator/av/interior-walk](../generated/workflows/creator/av/interior-walk.md)** | 1280x704 | `ez_walk` | Interior walk-through AV ~5 s |
| **[creator/av/fashion-turn](../generated/workflows/creator/av/fashion-turn.md)** | 768x1280 | `ez_turn` | Fashion turn AV 9:16 |
| **[creator/av/workout-rep](../generated/workflows/creator/av/workout-rep.md)** | 768x1280 | `ez_rep` | One exercise-rep AV 9:16 |
| **[creator/av/asmr-macro](../generated/workflows/creator/av/asmr-macro.md)** | 1280x704 | `ez_asmr` | Quiet macro foley AV ~5 s |
| **[creator/av/rain-window](../generated/workflows/creator/av/rain-window.md)** | 1280x704 | `ez_rain` | Rain-on-glass AV ~5 s |
| **[creator/av/fireplace](../generated/workflows/creator/av/fireplace.md)** | 1280x704 | `ez_fire` | Fireplace AV ~5 s |
| **[creator/av/podcast-set](../generated/workflows/creator/av/podcast-set.md)** | 1280x704 | `ez_pod_set` | Podcast-set AV ~5 s |
| **[creator/av/workshop-tools](../generated/workflows/creator/av/workshop-tools.md)** | 1280x704 | `ez_tools` | Workshop tools AV ~5 s |
| **[creator/av/crowd-ambience](../generated/workflows/creator/av/crowd-ambience.md)** | 1280x704 | `ez_crowd` | Distant crowd bed AV ~5 s |

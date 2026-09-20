"""Canonical _lab-relative ids after dropping -lab-example and family prefixes.

Not collected by pytest (leading underscore). Builders, stamps, and the
rename pass import ``OLD_TO_REL`` / ``rel_id``.
"""

from __future__ import annotations

import re

# Cryptic lab-relative id → slightly longer descriptive id.
# Applied after OLD_TO_REL so *-lab-example stems resolve in one rel_id() call.
REL_RENAMES: dict[str, str] = {
    "audio/dub/localize": "audio/dub/clone-translate",
    "audio/finish": "audio/stem-mix",
    "audio/podcast/audio-first": "audio/podcast/two-host-episode",
    "dcc/klein/canny-hero": "dcc/canny-hero",
    "dcc/klein/clay-hero": "dcc/clay-hero",
    "dcc/klein/clay-plates": "dcc/clay-plates",
    "dcc/klein/from-canny": "dcc/canny-hero",
    "dcc/klein/from-clay": "dcc/clay-hero",
    "dcc/klein/from-clay-plates": "dcc/clay-plates",
    "dcc/klein/from-guide-loader": "dcc/guide-still",
    "dcc/klein/guide-still": "dcc/guide-still",
    "dcc/canny-control-5s": "dcc/canny-control-8s",
    "dcc/canny-control-12s": "dcc/canny-control-8s",
    "dcc/depth-control-5s": "dcc/depth-control-8s",
    "dcc/depth-control-12s": "dcc/depth-control-8s",
    "dcc/ltx/canny-control-5s": "dcc/canny-control-8s",
    "dcc/ltx/depth-control-5s": "dcc/depth-control-8s",
    "dcc/ltx/depth-control-shorts": "dcc/depth-control-shorts",
    "dcc/ltx/depth-from-loader": "dcc/depth-from-loader",
    "dcc/ltx/iclora-canny-5s": "dcc/canny-control-8s",
    "dcc/ltx/iclora-depth-5s": "dcc/depth-control-8s",
    "dcc/ltx/iclora-depth-shorts": "dcc/depth-control-shorts",
    "dcc/ltx/iclora-from-guide-loader": "dcc/depth-from-loader",
    "dcc/trellis/from-klein-still": "dcc/still-to-mesh",
    "dcc/trellis/still-to-mesh": "dcc/still-to-mesh",
    "dcc/wan/first-last-from-guide": "dcc/first-last-from-guide",
    "dcc/wan/flf-from-guide": "dcc/first-last-from-guide",
    "klein/banner-wide": "stills/banner-wide",
    "klein/before-after": "stills/before-after",
    "klein/camera-angles": "stills/camera-angles",
    "klein/character-draft": "stills/character-draft",
    "klein/character-tweak": "stills/character-tweak",
    "klein/color-moods": "stills/color-moods",
    "klein/creator/album-cover": "creator/stills/album-cover",
    "klein/creator/audiogram-vert": "creator/stills/audiogram-vert",
    "klein/creator/audiogram-wide": "creator/stills/audiogram-wide",
    "klein/creator/brand-kit-4": "creator/stills/brand-kit-4",
    "klein/creator/coming-soon": "creator/stills/coming-soon",
    "klein/creator/desk-setup": "creator/stills/desk-setup",
    "klein/creator/email-header": "creator/stills/email-header",
    "klein/creator/episode-art": "creator/stills/episode-art",
    "klein/creator/facebook-post": "creator/stills/facebook-post",
    "klein/creator/fb-post": "creator/stills/facebook-post",
    "klein/creator/ig-carousel-5": "creator/stills/instagram-carousel-5",
    "klein/creator/ig-grid-3up": "creator/stills/instagram-grid-3up",
    "klein/creator/ig-highlight": "creator/stills/instagram-highlight",
    "klein/creator/ig-landscape": "creator/stills/instagram-landscape",
    "klein/creator/ig-portrait": "creator/stills/instagram-portrait",
    "klein/creator/ig-profile": "creator/stills/instagram-profile",
    "klein/creator/ig-reel-cover": "creator/stills/instagram-reel-cover",
    "klein/creator/ig-story": "creator/stills/instagram-story",
    "klein/creator/instagram-carousel-5": "creator/stills/instagram-carousel-5",
    "klein/creator/instagram-grid-3up": "creator/stills/instagram-grid-3up",
    "klein/creator/instagram-highlight": "creator/stills/instagram-highlight",
    "klein/creator/instagram-landscape": "creator/stills/instagram-landscape",
    "klein/creator/instagram-portrait": "creator/stills/instagram-portrait",
    "klein/creator/instagram-profile": "creator/stills/instagram-profile",
    "klein/creator/instagram-reel-cover": "creator/stills/instagram-reel-cover",
    "klein/creator/instagram-story": "creator/stills/instagram-story",
    "klein/creator/li-article": "creator/stills/linkedin-article",
    "klein/creator/li-banner": "creator/stills/linkedin-banner",
    "klein/creator/li-carousel-5": "creator/stills/linkedin-carousel-5",
    "klein/creator/li-landscape": "creator/stills/linkedin-landscape",
    "klein/creator/li-post": "creator/stills/linkedin-post",
    "klein/creator/linkedin-article": "creator/stills/linkedin-article",
    "klein/creator/linkedin-banner": "creator/stills/linkedin-banner",
    "klein/creator/linkedin-carousel-5": "creator/stills/linkedin-carousel-5",
    "klein/creator/linkedin-landscape": "creator/stills/linkedin-landscape",
    "klein/creator/linkedin-post": "creator/stills/linkedin-post",
    "klein/creator/lyric-card": "creator/stills/lyric-card",
    "klein/creator/merch-mug": "creator/stills/merch-mug",
    "klein/creator/merch-tee": "creator/stills/merch-tee",
    "klein/creator/moodboard-6up": "creator/stills/moodboard-6up",
    "klein/creator/patreon-post": "creator/stills/patreon-post",
    "klein/creator/pin-standard": "creator/stills/pinterest-pin",
    "klein/creator/pin-story": "creator/stills/pinterest-story",
    "klein/creator/pinterest-pin": "creator/stills/pinterest-pin",
    "klein/creator/pinterest-story": "creator/stills/pinterest-story",
    "klein/creator/poster-portrait": "creator/stills/poster-portrait",
    "klein/creator/product-lifestyle": "creator/stills/product-lifestyle",
    "klein/creator/slide-title": "creator/stills/slide-title",
    "klein/creator/spotify-canvas-still": "creator/stills/spotify-canvas-still",
    "klein/creator/spotify-playlist": "creator/stills/spotify-playlist",
    "klein/creator/substack-hero": "creator/stills/substack-hero",
    "klein/creator/threads-portrait": "creator/stills/threads-portrait",
    "klein/creator/tiktok-cover": "creator/stills/tiktok-cover",
    "klein/creator/tiktok-shop": "creator/stills/tiktok-shop",
    "klein/creator/tt-cover": "creator/stills/tiktok-cover",
    "klein/creator/tt-shop": "creator/stills/tiktok-shop",
    "klein/creator/twitch-banner": "creator/stills/twitch-banner",
    "klein/creator/twitch-brb": "creator/stills/twitch-brb",
    "klein/creator/twitch-ending": "creator/stills/twitch-ending",
    "klein/creator/twitch-offline": "creator/stills/twitch-offline",
    "klein/creator/twitch-overlay": "creator/stills/twitch-overlay",
    "klein/creator/twitch-panel": "creator/stills/twitch-panel",
    "klein/creator/twitch-profile": "creator/stills/twitch-profile",
    "klein/creator/twitch-starting": "creator/stills/twitch-starting",
    "klein/creator/x-card": "creator/stills/x-card",
    "klein/creator/x-header": "creator/stills/x-header",
    "klein/creator/x-post": "creator/stills/x-post",
    "klein/creator/youtube-channel-art": "creator/stills/youtube-channel-art",
    "klein/creator/youtube-channel-icon": "creator/stills/youtube-channel-icon",
    "klein/creator/youtube-chapter-card": "creator/stills/youtube-chapter-card",
    "klein/creator/youtube-community": "creator/stills/youtube-community",
    "klein/creator/youtube-end-screen": "creator/stills/youtube-end-screen",
    "klein/creator/youtube-shorts-thumb": "creator/stills/youtube-shorts-thumb",
    "klein/creator/youtube-subscribe-plate": "creator/stills/youtube-subscribe-plate",
    "klein/creator/yt-channel-art": "creator/stills/youtube-channel-art",
    "klein/creator/yt-channel-icon": "creator/stills/youtube-channel-icon",
    "klein/creator/yt-chapter-card": "creator/stills/youtube-chapter-card",
    "klein/creator/yt-community": "creator/stills/youtube-community",
    "klein/creator/yt-end-screen": "creator/stills/youtube-end-screen",
    "klein/creator/yt-shorts-thumb": "creator/stills/youtube-shorts-thumb",
    "klein/creator/yt-subscribe-plate": "creator/stills/youtube-subscribe-plate",
    "klein/creator/zoom-bg": "creator/stills/zoom-bg",
    "klein/dream-house": "stills/dream-house",
    "klein/dream-house-clay": "stills/dream-house-clay",
    "klein/endcard-cta": "stills/endcard-cta",
    "klein/food-tabletop": "stills/food-tabletop",
    "klein/hook-still": "stills/hook-still",
    "klein/identity-sheet": "stills/identity-sheet",
    "klein/ig-square": "stills/instagram-square",
    "klein/image-studio": "stills/image-studio",
    "klein/instagram-square": "stills/instagram-square",
    "klein/lighting-trio": "stills/lighting-trio",
    "klein/lower-third-bg": "stills/lower-third-bg",
    "klein/og-blog": "stills/open-graph",
    "klein/open-graph": "stills/open-graph",
    "klein/platform-pack": "stills/platform-pack",
    "klein/podcast-cover": "stills/podcast-cover",
    "klein/product-packshot": "stills/product-packshot",
    "klein/quote-bg": "stills/quote-bg",
    "klein/shorts-still": "stills/shorts-still",
    "klein/still-daily": "stills/still-daily",
    "klein/still-draft": "stills/still-draft",
    "klein/still-hero": "stills/still-hero",
    "klein/still-studio": "stills/still-studio",
    "klein/storyboard-6up": "stills/storyboard-6up",
    "klein/style-lock": "stills/style-lock",
    "klein/talking-head": "stills/talking-head",
    "klein/text-swap": "stills/text-swap",
    "klein/thumbnail": "stills/thumbnail",
    "klein/time-of-day": "stills/time-of-day",
    "ltx/a2v-5s": "motion/av/audio-to-video-8s",
    "ltx/audio-to-video-5s": "motion/av/audio-to-video-8s",
    "ltx/broll-ambient": "motion/av/broll-ambient",
    "ltx/creator/asmr-macro": "creator/av/asmr-macro",
    "ltx/creator/crowd-ambience": "creator/av/crowd-ambience",
    "ltx/creator/desk-work": "creator/av/desk-work",
    "ltx/creator/fashion-turn": "creator/av/fashion-turn",
    "ltx/creator/fireplace": "creator/av/fireplace",
    "ltx/creator/ig-reel-lifestyle": "creator/av/instagram-reel-lifestyle",
    "ltx/creator/instagram-reel-lifestyle": "creator/av/instagram-reel-lifestyle",
    "ltx/creator/interior-walk": "creator/av/interior-walk",
    "ltx/creator/music-visual": "creator/av/music-visual",
    "ltx/creator/podcast-set": "creator/av/podcast-set",
    "ltx/creator/product-unbox-av": "creator/av/product-unbox-av",
    "ltx/creator/rain-window": "creator/av/rain-window",
    "ltx/creator/recipe-pour": "creator/av/recipe-pour",
    "ltx/creator/tiktok-broll": "creator/av/tiktok-broll",
    "ltx/creator/travel-establishing": "creator/av/travel-establishing",
    "ltx/creator/tt-broll": "creator/av/tiktok-broll",
    "ltx/creator/twitch-starting-av": "creator/av/twitch-starting-av",
    "ltx/creator/workout-rep": "creator/av/workout-rep",
    "ltx/creator/workshop-tools": "creator/av/workshop-tools",
    "ltx/creator/youtube-outro-av": "creator/av/youtube-outro-av",
    "ltx/creator/yt-outro-av": "creator/av/youtube-outro-av",
    "ltx/dialogue-5s": "motion/av/dialogue-8s",
    "ltx/first-last-5s": "motion/av/first-last-8s",
    "ltx/flf-5s": "motion/av/first-last-8s",
    "ltx/hook-av": "motion/av/hook-av",
    "ltx/i2v-5s": "motion/av/still-to-video-8s",
    "ltx/i2v-shot": "motion/av/still-to-shot",
    "ltx/interior-ambience": "motion/av/interior-ambience",
    "ltx/multishot-5s": "motion/av/multishot-8s",
    "ltx/product-hero": "motion/av/product-hero",
    "ltx/shorts-i2v": "motion/av/shorts-still-8s",
    "ltx/shorts-still-5s": "motion/av/shorts-still-8s",
    "ltx/still-to-shot": "motion/av/still-to-shot",
    "ltx/still-to-video-5s": "motion/av/still-to-video-8s",
    "ltx/t2v-5s": "motion/av/text-to-video-8s",
    "ltx/text-to-video-5s": "motion/av/text-to-video-8s",
    "ltx/weather-broll": "motion/av/weather-broll",
    "motion/av/audio-to-video-5s": "motion/av/audio-to-video-8s",
    "motion/av/audio-to-video-12s": "motion/av/audio-to-video-8s",
    "motion/av/dialogue-5s": "motion/av/dialogue-8s",
    "motion/av/dialogue-12s": "motion/av/dialogue-8s",
    "motion/av/first-last-5s": "motion/av/first-last-8s",
    "motion/av/first-last-12s": "motion/av/first-last-8s",
    "motion/av/multishot-5s": "motion/av/multishot-8s",
    "motion/av/multishot-12s": "motion/av/multishot-8s",
    "motion/av/shorts-still-5s": "motion/av/shorts-still-8s",
    "motion/av/shorts-still-12s": "motion/av/shorts-still-8s",
    "motion/av/still-to-video-5s": "motion/av/still-to-video-8s",
    "motion/av/still-to-video-12s": "motion/av/still-to-video-8s",
    "motion/av/text-to-video-5s": "motion/av/text-to-video-8s",
    "motion/av/text-to-video-12s": "motion/av/text-to-video-8s",
    "optional/klein/trellis2": "optional/trellis2",
    "optional/wan/i2v-a14b": "optional/still-to-video-a14b",
    "optional/wan/still-to-video-a14b": "optional/still-to-video-a14b",
    "shorts/breakwater/act-01": "films/breakwater/act-01",
    "shorts/breakwater/act-02": "films/breakwater/act-02",
    "shorts/breakwater/act-03": "films/breakwater/act-03",
    "shorts/breakwater/act-04": "films/breakwater/act-04",
    "shorts/breakwater/act-05": "films/breakwater/act-05",
    "shorts/glasshouse/act-01": "films/glasshouse/act-01",
    "shorts/glasshouse/act-02": "films/glasshouse/act-02",
    "shorts/glasshouse/act-03": "films/glasshouse/act-03",
    "shorts/glasshouse/act-04": "films/glasshouse/act-04",
    "shorts/glasshouse/act-05": "films/glasshouse/act-05",
    "shorts/go-see": "films/go-see",
    "shorts/last-lane/act-01": "films/last-lane/act-01",
    "shorts/last-lane/act-02": "films/last-lane/act-02",
    "shorts/last-lane/act-03": "films/last-lane/act-03",
    "shorts/last-lane/act-04": "films/last-lane/act-04",
    "shorts/last-lane/act-05": "films/last-lane/act-05",
    "shorts/night-oven/act-01": "films/night-oven/act-01",
    "shorts/night-oven/act-02": "films/night-oven/act-02",
    "shorts/night-oven/act-03": "films/night-oven/act-03",
    "shorts/night-oven/act-04": "films/night-oven/act-04",
    "shorts/night-oven/act-05": "films/night-oven/act-05",
    "shorts/still-here": "films/still-here",
    "shorts/switchyard": "films/switchyard",
    "shorts/tide-table/act-01": "films/tide-table/act-01",
    "shorts/tide-table/act-02": "films/tide-table/act-02",
    "shorts/tide-table/act-03": "films/tide-table/act-03",
    "shorts/tide-table/act-04": "films/tide-table/act-04",
    "shorts/tide-table/act-05": "films/tide-table/act-05",
    "wan/bumper-loop": "motion/loops/bumper-loop",
    "wan/creator/candle-loop": "creator/silent/candle-loop",
    "wan/creator/city-night": "creator/silent/city-night",
    "wan/creator/confetti-loop": "creator/silent/confetti-loop",
    "wan/creator/fabric-breeze": "creator/silent/fabric-breeze",
    "wan/creator/handheld-vlog": "creator/silent/handheld-vlog",
    "wan/creator/ig-story-loop": "creator/silent/instagram-story-loop",
    "wan/creator/instagram-story-loop": "creator/silent/instagram-story-loop",
    "wan/creator/ken-burns": "creator/silent/ken-burns",
    "wan/creator/light-leak-loop": "creator/silent/light-leak-loop",
    "wan/creator/logo-sting": "creator/silent/logo-sting",
    "wan/creator/lyric-bg-loop": "creator/silent/lyric-bg-loop",
    "wan/creator/macro-product": "creator/silent/macro-product",
    "wan/creator/pan-left": "creator/silent/pan-left",
    "wan/creator/paper-flip": "creator/silent/paper-flip",
    "wan/creator/product-spin": "creator/silent/product-spin",
    "wan/creator/screen-bg-loop": "creator/silent/screen-bg-loop",
    "wan/creator/spotify-canvas": "creator/silent/spotify-canvas",
    "wan/creator/steam-loop": "creator/silent/steam-loop",
    "wan/creator/tiktok-hook": "creator/silent/tiktok-hook",
    "wan/creator/tilt-reveal": "creator/silent/tilt-reveal",
    "wan/creator/tt-hook": "creator/silent/tiktok-hook",
    "wan/creator/twitch-brb-loop": "creator/silent/twitch-brb-loop",
    "wan/creator/twitch-starting-loop": "creator/silent/twitch-starting-loop",
    "wan/creator/unbox-hands": "creator/silent/unbox-hands",
    "wan/creator/x-post-5s": "creator/silent/x-post-5s",
    "wan/creator/youtube-subscribe-bump": "creator/silent/youtube-subscribe-bump",
    "wan/creator/yt-subscribe-bump": "creator/silent/youtube-subscribe-bump",
    "wan/creator/zoom-punch": "creator/silent/zoom-punch",
    "wan/first-last-5s": "motion/silent/first-last-5s",
    "wan/flf-5s": "motion/silent/first-last-5s",
    "wan/gif-loop": "motion/loops/gif-loop",
    "wan/i2v-5s": "motion/silent/still-to-video-5s",
    "wan/i2v-shot": "motion/silent/still-to-shot",
    "wan/orbit-i2v": "motion/silent/orbit-still-5s",
    "wan/orbit-still-5s": "motion/silent/orbit-still-5s",
    "wan/parallax-i2v": "motion/silent/parallax-still-5s",
    "wan/parallax-still-5s": "motion/silent/parallax-still-5s",
    "wan/push-in-i2v": "motion/silent/push-in-still-5s",
    "wan/push-in-still-5s": "motion/silent/push-in-still-5s",
    "wan/shorts-i2v": "motion/silent/shorts-still-5s",
    "wan/shorts-still-5s": "motion/silent/shorts-still-5s",
    "wan/sticker-loop": "motion/loops/sticker-loop",
    "wan/still-to-shot": "motion/silent/still-to-shot",
    "wan/still-to-video-5s": "motion/silent/still-to-video-5s",
    "wan/t2v-5s": "motion/silent/text-to-video-5s",
    "wan/text-to-video-5s": "motion/silent/text-to-video-5s",
    "wan/vace-join": "motion/silent/vace-join",
}

# Old unique stem (no .json) → _lab-relative id (no .json).
OLD_TO_REL: dict[str, str] = {
    "klein-banner-wide-lab-example": "klein/banner-wide",
    "klein-before-after-lab-example": "klein/before-after",
    "klein-camera-angles-lab-example": "klein/camera-angles",
    "klein-character-draft-lab-example": "klein/character-draft",
    "klein-character-tweak-lab-example": "klein/character-tweak",
    "klein-color-moods-lab-example": "klein/color-moods",
    "klein-dream-house-clay-lab-example": "klein/dream-house-clay",
    "klein-dream-house-lab-example": "klein/dream-house",
    "klein-endcard-cta-lab-example": "klein/endcard-cta",
    "klein-food-tabletop-lab-example": "klein/food-tabletop",
    "klein-hook-still-lab-example": "klein/hook-still",
    "klein-identity-sheet-lab-example": "klein/identity-sheet",
    "klein-ig-square-lab-example": "klein/ig-square",
    "klein-lighting-trio-lab-example": "klein/lighting-trio",
    "klein-lower-third-bg-lab-example": "klein/lower-third-bg",
    "klein-og-blog-lab-example": "klein/og-blog",
    "klein-platform-pack-lab-example": "klein/platform-pack",
    "klein-podcast-cover-lab-example": "klein/podcast-cover",
    "klein-product-packshot-lab-example": "klein/product-packshot",
    "klein-quote-bg-lab-example": "klein/quote-bg",
    "klein-shorts-still-lab-example": "klein/shorts-still",
    "klein-still-daily-lab-example": "klein/still-daily",
    "klein-still-draft-lab-example": "klein/still-draft",
    "klein-still-hero-lab-example": "klein/still-hero",
    "klein-storyboard-6up-lab-example": "klein/storyboard-6up",
    "klein-style-lock-lab-example": "klein/style-lock",
    "klein-talking-head-lab-example": "klein/talking-head",
    "klein-thumbnail-lab-example": "klein/thumbnail",
    "klein-time-of-day-lab-example": "klein/time-of-day",
    "wan-bumper-loop-lab-example": "wan/bumper-loop",
    "wan-flf-5s-lab-example": "wan/flf-5s",
    "wan-gif-loop-lab-example": "wan/gif-loop",
    "wan-i2v-5s-lab-example": "wan/i2v-5s",
    "wan-i2v-shot-lab-example": "wan/i2v-shot",
    "wan-orbit-i2v-lab-example": "wan/orbit-i2v",
    "wan-parallax-i2v-lab-example": "wan/parallax-i2v",
    "wan-push-in-i2v-lab-example": "wan/push-in-i2v",
    "wan-shorts-i2v-lab-example": "wan/shorts-i2v",
    "wan-sticker-loop-lab-example": "wan/sticker-loop",
    "wan-t2v-5s-lab-example": "wan/t2v-5s",
    "wan-vace-join-lab-example": "wan/vace-join",
    "ltx-broll-ambient-lab-example": "ltx/broll-ambient",
    "ltx-hook-av-lab-example": "ltx/hook-av",
    "ltx-i2v-5s-lab-example": "ltx/i2v-5s",
    "ltx-i2v-shot-lab-example": "ltx/i2v-shot",
    "ltx-interior-ambience-lab-example": "ltx/interior-ambience",
    "ltx-shorts-i2v-lab-example": "ltx/shorts-i2v",
    "ltx-t2v-5s-lab-example": "ltx/t2v-5s",
    "ltx-weather-broll-lab-example": "ltx/weather-broll",
    "film-go-see-90s-run-lab-example": "shorts/go-see",
    "film-still-here-90s-lab-example": "shorts/still-here",
    "film-switchyard-90s-lab-example": "shorts/switchyard",
    "beat-sheet-lab-example": "inspire/beat-sheet",
    "prompt-forge-lab-example": "inspire/prompt-forge",
    "research-chat-lab-example": "inspire/research-chat",
    "klein-from-canny-lab-example": "dcc/klein/from-canny",
    "klein-from-clay-lab-example": "dcc/klein/from-clay",
    "klein-from-clay-plates-lab-example": "dcc/klein/from-clay-plates",
    "klein-from-guide-loader-lab-example": "dcc/klein/from-guide-loader",
    "ltx-iclora-canny-5s-lab-example": "dcc/ltx/iclora-canny-5s",
    "ltx-iclora-depth-5s-lab-example": "dcc/ltx/iclora-depth-5s",
    "ltx-iclora-depth-shorts-lab-example": "dcc/ltx/iclora-depth-shorts",
    "ltx-iclora-from-guide-loader-lab-example": "dcc/ltx/iclora-from-guide-loader",
    "trellis-from-klein-still-lab-example": "dcc/trellis/from-klein-still",
    "wan-flf-from-guide-lab-example": "dcc/wan/flf-from-guide",
    "klein-trellis2-lab-example": "optional/klein/trellis2",
    "longcat-video-lab-example": "optional/longcat-video",
    "wan-i2v-a14b-lab-example": "optional/wan/i2v-a14b",
    "audio-finish-lab-example": "audio/finish",
    "dub-localize-lab-example": "audio/dub/localize",
    "podcast-audio-first-lab-example": "audio/podcast/audio-first",
    "podcast-radio-drama-lab-example": "audio/podcast/radio-drama",
    "music-rap-draft-lab-example": "audio/music/rap-draft",
    "music-rap-full-lab-example": "audio/music/rap-full",
}


def rel_id(name: str) -> str:
    """Return the _lab-relative id for an old stem, new rel, or filename.

    Arguments:
        name: Old ``*-lab-example`` stem, ``lane/stem``, or ``stem.json``.
    Returns:
        Slash-separated id under ``workflows/_lab`` with no ``.json``.
    """
    text = str(name).replace("\\", "/").strip().lstrip("./")
    text = text.removeprefix("_lab/")
    if text.endswith(".json"):
        text = text[: -len(".json")]
    if text in OLD_TO_REL:
        text = OLD_TO_REL[text]
    else:
        basename = text.rsplit("/", 1)[-1]
        if basename in OLD_TO_REL:
            text = OLD_TO_REL[basename]
    return REL_RENAMES.get(text, text)


# Stems that are also English words. Full rels still rewrite; bare tokens do not.
# Shared Wan/LTX 5s stems must not token-rewrite the Wan silent graphs.
_GENERIC_STEMS = frozenset(
    {
        "finish",
        "localize",
        "still-to-video-5s",
        "text-to-video-5s",
        "shorts-still-5s",
        "first-last-5s",
        "i2v-5s",
        "t2v-5s",
        "flf-5s",
        "a2v-5s",
        "shorts-i2v",
    }
)


def stem_renames() -> dict[str, str]:
    """File-stem map implied by ``REL_RENAMES`` (no hyphenated collisions).

    Returns:
        Old file stem → new file stem. Values agree when two lanes share a stem.
        Generic English stems (``finish``, ``localize``) are omitted.
    """
    stems: dict[str, str] = {}
    for old, new in REL_RENAMES.items():
        old_stem = old.rsplit("/", 1)[-1]
        new_stem = new.rsplit("/", 1)[-1]
        if old_stem == new_stem or old_stem in _GENERIC_STEMS:
            continue
        previous = stems.get(old_stem)
        if previous is not None and previous != new_stem:
            raise ValueError(f"stem collision {old_stem}: {previous} vs {new_stem}")
        stems[old_stem] = new_stem
    return stems


def rewrite_lab_names(text: str) -> str:
    """Replace old lab-relative ids, then unique file stems, in ``text``.

    Full rels go first so ``wan/i2v-5s`` becomes ``motion/silent/still-to-video-5s``.
    Stem tokens skip a leading hyphen so subgraph ``wan-i2v-5s`` and print
    mode ``klein-from-clay`` stay put.

    Arguments:
        text: Source or JSON text.
    Returns:
        Rewritten text.
    """
    for old, new in sorted(REL_RENAMES.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(old, new)
    for old, new in sorted(stem_renames().items(), key=lambda item: len(item[0]), reverse=True):
        text = re.sub(
            rf"(?<![A-Za-z0-9_-]){re.escape(old)}(?![A-Za-z0-9_-])",
            new,
            text,
        )
    return text


def file_stem(rel: str) -> str:
    """Last path component of a lab-relative id."""
    return rel_id(rel).rsplit("/", 1)[-1]

"""Canonical _lab-relative ids after dropping -lab-example and family prefixes.

Not collected by pytest (leading underscore). Builders, stamps, and the
rename pass import ``OLD_TO_REL`` / ``rel_id``.
"""

from __future__ import annotations

import re

# Cryptic lab-relative id -> slightly longer descriptive id.
# Applied after OLD_TO_REL so *-lab-example stems resolve in one rel_id() call.
REL_RENAMES: dict[str, str] = {
    # One-graph lane moves that a subtree relocation cannot express: each of
    # these graphs pins a different model family than the lane it grew up in.
    # The value is the final id, so it must already read as the operator sees it.
    "stills/talking-head": "video/av/talking-head",
    "stills/still-flux3-fast": "labs/opt-in/still-flux3-fast",
    "stills/still-flux3-quality": "labs/opt-in/still-flux3-quality",
    "dcc/still-to-mesh": "3d/still-to-mesh",
    "optional/trellis2": "3d/trellis2",
    "audio/dub/localize": "audio/dub/clone-translate",
    "audio/finish": "audio/stem-mix",
    "audio/podcast/audio-first": "audio/podcast/two-host-episode",
    "dcc/klein/canny-hero": "guides/canny-hero",
    "dcc/klein/clay-hero": "guides/clay-hero",
    "dcc/klein/clay-plates": "guides/clay-plates",
    "dcc/klein/from-canny": "guides/canny-hero",
    "dcc/klein/from-clay": "guides/clay-hero",
    "dcc/klein/from-clay-plates": "guides/clay-plates",
    "dcc/klein/from-guide-loader": "guides/guide-still",
    "dcc/klein/guide-still": "guides/guide-still",
    "dcc/canny-control-5s": "guides/canny-control-8s",
    "dcc/canny-control-12s": "guides/canny-control-8s",
    "dcc/depth-control-5s": "guides/depth-control-8s",
    "dcc/depth-control-12s": "guides/depth-control-8s",
    "dcc/ltx/canny-control-5s": "guides/canny-control-8s",
    "dcc/ltx/depth-control-5s": "guides/depth-control-8s",
    "dcc/ltx/depth-control-shorts": "guides/depth-control-shorts",
    "dcc/ltx/depth-from-loader": "guides/depth-from-loader",
    "dcc/ltx/iclora-canny-5s": "guides/canny-control-8s",
    "dcc/ltx/iclora-depth-5s": "guides/depth-control-8s",
    "dcc/ltx/iclora-depth-shorts": "guides/depth-control-shorts",
    "dcc/ltx/iclora-from-guide-loader": "guides/depth-from-loader",
    "dcc/trellis/from-klein-still": "3d/still-to-mesh",
    "dcc/trellis/still-to-mesh": "3d/still-to-mesh",
    "dcc/wan/first-last-from-guide": "guides/first-last-from-guide",
    "dcc/wan/flf-from-guide": "guides/first-last-from-guide",
    "klein/banner-wide": "photos/banner-wide",
    "klein/before-after": "photos/before-after",
    "klein/camera-angles": "photos/camera-angles",
    "klein/character-draft": "photos/character-draft",
    "klein/character-tweak": "photos/character-tweak",
    "klein/color-moods": "photos/color-moods",
    "klein/creator/album-cover": "social/stills/album-cover",
    "klein/creator/audiogram-vert": "social/stills/audiogram-vert",
    "klein/creator/audiogram-wide": "social/stills/audiogram-wide",
    "klein/creator/brand-kit-4": "social/stills/brand-kit-4",
    "klein/creator/coming-soon": "social/stills/coming-soon",
    "klein/creator/desk-setup": "social/stills/desk-setup",
    "klein/creator/email-header": "social/stills/email-header",
    "klein/creator/episode-art": "social/stills/episode-art",
    "klein/creator/facebook-post": "social/stills/facebook-post",
    "klein/creator/fb-post": "social/stills/facebook-post",
    "klein/creator/ig-carousel-5": "social/stills/instagram-carousel-5",
    "klein/creator/ig-grid-3up": "social/stills/instagram-grid-3up",
    "klein/creator/ig-highlight": "social/stills/instagram-highlight",
    "klein/creator/ig-landscape": "social/stills/instagram-landscape",
    "klein/creator/ig-portrait": "social/stills/instagram-portrait",
    "klein/creator/ig-profile": "social/stills/instagram-profile",
    "klein/creator/ig-reel-cover": "social/stills/instagram-reel-cover",
    "klein/creator/ig-story": "social/stills/instagram-story",
    "klein/creator/instagram-carousel-5": "social/stills/instagram-carousel-5",
    "klein/creator/instagram-grid-3up": "social/stills/instagram-grid-3up",
    "klein/creator/instagram-highlight": "social/stills/instagram-highlight",
    "klein/creator/instagram-landscape": "social/stills/instagram-landscape",
    "klein/creator/instagram-portrait": "social/stills/instagram-portrait",
    "klein/creator/instagram-profile": "social/stills/instagram-profile",
    "klein/creator/instagram-reel-cover": "social/stills/instagram-reel-cover",
    "klein/creator/instagram-story": "social/stills/instagram-story",
    "klein/creator/li-article": "social/stills/linkedin-article",
    "klein/creator/li-banner": "social/stills/linkedin-banner",
    "klein/creator/li-carousel-5": "social/stills/linkedin-carousel-5",
    "klein/creator/li-landscape": "social/stills/linkedin-landscape",
    "klein/creator/li-post": "social/stills/linkedin-post",
    "klein/creator/linkedin-article": "social/stills/linkedin-article",
    "klein/creator/linkedin-banner": "social/stills/linkedin-banner",
    "klein/creator/linkedin-carousel-5": "social/stills/linkedin-carousel-5",
    "klein/creator/linkedin-landscape": "social/stills/linkedin-landscape",
    "klein/creator/linkedin-post": "social/stills/linkedin-post",
    "klein/creator/lyric-card": "social/stills/lyric-card",
    "klein/creator/merch-mug": "social/stills/merch-mug",
    "klein/creator/merch-tee": "social/stills/merch-tee",
    "klein/creator/moodboard-6up": "social/stills/moodboard-6up",
    "klein/creator/patreon-post": "social/stills/patreon-post",
    "klein/creator/pin-standard": "social/stills/pinterest-pin",
    "klein/creator/pin-story": "social/stills/pinterest-story",
    "klein/creator/pinterest-pin": "social/stills/pinterest-pin",
    "klein/creator/pinterest-story": "social/stills/pinterest-story",
    "klein/creator/poster-portrait": "social/stills/poster-portrait",
    "klein/creator/product-lifestyle": "social/stills/product-lifestyle",
    "klein/creator/slide-title": "social/stills/slide-title",
    "klein/creator/spotify-canvas-still": "social/stills/spotify-canvas-still",
    "klein/creator/spotify-playlist": "social/stills/spotify-playlist",
    "klein/creator/substack-hero": "social/stills/substack-hero",
    "klein/creator/threads-portrait": "social/stills/threads-portrait",
    "klein/creator/tiktok-cover": "social/stills/tiktok-cover",
    "klein/creator/tiktok-shop": "social/stills/tiktok-shop",
    "klein/creator/tt-cover": "social/stills/tiktok-cover",
    "klein/creator/tt-shop": "social/stills/tiktok-shop",
    "klein/creator/twitch-banner": "social/stills/twitch-banner",
    "klein/creator/twitch-brb": "social/stills/twitch-brb",
    "klein/creator/twitch-ending": "social/stills/twitch-ending",
    "klein/creator/twitch-offline": "social/stills/twitch-offline",
    "klein/creator/twitch-overlay": "social/stills/twitch-overlay",
    "klein/creator/twitch-panel": "social/stills/twitch-panel",
    "klein/creator/twitch-profile": "social/stills/twitch-profile",
    "klein/creator/twitch-starting": "social/stills/twitch-starting",
    "klein/creator/x-card": "social/stills/x-card",
    "klein/creator/x-header": "social/stills/x-header",
    "klein/creator/x-post": "social/stills/x-post",
    "klein/creator/youtube-channel-art": "social/stills/youtube-channel-art",
    "klein/creator/youtube-channel-icon": "social/stills/youtube-channel-icon",
    "klein/creator/youtube-chapter-card": "social/stills/youtube-chapter-card",
    "klein/creator/youtube-community": "social/stills/youtube-community",
    "klein/creator/youtube-end-screen": "social/stills/youtube-end-screen",
    "klein/creator/youtube-shorts-thumb": "social/stills/youtube-shorts-thumb",
    "klein/creator/youtube-subscribe-plate": "social/stills/youtube-subscribe-plate",
    "klein/creator/yt-channel-art": "social/stills/youtube-channel-art",
    "klein/creator/yt-channel-icon": "social/stills/youtube-channel-icon",
    "klein/creator/yt-chapter-card": "social/stills/youtube-chapter-card",
    "klein/creator/yt-community": "social/stills/youtube-community",
    "klein/creator/yt-end-screen": "social/stills/youtube-end-screen",
    "klein/creator/yt-shorts-thumb": "social/stills/youtube-shorts-thumb",
    "klein/creator/yt-subscribe-plate": "social/stills/youtube-subscribe-plate",
    "klein/creator/zoom-bg": "social/stills/zoom-bg",
    "klein/dream-house": "photos/dream-house",
    "klein/dream-house-clay": "photos/dream-house-clay",
    "klein/endcard-cta": "photos/endcard-cta",
    "klein/food-tabletop": "photos/food-tabletop",
    "klein/hook-still": "photos/hook-still",
    "klein/identity-sheet": "photos/identity-sheet",
    "klein/ig-square": "photos/instagram-square",
    "klein/image-studio": "photos/image-studio",
    "klein/instagram-square": "photos/instagram-square",
    "klein/lighting-trio": "photos/lighting-trio",
    "klein/lower-third-bg": "photos/lower-third-bg",
    "klein/og-blog": "photos/open-graph",
    "klein/open-graph": "photos/open-graph",
    "klein/platform-pack": "photos/platform-pack",
    "klein/podcast-cover": "photos/podcast-cover",
    "klein/product-packshot": "photos/product-packshot",
    "klein/quote-bg": "photos/quote-bg",
    "klein/shorts-still": "photos/shorts-still",
    "klein/still-daily": "photos/still-daily",
    "klein/still-draft": "photos/still-draft",
    "klein/still-hero": "photos/still-hero",
    "klein/still-studio": "photos/still-studio",
    "klein/storyboard-6up": "photos/storyboard-6up",
    "klein/style-lock": "photos/style-lock",
    "klein/talking-head": "video/av/talking-head",
    "klein/text-swap": "photos/text-swap",
    "klein/thumbnail": "photos/thumbnail",
    "klein/time-of-day": "photos/time-of-day",
    "ltx/a2v-5s": "video/av/audio-to-video-8s",
    "ltx/audio-to-video-5s": "video/av/audio-to-video-8s",
    "ltx/broll-ambient": "video/av/broll-ambient",
    "ltx/creator/asmr-macro": "social/av/asmr-macro",
    "ltx/creator/crowd-ambience": "social/av/crowd-ambience",
    "ltx/creator/desk-work": "social/av/desk-work",
    "ltx/creator/fashion-turn": "social/av/fashion-turn",
    "ltx/creator/fireplace": "social/av/fireplace",
    "ltx/creator/ig-reel-lifestyle": "social/av/instagram-reel-lifestyle",
    "ltx/creator/instagram-reel-lifestyle": "social/av/instagram-reel-lifestyle",
    "ltx/creator/interior-walk": "social/av/interior-walk",
    "ltx/creator/music-visual": "social/av/music-visual",
    "ltx/creator/podcast-set": "social/av/podcast-set",
    "ltx/creator/product-unbox-av": "social/av/product-unbox-av",
    "ltx/creator/rain-window": "social/av/rain-window",
    "ltx/creator/recipe-pour": "social/av/recipe-pour",
    "ltx/creator/tiktok-broll": "social/av/tiktok-broll",
    "ltx/creator/travel-establishing": "social/av/travel-establishing",
    "ltx/creator/tt-broll": "social/av/tiktok-broll",
    "ltx/creator/twitch-starting-av": "social/av/twitch-starting-av",
    "ltx/creator/workout-rep": "social/av/workout-rep",
    "ltx/creator/workshop-tools": "social/av/workshop-tools",
    "ltx/creator/youtube-outro-av": "social/av/youtube-outro-av",
    "ltx/creator/yt-outro-av": "social/av/youtube-outro-av",
    "ltx/dialogue-5s": "video/av/dialogue-8s",
    "ltx/first-last-5s": "video/av/first-last-8s",
    "ltx/flf-5s": "video/av/first-last-8s",
    "ltx/hook-av": "video/av/hook-av",
    "ltx/i2v-5s": "video/av/still-to-video-8s",
    "ltx/i2v-shot": "video/av/still-to-shot",
    "ltx/interior-ambience": "video/av/interior-ambience",
    "ltx/multishot-5s": "video/av/multishot-8s",
    "ltx/product-hero": "video/av/product-hero",
    "ltx/shorts-i2v": "video/av/shorts-still-8s",
    "ltx/shorts-still-5s": "video/av/shorts-still-8s",
    "ltx/still-to-shot": "video/av/still-to-shot",
    "ltx/still-to-video-5s": "video/av/still-to-video-8s",
    "ltx/t2v-5s": "video/av/text-to-video-8s",
    "ltx/text-to-video-5s": "video/av/text-to-video-8s",
    "ltx/weather-broll": "video/av/weather-broll",
    "motion/av/audio-to-video-5s": "video/av/audio-to-video-8s",
    "motion/av/audio-to-video-12s": "video/av/audio-to-video-8s",
    "motion/av/dialogue-5s": "video/av/dialogue-8s",
    "motion/av/dialogue-12s": "video/av/dialogue-8s",
    "motion/av/first-last-5s": "video/av/first-last-8s",
    "motion/av/first-last-12s": "video/av/first-last-8s",
    "motion/av/multishot-5s": "video/av/multishot-8s",
    "motion/av/multishot-12s": "video/av/multishot-8s",
    "motion/av/shorts-still-5s": "video/av/shorts-still-8s",
    "motion/av/shorts-still-12s": "video/av/shorts-still-8s",
    "motion/av/still-to-video-5s": "video/av/still-to-video-8s",
    "motion/av/still-to-video-12s": "video/av/still-to-video-8s",
    "motion/av/text-to-video-5s": "video/av/text-to-video-8s",
    "motion/av/text-to-video-12s": "video/av/text-to-video-8s",
    "optional/klein/trellis2": "3d/trellis2",
    "optional/wan/i2v-a14b": "labs/opt-in/still-to-video-a14b",
    "optional/wan/still-to-video-a14b": "labs/opt-in/still-to-video-a14b",
    "shorts/breakwater/act-01": "film/breakwater/act-01",
    "shorts/breakwater/act-02": "film/breakwater/act-02",
    "shorts/breakwater/act-03": "film/breakwater/act-03",
    "shorts/breakwater/act-04": "film/breakwater/act-04",
    "shorts/breakwater/act-05": "film/breakwater/act-05",
    "shorts/glasshouse/act-01": "film/glasshouse/act-01",
    "shorts/glasshouse/act-02": "film/glasshouse/act-02",
    "shorts/glasshouse/act-03": "film/glasshouse/act-03",
    "shorts/glasshouse/act-04": "film/glasshouse/act-04",
    "shorts/glasshouse/act-05": "film/glasshouse/act-05",
    "shorts/go-see": "film/go-see",
    "shorts/last-lane/act-01": "film/last-lane/act-01",
    "shorts/last-lane/act-02": "film/last-lane/act-02",
    "shorts/last-lane/act-03": "film/last-lane/act-03",
    "shorts/last-lane/act-04": "film/last-lane/act-04",
    "shorts/last-lane/act-05": "film/last-lane/act-05",
    "shorts/night-oven/act-01": "film/night-oven/act-01",
    "shorts/night-oven/act-02": "film/night-oven/act-02",
    "shorts/night-oven/act-03": "film/night-oven/act-03",
    "shorts/night-oven/act-04": "film/night-oven/act-04",
    "shorts/night-oven/act-05": "film/night-oven/act-05",
    "shorts/still-here": "film/still-here",
    "shorts/switchyard": "film/switchyard",
    "shorts/tide-table/act-01": "film/tide-table/act-01",
    "shorts/tide-table/act-02": "film/tide-table/act-02",
    "shorts/tide-table/act-03": "film/tide-table/act-03",
    "shorts/tide-table/act-04": "film/tide-table/act-04",
    "shorts/tide-table/act-05": "film/tide-table/act-05",
    "wan/bumper-loop": "video/loops/bumper-loop",
    "wan/creator/candle-loop": "social/silent/candle-loop",
    "wan/creator/city-night": "social/silent/city-night",
    "wan/creator/confetti-loop": "social/silent/confetti-loop",
    "wan/creator/fabric-breeze": "social/silent/fabric-breeze",
    "wan/creator/handheld-vlog": "social/silent/handheld-vlog",
    "wan/creator/ig-story-loop": "social/silent/instagram-story-loop",
    "wan/creator/instagram-story-loop": "social/silent/instagram-story-loop",
    "wan/creator/ken-burns": "social/silent/ken-burns",
    "wan/creator/light-leak-loop": "social/silent/light-leak-loop",
    "wan/creator/logo-sting": "social/silent/logo-sting",
    "wan/creator/lyric-bg-loop": "social/silent/lyric-bg-loop",
    "wan/creator/macro-product": "social/silent/macro-product",
    "wan/creator/pan-left": "social/silent/pan-left",
    "wan/creator/paper-flip": "social/silent/paper-flip",
    "wan/creator/product-spin": "social/silent/product-spin",
    "wan/creator/screen-bg-loop": "social/silent/screen-bg-loop",
    "wan/creator/spotify-canvas": "social/silent/spotify-canvas",
    "wan/creator/steam-loop": "social/silent/steam-loop",
    "wan/creator/tiktok-hook": "social/silent/tiktok-hook",
    "wan/creator/tilt-reveal": "social/silent/tilt-reveal",
    "wan/creator/tt-hook": "social/silent/tiktok-hook",
    "wan/creator/twitch-brb-loop": "social/silent/twitch-brb-loop",
    "wan/creator/twitch-starting-loop": "social/silent/twitch-starting-loop",
    "wan/creator/unbox-hands": "social/silent/unbox-hands",
    "wan/creator/x-post-5s": "social/silent/x-post-5s",
    "wan/creator/youtube-subscribe-bump": "social/silent/youtube-subscribe-bump",
    "wan/creator/yt-subscribe-bump": "social/silent/youtube-subscribe-bump",
    "wan/creator/zoom-punch": "social/silent/zoom-punch",
    "wan/first-last-5s": "video/silent/first-last-5s",
    "wan/flf-5s": "video/silent/first-last-5s",
    "wan/gif-loop": "video/loops/gif-loop",
    "wan/i2v-5s": "video/silent/still-to-video-5s",
    "wan/i2v-shot": "video/silent/still-to-shot",
    "wan/orbit-i2v": "video/silent/orbit-still-5s",
    "wan/orbit-still-5s": "video/silent/orbit-still-5s",
    "wan/parallax-i2v": "video/silent/parallax-still-5s",
    "wan/parallax-still-5s": "video/silent/parallax-still-5s",
    "wan/push-in-i2v": "video/silent/push-in-still-5s",
    "wan/push-in-still-5s": "video/silent/push-in-still-5s",
    "wan/shorts-i2v": "video/silent/shorts-still-5s",
    "wan/shorts-still-5s": "video/silent/shorts-still-5s",
    "wan/sticker-loop": "video/loops/sticker-loop",
    "wan/still-to-shot": "video/silent/still-to-shot",
    "wan/still-to-video-5s": "video/silent/still-to-video-5s",
    "wan/t2v-5s": "video/silent/text-to-video-5s",
    "wan/text-to-video-5s": "video/silent/text-to-video-5s",
    "wan/vace-join": "video/silent/vace-join",
}

# Old unique stem (no .json) -> _lab-relative id (no .json).
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

# Whole-subtree lane moves, keyed by the old ``_lab``-relative prefix and
# matched longest-first. The catalog is organized by what the operator is
# making, so a lane rename is one row here and not 200 ``REL_RENAMES`` rows.
# An exact ``REL_RENAMES`` entry still wins, which is how a single graph leaves
# its old lane for a different model family's lane.
LANE_RELOCATIONS: dict[str, str] = {
    "stills": "photos",
    "motion/silent": "video/silent",
    "motion/av": "video/av",
    "motion/loops": "video/loops",
    "motion": "video",
    "creator/stills": "social/stills",
    "creator/silent": "social/silent",
    "creator/av": "social/av",
    "creator": "social",
    "services": "business",
    "films": "film",
    "editing": "film",
    "dcc": "guides",
    "optional": "labs/opt-in",
    "inspire": "labs/assist",
}


def rel_id(name: str) -> str:
    """Return the _lab-relative id for an old stem, new rel, or filename.

    An exact ``REL_RENAMES`` entry always wins, so a single graph can leave its
    lane for a different one (``stills/talking-head`` is an LTX graph and moved
    under ``video/av``). Failing that, the longest matching ``LANE_RELOCATIONS``
    prefix re-homes the whole subtree, which is how the graphs that only
    changed lanes are handled without a dictionary row each.

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
    if text in REL_RENAMES:
        text = REL_RENAMES[text]
    return _relocated(text)


def _relocated(text: str) -> str:
    """Re-home ``text`` under the lane it now belongs to.

    Arguments:
        text: ``_lab``-relative id with no ``.json``.
    Returns:
        The same id with its longest matching lane prefix swapped, unchanged
        when no relocation covers it.
    """
    parts = text.split("/")
    for depth in range(len(parts) - 1, 0, -1):
        prefix = "/".join(parts[:depth])
        target = LANE_RELOCATIONS.get(prefix)
        if target is not None:
            return "/".join([target, *parts[depth:]])
    return text


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
        Old file stem -> new file stem. Values agree when two lanes share a stem.
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
    for old, new in sorted(
        ((f"{key}/", f"{value}/") for key, value in LANE_RELOCATIONS.items()),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
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

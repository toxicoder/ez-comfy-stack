"""Canonical _lab-relative ids after dropping -lab-example and family prefixes.

Not collected by pytest (leading underscore). Builders, stamps, and the
rename pass import ``OLD_TO_REL`` / ``rel_id``.
"""

from __future__ import annotations

import re

# Cryptic lab-relative id → slightly longer descriptive id.
# Applied after OLD_TO_REL so *-lab-example stems resolve in one rel_id() call.
REL_RENAMES: dict[str, str] = {
    "wan/i2v-5s": "wan/still-to-video-5s",
    "wan/t2v-5s": "wan/text-to-video-5s",
    "wan/flf-5s": "wan/first-last-5s",
    "wan/i2v-shot": "wan/still-to-shot",
    "wan/shorts-i2v": "wan/shorts-still-5s",
    "wan/orbit-i2v": "wan/orbit-still-5s",
    "wan/parallax-i2v": "wan/parallax-still-5s",
    "wan/push-in-i2v": "wan/push-in-still-5s",
    "ltx/i2v-5s": "ltx/still-to-video-5s",
    "ltx/t2v-5s": "ltx/text-to-video-5s",
    "ltx/flf-5s": "ltx/first-last-5s",
    "ltx/a2v-5s": "ltx/audio-to-video-5s",
    "ltx/i2v-shot": "ltx/still-to-shot",
    "ltx/shorts-i2v": "ltx/shorts-still-5s",
    "optional/wan/i2v-a14b": "optional/wan/still-to-video-a14b",
    "klein/ig-square": "klein/instagram-square",
    "klein/og-blog": "klein/open-graph",
    "klein/creator/yt-channel-icon": "klein/creator/youtube-channel-icon",
    "klein/creator/yt-channel-art": "klein/creator/youtube-channel-art",
    "klein/creator/yt-shorts-thumb": "klein/creator/youtube-shorts-thumb",
    "klein/creator/yt-community": "klein/creator/youtube-community",
    "klein/creator/yt-chapter-card": "klein/creator/youtube-chapter-card",
    "klein/creator/yt-subscribe-plate": "klein/creator/youtube-subscribe-plate",
    "klein/creator/yt-end-screen": "klein/creator/youtube-end-screen",
    "klein/creator/ig-portrait": "klein/creator/instagram-portrait",
    "klein/creator/ig-landscape": "klein/creator/instagram-landscape",
    "klein/creator/ig-story": "klein/creator/instagram-story",
    "klein/creator/ig-reel-cover": "klein/creator/instagram-reel-cover",
    "klein/creator/ig-highlight": "klein/creator/instagram-highlight",
    "klein/creator/ig-profile": "klein/creator/instagram-profile",
    "klein/creator/ig-carousel-5": "klein/creator/instagram-carousel-5",
    "klein/creator/ig-grid-3up": "klein/creator/instagram-grid-3up",
    "klein/creator/tt-cover": "klein/creator/tiktok-cover",
    "klein/creator/tt-shop": "klein/creator/tiktok-shop",
    "klein/creator/li-post": "klein/creator/linkedin-post",
    "klein/creator/li-landscape": "klein/creator/linkedin-landscape",
    "klein/creator/li-banner": "klein/creator/linkedin-banner",
    "klein/creator/li-article": "klein/creator/linkedin-article",
    "klein/creator/li-carousel-5": "klein/creator/linkedin-carousel-5",
    "klein/creator/pin-standard": "klein/creator/pinterest-pin",
    "klein/creator/pin-story": "klein/creator/pinterest-story",
    "klein/creator/fb-post": "klein/creator/facebook-post",
    "wan/creator/yt-subscribe-bump": "wan/creator/youtube-subscribe-bump",
    "wan/creator/ig-story-loop": "wan/creator/instagram-story-loop",
    "wan/creator/tt-hook": "wan/creator/tiktok-hook",
    "ltx/creator/yt-outro-av": "ltx/creator/youtube-outro-av",
    "ltx/creator/ig-reel-lifestyle": "ltx/creator/instagram-reel-lifestyle",
    "ltx/creator/tt-broll": "ltx/creator/tiktok-broll",
    "dcc/klein/from-clay": "dcc/klein/clay-hero",
    "dcc/klein/from-clay-plates": "dcc/klein/clay-plates",
    "dcc/klein/from-canny": "dcc/klein/canny-hero",
    "dcc/klein/from-guide-loader": "dcc/klein/guide-still",
    "dcc/ltx/iclora-depth-5s": "dcc/ltx/depth-control-5s",
    "dcc/ltx/iclora-canny-5s": "dcc/ltx/canny-control-5s",
    "dcc/ltx/iclora-depth-shorts": "dcc/ltx/depth-control-shorts",
    "dcc/ltx/iclora-from-guide-loader": "dcc/ltx/depth-from-loader",
    "dcc/wan/flf-from-guide": "dcc/wan/first-last-from-guide",
    "dcc/trellis/from-klein-still": "dcc/trellis/still-to-mesh",
    "audio/dub/localize": "audio/dub/clone-translate",
    "audio/finish": "audio/stem-mix",
    "audio/podcast/audio-first": "audio/podcast/two-host-episode",
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
_GENERIC_STEMS = frozenset({"finish", "localize"})


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

    Full rels go first so ``wan/i2v-5s`` becomes ``wan/still-to-video-5s``.
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

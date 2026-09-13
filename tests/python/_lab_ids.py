"""Canonical _lab-relative ids after dropping -lab-example and family prefixes.

Not collected by pytest (leading underscore). Builders, stamps, and the
rename pass import ``OLD_TO_REL`` / ``rel_id``.
"""

from __future__ import annotations

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
        return OLD_TO_REL[text]
    basename = text.rsplit("/", 1)[-1]
    if basename in OLD_TO_REL:
        return OLD_TO_REL[basename]
    return text


def file_stem(rel: str) -> str:
    """Last path component of a lab-relative id."""
    return rel_id(rel).rsplit("/", 1)[-1]

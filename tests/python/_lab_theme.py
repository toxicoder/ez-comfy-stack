"""Shared canned prompts for the lab photoreal techno-wizard identity.

Internal (never CLIP, never captions): a wizard of technology who is excited
about the future, cares about people, and is focused on the good uses of the
tools in front of them. Familiar, trustworthy, hopeful. On screen they stay
epic and adventurous — parkour, music, tropical cities, remote nature, and
everything between. Do not write hope, trust, or "bright future" into prompts.

Not imported by pytest collection (leading underscore). Builders import it:

  python3 tests/python/_wire_prompt_enhance.py
  python3 tests/python/_build_app_workflows.py
  python3 tests/python/_build_creator_video_workflows.py
"""

from __future__ import annotations

STYLE_LOCK = "photoreal still"
STYLE_LOCK_VIDEO = "photoreal shot"

# Camera-free place bible for klein-dream-house and klein-style-lock.
# Shot cards own lens, time, and weather. Do not name a camera here.
# Outdoor lamps are fixtures (inventory), not a time of day.
HOUSE_IDENTITY = (
    f"A {STYLE_LOCK} of one compact warm-glass crown penthouse on a tall "
    "unmarked tropical coastal tower over a bright bay, unmarked glass towers "
    "and palms behind. One wraparound terrace sits outside a three-bay "
    "black-framed bay glass wall. Teak floors, pale stone, coral-teal edge light. "
    "Lounge at the glass with one sand linen sofa facing the bays, kitchen island "
    "behind the sofa facing the cook wall, dining beside the island, master "
    "bedroom and bath left of the living volume. Warm teak terrace lanterns "
    "and low path lights on the terrace. Palms on the terrace and a fern "
    "living wall beside the glass. "
    "Unmarked home, empty of lettering."
)
HOUSE_INVENTORY = (
    "one sand linen sofa facing the three-bay glass, pale-stone kitchen island "
    "with warm-teak cabinets, teak dining table, linen bedding at the "
    "bay-window bedroom, freestanding stone tub facing frosted glass, two "
    "teak terrace chairs, compact unmarked data-staff, warm teak terrace "
    "lanterns, low path lights"
)

ROOFTOP_INVENTORY = (
    "unmarked sun-washed teal technical running coat with faint circuit-thread seams, "
    "floating unmarked warm gold-cyan holographic glyph rings, compact unmarked data-staff, "
    "tropical rooftop terrace with palms, unmarked glass towers over a bright bay"
)

I2V_LOCK = (
    "Keep every object and surface from the start image; do not redesign."
)

KLEIN_NEG_STILL = (
    "game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, melted "
    "geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks"
)


def _klein_still(lens: str) -> str:
    return (
        f"A {STYLE_LOCK} of a tropical coastal city rooftop terrace at golden hour. "
        "An original techno wizard in an unmarked sun-washed teal technical running coat "
        "with faint circuit-thread seams stands mid-stride on the terrace, warm gold-cyan "
        "holographic glyph rings blooming from a compact unmarked data-staff as if the "
        "code were a spell. Palms and unmarked glass towers recede toward a bright bay. "
        "Shot on a "
        f"{lens} lens at eye level, framed for YouTube 16:9. Clean unmarked surfaces, "
        "empty of lettering."
    )


KLEIN_STILL = _klein_still("24mm")
KLEIN_STILL_DAILY = _klein_still("35mm")

CREATOR_IDENTITY = (
    f"A {STYLE_LOCK} of a tropical coastal city rooftop terrace at golden hour. An original "
    "techno wizard in an unmarked sun-washed teal technical running coat with faint "
    "circuit-thread seams stands mid-stride on the terrace. Warm gold-cyan holographic "
    "glyph rings bloom from a compact unmarked data-staff, empty of lettering."
)

WAN_T2V = (
    "An original techno wizard in an unmarked sun-washed teal technical running coat with "
    "faint circuit-thread seams stands mid-stride on a tropical coastal city rooftop terrace "
    "at golden hour, warm gold-cyan holographic glyph rings blooming from a compact unmarked "
    "data-staff as if the code were a spell. Coat hem and glyph motes drift in a warm bay "
    "breeze while palms and unmarked glass towers hold a bright waterfront. The camera dollies "
    "in slowly toward the wizard over five seconds. Photoreal, physically plausible light, "
    "natural materials, 24mm, YouTube 16:9."
)
WAN_I2V = (
    "Slow push-in toward the start-image subject. Gentle motion in fabric, hair, or "
    "foliage. Keep the start-image identity locked. Keep every object and surface from "
    "the start image; do not redesign. One continuous five-second take at 24 fps."
)

LTX_AUDIO_HINT = "world SFX matching the start image, no score"
LTX_T2V = (
    f"A wide {STYLE_LOCK_VIDEO} of a tropical coastal city rooftop terrace at golden hour. "
    "An original techno wizard in an unmarked sun-washed teal technical running coat with "
    "faint circuit-thread seams stands mid-stride on the terrace as warm gold-cyan holographic "
    "glyph rings bloom from a compact unmarked data-staff as if the code were a spell. Coat hem "
    "and glyph motes drift in a warm bay breeze while palms and unmarked glass towers hold a "
    "bright waterfront. The camera dollies in slowly toward the wizard. A warm terrace breeze "
    "and palm rustle sit under distant bay traffic, then a glyph chime. Clean unmarked "
    "surfaces sit empty of lettering. No music and no score."
)
LTX_I2V = (
    "The start image holds as the first frame. The camera moves slowly toward the "
    "subject while fabric or foliage drifts. Light wind and world SFX matching the "
    "start image sit under the action. Keep every object and surface from the start "
    "image; do not redesign. No music and no score."
)

GIF_MOTION = (
    "Locked camera. Gentle cyclic breeze in fabric or leaves. Lights shimmer, "
    "then settle. Keep the start-image identity locked. "
    "Keep every object and surface from the start image; do not redesign. "
    "Gentle cyclic motion for a looping GIF."
)

KLEIN_SHORTS = (
    f"A {STYLE_LOCK} vertical still for Shorts. An original "
    "techno wizard in an unmarked sun-washed teal technical running coat with faint circuit-thread seams "
    "stands mid-stride on a tropical rooftop terrace at golden hour. Warm gold-cyan holographic glyph rings "
    "bloom from a compact unmarked data-staff, empty of lettering. Shot on a 35mm lens, framed "
    "for 9:16 with headroom for captions."
)
KLEIN_THUMBNAIL = (
    "A bold YouTube thumbnail still, 16:9. An original techno wizard in an "
    "unmarked sun-washed teal technical running coat with faint circuit-thread seams fills the frame on a "
    "tropical rooftop terrace at golden hour. High contrast key light, clear subject separation, warm gold-cyan "
    "holographic glyph rings and a compact unmarked data-staff, empty of lettering. Photoreal still, "
    "eye-catching, clean of burned-in words."
)
KLEIN_HOOK = (
    f"A {STYLE_LOCK} vertical hook still for Shorts. "
    "First-frame energy: an original techno wizard fills the lower third mid-stride on a "
    "tropical rooftop terrace at golden hour. Tight 9:16, caption headroom at the top. "
    "Warm gold-cyan holographic glyph rings, empty of lettering."
)

WAN_SHORTS_I2V = (
    "Locked vertical framing for Shorts. Gentle subject motion. Camera holds, then a "
    "slow push-in. Keep the start-image identity locked. Keep every object and surface "
    "from the start image; do not redesign. One continuous ~5 s take at 24 fps. No audio."
)
WAN_ORBIT = (
    "Slow orbit around the start-image subject. Camera arcs a few degrees right while "
    "keeping the product or hero identity locked. Keep every object and surface from "
    "the start image; do not redesign. One continuous ~5 s take, no cuts."
)
WAN_VACE = (
    "Hold identity from Shot A last frame and travel toward Shot B first frame. "
    "One continuous 17-frame join at 24 fps. Keep wardrobe and set locked. Do not redesign."
)

LTX_SHORTS_AUDIO = "world SFX matching the start image, no score"
LTX_SHORTS_I2V = (
    "The start image holds as the first frame in vertical Shorts framing. World SFX "
    "matching the start image sit under a slow push-in. Keep every object and surface "
    "from the start image; do not redesign. No music and no score."
)
LTX_BROLL_AUDIO = "warm terrace breeze, palm rustle, distant bay traffic, glyph chime, no score"
LTX_BROLL = (
    f"Locked-camera ambient B-roll of a tropical coastal city rooftop terrace at golden hour. Coat hem "
    "stirs, holographic glyph motes drift, palm fronds move, distant bay traffic and a warm breeze, "
    f"a glyph chime once. {STYLE_LOCK_VIDEO}, unmarked surfaces, "
    "empty of lettering. No music and no score. Five seconds."
)
LTX_WEATHER_AUDIO = "tropical rain, thunder far off, water on glass, palm slap, no score"
LTX_WEATHER = (
    "Locked-camera weather B-roll. A tropical storm streaks across a rooftop terrace and a "
    "sun-washed teal running coat; palms thrash and rain sheets off unmarked glass. Soft wind, "
    "rain on glass, thunder far off. Unmarked surfaces. No music and no score. Five seconds."
)
LTX_HOOK_AUDIO = "world SFX matching the start image, no score"
LTX_HOOK_AV = (
    "A five-second AV cold open. Camera snaps to the start-image subject with fast "
    "present-tense energy. World SFX matching the start image. Unmarked surfaces. "
    "No music and no score."
)
LTX_TALKING_AUDIO = "room tone matching the start image, modest speech, no score"
LTX_TALKING_HEAD = (
    "The start image holds as the first frame. The subject holds still and speaks one "
    "short line. Wardrobe and set stay locked. Mouth motion is modest. Room tone sits "
    "under the voice. No music and no score."
)

STORYBOARD = (
    ("ez_board_01", "Wide establishing of this scene, 24mm."),
    ("ez_board_02", "Enter: the bible subject arriving into this scene, 35mm."),
    ("ez_board_03", "Traverse: moving through this scene, 35mm."),
    ("ez_board_04", "Insert: a material or prop detail named in the bible, 50mm."),
    ("ez_board_05", "Exit: turning toward the way out of this scene, 35mm."),
    ("ez_board_06", "Closer hook of the same scene, 24mm."),
)

GOSEE_IDENTITY = (
    f"A {STYLE_LOCK}, first-person body-cam at golden hour. Unmarked sun-washed teal "
    "running-coat sleeves with faint circuit-thread seams and matching gloves occupy the "
    "lower edges of the frame, hands pumping as warm gold-cyan holographic glyph motes bloom "
    "at the wrists. A compact unmarked data-staff is slung across the back. Tropical rooftops, "
    "palms, and unmarked glass towers fill the view toward a bright bay. Eye-level 24mm "
    "body-cam, framed for YouTube 16:9. Clean unmarked surfaces, empty of lettering."
)
GOSEE_WAN_I2V_01 = (
    "First-person body-cam high-speed parkour sprint across a sunlit tropical terrace. "
    "Sun-washed teal sleeves and gloves pump at the frame edges, glyph motes at the wrists. "
    "Leap the first rooftop gap; boots flash in the lower frame. Continuous tracking, "
    "locked identity, no cut."
)
GOSEE_LTX_I2V_01 = (
    "The start image holds as the first frame. The first-person body-cam surges into a "
    "high-speed parkour sprint across a sunlit tropical terrace, sun-washed teal sleeves and "
    "matching gloves pumping hard at the lower edges while warm gold-cyan holographic glyph "
    "motes streak from the wrists. The camera leaps a gap between unmarked rooftops; boots "
    "flash through the bottom of the frame as they land and the run never stops. Warm wind "
    "shoves the coat, each footfall ticks warm grit, and breath sits close to the lens. "
    "Continuous body-cam tracking, no cut. No music and no score."
)
LAZY_FORGE = "A techno wizard on a sunny tropical city rooftop."

CHARACTER_DRAFT = (
    f"A {STYLE_LOCK} of an original character, standing, full body with headroom, "
    "Instagram 4:5. Distinct face, wardrobe, and one signature prop. Unmarked surfaces, "
    "empty of lettering. Eye-level 35mm."
)
CHARACTER_TWEAK = (
    "Keep this character's face, wardrobe, and proportions. Change only what this prompt names."
)

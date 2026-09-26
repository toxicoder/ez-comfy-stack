"""Shared canned prompts for the lab photoreal techno-wizard identity.

Internal (never CLIP, never captions): a wizard of technology who is excited
about the future, cares about people, and is focused on the good uses of the
tools in front of them. Familiar, trustworthy, hopeful. On screen they stay
epic and adventurous - parkour, music, tropical cities, remote nature, and
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
# Shot cards own lens, camera station, and aspect. Time, weather,
# materials, and architecture live here. Do not name a camera here.
# Outdoor lamps are fixtures (inventory), not a time of day.
HOUSE_IDENTITY = (
    f"A {STYLE_LOCK} of one full-floor warm-glass crown penthouse on a very "
    "tall unmarked tropical coastal tower in a dense city of unmarked glass "
    "skyscrapers, a bright bay only as a distant slot between towers. A wide "
    "wraparound terrace sits outside a three-bay black-framed glass wall. "
    "Teak floors, pale stone, coral-teal edge light. Lounge at the glass with "
    "one sand linen sofa facing the towers. Kitchen island faces a solid teak "
    "cook wall. Dining faces an interior stone wall. Master bedroom faces the "
    "headboard wall. Bath is an interior wet room with frosted glass. Study "
    "faces a teak shelf wall. Warm teak terrace lanterns and low path lights. "
    "Palms on the terrace. Unmarked home, empty of lettering."
)
HOUSE_INVENTORY = (
    "one sand linen sofa facing the three-bay glass, pale-stone kitchen island "
    "with warm-teak cabinets, teak dining table, linen bedding at the "
    "headboard wall, freestanding stone tub facing frosted glass, teak study "
    "desk at a shelf wall, two teak terrace chairs, compact unmarked "
    "data-staff, warm teak terrace lanterns, low path lights"
)

ROOFTOP_INVENTORY = (
    "unmarked dark indigo-violet suede running coat with silk-felt nap and faint circuit-thread seams, "
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
        "An original techno wizard in an unmarked dark indigo-violet suede running coat with silk-felt nap "
        "and faint circuit-thread seams stands mid-stride on the terrace, warm gold-cyan "
        "holographic glyph rings blooming from a compact unmarked data-staff as if the "
        "code were a spell. Hold a wide environmental terrace so palms and unmarked glass "
        "towers recede toward a bright bay. Match a standing eyeline. "
        f"{lens}-equivalent wide. Rake amber sidelight along fabric and terrace grit so "
        "long shadows stripe the terrace and highlights go honey. Locked as if a crawl "
        "dolly-in frozen. Framed for YouTube 16:9. Clean unmarked surfaces, "
        "empty of lettering."
    )


KLEIN_STILL = _klein_still("24mm")
KLEIN_STILL_DAILY = _klein_still("35mm")

CREATOR_IDENTITY = (
    f"A {STYLE_LOCK} of a tropical coastal city rooftop terrace at golden hour. An original "
    "techno wizard in an unmarked dark indigo-violet suede running coat with silk-felt nap and faint "
    "circuit-thread seams stands mid-stride on the terrace. Warm gold-cyan holographic "
    "glyph rings bloom from a compact unmarked data-staff, empty of lettering."
)

WAN_T2V = (
    "An original techno wizard in an unmarked dark indigo-violet suede running coat with silk-felt nap and "
    "faint circuit-thread seams stands mid-stride on a tropical coastal city rooftop terrace "
    "at golden hour, warm gold-cyan holographic glyph rings blooming from a compact unmarked "
    "data-staff as if the code were a spell. Coat hem and glyph motes drift in a warm bay "
    "breeze while palms and unmarked glass towers hold a bright waterfront. Rake amber "
    "sidelight along fabric and terrace grit, golden-hour amber rims. 24mm-equivalent wide. "
    "The camera dollies in slowly toward the wizard over five seconds. Photoreal, "
    "YouTube 16:9. No audio."
)
WAN_I2V = (
    "Slow dolly in toward the start-image subject. Gentle motion in fabric, hair, or "
    "foliage. Keep the start-image identity locked. Keep every object and surface from "
    "the start image; do not redesign. One continuous five-second take at 24 fps. "
    "dolly in. No audio."
)

LTX_AUDIO_HINT = "world SFX matching the start image, no score"
LTX_T2V = (
    f"A wide {STYLE_LOCK_VIDEO} of a tropical coastal city rooftop terrace at golden hour. "
    "An original techno wizard in an unmarked dark indigo-violet suede running coat with silk-felt nap and "
    "faint circuit-thread seams stands mid-stride on the terrace as warm gold-cyan holographic "
    "glyph rings bloom from a compact unmarked data-staff as if the code were a spell. Coat hem "
    "and glyph motes drift in a warm bay breeze while palms and unmarked glass towers hold a "
    "bright waterfront. Match a standing eyeline. 24mm-equivalent wide. The camera dollies in "
    "on a locked wheeled support, tightening without zooming. A warm terrace breeze "
    "and palm rustle sit under distant bay traffic, then a glyph chime. Clean unmarked "
    "surfaces sit empty of lettering. No music and no score."
)
LTX_I2V = (
    "The start image holds as the first frame. The camera dollies in slowly toward the "
    "subject while fabric or foliage drifts. Light wind and world SFX matching the "
    "start image sit under the action. Keep every object and surface from the start "
    "image; do not redesign. No music and no score."
)

GIF_MOTION = (
    "Locked camera, fixed camera. Gentle cyclic breeze in fabric or leaves. Lights shimmer, "
    "then settle. Keep the start-image identity locked. "
    "Keep every object and surface from the start image; do not redesign. "
    "Gentle cyclic motion for a looping GIF."
)

KLEIN_SHORTS = (
    f"A {STYLE_LOCK} vertical still for Shorts. An original "
    "techno wizard in an unmarked dark indigo-violet suede running coat with silk-felt nap and faint circuit-thread seams "
    "stands mid-stride on a tropical rooftop terrace at golden hour. Warm gold-cyan holographic glyph rings "
    "bloom from a compact unmarked data-staff, empty of lettering. Match a standing eyeline. "
    "35mm-equivalent classic reportage view, framed "
    "for 9:16 with headroom for captions."
)
KLEIN_THUMBNAIL = (
    "A bold YouTube thumbnail still, 16:9. An original techno wizard in an "
    "unmarked dark indigo-violet suede running coat with silk-felt nap and faint circuit-thread seams fills the frame on a "
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
    "slow dolly in. Keep the start-image identity locked. Keep every object and surface "
    "from the start image; do not redesign. One continuous ~5 s take at 24 fps. "
    "dolly in. No audio."
)
WAN_ORBIT = (
    "Slow orbit around the start-image subject. Camera arcs a few degrees right while "
    "keeping the product or hero identity locked. Keep every object and surface from "
    "the start image; do not redesign. One continuous ~5 s take, no cuts. orbit."
)
WAN_VACE = (
    "Hold identity from Shot A last frame and travel toward Shot B first frame. "
    "One continuous 17-frame join at 24 fps. Keep wardrobe and set locked. Do not redesign."
)

LTX_SHORTS_AUDIO = "world SFX matching the start image, no score"
LTX_SHORTS_I2V = (
    "The start image holds as the first frame in vertical Shorts framing. World SFX "
    "matching the start image sit under a slow dolly in. Keep every object and surface "
    "from the start image; do not redesign. No music and no score."
)
LTX_BROLL_AUDIO = "warm terrace breeze, palm rustle, distant bay traffic, glyph chime, no score"
LTX_BROLL = (
    f"fixed-camera ambient B-roll of a tropical coastal city rooftop terrace at golden hour. Coat hem "
    "stirs, holographic glyph motes drift, palm fronds move, distant bay traffic and a warm breeze, "
    f"a glyph chime once. {STYLE_LOCK_VIDEO}, unmarked surfaces, "
    "empty of lettering. No music and no score. Twelve seconds."
)
LTX_WEATHER_AUDIO = "tropical rain, thunder far off, water on glass, palm slap, no score"
LTX_WEATHER = (
    "fixed-camera weather B-roll. A tropical storm streaks across a rooftop terrace and a "
    "dark indigo-violet suede running coat; palms thrash and rain sheets off unmarked glass. Soft wind, "
    "rain on glass, thunder far off. Unmarked surfaces. No music and no score. Five seconds."
)
LTX_HOOK_AUDIO = "world SFX matching the start image, no score"
LTX_HOOK_AV = (
    "A five-second AV cold open. Camera snap-zooms to the start-image subject with fast "
    "present-tense energy, then holds. World SFX matching the start image. Unmarked surfaces. "
    "No music and no score."
)
LTX_TALKING_AUDIO = "room tone matching the start image, modest speech, no score"
LTX_TALKING_HEAD = (
    "The start image holds as the first frame. The subject holds still and speaks one "
    "short line. Wardrobe and set stay locked. Mouth motion is modest. Room tone sits "
    "under the voice. No music and no score."
)
LTX_DIALOGUE_AUDIO = (
    "warm terrace breeze, palm rustle, distant bay traffic, one spoken line, glyph chime, no score"
)
LTX_DIALOGUE = (
    "A medium photoreal shot of a tropical coastal city rooftop terrace at golden hour. "
    "An original techno wizard in an unmarked dark indigo-violet suede running coat with silk-felt nap and "
    "faint circuit-thread seams stands at the glass, warm gold-cyan holographic glyph rings "
    "hovering over a compact unmarked data-staff. The camera holds a locked-off frame, then dollies in as the "
    "wizard turns toward lens, eyes bright, and says, \"The tools are already here - we "
    "just have to use them well.\" A warm terrace breeze and palm rustle sit under distant "
    "bay traffic; the voice is close and clear, then a single glyph chime. Unmarked surfaces, "
    "empty of lettering. No music and no score. Twelve seconds."
)
LTX_MULTISHOT_AUDIO = (
    "terrace breeze continues across cuts, traffic muffled on the close-up, glyph chime on the bay, no score"
)
LTX_MULTISHOT = (
    "A wide photoreal shot frames a tropical coastal city rooftop terrace at golden hour. "
    "An original techno wizard in an unmarked dark indigo-violet suede running coat with silk-felt nap and "
    "faint circuit-thread seams stands mid-stride as warm gold-cyan holographic glyph rings "
    "bloom from a compact unmarked data-staff; palms and unmarked glass towers hold a bright "
    "bay, and a warm terrace breeze sits under distant traffic. A hard cut transitions to a "
    "medium close-up of the glyph rings over the staff, motes drifting across the dark indigo-violet suede coat, "
    "the breeze continuing across the cut while traffic muffles. The wizard's mouth stays "
    "closed. A match cut connects to a low wide of the same terrace looking out at the bay, "
    "the wizard small at the glass, a single glyph chime as the wind holds. Unmarked surfaces, "
    "empty of lettering. No music and no score. Twelve seconds."
)
LTX_PRODUCT_AUDIO = "soft tabletop room tone, a glass tick, fabric hush, no score"
LTX_PRODUCT_HERO = (
    "The start image holds as the first frame. The camera orbits a few degrees right around "
    "the product on the table while keeping identity locked. Soft room tone sits under a "
    "single glass tick and a fabric hush. Keep every object and surface from the start "
    "image; do not redesign. Unmarked, empty of lettering. No music and no score. Twelve seconds."
)
LTX_FLF_AUDIO = "terrace breeze, palm rustle, distant bay traffic, glyph chime at the last frame, no score"
LTX_FLF = (
    "The first frame holds, then the wizard steps through the terrace toward the last-frame "
    "pose as glyph rings bloom and settle. Camera eases with the motion; no cut. A warm "
    "breeze and palm rustle sit under distant bay traffic, then a glyph chime as the last "
    "frame lands. Keep wardrobe and set locked to both stills. Unmarked surfaces. No music "
    "and no score. Five seconds."
)
LTX_A2V_AUDIO = "use the loaded clip; do not invent a score"
LTX_A2V = (
    "The start image holds as the first frame. The subject listens and moves with the loaded "
    "soundtrack: modest head motion, fabric hush, locked wardrobe and set. Picture follows "
    "the audio. Keep every object and surface from the start image; do not redesign. "
    "Mouths will not match. No extra music. Five seconds."
)

STORYBOARD = (
    ("ez_board_01", "Wide establishing of this scene, 24mm-equivalent wide."),
    ("ez_board_02", "Enter: the bible subject arriving into this scene, 35mm-equivalent classic."),
    ("ez_board_03", "Traverse: moving through this scene, 35mm-equivalent classic."),
    ("ez_board_04", "Insert: a material or prop detail named in the bible, 50mm-equivalent."),
    ("ez_board_05", "Exit: turning toward the way out of this scene, 35mm-equivalent classic."),
    ("ez_board_06", "Closer hook of the same scene, 24mm-equivalent wide."),
)

GOSEE_IDENTITY = (
    "A chest-mounted first-person body-cam still, eye-level, already at a dead sprint "
    "across a golden-hour tropical rooftop terrace, looking straight ahead at a wide rooftop "
    "gap that already fills the center. Only the wearer's own ink-black fitted running sleeves "
    "and blank matte-black gloves enter from the bottom edge: contralateral pump, left glove "
    "hip-to-chest, empty palms, hands free. An open short storm-cloak in matte charcoal with a "
    "warm-gold inner lining streams at the left and right frame edges. Tiny floating warm-gold "
    "rune motes hover near the wrists only. Unmarked palm trees and glass towers rush toward a "
    "bright bay beyond the gap. Late-sun rim light, fabric weave and stone grit, mild film "
    "grain. Mount at sternum height. Wide 24mm body-cam, slight barrel, a full-bleed "
    "photographic plate in YouTube 16:9 "
    "with bare frame edges and a clean unmarked lens, empty of lettering."
)
GOSEE_WAN_I2V_01 = (
    "First-person eye-level body-cam already at a dead sprint across a sunlit terrace. "
    "Contralateral arm pump along the bottom edge, blank gloves, empty palms, elbows bent, "
    "hands swinging hip to chest, horizon bobbing with each stride. Open short "
    "storm-cloak streams at the edges. The rooftop gap grows until it fills the frame. "
    "Continuous tracking, no cut, locked identity."
)
GOSEE_LTX_I2V_01 = (
    "The start image holds as the first frame. Wordless mix: silent mouth. Race-pace "
    "footfalls strike terrace stone as the dead sprint continues, warm wind and grit "
    "ticks with each stride, close-mic breath on the contralateral pump. First-person "
    "eye-level body-cam tracks forward, horizon bobbing, no cut. The wearer's own "
    "ink-black sleeves and blank matte-black gloves stay along the bottom edge, empty "
    "palms. The rooftop gap already in the start frame grows dead ahead. Last frames hold "
    "the gap in the center until it fills the frame. No speech. No music and no score."
)
LAZY_FORGE = "A techno wizard on a sunny tropical city rooftop."

CHARACTER_DRAFT = (
    f"A {STYLE_LOCK} of an original character, standing, full body with headroom, "
    "Instagram 4:5. Distinct face, wardrobe, and one signature prop. Unmarked surfaces, "
    "empty of lettering. Match a standing eyeline. 35mm-equivalent classic."
)
CHARACTER_TWEAK = (
    "Keep this character's face, wardrobe, and proportions. Change only what this prompt names."
)
TEXT_SWAP = "HELLO"
TEXT_SWAP_LOCK = (
    "Keep the same typeface, weight, color, size, tracking, perspective, material, "
    "lighting, and every other pixel of the image. Spell the new lettering exactly."
)

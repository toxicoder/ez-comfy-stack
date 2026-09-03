"""Shared canned prompts for the lab cyberpunk tech-wizard cutscene identity.

Not imported by pytest collection (leading underscore). Builders import it:

  python3 tests/python/_wire_prompt_enhance.py
  python3 tests/python/_build_app_workflows.py
  python3 tests/python/_build_creator_video_workflows.py
"""

from __future__ import annotations

STYLE_LOCK = "HD 3D game-engine pre-rendered cutscene still"

ROOFTOP_INVENTORY = (
    "unmarked electric-cyan tech-mage coat with circuit-thread seams, "
    "floating unmarked holographic glyph rings, compact unmarked data-staff, "
    "neon-wet megacity rooftop terrace, unmarked spires in volumetric haze"
)

I2V_LOCK = (
    "Keep every object and surface from the start image; do not redesign."
)

KLEIN_NEG_STILL = (
    "live-action photoreal, Pixar rounded cartoon, muddy textures, melted geometry, "
    "duplicate limbs, watermarks, oversharpen halos, muddy blacks"
)


def _klein_still(lens: str) -> str:
    return (
        f"A {STYLE_LOCK} of a neon-wet dusk megacity rooftop. An original cyberpunk "
        "tech wizard in an unmarked electric-cyan coat with circuit-thread seams stands "
        "on a terrace, holographic glyph rings blooming from a compact unmarked "
        "data-staff as if the code were a spell. Unmarked spires recede into volumetric "
        "haze. Shot on a "
        f"{lens} lens at eye level, framed for YouTube 16:9. Clean unmarked surfaces, "
        "empty of lettering."
    )


KLEIN_STILL = _klein_still("24mm")
KLEIN_STILL_DAILY = _klein_still("35mm")

CREATOR_IDENTITY = (
    f"A {STYLE_LOCK} of a neon-wet dusk megacity rooftop. An original cyberpunk "
    "tech wizard in an unmarked electric-cyan coat with circuit-thread seams stands "
    "on a terrace. Holographic glyph rings bloom from a compact unmarked data-staff, "
    "empty of lettering."
)

WAN_T2V = (
    "An original cyberpunk tech wizard in an unmarked electric-cyan coat with "
    "circuit-thread seams stands on a neon-wet dusk megacity rooftop terrace, "
    "holographic glyph rings blooming from a compact unmarked data-staff as if the "
    "code were a spell. Coat hem and glyph motes drift in a high-altitude breeze "
    "while distant maglev glides between unmarked spires. The camera dollies in "
    "slowly toward the wizard over five seconds. HD 3D game-engine pre-rendered "
    "cutscene, physically based materials, cinematic three-point light, volumetric "
    "neon haze, 24mm, YouTube 16:9."
)
WAN_I2V = (
    "Slow cinematic dolly-in toward the tech wizard. Coat hem and holographic glyph "
    "motes drift in a high-altitude breeze. Distant maglev glides between unmarked "
    "spires. Keep the start-image identity locked. Keep every object and surface "
    "from the start image; do not redesign. One continuous five-second take "
    "at 24 fps."
)

LTX_AUDIO_HINT = "rooftop wind, electrical hum, distant maglev, glyph chime, no score"
LTX_T2V = (
    "A wide HD 3D game-engine pre-rendered cutscene shot of a neon-wet dusk megacity "
    "rooftop. An original cyberpunk tech wizard in an unmarked electric-cyan coat with "
    "circuit-thread seams stands on a terrace as holographic glyph rings bloom from a "
    "compact unmarked data-staff as if the code were a spell. Coat hem and glyph motes "
    "drift in a high-altitude breeze while distant maglev glides between unmarked "
    "spires. The camera dollies in slowly toward the wizard. Rooftop wind and an "
    "electrical hum sit under a distant maglev, then a glyph chime. Clean unmarked "
    "surfaces sit empty of lettering. No music and no score."
)
LTX_I2V = (
    "The start image holds as the first frame. The camera dollies in slowly toward "
    "the tech wizard while coat hem and holographic glyph motes drift in a high-altitude "
    "breeze and distant maglev glides between unmarked spires. Rooftop wind and an "
    "electrical hum sit under a distant maglev, then a glyph chime. The rooftop "
    "and wizard identity stay locked. Keep every object and surface from the start "
    "image; do not redesign. No music and no score."
)

GIF_MOTION = (
    "Locked camera. A high-altitude breeze cycles the coat hem and holographic glyph "
    "motes. Neon city lights shimmer, then settle. Keep the start-image identity locked. "
    "Keep every object and surface from the start image; do not redesign. "
    "Gentle cyclic motion for a looping GIF."
)

KLEIN_SHORTS = (
    "A HD 3D game-engine pre-rendered cutscene vertical still for Shorts. An original "
    "cyberpunk tech wizard in an unmarked electric-cyan coat with circuit-thread seams "
    "stands on a neon-wet dusk rooftop terrace. Holographic glyph rings bloom from a "
    "compact unmarked data-staff, empty of lettering. Shot on a 35mm lens, framed "
    "for 9:16 with headroom for captions."
)
KLEIN_THUMBNAIL = (
    "A bold YouTube thumbnail still, 16:9. An original cyberpunk tech wizard in an "
    "unmarked electric-cyan coat with circuit-thread seams fills the frame on a neon-wet "
    "dusk rooftop terrace. High contrast key light, clear subject separation, holographic "
    "glyph rings and a compact unmarked data-staff, empty of lettering. HD 3D game-engine "
    "pre-rendered cutscene, eye-catching, clean of burned-in words."
)
KLEIN_HOOK = (
    "A HD 3D game-engine pre-rendered cutscene vertical hook still for Shorts. "
    "First-frame energy: an original cyberpunk tech wizard fills the lower third on a "
    "neon-wet dusk rooftop terrace. Tight 9:16, caption headroom at the top. "
    "Holographic glyph rings, empty of lettering."
)

WAN_SHORTS_I2V = (
    "Locked vertical framing for Shorts. Coat hem and holographic glyph motes drift. "
    "Neon city lights hold. Camera holds, then a slow push-in. Keep the start-image "
    "identity locked. Keep every object and surface from the start image; do not redesign. "
    "One continuous ~5 s take at 24 fps. No audio."
)
WAN_ORBIT = (
    "Slow orbit around the start-image subject. Camera arcs a few degrees right while "
    "keeping the product or hero identity locked. Keep every object and surface from "
    "the start image; do not redesign. One continuous ~5 s take, no cuts."
)

LTX_SHORTS_AUDIO = "rooftop wind, electrical hum, distant maglev, glyph chime, no score"
LTX_SHORTS_I2V = (
    "The start image holds as the first frame in vertical Shorts framing. Rooftop "
    "wind and an electrical hum sit under a distant maglev, then a glyph chime. Slow "
    "push-in. Keep every object and surface from the start image; do not redesign. "
    "No music and no score."
)
LTX_BROLL_AUDIO = "rooftop wind, electrical hum, distant maglev, glyph chime, no score"
LTX_BROLL = (
    "Locked-camera ambient B-roll of a neon-wet dusk megacity rooftop terrace. Coat hem "
    "stirs, holographic glyph motes drift, neon lights shimmer, distant maglev and rooftop "
    "wind, a glyph chime once. HD 3D game-engine pre-rendered cutscene, unmarked surfaces, "
    "empty of lettering. No music and no score. Five seconds."
)
LTX_WEATHER_AUDIO = "rain, wind, drip, no score"
LTX_WEATHER = (
    "Locked-camera weather B-roll. Rain streaks across a neon-wet rooftop terrace and an "
    "electric-cyan tech-mage coat at dusk leftovers. Soft wind, rain on metal, distant "
    "drip. Unmarked surfaces. No music and no score. Five seconds."
)
LTX_HOOK_AUDIO = "rooftop wind, electrical hum, distant maglev, glyph chime, no score"
LTX_HOOK_AV = (
    "A five-second AV cold open. Camera snaps to an original cyberpunk tech wizard "
    "on a neon-wet dusk rooftop terrace as holographic glyph rings bloom and distant "
    "maglev hums. Fast present-tense energy, unmarked surfaces. No music and no score."
)

STORYBOARD = (
    ("ez_board_01", "Wide establishing shot of a neon-wet dusk megacity of unmarked spires from a rooftop, 24mm."),
    ("ez_board_02", "Medium shot of an original cyberpunk tech wizard on a rooftop terrace, 35mm."),
    ("ez_board_03", "Detail of the compact unmarked data-staff and holographic glyph rings, 50mm."),
    ("ez_board_04", "Rooftop tracking angle as distant maglev glides between spires, 35mm."),
    ("ez_board_05", "Over-the-shoulder toward the unmarked city skyline, neon dusk haze."),
    ("ez_board_06", "Closing wide as neon city lights warm in the spires, quiet terrace, 24mm."),
)

"""Shared canned prompts for the lab superhero 3D-animation identity.

Not imported by pytest collection (leading underscore). Builders import it:

  python3 tests/python/_wire_prompt_enhance.py
  python3 tests/python/_build_app_workflows.py
  python3 tests/python/_build_creator_video_workflows.py
"""

from __future__ import annotations

STYLE_LOCK = "3D feature-animation still"

KLEIN_NEG_STILL = (
    "live-action photoreal, muddy textures, melted geometry, duplicate limbs, "
    "watermarks, oversharpen halos, muddy blacks"
)


def _klein_still(lens: str) -> str:
    return (
        f"A {STYLE_LOCK} of a dusk city rooftop. An original superhero in a "
        "teal-and-copper flight suit stands on a helipad, unmarked circular "
        "starburst chest plate catching a warm key, a short unmarked capelet at rest. "
        "Rounded towers recede into volumetric haze. Shot on a "
        f"{lens} lens at eye level, framed for YouTube 16:9. Clean unmarked surfaces, "
        "empty of lettering."
    )


KLEIN_STILL = _klein_still("24mm")
KLEIN_STILL_DAILY = _klein_still("35mm")

CREATOR_IDENTITY = (
    f"A {STYLE_LOCK} of a dusk city rooftop. An original superhero in a "
    "teal-and-copper flight suit stands on a helipad. Unmarked circular "
    "starburst chest plate, empty of lettering."
)

WAN_T2V = (
    "An original superhero in a teal-and-copper flight suit stands on a rooftop "
    "helipad above a stylized dusk city of rounded towers, unmarked circular "
    "starburst chest plate catching a warm key. Suit fabric and a short capelet "
    "stir in a high-altitude breeze while distant air traffic glides between the "
    "towers. The camera dollies in slowly toward the hero over five seconds. "
    "Feature-film 3D animation, rounded forms, physically based materials, "
    "cinematic three-point light, volumetric dusk haze, 24mm, YouTube 16:9."
)
WAN_I2V = (
    "Slow cinematic dolly-in toward the superhero. Suit fabric and a short capelet "
    "stir in a high-altitude breeze. Distant air traffic glides between rounded "
    "towers. Keep the start-image identity locked. One continuous five-second take "
    "at 24 fps."
)

LTX_AUDIO_HINT = "rooftop wind, fabric snap, distant traffic hum, no score"
LTX_T2V = (
    "A wide 3D feature-animation shot of a dusk city rooftop. An original superhero "
    "in a teal-and-copper flight suit stands on a helipad as a warm key rakes the "
    "unmarked circular starburst chest plate. Suit fabric and a short capelet stir "
    "in a high-altitude breeze while distant air traffic glides between rounded "
    "towers. The camera dollies in slowly toward the hero. Rooftop wind snaps the "
    "fabric as a distant traffic hum rolls between the towers. Clean unmarked "
    "surfaces sit empty of lettering. No music and no score."
)
LTX_I2V = (
    "The start image holds as the first frame. The camera dollies in slowly toward "
    "the superhero while suit fabric and a short capelet stir in a high-altitude "
    "breeze and distant air traffic glides between rounded towers. Rooftop wind "
    "snaps the fabric as a distant traffic hum rolls between the towers. The rooftop "
    "and hero identity stay locked. No music and no score."
)

GIF_MOTION = (
    "Locked camera. A high-altitude breeze cycles the capelet and suit fabric. "
    "City lights shimmer, then settle. Keep the start-image identity locked. "
    "Gentle cyclic motion for a looping GIF."
)

KLEIN_SHORTS = (
    "A 3D feature-animation vertical still for Shorts. An original superhero in a "
    "teal-and-copper flight suit stands on a dusk rooftop helipad. Warm key, unmarked "
    "circular starburst chest plate, empty of lettering. Shot on a 35mm lens, framed "
    "for 9:16 with headroom for captions."
)
KLEIN_THUMBNAIL = (
    "A bold YouTube thumbnail still, 16:9. An original superhero in a teal-and-copper "
    "flight suit fills the frame on a dusk rooftop helipad. High contrast key light, "
    "clear subject separation, unmarked circular starburst chest plate, empty of "
    "lettering. Feature-film 3D animation, eye-catching, clean of burned-in words."
)
KLEIN_HOOK = (
    "A 3D feature-animation vertical hook still for Shorts. First-frame energy: an "
    "original teal-and-copper superhero fills the lower third on a dusk rooftop "
    "helipad. Tight 9:16, caption headroom at the top. Unmarked chest plate, empty "
    "of lettering."
)

WAN_SHORTS_I2V = (
    "Locked vertical framing for Shorts. Capelet and suit fabric flutter. City lights "
    "hold. Camera holds, then a slow push-in. Keep the start-image identity locked. "
    "One continuous ~5 s take at 24 fps. No audio."
)
WAN_ORBIT = (
    "Slow orbit around the start-image subject. Camera arcs a few degrees right while "
    "keeping the product or hero identity locked. One continuous ~5 s take, no cuts."
)

LTX_SHORTS_AUDIO = "rooftop wind, fabric snap, distant traffic hum, no score"
LTX_SHORTS_I2V = (
    "The start image holds as the first frame in vertical Shorts framing. Rooftop "
    "wind snaps a capelet as a distant traffic hum rolls between towers. Slow "
    "push-in. No music and no score."
)
LTX_BROLL_AUDIO = "rooftop wind, fabric snap, distant traffic hum, no score"
LTX_BROLL = (
    "Locked-camera ambient B-roll of a dusk city rooftop helipad. Capelet fabric "
    "stirs, city lights shimmer, distant traffic hum and rooftop wind, a fabric snap "
    "once. Feature-film 3D animation, unmarked surfaces, empty of lettering. No music "
    "and no score. Five seconds."
)
LTX_WEATHER_AUDIO = "rain, wind, drip, no score"
LTX_WEATHER = (
    "Locked-camera weather B-roll. Rain streaks across a rooftop helipad and a "
    "teal-and-copper flight suit at dusk leftovers. Soft wind, rain on metal, distant "
    "drip. Unmarked surfaces. No music and no score. Five seconds."
)
LTX_HOOK_AUDIO = "rooftop wind, fabric snap, distant traffic hum, no score"
LTX_HOOK_AV = (
    "A five-second AV cold open. Camera snaps to an original teal-and-copper "
    "superhero on a dusk rooftop helipad as wind hits a capelet and distant traffic "
    "hums. Fast present-tense energy, unmarked surfaces. No music and no score."
)

STORYBOARD = (
    ("ez_board_01", "Wide establishing shot of a stylized dusk city of rounded towers from a rooftop, 24mm."),
    ("ez_board_02", "Medium shot of an original teal-and-copper superhero on a helipad, 35mm."),
    ("ez_board_03", "Detail of the unmarked circular copper starburst chest plate, 50mm."),
    ("ez_board_04", "Rooftop tracking angle as distant air traffic glides between towers, 35mm."),
    ("ez_board_05", "Over-the-shoulder toward the unmarked city skyline, dusk haze."),
    ("ez_board_06", "Closing wide as city lights warm in the towers, quiet helipad, 24mm."),
)

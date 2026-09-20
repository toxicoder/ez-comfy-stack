#!/usr/bin/env python3
"""Write ez_prompt_enhance sample catalogs (20 recipes + index).

Not imported by pytest collection. Run from repo root:

  python3 tests/python/_build_sample_catalogs.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from _lab_theme import (
    CHARACTER_DRAFT,
    CHARACTER_TWEAK,
    TEXT_SWAP,
    TEXT_SWAP_LOCK,
    CREATOR_IDENTITY,
    GIF_MOTION,
    GOSEE_IDENTITY,
    HOUSE_IDENTITY,
    KLEIN_STILL,
    LAZY_FORGE,
    LTX_A2V,
    LTX_BROLL,
    LTX_DIALOGUE,
    LTX_FLF,
    LTX_HOOK_AV,
    LTX_I2V,
    LTX_MULTISHOT,
    LTX_PRODUCT_HERO,
    LTX_T2V,
    LTX_TALKING_HEAD,
    LTX_WEATHER,
    WAN_I2V,
    WAN_ORBIT,
    WAN_T2V,
    WAN_VACE,
)

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_music.nodes import DRAFT_LYRICS, FULL_LYRICS  # noqa: E402
from ez_podcast.nodes import RADIO_SEED_SCRIPT, SEED_SCRIPT  # noqa: E402
from ez_research.nodes import _DEFAULT_MESSAGE  # noqa: E402

DEST = CUSTOM / "ez_prompt_enhance" / "js" / "samples"

I2V_LOCK = (
    "Keep the start-image identity locked. Keep every object and surface from "
    "the start image; do not redesign."
)
NO_SCORE = "No music and no score."
UNMARKED = "Unmarked surfaces, empty of lettering."

RAP_TAGS = (
    "boom bap, hip-hop, dusty drums, vinyl crackle, dry snare, sampled piano "
    "stab, upright bass, male rap vocals, dry booth, no autotune, 88 bpm"
)
RAP_FULL_TAGS = (
    "boom bap, hip-hop, dusty drums, vinyl crackle, dry snare, sampled piano "
    "stab, upright bass, male rap vocals, dry booth, no autotune, 92 bpm"
)

CLAY_FINISH = (
    "Keep the clay blocking, camera, and silhouette from the start image. "
    "Finish as a photoreal still: physically plausible light, natural materials, "
    "unmarked surfaces empty of lettering. "
    "Do not redesign layout."
)

WAN_PUSH = (
    "Slow dolly in toward the start-image subject. Gentle motion in fabric, hair, or "
    f"foliage. {I2V_LOCK} One continuous five-second take at 24 fps. dolly in. No audio."
)
WAN_PARALLAX = (
    "Locked camera, fixed camera with a slight lateral slide so near objects drift against the "
    f"far plane. Gentle breeze in fabric or leaves. {I2V_LOCK} One continuous "
    "five-second take at 24 fps. No audio."
)

STILL_HERE_IDENTITY = (
    "A photoreal third-person household morning still. One cream ceramic mug with a "
    "hairline chip on the rim sits on a honey-oak table in first light. White subway "
    "tile backsplash, one linen curtain at a single window. Unmarked kitchen, empty of "
    "lettering. The mug is sharp in the foreground. Match a standing eyeline. "
    "35mm-equivalent classic reportage view, framed for YouTube 16:9."
)
SWITCHYARD_IDENTITY = (
    "A photoreal night freight-yard still in rain. Three generic unmarked boxcars sit "
    "on wet ballast under one yard lamp. Rain streaks in the lamp glow, gravel shining, "
    "empty of railroad company marks. Match a standing eyeline. 24mm-equivalent wide, "
    "framed for YouTube 16:9. Clean unmarked steel, empty of lettering."
)

RESEARCH_DEFAULT = _DEFAULT_MESSAGE


def _row(
    sid: str,
    label: str,
    prompt: str,
    *,
    tags: str = "",
    lyrics: str = "",
) -> dict[str, str]:
    row = {"id": sid, "label": label, "prompt": prompt}
    if tags:
        row["tags"] = tags
    if lyrics:
        row["lyrics"] = lyrics
    return row


def _klein(subject: str, place: str, light: str, camera: str) -> str:
    return (
        f"A photoreal still of {subject} {place}. {light} "
        f"{camera} {UNMARKED}"
    )


def _wan_t2v(entity: str, scene: str, motion: str, camera: str) -> str:
    return (
        f"{entity} {scene} {motion} The camera {camera} over five seconds. "
        "Photoreal, 24mm-equivalent wide, physically plausible light. YouTube 16:9. "
        "No audio."
    )


def _wan_i2v(motion: str, camera: str) -> str:
    return (
        f"{motion} The camera {camera}. {I2V_LOCK} One continuous five-second "
        "take at 24 fps. No audio."
    )


def _loop(motion: str) -> str:
    return (
        f"Locked camera. {motion} {I2V_LOCK} Gentle cyclic motion for a looping GIF."
    )


def _ltx_t2v(action: str, audio: str, camera: str) -> str:
    return (
        f"{action} {camera} {audio} {UNMARKED} {NO_SCORE} Twelve seconds."
    )


def _ltx_i2v(motion: str, audio: str, camera: str) -> str:
    return (
        f"The start image holds as the first frame. {motion} {camera} {audio} "
        f"{I2V_LOCK} {NO_SCORE}"
    )


def klein_image_studio() -> list[dict[str, str]]:
    """Twenty recipes for stills/image-studio covering generate, edit, and text."""
    return [
        _row(
            "photoreal-terrace",
            "Photoreal terrace",
            "A photoreal still of an original techno wizard in an unmarked dark indigo-violet suede running coat on a tropical rooftop terrace at golden hour. Warm sidelight, palms, unmarked glass towers, empty of lettering.",
        ),
        _row(
            "background-swap",
            "Background swap",
            "Keep the subject from the reference. Replace the background with a fog harbor pier at blue hour. Match ground contact and wrap light. Original character only.",
        ),
        _row(
            "change-text",
            "Change text",
            "Keep typeface, weight, tracking, and perspective. Replace the lettering with the original word HELLO. Lock glyph geometry.",
        ),
        _row(
            "change-ratio",
            "Change ratio",
            "Keep the subject. Reframe onto the Format canvas. Outpaint edges with matching scene. Empty of new lettering.",
        ),
        _row(
            "face-lock",
            "Face lock",
            "Lock the reference face. Same identity, wardrobe, and eyeline. Change only what the prompt names. Original character only.",
        ),
        _row(
            "outfit-change",
            "Outfit change",
            "Keep face and body from the reference. Change clothing to an unmarked charcoal technical coat. Original character only.",
        ),
        _row(
            "relight-night",
            "Relight night",
            "Keep the reference inventory. Relight as practical-lamp night interior. Warm pools, cool window rim.",
        ),
        _row(
            "product-packshot",
            "Product packshot",
            "Clean packshot of an unmarked ceramic mug on a sweep. Soft wrap light, sharp unmarked surfaces, empty of type.",
        ),
        _row(
            "youtube-thumb",
            "YouTube thumbnail",
            "YouTube thumbnail still. Large original character, one short original word, 16:9, high contrast, empty of real brands.",
        ),
        _row(
            "quote-card",
            "Quote card",
            "Quote card still. Original line on a clean field. Strong type, empty background.",
        ),
        _row(
            "sky-replace",
            "Sky replace",
            "Keep the scene from the reference. Replace only the sky with a storm front and the light it casts.",
        ),
        _row(
            "add-object",
            "Add object",
            "Keep the reference scene. Add one unmarked brass lamp on the table with matching light and contact shadow.",
        ),
        _row(
            "outpaint-wide",
            "Outpaint wide",
            "Keep the reference center. Extend the canvas to Format size with matching architecture left and right.",
        ),
        _row(
            "fix-hands",
            "Fix hands",
            "Keep the reference. Correct extra fingers and melted hands only. Original character only.",
        ),
        _row(
            "interior-room",
            "Interior room",
            "Architectural interior of a writing room. Window light, teak desk, unmarked shelves. Empty of signage.",
        ),
        _row(
            "golden-hour-look",
            "Golden hour look",
            "Golden-hour sidelight, long shadows, warm rim. Photoreal still of the prompted place. Empty of lettering.",
        ),
        _row(
            "instagram-post",
            "Instagram post",
            "Instagram 4:5 still. One original subject, clean background, empty of platform chrome and tiny type.",
        ),
        _row(
            "relabel-sign",
            "Relabel sign",
            "Keep the sign object. Swap the written words to OPEN. Lock glyph geometry and perspective.",
        ),
        _row(
            "wardrobe-transfer",
            "Wardrobe transfer",
            "Keep the person in the first reference. Transfer wardrobe look from a second still if present, else an unmarked dark indigo-violet suede coat. Original characters only.",
        ),
        _row(
            "empty-lettering",
            "Empty of lettering",
            "Keep the reference. Remove all lettering and reconstruct surfaces. Empty of marks.",
        ),
    ]


def klein_t2i() -> list[dict[str, str]]:
    return [
        _row("rooftop-golden-hour", "Rooftop golden hour", KLEIN_STILL),
        _row(
            "night-bay-overlook",
            "Night bay overlook",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede running coat with silk-felt nap and faint circuit-thread seams",
                "stands at a tropical rooftop rail above a dense unmarked city and a dark bay",
                "Practical terrace lanterns and distant tower lights; cool rim from the bay, warm coat lining.",
                "Match a standing eyeline. 35mm-equivalent classic reportage view. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "rain-terrace",
            "Rain on the terrace",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede running coat with silk-felt nap",
                "pauses under a terrace overhang while tropical rain sheets off unmarked glass",
                "Overcast daylight, wet stone grit, rain beads on fabric weave.",
                "Match a standing eyeline. 24mm-equivalent wide. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "dawn-switchback",
            "Dawn mountain road",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede running coat with a compact unmarked data-staff",
                "walks a high unmarked switchback above a tropical valley of palms",
                "First light rakes the ridge; long cool shadows, clear air.",
                "Slightly below eyeline. 35mm-equivalent classic reportage view. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "workshop-bench",
            "Workshop bench",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede coat",
                "leans over a teak workbench with warm-gold holographic glyph rings blooming from a compact unmarked data-staff",
                "A single practical lamp, tight falloff, metal filings and wood grain.",
                "Chest-cam height. 50mm-equivalent. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "fog-harbor",
            "Fog harbor",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede running coat",
                "stands on an unmarked concrete pier as fog holds a quiet tropical harbor",
                "Soft overcast, low contrast, wet concrete and rope texture.",
                "Match a standing eyeline. 35mm-equivalent classic reportage view. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "greenhouse-aisle",
            "Greenhouse aisle",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede coat",
                "walks a long unmarked greenhouse aisle of palms and broad leaves",
                "Dappled glass light, humid air, leaf sheen and condensation.",
                "Match a standing eyeline. 35mm-equivalent classic reportage view. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "desert-mesa",
            "Desert mesa dusk",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede running coat",
                "stands on a high unmarked mesa as the last sun hits red stone",
                "Hard warm sidelight, long shadows, grit in the air.",
                "Match a standing eyeline. 24mm-equivalent wide. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "library-stacks",
            "Library stacks",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede coat",
                "pauses between tall unmarked wood stacks in a quiet reading hall",
                "Warm practicals, dust in a window shaft, paper and wood texture.",
                "Match a standing eyeline. 50mm-equivalent. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "train-platform",
            "Night platform",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede running coat",
                "waits on an unmarked underground platform as a train smear passes",
                "Cool overhead fluorescents, warm coat lining, tiled grit.",
                "Match a standing eyeline. 35mm-equivalent classic reportage view. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "coastal-cliff",
            "Coastal cliff",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede coat with glyph rings at the staff",
                "stands on an unmarked cliff path above bright surf",
                "Hard noon sun, salt haze, fabric snap in wind.",
                "Match a standing eyeline. 24mm-equivalent wide. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "snow-ridge",
            "Snow pine ridge",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede running coat",
                "crosses a high unmarked ridge among snow-loaded pines",
                "Thin winter sun, blue shadow, breath in cold air.",
                "Match a standing eyeline. 35mm-equivalent classic reportage view. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "market-alley",
            "Covered alley",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede coat",
                "walks a narrow unmarked covered alley of stone and hanging cloth",
                "Dappled bounce light, warm cloth, cool stone.",
                "Match a standing eyeline. 35mm-equivalent classic reportage view. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "observatory",
            "Observatory dome",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede coat",
                "stands inside an unmarked dome with a slit of night sky",
                "Cool moonlight mix with a warm floor practical, metal and stone.",
                "Match a standing eyeline. 24mm-equivalent wide. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "river-ferry",
            "River ferry",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede running coat",
                "stands at the rail of a small unmarked ferry on a wide river at dusk",
                "Warm low sun, water glitter, paint and rust texture.",
                "Match a standing eyeline. 35mm-equivalent classic reportage view. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "arcade-neon",
            "Unmarked arcade",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede coat",
                "walks an unmarked indoor arcade of colored practicals and empty cabinets",
                "Mixed neon bounce, no readable cabinet art, floor shine.",
                "Match a standing eyeline. 24mm-equivalent wide. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "courtyard-fountain",
            "Stone courtyard",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede coat",
                "sits at an unmarked stone fountain in a quiet courtyard of palms",
                "Open shade, specular water, warm stone.",
                "Match a standing eyeline. 35mm-equivalent classic reportage view. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "subway-concourse",
            "Concourse rush",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede running coat mid-stride",
                "crosses a vast unmarked concourse of concrete and glass",
                "Cool overhead banks, motion blur in the far crowd only, coat sharp.",
                "Hip height. 24mm-equivalent wide. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "rooftop-night-storm",
            "Storm rooftop",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede coat with a short storm-cloak",
                "braces on a tropical rooftop as wind pulls the cloak",
                "Lightning far off, wet stone, warm lining flash.",
                "Match a standing eyeline. 24mm-equivalent wide. Framed for YouTube 16:9.",
            ),
        ),
        _row(
            "quiet-studio",
            "Quiet studio",
            _klein(
                "an original techno wizard in an unmarked dark indigo-violet suede coat",
                "sits at an unmarked teak desk with a compact data-staff resting beside a blank notebook",
                "Soft north window, paper tooth, wood grain.",
                "Match a standing eyeline. 50mm-equivalent. Framed for YouTube 16:9.",
            ),
        ),
    ]


def klein_identity() -> list[dict[str, str]]:
    return [
        _row("rooftop-wizard", "Rooftop wizard bible", CREATOR_IDENTITY),
        _row(
            "runner-cloak",
            "Sprint cloak bible",
            "A photoreal still of an original techno wizard in an unmarked charcoal storm-cloak with warm-gold lining over an ink-black fitted running layer, blank matte-black gloves, empty palms. Compact unmarked data-staff. No camera, no lens, no place named beyond a tropical rooftop terrace and unmarked glass towers.",
        ),
        _row(
            "workshop-maker",
            "Workshop maker bible",
            "A photoreal still of an original techno wizard in an unmarked worn dark indigo-violet felt shop coat, brass-thread seams, leather apron, compact unmarked data-staff on a teak bench. Warm practicals, wood and metal. No camera. Unmarked workshop, empty of lettering.",
        ),
        _row(
            "night-operator",
            "Night operator bible",
            "A photoreal still of an original techno wizard in an unmarked matte-black technical coat with faint circuit-thread seams, compact unmarked data-staff, warm-gold glyph rings. Night terrace lanterns. No camera. Unmarked home, empty of lettering.",
        ),
        _row(
            "field-botanist",
            "Field botanist bible",
            "A photoreal still of an original techno wizard in an unmarked sun-faded olive field coat, rolled sleeves, compact unmarked data-staff, a cloth roll of unmarked tools. Palms and wet stone. No camera. Empty of lettering.",
        ),
        _row(
            "ferry-coat",
            "Ferry coat bible",
            "A photoreal still of an original techno wizard in an unmarked waxed dark indigo-violet suede coat, salt-dull hardware, compact unmarked data-staff, warm-gold lining. River light. No camera. Unmarked ferry, empty of lettering.",
        ),
        _row(
            "winter-ridge",
            "Winter ridge bible",
            "A photoreal still of an original techno wizard in an unmarked heavy dark indigo-violet felt parka with circuit-thread seams, blank gloves, compact unmarked data-staff. Snow and pine. No camera. Empty of lettering.",
        ),
        _row(
            "desert-dust",
            "Desert dust bible",
            "A photoreal still of an original techno wizard in an unmarked sun-washed dark indigo-violet suede coat, dust on seams, compact unmarked data-staff, glyph motes. Mesa stone. No camera. Empty of lettering.",
        ),
        _row(
            "library-reader",
            "Library reader bible",
            "A photoreal still of an original techno wizard in an unmarked dark indigo-violet wool-felt coat, compact unmarked data-staff used as a quiet pointer, warm-gold rings dim. Wood stacks. No camera. Empty of lettering.",
        ),
        _row(
            "greenhouse-keeper",
            "Greenhouse keeper bible",
            "A photoreal still of an original techno wizard in an unmarked dark indigo-violet silk-linen coat, damp hems, compact unmarked data-staff, leaf-shadow on fabric. Glass house. No camera. Empty of lettering.",
        ),
        _row(
            "platform-commuter",
            "Platform commuter bible",
            "A photoreal still of an original techno wizard in an unmarked dark indigo-violet suede running coat, compact unmarked data-staff tucked, blank gloves. Tile and cool light. No camera. Empty of lettering.",
        ),
        _row(
            "cliff-wind",
            "Cliff wind bible",
            "A photoreal still of an original techno wizard in an unmarked dark indigo-violet suede coat snapping in salt wind, compact unmarked data-staff, glyph rings pulled thin. Surf below unnamed. No camera. Empty of lettering.",
        ),
        _row(
            "arcade-night",
            "Arcade night bible",
            "A photoreal still of an original techno wizard in an unmarked dark indigo-violet suede coat under mixed practical color, compact unmarked data-staff, glyph rings matching the bounce. Indoor arcade, cabinets blank. No camera. Empty of lettering.",
        ),
        _row(
            "courtyard-rest",
            "Courtyard rest bible",
            "A photoreal still of an original techno wizard in an unmarked dark indigo-violet suede coat seated, compact unmarked data-staff across the knees, glyph rings idle. Stone and palms. No camera. Empty of lettering.",
        ),
        _row(
            "studio-quiet",
            "Studio quiet bible",
            "A photoreal still of an original techno wizard in an unmarked dark indigo-violet suede coat at a teak desk, compact unmarked data-staff beside a blank notebook, no screens. North light. No camera. Empty of lettering.",
        ),
        _row(
            "storm-cloak",
            "Storm cloak bible",
            "A photoreal still of an original techno wizard in an unmarked charcoal storm-cloak, warm-gold lining, ink-black running layer, blank gloves, compact unmarked data-staff. Wet tropical stone. No camera. Empty of lettering.",
        ),
        _row(
            "harbor-fog",
            "Harbor fog bible",
            "A photoreal still of an original techno wizard in an unmarked dark indigo-violet suede coat beaded with fog, compact unmarked data-staff dim, glyph rings faint. Concrete pier. No camera. Empty of lettering.",
        ),
        _row(
            "ridge-dawn",
            "Ridge dawn bible",
            "A photoreal still of an original techno wizard in an unmarked dark indigo-violet suede running coat, compact unmarked data-staff, first-light rim. High unmarked switchback. No camera. Empty of lettering.",
        ),
        _row(
            "concourse-stride",
            "Concourse stride bible",
            "A photoreal still of an original techno wizard in an unmarked dark indigo-violet suede running coat mid-stride, compact unmarked data-staff, blank gloves. Vast unmarked concourse. No camera. Empty of lettering.",
        ),
        _row(
            "mesa-staff",
            "Mesa staff bible",
            "A photoreal still of an original techno wizard in an unmarked sun-washed dark indigo-violet suede coat, compact unmarked data-staff raised with warm-gold glyph rings. Red stone, clear air. No camera. Empty of lettering.",
        ),
    ]


def klein_place() -> list[dict[str, str]]:
    places = [
        ("lab-penthouse", "Lab penthouse", HOUSE_IDENTITY),
        (
            "cliff-villa",
            "Cliff villa",
            "A photoreal still of one full-floor warm-stone cliff villa on a high unmarked coastal bluff, bright sea only as a distant slot. A wide terrace sits outside a three-bay dark-framed glass wall. Pale limestone floors, teak, coral-teal edge light. Lounge at the glass with one sand linen sofa facing the water slot. Kitchen island faces a solid stone cook wall. Dining faces an interior plaster wall. Master bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a teak shelf wall. Warm terrace lanterns and low path lights. Palms in stone planters. Unmarked home, empty of lettering.",
        ),
        (
            "forest-cabin",
            "Forest cabin",
            "A photoreal still of one full-floor warm timber cabin in a dense unmarked pine forest, a bright creek only as a distant slot between trunks. A wide deck sits outside a three-bay black-framed glass wall. Wide-plank floors, wool, amber edge light. Lounge at the glass with one rust linen sofa facing the trees. Kitchen island faces a solid timber cook wall. Dining faces an interior stone chimney wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm deck lanterns and low path lights. Unmarked home, empty of lettering.",
        ),
        (
            "desert-courtyard",
            "Desert courtyard house",
            "A photoreal still of one full-floor rammed-earth courtyard house on an unmarked mesa, a bright wash only as a distant slot. A wide inner court sits outside a three-bay wood-framed glass wall. Packed-earth floors, linen, ochre edge light. Lounge at the glass with one sand sofa facing the court. Kitchen island faces a solid adobe cook wall. Dining faces an interior plaster wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm court lanterns and low path lights. Unmarked home, empty of lettering.",
        ),
        (
            "harbor-loft",
            "Harbor loft",
            "A photoreal still of one full-floor brick loft over an unmarked working harbor, water only as a distant slot between warehouses. A wide terrace sits outside a three-bay factory-sash wall. Sealed brick floors, steel, cool-teal edge light. Lounge at the glass with one charcoal sofa facing the slot. Kitchen island faces a solid brick cook wall. Dining faces an interior plaster wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm terrace lanterns. Unmarked home, empty of lettering.",
        ),
        (
            "rice-terrace",
            "Rice-terrace house",
            "A photoreal still of one full-floor timber house on an unmarked highland terrace, paddies only as a distant stepped slot. A wide veranda sits outside a three-bay wood-framed glass wall. Tatami-adjacent mats, pale wood, moss-green edge light. Lounge at the glass with one low linen sofa facing the slot. Kitchen island faces a solid wood cook wall. Dining faces an interior plaster wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm veranda lanterns. Unmarked home, empty of lettering.",
        ),
        (
            "snow-chalet",
            "Snow chalet",
            "A photoreal still of one full-floor timber chalet on an unmarked high ridge, snowfields only as a distant slot. A wide deck sits outside a three-bay black-framed glass wall. Wide boards, wool, pine-amber edge light. Lounge at the glass with one rust sofa facing the slot. Kitchen island faces a solid timber cook wall. Dining faces an interior stone wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm deck lanterns. Unmarked home, empty of lettering.",
        ),
        (
            "canyon-house",
            "Canyon house",
            "A photoreal still of one full-floor stone house cantilevered on an unmarked canyon rim, the drop only as a distant slot. A wide terrace sits outside a three-bay steel-framed glass wall. Flagstone floors, leather, rust-teal edge light. Lounge at the glass with one sand sofa facing the slot. Kitchen island faces a solid stone cook wall. Dining faces an interior plaster wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm terrace lanterns. Unmarked home, empty of lettering.",
        ),
        (
            "garden-courtyard",
            "Garden courtyard",
            "A photoreal still of one full-floor plaster townhouse around an unmarked inner garden, street only as a distant slot through a gate. A wide loggia sits outside a three-bay wood-framed glass wall. Terra-cotta floors, linen, leaf-green edge light. Lounge at the glass with one cream sofa facing the garden. Kitchen island faces a solid tile cook wall. Dining faces an interior plaster wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm loggia lanterns. Unmarked home, empty of lettering.",
        ),
        (
            "lake-pavilion",
            "Lake pavilion",
            "A photoreal still of one full-floor glass pavilion on an unmarked still lake, forest only as a distant slot. A wide deck sits outside a three-bay black-framed glass wall. Pale boards, linen, silver-teal edge light. Lounge at the glass with one sand sofa facing the water. Kitchen island faces a solid wood cook wall. Dining faces an interior plaster wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm deck lanterns. Unmarked home, empty of lettering.",
        ),
        (
            "dune-house",
            "Dune house",
            "A photoreal still of one full-floor limewashed house in unmarked dunes, sea only as a distant slot. A wide terrace sits outside a three-bay wood-framed glass wall. Pale plaster floors, linen, sand-gold edge light. Lounge at the glass with one white sofa facing the slot. Kitchen island faces a solid plaster cook wall. Dining faces an interior wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm terrace lanterns. Unmarked home, empty of lettering.",
        ),
        (
            "bamboo-court",
            "Bamboo court",
            "A photoreal still of one full-floor dark-wood house around an unmarked bamboo court, city only as a distant slot. A wide engawa sits outside a three-bay wood-framed glass wall. Dark boards, paper screens, moss edge light. Lounge at the glass with one low charcoal sofa facing the court. Kitchen island faces a solid wood cook wall. Dining faces an interior plaster wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm lanterns. Unmarked home, empty of lettering.",
        ),
        (
            "warehouse-loft",
            "Warehouse loft",
            "A photoreal still of one full-floor unmarked warehouse loft, street only as a distant slot through high sash. A wide loading terrace sits outside a three-bay industrial glass wall. Polished concrete, steel, cool-teal edge light. Lounge at the glass with one charcoal sofa facing the slot. Kitchen island faces a solid brick cook wall. Dining faces an interior plaster wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm terrace lanterns. Unmarked home, empty of lettering.",
        ),
        (
            "hill-farmhouse",
            "Hill farmhouse",
            "A photoreal still of one full-floor stone farmhouse on an unmarked green hill, valley only as a distant slot. A wide porch sits outside a three-bay wood-framed glass wall. Wide boards, linen, grass-gold edge light. Lounge at the glass with one sand sofa facing the slot. Kitchen island faces a solid stone cook wall. Dining faces an interior plaster wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm porch lanterns. Unmarked home, empty of lettering.",
        ),
        (
            "rain-tower",
            "Rain tower flat",
            "A photoreal still of one full-floor warm-glass flat on a tall unmarked tower in rain, city only as a distant slot between towers. A wide terrace sits outside a three-bay black-framed glass wall. Teak floors, pale stone, coral-teal edge light. Lounge at the glass with one sand linen sofa facing the towers. Kitchen island faces a solid teak cook wall. Dining faces an interior stone wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a teak shelf wall. Warm terrace lanterns. Palms. Unmarked home, empty of lettering.",
        ),
        (
            "canyon-camp",
            "Canyon camp",
            "A photoreal still of one full-floor canvas-and-timber camp on an unmarked canyon shelf, the drop only as a distant slot. A wide deck sits outside a three-bay wood-framed glass wall. Boards, wool, rust edge light. Lounge at the glass with one sand sofa facing the slot. Kitchen island faces a solid timber cook wall. Dining faces an interior canvas wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm deck lanterns. Unmarked home, empty of lettering.",
        ),
        (
            "orchard-house",
            "Orchard house",
            "A photoreal still of one full-floor plaster house in an unmarked orchard, trees only as a distant slot. A wide terrace sits outside a three-bay wood-framed glass wall. Terra-cotta, linen, leaf-gold edge light. Lounge at the glass with one cream sofa facing the slot. Kitchen island faces a solid plaster cook wall. Dining faces an interior wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm terrace lanterns. Unmarked home, empty of lettering.",
        ),
        (
            "fjord-cabin",
            "Fjord cabin",
            "A photoreal still of one full-floor dark-timber cabin on an unmarked fjord shelf, water only as a distant slot. A wide deck sits outside a three-bay black-framed glass wall. Wide boards, wool, cool-teal edge light. Lounge at the glass with one charcoal sofa facing the slot. Kitchen island faces a solid timber cook wall. Dining faces an interior plaster wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm deck lanterns. Unmarked home, empty of lettering.",
        ),
        (
            "mesa-night",
            "Mesa night house",
            "A photoreal still of one full-floor rammed-earth house on an unmarked mesa at night, stars only as a distant slot. A wide terrace sits outside a three-bay wood-framed glass wall. Packed earth, linen, ochre lantern light. Lounge at the glass with one sand sofa facing the dark wash. Kitchen island faces a solid adobe cook wall. Dining faces an interior plaster wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a shelf wall. Warm terrace lanterns. Unmarked home, empty of lettering.",
        ),
        (
            "city-atrium",
            "City atrium house",
            "A photoreal still of one full-floor atrium house on a tall unmarked tower, a bright bay only as a distant slot. A wide inner court sits outside a three-bay black-framed glass wall. Teak floors, pale stone, coral-teal edge light. Lounge at the glass with one sand linen sofa facing the court. Kitchen island faces a solid teak cook wall. Dining faces an interior stone wall. Bedroom faces the headboard wall. Bath is an interior wet room with frosted glass. Study faces a teak shelf wall. Warm court lanterns. Palms. Unmarked home, empty of lettering.",
        ),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in places]


def klein_character() -> list[dict[str, str]]:
    drafts = [
        ("lab-original", "Lab original", CHARACTER_DRAFT),
        (
            "teal-runner",
            "Indigo runner",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked dark indigo-violet suede running coat with silk-felt nap and faint circuit-thread seams, blank gloves, compact unmarked data-staff as the signature prop. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "storm-cloak",
            "Storm cloak",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked charcoal storm-cloak with warm-gold lining, ink-black running layer, blank matte gloves. Signature prop: compact unmarked data-staff. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "workshop-maker",
            "Workshop maker",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked worn dark indigo-violet felt shop coat, leather apron, rolled sleeves. Signature prop: compact unmarked data-staff. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "field-botanist",
            "Field botanist",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked sun-faded olive field coat, cloth roll of unmarked tools. Signature prop: compact unmarked data-staff. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "night-operator",
            "Night operator",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked matte-black technical coat, faint circuit-thread seams. Signature prop: compact unmarked data-staff with dim gold rings. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "ferry-hand",
            "Ferry hand",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked waxed dark indigo-violet suede coat, salt-dull hardware. Signature prop: compact unmarked data-staff. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "winter-ridge",
            "Winter ridge",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked heavy dark indigo-violet felt parka, blank gloves. Signature prop: compact unmarked data-staff. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "desert-guide",
            "Desert guide",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked sun-washed dark indigo-violet suede coat, dust on seams. Signature prop: compact unmarked data-staff. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "library-reader",
            "Library reader",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked dark indigo-violet wool-felt coat. Signature prop: compact unmarked data-staff used as a quiet pointer. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "greenhouse-keeper",
            "Greenhouse keeper",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked dark indigo-violet silk-linen coat, damp hems. Signature prop: compact unmarked data-staff. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "platform-commuter",
            "Platform commuter",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked dark indigo-violet suede running coat, blank gloves. Signature prop: compact unmarked data-staff tucked at the hip. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "cliff-walker",
            "Cliff walker",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked dark indigo-violet suede coat snapping in wind. Signature prop: compact unmarked data-staff. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "arcade-night",
            "Arcade night",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked dark indigo-violet suede coat under mixed practical color. Signature prop: compact unmarked data-staff. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "courtyard-rest",
            "Courtyard rest",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked dark indigo-violet suede coat, seated then standing pose, staff across the body. Signature prop: compact unmarked data-staff. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "studio-quiet",
            "Studio quiet",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked dark indigo-violet suede coat, calm hands. Signature prop: compact unmarked data-staff beside a blank notebook. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "rain-sprint",
            "Rain sprint",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked dark indigo-violet suede running coat beaded with rain, mid-stride. Signature prop: compact unmarked data-staff. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "harbor-fog",
            "Harbor fog",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked dark indigo-violet suede coat beaded with fog. Signature prop: compact unmarked data-staff dim. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "ridge-dawn",
            "Ridge dawn",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked dark indigo-violet suede running coat, first-light rim. Signature prop: compact unmarked data-staff. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
        (
            "mesa-staff",
            "Mesa staff",
            "A photoreal still of an original character, standing, full body with headroom, Instagram 4:5. Distinct face, unmarked sun-washed dark indigo-violet suede coat, staff raised with warm-gold glyph rings. Signature prop: compact unmarked data-staff. Unmarked surfaces, empty of lettering. Eye-level 35mm.",
        ),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in drafts]


def klein_character_edit() -> list[dict[str, str]]:
    edits = [
        ("keep-change-named", "Change only what is named", CHARACTER_TWEAK),
        (
            "turn-three-quarter",
            "Turn three-quarter",
            "Keep this character's face, wardrobe, and proportions. Turn the body to a three-quarter view. Change only the turn.",
        ),
        (
            "swap-cloak",
            "Add storm cloak",
            "Keep this character's face, wardrobe, and proportions. Add an unmarked charcoal storm-cloak with warm-gold lining over the existing coat. Change only the cloak.",
        ),
        (
            "rain-beads",
            "Rain on fabric",
            "Keep this character's face, wardrobe, and proportions. Add rain beads on the coat and wet stone underfoot. Change only weather.",
        ),
        (
            "night-practicals",
            "Night practicals",
            "Keep this character's face, wardrobe, and proportions. Shift to night with warm terrace lanterns. Change only the light.",
        ),
        (
            "sit-on-rail",
            "Sit on the rail",
            "Keep this character's face, wardrobe, and proportions. Seat them on an unmarked terrace rail, same clothes. Change only the pose.",
        ),
        (
            "raise-staff",
            "Raise the staff",
            "Keep this character's face, wardrobe, and proportions. Raise the compact unmarked data-staff so glyph rings bloom. Change only the gesture.",
        ),
        (
            "look-to-lens",
            "Look to lens",
            "Keep this character's face, wardrobe, and proportions. Turn the head to look into lens, eyes bright. Change only the gaze.",
        ),
        (
            "dawn-rim",
            "Dawn rim",
            "Keep this character's face, wardrobe, and proportions. Relight with first-light rim from camera left. Change only the light.",
        ),
        (
            "snow-dust",
            "Snow on shoulders",
            "Keep this character's face, wardrobe, and proportions. Add light snow on shoulders and breath in cold air. Change only weather.",
        ),
        (
            "workshop-apron",
            "Add apron",
            "Keep this character's face, wardrobe, and proportions. Add an unmarked leather apron over the coat. Change only the apron.",
        ),
        (
            "blank-gloves-off",
            "Bare hands",
            "Keep this character's face, wardrobe, and proportions. Remove the gloves; empty palms, same pose. Change only the hands.",
        ),
        (
            "wind-snap",
            "Wind snap",
            "Keep this character's face, wardrobe, and proportions. Pull the coat hem and hair in a hard side wind. Change only motion of cloth.",
        ),
        (
            "softer-grade",
            "Softer grade",
            "Keep this character's face, wardrobe, and proportions. Soften contrast and warm the midtones. Change only the grade.",
        ),
        (
            "closer-crop",
            "Closer crop",
            "Keep this character's face, wardrobe, and proportions. Crop to a medium close-up, same lens height. Change only framing.",
        ),
        (
            "profile-turn",
            "True profile",
            "Keep this character's face, wardrobe, and proportions. Turn to a true profile. Change only the turn.",
        ),
        (
            "glyph-idle",
            "Idle glyph rings",
            "Keep this character's face, wardrobe, and proportions. Dim the glyph rings to a faint idle. Change only the rings.",
        ),
        (
            "indoor-study",
            "Move indoors",
            "Keep this character's face, wardrobe, and proportions. Place them in an unmarked teak study, same clothes. Change only the place.",
        ),
        (
            "sprint-mid",
            "Mid-stride",
            "Keep this character's face, wardrobe, and proportions. Shift to a mid-stride running pose, empty palms. Change only the pose.",
        ),
        (
            "wet-cloak-open",
            "Open wet cloak",
            "Keep this character's face, wardrobe, and proportions. Open the storm-cloak so the lining shows, fabric wet. Change only the cloak.",
        ),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in edits]


def klein_product() -> list[dict[str, str]]:
    products = [
        (
            "cobalt-mug",
            "Cobalt mug",
            "A photoreal still of one cobalt ceramic mug with a hairline chip on the rim, three-quarter packshot on a pale stone tabletop. Soft studio key, honest contact shadow, unmarked surfaces, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "teak-staff",
            "Teak data-staff",
            "A photoreal still of one compact unmarked data-staff in warm teak and matte metal on pale stone. Soft key, faint glyph motes idle, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "blank-glove",
            "Blank glove pair",
            "A photoreal still of one pair of blank matte-black running gloves on pale stone, palms empty, no lettering. Soft key, fabric weave. Eye-level 50mm, 1:1.",
        ),
        (
            "linen-notebook",
            "Linen notebook",
            "A photoreal still of one unmarked linen-bound notebook and a plain pencil on teak. Soft north light, paper tooth, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "stone-bowl",
            "Stone bowl",
            "A photoreal still of one pale-stone bowl with clear water on a dark teak square. Soft key, specular rim, unmarked. Eye-level 50mm, 1:1.",
        ),
        (
            "glass-carafe",
            "Glass carafe",
            "A photoreal still of one unmarked clear glass carafe half-full on pale stone. Soft key, caustics, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "wool-cap",
            "Wool cap",
            "A photoreal still of one unmarked charcoal wool cap on pale stone. Soft key, knit texture, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "brass-lantern",
            "Brass lantern",
            "A photoreal still of one unmarked warm brass lantern, unlit, on dark teak. Soft key, metal patina, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "ceramic-vase",
            "Ceramic vase",
            "A photoreal still of one unmarked sand ceramic vase, matte glaze, on pale stone. Soft key, honest shadow. Eye-level 50mm, 1:1.",
        ),
        (
            "running-bottle",
            "Running bottle",
            "A photoreal still of one unmarked matte-teal running bottle on pale stone. Soft key, no logos, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "teak-cup",
            "Teak cup",
            "A photoreal still of one turned teak cup on pale stone. Soft key, end-grain, unmarked. Eye-level 50mm, 1:1.",
        ),
        (
            "linen-tote",
            "Linen tote",
            "A photoreal still of one unmarked sand linen tote standing on pale stone. Soft key, cloth weave, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "steel-flask",
            "Steel flask",
            "A photoreal still of one unmarked brushed-steel flask on dark teak. Soft key, metal grain, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "clay-planter",
            "Clay planter",
            "A photoreal still of one unmarked terracotta planter with a single palm pup on pale stone. Soft key, soil grit. Eye-level 50mm, 1:1.",
        ),
        (
            "wax-coat-hook",
            "Waxed coat",
            "A photoreal still of one unmarked waxed dark indigo-violet suede coat hung on a plain wood peg, packshot crop. Soft key, fabric sheen, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "glyph-ring",
            "Idle glyph ring",
            "A photoreal still of one compact unmarked data-staff lying on pale stone with a single idle warm-gold glyph ring. Soft key, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "stone-mug-pair",
            "Stone mug pair",
            "A photoreal still of two unmarked pale-stone mugs, one slightly forward, on teak. Soft key, honest shadows, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "glass-lens-cap",
            "Clear lens cap",
            "A photoreal still of one unmarked clear glass disc on pale stone, not a branded optic, no lettering. Soft key, edge specular. Eye-level 50mm, 1:1.",
        ),
        (
            "rope-coil",
            "Rope coil",
            "A photoreal still of one coil of unmarked natural rope on pale stone. Soft key, fiber texture. Eye-level 50mm, 1:1.",
        ),
        (
            "ink-pot",
            "Ink pot",
            "A photoreal still of one unmarked matte-black ink pot and a plain dip pen on teak. Soft key, empty of lettering. Eye-level 50mm, 1:1.",
        ),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in products]


def klein_food() -> list[dict[str, str]]:
    plates = [
        (
            "citrus-bowl",
            "Citrus bowl",
            "A photoreal tabletop still of unmarked citrus in a pale-stone bowl on teak, first light. Soft key, rind texture, juice sheen, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "morning-mug",
            "Morning mug",
            "A photoreal tabletop still of a cream ceramic mug with a hairline chip, steam lifting, on a honey-oak table. Soft window key, unmarked kitchen, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "tomato-board",
            "Tomato board",
            "A photoreal tabletop still of sliced unmarked tomatoes on a dark teak board, olive oil beads, coarse salt. Soft key, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "noodle-bowl",
            "Noodle bowl",
            "A photoreal tabletop still of a stoneware bowl of unmarked broth and noodles, steam, chopsticks at rest. Soft key, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "bread-loaf",
            "Bread loaf",
            "A photoreal tabletop still of one unmarked crusty loaf on linen, crumbs, a plain knife. Soft north light, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "berry-plate",
            "Berry plate",
            "A photoreal tabletop still of unmarked berries on a small pale plate, condensation, teak. Soft key, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "grill-fish",
            "Grill fish",
            "A photoreal tabletop still of an unmarked whole grilled fish on a stone platter, lemon, herb. Warm practical, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "rice-bowl",
            "Rice bowl",
            "A photoreal tabletop still of a small unmarked rice bowl and a plain spoon on dark wood. Soft key, steam, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "pastry-morning",
            "Morning pastry",
            "A photoreal tabletop still of one unmarked flaky pastry on linen, crumbs, a cream mug nearby. Soft window, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "olive-oil",
            "Oil and bread",
            "A photoreal tabletop still of unmarked bread torn beside a shallow dish of olive oil on teak. Soft key, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "citrus-press",
            "Citrus press",
            "A photoreal tabletop still of a halved unmarked citrus on a board, juice on stone, a plain reamer. Soft key, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "soup-steam",
            "Soup steam",
            "A photoreal tabletop still of a dark bowl of unmarked soup, steam, a linen napkin. Soft key, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "egg-skillet",
            "Egg skillet",
            "A photoreal tabletop still of an unmarked small skillet with eggs, first light, honey-oak. Soft key, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "herb-bundle",
            "Herb bundle",
            "A photoreal tabletop still of unmarked tied herbs on pale stone, water beads. Soft key, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "chocolate-shard",
            "Chocolate shard",
            "A photoreal tabletop still of unmarked dark chocolate shards on slate, a pinch of salt. Soft key, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "tea-pot",
            "Tea pot",
            "A photoreal tabletop still of an unmarked clay teapot and two small cups on teak, steam. Soft key, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "peach-cut",
            "Cut peach",
            "A photoreal tabletop still of an unmarked peach cut on a board, juice, summer window. Soft key, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "noodle-lift",
            "Noodle lift",
            "A photoreal tabletop still of chopsticks lifting unmarked noodles from a stone bowl, steam. Soft key, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "yogurt-honey",
            "Yogurt honey",
            "A photoreal tabletop still of an unmarked ceramic bowl of yogurt and honey on linen. Soft key, empty of lettering. Eye-level 50mm, 1:1.",
        ),
        (
            "grill-veg",
            "Grill vegetables",
            "A photoreal tabletop still of unmarked grilled vegetables on a stone platter, char, oil. Warm practical, empty of lettering. Eye-level 50mm, 1:1.",
        ),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in plates]


def klein_text_swap() -> list[dict[str, str]]:
    lock = TEXT_SWAP_LOCK
    swaps = [
        ("hello-lock", "Replace with HELLO", TEXT_SWAP),
        (
            "neon-closed",
            "Neon CLOSED",
            f"Replace the visible lettering with: CLOSED. {lock}",
        ),
        (
            "mug-good-morning",
            "Mug GOOD MORNING",
            f"Replace the mug lettering with: GOOD MORNING. {lock}",
        ),
        (
            "poster-headline",
            "Poster OPEN TONIGHT",
            f"Replace the poster headline with: OPEN TONIGHT. {lock}",
        ),
        (
            "book-spine",
            "Book spine FIELD NOTES",
            f"Replace the book-spine lettering with: FIELD NOTES. {lock}",
        ),
        (
            "awning-open",
            "Awning OPEN",
            f"Replace the awning lettering with: OPEN. {lock}",
        ),
        (
            "tee-print",
            "Tee KEEP GOING",
            f"Replace the shirt print with: KEEP GOING. {lock}",
        ),
        (
            "thumb-title",
            "Thumb NEW EPISODE",
            f"Replace the thumbnail title with: NEW EPISODE. {lock}",
        ),
        (
            "street-sign",
            "Street sign HARBOR WAY",
            f"Replace the street-sign lettering with: HARBOR WAY. {lock}",
        ),
        (
            "bakery-hours",
            "Hours 7AM-2PM",
            f"Replace the hours lettering with: 7AM-2PM. {lock}",
        ),
        (
            "sale-to-open",
            "SALE to OPEN",
            f"Replace SALE with OPEN. {lock}",
        ),
        (
            "chapter-card",
            "Chapter ONE",
            f"Replace the chapter-card lettering with: ONE. {lock}",
        ),
        (
            "enamel-pin",
            "Pin HELLO",
            f"Replace the pin lettering with: HELLO. {lock}",
        ),
        (
            "vinyl-sticker",
            "Sticker WAVE",
            f"Replace the sticker lettering with: WAVE. {lock}",
        ),
        (
            "cafe-chalkboard",
            "Board TODAY'S SOUP",
            f"Replace the chalkboard lettering with: TODAY'S SOUP. {lock}",
        ),
        (
            "shipping-crate",
            "Crate FRAGILE",
            f"Replace the crate stencil with: FRAGILE. {lock}",
        ),
        (
            "stadium-banner",
            "Banner GO HOME",
            f"Replace the banner lettering with: GO HOME. {lock}",
        ),
        (
            "arcade-marquee",
            "Marquee INSERT COIN",
            f"Replace the marquee lettering with: INSERT COIN. {lock}",
        ),
        (
            "luggage-tag",
            "Tag GATE B",
            f"Replace the luggage-tag lettering with: GATE B. {lock}",
        ),
        (
            "window-vinyl",
            "Window YES WE'RE OPEN",
            f"Replace the window vinyl with: YES WE'RE OPEN. {lock}",
        ),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in swaps]


def klein_clay_edit() -> list[dict[str, str]]:
    looks = [
        ("photoreal-finish", "Photoreal stem-mix", CLAY_FINISH),
        (
            "golden-hour-restyle",
            "Golden-hour restyle",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as a photoreal still at golden hour: warm sidelight, natural materials, unmarked surfaces empty of lettering. Do not redesign layout.",
        ),
        (
            "night-practicals",
            "Night practicals",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as a photoreal night interior with warm practicals and cool windows. Unmarked surfaces. Do not redesign layout.",
        ),
        (
            "overcast-rain",
            "Overcast rain",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as a photoreal overcast still with wet stone and rain on glass. Unmarked surfaces. Do not redesign layout.",
        ),
        (
            "dawn-cool",
            "Dawn cool",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as a photoreal still in first light, cool air, long shadows. Unmarked surfaces. Do not redesign layout.",
        ),
        (
            "teak-and-linen",
            "Teak and linen",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish materials as teak, pale stone, and sand linen. Photoreal, unmarked. Do not redesign layout.",
        ),
        (
            "rammed-earth",
            "Rammed earth",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as rammed earth, limewash, and linen. Photoreal, unmarked. Do not redesign layout.",
        ),
        (
            "brick-loft",
            "Brick loft",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as sealed brick, steel sash, and charcoal linen. Photoreal, unmarked. Do not redesign layout.",
        ),
        (
            "snow-window",
            "Snow at the glass",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as a photoreal winter interior, snow at the glass, wool and timber. Unmarked. Do not redesign layout.",
        ),
        (
            "harbor-haze",
            "Harbor haze",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as a photoreal still with harbor haze beyond the glass, cool-teal edge light. Unmarked. Do not redesign layout.",
        ),
        (
            "cinematic-contrast",
            "Cinematic contrast",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as a photoreal cinematic still, motivated practicals, rich shadows. Unmarked. Do not redesign layout.",
        ),
        (
            "soft-north",
            "Soft north light",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as a photoreal still in soft north window light, paper and wood. Unmarked. Do not redesign layout.",
        ),
        (
            "tropical-noon",
            "Tropical noon",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as a photoreal still in hard tropical noon, palm shadow, stone grit. Unmarked. Do not redesign layout.",
        ),
        (
            "fog-morning",
            "Fog morning",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as a photoreal still in morning fog, low contrast, wet decks. Unmarked. Do not redesign layout.",
        ),
        (
            "warm-tungsten",
            "Warm tungsten",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as a photoreal still under warm tungsten practicals, no daylight. Unmarked. Do not redesign layout.",
        ),
        (
            "limewash-coast",
            "Limewash coast",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as limewash, pale plaster, and linen with a coastal grade. Photoreal, unmarked. Do not redesign layout.",
        ),
        (
            "dark-timber",
            "Dark timber",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as dark timber, wool, and cool glass. Photoreal, unmarked. Do not redesign layout.",
        ),
        (
            "canny-inside",
            "Inside the edges",
            "Keep the line-art silhouette, camera, and layout from the start image. Finish as a photoreal still inside those edges. Unmarked surfaces. Do not invent new geometry.",
        ),
        (
            "dusk-coral",
            "Dusk coral-teal",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as a photoreal dusk still with coral-teal edge light and teak. Unmarked. Do not redesign layout.",
        ),
        (
            "museum-day",
            "Museum daylight",
            "Keep the clay blocking, camera, and silhouette from the start image. Finish as a photoreal still in even museum daylight, honest materials, no drama grade. Unmarked. Do not redesign layout.",
        ),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in looks]


def _write(name: str, rows: list[dict[str, str]]) -> None:
    if len(rows) != 20:
        raise SystemExit(f"{name} has {len(rows)} rows, need 20")
    labels = [row["label"] for row in rows]
    if len(set(labels)) != 20:
        raise SystemExit(f"{name} duplicate labels")
    ids = [row["id"] for row in rows]
    if len(set(ids)) != 20:
        raise SystemExit(f"{name} duplicate ids")
    dest = DEST / f"{name}.json"
    dest.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {dest.relative_to(ROOT)}")


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    catalogs = {
        "klein_t2i": klein_t2i(),
        "klein_image_studio": klein_image_studio(),
        "klein_identity": klein_identity(),
        "klein_place": klein_place(),
        "klein_character": klein_character(),
        "klein_character_edit": klein_character_edit(),
        "klein_product": klein_product(),
        "klein_food": klein_food(),
        "klein_clay_edit": klein_clay_edit(),
        "klein_text_swap": klein_text_swap(),
    }
    # Remaining catalogs are filled by the rest of this module via import-time
    # helpers defined below main in the second half — keep a single dump loop.
    from _sample_catalog_rest import rest_catalogs  # noqa: E402

    catalogs.update(rest_catalogs())
    index = {
        "stills/still-draft": "klein_t2i",
        "stills/still-daily": "klein_t2i",
        "stills/still-studio": "klein_t2i",
        "stills/image-studio": "klein_image_studio",
        "stills/still-hero": "klein_t2i",
        "stills/thumbnail": "klein_t2i",
        "stills/instagram-square": "klein_t2i",
        "stills/open-graph": "klein_t2i",
        "stills/banner-wide": "klein_t2i",
        "stills/shorts-still": "klein_t2i",
        "stills/hook-still": "klein_t2i",
        "stills/endcard-cta": "klein_t2i",
        "stills/quote-bg": "klein_t2i",
        "stills/lower-third-bg": "klein_t2i",
        "stills/podcast-cover": "klein_t2i",
        "stills/storyboard-6up": "klein_t2i",
        "stills/camera-angles": "klein_t2i",
        "stills/lighting-trio": "klein_t2i",
        "stills/color-moods": "klein_t2i",
        "stills/time-of-day": "klein_t2i",
        "stills/style-lock": "klein_t2i",
        "stills/before-after": "klein_t2i",
        "stills/platform-pack": "klein_t2i",
        "stills/identity-sheet": "klein_identity",
        "stills/dream-house": "klein_place",
        "stills/dream-house-clay": "klein_place",
        "stills/character-draft": "klein_character",
        "stills/character-tweak": "klein_character_edit",
        "stills/text-swap": "klein_text_swap",
        "stills/product-packshot": "klein_product",
        "stills/food-tabletop": "klein_food",
        "stills/talking-head": "ltx_talking",
        "dcc/clay-hero": "klein_clay_edit",
        "dcc/clay-plates": "klein_clay_edit",
        "dcc/canny-hero": "klein_clay_edit",
        "dcc/guide-still": "klein_clay_edit",
        "motion/silent/text-to-video-5s": "wan_t2v",
        "motion/silent/still-to-video-5s": "wan_i2v",
        "motion/silent/still-to-shot": "wan_i2v",
        "motion/silent/shorts-still-5s": "wan_i2v",
        "optional/still-to-video-a14b": "wan_i2v",
        "motion/loops/gif-loop": "wan_loop",
        "motion/loops/bumper-loop": "wan_loop",
        "motion/loops/sticker-loop": "wan_loop",
        "motion/silent/first-last-5s": "wan_flf",
        "dcc/first-last-from-guide": "wan_flf",
        "motion/silent/vace-join": "wan_vace",
        "motion/silent/orbit-still-5s": "wan_orbit",
        "motion/silent/push-in-still-5s": "wan_push_in",
        "motion/silent/parallax-still-5s": "wan_parallax",
        "motion/av/text-to-video-8s": "ltx_t2v",
        "motion/av/still-to-video-8s": "ltx_i2v",
        "motion/av/still-to-shot": "ltx_i2v",
        "motion/av/shorts-still-8s": "ltx_i2v",
        "motion/av/broll-ambient": "ltx_broll",
        "motion/av/weather-broll": "ltx_broll",
        "motion/av/interior-ambience": "ltx_broll",
        "motion/av/hook-av": "ltx_hook",
        "motion/av/dialogue-8s": "ltx_dialogue",
        "motion/av/multishot-8s": "ltx_multishot",
        "motion/av/product-hero": "ltx_product",
        "motion/av/first-last-8s": "ltx_flf",
        "motion/av/audio-to-video-8s": "ltx_a2v",
        "dcc/depth-control-8s": "ltx_iclora",
        "dcc/canny-control-8s": "ltx_iclora",
        "dcc/depth-control-shorts": "ltx_iclora",
        "dcc/depth-from-loader": "ltx_iclora",
        "films/go-see": "film_gosee",
        "films/still-here": "film_still_here",
        "films/switchyard": "film_switchyard",
        "audio/podcast/two-host-episode": "podcast_two_host",
        "audio/podcast/radio-drama": "podcast_radio",
        "audio/podcast/learn-episode": "podcast_learn",
        "audio/music/rap-draft": "rap_draft",
        "audio/music/rap-full": "rap_full",
        "inspire/prompt-forge": "forge_lazy",
        "inspire/research-chat": "research_chat",
        "inspire/app-forge": "app_forge",
        "inspire/beat-sheet": "beat_sheet_logline",
    }
    for name, rows in catalogs.items():
        _write(name, rows)
    missing = [cid for cid in index.values() if cid not in catalogs]
    if missing:
        raise SystemExit(f"index points at missing catalogs: {sorted(set(missing))}")
    (DEST / "index.json").write_text(
        json.dumps(index, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote { (DEST / 'index.json').relative_to(ROOT) }")


if __name__ == "__main__":
    main()

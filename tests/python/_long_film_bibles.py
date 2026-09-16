#!/usr/bin/env python3
"""Author and write the five 7.5 min (90-shot) film bibles.

Run via ``python3 tests/python/_long_film_bibles.py`` from the repo root.
Not collected by pytest (leading underscore).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_film.shots import write_shots_yaml  # noqa: E402

SHORTS = ROOT / "workflows" / "shorts"
CAMERAS = (
    "tracking",
    "dolly in",
    "pan left",
    "pan right",
    "fixed camera",
    "dolly out",
)

# Each film: identity, enhance, wordless, hook (LTX identity clause), wan lock,
# then 30 beats of (place, (script, foley, end)×3).
FilmSpec = dict[str, Any]


def _beat(
    place: str,
    s1: str,
    f1: str,
    e1: str,
    s2: str,
    f2: str,
    e2: str,
    s3: str,
    f3: str,
    e3: str,
) -> dict[str, Any]:
    """One enter/traverse/exit beat."""
    return {
        "place": place,
        "shots": (
            (s1, f1, e1),
            (s2, f2, e2),
            (s3, f3, e3),
        ),
    }


def _ltx(
    script: str,
    foley: str,
    camera: str,
    hook: str,
    end_state: str,
    *,
    wordless: bool,
) -> str:
    mix = "Wordless mix: silent mouth. " if wordless else ""
    speech = " No speech." if wordless else ""
    return (
        f"The start image holds as the first frame. {mix}{script} "
        f"{foley} {camera} {hook} Last frames hold {end_state}.{speech} "
        "No music and no score."
    )


def _wan(script: str, camera: str, lock: str, end_state: str) -> str:
    return (
        f"{lock} {script} {camera}, no cut, locked identity. "
        f"Last frames hold {end_state}."
    )


def _parsed(film: str, spec: FilmSpec) -> dict[str, Any]:
    slug = spec["slug"]
    beats: list[dict[str, Any]] = spec["beats"]
    hook = spec["hook"]
    lock = spec["wan_lock"]
    wordless = bool(spec["wordless"])
    shots: list[dict[str, Any]] = []
    prev = "identity"
    beat_no = 1
    for beat in beats:
        shot_no = 1
        for script, foley, end_state in beat["shots"]:
            camera = CAMERAS[(beat_no - 1) % len(CAMERAS)]
            prefix = f"ez_{slug}_b{beat_no}_s{shot_no}"
            cam_prose = {
                "tracking": "The camera tracks forward, no cut.",
                "dolly in": "The camera dollies in, no cut.",
                "pan left": "The camera pans left, no cut.",
                "pan right": "The camera pans right, no cut.",
                "fixed camera": "The camera stays fixed, no cut.",
                "dolly out": "The camera dollies out, no cut.",
            }[camera]
            shots.append(
                {
                    "beat": str(beat_no),
                    "shot": str(shot_no),
                    "prefix": prefix,
                    "load_from": prev,
                    "camera": camera,
                    "end_state": end_state,
                    "audio_world": foley,
                    "script": script,
                    "dialogue": "",
                    "clay": "skip",
                    "look": "",
                    "print_mode": "",
                    "audio_lock": "none",
                    "ltx_i2v": _ltx(
                        script, foley, cam_prose, hook, end_state, wordless=wordless
                    ),
                    "wan_i2v": _wan(script, camera, lock, end_state),
                }
            )
            prev = f"{prefix}_last"
            shot_no += 1
        beat_no += 1
    enhance = "true" if spec["identity_enhance"] else "false"
    return {
        "meta": {
            "film": film,
            "slug": slug,
            "frames": "121",
            "fps": "24",
            "duration_s": "5.00",
            "beats": "30",
            "shots_per_beat": "3",
            "total_shots": "90",
            "publish_cap_s": "450.00",
            "print": "ltx",
            "audio_policy": "world-only",
            "score": "none",
            "identity_seed": "42",
            "identity_enhance": enhance,
        },
        "identity": spec["identity"],
        "shots": shots,
    }


TIDE_TABLE: FilmSpec = {
    "slug": "tidetable",
    "identity_enhance": True,
    "wordless": False,
    "hook": (
        "The weathered unmarked skiff bow stays in the lower third, wet thwart "
        "grain sharp, empty of lettering."
    ),
    "wan_lock": "Third-person unmarked skiff bow in the lower third.",
    "identity": (
        "A photoreal third-person dawn still. A weathered unmarked wooden skiff "
        "bow fills the lower third, wet grain and a blank painter coil on the "
        "thwart, looking out from a stone hard toward a cut of unmarked piles "
        "and grey-pink water. Eye-level 35mm lens, framed for YouTube 16:9, "
        "empty of lettering, mild film grain, clean unmarked lens."
    ),
    "beats": [
        _beat("The hard", "Hands untie the painter from a wet ring", "rope ticks, metal click", "open cut between piles", "The skiff is pushed off the stone", "hull knock, grit scrape", "bow in the cut", "The bow clears the last pile", "water splash, wind", "grey-pink channel"),
        _beat("The cut", "The skiff noses into slack water", "hull tick, wind", "unmarked spar ahead", "Oarlocks creak on a slow pull", "wood creak, splash", "mid-channel light", "The bow aims at a dark pool", "water tick, cloth", "tide-pool lip"),
        _beat("First pool", "The hull kisses a rock shelf", "gravel scrape, splash", "green pool", "A look down into unmarked weed", "water tick, wind", "pale crab-shadow (no face)", "The bow slides along the shelf", "hull knock, grit", "next pool mouth"),
        _beat("Shelf walk", "The skiff tracks the wet granite", "wind, metal tick", "narrow slot", "A drip from the gunwale", "water tick, cloth", "dark slot", "The bow enters the slot", "hull scrape, splash", "fog on the far lip"),
        _beat("Fog edge", "Mist takes the far piles", "wind, water tick", "pale fog wall", "The bow holds a compass heading", "cloth, hull knock", "one unmarked spar", "The spar slides past", "wood creak, splash", "open fog"),
        _beat("Lost shore", "The hard vanishes astern", "wind, water tick", "empty grey", "A slow pull in the fog", "creak, splash", "a second spar", "The bow finds a wider pool", "hull tick, grit", "tide-table of rock"),
        _beat("Tide table", "The skiff grounds on a wet table", "gravel scrape, splash", "flat rock", "Hands hold the thwart", "cloth, wood creak", "anemone-dark water", "The bow points at a second table", "wind, water tick", "higher table"),
        _beat("Macro pool", "A look into a clear unmarked pool", "water tick, wind", "tiny shells", "A drip rings the pool", "splash, tick", "pool center", "The bow lifts on a swell", "hull knock, wind", "fog thinning"),
        _beat("Light leak", "A pale sun bar finds the thwart", "wind, cloth", "gold grain", "Steam of cold water in sun", "steam, splash", "bright lip", "The skiff slides off the table", "gravel scrape, hull tick", "deeper cut"),
        _beat("Channel", "The cut opens to a wider reach", "wind, splash", "distant unmarked spit", "A long pull", "creak, water tick", "spit closer", "The bow aims at the spit", "hull knock, grit", "spit rocks"),
        _beat("Spit", "The hull kisses spit gravel", "gravel scrape, splash", "driftwood unmarked", "A walk of the eye along the spit", "wind, cloth", "far hard ghost", "The bow turns for home", "hull tick, creak", "fog lane home"),
        _beat("Turn", "The skiff comes about in slack", "splash, wood creak", "painter coil", "The coil sits wet on the thwart", "cloth, water tick", "home bearing", "The bow takes the lane", "wind, hull knock", "fog lane"),
        _beat("Lane", "Piles return as pale marks", "wind, water tick", "first pile", "The pile slides past", "hull scrape, splash", "second pile", "The cut narrows", "creak, grit", "stone hard ghost"),
        _beat("Piles", "The hard is a grey bar ahead", "wind, splash", "ring on the wall", "The bow aims at the ring", "hull tick, cloth", "wet ring", "The hull kisses stone", "gravel scrape, metal click", "painter in hand"),
        _beat("Tie", "Hands take the painter", "rope ticks, cloth", "ring close", "The hitch is made", "metal click, wood creak", "tied bow", "The thwart holds still", "water tick, wind", "quiet hard"),
        _beat("Quiet", "The skiff rests against stone", "hull knock, water tick", "wet grain", "A last look down the cut", "wind, splash", "empty channel", "Hands leave the thwart", "cloth, creak", "empty bow"),
        _beat("Hold", "The unmarked bow sits in first real sun", "wind, water tick", "gold thwart", "Steam lifts off wet wood", "steam, cloth", "bright coil", "The camera holds the bow", "hull tick, grit", "still water"),
        _beat("Still water", "Ripples die against stone", "splash, wind", "mirror cut", "A gull-less empty sky", "wind, cloth", "open sky", "The bow and the hard together", "wood creak, water tick", "home plate"),
        _beat("Home plate", "The hard is dry above the ring", "grit, wind", "dry stone", "The painter drips once", "water tick, metal click", "dark ring", "The camera eases back", "cloth, hull knock", "whole skiff"),
        _beat("Ease back", "The whole unmarked skiff in frame", "wind, splash", "skiff and hard", "A slow hold", "water tick, creak", "bow grain", "Last light on the thwart", "steam, cloth", "warm grain"),
        _beat("Last light", "Sun leaves the cut", "wind, water tick", "cool bow", "The coil darkens", "cloth, hull tick", "dark painter", "The ring is a black mark", "metal click, grit", "night-edge stone"),
        _beat("Night edge", "The hard goes blue", "wind, splash", "blue stone", "One last drip", "water tick, creak", "quiet hull", "The camera holds", "cloth, hull knock", "still bow"),
        _beat("Hold two", "No one in frame but the skiff", "wind, water tick", "empty thwart", "The cut is a dark ribbon", "splash, grit", "dark ribbon", "The bow is the only warm wood", "wood creak, cloth", "warm wood"),
        _beat("Warm wood", "Grain of the thwart in close", "cloth, hull tick", "wet grain", "A hairline scratch, unmarked", "grit, water tick", "scratch", "The camera holds the scratch", "wind, creak", "scratch and coil"),
        _beat("Coil", "The blank painter coil fills the frame", "cloth, rope ticks", "coil", "A drip from the coil", "water tick, splash", "drip", "The drip hits stone", "grit, metal click", "stone splash"),
        _beat("Stone splash", "The splash dies", "water tick, wind", "quiet stone", "The hard is empty", "grit, cloth", "empty hard", "The skiff is a dark shape", "hull knock, creak", "dark shape"),
        _beat("Dark shape", "Night takes the cut", "wind, splash", "black water", "The bow is a silhouette", "hull tick, cloth", "silhouette", "A last hull knock", "wood creak, water tick", "silence"),
        _beat("Silence", "The unmarked skiff waits", "wind, cloth", "waiting bow", "No oar, no voice", "water tick, grit", "still coil", "The camera holds until the frame is still", "hull knock, creak", "still frame"),
        _beat("Still frame", "Dawn is gone; the plate is night", "wind, water tick", "night plate", "The ring glints once", "metal click, cloth", "glint", "The glint dies", "grit, splash", "dark ring"),
        _beat("Close", "The weathered unmarked bow in night", "hull tick, wind", "night bow", "A final hold on wet grain", "cloth, water tick", "grain", "The frame holds and does not cut", "wood creak, grit", "held bow"),
    ],
}

NIGHT_OVEN: FilmSpec = {
    "slug": "nightoven",
    "identity_enhance": True,
    "wordless": False,
    "hook": (
        "The flour-dusted linen apron on the steel bench stays in the "
        "foreground, unmarked, empty of lettering."
    ),
    "wan_lock": "Third-person flour-dusted linen apron on a steel bench.",
    "identity": (
        "A photoreal third-person bakery still at 2 a.m. A flour-dusted linen "
        "apron hangs on a steel bench in the foreground, unmarked mixer bowls "
        "and a dark oven mouth behind. Warm tungsten versus a sodium alley "
        "through one high window. Eye-level 35mm lens, framed for YouTube 16:9, "
        "empty of lettering, mild film grain, clean unmarked lens."
    ),
    "beats": [
        _beat("Bench", "The apron hangs still in tungsten", "cloth, hum", "apron on steel", "A hand lifts the apron", "cloth, metal tick", "apron in hand", "The apron is tied", "fabric, click", "tied waist"),
        _beat("Tie", "The knot sits at the waist", "cloth, hum", "knot", "Flour dust lifts", "grit, steam", "dust in tungsten", "The bench is empty", "metal scrape, tick", "empty steel"),
        _beat("Empty steel", "Bowls wait unmarked", "metal tick, hum", "bowls", "A pour of water", "pour, splash", "wet bowl", "A mixer starts", "hum, metal", "turning bowl"),
        _beat("Mixer", "The bowl turns slow", "hum, scrape", "dough", "A scrape of the hook", "metal scrape, tick", "hook", "The mixer stops", "click, hum", "resting dough"),
        _beat("Dough", "Hands fold the dough", "cloth, scrape", "folded dough", "A dust of flour", "grit, cloth", "white bench", "The dough rests", "hum, tick", "resting mound"),
        _beat("Rest", "The oven mouth is dark", "hum, metal tick", "dark mouth", "A match of warmth", "steam, click", "warm door", "The door opens", "metal scrape, steam", "open oven"),
        _beat("Oven", "Heat rolls out", "steam, hum", "orange mouth", "A tray slides in", "metal scrape, tick", "tray in", "The door shuts", "click, steam", "closed door"),
        _beat("Shut", "The window shows sodium alley", "hum, wind", "orange window", "A look at the alley", "wind, grit", "wet asphalt", "Back to the oven", "steam, cloth", "oven door"),
        _beat("Alley glance", "Sodium light on steel", "hum, metal tick", "steel bar", "The apron is a pale shape", "cloth, grit", "pale apron", "Hands check the door", "click, steam", "hot handle"),
        _beat("Handle", "The handle is too hot", "metal tick, cloth", "cloth on handle", "A wait", "hum, steam", "waiting door", "The door opens again", "scrape, steam", "gold bread"),
        _beat("Gold", "Unmarked loaves, no brand", "steam, tick", "loaves", "A tray slides out", "metal scrape, cloth", "tray on bench", "The apron is dusted again", "grit, fabric", "dusted apron"),
        _beat("Dust", "Cooling rack, unmarked", "hum, metal tick", "rack", "A loaf is set down", "tick, steam", "one loaf", "The alley window brightens", "wind, hum", "pale sodium"),
        _beat("Pale sodium", "Night thinning", "wind, cloth", "grey alley", "The mixer is washed", "pour, splash", "wet steel", "A cloth on the bench", "cloth, scrape", "clean steel"),
        _beat("Wash", "Water on steel", "pour, splash", "sheet of water", "A wring of the cloth", "cloth, tick", "wrung cloth", "The apron is untied", "fabric, click", "untied apron"),
        _beat("Untie", "The apron returns to the hook", "cloth, metal tick", "hook", "It hangs", "hum, grit", "hanging apron", "The oven is dark again", "click, steam", "dark mouth"),
        _beat("Dark mouth", "The bakery is almost still", "hum, tick", "still bowls", "A last look at the loaf", "steam, cloth", "one loaf", "The window goes towards dawn", "wind, hum", "blue window"),
        _beat("Blue window", "Tungsten loses to blue", "hum, cloth", "blue steel", "The loaf sits", "tick, steam", "loaf", "Hands do not take it", "cloth, grit", "untouched loaf"),
        _beat("Untouched", "The apron on the hook", "fabric, hum", "hooked apron", "Flour on the floor", "grit, tick", "floor dust", "A broom somewhere off", "scrape, cloth", "clean path"),
        _beat("Path", "The path to the door", "grit, hum", "door", "The door is unmarked", "click, wind", "closed door", "A pause at the door", "cloth, tick", "hand on door"),
        _beat("Door", "The door opens on the alley", "wind, click", "sodium alley", "Steam of cold in the alley", "steam, wind", "cold steam", "The bakery stays behind", "hum, metal tick", "warm interior"),
        _beat("Alley", "Wet asphalt, unmarked", "wind, grit", "asphalt", "A look back at the window", "hum, cloth", "warm window", "The window holds the apron", "fabric, tick", "apron in window"),
        _beat("Window", "The apron is a pale square", "cloth, wind", "pale square", "A hold", "hum, grit", "held square", "Dawn lifts the sodium", "wind, steam", "grey dawn"),
        _beat("Dawn", "The alley goes grey", "wind, grit", "grey brick", "No signage", "tick, cloth", "blank brick", "The bakery window cools", "hum, steam", "cool glass"),
        _beat("Cool glass", "The loaf is a silhouette", "tick, cloth", "silhouette loaf", "The apron still hangs", "fabric, hum", "hanging", "A last tungsten click", "click, metal", "dark shop"),
        _beat("Dark shop", "Lights out", "click, hum", "dark bench", "The apron in the dark", "cloth, grit", "dark apron", "A hold on the hook", "metal tick, fabric", "hook"),
        _beat("Hook", "The hook is a black mark", "metal tick, cloth", "hook", "Flour dust settles", "grit, steam", "settled dust", "The bench is empty", "hum, scrape", "empty bench"),
        _beat("Empty bench", "Steel and night", "metal tick, wind", "steel", "The mixer is a shape", "hum, scrape", "mixer shape", "The oven mouth is black", "click, steam", "black mouth"),
        _beat("Black mouth", "No fire", "tick, cloth", "cold door", "A last steam ghost", "steam, hum", "ghost", "The ghost dies", "wind, grit", "still air"),
        _beat("Still air", "The unmarked bakery waits", "hum, cloth", "waiting shop", "The apron waits", "fabric, tick", "waiting apron", "The camera holds", "metal tick, grit", "held apron"),
        _beat("Close", "Dawn at the high window only", "wind, steam", "high window", "The apron in first grey", "cloth, hum", "grey apron", "The frame holds the apron on steel", "fabric, metal tick", "held bench"),
    ],
}

GLASSHOUSE: FilmSpec = {
    "slug": "glasshouse",
    "identity_enhance": True,
    "wordless": False,
    "hook": (
        "The unmarked copper watering can stays in the foreground on wet "
        "flagstone, empty of lettering."
    ),
    "wan_lock": "Third-person unmarked copper watering can on wet flagstone.",
    "identity": (
        "A photoreal third-person still inside a botanical glasshouse. An "
        "unmarked copper watering can sits on wet flagstone, rain already "
        "ticking the glass roof, unmarked palms and ferns, no readable signs. "
        "Eye-level 35mm lens, framed for YouTube 16:9, empty of lettering, "
        "mild film grain, clean unmarked lens."
    ),
    "beats": [
        _beat("Flagstone", "Rain ticks the glass roof", "rain, tick", "roof ticks", "The can sits copper-wet", "metal tick, cloth", "wet can", "A drip hits the can", "splash, rain", "drip on copper"),
        _beat("Drip", "Drips become a sheet", "rain, splash", "sheet on glass", "Ferns bow", "wind, cloth", "bowed fern", "The can is moved", "metal scrape, grit", "can in hand"),
        _beat("In hand", "A pour into a clay pot", "pour, splash", "pot", "The pot drinks", "water tick, grit", "dark soil", "The can lowers", "metal tick, cloth", "can on stone"),
        _beat("Stone", "Puddle around the can", "splash, rain", "puddle", "A look up the nave of glass", "wind, rain", "glass nave", "Unmarked spars, no brand", "metal tick, wind", "spars"),
        _beat("Spars", "Rain on the ridge", "rain, tick", "ridge", "A leaf dumps water", "splash, cloth", "leaf", "The can is filled from a barrel", "pour, metal", "full can"),
        _beat("Barrel", "The barrel is unmarked", "pour, splash", "barrel", "Hands lift the full can", "metal scrape, cloth", "heavy can", "A walk down the aisle", "footstep, rain", "aisle"),
        _beat("Aisle", "Palms left and right", "rain, wind", "palms", "The can pours again", "pour, tick", "second pot", "Thunder is only rain louder", "rain, metal tick", "loud roof"),
        _beat("Loud roof", "The glass drums", "rain, tick", "drumming glass", "A puddle races the flagstone", "splash, grit", "racing puddle", "The can waits", "metal tick, cloth", "waiting can"),
        _beat("Wait", "Storm light, green", "wind, rain", "green dark", "A fern against the can", "cloth, tick", "fern and copper", "The fern drips on copper", "splash, metal", "drip on can"),
        _beat("Drip on can", "Copper darkens", "rain, metal tick", "dark copper", "A pour at the far bench", "pour, splash", "far bench", "The bench is wet wood", "wood creak, rain", "wet wood"),
        _beat("Wet wood", "Pots in a row, unmarked", "tick, grit", "row", "One pot overflows", "splash, pour", "overflow", "The overflow runs to stone", "water tick, rain", "runnel"),
        _beat("Runnel", "The runnel finds the aisle", "splash, grit", "aisle water", "A walk with the can", "footstep, metal", "walking can", "The door at the end is glass", "wind, rain", "glass door"),
        _beat("Glass door", "Rain outside harder", "rain, wind", "outside sheet", "The door stays shut", "click, cloth", "shut door", "A hold on the can against the door", "metal tick, rain", "can and door"),
        _beat("Can and door", "Steam fogs the glass", "steam, wind", "fogged glass", "A wipe", "cloth, tick", "cleared pane", "The garden outside is unmarked", "rain, grit", "wet garden"),
        _beat("Garden", "No path signs", "rain, wind", "blank garden", "Back to the nave", "footstep, splash", "nave", "The can is set down", "metal scrape, grit", "can on flag"),
        _beat("Can on flag", "Storm eases a hair", "rain, tick", "softer roof", "Light finds copper", "metal tick, wind", "bright copper", "A last pour", "pour, splash", "last pot"),
        _beat("Last pot", "The last pot is a fern", "pour, cloth", "fern pot", "Soil goes dark", "water tick, grit", "dark soil", "The can is empty", "metal tick, scrape", "empty can"),
        _beat("Empty can", "A shake", "metal tick, splash", "last drops", "The drops hit stone", "tick, rain", "drops", "The can rests", "cloth, grit", "resting can"),
        _beat("Resting", "Rain becomes drip", "rain, tick", "drip roof", "Gutters somewhere", "pour, metal", "gutter", "The nave brightens", "wind, cloth", "bright green"),
        _beat("Bright green", "Steam off flagstone", "steam, rain", "steam", "The can is a warm coin", "metal tick, wind", "warm copper", "A hold", "cloth, tick", "held can"),
        _beat("Held can", "No one else in the nave", "rain, wind", "empty nave", "Palms drip", "splash, cloth", "dripping palms", "The camera finds the can again", "metal tick, grit", "can center"),
        _beat("Can center", "Copper and wet stone", "tick, rain", "copper stone", "A slow circle of drips", "splash, wind", "drip circle", "The storm is a memory", "rain, cloth", "soft rain"),
        _beat("Soft rain", "The roof is only ticks", "tick, wind", "ticks", "A birdless quiet", "cloth, grit", "quiet", "The can does not move", "metal tick, rain", "still can"),
        _beat("Still can", "Light goes gold-green", "wind, steam", "gold-green", "Fern lace on copper", "cloth, tick", "lace shadow", "The shadow slides", "rain, metal", "moving lace"),
        _beat("Lace", "The storm has passed the ridge", "wind, rain", "clear ridge", "Puddles remain", "splash, grit", "puddles", "The can sits in a puddle", "metal tick, water tick", "can in puddle"),
        _beat("Puddle", "A sky in the puddle", "wind, splash", "sky puddle", "The copper breaks the sky", "metal tick, cloth", "broken sky", "A hold on that break", "tick, rain", "held break"),
        _beat("Held break", "Evening in the glass", "wind, steam", "evening glass", "The can cools", "metal tick, grit", "cool copper", "No more pours", "cloth, tick", "idle can"),
        _beat("Idle can", "The nave empties of weather", "wind, cloth", "still palms", "A last drip from the ridge", "tick, splash", "last drip", "The drip misses the can", "grit, rain", "missed drip"),
        _beat("Missed drip", "The drip hits stone", "splash, tick", "stone splash", "The can is dry-topped", "metal tick, cloth", "dry copper", "Night at the glass", "wind, steam", "night glass"),
        _beat("Close", "Night glasshouse, unmarked", "wind, tick", "night nave", "The copper can in one lamp", "metal tick, cloth", "lamp copper", "The frame holds the can on wet flagstone", "rain, grit", "held can"),
    ],
}

LAST_LANE: FilmSpec = {
    "slug": "lastlane",
    "identity_enhance": False,
    "wordless": True,
    "hook": (
        "Blank matte-black gloves stay on the unmarked wheel along the bottom "
        "edge, empty palms, dusty dash, no badges."
    ),
    "wan_lock": "Dashboard first-person, blank gloves on an unmarked wheel.",
    "identity": (
        "A dashboard first-person still at night on an unmarked two-lane. Dusty "
        "cracked dash, blank matte-black gloves on an unmarked wheel along the "
        "bottom edge, empty palms, headlight cone on pale gravel and sage. No "
        "vehicle badges, empty of lettering. Eye-level 24mm lens, framed for "
        "YouTube 16:9, mild film grain, clean unmarked lens."
    ),
    "beats": [
        _beat("Gravel", "The cone finds pale gravel", "grit, wind", "gravel road", "Gloves ease the wheel", "cloth, tick", "wheel ease", "A sage bush slides past", "wind, scrape", "sage"),
        _beat("Sage", "Bugs tick the unmarked glass", "tick, wind", "glass ticks", "The lane is only two ruts", "grit, hum", "two ruts", "A rise ahead", "wind, cloth", "rise"),
        _beat("Rise", "The cone climbs", "hum, grit", "crest", "A crest, then more lane", "wind, tick", "more lane", "Radio is only static hiss", "hum, wind", "static"),
        _beat("Static", "No song, only hiss", "hum, tick", "hiss", "Gloves do not reach a dial", "cloth, grit", "hands on wheel", "A cattle-grid rumble, unmarked", "metal, scrape", "grid"),
        _beat("Grid", "The grid ends", "metal tick, grit", "past grid", "The lane straightens", "wind, hum", "straight cone", "A pale mile with no sign", "grit, cloth", "no sign"),
        _beat("No sign", "Empty of lettering, always", "wind, tick", "blank night", "A jackrabbit-shadow only", "grit, scrape", "shadow gone", "The cone is the only light", "hum, wind", "only cone"),
        _beat("Only cone", "Dash cracks in the glow", "tick, cloth", "cracked dash", "Gloves at ten and two", "fabric, hum", "gloves", "A dip", "grit, wind", "dip"),
        _beat("Dip", "The cone dives", "hum, grit", "low cone", "Dust lifts", "wind, scrape", "dust", "The dip climbs out", "tick, cloth", "out of dip"),
        _beat("Out", "A fork, both unmarked", "wind, grit", "fork", "The wheel takes the left", "cloth, tick", "left rut", "The right dies in sage", "scrape, hum", "left only"),
        _beat("Left only", "The left is worse gravel", "grit, wind", "worse gravel", "A stone pops the wheel well", "tick, metal", "pop", "The cone finds a wash", "splash, grit", "wash"),
        _beat("Wash", "A thin wet line", "splash, wind", "wet line", "Gloves hold through it", "cloth, hum", "held wheel", "The wash is crossed", "grit, tick", "far bank"),
        _beat("Far bank", "Sage again", "wind, scrape", "sage again", "A long straight", "hum, grit", "long cone", "Heat-ghost of the day still", "steam, wind", "ghost"),
        _beat("Ghost", "The ghost dies", "wind, tick", "clear cone", "Dash dust hangs", "grit, cloth", "dust hang", "A faint other cone far", "hum, wind", "far light"),
        _beat("Far light", "It is not a town", "tick, grit", "not a town", "The other cone turns away", "wind, cloth", "gone light", "Alone again", "hum, scrape", "alone cone"),
        _beat("Alone cone", "The lane bends", "wind, grit", "bend", "Gloves follow", "cloth, tick", "follow", "A tank or trough, unmarked", "metal, wind", "trough"),
        _beat("Trough", "The trough slides past", "metal tick, grit", "past trough", "No cattle in frame", "wind, cloth", "empty", "The bend opens", "hum, scrape", "open flat"),
        _beat("Open flat", "Stars, no town glow", "wind, tick", "stars", "The cone is a short world", "grit, hum", "short world", "A slow mile", "cloth, wind", "slow mile"),
        _beat("Slow mile", "Gloves ease", "fabric, tick", "eased gloves", "The ruts shallow", "grit, scrape", "shallow ruts", "A harder pack", "hum, wind", "hard pack"),
        _beat("Hard pack", "Faster gravel tick", "tick, grit", "fast tick", "The wheel is still", "cloth, hum", "still wheel", "A rise of black mesa", "wind, scrape", "mesa"),
        _beat("Mesa", "The mesa is a wall", "wind, grit", "mesa wall", "The lane skirts it", "hum, tick", "skirt", "A pull-out of dirt", "scrape, cloth", "pull-out"),
        _beat("Pull-out", "The wheel does not take it", "cloth, wind", "pass pull-out", "The mesa ends", "grit, tick", "mesa end", "More lane", "hum, scrape", "more lane"),
        _beat("More lane", "A second wash, dry", "grit, wind", "dry wash", "Cross", "tick, cloth", "crossed", "The cone finds a gate, unmarked, open", "metal, scrape", "open gate"),
        _beat("Open gate", "No sign on the gate", "metal tick, wind", "blank gate", "Through", "grit, hum", "through gate", "The lane is the same", "cloth, tick", "same lane"),
        _beat("Same lane", "Dawn is a rumour", "wind, steam", "east pale", "Gloves stay", "fabric, grit", "staying gloves", "The pale grows", "hum, tick", "more pale"),
        _beat("More pale", "Sage goes from black to grey", "wind, scrape", "grey sage", "The cone weakens", "tick, cloth", "weak cone", "Day wants the dash", "grit, hum", "day dash"),
        _beat("Day dash", "Dust on the dash in grey", "grit, tick", "grey dust", "The wheel is clearer", "cloth, wind", "clear wheel", "No badges still", "hum, scrape", "blank wheel"),
        _beat("Blank wheel", "The lane keeps", "wind, grit", "keeps", "A last night bug on the glass", "tick, cloth", "bug", "The bug is gone", "hum, wind", "clean glass"),
        _beat("Clean glass", "Dawn on unmarked country", "wind, steam", "dawn country", "Gloves at rest on the wheel", "fabric, tick", "resting gloves", "The cone is nothing", "grit, cloth", "daylight ruts"),
        _beat("Daylight ruts", "The two-lane in first sun", "wind, grit", "sun ruts", "A hold on the gloves", "cloth, tick", "held gloves", "The dash in sun", "hum, scrape", "sun dash"),
        _beat("Close", "Blank gloves on the unmarked wheel", "cloth, wind", "gloves and wheel", "The country goes gold", "grit, tick", "gold sage", "The frame holds the dash and the lane", "fabric, hum", "held dash"),
    ],
}

BREAKWATER: FilmSpec = {
    "slug": "breakwater",
    "identity_enhance": False,
    "wordless": True,
    "hook": (
        "The wearer's own yellow unmarked slicker sleeves and blank matte-black "
        "gloves stay along the bottom edge, empty palms, no second body, no face."
    ),
    "wan_lock": (
        "First-person eye-level body-cam, yellow slicker sleeves and blank "
        "gloves along the bottom edge."
    ),
    "identity": (
        "A chest-mounted first-person body-cam still, eye-level, already walking "
        "a wet granite storm wall. Only the wearer's own yellow unmarked slicker "
        "sleeves and blank matte-black gloves enter from the bottom edge: "
        "contralateral swing, empty palms, hands free. Grey sea to the left, "
        "unmarked concrete to the right. Wide 24mm body-cam, slight barrel, a "
        "full-bleed photographic plate in YouTube 16:9 with bare frame edges and "
        "a clean unmarked lens, empty of lettering."
    ),
    "beats": [
        _beat("Wall walk", "A walk already underway on wet granite", "boot, wind", "granite blocks", "Gloves swing contralateral", "cloth, fabric", "swing", "Spray from the left", "splash, wind", "spray"),
        _beat("Spray", "The sea hits the wall", "splash, wind", "white water", "A look at the next block", "boot, grit", "next block", "The block is taken", "footstep, scrape", "taken block"),
        _beat("Taken block", "A gap between blocks", "wind, grit", "gap", "A step over the gap", "boot, splash", "over gap", "The far block holds", "footstep, cloth", "far block"),
        _beat("Far block", "A generic foghorn, not a real harbour", "horn, wind", "horn", "Gloves do not cover ears", "fabric, tick", "open gloves", "The wall turns", "boot, scrape", "turn"),
        _beat("Turn", "The turn shows more wall", "wind, splash", "more wall", "A puddle on granite", "water tick, grit", "puddle", "Through the puddle", "splash, boot", "past puddle"),
        _beat("Past puddle", "Rail to the right, unmarked", "metal tick, wind", "rail", "A glove near the rail, not grabbing", "cloth, scrape", "near rail", "The rail ends", "boot, grit", "rail end"),
        _beat("Rail end", "Open wall, sea louder", "wind, splash", "open wall", "A low crouch of the camera", "boot, cloth", "low cam", "Up again", "footstep, wind", "eye-level"),
        _beat("Eye-level", "Horizon bob with walk", "boot, wind", "bob", "Spray again", "splash, fabric", "spray two", "A stair of blocks down", "grit, scrape", "stairs"),
        _beat("Stairs", "Down three blocks", "boot, footstep", "down", "A landing", "grit, wind", "landing", "The sea is closer", "splash, horn", "close sea"),
        _beat("Close sea", "Green water, unmarked", "splash, wind", "green water", "A look, then walk", "boot, cloth", "walk on", "A chain, unmarked, rust", "metal, scrape", "chain"),
        _beat("Chain", "The chain is not held", "metal tick, wind", "idle chain", "Past the chain", "boot, grit", "past chain", "A wider landing", "footstep, splash", "wide landing"),
        _beat("Wide landing", "Puddles and grit", "grit, water tick", "grit puddles", "A pause", "wind, cloth", "pause", "Walk resumes", "boot, fabric", "resume"),
        _beat("Resume", "The wall climbs", "footstep, scrape", "climb", "Gloves pump", "cloth, wind", "pump", "The top is a path", "boot, grit", "top path"),
        _beat("Top path", "A path of wet concrete, unmarked", "grit, wind", "concrete path", "Sea left, townless right", "splash, boot", "sea left", "A lamp, generic, unlit", "metal tick, cloth", "unlit lamp"),
        _beat("Unlit lamp", "Past the lamp", "boot, wind", "past lamp", "Fog on the path", "wind, cloth", "fog path", "The fog thickens", "splash, grit", "thick fog"),
        _beat("Thick fog", "The wall edge is a guess", "wind, boot", "edge guess", "A slower walk", "footstep, cloth", "slow walk", "The horn again, generic", "horn, wind", "horn two"),
        _beat("Horn two", "No answering horn", "wind, splash", "one horn", "Gloves stay visible", "fabric, tick", "visible gloves", "Fog thins on a gust", "wind, grit", "thin fog"),
        _beat("Thin fog", "The path again", "boot, scrape", "path again", "A bench, unmarked, empty", "wood creak, wind", "empty bench", "The bench is passed", "footstep, cloth", "past bench"),
        _beat("Past bench", "A dip in the wall", "grit, splash", "dip", "Through the dip", "boot, wind", "through dip", "The far side climbs", "footstep, scrape", "climb two"),
        _beat("Climb two", "Up to a lookout pad", "boot, grit", "lookout", "A hold on the sea", "wind, splash", "held sea", "No ships with marks", "horn, cloth", "empty sea"),
        _beat("Empty sea", "Grey to the horizon", "wind, splash", "horizon", "A turn back along the wall", "boot, fabric", "turn back", "The path home", "footstep, grit", "home path"),
        _beat("Home path", "The unlit lamp returns", "metal tick, wind", "lamp return", "Past it the other way", "boot, cloth", "other way", "Spray less", "splash, grit", "less spray"),
        _beat("Less spray", "The sea is a rumble", "wind, splash", "rumble", "A faster walk", "footstep, fabric", "faster", "The stairs up", "boot, scrape", "stairs up"),
        _beat("Stairs up", "Up the blocks", "footstep, grit", "up", "The original wall", "wind, cloth", "original wall", "The gap again", "boot, splash", "gap two"),
        _beat("Gap two", "Over the gap homeward", "footstep, scrape", "over home", "Gloves still blank", "fabric, tick", "blank gloves", "The first granite", "boot, wind", "first granite"),
        _beat("First granite", "The start of the wall", "grit, splash", "start wall", "A last look at sea", "wind, horn", "last sea", "Walk toward the unmarked land end", "boot, cloth", "land end"),
        _beat("Land end", "Concrete meets a path", "grit, footstep", "path join", "No gate, no sign", "wind, scrape", "no gate", "A stop", "boot, cloth", "stop"),
        _beat("Stop", "Gloves hang still", "fabric, wind", "still gloves", "Only wind at the wall", "wind, splash", "wind only", "A hold on the wall behind", "grit, tick", "wall behind"),
        _beat("Wall behind", "The storm wall in grey", "wind, splash", "grey wall", "Sleeves at the bottom edge", "cloth, fabric", "sleeves", "The sea keeps", "horn, boot", "keeping sea"),
        _beat("Close", "Yellow unmarked slicker sleeves in frame", "cloth, wind", "sleeves in frame", "Blank gloves, empty palms", "fabric, tick", "empty palms", "The frame holds the wall and the sea", "splash, grit", "held wall"),
    ],
}

SPECS: dict[str, FilmSpec] = {
    "tide-table": TIDE_TABLE,
    "night-oven": NIGHT_OVEN,
    "glasshouse": GLASSHOUSE,
    "last-lane": LAST_LANE,
    "breakwater": BREAKWATER,
}

ACT_TITLES: dict[str, tuple[str, ...]] = {
    "tide-table": (
        "Launch from the hard",
        "Tide tables",
        "Fog and spit",
        "Home the cut",
        "Night on the bow",
    ),
    "night-oven": (
        "Tie the apron",
        "Heat",
        "Gold loaves",
        "Alley dawn",
        "Lights out",
    ),
    "glasshouse": (
        "Rain on copper",
        "Nave of glass",
        "Door and garden",
        "Storm passing",
        "Night can",
    ),
    "last-lane": (
        "Gravel cone",
        "Fork and wash",
        "Mesa",
        "Open gate",
        "Dawn dash",
    ),
    "breakwater": (
        "Wall walk",
        "Stairs to sea",
        "Fog path",
        "Lookout and return",
        "Land end hold",
    ),
}


def write_all(*, dest: Path | None = None) -> list[Path]:
    """Write the five long-film YAML bibles.

    Args:
        dest: Override ``workflows/shorts`` directory.

    Returns:
        Paths written.
    """
    out_dir = dest if dest is not None else SHORTS
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for film, spec in SPECS.items():
        if len(spec["beats"]) != 30:
            raise SystemExit(f"{film} has {len(spec['beats'])} beats, need 30")
        parsed = _parsed(film, spec)
        path = out_dir / f"{film}.shots.yaml"
        path.write_text(write_shots_yaml(parsed), encoding="utf-8")
        written.append(path)
        print(f"wrote {path.relative_to(ROOT)}")
    return written


if __name__ == "__main__":
    write_all()

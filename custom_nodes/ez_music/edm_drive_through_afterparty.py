"""Drive-through 180s bass-set takes (hour 4, afterparty).

Fictional act. Original dance arrangements. No living-artist names.
Warped hybrid-trap EDM: drop first, hard warpy drops, trap drums, dual-action
pedal bass on some takes, all instrumental.
"""

from __future__ import annotations

from .edm_examples import EdmExample, _ex, format_edm_score

# Catalog phase, track scores, and catalog rows.
AFTERPARTY_PHASE = 3


BRAKE_FADE_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nchest 808 warp\nbrake wreck"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder growl drop\nstacked 808 wall\nformant grind"),
    ("inst", "snare roll\nchest 808 punch"),
    ("inst", "full send drop\nlow rumble wreck\nwarped dirty"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)

DIESEL_HUM_LYRICS = format_edm_score(
    ("inst", "heavy warped drop\ndual-action pedal bass\nchest 808 wreck"),
    ("inst", "pedal 808 hold\ntrap hats roll"),
    ("inst", "harder growl drop\nrolling 808 wall\nhybrid formant"),
    ("inst", "full send drop\nchest sub wreck\npedal warp"),
    ("outro", "kick holds\nhats denser\npedal ride"),
)

AXLE_GRIND_LYRICS = format_edm_score(
    ("inst", "heavy tearout drop\ngrowl wreck\nwarped axle"),
    ("inst", "metal hats roll\ngrowl sustain"),
    ("inst", "harder formant drop\nsub crush\nchest 808"),
    ("inst", "trap hats denser\ngrowl hold"),
    ("inst", "full send drop\nstacked growl wreck\ntearout warp"),
    ("inst", "harder growl drop\nlow 808 wreck\naxle grind"),
    ("outro", "kick holds\nhats denser\ngrowl ride"),
)

WEIGH_STATION_LYRICS = format_edm_score(
    ("inst", "heavy brostep drop\nstacked 808 warp\nweigh wreck"),
    ("inst", "trap hats roll\ngrowl hold"),
    ("inst", "harder growl drop\nchest sub wall\nformant 808"),
    ("inst", "snare roll\n808 punch"),
    ("inst", "full send drop\nbody bass wreck\nwarped brostep"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)

BLACK_ICE_LYRICS = format_edm_score(
    ("inst", "heavy riddim drop\nwobble wreck\nwarped ice"),
    ("inst", "metal hats roll\nwobble sustain"),
    ("inst", "harder growl drop\nchest growl wreck\n808 crush"),
    ("inst", "trap hats denser\nwobble hold"),
    ("inst", "full send drop\nsub crush wreck\nchest formant"),
    ("inst", "snare roll\nbass growl hold"),
    ("inst", "harder warped drop\nlow rumble wreck\nriddim 808"),
    ("outro", "kick holds\nhats denser\nwobble ride"),
)

HIGH_BEAMS_LYRICS = format_edm_score(
    ("inst", "heavy color drop\ndual-action pedal bass\nchest 808 warp"),
    ("inst", "pedal 808 hold\ntrap hats roll"),
    ("inst", "harder stacked drop\nhybrid 808 wall\ncolor formant"),
    ("inst", "snare roll\nchest 808"),
    ("inst", "full send drop\nbody sub wreck\nwarped color"),
    ("inst", "harder growl drop\nstacked 808 wreck\npedal warp"),
    ("outro", "kick holds\nhats denser\ncolor ride"),
)

CHAIN_HOOK_LYRICS = format_edm_score(
    ("inst", "heavy brostep drop\ngrowl wreck\nwarped chain"),
    ("inst", "harder dirty drop\ndubstep wreck\nchest 808 formant"),
    ("inst", "full send drop\nstacked 808 wreck\ntrap growl"),
    ("outro", "kick holds\ntrap hats roll\ngrowl ride"),
)

GRIT_PLATE_LYRICS = format_edm_score(
    ("inst", "heavy wave drop\nwarped 808 wreck\ngrit fold"),
    ("inst", "trap hats denser\nwave 808 hold grit"),
    ("inst", "harder growl drop\nstacked 808 wall\nchest formant"),
    ("inst", "full send drop\nbody bass wreck\nwave warp"),
    ("outro", "kick holds\nhats denser\nwave ride"),
)

STEEL_GRATE_LYRICS = format_edm_score(
    ("inst", "heavy amen drop\nreese wreck\nwarped grate"),
    ("inst", "amen chops\ntrap hats 808 grate"),
    ("inst", "harder growl drop\nreese stack\nchest 808"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "full send drop\nstacked amen wreck\nformant 808"),
    ("inst", "snare roll\nchest 808 punch"),
    ("inst", "harder warped drop\nchest 808 wreck\ndrumstep grind"),
    ("inst", "full send drop\nlow rumble wreck\nreese wall"),
    ("outro", "kick holds\namen keep\nreese ride"),
)

REST_BAY_LYRICS = format_edm_score(
    ("inst", "heavy chest drop\ndual-action pedal bass\nsub warp wreck"),
    ("inst", "pedal 808 hold\ntrap hats roll"),
    ("inst", "harder growl drop\nstacked 808 wall\nchest formant"),
    ("inst", "snare roll\nchest 808"),
    ("inst", "full send drop\nbody chest wreck\npedal warp"),
    ("inst", "harder stacked drop\nlow 808 wreck\ntrap growl"),
    ("outro", "kick holds\nhats denser\npedal ride"),
)

HAUL_CRATE_LYRICS = format_edm_score(
    ("inst", "heavy hybrid drop\ntrap 808 wreck\nwarped crate"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder growl drop\nstacked trap bass\nchest formant"),
    ("inst", "snare roll\nchest 808 punch"),
    ("inst", "full send drop\nchest 808 wall\nhybrid warp"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)

NIGHT_SPLICE_LYRICS = format_edm_score(
    ("inst", "heavy wave drop\nwarped bass wreck\nsplice 808"),
    ("inst", "trap hats denser\nwave 808 sustain splice"),
    ("inst", "harder growl drop\nchest 808 wall\nformant fold"),
    ("inst", "full send drop\nlow swell wreck\nwave warp"),
    ("outro", "kick holds\nhats denser\nwave ride"),
)

TORQUE_BAY_LYRICS = format_edm_score(
    ("inst", "heavy neuro drop\nreese 808 wreck\nwarped torque"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "harder stacked drop\nchest reese wreck\nformant coil"),
    ("inst", "trap hats roll\n808 punch"),
    ("inst", "full send drop\nneuro 808 wreck\nchest warp"),
    ("inst", "harder growl drop\nstacked reese wreck\ntorque grind"),
    ("outro", "kick holds\ntrap hats roll\nreese ride"),
)

SPARE_DRUM_LYRICS = format_edm_score(
    ("inst", "heavy brostep drop\ndual-action pedal bass\nchest 808 warp"),
    ("inst", "pedal 808 hold\ntrap hats roll"),
    ("inst", "harder stacked drop\n808 wall wreck\nformant growl"),
    ("inst", "snare roll\nchest 808"),
    ("inst", "full send drop\nbody bass wreck\npedal warp"),
    ("outro", "kick holds\nhats denser\nbrostep ride"),
)

OIL_PAN_LYRICS = format_edm_score(
    ("inst", "heavy color drop\nwarped 808 wreck\npan grind"),
    ("inst", "trap hats roll\n808 punch hold"),
    ("inst", "harder growl drop\nstacked color 808\nchest formant"),
    ("inst", "snare roll\nchest 808"),
    ("inst", "full send drop\nbody bass wreck\ncolor warp"),
    ("inst", "harder stacked drop\nchest sub wreck\nwarped 808 wall"),
    ("outro", "kick holds\nhats denser\ncolor ride"),
)

CURB_CHECK_LYRICS = format_edm_score(
    ("inst", "heavy amen drop\n808 warp wreck\ncurb grind"),
    ("inst", "amen chops\ntrap hats 808 curb"),
    ("inst", "harder stacked drop\nreese 808 wreck\nchest formant"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "full send drop\nstacked amen wreck\nwarped 808"),
    ("inst", "snare roll\ncurb 808 punch"),
    ("inst", "harder growl drop\nchest trap wreck\ndrumstep grind"),
    ("outro", "kick holds\namen keep\nreese ride"),
)

LAST_EXIT_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\ndual-action pedal bass\nwarped exit"),
    ("inst", "pedal 808 hold\ntrap hats roll"),
    ("inst", "harder growl drop\nchest 808 wall\nformant crush"),
    ("inst", "full send drop\nlow rumble wreck\npedal warp"),
    ("outro", "kick holds\nhats denser\npedal ride"),
)

ASPHALT_HEART_LYRICS = format_edm_score(
    ("inst", "heavy chest drop\nsub warp wreck\nasphalt 808"),
    ("inst", "trap hats denser\nchest 808 hold"),
    ("inst", "full send drop\nbody chest wreck\nwarped 808"),
    ("outro", "kick holds\ntrap hats roll\nchest ride"),
)

CLUTCH_SLAM_LYRICS = format_edm_score(
    ("inst", "heavy tearout drop\ndual-action pedal bass\ngrowl wreck"),
    ("inst", "metal hats roll\ngrowl sustain"),
    ("inst", "harder formant drop\nsub crush\nchest 808"),
    ("inst", "pedal 808 hold\ntrap hats roll"),
    ("inst", "full send drop\nstacked growl wreck\nwarped clutch"),
    ("inst", "snare roll\n808 punch"),
    ("inst", "harder stacked drop\nchest 808 wreck\ntearout warp"),
    ("inst", "full send drop\nlow rumble wreck\npedal growl"),
    ("outro", "kick holds\nhats denser\ngrowl ride"),
)

TRAILER_HITCH_LYRICS = format_edm_score(
    ("inst", "heavy warped drop\nchest 808 wreck\nhitch grind"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder stacked drop\nrolling 808 wall\nhybrid formant"),
    ("inst", "snare roll\nchest 808 punch"),
    ("inst", "full send drop\nbody bass wreck\ntrap warp"),
    ("inst", "harder growl drop\nstacked 808 wreck\nchest formant"),
    ("inst", "full send drop\nchest sub wreck\nwarped hitch"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)


EDM_DRIVE_THROUGH_AFTERPARTY: tuple[EdmExample, ...] = (
    _ex(
        "brake-fade",
        "brake fade",
        150,
        457,
        AFTERPARTY_PHASE,
        "brake-fade dirty bass warp",
        BRAKE_FADE_LYRICS,
        recipe="rec_drive_dirty",
        picks={"bass_low_end": "bass_stacked_808"},
        layout="column",
    ),
    _ex(
        "diesel-hum",
        "diesel hum",
        152,
        461,
        AFTERPARTY_PHASE,
        "diesel-hum hybrid trap warp",
        DIESEL_HUM_LYRICS,
        recipe="rec_drive_through_drop",
        picks={"bass_low_end": "bass_pedal_dual"},
        layout="wide-stage",
    ),
    _ex(
        "axle-grind",
        "axle grind",
        155,
        463,
        AFTERPARTY_PHASE,
        "axle-grind tearout warp",
        AXLE_GRIND_LYRICS,
        recipe="rec_drive_tearout",
        layout="stacked-tower",
    ),
    _ex(
        "weigh-station",
        "weigh station",
        158,
        467,
        AFTERPARTY_PHASE,
        "weigh-station brostep warp",
        WEIGH_STATION_LYRICS,
        recipe="rec_drive_brostep",
        picks={"bass_low_end": "bass_stacked_808"},
        layout="prompt-left",
    ),
    _ex(
        "black-ice",
        "black ice",
        160,
        479,
        AFTERPARTY_PHASE,
        "black-ice riddim warp",
        BLACK_ICE_LYRICS,
        recipe="rec_drive_riddim",
        layout="output-rail",
    ),
    _ex(
        "high-beams",
        "high beams",
        165,
        487,
        AFTERPARTY_PHASE,
        "high-beams color bass warp",
        HIGH_BEAMS_LYRICS,
        recipe="rec_drive_color",
        picks={"bass_low_end": "bass_pedal_dual"},
        layout="column",
    ),
    _ex(
        "chain-hook",
        "chain hook",
        168,
        491,
        AFTERPARTY_PHASE,
        "chain-hook dirty dubstep warp",
        CHAIN_HOOK_LYRICS,
        recipe="rec_drive_brostep",
        picks={"genre_style": "gen_dirty_dubstep"},
        layout="wide-stage",
    ),
    _ex(
        "grit-plate",
        "grit plate",
        150,
        499,
        AFTERPARTY_PHASE,
        "grit-plate wave bass warp",
        GRIT_PLATE_LYRICS,
        recipe="rec_drive_wave",
        layout="stacked-tower",
    ),
    _ex(
        "steel-grate",
        "steel grate",
        172,
        503,
        AFTERPARTY_PHASE,
        "steel-grate drumstep warp",
        STEEL_GRATE_LYRICS,
        recipe="rec_drive_drumstep",
        picks={"drums_rhythm": "drm_amen_chop"},
        layout="prompt-left",
    ),
    _ex(
        "rest-bay",
        "rest bay",
        155,
        509,
        AFTERPARTY_PHASE,
        "rest-bay chest bass warp",
        REST_BAY_LYRICS,
        recipe="rec_drive_chest",
        picks={"bass_low_end": "bass_pedal_dual"},
        layout="output-rail",
    ),
    _ex(
        "haul-crate",
        "haul crate",
        170,
        521,
        AFTERPARTY_PHASE,
        "haul-crate hybrid trap warp",
        HAUL_CRATE_LYRICS,
        recipe="rec_drive_through_drop",
        picks={"genre_style": "gen_dirty_bass"},
        layout="column",
    ),
    _ex(
        "night-splice",
        "night splice",
        152,
        523,
        AFTERPARTY_PHASE,
        "night-splice wave bass warp",
        NIGHT_SPLICE_LYRICS,
        recipe="rec_drive_wave",
        layout="wide-stage",
    ),
    _ex(
        "torque-bay",
        "torque bay",
        176,
        541,
        AFTERPARTY_PHASE,
        "torque-bay neuro bass warp",
        TORQUE_BAY_LYRICS,
        recipe="rec_drive_neuro",
        picks={"genre_style": "gen_drumstep"},
        layout="stacked-tower",
    ),
    _ex(
        "spare-drum",
        "spare drum",
        165,
        547,
        AFTERPARTY_PHASE,
        "spare-drum brostep warp",
        SPARE_DRUM_LYRICS,
        recipe="rec_drive_brostep",
        picks={"bass_low_end": "bass_pedal_dual"},
        layout="prompt-left",
    ),
    _ex(
        "oil-pan",
        "oil pan",
        150,
        557,
        AFTERPARTY_PHASE,
        "oil-pan color bass warp",
        OIL_PAN_LYRICS,
        recipe="rec_drive_color",
        layout="output-rail",
    ),
    _ex(
        "curb-check",
        "curb check",
        174,
        563,
        AFTERPARTY_PHASE,
        "curb-check drumstep warp",
        CURB_CHECK_LYRICS,
        recipe="rec_drive_drumstep",
        picks={"drums_rhythm": "drm_amen_chop"},
        layout="column",
    ),
    _ex(
        "last-exit",
        "last exit",
        160,
        569,
        AFTERPARTY_PHASE,
        "last-exit dirty bass warp",
        LAST_EXIT_LYRICS,
        recipe="rec_drive_dirty",
        picks={"bass_low_end": "bass_pedal_dual"},
        layout="wide-stage",
    ),
    _ex(
        "asphalt-heart",
        "asphalt heart",
        155,
        571,
        AFTERPARTY_PHASE,
        "asphalt-heart chest bass warp",
        ASPHALT_HEART_LYRICS,
        recipe="rec_drive_chest",
        picks={"bass_low_end": "bass_stacked_808"},
        layout="stacked-tower",
    ),
    _ex(
        "clutch-slam",
        "clutch slam",
        168,
        577,
        AFTERPARTY_PHASE,
        "clutch-slam tearout warp",
        CLUTCH_SLAM_LYRICS,
        recipe="rec_drive_tearout",
        picks={"genre_style": "gen_dirty_dubstep", "bass_low_end": "bass_pedal_dual"},
        layout="prompt-left",
    ),
    _ex(
        "trailer-hitch",
        "trailer hitch",
        165,
        587,
        AFTERPARTY_PHASE,
        "trailer-hitch hybrid trap warp",
        TRAILER_HITCH_LYRICS,
        recipe="rec_drive_through_drop",
        picks={"bass_low_end": "bass_stacked_808"},
        layout="output-rail",
    ),
)

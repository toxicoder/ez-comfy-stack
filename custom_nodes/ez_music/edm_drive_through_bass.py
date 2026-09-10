"""Drive-through 180s rave DJ-set takes (hour 2, bass / feel-good).

Fictional act. Original dance arrangements. No living-artist names.
American festival EDM: drop early, dirty pyro on every drop, all instrumental.
"""

from __future__ import annotations

from .edm_examples import EdmExample, _ex, format_edm_score


RUMBLE_STRIP_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nchest 808 wreck\nDrive-through\nfireworks crash"),
    ("inst", "hats skip\nbass rolls"),
    ("inst", "harder dirty drop\nstacked bass house\nmainstage pyro"),
    ("outro", "filter down\nblend next"),
)

LOW_LANE_LYRICS = format_edm_score(
    ("intro", "filter in\nDrive-through"),
    ("inst", "heavy dirty drop\nchest sub wreck\nfireworks crash"),
    ("inst", "hats skip\nbass cut"),
    ("inst", "harder dirty drop\nrolling 808 wall\nmainstage pyro"),
    ("inst", "full send drop\nwarm sub stack\nfestival pyro"),
    ("outro", "blend next"),
)

WARM_MERGE_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nwarm 808 wreck\nDrive-through\nfireworks crash"),
    ("inst", "chord bed\nhats air"),
    ("inst", "harder dirty drop\nstacked future bass\nmainstage pyro"),
    ("outro", "blend out"),
)

COLOUR_SPAN_LYRICS = format_edm_score(
    ("intro", "arp tease\nDrive-through"),
    ("inst", "heavy dirty drop\ncomplextro wreck\nfireworks crash"),
    ("inst", "harder dirty drop\nanalog 808 stack\nchest pyro"),
    ("inst", "hats only\nair"),
    ("inst", "full send drop\ndirty electro wreck\nmainstage pyro"),
    ("outro", "arp out\nblend next"),
)

GARAGE_TICKET_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\ntrap 808 wreck\nDrive-through\nfireworks crash"),
    ("inst", "hats roll\nbass cut"),
    ("inst", "harder dirty drop\nstacked trap bass\nmainstage pyro"),
    ("inst", "full send drop\nchest 808 wall\nfestival pyro"),
    ("outro", "hats stop\nblend next"),
)

LIQUID_GRADE_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\ndrumstep wreck\nDrive-through\nfireworks crash"),
    ("inst", "amen chops\nair"),
    ("inst", "harder dirty drop\nreese stack\nchest pyro"),
    ("inst", "hats razor\nbass wind"),
    ("inst", "full send drop\nstacked amen wreck\nmainstage pyro"),
    ("inst", "harder dirty drop\n808 punch\nfestival pyro"),
    ("outro", "amen stop\nblend next"),
)

JUMP_BAY_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\ngrowl wreck\nDrive-through\nfireworks crash"),
    ("inst", "hats metal\nbass cut"),
    ("inst", "harder dirty drop\nsub crush\nchest pyro"),
    ("inst", "wobble tease\nspace"),
    ("inst", "full send drop\nbrostep wreck\nmainstage pyro"),
    ("inst", "hats ride\nbass growl"),
    ("inst", "harder dirty drop\nstacked 808 wreck\nfestival pyro"),
    ("outro", "span out\nblend next"),
)

PSY_MEDIAN_LYRICS = format_edm_score(
    ("intro", "mainstage air\nDrive-through"),
    ("inst", "heavy dirty drop\nbig room 808 wreck\nfireworks crash"),
    ("inst", "harder dirty drop\nstacked 808 saw\nmainstage pyro"),
    ("outro", "kick holds\nblend next"),
)

GROOVE_MILE_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nslap bass wreck\nDrive-through\nfireworks crash"),
    ("inst", "hats bounce\nbass cut"),
    ("inst", "harder dirty drop\nstacked 808 bounce\nchest pyro"),
    ("inst", "filter ride\nair"),
    ("inst", "full send drop\nbody bass wreck\nmainstage pyro"),
    ("outro", "blend next"),
)

DONK_RAMP_LYRICS = format_edm_score(
    ("intro", "spark in\nDrive-through"),
    ("inst", "heavy dirty drop\nelectro 808 wreck\nfireworks crash"),
    ("inst", "harder dirty drop\ncomplextro stack\nchest pyro"),
    ("inst", "full send drop\ndirty analog wreck\nmainstage pyro"),
    ("outro", "spark out\nblend next"),
)

BOUNCE_BOOTH_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nbounce bass wreck\nDrive-through\nfireworks crash"),
    ("inst", "hats bounce\nair"),
    ("inst", "harder dirty drop\nstacked bounce 808\nmainstage pyro"),
    ("outro", "booth out\nblend next"),
)

TOLL_GROWL_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\ntearout wreck\nDrive-through\nfireworks crash"),
    ("inst", "hats metal\nbass cut"),
    ("inst", "harder dirty drop\nsub crush\nchest pyro"),
    ("inst", "growl tease\nspace"),
    ("inst", "full send drop\nfour-floor wreck\nmainstage pyro"),
    ("inst", "hats ride\nbass growl"),
    ("inst", "harder dirty drop\nstacked growl wreck\nfestival pyro"),
    ("outro", "toll out\nblend next"),
)

NIGHT_OIL_LYRICS = format_edm_score(
    ("intro", "night oil\nDrive-through"),
    ("inst", "heavy dirty drop\nhybrid 808 wreck\nfireworks crash"),
    ("inst", "hats skip\nbass rolls"),
    ("inst", "harder dirty drop\ntrap bass wall\nmainstage pyro"),
    ("outro", "oil out\nblend next"),
)

CHEST_PASS_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nchest sub wreck\nDrive-through\nfireworks crash"),
    ("inst", "hats only\nair"),
    ("inst", "harder dirty drop\nstacked 808 wall\nmainstage pyro"),
    ("inst", "full send drop\nbody bass wreck\nfestival pyro"),
    ("outro", "pass out\nblend next"),
)

SUNRISE_SUB_LYRICS = format_edm_score(
    ("intro", "sunrise mix-in\nDrive-through"),
    ("inst", "heavy dirty drop\nwarm sub wreck\nfireworks crash"),
    ("inst", "harder dirty drop\nmainstage gold wreck\nchest pyro"),
    ("outro", "blend out\nsky paid"),
)

EDM_DRIVE_THROUGH_BASS: tuple[EdmExample, ...] = (
    _ex(
        "rumble-strip",
        "rumble strip",
        140,
        271,
        1,
        "rumble-strip dirty bass house",
        RUMBLE_STRIP_LYRICS,
        "bass house",
        "four on the floor",
        "dirty 808",
        "chest sub",
        "rave",
        "festival pyro",
    ),
    _ex(
        "low-lane",
        "low lane",
        144,
        277,
        1,
        "low-lane festival 808",
        LOW_LANE_LYRICS,
        "festival bass",
        "four on the floor",
        "chest sub",
        "rolling 808",
        "rave",
        "dirty pyro",
    ),
    _ex(
        "warm-merge",
        "warm merge",
        148,
        281,
        1,
        "warm-merge future bass",
        WARM_MERGE_LYRICS,
        "future bass",
        "four on the floor",
        "warm 808",
        "euphoric",
        "rave",
        "festival pyro",
    ),
    _ex(
        "colour-span",
        "colour span",
        150,
        283,
        1,
        "colour-span complextro",
        COLOUR_SPAN_LYRICS,
        "complextro",
        "electro house",
        "analog bass",
        "dirty 808",
        "rave",
        "festival pyro",
    ),
    _ex(
        "garage-ticket",
        "garage ticket",
        140,
        293,
        1,
        "garage-ticket festival trap",
        GARAGE_TICKET_LYRICS,
        "festival trap",
        "trap 808",
        "dirty bass",
        "four on the floor",
        "rave",
        "festival pyro",
    ),
    _ex(
        "liquid-grade",
        "liquid grade",
        174,
        307,
        1,
        "liquid-grade drumstep",
        LIQUID_GRADE_LYRICS,
        "drumstep",
        "festival",
        "amen break",
        "reese bass",
        "rave",
        "dirty pyro",
    ),
    _ex(
        "jump-bay",
        "jump bay",
        150,
        311,
        1,
        "jump-bay dirty brostep",
        JUMP_BAY_LYRICS,
        "brostep",
        "dirty dubstep",
        "bass growl",
        "heavy sub",
        "rave",
        "festival pyro",
    ),
    _ex(
        "psy-median",
        "psy median",
        145,
        313,
        1,
        "psy-median big room",
        PSY_MEDIAN_LYRICS,
        "big room",
        "festival",
        "four on the floor",
        "supersaw",
        "rave",
        "dirty 808",
    ),
    _ex(
        "groove-mile",
        "groove mile",
        144,
        317,
        1,
        "groove-mile slap house",
        GROOVE_MILE_LYRICS,
        "slap house",
        "four on the floor",
        "bounce bass",
        "dirty 808",
        "rave",
        "festival pyro",
    ),
    _ex(
        "donk-ramp",
        "donk ramp",
        150,
        331,
        1,
        "donk-ramp dirty electro",
        DONK_RAMP_LYRICS,
        "dirty electro",
        "complextro",
        "analog bass",
        "808 punch",
        "rave",
        "festival pyro",
    ),
    _ex(
        "bounce-booth",
        "bounce booth",
        140,
        337,
        1,
        "bounce-booth festival bounce",
        BOUNCE_BOOTH_LYRICS,
        "melbourne bounce",
        "four on the floor",
        "bounce bass",
        "dirty 808",
        "rave",
        "festival pyro",
    ),
    _ex(
        "toll-growl",
        "toll growl",
        150,
        347,
        1,
        "toll-growl dirty tearout",
        TOLL_GROWL_LYRICS,
        "tearout",
        "dirty dubstep",
        "bass growl",
        "heavy sub",
        "rave",
        "festival pyro",
    ),
    _ex(
        "night-oil",
        "night oil",
        142,
        349,
        1,
        "night-oil hybrid trap",
        NIGHT_OIL_LYRICS,
        "hybrid trap",
        "festival trap",
        "trap 808",
        "dirty bass",
        "rave",
        "festival pyro",
    ),
    _ex(
        "chest-pass",
        "chest pass",
        150,
        353,
        1,
        "chest-pass festival bass",
        CHEST_PASS_LYRICS,
        "festival bass",
        "four on the floor",
        "chest sub",
        "dirty 808",
        "rave",
        "festival pyro",
    ),
    _ex(
        "sunrise-sub",
        "sunrise sub",
        140,
        359,
        1,
        "sunrise-sub festival closer",
        SUNRISE_SUB_LYRICS,
        "progressive house",
        "four on the floor",
        "warm sub",
        "rave",
        "festival pyro",
    ),
)

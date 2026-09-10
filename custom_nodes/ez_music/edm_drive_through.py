"""Drive-through 180s rave DJ-set takes (hour 1).

Fictional act. Original dance arrangements. No living-artist names.
American festival EDM: drop early, dirty pyro on every drop, vocals rare.
"""

from __future__ import annotations

from .edm_examples import EdmExample, _ex, format_edm_score


NIGHT_WINDOW_LYRICS = format_edm_score(
    ("intro", "kick in\nDrive-through\nblend open"),
    ("inst", "heavy dirty drop\nfour on the floor\nchest 808 wreck\nfireworks crash"),
    ("inst", "hats skip\nbass cut"),
    ("inst", "harder dirty drop\nstacked rolling bass\nmainstage pyro"),
    ("outro", "filter down\nkick holds\nblend next"),
)

OPEN_LANE_LYRICS = format_edm_score(
    ("inst", "full send drop\nfestival bass in\ndirty 808 pyro"),
    ("inst", "hats only\nbass cut\nair"),
    ("inst", "harder stacked drop\n808 punch\nfireworks wreck"),
    ("outro", "blend out\nDrive-through"),
)

EXIT_SEVEN_LYRICS = format_edm_score(
    ("intro", "filter mix-in\nDrive-through"),
    ("inst", "stacked dirty drop\nanalog bass wreck\nchest pyro"),
    ("inst", "harder dirty drop\n808 wall\nfireworks crash"),
    ("outro", "filter blend\nkick into next"),
)

SKYLINE_PASS_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nDrive-through\nrolling bass wall\nfireworks crash"),
    ("inst", "pads thin\nbass cut"),
    ("inst", "harder dirty drop\nstacked supersaw\nmainstage pyro"),
    ("inst", "hats only\nair"),
    ("inst", "full send drop\nchest 808 wreck\nfestival pyro"),
    ("outro", "gate close\nblend next"),
)

ON_RAMP_LYRICS = format_edm_score(
    ("intro", "reverse swell\nDrive-through"),
    ("inst", "heavy dirty drop\nreverse bass wreck\nfireworks crash"),
    ("inst", "hats iron\nbass cut"),
    ("inst", "harder dirty drop\ndouble 808 split\nmainstage pyro"),
    ("inst", "screech tail\nhats iron"),
    ("inst", "full send drop\nstacked reverse wreck\nchest pyro"),
    ("outro", "kick out\nblend next"),
)

TUNNEL_BASS_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nindustrial bass wreck\nDrive-through\nfireworks crash"),
    ("inst", "harder dirty drop\nstacked 808 wreck\nmainstage pyro"),
    ("inst", "full send drop\nchest sub wreck\nfestival pyro"),
    ("outro", "kick out\nblend next"),
)

WIDE_OPEN_LYRICS = format_edm_score(
    ("intro", "mainstage air\nDrive-through"),
    ("inst", "heavy dirty drop\nstacked 808 wreck\nfireworks crash"),
    ("chorus", "hands up\nDrive-through"),
    ("inst", "harder dirty drop\ndouble saw wreck\nmainstage pyro"),
    ("outro", "kick holds\nblend next"),
)

OVERPASS_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nwobble wreck\nsub crush\nfireworks crash"),
    ("inst", "hats metal\nbass cut"),
    ("inst", "harder dirty drop\nstacked four-floor\nchest pyro"),
    ("inst", "hats ride\nbass growl"),
    ("inst", "full send drop\nmainstage wobble wreck\nfestival pyro"),
    ("outro", "span out\nDrive-through\nblend next"),
)

SECOND_WAVE_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nstacked growl wreck\nDrive-through\nfireworks crash"),
    ("chorus", "one more\nDrive-through"),
    ("inst", "harder double drop\nfull send bass wreck\nmainstage pyro"),
    ("outro", "process out\nblend next"),
)

FREIGHT_PULSE_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\namen wreck\nreese stack\nDrive-through"),
    ("inst", "break chops\nglitch"),
    ("inst", "harder dirty drop\ndouble amen wreck\nfireworks crash"),
    ("inst", "razor hats\nreese wind"),
    ("inst", "full send drop\nstacked amen wreck\nmainstage pyro"),
    ("inst", "harder dirty drop\nchest 808 wreck\nfestival pyro"),
    ("outro", "amen stop\nblend next"),
)

KEEP_GOING_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nstacked 808 wreck\nDrive-through\nfireworks crash"),
    ("inst", "hats only\nair"),
    ("inst", "harder dirty drop\nfull send 170 wreck\nmainstage pyro"),
    ("inst", "riser scream\nhats denser"),
    ("inst", "full send drop\nchest sub wreck\nfestival pyro"),
    ("outro", "still going\nblend next"),
)

HORIZON_KICK_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nkick split wreck\nreverse bass\nfireworks crash"),
    ("inst", "screech wind\nhats razor"),
    ("inst", "harder dirty drop\nstacked reverse wreck\nmainstage pyro"),
    ("outro", "kick rest\nDrive-through\nblend next"),
)

CLEAN_WRECKAGE_LYRICS = format_edm_score(
    ("intro", "bits gather\nDrive-through"),
    ("inst", "heavy dirty drop\nstacked 808 wreck\nfireworks crash"),
    ("inst", "harder dirty drop\nlead and kick stack\nchest pyro"),
    ("inst", "full send drop\nmainstage crash\nfestival pyro"),
    ("outro", "dust rest\nblend next"),
)

HEART_LANE_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nwarm 808 wreck\nDrive-through\nfireworks crash"),
    ("inst", "groove returns\npads thin"),
    ("inst", "harder dirty drop\nfull send kick wreck\nchest pyro"),
    ("inst", "full send drop\nstacked rolling bass\nmainstage pyro"),
    ("outro", "kick rest\nblend next"),
)

DAWN_RECEIPT_LYRICS = format_edm_score(
    ("intro", "sunrise mix-in\nDrive-through"),
    ("inst", "heavy dirty drop\nwarm bass wreck\nfireworks crash"),
    ("inst", "harder dirty drop\nmainstage gold wreck\nchest pyro"),
    ("outro", "blend out\nsky paid"),
)

EDM_DRIVE_THROUGH: tuple[EdmExample, ...] = (
    _ex(
        "night-window",
        "night window",
        145,
        193,
        0,
        "night-window dirty bass house",
        NIGHT_WINDOW_LYRICS,
        "bass house",
        "four on the floor",
        "rolling bass",
        "dirty 808",
        "rave",
        "festival pyro",
    ),
    _ex(
        "open-lane",
        "open lane",
        152,
        191,
        0,
        "open-lane festival bass",
        OPEN_LANE_LYRICS,
        "festival bass",
        "four on the floor",
        "supersaw",
        "stacked 808",
        "rave",
        "dirty drop",
    ),
    _ex(
        "exit-seven",
        "exit seven",
        142,
        233,
        0,
        "exit-seven electro house",
        EXIT_SEVEN_LYRICS,
        "electro house",
        "four on the floor",
        "analog bass",
        "dirty 808",
        "rave",
        "festival pyro",
    ),
    _ex(
        "skyline-pass",
        "skyline pass",
        145,
        199,
        0,
        "skyline-pass festival anthem",
        SKYLINE_PASS_LYRICS,
        "progressive house",
        "four on the floor",
        "festival anthem",
        "rolling bass",
        "rave",
        "supersaw",
    ),
    _ex(
        "on-ramp",
        "on-ramp",
        155,
        197,
        0,
        "on-ramp dirty festival bass",
        ON_RAMP_LYRICS,
        "festival bass",
        "dirty electro",
        "reverse bass",
        "808 punch",
        "rave",
        "heavy drop",
    ),
    _ex(
        "tunnel-bass",
        "tunnel bass",
        150,
        257,
        0,
        "tunnel-bass dirty festival bass",
        TUNNEL_BASS_LYRICS,
        "dirty bass",
        "four on the floor",
        "industrial bass",
        "festival pyro",
        "rave",
        "heavy kick",
    ),
    _ex(
        "wide-open",
        "wide open",
        150,
        239,
        0,
        "wide-open big room DJ shout",
        WIDE_OPEN_LYRICS,
        "big room",
        "festival",
        "four on the floor",
        "stacked 808",
        "rave",
        "dirty pyro",
        treat=True,
    ),
    _ex(
        "overpass",
        "overpass",
        150,
        227,
        0,
        "overpass dirty riddim switch",
        OVERPASS_LYRICS,
        "riddim",
        "rave bass",
        "four on the floor",
        "wobble bass",
        "dirty dubstep",
        "heavy sub",
    ),
    _ex(
        "second-wave",
        "second wave",
        150,
        241,
        0,
        "second-wave festival remix",
        SECOND_WAVE_LYRICS,
        "festival remix",
        "rave",
        "bass growl",
        "dirty 808",
        "heavy drop",
        treat=True,
    ),
    _ex(
        "freight-pulse",
        "freight pulse",
        176,
        211,
        0,
        "freight-pulse drumstep",
        FREIGHT_PULSE_LYRICS,
        "drumstep",
        "festival",
        "amen break",
        "reese bass",
        "rave",
        "dirty bass",
    ),
    _ex(
        "keep-going",
        "keep going",
        170,
        251,
        0,
        "keep-going drumstep peak",
        KEEP_GOING_LYRICS,
        "drumstep",
        "festival",
        "four on the floor",
        "heavy sub",
        "rave",
        "dirty pyro",
    ),
    _ex(
        "horizon-kick",
        "horizon kick",
        165,
        263,
        0,
        "horizon-kick dirty reverse bass",
        HORIZON_KICK_LYRICS,
        "festival bass",
        "dirty electro",
        "reverse bass",
        "808 punch",
        "rave",
        "heavy drop",
    ),
    _ex(
        "clean-wreckage",
        "clean wreckage",
        150,
        269,
        0,
        "clean-wreckage dirty electro",
        CLEAN_WRECKAGE_LYRICS,
        "dirty electro",
        "four on the floor",
        "complextro",
        "rave",
        "heavy sub",
    ),
    _ex(
        "heart-lane",
        "heart lane",
        145,
        223,
        0,
        "heart-lane future bass",
        HEART_LANE_LYRICS,
        "future bass",
        "four on the floor",
        "warm 808",
        "rave",
        "festival",
    ),
    _ex(
        "dawn-receipt",
        "dawn receipt",
        140,
        229,
        0,
        "dawn-receipt festival closer",
        DAWN_RECEIPT_LYRICS,
        "progressive house",
        "four on the floor",
        "warm bass",
        "rave",
        "festival pyro",
    ),
)

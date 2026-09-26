"""Drive-through full-length bass-set takes (hour 1).

Fictional act. Original dance arrangements. No living-artist names.
Warped hybrid-trap EDM: drop first, hard warpy drops, trap drums, no quiet
dips, vocals rare.
"""

from __future__ import annotations

from .edm_examples import EdmExample, _ex, format_edm_score

# Track scores and catalog rows.
NIGHT_WINDOW_LYRICS = format_edm_score(
    ("inst", "heavy warped drop\nhybrid trap 808 wreck\nchest-sub grind"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder warped drop\nchest sub warp\nstacked reese"),
    ("inst", "kick tightens\nchest 808 punch"),
    ("inst", "full send drop\nwarped 808 wall\nlow rumble wreck"),
    ("outro", "kick holds\ntrap hats roll\nwarp bass ride"),
)

OPEN_LANE_LYRICS = format_edm_score(
    ("inst", "full send drop\nriddim wobble wreck\nsub crush"),
    ("inst", "harder stacked drop\nwobble 808 punch\nwarped wall"),
    ("inst", "trap hats denser\nwobble sustain"),
    ("inst", "heavy warped drop\nlow sub wobble\nchest 808 wreck"),
    ("outro", "kick holds\nhats denser\nwobble ride"),
)

EXIT_SEVEN_LYRICS = format_edm_score(
    ("inst", "heavy tearout drop\ngrowl wreck\nchest-sub"),
    ("inst", "rapid hi-hats roll\n808 grind hold"),
    ("inst", "harder warped drop\nsub crush 808\nchest growl"),
    ("inst", "kick tightens\ntearout 808 sustain"),
    ("inst", "full send drop\nstacked growl wreck\nlow rumble"),
    ("inst", "trap hats denser\nchest-sub hold"),
    ("inst", "harder growl drop\nchest 808 warp\ntearout wreck"),
    ("outro", "kick holds\ntrap hats roll\ngrowl ride"),
)

SKYLINE_PASS_LYRICS = format_edm_score(
    ("inst", "heavy brostep drop\nchest-sub wreck\nwarped 808"),
    ("inst", "trap hats roll\ngrowl sustain"),
    ("inst", "harder reese drop\nstacked 808 wall\nchest-sub bend"),
    ("inst", "full send drop\nchest sub growl\nbrostep wreck"),
    ("inst", "kick tightens\nreese hold"),
    ("inst", "harder warped drop\nlow rumble wreck\n808 punch"),
    ("outro", "kick holds\nhats denser\nreese ride"),
)

ON_RAMP_LYRICS = format_edm_score(
    ("inst", "heavy wave drop\nwarped 808 wreck\nwavy low-mid line"),
    ("inst", "trap hats roll\nwave 808 sustain"),
    ("inst", "harder chest-sub drop\ndouble 808 split\nchest warp"),
    ("inst", "kick tightens\n808 slide"),
    ("inst", "full send drop\nstacked wave wreck\nwarped sub"),
    ("outro", "kick holds\ntrap hats roll\nwave ride"),
)

TUNNEL_BASS_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nindustrial 808 warp\nchest-sub wreck"),
    ("inst", "harder warped drop\ndual-action pedal bass\nchest punch"),
    ("inst", "trap hats roll\npedal 808 hold"),
    ("inst", "full send drop\nchest sub wreck\nwarped rumble"),
    ("outro", "kick holds\nhats denser\npedal ride"),
)

WIDE_OPEN_LYRICS = format_edm_score(
    ("inst", "heavy color drop\nwarped 808 wreck\nchest-sub stack"),
    ("inst", "harder warped drop\nchest sub warp\ncolor bass wreck"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "full send drop\nlow 808 wall\nwarped color"),
    ("outro", "kick holds\ntrap hats roll\ncolor ride"),
)

OVERPASS_LYRICS = format_edm_score(
    ("inst", "heavy wobble drop\ndirty dubstep wreck\nsub crush"),
    ("inst", "rapid hi-hats roll\nwobble sustain"),
    ("inst", "harder wobble drop\nstacked 808 warp\nchest rumble"),
    ("inst", "trap hats denser\n808 punch hold"),
    ("inst", "full send drop\nwarped wobble wreck\nlow sub"),
    ("inst", "kick tightens\nwarped hold"),
    ("inst", "harder warped drop\nchest 808 wreck\ndubstep grind"),
    ("outro", "kick holds\nhats denser\nwobble ride"),
)

SECOND_WAVE_LYRICS = format_edm_score(
    ("inst", "heavy warped drop\nhybrid trap warped wreck\n808 stack"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder double drop\nfull send bass warp\nchest-sub wreck"),
    ("inst", "full send drop\nchest 808 wreck\nwarped trap"),
    ("outro", "kick holds\ntrap hats roll\nwarped ride"),
)

FREIGHT_PULSE_LYRICS = format_edm_score(
    ("inst", "heavy amen drop\nreese stack wreck\nwarped 808"),
    ("inst", "amen chops\ntrap hats 808 freight"),
    ("inst", "harder warped drop\ndouble amen wreck\nchest-sub grind"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "full send drop\nstacked amen wreck\nwarped chest sub"),
    ("inst", "kick tightens\n808 punch"),
    ("inst", "harder warped drop\nchest 808 wreck\nreese wall"),
    ("outro", "kick holds\namen keep\nreese ride"),
)

KEEP_GOING_LYRICS = format_edm_score(
    ("inst", "heavy neuro drop\nreese 808 wreck\nwarped coil"),
    ("inst", "trap hats denser\nreese sustain"),
    ("inst", "harder warped drop\nfull send 170 wreck\nchest sub"),
    ("inst", "kick tightens\n808 slide"),
    ("inst", "full send drop\nchest sub wreck\nneuro warp"),
    ("outro", "kick holds\nhats denser\nreese ride"),
)

HORIZON_KICK_LYRICS = format_edm_score(
    ("inst", "heavy tearout drop\nkick split wreck\nwarped growl"),
    ("inst", "trap hats roll\ngrowl sustain"),
    ("inst", "harder stacked drop\nwarped reverse wreck\nchest 808"),
    ("inst", "808 triplets\nhats denser"),
    ("inst", "full send drop\nchest sub wreck\ntearout warp"),
    ("inst", "harder growl drop\nlow rumble wreck\n808 punch"),
    ("outro", "kick holds\ntrap hats roll\ngrowl ride"),
)

CLEAN_WRECKAGE_LYRICS = format_edm_score(
    ("inst", "heavy brostep drop\nstacked 808 warp\ngrowl wreck"),
    ("inst", "harder reese drop\nkick stack wreck\nchest-sub"),
    ("inst", "trap hats roll\n808 punch hold"),
    ("inst", "full send drop\nchest-sub crash\nwarped wall"),
    ("outro", "kick holds\nhats denser\nbrostep ride"),
)

HEART_LANE_LYRICS = format_edm_score(
    ("inst", "heavy wave drop\nchest 808 warp\nfold wreck"),
    ("inst", "trap hats roll\nwave 808 sustain lane"),
    ("inst", "harder warped drop\nfull send kick wreck\n808 slide"),
    ("inst", "kick tightens\nchest 808"),
    ("inst", "full send drop\nstacked wave bass\nwarped rumble"),
    ("outro", "kick holds\ntrap hats roll\nwave ride"),
)

DAWN_RECEIPT_LYRICS = format_edm_score(
    ("inst", "heavy chest drop\nwarped 808 wreck\nsub grind"),
    ("inst", "trap hats denser\n808 hold"),
    ("inst", "harder warped drop\nchest wall wreck\nchest-sub punch"),
    ("inst", "full send drop\nlow sub wreck\nwarped 808"),
    ("outro", "kick holds\nhats denser\nchest ride"),
)

EDM_DRIVE_THROUGH: tuple[EdmExample, ...] = (
    _ex(
        "night-window",
        "night window",
        145,
        193,
        0,
        "night-window hybrid trap warp",
        NIGHT_WINDOW_LYRICS,
        recipe="rec_drive_through_drop",
    ),
    _ex(
        "open-lane",
        "open lane",
        152,
        191,
        0,
        "open-lane riddim warp",
        OPEN_LANE_LYRICS,
        recipe="rec_drive_riddim",
    ),
    _ex(
        "exit-seven",
        "exit seven",
        142,
        233,
        0,
        "exit-seven tearout warp",
        EXIT_SEVEN_LYRICS,
        recipe="rec_drive_tearout",
    ),
    _ex(
        "skyline-pass",
        "skyline pass",
        145,
        199,
        0,
        "skyline-pass brostep warp",
        SKYLINE_PASS_LYRICS,
        recipe="rec_drive_brostep",
        picks={"bass_low_end": "bass_reese"},
    ),
    _ex(
        "on-ramp",
        "on-ramp",
        155,
        197,
        0,
        "on-ramp wave bass warp",
        ON_RAMP_LYRICS,
        recipe="rec_drive_wave",
    ),
    _ex(
        "tunnel-bass",
        "tunnel bass",
        150,
        257,
        0,
        "tunnel-bass dirty warp",
        TUNNEL_BASS_LYRICS,
        recipe="rec_drive_dirty",
        picks={"bass_low_end": "bass_pedal_dual"},
    ),
    _ex(
        "wide-open",
        "wide open",
        150,
        239,
        0,
        "wide-open color bass",
        WIDE_OPEN_LYRICS,
        recipe="rec_drive_color",
        picks={"bass_low_end": "bass_stacked_808"},
    ),
    _ex(
        "overpass",
        "overpass",
        150,
        227,
        0,
        "overpass dirty dubstep warp",
        OVERPASS_LYRICS,
        recipe="rec_drive_dirty_dubstep",
    ),
    _ex(
        "second-wave",
        "second wave",
        150,
        241,
        0,
        "second-wave hybrid trap",
        SECOND_WAVE_LYRICS,
        recipe="rec_drive_through_drop",
    ),
    _ex(
        "freight-pulse",
        "freight pulse",
        176,
        211,
        0,
        "freight-pulse drumstep warp",
        FREIGHT_PULSE_LYRICS,
        recipe="rec_drive_drumstep",
    ),
    _ex(
        "keep-going",
        "keep going",
        170,
        251,
        0,
        "keep-going neuro warp",
        KEEP_GOING_LYRICS,
        recipe="rec_drive_neuro",
    ),
    _ex(
        "horizon-kick",
        "horizon kick",
        165,
        263,
        0,
        "horizon-kick tearout warp",
        HORIZON_KICK_LYRICS,
        recipe="rec_drive_tearout",
        picks={"sound_design_fx": "sfx_kick_split"},
    ),
    _ex(
        "clean-wreckage",
        "clean wreckage",
        150,
        269,
        0,
        "clean-wreckage brostep warp",
        CLEAN_WRECKAGE_LYRICS,
        recipe="rec_drive_brostep",
        picks={"bass_low_end": "bass_chest_sub"},
    ),
    _ex(
        "heart-lane",
        "heart lane",
        145,
        223,
        0,
        "heart-lane wave bass warp",
        HEART_LANE_LYRICS,
        recipe="rec_drive_wave",
        picks={"bass_low_end": "bass_chest_sub"},
    ),
    _ex(
        "dawn-receipt",
        "dawn receipt",
        140,
        229,
        0,
        "dawn-receipt chest bass warp",
        DAWN_RECEIPT_LYRICS,
        recipe="rec_drive_chest",
    ),
)

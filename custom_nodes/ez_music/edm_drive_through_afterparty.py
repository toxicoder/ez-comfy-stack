"""Drive-through full-length bass-set takes (hour 4, afterparty).

Fictional act. Original dance arrangements. No living-artist names.
Warped hybrid-trap EDM: drop first, hard warpy drops, trap drums, dual-action
pedal bass on some takes, all instrumental.
"""

from __future__ import annotations

from .edm_album import (
    AFTERPARTY_PHASE,
    DriveRowSpec,
    build_album,
    layout_cycle,
)
from .edm_examples import EdmExampleRow, _ex, format_edm_score

# Track scores for this live-set hour.

BRAKE_FADE_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nchest 808 warp\nbrake wreck"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder warped drop\nstacked 808 wall\nchest-sub grind"),
    ("inst", "kick tightens\nchest 808 punch"),
    ("inst", "full send drop\nlow rumble wreck\nwarped dirty"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)

DIESEL_HUM_LYRICS = format_edm_score(
    ("inst", "heavy warped drop\ndual-action pedal bass\nchest 808 wreck"),
    ("inst", "pedal 808 hold\ntrap hats roll"),
    ("inst", "harder warped drop\nrolling 808 wall\nhybrid chest-sub"),
    ("inst", "full send drop\nchest sub wreck\npedal warp"),
    ("outro", "kick holds\nhats denser\npedal ride"),
)

AXLE_GRIND_LYRICS = format_edm_score(
    ("inst", "heavy tearout drop\ngrowl wreck\nwarped axle"),
    ("inst", "rapid hi-hats roll\ngrowl sustain"),
    ("inst", "harder warped drop\nsub crush\nchest 808"),
    ("inst", "trap hats denser\ngrowl hold"),
    ("inst", "full send drop\nstacked growl wreck\ntearout warp"),
    ("inst", "harder growl drop\nlow 808 wreck\naxle grind"),
    ("outro", "kick holds\nhats denser\ngrowl ride"),
)

WEIGH_STATION_LYRICS = format_edm_score(
    ("inst", "heavy brostep drop\nstacked 808 warp\nweigh wreck"),
    ("inst", "trap hats roll\ngrowl hold"),
    ("inst", "harder growl drop\nchest sub wall\nchest-sub 808"),
    ("inst", "kick tightens\n808 punch"),
    ("inst", "full send drop\nbody bass wreck\nwarped brostep"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)

BLACK_ICE_LYRICS = format_edm_score(
    ("inst", "heavy riddim drop\nwobble wreck\nwarped ice"),
    ("inst", "rapid hi-hats roll\nwobble sustain"),
    ("inst", "harder warped drop\nchest warped wreck\n808 crush"),
    ("inst", "trap hats denser\nwobble hold"),
    ("inst", "full send drop\nsub crush wreck\nchest warped"),
    ("inst", "kick tightens\nbass warped hold"),
    ("inst", "harder warped drop\nlow rumble wreck\nriddim 808"),
    ("outro", "kick holds\nhats denser\nwobble ride"),
)

HIGH_BEAMS_LYRICS = format_edm_score(
    ("inst", "heavy color drop\ndual-action pedal bass\nchest 808 warp"),
    ("inst", "pedal 808 hold\ntrap hats roll"),
    ("inst", "harder stacked drop\nhybrid 808 wall\ncolor warped"),
    ("inst", "kick tightens\nchest 808"),
    ("inst", "full send drop\nbody sub wreck\nwarped color"),
    ("inst", "harder warped drop\nstacked 808 wreck\npedal warp"),
    ("outro", "kick holds\nhats denser\ncolor ride"),
)

CHAIN_HOOK_LYRICS = format_edm_score(
    ("inst", "heavy brostep drop\ngrowl wreck\nwarped chain"),
    ("inst", "harder dirty drop\ndubstep wreck\nchest 808 warped"),
    ("inst", "full send drop\nstacked 808 wreck\ntrap growl"),
    ("outro", "kick holds\ntrap hats roll\ngrowl ride"),
)

GRIT_PLATE_LYRICS = format_edm_score(
    ("inst", "heavy wave drop\nwarped 808 wreck\ngrit fold"),
    ("inst", "trap hats denser\nwave 808 hold grit"),
    ("inst", "harder warped drop\nstacked 808 wall\nchest-sub"),
    ("inst", "full send drop\nbody bass wreck\nwave warp"),
    ("outro", "kick holds\nhats denser\nwave ride"),
)

STEEL_GRATE_LYRICS = format_edm_score(
    ("inst", "heavy amen drop\nreese wreck\nwarped grate"),
    ("inst", "amen chops\ntrap hats 808 grate"),
    ("inst", "harder reese drop\nreese stack\nchest 808"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "full send drop\nstacked amen wreck\nwarped 808"),
    ("inst", "kick tightens\nchest 808 punch"),
    ("inst", "harder warped drop\nchest 808 wreck\ndrumstep grind"),
    ("inst", "full send drop\nlow rumble wreck\nreese wall"),
    ("outro", "kick holds\namen keep\nreese ride"),
)

REST_BAY_LYRICS = format_edm_score(
    ("inst", "heavy chest drop\ndual-action pedal bass\nsub warp wreck"),
    ("inst", "pedal 808 hold\ntrap hats roll"),
    ("inst", "harder warped drop\nstacked 808 wall\nchest-sub"),
    ("inst", "kick tightens\nchest 808"),
    ("inst", "full send drop\nbody chest wreck\npedal warp"),
    ("inst", "harder stacked drop\nlow 808 wreck\ntrap warped"),
    ("outro", "kick holds\nhats denser\npedal ride"),
)

HAUL_CRATE_LYRICS = format_edm_score(
    ("inst", "heavy hybrid drop\ntrap 808 wreck\nwarped crate"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder warped drop\nstacked trap bass\nchest-sub"),
    ("inst", "kick tightens\nchest 808 punch"),
    ("inst", "full send drop\nchest 808 wall\nhybrid warp"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)

NIGHT_SPLICE_LYRICS = format_edm_score(
    ("inst", "heavy wave drop\nwarped bass wreck\nsplice 808"),
    ("inst", "trap hats denser\nwave 808 sustain splice"),
    ("inst", "harder warped drop\nchest 808 wall\nchest-sub fold"),
    ("inst", "full send drop\nlow swell wreck\nwave warp"),
    ("outro", "kick holds\nhats denser\nwave ride"),
)

TORQUE_BAY_LYRICS = format_edm_score(
    ("inst", "heavy neuro drop\nreese 808 wreck\nwarped torque"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "harder stacked drop\nchest reese wreck\nchest-sub coil"),
    ("inst", "trap hats roll\n808 punch"),
    ("inst", "full send drop\nneuro 808 wreck\nchest warp"),
    ("inst", "harder growl drop\nstacked reese wreck\ntorque grind"),
    ("outro", "kick holds\ntrap hats roll\nreese ride"),
)

SPARE_DRUM_LYRICS = format_edm_score(
    ("inst", "heavy brostep drop\ndual-action pedal bass\nchest 808 warp"),
    ("inst", "pedal 808 hold\ntrap hats roll"),
    ("inst", "harder stacked drop\n808 wall wreck\nchest-sub growl"),
    ("inst", "kick tightens\nchest 808"),
    ("inst", "full send drop\nbody bass wreck\npedal warp"),
    ("outro", "kick holds\nhats denser\nbrostep ride"),
)

OIL_PAN_LYRICS = format_edm_score(
    ("inst", "heavy color drop\nwarped 808 wreck\npan grind"),
    ("inst", "trap hats roll\n808 punch hold"),
    ("inst", "harder warped drop\nstacked color 808\nchest-sub"),
    ("inst", "kick tightens\nchest 808"),
    ("inst", "full send drop\nbody bass wreck\ncolor warp"),
    ("inst", "harder stacked drop\nchest sub wreck\nwarped 808 wall"),
    ("outro", "kick holds\nhats denser\ncolor ride"),
)

CURB_CHECK_LYRICS = format_edm_score(
    ("inst", "heavy amen drop\n808 warp wreck\ncurb grind"),
    ("inst", "amen chops\ntrap hats 808 curb"),
    ("inst", "harder stacked drop\nreese 808 wreck\nchest-sub"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "full send drop\nstacked amen wreck\nwarped 808"),
    ("inst", "kick tightens\ncurb 808 punch"),
    ("inst", "harder warped drop\nchest trap wreck\ndrumstep grind"),
    ("outro", "kick holds\namen keep\nreese ride"),
)

LAST_EXIT_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\ndual-action pedal bass\nwarped exit"),
    ("inst", "pedal 808 hold\ntrap hats roll"),
    ("inst", "harder warped drop\nchest 808 wall\nchest-sub crush"),
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
    ("inst", "rapid hi-hats roll\ngrowl sustain"),
    ("inst", "harder warped drop\nsub crush\nchest 808"),
    ("inst", "pedal 808 hold\ntrap hats roll"),
    ("inst", "full send drop\nstacked growl wreck\nwarped clutch"),
    ("inst", "kick tightens\n808 punch"),
    ("inst", "harder stacked drop\nchest 808 wreck\ntearout warp"),
    ("inst", "full send drop\nlow rumble wreck\npedal growl"),
    ("outro", "kick holds\nhats denser\ngrowl ride"),
)

TRAILER_HITCH_LYRICS = format_edm_score(
    ("inst", "heavy warped drop\nchest 808 wreck\nhitch grind"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder stacked drop\nrolling 808 wall\nhybrid warped"),
    ("inst", "kick tightens\nchest 808 punch"),
    ("inst", "full send drop\nbody bass wreck\ntrap warp"),
    ("inst", "harder warped drop\nstacked 808 wreck\nchest-sub"),
    ("inst", "full send drop\nchest sub wreck\nwarped hitch"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)

# Authored takes: one row per track, in track order.
_TAKES: tuple[DriveRowSpec, ...] = (
    {
        "slug": "brake-fade",
        "bpm": 150,
        "seed": 457,
        "take": "brake-fade dirty bass warp",
        "lyrics": BRAKE_FADE_LYRICS,
        "recipe": "rec_drive_dirty",
        "picks": {"bass_low_end": "bass_stacked_808"},
    },
    {
        "slug": "diesel-hum",
        "bpm": 152,
        "seed": 461,
        "take": "diesel-hum hybrid trap warp",
        "lyrics": DIESEL_HUM_LYRICS,
        "recipe": "rec_drive_through_drop",
        "picks": {"bass_low_end": "bass_pedal_dual"},
    },
    {
        "slug": "axle-grind",
        "bpm": 155,
        "seed": 463,
        "take": "axle-grind tearout warp",
        "lyrics": AXLE_GRIND_LYRICS,
        "recipe": "rec_drive_tearout",
    },
    {
        "slug": "weigh-station",
        "bpm": 158,
        "seed": 467,
        "take": "weigh-station brostep warp",
        "lyrics": WEIGH_STATION_LYRICS,
        "recipe": "rec_drive_brostep",
        "picks": {"bass_low_end": "bass_stacked_808"},
    },
    {
        "slug": "black-ice",
        "bpm": 160,
        "seed": 479,
        "take": "black-ice riddim warp",
        "lyrics": BLACK_ICE_LYRICS,
        "recipe": "rec_drive_riddim",
    },
    {
        "slug": "high-beams",
        "bpm": 165,
        "seed": 487,
        "take": "high-beams color bass warp",
        "lyrics": HIGH_BEAMS_LYRICS,
        "recipe": "rec_drive_color",
        "picks": {"bass_low_end": "bass_pedal_dual"},
    },
    {
        "slug": "chain-hook",
        "bpm": 168,
        "seed": 491,
        "take": "chain-hook dirty dubstep warp",
        "lyrics": CHAIN_HOOK_LYRICS,
        "recipe": "rec_drive_brostep",
        "picks": {"genre_style": "gen_dirty_dubstep"},
    },
    {
        "slug": "grit-plate",
        "bpm": 150,
        "seed": 499,
        "take": "grit-plate wave bass warp",
        "lyrics": GRIT_PLATE_LYRICS,
        "recipe": "rec_drive_wave",
    },
    {
        "slug": "steel-grate",
        "bpm": 172,
        "seed": 503,
        "take": "steel-grate drumstep warp",
        "lyrics": STEEL_GRATE_LYRICS,
        "recipe": "rec_drive_drumstep",
        "picks": {"drums_rhythm": "drm_amen_chop"},
    },
    {
        "slug": "rest-bay",
        "bpm": 155,
        "seed": 509,
        "take": "rest-bay chest bass warp",
        "lyrics": REST_BAY_LYRICS,
        "recipe": "rec_drive_chest",
        "picks": {"bass_low_end": "bass_pedal_dual"},
    },
    {
        "slug": "haul-crate",
        "bpm": 170,
        "seed": 521,
        "take": "haul-crate hybrid trap warp",
        "lyrics": HAUL_CRATE_LYRICS,
        "recipe": "rec_drive_through_drop",
        "picks": {"genre_style": "gen_dirty_bass"},
    },
    {
        "slug": "night-splice",
        "bpm": 152,
        "seed": 523,
        "take": "night-splice wave bass warp",
        "lyrics": NIGHT_SPLICE_LYRICS,
        "recipe": "rec_drive_wave",
    },
    {
        "slug": "torque-bay",
        "bpm": 176,
        "seed": 541,
        "take": "torque-bay neuro bass warp",
        "lyrics": TORQUE_BAY_LYRICS,
        "recipe": "rec_drive_neuro",
        "picks": {"genre_style": "gen_drumstep"},
    },
    {
        "slug": "spare-drum",
        "bpm": 165,
        "seed": 547,
        "take": "spare-drum brostep warp",
        "lyrics": SPARE_DRUM_LYRICS,
        "recipe": "rec_drive_brostep",
        "picks": {"bass_low_end": "bass_pedal_dual"},
    },
    {
        "slug": "oil-pan",
        "bpm": 150,
        "seed": 557,
        "take": "oil-pan color bass warp",
        "lyrics": OIL_PAN_LYRICS,
        "recipe": "rec_drive_color",
    },
    {
        "slug": "curb-check",
        "bpm": 174,
        "seed": 563,
        "take": "curb-check drumstep warp",
        "lyrics": CURB_CHECK_LYRICS,
        "recipe": "rec_drive_drumstep",
        "picks": {"drums_rhythm": "drm_amen_chop"},
    },
    {
        "slug": "last-exit",
        "bpm": 160,
        "seed": 569,
        "take": "last-exit dirty bass warp",
        "lyrics": LAST_EXIT_LYRICS,
        "recipe": "rec_drive_dirty",
        "picks": {"bass_low_end": "bass_pedal_dual"},
    },
    {
        "slug": "asphalt-heart",
        "bpm": 155,
        "seed": 571,
        "take": "asphalt-heart chest bass warp",
        "lyrics": ASPHALT_HEART_LYRICS,
        "recipe": "rec_drive_chest",
        "picks": {"bass_low_end": "bass_stacked_808"},
    },
    {
        "slug": "clutch-slam",
        "bpm": 168,
        "seed": 577,
        "take": "clutch-slam tearout warp",
        "lyrics": CLUTCH_SLAM_LYRICS,
        "recipe": "rec_drive_tearout",
        "picks": {"genre_style": "gen_dirty_dubstep", "bass_low_end": "bass_pedal_dual"},
    },
    {
        "slug": "trailer-hitch",
        "bpm": 165,
        "seed": 587,
        "take": "trailer-hitch hybrid trap warp",
        "lyrics": TRAILER_HITCH_LYRICS,
        "recipe": "rec_drive_through_drop",
        "picks": {"bass_low_end": "bass_stacked_808"},
    },
)

# Catalog rows. Finalized when the catalog assembles.
EDM_DRIVE_THROUGH_AFTERPARTY: tuple[EdmExampleRow, ...] = build_album(
    _TAKES,
    phase=AFTERPARTY_PHASE,
    row_for=_ex,
    layouts=layout_cycle(len(_TAKES), offset=0),
)

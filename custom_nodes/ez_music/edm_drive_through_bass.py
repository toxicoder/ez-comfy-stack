"""Drive-through full-length bass-set takes (hour 2).

Fictional act. Original dance arrangements. No living-artist names.
Warped hybrid-trap EDM: drop first, hard warpy drops, trap drums, no quiet
dips, all instrumental.
"""

from __future__ import annotations

from .edm_album import (
    BASS_PHASE,
    DriveRowSpec,
    build_album,
)
from .edm_examples import EdmExampleRow, _ex, format_edm_score

# Track scores for this live-set hour.

RUMBLE_STRIP_LYRICS = format_edm_score(
    ("inst", "heavy warped drop\nhybrid trap 808 wreck\nrumble grind"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder warped drop\ndual-action pedal bass\nstacked warp"),
    ("inst", "pedal 808 hold\nhats denser"),
    ("inst", "full send drop\nlow rumble wreck\nchest warped"),
    ("outro", "kick holds\ntrap hats roll\npedal ride"),
)

LOW_LANE_LYRICS = format_edm_score(
    ("inst", "heavy riddim drop\nchest sub wobble\nwarped wreck"),
    ("inst", "harder warped drop\nrolling 808 wall\nchest-sub crush"),
    ("inst", "trap hats denser\nwobble sustain"),
    ("inst", "kick tightens\nchest 808"),
    ("inst", "808 triplets\nriddim warped hold"),
    ("inst", "full send drop\nwarped sub stack\nriddim wreck"),
    ("outro", "kick holds\nhats denser\nwobble ride"),
)

WARM_MERGE_LYRICS = format_edm_score(
    ("inst", "heavy wave drop\nwarped 808 wreck\nfold grind"),
    ("inst", "trap hats roll\nwave 808 hold merge"),
    ("inst", "harder warped drop\nstacked wave bass\nchest 808"),
    ("inst", "kick tightens\n808 slide"),
    ("inst", "full send drop\nlow 808 wall\nwarped fold"),
    ("outro", "kick holds\ntrap hats roll\nwave ride"),
)

COLOUR_SPAN_LYRICS = format_edm_score(
    ("inst", "heavy color drop\nchest 808 warp\nchest-sub wreck"),
    ("inst", "harder warped drop\nanalog 808 stack\nwarped color"),
    ("inst", "trap hats denser\ncolor 808 sustain span"),
    ("inst", "full send drop\nstacked color wreck\nwarped sub"),
    ("outro", "kick holds\nhats denser\ncolor ride"),
)

GARAGE_TICKET_LYRICS = format_edm_score(
    ("inst", "heavy trap drop\nwarped 808 wreck\nchest-sub stamp"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder warped drop\nstacked trap bass\nchest warp"),
    ("inst", "kick tightens\nchest 808 punch"),
    ("inst", "full send drop\nchest 808 wall\nwarped trap"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)

LIQUID_GRADE_LYRICS = format_edm_score(
    ("inst", "heavy drumstep drop\nreese wreck\nwarped amen"),
    ("inst", "amen chops\ntrap hats 808 liquid"),
    ("inst", "harder reese drop\nreese stack\nchest-sub"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "full send drop\nstacked amen wreck\nwarped 808 punch"),
    ("inst", "harder warped drop\nchest 808 wreck\ndrumstep grind"),
    ("outro", "kick holds\namen keep\nreese ride"),
)

JUMP_BAY_LYRICS = format_edm_score(
    ("inst", "heavy brostep drop\ngrowl wreck\nwarped 808"),
    ("inst", "rapid hi-hats roll\ngrowl sustain"),
    ("inst", "harder warped drop\nsub crush\nchest 808"),
    ("inst", "trap hats denser\nwobble hold"),
    ("inst", "full send drop\nbrostep wreck\nstacked growl"),
    ("inst", "kick tightens\nbass growl hold"),
    ("inst", "harder warped drop\nstacked 808 wreck\nchest-sub"),
    ("outro", "kick holds\nhats denser\ngrowl ride"),
)

PSY_MEDIAN_LYRICS = format_edm_score(
    ("inst", "heavy neuro drop\nreese 808 wreck\nwarped coil"),
    ("inst", "trap hats roll\nreese sustain"),
    ("inst", "harder stacked drop\nwarped 808 wall\nchest sub"),
    ("inst", "full send drop\nchest sub wreck\nneuro warp"),
    ("outro", "kick holds\ntrap hats roll\nreese ride"),
)

GROOVE_MILE_LYRICS = format_edm_score(
    ("inst", "heavy warped drop\nhybrid trap 808 wreck\nmile grind"),
    ("inst", "trap hats roll\n808 bounce hold"),
    ("inst", "harder warped drop\nstacked 808 warp\nchest punch"),
    ("inst", "kick tightens\nchest 808"),
    ("inst", "full send drop\nbody bass wreck\nwarped trap"),
    ("outro", "kick holds\nhats denser\n808 ride"),
)

DONK_RAMP_LYRICS = format_edm_score(
    ("inst", "heavy tearout drop\ngrowl 808 wreck\nchest-sub ramp"),
    ("inst", "harder warped drop\nchest 808 stack\ntearout grind"),
    ("inst", "trap hats denser\ngrowl sustain"),
    ("inst", "full send drop\ndirty analog wreck\nwarped 808"),
    ("outro", "kick holds\ntrap hats roll\ngrowl ride"),
)

BOUNCE_BOOTH_LYRICS = format_edm_score(
    ("inst", "heavy chest drop\nwarped 808 wreck\nbooth grind"),
    ("inst", "trap hats roll\n808 punch hold"),
    ("inst", "harder warped drop\nstacked chest 808\nchest-sub wall"),
    ("inst", "kick tightens\nchest sub hold"),
    ("inst", "full send drop\nlow 808 wreck\nwarped chest"),
    ("outro", "kick holds\nhats denser\nchest ride"),
)

TOLL_GROWL_LYRICS = format_edm_score(
    ("inst", "heavy riddim drop\ntearout wobble wreck\nwarped toll"),
    ("inst", "rapid hi-hats roll\nwarped sustain"),
    ("inst", "harder warped drop\nsub crush\nchest 808"),
    ("inst", "trap hats denser\nwarped hold"),
    ("inst", "full send drop\nstacked wobble wreck\nwobble wall"),
    ("inst", "kick tightens\nbass warped hold"),
    ("inst", "harder warped drop\nstacked wobble wreck\nlow rumble"),
    ("outro", "kick holds\nhats denser\nwarped ride"),
)

NIGHT_OIL_LYRICS = format_edm_score(
    ("inst", "heavy hybrid drop\nwarped 808 wreck\noil grind"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder warped drop\ntrap bass wall\nchest-sub crush"),
    ("inst", "full send drop\nchest sub wreck\nhybrid warp"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)

CHEST_PASS_LYRICS = format_edm_score(
    ("inst", "heavy chest drop\nsub warp wreck\npass grind"),
    ("inst", "trap hats denser\n808 hold"),
    ("inst", "harder warped drop\ndual-action pedal bass\nstacked 808 wall"),
    ("inst", "pedal 808 hold\nhats roll"),
    ("inst", "full send drop\nbody bass wreck\nwarped chest"),
    ("outro", "kick holds\nhats denser\npedal ride"),
)

SUNRISE_SUB_LYRICS = format_edm_score(
    ("inst", "heavy wave drop\nwarped sub wreck\nfold 808"),
    ("inst", "trap hats roll\nwave 808 sustain dawn"),
    ("inst", "harder warped drop\nchest gold wreck\n808 punch"),
    ("inst", "full send drop\nlow 808 wreck\nwave warp"),
    ("outro", "kick holds\ntrap hats roll\nwave ride"),
)

# Authored takes: one row per track, in track order.
_TAKES: tuple[DriveRowSpec, ...] = (
    {
        "slug": "rumble-strip",
        "bpm": 140,
        "seed": 271,
        "take": "rumble-strip hybrid trap warp",
        "lyrics": RUMBLE_STRIP_LYRICS,
        "recipe": "rec_drive_through_drop",
        "picks": {"bass_low_end": "bass_pedal_dual"},
    },
    {
        "slug": "low-lane",
        "bpm": 144,
        "seed": 277,
        "take": "low-lane riddim warp",
        "lyrics": LOW_LANE_LYRICS,
        "recipe": "rec_drive_riddim",
        "picks": {"bass_low_end": "bass_stacked_808"},
    },
    {
        "slug": "warm-merge",
        "bpm": 148,
        "seed": 281,
        "take": "warm-merge wave bass warp",
        "lyrics": WARM_MERGE_LYRICS,
        "recipe": "rec_drive_wave",
        "picks": {"bass_low_end": "bass_chest_sub"},
    },
    {
        "slug": "colour-span",
        "bpm": 150,
        "seed": 283,
        "take": "colour-span color bass warp",
        "lyrics": COLOUR_SPAN_LYRICS,
        "recipe": "rec_drive_color",
        "picks": {"bass_low_end": "bass_warped"},
    },
    {
        "slug": "garage-ticket",
        "bpm": 140,
        "seed": 293,
        "take": "garage-ticket festival trap warp",
        "lyrics": GARAGE_TICKET_LYRICS,
        "recipe": "rec_drive_festival_trap",
        "picks": {"bass_low_end": "bass_warped"},
    },
    {
        "slug": "liquid-grade",
        "bpm": 174,
        "seed": 307,
        "take": "liquid-grade drumstep warp",
        "lyrics": LIQUID_GRADE_LYRICS,
        "recipe": "rec_drive_drumstep",
    },
    {
        "slug": "jump-bay",
        "bpm": 150,
        "seed": 311,
        "take": "jump-bay brostep warp",
        "lyrics": JUMP_BAY_LYRICS,
        "recipe": "rec_drive_brostep",
        "picks": {"genre_style": "gen_dirty_dubstep"},
    },
    {
        "slug": "psy-median",
        "bpm": 145,
        "seed": 313,
        "take": "psy-median neuro warp",
        "lyrics": PSY_MEDIAN_LYRICS,
        "recipe": "rec_drive_neuro",
        "picks": {"bass_low_end": "bass_stacked_808"},
    },
    {
        "slug": "groove-mile",
        "bpm": 144,
        "seed": 317,
        "take": "groove-mile hybrid trap warp",
        "lyrics": GROOVE_MILE_LYRICS,
        "recipe": "rec_drive_through_drop",
        "picks": {"bass_low_end": "bass_warped"},
    },
    {
        "slug": "donk-ramp",
        "bpm": 150,
        "seed": 331,
        "take": "donk-ramp tearout warp",
        "lyrics": DONK_RAMP_LYRICS,
        "recipe": "rec_drive_tearout",
    },
    {
        "slug": "bounce-booth",
        "bpm": 140,
        "seed": 337,
        "take": "bounce-booth chest bass warp",
        "lyrics": BOUNCE_BOOTH_LYRICS,
        "recipe": "rec_drive_chest",
        "picks": {"bass_low_end": "bass_warped"},
    },
    {
        "slug": "toll-growl",
        "bpm": 150,
        "seed": 347,
        "take": "toll-growl riddim warp",
        "lyrics": TOLL_GROWL_LYRICS,
        "recipe": "rec_drive_riddim",
    },
    {
        "slug": "night-oil",
        "bpm": 142,
        "seed": 349,
        "take": "night-oil hybrid trap warp",
        "lyrics": NIGHT_OIL_LYRICS,
        "recipe": "rec_drive_festival_trap",
        "picks": {"genre_style": "gen_hybrid_trap", "bass_low_end": "bass_chest_sub"},
    },
    {
        "slug": "chest-pass",
        "bpm": 150,
        "seed": 353,
        "take": "chest-pass dirty bass warp",
        "lyrics": CHEST_PASS_LYRICS,
        "recipe": "rec_drive_dirty",
        "picks": {"bass_low_end": "bass_pedal_dual"},
    },
    {
        "slug": "sunrise-sub",
        "bpm": 140,
        "seed": 359,
        "take": "sunrise-sub wave bass warp",
        "lyrics": SUNRISE_SUB_LYRICS,
        "recipe": "rec_drive_wave",
    },
)

# Catalog rows. Finalized when the catalog assembles.
EDM_DRIVE_THROUGH_BASS: tuple[EdmExampleRow, ...] = build_album(
    _TAKES,
    phase=BASS_PHASE,
    row_for=_ex,
    layouts=None,
)

"""Drive-through full-length bass-set takes (hour 3, headliner).

Fictional act. Original dance arrangements. No living-artist names.
Warped hybrid-trap EDM: drop first, hard warpy drops, trap drums, high-BPM
headliner energy, all instrumental.
"""

from __future__ import annotations

from .edm_album import (
    HEADLINER_PHASE,
    DriveRowSpec,
    build_album,
    layout_cycle,
)
from .edm_examples import EdmExampleRow, _ex, format_edm_score

# Track scores for this live-set hour.

LANTERN_MERGE_LYRICS = format_edm_score(
    ("inst", "heavy warped drop\ntrap 808 wreck\nchest-sub"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder warped drop\nstacked trap 808\nchest warp"),
    ("inst", "kick tightens\nchest 808 punch"),
    ("inst", "full send drop\nbody bass wreck\nwarped trap"),
    ("outro", "kick holds\ntrap hats roll\nchest ride"),
)

FIREFLY_LANE_LYRICS = format_edm_score(
    ("inst", "heavy color drop\ntrap 808 warp\nchest wreck"),
    ("inst", "trap hats denser\ncolor 808 sustain firefly"),
    ("inst", "harder stacked drop\nchest color wreck\nwarped 808"),
    ("inst", "full send drop\ndirty trap 808\nwarped wall"),
    ("outro", "kick holds\nhats denser\ncolor ride"),
)

CANOPY_BOUNCE_LYRICS = format_edm_score(
    ("inst", "heavy chest drop\ntrap 808 warp\ncanopy wreck"),
    ("inst", "trap hats roll\nchest 808 hold"),
    ("inst", "harder warped drop\nstacked body 808\nwarped chest"),
    ("inst", "kick tightens\n808 punch"),
    ("inst", "full send drop\nchest bass wreck\ntrap warp"),
    ("outro", "kick holds\ntrap hats roll\nchest ride"),
)

GROVE_WRECK_LYRICS = format_edm_score(
    ("inst", "heavy riddim drop\nwobble trap 808\nchest wreck"),
    ("inst", "rapid hi-hats roll\nwarp 808 sustain grove"),
    ("inst", "harder stacked drop\nchest warped wreck\ntrap 808"),
    ("inst", "trap hats denser\nwobble hold"),
    ("inst", "full send drop\nchest sub wreck\nwarped riddim"),
    ("inst", "harder warped drop\nchest 808 wreck\ntrap wobble"),
    ("outro", "kick holds\nhats denser\nwobble ride"),
)

MOSS_SUB_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nchest sub warp\ntrap 808 wreck"),
    ("inst", "trap hats roll\npedal 808 hold"),
    ("inst", "harder warped drop\ndual-action pedal bass\nrolling 808 wall"),
    ("inst", "hats denser\nchest 808"),
    ("inst", "full send drop\nbody 808 wreck\nwarped trap"),
    ("outro", "kick holds\ntrap hats roll\npedal ride"),
)

FERN_STACK_LYRICS = format_edm_score(
    ("inst", "heavy hybrid drop\nstacked trap 808\nchest warp wreck"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder stacked drop\nchest trap wreck\nwarped 808"),
    ("inst", "kick tightens\nchest 808 punch"),
    ("inst", "full send drop\nbody 808 stack\nwarped trap"),
    ("inst", "harder warped drop\ntrap bass wreck\nchest warp"),
    ("outro", "kick holds\nhats denser\n808 ride"),
)

POLLEN_KICK_LYRICS = format_edm_score(
    ("inst", "heavy amen drop\ntrap 808 warp\nchest wreck"),
    ("inst", "amen chops\ntrap hats 808 pollen"),
    ("inst", "harder stacked drop\nreese 808 wreck\nchest-sub"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "full send drop\nstacked amen 808 wreck\nwarped trap"),
    ("inst", "kick tightens\n808 punch"),
    ("inst", "harder reese drop\nchest trap wreck\nreese wall"),
    ("outro", "kick holds\namen keep\nreese ride"),
)

CEDAR_GROWL_LYRICS = format_edm_score(
    ("inst", "heavy tearout drop\ntrap growl wreck\nchest 808 warp"),
    ("inst", "rapid hi-hats roll\ngrowl sustain"),
    ("inst", "harder stacked drop\nchest 808 wreck\nwarped trap"),
    ("inst", "full send drop\nchest sub wreck\ntearout warp"),
    ("outro", "kick holds\ntrap hats roll\ngrowl ride"),
)

MOON_RAMP_LYRICS = format_edm_score(
    ("inst", "heavy wave drop\ntrap 808 warp\nchest fold wreck"),
    ("inst", "trap hats denser\nwave 808 hold moon"),
    ("inst", "harder warped drop\nchest 808 wall\nwarped wave"),
    ("inst", "kick tightens\n808 slide"),
    ("inst", "full send drop\nbody wave wreck\ntrap warped"),
    ("outro", "kick holds\nhats denser\nwave ride"),
)

TRAIL_BOUNCE_LYRICS = format_edm_score(
    ("inst", "heavy color drop\ntrap 808 warp\nchest trail wreck"),
    ("inst", "trap hats roll\n808 punch hold"),
    ("inst", "harder stacked drop\nchest color wreck\nwarped 808"),
    ("inst", "kick tightens\nchest 808"),
    ("inst", "full send drop\nbody 808 wreck\ncolor warp"),
    ("inst", "harder warped drop\ntrap bass wall\nchest-sub"),
    ("outro", "kick holds\ntrap hats roll\ncolor ride"),
)

DEW_WRECK_LYRICS = format_edm_score(
    ("inst", "heavy neuro drop\nreese trap 808\nchest warp wreck"),
    ("inst", "amen chops\ntrap hats 808 dew"),
    ("inst", "harder stacked drop\nchest reese wreck\nwarped 808"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "full send drop\ntrap 808 wreck\nchest warped"),
    ("inst", "kick tightens\n808 punch"),
    ("inst", "harder growl drop\nstacked neuro 808 wreck\ntrap warp"),
    ("inst", "full send drop\nbody reese wreck\nchest 808"),
    ("outro", "kick holds\namen keep\nreese ride"),
)

SAP_STACK_LYRICS = format_edm_score(
    ("inst", "heavy brostep drop\nchest trap 808\nwarped wreck"),
    ("inst", "trap hats denser\ngrowl hold"),
    ("inst", "harder stacked drop\ntrap 808 wall\nchest warped"),
    ("inst", "kick tightens\n808 punch"),
    ("inst", "full send drop\nbody bass wreck\nwarped trap"),
    ("inst", "harder growl drop\nstacked 808 wreck\nchest warp"),
    ("outro", "kick holds\nhats denser\nbrostep ride"),
)

GLADE_SPLIT_LYRICS = format_edm_score(
    ("inst", "heavy dubstep drop\ntrap 808 warp\nchest split wreck"),
    ("inst", "trap hats roll\nwobble hold"),
    ("inst", "harder stacked drop\nchest analog wreck\nwarped 808"),
    ("inst", "kick tightens\nchest 808"),
    ("inst", "full send drop\ndouble 808 wreck\ntrap warped"),
    ("inst", "hats denser\n808 punch"),
    ("inst", "harder wobble drop\nbody dubstep wreck\nchest warp"),
    ("outro", "kick holds\ntrap hats roll\nwobble ride"),
)

ROOT_CHEST_LYRICS = format_edm_score(
    ("inst", "heavy chest drop\ntrap sub wreck\nwarped 808"),
    ("inst", "trap hats denser\nchest 808 hold"),
    ("inst", "harder chest drop\ndual-action pedal bass\nstacked 808 warp"),
    ("inst", "pedal 808 hold\nhats roll"),
    ("inst", "full send drop\nbody chest wreck\ntrap warp"),
    ("inst", "hats denser\n808 punch"),
    ("inst", "harder stacked drop\ntrap 808 wreck\nchest warped"),
    ("inst", "full send drop\nchest sub wreck\nwarped pedal"),
    ("outro", "kick holds\ntrap hats roll\npedal ride"),
)

EMBER_CREST_LYRICS = format_edm_score(
    ("inst", "heavy warped drop\ntrap 808 wreck\nchest crest grind"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder stacked drop\nchest 808 wall\ntrap warped"),
    ("inst", "kick tightens\nchest 808 punch"),
    ("inst", "full send drop\nbody bass wreck\nwarped trap"),
    ("inst", "harder warped drop\nstacked trap wreck\nchest 808"),
    ("inst", "full send drop\nchest sub wreck\nwarp wall"),
    ("outro", "kick holds\nhats denser\n808 ride"),
)

# Authored takes: one row per track, in track order.
_TAKES: tuple[DriveRowSpec, ...] = (
    {
        "slug": "lantern-merge",
        "bpm": 150,
        "seed": 367,
        "take": "lantern-merge hybrid trap warp",
        "lyrics": LANTERN_MERGE_LYRICS,
        "recipe": "rec_drive_through_drop",
    },
    {
        "slug": "firefly-lane",
        "bpm": 152,
        "seed": 373,
        "take": "firefly-lane color bass warp",
        "lyrics": FIREFLY_LANE_LYRICS,
        "recipe": "rec_drive_color",
    },
    {
        "slug": "canopy-bounce",
        "bpm": 148,
        "seed": 379,
        "take": "canopy-bounce chest bass warp",
        "lyrics": CANOPY_BOUNCE_LYRICS,
        "recipe": "rec_drive_chest",
    },
    {
        "slug": "grove-wreck",
        "bpm": 150,
        "seed": 383,
        "take": "grove-wreck riddim warp",
        "lyrics": GROVE_WRECK_LYRICS,
        "recipe": "rec_drive_riddim",
    },
    {
        "slug": "moss-sub",
        "bpm": 150,
        "seed": 389,
        "take": "moss-sub dirty bass warp",
        "lyrics": MOSS_SUB_LYRICS,
        "recipe": "rec_drive_dirty",
        "picks": {"bass_low_end": "bass_pedal_dual"},
    },
    {
        "slug": "fern-stack",
        "bpm": 155,
        "seed": 397,
        "take": "fern-stack hybrid trap warp",
        "lyrics": FERN_STACK_LYRICS,
        "recipe": "rec_drive_through_drop",
        "picks": {"bass_low_end": "bass_stacked_808"},
    },
    {
        "slug": "pollen-kick",
        "bpm": 174,
        "seed": 401,
        "take": "pollen-kick drumstep warp",
        "lyrics": POLLEN_KICK_LYRICS,
        "recipe": "rec_drive_drumstep",
        "picks": {"drums_rhythm": "drm_amen_chop"},
    },
    {
        "slug": "cedar-growl",
        "bpm": 150,
        "seed": 409,
        "take": "cedar-growl tearout warp",
        "lyrics": CEDAR_GROWL_LYRICS,
        "recipe": "rec_drive_tearout",
    },
    {
        "slug": "moon-ramp",
        "bpm": 148,
        "seed": 419,
        "take": "moon-ramp wave bass warp",
        "lyrics": MOON_RAMP_LYRICS,
        "recipe": "rec_drive_wave",
    },
    {
        "slug": "trail-bounce",
        "bpm": 150,
        "seed": 421,
        "take": "trail-bounce color bass warp",
        "lyrics": TRAIL_BOUNCE_LYRICS,
        "recipe": "rec_drive_color",
        "picks": {"bass_low_end": "bass_body"},
    },
    {
        "slug": "dew-wreck",
        "bpm": 172,
        "seed": 431,
        "take": "dew-wreck neuro bass warp",
        "lyrics": DEW_WRECK_LYRICS,
        "recipe": "rec_drive_neuro",
        "picks": {"genre_style": "gen_drumstep"},
    },
    {
        "slug": "sap-stack",
        "bpm": 165,
        "seed": 433,
        "take": "sap-stack brostep warp",
        "lyrics": SAP_STACK_LYRICS,
        "recipe": "rec_drive_brostep",
        "picks": {"bass_low_end": "bass_stacked_808"},
    },
    {
        "slug": "glade-split",
        "bpm": 150,
        "seed": 439,
        "take": "glade-split dirty dubstep warp",
        "lyrics": GLADE_SPLIT_LYRICS,
        "recipe": "rec_drive_dirty_dubstep",
    },
    {
        "slug": "root-chest",
        "bpm": 148,
        "seed": 443,
        "take": "root-chest chest bass warp",
        "lyrics": ROOT_CHEST_LYRICS,
        "recipe": "rec_drive_chest",
        "picks": {"bass_low_end": "bass_pedal_dual"},
    },
    {
        "slug": "ember-crest",
        "bpm": 165,
        "seed": 449,
        "take": "ember-crest hybrid trap warp",
        "lyrics": EMBER_CREST_LYRICS,
        "recipe": "rec_drive_through_drop",
    },
)

# Catalog rows. Finalized when the catalog assembles.
EDM_DRIVE_THROUGH_HEADLINER: tuple[EdmExampleRow, ...] = build_album(
    _TAKES,
    phase=HEADLINER_PHASE,
    row_for=_ex,
    layouts=layout_cycle(len(_TAKES), offset=1),
)

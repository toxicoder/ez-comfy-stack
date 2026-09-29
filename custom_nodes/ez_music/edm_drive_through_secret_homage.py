"""Drive-through full-length bass-set takes (Secret Homage album).

Fictional act. Original dance arrangements. No living-artist names.
Warped bass EDM: drop first, hard warpy drops, trap drums, dirty dubstep,
brostep, riddim, tearout. All instrumental.
"""

from __future__ import annotations

from .edm_album import (
    SECRET_HOMAGE_PHASE,
    DriveRowSpec,
    build_album,
    layout_cycle,
)
from .edm_examples import EdmExampleRow, _ex, format_edm_score

# Track scores for this live-set hour.

HUSH_LANE_LYRICS = format_edm_score(
    ("inst", "heavy wobble drop\ndirty dubstep wreck\nwarped 808"),
    ("inst", "trap hats denser\nwobble sustain"),
    ("inst", "harder warped drop\nlow rumble wreck\nchest-sub"),
    ("inst", "full send drop\nchest sub wreck\ndubstep warp"),
    ("outro", "kick holds\ntrap hats roll\nwobble ride"),
)

CIPHER_LOCK_LYRICS = format_edm_score(
    ("inst", "heavy growl drop\nbrostep wreck\nwarped lock"),
    ("inst", "rapid hi-hats roll\ngrowl sustain"),
    ("inst", "harder dirty drop\nsub crush\nchest 808 warped"),
    ("inst", "trap hats denser\ngrowl hold"),
    ("inst", "full send drop\nstacked growl wreck\nbrostep warp"),
    ("outro", "kick holds\nhats denser\ngrowl ride"),
)

GHOST_DOCK_LYRICS = format_edm_score(
    ("inst", "heavy riddim drop\nwobble wreck\nwarped dock"),
    ("inst", "harder warped drop\nchest warped wreck\n808 crush"),
    ("inst", "trap hats roll\nwobble hold"),
    ("inst", "full send drop\nlow rumble wreck\nriddim warp"),
    ("outro", "kick holds\ntrap hats roll\nwobble ride"),
)

SEALED_RAMP_LYRICS = format_edm_score(
    ("inst", "heavy tearout drop\ngrowl wreck\nwarped seal"),
    ("inst", "rapid hi-hats roll\ngrowl sustain"),
    ("inst", "harder dirty drop\nsub crush\nchest 808 warp"),
    ("inst", "trap hats denser\ngrowl hold"),
    ("inst", "full send drop\nstacked tearout wreck\nwarped grind"),
    ("inst", "harder stacked drop\nlow rumble wreck\n808 warp"),
    ("outro", "kick holds\nhats denser\ngrowl ride"),
)

FOG_VAULT_LYRICS = format_edm_score(
    ("inst", "heavy color drop\nwarped 808 wreck\nvault grind"),
    ("inst", "trap hats roll\ncolor 808 hold vault"),
    ("inst", "harder warped drop\nchest analog wreck\nchest-sub 808"),
    ("inst", "kick tightens\nchest 808 punch"),
    ("inst", "full send drop\nstacked color wreck\nwarped sub"),
    ("outro", "kick holds\nhats denser\ncolor ride"),
)

DUMMY_LIGHT_LYRICS = format_edm_score(
    ("inst", "heavy warped drop\nstacked 808 wreck\nlight grind"),
    ("inst", "trap hats denser\n808 hold"),
    ("inst", "harder stacked drop\nchest sub wall\nhybrid warped"),
    ("inst", "full send drop\nlow 808 wreck\ntrap warp"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)

QUIET_WRECK_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nwarped bass wreck\nslam 808"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder warped drop\nlow rumble wreck\nchest-sub"),
    ("inst", "kick tightens\nchest 808 punch"),
    ("inst", "full send drop\nchest sub wreck\ndirty warp"),
    ("inst", "hats denser\n808 punch hold"),
    ("inst", "harder stacked drop\nslam wreck\nwarped 808"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)

OFF_LEDGER_LYRICS = format_edm_score(
    ("inst", "heavy amen drop\nreese wreck\nwarped ledger"),
    ("inst", "amen chops\ntrap hats 808 ledger"),
    ("inst", "harder dirty drop\nreese stack\nchest-sub"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "full send drop\nstacked amen wreck\n808 warp"),
    ("inst", "harder warped drop\nchest 808 wreck\ndrumstep grind"),
    ("outro", "kick holds\namen keep\nreese ride"),
)

BACK_ALLEY_LYRICS = format_edm_score(
    ("inst", "heavy neuro drop\nreese 808 wreck\nwarped alley"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "harder stacked drop\nchest reese wreck\nchest-sub coil"),
    ("inst", "trap hats roll\n808 punch"),
    ("inst", "full send drop\nneuro 808 wreck\nchest warp"),
    ("inst", "kick tightens\nalley 808 punch"),
    ("inst", "harder growl drop\nstacked reese wreck\nalley grind"),
    ("outro", "kick holds\nhats denser\nreese ride"),
)

CELLAR_KICK_LYRICS = format_edm_score(
    ("inst", "heavy wobble drop\ndirty dubstep wreck\nwarped cellar"),
    ("inst", "trap hats denser\nwobble sustain"),
    ("inst", "harder warped drop\nlow rumble wreck\nchest 808"),
    ("inst", "full send drop\nchest sub wreck\ndubstep warp"),
    ("outro", "kick holds\ntrap hats roll\nwobble ride"),
)

HIDDEN_BOOTH_LYRICS = format_edm_score(
    ("inst", "heavy hybrid drop\ntrap 808 wreck\nwarped booth"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder warped drop\nstacked trap bass\nchest-sub"),
    ("inst", "kick tightens\nchest 808 punch"),
    ("inst", "full send drop\nchest 808 wall\nhybrid warp"),
    ("outro", "kick holds\nhats denser\n808 ride"),
)

CODED_SUB_LYRICS = format_edm_score(
    ("inst", "heavy chest drop\ndual-action pedal bass\n808 warp wreck"),
    ("inst", "pedal 808 hold\ntrap hats roll"),
    ("inst", "harder warped drop\nrolling 808 wall\nchest-sub"),
    ("inst", "kick tightens\nchest 808"),
    ("inst", "hats denser\ncoded 808 hold"),
    ("inst", "full send drop\nchest sub wreck\npedal warp"),
    ("outro", "kick holds\nhats denser\npedal ride"),
)

SHADOW_COIL_LYRICS = format_edm_score(
    ("inst", "heavy neuro drop\nreese coil wreck\nwarped shadow"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "harder stacked drop\nchest reese wreck\nchest-sub coil"),
    ("inst", "trap hats roll\n808 punch"),
    ("inst", "full send drop\ncoiled 808 wreck\nchest warp"),
    ("inst", "kick tightens\nshadow 808 punch"),
    ("inst", "harder growl drop\nstacked reese wreck\nshadow grind"),
    ("outro", "kick holds\nhats denser\nreese ride"),
)

MUTE_PYRO_LYRICS = format_edm_score(
    ("inst", "heavy wave drop\nwarped 808 wreck\nfold grind"),
    ("inst", "harder warped drop\nchest analog wreck\nchest-sub 808"),
    ("inst", "trap hats roll\nwave 808 hold analog"),
    ("inst", "full send drop\nstacked wave wreck\nwarped sub"),
    ("outro", "kick holds\ntrap hats roll\nwave ride"),
)

UNLISTED_ROW_LYRICS = format_edm_score(
    ("inst", "heavy amen drop\nreese wreck\nwarped row"),
    ("inst", "amen chops\ntrap hats 808 row"),
    ("inst", "harder stacked drop\nchest reese wreck\nchest-sub 808"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "full send drop\nstacked amen wreck\n808 warp"),
    ("inst", "kick tightens\nchest 808 punch"),
    ("inst", "harder warped drop\nchest 808 wreck\ndrumstep grind"),
    ("outro", "kick holds\namen keep\nreese ride"),
)

NIGHT_CIPHER_LYRICS = format_edm_score(
    ("inst", "heavy wave drop\nwarped bass wreck\ncipher 808"),
    ("inst", "trap hats denser\nwave 808 sustain cipher"),
    ("inst", "harder warped drop\nchest 808 wall\nchest-sub fold"),
    ("inst", "full send drop\nlow swell wreck\nwave warp"),
    ("outro", "kick holds\nhats denser\nwave ride"),
)

BLANK_STENCIL_LYRICS = format_edm_score(
    ("inst", "heavy trap drop\nstencil 808 wreck\nwarped stamp"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder stacked drop\ntrap wall wreck\nchest warped"),
    ("inst", "kick tightens\nstencil 808 punch"),
    ("inst", "hats denser\ntrap 808 hold"),
    ("inst", "full send drop\nlow 808 wreck\nstencil warp"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)

BLIND_STAMP_LYRICS = format_edm_score(
    ("inst", "heavy riddim drop\nwobble wreck\nwarped stamp"),
    ("inst", "rapid hi-hats roll\nwobble sustain"),
    ("inst", "harder warped drop\nchest warped wreck\n808 crush"),
    ("inst", "trap hats denser\nwobble hold"),
    ("inst", "full send drop\nsub crush wreck\nriddim warp"),
    ("outro", "kick holds\nhats denser\nwobble ride"),
)

COLD_CACHE_LYRICS = format_edm_score(
    ("inst", "heavy hybrid drop\nwarped 808 wreck\ncache grind"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder warped drop\ntrap bass wall\nchest-sub"),
    ("inst", "kick tightens\nchest 808 punch"),
    ("inst", "hats denser\ncache 808 hold"),
    ("inst", "808 triplets\nhybrid warped sustain"),
    ("inst", "full send drop\nchest sub wreck\nhybrid warp"),
    ("outro", "kick holds\nhats denser\n808 ride"),
)

SECRET_HOMAGE_LYRICS = format_edm_score(
    ("inst", "heavy wobble drop\ndirty dubstep wreck\nwarped homage"),
    ("inst", "trap hats denser\nwobble sustain"),
    ("inst", "harder stacked drop\nchest sub wall\n808 warped"),
    ("inst", "full send drop\nlow rumble wreck\ndubstep warp"),
    ("outro", "kick holds\ntrap hats roll\nwobble ride"),
)

# Authored takes: one row per track, in track order.
_TAKES: tuple[DriveRowSpec, ...] = (
    {
        "slug": "hush-lane",
        "bpm": 140,
        "seed": 593,
        "take": "hush-lane dirty dubstep warp",
        "lyrics": HUSH_LANE_LYRICS,
        "recipe": "rec_drive_dirty_dubstep",
    },
    {
        "slug": "cipher-lock",
        "bpm": 140,
        "seed": 599,
        "take": "cipher-lock brostep warp",
        "lyrics": CIPHER_LOCK_LYRICS,
        "recipe": "rec_drive_brostep",
        "picks": {"genre_style": "gen_dirty_dubstep"},
    },
    {
        "slug": "ghost-dock",
        "bpm": 140,
        "seed": 601,
        "take": "ghost-dock riddim warp",
        "lyrics": GHOST_DOCK_LYRICS,
        "recipe": "rec_drive_riddim",
    },
    {
        "slug": "sealed-ramp",
        "bpm": 145,
        "seed": 607,
        "take": "sealed-ramp tearout warp",
        "lyrics": SEALED_RAMP_LYRICS,
        "recipe": "rec_drive_tearout",
    },
    {
        "slug": "fog-vault",
        "bpm": 142,
        "seed": 613,
        "take": "fog-vault color bass warp",
        "lyrics": FOG_VAULT_LYRICS,
        "recipe": "rec_drive_color",
    },
    {
        "slug": "dummy-light",
        "bpm": 145,
        "seed": 617,
        "take": "dummy-light hybrid trap warp",
        "lyrics": DUMMY_LIGHT_LYRICS,
        "recipe": "rec_drive_through_drop",
        "picks": {"bass_low_end": "bass_stacked_808"},
    },
    {
        "slug": "quiet-wreck",
        "bpm": 140,
        "seed": 619,
        "take": "quiet-wreck dirty bass warp",
        "lyrics": QUIET_WRECK_LYRICS,
        "recipe": "rec_drive_dirty",
    },
    {
        "slug": "off-ledger",
        "bpm": 174,
        "seed": 631,
        "take": "off-ledger drumstep warp",
        "lyrics": OFF_LEDGER_LYRICS,
        "recipe": "rec_drive_drumstep",
        "picks": {"drums_rhythm": "drm_amen_chop"},
    },
    {
        "slug": "back-alley",
        "bpm": 172,
        "seed": 641,
        "take": "back-alley neuro bass warp",
        "lyrics": BACK_ALLEY_LYRICS,
        "recipe": "rec_drive_neuro",
        "picks": {"genre_style": "gen_drumstep"},
    },
    {
        "slug": "cellar-kick",
        "bpm": 148,
        "seed": 643,
        "take": "cellar-kick dirty dubstep warp",
        "lyrics": CELLAR_KICK_LYRICS,
        "recipe": "rec_drive_dirty_dubstep",
    },
    {
        "slug": "hidden-booth",
        "bpm": 140,
        "seed": 647,
        "take": "hidden-booth hybrid trap warp",
        "lyrics": HIDDEN_BOOTH_LYRICS,
        "recipe": "rec_drive_through_drop",
        "picks": {"genre_style": "gen_dirty_bass"},
    },
    {
        "slug": "coded-sub",
        "bpm": 140,
        "seed": 653,
        "take": "coded-sub chest bass warp",
        "lyrics": CODED_SUB_LYRICS,
        "recipe": "rec_drive_chest",
        "picks": {"bass_low_end": "bass_pedal_dual"},
    },
    {
        "slug": "shadow-coil",
        "bpm": 150,
        "seed": 659,
        "take": "shadow-coil neuro bass warp",
        "lyrics": SHADOW_COIL_LYRICS,
        "recipe": "rec_drive_neuro",
    },
    {
        "slug": "mute-pyro",
        "bpm": 150,
        "seed": 661,
        "take": "mute-pyro wave bass warp",
        "lyrics": MUTE_PYRO_LYRICS,
        "recipe": "rec_drive_wave",
    },
    {
        "slug": "unlisted-row",
        "bpm": 176,
        "seed": 673,
        "take": "unlisted-row drumstep warp",
        "lyrics": UNLISTED_ROW_LYRICS,
        "recipe": "rec_drive_drumstep",
        "picks": {"drums_rhythm": "drm_amen_chop"},
    },
    {
        "slug": "night-cipher",
        "bpm": 140,
        "seed": 677,
        "take": "night-cipher wave bass warp",
        "lyrics": NIGHT_CIPHER_LYRICS,
        "recipe": "rec_drive_wave",
        "picks": {"genre_style": "gen_dirty_bass"},
    },
    {
        "slug": "blank-stencil",
        "bpm": 140,
        "seed": 683,
        "take": "blank-stencil festival trap warp",
        "lyrics": BLANK_STENCIL_LYRICS,
        "recipe": "rec_drive_festival_trap",
        "picks": {"genre_style": "gen_dirty_bass"},
    },
    {
        "slug": "blind-stamp",
        "bpm": 150,
        "seed": 691,
        "take": "blind-stamp riddim warp",
        "lyrics": BLIND_STAMP_LYRICS,
        "recipe": "rec_drive_riddim",
    },
    {
        "slug": "cold-cache",
        "bpm": 142,
        "seed": 701,
        "take": "cold-cache hybrid trap warp",
        "lyrics": COLD_CACHE_LYRICS,
        "recipe": "rec_drive_through_drop",
    },
    {
        "slug": "secret-homage",
        "bpm": 140,
        "seed": 709,
        "take": "secret-homage dirty dubstep warp",
        "lyrics": SECRET_HOMAGE_LYRICS,
        "recipe": "rec_drive_dirty_dubstep",
        "picks": {"bass_low_end": "bass_stacked_808"},
    },
)

# Catalog rows. Finalized when the catalog assembles.
EDM_DRIVE_THROUGH_SECRET_HOMAGE: tuple[EdmExampleRow, ...] = build_album(
    _TAKES,
    phase=SECRET_HOMAGE_PHASE,
    row_for=_ex,
    layouts=layout_cycle(len(_TAKES), offset=0),
)

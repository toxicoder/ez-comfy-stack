"""Drive-through 180s bass-set takes (Secret Homage album).

Fictional act. Original dance arrangements. No living-artist names.
Warped bass EDM: drop first, hard warpy drops, trap drums, dirty dubstep,
brostep, riddim, tearout. All instrumental.
"""

from __future__ import annotations

from .edm_examples import EdmExample, _ex, format_edm_score

# Catalog phase, track scores, and catalog rows.
SECRET_HOMAGE_PHASE = 4


HUSH_LANE_LYRICS = format_edm_score(
    ("inst", "heavy wobble drop\ndirty dubstep wreck\nwarped 808"),
    ("inst", "trap hats denser\nwobble sustain"),
    ("inst", "harder growl drop\nlow rumble wreck\nchest formant"),
    ("inst", "full send drop\nchest sub wreck\ndubstep warp"),
    ("outro", "kick holds\ntrap hats roll\nwobble ride"),
)

CIPHER_LOCK_LYRICS = format_edm_score(
    ("inst", "heavy growl drop\nbrostep wreck\nwarped lock"),
    ("inst", "metal hats roll\ngrowl sustain"),
    ("inst", "harder dirty drop\nsub crush\nchest 808 formant"),
    ("inst", "trap hats denser\ngrowl hold"),
    ("inst", "full send drop\nstacked growl wreck\nbrostep warp"),
    ("outro", "kick holds\nhats denser\ngrowl ride"),
)

GHOST_DOCK_LYRICS = format_edm_score(
    ("inst", "heavy riddim drop\nwobble wreck\nwarped dock"),
    ("inst", "harder growl drop\nchest growl wreck\n808 crush"),
    ("inst", "trap hats roll\nwobble hold"),
    ("inst", "full send drop\nlow rumble wreck\nriddim warp"),
    ("outro", "kick holds\ntrap hats roll\nwobble ride"),
)

SEALED_RAMP_LYRICS = format_edm_score(
    ("inst", "heavy tearout drop\ngrowl wreck\nwarped seal"),
    ("inst", "metal hats roll\ngrowl sustain"),
    ("inst", "harder dirty drop\nsub crush\nchest 808 warp"),
    ("inst", "trap hats denser\ngrowl hold"),
    ("inst", "full send drop\nstacked tearout wreck\nformant grind"),
    ("inst", "harder stacked drop\nlow rumble wreck\n808 warp"),
    ("outro", "kick holds\nhats denser\ngrowl ride"),
)

FOG_VAULT_LYRICS = format_edm_score(
    ("inst", "heavy color drop\nwarped 808 wreck\nvault grind"),
    ("inst", "trap hats roll\ncolor 808 hold vault"),
    ("inst", "harder growl drop\nchest analog wreck\nformant 808"),
    ("inst", "snare roll\nchest 808 punch"),
    ("inst", "full send drop\nstacked color wreck\nwarped sub"),
    ("outro", "kick holds\nhats denser\ncolor ride"),
)

DUMMY_LIGHT_LYRICS = format_edm_score(
    ("inst", "heavy warped drop\nstacked 808 wreck\nlight grind"),
    ("inst", "trap hats denser\n808 hold"),
    ("inst", "harder stacked drop\nchest sub wall\nhybrid formant"),
    ("inst", "full send drop\nlow 808 wreck\ntrap warp"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)

QUIET_WRECK_LYRICS = format_edm_score(
    ("inst", "heavy dirty drop\nwarped bass wreck\nslam 808"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder growl drop\nlow rumble wreck\nchest formant"),
    ("inst", "snare roll\nchest 808 punch"),
    ("inst", "full send drop\nchest sub wreck\ndirty warp"),
    ("inst", "hats denser\n808 punch hold"),
    ("inst", "harder stacked drop\nslam wreck\nwarped 808"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)

OFF_LEDGER_LYRICS = format_edm_score(
    ("inst", "heavy amen drop\nreese wreck\nwarped ledger"),
    ("inst", "amen chops\ntrap hats 808 ledger"),
    ("inst", "harder dirty drop\nreese stack\nchest formant"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "full send drop\nstacked amen wreck\n808 warp"),
    ("inst", "harder growl drop\nchest 808 wreck\ndrumstep grind"),
    ("outro", "kick holds\namen keep\nreese ride"),
)

BACK_ALLEY_LYRICS = format_edm_score(
    ("inst", "heavy neuro drop\nreese 808 wreck\nwarped alley"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "harder stacked drop\nchest reese wreck\nformant coil"),
    ("inst", "trap hats roll\n808 punch"),
    ("inst", "full send drop\nneuro 808 wreck\nchest warp"),
    ("inst", "snare roll\nalley 808 punch"),
    ("inst", "harder growl drop\nstacked reese wreck\nalley grind"),
    ("outro", "kick holds\nhats denser\nreese ride"),
)

CELLAR_KICK_LYRICS = format_edm_score(
    ("inst", "heavy wobble drop\ndirty dubstep wreck\nwarped cellar"),
    ("inst", "trap hats denser\nwobble sustain"),
    ("inst", "harder growl drop\nlow rumble wreck\nchest 808"),
    ("inst", "full send drop\nchest sub wreck\ndubstep warp"),
    ("outro", "kick holds\ntrap hats roll\nwobble ride"),
)

HIDDEN_BOOTH_LYRICS = format_edm_score(
    ("inst", "heavy hybrid drop\ntrap 808 wreck\nwarped booth"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder growl drop\nstacked trap bass\nchest formant"),
    ("inst", "snare roll\nchest 808 punch"),
    ("inst", "full send drop\nchest 808 wall\nhybrid warp"),
    ("outro", "kick holds\nhats denser\n808 ride"),
)

CODED_SUB_LYRICS = format_edm_score(
    ("inst", "heavy chest drop\ndual-action pedal bass\n808 warp wreck"),
    ("inst", "pedal 808 hold\ntrap hats roll"),
    ("inst", "harder growl drop\nrolling 808 wall\nchest formant"),
    ("inst", "snare roll\nchest 808"),
    ("inst", "hats denser\ncoded 808 hold"),
    ("inst", "full send drop\nchest sub wreck\npedal warp"),
    ("outro", "kick holds\nhats denser\npedal ride"),
)

SHADOW_COIL_LYRICS = format_edm_score(
    ("inst", "heavy neuro drop\nreese coil wreck\nwarped shadow"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "harder stacked drop\nchest reese wreck\nformant coil"),
    ("inst", "trap hats roll\n808 punch"),
    ("inst", "full send drop\ncoiled 808 wreck\nchest warp"),
    ("inst", "snare roll\nshadow 808 punch"),
    ("inst", "harder growl drop\nstacked reese wreck\nshadow grind"),
    ("outro", "kick holds\nhats denser\nreese ride"),
)

MUTE_PYRO_LYRICS = format_edm_score(
    ("inst", "heavy wave drop\nwarped 808 wreck\nfold grind"),
    ("inst", "harder growl drop\nchest analog wreck\nformant 808"),
    ("inst", "trap hats roll\nwave 808 hold analog"),
    ("inst", "full send drop\nstacked wave wreck\nwarped sub"),
    ("outro", "kick holds\ntrap hats roll\nwave ride"),
)

UNLISTED_ROW_LYRICS = format_edm_score(
    ("inst", "heavy amen drop\nreese wreck\nwarped row"),
    ("inst", "amen chops\ntrap hats 808 row"),
    ("inst", "harder stacked drop\nchest reese wreck\nformant 808"),
    ("inst", "hats denser\nreese hold"),
    ("inst", "full send drop\nstacked amen wreck\n808 warp"),
    ("inst", "snare roll\nchest 808 punch"),
    ("inst", "harder growl drop\nchest 808 wreck\ndrumstep grind"),
    ("outro", "kick holds\namen keep\nreese ride"),
)

NIGHT_CIPHER_LYRICS = format_edm_score(
    ("inst", "heavy wave drop\nwarped bass wreck\ncipher 808"),
    ("inst", "trap hats denser\nwave 808 sustain cipher"),
    ("inst", "harder growl drop\nchest 808 wall\nformant fold"),
    ("inst", "full send drop\nlow swell wreck\nwave warp"),
    ("outro", "kick holds\nhats denser\nwave ride"),
)

BLANK_STENCIL_LYRICS = format_edm_score(
    ("inst", "heavy trap drop\nstencil 808 wreck\nwarped stamp"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder stacked drop\ntrap wall wreck\nchest formant"),
    ("inst", "snare roll\nstencil 808 punch"),
    ("inst", "hats denser\ntrap 808 hold"),
    ("inst", "full send drop\nlow 808 wreck\nstencil warp"),
    ("outro", "kick holds\ntrap hats roll\n808 ride"),
)

BLIND_STAMP_LYRICS = format_edm_score(
    ("inst", "heavy riddim drop\nwobble wreck\nwarped stamp"),
    ("inst", "metal hats roll\nwobble sustain"),
    ("inst", "harder growl drop\nchest growl wreck\n808 crush"),
    ("inst", "trap hats denser\nwobble hold"),
    ("inst", "full send drop\nsub crush wreck\nriddim warp"),
    ("outro", "kick holds\nhats denser\nwobble ride"),
)

COLD_CACHE_LYRICS = format_edm_score(
    ("inst", "heavy hybrid drop\nwarped 808 wreck\ncache grind"),
    ("inst", "trap hats roll\n808 slide"),
    ("inst", "harder growl drop\ntrap bass wall\nchest formant"),
    ("inst", "snare roll\nchest 808 punch"),
    ("inst", "hats denser\ncache 808 hold"),
    ("inst", "808 triplets\nhybrid growl sustain"),
    ("inst", "full send drop\nchest sub wreck\nhybrid warp"),
    ("outro", "kick holds\nhats denser\n808 ride"),
)

SECRET_HOMAGE_LYRICS = format_edm_score(
    ("inst", "heavy wobble drop\ndirty dubstep wreck\nwarped homage"),
    ("inst", "trap hats denser\nwobble sustain"),
    ("inst", "harder stacked drop\nchest sub wall\n808 formant"),
    ("inst", "full send drop\nlow rumble wreck\ndubstep warp"),
    ("outro", "kick holds\ntrap hats roll\nwobble ride"),
)


EDM_DRIVE_THROUGH_SECRET_HOMAGE: tuple[EdmExample, ...] = (
    _ex(
        "hush-lane",
        "hush lane",
        140,
        593,
        SECRET_HOMAGE_PHASE,
        "hush-lane dirty dubstep warp",
        HUSH_LANE_LYRICS,
        recipe="rec_drive_dirty_dubstep",
        layout="column",
    ),
    _ex(
        "cipher-lock",
        "cipher lock",
        140,
        599,
        SECRET_HOMAGE_PHASE,
        "cipher-lock brostep warp",
        CIPHER_LOCK_LYRICS,
        recipe="rec_drive_brostep",
        picks={"genre_style": "gen_dirty_dubstep"},
        layout="wide-stage",
    ),
    _ex(
        "ghost-dock",
        "ghost dock",
        140,
        601,
        SECRET_HOMAGE_PHASE,
        "ghost-dock riddim warp",
        GHOST_DOCK_LYRICS,
        recipe="rec_drive_riddim",
        layout="stacked-tower",
    ),
    _ex(
        "sealed-ramp",
        "sealed ramp",
        145,
        607,
        SECRET_HOMAGE_PHASE,
        "sealed-ramp tearout warp",
        SEALED_RAMP_LYRICS,
        recipe="rec_drive_tearout",
        layout="prompt-left",
    ),
    _ex(
        "fog-vault",
        "fog vault",
        142,
        613,
        SECRET_HOMAGE_PHASE,
        "fog-vault color bass warp",
        FOG_VAULT_LYRICS,
        recipe="rec_drive_color",
        layout="output-rail",
    ),
    _ex(
        "dummy-light",
        "dummy light",
        145,
        617,
        SECRET_HOMAGE_PHASE,
        "dummy-light hybrid trap warp",
        DUMMY_LIGHT_LYRICS,
        recipe="rec_drive_through_drop",
        picks={"bass_low_end": "bass_stacked_808"},
        layout="column",
    ),
    _ex(
        "quiet-wreck",
        "quiet wreck",
        140,
        619,
        SECRET_HOMAGE_PHASE,
        "quiet-wreck dirty bass warp",
        QUIET_WRECK_LYRICS,
        recipe="rec_drive_dirty",
        layout="wide-stage",
    ),
    _ex(
        "off-ledger",
        "off ledger",
        174,
        631,
        SECRET_HOMAGE_PHASE,
        "off-ledger drumstep warp",
        OFF_LEDGER_LYRICS,
        recipe="rec_drive_drumstep",
        picks={"drums_rhythm": "drm_amen_chop"},
        layout="stacked-tower",
    ),
    _ex(
        "back-alley",
        "back alley",
        172,
        641,
        SECRET_HOMAGE_PHASE,
        "back-alley neuro bass warp",
        BACK_ALLEY_LYRICS,
        recipe="rec_drive_neuro",
        picks={"genre_style": "gen_drumstep"},
        layout="prompt-left",
    ),
    _ex(
        "cellar-kick",
        "cellar kick",
        148,
        643,
        SECRET_HOMAGE_PHASE,
        "cellar-kick dirty dubstep warp",
        CELLAR_KICK_LYRICS,
        recipe="rec_drive_dirty_dubstep",
        layout="output-rail",
    ),
    _ex(
        "hidden-booth",
        "hidden booth",
        140,
        647,
        SECRET_HOMAGE_PHASE,
        "hidden-booth hybrid trap warp",
        HIDDEN_BOOTH_LYRICS,
        recipe="rec_drive_through_drop",
        picks={"genre_style": "gen_dirty_bass"},
        layout="column",
    ),
    _ex(
        "coded-sub",
        "coded sub",
        140,
        653,
        SECRET_HOMAGE_PHASE,
        "coded-sub chest bass warp",
        CODED_SUB_LYRICS,
        recipe="rec_drive_chest",
        picks={"bass_low_end": "bass_pedal_dual"},
        layout="wide-stage",
    ),
    _ex(
        "shadow-coil",
        "shadow coil",
        150,
        659,
        SECRET_HOMAGE_PHASE,
        "shadow-coil neuro bass warp",
        SHADOW_COIL_LYRICS,
        recipe="rec_drive_neuro",
        layout="stacked-tower",
    ),
    _ex(
        "mute-pyro",
        "mute pyro",
        150,
        661,
        SECRET_HOMAGE_PHASE,
        "mute-pyro wave bass warp",
        MUTE_PYRO_LYRICS,
        recipe="rec_drive_wave",
        layout="prompt-left",
    ),
    _ex(
        "unlisted-row",
        "unlisted row",
        176,
        673,
        SECRET_HOMAGE_PHASE,
        "unlisted-row drumstep warp",
        UNLISTED_ROW_LYRICS,
        recipe="rec_drive_drumstep",
        picks={"drums_rhythm": "drm_amen_chop"},
        layout="output-rail",
    ),
    _ex(
        "night-cipher",
        "night cipher",
        140,
        677,
        SECRET_HOMAGE_PHASE,
        "night-cipher wave bass warp",
        NIGHT_CIPHER_LYRICS,
        recipe="rec_drive_wave",
        picks={"genre_style": "gen_dirty_bass"},
        layout="column",
    ),
    _ex(
        "blank-stencil",
        "blank stencil",
        140,
        683,
        SECRET_HOMAGE_PHASE,
        "blank-stencil festival trap warp",
        BLANK_STENCIL_LYRICS,
        recipe="rec_drive_festival_trap",
        picks={"genre_style": "gen_dirty_bass"},
        layout="wide-stage",
    ),
    _ex(
        "blind-stamp",
        "blind stamp",
        150,
        691,
        SECRET_HOMAGE_PHASE,
        "blind-stamp riddim warp",
        BLIND_STAMP_LYRICS,
        recipe="rec_drive_riddim",
        layout="stacked-tower",
    ),
    _ex(
        "cold-cache",
        "cold cache",
        142,
        701,
        SECRET_HOMAGE_PHASE,
        "cold-cache hybrid trap warp",
        COLD_CACHE_LYRICS,
        recipe="rec_drive_through_drop",
        layout="prompt-left",
    ),
    _ex(
        "secret-homage",
        "secret homage",
        140,
        709,
        SECRET_HOMAGE_PHASE,
        "secret-homage dirty dubstep warp",
        SECRET_HOMAGE_LYRICS,
        recipe="rec_drive_dirty_dubstep",
        picks={"bass_low_end": "bass_stacked_808"},
        layout="output-rail",
    ),
)

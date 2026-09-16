"""Wan / LTX / film / audio / inspire sample catalogs.

Imported only by ``_build_sample_catalogs.py``.
"""

from __future__ import annotations

from _build_sample_catalogs import (
    CLAY_FINISH,
    GIF_MOTION,
    GOSEE_IDENTITY,
    I2V_LOCK,
    LAZY_FORGE,
    LTX_A2V,
    LTX_BROLL,
    LTX_DIALOGUE,
    LTX_FLF,
    LTX_HOOK_AV,
    LTX_I2V,
    LTX_MULTISHOT,
    LTX_PRODUCT_HERO,
    LTX_T2V,
    LTX_TALKING_HEAD,
    LTX_WEATHER,
    NO_SCORE,
    RAP_FULL_TAGS,
    RAP_TAGS,
    RESEARCH_DEFAULT,
    STILL_HERE_IDENTITY,
    SWITCHYARD_IDENTITY,
    UNMARKED,
    WAN_I2V,
    WAN_ORBIT,
    WAN_PARALLAX,
    WAN_PUSH,
    WAN_T2V,
    WAN_VACE,
    _ltx_i2v,
    _ltx_t2v,
    _loop,
    _row,
    _wan_i2v,
    _wan_t2v,
)
from ez_music.nodes import DRAFT_LYRICS, FULL_LYRICS
from ez_podcast.nodes import RADIO_SEED_SCRIPT, SEED_SCRIPT


def wan_t2v() -> list[dict[str, str]]:
    return [
        _row("rooftop-dolly", "Rooftop dolly in", WAN_T2V),
        _row(
            "night-rail-pan",
            "Night rail pan",
            _wan_t2v(
                "An original techno wizard in an unmarked sun-washed teal technical running coat with faint circuit-thread seams",
                "stands at a tropical rooftop rail above unmarked glass towers and a dark bay.",
                "Coat hem and glyph motes drift in a warm breeze.",
                "pans left slowly along the rail",
            ),
        ),
        _row(
            "rain-track",
            "Rain tracking",
            _wan_t2v(
                "An original techno wizard in an unmarked teal running coat",
                "walks under a terrace overhang while tropical rain sheets off unmarked glass.",
                "Rain beads roll on fabric.",
                "tracks beside the wizard",
            ),
        ),
        _row(
            "workshop-push",
            "Workshop push-in",
            _wan_t2v(
                "An original techno wizard in an unmarked teal shop coat",
                "leans over a teak bench as warm-gold glyph rings bloom from a compact unmarked data-staff.",
                "Metal filings stay put; rings drift.",
                "dollies in slowly toward the staff",
            ),
        ),
        _row(
            "harbor-fixed",
            "Harbor fixed",
            _wan_t2v(
                "An original techno wizard in an unmarked teal coat",
                "stands on an unmarked concrete pier in fog.",
                "Fog crawls; coat beads.",
                "holds a fixed camera",
            ),
        ),
        _row(
            "ridge-dolly-out",
            "Ridge dolly out",
            _wan_t2v(
                "An original techno wizard in an unmarked teal running coat",
                "walks a high unmarked switchback at first light.",
                "Coat hem lifts in thin air.",
                "dollies out slowly to show the valley",
            ),
        ),
        _row(
            "greenhouse-track",
            "Greenhouse track",
            _wan_t2v(
                "An original techno wizard in an unmarked teal linen coat",
                "walks a long unmarked greenhouse aisle.",
                "Leaves shiver; condensation ticks.",
                "tracks forward down the aisle",
            ),
        ),
        _row(
            "mesa-pan",
            "Mesa pan",
            _wan_t2v(
                "An original techno wizard in an unmarked sun-washed teal coat",
                "stands on a high unmarked mesa at dusk.",
                "Dust motes drift; glyph rings idle.",
                "pans right across the stone",
            ),
        ),
        _row(
            "library-dolly",
            "Library dolly",
            _wan_t2v(
                "An original techno wizard in an unmarked dark teal wool coat",
                "walks between tall unmarked wood stacks.",
                "Dust turns in a window shaft.",
                "dollies in slowly",
            ),
        ),
        _row(
            "platform-track",
            "Platform track",
            _wan_t2v(
                "An original techno wizard in an unmarked teal running coat",
                "walks an unmarked underground platform as a train smear passes far.",
                "Coat hem snaps once.",
                "tracks beside the wizard",
            ),
        ),
        _row(
            "cliff-fixed",
            "Cliff fixed",
            _wan_t2v(
                "An original techno wizard in an unmarked teal coat",
                "stands on an unmarked cliff path above surf.",
                "Wind pulls the coat; spray at the edge.",
                "holds a fixed camera",
            ),
        ),
        _row(
            "snow-pan",
            "Snow pan",
            _wan_t2v(
                "An original techno wizard in an unmarked teal parka",
                "crosses a high unmarked ridge among pines.",
                "Snow sifts; breath shows.",
                "pans left with the walk",
            ),
        ),
        _row(
            "alley-track",
            "Alley track",
            _wan_t2v(
                "An original techno wizard in an unmarked teal coat",
                "walks a narrow unmarked covered alley.",
                "Cloth overhead stirs.",
                "tracks forward",
            ),
        ),
        _row(
            "ferry-dolly",
            "Ferry dolly",
            _wan_t2v(
                "An original techno wizard in an unmarked waxed teal coat",
                "stands at the rail of a small unmarked ferry at dusk.",
                "Water glitter slides; coat hardware dull.",
                "dollies in slowly",
            ),
        ),
        _row(
            "arcade-pan",
            "Arcade pan",
            _wan_t2v(
                "An original techno wizard in an unmarked teal coat",
                "walks an unmarked indoor arcade of colored practicals.",
                "Light shimmer; cabinets blank.",
                "pans right",
            ),
        ),
        _row(
            "courtyard-fixed",
            "Courtyard fixed",
            _wan_t2v(
                "An original techno wizard in an unmarked teal coat",
                "sits at an unmarked stone fountain.",
                "Water beads; palms idle.",
                "holds a fixed camera",
            ),
        ),
        _row(
            "concourse-track",
            "Concourse track",
            _wan_t2v(
                "An original techno wizard in an unmarked teal running coat mid-stride",
                "crosses a vast unmarked concourse.",
                "Far figures smear; the coat stays sharp.",
                "tracks beside the stride",
            ),
        ),
        _row(
            "storm-dolly",
            "Storm dolly",
            _wan_t2v(
                "An original techno wizard in an unmarked charcoal storm-cloak",
                "braces on a tropical rooftop in wind.",
                "Cloak streams; rain ticks stone.",
                "dollies in slowly",
            ),
        ),
        _row(
            "studio-fixed",
            "Studio fixed",
            _wan_t2v(
                "An original techno wizard in an unmarked teal coat",
                "sits at an unmarked teak desk.",
                "Paper stirs once; glyph rings idle.",
                "holds a fixed camera",
            ),
        ),
        _row(
            "observatory-pan",
            "Observatory pan",
            _wan_t2v(
                "An original techno wizard in an unmarked teal coat",
                "stands inside an unmarked dome with a slit of night sky.",
                "Cool moonlight mix; metal ticks.",
                "pans left along the slit",
            ),
        ),
    ]


def wan_i2v() -> list[dict[str, str]]:
    return [
        _row("slow-push", "Slow push-in", WAN_I2V),
        _row(
            "hold-then-push",
            "Hold then push",
            _wan_i2v(
                "The frame holds, then a slow push-in begins. Gentle motion in fabric or foliage.",
                "holds, then dollies in",
            ),
        ),
        _row(
            "gentle-pan-right",
            "Gentle pan right",
            _wan_i2v("Gentle motion in fabric or leaves.", "pans right slowly"),
        ),
        _row(
            "gentle-pan-left",
            "Gentle pan left",
            _wan_i2v("Gentle motion in fabric or leaves.", "pans left slowly"),
        ),
        _row(
            "track-right",
            "Track right",
            _wan_i2v("Gentle subject sway, fabric hush.", "tracks a few degrees right"),
        ),
        _row(
            "track-left",
            "Track left",
            _wan_i2v("Gentle subject sway, fabric hush.", "tracks a few degrees left"),
        ),
        _row(
            "dolly-out",
            "Slow dolly out",
            _wan_i2v("Gentle motion in fabric or foliage.", "dollies out slowly"),
        ),
        _row(
            "fixed-breeze",
            "Fixed breeze",
            _wan_i2v("Locked framing. Gentle cyclic breeze in fabric or leaves.", "holds a fixed camera"),
        ),
        _row(
            "push-lights",
            "Push with lights",
            _wan_i2v("Lights shimmer then settle. Gentle fabric motion.", "dollies in slowly"),
        ),
        _row(
            "rain-hold",
            "Rain hold",
            _wan_i2v("Rain beads on fabric. Gentle head motion only.", "holds a fixed camera"),
        ),
        _row(
            "wind-pan",
            "Wind pan",
            _wan_i2v("A harder breeze pulls coat hem and hair.", "pans right slowly"),
        ),
        _row(
            "breath-push",
            "Breath push",
            _wan_i2v("Subtle breath and fabric hush.", "dollies in slowly"),
        ),
        _row(
            "look-off",
            "Look off then back",
            _wan_i2v("The subject glances off-frame then back. Gentle fabric.", "holds a fixed camera"),
        ),
        _row(
            "staff-idle",
            "Idle staff motes",
            _wan_i2v("Glyph motes drift and settle. Gentle fabric.", "holds a fixed camera"),
        ),
        _row(
            "track-forward",
            "Track forward",
            _wan_i2v("Gentle stride energy without leaving the start pose far.", "tracks forward slowly"),
        ),
        _row(
            "settle-push",
            "Settle then push",
            _wan_i2v("Motion settles, then a slow push-in.", "dollies in slowly"),
        ),
        _row(
            "parallax-slide",
            "Slight slide",
            _wan_i2v(
                "Near fabric drifts against the far plane.",
                "slides a few degrees laterally",
            ),
        ),
        _row(
            "night-hold",
            "Night hold",
            _wan_i2v("Practicals shimmer. Gentle fabric.", "holds a fixed camera"),
        ),
        _row(
            "dawn-push",
            "Dawn push",
            _wan_i2v("Light warms a degree. Gentle fabric.", "dollies in slowly"),
        ),
        _row(
            "storm-cloak",
            "Cloak stream",
            _wan_i2v("Cloak lining streams then settles.", "holds a fixed camera"),
        ),
    ]


def wan_loop() -> list[dict[str, str]]:
    return [
        _row("breeze-cycle", "Breeze cycle", GIF_MOTION),
        _row("leaves-cycle", "Leaves cycle", _loop("Gentle cyclic breeze in leaves. Lights shimmer, then settle.")),
        _row("fabric-cycle", "Fabric cycle", _loop("Coat hem lifts and falls in a cyclic breeze.")),
        _row("curtain-cycle", "Curtain cycle", _loop("A curtain breathes in and out. No walk.")),
        _row("water-cycle", "Water cycle", _loop("Water beads and a fountain pulse, then settle.")),
        _row("lantern-cycle", "Lantern cycle", _loop("Lanterns shimmer, then settle. Fabric hush.")),
        _row("glyph-cycle", "Glyph cycle", _loop("Glyph motes orbit once and return.")),
        _row("rain-cycle", "Rain cycle", _loop("Rain beads form and roll, then the pattern repeats.")),
        _row("fog-cycle", "Fog cycle", _loop("Fog thickens and thins. Fabric hush.")),
        _row("palm-cycle", "Palm cycle", _loop("Palm fronds lift and drop in a cyclic breeze.")),
        _row("steam-cycle", "Steam cycle", _loop("Steam lifts and folds back. No walk.")),
        _row("flag-cycle", "Cloth cycle", _loop("A hanging cloth waves and returns.")),
        _row("spark-cycle", "Spark cycle", _loop("Tiny warm motes rise and fade in place.")),
        _row("shadow-cycle", "Shadow cycle", _loop("Leaf shadow crawls and returns on stone.")),
        _row("neon-cycle", "Practical cycle", _loop("Practicals pulse softly, then settle.")),
        _row("dust-cycle", "Dust cycle", _loop("Dust turns in a window shaft and settles.")),
        _row("wave-cycle", "Surf cycle", _loop("Distant surf pulses. Coat hem cyclic.")),
        _row("snow-cycle", "Snow cycle", _loop("Snow sifts and pauses. Breath cyclic.")),
        _row("heat-cycle", "Heat cycle", _loop("Heat shimmer over stone, then still.")),
        _row("idle-cycle", "Idle cycle", _loop("Tiny fabric and light idle. No walk.")),
    ]


def wan_flf() -> list[dict[str, str]]:
    rows = [
        (
            "hold-travel",
            "Hold then travel",
            f"Hold identity from the first still and travel toward the last-frame pose. One continuous take. {I2V_LOCK} No audio.",
        ),
        (
            "step-through",
            "Step through",
            f"The wizard steps through the terrace toward the last-frame pose as glyph rings bloom and settle. Camera eases with the motion; no cut. {I2V_LOCK} No audio.",
        ),
        (
            "slow-turn",
            "Slow turn",
            f"A slow turn from the first still into the last-frame pose. Fabric hush. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "staff-bloom",
            "Staff bloom",
            f"Glyph rings bloom from the staff while the body travels to the last pose. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "cloak-open",
            "Cloak opens",
            f"The cloak opens on the travel toward the last still. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "rail-walk",
            "Rail walk",
            f"A short walk along the rail from first to last still. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "sit-to-stand",
            "Sit to stand",
            f"Rise from the first pose into the last-frame stand. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "stand-to-sit",
            "Stand to sit",
            f"Settle from the first stand into the last-frame sit. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "look-off-on",
            "Look off then on",
            f"Gaze travels off-frame then lands in the last still. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "weather-shift",
            "Weather shift",
            f"Light and weather ease from the first still toward the last. Body travel small. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "push-with-body",
            "Push with body",
            f"Camera eases in as the body travels to the last pose. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "dolly-out-land",
            "Dolly out land",
            f"Camera eases out as the last pose lands. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "pan-link",
            "Pan link",
            f"A slow pan links first still to last pose. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "track-link",
            "Track link",
            f"A short track links first still to last pose. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "fixed-morph-no",
            "Fixed body travel",
            f"Fixed camera. The body travels to the last pose without a cut. {I2V_LOCK} No audio.",
        ),
        (
            "hands-staff",
            "Hands to staff",
            f"Hands travel to the staff as the last pose lands. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "wind-build",
            "Wind build",
            f"Wind builds from first still to last. Fabric only plus small body travel. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "night-to-dawn",
            "Night toward dawn",
            f"Light eases warmer while the body travels to the last pose. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "indoor-cross",
            "Indoor cross",
            f"A short indoor cross from first still to last pose. No cut. {I2V_LOCK} No audio.",
        ),
        (
            "last-frame-land",
            "Land the last frame",
            f"Ease into the last-frame pose and hold the last frames still. No cut. {I2V_LOCK} No audio.",
        ),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in rows]


def wan_vace() -> list[dict[str, str]]:
    rows = [("join-ab", "Join A to B", WAN_VACE)]
    verbs = [
        ("hold-wardrobe", "Hold wardrobe", "Hold wardrobe and set. Travel toward Shot B first frame."),
        ("short-join", "Short join", "A short 17-frame join. No redesign."),
        ("fabric-bridge", "Fabric bridge", "Fabric motion bridges Shot A last frame to Shot B first frame."),
        ("light-bridge", "Light bridge", "Light eases while identity holds across the join."),
        ("staff-bridge", "Staff bridge", "Staff and glyph rings hold while the join travels."),
        ("cloak-bridge", "Cloak bridge", "Cloak motion bridges the two stills."),
        ("head-turn", "Head turn join", "A small head turn bridges A to B."),
        ("step-join", "Step join", "One step bridges A last frame to B first frame."),
        ("pan-join", "Pan join", "A few degrees of pan during the join."),
        ("push-join", "Push join", "A tiny push-in during the join."),
        ("fixed-join", "Fixed join", "Fixed camera. Identity holds across the join."),
        ("weather-join", "Weather join", "Weather eases; identity holds."),
        ("indoor-join", "Indoor join", "Indoor practicals hold across the join."),
        ("night-join", "Night join", "Night practicals hold across the join."),
        ("dawn-join", "Dawn join", "Dawn light eases across the join."),
        ("crowd-far", "Far crowd join", "Far motion only; identity locked."),
        ("hands-join", "Hands join", "Hands travel slightly; identity locked."),
        ("settle-join", "Settle join", "Motion settles as Shot B lands."),
        ("lock-set", "Lock set join", "Keep every object and surface. Travel toward Shot B."),
    ]
    for sid, label, extra in verbs:
        rows.append(
            (
                sid,
                label,
                f"Hold identity from Shot A last frame and travel toward Shot B first frame. {extra} "
                "One continuous 17-frame join at 24 fps. Keep wardrobe and set locked. Do not redesign.",
            )
        )
    return [_row(sid, label, prompt) for sid, label, prompt in rows]


def wan_orbit() -> list[dict[str, str]]:
    rows = [("slow-orbit-right", "Slow orbit right", WAN_ORBIT)]
    extras = [
        ("orbit-left", "Slow orbit left", "Camera arcs a few degrees left."),
        ("orbit-product", "Product orbit", "Slow orbit around a tabletop product."),
        ("orbit-hero", "Hero orbit", "Slow orbit around the hero identity."),
        ("orbit-still-feet", "Feet locked", "Orbit a few degrees; feet planted."),
        ("orbit-lights", "Lights hold", "Orbit; practicals hold."),
        ("orbit-fabric", "Fabric hush", "Orbit; fabric hush only."),
        ("orbit-staff", "Staff center", "Orbit with the staff as center."),
        ("orbit-mug", "Mug orbit", "Orbit a mug on a table."),
        ("orbit-tight", "Tight orbit", "A very small orbit arc."),
        ("orbit-wide", "Wider arc", "A slightly wider orbit, still one take."),
        ("orbit-night", "Night orbit", "Orbit under night practicals."),
        ("orbit-dawn", "Dawn orbit", "Orbit in first light."),
        ("orbit-rain", "Rain orbit", "Orbit; rain beads hold."),
        ("orbit-indoor", "Indoor orbit", "Orbit in an unmarked room."),
        ("orbit-terrace", "Terrace orbit", "Orbit on a terrace."),
        ("orbit-settle", "Settle at end", "Orbit then settle."),
        ("orbit-no-cut", "No-cut orbit", "One continuous orbit, no cuts."),
        ("orbit-identity", "Identity lock", "Orbit; identity locked hard."),
        ("orbit-table", "Table orbit", "Orbit a tabletop set."),
    ]
    for sid, label, extra in extras:
        rows.append(
            (
                sid,
                label,
                f"{extra} Keep the start-image subject locked. {I2V_LOCK} One continuous ~5 s take, no cuts.",
            )
        )
    return [_row(sid, label, prompt) for sid, label, prompt in rows]


def wan_push_in() -> list[dict[str, str]]:
    rows = [("lab-push", "Lab push-in", WAN_PUSH)]
    extras = [
        ("slow-push", "Very slow push", "Very slow push-in."),
        ("hold-push", "Hold then push", "Hold, then push-in."),
        ("push-eyes", "Push to eyes", "Push-in toward the eyes."),
        ("push-staff", "Push to staff", "Push-in toward the staff."),
        ("push-product", "Push to product", "Push-in toward the product."),
        ("push-mug", "Push to mug", "Push-in toward the mug."),
        ("push-fabric", "Push fabric", "Push-in; fabric hush."),
        ("push-night", "Night push", "Push-in under night practicals."),
        ("push-dawn", "Dawn push", "Push-in in first light."),
        ("push-rain", "Rain push", "Push-in; rain beads."),
        ("push-indoor", "Indoor push", "Push-in in an unmarked room."),
        ("push-terrace", "Terrace push", "Push-in on a terrace."),
        ("push-settle", "Push then settle", "Push-in then settle."),
        ("push-lights", "Push lights", "Push-in; lights shimmer then settle."),
        ("push-breath", "Push breath", "Push-in; subtle breath."),
        ("push-lock", "Hard lock push", "Push-in; identity locked hard."),
        ("push-table", "Table push", "Push-in on a tabletop."),
        ("push-no-walk", "No walk push", "Push-in only. No walk."),
        ("push-end-hold", "End hold", "Push-in and hold the last frames."),
    ]
    for sid, label, extra in extras:
        rows.append(
            (
                sid,
                label,
                f"{extra} Gentle motion in fabric, hair, or foliage. {I2V_LOCK} One continuous five-second take at 24 fps. No audio.",
            )
        )
    return [_row(sid, label, prompt) for sid, label, prompt in rows]


def wan_parallax() -> list[dict[str, str]]:
    rows = [("lab-parallax", "Lab parallax", WAN_PARALLAX)]
    extras = [
        ("slide-right", "Slide right", "Slight slide right."),
        ("slide-left", "Slide left", "Slight slide left."),
        ("near-far", "Near against far", "Near objects drift against the far plane."),
        ("rail-slide", "Rail slide", "Slide along a rail; near posts drift."),
        ("aisle-slide", "Aisle slide", "Slide in an aisle; near leaves drift."),
        ("terrace-slide", "Terrace slide", "Slide on a terrace."),
        ("indoor-slide", "Indoor slide", "Slide indoors; near furniture drifts."),
        ("night-slide", "Night slide", "Slide under night practicals."),
        ("dawn-slide", "Dawn slide", "Slide in first light."),
        ("rain-slide", "Rain slide", "Slide; rain beads hold."),
        ("fog-slide", "Fog slide", "Slide in fog; near posts drift."),
        ("crowd-far", "Far crowd", "Far crowd smears; near identity locked."),
        ("fabric-slide", "Fabric slide", "Slide; fabric hush."),
        ("tiny-slide", "Tiny slide", "A very small lateral slide."),
        ("settle-slide", "Slide then settle", "Slide then settle."),
        ("lock-slide", "Hard lock slide", "Slide; identity locked hard."),
        ("table-slide", "Table slide", "Slide a tabletop; near rim drifts."),
        ("window-slide", "Window slide", "Slide; near frame vs far glass."),
        ("end-hold", "End hold", "Slide and hold the last frames."),
    ]
    for sid, label, extra in extras:
        rows.append(
            (
                sid,
                label,
                f"{extra} Gentle breeze in fabric or leaves. {I2V_LOCK} One continuous five-second take at 24 fps. No audio.",
            )
        )
    return [_row(sid, label, prompt) for sid, label, prompt in rows]


def ltx_t2v() -> list[dict[str, str]]:
    return [
        _row("rooftop-av", "Rooftop AV", LTX_T2V),
        _row(
            "night-rail",
            "Night rail AV",
            _ltx_t2v(
                "A wide photoreal shot of a tropical rooftop rail at night. An original techno wizard in an unmarked teal running coat stands as glyph rings idle.",
                "Warm lanterns and distant traffic sit under a single glyph chime.",
                "The camera pans left slowly along the rail.",
            ),
        ),
        _row(
            "rain-terrace",
            "Rain terrace AV",
            _ltx_t2v(
                "A photoreal shot of tropical rain sheeting off unmarked glass while a techno wizard waits under an overhang.",
                "Rain on glass and stone ticks; a warm breeze under the roof.",
                "The camera holds, then eases in.",
            ),
        ),
        _row(
            "workshop",
            "Workshop AV",
            _ltx_t2v(
                "A photoreal shot of a teak workbench as glyph rings bloom from a compact unmarked data-staff.",
                "A lamp hum and a single metal tick sit under a glyph chime.",
                "The camera dollies in slowly.",
            ),
        ),
        _row(
            "harbor-fog",
            "Harbor fog AV",
            _ltx_t2v(
                "A photoreal shot of an unmarked pier in fog. A techno wizard in a teal coat stands at the edge.",
                "Fog hush, water lap, distant horn far off — not a carrier identity.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "ridge-dawn",
            "Ridge dawn AV",
            _ltx_t2v(
                "A photoreal shot of a high unmarked switchback at first light. A techno wizard walks.",
                "Thin wind and grit under footfalls. No speech.",
                "The camera tracks beside the walk.",
            ),
        ),
        _row(
            "greenhouse",
            "Greenhouse AV",
            _ltx_t2v(
                "A photoreal shot down an unmarked greenhouse aisle of palms.",
                "Condensation ticks, leaves rustle, a distant drip.",
                "The camera tracks forward.",
            ),
        ),
        _row(
            "mesa-dusk",
            "Mesa dusk AV",
            _ltx_t2v(
                "A photoreal shot of a high unmarked mesa at dusk. Glyph rings idle.",
                "Dry wind and grit. A faint glyph chime.",
                "The camera pans right.",
            ),
        ),
        _row(
            "library",
            "Library AV",
            _ltx_t2v(
                "A photoreal shot between unmarked wood stacks.",
                "Paper hush, a distant chair, no speech.",
                "The camera dollies in slowly.",
            ),
        ),
        _row(
            "platform",
            "Platform AV",
            _ltx_t2v(
                "A photoreal shot of an unmarked underground platform as a train smear passes far.",
                "Rail rumble far off, coat snap, no speech.",
                "The camera tracks beside the wizard.",
            ),
        ),
        _row(
            "cliff",
            "Cliff AV",
            _ltx_t2v(
                "A photoreal shot of an unmarked cliff path above surf.",
                "Wind and surf. Fabric snap.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "snow",
            "Snow ridge AV",
            _ltx_t2v(
                "A photoreal shot of a high unmarked snow ridge among pines.",
                "Thin wind, snow sift, close breath. No speech.",
                "The camera pans left.",
            ),
        ),
        _row(
            "alley",
            "Alley AV",
            _ltx_t2v(
                "A photoreal shot down a narrow unmarked covered alley.",
                "Cloth stir, distant steps, no speech.",
                "The camera tracks forward.",
            ),
        ),
        _row(
            "ferry",
            "Ferry AV",
            _ltx_t2v(
                "A photoreal shot at the rail of a small unmarked ferry at dusk.",
                "Water slap, a single bell far off, no speech.",
                "The camera dollies in slowly.",
            ),
        ),
        _row(
            "arcade",
            "Arcade AV",
            _ltx_t2v(
                "A photoreal shot of an unmarked indoor arcade of colored practicals.",
                "Soft cabinet hum, shoe hush, no speech.",
                "The camera pans right.",
            ),
        ),
        _row(
            "courtyard",
            "Courtyard AV",
            _ltx_t2v(
                "A photoreal shot of an unmarked stone fountain in a quiet courtyard.",
                "Water beads, palm rustle, no speech.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "concourse",
            "Concourse AV",
            _ltx_t2v(
                "A photoreal shot of a vast unmarked concourse, wizard mid-stride.",
                "Far crowd hush, shoe strikes, no speech.",
                "The camera tracks beside the stride.",
            ),
        ),
        _row(
            "storm",
            "Storm rooftop AV",
            _ltx_t2v(
                "A photoreal shot of a tropical rooftop in wind. A storm-cloak streams.",
                "Wind, rain on stone, close breath. No speech.",
                "The camera dollies in slowly.",
            ),
        ),
        _row(
            "studio",
            "Studio AV",
            _ltx_t2v(
                "A photoreal shot of an unmarked teak desk, glyph rings idle.",
                "Room tone, a paper tick, no speech.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "observatory",
            "Observatory AV",
            _ltx_t2v(
                "A photoreal shot inside an unmarked dome with a slit of night sky.",
                "Metal tick, thin wind at the slit, no speech.",
                "The camera pans left.",
            ),
        ),
    ]


def ltx_i2v() -> list[dict[str, str]]:
    return [
        _row("start-push", "Start-image push", LTX_I2V),
        _row(
            "hold-push",
            "Hold then push",
            _ltx_i2v(
                "The camera holds, then eases in. Fabric or foliage drifts.",
                "Light wind and world SFX matching the start image sit under the action.",
                "Slow push-in.",
            ),
        ),
        _row(
            "pan-right",
            "Pan right",
            _ltx_i2v(
                "Fabric drifts. World SFX matching the start image.",
                "A warm breeze sits under the pan.",
                "The camera pans right slowly.",
            ),
        ),
        _row(
            "pan-left",
            "Pan left",
            _ltx_i2v(
                "Fabric drifts. World SFX matching the start image.",
                "A warm breeze sits under the pan.",
                "The camera pans left slowly.",
            ),
        ),
        _row(
            "fixed-breeze",
            "Fixed breeze",
            _ltx_i2v(
                "Locked framing. Gentle cyclic breeze in fabric or leaves.",
                "World SFX matching the start image.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "track-right",
            "Track right",
            _ltx_i2v(
                "Gentle subject sway.",
                "World SFX matching the start image.",
                "The camera tracks a few degrees right.",
            ),
        ),
        _row(
            "dolly-out",
            "Dolly out",
            _ltx_i2v(
                "Fabric hush as the frame widens a little.",
                "World SFX matching the start image.",
                "The camera dollies out slowly.",
            ),
        ),
        _row(
            "rain-hold",
            "Rain hold",
            _ltx_i2v(
                "Rain beads on fabric. Gentle head motion only.",
                "Rain ticks matching the start image.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "night-hold",
            "Night hold",
            _ltx_i2v(
                "Practicals shimmer. Gentle fabric.",
                "World SFX matching the start image.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "dawn-push",
            "Dawn push",
            _ltx_i2v(
                "Light warms a degree. Gentle fabric.",
                "World SFX matching the start image.",
                "The camera dollies in slowly.",
            ),
        ),
        _row(
            "breath-close",
            "Close breath",
            _ltx_i2v(
                "Subtle breath and fabric hush.",
                "Close-mic breath under world SFX matching the start image.",
                "The camera holds, then eases in.",
            ),
        ),
        _row(
            "look-off",
            "Look off",
            _ltx_i2v(
                "The subject glances off-frame then back. Mouth closed.",
                "World SFX matching the start image. No speech.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "staff-motes",
            "Staff motes",
            _ltx_i2v(
                "Glyph motes drift and settle.",
                "A single glyph chime under world SFX matching the start image.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "wind-pan",
            "Wind pan",
            _ltx_i2v(
                "A harder breeze pulls coat hem.",
                "Wind matching the start image.",
                "The camera pans right slowly.",
            ),
        ),
        _row(
            "track-forward",
            "Track forward",
            _ltx_i2v(
                "Gentle stride energy without leaving the start pose far.",
                "World SFX matching the start image.",
                "The camera tracks forward slowly.",
            ),
        ),
        _row(
            "settle",
            "Settle",
            _ltx_i2v(
                "Motion settles. Last frames hold.",
                "World SFX matching the start image.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "parallax",
            "Slight parallax",
            _ltx_i2v(
                "Near fabric drifts against the far plane.",
                "World SFX matching the start image.",
                "The camera slides a few degrees laterally.",
            ),
        ),
        _row(
            "cloak-stream",
            "Cloak stream",
            _ltx_i2v(
                "Cloak lining streams then settles.",
                "Wind matching the start image.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "indoor-hush",
            "Indoor hush",
            _ltx_i2v(
                "Room tone. Tiny fabric.",
                "Room tone matching the start image.",
                "The camera dollies in slowly.",
            ),
        ),
        _row(
            "end-hold",
            "End hold",
            _ltx_i2v(
                "A small move then the last frames hold still for the next I2V.",
                "World SFX matching the start image.",
                "The camera eases then holds.",
            ),
        ),
    ]


def ltx_broll() -> list[dict[str, str]]:
    return [
        _row("terrace-ambient", "Terrace ambient", LTX_BROLL),
        _row("storm-weather", "Storm weather", LTX_WEATHER),
        _row(
            "interior-room",
            "Interior room tone",
            _ltx_t2v(
                "Locked-camera ambient interior of an unmarked teak room. Curtain breath, dust in a window shaft.",
                "Room tone, a distant drip, fabric hush.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "palm-lock",
            "Palm lock",
            _ltx_t2v(
                "Locked-camera palms on an unmarked terrace.",
                "Palm rustle and a warm breeze.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "rain-glass",
            "Rain on glass",
            _ltx_t2v(
                "Locked-camera rain sheeting on unmarked glass.",
                "Rain on glass, thunder far off.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "harbor-lap",
            "Harbor lap",
            _ltx_t2v(
                "Locked-camera unmarked pier, water lap in fog.",
                "Water lap, fog hush.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "fountain",
            "Fountain",
            _ltx_t2v(
                "Locked-camera unmarked stone fountain.",
                "Water beads, courtyard hush.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "workshop-idle",
            "Workshop idle",
            _ltx_t2v(
                "Locked-camera teak bench, glyph motes idle.",
                "Lamp hum, a single metal tick.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "night-lanterns",
            "Night lanterns",
            _ltx_t2v(
                "Locked-camera terrace lanterns at night.",
                "Insect hush, distant traffic.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "dawn-ridge",
            "Dawn ridge wind",
            _ltx_t2v(
                "Locked-camera high unmarked ridge at first light.",
                "Thin wind, grit.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "snow-sift",
            "Snow sift",
            _ltx_t2v(
                "Locked-camera pines, snow sift.",
                "Thin wind, snow.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "arcade-hum",
            "Arcade hum",
            _ltx_t2v(
                "Locked-camera unmarked arcade practicals.",
                "Soft cabinet hum.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "ferry-water",
            "Ferry water",
            _ltx_t2v(
                "Locked-camera unmarked ferry rail, water glitter.",
                "Water slap, a distant bell.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "concourse-hush",
            "Concourse hush",
            _ltx_t2v(
                "Locked-camera unmarked concourse, far figures.",
                "Far crowd hush.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "library-dust",
            "Library dust",
            _ltx_t2v(
                "Locked-camera unmarked stacks, dust in a shaft.",
                "Paper hush.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "greenhouse-drip",
            "Greenhouse drip",
            _ltx_t2v(
                "Locked-camera unmarked greenhouse aisle.",
                "Drip, leaf rustle.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "mesa-wind",
            "Mesa wind",
            _ltx_t2v(
                "Locked-camera unmarked mesa at dusk.",
                "Dry wind, grit.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "studio-paper",
            "Studio paper",
            _ltx_t2v(
                "Locked-camera unmarked teak desk, paper stir.",
                "Room tone, paper tick.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "cloak-idle",
            "Cloak idle",
            _ltx_t2v(
                "Locked-camera storm-cloak on a rail, lining idle.",
                "Wind, fabric hush.",
                "The camera holds a fixed frame.",
            ),
        ),
        _row(
            "glyph-idle",
            "Glyph idle",
            _ltx_t2v(
                "Locked-camera compact unmarked data-staff, motes idle.",
                "A single glyph chime, then hush.",
                "The camera holds a fixed frame.",
            ),
        ),
    ]


def ltx_hook() -> list[dict[str, str]]:
    extras = [
        ("cold-open", "Cold open", LTX_HOOK_AV),
        (
            "snap-in",
            "Snap in",
            _ltx_i2v(
                "Camera snaps to the start-image subject with fast present-tense energy.",
                "World SFX matching the start image.",
                "A short aggressive push.",
            ),
        ),
        (
            "drop-in",
            "Drop in",
            _ltx_i2v(
                "The frame drops in on the subject already in motion.",
                "World SFX matching the start image.",
                "Fast present-tense energy, then hold.",
            ),
        ),
        (
            "turn-to-lens",
            "Turn to lens",
            _ltx_i2v(
                "The subject turns toward lens with bright eyes. Mouth closed.",
                "World SFX matching the start image. No speech.",
                "A short push-in.",
            ),
        ),
        (
            "staff-flash",
            "Staff flash",
            _ltx_i2v(
                "Glyph rings flash once then settle.",
                "A glyph chime under world SFX matching the start image.",
                "Hold then a short push.",
            ),
        ),
        (
            "cloak-snap",
            "Cloak snap",
            _ltx_i2v(
                "The cloak snaps in wind, then the frame holds.",
                "Wind matching the start image.",
                "Fast energy, then hold.",
            ),
        ),
        (
            "sprint-energy",
            "Sprint energy",
            _ltx_i2v(
                "Already-in-motion energy without leaving identity.",
                "Footfalls and breath matching the start image. No speech.",
                "Tracking energy, then hold.",
            ),
        ),
        (
            "night-flash",
            "Night flash",
            _ltx_i2v(
                "Night practicals flare once.",
                "World SFX matching the start image.",
                "Snap energy, then hold.",
            ),
        ),
        (
            "rain-hit",
            "Rain hit",
            _ltx_i2v(
                "A rain sheet hits glass, then the subject holds.",
                "Rain matching the start image.",
                "Snap energy, then hold.",
            ),
        ),
        (
            "look-up",
            "Look up",
            _ltx_i2v(
                "The subject looks up fast, then holds. Mouth closed.",
                "World SFX matching the start image. No speech.",
                "Short push-in.",
            ),
        ),
        (
            "hands-free",
            "Hands free",
            _ltx_i2v(
                "Empty palms flash into frame, then settle.",
                "World SFX matching the start image.",
                "Snap energy, then hold.",
            ),
        ),
        (
            "bay-reveal",
            "Bay reveal",
            _ltx_i2v(
                "A tiny pan reveals more bay, then holds.",
                "World SFX matching the start image.",
                "Fast pan, then hold.",
            ),
        ),
        (
            "glyph-rise",
            "Glyph rise",
            _ltx_i2v(
                "Glyph motes rise once and settle.",
                "A glyph chime under world SFX matching the start image.",
                "Hold.",
            ),
        ),
        (
            "wind-hit",
            "Wind hit",
            _ltx_i2v(
                "A wind hit pulls fabric, then settles.",
                "Wind matching the start image.",
                "Snap, then hold.",
            ),
        ),
        (
            "step-in",
            "Step in",
            _ltx_i2v(
                "One step into the lens, then hold.",
                "A footfall under world SFX matching the start image.",
                "Short push with the step.",
            ),
        ),
        (
            "eye-catch",
            "Eye catch",
            _ltx_i2v(
                "Eyes catch the lens, then hold. Mouth closed.",
                "World SFX matching the start image. No speech.",
                "Short push-in.",
            ),
        ),
        (
            "storm-open",
            "Storm open",
            _ltx_i2v(
                "Lightning far off, then the subject holds.",
                "Thunder far off under world SFX matching the start image.",
                "Snap, then hold.",
            ),
        ),
        (
            "quiet-open",
            "Quiet open",
            _ltx_i2v(
                "Almost still, then one precise move.",
                "Room tone matching the start image, then a tick.",
                "Hold, then a tiny push.",
            ),
        ),
        (
            "end-hold-hook",
            "End hold hook",
            _ltx_i2v(
                "Fast energy in the first seconds, last frames hold for the next shot.",
                "World SFX matching the start image.",
                "Snap then hold.",
            ),
        ),
        (
            "vertical-energy",
            "Vertical energy",
            _ltx_i2v(
                "Vertical Shorts energy, subject large, then hold.",
                "World SFX matching the start image.",
                "Short push-in.",
            ),
        ),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in extras]


def ltx_dialogue() -> list[dict[str, str]]:
    lines = [
        ("tools-here", "Tools are here", LTX_DIALOGUE),
        (
            "use-them-well",
            "Use them well",
            'A medium photoreal shot of a tropical rooftop terrace at golden hour. An original techno wizard in an unmarked teal running coat turns toward lens and says, "Use the tools in front of you well." A warm terrace breeze and palm rustle sit under the voice, then a glyph chime. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "stay-on-box",
            "Stay on the box",
            'A medium photoreal shot at an unmarked teak desk. The wizard looks to lens and says, "Stay on the machine in front of us." Room tone under a close voice. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "weights-local",
            "Weights stay local",
            'A medium photoreal shot on a terrace at night. The wizard says, "The weights stay on this box." Lantern hush under the voice, then a glyph chime. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "cut-is-ours",
            "The cut is ours",
            'A medium photoreal shot in an unmarked workshop. The wizard says, "If it ships from here, the cut is ours." A lamp hum under the voice. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "no-rented-beat",
            "No rented beat",
            'A medium photoreal shot at a teak bench. The wizard says, "No rented beat. The booth is local." Room tone under the voice. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "card-hot",
            "Card runs hot",
            'A medium photoreal shot, coat hem in a breeze. The wizard says, "The card runs hot. That is the point." Wind under the voice. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "own-the-silence",
            "Own the silence",
            'A medium photoreal shot at a fountain. The wizard says, "Own the silence between the words." Water beads under the voice. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "one-job",
            "One job",
            'A medium photoreal shot on a ridge. The wizard says, "One job on this box. Then we stop." Thin wind under the voice. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "look-twice",
            "Look twice",
            'A medium photoreal shot at unmarked glass. The wizard says, "Look twice before you print." Distant traffic under the voice. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "keep-the-bible",
            "Keep the bible",
            'A medium photoreal shot in an unmarked study. The wizard says, "Keep the bible. Change only the shot." Paper hush under the voice. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "hands-free",
            "Hands stay free",
            'A medium photoreal shot, empty palms visible. The wizard says, "Hands stay free. The staff is enough." Fabric hush under the voice. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "print-later",
            "Print later",
            'A medium photoreal shot at first light. The wizard says, "Write cheap. Print later." Soft wind under the voice. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "no-score-line",
            "World only",
            'A medium photoreal shot on a terrace. The wizard says, "World sound only. Let the street talk." Palm rustle under the voice. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "fog-line",
            "Fog line",
            'A medium photoreal shot on an unmarked pier. The wizard says, "The harbor will wait." Water lap under the voice. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "rain-line",
            "Rain line",
            'A medium photoreal shot under an overhang. The wizard says, "Let the rain stem-mix the take." Rain on glass under the voice. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "night-line",
            "Night line",
            'A medium photoreal shot under lanterns. The wizard says, "Hold the last frame." Insect hush under the voice. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "desk-line",
            "Desk line",
            'A medium photoreal shot at a blank notebook. The wizard says, "The notebook stays empty until the shot is true." Room tone under the voice. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "staff-line",
            "Staff line",
            'A medium photoreal shot, glyph rings idle. The wizard says, "The staff is a tool, not a trick." A glyph chime after the line. Unmarked surfaces. No music and no score. Five seconds.',
        ),
        (
            "close-line",
            "Close line",
            'A medium close photoreal shot. The wizard says, "We are already at the work." Close voice, world SFX under. Unmarked surfaces. No music and no score. Five seconds.',
        ),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in lines]


def ltx_multishot() -> list[dict[str, str]]:
    rows = [("terrace-cuts", "Terrace hard cuts", LTX_MULTISHOT)]
    extras = [
        (
            "wide-close-bay",
            "Wide / close / bay",
            "A wide photoreal terrace at golden hour, breeze under traffic. A hard cut to a medium close-up of glyph rings, breeze continuing. A match cut to a low wide of the bay, a glyph chime. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "workshop-cuts",
            "Workshop cuts",
            "A wide photoreal workshop, lamp hum. A hard cut to hands on a compact unmarked data-staff. A match cut to the full bench as a metal tick lands. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "rain-cuts",
            "Rain cuts",
            "A wide photoreal rain terrace. A hard cut to rain on glass. A match cut back to the wizard under the overhang, rain continuing. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "night-cuts",
            "Night cuts",
            "A wide photoreal night rail. A hard cut to lantern bokeh. A match cut to the wizard at the glass, traffic muffled. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "harbor-cuts",
            "Harbor cuts",
            "A wide photoreal pier in fog. A hard cut to water lap. A match cut to the coat at the rail, fog continuing. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "ridge-cuts",
            "Ridge cuts",
            "A wide photoreal switchback. A hard cut to boots on grit. A match cut to the valley slot, wind continuing. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "library-cuts",
            "Library cuts",
            "A wide photoreal stacks. A hard cut to a hand on wood. A match cut to the aisle, paper hush continuing. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "platform-cuts",
            "Platform cuts",
            "A wide photoreal platform. A hard cut to a train smear. A match cut to the wizard waiting, rumble continuing. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "greenhouse-cuts",
            "Greenhouse cuts",
            "A wide photoreal aisle. A hard cut to a leaf. A match cut to the far glass, drip continuing. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "mesa-cuts",
            "Mesa cuts",
            "A wide photoreal mesa at dusk. A hard cut to glyph motes. A match cut to the horizon, wind continuing. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "ferry-cuts",
            "Ferry cuts",
            "A wide photoreal ferry rail. A hard cut to water glitter. A match cut to the coat hardware, water slap continuing. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "arcade-cuts",
            "Arcade cuts",
            "A wide photoreal arcade. A hard cut to blank cabinets. A match cut to the wizard walking, hum continuing. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "courtyard-cuts",
            "Courtyard cuts",
            "A wide photoreal courtyard. A hard cut to fountain water. A match cut to the seated wizard, water continuing. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "concourse-cuts",
            "Concourse cuts",
            "A wide photoreal concourse. A hard cut to shoes. A match cut to the stride, hush continuing. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "storm-cuts",
            "Storm cuts",
            "A wide photoreal rooftop in wind. A hard cut to cloak lining. A match cut to the gap ahead, wind continuing. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "studio-cuts",
            "Studio cuts",
            "A wide photoreal desk. A hard cut to a blank notebook. A match cut to the idle staff, room tone continuing. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "snow-cuts",
            "Snow cuts",
            "A wide photoreal snow ridge. A hard cut to breath. A match cut to pines, wind continuing. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "observatory-cuts",
            "Observatory cuts",
            "A wide photoreal dome. A hard cut to the sky slit. A match cut to the wizard, metal tick continuing. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
        (
            "audio-continues",
            "Audio continues",
            "A wide photoreal terrace. A hard cut to a close-up; breeze continues across the cut. A match cut to the bay; a glyph chime. Mouth closed. Unmarked surfaces. No music and no score. Five seconds.",
        ),
    ]
    rows.extend(extras)
    return [_row(sid, label, prompt) for sid, label, prompt in rows]


def ltx_product() -> list[dict[str, str]]:
    extras = [
        ("orbit-tick", "Orbit and glass tick", LTX_PRODUCT_HERO),
        (
            "orbit-left",
            "Orbit left",
            _ltx_i2v(
                "The camera orbits a few degrees left around the product on the table.",
                "Soft room tone, a glass tick, a fabric hush.",
                "Slow orbit left.",
            ),
        ),
        (
            "push-product",
            "Push to product",
            _ltx_i2v(
                "The camera eases in toward the product. Identity locked.",
                "Soft room tone, a fabric hush.",
                "Slow push-in.",
            ),
        ),
        (
            "fixed-shimmer",
            "Fixed shimmer",
            _ltx_i2v(
                "Locked camera. A light shimmer on glaze.",
                "Soft room tone.",
                "Fixed camera.",
            ),
        ),
        (
            "slide-rim",
            "Slide along rim",
            _ltx_i2v(
                "A slight lateral slide so the rim drifts against the far plane.",
                "Soft room tone, a glass tick.",
                "Slight slide.",
            ),
        ),
        (
            "mug-chip",
            "Mug chip",
            _ltx_i2v(
                "Orbit a few degrees around a chipped ceramic mug.",
                "Soft room tone, a ceramic tick.",
                "Slow orbit right.",
            ),
        ),
        (
            "staff-table",
            "Staff on table",
            _ltx_i2v(
                "Orbit a compact unmarked data-staff on pale stone. Motes idle.",
                "Soft room tone, a glyph chime once.",
                "Slow orbit right.",
            ),
        ),
        (
            "bottle-caustic",
            "Bottle caustic",
            _ltx_i2v(
                "Orbit a clear unmarked carafe. Caustics crawl.",
                "Soft room tone, a glass tick.",
                "Slow orbit right.",
            ),
        ),
        (
            "bowl-water",
            "Bowl water",
            _ltx_i2v(
                "Locked camera. Water in a stone bowl ticks once.",
                "Soft room tone, a water tick.",
                "Fixed camera.",
            ),
        ),
        (
            "notebook",
            "Notebook",
            _ltx_i2v(
                "A tiny push toward an unmarked linen notebook.",
                "Soft room tone, a paper tick.",
                "Slow push-in.",
            ),
        ),
        (
            "lantern",
            "Lantern",
            _ltx_i2v(
                "Orbit an unmarked brass lantern, unlit.",
                "Soft room tone, a metal tick.",
                "Slow orbit right.",
            ),
        ),
        (
            "glove-pair",
            "Glove pair",
            _ltx_i2v(
                "A slight slide across blank matte gloves.",
                "Soft room tone, a fabric hush.",
                "Slight slide.",
            ),
        ),
        (
            "vase",
            "Vase",
            _ltx_i2v(
                "Orbit an unmarked sand ceramic vase.",
                "Soft room tone.",
                "Slow orbit left.",
            ),
        ),
        (
            "flask",
            "Flask",
            _ltx_i2v(
                "Orbit an unmarked brushed-steel flask.",
                "Soft room tone, a metal tick.",
                "Slow orbit right.",
            ),
        ),
        (
            "planter",
            "Planter",
            _ltx_i2v(
                "Locked camera. A palm pup leaf ticks.",
                "Soft room tone, a leaf tick.",
                "Fixed camera.",
            ),
        ),
        (
            "coat-peg",
            "Coat on peg",
            _ltx_i2v(
                "Fabric on a peg breathes. Tiny push.",
                "Soft room tone, a fabric hush.",
                "Slow push-in.",
            ),
        ),
        (
            "two-mugs",
            "Two mugs",
            _ltx_i2v(
                "Orbit a pair of unmarked stone mugs.",
                "Soft room tone, a ceramic tick.",
                "Slow orbit right.",
            ),
        ),
        (
            "rope",
            "Rope coil",
            _ltx_i2v(
                "A slight slide across an unmarked rope coil.",
                "Soft room tone, a fiber hush.",
                "Slight slide.",
            ),
        ),
        (
            "ink-pot",
            "Ink pot",
            _ltx_i2v(
                "Locked camera. A dip pen shadow crawls.",
                "Soft room tone.",
                "Fixed camera.",
            ),
        ),
        (
            "end-hold-product",
            "End hold",
            _ltx_i2v(
                "A small orbit then the last frames hold.",
                "Soft room tone, a glass tick.",
                "Orbit then hold.",
            ),
        ),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in extras]


def ltx_flf() -> list[dict[str, str]]:
    extras = [
        ("step-through", "Step through", LTX_FLF),
        (
            "ease-last",
            "Ease to last",
            _ltx_i2v(
                "The first frame holds, then the body eases toward the last-frame pose. No cut.",
                "A warm breeze and palm rustle, then a glyph chime as the last frame lands.",
                "Camera eases with the motion.",
            ),
        ),
        (
            "turn-last",
            "Turn to last",
            _ltx_i2v(
                "A slow turn from the first still into the last-frame pose. No cut.",
                "World SFX matching both stills, then a glyph chime.",
                "Camera eases with the turn.",
            ),
        ),
        (
            "staff-last",
            "Staff to last",
            _ltx_i2v(
                "Glyph rings bloom as the last pose lands. No cut.",
                "A glyph chime as the last frame lands.",
                "Camera eases in.",
            ),
        ),
        (
            "cloak-last",
            "Cloak to last",
            _ltx_i2v(
                "The cloak opens on the travel toward the last still. No cut.",
                "Wind matching the stills.",
                "Camera eases with the motion.",
            ),
        ),
        (
            "rail-last",
            "Rail to last",
            _ltx_i2v(
                "A short walk along the rail from first to last still. No cut.",
                "Footfalls and breeze, then a chime.",
                "Camera tracks with the walk.",
            ),
        ),
        (
            "sit-last",
            "Sit to last",
            _ltx_i2v(
                "Rise or settle between the two stills. No cut.",
                "Room tone, fabric hush, then a tick.",
                "Camera holds then eases.",
            ),
        ),
        (
            "weather-last",
            "Weather to last",
            _ltx_i2v(
                "Light and weather ease from first still toward last. Small body travel. No cut.",
                "World SFX matching the stills.",
                "Camera holds.",
            ),
        ),
        (
            "push-last",
            "Push to last",
            _ltx_i2v(
                "Camera eases in as the last pose lands. No cut.",
                "World SFX, then a glyph chime.",
                "Slow push-in.",
            ),
        ),
        (
            "dolly-last",
            "Dolly to last",
            _ltx_i2v(
                "Camera eases out as the last pose lands. No cut.",
                "World SFX matching the stills.",
                "Slow dolly out.",
            ),
        ),
        (
            "pan-last",
            "Pan to last",
            _ltx_i2v(
                "A slow pan links first still to last pose. No cut.",
                "World SFX matching the stills.",
                "Slow pan.",
            ),
        ),
        (
            "fixed-last",
            "Fixed to last",
            _ltx_i2v(
                "Fixed camera. The body travels to the last pose. No cut.",
                "World SFX matching the stills.",
                "Fixed camera.",
            ),
        ),
        (
            "hands-last",
            "Hands to last",
            _ltx_i2v(
                "Hands travel to the staff as the last pose lands. No cut.",
                "A fabric hush, then a chime.",
                "Camera eases in.",
            ),
        ),
        (
            "wind-last",
            "Wind to last",
            _ltx_i2v(
                "Wind builds from first still to last. No cut.",
                "Wind matching the stills.",
                "Camera holds.",
            ),
        ),
        (
            "night-last",
            "Night to last",
            _ltx_i2v(
                "Light eases while the body travels to the last pose. No cut.",
                "Night world SFX matching the stills.",
                "Camera eases.",
            ),
        ),
        (
            "indoor-last",
            "Indoor to last",
            _ltx_i2v(
                "A short indoor cross from first still to last pose. No cut.",
                "Room tone matching the stills.",
                "Camera eases.",
            ),
        ),
        (
            "rain-last",
            "Rain to last",
            _ltx_i2v(
                "Rain holds while the body travels to the last pose. No cut.",
                "Rain matching the stills.",
                "Camera holds.",
            ),
        ),
        (
            "fog-last",
            "Fog to last",
            _ltx_i2v(
                "Fog eases while the last pose lands. No cut.",
                "Fog hush matching the stills.",
                "Camera eases in.",
            ),
        ),
        (
            "chime-last",
            "Chime on last",
            _ltx_i2v(
                "Travel to the last pose. A glyph chime as the last frame lands. No cut.",
                "World SFX, then a glyph chime.",
                "Camera eases with the motion.",
            ),
        ),
        (
            "hold-last",
            "Hold last frames",
            _ltx_i2v(
                "Ease into the last-frame pose and hold the last frames still. No cut.",
                "World SFX matching the stills.",
                "Camera eases then holds.",
            ),
        ),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in extras]


def ltx_a2v() -> list[dict[str, str]]:
    extras = [
        ("listen-move", "Listen and move", LTX_A2V),
        (
            "head-nod",
            "Head nod",
            _ltx_i2v(
                "The subject listens and nods with the loaded soundtrack. Modest head motion, fabric hush, locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "sway",
            "Sway",
            _ltx_i2v(
                "The subject sways with the loaded clip. Fabric hush. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "hands",
            "Hands with the bed",
            _ltx_i2v(
                "Hands move with the loaded clip. Modest motion. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "breath",
            "Breath with the bed",
            _ltx_i2v(
                "Breath and tiny head motion with the loaded clip. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "look-off-a2v",
            "Look off",
            _ltx_i2v(
                "The subject looks off-frame with the loaded clip, then back. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "staff-idle-a2v",
            "Staff idle",
            _ltx_i2v(
                "Glyph motes idle with the loaded clip. Modest body motion. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "sit-listen",
            "Sit and listen",
            _ltx_i2v(
                "Seated listen. Modest head motion with the loaded clip. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "stand-listen",
            "Stand and listen",
            _ltx_i2v(
                "Standing listen. Modest sway with the loaded clip. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "tiny-push",
            "Tiny push",
            _ltx_i2v(
                "A tiny push-in while the subject listens to the loaded clip. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Slow push-in.",
            ),
        ),
        (
            "hold-freeze",
            "Hold freeze",
            _ltx_i2v(
                "Almost still. Picture follows the loaded clip. Locked wardrobe and set. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "fabric-only",
            "Fabric only",
            _ltx_i2v(
                "Fabric hush with the loaded clip. Body almost still. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "night-listen",
            "Night listen",
            _ltx_i2v(
                "Night practicals. Modest head motion with the loaded clip. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "rain-listen",
            "Rain listen",
            _ltx_i2v(
                "Rain beads. Modest motion with the loaded clip. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "desk-listen",
            "Desk listen",
            _ltx_i2v(
                "At a desk. Modest head motion with the loaded clip. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "rail-listen",
            "Rail listen",
            _ltx_i2v(
                "At a rail. Modest sway with the loaded clip. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "eyes-closed",
            "Eyes closed",
            _ltx_i2v(
                "Eyes close then open with the loaded clip. Modest motion. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "shoulder",
            "Shoulder roll",
            _ltx_i2v(
                "A small shoulder roll with the loaded clip. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
        (
            "end-still",
            "End still",
            _ltx_i2v(
                "Motion with the loaded clip, last frames still. Locked wardrobe and set. Picture follows the audio. Mouths will not match.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera then hold.",
            ),
        ),
        (
            "no-extra-score",
            "No extra score",
            _ltx_i2v(
                "The subject listens and moves with the loaded soundtrack only. Locked wardrobe and set. Picture follows the audio. Mouths will not match. No extra music.",
                "Use the loaded clip; do not invent a score.",
                "Fixed camera.",
            ),
        ),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in extras]


def ltx_talking() -> list[dict[str, str]]:
    extras = [
        ("hold-speaks", "Hold and speak", LTX_TALKING_HEAD),
        (
            "one-line",
            "One short line",
            _ltx_i2v(
                "The subject holds still and speaks one short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "nod-line",
            "Nod then line",
            _ltx_i2v(
                "A small nod, then one short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "look-lens-line",
            "Look to lens",
            _ltx_i2v(
                "The subject looks to lens and speaks one short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "look-off-line",
            "Look off, line",
            _ltx_i2v(
                "The subject looks off-frame, then speaks one short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "breath-line",
            "Breath then line",
            _ltx_i2v(
                "A breath, then one short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "hands-still",
            "Hands still",
            _ltx_i2v(
                "Hands still. One short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "tiny-push-line",
            "Tiny push, line",
            _ltx_i2v(
                "A tiny push-in while the subject speaks one short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Slow push-in.",
            ),
        ),
        (
            "sit-line",
            "Sit and speak",
            _ltx_i2v(
                "Seated. One short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "stand-line",
            "Stand and speak",
            _ltx_i2v(
                "Standing. One short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "night-line",
            "Night line",
            _ltx_i2v(
                "Night practicals. One short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "rain-line",
            "Rain line",
            _ltx_i2v(
                "Rain on glass. One short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "desk-line",
            "Desk line",
            _ltx_i2v(
                "At a desk. One short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "rail-line",
            "Rail line",
            _ltx_i2v(
                "At a rail. One short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "soft-line",
            "Soft line",
            _ltx_i2v(
                "Very small mouth motion. One short line. Wardrobe and set stay locked.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "pause-line",
            "Pause then line",
            _ltx_i2v(
                "A pause, then one short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "smile-line",
            "Small smile, line",
            _ltx_i2v(
                "A small smile, then one short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "two-beats",
            "Two short beats",
            _ltx_i2v(
                "Two short spoken beats, modest mouth motion. Wardrobe and set stay locked.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera.",
            ),
        ),
        (
            "end-still-talk",
            "End still",
            _ltx_i2v(
                "One short line, then the last frames hold still. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech, no score.",
                "Fixed camera then hold.",
            ),
        ),
        (
            "no-score-talk",
            "No score talk",
            _ltx_i2v(
                "The subject holds still and speaks one short line. Wardrobe and set stay locked. Mouth motion is modest.",
                "Room tone matching the start image, modest speech. No music and no score.",
                "Fixed camera.",
            ),
        ),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in extras]


def ltx_iclora() -> list[dict[str, str]]:
    extras = [
        (
            "envelope-hold",
            "Envelope hold",
            _ltx_i2v(
                "Motion under the guide envelope. Gentle fabric. Camera stays with the clay blocking.",
                "World SFX matching the start image.",
                "Camera follows the guide.",
            ),
        ),
        (
            "envelope-breeze",
            "Envelope breeze",
            _ltx_i2v(
                "Gentle breeze in fabric or leaves. Camera stays with the clay blocking.",
                "World SFX matching the start image.",
                "Camera follows the guide.",
            ),
        ),
        (
            "envelope-push",
            "Envelope push",
            _ltx_i2v(
                "A slow push that stays inside the guide envelope.",
                "World SFX matching the start image.",
                "Slow push-in along the guide.",
            ),
        ),
        (
            "envelope-pan",
            "Envelope pan",
            _ltx_i2v(
                "A slow pan that stays inside the guide envelope.",
                "World SFX matching the start image.",
                "Slow pan along the guide.",
            ),
        ),
        (
            "envelope-track",
            "Envelope track",
            _ltx_i2v(
                "A short track that stays inside the guide envelope.",
                "World SFX matching the start image.",
                "Track along the guide.",
            ),
        ),
        (
            "envelope-fixed",
            "Envelope fixed",
            _ltx_i2v(
                "Fixed camera. Motion is fabric and light only. Blocking from the guide.",
                "World SFX matching the start image.",
                "Fixed camera.",
            ),
        ),
        (
            "envelope-rain",
            "Envelope rain",
            _ltx_i2v(
                "Rain beads. Camera stays with the clay blocking.",
                "Rain matching the start image.",
                "Camera follows the guide.",
            ),
        ),
        (
            "envelope-night",
            "Envelope night",
            _ltx_i2v(
                "Night practicals. Camera stays with the clay blocking.",
                "World SFX matching the start image.",
                "Camera follows the guide.",
            ),
        ),
        (
            "envelope-dawn",
            "Envelope dawn",
            _ltx_i2v(
                "Dawn light. Camera stays with the clay blocking.",
                "World SFX matching the start image.",
                "Camera follows the guide.",
            ),
        ),
        (
            "envelope-crowd-far",
            "Envelope far crowd",
            _ltx_i2v(
                "Far motion only. Near blocking from the guide.",
                "World SFX matching the start image.",
                "Camera follows the guide.",
            ),
        ),
        (
            "envelope-hands",
            "Envelope hands",
            _ltx_i2v(
                "Modest hand motion. Silhouette from the guide.",
                "World SFX matching the start image.",
                "Camera follows the guide.",
            ),
        ),
        (
            "envelope-walk",
            "Envelope walk",
            _ltx_i2v(
                "A short walk that stays inside the guide path.",
                "Footfalls under world SFX matching the start image.",
                "Camera follows the guide.",
            ),
        ),
        (
            "envelope-settle",
            "Envelope settle",
            _ltx_i2v(
                "Motion settles. Last frames hold. Blocking from the guide.",
                "World SFX matching the start image.",
                "Camera follows the guide then holds.",
            ),
        ),
        (
            "envelope-canny",
            "Envelope canny",
            _ltx_i2v(
                "Stay inside the canny edges. Gentle fabric.",
                "World SFX matching the start image.",
                "Camera follows the guide.",
            ),
        ),
        (
            "envelope-depth",
            "Envelope depth",
            _ltx_i2v(
                "Stay inside the depth envelope. Gentle fabric.",
                "World SFX matching the start image.",
                "Camera follows the guide.",
            ),
        ),
        (
            "envelope-shorts",
            "Envelope vertical",
            _ltx_i2v(
                "Vertical Shorts framing. Motion under the guide envelope.",
                "World SFX matching the start image.",
                "Camera follows the guide.",
            ),
        ),
        (
            "envelope-indoor",
            "Envelope indoor",
            _ltx_i2v(
                "Indoor practicals. Camera stays with the clay blocking.",
                "Room tone matching the start image.",
                "Camera follows the guide.",
            ),
        ),
        (
            "envelope-wind",
            "Envelope wind",
            _ltx_i2v(
                "Wind pulls fabric. Camera stays with the clay blocking.",
                "Wind matching the start image.",
                "Camera follows the guide.",
            ),
        ),
        (
            "envelope-no-redesign",
            "No redesign",
            _ltx_i2v(
                "Do not redesign layout. Motion only under the guide.",
                "World SFX matching the start image.",
                "Camera follows the guide.",
            ),
        ),
        (
            "envelope-end-hold",
            "Envelope end hold",
            _ltx_i2v(
                "Motion under the guide, last frames hold for the next shot.",
                "World SFX matching the start image.",
                "Camera follows the guide then holds.",
            ),
        ),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in extras]


def film_gosee() -> list[dict[str, str]]:
    extras = [("dead-sprint-gap", "Dead sprint at the gap", GOSEE_IDENTITY)]
    beats = [
        ("gap-center", "Gap fills center", "the rooftop gap already fills the center"),
        ("bay-beyond", "Bay beyond the gap", "unmarked palms and glass towers rush toward a bright bay beyond the gap"),
        ("left-pump", "Left glove pump", "left glove hip-to-chest on the contralateral pump"),
        ("cloak-stream", "Cloak streams", "the storm-cloak streams at the left and right frame edges"),
        ("rune-wrists", "Rune motes at wrists", "tiny floating warm-gold rune motes hover near the wrists only"),
        ("wet-stone", "Wet stone grit", "late-sun rim light, fabric weave and stone grit"),
        ("night-sprint", "Night sprint", "night practicals, still a dead sprint, empty palms"),
        ("rain-sprint", "Rain sprint", "rain beads on ink-black sleeves, still a dead sprint"),
        ("dawn-sprint", "Dawn sprint", "first light, still a dead sprint at the gap"),
        ("maglev", "Maglev grating", "already at a dead sprint across unmarked grating toward a skybridge gap"),
        ("garden-glass", "Garden glass", "already at a dead sprint along unmarked hanging-garden glass"),
        ("causeway", "Storm causeway", "already at a dead sprint on a wet unmarked causeway"),
        ("ridge", "Ridge sprint", "already at a dead sprint on a coastal jungle ridge"),
        ("overlook", "Overlook sprint", "already at a dead sprint toward a warm-night bay overlook rail"),
        ("hands-free", "Hands free", "empty palms, hands free, no carried object"),
        ("no-face", "No wearer face", "no wearer face, only sleeves and gloves along the bottom edge"),
        ("barrel", "Slight barrel", "wide 24mm body-cam, slight barrel, bare frame edges"),
        ("plant-last", "Readable plant", "last frame still a sprint, landing readable for the next I2V"),
        ("wordless", "Wordless plate", "silent mouth implied, empty of lettering, clean unmarked lens"),
    ]
    for sid, label, extra in beats:
        extras.append(
            (
                sid,
                label,
                "A chest-mounted first-person body-cam still, eye-level, already at a dead sprint. "
                f"{extra.capitalize()}. Only the wearer's own ink-black fitted running sleeves and blank "
                "matte-black gloves enter from the bottom edge: contralateral pump, empty palms, hands free. "
                "An open short storm-cloak in matte charcoal with a warm-gold inner lining streams at the edges. "
                "Wide 24mm body-cam, slight barrel, a full-bleed photographic plate in YouTube 16:9 with bare "
                "frame edges and a clean unmarked lens, empty of lettering.",
            )
        )
    return [_row(sid, label, prompt) for sid, label, prompt in extras]


def film_still_here() -> list[dict[str, str]]:
    extras = [("chipped-mug", "Chipped cream mug", STILL_HERE_IDENTITY)]
    beats = [
        ("first-light", "First light mug", "first light on the honey-oak table"),
        ("steam", "Steam lift", "steam lifting from the chipped cream mug"),
        ("curtain", "Linen curtain", "one linen curtain at a single window"),
        ("tile", "Subway tile", "white subway tile backsplash, unmarked"),
        ("chip-sharp", "Chip sharp", "the hairline chip on the rim is sharp in the foreground"),
        ("two-mugs", "Two mugs", "the chipped cream mug plus a second plain mug, still the hero"),
        ("kettle", "Kettle nearby", "a kettle nearby, mug still the hero"),
        ("notebook", "Blank notebook", "a blank notebook beside the mug, unmarked"),
        ("rain-window", "Rain window", "rain on the single window, mug still sharp"),
        ("night-mug", "Night mug", "one practical, night kitchen, mug still sharp"),
        ("dawn-cool", "Dawn cool", "cool first light, mug still sharp"),
        ("hands-out", "No hands", "no hands in frame, mug only"),
        ("closer", "Closer mug", "closer on the chip, 35mm still"),
        ("wider", "Wider table", "wider on the table, mug still the hero"),
        ("linen-napkin", "Linen napkin", "a linen napkin beside the mug"),
        ("spoon", "Plain spoon", "a plain spoon beside the mug"),
        ("sun-patch", "Sun patch", "a sun patch on oak, mug in it"),
        ("quiet", "Quiet kitchen", "empty unmarked kitchen, mug only"),
        ("end-still", "End still", "the mug holds the frame for the next I2V"),
    ]
    for sid, label, extra in beats:
        extras.append(
            (
                sid,
                label,
                "A photoreal third-person household morning still. One cream ceramic mug with a hairline chip "
                f"on the rim sits on a honey-oak table. {extra.capitalize()}. White subway tile backsplash, "
                "one linen curtain at a single window. Unmarked kitchen, empty of lettering. The mug is sharp "
                "in the foreground. Match a standing eyeline. 35mm-equivalent classic reportage view, framed for YouTube 16:9.",
            )
        )
    return [_row(sid, label, prompt) for sid, label, prompt in extras]


def film_switchyard() -> list[dict[str, str]]:
    extras = [("three-cars-rain", "Three cars in rain", SWITCHYARD_IDENTITY)]
    beats = [
        ("one-lamp", "One yard lamp", "one yard lamp, rain in the glow"),
        ("wet-ballast", "Wet ballast", "wet ballast shining, empty of railroad marks"),
        ("three-cars", "Three boxcars", "three generic unmarked boxcars"),
        ("between-cars", "Between cars", "the slot between unmarked cars is the center"),
        ("puddle", "Puddle lamp", "a puddle holds the lamp"),
        ("gravel-walk", "Gravel walk still", "already mid-walk on wet gravel, still a still"),
        ("breath-cold", "Cold breath", "breath in cold air implied in the still"),
        ("no-marks", "No company marks", "empty of railroad company marks"),
        ("closer-steel", "Closer steel", "closer on unmarked wet steel"),
        ("wider-yard", "Wider yard", "wider on the yard, cars still the hero"),
        ("fog-mix", "Fog mix", "rain and fog, lamp still the key"),
        ("dawn-yard", "Dawn yard", "first light plus the lamp, still raining"),
        ("night-only", "Night only", "night only, one lamp, rain"),
        ("coupling-far", "Far coupling", "a distant coupling in the still, generic"),
        ("no-chase", "Not a chase", "a walk, not a chase, still frame"),
        ("empty-palms", "Empty frame of people", "no faces, cars and lamp only"),
        ("grain", "Mild grain", "mild film grain, wet grit"),
        ("24mm", "24mm yard", "eye-level 24mm, YouTube 16:9"),
        ("end-still", "End still", "the lamp and cars hold for the next I2V"),
    ]
    for sid, label, extra in beats:
        extras.append(
            (
                sid,
                label,
                "A photoreal night freight-yard still in rain. Three generic unmarked boxcars sit on wet "
                f"ballast. {extra.capitalize()}. Rain streaks in the lamp glow, gravel shining, empty of "
                "railroad company marks. Match a standing eyeline. 24mm-equivalent wide, framed for YouTube 16:9. Clean unmarked "
                "steel, empty of lettering.",
            )
        )
    return [_row(sid, label, prompt) for sid, label, prompt in extras]


def _rap(sid: str, label: str, tags: str, lyrics: str) -> dict[str, str]:
    return _row(sid, label, lyrics, tags=tags, lyrics=lyrics)


def rap_draft() -> list[dict[str, str]]:
    verses = [
        ("booth-stack", "Booth stack", RAP_TAGS, DRAFT_LYRICS),
        (
            "quiet-street",
            "Quiet street",
            RAP_TAGS,
            "[intro]\nyeah\nlocal signal\non the box\n\n[verse]\nFan stays loud on a quiet street\nWeights on disk, no rented beat\nCard runs hot, the cut stays clean\nIf it ships from here it stays unseen\n\n[chorus]\nOwn the booth, own the stack\nNo ghost in the hook, no borrowed track\nSpark in the rack, the master comes back",
        ),
        (
            "solo-take",
            "Solo take",
            RAP_TAGS,
            "[intro]\nyeah\nlocal signal\n\n[verse]\nRack light blinks on a solo take\nNo rented hook, no leased name\nBars stay tight, the booth stays mine\nStamp the master, keep the line\n\n[chorus]\nOwn the booth, own the stack\nNo ghost in the hook, no borrowed track",
        ),
        (
            "weights-disk",
            "Weights on disk",
            RAP_TAGS,
            "[verse]\nWeights on disk, the fan in the hall\nNo cloud verse, no rented call\nIf the card dies the show dies too\nThat is the bargain, that is the proof\n\n[chorus]\nOwn the booth, own the stack",
        ),
        (
            "cut-clean",
            "Cut stays clean",
            RAP_TAGS,
            "[verse]\nCut stays clean when the room stays small\nNo ghost in the hook, no borrowed call\nStamp it local, leave it plain\nIf it leaves this box it keeps my name\n\n[chorus]\nSpark in the rack, the master comes back",
        ),
        (
            "no-autotune",
            "Dry booth",
            RAP_TAGS,
            "[verse]\nDry booth, dry snare, no polish pass\nThe take is the take, let the air be glass\nIf it shakes it shakes, if it hits it hits\nI do not rent a throat for this\n\n[chorus]\nOwn the booth, own the stack",
        ),
        (
            "night-rack",
            "Night rack",
            RAP_TAGS,
            "[verse]\nNight rack hum, the street is thin\nI write the bar where the solder sits\nNo leased hook, no borrowed grin\nThe master stays where the spark begins\n\n[chorus]\nNo ghost in the hook, no borrowed track",
        ),
        (
            "hall-fan",
            "Hall fan",
            RAP_TAGS,
            "[verse]\nHall fan loud, the neighbor sleeps\nI keep the verse in a local keep\nNo wire in, no wire out\nIf it ships it ships from this house\n\n[chorus]\nOwn the booth, own the stack",
        ),
        (
            "stamp-plain",
            "Stamp it plain",
            RAP_TAGS,
            "[verse]\nStamp it plain, no sticker shine\nThe bar is a bolt, the hook is a line\nI do not borrow a famous climb\nI build the stair and I take my time\n\n[chorus]\nSpark in the rack, the master comes back",
        ),
        (
            "card-tab",
            "Card tab",
            RAP_TAGS,
            "[verse]\nCard tab hot, the meter true\nI pay the watts, I keep the room\nNo rented booth, no leased perfume\nThe cut is sweat and a local tune\n\n[chorus]\nOwn the booth, own the stack",
        ),
        (
            "quiet-hook",
            "Quiet hook",
            RAP_TAGS,
            "[verse]\nQuiet hook, no fireworks lie\nThe chorus is a door, not a sky\nI say the work, I say the why\nThen I sit down and let it dry\n\n[chorus]\nNo ghost in the hook, no borrowed track",
        ),
        (
            "floor-dust",
            "Floor dust",
            RAP_TAGS,
            "[verse]\nFloor dust, cable, a dented case\nThe booth is a closet that learned a bass\nI do not tour, I do not chase\nI print the bar and I give it space\n\n[chorus]\nOwn the booth, own the stack",
        ),
        (
            "one-mic",
            "One mic",
            RAP_TAGS,
            "[verse]\nOne mic, one take, one cheap stand\nThe room is the verb, the rack is the hand\nNo borrowed silk, no rented band\nIf it lives it lives where the solder lands\n\n[chorus]\nSpark in the rack, the master comes back",
        ),
        (
            "street-light",
            "Street light",
            RAP_TAGS,
            "[verse]\nStreet light through a dusty blind\nThe verse is a walk I do not rewind\nI keep the time, I keep the kind\nLocal signal, local mind\n\n[chorus]\nOwn the booth, own the stack",
        ),
        (
            "no-ghost",
            "No ghost",
            RAP_TAGS,
            "[verse]\nNo ghost in the hook, I said it twice\nI do not rent a famous vice\nThe booth is a box, the box is a life\nThe master comes back and it stays my slice\n\n[chorus]\nNo ghost in the hook, no borrowed track",
        ),
        (
            "solder",
            "Solder",
            RAP_TAGS,
            "[verse]\nSolder smell, a window cracked\nThe bar is a circuit I do not wrap\nI test the line, I hear it snap\nThen I print the take and I do not look back\n\n[chorus]\nSpark in the rack, the master comes back",
        ),
        (
            "keep-line",
            "Keep the line",
            RAP_TAGS,
            "[verse]\nKeep the line, keep the fault\nThe honest miss is part of the vault\nI do not auto the human salt\nI leave the air and I call it adult\n\n[chorus]\nOwn the booth, own the stack",
        ),
        (
            "small-room",
            "Small room",
            RAP_TAGS,
            "[verse]\nSmall room, big fan, no crowd noise\nThe hook is a tool, not a toy\nI write for the rack, I write for the choice\nTo keep the cut in a local voice\n\n[chorus]\nNo ghost in the hook, no borrowed track",
        ),
        (
            "last-pass",
            "Last pass",
            RAP_TAGS,
            "[verse]\nLast pass, the meter still true\nI do not gild what the first take knew\nStamp the master, leave the glue\nIf it ships from here it stays my proof\n\n[chorus]\nSpark in the rack, the master comes back",
        ),
        (
            "signal",
            "Local signal",
            RAP_TAGS,
            "[intro]\nyeah\nlocal signal\non the box\n\n[verse]\nLocal signal, local heat\nThe booth is a closet on a quiet street\nNo rented throat, no borrowed beat\nThe master comes back and the cut stays sweet\n\n[chorus]\nOwn the booth, own the stack",
        ),
    ]
    return [_rap(sid, label, tags, lyrics) for sid, label, tags, lyrics in verses]


def rap_full() -> list[dict[str, str]]:
    verses = [
        ("booth-full", "Booth full take", RAP_FULL_TAGS, FULL_LYRICS),
    ]
    extras = [
        (
            "two-verse",
            "Two verse stack",
            RAP_FULL_TAGS,
            FULL_LYRICS,
        ),
        (
            "rack-light",
            "Rack light full",
            RAP_FULL_TAGS,
            "[intro]\nyeah\nlocal signal\non the box\n\n[verse]\nFan stays loud on a quiet street\nWeights on disk, no rented beat\nCard runs hot, the cut stays clean\nIf it ships from here it stays unseen\n\n[chorus]\nOwn the booth, own the stack\nNo ghost in the hook, no borrowed track\nSpark in the rack, the master comes back\n\n[verse]\nRack light blinks on a solo take\nNo rented hook, no leased name\nBars stay tight, the booth stays mine\nStamp the master, keep the line\n\n[chorus]\nOwn the booth, own the stack\nNo ghost in the hook, no borrowed track\nSpark in the rack, the master comes back\n\n[outro]\nyeah\nlocal signal\ncut",
        ),
    ]
    # 17 more distinct full-length original songs
    more = [
        ("hall-full", "Hall fan full", "Hall fan loud, the neighbor sleeps"),
        ("night-full", "Night rack full", "Night rack hum, the street is thin"),
        ("solder-full", "Solder full", "Solder smell, a window cracked"),
        ("one-mic-full", "One mic full", "One mic, one take, one cheap stand"),
        ("dust-full", "Floor dust full", "Floor dust, cable, a dented case"),
        ("meter-full", "Meter full", "Card tab hot, the meter true"),
        ("plain-full", "Stamp plain full", "Stamp it plain, no sticker shine"),
        ("quiet-full", "Quiet hook full", "Quiet hook, no fireworks lie"),
        ("street-full", "Street light full", "Street light through a dusty blind"),
        ("ghost-full", "No ghost full", "No ghost in the hook, I said it twice"),
        ("fault-full", "Keep the fault", "Keep the line, keep the fault"),
        ("closet-full", "Closet booth", "The booth is a closet that learned a bass"),
        ("watts-full", "Pay the watts", "I pay the watts, I keep the room"),
        ("air-full", "Leave the air", "I leave the air and I call it adult"),
        ("proof-full", "Local proof", "If it ships from here it stays my proof"),
        ("choice-full", "Local voice", "I write for the rack, I write for the choice"),
        ("dry-full", "Dry take full", "Dry booth, dry snare, no polish pass"),
    ]
    verses.extend(extras)
    for sid, label, line in more:
        verses.append(
            (
                sid,
                label,
                RAP_FULL_TAGS,
                "[intro]\nyeah\nlocal signal\non the box\n\n"
                f"[verse]\n{line}\nWeights on disk, no rented beat\nCard runs hot, the cut stays clean\nIf it ships from here it stays unseen\n\n"
                "[chorus]\nOwn the booth, own the stack\nNo ghost in the hook, no borrowed track\nSpark in the rack, the master comes back\n\n"
                "[verse]\nRack light blinks on a solo take\nNo rented hook, no leased name\nBars stay tight, the booth stays mine\nStamp the master, keep the line\n\n"
                "[chorus]\nOwn the booth, own the stack\nNo ghost in the hook, no borrowed track\nSpark in the rack, the master comes back\n\n"
                "[outro]\nyeah\nlocal signal\ncut",
            )
        )
    return [_rap(sid, label, tags, lyrics) for sid, label, tags, lyrics in verses]


def podcast_two_host() -> list[dict[str, str]]:
    extras = [("local-signal", "Local Signal cold open", SEED_SCRIPT)]
    beats = [
        ("weights-disk", "Weights on disk", "Speaker A: The weights live on disk in this room.\nSpeaker B: If the card dies, the show dies with it.\nSpeaker A: That is the bargain we keep.\nSpeaker B: Edit the script before you generate speech."),
        ("no-cloud", "No cloud voices", "Speaker A: No cloud voices on this hour.\nSpeaker B: No rented music either.\nSpeaker A: The bed is local. The cut is local.\nSpeaker B: If we cannot own it, we do not air it."),
        ("one-job", "One job", "Speaker A: One heavy job on this box.\nSpeaker B: Then we stop and we listen.\nSpeaker A: That is how the street stays up.\nSpeaker B: Print later. Write now."),
        ("edit-human", "The edit is human", "Speaker A: The rewrite is a tool.\nSpeaker B: The edit is the human part.\nSpeaker A: Read it out loud before Queue.\nSpeaker B: If it sounds rented, cut it."),
        ("booth-small", "Small booth", "Speaker A: The booth is a closet with a fan.\nSpeaker B: That is enough.\nSpeaker A: We do not need a borrowed room.\nSpeaker B: We need a true line."),
        ("disclosure", "Say the bumper", "Speaker A: Voices on this show are synthesized.\nSpeaker B: The hosts are original characters.\nSpeaker A: We say that because it is true.\nSpeaker B: Then we do the work."),
        ("rain-hour", "Rain hour", "Speaker A: Rain on the glass, fan in the hall.\nSpeaker B: Good weather for a local hour.\nSpeaker A: Keep the bed instrumental.\nSpeaker B: Keep the talk honest."),
        ("night-desk", "Night desk", "Speaker A: Night desk, one lamp, no audience.\nSpeaker B: The audience is later.\nSpeaker A: Right now the script is the guest.\nSpeaker B: Then we record."),
        ("card-hot", "Card runs hot", "Speaker A: The card runs hot. That is the point.\nSpeaker B: We do not hide the heat.\nSpeaker A: We schedule around it.\nSpeaker B: One job. Then air."),
        ("no-rented-bed", "No rented bed", "Speaker A: The bed is ours or it is silent.\nSpeaker B: Silence is honest.\nSpeaker A: A rented bed is not.\nSpeaker B: Cue local only."),
        ("look-twice", "Look twice", "Speaker A: Look twice before you print a take.\nSpeaker B: Words are cheap. Prints are not.\nSpeaker A: That is why we read it first.\nSpeaker B: Then Queue."),
        ("harbor", "Harbor hour", "Speaker A: Fog on the harbor, fan in the rack.\nSpeaker B: We stay on the machine in front of us.\nSpeaker A: The city can wait.\nSpeaker B: The cut cannot."),
        ("workshop", "Workshop hour", "Speaker A: This hour is a workbench.\nSpeaker B: Tools on the table, no theater.\nSpeaker A: Name the tool. Name the limit.\nSpeaker B: Then use it well."),
        ("quiet-street", "Quiet street", "Speaker A: Quiet street, loud fan.\nSpeaker B: That is our room tone.\nSpeaker A: We do not fake a hall.\nSpeaker B: We keep the closet."),
        ("stop-first", "Stop first", "Speaker A: Stop the other occupancy first.\nSpeaker B: One GB10 job.\nSpeaker A: That sentence is the show.\nSpeaker B: Then we talk."),
        ("script-first", "Script first", "Speaker A: Script first, voice second.\nSpeaker B: If the line is weak, do not clone it.\nSpeaker A: Fix the line.\nSpeaker B: Then generate."),
        ("own-silence", "Own the silence", "Speaker A: Own the silence between the words.\nSpeaker B: Do not fill it with a rented swell.\nSpeaker A: The street is enough.\nSpeaker B: Let it sit."),
        ("end-on-work", "End on the work", "Speaker A: We end on the work, not a slogan.\nSpeaker B: What did we make.\nSpeaker A: A local hour.\nSpeaker B: Cut."),
        ("welcome-back", "Welcome back", "Speaker A: Welcome back to Local Signal.\nSpeaker B: Same box. Same bargain.\nSpeaker A: No cloud voices.\nSpeaker B: Edit before you generate."),
    ]
    extras.extend(beats)
    return [_row(sid, label, prompt) for sid, label, prompt in extras]


def podcast_radio() -> list[dict[str, str]]:
    extras = [("machine-only", "Machine-only hour", RADIO_SEED_SCRIPT)]
    beats = [
        ("transmitter", "Transmitter light", "Announcer: The transmitter light is steady.\nSpeaker A: We do not borrow a voice from the wire.\nSpeaker B: If the card goes dark, the play ends.\nAnnouncer: End of scene. The hosts are invented. The mix is local."),
        ("bargain", "The bargain", "Announcer: Tonight, the bargain.\nSpeaker A: If the card dies, the play dies.\nSpeaker B: Say the line like you mean the cut.\nAnnouncer: The hosts are invented. The mix is local."),
        ("instrumental", "Keep it instrumental", "Announcer: Cue the bed.\nSpeaker A: Keep it instrumental.\nSpeaker B: We own the silence between words.\nAnnouncer: End of scene."),
        ("rack", "Never left the rack", "Announcer: A story that never left the rack.\nSpeaker A: The light is steady.\nSpeaker B: We do not lease a throat.\nAnnouncer: The mix is local."),
        ("wire", "Not the wire", "Announcer: Not the wire.\nSpeaker A: Not the cloud.\nSpeaker B: The cut.\nAnnouncer: End of scene."),
        ("rain-play", "Rain play", "Announcer: Rain on the glass.\nSpeaker A: The booth is a closet.\nSpeaker B: The play still holds.\nAnnouncer: The hosts are invented."),
        ("night-play", "Night play", "Announcer: Night desk.\nSpeaker A: One lamp.\nSpeaker B: One hour.\nAnnouncer: The mix is local."),
        ("fan", "Fan in the hall", "Announcer: Fan in the hall.\nSpeaker A: That is the room.\nSpeaker B: Do not fake a hall.\nAnnouncer: End of scene."),
        ("no-borrow", "Do not borrow", "Announcer: Do not borrow a voice.\nSpeaker A: We invent the hosts.\nSpeaker B: We say so.\nAnnouncer: The mix is local."),
        ("cut-not-cloud", "Cut, not cloud", "Announcer: Say it like you mean the cut, not the cloud.\nSpeaker A: The line is the work.\nSpeaker B: The bed stays instrumental.\nAnnouncer: End of scene."),
        ("steady", "Light steady", "Announcer: Light steady.\nSpeaker A: Card hot.\nSpeaker B: Play live on the box.\nAnnouncer: The hosts are invented."),
        ("silence", "Own silence", "Announcer: Own the silence.\nSpeaker A: Do not rent a swell.\nSpeaker B: Let the street sit.\nAnnouncer: End of scene."),
        ("closet", "Closet stage", "Announcer: The stage is a closet.\nSpeaker A: That is enough.\nSpeaker B: The line has to carry.\nAnnouncer: The mix is local."),
        ("bargain-two", "Bargain two", "Announcer: The bargain holds.\nSpeaker A: Local weights.\nSpeaker B: Local cut.\nAnnouncer: End of scene."),
        ("no-wire", "No wire in", "Announcer: No wire in.\nSpeaker A: No wire out.\nSpeaker B: If it airs, it aired from here.\nAnnouncer: The hosts are invented."),
        ("cue-bed", "Cue bed", "Announcer: Cue the bed.\nSpeaker A: Instrumental only.\nSpeaker B: Then the line.\nAnnouncer: End of scene."),
        ("dark", "If it goes dark", "Announcer: If the card goes dark.\nSpeaker A: The play ends.\nSpeaker B: That is the honest end.\nAnnouncer: The mix is local."),
        ("invented", "Hosts invented", "Announcer: The hosts are invented.\nSpeaker A: Not recordings of real people.\nSpeaker B: We say the bumper because it is true.\nAnnouncer: End of scene."),
        ("end-scene", "End of scene", "Announcer: End of scene.\nSpeaker A: Hold the last line.\nSpeaker B: Then cut.\nAnnouncer: The mix is local."),
    ]
    extras.extend(beats)
    return [_row(sid, label, prompt) for sid, label, prompt in extras]


def forge_lazy() -> list[dict[str, str]]:
    extras = [
        ("rooftop-lazy", "Rooftop wizard", LAZY_FORGE),
        ("night-rail", "Night rail", "A techno wizard on a night rooftop rail over a tropical bay."),
        ("rain-terrace", "Rain terrace", "A techno wizard under a terrace overhang in tropical rain."),
        ("workshop", "Workshop", "A techno wizard at a teak workbench with glyph rings."),
        ("harbor-fog", "Harbor fog", "A techno wizard on an unmarked foggy pier."),
        ("ridge-dawn", "Ridge dawn", "A techno wizard on a high switchback at first light."),
        ("greenhouse", "Greenhouse", "A techno wizard walking a greenhouse aisle of palms."),
        ("mesa-dusk", "Mesa dusk", "A techno wizard on a desert mesa at dusk."),
        ("library", "Library", "A techno wizard between unmarked wood stacks."),
        ("platform", "Platform", "A techno wizard waiting on an unmarked night platform."),
        ("cliff", "Cliff", "A techno wizard on a coastal cliff path in wind."),
        ("snow", "Snow ridge", "A techno wizard on a snow pine ridge."),
        ("alley", "Covered alley", "A techno wizard in a narrow unmarked alley."),
        ("ferry", "Ferry", "A techno wizard at a ferry rail at dusk."),
        ("arcade", "Arcade", "A techno wizard in an unmarked indoor arcade."),
        ("courtyard", "Courtyard", "A techno wizard at a stone fountain in a courtyard."),
        ("concourse", "Concourse", "A techno wizard mid-stride in a vast unmarked concourse."),
        ("storm", "Storm rooftop", "A techno wizard in a storm-cloak on a windy rooftop."),
        ("studio", "Quiet studio", "A techno wizard at a teak desk with a blank notebook."),
        ("observatory", "Observatory", "A techno wizard inside an unmarked dome at night."),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in extras]


def research_chat() -> list[dict[str, str]]:
    extras = [
        ("rooftop-light", "Rooftop lighting language", RESEARCH_DEFAULT),
        ("night-practicals", "Night practicals", "What lighting language fits a night rooftop still of a techno wizard, lanterns only, no score, unmarked surfaces?"),
        ("i2v-motion", "I2V motion only", "How should a Wan I2V prompt describe motion and one camera without restating look from the start image?"),
        ("ltx-audio", "LTX audio interleave", "How do I interleave world SFX into an LTX-2.5 present-tense paragraph without writing a sound trailer?"),
        ("identity-bible", "Identity bible", "What belongs in a Klein identity bible versus a shot card for a three-angle sheet?"),
        ("dream-house", "Dream-house rooms", "How should a camera-free place bible name rooms and backdrops for a ten-still walkthrough?"),
        ("loop-safe", "GIF loop safe", "What motion is ping-pong safe for a locked-camera Wan GIF loop?"),
        ("packshot", "Packshot still", "How do I prompt a Klein 1:1 product packshot with unmarked surfaces and honest contact shadow?"),
        ("clay-edit", "Clay edit", "What should a Klein edit prompt say so it restyles clay without redesigning layout?"),
        ("dialogue-quotes", "Dialogue quotes", "When should an LTX prompt use quoted speech, and how do I keep world SFX under the line?"),
        ("multishot", "Named cuts", "How do I name hard cut and match cut in one LTX-2.5 five-second paragraph?"),
        ("a2v-freeze", "A2V freeze", "How do I prompt LTX A2V so the loaded wav owns timing and mouths are not expected to match?"),
        ("go-see", "Body-cam still", "What first-person body-cam grammar keeps sleeves and gloves on the bottom edge with empty palms?"),
        ("negative", "Negative that helps", "What negative terms help Klein without fighting a photoreal look?"),
        ("style-dropdown", "Style dropdown", "How does the style dropdown interact with a lazy Klein prompt when Enhance is on?"),
        ("one-camera", "One camera verb", "Give Wan T2V camera-verb choices that stay at one move for five seconds."),
        ("no-score", "No score shorts", "How do I keep LTX shorts world-SFX-only so distilled AV does not invent a score?"),
        ("character-tweak", "Character tweak", "What belongs in a Klein character-tweak prompt so face and wardrobe lock?"),
        ("handoff", "Still to motion", "What should I copy from a Spark Still into Wan I2V versus LTX I2V?"),
        ("forge-context", "Forge context", "What should I paste into Prompt Forge Context from a research brief?"),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in extras]


def app_forge() -> list[dict[str, str]]:
    extras = [
        ("mug-ig", "Mug IG square", "1:1 IG still of a chipped cobalt mug on pale stone, unmarked surfaces."),
        ("rooftop-still", "Rooftop still", "Spark still of a techno wizard on a tropical rooftop at golden hour."),
        ("silent-i2v", "Silent I2V", "silent 5s from a still of a wizard mid-stride on a terrace."),
        ("gif-palms", "GIF palms", "gif loop of palms and glyph motes, locked camera, ping-pong safe."),
        ("ltx-av", "LTX AV", "ltx 5s AV of a terrace with world foley, no score."),
        ("dialogue", "Dialogue 5s", "dialogue 5s with one quoted line and world SFX under."),
        ("thumbnail", "YouTube thumb", "thumbnail of a wizard and a chipped mug, 1280x720, unmarked."),
        ("banner", "Wide banner", "banner-wide still of a tropical bay between unmarked towers."),
        ("packshot", "Packshot", "packshot of one cobalt mug, 1:1, honest contact shadow."),
        ("podcast", "Podcast desk", "podcast two-host local hour about keeping the master on the box."),
        ("rap-draft", "Rap draft", "rap draft boom-bap booth take, dry vocals, no autotune."),
        ("beat-sheet", "Beat sheet", "beat-sheet logline for a rooftop sprint, world SFX only."),
        ("open-graph", "OG blog", "open-graph still of a teak desk and blank notebook, 1216x640."),
        ("character", "Character still", "character still of the techno wizard, 1024x1280, identity lock."),
        ("hook-still", "Hook still", "9:16 hook still of a wizard at a night rail, lanterns only."),
        ("a2v", "A2V freeze", "a2v freeze a 5s wav of rain on a terrace, picture follows audio."),
        ("bumper", "Bumper loop", "bumper loop MP4 of glyph rings, ping-pong."),
        ("weather-broll", "Weather B-roll", "ltx weather b-roll of tropical rain on unmarked stone."),
        ("clay-edit", "Clay edit", "Klein edit of clay first.png without moving the camera."),
        ("research-next", "Research next", "still of prompt ingredients from a night rooftop lighting brief."),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in extras]


def beat_sheet_logline() -> list[dict[str, str]]:
    extras = [
        ("approve-first", "Approve before UNET", "One-line premise. Approve before any UNET."),
        ("rooftop-sprint", "Rooftop sprint", "A first-person rooftop sprint across a tropical city, one gap at a time, no speech."),
        ("mug-morning", "Mug morning", "A third-person morning around one chipped cream mug in an unmarked kitchen."),
        ("yard-walk", "Yard walk", "A night walk through an unmarked freight yard in rain, not a chase."),
        ("local-hour", "Local hour", "Two hosts keep a local hour on one box; if the card dies the show dies."),
        ("staff-work", "Staff work", "A techno wizard finishes one tool on a teak bench before the street wakes."),
        ("ferry-dusk", "Ferry dusk", "A short crossing on an unmarked ferry at dusk, world SFX only."),
        ("greenhouse", "Greenhouse walk", "A walk down an unmarked greenhouse aisle, drip and leaf, no score."),
        ("ridge-dawn", "Ridge dawn", "A dawn walk on a high unmarked switchback, one job, then stop."),
        ("library", "Library hush", "A quiet pass between unmarked stacks, paper hush, no speech."),
        ("rain-hold", "Rain hold", "Hold under an overhang while tropical rain finishes the take."),
        ("night-rail", "Night rail", "A night rail look over an unmarked bay, lanterns only."),
        ("packshot-day", "Packshot day", "One unmarked object on stone, honest light, then a slow orbit."),
        ("clay-finish", "Clay stem-mix", "Finish a clay blocking as photoreal without moving the camera."),
        ("dialogue-one", "One line", "One spoken line on a terrace, world SFX under, no score."),
        ("loop-breeze", "Loop breeze", "A locked-camera breeze loop that can ping-pong."),
        ("a2v-listen", "A2V listen", "A still face listens to a loaded clip; picture follows audio."),
        ("concourse", "Concourse stride", "A mid-stride cross of an unmarked concourse, one camera."),
        ("storm-cloak", "Storm cloak", "Wind on a rooftop, cloak lining, then hold the last frame."),
        ("cut-local", "Cut stays local", "A studio hour about keeping the master on the box in front of us."),
    ]
    return [_row(sid, label, prompt) for sid, label, prompt in extras]


def rest_catalogs() -> dict[str, list[dict[str, str]]]:
    """Return the non-Klein-still catalogs."""
    _ = CLAY_FINISH  # imported for parity with the still builder
    return {
        "wan_t2v": wan_t2v(),
        "wan_i2v": wan_i2v(),
        "wan_loop": wan_loop(),
        "wan_flf": wan_flf(),
        "wan_vace": wan_vace(),
        "wan_orbit": wan_orbit(),
        "wan_push_in": wan_push_in(),
        "wan_parallax": wan_parallax(),
        "ltx_t2v": ltx_t2v(),
        "ltx_i2v": ltx_i2v(),
        "ltx_broll": ltx_broll(),
        "ltx_hook": ltx_hook(),
        "ltx_dialogue": ltx_dialogue(),
        "ltx_multishot": ltx_multishot(),
        "ltx_product": ltx_product(),
        "ltx_flf": ltx_flf(),
        "ltx_a2v": ltx_a2v(),
        "ltx_talking": ltx_talking(),
        "ltx_iclora": ltx_iclora(),
        "film_gosee": film_gosee(),
        "film_still_here": film_still_here(),
        "film_switchyard": film_switchyard(),
        "rap_draft": rap_draft(),
        "rap_full": rap_full(),
        "podcast_two_host": podcast_two_host(),
        "podcast_radio": podcast_radio(),
        "forge_lazy": forge_lazy(),
        "research_chat": research_chat(),
        "app_forge": app_forge(),
        "beat_sheet_logline": beat_sheet_logline(),
    }

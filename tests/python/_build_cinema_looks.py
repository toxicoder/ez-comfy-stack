"""Author atmosphere, genre, viral catalogs and starter recipes.

Run from repo root:

  python3 tests/python/_build_cinema_looks.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "custom_nodes" / "ez_prompt_enhance" / "cinema"

_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,47}$")
_BANNED = (
    "kodak",
    "portra",
    "sony",
    "canon",
    "leica",
    "hasselblad",
    "pixar",
    "unreal",
    "lumen",
    "ghibli",
    "panavision",
    "arriflex",
    "arri ",
    "red komodo",
    "imax",
    "dolby",
    "technicolor",
    "nolan",
    "fincher",
    "tarantino",
    "spielberg",
    "scorsese",
    "villeneuve",
    "blade runner",
    "mad max",
    "tiktok",
    "instagram",
    "youtube",
)
_STOP = frozenset(
    "the a an of to and in on at as with without from for by into onto over under "
    "is are was were be being been this that camera frame subject light look shot "
    "still motion".split()
)
_VARIANT_TOKENS = frozenset(
    {
        "left",
        "right",
        "up",
        "down",
        "slow",
        "fast",
        "whip",
        "crawl",
        "crash",
        "mild",
        "heavy",
        "near",
        "far",
        "high",
        "low",
        "wide",
        "tight",
        "soft",
        "hard",
        "warm",
        "cool",
        "day",
        "night",
        "dawn",
        "dusk",
        "vertical",
        "horizontal",
    }
)


def _entry(
    tid: str,
    label: str,
    clause: str,
    *,
    still: str = "",
    wan: str = "",
    audio: str = "",
    still_ok: bool = True,
    motion_ok: bool = True,
    av_ok: bool = True,
    conflicts: tuple[str, ...] = (),
    tags: tuple[str, ...] = (),
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": tid,
        "label": label,
        "clause": clause if clause.endswith(".") else f"{clause}.",
        "still": still,
        "wan_token": wan,
        "audio": audio,
        "still_ok": still_ok,
        "motion_ok": motion_ok,
        "av_ok": av_ok,
        "conflicts": list(conflicts),
        "tags": list(tags),
    }
    if still and not still.endswith("."):
        row["still"] = f"{still}."
    if audio and not audio.endswith("."):
        row["audio"] = f"{audio}."
    return row


def _dump(name: str, rows: list[dict[str, Any]]) -> None:
    path = OUT / name
    path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({len(rows)})")


def _atm(
    suffix: str,
    label: str,
    clause: str,
    audio: str,
    tags: tuple[str, ...],
    *conflicts: str,
) -> dict[str, Any]:
    return _entry(
        f"atm_{suffix}",
        label,
        clause,
        audio=audio,
        conflicts=conflicts,
        tags=tags,
    )


def _gen(
    suffix: str,
    label: str,
    clause: str,
    tags: tuple[str, ...],
    *conflicts: str,
) -> dict[str, Any]:
    return _entry(
        f"gen_{suffix}",
        label,
        clause,
        conflicts=conflicts,
        tags=tags,
    )


def _vir(
    suffix: str,
    label: str,
    clause: str,
    still: str,
    tags: tuple[str, ...],
    audio: str = "",
    *conflicts: str,
) -> dict[str, Any]:
    return _entry(
        f"vir_{suffix}",
        label,
        clause,
        still=still,
        audio=audio,
        conflicts=conflicts,
        tags=tags,
    )


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if word not in _STOP and len(word) > 2}


def _variant_normalized(text: str) -> set[str]:
    return {word for word in _tokens(text) if word not in _VARIANT_TOKENS}


def _validate(name: str, rows: list[dict[str, Any]], prefix: str, *, need_still: bool, need_audio: bool) -> None:
    if len(rows) < 108:
        raise SystemExit(f"{name} {len(rows)} < 108")
    seen_ids: set[str] = set()
    seen_labels: set[str] = set()
    bags: list[tuple[str, set[str]]] = []
    for row in rows:
        tid = str(row["id"])
        if not tid.startswith(prefix):
            raise SystemExit(f"{tid} missing prefix {prefix}")
        if not _ID_RE.fullmatch(tid):
            raise SystemExit(f"bad id {tid}")
        if tid in seen_ids:
            raise SystemExit(f"dup id {tid}")
        seen_ids.add(tid)
        label = str(row["label"]).strip().lower()
        if not label:
            raise SystemExit(f"empty label {tid}")
        if label in seen_labels:
            raise SystemExit(f"dup label {label}")
        seen_labels.add(label)
        clause = str(row["clause"]).strip()
        if not clause.endswith("."):
            raise SystemExit(f"{tid} clause needs period")
        if " is a " in clause.lower() and "camera" not in clause.lower():
            raise SystemExit(f"{tid} definitional clause")
        if need_still and row["still_ok"] and not str(row.get("still") or "").strip():
            raise SystemExit(f"{tid} needs still")
        if need_audio and not str(row.get("audio") or "").strip():
            raise SystemExit(f"{tid} needs audio")
        for field in ("clause", "still", "wan_token", "audio", "label"):
            blob = str(row.get(field) or "").lower()
            for brand in _BANNED:
                if brand in blob:
                    raise SystemExit(f"{tid}.{field} has {brand!r}")
        bags.append((tid, _variant_normalized(clause)))
    for idx, (left_id, left) in enumerate(bags):
        if len(left) < 6:
            raise SystemExit(f"{left_id} too few content words {left}")
        for right_id, right in bags[idx + 1 :]:
            if len(right) < 6:
                continue
            union = left | right
            overlap = len(left & right) / len(union)
            if overlap >= 0.85:
                raise SystemExit(
                    f"{name} {left_id} vs {right_id} overlap {overlap:.2f} shared={sorted(left & right)}"
                )


def atmosphere_weather() -> list[dict[str, Any]]:
    rows = [
        _atm("clear_plaza", "Cloudless plaza", "Hold a cloudless civic plaza in crisp sun, granite joints razor-sharp, no veil between cornice and enamel sky.", "Dry pigeon wing-flaps and a distant fountain.", ("clear",), "atm_blizzard_grid", "atm_heavy_overcast_mill"),
        _atm("cirrus_runway", "High cirrus runway", "Streak mare-tail cirrus over a quiet runway, ice-feathers barely dimming sun on pale concrete.", "Thin wind over open tarmac.", ("cirrus", "clear")),
        _atm("heavy_overcast_mill", "Heavy overcast mill", "Clamp a lead-gray stratus lid on a brick mill yard, shadows erased, wet soot color in every mortar line.", "Distant mill hum under muffled air.", ("overcast",), "atm_clear_plaza"),
        _atm("storm_shelf_wheat", "Storm shelf wheat", "Advance a charcoal shelf cloud over a wheat horizon, the underbelly scalloped, farmhouses still in leftover sun.", "Distant thunder, grain going still.", ("storm", "cloud")),
        _atm("post_rain_bright", "Post-rain bright", "Open post-rain air so puddles become mirrors and painted railings bead, leftover clouds as bright marble over warehouses.", "Dripping eaves and a far siren on wet streets.", ("post-rain", "wet")),
        _atm("marine_layer_blvd", "Marine layer boulevard", "Slide a marine-layer deck inland over a coastal boulevard, upper towers in sun, palms fog-wet at curb height.", "Muffled traffic and a far foghorn.", ("marine", "fog")),
        _atm("inversion_haze_basin", "Inversion haze basin", "Trap brown inversion haze in a basin of freeways, distant ridges dissolved, near overpasses still readable in dirty gold.", "Flattened highway roar.", ("haze", "inversion")),
        _atm("wildfire_orange_air", "Orange fire-sky air", "Stain the whole sky copper-orange from distant fire smoke, a playground in strange noon, rust-colored shadows on plastic slides.", "Dry hush and a far aircraft drone.", ("smoke", "optical")),
        _atm("drizzle_cobble", "Drizzle cobble", "Stipple a cobbled lane with fine drizzle, wool shoulders darkening, cobbles glistening without splash.", "Tiny ticks of drizzle on stone.", ("drizzle", "rain")),
        _atm("rain_bus_shelter", "Steady rain shelter", "Drive steady rain through a bus-shelter fluorescent, umbrellas flashing, gutter rivers carrying leaflets.", "Rain on plexi and passing tires.", ("rain",)),
        _atm("downpour_market", "Market downpour", "Hammer a downpour on a tin market roof, water sheeting off awnings, figures sprinting between stall poles.", "Roar of rain on corrugated tin.", ("downpour", "rain"), "atm_clear_plaza"),
        _atm("backlit_rain_alley", "Backlit rain alley", "Backlight rain into silver needles against a dark alley mouth, each drop a streak toward a lone bulb.", "Sparse drops and a buzzing fixture.", ("rain", "optical")),
        _atm("dry_snow_lake", "Dry powder lake", "Let dry powder snow skate across a frozen lake, crystals sparkling, boot prints filling instantly.", "Dry snow hiss and ice creak.", ("snow",)),
        _atm("wet_snow_iron", "Wet snow iron", "Paste wet snow on a black iron fence, clumps sliding, sidewalk slush reflecting shop windows.", "Wet slush slap under boots.", ("snow", "wet")),
        _atm("blizzard_grid", "Blizzard white-out", "Erase a street grid in blizzard white-out, a stop sign appearing then vanishing, snow bullets traveling sideways.", "Screaming wind and ice hitting metal.", ("blizzard", "snow"), "atm_clear_plaza", "atm_mesa_enamel"),
        _atm("sleet_greenhouse", "Sleet greenhouse", "Pelt sleet against a greenhouse roof, ice-rain ticking, plants inside still, glass frosting in patches.", "Sleet ticking on glass.", ("sleet", "ice")),
        _atm("hail_pickup_hood", "Hail on hood", "Bounce hail off a pickup hood, ice marbles collecting in the bed, dent-bright flashes on paint.", "Hail hammering steel.", ("hail",)),
        _atm("mist_pine_ridge", "Pine ridgeline mist", "Veil a pine ridgeline in pale mist, trunks fading by tens of meters, spider silk beading in the foreground.", "Muffled birds and dripping needles.", ("mist", "fog")),
        _atm("summer_haze_river", "Summer river haze", "Wash a river city in summer haze, bridges stacked as silhouettes, sun a white disk over brown water.", "Distant barge horn in thick air.", ("haze",)),
        _atm("ground_fog_pasture", "Ground fog pasture", "Pool knee-high ground fog in a pasture, cattle legs missing, fence posts as islands, stars still sharp above.", "Cowbells muffled in fog.", ("fog",)),
        _atm("valley_fog_spire", "Valley fog islands", "Fill a river valley with a fog ocean, only barn roofs and a church spire as islands at sunrise.", "Distant rooster through fog.", ("fog", "valley")),
        _atm("marine_fog_harbor", "Harbor marine fog", "Roll marine fog through a fishing harbor, masts appearing as lines, wet rope in close-up, hulls as ghosts.", "Foghorn and dripping rigging.", ("fog", "marine")),
        _atm("cabin_woodsmoke", "Cabin woodsmoke", "Drift woodsmoke from a cabin chimney across a snow yard, the plume blue in shadow and gold where sun hits.", "Firewood pop under still air.", ("smoke",)),
        _atm("barn_loft_dust", "Barn loft dust", "Hang ochre dust in a barn loft, a sun shaft making motes into a solid beam, hay texture glowing.", "Settling chaff and a far animal shift.", ("dust",)),
        _atm("meadow_pollen_cloud", "Meadow pollen cloud", "Cloud gold pollen off a meadow, backlit as a glowing fog around a walker, ragweed heads shaking.", "Bees and dry seed-heads ticking.", ("pollen",)),
        _atm("breakwater_spray", "Breakwater spray", "Throw white sea spray over a breakwater walk, salt crust on railings, figures leaning into the gust.", "Crashing surf and wind in jackets.", ("spray", "marine")),
        _atm("manhole_steam", "Manhole steam", "Vent manhole steam in a winter avenue, the plume wrapping a crossing signal, wet asphalt shining.", "Steam hiss and wet tire roll.", ("steam", "urban")),
        _atm("tram_breath_vapor", "Tram-stop breath", "Hang breath-vapor clouds in front of wool scarves at a tram stop, each exhale a small weather system.", "Wool rustle and a tram bell.", ("breath",)),
        _atm("desert_heat_shimmer", "Desert highway shimmer", "Ripple heat shimmer over a desert highway, the vanishing point dancing, asphalt looking wet with false water.", "Cicada heat and a far truck.", ("heat", "desert")),
        _atm("wet_asphalt_mirror", "Wet asphalt mirror", "Polish wet asphalt into a black mirror, streetlamp globes doubling, tire tracks as dull scribbles.", "Drip and a lone car on wet tar.", ("wet", "ground")),
        _atm("puddle_skyline", "Puddle skyline", "Use a curb puddle as a second city, signs inverted, a boot breaking the doubled cornices.", "Splash and city hush.", ("wet", "ground")),
        _atm("village_snowpack", "Village snow pack", "Lay a settled snow pack on a village roofscape, blue shadow in troughs, chimney bricks the only dark.", "Soft snow hush, a shovel far off.", ("snow", "ground")),
        _atm("red_clay_ruts", "Red clay ruts", "Churn red clay mud on a rural track, tire ruts filled with sky, splash dried on fenders.", "Wet mud suck under tires.", ("mud", "ground")),
        _atm("dirt_road_talc", "Dirt-road talc kick", "Kick dry talc dust from a dirt road behind a walking figure, the plume hanging, sagebrush still.", "Dry dust hiss and boot grit.", ("dust", "ground")),
        _atm("sycamore_leaf_wind", "Sycamore leaf wind", "Drive a river of dry sycamore leaves down a brownstone sidewalk, leaf-stars scraping, a stoop catching piles.", "Scratching leaves and wind in stoops.", ("wind", "leaves")),
        _atm("dawn_dew_lawn", "Dawn dew lawn", "Bead dawn dew on a spider-netted lawn, every blade a string of glass, first sun making them fire.", "Quiet insects and a distant sprinkler tick.", ("dew", "dawn")),
        _atm("stucco_noon_knife", "Stucco noon knife", "Hold noon air so a white stucco wall throws a knife shadow, no cloud, a ceramic pot the only dark.", "Cicadas and a far dog.", ("clear", "noon")),
        _atm("orchard_gold_dust", "Orchard golden dust", "Rake orchard dust at golden hour, backlight turning irrigation spray into gold fog between trunks.", "Sprinkler hiss and leaf rustle.", ("golden", "dust")),
        _atm("harbor_blue_hour", "Harbor blue-hour hush", "Soak a harbor in blue-hour hush, wet bollards, a single sodium lamp, water like dark glass.", "Water lap and a creaking hawser.", ("blue-hour",)),
        _atm("park_lamp_moisture", "Park-lamp moisture", "Let night moisture halo every park lamp, moths in the glow, benches glistening.", "Moth tick on glass and distant traffic.", ("night", "moisture")),
        _atm("black_wet_tavern", "Black-wet cobble", "Black-wet a cobblestone lane so every brick is lacquer, a tavern window the only color, rain just ended.", "Leftover drip and muffled bar murmur.", ("wet", "night")),
        _atm("tropical_verandah", "Tropical verandah humidity", "Weigh tropical humidity on a verandah, banana leaves dripping without rain, air thick enough to see, lizards still.", "Dripping leaves and a ceiling fan.", ("humidity", "tropical")),
        _atm("mesa_enamel", "Mesa enamel clear", "Clarify a mesa landscape to the last butte, shadows ink, sky a hard enamel, no haze at all.", "Dry wind over rock.", ("desert", "clear"), "atm_blizzard_grid"),
        _atm("granite_saddle", "Granite saddle thin air", "Thin the air on a granite saddle, distant peaks stacked without softening, a flag snapping, sky almost black-blue.", "Thin wind and flag snap.", ("mountain",)),
        _atm("cooling_stack_dusk", "Cooling-stack dusk steam", "Billow cooling-stack steam across a river at dusk, the plume pink, gantries as silhouettes.", "Industrial venting and river lap.", ("industrial", "steam")),
        _atm("terrace_chimney", "Terrace chimney pencil", "Pencil a thin chimney smoke column from a terrace fireplace into still evening, palm fronds unmoving.", "Quiet fire pop.", ("smoke",)),
        _atm("cliff_path_spray", "Cliff path sea spray", "Blast sea spray across a cliff path, ice-plant leaves jeweled, horizon a white grind.", "Surf grind and wind.", ("spray", "marine")),
        _atm("ice_fog_headlights", "Ice-fog headlights", "Fill a river town with ice fog, crystals glittering in headlights, eyelashes frosted, stop-lights as orbs.", "Ice-crystal tinkle and muffled engines.", ("ice-fog", "fog")),
        _atm("sun_shower_slide", "Sun-shower playground", "Fall a sun shower on a bright playground, rain glittering while the slide stays in full sun, a rainbow fragment.", "Light rain ticks and far voices.", ("sun-shower", "rain")),
        _atm("prairie_virga", "Prairie virga", "Hang virga streaks under a prairie anvil, rain evaporating before the ground, the soil still dust-dry.", "Dry wind and distant thunder.", ("virga", "storm")),
        _atm("two_lane_mirage", "Two-lane heat mirage", "Mirror a heat-mirage lake on a straight two-lane, telephone poles doubling, a pickup floating on fake water.", "Hot wind and tire drone.", ("mirage", "heat")),
        _atm("ozone_after_storm", "After-storm ozone clear", "Rinse the air after a storm so brick and leaf edges cut, leftover clouds as bright marble, gutters still running.", "Gutter rush and dripping trees.", ("post-storm", "clear")),
        _atm("altostratus_dome", "Altostratus courthouse", "Milk the sky with altostratus so a courthouse dome sits under a featureless white bowl, shadows barely there.", "Muted city, no bird song.", ("overcast",)),
        _atm("mammatus_fairground", "Mammatus fairground", "Pouch mammatus under a departing anvil over a fairground, the sky a quilt of hanging pouches, rides still.", "Distant thunder and a loose banner.", ("storm", "cloud")),
        _atm("thunderhead_soy", "Thunderhead over soy", "Build a thunderhead column over a soybean grid, the anvil spreading like a lid, the field still sunlit.", "Building rumble and insect hush.", ("storm",)),
        _atm("sheet_lightning_silos", "Sheet lightning silos", "Flash sheet lightning inside a cloud-mass over silos, the whole underbelly exposing rivets of light, ground dark.", "Thunder roll after a silent flash.", ("lightning",)),
        _atm("heat_lightning_corn", "Heat lightning corn", "Pulse distant heat lightning on a summer horizon beyond corn, no rain here, porch screens still.", "Cricket wash and far thunder.", ("lightning",)),
        _atm("rainbow_pasture", "Pasture rainbow", "Anchor a primary rainbow on a wet pasture, one foot in a barn roof, the grass supernaturally green.", "Dripping eaves and a far cow.", ("rainbow", "optical")),
        _atm("crepuscular_barge", "Crepuscular barge", "Shoot crepuscular rays through broken storm holes onto a river barge, god-beams in dirty air.", "Water slap and a tow engine.", ("rays", "optical")),
        _atm("sundog_harbor", "Frozen-harbor sun dog", "Plant a sun dog beside a winter sun over a frozen harbor, ice-halo fragments, cranes rimed.", "Ice boom and a chain rattle.", ("optical", "ice")),
        _atm("moon_halo_pines", "Pine cemetery moon halo", "Ring a full moon with an ice-crystal halo over a pine cemetery, headstones rimed, needles silver.", "Owl and frozen needle tick.", ("optical", "moon")),
        _atm("noctilucent_lake", "Noctilucent lake", "Streak electric-blue noctilucent clouds after midnight over a still lake, ripples copying the ribs.", "Almost silence, a fish jump.", ("optical", "night")),
        _atm("civil_twilight_close", "Civil twilight close", "Hold civil twilight over a suburban close, windows already lamp-warm, sky a green-blue gradient, no stars yet.", "Sprinkler tick and a porch door.", ("twilight",)),
        _atm("moonlight_quarry", "Moonlight quarry", "Paint a quarry in silver moonlight, limestone ledges stepped, a pool black, edges frost-bright.", "Drip in the pit and a far train.", ("moon",)),
        _atm("starlight_camp", "Starlight desert camp", "Expose starlight-only on a high desert camp, the milky band bright, tent a dark triangle, no moon.", "Tent nylon tick in cold.", ("night", "clear")),
        _atm("snowglow_spruce", "Overcast snow-glow", "Glow a snow-covered close under overcast, the ground brighter than the sky, spruce almost black.", "Snow hush and a plow far off.", ("snow", "overcast")),
        _atm("lake_effect_bands", "Lake-effect snow bands", "Stream lake-effect snow bands across a lakeshore boulevard, one block white, the next merely wet.", "Wind off water and wet tires.", ("snow",)),
        _atm("graupel_bleachers", "Graupel on bleachers", "Bounce graupel pellets on a stadium seat, soft hail like foam beads, a field still green.", "Pellets ticking plastic seats.", ("graupel", "hail")),
        _atm("freezing_rain_park", "Freezing-rain glass park", "Glaze every twig in freezing rain, a park becoming glass sculpture, sidewalk a sheet, streetlights doubled in ice.", "Ice ticking branches and a crack.", ("ice", "rain")),
        _atm("rime_ridge_fence", "Rime ridge fence", "Grow rime feathers on a ridge fence, windward ice-needles, the leeward wood still brown.", "Screaming ridge wind.", ("ice", "mountain")),
        _atm("hoarfrost_meadow", "Hoarfrost meadow", "Sugar hoarfrost on a meadow, every seed-head white, first sun melting the south faces only.", "Frost-crunch under a boot.", ("frost",)),
        _atm("cafe_dew_window", "Cafe dew window", "Fog a cafe window with interior dew, a finger-wiped viewport to a rainy street, condensation rivulets.", "Machine hiss and rain on pane.", ("condensation",)),
        _atm("night_bus_rain_pane", "Night-bus rain pane", "Sheet rain down a night bus window, city lights streaking, a reflected face over the drops.", "Wiper squeak and interior chatter.", ("rain", "night")),
        _atm("loft_skylight_rain", "Loft skylight rain", "Pepper a skylight with rain, the loft below getting moving caustics, hanging plants dripping.", "Rain on glass and a pipe drip.", ("rain",)),
        _atm("monsoon_courtyard", "Monsoon courtyard curtain", "Drop a monsoon curtain across a courtyard, one half dry tile, the other a waterfall off the eave.", "Waterfall eave and a scooter in water.", ("monsoon", "rain")),
        _atm("cloudburst_overpass", "Overpass cloudburst", "Burst a cloudburst on a freeway overpass, spray from trucks as walls, road paint disappearing.", "Wipers at full and truck spray.", ("downpour",)),
        _atm("thunderstorm_core", "Thunderstorm core", "Stand in a thunderstorm core: rain as rods, a green-black sky, a street tree thrashing, gutters overflowing.", "Thunder close and rain rods.", ("storm", "rain")),
        _atm("squall_ballfield", "Squall-line ballfield", "Roll a squall line of dust then rain across a ball field, the outfield vanishing, flags snapping.", "Flag snap then a sudden rain wall.", ("squall", "storm")),
        _atm("gust_front_town", "Gust-front town", "Push a gust-front wall of dust down a grid town, trash-can lids flying, tan air then dark rain.", "Metal lids and a wind roar.", ("dust", "storm")),
        _atm("haboob_palms", "Haboob palm avenue", "Advance a story-tall dust wall down a palm avenue, daylight turning to amber night.", "Rushing dust and palm fronds thrashing.", ("dust", "desert")),
        _atm("dune_sandstorm", "Dune camp sandstorm", "Scour a sandstorm across a dune camp, tents drumming, sun a rust coin, ripples moving on the slipface.", "Sand blasting nylon.", ("sand", "dust")),
        _atm("dust_devil_chaff", "Dust devil chaff", "Spin a dust devil across a fallow field, a skinny tan ghost, chaff in the corkscrew.", "Dry chaff hiss.", ("dust",)),
        _atm("prairie_wind_waves", "Prairie wind waves", "Comb prairie grass in long wind-waves toward a grain elevator, cloud-shadows racing, no rain.", "Grass hiss and elevator metal tick.", ("wind",)),
        _atm("slot_canyon_sand", "Slot-canyon wind", "Funnel wind down a slot of red rock, sand hissing along the floor, a ribbon of sky still blue.", "Sand hiss and echo wind.", ("wind", "desert")),
        _atm("glacier_katabatic", "Glacier katabatic", "Pour katabatic cold air down a glacier tongue, flags snapping downhill, breath instantly ice.", "Downhill roar and ice crack.", ("mountain", "ice")),
        _atm("cornice_spindrift", "Cornice spindrift", "Blow spindrift off an alpine cornice, a snow-smoke banner against cobalt, rocks rime-toothed.", "Spindrift hiss and ridge wind.", ("snow", "mountain")),
        _atm("glacier_valley_glare", "Glacier valley glare", "Blast glacier glare so a valley is overexposed white, ice-blue crevasses the only drawing.", "Ice drip and a far rumble.", ("ice", "optical")),
        _atm("pack_ice_sea_smoke", "Pack-ice sea smoke", "Steam sea-smoke off pack ice, black water leads smoking, a ship rail rimed.", "Hull creak and steaming leads.", ("ice", "steam")),
        _atm("coastal_highway_fog", "Coastal highway fog", "Advection-fog a coastal highway, headlights as cones, a lighthouse beam a dull smudge.", "Foghorn and wet tires.", ("fog", "marine")),
        _atm("hollow_radiation_fog", "Hollow radiation fog", "Pool radiation fog in a hollow after a clear night, a bridge deck above it, treetops as a forest on a cloud.", "Dripping and a truck on the bridge.", ("fog",)),
        _atm("upslope_fog_town", "Upslope fog town", "Push upslope fog against a mountain town, streets appearing floor by floor as you descend.", "Muffled church bell.", ("fog", "mountain")),
        _atm("freezing_fog_cables", "Freezing fog cables", "Deposit freezing-fog rime on a suspension cable, every wire furred, the river below invisible.", "Ice tick on cables and a horn.", ("ice-fog",)),
        _atm("pine_needle_drizzle", "Pine-needle drizzle", "Bead drizzle on pine needles until each fascicle is jeweled, a forest floor barely damp.", "Tiny drops on needles.", ("drizzle",)),
        _atm("tin_porch_rain", "Tin-porch rain", "Drum rain on a corrugated tin porch, water-beads racing the channels, a rocking chair still.", "Rain on tin and a chair creak.", ("rain",)),
        _atm("canvas_awning_rain", "Canvas awning rain", "Darken a canvas awning with rain, a market alley steaming, fruit skins beading.", "Rain on canvas and a drip-bucket.", ("rain",)),
        _atm("rainforest_drip", "Rainforest drip stages", "Drip rainforest rain in stages: leaf-roof first, then understory, leaf-cups overflowing onto ferns.", "Layered drips and a frog.", ("rain", "tropical")),
        _atm("herringbone_cobble_rain", "Herringbone cobble rain", "Gloss rain on herringbone cobble, cart ruts as mirrors, gas-lamp reflections broken.", "Rain on stone and a shutter.", ("rain",)),
        _atm("glass_tower_sheet", "Glass-tower rain sheet", "Sheet rain down a glass tower, interior offices still, each floor a different reflection of clouds.", "Wind-driven rain on curtain wall.", ("rain", "urban")),
        _atm("neon_noodle_rain", "Neon noodle rain", "Mix neon with rain so a noodle-shop sign melts on wet pavement, steam from a grate, umbrellas as colored lids.", "Rain, sizzle, and a shop bell.", ("rain", "neon")),
        _atm("monsoon_curb_flood", "Monsoon curb flood", "Flood monsoon puddles to curb height, scooter wake, tropical trees dripping, a reflected sky.", "Scooter through water and heavy drip.", ("monsoon", "wet")),
        _atm("hot_asphalt_steam_rain", "Hot-asphalt steam rain", "Steam a tropical downpour off hot asphalt, rain and vapor indistinguishable, a mango cart huddled.", "Rain hissing on hot tar.", ("tropical", "steam")),
        _atm("boardwalk_salt_haze", "Boardwalk salt haze", "Haze a boardwalk in salt air, distant ride structure soft, near painted rails crisp, gulls sharp.", "Gulls and a soft surf.", ("marine", "haze")),
        _atm("brown_basin_smog", "Brown-basin smog", "Sit a city in brown-air basin smog, mountains gone, near murals still saturated, sun white.", "Flattened traffic drone.", ("smog", "haze")),
        _atm("peat_bog_smoke", "Peat-bog smoke", "Drift peat smoke across a bog road, the air amber, heather dark, a cottage lamp early.", "Peat fire and wind in heather.", ("smoke",)),
        _atm("snowed_cabin_inversion", "Cabin inversion smoke", "Leak woodstove smoke from a snowed cabin eave, the plume flattening under inversion, split logs in the yard.", "Stove draw and snow tick on metal.", ("smoke", "inversion")),
        _atm("mill_stack_stripe", "Mill-stack plume", "Stripe a mill-stack plume across a brick-mill town, the smoke pink then gray over rail yards.", "Distant coupling cars.", ("industrial", "smoke")),
        _atm("cooling_tower_cumulus", "Cooling-tower cumulus", "Roll cooling-tower cumulus over a river plant, the man-made clouds the only weather, vapor blooming.", "Plant hum and river.", ("industrial", "steam")),
        _atm("foundry_door_glow", "Foundry door steam", "Vent foundry steam and orange glow from a mill door, snowflakes melting in the plume, slag texture underfoot.", "Furnace roar and melting flakes hiss.", ("industrial", "steam")),
        _atm("laundry_grate_steam", "Laundry-grate steam", "Billow laundry steam from a basement grate, winter pedestrians' legs, wet brick, vapor in a column.", "Steam hiss and footsteps.", ("steam", "urban")),
        _atm("night_kitchen_pass", "Night-kitchen steam", "Fill a night-kitchen pass with steam, stainless catching, a plate emerging from fog, tile wet.", "Sizzle, plate clack, extractor.", ("steam",)),
        _atm("subway_grate_winter", "Subway-grate winter steam", "Gush subway-grate steam around ankles on a winter sidewalk, a grate glowing, taxis smearing.", "Subway rumble and steam.", ("steam", "urban")),
        _atm("geyser_sinter", "Geyser sinter steam", "Jet geyser steam against a cold blue sky, sinter terraces wet, onlookers as silhouettes in the plume.", "Geyser roar and dripping sinter.", ("steam",)),
        _atm("riverside_hotspring", "Riverside hot-spring steam", "Steam a riverside hot spring, snow meeting mineral-blue water, vapor flattening at dusk.", "Bubbling mineral and a river.", ("steam",)),
        _atm("volcanic_ash_town", "Ash-veiled town", "Veil a town in fine volcanic ash, a gray flour on awnings, sun a copper disk, footprints on cars.", "Dry ash crunch underfoot.", ("ash", "dust")),
        _atm("cottonwood_june", "Cottonwood fluff June", "Snow the air with cottonwood fluff in June, a river path looking like a warm blizzard, seeds catching in hair.", "Seed fluff and a river.", ("pollen",)),
        _atm("dandelion_vacant_lot", "Dandelion-seed vacant lot", "Backlight a dandelion-seed blizzard over a vacant lot, each parachute a spark, chain-link catching tufts.", "Dry weed tick and a far highway.", ("pollen",)),
        _atm("waterfall_footbridge", "Waterfall footbridge mist", "Soak a footbridge in waterfall mist, a rainbow in the spray, moss black-green, stone slick.", "Waterfall roar.", ("spray", "mist")),
        _atm("pier_piling_shorebreak", "Pier piling shore-break", "Explode shore-break spray against a pier piling, foam hanging, a lens beaded, planks dark.", "Boom of shore-break.", ("spray", "marine")),
        _atm("ferry_bow_rainbow", "Ferry bow spray", "Throw bow-spray from a ferry, a rainbow in the droplets, the city approaching, deck wet.", "Bow slap and wind.", ("spray",)),
        _atm("ballpark_sprinkler", "Ballpark sprinkler gold", "Catch late-day sprinkler spray in a ballpark outfield, each arc a gold hyphen, grass steaming.", "Sprinkler ratchet and wet grass.", ("spray",)),
        _atm("plaza_fountain_mist", "Plaza fountain mist", "Halo a plaza fountain in wind-torn mist, granite wet, pigeons shaking, sun making a small rainbow.", "Fountain white-noise and wings.", ("spray",)),
        _atm("paddock_horse_breath", "Paddock horse-breath", "Jet horse-breath in a winter paddock, nostrils steaming, frost on the fence, hay gold.", "Horse snort and hay rustle.", ("breath",)),
        _atm("tar_roof_shimmer", "Tar-roof heat shimmer", "Shimmer a tar rooftop at mid-afternoon, HVAC units wobbling, the skyline dancing.", "HVAC drone and hot tar tick.", ("heat", "urban")),
        _atm("wet_marble_palace", "Wet marble palace", "Polish a wet marble plaza after rain, palace columns doubling, pigeons walking on sky.", "Pigeon wings and drip from cornice.", ("wet", "ground")),
        _atm("oil_slick_forecourt", "Oil-slick forecourt", "Iris an oil-slick puddle with spectrum rings, a garage forecourt, neon breaking into colors.", "Drip of oil and a distant compressor.", ("wet", "ground")),
        _atm("sastrugi_barn", "Sastrugi barn drift", "Sculpt wind-carved snow drifts against a red barn, sastrugi texture, one door dug out.", "Wind on barn tin.", ("snow", "ground")),
        _atm("pine_bough_dump", "Pine-bough snow dump", "Load pine boughs until they dump, a forest path muffled, trunks black, snow-smoke when a branch lets go.", "Sudden dump thud and hush.", ("snow",)),
        _atm("crosswalk_slush", "Crosswalk brown slush", "Churn brown slush at a crosswalk, salt stains, bus spray, a yellow signal smeared.", "Slush slap and bus hiss.", ("slush", "wet")),
        _atm("overpass_black_ice", "Overpass black ice", "Sheen black ice on an empty overpass, the asphalt looking merely wet, city lights long in the glaze.", "Almost silence, a far horn.", ("ice", "ground")),
        _atm("farmhouse_frost_ferns", "Farmhouse frost ferns", "Grow frost ferns on a farmhouse pane, kitchen warmth implied, the yard a blur through ice-flowers.", "Kettle and wind at the sash.", ("frost",)),
        _atm("eave_icicle_thaw", "Eave icicle thaw", "Drip icicles from a gutter edge in thaw, each drop catching sun, a dagger row shortening.", "Drip into a puddle.", ("thaw", "ice")),
        _atm("alley_snowmelt_braids", "Alley snowmelt braids", "Run snowmelt braids down a dirt alley, winter debris, prints in the mud-snow mix.", "Trickle and a dripping fire escape.", ("thaw", "mud")),
        _atm("sideways_rain_shelter", "Sideways rain shelter", "Drive rain sideways under a bus shelter, the far wall dry, legs wet, flags traveling with the gust.", "Rain hitting the back wall and flag snap.", ("rain", "wind")),
        _atm("polar_diamond_dust", "Polar diamond dust", "Sparkle diamond dust in a polar street, ice needles falling from a clear sky, every lamp a pillar.", "Faint ice tinkle.", ("ice", "optical")),
        _atm("frozen_waterfall_cave", "Frozen waterfall cave", "Lock a waterfall into amber-white ice, a cave of blue behind, spray still smoking at the lip.", "Ice groan and a trickle.", ("ice",)),
        _atm("lightning_pier_beads", "Lightning-lit pier rain", "Freeze-flash raindrops with a lightning bolt over a pier, every drop a bead, the sea white for a frame.", "Thunder crack and rain.", ("lightning", "rain")),
        _atm("anvil_iridescence", "Anvil iridescence", "Iridesce the sunward edge of an anvil, pastel oil-slick on ice-cloud, a field dark below.", "Distant thunder.", ("optical", "storm")),
        _atm("first_rain_dust_craters", "First-rain dust craters", "Darken dry earth to chocolate in the first minutes of rain, dust craters becoming mud cups, leaves jumping.", "First fat drops on dirt.", ("rain", "ground")),
        _atm("mackerel_port", "Mackerel sky port", "Scale a mackerel sky over a fishing port, altocumulus ripples, boats still, the pattern slowly traveling.", "Gulls and a halyard tick.", ("cloud",)),
        _atm("lenticular_cone", "Lenticular over cone", "Park a lenticular disk over a volcanic cone, the cloud stationary, wind screaming implied on the slopes.", "High wind roar.", ("cloud", "mountain")),
        _atm("pileus_silk_cap", "Pileus silk cap", "Cap a growing tower with pileus silk, the smooth hat over a soybean field.", "Still air and a far rumble.", ("cloud",)),
        _atm("coastal_roll_cloud", "Coastal roll cloud", "Slide a roll cloud down a coast like a tube, the rest of the sky clear, surfers pointing.", "Surf and a sudden cool gust.", ("cloud", "marine")),
        _atm("scud_rest_stop", "Scud at rest-stop", "Race scud fragments under a dark base, a highway rest-stop, the low clouds shredded and traveling.", "Truck idle and wind.", ("cloud",)),
        _atm("fogbow_cliff", "Cliff fog-bow", "Draw a white fog-bow over a cliff trail, no color, the sun behind, the drop-off gone in white.", "Wind and a distant buoy.", ("optical", "fog")),
        _atm("brocken_glory_ridge", "Ridge Brocken glory", "Cast a Brocken glory around a shadow on a cloud deck from a ridge, a rainbow halo on the fog below.", "Wind in alpine grass.", ("optical", "mountain")),
        _atm("polar_night_village", "Polar-night village", "Hold polar-night blue at midday, a fishing village in cobalt, windows gold, snow reflecting a sun that never rises.", "Snow crunch and a generator far.", ("polar", "night")),
        _atm("midnight_sun_fjord", "Midnight-sun fjord", "Stretch midnight-sun glitter on a fjord, the disk circling, cabins in perpetual gold, no real night.", "Water lap in endless evening.", ("polar", "golden")),
        _atm("inversion_smoke_lid", "Inversion smoke-lid", "Cap chimney smoke under an inversion so a valley town wears a flat smoke-lid, peaks in sun.", "Muffled dogs and still air.", ("inversion", "smoke")),
        _atm("shrine_incense_shafts", "Shrine incense shafts", "Layer incense as interior weather, sun-shafts becoming solid in a shrine, gilt catching, floorboards dusty-gold.", "Soft bell and a floor creak.", ("incense", "interior")),
        _atm("lake_campfire_smoke", "Lake campfire smoke", "Lean campfire smoke along a lake at dusk, the plume hugging water, sparks, pine silhouettes.", "Fire crackle and a loon far.", ("smoke",)),
        _atm("backyard_barbecue_plume", "Backyard barbecue plume", "Drift barbecue smoke across a backyard at golden hour, chain-link, a plume following the fence line.", "Fat drip sizzle.", ("smoke",)),
        _atm("windshield_pollen_smear", "Windshield pollen smear", "Yellow a windshield in pollen so thick the wipers smear gold, a suburban driveway, spring trees.", "Wiper smear and bees.", ("pollen",)),
        _atm("canal_petal_storm", "Canal petal storm", "Storm pink petals down a canal walk, water covered, a bicycle leaving a wake in blossoms.", "Petals on water and a bike bell.", ("petals", "wind")),
        _atm("wheat_oak_waves", "Wheat-field wind toward oak", "Run wind-waves through ripe wheat toward a lone oak, cloud-shadows, grain whispering.", "Wheat hiss.", ("wind",)),
        _atm("civic_flag_row", "Civic flag row", "Snap a row of unmarked flags on a civic plaza, sky enamel, the cloth the only weather, shadows whipping.", "Flag snap and plaza echo.", ("wind", "clear")),
        _atm("frost_football_field", "Pre-dawn frost field", "White a football field in pre-dawn frost, yard lines faint, breath from a single figure, sky still navy.", "Frost crunch and a whistle far.", ("frost", "dawn")),
        _atm("bakery_blue_hour_snow", "Bakery blue-hour snow", "Fall blue-hour snow in big flakes past a bakery window, interior gold, flakes slowing near the pane.", "Hush and a door chime.", ("snow", "blue-hour")),
        _atm("bridge_sodium_fog", "Bridge sodium fog", "Halo night fog around sodium lamps on a bridge, each globe a dandelion of glow, cables disappearing.", "Foghorn and wet tires.", ("fog", "night")),
        _atm("used_car_overcast", "Used-car overcast fluorescent", "Turn overcast noon into a giant fluorescent, a used-car lot with no shadow, chrome dull, sky white.", "Lot flags limp, a radio far.", ("overcast", "noon")),
        _atm("warehouse_cloud_patches", "Warehouse sun-shade patches", "Patch broken cloud so a warehouse roof strobes between sun and shade, puddles blinking.", "Metal tick as sun hits.", ("cloud",)),
        _atm("wall_cloud_silos", "Wall cloud over silos", "Lower a rotating wall cloud over prairie silos, the base looking close enough to touch, dust spinning up.", "Siren far and grain-dryer hum.", ("storm",)),
        _atm("pink_sunset_virga", "Pink sunset virga", "Color sunset virga pink under a departing cell, the streaks not reaching a still-dry highway.", "Dry wind and a far rumble.", ("virga", "golden")),
        _atm("marine_sunrise_cypress", "Marine-layer sunrise cypress", "Break sunrise through a marine layer as a red disk, a cliff path above the fog ocean, cypress black.", "Surf under fog.", ("marine", "dawn")),
        _atm("swamp_cypress_mist", "Cypress-knee swamp mist", "Hang swamp mist between cypress knees, bubbles in black water, moss beading, air green-gray.", "Frogs and a mosquito whine.", ("mist", "swamp")),
        _atm("jungle_track_steam", "Jungle-track after-rain steam", "Steam a jungle track after rain, leaf-litter smoking, the leaf-roof dripping, butterflies working the sun-holes.", "Drip and insect roar.", ("tropical", "steam")),
        _atm("tundra_standing_water", "Tundra close overcast", "Flatten tundra under a close overcast, lichen and standing water, a cabin, no shadow, wind.", "Wind over puddles.", ("tundra", "overcast")),
        _atm("salt_flat_erase", "Salt-flat noon erase", "Erase horizon on a salt flat at noon, white crust polygons, a figure standing in glare, sky and ground one.", "Salt crunch and empty wind.", ("desert", "optical")),
        _atm("sage_two_lane_noon", "Sage two-lane noon", "Cut high-desert noon so sage throws short black shadows, a two-lane, ranges knife-sharp.", "Dry insect and a far pickup.", ("desert", "noon")),
        _atm("redrock_rain_potholes", "Red-rock rain potholes", "Saturate red rock after a desert rain, potholes as skies, sandstone dark, a brief waterfall in a crack.", "Trickle in sandstone.", ("desert", "wet")),
        _atm("glass_canyon_shimmer", "Glass-canyon heat shimmer", "Shimmer an urban canyon of glass at late afternoon, taxi roofs wobbling, AC drip, a scrap of sky.", "AC drip and horn.", ("heat", "urban")),
        _atm("humid_porch_bugs", "Humid porch-light bugs", "Thicken a humid night with bugs in a porch light, air visible as wings, screen door, a swamp of glow.", "Insect roar and a screen slap.", ("humidity", "night")),
        _atm("wood_sauna_snow_window", "Sauna steam snow window", "Fill a wood sauna with steam so bodies are shapes, a small window of snow, ladle drip on stones.", "Hiss on stones and wood creak.", ("steam", "interior")),
        _atm("laundry_press_ghosts", "Laundry-press steam ghosts", "Burst iron-press steam in a laundry, shirts as ghosts, fluorescent, wet tile.", "Press hiss and a radio.", ("steam", "interior")),
        _atm("stage_apron_low_fog", "Stage-apron low fog", "Fog a stage apron with low white vapor, footlights cutting sheets, curtains heavy.", "HVAC and a board creak.", ("fog", "interior")),
        _atm("river_dawn_towboat", "River-dawn fog towboat", "Unspool river fog at first light, trees as smudges, water invisible, a towboat a shadow.", "Muffled horn and drip.", ("fog", "dawn")),
        _atm("desert_milky_band", "Desert-clear milky band", "Hold desert-clear night so the milky band is weather, a two-lane, sage, no humidity veil.", "Coyote far and cooling rock tick.", ("clear", "night", "desert")),
        _atm("hydrant_packing_snow", "Hydrant packing snow", "Pack wet snow on a hydrant until it becomes a white sculpture, a shoveled path, city gray.", "Shovel scrape.", ("snow", "urban")),
        _atm("aurora_snow_field", "Aurora-colored snow", "Glow green aurora on a snow field, the snow taking the color, spruce black, no moon.", "Snow hush and a dog far.", ("optical", "snow")),
        _atm("desert_golden_buttes", "Desert golden buttes", "Rake golden-hour sun across desert buttes, long purple shadows, dust as gold fog, a two-lane flashing.", "Dry wind and a hawk cry.", ("golden", "desert")),
        _atm("black_wet_night_neon", "Black-wet night neon", "Black-wet a night avenue so neon writes twice, once in air and once in tar, umbrellas as commas.", "Rain on awnings and a taxi hiss.", ("wet", "night", "neon")),
    ]
    return rows


def genre_looks() -> list[dict[str, Any]]:
    rows = [
        _gen("noir_venetian", "Noir venetian office", "Stripe a detective office with venetian-slat sun, cigarette-era dust hanging in the bars, oak desk and a slow ceiling fan, the room tobacco-dark beyond the blinds.", ("noir",), "gen_screwball_highkey", "gen_romcom_bounce"),
        _gen("neo_noir_wet", "Neo-noir wet street", "Gloss a rain-slick downtown canyon with shop-window tungsten, asphalt specularity, wet fire-escape iron, masonry walls making a black river of street.", ("noir", "wet"), "gen_solarpunk_glasshouse"),
        _gen("western_dust_noon", "Western dust noon", "Bake a false-front street in vertical noon, alkali dust hanging, hitching rails throwing knife shadows, clapboard texture raw.", ("western",), "gen_snowbound_cabin"),
        _gen("western_grit_close", "Western grit close", "Rake sidelight across a close face so alkali grit sits in pores and hat-felt, a porch post as bokeh, sweat catching in stubble.", ("western", "close")),
        _gen("screwball_highkey", "Screwball day interior", "Flood a day interior with high-key bounce, silk robe texture, art-deco moldings, overlapping bodies in a bright parlor, shadows almost gone.", ("comedy",), "gen_noir_venetian", "gen_horror_hallway_under"),
        _gen("melodrama_window", "Melodrama window", "Place a figure in a tall window of a melodrama house, net-curtain texture, weather as emotion on the pane, the room falling away, the face half-lit by glass.", ("drama",)),
        _gen("gothic_candle_nave", "Gothic candle nave", "Model a stone corridor with candle clusters, soot texture on plaster, dripping wax, the space a nave of moving gold and deep black.", ("gothic",)),
        _gen("slasher_fridge_practical", "Slasher night practical", "Underexpose a night house so a fridge practical or TV is the only key, linoleum texture, hallway depth, the dark as a solid extra.", ("horror",), "gen_romcom_bounce"),
        _gen("found_footage_led", "Found-footage LED shake", "Shake a night hallway with on-camera LED, wallpaper texture swimming, doorframes tilting, the wide lens making the corridor a tunnel.", ("horror", "found")),
        _gen("bodycam_precinct", "Body-cam precinct", "Ride a chest-cam through a precinct corridor, fluorescent smear, uniform fabric along the bottom, radios and door-glass, the space always slightly too close.", ("procedural", "pov")),
        _gen("heist_warehouse", "Heist cool tungsten", "Cool the tungsten of a night warehouse so faces go a little green-gold, crate wood texture, skylight moon as a rim, the space a grid of aisles.", ("heist",)),
        _gen("romcom_bounce", "Rom-com bounce beauty", "Bounce a beauty key off a white wall in a day interior, skin smooth, a messy apartment cheerful, catchlights round, the space warm and close.", ("comedy", "beauty"), "gen_horror_hallway_under", "gen_noir_venetian"),
        _gen("period_candle_day", "Period candle and daylight", "Mix window daylight with practical candles in a period room, linen texture, plaster walls, the two sources fighting on a face, no electric implied.", ("period",)),
        _gen("kitchen_sink_overcast", "Kitchen-sink overcast", "Hold a kitchen-sink interior under overcast window, chipped enamel texture, laundry on chairs, the room small and true, no beauty fill.", ("realist",), "gen_musical_cyc"),
        _gen("social_realist_stair", "Social-realist available stair", "Light a public stairwell with whatever the window gives, scuffed paint texture, the space unstyled, faces as found.", ("realist",)),
        _gen("prestige_shallow", "Prestige shallow complementary", "Grade a shallow-focus interior with complementary shadow-teal and honey-key, wool and wood texture, a window as a soft rectangle, faces separated from the room.", ("prestige",)),
        _gen("action_sun_haze", "Action sun-backlight haze", "Backlight a chase street with sun through kicked dust, asphalt grit, vehicles as silhouettes, the space a tunnel of glare.", ("action",)),
        _gen("superhero_comic_key", "Superhero comic key", "Key a rooftop figure with a comic hard key and a colored rim, cape weave, the city a graphic drop, shadows cut like ink.", ("superhero",)),
        _gen("musical_cyc", "Musical saturated theatrical", "Saturate a theatrical stage with colored cyc wash, sequin texture throwing sparks, the proscenium a candy frame, follow-spot as a coin on the face.", ("musical",), "gen_kitchen_sink_overcast"),
        _gen("horror_hallway_under", "Horror underexposed hallway", "Underexpose a residential hallway so the far door becomes a weak rectangle, carpet nap swallowing, wallpaper pattern barely drawn, the dark owning the volume.", ("horror",), "gen_romcom_bounce", "gen_screwball_highkey"),
        _gen("cosmic_shore_scale", "Cosmic-horror shore scale", "Dwarf a shoreline figure under a sky that is too large, faint wrong colors in the overcast, wet pebbles, the ocean like a slab, scale that refuses comfort.", ("horror", "scale")),
        _gen("folk_standing_stones", "Folk-horror overcast field", "Stand a figure in an overcast field of standing stones, wool texture, no sun, the village a gray lip on the horizon, the air still and wrong.", ("horror", "folk")),
        _gen("thriller_parking_long", "Thriller long-lens surveillance", "Park a long-lens view across a parking structure, a subject small in one bay, sodium texture, concrete ribs counting, the space observed not entered.", ("thriller",)),
        _gen("spy_plaza_tele", "Spy night telephoto", "Compress a night plaza on a long lens, a figure isolated in a hotel-marquee pool, bokeh of fountain spray, surveillance distance, heat ripple on stone.", ("spy",)),
        _gen("war_trench_dust", "War handheld dust", "Handheld a trench lip in dusty noon, grit on the lens, uniform weave, the space a ditch with a slice of blown sky.", ("war",)),
        _gen("submarine_red", "Submarine red practical", "Bathe a submarine compartment in red battle practicals, pipe-lagging texture, gauges catching, the bunk space cramped and sweating.", ("war", "interior")),
        _gen("spacecraft_led_ribs", "Spacecraft practical LED", "Key a spacecraft cabin with practical LED strips along the ribs, velcro texture, cable bundles, a small window of black, dust floating in the beams.", ("scifi",)),
        _gen("cyberpunk_wet_neon", "Cyberpunk wet neon", "Flood a rain-wet alley with competing neon-magenta shop, cyan crosswalk-so puddles become stained glass, steam texture, fire-escapes as black geometry.", ("cyber", "wet"), "gen_solarpunk_glasshouse"),
        _gen("solarpunk_glasshouse", "Solarpunk clear sun", "Wash a glasshouse street in clear sun, vine texture on solar-louvers, clean water channels, the space open and photosynthetic, no haze of industry.", ("solar",), "gen_cyberpunk_wet_neon", "gen_neo_noir_wet"),
        _gen("rural_raking_farm", "Rural raking Americana", "Rake late sun across a farm porch, peeling paint texture, a screen door, fields as gold bands, the space honest and long-shadowed.", ("rural",)),
        _gen("coastal_magic_hour", "Coastal magic-hour", "Gild a coastal cliff house at magic hour, salt-weathered wood texture, windows taking the disk, the ocean a hammered sheet below.", ("coastal", "golden")),
        _gen("mountain_sublime", "Mountain sublime wide", "Hold a tiny figure against a mountain wall in clear air, granite texture, weather a small cloud on the peak, the space sublime and uncomfortably large.", ("mountain", "scale")),
        _gen("sports_long_iso", "Sports long-lens isolation", "Isolate a runner in compressed stands on a long lens, sweat texture, crowd as a smear of color, the track space flattened to a ribbon.", ("sports",)),
        _gen("fashion_hard_beauty", "Fashion hard beauty", "Punch a hard beauty key with a silver bounce, skin pore-true, a cyclorama or loft brick, fashion space emptied of clutter, shadow edge knife-clean.", ("fashion",)),
        _gen("music_video_smear", "Music-video smear shutter", "Smear a night performance with a long shutter, LED wash dragging, sequin and sweat streaks, the club volume becoming ribbons of color.", ("music",)),
        _gen("product_wrap", "Commercial product wrap", "Wrap a tabletop hero in seamless white bounce, product material microdetail, a horizon of infinity paper, speculars walking in a controlled orbit.", ("commercial",)),
        _gen("doc_available_street", "Documentary available street", "Take available street light as found, coat-wool and brick texture, unposed timing, the sidewalk space unstyled and present-tense.", ("doc",)),
        _gen("verite_bounce_room", "Verite bounce room", "Bounce a small fixture off a ceiling in a lived room, carpet stain texture, overlapping talk, the space a real apartment not a set.", ("doc", "verite")),
        _gen("observational_lockoff", "Observational locked-off", "Lock off on a doorway in mixed available, scuff texture on the jamb, people entering and leaving a room that does not perform.", ("doc", "locked")),
        _gen("giallo_stair_gel", "Giallo color-gel night", "Gel a stairwell night in acid green and wine red, patent-leather reflections, terrazzo floors, a gloved hand on a banister, the space a candy-colored threat.", ("giallo", "horror")),
        _gen("gothic_romance_mist", "Gothic romance mist", "Veil a manor lawn in mist with window gold leaking, wet wool and iron-gate texture, the house a dark block, two figures small in weather.", ("gothic", "romance")),
        _gen("caper_night_cool", "Caper cool night", "Cool a night rooftop with distant neon bounce, gravel texture, a skyline as a diagram, faces in a pool of a work lamp, the space playful and precise.", ("caper", "heist")),
        _gen("courtroom_fluorescent", "Courtroom available fluorescent", "Light a courtroom with tired fluorescents and high windows, wood-panel texture, dust in the shafts, the space civic and unflattering.", ("procedural",)),
        _gen("hospital_green", "Hospital green practical", "Tint a hospital corridor with green-practical fluorescents, linoleum shine, curtain texture, the space endless and humming.", ("hospital",)),
        _gen("school_day_bounce", "School-day bounce", "Bounce day through classroom windows onto scuffed desks, chalk-dust texture, construction-paper color, the space ordinary and loud with sun.", ("school",)),
        _gen("beach_hard_sun", "Beach-day hard sun", "Blast beach noon with overhead sun, salt-skin texture, umbrellas as hard disks of shade, the sand space overexposed and glittering.", ("beach",)),
        _gen("club_strobe_fog", "Night-club strobe fog", "Strobe a night club so dancers freeze in white shards between darkness, fog texture catching each pop, a low ceiling of truss, faces unreadable in the black intervals.", ("club",)),
        _gen("rain_noir_alley", "Rain-noir alley", "Key a rain alley with a single fire-escape practical, brick running with water, dumpster metal, the space a wet slot of threat and speculars.", ("noir", "wet")),
        _gen("desert_western_magic", "Desert western magic hour", "Gild a desert western street at magic hour, adobe texture, long blue shadows, dust as gold, the false-fronts turning copper.", ("western", "golden")),
        _gen("snowbound_cabin", "Snow-bound isolation", "Hold a cabin window as the only warm rectangle in a snow field, frost-on-glass texture, the interior small, the exterior a white infinity.", ("isolation", "snow"), "gen_western_dust_noon"),
        _gen("jungle_leaf_vault", "Jungle wet leaf-vault", "Dapple wet jungle understory with broken sun through a leaf-vault, bark slick, vines as ropes, steam in the shafts, the path a tunnel of green.", ("jungle",), "gen_arctic_whiteout"),
        _gen("arctic_whiteout", "Arctic white-out", "Erase scale in an arctic white-out, a figure as a dark comma, no horizon, parka texture the only grain, glow coming from everywhere and nowhere.", ("arctic",), "gen_jungle_leaf_vault"),
        _gen("interrogation_bulb", "Noir interrogation bulb", "Hang a single bare bulb over a metal table, the rest of the box in falloff, sweat sheen, a one-way glass suggestion as a dark rectangle.", ("noir", "interior")),
        _gen("boxing_overhead", "Boxing-ring overhead", "Drop an overhead ring key so sweat and resin texture shine, ropes as lines, the crowd a dark bowl, the canvas space a bright island.", ("sports",)),
        _gen("diner_night_fluoro", "Diner night fluorescent", "Wash a night diner in cool fluorescent, laminate texture, pie case glow, rain on the glass, the booth space a lit aquarium on a dark street.", ("diner", "night")),
        _gen("motel_neon_vacancy", "Motel neon vacancy", "Key a motel facade with vacancy neon, pebble-dash texture, a pool of pink on wet concrete, the courtyard space empty and humming.", ("neon", "night")),
        _gen("gas_station_night", "Gas-station night", "Island a night forecourt under a bright fluorescent soffit, oil-stain texture, pumps as totems, desert dark beyond the lot.", ("night",)),
        _gen("carnival_tungsten", "Carnival tungsten", "Warm a carnival midway with tungsten bulb strings, painted-wood texture, fried-sugar air implied, the space a tunnel of rides and sawdust.", ("carnival",)),
        _gen("church_nave_shafts", "Church nave god-rays", "Drop dust-shafts from clerestory windows down a nave, pew-wood texture, stone floors, the space a long hush of gold and shadow.", ("sacred",)),
        _gen("victorian_gaslight", "Victorian parlor gaslight", "Model a Victorian parlor with gaslight practicals, velvet and walnut texture, wallpaper dense, the space cluttered and amber.", ("period",)),
        _gen("silent_era_highkey", "Silent-era high-key", "Flood a silent-era interior in high-key daylight, greasepaint texture, painted flats, the space theatrical and shadowless except for eyes.", ("period", "comedy")),
        _gen("expressionist_paint", "Expressionist painted shadow", "Paint shadows as architecture on studio walls, jagged texture, a staircase that is also a graphic, the space a mind not a room.", ("expressionist",)),
        _gen("new_wave_street", "New-wave street available", "Grab available street bounce on a cafe terrace, jumper-knit texture, handheld edges, the boulevard space casual and present.", ("new-wave", "doc")),
        _gen("teen_string_lights", "Teen bedroom string-lights", "Key a teen bedroom with string-lights and a desk lamp, poster texture, unmade bed, the space a cave of small practicals.", ("teen",)),
        _gen("road_windshield", "Road-movie windshield", "Look through a windshield at traveling weather, dash texture, bugs on glass, the cabin space a moving interior against a rushing land.", ("road",)),
        _gen("library_dust_shaft", "Library dust shaft", "Drop a sun shaft through library stacks, paper and leather texture, motes solid, the aisle space a gold tunnel of spines.", ("interior",)),
        _gen("gallery_white_cube", "Gallery white cube", "Even a white-cube gallery with skylight bounce, painted-wall texture, a single work, the space emptied to a hush of edges.", ("gallery",)),
        _gen("loft_industrial", "Loft industrial window", "Rake industrial windows across a loft, brick and iron texture, dust in the beams, the floor space a factory becoming a home.", ("loft",)),
        _gen("penthouse_city_night", "Penthouse city night", "Mix city-night bounce with interior practicals in a penthouse, glass texture, a skyline as wallpaper, the space expensive and thin.", ("night", "interior")),
        _gen("bunker_concrete", "Bunker concrete practical", "Key a bunker with a single cage practical, concrete texture, pipes sweating, the space a buried box.", ("war", "interior")),
        _gen("lab_clean_fluoro", "Lab clean fluorescent", "Wash a laboratory in even fluorescents, stainless and tile texture, the bench space sterile, reflections of overheads in glassware.", ("lab",)),
        _gen("newsroom_desks", "Newsroom desk lamps", "Pool newsroom desks in practical lamps under a dark ceiling, paper texture, monitor glow, the space a field of small gold islands.", ("interior",)),
        _gen("trench_flare_night", "Trench night flare", "Light a night trench with a falling flare, mud texture, faces going white then red, the ditch space a brief terrible stage.", ("war", "night")),
        _gen("lighthouse_storm", "Lighthouse storm", "Sweep a lighthouse beam through storm rain, wet stone texture, a gallery railing, the space a tower in a grinding sea.", ("storm", "coastal")),
        _gen("fishing_wheelhouse", "Fishing-boat wheelhouse", "Key a wheelhouse with instrument glow and gray sea windows, wet wool texture, condensation, the cabin space pitching.", ("marine",)),
        _gen("train_compartment", "Train-compartment window", "Mix compartment tungsten with traveling window daylight, upholstery texture, a table of paper, the space a moving room of blinds.", ("train",)),
        _gen("subway_car_fluoro", "Subway-car fluorescent", "Wash a subway car in sick fluorescent, ad-panel texture, poles and straps, the car space a tube of faces and smear windows.", ("urban",)),
        _gen("parking_sodium", "Parking-garage sodium", "Stain a parking garage in sodium orange, concrete texture, columns marching, the ramp space a spiral of ugly gold.", ("urban", "night")),
        _gen("fire_escape_night", "Fire-escape night", "Key a fire-escape two-shot with a kitchen window practical, rust texture, brick close, the city a drop beyond the rails.", ("urban", "night")),
        _gen("barn_loft_gold", "Barn loft gold shaft", "Drop a gold shaft through barn boards, hay texture, motes thick, the loft space a cathedral of dust and tack.", ("rural",)),
        _gen("ice_rink_overhead", "Ice-rink overhead", "Blast an ice rink with overhead sports keys, ice-scratch texture, breath vapor, the rink space a white rectangle in a dark bowl.", ("sports",)),
        _gen("haunted_flashlight", "Haunted-house flashlight", "Carve a decaying interior with a flashlight beam, peeling wallpaper texture, the beam a moving tunnel, the rest of the house withheld.", ("horror",)),
        _gen("crypt_torch", "Crypt torch", "Flicker torchlight on crypt stone, bone-niche texture, smoke staining the vault, the space a low rib of dark.", ("gothic",)),
        _gen("forge_dark_fantasy", "Dark-fantasy forge", "Key a forge with molten orange, soot and leather texture, hammer scale, the hall space a cave of heat and iron.", ("fantasy",)),
        _gen("throne_high_fantasy", "High-fantasy throne", "Shaft colored glass onto a throne hall, banner texture, stone flags, the space a long approach of light bars and hush.", ("fantasy",)),
        _gen("space_opera_bridge", "Space-opera bridge", "Key a command bridge with console glow and a giant window of stars, metal-grille texture, the space a dark theater facing cosmos.", ("scifi",)),
        _gen("rooftop_chase_sodium", "Rooftop-chase sodium", "Chase a rooftop in mixed sodium and billboard RGB, tar texture, HVAC obstacles, the skyline space a maze of drops.", ("action", "night")),
        _gen("tunnel_chase", "Car-chase tunnel", "Strobe a tunnel chase with passing fixtures, wet-tile texture, taillights as streaks, the tube space a rhythmic pulse.", ("action",)),
        _gen("embassy_night", "Embassy night", "Hold an embassy night exterior in security floods, limestone texture, flags limp, the grounds space empty and watched.", ("spy", "night")),
        _gen("safehouse_blinds", "Safehouse blinds", "Stripe a safehouse apartment with closed-blind sun, cheap carpet texture, a table of kit, the room space tense and ordinary.", ("spy",)),
        _gen("school_gym_bounce", "School-gym bounce", "Bounce gym-window sun off varnished wood, sneaker-scuff texture, bleachers empty, the court space echoing and large.", ("school", "sports")),
        _gen("ski_lodge_fire", "Ski-lodge fire", "Key a ski lodge with fireplace gold against window blue, wool and pine texture, snow outside, the room space a warm cave.", ("interior", "snow")),
        _gen("opera_footlights", "Opera footlights", "Throw footlights up into painted faces, velvet-curtain texture, the pit a dark gulf, the stage space a gold proscenium box.", ("theatrical",)),
        _gen("jazz_club_red", "Jazz-club red practical", "Bathe a jazz club in red practicals, brass and smoke texture, tiny tables, the bandstand space a glow in a cave.", ("club", "music")),
        _gen("poker_low_lamp", "Poker-room low lamp", "Drop a green-shade lamp on a felt table, card and chip texture, faces in the pool, the room beyond a dark suggestion.", ("interior",)),
        _gen("war_room_map", "War-room map light", "Key a war-room table with a map lamp, paper and ashtray texture, the walls a ring of officers, the space a bunker of plans.", ("war", "interior")),
        _gen("cockpit_glow", "Cockpit glow", "Key a night cockpit with instrument wash, leather-seat texture, rain on the windshield, the cabin space a tiny green cave.", ("vehicle", "night")),
        _gen("cargo_hold", "Cargo-hold practical", "Light a cargo hold with cage practicals, crate stencil texture, chain, the hold space a ribbed belly of a ship.", ("interior",)),
        _gen("stoop_golden", "Stoop golden hour", "Rake golden hour up a brownstone stoop, stoop-stone texture, a screen door, the street space neighborly and long-shadowed.", ("urban", "golden")),
        _gen("porch_moth_bulb", "Porch moth bulb", "Hang a bare porch bulb in humidity, moth texture in the glow, screen-door mesh, the yard space a black surround.", ("rural", "night")),
        _gen("orchard_raking", "Orchard raking sun", "Rake late sun down an orchard aisle, bark and fruit texture, dust as gold, the row space a repeating tunnel.", ("rural", "golden")),
        _gen("rodeo_hard_sun", "Rodeo hard sun", "Blast a rodeo arena with overhead sun, dirt-kick texture, chute wood, the oval space a bright dust bowl.", ("western", "sports")),
        _gen("samurai_courtyard", "Samurai courtyard raking", "Rake morning sun across a raked-gravel courtyard, wood-grain and paper-door texture, the space a rectangle of discipline and shadow.", ("period",)),
        _gen("wuxia_mist_ridge", "Wuxia mist ridge", "Veil a mountain ridge in wuxia mist, silk and pine texture, a bridge as a thread, the space floating and vertical.", ("wuxia", "mist")),
        _gen("dojo_sidelight", "Dojo sidelight", "Side-light a dojo so floorboards gleam, gi-cotton texture, a wall of weapons as geometry, the hall space spare and echoing.", ("martial",)),
        _gen("prison_yard_sun", "Prison-yard hard sun", "Blast a prison yard with overhead sun, concrete texture, chain-link shadow as a grid on faces, the yard space a pan of glare.", ("procedural",)),
        _gen("cell_slit_window", "Prison-cell slit window", "Key a cell from a high slit window, painted-steel texture, a toilet and bunk, the space a vertical box of falloff.", ("procedural", "interior")),
        _gen("regency_chandelier", "Regency ballroom chandelier", "Drop chandelier diamonds over a ballroom, silk and marble texture, candle-equivalents in glass, the floor space a mirror of movement.", ("period",)),
        _gen("ballet_ghost_light", "Ballet rehearsal ghost light", "Hold a rehearsal hall with a single ghost light on scuffed marley, chalk texture, the studio space empty and honest.", ("theatrical",)),
        _gen("casino_overhead", "Casino overhead wash", "Wash a casino floor in even overheads, carpet-pattern texture, no clocks, the space a maze of tables and glow.", ("interior",)),
        _gen("morgue_cold", "Morgue cold green", "Tint a morgue in cold green practicals, steel-drawer texture, tile shine, the room space refrigerated and still.", ("hospital",)),
        _gen("hydroponic_ship", "Colony-ship hydroponic", "Key a hydroponic bay with grow-LED magenta-green, leaf and pipe texture, the bay space a garden in a hull.", ("scifi",)),
        _gen("android_lab", "Android-lab clean", "Even an android lab in clean bounce, polymer-skin texture, tools on trays, the space white and watchful.", ("scifi", "lab")),
        _gen("billboard_apt", "Billboard-lit apartment", "Flood an apartment with billboard RGB through cheap blinds, laminate texture, the room space stained by advertising color.", ("urban", "night")),
        _gen("grain_elevator_noon", "Grain-elevator noon", "Bake a grain elevator in noon sun, corrugated texture, a two-lane, the prairie space empty except for that tower.", ("rural", "western")),
        _gen("swamp_night", "Swamp night methane", "Key a swamp night with a lantern and bioluminescent suggestion, moss texture, black water, the space a maze of knees and mist.", ("swamp", "night")),
        _gen("beach_landing_overcast", "Beach-landing overcast", "Hold a landing beach under military overcast, wet sand texture, obstacles as silhouettes, the space a gray sheet into surf.", ("war",)),
        _gen("sniper_nest_dusk", "Sniper-nest dusk", "Compress a dusk city from a nest, brick texture in the foreground, a distant figure small, the space a measured gap of air.", ("war", "thriller")),
        _gen("piano_bar_gold", "Piano-bar gold", "Warm a piano bar with gold practicals, lacquer and ivory texture, bottles as stained glass, the nook space intimate.", ("club", "music")),
        _gen("meadow_magic_rural", "Meadow magic-hour rural", "Gild a meadow at magic hour, grass-seed texture, a farmhouse small, the space a bowl of honey air and long shade.", ("rural", "golden")),
        _gen("kitchen_table_drama", "Kitchen-table family drama", "Key a kitchen table with a hanging practical, oilcloth texture, dishes, the room space close enough to hear breath.", ("drama",)),
        _gen("campaign_office_night", "Campaign-office night", "Keep a campaign office alive at night with desk lamps, paper-stack texture, maps, the space a warren of tired fluorescents off.", ("interior", "night")),
        _gen("elevator_tungsten", "Elevator tungsten", "Box two people in elevator tungsten, brushed-metal texture, a floor-number glow, the space a moving closet of reflections.", ("interior",)),
        _gen("airplane_cabin_night", "Airplane cabin night", "Wash a night cabin in reading-spot coins, seat-fabric texture, oval windows of black, the aisle space a long dim tube.", ("vehicle", "night")),
        _gen("circus_tent_color", "Circus tent colored", "Throw colored tent-wash on sawdust, sequin and animal-implied texture, bleachers, the ring space a bright dirt circle.", ("carnival",)),
        _gen("pulp_paperback_sat", "Pulp paperback saturation", "Push pulp saturation on a night diner or alley, cheap-print texture, a figure in a loud coat, the space a cover illustration made flesh.", ("pulp", "noir")),
        _gen("grindhouse_grain", "Grindhouse night grain", "Grind a night street with coarse grain and sick practicals, sticky-floor implied texture, a marquee, the space cheap and dangerous.", ("grindhouse",)),
        _gen("italian_western_cemetery", "Cemetery-western noon", "Blast a cemetery western in white noon, bleached-wood texture, a boot and a stone, the space a dusty amphitheater of graves.", ("western",)),
        _gen("locker_tungsten", "Sports-locker tungsten", "Key a locker room in tungsten cages, tile and tape texture, steam, the space a wet rectangle of benches.", ("sports", "interior")),
        _gen("detective_blinds_desk", "Detective blinds desk", "Stripe a desk with failing blinds, coffee-ring texture, a fan, the office space smaller than the noir version, more tired.", ("noir", "procedural")),
        _gen("precinct_fluorescent", "Police-precinct fluorescent", "Wash a precinct bullpen in mixed fluorescent, metal-desk texture, wanted-board, the space a noisy grid of tired light.", ("procedural",)),
        _gen("church_candle_gothic", "Church-candle gothic", "Multiply votive candles at an altar, wax-drip texture, gold leaf, the chapel space a cave of small fires.", ("gothic", "sacred")),
        _gen("monastery_cloister", "Monastery cloister", "Side-light a cloister walk with open-arcade sun, stone-wear texture, a garden square, the space a measured circuit of shade.", ("sacred", "period")),
        _gen("summer_camp_dusk", "Summer-camp woods dusk", "Hold dusk in woods around a cabin, pine-needle texture, a bug-zapper glow, the camp space between play and threat.", ("teen", "folk")),
        _gen("fairground_night", "Fairground night tungsten", "String a fairground night with bare bulbs, painted-steel texture, fried-air implied, the midway space a funnel of faces.", ("carnival", "night")),
        _gen("news_chopper_search", "Searchlight night ground", "Stab a searchlight onto a night street from above, wet-asphalt texture, figures as insects, the space a cone of exposure.", ("thriller", "night")),
        _gen("embassy_ballroom", "Embassy ballroom mixed", "Mix chandelier and window dusk in an embassy ballroom, silk texture, flags, the floor space diplomatic and watchful.", ("spy", "period")),
        _gen("radio_bunker_amber", "Radio-bunker amber", "Amber a radio bunker with bakelite glow, grill-cloth texture, maps, the room space a humming closet of war.", ("war", "interior")),
        _gen("hydro_dam_noon", "Dam noon sublime", "Hold a dam face in noon sun, concrete-scale texture, a tiny figure, the space industrial sublime.", ("scale", "industrial")),
        _gen("nursery_window_day", "Nursery window day", "Diffuse a nursery with sheer-curtain day, cotton texture, a mobile, the room space pale and quiet.", ("interior", "drama")),
        _gen("attic_storm_day", "Attic storm day", "Key an attic from a round window under storm, dust-cloth texture, trunks, the space a memory box of gray-green.", ("interior", "storm")),
        _gen("boardwalk_night", "Boardwalk night sodium", "Mix sodium and ride-color on a boardwalk night, salt-wood texture, a crowd, the pier space a strip into dark water.", ("coastal", "night")),
        _gen("observatory_dome", "Observatory dome night", "Key an observatory interior with console glow and a slit of stars, metal-track texture, the dome space a machine aimed at dark.", ("scifi", "night")),
        _gen("greenhouse_overcast", "Greenhouse overcast", "Fill a greenhouse with overcast bounce, wet-leaf texture, condensation, the nave of glass space humid and even.", ("interior", "overcast")),
        _gen("subway_platform_sodium", "Subway platform sodium", "Stain a subway platform in sodium and tube-wind, tile-ad texture, a yellow edge, the platform space a tunnel of wait.", ("urban",)),
        _gen("rooftop_billboard_rgb", "Rooftop billboard RGB", "Paint a rooftop figure with billboard RGB, tar texture, the sign as a monster key, the city space a drop of black.", ("urban", "night")),
        _gen("farmhouse_kitchen_am", "Farmhouse kitchen morning", "Rake morning through a farmhouse kitchen, enamel and grain-wood texture, steam from a kettle, the room space used and kind.", ("rural", "drama")),
        _gen("cathedral_crypt_blue", "Cathedral crypt blue", "Wash a crypt in cold window-blue, stone-effigy texture, the vault space a hush under the city.", ("gothic", "sacred")),
        _gen("factory_night_shift", "Factory night-shift", "Key a factory night-shift with mercury-vapor greens, machine-oil texture, the floor space a forest of presses.", ("industrial", "night")),
        _gen("motel_bathroom_fluoro", "Motel bathroom fluorescent", "Blast a motel bathroom in harsh fluorescent, mildew-tile texture, a mirror, the box space unflattering and true.", ("interior",)),
        _gen("wedding_bounce_day", "Wedding day bounce", "Bounce day off a pale wall onto formal clothes, flower texture, a hall, the space ceremonial and kind.", ("romance",)),
        _gen("funeral_overcast", "Funeral overcast", "Hold a graveside under overcast, wool-black texture, umbrellas, the cemetery space a gray bowl.", ("drama", "overcast")),
        _gen("high_school_hallway", "High-school hallway lockers", "Stripe a school hallway with locker rows in mixed fluorescent, enamel-dent texture, the corridor space a social tunnel.", ("school",)),
        _gen("pool_hall_over", "Pool-hall overhead", "Drop shaded lamps over green felt, chalk texture, smoke, the hall space a row of bright tables in dark wood.", ("interior", "club")),
        _gen("aquarium_blue", "Aquarium-blue interior", "Key an interior with aquarium-blue practicals, glass and water texture, moving caustics, the room space submarine without a hull.", ("interior", "scifi")),
        _gen("desert_night_stars", "Desert-night camp stars", "Key a desert camp with fire gold against star-true black, sand texture, a two-lane far, the space huge and cold above the flame.", ("western", "night")),
        _gen("rain_bus_interior", "Rain-bus interior", "Mix bus fluorescent with rain-window smear, plastic-seat texture, ads, the aisle space a wet public room.", ("urban", "wet")),
        _gen("office_cubicle_day", "Office cubicle daylight", "Even an open office in daylight fluorescents, fabric-panel texture, monitors, the floor space a maze of beige.", ("interior",)),
        _gen("church_basement_coffee", "Church-basement coffee", "Light a church basement with cheap fluorescents, folding-table texture, coffee, the room space humble and tiled.", ("interior", "realist")),
        _gen("rooftop_dawn_city", "Rooftop dawn city", "Hold a rooftop at city dawn, tar-and-vent texture, the skyline going pink, the space a private deck over a waking grid.", ("urban", "dawn")),
        _gen("mine_headlamp", "Mine headlamp tunnel", "Carve a mine tunnel with a headlamp, coal-glitter texture, timber props, the space a throat of dark.", ("industrial",)),
        _gen("ferry_night_deck", "Ferry night deck", "Key a ferry deck with work-lamps and city approaching, wet-paint texture, a railing, the space a windy platform on black water.", ("marine", "night")),
        _gen("stadium_night_flood", "Stadium night floods", "Blast a stadium night with floods, grass texture, the bowl of crowd as a glittering cliff, the pitch space a green table.", ("sports", "night")),
        _gen("convent_cell_day", "Convent-cell day", "Side-light a convent cell from a small window, plaster texture, a bed and a book, the space a measured poverty of sun.", ("sacred", "period")),
        _gen("arcade_neon_night", "Arcade neon night", "Fill an arcade with cabinet RGB, carpet-pattern texture, the hall space a cave of moving color and no daylight.", ("club", "night")),
        _gen("courtyard_moon", "Moonlit courtyard", "Paint a courtyard in moonlight and one window, flagstone texture, a well, the space a silver well of hush.", ("gothic", "night")),
        _gen("warehouse_rave_strobe", "Warehouse rave strobe", "Strobe a warehouse rave in fog, concrete texture, a truss of diodes, the volume space a pulsing industrial nave.", ("club",)),
        _gen("farm_silo_magic", "Farm silo magic hour", "Gild a silo and a gravel drive at magic hour, rust texture, a pickup, the farm space a hush of gold dust.", ("rural", "golden")),
        _gen("bridge_fog_noir", "Bridge fog noir", "Lose a figure on a fogged bridge in sodium, wet-rail texture, the span space disappearing in both directions.", ("noir", "fog")),
        _gen("attic_fairy_gold", "Attic gold slats", "Stripe an attic with gold slat-sun, trunk-leather texture, motes, the space a memory of summer stored.", ("interior", "golden")),
        _gen("dock_night_worklamp", "Dock night work-lamp", "Key a night dock with a work-lamp, wet-wood texture, ropes, the slip space a stage over black harbor.", ("marine", "night")),
        _gen("green_screen_cyc_empty", "Empty cyc studio", "Even an empty cyclorama in studio bounce, paint-seam texture, no set, the space a horizon of nothing waiting.", ("studio",)),
        _gen("horror_basement_bulb", "Horror basement bulb", "Hang a swinging bulb in a basement, dirt-floor texture, joists, the space a low threat of moving gold and black.", ("horror",)),
        _gen("romance_rain_window", "Romance rain window", "Key two faces with rain-window bounce, knit texture, a cafe table, the glass space a curtain of weather between them and the street.", ("romance", "wet")),
        _gen("western_campfire_faces", "Western campfire faces", "Key western faces from a campfire below, leather texture, horses as shadows, the desert space a ring of dark.", ("western", "night")),
        _gen("spy_hotel_corridor", "Spy hotel corridor", "Hold a hotel corridor in even practicals, patterned-carpet texture, a cart, the space a long measured threat of doors.", ("spy",)),
        _gen("doc_kitchen_window", "Documentary kitchen window", "Use only the kitchen window, dish-rack texture, a kettle, the room space ordinary and unstyled.", ("doc", "realist")),
        _gen("action_heli_search", "Helicopter-searchlight night", "Stab a helicopter searchlight onto a yard, grass texture going white, fences, the space a moving cone of exposure.", ("action", "night")),
        _gen("prestige_rain_estate", "Prestige rain estate", "Grade a rain-soaked estate in shallow complementary, wet-gravel texture, a facade, the drive space expensive and miserable.", ("prestige", "wet")),
        _gen("folk_barn_interior", "Folk-horror barn interior", "Stripe a barn interior with broken-board sun, straw texture, a figure in the aisle, the space a nave of dust and wrong quiet.", ("folk", "horror")),
        _gen("cyber_interior_rgb", "Cyber interior RGB ribs", "Key an interior with RGB ribs and rain-window neon, polymer texture, the room space a wet cockpit of city color.", ("cyber",)),
        _gen("solar_market_day", "Solarpunk market day", "Wash a market street in clear sun, produce and solar-shade texture, water channels, the space civic and green.", ("solar",)),
        _gen("snow_train_window", "Snow-bound train window", "Mix compartment tungsten with blizzard-white windows, frost texture, tea glass, the space a warm tube in a white war.", ("snow", "train")),
        _gen("jungle_night_bugs", "Jungle night bugs", "Key a jungle night camp with a lantern, leaf-wet texture, a wall of insect glow, the clearing space a small hole in black green.", ("jungle", "night")),
        _gen("arctic_hut_window", "Arctic hut window", "Hold an arctic hut interior against a white window, wool texture, ice on the pane, the room space a yellow box in forever.", ("arctic", "interior")),
        _gen("noir_rooftop_water", "Noir rooftop water tower", "Key a noir rooftop with a water-tower silhouette and a distant neon, tar texture, the city space a map of threats below.", ("noir", "night")),
        _gen("melodrama_stair", "Melodrama staircase", "Place a figure on a curving stair in window drama, runner-carpet texture, a chandelier, the hall space a vertical emotion.", ("drama",)),
        _gen("heist_vault_fluoro", "Heist vault fluorescent", "Wash a vault in cold fluorescent, steel-wheel texture, the room space a round door and a table of work.", ("heist",)),
        _gen("musical_rehearsal_day", "Musical rehearsal daylight", "Flood a rehearsal loft with day, marley texture, a piano, the space work-light honest with leftover sequin.", ("musical",)),
        _gen("bodycam_night_street", "Body-cam night street", "Ride a chest-cam on a night street, sodium smear, uniform fabric, wet asphalt, the space always too close and too wide.", ("procedural", "pov")),
        _gen("found_car_dash", "Found-footage dash night", "Shake a dash view at night, wiper texture, rain, a face at the edge, the cabin space a panic of glass and road.", ("found", "horror")),
        _gen("romcom_golden_stoop", "Rom-com golden stoop", "Bounce golden hour off a stoop onto two faces, brownstone texture, groceries, the street space cheerful and close.", ("comedy", "romance", "golden")),
        _gen("thriller_ferry_long", "Thriller ferry long-lens", "Compress a ferry deck on a long lens, paint texture, a subject isolated in tourists, the water space a moving trap.", ("thriller",)),
        _gen("war_tent_surgical", "War tent surgical", "Key a field-hospital tent with harsh practicals, canvas texture, steel, the space a hurried nave of white and mud.", ("war", "hospital")),
        _gen("sub_sonar_blue", "Submarine sonar blue", "Wash a sonar nook in blue-green CRTs, metal texture, the space a dark ear of the boat.", ("war", "scifi")),
        _gen("space_airlock", "Spacecraft airlock practical", "Key an airlock with strip practicals, warning-stencil texture, a round door, the space a closet between atmospheres.", ("scifi",)),
        _gen("fashion_daylight_cyc", "Fashion daylight cyc", "Even a fashion figure on a daylight cyc, fabric-micro texture, no prop, the space a horizon of pale nothing.", ("fashion",)),
        _gen("music_video_fog_rim", "Music-video fog rim", "Rim a performer in fog with a colored backlight, sequin texture, the stage space a silhouette factory.", ("music",)),
        _gen("commercial_kitchen_wrap", "Commercial kitchen wrap", "Wrap food in a kitchen-studio bounce, steam texture, stainless, the pass space appetizing and controlled.", ("commercial",)),
        _gen("verite_car_night", "Verite car night", "Bounce dashboard glow onto a talking driver, vinyl texture, passing sodium, the cabin space a confession booth on wheels.", ("verite", "night")),
        _gen("observational_shop", "Observational shop lockoff", "Lock off on a shop counter in mixed available, laminate texture, hands and goods, the space a small theater of ordinary work.", ("doc", "locked")),
        _gen("giallo_hotel_night", "Giallo hotel night", "Gel a hotel corridor in yellow and teal, patterned-carpet texture, a gloved hand, the space a candy threat of doors.", ("giallo",)),
        _gen("caper_vault_night", "Caper night street cool", "Cool a night street for a caper team, wet-brick texture, a van, the space playful geometry of alleys.", ("caper",)),
        _gen("court_high_windows", "Courtroom high windows", "Drop high-window shafts onto a jury box, wood texture, dust, the room space civic and taller than the people.", ("procedural",)),
        _gen("hospital_or_overhead", "Hospital OR overhead", "Blast an OR with overhead surgical keys, drape texture, chrome, the table space a white island of concentration.", ("hospital",)),
        _gen("school_blackboard_day", "School blackboard day", "Side-light a blackboard classroom with window day, chalk texture, desks, the room space ordinary and dusty-gold.", ("school",)),
        _gen("beach_magic_couple", "Beach magic-hour couple", "Gild two figures on a beach at magic hour, salt-skin texture, the ocean a sheet, the space romantic and windy.", ("beach", "romance", "golden")),
        _gen("club_uv_fog", "Night-club UV fog", "Expose a club in ultraviolet so whites scream, fog texture, teeth and shirts, the space a black light cave between strobes.", ("club",)),
        _gen("western_porch_magic", "Western porch magic hour", "Gild a western porch at magic hour, rocking-chair texture, a street of false fronts, the space honey and dust.", ("western", "golden")),
        _gen("snow_church_isolation", "Snow church isolation", "Hold a church as a dark rectangle in a snow field, clapboard texture, one window gold, the space a hymn of isolation.", ("snow", "sacred")),
        _gen("jungle_river_dapple", "Jungle river dapple", "Dapple a jungle river with broken sun, wet-log texture, the water a black mirror, the space a tunnel of green and current.", ("jungle",)),
        _gen("arctic_pack_ice_scale", "Arctic pack-ice scale", "Dwarf a figure on pack ice under a huge overcast, ice-blue texture, the space a broken white floor into fog.", ("arctic", "scale")),
        _gen("interrogation_two_bulb", "Two-bulb interrogation", "Hang two competing bulbs over a table, sweat texture, a metal chair, the box space a geometry of double shadows.", ("noir",)),
        _gen("superhero_alley_rim", "Superhero alley rim", "Rim a figure in an alley with a graphic colored kicker, brick texture, a dumpster, the space a comic panel of urban night.", ("superhero",)),
        _gen("action_market_haze", "Action market sun-haze", "Backlight a market chase in sun-haze, stall-cloth texture, spice-dust, the aisle space a tunnel of people and glare.", ("action",)),
        _gen("prestige_library_night", "Prestige library night", "Grade a library night in shallow complementary, leather texture, a lamp, the stacks space intellectual and lonely.", ("prestige",)),
        _gen("kitchen_sink_bathroom", "Kitchen-sink bathroom", "Hold a bathroom in overcast window, peeling-paint texture, laundry, the box space true and unkind.", ("realist",)),
        _gen("social_realist_bus", "Social-realist bus interior", "Use available bus light, coat texture, ads, the aisle space unstyled public life.", ("realist", "doc")),
        _gen("period_hearth_day", "Period hearth and daylight", "Mix hearth gold with a small window in a period cottage, wool texture, plaster, the room space a fight of two centuries of fire and day.", ("period",)),
        _gen("romcom_bookstore", "Rom-com bookstore bounce", "Bounce window day through a bookstore onto two faces, paper texture, aisles, the space warm and close with spines.", ("comedy", "romance")),
        _gen("heist_server_blue", "Heist server-room blue", "Wash a server room in cold blue, grille texture, the aisle space a humming chapel of theft.", ("heist", "scifi")),
        _gen("found_woods_night", "Found-footage woods night", "Shake woods at night with on-camera LED, leaf-wet texture, trunks jumping, the path space a panic of green-black.", ("found", "horror")),
        _gen("bodycam_stairwell", "Body-cam stairwell", "Climb a stairwell as a chest-cam, paint-chip texture, rails, fluorescent smear, the well space a vertical chase.", ("procedural", "pov")),
        _gen("slasher_wood_practical", "Slasher woods practical", "Underexpose woods so a cabin window is the only key, leaf texture, the dark as mass, the yard space a threat of withheld detail.", ("horror",)),
        _gen("gothic_ruin_moon", "Gothic ruin moonlight", "Paint a ruin in moonlight, ivy-stone texture, a broken rose window, the nave space open to weather.", ("gothic",)),
        _gen("melodrama_rain_street", "Melodrama rain street", "Key a figure in street rain from a shop window, wool texture, the pavement space a river of feeling.", ("drama", "wet")),
        _gen("screwball_newsroom", "Screwball newsroom high-key", "Flood a newsroom in high-key bounce, paper texture, overlapping bodies, the floor space comic and loud with sun.", ("comedy",)),
        _gen("western_river_noon", "Western river noon", "Bake a river crossing at noon, water-glitter texture, horses, the ford space a sheet of glare and dust.", ("western",)),
        _gen("neo_noir_apartment", "Neo-noir apartment blinds", "Stripe a night apartment with neon through blinds, cheap-wood texture, a glass, the room space a wet city entering private air.", ("noir", "night")),
        _gen("noir_diner_counter", "Noir diner counter", "Key a diner counter with a long fluorescent, laminate texture, a lonely stool, the space a bright strip in a dark street.", ("noir",)),
    ]
    return rows


def viral_looks() -> list[dict[str, Any]]:
    rows = [
        _vir("snap_push_hold", "Vertical snap-push hold", "Snap-push in on a vertical axis then hold the face for one second, upper third occupied, empty caption air below.", "Frozen at the end of a vertical snap-push, face held in the upper third, empty caption air in the lower frame.", ("hook",)),
        _vir("talking_mcu", "Face-to-camera talking MCU", "Hold a talking MCU square to lens, eyes to camera, a lived room behind, mouth and micro-expressions as the only action.", "Frozen mid-sentence in a talking MCU, eyes to camera, a lived room behind.", ("talking",), "Room tone and close speech."),
        _vir("walk_talk_gimbal", "Walking-and-talking gimbal", "Gimbal-walk beside a talking figure down a sidewalk, horizon true, shopfronts traveling, face staying readable.", "Frozen mid-stride in a sidewalk walk-and-talk, shopfronts as a traveling smear behind a sharp face.", ("talking", "walk")),
        _vir("breakfast_hands", "Breakfast hands day-in-life", "Fill the frame with breakfast hands: kettle, toast, a phone face-down, morning window, no head yet.", "Frozen on breakfast hands at a kettle and toast, morning window, phone face-down.", ("hands", "food"), "Kettle click and toast scrape."),
        _vir("mirror_ready_glass", "Mirror-ready lit glass", "Hold a mirror-ready close at a lit bathroom glass, face and hands doing hair or skin, the reflection as the true subject.", "Frozen at a lit bathroom glass, hands in hair, the reflection owning the frame.", ("beauty",), "Tap drip and a brush."),
        _vir("pov_chore_hands", "POV chore hands", "Shoot POV chore hands wiping a counter or folding cloth, the body implied, the task as the hook.", "Frozen POV on chore hands mid-wipe, counter grain, no face.", ("pov", "hands"), "Cloth on laminate."),
        _vir("macro_pour", "Satisfying macro pour", "Macro-pour a viscous liquid into a glass so the ribbon and bubbles are landscape, labels unmarked.", "Frozen mid-pour, a viscous ribbon hitting a glass, bubbles as landscape.", ("food", "macro"), "Viscous pour and glass ring."),
        _vir("product_orbit", "Orbit product", "Orbit a tabletop product at display speed, highlights walking around the object, seamless or lived backdrop.", "Frozen mid-orbit on a tabletop product, a highlight parked on the leading edge.", ("product",)),
        _vir("crash_zoom_react", "Crash-zoom reaction", "Crash-zoom into a reaction face from a medium, then hold the surprise, background compressing.", "Frozen at the end of a crash-zoom on a reaction face, background compressed.", ("hook", "reaction")),
        _vir("outfit_match_cut", "Outfit match-cut", "Match-cut an outfit change on a held pose, same mark, clothes swapping as if the body were a mannequin.", "Frozen on the after-outfit at the same mark and pose as the implied before.", ("fashion", "edit")),
        _vir("location_jump_cut", "Location jump match", "Match-cut a walking figure from one location into another on the same stride, clothes continuous, world swapped.", "Frozen on the landing stride in the second location, same clothes, new world.", ("edit", "walk")),
        _vir("cyclorama_studio", "Cyclorama studio", "Plant a figure on a seamless cyclorama, even studio bounce, no set dressing, product or body as the only object.", "Frozen on a seamless cyclorama, figure or product isolated on a horizon of nothing.", ("studio",)),
        _vir("caption_safe_916", "Caption-safe 9:16 headroom", "Compose 9:16 with the face in the upper third and the lower half empty of important features so caption air stays clean.", "Frozen 9:16 with face in the upper third and a clean empty lower half for caption air.", ("safe",), "", "vir_lower_third_empty"),
        _vir("lower_third_empty", "Lower-third-safe empty", "Keep the lower third of a vertical frame empty of hands, logos, and faces so a lower-third can sit later.", "Frozen vertical with a clean empty lower third, subject parked in the upper two-thirds.", ("safe",), "", "vir_caption_safe_916"),
        _vir("before_after_wipe", "Before/after wipe", "Wipe a before/after across a held composition, same mark, the world or face changing along a traveling edge.", "Frozen mid-wipe, half before and half after on the same mark.", ("edit",)),
        _vir("silent_hook_hold", "Silent-hook hold then move", "Hold a silent hook still for one second then begin motion, the first beat a picture not a pan.", "Frozen on the silent one-second hook before motion starts, a complete picture.", ("hook",)),
        _vir("subway_pole_close", "Subway-pole close", "Hold a subway-pole close, face and a hand on steel, fluorescent smear, other riders as bokeh, 9:16 center axis.", "Frozen on a subway pole, face and a gripping hand, fluorescent smear, riders as bokeh.", ("transit",), "Car rumble and pole squeak."),
        _vir("dash_talking", "Dash talking", "Mount on a dash looking aft at a talking driver, road smearing in the windows, city as traveling bokeh.", "Frozen on a dash-mounted talking driver, road smear in the side glass.", ("vehicle", "talking"), "Cabin road roar."),
        _vir("golden_boom_stick", "Golden-hour boom stick", "Boom an arm's-length stick at golden hour so face and sky share the vertical, wind in hair, the sun as a rim.", "Frozen on an arm's-length golden-hour boom, face and sky sharing the vertical, sun as a rim.", ("golden", "talking"), "Wind in hair and distant surf or traffic."),
        _vir("drone_hero_slowmo", "Drone-hero reveal slow-mo", "Reveal a figure from a drone rise then drop into slow-mo on the face, landscape arriving then time thickening.", "Frozen at the drone-reveal crest, figure small in landscape before the slow-mo drop.", ("drone", "hook")),
        _vir("fpv_dive_mark", "FPV dive to subject", "Dive as an FPV flyer toward a waiting figure, ground rushing, the last meters aimed at a chest mark.", "Frozen in an FPV dive, ground rushing, a waiting figure filling the center.", ("drone", "energy"), "Wind scream implied."),
        _vir("street_interview", "Street-interview two-shot", "Hold a street-interview two-shot, interviewer shoulder dirty, subject face-lit by bounce, sidewalk traffic wiping.", "Frozen on a street-interview two-shot, dirty interviewer shoulder, subject face-lit, traffic as smear.", ("talking", "street"), "Sidewalk chatter and a bus hiss."),
        _vir("confessional_mcu", "Confessional MCU", "Hold a confessional MCU against a simple wall, eyes to camera, a practical lamp, the talk as a private leak.", "Frozen in a confessional MCU against a simple wall, eyes to camera, a practical lamp.", ("talking",), "Close speech and room hush."),
        _vir("storytime_close", "Storytime close", "Push a storytime close so the mouth and eyes fill the vertical, a lived pillow or car-seat behind, hands occasionally entering.", "Frozen in a storytime close, mouth and eyes filling the vertical, a pillow behind.", ("talking",)),
        _vir("macro_texture_whisper", "Macro texture whisper", "Macro a satisfying texture: fabric nap, ice crystals, frosting, the sound implied by the surface, no face required.", "Frozen on a macro texture of fabric nap or frosting, no face, the surface as landscape.", ("macro", "asmr"), "Close texture ticks and a hush."),
        _vir("cook_overhead", "Cooking overhead", "Lock overhead on a board: knife, herbs, a pan entering, hands as the dancers, 9:16 or a cropped square in the vertical.", "Frozen overhead on a board, knife and herbs, hands mid-prep.", ("food",), "Knife on board and a pan tick."),
        _vir("recipe_inserts", "Recipe insert cascade", "Cascade recipe inserts: pour, sizzle, plate, each a clean insert on black or marble, no talking head.", "Frozen on one insert of the cascade, a plated bite on marble, steam still.", ("food",), "Sizzle and a plate clink."),
        _vir("gym_handheld", "Gym-effort handheld", "Handheld a gym effort, breath and iron, a mirror sometimes, the face effort-ugly, the space a rack of plates.", "Frozen mid-rep in a handheld gym effort, iron and breath, effort on the face.", ("gym",), "Iron plates and hard breath."),
        _vir("sunset_talk", "Sunset talk", "Talk to camera at sunset, sun as a disk or rim, wind, a railing, the sky doing half the work.", "Frozen in a sunset talk to camera, sun as a rim, a railing, wind in hair.", ("talking", "golden"), "Wind and distant traffic."),
        _vir("rain_walk", "Rain-walk", "Walk a rain street toward camera or with, hood beading, neon smear, steps splashing, the weather as co-star.", "Frozen mid-stride in a rain-walk, hood beading, neon smear, a splash hanging.", ("walk", "weather"), "Rain on a hood and wet steps."),
        _vir("night_bokeh_walk", "Night-city bokeh walk", "Walk a night city so shop-lights become bokeh balls, face sharp, the sidewalk a river of color.", "Frozen in a night-city bokeh walk, face sharp, shop-lights as balls.", ("walk", "night"), "City hush and heel ticks."),
        _vir("halfsec_change", "First-half-second change", "Change the picture in the first half-second: a smash of color, a door, a face, then settle, the hook before thought.", "Frozen on the post-change picture after a half-second smash, the new world already there.", ("hook",)),
        _vir("split_screen_vert", "Vertical split-screen", "Split the vertical into two stacked or side rooms, same person or a pair, actions answering each other.", "Frozen as a vertical split-screen, two rooms stacked or side by side, actions mid-answer.", ("edit",), "", "vir_stacked_two_shot"),
        _vir("gyro_skate_low", "Gyro skate low POV", "Ride a low gyro POV on a skate or board, asphalt grain, trucks, the city rushing at cheek height.", "Frozen at cheek height on a low skate POV, asphalt grain, trucks, city rushing.", ("pov", "energy"), "Wheels on tar."),
        _vir("float_car_mount", "Floating vehicle mount", "Float a vehicle mount with no operator body, the car as a moving island, city sliding, the subject talking or silent.", "Frozen on a floating vehicle mount, no operator body, city sliding past a talking or silent rider.", ("vehicle",)),
        _vir("hyperlapse_block", "Hyperlapse city block", "Hyperlapse a city block, lockoffs stepping forward, clouds and crowds streaking, architecture still between jumps.", "Frozen on one hyperlapse plate of a city block, crowds as ghosts, architecture sharp.", ("time", "city")),
        _vir("ccd_soft_digital", "Vintage small-sensor softness", "Render a vintage small-sensor digital still: slight bloom, weak microcontrast, pastel channel shift, a snapshot kitchen, no logo.", "Frozen as a vintage small-sensor digital still, bloomed highlights, pastel shift, a snapshot kitchen.", ("look", "still-look")),
        _vir("mist_halation_phone", "Phone mist-filter halation", "Bloom phone highlights through a misted optic, street lamps halating, skin glowing, a night sidewalk, no brand on the device.", "Frozen on a night sidewalk through a misted phone optic, lamps halating, skin glowing.", ("look", "night")),
        _vir("imperfect_handheld", "Imperfect-by-design handheld", "Keep imperfect handheld by design: micro-sway, a thumb in the edge, living timing, not a stabilizer commercial.", "Frozen mid-sway in imperfect handheld, a thumb in the edge, living timing.", ("handheld",)),
        _vir("center_axis_vert", "Center-axis vertical", "Plant the subject on the vertical center axis with depth behind, not a side third, the 9:16 as a tunnel.", "Frozen on a center-axis vertical, subject on the spine of the frame, depth as a tunnel behind.", ("comp",), "", "vir_depth_center_axis"),
        _vir("z_dolly_hook", "Z-axis dolly-in hook", "Dolly in on the Z-axis as the hook, face growing, background breathing, a three-second punch into eyes.", "Frozen mid Z-axis dolly-in, face growing, background breathing.", ("hook", "move")),
        _vir("three_sec_still", "Three-second hook then stillness", "Spend three seconds on a hook move then land in stillness, the hold as the talk beat.", "Frozen on the landed stillness after a three-second hook move, talk-ready.", ("hook",)),
        _vir("depth_center_axis", "Vertical dynamics with depth", "Build vertical dynamics: subject on center axis with a deep hallway or street behind, not a flat wall, motion in Z.", "Frozen on a center-axis figure with a deep hallway or street behind, Z-space readable.", ("comp",), "", "vir_center_axis_vert"),
        _vir("reaction_jump", "Reaction-cut jump", "Jump-cut to a reaction: a face replacing a thing, eyeline to camera or off, the cut as the joke.", "Frozen on the reaction face after a jump, eyeline to camera or off.", ("edit", "reaction")),
        _vir("top_bumper_empty", "Text-safe top bumper empty", "Leave the top bumper of the vertical empty of important face so a text bumper can sit, subject slightly low-center.", "Frozen with a clean empty top bumper, subject slightly low-center, face clear of the hat.", ("safe",)),
        _vir("stacked_two_shot", "Stacked two-shot", "Stack two talking heads in a vertical two-shot, one above the other, a shared beat, no platform chrome, a simple split.", "Frozen as a stacked two-shot, one talking head above the other, a shared beat, no platform chrome.", ("talking", "edit"), "", "vir_split_screen_vert"),
        _vir("grocery_pov", "POV grocery walk", "Walk a grocery POV, cart edge, fluorescent aisles, a hand grabbing unmarked goods, the store as a tunnel.", "Frozen POV in a grocery aisle, cart edge, a hand on unmarked goods.", ("pov", "walk"), "Cart squeak and aisle hush."),
        _vir("unbox_inserts", "Unbox insert cascade", "Cascade unbox inserts: tape peel, foam pull, object reveal, each a clean close, no talking.", "Frozen on a foam-pull insert, the object half-revealed in packing.", ("product", "hands"), "Tape peel and foam rub."),
        _vir("desk_overhead", "Desk-setup overhead", "Lock overhead on a desk setup: keyboard, a plant, a mug, hands arranging, the rectangle as a dollhouse.", "Frozen overhead on a desk, keyboard and mug, hands mid-arrange.", ("desk",), "Keycaps and a mug set-down."),
        _vir("night_drive_bokeh", "Night-drive bokeh", "Ride a night drive with windshield bokeh, dash glow on a face, wipers optional, the city as melted coins.", "Frozen on a night-drive face, dash glow, windshield bokeh as melted coins.", ("vehicle", "night"), "Cabin road roar and a blinker."),
        _vir("rooftop_golden_talk", "Rooftop golden talk", "Talk on a rooftop at golden hour, vents and a skyline, wind, face to camera, the city as a terrace.", "Frozen in a rooftop golden-hour talk, vents, skyline, face to camera.", ("talking", "golden"), "Wind and a distant horn."),
        _vir("whisper_mouth", "Whisper-close mouth", "Fill the vertical with a whisper-close mouth and a cheek, breath visible, the rest of the face cropped, ASMR-adjacent without a brand.", "Frozen on a whisper-close mouth and cheek, breath, the rest of the face cropped.", ("close", "asmr"), "Close breath and a whisper."),
        _vir("eyebrow_hold", "Eyebrow-raise hold", "Hold an eyebrow-raise to camera for a beat before speech, MCU, a lived wall, the face as a title card.", "Frozen on an eyebrow-raise to camera, MCU, a lived wall, pre-speech.", ("hook", "talking")),
        _vir("point_lens", "Point-at-lens", "Point at the lens as a hook, finger large, face behind, then drop the hand into talk.", "Frozen with a finger pointed at the lens, face behind, hook beat.", ("hook",)),
        _vir("outfit_spin", "Outfit spin", "Spin a full outfit on a center axis, clothes flaring, a lived room or cyc, then stop on a three-quarter.", "Frozen at the stop of an outfit spin, clothes still settling, three-quarter to camera.", ("fashion",)),
        _vir("hallway_fashion", "Hallway fashion walk", "Walk a fashion hallway toward camera, clothes reading, fluorescent or window, the corridor as a runway of ordinary architecture.", "Frozen mid-stride in a fashion hallway walk, clothes reading, corridor as runway.", ("fashion", "walk")),
        _vir("fridge_pov", "Fridge-open POV", "Open a fridge as POV, light blooming, a hand choosing, unmarked cartons, the kitchen dark around the box.", "Frozen POV inside an open fridge bloom, a hand on an unmarked carton.", ("pov", "food"), "Fridge seal and a bottle clink."),
        _vir("coffee_steam", "Coffee-steam close", "Close on coffee steam in a window, cup unmarked, hands wrapping, morning bokeh, the vapor as weather.", "Frozen on coffee steam in a window, hands wrapping an unmarked cup.", ("food", "macro"), "Soft sip and a window tick."),
        _vir("ice_cube_drop", "Ice-cube drop", "Drop ice into a glass as a macro event, splash crown, amber or clear liquid, the cube as a meteor.", "Frozen at the ice-cube splash crown in a glass, liquid amber or clear.", ("food", "macro"), "Ice crack and a glass ping."),
        _vir("sauce_drizzle", "Sauce drizzle", "Drizzle sauce over a plated bite in macro, the ribbon controlled, garnish waiting, steam optional.", "Frozen mid-drizzle, a sauce ribbon over a plated bite.", ("food", "macro"), "Viscous drizzle."),
        _vir("chop_overhead", "Knife-chop overhead", "Chop overhead in rhythm, board crumbs, herbs, hands safe but fast, the cadence as the hook.", "Frozen overhead mid-chop, herbs and crumbs, knife in the board.", ("food",), "Knife cadence on wood."),
        _vir("dough_stretch", "Dough stretch", "Stretch dough toward camera, gluten window, flour atmosphere, hands as the machine.", "Frozen on a dough stretch, gluten window backlit, flour in the air.", ("food", "hands"), "Dough slap and flour puff."),
        _vir("latte_pour", "Latte-art pour", "Pour latte art in a close cup, white ribbon on brown, the pattern forming, unmarked ceramic.", "Frozen mid latte-art pour, white ribbon on brown, pattern half-formed.", ("food",), "Milk pour and a cup set."),
        _vir("pan_sizzle", "Pan sizzle", "Fill the frame with a pan sizzle, oil weather, an ingredient hitting, steam as a wall.", "Frozen at the ingredient hit in a sizzling pan, oil weather, steam as a wall.", ("food",), "Hard sizzle and a spatula."),
        _vir("oven_pull", "Oven pull", "Pull a tray from an oven toward camera, heat ripple, mitts, the kitchen blooming with gold.", "Frozen on an oven-pull, tray halfway, heat ripple, mitts.", ("food",), "Oven door and a tray scrape."),
        _vir("first_bite", "First-bite close", "Close on a first bite, steam, a crumb, eyes optional, the food as the actor.", "Frozen on a first bite, steam and a crumb, food as the actor.", ("food",), "A crisp bite."),
        _vir("closet_tryon", "Closet try-on", "Try on in a closet, hangers, a mirror slice, outfits swapping on a body, the small room as a booth.", "Frozen in a closet try-on, hangers, a mirror slice, an outfit mid-swap.", ("fashion",)),
        _vir("shoe_floor_pov", "Shoe-on floor POV", "POV a shoe onto a floor, laces, unmarked leather or mesh, the room beyond the toe.", "Frozen POV as a shoe meets the floor, laces, room beyond the toe.", ("pov", "fashion"), "Sole on wood."),
        _vir("jewelry_macro", "Jewelry macro", "Macro unmarked jewelry on skin or velvet, a catchlight walking, the metal as landscape.", "Frozen jewelry macro on skin or velvet, a catchlight parked.", ("fashion", "macro")),
        _vir("perfume_backlight", "Perfume-spray backlight", "Backlight a perfume spray so the mist becomes weather, an unmarked bottle, a neck, the droplets as stars.", "Frozen on a backlit perfume mist, unmarked bottle, droplets as stars.", ("beauty",), "A spray hiss."),
        _vir("skincare_dots", "Skincare dots", "Dot skincare on a face in a lit glass, white points, hands patting, the bathroom as a clinic of ordinary tile.", "Frozen on skincare dots on a face in a lit glass, hands about to pat.", ("beauty",)),
        _vir("brush_macro", "Makeup-brush macro", "Macro a brush on skin, bristle weather, pigment, the face a landscape of pores and product.", "Frozen brush-macro on skin, bristles bent, pigment.", ("beauty", "macro"), "Bristle whisper."),
        _vir("hair_flip", "Hair-flip slow", "Slow a hair-flip in backlight, strands as weather, a window or practical, then settle on a face to camera.", "Frozen mid hair-flip, strands as weather in backlight.", ("beauty",), "Hair whoosh."),
        _vir("ring_vanity_led", "Circular vanity LED", "Key a face with a circular vanity LED at a glass, even beauty, tile behind, the circle catching in the eyes.", "Frozen at a circular vanity LED glass, even beauty, tile, the circle in the eyes.", ("beauty",)),
        _vir("elevator_mirror", "Elevator-mirror close", "Hold an elevator-mirror close, fluorescent, a floor-number glow, outfit check, the box as a booth.", "Frozen in an elevator-mirror close, fluorescent, floor-number glow, outfit check.", ("fashion", "urban")),
        _vir("gym_mirror", "Gym-mirror effort", "Use a gym mirror so the effort and the room both read, iron, a phone not branded, sweat.", "Frozen in a gym-mirror effort, iron and sweat, the room doubled.", ("gym",), "Plates and breath."),
        _vir("lift_side", "Lift side-on effort", "Side-on a lift, bar path, effort face, a rack, handheld allowed to be ugly.", "Frozen side-on mid-lift, bar path, effort face, a rack.", ("gym",), "Bar clink and a brace breath."),
        _vir("run_watch_pov", "Run-watch POV", "POV a run with a watch-arm entering, path grain, breath, the city or park rushing.", "Frozen run POV, watch-arm in, path grain, city or park rushing.", ("pov", "gym"), "Breath and footfalls."),
        _vir("bottle_squeeze", "Water-bottle squeeze", "Squeeze a water bottle in gym light, plastic flex, a drink, sweat, the hydration as the insert.", "Frozen on a squeezed bottle, plastic flex, gym light, sweat.", ("gym",), "Plastic flex and a gulp."),
        _vir("smoothie_pour", "Smoothie pour", "Pour a smoothie in macro, thick ribbon, an unmarked glass, fruit grit visible.", "Frozen mid smoothie pour, thick ribbon, fruit grit, unmarked glass.", ("food",), "Thick pour."),
        _vir("meal_prep_grid", "Meal-prep container grid", "Overhead a meal-prep grid of containers, hands filling, color-blocked food, the counter as a factory.", "Frozen overhead on a meal-prep grid, hands filling color-blocked containers.", ("food",), "Lid clicks."),
        _vir("grocery_haul", "Grocery-haul bag", "Dump a grocery haul onto a counter, unmarked packaging, a bag, the kitchen receiving cargo.", "Frozen as groceries hit a counter, unmarked packaging, a bag still in frame.", ("food", "hands"), "Bag rustle and cans."),
        _vir("foam_pull", "Foam-pull unbox", "Pull foam from a box in a satisfying close, the object appearing, packing weather, no logo readable.", "Frozen mid foam-pull, the object appearing, packing weather.", ("product",), "Foam rub."),
        _vir("peel_plastic", "Peel-plastic satisfy", "Peel a plastic film in macro, the curl traveling, a clean surface revealed, the sound as the star.", "Frozen mid plastic-peel, a curl traveling, clean surface half-revealed.", ("macro", "asmr"), "Plastic peel."),
        _vir("magnet_click", "Magnet click-in", "Click a magnet or lid into place as a satisfying close, the join as the hook, unmarked object.", "Frozen at the magnet or lid click-in, the join as the picture.", ("product", "asmr"), "A crisp click."),
        _vir("led_desk_wash", "Colored LED desk wash", "Wash a desk in colored LED, a face in monitor glow, hands on unmarked keys, the night room as a cockpit.", "Frozen at a colored-LED desk, face in monitor glow, hands on unmarked keys.", ("desk", "night")),
        _vir("keyboard_close", "Keyboard close", "Close on unmarked keycaps, fingers, a satisfying travel, the desk a blur, the sound implied.", "Frozen on unmarked keycaps, fingers mid-travel, desk a blur.", ("desk", "asmr"), "Keycap ticks."),
        _vir("cable_tidy", "Cable-management tidy", "Tidy cables in a desk close, clips, a before mess becoming a line, hands as the solver.", "Frozen mid cable-tidy, clips, a mess becoming a line.", ("desk", "hands")),
        _vir("monitor_glow", "Monitor-glow face", "Key a face with monitor glow only, the room dark, eyes to the screen then a glance to camera.", "Frozen on a monitor-glow face in a dark room, a glance to camera.", ("desk", "night")),
        _vir("night_code", "Night-code desk", "Hold a night-code desk, two screens unmarked, a mug, hands, the window a black rectangle.", "Frozen on a night-code desk, two unmarked screens, a mug, hands.", ("desk", "night"), "Keycaps and a far siren."),
        _vir("study_overhead", "Study-with-me overhead", "Overhead a study spread: book, lamp, a timer unmarked, a hand annotating, the table as a quiet stage.", "Frozen overhead on a study spread, book and lamp, a hand annotating.", ("desk",), "Page turn and a pen."),
        _vir("plant_water", "Plant-watering close", "Water a plant in a close, spout, soil darkening, a window, the leaf as the face.", "Frozen on a plant being watered, spout, soil darkening, a window.", ("hands",), "Water on soil."),
        _vir("dog_golden_walk", "Dog golden-hour walk", "Walk a dog at golden hour, leash, face and animal sharing the vertical, a park path.", "Frozen in a golden-hour dog walk, leash, face and animal sharing the vertical.", ("walk", "golden"), "Collar jingle and footsteps."),
        _vir("park_bench_talk", "Park-bench talk", "Talk on a park bench to camera, trees bokeh, a path of extras, the seat as a studio.", "Frozen on a park-bench talk to camera, trees bokeh, a path of extras.", ("talking",), "Birds and a far bike bell."),
        _vir("market_bag", "Farmer-market bag", "Fill a market bag with produce, stall canvas, sun, hands, the haul as the story.", "Frozen filling a market bag with produce, stall canvas, sun.", ("food", "hands"), "Paper bag and a stall murmur."),
        _vir("bakery_window", "Bakery-window close", "Close on a bakery window, trays, a face reflection optional, the glass as a menu of steam.", "Frozen on a bakery window of trays, steam on glass, a street reflection.", ("food",), "A door chime and street."),
        _vir("bookstore_aisle", "Bookstore-aisle walk", "Walk a bookstore aisle, spines unmarked, a hand pulling a volume, the stack as a canyon of paper.", "Frozen in a bookstore aisle, a hand pulling a volume, spines unmarked.", ("walk",), "Page hush and a floor creak."),
        _vir("crate_dig", "Record-crate dig", "Dig a record crate, unmarked sleeves, fingers, a shop lamp, the bin as a treasure box.", "Frozen digging a record crate, unmarked sleeves, fingers, a shop lamp.", ("hands",), "Sleeve card and shop murmur."),
        _vir("vinyl_needle", "Vinyl needle drop", "Drop a needle on vinyl in macro, groove weather, a label unmarked, the tonearm as a crane.", "Frozen at a needle drop on unmarked vinyl, groove weather, tonearm.", ("macro", "music"), "Needle crackle."),
        _vir("crowd_phone_glow", "Crowd phone-glow", "Hold a crowd at night with phone-glows as stars, a stage smear, the vertical full of raised hands, no brand on glass.", "Frozen on a night crowd, phone-glows as stars, raised hands, stage smear.", ("night", "crowd"), "Crowd roar and a kick drum far."),
        _vir("festival_dust", "Festival-dust sunset", "Walk festival dust at sunset, flags, a bottle unmarked, face to camera, the field as gold weather.", "Frozen in festival dust at sunset, flags, face to camera, gold weather.", ("golden", "walk"), "Distant bass and dust wind."),
        _vir("beach_gimbal", "Beach gimbal walk", "Gimbal-walk a beach, horizon true, feet optional, face talking or silent, glare managed.", "Frozen in a beach gimbal walk, horizon true, glare, face talking or silent.", ("walk", "beach"), "Surf and wind."),
        _vir("pool_overhead", "Pool-float overhead", "Overhead a pool float, water caustics, a body, the rectangle of blue as the whole world.", "Frozen overhead on a pool float, caustics, a body, a rectangle of blue.", ("beach",), "Water lap."),
        _vir("dive_board_pov", "Diving-board POV", "POV a diving-board walk then the drop, tile, the water rushing up, the last frame a smash of blue.", "Frozen on a diving-board POV, water rushing up, tile behind.", ("pov", "energy"), "Board spring and a splash."),
        _vir("ski_goggle_pov", "Ski-goggle POV", "POV through ski goggles, snow grain, a slope, breath in the foam, poles entering.", "Frozen ski-goggle POV, snow grain, a slope, breath in the foam.", ("pov", "snow"), "Wind and ski chatter."),
        _vir("handlebar_city", "Handlebar city POV", "POV handlebars through a city, unmarked stem, potholes, the vanishing point a street.", "Frozen handlebar POV, unmarked stem, a city vanishing point, potholes.", ("pov", "vehicle"), "Tire hum and a bell."),
        _vir("bus_window_face", "Bus-window face", "Hold a bus-window face, passing world as smear, interior reflection, 9:16, the pane as weather.", "Frozen on a bus-window face, passing smear, interior reflection.", ("transit",), "Bus rumble."),
        _vir("train_seat_talk", "Train-seat talk", "Talk from a train seat to camera, window fields, a table, the car as a moving room.", "Frozen in a train-seat talk, window fields, a table, the car as a moving room.", ("talking", "transit"), "Rail click and HVAC."),
        _vir("plane_window_wing", "Plane-window wing", "Hold a plane-window wing, weather, a tray table, a face optional, the wing as a landscape.", "Frozen on a plane-window wing, weather, a tray table.", ("transit",), "Cabin hiss."),
        _vir("hotel_room_pan", "Hotel-room pan tour", "Pan a hotel room as a tour, bed, window, a bag, no logos, the space as a brief home.", "Frozen mid hotel-room pan, bed and window, a bag, no logos.", ("travel",)),
        _vir("pack_cubes", "Packing-cube fill", "Fill packing cubes on a bed, clothes, a zipper, the suitcase as a puzzle.", "Frozen filling a packing cube on a bed, clothes, a zipper halfway.", ("hands", "travel"), "Zipper and fabric."),
        _vir("boot_mud_hike", "Hiking-boot mud", "Close on a hiking boot in mud, tread, a trail, the step as the hook.", "Frozen on a hiking boot in mud, tread, a trail.", ("walk",), "Mud suck."),
        _vir("summit_reveal", "Summit reveal", "Reveal a summit view past a figure, wind, a tiny person, the drop as the punch.", "Frozen at a summit reveal, a tiny figure, the drop, wind in clothes.", ("scale",), "Wind roar."),
        _vir("tent_morning", "Tent-morning unzip", "Unzip a tent morning, gold light, a sleeping-bag, the fly as a curtain, landscape arriving.", "Frozen mid tent-unzip, gold light, a sleeping-bag, landscape arriving.", ("travel",), "Zipper and birds."),
        _vir("camp_coffee", "Camp-coffee pour", "Pour camp coffee over a stove, enamel cup unmarked, pines, steam in cold air.", "Frozen pouring camp coffee into unmarked enamel, pines, steam in cold air.", ("food",), "Stove hiss and a pour."),
        _vir("bonfire_talk", "Bonfire talk", "Talk at a bonfire, faces gold, sparks, a dark ring of friends, the fire as the key.", "Frozen in a bonfire talk, face gold, sparks, a dark ring of friends.", ("talking", "night"), "Fire crackle."),
        _vir("cake_slice", "Cake-slice pull", "Pull a cake slice, crumb weather, a plate, the cut as the satisfy.", "Frozen pulling a cake slice, crumb weather, a plate.", ("food",), "A knife through crumb."),
        _vir("unwrap_gift", "Gift unwrap", "Unwrap a gift in close, paper tear, an object unmarked, hands, the reveal as the hook.", "Frozen mid gift-unwrap, paper tear, an unmarked object appearing.", ("hands",), "Paper tear."),
        _vir("side_eye_lens", "Side-eye to lens", "Throw a side-eye to the lens from a conversation, MCU, the fourth-wall as the joke.", "Frozen on a side-eye to the lens from a conversation, MCU.", ("hook", "talking")),
        _vir("wink_hold", "Fourth-wall wink hold", "Wink to camera and hold, MCU, a lived room, then resume the task.", "Frozen on a wink to camera, MCU, a lived room.", ("hook",)),
        _vir("paper_tear", "Paper-tear transition", "Tear paper as a transition, the hole becoming the next scene, hands, kraft texture.", "Frozen mid paper-tear, a hole opening into the next scene.", ("edit", "hands"), "Paper tear."),
        _vir("whip_to_product", "Whip to product", "Whip-pan to a product on a table, the smear resolving on the hero object, then a hold.", "Frozen at the end of a whip-to-product, smear resolved on the hero object.", ("product", "hook")),
        _vir("pottery_wheel", "Pottery-wheel close", "Close on a pottery wheel, clay weather, wet hands, the cylinder rising, water as spray.", "Frozen on a pottery wheel, clay cylinder rising, wet hands.", ("hands", "macro"), "Wet clay slap and a wheel hum."),
        _vir("match_strike", "Match-strike backlight", "Strike a match in backlight, sulfur bloom, a candle waiting, the flame as the cut-in.", "Frozen at match-strike bloom, sulfur, a candle waiting.", ("macro",), "Match hiss."),
        _vir("tea_high_pour", "High tea pour", "Pour tea from a height, the stream a line, unmarked pot, steam, a table of ordinary china.", "Frozen on a high tea pour, the stream a line, steam, unmarked pot.", ("food",), "Stream into a cup."),
        _vir("dumpling_fold", "Dumpling-fold close", "Fold dumplings in a close, pleats, flour, hands skilled, a tray filling.", "Frozen mid dumpling-fold, a pleat, flour, a tray.", ("food", "hands"), "Dough pinch."),
        _vir("night_market_steam", "Night-market steam", "Walk a night market of steam, skewers, neon smear, a bite, the aisle as weather.", "Frozen in a night-market steam aisle, skewers, neon smear, a bite.", ("food", "night"), "Sizzle and crowd murmur."),
        _vir("umbrella_street", "Umbrella-street walk", "Walk under an umbrella on a wet street, the dome as a lid, face in shadow, neon on the fabric.", "Frozen under an umbrella on a wet street, neon on the fabric, face in shadow.", ("walk", "weather"), "Rain on fabric."),
        _vir("mitten_cup", "Mitten-hold cup", "Hold a mittened cup in cold air, steam, a street, the hands as the story.", "Frozen on mittened hands around a steaming cup, a cold street.", ("winter",), "A soft sip and snow hush."),
        _vir("fireplace_talk", "Fireplace talk", "Talk by a fireplace, gold flicker on a face, a room of books, the fire as the only key.", "Frozen in a fireplace talk, gold flicker on a face, a room of books.", ("talking", "interior"), "Fire pop."),
        _vir("lantern_walk", "Lantern walk", "Walk with a lantern, the pool of gold traveling, a path, moths, the dark as the walls.", "Frozen in a lantern walk, a gold pool on a path, moths, dark walls.", ("walk", "night"), "Footsteps and insect hush."),
        _vir("soap_cut", "Soap-cut satisfy", "Cut soap or wax in macro, the slice clean, shavings, the interior pattern revealed.", "Frozen mid soap-cut, a clean slice, interior pattern, shavings.", ("macro", "asmr"), "A knife through wax."),
        _vir("paint_pour", "Paint-pour bloom", "Pour paint so colors bloom on a surface, unnamed fluid art, the puddle as weather.", "Frozen mid paint-pour, colors blooming on a surface.", ("macro",), "Viscous puddle."),
        _vir("incense_curl", "Incense-curl backlight", "Backlight an incense curl, the smoke as a drawing, an unmarked stick, a still room.", "Frozen on a backlit incense curl, smoke as a drawing, an unmarked stick.", ("macro", "interior"), "A quiet room and a faint hiss."),
        _vir("rain_window_talk", "Rain-window talk", "Talk at a rain window, drops as bokeh, face interior-lit, the weather as the other actor.", "Frozen in a rain-window talk, drops as bokeh, face interior-lit.", ("talking", "weather"), "Rain on pane."),
        _vir("breath_cold_talk", "Cold-breath talk", "Talk in cold air so breath is weather, a street or rooftop, face to camera, wool.", "Frozen in a cold-breath talk, vapor, wool, face to camera.", ("talking", "winter"), "Wool rustle and a far horn."),
        _vir("string_light_porch", "String-light porch talk", "Talk on a porch under string-lights, moths, a railing, the yard black, the face gold.", "Frozen on a string-light porch talk, moths, a railing, face gold.", ("talking", "night"), "Bug-zapper far and a chair creak."),
        _vir("cocktail_shake", "Cocktail shake", "Shake a cocktail in close, ice weather, an unmarked tin, then a pour.", "Frozen mid cocktail-shake, ice weather, unmarked tin.", ("food",), "Ice in a tin."),
        _vir("plate_wipe", "Plate-wipe garnish", "Wipe a plate and place a garnish as a chef close, sauce comma, steam, the china unmarked.", "Frozen on a plate-wipe, a garnish landing, sauce comma, steam.", ("food",), "Plate and a tweezer tick."),
        _vir("thrift_table", "Thrift-table flip", "Flip thrift finds on a table, unmarked garments, a hand, a window, the pile as a treasure map.", "Frozen flipping a thrift garment on a table, a window, a pile.", ("fashion", "hands"), "Hanger tick."),
        _vir("noodle_pull", "Noodle-pull close", "Pull noodles in a close, flour atmosphere, dough ropes, hands as machines.", "Frozen mid noodle-pull, dough ropes, flour atmosphere.", ("food", "hands"), "Dough slap."),
        _vir("espresso_crema", "Espresso crema close", "Close on espresso crema forming, unmarked cup, a machine implied, the tiger-skin as landscape.", "Frozen on forming espresso crema, unmarked cup, tiger-skin surface.", ("food", "macro"), "Machine pump and a drip."),
        _vir("ice_latte_swirl", "Ice-latte swirl", "Swirl an ice latte so milk weather marbles the glass, cubes, an unmarked straw later.", "Frozen on an ice-latte swirl, milk weather marbling the glass, cubes.", ("food", "macro"), "Ice and a stir."),
        _vir("citrus_twist", "Citrus-twist macro", "Twist citrus over a glass, oil spray as stars in backlight, peel, an unmarked drink.", "Frozen on a citrus twist, oil spray as stars, peel, unmarked glass.", ("food", "macro"), "Peel crack and a spray."),
        _vir("puddle_jump", "Puddle-jump", "Jump a puddle toward camera, splash crown, rain clothes, a street, the splash as the hook.", "Frozen at a puddle-jump splash crown, rain clothes, a street.", ("walk", "weather"), "A splash."),
        _vir("rewind_outfit", "Rewind outfit change", "Rewind an outfit change on a held mark, clothes flying back, then play forward, the body as a hinge.", "Frozen mid rewind-outfit, clothes in a flying in-between, the mark held.", ("fashion", "edit")),
        _vir("stop_motion_desk", "Stop-motion desk", "Animate a desk in stop-motion, objects traveling in chops, a hand sometimes, the table as a stage.", "Frozen on one stop-motion desk chop, objects mid-travel.", ("desk", "edit")),
        _vir("clone_offset", "Offset clone two-shot", "Offset the same person twice in a vertical, two tasks, a shared room, no platform chrome.", "Frozen as an offset clone two-shot of the same person, two tasks, a shared room.", ("edit",)),
        _vir("notification_face", "Notification-face glance", "Glance down at a phone then up to camera, MCU, the face as a reaction, the glass unmarked.", "Frozen on the up-glance to camera after a phone look, MCU, unmarked glass.", ("reaction", "talking")),
        _vir("text_safe_lower_talk", "Talk with lower-third air", "Talk MCU with the lower third empty of chin-hands, caption air reserved, a lived wall.", "Frozen in a talking MCU with empty lower-third air, chin clear of the hat.", ("talking", "safe")),
        _vir("boom_reveal_roof", "Boom-up rooftop reveal", "Boom up from a rooftop parapet to a talking face and skyline, the city arriving under the chin.", "Frozen at the top of a rooftop boom, face and skyline, parapet gone.", ("move", "talking")),
        _vir("slowmo_hair_sun", "Slow-mo hair sun", "Slow-mo hair in sun, strands, a laugh, then resume talk speed.", "Frozen in slow-mo hair-in-sun, strands, a laugh mid-peak.", ("beauty", "golden")),
        _vir("doorway_enter_hook", "Doorway-enter hook", "Enter a doorway toward camera as the first-frame hook, interior blooming, then talk.", "Frozen in a doorway-enter, interior blooming around a figure coming at camera.", ("hook", "walk")),
        _vir("bag_drop_desk", "Bag-drop desk start", "Drop a bag on a desk as the start, keys, a chair, then sit into talk, the arrival as the hook.", "Frozen at a bag-drop on a desk, keys, the sit not yet begun.", ("hook", "desk"), "Bag thud and keys."),
        _vir("window_lean_talk", "Window-lean talk", "Lean in a window talking to camera, street below, curtains, the sill as a desk.", "Frozen leaning in a window talking to camera, street below, curtains.", ("talking",)),
        _vir("bike_city_talk", "Bike-city talking mount", "Talk from a bike-city mount, unmarked bars, wind, storefronts traveling, the face stable-ish.", "Frozen on a bike-city talking mount, unmarked bars, storefronts traveling.", ("vehicle", "talking"), "Wind and a freewheel."),
        _vir("escalator_talk", "Escalator talking rise", "Talk on an escalator rise, mall or station architecture unrolling, face to camera, the steps as a treadmill.", "Frozen on an escalator talking rise, architecture unrolling, face to camera.", ("talking", "transit")),
        _vir("laundry_fold_talk", "Laundry-fold talk", "Fold laundry while talking to camera, cloth weather, a couch, the domestic as the set.", "Frozen folding laundry while talking, cloth weather, a couch.", ("talking", "hands"), "Cloth snap."),
        _vir("sink_splash_wake", "Sink-splash wake", "Splash a sink as a wake-up hook, water weather, a face coming up, tile.", "Frozen at a sink-splash, water weather, a face coming up, tile.", ("hook", "beauty"), "Water in a basin."),
        _vir("blinds_open_hook", "Blinds-open hook", "Open blinds as the first-frame hook, dust in the new sun, a room waking, then a turn to camera.", "Frozen mid blinds-open, dust in new sun, a room waking.", ("hook",), "Blinds clatter."),
        _vir("match_cut_food_to_face", "Food-to-face match", "Match-cut a plated bite to a first-bite face on the same axis, the food becoming the eater.", "Frozen on the face after a food-to-face match, the bite implied, same axis.", ("food", "edit")),
        _vir("center_product_hands", "Center-axis product hands", "Hold a product in center-axis hands, 9:16, a lived table, the object turning, face optional above.", "Frozen holding a product on the center axis, lived table, object mid-turn.", ("product", "comp")),
        _vir("rain_bus_talk", "Rain-bus talking", "Talk on a rain bus, pane drops, fluorescent, a pole, the public as the set.", "Frozen talking on a rain bus, pane drops, fluorescent, a pole.", ("talking", "transit"), "Bus HVAC and rain on glass."),
        _vir("golden_field_spin", "Golden-field spin", "Spin in a golden field, clothes flaring, then stop to camera, pollen weather.", "Frozen at the stop of a golden-field spin, clothes settling, pollen weather, face to camera.", ("golden", "fashion"), "Wind in grass."),
        _vir("night_rooftop_bokeh_talk", "Night rooftop bokeh talk", "Talk on a night rooftop, city bokeh, a practical, wind, the skyline as jewelry.", "Frozen in a night rooftop talk, city bokeh, a practical, skyline as jewelry.", ("talking", "night"), "Wind and a far siren."),
        _vir("asmr_ice_crack", "Ice-crack macro", "Crack ice in macro, fissures traveling, backlight, the sound as the star.", "Frozen mid ice-crack, fissures traveling, backlight.", ("macro", "asmr"), "Ice crack."),
        _vir("pour_over_bloom", "Pour-over bloom", "Bloom a pour-over in close, unmarked dripper, coffee weather, a spiral pour.", "Frozen on a pour-over bloom, unmarked dripper, a spiral pour.", ("food",), "Kettle and drip."),
        _vir("skillet_flip", "Skillet flip", "Flip a skillet toward camera, food in air, then the catch, a stove, the stunt as the hook.", "Frozen with food in air above a skillet, stove, the catch implied.", ("food", "hook"), "A pan whoosh."),
        _vir("closet_light_pull", "Closet-light pull", "Pull a closet light, the booth blooming, clothes as a wall, then a try-on.", "Frozen at the closet-light bloom, clothes as a wall, try-on about to start.", ("fashion", "hook"), "A pull-chain tick."),
        _vir("window_seat_book", "Window-seat book", "Hold a window-seat with a book, rain or sun, a face sometimes, the glass as weather TV.", "Frozen on a window-seat book, rain or sun on the glass, a face optional.", ("still-look",), "Page and pane."),
        _vir("crosswalk_center", "Crosswalk center-axis", "Walk a crosswalk on the center axis toward camera, signals, a city, the stripes as a runway.", "Frozen mid crosswalk on the center axis, signals, stripes as a runway.", ("walk", "comp"), "A walk signal and traffic."),
        _vir("mirror_flash_change", "Mirror flash outfit change", "Use a mirror flash or blink to hide an outfit change, same mark, the glass as a cut.", "Frozen after a mirror-flash outfit change, same mark, new clothes, the glass still.", ("fashion", "edit")),
        _vir("caption_headroom_talk", "Talking with caption headroom", "Talk MCU with extra headroom and empty lower third, 9:16, a lived wall, safe for later type.", "Frozen talking MCU with extra headroom and empty lower third, lived wall.", ("talking", "safe")),
        _vir("silent_product_hold", "Silent product one-second hold", "Hold a silent product hero for one second then orbit or tilt, the still as the thumb-stop.", "Frozen on a silent one-second product hero before the orbit starts.", ("product", "hook")),
        _vir("face_then_insert", "Face then insert cut", "Hold a talking face then cut to a matching insert of the thing named, the grammar of show-after-tell.", "Frozen on the insert after a talking face, the named object filling the frame.", ("talking", "edit")),
        _vir("z_push_then_hold_talk", "Z-push then hold talk", "Z-push into a talking MCU then hold for speech, the move as the hook, the hold as the point.", "Frozen at the hold after a Z-push, talking MCU, speech-ready.", ("hook", "talking")),
        _vir("crowd_part_walk", "Crowd-part walk to camera", "Walk through a parting crowd toward camera, shoulders wiping, then a MCU land.", "Frozen walking through a parting crowd toward camera, shoulders wiping, MCU approaching.", ("walk", "hook"), "Crowd murmur."),
        _vir("umbrella_open_hook", "Umbrella-open hook", "Open an umbrella toward camera as the first-frame bloom, then a rain-walk, the dome as a cut to weather.", "Frozen at umbrella-open bloom toward camera, rain implied, the dome filling the frame.", ("hook", "weather"), "Fabric whoosh and rain."),
    ]
    return rows


def _rec(rid: str, label: str, **axes: str) -> dict[str, Any]:
    return {"id": rid, "label": label, "axes": dict(axes)}


def recipes() -> list[dict[str, Any]]:
    return [
        _rec("rec_rain_noir", "Rain noir alley", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_slow_dolly_in", lenses_optics="opt_35_classic", composition="cmp_dirty_fg", lighting="lit_rain_wet_bounce", color_film_look="col_bleach_bypass", time_motion="tim_shutter_180", in_camera_optical="fx_rain_on_lens", atmosphere_weather="atm_neon_noodle_rain", genre_looks="gen_rain_noir_alley"),
        _rec("rec_neo_noir_wet", "Neo-noir wet street", framing_shot_size="size_full", camera_angles="ang_level", camera_movement="move_tracking_left", lenses_optics="opt_35_classic", composition="cmp_vanishing", lighting="lit_neon", color_film_look="col_crushed_shadow", time_motion="tim_shutter_180", in_camera_optical="fx_rain_on_lens", atmosphere_weather="atm_wet_asphalt_mirror", genre_looks="gen_neo_noir_wet"),
        _rec("rec_western_noon", "Western dust noon", framing_shot_size="size_long", camera_angles="ang_eye", camera_movement="move_locked_off", lenses_optics="opt_24_wide", composition="cmp_vanishing", lighting="lit_desert_sun", color_film_look="col_color_neg_warm", time_motion="tim_realtime", atmosphere_weather="atm_dirt_road_talc", genre_looks="gen_western_dust_noon"),
        _rec("rec_western_magic", "Desert western magic hour", framing_shot_size="size_cowboy", camera_angles="ang_eye", camera_movement="move_locked_off", lenses_optics="opt_50_normal", composition="cmp_thirds_right", lighting="lit_golden_hour", color_film_look="col_color_neg_warm", time_motion="tim_shutter_180", atmosphere_weather="atm_desert_golden_buttes", genre_looks="gen_desert_western_magic"),
        _rec("rec_horror_hall", "Horror hallway", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_slow_dolly_in", lenses_optics="opt_28_street", composition="cmp_vanishing", lighting="lit_low_key", color_film_look="col_crushed_shadow", time_motion="tim_realtime", atmosphere_weather="atm_park_lamp_moisture", genre_looks="gen_horror_hallway_under"),
        _rec("rec_folk_field", "Folk-horror field", framing_shot_size="size_ews", camera_angles="ang_eye", camera_movement="move_locked_off", lenses_optics="opt_24_wide", composition="cmp_isolation", lighting="lit_overcast_skyfill", color_film_look="col_print_density", time_motion="tim_realtime", atmosphere_weather="atm_heavy_overcast_mill", genre_looks="gen_folk_standing_stones"),
        _rec("rec_cyber_wet", "Cyberpunk wet neon", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_dolly_in", lenses_optics="opt_35_classic", composition="cmp_dirty_fg", lighting="lit_neon", color_film_look="col_split_tone_warm_cool", time_motion="tim_shutter_180", in_camera_optical="fx_rain_on_lens", atmosphere_weather="atm_neon_noodle_rain", genre_looks="gen_cyberpunk_wet_neon"),
        _rec("rec_solarpunk", "Solarpunk clear sun", framing_shot_size="size_full", camera_angles="ang_eye", camera_movement="move_locked_off", lenses_optics="opt_35_classic", composition="cmp_clean_graphic", lighting="lit_hard_noon", color_film_look="col_pastel_candy", time_motion="tim_realtime", atmosphere_weather="atm_stucco_noon_knife", genre_looks="gen_solarpunk_glasshouse"),
        _rec("rec_coastal_golden", "Coastal magic hour", framing_shot_size="size_full", camera_angles="ang_eye", camera_movement="move_locked_off", lenses_optics="opt_50_normal", composition="cmp_thirds_right", lighting="lit_golden_hour", color_film_look="col_color_neg_warm", time_motion="tim_shutter_180", atmosphere_weather="atm_cliff_path_spray", genre_looks="gen_coastal_magic_hour"),
        _rec("rec_mountain_sublime", "Mountain sublime", framing_shot_size="size_ews", camera_angles="ang_eye", camera_movement="move_pull_to_solitude", lenses_optics="opt_24_wide", composition="cmp_isolation", lighting="lit_open_shade", color_film_look="col_print_density", time_motion="tim_realtime", atmosphere_weather="atm_granite_saddle", genre_looks="gen_mountain_sublime"),
        _rec("rec_snow_iso", "Snow-bound isolation", framing_shot_size="size_long", camera_angles="ang_eye", camera_movement="move_locked_off", lenses_optics="opt_50_normal", composition="cmp_isolation", lighting="lit_snow_bounce", color_film_look="col_crushed_shadow", time_motion="tim_realtime", atmosphere_weather="atm_blizzard_grid", genre_looks="gen_snowbound_cabin"),
        _rec("rec_arctic", "Arctic white-out", framing_shot_size="size_ews", camera_angles="ang_eye", camera_movement="move_locked_off", lenses_optics="opt_35_classic", composition="cmp_isolation", lighting="lit_overcast_skyfill", color_film_look="col_super_white", time_motion="tim_realtime", atmosphere_weather="atm_ice_fog_headlights", genre_looks="gen_arctic_whiteout"),
        _rec("rec_gothic_candle", "Gothic candle", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_slow_dolly_in", lenses_optics="opt_35_classic", composition="cmp_frame_in_frame", lighting="lit_candle_multi", color_film_look="col_analogous_amber", time_motion="tim_shutter_180", atmosphere_weather="atm_moon_halo_pines", genre_looks="gen_gothic_candle_nave"),
        _rec("rec_romcom", "Rom-com bounce day", framing_shot_size="size_mcu", camera_angles="ang_eye", camera_movement="move_locked_off", lenses_optics="opt_50_normal", composition="cmp_thirds_right", lighting="lit_beauty", color_film_look="col_color_neg_warm", time_motion="tim_realtime", atmosphere_weather="atm_clear_plaza", genre_looks="gen_romcom_bounce"),
        _rec("rec_heist_cool", "Heist cool tungsten", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_locked_off", lenses_optics="opt_35_classic", composition="cmp_layers_three", lighting="lit_tungsten_daylight_mix", color_film_look="col_tungsten_day_cool", time_motion="tim_realtime", atmosphere_weather="atm_black_wet_tavern", genre_looks="gen_heist_warehouse"),
        _rec("rec_war_dust", "War handheld dust", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_handheld_breathe", lenses_optics="opt_28_street", composition="cmp_dirty_fg", lighting="lit_hard_noon", color_film_look="col_bleach_bypass", time_motion="tim_shutter_180", atmosphere_weather="atm_dirt_road_talc", genre_looks="gen_war_trench_dust"),
        _rec("rec_giallo_night", "Giallo gel night", framing_shot_size="size_ms", camera_angles="ang_dutch_mild", camera_movement="move_slow_dolly_in", lenses_optics="opt_35_classic", composition="cmp_diagonal", lighting="lit_dual_color_split", color_film_look="col_cross_process", time_motion="tim_realtime", atmosphere_weather="atm_black_wet_night_neon", genre_looks="gen_giallo_stair_gel"),
        _rec("rec_kitchen_sink", "Kitchen-sink overcast", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_handheld_breathe", lenses_optics="opt_35_classic", composition="cmp_dirty_fg", lighting="lit_overcast_skyfill", color_film_look="col_print_density", time_motion="tim_realtime", atmosphere_weather="atm_heavy_overcast_mill", genre_looks="gen_kitchen_sink_overcast"),
        _rec("rec_interrogation", "Noir interrogation bulb", framing_shot_size="size_mcu", camera_angles="ang_front", camera_movement="move_locked_off", lenses_optics="opt_50_normal", composition="cmp_center_punch", lighting="lit_interrogation", color_film_look="col_crushed_shadow", time_motion="tim_realtime", atmosphere_weather="atm_park_lamp_moisture", genre_looks="gen_interrogation_bulb"),
        _rec("rec_jungle_wet", "Jungle wet leaf-vault", framing_shot_size="size_full", camera_angles="ang_eye", camera_movement="move_fog_in", lenses_optics="opt_35_classic", composition="cmp_layers_three", lighting="lit_leaf_dapple", color_film_look="col_print_density", time_motion="tim_realtime", atmosphere_weather="atm_jungle_track_steam", genre_looks="gen_jungle_leaf_vault"),
        _rec("rec_club_strobe", "Night-club strobe", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_handheld_breathe", lenses_optics="opt_24_wide", composition="cmp_cluster", lighting="lit_disco_breakup", color_film_look="col_pastel_candy", time_motion="tim_shutter_45", atmosphere_weather="atm_stage_apron_low_fog", genre_looks="gen_club_strobe_fog"),
        _rec("rec_sports_iso", "Sports long-lens isolation", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_locked_off", lenses_optics="opt_200_sports", composition="cmp_isolation", lighting="lit_hard_noon", color_film_look="col_color_neg_warm", time_motion="tim_slowmo_40", atmosphere_weather="atm_stucco_noon_knife", genre_looks="gen_sports_long_iso"),
        _rec("rec_doc_available", "Documentary available", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_handheld_walk", lenses_optics="opt_28_street", composition="cmp_dirty_fg", lighting="lit_overcast_skyfill", color_film_look="col_print_density", time_motion="tim_realtime", atmosphere_weather="atm_heavy_overcast_mill", genre_looks="gen_doc_available_street"),
        _rec("rec_found_footage", "Found-footage night", framing_shot_size="size_ms", camera_angles="ang_pov", camera_movement="move_handheld_breathe", lenses_optics="opt_24_wide", composition="cmp_dirty_fg", lighting="lit_flashlight", color_film_look="col_crushed_shadow", time_motion="tim_realtime", atmosphere_weather="atm_park_lamp_moisture", genre_looks="gen_found_footage_led", viral_looks="vir_imperfect_handheld"),
        _rec("rec_period_candle", "Period candle and daylight", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_locked_off", lenses_optics="opt_50_normal", composition="cmp_frame_in_frame", lighting="lit_window", color_film_look="col_color_neg_warm", time_motion="tim_realtime", atmosphere_weather="atm_dawn_dew_lawn", genre_looks="gen_period_candle_day"),
        _rec("rec_caper_night", "Caper cool night", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_gimbal_orbit", lenses_optics="opt_35_classic", composition="cmp_layers_three", lighting="lit_blue_city_mix", color_film_look="col_tungsten_day_cool", time_motion="tim_realtime", atmosphere_weather="atm_black_wet_tavern", genre_looks="gen_caper_night_cool"),
        _rec("rec_court", "Courtroom fluorescent", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_locked_off", lenses_optics="opt_50_normal", composition="cmp_center_punch", lighting="lit_fluorescent_office", color_film_look="col_print_density", time_motion="tim_realtime", atmosphere_weather="atm_altostratus_dome", genre_looks="gen_courtroom_fluorescent"),
        _rec("rec_hospital", "Hospital green practical", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_locked_off", lenses_optics="opt_35_classic", composition="cmp_vanishing", lighting="lit_operating_room", color_film_look="col_print_density", time_motion="tim_realtime", atmosphere_weather="atm_altostratus_dome", genre_looks="gen_hospital_green"),
        _rec("rec_action_haze", "Action sun-backlight haze", framing_shot_size="size_full", camera_angles="ang_eye", camera_movement="move_handheld_walk", lenses_optics="opt_35_classic", composition="cmp_dirty_fg", lighting="lit_silhouette", color_film_look="col_bleach_bypass", time_motion="tim_shutter_180", atmosphere_weather="atm_dirt_road_talc", genre_looks="gen_action_sun_haze"),
        _rec("rec_prestige_blue", "Prestige blue-hour", framing_shot_size="size_mcu", camera_angles="ang_eye", camera_movement="move_slow_dolly_in", lenses_optics="opt_135_isolate", composition="cmp_isolation", lighting="lit_blue_hour", color_film_look="col_complementary_grade", time_motion="tim_shutter_180", atmosphere_weather="atm_harbor_blue_hour", genre_looks="gen_prestige_shallow"),
        _rec("rec_slasher_night", "Slasher night practical", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_handheld_breathe", lenses_optics="opt_28_street", composition="cmp_frame_in_frame", lighting="lit_fridge", color_film_look="col_crushed_shadow", time_motion="tim_realtime", atmosphere_weather="atm_park_lamp_moisture", genre_looks="gen_slasher_fridge_practical"),
        _rec("rec_musical", "Musical theatrical", framing_shot_size="size_full", camera_angles="ang_eye", camera_movement="move_dolly_in", lenses_optics="opt_24_wide", composition="cmp_center_punch", lighting="lit_white_cyc_highkey", color_film_look="col_three_strip", time_motion="tim_realtime", genre_looks="gen_musical_cyc"),
        _rec("rec_submarine", "Submarine red practical", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_locked_off", lenses_optics="opt_28_street", composition="cmp_frame_in_frame", lighting="lit_cameo", color_film_look="col_crushed_shadow", time_motion="tim_realtime", genre_looks="gen_submarine_red"),
        _rec("rec_viral_talk", "Viral talking MCU", framing_shot_size="size_mcu", camera_angles="ang_front", camera_movement="move_locked_off", lenses_optics="opt_35_classic", composition="cmp_center_vertical", lighting="lit_window", color_film_look="col_color_neg_warm", time_motion="tim_realtime", atmosphere_weather="atm_clear_plaza", viral_looks="vir_talking_mcu"),
        _rec("rec_viral_rain_walk", "Viral rain-walk", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_handheld_walk", lenses_optics="opt_35_classic", composition="cmp_center_vertical", lighting="lit_rain_wet_bounce", color_film_look="col_print_density", time_motion="tim_realtime", in_camera_optical="fx_rain_on_lens", atmosphere_weather="atm_rain_bus_shelter", viral_looks="vir_rain_walk"),
        _rec("rec_viral_mirror", "Viral mirror-ready glass", framing_shot_size="size_mcu", camera_angles="ang_front", camera_movement="move_locked_off", lenses_optics="opt_50_normal", composition="cmp_center_vertical", lighting="lit_vanity", color_film_look="col_color_neg_warm", time_motion="tim_realtime", viral_looks="vir_mirror_ready_glass"),
        _rec("rec_viral_pour", "Viral macro pour", framing_shot_size="size_insert_food", camera_angles="ang_tabletop", camera_movement="move_locked_off", lenses_optics="opt_100_compress", composition="cmp_center_punch", lighting="lit_soft", color_film_look="col_color_neg_warm", time_motion="tim_realtime", viral_looks="vir_macro_pour"),
        _rec("rec_viral_hook_hold", "Viral snap-push hold", framing_shot_size="size_mcu", camera_angles="ang_front", camera_movement="move_crash_dolly_in", lenses_optics="opt_35_classic", composition="cmp_center_vertical", lighting="lit_window", color_film_look="col_color_neg_warm", time_motion="tim_realtime", viral_looks="vir_snap_push_hold"),
        _rec("rec_viral_golden", "Viral golden boom", framing_shot_size="size_mcu", camera_angles="ang_eye", camera_movement="move_gimbal_rise", lenses_optics="opt_24_wide", composition="cmp_center_vertical", lighting="lit_golden_hour", color_film_look="col_color_neg_warm", time_motion="tim_shutter_180", atmosphere_weather="atm_orchard_gold_dust", viral_looks="vir_golden_boom_stick"),
        _rec("rec_viral_night_bokeh", "Viral night bokeh walk", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_handheld_walk", lenses_optics="opt_50_normal", composition="cmp_center_vertical", lighting="lit_neon", color_film_look="col_crushed_shadow", time_motion="tim_shutter_180", atmosphere_weather="atm_neon_noodle_rain", viral_looks="vir_night_bokeh_walk"),
        _rec("rec_viral_orbit", "Viral product orbit", framing_shot_size="size_insert_product", camera_angles="ang_tabletop", camera_movement="move_gimbal_orbit", lenses_optics="opt_100_compress", composition="cmp_center_punch", lighting="lit_wrap", color_film_look="col_color_neg_warm", time_motion="tim_realtime", genre_looks="gen_product_wrap", viral_looks="vir_product_orbit"),
        _rec("rec_viral_caption_safe", "Viral caption-safe talk", framing_shot_size="size_mcu", camera_angles="ang_front", camera_movement="move_locked_off", lenses_optics="opt_35_classic", composition="cmp_center_vertical", lighting="lit_soft", color_film_look="col_color_neg_warm", time_motion="tim_realtime", viral_looks="vir_caption_headroom_talk"),
        _rec("rec_noir_venetian", "Noir venetian office", framing_shot_size="size_ms", camera_angles="ang_eye", camera_movement="move_locked_off", lenses_optics="opt_50_normal", composition="cmp_frame_in_frame", lighting="lit_venetian_bars", color_film_look="col_crushed_shadow", time_motion="tim_realtime", atmosphere_weather="atm_barn_loft_dust", genre_looks="gen_noir_venetian"),
        _rec("rec_bodycam", "Body-cam precinct", framing_shot_size="size_ms", camera_angles="ang_chest_cam", camera_movement="move_handheld_walk", lenses_optics="opt_24_wide", composition="cmp_dirty_fg", lighting="lit_fluorescent_office", color_film_look="col_print_density", time_motion="tim_realtime", genre_looks="gen_bodycam_precinct", viral_looks="vir_imperfect_handheld"),
        _rec("rec_fpv_dive", "FPV dive hook", framing_shot_size="size_ews", camera_angles="ang_drone_oblique", camera_movement="move_fpv_dive", lenses_optics="opt_fisheye", composition="cmp_center_punch", lighting="lit_hard_noon", color_film_look="col_color_neg_warm", time_motion="tim_realtime", viral_looks="vir_fpv_dive_mark"),
        _rec("rec_drone_hero", "Drone-hero reveal", framing_shot_size="size_ews", camera_angles="ang_drone_oblique", camera_movement="move_drone_rise", lenses_optics="opt_24_wide", composition="cmp_isolation", lighting="lit_golden_hour", color_film_look="col_color_neg_warm", time_motion="tim_slowmo_40", atmosphere_weather="atm_clear_plaza", viral_looks="vir_drone_hero_slowmo"),
    ]


def _all_technique_ids() -> set[str]:
    known: set[str] = set()
    for path in OUT.glob("*.json"):
        if path.name in {"axes.json", "recipes.json"}:
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            continue
        for row in raw:
            if isinstance(row, dict):
                tid = str(row.get("id") or "").strip()
                if tid:
                    known.add(tid)
    return known


def _validate_recipes(rows: list[dict[str, Any]], known: set[str]) -> None:
    seen: set[str] = set()
    for row in rows:
        rid = str(row.get("id") or "").strip()
        if not _ID_RE.fullmatch(rid):
            raise SystemExit(f"bad recipe id {rid}")
        if rid in seen:
            raise SystemExit(f"dup recipe {rid}")
        seen.add(rid)
        axes = row.get("axes") or {}
        if not isinstance(axes, dict) or not axes:
            raise SystemExit(f"{rid} needs axes")
        for axis_id, tid in axes.items():
            if tid not in known:
                raise SystemExit(f"{rid} unknown technique {tid} on {axis_id}")


def _dump_recipes(ours: list[dict[str, Any]]) -> None:
    path = OUT / "recipes.json"
    by_id: dict[str, dict[str, Any]] = {}
    if path.is_file():
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            for row in raw:
                if not isinstance(row, dict):
                    continue
                rid = str(row.get("id") or "").strip()
                if rid:
                    by_id[rid] = row
    for row in ours:
        by_id[str(row["id"])] = row
    rows = list(by_id.values())
    known = _all_technique_ids()
    _validate_recipes(rows, known)
    path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({len(rows)})")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    atm = atmosphere_weather()
    gen = genre_looks()
    vir = viral_looks()
    rec = recipes()
    _validate("atmosphere_weather", atm, "atm_", need_still=False, need_audio=True)
    _validate("genre_looks", gen, "gen_", need_still=False, need_audio=False)
    _validate("viral_looks", vir, "vir_", need_still=True, need_audio=False)
    _dump("atmosphere_weather.json", atm)
    _dump("genre_looks.json", gen)
    _dump("viral_looks.json", vir)
    _dump_recipes(rec)


if __name__ == "__main__":
    main()



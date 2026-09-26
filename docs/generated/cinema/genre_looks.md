---
title: Genre Looks
description: Cinema Rack catalog - Genre Looks (230 spliceable techniques).
tags: [cinema, prompting, catalog]
---

# Genre Looks

**What's on this page**

- 230 spliceable techniques for **Genre Looks**
- Still mode `clause`; I2V include `False`
- 0 muted 5s illustration clips shipped
- Ids for the Cinema Rack combo (pick one per axis)

**What this enables**

- Picking a professional cinematography clause instead of guessing camera language
- Opening a technique page to watch a 5s example when the clip is shipped
- Seeing conflicts, still/motion/AV flags, and the Wan token when present

Do not hand-edit this file. Re-run `python3 docs/generate_cinema_docs.py`.
Operator playbook: [Cinema Rack](../../create/cinema-rack.md).

| Id | Label | Example | Clause | Use on | Conflicts |
| --- | --- | --- | --- | --- | --- |
| `gen_noir_venetian` | Noir venetian office | - | Stripe a detective office with venetian-slat sun, cigarette-era dust hanging in the bars, oak desk and a slow ceiling fan, the room tobacco... | still, motion, av | gen_screwball_highkey, gen_romcom_bounce |
| `gen_neo_noir_wet` | Neo-noir wet street | - | Gloss a rain-slick downtown canyon with shop-window tungsten, asphalt specularity, wet fire-escape iron, masonry walls making a black river... | still, motion, av | gen_solarpunk_glasshouse |
| `gen_western_dust_noon` | Western dust noon | - | Bake a false-front street in vertical noon, alkali dust hanging, hitching rails throwing knife shadows, clapboard texture raw. | still, motion, av | gen_snowbound_cabin |
| `gen_western_grit_close` | Western grit close | - | Rake sidelight across a close face so alkali grit sits in pores and hat-felt, a porch post as bokeh, sweat catching in stubble. | still, motion, av | - |
| `gen_screwball_highkey` | Screwball day interior | - | Flood a day interior with high-key bounce, silk robe texture, art-deco moldings, overlapping bodies in a bright parlor, shadows almost gone. | still, motion, av | gen_noir_venetian, gen_horror_hallway_under |
| `gen_melodrama_window` | Melodrama window | - | Place a figure in a tall window of a melodrama house, net-curtain texture, weather as emotion on the pane, the room falling away, the face ... | still, motion, av | - |
| `gen_gothic_candle_nave` | Gothic candle nave | - | Model a stone corridor with candle clusters, soot texture on plaster, dripping wax, the space a nave of moving gold and deep black. | still, motion, av | - |
| `gen_slasher_fridge_practical` | Slasher night practical | - | Underexpose a night house so a fridge practical or TV is the only key, linoleum texture, hallway depth, the dark as a solid extra. | still, motion, av | gen_romcom_bounce |
| `gen_found_footage_led` | Found-footage LED shake | - | Shake a night hallway with on-camera LED, wallpaper texture swimming, doorframes tilting, the wide lens making the corridor a tunnel. | still, motion, av | - |
| `gen_bodycam_precinct` | Body-cam precinct | - | Ride a chest-cam through a precinct corridor, fluorescent smear, uniform fabric along the bottom, radios and door-glass, the space always s... | still, motion, av | - |
| `gen_heist_warehouse` | Heist cool tungsten | - | Cool the tungsten of a night warehouse so faces go a little green-gold, crate wood texture, skylight moon as a rim, the space a grid of ais... | still, motion, av | - |
| `gen_romcom_bounce` | Rom-com bounce beauty | - | Bounce a beauty key off a white wall in a day interior, skin smooth, a messy apartment cheerful, catchlights round, the space warm and clos... | still, motion, av | gen_horror_hallway_under, gen_noir_venetian |
| `gen_period_candle_day` | Period candle and daylight | - | Mix window daylight with practical candles in a period room, linen texture, plaster walls, the two sources fighting on a face, no electric ... | still, motion, av | - |
| `gen_kitchen_sink_overcast` | Kitchen-sink overcast | - | Hold a kitchen-sink interior under overcast window, chipped enamel texture, laundry on chairs, the room small and true, no beauty fill. | still, motion, av | gen_musical_cyc |
| `gen_social_realist_stair` | Social-realist available stair | - | Light a public stairwell with whatever the window gives, scuffed paint texture, the space unstyled, faces as found. | still, motion, av | - |
| `gen_prestige_shallow` | Prestige shallow complementary | - | Grade a shallow-focus interior with complementary shadow-teal and honey-key, wool and wood texture, a window as a soft rectangle, faces sep... | still, motion, av | - |
| `gen_action_sun_haze` | Action sun-backlight haze | - | Backlight a chase street with sun through kicked dust, asphalt grit, vehicles as silhouettes, the space a tunnel of glare. | still, motion, av | - |
| `gen_superhero_comic_key` | Superhero comic key | - | Key a rooftop figure with a comic hard key and a colored rim, cape weave, the city a graphic drop, shadows cut like ink. | still, motion, av | - |
| `gen_musical_cyc` | Musical saturated theatrical | - | Saturate a theatrical stage with colored cyc wash, sequin texture throwing sparks, the proscenium a candy frame, follow-spot as a coin on t... | still, motion, av | gen_kitchen_sink_overcast |
| `gen_horror_hallway_under` | Horror underexposed hallway | - | Underexpose a residential hallway so the far door becomes a weak rectangle, carpet nap swallowing, wallpaper pattern barely drawn, the dark... | still, motion, av | gen_romcom_bounce, gen_screwball_highkey |
| `gen_cosmic_shore_scale` | Cosmic-horror shore scale | - | Dwarf a shoreline figure under a sky that is too large, faint wrong colors in the overcast, wet pebbles, the ocean like a slab, scale that ... | still, motion, av | - |
| `gen_folk_standing_stones` | Folk-horror overcast field | - | Stand a figure in an overcast field of standing stones, wool texture, no sun, the village a gray lip on the horizon, the air still and wron... | still, motion, av | - |
| `gen_thriller_parking_long` | Thriller long-lens surveillance | - | Park a long-lens view across a parking structure, a subject small in one bay, sodium texture, concrete ribs counting, the space observed no... | still, motion, av | - |
| `gen_spy_plaza_tele` | Spy night telephoto | - | Compress a night plaza on a long lens, a figure isolated in a hotel-marquee pool, bokeh of fountain spray, surveillance distance, heat ripp... | still, motion, av | - |
| `gen_war_trench_dust` | War handheld dust | - | Handheld a trench lip in dusty noon, grit on the lens, uniform weave, the space a ditch with a slice of blown sky. | still, motion, av | - |
| `gen_submarine_red` | Submarine red practical | - | Bathe a submarine compartment in red battle practicals, pipe-lagging texture, gauges catching, the bunk space cramped and sweating. | still, motion, av | - |
| `gen_spacecraft_led_ribs` | Spacecraft practical LED | - | Key a spacecraft cabin with practical LED strips along the ribs, velcro texture, cable bundles, a small window of black, dust floating in t... | still, motion, av | - |
| `gen_cyberpunk_wet_neon` | Cyberpunk wet neon | - | Flood a rain-wet alley with competing neon-magenta shop, cyan crosswalk-so puddles become stained glass, steam texture, fire-escapes as bla... | still, motion, av | gen_solarpunk_glasshouse |
| `gen_solarpunk_glasshouse` | Solarpunk clear sun | - | Wash a glasshouse street in clear sun, vine texture on solar-louvers, clean water channels, the space open and photosynthetic, no haze of i... | still, motion, av | gen_cyberpunk_wet_neon, gen_neo_noir_wet |
| `gen_rural_raking_farm` | Rural raking Americana | - | Rake late sun across a farm porch, peeling paint texture, a screen door, fields as gold bands, the space honest and long-shadowed. | still, motion, av | - |
| `gen_coastal_magic_hour` | Coastal magic-hour | - | Gild a coastal cliff house at magic hour, salt-weathered wood texture, windows taking the disk, the ocean a hammered sheet below. | still, motion, av | - |
| `gen_mountain_sublime` | Mountain sublime wide | - | Hold a tiny figure against a mountain wall in clear air, granite texture, weather a small cloud on the peak, the space sublime and uncomfor... | still, motion, av | - |
| `gen_sports_long_iso` | Sports long-lens isolation | - | Isolate a runner in compressed stands on a long lens, sweat texture, crowd as a smear of color, the track space flattened to a ribbon. | still, motion, av | - |
| `gen_fashion_hard_beauty` | Fashion hard beauty | - | Punch a hard beauty key with a silver bounce, skin pore-true, a cyclorama or loft brick, fashion space emptied of clutter, shadow edge knif... | still, motion, av | - |
| `gen_music_video_smear` | Music-video smear shutter | - | Smear a night performance with a long shutter, LED wash dragging, sequin and sweat streaks, the club volume becoming ribbons of color. | still, motion, av | - |
| `gen_product_wrap` | Commercial product wrap | - | Wrap a tabletop hero in seamless white bounce, product material microdetail, a horizon of infinity paper, speculars walking in a controlled... | still, motion, av | - |
| `gen_doc_available_street` | Documentary available street | - | Take available street light as found, coat-wool and brick texture, unposed timing, the sidewalk space unstyled and present-tense. | still, motion, av | - |
| `gen_verite_bounce_room` | Verite bounce room | - | Bounce a small fixture off a ceiling in a lived room, carpet stain texture, overlapping talk, the space a real apartment not a set. | still, motion, av | - |
| `gen_observational_lockoff` | Observational locked-off | - | Lock off on a doorway in mixed available, scuff texture on the jamb, people entering and leaving a room that does not perform. | still, motion, av | - |
| `gen_giallo_stair_gel` | Giallo color-gel night | - | Gel a stairwell night in acid green and wine red, patent-leather reflections, terrazzo floors, a gloved hand on a banister, the space a can... | still, motion, av | - |
| `gen_gothic_romance_mist` | Gothic romance mist | - | Veil a manor lawn in mist with window gold leaking, wet wool and iron-gate texture, the house a dark block, two figures small in weather. | still, motion, av | - |
| `gen_caper_night_cool` | Caper cool night | - | Cool a night rooftop with distant neon bounce, gravel texture, a skyline as a diagram, faces in a pool of a work lamp, the space playful an... | still, motion, av | - |
| `gen_courtroom_fluorescent` | Courtroom available fluorescent | - | Light a courtroom with tired fluorescents and high windows, wood-panel texture, dust in the shafts, the space civic and unflattering. | still, motion, av | - |
| `gen_hospital_green` | Hospital green practical | - | Tint a hospital corridor with green-practical fluorescents, linoleum shine, curtain texture, the space endless and humming. | still, motion, av | - |
| `gen_school_day_bounce` | School-day bounce | - | Bounce day through classroom windows onto scuffed desks, chalk-dust texture, construction-paper color, the space ordinary and loud with sun. | still, motion, av | - |
| `gen_beach_hard_sun` | Beach-day hard sun | - | Blast beach noon with overhead sun, salt-skin texture, umbrellas as hard disks of shade, the sand space overexposed and glittering. | still, motion, av | - |
| `gen_club_strobe_fog` | Night-club strobe fog | - | Strobe a night club so dancers freeze in white shards between darkness, fog texture catching each pop, a low ceiling of truss, faces unread... | still, motion, av | - |
| `gen_rain_noir_alley` | Rain-noir alley | - | Key a rain alley with a single fire-escape practical, brick running with water, dumpster metal, the space a wet slot of threat and specular... | still, motion, av | - |
| `gen_desert_western_magic` | Desert western magic hour | - | Gild a desert western street at magic hour, adobe texture, long blue shadows, dust as gold, the false-fronts turning copper. | still, motion, av | - |
| `gen_snowbound_cabin` | Snow-bound isolation | - | Hold a cabin window as the only warm rectangle in a snow field, frost-on-glass texture, the interior small, the exterior a white infinity. | still, motion, av | gen_western_dust_noon |
| `gen_jungle_leaf_vault` | Jungle wet leaf-vault | - | Dapple wet jungle understory with broken sun through a leaf-vault, bark slick, vines as ropes, steam in the shafts, the path a tunnel of gr... | still, motion, av | gen_arctic_whiteout |
| `gen_arctic_whiteout` | Arctic white-out | - | Erase scale in an arctic white-out, a figure as a dark comma, no horizon, parka texture the only grain, glow coming from everywhere and now... | still, motion, av | gen_jungle_leaf_vault |
| `gen_interrogation_bulb` | Noir interrogation bulb | - | Hang a single bare bulb over a metal table, the rest of the box in falloff, sweat sheen, a one-way glass suggestion as a dark rectangle. | still, motion, av | - |
| `gen_boxing_overhead` | Boxing-ring overhead | - | Drop an overhead ring key so sweat and resin texture shine, ropes as lines, the crowd a dark bowl, the canvas space a bright island. | still, motion, av | - |
| `gen_diner_night_fluoro` | Diner night fluorescent | - | Wash a night diner in cool fluorescent, laminate texture, pie case glow, rain on the glass, the booth space a lit aquarium on a dark street. | still, motion, av | - |
| `gen_motel_neon_vacancy` | Motel neon vacancy | - | Key a motel facade with vacancy neon, pebble-dash texture, a pool of pink on wet concrete, the courtyard space empty and humming. | still, motion, av | - |
| `gen_gas_station_night` | Gas-station night | - | Island a night forecourt under a bright fluorescent soffit, oil-stain texture, pumps as totems, desert dark beyond the lot. | still, motion, av | - |
| `gen_carnival_tungsten` | Carnival tungsten | - | Warm a carnival midway with tungsten bulb strings, painted-wood texture, fried-sugar air implied, the space a tunnel of rides and sawdust. | still, motion, av | - |
| `gen_church_nave_shafts` | Church nave god-rays | - | Drop dust-shafts from clerestory windows down a nave, pew-wood texture, stone floors, the space a long hush of gold and shadow. | still, motion, av | - |
| `gen_victorian_gaslight` | Victorian parlor gaslight | - | Model a Victorian parlor with gaslight practicals, velvet and walnut texture, wallpaper dense, the space cluttered and amber. | still, motion, av | - |
| `gen_silent_era_highkey` | Silent-era high-key | - | Flood a silent-era interior in high-key daylight, greasepaint texture, painted flats, the space theatrical and shadowless except for eyes. | still, motion, av | - |
| `gen_expressionist_paint` | Expressionist painted shadow | - | Paint shadows as architecture on studio walls, jagged texture, a staircase that is also a graphic, the space a mind not a room. | still, motion, av | - |
| `gen_new_wave_street` | New-wave street available | - | Grab available street bounce on a cafe terrace, jumper-knit texture, handheld edges, the boulevard space casual and present. | still, motion, av | - |
| `gen_teen_string_lights` | Teen bedroom string-lights | - | Key a teen bedroom with string-lights and a desk lamp, poster texture, unmade bed, the space a cave of small practicals. | still, motion, av | - |
| `gen_road_windshield` | Road-movie windshield | - | Look through a windshield at traveling weather, dash texture, bugs on glass, the cabin space a moving interior against a rushing land. | still, motion, av | - |
| `gen_library_dust_shaft` | Library dust shaft | - | Drop a sun shaft through library stacks, paper and leather texture, motes solid, the aisle space a gold tunnel of spines. | still, motion, av | - |
| `gen_gallery_white_cube` | Gallery white cube | - | Even a white-cube gallery with skylight bounce, painted-wall texture, a single work, the space emptied to a hush of edges. | still, motion, av | - |
| `gen_loft_industrial` | Loft industrial window | - | Rake industrial windows across a loft, brick and iron texture, dust in the beams, the floor space a factory becoming a home. | still, motion, av | - |
| `gen_penthouse_city_night` | Penthouse city night | - | Mix city-night bounce with interior practicals in a penthouse, glass texture, a skyline as wallpaper, the space expensive and thin. | still, motion, av | - |
| `gen_bunker_concrete` | Bunker concrete practical | - | Key a bunker with a single cage practical, concrete texture, pipes sweating, the space a buried box. | still, motion, av | - |
| `gen_lab_clean_fluoro` | Lab clean fluorescent | - | Wash a laboratory in even fluorescents, stainless and tile texture, the bench space sterile, reflections of overheads in glassware. | still, motion, av | - |
| `gen_newsroom_desks` | Newsroom desk lamps | - | Pool newsroom desks in practical lamps under a dark ceiling, paper texture, monitor glow, the space a field of small gold islands. | still, motion, av | - |
| `gen_trench_flare_night` | Trench night flare | - | Light a night trench with a falling flare, mud texture, faces going white then red, the ditch space a brief terrible stage. | still, motion, av | - |
| `gen_lighthouse_storm` | Lighthouse storm | - | Sweep a lighthouse beam through storm rain, wet stone texture, a gallery railing, the space a tower in a grinding sea. | still, motion, av | - |
| `gen_fishing_wheelhouse` | Fishing-boat wheelhouse | - | Key a wheelhouse with instrument glow and gray sea windows, wet wool texture, condensation, the cabin space pitching. | still, motion, av | - |
| `gen_train_compartment` | Train-compartment window | - | Mix compartment tungsten with traveling window daylight, upholstery texture, a table of paper, the space a moving room of blinds. | still, motion, av | - |
| `gen_subway_car_fluoro` | Subway-car fluorescent | - | Wash a subway car in sick fluorescent, ad-panel texture, poles and straps, the car space a tube of faces and smear windows. | still, motion, av | - |
| `gen_parking_sodium` | Parking-garage sodium | - | Stain a parking garage in sodium orange, concrete texture, columns marching, the ramp space a spiral of ugly gold. | still, motion, av | - |
| `gen_fire_escape_night` | Fire-escape night | - | Key a fire-escape two-shot with a kitchen window practical, rust texture, brick close, the city a drop beyond the rails. | still, motion, av | - |
| `gen_barn_loft_gold` | Barn loft gold shaft | - | Drop a gold shaft through barn boards, hay texture, motes thick, the loft space a cathedral of dust and tack. | still, motion, av | - |
| `gen_ice_rink_overhead` | Ice-rink overhead | - | Blast an ice rink with overhead sports keys, ice-scratch texture, breath vapor, the rink space a white rectangle in a dark bowl. | still, motion, av | - |
| `gen_haunted_flashlight` | Haunted-house flashlight | - | Carve a decaying interior with a flashlight beam, peeling wallpaper texture, the beam a moving tunnel, the rest of the house withheld. | still, motion, av | - |
| `gen_crypt_torch` | Crypt torch | - | Flicker torchlight on crypt stone, bone-niche texture, smoke staining the vault, the space a low rib of dark. | still, motion, av | - |
| `gen_forge_dark_fantasy` | Dark-fantasy forge | - | Key a forge with molten orange, soot and leather texture, hammer scale, the hall space a cave of heat and iron. | still, motion, av | - |
| `gen_throne_high_fantasy` | High-fantasy throne | - | Shaft colored glass onto a throne hall, banner texture, stone flags, the space a long approach of light bars and hush. | still, motion, av | - |
| `gen_space_opera_bridge` | Space-opera bridge | - | Key a command bridge with console glow and a giant window of stars, metal-grille texture, the space a dark theater facing cosmos. | still, motion, av | - |
| `gen_rooftop_chase_sodium` | Rooftop-chase sodium | - | Chase a rooftop in mixed sodium and billboard RGB, tar texture, HVAC obstacles, the skyline space a maze of drops. | still, motion, av | - |
| `gen_tunnel_chase` | Car-chase tunnel | - | Strobe a tunnel chase with passing fixtures, wet-tile texture, taillights as streaks, the tube space a rhythmic pulse. | still, motion, av | - |
| `gen_embassy_night` | Embassy night | - | Hold an embassy night exterior in security floods, limestone texture, flags limp, the grounds space empty and watched. | still, motion, av | - |
| `gen_safehouse_blinds` | Safehouse blinds | - | Stripe a safehouse apartment with closed-blind sun, cheap carpet texture, a table of kit, the room space tense and ordinary. | still, motion, av | - |
| `gen_school_gym_bounce` | School-gym bounce | - | Bounce gym-window sun off varnished wood, sneaker-scuff texture, bleachers empty, the court space echoing and large. | still, motion, av | - |
| `gen_ski_lodge_fire` | Ski-lodge fire | - | Key a ski lodge with fireplace gold against window blue, wool and pine texture, snow outside, the room space a warm cave. | still, motion, av | - |
| `gen_opera_footlights` | Opera footlights | - | Throw footlights up into painted faces, velvet-curtain texture, the pit a dark gulf, the stage space a gold proscenium box. | still, motion, av | - |
| `gen_jazz_club_red` | Jazz-club red practical | - | Bathe a jazz club in red practicals, brass and smoke texture, tiny tables, the bandstand space a glow in a cave. | still, motion, av | - |
| `gen_poker_low_lamp` | Poker-room low lamp | - | Drop a green-shade lamp on a felt table, card and chip texture, faces in the pool, the room beyond a dark suggestion. | still, motion, av | - |
| `gen_war_room_map` | War-room map light | - | Key a war-room table with a map lamp, paper and ashtray texture, the walls a ring of officers, the space a bunker of plans. | still, motion, av | - |
| `gen_cockpit_glow` | Cockpit glow | - | Key a night cockpit with instrument wash, leather-seat texture, rain on the windshield, the cabin space a tiny green cave. | still, motion, av | - |
| `gen_cargo_hold` | Cargo-hold practical | - | Light a cargo hold with cage practicals, crate stencil texture, chain, the hold space a ribbed belly of a ship. | still, motion, av | - |
| `gen_stoop_golden` | Stoop golden hour | - | Rake golden hour up a brownstone stoop, stoop-stone texture, a screen door, the street space neighborly and long-shadowed. | still, motion, av | - |
| `gen_porch_moth_bulb` | Porch moth bulb | - | Hang a bare porch bulb in humidity, moth texture in the glow, screen-door mesh, the yard space a black surround. | still, motion, av | - |
| `gen_orchard_raking` | Orchard raking sun | - | Rake late sun down an orchard aisle, bark and fruit texture, dust as gold, the row space a repeating tunnel. | still, motion, av | - |
| `gen_rodeo_hard_sun` | Rodeo hard sun | - | Blast a rodeo arena with overhead sun, dirt-kick texture, chute wood, the oval space a bright dust bowl. | still, motion, av | - |
| `gen_samurai_courtyard` | Samurai courtyard raking | - | Rake morning sun across a raked-gravel courtyard, wood-grain and paper-door texture, the space a rectangle of discipline and shadow. | still, motion, av | - |
| `gen_wuxia_mist_ridge` | Wuxia mist ridge | - | Veil a mountain ridge in wuxia mist, silk and pine texture, a bridge as a thread, the space floating and vertical. | still, motion, av | - |
| `gen_dojo_sidelight` | Dojo sidelight | - | Side-light a dojo so floorboards gleam, gi-cotton texture, a wall of weapons as geometry, the hall space spare and echoing. | still, motion, av | - |
| `gen_prison_yard_sun` | Prison-yard hard sun | - | Blast a prison yard with overhead sun, concrete texture, chain-link shadow as a grid on faces, the yard space a pan of glare. | still, motion, av | - |
| `gen_cell_slit_window` | Prison-cell slit window | - | Key a cell from a high slit window, painted-steel texture, a toilet and bunk, the space a vertical box of falloff. | still, motion, av | - |
| `gen_regency_chandelier` | Regency ballroom chandelier | - | Drop chandelier diamonds over a ballroom, silk and marble texture, candle-equivalents in glass, the floor space a mirror of movement. | still, motion, av | - |
| `gen_ballet_ghost_light` | Ballet rehearsal ghost light | - | Hold a rehearsal hall with a single ghost light on scuffed marley, chalk texture, the studio space empty and honest. | still, motion, av | - |
| `gen_casino_overhead` | Casino overhead wash | - | Wash a casino floor in even overheads, carpet-pattern texture, no clocks, the space a maze of tables and glow. | still, motion, av | - |
| `gen_morgue_cold` | Morgue cold green | - | Tint a morgue in cold green practicals, steel-drawer texture, tile shine, the room space refrigerated and still. | still, motion, av | - |
| `gen_hydroponic_ship` | Colony-ship hydroponic | - | Key a hydroponic bay with grow-LED magenta-green, leaf and pipe texture, the bay space a garden in a hull. | still, motion, av | - |
| `gen_android_lab` | Android-lab clean | - | Even an android lab in clean bounce, polymer-skin texture, tools on trays, the space white and watchful. | still, motion, av | - |
| `gen_billboard_apt` | Billboard-lit apartment | - | Flood an apartment with billboard RGB through cheap blinds, laminate texture, the room space stained by advertising color. | still, motion, av | - |
| `gen_grain_elevator_noon` | Grain-elevator noon | - | Bake a grain elevator in noon sun, corrugated texture, a two-lane, the prairie space empty except for that tower. | still, motion, av | - |
| `gen_swamp_night` | Swamp night methane | - | Key a swamp night with a lantern and bioluminescent suggestion, moss texture, black water, the space a maze of knees and mist. | still, motion, av | - |
| `gen_beach_landing_overcast` | Beach-landing overcast | - | Hold a landing beach under military overcast, wet sand texture, obstacles as silhouettes, the space a gray sheet into surf. | still, motion, av | - |
| `gen_sniper_nest_dusk` | Sniper-nest dusk | - | Compress a dusk city from a nest, brick texture in the foreground, a distant figure small, the space a measured gap of air. | still, motion, av | - |
| `gen_piano_bar_gold` | Piano-bar gold | - | Warm a piano bar with gold practicals, lacquer and ivory texture, bottles as stained glass, the nook space intimate. | still, motion, av | - |
| `gen_meadow_magic_rural` | Meadow magic-hour rural | - | Gild a meadow at magic hour, grass-seed texture, a farmhouse small, the space a bowl of honey air and long shade. | still, motion, av | - |
| `gen_kitchen_table_drama` | Kitchen-table family drama | - | Key a kitchen table with a hanging practical, oilcloth texture, dishes, the room space close enough to hear breath. | still, motion, av | - |
| `gen_campaign_office_night` | Campaign-office night | - | Keep a campaign office alive at night with desk lamps, paper-stack texture, maps, the space a warren of tired fluorescents off. | still, motion, av | - |
| `gen_elevator_tungsten` | Elevator tungsten | - | Box two people in elevator tungsten, brushed-metal texture, a floor-number glow, the space a moving closet of reflections. | still, motion, av | - |
| `gen_airplane_cabin_night` | Airplane cabin night | - | Wash a night cabin in reading-spot coins, seat-fabric texture, oval windows of black, the aisle space a long dim tube. | still, motion, av | - |
| `gen_circus_tent_color` | Circus tent colored | - | Throw colored tent-wash on sawdust, sequin and animal-implied texture, bleachers, the ring space a bright dirt circle. | still, motion, av | - |
| `gen_pulp_paperback_sat` | Pulp paperback saturation | - | Push pulp saturation on a night diner or alley, cheap-print texture, a figure in a loud coat, the space a cover illustration made flesh. | still, motion, av | - |
| `gen_grindhouse_grain` | Grindhouse night grain | - | Grind a night street with coarse grain and sick practicals, sticky-floor implied texture, a marquee, the space cheap and dangerous. | still, motion, av | - |
| `gen_italian_western_cemetery` | Cemetery-western noon | - | Blast a cemetery western in white noon, bleached-wood texture, a boot and a stone, the space a dusty amphitheater of graves. | still, motion, av | - |
| `gen_locker_tungsten` | Sports-locker tungsten | - | Key a locker room in tungsten cages, tile and tape texture, steam, the space a wet rectangle of benches. | still, motion, av | - |
| `gen_detective_blinds_desk` | Detective blinds desk | - | Stripe a desk with failing blinds, coffee-ring texture, a fan, the office space smaller than the noir version, more tired. | still, motion, av | - |
| `gen_precinct_fluorescent` | Police-precinct fluorescent | - | Wash a precinct bullpen in mixed fluorescent, metal-desk texture, wanted-board, the space a noisy grid of tired light. | still, motion, av | - |
| `gen_church_candle_gothic` | Church-candle gothic | - | Multiply votive candles at an altar, wax-drip texture, gold leaf, the chapel space a cave of small fires. | still, motion, av | - |
| `gen_monastery_cloister` | Monastery cloister | - | Side-light a cloister walk with open-arcade sun, stone-wear texture, a garden square, the space a measured circuit of shade. | still, motion, av | - |
| `gen_summer_camp_dusk` | Summer-camp woods dusk | - | Hold dusk in woods around a cabin, pine-needle texture, a bug-zapper glow, the camp space between play and threat. | still, motion, av | - |
| `gen_fairground_night` | Fairground night tungsten | - | String a fairground night with bare bulbs, painted-steel texture, fried-air implied, the midway space a funnel of faces. | still, motion, av | - |
| `gen_news_chopper_search` | Searchlight night ground | - | Stab a searchlight onto a night street from above, wet-asphalt texture, figures as insects, the space a cone of exposure. | still, motion, av | - |
| `gen_embassy_ballroom` | Embassy ballroom mixed | - | Mix chandelier and window dusk in an embassy ballroom, silk texture, flags, the floor space diplomatic and watchful. | still, motion, av | - |
| `gen_radio_bunker_amber` | Radio-bunker amber | - | Amber a radio bunker with bakelite glow, grill-cloth texture, maps, the room space a humming closet of war. | still, motion, av | - |
| `gen_hydro_dam_noon` | Dam noon sublime | - | Hold a dam face in noon sun, concrete-scale texture, a tiny figure, the space industrial sublime. | still, motion, av | - |
| `gen_nursery_window_day` | Nursery window day | - | Diffuse a nursery with sheer-curtain day, cotton texture, a mobile, the room space pale and quiet. | still, motion, av | - |
| `gen_attic_storm_day` | Attic storm day | - | Key an attic from a round window under storm, dust-cloth texture, trunks, the space a memory box of gray-green. | still, motion, av | - |
| `gen_boardwalk_night` | Boardwalk night sodium | - | Mix sodium and ride-color on a boardwalk night, salt-wood texture, a crowd, the pier space a strip into dark water. | still, motion, av | - |
| `gen_observatory_dome` | Observatory dome night | - | Key an observatory interior with console glow and a slit of stars, metal-track texture, the dome space a machine aimed at dark. | still, motion, av | - |
| `gen_greenhouse_overcast` | Greenhouse overcast | - | Fill a greenhouse with overcast bounce, wet-leaf texture, condensation, the nave of glass space humid and even. | still, motion, av | - |
| `gen_subway_platform_sodium` | Subway platform sodium | - | Stain a subway platform in sodium and tube-wind, tile-ad texture, a yellow edge, the platform space a tunnel of wait. | still, motion, av | - |
| `gen_rooftop_billboard_rgb` | Rooftop billboard RGB | - | Paint a rooftop figure with billboard RGB, tar texture, the sign as a monster key, the city space a drop of black. | still, motion, av | - |
| `gen_farmhouse_kitchen_am` | Farmhouse kitchen morning | - | Rake morning through a farmhouse kitchen, enamel and grain-wood texture, steam from a kettle, the room space used and kind. | still, motion, av | - |
| `gen_cathedral_crypt_blue` | Cathedral crypt blue | - | Wash a crypt in cold window-blue, stone-effigy texture, the vault space a hush under the city. | still, motion, av | - |
| `gen_factory_night_shift` | Factory night-shift | - | Key a factory night-shift with mercury-vapor greens, machine-oil texture, the floor space a forest of presses. | still, motion, av | - |
| `gen_motel_bathroom_fluoro` | Motel bathroom fluorescent | - | Blast a motel bathroom in harsh fluorescent, mildew-tile texture, a mirror, the box space unflattering and true. | still, motion, av | - |
| `gen_wedding_bounce_day` | Wedding day bounce | - | Bounce day off a pale wall onto formal clothes, flower texture, a hall, the space ceremonial and kind. | still, motion, av | - |
| `gen_funeral_overcast` | Funeral overcast | - | Hold a graveside under overcast, wool-black texture, umbrellas, the cemetery space a gray bowl. | still, motion, av | - |
| `gen_high_school_hallway` | High-school hallway lockers | - | Stripe a school hallway with locker rows in mixed fluorescent, enamel-dent texture, the corridor space a social tunnel. | still, motion, av | - |
| `gen_pool_hall_over` | Pool-hall overhead | - | Drop shaded lamps over green felt, chalk texture, smoke, the hall space a row of bright tables in dark wood. | still, motion, av | - |
| `gen_aquarium_blue` | Aquarium-blue interior | - | Key an interior with aquarium-blue practicals, glass and water texture, moving caustics, the room space submarine without a hull. | still, motion, av | - |
| `gen_desert_night_stars` | Desert-night camp stars | - | Key a desert camp with fire gold against star-true black, sand texture, a two-lane far, the space huge and cold above the flame. | still, motion, av | - |
| `gen_rain_bus_interior` | Rain-bus interior | - | Mix bus fluorescent with rain-window smear, plastic-seat texture, ads, the aisle space a wet public room. | still, motion, av | - |
| `gen_office_cubicle_day` | Office cubicle daylight | - | Even an open office in daylight fluorescents, fabric-panel texture, monitors, the floor space a maze of beige. | still, motion, av | - |
| `gen_church_basement_coffee` | Church-basement coffee | - | Light a church basement with cheap fluorescents, folding-table texture, coffee, the room space humble and tiled. | still, motion, av | - |
| `gen_rooftop_dawn_city` | Rooftop dawn city | - | Hold a rooftop at city dawn, tar-and-vent texture, the skyline going pink, the space a private deck over a waking grid. | still, motion, av | - |
| `gen_mine_headlamp` | Mine headlamp tunnel | - | Carve a mine tunnel with a headlamp, coal-glitter texture, timber props, the space a throat of dark. | still, motion, av | - |
| `gen_ferry_night_deck` | Ferry night deck | - | Key a ferry deck with work-lamps and city approaching, wet-paint texture, a railing, the space a windy platform on black water. | still, motion, av | - |
| `gen_stadium_night_flood` | Stadium night floods | - | Blast a stadium night with floods, grass texture, the bowl of crowd as a glittering cliff, the pitch space a green table. | still, motion, av | - |
| `gen_convent_cell_day` | Convent-cell day | - | Side-light a convent cell from a small window, plaster texture, a bed and a book, the space a measured poverty of sun. | still, motion, av | - |
| `gen_arcade_neon_night` | Arcade neon night | - | Fill an arcade with cabinet RGB, carpet-pattern texture, the hall space a cave of moving color and no daylight. | still, motion, av | - |
| `gen_courtyard_moon` | Moonlit courtyard | - | Paint a courtyard in moonlight and one window, flagstone texture, a well, the space a silver well of hush. | still, motion, av | - |
| `gen_warehouse_rave_strobe` | Warehouse rave strobe | - | Strobe a warehouse rave in fog, concrete texture, a truss of diodes, the volume space a pulsing industrial nave. | still, motion, av | - |
| `gen_farm_silo_magic` | Farm silo magic hour | - | Gild a silo and a gravel drive at magic hour, rust texture, a pickup, the farm space a hush of gold dust. | still, motion, av | - |
| `gen_bridge_fog_noir` | Bridge fog noir | - | Lose a figure on a fogged bridge in sodium, wet-rail texture, the span space disappearing in both directions. | still, motion, av | - |
| `gen_attic_fairy_gold` | Attic gold slats | - | Stripe an attic with gold slat-sun, trunk-leather texture, motes, the space a memory of summer stored. | still, motion, av | - |
| `gen_dock_night_worklamp` | Dock night work-lamp | - | Key a night dock with a work-lamp, wet-wood texture, ropes, the slip space a stage over black harbor. | still, motion, av | - |
| `gen_green_screen_cyc_empty` | Empty cyc studio | - | Even an empty cyclorama in studio bounce, paint-seam texture, no set, the space a horizon of nothing waiting. | still, motion, av | - |
| `gen_horror_basement_bulb` | Horror basement bulb | - | Hang a swinging bulb in a basement, dirt-floor texture, joists, the space a low threat of moving gold and black. | still, motion, av | - |
| `gen_romance_rain_window` | Romance rain window | - | Key two faces with rain-window bounce, knit texture, a cafe table, the glass space a curtain of weather between them and the street. | still, motion, av | - |
| `gen_western_campfire_faces` | Western campfire faces | - | Key western faces from a campfire below, leather texture, horses as shadows, the desert space a ring of dark. | still, motion, av | - |
| `gen_spy_hotel_corridor` | Spy hotel corridor | - | Hold a hotel corridor in even practicals, patterned-carpet texture, a cart, the space a long measured threat of doors. | still, motion, av | - |
| `gen_doc_kitchen_window` | Documentary kitchen window | - | Use only the kitchen window, dish-rack texture, a kettle, the room space ordinary and unstyled. | still, motion, av | - |
| `gen_action_heli_search` | Helicopter-searchlight night | - | Stab a helicopter searchlight onto a yard, grass texture going white, fences, the space a moving cone of exposure. | still, motion, av | - |
| `gen_prestige_rain_estate` | Prestige rain estate | - | Grade a rain-soaked estate in shallow complementary, wet-gravel texture, a facade, the drive space expensive and miserable. | still, motion, av | - |
| `gen_folk_barn_interior` | Folk-horror barn interior | - | Stripe a barn interior with broken-board sun, straw texture, a figure in the aisle, the space a nave of dust and wrong quiet. | still, motion, av | - |
| `gen_cyber_interior_rgb` | Cyber interior RGB ribs | - | Key an interior with RGB ribs and rain-window neon, polymer texture, the room space a wet cockpit of city color. | still, motion, av | - |
| `gen_solar_market_day` | Solarpunk market day | - | Wash a market street in clear sun, produce and solar-shade texture, water channels, the space civic and green. | still, motion, av | - |
| `gen_snow_train_window` | Snow-bound train window | - | Mix compartment tungsten with blizzard-white windows, frost texture, tea glass, the space a warm tube in a white war. | still, motion, av | - |
| `gen_jungle_night_bugs` | Jungle night bugs | - | Key a jungle night camp with a lantern, leaf-wet texture, a wall of insect glow, the clearing space a small hole in black green. | still, motion, av | - |
| `gen_arctic_hut_window` | Arctic hut window | - | Hold an arctic hut interior against a white window, wool texture, ice on the pane, the room space a yellow box in forever. | still, motion, av | - |
| `gen_noir_rooftop_water` | Noir rooftop water tower | - | Key a noir rooftop with a water-tower silhouette and a distant neon, tar texture, the city space a map of threats below. | still, motion, av | - |
| `gen_melodrama_stair` | Melodrama staircase | - | Place a figure on a curving stair in window drama, runner-carpet texture, a chandelier, the hall space a vertical emotion. | still, motion, av | - |
| `gen_heist_vault_fluoro` | Heist vault fluorescent | - | Wash a vault in cold fluorescent, steel-wheel texture, the room space a round door and a table of work. | still, motion, av | - |
| `gen_musical_rehearsal_day` | Musical rehearsal daylight | - | Flood a rehearsal loft with day, marley texture, a piano, the space work-light honest with leftover sequin. | still, motion, av | - |
| `gen_bodycam_night_street` | Body-cam night street | - | Ride a chest-cam on a night street, sodium smear, uniform fabric, wet asphalt, the space always too close and too wide. | still, motion, av | - |
| `gen_found_car_dash` | Found-footage dash night | - | Shake a dash view at night, wiper texture, rain, a face at the edge, the cabin space a panic of glass and road. | still, motion, av | - |
| `gen_romcom_golden_stoop` | Rom-com golden stoop | - | Bounce golden hour off a stoop onto two faces, brownstone texture, groceries, the street space cheerful and close. | still, motion, av | - |
| `gen_thriller_ferry_long` | Thriller ferry long-lens | - | Compress a ferry deck on a long lens, paint texture, a subject isolated in tourists, the water space a moving trap. | still, motion, av | - |
| `gen_war_tent_surgical` | War tent surgical | - | Key a field-hospital tent with harsh practicals, canvas texture, steel, the space a hurried nave of white and mud. | still, motion, av | - |
| `gen_sub_sonar_blue` | Submarine sonar blue | - | Wash a sonar nook in blue-green CRTs, metal texture, the space a dark ear of the boat. | still, motion, av | - |
| `gen_space_airlock` | Spacecraft airlock practical | - | Key an airlock with strip practicals, warning-stencil texture, a round door, the space a closet between atmospheres. | still, motion, av | - |
| `gen_fashion_daylight_cyc` | Fashion daylight cyc | - | Even a fashion figure on a daylight cyc, fabric-micro texture, no prop, the space a horizon of pale nothing. | still, motion, av | - |
| `gen_music_video_fog_rim` | Music-video fog rim | - | Rim a performer in fog with a colored backlight, sequin texture, the stage space a silhouette factory. | still, motion, av | - |
| `gen_commercial_kitchen_wrap` | Commercial kitchen wrap | - | Wrap food in a kitchen-studio bounce, steam texture, stainless, the pass space appetizing and controlled. | still, motion, av | - |
| `gen_verite_car_night` | Verite car night | - | Bounce dashboard glow onto a talking driver, vinyl texture, passing sodium, the cabin space a confession booth on wheels. | still, motion, av | - |
| `gen_observational_shop` | Observational shop lockoff | - | Lock off on a shop counter in mixed available, laminate texture, hands and goods, the space a small theater of ordinary work. | still, motion, av | - |
| `gen_giallo_hotel_night` | Giallo hotel night | - | Gel a hotel corridor in yellow and teal, patterned-carpet texture, a gloved hand, the space a candy threat of doors. | still, motion, av | - |
| `gen_caper_vault_night` | Caper night street cool | - | Cool a night street for a caper team, wet-brick texture, a van, the space playful geometry of alleys. | still, motion, av | - |
| `gen_court_high_windows` | Courtroom high windows | - | Drop high-window shafts onto a jury box, wood texture, dust, the room space civic and taller than the people. | still, motion, av | - |
| `gen_hospital_or_overhead` | Hospital OR overhead | - | Blast an OR with overhead surgical keys, drape texture, chrome, the table space a white island of concentration. | still, motion, av | - |
| `gen_school_blackboard_day` | School blackboard day | - | Side-light a blackboard classroom with window day, chalk texture, desks, the room space ordinary and dusty-gold. | still, motion, av | - |
| `gen_beach_magic_couple` | Beach magic-hour couple | - | Gild two figures on a beach at magic hour, salt-skin texture, the ocean a sheet, the space romantic and windy. | still, motion, av | - |
| `gen_club_uv_fog` | Night-club UV fog | - | Expose a club in ultraviolet so whites scream, fog texture, teeth and shirts, the space a black light cave between strobes. | still, motion, av | - |
| `gen_western_porch_magic` | Western porch magic hour | - | Gild a western porch at magic hour, rocking-chair texture, a street of false fronts, the space honey and dust. | still, motion, av | - |
| `gen_snow_church_isolation` | Snow church isolation | - | Hold a church as a dark rectangle in a snow field, clapboard texture, one window gold, the space a hymn of isolation. | still, motion, av | - |
| `gen_jungle_river_dapple` | Jungle river dapple | - | Dapple a jungle river with broken sun, wet-log texture, the water a black mirror, the space a tunnel of green and current. | still, motion, av | - |
| `gen_arctic_pack_ice_scale` | Arctic pack-ice scale | - | Dwarf a figure on pack ice under a huge overcast, ice-blue texture, the space a broken white floor into fog. | still, motion, av | - |
| `gen_interrogation_two_bulb` | Two-bulb interrogation | - | Hang two competing bulbs over a table, sweat texture, a metal chair, the box space a geometry of double shadows. | still, motion, av | - |
| `gen_superhero_alley_rim` | Superhero alley rim | - | Rim a figure in an alley with a graphic colored kicker, brick texture, a dumpster, the space a comic panel of urban night. | still, motion, av | - |
| `gen_action_market_haze` | Action market sun-haze | - | Backlight a market chase in sun-haze, stall-cloth texture, spice-dust, the aisle space a tunnel of people and glare. | still, motion, av | - |
| `gen_prestige_library_night` | Prestige library night | - | Grade a library night in shallow complementary, leather texture, a lamp, the stacks space intellectual and lonely. | still, motion, av | - |
| `gen_kitchen_sink_bathroom` | Kitchen-sink bathroom | - | Hold a bathroom in overcast window, peeling-paint texture, laundry, the box space true and unkind. | still, motion, av | - |
| `gen_social_realist_bus` | Social-realist bus interior | - | Use available bus light, coat texture, ads, the aisle space unstyled public life. | still, motion, av | - |
| `gen_period_hearth_day` | Period hearth and daylight | - | Mix hearth gold with a small window in a period cottage, wool texture, plaster, the room space a fight of two centuries of fire and day. | still, motion, av | - |
| `gen_romcom_bookstore` | Rom-com bookstore bounce | - | Bounce window day through a bookstore onto two faces, paper texture, aisles, the space warm and close with spines. | still, motion, av | - |
| `gen_heist_server_blue` | Heist server-room blue | - | Wash a server room in cold blue, grille texture, the aisle space a humming chapel of theft. | still, motion, av | - |
| `gen_found_woods_night` | Found-footage woods night | - | Shake woods at night with on-camera LED, leaf-wet texture, trunks jumping, the path space a panic of green-black. | still, motion, av | - |
| `gen_bodycam_stairwell` | Body-cam stairwell | - | Climb a stairwell as a chest-cam, paint-chip texture, rails, fluorescent smear, the well space a vertical chase. | still, motion, av | - |
| `gen_slasher_wood_practical` | Slasher woods practical | - | Underexpose woods so a cabin window is the only key, leaf texture, the dark as mass, the yard space a threat of withheld detail. | still, motion, av | - |
| `gen_gothic_ruin_moon` | Gothic ruin moonlight | - | Paint a ruin in moonlight, ivy-stone texture, a broken rose window, the nave space open to weather. | still, motion, av | - |
| `gen_melodrama_rain_street` | Melodrama rain street | - | Key a figure in street rain from a shop window, wool texture, the pavement space a river of feeling. | still, motion, av | - |
| `gen_screwball_newsroom` | Screwball newsroom high-key | - | Flood a newsroom in high-key bounce, paper texture, overlapping bodies, the floor space comic and loud with sun. | still, motion, av | - |
| `gen_western_river_noon` | Western river noon | - | Bake a river crossing at noon, water-glitter texture, horses, the ford space a sheet of glare and dust. | still, motion, av | - |
| `gen_neo_noir_apartment` | Neo-noir apartment blinds | - | Stripe a night apartment with neon through blinds, cheap-wood texture, a glass, the room space a wet city entering private air. | still, motion, av | - |
| `gen_noir_diner_counter` | Noir diner counter | - | Key a diner counter with a long fluorescent, laminate texture, a lonely stool, the space a bright strip in a dark street. | still, motion, av | - |

---
title: Lighting
description: Cinema Rack catalog — Lighting (136 spliceable techniques).
tags: [cinema, prompting, catalog]
---

# Lighting

**What's on this page**

- 136 spliceable techniques for **Lighting**
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
| `lit_rembrandt` | Rembrandt | — | Shape a key so a triangle of brightness sits on the shadow cheek and the eye in that well still gleams. | still, motion, av | — |
| `lit_loop` | Loop | — | Place the key to throw a small hook of nose shade onto the opposite cheek, both eyes open. | still, motion, av | — |
| `lit_butterfly` | Butterfly | — | Place a key on the lens axis above the eyes so a butterfly-shaped shade sits under the nose and both cheeks stay open. | still, motion, av | — |
| `lit_paramount` | Paramount | — | Drop a glamour key from slightly above the forehead with a scoop filling the eye sockets so cheekbones gleam and the upper lip wears a thin… | still, motion, av | — |
| `lit_split` | Split | — | Put the key full side-on so one half of the face is lit and the other half falls to black, the nose as a border. | still, motion, av | — |
| `lit_broad` | Broad | — | Key the face-to-lens side so the larger visible cheek is bright and the distant cheek recedes into shade. | still, motion, av | — |
| `lit_short` | Short | — | Key the averted side so the visible cheek is mostly shade and the smaller distant cheek is the bright one. | still, motion, av | — |
| `lit_clamshell` | Clamshell | — | Sandwich the face between an overhead key and a bounce from below so eye bags lift and catchlights sit in both upper and lower lids. | still, motion, av | — |
| `lit_beauty` | Beauty | — | Flood the face with even frontal glamour so texture minimizes, catchlights sit at ten-and-two, and the background stays a clean pale cyc. | still, motion, av | — |
| `lit_high_key` | High-Key | — | Lift almost all shadows so whites stay clean, the room feels bleached and airy, and contrast becomes a whisper. | still, motion, av | lit_silhouette, lit_chiaroscuro, lit_low_key |
| `lit_low_key` | Low-Key | — | Let most of the room fall to black so a small island of brightness carves the face and the rest is withheld. | still, motion, av | lit_high_key, lit_silhouette, lit_chiaroscuro |
| `lit_silhouette` | Silhouette | — | Back the person against a brighter field so the body becomes a cutout and facial features vanish into the shape. | still, motion, av | lit_high_key, lit_chiaroscuro, lit_low_key |
| `lit_semi_sil` | Semi-Silhouette | — | Keep a hair of wrap on the cheek so the cutout body still has a hint of feature, not a pure black shape. | still, motion, av | — |
| `lit_chiaroscuro` | Chiaroscuro | — | Pit a single pool against deep dark so form emerges from black as if carved, midtones scarce. | still, motion, av | lit_high_key, lit_silhouette, lit_low_key |
| `lit_rim` | Rim | — | Run a thin bright outline around the figure so they separate from a dark field without lighting the face. | still, motion, av | — |
| `lit_kicker` | Kicker | — | Throw a raking accent from behind-the-side so the jaw and neck have a stripe of glare. | still, motion, av | — |
| `lit_hair` | Hair Light | — | Place a source above and behind so hair becomes a halo of strands and sparkle, the face still keyed separately. | still, motion, av | — |
| `lit_edge` | Edge | — | Skim an edge along a shoulder or prop so a specular line draws the silhouette without filling the front. | still, motion, av | — |
| `lit_wrap` | Wrap | — | Let the key bend around the cheek so the terminator is gradual and pores stay readable into the shade. | still, motion, av | — |
| `lit_window` | Window | — | Key from a visible window so the pane is the source, falloff marches across the room, and curtains shape the beam. | still, motion, av | — |
| `lit_practical_lamp` | Practical Lamp | — | Motivate the key from a visible lamp so the shade, bulb glow, and a pool on the table are the logic of the face. | still, motion, av | — |
| `lit_neon` | Neon | — | Key or accent from neon tubes so skin picks up saturated contour and the tubes themselves are graphic lines in the pane. | still, motion, av | — |
| `lit_fire` | Fire | — | Key from flame so the face flickers, orange on the closer plane, and shadows jump with the fire. | still, motion, av | — |
| `lit_screen` | Screen | — | Key from an unmarked display so the face is the color of the interface and the room around the glow dies. | still, motion, av | — |
| `lit_street` | Streetlamp | — | Key from a streetlamp so a pool falls from above-the-street, moths in the beam, pavement bright. | still, motion, av | — |
| `lit_moonlight` | Moonlight | — | Top-fill with silver-cyan so crushed blacks hold, roof edges gleam, and skin is porcelain rather than honey. | still, motion, av | lit_golden_hour |
| `lit_overcast_skyfill` | Overcast Sky-Fill | — | Wrap the person in shadowless sky from an overcast dome so there is no sun disk and no attached shade on the ground. | still, motion, av | lit_hard_noon |
| `lit_hard_noon` | Hard Noon | — | Put the sun overhead so noses and chins throw short attached shade, pavement bleaches, and eye sockets go dark. | still, motion, av | lit_overcast_skyfill |
| `lit_golden_hour` | Golden Hour | — | Rake amber sidelight along brick and skin so long shadows stripe the street and highlights go honey. | still, motion, av | lit_moonlight |
| `lit_blue_hour` | Blue Hour | — | Let residual sky cyan be the key while practicals just start to read, the world between sundown and full dark. | still, motion, av | — |
| `lit_tungsten_daylight_mix` | Tungsten-Daylight Mix | — | Mix interior tungsten pools with blue window so skin is two temperatures at once, a lamp winning the cheek and sky winning the wall. | still, motion, av | — |
| `lit_hard` | Hard Light | — | Cast a small-source key so pores cast crisp self-shadows and the nose throws a sharp-edged triangle on the cheek. | still, motion, av | — |
| `lit_soft` | Soft Light | — | Wrap a large source so transitions on the jaw melt and speculars on skin become broad pillows. | still, motion, av | — |
| `lit_book_light` | Book Light | — | Bounce a source into a diffusion frame so the face is wrapped by a second-generation glow with almost no specular bite. | still, motion, av | — |
| `lit_bounce` | Bounce | — | Redirect the key off a wall or card so the source becomes a surface, not a lamp, and shade is open. | still, motion, av | — |
| `lit_diffusion` | Diffusion | — | Put diffusion in the beam so the source size grows, lashes cast gentler shade, and hot spots bloom. | still, motion, av | — |
| `lit_grid` | Grid | — | Fit a grid so spill dies and the beam becomes a controlled oval on the face, walls staying dark. | still, motion, av | — |
| `lit_snoot` | Snoot | — | Snoot the source into a small circle so only an eye or a product highlight exists, the rest falling off. | still, motion, av | — |
| `lit_shaft` | Shaft | — | Cut a shaft through haze so a visible beam is architecture and motes travel inside it. | still, motion, av | — |
| `lit_volumetric` | Volumetric | — | Thicken the air with haze so every beam becomes a volume and the room is carved in light-solid. | still, motion, av | — |
| `lit_blinds_breakup` | Blinds Breakup | — | Let blinds throw bars across face and wall so the person is printed with the window's geometry. | still, motion, av | — |
| `lit_leaf_dapple` | Leaf Dapple | — | Let canopy holes dapple the person with moving coin-spots of sun and leaf-shaped shade. | still, motion, av | — |
| `lit_water_caustics` | Water Caustics | — | Throw water caustics so wriggling bright veins crawl over face, tile, or hull. | still, motion, av | — |
| `lit_warm_key_cool_fill` | Warm Key Cool Fill | — | Key from an amber practical and fill the wells with window cyan so skin is honey on the key side and steel in the shade. | still, motion, av | — |
| `lit_motivated_mix` | Motivated Mix | — | Let every source on the face be justified by a visible lamp, window, or fire so nothing feels added. | still, motion, av | — |
| `lit_cameo` | Cameo | — | Light only the person against a dead-black field so they are a cameo and the room does not exist. | still, motion, av | — |
| `lit_limbo_white` | White Limbo | — | Surround with a seamless bright cyc so the person floats in tone, almost no horizon. | still, motion, av | — |
| `lit_noir_slash` | Noir Slash | — | Slash a barn-door bar across the eyes so the rest of the face is withheld in crime-story dark. | still, motion, av | — |
| `lit_cross_key` | Cross Key | — | Key two people from opposite sides so each is bright on the outer cheek and they share a dark middle. | still, motion, av | — |
| `lit_top` | Top Light | — | Drop the key from directly above so eye sockets hollow, the nose becomes a sundial, and hair becomes a lid of brightness. | still, motion, av | — |
| `lit_underlight` | Underlight | — | Key from below so the brow ridges invert, the face becomes a mask, and ceilings catch the bounce. | still, motion, av | — |
| `lit_three_point` | Three-Point | — | Combine a key, a weaker fill, and a back edge so form, shade, and separation all read at once. | still, motion, av | — |
| `lit_one_point` | One-Point | — | Use a single source only so falloff is honest and the distant wall dies. | still, motion, av | — |
| `lit_back_halo` | Back Halo | — | Let a rear source bloom the hair into a luminous wreath while a whisper of front fill keeps the eyes. | still, motion, av | — |
| `lit_candle` | Candle | — | Key from a candle so the face becomes a small living island, flicker in the eyes, hands close to the flame. | still, motion, av | — |
| `lit_flashlight` | Flashlight | — | Key from a handheld torch so a bouncing disk of brightness hunts the room and the beam becomes a character. | still, motion, av | — |
| `lit_headlights` | Headlights | — | Key from vehicle headlights so the person is blasted from road level, long shadows thrown up a wall. | still, motion, av | — |
| `lit_signage` | Signage Glow | — | Let unmarked signage wash the face in saturated color so letters or shapes of the sign spill onto skin. | still, motion, av | — |
| `lit_fridge` | Fridge Glow | — | Open a fridge so the person is keyed by the cold interior, food silhouettes in the closer plane. | still, motion, av | — |
| `lit_north_window` | North Window | — | Key from a north-facing window so the wrap is even and painterly, open shade without a sun patch. | still, motion, av | — |
| `lit_skylight_well` | Skylight Well | — | Key from a skylight well so a column of brightness hits the floor and faces enter or leave that column. | still, motion, av | — |
| `lit_ceiling_bounce` | Ceiling Bounce | — | Bounce the key off the ceiling so the room becomes a gentle downlight, eye sockets filled, lamps not visible as sources. | still, motion, av | — |
| `lit_wall_bounce` | Wall Bounce | — | Bounce off a side wall so the key arrives as a big vertical surface and one side of the nose is open. | still, motion, av | — |
| `lit_paper_lantern` | Paper Lantern | — | Key from a paper lantern so the source becomes a glowing orb in the pane and the wrap is omnidirectional and kind. | still, motion, av | — |
| `lit_bare_bulb` | Bare Bulb | — | Hang a bare bulb so it becomes a star in the pane, sharp shade, and the socket is part of the furniture. | still, motion, av | — |
| `lit_fresnel_spot` | Fresnel Spot | — | Spot with a fresnel so the beam has a crisp circle, barn-doorable edges, and theatrical falloff on the floor. | still, motion, av | — |
| `lit_projector_beam` | Projector Beam | — | Key from a projector so the face wears the image's color and dust lives in the throw. | still, motion, av | — |
| `lit_lightning` | Lightning | — | Light with a lightning flash so the scene becomes a single white instant, rain frozen, then implied dark. | still, motion, av | — |
| `lit_campfire` | Campfire | — | Circle a campfire so faces are orange islands in woods-dark, sparks rising through the pane. | still, motion, av | — |
| `lit_stove` | Stove | — | Key from a stove or burner so the cook's face is underlit by flame and pots throw copper bounce. | still, motion, av | — |
| `lit_vanity` | Vanity | — | Key from a bathroom vanity ring or strip so the mirror person is evenly frontal and tiles bounce white. | still, motion, av | — |
| `lit_interrogation` | Interrogation | — | Drop a single overhead practical so the table becomes a bright desk, faces sweat in a cone, corners of the room vanish. | still, motion, av | — |
| `lit_storefront` | Storefront Spill | — | Let a storefront spill onto the sidewalk so the person is half in shop-color and half in street dark. | still, motion, av | — |
| `lit_sunset_blinds` | Sunset Blinds | — | Let late sun through blinds so amber bars crawl the wall and the face is sliced by the same geometry. | still, motion, av | — |
| `lit_open_shade` | Open Shade | — | Stand the person in open shade so sky is the key, no sun patch, and color shifts slightly steel without going moonlit. | still, motion, av | — |
| `lit_desert_sun` | Desert Sun | — | Blast from a desert sun so bounce off sand fills from below, contrast is brutal, and squint is part of the face. | still, motion, av | — |
| `lit_forest_gloom` | Forest Gloom | — | Key a dim forest so trunks are dark columns, a clearing is the source, and moss eats bounce. | still, motion, av | — |
| `lit_underwater_blue` | Underwater Blue | — | Key underwater so caustics plus blue fill, the surface a bright lid, skin going cyan. | still, motion, av | — |
| `lit_night_window_ext` | Night Window Exterior | — | Shoot a person inside from outside after dark so the window becomes a diorama of tungsten and the street around it is black. | still, motion, av | — |
| `lit_fluorescent_office` | Fluorescent Office | — | Key from overhead office tubes so skin shifts slightly green-grey, ceiling tiles grid the bounce, and shadows are double. | still, motion, av | — |
| `lit_sodium_street` | Sodium Street | — | Bathe in sodium-vapor amber so the street is monochrome honey and other colors collapse. | still, motion, av | — |
| `lit_rain_wet_bounce` | Rain-Wet Bounce | — | Let wet pavement bounce sources back so faces get a second key from below and highlights streak. | still, motion, av | — |
| `lit_fog_street` | Fog Street | — | Mute sources with fog so each lamp becomes a glowing blob and the person appears as they enter a pool. | still, motion, av | — |
| `lit_smoke_volume` | Smoke Volume | — | Add smoke in layers so a doorway beam becomes a wall of brightness the person has to walk through. | still, motion, av | — |
| `lit_stained_glass` | Stained Glass | — | Key through stained glass so colored geometry paints the floor and the face wears patches of ruby and cobalt. | still, motion, av | — |
| `lit_aquarium` | Aquarium | — | Key from a tank so fish-shadows and a blue-green wash crawl the nearby cheek, the glass a practical. | still, motion, av | — |
| `lit_vending_glow` | Vending Glow | — | Key from a vending machine so the face is the color of the cabinet and rows of unmarked goods are the set. | still, motion, av | — |
| `lit_phone_key` | Phone Screen Key | — | Key from a phone screen so only the eyes and hands exist in a small rectangle of interface glow. | still, motion, av | — |
| `lit_laptop_key` | Laptop Key | — | Key from a laptop so the face is the page color, keyboard dim, and the room around the lid is gone. | still, motion, av | — |
| `lit_tv_flicker` | TV Flicker | — | Key from a television so the face pulses with scene changes and the sofa is an island in the dark. | still, motion, av | — |
| `lit_match_strike` | Match Strike | — | Light with a struck match so for a beat the face becomes a cave painting, then the flame settles in the fingers. | still, motion, av | — |
| `lit_oven` | Oven | — | Key from an open oven so the cook is underlit by the cavity, racks as bars, heat implied in the glow. | still, motion, av | — |
| `lit_silk_overhead` | Silk Overhead | — | Stretch a silk overhead so noon is tamed into a large even source, eyes open, ground shade still present but gentle. | still, motion, av | — |
| `lit_neg_fill` | Negative Fill | — | Flag the fill side with black so the key stays, but the shadow cheek goes to velvet and cheekbone pops. | still, motion, av | — |
| `lit_rim_only` | Rim Only | — | Kill the key and keep only a rim so the person is an outline drawing against dark. | still, motion, av | — |
| `lit_beauty_hair` | Beauty and Hair | — | Combine even frontal beauty with a hair halo so fashion gloss and strand separation both read. | still, motion, av | — |
| `lit_split_kicker` | Split plus Kicker | — | Split the face and add a kicker on the dark side so the withheld cheek has a thin lifeline of edge. | still, motion, av | — |
| `lit_cool_key_warm_fill` | Cool Key Warm Fill | — | Key from a north sky and bounce a tungsten lamp into the shadow cheek so the lit plane is porcelain and the dark plane is candle. | still, motion, av | — |
| `lit_golden_rim_cool_shadow` | Golden Rim Cool Shadow | — | Rim with late-sun gold and let the front fill be blue shade so the outline is honey and the face is steel. | still, motion, av | — |
| `lit_blue_city_mix` | Blue Hour City Mix | — | Mix residual-sky cyan with shop practicals so the person is cyan on top and amber in the storefront spill. | still, motion, av | — |
| `lit_practicals_vs_blue_window` | Practicals vs Blue Window | — | Let table lamps win the faces while a blue window claims the back wall, two worlds in one room. | still, motion, av | — |
| `lit_noon_bounce_fill` | Noon Bounce Fill | — | Keep overhead noon but bounce a card into the eye sockets so the brutal sun stays and the face remains readable. | still, motion, av | — |
| `lit_overcast_practicals` | Overcast plus Practicals | — | Keep overcast sky-fill and add interior lamps so the room is even from the windows and honey from the fixtures. | still, motion, av | — |
| `lit_operating_room` | Operating Room | — | Flood from multiple overhead surgical sources so there are no hiding places, skin is clinical, steel specular. | still, motion, av | — |
| `lit_disco_breakup` | Mirror-Ball Breakup | — | Break the room with a mirror-ball so coins of light crawl walls and the dancer is spotted by moving dots. | still, motion, av | — |
| `lit_snow_bounce` | Snow Bounce | — | Let snow on the ground bounce sky back into faces so the undersides of brows are filled and the world is bright from below. | still, motion, av | — |
| `lit_hard_doorway_sun` | Doorway Sun | — | Let sun through a doorway so a rectangle of brightness becomes a solid on the floor and a person stepping through is ignited. | still, motion, av | — |
| `lit_skimming_side` | Skimming Side | — | Skim the key along the wall so texture of brick or plaster rakes and the person is half in that rake. | still, motion, av | — |
| `lit_beauty_fill_below` | Beauty Fill Below | — | Add a bounce just for beauty so eyelashes throw tiny shade upward and the under-eye is cleaned. | still, motion, av | — |
| `lit_hair_and_edge` | Hair and Edge | — | Combine a hair halo with a shoulder edge so the whole outline is separated without lighting the shirt front. | still, motion, av | — |
| `lit_motivated_table_lamp` | Table-Lamp Key | — | Plant the key in a table lamp next to the person so the shade pattern prints on the wall and the closer cheek is the hot side. | still, motion, av | — |
| `lit_motivated_fireplace` | Fireplace Key | — | Key from a fireplace so the hearth is the source, faces orange toward it, backs going to room-dark. | still, motion, av | — |
| `lit_motivated_store` | Store Interior | — | Key from store-aisle overheads so rows of goods are the practicals and the person is shopper-lit, fluorescent and even. | still, motion, av | — |
| `lit_moon_through_trees` | Moon Through Trees | — | Let moonlight through trees so silver dapple moves on the face and the woods stay a black lace. | still, motion, av | — |
| `lit_overcast_beach` | Overcast Beach | — | Fill from overcast beach so sand becomes a giant bounce, sky is the key, and there is almost no eye-socket dark. | still, motion, av | — |
| `lit_industrial_mix` | Industrial Mix | — | Mix greenish industrial tubes with a tungsten work lamp so the shed is two chemical colors. | still, motion, av | — |
| `lit_bathroom_mirror` | Bathroom Mirror | — | Key from a mirrored bathroom so the person is doubled, tiles specular, and the source is the vanity in the glass. | still, motion, av | — |
| `lit_car_interior_night` | Car Interior Night | — | Key a car interior after dark from dash glow and passing street pools so faces pulse as lamps go by. | still, motion, av | — |
| `lit_tent_diffusion` | Tent Diffusion | — | Surround with a diffusion tent so product or face is wrapped one-hundred-eighty degrees, speculars huge and polite. | still, motion, av | — |
| `lit_flagged_face` | Flagged Face | — | Flag the key so a barn-door or flag cuts the chest and only the face wears the beam. | still, motion, av | — |
| `lit_checkerboard_shadow` | Checkerboard Shadow | — | Throw a lattice or grate shadow so the body becomes a checkerboard of brightness and withheld squares. | still, motion, av | — |
| `lit_lace_curtain_breakup` | Lace Curtain | — | Let lace curtains print floral shade on the face so the window's fabric becomes a tattoo of light. | still, motion, av | — |
| `lit_water_reflection_up` | Water Bounce Up | — | Bounce a source off water so the ceiling and jaw get moving bright veins from below. | still, motion, av | — |
| `lit_amber_practical_pool` | Amber Practical Pool | — | Sit the person in a pool from an amber practical so they can step in or out of being lit, the rest of the room dead. | still, motion, av | — |
| `lit_cyan_moon_edge` | Cyan Moon Edge | — | Put a cyan moon-edge on the profile so the outline is ice and the front of the face is almost unlit. | still, motion, av | — |
| `lit_dual_color_split` | Dual-Color Split | — | Split the face not only in brightness but in color, one cheek amber, the other cyan, the nose the border. | still, motion, av | — |
| `lit_white_cyc_highkey` | White Cyc High-Key | — | Flood a white cyc so the person is almost shadowless, fashion-catalog bright, seams of clothes still readable. | still, motion, av | — |
| `lit_black_limbo_lowkey` | Black Limbo | — | Drop the surround to black so the person becomes a sculpted island, no set, only form. | still, motion, av | — |
| `lit_rain_window_key` | Rain Window Key | — | Key from a rain-streaked window so the face wears moving rivulets of brightness and the pane is the source. | still, motion, av | — |
| `lit_welding_flash` | Welding Flash | — | Light with a welding flash so for a frame the shed is white, then the afterimage lives in the dark. | still, motion, av | — |
| `lit_headlamp_miner` | Headlamp | — | Key from a forehead lamp so the beam looks where the person looks, a disk of brightness on the task. | still, motion, av | — |
| `lit_porch_bug` | Porch Light | — | Key from a porch fixture so insects crowd the source, the face entering a yellow-white pool at the door. | still, motion, av | — |
| `lit_candle_multi` | Multi-Candle | — | Key from many candles so the table becomes a constellation of small sources, faces stitched from several directions. | still, motion, av | — |
| `lit_venetian_bars` | Venetian Bars | — | Throw venetian slat-bars across a torso so the body becomes a musical staff of brightness, not a full window print on the wall. | still, motion, av | — |
| `lit_bounce_card_fill` | Bounce-Card Fill | — | Hold a white card just out of pane so the shadow cheek opens a stop without adding a second lamp in the set. | still, motion, av | — |
| `lit_black_wrap` | Black Wrap | — | Wrap black around the key so spill dies on the walls and the face becomes a controlled island in a dark room. | still, motion, av | — |

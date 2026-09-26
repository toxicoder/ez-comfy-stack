---
title: Time and Motion
description: Cinema Rack catalog - Time and Motion (133 spliceable techniques).
tags: [cinema, prompting, catalog]
---

# Time and Motion

**What's on this page**

- 133 spliceable techniques for **Time and Motion**
- Still mode `freeze`; I2V include `True`
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
| `tim_shutter_180` | 180 Shutter Natural | - | Shoot with a 180-degree shutter so strides and rain-needles read as natural cinema cadence. | still, motion, av | - |
| `tim_shutter_45` | 45 Shutter Staccato | - | Chop the shutter to a 45-degree angle so fists become staccato chips and splashes sit like glass beads. | still, motion, av | tim_shutter_180, tim_shutter_360 |
| `tim_shutter_360` | 360 Shutter Smear | - | Open the shutter toward a 360-degree smear so arms taffy across the plate while lamps stay readable cores. | still, motion, av | tim_shutter_45 |
| `tim_long_exposure_still` | Long Exposure Still | - | Expose for many seconds on a locked tripod so pedestrians ghost and window lamps burn as solid bricks. | still, motion, av | - |
| `tim_drag_shutter_night` | Dragging Shutter Night | - | Drag the shutter through nocturnal traffic so headlights paint ribbons and neon worms along the boulevard. | still, motion, av | - |
| `tim_realtime` | Real Time | - | Play the scene in unwarped real time with a metronome gait and no speed change at all. | still, motion, av | tim_dream_slow, tim_panic_fast |
| `tim_slowmo_40` | Theatrical Linger | - | Let a waltz hang at a theatrical linger so skirts bloom like underwater bells around the dancers. | still, motion, av | - |
| `tim_slowmo_48` | Dreamy Sports Cadence | - | Stretch a jump at a dreamy sports cadence so turf pellets hover around the athlete's shoes. | still, motion, av | - |
| `tim_slowmo_96` | Honey Pour Beauty | - | Pour a ribbon of honey at commercial beauty speed so it coils in air before the spoon. | still, motion, av | - |
| `tim_slowmo_120` | Action Review Speed | - | Replay a tackle at action-review speed so grass blades and spit hang in a readable arc. | still, motion, av | - |
| `tim_slowmo_240` | Ultra Hang Casing | - | Hang a brass casing in air at ultra speed so rifling glints crawl along the metal. | still, motion, av | - |
| `tim_speed_ramp_in` | Speed Ramp In | - | Speed-ramp into the hug so the run stays realtime then melts into a slow embrace. | still, motion, av | - |
| `tim_speed_ramp_out` | Speed Ramp Out | - | Speed-ramp out of the whisper so the slow lean snaps back to hallway pace. | still, motion, av | - |
| `tim_timeslice` | Time Slice Slats | - | Time-slice the room as a stack of vertical slats, each slat a different instant of the same walk. | still, motion, av | - |
| `tim_lapse_clouds` | Cloud Time Lapse | - | Time-lapse the sky so storm towers boil while terrace furniture stays planted. | still, motion, av | - |
| `tim_lapse_crowds` | Crowd Time Lapse | - | Time-lapse the plaza so crowds become ant-trails while the fountain holds its carved shape. | still, motion, av | - |
| `tim_lapse_night_to_day` | Night to Day Lapse | - | Time-lapse night into morning so streetlamps die and the east windows catch first fire. | still, motion, av | - |
| `tim_hyperlapse` | Street Hyperlapse | - | Hyperlapse down the unmarked avenue, lockoffs stepping forward so architecture jumps closer each beat. | still, motion, av | - |
| `tim_freeze_frame` | Freeze Frame | - | Freeze-frame the turn so the coat becomes a statue and the world waits on that beat. | still, motion, av | tim_strobe |
| `tim_orbit_freeze` | Orbit Freeze | - | Orbit a frozen figure so clothing and spray hang while the background travels around them. | still, motion, av | - |
| `tim_stop_motion_stutter` | Stop Motion Stutter | - | Animate the body in stop-motion stutter so poses click from mark to mark with empty air between. | still, motion, av | - |
| `tim_pixilation` | Pixilation | - | Pixilate live actors as if they were puppets, sliding them in tiny jumps across the curb. | still, motion, av | - |
| `tim_step_printed` | Step Printed | - | Step-print the dance so each gesture reprints two or three times before the next begins. | still, motion, av | - |
| `tim_overcrank` | Overcrank Silk | - | Overcrank the capture so playback turns tears and breath into silk threads. | still, motion, av | tim_undercrank |
| `tim_undercrank` | Undercrank Chase | - | Undercrank the chase so legs bicycle in comic haste and dust pops in clumps. | still, motion, av | tim_overcrank |
| `tim_silent_undercrank_comedy` | Silent Era Undercrank | - | Undercrank in silent-era comedy cadence so pratfalls chop and title-card gaps feel imminent. | still, motion, av | - |
| `tim_dream_slow` | Dream Slow | - | Dream-slow the corridor so wallpaper breathes and footsteps take a year to land. | still, motion, av | tim_realtime, tim_panic_fast |
| `tim_panic_fast` | Panic Fast | - | Panic-fast the search so drawers blur and the head snaps between hiding places. | still, motion, av | tim_dream_slow |
| `tim_match_on_action` | Match On Action Time | - | Carry match-on-action continuity so the pour begun in close finishes in the wide without a skip. | still, motion, av | - |
| `tim_jumpcut_skip` | Jump Cut Time Skip | - | Jump-cut a time skip in the same setup so the person teleports a few feet as minutes vanish. | still, motion, av | - |
| `tim_montage_compress` | Montage Compression | - | Compress a workday into a montage of tools, clocks, and discarded cups. | still, motion, av | - |
| `tim_lingering_hold` | Lingering Hold | - | Linger on the face after the news, holding past comfort until the blink finally comes. | still, motion, av | - |
| `tim_beat_hold_then_move` | Beat Hold Then Move | - | Hold the beat locked, then let the body move only after the pause has hurt. | still, motion, av | - |
| `tim_drop_frame_energy` | Drop Frame Energy | - | Drop-frame the party so energy skips and limbs arrive later than the torso. | still, motion, av | - |
| `tim_strobe` | Strobe Pops | - | Strobe the dance so bodies are a stack of white pops against black gaps. | still, motion, av | tim_freeze_frame |
| `tim_doubletime_walk` | Double Time Walk | - | Double-time the walk so the sidewalk eats itself and coats flap like flags. | still, motion, av | - |
| `tim_halftime_fight` | Half Time Fight | - | Half-time the brawl so jawlines stretch toward the punch and saliva threads span the gap. | still, motion, av | - |
| `tim_clock_wipe_time` | Clock Wipe Time | - | Wipe hours with a clock-hand across the room so noon becomes evening in one rotation. | still, motion, av | - |
| `tim_day_for_night_temporal` | Hours Into Night | - | Keep rolling until daylight actually dies, letting hours-not a grade-turn the street to night. | still, motion, av | - |
| `tim_frozen_splash` | Frozen Splash | - | Freeze the splash as a glass crown, droplets hanging around the submerged heel. | still, motion, av | - |
| `tim_hanging_fabric` | Hanging Fabric | - | Hang the fabric in air so a cloak becomes a frozen wave, folds readable as sculpture. | still, motion, av | - |
| `tim_bullet_hang_sparks` | Hanging Sparks | - | Hang sparks from an impact so embers sit like stars around the struck steel. | still, motion, av | - |
| `tim_shutter_90` | 90 Shutter Crisp | - | Set a 90-degree shutter so bicycle spokes stay partly drawn and faces stay crisp. | still, motion, av | - |
| `tim_open_shutter_spin` | Open Shutter Spin | - | Spin the dancer under an open shutter so the tutu becomes a ring of light. | still, motion, av | - |
| `tim_ghost_afterimage` | Afterimage Ghosts | - | Leave afterimage ghosts of the walker, four pale copies trailing the sharp body. | still, motion, av | - |
| `tim_speed_ramp_impact` | Ramp At Impact | - | Ramp to slow at the impact so the vase shatters as a blooming map of shards. | still, motion, av | - |
| `tim_speed_ramp_look` | Ramp On The Look | - | Ramp to slow on the glance, eyes finding the doorway while the room stays hurried. | still, motion, av | - |
| `tim_mixed_speed_talk` | Mixed Speed Talk | - | Mix speeds in the talk: mouths realtime, hands slow, rain slower still. | still, motion, av | - |
| `tim_slo_hair` | Slow Hair Strands | - | Slow the hair so each strand writes a separate curl against the window. | still, motion, av | - |
| `tim_slo_dust` | Slow Dust Motes | - | Slow the dust motes into a galaxy between the projector beam and the seat. | still, motion, av | - |
| `tim_slo_rain` | Slow Rain Coins | - | Slow the rain into fat coins that bounce on the cafe awning. | still, motion, av | - |
| `tim_slo_embers` | Slow Ember Climb | - | Slow the fireplace embers so each spark becomes a climbing insect of light. | still, motion, av | - |
| `tim_slo_glass_break` | Slow Pane Map | - | Slow the pane as it maps into a spider then a rain of triangles. | still, motion, av | - |
| `tim_slo_dive` | Slow Dive Hang | - | Slow the dive so the body hangs above green water, fingers first to the surface. | still, motion, av | - |
| `tim_slo_breath` | Slow Breath Animal | - | Slow exhaled vapor into a rolling animal that hides the mouth. | still, motion, av | - |
| `tim_undercrank_alley` | Undercrank Alley | - | Undercrank the alley chase so trash leaps in clumps and corners arrive too soon. | still, motion, av | - |
| `tim_overcrank_tears` | Overcrank Tear Fall | - | Overcrank grief so a single tear takes a whole scene to leave the chin. | still, motion, av | - |
| `tim_heartbeat_remap` | Heartbeat Remap | - | Remap time to a heartbeat, the room pulsing wider on each thump. | still, motion, av | - |
| `tim_hold_then_snap` | Hold Then Snap | - | Hold frozen, then snap back to realtime as the glass hits the floor. | still, motion, av | - |
| `tim_reverse_pour` | Reverse Pour | - | Reverse the pour so wine climbs back into the bottle. | still, motion, av | - |
| `tim_reverse_then_forward` | Reverse Then Forward | - | Reverse the collapse then slam forward through the same fall. | still, motion, av | - |
| `tim_loop_gesture` | Looped Gesture | - | Loop a small nod and tap until the gesture becomes a machine. | still, motion, av | - |
| `tim_skip_strobe` | Skip Frame Strobe | - | Skip frames as a crude strobe, the runner appearing in new places without travel. | still, motion, av | - |
| `tim_two_frame_stutter` | Two Frame Stutter | - | Stutter on two-frame cycles so the laugh jitters like a broken toy. | still, motion, av | - |
| `tim_three_two_cadence` | Three Two Cadence | - | Cadence the walk with a 3:2 pulldown hitch, film-video hybrid ticks in the stride. | still, motion, av | - |
| `tim_cadence_24` | Twenty Four Cadence | - | Lock a 24-frame cadence so blinks and steps feel theatrical and heavy. | still, motion, av | - |
| `tim_cadence_30` | Thirty Video Cadence | - | Lock a 30-frame video cadence so office fluorescents stop rolling and talk feels present. | still, motion, av | - |
| `tim_cadence_60` | Sixty Sports Cadence | - | Lock a 60-frame sports cadence so a handshake is dissectible bone by bone. | still, motion, av | - |
| `tim_lapse_shadows` | Shadow Sundial Lapse | - | Time-lapse shadows so a sundial of the tower sweeps the plaza. | still, motion, av | - |
| `tim_lapse_tide` | Tide Lapse | - | Time-lapse the tide so the pier legs drown and dry in breaths. | still, motion, av | - |
| `tim_lapse_scaffold` | Scaffold Lapse | - | Time-lapse scaffolding climbing the unmarked facade like a growing cage. | still, motion, av | - |
| `tim_lapse_stars` | Star Polyline Lapse | - | Time-lapse stars into polylines over a locked ridge. | still, motion, av | - |
| `tim_lapse_traffic` | Traffic Marrow Lapse | - | Time-lapse traffic into red and white marrow through the street grid. | still, motion, av | - |
| `tim_lapse_blossom` | Blossom Lapse | - | Time-lapse blossoms exploding then dropping on the tablecloth. | still, motion, av | - |
| `tim_hyperlapse_stairs` | Stairwell Hyperlapse | - | Hyperlapse the stairwell, each landing a stepped lockoff higher in the well. | still, motion, av | - |
| `tim_hyperlapse_market` | Market Hyperlapse | - | Hyperlapse the market aisle, stalls jumping, steam as dashes above the pots. | still, motion, av | - |
| `tim_frozen_crowd_moment` | Crowd Freeze Courier | - | Freeze the crowd while one courier keeps moving through statues. | still, motion, av | - |
| `tim_debris_hang` | Debris Mobile Hang | - | Hang explosion debris as a mobile of timber and paper above the street. | still, motion, av | - |
| `tim_water_sheet_hang` | Water Sheet Hang | - | Hang a sheet of thrown water as a lens in front of the face. | still, motion, av | - |
| `tim_confetti_hang` | Confetti Blizzard Hang | - | Hang confetti as a paused blizzard of color around the kiss. | still, motion, av | - |
| `tim_smoke_pause` | Smoke Column Pause | - | Pause a smoke column so the mushroom is sculpture above the ashtray. | still, motion, av | - |
| `tim_clock_hands_race` | Racing Clock Hands | - | Race the clock hands around the dial while the room stays still. | still, motion, av | - |
| `tim_page_calendar` | Calendar Flutter | - | Flutter calendar pages until the season in the window changes. | still, motion, av | - |
| `tim_season_compress` | Season Compress | - | Compress seasons in the same orchard: blossom, leaf, fruit, then snow. | still, motion, av | - |
| `tim_sunrise_compress` | Sunrise Compress | - | Compress sunrise so the east goes from ink to brass in seconds. | still, motion, av | - |
| `tim_sunset_compress` | Sunset Compress | - | Compress sunset so windows light from inside as the sky fails. | still, motion, av | - |
| `tim_magic_hour_stretch` | Magic Hour Stretch | - | Stretch magic hour so the peach band on the horizon refuses to die. | still, motion, av | - |
| `tim_golden_to_blue` | Golden Into Blue | - | Run golden hour into blue hour in one accelerating sky. | still, motion, av | - |
| `tim_blue_to_black` | Blue Into Blackout | - | Run blue hour into blackout as windows become the only map of the block. | still, motion, av | - |
| `tim_memory_smear` | Memory Smear | - | Memory-smear the childhood kitchen, edges dragging like wet paint. | still, motion, av | - |
| `tim_nightmare_drop` | Nightmare Drop Frame | - | Nightmare drop-frame the hallway, doors teleporting closer each skipped beat. | still, motion, av | - |
| `tim_dance_halftime` | Chorus Half Time | - | Half-time the chorus line so heels hang and sequins rain. | still, motion, av | - |
| `tim_dance_double` | Tap Double Time | - | Double-time the tap so the floor becomes a typewriter of shoes. | still, motion, av | - |
| `tim_super_slo_sports` | Super Slow Serve | - | Super-slow the serve so felt fuzz leaves the tennis ball in a halo. | still, motion, av | - |
| `tim_wildlife_burst` | Bird Launch Burst | - | Burst-time a bird launch so every feather becomes a separate knife in the air. | still, motion, av | - |
| `tim_blink_hold` | Blink Hold | - | Hold through the blink so lashes meet and the world goes briefly private. | still, motion, av | - |
| `tim_exhale_stretch` | Exhale Stretch | - | Stretch the exhale until shoulders drop a full scene later. | still, motion, av | - |
| `tim_elastic_impact` | Elastic Crash | - | Elastic-time the crash, metal blooming then snapping to wreck. | still, motion, av | - |
| `tim_whoosh_skip` | Whoosh Skip Rooms | - | Whoosh-skip between rooms, the body already there, air still settling. | still, motion, av | - |
| `tim_axial_time_punch` | Axial Time Punch | - | Punch in axially while time slows, the eyes arriving later than the lens. | still, motion, av | - |
| `tim_glass_hang_shards` | Shard Curtain Hang | - | Hang window shards as a glittering curtain the runner slides through. | still, motion, av | - |
| `tim_ribbon_hang` | Ribbon Ceremony Hang | - | Hang cut ribbon mid-ceremony, scissors still open on the taut strip. | still, motion, av | - |
| `tim_powder_hang` | Festival Powder Hang | - | Hang colored powder from a festival strike as a frozen cloud. | still, motion, av | - |
| `tim_step_print_fight` | Step Printed Scuffle | - | Step-print the scuffle so each shove reprints, comic and brutal at once. | still, motion, av | - |
| `tim_pixilation_crosswalk` | Crosswalk Pixilation | - | Pixilate a crosswalk so people are chess pieces advancing a square at a time. | still, motion, av | - |
| `tim_stopmo_tabletop` | Tabletop Stop Motion | - | Stop-motion the tabletop meal, food rearranging between blinks of the diner. | still, motion, av | - |
| `tim_gomotion_blur` | Blurred Stop Motion | - | Add captured blur to each stop-motion step so the puppet smears instead of popping. | still, motion, av | - |
| `tim_time_stack` | Doorway Time Stack | - | Stack many hours of the same doorway into one plate of overlapping occupants. | still, motion, av | - |
| `tim_slit_scan` | Slit Scan Walker | - | Slit-scan the walker so the body becomes a stretched accordion of instants. | still, motion, av | - |
| `tim_chrono_array` | Chrono Slice Fan | - | Array a chrono-slice of the jump as a fan of bodies around the peak. | still, motion, av | - |
| `tim_silence_freeze` | Silence Freeze | - | Freeze the picture and drop the room to a thin ring, silence as time. | still, motion, av | - |
| `tim_tick_jump` | Clock Tick Jump | - | Jump the scene on each clock tick, poses landing on the second hand. | still, motion, av | - |
| `tim_rain_freeze_then_fall` | Rain Nails Then Fall | - | Freeze rain as nails, then let it fall all at once. | still, motion, av | - |
| `tim_fabric_settle` | Sheet Settle Stretch | - | Slow a dropped sheet until it takes a minute to find the floor. | still, motion, av | - |
| `tim_candle_hours` | Candle To Puddle | - | Time-lapse a candle to a puddle while the sitter never changes pose. | still, motion, av | - |
| `tim_crowd_freeze_photo` | Shared Flash Instant | - | Freeze a plaza as if a photographer's flash stole one shared instant. | still, motion, av | - |
| `tim_speed_ramp_door` | Doorway Speed Ramp | - | Ramp slow through the doorway, corridor realtime on both sides of the threshold. | still, motion, av | - |
| `tim_undercrank_work` | Undercrank Labor | - | Undercrank labor so crates stack themselves in a hurry. | still, motion, av | - |
| `tim_overcrank_smoke` | Overcrank Smoke Architecture | - | Overcrank cigarette smoke into architecture above the table. | still, motion, av | - |
| `tim_match_action_door` | Handle Turn Continuity | - | Match-on-action through a door so the handle turn is one continuous time. | still, motion, av | - |
| `tim_slo_punch_connect` | Glove Connect Slow | - | Slow the glove connecting so cheek flesh rolls in a wave from the impact. | still, motion, av | - |
| `tim_flashback_speed` | Flashback Cadence | - | Drop into a slightly undercranked flashback cadence, edges humming, present tense waiting. | still, motion, av | - |
| `tim_hold_on_exit` | Empty Frame After Exit | - | Hold on the empty room after the exit so time keeps moving without a person. | still, motion, av | - |
| `tim_pre_enter_hold` | Empty Frame Before Enter | - | Hold on empty space until someone enters, time as waiting. | still, motion, av | - |
| `tim_slo_cloak_settle` | Cloak Settle Slow | - | Slow a thrown cloak until it settles like weather on the shoulders. | still, motion, av | - |
| `tim_undercrank_crowd_part` | Undercrank Crowd Part | - | Undercrank a crowd parting so bodies hop aside in clumps. | still, motion, av | - |
| `tim_overcrank_flag` | Overcrank Flag Wave | - | Overcrank a flag so each ripple becomes a slow muscle across cloth. | still, motion, av | - |
| `tim_strobe_walk` | Strobe Walk Pops | - | Strobe a walk so the figure becomes a dotted line of white statues down the hall. | still, motion, av | - |
| `tim_timeslice_face` | Face Time Slice | - | Time-slice a turning face so one cheek is earlier than the other. | still, motion, av | - |
| `tim_hyperlapse_bridge` | Bridge Hyperlapse | - | Hyperlapse across a bridge, lockoffs eating the span in steps. | still, motion, av | - |
| `tim_lapse_windows` | Window Lights Lapse | - | Time-lapse office windows as a random piano of lamps going on and off. | still, motion, av | - |
| `tim_slo_paper_throw` | Slow Paper Storm | - | Slow thrown papers into a storm of pages around the desk. | still, motion, av | - |
| `tim_freeze_mid_stride` | Mid Stride Freeze | - | Freeze mid-stride, spray hanging, both feet off the ground for a beat. | still, motion, av | - |

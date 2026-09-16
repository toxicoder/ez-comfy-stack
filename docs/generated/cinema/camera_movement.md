---
title: Camera Movement
description: Cinema Rack catalog — Camera Movement (195 spliceable techniques).
tags: [cinema, prompting, catalog]
---

# Camera Movement

**What's on this page**

- 195 spliceable techniques for **Camera Movement**
- Still mode `freeze`; I2V include `True`
- Ids for the Cinema Rack combo (pick one per axis)

**What this enables**

- Picking a professional cinematography clause instead of guessing camera language
- Seeing conflicts, still/motion/AV flags, and the Wan token when present

Do not hand-edit this file. Re-run `python3 docs/generate_cinema_docs.py`.
Operator playbook: [Cinema Rack](../../create/cinema-rack.md).

| Id | Label | Clause | Use on | Conflicts |
| --- | --- | --- | --- | --- |
| `move_pan_left` | Pan left | The camera pans left on a locked tripod head, sweeping the unmarked street from the doorway toward the corner lamp. | still, motion, av | move_whip_pan_left |
| `move_pan_right` | Pan right | The camera pans right on a locked tripod head, letting terrace lanterns drift across the bay slot. | still, motion, av | move_whip_pan_right |
| `move_slow_pan_left` | Slow pan left | The camera pans left at crawl speed on a geared head, clouds and distant towers sliding a finger-width at a time. | still, motion, av | — |
| `move_slow_pan_right` | Slow pan right | The camera pans right at crawl speed on a geared head, a long colonnade revealing one column after another. | still, motion, av | — |
| `move_whip_pan_left` | Whip pan left | The camera whips left in a blurred pan, streaking practicals into unreadable color bands. | still, motion, av | move_pan_left, move_locked_off |
| `move_whip_pan_right` | Whip pan right | The camera whips right in a blurred pan, neon shopfronts collapsing into horizontal streaks. | still, motion, av | move_pan_right, move_locked_off |
| `move_search_pan` | Search pan | The camera pans in a searching arc on a fluid head, hunting a doorway then overshooting and correcting. | still, motion, av | — |
| `move_tilt_up` | Tilt up | The camera tilts up from a locked tripod, rising from pavement grit to the unmarked crown of the tower. | still, motion, av | — |
| `move_tilt_down` | Tilt down | The camera tilts down from a locked tripod, dropping from sky to the subject's hands and the teak deck. | still, motion, av | — |
| `move_slow_tilt_up` | Slow tilt up | The camera tilts up at crawl speed, a facade unrolling floor by floor. | still, motion, av | — |
| `move_slow_tilt_down` | Slow tilt down | The camera tilts down at crawl speed, a tree canopy giving way to roots and wet soil. | still, motion, av | — |
| `move_snap_tilt_up` | Snap tilt up | The camera snaps tilt up in one accent, punching from shoes to sky in a single jerk. | still, motion, av | — |
| `move_nod_tilt` | Nod tilt | The camera tilts in a small nodding search, checking the subject's face then the object in their hands. | still, motion, av | — |
| `move_dutch_roll` | Dutch roll | The camera rolls the horizon off-level while holding position, the floor line tilting as if the room lost its balance. | still, motion, av | move_locked_off |
| `move_level_out` | Level out | The camera rolls from a canted horizon back to level, the verticals of the tower standing up straight again. | still, motion, av | — |
| `move_dolly_in` | Dolly in | The camera dollies in on a locked wheeled support, tightening without zooming, the subject's face growing while background geometry stays h… | still, motion, av | fx_crash_zoom, opt_zoom_in |
| `move_dolly_out` | Dolly out | The camera dollies out on a locked wheeled support, widening without zooming, the room expanding around a still figure. | still, motion, av | opt_zoom_out |
| `move_slow_dolly_in` | Slow dolly in | The camera creeps in on silent dolly wheels, breath and blinks becoming the only motion in a shrinking frame. | still, motion, av | — |
| `move_slow_dolly_out` | Slow dolly out | The camera creeps out on silent dolly wheels, isolation growing as walls recede. | still, motion, av | — |
| `move_crash_dolly_in` | Crash dolly in | The camera crashes in on a fast dolly, the background ripping past in a sudden close-up. | still, motion, av | move_slow_dolly_in |
| `move_dolly_zoom_in` | Dolly zoom in | The camera dollies in while zooming out so the subject size holds and space warps, the corridor stretching while the face stays the same si… | still, motion, av | move_dolly_in, opt_zoom_out |
| `move_dolly_zoom_out` | Dolly zoom out | The camera dollies out while zooming in so the subject size holds and space crushes, the world flattening behind a face that does not grow. | still, motion, av | move_dolly_out, opt_zoom_in |
| `move_tracking_left` | Tracking left | The camera tracks left parallel to the subject, keeping pace beside a walk along a wet unmarked arcade. | still, motion, av | — |
| `move_tracking_right` | Tracking right | The camera tracks right parallel to the subject, matching stride along a night rail over the bay. | still, motion, av | — |
| `move_lead_tracking` | Lead tracking | The camera tracks ahead of the subject, looking back, the walker advancing toward camera down a long hall. | still, motion, av | — |
| `move_chase_tracking` | Chase tracking | The camera tracks behind the subject, following, the back of a coat leading into an unmarked tunnel. | still, motion, av | — |
| `move_lateral_truck_left` | Truck left | The camera trucks left on a perpendicular axis, sliding past a row of columns that wipe the frame. | still, motion, av | — |
| `move_lateral_truck_right` | Truck right | The camera trucks right on a perpendicular axis, a storefront sequence wiping by like cards. | still, motion, av | — |
| `move_pedestal_up` | Pedestal up | The camera pedestals straight up with no tilt, the horizon staying level while the camera rises past a railing. | still, motion, av | — |
| `move_pedestal_down` | Pedestal down | The camera pedestals straight down with no tilt, sinking from standing height to the grain of the floorboards. | still, motion, av | — |
| `move_crane_up` | Crane up | The camera cranes up on a jib arm, the terrace shrinking as rooftops and bay enter the top of frame. | still, motion, av | — |
| `move_crane_down` | Crane down | The camera cranes down on a jib arm, descending from weather into a private face. | still, motion, av | — |
| `move_crane_in` | Crane in | The camera cranes on an arc that also pushes in, arriving from above into an intimate two-shot. | still, motion, av | — |
| `move_crane_reveal` | Crane reveal | The camera cranes up and over a foreground occluder, a parapet dropping away to show the whole unmarked plaza. | still, motion, av | — |
| `move_jib_sweep` | Jib sweep | The camera sweeps a short jib in a smiling arc, the camera scooping from low dirt to eye-level in one piece. | still, motion, av | — |
| `move_arm_over` | Long arm over | The camera swings a long arm over the set, looking down the dining table as if from a gallery. | still, motion, av | — |
| `move_slider_left` | Slider left | The camera slides left on a short rail, a product on a table gaining a new three-quarter. | still, motion, av | — |
| `move_slider_right` | Slider right | The camera slides right on a short rail, parallax shifting a bottle against a soft practical. | still, motion, av | — |
| `move_slider_in` | Slider in | The camera slides in on a short rail aimed at the subject, a tabletop hero growing without a zoom. | still, motion, av | — |
| `move_slider_push_low` | Low slider push | The camera slides in from ankle height, floorboards racing toward a seated figure. | still, motion, av | — |
| `move_steadicam_follow` | Stabilized follow | The camera follows on a body-worn stabilizer, the operator floating through a doorway without foot-thud shake. | still, motion, av | — |
| `move_steadicam_lead` | Stabilized lead | The camera leads on a body-worn stabilizer, walking backward, the subject walking toward a floating lens down a corridor. | still, motion, av | — |
| `move_gimbal_orbit` | Gimbal orbit | The camera orbits on a handheld gimbal, circling a standing figure while the horizon stays locked. | still, motion, av | — |
| `move_gimbal_rise` | Gimbal rise | The camera rises on a handheld gimbal from kneel to stand, the lens lifting with the operator's legs, horizon true. | still, motion, av | — |
| `move_handheld_breathe` | Handheld breathe | The camera holds handheld with living micro-sway, the frame inhaling with the operator, never locked. | still, motion, av | move_locked_off |
| `move_handheld_walk` | Handheld walk | The camera walks handheld, documenting from inside the group, shoulders and footsteps leaking into the frame edges. | still, motion, av | move_locked_off |
| `move_handheld_run` | Handheld run | The camera runs handheld, horizon fighting to stay useful, pavement shock and pumping arms in a chase document. | still, motion, av | move_locked_off |
| `move_shoulder_doc` | Shoulder documentary | The camera rides a shoulder pad in observational mode, a slightly high documentary eyeline with organic drift. | still, motion, av | — |
| `move_bodycam_sprint` | Body-cam sprint | The camera sprints as a chest-mounted body-cam, only the wearer's sleeves along the bottom edge, landing filling the center. | still, motion, av | — |
| `move_bodycam_lookdown` | Body-cam look-down | The camera looks down as a chest-mounted body-cam, gloves and the next foothold filling the lower frame. | still, motion, av | — |
| `move_fpv_dive` | FPV dive | The camera dives as a first-person flyer, the plaza rushing up, lens screaming toward a landing mark. | still, motion, av | — |
| `move_fpv_through` | FPV through | The camera threads a gap as a first-person flyer, a doorway or railing whipping past at the frame edges. | still, motion, av | — |
| `move_drone_orbit` | Drone orbit | The camera orbits at mid altitude on a quiet multirotor, the unmarked tower turning against the bay. | still, motion, av | — |
| `move_drone_rise` | Drone rise | The camera rises on a quiet multirotor, the building shrinking into a city of unmarked glass. | still, motion, av | — |
| `move_drone_descend` | Drone descend | The camera descends on a quiet multirotor, weather giving way to terrace furniture and palms. | still, motion, av | — |
| `move_drone_reveal_ridge` | Drone ridge reveal | The camera flies up over a ridge or parapet, the hidden plaza blooming into frame past stone. | still, motion, av | — |
| `move_drone_topdown` | Drone top-down | The camera holds a nadir descent, plan-view massing of roof and courtyard tightening. | still, motion, av | — |
| `move_drone_push_in` | Drone push in | The camera pushes in from altitude toward a figure, a person on a roof growing from a speck to a readable body. | still, motion, av | — |
| `move_cable_traverse` | Cable traverse | The camera traverses on an overhead cable, the street sliding under a high centerline path. | still, motion, av | — |
| `move_cable_descend` | Cable descend | The camera descends along a cable toward a crowd, faces rising to meet a falling overhead lens. | still, motion, av | — |
| `move_vehicle_side` | Vehicle side mount | The camera rides a side-mounted vehicle camera, asphalt and lane lines streaking under a door-line lens. | still, motion, av | — |
| `move_vehicle_hood` | Vehicle hood mount | The camera rides a hood-mounted camera looking aft, the driver and windscreen filling the frame as city smears behind. | still, motion, av | — |
| `move_vehicle_chase` | Vehicle chase | The camera chases from a second vehicle, the lead car framed through a windshield, road vibration alive. | still, motion, av | — |
| `move_undercrank_handheld` | Undercranked handheld | The camera moves handheld with silent-era undercrank energy, jerky comic haste in every step. | still, motion, av | — |
| `move_locked_off` | Locked off | The camera holds a locked-off tripod, zero drift, architecture and body both pinned, only subject motion allowed. | still, motion, av | move_handheld_breathe, move_whip_pan_left |
| `move_static_then_push` | Hold then push | The camera holds locked, then begins a late dolly in, a conversation beat then a slow tightening. | still, motion, av | — |
| `move_push_then_hold` | Push then hold | The camera dollies in and lands on a locked close frame, motion dying as the eyes fill the frame. | still, motion, av | — |
| `move_orbit_left` | Orbit left | The camera orbits left around the subject at constant radius, background sliding the opposite way, face turning through three-quarter. | still, motion, av | — |
| `move_orbit_right` | Orbit right | The camera orbits right around the subject at constant radius, a product or person rotating against a traveling city. | still, motion, av | — |
| `move_arc_left` | Arc left | The camera arcs left on a shallow curve, not a full orbit, a doorway opening into a new wall of the room. | still, motion, av | — |
| `move_arc_right` | Arc right | The camera arcs right on a shallow curve, not a full orbit, a window coming into play as the camera rounds a chair. | still, motion, av | — |
| `move_circle_360` | Full circle | The camera completes a 360-degree orbit, every wall of the room passing once behind the subject. | still, motion, av | — |
| `move_figure_eight` | Figure-eight | The camera traces a figure-eight on the floor around two marks, two subjects trading foreground as the path crosses. | still, motion, av | — |
| `move_boom_up_track` | Boom up while tracking | The camera booms up while tracking beside the subject, rising from hip to face without losing the walk. | still, motion, av | — |
| `move_boom_down_track` | Boom down while tracking | The camera booms down while tracking beside the subject, dropping to the feet without losing pace. | still, motion, av | — |
| `move_reveal_wipe_by` | Wipe-by reveal | The camera lets a foreground passerby wipe the lens into a new composition, a shoulder or vehicle clearing to a changed scene. | still, motion, av | — |
| `move_reveal_focus_pull_in` | Focus-pull reveal in | The camera dollies in as focus throws from glass to the person beyond, a dirty window going sharp on the figure inside. | still, motion, av | — |
| `move_push_through_door` | Push through door | The camera pushes through a doorway on a stabilizer, the frame catching both rooms for a beat of threshold. | still, motion, av | — |
| `move_pull_out_door` | Pull out of door | The camera pulls backward through a doorway, the interior shrinking inside a dark jamb. | still, motion, av | — |
| `move_around_corner` | Around the corner | The camera rounds a corner and discovers the next plane, a new hallway snapping into existence. | still, motion, av | — |
| `move_elevator_rise` | Elevator rise | The camera rises as if in an elevator cab, verticals true, floors of glass sliding down the frame like a count. | still, motion, av | — |
| `move_elevator_drop` | Elevator drop | The camera drops as if in an elevator cab, the lobby floor rushing up to meet the boots. | still, motion, av | — |
| `move_underwater_track` | Underwater track | The camera tracks underwater with a housed lens, caustics crawling over a body moving through blue. | still, motion, av | — |
| `move_underwater_rise` | Underwater rise | The camera rises underwater toward the sunlit surface, the underside of the waves becoming a bright ceiling. | still, motion, av | — |
| `move_surface_breach` | Surface breach | The camera breaches from underwater into air, droplets and a sudden dry world above the split. | still, motion, av | — |
| `move_macro_push` | Macro push | The camera pushes in at macro working distance, pores, weave, or condensation becoming landscape. | still, motion, av | — |
| `move_probe_in` | Probe in | The camera slides a probe lens into a tight cavity, a miniature interior opening around a tiny entrance. | still, motion, av | — |
| `move_periscope_over` | Periscope over | The camera looks over a low wall with a periscope optic, the far table appearing as if the camera had no body. | still, motion, av | — |
| `move_tilt_up_dolly_in` | Tilt up while dollying in | The camera tilts up while dollying in, rising attention and closer proximity in one move. | still, motion, av | — |
| `move_pan_with_walk` | Pan with walk | The camera pans to keep a walker centered, background streaking while the stride stays planted in frame. | still, motion, av | — |
| `move_counter_zoom_track` | Counter-zoom track | The camera tracks one way while a slow zoom opposes, speed of background disagreeing with subject size. | still, motion, av | — |
| `move_snorricam_body` | Body-mounted facing | The camera rides a rig facing the walker from their own chest, the world sliding behind a stable face and shoulders. | still, motion, av | — |
| `move_low_mode_track` | Low-mode track | The camera tracks in low-mode with the lens near the floor, shoes and dust kicking, ceiling running overhead. | still, motion, av | — |
| `move_high_mode_track` | High-mode track | The camera tracks in high-mode above head height, crowns and hats, the floor falling away. | still, motion, av | — |
| `move_steeper_jib_up` | Steep jib up | The camera jibs up on a steep almost-vertical arc, going from worm's-eye to plan in one scoop. | still, motion, av | — |
| `move_carousel_around_table` | Carousel around table | The camera circles a table at seated height, plates and faces trading the foreground chair by chair. | still, motion, av | — |
| `move_reverse_crash_out` | Crash out | The camera crashes out on a fast dolly, the close face ripping to a wide isolation. | still, motion, av | — |
| `move_zolly_horror` | Space-warp push | The camera combines a slow push with opposing zoom for dread, the hallway becoming a tunnel while the person does not grow. | still, motion, av | move_dolly_in |
| `move_timelapse_pan` | Timelapse pan | The camera pans across a long exposure sequence of the same place, clouds and crowds in streaks, architecture still. | still, motion, av | — |
| `move_hyperlapse_walk` | Hyperlapse walk | The camera advances in a hyperlapse along a path, the street jumping forward in stepped lockoffs. | still, motion, av | — |
| `move_orbit_and_rise` | Orbit and rise | The camera orbits while rising, the subject turning and shrinking as rooftops enter. | still, motion, av | — |
| `move_push_in_rack` | Push in with rack | The camera dollies in as focus racks from eyes to a foreground object, the held object winning the plane as the face softens. | still, motion, av | — |
| `move_pull_focus_track` | Track with follow-focus | The camera tracks while follow-focus holds the moving eyes, the walker sharp, background breathing in and out of plane. | still, motion, av | — |
| `move_lock_off_then_whip` | Lock then whip | The camera holds locked, then whips to a new mark, a still conversation then a violent redirect. | still, motion, av | move_locked_off |
| `move_start_stop_dolly` | Start-stop dolly | The camera dollies in pulses, easing to dead stops, punctuation in the approach, not a constant glide. | still, motion, av | — |
| `move_ease_in_pan` | Ease-in pan | The camera starts a pan from a dead stop with a long ease, the street only just beginning to travel. | still, motion, av | — |
| `move_ease_out_dolly` | Ease-out dolly | The camera ends a dolly with a long settle, the last inch of approach dying into a portrait. | still, motion, av | — |
| `move_parallax_slide` | Parallax slide | The camera slides so near objects wipe faster than far towers, a railing streaking, the bay almost still. | still, motion, av | — |
| `move_vertigo_corridor` | Corridor stretch | The camera walks a long corridor with a slow opposing zoom, linoleum and doors receding unnaturally. | still, motion, av | — |
| `move_helmet_cam` | Helmet cam | The camera rides a helmet-mounted lens, the visor edge and the next obstacle owning the frame. | still, motion, av | — |
| `move_dash_forward` | Dash forward | The camera looks forward from a dash mount, the road and wipers, city rushing the vanishing point. | still, motion, av | — |
| `move_bike_low` | Bike low mount | The camera rides a low bicycle or board mount, wheels, tar, and ankles at speed. | still, motion, av | — |
| `move_wheelchair_smooth` | Chair-smooth track | The camera tracks from a wheelchair or doorway dolly, very smooth and low, interior thresholds gliding at seated height. | still, motion, av | — |
| `move_office_chair_whip` | Chair whip | The camera spins on a chair dolly for a fast orbit fragment, the room smearing around a seated subject. | still, motion, av | — |
| `move_step_print_move` | Step-printed move | The camera moves with step-printed stutter on a simple pan, the street advancing in chopped increments. | still, motion, av | — |
| `move_drone_strafe` | Drone strafe | The camera strafes sideways at altitude without yawing, facades sliding as if on a high slider. | still, motion, av | — |
| `move_boom_over_bed` | Boom over bed | The camera booms over a bed or table from foot to overhead, the recumbent figure going from profile to plan. | still, motion, av | — |
| `move_entry_threshold` | Threshold enter | The camera crosses a threshold from dark exterior to lit interior, exposure and color of the room blooming around the lens. | still, motion, av | — |
| `move_exit_threshold` | Threshold exit | The camera crosses from lit interior into night, the warm room shrinking behind a dark street. | still, motion, av | — |
| `move_spiral_stair` | Spiral stair | The camera descends or climbs a spiral with the railing as a guide, the well of the stair turning around a central void. | still, motion, av | — |
| `move_crowd_part` | Crowd part | The camera pushes through a parting crowd on a stabilizer, shoulders wiping either side of a path to a waiting face. | still, motion, av | — |
| `move_window_pass` | Window pass | The camera passes a window from outside, seeing in then out, interior lamp-light then reflection of the street. | still, motion, av | — |
| `move_mirror_slide` | Mirror slide | The camera slides along a mirror so the reflection rebuilds the room, the real room and its double trading dominance. | still, motion, av | — |
| `move_over_shoulder_adjust` | Over-shoulder adjust | The camera makes a tiny lateral to dirty or clean an over-shoulder, a cheek entering or leaving the foreground edge. | still, motion, av | — |
| `move_push_to_insert` | Push to insert | The camera pushes from a medium into an insert of the hands, the face leaving, the object becoming the scene. | still, motion, av | — |
| `move_pull_to_wide` | Pull to wide | The camera pulls from a close face to a wide of the whole place, context arriving around a still expression. | still, motion, av | — |
| `move_crane_kiss` | Crane kiss | The camera cranes down to a near-touch of a tabletop then stops, the last inch of air over glass or food. | still, motion, av | — |
| `move_slider_vert` | Vertical slider | The camera slides vertically on a tower rail, a poster or facade unrolling without a tilt. | still, motion, av | — |
| `move_yaw_on_the_move` | Yaw while tracking | The camera yaws to a new subject while still tracking the first path, attention leaving one walker for another without stopping. | still, motion, av | — |
| `move_hidden_cut_move` | Hidden-cut move | The camera moves to a passing occluder meant to hide a join, a column or truck filling the frame as a seam. | still, motion, av | — |
| `move_lock_off_breathing_iris` | Locked with breathing iris | The camera holds position while the iris breathes as a character, the world dimming and opening without a pan. | still, motion, av | — |
| `move_mini_jib_food` | Mini-jib food | The camera scoops a tiny jib over a plate, steam and garnish becoming the whole landscape. | still, motion, av | — |
| `move_studio_ped_sit` | Studio pedestal sit | The camera sits a studio pedestal to seated eyeline, a talk setup dropping from standing host to guest height. | still, motion, av | — |
| `move_studio_ped_stand` | Studio pedestal stand | The camera rises a studio pedestal to standing eyeline, the desk falling out as the host stands. | still, motion, av | — |
| `move_remote_head_tilt` | Remote-head tilt | The camera tilts on a remote head at the end of a long arm, the operator nowhere near the lens, the view from a crane tongue. | still, motion, av | — |
| `move_remote_head_pan_search` | Remote-head search | The camera pans a remote head hunting a mark from high up, a high corner looking for a figure in a yard. | still, motion, av | — |
| `move_slow_orbit_product` | Slow product orbit | The camera orbits a product at display speed, highlights walking around a bottle or device. | still, motion, av | — |
| `move_snap_orbit_quarter` | Snap quarter orbit | The camera snaps a 90-degree orbit in one accent, the three-quarter appearing as if cut, but moved. | still, motion, av | — |
| `move_keep_horizon_run` | Horizon-locked run | The camera runs with a gimbal fighting to keep horizon, legs pumping, skyline true, urgency without dutch. | still, motion, av | — |
| `move_drift_in_current` | Drift in current | The camera drifts with water current past a still subject, weeds and particles traveling while a rock or body holds. | still, motion, av | — |
| `move_boom_mic_avoid` | Boom-avoiding dip | The camera dips under an imagined boom then recovers, the frame ducking then finding eyes again. | still, motion, av | — |
| `move_call_and_answer_pan` | Call-and-answer pan | The camera pans from speaker to listener as a sentence lands, the first face leaving, the reaction arriving. | still, motion, av | — |
| `move_match_speed_walk` | Match-speed walk | The camera matches walking speed exactly, background the only travel, the subject glued in frame, world sliding. | still, motion, av | — |
| `move_under_speed_walk` | Under-speed walk | The camera tracks slower than the walk so the subject overtakes, the walker passing camera and receding. | still, motion, av | — |
| `move_over_speed_walk` | Over-speed walk | The camera tracks faster than the walk so the camera overtakes, the lens pulling ahead and looking back. | still, motion, av | — |
| `move_crane_sun_against` | Crane against sun | The camera cranes up into a backlit sun flare, the figure going to silhouette as the sky floods. | still, motion, av | — |
| `move_night_practical_push` | Night practical push | The camera pushes toward a practical lamp that becomes the key, a porch light blooming as the face enters its pool. | still, motion, av | — |
| `move_rain_windshield` | Rain windshield | The camera looks through a rained windshield with wipers, drops and arcs of the wiper as the road smears. | still, motion, av | — |
| `move_two_shot_rebalance` | Two-shot rebalance | The camera slides to rebalance a two-shot as one person sits, empty air filling where a standing body just was. | still, motion, av | — |
| `move_close_circle_face` | Close face circle | The camera orbits very close around a face, pores and ear giving way to profile, background a ring of blur. | still, motion, av | — |
| `move_god_view_drop` | God-view drop | The camera drops from a high plan toward a single person, the crowd becoming one readable figure. | still, motion, av | — |
| `move_exit_frame_hold` | Hold after exit | The camera holds locked after the subject leaves frame, the place continuing without them. | still, motion, av | — |
| `move_enter_frame_hold` | Hold before enter | The camera holds locked on empty space until someone enters, the doorway waiting. | still, motion, av | — |
| `move_snorricam_hands` | Hands-forward body rig | The camera points a body rig at the hands working, tools in the lower frame, world sliding beyond the wrists. | still, motion, av | — |
| `move_pocket_peek` | Pocket peek | The camera rises from a pocket or bag height to the street, fabric then sudden city. | still, motion, av | — |
| `move_table_surface_slide` | Table-surface slide | The camera slides at tabletop height along a spread of objects, glassware and cards wiping the near field. | still, motion, av | — |
| `move_bookshelf_track` | Bookshelf track | The camera tracks along a shelf of unmarked spines, wood and paper rhythm, a face waiting at the aisle end. | still, motion, av | — |
| `move_industrial_catwalk` | Catwalk track | The camera tracks a high industrial catwalk, grate floor and a drop to machinery on both sides. | still, motion, av | — |
| `move_fog_in` | Push into fog | The camera pushes into thickening fog until the subject is a shape, depth collapsing to tone. | still, motion, av | — |
| `move_fog_out` | Pull out of fog | The camera pulls out of fog into readable air, edges returning to the world. | still, motion, av | — |
| `move_sparkler_orbit` | Spark-orbit | The camera orbits a handheld sparkler or spark source, ember trails wrapping a silhouette. | still, motion, av | — |
| `move_candle_approach` | Candle approach | The camera approaches a single candle until it floods the lens, the flame becoming the whole exposure. | still, motion, av | — |
| `move_stage_bow_out` | Stage bow-out | The camera dollies out down an aisle as if leaving a stage, a figure shrinking in lights, rows entering the sides. | still, motion, av | — |
| `move_aisle_procession` | Aisle procession | The camera tracks down a center aisle toward an altar or desk, symmetry pulling the eye to the far plane. | still, motion, av | — |
| `move_loading_dock_strafe` | Dock strafe | The camera strafes a loading dock at truck-bed height, bumpers and bays counting off. | still, motion, av | — |
| `move_mezzanine_slide` | Mezzanine slide | The camera slides a mezzanine railing looking down, the floor below traveling under a banister. | still, motion, av | — |
| `move_skater_low` | Skater low | The camera rides a very low board-height lens, coping and asphalt at cheek height. | still, motion, av | — |
| `move_float_invisible_stick` | Floating stick | The camera floats as if on a hidden selfie stick, no operator body, the subject with empty air where a stick would be. | still, motion, av | — |
| `move_bullet_orbit_freeze` | Orbit freeze | The camera orbits while time feels frozen on the subject, clothing and spray hanging while the background travels. | still, motion, av | — |
| `move_crash_zoom_on_move` | Move then crash zoom | The camera tracks then crash-zooms the last beat, a walk landing in a sudden tight face. | still, motion, av | move_dolly_in, fx_crash_zoom |
| `move_locked_off_zoom` | Locked zoom | The camera zooms on a locked tripod, no body move, compression changing while the nodal point holds. | still, motion, av | move_dolly_in |
| `move_snap_zoom_in` | Snap zoom in | The camera snap-zooms in on a locked support, the face punching larger in one optical hit. | still, motion, av | move_dolly_in, fx_crash_zoom |
| `move_snap_zoom_out` | Snap zoom out | The camera snap-zooms out on a locked support, context slamming around a face. | still, motion, av | — |
| `move_live_switcher_pan` | Switcher pan | The camera pans as if a live-event camera finding a mark, a stage finding the next speaker from a house position. | still, motion, av | — |
| `move_house_left_push` | House-left push | The camera pushes from house left toward a stage, audience heads as foreground, a figure growing on stage. | still, motion, av | — |
| `move_wings_reveal` | Wings reveal | The camera slides out from stage wings, black masking giving way to lights and an audience. | still, motion, av | — |
| `move_follow_spotlight_feel` | Follow-spot feel | The camera tilts and pans as if chasing a follow-spot beam, the bright pool moving, the camera glued to it. | still, motion, av | — |
| `move_security_pan` | Security pan | The camera pans slowly like a high-corner security head, a room surveyed from the ceiling corner, slightly wide and cold. | still, motion, av | — |
| `move_baby_mobile_orbit` | Over-crib orbit | The camera orbits slowly above a crib or small bed, mobiles and a small recumbent figure in plan. | still, motion, av | — |
| `move_kitchen_pass` | Kitchen pass | The camera tracks a pass-through from kitchen to dining, steam and plates traveling into the next room. | still, motion, av | — |
| `move_service_corridor` | Service corridor | The camera tracks a narrow service corridor, pipes, scuff, and a vanishing point of doors. | still, motion, av | — |
| `move_garden_hedge_wipe` | Hedge wipe | The camera tracks behind a hedge that wipes to a lawn, leaves then sudden open grass. | still, motion, av | — |
| `move_pier_out` | Pier dolly out | The camera dollies backward along a pier, the walker shrinking, water widening on both sides. | still, motion, av | — |
| `move_pier_in` | Pier dolly in | The camera dollies in along a pier toward a waiting figure, planks rushing, a silhouette growing against the bay. | still, motion, av | — |
| `move_switchback_drone` | Switchback drone | The camera follows a mountain switchback from above, hairpin road and a tiny traveler. | still, motion, av | — |
| `move_wave_level` | Wave-level track | The camera tracks at the height of breaking water, foam and a body in the same plane. | still, motion, av | — |
| `move_train_window` | Train window | The camera looks out a train window with passing world, poles and fields strobing, interior reflection faint. | still, motion, av | — |
| `move_subway_lurch` | Subway lurch | The camera handheld in a lurching subway car, straps and poles, the floor not agreeing with the horizon. | still, motion, av | — |
| `move_escalator_ride` | Escalator ride | The camera rides an escalator, looking with the rise, steps and a mall or station opening above. | still, motion, av | — |
| `move_down_escalator` | Down escalator | The camera rides an escalator down, a concourse rising to meet the lens. | still, motion, av | — |
| `move_carousel_horse` | Fairground circle | The camera circles as if on a fairground ride, lights smearing, a face returning every turn. | still, motion, av | — |
| `move_ferris_rise` | Ferris rise | The camera rises on a long slow arc like a ferris chair, the fairground shrinking, wind and city arriving. | still, motion, av | — |
| `move_locked_off_cloud` | Locked cloud | The camera locks off on sky so only clouds move, architecture as a silhouette against traveling weather. | still, motion, av | — |
| `move_push_into_eyes` | Push into eyes | The camera dollies until the eyes are the whole story, iris, catchlight, and almost no face left. | still, motion, av | — |
| `move_pull_to_solitude` | Pull to solitude | The camera pulls until the person is small in a huge place, architecture and weather dwarfing a single body. | still, motion, av | — |

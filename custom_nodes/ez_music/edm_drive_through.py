"""Drive-through 180s instrumental EDM takes.

Fictional act. Original arrangements. No living-artist names.
Hardcore but pure of heart: vast melody, then a ~30 s multi-instrument drop,
then the cycle repeats.
"""

from __future__ import annotations

from .edm_examples import (
    EDM_DURATION_S,
    EdmExample,
    _desc,
    drive_tags,
    format_edm_arrangement,
)


def _ex(
    slug: str,
    title: str,
    bpm: int,
    seed: int,
    prefix: str,
    take: str,
    lyrics: str,
    *tag_parts: str,
) -> EdmExample:
    return {
        "stem": f"music-edm-drive-through-{slug}-lab-example",
        "series": "drive-through",
        "title": title,
        "tags": drive_tags(*tag_parts, bpm=bpm),
        "bpm": bpm,
        "duration": EDM_DURATION_S,
        "seed": seed,
        "prefix": prefix,
        "description": _desc(take),
        "lyrics": lyrics,
    }


OPEN_LANE_LYRICS = format_edm_arrangement(
    intro="night road glow\nhorizon wide\nDrive-through rolling",
    melody=(
        "open lane ahead\n"
        "vast sky pulling\n"
        "pluck notes climb\n"
        "wide pads bloom\n"
        "heart stays clean\n"
        "future bass lift\n"
        "supersaw far\n"
        "the road is ours"
    ),
    build=(
        "filter opens\n"
        "snare roll up\n"
        "bass tease in\n"
        "hats go tight\n"
        "risers climb\n"
        "kick about to hit"
    ),
    drop=(
        "thirty second drop\n"
        "heavy sub bass\n"
        "layered reese\n"
        "complex hats\n"
        "supersaw stack\n"
        "kick punch hard\n"
        "sidechain pump\n"
        "multi instrument wreck\n"
        "pure heart still\n"
        "Drive-through holds the wheel"
    ),
    break_=(
        "horizon again\n"
        "vast pads return\n"
        "heart in the lead\n"
        "open road glow\n"
        "melody breathes\n"
        "plucks come home"
    ),
    build2=(
        "snare roll back\n"
        "filter wider\n"
        "bass knocks once\n"
        "risers scream\n"
        "hats double\n"
        "now"
    ),
    drop2=(
        "thirty second drop\n"
        "heavier sub\n"
        "stacked reese choir\n"
        "glitch fills\n"
        "layered kicks\n"
        "complex lead weave\n"
        "hard but clean\n"
        "the lane stays open"
    ),
    outro="kick out\nhorizon left\nDrive-through gone\nyeah",
)

NIGHT_WINDOW_LYRICS = format_edm_arrangement(
    intro="glass glow\ncity grid\nDrive-through waiting",
    melody=(
        "night window open\n"
        "chord lights blink\n"
        "vast street below\n"
        "warm bass hum\n"
        "heart in the glass\n"
        "house keys lift\n"
        "the lane still calls"
    ),
    build=(
        "offbeat hats\n"
        "tom fill up\n"
        "filter sweep\n"
        "kick on the lip\n"
        "bass knocks twice"
    ),
    drop=(
        "thirty second drop\n"
        "four-on-the-floor\n"
        "heavy kick punch\n"
        "rolling bass house\n"
        "stabs in layers\n"
        "claps on the two\n"
        "complex percussion\n"
        "sub in the ribs\n"
        "pure of heart\n"
        "window still open"
    ),
    break_=(
        "open glass again\n"
        "vast grid humming\n"
        "heart chord holds\n"
        "city breathes slow\n"
        "melody in the pane"
    ),
    build2=(
        "hats skip faster\n"
        "tom roll back\n"
        "bass tease low\n"
        "kick counts in"
    ),
    drop2=(
        "thirty second drop\n"
        "harder kick\n"
        "layered bass growl\n"
        "stab choir\n"
        "offbeat wreck\n"
        "multi hat weave\n"
        "clean but loud\n"
        "the window holds"
    ),
    outro="kick fade\nglass dark\nDrive-through out\nyeah",
)

ON_RAMP_LYRICS = format_edm_arrangement(
    intro="merge lights\nengine count\nDrive-through climbing",
    melody=(
        "on-ramp rising\n"
        "vast night ahead\n"
        "screech lead far\n"
        "open throttle heart\n"
        "pads in the climb\n"
        "the merge is clean"
    ),
    build=(
        "kick split tease\n"
        "snare roll hard\n"
        "reverse swell\n"
        "hats go iron\n"
        "count it in"
    ),
    drop=(
        "thirty second drop\n"
        "reverse bass hit\n"
        "kick split hard\n"
        "screech stack\n"
        "layered gabber punch\n"
        "complex lead weave\n"
        "sub in the chest\n"
        "pure heart drive\n"
        "the ramp stays true"
    ),
    break_=(
        "horizon still\n"
        "open merge glow\n"
        "heart in the climb\n"
        "vast road waiting\n"
        "melody breathes"
    ),
    build2=(
        "split kick tease\n"
        "roll even louder\n"
        "screech winds up\n"
        "now"
    ),
    drop2=(
        "thirty second drop\n"
        "harder reverse bass\n"
        "double kick split\n"
        "screech choir\n"
        "layered percussion\n"
        "complex wreck\n"
        "clean grit\n"
        "ramp holds the line"
    ),
    outro="kick out\nmerge done\nDrive-through gone\nyeah",
)

SKYLINE_PASS_LYRICS = format_edm_arrangement(
    intro="gated air\ncity crown\nDrive-through lifting",
    melody=(
        "skyline pass\n"
        "vast pads open\n"
        "rolling bass far\n"
        "heart in the gate\n"
        "pickup glow\n"
        "the horizon sings"
    ),
    build=(
        "pickup fill\n"
        "snare climb\n"
        "gate tightens\n"
        "bass rolls up\n"
        "hands in the air"
    ),
    drop=(
        "thirty second drop\n"
        "trance kick drive\n"
        "rolling bass wall\n"
        "gated pad stack\n"
        "complex arps\n"
        "supersaw choir\n"
        "layered hats\n"
        "pure heart lift\n"
        "the skyline holds"
    ),
    break_=(
        "open gate again\n"
        "vast city crown\n"
        "heart pad holds\n"
        "horizon still wide\n"
        "melody returns"
    ),
    build2=(
        "pickup harder\n"
        "snare taller\n"
        "gate snaps\n"
        "roll into it"
    ),
    drop2=(
        "thirty second drop\n"
        "harder trance kick\n"
        "bass wall thicker\n"
        "arp weave\n"
        "pad choir wreck\n"
        "complex fill stack\n"
        "clean uplift\n"
        "pass stays open"
    ),
    outro="kick fade\ncrown dark\nDrive-through out\nyeah",
)

FREIGHT_PULSE_LYRICS = format_edm_arrangement(
    intro="rail click\namen far\nDrive-through counting",
    melody=(
        "freight pulse low\n"
        "vast yard lights\n"
        "amen hush\n"
        "open reese tease\n"
        "heart in the count\n"
        "the line runs true"
    ),
    build=(
        "break chops\n"
        "snare edit\n"
        "bass growl in\n"
        "hats go razor\n"
        "drop incoming"
    ),
    drop=(
        "thirty second drop\n"
        "neurofunk reese\n"
        "amen wreck\n"
        "layered drums\n"
        "complex edits\n"
        "sub punches\n"
        "multi bass stack\n"
        "pure heart freight\n"
        "the pulse stays hard"
    ),
    break_=(
        "horizon rails\n"
        "vast yard glow\n"
        "open count\n"
        "heart click\n"
        "melody in the dark"
    ),
    build2=(
        "chop tighter\n"
        "edit sharper\n"
        "reese winds\n"
        "now"
    ),
    drop2=(
        "thirty second drop\n"
        "heavier neuro\n"
        "double amen\n"
        "glitch weave\n"
        "layered kick\n"
        "complex bass choir\n"
        "clean wreckage\n"
        "freight holds the night"
    ),
    outro="amen stop\nrails dark\nDrive-through gone\nyeah",
)

HEART_LANE_LYRICS = format_edm_arrangement(
    intro="soft lead\nclean night\nDrive-through honest",
    melody=(
        "heart lane open\n"
        "vast chord bed\n"
        "melodic bass lift\n"
        "plucks like hope\n"
        "the horizon waits\n"
        "pure of heart"
    ),
    build=(
        "filter swell\n"
        "snare up\n"
        "bass knocks kind\n"
        "hats gather\n"
        "here it comes"
    ),
    drop=(
        "thirty second drop\n"
        "heavy but clean\n"
        "layered bass hymn\n"
        "complex chords\n"
        "hard kick still\n"
        "multi lead weave\n"
        "sub with a soul\n"
        "heart stays loud\n"
        "the lane does not lie"
    ),
    break_=(
        "open heart again\n"
        "vast bed returns\n"
        "horizon hush\n"
        "melody kind\n"
        "the night still believes"
    ),
    build2=(
        "swell bigger\n"
        "snare taller\n"
        "bass kinder-hard\n"
        "count"
    ),
    drop2=(
        "thirty second drop\n"
        "harder clean bass\n"
        "chord choir\n"
        "layered hymn wreck\n"
        "complex kick\n"
        "multi instrument soul\n"
        "pure still\n"
        "heart lane holds"
    ),
    outro="kick rest\nheart open\nDrive-through out\nyeah",
)

OVERPASS_LYRICS = format_edm_arrangement(
    intro="concrete hush\nspace wide\nDrive-through under",
    melody=(
        "overpass open\n"
        "vast echo\n"
        "sparse pluck\n"
        "heart in the dark\n"
        "sub far away\n"
        "the span holds"
    ),
    build=(
        "half-time knock\n"
        "snare dry\n"
        "wobble tease\n"
        "space closes\n"
        "drop coming"
    ),
    drop=(
        "thirty second drop\n"
        "riddim wobble\n"
        "heavy sub crush\n"
        "layered growls\n"
        "complex syncopation\n"
        "metal hats\n"
        "multi bass wreck\n"
        "pure heart still\n"
        "the overpass shakes"
    ),
    break_=(
        "open span again\n"
        "vast concrete hush\n"
        "heart pluck\n"
        "horizon under\n"
        "melody thin and true"
    ),
    build2=(
        "knock harder\n"
        "wobble closer\n"
        "space gone\n"
        "now"
    ),
    drop2=(
        "thirty second drop\n"
        "deeper wobble\n"
        "double growl\n"
        "layered crush\n"
        "complex fill\n"
        "hard but clean\n"
        "span still stands"
    ),
    outro="wobble out\nspan dark\nDrive-through gone\nyeah",
)

SECOND_WAVE_LYRICS = format_edm_arrangement(
    intro="cycle in\nagain\nDrive-through repeats",
    melody=(
        "second wave coming\n"
        "vast first glow\n"
        "open motif\n"
        "heart remembers\n"
        "the drop will return\n"
        "that is the point"
    ),
    build=(
        "growl tease\n"
        "snare machine\n"
        "bass talks\n"
        "hats metal\n"
        "repeat incoming"
    ),
    drop=(
        "thirty second drop\n"
        "brostep growl\n"
        "layered bass talk\n"
        "complex mid wreck\n"
        "hard kick punch\n"
        "multi growl choir\n"
        "pure heart still\n"
        "the process repeats"
    ),
    break_=(
        "open motif back\n"
        "vast glow again\n"
        "heart knows this\n"
        "horizon same\n"
        "melody waits for two"
    ),
    build2=(
        "talk louder\n"
        "snare meaner\n"
        "growl wider\n"
        "again"
    ),
    drop2=(
        "thirty second drop\n"
        "second growl wave\n"
        "heavier talk\n"
        "layered mid stack\n"
        "complex punch\n"
        "repeat the wreck\n"
        "clean still\n"
        "the process holds"
    ),
    outro="growl stop\ncycle rest\nDrive-through out\nyeah",
)

KEEP_GOING_LYRICS = format_edm_arrangement(
    intro="climb start\nno quit\nDrive-through forward",
    melody=(
        "keep going up\n"
        "vast climb glow\n"
        "open hats\n"
        "heart in the rise\n"
        "trap lift far\n"
        "the road does not end"
    ),
    build=(
        "808 knock\n"
        "hat roll\n"
        "riser scream\n"
        "bass half-time\n"
        "drop soon"
    ),
    drop=(
        "thirty second drop\n"
        "hybrid trap bass\n"
        "layered 808\n"
        "complex hat chop\n"
        "hard kick\n"
        "multi synth wreck\n"
        "pure heart grind\n"
        "keep going still"
    ),
    break_=(
        "open climb again\n"
        "vast rise\n"
        "heart forward\n"
        "horizon not done\n"
        "melody refuses stop"
    ),
    build2=(
        "808 louder\n"
        "hats denser\n"
        "riser longer\n"
        "go"
    ),
    drop2=(
        "thirty second drop\n"
        "harder hybrid bass\n"
        "double 808\n"
        "hat wreck weave\n"
        "layered kick\n"
        "complex climb punch\n"
        "clean grit\n"
        "still going"
    ),
    outro="808 rest\nclimb holds\nDrive-through gone\nyeah",
)

TUNNEL_BASS_LYRICS = format_edm_arrangement(
    intro="tile echo\ndark run\nDrive-through inside",
    melody=(
        "tunnel bass hum\n"
        "vast black ahead\n"
        "open pulse\n"
        "heart in the echo\n"
        "offbeat tick\n"
        "the tube holds"
    ),
    build=(
        "hat machine\n"
        "tom tunnel\n"
        "filter acid\n"
        "kick on the lip\n"
        "in"
    ),
    drop=(
        "thirty second drop\n"
        "hard techno kick\n"
        "industrial bass\n"
        "layered offbeats\n"
        "complex acid\n"
        "metal percussion\n"
        "multi rumble\n"
        "pure heart in the dark\n"
        "the tunnel drives"
    ),
    break_=(
        "open echo again\n"
        "vast black glow\n"
        "heart tick\n"
        "horizon as a light\n"
        "melody in tile"
    ),
    build2=(
        "machine faster\n"
        "acid closer\n"
        "kick meaner\n"
        "now"
    ),
    drop2=(
        "thirty second drop\n"
        "harder techno\n"
        "double industrial\n"
        "acid weave\n"
        "layered rumble\n"
        "complex metal\n"
        "clean dark\n"
        "light at the end"
    ),
    outro="kick out\ntile dark\nDrive-through gone\nyeah",
)

HORIZON_KICK_LYRICS = format_edm_arrangement(
    intro="raw air\nfar line\nDrive-through aiming",
    melody=(
        "horizon kick far\n"
        "vast raw pad\n"
        "open screech seed\n"
        "heart in the aim\n"
        "the line is clean"
    ),
    build=(
        "kick tease\n"
        "snare iron\n"
        "screech wind\n"
        "hats razor\n"
        "split soon"
    ),
    drop=(
        "thirty second drop\n"
        "rawstyle kick split\n"
        "heavy reverse bass\n"
        "layered screech\n"
        "complex punch chain\n"
        "multi lead wreck\n"
        "pure heart still\n"
        "the horizon hits"
    ),
    break_=(
        "open line again\n"
        "vast raw air\n"
        "heart aim\n"
        "horizon waiting\n"
        "melody thin"
    ),
    build2=(
        "split tease\n"
        "iron louder\n"
        "screech screams\n"
        "hit"
    ),
    drop2=(
        "thirty second drop\n"
        "harder raw kick\n"
        "double reverse\n"
        "screech choir\n"
        "layered punch\n"
        "complex split wreck\n"
        "clean fire\n"
        "horizon holds"
    ),
    outro="kick rest\nline dark\nDrive-through out\nyeah",
)

CLEAN_WRECKAGE_LYRICS = format_edm_arrangement(
    intro="dust settle\nstill standing\nDrive-through honest",
    melody=(
        "clean wreckage glow\n"
        "vast after-light\n"
        "open chords\n"
        "heart in the ruin\n"
        "bass kind and hard\n"
        "the frame still holds"
    ),
    build=(
        "bits gather\n"
        "snare stack\n"
        "bass coils\n"
        "hats complex\n"
        "wreck incoming"
    ),
    drop=(
        "thirty second drop\n"
        "complex bass music\n"
        "layered instruments\n"
        "heavy sub\n"
        "multi growl and lead\n"
        "hard kick clean\n"
        "pure heart wreck\n"
        "nothing cruel in it"
    ),
    break_=(
        "open after-light\n"
        "vast frame\n"
        "heart still here\n"
        "horizon through dust\n"
        "melody stands"
    ),
    build2=(
        "bits denser\n"
        "coil tighter\n"
        "stack taller\n"
        "now"
    ),
    drop2=(
        "thirty second drop\n"
        "heavier complex bass\n"
        "more layers\n"
        "lead and growl weave\n"
        "hard kick still clean\n"
        "multi instrument crash\n"
        "pure still\n"
        "wreckage holds kind"
    ),
    outro="dust rest\nframe stands\nDrive-through gone\nyeah",
)

EXIT_SEVEN_LYRICS = format_edm_arrangement(
    intro="sign flash\nriff seed\nDrive-through turning",
    melody=(
        "exit seven open\n"
        "vast interchange\n"
        "adventure riff\n"
        "heart in the turn\n"
        "electro pluck\n"
        "the ramp is ours"
    ),
    build=(
        "arp faster\n"
        "clap count\n"
        "bass analog\n"
        "filter open\n"
        "take the exit"
    ),
    drop=(
        "thirty second drop\n"
        "complextro bass\n"
        "layered analog\n"
        "complex arp wreck\n"
        "hard clap kick\n"
        "multi riff stack\n"
        "pure heart turn\n"
        "exit seven hits"
    ),
    break_=(
        "open interchange\n"
        "vast sign glow\n"
        "heart riff\n"
        "horizon of ramps\n"
        "melody turns kind"
    ),
    build2=(
        "arp denser\n"
        "analog closer\n"
        "clap meaner\n"
        "now"
    ),
    drop2=(
        "thirty second drop\n"
        "harder complextro\n"
        "double analog\n"
        "arp weave\n"
        "layered riff\n"
        "complex punch\n"
        "clean turn\n"
        "seven still open"
    ),
    outro="riff out\nsign dark\nDrive-through gone\nyeah",
)

WIDE_OPEN_LYRICS = format_edm_arrangement(
    intro="mainstage air\nhands up\nDrive-through huge",
    melody=(
        "wide open field\n"
        "vast supersaw\n"
        "festival heart\n"
        "horizon crowd glow\n"
        "the night is a room"
    ),
    build=(
        "tom run\n"
        "snare wall\n"
        "saw swell\n"
        "kick on deck\n"
        "hands"
    ),
    drop=(
        "thirty second drop\n"
        "big room kick\n"
        "festival bass\n"
        "layered supersaw\n"
        "complex fill\n"
        "hard clap\n"
        "multi lead wreck\n"
        "pure heart huge\n"
        "the field opens"
    ),
    break_=(
        "open field again\n"
        "vast saw hush\n"
        "heart in the crowd\n"
        "horizon still\n"
        "melody wide"
    ),
    build2=(
        "tom bigger\n"
        "saw taller\n"
        "wall louder\n"
        "now"
    ),
    drop2=(
        "thirty second drop\n"
        "harder big room\n"
        "double saw choir\n"
        "festival wreck\n"
        "layered kick\n"
        "complex mainstage\n"
        "clean huge\n"
        "still wide open"
    ),
    outro="kick rest\nfield dark\nDrive-through out\nyeah",
)

DAWN_RECEIPT_LYRICS = format_edm_arrangement(
    intro="pink sky\nwindow slip\nDrive-through paying",
    melody=(
        "dawn receipt glow\n"
        "vast sunrise pads\n"
        "open house keys\n"
        "heart in the slip\n"
        "progressive climb\n"
        "the night clocks out"
    ),
    build=(
        "hat four-four\n"
        "tom sunrise\n"
        "bass warm\n"
        "filter gold\n"
        "peak soon"
    ),
    drop=(
        "thirty second drop\n"
        "peak-time house\n"
        "warm heavy bass\n"
        "layered keys\n"
        "complex percussion\n"
        "hard kick still kind\n"
        "multi instrument dawn\n"
        "pure heart receipt\n"
        "the sky pays out"
    ),
    break_=(
        "open sunrise\n"
        "vast pink\n"
        "heart slip\n"
        "horizon gold\n"
        "melody clocks in"
    ),
    build2=(
        "hats busier\n"
        "gold louder\n"
        "bass warmer\n"
        "now"
    ),
    drop2=(
        "thirty second drop\n"
        "harder peak house\n"
        "double key stack\n"
        "layered percussion\n"
        "warm wreck\n"
        "complex sunrise punch\n"
        "clean gold\n"
        "receipt still open"
    ),
    outro="kick fade\nsky paid\nDrive-through gone\nyeah",
)

EDM_DRIVE_THROUGH: tuple[EdmExample, ...] = (
    _ex(
        "open-lane",
        "open lane",
        148,
        191,
        "ez_edm_drive_openlane",
        "open-lane future bass",
        OPEN_LANE_LYRICS,
        "future bass",
        "supersaw",
        "stacked 808",
        "pluck melody",
        "heavy drop",
    ),
    _ex(
        "night-window",
        "night window",
        140,
        193,
        "ez_edm_drive_night",
        "night-window bass house",
        NIGHT_WINDOW_LYRICS,
        "bass house",
        "four on the floor",
        "rolling bass",
        "offbeat hats",
        "heavy kick",
    ),
    _ex(
        "on-ramp",
        "on-ramp",
        150,
        197,
        "ez_edm_drive_onramp",
        "on-ramp hardstyle",
        ON_RAMP_LYRICS,
        "hardstyle",
        "reverse bass",
        "kick split",
        "screech lead",
        "heavy drop",
    ),
    _ex(
        "skyline-pass",
        "skyline pass",
        138,
        199,
        "ez_edm_drive_skyline",
        "skyline-pass uplifting trance",
        SKYLINE_PASS_LYRICS,
        "uplifting trance",
        "gated pads",
        "rolling bass",
        "pickup drum fill",
        "supersaw",
    ),
    _ex(
        "freight-pulse",
        "freight pulse",
        174,
        211,
        "ez_edm_drive_freight",
        "freight-pulse drum and bass",
        FREIGHT_PULSE_LYRICS,
        "drum and bass",
        "neurofunk",
        "amen break",
        "reese bass",
        "complex edits",
    ),
    _ex(
        "heart-lane",
        "heart lane",
        140,
        223,
        "ez_edm_drive_heart",
        "heart-lane melodic bass",
        HEART_LANE_LYRICS,
        "melodic bass",
        "clean heavy sub",
        "chord hymn",
        "pluck lead",
        "hard kick",
    ),
    _ex(
        "overpass",
        "overpass",
        140,
        227,
        "ez_edm_drive_overpass",
        "overpass riddim dubstep",
        OVERPASS_LYRICS,
        "riddim",
        "dubstep",
        "wobble bass",
        "half-time",
        "heavy sub",
    ),
    _ex(
        "second-wave",
        "second wave",
        150,
        241,
        "ez_edm_drive_second",
        "second-wave brostep",
        SECOND_WAVE_LYRICS,
        "brostep",
        "bass growl",
        "mid-range talk",
        "heavy drop",
        "complex growl",
    ),
    _ex(
        "keep-going",
        "keep going",
        150,
        251,
        "ez_edm_drive_keep",
        "keep-going hybrid trap",
        KEEP_GOING_LYRICS,
        "hybrid trap",
        "808 bass",
        "hat rolls",
        "festival drop",
        "heavy 808",
    ),
    _ex(
        "tunnel-bass",
        "tunnel bass",
        145,
        257,
        "ez_edm_drive_tunnel",
        "tunnel-bass hard techno",
        TUNNEL_BASS_LYRICS,
        "hard techno",
        "industrial bass",
        "offbeat hats",
        "acid line",
        "heavy kick",
    ),
    _ex(
        "horizon-kick",
        "horizon kick",
        160,
        263,
        "ez_edm_drive_horizon",
        "horizon-kick rawstyle",
        HORIZON_KICK_LYRICS,
        "rawstyle",
        "kick split",
        "reverse bass",
        "screech lead",
        "heavy drop",
    ),
    _ex(
        "clean-wreckage",
        "clean wreckage",
        140,
        269,
        "ez_edm_drive_wreck",
        "clean-wreckage complex bass",
        CLEAN_WRECKAGE_LYRICS,
        "complex bass",
        "layered instruments",
        "heavy sub",
        "growl and lead",
        "hard kick",
    ),
    _ex(
        "exit-seven",
        "exit seven",
        140,
        233,
        "ez_edm_drive_exit",
        "exit-seven complextro",
        EXIT_SEVEN_LYRICS,
        "complextro",
        "electro house",
        "analog bass",
        "complex arp",
        "heavy drop",
    ),
    _ex(
        "wide-open",
        "wide open",
        150,
        239,
        "ez_edm_drive_wide",
        "wide-open big room",
        WIDE_OPEN_LYRICS,
        "big room",
        "festival",
        "supersaw",
        "four on the floor",
        "heavy kick",
    ),
    _ex(
        "dawn-receipt",
        "dawn receipt",
        128,
        229,
        "ez_edm_drive_dawn",
        "dawn-receipt progressive house",
        DAWN_RECEIPT_LYRICS,
        "progressive house",
        "peak time",
        "warm bass",
        "house keys",
        "four on the floor",
    ),
)

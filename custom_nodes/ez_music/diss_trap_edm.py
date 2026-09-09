"""Trap/EDM-pack 180s Nill Bye vs Rake diss takes.

Rap over club beds. Same dry-booth vocal as the lab catalog.
Fictional MCs only. Original lyrics. No living-artist names. No autotune.
"""

from __future__ import annotations

from .diss_examples import (
    DISS_DURATION_S,
    DissExample,
    _desc,
    format_diss_lyrics,
    nill_tags,
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
) -> DissExample:
    return {
        "stem": f"music-rap-nill-bye-{slug}-lab-example",
        "series": "trap-edm",
        "title": title,
        "tags": nill_tags(*tag_parts, bpm=bpm),
        "bpm": bpm,
        "duration": DISS_DURATION_S,
        "seed": seed,
        "prefix": prefix,
        "description": _desc(take),
        "lyrics": lyrics,
    }


FALSE_DROP_LYRICS = format_diss_lyrics(
    intro="riser fake\nsnare tease\ndrop ducks",
    chorus=(
        "False drop\n"
        "You teased a climax\n"
        "Nill Bye waits on mute\n"
        "Rake sold a dummy\n"
        "Build-up mouth, kick never lands\n"
        "Your peak was a dummy cue"
    ),
    verses=(
        "Rake rides a riser with no punch\n"
        "Talks a climax that never lands\n"
        "Snare roll climbing, the kick stays mute\n"
        "That's a tease in a headliner stance\n"
        "I wait for the drop, you sell the wait\n"
        "You sell a peak, then you duck the hit\n"
        "Hats in a panic, the bass won't commit\n"
        "Dummy cue flashing, the floor won't sit\n"
        "Nill Bye counts the missing punch\n"
        "Your whole build is a dummy stunt\n"
        "Mouth on a riser, the downbeat hides",
        "You count eight bars like a promise made\n"
        "Then you ghost when the kick should land\n"
        "Hats keep rolling, the downbeat sleeps\n"
        "Dark pad waiting while the promise leaks\n"
        "I want a punch that can move the floor\n"
        "You want a riser and a cheaper roar\n"
        "Dummy peak flashing in a cheap display\n"
        "The floor is waiting, you fade away\n"
        "Nill Bye clocks the dummy cue\n"
        "Rake, your climax never came through\n"
        "Build-up mouth with a mute debut",
        "The riser screams like a headline lie\n"
        "Then it dies when the kick should fly\n"
        "I came for a drop, you brought a tease\n"
        "You sold a peak with a dummy lease\n"
        "Hats still climbing, the bass still hid\n"
        "That's a climax you never did\n"
        "False drop king on a borrowed thrill\n"
        "The downbeat never paid the bill\n"
        "Nill Bye reading the mute that stays\n"
        "Rake on a riser that never pays\n"
        "Tease, then stall, then a cheap goodbye",
        "Morning comes, the tease looks small\n"
        "The kick you promised never called\n"
        "Hats still ticking, the dummy still queued\n"
        "Riser exhausted, the floor unmoved\n"
        "Nill Bye files the fake climax\n"
        "Rake packed a peak in a dummy pack\n"
        "Build-up mouth, the downbeat ducked\n"
        "Your whole set was a riser stuck\n"
        "Put the tease back in the crate\n"
        "Your false drop cannot carry weight\n"
        "Mute remains when the riser drains",
    ),
    outro="riser dies\nmute holds\ndummy filed\nyeah",
)


VELVET_ROPE_LYRICS = format_diss_lyrics(
    intro="stanchion up\nlist blank\nwristband fake",
    chorus=(
        "Velvet rope\n"
        "Blank name on the rail\n"
        "Nill Bye holds the list\n"
        "Rake poses VIP\n"
        "Empty queue, clipboard dry\n"
        "No stamp, no entry"
    ),
    verses=(
        "Rake leans on velvet like a borrowed stanchion\n"
        "Name not written, he still wants the zone\n"
        "Stanchion up, the clipboard stares\n"
        "Your VIP is a vacant chair\n"
        "I hold the list, you hold a pose\n"
        "Wristband missing, the bouncer knows\n"
        "Camera ready, the queue is none\n"
        "That's a king with a lanyard undone\n"
        "Nill Bye reading a blank-name card\n"
        "Your whole guest is a velvet shard\n"
        "Pose for a rope that will not part",
        "You sell a lanyard like a bloodline pass\n"
        "Then you fold when they check the glass\n"
        "Festival bass, the rope stays shut\n"
        "Your whole cool is a borrowed strut\n"
        "I stamp the real, you stamp a ghost\n"
        "The velvet knows who paid the most\n"
        "Bring a name or don't join the line\n"
        "The rope is short and the list is mine\n"
        "Nill Bye keeps the clipboard tight\n"
        "Rake posing VIP with no invite\n"
        "Empty chair humming under the lights\n"
        "Your whole flex is a velvet slight",
        "You treat the rope like a personality\n"
        "Then you crash when they ask for ID\n"
        "I clock the stanchion, I clock the queue\n"
        "I clock a brand that never came through\n"
        "Empty list humming under the bass\n"
        "That's a VIP with a vacant face\n"
        "Nill Bye filing the blank-name slot\n"
        "Rake looping a pose the door forgot\n"
        "Keep the pose, lose the velvet\n"
        "The list don't owe you a credit\n"
        "Wristband missing, the bouncer shrugs\n"
        "Your soundtrack snapped on a velvet tug",
        "You print a lanyard off a printer\n"
        "Then you ask the rope to be nicer\n"
        "Festival lights on an empty rail\n"
        "Pose for a camera that will not hail\n"
        "I keep the clipboard, you keep the skit\n"
        "You name a hit that the door won't admit\n"
        "Nill Bye shutting the empty slot\n"
        "Rake wants a throne for a name he dropped\n"
        "Put the lanyard back on the tray\n"
        "The rope don't score a vacant play\n"
        "Stanchion stays, the file is closed\n"
        "Your soundtrack snapped on a velvet close",
    ),
    outro="stanchion stays\nbouncer shrugs\ncut\nyeah",
)


FOG_MACHINE_LYRICS = format_diss_lyrics(
    intro="jet hiss\nhaze thick\nstage missing",
    chorus=(
        "Fog machine\n"
        "The stage is missing\n"
        "Nill Bye reads the haze\n"
        "Rake hides in the jet\n"
        "Fog for a missing set\n"
        "Haze is your alibi"
    ),
    verses=(
        "Rake hits the jet like a headline act\n"
        "Talks a set that the stage subtracts\n"
        "Laser hats cut a missing band\n"
        "I count the jets, you count the cheers\n"
        "I map the haze, you map the mirrors\n"
        "Fog for a missing opening act\n"
        "Distorted bass on an empty track\n"
        "Nill Bye staring through a rented plume\n"
        "You smiling through a highlight fume\n"
        "Show the set or leave the floor\n"
        "Haze covering a missing encore",
        "You treat the haze like a body double\n"
        "Then you vanish when the jet is trouble\n"
        "I count the canisters, you count the stares\n"
        "Hold the nozzle, don't sell the plume\n"
        "Your cool is vapor, mine is a tune\n"
        "Talk a set like a rented reel\n"
        "Then you crash out when the jet gets real\n"
        "Nill Bye clocking what the haze keeps in\n"
        "Rake with a name-tag spin\n"
        "Show the body or kill the jet\n"
        "The jet is cheap and the haze falls flat",
        "You sell the haze like a limited drop\n"
        "Then you fold when the playlist pops\n"
        "I clock the jet, I clock the pose\n"
        "I clock a brand in borrowed clothes\n"
        "Nill Bye reading a missing-set log\n"
        "Rake looping a jet like a catalog\n"
        "Set is due, the merch is not\n"
        "You wrapped a skip in a foggy shot\n"
        "Keep the jet, lose the alibi\n"
        "Hats stay put, the boast walks\n"
        "Haze for a show that never starts",
        "You write the set like a product sheet\n"
        "Then you ask the jet for relief\n"
        "I hold the nozzle, you hold the bit\n"
        "I name the haze, you name the hit\n"
        "Rage hats on a high-key play\n"
        "Nill Bye mad at the costume jet\n"
        "Rake at the end of a rented set\n"
        "You want a throne for a rented pain\n"
        "Put the canister back on the tray\n"
        "The jet don't score a vacant play\n"
        "Jet cuts out, the file is closed\n"
        "Your soundtrack snapped on a haze close",
    ),
    outro="jet off\nhaze clears\nstage denied\nyeah",
)


GUEST_LIST_LYRICS = format_diss_lyrics(
    intro="clipboard dry\ndoor shut\nname missing",
    chorus=(
        "Guest list closed\n"
        "You are not on it\n"
        "Nill Bye checks the door\n"
        "Rake argues the mark\n"
        "Clipboard miss, no pass\n"
        "Name never made the ink"
    ),
    verses=(
        "Rake taps the cowbell like a password\n"
        "No name inked, just a leftover\n"
        "I ask the door, you send a spin\n"
        "I ask the clipboard, you dodge the pen\n"
        "Crunchy sample on a missing sign\n"
        "Drifted bass on a nameless vine\n"
        "Nill Bye marking a nameless slot\n"
        "Bring the pass or lose the knot\n"
        "Cowbell ticks, the door stays locked\n"
        "Talk that life with an empty badge\n"
        "Phonk hush when the bouncer bags it",
        "You name a plus-one like a golden ticket\n"
        "That's a sticker, not a permit\n"
        "You name a booth like a lifetime pin\n"
        "That's a vibe with a paper skin\n"
        "Cowbell tick, dry booth, no gloss\n"
        "I hold the ink, you hold a rumor\n"
        "Nill Bye stamping at the door\n"
        "Rake rides a ghost pass at the door\n"
        "Write the surname, drop the clipboard\n"
        "No surname, no corner\n"
        "Phonk truth, the stack is light\n"
        "Your plus-one never made it back",
        "Cowbell cracking on an empty rail\n"
        "You drew a king with marker art\n"
        "The bouncer squints at a smudged ID\n"
        "You swear the manager blessed the three\n"
        "Nill Bye talking from the doorway\n"
        "Rake keeps folding when the ink goes slack\n"
        "Name is filed, the pass is gone\n"
        "Lights stay on, the name is wrong\n"
        "Clipboard flipping, your slot was never\n"
        "The door don't owe you a forever\n"
        "Blank field where the surname sits\n"
        "That's a boast with no visits",
        "Rake at the blank-name rail\n"
        "Nill Bye posting the door law\n"
        "No plus-one, no afterparty\n"
        "Just a selfie and a borrowed cheer\n"
        "Entry missing, it did not persist\n"
        "Cut the lore, keep the name on the list\n"
        "Door closed, that is the quote\n"
        "The bouncer stands, the thread is smoke\n"
        "He still leaking through a broken joke\n"
        "Blank name filed, the cowbell dries\n"
        "Show the pass or step aside\n"
        "Phonk hush, the rumor died",
    ),
    outro="clipboard shut\ndoor locked\ncut\nyeah",
)


SPARKLER_LYRICS = format_diss_lyrics(
    intro="stick lit\npretty burn\nyield zero",
    chorus=(
        "Sparkler science\n"
        "Pretty burn, no yield\n"
        "Nill Bye wants a reaction\n"
        "Rake sold a stick\n"
        "Sparks are not a product\n"
        "Ash is all you built"
    ),
    verses=(
        "Rake lights a stick like a breakthrough\n"
        "Talks a reaction he never knew\n"
        "Sparks climb pretty, the yield stays zero\n"
        "That's a party trick in a tourist hero\n"
        "I want a product, you want a fizz\n"
        "You want a photo of a pretty hiss\n"
        "Wire burning, nothing in the pan\n"
        "Ash on the table, that was the plan\n"
        "Nill Bye weighing a dead sparkler\n"
        "Your whole reaction is a tourist dollar\n"
        "Pretty burn, then the stick goes dull",
        "You name a spark like a published find\n"
        "Then you fold when I ask the yield behind\n"
        "Hats keep ticking, the stick keeps wasting\n"
        "Dark pads waiting while the ash is tasting\n"
        "I want a gram that can hit a scale\n"
        "You want a glitter that can fill a tale\n"
        "Sparkler king on a wire diet\n"
        "No compound, just a camera riot\n"
        "Nill Bye bagging the pretty waste\n"
        "Rake calling fireworks a dataset\n"
        "Burn looks busy, the pan stays clean",
        "Sparks jump left, then they jump right\n"
        "Still no product in the morning light\n"
        "I clock the wire, I clock the ash\n"
        "I clock a flex with a tourist splash\n"
        "Nill Bye filing a zero-yield blotter\n"
        "Rake still selling a backyard starter\n"
        "Pretty hiss dressed as a breakthrough\n"
        "The stick burned out, and so did you\n"
        "Hold the sparkler or drop the claim\n"
        "Your reaction never left the frame\n"
        "Ash in a pile, the boast looks tiny",
        "Morning hits, the wire is cold\n"
        "Glitter gone, the story sold\n"
        "Hats go quiet, the stick gets binned\n"
        "No yield logged, the boast was skinned\n"
        "Nill Bye tagging a tourist burn\n"
        "Rake still calling it a return\n"
        "Sparkler king with a rented fizz\n"
        "The product never paid the biz\n"
        "File the ash, keep the stick\n"
        "Pretty chemistry is a party trick\n"
        "Wire dead, the pan stays even",
    ),
    outro="stick dead\nash cools\nyield none\nyeah",
)


BOTTLE_SERVICE_LYRICS = format_diss_lyrics(
    intro="magnum rented\ntab borrowed\nice theater",
    chorus=(
        "Bottle service\n"
        "Rented magnum, fake tab\n"
        "Nill Bye reads the check\n"
        "Rake toasts on a stranger\n"
        "Ice bucket theater\n"
        "The bill is not yours"
    ),
    verses=(
        "Rake pops a cork like he owns the suite\n"
        "Tab in a name that he never wore\n"
        "Ice bucket shining, the magnum's rented\n"
        "Waiter hovering, the flex invented\n"
        "Piano stab, the sidechain pumps\n"
        "You toast a life that the ledger dumps\n"
        "I read the check, you read the booth\n"
        "Four-on-the-floor while you spend perfume\n"
        "Nill Bye adding the stranger's check\n"
        "Your whole bottle is a costume flex\n"
        "Cork in the air, the ice is theater",
        "You name a vintage like a bloodline cork\n"
        "Then you freeze when they ask who signed\n"
        "House hats ticking, the ice stays pretty\n"
        "Sidechain pumping a borrowed city\n"
        "I want a tab that can match the toast\n"
        "You want a photo with a magnum ghost\n"
        "Rented bottles in a stranger's script\n"
        "You sip a flex that the card won't tip\n"
        "Nill Bye circling the fake account\n"
        "Rake toasting debt like a fountain\n"
        "Ice melts faster than the story does",
        "Waiter knows the name on the slip\n"
        "It is not yours, you still take a sip\n"
        "I clock the bucket, I clock the pour\n"
        "I clock a king at a rented rail\n"
        "Nill Bye filing the borrowed tab\n"
        "Rake still posing with a magnum grab\n"
        "House lights low, the toast looks expensive\n"
        "The ledger says you are a guest detective\n"
        "Keep the ice, lose the costume pour\n"
        "Your service never paid the store\n"
        "Cork on the table, the bill on a stranger",
        "Morning comes, the ice is water\n"
        "Magnum gone, the toast is fodder\n"
        "Hats go quiet, the waiter blinks\n"
        "Tab bounced back on a trail of plugs\n"
        "Nill Bye bagging a rented cork\n"
        "Rake still calling it a masterwork\n"
        "Bottle king with a costume sip\n"
        "The card declined on a phantom tip\n"
        "Put the magnum back in the cage\n"
        "Your whole toast is a rented stage\n"
        "Ice dumped, the theater closes",
    ),
    outro="magnum back\ntab bounced\nice dumped\nyeah",
)


STROBE_CLAIM_LYRICS = format_diss_lyrics(
    intro="flash burst\nblink gone\nboast missing",
    chorus=(
        "Strobe claim\n"
        "Blink and the boast is gone\n"
        "Nill Bye stands in the dark\n"
        "Rake lives in a flash\n"
        "No substance, only pulse\n"
        "Your legend is a blink"
    ),
    verses=(
        "Rake talks big in a white-hot strobe\n"
        "Between the flashes, it's a cheap probe\n"
        "Dry kick ticking, the boast is a blink\n"
        "Acid line humming on a vanishing brink\n"
        "I wait in the dark for a solid pulse\n"
        "You only exist in a strobe convulse\n"
        "Hat offbeats catch a vanishing image\n"
        "That's a king with a disposable voltage\n"
        "Nill Bye standing when the bulbs go black\n"
        "Your whole claim is a strobe attack\n"
        "Flash, then nothing, then a cheaper flicker",
        "You sell a win like a lightning shutter\n"
        "Then you vanish when the blackout clutters\n"
        "Techno pulse, the flex is a phosphor\n"
        "Acid drip on a disappearing author\n"
        "I want a bar that can hold a minute\n"
        "You want a blink with a rumor in it\n"
        "Strobe claim king on a duty cycle\n"
        "No body there, just a white-hot idol\n"
        "Nill Bye timing the dark between flashes\n"
        "Rake melting soon as the bulbs go ashes\n"
        "Pulse looks busy, the substance flickers",
        "Flash left, flash right, still no fixture\n"
        "Your legend lives in a flicker picture\n"
        "I clock the dark, I clock the burst\n"
        "I clock a flex that the blackout cursed\n"
        "Nill Bye filing a blink-and-gone blot\n"
        "Rake still selling a strobe as plot\n"
        "White-hot hiss dressed as a brief\n"
        "The bulbs cut out, and so did the grief\n"
        "Hold the pulse or drop the strobe\n"
        "Your claim never sat in the globe\n"
        "Dark in the middle, the boast looks cheap",
        "House lights up, the strobe looks weak\n"
        "Blink erased, the legend's asleep\n"
        "Hats go even, the flash gets boxed\n"
        "No substance logged, the boast was foxed\n"
        "Nill Bye tagging a disposable burst\n"
        "Rake still calling it a universe\n"
        "Strobe king with a rented pulse\n"
        "The body never paid the dues\n"
        "File the blink, keep the dark\n"
        "Flash chemistry is a party spark\n"
        "Bulbs dead, the booth stays level",
    ),
    outro="flash dead\nblink filed\nboast gone\nyeah",
)


AMEN_RUMOR_LYRICS = format_diss_lyrics(
    intro="break empty\nfill missing\nrumor racing",
    chorus=(
        "Amen rumor\n"
        "Fast chop, empty bar\n"
        "Nill Bye wants a fill\n"
        "Rake loops a ghost\n"
        "Break with no answer\n"
        "Rumor riding the snare"
    ),
    verses=(
        "Rake chops an amen like a headline\n"
        "Talks a fill that he never signed\n"
        "Break racing, the barline's empty\n"
        "Sub reese humming on a rumor plenty\n"
        "I wait for the answer after the snare\n"
        "You loop the chop and you call it prayer\n"
        "Hats in a hurry, the fill won't click\n"
        "That's a king with a ghost in the stick\n"
        "Nill Bye counting the missing fill\n"
        "Your whole amen is a hollow drill\n"
        "Fast chop, then a cheaper hush",
        "You name a break like a vintage stamp\n"
        "Then you freeze when I ask who filled the gap\n"
        "Drum-and-bass ticking, the snare stays lonely\n"
        "Reese underneath on a story only\n"
        "I want a fill that can close the phrase\n"
        "You want a chop with a rumor glaze\n"
        "Amen king on a looped excuse\n"
        "No answer bar, just a flying ruse\n"
        "Nill Bye marking the empty bar\n"
        "Rake riding chops like a stolen car\n"
        "Break looks busy, the fill still lags",
        "Chop left, chop right, still no answer\n"
        "Your legend lives in a break you rented\n"
        "I clock the snare, I clock the gap\n"
        "I clock a flex with a missing clap\n"
        "Nill Bye filing a no-fill docket\n"
        "Rake still selling a break as canvas\n"
        "Ghost bar dressed as a lecture\n"
        "The chop runs out, and so do the verses\n"
        "Hold the amen or drop the mic\n"
        "Your rumor never sat in the kick\n"
        "Empty in the middle, the boast looks hollow",
        "Morning comes, the break is tired\n"
        "Fill never came, the rumor fired\n"
        "Hats go even, the chop gets shelved\n"
        "No answer logged, the boast was delved\n"
        "Nill Bye tagging a ghosted fill\n"
        "Rake still calling it a skill\n"
        "Amen king with a rented snare\n"
        "The bar never paid the fare\n"
        "File the chop, keep the gap\n"
        "Fast rumor is a party map\n"
        "Break dead, the booth stays sober",
    ),
    outro="break stops\nfill never\nrumor dies\nyeah",
)


WOBBLE_ALIBI_LYRICS = format_diss_lyrics(
    intro="LFO thick\ngrowl covering\nmiss hiding",
    chorus=(
        "Wobble alibi\n"
        "Bass covering the miss\n"
        "Nill Bye hears the hole\n"
        "Rake hides in the growl\n"
        "LFO is not an excuse\n"
        "Your alibi wobbles too"
    ),
    verses=(
        "Rake throws a wobble over a fumble\n"
        "Talks a landing that starts to crumble\n"
        "Half-time snare, the miss still sitting\n"
        "Growl so thick that the hole looks fitting\n"
        "I hear the gap when the LFO breathes\n"
        "You ride the bass like a stack of leaves\n"
        "Hats in a crawl, the excuse keeps moving\n"
        "That's a king with a cover he's proving\n"
        "Nill Bye picking the miss in the growl\n"
        "Your whole alibi is a wobble rag\n"
        "Bass looks busy, the landing ducks",
        "You name a drop like a courtroom oath\n"
        "Then you hide when the growl thins both\n"
        "Dubstep pulse, the flex won't settle\n"
        "Wobble drip on a vanishing metal\n"
        "I want a bar that can hold a landing\n"
        "You want a growl with a rumor standing\n"
        "Wobble king on a moving filter\n"
        "No landing there, just a sliding pillar\n"
        "Nill Bye timing the hole in the sweep\n"
        "Rake melting soon as the bass goes mild\n"
        "LFO busy, the substance stalls",
        "Growl left, growl right, still no core\n"
        "Your legend lives in a moving roar\n"
        "I clock the miss, I clock the sweep\n"
        "I clock a flex that the filter eats\n"
        "Nill Bye filing a covered-miss ledger\n"
        "Rake still selling a wobble as texture\n"
        "Moving hiss dressed as a sermon\n"
        "The bass cuts out, and so did the cover\n"
        "Hold the growl or drop the excuse\n"
        "Your alibi never sat in the juice\n"
        "Hole in the middle, the boast looks soggy",
        "House lights up, the wobble looks fake\n"
        "Growl erased, the legend's opaque\n"
        "Hats go even, the sweep gets packed\n"
        "No landing logged, the boast was cracked\n"
        "Nill Bye tagging a disposable growl\n"
        "Rake still calling it a vow\n"
        "Wobble king with a rented sweep\n"
        "The body never paid the keep\n"
        "File the sweep, keep the miss\n"
        "Bass cover is a party hiss\n"
        "LFO dead, the booth stays rigid",
    ),
    outro="growl cuts\nalibi fails\nmiss shows\nyeah",
)


SUPERSAW_FLEX_LYRICS = format_diss_lyrics(
    intro="detune stacked\npatch flexing\npaper missing",
    chorus=(
        "Supersaw flex\n"
        "Stacked detune, no paper\n"
        "Nill Bye asks for a patch note\n"
        "Rake flexes a unison\n"
        "Saw stack is not a resume\n"
        "Your flex is a preset"
    ),
    verses=(
        "Rake stacks a saw like a diploma\n"
        "Talks a paper he never authored\n"
        "Detune climbing, the resume's empty\n"
        "Pitched chords humming on a rumor surplus\n"
        "I ask for a patch, you send a flex\n"
        "You send a unison and you call it text\n"
        "Hats in a hurry, the paper won't print\n"
        "That's a king with a preset imprint\n"
        "Nill Bye reading a blank-patch file\n"
        "Your whole supersaw is costume vinyl\n"
        "Stacked detune, then a cheaper quiet",
        "You name a chord like a vintage bank\n"
        "Then you freeze when I ask who wrote the patch\n"
        "Future-bass ticking, the stack stays vacant\n"
        "Bass stacked under a borrowed fable\n"
        "I want a note that can close the measure\n"
        "You want a saw with a rumor varnish\n"
        "Supersaw king on a looped preset\n"
        "No paper trail, just a flying fib\n"
        "Nill Bye marking the empty patch\n"
        "Rake riding stacks like a stolen hatch\n"
        "Chord looks busy, the paper still idles",
        "Detune left, detune right, still no sheet\n"
        "Your legend lives in a preset you cheat\n"
        "I clock the stack, I clock the unison\n"
        "I clock a flex with a missing author\n"
        "Nill Bye filing a no-paper folder\n"
        "Rake still selling a saw as sculpture\n"
        "Ghost patch dressed as a pamphlet\n"
        "The stack runs out, and so do the boasts\n"
        "Hold the unison or drop the stack\n"
        "Your flex never sat in the rack\n"
        "Empty in the middle, the boast looks lazy",
        "Morning comes, the saw is weary\n"
        "Paper never came, the rumor faded\n"
        "Hats go even, the stack gets archived\n"
        "No note logged, the boast was carved\n"
        "Nill Bye tagging a ghosted patch\n"
        "Rake still calling it a catch\n"
        "Saw king with a rented chord\n"
        "The file never paid the board\n"
        "File the detune, keep the unison\n"
        "Stacked rumor is a party sticker\n"
        "Patch dead, the booth stays stacked",
    ),
    outro="detune dies\npatch folds\nflex filed\nyeah",
)


LASER_SHOW_LYRICS = format_diss_lyrics(
    intro="scanner on\ngobo fake\nlogos floating",
    chorus=(
        "Laser show\n"
        "Lights, no paper\n"
        "Nill Bye wants a set list\n"
        "Rake draws logos in haze\n"
        "Beams without a song\n"
        "Your show is a scanner"
    ),
    verses=(
        "Rake draws a logo in a rented beam\n"
        "Talks a set list he never schemed\n"
        "Scanner climbing on a fake gobo\n"
        "Analog bass on a rumor garnish\n"
        "I ask for a song, you send a gobo\n"
        "You send a haze and you call it promo\n"
        "Clap on two, the paper won't stick\n"
        "That's a king with a logo stencil\n"
        "Nill Bye reading a blank-set menu\n"
        "Your whole laser is costume tinsel\n"
        "Beams look busy, the song stays hidden",
        "You name a brand like a tunnel badge\n"
        "Then you freeze when I ask who played\n"
        "Electro ticking, the scanner stays parked\n"
        "Clap underneath on a story borrowed\n"
        "I want a list that can close the set\n"
        "You want a beam with a rumor net\n"
        "Laser king on a looped projector\n"
        "No paper trail, just a flying vector\n"
        "Nill Bye marking the empty truss\n"
        "Rake riding beams like a stolen plus\n"
        "Logo looks busy, the song still drifts",
        "Beam left, beam right, still no song\n"
        "Your legend lives in a gobo you hung\n"
        "I clock the scanner, I clock the truss\n"
        "I clock a flex with a missing chorus\n"
        "Nill Bye filing a no-set binder\n"
        "Rake still selling a beam as mural\n"
        "Ghost logo dressed as a flyer\n"
        "The haze runs out, and so do the captions\n"
        "Hold the scanner or drop the logo\n"
        "Your show never sat in the rafter\n"
        "Empty in the middle, the boast looks airy",
        "Morning comes, the beam is dim\n"
        "Song never came, the rumor rusted\n"
        "Hats go even, the gobo gets crated\n"
        "No list logged, the boast was dusted\n"
        "Nill Bye tagging a ghosted scanner\n"
        "Rake still calling it a banner\n"
        "Laser king with a rented logo\n"
        "The file never paid the truss\n"
        "File the beam, keep the haze\n"
        "Haze rumor is a party stencil\n"
        "Scanner dead, the booth stays still",
    ),
    outro="beams off\nlogos fade\npaper none\nyeah",
)


TWO_STEP_LYRICS = format_diss_lyrics(
    intro="shuffle left\nskip the one\nproof dodging",
    chorus=(
        "Two-step alibi\n"
        "Shuffle past the proof\n"
        "Nill Bye stands on the one\n"
        "Rake skips the downbeat\n"
        "Garage excuse, no landing\n"
        "Your two-step is a dodge"
    ),
    verses=(
        "Rake shuffles left when the one comes due\n"
        "Talks a landing he never walked through\n"
        "Organ stab, the proof stays skipped\n"
        "Sub bass humming while the downbeat's stripped\n"
        "I stand on the one, you skip the brick\n"
        "You sell a shuffle like a magic dodge\n"
        "Hats in a skip, the excuse keeps sliding\n"
        "That's a king with a dodge he's hiding\n"
        "Nill Bye planting a foot on the one\n"
        "Your two-step is a rumor sidestep\n"
        "Shuffle looks busy, the landing skips",
        "You name a step like a courtroom plea\n"
        "Then you skip when the proof walks in\n"
        "UK pulse, the flex won't tarry\n"
        "Organ drip on a disappearing dancer\n"
        "I want a bar that can hold the one\n"
        "You want a skip with a rumor tucked\n"
        "Two-step king on a shuffled cycle\n"
        "No landing there, just a shuffled idol\n"
        "Nill Bye timing the skip between\n"
        "Rake melting soon as the one goes slack\n"
        "Shuffle busy, the substance fades",
        "Skip left, skip right, still no downbeat\n"
        "Your legend lives in a shuffled line\n"
        "I clock the one, I clock the skip\n"
        "I clock a flex that the shuffle steals\n"
        "Nill Bye filing a skipped-beat record\n"
        "Rake still selling a two-step as craft\n"
        "Garage shuffle dressed as a riddle\n"
        "The organ cuts out, and so did the story\n"
        "Hold the one or drop the dodge\n"
        "Your two-step never sat in the brick\n"
        "Gap in the middle, the boast looks shuffled",
        "House lights up, the shuffle looks worn\n"
        "Skip erased, the legend's dim\n"
        "Hats go even, the dodge gets filed\n"
        "No landing logged, the boast was skipped\n"
        "Nill Bye tagging a disposable skip\n"
        "Rake still calling it a trip\n"
        "Garage king with a rented shuffle\n"
        "The shuffle never paid the brick\n"
        "File the skip, keep the one\n"
        "Shuffle chemistry is a party dodge\n"
        "Organ dead, the booth stays quiet",
    ),
    outro="shuffle stops\nskip exposed\ncut\nyeah",
)


JERSEY_BOUNCE_LYRICS = format_diss_lyrics(
    intro="squeaks up\nbounce hollow\nchops flying",
    chorus=(
        "Jersey bounce\n"
        "Bounce with no proof\n"
        "Nill Bye wants a body\n"
        "Rake chops an empty bed\n"
        "Squeaks without a claim\n"
        "Your bounce is a hollow"
    ),
    verses=(
        "Rake chops a squeak like a headline\n"
        "Talks a body that he never signed\n"
        "Bounce racing, the bedframe's empty\n"
        "Kick drums humming on a rumor plenty\n"
        "I wait for a body after the chop\n"
        "You loop the squeak and you call it pop\n"
        "Hats in a hurry, the proof won't land\n"
        "That's a king with a ghost in the bed\n"
        "Nill Bye counting the missing body\n"
        "Your whole bounce is a hollow copy\n"
        "Fast chop, then a cheaper silence",
        "You name a bounce like a clubbed-in win\n"
        "Then you freeze when I ask who lived in\n"
        "Jersey ticking, the mattress stays lonely\n"
        "Squeaks underneath on a story only\n"
        "I want a body that can close the phrase\n"
        "You want a squeak with a rumor glaze\n"
        "Bounce king on a looped bedframe\n"
        "No living bar, just a flying claim\n"
        "Nill Bye marking the empty bed\n"
        "Rake riding chops like a stolen thread\n"
        "Bounce looks busy, the proof still lags",
        "Chop left, chop right, still no body\n"
        "Your legend lives in a squeak you copied\n"
        "I clock the squeak, I clock the mattress\n"
        "I clock a flex with a missing address\n"
        "Nill Bye filing a no-body docket\n"
        "Rake still selling a bounce as product\n"
        "Ghost bed dressed as a lecture\n"
        "The squeak runs out, and so do the verses\n"
        "Hold the bounce or drop the mic\n"
        "Your rumor never sat in the bed\n"
        "Empty in the middle, the boast looks copied",
        "Morning comes, the bounce is tired\n"
        "Body never came, the rumor fired\n"
        "Hats go even, the bounce gets shelved\n"
        "No claim logged, the boast was delved\n"
        "Nill Bye tagging a ghosted squeak\n"
        "Rake still calling it a technique\n"
        "Jersey king with a rented bed\n"
        "The bar never paid the thread\n"
        "File the squeak, keep the gap\n"
        "Fast bounce is a party map\n"
        "Squeak dead, the booth stays sober",
    ),
    outro="bounce stops\nchops mute\nhollow filed\nyeah",
)


KICK_SPLIT_LYRICS = format_diss_lyrics(
    intro="reverse punch\nsplit dummy\ndata missing",
    chorus=(
        "Kick-split myth\n"
        "Reverse punch, no data\n"
        "Nill Bye wants both halves\n"
        "Rake splits a rumor\n"
        "Dummy split, empty arms\n"
        "Your kick is a story"
    ),
    verses=(
        "Rake splits a kick like a magic trick\n"
        "Talks two halves that he never picked\n"
        "Reverse racing, the data stays dummy\n"
        "Screech lead humming on a rumor tummy\n"
        "I wait for the other arm after the punch\n"
        "You loop the split and you call it crunch\n"
        "Hats in a hurry, the halves won't lock\n"
        "That's a king with a ghost in the sock\n"
        "Nill Bye counting the missing half\n"
        "Your whole kick-split is a rumor craft\n"
        "Reverse punch, then a cheaper hush",
        "You name a split like a vintage stamp\n"
        "Then you freeze when I ask who logged the ramp\n"
        "Hardstyle ticking, the arms stay lonely\n"
        "Screech underneath on a story only\n"
        "I want a half that can close the phrase\n"
        "You want a kick with a rumor glaze\n"
        "Split king on a looped reverse\n"
        "No second arm, just a flying verse\n"
        "Nill Bye marking the empty split\n"
        "Rake riding reverse like a stolen hit\n"
        "Kick looks busy, the data still lags",
        "Half left, half right, still no partner\n"
        "Your legend lives in a reverse barter\n"
        "I clock the reverse, I clock the dummy\n"
        "I clock a flex with a missing tummy\n"
        "Nill Bye filing a no-data folder\n"
        "Rake still selling a split as sculpture\n"
        "Ghost arm dressed as a pamphlet\n"
        "The punch runs out, and so do the boasts\n"
        "Hold the kick or drop the stack\n"
        "Your rumor never sat in the rack\n"
        "Empty in the middle, the boast looks dummy",
        "Morning comes, the reverse is weary\n"
        "Half never came, the rumor faded\n"
        "Hats go even, the split gets archived\n"
        "No data logged, the boast was carved\n"
        "Nill Bye tagging a ghosted punch\n"
        "Rake still calling it a crunch\n"
        "Kick king with a rented half\n"
        "The arm never paid the craft\n"
        "File the reverse, keep the dummy\n"
        "Dummy split is a party sticker\n"
        "Screech dead, the booth stays stacked",
    ),
    outro="reverse dies\nsplit dummy\ndata none\nyeah",
)


UPLIFT_RUMOR_LYRICS = format_diss_lyrics(
    intro="hands lifted\npads gated\nnumbers flat",
    chorus=(
        "Uplifting rumor\n"
        "Hands up, numbers flat\n"
        "Nill Bye waits for lift\n"
        "Rake sells a pickup\n"
        "Pads gated, no rise\n"
        "Your rumor never lifts"
    ),
    verses=(
        "Rake throws his hands like a headline\n"
        "Talks a lift that he never signed\n"
        "Pickup racing, the numbers stay flat\n"
        "Gated pads humming on a rumor vat\n"
        "I wait for the rise after the fill\n"
        "You loop the hands and you call it skill\n"
        "Hats in a hurry, the lift won't click\n"
        "That's a king with a ghost in the pad\n"
        "Nill Bye counting the missing rise\n"
        "Your whole pickup is a rumor plateau\n"
        "Hands up, then a cheaper hush",
        "You name a lift like a vintage crest\n"
        "Then you freeze when I ask who logged the rest\n"
        "Trance ticking, the pads stay gated\n"
        "Rolling bass on a story fated\n"
        "I want a rise that can close the phrase\n"
        "You want a hand with a rumor glaze\n"
        "Uplift king on a looped plateau\n"
        "No number move, just a flying halo\n"
        "Nill Bye marking the empty lift\n"
        "Rake riding hands like a stolen drift\n"
        "Pickup looks busy, the numbers still lag",
        "Hand left, hand right, still no altitude\n"
        "Your legend lives in a pickup salute\n"
        "I clock the pad, I clock the plateau\n"
        "I clock a flex with a missing halo\n"
        "Nill Bye filing a no-lift binder\n"
        "Rake still selling a pickup as mural\n"
        "Ghost rise dressed as a flyer\n"
        "The pad runs out, and so do the captions\n"
        "Hold the hands or drop the logo\n"
        "Your rumor never sat in the rafter\n"
        "Empty in the middle, the boast looks gated",
        "Morning comes, the pickup is dim\n"
        "Lift never came, the rumor rusted\n"
        "Hats go even, the hands get crated\n"
        "No rise logged, the boast was dusted\n"
        "Nill Bye tagging a ghosted pad\n"
        "Rake still calling it a fad\n"
        "Trance king with a rented lift\n"
        "The number never paid the truss\n"
        "File the pickup, keep the haze\n"
        "Hands-up rumor is a party stencil\n"
        "Pads dead, the booth stays still",
    ),
    outro="hands drop\npads gate\nlift denied\nyeah",
)


DISS_TRAP_EDM: tuple[DissExample, ...] = (
    _ex(
        "false-drop",
        "false drop",
        140,
        107,
        "ez_rap_nill_drop",
        "false-drop roast of Rake",
        FALSE_DROP_LYRICS,
        "dark trap",
        "808 bass",
        "rapid hi-hats",
        "half-time",
    ),
    _ex(
        "velvet-rope",
        "velvet rope",
        150,
        109,
        "ez_rap_nill_rope",
        "velvet-rope roast of Rake",
        VELVET_ROPE_LYRICS,
        "festival trap",
        "808 bass",
        "crowd-bed",
        "supersaw stab",
    ),
    _ex(
        "fog-machine",
        "fog machine",
        148,
        113,
        "ez_rap_nill_fog",
        "fog-machine roast of Rake",
        FOG_MACHINE_LYRICS,
        "rage",
        "distorted 808",
        "laser hats",
    ),
    _ex(
        "guest-list",
        "guest list",
        132,
        127,
        "ez_rap_nill_guest",
        "guest-list roast of Rake",
        GUEST_LIST_LYRICS,
        "phonk",
        "cowbell",
        "drifted 808",
        "crunchy sample",
    ),
    _ex(
        "sparkler",
        "sparkler science",
        145,
        131,
        "ez_rap_nill_spark",
        "sparkler roast of Rake",
        SPARKLER_LYRICS,
        "trap",
        "808 bass",
        "rapid hats",
        "dark pads",
    ),
    _ex(
        "bottle-service",
        "bottle service",
        126,
        137,
        "ez_rap_nill_bottle",
        "bottle-service roast of Rake",
        BOTTLE_SERVICE_LYRICS,
        "house",
        "four-on-the-floor",
        "piano stab",
        "sidechain bass",
    ),
    _ex(
        "strobe-claim",
        "strobe claim",
        132,
        139,
        "ez_rap_nill_strobe",
        "strobe-claim roast of Rake",
        STROBE_CLAIM_LYRICS,
        "techno",
        "dry kick",
        "hat offbeats",
        "acid line",
    ),
    _ex(
        "amen-rumor",
        "amen rumor",
        174,
        149,
        "ez_rap_nill_amen",
        "amen-rumor roast of Rake",
        AMEN_RUMOR_LYRICS,
        "drum and bass",
        "amen break",
        "sub reese",
    ),
    _ex(
        "wobble-alibi",
        "wobble alibi",
        140,
        151,
        "ez_rap_nill_wobble",
        "wobble-alibi roast of Rake",
        WOBBLE_ALIBI_LYRICS,
        "dubstep",
        "wobble bass",
        "half-time snare",
    ),
    _ex(
        "supersaw-flex",
        "supersaw flex",
        148,
        157,
        "ez_rap_nill_saw",
        "supersaw-flex roast of Rake",
        SUPERSAW_FLEX_LYRICS,
        "future bass",
        "supersaw",
        "pitched synth chords",
        "808 bass",
    ),
    _ex(
        "laser-show",
        "laser show",
        128,
        163,
        "ez_rap_nill_laser",
        "laser-show roast of Rake",
        LASER_SHOW_LYRICS,
        "electro house",
        "analog bass",
        "clap on 2 and 4",
    ),
    _ex(
        "two-step",
        "two-step alibi",
        130,
        167,
        "ez_rap_nill_twostep",
        "two-step roast of Rake",
        TWO_STEP_LYRICS,
        "UK garage",
        "shuffled hats",
        "organ stab",
        "sub bass",
    ),
    _ex(
        "jersey-bounce",
        "jersey bounce",
        140,
        173,
        "ez_rap_nill_jersey",
        "jersey-bounce roast of Rake",
        JERSEY_BOUNCE_LYRICS,
        "jersey club",
        "chopped percussion",
        "bed squeaks",
        "kick drums",
    ),
    _ex(
        "kick-split",
        "kick-split myth",
        150,
        179,
        "ez_rap_nill_kick",
        "kick-split roast of Rake",
        KICK_SPLIT_LYRICS,
        "hardstyle",
        "reverse bass",
        "kick split",
        "screech lead",
    ),
    _ex(
        "uplift-rumor",
        "uplifting rumor",
        138,
        181,
        "ez_rap_nill_uplift",
        "uplifting-rumor roast of Rake",
        UPLIFT_RUMOR_LYRICS,
        "trance",
        "gated pads",
        "rolling bass",
        "pickup drum fill",
    ),
)

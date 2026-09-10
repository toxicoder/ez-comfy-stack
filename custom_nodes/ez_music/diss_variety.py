"""Style-pack 180s Nill Bye vs Rake diss takes (non-trap, non-EDM beds).

Fictional MCs only. Original lyrics. No living-artist names.
Same dry-booth vocal tags as the lab catalog.
"""

from __future__ import annotations

from .diss_examples import (
    DISS_DURATION_S,
    DissExample,
    _desc,
    format_diss_lyrics,
    nill_output_prefix,
    nill_tags,
)

VARIETY_PHASE = 1


def _ex(
    slug: str,
    title: str,
    bpm: int,
    seed: int,
    take: str,
    lyrics: str,
    *tag_parts: str,
) -> DissExample:
    return {
        "stem": f"music-rap-nill-bye-{slug}-lab-example",
        "series": "variety",
        "title": title,
        "tags": nill_tags(*tag_parts, bpm=bpm),
        "bpm": bpm,
        "duration": DISS_DURATION_S,
        "seed": seed,
        "phase": VARIETY_PHASE,
        "prefix": nill_output_prefix(title, VARIETY_PHASE),
        "description": _desc(take),
        "lyrics": lyrics,
    }


CITATION_NEEDED_LYRICS = format_diss_lyrics(
    intro="brushed snare\nsource missing\nNill Bye citing",
    chorus=(
        "Citation needed\n"
        "Nill Bye stamps the ibid\n"
        "Rake with a blank cite\n"
        "No DOI in the thread\n"
        "Jazz hop, the field is bare\n"
        "A screenshot is not a cite"
    ),
    verses=(
        "Rake drops a claim with no cite\n"
        "No footnote, just a boast\n"
        "I ask the source, you stall\n"
        "I ask the issue, you dodge\n"
        "Muted horn on a missing cite\n"
        "Upright bass on a ghosted site\n"
        "Nill Bye citing what you hide\n"
        "He sent a screenshot, no DOI\n"
        "ibid blank, the volume vanished\n"
        "Your paper is a dangling pawn\n"
        "Bring a DOI or step aside",
        "You treat a handle like a cite\n"
        "That's a username, not a write\n"
        "You treat a high like a journal prize\n"
        "That's a vibe with no ISSN\n"
        "Brushed drums, the booth stays matte\n"
        "I hold the book, you hold a bluff\n"
        "Nill Bye stamping every byte\n"
        "Rake riding a ghost cite\n"
        "Write the author, drop the throne\n"
        "No issue year, no cornerstone\n"
        "Jazz hop truth, the stack is slack\n"
        "Your scholarship never came back",
        "Trumpet mute on a rumor grid\n"
        "You drew a king with crayon ink\n"
        "Nill Bye talking from the annex\n"
        "Rake folds when the cite goes blank\n"
        "Feelings filed, the source has left\n"
        "Lights stay on, the cite is wrong\n"
        "Bring a footnote, drop the skit\n"
        "One of us sourced, one of us split\n"
        "Science will not barter cites\n"
        "Your claim arrived late\n"
        "Blank field where the volume sits\n"
        "That's a boast with no exhibits",
        "Rake at the blank-cite gap\n"
        "Nill Bye posting the footnote law\n"
        "No author listed, no issue year\n"
        "Just a screenshot and borrowed cheer\n"
        "Footnote missing, it did not persist\n"
        "Keep the cite on the working list\n"
        "Citation closed, that is the mark\n"
        "The record stands, the thread is vapor\n"
        "He still leaking through a broken yoke\n"
        "Blank cite filed, the horn goes dry\n"
        "Show the paper or step aside\n"
        "Jazz hop closed, the rumor died",
    ),
    outro="source missing\nblank cite filed\ncut\nyeah",
)

P_HACKING_LYRICS = format_diss_lyrics(
    intro="synth bass\ncherry pick\nNill Bye slicing",
    chorus=(
        "P-hacking king\n"
        "Your night is a slice\n"
        "Nill Bye on the uncut batch\n"
        "Rake paid the price\n"
        "Pick the crest, hide the miss\n"
        "That is a p-hack, kid"
    ),
    verses=(
        "Rake ran the hours till it smiled\n"
        "Threw the rest in a junk-file pile\n"
        "Talkbox keys on a cherry plot\n"
        "You kept the spike, you dumped the lot\n"
        "I want the full run, you send a slice\n"
        "I want the miss that you won't splice\n"
        "Nill Bye mad at a trimmed readout\n"
        "He hid a miss in a rented cult\n"
        "Dry claps pop, your curve is cooked\n"
        "G-funk bounce on a cherry hook\n"
        "Show the misses or sit aside\n"
        "The slice you sold is a drought",
        "You slice the hours till the curve looks ripe\n"
        "Then you crash when I ask the reel\n"
        "Girls as points you decided to keep\n"
        "Nights as trophies you put to sleep\n"
        "Rake p-hacks a p of none\n"
        "Nill Bye running the count till done\n"
        "Talkbox lead, the boast stays cheap\n"
        "Synth bass waiting to cash the cheat\n"
        "Bring the raw file, drop the throne\n"
        "Cherry-pick science is inverted\n"
        "I log the trash you stuffed below\n"
        "Your whole paper is a highlight reel",
        "I ask the n, you send a taste\n"
        "I ask the miss, you change the case\n"
        "Underpowered, overclaimed\n"
        "That is the brand you tried to keep\n"
        "Nill Bye talking from the plot grid\n"
        "Rake keeps folding when the notes get sparse\n"
        "You flex first, then you hide the miss\n"
        "That's a p-hack loop I have mapped\n"
        "Cut the slice, keep the batch\n"
        "P-hack drought, now pay the debt\n"
        "Hide a miss, the flex looks huge\n"
        "Show a miss, the flex looks cheap",
        "Rake at the junk-file bin\n"
        "Nill Bye posting the uncut law\n"
        "You want a trophy from a trim\n"
        "I want a line that survives the audit\n"
        "Hide the miss, the flex looks huge\n"
        "Show the miss, the flex looks cheap\n"
        "I walk in with the uncut stack\n"
        "You walk in with a rumor pack\n"
        "The slicing stops, the legend slumps\n"
        "Numbers shift when the junk-file tilts\n"
        "He still picking through the range\n"
        "P-hack closed on a cooked exchange",
    ),
    outro="slice denied\nfull set in\ncut\nyeah",
)

NULL_RESULT_LYRICS = format_diss_lyrics(
    intro="rimshot\noffbeat\nNill Bye gauging",
    chorus=(
        "Null result, flex found none\n"
        "Your boast came back vacant\n"
        "Nill Bye on the empty claim\n"
        "Rake lost the bounce\n"
        "Organ bubble, rumor hush\n"
        "Reggae truth, the flex is nil"
    ),
    verses=(
        "Rake swore the flex would land\n"
        "Offbeat guitar, your curve is sand\n"
        "Reggae bounce on an empty boast\n"
        "Rimshot ticks, you look the same\n"
        "You talk a high like a measured crest\n"
        "I run the test, your curve is dust\n"
        "Nill Bye repeats the vacant trial\n"
        "He sits in denial, the organ mild\n"
        "Rimshot ticks, the flex is gone\n"
        "Club-sample will not hold on\n"
        "Show the work or sit this round\n"
        "Null on cool, that is the route",
        "I log the chatter, I log the walk\n"
        "I log the crash at the end of the talk\n"
        "Your legend lives in a chat-thread haze\n"
        "My legend lives in a measured cadence\n"
        "Null result on the cool-guy flex-out\n"
        "All that smoke and you still look vacant\n"
        "Rake flexing a sample too slight\n"
        "Nill Bye repeating until it's right\n"
        "Organ bubble, the boast goes still\n"
        "Science calm, the rumor ill\n"
        "Bring a method, bring a citation-trail\n"
        "Or get bounced from the lecture rail",
        "I graph the chatter, I graph the dip\n"
        "I graph the rumor on a lecture strip\n"
        "You treat a high like a plotted crest\n"
        "That's a spike that will not persist\n"
        "Nill Bye speaking from the bench once\n"
        "Rake keeps folding at the first hitch\n"
        "Null on cool, null on the title\n"
        "Club-talk p-value losing vital\n"
        "Trial two, same vacant yield\n"
        "Your legend fails the consult field\n"
        "Offbeat truth, your flex is drained\n"
        "Retract the night, the rumor warped",
        "Reviewer light on a rumor sketch\n"
        "You drew a monarch with crayon stretch\n"
        "Nill Bye testing from the bench once more\n"
        "Rake in denial with a borrowed oar\n"
        "Bring a method, drop the fable\n"
        "Science stays when the club's unable\n"
        "Board wiped clean, your curve is warped\n"
        "Null result, the rumor spent\n"
        "Cut the trial, file the memo\n"
        "Empty flex, that is the echo\n"
        "He still claiming everyone\n"
        "Null result when the test is done",
    ),
    outro="flex found none\nnull result filed\ncut\nyeah",
)

EXPIRED_REAGENT_LYRICS = format_diss_lyrics(
    intro="rhodes warm\ndate passed\nNill Bye dating",
    chorus=(
        "Expired reagent\n"
        "Your cool is past date\n"
        "Nill Bye reads the printed stamp\n"
        "Rake showed up late\n"
        "Shelf-life gone, the drip is stale\n"
        "Neo-soul truth, rumor in the bin"
    ),
    verses=(
        "Rake pops a flask with a faded stamp\n"
        "Talks a high like he bottled the amp\n"
        "I read the stamp, the month is skewed\n"
        "Your whole brand is a leftover hymn\n"
        "Soft snare, warm bass, dry booth\n"
        "I hold the vial, you hold the spoof\n"
        "Nill Bye mad at a dated sheen\n"
        "He wilts when the numbers convene\n"
        "Chemistry talk, a science tote\n"
        "One of us measured, one of us bolted\n"
        "Toss the bottle, keep the readout\n"
        "Your whole cool is a rented porch",
        "You name a night like a fresh solvent\n"
        "Then you crash when the clock is sound\n"
        "Rhodes hum low, the boast is stale\n"
        "Sad-boy mask on an expired yarn\n"
        "Rake with a yellowed label hanging\n"
        "Nill Bye clocking what the dates are cancelling\n"
        "Bring a batch that survives the month\n"
        "You want a caption, then you crest\n"
        "Printed date on a dusty shelf\n"
        "Expired reagent, you bottled yourself\n"
        "Shelf-life of drip is a short parade\n"
        "I dump the flask, you want it replayed",
        "Warm bass under a cork gone dry\n"
        "You sold a vintage that would not fly\n"
        "Nill Bye reading the tiny print\n"
        "Rake still sipping a ghost of a hint\n"
        "Yellowed tape on a cloudy vial\n"
        "Your cool curdled after a while\n"
        "Neo-soul keys, the boast is dated\n"
        "I file the batch, you want it fated\n"
        "Toss the reagent, keep the ledger\n"
        "Past-date drip is a borrowed treasure\n"
        "He still pouring a week-old mix\n"
        "I stamp expired on the bag of tricks",
        "Rake at the dusty shelf once more\n"
        "Nill Bye posting the expiry then\n"
        "Cool past the printed date you hid\n"
        "A leftover song in a cloudy lid\n"
        "Shelf-life gone, the flask is waste\n"
        "You wanted a toast from a spoiled taste\n"
        "Rhodes stay warm, the drip is over\n"
        "I cork the tale, you play the rover\n"
        "Date-stamp wins, the rumor curdles\n"
        "Expired reagent, pay the guilt\n"
        "He still hunting a usable drop\n"
        "I close the cabinet, the selling halts",
    ),
    outro="date passed\nflask tossed\ncut\nyeah",
)

LAB_SAFETY_LYRICS = format_diss_lyrics(
    intro="live drums\nhood open\nNill Bye warning",
    chorus=(
        "Lab safety\n"
        "Goggles on, you ducked the drill\n"
        "Nill Bye on the overdrive riff\n"
        "Rake skipped the hood for a thrill\n"
        "Rap-rock stomp, the visor stays\n"
        "No goggles, no mic today"
    ),
    verses=(
        "Rake skipped the goggles for a look\n"
        "Walked the hood like a fashion book\n"
        "Live drums hit, the siren cries\n"
        "You treated a drill like a punchline prize\n"
        "Overdriven guitar on a splash risk\n"
        "I clamp the line, you chase a disc\n"
        "Nill Bye warning from the visor brim\n"
        "He laughs at a drill he would not trim\n"
        "Crowd stomp under a skipped alarm\n"
        "Your cool is a burn on an ungloved arm\n"
        "Hood wide open, the latch undone\n"
        "Lab safety is not a joke, son",
        "You posed at the shield for a candid frame\n"
        "Then you ducked the drill when the siren came\n"
        "Rake with a visor hanging loose\n"
        "Nill Bye tightening the clamp on the juice\n"
        "Live kit pounding, the splash is raw\n"
        "You wanted a riff more than a seal\n"
        "Goggles scuffed on a borrowed hook\n"
        "I run the drill from the safety book\n"
        "Skip the hood, you skip the right\n"
        "Rap-rock truth in a strobe-less light\n"
        "Stomp the floor, keep the visor clamped\n"
        "Your thrill is a fine and a writeup",
        "Siren loops while you chase a solo\n"
        "I want a latch that will actually hold, though\n"
        "Nill Bye counting the skipped-drill tally\n"
        "Rake still treating the hood like an alley\n"
        "Overdrive snarls, the clamp is locked\n"
        "You wanted applause from a wet duet\n"
        "Goggles fogged from a laugh you faked\n"
        "I wipe the lens, you want it baked\n"
        "Lab safety is a stomp, not a skit\n"
        "You ducked the drill, now sit\n"
        "Shield up, the riff can pause\n"
        "No visor, no debate",
        "Rake at the open hood once more\n"
        "Nill Bye posting the safety then\n"
        "Goggles first, the guitar can pause\n"
        "You wanted a crowd for a reckless gait\n"
        "Skipped-drill king with a scuffed-up shield\n"
        "I file the warning, you want it repealed\n"
        "Live drums close, the latch clicks shut\n"
        "Your fashion walk was a splash-risk rut\n"
        "Hood stays down, the visor holds\n"
        "Lab safety outlasts the encore days\n"
        "He still posing without the gear\n"
        "I pull the plug on the reckless skit",
    ),
    outro="drill skipped\ngoggles on\ncut\nyeah",
)

RUMOR_MILL_LYRICS = format_diss_lyrics(
    intro="metal percussion\nmill turning\nNill Bye weighing",
    chorus=(
        "Rumor mill\n"
        "Gossip ground till the hopper jammed\n"
        "Nill Bye on the measured grind\n"
        "Rake fed the mill and got slammed\n"
        "Industrial truth, the sprocket stalls\n"
        "Weigh the claim or leave the mill"
    ),
    verses=(
        "Rake fed the rumor mill a boast\n"
        "Metal percussion on a gossip roast\n"
        "Hopper full of a second-hand yarn\n"
        "I weigh the grain, you weigh the sale\n"
        "Distorted bass on a conveyor fib\n"
        "You ground a whisper into a supply\n"
        "Nill Bye weighing what the mill spat out\n"
        "He smiles at a rumor he cannot route\n"
        "Turbine hums, the sprocket slips\n"
        "Your cool is a grind with no receipts\n"
        "Industrial hop, the press is loud-ish\n"
        "Measurement waits while the gossip rushes",
        "You poured a whisper into the hopper\n"
        "Then you danced when the rumor got proper\n"
        "Rake at the mill with a borrowed crank\n"
        "Nill Bye stopping the gear in a clank\n"
        "Metal on metal, the gossip thins\n"
        "I want a mass, you want a win's\n"
        "Conveyor jammed on a recycled quote\n"
        "You sold a grind as a measured blip\n"
        "Rumor mill closed when the scale is true\n"
        "Your hopper empty, the sprocket chewed\n"
        "Weigh the grain or kill the press\n"
        "Industrial truth, the rest is mess",
        "Turbine rumor versus a weighed-out gram\n"
        "You wanted a mill more than a exam\n"
        "Nill Bye filing the measured grind\n"
        "Rake still feeding the hopper blind\n"
        "Distorted bass, the gear is stripped\n"
        "Your gossip crop is a factory script\n"
        "Sprocket stalls, the conveyor seizes\n"
        "I log a mass, you log a prize\n"
        "Rumor mill is a mill, not a proofing\n"
        "You ground a nothing into a roofing\n"
        "Press goes quiet, the hopper yawns\n"
        "He still cranking for leftover dawns",
        "Rake at the jammed mill hatch\n"
        "Nill Bye posting the weigh-in score\n"
        "Gossip ground till the turbine seized\n"
        "You wanted a legend the scale just teased\n"
        "Industrial hop, the sprocket rusts\n"
        "I keep the mass, you keep the gusts\n"
        "Hopper empty, the rumor starved\n"
        "Your mill ran hot and the claim got carved\n"
        "Metal percussion, the press is done\n"
        "Measurement wins, the gossip's none\n"
        "He still oiling a silent gear\n"
        "Rumor mill closed, disappear",
    ),
    outro="mill jammed\nrumor weighed\ncut\nyeah",
)

GYM_SELFIE_LYRICS = format_diss_lyrics(
    intro="log drum\ncamera up\nNill Bye tallying",
    chorus=(
        "Gym selfie\n"
        "Camera first, the reps can wait\n"
        "Nill Bye on the counted set\n"
        "Rake posed a plate for the bait\n"
        "Afrobeat truth, the shutter lied\n"
        "Do the work or lose the selfie"
    ),
    verses=(
        "Rake posed a gym selfie mid-rep\n"
        "Log drum knocking while he saved the step\n"
        "Camera up before the bar even moved\n"
        "I count the reps, you count the views\n"
        "Shekere shake on a borrowed pump\n"
        "Your lats are a filter, your form is a dump\n"
        "Nill Bye counting what the rack can prove\n"
        "He smiles at a shutter he cannot move\n"
        "Guitar stab, the chalk is fake\n"
        "You wanted a frame more than a break\n"
        "Pose versus reps, the camera won\n"
        "Gym selfie closed when the work's not done",
        "You curled a look for a story stack\n"
        "Then you racked the bar after one weak pack\n"
        "Rake with a selfie before the sweat\n"
        "Nill Bye logging the reps you forget\n"
        "Log drum low, the shutter clicks\n"
        "I want a set, you want a mix\n"
        "Chalk on the hands, none on the bar\n"
        "Your pump is a costume, your form bizarre\n"
        "Afrobeat bounce, the plate is light\n"
        "You lifted a lens, not a honest lift\n"
        "Camera before the work, that's the brand\n"
        "Gym selfie dust on an unused stand",
        "Shekere ticks while you chase a angle\n"
        "I want a squat that can actually dangle\n"
        "Nill Bye reading the unused rack\n"
        "Rake still posing with a towel on his back\n"
        "Guitar stab, the rest is skipped\n"
        "You sold a pump that the film had clipped\n"
        "Reps unpaid, the selfie cashed\n"
        "I keep the count, you keep it mashed\n"
        "Form collapsed for a prettier crop\n"
        "That's a gym selfie, not a drop\n"
        "Plate still cold, the shutter warm\n"
        "He flexed a story, I flexed a form",
        "Rake at the mirror with the camera lit\n"
        "Nill Bye posting the unpaid reps\n"
        "Gym selfie first, the rack can idle\n"
        "You wanted a like for a half-done plate\n"
        "Log drum fades, the chalk is dry\n"
        "I close the count, you ask me why\n"
        "Shutter closed, the reps still due\n"
        "Pose versus work, I pick the true\n"
        "Afrobeat out, the selfie wilts\n"
        "Do the set or lose the prize\n"
        "He still hunting a flattering beam\n"
        "I rack the truth on a quieter team",
    ),
    outro="shutter closed\nreps unpaid\ncut\nyeah",
)

RENTED_DRIP_LYRICS = format_diss_lyrics(
    intro="analog growl\nreturn-by\nNill Bye tagging",
    chorus=(
        "Rented drip\n"
        "Return-by tag on a costume cool\n"
        "Nill Bye on the analog bass\n"
        "Rake leased a look for the vestibule\n"
        "Synthwave neon, the zipper talks\n"
        "Scan the tag or lose the drip"
    ),
    verses=(
        "Rake wore a rented drip to strut\n"
        "Return-by tag hanging off the next\n"
        "Analog bass on a neon lease\n"
        "I scan the stitch, you scan for peace\n"
        "Gated snare, the zipper shines\n"
        "Your cool is a costume with overdue fines\n"
        "Nill Bye tagging what the hanger kept\n"
        "He struts in a look that the shop still prepped\n"
        "Synthwave pads on a mannequin loan\n"
        "You rented a myth and you called it a throne\n"
        "Deposit due when the lights go mild\n"
        "Rented drip is a weekend child",
        "You cinched a jacket with a plastic tag\n"
        "Then you froze when I read the bag\n"
        "Rake in a costume cool he cannot keep\n"
        "Nill Bye clocking the return-by beep\n"
        "Neon pads, the stitch is temporary\n"
        "I want a fit that is actually hereditary\n"
        "Hanger still warm from the shop you robbed\n"
        "Your analog glow is a leased-out job\n"
        "Synthwave night on a zipper lease\n"
        "Scan the tag, the swagger will cease\n"
        "Return-by morning, the drip goes home\n"
        "You were a mannequin in a rented poem",
        "Gated snare while you chase a invoice\n"
        "I want a stitch that can actually join us\n"
        "Nill Bye reading the tiny tag\n"
        "Rake still posing in a costume brag\n"
        "Analog bass, the deposit waits\n"
        "You sold a neon that the shop dictates\n"
        "Zipper talks, the hanger scores\n"
        "Rented drip is a weekend's sins\n"
        "Lease expired, the pads go dim\n"
        "I file the receipt, you want a hymn\n"
        "Mannequin cool on a borrowed rack\n"
        "He still hoping I will not track",
        "Rake at the return-by desk-less bay\n"
        "Nill Bye posting the tag anyway\n"
        "Costume cool with a scanned-out stitch\n"
        "You wanted a forever from a weekend pitch\n"
        "Synthwave fades, the zipper rusts\n"
        "I keep the receipt, you keep the gusts\n"
        "Rented drip back on the hanger hook\n"
        "Your neon story is a shopkeeper's book\n"
        "Analog out, the lease is lapsed\n"
        "Scan the tag, the myth is untrue\n"
        "He still asking to extend the night-wear\n"
        "I close the till on the costume affair",
    ),
    outro="tag scanned\ndrip returned\ncut\nyeah",
)

CLOUT_DIET_LYRICS = format_diss_lyrics(
    intro="dusty break\nlikes as food\nNill Bye scanning",
    chorus=(
        "Clout diet\n"
        "Likes as calories, macros none\n"
        "Nill Bye on the empty plate\n"
        "Rake chewed a metric for fun\n"
        "Trip-hop hunger, the serving's air\n"
        "Eat the work or starve the diet"
    ),
    verses=(
        "Rake ate a clout diet of likes\n"
        "Dusty break under a hollow spike\n"
        "Calories counted in a double-tap gram\n"
        "I want a protein, you want a ham\n"
        "Spy keys click on an empty macro\n"
        "Your hunger is a feed, your plate is a tableau\n"
        "Nill Bye reading what the serving hid\n"
        "He smiles at a calorie that never did\n"
        "Sub bass low, the portion shrinks\n"
        "You fasted on applause till the body blinks\n"
        "Clout diet closed when the likes run dry\n"
        "Empty macros, a decorative pie",
        "You plated a metric and called it a meal\n"
        "Then you crashed when the hunger got stark\n"
        "Rake with a clout diet, no fiber in\n"
        "Nill Bye weighing the hollow grin\n"
        "Trip-hop dust, the snack is air\n"
        "I want a gram, you want a stare\n"
        "Likes as calories, the scale is fake\n"
        "Your protein is a caption you cannot bake\n"
        "Spy keys wait on a fasting boast\n"
        "You sold a diet that was mostly ghost\n"
        "Empty macros on a pretty dish\n"
        "Clout diet truth, you swallowed a wish",
        "Dusty break while you chase a serving\n"
        "I want a portion that is actually deserving\n"
        "Nill Bye logging the missing gram\n"
        "Rake still chewing a numerical jam\n"
        "Sub bass under a calorie mirage\n"
        "You wanted a bulk from a borrowed collage\n"
        "Hunger first, then the flex, then the crash-out\n"
        "That's a clout diet, not a workout\n"
        "Fiber none, the plate is styled\n"
        "I keep the ledger, you keep it wild\n"
        "Likes unpaid, the macros vacant\n"
        "He still ordering a decorative bacon",
        "Rake at the empty-plate bar\n"
        "Nill Bye posting the diet's scar\n"
        "Clout diet first, the work can idle\n"
        "You wanted a bulk from a hungry bait\n"
        "Trip-hop fades, the serving's gone\n"
        "I close the scale, you ask what went wrong\n"
        "Calories of clout do not rebuild\n"
        "Empty macros, the hunger filled\n"
        "Spy keys out, the snack is lapsed\n"
        "Eat the work, the likes are untrue\n"
        "He still hunting a numerical feast\n"
        "I file the diet as a decorative beast",
    ),
    outro="likes unpaid\nmacros empty\ncut\nyeah",
)

MOOD_FORECAST_LYRICS = format_diss_lyrics(
    intro="strings swell\nradar ping\nNill Bye tracking",
    chorus=(
        "Mood forecast\n"
        "Storm then sun on a rented map\n"
        "Nill Bye on the barometer\n"
        "Rake sold a squall as a nap\n"
        "Cinematic pressure, the radar lies\n"
        "Read the sky or lose the forecast"
    ),
    verses=(
        "Rake sold a mood forecast of sun\n"
        "Strings swell under a drizzle he spun\n"
        "Storm-then-sun brand on a timpani roll\n"
        "I read the radar, you read the poll\n"
        "Low brass under a humidity pitch\n"
        "Your feeling is weather you cannot stitch\n"
        "Nill Bye tracking the pressure drop\n"
        "He smiles at a squall he refused to stop\n"
        "Cirrus talk on a Doppler fib\n"
        "You wanted an outlook money could buy\n"
        "Mood forecast closed when the isobar shifts\n"
        "Storm-then-sun is a costume of gifts",
        "You called for clear, then you booked a squall\n"
        "Then you asked for cover when the pressure crawled\n"
        "Rake with a forecast taped to his sleeve\n"
        "Nill Bye reading what the radar would not believe\n"
        "Timpani rolls on a humidity swell\n"
        "I want a climate, you want a next\n"
        "Barometer falling, the brand stays bright\n"
        "Your storm is a product, your sun is a light\n"
        "Cinematic swell, the drizzle is hired\n"
        "Mood forecast truth, the outlook expired\n"
        "Isobar bent on a feeling you sold\n"
        "I keep the radar, you keep the gold",
        "Strings hold a front you cannot name-drop\n"
        "I want a sky that will actually nonstop\n"
        "Nill Bye clocking the Doppler spin-out\n"
        "Rake still selling a storm-then-sun route\n"
        "Low brass warns, the humidity lingers\n"
        "You wanted a climate that a caption pays\n"
        "Squall on cue, then a sudden clear\n"
        "That's a mood forecast, not a year\n"
        "Radar ping, the outlook sags\n"
        "I file the weather, you file the gilts\n"
        "Cirrus fading, the brand is mist\n"
        "He still promising a sun I missed",
        "Rake at the radar with a painted sky\n"
        "Nill Bye posting the pressure spike\n"
        "Mood forecast first, the climate can idle\n"
        "You wanted a squall for a sold-out date\n"
        "Timpani out, the drizzle thins\n"
        "I close the map, you ask me why the surprise\n"
        "Storm-then-sun is a rented front\n"
        "Barometer honest, the brand is blunt\n"
        "Cinematic hush, the forecast fails\n"
        "Read the sky, the feeling derails\n"
        "He still hunting a profitable breeze\n"
        "I file the weather as a costume sneeze",
    ),
    outro="radar clear\nforecast wrong\ncut\nyeah",
)

ALGORITHM_LYRICS = format_diss_lyrics(
    intro="wah guitar\nfeed loading\nNill Bye ranking",
    chorus=(
        "Algorithm\n"
        "You chased the feed till it owned the breath\n"
        "Nill Bye on the clavinet\n"
        "Rake sold a rank as a death\n"
        "Funk-tight snare, the metric is boss\n"
        "Leave the scroll or serve the algorithm"
    ),
    verses=(
        "Rake chased the algorithm for rank\n"
        "Wah guitar under a hungry tank\n"
        "Feed loading, the metric blinks first\n"
        "I want a song, you want a burst\n"
        "Clavinet chop on a timeline leash\n"
        "Your cool is a vector the ranking can teach\n"
        "Nill Bye ranking what the click cannot\n"
        "He smiles at a token the feed just bought\n"
        "Tight snare, the scroll owns the hour\n"
        "You traded a voice for a engagement shower\n"
        "Algorithm closed when the metric yawns\n"
        "Chasing the feed till the person is gone",
        "You tuned a bar to a ranking whim\n"
        "Then you panicked when the scroll went dim\n"
        "Rake with a feed in a clenched-up fist\n"
        "Nill Bye pulling the clavinet twist\n"
        "Wah cries out, the token spends\n"
        "I want a line, you want a trend's\n"
        "Timeline leash on a borrowed groove\n"
        "Your metric master will not let you move\n"
        "Funk stays tight, the algorithm feeds\n"
        "You chewed a rank till it chewed your needs\n"
        "Click for a life, then the ranking shifts\n"
        "He still refreshing the numerical gifts",
        "Clavinet talks while you chase a vector\n"
        "I want a pocket that can actually correct her\n"
        "Nill Bye logging the owned-out breath\n"
        "Rake still serving a algorithmic death\n"
        "Tight snare waiting, the feed is loud-ish\n"
        "You wanted a burst more than a vow, this\n"
        "Scroll till morning, the metric is king-like\n"
        "That's an algorithm, not a mic-strike\n"
        "Token spent, the ranking cools\n"
        "I keep the funk, you keep the rules\n"
        "Wah guitar out, the leash is lapsed\n"
        "Leave the feed, the owner is you",
        "Rake at the timeline with a hungry thumb\n"
        "Nill Bye posting the metric's sum\n"
        "Algorithm first, the pocket can idle\n"
        "You wanted a rank for a sold-out fate\n"
        "Clavinet fades, the scroll still begs\n"
        "I close the feed, you ask for the dregs\n"
        "Chasing the metric till it owns the chest\n"
        "Funk tells the truth, the ranking is dressed\n"
        "Tight snare hush, the token fizzles\n"
        "Leave the algorithm, keep the tries\n"
        "He still hunting a numerical hug\n"
        "I file the feed as a decorative drug",
    ),
    outro="feed paused\nmetric owned\ncut\nyeah",
)

STORY_TIME_LYRICS = format_diss_lyrics(
    spoken=(
        "Story time\n"
        "Rake brought a bedtime rumor\n"
        "Zero timestamps\n"
        "Tossed"
    ),
    intro="guitar sting\nlamp low\nNill Bye listening",
    chorus=(
        "Story time\n"
        "Bedtime rumor with no clock\n"
        "Nill Bye on the harmonica\n"
        "Rake tucked a fable in a sock\n"
        "Blues-shuffle truth, the yarn is cheap\n"
        "Stamp the time or lose the story"
    ),
    verses=(
        "Rake told a bedtime rumor twice\n"
        "Guitar sting on a pillow of ice\n"
        "Lamp low, the chapter has no stamp\n"
        "I want a clock, you want a camp\n"
        "Harmonica moan on a quilted fib\n"
        "Your yarn is a whisper you cannot tie\n"
        "Nill Bye listening for a timestamp click\n"
        "He smiles at a fable he will not pick\n"
        "Shuffled snare, the blanket talks\n"
        "You sold a parable with missing clocks\n"
        "Story time closed when the wick burns out\n"
        "Bedtime rumor, I toss it out",
        "You slid a fable under the door-sill\n"
        "Then you asked for hush when I asked the till\n"
        "Rake with a pillow where the dates should sit\n"
        "Nill Bye reading the wick of it\n"
        "Blues sting, the chapter skips a hour\n"
        "I want a stamp, you want a power\n"
        "Yarn so soft it forgets the when\n"
        "Your bedtime rumor is a borrowed pen\n"
        "Harmonica waits on a clockless yarn\n"
        "Story time truth, the timestamps fail\n"
        "Quilt pulled up, the rumor hides\n"
        "I keep the hour, you keep the tides",
        "Lamp flickers while you chase a whisper\n"
        "I want a chapter that can actually blister\n"
        "Nill Bye clocking the missing stamp\n"
        "Rake still tucking a rumor in the damp\n"
        "Shuffled snare, the fable thins\n"
        "You wanted a hush more than a cheer\n"
        "Pillow talk with a zero on the clock\n"
        "That's story time, not a rock\n"
        "Wick going dark, the yarn is spent\n"
        "I file the rumor, you want it lent\n"
        "Bedtime closed, the parable drops\n"
        "He still asking to rewind the props",
        "Rake at the lamp with a clockless book\n"
        "Nill Bye posting the timestamp hook\n"
        "Story time first, the dates can idle\n"
        "You wanted a legend from a bedtime bait\n"
        "Guitar sting fades, the quilt goes slack\n"
        "I close the chapter, you want it back\n"
        "Zero timestamps, the yarn is tossed\n"
        "Harmonica honest, the rumor lost\n"
        "Blues hush, the fable wilts\n"
        "Stamp the hour, the whisper lies\n"
        "He still hunting a pillow-proof myth-let\n"
        "I file the story as a clockless skit",
    ),
    outro="lamp out\nrumor tossed\ncut\nyeah",
)

CAPTION_LYRICS = format_diss_lyrics(
    intro="square lead\npretty type\nNill Bye tabling",
    chorus=(
        "Caption vs data\n"
        "Pretty type on an ugly table\n"
        "Nill Bye on the spreadsheet\n"
        "Rake sold a sprite as a fable\n"
        "Chiptune beep, the header wins\n"
        "Show the cells or lose the caption"
    ),
    verses=(
        "Rake wrote a caption vs data fib\n"
        "Square lead chirping while the numbers die\n"
        "Pretty type on a ugly grid\n"
        "I want a cell, you want a id\n"
        "8-bit drums on a header boast\n"
        "Your caption is makeup, the table is a ghost\n"
        "Nill Bye tabling what the sprite concealed\n"
        "He smiles at a pixel the column repealed\n"
        "Spreadsheet open, the pretty type cracks\n"
        "You wanted a nibble more than the facts\n"
        "Caption vs data, the header is mean\n"
        "Chiptune truth on a ugly screen",
        "You framed a number in a candy font\n"
        "Then you folded when the column went blunt\n"
        "Rake with a caption the cells refuse\n"
        "Nill Bye reading the spreadsheet news\n"
        "Square-wave beep, the sprite is cute\n"
        "I want a total, you want a loot\n"
        "Ugly table, the pretty type lies\n"
        "Your 8-bit story is a cosmetic prize\n"
        "Header honest, the caption wilts\n"
        "Caption vs data, pay the guilt\n"
        "Pixel perfect, the sum is wrong\n"
        "I keep the grid, you keep the song",
        "Chiptune hops while you chase a sprite\n"
        "I want a column that can actually write\n"
        "Nill Bye logging the makeup type\n"
        "Rake still posting a decorative hype\n"
        "8-bit snare, the cell is blank\n"
        "You wanted a caption more than a bank\n"
        "Spreadsheet waits, the pretty type folds\n"
        "That's caption vs data, not a gold\n"
        "Nibble spent, the header cools\n"
        "I keep the table, you keep the rules\n"
        "Square lead out, the sprite is lapsed\n"
        "Show the cells, the caption is untrue",
        "Rake at the pretty type with a empty cell\n"
        "Nill Bye posting the table as well\n"
        "Caption vs data, the font can idle\n"
        "You wanted a sprite for a sold-out fate\n"
        "Chiptune fades, the header lingers\n"
        "I close the sheet, you ask for praise\n"
        "Ugly table beats a candy line\n"
        "Pixel makeup will not redefine\n"
        "8-bit hush, the caption wilts\n"
        "Show the data, the story lies\n"
        "He still hunting a prettier sum\n"
        "I file the type as a decorative crumb",
    ),
    outro="pixels off\ntable wins\ncut\nyeah",
)

ENERGY_DRINK_LYRICS = format_diss_lyrics(
    intro="tuba bass\ncan cracked\nNill Bye timing",
    chorus=(
        "Energy drink\n"
        "The fuel is fake, the crash is due\n"
        "Nill Bye on the brass-band hype\n"
        "Rake sold a fizz as a true\n"
        "Tuba punch, the aftertaste lies\n"
        "Dump the can or own the drink"
    ),
    verses=(
        "Rake cracked an energy drink for hype\n"
        "Tuba punching while the jitter is ripe\n"
        "Snare cadence on a caffeine bluff\n"
        "I want a rest, you want a puff\n"
        "Brass-band shine on a pull-tab grin-out\n"
        "Your fuel is a fizz, your crash is a spin-out\n"
        "Nill Bye timing what the can conceals\n"
        "He smiles at a buzz the morning repeals\n"
        "Foam on the lip, the aftertaste sours\n"
        "You wanted a march more than the hours\n"
        "Energy drink closed when the jitter drops\n"
        "Fake fuel filed, the tuba halts",
        "You marched a high on a carbonated loan\n"
        "Then you folded when the crash hit bone\n"
        "Rake with a can and a brass-band grin-ish\n"
        "Nill Bye reading the crash in the finish\n"
        "Tuba low, the caffeine lies\n"
        "I want a pace, you want a prize\n"
        "Pull-tab clicked, the aftertaste bites\n"
        "Your hype is a fizz that the morning indicts\n"
        "Snare cadence waits on a empty tank\n"
        "Energy drink truth, the fuel is a prank\n"
        "Jitter first, then the crash, then the hush\n"
        "He still cracking a decorative rush",
        "Brass hits hard while you chase a foam\n"
        "I want a tempo that can actually roam\n"
        "Nill Bye logging the fake-fuel tab\n"
        "Rake still marching in a caffeine cab\n"
        "Tuba warning, the fizz is thin-ish\n"
        "You wanted a burst more than a finish\n"
        "Aftertaste metal, the crash is prompt\n"
        "That's an energy drink, not a pomp\n"
        "Can still cold, the buzz is theater\n"
        "I keep the time, you keep the liter\n"
        "Snare cadence out, the jitter fizzles\n"
        "Dump the fuel, the hype is lies",
        "Rake at the cooler with a cracked-out can\n"
        "Nill Bye posting the crash as a plan\n"
        "Energy drink first, the rest can pause\n"
        "You wanted a tuba for a sold-out fate\n"
        "Brass-band fades, the aftertaste lingers\n"
        "I close the march, you ask for praise\n"
        "Fake fuel will not rebuild a pace\n"
        "Caffeine costume on a jittery face\n"
        "Tuba hush, the can is tossed\n"
        "Own the crash, the fizz is lost\n"
        "He still hunting a carbonated crown-let\n"
        "I file the drink as a decorative outlet",
    ),
    outro="can tossed\ncrash filed\ncut\nyeah",
)

CAMPFIRE_LYRICS = format_diss_lyrics(
    intro="acoustic guitar\nember talk\nNill Bye sifting",
    chorus=(
        "Campfire rumor\n"
        "Smoke story, no ember of backing\n"
        "Nill Bye on the room-mic circle\n"
        "Rake sold a kindling as a packing\n"
        "Folk hush, the tinder is weak\n"
        "Show the ash or lose the campfire"
    ),
    verses=(
        "Rake spun a campfire into lore\n"
        "Acoustic hush on a borrowed floor\n"
        "Circle sits, the smoke is thick-ish\n"
        "I want an ember, you want a wish\n"
        "Shaker ticks on a kindling fib\n"
        "Your folk is a story the ash will deny\n"
        "Nill Bye sifting what the tinder hid\n"
        "He smiles at a hearth he never did\n"
        "Room mic catches a smoke-only proofing\n"
        "You wanted a circle more than a roofing\n"
        "Campfire closed when the ember is none\n"
        "Folk on facts, the rumor is done",
        "You booked a slot by a borrowed flame\n"
        "Then you folded when I asked the source\n"
        "Rake with a campfire and a clockless log\n"
        "Nill Bye reading the ash in the fog-less bog\n"
        "Acoustic guitar, the kindling pops\n"
        "I want a heat, you want the props\n"
        "Smoke story circling a empty hearth\n"
        "Your ember of backing was never a birth\n"
        "Shaker waits on a tinder that fails\n"
        "Campfire rumor, the folk derails\n"
        "Circle tight, the proof is vapor-ish\n"
        "He still feeding a decorative flourish",
        "Room mic close while you chase a crackle\n"
        "I want a log that can actually tackle\n"
        "Nill Bye clocking the missing ember\n"
        "Rake still selling a smoke to remember\n"
        "Folk hush, the kindling is theater\n"
        "You wanted a circle more than a meter\n"
        "Ash on the hands, no heat in the yarn\n"
        "That's a campfire, not a grail\n"
        "Tinder spent, the hearth is cold\n"
        "I keep the fact, you keep the gold\n"
        "Acoustic out, the smoke is lapsed\n"
        "Show the ember, the rumor is untrue",
        "Rake at the circle with a smoky book\n"
        "Nill Bye posting the ember's look\n"
        "Campfire first, the backing can pause\n"
        "You wanted a folk for a sold-out fate\n"
        "Shaker fades, the kindling wilts\n"
        "I close the hearth, you ask me why the surprise\n"
        "Smoke story, no ember of backing\n"
        "Room mic honest, the circle is lacking\n"
        "Folk hush, the rumor tossed\n"
        "Show the ash, the legend is lost\n"
        "He still hunting a profitable flame\n"
        "I file the campfire as a costume brand",
    ),
    outro="fire out\ncircle broke\nfolk hush\nyeah",
)


DISS_VARIETY: tuple[DissExample, ...] = (
    _ex(
        "citation-needed",
        "citation needed",
        90,
        41,
        "citation-needed roast of Rake",
        CITATION_NEEDED_LYRICS,
        "jazz hop",
        "brushed drums",
        "upright bass",
        "muted trumpet",
    ),
    _ex(
        "p-hacking",
        "p-hacking",
        98,
        43,
        "p-hacking roast of Rake",
        P_HACKING_LYRICS,
        "g-funk",
        "synth bass",
        "dry claps",
        "talkbox lead",
    ),
    _ex(
        "null-result",
        "null result",
        92,
        47,
        "null-result roast of Rake",
        NULL_RESULT_LYRICS,
        "reggae",
        "offbeat guitar",
        "rimshot",
        "organ bubble",
    ),
    _ex(
        "expired-reagent",
        "expired reagent",
        84,
        53,
        "expired-reagent roast of Rake",
        EXPIRED_REAGENT_LYRICS,
        "neo-soul",
        "rhodes",
        "soft snare",
        "warm bass",
    ),
    _ex(
        "lab-safety",
        "lab safety",
        168,
        59,
        "lab-safety roast of Rake",
        LAB_SAFETY_LYRICS,
        "rap rock",
        "live drums",
        "overdriven guitar",
        "crowd stomp",
    ),
    _ex(
        "rumor-mill",
        "rumor mill",
        108,
        61,
        "rumor-mill roast of Rake",
        RUMOR_MILL_LYRICS,
        "industrial hip-hop",
        "metal percussion",
        "distorted bass",
    ),
    _ex(
        "gym-selfie",
        "gym selfie",
        110,
        67,
        "gym-selfie roast of Rake",
        GYM_SELFIE_LYRICS,
        "afrobeat",
        "log drum",
        "guitar stab",
        "shekere",
    ),
    _ex(
        "rented-drip",
        "rented drip",
        104,
        71,
        "rented-drip roast of Rake",
        RENTED_DRIP_LYRICS,
        "synthwave",
        "analog bass",
        "gated snare",
        "neon pads",
    ),
    _ex(
        "clout-diet",
        "clout diet",
        86,
        73,
        "clout-diet roast of Rake",
        CLOUT_DIET_LYRICS,
        "trip-hop",
        "dusty break",
        "sub bass",
        "spy keys",
    ),
    _ex(
        "mood-forecast",
        "mood forecast",
        76,
        79,
        "mood-forecast roast of Rake",
        MOOD_FORECAST_LYRICS,
        "cinematic",
        "strings",
        "timpani",
        "low brass",
    ),
    _ex(
        "algorithm",
        "algorithm",
        114,
        83,
        "algorithm roast of Rake",
        ALGORITHM_LYRICS,
        "funk",
        "wah guitar",
        "tight snare",
        "clavinet",
    ),
    _ex(
        "story-time",
        "story time",
        74,
        89,
        "story-time roast of Rake",
        STORY_TIME_LYRICS,
        "blues",
        "guitar sting",
        "shuffled snare",
        "harmonica",
    ),
    _ex(
        "caption",
        "caption vs data",
        100,
        97,
        "caption-vs-data roast of Rake",
        CAPTION_LYRICS,
        "chiptune",
        "square lead",
        "8-bit drums",
    ),
    _ex(
        "energy-drink",
        "energy drink",
        120,
        101,
        "energy-drink roast of Rake",
        ENERGY_DRINK_LYRICS,
        "brass band",
        "tuba bass",
        "snare cadence",
    ),
    _ex(
        "campfire",
        "campfire rumor",
        82,
        103,
        "campfire-rumor roast of Rake",
        CAMPFIRE_LYRICS,
        "folk",
        "acoustic guitar",
        "shaker",
        "room mic",
    ),
)

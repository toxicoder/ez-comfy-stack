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
        "series": "variety",
        "title": title,
        "tags": nill_tags(*tag_parts, bpm=bpm),
        "bpm": bpm,
        "duration": DISS_DURATION_S,
        "seed": seed,
        "prefix": prefix,
        "description": _desc(take),
        "lyrics": lyrics,
    }


CITATION_NEEDED_LYRICS = format_diss_lyrics(
    intro="brushed snare\nsource missing\nNill Bye reading",
    chorus=(
        "Citation needed\n"
        "Nill Bye on the page\n"
        "Rake with a blank cite\n"
        "Club talk, no source in sight\n"
        "Show the paper, drop the myth\n"
        "Jazz hop truth, rumor stiff"
    ),
    verses=(
        "Rake drops a claim with a finger snap\n"
        "No footnote, just a nightcap\n"
        "I ask the source, you send a grin\n"
        "I ask the page, you spin again\n"
        "Muted horn on a missing line\n"
        "Upright bass and a rotten spine\n"
        "Nill Bye mad at a naked quote\n"
        "Rake in his feels with a borrowed note\n"
        "Bring the paper, lose the crown\n"
        "Science reads, club talk down\n"
        "Talk that life with an empty stack\n"
        "I send the rumor right back",
        "You name a girl like a cited fact\n"
        "That's a caption, not an act\n"
        "You name a high like a journal win\n"
        "That's a vibe with a paper-thin\n"
        "Brushed drums, dry booth, no shine\n"
        "I hold the book, you hold the line\n"
        "Rake in his feels on a ghost cite\n"
        "Nill Bye stamping in the night\n"
        "ibid blank, your legend folds\n"
        "Club-talk scholarship never holds\n"
        "Show the work or leave the hall\n"
        "Citation truth, that is the call",
        "I log the miss, you log the glow\n"
        "I log the night you will not show\n"
        "Trumpet mute on a rumor chart\n"
        "You drew a king with a crayon heart\n"
        "Nill Bye talking from the stacks\n"
        "Rake keeps folding when the page goes slack\n"
        "Feelings filed, the source is gone\n"
        "Club-talk abstract, the lights stay on\n"
        "Bring a footnote, drop the bit\n"
        "One of us measured, one of us quit\n"
        "Jazz hop swing, your claim is late\n"
        "Science does not negotiate",
        "Rake in his feels at the blank-cite wall\n"
        "Nill Bye posting the protocol\n"
        "You want a law from a Friday spark\n"
        "I want a line that can hold in the dark\n"
        "No page number, no author name\n"
        "Just a screenshot and a borrowed fame\n"
        "Write it down or get off the spit\n"
        "Ink or it did not exist\n"
        "Cut the lore, keep the note\n"
        "Citation closed, that is the quote\n"
        "Nill Bye out, the record stands\n"
        "Rake still leaking through his hands",
    ),
    outro="source missing\nclaim denied\ncut\nyeah",
)

P_HACKING_LYRICS = format_diss_lyrics(
    intro="synth bass\ncherry pick\nNill Bye testing",
    chorus=(
        "P-hacking king\n"
        "Your night is a slice\n"
        "Nill Bye in the lab\n"
        "Rake paid the price\n"
        "Pick the peak, hide the miss\n"
        "That is not a method, kid"
    ),
    verses=(
        "Rake ran the night till the number smiled\n"
        "Threw the rest in a junk-file pile\n"
        "Talkbox keys on a cherry plot\n"
        "You kept the win, you lost the lot\n"
        "I want the full set, you send a peak\n"
        "I want the miss that you will not speak\n"
        "Nill Bye mad at a trimmed result\n"
        "Rake in his feels with a rented cult\n"
        "Dry claps pop, your curve is fake\n"
        "G-funk bounce on a cooked mistake\n"
        "Show the misses or sit this out\n"
        "Science in, club talk drought",
        "You slice the hours till the glow looks real\n"
        "Then you crash when I ask the reel\n"
        "Girls as points you decided to keep\n"
        "Nights as proof that you put to sleep\n"
        "Rake in his feels with a p of none\n"
        "Nill Bye running the count till done\n"
        "Talkbox lead, the boast stays thin\n"
        "Synth bass waiting to cash you in\n"
        "Bring the raw file, drop the crown\n"
        "Cherry-pick science is upside down\n"
        "I log the trash you would not show\n"
        "Your whole paper is a highlight show",
        "I ask the n, you send a clip\n"
        "I ask the miss, you send a sip\n"
        "Underpowered, oversold\n"
        "That is the brand you tried to hold\n"
        "Nill Bye talking from the plot desk\n"
        "Rake keeps folding when the notes get terse\n"
        "Feelings first, then the flex, then the fall\n"
        "That's the loop, I have seen it all\n"
        "Lab coat truth vs a night-out myth\n"
        "One of us measured, and one of us quit\n"
        "Cut the slice, keep the set\n"
        "P-hack drought, now pay the debt",
        "Rake in his feels at the junk-file wall\n"
        "Nill Bye posting the protocol\n"
        "You want a law from a Friday spark\n"
        "I want a line that can hold in the dark\n"
        "Hide the miss, the claim looks tall\n"
        "Show the miss, the claim looks small\n"
        "Science guy here with the full stack\n"
        "Fake-cool king with a rumor pack\n"
        "Whiskers up, your legend drops\n"
        "Club talk drought when the slicing stops\n"
        "Nill Bye out, now the numbers change\n"
        "Rake still picking through the range",
    ),
    outro="slice denied\nfull set in\ncut\nyeah",
)

NULL_RESULT_LYRICS = format_diss_lyrics(
    intro="rimshot\noffbeat\nNill Bye testing",
    chorus=(
        "Null result\n"
        "Your flex found none\n"
        "Nill Bye in the lab\n"
        "Rake on the run\n"
        "Organ bubble, rumor down\n"
        "Science wins, club talk drown"
    ),
    verses=(
        "Hypothesis: Rake is king\n"
        "Lab notes say you failed the thing\n"
        "Reggae bounce on an empty claim\n"
        "Offbeat guitar, you look the same\n"
        "You talk a high like a measured fact\n"
        "I run the test, your curve falls flat\n"
        "Nill Bye mad, I repeat the trial\n"
        "Rake in his feels in denial\n"
        "Rimshot ticks, the proof is gone\n"
        "Club-talk sample will not hold on\n"
        "Show the work or sit this out\n"
        "Null on cool, that is the route",
        "I log the night, I log the talk\n"
        "I log the crash at the end of the walk\n"
        "Your legend lives in a group-chat haze\n"
        "My legend lives in a measured phase\n"
        "Null result on the cool-guy claim\n"
        "All that smoke and you still look lame\n"
        "Rake in his feels with a sample of one\n"
        "Nill Bye repeating until it's done\n"
        "Organ bubble, the boast goes still\n"
        "Science calm, club talk ill\n"
        "Bring a method, bring a source\n"
        "Or get bounced from the lecture course",
        "I graph the talk, I graph the fall\n"
        "I graph the rumor on the lecture wall\n"
        "You treat a high like a plotted peak\n"
        "That's a spike that will not repeat\n"
        "Nill Bye speaking from the lab bench\n"
        "Rake keeps folding at the first wrench\n"
        "Null on cool, null on the crown\n"
        "Club-talk p-value crashing down\n"
        "Trial two, same result\n"
        "Your legend fails the consult\n"
        "Offbeat truth, your flex is spent\n"
        "Retract the night, the rumor bent",
        "Peer-review light on a rumor chart\n"
        "You drew a king with a crayon heart\n"
        "Nill Bye testing from the bench again\n"
        "Rake in denial with a borrowed pen\n"
        "Bring a method, drop the myth\n"
        "Science stays when the club goes stiff\n"
        "Whiteboard clean, your curve is bent\n"
        "Null result, the rumor spent\n"
        "Cut the trial, file the note\n"
        "Club talk drought, that is the quote\n"
        "Nill Bye out when the test is done\n"
        "Rake still claiming everyone",
    ),
    outro="trial over\nnull result\ncut\nyeah",
)

EXPIRED_REAGENT_LYRICS = format_diss_lyrics(
    intro="rhodes warm\ndate passed\nNill Bye checking",
    chorus=(
        "Expired reagent\n"
        "Your cool is past date\n"
        "Nill Bye in the lab\n"
        "Rake showed up late\n"
        "Shelf-life gone, the glow is thin\n"
        "Neo-soul truth, rumor in the bin"
    ),
    verses=(
        "Rake pops a flex from a dusty shelf\n"
        "Talks a high like he bottled himself\n"
        "I read the stamp, the month is wrong\n"
        "Your whole brand is a leftover song\n"
        "Soft snare, warm bass, dry booth\n"
        "I hold the flask, you hold the spoof\n"
        "Nill Bye mad at a dated glow\n"
        "Rake in his feels when the numbers show\n"
        "Club-talk chemistry, science kit\n"
        "One of us measured, and one of us quit\n"
        "Toss the bottle, keep the proof\n"
        "Your whole cool is a rented roof",
        "You name a night like a fresh compound\n"
        "Then you crash when the clock is found\n"
        "Rhodes hum low, the boast is stale\n"
        "Sad-boy mask on a expired tale\n"
        "Rake in his feels with a yellowed label\n"
        "Nill Bye clocking what the dates disable\n"
        "Bring a batch that survives the week\n"
        "You want a caption, then you peak\n"
        "Shelf-life law, not a vibe you spin\n"
        "Science does not play pretend\n"
        "I log the stamp, you log the shine\n"
        "Your reagent died in forty-nine",
        "I ask the date, you send a pose\n"
        "I ask the lot, you send the clothes\n"
        "Past-due cool in a glass-bottle flex\n"
        "No active dose, just a caption next\n"
        "Nill Bye talking from the cold shelf\n"
        "Rake keeps folding when he sees himself\n"
        "Feelings first, then the flex, then the fall\n"
        "That's the loop, I have seen it all\n"
        "Keep the tear, lose the store\n"
        "Expired aisle, I close the door\n"
        "Soft keys stay, the boast walks out\n"
        "Facts don't owe you a fade-out",
        "Rake in his feels at the date-stamp wall\n"
        "Nill Bye posting the protocol\n"
        "You want a crown from a leftover spark\n"
        "I want a line that can hold in the dark\n"
        "Write the lot, write it true\n"
        "Club talk drought when the stamp comes through\n"
        "Science guy here with a fresh stack\n"
        "Fake-cool king with a rumor pack\n"
        "Cut the bottle, keep the note\n"
        "Past-due closed, that is the quote\n"
        "Nill Bye out, the record stands\n"
        "Rake still leaking through his hands",
    ),
    outro="date passed\nbottle tossed\nsoft out\nyeah",
)

LAB_SAFETY_LYRICS = format_diss_lyrics(
    intro="live drums\ngoggles off\nNill Bye mad",
    chorus=(
        "Lab safety first\n"
        "You skipped the kit\n"
        "Nill Bye in the coat\n"
        "Rake took a hit\n"
        "Goggles on, the proof is slow\n"
        "Rap rock truth, club talk no"
    ),
    verses=(
        "Rake walks in with the hood still up\n"
        "No glove, no glass, just a trophy cup\n"
        "Overdriven guitar, your method wild\n"
        "I run a drill, you run a child\n"
        "Crowd stomp bed, your story stains\n"
        "Live drums punch while the real you drains\n"
        "Nill Bye mad at a broken rule\n"
        "Rake in his feels like the lab is a pool\n"
        "I weigh the salt, you weigh the likes\n"
        "I time the drop, you time the nights\n"
        "Show the work or leave the hall\n"
        "Safety truth, that is the call",
        "You skip the hood, you skip the glove\n"
        "Call it swag, I call it shove\n"
        "Beaker rings, your chain is loud\n"
        "One of us measured, one of us proud\n"
        "Rake in his feels with a name-tag smile\n"
        "Nill Bye in the coat for a long trial\n"
        "You borrow cool from a rented light\n"
        "I borrow nothing, I write it right\n"
        "Club report folded, the margin blank\n"
        "Your whole method is a credit rank\n"
        "Goggles on or get off the spit\n"
        "Science does not do the bit",
        "I hold the flask, don't hold the room\n"
        "Your cool is smoke, my cool is proof\n"
        "Talk that life like a highlight reel\n"
        "Then you crash out when the night gets real\n"
        "Nill Bye speaking, the whiteboard wins\n"
        "Rake keeps leaking those made-up sins\n"
        "Live drums stay, the boast walks out\n"
        "Facts don't owe you a fade-out\n"
        "Come correct or don't come at all\n"
        "The booth is small and the facts stand tall\n"
        "Put the kit back, lose the crown\n"
        "Safety in, club talk down",
        "Office hours empty, you ghost the slot\n"
        "Then you flex like you gave a lot\n"
        "I grade the claim with a colder eye\n"
        "You grade the night with a rented high\n"
        "Nill Bye talking from the front row\n"
        "Rake keeps posing for a highlight show\n"
        "Cut the rumor, keep the fact\n"
        "Lab light on, no turning back\n"
        "Class is long and the proof is slow\n"
        "Your cool expired two weeks ago\n"
        "Goggles down, the file is closed\n"
        "Your soundtrack snapped and the truth exposed",
    ),
    outro="kit on\ncase closed\ncut\nyeah",
)

RUMOR_MILL_LYRICS = format_diss_lyrics(
    intro="metal hit\ndistorted bass\nNill Bye logging",
    chorus=(
        "Rumor mill loud\n"
        "The measure is quiet\n"
        "Nill Bye in the lab\n"
        "Rake on a diet\n"
        "Gossip in, the facts walk out\n"
        "Industrial truth, club talk drought"
    ),
    verses=(
        "Rake feeds a mill with a group-chat haze\n"
        "I keep a notebook with a dated page\n"
        "Metal percussion on a leaking tale\n"
        "Distorted bass while the rumor sails\n"
        "Club-talk lore with a missing time\n"
        "That's a story that will not rhyme\n"
        "Nill Bye mad at a vanished note\n"
        "Rake in his feels with a borrowed quote\n"
        "Receipts in ink, your proof in air\n"
        "One of us measured, one of us swear\n"
        "Show the book or leave the hall\n"
        "Rumor mill truth, that is the call",
        "You cite a night with no line item\n"
        "I cite a row with a time and chem\n"
        "Chain of custody on a beaker lid\n"
        "Your chain of custody is a story you hid\n"
        "Rake in his feels when I ask the date\n"
        "Nill Bye waiting while you obfuscate\n"
        "Bring the notebook, drop the myth\n"
        "Club-talk science is a rumor gift\n"
        "Margin clean, your caption gold\n"
        "That is a tale the lab will hold\n"
        "Write it down or get off the spit\n"
        "Ink or it did not exist",
        "I log the miss, you log the glow\n"
        "I log the crash that you will not show\n"
        "Page number, time, and the witness name\n"
        "You got a screenshot and a borrowed fame\n"
        "Nill Bye talking from the bench log\n"
        "Rake keeps folding when the ink gets taut\n"
        "Feelings filed in an empty book\n"
        "Club-talk abstract, a second look\n"
        "Keep the diary, lose the brand\n"
        "Facts don't live in a disappearing hand\n"
        "Show the leaf, the stamped row\n"
        "Or the file is closed, now you know",
        "Rake in his feels at the missing page\n"
        "Nill Bye filing what the dates engage\n"
        "You want a crown from a chat-thread spark\n"
        "I want a line that can hold in the dark\n"
        "Write it once, write it true\n"
        "Club talk drought when the ink comes through\n"
        "Science guy here with a bound stack\n"
        "Fake-cool king with a rumor pack\n"
        "Cut the lore, keep the note\n"
        "Mill shut down, that is the quote\n"
        "Nill Bye out, the record stands\n"
        "Rake still leaking through his hands",
    ),
    outro="mill closed\nink dry\ncut\nyeah",
)

GYM_SELFIE_LYRICS = format_diss_lyrics(
    intro="log drum\npose held\nNill Bye counting",
    chorus=(
        "Gym selfie king\n"
        "The work is missing\n"
        "Nill Bye in the lab\n"
        "Rake still listing\n"
        "Pose is loud, the set is small\n"
        "Afrobeat truth, club talk stall"
    ),
    verses=(
        "Rake hits the glass like a measured set\n"
        "Talks a PR that the numbers forget\n"
        "Log drum knock, your form is a brand\n"
        "I count the reps, you count the hands\n"
        "Shekere shake on a rented glow\n"
        "Guitar stab while the real work shows\n"
        "Nill Bye mad at a camera trial\n"
        "Rake in his feels with a highlight smile\n"
        "I run the program, you run the pose\n"
        "I write the log, you write the clothes\n"
        "Show the work or leave the floor\n"
        "Selfie science is a closed door",
        "You treat the booth like a mirror stage\n"
        "Sad-boy pump on a rented page\n"
        "I count the moles, you count the stares\n"
        "I map the load, you map the stares\n"
        "Hold the bar, don't hold the room\n"
        "Your cool is smoke, my cool is proof\n"
        "Rake in his feels with a name-tag grin\n"
        "Nill Bye clocking what the notes keep in\n"
        "Talk that life like a highlight reel\n"
        "Then you crash out when the night gets real\n"
        "Come correct or don't come at all\n"
        "The booth is small and the facts stand tall",
        "You sell the pump like a limited drop\n"
        "Then you fold when the playlist stops\n"
        "I clock the rain, I clock the pose\n"
        "I clock the brand in the borrowed clothes\n"
        "Rake in his feels on a looped refrain\n"
        "Nill Bye reading through the window pane\n"
        "Work is real, the merch is not\n"
        "You wrapped a set in a camera shot\n"
        "Keep the tear, lose the store\n"
        "Pose-boy aisle, I close the door\n"
        "Log drums stay, the boast walks out\n"
        "Facts don't owe you a fade-out",
        "You write the night like a product brief\n"
        "Then you ask the booth for relief\n"
        "I hold the line, you hold the bit\n"
        "I name the trick, you name the hit\n"
        "Afrobeat haze, high-key play\n"
        "Rake in his feels at the end of day\n"
        "Nill Bye mad at the costume rain\n"
        "You want a crown for a rented pain\n"
        "Come correct, put the brand away\n"
        "The lab don't score a sad display\n"
        "Cold read done, the file is closed\n"
        "Your soundtrack snapped and the truth exposed",
    ),
    outro="set logged\npose denied\ncut\nyeah",
)

RENTED_DRIP_LYRICS = format_diss_lyrics(
    intro="neon pad\ngated snare\nNill Bye mad",
    chorus=(
        "Rented drip\n"
        "The tag still on\n"
        "Nill Bye in the lab\n"
        "Rake is gone\n"
        "Costume cool, empty rack\n"
        "Synthwave truth, send it back"
    ),
    verses=(
        "Rake talk clothes like a uniform\n"
        "Talk a high like a thunderstorm\n"
        "Talk the chain like a scoreboard lit\n"
        "That's a child in a grown-man kit\n"
        "Analog bass, your story stalls\n"
        "Gated snare while the real you falls\n"
        "Fake-cool walk in a borrowed coat\n"
        "All that talk with a paper throat\n"
        "Nill Bye in the lab, I don't do the bit\n"
        "Rake in his feels when the lights don't hit\n"
        "Show the receipt or sit this out\n"
        "Rented drip, club talk drought",
        "You name a fit like a medal pin\n"
        "Then you crash when the work walks in\n"
        "You name a look like a trophy cup\n"
        "Then you cry when the night dries up\n"
        "Neon pads, full-time fraud\n"
        "Science guy here to retire the god\n"
        "I run the numbers, you run the club\n"
        "I keep the line, you smear the dub\n"
        "Rake, sit down, that's a costume life\n"
        "Talking cool while you duck the knife\n"
        "The synth is loud, your proof is thin\n"
        "Nill Bye closes the case you spin",
        "Hats stay dry, the claim stays weak\n"
        "You want a crown for a three-day streak\n"
        "I want a method that holds at dawn\n"
        "You want a caption, then you are gone\n"
        "Feelings first, then the flex, then the fall\n"
        "That's the loop, I have seen it all\n"
        "Lab coat truth vs a night-out myth\n"
        "One of us measured, and one of us quit\n"
        "Rake in his feels on a borrowed shine\n"
        "Nill Bye reading what the tags define\n"
        "Drop the chain, keep the proof\n"
        "Your whole drip is a rented roof",
        "You clock a look like a shift you pulled\n"
        "Then you fold when the morning's dull\n"
        "Pads still running, the claim still thin\n"
        "Gated snare waiting to cash you in\n"
        "Nill Bye mad in a quiet lab\n"
        "Rake in his feels with a rented cab\n"
        "Club-talk uniform, science kit\n"
        "One of us measured, and one of us quit\n"
        "Put the scoreboard back on the wall\n"
        "Your fake cool cannot walk at all\n"
        "Synthwave fades, the method stays\n"
        "Nill Bye closing the costume days",
    ),
    outro="tag on\ncase closed\nNill Bye out\nyeah",
)

CLOUT_DIET_LYRICS = format_diss_lyrics(
    intro="dusty break\nempty plate\nNill Bye measuring",
    chorus=(
        "Clout diet\n"
        "You ate the likes\n"
        "Nill Bye in the lab\n"
        "Rake on a spike\n"
        "Calories fake, the method thin\n"
        "Trip-hop truth, rumor in the bin"
    ),
    verses=(
        "Rake counts a meal by the double-tap\n"
        "Calls it fuel with a caption gap\n"
        "Spy keys low, your plate is a screen\n"
        "Sub bass hums on a hungry scene\n"
        "I weigh the salt, you weigh the hits\n"
        "I time the drop, you time the clips\n"
        "Nill Bye mad at a sugar claim\n"
        "Rake in his feels with a borrowed name\n"
        "Likes as calories, science none\n"
        "Feelings loud till the daylight's done\n"
        "Show the log or sit this out\n"
        "Clout diet, club talk drought",
        "You graph a peak from a party set\n"
        "I graph a miss that you want to forget\n"
        "Power low, your swagger high\n"
        "Error fat on a borrowed lie\n"
        "Rake in his feels with a sample thin\n"
        "Nill Bye running the count again\n"
        "Girls as data, nights as proof\n"
        "That is a child in a lab-coat spoof\n"
        "Widen the n or drop the crown\n"
        "Science does not play around\n"
        "I log repeats, you log a glow\n"
        "Your whole paper is a one-row show",
        "I ask for weeks, you send a clip\n"
        "I ask for n, you send a sip\n"
        "Underpowered, oversold\n"
        "That is the brand you tried to hold\n"
        "Nill Bye talking from the count desk\n"
        "Rake keeps folding when the notes get terse\n"
        "Bring a cohort, lose the myth\n"
        "One good night is a rumor gift\n"
        "Club-talk n is a party of you\n"
        "Lab-talk n is a measured crew\n"
        "File the miss, don't file the king\n"
        "Sample size is the whole thing",
        "Rake in his feels at the small-n wall\n"
        "Nill Bye posting the protocol\n"
        "You want a law from a Friday spark\n"
        "I want a line that can hold in the dark\n"
        "Repeat the night, it will not rhyme\n"
        "That is the cost of a one-time climb\n"
        "Count the misses, count the wins\n"
        "Count the crash when the daylight spins\n"
        "Science guy here with a bigger set\n"
        "Fake-cool king with a single bet\n"
        "n goes up, your legend drops\n"
        "Club talk drought when the counting stops",
    ),
    outro="plate empty\nclaim denied\ncut\nyeah",
)

MOOD_FORECAST_LYRICS = format_diss_lyrics(
    intro="low brass\ntimpani\nNill Bye reading",
    chorus=(
        "Mood forecast\n"
        "Your weather is fake\n"
        "Nill Bye in the lab\n"
        "Rake on the take\n"
        "Storm then sun, no measured rain\n"
        "Cinematic truth, rumor strain"
    ),
    verses=(
        "Rake talks the girls like a weather report\n"
        "Storm then sun, then you want support\n"
        "Strings swell up on a costume grief\n"
        "Timpani hit, then you want relief\n"
        "I respect grief, I reject the brand\n"
        "You wear the mood like a souvenir stand\n"
        "Nill Bye mad at the costume rain\n"
        "Rake on loop like a falling vane\n"
        "You tell the night it was all so deep\n"
        "I tell the night you were fast asleep\n"
        "Feelings real until they pay the rent\n"
        "Then the diary turns to a paid event",
        "You talk a high like a badge you earned\n"
        "That's a story the lab returned\n"
        "Low brass holds while the boast falls through\n"
        "Your whole cool is a borrowed blue\n"
        "Rake in his feels on a looped refrain\n"
        "Nill Bye reading through the window pane\n"
        "Grief is real, the merch is not\n"
        "You wrapped a wound in a camera shot\n"
        "Keep the tear, lose the store\n"
        "Sad-boy aisle, I close the door\n"
        "Come correct or don't come at all\n"
        "The booth is small and the facts stand tall",
        "You sell the sigh like a limited drop\n"
        "Then you crash when the playlist stops\n"
        "I clock the rain, I clock the pose\n"
        "I clock the brand in the borrowed clothes\n"
        "Nill Bye talking from the map desk\n"
        "Rake keeps folding when the notes get terse\n"
        "Forecast loud, the station wrong\n"
        "Club-talk climate is a three-day song\n"
        "Bring a reading, drop the myth\n"
        "Science stays when the club goes stiff\n"
        "File the miss, don't file the king\n"
        "Weather bars are the whole thing",
        "You write the night like a product brief\n"
        "Then you ask the booth for relief\n"
        "I hold the line, you hold the bit\n"
        "I name the trick, you name the hit\n"
        "Cinematic haze, high-key play\n"
        "Rake in his feels at the end of day\n"
        "Nill Bye mad at the costume rain\n"
        "You want a crown for a rented pain\n"
        "Come correct, put the brand away\n"
        "The lab don't score a sad display\n"
        "Cold read done, the file is closed\n"
        "Your soundtrack snapped and the truth exposed",
    ),
    outro="station closed\nclaim denied\nsoft out\nyeah",
)

ALGORITHM_LYRICS = format_diss_lyrics(
    intro="wah guitar\nfeed spinning\nNill Bye measuring",
    chorus=(
        "Algorithm cosplay\n"
        "You chased the feed\n"
        "Nill Bye in the lab\n"
        "Rake on a need\n"
        "Clavinet tick, the method thin\n"
        "Funk on facts, rumor in the bin"
    ),
    verses=(
        "Rake tunes a night to a ranking chart\n"
        "Talks a high like a trending art\n"
        "Wah guitar on a borrowed hook\n"
        "Tight snare pops while you duck the book\n"
        "I run the test, you run the scroll\n"
        "I write the notes, you write the role\n"
        "Nill Bye mad at a costume climb\n"
        "Rake in his feels with a rented rhyme\n"
        "Feed is loud, the proof is none\n"
        "Feelings first till the daylight's done\n"
        "Show the work or sit this out\n"
        "Algo truth, club talk drought",
        "You treat the booth like a diary page\n"
        "Sad-boy loop on a rented stage\n"
        "I count the moles, you count the stares\n"
        "I map the world, you map the stares\n"
        "Hold the flask, don't hold the room\n"
        "Your cool is smoke, my cool is proof\n"
        "Talk that life like a highlight reel\n"
        "Then you crash out when the night gets real\n"
        "Nill Bye speaking, the whiteboard wins\n"
        "Rake keeps leaking those made-up sins\n"
        "Clavinet talks, your claim stays weak\n"
        "Science guy here for a long week",
        "You skip the hood, you skip the glove\n"
        "Call it swag, I call it shove\n"
        "I weigh the salt, you weigh the likes\n"
        "I time the drop, you time the nights\n"
        "Rake in his feels with a name-tag smile\n"
        "Nill Bye in the coat for a long trial\n"
        "You borrow cool from a rented light\n"
        "I borrow nothing, I write it right\n"
        "Club report folded, the margin blank\n"
        "Your whole method is a credit rank\n"
        "Show the work or leave the hall\n"
        "Lab coat truth, that is the call",
        "Office hours empty, you ghost the slot\n"
        "Then you flex like you gave a lot\n"
        "I grade the claim with a colder eye\n"
        "You grade the night with a rented high\n"
        "Beaker rings, your chain is loud\n"
        "One of us measured, one of us proud\n"
        "Nill Bye talking from the front row\n"
        "Rake keeps posing for a highlight show\n"
        "Cut the rumor, keep the fact\n"
        "Lab light on, no turning back\n"
        "Class is long and the proof is slow\n"
        "Your cool expired two weeks ago",
    ),
    outro="feed closed\nrank denied\ncut\nyeah",
)

STORY_TIME_LYRICS = format_diss_lyrics(
    spoken="Story time\nRake submitted a bedtime rumor\nZero timestamps\nRejected",
    intro="guitar sting\nharmonica\nNill Bye reading",
    chorus=(
        "Story time over\n"
        "The clock is loud\n"
        "Nill Bye on the red pen\n"
        "Rake lost the crowd\n"
        "Shuffled snare, the myth is thin\n"
        "Blues on facts, rumor in the bin"
    ),
    verses=(
        "Claim one: you live so loud\n"
        "Source? a mirror and a crowd\n"
        "Claim two: the night is proof\n"
        "That's a mood, that is not truth\n"
        "Claim three: the girls all spin\n"
        "That's a boast with a paper-thin\n"
        "I ask for data, you send a sigh\n"
        "I ask for method, you send a vibe\n"
        "Story time is a metal gate\n"
        "Your whole brand is a late debate\n"
        "Stamp denied on the title page\n"
        "Feelings filed in an empty cage",
        "You pad the abstract with a club-night tale\n"
        "Then you fold when the numbers fail\n"
        "I cite the graph, you cite the mood\n"
        "I run the trial, you run the room\n"
        "Rake in his feels with a borrowed crown\n"
        "Nill Bye in the lab taking fiction down\n"
        "Edit your draft, lose the trophy talk\n"
        "Keep the feelings, drop the fake-cool walk\n"
        "The board is cold and the lights are harsh\n"
        "Your legend ends at the loading dock\n"
        "Rejected, filed, do not resubmit\n"
        "Bring a method or get off the spit",
        "You cite a vibe with a broken link\n"
        "I cite a table, then I let it sink\n"
        "Rake in his feels on the comment thread\n"
        "Nill Bye stamping what the board just said\n"
        "Revise and resubmit is a gift\n"
        "You treat a note like a personal rift\n"
        "Margin red, your caption gold\n"
        "That is a story the lab will hold\n"
        "Bring a method, drop the crown\n"
        "Bedtime review does not play around\n"
        "Nill Bye reading till the ink is dry\n"
        "Rake still leaking a lullaby",
        "Desk copy lost, your legend stays\n"
        "Until the numbers cut the haze\n"
        "I run the check, you run the spin\n"
        "I log the miss, you log a win\n"
        "Feelings filed, the drawer is shut\n"
        "Club-talk abstract, the door stays cut\n"
        "Nill Bye mad at a padded claim\n"
        "Rake in his feels with a borrowed name\n"
        "Do not resubmit the same old night\n"
        "Bring a source or step off the mic\n"
        "Red pen down when the work is real\n"
        "Your cool cannot pass the steel",
    ),
    outro="story closed\nred pen down\ncut\nyeah",
)

CAPTION_LYRICS = format_diss_lyrics(
    intro="square lead\n8-bit drums\nNill Bye reading",
    chorus=(
        "Caption vs data\n"
        "The pixels lie\n"
        "Nill Bye in the lab\n"
        "Rake on a high\n"
        "Chiptune tick, the method thin\n"
        "Show the table, rumor in"
    ),
    verses=(
        "Rake writes a night in a golden font\n"
        "Talks a high like a screenshot want\n"
        "Square lead chirp, your numbers hide\n"
        "8-bit drums on a caption ride\n"
        "I ask the table, you send a frame\n"
        "I ask the axis, you send a name\n"
        "Nill Bye mad at a padded claim\n"
        "Rake in his feels with a borrowed fame\n"
        "Pixels loud, the proof is none\n"
        "Feelings first till the daylight's done\n"
        "Show the sheet or sit this out\n"
        "Caption truth, club talk drought",
        "You plot a point like a trophy pin\n"
        "Leave the bars off, then you call it win\n"
        "I add the whiskers, the peak looks small\n"
        "Your legend lives in a caption wall\n"
        "Rake in his feels with a fake CI\n"
        "Nill Bye drawing what the notes imply\n"
        "Confidence is a measured gate\n"
        "Not a mood that you allocate\n"
        "Bring the spread or sit this out\n"
        "Science in, club talk drought\n"
        "I log the miss, you log the glow\n"
        "Your whole chart is a one-dot show",
        "I ask the range, you send a pose\n"
        "I ask the n, you send the clothes\n"
        "Interval fat, your story slim\n"
        "That is a child in a grown-man hymn\n"
        "Nill Bye talking from the plot desk\n"
        "Rake keeps folding when the notes get terse\n"
        "Girls as points, nights as proof\n"
        "That is a chart with a rotten roof\n"
        "Show the whiskers, lose the myth\n"
        "Club-talk science is a rumor gift\n"
        "File the spread, don't file the king\n"
        "Error bars are the whole thing",
        "Rake in his feels at the wide-bar wall\n"
        "Nill Bye posting the protocol\n"
        "You want a law from a Friday spark\n"
        "I want a line that can hold in the dark\n"
        "Hide the spread, the claim looks tall\n"
        "Show the spread, the claim looks small\n"
        "Science guy here with a honest plot\n"
        "Fake-cool king with a one-dot shot\n"
        "Whiskers up, your legend drops\n"
        "Club talk drought when the plotting stops\n"
        "Cut the swagger, keep the range\n"
        "Nill Bye out, now the numbers change",
    ),
    outro="pixels off\nclaim denied\ncut\nyeah",
)

ENERGY_DRINK_LYRICS = format_diss_lyrics(
    intro="tuba bass\nsnare cadence\nNill Bye mad",
    chorus=(
        "Energy drink\n"
        "The fuel is fake\n"
        "Nill Bye in the lab\n"
        "Rake on the take\n"
        "Brass band truth, sugar high\n"
        "Show the dose or say goodbye"
    ),
    verses=(
        "Rake take a high like a sugar coat\n"
        "Talks a cure from a party note\n"
        "Placebo cool in a glass-bottle flex\n"
        "No active dose, just a caption next\n"
        "Tuba punch, your glow is fake\n"
        "Snare cadence while the real you breaks\n"
        "Nill Bye in the lab, I clock the pill\n"
        "Rake in his feels when the night goes still\n"
        "Club-talk medicine, science kit\n"
        "One of us measured, and one of us quit\n"
        "Show the label or sit this out\n"
        "Fuel is loud, the method drought",
        "You name a high like a treatment win\n"
        "Then you crash when the work walks in\n"
        "No active compound in the boast you sell\n"
        "Just a night and a story you tell\n"
        "Brass hits hard, full-time fraud\n"
        "Science guy here to retire the god\n"
        "I split the arms, you split the room\n"
        "I keep the notes, you chase the bloom\n"
        "Rake, sit down, that's a sugar life\n"
        "Talking healed while you duck the knife\n"
        "The tuba is loud, the dose is none\n"
        "Nill Bye closing the case you spun",
        "Hats stay dry, the claim stays weak\n"
        "You want a crown for a three-day streak\n"
        "I want a method that holds at dawn\n"
        "You want a caption, then you are gone\n"
        "Feelings first, then the flex, then the fall\n"
        "That's the loop, I have seen it all\n"
        "Lab coat truth vs a night-out myth\n"
        "One of us measured, and one of us quit\n"
        "Rake in his feels on a sugar high\n"
        "Nill Bye reading what the numbers cry\n"
        "Drop the can, keep the proof\n"
        "Your whole cure is a rented roof",
        "You clock a glow like a shift you pulled\n"
        "Then you fold when the morning's dull\n"
        "Cadence running, the dose still fake\n"
        "Brass band waiting to cash the take\n"
        "Nill Bye mad in a quiet lab\n"
        "Rake in his feels with a rented cab\n"
        "Club-talk medicine, science kit\n"
        "One of us measured, and one of us quit\n"
        "Put the sugar back on the shelf\n"
        "Your fake cool cannot heal itself\n"
        "Tuba fades, the method stays\n"
        "Nill Bye closing the costume days",
    ),
    outro="dose none\ncan tossed\nNill Bye out\nyeah",
)

CAMPFIRE_LYRICS = format_diss_lyrics(
    intro="acoustic guitar\nshaker\nNill Bye waiting",
    chorus=(
        "Campfire rumor\n"
        "The spark is thin\n"
        "Nill Bye in the lab\n"
        "Rake leaning in\n"
        "Room mic truth, the myth is loud\n"
        "Folk on facts, no borrowed crowd"
    ),
    verses=(
        "Rake booked a slot by a borrowed flame\n"
        "Talks a high like he gave it a name\n"
        "Acoustic hush, the chalkboard clean\n"
        "Your whole brand is a no-show scene\n"
        "I respect struggle, I reject the skip\n"
        "You wear the cool like a scholarship\n"
        "Nill Bye mad at the empty chair\n"
        "Rake on loop like he isn't there\n"
        "You tell the night it was all so deep\n"
        "I tell the night you were fast asleep\n"
        "Feelings real until the work is due\n"
        "Then the diary ducks the review",
        "You talk the girls like a weather report\n"
        "Storm then sun, then you want support\n"
        "You talk a high like a badge you earned\n"
        "That's a story the lab returned\n"
        "Shaker ticks, your boast falls through\n"
        "Your whole cool is a borrowed blue\n"
        "I hold a note, you hold a pose\n"
        "I write the truth, you write the lows\n"
        "Come correct or don't come at all\n"
        "The booth is small and the facts stand tall\n"
        "Bring a method, drop the myth\n"
        "Science stays when the club goes stiff",
        "You sell the sigh like extra credit\n"
        "Then you crash when the syllabus said it\n"
        "I clock the chair, I clock the clock\n"
        "I clock the brand that will not knock\n"
        "Rake in his feels on a looped refrain\n"
        "Nill Bye reading through the window pane\n"
        "Help is real, the ghost is not\n"
        "You wrapped a skip in a camera shot\n"
        "Keep the tear, lose the store\n"
        "Sad-boy aisle, I close the door\n"
        "Soft strings stay, the boast walks out\n"
        "Facts don't owe you a fade-out",
        "You write the night like a product brief\n"
        "Then you ask the booth for relief\n"
        "I hold the line, you hold the bit\n"
        "I name the trick, you name the hit\n"
        "Folk haze, high-key play\n"
        "Rake in his feels at the end of day\n"
        "Nill Bye mad at the empty slot\n"
        "You want a crown for a class you dropped\n"
        "Come correct, put the brand away\n"
        "The lab don't score a sad display\n"
        "Door stays open, the file is closed\n"
        "Your soundtrack snapped and the truth exposed",
    ),
    outro="fire out\nchair empty\nsoft out\nyeah",
)


DISS_VARIETY: tuple[DissExample, ...] = (
    _ex(
        "citation-needed",
        "citation needed",
        90,
        41,
        "ez_rap_nill_cite",
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
        "ez_rap_nill_phack",
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
        "ez_rap_nill_null",
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
        "ez_rap_nill_expired",
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
        "ez_rap_nill_safety",
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
        "ez_rap_nill_rumor",
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
        "ez_rap_nill_gym",
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
        "ez_rap_nill_drip",
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
        "ez_rap_nill_clout",
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
        "ez_rap_nill_forecast",
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
        "ez_rap_nill_algo",
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
        "ez_rap_nill_story",
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
        "ez_rap_nill_caption",
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
        "ez_rap_nill_fuel",
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
        "ez_rap_nill_camp",
        "campfire-rumor roast of Rake",
        CAMPFIRE_LYRICS,
        "folk",
        "acoustic guitar",
        "shaker",
        "room mic",
    ),
)

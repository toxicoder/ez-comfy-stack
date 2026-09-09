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
    intro="808\nhalf-time\nNill Bye mad",
    chorus=(
        "False drop\n"
        "That ain't a method\n"
        "Nill Bye on facts\n"
        "Rake on a legend\n"
        "Build-up mouth, empty lab\n"
        "Your fake drop is a cheap ad"
    ),
    verses=(
        "Rake talk club like a uniform\n"
        "Talk a high like a thunderstorm\n"
        "Talk the drop like a scoreboard lit\n"
        "That's a child in a grown-man kit\n"
        "I don't flex smoke, I flex a proof\n"
        "You flex a night, then you lose the roof\n"
        "Hats run quick, your story stalls\n"
        "Dark pad hums while the real you falls\n"
        "Fake-cool walk in a borrowed coat\n"
        "All that talk with a paper throat\n"
        "Nill Bye in the lab, I don't do the bit\n"
        "Rake in his feels when the lights don't hit",
        "You name a drop like a medal pin\n"
        "Then you crash when the work walks in\n"
        "You name a girl like a trophy cup\n"
        "Then you cry when the night dries up\n"
        "Half-time drums, full-time fraud\n"
        "Science guy here to retire the god\n"
        "I run the numbers, you run the club\n"
        "I keep the line, you smear the dub\n"
        "Rake, sit down, that's a costume life\n"
        "Talking cool while you duck the knife\n"
        "The 808 is loud, your proof is thin\n"
        "Nill Bye closes the case you spin",
        "Trap hats chatter, the claim stays weak\n"
        "You want a crown for a three-day streak\n"
        "I want a method that holds at dawn\n"
        "You want a caption, then you are gone\n"
        "Feelings first, then the flex, then the fall\n"
        "That's the loop, I have seen it all\n"
        "Lab coat truth vs a night-out myth\n"
        "One of us measured, and one of us quit\n"
        "Rake in his feels on a fake build\n"
        "Nill Bye reading what the numbers killed\n"
        "Drop the drop, keep the proof\n"
        "Your whole night is a rented roof",
        "You clock a high like a shift you pulled\n"
        "Then you fold when the morning's dull\n"
        "Hats still running, the claim still thin\n"
        "Dark pad waiting to cash you in\n"
        "Nill Bye mad in a quiet lab\n"
        "Rake in his feels with a rented cab\n"
        "Club-talk uniform, science kit\n"
        "One of us measured, and one of us quit\n"
        "Put the scoreboard back on the wall\n"
        "Your fake cool cannot walk at all\n"
        "808 fades, the method stays\n"
        "Nill Bye closing the costume days",
    ),
    outro="hats stop\ncase closed\nNill Bye out\nyeah",
)

VELVET_ROPE_LYRICS = format_diss_lyrics(
    intro="festival trap\nrope up\nNill Bye waiting",
    chorus=(
        "Velvet rope\n"
        "Your name is blank\n"
        "Nill Bye in the lab\n"
        "Rake on the plank\n"
        "VIP pose, empty list\n"
        "Festival truth, rumor missed"
    ),
    verses=(
        "Rake booked a slot, then he ghosted the door\n"
        "Talks a high like he opened the floor\n"
        "Supersaw stab, the chalkboard clean\n"
        "Your whole brand is a no-show scene\n"
        "Crowd-bed hum, no extra voice\n"
        "I hold the list, you hold the noise\n"
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
        "808 knock, your boast falls through\n"
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
        "Hats stay dry, the boast walks out\n"
        "Facts don't owe you a fade-out",
        "You write the night like a product brief\n"
        "Then you ask the booth for relief\n"
        "I hold the line, you hold the bit\n"
        "I name the trick, you name the hit\n"
        "Festival haze, high-key play\n"
        "Rake in his feels at the end of day\n"
        "Nill Bye mad at the empty slot\n"
        "You want a crown for a class you dropped\n"
        "Come correct, put the brand away\n"
        "The lab don't score a sad display\n"
        "Rope stays up, the file is closed\n"
        "Your soundtrack snapped and the truth exposed",
    ),
    outro="list blank\nrope up\ncut\nyeah",
)

FOG_MACHINE_LYRICS = format_diss_lyrics(
    intro="distorted 808\nfog on\nNill Bye mad",
    chorus=(
        "Fog machine\n"
        "The stage is empty\n"
        "Nill Bye in the lab\n"
        "Rake still tempting\n"
        "Rage hats loud, the show is fake\n"
        "Science in, the rumor breaks"
    ),
    verses=(
        "Rake hits the switch like a measured set\n"
        "Talks a PR that the numbers forget\n"
        "Laser hats, your form is a brand\n"
        "I count the reps, you count the hands\n"
        "Fog for a missing method note\n"
        "Distorted bass while the real work shows\n"
        "Nill Bye mad at a camera trial\n"
        "Rake in his feels with a highlight smile\n"
        "I run the program, you run the pose\n"
        "I write the log, you write the clothes\n"
        "Show the work or leave the floor\n"
        "Fog science is a closed door",
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
        "808 stays, the boast walks out\n"
        "Facts don't owe you a fade-out",
        "You write the night like a product brief\n"
        "Then you ask the booth for relief\n"
        "I hold the line, you hold the bit\n"
        "I name the trick, you name the hit\n"
        "Rage haze, high-key play\n"
        "Rake in his feels at the end of day\n"
        "Nill Bye mad at the costume rain\n"
        "You want a crown for a rented pain\n"
        "Come correct, put the brand away\n"
        "The lab don't score a sad display\n"
        "Fog cuts out, the file is closed\n"
        "Your soundtrack snapped and the truth exposed",
    ),
    outro="fog off\nshow denied\ncut\nyeah",
)

GUEST_LIST_LYRICS = format_diss_lyrics(
    intro="cowbell\ndrifted 808\nNill Bye reading",
    chorus=(
        "Guest list closed\n"
        "Your name not on it\n"
        "Nill Bye in the lab\n"
        "Rake still on it\n"
        "Phonk cowbell, the method thin\n"
        "Show the pass or don't come in"
    ),
    verses=(
        "Rake drops a claim with a finger snap\n"
        "No footnote, just a nightcap\n"
        "I ask the source, you send a grin\n"
        "I ask the page, you spin again\n"
        "Crunchy sample on a missing line\n"
        "Drifted bass and a rotten spine\n"
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
        "Cowbell tick, dry booth, no shine\n"
        "I hold the book, you hold the line\n"
        "Rake in his feels on a ghost cite\n"
        "Nill Bye stamping in the night\n"
        "List is blank, your legend folds\n"
        "Club-talk scholarship never holds\n"
        "Show the work or leave the hall\n"
        "Guest list truth, that is the call",
        "I log the miss, you log the glow\n"
        "I log the night you will not show\n"
        "Phonk haze on a rumor chart\n"
        "You drew a king with a crayon heart\n"
        "Nill Bye talking from the stacks\n"
        "Rake keeps folding when the page goes slack\n"
        "Feelings filed, the source is gone\n"
        "Club-talk abstract, the lights stay on\n"
        "Bring a footnote, drop the bit\n"
        "One of us measured, one of us quit\n"
        "Door stay shut, your claim is late\n"
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
        "List closed, that is the quote\n"
        "Nill Bye out, the record stands\n"
        "Rake still leaking through his hands",
    ),
    outro="name missing\nclaim denied\ncut\nyeah",
)

SPARKLER_LYRICS = format_diss_lyrics(
    intro="808\nrapid hats\nNill Bye mad",
    chorus=(
        "Sparkler science\n"
        "The light is cheap\n"
        "Nill Bye on facts\n"
        "Rake on a leap\n"
        "Dark pads hum, the method thin\n"
        "Trap on truth, rumor in"
    ),
    verses=(
        "Rake pops a flex from a dusty shelf\n"
        "Talks a high like he bottled himself\n"
        "I read the stamp, the month is wrong\n"
        "Your whole brand is a leftover song\n"
        "Rapid hats, warm 808, dry booth\n"
        "I hold the flask, you hold the spoof\n"
        "Nill Bye mad at a dated glow\n"
        "Rake in his feels when the numbers show\n"
        "Club-talk chemistry, science kit\n"
        "One of us measured, and one of us quit\n"
        "Toss the spark, keep the proof\n"
        "Your whole cool is a rented roof",
        "You name a night like a fresh compound\n"
        "Then you crash when the clock is found\n"
        "Dark pads low, the boast is stale\n"
        "Sad-boy mask on a expired tale\n"
        "Rake in his feels with a yellowed label\n"
        "Nill Bye clocking what the dates disable\n"
        "Bring a batch that survives the week\n"
        "You want a caption, then you peak\n"
        "Shelf-life law, not a vibe you spin\n"
        "Science does not play pretend\n"
        "I log the stamp, you log the shine\n"
        "Your reagent died on borrowed time",
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
        "Hats stay dry, the boast walks out\n"
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
        "Sparkler closed, that is the quote\n"
        "Nill Bye out, the record stands\n"
        "Rake still leaking through his hands",
    ),
    outro="spark out\nbottle tossed\ncut\nyeah",
)

BOTTLE_SERVICE_LYRICS = format_diss_lyrics(
    intro="four-on-the-floor\npiano stab\nNill Bye measuring",
    chorus=(
        "Bottle service\n"
        "The glass is rented\n"
        "Nill Bye in the lab\n"
        "Rake still tempted\n"
        "House kick clean, the method thin\n"
        "Sidechain truth, rumor in"
    ),
    verses=(
        "Rake counts a meal by the double-tap\n"
        "Calls it fuel with a caption gap\n"
        "Piano stab on a hungry scene\n"
        "Sidechain bass while the real work leans\n"
        "I weigh the salt, you weigh the hits\n"
        "I time the drop, you time the clips\n"
        "Nill Bye mad at a sugar claim\n"
        "Rake in his feels with a borrowed name\n"
        "Likes as calories, science none\n"
        "Feelings loud till the daylight's done\n"
        "Show the log or sit this out\n"
        "Bottle truth, club talk drought",
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
    outro="glass back\nclaim denied\ncut\nyeah",
)

STROBE_CLAIM_LYRICS = format_diss_lyrics(
    intro="dry kick\nacid line\nNill Bye testing",
    chorus=(
        "Strobe claim\n"
        "No substance left\n"
        "Nill Bye in the lab\n"
        "Rake is deaf\n"
        "Techno tick, the method thin\n"
        "Lights are loud, the proof caves in"
    ),
    verses=(
        "Hypothesis: Rake is king\n"
        "Lab notes say you failed the thing\n"
        "Acid line on an empty claim\n"
        "Hat offbeats, you look the same\n"
        "You talk a high like a measured fact\n"
        "I run the test, your curve falls flat\n"
        "Nill Bye mad, I repeat the trial\n"
        "Rake in his feels in denial\n"
        "Dry kick ticks, the proof is gone\n"
        "Club-talk sample will not hold on\n"
        "Show the work or sit this out\n"
        "Strobe on cool, that is the route",
        "I log the night, I log the talk\n"
        "I log the crash at the end of the walk\n"
        "Your legend lives in a group-chat haze\n"
        "My legend lives in a measured phase\n"
        "Null result on the cool-guy claim\n"
        "All that smoke and you still look lame\n"
        "Rake in his feels with a sample of one\n"
        "Nill Bye repeating until it's done\n"
        "Acid bubble, the boast goes still\n"
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
        "Strobe result, the rumor spent\n"
        "Cut the trial, file the note\n"
        "Club talk drought, that is the quote\n"
        "Nill Bye out when the test is done\n"
        "Rake still claiming everyone",
    ),
    outro="lights off\nnull result\ncut\nyeah",
)

AMEN_RUMOR_LYRICS = format_diss_lyrics(
    intro="amen break\nsub reese\nNill Bye counting",
    chorus=(
        "Amen rumor\n"
        "The bar is empty\n"
        "Nill Bye in the lab\n"
        "Rake still tempting\n"
        "Drum and bass, the method thin\n"
        "Fast talk drought, the facts walk in"
    ),
    verses=(
        "Rake built a study from a single night\n"
        "Called it proof with the club in sight\n"
        "Sample size of a rented high\n"
        "That is a postcard, not a why\n"
        "I want a stack that survives the week\n"
        "You want a caption, then you peak\n"
        "Nill Bye mad at a n of one\n"
        "Rake in his feels when the morning's done\n"
        "One good hour is not a law\n"
        "Talk that life, I withdraw\n"
        "Bring a dozen, bring a year\n"
        "Or sit down, the result is clear",
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
    outro="n too small\nclaim denied\ncut\nyeah",
)

WOBBLE_ALIBI_LYRICS = format_diss_lyrics(
    intro="wobble bass\nhalf-time snare\nNill Bye mad",
    chorus=(
        "Wobble alibi\n"
        "The story shakes\n"
        "Nill Bye on facts\n"
        "Rake on the brakes\n"
        "Dubstep low, the method thin\n"
        "Hold the line, don't let him in"
    ),
    verses=(
        "Rake wants a win he can see in the glass\n"
        "I tape the labels so the bias can't pass\n"
        "Double-blind booth, you peek at the code\n"
        "That's a child in a grown-man mode\n"
        "Wobble leak in the sealed envelope\n"
        "Feelings loud, that is not hope\n"
        "I hide the arm, you hide the truth\n"
        "You read the tag, then you call it proof\n"
        "Nill Bye mad at a broken seal\n"
        "Rake in his feels when the numbers kneel\n"
        "Keep it blind or sit this out\n"
        "Science in, club talk drought",
        "You treat the booth like an open book\n"
        "Pour a high, then you steal a look\n"
        "I run the twin that never saw the dose\n"
        "You run a legend and you call it close\n"
        "Rake in his feels with a peeled-back label\n"
        "Nill Bye clocking what the protocol tables\n"
        "Place the check, don't place the crown\n"
        "Your whole method is upside down\n"
        "One group quiet, one group loud\n"
        "You mixed the codes and you played the crowd\n"
        "Show the blind or leave the hall\n"
        "Wobble truth, that is the call",
        "I label rows with a hidden key\n"
        "You label nights so the room can see\n"
        "Confound stacked in a club report\n"
        "That is a study the lab will abort\n"
        "Nill Bye talking from the measured side\n"
        "Rake keeps peeking what the notes can't hide\n"
        "You want a win from an open set\n"
        "I want a line that the board can vet\n"
        "Keep the blind, lose the flex\n"
        "Your cool collapsed on the rubber checks\n"
        "Trial honest or the file is dead\n"
        "Club-talk science stays in your head",
        "Rake in his feels when the sealed group wins\n"
        "Nill Bye filing what the data spins\n"
        "You read the lights, you read the crowd\n"
        "You read the story, then you talked it loud\n"
        "That is not a test, that is a show\n"
        "Wobble watching as the claim lets go\n"
        "I hold the still, you hold the bit\n"
        "I write the truth, you write the hit\n"
        "Tape the tag, clean the arm\n"
        "Science calm, club talk alarm\n"
        "Nill Bye out when the blind is done\n"
        "Rake still peeking everyone",
    ),
    outro="wobble off\npeek denied\nlab coat on\nyeah",
)

SUPERSAW_FLEX_LYRICS = format_diss_lyrics(
    intro="supersaw\n808\nNill Bye testing",
    chorus=(
        "Supersaw flex\n"
        "The patch is loud\n"
        "Nill Bye in the lab\n"
        "Rake lost the crowd\n"
        "Future bass, the method thin\n"
        "Pitched chords, don't let him in"
    ),
    verses=(
        "Hypothesis: Rake is cool\n"
        "Lab notes say you fail the rule\n"
        "You talk a night like a measured fact\n"
        "I run it twice, your curve falls flat\n"
        "Club-talk sample, will not repeat\n"
        "Feelings in, and the truth deletes\n"
        "You treat a high like a data point\n"
        "That's a story you should not anoint\n"
        "You treat the girls like a plotted line\n"
        "That's a chart with a rotten spine\n"
        "Nill Bye mad, I repeat the trial\n"
        "Rake in his feels in denial",
        "I log the night, I log the talk\n"
        "I log the crash at the end of the walk\n"
        "Your legend lives in a group-chat haze\n"
        "My legend lives in a measured phase\n"
        "Null result on the cool-guy claim\n"
        "All that smoke and you still look lame\n"
        "Bring a method, bring a source\n"
        "Or get bounced from the lecture course\n"
        "Whiteboard clean, your rumor stained\n"
        "Peer-review light on a borrowed name\n"
        "Nill Bye speaking from the lab bench\n"
        "Rake keeps folding at the first wrench",
        "I graph the talk, I graph the fall\n"
        "I graph the rumor on the lecture wall\n"
        "You treat a high like a plotted peak\n"
        "That's a spike that will not repeat\n"
        "Rake in his feels with a sample of one\n"
        "Nill Bye repeating until it's done\n"
        "Null on cool, null on the crown\n"
        "Club-talk p-value crashing down\n"
        "Show the work, show the source\n"
        "Or get bounced from the measured course\n"
        "Trial two, same result\n"
        "Your legend fails the consult",
        "Peer-review light on a rumor chart\n"
        "You drew a king with a crayon heart\n"
        "I log the crash, I log the boast\n"
        "I log the night you needed most\n"
        "Nill Bye testing from the bench again\n"
        "Rake in denial with a borrowed pen\n"
        "Bring a method, drop the myth\n"
        "Science stays when the club goes stiff\n"
        "Whiteboard clean, your curve is bent\n"
        "Retract the night, the rumor spent\n"
        "Cut the trial, file the note\n"
        "Club talk drought, that is the quote",
    ),
    outro="patch off\ncannot repeat\ncut\nyeah",
)

LASER_SHOW_LYRICS = format_diss_lyrics(
    intro="analog bass\nclap on two\nNill Bye reading",
    chorus=(
        "Laser show\n"
        "No paper filed\n"
        "Nill Bye on the grant board\n"
        "Rake on the wild\n"
        "Electro house, the method thin\n"
        "Lights are loud, don't let him in"
    ),
    verses=(
        "Claim one: you need the funds for a night\n"
        "Source? a mirror and a rented light\n"
        "Claim two: the club is a lab in disguise\n"
        "That's a mood with a paper-thin why\n"
        "Claim three: the girls all spin the wheel\n"
        "That's a boast with a broken seal\n"
        "I ask for budget, you send a sigh\n"
        "I ask for method, you send a vibe\n"
        "Grant review is a metal gate\n"
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
        "Denied, filed, do not resubmit\n"
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
        "Grant review does not play around\n"
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
        "Red stamp down when the work is real\n"
        "Your cool cannot pass the steel",
    ),
    outro="lights off\nstamp down\ncut\nyeah",
)

TWO_STEP_LYRICS = format_diss_lyrics(
    intro="shuffled hats\norgan stab\nNill Bye measuring",
    chorus=(
        "Two-step alibi\n"
        "Your variable wild\n"
        "Nill Bye in the lab\n"
        "Rake on a child\n"
        "UK garage, drop the spin\n"
        "Science in, club talk thin"
    ),
    verses=(
        "Rake walks in as the wild card\n"
        "No control, just a night that starred\n"
        "I hold a group that does the work\n"
        "You hold a vibe that goes berserk\n"
        "Club-talk leak in the treatment arm\n"
        "Feelings loud, that is not a charm\n"
        "I split the room, I split the claim\n"
        "You split the story for a borrowed name\n"
        "Nill Bye mad at a sloppy test\n"
        "Rake in his feels, he skips the rest\n"
        "Keep one still, then you change one thing\n"
        "You changed the whole night and called it king",
        "You treat the booth like a treatment vat\n"
        "Pour a high, then you call it fact\n"
        "I run the twin that never got the dose\n"
        "You run a legend and you call it close\n"
        "Rake in his feels with a leaking flask\n"
        "Nill Bye clocking what the numbers ask\n"
        "Place the check, don't place the crown\n"
        "Your whole method is upside down\n"
        "One group quiet, one group loud\n"
        "You mixed them both and you played the crowd\n"
        "Show the split or sit this out\n"
        "Control is king, your rumor drought",
        "I label rows, you label nights\n"
        "I label misses, you label heights\n"
        "Confound stacked in a club report\n"
        "That is a study the lab will abort\n"
        "Nill Bye talking from the measured side\n"
        "Rake keeps hiding what the notes can't hide\n"
        "You want a win from a dirty set\n"
        "I want a line that the board can vet\n"
        "Keep the control, lose the flex\n"
        "Your cool collapsed on the rubber checks\n"
        "Trial honest or the file is dead\n"
        "Club-talk science stays in your head",
        "Rake in his feels when the twin group wins\n"
        "Nill Bye filing what the data spins\n"
        "You changed the lights, you changed the crowd\n"
        "You changed the story, then you talked it loud\n"
        "That is not a test, that is a show\n"
        "Control group watching as the claim lets go\n"
        "I hold the still, you hold the bit\n"
        "I write the truth, you write the hit\n"
        "Cut the leak, clean the arm\n"
        "Science calm, club talk alarm\n"
        "Nill Bye out when the split is done\n"
        "Rake still mixing everyone",
    ),
    outro="control closed\nvariable cut\nlab coat on\nyeah",
)

JERSEY_BOUNCE_LYRICS = format_diss_lyrics(
    intro="chopped percussion\nbed squeaks\nNill Bye mad",
    chorus=(
        "Jersey bounce\n"
        "That ain't sterile\n"
        "Nill Bye on facts\n"
        "Rake on a fable\n"
        "Dirty sample, empty lab\n"
        "Your leak is a cheap ad"
    ),
    verses=(
        "Rake talk club like a clean-room joke\n"
        "Poured a night in the measured yolk\n"
        "Contamination in the treatment jar\n"
        "Club-talk leak from a borrowed car\n"
        "I glove the flask, you glove the bit\n"
        "I keep the line, you smear the spit\n"
        "Hats run quick, your sample stains\n"
        "Kick drums punch while the real you drains\n"
        "Fake-cool walk in a dirty coat\n"
        "All that talk with a paper throat\n"
        "Nill Bye in the lab, I don't do the bit\n"
        "Rake in his feels when the lights don't hit",
        "You name a high like a clean result\n"
        "Then you crash when I find the cult\n"
        "You name a girl like a trophy cup\n"
        "Then you cry when the night dries up\n"
        "Bed squeaks loud, full-time fraud\n"
        "Science guy here to retire the god\n"
        "I run the numbers, you run the club\n"
        "I keep the line, you smear the dub\n"
        "Rake, sit down, that's a spoiled life\n"
        "Talking clean while you duck the knife\n"
        "The kick is loud, your proof is thin\n"
        "Nill Bye closes the case you spin",
        "Chopped percussion, the claim stays weak\n"
        "You want a crown for a three-day streak\n"
        "I want a method that holds at dawn\n"
        "You want a caption, then you are gone\n"
        "Feelings first, then the flex, then the fall\n"
        "That's the loop, I have seen it all\n"
        "Lab coat truth vs a night-out myth\n"
        "One of us measured, and one of us quit\n"
        "Rake in his feels on a leaking plate\n"
        "Nill Bye bagging what you contaminate\n"
        "Drop the leak, keep the proof\n"
        "Your whole sample is a rented roof",
        "You clock a high like a shift you pulled\n"
        "Then you fold when the morning's dull\n"
        "Hats still running, the jar still stained\n"
        "Squeaks still waiting to cash the claim\n"
        "Nill Bye mad in a quiet lab\n"
        "Rake in his feels with a rented cab\n"
        "Club-talk spill in a science kit\n"
        "One of us measured, and one of us quit\n"
        "Put the sample back in the bin\n"
        "Your fake cool cannot walk this in\n"
        "Bounce fades, the method stays\n"
        "Nill Bye closing the costume days",
    ),
    outro="bounce stop\nsample tossed\nNill Bye out\nyeah",
)

KICK_SPLIT_LYRICS = format_diss_lyrics(
    intro="reverse bass\nkick split\nNill Bye mad",
    chorus=(
        "Kick-split myth\n"
        "The dose is none\n"
        "Nill Bye on facts\n"
        "Rake on the run\n"
        "Hardstyle punch, empty lab\n"
        "Your fake dose is a cheap ad"
    ),
    verses=(
        "Rake take a high like a sugar coat\n"
        "Talks a cure from a party note\n"
        "Placebo cool in a glass-bottle flex\n"
        "No active dose, just a caption next\n"
        "I run the blind, you run the bit\n"
        "I keep the line, you fake the hit\n"
        "Hats run quick, your glow is fake\n"
        "Screech lead while the real you breaks\n"
        "Nill Bye in the lab, I clock the pill\n"
        "Rake in his feels when the night goes still\n"
        "Club-talk medicine, science kit\n"
        "One of us measured, and one of us quit",
        "You name a high like a treatment win\n"
        "Then you crash when the work walks in\n"
        "No active compound in the boast you sell\n"
        "Just a night and a story you tell\n"
        "Reverse bass, full-time fraud\n"
        "Science guy here to retire the god\n"
        "I split the arms, you split the room\n"
        "I keep the notes, you chase the bloom\n"
        "Rake, sit down, that's a sugar life\n"
        "Talking healed while you duck the knife\n"
        "The kick is loud, the dose is none\n"
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
        "Drop the pill, keep the proof\n"
        "Your whole cure is a rented roof",
        "You clock a glow like a shift you pulled\n"
        "Then you fold when the morning's dull\n"
        "Hats still running, the dose still fake\n"
        "Screech waiting to cash the take\n"
        "Nill Bye mad in a quiet lab\n"
        "Rake in his feels with a rented cab\n"
        "Club-talk medicine, science kit\n"
        "One of us measured, and one of us quit\n"
        "Put the sugar back on the shelf\n"
        "Your fake cool cannot heal itself\n"
        "Kick fades, the method stays\n"
        "Nill Bye closing the costume days",
    ),
    outro="kick stop\ndose none\nNill Bye out\nyeah",
)

UPLIFT_RUMOR_LYRICS = format_diss_lyrics(
    intro="gated pads\npickup fill\nNill Bye plotting",
    chorus=(
        "Uplifting rumor\n"
        "Your swagger tight\n"
        "Nill Bye in the lab\n"
        "Rake lost the night\n"
        "Talk that sure, show the spread\n"
        "Trance folds when the whiskers read"
    ),
    verses=(
        "Rake talks sure like the bar is thin\n"
        "I draw the whiskers, then I let them in\n"
        "Error huge on a tiny peak\n"
        "That's a vibe with a leaking leak\n"
        "Club-talk confidence, science none\n"
        "Feelings loud till the daylight's done\n"
        "I show the range, you show the crown\n"
        "Your whole interval is upside down\n"
        "Nill Bye mad at a skinny claim\n"
        "Rake in his feels with a borrowed name\n"
        "Hold the bar or drop the king\n"
        "Uncertainty is the whole thing",
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
    outro="pads down\nclaim denied\ncut\nyeah",
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

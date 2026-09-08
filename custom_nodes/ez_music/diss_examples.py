"""Canned 90s Nill Bye vs Rake diss takes for ACE-Step rap lab graphs.

Fictional MCs only. Original lyrics. No living-artist names.
"""

from __future__ import annotations

from typing import TypedDict

BOOM_BAP_TAGS_88 = (
    "boom bap, hip-hop, dusty drums, vinyl crackle, dry snare, sampled piano "
    "stab, upright bass, male rap vocals, dry booth, no autotune, 88 bpm"
)
BOOM_BAP_TAGS_92 = (
    "boom bap, hip-hop, dusty drums, vinyl crackle, dry snare, sampled piano "
    "stab, upright bass, male rap vocals, dry booth, no autotune, 92 bpm"
)
TRAP_TAGS = (
    "trap, 808 bass, rapid hi-hats, dark pads, male rap vocals, half-time, 140 bpm"
)
LOFI_TAGS = (
    "lo-fi hip-hop, dusty drums, rhodes, vinyl crackle, laid-back male rap vocals, 86 bpm"
)

DISS_DURATION_S = 90.0


class DissExample(TypedDict):
    stem: str
    title: str
    tags: str
    bpm: int
    duration: float
    seed: int
    prefix: str
    description: str
    lyrics: str


LAB_COAT_LYRICS = """[intro]
yeah
lab coat on
Nill Bye talking

[verse]
Rake walks in with a club report
Talks a high like a science sport
Name-drops girls like a trophy board
That's a vibe, that is not a law
I run tests, you run your mouth
I write notes, you write a drought
Beaker clean, your story stained
Feelings loud, the method lame
You skip class, then you talk so big
I drop facts, you drop a gig
Lab light on, your night light off
Proof in glass, your proof is talk

[chorus]
Nill Bye in the lab coat
Rake in his feelings
Science on the downbeat
Club talk is leaking
You talk cool, I talk true
Your flex failed the review

[verse]
You treat the booth like a diary page
Sad-boy loop on a rented stage
I count the moles, you count the stares
I map the world, you map the stares
Hold the flask, don't hold the room
Your cool is smoke, my cool is proof
Talk that life like a highlight reel
Then you crash out when the night gets real
I came mad from the lecture hall
You came soft with a curtain call
Nill Bye speaking, the whiteboard wins
Rake keeps leaking those made-up sins

[chorus]
Nill Bye in the lab coat
Rake in his feelings
Science on the downbeat
Club talk is leaking
You talk cool, I talk true
Your flex failed the review

[outro]
class dismissed
cut the mic
lab coat on
yeah"""

PEER_REVIEW_LYRICS = """[spoken word]
Peer review time
Rake submitted feelings
Zero citations
Rejected

[intro]
red pen out
Nill Bye reading

[verse]
Claim one: you live so loud
Source? a mirror and a crowd
Claim two: the night is proof
That's a mood, that is not truth
Claim three: the girls all spin
That's a boast with a paper-thin
I ask for data, you send a sigh
I ask for method, you send a vibe
Peer review is a metal gate
Your whole brand is a late debate
Stamp denied on the title page
Feelings filed in an empty cage

[chorus]
Nill Bye on the red pen
Rake on the sad end
No citations in the stack
Send that rumor right back
Science reads, club talk folds
Your thesis melted in the cold

[verse]
You pad the abstract with a club-night tale
Then you fold when the numbers fail
I cite the graph, you cite the mood
I run the trial, you run the room
Rake in his feels with a borrowed crown
Nill Bye in the lab taking fiction down
Edit your draft, lose the trophy talk
Keep the feelings, drop the fake-cool walk
The board is cold and the lights are harsh
Your legend ends at the loading dock
Rejected, filed, do not resubmit
Bring a method or get off the spit

[chorus]
Nill Bye on the red pen
Rake on the sad end
No citations in the stack
Send that rumor right back
Science reads, club talk folds
Your thesis melted in the cold

[outro]
peer review closed
red pen down
cut"""

FEELS_LYRICS = """[intro]
soft drums
hard facts
Nill Bye here

[verse]
Rake in his feels like a full-time job
Writes the rain on a nameless blog
Talks the pain like a product line
Sells the tear with a catchy shine
I respect grief, I reject the brand
You wear the mood like a souvenir stand
Laid-back loop, high-key fraud
Sad-boy mask on a rented god
You tell the night it was all so deep
I tell the night you were fast asleep
Feelings real until they pay the rent
Then the diary turns to a paid event

[chorus]
Nill Bye with the cold read
Rake in his feels again
Science don't bend for a sad hook
Club talk is a dead look
Keep your rain, lose the act
Facts don't owe you a soundtrack

[verse]
You talk the girls like a weather report
Storm then sun, then you want support
You talk a high like a badge you earned
That's a story the lab returned
Nill Bye mad at the costume grief
Rake on loop like a falling leaf
I hold a note, you hold a pose
I write the truth, you write the lows
Soft keys hum while the boast falls through
Your whole cool is a borrowed blue
Come correct or don't come at all
The booth is small and the facts stand tall

[chorus]
Nill Bye with the cold read
Rake in his feels again
Science don't bend for a sad hook
Club talk is a dead look
Keep your rain, lose the act
Facts don't owe you a soundtrack

[outro]
feelings noted
claim denied
soft out
yeah"""

FAKE_COOL_LYRICS = """[intro]
808
half-time
Nill Bye mad

[verse]
Rake talk club like a uniform
Talk a high like a thunderstorm
Talk the girls like a scoreboard lit
That's a child in a grown-man kit
I don't flex smoke, I flex a proof
You flex a night, then you lose the roof
Hats run quick, your story stalls
Dark pad hums while the real you falls
Fake-cool walk in a borrowed coat
All that talk with a paper throat
Nill Bye in the lab, I don't do the bit
Rake in his feels when the lights don't hit

[chorus]
Talk that club talk
That ain't a method
Nill Bye on facts
Rake on a legend
Scoreboard mouth, empty lab
Your fake cool is a cheap ad

[verse]
You name a high like a medal pin
Then you crash when the work walks in
You name a girl like a trophy cup
Then you cry when the night dries up
Half-time drums, full-time fraud
Science guy here to retire the god
I run the numbers, you run the club
I keep the line, you smear the dub
Rake, sit down, that's a costume life
Talking cool while you duck the knife
The 808 is loud, your proof is thin
Nill Bye closes the case you spin

[verse]
Trap hats chatter, the claim stays weak
You want a crown for a three-day streak
I want a method that holds at dawn
You want a caption, then you are gone
Feelings first, then the flex, then the fall
That's the loop, I have seen it all
Lab coat truth vs a night-out myth
One of us measured, and one of us quit

[chorus]
Talk that club talk
That ain't a method
Nill Bye on facts
Rake on a legend
Scoreboard mouth, empty lab
Your fake cool is a cheap ad

[outro]
hats stop
case closed
Nill Bye out
yeah"""

HYPOTHESIS_LYRICS = """[intro]
null result
Nill Bye testing

[verse]
Hypothesis: Rake is cool
Lab notes say the claim is cruel
You talk rumors like a measured fact
I run the test, your curve falls flat
Club-talk sample, bias high
Feelings in, and the truth walks by
You treat a high like a data point
That's a story you should not anoint
You treat the girls like a plotted line
That's a chart with a rotten spine
Nill Bye mad, I repeat the trial
Rake in his feels in denial

[chorus]
Hypothesis up
Your rumor is down
Nill Bye in the lab
Rake lost the crown
Show the work or sit this out
Science wins, club talk drought

[verse]
I log the night, I log the talk
I log the crash at the end of the walk
Your legend lives in a group-chat haze
My legend lives in a measured phase
Null result on the cool-guy claim
All that smoke and you still look lame
Bring a method, bring a source
Or get bounced from the lecture course
Whiteboard clean, your rumor stained
Peer-review light on a borrowed name
Nill Bye speaking from the lab bench
Rake keeps folding at the first wrench

[chorus]
Hypothesis up
Your rumor is down
Nill Bye in the lab
Rake lost the crown
Show the work or sit this out
Science wins, club talk drought

[outro]
trial over
null result
cut
yeah"""


DISS_EXAMPLES: tuple[DissExample, ...] = (
    {
        "stem": "music-rap-nill-bye-lab-coat-lab-example",
        "title": "lab coat lecture",
        "tags": BOOM_BAP_TAGS_88,
        "bpm": 88,
        "duration": DISS_DURATION_S,
        "seed": 42,
        "prefix": "ez_rap_nill_labcoat",
        "description": (
            "US-safe rap 90s diss: Nill Bye lab-coat roast of Rake, "
            "ACE-Step 1.5 turbo AIO, invented vocal"
        ),
        "lyrics": LAB_COAT_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-peer-review-lab-example",
        "title": "peer review",
        "tags": BOOM_BAP_TAGS_88,
        "bpm": 88,
        "duration": DISS_DURATION_S,
        "seed": 42,
        "prefix": "ez_rap_nill_review",
        "description": (
            "US-safe rap 90s diss: Nill Bye peer-review roast of Rake, "
            "ACE-Step 1.5 turbo AIO, invented vocal"
        ),
        "lyrics": PEER_REVIEW_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-feels-lab-example",
        "title": "in his feels",
        "tags": LOFI_TAGS,
        "bpm": 86,
        "duration": DISS_DURATION_S,
        "seed": 42,
        "prefix": "ez_rap_nill_feels",
        "description": (
            "US-safe rap 90s diss: Nill Bye lo-fi roast of Rake in his feels, "
            "ACE-Step 1.5 turbo AIO, invented vocal"
        ),
        "lyrics": FEELS_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-fake-cool-lab-example",
        "title": "fake cool",
        "tags": TRAP_TAGS,
        "bpm": 140,
        "duration": DISS_DURATION_S,
        "seed": 42,
        "prefix": "ez_rap_nill_fakecool",
        "description": (
            "US-safe rap 90s diss: Nill Bye trap roast of Rake fake-cool talk, "
            "ACE-Step 1.5 turbo AIO, invented vocal"
        ),
        "lyrics": FAKE_COOL_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-hypothesis-lab-example",
        "title": "hypothesis vs rumor",
        "tags": BOOM_BAP_TAGS_92,
        "bpm": 92,
        "duration": DISS_DURATION_S,
        "seed": 7,
        "prefix": "ez_rap_nill_hypothesis",
        "description": (
            "US-safe rap 90s diss: Nill Bye hypothesis roast of Rake, "
            "ACE-Step 1.5 turbo AIO, invented vocal"
        ),
        "lyrics": HYPOTHESIS_LYRICS,
    },
)

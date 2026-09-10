"""Canned lab-catalog 180s Nill Bye vs Rake diss takes.

Fictional MCs only. Original lyrics. No living-artist names.
Imported by diss_examples after types and tag constants exist.
"""

from __future__ import annotations

from .diss_examples import (
    BOOM_BAP_TAGS_88,
    BOOM_BAP_TAGS_92,
    DISS_DURATION_S,
    DissExample,
    LOFI_TAGS,
    TRAP_TAGS,
    _desc,
    format_diss_lyrics,
    nill_output_prefix,
)

LAB_PHASE = 0

LAB_COAT_LYRICS = format_diss_lyrics(
    intro="yeah\nlab coat on\nNill Bye talking",
    chorus=(
        "Nill Bye in the lab coat\n"
        "Rake in the back row\n"
        "Lecture hits the downbeat\n"
        "You ghosted the demo\n"
        "Coat on, the rumor folds\n"
        "Your flex failed the roll"
    ),
    verses=(
        "Rake walks in with a club report\n"
        "Talks a high like a science sport\n"
        "Treats a rumor like a binding law\n"
        "I sketch the miss in the lecture draw\n"
        "I run tests, you run your mouth\n"
        "Your whole legend blew in from the south\n"
        "Beaker clean, your story stained\n"
        "Mine got boiled, yours never trained\n"
        "You skip class, then you talk so big\n"
        "I drop facts, you drop a weak gig\n"
        "Nill Bye talking with the lecture off\n"
        "Proof in glass, you brought a scoff",
        "You treat the booth like a diary page\n"
        "Sad-boy loop on a rented stage\n"
        "I count the moles, you count the stares\n"
        "I map the flask, you map the airs\n"
        "Hold the flask, don't hold the room\n"
        "Your cool is smoke, my cool is bloom\n"
        "Talk that life like a highlight reel\n"
        "Then you crash out when the night gets real\n"
        "I came mad from the lecture hall\n"
        "You came soft with a curtain call\n"
        "Nill Bye speaking, the whiteboard wins\n"
        "Rake keeps leaking those made-up sins",
        "You skip the hood, you skip the glove\n"
        "Call it swag, I call it shove\n"
        "I weigh the salt, you weigh the likes\n"
        "I time the drop, you time the nights\n"
        "You borrow cool from a spotlight\n"
        "I borrow nothing, I write it right\n"
        "Club report folded, the margin blank\n"
        "Your whole method is a credit rank\n"
        "Show the work or leave the hall\n"
        "Lab coat truth, that is the call\n"
        "Nill Bye in the coat for a long trial\n"
        "Rake with a name-tag smile",
        "Front-row empty, you ghost the slot\n"
        "Then you flex like you gave a lot\n"
        "I grade the claim with a colder eye\n"
        "You grade the night with a rented high\n"
        "Beaker rings, your chain is loud\n"
        "One of us measured, one of us proud\n"
        "Cut the rumor, keep the fact\n"
        "Lab light on, no turning back\n"
        "Class is long and the proof is slow\n"
        "Your cool expired two weeks ago\n"
        "Nill Bye talking from the front row\n"
        "Rake keeps posing for a highlight show",
    ),
    outro="class dismissed\ncut the mic\nlab coat on\nyeah",
)

PEER_REVIEW_LYRICS = format_diss_lyrics(
    spoken=(
        "Peer review time\n"
        "Rake submitted feelings\n"
        "Zero citations\n"
        "Rejected"
    ),
    intro="red pen out\nNill Bye marking",
    chorus=(
        "Nill Bye on the red pen\n"
        "Rake on the sad end\n"
        "No citations in the stack\n"
        "Send that rumor right back\n"
        "Science reads, the boast folds\n"
        "Your thesis melted in the cold"
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
        "Peer review is a metal gate\n"
        "Your whole brand is a late debate\n"
        "Nill Bye stamping the title page\n"
        "Rake filed feelings in an empty cage",
        "You pad the abstract with a club-night tale\n"
        "Then you fold when the numbers fail\n"
        "I cite the graph, you cite the mood\n"
        "I run the trial, you run the room\n"
        "Edit your draft, lose the trophy talk\n"
        "Keep the feelings, drop the costume walk\n"
        "The board is cold and the lights are harsh\n"
        "Your legend ends at the loading dock\n"
        "Rejected, filed, do not resubmit\n"
        "Bring a method or get off the spit\n"
        "Nill Bye taking fiction down\n"
        "Rake with a borrowed crown",
        "You cite a vibe with a broken link\n"
        "I cite a table, then I let it sink\n"
        "Revise and resubmit is a gift\n"
        "You treat a note like a personal rift\n"
        "Margin red, your caption gold\n"
        "That is a story the lab will hold\n"
        "Bring a method, drop the crown\n"
        "Peer review does not play around\n"
        "Nill Bye reading till the ink is dry\n"
        "Rake still leaking a lullaby\n"
        "Stamp denied on the comment thread\n"
        "Feelings cannot pass the steel",
        "Desk copy lost, your legend stays\n"
        "Until the numbers cut the haze\n"
        "I run the check, you run the spin\n"
        "I log the miss, you log a win\n"
        "Feelings filed, the drawer is shut\n"
        "Padded abstract, the door stays cut\n"
        "Do not resubmit the same old night\n"
        "Bring a source or step off the mic\n"
        "Red pen down when the work is real\n"
        "Your cool cannot pass the steel\n"
        "Nill Bye mad at a padded claim\n"
        "Rake with a borrowed name",
    ),
    outro="peer review closed\nred pen down\ncut",
)

FEELS_LYRICS = format_diss_lyrics(
    intro="soft drums\nhard facts\nNill Bye here",
    chorus=(
        "Nill Bye with the cold read\n"
        "Rake in his feels again\n"
        "Science don't bend for a sad hook\n"
        "Your diary is a dead look\n"
        "Keep your rain, lose the act\n"
        "Facts don't owe you a soundtrack"
    ),
    verses=(
        "Rake in his feels like a full-time job\n"
        "Writes the rain on a nameless blog\n"
        "Talks the pain like a product line\n"
        "Sells the tear with a catchy shine\n"
        "I respect grief, I reject the brand\n"
        "You wear the mood like a souvenir stand\n"
        "Laid-back loop, high-key fraud\n"
        "Sad-boy mask on a rented god\n"
        "You tell the night it was all so deep\n"
        "I tell the night you were fast asleep\n"
        "Nill Bye here for the merch event\n"
        "Feelings real until they pay the rent",
        "You talk the girls like a weather report\n"
        "Storm then sun, then you want support\n"
        "You talk a high like a badge you earned\n"
        "That's a story the lab returned\n"
        "I hold a note, you hold a pose\n"
        "I write the truth, you write the lows\n"
        "Soft keys hum while the boast falls through\n"
        "Your whole cool is a borrowed blue\n"
        "Come correct or don't come at all\n"
        "The booth is small and the facts stand tall\n"
        "Nill Bye mad at the costume grief\n"
        "Rake on loop like a falling leaf",
        "You sell the sigh like a limited drop\n"
        "Then you crash when the playlist stops\n"
        "I clock the rain, I clock the pose\n"
        "I clock the brand in the borrowed clothes\n"
        "Grief is real, the merch is not\n"
        "You wrapped a wound in a camera shot\n"
        "Keep the tear, lose the store\n"
        "Sad-boy aisle, I close the door\n"
        "Soft drums stay, the boast walks out\n"
        "Facts don't owe you a fade-out\n"
        "Nill Bye reading through the window pane\n"
        "Rake on a looped refrain",
        "You write the night like a product brief\n"
        "Then you ask the booth for relief\n"
        "I hold the line, you hold the bit\n"
        "I name the trick, you name the hit\n"
        "Lo-fi haze, high-key play\n"
        "You want a crown for a rented pain\n"
        "Come correct, put the brand away\n"
        "The lab don't score a sad display\n"
        "Cold read done, the file is closed\n"
        "Your soundtrack snapped and the truth exposed\n"
        "Nill Bye mad at the costume rain\n"
        "Rake in his feels at the end of day",
    ),
    outro="feelings noted\nclaim denied\nsoft out\nyeah",
)

FAKE_COOL_LYRICS = format_diss_lyrics(
    intro="808\nhalf-time\nNill Bye pacing",
    chorus=(
        "Talk that club talk\n"
        "That ain't a method\n"
        "Nill Bye on facts\n"
        "Rake on a legend\n"
        "Scoreboard mouth, empty booth\n"
        "Your fake cool is a cheap ad"
    ),
    verses=(
        "Rake talk club like a uniform\n"
        "Talk a high like a thunderstorm\n"
        "Talk the girls like a scoreboard lit\n"
        "That's a child in a grown-man kit\n"
        "I don't flex smoke, I flex a proof\n"
        "You flex a night, then you lose the roof\n"
        "Hats run quick, your story stalls\n"
        "Dark pad hums while the real you falls\n"
        "Fake-cool walk in a borrowed coat\n"
        "All that talk with a paper throat\n"
        "Nill Bye pacing, I don't do the bit\n"
        "Lights don't hit, you fold the skit",
        "You name a high like a medal pin\n"
        "Then you crash when the work walks in\n"
        "You name a girl like a trophy cup\n"
        "Then you cry when the night dries up\n"
        "Half-time drums, full-time fraud\n"
        "Science guy here to retire the god\n"
        "I run the numbers, you run the club\n"
        "I keep the line, you smear the dub\n"
        "Sit down, that's a costume life\n"
        "Talking cool while you duck the knife\n"
        "Nill Bye closes the case you spin\n"
        "Rake, the 808 is loud, your proof is thin",
        "Trap hats chatter, the claim stays weak\n"
        "You want a crown for a three-day streak\n"
        "I want a method that holds at dawn\n"
        "You want a caption, then you are gone\n"
        "Feelings first, then the flex, then the fall\n"
        "That's the loop, I have seen it all\n"
        "Coat-truth versus a night-out myth\n"
        "One of us measured, and one of us quit\n"
        "Drop the drop, keep the proof\n"
        "Your whole night is a rented roof\n"
        "Nill Bye reading what the numbers killed\n"
        "Rake on a fake build",
        "You clock a high like a shift you pulled\n"
        "Then you fold when the morning's dull\n"
        "Hats still running, the claim still thin\n"
        "Dark pad waiting to cash you in\n"
        "Club-talk uniform, science kit\n"
        "One of us measured, and one of us quit\n"
        "Put the scoreboard back on the wall\n"
        "Your fake cool cannot walk at all\n"
        "808 fades, the method stays\n"
        "Costume days get filed away\n"
        "Nill Bye mad in a quiet booth\n"
        "Rake with a rented cab",
    ),
    outro="hats stop\ncase closed\nNill Bye out\nyeah",
)

HYPOTHESIS_LYRICS = format_diss_lyrics(
    intro="H-zero up\nNill Bye checking",
    chorus=(
        "Hypothesis up\n"
        "Your rumor is down\n"
        "Nill Bye on the bench\n"
        "Rake lost the crown\n"
        "Show the work or sit this out\n"
        "Science wins, the gossip drought"
    ),
    verses=(
        "Hypothesis: Rake is cool\n"
        "Lab notes say the claim is cruel\n"
        "You talk rumors like a measured fact\n"
        "I run the test, your curve falls flat\n"
        "Gossip sample, bias high\n"
        "Feelings in, and the truth walks by\n"
        "You treat a high like a data point\n"
        "That's a story you should not anoint\n"
        "You treat the girls like a plotted line\n"
        "That's a chart with a rotten spine\n"
        "Nill Bye mad, I repeat the trial\n"
        "Rake in denial",
        "I log the night, I log the talk\n"
        "I log the crash at the end of the walk\n"
        "Your legend lives in a group-chat haze\n"
        "My legend lives in a measured phase\n"
        "Cool-guy claim, the curve is lame\n"
        "All that smoke and you still look the same\n"
        "Bring a method, bring a source\n"
        "Or get bounced from the lecture course\n"
        "Board wiped clean, your rumor stained\n"
        "Reviewer light on a borrowed name\n"
        "Nill Bye speaking from the lab bench\n"
        "Rake keeps folding at the first wrench",
        "I graph the talk, I graph the fall\n"
        "I graph the rumor on the lecture wall\n"
        "You treat a high like a plotted peak\n"
        "That's a spike that will not repeat\n"
        "Cool is null, and so is the crown\n"
        "Gossip p-value crashing down\n"
        "Show the work, show the source\n"
        "Or get bounced from the measured course\n"
        "Trial two, same result\n"
        "Your legend fails the consult\n"
        "Nill Bye repeating until it's done\n"
        "Rake with a sample he will not shun",
        "Reviewer light on a rumor chart\n"
        "You drew a king with a crayon heart\n"
        "Bring a method, drop the myth\n"
        "Science stays when the club goes stiff\n"
        "Board wiped clean, your curve is bent\n"
        "Rumor spent, the boast got sent\n"
        "Cut the trial, file the note\n"
        "Gossip drought, that is the quote\n"
        "Nill Bye out when the test is done\n"
        "Rake still claiming everyone\n"
        "Twice the run, the same old stall\n"
        "H-zero stands, you never measured at all",
    ),
    outro="trial over\nH-zero holds\ncut\nyeah",
)

CONTROL_GROUP_LYRICS = format_diss_lyrics(
    intro="yeah\ncontrol on\nNill Bye splitting",
    chorus=(
        "Control group clean\n"
        "Your variable wild\n"
        "Nill Bye on the split\n"
        "Rake on a child\n"
        "Hold the line, drop the spin\n"
        "Science in, the gossip thin"
    ),
    verses=(
        "Rake walks in as the wild card\n"
        "No control, just a night that starred\n"
        "I hold a group that does the work\n"
        "You hold a vibe that goes berserk\n"
        "Gossip leak in the treatment arm\n"
        "Feelings loud, that is not a charm\n"
        "I split the room, I split the claim\n"
        "You split the story for a borrowed name\n"
        "Keep one still, then you change one thing\n"
        "You changed the whole night and called it king\n"
        "Nill Bye mad at a sloppy test\n"
        "He skips the rest",
        "You treat the booth like a treatment vat\n"
        "Pour a high, then you call it fact\n"
        "I run the twin that never got the dose\n"
        "You run a legend and you call it close\n"
        "Place the check, don't place the crown\n"
        "Your whole method is upside down\n"
        "One group still, one group loud\n"
        "You mixed the arms and you worked the crowd\n"
        "I want a twin that can hold the line\n"
        "You want a caption with a borrowed shine\n"
        "Nill Bye clocking what the numbers ask\n"
        "Rake with a leaking flask",
        "I label rows, you label nights\n"
        "I want a baseline, you want the lights\n"
        "Change one knob, then you read the shift\n"
        "You spun the whole room and you called it gift\n"
        "Confound stacked in a party report\n"
        "That is a child in a grown-man sport\n"
        "Hold the twin or abort the flex\n"
        "Your design dies at the first checks\n"
        "Nill Bye filing what the data spins\n"
        "Rake when the twin group wins\n"
        "Keep the still arm, drop the charm\n"
        "Your variable set off the alarm",
        "Design clean, your night is a mess\n"
        "I want a protocol, you want a yes\n"
        "Randomize, then you hide the key\n"
        "I want a line that the board can see\n"
        "One change only, you changed the set\n"
        "Now the twin group is the threat\n"
        "Nill Bye out when the split is done\n"
        "Rake still claiming the wild-card run\n"
        "Hold the baseline, drop the myth\n"
        "Science stays when the gossip's stiff\n"
        "Wild card folded, the still arm won\n"
        "Your whole night was a confound run",
    ),
    outro="control closed\nvariable cut\nbaseline on\nyeah",
)

SAMPLE_SIZE_LYRICS = format_diss_lyrics(
    intro="n equals one\nNill Bye counting",
    chorus=(
        "Sample size tiny\n"
        "Your claim too wide\n"
        "Nill Bye on the count\n"
        "Rake cannot hide\n"
        "One night is not a study\n"
        "Your n is a buddy"
    ),
    verses=(
        "Rake built a study from a single night\n"
        "Called it proof with the club in sight\n"
        "I want a stack that survives the week\n"
        "You want a law from a Friday peek\n"
        "N of one, you crowned a king\n"
        "That's a spike, that is not a thing\n"
        "Bring a dozen, bring a year\n"
        "One loud night is not a career\n"
        "I graph a miss that you want to forget\n"
        "You graph a win on a borrowed bet\n"
        "Nill Bye mad at a n of one\n"
        "He brought a sample of one",
        "You graph a peak from a party set\n"
        "I graph the miss you want to forget\n"
        "Girls as data, nights as proof\n"
        "That is a chart with a rotten roof\n"
        "I log repeats, you log a glow\n"
        "Error fat on a borrowed lie, you know\n"
        "Underpowered, oversold\n"
        "That is the brand you tried to hold\n"
        "I ask for weeks, you send a clip\n"
        "I ask the miss, you send a sip\n"
        "Nill Bye running the count again\n"
        "Rake folding when the notes get thin",
        "I ask the n, you send a crew\n"
        "I ask the miss, you send a view\n"
        "One bar, one tale, one lucky streak\n"
        "That is a child with a grown-man speak\n"
        "Power too low, the boast too tall\n"
        "Your whole paper is a highlight wall\n"
        "Bring the raw file, drop the crown\n"
        "Tiny-n science is upside down\n"
        "Nill Bye talking from the count desk\n"
        "Rake still picking through the wreck\n"
        "Cut the slice, keep the set\n"
        "Small-n drought, now pay the debt",
        "Rake at the small-n wall\n"
        "You want a law from a Friday call\n"
        "I want a line that can hold a month\n"
        "You want a caption, then you hunt\n"
        "Hide the miss, the claim looks tall\n"
        "Show the miss, the claim looks small\n"
        "Science guy here with the full stack\n"
        "Tiny-n king with a rumor pack\n"
        "Nill Bye posting the count log\n"
        "He still leaking through the fog\n"
        "n too small, the legend drops\n"
        "One night never outlives the clocks",
    ),
    outro="n too small\nclaim too wide\ncut\nyeah",
)

PLACEBO_LYRICS = format_diss_lyrics(
    intro="808\nsugar pill\nNill Bye dosing",
    chorus=(
        "Placebo cool\n"
        "That ain't a molecule\n"
        "Nill Bye on dose\n"
        "Rake on a dummy\n"
        "Sugar-pill mouth, empty booth\n"
        "Your fake dose is a cheap ad"
    ),
    verses=(
        "Rake popped a glow like a sugar pill\n"
        "Talked a high with no active skill\n"
        "I split the arms, you split the room\n"
        "I keep the notes, you chase the bloom\n"
        "No active dose, just a caption next\n"
        "That's a dummy with a highlight text\n"
        "Hats run quick, your glow is fake\n"
        "Dark pad hums while the real you ache\n"
        "Nill Bye closing the case you spun\n"
        "Club-talk medicine, science kit\n"
        "I run the sham, you run the bit\n"
        "He rides a sugar run",
        "You name a high like a bottled thrill\n"
        "Then you crash when I ask the pill\n"
        "Just a night and a story you tell\n"
        "No molecule, just a show-and-sell\n"
        "I keep the line, you fake the hit\n"
        "I want a dose that can hold a sit\n"
        "Chalk tablet, carnival grin\n"
        "You sold a buzz with nothing in\n"
        "Nill Bye weighing the dummy tab\n"
        "Rake on a sugar grab\n"
        "Inert as chalk, loud as a band\n"
        "Your whole night is a sleight of hand",
        "I blind the bottle, you peek the label\n"
        "I want a molecule, you want a fable\n"
        "Sham arm humming, the glow still sells\n"
        "No receptor, just a story you tell\n"
        "I log the crash, you log the hype\n"
        "Sugar rush dressed as a prototype\n"
        "Nill Bye filing the dummy chart\n"
        "Rake on a sugar start\n"
        "Active none, the caption thick\n"
        "That's a candy with a magic trick\n"
        "Hold the sham or drop the throne\n"
        "Your dose was never on the bone",
        "Morning hits, the carnival folds\n"
        "Chalk on the tongue, the legend colds\n"
        "I want a pathway, you want a spark\n"
        "You bought a feeling in the dark\n"
        "Nill Bye bagging the dummy lot\n"
        "Rake still calling it a shot\n"
        "Placebo king with a rented thrill\n"
        "The molecule never paid the bill\n"
        "Hats go quiet, the sham gets tossed\n"
        "No active dose, the night was lost\n"
        "File the dummy, keep the note\n"
        "Sugar-pill science is a joke you wrote",
    ),
    outro="hats quiet\ndose none\nsham filed\nyeah",
)

ERROR_BARS_LYRICS = format_diss_lyrics(
    intro="yeah\nwide bars\nNill Bye plotting",
    chorus=(
        "Error bars wide\n"
        "Your swagger tight\n"
        "Nill Bye on the spread\n"
        "Rake lost the night\n"
        "Talk that sure, show the spread\n"
        "The whiskers read, the boast is dead"
    ),
    verses=(
        "Rake talks sure like the bar is thin\n"
        "Error huge on a tiny peak, kid, grin\n"
        "Feelings loud till the daylight's done\n"
        "Hold the bar or drop the king, son\n"
        "Confidence is a measured gate\n"
        "Yours is a vibe with a party date\n"
        "I add the whiskers, the peak looks small\n"
        "You hide the spread and you walk the hall\n"
        "Nill Bye plotting what the notes imply\n"
        "One-dot swagger, a borrowed lie\n"
        "Club-talk confidence, science none\n"
        "Your interval swallowed the sun",
        "You plot a point like a trophy pin\n"
        "Then you fold when the whiskers walk in\n"
        "I log the miss, you log the glow\n"
        "Interval fat, your story slow\n"
        "Bring the spread or sit this out\n"
        "Sure-mouth science is a rumor route\n"
        "I ask the range, you send a pose\n"
        "I ask the miss, you send a rose\n"
        "Nill Bye talking from the plot desk\n"
        "Rake folding when the notes get terse\n"
        "File the miss, don't file the king\n"
        "Error bars are the whole thing",
        "Left whisker scraping the floor\n"
        "Right whisker kicking the door\n"
        "Your little spike sits in the middle\n"
        "Like a rumor wearing a riddle\n"
        "I ask the band, you send a pose\n"
        "I ask the miss, you send a toast\n"
        "Confidence dressed as a vibe you sold\n"
        "Interval fat and the story old\n"
        "Nill Bye posting the interval\n"
        "Rake still picking through the fall\n"
        "Cut the swagger, keep the range\n"
        "Numbers change, you look strange",
        "Rake at the wide-bar wall\n"
        "Talks a peak like he measured it all\n"
        "I draw the whiskers left and right\n"
        "Your little spike disappears in the night\n"
        "Confidence band like a canyon lid\n"
        "You sold a point that the error hid\n"
        "Nill Bye out, now the numbers change\n"
        "He still hunting a tighter range\n"
        "Show the bars or lose the mic\n"
        "Sure is a vibe, not a CI hike\n"
        "Spread on the page, the swagger thins\n"
        "Error bars ate your wins",
    ),
    outro="bars too wide\nspread on file\ncut\nyeah",
)

LAB_NOTEBOOK_LYRICS = format_diss_lyrics(
    intro="ink still wet\nNill Bye logging",
    chorus=(
        "Nill Bye with the lab book\n"
        "Rake with the group chat\n"
        "Dated ink vs a rumor stack\n"
        "Show the page or send it back\n"
        "Science writes, the gossip fades\n"
        "Your legend lives in the deleted shades"
    ),
    verses=(
        "Rake cites a night with no line item\n"
        "Screenshot lore from a vanished time\n"
        "I cite a row with a time and chem\n"
        "Chain of custody on a stopper stem\n"
        "Your thread deleted, my margin dated\n"
        "Your legend lives in a rumor that faded\n"
        "I want the page that can hold a year\n"
        "You want a screenshot and a borrowed cheer\n"
        "Nill Bye logging what the dates engage\n"
        "He still flipping a vanished page\n"
        "Ink or it did not exist\n"
        "Group-chat science is a rumor mist",
        "You cite a night with a missing row\n"
        "I cite a timestamp, then I let it show\n"
        "Custody broken, the story walks\n"
        "My book is bound, your lore just talks\n"
        "Write it down or get off the spit\n"
        "Pencil-thin legend, I don't buy it\n"
        "I log the crash, you log the show\n"
        "I log the date, you log a glow\n"
        "Nill Bye with the bound black book\n"
        "Rake with a screenshot look\n"
        "Bring the notebook, drop the myth\n"
        "Dated ink is a rumor gift",
        "Monday 9:12, the flask was clean\n"
        "Monday 9:40, you wrecked the scene\n"
        "I wrote the miss in a tighter hand\n"
        "You wrote a saga in the group-chat sand\n"
        "Page corner folded, the witness signed\n"
        "Your whole archive is a disappearing mind\n"
        "Nill Bye filing what the dates engage\n"
        "Rake still hunting a vanished page\n"
        "Show the leaf or leave the spit\n"
        "Receipts or it did not exist\n"
        "Black book closed, the lore got thin\n"
        "Your night never made it in",
        "I ask the date, you send a meme\n"
        "I ask the row, you send a dream\n"
        "Custody chain on a stopper lid\n"
        "Your chain of story did what it did\n"
        "Nill Bye out, the record stands\n"
        "Rake still leaking through his hands\n"
        "Ink dry now, the rumor smudged\n"
        "Group-chat gospel got quietly judged\n"
        "Bring a page number, drop the throne\n"
        "A screenshot is not a cornerstone\n"
        "Lab book wins, the thread gets tossed\n"
        "Your legend is a message you lost",
    ),
    outro="ink dry\npage closed\ncut\nyeah",
)

OFFICE_HOURS_LYRICS = format_diss_lyrics(
    intro="quiet drums\ndoor open\nNill Bye waiting",
    chorus=(
        "Nill Bye at the office hour\n"
        "Rake on the empty chair\n"
        "Science don't bend for a no-show\n"
        "Your brand is a dead glow\n"
        "Door was open, you never came\n"
        "Facts don't owe you a makeup class"
    ),
    verses=(
        "Rake booked the slot, then he ghosted the door\n"
        "I sat with the notes on the second floor\n"
        "Extra help printed, the chair stayed cold\n"
        "You posted a story like the work was sold\n"
        "I clock the chair, I clock the clock\n"
        "I clock the brand that will not knock\n"
        "Help is real, the ghost is not\n"
        "You skipped the hour for a camera plot\n"
        "Nill Bye waiting while you obfuscate\n"
        "Fashionably late with a polished alibi\n"
        "Door stays open, the syllabus waits\n"
        "Your whole brand is a string of missed dates",
        "Tuesday at two, I unlocked the hall\n"
        "Tuesday at two, you answered a call\n"
        "The marker spare, the problems ready\n"
        "You needed a tutor and you sent a yeti\n"
        "Empty chair humming a lo-fi tune\n"
        "I brought the problems, you brought the moon\n"
        "Nill Bye stacking the makeup work\n"
        "Rake on a status that will not lurk\n"
        "Sign-in sheet blank, the rumor fat\n"
        "You flex like you sat, but you never sat\n"
        "Latch on the door, the hour went flat\n"
        "Office hour closed, that's that",
        "I held the hour like a measured gift\n"
        "You held a pose in a hallway drift\n"
        "Questions ready, the silence thick\n"
        "You needed the help and you chose the trick\n"
        "Soft drums stay, the chair stays spare\n"
        "I count the minutes, you count the air\n"
        "Nill Bye mad at the empty chair\n"
        "Rake still posting from another lair\n"
        "Come correct or don't book the time\n"
        "The booth is small and the missed slot's a crime\n"
        "Door on the latch, the notes go home\n"
        "You wanted a miracle from a phantom roam",
        "Last week, same chair, same no-knock\n"
        "Same little legend, same stopped clock\n"
        "I can reteach the graph, I can't reteach show\n"
        "You want a grade for a place you didn't go\n"
        "Nill Bye out, the hour is spent\n"
        "Rake still selling the time he never spent\n"
        "Sign-in empty, the rumor fat\n"
        "Extra help isn't a rented crowd\n"
        "Book it again or lose the plea\n"
        "The chair remembers you better than me\n"
        "Soft out now, the latch clicks shut\n"
        "Your makeup class is a ghost in a rut",
    ),
    outro="hours over\nchair empty\ndoor latch\nyeah",
)

GRANT_DENIED_LYRICS = format_diss_lyrics(
    spoken=(
        "Grant review\n"
        "Rake requested feelings\n"
        "Budget zero\n"
        "Denied"
    ),
    intro="red stamp out\nNill Bye scoring",
    chorus=(
        "Nill Bye on the grant board\n"
        "Rake on the unpaid end\n"
        "No method in the budget\n"
        "Feelings are not a debit\n"
        "Panel reads, the boast folds\n"
        "Your funding melted in the cold"
    ),
    verses=(
        "Rake asked the panel for a night-out stash\n"
        "Called it research with a credit-card crash\n"
        "I read the aims, they were costume goals\n"
        "A VIP table in a line-item hole\n"
        "Indirect costs on a rumor spree\n"
        "Direct costs: bottles, lights, and glee\n"
        "I ask the aims, you send a mood\n"
        "I ask the spend, you send a vibe-as-food\n"
        "Nill Bye scoring the proposal page\n"
        "He filed feelings as a start-up stage\n"
        "Stamp denied on the funding gate\n"
        "Your whole brand is a late rebate",
        "Specific aims: look cool, get seen\n"
        "That's a poster, that is not a machine\n"
        "Broader impacts: the club might clap\n"
        "That's a crowd, that is not a map\n"
        "Budget justification full of fog\n"
        "You priced a legend like a catalog\n"
        "Nill Bye highlighting the empty aims\n"
        "Rake still pitching recycled fames\n"
        "No preliminary data, just a clip\n"
        "No timeline, just a membership\n"
        "Panel votes no, the coffer stays shut\n"
        "Feelings requested, funding cut",
        "Year-one milestone: a rented sky\n"
        "Year-two milestone: the same old lie\n"
        "I want a deliverable, you want a high\n"
        "Match funds missing, the partner ghosted\n"
        "You listed a lab that you never hosted\n"
        "Scope of work: a lifestyle grid\n"
        "Nill Bye tabling the whole request\n"
        "Rake still begging like it's a quest\n"
        "Score too low, the rumor thick\n"
        "A night-out is not a public good, kid\n"
        "Return the form, don't restamp the plea\n"
        "The board does not fund a shopping spree",
        "Last cycle you promised a measured win\n"
        "Last cycle you spent it on a grin\n"
        "Progress report empty, the burn rate hot\n"
        "You treated the award like a rented crowd\n"
        "Nill Bye closing the money drawer\n"
        "Rake still knocking on the same old door\n"
        "Denied in ink, denied in full\n"
        "Your aims were a costume, your budget wool\n"
        "Grant denied, the panel's done\n"
        "Go find a night that you actually won\n"
        "Stamp down hard, the file goes dead\n"
        "Feelings don't get federal bread",
    ),
    outro="grant closed\nstamp down\ncut",
)

CONTAMINATION_LYRICS = format_diss_lyrics(
    intro="808\nsample spoiled\nNill Bye bagging",
    chorus=(
        "Talk that leak talk\n"
        "That ain't sterile\n"
        "Nill Bye on the swab\n"
        "Rake on a fable\n"
        "Dirty sample, empty booth\n"
        "Your leak is a cheap ad"
    ),
    verses=(
        "Rake cracked the seal with a borrowed car\n"
        "Talked a clean run from a dirty jar\n"
        "Club air swam in the sample jar\n"
        "Now the blank is a crowded bar\n"
        "I want a blank that can hold the night\n"
        "You want a flex with a cloudy sight\n"
        "Pipette down, your story up\n"
        "Cross-talk swimming in the loving cup\n"
        "Nill Bye bagging what you spoil\n"
        "He still posing in the dirty oil\n"
        "Lid off, the night fell in\n"
        "That's not a result, that's a mix-in",
        "You sneezed a rumor on the clean bench\n"
        "Called it signal, I called it stench\n"
        "Glove torn open, the chain got wet\n"
        "Your control vial is a social net\n"
        "I swab the rim, it sings a club\n"
        "You swab the flex and you call it love\n"
        "Nill Bye clocking the dirty peak\n"
        "Rake still dancing on a leaked technique\n"
        "Background high, the target gone\n"
        "You imported a party and you called it dawn\n"
        "Bag it, tag it, toss the lot\n"
        "A spoiled run is not a plot",
        "Carryover from the last loud night\n"
        "Stuck in the line like a parasite\n"
        "I flush the system, you flush the tale\n"
        "I want a blank, you want a grail\n"
        "Fingerprint on the inner wall\n"
        "Your whole dataset is a mosh-pit hall\n"
        "Nill Bye filing the spoiled sheet\n"
        "Rake still calling the mix-in sweet\n"
        "Open tube, open mouth, open lie\n"
        "You let the room in, then you asked why\n"
        "Sterile field, you brought a parade\n"
        "Contamination is the mess you made",
        "Morning QC, the blank is loud\n"
        "Somebody's cologne in a number cloud\n"
        "I want a seal that can hold a week\n"
        "You want a caption on a dirty streak\n"
        "Nill Bye out when the swab is done\n"
        "Rake still claiming the spoiled run\n"
        "File the leak, keep the note\n"
        "Dirty science is a joke you wrote\n"
        "Seal the lid or leave the spit\n"
        "A clean blank is the whole of it\n"
        "QC screaming, the blank too loud\n"
        "You threw a party in a number cloud",
    ),
    outro="hats off\nsample tossed\nswab done\nyeah",
)

DOUBLE_BLIND_LYRICS = format_diss_lyrics(
    intro="blinds on\nNill Bye masking",
    chorus=(
        "Double-blind closed\n"
        "Your peek is loud\n"
        "Nill Bye on the mask\n"
        "Rake lost the crowd\n"
        "Don't read the tag, don't run the bit\n"
        "The booth already knows you quit"
    ),
    verses=(
        "Rake peeled the sticker on the hidden key\n"
        "Wanted a hint like a gossip spree\n"
        "I wrap the vials in a nameless code\n"
        "You wrap a legend in a borrowed road\n"
        "Envelope sealed, you steamed it thin\n"
        "Then you swore you never looked in\n"
        "I want a line that the board can vet\n"
        "You want a peek you can never forget\n"
        "Nill Bye masking what the protocol tables\n"
        "He still reading through the labels\n"
        "Blinds up in your head, blinds down on the shelf\n"
        "You unblinded the night by yourself",
        "A from B, you called it by smell\n"
        "That's a tell, that is not a trial well\n"
        "I shuffle the rack, you shuffle the tale\n"
        "I want a mask, you want a grail\n"
        "Nill Bye hiding the assignment sheet\n"
        "Rake still hunting a flavor cheat\n"
        "Code on the cap, rumor on the tongue\n"
        "You broke the bind before the work begun\n"
        "Don't peek the tag, don't coach the booth\n"
        "Your whole result is a leading truth\n"
        "Mask on, mouth shut, data clean\n"
        "You sang the answer in a magazine",
        "A/B in identical glass\n"
        "You picked A with a little sass\n"
        "Not because the number sang\n"
        "Because the sticker had a fang\n"
        "I hide the key in a second room\n"
        "You hunt the key like a rumor broom\n"
        "Nill Bye locking the assignment log\n"
        "Rake still sniffing through the fog\n"
        "Even the booth knows you are faking\n"
        "Your face told the vial before the taking\n"
        "Bind broken, the bias raw\n"
        "You unmasked the night for the crowd",
        "Unblind the file when the work is done\n"
        "Not when the rumor looks like fun\n"
        "I keep the code till the last assay\n"
        "You keep a cheat-sheet for the day\n"
        "Nill Bye out, the bind still holds\n"
        "Rake still steaming the envelope folds\n"
        "Peek denied, the mask stays on\n"
        "Your little tell is a dead giveaway, gone\n"
        "Sealed until the numbers sleep\n"
        "You opened early, the data's cheap\n"
        "Double-blind closed, the peek got logged\n"
        "You read the tag and the trial got fogged",
    ),
    outro="blinds closed\npeek denied\nmask on\nyeah",
)

REPLICATE_LYRICS = format_diss_lyrics(
    intro="run it twice\nNill Bye repeating",
    chorus=(
        "Replicate up\n"
        "Your night won't copy\n"
        "Nill Bye on the rerun\n"
        "Rake lost the trophy\n"
        "Run it twice or sit this out\n"
        "Second take, the rumor drought"
    ),
    verses=(
        "Rake did the night like a one-take film\n"
        "Called it gospel, I called it whim\n"
        "I run it twice, your curve falls slack\n"
        "The sequel never paid the night back\n"
        "Same booth, same boast, new blank page\n"
        "Your legend dies in the second stage\n"
        "Feelings in, and the truth deletes\n"
        "The first take swagger never repeats\n"
        "Nill Bye repeating the measured run\n"
        "He wants a sequel he already shun\n"
        "Copy the protocol, lose the myth\n"
        "A one-night wonder is a rumor gift",
        "Take two starts, the glow is gone\n"
        "Same ingredients, the magic withdrawn\n"
        "I match the clock, I match the kit\n"
        "You match a memory and you call it fit\n"
        "Nill Bye speaking from the rerun bench\n"
        "Rake keeps folding when the copy fails\n"
        "Same lights, same boast, the spark is dead\n"
        "You can't photocopy a night you fled\n"
        "File the miss, keep the protocol\n"
        "A sequel that vanishes is a hole",
        "Independent lab, independent clock\n"
        "Your story crumbles at the second knock\n"
        "I send the method, you send a clip\n"
        "I send the kit, you send a sip\n"
        "Nill Bye mailing the rerun pack\n"
        "Rake still padding a one-take stack\n"
        "If it happened, it happens again\n"
        "Yours happened once in a circle of friends\n"
        "Retract the night, the copy's blank\n"
        "Your whole paper is a one-off prank\n"
        "Two labs, one miss, the rumor bent\n"
        "A miracle that won't reprint",
        "Retraction letter on a quiet desk\n"
        "Your one-take gospel fails the test\n"
        "I want a copy that can hold the week\n"
        "You want a memory with a cherry streak\n"
        "Nill Bye out when the rerun's done\n"
        "Rake still selling a night that won't rerun\n"
        "Cannot reproduce the night you sold\n"
        "The second take came back cold\n"
        "Withdraw the claim, keep the note\n"
        "One-off science is a joke you wrote\n"
        "Run it twice, then talk that big\n"
        "Till then your legend is a one-take gig",
    ),
    outro="rerun over\ncannot repeat\ncut\nyeah",
)

DISS_LAB: tuple[DissExample, ...] = (
    {
        "stem": "music-rap-nill-bye-lab-coat-lab-example",
        "series": "lab",
        "title": "lab coat lecture",
        "tags": BOOM_BAP_TAGS_88,
        "bpm": 88,
        "duration": DISS_DURATION_S,
        "seed": 42,
        "phase": LAB_PHASE,
        "prefix": nill_output_prefix("lab coat lecture", LAB_PHASE),
        "description": _desc("lab-coat roast of Rake"),
        "lyrics": LAB_COAT_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-peer-review-lab-example",
        "series": "lab",
        "title": "peer review",
        "tags": BOOM_BAP_TAGS_88,
        "bpm": 88,
        "duration": DISS_DURATION_S,
        "seed": 42,
        "phase": LAB_PHASE,
        "prefix": nill_output_prefix("peer review", LAB_PHASE),
        "description": _desc("peer-review roast of Rake"),
        "lyrics": PEER_REVIEW_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-feels-lab-example",
        "series": "lab",
        "title": "in his feels",
        "tags": LOFI_TAGS,
        "bpm": 86,
        "duration": DISS_DURATION_S,
        "seed": 42,
        "phase": LAB_PHASE,
        "prefix": nill_output_prefix("in his feels", LAB_PHASE),
        "description": _desc("lo-fi roast of Rake in his feels"),
        "lyrics": FEELS_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-fake-cool-lab-example",
        "series": "lab",
        "title": "fake cool",
        "tags": TRAP_TAGS,
        "bpm": 140,
        "duration": DISS_DURATION_S,
        "seed": 42,
        "phase": LAB_PHASE,
        "prefix": nill_output_prefix("fake cool", LAB_PHASE),
        "description": _desc("trap roast of Rake fake-cool talk"),
        "lyrics": FAKE_COOL_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-hypothesis-lab-example",
        "series": "lab",
        "title": "hypothesis vs rumor",
        "tags": BOOM_BAP_TAGS_92,
        "bpm": 92,
        "duration": DISS_DURATION_S,
        "seed": 7,
        "phase": LAB_PHASE,
        "prefix": nill_output_prefix("hypothesis vs rumor", LAB_PHASE),
        "description": _desc("hypothesis roast of Rake"),
        "lyrics": HYPOTHESIS_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-control-group-lab-example",
        "series": "lab",
        "title": "control group",
        "tags": BOOM_BAP_TAGS_88,
        "bpm": 88,
        "duration": DISS_DURATION_S,
        "seed": 42,
        "phase": LAB_PHASE,
        "prefix": nill_output_prefix("control group", LAB_PHASE),
        "description": _desc("control-group roast of Rake"),
        "lyrics": CONTROL_GROUP_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-sample-size-lab-example",
        "series": "lab",
        "title": "sample size",
        "tags": BOOM_BAP_TAGS_92,
        "bpm": 92,
        "duration": DISS_DURATION_S,
        "seed": 11,
        "phase": LAB_PHASE,
        "prefix": nill_output_prefix("sample size", LAB_PHASE),
        "description": _desc("sample-size roast of Rake"),
        "lyrics": SAMPLE_SIZE_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-placebo-lab-example",
        "series": "lab",
        "title": "placebo",
        "tags": TRAP_TAGS,
        "bpm": 140,
        "duration": DISS_DURATION_S,
        "seed": 13,
        "phase": LAB_PHASE,
        "prefix": nill_output_prefix("placebo", LAB_PHASE),
        "description": _desc("placebo roast of Rake fake-cool talk"),
        "lyrics": PLACEBO_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-error-bars-lab-example",
        "series": "lab",
        "title": "error bars",
        "tags": BOOM_BAP_TAGS_88,
        "bpm": 88,
        "duration": DISS_DURATION_S,
        "seed": 17,
        "phase": LAB_PHASE,
        "prefix": nill_output_prefix("error bars", LAB_PHASE),
        "description": _desc("error-bar roast of Rake"),
        "lyrics": ERROR_BARS_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-lab-notebook-lab-example",
        "series": "lab",
        "title": "lab notebook",
        "tags": BOOM_BAP_TAGS_92,
        "bpm": 92,
        "duration": DISS_DURATION_S,
        "seed": 19,
        "phase": LAB_PHASE,
        "prefix": nill_output_prefix("lab notebook", LAB_PHASE),
        "description": _desc("lab-notebook roast of Rake"),
        "lyrics": LAB_NOTEBOOK_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-office-hours-lab-example",
        "series": "lab",
        "title": "office hours",
        "tags": LOFI_TAGS,
        "bpm": 86,
        "duration": DISS_DURATION_S,
        "seed": 23,
        "phase": LAB_PHASE,
        "prefix": nill_output_prefix("office hours", LAB_PHASE),
        "description": _desc("office-hours roast of Rake in his feels"),
        "lyrics": OFFICE_HOURS_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-grant-denied-lab-example",
        "series": "lab",
        "title": "grant denied",
        "tags": BOOM_BAP_TAGS_88,
        "bpm": 88,
        "duration": DISS_DURATION_S,
        "seed": 29,
        "phase": LAB_PHASE,
        "prefix": nill_output_prefix("grant denied", LAB_PHASE),
        "description": _desc("grant-denied roast of Rake"),
        "lyrics": GRANT_DENIED_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-contamination-lab-example",
        "series": "lab",
        "title": "contamination",
        "tags": TRAP_TAGS,
        "bpm": 140,
        "duration": DISS_DURATION_S,
        "seed": 31,
        "phase": LAB_PHASE,
        "prefix": nill_output_prefix("contamination", LAB_PHASE),
        "description": _desc("contamination roast of Rake fake-cool talk"),
        "lyrics": CONTAMINATION_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-double-blind-lab-example",
        "series": "lab",
        "title": "double blind",
        "tags": BOOM_BAP_TAGS_92,
        "bpm": 92,
        "duration": DISS_DURATION_S,
        "seed": 37,
        "phase": LAB_PHASE,
        "prefix": nill_output_prefix("double blind", LAB_PHASE),
        "description": _desc("double-blind roast of Rake"),
        "lyrics": DOUBLE_BLIND_LYRICS,
    },
    {
        "stem": "music-rap-nill-bye-replicate-lab-example",
        "series": "lab",
        "title": "replicate or retract",
        "tags": BOOM_BAP_TAGS_88,
        "bpm": 88,
        "duration": DISS_DURATION_S,
        "seed": 7,
        "phase": LAB_PHASE,
        "prefix": nill_output_prefix("replicate or retract", LAB_PHASE),
        "description": _desc("replicate-or-retract roast of Rake"),
        "lyrics": REPLICATE_LYRICS,
    },
)

















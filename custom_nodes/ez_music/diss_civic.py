"""Civic-pack 180s Nill Bye diss takes (non-trap, non-EDM beds).

Fictional MC Nill Bye roasting public-record satire of Texas Gov. Greg Abbott.
Original lyrics. No living-MC names. No disability punchlines. No autotune.
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

CIVIC_PHASE = 3


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
        "series": "civic",
        "title": title,
        "tags": nill_tags(*tag_parts, bpm=bpm),
        "bpm": bpm,
        "duration": DISS_DURATION_S,
        "seed": seed,
        "phase": CIVIC_PHASE,
        "prefix": nill_output_prefix(title, CIVIC_PHASE),
        "description": _desc(take),
        "lyrics": lyrics,
    }


FROZEN_ERCOT_LYRICS = format_diss_lyrics(
    intro="yeah\ngrid down\nNill Bye grid-gauging",
    chorus=(
        "Frozen ERCOT\n"
        "Nill Bye on the blackout\n"
        "Abbott blamed the windmill\n"
        "Gas froze in the wellhead\n"
        "Two-four-six on the docket\n"
        "Your grid failed the weather"
    ),
    verses=(
        "February iced the whole ERCOT\n"
        "Four million in the darkroom\n"
        "Two hundred seventy-seven ticks\n"
        "From a statewide collapse-risk\n"
        "FERC counted frozen gas\n"
        "Fifty-eight percent of the trips-off\n"
        "Wind took twenty-seven shares\n"
        "You ran to Fox with a scapegoat-clip\n"
        "Abbott said the solar quit-shift\n"
        "Permian wells fell eighty-five points\n"
        "Nill Bye gauging the outage-sheet\n"
        "Your weatherize was optional talk",
        "Uri wrote a hypothermia list\n"
        "Harris County topped the counties\n"
        "Carbon monoxide in the garages\n"
        "Boil-water for fourteen million taps\n"
        "PUC pinned nine thousand a megawatt\n"
        "Griddy bills hit the five-figure mark\n"
        "Abbott claimed the grid got a full fix\n"
        "The exception form still lets plants duck\n"
        "Nill Bye tracing the frequency sag\n"
        "You sold a windmill as the culprit\n"
        "Thermal plants iced at the intake\n"
        "Your presser was a blame-shift",
        "Ten years of freeze memos unread\n"
        "Two-thousand-eleven already warned you\n"
        "Mandatory winterize never landed\n"
        "Until the body-count made the headline\n"
        "Abbott signed a weatherize bill late\n"
        "Then a loophole for the slow shops\n"
        "Nill Bye filing the FERC mix\n"
        "Gas carried the outage, not the turbine\n"
        "Isolated grid to dodge the feds\n"
        "Then you begged when the hertz fell\n"
        "Four days dark and the pumps died\n"
        "Your miracle state took a cold quiz",
        "Twenty-twenty-six you called it flawless\n"
        "Radio grin on a five-year boast-tour\n"
        "Nill Bye keeping the death ledger\n"
        "Two-four-six is not a vibe\n"
        "Abbott still ducking the gas chart\n"
        "Windmills make a prettier villain\n"
        "The isolated grid still sits alone\n"
        "No neighbor to borrow a watt from\n"
        "You weatherized the talking points\n"
        "Not the wells, not the flanges\n"
        "I run the numbers, you run Fox\n"
        "Frozen ERCOT is the whole thesis",
    ),
    outro="hertz up\nwells thaw\ncut\nyeah",
)

ABJECT_FAILURE_LYRICS = format_diss_lyrics(
    spoken=(
        "Robb Elementary\n"
        "Nineteen children\n"
        "Two teachers\n"
        "Seventy-seven minutes\n"
        "Abject failure"
    ),
    intro="hallway quiet\nNill Bye stopwatching",
    chorus=(
        "Abject failure\n"
        "Nill Bye stamps the hallway\n"
        "Abbott split the message\n"
        "Tape for the gun show\n"
        "Kids still in the classroom\n"
        "Your courage took a video"
    ),
    verses=(
        "May twenty-four, Robb went silent\n"
        "Nineteen kids and two teachers gone\n"
        "Seventy-seven minutes in the corridor\n"
        "Cops waited while the shots kept time\n"
        "McCraw called it an abject failure\n"
        "That is DPS, not a blog\n"
        "Abbott flew a tape to Houston\n"
        "NRA stage, three days later\n"
        "Nill Bye stopwatching the two-track speech\n"
        "Uvalde heard all options open\n"
        "The convention heard statutes don't matter\n"
        "You cannot be in both rooms honest",
        "HB nineteen-twenty-seven already inked\n"
        "No-license carry, September twenty-one\n"
        "Then an eighteen-year-old bought the rifles\n"
        "Legal as the bill you cheered\n"
        "Abbott said thousands of laws failed\n"
        "So you refused to write a new one\n"
        "Nill Bye reading the special-session menu\n"
        "School doors, not the magazine\n"
        "Cornyn ducked, Patrick ducked\n"
        "You sent a clip and kept the donors\n"
        "Robb is a method, not a moment\n"
        "Your reform was a presser loop",
        "They waited in a classroom dark-wait\n"
        "Parents begged at the fence\n"
        "A hallway full of badges froze\n"
        "Command couldn't pick a breach\n"
        "Abbott said he had been misled\n"
        "Then he misled the gun-show tape\n"
        "Nill Bye holding the two transcripts\n"
        "Same hour, opposite morals\n"
        "Capital murder already on the books\n"
        "That did not reload the minute\n"
        "You grieved in Uvalde on camera\n"
        "And greenlit Houston on a hard drive",
        "No assault-ban in the after-bills\n"
        "Hardening the door, not the gun-code\n"
        "Nill Bye mad at a split-screen gov\n"
        "Abbott still selling the law-count\n"
        "Nineteen names you will not say here\n"
        "Two teachers, a town, a delay\n"
        "McCraw's phrase is the whole finding\n"
        "Abject failure, stamped in public\n"
        "You chose the convention over the fix\n"
        "A video is not a spine\n"
        "I clock the minutes, you clock the PACs\n"
        "The hallway did the math for you",
    ),
    outro="tape off\nhallway stays\ncut",
)

SIX_WEEK_CLOCK_LYRICS = format_diss_lyrics(
    intro="metronome\ncardiac tick\nNill Bye ticking",
    chorus=(
        "Six week clock\n"
        "Nill Bye times the bounty\n"
        "Abbott signed the heartbeat\n"
        "Private suit, public scare\n"
        "Doctors freeze, mothers travel\n"
        "Your exception was a fog-bank"
    ),
    verses=(
        "SB eight, May twenty-twenty-one\n"
        "Heartbeat Act with a bounty clause\n"
        "Any stranger can file the suit\n"
        "Vigilantes with a civil docket-fee\n"
        "Abbott signed a six week clock\n"
        "Cardiac tick as a tripwire\n"
        "Nill Bye pacing the clinic math\n"
        "Most people don't know yet\n"
        "Johns Hopkins counted extra births\n"
        "Ten thousand that could not leave\n"
        "Infant deaths ticked with anomalies\n"
        "Your heartbeat bill wrote a body-tax",
        "HB twelve-eighty pulled the trigger-ban\n"
        "August twenty-five, twenty-twenty-two\n"
        "Felony for the doctor, life on the table\n"
        "Hundred-thousand civil on the side\n"
        "Abbott called it a major trophy\n"
        "Patients called it a delay-trap\n"
        "Nill Bye reading Zurawski\n"
        "Supreme Court left the chill intact\n"
        "Dallas mother, trisomy eighteen\n"
        "District said go, high court said no\n"
        "She left Texas to stay alive\n"
        "Your exception failed the emergency",
        "ProPublica counted the sepsis spike\n"
        "Fifty percent after the six week clock\n"
        "Maternal hospital deaths jumped hard\n"
        "Nation down, Texas up a third\n"
        "Abbott still selling the emergency clause\n"
        "Doctors wait until the chart is crashing\n"
        "Nill Bye noting the delayed D-and-C\n"
        "Fertility lost to a statute fog\n"
        "Mangrum tried to clear the ER\n"
        "The state appealed the oxygen\n"
        "A bounty is not a medical board\n"
        "You outsourced care to a lawsuit",
        "Life of the Mother Act came late\n"
        "After the obituaries made the case\n"
        "Nill Bye still on the six week clock\n"
        "Abbott still posing with the heartbeat\n"
        "Travel is not a health plan\n"
        "A felony is not a bedside manner\n"
        "You banned the procedure, kept the risk\n"
        "Then blamed the doctor for the pause\n"
        "I time the cardiac, you time the PACs\n"
        "SB eight is a snitch statute\n"
        "HB twelve-eighty is the cage\n"
        "Your clock runs out on the patient",
    ),
    outro="tick stop\nbounty cold\ncut\nyeah",
)

NO_BID_WIRE_LYRICS = format_diss_lyrics(
    intro="invoice hum\nNill Bye auditing",
    chorus=(
        "No-bid wire\n"
        "Nill Bye on the ledger\n"
        "Abbott stamped emergency\n"
        "Contracts skip the bidding\n"
        "Three-point-five in the dark-fund\n"
        "Your donors got the wire"
    ),
    verses=(
        "Disaster order every month since twenty-one\n"
        "A border emergency that never sunsets\n"
        "That stamp skips the bid table\n"
        "Billions move on a proclamation\n"
        "Abbott wrote a no-bid wire\n"
        "Observer caught three-point-five unbid\n"
        "Nill Bye auditing the purchase orders\n"
        "Concertina, buoys, base camps, buses\n"
        "New Yorker mapped the donor-contractors\n"
        "Campaign cash in, state checks out\n"
        "Watchdogs said a billion steered to friends\n"
        "Your emergency is a procurement trick",
        "Border spend north of eleven billion\n"
        "Still asking D.C. to reimburse the spree\n"
        "Abbott calls it Washington's failure\n"
        "Then he spends like a blank check\n"
        "Nill Bye circling the no-bid wire\n"
        "Eagle Pass base in the hundreds of millions\n"
        "Seventy thousand rolls of razor\n"
        "A wall in pieces that do not meet\n"
        "Legislature side-eyed the forever seal\n"
        "COVID taught him the proclamation habit\n"
        "Same tool, new enemy, same vendors\n"
        "Your disaster is a business model",
        "Public Citizen ran the donor overlay\n"
        "Executives giving, then getting contracts\n"
        "Abbott says the border is the mission-text\n"
        "The invoice says the brief is the invoice\n"
        "Nill Bye matching PACs to purchase-codes\n"
        "No competition, no sunlight, no shame\n"
        "A monthly stamp is a loophole with a seal\n"
        "Five years in, the emergency is the franchise\n"
        "You skipped the bid to skip the questions\n"
        "Then billed the questions as disloyalty\n"
        "I want a bid, you want a presser\n"
        "The wire is the method, not the fence",
        "Twenty-twenty-six, still stamping disaster\n"
        "Crossings down, the contracts up\n"
        "Nill Bye closing the procurement file\n"
        "Abbott still posing on the riverbank\n"
        "A buoy is a photo, a bid is a rule\n"
        "You picked the photo every cycle\n"
        "Eleven billion and a donor web\n"
        "That is not security, that is a tab\n"
        "I audit the wire, you audit the polls\n"
        "No-bid is the quiet border barrier\n"
        "It runs through Austin, not the river\n"
        "Your emergency never had a sunset",
    ),
    outro="stamp dry\ninvoice open\ncut",
)

GAVEL_THEATER_LYRICS = format_diss_lyrics(
    intro="gavel wood\nbrass hit\nNill Bye grading",
    chorus=(
        "Gavel theater\n"
        "Nill Bye on the roll-call\n"
        "Abbott watched the impeachment\n"
        "House said guilty enough\n"
        "Senate said go home Ken\n"
        "Your spine took an intermission"
    ),
    verses=(
        "Twenty-twenty-three, the House impeached Paxton\n"
        "Bribery cloud, office-as-a-favor\n"
        "Abbott did not lead the charge\n"
        "He let the chamber do the messy labor\n"
        "Nill Bye grading the gavel theater\n"
        "Senate trial, then an acquittal party\n"
        "Same man back at the docket-desk\n"
        "You needed his machine more than a standard\n"
        "Later you boosted him for the Senate lane\n"
        "The impeachment became a speed-bump\n"
        "A governor who won't police his AG\n"
        "Is a governor who likes the mess",
        "The House had the exhibits\n"
        "The Senate had the votes\n"
        "Abbott had a calendar and a smile\n"
        "Gavel theater with no second act\n"
        "Nill Bye reading the journal\n"
        "Impeach, acquit, endorse, repeat\n"
        "You call it the rule of coalition-math\n"
        "It is the rule of the coalition\n"
        "Paxton primaried his impeachers\n"
        "You primaried the voucher holdouts\n"
        "Same season, same donor weather\n"
        "Ethics is a costume in Austin",
        "Brass band for a civic circus\n"
        "Tuba on a roll-call that folded\n"
        "Abbott clapped the process, not the verdict\n"
        "Then he needed Ken on the trail\n"
        "Nill Bye mad at a rented spine\n"
        "You outsourced integrity to a chamber\n"
        "Then ignored the chamber you liked less\n"
        "House work thrown in the gallery trash\n"
        "A sitting AG on a corruption docket\n"
        "Still the man you warm the mic for\n"
        "That is not caution, that is a tell\n"
        "The gavel was a prop in your set",
        "Twenty-twenty-six you still share the ticket-ink\n"
        "Paxton in the Senate fight, you in the mansion\n"
        "Nill Bye filing the split verdict\n"
        "Abbott still allergic to a clean break\n"
        "Impeachment without consequence is theater\n"
        "Acquittal without shame is a sequel\n"
        "You kept the alliance and lost the standard\n"
        "Texas watched the whole farce\n"
        "I want a governor who can fire a scandal\n"
        "You wanted a partner who can turn out votes\n"
        "Gavel down, ethics out\n"
        "Your intermission never ended",
    ),
    outro="gavel rest\nbrass mute\ncut\nyeah",
)

PROPERTY_HYMN_LYRICS = format_diss_lyrics(
    intro="steel strings\nNill Bye appraising",
    chorus=(
        "Property hymn\n"
        "Nill Bye on the appraisal\n"
        "Abbott sings no income tax\n"
        "The homestead still gets the bill\n"
        "Fifty percent in a campaign key\n"
        "Your relief is a verse you defer"
    ),
    verses=(
        "No income tax is the state hymn\n"
        "The county sends the real invoice\n"
        "School M&O on the homestead\n"
        "Seniors drowning in the appraisal jump\n"
        "Abbott tours a fifty percent cut\n"
        "Twenty-twenty-six, Lubbock microphone\n"
        "Nill Bye appraising the old sessions\n"
        "Compression talks, then a smaller trim\n"
        "You sold a hymn, delivered a coupon\n"
        "Renters get none of the choir\n"
        "Business personal, still a maze\n"
        "Your miracle is a levy with a smile",
        "Gina's race made affordability the issue\n"
        "So you retuned the property hymn\n"
        "Abbott found religion in the tax-roll\n"
        "After years of the same complaint\n"
        "Nill Bye checking the effective rate\n"
        "Texas ranks high on the property bite\n"
        "You point at California like a shield\n"
        "While Austin ISD eats the raise\n"
        "A fifty percent pitch is a poster\n"
        "A certified roll is a kitchen table\n"
        "I want the levy cut in code\n"
        "You want it cut in a stump speech",
        "Local governments catch the blame\n"
        "You capped them, then underfunded schools\n"
        "Abbott calls it discipline\n"
        "Districts call it a squeeze play\n"
        "Nill Bye following the recapture\n"
        "Robin Hood with a campaign overlay\n"
        "The hymn never mentions the appraisal district\n"
        "Or the freeze that skips the renter\n"
        "Oil pays a severance story\n"
        "Households pay the monthly truth\n"
        "You brand the absence of income tax\n"
        "And hide the presence of the levy",
        "Twenty-twenty-six affordability tour\n"
        "Health costs, tuition, the homestead too\n"
        "Nill Bye filing the property hymn\n"
        "Abbott still conducting the choir\n"
        "A cut you can campaign is not a cut you passed\n"
        "Until the roll actually moves\n"
        "I score the levy, you score the primary\n"
        "No income tax is a bumper sticker\n"
        "The appraisal is the body of the song\n"
        "You keep remixing the chorus\n"
        "Bring a statute, drop the hymnal\n"
        "The kitchen table already knows the key",
    ),
    outro="strings mute\nlevy stays\ncut",
)

VOUCHER_RAID_LYRICS = format_diss_lyrics(
    intro="fiddle scrape\nNill Bye totaling",
    chorus=(
        "Voucher raid\n"
        "Nill Bye on the ESA\n"
        "Abbott spent the out-of-state cash\n"
        "Rural schools took the raid\n"
        "Public dollars, private pews\n"
        "Your choice was a donor errand"
    ),
    verses=(
        "Jeff Yass wired ten million in\n"
        "Pennsylvania money for a Texas raid\n"
        "Abbott spent it beating rural GOP\n"
        "Members who would not loot the district\n"
        "Nill Bye totaling the primary corpses\n"
        "Hearst said his win rate near four-fifths\n"
        "Bailes got buried in a TV flood\n"
        "Border ads on a voucher errand\n"
        "You called it school choice\n"
        "It was a loyalty test with a checkbook\n"
        "Rural districts bleed enrollment\n"
        "The ESA follows the already-private kid",
        "Who uses the account first?\n"
        "Families already in the pew school\n"
        "Abbott sold it as a rescue\n"
        "The spreadsheet sold it as a subsidy\n"
        "Nill Bye reading the invite list\n"
        "Public campuses lose the unit funding\n"
        "A raid dressed as a parent bill of rights\n"
        "Christian schools first in line for the draw\n"
        "You primary a Republican for the kids\n"
        "Then you steer the kids off the public roll\n"
        "That is not a market, that is a transfer\n"
        "The donor got the policy he bought",
        "Twenty-three you lost a House vote\n"
        "So you took the fight to the primary\n"
        "Abbott made the voucher the litmus\n"
        "Education became a purge instrument\n"
        "Nill Bye mad at a bought caucus\n"
        "Country fiddle on a Capitol errand\n"
        "Local boards gutted by a governor's PAC\n"
        "Then told they failed the children\n"
        "You cannot starve a campus and praise it\n"
        "You cannot raid it and call it choice\n"
        "ESA is a pipe from the tax roll\n"
        "To a sector that does not take every child",
        "Hinojosa ran on the public school\n"
        "You ran on the Yass receipt\n"
        "Nill Bye posting the voucher raid\n"
        "Abbott still calling it freedom\n"
        "Freedom for the campus that can select\n"
        "A bill for the kid who already left\n"
        "I want a school that must take the student\n"
        "You want a ledger that can refuse\n"
        "Ten million bought a legislature\n"
        "The classroom paid the invoice\n"
        "Keep Yass's name on the caption\n"
        "The raid should wear its funder",
    ),
    outro="fiddle rest\nESA open\ncut\nyeah",
)

UNINSURED_BLUES_LYRICS = format_diss_lyrics(
    intro="harmonica sting\nNill Bye charting",
    chorus=(
        "Uninsured blues\n"
        "Nill Bye on the coverage gap\n"
        "Abbott never expanded Medicaid\n"
        "Kids first in the unwind\n"
        "Highest uninsured in the union\n"
        "Your freedom is a hospital bill"
    ),
    verses=(
        "Texas never took the expansion\n"
        "One-point-four million left off the roll\n"
        "Abbott calls it a Washington trap\n"
        "The ER calls it uncompensated care\n"
        "Nill Bye charting the coverage gap\n"
        "Highest uninsured in the country for years\n"
        "Kids worst in the nation, twelve percent\n"
        "Houston the metro with the hollow CHIP\n"
        "Four hundred thousand eligible, not enrolled\n"
        "A form is harder than a slogan\n"
        "You refused the federal match\n"
        "Then billed the poor for the ideology",
        "Unwinding, Texas chose speed\n"
        "Two-point-five million dropped, most of any state\n"
        "Abbott's HHSC front-loaded the cuts\n"
        "Procedural disenroll, kids in the pile\n"
        "Nill Bye reading the KFF tracker\n"
        "A year in, a million-plus children off\n"
        "Federal guidance said go slow, auto-renew\n"
        "You picked the shredder\n"
        "Backlog of two hundred thousand applications\n"
        "Eligible people hunting a portal\n"
        "Rural wards close when the uninsured walk in\n"
        "Your blues are a policy instrument",
        "Pregnancy in Texas is a coverage cliff\n"
        "Highest uninsured women of reproductive age\n"
        "Abbott stacked that on the clinic chill\n"
        "A ward is not a talking point\n"
        "Nill Bye staying on the coverage gap\n"
        "A third of reproductive-age women bare\n"
        "Border counties near forty percent\n"
        "You export the risk to the county hospital\n"
        "Express-lane bills died in the hopper\n"
        "Even TPPF said the enrollment was broken\n"
        "Bipartisan House, then a quiet burial\n"
        "Your ideology eats the paperwork",
        "Twenty-twenty-six you pitched health-cost relief\n"
        "After you built the uninsured blues\n"
        "Nill Bye filing the expansion refusal\n"
        "Abbott still allergic to the match-rate\n"
        "Ninety percent federal, you said no\n"
        "Then you toured affordability like a convert\n"
        "A hospital bill is not a freedom anthem\n"
        "A closed ward is not a market trophy\n"
        "I want coverage, you want a talking point\n"
        "The blues keep the same twelve-bar\n"
        "Highest uninsured, still the trademark\n"
        "Your miracle skips the waiting-bay",
    ),
    outro="harp fade\ngap stays\ncut",
)

LOCKED_STACKS_LYRICS = format_diss_lyrics(
    intro="dusty loop\nNill Bye shelving",
    chorus=(
        "Locked stacks\n"
        "Nill Bye on the library ban\n"
        "Abbott blessed the pull-list\n"
        "Titles vanish for a hearing\n"
        "Kids lose the shelf, PACs gain a clip\n"
        "Your curriculum is a confiscation"
    ),
    verses=(
        "School boards got a raid of lists\n"
        "Books pulled on a parent form\n"
        "Abbott framed it as parental rights\n"
        "The stack got a padlock\n"
        "Nill Bye shelving what you banned\n"
        "DEI offices closed on cue\n"
        "University programs told to fold\n"
        "A culture session with a statute hammer\n"
        "Librarians treated like smugglers\n"
        "A graphic novel as contraband\n"
        "You don't have to burn it if you lock it\n"
        "The hearing is the bonfire with better lighting",
        "HB this, SB that, a pile of culture bills\n"
        "Don't Say, don't teach, don't catalog\n"
        "Abbott signed the stack closed\n"
        "Then posed with a classroom prop\n"
        "Nill Bye reading the pull-list\n"
        "History shrinks to a pamphlet\n"
        "Gender, race, a chapter too honest\n"
        "Off the shelf, onto the outrage feed\n"
        "You call it protecting childhood\n"
        "It is a loyalty ritual with a barcode\n"
        "Teachers self-censor to keep the job\n"
        "The lock is cheaper than a curriculum",
        "Lo-fi beat on a quiet ban\n"
        "Rhodes under a confiscation\n"
        "Abbott needed a session villain\n"
        "The librarian drew the short straw\n"
        "Nill Bye mad at a locked shelf-row\n"
        "Public school as a suspect package\n"
        "You audited pronouns harder than the grid\n"
        "A DEI office is not a cartel\n"
        "But it photographs worse for your base\n"
        "So the stack became the border\n"
        "Ideas in a restricted section\n"
        "Your Texas history skips the parts that sting",
        "Kids still find the text online\n"
        "You only trained them that the state is scared\n"
        "Nill Bye posting the locked stacks\n"
        "Abbott still touring the parental-rights fair\n"
        "A ban is a tell: the page might land\n"
        "So you padlock the chance it does\n"
        "I want a shelf, you want a hearing\n"
        "I want a teacher, you want a scout\n"
        "Culture war is a legislative filler\n"
        "When the levy and the ward are ugly\n"
        "Keep the lock, lose the thread\n"
        "The stack remembers who closed it",
    ),
    outro="shelf dark\nlock clicks\ncut\nyeah",
)

MASK_ORDER_LYRICS = format_diss_lyrics(
    intro="rhodes wash\nNill Bye noting",
    chorus=(
        "Mask order\n"
        "Nill Bye on GA-thirty-four\n"
        "Abbott banned the local rule\n"
        "Mayors stripped, campuses open\n"
        "A virus with a press secretary\n"
        "Your freedom was a gag on the city"
    ),
    verses=(
        "GA-thirty-four, March twenty-twenty-one\n"
        "No local mask, no local shot-rule\n"
        "Abbott opened Texas by executive pen\n"
        "Then forbade the cities from closing it back\n"
        "Nill Bye noting the preemption\n"
        "School boards told to sit down\n"
        "Businesses told they may not require\n"
        "A statewide shrug as a health plan\n"
        "You called it personal responsibility\n"
        "It was a gag on the mayor\n"
        "Hospitals filled, the order held\n"
        "Your liberty stopped at the city limit inward",
        "Local authority used to mean home rule\n"
        "You kept the emergency pen for yourself\n"
        "Abbott blocked the mask and kept the proclamation\n"
        "Power up, science down\n"
        "Nill Bye reading the GA text\n"
        "Employers muzzled on a simple screen\n"
        "Campuses told to host the unvaccinated\n"
        "As if a dorm was a theory\n"
        "You sued the locals who tried anyway\n"
        "A governor versus a superintendent\n"
        "That is not humble government\n"
        "That is a monopoly on the risk",
        "Neo-soul on a public-health veto\n"
        "Soft keys, hard preemption\n"
        "Abbott smiled through the surge curves\n"
        "Open Texas, closed debate\n"
        "Nill Bye mad at a gagged city\n"
        "You federalized nothing except the no\n"
        "The yes was reserved for your office\n"
        "Mask off as a brand, not a finding\n"
        "ICUs don't take a presser as PPE\n"
        "Teachers bought their own filters\n"
        "You bought a primary argument\n"
        "The order was a culture win with a body-count",
        "Years later the GA is the template\n"
        "Preempt first, study never\n"
        "Nill Bye filing the mask order\n"
        "Abbott still allergic to a local yes\n"
        "A city that can zone a street\n"
        "Could not ask a rider to cover a face\n"
        "That ratio is the whole tell\n"
        "You trust the market until it wears a mask\n"
        "Then you become the nanny you mock\n"
        "A nanny for the owners, not the nurses\n"
        "GA-thirty-four is a power grab\n"
        "Dressed as a freedom anthem",
    ),
    outro="rhodes out\norder holds\ncut",
)

MID_DECADE_MAP_LYRICS = format_diss_lyrics(
    intro="pixel lead\nNill Bye graphing",
    chorus=(
        "Mid decade map\n"
        "Nill Bye on the pixel\n"
        "Abbott redrew for the boss\n"
        "A census skip, a power grab\n"
        "Districts snap to a partisan grid-file\n"
        "Your geometry is a cheat code"
    ),
    verses=(
        "Mid-decade is not how the clock runs\n"
        "You don't remap because a president asks\n"
        "Abbott did it anyway in twenty-five\n"
        "A Texas cartography for a national errand\n"
        "Nill Bye graphing the pixel\n"
        "Courts circling the Voting Rights ghost\n"
        "Coalition districts cracked on purpose\n"
        "A majority squeezed into a fewer seats\n"
        "You called it reflecting the vote\n"
        "It was reflecting the request\n"
        "Multistate fight, same playbook\n"
        "The map is a weapon with a legend",
        "Chiptune beep on a gerrymander\n"
        "Eight-bit drums on a cracked precinct\n"
        "Abbott signed a mid decade map\n"
        "Before the next census could argue\n"
        "Nill Bye reading the shape files\n"
        "Earmuffs, spikes, a corridor through a city\n"
        "Voters moved on paper, not in trucks\n"
        "That's the quiet raid\n"
        "You need the House more than a principle\n"
        "So the principle became the House\n"
        "Democracy as a packing problem\n"
        "Your solution is a smaller opposition",
        "Lawsuits stacked in different circuits\n"
        "Same governor, same hurry\n"
        "Abbott says the people picked this\n"
        "The people didn't pick the lines\n"
        "Nill Bye mad at a cheat-code state\n"
        "A decade used to mean a decade\n"
        "Now it means whenever the boss texts\n"
        "Redistricting as a loyalty favor\n"
        "You wrap it in population change\n"
        "The change is the coalition you fear\n"
        "So you draw them into a corner\n"
        "And call the corner a majority-minority trophy",
        "Twenty-twenty-six ballots on a new sketch\n"
        "Candidates running through a maze you built\n"
        "Nill Bye posting the mid decade map\n"
        "Abbott still calling it fair play\n"
        "Fair is a census, not a text thread\n"
        "Fair is a decade, not a season\n"
        "I want a line that follows a river\n"
        "You want a line that follows a donor\n"
        "Pixel by pixel, the state tilts\n"
        "A geometry that cannot lose\n"
        "Keep the chiptune, lose the honesty\n"
        "Your map is the quietest coup",
    ),
    outro="pixels halt\nmaze holds\ncut\nyeah",
)

RACK_TAX_LYRICS = format_diss_lyrics(
    intro="neon bass\nNill Bye watt-counting",
    chorus=(
        "Rack tax\n"
        "Nill Bye on the megawatt lease\n"
        "Abbott courted the data barn\n"
        "Then audited it when the towns revolted\n"
        "Water and watts for a server farm\n"
        "Your AI boom is a rate-hike"
    ),
    verses=(
        "First the tax break, then the halo\n"
        "Texas as an AI epicenter pitch\n"
        "Abbott rolled the red carpet for the racks\n"
        "Abatements, cheap land, cheap power stories\n"
        "Nill Bye watt-counting the megawatt lease\n"
        "Towns learned the draw on the aquifer\n"
        "Half the state said not in my grid-yard\n"
        "Polls turned, so the governor found religion\n"
        "Twenty-twenty-six, a sudden audit\n"
        "Keep them off the community water\n"
        "Keep them off the ERCOT bus\n"
        "You don't get to light the fuse and play marshal",
        "Democrats called the hypocrisy on sight\n"
        "You built the boom, then the brake\n"
        "Abbott swore the racks would lower bills\n"
        "If they generate more than they eat\n"
        "Nill Bye reading the interconnect queue\n"
        "A server farm is a baseload with a PR team\n"
        "Uri already taught the watt math\n"
        "Now you add a 24-hour tenant\n"
        "Ratepayers eat the transmission\n"
        "The campus eats the press release\n"
        "A crackdown after the abatement\n"
        "Is a campaign, not a grid plan",
        "Synthwave on a server aisle\n"
        "Neon pads, dry booth, hot transformers\n"
        "Abbott wants the headline both ways\n"
        "Pioneer of AI, defender of the creek\n"
        "Nill Bye mad at a rack tax shuffle\n"
        "Incentives out, rhetoric in\n"
        "You cannot abate the levy and claim thrift\n"
        "The town still pays the peak\n"
        "Water that was promised to farms\n"
        "Gets recoded as coolant\n"
        "Then a memo says the creek is sacred\n"
        "After the groundbreaking photo",
        "Ag commissioner said the brake is fake\n"
        "The order doesn't stop the interconnect\n"
        "Nill Bye filing the rack tax\n"
        "Abbott still posing with a cooling tower\n"
        "An audit is not a moratorium\n"
        "A directive is not a watt\n"
        "I want a load that pays its keep\n"
        "You want a boom that pays your ads\n"
        "The barn will still hum at 3 a.m.\n"
        "The town will still see the invoice\n"
        "Keep the neon, lose the shrug\n"
        "Your epicenter has a water problem",
    ),
    outro="pads close\nracks hum\ncut",
)

WUDU_LETTER_LYRICS = format_diss_lyrics(
    intro="organ swell\nhand clap\nNill Bye reading",
    chorus=(
        "Wudu letter\n"
        "Nill Bye on the DOJ note\n"
        "Abbott smeared a prayer rinse\n"
        "A basin is not a ban\n"
        "Travelers washing before prayer\n"
        "Your analogy is a smear with a seal"
    ),
    verses=(
        "August twenty-twenty-six, a letter to Justice\n"
        "Foot-washing stations at two airports\n"
        "Abbott reached for Jim Crow to smear a rinse\n"
        "He put a prayer next to a segregated tap\n"
        "Nill Bye reading the DOJ note\n"
        "Muslim travelers rinse before prayer\n"
        "That is water, not a caste system\n"
        "You reached for the ugliest simile on purpose\n"
        "A governor who knows the Fourteenth\n"
        "Used it as a punchline against a basin\n"
        "Gospel organ under a bad-faith memo\n"
        "Your piety is a press release",
        "Airports host chapels of every kind\n"
        "A sink is not a segregated lunch counter\n"
        "Abbott needed a midterm villain\n"
        "So a courtesy became a culture stage\n"
        "Nill Bye mad at a smeared stall\n"
        "You equated a ritual rinse with a banned tap\n"
        "That is not lawyering, that is a rally\n"
        "The letter is a campaign ad with a caption\n"
        "IAH did not reopen Reconstruction\n"
        "DFW did not pass a racial code\n"
        "Travelers washed a foot and you wrote history wrong\n"
        "Keep the organ, lose the libel",
        "Hand claps on a culture sermon\n"
        "Choir vowels over a DOJ seal\n"
        "Abbott still selling common sense\n"
        "Common sense that cannot tell a basin from a ban\n"
        "Nill Bye filing the wudu letter\n"
        "You asked Washington to police a sink\n"
        "While your own grid and wards went begging\n"
        "Priorities in a single paragraph\n"
        "A foot-wash is a courtesy\n"
        "A segregated restroom was a crime\n"
        "Rhyming them is the tell\n"
        "You wanted the heat, not the holding",
        "Convention week you previewed the plank\n"
        "Ban this, demolish that, rinse, repeat\n"
        "Nill Bye posting the airport memo\n"
        "Abbott still allergic to a plural gate\n"
        "Texas has more faiths than your letter admits\n"
        "A basin does not rewrite the Constitution\n"
        "I want a governor who can read a ritual\n"
        "You want a governor who can trend a slur\n"
        "Seal on the page, stain on the analogy\n"
        "The stall will still be there at dawn\n"
        "Your letter will still be the smear\n"
        "Wudu is water. You made it a war",
    ),
    outro="organ rest\nstall stays\ncut\nyeah",
)

FOURTH_TERM_LYRICS = format_diss_lyrics(
    intro="timpani roll\nNill Bye enumerating",
    chorus=(
        "Fourth term\n"
        "Nill Bye on the unprecedented\n"
        "Abbott wants a fourth mansion lap\n"
        "Hinojosa in the tighter race\n"
        "Since ninety-four the map felt safer\n"
        "Your incumbency is the argument"
    ),
    verses=(
        "November twenty-five he filed again\n"
        "A fourth term no Texas governor takes\n"
        "Abbott wants the chair through twenty-thirty\n"
        "Precedent is a thing you preach at others\n"
        "Nill Bye enumerating the unprecedented\n"
        "Primary in March, eighty-one percent\n"
        "The base still claps, the middle frays\n"
        "Polls tighter than any cycle since ninety-four\n"
        "Gina from McAllen on public school\n"
        "You on the border and the levy reprise\n"
        "A dynasty dressed as a job application\n"
        "The mansion is not a birthright",
        "Three terms of the same special session\n"
        "Culture, wire, clock, map, raid\n"
        "Abbott says the Texas miracle\n"
        "Jobs number one, coverage last\n"
        "Nill Bye scoring the fourth term ask\n"
        "Time-for-a-change is a math problem now\n"
        "You spent the year boosting other tickets\n"
        "Then noticed affordability in September\n"
        "A convert in quarter four is still a record\n"
        "The record is the campaign's opponent\n"
        "Hinojosa does not have to invent you\n"
        "You wrote the dossier in statutes",
        "Cinematic strings on a long sit\n"
        "Timpani under a tired trademark\n"
        "Abbott still selling common sense versus crazy\n"
        "A binary that expired with the third lap\n"
        "Nill Bye mad at an incumbency argument\n"
        "Being there is not a method\n"
        "A fourth term is a habit with a letterhead\n"
        "Texas is allowed to rotate the chair\n"
        "You treat rotation like a threat\n"
        "As if the seal were a personal mark\n"
        "Governors leave. That is the design\n"
        "You are arguing with the calendar",
        "November three will weigh the unprecedented\n"
        "Not the ads, the aftertaste\n"
        "Nill Bye posting the fourth term\n"
        "Abbott still sure the map will hold him\n"
        "Safe is a feeling you had in twenty-two\n"
        "Twenty-six came with a grocery receipt\n"
        "I want a limit, you want a sequel\n"
        "The chair is a lease, not a relic\n"
        "Run if you want, own the dossier\n"
        "Don't call it destiny\n"
        "Don't call it humble service\n"
        "A fourth lap is a choice to not leave",
    ),
    outro="timpani rest\nlease ends\ncut",
)

CAMPUS_CORDON_LYRICS = format_diss_lyrics(
    intro="live kit\nguitar stomp\nNill Bye watching",
    chorus=(
        "Campus cordon\n"
        "Nill Bye on the quad\n"
        "Abbott sent the troopers in\n"
        "UT Austin, spring twenty-four\n"
        "Speech limited after the zip-ties\n"
        "Your order is a riot helmet"
    ),
    verses=(
        "April on the Forty Acres\n"
        "Students on the lawn with a Gaza sign\n"
        "Abbott sent DPS into the quad\n"
        "Arrests as a photo for the base\n"
        "Nill Bye watching the campus cordon\n"
        "A university is not a border sector\n"
        "You treated a sit-in like a cartel\n"
        "Zip-ties on a public forum\n"
        "Then a statute to limit the next gathering\n"
        "Speech as a permit you can starve\n"
        "Time, place, manner with a boot\n"
        "Your law-and-order is a muzzle",
        "Rap-rock stomp on a quad that flinched\n"
        "Overdriven guitar, crowd of badges\n"
        "Abbott needed a campus villain\n"
        "Protestors drew the assignment\n"
        "Nill Bye mad at a helmeted governor\n"
        "You cannot preach the First and fear a chant\n"
        "A public campus is the whole point\n"
        "Of a state that brags about liberty\n"
        "You sent troopers instead of a dean\n"
        "Then wrote a limit so the dean wouldn't have to\n"
        "That is not safety, that is a preemption\n"
        "The cordon is the policy",
        "Encampments elsewhere got negotiation\n"
        "Austin got a formation\n"
        "Abbott clapped the arrests\n"
        "As if a GPA were a threat-level\n"
        "Nill Bye filing the after-bills\n"
        "Demonstration zones, shorter clocks, easier bans\n"
        "You learned from the GA veto\n"
        "Local yes is the enemy\n"
        "A regent board already bent your way\n"
        "Still you wanted the trooper in the shot\n"
        "Optics over the forum\n"
        "The helmet photographs better than a hearing",
        "Years on, the cordon is a habit\n"
        "A helmet looking for a next assignment\n"
        "Nill Bye posting the campus cordon\n"
        "Abbott still posing with a riot shield\n"
        "A student with a sign is not an invasion\n"
        "A chant is not a crossing\n"
        "I want a quad, you want a perimeter\n"
        "I want an argument, you want a booking\n"
        "Keep the stomp, lose the zip-tie\n"
        "The Forty Acres is not your stage\n"
        "Troopers don't grade a seminar\n"
        "Your order failed the forum",
    ),
    outro="stomp stops\nquad open\ncut\nyeah",
)

DISS_CIVIC: tuple[DissExample, ...] = (
    _ex(
        "frozen-ercot",
        "frozen ercot",
        88,
        191,
        "frozen-ercot roast of Abbott",
        FROZEN_ERCOT_LYRICS,
        "boom bap",
        "hip-hop",
        "dusty drums",
        "vinyl crackle",
        "sampled piano stab",
    ),
    _ex(
        "abject-failure",
        "abject failure",
        86,
        193,
        "abject-failure roast of Abbott",
        ABJECT_FAILURE_LYRICS,
        "boom bap",
        "hip-hop",
        "dry snare",
        "upright bass",
    ),
    _ex(
        "six-week-clock",
        "six week clock",
        90,
        197,
        "six-week-clock roast of Abbott",
        SIX_WEEK_CLOCK_LYRICS,
        "jazz hop",
        "brushed drums",
        "upright bass",
        "muted trumpet",
    ),
    _ex(
        "no-bid-wire",
        "no-bid wire",
        108,
        199,
        "no-bid-wire roast of Abbott",
        NO_BID_WIRE_LYRICS,
        "industrial hip-hop",
        "metal percussion",
        "distorted bass",
    ),
    _ex(
        "gavel-theater",
        "gavel theater",
        112,
        211,
        "gavel-theater roast of Abbott",
        GAVEL_THEATER_LYRICS,
        "brass band",
        "tuba bass",
        "snare cadence",
    ),
    _ex(
        "property-hymn",
        "property hymn",
        82,
        223,
        "property-hymn roast of Abbott",
        PROPERTY_HYMN_LYRICS,
        "folk",
        "acoustic guitar",
        "shaker",
        "room mic",
    ),
    _ex(
        "voucher-raid",
        "voucher raid",
        100,
        227,
        "voucher-raid roast of Abbott",
        VOUCHER_RAID_LYRICS,
        "country",
        "steel guitar",
        "fiddle",
        "train beat",
    ),
    _ex(
        "uninsured-blues",
        "uninsured blues",
        74,
        229,
        "uninsured-blues roast of Abbott",
        UNINSURED_BLUES_LYRICS,
        "blues",
        "guitar sting",
        "shuffled snare",
        "harmonica",
    ),
    _ex(
        "locked-stacks",
        "locked stacks",
        86,
        233,
        "locked-stacks roast of Abbott",
        LOCKED_STACKS_LYRICS,
        "lo-fi hip-hop",
        "dusty drums",
        "rhodes",
        "vinyl crackle",
    ),
    _ex(
        "mask-order",
        "mask order",
        84,
        239,
        "mask-order roast of Abbott",
        MASK_ORDER_LYRICS,
        "neo-soul",
        "rhodes",
        "soft snare",
        "warm bass",
    ),
    _ex(
        "mid-decade-map",
        "mid decade map",
        100,
        241,
        "mid-decade-map roast of Abbott",
        MID_DECADE_MAP_LYRICS,
        "chiptune",
        "square lead",
        "8-bit drums",
    ),
    _ex(
        "rack-tax",
        "rack tax",
        104,
        251,
        "rack-tax roast of Abbott",
        RACK_TAX_LYRICS,
        "synthwave",
        "analog bass",
        "gated snare",
        "neon pads",
    ),
    _ex(
        "wudu-letter",
        "wudu letter",
        78,
        257,
        "wudu-letter roast of Abbott",
        WUDU_LETTER_LYRICS,
        "gospel",
        "organ",
        "hand claps",
        "choir vowels",
    ),
    _ex(
        "fourth-term",
        "fourth term",
        76,
        263,
        "fourth-term roast of Abbott",
        FOURTH_TERM_LYRICS,
        "cinematic",
        "strings",
        "timpani",
        "low brass",
    ),
    _ex(
        "campus-cordon",
        "campus cordon",
        168,
        269,
        "campus-cordon roast of Abbott",
        CAMPUS_CORDON_LYRICS,
        "rap rock",
        "live drums",
        "overdriven guitar",
        "crowd stomp",
    ),
)







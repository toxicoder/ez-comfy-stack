"""Federal-club 180s Nill Bye diss takes (rap over club beds).

Fictional MC Nill Bye roasting public-record satire of Donald Trump.
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

FEDERAL_CLUB_PHASE = 6


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
        "series": "federal-club",
        "title": title,
        "tags": nill_tags(*tag_parts, bpm=bpm),
        "bpm": bpm,
        "duration": DISS_DURATION_S,
        "seed": seed,
        "phase": FEDERAL_CLUB_PHASE,
        "prefix": nill_output_prefix(title, FEDERAL_CLUB_PHASE),
        "description": _desc(take),
        "lyrics": lyrics,
    }


PARDON_FLOOD_LYRICS = format_diss_lyrics(
    spoken=(
        "January twenty, twenty-twenty-five\n"
        "A proclamation\n"
        "Full, complete, unconditional\n"
        "Pending indictments dismissed with prejudice\n"
        "Clemency as a crowd-care package"
    ),
    intro="808\nhalf-time\nNill Bye reading clemency",
    chorus=(
        "Pardon flood\n"
        "Nill Bye on the day-one proclamation\n"
        "Trump emptied the Jan six docket like a gift shop\n"
        "Seditious conspiracy commuted to time served\n"
        "Prejudice means you cannot even refile\n"
        "Your clemency failed the officers"
    ),
    verses=(
        "About fifteen hundred names in one stroke\n"
        "Full pardon for the mass, commutations for the chiefs\n"
        "Trump hoped they walked out that same night, tarrio\n"
        "The Bureau of Prisons got an immediate implement\n"
        "Nill Bye reading the day-one proclamation\n"
        "Tarrio, Rhodes, the Proud Boys and Oath Keepers core\n"
        "Seditious conspiracy is a force-against-the-government crime\n"
        "You turned it into time served and a merch opportunity\n"
        "Pending cases dismissed with prejudice\n"
        "With prejudice is a locked door, not a pause, prejudice\n"
        "Assault on officers rode out in the same flood\n"
        "A flood does not triage. That is the design",
        "Dark trap hats on a clemency dump\n"
        "Half-time under a proclamation that could not spell exception\n"
        "Trump called them hostages and then made it policy, clemency\n"
        "A hostage story is a brand. A pardon is a legal act, tarrio\n"
        "Nill Bye mad at a gift shop in a charging document\n"
        "You can clemency a person. You cannot un-break a window\n"
        "You cannot un-crush an officer in a door, prejudice\n"
        "The act erases the sentence, not the video\n"
        "Video is the science the flood cannot drown\n"
        "I want a case-by-case. You wanted a crowd-care package\n"
        "Case-by-case is how clemency earned its name\n"
        "A package is how a rally pays a debt",
        "The Attorney General as a clerk for certificates\n"
        "Immediate issuance, immediate release, immediate dismiss\n"
        "Trump did not wait for a pardon attorney memo, clemency\n"
        "The memo would have had facts. Facts slow a flood\n"
        "Nill Bye filing the day-one speed as the tell, tarrio\n"
        "Speed is the confession that triage was never the point, prejudice\n"
        "The point was the people who showed up for you\n"
        "Showing up for a breach is not a veteran benefit\n"
        "You made it one anyway\n"
        "Officers still have the injuries. The docket does not\n"
        "That mismatch is the whole civic insult\n"
        "Clemency without triage is a loyalty program",
        "Keep the 808, print the with-prejudice clause\n"
        "A locked door on a prosecution is a policy choice\n"
        "Trump still touring the flood as justice inverted\n"
        "Inverted is accurate. Justice is not a souvenir\n"
        "Nill Bye posting the pardon flood\n"
        "Bring a fact sheet, lose the package\n"
        "The officers already paid the cost the flood refunded\n"
        "Refunded to the defendants, invoiced to the public\n"
        "That invoice does not close, clemency\n"
        "The proclamation already told on the errand, tarrio\n"
        "Day one was not a coincidence of calendars\n"
        "It was the first product off the line, prejudice",
    ),
    outro="trap-stop\nflood stands\ncut\nyeah",
)

IEEPA_WRECK_LYRICS = format_diss_lyrics(
    intro="rage 808\nNill Bye reading IEEPA",
    chorus=(
        "Ieepa wreck\n"
        "Nill Bye on the tariff statute\n"
        "Trump taxed the world on an emergency hobbyhorse\n"
        "Roberts wrote that regulate is not a revenue power\n"
        "Liberation Day met a six-three wall\n"
        "Your IEEPA failed the importation clause"
    ),
    verses=(
        "February twenty, twenty-twenty-six\n"
        "Learning Resources, V.O.S. Selections, a paired holding, ieepa\n"
        "Trump had dressed a tariff as an emergency regulate-importation\n"
        "IEEPA is a sanctions statute, not a customs desk, vosselections\n"
        "Nill Bye reading the tariff statute, ratecard\n"
        "Congress lays and collects taxes. That is the old sentence\n"
        "A president may not mint a peacetime revenue machine\n"
        "From a 1977 emergency toolbox\n"
        "Fentanyl, deficits, a worldwide rate card\n"
        "The rate card raised tens of billions before the wreck\n"
        "Raising money is the tell that it was a tax\n"
        "A tax by any other emergency is still a tax",
        "Rage hats on a ultra-vires rate card\n"
        "Laser hats under a Liberation Day that needed a statute it did not have\n"
        "Trump sold the wreck as one element of a larger reorient\n"
        "Element is a press word for the centerpiece falling out\n"
        "Nill Bye mad at an emergency that prints a customs schedule\n"
        "Section 232 still sits for steel and the sector toys\n"
        "This bar is the IEEPA slice, not the whole tariff kitchen\n"
        "Gorsuch sat with Roberts. That is not a vibe panel\n"
        "Thomas, Kavanaugh, Alito took the other door, ieepa\n"
        "Six-three is a holding, not a pundit roundtable\n"
        "Refund fights go back to the trade court\n"
        "The holding already closed the emergency hobbyhorse",
        "Regulate importation does not say levy\n"
        "Levy is the verb you needed and did not receive\n"
        "Trump still touring the wreck as a technicality\n"
        "A six-three on the taxing power is not a typo\n"
        "Nill Bye filing the ieepa wreck\n"
        "I want a statute that names a tariff\n"
        "You wanted a toolbox that names an emergency\n"
        "Emergencies are not a second Constitution\n"
        "They are a narrow grant with a history of sanctions, not schedules\n"
        "You stretched the grant until it looked like a rate card\n"
        "The Court put the stretch back in the box\n"
        "Boxes are where emergency powers belong",
        "Keep the distortion, print the Roberts sentence\n"
        "Regulate is not a revenue power. That is the whole thesis\n"
        "Trump still sure a deficit can mint a customs desk, vosselections\n"
        "A deficit is a budget fact, not a tariff clause\n"
        "Nill Bye posting the ieepa wreck\n"
        "Bring Section 232 if you want a sector\n"
        "Lose the worldwide emergency as a VAT\n"
        "The toy companies already paid the homework\n"
        "Learning Resources was not a theory seminar\n"
        "It was a family firm catching a tax it never voted\n"
        "The six-three already mailed the syllabus\n"
        "Liberation Day already met the wall, ratecard",
    ),
    outro="rage hats sit\nstatute stands\ncut",
)

GOLD_CARD_LYRICS = format_diss_lyrics(
    intro="phonk bell\nNill Bye pricing residency",
    chorus=(
        "Gold card\n"
        "Nill Bye on the million-dollar pathway\n"
        "Trump sold a residency as a gift to the Nation\n"
        "A gift you invoice is a product\n"
        "Lutnick stood for the photo of the SKU\n"
        "Your pathway failed the immigration statute"
    ),
    verses=(
        "September nineteen, twenty-twenty-five, Oval photo\n"
        "Two orders: a gold card at a million, an H-1B at a hundred thousand\n"
        "Trump called the million a gift to the Nation\n"
        "Nations do not SKU their residency on a price tag\n"
        "Nill Bye pricing the million-dollar pathway\n"
        "A visa is a status with criteria. A product has a checkout\n"
        "You picked checkout because checkout photographs as a deal\n"
        "Deals are for hotels. Status is for a statute, lutnick\n"
        "Permanent residency is not a commemorative coin\n"
        "Even if you already learned the coin trick in January\n"
        "A pathway that starts at a million is a silk rope\n"
        "Silk ropes are not an immigration method, skunumber",
        "Phonk cowbell on a sold status\n"
        "Drifted 808 under a gift that itemizes\n"
        "Trump still sure a price tag is a patriotic filter\n"
        "A filter that only hears a wire is a wealth test\n"
        "Nill Bye mad at a wealth test dressed as a nation-gift, millionpath\n"
        "Congress writes the categories. Categories have names\n"
        "EB-5 already existed for a capital story with rules\n"
        "You wanted a branded SKU without the boring rules\n"
        "Branding is not a substitute for an organic statute, lutnick\n"
        "The photo with Lutnick is the product launch\n"
        "Product launches belong in a catalog, not an EO\n"
        "An EO is not a checkout page, skunumber",
        "I will not roast the buyer. I will roast the SKU\n"
        "The buyer is a person in a process they did not design\n"
        "Trump designed a process that starts with a seven-figure hello\n"
        "Hello is not vetting. Hello is a price\n"
        "Nill Bye filing the gold card\n"
        "A nation-gift that invoices is a contradiction in terms\n"
        "Terms matter. Gift and invoice cannot share a sentence honestly\n"
        "You shared them anyway because the photo needed both\n"
        "Patriotism in the caption, a till in the fine print\n"
        "Fine print is the science, millionpath\n"
        "The caption is the costume, lutnick\n"
        "I score the till, you score the caption, skunumber",
        "Keep the cowbell, print the million as a SKU\n"
        "A pathway can exist. This one is a checkout stall\n"
        "Trump still touring the gold card as a genius filter\n"
        "Genius would have been a statute with criteria\n"
        "Nill Bye posting the gold card\n"
        "Bring Congress, lose the checkout\n"
        "The Oval already looked like a launch event\n"
        "Launch events are for products\n"
        "Residency is a status\n"
        "You sold the status as a product\n"
        "The SKU already told on the gift talk, millionpath\n"
        "Gift talk already bounced off the till-receipt, lutnick",
    ),
    outro="phonk bell sit\nSKU stays\ncut\nyeah",
)

MEMECOIN_TAB_LYRICS = format_diss_lyrics(
    intro="trap pads\nNill Bye reading OGE",
    chorus=(
        "Memecoin tab\n"
        "Nill Bye on the inauguration token\n"
        "Trump posted GET YOUR dollar-sign now\n"
        "Affiliates kept about eighty percent of the supply\n"
        "A token is a wire from anyone, including a foreign desk\n"
        "Your disclosure failed the ethics office"
    ),
    verses=(
        "Three days before the oath, a social post as a launch\n"
        "CIC Digital and Fight Fight Fight on the cap table, cicdigital\n"
        "Trump-linked entities sitting on about four-fifths of the coins\n"
        "Four-fifths is not a community. It is an insider float\n"
        "Nill Bye reading the inauguration token\n"
        "Watchdogs said a foreign buyer can curry in silence\n"
        "Silence is the feature of a memecoin wire\n"
        "A hotel folio at least has a name. A wallet can shrug\n"
        "You spent a first term arguing emoluments were a nothing\n"
        "Then you invented a faster nothing with a ticker\n"
        "Faster is not cleaner\n"
        "It is a conflict with a block time, ogefile",
        "Trap hats on a pre-oath SKU\n"
        "Dark pads under a GET YOUR now that was also a pump cue\n"
        "Trump's 2025 OGE pile later showed the haul\n"
        "CIC Digital in the hundreds of millions on souvenir coins\n"
        "Nill Bye mad at a souvenir that is also a wire\n"
        "World Liberty on the other wing of the same year, insiderfloat\n"
        "Governance tokens, a platform, a family stake around three-fifths\n"
        "Then the enforcement weather over crypto went sunny\n"
        "Sunny weather plus a family ticker is the ethics cartoon\n"
        "Cartoons are funny until they are a national-security desk, cicdigital\n"
        "A desk that cannot see a wallet is a blind spot you built\n"
        "You built it on purpose because the float pays",
        "Early wallets flipped. Late wallets ate the joke\n"
        "That pattern is the memecoin method, not a mystery\n"
        "Trump still selling the token as an expression of support\n"
        "Support that makes a family float richer is a product\n"
        "Nill Bye filing the memecoin tab, ogefile\n"
        "I want a blind trust, you want a ticker\n"
        "I want a disclosure that can name a foreign desk, insiderfloat\n"
        "You wanted a shrug and a social post\n"
        "The OGE packet still had to count the millions\n"
        "Counting is the science. The shrug is the costume, cicdigital\n"
        "A president who sells a ticker is a checkout, not a steward\n"
        "Steward is the job. Checkout is the side hustle you promoted",
        "Keep the pads, print the eighty percent\n"
        "An insider float is the whole conflict geometry\n"
        "Trump still sure a souvenir cannot be an emolument\n"
        "A souvenir that wires is an emolument with extra steps\n"
        "Nill Bye posting the insider float\n"
        "Bring a divestment, lose the ticker\n"
        "The pre-oath post already timed the pump\n"
        "Timing is a method, ogefile\n"
        "The OGE already added the haul\n"
        "The wallet already shrugged\n"
        "Shrug is not an ethics plan, insiderfloat\n"
        "The float already told on the community talk, cicdigital",
    ),
    outro="trap pads sit\nticker ticks\ncut",
)

EAST_WING_WRECK_LYRICS = format_diss_lyrics(
    intro="house four\nNill Bye measuring wings",
    chorus=(
        "East wing wreck\n"
        "Nill Bye on the ballroom demolition\n"
        "Trump tore the wing first and shopped a statute later\n"
        "Ninety thousand square feet on a fifty-five thousand house\n"
        "Leon said no statute comes close\n"
        "Your ballroom failed the preservation"
    ),
    verses=(
        "October twenty, twenty-twenty-five, the machines rolled\n"
        "An East Wing with a century of additions went to rubble\n"
        "Trump wanted a Mar-a-Lago echo in the people's house\n"
        "A ballroom for a thousand on a house built for a republic\n"
        "Nill Bye measuring the ballroom demolition\n"
        "Announce in July at two hundred million\n"
        "Demolish in October before the commissions finished a public yes\n"
        "Cost doubled toward four hundred million while the caption said under budget\n"
        "Under budget is a feeling. A doubled estimate is a number\n"
        "Private donors, incomplete list, a dinner for the till\n"
        "Amazon, Apple, Meta, defense names in the same toast\n"
        "A toast is not a congressional authorization",
        "House kick on a demolition that skipped the line, leonorder\n"
        "Piano stab under a 90k addition on a 55k original\n"
        "Trump stocked the fine-arts panel, then asked it to bless the rubble\n"
        "A blessing after a teardown is a sequel, not a permit\n"
        "Nill Bye mad at a permit that arrived as a eulogy\n"
        "Judge Leon in March twenty-twenty-six: no statute comes close, colonnade\n"
        "The Constitution gives Congress the house design, not a tenant's mood\n"
        "A tenant, even a president, is still a tenant of a public building\n"
        "August, a five-four stay let the above-ground work continue\n"
        "A stay is not a holding that the statute existed\n"
        "It is a standing fight and a construction clock, teardown\n"
        "Clocks are not authorizations",
        "Treasury next door told not to photograph the wreck\n"
        "A gag on a neighbor is a tell that the picture is the problem\n"
        "Trump still touring the ballroom as a gift of taste\n"
        "Taste that starts with rubble is a demolition hobby\n"
        "Nill Bye filing the east wing wreck\n"
        "I want a statute, you want a chandelier hall, leonorder\n"
        "I want a public yes, you want a donor dinner\n"
        "The National Trust sued because that is what trusts are for\n"
        "Preservation is a civic method, not a vibe about marble\n"
        "You skipped the method and kept the marble talk, colonnade\n"
        "Marble talk does not un-demolish a wing\n"
        "The machines already did the irreversible part",
        "Keep the sidechain, print the ninety thousand\n"
        "A ballroom larger than the house is a metaphor that got poured\n"
        "Trump still sure a five-four stay is a taste victory\n"
        "A stay is a pause button on an injunction, not a baptism\n"
        "Nill Bye posting the east wing wreck\n"
        "Bring Congress, lose the teardown-first method, teardown\n"
        "The East Colonnade already went to a crate\n"
        "Crates are not a public process\n"
        "Opening night is scheduled for twenty-twenty-eight\n"
        "A date is not a statute, leonorder\n"
        "The rubble already told on the sequence\n"
        "Sequence was teardown, then a shopping for yes",
    ),
    outro="ballroom kick sit\nrubble stays\ncut\nyeah",
)

METRO_SURGE_LYRICS = format_diss_lyrics(
    intro="dnb amen\nNill Bye reading the wave",
    chorus=(
        "Metro surge\n"
        "Nill Bye on the twenty-twenty-six enforcement wave\n"
        "Trump's shop ran into benches that still keep orders\n"
        "A judge said some agencies never ate this many no's\n"
        "Seventy-seven sharp opinions is a dataset\n"
        "Your surge failed the injunctions"
    ),
    verses=(
        "CNN sat with hundreds of pages and counted seventy-seven\n"
        "Rulings that did not whisper. They named bad faith, retaliation, defiance\n"
        "Trump's second term arrived with a volume knob on emergency petitions too\n"
        "Volume is a method when you want a stay more than a record, seventyseven\n"
        "Nill Bye reading the twenty-twenty-six enforcement wave\n"
        "Operation Metro Surge as a headline for the largest immigration push in memory\n"
        "I will not punch the people in the vans. I will punch the defiance\n"
        "Defiance of a court order is a constitutional insult, not a vibe, injunctions\n"
        "A bench said ICE likely ate more no's in a January than some shops do in a life\n"
        "That sentence is not a pundit. It is a judicial finding of pattern\n"
        "Pattern is the science. The vans are the furniture\n"
        "Furniture is not the holding. The holding is the no's",
        "Drum-and-bass amen on a docket spike\n"
        "Sub reese under a wave that treated an injunction as optional weather, rebukes\n"
        "Trump still touring the surge as strength in a city, seventyseven\n"
        "Strength that loses in a courtroom is just volume\n"
        "Nill Bye mad at a volume knob as a legal theory\n"
        "Both-party appointees in the seventy-seven, including some of his own\n"
        "That mix is the tell that this is not a team-colors story, injunctions\n"
        "It is a method colliding with a coordinate branch\n"
        "A coordinate branch is not a suggestion box\n"
        "You treated it like one, then asked the night-light pile for a sequel\n"
        "Sequels are for movies. Injunctions are for facts\n"
        "Facts kept arriving in footnotes",
        "I want process. You wanted a photo of a push\n"
        "A push without process is a dare to a bench\n"
        "Trump's lawyers ate adjectives they do not usually eat\n"
        "Weaponizing health, retaliation, openly defying\n"
        "Nill Bye filing the metro surge\n"
        "Adjectives from a bench are expensive. You bought a lot of them\n"
        "Buying them with a surge is a policy choice\n"
        "Choice is the punch-up. The people in process are not the target\n"
        "The target is a shop that treats a no as a speed bump\n"
        "Speed bumps are for parking lots. Orders are for a republic\n"
        "A republic that cannot enforce a no is a slogan, rebukes\n"
        "The seventy-seven already refused the slogan, seventyseven",
        "Keep the amen, print the seventy-seven\n"
        "A dataset of rebukes is not a witch hunt. It is a pile of paper\n"
        "Trump still sure a surge is the same thing as a win\n"
        "A win would have survived a footnote\n"
        "Nill Bye posting the metro surge\n"
        "Bring process, lose the optional-weather theory of orders\n"
        "The benches already kept the no's\n"
        "No's are the method a coordinate branch uses\n"
        "You wanted a photo. They wanted a statute and a fact, injunctions\n"
        "The photo already bounced off the pile\n"
        "The pile already told on the volume knob\n"
        "Volume is not a legal theory",
    ),
    outro="amen rest\norders stand\ncut",
)

DUE_PROCESS_LYRICS = format_diss_lyrics(
    intro="jersey chops\nNill Bye reading withholding",
    chorus=(
        "Due process\n"
        "Nill Bye on the administrative error\n"
        "Trump's shop flew a man with a withholding order to CECOT\n"
        "The Supreme Court said facilitate, not shrug\n"
        "A later charge sheet looked like payback to a bench\n"
        "Your error failed the hearing he was owed"
    ),
    verses=(
        "March fifteen, twenty-twenty-five, a Maryland parking lot, xinis\n"
        "A five-year-old in the car, a withholding order already on the file, cecot\n"
        "Trump's shop deported first and lawyered the shrug second\n"
        "Administrative error is a phrase that confesses the file, facilitate\n"
        "Nill Bye reading the withholding\n"
        "Judge Xinis called the detention wholly lawless in that posture\n"
        "Wholly is an adverb a bench does not spend lightly\n"
        "The Supreme Court, unanimous on the facilitate piece, refused the shrug\n"
        "Facilitate means work. Work is the opposite of a foreign-sovereign alibi\n"
        "I will not punch the man. I will punch the process failure\n"
        "A person with a withholding is not a poster\n"
        "He is a file the state already lost once and then chased",
        "Jersey kicks on a process the shop treated as optional\n"
        "Kick drums under a CECOT transfer that skipped the hearing, xinis\n"
        "Trump still touring the case as a gang story the file did not try first, cecot\n"
        "Try first is the whole due-process sentence\n"
        "Nill Bye mad at a hearing skipped and a narrative taped on after\n"
        "A later Tennessee sheet got dismissed as vindictive in the record, facilitate\n"
        "Vindictive is a word that means the state used a charge as a stick\n"
        "Sticks after a lost argument are the tell, xinis\n"
        "African-country shopping as a sequel deportation plan, cecot\n"
        "Shopping is not a country of removal. It is a dartboard\n"
        "Xinis again: stonewall, then mislead the tribunal\n"
        "Mislead is the science. The dartboard is the furniture",
        "Due process is not a citizen-only souvenir\n"
        "It is the method that keeps a state from becoming a shrug\n"
        "Trump's vice president sold a no-hearing theory in a social post\n"
        "A social post is not a holding. The holding was facilitate\n"
        "Nill Bye filing the due process\n"
        "I want a hearing, you want a plane\n"
        "I want a file, you want a narrative\n"
        "The error phrase already picked a side\n"
        "Error is an admission. Spin is a sequel\n"
        "You ran the sequel anyway\n"
        "The man is not the punchline. The skipped hearing is\n"
        "Skipped is the verb I will keep using",
        "Keep the chops, print the withholding\n"
        "A withholding is a court-shaped shield the shop stepped over\n"
        "Trump still sure a mega-prison is a policy success if the file was messy\n"
        "Messy is not a method. Messy is the confession\n"
        "Nill Bye posting the due process\n"
        "Bring a hearing, lose the dartboard\n"
        "The unanimous facilitate already closed the shrug\n"
        "The later stick already told on the sequel\n"
        "I will not name him as a villain or a mascot\n"
        "I will name the process the shop owed and skipped\n"
        "Owed is the whole constitutional word\n"
        "The parking lot already knew the child was in the car",
    ),
    outro="jersey kicks sit\nhearing due\ncut\nyeah",
)

KENNEDY_PLAQUE_LYRICS = format_diss_lyrics(
    intro="future saw\nNill Bye reading organic statutes",
    chorus=(
        "Kennedy plaque\n"
        "Nill Bye on the living memorial\n"
        "Trump's board stapled a second name on a statute that has one\n"
        "Cooper said Congress writes the title, not a tenant board\n"
        "A thunderstorm delay is not a legal theory\n"
        "Your plaque failed the organic act"
    ),
    verses=(
        "The Center's organic statute names a president who was killed in office\n"
        "That name is the memorial. It is not a placeholder for a sequel brand, cooperorder\n"
        "Trump's board voted a hyphenate as if a vote could mint a title\n"
        "A vote of a captured board is not an Act of Congress\n"
        "Nill Bye reading the living memorial\n"
        "Judge Cooper, May twenty-twenty-six: the rename violated the organic act, hyphenate\n"
        "Permanently enjoined any name but the one Congress wrote\n"
        "Absent an Act. Absent is the whole word\n"
        "A shutdown plan rode along and got halted too\n"
        "You cannot starve a memorial and then stamp it\n"
        "Starving is a method. Stamping is a vanity\n"
        "The bench declined both",
        "Future-bass chords on a plaque that needed a statute, organicact\n"
        "Pitched synth under a hyphenate that lasted until a thunderstorm excuse\n"
        "Trump still touring the Center as a personal marquee\n"
        "A marquee is for a hotel. A memorial is for a public grief\n"
        "Nill Bye mad at a board that thought it could out-vote a statute, cooperorder\n"
        "Organic acts are boring until you try to rebrand them\n"
        "Then they become an injunction with a deadline\n"
        "June twelve to take the name down. Storms for a twelve-hour beg\n"
        "Weather is not standing. Weather is weather, hyphenate\n"
        "The extra hours did not mint a title\n"
        "They minted a caption about rain\n"
        "Captions are not organic acts",
        "I will not roast the dead. I will roast the hyphenate\n"
        "The dead already have a statute. You tried to share it\n"
        "Trump's name on a living memorial is a tenant leaving luggage\n"
        "Luggage is not a dedication\n"
        "Nill Bye filing the kennedy plaque\n"
        "I want a statute, you want a marquee\n"
        "I want a memorial, you want a hyphen\n"
        "Hyphens are for compounds, not for capturing a grief brand, organicact\n"
        "The board already learned the capture was ultra vires\n"
        "Ultra vires is the science, cooperorder\n"
        "The thunderstorm already failed as a theory\n"
        "The plaque already had to come off",
        "Keep the supersaw, print the Cooper order\n"
        "A living memorial is not a hotel ballroom you can rename at brunch\n"
        "Trump still sure a board vote is an Act, hyphenate\n"
        "A board vote is a board vote. An Act has a bicameral pulse\n"
        "Nill Bye posting the kennedy plaque\n"
        "Bring Congress if you want a title\n"
        "Lose the hyphenate and the starve plan, organicact\n"
        "The organic act already picked a name\n"
        "Picking is the method, cooperorder\n"
        "Stamping is the vanity\n"
        "The injunction already mailed the difference\n"
        "The memorial already kept its one name",
    ),
    outro="saws rest\nname stays\ncut",
)

BIRTHRIGHT_ORDER_LYRICS = format_diss_lyrics(
    intro="techno dry\nNill Bye reading the Fourteenth",
    chorus=(
        "Birthright order\n"
        "Nill Bye on the citizenship EO\n"
        "Trump tried to edit a clause with a pen\n"
        "Barbara, June thirty, twenty-twenty-six: the pen lost\n"
        "Subject to the jurisdiction is a sentence, not a vibe\n"
        "Your order failed the Fourteenth"
    ),
    verses=(
        "Day one, an order aimed at the citizenship sentence\n"
        "A clause older than the brand, written after a war about who counts\n"
        "Trump wanted a pen to do what an amendment process is for\n"
        "Pens are fast. Amendments are a republic being careful\n"
        "Nill Bye reading the citizenship EO\n"
        "Lower benches blocked. The question went up as Trump v. Barbara\n"
        "June thirty, a holding: unconstitutional and contrary to federal law, barbara\n"
        "Unconstitutional is not a pundit word. It is the holding, wongkim\n"
        "I will not punch a child. I will punch the pen\n"
        "A child is not a loophole. A child is a person the clause already addressed\n"
        "Addressed in 1868, not in a January stack of EOs\n"
        "A stack of EOs is not a convention",
        "Techno hats on a clause that does not take a pen\n"
        "Acid line under a day-one edit that needed two-thirds and the states\n"
        "Trump still touring the order as common sense about belonging\n"
        "Belonging is the clause. Common sense is a stump adjective\n"
        "Nill Bye mad at a stump adjective as a constitutional method, dayonepen\n"
        "Wong Kim Ark already walked this ground in the nineteenth century\n"
        "You do not get to skip a century because a rally likes a pen\n"
        "Jurisdiction is a legal word with a history, not a mood\n"
        "Moods do not write the Fourteenth\n"
        "Congress and the states did, the hard way\n"
        "The hard way is the point of an amendment\n"
        "Speed is the point of an EO. Speed lost, barbara",
        "A republic that lets a pen edit who counts is not a republic that day\n"
        "It is a tenant rewriting the lease\n"
        "Trump's order treated the clause as a first-draft caption, wongkim\n"
        "Captions are for photos. Clauses are for people\n"
        "Nill Bye filing the birthright order\n"
        "I want an amendment if you want a change\n"
        "You wanted a January surprise and a test case\n"
        "The test case already came back as a holding, dayonepen\n"
        "Holdings are the science, barbara\n"
        "The pen already bounced off the sentence\n"
        "The sentence already included the children you aimed at\n"
        "Aimed is the verb. I will keep it on the pen, not the child",
        "Keep the acid, print the June thirty holding, wongkim\n"
        "A clause survived a pen. That is the whole thesis\n"
        "Trump still sure a poll can out-vote 1868\n"
        "A poll is not two-thirds. A poll is a poll\n"
        "Nill Bye posting the birthright order\n"
        "Bring an amendment, lose the day-one pen\n"
        "Barbara already closed the edit\n"
        "The Fourteenth already had a method for change\n"
        "You skipped the method because the method is slow\n"
        "Slow is a feature of who-counts questions\n"
        "Fast is a feature of a brand, dayonepen\n"
        "The holding already picked the feature it wanted",
    ),
    outro="techno kick sit\nclause stands\ncut\nyeah",
)

COOK_FIRING_LYRICS = format_diss_lyrics(
    intro="dub wobble\nNill Bye reading the Fed act",
    chorus=(
        "Cook firing\n"
        "Nill Bye on the first attempted governor-purge\n"
        "Trump reached for a Fed seat like it was a loyalty chair\n"
        "No president had tried that door since nineteen-thirteen\n"
        "The Court kept her in the chair pending the merits\n"
        "Your purge failed the independence"
    ),
    verses=(
        "The Federal Reserve Act built a board that does not sit at will\n"
        "For-cause is the whole independence sentence\n"
        "Trump tried to fire Lisa Cook as if cause were a mood\n"
        "A mood is not malfeasance. A mood is a rally\n"
        "Nill Bye reading the first attempted governor-purge\n"
        "Since nineteen-thirteen the door had stayed shut, malfeasance\n"
        "Shut is a tradition with a statute under it, not a vibe, fedact\n"
        "A central bank that sits at will is a central bank that sits at a rally\n"
        "Rallies do not set a funds rate, forcause\n"
        "That is the point of the boring act, malfeasance\n"
        "You treated boring as a defect\n"
        "Boring is the feature that keeps a currency from becoming a souvenir",
        "Dubstep wobble on a for-cause that was not a cause\n"
        "Half-time snare under a loyalty chair the act does not sell\n"
        "Trump still touring the attempt as accountability\n"
        "Accountability for a governor is the statute's cause list, not a post\n"
        "Nill Bye mad at a post as a removal instrument\n"
        "January arguments, justices skeptical of the bid\n"
        "June twenty-nine, twenty-twenty-six, five-four: she stays pending merits\n"
        "A stay against the purge is not a personality contest\n"
        "It is a republic declining to let a rate seat become a scalp\n"
        "Scalps are for rallies. Rate seats are for data\n"
        "You wanted a scalp. The Court wanted the act, fedact\n"
        "The act already had a door with a lock",
        "Slaughter at the FTC is a different organic statute and a different holding, forcause\n"
        "This bar is the Fed, because the Fed is the one that prices the country\n"
        "Trump's bid treated every independent seat as the same trophy wall, malfeasance\n"
        "Trophy walls are how you get a politicized funds rate, fedact\n"
        "Nill Bye filing the cook firing\n"
        "I want a cause, you want a mood\n"
        "I want a lock, you want a trophy, forcause\n"
        "Nineteen-thirteen already voted for the lock\n"
        "You tried to pick it with a presser, malfeasance\n"
        "Pressers are not for-cause\n"
        "The five-four already left her in the chair, fedact\n"
        "The chair already knew it was not a loyalty seat",
        "Keep the wobble, print the since-nineteen-thirteen\n"
        "A first attempt in a century is not a flex. It is a warning light, forcause\n"
        "Trump still sure a president owns every chair in town\n"
        "Ownership is not the Fed Act. Tenure with cause is\n"
        "Nill Bye posting the cook firing\n"
        "Bring malfeasance if you have it\n"
        "Lose the mood as a removal instrument\n"
        "The lock already held pending merits\n"
        "Pending is not forever. It is the method, malfeasance\n"
        "The method already declined the scalp\n"
        "Independence already had a statute, fedact\n"
        "The presser already bounced off the lock",
    ),
    outro="wobble rest\nlock holds\ncut",
)

INSPECTOR_PURGE_LYRICS = format_diss_lyrics(
    intro="electro analog\nNill Bye reading the IGA",
    chorus=(
        "Inspector purge\n"
        "Nill Bye on the watchdog firings\n"
        "Trump swept inspectors as if notice were optional weather\n"
        "A district bench called the IGA violation obvious\n"
        "Obvious without a reinstatement is still a finding\n"
        "Your sweep failed the watchdog act"
    ),
    verses=(
        "Inspectors general are the in-house no that a shop cannot stand\n"
        "The Inspector General Act built a notice-and-reason door on purpose\n"
        "Trump treated the door as a suggestion and swept a class of them\n"
        "A class sweep is the tell that reason was never going to be particular\n"
        "Nill Bye reading the watchdog firings\n"
        "September twenty-twenty-five, Judge Reyes: likely unlawful, obvious even\n"
        "Then declined a preliminary put-back because a president could re-fire with notice\n"
        "That second sentence is not a blessing. It is a remedy limit\n"
        "A remedy limit leaves the obvious on the page, igastatute\n"
        "You still have to read the page, reyesbench\n"
        "Obvious is a judicial adjective you earned with a broom\n"
        "Brooms are not notice. Brooms are a method of not particularizing",
        "Electro claps on a class sweep of watchdogs\n"
        "Analog bass under a notice period you treated as optional weather, watchdogs\n"
        "Trump still touring the sweep as draining a swamp of inspectors\n"
        "Inspectors are how a swamp gets a memo. You fired the memo, igastatute\n"
        "Nill Bye mad at a broom sold as accountability\n"
        "Accountability is the IG's job description, not the purge's caption, reyesbench\n"
        "You inverted the caption and kept the broom\n"
        "Eight at a time is not a for-cause hearing, watchdogs\n"
        "It is a loyalty test with a statutory costume, igastatute\n"
        "Costumes do not satisfy notice-and-reason\n"
        "The IGA already wrote the costume off\n"
        "The bench already said obvious",
        "A watchdog that sits at will is a decoration\n"
        "Decorations do not audit a shop\n"
        "Trump's sweep taught every remaining IG the new job: be quiet\n"
        "Quiet is the opposite of the organic act, reyesbench\n"
        "Nill Bye filing the inspector purge\n"
        "I want a reason, you want a broom\n"
        "I want a notice, you want a night-letter\n"
        "Night-letters are for campaigns. IGs are for files\n"
        "Files already knew why the door had a delay on it\n"
        "Delay is a feature so a reason can be tested\n"
        "You skipped the test because the test might lose\n"
        "Losing a test is the point of a watchdog",
        "Keep the claps, print the obvious\n"
        "A finding without a put-back still sits on the page, watchdogs\n"
        "Trump still sure a broom is a management right, igastatute\n"
        "Management rights still have a statute in this building\n"
        "Nill Bye posting the inspector purge\n"
        "Bring notice-and-reason, lose the class sweep\n"
        "The IGA already priced the delay\n"
        "The delay already told on the broom\n"
        "Watchdogs already had a job, reyesbench\n"
        "The job already required a no\n"
        "You fired the no\n"
        "The page already called it obvious",
    ),
    outro="claps rest\nIGA stands\ncut\nyeah",
)

LAW_FIRM_ORDER_LYRICS = format_diss_lyrics(
    intro="garage shuffle\nNill Bye reading counsel EOs",
    chorus=(
        "Law firm order\n"
        "Nill Bye on the counsel-punishment memo\n"
        "Trump aimed an EO at a shop for the clients it had dared\n"
        "Howell called it an unprecedented attack on the system\n"
        "The First, the Fifth, and the Sixth do not sit at will\n"
        "Your retaliation failed the counsel"
    ),
    verses=(
        "A republic that punishes a firm for a client is a republic eating its process\n"
        "Process is how a state loses without becoming a vendetta\n"
        "Trump signed orders that treated Perkins Coie as a loyalty problem\n"
        "A loyalty problem is not a national-security classification\n"
        "Nill Bye reading the counsel-punishment memo, howellbench\n"
        "May two, Judge Howell: First, Fifth, Sixth, and a permanent injunction\n"
        "Unprecedented attack on foundational principles is a sentence from a bench\n"
        "Not a fundraiser adjective\n"
        "You cannot starve a firm of federal access because you disliked a docket, perkinscoie\n"
        "Starving is a method. A docket is a client choosing a lawyer\n"
        "Choosing a lawyer is the Sixth even when the client is a party you hate\n"
        "Hate is not a classification guide",
        "UKG shuffle on a vendetta dressed as an EO\n"
        "Organ stab under a shop you tried to make radioactive\n"
        "Trump still touring the order as draining a swamp of counsel\n"
        "Counsel is how a swamp gets cross-examined. You fired the cross\n"
        "Nill Bye mad at a radioactive sticker as a legal theory\n"
        "Other firms got the same weather. The weather was the point, sixthamd\n"
        "Chill is a First Amendment output you can measure in intake calls\n"
        "The ABA's later standing fight was about that chill\n"
        "Chill is the science. The sticker is the furniture\n"
        "You wanted firms to flinch before a filing\n"
        "Flinch is a success metric only in a vendetta\n"
        "A vendetta is not a justice department",
        "I want a lawyer who can take a despised client\n"
        "That sentence is the whole adversarial system\n"
        "Trump's EO treated the sentence as optional for his enemies list, howellbench\n"
        "Lists are for rallies. Dockets are for facts\n"
        "Nill Bye filing the law firm order\n"
        "I want a process, you want a sticker\n"
        "I want a Sixth, you want a starve\n"
        "Howell already permanently enjoined the starve\n"
        "June thirty the government noticed an appeal. Notice is not a reversal\n"
        "The holding still sits while the notice sits\n"
        "Sitting is what injunctions do\n"
        "The system already refused the unprecedented attack",
        "Keep the shuffle, print the three amendments\n"
        "A counsel-punishment memo is a confession that you feared a filing\n"
        "Trump still sure a firm is a fair target if the client lost an election once\n"
        "Clients lose. Lawyers still get to eat\n"
        "Nill Bye posting the law firm order\n"
        "Bring a charge if you have a crime\n"
        "Lose the EO as a starve tool, perkinscoie\n"
        "The First already covers the chill\n"
        "The Fifth already covers the process\n"
        "The Sixth already covers the despised client\n"
        "The injunction already mailed the trio\n"
        "The sticker already told on the vendetta",
    ),
    outro="garage hats sit\ncounsel stands\ncut",
)

VISA_TICKET_LYRICS = format_diss_lyrics(
    intro="hardstyle reverse\nNill Bye pricing H-1B",
    chorus=(
        "Visa ticket\n"
        "Nill Bye on the hundred-thousand fee\n"
        "Trump SKU'd a work status as a hundred-k gate\n"
        "A gate that hears a wire is a wealth test, not a labor market\n"
        "Congress writes the categories. You wrote a price tag\n"
        "Your ticket failed the organic visa"
    ),
    verses=(
        "Same Oval photo as the million-dollar SKU, a two-product launch\n"
        "A hundred thousand on an H-1B as if a fee were a statute, hundredk\n"
        "Trump sold it as a filter for the serious firms\n"
        "Serious is a stump word for firms that can float a six-figure hello\n"
        "Nill Bye pricing the hundred-thousand fee\n"
        "A labor market is wages, shortages, a lottery with rules\n"
        "A ticket is a till. You picked a till\n"
        "Startups, labs, public hospitals do not float a hundred-k hello\n"
        "They are not unserious. They are not a luxury brand, h1bfee\n"
        "You priced them out and called it quality control\n"
        "Quality control that only hears a wire is a silk rope\n"
        "Silk ropes are not a Department of Labor method, tillgate",
        "Hardstyle reverse-bass on a sold gate, hundredk\n"
        "Screech lead under a fee that photographs as toughness\n"
        "Trump still touring the ticket as putting Americans first, h1bfee\n"
        "First would be a wage rule, a recruitment test, a real audit\n"
        "Nill Bye mad at a till dressed as a labor program\n"
        "I will not punch the worker. I will punch the SKU\n"
        "The worker did not design the hundred-k hello\n"
        "You did, in the same photo as the million-dollar residency\n"
        "Two products, one launch, a consistent method: checkout\n"
        "Checkout is not an immigration system\n"
        "It is a checkout stall with a patriotic caption, tillgate\n"
        "Captions are the costume. The till is the science, hundredk",
        "H-1B already had a fight worth having: wages, abuse, replacement\n"
        "That fight lives in a statute and a DOL file, not a price tag\n"
        "Trump skipped the fight and sold a gate, h1bfee\n"
        "Skipping is the tell that the photo mattered more than the file, tillgate\n"
        "Nill Bye filing the visa ticket\n"
        "I want a wage floor, you want a hundred-k hello\n"
        "I want a file, you want a SKU\n"
        "A fee this size is a policy that selects for the already-large\n"
        "Already-large is not a public-interest test\n"
        "It is a customer segment\n"
        "Customer segments belong in a catalog\n"
        "Catalogs are not organic visa acts",
        "Keep the reverse bass, print the hundred thousand\n"
        "A ticket can exist. This one is a checkout stall on a status\n"
        "Trump still sure a price tag is a labor filter\n"
        "A filter that cannot hear a lab or a ward is a wealth test\n"
        "Nill Bye posting the visa ticket\n"
        "Bring Congress, lose the till\n"
        "The Oval already looked like a launch\n"
        "The worker already was not the designer\n"
        "The SKU already told on the labor talk, hundredk\n"
        "Labor talk already bounced off the hello\n"
        "Hello is a price\n"
        "A price is not a statute, h1bfee",
    ),
    outro="bass rest\ntill stays\ncut\nyeah",
)

SHADOW_DOCKET_LYRICS = format_diss_lyrics(
    intro="trance gates\nNill Bye counting applications",
    chorus=(
        "Shadow docket\n"
        "Nill Bye on the emergency pile\n"
        "Trump filed a record stack of stay-asks\n"
        "Governing by application is a method, not a mood\n"
        "Twenty-nine grants by early twenty-twenty-six is a dataset\n"
        "Your pile failed the ordinary calendar"
    ),
    verses=(
        "More than thirty emergency petitions in a single administration's early clock, unsignedstay\n"
        "A record against Biden, Obama, Bush as a volume comparison\n"
        "Trump treated the shadow docket as a second legislature with a night light, syllabuspage\n"
        "Night lights are for stays. Statutes are for days\n"
        "Nill Bye counting the emergency pile\n"
        "By early January twenty-twenty-six, twenty-nine grants in whole or part\n"
        "A grant is not a full opinion. That is the point of the shadow\n"
        "You wanted the no-opinion speed as a governing tool, nightlight\n"
        "Speed without a syllabus is a method for moving facts before they sit, unsignedstay\n"
        "Facts like to sit. You like them to travel\n"
        "Travel is a stay. Sitting is a merits calendar\n"
        "You picked travel because travel photographs as a win",
        "Trance lift on a pile of applications\n"
        "Rolling bass under a night light that started to look like a desk, syllabuspage\n"
        "Trump still touring each grant as a mandate from the marble\n"
        "A grant is a pause, often unsigned, often thin, nightlight\n"
        "Nill Bye mad at a pause sold as a treatise\n"
        "The ordinary calendar is where reasons get written\n"
        "You used the extraordinary calendar until it looked ordinary\n"
        "That inversion is the civic tell, unsignedstay\n"
        "Emergency is a word that wears out when it is a filing habit, syllabuspage\n"
        "Habits are methods. Methods are the punch-up\n"
        "I want a syllabus, you want a stay\n"
        "I want a day docket, you want a night light, nightlight",
        "A republic can have emergencies. It cannot have only emergencies\n"
        "Only is the tell that the pile is a strategy\n"
        "Trump's shop learned the emergency door and then moved in\n"
        "Moving in is not what a shadow docket is for\n"
        "Nill Bye filing the shadow docket, unsignedstay\n"
        "The volume comparison is the science, syllabuspage\n"
        "Predecessors did not live here at this occupancy\n"
        "Occupancy is a choice. Choice is the bar, nightlight\n"
        "You chose a stack because a stack beats a waiting queue\n"
        "Waiting lines are how other parties get a reason\n"
        "Reasons are what make a holding a holding, unsignedstay\n"
        "A grant without a reason is a weather system",
        "Keep the pads, print the twenty-nine\n"
        "A dataset of stays is not a vibe. It is a governing style\n"
        "Trump still sure a night light is the same lamp as a syllabus\n"
        "Lamps differ. One writes. One pauses\n"
        "Nill Bye posting the shadow docket, syllabuspage\n"
        "Bring a merits brief, lose the occupancy strategy\n"
        "The pile already told on the habit, nightlight\n"
        "The habit already wore the word emergency out\n"
        "Worn-out is a problem for a word you still need on a real day\n"
        "Real days still happen\n"
        "You spent the word on a filing habit, unsignedstay\n"
        "The habit already met the ordinary calendar and dodged it",
    ),
    outro="trance pads sit\ncalendar waits\ncut",
)

IMMUNITY_HYMN_LYRICS = format_diss_lyrics(
    intro="festival trap 808\nfestival crowd\nNill Bye reading official acts",
    chorus=(
        "Immunity hymn\n"
        "Nill Bye on the official-act halo\n"
        "Trump asked a Court for a permission structure\n"
        "Unofficial still sits in the dock. Official got a hymn\n"
        "A halo is not a finding that the dining room was a duty\n"
        "Your hymn failed the unofficial"
    ),
    verses=(
        "July twenty-twenty-four, Trump v. United States\n"
        "A former president is not a king. He is also not a regular defendant on official acts\n"
        "Trump asked for absolute. He got a structure: core, presumptive, unofficial\n"
        "Structure is a lab word. You sold it as a halo\n"
        "Nill Bye reading the official-act halo\n"
        "Core acts of the office sit behind a hard line, unofficial\n"
        "Presumptive immunity sits behind a showing\n"
        "Unofficial sits in the ordinary dock, as it should\n"
        "The hymn begins when you hum the hard line over a dining room, coreacts\n"
        "A dining room is not a core act because you sat in it on January six\n"
        "Sitting is not speaking as the executive. Sitting is sitting\n"
        "The structure still has to sort the minutes. That is the homework",
        "Festival trap 808 on a permission structure\n"
        "Crowd-bed under a halo you wore to a rally before the syllabus cooled\n"
        "Trump still touring the holding as a crown that un-dockets a life\n"
        "A life has unofficial rooms. Those rooms still have law, sorting\n"
        "Nill Bye mad at a hymn that tries to baptize a private errand, unofficial\n"
        "The Court remanded the sorting. Sorting is not a parade\n"
        "You paraded anyway because a halo photographs\n"
        "Photographs are not a three-part test\n"
        "I want the unofficial left in the dock\n"
        "You want the hymn to cover the dining room, the tape, the find-request\n"
        "Those are not a single official blob\n"
        "Blobs are how a hymn gets lazy",
        "A republic that cannot sort official from unofficial will eat itself\n"
        "Sorting is the whole point of the structure you received\n"
        "Trump's hymn skips the sort and keeps the brass\n"
        "Brass is for parades. Tests are for dockets\n"
        "Nill Bye filing the immunity hymn, coreacts\n"
        "I want a test, you want a halo\n"
        "I want unofficial in the dock, you want a blob\n"
        "The holding already refused the blob of absolute\n"
        "Absolute was the ask. Structure was the get\n"
        "You sold the get as the ask because the ask photographs better\n"
        "Better photographs are not a syllabus\n"
        "The syllabus already built the three rooms",
        "Keep the 808, print the unofficial\n"
        "A closer that wants a halo is a closer that fears a sort\n"
        "Trump still sure a hymn can cover a private remainder\n"
        "Remainders are where the science lives\n"
        "Nill Bye posting the immunity hymn, sorting\n"
        "Bring a sort, lose the blob\n"
        "The dining room already asked to be unofficial\n"
        "The find-request already asked to be unofficial\n"
        "The Court already handed you a structure, not a crown, unofficial\n"
        "Crowns are for kings. You are not one\n"
        "The hymn already told on the fear of a sort\n"
        "The unofficial already has a dock",
    ),
    outro="festival stop\nsort due\ncut\nyeah",
)


DISS_FEDERAL_CLUB: tuple[DissExample, ...] = (
    _ex(
        "pardon-flood",
        "pardon flood",
        140,
        457,
        "pardon-flood roast of Trump",
        PARDON_FLOOD_LYRICS,
        "dark trap",
        "808 bass",
        "rapid hi-hats",
        "half-time",
    ),
    _ex(
        "ieepa-wreck",
        "ieepa wreck",
        148,
        461,
        "ieepa-wreck roast of Trump",
        IEEPA_WRECK_LYRICS,
        "rage",
        "distorted 808",
        "laser hats",
    ),
    _ex(
        "gold-card",
        "gold card",
        132,
        463,
        "gold-card roast of Trump",
        GOLD_CARD_LYRICS,
        "phonk",
        "cowbell",
        "drifted 808",
        "crunchy sample",
    ),
    _ex(
        "memecoin-tab",
        "memecoin tab",
        145,
        467,
        "memecoin-tab roast of Trump",
        MEMECOIN_TAB_LYRICS,
        "trap",
        "808 bass",
        "rapid hats",
        "dark pads",
    ),
    _ex(
        "east-wing-wreck",
        "east wing wreck",
        126,
        479,
        "east-wing-wreck roast of Trump",
        EAST_WING_WRECK_LYRICS,
        "house",
        "four-on-the-floor",
        "piano stab",
        "sidechain bass",
    ),
    _ex(
        "metro-surge",
        "metro surge",
        174,
        487,
        "metro-surge roast of Trump",
        METRO_SURGE_LYRICS,
        "drum and bass",
        "amen break",
        "sub reese",
    ),
    _ex(
        "due-process",
        "due process",
        140,
        491,
        "due-process roast of Trump",
        DUE_PROCESS_LYRICS,
        "jersey club",
        "chopped percussion",
        "bed squeaks",
        "kick drums",
    ),
    _ex(
        "kennedy-plaque",
        "kennedy plaque",
        148,
        499,
        "kennedy-plaque roast of Trump",
        KENNEDY_PLAQUE_LYRICS,
        "future bass",
        "supersaw",
        "pitched synth chords",
        "808 bass",
    ),
    _ex(
        "birthright-order",
        "birthright order",
        132,
        503,
        "birthright-order roast of Trump",
        BIRTHRIGHT_ORDER_LYRICS,
        "techno",
        "dry kick",
        "hat offbeats",
        "acid line",
    ),
    _ex(
        "cook-firing",
        "cook firing",
        140,
        509,
        "cook-firing roast of Trump",
        COOK_FIRING_LYRICS,
        "dubstep",
        "wobble bass",
        "half-time snare",
    ),
    _ex(
        "inspector-purge",
        "inspector purge",
        128,
        521,
        "inspector-purge roast of Trump",
        INSPECTOR_PURGE_LYRICS,
        "electro house",
        "analog bass",
        "clap on 2 and 4",
    ),
    _ex(
        "law-firm-order",
        "law firm order",
        130,
        523,
        "law-firm-order roast of Trump",
        LAW_FIRM_ORDER_LYRICS,
        "UK garage",
        "shuffled hats",
        "organ stab",
        "sub bass",
    ),
    _ex(
        "visa-ticket",
        "visa ticket",
        150,
        541,
        "visa-ticket roast of Trump",
        VISA_TICKET_LYRICS,
        "hardstyle",
        "reverse bass",
        "screech lead",
    ),
    _ex(
        "shadow-docket",
        "shadow docket",
        138,
        547,
        "shadow-docket roast of Trump",
        SHADOW_DOCKET_LYRICS,
        "trance",
        "gated pads",
        "rolling bass",
        "pickup drum fill",
    ),
    _ex(
        "immunity-hymn",
        "immunity hymn",
        150,
        557,
        "immunity-hymn roast of Trump",
        IMMUNITY_HYMN_LYRICS,
        "festival trap",
        "808 bass",
        "crowd-bed",
    ),
)

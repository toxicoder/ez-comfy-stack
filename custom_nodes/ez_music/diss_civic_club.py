"""Civic-club 180s Nill Bye diss takes (rap over club beds).

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

CIVIC_CLUB_PHASE = 4


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
        "series": "civic-club",
        "title": title,
        "tags": nill_tags(*tag_parts, bpm=bpm),
        "bpm": bpm,
        "duration": DISS_DURATION_S,
        "seed": seed,
        "phase": CIVIC_CLUB_PHASE,
        "prefix": nill_output_prefix(title, CIVIC_CLUB_PHASE),
        "description": _desc(take),
        "lyrics": lyrics,
    }


LONE_STAR_TAB_LYRICS = format_diss_lyrics(
    intro="808\nhalf-time\nNill Bye summing",
    chorus=(
        "Lone Star tab\n"
        "Nill Bye on the eleven-billion\n"
        "Abbott still renews the disaster\n"
        "Five years in, the crossing peaked\n"
        "A mission without a metric\n"
        "Your border is a budget"
    ),
    verses=(
        "March twenty-twenty-one, the operation opened\n"
        "Troopers, Guard, a trespass workaround\n"
        "Abbott built a Lone Star tab\n"
        "Eleven billion and climbing\n"
        "Nill Bye summing the weekly burn\n"
        "Two-point-five million a week at the peak\n"
        "Ten thousand troops on a state order\n"
        "No GI bill, no federal shield\n"
        "You said Washington failed the river\n"
        "Then you billed Texas for a forever mission\n"
        "A disaster that renews like a subscription\n"
        "The tab is the policy",
        "HRW called it expensive, ineffective, abusive\n"
        "You called it denying cartels a lane\n"
        "Abbott still wants a federal reimbursement\n"
        "Eleven billion as an IOU to himself\n"
        "Nill Bye reading the appropriation\n"
        "House writers cutting checks they already regret\n"
        "A mission that grew faster than a memo\n"
        "Pay delayed, camps dirty, troops sent home in waves\n"
        "You cannot measure success if the stamp never ends\n"
        "A peak in crossings, a peak in spend, no sunset\n"
        "Dark trap on a blank-check war\n"
        "Your security is a line item",
        "Trespass charges as an immigration hack\n"
        "State cops doing a federal job by nickname\n"
        "Abbott needed a workaround to the Supremacy Clause\n"
        "So a rancher's complaint became a docket\n"
        "Nill Bye mad at a tab with no ledger-goal\n"
        "Felony counts on a press release\n"
        "Eighty percent of smuggling bookings were citizens\n"
        "Teenagers in a ten-year minimum\n"
        "That is not a cartel takedown\n"
        "That is a volume business in a courtroom\n"
        "You export the photo, keep the invoice\n"
        "Lone Star is a brand with a burn rate",
        "Twenty-twenty-six, still declaring the emergency\n"
        "White House flipped, crossings down, stamp still wet\n"
        "Nill Bye posting the Lone Star tab\n"
        "Abbott still posing on a riverbank tour\n"
        "A program that cannot end because ending is the tell\n"
        "Success would kill the appropriation\n"
        "So success is never declared, only funded\n"
        "I want a metric, you want a renewal\n"
        "Eleven billion is a confession\n"
        "The border was the excuse\n"
        "The tab was the point\n"
        "Keep the 808, lose the forever war",
    ),
    outro="hats cease\ntab open\ncut\nyeah",
)

RIVER_BUOY_LYRICS = format_diss_lyrics(
    intro="distorted 808\nlaser hats\nNill Bye sounding",
    chorus=(
        "River buoy\n"
        "Nill Bye on the floating wall\n"
        "Abbott put saw-teeth in the current\n"
        "Razor on the bank, orange in the channel\n"
        "DOJ sued, the river still cut\n"
        "Your deterrent is a snag"
    ),
    verses=(
        "Eagle Pass, a string of orange buoys\n"
        "Saw-bladed, chained, a floating barrier\n"
        "Abbott planted a river buoy\n"
        "In a channel that kills without help\n"
        "Nill Bye sounding the current\n"
        "Seventy thousand rolls of concertina\n"
        "People snagged in wire, turned back to the current\n"
        "A barrier designed to injure the crossing\n"
        "Washington asked a court to pull them\n"
        "You dared the feds to come get the chain\n"
        "Rage hats on a cruelty gadget\n"
        "Your sovereignty is a snag-hook",
        "The Rio Grande is not a moat you own alone\n"
        "It is a boundary with a treaty and a flow\n"
        "Abbott treated it like a prop table\n"
        "Buoys for the cameras, wire for the feet\n"
        "Nill Bye mad at a floating barrier\n"
        "A child in the current does not parse jurisdiction\n"
        "You wrote a presser on a drowning risk\n"
        "Then called the risk a feature\n"
        "DOJ filed, you appealed, the orange stayed\n"
        "A standoff as a product\n"
        "Injury is the metric you will not print\n"
        "The river prints it anyway",
        "Concertina on the bank like a thicket\n"
        "Troopers told to hold the line, not the person\n"
        "Abbott's memo: don't assist the crossing\n"
        "Hold the line, not the person in the current\n"
        "Nill Bye holding the cruelty gadget\n"
        "A policy written to make the river worse\n"
        "You engineered a snag and called it security\n"
        "A saw-tooth is not a code-book\n"
        "A chain is not a hearing\n"
        "The current was already the danger\n"
        "You added teeth because the photo needed teeth\n"
        "Rage drop, no mercy in the mix",
        "Courts can yank a buoy\n"
        "They cannot yank the intent\n"
        "Nill Bye posting the river buoy\n"
        "Abbott still standing on the bank for the lens\n"
        "A floating wall that does not stop a presser\n"
        "It stops a person who cannot swim the extra yard\n"
        "I want a border with a process\n"
        "You want a border with a laceration\n"
        "Orange in the channel, red in the briefing\n"
        "Keep the distortion, lose the saw\n"
        "The river was a river\n"
        "You made it a trap",
    ),
    outro="hats ring\nchain stays\ncut",
)

BUS_RECEIPT_LYRICS = format_diss_lyrics(
    intro="cowbell\ndrifted 808\nNill Bye punching",
    chorus=(
        "Bus receipt\n"
        "Nill Bye on the manifest\n"
        "Abbott mailed people like a presser\n"
        "NYC, D.C., Chicago on a ticket\n"
        "A person is not a payload\n"
        "Your compassion is a waybill"
    ),
    verses=(
        "More than a hundred thousand on a coach\n"
        "Destinations picked for the headline\n"
        "Abbott signed a bus receipt\n"
        "Podium cities picked for the yell\n"
        "Nill Bye punching the manifest\n"
        "Phonk cowbell on a one-way errand\n"
        "You called it sharing the burden\n"
        "It was exporting a photo-op\n"
        "Cities that asked for coordination got a drop-off\n"
        "No notice, winter, a podium waiting\n"
        "A person is not a parcel\n"
        "Your waybill is the cruelty",
        "The spreadsheet had a media column\n"
        "Which mayor would yell on cable\n"
        "Abbott played dispatcher for a narrative\n"
        "Asylum as a prop in a blue city\n"
        "Nill Bye mad at a ticket-as-taunt\n"
        "You can move a person and miss a policy\n"
        "A coach does not adjudicate a claim\n"
        "It just relocates the camera\n"
        "Texas spent the fare and kept the talking point\n"
        "Receiving cities spent the shelter\n"
        "That is not federalism\n"
        "That is a chain letter with a diesel engine",
        "Phonk drift on a midnight arrival\n"
        "Crunchy sample, no welcome script\n"
        "Abbott still brags the receipt\n"
        "As if a bus were a border solution\n"
        "Nill Bye reading the drop-off logs\n"
        "Some sent to VP's door for the clip\n"
        "A human being as a tagged parcel\n"
        "You wrapped the insult in a travel voucher\n"
        "Coordination would have been government\n"
        "Ambush is a campaign\n"
        "I want a process, you want a mayor on defense\n"
        "The manifest is the method",
        "Years of coaches, same stunt, new city\n"
        "The tab hid inside the bigger burn\n"
        "Nill Bye posting the bus receipt\n"
        "Abbott still treating a passenger as a payload\n"
        "A waybill is not a welcome\n"
        "A drop-off is not a hearing\n"
        "Keep the cowbell, lose the parcel act\n"
        "People get off a coach tired, not converted\n"
        "Your message landed on a sidewalk\n"
        "The policy never did\n"
        "File the receipt, file the stunt\n"
        "The phonk already told on you",
    ),
    outro="cowbell rest\nmanifest cold\ncut\nyeah",
)

GUARD_DETAIL_LYRICS = format_diss_lyrics(
    intro="rapid hats\ndark pads\nNill Bye calling roll",
    chorus=(
        "Guard detail\n"
        "Nill Bye on the state order\n"
        "Abbott sent them far from home\n"
        "Seventeen non-combat, some by their own hand\n"
        "Bishop drowned on a rescue\n"
        "Your mission ate the roster"
    ),
    verses=(
        "State orders, not federal orders\n"
        "No GI bill, no survivor guarantee at first\n"
        "Abbott put the Guard on a forever detail\n"
        "Jobs paused, families on hold, pay late\n"
        "Nill Bye calling roll on a quiet list\n"
        "Twelve to seventeen dead, none in a firefight\n"
        "Suicide, wreck, a negligent discharge\n"
        "A parking lot in San Antonio\n"
        "Joshua had a dream job waiting\n"
        "The exemption never came\n"
        "You deployed a kid and called it elite\n"
        "The roster paid in quiet ways",
        "Bishop Evans went into the Rio\n"
        "Two people in the current, he went after them\n"
        "Abbott's river policy said hold the bank\n"
        "The soldier said hold the person\n"
        "Nill Bye keeping Bishop on the detail\n"
        "The House later named a benefit bill for him\n"
        "Troopers already had the half-million\n"
        "Guard families had to beg the same\n"
        "You will pose with a C-17 of tin soldiers\n"
        "Chicago-bound, riot shields, a caption\n"
        "Ever ready, deploying now\n"
        "Ready for a camera, late for a death benefit",
        "Dajuan, nineteen, a negligent round\n"
        "Training and kit that did not match the speech\n"
        "Abbott likes the elite Texas National Guard slogan\n"
        "The camps had pay problems and dirty water\n"
        "Nill Bye mad at a detail with no care\n"
        "Involuntary call-ups until the department blinked\n"
        "Thousands sent home after the damage\n"
        "The mission still hungry for bodies\n"
        "A soldier is not a sandbag\n"
        "A state order is not a career\n"
        "You borrowed a life and underwrote it cheap\n"
        "The trap kit cannot hide the roll",
        "Texas Monthly asked where the soldiers went\n"
        "The answer is a parking lot, a river, a barracks\n"
        "Nill Bye posting the Guard detail\n"
        "Abbott still boarding planes for other cities\n"
        "A caption on a Globemaster is not a eulogy\n"
        "A shield is not a stipend\n"
        "I want the roster home\n"
        "You want the roster in the shot\n"
        "Seventeen is not a rumor\n"
        "It is a cost you will not read on a stump\n"
        "Keep the hats, lose the forever call-up\n"
        "The detail already came due",
    ),
    outro="hats fade\nroll closed\ncut",
)

CHASE_WRECK_LYRICS = format_diss_lyrics(
    intro="four-on-the-floor\nsidechain\nNill Bye clocking",
    chorus=(
        "Chase wreck\n"
        "Nill Bye on the pursuit log\n"
        "Abbott flooded OLS counties with troopers\n"
        "One-oh-six dead, three-oh-one hurt\n"
        "Bystanders in the intersection\n"
        "Your policing is a high-speed bet"
    ),
    verses=(
        "Human Rights Watch did the count\n"
        "One hundred six killed in the chase wreck\n"
        "Abbott's counties, thirteen percent of the people\n"
        "Two-thirds of the pursuits\n"
        "Nill Bye clocking the pursuit log\n"
        "DPS up fifty percent in three years\n"
        "Seventy percent of that spike in OLS zones\n"
        "No officer dead, plenty of bystanders\n"
        "A mother on her way to a shift\n"
        "A child in a car that was not the suspect\n"
        "You added troopers without a pursuit policy that holds\n"
        "The intersection paid",
        "Best practice says don't chase for a hunch\n"
        "CBP itself cooled the high-speed habit\n"
        "Abbott leaned the other way\n"
        "More badges, more ignition, more wrecks\n"
        "Nill Bye mad at a four-on-the-floor funeral\n"
        "House kick under a crash report\n"
        "You cannot flood a county with state cops\n"
        "And act shocked when the highway becomes a weapon\n"
        "Ten bystanders dead in the first tallies\n"
        "Twenty hurt who were not in the suspect car\n"
        "That is not collateral in a war\n"
        "That is a policy with a skid mark",
        "Sixty-seven counties in the program\n"
        "A death rate eight times the national chase-rate\n"
        "Abbott still funds the same posture\n"
        "Deportation extra, same accelerator\n"
        "Nill Bye reading the Statesman follow-up\n"
        "Thirty-two more after the first report\n"
        "The wreck did not plateau, it compounded\n"
        "A mission without a brake pedal\n"
        "You measure seizures and skip the morgue\n"
        "Fentanyl numbers on a podium\n"
        "One-oh-six not on the slide\n"
        "The piano stab cannot cover a siren",
        "End the appropriation, HRW said\n"
        "You renewed it like a club membership\n"
        "Nill Bye posting the chase wreck\n"
        "Abbott still selling the flood of troopers as safety\n"
        "Safety for who, in which intersection\n"
        "A bystander does not get a briefing\n"
        "I want a pursuit that can let go\n"
        "You want a pursuit that films well\n"
        "Sidechain pump on a crash log\n"
        "Keep the house kick, lose the bet\n"
        "One-oh-six is a club you should close\n"
        "The wreck already called last round",
    ),
    outro="kick stops\nlog open\ncut\nyeah",
)

FREQUENCY_DROP_LYRICS = format_diss_lyrics(
    intro="amen break\nsub reese\nNill Bye counting hertz",
    chorus=(
        "Frequency drop\n"
        "Nill Bye on the load-shed\n"
        "Abbott's grid kissed collapse\n"
        "Twenty thousand megawatts yanked\n"
        "Largest manual cut in the country\n"
        "Your drop almost went dark forever"
    ),
    verses=(
        "ERCOT ordered the big shed\n"
        "Twenty thousand megawatts off the bus\n"
        "Abbott's isolated island had no neighbor\n"
        "Frequency falling toward the cliff\n"
        "Nill Bye counting the hertz as they sagged\n"
        "A few minutes from a black-start nightmare\n"
        "Weeks of dark if the relays had gone\n"
        "Drum-and-bass on a near-death grid\n"
        "You got a drop you did not want\n"
        "Operators did, so the state still exists\n"
        "A club drop is a joke\n"
        "This one almost took the lights for a month",
        "Amen break under a control-room panic\n"
        "Reese bass like a turbine trip\n"
        "Abbott was on TV selling a wind story\n"
        "While the frequency was the only story\n"
        "Nill Bye mad at a governor off-beat\n"
        "The drop is physics, not a culture war\n"
        "Sixty hertz or you lose the machine\n"
        "You cannot Fox-News a relay\n"
        "Load-shed is a last tool\n"
        "You made it a lifestyle for four days\n"
        "Rolling blackouts that did not roll, they stuck\n"
        "The amen already told the truth",
        "Largest manually controlled shed on the books\n"
        "FERC wrote it like a eulogy for luck\n"
        "Abbott later called the grid flawless\n"
        "A sequel with amnesia\n"
        "Nill Bye filing the frequency drop\n"
        "You cannot brag a save you almost fumbled\n"
        "The operators held the cliff\n"
        "You held a microphone\n"
        "A reese does not care about your trademark\n"
        "Neither does sixty hertz\n"
        "I want weatherize, you want a drop that photographs\n"
        "The control room does not do encore",
        "When the next arctic sits on DFW\n"
        "The same island, the same math\n"
        "Nill Bye posting the load-shed\n"
        "Abbott still dancing like the amen was a trophy\n"
        "A drop you survive is not a drop you designed\n"
        "It is a warning with a body-count nearby\n"
        "Keep the break, lose the swagger\n"
        "Twenty thousand off is not a flex\n"
        "It is the sound of a state that almost ended\n"
        "The sub is the remaining margin\n"
        "Don't DJ a collapse\n"
        "The frequency already dropped you",
    ),
    outro="amen halt\nhertz holds\ncut",
)

PERMITLESS_LYRICS = format_diss_lyrics(
    intro="chopped percussion\nkick drums\nNill Bye reading HB",
    chorus=(
        "Permitless\n"
        "Nill Bye on nineteen-twenty-seven\n"
        "Abbott made the license optional\n"
        "Twenty-one and a holster, no class\n"
        "Then a school with a legal rifle\n"
        "Your freedom skipped the range"
    ),
    verses=(
        "September first, twenty-twenty-one\n"
        "HB nineteen-twenty-seven went live\n"
        "Abbott signed permitless carry\n"
        "Open or concealed, no exam, no range-time\n"
        "Nill Bye reading the penal rewrite\n"
        "Forty-six-oh-two used to mean a license\n"
        "You deleted the ticket and kept the gun\n"
        "Club bounce on a statute that shrugs\n"
        "Training became a vibe\n"
        "A class A became a lifestyle\n"
        "You called it constitutional\n"
        "It was a primary gift with a holster",
        "Eight months later Robb had a legal purchase\n"
        "Eighteen, two rifles, a store that followed the new weather\n"
        "Abbott said more laws would not have mattered\n"
        "He had just subtracted one\n"
        "Nill Bye mad at a bounce with no brake\n"
        "You cannot loosen the carry and then point at the statute pile\n"
        "The pile is smaller because you took a brick out\n"
        "Permitless is the brick\n"
        "Kick drums on a policy that skipped the qualifier\n"
        "Who should carry is a question you retired\n"
        "Anyone twenty-one not already banned\n"
        "Is a standard you can print on a hat",
        "Other states kept the class and the range\n"
        "You kept the presser\n"
        "Abbott still sells the holster as liberty\n"
        "Liberty without a qualifier is a slogan\n"
        "Nill Bye filing permitless\n"
        "A bounce that does not ask if you can hit a target\n"
        "Only if you can buy one\n"
        "The chopped percussion is the loophole\n"
        "You did not wait for Robb to freeze the statute\n"
        "The bill was already the weather\n"
        "Afterward you froze the reform instead\n"
        "A special session for doors, not for carry",
        "Club-bed bounce, no permit in the mix\n"
        "Bed squeaks, statute shrugs, kick on one\n"
        "Nill Bye posting the holster statute\n"
        "Abbott still sure a class is tyranny\n"
        "A class is a minimum\n"
        "You removed the floor and kept the slogan\n"
        "I want a range, you want a rally\n"
        "I want a qualifier, you want a vibe\n"
        "Keep the bounce, lose the shrug\n"
        "Nineteen-twenty-seven is the quiet preload\n"
        "The next purchase does not need your blessing\n"
        "You already gave it",
    ),
    outro="kicks rest\nholster law\ncut\nyeah",
)

TRIGGER_CLOCK_LYRICS = format_diss_lyrics(
    intro="supersaw\npitched chords\nNill Bye watching Dobbs",
    chorus=(
        "Trigger clock\n"
        "Nill Bye on twelve-eighty\n"
        "Abbott hid a felony in a delay\n"
        "Thirty days after the opinion became judgment\n"
        "Life in prison for a doctor\n"
        "Your ban was a time bomb"
    ),
    verses=(
        "HB twelve-eighty sat armed in twenty-one\n"
        "Human Life Protection Act, a sleeper\n"
        "Abbott signed a trigger clock\n"
        "Not a bounty, a cage\n"
        "Nill Bye watching Dobbs become a date\n"
        "July twenty-six judgment, plus thirty\n"
        "August twenty-five the felony went live\n"
        "Future-bass swell on a criminal statute\n"
        "A doctor looking at a hundred thousand civil\n"
        "And a possible life term\n"
        "That is not a heartbeat civil suit\n"
        "That is the second clock, the louder one",
        "SB eight was the snitch. This is the cell\n"
        "Two machines, one governor, one year\n"
        "Abbott got the civil bounty and the criminal cage\n"
        "A belt and a bolt\n"
        "Nill Bye mad at a delay that was the point\n"
        "Write it before the Court moves\n"
        "Let the Court pull the pin\n"
        "Then shrug like the physics did it\n"
        "A trigger is a coward's favorite tool\n"
        "You get the ban without the signing-day photo of the cage\n"
        "The photo already ran on the civil statute\n"
        "The cage arrived by calendar",
        "Exceptions on paper, chill in the ward\n"
        "Reasonable medical judgment until the AG tweets\n"
        "Abbott still reciting the emergency clause\n"
        "The trigger does not care about the clause\n"
        "Nill Bye filing twelve-eighty\n"
        "A pitched chord on a felony\n"
        "You can dress a bomb as a delayed enactment\n"
        "It still detonates on a clinic\n"
        "Providers left, remaining ones lawyer-up first\n"
        "Care second if the chart is screaming\n"
        "That lag is the statute working as designed\n"
        "A time bomb with a legislative caption",
        "Future bass, pretty swell, ugly payload\n"
        "The saw is bright, the clause is dark\n"
        "Nill Bye posting the trigger clock\n"
        "Abbott still calling it protection\n"
        "Protection that threatens the person with the scalpel\n"
        "Until the patient is close enough to dying\n"
        "I want a doctor unafraid of the code\n"
        "You want a code the doctor is afraid of\n"
        "Keep the chords, lose the sleeper\n"
        "Thirty days was not mercy\n"
        "It was a fuse\n"
        "The judgment lit it",
    ),
    outro="saw fades\ncage holds\ncut",
)

DISASTER_STAMP_LYRICS = format_diss_lyrics(
    spoken=(
        "Border disaster\n"
        "Monthly since twenty-twenty-one\n"
        "Still wet in twenty-twenty-six\n"
        "The stamp is the government"
    ),
    intro="dry kick\nacid line\nNill Bye inking",
    chorus=(
        "Disaster stamp\n"
        "Nill Bye on the proclamation\n"
        "Abbott renews a five-year emergency\n"
        "Contracting rules on pause\n"
        "A month is a loophole if you repeat it\n"
        "Your disaster is a habit"
    ),
    verses=(
        "Every month the same ink\n"
        "A border emergency that outlived the peak\n"
        "Abbott treats a stamp like a standing army\n"
        "TDEM paper as a second legislature\n"
        "Nill Bye inking the calendar\n"
        "COVID taught the forever order\n"
        "His own party tried to clip that habit\n"
        "Then the river gave it a second life\n"
        "Techno kick on a bureaucratic cheat\n"
        "You cannot lose a vote you never take\n"
        "A proclamation skips the bid, skips the sunset\n"
        "Democracy as a rubber date",
        "April twenty-twenty-six, still quietly renewed\n"
        "Crossings off the highs, stamp on the highs\n"
        "Abbott needs the paper to keep the spend legal-ish\n"
        "And to loan troopers to someone else's city\n"
        "Nill Bye mad at a monthly miracle\n"
        "An emergency that can wait for the printer\n"
        "Is not an emergency\n"
        "It is a subscription\n"
        "Acid line under a seal\n"
        "Health agencies told to track status\n"
        "A gang designated by press release\n"
        "The stamp makes any noun a crisis",
        "Legislature side-eye, then another check\n"
        "Because arguing with a disaster poll is expensive\n"
        "Abbott learned the COVID lesson backward\n"
        "Keep the pen, lose the humility\n"
        "Nill Bye filing the forever seal\n"
        "Five years is a regime, not a moment\n"
        "You bypassed contracting in the name of haste\n"
        "Haste that had time to become a franchise\n"
        "A true disaster ends\n"
        "Yours files a continuation\n"
        "I want a vote, you want a date-seal\n"
        "The kick already knows which one is cheaper",
        "Hat offbeats on a forever seal\n"
        "Dry as the process you skipped\n"
        "Nill Bye posting the proclamation\n"
        "Abbott still sure the river justifies the ink\n"
        "A river is weather\n"
        "A stamp is a choice\n"
        "Keep the techno, lose the standing emergency\n"
        "Five years in, the disaster is the government\n"
        "Not the crossing, not the cartel slide\n"
        "The government that will not put the pen down\n"
        "Ink dry, power wet\n"
        "Your habit has a seal",
    ),
    outro="kick dry\nseal holds\ncut\nyeah",
)

WINDMILL_BLAME_LYRICS = format_diss_lyrics(
    intro="wobble bass\nhalf-time snare\nNill Bye fact-checking",
    chorus=(
        "Windmill blame\n"
        "Nill Bye on the Fox clip\n"
        "Abbott said the solar quit\n"
        "Gas wells iced, coal tripped, nukes derated\n"
        "A scapegoat with a pretty blade\n"
        "Your wobble is a talking point"
    ),
    verses=(
        "Day after Uri, the clip went national\n"
        "Wind and solar got shut down, he said\n"
        "Abbott needed a villain that photographs\n"
        "A turbine is prettier than a frozen separator\n"
        "Nill Bye fact-checking the mix\n"
        "FERC: freezing plus fuel, three-quarters of the trips\n"
        "Gas the majority of the failed units\n"
        "Wind a share, not the story\n"
        "UT later: Permian gas production cratered\n"
        "Eighty-five percent down in the basin\n"
        "You cannot wobble that into a Green Deal fable\n"
        "The wellhead already testified",
        "Local TV he admitted everything tripped\n"
        "Then Fox got a simpler script\n"
        "Abbott ran the simpler script\n"
        "Because a frozen gas field is an own-goal\n"
        "Nill Bye mad at a scapegoat bass-riff\n"
        "Call it windmill blame, keep the low-end dirty\n"
        "You sold a culture war as a generation mix\n"
        "While thermal plants iced at the intake filters\n"
        "Four component types, two-thirds of ERCOT's outages\n"
        "Protect those, skip the scapegoat\n"
        "A half-time snare on a lie that traveled\n"
        "The turbine was the costume",
        "Twenty-twenty-six radio: the grid works flawlessly\n"
        "A sequel to everything that needed to be done was done\n"
        "Abbott still allergic to the gas chart\n"
        "Still fluent in the blade\n"
        "Nill Bye filing the windmill blame\n"
        "You can weatherize a talking point in a day\n"
        "A well takes a statute and a inspector\n"
        "You picked the day\n"
        "Wobble bass under a scapegoat\n"
        "The drop is the moment the facts arrive\n"
        "They arrived. You kept dancing\n"
        "The clip still pays in primary season",
        "A turbine that ices is a maintenance note\n"
        "A governor who ices the record is a method\n"
        "Nill Bye posting the Fox mix-up\n"
        "Abbott still sure the blade did the murder\n"
        "Murder is a word for the freeze, not the farm\n"
        "Hypothermia does not care what you blamed\n"
        "I want the wellhead on the slide\n"
        "You want the windmill in the chyron\n"
        "Keep the wobble, lose the fable\n"
        "The mix already named the majority fuel\n"
        "It was not a pinwheel\n"
        "It was the brand you run on",
    ),
    outro="wobble out\nmix stands\ncut",
)

YASS_PRIMARY_LYRICS = format_diss_lyrics(
    intro="analog bass\nclap on two\nNill Bye tracing wires",
    chorus=(
        "Yass primary\n"
        "Nill Bye on the out-of-state cash\n"
        "Abbott spent millions beating his own\n"
        "Rural GOP who would not raid the campus\n"
        "A billionaire from Pennsylvania\n"
        "Your party is a purchased caucus"
    ),
    verses=(
        "Eighteen races, a TV flood\n"
        "Hearst ran the tape: turnout spiked where he spent\n"
        "Abbott put Yass money on rural incumbents' throats\n"
        "Members who voted no on the ESA\n"
        "Nill Bye tracing the wires\n"
        "Janis Holt over Bailes in a fourteen-point bury\n"
        "Seven hundred thousand on one seat\n"
        "Border ads for a school measure\n"
        "You did not argue the classroom\n"
        "You argued loyalty\n"
        "Electro house on a purge\n"
        "The clap is the donor",
        "Paxton hunted his impeachers the same season\n"
        "He spent none of his own and won less\n"
        "Abbott spent and won near four-fifths\n"
        "A governor as a PAC with a seal\n"
        "Nill Bye mad at a purchased caucus\n"
        "The House that said no became a House that said yes\n"
        "That is not persuasion\n"
        "That is a buyout\n"
        "Rural districts that needed the public campus\n"
        "Got a primary instead of a formula\n"
        "You called it the will of the voters\n"
        "After you bought the weather the voters walked through",
        "Clap on two and four, analog growl\n"
        "A dance-floor for a political funeral\n"
        "Abbott still sells it as school choice energy\n"
        "Energy that came from Pennsylvania\n"
        "Nill Bye filing the Yass primary\n"
        "Ten million as a rumor until the filings landed\n"
        "Then it was a fact with a receipt\n"
        "You cannot un-spend a burial\n"
        "A member who would not loot kids' campuses\n"
        "Is not a RINO. He is a constituent-listener\n"
        "You made listening a firing offense\n"
        "The electro already wrote the pink slip",
        "The ESA followed the new majority\n"
        "As designed, as purchased\n"
        "Nill Bye posting the out-of-state cash\n"
        "Abbott still sure Texas asked for this\n"
        "Texas asked in ads he paid for\n"
        "That is a loop, not a mandate\n"
        "I want a caucus, you want a cart\n"
        "I want a vote, you want a wire\n"
        "Keep the clap, print the donor\n"
        "Yass should be in the caption every time\n"
        "The primary was not a conversation\n"
        "It was a transaction with a receipt",
    ),
    outro="claps stop\nwires show\ncut\nyeah",
)

HOLD_REQUEST_LYRICS = format_diss_lyrics(
    intro="shuffled hats\norgan stab\nNill Bye filing",
    chorus=(
        "Hold request\n"
        "Nill Bye on the extradite\n"
        "Abbott would not send the agent back\n"
        "Minnesota charged a shooting and a lie\n"
        "A governor as a shelter\n"
        "Your federalism is a hiding place"
    ),
    verses=(
        "August twenty-twenty-six, a suit from Minnesota\n"
        "An ICE officer accused of wounding a man\n"
        "Abbott declined the hold request\n"
        "Keep the agent, skip the trial\n"
        "Nill Bye filing the extradite\n"
        "UK-garage shuffle on a custody fight\n"
        "You preach law and order until the badge is yours\n"
        "Then the order becomes a shield\n"
        "A shooting in another state is still a shooting\n"
        "A lie in a report is still a lie\n"
        "You made Texas a dock for a federal gun\n"
        "And called it sovereignty",
        "The AG in Minnesota asked a judge to compel\n"
        "Because asking you politely had failed\n"
        "Abbott likes a compact when it buses people out\n"
        "Not when it sends a shooter back\n"
        "Nill Bye mad at a two-way federalism\n"
        "Export the buses, import the impunity\n"
        "A shuffled garage on a double standard\n"
        "You cannot brag the rule of statutes\n"
        "And then sit on the warrant\n"
        "A hold is a courtesy among states\n"
        "You spent it on a faction\n"
        "The organ stab is the tell",
        "Minneapolis crackdown, a man wounded\n"
        "The report allegedly cleaned the facts\n"
        "Abbott heard ICE and stopped hearing the victim\n"
        "A letterhead as a hiding place\n"
        "Nill Bye reading the complaint\n"
        "Extradition is not a vibe\n"
        "It is a statute you like when it hunts the other direction\n"
        "Here the direction was inconvenient\n"
        "So the request went to a file\n"
        "And the agent stayed in the friendly state\n"
        "That is not comity\n"
        "That is a club with a star on the door",
        "Shuffled hats, sub under a standoff\n"
        "Two states, one badge, zero spine from Austin\n"
        "Nill Bye posting the hold request\n"
        "Abbott still sure a federal agent is above a state charge\n"
        "If the charge is real, send him\n"
        "If the charge is not, beat it in court\n"
        "Hiding is a third option for the guilty-adjacent\n"
        "I want a trial, you want a dock\n"
        "Keep the shuffle, lose the shelter\n"
        "Minnesota should not have to sue a governor\n"
        "To knock on a door\n"
        "Your federalism only opens one way",
    ),
    outro="hats hush\ndock full\ncut",
)

SHARIA_PLANK_LYRICS = format_diss_lyrics(
    intro="reverse bass\nkick split\nNill Bye hearing",
    chorus=(
        "Sharia plank\n"
        "Nill Bye on the Dallas mic\n"
        "Abbott vowed a ban in a convention hall\n"
        "A scare looking for a neighbor\n"
        "Texas code already runs the courts\n"
        "Your hardstyle is a smear"
    ),
    verses=(
        "September ten, twenty-twenty-six, RNC in Dallas\n"
        "Midterm convention, a friendly chamber\n"
        "Abbott vowed to ban Sharia Law in Texas\n"
        "As if a neighbor's faith were on the ballot\n"
        "Nill Bye hearing the plank\n"
        "The Constitution already does that job\n"
        "You don't need a new ban to keep Texas code\n"
        "You need a crowd that wants a villain\n"
        "Hardstyle kick on a ghost threat\n"
        "A reverse bass under a phantom code\n"
        "Texas courts already apply Texas code\n"
        "Your plank is a scare looking for a section",
        "Same night: common sense versus crazy\n"
        "A buffet of villains, one mic, one grin\n"
        "Abbott stacked land, elections, energy, fear\n"
        "A chamber that cheers a word more than a memo\n"
        "Nill Bye mad at a plank with no case file\n"
        "Show the court where that word entered a judgment\n"
        "Not a chapel, not a basin, a holding\n"
        "You brought a feeling and asked for a statute\n"
        "A screech lead on a hollow memo\n"
        "A split kick on a sentence that needs no partner\n"
        "Banning what is not in force is theater\n"
        "Theater that points at a neighbor",
        "Muslim Texans already live under the code you run\n"
        "Taxes, traffic, contracts, the same penal title\n"
        "Abbott still needed a scare-word for the chamber\n"
        "Because keeping Texas code does not cheer\n"
        "Nill Bye filing the Sharia plank\n"
        "A hardstyle drop on a nothing-burger with a target\n"
        "You chose a neighbor as the villain slot\n"
        "You chose the smear because the chamber is easier than a memo\n"
        "A vow is cheap when the thing is already void\n"
        "So the vow is not about the thing\n"
        "It is about who hears their name in the villain slot\n"
        "The kick already picked the target",
        "Convention lights, a governor as a headliner\n"
        "Keep Texas red, help the national ticket\n"
        "Nill Bye posting the Dallas mic\n"
        "Abbott still sure a slogan is a legal reform\n"
        "Reform would name a case, a clause, a harm\n"
        "You named a word and a mood\n"
        "I want a statute that does labor\n"
        "You want a plank that does a crowd\n"
        "Keep the reverse bass, print the empty cite\n"
        "Sharia is not on the docket\n"
        "Your fear is\n"
        "The hall applauded the fear",
    ),
    outro="kick rest\nplank hollow\ncut\nyeah",
)

INVASION_HYMN_LYRICS = format_diss_lyrics(
    intro="gated pads\nrolling bass\nNill Bye arranging",
    chorus=(
        "Invasion hymn\n"
        "Nill Bye on the rhetoric\n"
        "Abbott sings a war into a crossing\n"
        "Peak years used as a forever verse\n"
        "A word stretched to fund a force\n"
        "Your trance is a recruitment tape"
    ),
    verses=(
        "Invasion is a word with a legal weight\n"
        "He hung it on a migration flow\n"
        "Abbott needed a hymn that licenses force\n"
        "So a crossing became a campaign of occupation\n"
        "Nill Bye arranging the gated pads\n"
        "When the numbers peaked, the word was a megaphone\n"
        "When the numbers fell, the word stayed\n"
        "A trance that cannot find the down button\n"
        "You upgraded a headline into a wartime presser\n"
        "A noun upgraded so the stamp could widen\n"
        "Rhetoric is a force multiplier\n"
        "It multiplies troopers, not facts",
        "Lifted key, ugly lyric\n"
        "Hands in the air for a phantom occupier\n"
        "Abbott still conducting the invasion hymn\n"
        "After the peak, after the White House flip\n"
        "Nill Bye mad at a song that cannot end\n"
        "Because ending would end the appropriation\n"
        "A hymn with no final cadence is a tool\n"
        "Not a description\n"
        "You don't demobilize a feeling\n"
        "You demobilize a unit\n"
        "The feeling is cheaper to keep\n"
        "So the pads keep lifting a false war",
        "People at a river are not an army\n"
        "You stacked the claim until it funded itself\n"
        "Abbott talks denial of smugglers as if the hymn did it\n"
        "HRW said the aim failed and the harms did not\n"
        "Nill Bye filing the rhetoric\n"
        "A rolling bass under a stretched word\n"
        "War language gets you Guard, wire, buoys, buses\n"
        "Census language gets you process\n"
        "You picked war\n"
        "Then you picked it again every month\n"
        "A pickup fill into a drop that never resolves\n"
        "Because resolution is a budget cut",
        "Trance wants a lift. You want a forever lift\n"
        "Hands up for a crisis that prints\n"
        "Nill Bye posting the invasion hymn\n"
        "Abbott still sure a noun can be a mission\n"
        "A noun is not a mission\n"
        "A crossing is not an occupation\n"
        "I want a fact, you want a choir\n"
        "I want a peak acknowledged as a peak\n"
        "Keep the pads, lose the war-paint\n"
        "The hymn already told on the spend\n"
        "It was never about a map of armies\n"
        "It was about a map of appropriations",
    ),
    outro="pads fade\nhymn holds\ncut",
)

DEMOLISH_HOOK_LYRICS = format_diss_lyrics(
    intro="festival 808\ncrowd-bed\nNill Bye sampling",
    chorus=(
        "Demolish hook\n"
        "Nill Bye on the convention closer\n"
        "Abbott said demolish the Democrats\n"
        "Common sense versus crazy as a binary\n"
        "A headliner who cannot share a state\n"
        "Your festival is a wrecking bar"
    ),
    verses=(
        "Dallas, lights, a midterm chamber\n"
        "Keep Texas red, help the national ticket stay up\n"
        "Abbott reached for demolish\n"
        "Not defeat, not debate, demolish\n"
        "Nill Bye sampling the closer\n"
        "A festival-trap 808 under a wrecking bar\n"
        "You don't demolish a party in a republic\n"
        "You beat it and still owe it a government\n"
        "The hook is the tell: opposition as rubble\n"
        "Crazy as the only other option\n"
        "A binary that flatters the chamber\n"
        "And insults the half that isn't in it",
        "Common sense versus crazy is a children's slogan\n"
        "Adults have tradeoffs, numbers, wards, grids\n"
        "Abbott skipped the tradeoffs for a chant\n"
        "Demolish is easier than a levy cut that sticks\n"
        "Nill Bye mad at a closer that wants rubble\n"
        "A state is not a demo site\n"
        "Hinojosa is not debris\n"
        "A voter who splits a ticket is not crazy\n"
        "You ran the hook because the dossier is heavy\n"
        "Wards, wire, clocks, maps, raids, stamps\n"
        "A wrecking bar is lighter than a record\n"
        "So you picked the bar",
        "Crowd-bed, pyro in the adjectives\n"
        "A mainstage grin on a wrecking bar\n"
        "Abbott still mouthing demolish\n"
        "As if a verb could be a platform\n"
        "Nill Bye filing the convention closer\n"
        "A national slogan leaning on a state job\n"
        "You have a state to run\n"
        "Running it is the opposite of demolish\n"
        "A headliner can chant wreckage\n"
        "A governor has to keep the lights and the ward\n"
        "The 808 does not mind the contradiction\n"
        "The dossier does",
        "Festival trap as a last take\n"
        "A closer that wants rubble more than a roll-call\n"
        "Nill Bye posting the demolish hook\n"
        "Abbott still sure the hall is the state\n"
        "The chamber is a box\n"
        "The state has the people you want in rubble\n"
        "I want a contest, you want a demolition\n"
        "I want a record, you want a chant\n"
        "Keep the 808, print the verb\n"
        "Demolish is not governance\n"
        "It is a hook\n"
        "And it already told on you",
    ),
    outro="808 stop\nhook rings\ncut\nyeah",
)

DISS_CIVIC_CLUB: tuple[DissExample, ...] = (
    _ex(
        "lone-star-tab",
        "lone star tab",
        140,
        271,
        "lone-star-tab roast of Abbott",
        LONE_STAR_TAB_LYRICS,
        "dark trap",
        "808 bass",
        "rapid hi-hats",
        "half-time",
    ),
    _ex(
        "river-buoy",
        "river buoy",
        148,
        277,
        "river-buoy roast of Abbott",
        RIVER_BUOY_LYRICS,
        "rage",
        "distorted 808",
        "laser hats",
    ),
    _ex(
        "bus-receipt",
        "bus receipt",
        132,
        281,
        "bus-receipt roast of Abbott",
        BUS_RECEIPT_LYRICS,
        "phonk",
        "cowbell",
        "drifted 808",
        "crunchy sample",
    ),
    _ex(
        "guard-detail",
        "guard detail",
        145,
        283,
        "guard-detail roast of Abbott",
        GUARD_DETAIL_LYRICS,
        "trap",
        "808 bass",
        "rapid hats",
        "dark pads",
    ),
    _ex(
        "chase-wreck",
        "chase wreck",
        126,
        293,
        "chase-wreck roast of Abbott",
        CHASE_WRECK_LYRICS,
        "house",
        "four-on-the-floor",
        "piano stab",
        "sidechain bass",
    ),
    _ex(
        "frequency-drop",
        "frequency drop",
        174,
        307,
        "frequency-drop roast of Abbott",
        FREQUENCY_DROP_LYRICS,
        "drum and bass",
        "amen break",
        "sub reese",
    ),
    _ex(
        "permitless",
        "permitless",
        140,
        311,
        "permitless roast of Abbott",
        PERMITLESS_LYRICS,
        "jersey club",
        "chopped percussion",
        "bed squeaks",
        "kick drums",
    ),
    _ex(
        "trigger-clock",
        "trigger clock",
        148,
        313,
        "trigger-clock roast of Abbott",
        TRIGGER_CLOCK_LYRICS,
        "future bass",
        "supersaw",
        "pitched synth chords",
        "808 bass",
    ),
    _ex(
        "disaster-stamp",
        "disaster stamp",
        132,
        317,
        "disaster-stamp roast of Abbott",
        DISASTER_STAMP_LYRICS,
        "techno",
        "dry kick",
        "hat offbeats",
        "acid line",
    ),
    _ex(
        "windmill-blame",
        "windmill blame",
        140,
        331,
        "windmill-blame roast of Abbott",
        WINDMILL_BLAME_LYRICS,
        "dubstep",
        "wobble bass",
        "half-time snare",
    ),
    _ex(
        "yass-primary",
        "yass primary",
        128,
        337,
        "yass-primary roast of Abbott",
        YASS_PRIMARY_LYRICS,
        "electro house",
        "analog bass",
        "clap on 2 and 4",
    ),
    _ex(
        "hold-request",
        "hold request",
        130,
        347,
        "hold-request roast of Abbott",
        HOLD_REQUEST_LYRICS,
        "UK garage",
        "shuffled hats",
        "organ stab",
        "sub bass",
    ),
    _ex(
        "sharia-plank",
        "sharia plank",
        150,
        349,
        "sharia-plank roast of Abbott",
        SHARIA_PLANK_LYRICS,
        "hardstyle",
        "reverse bass",
        "screech lead",
    ),
    _ex(
        "invasion-hymn",
        "invasion hymn",
        138,
        353,
        "invasion-hymn roast of Abbott",
        INVASION_HYMN_LYRICS,
        "trance",
        "gated pads",
        "rolling bass",
        "pickup drum fill",
    ),
    _ex(
        "demolish-hook",
        "demolish hook",
        150,
        359,
        "demolish-hook roast of Abbott",
        DEMOLISH_HOOK_LYRICS,
        "festival trap",
        "808 bass",
        "crowd-bed",
    ),
)










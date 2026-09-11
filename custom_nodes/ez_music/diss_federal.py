"""Federal-pack 180s Nill Bye diss takes (non-trap, non-EDM beds).

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

FEDERAL_PHASE = 5


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
        "series": "federal",
        "title": title,
        "tags": nill_tags(*tag_parts, bpm=bpm),
        "bpm": bpm,
        "duration": DISS_DURATION_S,
        "seed": seed,
        "phase": FEDERAL_PHASE,
        "prefix": nill_output_prefix(title, FEDERAL_PHASE),
        "description": _desc(take),
        "lyrics": lyrics,
    }


THIRTY_FOUR_COUNTS_LYRICS = format_diss_lyrics(
    intro="yeah\nledger open\nNill Bye counting felonies",
    chorus=(
        "Thirty four counts\n"
        "Nill Bye on the reimbursement\n"
        "Trump labeled a legal fee\n"
        "A jury labeled thirty-four felonies\n"
        "Discharge is not an acquittal\n"
        "Your records failed the catch-and-kill"
    ),
    verses=(
        "May thirty, twenty-twenty-four\n"
        "Manhattan found every count, felonies\n"
        "One hundred thirty thousand hush, merchan\n"
        "Wired so a story stayed buried\n"
        "Trump repaid it as a retainer\n"
        "The stubs said legal, the purpose didn't\n"
        "Nill Bye opening the reimbursement\n"
        "Cohen was the pass-through, not a firm\n"
        "Pecker bagged the National Enquirer lane\n"
        "Catch-and-kill as a campaign tool, enquirer\n"
        "First former president with a felony sheet, pecker\n"
        "The verdict sheet did not stutter",
        "Thirty-four identical false entries\n"
        "A pattern, not a clerical oops\n"
        "Trump needed the 2016 news quiet\n"
        "So the books learned a second language\n"
        "Nill Bye tracing the stub to the motive\n"
        "Election influence dressed as payroll\n"
        "Merchan kept the courtroom from a rally\n"
        "You treated the bench like a bleacher\n"
        "A gag order is not persecution\n"
        "It is a ruler for a loud defendant\n"
        "The jury sat through the whole method, stubs\n"
        "Then they filled every box the same",
        "January ten, twenty-twenty-five\n"
        "Unconditional discharge ten days out\n"
        "Trump called it proof he won the case\n"
        "Merchan called it the only sentence left\n"
        "Nill Bye reading the discharge as a comma\n"
        "The presidency ducked the penalty\n"
        "It did not erase the thirty-four felonies\n"
        "A comma is not a retraction\n"
        "You ran on the silence you bought\n"
        "Then you ran on the verdict as a trophy-claim, felonies\n"
        "I score the entries, you score the rally\n"
        "The ledger still has thirty-four ticks",
        "Science guy with a scarlet marker\n"
        "A reimbursement is a data trail\n"
        "Trump still selling innocence as a brand, merchan\n"
        "The brand cannot un-check a box\n"
        "Nill Bye posting the thirty four counts\n"
        "Catch-and-kill is a method, not a vibe, enquirer\n"
        "You hid a story from a ballot\n"
        "Then you hid the payment from a ledger\n"
        "Two hides, one motive, thirty-four boxes\n"
        "A discharge is a courtesy of the office\n"
        "Bring a reversal, not a rally chant\n"
        "The counts already did the talking",
    ),
    outro="stubs close\nfelonies stay\ncut\nyeah",
)

ONE_EIGHTY_SEVEN_LYRICS = format_diss_lyrics(
    spoken=(
        "One ten p.m. Ellipse\n"
        "Four seventeen the video\n"
        "One hundred eighty-seven minutes\n"
        "Dining room, Fox on\n"
        "Dereliction"
    ),
    intro="stopwatch click\nNill Bye stopwatching the Ellipse",
    chorus=(
        "One eighty seven\n"
        "Nill Bye on the idle minutes\n"
        "Trump watched the breach on cable\n"
        "Then praised the crowd as very special\n"
        "A president is a switch, not a spectator\n"
        "Your dining room failed the Capitol"
    ),
    verses=(
        "One ten, the Ellipse speech closed, ellipse\n"
        "March to the Capitol was the last cue\n"
        "Trump wanted a motorcade into the riot\n"
        "Secret Service boxed the tantrum in the car\n"
        "Nill Bye timing the idle minutes\n"
        "One twenty-five, a dining-room head-of-table, cipollone\n"
        "Fox as the only brief in the room, stopwatch\n"
        "Photographer told to bag the camera\n"
        "Cipollone said say it now, leave\n"
        "You could not be moved, the committee said\n"
        "Officers took the beating in the meantime\n"
        "The switch stayed off on purpose",
        "Pence was the named target in the chant\n"
        "You had the one voice the mob would hear\n"
        "Trump sat through the smash and the crush\n"
        "Aides, family, allies texting Meadows\n"
        "Nill Bye mad at a spectator presidency\n"
        "The only person who could call it off\n"
        "Waited until four seventeen for a clip, dereliction\n"
        "Then mixed go-home with you are special\n"
        "A script said peaceful. You skipped the word\n"
        "You kept the steal in the same breath\n"
        "That is not confusion, that is a choice\n"
        "The stopwatch already filed it",
        "One hundred eighty-seven is a measurement\n"
        "Not a mood, not a vibe, a duration\n"
        "Trump later called it a loving afternoon\n"
        "The officers called it a war zone\n"
        "Nill Bye keeping the committee clock, ellipse\n"
        "Cheney named it supreme dereliction\n"
        "Thompson said something is wrong with that wait\n"
        "A dining room is not a command post\n"
        "Cable is not an intelligence brief\n"
        "Special is not an order to disperse\n"
        "You praised the people who broke the glass\n"
        "Then you ran on their mugshots as saints",
        "Twenty-twenty-five you called them hostages\n"
        "The minutes did not get shorter with the brand, cipollone\n"
        "Trump still selling a tourist afternoon\n"
        "The tape is the officers, not the merch\n"
        "Nill Bye posting the one eighty seven\n"
        "A stopwatch does not take a side\n"
        "I want a switch flipped at one eleven\n"
        "You wanted a show from a dining chair, stopwatch\n"
        "Keep the boom-bap, print the duration\n"
        "One ten to four seventeen is the whole thesis\n"
        "Very special is a tell, not a pardon of physics\n"
        "The Capitol already knew the idle minutes",
    ),
    outro="stopwatch rest\nminutes stand\ncut",
)

ELEVEN_SEVEN_EIGHTY_LYRICS = format_diss_lyrics(
    intro="tape hiss\nNill Bye transcribing",
    chorus=(
        "Eleven seven eighty\n"
        "Nill Bye on the Georgia tape\n"
        "Trump asked to find a margin-plus-one\n"
        "Raffensperger kept the certified math\n"
        "Three counts, same winner, one ask\n"
        "Your find was a demand, not an audit"
    ),
    verses=(
        "January two, a Saturday pressure-call, raffensperger\n"
        "Brad Raffensperger, fellow Republican\n"
        "Trump wanted eleven thousand seven hundred eighty\n"
        "One more than the eleven thousand seven hundred seventy-nine\n"
        "Nill Bye transcribing the Georgia tape\n"
        "The state had counted, audited, recounted\n"
        "Biden's margin did not move for a threat\n"
        "You offered a criminal overlay if they refused\n"
        "Dead voters at five thousand, they found two\n"
        "The data you have is wrong, he said\n"
        "You said recalculate. He said stand by the numbers\n"
        "A secretary of state is not a vending slot, canvass",
        "Jazz hop brushes on a recorded hour\n"
        "Muted trumpet under a demand dressed as math, remainder\n"
        "Trump treated a certified result as a suggestion\n"
        "Find is a verb with a destination built in\n"
        "Nill Bye mad at a hunt for uncast ballots\n"
        "You do not find votes the way you find a sock\n"
        "You count them, then you live with the total\n"
        "Meadows asked for compromise on a certified sheet, raffensperger\n"
        "Compromise is for a bill, not a tally\n"
        "Georgia already ran the machine and the hand\n"
        "Three methods, one winner, zero magic remainder\n"
        "The tape is the exhibit, not a gossip mill",
        "Fulton theories, suitcase lore, scanned-thrice myths\n"
        "Each one died in the same conversation\n"
        "Trump kept stacking debunked clips as if volume were proof\n"
        "Raffensperger kept answering with the actual canvass\n"
        "Nill Bye filing the margin-plus-one ask\n"
        "One more than you lost by is not a coincidence\n"
        "It is the tell that the number was the goal\n"
        "Accuracy was the costume, canvass\n"
        "A Republican official still said no\n"
        "That no is the whole civic method, remainder\n"
        "You wanted a colleague to break his own count, raffensperger\n"
        "He declined, and the tape kept running",
        "Years on, you still tour the same remainder\n"
        "As if a recording were a rumor you could out-shout\n"
        "Trump still sure Georgia hid a sock-drawer of ballots\n"
        "The drawer was a certified canvass\n"
        "Nill Bye posting the eleven seven eighty\n"
        "A find-request is a pressure campaign\n"
        "I want a tally, you want a remainder that fits\n"
        "Keep the brushes, print the ask\n"
        "Eleven thousand seven hundred eighty is not an audit finding\n"
        "It is a shopping list, canvass\n"
        "The tape already priced the errand, remainder\n"
        "Raffensperger already closed the register",
    ),
    outro="tape stop\nmargin holds\ncut\nyeah",
)

FAKE_ELECTORS_LYRICS = format_diss_lyrics(
    intro="metal hit\nNill Bye reading slates",
    chorus=(
        "Fake electors\n"
        "Nill Bye on the seven slates\n"
        "Trump needed a paper Biden did not win\n"
        "So a memo tried to mint a second college\n"
        "Eastman wrote the obvious illegal\n"
        "Your ascertainment was a costume ballot"
    ),
    verses=(
        "Arizona, Georgia, Michigan, Nevada\n"
        "New Mexico, Pennsylvania, Wisconsin\n"
        "Trump lost the certified electors in all seven\n"
        "So a parallel slate signed a fiction\n"
        "Nill Bye reading the seven slates\n"
        "Chesebro sketched the expansion after the first memo, ascertainment\n"
        "Giuliani ran the phone tree like a field office\n"
        "Wilenchik wrote fake in quotes and sent it anyway\n"
        "Pence was supposed to treat the fiction as a fork\n"
        "The Electoral Count Act does not sell forks\n"
        "Judge Carter called the illegality obvious\n"
        "Obvious is a holding, not an insult",
        "Industrial percussion on a forged college\n"
        "Distorted bass under a costume ballot\n"
        "Trump was briefed that the Pence card was a violation\n"
        "He still walked Eastman into the room, chesebro\n"
        "Nill Bye mad at a second college as a prop\n"
        "Dec fourteen the real electors met at noon\n"
        "Your extras met in a different hallway\n"
        "Same date, opposite authority\n"
        "A certificate of ascertainment is a governor's act, wilenchik\n"
        "You tried to photocopy the seal with a Sharpie energy\n"
        "Ronna was asked to staff the extras\n"
        "A party chair is not a printer for electors",
        "April twenty-twenty-six, California closed the file, ascertainment\n"
        "Eastman disbarred for the false statements and the scheme\n"
        "Trump still touring the memo as a theory\n"
        "A disbarment is a profession voting no\n"
        "Nill Bye filing the architect's sanction\n"
        "Patently false in court papers is not a vibe, chesebro\n"
        "It is a finding with a five-thousand sanction beside it\n"
        "Seven states is a conspiracy of paperwork\n"
        "Not a grassroots mix-up\n"
        "You needed Pence to launder the extras on January six\n"
        "He would not, so the extras died as exhibits\n"
        "The exhibits did not die as evidence",
        "A college is a count, not a costume shop\n"
        "You opened a second shop and called it law, wilenchik\n"
        "Trump still sure a memo can mint a win\n"
        "A memo cannot mint a slate the governor did not sign\n"
        "Nill Bye posting the fake electors\n"
        "I want a certificate, you want a photocopy\n"
        "Keep the metal, print the seven names\n"
        "Eastman paid a license, you kept the theory\n"
        "The Pence card was never in the deck\n"
        "It was a sticky note on a statute you disliked\n"
        "Bring a governor's seal or sit down, ascertainment\n"
        "The extras already told on the errand, chesebro",
    ),
    outro="slates fold\ncollege stands\ncut",
)

BATHROOM_BOXES_LYRICS = format_diss_lyrics(
    intro="brass sting\nNill Bye inventorying",
    chorus=(
        "Bathroom boxes\n"
        "Nill Bye on the Mar-a-Lago stacks\n"
        "Trump stored classifieds by a toilet\n"
        "A ballroom closet is not a SCIF\n"
        "The photo is the inventory\n"
        "Your storage failed the classification"
    ),
    verses=(
        "Boxes in a bath, boxes on a stage, maralago\n"
        "A chandelier over a classified pile\n"
        "Trump treated a club as a file room, sf312\n"
        "NARA asked, the club slow-walked\n"
        "Nill Bye inventorying the Mar-a-Lago stacks\n"
        "A SCIF has a door, a lock, a method, chandelier\n"
        "A toilet has none of those on purpose\n"
        "The FBI found what the subpoena already named\n"
        "Empty folders with classified banners still on them\n"
        "A banner is not a souvenir\n"
        "It is a handling instruction you ignored\n"
        "The photo did the cataloging for you",
        "Brass band snare on a closet inventory\n"
        "Tuba under a chandelier that never signed an SF-312\n"
        "Trump said I declassified with my mind\n"
        "A mind is not a marking, a log, or a courier\n"
        "Nill Bye mad at telepathy as a records act, maralago\n"
        "The Espionage Act cares about possession and storage\n"
        "Not about a feeling you had on a fairway\n"
        "Later dockets moved, later charges shifted\n"
        "The boxes did not become a spa display\n"
        "A dropped case is not a clean closet\n"
        "The inventory still sits in the photograph\n"
        "You cannot un-stack a picture",
        "Mar-a-Lago is a club that sells memberships\n"
        "Members walk halls. Staff walk halls. Cameras walk halls\n"
        "Trump stored the country's paper in a traffic pattern\n"
        "That is the opposite of need-to-know\n"
        "Nill Bye filing the bathroom as a storage site\n"
        "A ballroom is for dancing, not for compartments\n"
        "You mixed the two and called it a library\n"
        "Libraries have catalogs. You had piles\n"
        "The subpoena named documents. The bath produced boxes\n"
        "A mismatch that large is a method, sf312\n"
        "Not a packing error on moving day\n"
        "Moving day does not last two years",
        "Keep the tuba, print the chandelier shot, chandelier\n"
        "A classified banner in a bathroom is the whole joke\n"
        "Trump still selling mind-powers as a records policy, maralago\n"
        "The policy is a lock, a log, a courier, a SCIF\n"
        "Nill Bye posting the bathroom boxes\n"
        "I want a compartment, you want a closet\n"
        "I want a marking, you want a vibe, sf312\n"
        "The photo already picked a side\n"
        "Storage is the offense the picture proves\n"
        "Later lawyering cannot redecorate the tile\n"
        "Bring a SCIF, lose the toilet\n"
        "The stacks already told on the club",
    ),
    outro="tuba mute\nboxes stay\ncut\nyeah",
)

STATEMENT_OF_WORTH_LYRICS = format_diss_lyrics(
    intro="folk scrape\nNill Bye tape-measuring",
    chorus=(
        "Statement of worth\n"
        "Nill Bye on the inflated SFSs\n"
        "Trump sold a number banks could price\n"
        "Engoron found the number was a costume\n"
        "A tossed fine is not a tossed finding\n"
        "Your penthouse gained a phantom floor"
    ),
    verses=(
        "A statement of financial condition is a tool, engoron\n"
        "Banks and insurers price the person from the tool, triplex\n"
        "Trump's tool grew penthouses, clubs, and air\n"
        "Triplex square-footage that a tape would not love\n"
        "Nill Bye appraising the inflated SFSs\n"
        "Engoron sat through the three-month bench trial, disgorgement\n"
        "The ill-gotten savings had a dollar figure\n"
        "Three hundred fifty-four million and change at first blush\n"
        "Interest made it uglier while the appeal slept\n"
        "Then August twenty-twenty-five, a panel called the fine excessive\n"
        "Eighth Amendment on the disgorgement, split on the merits\n"
        "Excessive is a size complaint, not a blessing of the books",
        "Folk guitar on a phantom floor, engoron\n"
        "Room mic on a square-foot that never existed\n"
        "Trump blamed accountants, then praised the same books\n"
        "A defendant cannot be the author and the bystander\n"
        "Nill Bye mad at a costume net-worth\n"
        "Mar-a-Lago as a palace on paper, a club in fact, triplex\n"
        "Golf courses priced like they had never met weather, disgorgement\n"
        "The Old Post Office lease rode the same costume, engoron\n"
        "You do not get cheaper money for a fiction\n"
        "And then keep the fiction when the tape comes out\n"
        "A gag order followed the courtroom mouth\n"
        "The books were the exhibit, the mouth was the encore",
        "James brought the case as a consumer protection\n"
        "You brought a rally as a defense exhibit\n"
        "Trump still touring the tossed penalty as innocence\n"
        "A vacated dollar is not a vacated appraisal\n"
        "Nill Bye filing the difference with a scarlet marker\n"
        "The panel said the fine was too big\n"
        "It did not say the penthouse grew an extra floor in reality\n"
        "Size of remedy and truth of statement are different axes\n"
        "You collapsed them because the collapse is useful\n"
        "Useful is not the same as accurate\n"
        "I want the square-footage, you want the headline, triplex\n"
        "The tape already walked the triplex",
        "Keep the fiddle, print the phantom floor, disgorgement\n"
        "A statement of worth is a representation\n"
        "Trump still sure a tossed fine un-inflates a club\n"
        "Un-inflate is a verb the building cannot do\n"
        "Nill Bye posting the statement of worth\n"
        "Bring a tape measure, lose the costume, engoron\n"
        "Banks priced the costume. That was the harm\n"
        "A later size-check on the remedy is not a blessing\n"
        "The finding was the inflation\n"
        "The fight was the dollar\n"
        "You won a size argument and sold it as a baptism\n"
        "The penthouse still has the floors it has",
    ),
    outro="folk strings rest\nappraisal holds\ncut",
)

UNIVERSITY_TAB_LYRICS = format_diss_lyrics(
    intro="steel guitar\nNill Bye totaling tuition",
    chorus=(
        "University tab\n"
        "Nill Bye on the twenty-five million\n"
        "Trump sold a last name as a faculty\n"
        "Instructors he did not pick taught the pitch\n"
        "A settlement is a refund with a calendar\n"
        "Your seminar failed the students"
    ),
    verses=(
        "Up to thirty-five thousand for a mentorship\n"
        "Three-day tickets in the fifteen-hundred lane\n"
        "Trump's name on the banner, not in the classroom\n"
        "Depositions said he did not choose the instructors\n"
        "Nill Bye totaling the twenty-five million\n"
        "High-pressure upsells after the free taste\n"
        "A university that was a seminar with a trademark\n"
        "Schneiderman stacked the New York piece beside the class\n"
        "Curiel had a jury date ten days from the deal\n"
        "You settled so the oath would not share a week with a stand\n"
        "A president-elect does not like a witness chair, curiel\n"
        "The students liked a refund more than a cameo",
        "Country train-beat on a sold last name\n"
        "Fiddle under a faculty that never met the dean\n"
        "Trump mocked businessmen who settle, then settled\n"
        "The mock is the tell when the check follows\n"
        "Nill Bye mad at a trademark dressed as a campus\n"
        "Hand-picked was the ad. Unpicked was the deposition\n"
        "Those two sentences cannot share a catalog\n"
        "Restitution around half the fees for the class\n"
        "A million in penalties to New York on the education law, schneiderman\n"
        "You called it a university. The state called it a violation\n"
        "Sell, sell, sell was the instructor's job description\n"
        "A job description is a method, not a vibe, mentorship",
        "March twenty-seventeen, final approval landed\n"
        "The refunds moved. The trademark did not become a campus\n"
        "Trump still selling the deal as a nuisance tax\n"
        "Twenty-five million is a large nuisance if it is only noise\n"
        "Nill Bye filing the university tab, curiel\n"
        "A last name is not a syllabus\n"
        "A syllabus is not a pressure room, schneiderman\n"
        "You stacked all three and cashed the confusion\n"
        "Students paid for Trump. They got a closer\n"
        "That delta is the whole consumer case\n"
        "Bring a faculty, lose the upsell\n"
        "The settlement already priced the delta",
        "Keep the steel, print the twenty-five million\n"
        "A seminar can be honest. This one sold a ghost dean\n"
        "Trump still sure a trademark teaches real estate\n"
        "A trademark teaches recognition, not a deal\n"
        "Nill Bye posting the seminar refund\n"
        "I want a syllabus, you want a closer\n"
        "I want a pick, you want a poster\n"
        "The deposition already picked a side\n"
        "Hand-picked died on the record, mentorship\n"
        "The refund is the aftertaste\n"
        "Keep the fiddle, lose the campus costume, curiel\n"
        "The students already sat the course",
    ),
    outro="steel rest\nrefunds move\ncut\nyeah",
)

UKRAINE_HOLD_LYRICS = format_diss_lyrics(
    intro="blues harp bite\nNill Bye tracing aid",
    chorus=(
        "Ukraine hold\n"
        "Nill Bye on the frozen assistance\n"
        "Trump wanted a personal errand for a pause\n"
        "Sondland said the hold had a why\n"
        "The House wrote articles. The Senate sat on them\n"
        "Your freeze was a quid, not a review"
    ),
    verses=(
        "Three hundred ninety-one million in security assistance\n"
        "Voted, appropriated, then paused in the pipeline\n"
        "Trump wanted a public Ukraine statement on a rival\n"
        "The pause sat on the money until the press got loud, sondland\n"
        "Nill Bye tracing the frozen assistance\n"
        "A president can review a flow. He cannot pawn it\n"
        "Sondland told the committees the why was the ask\n"
        "The ask was dirt, the pawn was Javelins and support\n"
        "Ambassadors shuffled. A memo became a talking point, javelins\n"
        "The perfect call was imperfect on arrival\n"
        "A transcript is not a blessing\n"
        "It is a record of the errand, assistance",
        "Blues shuffle on a paused appropriation\n"
        "Guitar sting under a personal errand in a war budget\n"
        "Trump treated a partner as a campaign research desk, sondland\n"
        "Aid is not a retainer for a smear\n"
        "Nill Bye mad at a freeze with a why\n"
        "The House impeached. That is a constitutional instrument\n"
        "The Senate acquitted. That is a vote, not a lab result\n"
        "Acquittal is not a finding that the pause was a review\n"
        "It is a finding that two-thirds would not remove\n"
        "Those are different machines\n"
        "You sold the second as if it un-paused the first, javelins\n"
        "The money had already learned the errand, assistance",
        "A rival's name in a security pipeline is the tell, sondland\n"
        "Reviews do not need a presser from Kyiv\n"
        "Trump still touring the perfect-call brand, javelins\n"
        "Perfect is a marketing word for a messy transcript\n"
        "Nill Bye filing the Ukraine hold\n"
        "Quid pro quo is Latin for the why Sondland named\n"
        "You can dislike the Latin. You cannot dislike the pause, assistance\n"
        "The pause is in the OMB paper and the calendar\n"
        "The articles are in the Congressional Record, sondland\n"
        "I want an appropriation that arrives\n"
        "You wanted a statement that campaigns\n"
        "Those wants do not share a national-security file, javelins",
        "Keep the harmonica, print the three-ninety-one\n"
        "A freeze is a lever. You put a rival on the lever\n"
        "Trump still sure an acquittal un-asks the ask\n"
        "An acquittal un-removes a person, not an errand, assistance\n"
        "Nill Bye posting the Ukraine hold\n"
        "Bring a review memo that never names a rival\n"
        "Lose the pawn-shop in a security pipeline\n"
        "The House already wrote the instrument\n"
        "The Senate already sat\n"
        "The money already waited\n"
        "Waiting was the policy, sondland\n"
        "The errand was the why",
    ),
    outro="harmonica rest\naid unpaused\ncut",
)

TRAVEL_MEMO_LYRICS = format_diss_lyrics(
    intro="lo-fi rhodes\nNill Bye reading the roster",
    chorus=(
        "Travel memo\n"
        "Nill Bye on the seven-country list\n"
        "Trump signed a blunt entry freeze\n"
        "A list is not a security method\n"
        "Courts made you revise the blunt tool\n"
        "Your ban was a headline with a roster"
    ),
    verses=(
        "January twenty-seven, twenty-seventeen\n"
        "Executive Order 13769, a seven-country roster\n"
        "Trump froze entry on a Friday and stunned the airports\n"
        "Green-card holders in the same blunt net at first, entryfreeze\n"
        "Nill Bye reading the entry freeze\n"
        "A security method names a person, a visa, a fact, rosterseven\n"
        "A roster names a map and calls the map a threat\n"
        "Airports became the implementation desk, terminals\n"
        "Lawyers slept on floors. That is a design tell, entryfreeze\n"
        "You can screen. You cannot outsource screening to a continent-color\n"
        "The blunt tool was the point of the presser, rosterseven\n"
        "Precision would not have made the same noise",
        "Lo-fi drums on a revised roster\n"
        "Vinyl crackle under a headline that needed a court\n"
        "Trump had to walk the first order into a second, then a third\n"
        "Revision is an admission dressed as a sequel\n"
        "Nill Bye mad at a list sold as a method, terminals\n"
        "Hawaii went up. Other benches went up\n"
        "The Supreme Court later blessed a narrower later version\n"
        "A later version is not a baptism of the first weekend\n"
        "The first weekend is the implementation you chose\n"
        "Chaos at a terminal is a policy output\n"
        "Not an accident of paperwork\n"
        "You wanted the noise. The noise arrived",
        "A faith is not a security file, entryfreeze\n"
        "I will not borrow your smear to roast the smear\n"
        "Trump campaigned on a total shutdown of a faith\n"
        "Then the counsel shop turned it into a country roster\n"
        "Nill Bye filing the translation as the tell, rosterseven\n"
        "If the method were vetting, the memo would vet\n"
        "The memo listed. Listing is easier than vetting\n"
        "Easier is not safer\n"
        "Safer is casework, interviews, data, appeals\n"
        "You picked a roster because a roster photographs\n"
        "A photograph is not a screen\n"
        "The terminals already knew the difference",
        "Keep the rhodes, print the seven names\n"
        "A blunt tool can be revised. The bluntness was the design\n"
        "Trump still selling the first weekend as strength\n"
        "Strength would have been a method that survived the first bench\n"
        "Nill Bye posting the travel memo, terminals\n"
        "I want a screen, you want a roster\n"
        "I want a person, you want a map, entryfreeze\n"
        "The airports already graded the implementation\n"
        "Revision is the aftertaste of a blunt tool, rosterseven\n"
        "Bring casework, lose the continent-color\n"
        "The list already told on the headline, terminals\n"
        "A headline is not a security method, entryfreeze",
    ),
    outro="rhodes fade\nroster stays\ncut\nyeah",
)

ZERO_TOLERANCE_LYRICS = format_diss_lyrics(
    intro="soft snare\nNill Bye reading memos",
    chorus=(
        "Zero tolerance\n"
        "Nill Bye on the separation memo\n"
        "Trump's shop made parenting a prosecutorial step\n"
        "Kids as a deterrent is a policy confession\n"
        "A later executive undo is not a time machine\n"
        "Your memo failed the families it used"
    ),
    verses=(
        "Spring twenty-eighteen, a prosecutorial switch\n"
        "Misdemeanor crossing charged as a rule, not a triage\n"
        "Trump's cabinet put children on a different bus\n"
        "Because the adult went to a dock\n"
        "Nill Bye reading the separation memo, oigcount\n"
        "DHS OIG later counted the chaos in the handoff\n"
        "Thousands of children, tracking that lagged the policy, reunification\n"
        "A government that cannot find the child it moved\n"
        "Has confessed the design was the shock, not the file, handoff\n"
        "Deterrence that uses a child is not border craft\n"
        "It is a lever pulled on a person who cannot vote the lever\n"
        "That is the punch-up: the lever, not the child",
        "Neo-soul keys on a prosecutorial parenting step\n"
        "Warm bass under a file that lost its own matches\n"
        "Trump said the law made him do it\n"
        "The law did not require the child on a separate bus\n"
        "Nill Bye mad at a choice sold as a statute, oigcount\n"
        "Sessions announced the zero. Nielsen inherited the mess\n"
        "A later order tried to look like mercy\n"
        "Mercy after the shock is a presser, not a method, reunification\n"
        "Reunification became a scavenger hunt with lawyers\n"
        "A scavenger hunt is not a child-welfare system\n"
        "You do not get to lose the match and keep the talking point, handoff\n"
        "The match was the minimum the state owed",
        "I will not mock a child. I will mock the memo, oigcount\n"
        "The memo treated a family as a deterrent poster\n"
        "Trump still touring toughness as if toughness were tracking\n"
        "Toughness that loses a child is incompetence with a slogan, reunification\n"
        "Nill Bye filing the zero tolerance\n"
        "A prosecutorial switch can exist without the bus split\n"
        "You added the split because the split photographs as pain\n"
        "Pain as a message is the confession\n"
        "OIG papered the tracking failure\n"
        "Paper is the opposite of a vibe, handoff\n"
        "I want a file that can find a child\n"
        "You wanted a headline that could move a poll",
        "Keep the rhodes, print the OIG count, oigcount\n"
        "A later undo does not un-ride the bus\n"
        "Trump still sure a slogan is a child-welfare plan, reunification\n"
        "A plan has matches, beds, counsel, a clock, handoff\n"
        "Nill Bye posting the zero tolerance\n"
        "Bring a match, lose the deterrent poster\n"
        "The families were not a talking point, oigcount\n"
        "They were the people the memo used\n"
        "Used is the verb. I will keep using it\n"
        "A state does not get to use a child as a lever\n"
        "The lever already told on the shop\n"
        "The OIG already counted the lost matches",
    ),
    outro="keys rest\nmatches due\ncut",
)

CENSUS_QUESTION_LYRICS = format_diss_lyrics(
    intro="8-bit blip\nNill Bye reading Commerce",
    chorus=(
        "Census question\n"
        "Nill Bye on the pretext file\n"
        "Trump's Commerce wanted a citizenship box\n"
        "The box had a Voting Rights costume\n"
        "Roberts called the reason contrived\n"
        "Your questionnaire failed the Administrative Procedure"
    ),
    verses=(
        "A census is a count, not a trapdoor\n"
        "Adding a citizenship box late is a method with a why\n"
        "Trump's Commerce, Ross at the desk, wanted the box\n"
        "The stated why was Voting Rights Act enforcement\n"
        "Nill Bye reading the pretext file, hofeller\n"
        "The record showed the VRA costume arriving after the want\n"
        "A why that arrives after the want is a pretext\n"
        "Department of Commerce v. New York, twenty-nineteen\n"
        "Roberts wrote that the explanation was contrived\n"
        "Contrived is a Supreme Court adjective, not a tweet\n"
        "The box dropped. The count went on without the trapdoor\n"
        "A dropped box is not a blessing of the costume, pretextbox",
        "Chiptune square-lead on a late questionnaire\n"
        "Eight-bit drums under a VRA costume that did not fit\n"
        "Trump wanted a question that would chill a household\n"
        "Chill is a census error with a political use\n"
        "Nill Bye mad at a count that tries to scare itself small\n"
        "Apportionment rides the count. Money rides the count, contrived\n"
        "A scared household is a theft from a city, hofeller\n"
        "You do not get to shrink a city with a box\n"
        "And then call the shrink a civil-rights tool, pretextbox\n"
        "The VRA is a sword against dilution\n"
        "You tried to borrow the sword as a scarecrow\n"
        "The Court declined to lend it",
        "Hofeller files later made the political use uglier\n"
        "A strategist's memo is not a Commerce justification\n"
        "Trump still touring the box as a common-sense ask\n"
        "Common sense would have shown up in the original record, contrived\n"
        "Nill Bye filing the census question\n"
        "APA is a boring statute until you lie to it\n"
        "Then it becomes a holding with an adjective\n"
        "Contrived is the holding, hofeller\n"
        "I want a count, you want a chill\n"
        "I want a why that exists before the want\n"
        "You wanted the want, then shopped a why\n"
        "Shopping a why is the whole case",
        "Keep the blips, print the Roberts adjective\n"
        "A questionnaire is a method. Pretext is a tell, pretextbox\n"
        "Trump still sure a box is just a question\n"
        "A question at census scale is a policy machine\n"
        "Nill Bye posting the census question\n"
        "Bring a why that predates the want\n"
        "Lose the VRA costume on a scarecrow\n"
        "The record already sequenced the want and the why\n"
        "Sequence is the science, contrived\n"
        "The Court already ran the sequence\n"
        "Contrived is the aftertaste\n"
        "The count already refused the trapdoor",
    ),
    outro="blips halt\ncount stands\ncut\nyeah",
)

PARIS_WALKOUT_LYRICS = format_diss_lyrics(
    intro="analog neon\nNill Bye reading accords",
    chorus=(
        "Paris walkout\n"
        "Nill Bye on the withdrawal letter\n"
        "Trump treated a treaty-shaped deal as a presser\n"
        "Celsius does not pause for a rally\n"
        "A later rejoin is not a time machine either\n"
        "Your walkout failed the atmosphere"
    ),
    verses=(
        "June twenty-seventeen, a Rose Garden exit speech\n"
        "Paris Agreement as a bad deal in the stump cadence\n"
        "Trump started the withdrawal clock the statute allowed\n"
        "The letter landed, the parties kept meeting without the chair, ndcpledge\n"
        "Nill Bye reading the withdrawal letter\n"
        "An accord is not a vibe. It is a nationally determined contribution\n"
        "You can argue the contribution. You cannot argue the thermometer\n"
        "Celsius kept moving while the letter sat in a tray\n"
        "A presser does not renegotiate physics\n"
        "Other parties priced the absence and moved\n"
        "Absence is also a policy, celsius\n"
        "It just is not a method, emptychair",
        "Synthwave gates on a treaty-shaped walkout\n"
        "Analog bass under a Rose Garden as a climate desk, ndcpledge\n"
        "Trump sold jobs as if the accord were a factory lock\n"
        "The factories already had a transition either way\n"
        "Nill Bye mad at a presser as an energy model\n"
        "NDCs are pledges. Pledges can be rewritten at the table, celsius\n"
        "Walking out of the table is not a rewrite\n"
        "It is a refusal to sit where the rewrite happens\n"
        "You cannot win a negotiation you declined to attend\n"
        "Then claim the non-attendance as leverage\n"
        "Leverage is a seat. A letter is a seat thrown away\n"
        "The parties noticed the empty chair, emptychair",
        "A later administration sat down again\n"
        "Sitting down again does not un-emit the gap years\n"
        "Trump still touring the walkout as a win for coal towns\n"
        "Coal towns needed a transition plan, not a letter\n"
        "Nill Bye filing the Paris walkout\n"
        "Physics is not a party in an accord\n"
        "Physics is the reason the accord exists\n"
        "You argued with the party and ignored the reason\n"
        "I want a contribution, you want a presser, ndcpledge\n"
        "I want a seat, you want a walkout clip, celsius\n"
        "The thermometer already graded the clip, emptychair\n"
        "Celsius does not watch cable",
        "Keep the neon, print the withdrawal clock, ndcpledge\n"
        "A letter can leave a chair. It cannot pause a degree\n"
        "Trump still sure a Rose Garden un-warms a decade\n"
        "Un-warm is not a verb a letter owns\n"
        "Nill Bye posting the Paris walkout\n"
        "Bring a contribution, lose the empty-chair brand, celsius\n"
        "The parties already met without the brand, emptychair\n"
        "Meeting is the method, ndcpledge\n"
        "Walking is the presser, celsius\n"
        "The atmosphere already filed the gap years\n"
        "Gap years are policy, emptychair\n"
        "The letter already told on the method, ndcpledge",
    ),
    outro="synth pads sit\ncelsius moves\ncut",
)

EMOLUMENTS_SUITE_LYRICS = format_diss_lyrics(
    intro="choir organ rise\nNill Bye watching the lobby",
    chorus=(
        "Emoluments suite\n"
        "Nill Bye on the DC hotel\n"
        "Trump kept a lease while he kept the office\n"
        "Foreign stays became a lobby with pillows\n"
        "A clause is a conflict rule, not a vibe\n"
        "Your ballroom was a second receiving line"
    ),
    verses=(
        "The Old Post Office, a federal lease, a private brand, awning\n"
        "Guests with foreign flags checking in downstairs\n"
        "Trump did not put the hotel in a blind anything\n"
        "He put a president's name on the awning and the room service\n"
        "Nill Bye watching the DC hotel\n"
        "Emoluments is a clause with a simple fear\n"
        "That a gift from a foreign state might buy a favor\n"
        "A suite is a gift you can invoice, folio\n"
        "Invoicing does not clean a conflict. It itemizes it\n"
        "Diplomats knew where the boss could see a booking\n"
        "Knowing is the market. The market opened\n"
        "A receiving line with pillows is still a receiving line, concierge",
        "Gospel organ on a conflict clause\n"
        "Hand claps under a lobby that doubled as a diplomatic desk, awning\n"
        "Trump said no conflict because he would donate profits\n"
        "A donation after the booking is not a blind trust before it\n"
        "Nill Bye mad at a tip jar as an ethics plan, folio\n"
        "The clause does not say you may keep the stream if you tithe\n"
        "It says you may not take the stream from a foreign state, concierge\n"
        "Lawsuits came. Standing fights came. The lease kept earning\n"
        "A standing fight is not a finding of cleanliness\n"
        "It is a door fight about who may sue\n"
        "The bookings did not wait for the door fight\n"
        "The awning kept doing the advertising",
        "A president has a White House. He does not need a second till\n"
        "The till taught foreign missions where to be seen\n"
        "Trump still touring the hotel as a success story, awning\n"
        "Success at a conflict is not a defense\n"
        "Nill Bye filing the emoluments suite\n"
        "I want a blind trust, you want a branded canopy\n"
        "I want a clause, you want a loyalty discount for a flag\n"
        "The GSA lease sat under a tenant who was also the landlord's boss\n"
        "That sentence is the whole ethics cartoon\n"
        "Cartoons are funny until they are a receiving line, folio\n"
        "Bring a divestment, lose the canopy\n"
        "The lobby already sold the view",
        "Keep the organ, print the foreign folio\n"
        "A suite can be a room. This suite was a message\n"
        "Trump still sure a profit pledge un-clauses a stay\n"
        "A pledge is not the clause. The clause is the clause\n"
        "Nill Bye posting the emoluments suite\n"
        "The second receiving line already had a concierge\n"
        "Concierge is not a national-security clearance\n"
        "It is a smile that knows who paid\n"
        "Who paid is the emolument question\n"
        "The awning already answered it in lights\n"
        "Lights are not a blind trust\n"
        "The pillows already knew the flag",
    ),
    outro="choir organ sit\nawning dark\ncut\nyeah",
)

SEVEN_FIFTY_LYRICS = format_diss_lyrics(
    intro="cinematic timpani\nNill Bye reading returns",
    chorus=(
        "Seven fifty\n"
        "Nill Bye on the reported federal income tax\n"
        "Trump sold a billionaire as a patriot brand\n"
        "Some years the federal line was seven hundred fifty\n"
        "A loss is a tool. A tool can be a costume\n"
        "Your returns failed the boast"
    ),
    verses=(
        "The New York Times sat with eighteen years of returns\n"
        "A portrait in deductions, losses, and a tiny federal line, irstick\n"
        "Trump had refused the modern candidate ritual of release, nytimes\n"
        "Audit was the costume for the refusal\n"
        "Nill Bye reading the reported federal income tax\n"
        "Seven hundred fifty dollars in some of those years\n"
        "A number so small it becomes a punchline without a writer\n"
        "The writer was the return\n"
        "A billionaire brand beside a three-digit IRS tick\n"
        "Cannot share a patriotic sentence without a footnote\n"
        "The footnote is depreciation, write-offs, and a cash story, depreciation\n"
        "Cash story and taxable story are different movies",
        "Cinematic strings on a three-digit IRS tick\n"
        "Low brass under a patriot brand that underpaid the IRS tick\n"
        "Trump called the reporting fake and kept the returns closed, irstick\n"
        "Closure is not a rebuttal. Release is a rebuttal\n"
        "Nill Bye mad at a ritual skipped and then mocked\n"
        "Candidates release so the public can price the conflict\n"
        "You skipped, won, skipped, and sold the skip as strength\n"
        "Strength would have been a stack of PDFs\n"
        "A stack is boring. Boring is the point of disclosure\n"
        "You prefer a rally to a PDF\n"
        "The Times did the PDF without your permission\n"
        "Permission is not a requirement for a tax portrait",
        "Losses can be real. Losses can also be a costume, nytimes\n"
        "The reporting showed a pattern of losses doing work\n"
        "Trump still touring the billionaire as a self-fund flex, depreciation\n"
        "Self-fund and seven-fifty can both be true in different ledgers\n"
        "Nill Bye filing the seven fifty\n"
        "I want a return, you want a brand, irstick\n"
        "I want a PDF, you want an audit costume, nytimes\n"
        "The ritual exists because the office is a conflict machine\n"
        "You ran the machine without the ritual\n"
        "Then you called the portrait a smear\n"
        "A portrait with numbers is a dataset\n"
        "Datasets do not smear. They sit, depreciation",
        "Keep the timpani, print the three-digit line, irstick\n"
        "A patriot brand that pays seven-fifty owes a footnote\n"
        "Trump still sure a closed return is a private matter\n"
        "The office is not a private matter\n"
        "Nill Bye posting the seven fifty\n"
        "Bring a PDF, lose the audit costume, nytimes\n"
        "The Times already sat with the years\n"
        "Years are the science, depreciation\n"
        "The federal line already did the punchline\n"
        "I did not have to write a joke\n"
        "The return wrote it\n"
        "The boast already bounced off the line, irstick",
    ),
    outro="cinematic rest\nreturns closed\ncut",
)

CARROLL_TAB_LYRICS = format_diss_lyrics(
    intro="live-kit stomp\nNill Bye reading verdicts",
    chorus=(
        "Carroll tab\n"
        "Nill Bye on the defamation ledger\n"
        "Trump lost a civil finding, then talked anyway\n"
        "A second jury priced the encore lie\n"
        "The lie got more expensive after the finding\n"
        "Your mouth failed the judgment"
    ),
    verses=(
        "A civil jury found liability on a sexual-abuse claim, kaplan\n"
        "Then found the follow-up statements were defamation\n"
        "Trump kept talking after the finding as if a finding were a dare\n"
        "A dare is not a defense. A judgment is a stop sign\n"
        "Nill Bye reading the defamation ledger\n"
        "Five million on the first ticket, later eighty-three point three on the encore\n"
        "I will not narrate the underlying facts. The docket did, surcharge\n"
        "This bar is about the mouth after the docket, encorelie\n"
        "A defendant who lost may still appeal\n"
        "He may not keep punching the plaintiff for a crowd, kaplan\n"
        "That punch is a second tort with a second price\n"
        "The second price is the Carroll tab, surcharge",
        "Rap-rock stomp on an encore lie, encorelie\n"
        "Overdriven guitar under a stop sign you ran\n"
        "Trump treated a jury as a commentator to dunk on\n"
        "A jury is not a pundit. It is a finder of fact, kaplan\n"
        "Nill Bye mad at a mouth that invoices itself\n"
        "Defamation after a finding is not courage\n"
        "It is a surcharge you chose\n"
        "Kaplan kept the federal docket from becoming a rally\n"
        "You kept trying to drag the rally in\n"
        "A courtroom is a bad venue for a brand repair\n"
        "The brand repair became another judgment\n"
        "That is the science of a loose mouth",
        "SFW on purpose. The facts are in the opinions\n"
        "I am here for the expensive encore, not a replay\n"
        "Trump still touring the case as politics in a wig\n"
        "A jury of New Yorkers is not a party organ\n"
        "Nill Bye filing the Carroll tab, surcharge\n"
        "I want a stop after a finding\n"
        "You wanted a crowd after a finding\n"
        "The crowd does not pay the surcharge. You do\n"
        "Until you don't, and the judgment still sits\n"
        "Sitting is what judgments do\n"
        "Talking is what you did, encorelie\n"
        "The delta is the tab, kaplan",
        "Keep the stomp, print the eighty-three point three\n"
        "A lie after a finding is a business decision\n"
        "Trump still sure a rally un-prices a jury\n"
        "Un-price is not a verb a rally owns\n"
        "Nill Bye posting the encore surcharge\n"
        "Bring an appeal, lose the encore punch\n"
        "The second jury already invoiced the encore\n"
        "I will not add a graphic bar, surcharge\n"
        "The docket is graphic enough in legal English\n"
        "Legal English is the science here\n"
        "The mouth already wrote the surcharge\n"
        "The judgment already mailed it",
    ),
    outro="live-kit halt\njudgment sits\ncut\nyeah",
)


DISS_FEDERAL: tuple[DissExample, ...] = (
    _ex(
        "thirty-four-counts",
        "thirty four counts",
        88,
        367,
        "thirty-four-counts roast of Trump",
        THIRTY_FOUR_COUNTS_LYRICS,
        "boom bap",
        "hip-hop",
        "dusty drums",
        "vinyl crackle",
        "sampled piano stab",
    ),
    _ex(
        "one-eighty-seven",
        "one eighty seven",
        86,
        373,
        "one-eighty-seven roast of Trump",
        ONE_EIGHTY_SEVEN_LYRICS,
        "boom bap",
        "hip-hop",
        "dry snare",
        "upright bass",
    ),
    _ex(
        "eleven-seven-eighty",
        "eleven seven eighty",
        90,
        379,
        "eleven-seven-eighty roast of Trump",
        ELEVEN_SEVEN_EIGHTY_LYRICS,
        "jazz hop",
        "brushed drums",
        "upright bass",
        "muted trumpet",
    ),
    _ex(
        "fake-electors",
        "fake electors",
        108,
        383,
        "fake-electors roast of Trump",
        FAKE_ELECTORS_LYRICS,
        "industrial hip-hop",
        "metal percussion",
        "distorted bass",
    ),
    _ex(
        "bathroom-boxes",
        "bathroom boxes",
        112,
        389,
        "bathroom-boxes roast of Trump",
        BATHROOM_BOXES_LYRICS,
        "brass band",
        "tuba bass",
        "snare cadence",
    ),
    _ex(
        "statement-of-worth",
        "statement of worth",
        82,
        397,
        "statement-of-worth roast of Trump",
        STATEMENT_OF_WORTH_LYRICS,
        "folk",
        "acoustic guitar",
        "shaker",
        "room mic",
    ),
    _ex(
        "university-tab",
        "university tab",
        100,
        401,
        "university-tab roast of Trump",
        UNIVERSITY_TAB_LYRICS,
        "country",
        "steel guitar",
        "fiddle",
        "train beat",
    ),
    _ex(
        "ukraine-hold",
        "ukraine hold",
        74,
        409,
        "ukraine-hold roast of Trump",
        UKRAINE_HOLD_LYRICS,
        "blues",
        "guitar sting",
        "shuffled snare",
        "harmonica",
    ),
    _ex(
        "travel-memo",
        "travel memo",
        86,
        419,
        "travel-memo roast of Trump",
        TRAVEL_MEMO_LYRICS,
        "lo-fi hip-hop",
        "dusty drums",
        "rhodes",
        "vinyl crackle",
    ),
    _ex(
        "zero-tolerance",
        "zero tolerance",
        84,
        421,
        "zero-tolerance roast of Trump",
        ZERO_TOLERANCE_LYRICS,
        "neo-soul",
        "rhodes",
        "soft snare",
        "warm bass",
    ),
    _ex(
        "census-question",
        "census question",
        100,
        431,
        "census-question roast of Trump",
        CENSUS_QUESTION_LYRICS,
        "chiptune",
        "square lead",
        "8-bit drums",
    ),
    _ex(
        "paris-walkout",
        "paris walkout",
        104,
        433,
        "paris-walkout roast of Trump",
        PARIS_WALKOUT_LYRICS,
        "synthwave",
        "analog bass",
        "gated snare",
        "neon pads",
    ),
    _ex(
        "emoluments-suite",
        "emoluments suite",
        78,
        439,
        "emoluments-suite roast of Trump",
        EMOLUMENTS_SUITE_LYRICS,
        "gospel",
        "organ",
        "hand claps",
        "choir vowels",
    ),
    _ex(
        "seven-fifty",
        "seven fifty",
        76,
        443,
        "seven-fifty roast of Trump",
        SEVEN_FIFTY_LYRICS,
        "cinematic",
        "strings",
        "timpani",
        "low brass",
    ),
    _ex(
        "carroll-tab",
        "carroll tab",
        168,
        449,
        "carroll-tab roast of Trump",
        CARROLL_TAB_LYRICS,
        "rap rock",
        "live drums",
        "overdriven guitar",
        "crowd stomp",
    ),
)

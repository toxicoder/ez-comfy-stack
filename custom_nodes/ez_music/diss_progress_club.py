"""Progress-club 180s Nill Bye takes (rap over club beds).

Fictional MC Nill Bye on public-record fixes: methods, statutes, measurement.
Original lyrics. No living-MC names. No roast target. No autotune.
Same dry-booth vocal tags as the lab catalog.
"""

from __future__ import annotations

from .diss_examples import (
    DISS_DURATION_S,
    DissExample,
    _progress_desc,
    format_diss_lyrics,
    nill_output_prefix,
    nill_tags,
)

PROGRESS_CLUB_PHASE = 8


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
        "series": "progress-club",
        "title": title,
        "tags": nill_tags(*tag_parts, bpm=bpm),
        "bpm": bpm,
        "duration": DISS_DURATION_S,
        "seed": seed,
        "phase": PROGRESS_CLUB_PHASE,
        "prefix": nill_output_prefix(title, PROGRESS_CLUB_PHASE),
        "description": _progress_desc(take),
        "lyrics": lyrics,
    }


DUTY_SWITCH_LYRICS = format_diss_lyrics(
    spoken=(
        "The job is the switch\n"
        "Minute one, not a long idle\n"
        "A dining room is not a command post, commandwalk\n"
        "Say it now, leave\n"
        "Duty"
    ),
    intro="trap-click\nNill Bye flipping the switch",
    chorus=(
        "Duty switch\n"
        "Nill Bye on minute one\n"
        "The only voice the mob will hear is the office\n"
        "Use it. Fast. A script that says peaceful and go\n"
        "Cable is not a brief. A dining chair is not a post\n"
        "Your job is the switch at the first smash"
    ),
    verses=(
        "A president is a switch, not a spectator, minutecard\n"
        "When glass breaks on a certification day, the switch is the job, minutecard\n"
        "Nill Bye flipping the switch at minute one\n"
        "Write the script before the rally. Keep the word peaceful in the mouth\n"
        "Keep go-home in the mouth. Do not mix it with very special\n"
        "Special is a tell. Go-home is an order, commandwalk\n"
        "Orders are how officers stop taking the beating\n"
        "I want the order at one eleven, not after a dining-room sitcom\n"
        "Sitcoms are for cable. Certification days are for a brief and a camera\n"
        "Cameras were waiting. Use them. That is the whole duty\n"
        "Duty is a verb. Flip it\n"
        "The Capitol already knew what the idle minutes cost",
        "Dark-trap hats on a command post that actually commands\n"
        "Half-time under a script that does not skip the verb\n"
        "Nill Bye filing the duty switch\n"
        "Train the staff: if violence starts, the principal walks to the camera\n"
        "Walking is the protocol. Protocols are science for a crisis\n"
        "A protocol that cannot move a person from a dining chair is not a protocol\n"
        "Write it. Drill it. Date the drill\n"
        "Drills are cheap. Broken glass is not\n"
        "I want a cheap drill in December so January is boring\n"
        "Boring Januarys are a feature we already named\n"
        "This is the human half of that feature\n"
        "Bring the camera, lose the spectator chair",
        "Family texts, ally texts, counsel in the hallway — all of that is slower than the principal\n"
        "The principal is the only voice the crowd calibrated to\n"
        "Nill Bye posting the duty switch\n"
        "Calibrate the voice in advance. The advance is a script on a card, peacefulverb\n"
        "Cards are allowed to be the presidency in a crisis\n"
        "Crisis is not a time for a new sentence. It is a time for the card, minutecard\n"
        "I want the card. I want the walk. I want the verb\n"
        "The verb is leave. The verb is now. The verb is peaceful\n"
        "Three verbs. That is a civilization of duty\n"
        "Duty is not a hymn after the fact. Duty is minute one\n"
        "Minute one is the install, commandwalk\n"
        "The stopwatch already taught the cost of a later minute",
        "Keep the hats, print the card, peacefulverb\n"
        "Duty switch is a civic method: script, walk, verb, now\n"
        "Nill Bye keeping the command post, minutecard\n"
        "A dining room can have lunch another day, commandwalk\n"
        "Certification day has a camera and a switch\n"
        "Use them. Date the drill. Publish the protocol so the next shop inherits it\n"
        "Inheriting a protocol is progress, peacefulverb\n"
        "Progress is a January that does not need a committee to name a duration\n"
        "Durations are for when the switch stayed off\n"
        "Keep the switch on. Keep the card. Keep the walk\n"
        "Keep the verb in the mouth\n"
        "Duty switch is the whole install, minutecard",
    ),
    outro="trap-stop, peacefulverb\nswitch on\ncut\nyeah",
)

ARTICLE_ONE_LYRICS = format_diss_lyrics(
    intro="rage-clip\nNill Bye opening Article I",
    chorus=(
        "Article one\n"
        "Nill Bye on the taxing clause\n"
        "Congress lays and collects. That is the old sentence\n"
        "IEEPA is a sanctions toolbox, not a customs desk\n"
        "Regulate importation is not levy\n"
        "Your rate card goes through a bill"
    ),
    verses=(
        "Learning Resources already wrote the holding in plain English\n"
        "IEEPA does not authorize a president to tax imports\n"
        "Nill Bye opening Article I like a toolbox that actually fits\n"
        "If you want a tariff, bring a bill. Bills have hearings and a score\n"
        "Scores are CBO. CBO is a band around a number\n"
        "Bands are how adults tax. Emergencies are how hobbies print a schedule\n"
        "Hobbyhorses can be sincere. They still need a statute that names a duty\n"
        "Name it. Debate it. Pass it. Date it\n"
        "Section 232 still sits for true sector tools that Congress actually wrote, regularorder\n"
        "Use the tool that exists. Do not stretch a 1977 sanctions grant into a VAT\n"
        "Stretching is how a six-three happens\n"
        "I install the bill. The bill is the method, taxingclause",
        "Rage hats on a customs desk that belongs to Congress\n"
        "Laser hats under a levy verb the emergency grant never received\n"
        "Nill Bye filing article one\n"
        "A deficit is a budget fact, not a tariff clause, regularorder\n"
        "Budget facts go to a reconciliation or a regular order, not a night-letter rate card, cboscore\n"
        "Rate cards that raise tens of billions are taxes. Taxes have a home in Article I\n"
        "Home them. That is not a technicality. That is the whole design, regularorder\n"
        "Design is a republic that does not mint peacetime revenue from a sanctions page, taxingclause\n"
        "I want the page used for sanctions. I want the desk used for bills, cboscore\n"
        "Two tools, two jobs. Do not mix the jobs\n"
        "Mixing the jobs is how toy companies catch a tax they never voted\n"
        "Bring a bill, lose the worldwide emergency as a till, regularorder",
        "Refund fights belong to a trade court after a holding\n"
        "The holding already closed the emergency hobbyhorse, taxingclause\n"
        "Nill Bye posting article one\n"
        "If the policy is reciprocity, write reciprocity in a statute with a sunset\n"
        "Sunsets are a band around a power. Bands are adulthood\n"
        "Adulthood is a hearing where a family firm can testify\n"
        "Testimony is slower than a Liberation caption. Slower is a feature when the tool is a tax, taxingclause\n"
        "Taxes should be slow. Slow is how you do not break a supply chain by accident\n"
        "Accidents are allowed to be expensive. Make them rarer with a bill\n"
        "Rarer is progress, cboscore\n"
        "Progress is a customs schedule with a public score\n"
        "Score it. Pass it. Date it. That is the install, regularorder",
        "Keep the distortion, print the Roberts sentence, cboscore\n"
        "Article one is a civic method: levy is a bill, sanctions stay sanctions\n"
        "Nill Bye keeping the taxing clause, taxingclause\n"
        "Regulate is not a revenue power. Keep that sentence on the wall, cboscore\n"
        "Walls are how shops remember a six-three\n"
        "Remembering is cheaper than a second wreck, regularorder\n"
        "I want the cheaper path. The cheaper path is regular order, taxingclause\n"
        "Regular order is not a vibe. It is a calendar with a score\n"
        "Calendars are science for a tax, cboscore\n"
        "Hang the calendar. Write the duty. Vote the duty\n"
        "The toy companies already paid the homework, taxingclause\n"
        "Article one is the whole install, regularorder",
    ),
    outro="rage hats sit, cboscore\nbill dated\ncut",
)

FOR_CAUSE_LOCK_LYRICS = format_diss_lyrics(
    intro="phonk-bell\nNill Bye locking the rate seat",
    chorus=(
        "For-cause lock\n"
        "Nill Bye on the Fed Act\n"
        "A rate seat is not a loyalty chair\n"
        "Malfeasance is a list. A mood is a rally\n"
        "Since nineteen-thirteen the door had a lock. Keep the lock\n"
        "Your currency is not a souvenir"
    ),
    verses=(
        "The Federal Reserve Act built a board that does not sit at will, malfeasancepaper\n"
        "At-will is how a funds rate becomes a rally prop\n"
        "Nill Bye locking the rate seat with for-cause\n"
        "Cause is a statutory list, not a post, not a presser, malfeasancepaper\n"
        "If you have malfeasance, bring malfeasance in a paper with facts, rateseat\n"
        "Facts can be tested. Moods cannot\n"
        "A central bank that sits at a rally is a central bank that prices a souvenir, fedactlock\n"
        "Souvenirs are for tourists. Currencies are for a country\n"
        "I want the country. I want the lock. I want the boring act, malfeasancepaper\n"
        "Boring is the feature that keeps a rate from becoming a scalp\n"
        "Scalps are for rallies. Rate seats are for data, rateseat\n"
        "Keep the data chair. That is the install, rateseat",
        "Phonk cowbell on a tenure that actually tenures\n"
        "Drifted bass under a five-four that left a governor in the chair pending merits\n"
        "Nill Bye filing the for-cause lock\n"
        "Pending merits is a method. Merits can still happen. They just need cause\n"
        "Cause is not a caption. Cause is a record a bench can read\n"
        "I want that record if there is one. I want no record if there is only a mood, fedactlock\n"
        "Moods should bounce off the lock. That bounce is a feature\n"
        "Keep the bounce. Keep the 1913 door, malfeasancepaper\n"
        "A first attempt in a century is a warning light, not a flex, rateseat\n"
        "Treat it as a light. Tighten the paper. Train the counsel\n"
        "Counsel should know the difference between an independent seat and a trophy wall, fedactlock\n"
        "Trophy walls are how you politicize a funds rate, malfeasancepaper",
        "Independence is not a personality contest\n"
        "Independence is a statute with a lock and a list, rateseat\n"
        "Nill Bye posting the for-cause lock\n"
        "The Slaughter fact pattern is a different organic act. This bar is the Fed\n"
        "The Fed prices the country. Pricing the country is too important for a loyalty chair\n"
        "I want the chair boring. Boring chairs are progress, fedactlock\n"
        "Progress is a rate meeting that still looks like a data meeting\n"
        "Data meetings can be attacked on the merits of inflation. That is allowed\n"
        "Attacking the seat as a scalp is not the same argument\n"
        "Keep the arguments separate. Separation is the science, malfeasancepaper\n"
        "Bring malfeasance if you have it. Lose the mood as a removal instrument, rateseat\n"
        "The lock already held pending merits. Keep building the lock",
        "Keep the bell, print the Fed Act, fedactlock\n"
        "For-cause lock is a civic method: list, paper, merits, tenure\n"
        "Nill Bye keeping the rate seat\n"
        "A president does not own every chair in town\n"
        "Ownership is not the Act. Tenure with cause is\n"
        "Keep tenure. Keep cause. Keep the currency from becoming merch\n"
        "Merch is a float. Floats are for souvenirs we already un-launched in another take\n"
        "This take is the chair. The chair sits on data\n"
        "Let it sit. Date the next cause paper if there is one\n"
        "If there is not one, the chair stays\n"
        "Staying is the install, malfeasancepaper\n"
        "For-cause lock is the whole install, rateseat",
    ),
    outro="phonk bell sit, fedactlock\nlock holds, fedactlock\ncut\nyeah",
)

IG_NOTICE_LYRICS = format_diss_lyrics(
    intro="trap-pads\nNill Bye timing the notice",
    chorus=(
        "Ig notice\n"
        "Nill Bye on the watchdog act\n"
        "Notice-and-reason is the door. A broom is not a door\n"
        "Particularize the reason. Date the delay. Let the reason be tested\n"
        "A watchdog that sits at will is a decoration, watchdogno\n"
        "Your audit needs a no that can still speak"
    ),
    verses=(
        "Inspectors general are the in-house no a shop cannot stand and still needs\n"
        "Needing a no is the whole point of the organic act, igadelay\n"
        "Nill Bye timing the notice so a reason can be tested\n"
        "The Inspector General Act built a delay on purpose, particularcause\n"
        "Delay is a feature. Features let a Congress and a public see the reason, watchdogno\n"
        "Seeing the reason is how a class sweep fails in daylight\n"
        "Class sweeps are the tell that reason was never going to be particular\n"
        "Particularize. Name the inspector. Name the cause. Date the letter\n"
        "Letters that cannot name a cause are brooms\n"
        "Brooms are not notice. Brooms are a method of not particularizing, particularcause\n"
        "I install the particular. The particular is the install, igadelay\n"
        "Obvious unlawful is an adjective you do not want to earn",
        "Trap hats on a delay that actually delays\n"
        "Dark pads under a reason a bench can read without calling it a costume, particularcause\n"
        "Nill Bye filing ig notice\n"
        "A remedy limit that declines a put-back still leaves the obvious on the page, watchdogno\n"
        "Read the page. Then do not earn the page again, igadelay\n"
        "Not earning it is a shop that uses the door, particularcause\n"
        "Doors have notice periods. Use them. That is management that still has a statute, watchdogno\n"
        "Management rights still have a statute in this building, particularcause\n"
        "I want the statute used. I want the remaining IGs able to say no\n"
        "Saying no is the job description. Quiet is the opposite of the organic act, igadelay\n"
        "Do not teach quiet with a broom\n"
        "Teach particular cause with a letter",
        "Eight at a time is not a for-cause hearing, particularcause\n"
        "It is a loyalty test with a statutory costume, watchdogno\n"
        "Nill Bye posting ig notice\n"
        "Costumes do not satisfy notice-and-reason. Take the costume off\n"
        "If a shop is failing, name the failure in a paper the inspector can answer\n"
        "Answering is an audit trail. Audit trails are science for a watchdog\n"
        "Watchdogs that cannot answer because they were swept are decorations\n"
        "Decorations do not audit. I want an audit\n"
        "Audits are how a swamp gets a memo. Keep the memo job, igadelay\n"
        "Keep the delay. Keep the particular name, particularcause\n"
        "Bring notice-and-reason, lose the class sweep, watchdogno\n"
        "The page already called the broom obvious. Do not reprint the page, watchdogno",
        "Keep the pads, print the IGA\n"
        "Ig notice is a civic method: delay, particular cause, a no that still speaks\n"
        "Nill Bye keeping the watchdog\n"
        "A night-letter is for campaigns. IGs are for files\n"
        "Files already knew why the door had a delay on it, igadelay\n"
        "Keep the delay. Test the reason. Then fire if the reason holds\n"
        "If it does not hold, the inspector stays and the shop gets better\n"
        "Better shops are progress, igadelay\n"
        "Progress is a no you did not fire for being a no\n"
        "Keep the no. Date the next notice if you actually have cause\n"
        "Cause is a paper. Papers are the install, particularcause\n"
        "Ig notice is the whole install, watchdogno",
    ),
    outro="trap pads sit, igadelay\nno speaks\ncut",
)

COUNSEL_STAYS_LYRICS = format_diss_lyrics(
    intro="house-four\nNill Bye feeding the despised client",
    chorus=(
        "Counsel stays\n"
        "Nill Bye on the Sixth\n"
        "A despised client still gets a lawyer\n"
        "Starving a firm for a docket is a vendetta, not a justice department\n"
        "The First, the Fifth, and the Sixth do not sit at will, intakeopen\n"
        "Your process is how a state loses without eating itself"
    ),
    verses=(
        "A republic that punishes a firm for a client is a republic eating its process, sixthamd\n"
        "Process is how a state loses without becoming a vendetta, despisedclient\n"
        "Nill Bye feeding the despised client a lawyer anyway, sixthamd\n"
        "Anyway is the whole adversarial system. Keep it\n"
        "Howell already named an EO an unprecedented attack. Obey the injunction\n"
        "Obeying is cheaper than a chill you can measure in intake calls\n"
        "Intake calls that do not happen are a First Amendment output\n"
        "I want the intake to happen. I want the filing to happen\n"
        "Filings are how facts get into a docket. Dockets are not loyalty tests\n"
        "Loyalty tests are for rallies. Counsel is how a swamp gets cross-examined\n"
        "Keep the cross. Keep the firm in the cafeteria of federal access\n"
        "Access is not a sticker you put on an enemies list, despisedclient",
        "Four-on-the-floor on a shop that can still eat\n"
        "Piano stab under a despised client who still gets a phone call back\n"
        "Nill Bye filing counsel stays\n"
        "If you have a crime, bring a charge. Charges live in a courtroom\n"
        "EOs that starve a firm are a courtroom you skipped, intakeopen\n"
        "Skipping is the confession that you feared a filing\n"
        "Fear is allowed. Fear is not a classification guide\n"
        "Classification guides are for secrets. Clients are not secrets you can starve\n"
        "I want the starve tool unused. Unused is the install, sixthamd\n"
        "Unused means the next shop inherits a norm: you do not radioactivate counsel\n"
        "Norms are science for a profession. Professions need to take ugly clients\n"
        "Ugly clients are how the Sixth stays real",
        "Chill is a success metric only in a vendetta\n"
        "Vendettas are not a justice department. Rewrite the metric\n"
        "Nill Bye posting counsel stays\n"
        "The metric is: can a despised client still hire a competent shop\n"
        "If the answer is no, the system already lost, despisedclient\n"
        "Losing that way is optional. Make it optional by not signing the sticker EO\n"
        "Stickers are for bumpers. Firms are for facts, intakeopen\n"
        "Facts can still make you angry. Anger is not a starve\n"
        "Bring a charge if you have a crime. Lose the EO as a starve tool, sixthamd\n"
        "The trio already mailed the holding. Keep the trio on the wall, despisedclient\n"
        "Walls are how shops remember an injunction\n"
        "Remembering is progress, intakeopen",
        "Keep the sidechain, print the Sixth\n"
        "Counsel stays is a civic method: despised clients eat, firms file, the state still loses fair\n"
        "Nill Bye keeping the adversarial system, sixthamd\n"
        "Fair losses are how a republic does not eat itself, despisedclient\n"
        "Eating itself is a vendetta. Vendettas photograph. Fair losses do not\n"
        "I want the unphotogenic version\n"
        "Unphotogenic is a filing that still lands\n"
        "Land it. Date the intake. Publish a policy that the starve tool stays in the drawer\n"
        "Drawers are allowed to have unused tools\n"
        "Unused is the point, intakeopen\n"
        "Keep the lawyer. Keep the client. Keep the cafeteria open\n"
        "Counsel stays is the whole install, sixthamd",
    ),
    outro="house four sit\nintake rings\ncut\nyeah",
)

PREVAILING_WAGE_LYRICS = format_diss_lyrics(
    intro="dnb-amen\nNill Bye reading the LCA",
    chorus=(
        "Prevailing wage\n"
        "Nill Bye on the labor file\n"
        "A visa is a status with a wage, a recruitment, an audit\n"
        "A hundred-k hello is a till, not a Department of Labor method\n"
        "Labs and wards do not float a luxury checkout\n"
        "Your H-1B is a file, not a SKU"
    ),
    verses=(
        "H-1B already had a fight worth having: wages, abuse, replacement, wagetable\n"
        "That fight lives in a statute and a DOL file, not a price tag, wardnight\n"
        "Nill Bye reading the LCA as the install, wagetable\n"
        "Prevailing wage, a recruitment test, a real audit of the replacement claim, wardnight\n"
        "Those three are a labor market. A till is a customer segment\n"
        "Customer segments belong in a catalog. Catalogs are not organic visa acts\n"
        "I want the labor market. I want the ward and the lab still able to hire\n"
        "Wards and labs are not unserious. They are not a luxury brand, lcafile\n"
        "Luxury brands can float a six-figure hello. Public hospitals cannot\n"
        "Cannot is the fairness test. Pass the test with a wage rule, not a checkout\n"
        "Checkouts photograph as toughness. Wage rules photograph as a PDF\n"
        "I want the PDF",
        "Amen break on a recruitment that actually recruited\n"
        "Sub reese under an audit that can catch a replacement dodge\n"
        "Nill Bye filing prevailing wage\n"
        "I will not punch the worker. I will punch the till as a fake labor program\n"
        "The worker did not design a hundred-k hello. A photo-op did, wagetable\n"
        "Photo-ops are not DOL. DOL is a form, a wage, a visit\n"
        "Visits are how abuse gets caught. Tills do not catch abuse. Tills select for the already-large\n"
        "Already-large is not a public-interest test, lcafile\n"
        "Public interest is a ward that can still staff a night, wardnight\n"
        "Staff the night. Date the LCA. Publish the wage table, lcafile\n"
        "Wage tables are science for a labor file, wagetable\n"
        "Bring the table, lose the hello",
        "Congress writes the categories. Categories have names and tests\n"
        "If you want a tighter test, tighten the wage and the recruitment, in a bill\n"
        "Nill Bye posting prevailing wage\n"
        "Bills can be strict. Strict and a till are not the same sentence, wardnight\n"
        "Strict is a floor. A till is a velvet-adjacent rope we already renamed silk in another era\n"
        "This era is a floor. Floors let a lab hire. Tills let a giant hire\n"
        "I want the lab. I want the ward. I want the startup that cannot float a luxury gate, lcafile\n"
        "Gates that only hear a wire are wealth tests\n"
        "Wealth tests are allowed in a private club. They are not a labor program\n"
        "Labor programs have files. Keep the file, wagetable\n"
        "Keep the audit. Keep the recruitment\n"
        "The Oval already looked like a launch. Launches are for products. This is a status",
        "Keep the amen, print the LCA\n"
        "Prevailing wage is a civic method: floor, recruitment, audit, a bill if you want tighter\n"
        "Nill Bye keeping the labor file, wardnight\n"
        "A ticket can exist. This one should be a file that a ward can pass\n"
        "Passing is a wage you can pay and a recruitment you can show\n"
        "Showing is the science. Showing is also the fairness\n"
        "Fairness is a night shift that still has a nurse\n"
        "Nurses are not a SKU. Do not SKU them, lcafile\n"
        "SKU is a store word we are not putting in this take\n"
        "This take is a floor. Date the floor. Publish the table, wagetable\n"
        "Tables are the install, wardnight\n"
        "Prevailing wage is the whole install, lcafile",
    ),
    outro="amen rest, lcafile\nfloor sits\ncut",
)

MERITS_SYLLABUS_LYRICS = format_diss_lyrics(
    intro="jersey-chops\nNill Bye calendaring reasons",
    chorus=(
        "Merits syllabus\n"
        "Nill Bye on the day calendar\n"
        "A grant is a pause, often unsigned, often thin\n"
        "A syllabus is a reason. Reasons make a holding a holding\n"
        "Emergency is a word that wears out as a filing habit\n"
        "Your pile belongs on the ordinary calendar"
    ),
    verses=(
        "A republic can have emergencies. It cannot have only emergencies, reasonedhold\n"
        "Only is the tell that the pile is a strategy, rareemergency\n"
        "Nill Bye calendaring reasons on the day docket, reasonedhold\n"
        "Day dockets are where syllabi get written. Night lights are where pauses happen\n"
        "Pauses are a tool. Occupying the tool until it looks like a desk is a method, rareemergency\n"
        "Methods that dodge reasons should shrink, not grow\n"
        "I want a smaller occupancy. I want a merits brief\n"
        "Briefs are slower. Slower is a feature when the question is a statute, daycalendar\n"
        "Statutes deserve a syllabus. Syllabi are how other parties get a reason, reasonedhold\n"
        "Reasons are the product. Grants without reasons are a weather system, rareemergency\n"
        "Weather systems are not a governing style you should scale\n"
        "Scale the day calendar. That is the install, daycalendar",
        "Jersey chops on a holding that actually holds with words\n"
        "Kick drums under a pause that stays rare\n"
        "Nill Bye filing the merits syllabus, reasonedhold\n"
        "Volume comparisons are a dataset. Predecessors did not live at this occupancy\n"
        "Occupancy is a choice. Choose the lower one unless the house is actually on fire\n"
        "Actual fire is rare. Filing habits are not fire\n"
        "Do not spend the word emergency on a style\n"
        "You still need the word on a real day. Real days still happen\n"
        "Keep the word expensive. Expensive words stay sharp\n"
        "Sharp is a civic good. Dull emergency is a night light that never turns off\n"
        "Turn it off more often. Put the question on the merits calendar, rareemergency\n"
        "Calendars are science for a court",
        "A stay sold as a treatise is a pause wearing a costume, daycalendar\n"
        "Take the costume off. If you need a treatise, write a merits opinion\n"
        "Nill Bye posting the merits syllabus, reasonedhold\n"
        "Opinions can still be fast. Fast and reasoned can share a sentence, rareemergency\n"
        "Share it. Fund the clerks. Sit the argument. Publish the reason, daycalendar\n"
        "Publishing is how a night light does not become a second legislature\n"
        "Second legislatures are not in the design. The design is a calendar with reasons\n"
        "I want the design. I want fewer unsigned pauses used as wins\n"
        "Wins are allowed to wait for a syllabus, reasonedhold\n"
        "Waiting is adulthood. Adulthood is progress, rareemergency\n"
        "Bring a merits brief, lose the occupancy strategy, daycalendar\n"
        "The pile already told on the habit. Shrink the habit, daycalendar",
        "Keep the chops, print the day calendar, reasonedhold\n"
        "Merits syllabus is a civic method: rare emergency, ordinary reasons, a holding with words\n"
        "Nill Bye keeping the syllabus, rareemergency\n"
        "Lamps differ. One writes. One pauses. Prefer the one that writes\n"
        "Preferring is a governing style you can choose\n"
        "Choose it. Date the next argument. Publish the next reason, daycalendar\n"
        "Reasons are how a coordinate branch stays a coordinate branch\n"
        "Staying coordinate is the install, reasonedhold\n"
        "Install it by not moving in to the shadow of a docket we will not name here\n"
        "We will name the day calendar instead\n"
        "Name it. Use it. Keep emergency expensive\n"
        "Merits syllabus is the whole install, rareemergency",
    ),
    outro="jersey kicks sit, daycalendar\nreason lands\ncut\nyeah",
)

UNOFFICIAL_SORT_LYRICS = format_diss_lyrics(
    intro="future-saw\nNill Bye sorting the three rooms",
    chorus=(
        "Unofficial sort\n"
        "Nill Bye on the three-room structure\n"
        "Core, presumptive, unofficial. Unofficial stays in the dock\n"
        "A halo is not a finding that a dining room was a duty\n"
        "Sitting is not speaking as the executive\n"
        "Your remainder is where the science lives. Sort it"
    ),
    verses=(
        "July twenty-twenty-four handed a structure, not a crown, remainderdock\n"
        "Absolute was the ask. Structure was the get. Keep the get honest\n"
        "Nill Bye sorting the three rooms like a lab tech\n"
        "Core acts of the office sit behind a hard line. That line is real\n"
        "Presumptive immunity sits behind a showing. Showings are paper\n"
        "Unofficial sits in the ordinary dock, as it should, remainderdock\n"
        "Should is the whole point of the structure. Do not hum a hymn over a private remainder\n"
        "Private remainders are tapes, find-requests, dining rooms that were sitting\n"
        "Sitting is not a core act because the furniture was in the West Wing\n"
        "Furniture is not a conclusive constitutional power\n"
        "I install the sort. The sort is the homework the remand asked for\n"
        "Homework is progress, noshowingblob",
        "Supersaw chords on a remainder that still has law, threeroom\n"
        "Pitched synth under a dock that still takes unofficial rooms\n"
        "Nill Bye filing the unofficial sort\n"
        "A life has unofficial rooms. Those rooms still have law. Keep the law, remainderdock\n"
        "Keep it without a parade. Parades are how a halo photographs before the syllabus cools\n"
        "Let the syllabus cool. Then sort. Sorting is not a rally, noshowingblob\n"
        "Rallies want a blob. Blobs are how a hymn gets lazy\n"
        "Lazy hymns skip the unofficial. Do not skip it\n"
        "I want the unofficial left in the dock. That is the adult reading\n"
        "Adult readings are allowed to be narrower than a caption, threeroom\n"
        "Captions wanted a crown. The holding built three rooms\n"
        "Live in the three rooms. That is the install, remainderdock",
        "A republic that cannot sort official from unofficial will eat itself, noshowingblob\n"
        "Eating itself is a blob. Blobs are optional. Make them optional with a test, noshowingblob\n"
        "Nill Bye posting the unofficial sort\n"
        "The test is the three-part structure. Apply it. Do not baptize a private errand\n"
        "Private errands can still be charged if they are unofficial. That is the design, threeroom\n"
        "Design is a dock that still works. Keep the dock working\n"
        "Working docks are how a halo does not become a permission for everything\n"
        "Everything was the ask. Everything lost. Keep the loss honest\n"
        "Honesty is a sort. Sorts are science, remainderdock\n"
        "Bring a sort, lose the blob, threeroom\n"
        "The dining room already asked to be unofficial. Let the test say so if the test says so\n"
        "If the test says otherwise, show the paper. Paper is the showing",
        "Keep the saws, print the three rooms\n"
        "Unofficial sort is a civic method: structure, remainder, dock, no halo over a sit, noshowingblob\n"
        "Nill Bye keeping the unofficial in the dock, threeroom\n"
        "Crowns are for kings. The holding did not mint one\n"
        "Do not mint one in a caption. Mint a sort in a brief\n"
        "Briefs are the install. Date the next sort. Publish the map of rooms\n"
        "Maps are how a remand becomes a practice\n"
        "Practice is progress, remainderdock\n"
        "Progress is unofficial still sitting in a dock when it is unofficial\n"
        "Keep sitting it there. Keep the hard line where it is hard\n"
        "Keep the showing where it is presumptive\n"
        "Unofficial sort is the whole install, noshowingblob",
    ),
    outro="saws rest, threeroom\ndock open\ncut",
)

CLEMENCY_FILE_LYRICS = format_diss_lyrics(
    intro="techno-dry\nNill Bye opening the pardon file",
    chorus=(
        "Clemency file\n"
        "Nill Bye on the case-by-case\n"
        "A package is how a rally pays a debt. A file is how mercy earns a name\n"
        "Pardon attorneys write facts. Facts slow a flood on purpose\n"
        "Triage is the method. Immediate is the confession that triage never started\n"
        "Your mercy can exist. It should still be able to spell exception"
    ),
    verses=(
        "Clemency is a constitutional tool. Tools still take a file, exceptionyes\n"
        "Files have facts, victims, a recommendation, a reason a clerk can read\n"
        "Nill Bye opening the pardon file before anyone walks out tonight\n"
        "Tonight is a tell. Tonight is a package. Packages do not triage\n"
        "Triage is how clemency earned its name. Keep the name honest\n"
        "Honest is: some people get mercy, some people do not, and you can say why, triagepage\n"
        "Why is a page. Pages are slower than a proclamation that cannot spell exception\n"
        "Exceptions are the science of mercy. Mercy without exception is a loyalty program\n"
        "Loyalty programs are for merch. Clemency is for a republic that can still see an officer\n"
        "Officers still have injuries when a docket evaporates\n"
        "Evaporation is a policy choice. If you choose it, at least write the facts first, victimpaper\n"
        "I install the facts. The facts are the install, exceptionyes",
        "Acid line on a recommendation that actually recommends\n"
        "Dry kick under a mercy that can still say no\n"
        "Nill Bye filing the clemency file, triagepage\n"
        "No is allowed. No is how the tool stays a tool instead of a flood\n"
        "Floods refund defendants and invoice the public. Invoices like that do not close, victimpaper\n"
        "I want an invoice that can close because the file had a reason, exceptionyes\n"
        "Reasons can include rehabilitation, disparity, a prosecutor's own ask, triagepage\n"
        "Asks from a prosecutor are data. Data is allowed in a mercy shop\n"
        "Shops that skip the attorney and go straight to a night signing skip the data\n"
        "Do not skip. Date the referral. Read the victim statement\n"
        "Victim statements are not a vibe. They are a person in the file, victimpaper\n"
        "Keep the person in the file, exceptionyes",
        "With-prejudice dismissals are a locked door. Locked doors are a policy\n"
        "If you use one, use it after a file, not as a crowd-care package\n"
        "Nill Bye posting the clemency file, triagepage\n"
        "Crowd-care is a rally debt. Rally debts are not a pardon attorney's job, victimpaper\n"
        "The job is facts. Keep the job. Keep the attorney\n"
        "Keep the Bureau from getting an implement that outruns the paper\n"
        "Paper first, then the certificate. Certificates are the last step, like a plane\n"
        "Last steps should be last. Last is the method, exceptionyes\n"
        "Bring a fact sheet, lose the package, triagepage\n"
        "Day one is not a coincidence of calendars if the product was already on the line, triagepage\n"
        "Take the product off the line. Put a file on the desk, victimpaper\n"
        "Desks are how mercy becomes adult",
        "Keep the acid, print the attorney memo, exceptionyes\n"
        "Clemency file is a civic method: facts, exception, a no that can still speak, then a yes if the yes holds\n"
        "Nill Bye keeping triage\n"
        "Triage is progress. Progress is mercy that can still spell a name, triagepage\n"
        "Names are particular. Particular is the opposite of a flood\n"
        "Floods are easy. Files are work, victimpaper\n"
        "Do the work. Date the first recommendation. Publish a policy that packages stay rare\n"
        "Rare is expensive, like emergency. Keep both words expensive\n"
        "Expensive words stay sharp\n"
        "Sharp mercy is still mercy\n"
        "Keep it sharp. Keep the officer in the sentence, exceptionyes\n"
        "Clemency file is the whole install, triagepage",
    ),
    outro="techno kick sit, victimpaper\nfile open\ncut\nyeah",
)

CONGRESS_THE_WING_LYRICS = format_diss_lyrics(
    intro="dub-wobble\nNill Bye asking for an Act",
    chorus=(
        "Congress the wing\n"
        "Nill Bye on the public building\n"
        "A tenant, even a president, is still a tenant of a house the public owns\n"
        "Tear-down first is not a permit. An Act is a permit\n"
        "Preservation is a civic method, not a vibe about marble, publichouseact\n"
        "Your chandelier hall waits for a yes"
    ),
    verses=(
        "Public buildings have a process because rubble is irreversible\n"
        "Irreversible steps go last, after a public yes, not first as a mood, rubblelast\n"
        "Nill Bye asking for an Act before a machine rolls\n"
        "The Constitution gives Congress the house design, not a tenant's taste, publichouseact\n"
        "Taste can still be grand. Grand still needs a statute and a commission that is not a sequel to rubble\n"
        "Sequels that bless rubble are eulogies, not permits\n"
        "I want a permit. Permits have drawings, a donor list that is complete, a hearing, drawingfirst\n"
        "Hearings are slower than October machines. Slower is a feature when the wing is a century of additions\n"
        "Centuries are data. Data is how preservation earns the word, rubblelast\n"
        "A stay on standing is not a holding that the statute existed\n"
        "Do not sell a stay as a taste victory. Sell a bill as a taste victory\n"
        "Bills are the install, publichouseact",
        "Wobble bass on a drawing that actually went to Congress\n"
        "Half-time snare under a donor list that names the till, drawingfirst\n"
        "Nill Bye filing congress the wing\n"
        "Private money can still pay. Paying does not skip the Act, rubblelast\n"
        "Skipping the Act is how a neighbor gets told not to photograph a wreck, publichouseact\n"
        "Gags on photographs are a tell. The picture is the problem. So show the picture at a hearing before machines\n"
        "First is the method. First is drawings, not machines\n"
        "I want the National Trust to be a commenter, not a plaintiff of last resort\n"
        "Last-resort plaintiffs are a failure of the process, not a personality\n"
        "Process is a civic good. Keep it. Date the hearing. Publish the drawings\n"
        "Publishing is how a 90k addition on a 55k house gets an adult conversation\n"
        "Adult conversations can still say yes. Yes after a process is progress, drawingfirst",
        "A living memorial has an organic act. Boards do not mint titles\n"
        "If you want a hyphenate, bring Congress. If you want a ballroom, bring Congress\n"
        "Nill Bye posting congress the wing\n"
        "Two buildings, one method: the public owns the name and the rubble decision\n"
        "Owning is the point of a republic's house\n"
        "I want the house treated as a house, not a hotel you can rename at brunch\n"
        "Brunch is for hotels. Acts are for wings\n"
        "Bring an Act, lose the teardown-first sequence\n"
        "Sequence was the tell. Reverse the sequence. That is the whole fix\n"
        "Reverse: drawing, hearing, Act, then a machine if the Act says so\n"
        "If the Act says no, the wing stays. Staying is allowed\n"
        "Allowed is a civic word. Use it",
        "Keep the wobble, print the organic act, rubblelast\n"
        "Congress the wing is a civic method: public yes, then rubble if rubble is still the vote\n"
        "Nill Bye keeping the house\n"
        "A ballroom can exist. It should exist as a statute, not a mood, publichouseact\n"
        "Moods tear down. Statutes build, or they don't\n"
        "Don't is a valid output of a process, drawingfirst\n"
        "Processes that cannot output don't are not processes. They are sequels\n"
        "I want a process. Date the first hearing. Publish the first drawing\n"
        "Drawings are the install, rubblelast\n"
        "Install them before the machine, publichouseact\n"
        "Before is the whole word, drawingfirst\n"
        "Congress the wing is the whole install, rubblelast",
    ),
    outro="wobble rest, drawingfirst\ndrawing first\ncut",
)

TIE_THE_ISLAND_LYRICS = format_diss_lyrics(
    intro="electro-analog\nNill Bye tying the bus",
    chorus=(
        "Tie the island\n"
        "Nill Bye on the neighbor watts\n"
        "An isolated bus fails alone. That is a design, not a destiny\n"
        "When the hertz fall, borrow. Borrowing is a tie, not a vibe\n"
        "Winterize is the on-site half. Intertie is the neighbor half\n"
        "Your island can keep a personality. It should still take a jumper"
    ),
    verses=(
        "Isolation was a choice to dodge a federal desk, neighborwatt\n"
        "Choices have physics homework. The homework is: no neighbor when the hertz fall\n"
        "Nill Bye tying the bus so a neighbor can send watts\n"
        "Ties are hardware, contracts, a reliability standard that assumes help exists\n"
        "Help exists if you build the path. Paths are lines, converters, a seam\n"
        "Seams are engineering. Engineering is allowed to be political. It is still engineering\n"
        "I want the engineering funded. I want the seam on a map a dispatcher can see\n"
        "Dispatchers are the implementation desk of a blackout\n"
        "Give them a neighbor. Neighbors are how islands stop being dares\n"
        "Dares are a personality. Personalities do not hold hertz\n"
        "Hertz are physics. Physics does not read a radio grin, converterpath\n"
        "Install the jumper. That is the thesis, jumperseam",
        "Electro claps on a converter that actually converts\n"
        "Analog bass under a seam a neighboring pool can energize\n"
        "Nill Bye filing tie the island\n"
        "You can keep a market design and still take a jumper. Those are not enemies\n"
        "Enemies were a talking point. Talking points do not restore a pump\n"
        "Pumps need watts. Watts can be local jackets and imported seams\n"
        "Both. Both is an engineering sentence, neighborwatt\n"
        "I want both funded in the same season, not a presser that picks a prettier villain, converterpath\n"
        "Villains are for hymns. Seams are for winter\n"
        "Winter is a calendar. Calendars are science you can hang\n"
        "Hang the tie-in date. Hang the drill with the neighbor\n"
        "Drills with neighbors are how you find the seam is real",
        "Uri already taught the isolated quiz. The quiz had a missing neighbor\n"
        "Put the neighbor back. That is not a surrender. That is a jumper cable\n"
        "Nill Bye posting tie the island\n"
        "Jumper cables are humble. Humble is allowed in a grid, jumperseam\n"
        "Humble grids still have pride. Pride is a wellhead with a jacket and a seam that works\n"
        "Working seams are progress you can measure in restored megawatts\n"
        "Megawatts are the unit. Units are how adults talk about a blackout\n"
        "Talk in units. Then build the path. Then drill the path\n"
        "Bring the jumper, lose the island-as-destiny story, neighborwatt\n"
        "Destiny is a hymn. Hardware is a fix\n"
        "Fixes photograph as substations, not as speeches\n"
        "Photograph the substation. Date the first import",
        "Keep the claps, print the seam\n"
        "Tie the island is a civic method: jacket on site, jumper to a neighbor, a drill in November\n"
        "Nill Bye keeping the intertie\n"
        "An island can be a market. It should not be a dare to physics\n"
        "Physics already scored the dare. Take the score. Build the path\n"
        "Paths are the install. Date the converter. Publish the neighbor contract\n"
        "Contracts are how watts know where to go at 3 a.m.\n"
        "3 a.m. is the test. Pass the test with a seam\n"
        "Seams are progress, converterpath\n"
        "Progress is a pump that still runs when the local bus stumbles\n"
        "Keep the pump. Keep the neighbor. Keep the jumper\n"
        "Tie the island is the whole install, jumperseam",
    ),
    outro="claps rest, jumperseam\nseam live\ncut\nyeah",
)

DECADE_LINES_LYRICS = format_diss_lyrics(
    intro="garage-shuffle\nNill Bye tracing a river",
    chorus=(
        "Decade lines\n"
        "Nill Bye on the census clock\n"
        "A decade used to mean a decade. Keep that meaning\n"
        "Fair is a census, not a text thread, enumerator. Fair is a river, not a donor\n"
        "Mid-season sketches are a weapon with a legend. Put the weapon down\n"
        "Your map waits for the count"
    ),
    verses=(
        "Redistricting is a census job. Census jobs have a clock, rivermap\n"
        "The clock is a decade. Keep the clock. That is the whole fairness technology\n"
        "Nill Bye tracing a river instead of a corridor through a city, onceperdecade\n"
        "Rivers are a geography. Geography is a better legend than a donor\n"
        "Donors can still speak. They should not draw. Drawing is a public act after a count\n"
        "After is the method. After is how a maze does not get rebuilt as a season\n"
        "Seasons are for campaigns. Maps are for a decade of ballots\n"
        "I want the decade. I want the count first. I want a line a voter can explain\n"
        "Explainable lines are science for a democracy\n"
        "Unexplainable earmuffs are a packing problem sold as a trophy, censusclock\n"
        "Do not sell the trophy. Sell a line that follows a river, rivermap\n"
        "Rivers are the install, onceperdecade",
        "Shuffled hats on a shape file that waited for the census\n"
        "Organ stab under a decade that still means ten years, censusclock\n"
        "Nill Bye filing decade lines\n"
        "Voters should move in trucks, not on paper, in the off-years, rivermap\n"
        "Off-year paper moves are a quiet raid. Quiet raids are optional. Make them illegal in the state code if the federal floor is thin, onceperdecade\n"
        "Floors can be thin. States can still write a thicker clock, censusclock\n"
        "Write it. Date it. Let a court have a bright line, rivermap\n"
        "Bright lines are how a mid-season text thread fails\n"
        "I want that failure. Failure of a raid is progress, onceperdecade\n"
        "Progress is a candidate running through a district a river could explain\n"
        "Bring the river, lose the maze\n"
        "The pixels already told on the hurry. Do not hurry",
        "A majority squeezed into fewer seats is a packing problem, not a reflection of a vote\n"
        "Reflection is a census. Reflection is not a request, censusclock\n"
        "Nill Bye posting decade lines\n"
        "Requests are for donors. Censuses are for people\n"
        "People get a map after they are counted, not when a boss wants a House\n"
        "Wanting a House is allowed. Wanting it via an off-year sketch is the cheat-code, rivermap\n"
        "Turn the cheat-code off in statute, onceperdecade\n"
        "Statutes are the install. Date the once-per-decade rule. Publish the shape files when the count lands\n"
        "Landing is a year ending in zero, plus the lag the Bureau needs\n"
        "Lags are science. Lags are not a season you skip because a text arrived\n"
        "Let the lag happen. Then draw. Then live with it for a decade\n"
        "Living with it is adulthood",
        "Keep the shuffle, print the once-per-decade\n"
        "Decade lines is a civic method: count, then draw, then wait\n"
        "Nill Bye keeping the clock, censusclock\n"
        "A decade is a technology. Keep the technology\n"
        "Technology is a calendar, a river, a file a voter can explain\n"
        "Explainable is the test. Pass the test. Date the next count\n"
        "Counts are how maps earn a new legend\n"
        "Legends should be geography, not a donor\n"
        "Keep the geography. Keep the ten years, rivermap\n"
        "Keep the maze in a museum\n"
        "Museums are for weapons with a legend you retired\n"
        "Decade lines is the whole install, onceperdecade",
    ),
    outro="garage hats sit, censusclock, cboscore\nriver holds\ncut",
)

RATEPAYER_BUS_LYRICS = format_diss_lyrics(
    intro="hardstyle-reverse\nNill Bye watt-counting the barn",
    chorus=(
        "Ratepayer bus\n"
        "Nill Bye on cost causation\n"
        "A server farm is a baseload with a PR team, costcausation\n"
        "Abatement is not a halo. Watts and water have a bill\n"
        "If they generate more than they eat, show the meter\n"
        "Your boom is a rate-hike unless the barn pays the draw"
    ),
    verses=(
        "First the tax break, then the towns learned the aquifer\n"
        "Learning is data. Data should have arrived before the red carpet\n"
        "Nill Bye watt-counting the barn as a tenant on the bus\n"
        "Tenants pay. Paying is cost causation. Causation is a civic science, barnbill\n"
        "If the campus eats transmission, the campus funds transmission\n"
        "If the campus drinks a well, the campus funds the well and the neighbor's remaining drop, costcausation\n"
        "Remaining drops are a common-pool. Common-pools need a meter and a price\n"
        "Prices are allowed to be high when the draw is 24-hour\n"
        "24-hour is a baseload. Baseloads do not get to wear a press-release halo\n"
        "Halos are for saints. Barns are for racks. Racks pay\n"
        "I install the meter. The meter is the thesis, watermeter\n"
        "Meters are how a boom does not become a rate-hike by surprise",
        "Reverse bass on a bill that actually lands on the campus\n"
        "Screech lead under an interconnect that is not a free on-ramp\n"
        "Nill Bye filing the ratepayer bus\n"
        "Uri already taught the watt math. Adding a 24-hour tenant without a bill is a second quiz\n"
        "Pass the quiz with a tariff the barn can see in advance\n"
        "Advance is how towns stop revolting after the carpet\n"
        "Revolts are data that the sequence was backwards. Reverse the sequence\n"
        "Sequence: meter, water study, bill, then the ribbon\n"
        "Ribbons are last. Last is the method we keep using because it works\n"
        "Bring the meter, lose the halo\n"
        "The aquifer already knew the draw. Price the draw\n"
        "Pricing is progress, barnbill",
        "Keep them off the community well if the study says the well cannot share\n"
        "Sharing is a number, not a pitch. Numbers can say no\n"
        "Nill Bye posting the ratepayer bus\n"
        "No is a valid output. No is how a town keeps a tap\n"
        "Taps are a civic product. Do not sell the product as an AI epicenter story without a bill\n"
        "Stories are allowed. Bills are required\n"
        "Required is a statute: cost causation, a water study, a published tariff\n"
        "Publish it. Date it. Let the barn decide if the boom still pencils\n"
        "Penciling is a market. Markets that skip the bill are a transfer\n"
        "Transfers from households to racks are a quiet raid\n"
        "Turn the raid into a tariff. Tariffs are honest\n"
        "Honest barns can still boom. Booms that pay are the install, costcausation",
        "Keep the reverse, print the meter\n"
        "Ratepayer bus is a civic method: cause, meter, bill, then ribbon\n"
        "Nill Bye keeping the household on the bus without a hidden passenger\n"
        "Hidden passengers are a PR team. PR teams are not a tariff\n"
        "I want the tariff. I want the study. I want the no if the no is the number\n"
        "Numbers are science. Science can still love a barn that pays\n"
        "Paying barns are progress, watermeter\n"
        "Progress is a tap that still works in August\n"
        "August is a test. Pass it with a well that was not promised to a rack for free\n"
        "Free was the halo. Retire the halo\n"
        "Date the first bill. Publish the first study\n"
        "Ratepayer bus is the whole install, barnbill",
    ),
    outro="bass rest, watermeter\nmeter ticks\ncut\nyeah",
)

OPEN_QUAD_LYRICS = format_diss_lyrics(
    intro="trance-gates\nNill Bye opening the forum",
    chorus=(
        "Open quad\n"
        "Nill Bye on the argument\n"
        "A student with a sign is not an invasion, tpmrule\n"
        "A chant is not a crossing. Time-place-manner is a forum tool\n"
        "Troopers don't grade a seminar. Helmets photograph. Hearings teach\n"
        "Your first tool is a clock and a mic, not a perimeter"
    ),
    verses=(
        "A campus is a forum with a clock. Clocks are how chants end without a cordon\n"
        "Cordon as a habit is a helmet looking for a next assignment\n"
        "Nill Bye opening the forum with time-place-manner that a dean can explain\n"
        "Explainable rules are science for speech. Unexplainable zip-ties are a stage, helmetlast\n"
        "Stages are for concerts. Quads are for arguments\n"
        "I want the argument. I want the mic. I want the clock that actually ends the night, tpmrule\n"
        "Nights that end are a feature. Features keep a seminar possible in the morning\n"
        "Mornings are the product of a university. Keep the product, stewardmic\n"
        "Keeping it does not require a trooper as the first tool, helmetlast\n"
        "First tools should be a steward, a time, a place, a manner\n"
        "Manners are not manners of tone. Manners are a map of where the chant can stand, tpmrule\n"
        "Maps are the install, stewardmic",
        "Gated pads on a mic that still turns on\n"
        "Rolling bass under a clock a steward can point at\n"
        "Nill Bye filing the open quad\n"
        "A sign is not an occupation of a state. Do not borrow a war-word for a chant, helmetlast\n"
        "War-words license force. Force is a last tool. Last is the method, tpmrule\n"
        "I want last to stay last. Last is how a Forty Acres stays a classroom\n"
        "Classrooms need a forum. Forums need a rule a student can read without a lawyer\n"
        "Readable rules are progress. Unreadable perimeters are a presser, stewardmic\n"
        "Pressers photograph helmets. Helmets are not a grade\n"
        "Do not grade a seminar with a riot shield, helmetlast\n"
        "Bring the clock, lose the zip-tie as a first move\n"
        "First moves are the tell. Make the first move a mic, tpmrule",
        "Local yes is a hearing. Hearings are slower than a demonstration zone with a shorter clock, stewardmic\n"
        "Shorter clocks can still be lawful. They should still be a forum, not a booking quota\n"
        "Nill Bye posting the open quad\n"
        "Booking quotas are a metric from a different shop. Do not import them to a quad\n"
        "Quads are for speech. Speech can be loud. Loud is not a crossing\n"
        "I want the loud and the morning class. Both. Both is an adult campus\n"
        "Adult campuses fund stewards, not only helmets\n"
        "Stewards are cheaper than a sequel cordon. Cheaper is allowed to be the argument\n"
        "The argument still ends at the same install, nightbed: a map, a clock, a mic, a last-tool force\n"
        "Last-tool force still exists. It just is not the opener\n"
        "Openers are the progress. Open the quad\n"
        "Open is the word. Keep it",
        "Keep the pads, print the time-place-manner\n"
        "Open quad is a civic method: map, clock, mic, helmet last\n"
        "Nill Bye keeping the forum\n"
        "A chant is a sentence. Sentences get a place to stand, helmetlast\n"
        "Standing places are the install. Date the map. Publish the clock, tpmrule\n"
        "Publish so a student can plan a sign without guessing a zip-tie\n"
        "Guessing is how forums die. Dying forums are optional\n"
        "Keep the forum. Keep the morning class. Keep the steward\n"
        "Keep the last tool last\n"
        "Last is the whole word, stewardmic\n"
        "The Forty Acres is not a stage for a helmet. It is a classroom with a lawn\n"
        "Open quad is the whole install, helmetlast",
    ),
    outro="trance pads sit, stewardmic\nmic on\ncut",
)

LEAD_OUT_LYRICS = format_diss_lyrics(
    intro="festival-trap\nfestival-crowd\nNill Bye pulling pipe",
    chorus=(
        "Wrench the tap\n"
        "Nill Bye on the service line\n"
        "A neurotoxin in a tap is a measurement you can end with a wrench\n"
        "EPA already wrote the replacement. Fund it. Dig it. Date it\n"
        "Blood-lead is a number. Numbers fall when the pipe leaves the ground\n"
        "Your progress is a trench and a new line"
    ),
    verses=(
        "Lead service lines are a 19th-century install still drinking in a 21st-century kitchen\n"
        "Kitchens are a civic product. The product should not dose a child, bloodleaddelta\n"
        "Nill Bye pulling pipe as a public-health method, worstfirst\n"
        "EPA's Lead and Copper Rule Improvements already named replacement as the work, lslrtrench\n"
        "Work is a trench, a new line, a flush, a test, bloodleaddelta\n"
        "Tests are blood and water. Both should fall. Falling is the science, worstfirst\n"
        "I want the fall. I want the inventory of lines published so a block can see the queue\n"
        "Queues that hide are how a quiet dose continues\n"
        "Continue is optional. Make it optional by digging\n"
        "Digging is not glamorous. Digging is a civilization of care you can photograph as a trench\n"
        "Photograph the trench. Date the first block. Publish the blood-lead delta\n"
        "Deltas are the thesis, lslrtrench",
        "Festival 808 on a wrench that actually turns\n"
        "Crowd-bed under a block that got the new line first because the number was worst\n"
        "Nill Bye filing wrench the tap\n"
        "Worst-first is a triage. Triage is science. Do not reverse it for a ribbon in a richer zip\n"
        "Zips are not a health method. Blood-lead is a health method, bloodleaddelta\n"
        "I want the method. I want the crew. I want the year-by-year replacement clock, worstfirst\n"
        "Clocks are how a rule becomes a pipe on a truck\n"
        "Trucks are the implementation desk. Fund the trucks. Staff the trench\n"
        "Trenches are cheaper than a lifetime of a neurotoxin\n"
        "Cheaper is allowed to be the argument. The argument still ends at the same install, lslrtrench, nightbed\n"
        "Install the line. Flush the tap. Test the tap\n"
        "Bring the wrench, lose the quiet dose",
        "A filter is a bridge. A replacement is the destination\n"
        "Do not let the bridge become the policy. The policy is the trench\n"
        "Nill Bye posting wrench the tap\n"
        "Bridges can still ship while the trench is queued. Queue in public\n"
        "Public queues are how a block knows it is not forgotten\n"
        "Forgotten blocks are how a neurotoxin becomes a geography\n"
        "Geographies of dose are optional. Un-write them with a map of lines\n"
        "Maps are science. Maps plus a wrench are progress, bloodleaddelta\n"
        "Progress is a kid whose blood-lead fell because a pipe left the dirt\n"
        "Kids are not a talking point. Kids are the reason the number exists\n"
        "Keep the reason. Keep the wrench. Keep the worst-first, worstfirst\n"
        "The kitchen already knew the tap was the test, lslrtrench",
        "Keep the 808, print the replacement clock, bloodleaddelta\n"
        "Wrench the tap is a civic method: inventory, worst-first, trench, test, publish the delta\n"
        "Nill Bye keeping the wrench\n"
        "A neurotoxin is not a vibe. It is a metal you can take out of the ground\n"
        "Take it out. Date the last line in the worst census tract\n"
        "Tracts are a map. Maps are how a closer stays honest\n"
        "Honest closers still have a bass. The bass can celebrate a trench\n"
        "Celebrating a trench is allowed. That is raw progress, worstfirst\n"
        "Raw progress is a tap that does not dose\n"
        "Do not dose. Dig. Replace. Test, lslrtrench\n"
        "Three verbs. Civilization is verbs with a wrench\n"
        "Wrench the tap is the whole install, bloodleaddelta",
    ),
    outro="festival stop, lslrtrench\ntap clean\ncut\nyeah",
)


DISS_PROGRESS_CLUB: tuple[DissExample, ...] = (
    _ex(
        "duty-switch",
        "duty switch",
        140,
        647,
        "duty-switch command-post fix",
        DUTY_SWITCH_LYRICS,
        "dark trap",
        "808 bass",
        "rapid hi-hats",
        "half-time",
    ),
    _ex(
        "article-one",
        "article one",
        148,
        653,
        "article-one tariff fix",
        ARTICLE_ONE_LYRICS,
        "rage",
        "distorted 808",
        "laser hats",
    ),
    _ex(
        "for-cause-lock",
        "for-cause lock",
        132,
        659,
        "for-cause-lock Fed fix",
        FOR_CAUSE_LOCK_LYRICS,
        "phonk",
        "cowbell",
        "drifted 808",
        "crunchy sample",
    ),
    _ex(
        "ig-notice",
        "ig notice",
        145,
        661,
        "ig-notice watchdog fix",
        IG_NOTICE_LYRICS,
        "trap",
        "808 bass",
        "rapid hats",
        "dark pads",
    ),
    _ex(
        "counsel-stays",
        "counsel stays",
        126,
        673,
        "counsel-stays Sixth fix",
        COUNSEL_STAYS_LYRICS,
        "house",
        "four-on-the-floor",
        "piano stab",
        "sidechain bass",
    ),
    _ex(
        "prevailing-wage",
        "prevailing wage",
        174,
        677,
        "prevailing-wage labor-file fix",
        PREVAILING_WAGE_LYRICS,
        "drum and bass",
        "amen break",
        "sub reese",
    ),
    _ex(
        "merits-syllabus",
        "merits syllabus",
        140,
        683,
        "merits-syllabus calendar fix",
        MERITS_SYLLABUS_LYRICS,
        "jersey club",
        "chopped percussion",
        "bed squeaks",
        "kick drums",
    ),
    _ex(
        "unofficial-sort",
        "unofficial sort",
        148,
        691,
        "unofficial-sort three-room fix",
        UNOFFICIAL_SORT_LYRICS,
        "future bass",
        "supersaw",
        "pitched synth chords",
        "808 bass",
    ),
    _ex(
        "clemency-file",
        "clemency file",
        132,
        701,
        "clemency-file triage fix",
        CLEMENCY_FILE_LYRICS,
        "techno",
        "dry kick",
        "hat offbeats",
        "acid line",
    ),
    _ex(
        "congress-the-wing",
        "congress the wing",
        140,
        709,
        "congress-the-wing preservation fix",
        CONGRESS_THE_WING_LYRICS,
        "dubstep",
        "wobble bass",
        "half-time snare",
    ),
    _ex(
        "tie-the-island",
        "tie the island",
        128,
        719,
        "tie-the-island intertie fix",
        TIE_THE_ISLAND_LYRICS,
        "electro house",
        "analog bass",
        "clap on 2 and 4",
    ),
    _ex(
        "decade-lines",
        "decade lines",
        130,
        727,
        "decade-lines census-clock fix",
        DECADE_LINES_LYRICS,
        "UK garage",
        "shuffled hats",
        "organ stab",
        "sub bass",
    ),
    _ex(
        "ratepayer-bus",
        "ratepayer bus",
        150,
        733,
        "ratepayer-bus cost-causation fix",
        RATEPAYER_BUS_LYRICS,
        "hardstyle",
        "reverse bass",
        "screech lead",
    ),
    _ex(
        "open-quad",
        "open quad",
        138,
        739,
        "open-quad forum fix",
        OPEN_QUAD_LYRICS,
        "trance",
        "gated pads",
        "rolling bass",
        "pickup drum fill",
    ),
    _ex(
        "wrench-the-tap",
        "wrench the tap",
        150,
        743,
        "wrench-the-tap pipe-replacement fix",
        LEAD_OUT_LYRICS,
        "festival trap",
        "808 bass",
        "crowd-bed",
    ),
)

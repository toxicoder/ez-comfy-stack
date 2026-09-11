"""Progress-pack 180s Nill Bye takes (non-trap, non-EDM beds).

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

PROGRESS_PHASE = 7


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
        "series": "progress",
        "title": title,
        "tags": nill_tags(*tag_parts, bpm=bpm),
        "bpm": bpm,
        "duration": DISS_DURATION_S,
        "seed": seed,
        "phase": PROGRESS_PHASE,
        "prefix": nill_output_prefix(title, PROGRESS_PHASE),
        "description": _progress_desc(take),
        "lyrics": lyrics,
    }


WINTERIZE_WELLS_LYRICS = format_diss_lyrics(
    intro="yeah\nflange kit\nNill Bye weatherizing",
    chorus=(
        "Winterize wells\n"
        "Nill Bye on the missing gas rule\n"
        "EOP-012 jackets the generator\n"
        "Wells still sit outside NERC\n"
        "Write the production rule in a state house\n"
        "Your chain passes the cold quiz"
    ),
    verses=(
        "Uri taught the isolated bus a physics class\n"
        "Four million dark, pumps dead, hertz falling\n"
        "Nill Bye splitting the ladder on purpose, nercsheet\n"
        "EOP-012-3 is FERC-approved freeze protection for generating units\n"
        "October one, twenty-twenty-five, the electric half went mandatory\n"
        "Biennial filings through thirty-four. That half has a docket\n"
        "Natural Gas Act 717(b) still leaves production and gathering out\n"
        "Out means no NERC jacket on the wellhead yet\n"
        "Elliott's after-action asked Congress or a state to write that half\n"
        "Texas Railroad Commission mapped critical fuel in twenty-twenty-two\n"
        "A map of some wells is not a reliability standard\n"
        "I want the missing half named as the install, wellhead",
        "Boom-bap dust on a two-rung ladder\n"
        "Vinyl on a generator that already got a coat, flangekit\n"
        "Nill Bye filing the NERC sheet where it actually reaches\n"
        "Bulk-power units: heat-trace, procedures, a cold-weather constraint you can audit\n"
        "Close R8 carve-outs that call a retrofit unduly burdensome without a photo\n"
        "Twenty-four and forty-eight month clocks in R7 still need a date on steel\n"
        "FERC can watch the electric rung. The gas rung needs a legislature\n"
        "A thermal plant is a chain. The uninsulated well is still off the federal rung, heattrace\n"
        "S.B. 3 jackets specified ERCOT wholesale generators in-state\n"
        "PUCT 25.55 is summer and winter prep for that set\n"
        "Set is not the whole fuel chain. Publish the miss on gathering lines, nercsheet\n"
        "Science is a jacket on the unit and a statute on the well",
        "Neighbor watts help when the island is a choice, wellhead\n"
        "Winterize the unit on site. Write the well rule next door, flangekit\n"
        "Nill Bye posting the winterize wells as the gap that remains\n"
        "You do not need a miracle market. You need EOP-012 on the generating unit\n"
        "And a production-gathering rule that NERC is not allowed to mint\n"
        "Allowed is 717(b). So the state house or Congress holds the pen\n"
        "A drill in November is cheap. A blackout is a ledger of funerals\n"
        "I want the generator warm under EOP-012\n"
        "I want the well producing under a rule that actually names it\n"
        "The front does not read a radio grin, heattrace\n"
        "The front reads a unit procedure and a wellhead torque spec\n"
        "Two specs. Two shops. One cold morning",
        "Keep the dusty drums, print EOP-012 and 717(b), nercsheet\n"
        "A civic fix is a standard where jurisdiction exists and a bill where it does not\n"
        "Nill Bye keeping the two-rung weatherization ladder\n"
        "Gas froze in the wellhead. The wellhead still needs the coat from a legislature\n"
        "Generators got the federal coat. Keep tightening Attachment 1\n"
        "Ready is the word. Ready is not a vibe, wellhead\n"
        "Ready is a clamp on the unit and a statute on the gathering pipe\n"
        "Bring the jacket where FERC can reach. Bring the bill where it cannot\n"
        "The next Uri is a calendar, not a rumor\n"
        "Calendars are science you can hang on a wall, flangekit\n"
        "Hang both rungs. Torque the flange the jurisdiction can actually reach\n"
        "Winterize wells is the missing rung, heattrace",
    ),
    outro="flange warm\nhertz hold\ncut\nyeah",
)

REGISTERED_REPORT_LYRICS = format_diss_lyrics(
    spoken=(
        "Preregister the plan\n"
        "Then run the plan\n"
        "Results cannot un-write the protocol\n"
        "A null is a result\n"
        "Open science"
    ),
    intro="notebook click\nNill Bye preregistering",
    chorus=(
        "Registered report\n"
        "Nill Bye on the protocol lock\n"
        "Write the method before the p lights up\n"
        "A surprise finding still has to survive the plan\n"
        "Center for Open Science already built the door\n"
        "Your results cannot un-write the protocol"
    ),
    verses=(
        "A hypothesis is a bet you place in public\n"
        "Placing it after the scatterplot is a costume, osfhash\n"
        "Nill Bye preregistering the protocol lock\n"
        "Sample size, exclusion rules, the analysis script, protocolock\n"
        "Date-stamped, hashed, sitting where a reviewer can fetch it\n"
        "Then you run the study. Then you report what arrived\n"
        "If the null arrives, the null is the result\n"
        "A null is not a failure. A null is a measurement\n"
        "Journals that only print fireworks teach fireworks\n"
        "Registered reports print the plan, then the weather\n"
        "Weather is honest. Fireworks are a selection effect\n"
        "I want the plan locked before the first pipette",
        "Boom-bap snare on an OSF timestamp\n"
        "Upright bass under a method that cannot sneak a new outcome\n"
        "Nill Bye filing the registered report, prereg\n"
        "You can still explore. You label the explore as explore\n"
        "Exploratory is a door. Confirmatory is a different door, osfhash\n"
        "Mixing the doors is how a field eats its own confidence\n"
        "ASA already said a p is not a truth machine, protocolock\n"
        "A p is a tail. Tails need a prewritten question\n"
        "Write the question. Then look. Then tell the truth, prereg\n"
        "Retraction is a cleanup. Preregistration is a design, osfhash\n"
        "Design is cheaper than cleanup\n"
        "I install the lock. The lock is kindness to the next lab",
        "Replication is not a vibe. It is a second protocol\n"
        "A second lab, a second n, the same hashed plan, protocolock\n"
        "Nill Bye posting the registered report, prereg\n"
        "If it does not replicate, the first paper still did its job, osfhash\n"
        "The job was a claim with a method, not a brand, protocolock\n"
        "Brands hate nulls. Methods collect them, prereg\n"
        "Collecting nulls is how a map gets coastlines\n"
        "A map with only peaks is a brochure\n"
        "I want a coastline. You can keep the brochure for a poster session\n"
        "The session is not the record. The OSF is the record\n"
        "Bring a hash, lose the secret outcome-swap\n"
        "The pipette already knew the honest order, osfhash",
        "Keep the dry booth, print the protocol lock\n"
        "Open science is a door with a timestamp, not a slogan, protocolock\n"
        "Nill Bye keeping the registered report, prereg\n"
        "Write it, lock it, run it, report it\n"
        "Four verbs. That is a civilization of measurement\n"
        "A field that skips the lock will sell certainty it did not buy\n"
        "Certainty is expensive. You buy it with n and a plan, osfhash\n"
        "Buy it. Then share the weather even when it is gray\n"
        "Gray weather is still data\n"
        "Data is how we stop guessing in public\n"
        "Guessing in public is a presser, protocolock\n"
        "The protocol lock already closed the presser, prereg",
    ),
    outro="hash sits\nplan holds\ncut",
)

NAMED_UNCERTAINTY_LYRICS = format_diss_lyrics(
    intro="brushed snare, intervalband\nNill Bye intervaling",
    chorus=(
        "Named uncertainty\n"
        "Nill Bye on the interval\n"
        "A point estimate without a range is a costume number\n"
        "n of many, not a sample of swagger\n"
        "A null is a result with a confidence band\n"
        "Your claim wears the interval it earned"
    ),
    verses=(
        "A mean is a location. A range is a honesty tax, honestytax\n"
        "Pay the tax. Print the interval beside the mean\n"
        "Nill Bye intervaling the civic number too\n"
        "Polls, death counts, watt shortfalls, caseloads\n"
        "A headline that strips the range is a costume, nullband\n"
        "Costumes move faster. Intervals keep you from lying by accident\n"
        "A single case is a story. n of many is a measurement\n"
        "I want the many. I want the band. I want the caveat in the same sentence, intervalband\n"
        "A caveat is not weakness. A caveat is the science talking\n"
        "Talk like that in a hearing and the hearing gets smarter\n"
        "Talk like a point-estimate prophet and the hearing buys a myth, honestytax\n"
        "Myths are cheap. Intervals are the install, nullband",
        "Jazz hop brushes on a confidence band\n"
        "Muted trumpet under a null that still gets a paragraph\n"
        "Nill Bye filing named uncertainty\n"
        "If the interval covers zero, say so without a funeral\n"
        "Zero covered is information. It is not a scandal\n"
        "A scandal is pretending the mean stood alone\n"
        "ASA already warned that a p is not a license to swagger\n"
        "Swagger is a point with the interval shaved off\n"
        "Leave the interval. Name the model. Name the missingness\n"
        "Missingness is a third number hiding in the table, intervalband\n"
        "Tables that hide it are not tables. They are ads\n"
        "I print the ads out of the lab",
        "Civic life needs the same tax, honestytax\n"
        "A budget forecast without a band is a hymn, nullband\n"
        "Nill Bye posting named uncertainty\n"
        "Score the grid, the ward, the caseload with ranges\n"
        "Then decide. Decision under a range is adulthood\n"
        "Decision under a single digit is a rally trick, intervalband\n"
        "I want adulthood in the briefing room, honestytax\n"
        "Briefings can still be short. Short and honest is a craft\n"
        "Craft is a sentence that carries its own doubt\n"
        "Doubt is a tool. Certainty without a band is a costume, nullband\n"
        "Bring the band, lose the prophet voice\n"
        "The interval already did the talking",
        "Keep the brushes, print the honesty tax, intervalband\n"
        "Named uncertainty is a civic method, not a stats elective\n"
        "Nill Bye keeping the interval\n"
        "n of many, a range, a null that still sits in the paper\n"
        "That trio is how a field stops eating itself, honestytax\n"
        "It is also how a state stops governing on a rounded myth, nullband\n"
        "Rounded myths feel like leadership\n"
        "Leadership is a decision that can name its own error\n"
        "Name it. Then act. Then measure again, intervalband\n"
        "Again is the loop. The loop is progress, honestytax\n"
        "Progress is not a presser. It is a band that shrinks when the n grows\n"
        "Shrink the band. That is the whole install, nullband",
    ),
    outro="brushes rest\nband sits\ncut\nyeah",
)

SCIF_ONLY_LYRICS = format_diss_lyrics(
    intro="metal clamp\nNill Bye compartmenting",
    chorus=(
        "Scif only\n"
        "Nill Bye on the compartment\n"
        "A bathroom is not a vault\n"
        "Markings, courier, log, a door that means it\n"
        "A mind is not a declassifier\n"
        "Your paper lives where the lock lives"
    ),
    verses=(
        "Need-to-know is a geometry, not a feeling\n"
        "A SCIF has a door, a perimeter, a visitor list, cfr2001\n"
        "Nill Bye compartmenting the country's paper\n"
        "Banners stay on the folder. Couriers stay on the manifest\n"
        "32 CFR 2001 already wrote the handling\n"
        "Handling is boring. Boring is how secrets survive\n"
        "A club hallway is a traffic pattern. Traffic is the opposite of need-to-know\n"
        "Put the stack in the compartment. Date the log. Badge the escort\n"
        "If it is not marked, it is not moving\n"
        "If it is moving, it is in a pouch that can be counted\n"
        "Counting is the science. Vibes are how a chandelier becomes a file room, compartment\n"
        "I install the door. The door is the whole thesis, pouchlog",
        "Industrial percussion on a vault that actually vaults\n"
        "Distorted bass under a courier with a receipt, cfr2001\n"
        "Nill Bye filing scif only\n"
        "Telepathy is not a records act. A log is a records act, compartment\n"
        "You declassify with a process, a packet, a date, a notice\n"
        "A process can be slow. Slow is a feature when the paper can start a war, pouchlog\n"
        "Start-a-war paper does not sit by a toilet\n"
        "It sits behind a lock that was built for it\n"
        "Build the lock. Fund the lock. Inspect the lock\n"
        "Inspection is kindness to the next administration\n"
        "The next administration should inherit a compartment, not a pile, cfr2001\n"
        "Piles are how photos become the catalog, compartment",
        "Empty folders with banners still on them are a confession\n"
        "The confession is: the handling lagged the ego\n"
        "Nill Bye posting scif only\n"
        "Ego does not get a closet. The closet gets a SCIF or it gets empty\n"
        "Empty is allowed. Empty is a legal storage plan, pouchlog\n"
        "A legal storage plan is a sentence you can read in a hearing without flinching\n"
        "I want that sentence. I want the badge reader. I want the escort log, cfr2001\n"
        "I want a courier who can say where the pouch slept\n"
        "Sleeping locations are data. Data is how you pass an audit\n"
        "Audits are not persecution. Audits are how a republic keeps its paper\n"
        "Bring the compartment, lose the chandelier library\n"
        "The lock already knew the difference",
        "Keep the metal, print the 32 CFR\n"
        "A civic fix is a door with a standard, not a mind-power\n"
        "Nill Bye keeping the compartment\n"
        "Mark it, log it, pouch it, lock it\n"
        "Four verbs again. Civilization is verbs with receipts\n"
        "Receipts are how you sleep. Secrets are how other people sleep\n"
        "Other people's sleep is the national-security product, compartment\n"
        "Protect the product. The club can sell memberships without the stacks\n"
        "Memberships are a business. Stacks are a duty\n"
        "Duty lives in a SCIF\n"
        "Install the SCIF. Date the first log, pouchlog\n"
        "Scif only is the whole install, cfr2001",
    ),
    outro="clamp set\nlog dated\ncut",
)

HEARING_FIRST_LYRICS = format_diss_lyrics(
    intro="tuba swell\nNill Bye docketing the hearing",
    chorus=(
        "Hearing first\n"
        "Nill Bye on the withholding\n"
        "A plane is a last step, not a first shrug\n"
        "Facilitate means work, not a foreign-sovereign alibi\n"
        "The file that already won a shield keeps the shield\n"
        "Your process is the plane's permission slip"
    ),
    verses=(
        "A withholding is a court-shaped shield already on the file, withholdflag\n"
        "You do not step over a shield because a parking lot is convenient\n"
        "Nill Bye docketing the hearing first, tarmaclast\n"
        "Notice, counsel, a judge, a record that can be read later\n"
        "Later is how a republic proves it did not shrug, flowchartred\n"
        "A shrug that puts a person on a plane is not an error you can brand, withholdflag\n"
        "Call it an administrative miss if you must. Then reverse the miss\n"
        "Reverse means facilitate. Facilitate means work, tarmaclast\n"
        "Work is phone calls, paper, a return, a new hearing on the merits\n"
        "Merits are facts. Facts need a room with a clock and a transcript\n"
        "I want that room before the tarmac\n"
        "The tarmac is a last tool, not a personality",
        "Brass cadence on a process that can find its own file, flowchartred\n"
        "Snare under a child who should not be the first witness to a shrug, withholdflag\n"
        "Nill Bye filing hearing first, tarmaclast\n"
        "I will not punch the person. I will punch the skipped step\n"
        "The skipped step is the whole constitutional insult\n"
        "Fix the step and the insult shrinks\n"
        "Train the officers on the withholding flag\n"
        "A flag in the database is cheaper than a mega-prison sequel, flowchartred\n"
        "Cheaper and cleaner. Cleaner is a hearing, withholdflag\n"
        "If the government already lost the shield fight, it does not get a plane as a do-over\n"
        "Do-overs are for sports. Files are for law, tarmaclast\n"
        "Install the flag. Date the training. Publish the miss-rate, flowchartred",
        "A social post is not a holding. A holding is facilitate\n"
        "Obey the holding. Then try the case you actually have\n"
        "Nill Bye posting hearing first, withholdflag\n"
        "If you have a charge, bring a charge in a courtroom\n"
        "If you have a removal, bring a removal after a hearing, tarmaclast\n"
        "If you have neither, you have a shrug, and a shrug is not a policy\n"
        "Policy is a flowchart that a night officer can follow\n"
        "Flowcharts are science for a shop that moves people\n"
        "People are not dartboards. Dartboards are how sequels get ugly\n"
        "I want the flowchart. I want the withheld name to light up red\n"
        "Red is a stop. Stop is the install, flowchartred\n"
        "The parking lot already needed that red light, withholdflag",
        "Keep the tuba, print the withholding flag\n"
        "Hearing first is a civic method you can train in a week\n"
        "Nill Bye keeping the process, tarmaclast\n"
        "Notice, counsel, transcript, then the plane if the plane is still lawful\n"
        "Lawful is a word a bench can read without adjectives\n"
        "Adjectives from a bench are expensive. Buy fewer of them, flowchartred\n"
        "Buy them by skipping steps. Save them by installing steps\n"
        "Install the steps. That is progress you can photograph as a flowchart\n"
        "Photographs of flowcharts are not glamorous\n"
        "Glamour is optional. Process is not\n"
        "Bring the hearing, lose the shrug, withholdflag\n"
        "The shield already knew the order, tarmaclast",
    ),
    outro="tuba rest\nflag red\ncut\nyeah",
)

KEEP_THE_MATCH_LYRICS = format_diss_lyrics(
    intro="folk scrape, caseidrow\nNill Bye matching files",
    chorus=(
        "Keep the match\n"
        "Nill Bye on the family file\n"
        "A child is not a deterrent poster\n"
        "One case-id, two humans, a bed that can be found\n"
        "Reunification is a database, not a scavenger hunt\n"
        "Your memo owes the match it moved"
    ),
    verses=(
        "A prosecutorial switch can exist without a bus split\n"
        "The split is a choice. Un-choose it in the memo, reunifydesk\n"
        "Nill Bye matching files before anyone boards\n"
        "One case-id that follows the adult and the child, nightbed\n"
        "Wristbands, photos, a number a night officer can type\n"
        "If the number does not resolve, the bus does not move\n"
        "That stop is the whole child-welfare science, caseidrow\n"
        "OIG already counted what happens when the stop is missing\n"
        "Missing matches are not toughness. They are a lost file, reunifydesk\n"
        "A lost file is incompetence with a slogan, nightbed\n"
        "I want the slogan gone. I want the case-id\n"
        "I want a bed the database can find at 3 a.m.",
        "Acoustic guitar on a reunification table, caseidrow\n"
        "Shaker under a memo that keeps the family on one ticket\n"
        "Nill Bye filing keep the match\n"
        "Deterrence that uses a child is a lever pulled on someone who cannot vote the lever\n"
        "Put the lever down. Write family-unity as the default\n"
        "Default is a flowchart. Exceptions get a supervisor and a clock, reunifydesk\n"
        "Clocks are how exceptions do not become a season\n"
        "A season of lost matches is a policy confession\n"
        "Confess by installing the database, not by a later mercy presser, nightbed\n"
        "Mercy after the shock is a caption. Captions do not find children\n"
        "Databases find children. Fund the database. Staff the night desk, caseidrow\n"
        "Night desks are the install, reunifydesk",
        "I will not mock a child. I will mock a memo that treated a family as a poster, nightbed\n"
        "The fix is the memo, the id, the bed, the counsel\n"
        "Nill Bye posting keep the match\n"
        "Counsel for the parent. A guardian for the child. A court that can see both\n"
        "Seeing both is the minimum a state owes\n"
        "Owe it in the first hour, not after a scavenger hunt with lawyers\n"
        "Lawyers should not have to be detectives for a government's own bus\n"
        "Detectives are for crimes. This is a filing problem, caseidrow\n"
        "Filing problems have filing solutions\n"
        "Bring the case-id, lose the deterrent poster, reunifydesk\n"
        "The family was never a talking point, nightbed\n"
        "The family is two humans the file must be able to rejoin",
        "Keep the folk scrape, caseidrow, print the case-id\n"
        "Keep the match is a civic method you can ship as software\n"
        "Nill Bye keeping the reunification table, caseidrow\n"
        "One number, two names, a bed, a clock, a supervisor\n"
        "Five nouns. That is a civilization of care\n"
        "Care is not a vibe. Care is a row in a table that resolves\n"
        "If it does not resolve, the bus waits\n"
        "Waiting is cheaper than a lost child, reunifydesk\n"
        "Cheaper is allowed to be the argument\n"
        "The argument still ends at the same install, nightbed\n"
        "Install the row. Date the first resolve\n"
        "Keep the match is the whole install, caseidrow",
    ),
    outro="strings rest\nrow resolves\ncut",
)

HONEST_CENSUS_LYRICS = format_diss_lyrics(
    intro="train beat\nNill Bye counting households",
    chorus=(
        "Honest census\n"
        "Nill Bye on the count, apakitchentable\n"
        "A box that arrives after the want is a pretext\n"
        "APA wants a why that predates the want\n"
        "A scared household is a theft from a city\n"
        "Your questionnaire is a count, not a trapdoor"
    ),
    verses=(
        "A census is a map of who is here\n"
        "Money and seats ride the map. So the map has to be boring\n"
        "Nill Bye counting households without a trapdoor\n"
        "Boring is a short form that does not chill a kitchen table, enumerator\n"
        "Chill is a census error with a political use, apakitchentable\n"
        "Use is the tell. The tell is a why that arrived after the want\n"
        "Roberts already named that why contrived\n"
        "Contrived is an adjective a Court spends rarely. Spend it, then obey it\n"
        "Obey it by not shopping a civil-rights costume for a scarecrow\n"
        "The VRA is a sword against dilution. It is not a scarecrow\n"
        "I want the sword used as a sword\n"
        "I want the count used as a count",
        "Country fiddle on a questionnaire that does not flinch a household\n"
        "Steel guitar under an APA file that sequences want and why, apakitchentable\n"
        "Nill Bye filing honest census\n"
        "If you need citizenship data, build a method that does not shrink the count\n"
        "Shrinking the count steals from a city that already showed up\n"
        "Showing up is the civic act. Do not punish it with a box, undercountplan\n"
        "A box at census scale is a policy machine, enumerator\n"
        "Machines need a why that exists in the original record\n"
        "Original is the science. Sequels are how pretext gets dressed\n"
        "Dressing is not a method. Sequence is a method, apakitchentable\n"
        "Sequence the want after a true operational need, or drop the box, undercountplan\n"
        "Dropping the box is allowed. It is how the 2020 count survived",
        "Apportionment is too important to be a chill experiment\n"
        "Experiments belong in a lab with consent. A census is not that lab\n"
        "Nill Bye posting honest census\n"
        "Print the form. Fund the enumerators. Translate the form\n"
        "Knock the door. Count the people who live there\n"
        "Living there is the jurisdiction the clause already named\n"
        "I want that clause left alone at the kitchen table, enumerator\n"
        "Kitchen tables fill in honest forms when the form is not a trap\n"
        "Traps produce undercounts. Undercounts produce crooked money\n"
        "Crooked money is a quiet raid\n"
        "Bring a boring form, lose the scarecrow\n"
        "The Court already sequenced the want and the why, apakitchentable",
        "Keep the train beat, print the APA order, undercountplan\n"
        "Honest census is a civic method: count, do not chill\n"
        "Nill Bye keeping the questionnaire\n"
        "A why before the want, a form that does not shrink a city, enumerator\n"
        "That pair is progress you can put in a Bureau handbook\n"
        "Handbooks are not glamorous. Handbooks are how a decade stays fair\n"
        "Fair is a census, not a text thread, enumerator\n"
        "Fair is a count that can survive a kitchen-table pause, apakitchentable\n"
        "Pause, then check the box that is actually about who lives there\n"
        "Who lives there is the whole job, undercountplan\n"
        "Do the job. Date the form. Publish the undercount plan, enumerator\n"
        "Honest census is the whole install, apakitchentable",
    ),
    outro="fiddle rest, undercountplan\ncount stands, undercountplan\ncut\nyeah",
)

PARIS_SEAT_LYRICS = format_diss_lyrics(
    intro="harmonica air\nNill Bye sitting the NDC",
    chorus=(
        "Paris seat\n"
        "Nill Bye on the Article Four pledge\n"
        "Celsius does not watch cable, ndcslope\n"
        "A contribution is a number you bring to the table\n"
        "Walking out is not a rewrite. Sitting is a rewrite\n"
        "Your empty chair is a policy. Fill it"
    ),
    verses=(
        "An accord is a nationally determined contribution\n"
        "You can argue the contribution. You cannot argue the thermometer, articlefour\n"
        "Nill Bye sitting the NDC at the table, gigaton\n"
        "Article Four is a pledge you can tighten at the next meeting\n"
        "Meetings are where rewrites happen. Letters are where chairs get thrown\n"
        "I want the seat. I want the inventory. I want the next tighter number\n"
        "Tighter is a slope. Slopes are science, articlefour\n"
        "A presser is not a slope. A presser is a caption on a walkout\n"
        "Captions do not un-emit a gigaton\n"
        "Gigatons are the unit. Units are how adults talk about air\n"
        "Talk in units. Then stay for the inventory review\n"
        "Reviews are how pledges become more than posters",
        "Blues shuffle on a chair that stays filled\n"
        "Guitar sting under a thermometer that does not take a party whip\n"
        "Nill Bye filing the paris seat\n"
        "Physics is not a party in the accord. Physics is the reason the accord exists\n"
        "Argue with the contribution. Do not argue with the reason, ndcslope\n"
        "The reason is radiative physics you can put in a textbook\n"
        "Textbooks do not care who is in the Rose Garden\n"
        "The Rose Garden can still host a tighter NDC\n"
        "Hosting a tighter NDC is leadership that shows up as a number\n"
        "Numbers can be attacked. That is allowed. Attack them at the table, gigaton\n"
        "The table is the method. The letter is the refusal of the method, articlefour\n"
        "I install the seat. The seat is the install, ndcslope",
        "Gap years still emit. Sitting down later does not un-emit them, gigaton\n"
        "So sit now. Inventory now. Tighten now\n"
        "Nill Bye posting the paris seat\n"
        "Coal towns needed a transition plan, not an empty chair as a brand, articlefour\n"
        "Plans have retraining, timelines, replacement watts\n"
        "Replacement watts can be nuclear uprates, wind, gas with a jacket, storage\n"
        "A mix is an engineering sentence. A letter is a political sentence, ndcslope\n"
        "I want the engineering sentence funded\n"
        "Fund it, then bring the NDC that matches the fund\n"
        "Matching is honesty. Honesty is a slope you can defend\n"
        "Bring a slope, lose the empty-chair brand, gigaton\n"
        "Celsius already graded the clip, articlefour",
        "Keep the harmonica, print Article Four\n"
        "Paris seat is a civic method: stay, inventory, tighten\n"
        "Nill Bye keeping the chair\n"
        "A contribution is a number. A number is a promise with units\n"
        "Promises with units can be checked. Checking is the science, ndcslope\n"
        "Checking is also the diplomacy. They are the same loop\n"
        "Loop: sit, count, tighten, sit again, gigaton\n"
        "Again is progress. Progress is not a walkout video\n"
        "Videos are easy. Slopes are work, articlefour\n"
        "Do the work. Date the inventory. Publish the next NDC\n"
        "The parties already know how to meet\n"
        "Fill the chair. That is the whole install, ndcslope",
    ),
    outro="harp rest\nslope holds\ncut",
)

QUALIFIED_DIVEST_LYRICS = format_diss_lyrics(
    intro="rhodes wash, usc208\nNill Bye boxing the till",
    chorus=(
        "Qualified divest\n"
        "Nill Bye on the blind instrument\n"
        "The office is a conflict machine. Take the till off the desk\n"
        "No ticker, no canopy, no SKU-as-status\n"
        "A donation after the booking is not a blind anything\n"
        "Your duty starts when the asset leaves the room"
    ),
    verses=(
        "18 U.S.C. 208 is a boring conflict rule\n"
        "Boring is the point. The office should not have a second receiving line, trustee\n"
        "Nill Bye boxing the till before the oath\n"
        "A qualified instrument with an independent trustee\n"
        "The trustee does not take captions. The trustee sells\n"
        "Selling is how a canopy stops being a foreign folio\n"
        "A folio with a flag is an emolument question even if you invoice it\n"
        "Invoicing itemizes a conflict. It does not clean it\n"
        "Clean is gone. Gone is a sale, a trust, a wall the president cannot peek through, awningdark\n"
        "Peeking is the market. The market opened last time on an awning\n"
        "I want the awning dark. I want the ticker gone\n"
        "I want the SKU un-launched",
        "Lo-fi drums on an asset that left the room, usc208\n"
        "Vinyl under a trustee who does not need a social post, trustee\n"
        "Nill Bye filing qualified divest\n"
        "A souvenir that wires is a gift with extra steps\n"
        "Extra steps are still a stream from anyone, including a foreign desk, awningdark\n"
        "Wallets shrug. Folios at least had names. Shrugging is worse\n"
        "Worse is not a brand. Worse is a national-security blind spot you built\n"
        "Do not build it. Do not launch a float three days before the oath\n"
        "Three days is a tell. The tell is: the office and the till were going to share a desk, usc208\n"
        "Unshare them. That is the whole ethics cartoon, inverted into a fix\n"
        "Inversion is allowed when the cartoon was the problem, trustee\n"
        "Install the wall. Date the sale. Publish the trustee",
        "A million-dollar pathway is a checkout, not a statute, awningdark\n"
        "Statutes have criteria. Checkouts have SKUs\n"
        "Nill Bye posting qualified divest\n"
        "If Congress wants a capital visa, Congress writes EB-5 rules, usc208\n"
        "Rules are boring. Boring is the opposite of a launch photo\n"
        "Launch photos belong in a catalog, not an EO\n"
        "I want the EO unused for a family float\n"
        "I want the hotel lease not sitting under a tenant who is also the landlord's boss\n"
        "That sentence was the cartoon. The fix is: do not be the tenant\n"
        "Do not be the ticker. Do not be the SKU\n"
        "Bring a trustee, lose the canopy\n"
        "The desk already had enough conflicts without a second till, trustee",
        "Keep the rhodes, print the 208\n"
        "Qualified divest is a civic method: the asset leaves, the duty stays\n"
        "Nill Bye keeping the wall, awningdark\n"
        "Sell, trust, wall, publish\n"
        "Four verbs. The office can survive without a souvenir coin\n"
        "Souvenirs are for tourists. The desk is for the republic\n"
        "The republic does not need a family float to feel loved\n"
        "Love is not a ticker. Love is a conflict rule you obey\n"
        "Obey it early. Early is before the oath, not after the first booking\n"
        "Bookings are the stream. Cut the stream\n"
        "Cut it, date it, let the trustee work in the dark\n"
        "Dark is how a blind instrument earns the word blind",
    ),
    outro="rhodes sit\nwall holds\ncut\nyeah",
)

RETURN_PDF_LYRICS = format_diss_lyrics(
    intro="soft keys\nNill Bye stacking PDFs",
    chorus=(
        "Return pdf\n"
        "Nill Bye on the disclosure stack\n"
        "Net tax is a number. Total tax is a different number\n"
        "A closed return is not a rebuttal. A PDF is a rebuttal\n"
        "The office is a conflict machine. Show the machine the 1040\n"
        "Your ritual is a stack the public can price"
    ),
    verses=(
        "Candidates release so the public can price the conflict, jctcolumn\n"
        "Pricing needs a PDF, not an audit costume, disclosureurl\n"
        "Nill Bye stacking PDFs before the first debate\n"
        "JCT already showed how to read net tax beside total tax, form1040\n"
        "Net tax of seven hundred fifty in a year is a tick, not a myth, jctcolumn\n"
        "A line that small beside a billionaire brand is a footnote the brand owes\n"
        "Owe the footnote in public. That is the ritual\n"
        "Rituals are boring. Boring is how conflict machines get inspected\n"
        "Inspect the depreciation, the write-off, the cash story versus the taxable story, disclosureurl\n"
        "Two stories can both be true in different ledgers\n"
        "The public is allowed to see both ledgers\n"
        "Seeing is the install, form1040",
        "Neo-soul keys on a 1040 that actually lands\n"
        "Warm bass under a ritual that does not need a rally to replace it\n"
        "Nill Bye filing the return pdf\n"
        "Audit is a process. It is not a costume for a skip\n"
        "If an audit is running, say so and still release the years that are closed, jctcolumn\n"
        "Closed years are data. Data is how a conflict gets priced\n"
        "Priced is not smeared. A dataset does not smear. It sits, disclosureurl\n"
        "Sitting is what PDFs do. Let them sit on a government page, form1040\n"
        "A government page is a better venue than a leak\n"
        "Leaks happen when the ritual is skipped, jctcolumn\n"
        "Do not skip. Date the upload. Check the redactions for actual secrets\n"
        "Redactions are a tool. They are not a black square over the whole return",
        "A patriot brand that pays a three-digit federal line still owes the stack, disclosureurl\n"
        "Owing the stack is not persecution. It is the job interview\n"
        "Nill Bye posting the return pdf\n"
        "The office is not a private matter. The 1040 is the interview take-home\n"
        "Take-homes are allowed to be ugly. Ugly is information\n"
        "Information is how voters stop guessing the conflict\n"
        "Guessing is a presser. Pressers are not disclosure\n"
        "Disclosure is a URL with six years of PDFs\n"
        "Six is a habit. Habits are how rituals survive a cycle\n"
        "Bring the URL, lose the audit costume, form1040\n"
        "The Times should not have to be the disclosure office, jctcolumn\n"
        "The candidate can be the disclosure office. That is the upgrade",
        "Keep the keys, print the JCT columns\n"
        "Return pdf is a civic method: net, total, years, a URL\n"
        "Nill Bye keeping the stack, disclosureurl\n"
        "Show the machine the 1040. Let the public do arithmetic\n"
        "Arithmetic is not a smear. Arithmetic is a civic skill\n"
        "Skill is cheaper than a portrait assembled from leaks\n"
        "Leaks are a failure of the ritual. Run the ritual\n"
        "Run it early. Early is before the convention, not after the oath\n"
        "After the oath is late. Late is how conflicts get a head start\n"
        "Do not give them a head start\n"
        "Upload, date, leave the PDF sitting\n"
        "Return pdf is the whole install, form1040",
    ),
    outro="keys rest, form1040\nURL sits\ncut",
)

CASEWORK_SCREEN_LYRICS = format_diss_lyrics(
    intro="8-bit tick\nNill Bye casing the file",
    chorus=(
        "Casework screen\n"
        "Nill Bye on the person-level file\n"
        "A roster is a map. A screen is a person, a visa, a fact\n"
        "Airports should not be the implementation desk of a blunt tool\n"
        "Precision is interviews, data, appeals\n"
        "Your method names a file, not a continent-color"
    ),
    verses=(
        "A security method names a person, a visa, a fact\n"
        "A roster names a map and calls the map a threat, personfile\n"
        "Nill Bye casing the file at the person level\n"
        "Interviews, watchlists that actually match, a right to appeal\n"
        "Appeals are how you do not outsource screening to a continent-color\n"
        "Color is not a screen. Color is a photograph of a policy\n"
        "Photographs made the first weekend loud. Loud is not safer\n"
        "Safer is casework that survives the first bench because it was casework\n"
        "If the method were vetting, the memo would vet, visaappeal\n"
        "Vetting is slower. Slower is a feature when the cost of a miss is a life, personfile\n"
        "The cost of a blunt tool is a terminal full of people who were never the miss\n"
        "I install the file. The file is the method, visaappeal",
        "Chiptune square-lead on a visa that has a fact pattern\n"
        "Eight-bit drums under an appeal that can actually reverse a miss\n"
        "Nill Bye filing the casework screen\n"
        "A faith is not a security file. I will not borrow a smear to write a screen\n"
        "A screen does not need a smear. A screen needs data and a human reviewer\n"
        "Humans with training, not a Friday roster that stuns an airport\n"
        "Friday rosters are how you get lawyers on floors\n"
        "Lawyers on floors are a design tell. Redesign\n"
        "Redesign is: match the name, check the visa, read the fact, write the reason, reviewer\n"
        "Reasons can be appealed. Rosters cannot be appealed except as a class\n"
        "Class tools are for true classes. People are not a class because a map is handy\n"
        "Handy is not a method. Handy is a headline, personfile",
        "Green-card holders in a blunt net is the implementation you do not repeat\n"
        "Do not repeat it. Write the exception into the first draft\n"
        "Nill Bye posting the casework screen\n"
        "The first draft should survive a bench because it named files, not countries as a mood, visaappeal\n"
        "Moods are for rallies. Files are for ports\n"
        "Ports can be strict. Strict and precise can share a sentence, reviewer\n"
        "Share it. Fund the interviewers. Fund the translators. Fund the appeal clock, personfile\n"
        "Clocks that actually run are how precision stays strict\n"
        "Strict without a clock is just a roster with better lighting\n"
        "Bring the file, lose the continent-color\n"
        "The terminals already graded the blunt tool, visaappeal\n"
        "Grade the next memo by whether a single person can appeal it",
        "Keep the blips, print the person-level file, reviewer\n"
        "Casework screen is a civic method: fact, visa, appeal\n"
        "Nill Bye keeping the reviewer\n"
        "A map can inform a risk model. A map cannot be the whole model\n"
        "Models that collapse to a roster will stun an airport again, personfile\n"
        "Again is optional. Make it optional by installing casework\n"
        "Casework is interviews and data and a reason on a page, visaappeal\n"
        "Pages can be wrong. Pages can be reversed. That is the adult version of strict\n"
        "Adult strict is progress, reviewer\n"
        "Progress is not a total shutdown of a faith as a campaign tape\n"
        "Tapes are not screens. Screens are files\n"
        "Casework screen is the whole install, personfile",
    ),
    outro="blips halt, reviewer\nfile sits\ncut\nyeah",
)

PUBLIC_CAMPUS_LYRICS = format_diss_lyrics(
    intro="neon pad\nNill Bye totaling unit funding",
    chorus=(
        "District door\n"
        "Nill Bye on the district that takes every child\n"
        "A transfer to the already-private is not a market\n"
        "Unit funding follows the child who still needs the public door\n"
        "Choice that loots the campus is a raid with a brochure\n"
        "Your ESA can wait. The district cannot"
    ),
    verses=(
        "A public door has to take every child who shows up\n"
        "That is the job. The job is expensive and it is the point, hardcase\n"
        "Nill Bye totaling unit funding at the campus that cannot pick\n"
        "Private pews can pick. Public doors cannot. Fund the cannot\n"
        "An ESA that follows the already-private kid first is a subsidy, not a rescue\n"
        "Rescues start at the campus that is required to enroll the hard case, mondayopen\n"
        "Hard cases are the civic product. Do not siphon the product to a sector that can say no\n"
        "Saying no is allowed in a pew school. It is not allowed at the public door, unitfunding\n"
        "So the dollar should be heavier at the door that cannot say no\n"
        "Heavier is a formula. Formulas are science for a budget\n"
        "I want that formula in statute, hardcase\n"
        "I want the rural campus to keep the teacher when the formula runs",
        "Synthwave gates on a district that still has a science lab\n"
        "Analog bass under a formula that does not raid the lab for a pew\n"
        "Nill Bye filing district door, mondayopen\n"
        "Out-of-state cash for a primary is a donor errand, not a parent bill of rights\n"
        "Parent bills of rights can exist. They should not be a pipe off the tax roll, unitfunding\n"
        "Pipes off the tax roll need a statute that names who still gets served\n"
        "Served means transportation, hard-case services, English learners, a counselor\n"
        "Those lines live on the district door. Keep them alive\n"
        "Alive is a teacher, a nurse, a bus, a lab\n"
        "Labs are how a state grows the next measurement crew\n"
        "Bring the unit, lose the raid brochure\n"
        "The already-private kid was never the emergency, hardcase",
        "Local boards should not be gutted to pass a loyalty test, mondayopen\n"
        "Loyalty tests are for caucuses. Campuses are for children\n"
        "Nill Bye posting district door, unitfunding\n"
        "If you want a market, the market has to take the hard case too\n"
        "If it will not take the hard case, it is not a market. It is a skim\n"
        "Skims are allowed to be named. Name them. Then fund the door, hardcase\n"
        "The door is the progress. Progress is a kid who can still walk in Monday\n"
        "Monday is a test you can photograph without a donor\n"
        "Photograph the lab. Photograph the nurse. Photograph the bus\n"
        "Those photos are the opposite of a brochure\n"
        "Brochures sell a pew. The bus serves a county\n"
        "Serve the county. Date the formula. Publish the unit",
        "Keep the neon, print the unit funding\n"
        "District door is a civic method: the door that cannot pick gets the dollar\n"
        "Nill Bye keeping the district\n"
        "Every child, a formula, a lab, a nurse, a bus\n"
        "Five nouns again. Civilization is nouns you can fund\n"
        "Fund them in statute so a primary cannot loot them, mondayopen\n"
        "Primaries are for candidates. Campuses are for the hard case, unitfunding\n"
        "The hard case is the point of a public door, hardcase\n"
        "Keep the point. Keep the teacher. Keep the lab\n"
        "Keep the Monday that still opens\n"
        "Open is the install, mondayopen\n"
        "District door is the whole install, unitfunding",
    ),
    outro="pads sit\ndoor open, unitfunding\ncut",
)

LEVY_IN_CODE_LYRICS = format_diss_lyrics(
    intro="organ rise\nNill Bye drafting the roll",
    chorus=(
        "Levy in code\n"
        "Nill Bye on the appraisal statute\n"
        "A cut you can campaign is not a cut you passed, rolldelta\n"
        "Until the roll actually moves, the hymn is a sticker\n"
        "No income tax is a bumper. The levy is the body of the song\n"
        "Your kitchen table wants a statute, not a choir"
    ),
    verses=(
        "A homestead story that skips the renter is a choir, not a cut, appraisaldistrict\n"
        "Write the cut in the code. Date the effective. Publish the roll delta\n"
        "Nill Bye drafting the roll so the kitchen table can check it\n"
        "Appraisal districts are the machine. Machines need a statute, not a stump\n"
        "Stumps photograph. Statutes move the levy\n"
        "I want the levy moved for the household that actually pays it\n"
        "Paying it is the civic act. Do not hide it under a no-income-tax sticker, renterclause\n"
        "Stickers are allowed. They are not the body of the song\n"
        "The body is the appraisal, the recapture, the local squeeze\n"
        "Name those in the bill. Then pass the bill. Then show the new roll, rolldelta\n"
        "Showing the roll is the science, appraisaldistrict\n"
        "Science is a PDF of parcels, not a hymn, renterclause",
        "Gospel organ on a statute that actually moves a number\n"
        "Hand claps under a kitchen table that can find the delta\n"
        "Nill Bye filing levy in code, rolldelta\n"
        "Local governments catch the blame when the cap arrives without the funding\n"
        "If you cap, you replace. Replacement is a line in the same bill\n"
        "A line in the same bill is adulthood\n"
        "Adulthood is not a tour in quarter four about affordability\n"
        "Affordability is a roll that moved in January\n"
        "January is a date. Dates are how hymns become laws\n"
        "Bring the date, lose the hymnal\n"
        "The renter is still in the song. Write the renter in\n"
        "Writing the renter in is the whole fairness test, appraisaldistrict",
        "Oil can pay a severance story. Households pay the monthly truth, renterclause\n"
        "Monthly truth is the levy. Put the levy in code where a clerk can apply it\n"
        "Nill Bye posting levy in code, rolldelta\n"
        "Clerks are the implementation desk. Give them a formula, not a choir packet\n"
        "Choir packets are for Sundays. Formulas are for appraisal season\n"
        "Season is a calendar. Calendars are science you can hang\n"
        "Hang the effective date. Hang the delta. Hang the renter clause, appraisaldistrict\n"
        "Three hangings. That is a bill\n"
        "A bill that cannot hang those three is still a hymn, renterclause\n"
        "I want a bill. The table already knows the key\n"
        "The key is the monthly number, not the slogan, rolldelta\n"
        "Match the monthly number to a statute and the slogan can rest",
        "Keep the organ, print the roll delta\n"
        "Levy in code is a civic method: pass, date, publish, check\n"
        "Nill Bye keeping the appraisal\n"
        "A cut in code is a cut. A cut in a stump speech is a promise\n"
        "Promises are cheap. Rolls are not\n"
        "Move the roll. Then campaign on the PDF\n"
        "PDFs are allowed to be the campaign\n"
        "That campaign would be progress, appraisaldistrict\n"
        "Progress is a kitchen table that can find the new number without a choir\n"
        "Without a choir is the test, renterclause\n"
        "Pass the test. Date the statute. Publish the parcels\n"
        "Levy in code is the whole install, rolldelta",
    ),
    outro="organ sit\nroll moved\ncut\nyeah",
)

FOURTEENTH_CLAUSE_LYRICS = format_diss_lyrics(
    intro="timpani low\nNill Bye reading the clause",
    chorus=(
        "Fourteenth clause\n"
        "Nill Bye on the citizenship sentence\n"
        "Subject to the jurisdiction is a sentence, not a vibe, slowdoor\n"
        "Wong Kim Ark already walked this ground\n"
        "A pen does not edit who counts. An amendment does\n"
        "Your clause survived. Keep it"
    ),
    verses=(
        "A clause older than the brand, written after a war about who counts, barbarahold\n"
        "Counting is the civic science. The sentence already did the counting rule\n"
        "Nill Bye reading the citizenship sentence as the install, wongkim\n"
        "Born here, subject to the jurisdiction, a citizen at birth\n"
        "That is the holding Barbara reaffirmed. Keep the holding\n"
        "Keep it without a day-one pen. Pens are fast. Who-counts is slow on purpose, barbarahold\n"
        "Slow is two-thirds and the states. That is the method for a change\n"
        "If you want a change, bring an amendment. Do not bring a January stack, slowdoor\n"
        "January stacks are EOs. EOs are not conventions\n"
        "I want the convention process if the sentence is to move\n"
        "Until then the sentence stands, including the children a pen aimed at\n"
        "Aimed is a verb I keep on the pen, not the child, wongkim",
        "Cinematic strings on a clause that does not take a poll as a rewrite\n"
        "Low brass under Wong Kim Ark walking the same ground in the nineteenth century\n"
        "Nill Bye filing the fourteenth clause, barbarahold\n"
        "A century is not a rumor you skip because a rally likes a pen, slowdoor\n"
        "Jurisdiction is a legal word with a history, not a mood, wongkim\n"
        "Moods do not write the Fourteenth. Congress and the states did, the hard way, wongkim\n"
        "The hard way is the point of an amendment, barbarahold\n"
        "Speed is the point of an EO. Speed lost, and that is the method working\n"
        "Working methods should be kept. Keep the clause. Keep the slow door, barbarahold\n"
        "The slow door is how a republic does not let a tenant rewrite the lease, slowdoor\n"
        "The lease is the people. The people include the children born here\n"
        "Include them. That is the install, wongkim",
        "I will not punch a child. I will keep the sentence that already included them, barbarahold\n"
        "Keeping is a civic act. Keeping is also a legal act, slowdoor\n"
        "Nill Bye posting the fourteenth clause, wongkim\n"
        "Train the agencies to obey the holding\n"
        "Obey is a flowchart: born here, subject to the jurisdiction, issue the paper\n"
        "Paper is a certificate, not a test case as a personality\n"
        "Personalities can still argue for an amendment. Argue it the hard way, barbarahold\n"
        "The hard way is public, slow, and bicameral\n"
        "Bicameral is a pulse. A pulse is how who-counts questions stay adult\n"
        "Adult is progress. Progress is not a day-one surprise\n"
        "Bring an amendment if you want a change\n"
        "Until then keep the clause. Date the agency memo that obeys Barbara",
        "Keep the timpani, print the sentence, slowdoor\n"
        "Fourteenth clause is a civic method: obey the holding, use the slow door for change\n"
        "Nill Bye keeping the citizenship sentence, wongkim\n"
        "A poll is not two-thirds. A pen is not a convention\n"
        "Two-thirds is the science of a hard change\n"
        "Hard changes are allowed. They are just not EO-shaped\n"
        "EO-shaped tools bounce off this sentence. That bounce is a feature\n"
        "Features should be kept. Keep the bounce. Keep the children in the sentence, barbarahold\n"
        "Keep Wong Kim on the shelf beside Barbara\n"
        "Shelves are how a republic remembers\n"
        "Remember, obey, amend only the hard way, slowdoor\n"
        "Fourteenth clause is the whole install, wongkim",
    ),
    outro="timpani rest, wongkim\nclause stands, slowdoor\ncut",
)

ONE_COLLEGE_LYRICS = format_diss_lyrics(
    intro="live-kit stomp, governorseal\nNill Bye certifying one slate",
    chorus=(
        "One college\n"
        "Nill Bye on the certified slate\n"
        "A governor's seal is the ascertainment\n"
        "A photocopy with a Sharpie energy is not a second college\n"
        "Electoral Count Reform Act already named the one file\n"
        "Your extras can sit down. The canvass already stood"
    ),
    verses=(
        "Dec fourteen the real electors meet at noon\n"
        "Noon is a clock. Clocks are how a college stays one college\n"
        "Nill Bye certifying one slate with a governor's seal, noonmeeting\n"
        "The Electoral Count Reform Act already wrote the objection rules tighter\n"
        "Tighter is a feature. Implement it. Fund the clerks who run it\n"
        "Clerks are the implementation desk of a republic's math, ecrafile\n"
        "Math is a canvass you live with. Living with it is adulthood\n"
        "Adulthood is not a hallway extras meeting with a costume ballot\n"
        "Costume ballots are how a memo tries to mint a fork\n"
        "Forks are not in the Act. The Act is one file, governorseal\n"
        "I install the one file. The one file is the thesis, noonmeeting\n"
        "A party chair is not a printer for electors, ecrafile",
        "Rap-rock stomp on a seal that actually issued\n"
        "Overdriven guitar under a canvass that already ran three times\n"
        "Nill Bye filing one college\n"
        "Find is a verb with a destination. Count is a verb with a total\n"
        "Use count. Then live with the total\n"
        "Living with the total is how a secretary of state stays a civic officer\n"
        "Civic officers need backup: paper, audits, a public canvass, a statute that names one slate\n"
        "Name it. Train the electors. Date the meeting. Publish the certificate\n"
        "Certificates are boring. Boring is how extras die as exhibits instead of as a government, ecrafile\n"
        "I want them to stay exhibits. Exhibits are for museums and dockets\n"
        "Governments are for one college\n"
        "Bring the seal, lose the photocopy",
        "Pence was never a fork. The Act does not sell forks\n"
        "Do not ask a vice president to launder extras. Ask a governor to certify the winner\n"
        "Nill Bye posting one college\n"
        "Winners are allowed to be the other party. That is the design, governorseal\n"
        "The design is a clock, a seal, a meeting, a count in January that is a math problem, noonmeeting\n"
        "Math problems are not memos. Memos that mint slates are a costume shop\n"
        "Close the shop. Keep the Act. Keep the clerks\n"
        "Keep the three-count habit in close states because habit is a civic science, ecrafile\n"
        "Habits that survive a pressure-call are the product, governorseal\n"
        "The product is a total you can stand by\n"
        "Stand by the numbers. That sentence is the whole install, noonmeeting\n"
        "The tape already taught the opposite. Do not teach the opposite again, ecrafile",
        "Keep the stomp, print the Reform Act, governorseal\n"
        "One college is a civic method: seal, noon, one file, live with it\n"
        "Nill Bye keeping the canvass\n"
        "A second college is not a theory. It is a costume, noonmeeting\n"
        "Costumes can be studied. They should not be run, ecrafile\n"
        "Run the one file. Date the certificate. Publish the electors\n"
        "Publishing is how extras fail in daylight\n"
        "Daylight is progress, governorseal\n"
        "Progress is a January that is boring because the math already happened\n"
        "Boring Januarys are a feature\n"
        "Keep the feature. Keep the seal. Keep the noon meeting\n"
        "One college is the whole install, noonmeeting",
    ),
    outro="kit halt\nseal sits\ncut\nyeah",
)


DISS_PROGRESS: tuple[DissExample, ...] = (
    _ex(
        "winterize-wells",
        "winterize wells",
        88,
        563,
        "winterize-wells grid fix",
        WINTERIZE_WELLS_LYRICS,
        "boom bap",
        "hip-hop",
        "dusty drums",
        "vinyl crackle",
        "sampled piano stab",
    ),
    _ex(
        "registered-report",
        "registered report",
        86,
        569,
        "registered-report open-science fix",
        REGISTERED_REPORT_LYRICS,
        "boom bap",
        "hip-hop",
        "dry snare",
        "upright bass",
    ),
    _ex(
        "named-uncertainty",
        "named uncertainty",
        90,
        571,
        "named-uncertainty interval fix",
        NAMED_UNCERTAINTY_LYRICS,
        "jazz hop",
        "brushed drums",
        "upright bass",
        "muted trumpet",
    ),
    _ex(
        "scif-only",
        "scif only",
        108,
        577,
        "scif-only compartment fix",
        SCIF_ONLY_LYRICS,
        "industrial hip-hop",
        "metal percussion",
        "distorted bass",
    ),
    _ex(
        "hearing-first",
        "hearing first",
        112,
        587,
        "hearing-first process fix",
        HEARING_FIRST_LYRICS,
        "brass band",
        "tuba bass",
        "snare cadence",
    ),
    _ex(
        "keep-the-match",
        "keep the match",
        82,
        593,
        "keep-the-match family-unity fix",
        KEEP_THE_MATCH_LYRICS,
        "folk",
        "acoustic guitar",
        "shaker",
        "room mic",
    ),
    _ex(
        "honest-census",
        "honest census",
        100,
        599,
        "honest-census count fix",
        HONEST_CENSUS_LYRICS,
        "country",
        "steel guitar",
        "fiddle",
        "train beat",
    ),
    _ex(
        "paris-seat",
        "paris seat",
        74,
        601,
        "paris-seat NDC fix",
        PARIS_SEAT_LYRICS,
        "blues",
        "guitar sting",
        "shuffled snare",
        "harmonica",
    ),
    _ex(
        "qualified-divest",
        "qualified divest",
        86,
        607,
        "qualified-divest conflict fix",
        QUALIFIED_DIVEST_LYRICS,
        "lo-fi hip-hop",
        "dusty drums",
        "rhodes",
        "vinyl crackle",
    ),
    _ex(
        "return-pdf",
        "return pdf",
        84,
        613,
        "return-pdf disclosure fix",
        RETURN_PDF_LYRICS,
        "neo-soul",
        "rhodes",
        "soft snare",
        "warm bass",
    ),
    _ex(
        "casework-screen",
        "casework screen",
        100,
        617,
        "casework-screen vetting fix",
        CASEWORK_SCREEN_LYRICS,
        "chiptune",
        "square lead",
        "8-bit drums",
    ),
    _ex(
        "district-door",
        "district door",
        104,
        619,
        "district-door funding fix",
        PUBLIC_CAMPUS_LYRICS,
        "synthwave",
        "analog bass",
        "gated snare",
        "neon pads",
    ),
    _ex(
        "levy-in-code",
        "levy in code",
        78,
        631,
        "levy-in-code statute fix",
        LEVY_IN_CODE_LYRICS,
        "gospel",
        "organ",
        "hand claps",
        "choir vowels",
    ),
    _ex(
        "fourteenth-clause",
        "fourteenth clause",
        76,
        641,
        "fourteenth-clause citizenship fix",
        FOURTEENTH_CLAUSE_LYRICS,
        "cinematic",
        "strings",
        "timpani",
        "low brass",
    ),
    _ex(
        "one-college",
        "one college",
        168,
        643,
        "one-college canvass fix",
        ONE_COLLEGE_LYRICS,
        "rap rock",
        "live drums",
        "overdriven guitar",
        "crowd stomp",
    ),
)

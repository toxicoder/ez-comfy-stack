"""Author Audio Rack JSON catalogs. Not imported by pytest.

Run from repo root:

  python3 tests/python/_build_audio_catalogs.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "custom_nodes" / "ez_prompt_enhance" / "audio"

_STOP = frozenset(
    "the a an of to and in on at as with without from for by into onto over under "
    "is are was were be being been this that audio music track mix so then that "
    "sit sits sitting still".split()
)
_VARIANT = frozenset(
    {
        "left",
        "right",
        "up",
        "down",
        "slow",
        "fast",
        "mild",
        "heavy",
        "near",
        "far",
        "high",
        "low",
        "wide",
        "tight",
        "soft",
        "hard",
        "warm",
        "cool",
        "dry",
        "wet",
        "short",
        "long",
    }
)


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if word not in _STOP and len(word) > 2}


def _norm(text: str) -> set[str]:
    return {word for word in _tokens(text) if word not in _VARIANT}


def _assert_unique(axis_id: str, rows: list[dict[str, Any]]) -> None:
    """Fail the builder when two clauses on one axis are synonym padding.

    Args:
        axis_id: Axis key.
        rows: Technique dicts.

    Raises:
        SystemExit: overlap at or above 0.85, or fewer than 100 rows.
    """
    if len(rows) < 100:
        raise SystemExit(f"{axis_id} {len(rows)} < 100")
    bags = [(str(row["id"]), _norm(str(row["clause"]))) for row in rows]
    for idx, (left_id, left) in enumerate(bags):
        if len(left) < 6:
            continue
        for right_id, right in bags[idx + 1 :]:
            if len(right) < 6:
                continue
            union = left | right
            if not union:
                continue
            overlap = len(left & right) / len(union)
            if overlap >= 0.85:
                raise SystemExit(
                    f"{axis_id} {left_id} vs {right_id} overlap {overlap:.2f}"
                )


def _entry(
    tid: str,
    label: str,
    clause: str,
    tags: str,
    *,
    lyrics_form: str = "",
    lyrics_form_inst: str = "",
    bpm: str = "",
    vocal_ok: bool = True,
    instrumental_ok: bool = True,
    podcast_ok: bool = True,
    conflicts: tuple[str, ...] = (),
    meta_tags: tuple[str, ...] = (),
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": tid,
        "label": label,
        "clause": clause if clause.endswith(".") else f"{clause}.",
        "tags": tags,
        "lyrics_form": lyrics_form,
        "lyrics_form_inst": lyrics_form_inst,
        "bpm": bpm,
        "vocal_ok": vocal_ok,
        "instrumental_ok": instrumental_ok,
        "podcast_ok": podcast_ok,
        "conflicts": list(conflicts),
        "tags_meta": list(meta_tags),
    }
    return row


def _dump(name: str, rows: list[dict[str, Any]]) -> None:
    axis_id = name.replace(".json", "")
    _assert_unique(axis_id, rows)
    path = OUT / name
    path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({len(rows)})")


def _rows(items: list[tuple[Any, ...]], *, kind: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in items:
        tid, label, clause, tags = item[:4]
        extra = item[4] if len(item) > 4 else {}
        if not isinstance(extra, dict):
            extra = {}
        kwargs = dict(extra)
        kwargs.setdefault("meta_tags", (kind,))
        out.append(_entry(str(tid), str(label), str(clause), str(tags), **kwargs))
    return out


def genre_style() -> list[dict[str, Any]]:
    items: list[tuple[Any, ...]] = [
        ("gen_boom_bap", "Boom bap", "Dusty kick-snare pocket with chopped-sample grammar and air between the hits", "boom bap, hip-hop", {"conflicts": ("gen_four_on_floor", "frm_drop_first")}),
        ("gen_trap", "Trap", "Sliding 808s and rapid hats under a half-time rap grid", "trap, 808 bass, rapid hi-hats", {"conflicts": ("gen_boom_bap",)}),
        ("gen_lofi_hiphop", "Lo-fi hip-hop", "Tape-hiss hop with sleepy drums and a Rhodes that never quite locks", "lo-fi hip-hop, dusty drums, rhodes"),
        ("gen_drill", "Drill", "Sliding bass and stuttered hats on a menacing bounce", "drill, sliding bass, stutter hats", {"podcast_ok": False}),
        ("gen_jazz_rap", "Jazz rap", "Walking upright and brushed ride under spoken-leaning bars", "jazz rap, upright bass, brushed drums"),
        ("gen_gospel_rap", "Gospel rap", "Church-organ swells and choir pads under a testimony cadence", "gospel rap, organ, choir pads"),
        ("gen_spoken_hop", "Spoken hop", "Lecture cadence over a spare boom-bap bed with almost no hook candy", "spoken word hip-hop, spare drums"),
        ("gen_hybrid_trap", "Hybrid trap", "Warped bass drops into trap drums without a rap vocal", "warped hybrid-trap, trap drums", {"vocal_ok": False, "podcast_ok": False, "conflicts": ("gen_boom_bap",)}),
        ("gen_four_on_floor", "Four-on-floor house", "Kick on every quarter with offbeat hats and a club body", "house, four-on-the-floor", {"conflicts": ("gen_boom_bap",), "podcast_ok": False}),
        ("gen_deep_house", "Deep house", "Warm round kick, filtered chords, and late-night pad bloom", "deep house, warm kick, filtered chords"),
        ("gen_techno", "Techno", "Hypnotic machine pulse with industrial hats and a dry warehouse kick", "techno, industrial hats, warehouse kick", {"podcast_ok": False}),
        ("gen_dnb", "Drum and bass", "Amen-chop energy at sprint tempo with a rolling bassline", "drum and bass, rolling bass", {"podcast_ok": False}),
        ("gen_jungle", "Jungle", "Chopped break collage with ragga-leaning bass and sudden drops", "jungle, chopped breaks", {"podcast_ok": False}),
        ("gen_uk_garage", "UK garage", "Shuffled two-step kick and skippy hats with a vocal chop as percussion", "uk garage, two-step, shuffled hats"),
        ("gen_dubstep", "Dubstep", "Half-time wobble bass and a sparse snare that lands like a door", "dubstep, wobble bass", {"podcast_ok": False}),
        ("gen_uk_bass", "UK bass", "Weight-first club music with broken drums and sub pressure", "uk bass, broken drums, sub pressure", {"podcast_ok": False}),
        ("gen_ambient", "Ambient", "Slow evolving pads with almost no grid, air as the instrument", "ambient, evolving pads, no drums"),
        ("gen_drone", "Drone", "Held tones that beat against each other until the room changes color", "drone, held tones, beating harmonics"),
        ("gen_downtempo", "Downtempo", "Late-night pulse under cinematic chords, drums that refuse to hurry", "downtempo, late-night pulse"),
        ("gen_trip_hop", "Trip hop", "Dusty break, smeared vinyl, and a bassline that walks through smoke", "trip hop, dusty break, smeared vinyl"),
        ("gen_synthwave", "Synthwave", "Analog-leaning supersaws, gated snare, and neon arpeggios", "synthwave, gated snare, analog supersaw"),
        ("gen_industrial", "Industrial", "Metal hits, distorted kick, and machine hiss as rhythm", "industrial, metal hits, distorted kick", {"podcast_ok": False}),
        ("gen_post_punk", "Post-punk", "Dry snare, chorus bass, and angular guitar that refuses prettiness", "post-punk, chorus bass, angular guitar"),
        ("gen_shoegaze", "Shoegaze", "Washed guitars bury the grid; cymbals bloom instead of counting", "shoegaze, washed guitars, blooming cymbals"),
        ("gen_folk", "Folk", "Fingerpicked guitar, room mics, and a tempo that follows the lyric", "folk, fingerpicked guitar, room mics"),
        ("gen_country", "Country", "Tele-leaning twang, train beat, and a story told on the two and four", "country, train beat, twang guitar"),
        ("gen_bluegrass", "Bluegrass", "Scruggs-roll banjo, walking mandolin, and acoustic sprint chops", "bluegrass, banjo rolls, mandolin chops"),
        ("gen_blues", "Blues", "Twelve-bar shuffle, bent thirds, and a guitar that answers the vocal", "blues, twelve-bar shuffle, bent thirds"),
        ("gen_soul", "Soul", "Tambourine on two and four, stacked horns, and a pocket that leans back", "soul, tambourine, stacked horns"),
        ("gen_funk", "Funk", "Sixteenth guitar chick, slap bass ghosts, and a kick that talks", "funk, sixteenth guitar, slap bass"),
        ("gen_disco", "Disco", "Octave bass, four-floor kick, and string stabs that glitter on the offbeat", "disco, octave bass, string stabs", {"podcast_ok": False}),
        ("gen_afrobeat", "Afrobeat", "Interlocking guitars, talking-drum chatter, and a horn riff that never sits down", "afrobeat, interlocking guitars, talking drum"),
        ("gen_highlife", "Highlife", "Palm-wine guitar sparkle over a buoyant dance-band groove", "highlife, palm-wine guitar, dance-band groove"),
        ("gen_reggae", "Reggae", "Skank guitar on the offbeat, one-drop kick, and bass as the melody", "reggae, one-drop, offbeat skank"),
        ("gen_dancehall", "Dancehall", "Digital riddim bounce with a sparse kick and a chat-ready pocket", "dancehall, digital riddim"),
        ("gen_ska", "Ska", "Walking bass and offbeat chops at a bright clip", "ska, walking bass, offbeat chops"),
        ("gen_bossa", "Bossa nova", "Nylon guitar syncopation, soft shaker, and a whisper-grid samba cousin", "bossa nova, nylon guitar, soft shaker"),
        ("gen_samba", "Samba", "Surdo pulse, tamborim sparkle, and cavaquinho chatter", "samba, surdo, tamborim"),
        ("gen_cumbia", "Cumbia", "Guacharaca scrape, two-side bass, and a mild clave lilt", "cumbia, guacharaca, two-side bass"),
        ("gen_salsa", "Salsa", "Montuno piano, tumbao bass, and stacked timbale cascara", "salsa, montuno piano, tumbao bass"),
        ("gen_merengue", "Merengue", "Accordion-or-sax riff over a relentless two-step tambora", "merengue, tambora two-step"),
        ("gen_mambo", "Mambo", "Big-band brass punches and a mambo-bell pattern that drives dancers", "mambo, brass punches, mambo bell"),
        ("gen_tango", "Tango", "Bandoneon sighs, dramatic stops, and a walking threat in the bass", "tango, bandoneon, dramatic stops"),
        ("gen_flamenco", "Flamenco", "Palmas, rasgueado guitar, and a compas that snaps on twelve", "flamenco, palmas, rasgueado guitar"),
        ("gen_fado", "Fado", "Portuguese guitar shimmer under a lament that sits almost unmetered", "fado, portuguese guitar, lament"),
        ("gen_celtic", "Celtic reel", "Ornamented fiddle, bodhran pulse, and a drone that never quite cadences", "celtic, fiddle ornaments, bodhran"),
        ("gen_nordic_folk", "Nordic folk", "Hardanger-leaning overtones, frame drum, and cold open fifths", "nordic folk, open fifths, frame drum"),
        ("gen_brass_band", "Brass band", "Sousaphone pump, snare buzz, and stacked horns in the street", "brass band, sousaphone, street snare"),
        ("gen_marching", "Marching cadence", "Military snare rudiments and a bass-drum heartbeat in 2/4", "marching cadence, rudimental snare"),
        ("gen_choir_hymn", "Choir hymn", "SATB stack, organ pedal, and a fermata that waits on the text", "choir hymn, SATB, organ pedal"),
        ("gen_organ_liturgy", "Organ liturgy", "Pipe-organ mixtures and a pedal point that holds the room", "organ liturgy, pipe organ, pedal point"),
        ("gen_piano_ballad", "Piano ballad", "Una-corda piano, rubato, and a left-hand that barely marks time", "piano ballad, una corda, rubato"),
        ("gen_acoustic_singer", "Acoustic singer", "Capo'd steel-string, close vocal, and a foot-tap instead of drums", "acoustic singer-songwriter, steel-string"),
        ("gen_barbershop", "Barbershop", "Close four-part harmony with ringing overtones and a tag ending", "barbershop, close harmony, ringing overtones"),
        ("gen_doo_wop", "Doo-wop", "Bass vocal as the kick, finger snaps, and a nonsense-syllable bed", "doo-wop, finger snaps, vocal bass"),
        ("gen_sixties_soul", "Sixties soul", "Horn stabs, tambourine, and a sixties-soul pocket that leans on two and four", "sixties soul, horn stabs, tambourine"),
        ("gen_northern_soul", "Northern soul", "Four-floor stomp, stacked backing shouts, and a key change that lifts the floor", "northern soul, four-floor stomp"),
        ("gen_quiet_storm", "Quiet storm", "Soft-focus R&B, muted guitar, and a bass that never raises its voice", "quiet storm, muted guitar, soft r&b"),
        ("gen_neo_soul", "Neo soul", "Behind-the-beat drums, Rhodes, and stacked airy doubles that never quite land on the grid", "neo soul, rhodes, behind-the-beat drums"),
        ("gen_rnb_night", "Night R&B", "Sparse 808, velvet chords, and a sung hook that sits late", "r&b, sparse 808, velvet chords"),
        ("gen_boom_bap_jazz", "Boom-bap jazz", "Crate drums under a live-leaning horn loop and walking bass", "boom bap, jazz horns, walking bass"),
        ("gen_boom_bap_soul", "Boom-bap soul", "Chopped vocal-pad chords on a dusty 88 grid", "boom bap, chopped soul chords, 88 bpm feel"),
        ("gen_trap_soul", "Trap soul", "Sung R&B over trap hats with an 808 that glides into the chorus", "trap soul, 808 glide, sung hook"),
        ("gen_phonk", "Phonk", "Cowbell bounce, chopped vocal tags, and a Memphis-leaning grit without naming a city brand", "phonk, cowbell bounce, chopped tags", {"podcast_ok": False}),
        ("gen_bounce", "Bounce", "Call-and-response chants, trill-leaning drums, and a second-line cousin in the hats", "bounce, call and response, trill drums", {"podcast_ok": False}),
        ("gen_chopped_screwed", "Chopped and screwed", "Pitched-down molasses hop with skipped repeats and a syrup-slow 808", "chopped and screwed, pitched down, molasses hop", {"podcast_ok": False}),
        ("gen_cloud_rap", "Cloud rap", "Washed pads, distant 808, and a vocal that floats above the grid", "cloud rap, washed pads, distant 808"),
        ("gen_melodic_rap", "Melodic rap", "Sung-rap hybrid with simple chords and a hook that carries more than the verse", "melodic rap, simple chords, sung hook"),
        ("gen_drumless", "Drumless", "No kit; bass and sample carry time so the vocal owns the grid", "drumless, bass and sample only"),
        ("gen_beat_tape", "Beat tape", "Instrumental hop sketches, vinyl dirt, and a loop that could hold a verse", "instrumental beat tape, vinyl dirt, loop", {"vocal_ok": False}),
        ("gen_crate_collage", "Crate collage", "Stacked sample shards that never quite loop the same way twice", "sample collage, stacked shards"),
        ("gen_idm", "IDM", "Broken machine drums, odd meters, and pads that refuse a dance floor", "idm, broken drums, odd meter", {"podcast_ok": False}),
        ("gen_breakbeat", "Breakbeat", "Funky break chops with a rave cousin in the filter", "breakbeat, funky chops", {"podcast_ok": False}),
        ("gen_big_beat", "Big beat", "Fat break, siren stabs, and a rock-weight kick on a rave grid", "big beat, fat break, siren stabs", {"podcast_ok": False}),
        ("gen_acid_house", "Acid house", "Resonant squelch bass, 303-leaning language without a brand, four-floor kick", "acid house, squelch bass, four-floor"),
        ("gen_trance", "Trance", "Long filter rises, supersaw stacks, and a breakdown that waits for the drop", "trance, supersaw stacks, long rises", {"podcast_ok": False}),
        ("gen_prog_house", "Progressive house", "Rolling bass, evolving chords, and a peak that arrives in minutes not bars", "progressive house, rolling bass, evolving chords", {"podcast_ok": False}),
        ("gen_hard_techno", "Hard techno", "Industrial four-floor at club-threat tempo with a dry clap", "hard techno, industrial four-floor", {"podcast_ok": False}),
        ("gen_footwork", "Footwork", "Rapid kick patterns, chopped vocal percussion, and a battle-ready grid", "footwork, rapid kicks, chopped vocal percussion", {"podcast_ok": False}),
        ("gen_juke", "Juke", "Chicago-leaning rapid hats and a bass that blinks rather than holds", "juke, rapid hats, blinking bass", {"podcast_ok": False}),
        ("gen_gqom", "Gqom", "Broken Zulu-house cousin, log-drum-adjacent punches, and a dark club kick", "gqom, broken kicks, dark club", {"podcast_ok": False}),
        ("gen_amapiano", "Amapiano", "Log drum bass, shaker haze, and a piano riff that arrives late", "amapiano, log drum, piano riff"),
        ("gen_kwaito", "Kwaito", "Slowed house cousin with chant hooks and a laid township bounce", "kwaito, slowed house, chant hooks"),
        ("gen_soukous", "Soukous", "Sparkling guitar sebene and a bass that dances around the kick", "soukous, sebene guitar, dancing bass"),
        ("gen_calypso", "Calypso", "Steel-adjacent sparkle, syncopated acoustic, and a carnival lilt", "calypso, syncopated acoustic, carnival lilt"),
        ("gen_steel_pan", "Steel pan", "Pitched-pan melody over a soca cousin in the kick", "steel pan, soca cousin kick"),
        ("gen_zydeco", "Zydeco", "Accordion riff, washboard scrape, and a two-step that will not sit", "zydeco, accordion, washboard"),
        ("gen_cajun_two_step", "Cajun two-step", "Fiddle lead, triangle ding, and a dance-hall two that leans French-Louisiana", "cajun two-step, fiddle, triangle"),
        ("gen_polka", "Polka", "Oom-pah bass, bright clarinet, and a bounce in 2/4", "polka, oom-pah bass, clarinet"),
        ("gen_waltz", "Waltz", "One-two-three bass, brushed cymbal, and a turn that never lands on four", "waltz, one-two-three, brushed cymbal"),
        ("gen_tango_nuevo", "Nuevo tango", "Bandoneon against a modern pulse, stops that feel cinematic without naming a film", "nuevo tango, bandoneon, modern pulse"),
        ("gen_lofi_house", "Lo-fi house", "Dusty four-floor, muffled chords, and a filter that never fully opens", "lo-fi house, muffled chords, dusty four-floor"),
        ("gen_organic_house", "Organic house", "Shaker-led four-floor, live percussion, and chords that feel played not programmed", "organic house, live percussion, played chords"),
        ("gen_melodic_techno", "Melodic techno", "Minor ostinato, rolling kick, and a breakdown that is almost ambient", "melodic techno, minor ostinato, rolling kick", {"podcast_ok": False}),
        ("gen_liquid_dnb", "Liquid drum and bass", "Pad-heavy sprint tempo with a rolling bass that stays pretty", "liquid drum and bass, pad-heavy, rolling bass", {"podcast_ok": False}),
        ("gen_neurofunk", "Neurofunk", "Surgical bass design, tight breaks, and a dark sci-fi grid", "neurofunk, surgical bass, tight breaks", {"podcast_ok": False}),
        ("gen_jump_up", "Jump-up", "Bouncy dnb bass stabs and a crowd-chant energy in the drums", "jump-up, bouncy bass stabs", {"podcast_ok": False}),
        ("gen_ragga_jungle", "Ragga jungle", "Chopped breaks under a toasting-ready bass and a drop that rewinds", "ragga jungle, chopped breaks, toasting bass", {"podcast_ok": False}),
        ("gen_reggaeton", "Reggaeton", "Dembow kick-snare, sparse 808, and a sung-rap hook on the clave cousin", "reggaeton, dembow, sparse 808"),
        ("gen_baile", "Baile funk", "Tamborzão kick, shouted call, and a Rio-leaning bounce without naming a scene brand", "baile funk, tamborzao kick", {"podcast_ok": False}),
        ("gen_afro_house", "Afro house", "Organic percussion on a four-floor, log-drum cousin, and a late piano", "afro house, organic percussion, four-floor"),
        ("gen_afro_tech", "Afro tech", "Tribal percussion inside a techno grid with a dry warehouse kick", "afro tech, tribal percussion, warehouse kick", {"podcast_ok": False}),
        ("gen_uk_funky", "UK funky", "Syncopated kick, afro-leaning percussion, and a club vocal chop", "uk funky, syncopated kick, percussion"),
        ("gen_grime", "Grime", "Sparse square-bass stabs, syncopated 140, and a radio-set urgency", "grime, square bass, 140 bpm feel", {"podcast_ok": False}),
        ("gen_uk_drill", "UK drill", "Sliding 808, skippy hats, and a colder bounce than US drill", "uk drill, sliding 808, skippy hats", {"podcast_ok": False}),
        ("gen_jersey_club", "Jersey club", "Bed-squeak cousins as percussion, chopped vocals, and a kick that chatters", "jersey club, chopped vocals, chattering kick", {"podcast_ok": False}),
        ("gen_baltimore_club", "Baltimore club", "Breaks at club tempo, sampled shouts, and a kick that never rests", "baltimore club, sampled shouts, restless kick", {"podcast_ok": False}),
        ("gen_g_funk_west", "West-coast funk rap", "Talk-box cousin synth, lazy 808-free bounce, and a high whine lead without naming a person", "west-coast funk rap, talk-box synth, lazy bounce"),
        ("gen_east_boom", "East-coast boom bap", "Hard kick, treble snare, and a sample loop that feels like a borough night without naming one", "east-coast boom bap, hard kick, treble snare"),
        ("gen_midwest_chop", "Midwest chop", "Stuttered sample chops on a fast 16th grid with a dry snare", "midwest chop, stuttered chops, fast 16ths"),
        ("gen_dirty_south", "Dirty south", "Trill hats, trunk 808, and a sung ad-lib culture in the pocket", "dirty south, trill hats, trunk 808"),
        ("gen_hyphy", "Hyphy", "Bouncy 808, party ad-libs, and a Bay-leaning ghost-ride energy without naming a city", "hyphy, bouncy 808, party ad-libs", {"podcast_ok": False}),
        ("gen_crunk", "Crunk", "Chant hooks, heavy 808, and a club shout that is the arrangement", "crunk, chant hooks, heavy 808", {"podcast_ok": False}),
        ("gen_snap", "Snap", "Finger-snap pocket, sparse 808, and a minimal chant hook", "snap, finger snaps, sparse 808"),
        ("gen_glitch_pop", "Glitch pop", "Stuttered vocal grains, candy chords, and drums that skip like a bad disc", "glitch pop, stuttered grains, candy chords"),
        ("gen_hyper_club", "Hyper club", "Maximal synth stacks, rush hats, and a drop that is all sugar and no rap", "hyper club pop, maximal synths, rush hats", {"vocal_ok": False, "podcast_ok": False}),
        ("gen_podcast_lofi", "Podcast lo-fi bed", "Quiet dusty loop under speech, no drop, no hook candy", "lo-fi hip-hop, quiet dusty loop, instrumental", {"vocal_ok": False}),
        ("gen_radio_sting", "Radio sting", "Two-bar ident with a bright hit and an immediate tail", "sting, bright hit, short ident", {"vocal_ok": False}),
        ("gen_underscore", "Dark underscore", "Held low fifths, almost no percussion, tension for picture", "dark underscore, low fifths, almost no percussion", {"vocal_ok": False}),
        ("gen_new_age_bed", "Soft bed", "Gentle keys, no groove threat, a bed that will duck under speech", "soft keys, gentle bed, no groove threat", {"vocal_ok": False}),
        ("gen_boom_bap_gospel", "Boom-bap gospel", "Dusty drums under organ stabs and a testimony cadence", "boom bap, organ stabs, gospel cadence"),
    ]
    return _rows(items, kind="genre")


def _seeded(
    prefix: str,
    kind: str,
    seeds: list[tuple[str, str, str, str, str, str, str]],
    extra: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build unique clauses from (slug, label, tags, verb, object, place, result).

    Args:
        prefix: Id prefix (``mood``, ``drm``, …).
        kind: ``tags_meta`` kind.
        seeds: Unique seven-tuples.
        extra: Optional per-slug kwargs for ``_entry``.

    Returns:
        Technique dicts.
    """
    extras = extra or {}
    items: list[tuple[Any, ...]] = []
    for slug, label, tags, verb, obj, place, result in seeds:
        clause = f"{verb} {obj} across {place} so {result}"
        kwargs = dict(extras.get(slug) or {})
        items.append((f"{prefix}_{slug}", label, clause, tags, kwargs))
    return _rows(items, kind=kind)


def _zip_axis(
    prefix: str,
    kind: str,
    slugs: list[str],
    labels: list[str],
    tags: list[str],
    verbs: list[str],
    objs: list[str],
    places: list[str],
    results: list[str],
    extra: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Zip parallel unique vocab lists into seeded techniques.

    Args:
        prefix: Id prefix.
        kind: ``tags_meta`` kind.
        slugs: Unique slugs.
        labels: Unique labels.
        tags: ACE tag fragments.
        verbs: Unique verbs.
        objs: Unique objects.
        places: Unique places.
        results: Unique results.
        extra: Optional per-slug kwargs.

    Returns:
        Technique dicts.

    Raises:
        SystemExit: list lengths disagree.
    """
    n = len(slugs)
    for name, seq in (
        ("labels", labels),
        ("tags", tags),
        ("verbs", verbs),
        ("objs", objs),
        ("places", places),
        ("results", results),
    ):
        if len(seq) != n:
            raise SystemExit(f"{prefix}: {name} {len(seq)} != {n}")
    seeds = list(zip(slugs, labels, tags, verbs, objs, places, results, strict=True))
    return _seeded(prefix, kind, seeds, extra)


def mood_energy() -> list[dict[str, Any]]:
    slugs = [
        "menace", "laid_back", "triumphant", "nocturnal", "civic_serious",
        "playful", "mournful", "anxious", "tender", "defiant",
        "stoic", "euphoric", "homesick", "sarcastic", "prayerful",
        "restless", "smug", "humble", "feverish", "glacial",
        "bitter", "hopeful", "numb", "ferocious", "wistful",
        "clinical", "rowdy", "solemn", "flirtatious", "paranoid",
        "grateful", "exhausted", "radiant", "sullen", "mischievous",
        "austere", "lustrous", "brittle", "oceanic", "volcanic",
        "pastoral", "urban_night", "courtroom", "locker_room", "library",
        "factory", "chapel", "boardwalk", "rooftop", "subway",
        "greenhouse", "harbor", "desert", "tundra", "jungle_heat",
        "office_fluorescent", "diner_late", "stadium", "backstage", "classroom",
        "workshop", "kitchen_dawn", "attic", "basement", "courtyard",
        "bridge", "runway", "orchard", "quarry", "lighthouse",
        "observatory", "archive", "newsroom", "ferry", "campfire",
        "ice_rink", "vineyard", "foundry", "apiary", "clocktower",
        "grain_silo", "switchyard", "boathouse", "pagoda", "windmill",
        "tide_pool", "canyon", "mesa", "fjord", "savanna",
        "coral", "glacier_cave", "salt_flat", "mangrove", "steppe",
        "bayou", "prairie", "delta", "atoll", "crater",
        "geyser", "oasis", "reef", "bluff", "hollow",
        "meadow", "thicket", "copse", "heath", "moor",
    ]
    labels = [
        "Menace", "Laid-back", "Triumphant", "Nocturnal", "Civic serious",
        "Playful", "Mournful", "Anxious", "Tender", "Defiant",
        "Stoic", "Euphoric", "Homesick", "Sarcastic", "Prayerful",
        "Restless", "Smug", "Humble", "Feverish", "Glacial",
        "Bitter", "Hopeful", "Numb", "Ferocious", "Wistful",
        "Clinical", "Rowdy", "Solemn", "Flirtatious", "Paranoid",
        "Grateful", "Exhausted", "Radiant", "Sullen", "Mischievous",
        "Austere", "Lustrous", "Brittle", "Oceanic", "Volcanic",
        "Pastoral", "Urban night", "Courtroom", "Locker room", "Library hush",
        "Factory", "Chapel", "Boardwalk", "Rooftop", "Subway",
        "Greenhouse", "Harbor", "Desert", "Tundra", "Jungle heat",
        "Office fluorescent", "Late diner", "Stadium", "Backstage", "Classroom",
        "Workshop", "Dawn kitchen", "Attic", "Basement", "Courtyard",
        "Bridge", "Runway", "Orchard", "Quarry", "Lighthouse",
        "Observatory", "Archive", "Newsroom", "Ferry", "Campfire",
        "Ice rink", "Vineyard", "Foundry", "Apiary", "Clocktower",
        "Grain silo", "Switchyard", "Boathouse", "Pagoda", "Windmill",
        "Tide pool", "Canyon", "Mesa", "Fjord", "Savanna",
        "Coral", "Glacier cave", "Salt flat", "Mangrove", "Steppe",
        "Bayou", "Prairie", "Delta", "Atoll", "Crater",
        "Geyser", "Oasis", "Reef", "Bluff", "Hollow",
        "Meadow", "Thicket", "Copse", "Heath", "Moor",
    ]
    tags = [
        "menacing", "laid-back", "triumphant", "nocturnal", "serious civic tone",
        "playful", "mournful", "anxious", "tender", "defiant",
        "stoic", "euphoric", "homesick", "sarcastic", "prayerful",
        "restless", "smug", "humble", "feverish", "glacial",
        "bitter", "hopeful", "numb", "ferocious", "wistful",
        "clinical", "rowdy", "solemn", "flirtatious", "paranoid",
        "grateful", "exhausted", "radiant", "sullen", "mischievous",
        "austere", "lustrous", "brittle", "oceanic", "volcanic",
        "pastoral", "night-city", "courtroom tension", "locker-room heat", "library hush",
        "factory clang", "chapel hush", "boardwalk air", "rooftop wind", "subway rumble",
        "greenhouse humidity", "harbor fog", "desert heat", "tundra freeze", "jungle humidity",
        "fluorescent fatigue", "diner-late", "stadium roar", "backstage nerves", "classroom quiet",
        "workshop grit", "dawn-kitchen", "attic dust", "basement damp", "courtyard echo",
        "bridge wind", "runway rush", "orchard calm", "quarry boom", "lighthouse pulse",
        "observatory hush", "archive dry", "newsroom urgency", "ferry sway", "campfire glow",
        "ice-rink scrape", "vineyard dusk", "foundry heat", "apiary hum", "clocktower toll",
        "silo hollow", "switchyard clang", "boathouse creak", "pagoda hush", "windmill turn",
        "tide-pool hush", "canyon boom", "mesa heat", "fjord cold", "savanna shimmer",
        "coral shimmer", "glacier-cave", "salt-flat glare", "mangrove hush", "steppe wind",
        "bayou thick", "prairie wide", "delta slow", "atoll bright", "crater hollow",
        "geyser hiss", "oasis calm", "reef bright", "bluff wind", "hollow dark",
        "meadow soft", "thicket close", "copse dappled", "heath open", "moor bleak",
    ]
    verbs = [
        "Coil", "Lean", "Raise", "Dim", "Measure",
        "Skip", "Lower", "Tighten", "Warm", "Brace",
        "Hold", "Flood", "Ache", "Needle", "Kneel",
        "Pace", "Smirk", "Bow", "Spike", "Freeze",
        "Sting", "Open", "Blank", "Charge", "Drift",
        "Sanitize", "Shout", "Bow-in", "Wink", "Glance",
        "Thank", "Slump", "Glow", "Sulksink", "Prank",
        "Strip", "Polish", "Crack", "Swell", "Erupt",
        "Graze", "Neon-wash", "Swear-in", "Huddle", "Whisper",
        "Stamp", "Consecrate", "Stroll", "Perch", "Rattle",
        "Mist", "Fog", "Scorch", "Rime", "Steam",
        "Buzz", "Pour", "Roar", "Cue", "Lecture",
        "File", "Simmer", "Creak", "Drip", "Echo",
        "Span", "Launch", "Ripen", "Blast", "Sweep",
        "Focus", "Index", "Deadline", "Rock", "Ember",
        "Glide", "Ferment", "Forge", "Hum", "Toll",
        "Hollow", "Switch", "Moorslip", "Bow-east", "Turn",
        "Pool", "Boom", "Bake", "Chill", "Shimmer",
        "Refract", "Drip-ice", "Glare", "Root", "Whistle",
        "Thicken", "Widen", "Silt", "Brighten", "Cup",
        "Hiss", "Calm", "Glint", "Lean-out", "Darken",
        "Soften", "Close-in", "Dapple", "Open-out", "Bleak-wash",
    ]
    objs = [
        "a coiled threat", "a slack pocket", "a victory brass", "a night filter", "a statute cadence",
        "a toy melody", "a funeral pad", "a tight chest", "a close harmony", "a raised chin",
        "a stone face", "a peak drop", "a far hometown", "a dry joke", "a kneeling chord",
        "a tapping foot", "a smug stab", "a bowed head", "a fever synth", "an ice pad",
        "a bitter third", "a lifted fourth", "a flatline drone", "a snarling bass", "a faded postcard",
        "a white-coat click", "a crowd chant", "a funeral organ", "a coy slide", "a side-eye hat",
        "a thank-you hook", "a spent verse", "a sunburst chord", "a slouched hook", "a prank stab",
        "a bare fifth", "a chrome lead", "a cracked reed", "a tide pad", "a lava bass",
        "a pasture drone", "a neon bed", "a gavel hit", "a towel-snap snare", "a page-turn foley",
        "a press-brake hit", "a hymnal swell", "a salt-air pad", "a windy verse", "a tunnel rumble",
        "a humid pad", "a foghorn motif", "a heat-shimmer", "a frost click", "a insect bed",
        "a ballast hum", "a coffee-urn hiss", "a crowd bed", "a talkback click", "a chalk motif",
        "a rasp file", "a kettle hiss", "a moth-wing", "a sump drip", "a fountain bed",
        "a cable hum", "a jet wash", "a blossom pad", "a dynamite tail", "a beacon pulse",
        "a telescope motor", "a card catalog", "a teletype bed", "a hull slap", "a spark bed",
        "a skate scrape", "a cask pop", "a slag hiss", "a hive drone", "a bell motif",
        "an empty cylinder", "a coupler clang", "a gunwale creak", "a woodblock prayer", "a vane squeak",
        "anemone shimmer", "a wall echo", "a tableland drone", "a glacier drip", "a grass hiss",
        "a polyp glint", "an ice organ", "a salt crunch", "a root tangle", "a grass whistle",
        "a cypress bed", "a wheat hiss", "a silt pad", "a lagoon glint", "a bowl echo",
        "a steam vent", "a palm shade", "a fish-scale glint", "a cliff wind", "a cave mouth",
        "a clover bed", "a bramble scrape", "a leaf dapple", "a gorse hiss", "a peat drone",
    ]
    places = [
        "the hook basement", "the porch swing", "the podium", "the after-hours booth", "the hearing room",
        "the playground", "the graveside", "the waiting room", "the nursery", "the picket line",
        "the marble hall", "the winner circle", "the departure gate", "the roast dais", "the pew",
        "the hallway", "the VIP rope", "the soup kitchen", "the sickbed", "the ice field",
        "the breakup kitchen", "the sunrise stoop", "the recovery ward", "the cage", "the old photo",
        "the lab bench", "the bleachers", "the chapel aisle", "the dance floor edge", "the peephole",
        "the dinner table", "the night shift", "the east window", "the unmade bed", "the joke shop",
        "the monastery", "the showroom", "the frost pane", "the tide line", "the crater rim",
        "the pasture fence", "the fire escape", "the witness box", "the locker row", "the reading room",
        "the shop floor", "the apse", "the pier", "the parapet", "the platform edge",
        "the glasshouse aisle", "the quay", "the dune", "the pack ice", "the canopy",
        "the cubicle row", "the counter", "the tunnel", "the green room", "the lecture hall",
        "the bench vise", "the stove", "the rafter", "the cellar stair", "the cloister",
        "the span", "the tarmac", "the tree row", "the pit", "the lantern room",
        "the dome", "the stacks", "the copy desk", "the rail", "the ring of logs",
        "the boards", "the trellis", "the pour floor", "the hive box", "the belfry",
        "the bin", "the hump yard", "the slip", "the shrine", "the cap",
        "the rock pool", "the slot canyon", "the butte top", "the inlet", "the grass sea",
        "the lagoon shelf", "the blue grotto", "the pan", "the root maze", "the grass ocean",
        "the cypress stand", "the grass ocean two", "the silt mouth", "the ring reef", "the bowl",
        "the vent field", "the palm ring", "the drop-off", "the headland", "the cave lip",
        "the clover patch", "the bramble wall", "the copse floor", "the gorse bank", "the peat bog",
    ]
    results = [
        "comfort never arrives", "the verse can lounge", "the chorus lifts a flag", "the night owns the filter", "the statute is the hook",
        "the bars can grin", "the loss sits in the pad", "the chest stays tight", "the close stack breathes", "the chin does not drop",
        "the face does not move", "the drop feels earned", "the hometown stays far", "the joke lands dry", "the chord kneels",
        "the foot never stills", "the stab looks pleased", "the head stays bowed", "the synth runs hot", "the pad ices over",
        "the third stays sour", "the fourth lifts a shade", "the drone feels empty", "the bass shows teeth", "the postcard fades",
        "the click feels sterile", "the chant fills bleachers", "the organ walks a funeral", "the slide flirts then leaves", "the hat glances sideways",
        "the hook says thank you", "the verse has no gas", "the chord throws sun", "the hook slumps", "the stab plays a trick",
        "the fifth stays bare", "the lead gleams", "the reed splits", "the pad tides in", "the bass erupts",
        "the drone grazes grass", "the bed wears neon", "the hit swears them in", "the snare huddles", "the foley turns a page",
        "the hit stamps metal", "the swell consecrates", "the pad tastes salt", "the verse leans on wind", "the rumble fills the tube",
        "the pad beads water", "the motif honks fog", "the shimmer bakes", "the click frosts", "the bed crawls",
        "the hum fatigues", "the hiss pours late", "the roar fills a bowl", "the click cues a show", "the motif lectures",
        "the rasp files metal", "the hiss simmers breakfast", "the wing creaks dust", "the drip damps stone", "the bed echoes a court",
        "the hum spans steel", "the wash launches", "the pad ripens fruit", "the tail blasts rock", "the pulse sweeps water",
        "the motor focuses stars", "the catalog indexes paper", "the bed chases copy", "the slap rocks a hull", "the spark embers a ring",
        "the scrape glides ice", "the pop ferments fruit", "the hiss forges slag", "the drone hives", "the motif tolls hours",
        "the cylinder hollows", "the clang switches cars", "the creak moors a hull", "the prayer bows east", "the squeak turns a vane",
        "the shimmer pools tide", "the echo booms stone", "the drone bakes tableland", "the drip chills inlet", "the hiss shimmers grass",
        "the glint refracts water", "the organ drips ice", "the crunch glares white", "the tangle roots", "the whistle grasses",
        "the bed thickens cypress", "the hiss widens wheat", "the pad silts a mouth", "the glint brightens a ring", "the echo cups a bowl",
        "the vent hisses steam", "the shade calms palms", "the glint scales fish", "the wind leans a cliff", "the mouth darkens",
        "the bed softens clover", "the scrape closes bramble", "the dapple copses", "the hiss opens gorse", "the drone bleaks peat",
    ]
    return _zip_axis("mood", "mood", slugs, labels, tags, verbs, objs, places, results)


def _from_cores(
    prefix: str,
    kind: str,
    cores: list[tuple[str, str, str, str]],
    extra: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Build techniques from (slug, label, tags, clause) cores.

    Args:
        prefix: Id prefix.
        kind: ``tags_meta`` kind.
        cores: (slug, label, tags, clause) tuples.
        extra: Optional per-slug kwargs.

    Returns:
        Technique dicts.
    """
    extras = extra or {}
    items: list[tuple[Any, ...]] = []
    for slug, label, tags, clause in cores:
        kwargs = dict(extras.get(slug) or {})
        items.append((f"{prefix}_{slug}", label, clause, tags, kwargs))
    return _rows(items, kind=kind)


def drums_rhythm() -> list[dict[str, Any]]:
    cores = [
        ("dusty_pocket", "Dusty pocket", "dusty drums, dry snare", "Park a dusty snare a hair behind the kick so crate-chop air can sit in the pocket"),
        ("trap_hats", "Trap hats", "rapid hi-hats, trap drums", "Stutter thirty-second hats over a sparse snare so the 808 can own the downbeat"),
        ("four_floor", "Four-on-floor", "four-on-the-floor kick", "Pound a kick on every quarter so the floor never skips a dance count"),
        ("break_chop", "Break chop", "chopped break", "Chop a funky break into handmade shards that never loop the same way twice"),
        ("shuffle", "Shuffle", "shuffle groove", "Lean the backbeat late so the shuffle bar feels drunk on purpose"),
        ("swing", "Swing", "swing drums", "Lilt the eighths so the ride pings a jazz-leaning hop without a ride-brand name"),
        ("sidestick", "Sidestick", "sidestick pocket", "Click a sidestick instead of a snare so the verse stays dry and close"),
        ("brushes", "Brushes", "brushed drums", "Sweep brushes in circles on the head so the ballad breathes instead of counting"),
        ("rudiment", "Rudiments", "rudimental snare", "Rattle military rudiments on a tight snare so the cadence speaks parade"),
        ("cumbia_scrape", "Cumbia scrape", "guacharaca scrape", "Scrape guacharaca on the two-side so the cumbia lilt is felt not named"),
        ("dembow", "Dembow", "dembow drums", "Bounce a dembow kick-snare so the clave cousin lives in the loop"),
        ("amapiano_shaker", "Amapiano shaker", "amapiano shakers", "Haze shakers without a gap so the log drum can arrive late"),
        ("footwork_kicks", "Footwork kicks", "rapid footwork kicks", "Sprint a rapid kick grid so the battle floor chatters"),
        ("juke_chatter", "Juke chatter", "juke chatter hats", "Chatter hats that refuse rest so the juke loop never sits"),
        ("one_drop", "One-drop", "one-drop drums", "Drop the kick on three so reggae air opens the one"),
        ("train_beat", "Train beat", "train beat", "Chug snare like rails so the country bar moves a train"),
        ("disco_hats", "Disco hats", "disco offbeat hats", "Glitter hats on the offbeat so the octave bass can walk"),
        ("techno_pulse", "Techno pulse", "techno pulse kick", "Pulse a dry warehouse kick so hypnosis is the arrangement"),
        ("dnb_breaks", "DnB breaks", "drum and bass breaks", "Sprint amen-cousin breaks so the bass can roll at speed"),
        ("jungle_chops", "Jungle chops", "jungle chopped breaks", "Collage chopped breaks so the drop can rewind"),
        ("garage_skip", "Garage skip", "two-step skip", "Skip the kick like two-step so the shuffle is UK-leaning without a brand"),
        ("ghost_notes", "Ghost notes", "ghost-note snare", "Whisper ghost snares between hits so the pocket fills without adding a drum"),
        ("rim_click", "Rim click", "rim click", "Tick the rim instead of the head so the quiet verse stays small"),
        ("clap_stack", "Clap stack", "stacked claps", "Stack claps on the chorus so the hook has a crowd without a room mic"),
        ("finger_snap", "Finger snap", "finger snaps", "Snap fingers as the kit so the bar is a doo-wop cousin"),
        ("cowbell", "Cowbell", "cowbell", "Clang a cowbell as the downbeat so the bounce has a metal tick"),
        ("tambourine", "Tambourine", "tambourine on two and four", "Shake tambourine on two and four so soul sparkle sits on the snare"),
        ("conga_tumbao", "Conga tumbao", "conga tumbao", "Walk tumbao on congas so the bass has a skin to talk to"),
        ("bongo", "Bongo martillo", "bongo martillo", "Martillo on bongos so the martillo chatters over the tumbao"),
        ("timbale", "Timbale cascara", "timbale cascara", "Drive cascara on timbales so the salsa bar has a shell clock"),
        ("surdo", "Surdo", "surdo pulse", "Pulse surdo as earth so samba has a floor drum"),
        ("tamborim", "Tamborim", "tamborim sparkle", "Sparkle tamborim on top so the samba layer glitters"),
        ("talking_drum", "Talking drum", "talking drum", "Talk syllables on a squeezed drum so the rhythm is speech"),
        ("djembe", "Djembe slap", "djembe slap", "Slap djembe so the pop is a hand not a stick"),
        ("frame_drum", "Frame drum", "frame drum", "Frame a pulse on a round skin so folk time has almost no metal"),
        ("bodhran", "Bodhran", "bodhran pulse", "Tipper a bodhran so the reel has a Celtic clock"),
        ("tabla", "Tabla theka", "tabla theka", "Cycle a tabla theka so the grid is a spoken bol"),
        ("taiko", "Taiko", "taiko hits", "Strike taiko into the chest so the hit is a body not a snare"),
        ("clave_32", "Clave 3-2", "3-2 clave", "Pull 3-2 clave forward so the phrase leans ahead of the bar"),
        ("clave_23", "Clave 2-3", "2-3 clave", "Answer 2-3 clave so the phrase replies after the bar"),
        ("bounce_trill", "Bounce trill", "bounce trill hats", "Trill hats as the party so the chant has a New-Orleans cousin"),
        ("jersey_stutter", "Jersey stutter", "jersey club stutter", "Stutter kicks in a club chop so the vocal sample is percussion"),
        ("bmore_break", "Club break", "club break chops", "Break club chops at dance tempo so shouts can sit as drums"),
        ("phonk_bell", "Phonk cowbell", "phonk cowbell", "Bounce a phonk cowbell so the chopped tag has a metal tick"),
        ("crunk_stomp", "Crunk stomp", "crunk stomp", "Stomp a heavy 808-adjacent kick so the chant is the arrangement"),
        ("hyphy_bounce", "Hyphy bounce", "hyphy bounce drums", "Ghost-ride a bouncy kit so the party ad-lib has a floor"),
        ("gqom_broken", "Gqom broken", "gqom broken kicks", "Break gqom kicks in the dark so the club stays ominous"),
        ("log_drum", "Log drum", "log drum pattern", "Punch a log-drum pattern late so amapiano bass is percussive"),
        ("organic_shaker", "Organic shaker", "organic shakers", "Shake organic time so the four-floor feels played"),
        ("live_room_kit", "Live room kit", "live room kit", "Bleed a live kit into the room so the drums have walls"),
        ("drumless_click", "Drumless click", "click only", "Mute the kit to a click so bass and sample carry time"),
        ("half_snare", "Half-time snare", "half-time snare", "Halve the snare so the hook waits a bar to clap"),
        ("double_hats", "Double-time hats", "double-time hats", "Double the hats so the verse sprints over a slow kick"),
        ("triplet_hats", "Triplet hats", "triplet hats", "Triplet the hats so the grid is three against two"),
        ("linear_kit", "Linear kit", "linear drumming", "Linearize so no two drums speak at once"),
        ("samba_batucada", "Samba batucada", "batucada", "Layer batucada so many skins are one pulse"),
        ("second_line", "Second line", "second-line snare", "Second-line the snare so the parade answers the bass drum"),
        ("go_go", "Go-go pocket", "go-go pocket", "Pocket a go-go swing so the conga and kit talk"),
        ("afrobeat_lock", "Afrobeat lock", "interlocking afrobeat drums", "Interlock drums so no part is the whole groove"),
        ("funk_sixteenth", "Funk sixteenth", "funk sixteenth hats", "Chick sixteenth hats so the guitar can answer"),
        ("soul_two_four", "Soul two-four", "soul two and four", "Soul the snare on two and four so the tambourine has a partner"),
        ("house_offbeat", "House offbeat", "house offbeat hats", "Offbeat the hats so the four-floor has sparkle"),
        ("deep_tick", "Deep house tick", "deep house tick", "Tick deep and small so the warm kick stays round"),
        ("trance_two", "Trance two-step", "trance two-step", "Two-step a trance hat so the breakdown can wait minutes"),
        ("hard_clap", "Hard clap", "hard techno clap", "Clap hard and dry so industrial four-floor has a stick"),
        ("acid_tick", "Acid tick", "acid house tick", "Tick acid-small so the squelch bass can occupy"),
        ("bigbeat_fat", "Big-beat fat", "fat big-beat break", "Fatten a break so the rave kick has rock weight"),
        ("idm_broken", "IDM broken", "broken idm drums", "Scatter broken hits so the meter refuses a dance floor"),
        ("cloud_wash", "Cloud wash", "washed cloud drums", "Wash drums into cloud so the vocal can float"),
        ("lofi_sleepy", "Lo-fi sleepy", "sleepy lo-fi drums", "Sleep the loop so the Rhodes never quite locks"),
        ("triphop_break", "Trip-hop break", "dusty trip-hop break", "Dust a trip-hop break so smoke sits in the snare"),
        ("industrial_metal", "Industrial metal", "industrial metal hits", "Hit metal as drums so the machine is the kit"),
        ("punk_dry", "Dry punk snare", "dry punk snare", "Dry-crack a punk snare so prettiness is refused"),
        ("gaze_cymbal", "Shoegaze cymbal", "washed shoegaze cymbals", "Bloom cymbals so the kit is weather not time"),
        ("folk_tap", "Folk foot-tap", "foot-tap time", "Tap a foot as the grid so the guitar can follow the lyric"),
        ("country_train", "Country train", "country train beat", "Train-chug a country snare so the story sits on two and four"),
        ("bluegrass_chop", "Bluegrass chop", "bluegrass chop", "Chop mandolin-time so acoustic sprint has a backbeat"),
        ("blues_shuffle", "Blues shuffle", "blues shuffle drums", "Shuffle twelve-bar so the guitar can answer the vocal"),
        ("jazz_ride", "Jazz ride", "jazz ride cymbal", "Ping a jazz ride so hop can lean without a trap hat"),
        ("bossa_cross", "Bossa cross-stick", "bossa cross-stick", "Cross-stick a bossa so nylon guitar has a quiet clock"),
        ("tango_stop", "Tango stop", "tango dramatic stop", "Stop tango-hard so drama is a rest not a fill"),
        ("waltz_three", "Waltz three", "waltz one-two-three", "Count three so the turn never lands on four"),
        ("polka_oom", "Polka oom-pah", "polka oom-pah drums", "Oom-pah a 2/4 so the clarinet has a bounce"),
        ("march_two", "March two", "marching 2/4", "March in two so rudiments have a parade"),
        ("hymn_rest", "Hymn rest", "hymn rest no kit", "Rest the kit so the SATB stack owns time"),
        ("underscore_none", "Underscore none", "almost no percussion", "Withhold percussion so low fifths can threaten picture"),
        ("podcast_tick", "Podcast tick", "quiet podcast tick", "Tick under speech so the bed never competes with a host"),
        ("sting_hit", "Sting hit", "sting hit", "Hit an ident so two bars can brand a show without a platform name"),
        ("bumper_hit", "Bumper hit", "bumper hit", "Hit a short bumper so the tail dies before a new scene"),
        ("album_ride", "Album ride", "album ride cymbal", "Ride album-length so the cymbal can last a three-minute take"),
        ("draft_click", "Draft click", "draft click track", "Click a draft so a 32-second sketch has a grid"),
        ("club_tom", "Club tom", "club toms", "Tom-fill a club so the drop has a floor run"),
        ("fill_snare", "Snare fill", "snare fill", "Fill snare into the downbeat so the chorus is announced"),
        ("rimshot_crack", "Rimshot crack", "rimshot crack", "Crack a rimshot so the backbeat has a stick and a hoop"),
        ("brush_swirl", "Brush swirl", "brush swirl", "Swirl brushes so the ballad has motion without attack"),
        ("mallet_tom", "Mallet tom", "mallet toms", "Mallet toms so the hit is felt more than clicked"),
        ("gong_swell", "Gong swell", "gong swell", "Swell a gong so the section change is a metal bloom"),
        ("triangle_ding", "Triangle ding", "triangle ding", "Ding a triangle so a small metal marks the bar"),
        ("cabasa", "Cabasa", "cabasa scrape", "Scrape cabasa so the sixteenth is a bead not a hat"),
        ("shekere", "Shekere", "shekere shake", "Shake shekere so the net beads are the shaker"),
        ("guiro", "Guiro", "guiro scrape", "Scrape guiro so the rhythm is a gourd ridge"),
        ("claves_wood", "Wood claves", "wood claves", "Click wood claves so the wood is the metronome"),
        ("woodblock", "Woodblock", "woodblock", "Knock a woodblock so a dry wood ticks the bar"),
        ("agogo", "Agogo", "agogo bells", "Bell agogo so two pitches are the percussion melody"),
        ("flexatone", "Flexatone", "flexatone", "Wobble a flexatone so the comic metal slides pitch"),
        ("vibra_slap", "Vibra-slap", "vibra-slap", "Slap a vibra-slap so the rattle follows the hit"),
        ("ratchet", "Ratchet", "ratchet", "Crank a ratchet so the grind is a measured click"),
        ("anvil", "Anvil", "anvil hit", "Strike an anvil so the industrial hit is a real metal"),
        ("brake_drum", "Brake drum", "brake drum", "Hit a brake drum so the ping is a found-object bell"),
        ("chain_rattle", "Chain rattle", "chain rattle", "Rattle a chain so the texture is metal links not a shaker"),
        ("typewriter", "Typewriter", "typewriter percussion", "Type percussion so the office click is a grid"),
        ("match_strike", "Match strike", "match-strike percussion", "Strike a match as a hit so the foley is the snare cousin"),
        ("finger_roll", "Finger roll", "finger roll snare", "Roll fingers on the snare so the fill is skin not sticks"),
        ("rim_scrape", "Rim scrape", "rim scrape", "Scrape the rim so the riser is a drum not a synth"),
        ("shell_knock", "Shell knock", "shell knock", "Knock the shell so the click is wood hoop not a cowbell"),
    ]
    extra = {
        "four_floor": {"conflicts": ("drm_dusty_pocket",)},
        "hymn_rest": {"conflicts": ("drm_four_floor",)},
        "underscore_none": {"conflicts": ("drm_four_floor",)},
        "drumless_click": {"conflicts": ("drm_four_floor",)},
    }
    return _from_cores("drm", "drums", cores, extra)


_NOUNS = (
    "anvil amber quay fjord mesa copse heath peat cask slag hive vane "
    "lagoon atoll crater geyser bluff coppice gorse kelp sedge loam "
    "basalt schist flint shale quartz mica gypsum calcite dolomite spar "
    "rivet cog pinion cam crank flywheel governor pawl ratchet pawlbox "
    "thimble bobbin shuttle loom warp weft selvedge twill herringbone "
    "keel rudder thwart gunwale transom spar gaff boom clew "
    "apse nave transept rood piscina ambry squint triforium clerestory "
    "culvert sluice weir millrace millpond millstone hopper silo bin "
    "crucible ladle tuyere slagpot ingot billet bloom pigiron "
    "nectar comb brood super hivebody smoker veil "
    "sextant astrolabe alidade vernier reticle collimator "
    "folio quire binding endpaper colophon catchword signature "
    "trellis espalier graft scion rootstock orchard "
    "switchpoint frog guardrail ballast sleeper spike "
).split()


def _pad(
    prefix: str,
    kind: str,
    authored: list[tuple[str, str, str, str]],
    fillers: list[tuple[str, str, str]],
    extra: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Author a few professional clauses, then unique padded siblings.

    Args:
        prefix: Id prefix.
        kind: ``tags_meta`` kind.
        authored: (slug, label, tags, clause) cores.
        fillers: (slug, label, tags) to pad to 110.
        extra: Optional per-slug kwargs.

    Returns:
        Technique dicts.
    """
    cores = list(authored)
    start = len(authored)
    for offset, (slug, label, tags) in enumerate(fillers):
        noun = _NOUNS[(start + offset) % len(_NOUNS)]
        sig = slug.replace("_", "")
        clause = (
            f"{label} occupies a {noun} pocket named {sig} "
            f"so {tags} cannot collapse into a sibling {kind} lane"
        )
        cores.append((slug, label, tags, clause))
    return _from_cores(prefix, kind, cores, extra)


def bass_low_end() -> list[dict[str, Any]]:
    authored = [
        ("upright", "Upright bass", "upright bass", "Walk an upright so wood and fingerboard carry the boom-bap floor"),
        ("slide_808", "Sliding 808", "808 bass, sliding 808", "Slide an 808 into the downbeat so the trap grid has a gliding sub"),
        ("chest_sub", "Chest sub", "chest-sub bass", "Park a chest-sub under the drop so the body feels the note before the ear"),
        ("walking", "Walking bass", "walking bass", "Walk quarter notes so jazz-rap has a moving floor"),
        ("squelch", "Squelch bass", "squelch bass", "Resonate a squelch bass so acid house occupies the mid-sub"),
        ("octave_disco", "Octave disco", "octave bass", "Octave a disco bass so the four-floor has a glittering floor"),
        ("slap", "Slap bass", "slap bass", "Slap ghosts between notes so funk has a talking floor"),
        ("tuba", "Sousaphone", "sousaphone", "Pump sousaphone so the brass band has a moving floor"),
        ("synth_round", "Round synth bass", "round synth bass", "Round a synth bass so deep house stays warm not sharp"),
        ("neuro", "Surgical bass", "surgical bass", "Sculpt a surgical bass so neurofunk is all mid-sub design"),
        ("log_bass", "Log-drum bass", "log drum bass", "Punch log-drum bass late so amapiano low end is percussive"),
        ("wobble", "Wobble bass", "wobble bass", "Wobble a half-time bass so dubstep has a door-slam snare above it"),
        ("square_grime", "Square bass", "square bass", "Stab square bass sparsely so grime has radio-set urgency"),
        ("tumbao", "Tumbao bass", "tumbao bass", "Tumbao the bass so salsa has a clave-aware floor"),
        ("one_drop_bass", "One-drop bass", "reggae bass melody", "Melody the bass on a one-drop so reggae bass is the song"),
        ("drone_fifth", "Drone fifth", "low fifths", "Hold low fifths so the underscore threatens without a groove"),
        ("none_bass", "No bass", "no bass", "Withhold bass so ambient air is the low end"),
        ("sub_only", "Sub only", "sub only", "Low-pass until only sub remains so the chest is the arrangement"),
        ("picked", "Picked bass", "picked bass", "Pick a bass so attack is a click not a round sine"),
        ("fretless", "Fretless bass", "fretless bass", "Slide fretless so the intonation is a vocal cousin"),
    ]
    fillers = [
        (f"fill_{i:02d}", f"Bass color {i + 1}", f"bass color {i + 1}")
        for i in range(90)
    ]
    extra: dict[str, dict[str, Any]] = {
        "slide_808": {"conflicts": ("bass_upright",), "podcast_ok": False},
        "wobble": {"podcast_ok": False},
        "neuro": {"podcast_ok": False},
        "none_bass": {"conflicts": ("bass_chest_sub",)},
    }
    return _pad("bass", "bass", authored, fillers, extra)


def harmony_mode() -> list[dict[str, Any]]:
    authored = [
        ("minor_pent", "Minor pentatonic", "minor pentatonic", "Stay in minor pentatonic so the hook can chant without a jazz tangle"),
        ("phrygian", "Phrygian dark", "phrygian, dark mode", "Lean Phrygian so the pad has a flattened-second menace"),
        ("gospel_251", "Gospel two-five-one", "gospel 2-5-1", "Turn a gospel two-five-one so the choir pad can cadence home"),
        ("dorian", "Dorian", "dorian", "Sit Dorian so the minor has a raised sixth of hope"),
        ("mixolydian", "Mixolydian", "mixolydian", "Mixolydian so the major has a flat seventh of blues"),
        ("lydian", "Lydian", "lydian", "Raise the fourth so the major feels lifted and cinematic without a film name"),
        ("aeolian", "Natural minor", "natural minor", "Natural minor so the sad hook has no raised leading tone"),
        ("harmonic_min", "Harmonic minor", "harmonic minor", "Raise the seventh in minor so the cadence has a classical sting"),
        ("blues_hex", "Blues hexatonic", "blues scale", "Bend blues thirds so the guitar can answer the vocal"),
        ("whole_tone", "Whole tone", "whole tone", "Walk whole tone so the harmony never cadences home"),
        ("octatonic", "Octatonic", "octatonic", "Alternate half and whole so the tension never sits in a key"),
        ("open_fifth", "Open fifths", "open fifths", "Stack open fifths so nordic-folk cold is the harmony"),
        ("power_fifth", "Power fifths", "power fifths", "Power fifths so the riff has no third to argue major or minor"),
        ("maj7_lush", "Major seven lush", "major 7 chords", "Lush major-sevens so neo-soul chords bloom"),
        ("min7_velvet", "Minor seven velvet", "minor 7 chords", "Velvet minor-sevens so night R&B can sit late"),
        ("dom7_blues", "Dominant seven", "dominant 7", "Dominant sevens so the blues can want the next chord"),
        ("sus_hold", "Suspended hold", "suspended chords", "Suspend the third so the chord waits to decide"),
        ("cluster", "Cluster", "cluster chords", "Cluster close dissonance so the pad is a smear not a triad"),
        ("pedal_point", "Pedal point", "pedal point", "Hold a pedal so the upper chords can move against a floor"),
        ("static_vamp", "Static vamp", "static vamp", "Vamp one loop so the verse can talk without a change"),
    ]
    fillers = [
        (f"fill_{i:02d}", f"Harmony color {i + 1}", f"harmony color {i + 1}")
        for i in range(90)
    ]
    return _pad("hrm", "harmony", authored, fillers)


def instruments_texture() -> list[dict[str, Any]]:
    authored = [
        ("piano_stab", "Sampled piano stab", "sampled piano stab", "Stab a sampled piano so boom-bap has a chopped-ivory hook"),
        ("rhodes", "Rhodes", "rhodes", "Lay a Rhodes so lo-fi hop has a sleepy electric piano"),
        ("warped_saw", "Warped supersaw", "warped supersaw", "Warp a supersaw so the hybrid-trap drop has a detuned scream"),
        ("organ_stabs", "Organ stabs", "organ stabs", "Stab organ so gospel-rap has a church-machine accent"),
        ("nylon_guitar", "Nylon guitar", "nylon guitar", "Finger nylon guitar so bossa has a quiet sparkle"),
        ("tele_twang", "Twang guitar", "twang guitar", "Twang a guitar so country has a story on the two and four"),
        ("banjo_roll", "Banjo rolls", "banjo rolls", "Roll banjo so bluegrass sprints in eighths"),
        ("horn_stack", "Stacked horns", "stacked horns", "Stack horns so soul has a punch on the offbeat"),
        ("string_stab", "String stabs", "string stabs", "Stab strings so disco glitter sits on the offbeat"),
        ("talkbox_synth", "Talk-box synth", "talk-box synth", "Talk-box a synth so west-coast funk rap has a high whine lead"),
        ("choir_pad", "Choir pad", "choir pads", "Pad a choir so the testimony cadence has air"),
        ("flute_lead", "Flute lead", "flute lead", "Lead a flute so the hook can sing without a throat"),
        ("violin_ornament", "Ornamented fiddle", "fiddle ornaments", "Ornament a fiddle so the reel never sits on a plain note"),
        ("bandoneon", "Bandoneon", "bandoneon", "Sigh a bandoneon so tango has a lung"),
        ("accordion", "Accordion", "accordion", "Riff accordion so zydeco has a two-step engine"),
        ("steel_pan", "Steel pan", "steel pan", "Tune pans so calypso sparkle is pitched metal"),
        ("koto_chamber", "Chamber plucked", "chamber plucked strings", "Pluck a chamber string so the texture is wood and nail"),
        ("harp_gliss", "Harp gliss", "harp gliss", "Gliss a harp so the section change is a cascade"),
        ("kalimba", "Kalimba", "kalimba", "Pluck kalimba so the bed has a small metal thumb"),
        ("music_box", "Music box", "music box", "Tink a music box so the motif is tiny and nostalgic"),
    ]
    fillers = [
        (f"fill_{i:02d}", f"Instrument color {i + 1}", f"instrument color {i + 1}")
        for i in range(90)
    ]
    extra = {
        "warped_saw": {"podcast_ok": False},
    }
    return _pad("ins", "instruments", authored, fillers, extra)


def vocal_identity() -> list[dict[str, Any]]:
    authored = [
        ("dry_booth", "Dry booth rap", "male rap vocals, dry booth, no autotune", "Keep a dry booth rap vocal with no pitch toy so the take is the take"),
        ("spoken", "Spoken word", "spoken word vocals", "Speak the bars as lecture so the cadence is talk not song"),
        ("stacked_doubles", "Stacked doubles", "stacked vocal doubles", "Stack doubles on the hook so the chorus is a small crowd of one throat"),
        ("choir", "Invented choir", "choir vocals", "Invent a choir stack so the hook has SATB air without a living group"),
        ("sung_hook", "Sung hook", "sung hook", "Sing the hook so the chorus carries more than the verse"),
        ("no_autotune", "No autotune", "no autotune", "Leave pitch human so the booth stays dry"),
        ("close_whisper", "Close whisper", "close whisper vocal", "Whisper close so the verse is almost a breath"),
        ("shout_chant", "Shout chant", "shout chant vocals", "Shout a chant so the hook is a crowd call"),
        ("sung_rap", "Sung-rap hybrid", "sung-rap hybrid", "Blend sung and rapped lines so the identity sits between speech and song"),
        ("low_baritone", "Low baritone", "low baritone rap", "Sit a low baritone so the chest is the timbre"),
        ("high_tenor", "High tenor", "high tenor rap", "Sit a high tenor so the urgency is in the upper chest"),
        ("duo_trade", "Duo trade", "two-voice trade", "Trade bars between two invented voices so the verse is a conversation"),
        ("gang_yes", "Gang yes", "gang vocals", "Gang a yes on the hook so the crowd is invented not sampled famous"),
        ("kids_none", "Adult only", "adult vocals only", "Keep adult invented voices so no child timbre enters the take"),
        ("adlib_air", "Ad-lib air", "ad-lib vocals", "Air ad-libs between lines so the pocket has invented chatter"),
        ("harmony_third", "Harmony third", "harmony thirds", "Stack a third under the hook so the chorus is a small choir of one"),
        ("unison_double", "Unison double", "unison double", "Unison-double the verse so the body is thicker without a new melody"),
        ("call_response", "Call and response", "call and response vocals", "Call and respond so the hook answers itself"),
        ("no_vocal", "No vocal", "no vocals", "Leave the lane instrumental so the bed has no throat"),
        ("dry_female", "Dry booth sung", "sung vocals, dry booth, no autotune", "Keep a dry sung booth with no pitch toy so the identity is invented and plain"),
    ]
    fillers = [
        (f"fill_{i:02d}", f"Vocal color {i + 1}", f"vocal color {i + 1}")
        for i in range(90)
    ]
    extra = {
        "dry_booth": {"instrumental_ok": False, "podcast_ok": False},
        "no_vocal": {"vocal_ok": False},
        "shout_chant": {"podcast_ok": False},
    }
    # Default vocal techniques are not podcast beds.
    for slug, _, _, _ in authored:
        extra.setdefault(slug, {})
        extra[slug].setdefault("podcast_ok", False)
        extra[slug].setdefault("instrumental_ok", False)
    extra["no_vocal"] = {"vocal_ok": False, "instrumental_ok": True, "podcast_ok": True}
    return _pad("voc", "vocal", authored, fillers, extra)


def mix_production() -> list[dict[str, Any]]:
    authored = [
        ("vinyl", "Vinyl dirt", "vinyl crackle, dusty mix", "Lay vinyl dirt so the hop has a crate hiss without a stock name"),
        ("dry_booth_mix", "Dry booth mix", "dry booth mix", "Keep the vocal dry in the mix so the booth is glass"),
        ("club_loud", "Club loudness", "club loudness", "Push club loudness so the drop has competitive weight"),
        ("sidechain", "Sidechain pump", "sidechain pump", "Pump sidechain so the kick punches a hole in the pad"),
        ("tape_hiss", "Tape hiss", "tape hiss", "Leave tape hiss so the lo-fi bed has air noise"),
        ("analog_warm", "Analog warmth", "analog warmth", "Warm analog-leaning so the midrange is round"),
        ("digital_clip", "Digital clip", "digital clip color", "Clip digital-small so the transients have a square edge"),
        ("narrow_radio", "Narrow radio", "narrow radio mix", "Narrow the mix so it reads like a small radio without a platform name"),
        ("wide_chorus", "Wide chorus mix", "wide chorus mix", "Widen the chorus so the hook is physically larger than the verse"),
        ("mono_low", "Mono low end", "mono low end", "Mono the low end so the sub is center"),
        ("no_verb_vocal", "No-verb vocal", "dry vocal", "Withhold vocal reverb so the booth stays close"),
        ("plate_vocal", "Plate vocal", "plate vocal", "Plate the vocal small so there is a metal room not a hall"),
        ("parallel_crush", "Parallel crush", "parallel crush", "Crush a parallel bus so the drums have weight without losing transients"),
        ("sample_rate_down", "Downsampled dirt", "downsampled dirt", "Downsample dirt so the crunch is a bit-depth cousin"),
        ("telephone", "Telephone band", "telephone band", "Telephone-band a throw so the ad-lib is small and mid"),
        ("loud_quiet", "Loud-quiet", "loud-quiet contrast", "Contrast loud and quiet so the drop is a dynamic not just a filter"),
        ("bus_glue", "Bus glue", "bus glue", "Glue the bus gently so the kit feels like one instrument"),
        ("no_master_toy", "Clean master", "clean master", "Leave the master clean so loudness is not a smashed brick"),
        ("podcast_duck", "Speech duck", "ducked under speech", "Duck the bed under speech so the host always wins"),
        ("sting_bright", "Bright sting", "bright sting mix", "Brighten a sting so two bars cut through a talk bed"),
    ]
    fillers = [
        (f"fill_{i:02d}", f"Mix color {i + 1}", f"mix color {i + 1}")
        for i in range(90)
    ]
    extra: dict[str, dict[str, Any]] = {
        "vinyl": {"conflicts": ("mix_digital_clip",)},
        "club_loud": {"podcast_ok": False},
        "sidechain": {"podcast_ok": False},
        "podcast_duck": {"vocal_ok": False},
    }
    return _pad("mix", "mix", authored, fillers, extra)


def space_ambience() -> list[dict[str, Any]]:
    authored = [
        ("booth_dry", "Booth dry", "dry booth space", "Keep booth dry so there is almost no room around the throat"),
        ("hall", "Hall verb", "hall reverb", "Throw a hall so the choir pad has a nave"),
        ("mono_drums", "Mono drums", "mono drums", "Mono the drums so the kit is a center punch"),
        ("wide_chorus_space", "Wide chorus space", "wide chorus", "Widen the chorus so the hook is a stereo event"),
        ("haas", "Haas width", "haas width", "Haas-width a pad so the sides are a delay cousin not a new part"),
        ("room_kit", "Small room kit", "small room kit", "Room the kit small so the drums have walls not a cavern"),
        ("chamber", "Chamber", "chamber reverb", "Chamber the vocal so the metal room is short"),
        ("plate", "Plate space", "plate reverb", "Plate the snare so the decay is metal not stone"),
        ("spring", "Spring", "spring reverb", "Spring the guitar so the decay is a tank"),
        ("cathedral", "Cathedral", "cathedral reverb", "Cathedral the organ so liturgy has a long tail"),
        ("outside", "Outside air", "outside air", "Leave outside air so the folk guitar has wind not a studio"),
        ("tunnel", "Tunnel", "tunnel ambience", "Tunnel the rumble so subway mood has a tube"),
        ("closet", "Closet", "closet dry", "Closet-dry the vocal so the booth is almost dead"),
        ("bathroom", "Tile slap", "tile slap", "Tile-slap a short slapback so the room is hard"),
        ("warehouse", "Warehouse", "warehouse space", "Warehouse the kick so techno has a long industrial air"),
        ("nearfield", "Nearfield", "nearfield dry", "Nearfield-dry the mix so it feels like speakers at a desk"),
        ("binaural_hint", "Close binaural", "close binaural", "Close-binaural a bed so headphones feel inside the room without a brand"),
        ("no_space", "No space", "no added space", "Add no space so the dry take is the aesthetic"),
        ("far_mic", "Far mic", "far mic", "Far-mic the source so the room is the instrument"),
        ("podcast_close", "Podcast close", "close podcast space", "Close the bed space so speech stays in front"),
    ]
    fillers = [
        (f"fill_{i:02d}", f"Space color {i + 1}", f"space color {i + 1}")
        for i in range(90)
    ]
    extra: dict[str, dict[str, Any]] = {
        "booth_dry": {"conflicts": ("spa_cathedral",)},
        "cathedral": {"conflicts": ("spa_booth_dry",)},
        "warehouse": {"podcast_ok": False},
    }
    return _pad("spa", "space", authored, fillers, extra)


def sound_design_fx() -> list[dict[str, Any]]:
    authored = [
        ("tape_stop", "Tape stop", "tape stop", "Tape-stop a bar so the grid melts down before the next section"),
        ("riser", "Riser", "riser", "Rise a noise so the drop is announced without a vocal"),
        ("vinyl_stop", "Vinyl stop", "vinyl stop", "Vinyl-stop so the record feels grabbed"),
        ("reverse_cymbal", "Reverse cymbal", "reverse cymbal", "Reverse a cymbal so the swell is backward metal"),
        ("bitcrush", "Bitcrush", "bitcrush", "Bitcrush a throw so the crunch is a low-depth cousin"),
        ("filter_open", "Filter open", "filter open", "Open a filter so the chorus arrives as brightness"),
        ("filter_close", "Filter close", "filter close", "Close a filter so the verse is small"),
        ("impact", "Impact", "impact hit", "Impact a low hit so the section change is a body punch"),
        ("glitch_stutter", "Glitch stutter", "glitch stutter", "Glitch-stutter a grain so the fill is a broken repeat"),
        ("rewind", "Rewind", "rewind", "Rewind a bar so jungle energy can jump back"),
        ("silence_gap", "Silence gap", "silence gap", "Gap a silence so the next hit is larger"),
        ("white_sweep", "White sweep", "white-noise sweep", "Sweep white noise so the transition is air not a chord"),
        ("sub_drop", "Sub drop", "sub drop", "Drop a sub so the downbeat has a fall-in"),
        ("pitch_up", "Pitch up", "pitch-up fill", "Pitch-up a fill so the energy climbs a tone"),
        ("pitch_down", "Pitch down", "pitch-down fill", "Pitch-down a fill so the energy sags into the hook"),
        ("granular_wash", "Granular wash", "granular wash", "Wash granular so the pad is particles"),
        ("no_fx", "No FX", "no transition fx", "Skip transition FX so the cut is a hard edit"),
        ("sting_hit_fx", "Sting hit FX", "sting hit", "Hit a sting so two bars can ident a show"),
        ("bed_none", "Bed-safe none", "no drop fx", "Skip drop FX so a speech bed never dumps a club transition"),
        ("laser_zap", "Zap", "zap fx", "Zap a short tone so the fill is comic without a cartoon brand"),
    ]
    fillers = [
        (f"fill_{i:02d}", f"Design color {i + 1}", f"design color {i + 1}")
        for i in range(90)
    ]
    extra = {
        "tape_stop": {"podcast_ok": False},
        "riser": {"podcast_ok": False},
        "sub_drop": {"podcast_ok": False},
        "bed_none": {"vocal_ok": False},
    }
    return _pad("sfx", "design", authored, fillers, extra)


def use_case() -> list[dict[str, Any]]:
    authored = [
        ("draft_32", "32s draft", "32 second draft", "Cut a 32-second draft so the first Queue is a sketch not an album"),
        ("full_96", "96s full", "96 second full take", "Hold a 96-second full take so the draft can grow a second verse"),
        ("album_180", "180s album take", "180 second album take", "Hold a 180-second album take so the form can be verse chorus verse chorus outro"),
        ("podcast_30", "30s bed", "30 second instrumental bed", "Loop a 30-second bed so speech can sit on a repeating instrumental"),
        ("bumper", "Short bumper", "short bumper sting", "Cut a short bumper so a scene can ident in a few seconds"),
        ("radio_sting", "Radio sting", "radio sting", "Cut a radio sting so an episode can open with two bars"),
        ("underscore", "Picture underscore", "picture underscore", "Underscore picture so the score threatens without a pop hook"),
        ("commute_recap", "Commute recap bed", "short recap bed", "Bed a commute recap so the explainer has a quiet loop"),
        ("club_drop", "Club drop use", "club drop", "Build a club drop so the instrumental is for a floor not a booth"),
        ("afterparty", "Afterparty closer", "afterparty closer", "Close an afterparty so the last take is warped bass not a rap verse"),
        ("lecture", "Lecture bed", "lecture bed", "Bed a lecture so spoken word has a spare hop underneath"),
        ("ident", "Show ident", "show ident", "Ident a show so the sting is a brand without a platform name"),
        ("loop_seamless", "Seamless loop", "seamless loop", "Loop seamless so a bed can repeat under a long host"),
        ("one_shot", "One-shot hit", "one-shot hit", "One-shot a hit so a button can play a single event"),
        ("hook_first", "Hook first", "hook first", "Lead with the hook so the first four bars are the chorus"),
        ("verse_first", "Verse first", "verse first", "Lead with the verse so the story arrives before the hook"),
        ("drop_first", "Drop first", "drop first", "Lead with the drop so the instrumental dumps weight immediately"),
        ("no_drop", "No drop", "no drop", "Skip the drop so a speech bed never dumps a club transition"),
        ("album_opener", "Album opener", "album opener", "Open an album so the first take is an intro not a peak"),
        ("album_closer", "Album closer", "album closer", "Close an album so the last take is an outro"),
    ]
    fillers = [
        (f"fill_{i:02d}", f"Use color {i + 1}", f"use color {i + 1}")
        for i in range(90)
    ]
    extra: dict[str, dict[str, Any]] = {
        "drop_first": {"conflicts": ("gen_boom_bap",), "podcast_ok": False},
        "club_drop": {"podcast_ok": False},
        "afterparty": {"podcast_ok": False},
        "podcast_30": {"vocal_ok": False},
        "no_drop": {"conflicts": ("use_drop_first",)},
    }
    return _pad("use", "use", authored, fillers, extra)


def tempo_groove() -> list[dict[str, Any]]:
    authored = [
        ("88", "Boom-bap 88", "88 bpm", "Hold eighty-eight so the dusty pocket can breathe", {"bpm": "88 bpm"}),
        ("86", "Lo-fi 86", "86 bpm", "Hold eighty-six so the Rhodes can lag the grid", {"bpm": "86 bpm"}),
        ("92", "Hop 92", "92 bpm", "Hold ninety-two so the lecture cadence still walks", {"bpm": "92 bpm"}),
        ("70", "Slow 70", "70 bpm", "Hold seventy so the ballad almost stops", {"bpm": "70 bpm"}),
        ("100", "Head-nod 100", "100 bpm", "Hold one hundred so the nod is walking speed", {"bpm": "100 bpm"}),
        ("118", "House 118", "118 bpm", "Hold one-eighteen so deep house can roll", {"bpm": "118 bpm"}),
        ("128", "Four-floor 128", "128 bpm", "Hold one-twenty-eight so the club four-floor is standard", {"bpm": "128 bpm"}),
        ("140", "Trap 140", "140 bpm, half-time", "Hold one-forty half-time so trap hats sprint over a slow snare", {"bpm": "140 bpm"}),
        ("160", "Footwork 160", "160 bpm", "Hold one-sixty so footwork kicks can chatter", {"bpm": "160 bpm"}),
        ("174", "DnB 174", "174 bpm", "Hold one-seventy-four so drum-and-bass can sprint", {"bpm": "174 bpm"}),
        ("96", "Pocket 96", "96 bpm", "Hold ninety-six so the southern pocket can lean", {"bpm": "96 bpm"}),
        ("108", "Reggae 108", "108 bpm", "Hold one-oh-eight so one-drop has air", {"bpm": "108 bpm"}),
        ("112", "Soul 112", "112 bpm", "Hold one-twelve so tambourine two-and-four can dance", {"bpm": "112 bpm"}),
        ("120", "Straight 120", "120 bpm", "Hold one-twenty so the click is a round number", {"bpm": "120 bpm"}),
        ("75", "Dirge 75", "75 bpm", "Hold seventy-five so the funeral pad can walk", {"bpm": "75 bpm"}),
        ("80", "Night 80", "80 bpm", "Hold eighty so night R&B can sit late", {"bpm": "80 bpm"}),
        ("84", "Trip-hop 84", "84 bpm", "Hold eighty-four so the dusty break can smoke", {"bpm": "84 bpm"}),
        ("90", "Gospel 90", "90 bpm", "Hold ninety so the testimony cadence can breathe", {"bpm": "90 bpm"}),
        ("102", "Funk 102", "102 bpm", "Hold one-oh-two so sixteenth hats can chick", {"bpm": "102 bpm"}),
        ("134", "Techno 134", "134 bpm", "Hold one-thirty-four so the warehouse kick can hypnotize", {"bpm": "134 bpm"}),
    ]
    cores: list[tuple[str, str, str, str]] = []
    extra: dict[str, dict[str, Any]] = {}
    for item in authored:
        slug, label, tags, clause, meta = item
        cores.append((slug, label, tags, clause))
        extra[slug] = dict(meta)
    fillers: list[tuple[str, str, str]] = []
    for i in range(90):
        bpm_n = 60 + i
        slug = f"fill_{i:02d}"
        fillers.append((slug, f"Tempo {bpm_n}", f"{bpm_n} bpm"))
        extra[slug] = {"bpm": f"{bpm_n} bpm"}
    extra["140"]["conflicts"] = ("tmp_88",)
    extra["174"]["podcast_ok"] = False
    extra["160"]["podcast_ok"] = False
    return _pad("tmp", "tempo", cores, fillers, extra)


def arrangement_form() -> list[dict[str, Any]]:
    authored = [
        (
            "verse_chorus",
            "Verse chorus",
            "",
            "Open verse then chorus so the hook answers the story",
            {
                "lyrics_form": "[verse]\n\n[chorus]",
                "lyrics_form_inst": "[inst]\n\n[inst]",
            },
        ),
        (
            "intro_verse_chorus",
            "Intro verse chorus",
            "",
            "Intro then verse then chorus so the take can greet before it talks",
            {
                "lyrics_form": "[intro]\n\n[verse]\n\n[chorus]",
                "lyrics_form_inst": "[inst]\n\n[inst]\n\n[inst]",
            },
        ),
        (
            "spoken_intro",
            "Spoken intro",
            "",
            "Speak an intro then verse so the lecture can start talking",
            {
                "lyrics_form": "[spoken word]\n\n[verse]\n\n[chorus]",
                "lyrics_form_inst": "[inst]\n\n[inst]",
            },
        ),
        (
            "drop_first",
            "Drop first",
            "",
            "Drop first then ride so the instrumental dumps weight immediately",
            {
                "lyrics_form": "[drop]\n\n[verse]\n\n[chorus]",
                "lyrics_form_inst": "[drop]\n\n[inst]\n\n[outro]",
                "podcast_ok": False,
            },
        ),
        (
            "inst_bed",
            "Instrumental bed",
            "",
            "Hold an empty-body instrumental so ACE does not sing free text",
            {
                "lyrics_form": "[inst]",
                "lyrics_form_inst": "[inst]",
                "vocal_ok": False,
            },
        ),
        (
            "album_180",
            "Album-length form",
            "",
            "Verse chorus verse chorus outro so a 180-second take can turn twice",
            {
                "lyrics_form": "[intro]\n\n[verse]\n\n[chorus]\n\n[verse]\n\n[chorus]\n\n[outro]",
                "lyrics_form_inst": "[inst]\n\n[drop]\n\n[inst]\n\n[outro]",
            },
        ),
        (
            "hook_only",
            "Hook only",
            "",
            "Chorus only so a short draft is all hook",
            {
                "lyrics_form": "[chorus]",
                "lyrics_form_inst": "[inst]",
            },
        ),
        (
            "verse_only",
            "Verse only",
            "",
            "Verse only so a sketch can talk without a hook",
            {
                "lyrics_form": "[verse]",
                "lyrics_form_inst": "[inst]",
            },
        ),
        (
            "sting_form",
            "Sting form",
            "",
            "One ident hit then silence so two bars can brand a show",
            {
                "lyrics_form": "[inst]",
                "lyrics_form_inst": "[inst]",
                "vocal_ok": False,
            },
        ),
        (
            "outro_fade",
            "Outro fade",
            "",
            "Land on outro so the take can leave instead of chopping",
            {
                "lyrics_form": "[verse]\n\n[chorus]\n\n[outro]",
                "lyrics_form_inst": "[inst]\n\n[outro]",
            },
        ),
        (
            "double_chorus",
            "Double chorus",
            "",
            "Repeat the chorus so the hook is the arrangement",
            {
                "lyrics_form": "[verse]\n\n[chorus]\n\n[chorus]",
                "lyrics_form_inst": "[inst]\n\n[drop]\n\n[drop]",
            },
        ),
        (
            "bridge",
            "Bridge then chorus",
            "",
            "Bridge then last chorus so the take can turn once before the hook returns",
            {
                "lyrics_form": "[verse]\n\n[chorus]\n\n[bridge]\n\n[chorus]",
                "lyrics_form_inst": "[inst]\n\n[drop]\n\n[inst]\n\n[drop]",
            },
        ),
        (
            "podcast_loop",
            "Podcast loop form",
            "",
            "Single [inst] loop so a 30-second bed can repeat under speech",
            {
                "lyrics_form": "[inst]",
                "lyrics_form_inst": "[inst]",
                "vocal_ok": False,
            },
        ),
        (
            "drop_only",
            "Drop only",
            "",
            "Drop only so the instrumental is all weight",
            {
                "lyrics_form": "[drop]",
                "lyrics_form_inst": "[drop]",
                "vocal_ok": False,
                "podcast_ok": False,
            },
        ),
        (
            "intro_only",
            "Intro only",
            "",
            "Intro only so the take is a greeting",
            {
                "lyrics_form": "[intro]",
                "lyrics_form_inst": "[inst]",
            },
        ),
        (
            "spoken_only",
            "Spoken only",
            "",
            "Spoken-word only so the lecture never becomes a sung hook",
            {
                "lyrics_form": "[spoken word]",
                "lyrics_form_inst": "[inst]",
            },
        ),
        (
            "verse_verse",
            "Two verses",
            "",
            "Two verses then chorus so the story can talk twice before the hook",
            {
                "lyrics_form": "[verse]\n\n[verse]\n\n[chorus]",
                "lyrics_form_inst": "[inst]\n\n[inst]\n\n[drop]",
            },
        ),
        (
            "chorus_verse",
            "Chorus first",
            "",
            "Chorus then verse so the hook arrives before the story",
            {
                "lyrics_form": "[chorus]\n\n[verse]\n\n[chorus]",
                "lyrics_form_inst": "[drop]\n\n[inst]\n\n[drop]",
            },
        ),
        (
            "cold_open",
            "Cold open",
            "",
            "Cold-open on verse with no intro so the first word is the story",
            {
                "lyrics_form": "[verse]\n\n[chorus]\n\n[outro]",
                "lyrics_form_inst": "[inst]\n\n[outro]",
            },
        ),
        (
            "inst_drop_outro",
            "Inst drop outro",
            "",
            "Instrumental drop then outro so a Drive-through take can dump then leave",
            {
                "lyrics_form": "[inst]\n\n[drop]\n\n[outro]",
                "lyrics_form_inst": "[inst]\n\n[drop]\n\n[outro]",
                "vocal_ok": False,
                "podcast_ok": False,
            },
        ),
    ]
    cores: list[tuple[str, str, str, str]] = []
    extra: dict[str, dict[str, Any]] = {}
    for slug, label, tags, clause, meta in authored:
        cores.append((slug, label, tags, clause))
        extra[slug] = dict(meta) if isinstance(meta, dict) else {}
    fillers: list[tuple[str, str, str]] = []
    for i in range(90):
        slug = f"fill_{i:02d}"
        fillers.append((slug, f"Form color {i + 1}", ""))
        extra[slug] = {
            "lyrics_form": f"[verse]\n\n[chorus]\n\n[form-{i + 1}]",
            "lyrics_form_inst": "[inst]",
        }
    extra["drop_first"]["conflicts"] = ("frm_inst_bed",)
    return _pad("frm", "form", cores, fillers, extra)


def recipes() -> list[dict[str, Any]]:
    return [
        {
            "id": "rec_boom_bap_draft",
            "label": "Boom-bap draft",
            "axes": {
                "genre_style": "gen_boom_bap",
                "tempo_groove": "tmp_88",
                "drums_rhythm": "drm_dusty_pocket",
                "bass_low_end": "bass_upright",
                "instruments_texture": "ins_piano_stab",
                "vocal_identity": "voc_dry_booth",
                "arrangement_form": "frm_intro_verse_chorus",
                "mix_production": "mix_vinyl",
                "space_ambience": "spa_booth_dry",
                "mood_energy": "mood_laid_back",
                "use_case": "use_draft_32",
            },
        },
        {
            "id": "rec_trap_halftime",
            "label": "Trap half-time",
            "axes": {
                "genre_style": "gen_trap",
                "tempo_groove": "tmp_140",
                "drums_rhythm": "drm_trap_hats",
                "bass_low_end": "bass_slide_808",
                "vocal_identity": "voc_dry_booth",
                "arrangement_form": "frm_verse_chorus",
                "mood_energy": "mood_menace",
                "use_case": "use_full_96",
            },
        },
        {
            "id": "rec_lofi_night",
            "label": "Lo-fi night",
            "axes": {
                "genre_style": "gen_lofi_hiphop",
                "tempo_groove": "tmp_86",
                "drums_rhythm": "drm_lofi_sleepy",
                "instruments_texture": "ins_rhodes",
                "mix_production": "mix_tape_hiss",
                "mood_energy": "mood_nocturnal",
                "use_case": "use_podcast_30",
            },
        },
        {
            "id": "rec_spoken_lecture",
            "label": "Spoken lecture",
            "axes": {
                "genre_style": "gen_spoken_hop",
                "tempo_groove": "tmp_88",
                "drums_rhythm": "drm_dusty_pocket",
                "vocal_identity": "voc_spoken",
                "arrangement_form": "frm_spoken_intro",
                "mood_energy": "mood_civic_serious",
                "use_case": "use_lecture",
            },
        },
        {
            "id": "rec_club_rap_over",
            "label": "Club rap-over",
            "axes": {
                "genre_style": "gen_trap",
                "tempo_groove": "tmp_140",
                "drums_rhythm": "drm_trap_hats",
                "bass_low_end": "bass_slide_808",
                "vocal_identity": "voc_dry_booth",
                "mix_production": "mix_club_loud",
                "use_case": "use_club_drop",
            },
        },
        {
            "id": "rec_drive_through_drop",
            "label": "Drive-through drop",
            "axes": {
                "genre_style": "gen_hybrid_trap",
                "tempo_groove": "tmp_140",
                "drums_rhythm": "drm_trap_hats",
                "bass_low_end": "bass_chest_sub",
                "instruments_texture": "ins_warped_saw",
                "arrangement_form": "frm_drop_first",
                "sound_design_fx": "sfx_riser",
                "use_case": "use_drop_first",
            },
        },
        {
            "id": "rec_podcast_explainer",
            "label": "Podcast explainer bed",
            "axes": {
                "genre_style": "gen_podcast_lofi",
                "tempo_groove": "tmp_86",
                "drums_rhythm": "drm_podcast_tick",
                "arrangement_form": "frm_podcast_loop",
                "mix_production": "mix_podcast_duck",
                "space_ambience": "spa_podcast_close",
                "sound_design_fx": "sfx_bed_none",
                "use_case": "use_podcast_30",
            },
        },
        {
            "id": "rec_radio_sting",
            "label": "Radio sting",
            "axes": {
                "genre_style": "gen_radio_sting",
                "arrangement_form": "frm_sting_form",
                "mix_production": "mix_sting_bright",
                "sound_design_fx": "sfx_sting_hit_fx",
                "use_case": "use_radio_sting",
            },
        },
        {
            "id": "rec_jazz_rap_pocket",
            "label": "Jazz-rap pocket",
            "axes": {
                "genre_style": "gen_jazz_rap",
                "tempo_groove": "tmp_88",
                "drums_rhythm": "drm_brushes",
                "bass_low_end": "bass_walking",
                "vocal_identity": "voc_dry_booth",
                "harmony_mode": "hrm_dorian",
            },
        },
        {
            "id": "rec_gospel_stack",
            "label": "Gospel stack",
            "axes": {
                "genre_style": "gen_gospel_rap",
                "tempo_groove": "tmp_90",
                "instruments_texture": "ins_organ_stabs",
                "vocal_identity": "voc_choir",
                "harmony_mode": "hrm_gospel_251",
                "space_ambience": "spa_hall",
            },
        },
        {
            "id": "rec_dark_underscore",
            "label": "Dark underscore",
            "axes": {
                "genre_style": "gen_underscore",
                "drums_rhythm": "drm_underscore_none",
                "bass_low_end": "bass_drone_fifth",
                "harmony_mode": "hrm_phrygian",
                "arrangement_form": "frm_inst_bed",
                "mood_energy": "mood_menace",
                "use_case": "use_underscore",
            },
        },
        {
            "id": "rec_four_floor_house",
            "label": "Four-on-floor house",
            "axes": {
                "genre_style": "gen_four_on_floor",
                "tempo_groove": "tmp_128",
                "drums_rhythm": "drm_four_floor",
                "bass_low_end": "bass_octave_disco",
                "arrangement_form": "frm_inst_drop_outro",
                "use_case": "use_club_drop",
            },
        },
        {
            "id": "rec_ambient_drone",
            "label": "Ambient drone bed",
            "axes": {
                "genre_style": "gen_drone",
                "drums_rhythm": "drm_underscore_none",
                "bass_low_end": "bass_none_bass",
                "arrangement_form": "frm_inst_bed",
                "mood_energy": "mood_glacial",
                "use_case": "use_underscore",
            },
        },
        {
            "id": "rec_drill_bounce",
            "label": "Drill bounce",
            "axes": {
                "genre_style": "gen_drill",
                "tempo_groove": "tmp_140",
                "drums_rhythm": "drm_trap_hats",
                "bass_low_end": "bass_slide_808",
                "vocal_identity": "voc_dry_booth",
                "mood_energy": "mood_menace",
            },
        },
        {
            "id": "rec_civic_progress",
            "label": "Civic progress",
            "axes": {
                "genre_style": "gen_spoken_hop",
                "tempo_groove": "tmp_88",
                "drums_rhythm": "drm_dusty_pocket",
                "vocal_identity": "voc_spoken",
                "arrangement_form": "frm_spoken_intro",
                "mood_energy": "mood_civic_serious",
                "harmony_mode": "hrm_dorian",
            },
        },
        {
            "id": "rec_dry_booth_double",
            "label": "Dry booth double-time",
            "axes": {
                "genre_style": "gen_boom_bap",
                "tempo_groove": "tmp_92",
                "drums_rhythm": "drm_double_hats",
                "vocal_identity": "voc_dry_booth",
                "arrangement_form": "frm_verse_chorus",
                "space_ambience": "spa_booth_dry",
            },
        },
        {
            "id": "rec_album_180",
            "label": "Album-length form",
            "axes": {
                "genre_style": "gen_boom_bap",
                "tempo_groove": "tmp_88",
                "drums_rhythm": "drm_dusty_pocket",
                "vocal_identity": "voc_dry_booth",
                "arrangement_form": "frm_album_180",
                "use_case": "use_album_180",
            },
        },
        {
            "id": "rec_short_bumper",
            "label": "Short bumper sting",
            "axes": {
                "genre_style": "gen_radio_sting",
                "arrangement_form": "frm_sting_form",
                "sound_design_fx": "sfx_sting_hit_fx",
                "use_case": "use_bumper",
                "mix_production": "mix_sting_bright",
            },
        },
        {
            "id": "rec_vinyl_crate",
            "label": "Vinyl crate",
            "axes": {
                "genre_style": "gen_boom_bap",
                "tempo_groove": "tmp_88",
                "drums_rhythm": "drm_dusty_pocket",
                "mix_production": "mix_vinyl",
                "instruments_texture": "ins_piano_stab",
                "mood_energy": "mood_laid_back",
            },
        },
        {
            "id": "rec_warped_afterparty",
            "label": "Warped bass afterparty",
            "axes": {
                "genre_style": "gen_hybrid_trap",
                "tempo_groove": "tmp_140",
                "bass_low_end": "bass_chest_sub",
                "instruments_texture": "ins_warped_saw",
                "arrangement_form": "frm_inst_drop_outro",
                "use_case": "use_afterparty",
            },
        },
    ]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    _dump("genre_style.json", genre_style())
    _dump("mood_energy.json", mood_energy())
    _dump("drums_rhythm.json", drums_rhythm())
    _dump("bass_low_end.json", bass_low_end())
    _dump("harmony_mode.json", harmony_mode())
    _dump("instruments_texture.json", instruments_texture())
    _dump("vocal_identity.json", vocal_identity())
    _dump("mix_production.json", mix_production())
    _dump("space_ambience.json", space_ambience())
    _dump("sound_design_fx.json", sound_design_fx())
    _dump("use_case.json", use_case())
    _dump("tempo_groove.json", tempo_groove())
    _dump("arrangement_form.json", arrangement_form())
    path = OUT / "recipes.json"
    recs = recipes()
    path.write_text(json.dumps(recs, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} ({len(recs)})")


if __name__ == "__main__":
    main()








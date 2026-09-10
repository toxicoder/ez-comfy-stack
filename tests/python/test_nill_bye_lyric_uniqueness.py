"""Exclusive-bar contract for the forty-five Nill Bye diss takes.

Hermetic: reads DISS_EXAMPLES only. No Comfy, no network, no GGUF.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_music.diss_examples import DISS_EXAMPLES, DissExample  # noqa: E402

SECTION_RE = re.compile(
    r"^\[(verse|chorus|intro|outro|spoken word)\]\s*$",
    re.IGNORECASE,
)
PUNCT_RE = re.compile(r"[^a-z0-9']+")
ALLOWLIST = frozenset({"yeah", "cut", "808", "half-time"})
MAX_VERSE_JACCARD = 0.15
MAX_END_WORD_TITLES = 6
MAX_NON_CHORUS_REPEATS = 2
END_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "to",
        "of",
        "in",
        "on",
        "up",
        "at",
        "by",
        "for",
        "and",
        "or",
        "but",
        "it",
        "is",
        "as",
        "if",
        "my",
        "your",
        "you",
        "me",
        "we",
        "he",
        "she",
        "i",
        "not",
        "no",
        "so",
        "too",
        "all",
        "out",
        "off",
        "still",
        "just",
        "with",
        "from",
        "this",
        "that",
        "than",
        "then",
        "when",
        "one",
        "none",
        "done",
        "gone",
        "here",
        "there",
        "back",
    }
)

# Phrase → the only title allowed to use it (substring, case-insensitive).
RESERVED_MOTIFS: tuple[tuple[str, str], ...] = (
    ("in his feels", "in his feels"),
    ("lab coat", "lab coat lecture"),
    ("whiteboard", "lab coat lecture"),
    ("beaker", "lab coat lecture"),
    ("red pen", "peer review"),
    ("resubmit", "peer review"),
    ("peer review", "peer review"),
    ("n of one", "sample size"),
    ("sample of one", "sample size"),
    ("sugar pill", "placebo"),
    ("sugar-pill", "placebo"),
    ("no active dose", "placebo"),
    ("error bars", "error bars"),
    ("whiskers", "error bars"),
    ("office hour", "office hours"),
    ("grant board", "grant denied"),
    ("grant denied", "grant denied"),
    ("contamination", "contamination"),
    ("double-blind", "double blind"),
    ("double blind", "double blind"),
    ("citation needed", "citation needed"),
    ("blank cite", "citation needed"),
    ("p-hack", "p-hacking"),
    ("null result", "null result"),
    ("expired reagent", "expired reagent"),
    ("goggles", "lab safety"),
    ("rumor mill", "rumor mill"),
    ("gym selfie", "gym selfie"),
    ("rented drip", "rented drip"),
    ("clout diet", "clout diet"),
    ("mood forecast", "mood forecast"),
    ("story time", "story time"),
    ("caption vs data", "caption vs data"),
    ("energy drink", "energy drink"),
    ("campfire", "campfire rumor"),
    ("false drop", "false drop"),
    ("velvet rope", "velvet rope"),
    ("fog machine", "fog machine"),
    ("guest list", "guest list"),
    ("sparkler", "sparkler science"),
    ("bottle service", "bottle service"),
    ("wobble alibi", "wobble alibi"),
    ("supersaw flex", "supersaw flex"),
    ("laser show", "laser show"),
    ("two-step", "two-step alibi"),
    ("jersey bounce", "jersey bounce"),
    ("kick-split", "kick-split myth"),
    ("uplifting rumor", "uplifting rumor"),
    ("fake cool", "fake cool"),
    ("control group", "control group"),
    ("lab notebook", "lab notebook"),
    ("lab book", "lab notebook"),
    ("amen rumor", "amen rumor"),
    ("strobe claim", "strobe claim"),
)


def parse_sections(lyrics: str) -> list[tuple[str, str]]:
    """Split a lyric block into (kind, body) sections."""
    sections: list[tuple[str, str]] = []
    cur_kind: str | None = None
    buf: list[str] = []
    for raw in lyrics.splitlines():
        matched = SECTION_RE.match(raw.strip())
        if matched:
            if cur_kind is not None:
                sections.append((cur_kind, "\n".join(buf).strip()))
            cur_kind = matched.group(1).lower()
            buf = []
        else:
            buf.append(raw)
    if cur_kind is not None:
        sections.append((cur_kind, "\n".join(buf).strip()))
    return sections


def content_lines(body: str) -> list[str]:
    """Non-empty stripped lines from a section body."""
    return [line.strip() for line in body.splitlines() if line.strip()]


def verse_blocks(ex: DissExample) -> list[str]:
    return [body for kind, body in parse_sections(str(ex["lyrics"])) if kind == "verse"]


def chorus_block(ex: DissExample) -> str:
    for kind, body in parse_sections(str(ex["lyrics"])):
        if kind == "chorus":
            return body
    return ""


def non_chorus_lines(ex: DissExample) -> list[str]:
    lines: list[str] = []
    for kind, body in parse_sections(str(ex["lyrics"])):
        if kind == "chorus":
            continue
        lines.extend(content_lines(body))
    return lines


def line_set(body: str) -> set[str]:
    return {line.lower() for line in content_lines(body)}


def end_word(line: str) -> str:
    tokens = PUNCT_RE.sub(" ", line.lower()).split()
    return tokens[-1] if tokens else ""


def test_content_lines_are_track_exclusive() -> None:
    owners: dict[str, set[str]] = defaultdict(set)
    for ex in DISS_EXAMPLES:
        title = str(ex["title"])
        seen: set[str] = set()
        for kind, body in parse_sections(str(ex["lyrics"])):
            del kind
            for line in content_lines(body):
                key = line.lower()
                if key in ALLOWLIST or key in seen:
                    continue
                seen.add(key)
                owners[key].add(title)
    leaks = {line: sorted(titles) for line, titles in owners.items() if len(titles) > 1}
    assert leaks == {}, f"shared bars across takes: {leaks}"


def test_verse_bodies_are_unique() -> None:
    owners: dict[str, list[str]] = defaultdict(list)
    for ex in DISS_EXAMPLES:
        title = str(ex["title"])
        seen: set[str] = set()
        for body in verse_blocks(ex):
            key = body.strip().lower()
            if key in seen:
                continue
            seen.add(key)
            owners[key].append(title)
    clones = {body.splitlines()[0]: titles for body, titles in owners.items() if len(titles) > 1}
    assert clones == {}, f"cloned verses: {clones}"


def test_cross_track_verse_jaccard_is_low() -> None:
    verses = [(str(ex["title"]), verse_blocks(ex)) for ex in DISS_EXAMPLES]
    hot: list[tuple[float, str, str, int, int]] = []
    for i, (t1, vs1) in enumerate(verses):
        for t2, vs2 in verses[i + 1 :]:
            for a, left in enumerate(vs1, start=1):
                set_a = line_set(left)
                if not set_a:
                    continue
                for b, right in enumerate(vs2, start=1):
                    set_b = line_set(right)
                    if not set_b:
                        continue
                    union = set_a | set_b
                    score = len(set_a & set_b) / len(union)
                    if score > MAX_VERSE_JACCARD:
                        hot.append((score, t1, t2, a, b))
    hot.sort(reverse=True)
    assert hot == [], f"verse overlap above {MAX_VERSE_JACCARD}: {hot[:12]}"


def test_non_chorus_lines_repeat_at_most_twice() -> None:
    offenders: list[tuple[str, str, int]] = []
    for ex in DISS_EXAMPLES:
        counts: dict[str, int] = defaultdict(int)
        for line in non_chorus_lines(ex):
            counts[line.lower()] += 1
        for line, n in counts.items():
            if line in ALLOWLIST:
                continue
            if n > MAX_NON_CHORUS_REPEATS:
                offenders.append((str(ex["title"]), line, n))
    assert offenders == [], f"non-chorus bar reused too often: {offenders}"


def test_reserved_motifs_stay_on_one_title() -> None:
    leaks: list[tuple[str, str, list[str]]] = []
    for phrase, owner in RESERVED_MOTIFS:
        needle = phrase.lower()
        hits = [
            str(ex["title"])
            for ex in DISS_EXAMPLES
            if needle in str(ex["lyrics"]).lower()
        ]
        extra = sorted({title for title in hits if title != owner})
        if extra:
            leaks.append((phrase, owner, extra))
    assert leaks == [], f"reserved disses leaked: {leaks}"


def test_verse_end_words_are_not_catalog_wide() -> None:
    titles_by_word: dict[str, set[str]] = defaultdict(set)
    for ex in DISS_EXAMPLES:
        title = str(ex["title"])
        for body in verse_blocks(ex):
            for line in content_lines(body):
                word = end_word(line)
                if word and word not in END_STOPWORDS:
                    titles_by_word[word].add(title)
    wide = {
        word: sorted(titles)
        for word, titles in titles_by_word.items()
        if len(titles) > MAX_END_WORD_TITLES
    }
    assert wide == {}, f"verse end-words in more than {MAX_END_WORD_TITLES} takes: {wide}"


def test_name_stamps_at_most_once_per_verse() -> None:
    offenders: list[tuple[str, int, str, int]] = []
    for ex in DISS_EXAMPLES:
        title = str(ex["title"])
        for idx, body in enumerate(verse_blocks(ex), start=1):
            nill = 0
            rake = 0
            for line in content_lines(body):
                low = line.lower()
                if low.startswith("nill bye"):
                    nill += 1
                if low.startswith("rake"):
                    rake += 1
            if nill > 1:
                offenders.append((title, idx, "Nill Bye", nill))
            if rake > 1:
                offenders.append((title, idx, "Rake", rake))
    assert offenders == [], f"name stamps over cap: {offenders}"


def test_choruses_stay_unique() -> None:
    owners: dict[str, list[str]] = defaultdict(list)
    for ex in DISS_EXAMPLES:
        owners[chorus_block(ex).strip().lower()].append(str(ex["title"]))
    dups = {body.splitlines()[0]: titles for body, titles in owners.items() if len(titles) > 1}
    assert dups == {}
    assert len(owners) == len(DISS_EXAMPLES)

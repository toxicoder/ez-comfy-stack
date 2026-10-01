"""Drive-through arrangement: an epic arc of ACE passes, 180-480 s.

A take is a story told in movements. Each movement is one ACE-Step
render (an ACE pass) of 48, 56, or 64 bars: it opens on a build-up,
lands its drops, and closes on a pre-impact build-up so the seam into
the next pass lands on a downbeat. The graph renders the passes in
order and ``ez_music.join.EZAudioBeatJoin`` butts them into one master,
so a take ships as a single recording with several build-up and drop
cycles, each one harder than the last.

Each stanza is 2 bars, under 3 seconds at 174-176. Duration is that sum
at the take's BPM, less the whole-bar seams the joiner overlaps. Bars
are not stretched or squeezed to hit a clock time.

Tempos snap onto Audio Rack ids that already exist (174 and 176). The
authored BPM stays the rank; the encoder and the tags use the snapped
value.

Every pass is fitted to ``DRIVE_PASS_CHAR_BUDGET`` separately, so each
pass's score covers its own latent - no unguided tail loops the last
texture. That per-pass fit is the whole reason a take is several passes:
ACE-Step truncates one lyric field at 2048 tokens, which is roughly 100
seconds of guided score, so a single 300-480 s latent would render the
unguided remainder as static.
"""

from __future__ import annotations

import functools
import hashlib
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, Literal, TypedDict

from ez_music.song_plan import (
    SongPlan,
    SongSection,
    _parse_edm,
    bar_aligned_seconds,
    duration_seconds,
    keyscale_for,
    validate_keyscale,
)

# Floor, cap, and the fast tempos the Audio Rack already knows. A take is
# 3-8 minutes; an ACE pass stays in the 48-64 bar zone it renders well.
DRIVE_FLOOR_S = 180
DRIVE_CAP_S = 480
DRIVE_BPM_CHOICES: tuple[int, ...] = (174, 176)
# ACE-Step 1.5 truncates lyrics at 2048 tokens. Measured at 3.27-3.57
# chars/token on this vocabulary (real Qwen3 tokenizer over the shipped
# scores), so 6000 chars is at worst ~1836 tokens with margin. The budget
# is per pass: 6000 chars at the pessimistic 60 chars/second of coverage
# guides ~100 s, which is why a pass caps at 64 bars (~88 s at 174-176).
DRIVE_PASS_CHAR_BUDGET = 6000
DRIVE_LYRICS_CHAR_BUDGET = DRIVE_PASS_CHAR_BUDGET
DRIVE_CHARS_PER_SEC_MAX = 60
_BPM_LO = 140
_BPM_HI = 176
_BAR_PALETTE = frozenset({2})
# Body stanza count dealt per pass before the fit. Cells are 2 bars, so
# the menu covers 44-64 bars: 64 bars is under 89 s at 174-176, inside
# the ~100 s a 6000-char score can guide.
# Cells per pass. A cell is 2 bars, so a pass is 48, 56, or 64 bars:
# under 89 s at these tempos, inside the ~100 s a 6000-char score can
# guide. Passes grow in 4-cell (8-bar) steps so each
# one closes on an 8-bar phrase boundary.
PASS_CELL_MIN = 24
PASS_CELL_MAX = 32
# Lowest a pass may fall to after the char-budget thin takes cells off.
PASS_CELL_THIN_FLOOR = 16
PASS_CELL_CHOICES: tuple[int, ...] = (24, 28, 32)
_PASS_CELL_MENU = PASS_CELL_CHOICES
_MENU = _PASS_CELL_MENU
_BODY_ROLES = ("inst", "drop", "build-up")
# Drops must hit hard and often: every take deals at least _DROP_FLOOR
# drops and every pass lands at least one; _drop_target scales the
# requirement with body size, capped at _DROP_CAP per pass.
_DROP_FLOOR = 8
_DROP_CAP = 14
_DROP_SHARE = 0.30
# The randomizable structure set. Each archetype is the ordered list of
# movement roles; the tier ladder says how hard each movement has to hit
# and the last movement of every archetype is the climax. Pass sizes come
# from the length band at the take's tempo, so one structure can be a
# 3-minute or a 6-minute take without breaking the pass cap.
MovementRole = Literal["burn", "cycle", "break", "climax", "tag"]
# Ordered movement roles per archetype; the last movement is always the
# climax, and the tier ladder escalates builds and drops movement by
# movement. Pass sizes come from the length band at the take's tempo.
_ARCHETYPES: dict[str, tuple[MovementRole, ...]] = {
    "slow-burn-arc": ("burn", "cycle", "climax"),
    "twin-peak": ("cycle", "break", "climax"),
    "cold-open": ("cycle", "cycle", "climax"),
    "drop-ladder": ("cycle", "cycle", "cycle", "climax"),
    "breakbeat-interlude": ("burn", "break", "cycle", "climax"),
    "long-arc": ("burn", "cycle", "cycle", "climax"),
    "night-run": ("cycle", "break", "cycle", "climax"),
    "finale-climax": ("burn", "cycle", "break", "cycle", "climax"),
}
# Which length bands each pass count can actually reach. A 3-movement take
# lands about 131-265 s at 174-176, a 4-movement take about 175-353 s, a
# 5-movement take about 218-441 s, so the band picks the pass count and
# the structure.
_BANDS: tuple[tuple[str, int, int], ...] = (
    ("short", 180, 215),
    ("mid", 215, 280),
    ("long", 280, 385),
    ("epic", 385, 481),
)
# Albums that lean long. The headliner set is the feature presentation.
LONG_LEANING_ALBUMS = frozenset({"headliner", "afterparty", "secret-homage"})
# Weight of each band in the per-take roll: 45% short, 30% mid, 17% long,
# 8% epic. Most of the album stays near 3 minutes so the fleet renders.
_BAND_WEIGHTS: tuple[tuple[str, int], ...] = (
    ("short", 45),
    ("mid", 30),
    ("long", 17),
    ("epic", 8),
)
# Cells at or above which the climax pass earns a cadenza cell.
CADENZA_MIN_CELLS = 28
# Bed rotation: a bed may not come back inside this many cells, and no
# one bed may voice more than this share of a take. A constant bed under
# every stanza is what made earlier takes sound like one note.
_BED_WINDOW = 4
_BED_SHARE_MAX = 0.2
_BED_LIMIT_MIN = 5
# Passes with at least this many body cells backfill to this many
# downbeat-only stanzas.
_SPARSE_MIN_BODY = 12
_SPARSE_FLOOR = 3
# One in three takes with a valley movement plays a breakdown there.
_BREAKDOWN_GATE = 3

_BRASS = (
    "brass",
    "horn",
    "trumpet",
    "trombone",
    "saxophone",
    "fanfare",
    "stab",
)
# Rotating electric beds: no single bed owns the whole take.
_BEDS = (
    "chest-sub",
    "FM warp sub",
    "wavy phase sub",
    "neuro wobble sub",
    "bitcrushed 808",
    "phase-distorted sub",
    "octave sub pulse",
)
_SUBS = (
    "mono chest-sub",
    "octave sub stack",
    "stacked 808",
    "low chest-sub",
    "body bass",
    "FM 808",
)
# Counter-lines that answer the drop's main bass figure, one per voice.
_MIDS = (
    "low-mid bass melody",
    "chest-sub melody",
    "low wobble answer",
    "body bass answer",
    "low reese counterline",
    "wavy low-mid line",
)
# Electric, wavy, warpy melodic voice in the mid-low register.
_LEADS = (
    "warped FM lead",
    "phase-wavy synth line",
    "wobble FM voice",
    "granular bass figure",
    "distorted sub figure",
    "square-wave pulse figure",
    "neuro wobble lead",
    "acid squelch line",
)
# Drum fills dealt into body stanzas; the groove stays trap throughout.
_DRUMS = (
    "rapid hi-hats",
    "offbeat hats",
    "trap drums denser",
    "ghost snare",
    "kick pattern flip",
)
# Hit weight words; every drop cue carries one before its warp word.
_WEIGHTS = ("heavy", "wreck", "harder", "stacked", "full send")
# Timbre words for the drop hit, paired with a weight in every cue.
_WARPS = ("warped", "wobble", "reese")
# Imaging phrases so the low end moves around the head instead of sitting centre.
_SPATIAL = (
    "3D low-mid orbit",
    "bass circles the low-mid",
    "sub center, low-mid moves wide",
    "low-mid orbits the sub",
    "bass pans wide behind",
    "low-mid from every angle",
    "sub anchored, mids orbit",
    "layers surround the ear",
    "wide 3D bass field",
    "panning low-mid sweep",
)
# Downbeat-only phrases for the sparse stanzas.
_SPARSE = (
    "downbeat kick",
    "kick only on downbeats",
    "downbeat sub pulse",
    "sparse four-on-floor kick",
)
# Performative tempo pushes. The global BPM never moves.
_TEMPO_PUSH = ("tempo push", "accelerating hats", "rising energy")
# Stack descriptions used by build-ups and layered drops.
_LAYERS = (
    "wide stereo layer",
    "octave 808 stack",
    "panning bass layer",
    "layered sub stack",
    "parallel low-mid layer",
)
# Build-up phrasing by tier. ACE renders literal SFX words (riser, snare
# roll) as static, so a build is described as energy, pressure, and gate
# motion instead. Tiers escalate: pressure, then rhythm density, then
# gating, then the melodic climb that opens the drop.
_BUILD_T1 = (
    "sub energy lifts",
    "low-end pressure builds",
    "kick tightens",
    "ghost snare",
    "offbeat push",
    "low-mid stack tightens",
    "mono kick punch",
)
_BUILD_T2 = (
    "bass pressure builds",
    "accelerating hats",
    "triplet hats",
    "tom run",
    "sub swell",
    "gated bass",
    "side snare",
)
_BUILD_T3 = (
    "stutter gate",
    "beat stutter",
    "kick run",
    "low-mid orbit widens",
    "octave 808 stack",
    "rolling hats",
)
_BUILD_T4 = (
    "bass melody climbs",
    "low-mid climbs",
    "energy surge",
    "kick doubles",
    "parallel low-mid layer",
    "wide stereo layer",
)
_BUILD_BY_TIER = (_BUILD_T1, _BUILD_T2, _BUILD_T3, _BUILD_T4)
# The same pools minus the tempo-push words. A stanza on a seam side
# (the pass-opening build, a last body cell, the pass-closing build)
# plays under the crossfade, where a written accelerando or "rising
# energy" makes the hand-off read as a tempo change. Seam-side stanzas
# draw from these pools instead.
_BUILD_SEAM_BY_TIER = tuple(
    tuple(phrase for phrase in pool if phrase not in _TEMPO_PUSH)
    for pool in _BUILD_BY_TIER
)
# Last stanza of a pass. It hands off to the next pass on the downbeat,
# so it names an arrival rather than a fade.
_PRE_SEAM = (
    "pre-impact hold",
    "downbeat impact",
    "sub pickup",
    "kick stomp",
    "bass returns",
)
# Drop escalation by tier. Every phrase keeps a canonical
# ``<weight> <warp> drop`` tail so a drop always names a weight, a warp,
# and a stack; the prefix adds the tier's electric charge and the layer
# count. Tier 1 is the plain hit, tier 4 is the mountain.
_DROP_MOD_T1 = ("",)
_DROP_MOD_T2 = ("electric", "laser-lit")
_DROP_MOD_T3 = (
    "laser electric",
    "multi-stack",
    "phase-charged",
    "wide laser",
)
_DROP_MOD_T4 = (
    "max stack laser",
    "full send laser",
    "octave-stacked electric",
    "laser electric tower",
)
_DROP_BY_TIER = (_DROP_MOD_T1, _DROP_MOD_T2, _DROP_MOD_T3, _DROP_MOD_T4)
# The answering line that makes a drop layered rather than single-file.
_COUNTER = (
    "counter-lead answers",
    "counter melody",
    "counter-line",
    "response line",
    "second low-mid line",
    "low wobble answer",
)
# Drop-role only: the two-bar button before the outro of a climax pass.
_CADENZA = ("downbeat impact", "sub pickup", "drop returns")
# Fast heavy bass rhythm that replaces the plain drum slot at tier 3+.
_BASSRUSH = (
    "fast bass triplets",
    "rolling 808 run",
    "double-time bass gallop",
    "staccato sub bursts",
    "driving sub pulse run",
)
_MOTIONS = (
    "hat density up",
    "kick opens",
    "kick tightens",
    "snare answers",
    "offbeat push",
    "straight hats",
    "triplet hats",
    "backbeat shove",
    "ghost notes",
    "dry hats",
    "wide hat bed",
    "mono kick",
    "side snare",
    "rolling hats",
    "late snare",
    "early kick",
    "syncopated hats",
    "open hat",
    "closed hat",
    "room snare",
    "tight kick",
    "loose hats",
    "pushed snare",
    "chopped hats",
)
RECIPE_LINES = {
    "rec_drive_through_drop": "warped hybrid-trap",
    "rec_drive_riddim": "wobble bass",
    "rec_drive_tearout": "tearout",
    "rec_drive_brostep": "brostep",
    "rec_drive_wave": "wave bass",
    "rec_drive_color": "color bass",
    "rec_drive_dirty": "dirty bass",
    "rec_drive_dirty_dubstep": "dirty dubstep",
    "rec_drive_drumstep": "amen break",
    "rec_drive_neuro": "reese bass",
    "rec_drive_chest": "chest-sub",
    "rec_drive_festival_trap": "festival trap",
    "rec_drive_dj_shout": "warped hybrid-trap",
}


def _drop_target(body: int) -> int:
    """Drop-count target for one pass of this body size.

    About 30% drop density keeps builds short and hits frequent; the cap
    keeps a full pass from demanding more drops than its unique
    drop-combo space can voice.

    Args:
        body: Body stanza count for one pass, excluding its opening
            build-up, its closing build-up, and any cadenza.

    Returns:
        Required drop count: at least the floor, at most the cap.
    """
    return max(_DROP_FLOOR, min(_DROP_CAP, round(body * _DROP_SHARE)))


def lift_drive_bpm(authored: int) -> int:
    """Map an authored tempo onto a fast Audio Rack BPM, keeping rank.

    Args:
        authored: Tempo written on the take. Values outside 140-176 clamp
            to that span before the map.

    Returns:
        One of ``DRIVE_BPM_CHOICES``. 140 lands on 165. 176 stays 176.
    """
    value = min(_BPM_HI, max(_BPM_LO, int(authored)))
    span = _BPM_HI - _BPM_LO
    pos = (value - _BPM_LO) * (len(DRIVE_BPM_CHOICES) - 1)
    index = (pos + span // 2) // span
    return DRIVE_BPM_CHOICES[index]


def fit_drive_sections(
    sections: list[SongSection],
    *,
    bpm: int,
    salt: int,
    used: set[str] | None = None,
) -> list[SongSection]:
    """Add or drop whole stanzas until the take sits in 180-480 s.

    The opening build, the first drop, and the outro stay. Their bar
    counts stay. New stanzas are inserted in front of the outro. Extra
    tail stanzas are removed from in front of the outro. The rendered
    score then re-syncs the plan's duration to the stanzas that ship,
    so the take's duration equals the score's coverage - no unguided
    tail.

    Args:
        sections: Stanzas, build then drop ... outro.
        bpm: Performance tempo.
        salt: Cue salt for any stanza this function adds.
        used: Cues and drop-combo keys already spent on this take.
            Inserted stanzas avoid them. Defaults to the music text of
            the given sections.

    Returns:
        A new list. Surviving stanzas are the same dicts.

    Raises:
        ValueError: the list cannot reach the window without resizing.
    """
    out = list(sections)
    if used is None:
        used = {_music(section["pattern"]) for section in out}
    guard = 0
    while _seconds(out, bpm) > DRIVE_CAP_S and len(out) > 3 and guard < 80:
        _drop_tail(out)
        guard += 1
    guard = 0
    while _seconds(out, bpm) < DRIVE_FLOOR_S and guard < 80:
        _insert(out, salt=salt + guard * 19, used=used)
        guard += 1
    seconds = _seconds(out, bpm)
    if seconds < DRIVE_FLOOR_S or seconds > DRIVE_CAP_S:
        raise ValueError(f"drive duration {seconds}s is outside 180-480")
    return out


def plan_drive_album(
    album_slug: str,
    rows: Sequence[Mapping[str, Any]],
) -> list[DrivePlan]:
    """Plan one Drive-through album. Shapes are unique inside the album.

    Args:
        album_slug: Folder slug. Shifts the movement menu and the key.
        rows: Catalog rows with ``bpm``, ``seed``, ``lyrics``, ``recipe``.
            ``bpm`` is already the performance tempo.

    Returns:
        One plan per row.

    Raises:
        ValueError: a take cannot be given its own ``(role, bars)`` shape.
    """
    plans: list[DrivePlan] = []
    seen: set[tuple[tuple[str, int], ...]] = set()
    for index, row in enumerate(rows, 1):
        placed = False
        for extra in range(8):
            plan = _plan_one(
                album_slug=album_slug,
                track_number=index,
                bpm=int(row["bpm"]),
                seed=int(row["seed"]),
                lyrics=str(row["lyrics"]),
                recipe=str(row.get("recipe") or ""),
                extra=extra,
            )
            signature = _signature(plan["sections"])
            if signature not in seen:
                seen.add(signature)
                plans.append(plan)
                placed = True
                break
        if not placed:
            raise ValueError(f"drive form collision on {album_slug} track {index}")
    return plans


def arrange_drive_passes(
    source: str,
    plan: DrivePlan,
    *,
    treat: bool = False,
) -> list[str]:
    """Render a plan as one ACE score per pass, each inside its own window.

    Every pass gets the markers for its own stanzas and nothing more, so
    each latent is guided for its full length. A treat keeps one short
    chorus chop, attached to the opening pass right after its first drop.

    Args:
        source: Authored score. Only the chorus chop is read.
        plan: Planned passes. ``movements_sections`` and ``pass_scores``
            are read and ``pass_scores`` is filled in.
        treat: When True, insert the DJ chop into the first pass.

    Returns:
        One score per pass, in render order, each within
        ``DRIVE_PASS_CHAR_BUDGET``.

    Raises:
        ValueError: a pass cannot be fitted to its window.
    """
    passes = [list(span) for span in plan.get("movements_sections") or []]
    if not passes:
        passes = [list(plan["sections"])]
    bpm = int(plan["bpm"])
    scores: list[str] = []
    for index, span in enumerate(passes):
        kept = fit_sections_to_pass_lyrics(span)
        blocks = [
            f"[{section['role']} - {section['pattern']}]"
            for section in kept
        ]
        if treat and index == 0:
            _cues, chorus = _parse_edm(source)
            text = " ".join(chorus.split())
            if text:
                blocks.insert(2, f"[chorus]\n{text}")
                if len("\n\n".join(blocks)) > DRIVE_PASS_CHAR_BUDGET:
                    raise ValueError("drive chop will not fit the first pass")
        scores.append("\n\n".join(blocks))
    plan["pass_scores"] = scores
    plan["pass_seconds"] = [_aligned_seconds(span, bpm) for span in passes]
    plan["sections"] = [section for span in passes for section in span]
    seams = [int(bars) for bars in plan.get("overlap_bars") or ()]
    plan["duration_s"] = int(
        round(sum(plan["pass_seconds"]) - _seam_seconds(seams, bpm))
    )
    plan["bucket"] = _bucket(int(plan["duration_s"]))
    return scores


def arrange_drive(
    source: str,
    plan: DrivePlan,
    *,
    treat: bool = False,
) -> str:
    """Render a plan as ACE markers, one block per stanza.

    The take is several ACE passes; this returns them joined, which is
    the human-readable score and what the catalog stores on ``lyrics``.
    The graph renders each pass from ``plan["pass_scores"]`` so no single
    latent is asked to carry more score than its own window holds. The
    plan's duration and bucket re-sync to the stanzas that ship, so the
    take's duration equals the score's coverage - no unguided tail.

    Args:
        source: Authored score. Only the chorus chop is read.
        plan: Planned stanzas and passes. Patterns already include the
            bar count. Mutated: ``pass_scores``, ``sections``,
            ``duration_s``, and ``bucket`` follow what ships.
        treat: When True, insert the DJ chop after the first drop.

    Returns:
        The joined ACE score. Instrumental lines are one bracket each.

    Raises:
        ValueError: a pass cannot be fitted to its window.
    """
    return "\n\n".join(arrange_drive_passes(source, plan, treat=treat))


def fit_sections_to_pass_lyrics(
    sections: Sequence[SongSection],
) -> list[SongSection]:
    """Keep the stanzas of one pass whose rendered score fits its window.

    ``fit_sections_to_lyrics`` measures a whole take against the single
    2048-token lyric window. A pass is smaller than that window by
    design, so this measures one pass against the same budget without
    treating the outro as a trimming target beyond the pass's own tail.

    Args:
        sections: One pass's stanzas.

    Returns:
        The surviving stanzas, in order.

    Raises:
        ValueError: the budget cannot be met without losing structure.
    """
    blocks = [
        f"[{section['role']} - {section['pattern']}]" for section in sections
    ]
    return [sections[index] for index in _pass_survivor_indices(blocks)]


def _pass_survivor_indices(blocks: Sequence[str]) -> list[int]:
    """Indices of the stanzas of one pass that survive the window fit.

    The opening build-up, the first drop, the pass drop floor, and the
    closing stanza stay; anything else can go from the back.

    Args:
        blocks: Bracketed stanzas for one pass.

    Returns:
        Surviving block indices, in order.

    Raises:
        ValueError: the budget cannot be met without losing structure.
    """

    def size(indices: Sequence[int]) -> int:
        """Joined character count of the blocks at these indices.

        Args:
            indices: Block indices to measure.

        Returns:
            Character count of the blocks joined with blank lines.
        """
        return len("\n\n".join(blocks[index] for index in indices))

    all_indices = list(range(len(blocks)))
    if size(all_indices) <= DRIVE_PASS_CHAR_BUDGET:
        return all_indices
    kept = list(all_indices)
    while size(kept) > DRIVE_PASS_CHAR_BUDGET:
        drops = sum(1 for index in kept if blocks[index].startswith("[drop"))
        for position in range(len(kept) - 2, 1, -1):
            if blocks[kept[position]].startswith("[drop") and drops <= _DROP_FLOOR:
                continue
            kept.pop(position)
            break
        else:
            raise ValueError("drive pass cannot fit the lyric window")
    return kept


def _fit_lyrics_window(blocks: list[str]) -> str:
    """Join stanzas, dropping the tail before the outro when over budget.

    ACE-Step 1.5 truncates lyrics at 2048 tokens; a longer score
    conditions on a cut-off prefix and renders as static. Keeps the
    opening build-up, the first drop, at least five drops, and the
    outro.

    Args:
        blocks: Bracketed stanzas, build-up then drop ... outro.

    Returns:
        The joined score within ``DRIVE_LYRICS_CHAR_BUDGET``.

    Raises:
        ValueError: the budget cannot be met without losing structure.
    """
    kept = _window_survivor_indices(blocks)
    return "\n\n".join(blocks[index] for index in kept)


def _window_survivor_indices(blocks: Sequence[str]) -> list[int]:
    """Indices of the stanzas that survive the lyric-window fit.

    Trims from in front of the outro. The opening build-up, the first
    drop, at least five drops, and the outro stay.

    Args:
        blocks: Bracketed stanzas, build-up then drop ... outro.

    Returns:
        Surviving block indices, in order.

    Raises:
        ValueError: the budget cannot be met without losing structure.
    """

    def size(indices: Sequence[int]) -> int:
        """Joined character count of the blocks at these indices.

        Args:
            indices: Block indices to measure.

        Returns:
            Character count of the blocks joined with blank lines.
        """
        return len("\n\n".join(blocks[index] for index in indices))

    all_indices = list(range(len(blocks)))
    if size(all_indices) <= DRIVE_LYRICS_CHAR_BUDGET:
        return all_indices
    kept = list(all_indices)
    while size(kept) > DRIVE_LYRICS_CHAR_BUDGET:
        drops = sum(1 for index in kept if blocks[index].startswith("[drop"))
        for position in range(len(kept) - 2, 1, -1):
            if blocks[kept[position]].startswith("[drop") and drops <= _DROP_FLOOR:
                continue
            kept.pop(position)
            break
        else:
            raise ValueError("drive score cannot fit the lyric window")
    return kept


def fit_sections_to_lyrics(
    sections: Sequence[SongSection],
) -> list[SongSection]:
    """Keep the stanzas whose rendered score fits the lyric window.

    Mirrors ``_fit_lyrics_window`` on the stanza data so a caller can
    re-voice the survivors before the final render.

    Args:
        sections: Fitted stanzas, build-up then drop ... outro.

    Returns:
        The surviving stanzas, in order.

    Raises:
        ValueError: the budget cannot be met without losing structure.
    """
    blocks = [
        f"[{section['role']} - {section['pattern']}]" for section in sections
    ]
    return [sections[index] for index in _window_survivor_indices(blocks)]


def _signature(sections: list[SongSection]) -> tuple[tuple[str, int], ...]:
    """``(role, bars)`` shape of a take.

    Args:
        sections: Planned stanzas.

    Returns:
        The shape tuple.
    """
    return tuple((section["role"], int(section["bars"])) for section in sections)


def _seconds(sections: list[SongSection], bpm: int) -> int:
    """Unclamped seconds for the summed bar count.

    Args:
        sections: Stanzas.
        bpm: Performance tempo.

    Returns:
        Rounded seconds. Not clamped to the rap window.
    """
    total = sum(int(section["bars"]) for section in sections)
    return duration_seconds(bars=total, meter="4", bpm=int(bpm), clamp=False)


def _aligned_seconds(sections: list[SongSection], bpm: int) -> float:
    """Latent-frame-aligned seconds for the summed bar count.

    Args:
        sections: Stanzas.
        bpm: Performance tempo.

    Returns:
        Seconds on the ACE latent-frame grid. Not clamped.
    """
    total = sum(int(section["bars"]) for section in sections)
    return bar_aligned_seconds(bars=total, meter="4", bpm=int(bpm))


def _salt(*parts: object) -> int:
    """Stable integer salt from the given parts.

    Args:
        parts: Mixed into the digest in order.

    Returns:
        A positive integer.
    """
    blob = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(blob.encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _music(pattern: str) -> str:
    """Cue text without the trailing bar count.

    Args:
        pattern: Section pattern.

    Returns:
        The musical cue.
    """
    marker = ", "
    suffix = " bars"
    if pattern.endswith(suffix) and marker in pattern:
        head, _tail = pattern.rsplit(marker, 1)
        if _tail.endswith(suffix) and _tail[: -len(suffix)].isdigit():
            return head
    return pattern


def _menu_count(album_slug: str, track_number: int) -> int:
    """Body stanza count a pass is dealt, before the per-pass fit.

    Args:
        album_slug: Album folder slug.
        track_number: One-based index.

    Returns:
        A menu size inside ``_PASS_CELL_MENU``; the per-pass fit then
        keeps the pass inside its 6000-char score window.
    """
    offset = sum(ord(char) for char in album_slug) % len(_PASS_CELL_MENU)
    return _PASS_CELL_MENU[(int(track_number) - 1 + offset) % len(_PASS_CELL_MENU)]


def _band_of(seconds: int) -> str:
    """Length band a take falls in.

    Args:
        seconds: Planned take duration.

    Returns:
        A name from ``_BANDS``: ``short``, ``mid``, ``long``, ``epic``.
    """
    name = "short"
    for band, low, high in _BANDS:
        if int(seconds) >= low and int(seconds) < high:
            name = band
    return name


def _roll_band(album_slug: str, track_number: int, seed: int) -> str:
    """Length band this take rolls, with the long-leaning albums pushed up.

    Args:
        album_slug: Album folder slug.
        track_number: One-based index.
        seed: Take seed.

    Returns:
        A band name from ``_BANDS``.
    """
    salt = _salt(album_slug, track_number, seed, "band")
    total = sum(weight for _, weight in _BAND_WEIGHTS)
    lean = 20 if album_slug in LONG_LEANING_ALBUMS else 0
    roll = salt % (total + lean)
    cursor = 0
    for name, weight in _BAND_WEIGHTS:
        cursor += weight
        if roll < cursor:
            return name
    return "epic"


def _band_window(name: str) -> tuple[int, int]:
    """Seconds window for one length band.

    Args:
        name: Band name.

    Returns:
        ``(low, high)`` clamped to the take floor and cap, high exclusive.
    """
    for band, low, high in _BANDS:
        if band == name:
            return max(DRIVE_FLOOR_S, low), min(DRIVE_CAP_S + 1, high)
    return DRIVE_FLOOR_S, DRIVE_CAP_S + 1


def _pass_bounds(bpm: int) -> tuple[int, int]:
    """Shortest and longest a pass of this tempo can run, in seconds.

    Args:
        bpm: Performance tempo.

    Returns:
        ``(floor_seconds, cap_seconds)`` for one pass.
    """
    return (
        duration_seconds(
            bars=PASS_CELL_THIN_FLOOR * 2, meter="4", bpm=int(bpm), clamp=False
        ),
        duration_seconds(bars=PASS_CELL_MAX * 2, meter="4", bpm=int(bpm), clamp=False),
    )


def _take_span(count: int, bpm: int) -> tuple[int, int]:
    """Shortest and longest a take of this many passes can run.

    Args:
        count: Pass count.
        bpm: Performance tempo.

    Returns:
        ``(min_seconds, max_seconds)`` with every pass at its floor or cap.
    """
    low, high = _pass_bounds(int(bpm))
    return count * low, count * high


def _band_reachable(
    roles: Sequence[MovementRole],
    low: int,
    high: int,
    bpm: int,
) -> bool:
    """True when an archetype's pass count can reach this seconds band.

    Args:
        roles: Movement roles in render order.
        low: Band floor in seconds.
        high: Band ceiling in seconds, exclusive.
        bpm: Performance tempo.

    Returns:
        Whether some pass sizing of this many passes lands in the band.
    """
    floor_s, cap_s = _take_span(len(roles), int(bpm))
    return floor_s < high and cap_s >= low


def _archetype_for(
    album_slug: str,
    track_number: int,
    seed: int,
    extra: int,
    bpm: int,
) -> tuple[str, tuple[MovementRole, ...]]:
    """Pick the structure archetype for one take.

    The band comes from the take identity alone. The roll runs over the
    archetypes that can reach that band at this tempo, and the collision
    retry rotates it, so a retry can move a take to a different structure
    and every take keeps its own shape.

    Args:
        album_slug: Album folder slug.
        track_number: One-based index.
        seed: Take seed.
        extra: Collision retry.
        bpm: Performance tempo.

    Returns:
        ``(archetype_id, movement_roles)`` in render order.
    """
    low, high = _band_window(_roll_band(album_slug, track_number, seed))
    eligible = [
        (name, roles)
        for name, roles in _ARCHETYPES.items()
        if _band_reachable(roles, low, high, int(bpm))
    ]
    if not eligible:
        eligible = list(_ARCHETYPES.items())
    roll = _salt(album_slug, track_number, seed, extra, "arch") % len(eligible)
    return eligible[roll]


def _archetype_seconds(roles: Sequence[MovementRole], bpm: int) -> int:
    """Seconds an archetype runs at with every pass at its floor size.

    Args:
        roles: Movement roles in render order.
        bpm: Performance tempo.

    Returns:
        Rounded seconds for the summed bars, seams aside.
    """
    bars = len(roles) * PASS_CELL_MIN * 2
    return duration_seconds(bars=bars, meter="4", bpm=int(bpm), clamp=False)


def _allocate_cells(
    roles: Sequence[MovementRole],
    target_seconds: int,
    bpm: int,
    salt: int,
) -> list[int]:
    """Give every pass a cell count, inside the pass caps.

    Passes grow in whole-phrase steps of 4 cells (8 bars), longest-need
    first, so a pass stays 48, 56, or 64 bars and always closes on an
    8-bar phrase boundary.

    Args:
        roles: Movement roles in render order.
        target_seconds: Seconds this take is aiming for.
        bpm: Performance tempo.
        salt: Take salt. Picks which pass grows first.

    Returns:
        Cells per pass, each inside ``PASS_CELL_MIN``..``PASS_CELL_MAX``.
    """
    cells = [PASS_CELL_MIN for _role in roles]
    if not cells:
        return cells
    need_bars = int(target_seconds) * int(bpm) / 240
    order = sorted(range(len(cells)), key=lambda index: _mix_int(salt, index, 11))
    guard = 0
    while (
        sum(cells) * 2 < need_bars
        and any(cell < PASS_CELL_MAX for cell in cells)
        and guard < 400
    ):
        for index in order:
            if cells[index] < PASS_CELL_MAX:
                cells[index] = min(PASS_CELL_MAX, cells[index] + 4)
                break
        guard += 1
    return cells


def _movement_tiers(roles: Sequence[MovementRole]) -> list[int]:
    """Escalation tier for each movement, 1-4, never going backwards.

    The last movement is always tier 4, a breakdown sits in the valley at
    tier 2, and a long fuse opens at tier 1, so intensity only climbs
    across the take.

    Args:
        roles: Movement roles in render order.

    Returns:
        One tier per movement, non-decreasing.
    """
    count = len(roles)
    tiers: list[int] = []
    for index, role in enumerate(roles):
        if role == "climax":
            tier = 4
        elif role == "break":
            tier = 2
        elif role == "burn":
            tier = 1
        elif role == "tag":
            tier = 3
        else:
            tier = 2 + (index % 2)
        if index == count - 1:
            tier = 4
        if tiers:
            tier = max(tier, tiers[-1])
        tiers.append(max(1, min(4, tier)))
    return tiers


def _pass_seam_bars(roles: Sequence[MovementRole]) -> list[int]:
    """Seam overlap in whole bars, one entry per join.

    A seam into a movement that lands drops gets three bars so the
    incoming downbeat has room to arrive; a seam into a valley gets
    two. The wider window also gives the crossfade run to cover: two
    bars over two independent renders was long enough to hear as a hole
    in the track, thin at the edges and jarring into the next drop.

    Args:
        roles: Movement roles in render order.

    Returns:
        Bars to overlap at each seam.
    """
    seams: list[int] = []
    for index in range(1, len(roles)):
        seams.append(2 if roles[index] == "break" else 3)
    return seams
@functools.cache
def _needles() -> tuple[str, ...]:
    """Brass, high-pitch, and score bans. Imported lazily to avoid a cycle.

    Returns:
        Substrings a cue must not contain.
    """
    from ez_music.edm_examples import FORBIDDEN_SCORE_NEEDLES, HIGH_PITCH_NEEDLES

    return (*FORBIDDEN_SCORE_NEEDLES, *HIGH_PITCH_NEEDLES, *_BRASS)


def _blocked(text: str) -> bool:
    """True when text names brass, a high lead, or a banned cue.

    Args:
        text: Cue fragment.

    Returns:
        Whether the fragment is illegal in a Drive-through score.
    """
    low = text.lower()
    for needle in _needles():
        if needle == "mute":
            if "mute" in low.replace("muted", ""):
                return True
            continue
        if needle in low:
            return True
    return False


def _slot(pool: tuple[str, ...], n: int, salt: int, attempt: int, step: int) -> str:
    """Pick one pool entry. ``attempt`` always moves the choice.

    Args:
        pool: Phrase pool.
        n: Section index.
        salt: Take salt.
        attempt: Retry counter.
        step: Stride for the section index.

    Returns:
        One phrase.
    """
    mixed = n * step + attempt + (salt % (len(pool) * step + 1))
    return pool[mixed % len(pool)]


def _bed(n: int, salt: int, attempt: int) -> str:
    """Front of every cue: a rotating electric bed and a 3D move.

    Args:
        n: Section index.
        salt: Take salt.
        attempt: Retry counter.

    Returns:
        The shared prefix: bed phrase plus a spatial phrase.
    """
    bed = _slot(_BEDS, n, salt, attempt, 9)
    spatial = _slot(_SPATIAL, n, salt, attempt, 13)
    return f"{bed}, {spatial}"


def _cue_for(
    role: str,
    n: int,
    salt: int,
    attempt: int = 0,
    *,
    depth: float = 0.5,
    sparse: bool = False,
    tier: int = 0,
    pre_seam: bool = False,
    on_seam: bool = False,
    cadenza: bool = False,
) -> str:
    """One layered cue. Drops name a weight and a warp. Beds do not say drop.

    Slots stack up as the take deepens: the sub slot opens at 0.25, the
    mid slot and an optional lead at 0.5, and the layer slot at 0.7.
    Drops always render at full depth. A sparse stanza is just the
    rotating bed plus one downbeat phrase.

    ``tier`` (1-4, 0 meaning "unranked") escalates the drop and build
    phrasing and adds the answering counter line from tier 2, the fast
    bass rush from tier 3, and the forced double-time feel at tier 4.
    ``pre_seam`` closes a pass on the downbeat; ``cadenza`` is the
    drop-role button before an outro.

    Args:
        role: Section role.
        n: Cue index.
        salt: Take salt.
        attempt: Retry counter. Changes every layer so retries cannot repeat.
        depth: 0-to-1 position across the take. Gates the stacking slots.
        sparse: When True, return the downbeat-only two-part cue.
        tier: Escalation tier, clamped to 0-4.
        pre_seam: When True, this cue closes a pass into the next one.
        on_seam: When True, the stanza plays under a seam crossfade:
            no tempo-push words and build phrasing from the seam pools.
        cadenza: When True, this drop-role cue buttons before the outro.

    Returns:
        Comma-separated production cue.
    """
    rank = max(0, min(4, int(tier)))
    if sparse:
        return f"{_bed(n, salt, attempt)}, {_slot(_SPARSE, n, salt, attempt, 5)}"
    if role == "drop":
        depth = 1.0
    bed = _bed(n, salt, attempt)
    sub = _slot(_SUBS, n, salt, attempt, 3) if depth >= 0.25 else ""
    mid = _slot(_MIDS, n, salt, attempt, 5) if depth >= 0.5 else ""
    lead = (
        _slot(_LEADS, n, salt, attempt, 7)
        if depth >= 0.5 and role != "outro" and _mix_int(salt, n, 5) % 5 < 3
        else ""
    )
    layer = (
        _slot(_LAYERS, n, salt, attempt, 11)
        if depth >= 0.7 and role != "drop"
        else ""
    )
    motion = _slot(_MOTIONS, n, salt, attempt, 1)
    if role == "drop":
        weight = _slot(_WEIGHTS, n, salt, attempt, 2)
        warp = _slot(_WARPS, n, salt, attempt, 4)
        if cadenza:
            button = _slot(_CADENZA, n, salt, attempt, 3)
            head = f"{weight} {warp} drop"
            parts = [
                f"{bed}, {_slot(_LAYERS, n, salt, attempt, 11)}, {head}, {button}"
            ]
        else:
            modifier = (
                _slot(_DROP_BY_TIER[rank - 1], n, salt, attempt, 6)
                if rank >= 1
                else ""
            )
            head = f"{weight} {warp} drop"
            if modifier:
                head = f"{modifier} {head}"
            parts = [
                f"{bed}, {_slot(_LAYERS, n, salt, attempt, 11)}, {head}"
            ]
        if rank >= 2:
            parts.append(_slot(_COUNTER, n, salt, attempt, 5))
        if rank >= 3 or _mix_int(salt, n, 6) % 5 < 2:
            parts.append("double-time feel")
    elif role == "build-up":
        push = "" if on_seam else _slot(_TEMPO_PUSH, n, salt, attempt, 2)
        if pre_seam:
            parts = [
                f"{bed}, kick tightens, {_slot(_PRE_SEAM, n, salt, attempt, 3)}"
            ]
        else:
            pool = _BUILD_SEAM_BY_TIER if on_seam else _BUILD_BY_TIER
            build = (
                _slot(pool[rank - 1], n, salt, attempt, 2)
                if rank >= 1
                else "kick tightens"
            )
            parts = [f"{bed}, kick tightens, {build}"]
        if push and push not in parts[0]:
            parts.append(push)
    elif role == "breakdown":
        parts = [f"{bed}, rapid hi-hats, tempo dip"]
    elif role == "outro":
        parts = [f"{bed}, kick pattern flip, rapid hi-hats"]
    else:
        parts = [bed]
    if layer:
        parts.append(layer)
    if sub:
        parts.append(sub)
    if mid:
        parts.append(mid)
    if lead:
        parts.append(lead)
    if role in ("drop", "inst"):
        if rank >= 3:
            parts.append(_slot(_BASSRUSH, n, salt, attempt, 7))
        else:
            parts.append(_slot(_DRUMS, n, salt, attempt, 7))
    parts.append(motion)
    return ", ".join(parts)


def _drop_combo(n: int, salt: int, attempt: int, tier: int = 0) -> str:
    """Weight/warp/spatial combo for one drop cue attempt.

    Ranked drops keep the canonical ``<weight> <warp> drop`` tail, so the
    combo is the same triple at every tier; the tier modifier rides on top
    of it and the used-set keeps two drops from voicing the same stack.

    Args:
        n: Cue index.
        salt: Take salt.
        attempt: Retry counter.
        tier: Escalation tier. Kept for a stable call shape.

    Returns:
        Pipe-joined combo, stable for the same cue.
    """
    del tier
    weight = _slot(_WEIGHTS, n, salt, attempt, 2)
    warp = _slot(_WARPS, n, salt, attempt, 4)
    spatial = _slot(_SPATIAL, n, salt, attempt, 13)
    return f"{weight}|{warp}|{spatial}"


def _unique_cue(
    role: str,
    n: int,
    salt: int,
    used: set[str],
    *,
    depth: float = 0.5,
    sparse: bool = False,
    tier: int = 0,
    pre_seam: bool = False,
    on_seam: bool = False,
    cadenza: bool = False,
    recent_beds: Sequence[str] = (),
    bed_counts: Mapping[str, int] | None = None,
    bed_limit: int = 0,
) -> str:
    """A cue this take has not used yet.

    Drop cues must also carry a weight/warp/spatial combo the take has
    not voiced, so two drops never sound like the same stack. When
    ``recent_beds`` is given, the bed (cue's first phrase) may not repeat
    inside that window, and a bed already used ``bed_limit`` times in the
    take is skipped too, so no single bed owns a long take.

    Args:
        role: Section role.
        n: Preferred index.
        salt: Take salt.
        used: Musical cues already emitted. Updated on success.
        depth: Stacking depth threaded to ``_cue_for``.
        sparse: Downbeat-only cue, threaded to ``_cue_for``.
        tier: Escalation tier threaded to ``_cue_for``.
        pre_seam: Pass-closing build-up, threaded to ``_cue_for``.
        cadenza: Drop-role button, threaded to ``_cue_for``.
        recent_beds: Beds used by the last few cells, oldest first.
        bed_counts: Beds used so far in the whole take.
        bed_limit: Maximum times one bed may voice a cell in the take;
            0 disables the cap.

    Returns:
        The cue.

    Raises:
        ValueError: the cue space for this role is exhausted.
    """
    for attempt in range(len(_MOTIONS)):
        cue = _cue_for(
            role,
            n,
            salt,
            attempt,
            depth=depth,
            sparse=sparse,
            tier=tier,
            pre_seam=pre_seam,
            on_seam=on_seam,
            cadenza=cadenza,
        )
        if cue in used or _blocked(cue):
            continue
        bed = cue.split(", ", 1)[0]
        if bed in recent_beds:
            continue
        if bed_limit and bed_counts is not None:
            if bed_counts.get(bed, 0) >= bed_limit:
                continue
        combo_key: str | None = None
        if role == "drop":
            combo_key = f"drop-combo::{_drop_combo(n, salt, attempt, tier)}"
            if combo_key in used:
                continue
        if role != "drop" and "drop" in cue:
            continue
        used.add(cue)
        if combo_key is not None:
            used.add(combo_key)
        return cue
    raise ValueError(f"no unique cue for {role}")


def _mix_int(salt: int, index: int, lane: int) -> int:
    """Irregular mix so section choices do not repeat on a short cycle.

    Args:
        salt: Take salt.
        index: Section index.
        lane: Independent stream (role, bars, cue).

    Returns:
        A positive integer.
    """
    value = (int(salt) + index * 0x9E3779B1 + lane * 0x85EBCA77) & 0xFFFFFFFFFFFFFFFF
    value = (value ^ (value >> 30)) * 0xBF58476D1CE4E5B9 & 0xFFFFFFFFFFFFFFFF
    value = (value ^ (value >> 27)) * 0x94D049BB133111EB & 0xFFFFFFFFFFFFFFFF
    return value ^ (value >> 31)


# Weighted role roll: a 20-step cycle where drops take the first 9 steps,
# instrumentals the next 7, and build-ups the remaining 4.
_ROLE_PERIOD = 20
_DROP_SLICE = 9
_INST_SLICE = 7


def _pick_role(salt: int, index: int, prev: str) -> str:
    """Next body role, drop-weighted, never the stanza just written.

    Drops take 9 of 20 rolls so builds stay short and hits come fast.

    Args:
        salt: Take salt.
        index: Section index. Mixed so the role order is not a 4-step loop.
        prev: Previous role.

    Returns:
        A body role, different from ``prev``.
    """
    mixed = _mix_int(salt, index, 1)
    roll = mixed % _ROLE_PERIOD
    if roll < _DROP_SLICE:
        role = "drop"
    elif roll < _DROP_SLICE + _INST_SLICE:
        role = "inst"
    else:
        role = "build-up"
    if role == prev:
        role = _BODY_ROLES[(_BODY_ROLES.index(role) + 1) % len(_BODY_ROLES)]
    return role


def _pick_bars(role: str, prev: int, salt: int, index: int, *, before_outro: bool) -> int:
    """Bar count for one stanza. Every cell is 2 bars.

    Args:
        role: Section role. Ignored. Kept so callers stay stable.
        prev: Previous stanza's bars. Ignored.
        salt: Take salt. Ignored.
        index: Section index. Ignored.
        before_outro: Ignored.

    Returns:
        2. Under 3 seconds at 165-176.
    """
    del role, prev, salt, index, before_outro
    return 2


def _make(role: str, bars: int, cue: str) -> SongSection:
    """One stanza. The pattern records the musical cue and its bar count.

    Args:
        role: ACE role.
        bars: Bar count.
        cue: Musical cue, without the bar suffix.

    Returns:
        A section dict.
    """
    return {"role": role, "bars": int(bars), "pattern": f"{cue}, {int(bars)} bars"}


def _donor_queue(source: str) -> list[str]:
    """Authored cue fragments, grid stamps removed, bans dropped.

    Args:
        source: Authored score.

    Returns:
        Fragments in order, duplicates skipped.
    """
    cues, _chorus = _parse_edm(source)
    out: list[str] = []
    seen: set[str] = set()
    for cue in cues:
        frag = " ".join(cue.split())
        if not frag or frag in seen or _blocked(frag):
            continue
        seen.add(frag)
        out.append(frag)
    return out


def _take_donor(queue: list[str], role: str) -> str:
    """Pop the next donor that may sit on this role.

    Drop-language stays on drops so a fill is not reclassified as a drop.

    Args:
        queue: Remaining donors. Mutated.
        role: Destination role.

    Returns:
        The fragment, or empty.
    """
    for index, frag in enumerate(queue):
        if role != "drop" and "drop" in frag.lower():
            continue
        queue.pop(index)
        return frag
    return ""


def _with_extras(
    role: str,
    cue: str,
    queue: list[str],
    *,
    identity: str,
    pedal: bool,
    used: set[str],
) -> str:
    """Append one donor, and on the first drop the recipe line and pedal.

    Args:
        role: Section role.
        cue: Base cue already recorded in ``used``.
        queue: Donor queue.
        identity: Recipe line. Empty skips it.
        pedal: When True, keep the dual-action pedal phrase.
        used: Musical cues. The merged cue is recorded when it changes.

    Returns:
        The cue that should ship.
    """
    extras: list[str] = []
    if identity and identity not in cue:
        extras.append(identity)
    if pedal and "dual-action pedal" not in cue:
        extras.append("dual-action pedal bass")
    donor = _take_donor(queue, role)
    if donor and donor not in cue:
        extras.append(donor)
    if not extras:
        return cue
    merged = cue + ", " + ", ".join(extras)
    if _blocked(merged) or (role != "drop" and "drop" in merged):
        return cue
    if merged in used:
        return cue
    used.add(merged)
    return merged


def _cue_with_donor(
    role: str,
    n: int,
    salt: int,
    used: set[str],
    queue: list[str],
    *,
    identity: str = "",
    pedal: bool = False,
    depth: float = 0.5,
    sparse: bool = False,
    tier: int = 0,
    pre_seam: bool = False,
    on_seam: bool = False,
    cadenza: bool = False,
    recent_beds: Sequence[str] = (),
    bed_counts: Mapping[str, int] | None = None,
    bed_limit: int = 0,
) -> str:
    """Unique base cue plus at most one donor and the optional identity.

    A sparse stanza ships the downbeat cue as-is: no donor, identity, or
    pedal extras, so it stays exactly bed plus phrase.

    Args:
        role: Section role.
        n: Cue index.
        salt: Take salt.
        used: Cues already used.
        queue: Donor queue.
        identity: Recipe line for the first drop.
        pedal: Keep the pedal phrase on the first drop.
        depth: Stacking depth threaded to ``_cue_for``.
        sparse: Downbeat-only stanza; extras are skipped.
        tier: Escalation tier threaded to ``_unique_cue``.
        pre_seam: Pass-closing build-up, threaded to ``_unique_cue``.
        on_seam: Seam-side stanza, threaded to ``_unique_cue``.
        cadenza: Drop-role button, threaded to ``_unique_cue``.
        recent_beds: Beds used by the last few cells, oldest first.
        bed_counts: Beds used so far in the take.
        bed_limit: Per-take bed reuse cap; 0 disables it.

    Returns:
        Musical cue.
    """
    cue = _unique_cue(
        role,
        n,
        salt,
        used,
        depth=depth,
        sparse=sparse,
        tier=tier,
        pre_seam=pre_seam,
        on_seam=on_seam,
        cadenza=cadenza,
        recent_beds=recent_beds,
        bed_counts=bed_counts,
        bed_limit=bed_limit,
    )
    if sparse:
        return cue
    return _with_extras(
        role,
        cue,
        queue,
        identity=identity,
        pedal=pedal,
        used=used,
    )


def _drop_tail(out: list[SongSection]) -> None:
    """Remove the stanza in front of the outro.

    One stanza only. Every cell is 2 bars, so deleting while the
    neighbor shares the outro's length would eat the take.

    Args:
        out: Stanza list ending in the outro. Mutated.
    """
    if len(out) <= 3:
        return
    del out[-2]


def _insert(out: list[SongSection], *, salt: int, used: set[str]) -> None:
    """Insert one new dense stanza in front of the outro.

    Fit padding renders near full depth so a padded stanza is a stacked
    cue, never a thin one.

    Args:
        out: Stanza list ending in the outro. Mutated.
        salt: Cue salt.
        used: Musical cues. Updated.
    """
    prev = out[-2]
    index = len(out)
    role = _pick_role(salt, index, prev["role"])
    bars = _pick_bars(role, int(prev["bars"]), salt, index, before_outro=True)
    cue = _unique_cue(role, salt, salt, used, depth=0.95)
    out.insert(-1, _make(role, bars, cue))


def _ensure_drops(
    out: list[SongSection],
    salt: int,
    used: set[str],
    *,
    floor: int = _DROP_FLOOR,
    tier: int = 0,
    run_cap: int = 2,
) -> None:
    """Promote fills to drops until this pass's floor and target hold.

    A fill is promoted only when doing so keeps the drop run at or under
    ``run_cap``, so roles keep switching. Promoted cells stay 2 bars.

    Args:
        out: One pass's stanzas. Mutated.
        salt: Take salt.
        used: Musical cues. Updated.
        floor: Drop count this pass must reach.
        tier: Escalation tier threaded to the promoted cue.
        run_cap: Longest legal run of one role in this pass.

    Raises:
        ValueError: no legal slot is left for another drop.
    """
    while True:
        body = len(out) - 2
        drops = sum(section["role"] == "drop" for section in out)
        if drops >= floor and drops >= _drop_target(body):
            return
        for index in range(2, len(out) - 1):
            if out[index]["role"] == "drop":
                continue
            left = 0
            while out[index - 1 - left]["role"] == "drop":
                left += 1
            right = 0
            while out[index + 1 + right]["role"] == "drop":
                right += 1
            if left + right >= run_cap:
                continue
            cue = _unique_cue("drop", salt + index, salt, used, tier=tier)
            out[index] = _make("drop", 2, cue)
            break
        else:
            raise ValueError("could not place a drive drop")


def _place_rare_breakdown(
    out: list[SongSection],
    salt: int,
    used: set[str],
    *,
    gate: int,
) -> None:
    """Turn one inst into a 2-bar breakdown on about one take in five.

    The cue stacks at late-take depth; the role is the dip. Two bars
    keeps that dip under 3 seconds. ``gate`` ignores the collision retry
    so a retry cannot drop the dip. Only the break movement asks, so the
    modulus is tighter than the old whole-album rate to keep the album
    dip count in its band.

    Args:
        out: Stanza list ending in the outro. Mutated.
        salt: Take salt, including the collision retry. Chooses the cue.
        used: Musical cues. Updated when a breakdown is placed.
        gate: Identity salt for this take. A breakdown is placed only
            when ``gate % 5 == 0``.
    """
    if gate % 5 != 0:
        return
    for index in range(2, len(out) - 1):
        if out[index]["role"] != "inst":
            continue
        cue = _unique_cue("breakdown", salt + index, salt, used, depth=0.95)
        out[index] = _make("breakdown", 2, cue)
        return


def _ensure_sparse(
    out: list[SongSection],
    salt: int,
    queue: list[str],
    used: set[str],
) -> None:
    """Guarantee at least three downbeat-only stanzas in a long body.

    The probabilistic sparse pick in ``_compose`` lands below the check
    floor on unlucky rolls; backfill the gap by converting the earliest
    eligible fill (never a drop, never adjacent to an existing sparse
    stanza, never one of the last two stanzas -- they sit under the seam
    crossfade into the next pass) so every long take keeps the
    dense/sparse back-and-forth.

    Args:
        out: Fitted stanzas ending in the outro. Mutated.
        salt: Take salt, including the collision retry.
        queue: Donor queue. Unused by sparse cues; kept for a stable
            call shape with ``_cue_with_donor``.
        used: Musical cues. Updated when a sparse cue lands.

    Raises:
        ValueError: no legal slot is left for a sparse stanza.
    """
    if len(out) - 2 < _SPARSE_MIN_BODY:
        return
    while sum(1 for section in out if _is_sparse(section)) < _SPARSE_FLOOR:
        for index in range(2, len(out) - 2):
            section = out[index]
            if section["role"] == "drop" or _is_sparse(section):
                continue
            if _is_sparse(out[index - 1]) or _is_sparse(out[index + 1]):
                continue
            out[index] = _make(
                section["role"],
                section["bars"],
                _cue_with_donor(
                    section["role"], index, salt, used, queue, sparse=True
                ),
            )
            break
        else:
            raise ValueError("no legal slot for a sparse stanza")


def _structure_for(
    album_slug: str,
    track_number: int,
    seed: int,
    extra: int,
    bpm: int,
) -> tuple[str, tuple[MovementRole, ...], list[int], list[int], list[int]]:
    """Resolve one take's structure: archetype, roles, cells, tiers, seams.

    The band decides how many passes the take needs, the roll picks a
    structure with that pass count, and the cells fill the band at this
    tempo.

    Args:
        album_slug: Album folder slug.
        track_number: One-based index.
        seed: Take seed.
        extra: Collision retry.
        bpm: Performance tempo.

    Returns:
        ``(archetype, roles, cells, tiers, seam_bars)``.
    """
    band = _roll_band(album_slug, track_number, seed)
    low, high = _band_window(band)
    archetype, roles = _archetype_for(
        album_slug, track_number, seed, extra, int(bpm)
    )
    target = _salt(album_slug, track_number, seed, extra, "target")
    span = max(1, high - low - 1)
    target_seconds = low + target % span
    cells = _allocate_cells(roles, target_seconds, int(bpm), target)
    tiers = _movement_tiers(roles)
    seams = _pass_seam_bars(roles)
    return archetype, roles, cells, tiers, seams


def _pass_depth(tier: int, cell: int, cells: int) -> float:
    """Stacking depth for one cell, from its tier and place in the pass.

    The tier carries most of the intensity so a later pass always sits
    above an earlier one; the position inside the pass adds the local
    ramp into its drop.

    Args:
        tier: Movement tier, 1-4.
        cell: Zero-based cell index inside the pass.
        cells: Cell count of the pass.

    Returns:
        Depth in 0-1.
    """
    rank = max(1, min(4, int(tier)))
    share = cell / max(1, int(cells))
    return min(1.0, 0.55 * (rank - 1) / 3 + 0.45 * share)


def _compose_pass(
    *,
    role: MovementRole,
    cells: int,
    tier: int,
    salt: int,
    used: set[str],
    queue: list[str],
    identity: str,
    pedal: bool,
    first_pass: bool,
    last_pass: bool,
    recent_beds: list[str],
    bed_counts: dict[str, int],
    bed_limit: int,
) -> list[SongSection]:
    """Deal one ACE pass: an opening build, its body, and its hand-off.

    A pass opens on a build-up and lands its first drop in the second
    cell, so each render re-anchors the pulse from its first bar. A pass
    that is not the last closes on a build-up carrying a pre-impact
    phrase, which is what the joiner butts against the next pass. The
    last pass buttons with a two-bar cadenza drop before the outro when
    it is long enough to earn one.

    Args:
        role: Movement role for this pass.
        cells: Cell count for this pass.
        tier: Movement escalation tier, 1-4.
        salt: Take salt.
        used: Cues and drop-combo keys already spent. Updated.
        queue: Donor queue. Mutated.
        identity: Recipe line for the first drop of the take.
        pedal: Keep the pedal phrase on the first drop of the take.
        first_pass: Whether this is the opening pass.
        last_pass: Whether this is the closing pass.
        recent_beds: Beds used by the last few cells of the take. Mutated.
        bed_counts: Bed use counts for the take. Mutated.
        bed_limit: Maximum cells one bed may voice across the take.

    Returns:
        The pass's stanzas, 2 bars each.
    """
    body = max(2, int(cells) - 2)
    break_pass = role == "break"
    sections: list[SongSection] = []
    prev_role = ""
    prev_sparse = False
    drop_deals = 0
    head_identity = identity if first_pass else ""
    head_pedal = pedal if first_pass else False
    for index in range(body):
        if index == 0:
            role_name = "build-up"
        elif index == 1:
            # The pass's opening drop is structural - every pass lands its
            # first drop in its second cell - so the dealt cap never
            # flips it away.
            role_name = "drop"
        else:
            role_name = _pick_role(salt, index, prev_role)
        if role_name == "drop":
            dealt_past_cap = index != 1 and (
                drop_deals >= _DROP_CAP
                or (break_pass and drop_deals >= max(1, _DROP_FLOOR // 2))
            )
            if dealt_past_cap:
                role_name = "inst" if prev_role != "inst" else "build-up"
            else:
                drop_deals += 1
        depth = _pass_depth(tier, index, body)
        if break_pass and role_name == "drop" and drop_deals > 1:
            depth = min(depth, 0.6)
        # The pass-opening build and the last body cell sit under the
        # seam crossfade (with the pass-closing build), so neither may
        # go sparse: a downbeat-only stanza under the hand-off is the
        # quiet patch that read as a hole in the track.
        sparse = (
            2 <= index < body - 1
            and role_name != "drop"
            and not prev_sparse
            and _mix_int(salt, index, 7) % 10 < 3
        )
        on_seam = (index == 0 and not first_pass) or (
            not last_pass and index == body - 1
        )
        cue = _cue_with_donor(
            role_name,
            index,
            salt,
            used,
            queue,
            identity=head_identity if index == 1 else "",
            pedal=head_pedal if index == 1 else False,
            depth=depth,
            sparse=sparse,
            tier=tier,
            on_seam=on_seam,
            recent_beds=recent_beds,
            bed_counts=bed_counts,
            bed_limit=bed_limit,
        )
        _note_bed(cue, recent_beds, bed_counts)
        sections.append(_make(role_name, 2, cue))
        prev_role = role_name
        prev_sparse = sparse
    if not last_pass:
        cue = _cue_with_donor(
            "build-up",
            body,
            salt,
            used,
            queue,
            depth=min(1.0, _pass_depth(tier, body, body)),
            tier=tier,
            pre_seam=True,
            on_seam=True,
            recent_beds=recent_beds,
            bed_counts=bed_counts,
            bed_limit=bed_limit,
        )
        _note_bed(cue, recent_beds, bed_counts)
        sections.append(_make("build-up", 2, cue))
        return sections
    if body >= CADENZA_MIN_CELLS:
        cue = _cue_with_donor(
            "drop",
            body,
            salt,
            used,
            queue,
            tier=4,
            cadenza=True,
            recent_beds=recent_beds,
            bed_counts=bed_counts,
            bed_limit=bed_limit,
        )
        _note_bed(cue, recent_beds, bed_counts)
        sections.append(_make("drop", 2, cue))
    cue = _unique_cue(
        "outro",
        body + 1,
        salt,
        used,
        recent_beds=recent_beds,
        bed_counts=bed_counts,
        bed_limit=bed_limit,
    )
    _note_bed(cue, recent_beds, bed_counts)
    sections.append(_make("outro", 2, cue))
    return sections


def _bed_of(cue: str) -> str:
    """The bed phrase a cue leads with.

    Args:
        cue: A musical cue.

    Returns:
        Its first comma part.
    """
    return cue.split(", ", 1)[0]


def _repair_beds(
    passes: Sequence[list[SongSection]],
    *,
    tiers: Sequence[int],
    salt: int,
    used: set[str],
    queue: list[str],
) -> None:
    """Re-voice cells whose bed breaks the rotation window or the cap.

    Every backfill (drop promotion, sparse backfill, thinning) can hand a
    cell a fresh cue without the take's bed history, and thinning moves
    cells that were far apart next to each other. This single pass over
    the finished take guarantees the rotation invariant however it was
    broken: a cell whose bed came back inside the window, or whose bed is
    over the per-take cap, is re-cued at the same role, tier, and shape.

    Args:
        passes: The finished passes. Mutated in place.
        tiers: Escalation tier of each pass.
        salt: Take salt.
        used: Cues and drop-combo keys already spent. Updated.
        queue: Donor queue.

    Raises:
        ValueError: no legal bed is left for a violating cell.
    """
    flat: list[tuple[int, int]] = []
    for pass_index, span in enumerate(passes):
        for cell_index in range(len(span)):
            flat.append((pass_index, cell_index))
    if not flat:
        return
    limit = max(_BED_LIMIT_MIN, math.ceil(len(flat) * _BED_SHARE_MAX))
    last_pass = len(passes) - 1
    for position, (pass_index, cell_index) in enumerate(flat):
        span = passes[pass_index]
        section = span[cell_index]
        beds = [
            _bed_of(_music(passes[p][c]["pattern"])) for p, c in flat
        ]
        bed = beds[position]
        recent = beds[max(0, position - _BED_WINDOW + 1) : position]
        if bed not in recent and Counter(beds)[bed] <= limit:
            continue
        # Seam-zone cells (first two of a non-first pass, last two of a
        # non-last pass) re-voice seam-neutral, matching _compose_pass.
        in_head = pass_index > 0 and cell_index < 2
        in_tail = pass_index < last_pass and cell_index >= len(span) - 2
        on_seam = in_head or in_tail
        sparse = _is_sparse(section)
        cue = _cue_with_donor(
            section["role"],
            cell_index + pass_index * 7,
            salt + pass_index * 101,
            used,
            queue,
            depth=_pass_depth(tiers[pass_index], cell_index, max(1, len(span))),
            sparse=sparse,
            tier=tiers[pass_index],
            on_seam=on_seam,
            recent_beds=recent,
            bed_counts=dict(Counter(beds)),
            bed_limit=limit,
        )
        span[cell_index] = _make(section["role"], section["bars"], cue)


def _note_bed(
    cue: str,
    recent_beds: list[str],
    bed_counts: dict[str, int],
) -> None:
    """Record the bed a cue used, for the rotation window and the cap.

    Args:
        cue: The cue just emitted.
        recent_beds: Sliding window of recent beds. Mutated.
        bed_counts: Per-take bed tallies. Mutated.
    """
    bed = cue.split(", ", 1)[0]
    recent_beds.append(bed)
    del recent_beds[:-_BED_WINDOW]
    bed_counts[bed] = bed_counts.get(bed, 0) + 1


def _compose_passes(
    *,
    album_slug: str,
    track_number: int,
    bpm: int,
    seed: int,
    lyrics: str,
    recipe: str,
    extra: int,
) -> tuple[str, tuple[MovementRole, ...], list[int], list[int], list[list[SongSection]]]:
    """Deal the whole take as an ordered list of ACE passes.

    Args:
        album_slug: Album folder slug.
        track_number: One-based index.
        bpm: Performance tempo.
        seed: Take seed.
        lyrics: Authored score (donors and the pedal phrase).
        recipe: Audio Rack recipe id.
        extra: Collision retry.

    Returns:
        ``(archetype, roles, cells, seam_bars, passes)`` with the passes
        in render order.
    """
    salt = _salt(album_slug, track_number, seed, extra)
    archetype, roles, cells, tiers, seams = _structure_for(
        album_slug, track_number, seed, extra, int(bpm)
    )
    used: set[str] = set()
    queue = _donor_queue(lyrics)
    pedal = "dual-action pedal" in lyrics.lower()
    identity = RECIPE_LINES.get(recipe, "")
    recent_beds: list[str] = []
    bed_counts: dict[str, int] = {}
    breakdowns_placed = False
    bed_limit = max(
        _BED_LIMIT_MIN,
        -(-sum(cells) * int(_BED_SHARE_MAX * 100) // 100),
    )
    passes: list[list[SongSection]] = []
    for index, role in enumerate(roles):
        pass_salt = salt + index * 101
        sections = _compose_pass(
            role=role,
            cells=cells[index],
            tier=tiers[index],
            salt=pass_salt,
            used=used,
            queue=queue,
            identity=identity,
            pedal=pedal,
            first_pass=index == 0,
            last_pass=index == len(roles) - 1,
            recent_beds=recent_beds,
            bed_counts=bed_counts,
            bed_limit=bed_limit,
        )
        _ensure_drops(
            sections,
            pass_salt,
            used,
            floor=_pass_drop_floor(role),
            tier=tiers[index],
            run_cap=3 if role == "climax" else 2,
        )
        if role == "break" and not breakdowns_placed:
            _place_rare_breakdown(
                sections,
                pass_salt,
                used,
                gate=_salt(album_slug, track_number, seed),
            )
            breakdowns_placed = any(
                section["role"] == "breakdown" for section in sections
            )
        _ensure_sparse(sections, pass_salt, queue, used)
        passes.append(sections)
    tiers = _movement_tiers(roles)
    # Bed repair can lengthen a cue and thinning can bring two cells that
    # used the same bed together, so the two passes run until both hold.
    for _round in range(3):
        _repair_beds(
            passes, tiers=tiers, salt=salt, used=used, queue=queue,
        )
        if not any(
            len(_pass_score(sections)) > DRIVE_PASS_CHAR_BUDGET
            for sections in passes
        ):
            break
        for sections in passes:
            _thin_pass(sections, bpm=int(bpm))
    return archetype, roles, cells, seams, passes


def _compose(
    *,
    album_slug: str,
    track_number: int,
    bpm: int,
    seed: int,
    lyrics: str,
    recipe: str,
    extra: int,
) -> list[SongSection]:
    """Deal the take as passes and return the flat stanza list.

    Args:
        album_slug: Album folder slug.
        track_number: One-based index.
        bpm: Performance tempo.
        seed: Take seed.
        lyrics: Authored score (donors and the pedal phrase).
        recipe: Audio Rack recipe id.
        extra: Collision retry. Changes the salt, not a clock target.

    Returns:
        Fitted stanzas, the passes concatenated in render order.
    """
    _archetype, _roles, _cells, _seams, passes = _compose_passes(
        album_slug=album_slug,
        track_number=track_number,
        bpm=bpm,
        seed=seed,
        lyrics=lyrics,
        recipe=recipe,
        extra=extra,
    )
    fitted: list[SongSection] = []
    for sections in passes:
        fitted.extend(sections)
    return fitted


def _pass_drop_floor(role: MovementRole) -> int:
    """Drop floor one pass must land, given its movement role.

    The valley pass keeps its drops sparse so the take still dips; every
    other pass hits the full floor.

    Args:
        role: Movement role.

    Returns:
        Minimum drop count for that pass.
    """
    if role == "break":
        return max(1, _DROP_FLOOR // 3)
    return _DROP_FLOOR


def _pass_score(sections: Sequence[SongSection]) -> str:
    """Joined ACE score for one pass.

    Args:
        sections: The pass's stanzas.

    Returns:
        Bracketed blocks joined with blank lines.
    """
    return "\n\n".join(
        f"[{section['role']} - {section['pattern']}]" for section in sections
    )


def _thin_pass(sections: list[SongSection], *, bpm: int) -> None:
    """Trim whole stanzas until the pass score fits its char budget.

    A pass whose score runs past ``DRIVE_PASS_CHAR_BUDGET`` is cut off
    mid-cue by ACE-Step and renders the rest of its latent as static, so
    trimming happens at plan time. Cells are 2 bars and a pass must span
    whole 8-bar phrases for the seams to land musically, so stanzas come
    off in pairs from the back. The opening build-up, the first drop, the
    drop floor, and the closing stanza are protected.

    Args:
        sections: The pass's stanzas. Mutated in place.
        bpm: Performance tempo, for the pass floor check.

    Raises:
        ValueError: the budget cannot be met without losing structure.
    """
    del bpm
    if len(_pass_score(sections)) <= DRIVE_PASS_CHAR_BUDGET:
        return
    guard = 0
    while len(_pass_score(sections)) > DRIVE_PASS_CHAR_BUDGET and guard < 100:
        guard += 1
        pair = _thinnable_pair(sections)
        if pair is None:
            raise ValueError("drive pass cannot fit the lyric window")
        del sections[pair[0] : pair[1]]
    if len(_pass_score(sections)) > DRIVE_PASS_CHAR_BUDGET:
        raise ValueError("drive pass cannot fit the lyric window")


def _thinnable_pair(sections: list[SongSection]) -> tuple[int, int] | None:
    """Which adjacent pair of stanzas to drop next on an over-budget pass.

    Args:
        sections: The pass's stanzas.

    Returns:
        ``(start, end)`` slice bounds, or None when nothing may go.
    """
    drops = sum(section["role"] == "drop" for section in sections)
    floor = PASS_CELL_THIN_FLOOR
    last = len(sections) - 1
    for start in range(last - 2, 1, -1):
        end = start + 2
        pair = sections[start:end]
        if any(section["role"] == "breakdown" for section in pair):
            continue
        pair_drops = sum(section["role"] == "drop" for section in pair)
        if pair_drops and drops - pair_drops < _DROP_FLOOR:
            continue
        if len(sections) - 2 < floor:
            continue
        return (start, end)
    return None


def _is_sparse(section: SongSection) -> bool:
    """Whether a stanza's cue is a downbeat-only sparse one.

    Args:
        section: Planned stanza.

    Returns:
        True when the cue's last comma part is a ``_SPARSE`` phrase.
    """
    parts = _music(section["pattern"]).split(", ")
    return len(parts) >= 2 and parts[-1] in _SPARSE


def _check(
    sections: list[SongSection],
    *,
    pass_lengths: Sequence[int] | None = None,
    tiers: Sequence[int] | None = None,
    roles: Sequence[MovementRole] | None = None,
    bpm: int | None = None,
) -> None:
    """Reject a take that breaks an arrangement invariant.

    Checks the shape, the drop floors, the role runs, the sparse
    back-and-forth, the bed rotation, and the cue bans. Pass-aware rules
    (per-pass drop floor, per-pass char budget, tier escalation) run only
    when the caller passes the structure, so a hand-built stanza list is
    still checkable on its own.

    Args:
        sections: Fitted stanzas, the passes concatenated.
        pass_lengths: Cell count of each pass, in render order.
        tiers: Escalation tier of each pass, in render order.
        roles: Movement role of each pass, in render order.
        bpm: Performance tempo, needed for the per-pass duration check.

    Raises:
        ValueError: an arrangement invariant failed.
    """
    if sections[0]["role"] != "build-up" or int(sections[0]["bars"]) != 2:
        raise ValueError("opening build is missing or long")
    if sections[1]["role"] != "drop":
        raise ValueError("first drop is not the second stanza")
    if sections[-1]["role"] != "outro" or int(sections[-1]["bars"]) != 2:
        raise ValueError("outro must be the last stanza and 2 bars")
    bars = [int(section["bars"]) for section in sections]
    if any(count not in _BAR_PALETTE for count in bars):
        raise ValueError("bar count left the 2-bar palette")
    drops = sum(section["role"] == "drop" for section in sections)
    if drops < _DROP_FLOOR:
        raise ValueError(f"need at least {_DROP_FLOOR} drops")
    body = len(sections) - 2
    if body > 0 and drops < _drop_target(body):
        raise ValueError("drop target below minimum")
    run_cap = 3 if roles and roles[-1] == "climax" else 2
    run = 0
    prev_run_role: str | None = None
    for section in sections:
        if section["role"] == prev_run_role:
            run += 1
        else:
            run = 1
            prev_run_role = section["role"]
        if run > run_cap:
            raise ValueError("role run longer than the cap")
    if sum(section["role"] == "breakdown" for section in sections) > 1:
        raise ValueError("more than one breakdown")
    sparse_flags = [_is_sparse(section) for section in sections]
    for flag, prev in zip(sparse_flags[1:], sparse_flags):
        if flag and prev:
            raise ValueError("two adjacent stanzas are both sparse")
    if body >= _SPARSE_MIN_BODY and sum(sparse_flags) < _SPARSE_FLOOR:
        raise ValueError("take needs at least three sparse stanzas")
    musics = [_music(section["pattern"]) for section in sections]
    if len(musics) != len(set(musics)):
        raise ValueError("a cue repeats inside the take")
    for section, music in zip(sections, musics):
        if _blocked(music):
            raise ValueError(f"banned cue in {section['role']}")
        if section["role"] != "drop" and "drop" in music:
            raise ValueError("drop language landed on a fill")
    beds = [music.split(", ", 1)[0] for music in musics]
    _check_beds(beds)
    if pass_lengths is not None:
        _check_passes(
            sections,
            pass_lengths,
            tiers=tiers or (),
            roles=roles or (),
            bpm=int(bpm) if bpm is not None else None,
        )


def _check_beds(beds: Sequence[str]) -> None:
    """Reject a bed that repeats too close to itself or hogs the take.

    Args:
        beds: Bed phrase of every stanza, in order.

    Raises:
        ValueError: the rotation window or the per-bed share is broken.
    """
    pool = [bed for bed in beds if bed in _BEDS]
    if not pool:
        return
    window = _BED_WINDOW
    for index, bed in enumerate(pool):
        if bed in pool[max(0, index - window + 1) : index]:
            raise ValueError(f"bed {bed} returns inside the rotation window")
    limit = max(_BED_LIMIT_MIN, math.ceil(len(pool) * _BED_SHARE_MAX))
    for bed, count in Counter(pool).items():
        if count > limit:
            raise ValueError(f"bed {bed} voices {count} of {len(pool)} cells")


def _check_passes(
    sections: Sequence[SongSection],
    pass_lengths: Sequence[int],
    *,
    tiers: Sequence[int],
    roles: Sequence[MovementRole],
    bpm: int | None,
) -> None:
    """Check the per-pass rules of a multi-pass take.

    Args:
        sections: All stanzas, the passes concatenated.
        pass_lengths: Cell count of each pass, in render order.
        tiers: Escalation tier of each pass. Checked for monotonicity.
        roles: Movement role of each pass, for its drop floor.
        bpm: Performance tempo for the per-pass duration check.

    Raises:
        ValueError: a pass breaks its own invariant.
    """
    cursor = 0
    spans: list[list[SongSection]] = []
    for cells in pass_lengths:
        if cells <= 0 or cursor + cells > len(sections):
            raise ValueError("pass lengths do not cover the take")
        spans.append(list(sections[cursor : cursor + cells]))
        cursor += cells
    if cursor != len(sections):
        raise ValueError("pass lengths leave stanzas unassigned")
    for index, span in enumerate(spans):
        if len(_pass_score(span)) > DRIVE_PASS_CHAR_BUDGET:
            raise ValueError(f"pass {index} exceeds the lyric window")
        if len(span) < 4:
            raise ValueError(f"pass {index} is too short to build and drop")
        if span[0]["role"] != "build-up":
            raise ValueError(f"pass {index} does not open on a build-up")
        if span[1]["role"] != "drop":
            raise ValueError(f"pass {index} does not land its first drop")
        if index + 1 < len(spans) and span[-1]["role"] != "build-up":
            raise ValueError(f"pass {index} does not hand off on a build-up")
        floor = _pass_drop_floor(
            roles[index] if index < len(roles) else "cycle"
        )
        if sum(section["role"] == "drop" for section in span) < floor:
            raise ValueError(f"pass {index} is under its drop floor")
        if bpm is not None:
            seconds = _seconds(list(span), int(bpm))
            low, high = _pass_bounds(int(bpm))
            if not low - 2 <= seconds <= high + 2:
                raise ValueError(f"pass {index} runs {seconds}s, outside pass bounds")
    if tiers and any(right < left for left, right in zip(tiers, tiers[1:])):
        raise ValueError("intensity drops between passes")


def _form_id(album_slug: str, seed: int, sections: list[SongSection]) -> str:
    """Short id for this take's shape.

    Args:
        album_slug: Album folder slug.
        seed: Take seed.
        sections: Fitted stanzas.

    Returns:
        ``drv-`` plus 10 hex characters.
    """
    blob = f"{album_slug}|{seed}|" + ",".join(
        f"{section['role']}:{section['bars']}" for section in sections
    )
    digest = hashlib.sha256(blob.encode()).hexdigest()[:10]
    return f"drv-{digest}"


def _bucket(seconds: int) -> str:
    """Coarse length label stored on the plan. Not a clock target.

    Args:
        seconds: Fitted duration.

    Returns:
        ``short`` under 210, ``standard`` under 300, ``long`` under 400,
        else ``epic``.
    """
    if seconds < 210:
        return "short"
    if seconds < 300:
        return "standard"
    if seconds < 400:
        return "long"
    return "epic"


class DrivePlan(TypedDict):
    """Arrangement for one Drive-through take, told in ACE passes.

    Attributes:
        form_id: Shape id for this take.
        sections: Every stanza, the passes concatenated in render order.
        meter: Encoder time signature.
        keyscale: Encoder key, identical across the passes.
        duration_s: Whole-second length of the joined master.
        bpm: Performance tempo, identical across the passes.
        bucket: Coarse length label.
        archetype: Structure-set id the take rolled.
        movements: Movement role of each pass, in render order.
        movements_sections: Stanzas grouped per pass, render order.
        pass_cells: Cell count dealt to each pass.
        pass_seconds: Latent-frame-aligned seconds of each pass before
            its seam.
        overlap_bars: Seam overlap in whole bars, one entry per join.
        pass_scores: Joined ACE score per pass, index-aligned.
    """

    form_id: str
    sections: list[SongSection]
    meter: str
    keyscale: str
    duration_s: int
    bpm: int
    bucket: str
    archetype: str
    movements: list[MovementRole]
    movements_sections: list[list[SongSection]]
    pass_cells: list[int]
    pass_seconds: list[float]
    overlap_bars: list[int]
    pass_scores: list[str]


def _seam_seconds(overlap_bars: Sequence[int], bpm: int) -> int:
    """Seconds the joiner overlaps away, across all seams.

    Args:
        overlap_bars: Bars overlapped at each seam.
        bpm: Performance tempo.

    Returns:
        Rounded seconds removed from the summed pass lengths.
    """
    return int(round(sum(int(bars) for bars in overlap_bars) * 240 / int(bpm)))


def _plan_one(
    *,
    album_slug: str,
    track_number: int,
    bpm: int,
    seed: int,
    lyrics: str,
    recipe: str,
    extra: int,
) -> DrivePlan:
    """Plan one take as an ordered set of ACE passes.

    Args:
        album_slug: Album folder slug.
        track_number: One-based index.
        bpm: Performance tempo.
        seed: Take seed.
        lyrics: Authored score.
        recipe: Audio Rack recipe id.
        extra: Collision retry.

    Returns:
        The song plan, including the per-pass render data.
    """
    archetype, roles, cells, seams, passes = _compose_passes(
        album_slug=album_slug,
        track_number=track_number,
        bpm=bpm,
        seed=seed,
        lyrics=lyrics,
        recipe=recipe,
        extra=extra,
    )
    sections: list[SongSection] = []
    for span in passes:
        sections.extend(span)
    _check(
        sections,
        pass_lengths=[len(span) for span in passes],
        tiers=_movement_tiers(roles),
        roles=roles,
        bpm=int(bpm),
    )
    pass_seconds = [_aligned_seconds(span, int(bpm)) for span in passes]
    seconds = int(round(sum(pass_seconds) - _seam_seconds(seams, int(bpm))))
    return {
        "form_id": _form_id(album_slug, seed, sections),
        "sections": sections,
        "meter": "4",
        "keyscale": validate_keyscale(
            keyscale_for("drive-through", album_slug, track_number)
        ),
        "duration_s": seconds,
        "bpm": int(bpm),
        "bucket": _bucket(seconds),
        "archetype": archetype,
        "movements": list(roles),
        "movements_sections": passes,
        "pass_cells": [len(span) for span in passes],
        "pass_seconds": pass_seconds,
        "overlap_bars": seams,
        "pass_scores": [],
    }

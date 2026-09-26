"""Drive-through arrangement: two-bar cells, an early drop, 90–120 s.

Each stanza is 2 bars, under 3 seconds at 165–176. Duration is that sum
at the take's BPM. A shortfall adds whole stanzas. An overrun drops
whole stanzas. Bars are not stretched or squeezed to hit a clock time.

Tempos snap onto Audio Rack ids that already exist (165–176). The
authored BPM stays the rank; the encoder and the tags use the snapped
value.

The rendered score is fitted to ``DRIVE_LYRICS_CHAR_BUDGET`` so the
whole score stays inside ACE-Step's 2048-token lyric window. The plan's
duration equals the score's coverage, so no unguided tail loops the last
texture.
"""

from __future__ import annotations

import functools
import hashlib
from collections.abc import Mapping, Sequence
from typing import Any

from ez_music.song_plan import (
    SongPlan,
    SongSection,
    _parse_edm,
    duration_seconds,
    keyscale_for,
    validate_keyscale,
)

# Floor, cap, and the fast tempos the Audio Rack already knows.
DRIVE_FLOOR_S = 90
DRIVE_CAP_S = 120
DRIVE_BPM_CHOICES: tuple[int, ...] = (165, 168, 170, 172, 174, 176)
# ACE-Step 1.5 truncates lyrics at 2048 tokens. Measured at 3.43–3.56
# chars/token on this vocabulary, so 6000 chars stays under the window
# with margin. The score covers the whole take — no unguided tail.
DRIVE_LYRICS_CHAR_BUDGET = 6000
_BPM_LO = 140
_BPM_HI = 176
_BAR_PALETTE = frozenset({2})
# Body stanza count dealt per take before the duration fit. The menu
# sizes keep every take inside the 90–120 s window after the fit.
_MENU = (31, 34, 37, 40, 43)
_BODY_ROLES = ("inst", "drop", "build-up")
# Drops must hit hard and often: every take deals at least _DROP_FLOOR
# drops; _drop_target scales the requirement with body size, capped at
# _DROP_CAP so long bodies do not demand more drops than the take holds.
_DROP_FLOOR = 5
_DROP_CAP = 30
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
_DRUMS = (
    "rapid hi-hats",
    "offbeat hats",
    "trap drums denser",
    "ghost snare",
    "kick pattern flip",
)
_WEIGHTS = ("heavy", "wreck", "harder", "stacked", "full send")
_WARPS = ("warped", "wobble", "reese")
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
_LAYERS = (
    "wide stereo layer",
    "octave 808 stack",
    "panning bass layer",
    "layered sub stack",
    "parallel low-mid layer",
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
    """Drop-count target for a body of this size.

    About 35% drop density keeps builds short and hits frequent; the
    cap keeps long bodies from demanding endless drops.

    Args:
        body: Body stanza count, excluding the opening build and outro.

    Returns:
        Required drop count: at least the floor, at most the cap.
    """
    return max(_DROP_FLOOR, min(_DROP_CAP, round(body * 0.35)))


def lift_drive_bpm(authored: int) -> int:
    """Map an authored tempo onto a fast Audio Rack BPM, keeping rank.

    Args:
        authored: Tempo written on the take. Values outside 140–176 clamp
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
    """Add or drop whole stanzas until duration sits in 90–120 s.

    The opening build, the first drop, and the outro stay. Their bar
    counts stay. New stanzas are inserted in front of the outro. Extra
    tail stanzas are removed from in front of the outro. The rendered
    score then re-syncs the plan's duration to the stanzas that ship,
    so the take's duration equals the score's coverage — no unguided
    tail.

    Args:
        sections: Stanzas, build then drop … outro.
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
        raise ValueError(f"drive duration {seconds}s is outside 90–120")
    return out


def plan_drive_album(
    album_slug: str,
    rows: Sequence[Mapping[str, Any]],
) -> list[SongPlan]:
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
    plans: list[SongPlan] = []
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


def arrange_drive(source: str, plan: SongPlan, *, treat: bool = False) -> str:
    """Render a plan as ACE markers, fitted to the lyric window.

    A treat keeps one short chorus chop. The tail is trimmed before the
    outro so the joined score stays inside ``DRIVE_LYRICS_CHAR_BUDGET``.
    The plan's duration and bucket re-sync to the stanzas that ship, so
    the take's duration equals the score's coverage — no unguided tail.

    Args:
        source: Authored score. Only the chorus chop is read.
        plan: Planned stanzas. Patterns already include the bar count.
            Mutated: ``duration_s`` and ``bucket`` follow the stanzas
            that survive the lyric-window fit.
        treat: When True, insert the DJ chop after the first drop.

    Returns:
        ACE score within the char budget. Instrumental lines are one
        bracket each.
    """
    kept_sections = fit_sections_to_lyrics(plan["sections"])
    blocks = [
        f"[{section['role']} - {section['pattern']}]"
        for section in kept_sections
    ]
    if treat:
        _cues, chorus = _parse_edm(source)
        text = " ".join(chorus.split())
        if text:
            blocks.insert(2, f"[chorus]\n{text}")
    plan["duration_s"] = _seconds(kept_sections, int(plan["bpm"]))
    plan["bucket"] = _bucket(int(plan["duration_s"]))
    kept = _window_survivor_indices(blocks)
    return "\n\n".join(blocks[index] for index in kept)


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
    """How many body stanzas this take is dealt, before the floor and cap.

    Args:
        album_slug: Album folder slug.
        track_number: One-based index.

    Returns:
        A menu size of 31–43 body stanzas; the duration fit then keeps
        the take inside the 90–120 s window.
    """
    offset = sum(ord(char) for char in album_slug) % len(_MENU)
    return _MENU[(int(track_number) - 1 + offset) % len(_MENU)]


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
) -> str:
    """One layered cue. Drops name a weight and a warp. Beds do not say drop.

    Slots stack up as the take deepens: the sub slot opens at 0.25, the
    mid slot and an optional lead at 0.5, and the layer slot at 0.7.
    Drops always render at full depth. A sparse stanza is just the
    rotating bed plus one downbeat phrase.

    Args:
        role: Section role.
        n: Cue index.
        salt: Take salt.
        attempt: Retry counter. Changes every layer so retries cannot repeat.
        depth: 0-to-1 position across the take. Gates the stacking slots.
        sparse: When True, return the downbeat-only two-part cue.

    Returns:
        Comma-separated production cue.
    """
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
        parts = [
            f"{bed}, {_slot(_LAYERS, n, salt, attempt, 11)}, "
            f"{weight} {warp} drop"
        ]
        if _mix_int(salt, n, 6) % 5 < 2:
            parts.append("double-time feel")
    elif role == "build-up":
        parts = [
            f"{bed}, kick tightens, {_slot(_TEMPO_PUSH, n, salt, attempt, 2)}"
        ]
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
        parts.append(_slot(_DRUMS, n, salt, attempt, 7))
    parts.append(motion)
    return ", ".join(parts)


def _drop_combo(n: int, salt: int, attempt: int) -> str:
    """Weight/warp/spatial combo for one drop cue attempt.

    Args:
        n: Cue index.
        salt: Take salt.
        attempt: Retry counter.

    Returns:
        Pipe-joined combo, stable for the same cue.
    """
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
) -> str:
    """A cue this take has not used yet.

    Drop cues must also carry a weight/warp/spatial combo the take has
    not voiced, so two drops never sound like the same stack.

    Args:
        role: Section role.
        n: Preferred index.
        salt: Take salt.
        used: Musical cues already emitted. Updated on success.
        depth: Stacking depth threaded to ``_cue_for``.
        sparse: Downbeat-only cue, threaded to ``_cue_for``.

    Returns:
        The cue.

    Raises:
        ValueError: the cue space for this role is exhausted.
    """
    for attempt in range(len(_MOTIONS)):
        cue = _cue_for(role, n, salt, attempt, depth=depth, sparse=sparse)
        if cue in used or _blocked(cue):
            continue
        combo_key: str | None = None
        if role == "drop":
            combo_key = f"drop-combo::{_drop_combo(n, salt, attempt)}"
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
        2. Under 3 seconds at 165–176.
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

    Returns:
        Musical cue.
    """
    cue = _unique_cue(role, n, salt, used, depth=depth, sparse=sparse)
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


def _ensure_drops(out: list[SongSection], salt: int, used: set[str]) -> None:
    """Promote fills to drops until the floor and target hold.

    A fill is promoted only when doing so keeps the drop run at most
    two stanzas, so roles keep switching. Promoted cells stay 2 bars.

    Args:
        out: Stanza list ending in the outro. Mutated.
        salt: Take salt.
        used: Musical cues. Updated.

    Raises:
        ValueError: no legal slot is left for another drop.
    """
    while True:
        body = len(out) - 2
        drops = sum(section["role"] == "drop" for section in out)
        if drops >= _DROP_FLOOR and drops >= _drop_target(body):
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
            if left + right >= 2:
                continue
            cue = _unique_cue("drop", salt + index, salt, used)
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
    """Turn one inst into a 2-bar breakdown on about one take in seven.

    The cue stacks at late-take depth; the role is the dip. Two bars
    keeps that dip under 3 seconds. ``gate`` ignores the collision retry
    so a retry cannot drop the dip.

    Args:
        out: Stanza list ending in the outro. Mutated.
        salt: Take salt, including the collision retry. Chooses the cue.
        used: Musical cues. Updated when a breakdown is placed.
        gate: Identity salt for this take. A breakdown is placed only
            when ``gate % 7 == 0``.
    """
    if gate % 7 != 0:
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
    stanza) so every long take keeps the dense/sparse back-and-forth.

    Args:
        out: Fitted stanzas ending in the outro. Mutated.
        salt: Take salt, including the collision retry.
        queue: Donor queue. Unused by sparse cues; kept for a stable
            call shape with ``_cue_with_donor``.
        used: Musical cues. Updated when a sparse cue lands.

    Raises:
        ValueError: no legal slot is left for a sparse stanza.
    """
    if len(out) - 2 < 20:
        return
    while sum(1 for section in out if _is_sparse(section)) < 3:
        for index in range(2, len(out) - 1):
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
    """Deal the movement list, fit it to the duration window, then hit the
    drop floor and the rare breakdown.

    Cues deepen with position: the opening build sits at depth zero and
    each body stanza ramps toward full depth, so stanzas gain slots as
    the take goes. About three of ten non-drop stanzas are downbeat-only
    and never two in a row, cutting the loop feel.

    Args:
        album_slug: Album folder slug.
        track_number: One-based index.
        bpm: Performance tempo.
        seed: Take seed.
        lyrics: Authored score (donors and the pedal phrase).
        recipe: Audio Rack recipe id.
        extra: Collision retry. Changes the salt, not a clock target.

    Returns:
        Fitted stanzas.
    """
    salt = _salt(album_slug, track_number, seed, extra)
    used: set[str] = set()
    queue = _donor_queue(lyrics)
    pedal = "dual-action pedal" in lyrics.lower()
    identity = RECIPE_LINES.get(recipe, "")
    sections = [
        _make(
            "build-up",
            2,
            _cue_with_donor("build-up", 0, salt, used, queue, depth=0.0),
        ),
        _make(
            "drop",
            2,
            _cue_with_donor(
                "drop",
                1,
                salt,
                used,
                queue,
                identity=identity,
                pedal=pedal,
            ),
        ),
    ]
    prev_role = "drop"
    prev_bars = 2
    prev_sparse = False
    drop_deals = 0
    menu = _menu_count(album_slug, track_number)
    for index in range(menu):
        role = _pick_role(salt, index, prev_role)
        if role == "drop" and drop_deals >= _DROP_CAP:
            # The dealt drop count is capped so long bodies stay inside
            # the unique drop-combo space; keep roles switching.
            role = "inst" if prev_role != "inst" else "build-up"
        elif role == "drop":
            drop_deals += 1
        before_outro = index == menu - 1
        bars = _pick_bars(role, prev_bars, salt, index, before_outro=before_outro)
        depth = (index + 2) / (menu + 2)
        sparse = (
            role != "drop"
            and not prev_sparse
            and _mix_int(salt, index, 7) % 10 < 3
        )
        cue = _cue_with_donor(
            role, index + 2, salt, used, queue, depth=depth, sparse=sparse
        )
        sections.append(_make(role, bars, cue))
        prev_role = role
        prev_bars = bars
        prev_sparse = sparse
    sections.append(_make("outro", 2, _unique_cue("outro", salt + 99, salt, used)))
    fitted = fit_drive_sections(sections, bpm=bpm, salt=salt, used=used)
    _ensure_drops(fitted, salt, used)
    _place_rare_breakdown(
        fitted,
        salt,
        used,
        gate=_salt(album_slug, track_number, seed),
    )
    _ensure_sparse(fitted, salt, queue, used)
    return fitted


def _is_sparse(section: SongSection) -> bool:
    """Whether a stanza's cue is a downbeat-only sparse one.

    Args:
        section: Planned stanza.

    Returns:
        True when the cue's last comma part is a ``_SPARSE`` phrase.
    """
    parts = _music(section["pattern"]).split(", ")
    return len(parts) >= 2 and parts[-1] in _SPARSE


def _check(sections: list[SongSection]) -> None:
    """Reject a take that runs long, starts late, or names brass.

    Also rejects two adjacent sparse stanzas and long takes with fewer
    than three of them.

    Args:
        sections: Fitted stanzas.

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
        raise ValueError("need at least five drops")
    body = len(sections) - 2
    if body > 0 and drops < _drop_target(body):
        raise ValueError("drop target below minimum")
    run = 0
    prev_run_role: str | None = None
    for section in sections:
        if section["role"] == prev_run_role:
            run += 1
        else:
            run = 1
            prev_run_role = section["role"]
        if run > 2:
            raise ValueError("role run longer than two stanzas")
    if sum(section["role"] == "breakdown" for section in sections) > 1:
        raise ValueError("more than one breakdown")
    sparse_flags = [_is_sparse(section) for section in sections]
    for flag, prev in zip(sparse_flags[1:], sparse_flags):
        if flag and prev:
            raise ValueError("two adjacent stanzas are both sparse")
    if body >= 20 and sum(sparse_flags) < 3:
        raise ValueError("take needs at least three sparse stanzas")
    musics = [_music(section["pattern"]) for section in sections]
    if len(musics) != len(set(musics)):
        raise ValueError("a cue repeats inside the take")
    for section, music in zip(sections, musics):
        if _blocked(music):
            raise ValueError(f"banned cue in {section['role']}")
        if section["role"] != "drop" and "drop" in music:
            raise ValueError("drop language landed on a fill")


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
        ``short`` under 100, ``standard`` under 112, else ``long``.
    """
    if seconds < 100:
        return "short"
    if seconds < 112:
        return "standard"
    return "long"


def _plan_one(
    *,
    album_slug: str,
    track_number: int,
    bpm: int,
    seed: int,
    lyrics: str,
    recipe: str,
    extra: int,
) -> SongPlan:
    """Plan one take.

    Args:
        album_slug: Album folder slug.
        track_number: One-based index.
        bpm: Performance tempo.
        seed: Take seed.
        lyrics: Authored score.
        recipe: Audio Rack recipe id.
        extra: Collision retry.

    Returns:
        The song plan.
    """
    sections = _compose(
        album_slug=album_slug,
        track_number=track_number,
        bpm=bpm,
        seed=seed,
        lyrics=lyrics,
        recipe=recipe,
        extra=extra,
    )
    _check(sections)
    seconds = _seconds(sections, bpm)
    return {
        "form_id": _form_id(album_slug, seed, sections),
        "sections": sections,
        "meter": "4",
        "keyscale": validate_keyscale(keyscale_for("drive-through", album_slug, track_number)),
        "duration_s": seconds,
        "bpm": int(bpm),
        "bucket": _bucket(seconds),
    }

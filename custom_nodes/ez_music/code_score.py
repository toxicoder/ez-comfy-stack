"""Translate the Drive-through coder into bass-set cues.

The corpus is ``drive_arrange.py`` then ``edm_examples.py``, in source
order. Comments and punctuation are skipped. A banned spelling never
enters a cue; its length and a digest still move the salt, so the
refusal is heard as a different palette choice.
"""

from __future__ import annotations

import hashlib
import io
import re
import tokenize
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

from .drive_arrange import (
    DRIVE_LYRICS_CHAR_BUDGET,
    RECIPE_LINES,
    _blocked,
    _cue_for,
    _salt,
    fit_sections_to_lyrics,
    lift_drive_bpm,
)
from .song_plan import SongSection

# Source files, in the order the album reads them.
_ARRANGER = "drive_arrange.py"
_CATALOG = "edm_examples.py"
_WORD = re.compile(r"[A-Za-z0-9_]+")
_TEXT_TYPES = frozenset({tokenize.STRING, tokenize.FSTRING_MIDDLE})
_ATTEMPTS = 96

# (filename, slug, title, function names) in album order.
_GROUPS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (_ARRANGER, "lift-tempo", "lift tempo", ("lift_drive_bpm",)),
    (_ARRANGER, "fit-window", "fit window", ("fit_drive_sections",)),
    (_ARRANGER, "plan-album", "plan album", ("plan_drive_album",)),
    (
        _ARRANGER,
        "arrange-score",
        "arrange score",
        ("arrange_drive", "_signature", "_seconds"),
    ),
    (_ARRANGER, "salt-menu", "salt menu", ("_salt", "_music", "_menu_count")),
    (_ARRANGER, "ban-list", "ban list", ("_needles", "_blocked")),
    (
        _ARRANGER,
        "cue-bed",
        "cue bed",
        ("_slot", "_bed", "_cue_for", "_unique_cue"),
    ),
    (
        _ARRANGER,
        "pick-role",
        "pick role",
        ("_mix_int", "_pick_role", "_pick_bars", "_make"),
    ),
    (
        _ARRANGER,
        "donor-lane",
        "donor lane",
        ("_donor_queue", "_take_donor", "_with_extras", "_cue_with_donor"),
    ),
    (
        _ARRANGER,
        "fit-edits",
        "fit edits",
        ("_drop_tail", "_insert", "_ensure_drops", "_place_rare_breakdown"),
    ),
    (_ARRANGER, "compose", "compose", ("_compose",)),
    (
        _ARRANGER,
        "check-form",
        "check form",
        ("_check", "_form_id", "_bucket", "_plan_one"),
    ),
    (_CATALOG, "splice-tags", "splice tags", ("_tempo_id", "_splice_drive", "drive_tags")),
    (_CATALOG, "catalog-row", "catalog row", ("_desc", "_ex")),
    (
        _CATALOG,
        "score-format",
        "score format",
        ("_cues_from_body", "_uniquify_score", "_spell_score_body", "format_edm_score"),
    ),
    (
        _CATALOG,
        "finalize-album",
        "finalize album",
        ("drive_slug_from_stem", "finalize_drive_album", "_catalog"),
    ),
)


class CodeSpan(NamedTuple):
    """One album take's slice of the coder.

    Attributes:
        slug: Kebab title used in the lab stem.
        title: Operator-facing take name.
        tokens: Names, keywords, numbers, and string words in order.
    """

    slug: str
    title: str
    tokens: tuple[str, ...]


def _package_dir() -> Path:
    """Directory that holds the coder sources.

    Returns:
        ``custom_nodes/ez_music``.
    """
    return Path(__file__).resolve().parent


def _function_lines(source: str) -> dict[str, tuple[int, int]]:
    """Map each top-level function or class to inclusive line numbers.

    Args:
        source: Python source.

    Returns:
        Name to ``(first line, last line)``, 1-based.
    """
    import ast

    tree = ast.parse(source)
    found: dict[str, tuple[int, int]] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            end = node.end_lineno
            assert end is not None
            found[node.name] = (node.lineno, end)
    return found


def _bounds(
    source: str,
    groups: Sequence[tuple[str, ...]],
) -> tuple[tuple[int, int], ...]:
    """Line ranges for one file's groups.

    Leading lines attach to the first group. A gap attaches to the next
    group. Trailing lines attach to the last group.

    Args:
        source: Python source of one coder file.
        groups: Function-name tuples, in source order.

    Returns:
        Inclusive 1-based ``(start, end)`` per group.

    Raises:
        ValueError: a named function is not in the source.
    """
    found = _function_lines(source)
    ranges: list[list[int]] = []
    for names in groups:
        starts: list[int] = []
        ends: list[int] = []
        for name in names:
            if name not in found:
                raise ValueError(f"missing coder function {name}")
            start, end = found[name]
            starts.append(start)
            ends.append(end)
        ranges.append([min(starts), max(ends)])
    if not ranges:
        return ()
    ranges[0][0] = 1
    last_line = max(len(source.splitlines()), 1)
    for index in range(1, len(ranges)):
        ranges[index][0] = ranges[index - 1][1] + 1
    ranges[-1][1] = last_line
    return tuple((start, end) for start, end in ranges)


def _words(tok: tokenize.TokenInfo) -> tuple[str, ...]:
    """Words contributed by one token. Punctuation and comments add none.

    Args:
        tok: A tokenizer token.

    Returns:
        Zero or more source words.
    """
    if tok.type in {tokenize.NAME, tokenize.NUMBER}:
        return (tok.string,)
    if tok.type in _TEXT_TYPES:
        return tuple(_WORD.findall(tok.string))
    return ()


def _tokens_in(source: str, start: int, end: int) -> tuple[str, ...]:
    """Words whose token starts on a line in ``start..end``.

    Args:
        source: Python source.
        start: First line, 1-based, inclusive.
        end: Last line, 1-based, inclusive.

    Returns:
        Words in source order.
    """
    words: list[str] = []
    reader = io.StringIO(source).readline
    for tok in tokenize.generate_tokens(reader):
        line = tok.start[0]
        if line < start or line > end:
            continue
        words.extend(_words(tok))
    return tuple(words)


def coder_spans() -> tuple[CodeSpan, ...]:
    """The sixteen takes, covering both coder files in order.

    Returns:
        One span per album track.

    Raises:
        ValueError: a grouped function is missing from its file.
    """
    root = _package_dir()
    by_file: dict[str, list[tuple[str, str, tuple[str, ...]]]] = {}
    for filename, slug, title, names in _GROUPS:
        by_file.setdefault(filename, []).append((slug, title, names))
    spans: list[CodeSpan] = []
    for filename, groups in by_file.items():
        source = (root / filename).read_text(encoding="utf-8")
        bounds = _bounds(source, tuple(names for _slug, _title, names in groups))
        for (slug, title, _names), (start, end) in zip(groups, bounds):
            spans.append(CodeSpan(slug, title, _tokens_in(source, start, end)))
    return tuple(spans)


def coder_tokens() -> tuple[str, ...]:
    """Every kept word of both coder files, arranger then catalog.

    Returns:
        The album's token stream.
    """
    root = _package_dir()
    words: list[str] = []
    for filename in (_ARRANGER, _CATALOG):
        source = (root / filename).read_text(encoding="utf-8")
        last = len(source.splitlines()) or 1
        words.extend(_tokens_in(source, 1, last))
    return tuple(words)


def _windows(tokens: Sequence[str], cells: int) -> tuple[tuple[str, ...], ...]:
    """Pack tokens into cells from the front. Extra cells stay empty.

    Window width is ``ceil(len(tokens) / cells)``, so every token lands
    in exactly one cell and empty cells sit at the end.

    Args:
        tokens: Span words.
        cells: How many stanzas need a window.

    Returns:
        One window per cell. Empty when there are no cells.
    """
    if cells < 1:
        return ()
    total = len(tokens)
    if total < 1:
        return tuple(() for _index in range(cells))
    width = (total + cells - 1) // cells
    packed: list[tuple[str, ...]] = []
    for index in range(cells):
        start = index * width
        if start >= total:
            packed.append(())
            continue
        packed.append(tuple(tokens[start : min(total, start + width)]))
    return tuple(packed)


def _piece(token: str) -> str:
    """Salt fragment for one word.

    A banned spelling is replaced with its length and digest so the cue
    text cannot echo the word.

    Args:
        token: One source word.

    Returns:
        A fragment safe to mix into the salt.
    """
    if _blocked(token):
        digest = hashlib.sha256(token.encode()).hexdigest()[:8]
        return f"refused:{len(token)}:{digest}"
    return token


def _window_salt(window: Sequence[str], cell: int, span: Sequence[str]) -> int:
    """Salt for one cell. An empty window re-voices the whole span.

    Args:
        window: This cell's words. Empty when the span ran out.
        cell: Cell index.
        span: The take's full token stream.

    Returns:
        A stable positive integer.
    """
    source = window if window else span
    parts = [_piece(token) for token in source]
    if not window:
        parts.append(f"revoice:{cell}")
    parts.append(f"cell:{cell}")
    return _salt(*parts)


def _fresh_cue(role: str, index: int, salt: int, used: set[str]) -> str:
    """One palette cue this take has not used yet.

    Args:
        role: ACE role.
        index: Cell index.
        salt: Window salt.
        used: Cues already emitted. Updated on success.

    Returns:
        A Drive-through production cue.

    Raises:
        ValueError: every attempt was banned, repeated, or drop-language
            on a fill.
    """
    for attempt in range(_ATTEMPTS):
        cue = _cue_for(role, index, salt + attempt, attempt)
        if cue in used or _blocked(cue):
            continue
        if role != "drop" and "drop" in cue:
            continue
        used.add(cue)
        return cue
    raise ValueError(f"no code cue for {role} at {index}")


def cell_cues(tokens: Sequence[str], roles: Sequence[str]) -> tuple[str, ...]:
    """Translate a token span into one cue per role.

    Args:
        tokens: Words for this take, in source order.
        roles: Stanza roles, build then body then outro.

    Returns:
        One cue per role. Earlier cues ignore later tokens.
    """
    used: set[str] = set()
    span = tuple(tokens)
    windows = _windows(span, len(roles))
    cues: list[str] = []
    for index, role in enumerate(roles):
        salt = _window_salt(windows[index], index, span)
        cues.append(_fresh_cue(role, index, salt, used))
    return tuple(cues)


def apply_code_cues(sections: list[SongSection], tokens: Sequence[str]) -> None:
    """Replace each stanza's musical cue with the code translation.

    Roles and bar counts stay. The pattern keeps the ``, N bars`` suffix
    the arranger already writes.

    Args:
        sections: Fitted stanzas. Mutated.
        tokens: This take's coder words.
    """
    cues = cell_cues(tokens, tuple(section["role"] for section in sections))
    for section, cue in zip(sections, cues):
        bars = int(section["bars"])
        section["pattern"] = f"{cue}, {bars} bars"


def voice_code_sections(
    sections: Sequence[SongSection],
    tokens: Sequence[str],
) -> list[SongSection]:
    """Fit stanzas to the lyric window, then voice the survivors.

    Re-voicing can change the score length, so the fit is re-measured
    after every voice pass. When the re-voiced score runs over the
    window, one more stanza is dropped in front of the outro and the
    pass repeats. The plan keeps its full duration.

    Args:
        sections: Fitted stanzas, build-up then drop ... outro.
        tokens: This take's coder words.

    Returns:
        New stanza list whose cues come from the coder span and whose
        rendered score fits ``DRIVE_LYRICS_CHAR_BUDGET``.

    Raises:
        ValueError: the budget cannot be met without losing structure.
    """
    current = list(sections)
    while True:
        kept = fit_sections_to_lyrics(current)
        apply_code_cues(kept, tokens)
        score = [
            f"[{section['role']} - {section['pattern']}]" for section in kept
        ]
        if len("\n\n".join(score)) <= DRIVE_LYRICS_CHAR_BUDGET:
            return kept
        _drop_lyrics_tail(kept)
        current = kept


def _drop_lyrics_tail(sections: list[SongSection]) -> None:
    """Drop one more stanza in front of the outro after an overrun.

    Args:
        sections: Stanzas ending in the outro. Mutated.

    Raises:
        ValueError: no unprotected stanza is left to drop.
    """
    drops = sum(section["role"] == "drop" for section in sections)
    for index in range(len(sections) - 2, 1, -1):
        if sections[index]["role"] == "drop" and drops <= 3:
            continue
        del sections[index]
        return
    raise ValueError("drive score cannot fit the lyric window")


def authored_bpm(tokens: Sequence[str]) -> int:
    """Authored tempo for a span, before the Audio Rack snap.

    Args:
        tokens: Take words.

    Returns:
        An integer from 140 through 176.
    """
    return 140 + (_salt(*tokens) % 37)


def performance_bpm(tokens: Sequence[str]) -> int:
    """Snapped Drive-through tempo for a span.

    Args:
        tokens: Take words.

    Returns:
        One of 165, 168, 170, 172, 174, 176.
    """
    return lift_drive_bpm(authored_bpm(tokens))


def performance_recipe(tokens: Sequence[str]) -> str:
    """Audio Rack recipe for a span. Never the DJ-shout recipe.

    Args:
        tokens: Take words.

    Returns:
        A ``rec_drive_*`` id other than ``rec_drive_dj_shout``.
    """
    keys = tuple(key for key in RECIPE_LINES if key != "rec_drive_dj_shout")
    return keys[_salt("recipe", *tokens) % len(keys)]

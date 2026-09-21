"""Schema, uniqueness, and brand-scan tests for Audio Rack catalogs."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_prompt_enhance import audio  # noqa: E402

_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,47}$")
_MIN_PER_AXIS = 100

_BANNED = (
    "drake",
    "kendrick",
    "eminem",
    "kanye",
    "beyonce",
    "ableton",
    "serum",
    "omnisphere",
    "fabfilter",
    "tiktok",
    "instagram",
    "youtube",
    "spotify",
    "distrokid",
    "nill bye",
    "in the style of",
)

_STOP = frozenset(
    "the a an of to and in on at as with without from for by into onto over under "
    "is are was were be being been this that audio music track mix so then that "
    "sit sits sitting still".split()
)

_VARIANT_TOKENS = frozenset(
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


def _variant_normalized(text: str) -> set[str]:
    return {word for word in _tokens(text) if word not in _VARIANT_TOKENS}


def test_axes_cover_thirteen_widget_ids() -> None:
    audio.reset_audio_caches_for_tests()
    axes = audio.load_axes()
    assert len(axes) == 13
    assert tuple(audio.axis_ids()) == audio.WIDGET_AXIS_ORDER
    orders = [int(meta["splice_order"]) for meta in axes.values()]
    assert orders == sorted(orders)
    for axis_id, meta in axes.items():
        assert meta["id"] == axis_id
        assert str(meta["label"]).strip()
        assert isinstance(meta["vocal_include"], bool)
        assert isinstance(meta["instrumental_include"], bool)
        assert isinstance(meta["podcast_include"], bool)
        assert isinstance(meta["bpm_axis"], bool)
        assert isinstance(meta["form_axis"], bool)
        assert isinstance(meta["vocal_axis"], bool)


def test_each_axis_has_at_least_one_hundred_unique_techniques() -> None:
    audio.reset_audio_caches_for_tests()
    seen: set[str] = set()
    for axis_id in audio.axis_ids():
        rows = audio.load_axis(axis_id)
        assert len(rows) >= _MIN_PER_AXIS, f"{axis_id} has {len(rows)}"
        labels: set[str] = set()
        for row in rows:
            tid = str(row["id"])
            assert audio.validate_id(tid), tid
            assert tid not in seen, f"duplicate id {tid}"
            seen.add(tid)
            label = str(row["label"]).strip()
            assert label, tid
            assert label.lower() not in labels, f"duplicate label {label} on {axis_id}"
            labels.add(label.lower())
            clause = str(row["clause"]).strip()
            assert clause, tid
            assert not re.search(
                r"^[a-z][a-z0-9 ]{0,40} is a (type of|kind of|term for)\b",
                clause.lower(),
            ), tid
            if row.get("_bpm_axis"):
                assert str(row.get("bpm") or "").strip(), f"{tid} needs bpm"
            if row.get("_form_axis"):
                form_blob = "\n".join(
                    (
                        str(row.get("lyrics_form") or ""),
                        str(row.get("lyrics_form_inst") or ""),
                    )
                )
                assert form_blob.strip(), f"{tid} needs lyrics form"
                assert "[form-" not in form_blob, tid
                for line in form_blob.splitlines():
                    stripped = line.strip()
                    if not stripped.startswith("["):
                        continue
                    label = stripped[1:].split("]", 1)[0].split(" - ", 1)[0].strip()
                    assert label in {
                        "intro",
                        "verse",
                        "pre-chorus",
                        "chorus",
                        "bridge",
                        "inst",
                        "breakdown",
                        "build-up",
                        "drop",
                        "outro",
                        "spoken word",
                    }, (tid, label)
            for field in ("clause", "tags", "lyrics_form", "bpm", "label"):
                blob = str(row.get(field) or "").lower()
                for brand in _BANNED:
                    assert brand not in blob, f"{tid}.{field} has {brand!r}"


def test_conflict_ids_exist() -> None:
    audio.reset_audio_caches_for_tests()
    known = {
        str(row["id"])
        for axis_id in audio.axis_ids()
        for row in audio.load_axis(axis_id)
    }
    for axis_id in audio.axis_ids():
        for row in audio.load_axis(axis_id):
            for other in audio._string_list(row, "conflicts"):
                assert other in known, f"{row['id']} conflicts unknown {other}"


def test_combo_ids_start_with_none() -> None:
    audio.reset_audio_caches_for_tests()
    for axis_id in audio.axis_ids():
        ids = audio.combo_ids(axis_id)
        assert ids[0] == audio.NONE
        assert len(ids) == 1 + len(audio.load_axis(axis_id))


def test_same_axis_clauses_are_not_synonym_padding() -> None:
    audio.reset_audio_caches_for_tests()
    for axis_id in audio.axis_ids():
        rows = audio.load_axis(axis_id)
        bags = [
            (str(row["id"]), _variant_normalized(str(row["clause"]))) for row in rows
        ]
        for idx, (left_id, left) in enumerate(bags):
            if len(left) < 6:
                continue
            for right_id, right in bags[idx + 1 :]:
                if len(right) < 6:
                    continue
                shared = left & right
                union = left | right
                if not union:
                    continue
                overlap = len(shared) / len(union)
                assert overlap < 0.85, (
                    f"{axis_id} {left_id} vs {right_id} overlap {overlap:.2f}"
                )


def test_drive_through_catalog_ids_exist() -> None:
    audio.reset_audio_caches_for_tests()
    needed = (
        "gen_riddim",
        "gen_tearout",
        "gen_brostep",
        "gen_wave_bass",
        "gen_color_bass",
        "gen_dirty_bass",
        "gen_dirty_dubstep",
        "gen_drumstep",
        "gen_neuro_bass",
        "gen_chest_bass",
        "gen_festival_trap",
        "bass_growl",
        "bass_reese",
        "bass_formant",
        "bass_warped",
        "bass_pedal_dual",
        "bass_fold",
        "bass_stacked_808",
        "bass_body",
        "ins_warped_bass",
        "mix_drive_lock",
        "mix_drive_treat",
        "voc_dj_shout",
        "frm_drop_shout",
        "tmp_150",
        "tmp_176",
        "rec_drive_riddim",
        "rec_drive_dj_shout",
    )
    for tid in needed:
        if tid.startswith("rec_"):
            assert tid in audio.load_recipes(), tid
        else:
            assert audio.technique(tid) is not None, tid
    drop = audio.load_recipes()["rec_drive_through_drop"]["axes"]
    assert drop["instruments_texture"] == "ins_warped_bass"
    after = audio.load_recipes()["rec_warped_afterparty"]["axes"]
    assert after["instruments_texture"] == "ins_warped_bass"


def test_recipes_fill_known_axes() -> None:
    audio.reset_audio_caches_for_tests()
    recipes = audio.load_recipes()
    assert len(recipes) >= 20
    known = {
        str(row["id"])
        for axis_id in audio.axis_ids()
        for row in audio.load_axis(axis_id)
    }
    for rid, recipe in recipes.items():
        assert audio.validate_id(rid), rid
        assert str(recipe.get("label") or "").strip(), rid
        axes = recipe.get("axes") or {}
        assert isinstance(axes, dict) and axes, rid
        for axis_id, tid in axes.items():
            assert axis_id in audio.load_axes(), f"{rid} unknown axis {axis_id}"
            assert tid in known, f"{rid} unknown technique {tid}"

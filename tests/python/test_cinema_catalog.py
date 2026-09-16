"""Schema, uniqueness, and brand-scan tests for Cinema Rack catalogs."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_prompt_enhance import cinema  # noqa: E402

_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,47}$")
_MIN_PER_AXIS = 100

_BANNED = (
    "kodak",
    "portra",
    "sony",
    "canon",
    "leica",
    "hasselblad",
    "pixar",
    "unreal",
    "lumen",
    "ghibli",
    "panavision",
    "arriflex",
    "arri ",
    "red komodo",
    "imax",
    "dolby",
    "technicolor",
    "nolan",
    "fincher",
    "tarantino",
    "spielberg",
    "scorsese",
    "villeneuve",
    "blade runner",
    "mad max",
    "tiktok",
    "instagram",
    "youtube",
)

_STOP = frozenset(
    "the a an of to and in on at as with without from for by into onto over under "
    "is are was were be being been this that camera frame subject light look shot "
    "still motion".split()
)

_VARIANT_TOKENS = frozenset(
    {
        "left",
        "right",
        "up",
        "down",
        "slow",
        "fast",
        "whip",
        "crawl",
        "crash",
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
        "day",
        "night",
        "dawn",
        "dusk",
        "vertical",
        "horizontal",
    }
)


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if word not in _STOP and len(word) > 2}


def _variant_normalized(text: str) -> set[str]:
    return {word for word in _tokens(text) if word not in _VARIANT_TOKENS}


def test_axes_cover_thirteen_widget_ids() -> None:
    cinema.reset_cinema_caches_for_tests()
    axes = cinema.load_axes()
    assert len(axes) == 13
    assert tuple(cinema.axis_ids()) == cinema.WIDGET_AXIS_ORDER
    orders = [int(meta["splice_order"]) for meta in axes.values()]
    assert orders == sorted(orders)
    for axis_id, meta in axes.items():
        assert meta["id"] == axis_id
        assert str(meta["label"]).strip()
        assert meta["still_mode"] in {"clause", "freeze", "omit"}
        assert isinstance(meta["i2v_include"], bool)
        assert isinstance(meta["identity_include"], bool)
        assert isinstance(meta["wan_camera"], bool)


def test_each_axis_has_at_least_one_hundred_unique_techniques() -> None:
    cinema.reset_cinema_caches_for_tests()
    seen: set[str] = set()
    for axis_id in cinema.axis_ids():
        rows = cinema.load_axis(axis_id)
        assert len(rows) >= _MIN_PER_AXIS, f"{axis_id} has {len(rows)}"
        labels: set[str] = set()
        for row in rows:
            tid = str(row["id"])
            assert cinema.validate_id(tid), tid
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
            still_ok = cinema._as_bool(row.get("still_ok"), True)
            still_mode = str(row.get("_still_mode") or "")
            if still_ok and still_mode == "freeze":
                assert str(row.get("still") or "").strip(), f"{tid} needs still"
            if row.get("_wan_camera"):
                assert str(row.get("wan_token") or "").strip(), f"{tid} needs wan_token"
            for field in ("clause", "still", "wan_token", "audio", "label"):
                blob = str(row.get(field) or "").lower()
                for brand in _BANNED:
                    assert not re.search(
                        rf"\b{re.escape(brand)}\b", blob
                    ), f"{tid}.{field} has {brand!r}"


def test_conflict_ids_exist() -> None:
    cinema.reset_cinema_caches_for_tests()
    known = {str(row["id"]) for axis_id in cinema.axis_ids() for row in cinema.load_axis(axis_id)}
    for axis_id in cinema.axis_ids():
        for row in cinema.load_axis(axis_id):
            for other in cinema._string_list(row, "conflicts"):
                assert other in known, f"{row['id']} conflicts unknown {other}"


def test_combo_ids_start_with_none() -> None:
    cinema.reset_cinema_caches_for_tests()
    for axis_id in cinema.axis_ids():
        ids = cinema.combo_ids(axis_id)
        assert ids[0] == cinema.NONE
        assert len(ids) == 1 + len(cinema.load_axis(axis_id))


def test_same_axis_clauses_are_not_synonym_padding() -> None:
    cinema.reset_cinema_caches_for_tests()
    for axis_id in cinema.axis_ids():
        rows = cinema.load_axis(axis_id)
        bags = [(str(row["id"]), _variant_normalized(str(row["clause"]))) for row in rows]
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

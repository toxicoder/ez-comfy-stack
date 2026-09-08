"""Shot-bible contract for US-safe 90s shorts.

Hermetic: stdlib only. YAML parsed via ez_film.shots (no PyYAML).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from _lab_paths import lab_json

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_film.shots import (  # noqa: E402
    DFR_TEMPLATE,
    ICLORA_TEMPLATE,
    LTX_PRINT_TEMPLATE,
    parse_shots_yaml,
    print_template,
    scaffold_shot_sheet,
    write_shots_yaml,
)

SHORTS = ROOT / "workflows" / "shorts"

FILMS = (
    ("go-see", "gosee"),
    ("still-here", "stillhere"),
    ("switchyard", "switchyard"),
)

BANNED = ("MiniMax", "MiniMaxH3", "minimax_h3", "klein-9b", "FLUX.2-dev")
LONG_LATENT_TYPES = (
    "Wan22ImageToVideoLatent",
    "LTXVImgToVideo",
    "EmptyLTXVLatentVideo",
    "LTXVEmptyLatentAudio",
)
KLEIN_NEGATION = ("no logos", "no violence", "without text", "no people")
SHOT_INDEX_RE = re.compile(r"Shot \d+ of 18")
WAN_AUDIO_WORDS = ("score", "music", "audio", "sound", "breath")
LTX_CLOSE = "No music and no score."
BIBLES = {
    "go-see": "film-go-see-90s-run-lab-example.json",
    "still-here": "film-still-here-90s-lab-example.json",
    "switchyard": "film-switchyard-90s-lab-example.json",
}


def _path(film: str) -> Path:
    return SHORTS / f"{film}.shots.yaml"


def test_print_template_ltx_and_dfr() -> None:
    assert print_template("ltx") == LTX_PRINT_TEMPLATE
    assert print_template("dfr") == DFR_TEMPLATE
    assert print_template("ltx-iclora-depth") == ICLORA_TEMPLATE
    assert print_template("wan-flf") == "wan-flf-5s-lab-example.json"
    assert print_template("dcc-final") == "dcc-final"
    assert DFR_TEMPLATE.startswith("templates/ltx-2.5/")
    try:
        print_template("nope")
    except ValueError as exc:
        assert "ltx-iclora-depth" in str(exc)
    else:
        raise AssertionError("print_template must refuse unknown modes")


def test_three_shot_bibles_exist() -> None:
    for film, _slug in FILMS:
        assert _path(film).is_file(), film


def test_eighteen_shots_and_chain() -> None:
    for film, slug in FILMS:
        text = _path(film).read_text(encoding="utf-8")
        parsed = parse_shots_yaml(text)
        meta = parsed["meta"]
        assert meta["film"] == film
        assert meta["slug"] == slug
        assert meta["frames"] == "120"
        assert meta["fps"] == "24"
        assert meta["duration_s"] == "5.00"
        assert meta["beats"] == "6"
        assert meta["shots_per_beat"] == "3"
        assert meta["total_shots"] == "18"
        assert meta["publish_cap_s"] == "90.00"
        assert meta["print"] == "ltx"
        assert meta["identity_seed"] == "42"
        if film == "go-see":
            assert meta["identity_enhance"] == "false"
        else:
            assert meta["identity_enhance"] == "true"
        shots = parsed["shots"]
        assert len(shots) == 18, (film, len(shots))
        prefixes = [s["prefix"] for s in shots]
        assert len(set(prefixes)) == 18
        assert shots[0]["load_from"] == "identity"
        for i, shot in enumerate(shots):
            assert shot["prefix"] == f"ez_{slug}_b{shot['beat']}_s{shot['shot']}"
            if i:
                assert shot["load_from"] == f"{shots[i - 1]['prefix']}_last"
        assert parsed["identity"].strip()
        assert LTX_CLOSE in text
        assert parsed["meta"]["audio_policy"] == "world-only"
        assert parsed["meta"]["score"] == "none"
        for shot in shots:
            assert shot["clay"] == "skip"
            assert shot["audio_lock"] == "none"
            assert shot["dialogue"] == ""


def test_klein_identity_is_model_native() -> None:
    for film, _slug in FILMS:
        identity = parse_shots_yaml(_path(film).read_text(encoding="utf-8"))["identity"]
        lower = identity.lower()
        assert "YouTube 16:9" in identity or "youtube 16:9" in lower
        assert "mm" in lower
        assert "unmarked" in lower or "empty of lettering" in lower
        for needle in KLEIN_NEGATION:
            assert needle not in lower, (film, needle)
        words = identity.split()
        assert len(words) < 150, (film, len(words))


def test_ltx_i2v_prompts_are_model_native() -> None:
    for film, _slug in FILMS:
        parsed = parse_shots_yaml(_path(film).read_text(encoding="utf-8"))
        for shot in parsed["shots"]:
            ltx = shot["ltx_i2v"]
            assert ltx.startswith("The start image holds as the first frame.")
            assert not ltx.startswith("The scene opens with")
            assert SHOT_INDEX_RE.search(ltx) is None, (film, shot["prefix"])
            assert LTX_CLOSE in ltx
            assert len(ltx.split()) <= 200, (film, shot["prefix"], len(ltx.split()))
            foley = (
                "breath",
                "wind",
                "rain",
                "footfall",
                "footstep",
                "grit",
                "kettle",
                "hum",
                "steam",
                "gravel",
                "creak",
                "click",
                "splash",
                "horn",
                "rung",
                "pour",
                "ceramic",
                "cloth",
                "tick",
                "ice",
                "grating",
                "fabric",
                "chime",
                "boot",
                "scrape",
                "metal",
            )
            assert any(word in ltx.lower() for word in foley), (film, shot["prefix"])
            wan = shot["wan_i2v"]
            wan_l = wan.lower()
            for word in WAN_AUDIO_WORDS:
                assert word not in wan_l, (film, shot["prefix"], word)


def test_shot_card_invalid_audio_policy_fails() -> None:
    text = _path("go-see").read_text(encoding="utf-8")
    text = "audio_policy: karaoke\n" + text
    try:
        parse_shots_yaml(text)
    except ValueError as exc:
        assert "audio_policy" in str(exc)
    else:
        raise AssertionError("invalid audio_policy must fail closed")


def test_shot_card_roundtrip_defaults() -> None:
    text = _path("go-see").read_text(encoding="utf-8")
    parsed = parse_shots_yaml(text)
    parsed["meta"]["audio_policy"] = "stems"
    parsed["shots"][0]["clay"] = "required"
    parsed["shots"][0]["camera"] = "fixed"
    parsed["shots"][0]["script"] = "Sprint the terrace."
    out = write_shots_yaml(parsed)
    again = parse_shots_yaml(out)
    assert again["meta"]["audio_policy"] == "stems"
    assert again["shots"][0]["clay"] == "required"
    assert again["shots"][0]["camera"] == "fixed camera"
    assert again["shots"][0]["script"] == "Sprint the terrace."
    assert len(again["shots"]) == 18
    scaffold = scaffold_shot_sheet(text)
    sc = parse_shots_yaml(scaffold)
    assert sc["meta"]["audio_policy"] == "world-only"
    assert "audio_policy: world-only" in scaffold


def test_shorts_yaml_has_no_banned_models() -> None:
    for film, _slug in FILMS:
        text = _path(film).read_text(encoding="utf-8")
        for needle in BANNED:
            assert needle not in text, (film, needle)


def test_creative_locks() -> None:
    go = _path("go-see").read_text(encoding="utf-8")
    assert "sun-washed teal" in go
    assert "olive windbreaker" not in go
    assert "First-person" in go or "first-person" in go
    assert "body-cam" in go
    assert "parkour" in go.lower()
    assert "gloves" in go.lower()
    assert "dead sprint" in go.lower()
    assert "laugh" not in go.lower()
    for needle in ("Faith", "Mirror's Edge", "Mirrors Edge", "barrel-roll", "backflip"):
        assert needle not in go, needle
    parsed = parse_shots_yaml(go)
    stunts = (
        "sprint",
        "flip",
        "vault",
        "wall-run",
        "leap",
        "dive",
        "slide",
        "climb",
        "hold",
        "burst",
    )
    for shot in parsed["shots"]:
        blob = shot["ltx_i2v"].lower()
        assert "no speech" in blob, shot["prefix"]
        assert any(token in blob for token in stunts), shot["prefix"]
        if shot["prefix"] != "ez_gosee_b6_s3":
            assert shot["end_state"], shot["prefix"]
    for i, shot in enumerate(parsed["shots"][:-1]):
        token = shot["end_state"].lower()
        nxt = parsed["shots"][i + 1]["ltx_i2v"].lower()
        assert token in nxt, (shot["prefix"], token)
    here = _path("still-here").read_text(encoding="utf-8")
    assert "ceramic mug" in here
    assert "two-note" in here or "invented" in here
    yard = _path("switchyard").read_text(encoding="utf-8")
    assert "railroad" in yard
    assert "boxcar" in yard or "boxcars" in yard


def _json_files() -> list[Path]:
    from _lab_paths import LAB_ROOT

    files = sorted((LAB_ROOT / "shorts").glob("*-lab-example.json"))
    assert files, "expected shorts lab JSON"
    return files


def _overlap_hits(graph: dict) -> list[str]:
    pad = 20
    boxes = []
    for node in graph["nodes"]:
        x, y = node["pos"]
        size = node.get("size", [200, 100])
        if isinstance(size, dict):
            width, height = float(size.get("0", 200)), float(size.get("1", 100))
        else:
            width, height = float(size[0]), float(size[1])
        boxes.append(
            (
                node["id"],
                node["type"],
                x - pad,
                y - pad,
                x + width + pad,
                y + height + pad,
            )
        )
    hits = []
    for i, a in enumerate(boxes):
        for b in boxes[i + 1 :]:
            if a[2] < b[4] and a[4] > b[2] and a[3] < b[5] and a[5] > b[3]:
                hits.append(f"{a[0]}({a[1]}) vs {b[0]}({b[1]})")
    return hits


def test_shorts_json_parse_ids_and_banned_strings() -> None:
    expected = {
        "film-go-see-90s-run-lab-example",
        "film-still-here-90s-lab-example",
        "film-switchyard-90s-lab-example",
    }
    names = {p.stem for p in _json_files()}
    assert names == expected
    for path in _json_files():
        text = path.read_text(encoding="utf-8")
        for needle in BANNED:
            assert needle not in text, (path.name, needle)
        graph = json.loads(text)
        assert graph.get("id") == path.stem
        ids = [n["id"] for n in graph["nodes"]]
        assert len(ids) == len(set(ids)), path.name
        assert not _overlap_hits(graph), (path.name, _overlap_hits(graph))
        notes = [n for n in graph["nodes"] if n.get("type") in ("Note", "MarkdownNote")]
        assert notes
        assert any(
            isinstance(n.get("widgets_values"), list)
            and n["widgets_values"]
            and len(str(n["widgets_values"][0]).strip()) > 40
            for n in notes
        )
        clips = [n for n in graph["nodes"] if n.get("type") == "CLIPTextEncode"]
        assert len(clips) >= 20, path.name
        lab_note = graph.get("extra", {}).get("lab_note")
        assert isinstance(lab_note, str) and lab_note.strip()
        assert "Queue once" in lab_note or "Queue **once**" in lab_note


def test_shot_graphs_are_five_second_i2v() -> None:
    wan = json.loads(lab_json("wan-i2v-shot-lab-example.json").read_text(encoding="utf-8"))
    ltx = json.loads(lab_json("ltx-i2v-shot-lab-example.json").read_text(encoding="utf-8"))
    wan_len = next(
        n["widgets_values"][2]
        for n in wan["nodes"]
        if n.get("type") == "Wan22ImageToVideoLatent"
    )
    ltx_len = next(
        n["widgets_values"][2] for n in ltx["nodes"] if n.get("type") == "LTXVImgToVideo"
    )
    audio_len = next(
        n["widgets_values"][0]
        for n in ltx["nodes"]
        if n.get("type") == "LTXVEmptyLatentAudio"
    )
    assert wan_len == 120
    assert ltx_len == 120
    assert audio_len == 120
    for graph, prefix in ((wan, "ez_gosee_b1_s1_wan_video"), (ltx, "ez_gosee_b1_s1_ltx_video")):
        vhs = next(n for n in graph["nodes"] if n.get("type") == "VHS_VideoCombine")
        assert vhs["widgets_values"]["format"] == "video/h264-mp4"
        assert float(vhs["widgets_values"]["frame_rate"]) == 24
        assert vhs["widgets_values"]["save_output"] is True
        assert vhs["widgets_values"]["filename_prefix"] == prefix
        last = next(n for n in graph["nodes"] if n.get("title") == "Save last frame")
        assert last["widgets_values"][0] == "ez_gosee_b1_s1_last"
        batch = next(n for n in graph["nodes"] if n.get("type") == "ImageFromBatch")
        assert batch["widgets_values"][0] == 119
        load = next(n for n in graph["nodes"] if n.get("type") == "LoadImage")
        assert load["widgets_values"][0] == "example.png"


def test_no_long_latents_in_shorts() -> None:
    for path in _json_files():
        graph = json.loads(path.read_text(encoding="utf-8"))
        nodes = list(graph["nodes"])
        for sub in ((graph.get("definitions") or {}).get("subgraphs") or []):
            nodes.extend(sub.get("nodes") or [])
        for node in nodes:
            if node.get("type") not in LONG_LATENT_TYPES:
                continue
            values = node.get("widgets_values") or []
            length = int(values[2] if node["type"] != "LTXVEmptyLatentAudio" else values[0])
            assert length == 120, (path.name, node["type"], length)
            assert length < 241


def test_bible_graphs_are_one_click_klein_plus_ltx() -> None:
    for film, slug in FILMS:
        path = lab_json(BIBLES[film])
        graph = json.loads(path.read_text(encoding="utf-8"))
        text = path.read_text(encoding="utf-8")
        parsed = parse_shots_yaml(_path(film).read_text(encoding="utf-8"))
        assert "flux-2-klein-4b-fp8.safetensors" in text
        assert "qwen_3_4b.safetensors" in text
        assert "flux2-vae.safetensors" in text
        assert '"flux2"' in text
        assert "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors" in text
        printers = [n for n in graph["nodes"] if n.get("type") == "LTXVImgToVideo"]
        assert len(printers) == 18, (path.name, len(printers))
        assert all(n.get("mode") == 0 for n in printers)
        assert all(n["widgets_values"][0] == 1280 for n in printers)
        assert all(n["widgets_values"][1] == 704 for n in printers)
        assert all(n["widgets_values"][2] == 120 for n in printers)
        assert any(n.get("type") == "LTXVAudioVAEDecode" for n in graph["nodes"])
        assert any(n.get("type") == "EZUnloadModels" for n in graph["nodes"])
        concat = next(n for n in graph["nodes"] if n.get("type") == "EZFilmConcat")
        assert concat["widgets_values"][0] == film
        assert len(concat["widgets_values"]) >= 3
        title = (concat.get("title") or "").lower()
        assert "play" in title or "preview" in title or "download" in title
        if film == "go-see":
            assert concat["widgets_values"][2] == 8
            assert concat["pos"][0] < 400
        else:
            assert concat["widgets_values"][2] == 0
        identity = next(
            n
            for n in graph["nodes"]
            if n.get("type") == "SaveImage"
            and n["widgets_values"][0] == f"ez_{slug}_identity"
        )
        assert identity["widgets_values"][0] == f"ez_{slug}_identity"
        vhs_nodes = [n for n in graph["nodes"] if n.get("type") == "VHS_VideoCombine"]
        assert len(vhs_nodes) == 18
        prefixes = {n["widgets_values"]["filename_prefix"] for n in vhs_nodes}
        expected_prefixes = {f"{s['prefix']}_ltx_video" for s in parsed["shots"]}
        assert prefixes == expected_prefixes
        for node in vhs_nodes:
            assert node["widgets_values"]["save_output"] is True
            audio = next(i for i in node["inputs"] if i.get("name") == "audio")
            assert audio.get("link") is not None
        assert not any(n.get("type") == "LoadImage" for n in graph["nodes"])
        ltx_enh = [n for n in graph["nodes"] if n.get("type") == "EZLTXPromptEnhance"]
        assert len(ltx_enh) == 18
        klein_sampler = next(
            n
            for n in graph["nodes"]
            if n.get("type") == "KSampler" and n["widgets_values"][2] == 4
        )
        assert klein_sampler["widgets_values"][0] == 42
        assert klein_sampler["widgets_values"][3] == 1.0
        enhance = next(n for n in graph["nodes"] if n.get("type") == "EZKleinPromptEnhance")
        assert enhance["widgets_values"][0] == parsed["identity"]
        if film == "go-see":
            assert all(n["widgets_values"][1] is False for n in ltx_enh)
            assert enhance["widgets_values"][1] is False
            assert enhance["widgets_values"][2] == "t2i"
        else:
            assert all(n["widgets_values"][1] is True for n in ltx_enh)
            assert enhance["widgets_values"][1] is True
            assert enhance["widgets_values"][2] == "identity"
        ltx_pos = [
            n
            for n in graph["nodes"]
            if n.get("type") == "CLIPTextEncode" and str(n.get("title") or "").endswith("LTX I2V")
        ]
        assert len(ltx_pos) == 18
        baked = {n["widgets_values"][0] for n in ltx_pos}
        expected_ltx = {s["ltx_i2v"] for s in parsed["shots"]}
        assert baked == expected_ltx
        latent = next(n for n in graph["nodes"] if n.get("type") == "EmptyFlux2LatentImage")
        assert latent["widgets_values"][0] == 1280
        assert latent["widgets_values"][1] == 704
        assert latent["widgets_values"][2] == 1
        last_saves = [
            n
            for n in graph["nodes"]
            if n.get("type") == "SaveImage" and n.get("title") == "Save last frame"
        ]
        assert len(last_saves) == 18
        note = next(n for n in graph["nodes"] if n.get("type") == "Note")
        body = note["widgets_values"][0]
        assert "Queue once" in body or "Queue **once**" in body
        assert "concat-shots.sh" in body
        assert "already on disk" in body
        assert f"ez_{slug}_90s.mp4" in body
        mmap = next(n for n in graph["nodes"] if n.get("type") == "MarkdownNote")
        table = mmap["widgets_values"][0]
        assert "120" in table
        assert "90" in table

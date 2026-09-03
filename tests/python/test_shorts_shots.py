"""Shot-bible contract for US-safe 90s shorts.

Hermetic: stdlib only. YAML subset parsed without PyYAML.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
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


def _path(film: str) -> Path:
    return SHORTS / f"{film}.shots.yaml"


def _load_meta(text: str) -> dict[str, str]:
    meta = {}
    for key in ("film", "slug", "frames", "fps", "duration_s", "beats", "shots_per_beat", "total_shots", "publish_cap_s"):
        m = re.search(rf"^{key}:\s*(.+)$", text, re.M)
        assert m, key
        meta[key] = m.group(1).strip()
    return meta


def _load_shots(text: str) -> list[dict[str, str]]:
    blocks = re.split(r"\n  - beat:", text)[1:]
    shots = []
    for block in blocks:
        body = "beat:" + block
        def field(name: str) -> str:
            m = re.search(rf"^\s*{name}:\s*(.+)$", body, re.M)
            assert m, name
            return m.group(1).strip()
        shots.append(
            {
                "beat": field("beat"),
                "shot": field("shot"),
                "prefix": field("prefix"),
                "load_from": field("load_from"),
                "motion": body,
                "audio": body,
            }
        )
    return shots


def test_three_shot_bibles_exist() -> None:
    for film, _slug in FILMS:
        assert _path(film).is_file(), film


def test_eighteen_shots_and_chain() -> None:
    for film, slug in FILMS:
        text = _path(film).read_text(encoding="utf-8")
        meta = _load_meta(text)
        assert meta["film"] == film
        assert meta["slug"] == slug
        assert meta["frames"] == "120"
        assert meta["fps"] == "24"
        assert meta["duration_s"] == "5.00"
        assert meta["beats"] == "6"
        assert meta["shots_per_beat"] == "3"
        assert meta["total_shots"] == "18"
        assert meta["publish_cap_s"] == "90.00"
        shots = _load_shots(text)
        assert len(shots) == 18, (film, len(shots))
        prefixes = [s["prefix"] for s in shots]
        assert len(set(prefixes)) == 18
        assert shots[0]["load_from"] == "example.png"
        for i, s in enumerate(shots):
            assert s["prefix"] == f"ez_{slug}_b{s['beat']}_s{s['shot']}"
            if i:
                assert s["load_from"] == f"{shots[i - 1]['prefix']}_last"
        assert "identity_look:" in text
        assert "No score" in text or "no score" in text


def test_shorts_yaml_has_no_banned_models() -> None:
    for film, _slug in FILMS:
        text = _path(film).read_text(encoding="utf-8")
        for needle in BANNED:
            assert needle not in text, (film, needle)


def test_creative_locks() -> None:
    go = _path("go-see").read_text(encoding="utf-8")
    assert "olive windbreaker" in go
    assert "worn black gloves" in go
    assert "First-person" in go or "first-person" in go
    assert "running" in go or "footfall" in go
    for needle in ("vault", "barrel-roll", "parkour", "Parkour"):
        assert needle not in go, needle
    here = _path("still-here").read_text(encoding="utf-8")
    assert "ceramic mug" in here
    assert "two-note" in here or "invented" in here
    yard = _path("switchyard").read_text(encoding="utf-8")
    assert "railroad" in yard
    assert "boxcar" in yard or "boxcars" in yard


def _json_files() -> list[Path]:
    files = sorted(SHORTS.glob("*-lab-example.json"))
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
        assert len(clips) >= 2, path.name
        lab_note = graph.get("extra", {}).get("lab_note")
        assert isinstance(lab_note, str) and lab_note.strip()


def test_shot_graphs_are_five_second_i2v() -> None:
    wan = json.loads((ROOT / "workflows" / "wan-i2v-shot-lab-example.json").read_text(encoding="utf-8"))
    ltx = json.loads((ROOT / "workflows" / "ltx-i2v-shot-lab-example.json").read_text(encoding="utf-8"))
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
        for node in graph["nodes"]:
            if node.get("type") not in LONG_LATENT_TYPES:
                continue
            values = node.get("widgets_values") or []
            length = int(values[2] if node["type"] != "LTXVEmptyLatentAudio" else values[0])
            assert length == 120, (path.name, node["type"], length)
            assert length < 241


BIBLES = {
    "go-see": "film-go-see-90s-run-lab-example.json",
    "still-here": "film-still-here-90s-lab-example.json",
    "switchyard": "film-switchyard-90s-lab-example.json",
}


def test_bible_graphs_are_unified_klein_plus_ltx() -> None:
    for film, slug in FILMS:
        path = SHORTS / BIBLES[film]
        graph = json.loads(path.read_text(encoding="utf-8"))
        text = path.read_text(encoding="utf-8")
        assert "flux-2-klein-4b-fp8.safetensors" in text
        assert "qwen_3_4b.safetensors" in text
        assert "flux2-vae.safetensors" in text
        assert '"flux2"' in text
        assert "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors" in text
        assert any(n.get("type") == "LTXVImgToVideo" for n in graph["nodes"])
        assert any(n.get("type") == "LTXVAudioVAEDecode" for n in graph["nodes"])
        assert any(n.get("type") == "VHS_VideoCombine" for n in graph["nodes"])
        identity = next(
            n
            for n in graph["nodes"]
            if n.get("type") == "SaveImage"
            and n["widgets_values"][0] == f"ez_{slug}_identity"
        )
        assert identity["widgets_values"][0] == f"ez_{slug}_identity"
        vhs = next(n for n in graph["nodes"] if n.get("type") == "VHS_VideoCombine")
        assert vhs["widgets_values"]["filename_prefix"] == f"ez_{slug}_b1_s1_ltx_video"
        assert vhs["widgets_values"]["save_output"] is True
        audio = next(i for i in vhs["inputs"] if i.get("name") == "audio")
        assert audio.get("link") is not None
        # LTX print starts bypassed so first Queue is identity-only
        assert any(
            n.get("type") == "LTXVImgToVideo" and n.get("mode") == 4 for n in graph["nodes"]
        )
        mmap = next(n for n in graph["nodes"] if n.get("type") == "MarkdownNote")
        body = mmap["widgets_values"][0]
        yaml_text = _path(film).read_text(encoding="utf-8")
        for shot in _load_shots(yaml_text):
            assert shot["prefix"] in body
            assert shot["load_from"] in body
            # Audio lines must be paste-ready (not empty)
            assert f"- Audio:" in body
        audio_lines = [
            line for line in body.splitlines() if line.startswith("- Audio:")
        ]
        assert len(audio_lines) == 18, (film, len(audio_lines))
        assert all(len(line) > 12 for line in audio_lines)
        assert "No score" in body or "no score" in body
        assert "120" in body
        assert "90.00" in body or "90s" in body
        latent = next(n for n in graph["nodes"] if n.get("type") == "EmptyFlux2LatentImage")
        assert latent["widgets_values"][0] == 1280
        assert latent["widgets_values"][1] == 720
        ltx_len = next(
            n["widgets_values"][2]
            for n in graph["nodes"]
            if n.get("type") == "LTXVImgToVideo"
        )
        assert ltx_len == 120

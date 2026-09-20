"""Creator toolkit lab workflow contracts."""

from __future__ import annotations

import json
from pathlib import Path

from ez_music.diss_examples import DISS_EXAMPLES
from ez_music.edm_examples import EDM_EXAMPLES

from _lab_paths import WF, lab_json
from _stamp_app_mode import STAMP_SPECS, linear_input_node_id, suite_json_paths

ROOT = Path(__file__).resolve().parents[2]

CREATORS = (
    ("stills/shorts-still", "ez_shorts_still", False),
    ("motion/silent/shorts-still-5s", "ez_shorts_wan_video", True),
    ("motion/av/shorts-still-10s", "ez_shorts_ltx_video", True),
    ("stills/thumbnail", "ez_thumbnail", False),
    ("stills/product-packshot", "ez_packshot", False),
    ("stills/before-after", "ez_before", False),
    ("stills/style-lock", "ez_style_01", False),
    ("motion/loops/bumper-loop", "ez_bumper", True),
    ("motion/av/broll-ambient", "ez_broll_video", True),
    ("stills/storyboard-6up", "ez_board_01", False),
    ("stills/endcard-cta", "ez_endcard", False),
    ("stills/quote-bg", "ez_quote_bg", False),
    ("stills/open-graph", "ez_og", False),
    ("stills/podcast-cover", "ez_podcast", False),
    ("stills/banner-wide", "ez_banner", False),
    ("stills/instagram-square", "ez_ig_square", False),
    ("stills/hook-still", "ez_hook_still", False),
    ("stills/lower-third-bg", "ez_lowerthird", False),
    ("stills/food-tabletop", "ez_tabletop", False),
    ("stills/lighting-trio", "ez_light_01", False),
    ("stills/time-of-day", "ez_tod_01", False),
    ("stills/camera-angles", "ez_angle_wide", False),
    ("stills/color-moods", "ez_mood_01", False),
    ("motion/silent/orbit-still-5s", "ez_orbit_video", True),
    ("motion/silent/push-in-still-5s", "ez_pushin_video", True),
    ("motion/silent/parallax-still-5s", "ez_parallax_video", True),
    ("motion/loops/sticker-loop", "ez_sticker", True),
    ("motion/av/weather-broll", "ez_weather_video", True),
    ("motion/av/interior-ambience", "ez_interior_video", True),
    ("motion/av/hook-av", "ez_hook_video", True),
    ("motion/av/dialogue-10s", "ez_ltx_dialogue", True),
    ("motion/av/multishot-10s", "ez_ltx_multishot", True),
    ("motion/av/product-hero", "ez_ltx_product", True),
    ("motion/av/first-last-10s", "ez_ltx_flf", True),
    ("motion/av/audio-to-video-10s", "ez_ltx_a2v", True),
    ("audio/podcast/two-host-episode", "ez_podcast_ep", False),
    ("audio/podcast/radio-drama", "ez_radio_ep", False),
    ("audio/podcast/learn-episode", "ez_learn_ep", False),
    ("audio/music/rap-draft", "ez_rap_draft", False),
    ("audio/music/rap-full", "ez_rap_full", False),
) + tuple((ex["stem"], ex["prefix"], False) for ex in DISS_EXAMPLES) + tuple(
    (ex["stem"], ex["prefix"], False) for ex in EDM_EXAMPLES
)

BANNED = ("MiniMax", "MiniMaxH3", "minimax_h3", "klein-9b", "FLUX.2-dev")


def test_creator_toolkit_files_and_prefixes() -> None:
    for stem, prefix, is_video in CREATORS:
        path = lab_json(stem)
        assert path.is_file(), stem
        text = path.read_text(encoding="utf-8")
        for needle in BANNED:
            assert needle not in text, (stem, needle)
        graph = json.loads(text)
        assert graph.get("id") == Path(stem).name
        rel = graph.get("extra", {}).get("lab_rel")
        assert rel == stem or str(rel).endswith("/" + Path(stem).name)
        assert graph.get("extra", {}).get("lab_note", "").strip()
        assert graph.get("extra", {}).get("lab_description", "").strip()
        blob = json.dumps(graph)
        assert prefix in blob, (stem, prefix)
        vhs = [n for n in graph["nodes"] if n.get("type") == "VHS_VideoCombine"]
        if is_video:
            assert len(vhs) >= 1, stem
            for node in vhs:
                assert node["widgets_values"]["save_output"] is True
                assert str(node["widgets_values"]["filename_prefix"]).startswith("ez_")
                assert "preview" in (node.get("title") or "").lower()
        if any(n.get("type") == "LTXVSeparateAVLatent" for n in graph["nodes"]):
            has_decode = any(n.get("type") == "LTXVAudioVAEDecode" for n in graph["nodes"])
            has_load_audio = any(n.get("type") == "LoadAudio" for n in graph["nodes"])
            assert has_decode or has_load_audio, stem
            for node in vhs:
                audio = next(i for i in node["inputs"] if i.get("name") == "audio")
                assert audio.get("link") is not None, stem


def test_vertical_shorts_sizes() -> None:
    still = json.loads(lab_json("stills/shorts-still.json").read_text(encoding="utf-8"))
    latent = next(n for n in still["nodes"] if n.get("type") == "EmptyFlux2LatentImage")
    assert latent["widgets_values"][0] == 432
    assert latent["widgets_values"][1] == 768
    wan = json.loads(lab_json("motion/silent/shorts-still-5s.json").read_text(encoding="utf-8"))
    wlat = next(n for n in wan["nodes"] if n.get("type") == "Wan22ImageToVideoLatent")
    assert wlat["widgets_values"][0] == 480
    assert wlat["widgets_values"][1] == 832


def test_before_after_and_storyboard_prefixes() -> None:
    before = json.loads(lab_json("stills/before-after.json").read_text(encoding="utf-8"))
    prefixes = {
        n["widgets_values"][0]
        for n in before["nodes"]
        if n.get("type") == "SaveImage"
    }
    assert "ez_before" in prefixes
    assert "ez_after" in prefixes
    board = json.loads(lab_json("stills/storyboard-6up.json").read_text(encoding="utf-8"))
    board_prefixes = {
        n["widgets_values"][0]
        for n in board["nodes"]
        if n.get("type") == "SaveImage"
    }
    assert board_prefixes == {f"ez_board_{i:02d}" for i in range(1, 7)}


def _save_prefixes(stem: str) -> set[str]:
    graph = json.loads(lab_json(stem).read_text(encoding="utf-8"))
    return {
        n["widgets_values"][0]
        for n in graph["nodes"]
        if n.get("type") == "SaveImage"
    }


def test_hook_still_is_vertical() -> None:
    still = json.loads(lab_json("stills/hook-still.json").read_text(encoding="utf-8"))
    latent = next(n for n in still["nodes"] if n.get("type") == "EmptyFlux2LatentImage")
    assert latent["widgets_values"][0] == 432
    assert latent["widgets_values"][1] == 768


def _identity_plate_contract(stem: str, prefixes: set[str], persist: str = "state") -> None:
    graph = json.loads(lab_json(stem).read_text(encoding="utf-8"))
    encode_n = sum(1 for n in graph["nodes"] if n.get("type") == "VAEEncode")
    ref_n = sum(1 for n in graph["nodes"] if n.get("type") == "ReferenceLatent")
    enhance = [n for n in graph["nodes"] if n.get("type") == "EZKleinPromptEnhance"]
    assert enhance
    ident = next(
        (n for n in enhance if "IDENTITY" in str(n.get("title") or "").upper()),
        enhance[0],
    )
    values = ident["widgets_values"]
    if len(values) >= 7:
        assert values[2] is True
        assert values[3] in ("identity", "t2i")
        assert values[5] == "none"
    else:
        assert values[1] is True
        assert values[2] in ("identity", "t2i")
        assert values[-1] == "none"
    joins = [n for n in graph["nodes"] if n.get("type") == "EZPromptJoin"]
    assert len(joins) == len(prefixes)
    for join in joins:
        values = join["widgets_values"]
        if stem == "stills/before-after":
            assert values[1].strip(), stem
        else:
            assert values[1].strip() == "", stem
        assert values[2] == persist, stem
    seeds = {
        n["widgets_values"][0]
        for n in graph["nodes"]
        if n.get("type") == "KSampler"
    }
    assert seeds == {42}
    saves = {
        n["widgets_values"][0]
        for n in graph["nodes"]
        if n.get("type") == "SaveImage"
    }
    assert saves == prefixes
    by_id = {n["id"]: n for n in graph["nodes"]}
    incoming: dict[tuple[int, int], list] = {}
    for link in graph["links"]:
        incoming.setdefault((link[3], link[4]), []).append(link)
    samplers = sorted(
        (n for n in graph["nodes"] if n.get("type") == "KSampler"),
        key=lambda n: n["pos"][1],
    )
    if persist == "state":
        assert encode_n == 1, stem
        assert ref_n >= 1, stem
        for i, ks in enumerate(samplers):
            pos_src = by_id[incoming[(ks["id"], 1)][0][1]]["type"]
            if i == 0:
                assert pos_src == "CLIPTextEncode"
            else:
                assert pos_src == "ReferenceLatent"
    else:
        assert encode_n == 0, stem
        assert ref_n == 0, stem
        for ks in samplers:
            pos_src = by_id[incoming[(ks["id"], 1)][0][1]]["type"]
            assert pos_src == "CLIPTextEncode", stem


def test_pack_v2_prefixes() -> None:
    assert _save_prefixes("stills/lighting-trio") == {
        "ez_light_01",
        "ez_light_02",
        "ez_light_03",
    }
    assert _save_prefixes("stills/time-of-day") == {
        f"ez_tod_{i:02d}" for i in range(1, 5)
    }
    assert _save_prefixes("stills/camera-angles") == {
        "ez_angle_wide",
        "ez_angle_med",
        "ez_angle_close",
    }
    assert _save_prefixes("stills/color-moods") == {
        f"ez_mood_{i:02d}" for i in range(1, 5)
    }
    _identity_plate_contract(
        "stills/lighting-trio",
        {"ez_light_01", "ez_light_02", "ez_light_03"},
    )
    _identity_plate_contract(
        "stills/time-of-day",
        {f"ez_tod_{i:02d}" for i in range(1, 5)},
    )
    _identity_plate_contract(
        "stills/camera-angles",
        {"ez_angle_wide", "ez_angle_med", "ez_angle_close"},
        persist="view",
    )
    _identity_plate_contract(
        "stills/color-moods",
        {f"ez_mood_{i:02d}" for i in range(1, 5)},
    )
    _identity_plate_contract(
        "stills/before-after",
        {"ez_before", "ez_after"},
    )
    _identity_plate_contract(
        "stills/style-lock",
        {f"ez_style_{i:02d}" for i in range(1, 5)},
        persist="view",
    )
    _identity_plate_contract(
        "stills/storyboard-6up",
        {f"ez_board_{i:02d}" for i in range(1, 7)},
        persist="view",
    )


def test_suite_graphs_have_app_mode_and_resolving_linear_data() -> None:
    paths = suite_json_paths(WF)
    assert len(paths) == len(STAMP_SPECS), (
        sorted(STAMP_SPECS) ,
        sorted(p.stem for p in paths),
    )
    for path in paths:
        graph = json.loads(path.read_text(encoding="utf-8"))
        extra = graph.get("extra") or {}
        mode = extra.get("lab_app_mode") or {}
        assert mode.get("enabled") is True, path.name
        linear = extra.get("linearData") or {}
        inputs = linear.get("inputs") or []
        outputs = linear.get("outputs") or []
        assert inputs, path.name
        assert outputs, path.name
        by_id = {int(n["id"]): n for n in graph["nodes"]}
        for entry in inputs:
            node_id = linear_input_node_id(entry)
            widget_name = entry[1]
            assert isinstance(entry[0], int), (path.name, entry[0])
            assert node_id in by_id, (path.name, entry[0])
            assert widget_name == entry[1]
        for node_id in outputs:
            assert int(node_id) in by_id, (path.name, node_id)


PACK_PLATES = (
    ("ez_pack_thumb", 1280, 720),
    ("ez_pack_ig", 1024, 1024),
    ("ez_pack_portrait", 1024, 1280),
    ("ez_pack_shorts", 432, 768),
    ("ez_pack_og", 1216, 640),
    ("ez_pack_banner", 1536, 512),
)


def test_platform_pack_prefixes_sizes_and_independent_t2i() -> None:
    graph = json.loads(lab_json("stills/platform-pack.json").read_text(encoding="utf-8"))
    assert graph["id"] == "platform-pack"
    assert graph["extra"].get("lab_rel") == "stills/platform-pack"
    assert graph["extra"]["lab_app_mode"]["lane"] == "produce"
    assert graph["extra"]["lab_app_mode"]["occupancy"] == "klein"
    assert graph["extra"]["lab_app_mode"]["enhance_off_identity"] is False
    assert not any(n.get("type") == "ReferenceLatent" for n in graph["nodes"])
    enhance = next(n for n in graph["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    values = enhance["widgets_values"]
    flag = values[2] if len(values) >= 7 else values[1]
    assert flag is True
    saves = {
        n["widgets_values"][0]: n
        for n in graph["nodes"]
        if n.get("type") == "SaveImage"
    }
    latents = [n for n in graph["nodes"] if n.get("type") == "EmptyFlux2LatentImage"]
    assert len(latents) == 6
    by_size = {(int(n["widgets_values"][0]), int(n["widgets_values"][1])) for n in latents}
    for prefix, width, height in PACK_PLATES:
        assert prefix in saves, prefix
        assert (width, height) in by_size, (prefix, width, height)
    seeds = {n["widgets_values"][0] for n in graph["nodes"] if n.get("type") == "KSampler"}
    assert seeds == {42}
    blob = json.dumps(graph)
    for needle in BANNED:
        assert needle not in blob
    assert "241" not in blob


def test_only_daily_still_exposes_unet_in_app_inputs() -> None:
    unet_stems = []
    for path in suite_json_paths(WF):
        graph = json.loads(path.read_text(encoding="utf-8"))
        linear = graph.get("extra", {}).get("linearData") or {}
        hits = [entry for entry in linear.get("inputs") or [] if entry[1] == "unet_name"]
        if hits:
            unet_stems.append(graph["id"])
    assert set(unet_stems) == {"still-daily", "still-studio", "image-studio"}


def test_app_inputs_are_prompt_first_and_hide_join_shots() -> None:
    latent_stems = []
    for path in suite_json_paths(WF):
        graph = json.loads(path.read_text(encoding="utf-8"))
        linear = graph.get("extra", {}).get("linearData") or {}
        names = [entry[1] for entry in linear.get("inputs") or []]
        assert "shot" not in names, graph["id"]
        assert "inventory" not in names, graph["id"]
        creator = next(
            (
                name
                for name in names
                if name in {
                    "sample",
                    "prompt",
                    "subject",
                    "brief",
                    "tags",
                    "lyrics",
                    "value",
                    "slug",
                    "plate",
                    "artist",
                    "album",
                }
            ),
            None,
        )
        assert creator is not None, graph["id"]
        if "sample" in names and "prompt" in names:
            assert names.index("sample") < names.index("prompt"), graph["id"]
        if "seed" in names:
            assert names.index(creator) < names.index("seed"), graph["id"]
        if "width" in names:
            assert "format" in names, graph["id"]
            latent_stems.append(graph["id"])
        if "unet_name" in names:
            assert graph["id"] in {"still-daily", "still-studio", "image-studio"}
    assert latent_stems
    assert "still-studio" in latent_stems
    assert "still-draft" in latent_stems


def _app_labels(graph: dict) -> list[str]:
    labels: list[str] = []
    for entry in (graph.get("extra") or {}).get("linearData", {}).get("inputs") or []:
        name = entry[1]
        config = entry[2] if len(entry) > 2 else {}
        labels.append((config or {}).get("label") or name)
    return labels


def _enhance_mode(graph: dict) -> str:
    for node in graph.get("nodes") or []:
        ntype = node.get("type")
        values = list(node.get("widgets_values") or [])
        if ntype in (
            "EZKleinPromptEnhance",
            "EZWanPromptEnhance",
            "EZLTXPromptEnhance",
        ):
            idx = 3 if len(values) >= 7 else 2
            return str(values[idx]) if len(values) > idx else ""
        if ntype == "EZAceStepPromptEnhance":
            idx = 4 if len(values) >= 6 else 3
            return str(values[idx]) if len(values) > idx else ""
    return ""


def test_app_input_labels_are_unique_and_i2v_hides_noop_style() -> None:
    dead_image = []
    style_on_i2v = []
    for path in suite_json_paths(WF):
        graph = json.loads(path.read_text(encoding="utf-8"))
        extra = graph.get("extra") or {}
        if extra.get("lab_app_mode", {}).get("default_view") != "app":
            continue
        labels = _app_labels(graph)
        assert labels, graph["id"]
        assert len(labels) == len(set(labels)), (graph["id"], labels)
        linear = extra.get("linearData") or {}
        names = [entry[1] for entry in linear.get("inputs") or []]
        by_id = {int(n["id"]): n for n in graph["nodes"]}
        for entry in linear.get("inputs") or []:
            if entry[1] != "image":
                continue
            node = by_id[linear_input_node_id(entry)]
            linked = any(
                str(out.get("name") or "").upper() == "IMAGE" and out.get("links")
                for out in node.get("outputs") or []
            )
            live = int(node.get("mode") or 0) == 0
            if not (linked and live):
                dead_image.append(graph["id"])
        if (
            graph["id"] != "inspire/prompt-forge"
            and _enhance_mode(graph) in {"i2v", "flf", "vace"}
            and "style" in names
        ):
            style_on_i2v.append(graph["id"])
        assert "backend" not in names, graph["id"]
        assert "speaker_a_ref" not in names, graph["id"]
    assert dead_image == []
    assert style_on_i2v == []


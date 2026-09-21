"""Hermetic tests for EZModelCheck, disk scan, and graph stamp."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from _lab_paths import lab_graph_paths
from _wire_model_check import (
    CHECK_DEFAULT,
    CHECK_TYPE,
    CHECK_WIDGET,
    ensure_model_check_node,
    find_model_check_node,
    stamp_all_model_check,
)
from _wire_quality import QUALITY_TYPE, find_quality_node

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_quality.check import (  # noqa: E402
    ACE_TURBO,
    CLIP_4B,
    CLIP_8B,
    CLIP_MISTRAL,
    CMD_DOWNLOAD_MODELS,
    CMD_DREAMX,
    CMD_DUB,
    CMD_IMAGE_9B,
    CMD_IMAGE_9B_BASE,
    CMD_IMAGE_FLUX2_DEV,
    CMD_LLM_35B,
    CMD_LLM_DESCRIBE,
    CMD_LONGCAT,
    CMD_LTX_ICLORA,
    CMD_MUSIC,
    CMD_PODCAST,
    CMD_RESTORE,
    CMD_TRELLIS,
    CMD_WAN_FUN,
    CMD_WAN_S2V,
    CMD_WAN_VACE,
    DREAMX_WEIGHTS,
    FLUX2_DEV,
    KLEIN_9B,
    KLEIN_9B_BASE,
    KLEIN_DISTILLED,
    LLM_35B,
    LLM_GGUF,
    LTX_ICLORA,
    QUALITY_FREE_COMMERCIAL,
    QUALITY_MAX,
    QUALITY_ULTRA,
    SEEDVR2,
    STATUS_DEFAULT,
    CheckHints,
    FileSpec,
    SUB_CLIP,
    SUB_UNET,
    WAN_5B,
    _as_bool,
    _as_str_tuple,
    _folder_paths_has,
    _iter_basenames,
    _loader_name,
    command_for_filename,
    format_report,
    hints_from_args,
    hints_from_graph,
    inspect_file,
    models_roots,
    requirements_for,
    run_check,
    scan,
)
from ez_quality.nodes import EZModelCheck, EZQuality  # noqa: E402
from ez_quality.routes import handle_check, register_routes, request_json  # noqa: E402


def _touch(path: Path, data: bytes = b"x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _comfy(root: Path, subdir: str, name: str, data: bytes = b"x") -> Path:
    path = root / "comfy" / subdir / name
    _touch(path, data)
    return path


def test_node_contract() -> None:
    assert EZModelCheck.OUTPUT_NODE is False
    assert EZModelCheck.RETURN_TYPES == ()
    assert EZModelCheck.FUNCTION == "idle"
    types = EZModelCheck.INPUT_TYPES()
    assert types["required"]["status"][1]["default"] == STATUS_DEFAULT
    assert EZModelCheck().idle("ignored") == ()
    from ez_quality import nodes as quality_nodes

    assert quality_nodes.NODE_CLASS_MAPPINGS["EZModelCheck"] is EZModelCheck
    assert quality_nodes.NODE_DISPLAY_NAME_MAPPINGS["EZModelCheck"] == "Check models"
    assert quality_nodes.NODE_CLASS_MAPPINGS["EZQuality"] is EZQuality


def test_as_bool_and_str_tuple() -> None:
    assert _as_bool(None) is False
    assert _as_bool(None, default=True) is True
    assert _as_bool(True) is True
    assert _as_bool(0) is False
    assert _as_bool(2) is True
    assert _as_bool("True") is True
    assert _as_bool("off") is False
    assert _as_bool("") is False
    assert _as_bool("maybe") is False
    assert _as_str_tuple("a") == ("a",)
    assert _as_str_tuple("  ") == ()
    assert _as_str_tuple(["a", "", "a", "b"]) == ("a", "b")
    assert _as_str_tuple(3) == ()


def test_loader_name_shapes() -> None:
    assert _loader_name({"unet_name": "a.safetensors"}) == "a.safetensors"
    assert _loader_name({"ckpt_name": "b.safetensors"}) == "b.safetensors"
    assert _loader_name({"lora_name": "c.safetensors"}) == "c.safetensors"
    assert _loader_name({"vae_name": "d.safetensors"}) == "d.safetensors"
    assert _loader_name({}) == ""
    assert _loader_name(["file.safetensors", "default"]) == "file.safetensors"
    assert _loader_name([True]) == ""
    assert _loader_name([]) == ""
    assert _loader_name(None) == ""


def test_command_for_filename_needles() -> None:
    assert command_for_filename(KLEIN_DISTILLED) == CMD_DOWNLOAD_MODELS
    assert command_for_filename(LTX_ICLORA) == CMD_LTX_ICLORA
    assert command_for_filename("wan_fun_inp.safetensors") == CMD_WAN_FUN
    assert command_for_filename("wan_vace.safetensors") == CMD_WAN_VACE
    assert command_for_filename("wan_s2v.safetensors") == CMD_WAN_S2V
    assert command_for_filename(KLEIN_9B) == CMD_IMAGE_9B
    assert command_for_filename(KLEIN_9B_BASE) == CMD_IMAGE_9B_BASE
    assert command_for_filename(FLUX2_DEV) == CMD_IMAGE_FLUX2_DEV
    assert command_for_filename(CLIP_8B) == CMD_IMAGE_9B
    assert command_for_filename(ACE_TURBO) == CMD_MUSIC
    assert command_for_filename("trellis_2_int8_convrot.safetensors") == CMD_TRELLIS
    assert command_for_filename("Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf") == CMD_LLM_DESCRIBE
    assert command_for_filename(LLM_35B) == CMD_LLM_35B
    assert command_for_filename(LLM_GGUF) == CMD_DOWNLOAD_MODELS
    assert command_for_filename("kokoro-v1.0.onnx") == CMD_PODCAST
    assert command_for_filename("t3_mtl23ls_v3.safetensors") == CMD_DUB
    assert command_for_filename(SEEDVR2) == CMD_RESTORE
    assert command_for_filename("longcat_video.safetensors") == CMD_LONGCAT
    assert command_for_filename(DREAMX_WEIGHTS) == CMD_DREAMX
    assert command_for_filename("mystery.bin") == CMD_DOWNLOAD_MODELS


def test_coverage_gaps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODELS_ROOT", "/models")
    monkeypatch.delenv("MODELS_DIR", raising=False)
    roots = models_roots()
    assert roots[0] == Path("/models")
    assert roots.count(Path("/models")) == 1
    empty_type = hints_from_graph({"nodes": [{"type": "", "widgets_values": []}]})
    assert empty_type.types == ()

    _comfy(tmp_path, "diffusion_models", KLEIN_DISTILLED)
    _comfy(tmp_path, "text_encoders", CLIP_4B)
    _comfy(tmp_path, "vae", "flux2-vae.safetensors")
    _comfy(tmp_path, "diffusion_models", KLEIN_9B)
    _comfy(tmp_path, "diffusion_models", "flux-2-klein-9b-nvfp4.safetensors")
    _comfy(tmp_path, "text_encoders", CLIP_8B)
    both = run_check(
        {"occupancy": "klein", "quality": QUALITY_ULTRA, "unets": [KLEIN_DISTILLED]},
        roots=(tmp_path,),
    )
    assert both["ok"] is True
    dup_missing = run_check(
        {"occupancy": "klein", "unets": [KLEIN_DISTILLED]},
        roots=(tmp_path / "empty",),
    )
    assert dup_missing["ok"] is False
    (tmp_path / "comfy" / "diffusion_models" / KLEIN_9B).unlink()
    (tmp_path / "comfy" / "diffusion_models" / "flux-2-klein-9b-nvfp4.safetensors").unlink()
    _comfy(tmp_path, "diffusion_models", KLEIN_DISTILLED)
    _comfy(tmp_path, "diffusion_models", FLUX2_DEV)
    _comfy(tmp_path, "text_encoders", CLIP_MISTRAL)
    max_ok = run_check(
        {"occupancy": "klein", "quality": QUALITY_MAX},
        roots=(tmp_path,),
    )
    assert max_ok["ok"] is True
    hidden = tmp_path / "comfy" / "diffusion_models" / ".hidden"
    hidden.write_bytes(b"x")
    names = _iter_basenames(tmp_path, "diffusion_models")
    assert ".hidden" not in names
    assert _iter_basenames(tmp_path, "missing-subdir") == []
    assert _as_bool("yes") is True
    assert _as_bool("1") is True


def test_models_roots_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MODELS_ROOT", str(tmp_path / "root"))
    monkeypatch.setenv("MODELS_DIR", str(tmp_path / "root"))
    roots = models_roots()
    assert roots[0] == tmp_path / "root"
    assert Path("/models") in roots
    assert Path("/mnt/models") in roots
    monkeypatch.delenv("MODELS_ROOT")
    monkeypatch.delenv("MODELS_DIR")
    fallback = models_roots()
    assert fallback[0] == Path("/models")


def test_klein_lab_ready_and_ultra_missing(tmp_path: Path) -> None:
    _comfy(tmp_path, "diffusion_models", KLEIN_DISTILLED)
    _comfy(tmp_path, "text_encoders", CLIP_4B)
    _comfy(tmp_path, "vae", "flux2-vae.safetensors")
    _comfy(tmp_path, "llm", LLM_GGUF)
    lab = run_check(
        {
            "lab_rel": "stills/still-draft",
            "occupancy": "klein",
            "quality": "lab",
            "enhance_on": True,
        },
        roots=(tmp_path,),
    )
    assert lab["ok"] is True
    assert "Ready for stills/still-draft @ lab" in lab["message"]
    ultra = run_check(
        {
            "lab_rel": "stills/still-draft",
            "occupancy": "klein",
            "quality": QUALITY_ULTRA,
            "enhance_on": False,
        },
        roots=(tmp_path,),
    )
    assert ultra["ok"] is False
    assert CMD_IMAGE_9B in ultra["commands"]
    assert any(KLEIN_9B.split(".")[0] in row["name"] or KLEIN_9B in row["name"] for row in ultra["missing"])


def test_klein_max_clip_and_free_commercial(tmp_path: Path) -> None:
    _comfy(tmp_path, "diffusion_models", KLEIN_DISTILLED)
    _comfy(tmp_path, "text_encoders", CLIP_4B)
    _comfy(tmp_path, "vae", "full_encoder_small_decoder.safetensors")
    _comfy(tmp_path, "diffusion_models", KLEIN_9B_BASE)
    missing_clip = run_check(
        {"occupancy": "klein", "quality": QUALITY_MAX},
        roots=(tmp_path,),
    )
    assert missing_clip["ok"] is False
    assert CLIP_8B in [row["name"] for row in missing_clip["missing"]]
    _comfy(tmp_path, "text_encoders", CLIP_8B)
    ready = run_check(
        {"occupancy": "klein", "quality": QUALITY_MAX},
        roots=(tmp_path,),
    )
    assert ready["ok"] is True
    (tmp_path / "comfy" / "diffusion_models" / KLEIN_9B_BASE).unlink()
    _comfy(tmp_path, "diffusion_models", FLUX2_DEV)
    miss_mistral = run_check(
        {"occupancy": "klein", "quality": QUALITY_MAX},
        roots=(tmp_path,),
    )
    assert CLIP_MISTRAL in [row["name"] for row in miss_mistral["missing"]]
    _comfy(tmp_path, "text_encoders", CLIP_MISTRAL)
    free = run_check(
        {"occupancy": "klein", "quality": QUALITY_FREE_COMMERCIAL},
        roots=(tmp_path,),
    )
    assert free["ok"] is True


def test_occupancy_packs_and_extras(tmp_path: Path) -> None:
    wan = requirements_for(CheckHints(occupancy="wan"))
    assert any(need.pack == "wan-ti2v-5b" for need in wan)
    ltx = requirements_for(CheckHints(occupancy="ltx"))
    assert any(need.pack == "ltx-2.5" for need in ltx)
    film = requirements_for(CheckHints(occupancy="film"))
    assert any(need.pack == "ltx-2.5" for need in film)
    audio = requirements_for(CheckHints(occupancy="audio"))
    assert any(need.pack == "music-turbo" for need in audio)
    trellis = requirements_for(CheckHints(occupancy="trellis"))
    assert any(need.pack == "trellis2" for need in trellis)
    llm = requirements_for(CheckHints(occupancy="llm"))
    assert any(need.pack == "llm-qwen3-4b" for need in llm)
    research = requirements_for(CheckHints(types=("EZCreativeResearch",)))
    assert any(need.pack == "llm-qwen3-4b" for need in research)
    none = requirements_for(CheckHints(occupancy="none"))
    assert none == []
    describe = requirements_for(CheckHints(describe_on=True))
    assert any(need.pack == "llm-describe" for need in describe)
    iclora = requirements_for(CheckHints(flags=("iclora",)))
    assert any(need.pack == "ltx-iclora" for need in iclora)
    vace = requirements_for(CheckHints(flags=("vace",)))
    assert any(need.cmd == CMD_WAN_VACE for need in vace)
    fun = requirements_for(CheckHints(lab_rel="motion/silent/first-last-fun-inp"))
    assert any(need.cmd == CMD_WAN_FUN for need in fun)
    s2v = requirements_for(CheckHints(flags=("s2v",)))
    assert any(need.cmd == CMD_WAN_S2V for need in s2v)
    dub = requirements_for(CheckHints(types=("EZDubRender",)))
    assert any(need.cmd == CMD_DUB for need in dub)
    pod = requirements_for(CheckHints(types=("EZKokoroTTS",)))
    assert any(need.cmd == CMD_PODCAST for need in pod)
    longcat = requirements_for(CheckHints(types=("EZLongCatPromptEnhance",)))
    assert any(need.cmd == CMD_LONGCAT for need in longcat)
    dreamx = requirements_for(CheckHints(types=("EZDreamXPromptEnhance",)))
    assert any(need.cmd == CMD_DREAMX for need in dreamx)
    seed = requirements_for(CheckHints(unets=(SEEDVR2,)))
    assert any(need.cmd == CMD_RESTORE for need in seed)
    authored = requirements_for(CheckHints(unets=(WAN_5B,), clips=(CLIP_4B,), vaes=("flux2-vae.safetensors",), loras=(LTX_ICLORA,), checkpoints=(ACE_TURBO,)))
    packs = {need.pack for need in authored}
    assert "authored-unet" in packs
    assert "authored-clip" in packs
    assert "authored-vae" in packs
    assert "authored-lora" in packs
    assert "authored-ckpt" in packs


def test_inspect_file_states(tmp_path: Path) -> None:
    good = _comfy(tmp_path, "diffusion_models", KLEIN_DISTILLED)
    assert inspect_file(FileSpec(SUB_UNET, KLEIN_DISTILLED), (tmp_path,)) == "present"
    empty = _comfy(tmp_path, "diffusion_models", "empty.safetensors", b"")
    assert inspect_file(FileSpec(SUB_UNET, "empty.safetensors"), (tmp_path,)) == "missing"
    broken = tmp_path / "comfy" / "diffusion_models" / "broken.safetensors"
    broken.symlink_to("nope.safetensors")
    assert inspect_file(FileSpec(SUB_UNET, "broken.safetensors"), (tmp_path,)) == "broken"
    abs_link = tmp_path / "comfy" / "diffusion_models" / "abs.safetensors"
    abs_link.symlink_to(good.resolve())
    assert inspect_file(FileSpec(SUB_UNET, "abs.safetensors"), (tmp_path,)) == "absolute"
    _comfy(tmp_path, "diffusion_models", "wan_vace_join.safetensors")
    assert inspect_file(FileSpec(SUB_UNET, "", needle="vace"), (tmp_path,)) == "present"
    assert inspect_file(FileSpec(SUB_UNET, "", needle="missing-needle"), (tmp_path,)) == "missing"
    del empty


def test_folder_paths_and_iterdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _folder_paths_has("") is False
    monkeypatch.setitem(sys.modules, "folder_paths", SimpleNamespace())
    assert _folder_paths_has("x.safetensors") is False

    def _raise(_key: str) -> list[str]:
        raise RuntimeError("unknown")

    monkeypatch.setitem(
        sys.modules,
        "folder_paths",
        SimpleNamespace(get_filename_list=_raise),
    )
    assert _folder_paths_has("x.safetensors") is False
    monkeypatch.setitem(
        sys.modules,
        "folder_paths",
        SimpleNamespace(get_filename_list=lambda _key: []),
    )
    assert _folder_paths_has("x.safetensors") is False
    monkeypatch.setitem(
        sys.modules,
        "folder_paths",
        SimpleNamespace(get_filename_list=lambda _key: [KLEIN_DISTILLED]),
    )
    assert inspect_file(FileSpec(SUB_UNET, KLEIN_DISTILLED), (tmp_path,)) == "present"

    def _boom(_self: Path) -> Any:
        raise OSError("denied")

    (tmp_path / "comfy" / "diffusion_models").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(Path, "iterdir", _boom, raising=False)
    assert _iter_basenames(tmp_path, "diffusion_models") == []


def test_folder_paths_import_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def _no_fp(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "folder_paths":
            raise ImportError("no folder_paths")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_fp)
    assert _folder_paths_has("x.safetensors") is False


def test_hints_from_graph_and_args() -> None:
    graph = {
        "id": "still-draft",
        "extra": {
            "lab_rel": "stills/still-draft",
            "lab_app_mode": {"occupancy": "klein"},
            "lab_iclora": {"enabled": True},
            "lab_vace": {"enabled": True},
        },
        "nodes": [
            {"type": "UNETLoader", "widgets_values": [KLEIN_DISTILLED, "default"]},
            {"type": "CLIPLoader", "widgets_values": [CLIP_4B, "flux2"]},
            {"type": "VAELoader", "widgets_values": ["flux2-vae.safetensors"]},
            {"type": "LoraLoader", "widgets_values": [LTX_ICLORA]},
            {"type": "CheckpointLoaderSimple", "widgets_values": [ACE_TURBO]},
            {"type": "EZQuality", "widgets_values": [QUALITY_ULTRA]},
            {
                "type": "EZKleinPromptEnhance",
                "widgets_values": ["custom", "a cat", True, "t2i"],
            },
            {"type": "EZImageDescribe", "widgets_values": [True]},
            {"type": "Note", "widgets_values": ["hi"]},
        ],
    }
    hints = hints_from_graph(graph)
    assert hints.occupancy == "klein"
    assert hints.quality == QUALITY_ULTRA
    assert hints.enhance_on is True
    assert hints.describe_on is True
    assert "iclora" in hints.flags
    assert "vace" in hints.flags
    assert KLEIN_DISTILLED in hints.unets
    from_args = hints_from_args({"graph": graph})
    assert from_args.lab_rel == "stills/still-draft"
    rel_flags = hints_from_graph(
        {
            "extra": {"lab_rel": "dcc/depth-iclora"},
            "nodes": [{"type": "SaveImage"}],
        }
    )
    assert "iclora" in rel_flags.flags
    vace_rel = hints_from_graph(
        {"extra": {"lab_rel": "motion/silent/vace-join"}, "nodes": [{"type": "VHS_VideoCombine"}, {"type": "UNETLoader", "widgets_values": [WAN_5B]}]}
    )
    assert "vace" in vace_rel.flags
    fun_rel = hints_from_graph(
        {"extra": {"lab_rel": "dcc/first-last-fun-inp"}, "nodes": []}
    )
    assert "fun-inp" in fun_rel.flags
    s2v_rel = hints_from_graph(
        {"extra": {"lab_rel": "motion/av/speech-to-video"}, "nodes": []}
    )
    assert "s2v" in s2v_rel.flags
    off = hints_from_graph(
        {
            "nodes": [
                {
                    "type": "EZKleinPromptEnhance",
                    "widgets_values": ["custom", "x", False],
                }
            ]
        }
    )
    assert off.enhance_on is False
    none_bool = hints_from_graph(
        {"nodes": [{"type": "EZWanPromptEnhance", "widgets_values": ["custom", "x"]}]}
    )
    assert none_bool.enhance_on is True
    skip = hints_from_graph({"nodes": ["bad"]})
    assert skip.types == ()
    payload = hints_from_args(
        {
            "occupancy": "wan",
            "quality": "draft",
            "types": "VHS_VideoCombine",
            "flags": "vace",
        }
    )
    assert payload.occupancy == "wan"
    assert payload.types == ("VHS_VideoCombine",)
    status, body = handle_check({"occupancy": "none"})
    assert status == 200
    assert "message" in body


def test_scan_any_group_and_report(tmp_path: Path) -> None:
    _comfy(tmp_path, "diffusion_models", KLEIN_DISTILLED)
    _comfy(tmp_path, "text_encoders", CLIP_4B)
    _comfy(tmp_path, "vae", "flux2-vae.safetensors")
    _comfy(tmp_path, "diffusion_models", KLEIN_9B)
    _comfy(tmp_path, "text_encoders", CLIP_8B)
    result = scan(
        CheckHints(lab_rel="stills/hero", occupancy="klein", quality=QUALITY_ULTRA),
        (tmp_path,),
    )
    assert result.ok is True
    text = format_report(result)
    assert text.startswith("Ready for stills/hero @ ultra")
    missing = scan(CheckHints(occupancy="audio"), (tmp_path,))
    assert missing.ok is False
    report = format_report(missing)
    assert "Missing for this App" in report
    assert CMD_MUSIC in report
    assert "Run:" in report


def test_inspect_symlink_oserror(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _comfy(tmp_path, "diffusion_models", "x.safetensors")

    def _boom(self: Path) -> bool:
        if self.name == "x.safetensors":
            raise OSError("stat")
        return Path.is_symlink(self)

    monkeypatch.setattr(Path, "is_symlink", _boom)
    assert inspect_file(FileSpec(SUB_UNET, "x.safetensors"), (tmp_path,)) == "missing"


def test_register_routes_fail_soft_and_handler(tmp_path: Path) -> None:
    def _respond_early(payload: dict[str, Any], *, status: int = 200) -> tuple[int, dict[str, Any]]:
        return status, payload

    assert register_routes(server=object()) is False
    assert register_routes(server=SimpleNamespace(routes=None)) is False
    assert register_routes(server=SimpleNamespace(routes=SimpleNamespace())) is False
    assert (
        register_routes(
            server=SimpleNamespace(routes=object()),
            json_response=_respond_early,
        )
        is False
    )

    handlers: dict[str, Any] = {}

    class _Adder:
        def post(self, path: str) -> Any:
            def deco(fn: Any) -> Any:
                handlers[path] = fn
                return fn

            return deco

    def _respond(payload: dict[str, Any], *, status: int = 200) -> tuple[int, dict[str, Any]]:
        return status, payload

    fake = SimpleNamespace(routes=_Adder())
    assert register_routes(server=fake, json_response=_respond) is True
    assert "/ez_quality/check" in handlers

    class _Req:
        def __init__(self, body: Any = None, *, boom: bool = False) -> None:
            self._body = body
            self._boom = boom

        async def json(self) -> Any:
            if self._boom:
                raise ValueError("bad json")
            return self._body

    async def _run() -> None:
        listed = await handlers["/ez_quality/check"](_Req(body={"occupancy": "none"}))
        assert listed[0] == 200
        bad = await handlers["/ez_quality/check"](_Req(body=["nope"]))
        assert bad[0] == 200
        boom = await handlers["/ez_quality/check"](_Req(boom=True))
        assert boom[0] == 200

    asyncio.run(_run())


def test_register_routes_prompt_server_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_mod = SimpleNamespace(
        PromptServer=SimpleNamespace(instance=SimpleNamespace(routes=None))
    )
    monkeypatch.setitem(sys.modules, "server", fake_mod)
    assert (
        register_routes(json_response=lambda payload, status=200: (status, payload))
        is False
    )
    monkeypatch.setitem(
        sys.modules,
        "server",
        SimpleNamespace(PromptServer=SimpleNamespace(instance=None)),
    )
    assert (
        register_routes(json_response=lambda payload, status=200: (status, payload))
        is False
    )


def test_register_routes_server_import_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def _no_server(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "server":
            raise ImportError("no server")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_server)
    assert (
        register_routes(json_response=lambda payload, status=200: (status, payload))
        is False
    )


def test_register_routes_uses_aiohttp(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Web:
        @staticmethod
        def json_response(payload: dict[str, Any], status: int = 200) -> tuple[int, dict[str, Any]]:
            return status, payload

    monkeypatch.setitem(sys.modules, "aiohttp", SimpleNamespace(web=_Web))

    class _Adder:
        def post(self, path: str) -> Any:
            def deco(fn: Any) -> Any:
                return fn

            return deco

    assert register_routes(server=SimpleNamespace(routes=_Adder())) is True


def test_register_routes_aiohttp_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def _no_aiohttp(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "aiohttp" or name.startswith("aiohttp."):
            raise ImportError("no aiohttp")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_aiohttp)
    fake = SimpleNamespace(
        routes=SimpleNamespace(post=lambda _p: lambda fn: fn)
    )
    assert register_routes(server=fake) is False


def test_request_json_sync_and_missing() -> None:
    class _Sync:
        def json(self) -> dict[str, str]:
            return {"occupancy": "klein"}

    class _Boom:
        def json(self) -> dict[str, str]:
            raise ValueError("bad")

    assert asyncio.run(request_json(SimpleNamespace())) == {}
    assert asyncio.run(request_json(_Sync())) == {"occupancy": "klein"}
    assert asyncio.run(request_json(_Boom())) == {}


def test_ensure_model_check_node_is_idempotent() -> None:
    graph: dict[str, Any] = {
        "id": "probe",
        "last_node_id": 1,
        "nodes": [
            {
                "id": 1,
                "type": "SaveImage",
                "pos": [40, 80],
                "size": [320, 270],
                "inputs": [],
                "outputs": [],
            }
        ],
        "extra": {"linearData": {"inputs": [[1, "filename_prefix"]], "outputs": [1]}},
    }
    ensure_model_check_node(graph)
    first = find_model_check_node(graph)
    assert first is not None
    node_id = first["id"]
    pos = list(first["pos"])
    ensure_model_check_node(graph)
    again = find_model_check_node(graph)
    assert again is not None
    assert again["id"] == node_id
    assert again["pos"] == pos
    quality = find_quality_node(graph)
    assert quality is not None
    linear = graph["extra"]["linearData"]
    names = [entry[1] for entry in linear["inputs"]]
    assert CHECK_WIDGET not in names
    assert 1 in linear["outputs"]
    assert int(first["id"]) not in {int(n) for n in linear["outputs"]}
    assert first["widgets_values"] == [CHECK_DEFAULT]
    assert first["mode"] == 0


def test_stamper_places_without_overlap() -> None:
    graph: dict[str, Any] = {
        "id": "probe",
        "last_node_id": 2,
        "nodes": [
            {
                "id": 1,
                "type": "SaveImage",
                "pos": [40, 80],
                "size": [320, 270],
            },
            {
                "id": 2,
                "type": QUALITY_TYPE,
                "pos": [40.0, -120.0],
                "size": [320.0, 82.0],
                "widgets_values": ["lab"],
            },
        ],
        "extra": {},
    }
    ensure_model_check_node(graph)
    check = find_model_check_node(graph)
    assert check is not None
    from _lab_layout import node_overlap_hits

    assert node_overlap_hits(graph) == []


def test_stamp_all_model_check_writes(tmp_path: Path) -> None:
    lab = tmp_path / "_lab" / "stills"
    lab.mkdir(parents=True)
    graph = {
        "id": "still-draft",
        "last_node_id": 1,
        "nodes": [
            {
                "id": 1,
                "type": "SaveImage",
                "pos": [40, 80],
                "size": [320, 270],
            }
        ],
        "extra": {},
    }
    path = lab / "still-draft.json"
    path.write_text(json.dumps(graph), encoding="utf-8")
    count = stamp_all_model_check(tmp_path)
    assert count == 1
    written = json.loads(path.read_text(encoding="utf-8"))
    assert find_model_check_node(written) is not None
    assert find_quality_node(written) is not None


@pytest.mark.parametrize("path", lab_graph_paths(), ids=lambda p: p.name)
def test_every_lab_graph_has_one_model_check_node(path: Path) -> None:
    graph = json.loads(path.read_text(encoding="utf-8"))
    hits = [n for n in graph.get("nodes") or [] if n.get("type") == CHECK_TYPE]
    assert len(hits) == 1, path
    extra = graph.get("extra") or {}
    linear = extra.get("linearData") or {}
    inputs = linear.get("inputs") or []
    names = [entry[1] for entry in inputs if isinstance(entry, (list, tuple)) and len(entry) > 1]
    assert CHECK_WIDGET not in names
    outputs = [int(n) for n in linear.get("outputs") or []]
    assert int(hits[0]["id"]) not in outputs
    wired = False
    for node in graph.get("nodes") or []:
        if node.get("type") != CHECK_TYPE:
            continue
        for out in node.get("outputs") or []:
            if out.get("links"):
                wired = True
        for inp in node.get("inputs") or []:
            if inp.get("link") is not None:
                wired = True
    assert wired is False

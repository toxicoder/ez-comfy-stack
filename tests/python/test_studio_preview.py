"""Image-studio run preview: the App text matches what Queue will send."""

from __future__ import annotations

import asyncio
import builtins
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
PY = ROOT / "tests" / "python"
for path in (CUSTOM, PY):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from _lab_paths import lab_json, load_lab_graph  # noqa: E402
from ez_image.formats import resolve_canvas  # noqa: E402
from ez_image.modes import (  # noqa: E402
    ITERATE_EDIT_LINE,
    ITERATE_PREFIX,
    EZImageMode,
    get_mode,
    resolve_mode,
    resolve_studio_mode,
)
from ez_image.routes import (  # noqa: E402
    PREVIEW_UNAVAILABLE,
    handle_preview,
    register_routes,
    request_json,
)
from ez_prompt_enhance._styles import apply_style_to_prompt  # noqa: E402
from ez_prompt_enhance.background import wrap_background_prompt  # noqa: E402
from ez_prompt_enhance.lettering import wrap_text_swap_prompt  # noqa: E402
from ez_prompt_enhance.studio_preview import (  # noqa: E402
    preview_payload,
    preview_studio_run,
)

_FORMAT = "16:9 LTX feeder (1280×704)"


class _Still:
    """Stand-in IMAGE tensor with a BHWC shape."""

    def __init__(self, height: int, width: int) -> None:
        self.shape = (1, height, width, 3)


def _preview(**kwargs: Any) -> Any:
    base: dict[str, Any] = {
        "category": "Generate",
        "mode": "Photoreal still",
        "format_value": _FORMAT,
        "prompt": "a red door",
        "sample": "custom",
        "style": "none",
        "rewrite": False,
        "steps": 4,
        "cfg": 1,
        "unet": "flux-2-klein-4b-fp8.safetensors",
        "seed": 42,
        "seed_control": "fixed",
    }
    base.update(kwargs)
    return preview_studio_run(**base)


def test_iterate_off_matches_resolve_mode_and_node_run() -> None:
    canvas = resolve_canvas(_FORMAT, look="none")
    preview = _preview(iterate=False, look="none")
    packed = EZImageMode().run(
        "Generate",
        "Photoreal still",
        context=canvas.context,
        iterate=False,
    )
    direct = resolve_mode("Photoreal still", extra_context=canvas.context)
    assert preview.enhance_mode == packed["result"][1] == direct.enhance_mode == "t2i"
    assert preview.prefix == packed["result"][2] == direct.prefix == "ez_gen_photoreal"
    assert preview.context == packed["result"][0] == direct.context
    assert "Generate a photoreal still" in preview.context
    assert preview.next_pass == "text to image"
    assert "Rewrite is off" in preview.summary
    assert "Seed 42 (fixed)" in preview.summary
    assert "Steps 4 · CFG 1 · flux-2-klein-4b-fp8.safetensors" in preview.summary


def test_iterate_without_a_file_is_text_to_image() -> None:
    spec = get_mode("Change text")
    preview = _preview(category="Text", mode="Change text", iterate=True, filename="")
    packed = EZImageMode().run(
        "Text",
        "Change text",
        iterate=True,
        has_image=False,
        context=preview.context,
    )
    assert preview.enhance_mode == "t2i"
    assert preview.prefix == ITERATE_PREFIX
    assert packed["result"][1] == "t2i"
    assert packed["result"][2] == ITERATE_PREFIX
    assert spec.instruction not in preview.context
    assert preview.next_pass == "text to image"
    assert "Creator mode is not used" in preview.summary
    assert resolve_studio_mode("Change text", iterate="on").enhance_mode == "t2i"
    assert resolve_studio_mode("Change text", iterate=0).enhance_mode == "text_swap"
    assert resolve_studio_mode("Change text", iterate=object()).enhance_mode == "text_swap"
    assert resolve_studio_mode("Change text", iterate="no").prefix != ITERATE_PREFIX


def test_iterate_with_a_still_is_an_edit() -> None:
    image = _Still(800, 400)
    preview = _preview(
        mode="Photoreal still",
        iterate=True,
        filename="plate.png",
        image=image,
        size_mode="Match input",
    )
    packed = EZImageMode().run(
        "Generate",
        "Photoreal still",
        iterate="yes",
        has_image=True,
        context="",
    )
    assert preview.has_image is True
    assert preview.missing_file is False
    assert preview.enhance_mode == "edit"
    assert preview.prefix == ITERATE_PREFIX
    assert preview.next_pass == "edit plate.png"
    assert ITERATE_EDIT_LINE in preview.context
    assert ITERATE_EDIT_LINE in preview.summary
    assert packed["result"][1] == "edit"
    assert "Creator mode is not used" in preview.summary
    canvas = resolve_canvas(_FORMAT, size_mode="Match input", image=image)
    assert (preview.width, preview.height) == (canvas.width, canvas.height)
    assert preview.format_label == canvas.label


def test_missing_filename_is_text_to_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ez_prompt_enhance.studio_preview.load_input_still",
        lambda _name: None,
    )
    preview = _preview(iterate=True, filename="gone.png", rewrite=True)
    assert preview.missing_file is True
    assert preview.has_image is False
    assert preview.enhance_mode == "t2i"
    assert "Reference file missing (gone.png)" in preview.summary
    assert "not the CLIP text" in preview.summary
    assert preview.prompt == "a red door"


def test_sample_recipe_wins_and_custom_uses_the_box() -> None:
    named = _preview(sample="Photoreal terrace", prompt="typed something else")
    assert "techno wizard" in named.prompt
    assert named.prompt_source == "sample recipe"
    assert "sample recipe" in named.summary
    custom = _preview(sample="custom", prompt="my own still")
    assert custom.prompt == "my own still"
    assert custom.prompt_source == "prompt box"
    assert _preview(sample="", prompt="blank sample").prompt == "blank sample"


def test_style_ignored_on_text_swap_and_applied_when_rewrite_is_off() -> None:
    swapped = _preview(
        category="Text",
        mode="Change text",
        prompt="HELLO",
        style="photorealistic",
        rewrite=False,
    )
    assert swapped.enhance_mode == "text_swap"
    assert swapped.prompt == wrap_text_swap_prompt("HELLO")
    assert "style ignored" in swapped.style_note
    assert "style ignored" in swapped.summary
    assert swapped.next_pass == "text_swap"
    styled = _preview(prompt="a red door", style="photorealistic", rewrite=False)
    assert styled.prompt == apply_style_to_prompt("a red door", "photorealistic")
    assert styled.style_note == "style photorealistic"
    assert "this prompt is the CLIP text" in styled.summary
    noted = _preview(prompt="a red door", style="photorealistic", rewrite=True)
    assert noted.prompt == "a red door"
    assert noted.style_note == "style photorealistic"
    assert "not the CLIP text" in noted.summary
    unknown = _preview(style="not-a-style", rewrite=False)
    assert unknown.style_note == "style none"
    assert unknown.prompt == "a red door"


def test_background_wrap_and_reference_pass_name() -> None:
    image = _Still(64, 64)
    preview = _preview(
        category="Scene",
        mode="Background swap",
        prompt="pier",
        filename="pier.png",
        image=image,
        rewrite=False,
        style="photorealistic",
    )
    assert preview.enhance_mode == "background_swap"
    assert preview.prompt == wrap_background_prompt("pier", "background_swap", "")
    assert "style ignored" in preview.style_note
    assert preview.next_pass == "background_swap · pier.png"
    bare = _preview(category="Text", mode="Change text", filename="", rewrite=False)
    assert bare.next_pass == "text_swap"


def test_loaded_filename_counts_as_a_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ez_prompt_enhance.studio_preview.load_input_still",
        lambda _name: _Still(32, 32),
    )
    preview = _preview(filename="ok.png", iterate="yes", rewrite=None)
    assert preview.has_image is True
    assert preview.filename == "ok.png"
    assert preview.iterate is True
    assert preview.rewrite is True
    assert _preview(iterate=object(), rewrite="off").iterate is False
    assert _preview(rewrite="off").rewrite is False
    assert _preview(iterate=1).iterate is True


def test_iterate_batch_note_and_seed_randomize() -> None:
    preview = _preview(
        iterate=True,
        batch=2,
        seed_control="randomize",
        seed=7,
    )
    assert "changes when you Run (randomize)" in preview.summary
    assert "Iterate feeds the first still only." in preview.summary
    assert "batch 2" in preview.summary
    bumped = _preview(seed_control="increment", seed=3, iterate=False)
    assert "changes when you Run (increment)" in bumped.seed_note
    assert _preview(seed_control="", seed=3).seed_note == "Seed 3 (fixed)"
    assert _preview(seed_control="decrement", seed=1).seed_note.endswith("(decrement)")


def test_preview_payload_reads_widget_names() -> None:
    payload = preview_payload(
        {
            "mode": "Photoreal still",
            "category": "Generate",
            "format_value": _FORMAT,
            "prompt": "from payload",
            "enhance": False,
            "batch_size": 1,
            "steps": None,
            "cfg": 1.5,
            "unet": None,
            "iterate": "off",
        }
    )
    assert payload["ok"] is True
    assert payload["prompt"] == "from payload"
    assert payload["rewrite"] is False
    assert payload["width"] > 0
    empty = preview_payload(["nope"])
    assert empty["ok"] is True
    assert empty["enhance_mode"] == "t2i"


def test_handle_preview_fail_soft(monkeypatch: pytest.MonkeyPatch) -> None:
    status, payload = handle_preview({"mode": "Photoreal still", "format": _FORMAT})
    assert status == 200
    assert payload["ok"] is True
    assert payload["enhance_mode"] == "t2i"

    def _boom(_body: object) -> dict[str, Any]:
        raise RuntimeError("catalog")

    monkeypatch.setattr(
        "ez_prompt_enhance.studio_preview.preview_payload",
        _boom,
    )
    status, failed = handle_preview({"mode": "Photoreal still"})
    assert status == 200
    assert failed["ok"] is False
    assert failed["summary"] == PREVIEW_UNAVAILABLE

    real_import = builtins.__import__

    def _no_preview(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "ez_prompt_enhance.studio_preview":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_preview)
    status, missing = handle_preview({"mode": "x"})
    assert missing["summary"] == PREVIEW_UNAVAILABLE


def test_image_studio_wires_iterate_and_shows_it_first() -> None:
    graph = load_lab_graph(lab_json("stills/image-studio.json"))
    mode = next(node for node in graph["nodes"] if node.get("type") == "EZImageMode")
    fmt = next(node for node in graph["nodes"] if node.get("type") == "EZImageFormat")
    opt = next(node for node in graph["nodes"] if node.get("type") == "EZOptionalImage")
    values = list(mode.get("widgets_values") or [])
    assert values[0] == "Generate"
    assert values[1] == "Photoreal still"
    assert values[2] is False
    assert values[3] == ""
    links = {int(row[0]): row for row in graph["links"]}
    has_in = next(item for item in mode["inputs"] if item.get("name") == "has_image")
    has_link = links[int(has_in["link"])]
    assert has_link[1] == opt["id"]
    assert has_link[2] == 2
    image_in = next(item for item in fmt["inputs"] if item.get("name") == "image")
    image_link = links[int(image_in["link"])]
    assert image_link[1] == opt["id"]
    assert image_link[2] == 0
    names = [entry[1] for entry in graph["extra"]["linearData"]["inputs"]]
    assert names[:2] == ["iterate", "run_summary"]
    assert "Iterate" in graph["extra"]["lab_note"]
    assert "This run" in graph["extra"]["lab_note"]


def test_register_routes_fail_soft_and_handler() -> None:
    def _respond_early(
        payload: dict[str, Any], *, status: int = 200
    ) -> tuple[int, dict[str, Any]]:
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

    def _respond(
        payload: dict[str, Any], *, status: int = 200
    ) -> tuple[int, dict[str, Any]]:
        return status, payload

    fake = SimpleNamespace(routes=_Adder())
    assert register_routes(server=fake, json_response=_respond) is True
    assert "/ez_image/studio-preview" in handlers

    class _Req:
        def __init__(self, body: Any = None, *, boom: bool = False) -> None:
            self._body = body
            self._boom = boom

        async def json(self) -> Any:
            if self._boom:
                raise ValueError("bad json")
            return self._body

    async def _run() -> None:
        listed = await handlers["/ez_image/studio-preview"](
            _Req(body={"mode": "Photoreal still", "format": _FORMAT})
        )
        assert listed[0] == 200
        assert listed[1]["ok"] is True
        bad = await handlers["/ez_image/studio-preview"](_Req(body=["nope"]))
        assert bad[0] == 200
        boom = await handlers["/ez_image/studio-preview"](_Req(boom=True))
        assert boom[0] == 200

    asyncio.run(_run())


def test_register_routes_prompt_server_instance(monkeypatch: pytest.MonkeyPatch) -> None:
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
        def json_response(
            payload: dict[str, Any], status: int = 200
        ) -> tuple[int, dict[str, Any]]:
            return status, payload

    monkeypatch.setitem(sys.modules, "aiohttp", SimpleNamespace(web=_Web))

    class _Adder:
        def post(self, path: str) -> Any:
            def deco(fn: Any) -> Any:
                return fn

            return deco

    assert register_routes(server=SimpleNamespace(routes=_Adder())) is True


def test_register_routes_aiohttp_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def _no_aiohttp(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "aiohttp" or name.startswith("aiohttp."):
            raise ImportError("no aiohttp")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_aiohttp)
    fake = SimpleNamespace(routes=SimpleNamespace(post=lambda _p: (lambda fn: fn)))
    assert register_routes(server=fake) is False


def test_request_json_sync_and_missing() -> None:
    class _Sync:
        def json(self) -> dict[str, str]:
            return {"mode": "Photoreal still"}

    class _Boom:
        def json(self) -> dict[str, str]:
            raise ValueError("bad")

    assert asyncio.run(request_json(SimpleNamespace())) == {}
    assert asyncio.run(request_json(_Sync())) == {"mode": "Photoreal still"}
    assert asyncio.run(request_json(_Boom())) == {}

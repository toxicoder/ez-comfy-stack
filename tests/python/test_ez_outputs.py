"""Hermetic tests for the Outputs sidebar catalog and fail-soft routes."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from ez_outputs.catalog import (
    CatalogError,
    bounded_rels,
    copy_many_to_input,
    copy_to_input,
    delete_many,
    delete_output,
    input_root,
    kind_of,
    list_outputs,
    output_directory,
    resolve_under,
)
from ez_outputs.routes import (
    handle_delete,
    handle_list,
    handle_to_input,
    register_routes,
    rels_from_args,
    request_json,
)


def _touch(path: Path, data: bytes = b"x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def test_kind_of_media_suffixes() -> None:
    assert kind_of(".PNG") == "image"
    assert kind_of(".mp4") == "video"
    assert kind_of(".flac") == "audio"
    assert kind_of(".json") is None


def test_list_outputs_skips_system_dirs_and_sorts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "out"
    _touch(root / "ez_still_draft_00001_.png", b"aa")
    _touch(root / "clip.mp4", b"bbbb")
    _touch(root / "song.flac", b"c")
    _touch(root / "notes.txt", b"nope")
    _touch(root / "comfy-user" / "default" / "secret.png", b"hide")
    _touch(root / "input" / "start.png", b"hide")
    _touch(root / ".cache" / "x.png", b"hide")
    later = root / "newer.png"
    _touch(later, b"zz")
    later.touch()
    rows = list_outputs(root)
    rels = [row["rel"] for row in rows]
    assert "ez_still_draft_00001_.png" in rels
    assert "clip.mp4" in rels
    assert "song.flac" in rels
    assert "newer.png" in rels
    assert "notes.txt" not in rels
    assert all("comfy-user" not in row["rel"] for row in rows)
    assert all(not row["rel"].startswith("input/") for row in rows)
    assert rows[0]["rel"] == "newer.png"
    images = list_outputs(root, kind="image")
    assert {row["kind"] for row in images} == {"image"}
    filtered = list_outputs(root, query="still_draft")
    assert [row["rel"] for row in filtered] == ["ez_still_draft_00001_.png"]
    assert list_outputs(root, limit=1) == rows[:1]
    assert len(list_outputs(root, limit=-5)) == 1
    assert list_outputs(tmp_path / "missing") == []
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(root))
    monkeypatch.delenv("COMFY_OUTPUT", raising=False)
    listed = handle_list({"kind": "video", "q": "clip"})
    assert listed[0] == 200
    assert listed[1]["items"][0]["rel"] == "clip.mp4"


def test_resolve_delete_copy_and_refuses(tmp_path: Path) -> None:
    root = tmp_path / "out"
    src = root / "ez_hero.png"
    _touch(src, b"img")
    _touch(root / "comfy-user" / "x.png", b"no")
    _touch(root / "meta.json", b"{}")
    resolved = resolve_under(root, "ez_hero.png")
    assert resolved == src.resolve()
    with pytest.raises(CatalogError, match="invalid"):
        resolve_under(root, "../ez_hero.png")
    with pytest.raises(CatalogError, match="escapes|invalid"):
        resolve_under(root, "..")
    with pytest.raises(CatalogError, match="skipped"):
        resolve_under(root, "comfy-user/x.png")
    with pytest.raises(CatalogError, match="not a media"):
        resolve_under(root, "meta.json")
    with pytest.raises(CatalogError, match="missing"):
        resolve_under(root, "nope.png")
    dest_dir = tmp_path / "inputs"
    copied = copy_to_input(root, "ez_hero.png", input_dir=dest_dir)
    assert copied == dest_dir / "ez_hero.png"
    assert copied.read_bytes() == b"img"
    deleted = delete_output(root, "ez_hero.png")
    assert deleted == src.resolve()
    assert not src.exists()
    assert copied.exists()


def test_route_handlers_ok_and_errors(tmp_path: Path) -> None:
    root = tmp_path / "out"
    inputs = tmp_path / "in"
    _touch(root / "plate.webp", b"p")
    status, payload = handle_list({"kind": "all"}, root=root)
    assert status == 200
    assert payload["items"][0]["name"] == "plate.webp"
    bad = handle_delete({"rel": "missing.png"}, root=root)
    assert bad[0] == 400
    assert "error" in bad[1]
    ok = handle_to_input({"rel": "plate.webp"}, root=root, input_dir=inputs)
    assert ok[0] == 200
    assert ok[1]["name"] == "plate.webp"
    assert (inputs / "plate.webp").is_file()
    gone = handle_delete({"rel": "plate.webp"}, root=root)
    assert gone == (200, {"ok": True, "rel": "plate.webp"})
    empty = handle_delete({"rel": ""}, root=root)
    assert empty[0] == 400


def test_register_routes_fail_soft_and_fake_server(tmp_path: Path) -> None:
    import asyncio

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

    recorded: list[tuple[str, str]] = []
    handlers: dict[str, Any] = {}

    class _Adder:
        def get(self, path: str) -> Any:
            def deco(fn: Any) -> Any:
                recorded.append(("get", path))
                handlers[path] = fn
                return fn

            return deco

        def post(self, path: str) -> Any:
            def deco(fn: Any) -> Any:
                recorded.append(("post", path))
                handlers[path] = fn
                return fn

            return deco

    def _respond(payload: dict[str, Any], *, status: int = 200) -> tuple[int, dict[str, Any]]:
        return status, payload

    fake = SimpleNamespace(routes=_Adder())
    assert register_routes(server=fake, json_response=_respond) is True
    assert ("get", "/ez_outputs/list") in recorded
    assert ("post", "/ez_outputs/delete") in recorded
    assert ("post", "/ez_outputs/to-input") in recorded

    _touch(tmp_path / "shot.png")

    class _Req:
        def __init__(self, query: dict[str, str] | None = None, body: Any = None, *, boom: bool = False) -> None:
            self.query = query or {}
            self._body = body
            self._boom = boom

        async def json(self) -> Any:
            if self._boom:
                raise ValueError("bad json")
            return self._body

    monkey_root = tmp_path

    async def _run() -> None:
        import ez_outputs.routes as routes_mod

        orig_out = routes_mod.output_directory
        orig_in = routes_mod.input_root

        def _out() -> Any:
            return monkey_root

        def _in() -> Any:
            return monkey_root / "in"

        routes_mod.output_directory = _out  # type: ignore[assignment]
        routes_mod.input_root = _in  # type: ignore[assignment]
        try:
            listed = await handlers["/ez_outputs/list"](_Req(query={"kind": "image"}))
            assert listed[0] == 200
            assert listed[1]["items"][0]["name"] == "shot.png"
            copied = await handlers["/ez_outputs/to-input"](
                _Req(body={"rel": "shot.png"})
            )
            assert copied[0] == 200
            empty_del = await handlers["/ez_outputs/delete"](_Req(boom=True))
            assert empty_del[0] == 400
            not_dict = await handlers["/ez_outputs/to-input"](_Req(body=["x"]))
            assert not_dict[0] == 400
            not_dict_del = await handlers["/ez_outputs/delete"](_Req(body=["x"]))
            assert not_dict_del[0] == 400
            boom_in = await handlers["/ez_outputs/to-input"](_Req(boom=True))
            assert boom_in[0] == 400
            no_json = SimpleNamespace(query={})
            no_json_del = await handlers["/ez_outputs/delete"](no_json)
            assert no_json_del[0] == 400
            no_json_in = await handlers["/ez_outputs/to-input"](no_json)
            assert no_json_in[0] == 400
            gone = await handlers["/ez_outputs/delete"](_Req(body={"rel": "shot.png"}))
            assert gone[0] == 200
        finally:
            routes_mod.output_directory = orig_out
            routes_mod.input_root = orig_in

    asyncio.run(_run())


def test_pack_exports_empty_mappings_and_js() -> None:
    import ez_outputs

    assert ez_outputs.NODE_CLASS_MAPPINGS == {}
    assert ez_outputs.WEB_DIRECTORY == "./js"
    pack_js = Path(__file__).resolve().parents[2] / "custom_nodes" / "ez_outputs" / "js"
    js = pack_js / "ez_outputs.js"
    css = pack_js / "ez_outputs.css"
    body = js.read_text(encoding="utf-8")
    sheet = css.read_text(encoding="utf-8")
    assert "registerSidebarTab" in body
    assert "ez.outputs" in body
    assert "History does not" in body
    assert "node_widget" not in body
    assert "onResize" not in body
    assert "ez-out-grid" in body
    assert "ez-out-list" in body
    assert "--ez-out-thumb" in body
    assert "preview=webp" in body
    assert "localStorage" in body
    assert "rels" in body
    assert 'type = "checkbox"' in body
    assert "shiftKey" in body
    assert "Select all" in body
    assert "executed" in body
    assert "ez-out-grid" in sheet
    assert "ez-out-list" in sheet
    assert "--ez-out-thumb" in sheet
    assert "auto-fill" in sheet


def test_output_and_input_root_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path / "media"))
    assert output_directory() == tmp_path / "media"
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    assert input_root(default=tmp_path / "in") == tmp_path / "in"


def test_handle_list_bad_limit(tmp_path: Path) -> None:
    _touch(tmp_path / "a.png")
    status, payload = handle_list({"limit": "nope"}, root=tmp_path)
    assert status == 200
    assert payload["items"]


def test_output_directory_fallbacks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import builtins
    import sys

    from ez_outputs import catalog as cat

    real_import = builtins.__import__

    def _no_ez_common(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "ez_common" or name.startswith("ez_common."):
            raise ImportError("no ez_common")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_ez_common)
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path / "env-out"))
    assert cat.output_directory() == tmp_path / "env-out"
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)

    fake_fp = SimpleNamespace(get_output_directory=lambda: str(tmp_path / "fp-out"))
    monkeypatch.setitem(sys.modules, "folder_paths", fake_fp)
    assert cat.output_directory() == tmp_path / "fp-out"

    def _no_common_or_fp(name: str, *args: Any, **kwargs: Any) -> Any:
        if name in {"ez_common", "folder_paths"} or name.startswith("ez_common."):
            raise ImportError("no")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_common_or_fp)
    monkeypatch.delitem(sys.modules, "folder_paths", raising=False)
    assert cat.output_directory() == Path("/outputs")


def test_input_root_folder_paths_and_skip_outside(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys

    from ez_outputs.catalog import _skip_parts

    fake_fp = SimpleNamespace(get_input_directory=lambda: str(tmp_path / "fp-in"))
    monkeypatch.setitem(sys.modules, "folder_paths", fake_fp)
    assert input_root() == tmp_path / "fp-in"
    outside = tmp_path / "other" / "x.png"
    _touch(outside)
    assert _skip_parts(outside, tmp_path / "out") is True


def test_list_outputs_skips_stat_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _touch(tmp_path / "ok.png", b"aa")
    boom = tmp_path / "boom.png"
    _touch(boom, b"bb")
    real_stat = Path.stat

    def _stat(self: Path, *args: Any, **kwargs: Any) -> Any:
        if self.name == "boom.png":
            raise OSError("gone")
        return real_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", _stat)
    rels = [row["rel"] for row in list_outputs(tmp_path)]
    assert "ok.png" in rels
    assert "boom.png" not in rels

    hits = {"n": 0}

    def _stat_second(self: Path, *args: Any, **kwargs: Any) -> Any:
        if self.name == "ok.png":
            hits["n"] += 1
            if hits["n"] > 1:
                raise OSError("gone later")
        return real_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", _stat_second)
    leftover = [row["rel"] for row in list_outputs(tmp_path)]
    assert "ok.png" not in leftover


def test_input_root_empty_folder_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys

    fake_fp = SimpleNamespace(get_input_directory=lambda: "")
    monkeypatch.setitem(sys.modules, "folder_paths", fake_fp)
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path / "media"))
    assert input_root() == tmp_path / "media" / "input"


def test_register_routes_prompt_server_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys

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


def test_resolve_under_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path / "outside.png"
    _touch(outside)
    root = tmp_path / "out"
    root.mkdir()
    (root / "link.png").symlink_to(outside)
    with pytest.raises(CatalogError, match="escapes"):
        resolve_under(root, "link.png")


def test_copy_to_input_default_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ez_outputs import catalog as cat

    root = tmp_path / "out"
    _touch(root / "still.png")
    monkeypatch.setattr(cat, "input_root", lambda **_kwargs: tmp_path / "auto-in")
    dest = copy_to_input(root, "still.png")
    assert dest == tmp_path / "auto-in" / "still.png"
    assert dest.is_file()


def test_list_outputs_parent_and_truncated(tmp_path: Path) -> None:
    _touch(tmp_path / "root.png")
    _touch(tmp_path / "shots" / "take.webp")
    rows = {row["rel"]: row for row in list_outputs(tmp_path)}
    assert rows["root.png"]["parent"] == ""
    assert rows["shots/take.webp"]["parent"] == "shots"
    status, payload = handle_list({"limit": 1}, root=tmp_path)
    assert status == 200
    assert payload["truncated"] is True
    assert payload["count"] == 1
    assert len(payload["items"]) == 1
    full = handle_list({"limit": 50}, root=tmp_path)
    assert full[1]["truncated"] is False
    assert full[1]["count"] == 2


def test_bounded_rels_and_bulk_delete_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from ez_outputs import catalog as cat

    root = tmp_path / "out"
    _touch(root / "keep.png", b"k")
    _touch(root / "gone.png", b"g")
    _touch(root / "also.png", b"a")
    _touch(root / "comfy-user" / "hid.png", b"h")
    _touch(root / "clip.mp4", b"v")
    with pytest.raises(CatalogError, match="invalid"):
        bounded_rels([])
    with pytest.raises(CatalogError, match="invalid"):
        bounded_rels(["", "  "])
    assert bounded_rels(["a.png", "a.png", "b.png"]) == ["a.png", "b.png"]
    monkeypatch.setattr(cat, "LIST_CAP", 2)
    assert bounded_rels(["a", "b", "c"]) == ["a", "b"]
    monkeypatch.setattr(cat, "LIST_CAP", 500)

    deleted, errors = delete_many(
        root, ["gone.png", "missing.png", "comfy-user/hid.png", "../x.png", "also.png"]
    )
    assert deleted == ["gone.png", "also.png"]
    reasons = {row["rel"]: row["error"] for row in errors}
    assert "missing.png" in reasons
    assert "comfy-user/hid.png" in reasons
    assert (root / "keep.png").is_file()
    assert not (root / "gone.png").exists()

    dest = tmp_path / "in"
    copied, copy_err = copy_many_to_input(
        root, ["keep.png", "clip.mp4", "missing.png"], input_dir=dest
    )
    assert [row["name"] for row in copied] == ["keep.png", "clip.mp4"]
    assert copy_err[0]["rel"] == "missing.png"
    assert (dest / "keep.png").is_file()
    with pytest.raises(CatalogError, match="invalid"):
        delete_many(root, [])
    with pytest.raises(CatalogError, match="invalid"):
        copy_many_to_input(root, [], input_dir=dest)


def test_rels_from_args_and_bulk_handlers(tmp_path: Path) -> None:
    assert rels_from_args({"rel": "a.png"}) == ["a.png"]
    assert rels_from_args({"rels": ["a.png", "", "b.png"]}) == ["a.png", "b.png"]
    assert rels_from_args({"rels": "solo.png"}) == ["solo.png"]
    assert rels_from_args({"rels": [], "rel": "fallback.png"}) == ["fallback.png"]
    assert rels_from_args({"rels": {"x": 1}, "rel": "ok.png"}) == ["ok.png"]
    assert rels_from_args({}) == []

    root = tmp_path / "out"
    inputs = tmp_path / "in"
    _touch(root / "one.png")
    _touch(root / "two.png")
    _touch(root / "three.png")
    single = handle_delete({"rels": ["one.png"]}, root=root)
    assert single == (200, {"ok": True, "rel": "one.png"})
    bulk = handle_delete({"rels": ["two.png", "missing.png", "three.png"]}, root=root)
    assert bulk[0] == 200
    assert bulk[1]["deleted"] == ["two.png", "three.png"]
    assert bulk[1]["errors"][0]["rel"] == "missing.png"
    none = handle_delete({"rels": ["nope.png", "also-no.png"]}, root=root)
    assert none[0] == 400
    assert "error" in none[1]
    empty_bulk = handle_delete({"rels": []}, root=root)
    assert empty_bulk[0] == 400

    _touch(root / "still.png")
    _touch(root / "song.flac")
    copied = handle_to_input(
        {"rels": ["still.png", "song.flac", "gone.png"]},
        root=root,
        input_dir=inputs,
    )
    assert copied[0] == 200
    names = [row["name"] for row in copied[1]["copied"]]
    assert names == ["still.png", "song.flac"]
    assert (inputs / "still.png").is_file()
    one = handle_to_input({"rels": ["still.png"]}, root=root, input_dir=inputs)
    assert one[0] == 200
    assert one[1]["name"] == "still.png"
    fail_copy = handle_to_input({"rels": ["nope.png", "no2.png"]}, root=root, input_dir=inputs)
    assert fail_copy[0] == 400


def test_bulk_handlers_catalog_error_and_copy_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ez_outputs.routes as routes_mod
    from ez_outputs import catalog as cat

    def _boom(*_args: Any, **_kwargs: Any) -> Any:
        raise CatalogError("invalid output path")

    monkeypatch.setattr(routes_mod, "delete_many", _boom)
    monkeypatch.setattr(routes_mod, "copy_many_to_input", _boom)
    bad_del = handle_delete({"rels": ["a.png", "b.png"]}, root=tmp_path)
    assert bad_del[0] == 400
    assert "error" in bad_del[1]
    bad_copy = handle_to_input(
        {"rels": ["a.png", "b.png"]}, root=tmp_path, input_dir=tmp_path
    )
    assert bad_copy[0] == 400

    root = tmp_path / "out"
    _touch(root / "still.png")
    monkeypatch.setattr(cat, "input_root", lambda **_kwargs: tmp_path / "auto-in")
    copied, errors = copy_many_to_input(root, ["still.png"])
    assert errors == []
    assert copied[0]["name"] == "still.png"
    assert (tmp_path / "auto-in" / "still.png").is_file()


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
    import sys

    class _Web:
        @staticmethod
        def json_response(payload: dict[str, Any], status: int = 200) -> tuple[int, dict[str, Any]]:
            return status, payload

    monkeypatch.setitem(sys.modules, "aiohttp", SimpleNamespace(web=_Web))

    class _Adder:
        def get(self, path: str) -> Any:
            def deco(fn: Any) -> Any:
                return fn

            return deco

        def post(self, path: str) -> Any:
            def deco(fn: Any) -> Any:
                return fn

            return deco

    assert register_routes(server=SimpleNamespace(routes=_Adder())) is True


def test_request_json_sync_and_missing() -> None:
    import asyncio

    class _Sync:
        def json(self) -> dict[str, str]:
            return {"rel": "x.png"}

    class _Boom:
        def json(self) -> dict[str, str]:
            raise ValueError("bad")

    assert asyncio.run(request_json(SimpleNamespace())) == {}
    assert asyncio.run(request_json(_Sync())) == {"rel": "x.png"}
    assert asyncio.run(request_json(_Boom())) == {}


def test_register_routes_aiohttp_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def _no_aiohttp(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "aiohttp" or name.startswith("aiohttp."):
            raise ImportError("no aiohttp")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_aiohttp)
    fake = SimpleNamespace(routes=SimpleNamespace(get=lambda _p: lambda fn: fn, post=lambda _p: lambda fn: fn))
    assert register_routes(server=fake) is False

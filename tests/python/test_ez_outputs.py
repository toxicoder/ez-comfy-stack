"""Hermetic tests for the Outputs sidebar catalog and fail-soft routes."""

from __future__ import annotations

import builtins
import json
import os
import re
import subprocess
import sys
import zlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from ez_outputs import probe
from ez_outputs.catalog import (
    MIDI_SUFFIXES,
    REPORT_FILENAMES,
    CatalogError,
    OutputRow,
    bounded_rels,
    classify,
    copy_many_to_input,
    copy_to_input,
    delete_many,
    delete_output,
    input_root,
    kind_of,
    list_outputs,
    output_directory,
    report_kind_of,
    resolve_under,
)
from ez_outputs.routes import (
    ListPayload,
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

    def _respond_early(payload: object, *, status: int = 200) -> tuple[int, object]:
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

    def _respond(payload: object, *, status: int = 200) -> tuple[int, object]:
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

        routes_mod.output_directory = _out
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


def _outputs_js() -> str:
    """Return the Outputs sidebar frontend source.

    Returns:
        Contents of ``custom_nodes/ez_outputs/js/ez_outputs.js``.
    """
    pack_js = Path(__file__).resolve().parents[2] / "custom_nodes" / "ez_outputs" / "js"
    return (pack_js / "ez_outputs.js").read_text(encoding="utf-8")


def test_outputs_js_toolbar_report_buttons() -> None:
    """The top chrome carries prefilled bug and feature report buttons."""
    body = _outputs_js()
    assert 'makeButton("Report a problem", "ez-out-btn"' in body
    assert "  }, { icon: true });" in body
    assert 'makeButton("Suggest a feature", "ez-out-btn"' in body
    assert 'explorerReport("bug")' in body
    assert 'explorerReport("enhancement")' in body
    assert 'surface: "media-explorer"' in body
    # Appended alongside Refresh in the kind row, not into a dialog of our own.
    assert body.index("kindRow.appendChild(refreshBtn)") < body.index(
        "kindRow.appendChild(reportBtn)"
    ) < body.index("kindRow.appendChild(featureBtn)")
    assert "showModal" not in body
    assert "window.alert" not in body


def test_outputs_js_lightbox_report_is_per_file() -> None:
    """The lightbox bar reports one file on the media-file surface."""
    body = _outputs_js()
    assert 'makeButton("Report", "ez-out-btn"' in body
    assert 'surface: "media-file"' in body
    assert 'summary: clipText("Problem with " + row.rel, 120)' in body
    assert "context: fileContext(row)" in body
    # Sits with the other bar actions and never displaces Close.
    assert body.index('makeButton("Report", "ez-out-btn"') < body.index(
        'makeButton("Close", "ez-out-btn"'
    )
    # The keyboard cursor and arrow stepping stay owned by el's single handler.
    assert body.count('addEventListener("keydown"') == 1
    assert body.count("window.confirm(") == 1


_ICON_LABELS = ("Report a problem", "Suggest a feature", "Report this problem", "Report")


def _button_call_flags(body: str) -> dict[str, bool]:
    """Whether each string-labelled makeButton call asks for the icon.

    Args:
        body: Contents of ``custom_nodes/ez_outputs/js/ez_outputs.js``.

    Returns:
        ``label -> icon`` for every ``makeButton("<label>", ...)`` call site, in
        source order, where a repeated label keeps its last call's value.
    """
    starts = [match.start() for match in re.finditer(r'makeButton\(\s*"', body)]
    flags: dict[str, bool] = {}
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(body)
        chunk = body[start:end]
        label = re.search(r'makeButton\(\s*"([^"]+)"', chunk)
        assert label is not None, chunk[:80]
        flags[label.group(1)] = "{ icon: true }" in chunk
    return flags


def test_outputs_js_report_buttons_carry_the_github_mark() -> None:
    """Only the report buttons prepend the octicon mark; labels stay plain text."""
    body = _outputs_js()
    flags = _button_call_flags(body)
    for label in _ICON_LABELS:
        assert flags.get(label) is True, label
    for label, icon in flags.items():
        if label not in _ICON_LABELS:
            assert icon is False, label
    assert body.count("{ icon: true }") == 4
    # The mark is hand-built DOM: createElementNS, never innerHTML.
    assert "function githubIconSvg()" in body
    assert 'const SVG_NS = "http://www.w3.org/2000/svg";' in body
    assert 'document.createElementNS(SVG_NS, "svg")' in body
    assert 'document.createElementNS(SVG_NS, "path")' in body
    assert 'svg.setAttribute("viewBox", "0 0 16 16");' in body
    assert 'svg.setAttribute("width", "14");' in body
    assert 'svg.setAttribute("height", "14");' in body
    assert 'svg.setAttribute("aria-hidden", "true");' in body
    assert 'svg.setAttribute("class", "ez-out-icon");' in body
    assert 'path.setAttribute("fill", "currentColor");' in body
    assert "button.insertBefore(githubIconSvg(), button.firstChild);" in body
    assert "opts && opts.icon" in body
    assert "innerHTML" not in body
    mark = re.search(r'const GITHUB_MARK_PATH = "([^"]+)";', body)
    assert mark is not None
    assert mark.group(1).startswith("M6.766 11.328c-2.063")
    assert mark.group(1).endswith("5.47-.5.657-.656")


def test_outputs_js_reaches_the_core_lazily_with_a_handoff_fallback() -> None:
    """window.EzFeedback is read at click time and absent-core falls back."""
    body = _outputs_js()
    assert "const fb = window.EzFeedback;" in body
    assert "function feedbackCore(method)" in body
    assert "typeof fb[method] !== " in body
    assert "fb.openReport(report)" in body
    assert "fb.recordError({" in body
    assert "ts: new Date().toISOString()" in body
    assert "function issuesHandoffUrl(report)" in body
    assert (
        'const ISSUES_URL = "https://github.com/toxicoder/ez-comfy-stack/issues/new";'
        in body
    )
    assert 'window.open(issuesHandoffUrl(report), "_blank", "noopener")' in body
    assert "REPORT_HREF_MAX" in body
    assert '"## What happened"' in body
    # Same-origin only: the single fetch is the backend route, the one absolute
    # URL is the GitHub handoff tab.
    assert body.count("await fetch(") == 1
    assert body.count("https://") == 1
    assert "window.location" not in body


def test_outputs_js_records_route_failures() -> None:
    """Every catch feeds the ring buffer with endpoint and status."""
    body = _outputs_js()
    assert "error.endpoint = path;" in body
    assert "error.status = response.status;" in body
    assert 'noteFailure("/ez_outputs/delete", err,' in body
    assert 'noteFailure("/ez_outputs/to-input", err,' in body
    assert 'noteFailure("/ez_outputs/list", err,' in body
    assert '"endpoint=" + endpoint' in body
    assert '"status=" + httpStatus' in body
    assert "function errorDetail(errors)" in body
    assert "endpoint=/ez_outputs/delete " in body
    assert "endpoint=/ez_outputs/to-input " in body
    # A broken list is one click from a filed issue.
    assert 'fail.className = "ez-out-fail";' in body
    assert 'failReportButton("/ez_outputs/list", message, httpStatus)' in body
    assert 'makeButton("Report this problem", "ez-out-btn"' in body


def test_outputs_js_report_context_is_prefilled_from_scope() -> None:
    """Context carries the filters and the selected rels, never host paths."""
    body = _outputs_js()
    for pair in (
        '["folder", folderToken()]',
        '["prefix", prefix || "-"]',
        '["kind", kind]',
        '["search", query || "-"]',
        '["view", view]',
        '["sort", sortMode]',
        '["items", String(vis.length)]',
        '["loaded", String(items.length)]',
        '["truncated", truncated ?',
        '["selected", chosen.length',
    ):
        assert pair in body, pair
    assert "const REPORT_REL_CAP = 10;" in body
    assert ".slice(0, REPORT_REL_CAP)" in body
    for pair in (
        '["rel", String(item.rel || "")]',
        '["kind", String(item.kind || "")]',
        '["size", String(item.size',
        '["mtime", String(item.mtime',
        '["suffix", String(item.suffix',
        '["parent", String(item.parent',
    ):
        assert pair in body, pair
    assert "function folderToken()" in body
    assert 'if (folder === ROOT_FOLDER)' in body


def test_outputs_css_styles_the_fail_pane_button() -> None:
    """The report button inside the failure pane keeps the pane's palette."""
    pack_js = Path(__file__).resolve().parents[2] / "custom_nodes" / "ez_outputs" / "js"
    sheet = (pack_js / "ez_outputs.css").read_text(encoding="utf-8")
    assert ".ez-out-fail .ez-out-btn" in sheet
    assert ".ez-out-chip," in sheet
    # The GitHub mark sits on the label baseline and follows the button colour.
    assert ".ez-out-btn .ez-out-icon {" in sheet
    rule = sheet.split(".ez-out-btn .ez-out-icon {", 1)[1].split("}", 1)[0]
    assert "display: inline-block;" in rule
    assert "vertical-align: -2px;" in rule
    assert "fill: currentColor;" in rule


def _css_rule(sheet: str, selector: str) -> str:
    """Return the declaration block one class selector owns.

    Comments are dropped and the sheet is read rule by rule, so a grouped rule
    (``.ez-out-batch,`` / ``.ez-out-take-label {``) answers for each of its
    selectors and a compound one (``.ez-out-take`` never matches
    ``.ez-out-take-name``) cannot.

    Args:
        sheet: Stylesheet source.
        selector: Selector exactly as the sheet spells it.

    Returns:
        The text between that rule's braces.

    Raises:
        AssertionError: when the sheet has no such rule.
    """
    stripped = re.sub(r"/\*.*?\*/", "", sheet, flags=re.DOTALL)
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", stripped):
        if selector in [part.strip() for part in match.group(1).split(",")]:
            return match.group(2)
    raise AssertionError(selector)


def test_outputs_css_styles_the_probed_card_lines() -> None:
    """Root line, detail lines, and batch captions read as secondary text."""
    pack_js = Path(__file__).resolve().parents[2] / "custom_nodes" / "ez_outputs" / "js"
    sheet = (pack_js / "ez_outputs.css").read_text(encoding="utf-8")
    for selector in (".ez-out-root", ".ez-out-line", ".ez-out-take-facts"):
        rule = _css_rule(sheet, selector)
        assert "color: var(--ez-out-muted);" in rule, selector
        assert "font-variant-numeric: tabular-nums;" in rule, selector
    for selector in (".ez-out-root", ".ez-out-line", ".ez-out-take-name"):
        rule = _css_rule(sheet, selector)
        assert "white-space: nowrap;" in rule, selector
        assert "overflow: hidden;" in rule, selector
        assert "text-overflow: ellipsis;" in rule, selector
    for selector in (".ez-out-batch", ".ez-out-take-label"):
        rule = _css_rule(sheet, selector)
        assert "border-radius: 999px;" in rule, selector
        assert "color: var(--ez-out-muted);" in rule, selector


def test_outputs_css_indents_the_take_list_under_its_batch_card() -> None:
    """A batch card lists its takes, indented, on a row of their own."""
    pack_js = Path(__file__).resolve().parents[2] / "custom_nodes" / "ez_outputs" / "js"
    sheet = (pack_js / "ez_outputs.css").read_text(encoding="utf-8")
    takes = _css_rule(sheet, ".ez-out-group .ez-out-takes")
    assert "grid-column: 1 / -1;" in takes
    assert "flex-direction: column;" in takes
    take = _css_rule(sheet, ".ez-out-take")
    assert "cursor: pointer;" in take
    assert "border-radius: var(--ez-out-radius-sm);" in take
    # The indent is an em of the card font, never a fixed pixel width.
    assert "margin-left: 1.25em;" in take
    assert "flex: 1 1 100%;" in _css_rule(sheet, ".ez-out-take .ez-out-line")


UNSTYLED_JS_CLASSES = frozenset({"ez-out-badge-", "ez-out-group-check"})
"""Classes the frontend assigns that legitimately carry no rule of their own.

``ez-out-badge-`` is the half of a name built at runtime (the kind suffix is
appended, and every spelled-out suffix has its own rule); ``ez-out-group-check``
is a ``querySelector`` hook on a checkbox styled through ``.ez-out-check``.
"""


def _js_classes(body: str) -> set[str]:
    """Return every ``ez-out-*`` class name the frontend assigns.

    Args:
        body: Panel frontend source.

    Returns:
        Names from class assignments and ``classList.add`` calls.
    """
    names: set[str] = set()
    for blob in re.findall(r'"([^"\\\n]*ez-out-[^"\\\n]*)"', body):
        names.update(token for token in blob.split() if token.startswith("ez-out-"))
    for added in re.findall(r'classList\.add\("([^"]+)"\)', body):
        if added.startswith("ez-out-"):
            names.add(added)
    return names


def test_outputs_css_styles_every_class_the_js_renders() -> None:
    """No card part ships unstyled: every rendered class has a selector.

    The batch card, its take list, the probed detail lines, the output-root
    line, and the MIDI and report placeholders each arrived without a rule;
    this is the gate that stops the next one from doing the same.
    """
    pack_js = Path(__file__).resolve().parents[2] / "custom_nodes" / "ez_outputs" / "js"
    body = (pack_js / "ez_outputs.js").read_text(encoding="utf-8")
    sheet = (pack_js / "ez_outputs.css").read_text(encoding="utf-8")
    styled = {match.lstrip(".") for match in re.findall(r"\.ez-out-[a-z0-9-]+", sheet)}
    unstyled = _js_classes(body) - styled - UNSTYLED_JS_CLASSES
    assert not unstyled, f"rendered by the JS with no rule in the CSS: {sorted(unstyled)}"


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

    # A file can disappear after the is_file() probe, so the row-level stat has
    # its own guard. Pin is_file() open rather than counting Path.stat() calls:
    # CPython routes is_file() through Path.stat() on 3.12 but not on 3.14, so
    # a call counter only fires on the older interpreter.
    def _stat_late(self: Path, *args: Any, **kwargs: Any) -> Any:
        if self.name == "ok.png":
            raise OSError("gone later")
        return real_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "is_file", lambda self: True)
    monkeypatch.setattr(Path, "stat", _stat_late)
    leftover = [row["rel"] for row in list_outputs(tmp_path)]
    assert "ok.png" not in leftover

    # The is_file() probe failing is a separate branch from the row-level stat,
    # and on 3.14 nothing routes through Path.stat() there, so drive it directly.
    def _is_file(self: Path) -> bool:
        if self.name == "boom.png":
            raise OSError("probe failed")
        return True

    monkeypatch.setattr(Path, "is_file", _is_file)
    monkeypatch.setattr(Path, "stat", real_stat)
    raced = [row["rel"] for row in list_outputs(tmp_path)]
    assert "boom.png" not in raced
    assert "ok.png" in raced


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


# --------------------------------------------------------------------------- #
# Kinds the catalog used to hide, and the lines each kind's card carries.
# --------------------------------------------------------------------------- #


@pytest.fixture(autouse=True)
def _fresh_probe_cache() -> Any:
    """Isolate the row-detail cache, which is keyed by path and mtime.

    Yields:
        Nothing; the cache is empty on both sides of the test.
    """
    probe.clear_cache()
    yield
    probe.clear_cache()


def _chunk(kind: bytes, data: bytes) -> bytes:
    """Frame one PNG chunk.

    Args:
        kind: Four-byte chunk type.
        data: Chunk payload.

    Returns:
        Length, type, payload, and a decorative CRC (the probe reads none).
    """
    return len(data).to_bytes(4, "big") + kind + data + b"\x00\x00\x00\x00"


def _png(width: int, height: int, chunks: tuple[bytes, ...] = ()) -> bytes:
    """Build a PNG head with an IHDR, optional text chunks, and an IEND.

    Args:
        width: Pixel width written into IHDR.
        height: Pixel height written into IHDR.
        chunks: Extra chunks to place between IHDR and IEND.

    Returns:
        Bytes that parse as a PNG.
    """
    ihdr = _chunk(
        b"IHDR",
        width.to_bytes(4, "big") + height.to_bytes(4, "big") + b"\x08\x06\x00\x00\x00",
    )
    return b"\x89PNG\r\n\x1a\n" + ihdr + b"".join(chunks) + _chunk(b"IEND", b"")


def _txt(keyword: str, text: str) -> bytes:
    """Build a ``tEXt`` chunk.

    Args:
        keyword: Chunk keyword.
        text: Payload text.

    Returns:
        One framed chunk.
    """
    return _chunk(b"tEXt", keyword.encode("latin-1") + b"\x00" + text.encode("latin-1"))


def _ztxt(keyword: str, payload: bytes) -> bytes:
    """Build a ``zTXt`` chunk whose payload is already deflated bytes.

    Args:
        keyword: Chunk keyword.
        payload: Deflate stream (byte 0 of the chunk body is the method).

    Returns:
        One framed chunk.
    """
    return _chunk(b"zTXt", keyword.encode("latin-1") + b"\x00\x00" + payload)


def _itxt(keyword: str, payload: bytes, compressed: bool = False) -> bytes:
    """Build an ``iTXt`` chunk.

    Args:
        keyword: Chunk keyword.
        payload: Text bytes, deflated when ``compressed``.
        compressed: Set the chunk's compression flag.

    Returns:
        One framed chunk.
    """
    flag = b"\x01" if compressed else b"\x00"
    body = keyword.encode("latin-1") + b"\x00" + flag + b"\x00en\x00\x00" + payload
    return _chunk(b"iTXt", body)


def _midi(tracks: int, magic: bytes = b"MThd") -> bytes:
    """Build a MIDI header block.

    Args:
        tracks: Track count written at offset 10.
        magic: Four-byte form type, wrong on purpose in one test.

    Returns:
        The 14-byte ``MThd`` header.
    """
    return magic + (6).to_bytes(4, "big") + b"\x00\x01" + tracks.to_bytes(2, "big") + b"\x00\x60"


def _jpeg(width: int, height: int) -> bytes:
    """Build a JPEG head whose first segment is a start-of-frame marker.

    Args:
        width: Pixel width.
        height: Pixel height.

    Returns:
        Bytes that parse as a JPEG.
    """
    return (
        b"\xff\xd8\xff\xc0"
        + (17).to_bytes(2, "big")
        + b"\x08"
        + height.to_bytes(2, "big")
        + width.to_bytes(2, "big")
        + b"\x01\x11\x00"
    )


def _webp(fourcc: bytes, width: int, height: int) -> bytes:
    """Build a WebP head for one chunk type.

    Args:
        fourcc: ``VP8 `` or ``VP8L``, or anything else for the refuse.
        width: Pixel width.
        height: Pixel height.

    Returns:
        Bytes that parse as that WebP variant.
    """
    if fourcc == b"VP8L":
        bits = ((height - 1) & 0x3FFF) << 14 | ((width - 1) & 0x3FFF)
        return b"RIFF" + b"\x00" * 4 + b"WEBP" + fourcc + b"\x00" * 4 + b"\x2f" + bits.to_bytes(
            4, "little"
        )
    body = b"\x00" * 3 + b"\x9d\x01\x2a" + width.to_bytes(2, "little") + height.to_bytes(
        2, "little"
    )
    return b"RIFF" + b"\x00" * 4 + b"WEBP" + fourcc + (len(body)).to_bytes(4, "little") + body


def _fake_ffprobe(
    monkeypatch: pytest.MonkeyPatch,
    payload: Any = None,
    *,
    which: bool = True,
    returncode: int = 0,
    boom: BaseException | None = None,
    raw: str | None = None,
) -> None:
    """Give the probe a canned ``ffprobe`` answer.

    Args:
        monkeypatch: Pytest monkeypatcher.
        payload: Object to serialise as ffprobe's JSON, or ``None``.
        which: Whether ``ffprobe`` is on PATH at all.
        returncode: Exit code the fake binary reports.
        boom: Exception the fake binary raises instead of answering.
        raw: stdout verbatim, for the malformed-JSON branch.
    """
    monkeypatch.setattr(
        probe.shutil, "which", lambda _name: "/usr/bin/ffprobe" if which else None
    )
    stdout = raw if raw is not None else json.dumps(payload if payload is not None else {})

    def _run(_argv: object, **_kwargs: object) -> SimpleNamespace:
        if boom is not None:
            raise boom
        return SimpleNamespace(returncode=returncode, stdout=stdout)

    monkeypatch.setattr(probe.subprocess, "run", _run)


def _row(
    rel: str, kind: str, *, suffix: str = "", mtime: float = 1.0, size: int = 10
) -> OutputRow:
    """Build one catalog row for a probe test.

    Args:
        rel: Path relative to the output root.
        kind: Catalog kind.
        suffix: Suffix override for a row whose name lies about its type.
        mtime: Unix mtime; one half of the probe cache key.
        size: Byte length; the other half of the cache key.

    Returns:
        A complete catalog row, in the shape
        :func:`ez_outputs.probe.detail_lines` takes.
    """
    return {
        "rel": rel,
        "name": Path(rel).name,
        "kind": kind,
        "size": size,
        "mtime": mtime,
        "suffix": suffix or Path(rel).suffix.lower(),
        "parent": str(Path(rel).parent) if "/" in rel else "",
    }


def test_classify_names_midi_and_qc_reports() -> None:
    """MIDI is a kind of its own; only ``qc.json`` is a report."""
    assert MIDI_SUFFIXES == frozenset({".mid", ".midi"})
    assert REPORT_FILENAMES == frozenset({"qc.json"})
    assert kind_of(".mid") == "midi"
    assert kind_of(".MIDI") == "midi"
    assert kind_of(".json") is None
    assert report_kind_of("qc.json") == "report"
    assert report_kind_of("QC.json") == "report"
    assert report_kind_of("state.json") is None
    assert report_kind_of("scene.json") is None
    assert report_kind_of("workflow.json") is None
    assert report_kind_of("song.flac.meta.json") is None
    assert classify("qc.json", ".json") == "report"
    assert classify("state.json", ".json") is None
    assert classify("ez_still_00001_.png", ".png") == "image"
    assert classify("notes.txt", ".txt") is None


def test_list_outputs_surfaces_midi_and_reports_only(tmp_path: Path) -> None:
    """A batch of takes, a MIDI, and a QC report list; machine JSON stays hidden."""
    root = tmp_path / "out"
    _touch(root / "songs" / "ez_breakwater_theme_00001_.mid", _midi(4))
    _touch(root / "dubs" / "ep1" / "qc.json", b'{"ok": true, "checks": []}')
    _touch(root / "dubs" / "ep1" / "state.json", b'{"status": "done"}')
    _touch(root / "dubs" / "ep1" / "scene.json", b"{}")
    _touch(root / "dubs" / "ep1" / "workflow.json", b"{}")
    _touch(root / "albums" / "drift" / "01 - Drift.mp3.meta.json", b'{"artist": "x"}')
    rels = [row["rel"] for row in list_outputs(root)]
    assert "songs/ez_breakwater_theme_00001_.mid" in rels
    assert "dubs/ep1/qc.json" in rels
    assert all(not row["rel"].endswith("state.json") for row in list_outputs(root))
    assert all("scene.json" not in row["rel"] for row in list_outputs(root))
    assert all("workflow.json" not in row["rel"] for row in list_outputs(root))
    assert all("meta.json" not in row["rel"] for row in list_outputs(root))
    midi = list_outputs(root, kind="midi")
    assert [row["kind"] for row in midi] == ["midi"]
    reports = list_outputs(root, kind="report")
    assert [row["rel"] for row in reports] == ["dubs/ep1/qc.json"]


def test_reports_and_midi_stay_out_of_the_loadimage_lane(tmp_path: Path) -> None:
    """A QC report resolves for viewing but never stages as a LoadImage input."""
    root = tmp_path / "out"
    _touch(root / "dubs" / "ep1" / "qc.json", b'{"ok": true}')
    _touch(root / "dubs" / "ep1" / "state.json", b'{"status": "done"}')
    _touch(root / "songs" / "theme.mid", _midi(2))
    assert resolve_under(root, "dubs/ep1/qc.json").name == "qc.json"
    with pytest.raises(CatalogError, match="not a media"):
        resolve_under(root, "dubs/ep1/state.json")
    with pytest.raises(CatalogError, match="QC report is not a LoadImage input"):
        copy_to_input(root, "dubs/ep1/qc.json", input_dir=tmp_path / "in")
    with pytest.raises(CatalogError, match="MIDI sequence is not a LoadImage input"):
        copy_to_input(root, "songs/theme.mid", input_dir=tmp_path / "in")


def _rows(body: ListPayload) -> list[dict[str, Any]]:
    """Return one list body's rows as plain mappings.

    ``lines`` is optional on ``OutputRow``, so indexing it on the TypedDict is
    a typed-access error; widening here names what the test reads.

    Args:
        body: The ``(200, body)`` payload from ``handle_list``.

    Returns:
        The rows as plain mappings.
    """
    return [dict(row) for row in body["items"]]


def test_handle_list_reports_the_root_and_probes_the_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The payload names the absolute output root and carries card lines."""
    root = tmp_path / "out"
    _touch(root / "ez_still_hero_00001_.png", _png(1024, 768))
    _fake_ffprobe(
        monkeypatch,
        {
            "format": {"duration": "5.04"},
            "streams": [
                {"codec_type": "video", "width": 1280, "height": 720, "avg_frame_rate": "24/1"},
                {"codec_type": "audio", "codec_name": "aac"},
            ],
        },
    )
    status, payload = handle_list({}, root=root)
    assert status == 200
    assert payload["output_root"] == os.path.abspath(str(root))
    assert payload["count"] == 1
    assert _rows(payload)[0]["lines"] == ["1024 x 768"]
    _touch(root / "clip.mp4", b"junk")
    listed = handle_list({"kind": "video"}, root=root)
    assert _rows(listed[1])[0]["lines"] == [
        "1280 x 720",
        "5.0 s at 24 fps",
        "audio track",
    ]


def _graph(prompt: str = "a lighthouse at dawn", seed: int = 4611686018427387904) -> str:
    """Build a ComfyUI prompt dump as saved by SaveImage.

    Args:
        prompt: Text carried by the positive CLIP node.
        seed: KSampler seed.

    Returns:
        JSON text for a ``prompt`` chunk.
    """
    return json.dumps(
        {
            "1": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 4}},
            "2": {"class_type": "CLIPTextEncode", "inputs": {"prompt": prompt}},
        }
    )


def test_still_card_carries_prompt_and_seed_when_the_image_has_them(
    tmp_path: Path,
) -> None:
    """A ComfyUI still answers "what made this" from its own header."""
    root = tmp_path / "out"
    blob = _png(64, 32, (_txt("prompt", _graph()),))
    _touch(root / "ez_still_hero_00001_.png", blob)
    assert probe.detail_lines(root, _row("ez_still_hero_00001_.png", "image")) == [
        "64 x 32",
        f"seed {4611686018427387904}",
        '"a lighthouse at dawn"',
    ]


def test_still_card_omits_the_prompt_line_cleanly(tmp_path: Path) -> None:
    """No chunk, junk chunk, or an image without metadata costs only the line."""
    root = tmp_path / "out"
    _touch(root / "bare.png", _png(16, 9))
    assert probe.detail_lines(root, _row("bare.png", "image")) == ["16 x 9"]
    _touch(root / "junk.png", _png(16, 9, (_txt("prompt", "not json at all"),)))
    assert probe.detail_lines(root, _row("junk.png", "image")) == ["16 x 9"]
    _touch(root / "shot.jpg", _jpeg(320, 200))
    assert probe.detail_lines(root, _row("shot.jpg", "image")) == ["320 x 200"]
    _touch(root / "mystery.dat", b"random bytes here")
    assert probe.detail_lines(root, _row("mystery.dat", "image")) == []
    _touch(root / "gone.png", b"")
    assert probe.detail_lines(root, _row("no-such-file.png", "image")) == []


def test_image_dimensions_reads_every_supported_header(tmp_path: Path) -> None:
    """PNG, JPEG, GIF, and both WebP variants report size from the header."""
    root = tmp_path / "out"
    cases: dict[str, tuple[bytes, tuple[int, int] | None]] = {
        "a.png": (_png(1024, 768), (1024, 768)),
        "b.jpg": (_jpeg(1920, 1080), (1920, 1080)),
        "c.gif": (b"GIF89a" + (12).to_bytes(2, "little") + (34).to_bytes(2, "little"), (12, 34)),
        "d.gif": (b"GIF87a" + (5).to_bytes(2, "little") + (6).to_bytes(2, "little"), (5, 6)),
        "e.webp": (_webp(b"VP8 ", 100, 50), (100, 50)),
        "f.webp": (_webp(b"VP8L", 7, 3), (7, 3)),
        "g.webp": (_webp(b"VP8X", 7, 3), None),
        "h.png": (b"\x89PNG\r\n\x1a\n" + b"\x00" * 10, None),
        "i.gif": (b"GIF89a\x01", None),
        "j.jpg": (_jpeg(8, 8), (8, 8)),
        "k.jpg": (b"\xff\xd8\xff\xd0" + _jpeg(40, 20)[2:], (40, 20)),
        "l.jpg": (b"\xff\xd8\xff\xdb\x00\x01" + b"\x00" * 12, None),
        "m.jpg": (b"\xff\xd8\xff\xdb\x00\x04\x00\x00" + b"\x11" * 12, None),
        "n.jpg": (b"\xff\xd8\xff", None),
        "o.webp": (b"RIFF\x00\x00\x00\x00WEBPVP8 \x00\x00\x00\x00", None),
        "p.webp": (b"RIFF\x00\x00\x00\x00WEBPVP8L\x00\x00\x00\x00\x2f\x00", None),
        "q.txt": (b"no header at all", None),
    }
    for name, (blob, want) in cases.items():
        _touch(root / name, blob)
        assert probe.image_dimensions(root / name) == want, name
    assert probe.image_dimensions(root / "absent.png") is None
    assert probe.image_dimensions(root) is None


def test_png_text_chunks_decodes_every_chunk_shape(tmp_path: Path) -> None:
    """tEXt, zTXt, and both iTXt modes decode; junk chunks are skipped."""
    root = tmp_path / "out"
    graph = _graph(prompt="night market rain")
    blob = _png(
        8,
        8,
        (
            _txt("parameters", "steps: 4"),
            _ztxt("prompt", zlib.compress(graph.encode("utf-8"))),
            _itxt("comment", b"plain", compressed=False),
            _itxt("note", zlib.compress(b"packed"), compressed=True),
            _chunk(b"tEXt", b"\x00no keyword"),
            _chunk(b"tEXt", b"\x00\x00\x00"),
            _ztxt("broken", b"not a deflate stream"),
            _ztxt("badutf", zlib.compress(b"\xff\xfe")),
            _chunk(b"iTXt", b"kw\x00\x00"),
            _chunk(b"iTXt", b"two\x00ab"),
            _chunk(b"iTXt", b"short"),
            _chunk(b"iTXt", b"kw\x00\x01\x00en\x00\x00" + b"not deflate"),
            _chunk(b"pHYs", b"\x00" * 9),
        ),
    )
    _touch(root / "rich.png", blob)
    found = probe.png_text_chunks(root / "rich.png")
    assert found["parameters"] == "steps: 4"
    assert json.loads(found["prompt"])["1"]["inputs"]["seed"] == 4611686018427387904
    assert found["comment"] == "plain"
    assert found["note"] == "packed"
    assert "broken" not in found
    assert "badutf" not in found
    assert "kw" not in found
    assert "two" not in found
    assert "short" not in found
    assert "pHYs" not in found
    _touch(root / "flat.png", b"not a png")
    assert probe.png_text_chunks(root / "flat.png") == {}
    assert probe.png_text_chunks(root / "absent.png") == {}
    _touch(root / "short.png", _png(4, 4)[:20])
    assert probe.png_text_chunks(root / "short.png") == {}
    _touch(root / "half.png", _png(4, 4)[:-4])
    assert probe.png_text_chunks(root / "half.png") == {}


def test_prompt_metadata_survives_a_mangled_graph() -> None:
    """A graph dump that is absent, wrong-shaped, or huge yields sane lines."""
    assert probe.prompt_metadata({}) == ("", None)
    assert probe.prompt_metadata({"prompt": "   "}) == ("", None)
    junk: dict[str, Any] = {"prompt": 42}
    assert probe.prompt_metadata(junk) == ("", None)
    assert probe.prompt_metadata({"prompt": "{oops"}) == ("", None)
    assert probe.prompt_metadata({"prompt": "[1, 2]"}) == ("", None)
    odd = json.dumps(
        {
            "0": ["not", "a", "node"],
            "1": {"class_type": "KSampler", "inputs": "nope"},
            "2": {"class_type": "KSampler", "inputs": {"seed": "0"}},
            "3": {"class_type": "EmptyLatentImage", "inputs": {"seed": 9}},
            "4": {"class_type": "KSampler", "inputs": {"prompt": "   "}},
        }
    )
    assert probe.prompt_metadata({"prompt": odd}) == ("", None)
    two_step = json.dumps(
        {
            "1": {"class_type": "CLIPTextEncode", "inputs": {"prompt": "first"}},
            "2": {"class_type": "KSampler", "inputs": {"seed": "0"}},
            "3": {"class_type": "KSampler", "inputs": {"seed": 7}},
        }
    )
    assert probe.prompt_metadata({"prompt": two_step}) == ("first", 7)
    long_prompt = json.dumps(
        {"1": {"class_type": "KSampler", "inputs": {"seed": 90, "prompt": "ab " * 90}}}
    )
    text, seed = probe.prompt_metadata({"workflow": long_prompt})
    assert seed == 90
    assert text.endswith("...")
    assert len(text) == probe.PROMPT_CHARS
    quiet = json.dumps({"1": {"class_type": "VAEDecode", "inputs": {"prompt": "quiet"}}})
    assert probe.prompt_metadata({"prompt": quiet}) == ("quiet", None)


def _video_payload(**over: Any) -> dict[str, Any]:
    """Build an ffprobe payload for one clip.

    Args:
        **over: Fields merged into the video stream.

    Returns:
        A payload with one video stream and no audio stream.
    """
    video: dict[str, Any] = {
        "codec_type": "video",
        "width": 1280,
        "height": 720,
        "avg_frame_rate": "24",
    }
    video.update(over)
    return {"format": {"duration": "5.04"}, "streams": [video]}


def test_video_card_answers_every_question_the_contract_asks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Size, length, frame rate, and whether the clip can be heard."""
    root = tmp_path / "out"
    _touch(root / "clip.mp4", b"junk")
    row = _row("clip.mp4", "video")
    with_audio = _video_payload()
    with_audio["streams"].append({"codec_type": "audio", "codec_name": "aac"})
    _fake_ffprobe(monkeypatch, with_audio)
    assert probe.detail_lines(root, row) == [
        "1280 x 720",
        "5.0 s at 24 fps",
        "audio track",
    ]
    probe.clear_cache()
    _fake_ffprobe(monkeypatch, _video_payload(avg_frame_rate="24000/1001"))
    assert probe.detail_lines(root, row) == [
        "1280 x 720",
        "5.0 s at 23.976 fps",
        "silent - no audio track",
    ]
    probe.clear_cache()
    _fake_ffprobe(monkeypatch, _video_payload(width="abc", height=True, avg_frame_rate="0"))
    assert probe.detail_lines(root, row) == ["5.0 s", "silent - no audio track"]
    probe.clear_cache()
    _fake_ffprobe(monkeypatch, {"streams": [_video_payload().get("streams", [{}])[0]]})
    assert probe.detail_lines(root, row) == ["1280 x 720", "24 fps", "silent - no audio track"]
    probe.clear_cache()
    _fake_ffprobe(
        monkeypatch,
        {
            "format": "no",
            "streams": [
                {"codec_type": "video", "duration": "182", "avg_frame_rate": "junk"},
                "junk",
            ],
        },
    )
    assert probe.detail_lines(root, row) == ["3:02", "silent - no audio track"]
    probe.clear_cache()
    _fake_ffprobe(
        monkeypatch,
        {
            "format": {"duration": "junk"},
            "streams": [{"codec_type": "video", "duration": "182", "avg_frame_rate": "24/0"}],
        },
    )
    assert probe.detail_lines(root, row) == ["3:02", "silent - no audio track"]
    probe.clear_cache()
    _fake_ffprobe(monkeypatch, {"streams": "not a list"})
    assert probe.detail_lines(root, row) == []


def test_video_card_still_lists_when_ffprobe_cannot_answer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Missing binary, slow binary, and a failing binary all cost the lines only."""
    root = tmp_path / "out"
    _touch(root / "clip.mp4", b"junk")
    row = _row("clip.mp4", "video")
    cases: list[dict[str, Any]] = [
        {"which": False},
        {"boom": subprocess.TimeoutExpired(cmd="ffprobe", timeout=1)},
        {"boom": OSError("ffprobe vanished")},
        {"payload": {}, "returncode": 1},
        {"raw": "not json"},
        {"raw": "[1, 2]"},
        {"raw": ""},
    ]
    for kwargs in cases:
        probe.clear_cache()
        _fake_ffprobe(monkeypatch, **kwargs)
        assert probe.detail_lines(root, row) == [], kwargs


def test_audio_card_reports_length_rate_and_the_stamped_tags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Music answers with length, sample rate, and the Artist - Album - Track line."""
    root = tmp_path / "out"
    _touch(root / "albums" / "drift" / "01 - Drift.mp3", b"junk")
    row = _row("albums/drift/01 - Drift.mp3", "audio")
    payload = {
        "format": {"duration": "182.4"},
        "streams": [
            {
                "codec_type": "audio",
                "sample_rate": "44100",
                "tags": {"artist": "Tagged", "album": "Tagged Album", "title": "Tagged Track"},
            },
            {"codec_type": "video"},
        ],
    }
    _fake_ffprobe(monkeypatch, payload)
    assert probe.detail_lines(root, row) == [
        "3:02",
        "44.1 kHz",
        "Tagged - Tagged Album - Tagged Track",
    ]
    probe.clear_cache()
    _touch(
        root / "albums" / "drift" / "01 - Drift.mp3.meta.json",
        b'{"artist": "Beatwater", "album": "Drift", "title": "Drift", "track": "1"}',
    )
    assert probe.detail_lines(root, row) == [
        "3:02",
        "44.1 kHz",
        "Beatwater - Drift - Drift",
    ]
    probe.clear_cache()
    _fake_ffprobe(monkeypatch, {"streams": [{"codec_type": "audio", "sample_rate": "48000"}]})
    assert probe.detail_lines(root, row) == ["48 kHz", "Beatwater - Drift - Drift"]
    (root / "albums" / "drift" / "01 - Drift.mp3.meta.json").unlink()
    probe.clear_cache()
    assert probe.detail_lines(root, row) == ["48 kHz"]
    probe.clear_cache()
    _fake_ffprobe(monkeypatch, {"streams": [{"codec_type": "audio", "tags": "nope"}]})
    assert probe.detail_lines(root, row) == []
    probe.clear_cache()
    _fake_ffprobe(
        monkeypatch,
        {"streams": [{"codec_type": "audio"}], "format": {"duration": "1.2"}},
    )
    assert probe.detail_lines(root, row) == ["1.2 s"]


def test_dub_card_names_both_languages_and_the_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dub master says what it was translated from and how QC scored it."""
    root = tmp_path / "out"
    job = root / "dubs" / "ep1"
    _touch(job / "voice.wav", b"junk")
    _fake_ffprobe(
        monkeypatch,
        {"format": {"duration": "1.2"}, "streams": [{"codec_type": "audio"}]},
    )
    row = _row("dubs/ep1/voice.wav", "audio")
    _touch(job / "state.json", b'{"source_language": "en", "target_language": "es"}')
    _touch(job / "qc.json", b'{"ok": false, "checks": [{"level": "fail", "rule": "lip-sync"}]}')
    assert probe.detail_lines(root, row) == ["dub: English -> Spanish", "dub QC fail"]
    _touch(job / "qc.json", b'{"ok": true, "checks": [{"level": "warn", "rule": "loudness"}]}')
    probe.clear_cache()
    assert probe.detail_lines(root, row) == [
        "dub: English -> Spanish",
        "dub QC pass - 1 warning(s)",
    ]
    (job / "qc.json").unlink()
    probe.clear_cache()
    assert probe.detail_lines(root, row) == ["dub: English -> Spanish"]
    _touch(job / "state.json", b'{"source_language": "auto", "target_language": "xx"}')
    probe.clear_cache()
    assert probe.detail_lines(root, row) == ["dub: source -> xx"]
    _touch(job / "state.json", b'{"status": "running"}')
    probe.clear_cache()
    assert probe.detail_lines(root, row) == ["1.2 s"]
    (job / "state.json").unlink()
    probe.clear_cache()
    assert probe.detail_lines(root, row) == ["1.2 s"]


def test_midi_card_says_what_it_is_and_how_many_tracks(tmp_path: Path) -> None:
    """A ``.mid`` is a plain-language line plus the track count when parseable."""
    assert probe.MIDI_NOTE == "MIDI sequence - opens in a DAW"
    root = tmp_path / "out"
    _touch(root / "songs" / "theme.mid", _midi(4))
    assert probe.detail_lines(root, _row("songs/theme.mid", "midi")) == [
        probe.MIDI_NOTE,
        "4 tracks",
    ]
    _touch(root / "songs" / "one.mid", _midi(0))
    assert probe.detail_lines(root, _row("songs/one.mid", "midi")) == [probe.MIDI_NOTE]
    _touch(root / "songs" / "bad.mid", _midi(3, magic=b"XTMd"))
    assert probe.detail_lines(root, _row("songs/bad.mid", "midi")) == [probe.MIDI_NOTE]
    _touch(root / "songs" / "cut.mid", _midi(4)[:11])
    assert probe.detail_lines(root, _row("songs/cut.mid", "midi")) == [probe.MIDI_NOTE]


def test_mesh_card_names_blender_and_the_plate_it_came_from(tmp_path: Path) -> None:
    """A GLB says it opens in Blender, plus its source still when stamped."""
    root = tmp_path / "out"
    _touch(root / "assets" / "cup.glb", b"glTF")
    assert probe.detail_lines(root, _row("assets/cup.glb", "model3d")) == [
        "GLB - opens in Blender, no in-browser preview"
    ]
    _touch(root / "assets" / "cup.glb.json", b'{"source_still": "plates/hero.png"}')
    probe.clear_cache()
    assert probe.detail_lines(root, _row("assets/cup.glb", "model3d")) == [
        "GLB - opens in Blender, no in-browser preview",
        "from hero.png",
    ]
    (root / "assets" / "cup.glb.json").unlink()
    _touch(root / "assets" / "cup.json", b'{"image": "C:\\\\plates\\\\hero.jpg"}')
    probe.clear_cache()
    assert probe.detail_lines(root, _row("assets/cup.glb", "model3d"))[-1] == "from hero.jpg"
    _touch(root / "assets" / "cup.json", b'["not", "a", "map"]')
    probe.clear_cache()
    assert len(probe.detail_lines(root, _row("assets/cup.glb", "model3d"))) == 1
    _touch(root / "assets" / "cup.json", b'{"image": "   "}')
    probe.clear_cache()
    assert len(probe.detail_lines(root, _row("assets/cup.glb", "model3d"))) == 1
    _touch(root / "assets" / "lamp.gltf", b"glTF")
    assert probe.detail_lines(root, _row("assets/lamp.gltf", "model3d", suffix=".gltf")) == [
        "GLTF - opens in Blender, no in-browser preview"
    ]


def test_report_card_renders_the_verdict(tmp_path: Path) -> None:
    """``qc.json`` answers with the verdict and the rules that fired."""
    root = tmp_path / "out"
    qc = root / "dubs" / "ep1" / "qc.json"
    _touch(qc, b'{"ok": true}')
    assert probe.detail_lines(root, _row("dubs/ep1/qc.json", "report")) == ["QC pass"]
    _touch(qc, b'{"ok": true, "checks": "nope"}')
    probe.clear_cache()
    assert probe.detail_lines(root, _row("dubs/ep1/qc.json", "report")) == ["QC pass"]
    _touch(
        qc,
        b'{"ok": true, "checks": [{"level": "warn", "rule": "loud"},'
        b' {"level": "warn", "rule": "sync"}, {"level": "info", "rule": "a"},'
        b' {"level": "warn", "rule": "b"}, "junk", {"level": "warn"}]}',
    )
    probe.clear_cache()
    assert probe.detail_lines(root, _row("dubs/ep1/qc.json", "report")) == [
        "QC pass - 4 warning(s)",
        "loud; sync; a",
    ]
    _touch(qc, b"[1, 2]")
    probe.clear_cache()
    assert probe.detail_lines(root, _row("dubs/ep1/qc.json", "report")) == []
    probe.clear_cache()
    assert probe.detail_lines(root, _row("dubs/ep1/absent.json", "report")) == []
    assert probe.detail_lines(root, _row("dubs/ep1/other.txt", "text")) == []


def test_dub_language_label_falls_back_when_the_dub_pack_is_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without ``ez_dub`` the card prints the code it was given."""
    root = tmp_path / "out"
    job = root / "dubs" / "ep2"
    _touch(job / "voice.wav", b"junk")
    _touch(job / "state.json", b'{"source_language": "en", "target_language": "ja"}')
    probe.clear_cache()
    assert probe.detail_lines(root, _row("dubs/ep2/voice.wav", "audio")) == [
        "dub: English -> Japanese"
    ]
    monkeypatch.setitem(sys.modules, "ez_dub.pipeline", None)
    probe.clear_cache()
    assert probe.detail_lines(root, _row("dubs/ep2/voice.wav", "audio")) == [
        "dub: en -> ja"
    ]


def test_detail_lines_caches_by_path_mtime_and_size(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A refresh re-probes nothing, and the cache stays bounded."""
    root = tmp_path / "out"
    _touch(root / "a.png", _png(8, 8))
    calls: list[str] = []
    real = probe._probe_row

    def _spy(base: Path, path: Path, row: OutputRow) -> list[str]:
        calls.append(str(path))
        return real(base, path, row)

    monkeypatch.setattr(probe, "_probe_row", _spy)
    row = _row("a.png", "image")
    assert probe.detail_lines(root, row) == ["8 x 8"]
    assert probe.detail_lines(root, row) == ["8 x 8"]
    assert len(calls) == 1
    stale = _row("a.png", "image", mtime=2.0)
    assert probe.detail_lines(root, stale) == ["8 x 8"]
    assert len(calls) == 2
    monkeypatch.setattr(probe, "CACHE_MAX", 2)
    _touch(root / "b.png", _png(9, 9))
    _touch(root / "c.png", _png(10, 10))
    probe.detail_lines(root, _row("b.png", "image"))
    probe.detail_lines(root, _row("c.png", "image"))
    assert len(probe._CACHE) == 2

    def _boom(*_args: object) -> list[str]:
        raise RuntimeError("probe exploded")

    monkeypatch.setattr(probe, "_probe_row", _boom)
    assert probe.detail_lines(root, _row("a.png", "image", mtime=99.0)) == []


def test_outputs_js_surfaces_every_kind_and_answers_where_the_file_is() -> None:
    """The pane labels MIDI and reports, groups takes, and prints the output root."""
    body = _outputs_js()
    assert 'midi: "MIDI"' in body
    assert 'report: "Report"' in body
    assert '["midi", "MIDI"]' in body
    assert '["report", "Reports"]' in body
    assert "Download it to open in a DAW" in body
    assert "no in-browser preview" in body
    # The kind that cannot stage for LoadImage downloads instead.
    assert 'row.kind === "midi" || row.kind === "report"' in body
    # Batch grouping and the render-time human title.
    assert "function groupRows(" in body
    assert "function titleOf(" in body
    assert '" files"' in body
    assert "take " in body
    # "Where is my file": the root once in the header, a copy action per card.
    assert "output_root" in body
    assert "ez-out-root" in body
    assert 'makeButton("Copy path", "ez-out-btn"' in body
    assert "function absolutePath(" in body
    # Selection still keys off the per-file marker, so nested takes stay reachable.
    assert 'querySelectorAll("[data-rel]")' in body

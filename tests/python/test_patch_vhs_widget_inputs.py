"""Unit tests for docker/patch_vhs_widget_inputs.py (100% line coverage).

Hermetic: fake ComfyUI trees under pytest tmp_path. No GPU, network, or
real VideoHelperSuite clone.
"""

from __future__ import annotations

import sys
from pathlib import Path

import patch_vhs_widget_inputs as patch_mod
import pytest

SAMPLE = (
    "import { app } from '../../../scripts/app.js'\n"
    "import { api } from '../../../scripts/api.js'\n"
    "import { setWidgetConfig } from '../../../extensions/core/widgetInputs.js'\n"
    'import { applyTextReplacements } from "../../../scripts/utils.js";\n'
    "\n"
    "function chainCallback() {\n"
    "    return;\n"
    "}\n"
)

ALREADY_MODERN = (
    "import { app } from '../../../scripts/app.js'\n"
    "import { api } from '../../../scripts/api.js'\n"
    'import { applyTextReplacements } from "../../../scripts/utils.js";\n'
    "const setWidgetConfig = window.comfyAPI?.widgetInputs?.setWidgetConfig "
    "?? (() => {});\n"
    "\n"
    "function chainCallback() {\n"
    "    return;\n"
    "}\n"
)


def _core_path(tmp_path: Path) -> Path:
    dest = tmp_path / "custom_nodes" / "ComfyUI-VideoHelperSuite" / "web" / "js"
    dest.mkdir(parents=True, exist_ok=True)
    return dest / "VHS.core.js"


def _write_core(tmp_path: Path, text: str, newline: str = "\n") -> Path:
    target = _core_path(tmp_path)
    target.write_text(text.replace("\n", newline), encoding="utf-8", newline="")
    return target


def test_skip_missing_pack(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = patch_mod.apply_patch(tmp_path)
    assert rc == 0
    assert "skip" in capsys.readouterr().err


def test_skip_missing_core(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pack = tmp_path / "custom_nodes" / "ComfyUI-VideoHelperSuite"
    pack.mkdir(parents=True, exist_ok=True)
    rc = patch_mod.apply_patch(tmp_path)
    assert rc == 0
    err = capsys.readouterr().err
    assert "skip" in err
    assert "VHS.core.js" in err


def test_apply_rewrites_import(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = _write_core(tmp_path, SAMPLE)
    assert patch_mod.apply_patch(tmp_path) == 0
    text = target.read_text(encoding="utf-8")
    assert patch_mod.MARKER in text
    assert "widgetInputs.js" not in text
    assert "scripts/app.js" in text
    assert "scripts/api.js" in text
    assert "scripts/utils.js" in text
    assert "window.comfyAPI" in text
    assert text.find("import {") < text.find("const setWidgetConfig")
    assert "rewrote" in capsys.readouterr().out


@pytest.mark.parametrize(
    "import_line",
    [
        "import { setWidgetConfig } from '../../../extensions/core/widgetInputs.js'",
        'import { setWidgetConfig } from "../../../extensions/core/widgetInputs.js";',
        'import { setWidgetConfig } from "/extensions/core/widgetInputs.js";',
    ],
)
def test_import_quote_and_path_variants(
    tmp_path: Path, import_line: str
) -> None:
    body = (
        "import { app } from '../../../scripts/app.js'\n"
        "import { api } from '../../../scripts/api.js'\n"
        f"{import_line}\n"
        'import { applyTextReplacements } from "../../../scripts/utils.js";\n'
        "function chainCallback() { return; }\n"
    )
    target = _write_core(tmp_path, body)
    assert patch_mod.apply_patch(tmp_path) == 0
    text = target.read_text(encoding="utf-8")
    assert patch_mod.MARKER in text
    assert "widgetInputs.js" not in text


def test_blank_line_between_imports(tmp_path: Path) -> None:
    body = (
        "import { app } from '../../../scripts/app.js'\n"
        "\n"
        "import { api } from '../../../scripts/api.js'\n"
        "import { setWidgetConfig } from '../../../extensions/core/widgetInputs.js'\n"
        'import { applyTextReplacements } from "../../../scripts/utils.js";\n'
        "function chainCallback() { return; }\n"
    )
    target = _write_core(tmp_path, body)
    assert patch_mod.apply_patch(tmp_path) == 0
    text = target.read_text(encoding="utf-8")
    assert patch_mod.MARKER in text
    assert text.find("import { app }") < text.find("const setWidgetConfig")
    assert text.find("import { api }") < text.find("const setWidgetConfig")
    assert text.find("applyTextReplacements") < text.find("const setWidgetConfig")


def test_idempotent(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_core(tmp_path, SAMPLE)
    assert patch_mod.apply_patch(tmp_path) == 0
    capsys.readouterr()
    assert patch_mod.apply_patch(tmp_path) == 0
    assert "already applied" in capsys.readouterr().out


def test_already_modern(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = _write_core(tmp_path, ALREADY_MODERN)
    assert patch_mod.apply_patch(tmp_path) == 0
    assert target.read_text(encoding="utf-8") == ALREADY_MODERN
    assert "already modern" in capsys.readouterr().out


def test_unknown_header_warns(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = _write_core(tmp_path, "function chainCallback() { return; }\n")
    original = target.read_text(encoding="utf-8")
    assert patch_mod.apply_patch(tmp_path) == 0
    assert target.read_text(encoding="utf-8") == original
    assert "WARNING" in capsys.readouterr().err


def test_comment_mentions_widget_inputs_warns(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    body = (
        "import { app } from '../../../scripts/app.js'\n"
        "import { api } from '../../../scripts/api.js'\n"
        'import { applyTextReplacements } from "../../../scripts/utils.js";\n'
        "// leftover note about widgetInputs.js\n"
        "function chainCallback() { return; }\n"
    )
    target = _write_core(tmp_path, body)
    original = target.read_text(encoding="utf-8")
    assert patch_mod.apply_patch(tmp_path) == 0
    assert target.read_text(encoding="utf-8") == original
    assert "WARNING" in capsys.readouterr().err


def test_validity_check_aborts_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = _write_core(tmp_path, SAMPLE)
    original = target.read_text(encoding="utf-8")
    monkeypatch.setattr(patch_mod, "_looks_valid", lambda *_a, **_k: False)
    assert patch_mod.apply_patch(tmp_path) == 0
    assert target.read_text(encoding="utf-8") == original
    assert "validity check" in capsys.readouterr().err


def test_crlf_line_endings(tmp_path: Path) -> None:
    target = _write_core(tmp_path, SAMPLE, newline="\r\n")
    assert patch_mod.apply_patch(tmp_path) == 0
    raw = target.read_bytes()
    assert b"\r\n" in raw
    assert patch_mod.MARKER.encode() in raw
    assert b"widgetInputs.js" not in raw


def test_import_at_eof_without_newline(tmp_path: Path) -> None:
    body = (
        "import { app } from '../../../scripts/app.js'\n"
        "import { api } from '../../../scripts/api.js'\n"
        "import { setWidgetConfig } from '../../../extensions/core/widgetInputs.js'\n"
        'import { applyTextReplacements } from "../../../scripts/utils.js";'
    )
    target = _write_core(tmp_path, body)
    target.write_text(body, encoding="utf-8", newline="")
    assert patch_mod.apply_patch(tmp_path) == 0
    text = target.read_text(encoding="utf-8")
    assert patch_mod.MARKER in text
    assert "widgetInputs.js" not in text


def test_looks_valid_helper() -> None:
    good = patch_mod._replacement("\n")  # noqa: SLF001
    header = (
        "import { app } from '../../../scripts/app.js'\n"
        "import { api } from '../../../scripts/api.js'\n"
        'import { applyTextReplacements } from "../../../scripts/utils.js";\n'
    )
    assert patch_mod._looks_valid(header + good) is True  # noqa: SLF001
    assert patch_mod._looks_valid(header) is False  # noqa: SLF001
    assert patch_mod._looks_valid(good) is False  # noqa: SLF001
    mixed = (
        header
        + good
        + "import { leftover } from '../../../extensions/core/widgetInputs.js'\n"
    )
    assert patch_mod._looks_valid(mixed) is False  # noqa: SLF001
    no_api = (
        "import { app } from '../../../scripts/app.js'\n"
        'import { applyTextReplacements } from "../../../scripts/utils.js";\n'
        + good
    )
    assert patch_mod._looks_valid(no_api) is False  # noqa: SLF001
    no_utils = (
        "import { app } from '../../../scripts/app.js'\n"
        "import { api } from '../../../scripts/api.js'\n"
        + good
    )
    assert patch_mod._looks_valid(no_utils) is False  # noqa: SLF001
    marked_no_api_obj = header + f"const setWidgetConfig = 1; // {patch_mod.MARKER}\n"
    assert patch_mod._looks_valid(marked_no_api_obj) is False  # noqa: SLF001
    marked_no_shim = header + f"window.comfyAPI = {{}}; // {patch_mod.MARKER}\n"
    assert patch_mod._looks_valid(marked_no_shim) is False  # noqa: SLF001
    shim_first = good + header
    assert patch_mod._looks_valid(shim_first) is False  # noqa: SLF001


def test_replacement_contains_marker() -> None:
    block = patch_mod._replacement("\n")  # noqa: SLF001
    assert patch_mod.MARKER in block
    assert "widgetInputs.js" not in block
    assert "window.comfyAPI" in block


def test_header_import_end_edges() -> None:
    assert patch_mod._header_import_end("") == 0  # noqa: SLF001
    assert patch_mod._header_import_end("function x() {}\n") == 0  # noqa: SLF001
    text = "import { app } from '../../../scripts/app.js'\n\nfunction x() {}\n"
    end = patch_mod._header_import_end(text)  # noqa: SLF001
    assert text[:end].startswith("import")
    assert "function" not in text[:end]


def test_consumed_newline_variants() -> None:
    needle = "abc"
    assert patch_mod._consumed_and_newline("abc\r\nX", needle, 0) == (  # noqa: SLF001
        "abc\r\n",
        "\r\n",
    )
    assert patch_mod._consumed_and_newline("abc\nX", needle, 0) == (  # noqa: SLF001
        "abc\n",
        "\n",
    )
    assert patch_mod._consumed_and_newline("abc", needle, 0) == (needle, "\n")  # noqa: SLF001


def test_main_default_and_arg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_core(tmp_path, SAMPLE)
    assert patch_mod.main([str(tmp_path)]) == 0
    monkeypatch.setattr(sys, "argv", ["patch", str(tmp_path)])
    assert patch_mod.main() == 0


def test_main_no_args_default_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", ["patch"])
    assert patch_mod.main([]) == 0


def test_module_main_entrypoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import runpy

    _write_core(tmp_path, SAMPLE)
    monkeypatch.setattr(sys, "argv", ["patch_vhs_widget_inputs.py", str(tmp_path)])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(
            str(
                Path(__file__).resolve().parents[2]
                / "docker"
                / "patch_vhs_widget_inputs.py"
            ),
            run_name="__main__",
        )
    assert exc.value.code == 0

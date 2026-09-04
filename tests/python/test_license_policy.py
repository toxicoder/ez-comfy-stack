"""Grep the US-safe model license table (not legal advice).

Hermetic: stdlib only. No Comfy runtime, network, or GPU.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LICENSE_ROOT = ROOT / "LICENSE-MODELS.md"
LICENSE_DOCS = ROOT / "docs" / "licenses.md"

HEADER_COLS = (
    "model",
    "HF repo",
    "license name",
    "US self-host OK?",
    "monetized YouTube OK?",
    "$ threshold",
    "attribution",
    "distillation ban",
    "default download?",
)

REQUIRED_SNIPPETS = (
    "Apache 2.0",
    "FLUX.2 Klein 4B distilled FP8",
    "black-forest-labs/FLUX.2-klein-4b-fp8",
    "Z-Image Turbo",
    "Wan 2.2 TI2V-5B",
    "Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
    "Wan 2.2 A14B",
    "LTX-2.5 distilled INT8-convrot",
    "Lightricks/LTX-2.5",
    "LTX Community License",
    "$10M COMPANY annual revenue",
    "LTX-2.3 distilled FP8",
    "FLUX.2 Klein 9B",
    "FLUX Non-Commercial",
    "FLUX.2 [dev]",
    "black-forest-labs/FLUX.2-dev",
    "MiniMax H3",
    "US Excluded Territory",
    "Wan 2.5",
    "Seedance",
    "Kling",
    "Veo",
    "flux-2-klein-4b-fp8.safetensors",
    "qwen_3_4b.safetensors",
    "flux2-vae.safetensors",
    "wan2.2_ti2v_5B_fp16.safetensors",
    "wan2.2_vae.safetensors",
    "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
    "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors",
    "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors",
    "ltx-2.5-video-vae-bf16.safetensors",
    "ltx-2.5-audio-vae-bf16.safetensors",
    "Qwen3-4B-Instruct-2507",
    "Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
    "unsloth/Qwen3-4B-Instruct-2507-GGUF",
    "Kokoro-82M",
    "hexgrad/Kokoro-82M",
    "ACE-Step 1.5",
    "Comfy-Org/ace_step_1.5_ComfyUI_files",
    "Chatterbox",
    "ResembleAI/chatterbox",
    "Qwen3-TTS 0.6B",
    "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    "F5-TTS official weights",
    "CC-BY-NC-4.0",
    "Coqui XTTS v2",
    "CPML",
    "Echo-TTS",
    "CC-BY-NC-SA",
    "Fish Audio S2",
    "Higgs Boson",
    "TTS-Audio-Suite",
    "OldTimeRadio",
    "Not legal advice",
)

# Default-pack rows must say Yes in the last column of their table line.
DEFAULT_YES_MODELS = (
    "FLUX.2 Klein 4B distilled FP8",
    "Wan 2.2 TI2V-5B",
    "LTX-2.5 distilled INT8-convrot",
    "Qwen3-4B-Instruct-2507 Q4_K_M GGUF",
)

DEFAULT_NO_MODELS = (
    "Z-Image Turbo",
    "Wan 2.2 A14B T2V/I2V",
    "LTX-2.3 distilled FP8",
    "FLUX.2 Klein 9B",
    "FLUX.2 [dev]",
    "MiniMax H3",
    "HunyuanVideo 1.5",
    "LongCat-Video",
    "Kokoro-82M",
    "ACE-Step 1.5 / 1.5 XL",
    "Chatterbox / Multilingual v3 / Turbo",
    "Qwen3-TTS 0.6B",
    "F5-TTS official weights",
    "Coqui XTTS v2",
    "Echo-TTS",
    "Fish Audio S2",
    "Higgs Boson",
    "TTS-Audio-Suite",
    "OldTimeRadio",
)


def _read(path: Path) -> str:
    assert path.is_file(), path
    return path.read_text(encoding="utf-8")


def test_license_files_exist() -> None:
    assert LICENSE_ROOT.is_file(), LICENSE_ROOT
    assert LICENSE_DOCS.is_file(), LICENSE_DOCS


def test_table_header_columns_in_both_files() -> None:
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        text = _read(path)
        for col in HEADER_COLS:
            assert col in text, f"{path.name} missing column {col!r}"


def test_required_policy_snippets_in_both_files() -> None:
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        text = _read(path)
        for snippet in REQUIRED_SNIPPETS:
            assert snippet in text, f"{path.name} missing {snippet!r}"


def _table_rows(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if ln.startswith("| ") and "---" not in ln]


def test_default_download_yes_no_flags() -> None:
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        rows = _table_rows(_read(path))
        by_model = {}
        for row in rows:
            cells = [c.strip() for c in row.strip("|").split("|")]
            if len(cells) < 9:
                continue
            by_model[cells[0]] = cells[8]
        for name in DEFAULT_YES_MODELS:
            assert name in by_model, f"{path.name} missing row {name!r}"
            assert by_model[name] == "Yes", f"{path.name} {name!r} default={by_model[name]!r}"
        for name in DEFAULT_NO_MODELS:
            assert name in by_model, f"{path.name} missing row {name!r}"
            assert by_model[name] == "No", f"{path.name} {name!r} default={by_model[name]!r}"


def test_ltx_is_not_called_apache() -> None:
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        for row in _table_rows(_read(path)):
            if "LTX-2.5" in row or "LTX-2.3" in row:
                assert "Apache 2.0" not in row, f"{path.name} must not call LTX Apache: {row}"
                assert "LTX Community License" in row


def test_klein_9b_not_youtube_ok() -> None:
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        for row in _table_rows(_read(path)):
            if "FLUX.2 Klein 9B" in row:
                cells = [c.strip() for c in row.strip("|").split("|")]
                assert cells[4] == "No", row
                assert "FLUX Non-Commercial" in row


def test_banned_podcast_rows_us_not_ok() -> None:
    names = (
        "F5-TTS official weights",
        "Coqui XTTS v2",
        "Echo-TTS",
        "Fish Audio S2",
        "Higgs Boson",
        "TTS-Audio-Suite",
        "OldTimeRadio",
    )
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        rows = _table_rows(_read(path))
        by_model = {}
        for row in rows:
            cells = [c.strip() for c in row.strip("|").split("|")]
            if len(cells) < 9:
                continue
            by_model[cells[0]] = cells
        for name in names:
            assert name in by_model, f"{path.name} missing row {name!r}"
            assert by_model[name][3].startswith("No"), by_model[name]
            assert by_model[name][4] == "No", by_model[name]
            assert by_model[name][8] == "No", by_model[name]


def test_minimax_h3_us_excluded() -> None:
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        text = _read(path)
        assert "US Excluded Territory for weights AND outputs" in text or (
            "US Excluded Territory" in text and "MiniMax H3" in text
        )
        for row in _table_rows(text):
            if row.startswith("| MiniMax H3 "):
                cells = [c.strip() for c in row.strip("|").split("|")]
                assert cells[3].startswith("No"), row
                assert cells[4] == "No", row
                assert cells[8] == "No", row

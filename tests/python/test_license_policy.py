"""Grep the US-safe model license table (not legal advice).

Hermetic: stdlib only. No Comfy runtime, network, or GPU.
"""

from __future__ import annotations

from pathlib import Path

from _docs_paths import docs_file

ROOT = Path(__file__).resolve().parents[2]
LICENSE_ROOT = ROOT / "LICENSE-MODELS.md"
LICENSE_DOCS = docs_file(ROOT / "docs" / "licenses.md")

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
    "FLUX 3 Image Klein",
    "FLUX Kommunity License",
    "black-forest-labs/flux-3-image-klein-comfy",
    "feef60b0aaf63a4773ace96636ebbcf43b881312",
    "$5M gross annualized revenue",
    "flux3-image-klein-int8-convrot.safetensors",
    "flux3-image-klein-base-int8-convrot.safetensors",
    "flux3-image-klein-base-nvfp4.safetensors",
    "flux3-image-klein-base-bf16.safetensors",
    "qwen3vl_4b_int8_convrot.safetensors",
    "qwen3.5_9b_flux3_prompt_upsampler_int8_convrot.safetensors",
    "download-image --tier flux3",
    "Qwen RESEARCH LICENSE AGREEMENT",
    "Qwen-Image 2.1 INT8-convrot",
    "Qwen-Image 2.1 Turbo INT8-convrot",
    "Qwen-Image 2.1 NVFP4",
    "Qwen-Image 2.1 Turbo NVFP4",
    "Qwen3VL-8B text encoder (Qwen-Image 2.1 companion)",
    "Qwen-Image 2.1 VAE BF16",
    "Comfy-Org/Qwen-Image-2.1",
    "Qwen/Qwen-Image-2.1",
    "Qwen/Qwen-Image-2.1-Turbo",
    "BennyDaBall/Qwen-Image-2.1-NVFP4",
    "BennyDaBall/Qwen-Image-2.1-Turbo-NVFP4",
    "aacf31a6d48e707f352ecba714cee0680da3479b",
    "b0e954a1ba86f00e30f76bac2494f45b0a221948",
    "82226d8cadaf20a678338f8faf5e5a0cfc3e1dfd",
    "qwen_image_2.1_int8_convrot.safetensors",
    "qwen_image_2.1_turbo_int8_convrot.safetensors",
    "qwen_image_2.1_nvfp4.safetensors",
    "qwen_image_2.1_turbo_nvfp4.safetensors",
    "qwen3vl_8b_int8_convrot.safetensors",
    "qwen3vl_8b_nvfp4.safetensors",
    "qwen3vl_8b_turbo_nvfp4.safetensors",
    "qwen_image_2.1_vae_bf16.safetensors",
    "download-image --tier qwen-image",
    "Built with Qwen",
    "Hangzhou Tongyi Laboratory",
    "diffusers",
    "Z-Image Turbo",
    "Wan 2.2 TI2V-5B",
    "Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
    "Wan 2.2 A14B",
    "Wan 2.2 Fun InP A14B",
    "alibaba-pai/Wan2.2-Fun-A14B-InP",
    "SeedVR2-3B",
    "ByteDance-Seed/SeedVR2-3B",
    "TRELLIS.2 native",
    "microsoft/TRELLIS.2",
    "Comfy-Org/TRELLIS.2",
    "DINOv3 License",
    "DINOv3",
    "trellis_2_int8_convrot",
    "DA3-BASE",
    "depth-anything/DA3-BASE",
    "Wan 2.1 VACE 1.3B",
    "nvdiffrast",
    "DreamX-Creator 1.0",
    "GD-ML/DreamX-Creator",
    "DreamX-World",
    "Wan 2.2 S2V 14B",
    "meituan-longcat/LongCat-Video",
    "LTX-2.5 distilled INT8-convrot",
    "Lightricks/LTX-2.5",
    "LTX-2.5 IC-LoRA Union Control",
    "Lightricks/LTX-2.3-22b-IC-LoRA-Union-Control",
    "ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors",
    "Distilled-only",
    "LTX Community License",
    "$10M COMPANY annual revenue",
    "LTX-2.3 distilled FP8",
    "FLUX.2 Klein 9B",
    "FLUX Non-Commercial",
    "FLUX.2 [dev]",
    "black-forest-labs/FLUX.2-dev",
    "black-forest-labs/FLUX.2-klein-9b-fp8",
    "flux-2-klein-9b-fp8.safetensors",
    "qwen_3_8b_fp8mixed.safetensors",
    "full_encoder_small_decoder.safetensors",
    "FLUX.2-small-decoder",
    "flux2_dev_fp8mixed.safetensors",
    "mistral_3_small_flux2_bf16.safetensors",
    "download-image --tier 9b",
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
    "Qwen2.5-VL-3B-Instruct Q4_K_M GGUF",
    "ggml-org/Qwen2.5-VL-3B-Instruct-GGUF",
    "Kokoro-82M",
    "hexgrad/Kokoro-82M",
    "ACE-Step 1.5",
    "ACE-Step 1.5 turbo AIO",
    "ACE-Step 1.5 XL",
    "MIT upstream / Apache companion pack",
    "Comfy-Org/ace_step_1.5_ComfyUI_files",
    "MiniMax Music 3",
    "Suno / Udio",
    "Chatterbox",
    "ResembleAI/chatterbox",
    "Qwen3-TTS 0.6B",
    "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    "Systran/faster-whisper-large-v3",
    "snakers4/silero-vad",
    "faster-whisper large-v3",
    "Silero VAD",
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
    # NVIDIA research lane: the four license names, the bars, and the footnote.
    "NVIDIA One-Way Noncommercial License",
    "NVIDIA OneWay Noncommercial License",
    "NVIDIA Open Model License",
    "NVIDIA Internal Scientific Research and Development Model License",
    "Waymo Dataset License Agreement for Non-Commercial Use",
    "no deployment, no redistribution, no works for sale or distribution",
    "commercial use of the weights is prohibited",
    "confirm before use",
    "NVIDIA research-lane footnote",
    "research-lane only",
    "never fetched by `download-models`, never keep-set protected, never pinned in a promoted workflow",
    "Klein 4B stills, Wan 2.2 silent motion, LTX-2.5 AV, TRELLIS.2, and TripoSplat",
    "nvidia/ArtiFixer",
    "nvidia/Fixer",
    "nvidia/Lyra",
    "nvidia/Lyra-2.0",
    "nvidia/PixelUMM",
    "nvidia/GEN3C-Cosmos-7B",
    "nvidia/LuxDiT",
    "yifanlu/InfiniCube-checkpoints",
    "nvidia/Cosmos-Drive-Dreams",
    "nvidia/dvlt",
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
    "Qwen2.5-VL-3B-Instruct Q4_K_M GGUF",
    "Z-Image Turbo",
    "Wan 2.2 A14B T2V/I2V",
    "Wan 2.2 Fun InP A14B",
    "SeedVR2-3B",
    "TRELLIS.2 native",
    "DINOv3 ViT-L (TRELLIS companion)",
    "DA3-BASE",
    "Wan 2.1 VACE 1.3B",
    "Wan 2.2 S2V 14B",
    "SuperSplat",
    "DreamX-Creator 1.0",
    "LTX-2.5 IC-LoRA Union Control",
    "LTX-2.3 distilled FP8",
    "FLUX.2 Klein 9B",
    "FLUX.2 Klein 9B base FP8",
    "FLUX.2 Klein 9B NVFP4",
    "Qwen3-8B text encoder (Klein 9B companion)",
    "FLUX.2 small decoder VAE",
    "FLUX.2 [dev]",
    "FLUX.2 [dev] FP8 Comfy pack",
    "Mistral Small Flux2 text encoder",
    "FLUX 3 Image Klein distilled INT8-convrot",
    "FLUX 3 Image Klein base INT8",
    "FLUX 3 Image Klein base NVFP4",
    "FLUX 3 Image Klein base BF16",
    "Qwen3VL-4B text encoder (FLUX 3 companion)",
    "Qwen3.5-9B prompt upsampler (FLUX 3 companion)",
    "MiniMax H3",
    "HunyuanVideo 1.5",
    "LongCat-Video",
    "Kokoro-82M",
    "ACE-Step 1.5 turbo AIO",
    "ACE-Step 1.5 XL",
    "MiniMax Music 3",
    "Suno / Udio",
    "Chatterbox / Multilingual v3 / Turbo",
    "Qwen3-TTS 0.6B",
    "faster-whisper large-v3",
    "Silero VAD",
    "F5-TTS official weights",
    "Coqui XTTS v2",
    "Echo-TTS",
    "Fish Audio S2",
    "Higgs Boson",
    "TTS-Audio-Suite",
    "OldTimeRadio",
    "Qwen-Image 2.1 INT8-convrot",
    "Qwen-Image 2.1 Turbo INT8-convrot",
    "Qwen-Image 2.1 NVFP4",
    "Qwen-Image 2.1 Turbo NVFP4",
    "Qwen3VL-8B text encoder (Qwen-Image 2.1 companion)",
    "Qwen-Image 2.1 VAE BF16",
)

# Research-lane rows: opt-in NVIDIA exploration the operator pulls by hand. Every row is
# a non-default, and column 3 is the license name grepped before a download.
RESEARCH_LANE_MODELS = (
    "ArtiFixer",
    "Fixer",
    "Lyra-1",
    "Lyra-2.0",
    "PixelUMM",
    "GEN3C",
    "LuxDiT",
    "InfiniCube",
    "Cosmos-Drive-Dreams",
    "DVLT",
)

RESEARCH_ROW_LABEL = "(research lane, opt-in)"

RESEARCH_LANE_LICENSES = {
    "ArtiFixer": "NVIDIA One-Way Noncommercial License",
    "Fixer": "NVIDIA Open Model License",
    "Lyra-1": "NVIDIA Open Model License",
    "Lyra-2.0": "NVIDIA Internal Scientific Research and Development Model License",
    "PixelUMM": "NVIDIA One-Way Noncommercial License",
    "GEN3C": "NVIDIA Open Model License",
    "LuxDiT": "NVIDIA OneWay Noncommercial License",
    "InfiniCube": "Waymo Dataset License Agreement for Non-Commercial Use",
    "Cosmos-Drive-Dreams": "Apache-2.0 code; Cosmos checkpoints carry their own NVIDIA terms",
    "DVLT": "NVIDIA License (non-commercial)",
}

# Weights with no commercial grant: their output never goes to monetized YouTube.
NONCOMMERCIAL_RESEARCH_MODELS = ("ArtiFixer", "PixelUMM", "LuxDiT", "DVLT")

# Cards that state commercial use is allowed; the stack still does not promote them.
OPEN_MODEL_RESEARCH_MODELS = ("Fixer", "Lyra-1", "GEN3C")


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


def test_flux3_klein_is_kommunity_not_apache() -> None:
    """FLUX 3 rows carry the Kommunity license and never claim Apache 2.0."""
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        rows = []
        for row in _table_rows(_read(path)):
            cells = [c.strip() for c in row.strip("|").split("|")]
            if len(cells) >= 9 and "FLUX 3 Image Klein" in row:
                rows.append((row, cells))
        assert len(rows) >= 4, path
        for row, cells in rows:
            assert "FLUX Kommunity License" in row, row
            assert "Apache 2.0" not in row, row
            assert cells[3].startswith("Yes"), row
            assert cells[8] == "No", row


def test_flux3_klein_is_not_the_default_still() -> None:
    """Docs keep Apache Klein 4B as the default and FLUX 3 as opt-in Kommunity."""
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        text = _read(path)
        assert "Kommunity" in text, path
        assert "Klein 4B" in text, path
        lower = text.lower()
        assert "opt-in" in lower, path
        assert "not legal advice" in lower, path


def test_qwen_image_21_is_research_license_not_apache() -> None:
    """Qwen-Image 2.1 rows carry the research license and never claim Apache 2.0."""
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        rows = []
        for row in _table_rows(_read(path)):
            cells = [c.strip() for c in row.strip("|").split("|")]
            if len(cells) >= 9 and "Qwen-Image 2.1" in cells[0]:
                rows.append((row, cells))
        assert len(rows) >= 6, f"{path.name} expected the six Qwen-Image 2.1 rows"
        for row, cells in rows:
            assert "Qwen RESEARCH LICENSE AGREEMENT" in row, row
            assert "Apache 2.0" not in row, row
            assert cells[3].startswith("Yes"), row
            assert cells[4] == "No", row
            assert cells[8] == "No", row


def test_qwen_image_21_is_not_the_default_still() -> None:
    """Apache Klein 4B stays the default still; Qwen-Image 2.1 stays opt-in research weights."""
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        lower = _read(path).lower()
        assert "qwen research license agreement" in lower, path
        assert "commercial use" in lower, path
        assert "klein 4b remains the apache default still" in lower, path


def test_banned_podcast_rows_us_not_ok() -> None:
    names = (
        "F5-TTS official weights",
        "Coqui XTTS v2",
        "Echo-TTS",
        "Fish Audio S2",
        "Higgs Boson",
        "TTS-Audio-Suite",
        "OldTimeRadio",
        "MiniMax Music 3",
        "Suno / Udio",
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


def _research_rows(text: str) -> dict[str, list[str]]:
    """Research-lane table rows keyed by the bare model name."""
    rows: dict[str, list[str]] = {}
    for row in _table_rows(text):
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) == 9 and cells[0].endswith(RESEARCH_ROW_LABEL):
            rows[cells[0][: -len(RESEARCH_ROW_LABEL)].strip()] = cells
    return rows


def test_nvidia_research_rows_exist_and_are_never_defaults() -> None:
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        rows = _research_rows(_read(path))
        for name in RESEARCH_LANE_MODELS:
            assert name in rows, f"{path.name} missing research row {name!r}"
            assert rows[name][8] == "No", f"{path.name} research row {name!r} must not be a default"


def test_nvidia_research_rows_state_the_governing_license() -> None:
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        rows = _research_rows(_read(path))
        for name, license_name in RESEARCH_LANE_LICENSES.items():
            assert license_name in rows[name][2], f"{path.name} {name!r} license={rows[name][2]!r}"


def test_nvidia_research_noncommercial_rows_bar_monetized_output() -> None:
    """A row whose weights carry no commercial grant never says Yes to monetized YouTube."""
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        rows = _research_rows(_read(path))
        for name in NONCOMMERCIAL_RESEARCH_MODELS:
            cells = rows[name]
            assert cells[3] == "Yes (research and personal use only)", cells
            assert cells[4] == "No", cells


def test_nvidia_research_open_model_rows_cite_the_card() -> None:
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        rows = _research_rows(_read(path))
        for name in OPEN_MODEL_RESEARCH_MODELS:
            cells = rows[name]
            assert cells[3].startswith("Yes"), cells
            assert cells[4].startswith("Yes per card"), cells
            assert "not a promoted lab pick" in cells[4], cells


def test_lyra_2_is_internal_rd_only() -> None:
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        cells = _research_rows(_read(path))["Lyra-2.0"]
        assert cells[3] == "Yes (non-production internal R&D only)", cells
        assert cells[4] == "No", cells
        assert cells[7] == "no deployment, no redistribution, no works for sale or distribution", cells


def test_infinicube_and_cosmos_drive_dreams_are_confirm_before_use() -> None:
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        rows = _research_rows(_read(path))
        infinicube = rows["InfiniCube"]
        assert "Waymo Open Dataset derivative" in infinicube[2], infinicube
        assert infinicube[4].startswith("No"), infinicube
        assert "commercial use of the weights is prohibited" in infinicube[4], infinicube
        cosmos = rows["Cosmos-Drive-Dreams"]
        assert "Apache-2.0 code" in cosmos[2], cosmos
        assert "confirm before use" in cosmos[2], cosmos
        assert cosmos[4].startswith("No"), cosmos
        assert "confirm" in cosmos[4].lower(), cosmos


def test_research_lane_footnote_names_the_promoted_catalog() -> None:
    for path in (LICENSE_ROOT, LICENSE_DOCS):
        text = _read(path)
        assert "NVIDIA research-lane footnote" in text, path
        assert "3DGRUT" in text, path
        assert "ships no checkpoint" in text, path
        assert "research-lane only" in text, path
        assert (
            "never fetched by `download-models`, never keep-set protected, "
            "never pinned in a promoted workflow" in text
        ), path
        assert (
            "Klein 4B stills, Wan 2.2 silent motion, LTX-2.5 AV, TRELLIS.2, and TripoSplat" in text
        ), path


def test_docs_research_bucket_links_the_declined_list() -> None:
    """The operator page buckets the lane and points at the declined-integrations page."""
    text = _read(LICENSE_DOCS)
    assert "| **Opt-in research (NVIDIA)** |" in text, LICENSE_DOCS
    assert "reference/declined-integrations.md" in text, LICENSE_DOCS
    lower = text.lower()
    assert "local experimentation" in lower, LICENSE_DOCS
    assert "not legal advice" in lower, LICENSE_DOCS

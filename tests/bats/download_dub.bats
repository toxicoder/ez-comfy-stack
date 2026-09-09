#!/usr/bin/env bats
#
# ## download_dub.bats
#
# Cover scripts/utilities/download-dub.sh (strict inventory). Hermetic mock HF.

load 'test_helper'

setup() {
  setup_repo_env
  install_hf_mock
  export DP="${UTILITIES_DIR}/download-dub.sh"
  chmod +x "${DP}"
  # shellcheck disable=SC1090
  source "${DP}"
}

teardown() {
  teardown_repo_env
}

@test "download-dub CLI help status asr unknown and banned tiers" {
  run bash "${DP}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"asr"* ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DP}\" status --tier asr --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"tiers"* ]]
  [[ "${output}" == *"silero"* || "${output}" == *"whisper"* ]]
  run bash "${DP}" status --nope
  [ "${status}" -ne 0 ]
  run bash "${DP}" run --tier f5
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"Banned"* ]]
  run bash "${DP}" run --tier xtts
  [ "${status}" -ne 0 ]
  run bash "${DP}" run --tier nllb
  [ "${status}" -ne 0 ]
  run bash "${DP}" --tier wav2lip
  [ "${status}" -ne 0 ]
  run bash "${DP}" --tier elevenlabs
  [ "${status}" -ne 0 ]
  run bash "${DP}" --tier rogan
  [ "${status}" -ne 0 ]
}

@test "download-dub helpers repo min dir includes process" {
  run dub_tier_repo vad
  [[ "${output}" == *"silero-vad"* ]]
  run dub_tier_repo whisper
  [[ "${output}" == *"faster-whisper"* ]]
  run dub_tier_repo clone
  [[ "${output}" == *"chatterbox"* ]]
  run dub_tier_repo bogus
  [ "${output}" = "" ]
  run dub_tier_min_gb vad
  [ "${output}" = "0" ]
  run dub_tier_min_gb clone
  [ "${output}" = "4" ]
  run dub_tier_min_gb x
  [ "${output}" = "0" ]
  run dub_tier_include_patterns vad
  [[ "${output}" == *"silero_vad.onnx"* ]]
  run dub_tier_include_patterns whisper
  [[ "${output}" == *"model.bin"* ]]
  [[ "${output}" == *"config.json"* ]]
  [[ "${output}" == *"vocabulary.json"* ]]
  run dub_tier_include_patterns clone
  [[ "${output}" == *"t3_mtl23ls_v3.safetensors"* ]]
  [[ "${output}" == *"ve.pt"* ]]
  [[ "${output}" == *"s3gen.pt"* ]]
  [[ "${output}" == *"grapheme_mtl_merged_expanded_v1.json"* ]]
  [[ "${output}" != *"t3_mtl23ls_v2.safetensors"* ]]
  [[ "${output}" != *"s3gen.safetensors"* ]]
  TIER=asr
  run dub_tiers_to_process
  [[ "${output}" == *"vad"* && "${output}" == *"whisper"* ]]
  TIER=all
  run dub_tiers_to_process
  [[ "${output}" == *"clone"* ]]
  run dub_comfy_dest_subdir silero_vad.onnx
  [ "${output}" = "onnx" ]
  run dub_comfy_dest_subdir model.bin
  [ "${output}" = "whisper" ]
  run dub_comfy_dest_subdir config.json
  [ "${output}" = "whisper" ]
  run dub_comfy_dest_subdir tokenizer.json
  [ "${output}" = "whisper" ]
  run dub_comfy_dest_subdir ve.pt
  [ "${output}" = "tts" ]
  run dub_comfy_dest_subdir s3gen.pt
  [ "${output}" = "tts" ]
  run dub_comfy_dest_subdir t3_mtl23ls_v3.safetensors
  [ "${output}" = "tts" ]
  run dub_comfy_dest_subdir grapheme_mtl_merged_expanded_v1.json
  [ "${output}" = "tts" ]
  dub_parse_args status --tier asr --json
  [ "${CMD}" = "status" ]
  run dub_tier_files_ready vad
  [ "${status}" -ne 0 ]
  run refuse_banned_dub_tier asr
  [ "${status}" -eq 0 ]
  run refuse_banned_dub_tier f5-tts
  [ "${status}" -ne 0 ]
  run dub_tier_size_gb "${MODELS_DIR}/nope"
  [ "${output}" = "0" ]
}

@test "download-dub link_into_comfy cmd_status cmd_run mock relative" {
  local tdir dest tgt
  tdir="$(dub_tier_dir vad)"
  mkdir -p "${tdir}/src/silero_vad/data"
  echo x >"${tdir}/src/silero_vad/data/silero_vad.onnx"
  run dub_link_into_comfy vad
  [ "${status}" -eq 0 ]
  dest="${MODELS_DIR}/comfy/onnx/silero_vad.onnx"
  [[ -L ${dest} ]]
  tgt="$(readlink "${dest}")"
  [[ ${tgt} != /* ]]
  TIER=asr
  run dub_cmd_status
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DP}\" run --tier asr"
  [ "${status}" -eq 0 ]
  [[ -L "${MODELS_DIR}/comfy/whisper/model.bin" ]]
  [[ -L "${MODELS_DIR}/comfy/whisper/config.json" ]]
  [[ -L "${MODELS_DIR}/comfy/onnx/silero_vad.onnx" ]]
  LAB_MOCK_HF_DOWNLOAD=fail
  TIER=asr
  rm -rf "$(dub_tier_dir vad)" "$(dub_tier_dir whisper)"
  run dub_cmd_run
  [ "${status}" -ne 0 ]
}

@test "download-dub clone mock links safetensors and cleanup dry-run" {
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DP}\" run --tier clone"
  [ "${status}" -eq 0 ]
  [[ -L "${MODELS_DIR}/comfy/tts/t3_mtl23ls_v3.safetensors" ]]
  [[ -L "${MODELS_DIR}/comfy/tts/ve.pt" ]]
  [[ -L "${MODELS_DIR}/comfy/tts/s3gen.pt" ]]
  [[ -L "${MODELS_DIR}/comfy/tts/grapheme_mtl_merged_expanded_v1.json" ]]
  tdir="$(dub_tier_dir clone)"
  echo extra >"${tdir}/junk.bin"
  TIER=clone
  CLEANUP_YES=0
  run dub_cmd_cleanup
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"would remove"* ]]
  [[ -f ${tdir}/junk.bin ]]
  CLEANUP_YES=1
  run dub_cmd_cleanup
  [ "${status}" -eq 0 ]
  [[ ! -f ${tdir}/junk.bin ]]
  run dub_prune_empty_dirs "${tdir}/does-not-exist"
  [ "${status}" -eq 0 ]
  run dub_is_keep_relpath clone README.md
  [ "${status}" -eq 0 ]
  run dub_list_extra_files clone
  [ "${status}" -eq 0 ]
}

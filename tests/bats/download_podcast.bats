#!/usr/bin/env bats
#
# ## download_podcast.bats
#
# Cover scripts/utilities/download-podcast.sh (strict inventory). Hermetic mock HF.

load 'test_helper'

setup() {
  setup_repo_env
  install_hf_mock
  export DP="${UTILITIES_DIR}/download-podcast.sh"
  chmod +x "${DP}"
  # shellcheck disable=SC1090
  source "${DP}"
}

teardown() {
  teardown_repo_env
}

@test "download-podcast CLI help status analog unknown and banned tiers" {
  run bash "${DP}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"analog"* ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DP}\" status --tier analog --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"tiers"* ]]
  [[ "${output}" == *"kokoro"* ]]
  run bash "${DP}" status --nope
  [ "${status}" -ne 0 ]
  run bash "${DP}" run --tier f5
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"Banned"* ]]
  run bash "${DP}" run --tier xtts
  [ "${status}" -ne 0 ]
  run bash "${DP}" run --tier fish
  [ "${status}" -ne 0 ]
  run bash "${DP}" --tier h3
  [ "${status}" -ne 0 ]
  run bash "${DP}" --tier music3
  [ "${status}" -ne 0 ]
  run bash "${DP}" --tier oldtimeradio
  [ "${status}" -ne 0 ]
  run bash "${DP}" --tier tts-audio-suite
  [ "${status}" -ne 0 ]
  run bash "${DP}" --tier rogan
  [ "${status}" -ne 0 ]
}

@test "download-podcast helpers repo min dir includes process" {
  run tier_repo analog
  [[ "${output}" == *"kokoro-onnx"* ]]
  run tier_repo acestep
  [[ "${output}" == *"ace_step_1.5_ComfyUI_files"* ]]
  run tier_repo chatterbox
  [[ "${output}" == *"chatterbox-turbo"* ]]
  run tier_repo qwen3tts
  [[ "${output}" == *"Qwen3-TTS"* ]]
  run tier_repo bogus
  [ "${output}" = "" ]
  run tier_min_gb analog
  [ "${output}" = "0" ]
  run tier_min_gb x
  [ "${output}" = "0" ]
  run tier_include_patterns analog
  [[ "${output}" == *"kokoro-v1.0.onnx"* ]]
  [[ "${output}" == *"voices-v1.0.bin"* ]]
  run tier_include_patterns acestep
  [[ "${output}" == *"ace_step_1.5_turbo_aio.safetensors"* ]]
  TIER=analog
  run tiers_to_process
  [[ "${output}" == *"analog"* ]]
  TIER=all
  run tiers_to_process
  [[ "${output}" == *"acestep"* && "${output}" == *"chatterbox"* ]]
  run comfy_dest_subdir kokoro-v1.0.onnx
  [ "${output}" = "onnx" ]
  run comfy_dest_subdir voices-v1.0.bin
  [ "${output}" = "tts" ]
  run comfy_dest_subdir ace_step_1.5_turbo_aio.safetensors
  [ "${output}" = "checkpoints" ]
  parse_args status --tier analog --json
  [ "${CMD}" = "status" ]
  run refuse_banned_podcast_tier analog
  [ "${status}" -eq 0 ]
  run refuse_banned_podcast_tier f5-tts
  [ "${status}" -ne 0 ]
  run tier_size_gb "${MODELS_DIR}/nope"
  [ "${output}" = "0" ]
}

@test "download-podcast link_into_comfy cmd_status cmd_run mock relative" {
  local tdir dest tgt
  tdir="$(tier_dir analog)"
  mkdir -p "${tdir}"
  echo x >"${tdir}/kokoro-v1.0.onnx"
  echo x >"${tdir}/voices-v1.0.bin"
  run link_into_comfy analog
  [ "${status}" -eq 0 ]
  dest="${MODELS_DIR}/comfy/onnx/kokoro-v1.0.onnx"
  [[ -L ${dest} ]]
  tgt="$(readlink "${dest}")"
  [[ ${tgt} != /* ]]
  [[ -L "${MODELS_DIR}/comfy/tts/voices-v1.0.bin" ]]
  TIER=analog
  run cmd_status
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DP}\" run --tier analog"
  [ "${status}" -eq 0 ]
  LAB_MOCK_HF_DOWNLOAD=fail
  TIER=analog
  rm -rf "$(tier_dir analog)"
  run cmd_run
  [ "${status}" -ne 0 ]
}

@test "download-podcast acestep mock links checkpoint" {
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DP}\" run --tier acestep"
  [ "${status}" -eq 0 ]
  [[ -L "${MODELS_DIR}/comfy/checkpoints/ace_step_1.5_turbo_aio.safetensors" ]]
  tgt="$(readlink "${MODELS_DIR}/comfy/checkpoints/ace_step_1.5_turbo_aio.safetensors")"
  [[ ${tgt} != /* ]]
}

@test "download-podcast cleanup keep selective and prune" {
  local tdir extra
  tdir="$(tier_dir analog)"
  mkdir -p "${tdir}"
  echo keep >"${tdir}/kokoro-v1.0.onnx"
  echo keep >"${tdir}/voices-v1.0.bin"
  extra="${tdir}/junk.bin"
  echo waste >"${extra}"
  echo meta >"${tdir}/LICENSE"
  run is_keep_relpath analog "kokoro-v1.0.onnx"
  [ "${status}" -eq 0 ]
  run is_keep_relpath analog "junk.bin"
  [ "${status}" -ne 0 ]
  run list_extra_files analog
  [[ "${output}" == *"${extra}"* ]]
  run tier_files_ready analog
  [ "${status}" -eq 0 ]
  CLEANUP_YES=1
  TIER=analog
  run cmd_cleanup
  [ "${status}" -eq 0 ]
  [[ ! -f ${extra} ]]
  [[ -f ${tdir}/kokoro-v1.0.onnx ]]
  run prune_empty_dirs "${tdir}"
  [ "${status}" -eq 0 ]
}

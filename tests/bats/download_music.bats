#!/usr/bin/env bats
#
# ## download_music.bats
#
# Cover scripts/utilities/download-music.sh (strict inventory). Hermetic mock HF.

load 'test_helper'

setup() {
  setup_repo_env
  install_hf_mock
  export DM="${UTILITIES_DIR}/download-music.sh"
  chmod +x "${DM}"
  # shellcheck disable=SC1090
  source "${DM}"
}

teardown() {
  teardown_repo_env
}

@test "download-music CLI help status turbo unknown and banned tiers" {
  run bash "${DM}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"turbo"* ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" bash \"${DM}\" status --tier turbo --json"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"tiers"* ]]
  [[ "${output}" == *"ace_step_1.5_ComfyUI_files"* ]]
  run bash "${DM}" status --nope
  [ "${status}" -ne 0 ]
  run bash "${DM}" run --tier music3
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"Banned"* ]]
  run bash "${DM}" run --tier minimax
  [ "${status}" -ne 0 ]
  run bash "${DM}" --tier suno
  [ "${status}" -ne 0 ]
  run bash "${DM}" --tier udio
  [ "${status}" -ne 0 ]
  run bash "${DM}" --tier h3
  [ "${status}" -ne 0 ]
  run bash "${DM}" --tier stable-audio
  [ "${status}" -ne 0 ]
}

@test "download-music helpers repo min dir includes process aio" {
  run tier_repo turbo
  [[ "${output}" == *"ace_step_1.5_ComfyUI_files"* ]]
  run tier_repo xl
  [[ "${output}" == *"ace_step_1.5_ComfyUI_files"* ]]
  run tier_repo bogus
  [ "${output}" = "" ]
  run aio_basename
  [ "${output}" = "ace_step_1.5_turbo_aio.safetensors" ]
  run tier_min_gb turbo
  [ "${output}" = "9" ]
  run tier_min_gb xl
  [ "${output}" = "14" ]
  run tier_min_gb x
  [ "${output}" = "0" ]
  run tier_include_patterns turbo
  [[ "${output}" == *"ace_step_1.5_turbo_aio.safetensors"* ]]
  run tier_include_patterns xl
  [[ "${output}" == *"acestep_v1.5_xl_turbo_bf16.safetensors"* ]]
  TIER=turbo
  run tiers_to_process
  [[ "${output}" == *"turbo"* ]]
  TIER=all
  run tiers_to_process
  [[ "${output}" == *"turbo"* && "${output}" == *"xl"* ]]
  run comfy_dest_subdir ace_step_1.5_turbo_aio.safetensors
  [ "${output}" = "checkpoints" ]
  run comfy_dest_subdir ace_1.5_vae.safetensors
  [ "${output}" = "vae" ]
  run comfy_dest_subdir qwen_0.6b_ace15.safetensors
  [ "${output}" = "text_encoders" ]
  run comfy_dest_subdir acestep_v1.5_xl_turbo_bf16.safetensors
  [ "${output}" = "diffusion_models" ]
  parse_args status --tier turbo --json
  [ "${CMD}" = "status" ]
  run refuse_banned_music_tier turbo
  [ "${status}" -eq 0 ]
  run refuse_banned_music_tier music3
  [ "${status}" -ne 0 ]
  run refuse_banned_music_tier suno
  [ "${status}" -ne 0 ]
  run refuse_banned_music_tier udio
  [ "${status}" -ne 0 ]
  run refuse_banned_music_tier h3
  [ "${status}" -ne 0 ]
  run refuse_banned_music_tier minimax
  [ "${status}" -ne 0 ]
  run refuse_banned_music_tier stable-audio
  [ "${status}" -ne 0 ]
  run tier_size_gb "${MODELS_DIR}/nope"
  [ "${output}" = "0" ]
  run tier_dir turbo
  [ "${output}" = "${MODELS_DIR}/Comfy-Org__ace_step_1.5_ComfyUI_files_acestep" ]
}

@test "download-music turbo dest matches podcast acestep" {
  run tier_dir turbo
  [ "${output}" = "${MODELS_DIR}/Comfy-Org__ace_step_1.5_ComfyUI_files_acestep" ]
  local podcast_dir
  # shellcheck disable=SC1091
  podcast_dir="$(
    MODELS_DIR="${MODELS_DIR}" bash -c "source \"${UTILITIES_DIR}/download-podcast.sh\"; tier_dir acestep"
  )"
  [ "${podcast_dir}" = "$(tier_dir turbo)" ]
}

@test "download-music link_into_comfy cmd_status cmd_run mock relative" {
  local tdir dest tgt
  tdir="$(tier_dir turbo)"
  mkdir -p "${tdir}/checkpoints"
  echo x >"${tdir}/checkpoints/ace_step_1.5_turbo_aio.safetensors"
  run link_into_comfy turbo
  [ "${status}" -eq 0 ]
  dest="${MODELS_DIR}/comfy/checkpoints/ace_step_1.5_turbo_aio.safetensors"
  [[ -L ${dest} ]]
  tgt="$(readlink "${dest}")"
  [[ ${tgt} != /* ]]
  TIER=turbo
  run cmd_status
  [ "${status}" -eq 0 ]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DM}\" run --tier turbo"
  [ "${status}" -eq 0 ]
  LAB_MOCK_HF_DOWNLOAD=fail
  TIER=turbo
  rm -rf "$(tier_dir turbo)" "${MODELS_DIR}/comfy"
  run cmd_run
  [ "${status}" -ne 0 ]
}

@test "download-music turbo mock links relative AIO" {
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DM}\" run --tier turbo"
  [ "${status}" -eq 0 ]
  [[ -L "${MODELS_DIR}/comfy/checkpoints/ace_step_1.5_turbo_aio.safetensors" ]]
  tgt="$(readlink "${MODELS_DIR}/comfy/checkpoints/ace_step_1.5_turbo_aio.safetensors")"
  [[ ${tgt} != /* ]]
  run existing_aio_path
  [ "${status}" -eq 0 ]
}

@test "download-music turbo cache-hits podcast acestep AIO" {
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${UTILITIES_DIR}/download-podcast.sh\" run --tier acestep"
  [ "${status}" -eq 0 ]
  [[ -L "${MODELS_DIR}/comfy/checkpoints/ace_step_1.5_turbo_aio.safetensors" ]]
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=fail bash \"${DM}\" run --tier turbo"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"cache hit"* || "${output}" == *"already present"* ]]
  run existing_aio_path
  [ "${status}" -eq 0 ]
  run tier_files_ready turbo
  [ "${status}" -eq 0 ]
}

@test "download-music cleanup keep selective and prune" {
  local tdir extra
  tdir="$(tier_dir turbo)"
  mkdir -p "${tdir}/checkpoints"
  echo keep >"${tdir}/checkpoints/ace_step_1.5_turbo_aio.safetensors"
  extra="${tdir}/junk.bin"
  echo waste >"${extra}"
  echo meta >"${tdir}/LICENSE"
  run is_keep_relpath turbo "checkpoints/ace_step_1.5_turbo_aio.safetensors"
  [ "${status}" -eq 0 ]
  run is_keep_relpath turbo "junk.bin"
  [ "${status}" -ne 0 ]
  run list_extra_files turbo
  [[ "${output}" == *"${extra}"* ]]
  run tier_files_ready turbo
  [ "${status}" -eq 0 ]
  CLEANUP_YES=1
  TIER=turbo
  run cmd_cleanup
  [ "${status}" -eq 0 ]
  [[ ! -f ${extra} ]]
  [[ -f ${tdir}/checkpoints/ace_step_1.5_turbo_aio.safetensors ]]
  run prune_empty_dirs "${tdir}"
  [ "${status}" -eq 0 ]
}

@test "download-music xl mock links split files" {
  run bash -c "MODELS_DIR=\"${MODELS_DIR}\" LAB_MOCK_HF_DOWNLOAD=1 bash \"${DM}\" run --tier xl"
  [ "${status}" -eq 0 ]
  [[ -L "${MODELS_DIR}/comfy/diffusion_models/acestep_v1.5_xl_turbo_bf16.safetensors" ]]
  [[ -L "${MODELS_DIR}/comfy/vae/ace_1.5_vae.safetensors" ]]
  tgt="$(readlink "${MODELS_DIR}/comfy/diffusion_models/acestep_v1.5_xl_turbo_bf16.safetensors")"
  [[ ${tgt} != /* ]]
}

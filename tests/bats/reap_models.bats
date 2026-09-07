#!/usr/bin/env bats
#
# Hermetic reap-models fixture (no GPU, no network).

load 'test_helper'

setup() {
  setup_repo_env
  install_docker_mocks
  export RM="${UTILITIES_DIR}/reap-models.sh"
  chmod +x "${RM}" "${UTILITIES_DIR}/models-manifest.sh"
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/scripts/lib/models.sh"
  # shellcheck disable=SC1090
  source "${RM}"
  mkdir -p \
    "${MODELS_DIR}/Lightricks__LTX-2.5_2.5" \
    "${MODELS_DIR}/Lightricks__LTX-2.3_2.3" \
    "${MODELS_DIR}/comfy/diffusion_models" \
    "${MODELS_DIR}/comfy/vae" \
    "${MODELS_DIR}/foreign" \
    "${MODELS_DIR}/music"
  echo live >"${MODELS_DIR}/Lightricks__LTX-2.5_2.5/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"
  echo old >"${MODELS_DIR}/Lightricks__LTX-2.3_2.3/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors"
  echo part >"${MODELS_DIR}/Lightricks__LTX-2.5_2.5/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors.incomplete"
  echo h3 >"${MODELS_DIR}/MiniMax-H3.safetensors"
  ln -sfn "${MODELS_DIR}/missing-target" "${MODELS_DIR}/comfy/diffusion_models/broken.safetensors"
  echo ace >"${MODELS_DIR}/music/ace_step_1.5_turbo_aio.safetensors"
  echo vae >"${MODELS_DIR}/comfy/vae/flux2-vae.safetensors"
  echo splat >"${MODELS_DIR}/triposplat.safetensors"
  echo lab >"${MODELS_DIR}/foreign/nvidia-lab.bin"
}

teardown() {
  teardown_repo_env
}

@test "reap-models --plan lists junk superseded banned not live 2.5 or ACE" {
  MODE=plan
  CLASS="junk,superseded,banned"
  run reap_plan
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"junk"* ]]
  [[ "${output}" == *".incomplete"* ]]
  [[ "${output}" == *"superseded"* ]]
  [[ "${output}" == *"LTX-2.3"* ]]
  [[ "${output}" == *"banned"* || "${output}" == *"MiniMax-H3"* ]]
  [[ "${output}" != *"PLAN live"* ]]
  [[ "${output}" != *"ace_step_1.5_turbo_aio"* ]]
  [[ "${output}" == *"foreign skip"* ]]
}

@test "reap-models --apply junk deletes incomplete and broken link only" {
  CLASS="junk"
  YES=1
  QUARANTINE=0
  MODE=apply
  run reap_apply
  [ "${status}" -eq 0 ]
  [[ ! -e ${MODELS_DIR}/Lightricks__LTX-2.5_2.5/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors.incomplete ]]
  [[ ! -e ${MODELS_DIR}/comfy/diffusion_models/broken.safetensors ]]
  [[ -f ${MODELS_DIR}/Lightricks__LTX-2.5_2.5/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors ]]
  [[ -f ${MODELS_DIR}/Lightricks__LTX-2.3_2.3/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors ]]
  echo leftover >"${MODELS_DIR}/junk-extra.incomplete"
  run reap_one junk "${MODELS_DIR}/junk-extra.incomplete"
  [ "${status}" -eq 0 ]
  [[ ! -e ${MODELS_DIR}/junk-extra.incomplete ]]
}

@test "reap-models drop-pack triposplat does not remove flux2-vae" {
  DROP_PACK=triposplat
  YES=1
  QUARANTINE=1
  run reap_drop_pack
  [ "${status}" -eq 0 ]
  [[ -f ${MODELS_DIR}/comfy/vae/flux2-vae.safetensors ]]
}

@test "reap-models superseded quarantine and restore" {
  CLASS="superseded"
  YES=1
  QUARANTINE=1
  run reap_apply
  [ "${status}" -eq 0 ]
  [[ ! -f ${MODELS_DIR}/Lightricks__LTX-2.3_2.3/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors ]]
  local q
  q="$(find "${MODELS_DIR}/.reap-quarantine" -name 'ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors' | head -1)"
  [[ -n ${q} ]]
  RESTORE_FROM="$(dirname "$(dirname "${q}")")"
  # restore from utc dir
  RESTORE_FROM="$(find "${MODELS_DIR}/.reap-quarantine" -mindepth 1 -maxdepth 1 -type d | head -1)"
  run reap_restore
  [ "${status}" -eq 0 ]
  [[ -f ${MODELS_DIR}/Lightricks__LTX-2.3_2.3/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors ]]
}

@test "reap-models refuse apply with hf pid file and path escape" {
  : >"${MODELS_DIR}/.hf-download.pid"
  CLASS="junk"
  YES=1
  run reap_apply
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"pid file"* ]]
  rm -f "${MODELS_DIR}/.hf-download.pid"
  run models_realpath_under /etc/passwd
  [ "${status}" -ne 0 ]
  [[ "${output}" == *"escapes"* ]]
}

@test "reap-models help and models_keep_set includes default filenames" {
  run bash "${RM}" --help
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"plan"* ]]
  [[ "${output}" == *"does not delete weights"* ]]
  run models_keep_set
  [[ "${output}" == *"flux-2-klein-4b-fp8.safetensors"* ]]
  [[ "${output}" == *"flux2-vae.safetensors"* ]]
  run models_default_keep_set
  [[ "${output}" == *"ltx-2.5-video-vae-bf16.safetensors"* ]]
  run models_refuse_list
  [[ "${output}" == *"MiniMax-H3"* ]]
  [[ "${output}" == *"FLUX.2-dev"* ]]
  [[ "${output}" == *"DA3-LARGE"* ]]
  [[ "${output}" == *"Inria-3DGS"* ]]
  run models_dir_is_safe
  [ "${status}" -eq 0 ]
  parse_args --plan --class junk
  [ "${MODE}" = "plan" ]
  run class_selected junk
  [ "${status}" -eq 0 ]
  run reap_classify_path "${MODELS_DIR}/MiniMax-H3.safetensors"
  [ "${output}" = "banned" ]
  run reap_classify_path "${MODELS_DIR}/Lightricks__LTX-2.5_2.5/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"
  [ "${output}" = "live" ]
  run models_is_keep_file flux2-vae.safetensors
  [ "${status}" -eq 0 ]
  YES=1
  mkdir -p "${MODELS_DIR}/.reap-quarantine/old"
  run reap_drop_quarantine
  [ "${status}" -eq 0 ]
  run reap_apply_guards
  [ "${status}" -eq 0 ]
  reap_log "test-line"
  grep -q "test-line" "${MODELS_DIR}/.reap-log"
}
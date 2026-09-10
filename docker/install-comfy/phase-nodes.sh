#!/usr/bin/env bash
#
# ## install-comfy/phase-nodes.sh
#
# Docker cache phase: custom nodes + optional packages (fail-soft).
# Source common.sh before this file.
#

#######################################
# True if the installed nunchaku package looks like the real SVDQuant engine.
# Globals:
#   None (uses active venv python)
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 if real nunchaku; 1 if missing or wrong PyPI stats package
#######################################
nunchaku_is_real() {
  python - <<'PY' 2>/dev/null
import importlib.util
import sys

if importlib.util.find_spec("nunchaku") is None:
    sys.exit(1)
try:
    import nunchaku

    # Real engine exposes model classes; PyPI "nunchaku" is unrelated Bayesian stats
    if hasattr(nunchaku, "NunchakuFluxTransformer2dModel") or hasattr(nunchaku, "NunchakuT5EncoderModel"):
        sys.exit(0)
    if importlib.util.find_spec("nunchaku.models") is not None:
        sys.exit(0)
except Exception:
    pass
sys.exit(1)
PY
}

#######################################
# Remove the wrong PyPI "nunchaku" stats package if present (not SVDQuant).
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   log/warn
# Returns:
#   0 always (soft)
#######################################
cleanup_wrong_nunchaku() {
  if ! python -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('nunchaku') else 1)" 2>/dev/null; then
    return 0
  fi
  if nunchaku_is_real; then
    return 0
  fi
  warn "Removing wrong PyPI 'nunchaku' package (stats lib, not SVDQuant engine)"
  pip uninstall -y nunchaku >/dev/null 2>&1 || true
}

#######################################
# Map machine arch to manylinux wheel platform tag used by nunchaku releases.
# Globals:
#   None
# Arguments:
#   $1  Machine arch (e.g. from uname -m: x86_64, aarch64)
# Outputs:
#   Platform tag on stdout (empty if unsupported)
# Returns:
#   0
#######################################
nunchaku_platform_tag() {
  local arch="${1:?nunchaku_platform_tag requires arch}"
  case "${arch}" in
    x86_64 | amd64) echo "linux_x86_64" ;;
    aarch64 | arm64) echo "linux_aarch64" ;;
    *) echo "" ;;
  esac
}

#######################################
# Build a candidate GitHub release wheel URL for nunchaku (no network).
# Globals:
#   NUNCHAKU_VERSION — default 1.2.1 (aligned with ComfyUI-nunchaku v1.2.1)
# Arguments:
#   $1  Platform tag (linux_x86_64, …)
#   $2  Python tag (cp312)
#   $3  CUDA tag (cu13.0)
#   $4  Torch tag (torch2.11)
# Outputs:
#   URL on stdout
# Returns:
#   0
#######################################
nunchaku_wheel_url() {
  local plat="${1}"
  local py_tag="${2}"
  local cu_tag="${3}"
  local torch_tag="${4}"
  local ver="${NUNCHAKU_VERSION:-1.2.1}"
  local wheel="nunchaku-${ver}+${cu_tag}${torch_tag}-${py_tag}-${py_tag}-${plat}.whl"
  echo "https://github.com/nunchaku-ai/nunchaku/releases/download/v${ver}/${wheel}"
}

#######################################
# Install real nunchaku from GitHub wheels only (never bare PyPI nunchaku).
# Lab workflows use core loaders; this is fail-soft optional acceleration.
# Globals:
#   NUNCHAKU_VERSION, NUNCHAKU_WHEEL_URL (optional full override)
# Arguments:
#   None
# Outputs:
#   log/warn
# Returns:
#   0 always (soft-fail)
#######################################
install_nunchaku_wheel() {
  local plat py_tag torch_mm cu_tag torch_tag url
  local -a torch_cands cu_cands

  cleanup_wrong_nunchaku
  if nunchaku_is_real; then
    log "nunchaku already installed (real engine)"
    return 0
  fi

  if [[ -n ${NUNCHAKU_WHEEL_URL:-} ]]; then
    log "Installing nunchaku from NUNCHAKU_WHEEL_URL"
    if pip_install "${NUNCHAKU_WHEEL_URL}"; then
      log "nunchaku wheel install ok"
      return 0
    fi
    warn "nunchaku wheel install failed from NUNCHAKU_WHEEL_URL (optional)"
    return 0
  fi

  plat="$(nunchaku_platform_tag "$(uname -m)")"
  if [[ -z ${plat} ]]; then
    warn "nunchaku: unsupported arch $(uname -m); skipping (optional)"
    return 0
  fi
  # Official v1.2.1 release assets are linux_x86_64 / win_amd64 only — no aarch64
  if [[ ${plat} == "linux_aarch64" ]]; then
    warn "nunchaku: no official linux_aarch64 wheels (GB10/Spark) — skipping"
    warn "*-lab-example graphs use core UNET/CLIP/VAE loaders and do not need nunchaku"
    return 0
  fi

  py_tag="$(python -c 'import sys; print(f"cp{sys.version_info.major}{sys.version_info.minor}")' 2>/dev/null || echo "cp312")"
  torch_mm="$(python -c 'import torch; v=torch.__version__.split("+")[0].split("."); print(f"{v[0]}.{v[1]}")' 2>/dev/null || echo "2.11")"
  # Prefer exact torch minor, then published nunchaku wheel train
  torch_cands=("${torch_mm}" "2.11" "2.10" "2.9")
  cu_cands=("cu13.0" "cu12.8")

  local t c tried=0
  for t in "${torch_cands[@]}"; do
    torch_tag="torch${t}"
    for c in "${cu_cands[@]}"; do
      cu_tag="${c}"
      url="$(nunchaku_wheel_url "${plat}" "${py_tag}" "${cu_tag}" "${torch_tag}")"
      tried=$((tried + 1))
      log "Trying nunchaku wheel: ${url}"
      if pip_install "${url}"; then
        if nunchaku_is_real; then
          log "nunchaku wheel install ok (${cu_tag}${torch_tag})"
          return 0
        fi
        warn "Installed wheel but import check failed; uninstalling"
        pip uninstall -y nunchaku >/dev/null 2>&1 || true
      fi
    done
  done
  warn "nunchaku wheel not available for ${plat}/${py_tag}/torch${torch_mm} after ${tried} tries (optional)"
  warn "Do not pip install bare 'nunchaku' from PyPI — that is an unrelated stats package"
  return 0
}

#######################################
# Hide ComfyUI-nunchaku when the SVDQuant engine is missing (Comfy skips *.disabled).
# Re-enable the pack if a real engine later imports. Lab graphs use core loaders.
# Globals:
#   COMFY_HOME, CUSTOM
# Arguments:
#   None
# Outputs:
#   log
# Returns:
#   0 always
#######################################
configure_nunchaku_pack() {
  local custom enabled disabled
  custom="${CUSTOM:-${COMFY_HOME}/custom_nodes}"
  enabled="${custom}/ComfyUI-nunchaku"
  disabled="${custom}/ComfyUI-nunchaku.disabled"
  mkdir -p "${custom}"
  if nunchaku_is_real; then
    if [[ -d ${disabled} && ! -d ${enabled} ]]; then
      mv "${disabled}" "${enabled}"
      log "nunchaku node enabled (engine importable)"
    fi
    return 0
  fi
  if [[ -d ${enabled} ]]; then
    rm -rf "${disabled}"
    mv "${enabled}" "${disabled}"
    log "nunchaku node disabled (no engine wheel; lab graphs use core loaders)"
  fi
  return 0
}

#######################################
# Ensure ComfyUI-VideoHelperSuite is present (required for LTX lab MP4 output).
# Idempotent: safe on cold install and stamp-present refresh.
# Globals:
#   COMFY_HOME, CUSTOM, COMFYUI_VHS_REF, VENV
# Arguments:
#   None
# Outputs:
#   Progress via log/warn/err
# Returns:
#   0 if VHS tree exists; 1 if still missing after clone attempt
#######################################
ensure_lab_video_nodes() {
  activate_venv
  CUSTOM="${COMFY_HOME}/custom_nodes"
  mkdir -p "${CUSTOM}"
  clone_node "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git" \
    "ComfyUI-VideoHelperSuite" "${COMFYUI_VHS_REF:-}"
  if [[ ! -d ${CUSTOM}/ComfyUI-VideoHelperSuite ]]; then
    warn "ComfyUI-VideoHelperSuite missing under ${CUSTOM} (required for LTX lab MP4)"
    return 1
  fi
  return 0
}

# Official llama-cpp-python CPU wheels. PyPI is sdist-only; --only-binary
# against PyPI always misses on DGX Spark. Pins live in llama-cpp-cpu.sh.
# shellcheck source=llama-cpp-cpu.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/llama-cpp-cpu.sh"

#######################################
# Install llama-cpp-python CPU wheel so prompt enhance stays off the GPU.
# CPU extra-index is --index-url (not only extra-index) so pip does not stop
# on PyPI's sdist. Direct GitHub wheel URL is the fallback. No cmake, no CUDA
# extra-index. Fail-soft: Enhance/dub pass through if missing; Queue can heal.
# Globals:
#   LLAMA_CPP_CPU_INDEX, PYPI_SIMPLE_INDEX, LLAMA_CPP_CPU_PKG
# Arguments:
#   None
# Outputs:
#   log/warn
# Returns:
#   0 always (soft-fail)
#######################################
install_llama_cpp_cpu() {
  local wheel
  local -a args=()
  while IFS= read -r tok; do
    args+=("${tok}")
  done < <(llama_cpp_cpu_pip_index_args)
  if pip_install "${args[@]}"; then
    log "llama-cpp-python (CPU wheel) installed for prompt enhance"
    return 0
  fi
  wheel="$(llama_cpp_direct_wheel_url)"
  if [[ -n ${wheel} ]] && pip_install --only-binary=:all: "${wheel}"; then
    log "llama-cpp-python (CPU wheel) installed from GitHub release"
    return 0
  fi
  warn "llama-cpp-python CPU wheel pip failed — Enhance/dub will pass through until Queue heals the wheel"
  return 0
}

#######################################
# Optional faster-whisper for local dub ASR. Fail-soft. Independent of clone.
# chatterbox-tts pins torch==2.6.0 — never install it on the same pip command.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   log/warn
# Returns:
#   0 always (soft-fail)
#######################################
install_faster_whisper_wheel() {
  if pip_install --upgrade-strategy only-if-needed faster-whisper; then
    log "faster-whisper installed for local dub ASR"
    return 0
  fi
  warn "faster-whisper pip failed — Queue writes empty mix until: pip install faster-whisper"
  return 0
}

#######################################
# Optional chatterbox-tts for local dub clone. Fail-soft. Install the GitHub
# zip (PyPI 0.1.7 has no t3_model=v3) with --no-deps so the package cannot pin
# torch==2.6.0 / transformers==5.2.0 over the lab venv.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   log/warn
# Returns:
#   0 always (soft-fail)
#######################################
install_chatterbox_wheel() {
  local zip
  local -a extras=(
    librosa
    s3tokenizer
    resemble-perth
    conformer
    pykakasi
    pyloudnorm
    omegaconf
    spacy-pkuseg
  )
  zip="$(chatterbox_tts_zip_url)"
  pip_install --upgrade-strategy only-if-needed "${extras[@]}" ||
    warn "chatterbox extras pip failed — clone may still miss"
  if pip_install --upgrade --force-reinstall --no-deps "${zip}"; then
    log "chatterbox-tts V3 source installed --no-deps (did not pin torch)"
    return 0
  fi
  warn "chatterbox-tts --no-deps failed — clone status will name the miss"
  return 0
}

#######################################
# Optional faster-whisper + chatterbox-tts for local dub. Fail-soft.
# Installs ASR first so a clone miss cannot block transcription.
# Does not pull weights (download-dub). Missing wheels → empty mix + Dub status.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   log/warn
# Returns:
#   0 always (soft-fail)
#######################################
install_dub_wheels() {
  install_faster_whisper_wheel
  install_chatterbox_wheel
}

#######################################
# Optional ABI-matched SageAttention wheel. Default is Kitchen (--use-ck-attention).
# Never pip-installs the PyPI package ``sageattention`` (silent aarch64 fallback).
# Globals:
#   LAB_SAGE_WHEEL_URL, LAB_SAGE_WHEEL_SHA256
# Arguments:
#   None
# Outputs:
#   log/warn
# Returns:
#   0 always (fail-soft)
#######################################
install_sage_wheel_if_pinned() {
  local url sha
  url="${LAB_SAGE_WHEEL_URL:-}"
  sha="${LAB_SAGE_WHEEL_SHA256:-}"
  if [[ -z ${url} ]]; then
    log "SageAttention: skipped (Kitchen is default; do not pip install sageattention from PyPI)"
    return 0
  fi
  if [[ -z ${sha} ]]; then
    warn "LAB_SAGE_WHEEL_URL set without LAB_SAGE_WHEEL_SHA256 — refusing Sage wheel"
    return 0
  fi
  log "SageAttention pinned wheel requested (sha256=${sha})"
  warn "Kitchen remains the Comfy CLI default; do not pass --use-sage-attention with --use-ck-attention"
  if pip_install "${url}"; then
    log "Sage wheel pip ok — verify torch ABI before switching attention flags"
  else
    warn "Sage wheel install failed (optional; Kitchen stays default)"
  fi
  return 0
}

#######################################
# Install custom nodes and optional packages (Docker phase: nodes).
# Globals:
#   COMFY_HOME, VENV, CUSTOM, COMFYUI_MANAGER_REF, COMFYUI_NUNCHAKU_NODE_REF,
#   COMFYUI_VHS_REF
# Arguments:
#   None
# Outputs:
#   Progress via log/warn
# Returns:
#   0 on success; non-zero if required VideoHelperSuite is missing
#   (nunchaku / optional Sage wheel remain fail-soft)
#######################################
phase_nodes() {
  activate_venv
  CUSTOM="${COMFY_HOME}/custom_nodes"
  mkdir -p "${CUSTOM}"
  clone_node "https://github.com/ltdrdata/ComfyUI-Manager.git" "ComfyUI-Manager" \
    "${COMFYUI_MANAGER_REF:-}"
  # Required for ltx-*-lab-example VHS_VideoCombine MP4 output
  ensure_lab_video_nodes || return 1
  clone_node "https://github.com/nunchaku-ai/ComfyUI-nunchaku.git" "ComfyUI-nunchaku" \
    "${COMFYUI_NUNCHAKU_NODE_REF:-}" ||
    clone_node "https://github.com/nunchaku-tech/ComfyUI-nunchaku.git" "ComfyUI-nunchaku" \
      "${COMFYUI_NUNCHAKU_NODE_REF:-}" ||
    clone_node "https://github.com/mit-han-lab/ComfyUI-nunchaku.git" "ComfyUI-nunchaku" \
      "${COMFYUI_NUNCHAKU_NODE_REF:-}" ||
    warn "Nunchaku custom node unavailable"
  # MagCache: Wan 5B draft only. Fail-soft. Hero LTX graphs must not depend on it.
  clone_node "https://github.com/Zehong-Ma/ComfyUI-MagCache.git" "ComfyUI-MagCache" \
    "${COMFYUI_MAGCACHE_REF}" ||
    warn "ComfyUI-MagCache unavailable (Wan 5B draft MagCache extra still documents the pin)"
  # OpenCut MIT embed (not the Rust rewrite, not a hosted Next.js stack).
  clone_node "https://github.com/jtydhr88/ComfyUI-OpenCut.git" "ComfyUI-OpenCut" \
    "${COMFYUI_OPENCUT_REF}" ||
    warn "ComfyUI-OpenCut unavailable (timeline embed is optional)"
  # GPL LTX Director: clone into the Comfy volume only when opted in. Not vendored.
  if [[ ${LAB_ENABLE_LTX_DIRECTOR:-0} == "1" ]]; then
    clone_node "https://github.com/WhatDreamsCost/WhatDreamsCost-ComfyUI.git" \
      "WhatDreamsCost-ComfyUI" "${COMFYUI_LTX_DIRECTOR_REF}" ||
      warn "LTX Director clone failed"
  else
    log "LTX Director skipped (set LAB_ENABLE_LTX_DIRECTOR=1 to clone GPL pin into the volume)"
  fi
  install_sage_wheel_if_pinned
  install_nunchaku_wheel
  configure_nunchaku_pack
  install_llama_cpp_cpu
  install_dub_wheels
}

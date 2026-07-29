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
#   (nunchaku/SageAttention remain fail-soft)
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
  pip_install sageattention || warn "SageAttention pip install failed (optional on aarch64)"
  install_nunchaku_wheel
}

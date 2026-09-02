#!/usr/bin/env bash
#
# ## entrypoint
#
# Container entrypoint for the ez-comfy flux-to-ltx image.
#
# Purpose:
#   1) Seed ComfyUI from /opt/comfy-prebuilt when present (fast), else cold install
#   2) Refresh model links + free-memory patch
#   3) Exec ComfyUI on 0.0.0.0:8188
#
# Environment:
#   COMFY_HOME, LAB_PREBUILT_ROOT, LAB_FORCE_COLD_INSTALL, LAB_ENTRYPOINT_*
#
set -euo pipefail

#######################################
# Timestamped entrypoint phase line.
# Globals:
#   None
# Arguments:
#   $@  Message
# Outputs:
#   stdout
# Returns:
#   0
#######################################
ep_log() {
  echo "[entrypoint $(date -u +%H:%M:%SZ)] $*"
}

#######################################
# True if prebuilt tree looks usable.
# Globals:
#   LAB_PREBUILT_ROOT
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 if prebuilt venv python exists
#######################################
prebuilt_ready() {
  local root="${LAB_PREBUILT_ROOT:-/opt/comfy-prebuilt}"
  [[ -x "${root}/.venv/bin/python" ]]
}

#######################################
# Copy prebuilt Comfy tree onto the volume (local disk; no pip).
# Globals:
#   COMFY_HOME, LAB_PREBUILT_ROOT
# Arguments:
#   None
# Outputs:
#   Progress logs
# Returns:
#   0 on success
#######################################
seed_from_prebuilt() {
  local root="${LAB_PREBUILT_ROOT:-/opt/comfy-prebuilt}"
  local dest="${COMFY_HOME:-/comfy-state/ComfyUI}"
  ep_log "Seeding ${dest} from ${root} (local copy — not re-downloading torch)"
  mkdir -p "${dest}"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --info=progress2 "${root}/" "${dest}/" || rsync -a "${root}/" "${dest}/"
  else
    ep_log "rsync missing; using cp -a (no progress bar)"
    cp -a "${root}/." "${dest}/"
  fi
  ep_log "Seed complete"
}

#######################################
# Resolve directory containing libcuda.so.1 for gcc link / dlopen.
# Globals:
#   LD_LIBRARY_PATH
# Arguments:
#   None
# Outputs:
#   Absolute directory path on stdout when found
# Returns:
#   0 if found; 1 otherwise
#######################################
find_libcuda_dir() {
  local line path dir cand
  local -a search_dirs=()
  local old_ifs="${IFS}"
  if command -v ldconfig >/dev/null 2>&1; then
    while IFS= read -r line; do
      # ldconfig -p lines: "libcuda.so.1 (libc6,…) => /path/libcuda.so.1"
      path="${line#*=>}"
      path="${path#"${path%%[![:space:]]*}"}"
      path="${path%"${path##*[![:space:]]}"}"
      if [[ -n ${path} && -e ${path} ]]; then
        dir="$(dirname "${path}")"
        echo "${dir}"
        return 0
      fi
    done < <(ldconfig -p 2>/dev/null | grep -F 'libcuda.so.1' || true)
  fi
  if [[ -n ${LD_LIBRARY_PATH:-} ]]; then
    IFS=':'
    # shellcheck disable=SC2206
    search_dirs=(${LD_LIBRARY_PATH})
    IFS="${old_ifs}"
  fi
  search_dirs+=(
    /lib/aarch64-linux-gnu
    /usr/lib/aarch64-linux-gnu
    /lib/x86_64-linux-gnu
    /usr/lib/x86_64-linux-gnu
    /usr/local/nvidia/lib64
    /usr/local/cuda/compat/lib
    /usr/local/cuda/lib64
  )
  for dir in "${search_dirs[@]}"; do
    [[ -n ${dir} ]] || continue
    cand="${dir}/libcuda.so.1"
    if [[ -e ${cand} ]]; then
      echo "${dir}"
      return 0
    fi
  done
  return 1
}

#######################################
# Export LIBRARY_PATH / LD_LIBRARY_PATH so Triton can link libcuda at JIT time.
# Globals:
#   LIBRARY_PATH, LD_LIBRARY_PATH
# Arguments:
#   None
# Outputs:
#   Progress logs
# Returns:
#   0 always (best-effort)
#######################################
ensure_triton_build_env() {
  local cuda_dir
  if cuda_dir="$(find_libcuda_dir)"; then
    export LIBRARY_PATH="${cuda_dir}${LIBRARY_PATH:+:${LIBRARY_PATH}}"
    case ":${LD_LIBRARY_PATH:-}:" in
      *":${cuda_dir}:"*) ;;
      *)
        export LD_LIBRARY_PATH="${cuda_dir}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
        ;;
    esac
    ep_log "Triton link env: libcuda dir=${cuda_dir}"
  else
    ep_log "Triton link env: libcuda.so.1 not found yet (GPU mount may appear later)"
  fi
  return 0
}

#######################################
# True when gcc, Python.h, and libcuda look available for Triton cuda_utils JIT.
# Globals:
#   None (uses active python on PATH)
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 if deps OK; 1 otherwise
#######################################
triton_build_deps_ok() {
  local py_include
  if ! command -v gcc >/dev/null 2>&1; then
    return 1
  fi
  if ! command -v python >/dev/null 2>&1 && ! command -v python3 >/dev/null 2>&1; then
    return 1
  fi
  py_include="$(
    python -c 'import sysconfig; print(sysconfig.get_paths().get("include",""))' 2>/dev/null ||
      python3 -c 'import sysconfig; print(sysconfig.get_paths().get("include",""))' 2>/dev/null ||
      true
  )"
  if [[ -z ${py_include} || ! -f ${py_include}/Python.h ]]; then
    return 1
  fi
  if ! find_libcuda_dir >/dev/null; then
    return 1
  fi
  return 0
}

#######################################
# Point ComfyUI/output at the host bind-mount (/outputs).
# Migrates leftover files from a real output/ dir on the named volume.
# Globals:
#   COMFY_HOME, LAB_OUTPUTS_MOUNT
# Arguments:
#   $1 - Optional Comfy output path (default COMFY_HOME/output)
# Outputs:
#   Progress logs
# Returns:
#   0
#######################################
link_comfy_output_dir() {
  local dest="${1:-}"
  local mount="${LAB_OUTPUTS_MOUNT:-/outputs}"
  if [[ -z ${dest} ]]; then
    dest="${COMFY_HOME:-/comfy-state/ComfyUI}/output"
  fi
  mkdir -p "${mount}"
  if [[ -d ${dest} && ! -L ${dest} ]]; then
    if [[ -n "$(ls -A "${dest}" 2>/dev/null || true)" ]]; then
      ep_log "Migrating existing Comfy output/ into ${mount}"
      if command -v rsync >/dev/null 2>&1; then
        rsync -a "${dest}/" "${mount}/"
      else
        cp -a "${dest}/." "${mount}/"
      fi
    fi
    rm -rf "${dest}"
  elif [[ -L ${dest} || -e ${dest} ]]; then
    rm -f "${dest}"
  fi
  ln -sfn "${mount}" "${dest}"
  ep_log "Comfy output → ${mount} (host COMFY_OUTPUT_DIR bind-mount)"
}

#######################################
# Prefer working Triton; disable torch python_native Triton when deps missing.
# Globals:
#   LAB_DISABLE_TORCH_NATIVE_TRITON, PYTHONPATH
# Arguments:
#   None
# Outputs:
#   Progress logs; may export env for sitecustomize
# Returns:
#   0 always
#######################################
configure_torch_native_triton() {
  local py_root="${LAB_PYTHONPATH_ROOT:-/opt/ez-comfy/pythonpath}"
  # Always expose sitecustomize so the disable flag can take effect.
  if [[ -d ${py_root} ]]; then
    case ":${PYTHONPATH:-}:" in
      *":${py_root}:"*) ;;
      *)
        export PYTHONPATH="${py_root}${PYTHONPATH:+:${PYTHONPATH}}"
        ;;
    esac
  fi

  if [[ ${LAB_DISABLE_TORCH_NATIVE_TRITON:-0} == "1" ]]; then
    ep_log "LAB_DISABLE_TORCH_NATIVE_TRITON=1 — torch.backends.python_native.triton off"
    return 0
  fi

  if triton_build_deps_ok; then
    ep_log "Triton JIT deps OK (gcc + Python.h + libcuda) — native Triton enabled"
    export LAB_DISABLE_TORCH_NATIVE_TRITON=0
    return 0
  fi

  export LAB_DISABLE_TORCH_NATIVE_TRITON=1
  ep_log "WARN: Triton JIT deps incomplete — disabling torch.backends.python_native.triton"
  ep_log "WARN: CLIP still works via eager/cuBLAS. Fix: image with python3-dev+gcc, GPU toolkit mounts"
  return 0
}

#######################################
# Run install, seed, patch, and exec ComfyUI.
# Globals:
#   COMFY_HOME, VENV, LAB_*
# Arguments:
#   None
# Outputs:
#   Progress on stdout/stderr
# Returns:
#   Does not return on success (exec)
#######################################
main() {
  local install_cmd="${LAB_ENTRYPOINT_INSTALL_CMD:-bash /opt/ez-comfy/install-comfy.sh}"
  local comfy_home venv stamp vol_pin want
  # Read outer COMFY_HOME env before assigning locals
  comfy_home="${COMFY_HOME:-/comfy-state/ComfyUI}"
  venv="${comfy_home}/.venv"
  stamp="${comfy_home}/.lab-install-complete"
  LAB_PREBUILT_ROOT="${LAB_PREBUILT_ROOT:-/opt/comfy-prebuilt}"
  export PYTHONUNBUFFERED=1
  export COMFY_HOME="${comfy_home}"

  ep_log "══ start ══ COMFY_HOME=${comfy_home}"
  ep_log "phase 1/4: prepare ComfyUI tree"

  if [[ ${LAB_FORCE_COLD_INSTALL:-0} == "1" ]]; then
    ep_log "LAB_FORCE_COLD_INSTALL=1 — full pip install (slow)"
    # shellcheck disable=SC2086
    ${install_cmd}
  elif [[ -f ${stamp} && -x ${venv}/bin/python ]]; then
    vol_pin="$(tr -d '\n' <"${comfy_home}/.lab-comfyui-ref" 2>/dev/null || true)"
    want="${COMFYUI_REF:-v0.34.0}"
    if [[ ${vol_pin} != "${want}" ]]; then
      ep_log "Comfy pin needs sync (${vol_pin:-unset} → ${want})"
      if prebuilt_ready; then
        ep_log "Re-seeding volume from prebuilt"
        seed_from_prebuilt
      else
        ep_log "Prebuilt missing — install refresh will clone COMFYUI_REF"
      fi
    fi
    ep_log "Install stamp present — refresh (pin sync + links + patch)"
    # shellcheck disable=SC2086
    ${install_cmd}
  elif prebuilt_ready; then
    ep_log "Prebuilt image detected — seeding volume (skip multi-GB pip)"
    seed_from_prebuilt
    # Refresh path: model links + patch (stamp already in prebuilt)
    # shellcheck disable=SC2086
    ${install_cmd}
  else
    ep_log "No prebuilt tree — cold install (10–30+ min; multi-GB wheels)"
    # shellcheck disable=SC2086
    ${install_cmd}
  fi
  ep_log "phase 1/4: prepare finished"

  if [[ ! -x "${venv}/bin/python" ]]; then
    ep_log "ERROR: venv missing at ${venv}"
    exit 1
  fi

  # shellcheck disable=SC1091
  source "${venv}/bin/activate"

  ep_log "phase 2/4: free-memory patch (best-effort)"
  if [[ -f /opt/ez-comfy/patch_get_free_memory.py ]]; then
    python3 /opt/ez-comfy/patch_get_free_memory.py "${comfy_home}" || true
  fi

  ep_log "phase 3/4: install lab workflows into user workflows"
  mkdir -p "${comfy_home}/user/default/workflows"
  local wf n_wf=0
  if [[ -d /opt/ez-comfy/workflows ]]; then
    for wf in /opt/ez-comfy/workflows/*.json; do
      [[ -f ${wf} ]] || continue
      cp -f "${wf}" "${comfy_home}/user/default/workflows/"
      n_wf=$((n_wf + 1))
      ep_log "installed workflow $(basename "${wf}")"
    done
  fi
  if [[ ${n_wf} -eq 0 ]]; then
    ep_log "no workflows under /opt/ez-comfy/workflows (optional mount)"
  else
    ep_log "installed ${n_wf} workflow(s)"
  fi

  export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
  ensure_triton_build_env
  configure_torch_native_triton
  cd "${comfy_home}"
  link_comfy_output_dir "${comfy_home}/output"
  ep_log "phase 4/4: exec ComfyUI → 0.0.0.0:8188 (output ${LAB_OUTPUTS_MOUNT:-/outputs})"
  if [[ ${LAB_ENTRYPOINT_NO_EXEC:-} == "1" ]]; then
    ep_log "LAB_ENTRYPOINT_NO_EXEC=1; skipping exec"
    return 0
  fi
  exec python main.py --listen 0.0.0.0 --port 8188 \
    --output-directory "${LAB_OUTPUTS_MOUNT:-/outputs}"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi

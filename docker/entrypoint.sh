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
# Print paths that prebuilt seed must not overwrite.
# Includes operator custom_nodes/_user (host bind). Never rm -rf that tree.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   One exclude pattern per line on stdout
# Returns:
#   0
#######################################
prebuilt_exclude_patterns() {
  printf '%s\n' \
    user/ \
    input/ \
    output/ \
    temp/ \
    extra_model_paths.yaml \
    custom_nodes/_user/
}

#######################################
# Copy prebuilt tree into dest honoring seed excludes (rsync missing).
# Does not --delete dest-only files. Never writes custom_nodes/_user.
# Globals:
#   None
# Arguments:
#   $1  source prebuilt root
#   $2  destination COMFY_HOME
# Outputs:
#   None
# Returns:
#   0
#######################################
copy_prebuilt_tree() {
  local src="${1:?}"
  local dest="${2:?}"
  local item base pack
  mkdir -p "${dest}"
  (
    shopt -s dotglob nullglob
    for item in "${src}"/*; do
      base="$(basename "${item}")"
      case "${base}" in
        user | input | output | temp | extra_model_paths.yaml) continue ;;
      esac
      if [[ ${base} == custom_nodes && -d ${item} ]]; then
        mkdir -p "${dest}/custom_nodes"
        for pack in "${item}"/*; do
          [[ -e ${pack} ]] || continue
          if [[ $(basename "${pack}") == _user ]]; then
            continue
          fi
          cp -a "${pack}" "${dest}/custom_nodes/"
        done
        continue
      fi
      cp -a "${item}" "${dest}/"
    done
  )
}

#######################################
# Copy prebuilt Comfy tree onto the volume (local disk; no pip).
# rsync --exclude (or copy_prebuilt_tree) skips user/, input/, output/,
# temp/, extra_model_paths.yaml, and custom_nodes/_user/. Never --delete
# those trees. Image includes rsync; cp fallback honors the same list.
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
  local -a rsync_excludes=()
  local pat
  ep_log "Seeding ${dest} from ${root} (local copy — not re-downloading torch)"
  mkdir -p "${dest}"
  while IFS= read -r pat; do
    rsync_excludes+=(--exclude "${pat}")
  done < <(prebuilt_exclude_patterns)
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --info=progress2 "${rsync_excludes[@]}" "${root}/" "${dest}/" ||
      rsync -a "${rsync_excludes[@]}" "${root}/" "${dest}/"
  else
    ep_log "rsync missing; using cp -a with seed excludes (no progress bar)"
    copy_prebuilt_tree "${root}" "${dest}"
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
# Point ComfyUI/input at the host bind-mount (/inputs).
# Migrates leftover files from a real input/ dir on the named volume.
# Globals:
#   COMFY_HOME, LAB_INPUTS_MOUNT
# Arguments:
#   $1 - Optional Comfy input path (default COMFY_HOME/input)
# Outputs:
#   Progress logs
# Returns:
#   0
#######################################
link_comfy_input_dir() {
  local dest="${1:-}"
  local mount="${LAB_INPUTS_MOUNT:-/inputs}"
  if [[ -z ${dest} ]]; then
    dest="${COMFY_HOME:-/comfy-state/ComfyUI}/input"
  fi
  mkdir -p "${mount}"
  if [[ -d ${dest} && ! -L ${dest} ]]; then
    if [[ -n "$(ls -A "${dest}" 2>/dev/null || true)" ]]; then
      ep_log "Migrating existing Comfy input/ into ${mount}"
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
  ep_log "Comfy input → ${mount} (host COMFY_OUTPUT_DIR/input bind-mount)"
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
# True if a lab graph should seed as Comfy .app.json (Apps sidebar).
# Comfy AppsSidebarTab lists suffix app.json; Workflows lists every JSON.
# Parse failure or missing python3 is not an app (start still copies .json).
# Globals:
#   None
# Arguments:
#   $1  path to workflow JSON
# Outputs:
#   None
# Returns:
#   0 if extra.linearMode is true or lab_app_mode default_view is app
#######################################
lab_workflow_is_app() {
  local path="${1:?}"
  if ! command -v python3 >/dev/null 2>&1; then
    return 1
  fi
  python3 - "${path}" <<'PY'
import json
import sys

path = sys.argv[1]
try:
    extra = json.load(open(path, encoding="utf-8")).get("extra") or {}
except (OSError, json.JSONDecodeError, TypeError, AttributeError):
    raise SystemExit(1)
if extra.get("linearMode") is True:
    raise SystemExit(0)
mode = extra.get("lab_app_mode") or {}
if (
    isinstance(mode, dict)
    and mode.get("enabled") is True
    and mode.get("default_view") == "app"
):
    raise SystemExit(0)
raise SystemExit(1)
PY
}

#######################################
# Map a workflow path relative to the workflows root onto a sidebar lane.
# Prefers _lab/<lane>/…; else filename/dir globs used during the flat-tree
# transition (deleted after git mv into workflows/_lab).
# Globals:
#   None
# Arguments:
#   $1  relative path (e.g. _lab/klein/foo.json or klein-foo.json)
# Outputs:
#   Lane name on stdout
# Returns:
#   0 when mapped; 1 when the path must not be seeded
#######################################
lab_workflow_lane() {
  local rel="${1:?}"
  local rest
  rel="${rel#./}"
  case "${rel}" in
    _lab/*)
      rest="${rel#_lab/}"
      rest="${rest%%/*}"
      if [[ -z ${rest} || ${rest} == _user ]]; then
        return 1
      fi
      printf '%s\n' "${rest}"
      return 0
      ;;
    shorts/*) printf '%s\n' shorts ;;
    dcc/*) printf '%s\n' dcc ;;
    optional/*) printf '%s\n' optional ;;
    klein-*) printf '%s\n' klein ;;
    wan-*) printf '%s\n' wan ;;
    ltx-*) printf '%s\n' ltx ;;
    podcast-* | music-*) printf '%s\n' audio ;;
    prompt-forge-* | beat-sheet-*) printf '%s\n' inspire ;;
    *) return 1 ;;
  esac
}

#######################################
# Sync JSON under src into dest, preserving relative folders.
# Prefers rsync -a --delete scoped to dest (JSON only). Without rsync,
# find+cp then delete dest *.json that are not in src. Never copies
# *.shots.yaml, NOTICE.md, or non-JSON.
# Globals:
#   None
# Arguments:
#   $1  source directory
#   $2  destination directory
# Outputs:
#   None
# Returns:
#   0
#######################################
sync_lab_json_dir() {
  local src="${1:?}"
  local dest="${2:?}"
  local path rel tmp
  mkdir -p "${dest}"
  if [[ ! -d ${src} ]]; then
    return 0
  fi
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
      --include='*/' \
      --include='*.json' \
      --exclude='*' \
      "${src}/" "${dest}/"
    return 0
  fi
  tmp="$(mktemp -d)"
  while IFS= read -r -d '' path; do
    rel="${path#"${src}"/}"
    mkdir -p "${tmp}/$(dirname "${rel}")"
    cp -a "${path}" "${tmp}/${rel}"
  done < <(find "${src}" -type f -name '*.json' -print0)
  while IFS= read -r -d '' path; do
    rel="${path#"${dest}"/}"
    if [[ ! -f ${tmp}/${rel} ]]; then
      rm -f "${path}"
    fi
  done < <(find "${dest}" -type f -name '*.json' -print0)
  while IFS= read -r -d '' path; do
    rel="${path#"${tmp}"/}"
    mkdir -p "${dest}/$(dirname "${rel}")"
    cp -a "${path}" "${dest}/${rel}"
  done < <(find "${tmp}" -type f -name '*.json' -print0)
  rm -rf "${tmp}"
}

#######################################
# Map legacy flat repo globs into dest/_lab/<lane>/ then sync --delete.
# Transition only: used when src/_lab is absent. Do not copy quality/,
# YAML, NOTICE, or _user/.
# Globals:
#   None
# Arguments:
#   $1  source workflows root
#   $2  destination _lab directory
# Outputs:
#   None
# Returns:
#   0
#######################################
seed_legacy_lab_workflows() {
  local src="${1:?}"
  local dest_lab="${2:?}"
  local tmp wf rel lane
  tmp="$(mktemp -d)"
  (
    shopt -s nullglob
    for wf in \
      "${src}"/*.json \
      "${src}"/shorts/*.json \
      "${src}"/dcc/*.json \
      "${src}"/optional/*.json; do
      [[ -f ${wf} ]] || continue
      rel="${wf#"${src}"/}"
      lane="$(lab_workflow_lane "${rel}")" || continue
      mkdir -p "${tmp}/${lane}"
      cp -a "${wf}" "${tmp}/${lane}/$(basename "${wf}")"
    done
  )
  sync_lab_json_dir "${tmp}" "${dest_lab}"
  rm -rf "${tmp}"
}

#######################################
# Rename dest _lab App Mode graphs to stem.app.json (Apps sidebar).
# Films and default_view graph stay *.json. Walks after rsync so --delete
# can restore git *.json then this pass rewrites the dest name.
# Globals:
#   None
# Arguments:
#   $1  destination _lab directory
# Outputs:
#   None
# Returns:
#   0
#######################################
apply_lab_app_json_names() {
  local dest_lab="${1:?}"
  local wf dir stem
  [[ -d ${dest_lab} ]] || return 0
  while IFS= read -r -d '' wf; do
    [[ ${wf} == *.app.json ]] && continue
    dir="$(dirname "${wf}")"
    stem="$(basename "${wf}" .json)"
    if lab_workflow_is_app "${wf}"; then
      mv -f "${wf}" "${dir}/${stem}.app.json"
    fi
  done < <(find "${dest_lab}" -type f -name '*.json' -print0)
}

#######################################
# Log seeded JSON counts per sidebar lane.
# Globals:
#   None
# Arguments:
#   $1  destination _lab directory
# Outputs:
#   ep_log lines
# Returns:
#   0
#######################################
log_lab_seed_counts() {
  local dest_lab="${1:?}"
  local lane n total=0
  local -a lanes=(klein wan ltx shorts dcc optional audio inspire)
  for lane in "${lanes[@]}"; do
    n=0
    if [[ -d ${dest_lab}/${lane} ]]; then
      n="$(find "${dest_lab}/${lane}" -type f -name '*.json' | wc -l | tr -d ' ')"
    fi
    if [[ ${n} -gt 0 ]]; then
      ep_log "installed ${n} workflow(s) in _lab/${lane}"
      total=$((total + n))
    fi
  done
  if [[ ${total} -eq 0 ]]; then
    ep_log "no workflows under ${dest_lab}"
  else
    ep_log "installed ${total} workflow(s) under _lab/"
  fi
}

#######################################
# Copy host lab JSON into Comfy user/default/workflows/_lab/<lane>/.
# Preferred: rsync -a --delete src/_lab/ → dest/_lab/ (JSON only).
# Transition: when src/_lab is missing, map legacy flat globs into _lab/.
# Then rename App Mode graphs to stem.app.json in dest only.
# Never writes dest/_user/ or dest root. Never copies YAML, NOTICE, quality/.
# Globals:
#   None
# Arguments:
#   $1  source workflows root (default /opt/ez-comfy/workflows)
#   $2  destination user/default/workflows
# Outputs:
#   ep_log lines
# Returns:
#   0
#######################################
install_lab_workflows() {
  local src="${1:-/opt/ez-comfy/workflows}"
  local dest="${2:?}"
  mkdir -p "${dest}/_lab" "${dest}/_user"
  if [[ ! -d ${src} ]]; then
    ep_log "no workflows under ${src} (optional mount)"
    return 0
  fi
  if [[ -d ${src}/_lab ]]; then
    sync_lab_json_dir "${src}/_lab" "${dest}/_lab"
  else
    seed_legacy_lab_workflows "${src}" "${dest}/_lab"
  fi
  apply_lab_app_json_names "${dest}/_lab"
  log_lab_seed_counts "${dest}/_lab"
}

#######################################
# Copy one in-tree custom-node pack into Comfy custom_nodes.
# Bind-mounted like workflows so node edits skip image rebuild.
# Globals:
#   None
# Arguments:
#   $1  source pack directory (must contain __init__.py)
#   $2  destination directory
# Outputs:
#   ep_log lines
# Returns:
#   0
#######################################
install_lab_custom_nodes() {
  local src="${1:-}"
  local dest="${2:?}"
  if [[ -z ${src} || ! -d ${src} || ! -f "${src}/__init__.py" ]]; then
    ep_log "no custom node pack under ${src:-unset} (optional mount)"
    return 0
  fi
  mkdir -p "$(dirname "${dest}")"
  rm -rf "${dest}"
  cp -a "${src}" "${dest}"
  rm -rf "${dest}/__pycache__" "${dest}/.pytest_cache"
  ep_log "installed custom node $(basename "${dest}")"
}

#######################################
# Print ComfyUI CLI tokens (one per line) for GB10 unified memory.
# Kitchen XOR Sage: never includes --use-sage-attention.
# Default VRAM (omit --highvram / --gpu-only / --lowvram). ComfyUI v0.34+
# dropped --normalvram; passing it exits with unrecognized arguments.
# Globals:
#   LAB_OUTPUTS_MOUNT
# Arguments:
#   None
# Outputs:
#   argv tokens on stdout
# Returns:
#   0
#######################################
comfy_exec_args() {
  printf '%s\n' \
    --listen \
    0.0.0.0 \
    --port \
    8188 \
    --output-directory \
    "${LAB_OUTPUTS_MOUNT:-/outputs}" \
    --input-directory \
    "${LAB_INPUTS_MOUNT:-/inputs}" \
    --use-ck-attention \
    --disable-dynamic-vram \
    --disable-pinned-memory \
    --disable-async-offload \
    --dont-upcast-attention \
    --reserve-vram \
    1 \
    --bf16-unet \
    --bf16-vae \
    --bf16-text-enc \
    --disable-mmap
}

#######################################
# Copy every in-tree pack under a root into Comfy custom_nodes.
# Globals:
#   None
# Arguments:
#   $1  source root (default /opt/ez-comfy/custom_nodes)
#   $2  destination custom_nodes directory
# Outputs:
#   ep_log lines
# Returns:
#   0
#######################################
install_all_lab_custom_nodes() {
  local src_root="${1:-/opt/ez-comfy/custom_nodes}"
  local dest_root="${2:?}"
  local src dest n pack
  n=0
  if [[ ! -d ${src_root} ]]; then
    ep_log "no custom node packs under ${src_root} (optional mount)"
    return 0
  fi
  mkdir -p "${dest_root}"
  for src in "${src_root}"/*; do
    [[ -d ${src} && -f "${src}/__init__.py" ]] || continue
    pack="$(basename "${src}")"
    dest="${dest_root}/${pack}"
    install_lab_custom_nodes "${src}" "${dest}"
    n=$((n + 1))
  done
  if [[ ${n} -eq 0 ]]; then
    ep_log "no custom node packs under ${src_root}"
  else
    ep_log "installed ${n} custom node pack(s)"
  fi
}

#######################################
# True when venv python can execute a one-liner import.
# Globals:
#   None
# Arguments:
#   $1  Python interpreter
#   $2  Statement passed to python -c
# Outputs:
#   None
# Returns:
#   0 when the statement succeeds; 1 otherwise
#######################################
dub_python_can_import() {
  local py="${1:?}"
  local stmt="${2:?}"
  "${py}" -c "${stmt}" >/dev/null 2>&1
}

#######################################
# Interpreter Comfy will exec (after venv activate). Prefer VIRTUAL_ENV.
# Globals:
#   VIRTUAL_ENV, COMFY_HOME
# Arguments:
#   None
# Outputs:
#   Absolute python path on stdout
# Returns:
#   0 when a python exists; 1 otherwise
#######################################
comfy_runtime_python() {
  local py
  if [[ -n ${VIRTUAL_ENV:-} && -x ${VIRTUAL_ENV}/bin/python ]]; then
    printf '%s\n' "${VIRTUAL_ENV}/bin/python"
    return 0
  fi
  py="${COMFY_HOME:-/comfy-state/ComfyUI}/.venv/bin/python"
  if [[ -x ${py} ]]; then
    printf '%s\n' "${py}"
    return 0
  fi
  py="$(command -v python 2>/dev/null || true)"
  if [[ -n ${py} && -x ${py} ]]; then
    printf '%s\n' "${py}"
    return 0
  fi
  return 1
}

#######################################
# pip-install faster-whisper into the Comfy venv. Fail-soft. Does not touch torch.
# Globals:
#   None
# Arguments:
#   $1  venv python
# Outputs:
#   ep_log
# Returns:
#   0 always (soft-fail)
#######################################
install_dub_asr_wheel() {
  local py="${1:?}"
  ep_log "dub ASR: pip install faster-whisper"
  if "${py}" -m pip install --upgrade-strategy only-if-needed faster-whisper; then
    ep_log "dub ASR: faster-whisper installed"
    return 0
  fi
  ep_log "WARN: faster-whisper pip failed — Queue writes empty mix"
  return 0
}

#######################################
# pip-install chatterbox extras then chatterbox-tts --no-deps. Fail-soft.
# --no-deps so the package cannot pin torch==2.6.0 over the lab venv.
# Globals:
#   None
# Arguments:
#   $1  venv python
# Outputs:
#   ep_log
# Returns:
#   0 always (soft-fail)
#######################################
install_dub_clone_wheel() {
  local py="${1:?}"
  local -a extras=(
    librosa
    s3tokenizer
    resemble-perth
    conformer
    pykakasi
    pyloudnorm
    omegaconf
  )
  ep_log "dub clone: extras then chatterbox-tts --no-deps (skip torch pin)"
  "${py}" -m pip install --upgrade-strategy only-if-needed "${extras[@]}" || true
  if "${py}" -m pip install --no-deps chatterbox-tts; then
    ep_log "dub clone: chatterbox-tts --no-deps installed"
    return 0
  fi
  ep_log "WARN: chatterbox-tts --no-deps failed"
  return 0
}

# Official llama-cpp-python CPU wheels (aarch64 manylinux py3-none). PyPI is
# sdist-only; --only-binary against PyPI always misses on DGX Spark.
LLAMA_CPP_CPU_INDEX="https://abetlen.github.io/llama-cpp-python/whl/cpu"

#######################################
# pip-install llama-cpp-python CPU wheel into the Comfy venv. Fail-soft.
# Binaries only (no compile). Does not touch torch. CUDA extra-index unused.
# Globals:
#   LLAMA_CPP_CPU_INDEX
# Arguments:
#   $1  venv python
# Outputs:
#   ep_log
# Returns:
#   0 always (soft-fail)
#######################################
install_llama_cpp_cpu_wheel() {
  local py="${1:?}"
  local index="${LLAMA_CPP_CPU_INDEX}"
  ep_log "llama.cpp: pip install llama-cpp-python (CPU extra-index, binaries only)"
  if "${py}" -m pip install --only-binary=:all: --extra-index-url "${index}" \
    llama-cpp-python; then
    ep_log "llama.cpp: llama-cpp-python CPU wheel installed"
    return 0
  fi
  ep_log "WARN: llama-cpp-python CPU wheel pip failed — Enhance/dub translation will pass through"
  return 0
}

#######################################
# Heal missing llama-cpp-python on an existing named volume. Import-check first.
# Existing ez-comfy-state volumes are not re-seeded when COMFYUI_REF matches,
# so baked image wheels never arrive unless we pip here.
# Globals:
#   COMFY_HOME
# Arguments:
#   None
# Outputs:
#   ep_log
# Returns:
#   0 always (soft-fail)
#######################################
ensure_llama_cpp_cpu() {
  local py
  if ! py="$(comfy_runtime_python)"; then
    ep_log "llama.cpp: venv python missing — skip"
    return 0
  fi
  ep_log "llama.cpp: python=${py}"
  if dub_python_can_import "${py}" "from llama_cpp import Llama"; then
    ep_log "llama.cpp: Llama already importable"
    return 0
  fi
  install_llama_cpp_cpu_wheel "${py}"
  return 0
}

#######################################
# Heal missing dub wheels on an existing named volume. Import-check first.
# Existing ez-comfy-state volumes are not re-seeded when COMFYUI_REF matches,
# so baked image wheels never arrive unless we pip here or via download-dub.
# Globals:
#   COMFY_HOME
# Arguments:
#   None
# Outputs:
#   ep_log
# Returns:
#   0 always (soft-fail)
#######################################
ensure_dub_wheels() {
  local py
  if ! py="$(comfy_runtime_python)"; then
    ep_log "dub wheels: venv python missing — skip"
    return 0
  fi
  ep_log "dub wheels: python=${py}"
  if dub_python_can_import "${py}" "from faster_whisper import WhisperModel"; then
    ep_log "dub ASR: WhisperModel already importable"
  else
    install_dub_asr_wheel "${py}"
  fi
  if dub_python_can_import "${py}" \
    "from chatterbox.mtl_tts import ChatterboxMultilingualTTS"; then
    ep_log "dub clone: ChatterboxMultilingualTTS already importable"
  else
    install_dub_clone_wheel "${py}"
  fi
  return 0
}

#######################################
# Write an empty custom_nodes/_user pack so Comfy does not FileNotFoundError.
# Never overwrites an operator __init__.py.
# Globals:
#   COMFY_HOME
# Arguments:
#   $1  Optional _user directory (default $COMFY_HOME/custom_nodes/_user)
# Outputs:
#   ep_log
# Returns:
#   0 always
#######################################
ensure_user_custom_node_stub() {
  local dest init
  dest="${1:-${COMFY_HOME:-/comfy-state/ComfyUI}/custom_nodes/_user}"
  mkdir -p "${dest}"
  init="${dest}/__init__.py"
  if [[ -f ${init} ]]; then
    ep_log "operator custom_nodes/_user already has __init__.py"
    return 0
  fi
  cat >"${init}" <<'PY'
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
PY
  ep_log "wrote empty custom_nodes/_user stub (Comfy requires __init__.py)"
  return 0
}

#######################################
# True when the given python imports a real nunchaku SVDQuant engine.
# Globals:
#   None
# Arguments:
#   $1  Python interpreter
# Outputs:
#   None
# Returns:
#   0 if real engine; 1 otherwise
#######################################
nunchaku_engine_importable() {
  local py="${1:?}"
  dub_python_can_import "${py}" \
    "import importlib.util, nunchaku, sys; sys.exit(0 if (hasattr(nunchaku, 'NunchakuFluxTransformer2dModel') or importlib.util.find_spec('nunchaku.models') is not None) else 1)"
}

#######################################
# Hide ComfyUI-nunchaku when the engine is missing (Comfy skips *.disabled).
# Globals:
#   COMFY_HOME
# Arguments:
#   None
# Outputs:
#   ep_log
# Returns:
#   0 always
#######################################
configure_nunchaku_pack() {
  local custom enabled disabled py
  custom="${COMFY_HOME:-/comfy-state/ComfyUI}/custom_nodes"
  enabled="${custom}/ComfyUI-nunchaku"
  disabled="${custom}/ComfyUI-nunchaku.disabled"
  mkdir -p "${custom}"
  py="$(comfy_runtime_python 2>/dev/null || true)"
  if [[ -n ${py} ]] && nunchaku_engine_importable "${py}"; then
    if [[ -d ${disabled} && ! -d ${enabled} ]]; then
      mv "${disabled}" "${enabled}"
      ep_log "nunchaku node enabled (engine importable)"
    fi
    return 0
  fi
  if [[ -d ${enabled} ]]; then
    rm -rf "${disabled}"
    mv "${enabled}" "${disabled}"
    ep_log "nunchaku node disabled (no engine wheel; lab graphs use core loaders)"
  fi
  return 0
}

#######################################
# Seed ez_house_clay_01..10.png into /inputs when missing or wrong size.
# Host start still prefers layout-accurate plates. Fail-soft.
# Globals:
#   LAB_INPUTS_MOUNT
# Arguments:
#   None
# Outputs:
#   ep_log
# Returns:
#   0 always
#######################################
seed_clay_inputs_if_missing() {
  local dest="${LAB_INPUTS_MOUNT:-/inputs}"
  local script="${LAB_SEED_CLAY_PY:-/opt/ez-comfy/seed_clay_inputs.py}"
  if [[ ! -f ${script} ]]; then
    ep_log "clay seed: seed_clay_inputs.py missing — skip"
    return 0
  fi
  mkdir -p "${dest}"
  if python3 "${script}" "${dest}"; then
    ep_log "clay plates ready in ${dest}"
    return 0
  fi
  ep_log "WARN: clay seed backstop failed — klein-dream-house-clay LoadImage may be empty"
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
    want="${COMFYUI_REF:-v0.34.6}"
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

  ep_log "phase 2/4: free-memory + unified-memory copy + MagCache compat patches (best-effort)"
  if [[ -f /opt/ez-comfy/patch_get_free_memory.py ]]; then
    python3 /opt/ez-comfy/patch_get_free_memory.py "${comfy_home}" || true
  fi
  if [[ -f /opt/ez-comfy/patch_unified_memory_copy.py ]]; then
    python3 /opt/ez-comfy/patch_unified_memory_copy.py "${comfy_home}" || true
  fi
  if [[ -f /opt/ez-comfy/patch_magcache_compat.py ]]; then
    python3 /opt/ez-comfy/patch_magcache_compat.py "${comfy_home}" || true
  fi

  ep_log "phase 3/4: install lab workflows and custom nodes"
  install_lab_workflows /opt/ez-comfy/workflows "${comfy_home}/user/default/workflows"
  install_all_lab_custom_nodes \
    "${LAB_CUSTOM_NODES_SRC:-/opt/ez-comfy/custom_nodes}" \
    "${comfy_home}/custom_nodes"
  ensure_user_custom_node_stub "${comfy_home}/custom_nodes/_user"
  configure_nunchaku_pack

  export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
  export TORCH_COMPILE_DISABLE="${TORCH_COMPILE_DISABLE:-1}"
  export OMP_NUM_THREADS="${OMP_NUM_THREADS:-20}"
  ensure_triton_build_env
  configure_torch_native_triton
  ensure_llama_cpp_cpu
  ensure_dub_wheels
  cd "${comfy_home}"
  link_comfy_output_dir "${comfy_home}/output"
  link_comfy_input_dir "${comfy_home}/input"
  seed_clay_inputs_if_missing
  ep_log "phase 4/4: exec ComfyUI → 0.0.0.0:8188 (output ${LAB_OUTPUTS_MOUNT:-/outputs}; input ${LAB_INPUTS_MOUNT:-/inputs}; Kitchen attention)"
  if [[ ${LAB_ENTRYPOINT_NO_EXEC:-} == "1" ]]; then
    ep_log "LAB_ENTRYPOINT_NO_EXEC=1; skipping exec"
    return 0
  fi
  local -a exec_args=()
  local tok
  while IFS= read -r tok; do
    exec_args+=("${tok}")
  done < <(comfy_exec_args)
  exec python main.py "${exec_args[@]}"
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi

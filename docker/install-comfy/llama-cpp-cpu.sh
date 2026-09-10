#!/usr/bin/env bash
#
# ## install-comfy/llama-cpp-cpu.sh
#
# Shared llama-cpp-python CPU-wheel pins and install helpers.
# PyPI is sdist-only; the official CPU extra-index is the primary index so
# --only-binary does not stop on that sdist. No CUDA extra-index.
#
# Sourced by phase-nodes.sh, entrypoint.sh, and manage.sh.
#

if [[ -n ${_EZ_LLAMA_CPP_CPU_LOADED:-} ]]; then
  return 0
fi
_EZ_LLAMA_CPP_CPU_LOADED=1

LLAMA_CPP_CPU_INDEX="https://abetlen.github.io/llama-cpp-python/whl/cpu"
PYPI_SIMPLE_INDEX="https://pypi.org/simple"
LLAMA_CPP_CPU_VERSION="0.3.35"
LLAMA_CPP_CPU_PKG="llama-cpp-python==${LLAMA_CPP_CPU_VERSION}"

#######################################
# Direct GitHub release wheel URL for this uname -m (Linux manylinux).
# Globals:
#   LLAMA_CPP_CPU_VERSION
# Arguments:
#   None
# Outputs:
#   HTTPS wheel URL on stdout, or empty when the arch is unknown
# Returns:
#   0
#######################################
llama_cpp_direct_wheel_url() {
  local machine
  machine="$(uname -m)"
  case "${machine}" in
    aarch64 | arm64)
      printf '%s\n' \
        "https://github.com/abetlen/llama-cpp-python/releases/download/v${LLAMA_CPP_CPU_VERSION}/llama_cpp_python-${LLAMA_CPP_CPU_VERSION}-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl"
      ;;
    x86_64 | amd64)
      printf '%s\n' \
        "https://github.com/abetlen/llama-cpp-python/releases/download/v${LLAMA_CPP_CPU_VERSION}/llama_cpp_python-${LLAMA_CPP_CPU_VERSION}-py3-none-manylinux2014_x86_64.manylinux_2_17_x86_64.whl"
      ;;
    *)
      printf '%s\n' ""
      ;;
  esac
}

#######################################
# pip argv for the CPU extra-index install (one token per line).
# Globals:
#   LLAMA_CPP_CPU_INDEX, PYPI_SIMPLE_INDEX, LLAMA_CPP_CPU_PKG
# Arguments:
#   None
# Outputs:
#   pip install operands on stdout
# Returns:
#   0
#######################################
llama_cpp_cpu_pip_index_args() {
  printf '%s\n' \
    --only-binary=:all: \
    --index-url \
    "${LLAMA_CPP_CPU_INDEX}" \
    --extra-index-url \
    "${PYPI_SIMPLE_INDEX}" \
    "${LLAMA_CPP_CPU_PKG}"
}

#######################################
# pip argv to replace a same-version wheel from the GitHub manylinux URL.
# --no-deps keeps torch 2.14. Empty when the arch has no published wheel.
# Globals:
#   LLAMA_CPP_CPU_VERSION
# Arguments:
#   None
# Outputs:
#   pip install operands on stdout, or nothing when the URL is unknown
# Returns:
#   0
#######################################
llama_cpp_direct_wheel_pip_args() {
  local wheel
  wheel="$(llama_cpp_direct_wheel_url)"
  if [[ -z ${wheel} ]]; then
    return 0
  fi
  printf '%s\n' \
    --force-reinstall \
    --no-deps \
    --only-binary=:all: \
    "${wheel}"
}

#######################################
# True when the interpreter can import llama_cpp.Llama.
# Globals:
#   None
# Arguments:
#   $1  Python interpreter
# Outputs:
#   None
# Returns:
#   0 when import succeeds; 1 otherwise
#######################################
llama_cpp_python_can_import() {
  local py="${1:?}"
  "${py}" -c "from llama_cpp import Llama" >/dev/null 2>&1
}

#######################################
# pip-install the CPU wheel into $1, then import-check. Fail-soft for callers.
# Tries the CPU extra-index as --index-url, then the arch GitHub wheel URL.
# Globals:
#   LLAMA_CPP_CPU_INDEX, PYPI_SIMPLE_INDEX, LLAMA_CPP_CPU_PKG
# Arguments:
#   $1  venv python
# Outputs:
#   None (callers log)
# Returns:
#   0 when Llama imports; 1 after both pip attempts fail
#######################################
install_llama_cpp_cpu_wheel() {
  local py="${1:?}"
  local -a args=()
  while IFS= read -r tok; do
    args+=("${tok}")
  done < <(llama_cpp_cpu_pip_index_args)
  if "${py}" -m pip install "${args[@]}" &&
    llama_cpp_python_can_import "${py}"; then
    return 0
  fi
  args=()
  while IFS= read -r tok; do
    args+=("${tok}")
  done < <(llama_cpp_direct_wheel_pip_args)
  if [[ ${#args[@]} -gt 0 ]] &&
    "${py}" -m pip install "${args[@]}" &&
    llama_cpp_python_can_import "${py}"; then
    return 0
  fi
  return 1
}

#!/usr/bin/env bash
#
# ## install-comfy/qwen-tts.sh
#
# Optional Qwen3-TTS wheel extras. Official qwen-tts pins
# transformers==4.57.3 — never install it unconstrained on the lab venv
# (Comfy 0.34.6 + torch 2.14+cu130). Extras first, then --no-deps.
#
# Sourced by manage.sh. Not baked into phase-nodes / ensure_dub_wheels.
#

if [[ -n ${_EZ_QWEN_TTS_LOADED:-} ]]; then
  return 0
fi
_EZ_QWEN_TTS_LOADED=1

#######################################
# Safe extras for qwen-tts --no-deps (one package per line).
# Does not include transformers, accelerate, gradio, or torchaudio.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Package names on stdout
# Returns:
#   0
#######################################
qwen_tts_extra_packages() {
  printf '%s\n' \
    einops \
    soundfile
}

#######################################
# PyPI package name for the optional Qwen3-TTS wheel.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Package name on stdout
# Returns:
#   0
#######################################
qwen_tts_wheel() {
  printf '%s\n' "qwen-tts"
}

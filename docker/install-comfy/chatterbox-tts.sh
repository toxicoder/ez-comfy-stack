#!/usr/bin/env bash
#
# ## install-comfy/chatterbox-tts.sh
#
# Shared Chatterbox Multilingual V3 pin, zip URL, and clone extras.
# PyPI chatterbox-tts==0.1.7 predates from_local(..., t3_model="v3") (PR #516).
# Install the GitHub zip --no-deps so the package cannot pin torch==2.6.0.
# resemble-perth 1.0.1 still imports pretrained weights via pkg_resources,
# which setuptools 82 removed — pin setuptools<82 so PerTh stays on.
#
# Sourced by common.sh, phase-nodes.sh, entrypoint.sh, and manage.sh.
#

if [[ -n ${_EZ_CHATTERBOX_TTS_LOADED:-} ]]; then
  return 0
fi
_EZ_CHATTERBOX_TTS_LOADED=1

CHATTERBOX_TTS_REF="${CHATTERBOX_TTS_REF:-5de7a54aa4e5e2baadb0182dde554908b48b85c2}"
# resemble-perth 1.0.1 needs pkg_resources (removed in setuptools 82).
CHATTERBOX_SETUPTOOLS_PIN="setuptools<82"

#######################################
# GitHub archive URL for the Chatterbox V3-capable source tree.
# Globals:
#   CHATTERBOX_TTS_REF
# Arguments:
#   None
# Outputs:
#   HTTPS zip URL on stdout
# Returns:
#   0
#######################################
chatterbox_tts_zip_url() {
  echo "https://github.com/resemble-ai/chatterbox/archive/${CHATTERBOX_TTS_REF}.zip"
}

#######################################
# setuptools pin so PerTh (resemble-perth) can import pkg_resources.
# Must be pip-installed without --upgrade-strategy only-if-needed so 82+
# can downgrade.
# Globals:
#   CHATTERBOX_SETUPTOOLS_PIN
# Arguments:
#   None
# Outputs:
#   pip requirement on stdout
# Returns:
#   0
#######################################
chatterbox_setuptools_pin() {
  printf '%s\n' "${CHATTERBOX_SETUPTOOLS_PIN}"
}

#######################################
# Chatterbox clone extras (one package per line). Does not include
# setuptools — that pin is chatterbox_setuptools_pin.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Package names on stdout
# Returns:
#   0
#######################################
chatterbox_clone_extra_packages() {
  printf '%s\n' \
    librosa \
    s3tokenizer \
    resemble-perth \
    conformer \
    pykakasi \
    pyloudnorm \
    omegaconf \
    spacy-pkuseg
}

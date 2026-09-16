#!/usr/bin/env bash
# ## blender_host
#
# Resolve a host Blender binary for Workbench dumps. Never in docker/Dockerfile.
# Source after scripts/lib/common.sh (uses err). Not executable.
#
# Safety:
#   Does not start Compose. Does not apt-install unless blender-install.sh
#   is invoked. Does not weaken restart: "no", headroom, or download-limit.

#######################################
# Ordered candidate paths for a host blender binary.
# Globals:
#   BLENDER_BIN, HOME, PATH
# Arguments:
#   None
# Outputs:
#   One absolute or operator-supplied path per line
# Returns:
#   0
#######################################
blender_host_candidates() {
  if [[ -n ${BLENDER_BIN:-} ]]; then
    printf '%s\n' "${BLENDER_BIN}"
  fi
  local which_bin=""
  which_bin="$(command -v blender 2>/dev/null || true)"
  if [[ -n ${which_bin} ]]; then
    printf '%s\n' "${which_bin}"
  fi
  local home="${HOME:-}"
  if [[ -n ${home} ]]; then
    printf '%s\n' "${home}/.local/bin/blender"
    printf '%s\n' "${home}/.local/opt/blender/blender"
  fi
  # System prefixes are skipped under LAB_HERMETIC so missing-binary tests
  # stay closed on hosts that already have apt blender.
  if [[ ${LAB_HERMETIC:-} == "1" ]]; then
    return 0
  fi
  printf '%s\n' /usr/bin/blender
  printf '%s\n' /usr/local/bin/blender
  printf '%s\n' /snap/bin/blender
  printf '%s\n' /opt/blender/blender
}

#######################################
# First executable host blender path.
# Globals:
#   BLENDER_BIN, HOME, PATH
# Arguments:
#   None
# Outputs:
#   Absolute or operator-supplied path on stdout when found
# Returns:
#   0 when an executable exists; 1 when missing
#######################################
blender_host_bin() {
  local cand
  while IFS= read -r cand; do
    [[ -n ${cand} ]] || continue
    if [[ -f ${cand} && -x ${cand} ]]; then
      printf '%s\n' "${cand}"
      return 0
    fi
  done < <(blender_host_candidates)
  return 1
}

#######################################
# Print host-install hint when blender is missing.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Hint on stderr
# Returns:
#   0
#######################################
print_blender_host_hint() {
  err "blender not on PATH. Host install only — never in docker/Dockerfile."
  err "occupancy enter blender-desk does not install Blender."
  err "Install: ./scripts/manage.sh blender-install"
  err "  or: sudo apt-get install -y blender"
  err "No Blender → house-views --seed-inputs or klein/dream-house (T2I)."
  err "See docs/blender-gb10-sidecar.md"
}

#######################################
# Fail unless a host blender binary can be resolved.
# Globals:
#   BLENDER_BIN, HOME, PATH
# Arguments:
#   None
# Outputs:
#   Install hint on stderr when missing
# Returns:
#   0 present; 1 missing
#######################################
require_blender() {
  if blender_host_bin >/dev/null; then
    return 0
  fi
  print_blender_host_hint
  return 1
}

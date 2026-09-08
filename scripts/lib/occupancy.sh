#!/usr/bin/env bash
# ## occupancy
#
# Shared compose-up refuse for host GPU sidecars (Blender, NVENC, guide dump,
# house-views).
# Source after scripts/lib/compose.sh. Not executable.
#
# Safety:
#   One heavy GPU job on GB10. ComfyUI compose XOR host DCC/NVENC/TRELLIS.
#   Does not weaken restart: "no", mem_limit, or headroom.

#######################################
# Refuse when studio compose (comfyui) is running.
# Globals:
#   None (compose_is_running uses compose project env)
# Arguments:
#   $1  Optional job label (default: host GPU sidecar (occupancy))
# Outputs:
#   Error on stderr when compose is up
# Returns:
#   0 idle; 2 when ComfyUI is running
#######################################
refuse_if_comfy_running() {
  local job="${1:-host GPU sidecar (occupancy)}"
  if compose_is_running; then
    err "ComfyUI is running — stop it before ${job}"
    return 2
  fi
  return 0
}

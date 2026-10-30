#!/usr/bin/env bash
#
# ## compose_config_test
#
# Validate docker/docker-compose.yml the way Compose itself parses it.
#
# Purpose:
#   Run `docker compose config -q` over the compose file the stack starts, so
#   a broken anchor, a duplicate key, an unresolvable environment reference, or
#   a service that no longer parses fails a Bazel gate instead of failing the
#   operator's first `./scripts/manage.sh start`. Compose validates the merged
#   document, which no text-level gate here reproduces.
#
# Usage:
#   bash docker/compose_config_test.sh
#   bazelisk test //docker:compose_config
#
# Safety: Read-only. It renders the configuration and writes nothing: no
#   container is created, no image is pulled, no daemon state is touched, and
#   the stack's restart: "no" policy is never exercised.
#
# Requirements:
#   docker CLI (the config subcommand is client-side; no daemon is required
#   for the checks that matter here).
#
# Exit codes:
#   0 when the compose file renders cleanly, or when the docker CLI is absent
#     and the gate is running outside strict lint mode.
#   1 when docker is missing under REQUIRE_LINT_TOOLS=1, when the checkout
#     root cannot be located, or when Compose reports a problem.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n ${TEST_SRCDIR:-} && -f ${TEST_SRCDIR}/_main/scripts/lib/check_tool.sh ]]; then
  # shellcheck source=../scripts/lib/check_tool.sh disable=SC1091
  source "${TEST_SRCDIR}/_main/scripts/lib/check_tool.sh"
elif [[ -n ${BUILD_WORKSPACE_DIRECTORY:-} ]]; then
  # shellcheck source=../scripts/lib/check_tool.sh disable=SC1091
  source "${BUILD_WORKSPACE_DIRECTORY}/scripts/lib/check_tool.sh"
else
  # shellcheck source=../scripts/lib/check_tool.sh disable=SC1091
  source "${SCRIPT_DIR}/../scripts/lib/check_tool.sh"
fi

# Compose file under test, relative to the checkout root.
COMPOSE_FILE="docker/docker-compose.yml"

#######################################
# Render the compose file and require it to parse.
# Globals:
#   COMPOSE_FILE
# Arguments:
#   None
# Outputs:
#   Compose diagnostics on stdout/stderr; a skip line when docker is absent
# Returns:
#   0 when the file renders, 1 when it does not or the root is unreachable
#######################################
run_compose_config() {
  local root
  root="$(bazel_checkout_root)"
  if [[ ! -f ${root}/${COMPOSE_FILE} ]]; then
    echo "compose_config_test: no ${COMPOSE_FILE} under ${root}" >&2
    return 1
  fi
  echo "Running docker compose config -q on ${COMPOSE_FILE}..."
  if ! docker compose -f "${root}/${COMPOSE_FILE}" config -q; then
    echo "compose_config_test: ${COMPOSE_FILE} does not render" >&2
    return 1
  fi
  echo "Compose config is valid."
}

#######################################
# Compose config entrypoint.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Status line plus Compose diagnostics
# Returns:
#   0 on success or an intentional skip; 1 on a validation failure
#######################################
main() {
  check_tool docker "install the Docker CLI (docker compose config is client-side)"
  run_compose_config
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi

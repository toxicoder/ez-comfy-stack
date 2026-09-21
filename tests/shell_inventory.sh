#!/usr/bin/env bash
#
# ## shell_inventory
#
# Strict gate: every function in scripts/**/*.sh and docker/**/*.sh must be
# named under tests/.
#
# Usage:
#   bash tests/shell_inventory.sh
#   bazelisk test //tests:shell_inventory
#
# Safety: Read-only source scan.

set -euo pipefail
# ASCII function names; keep comm and sort in the same order on every runner.
export LC_ALL=C

# shellcheck source=repo_root.sh disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/repo_root.sh"
ROOT="$(tests_repo_root)"
cd "${ROOT}"

#######################################
# Collect production function names from scripts/ and docker/*.sh.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Sorted unique function names
# Returns:
#   0
#######################################
list_production_functions() {
  {
    grep -RhoE '^[a-zA-Z_][a-zA-Z0-9_]*\(\)' scripts --include='*.sh' 2>/dev/null || true
    grep -RhoE '^[a-zA-Z_][a-zA-Z0-9_]*\(\)' docker --include='*.sh' 2>/dev/null || true
  } | sed 's/()//' | sort -u
}

#######################################
# Identifiers named under tests/, comments stripped.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Sorted unique identifiers, one per line
# Returns:
#   0
#######################################
list_test_identifiers() {
  # One scan. A per-function grep of this blob exceeds the 60s CI timeout.
  grep -hvE '^[[:space:]]*(#|//)' \
    tests/bats/*.bats tests/bats/*.bash tests/python/*.py tests/*.sh 2>/dev/null |
    grep -hoE '[A-Za-z_][A-Za-z0-9_]*' |
    sort -u || true
}

#######################################
# Fail when a production function is not named under tests/.
# Globals:
#   None
# Arguments:
#   None
# Outputs:
#   Missing names on stderr
# Returns:
#   0 when complete; 1 when missing
#######################################
main() {
  echo "=== Shell function inventory (strict: must appear under tests/) ==="
  local funcs missing count
  funcs="$(list_production_functions | grep -vx 'main' || true)"
  missing="$(comm -23 <(printf '%s\n' "${funcs}") <(list_test_identifiers))"
  if [[ -n ${missing} ]]; then
    echo "Untested shell functions (not referenced under tests/):" >&2
    printf '%s\n' "${missing}" >&2
    return 1
  fi
  count="$(printf '%s\n' "${funcs}" | grep -c . || true)"
  echo "All ${count} production shell functions referenced under tests/."
}

if [[ ${BASH_SOURCE[0]} == "${0}" ]]; then
  main "$@"
fi

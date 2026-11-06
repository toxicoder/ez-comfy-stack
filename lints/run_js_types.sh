#!/usr/bin/env bash
# Purpose: typecheck the ComfyUI frontends (custom_nodes/**/*.js) with tsc --checkJs.
#
# The custom-node extensions are plain JavaScript, so their types live in JSDoc.
# TypeScript can check those annotations, but the extensions import ComfyUI's own
# frontend at runtime-only relative paths ("../../scripts/app.js"), which do not
# exist in this repo. --noResolve skips module resolution so the JSDoc types on
# first-party code are still checked; the ComfyUI objects arrive as untyped
# imports, exactly as they do at runtime.
#
# This gate ratchets: lints/js_types_baseline.json records how many diagnostics
# each file still owes. A file may go down, never up, and a new file must be
# listed. Lower a number by replacing a JSDoc `{object}` with a real @typedef.
#
# Requires node + the pinned TypeScript in docs-site/node_modules (same tool the
# docs-site typecheck target uses).
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
ROOT="$(bazel_checkout_root)"
check_tool python3 "install Python 3"
cd "${ROOT}"

TSC="docs-site/node_modules/.bin/tsc"
if [[ ! -x ${TSC} ]]; then
  if [[ ${CI:-} == "true" || ${REQUIRE_LINT_TOOLS:-} == "1" ]]; then
    echo "tsc missing - required in CI/strict mode (cd docs-site && npm ci --legacy-peer-deps)" >&2
    exit 1
  fi
  echo "tsc missing - skipping JS typecheck (cd docs-site && npm ci --legacy-peer-deps)"
  exit 0
fi

BASELINE="lints/js_types_baseline.json"
if [[ ! -f ${BASELINE} ]]; then
  echo "missing ${BASELINE} - the JS typecheck baseline is committed; restore it" >&2
  exit 1
fi

mapfile -t JS_FILES < <(git ls-files 'custom_nodes/**/*.js')
if [[ ${#JS_FILES[@]} -eq 0 ]]; then
  echo "no custom_nodes JS files found - git ls-files failed?" >&2
  exit 1
fi

# --ignoreConfig: docs-site/tsconfig.json would otherwise be picked up and would
# refuse command-line files. --strict false keeps the gate on the JSDoc types the
# files actually claim, not on implicit-any in untyped frontend glue.
ERRS="$(mktemp)"
trap 'rm -f "${ERRS}"' EXIT
"${TSC}" --ignoreConfig --noEmit --allowJs --checkJs --noResolve \
  --target es2022 --module esnext --strict false "${JS_FILES[@]}" >"${ERRS}" 2>&1 || true

python3 - "${BASELINE}" "${ERRS}" <<'PY' || exit 1
"""Compare per-file tsc diagnostics against the committed ratchet baseline."""
import collections
import json
import re
import sys

baseline_path, errors_path = sys.argv[1], sys.argv[2]
allowed = json.load(open(baseline_path, encoding="utf-8"))
pattern = re.compile(r"^(?P<path>custom_nodes/[^ :(]+\.js)\((?P<line>\d+),\d+\): error TS\d+")

counts: collections.Counter[str] = collections.Counter()
for text in open(errors_path, encoding="utf-8"):
    match = pattern.match(text)
    if match:
        counts[match.group("path")] += 1

problems: list[str] = []
for path, count in sorted(counts.items()):
    limit = allowed.get(path)
    if limit is None:
        problems.append(f"{path}: {count} diagnostics and no baseline entry (add it)")
    elif count > limit:
        problems.append(f"{path}: {count} diagnostics, baseline allows {limit}")
for path, limit in sorted(allowed.items()):
    if path not in counts and limit != 0:
        problems.append(f"{path}: baseline says {limit} but the file is now clean - set it to 0")

total = sum(counts.values())
if problems:
    print("JS typecheck ratchet failed:", file=sys.stderr)
    for problem in problems:
        print(f"  {problem}", file=sys.stderr)
    print(
        f"\nTotal diagnostics: {total}. Fix the JSDoc types (replace {{object}} with a "
        "@typedef) instead of raising the baseline.",
        file=sys.stderr,
    )
    raise SystemExit(1)
print(f"JS typecheck passed: {total} diagnostics across {len(counts)} files (within baseline).")
PY

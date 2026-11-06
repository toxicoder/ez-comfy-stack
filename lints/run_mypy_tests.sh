#!/usr/bin/env bash
# Purpose: typecheck the pytest tree with mypy-tests.ini and ratchet the debt.
#
# The production law (mypy.ini, run by tests/typecheck.sh) is absolute: zero
# errors. The pytest tree is held to the same law on paper - full annotations,
# no bare generics, no silent Any returns, no stale ignores - but it carries a
# four-figure backlog of sites where a test hands a fake to a production
# signature that has since been narrowed. Failing the build on all of them at
# once would mean either deleting the lane or deleting the tests, so this gate
# ratchets instead: lints/mypy_tests_baseline.json records how many diagnostics
# each test file still owes.
#
# A file may go down, never up, and a new file must be listed. Lower a number
# by teaching the test to narrow what it gets back (assert isinstance, or a
# typed helper) instead of widening the production signature to suit the fake.
#
# `--write` regenerates the baseline from the current run; use it only as part
# of a deliberate, reviewed decrease.
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

if ! python3 -m mypy --version >/dev/null 2>&1; then
  if [[ ${CI:-} == "true" || ${REQUIRE_LINT_TOOLS:-} == "1" ]]; then
    echo "mypy missing - required in CI/strict mode (pip install -r tests/requirements.txt)" >&2
    exit 1
  fi
  echo "mypy missing - skipping pytest-tree typecheck (pip install -r tests/requirements.txt)"
  exit 0
fi

BASELINE="lints/mypy_tests_baseline.json"
WRITE="${1:-}"
if [[ ! -f ${BASELINE} && ${WRITE} != "--write" ]]; then
  echo "missing ${BASELINE} - the pytest-tree baseline is committed; restore it" >&2
  exit 1
fi

ERRS="$(mktemp)"
trap 'rm -f "${ERRS}"' EXIT
# The exit status is deliberately dropped: the ratchet below decides pass or
# fail, and it needs the diagnostics rather than a short-circuit.
python3 -m mypy --config-file mypy-tests.ini >"${ERRS}" 2>&1 || true

python3 - "${BASELINE}" "${ERRS}" "${WRITE}" <<'PY' || exit 1
"""Compare per-file mypy diagnostics against the committed ratchet baseline."""
import collections
import json
import os
import re
import sys

baseline_path, errors_path, write = sys.argv[1], sys.argv[2], sys.argv[3]
pattern = re.compile(r"^(?P<path>tests/python/[^ :]+\.py):\d+: error: ")

counts: collections.Counter[str] = collections.Counter()
for text in open(errors_path, encoding="utf-8"):
    match = pattern.match(text)
    if match:
        counts[match.group("path")] += 1

total = sum(counts.values())
if write == "--write":
    payload = {"total": total, "files": dict(sorted(counts.items()))}
    tmp = baseline_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(tmp, baseline_path)
    print(f"wrote {baseline_path}: {total} diagnostics across {len(counts)} files")
    raise SystemExit(0)

with open(baseline_path, encoding="utf-8") as handle:
    allowed = json.load(handle)["files"]

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

if problems:
    print("pytest-tree typecheck ratchet failed:", file=sys.stderr)
    for problem in problems:
        print(f"  {problem}", file=sys.stderr)
    print(
        f"\nTotal diagnostics: {total}. Narrow what the test hands a production "
        "signature instead of raising the baseline.",
        file=sys.stderr,
    )
    raise SystemExit(1)

slack = sum(allowed.values()) - total
print(
    f"pytest-tree typecheck passed: {total} diagnostics across {len(counts)} files "
    f"(within baseline{f'; {slack} to reclaim' if slack else ''})."
)
PY

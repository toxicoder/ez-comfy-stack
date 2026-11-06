#!/usr/bin/env bash
# Purpose: Pyright on the pytest tree, ratcheted against a committed ledger.
#
# The production law is tests/typecheck.sh: Pyright over pyrightconfig.json and
# mypy over mypy.ini, both absolute. The pytest tree is held to the same rules
# (pyrightconfig-tests.json) but carries a backlog, so this gate ratchets the
# way lints/run_mypy_tests.sh and lints/run_js_types.sh do:
# lints/pyright_tests_baseline.json records how many diagnostics each test file
# still owes, a file may go down and never up, and a new file must be listed.
#
# Lower a number by naming a type the test was guessing at, not by loosening a
# production signature to suit the fake.
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

if ! python3 -m pyright --version >/dev/null 2>&1; then
  if [[ ${CI:-} == "true" || ${REQUIRE_LINT_TOOLS:-} == "1" ]]; then
    echo "pyright missing - required in CI/strict mode (pip install -r tests/requirements.txt)" >&2
    exit 1
  fi
  echo "pyright missing - skipping pytest-tree typecheck (pip install -r tests/requirements.txt)"
  exit 0
fi

BASELINE="lints/pyright_tests_baseline.json"
WRITE="${1:-}"
if [[ ! -f ${BASELINE} && ${WRITE} != "--write" ]]; then
  echo "missing ${BASELINE} - the pytest-tree baseline is committed; restore it" >&2
  exit 1
fi

OUT="$(mktemp)"
trap 'rm -f "${OUT}"' EXIT
# --outputjson keeps the ledger independent of how pyright phrases a diagnostic,
# and the exit status is dropped on purpose: the comparison below decides.
python3 -m pyright --outputjson --project pyrightconfig-tests.json >"${OUT}" 2>/dev/null || true

python3 - "${BASELINE}" "${OUT}" "${WRITE}" <<'PY' || exit 1
"""Compare per-file pyright diagnostics against the committed ratchet baseline."""
import collections
import json
import os
import sys

baseline_path, report_path, write = sys.argv[1], sys.argv[2], sys.argv[3]
root = os.getcwd()

try:
    with open(report_path, encoding="utf-8") as handle:
        report = json.load(handle)
except (json.JSONDecodeError, OSError) as exc:
    print(f"could not read the pyright report ({exc}) - did pyright crash?", file=sys.stderr)
    raise SystemExit(1) from exc

counts: collections.Counter[str] = collections.Counter()
for diagnostic in report.get("generalDiagnostics", []) + [
    entry for file_ in report.get("files", []) for entry in file_.get("generalDiagnostics", [])
]:
    if diagnostic.get("severity") != "error":
        continue
    path = os.path.relpath(diagnostic["file"], root).replace(os.sep, "/")
    if path.startswith("tests/python/"):
        counts[path] += 1

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
    print("pytest-tree pyright ratchet failed:", file=sys.stderr)
    for problem in problems:
        print(f"  {problem}", file=sys.stderr)
    print(
        f"\nTotal diagnostics: {total}. Name the type the test was guessing at "
        "instead of raising the baseline.",
        file=sys.stderr,
    )
    raise SystemExit(1)

slack = sum(allowed.values()) - total
suffix = f"; {slack} to reclaim" if slack else ""
print(
    f"pytest-tree pyright passed: {total} diagnostics across {len(counts)} files"
    f" (within baseline{suffix})."
)
PY

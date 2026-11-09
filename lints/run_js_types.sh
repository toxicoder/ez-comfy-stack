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
# A second ratchet scores the debt that fix retires directly: the count of
# unnamed JSDoc types the source still claims, against
# lints/js_object_baseline.json. Same law - down only, new file must be listed.
# `--write-types-baseline` and `--write-object-baseline` regenerate one ledger
# each from the current run; use them only inside a deliberate, reviewed
# decrease.
#
# Requires node plus a TypeScript compiler: the pinned one in
# docs-site/node_modules (same tool the docs-site typecheck target uses), or a
# tsc on the PATH when the checkout has none.
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

# The pinned compiler is the one the docs-site lockfile carries, so the JSDoc
# types are checked by the same TypeScript that compiles the site. A tsc on the
# PATH is only consulted when the checkout has none: a stray global version would
# move the diagnostic counts the ratchet records for reasons no diff explains.
TSC="docs-site/node_modules/.bin/tsc"
if [[ ! -x ${TSC} ]]; then
  TSC="$(command -v tsc || true)"
fi
if [[ -z ${TSC} ]]; then
  hint="install the pinned toolchain (bazelisk run //docs-site:install, or cd docs-site && npm ci --legacy-peer-deps)"
  if [[ ${CI:-} == "true" || ${REQUIRE_LINT_TOOLS:-} == "1" ]]; then
    echo "tsc missing - required in CI/strict mode (${hint})" >&2
    exit 1
  fi
  echo "tsc missing - skipping JS typecheck (${hint})"
  exit 0
fi

BASELINE="lints/js_types_baseline.json"
if [[ ! -f ${BASELINE} ]]; then
  echo "missing ${BASELINE} - the JS typecheck baseline is committed; restore it" >&2
  exit 1
fi

WRITE=""
WRITE_TYPES=""
for arg in "$@"; do
  if [[ ${arg} == "--write-object-baseline" ]]; then
    WRITE="${arg}"
  elif [[ ${arg} == "--write-types-baseline" ]]; then
    WRITE_TYPES="${arg}"
  fi
done

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

python3 - "${BASELINE}" "${ERRS}" "${WRITE_TYPES}" <<'PY' || exit 1
"""Compare per-file tsc diagnostics against the committed ratchet baseline."""
import collections
import json
import os
import re
import sys

baseline_path, errors_path, write_types = sys.argv[1], sys.argv[2], sys.argv[3]
pattern = re.compile(r"^(?P<path>custom_nodes/[^ :(]+\.js)\((?P<line>\d+),\d+\): error TS\d+")

counts: collections.Counter[str] = collections.Counter()
for text in open(errors_path, encoding="utf-8"):
    match = pattern.match(text)
    if match:
        counts[match.group("path")] += 1

if write_types == "--write-types-baseline":
    payload = dict(sorted(counts.items()))
    tmp = baseline_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(tmp, baseline_path)
    total_w = sum(counts.values())
    print(f"wrote {baseline_path}: {total_w} diagnostics across {len(counts)} files")
    raise SystemExit(0)

allowed = json.load(open(baseline_path, encoding="utf-8"))

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

# The second ratchet scores the unnamed types themselves rather than the
# diagnostics tsc happens to emit, so the number stays put when untyped
# frontend glue changes shape and only moves when someone names a type.
# `--write-object-baseline` regenerates it; use it only as part of a
# deliberate, reviewed decrease.
JSDOC_BASELINE="lints/js_object_baseline.json"
if [[ ! -f ${JSDOC_BASELINE} && -z ${WRITE} ]]; then
  echo "missing ${JSDOC_BASELINE} - the JSDoc object baseline is committed; restore it" >&2
  exit 1
fi

python3 - "${JSDOC_BASELINE}" "${WRITE}" "${JS_FILES[@]}" <<'PY' || exit 1
"""Ratchet the unnamed JSDoc types the first-party frontends still claim."""
import collections
import json
import os
import re
import sys

baseline_path, write = sys.argv[1], sys.argv[2]
paths = sys.argv[3:]

# A JSDoc type only ever follows a block tag, so prose inside a comment cannot
# move the count. The token has to lead its brace group: `{object|null}` and
# `{object[]}` are the debt, while `{row|null}`, where a name already leads,
# is not. `{Object}` and `{*}` join `{object}` so no spelling is an escape.
# `@typedef` is deliberately absent: that line *is* the act of naming, and its
# base is the Object constructor (`{Object<string, *>}` for a map whose keys the
# file cannot enumerate), which the same policy accepts as an opaque pass-through.
TAG_RE = re.compile(
    r"@(?:param|returns?|type|property|prop|arg|argument|var|dict"
    r"|this|throws?|raises?)\b"
)
UNNAMED_RE = re.compile(r"\{\s*(?:object|Object|\*)(?![\w$])")

counts: collections.Counter[str] = collections.Counter()
for rel in paths:
    with open(rel, encoding="utf-8") as handle:
        for line in handle:
            if TAG_RE.search(line):
                counts[rel] += len(UNNAMED_RE.findall(line))

total = sum(counts.values())
if write == "--write-object-baseline":
    payload = {"total": total, "files": dict(sorted(counts.items()))}
    tmp = baseline_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(tmp, baseline_path)
    print(f"wrote {baseline_path}: {total} unnamed JSDoc types in {len(counts)} files")
    raise SystemExit(0)

with open(baseline_path, encoding="utf-8") as handle:
    allowed = json.load(handle)["files"]

problems: list[str] = []
for path, count in sorted(counts.items()):
    limit = allowed.get(path)
    if limit is None:
        problems.append(f"{path}: {count} unnamed and no baseline entry (add it)")
    elif count > limit:
        problems.append(f"{path}: {count} unnamed JSDoc types, baseline allows {limit}")
for path, limit in sorted(allowed.items()):
    if path not in counts and limit != 0:
        problems.append(f"{path}: baseline says {limit} but the file is now clean - set it to 0")

if problems:
    print("JSDoc object ratchet failed:", file=sys.stderr)
    for problem in problems:
        print(f"  {problem}", file=sys.stderr)
    print(
        f"\nTotal unnamed JSDoc types: {total}. Name the record with an @typedef "
        "instead of raising the baseline.",
        file=sys.stderr,
    )
    raise SystemExit(1)

slack = sum(allowed.values()) - total
print(
    f"JSDoc object ratchet passed: {total} unnamed types in {len(counts)} files "
    f"(within baseline{f'; {slack} to reclaim' if slack else ''})."
)
PY

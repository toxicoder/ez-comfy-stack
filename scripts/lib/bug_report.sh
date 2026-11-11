#!/usr/bin/env bash
#
# ## bug_report helper
#
# Turns a command-line or bazelisk failure into a bug report the operator can
# file in one click. It is the host twin of the browser pack's "Report a bug"
# button (custom_nodes/ez_feedback/): the same section headings, filled from
# what the host can name without a live graph.
#
# Two ways in:
#   - automatic: die() in lib/common.sh, the manage.sh EXIT trap, and the
#     gate()/slice traps in everything.sh and validate.sh call
#     bug_report_hint, which stays quiet unless a human is watching.
#   - explicit: `bazelisk run //:manage -- report-bug` prints the template,
#     saves it, and prints the prefilled URL.
#
# Nothing here submits anything. The prefilled URL is a handoff; the saved
# markdown file is the complete artefact and the one to attach when the URL
# says the body was shortened.
#
# @function bug_report_hint
# Usage:
#   source "$(dirname "$0")/lib/bug_report.sh"
#   bug_report_hint "bazel" "bazelisk test //:test-all" 1 /tmp/test-all.log
#
# Safety: Read-only probes behind a timeout, one 0600 file under
#   EZ_BUG_REPORT_DIR, and a URL string. No network, no sudo, no docker, no
#   GPU, and .env is never read. Only the whitelisted keys below are printed,
#   token-shaped values become [redacted], and $HOME becomes ~.

# Repository issues are filed here; the browser pack files against the same
# repo, so the two entry points cannot drift apart.
EZ_BUG_REPO="${EZ_BUG_REPO:-toxicoder/ez-comfy-stack}"

# Where a run leaves its templates. Under /tmp by design: a bug report is
# scratch, and nothing here may dirty the git checkout.
EZ_BUG_REPORT_DIR="${EZ_BUG_REPORT_DIR:-${TMPDIR:-/tmp}/ez-comfy-stack-bug-reports}"

# Self-imposed safety margin for a prefilled GET URL. GitHub publishes no
# number, so this stays a margin we chose rather than a limit we claim; the
# full text always survives in the saved file regardless of what it is.
BUG_REPORT_MAX_HREF="${BUG_REPORT_MAX_HREF:-5500}"

# Lines of a log file attached as ## Command output.
BUG_REPORT_LOG_TAIL="${BUG_REPORT_LOG_TAIL:-80}"

# Seconds one host probe may take before the line reads "unavailable". A cold
# nvidia-smi must never be able to hang a failure message.
BUG_REPORT_PROBE_TIMEOUT="${BUG_REPORT_PROBE_TIMEOUT:-5}"

# The marker the browser pack uses for a field the operator still owes.
BUG_REPORT_FILL_IN="${BUG_REPORT_FILL_IN:-<!-- Replace this line. -->}"

# Docs page the hint names, kept as a repo-relative path.
BUG_REPORT_DOCS="${BUG_REPORT_DOCS:-docs/operate/reporting-issues.mdx}"

# Body under construction by bug_report_markdown; written by
# _bug_report_add_section and reset at the top of every build.
BUG_REPORT_BODY=""

#######################################
# Decide whether a failing run should print the filing hint.
#
# Off under bats (suites assert on stderr), off when stderr is redirected
# (a pipe or a log is not a human), forced on with EZ_BUG_HINT=1 for a
# non-interactive check, forced off with EZ_BUG_HINT=0 or off.
# Globals:
#   EZ_BUG_HINT, BATS_TEST_FILENAME, BATS_RUN_TMPDIR
# Arguments:
#   None
# Outputs:
#   None
# Returns:
#   0 when the hint should print, 1 when it must stay silent
#######################################
bug_report_enabled() {
  case "${EZ_BUG_HINT:-}" in
    1 | on | true) return 0 ;;
    0 | off | false) return 1 ;;
  esac
  if [[ -n ${BATS_TEST_FILENAME:-} || -n ${BATS_RUN_TMPDIR:-} ]]; then
    return 1
  fi
  if [[ ! -t 2 ]]; then
    return 1
  fi
  return 0
}

#######################################
# Redact standard input: token-shaped secrets and the home directory.
# Globals:
#   HOME
# Arguments:
#   None (reads stdin)
# Outputs:
#   Redacted text on stdout
# Returns:
#   0
#######################################
bug_report_redact_stdin() {
  local text=""
  text="$(
    cat
    printf x
  )"
  text="${text%x}"
  if [[ -n ${HOME:-} ]]; then
    # The replacement is quoted on purpose: an unquoted ~ here is tilde
    # expanded back to $HOME and the substitution silently becomes a no-op.
    text="${text//"${HOME}"/'~'}"
  fi
  printf '%s' "${text}" |
    sed -E 's/(ghp_|gho_|ghu_|ghs_|github_pat_|github_ent_|hf_)[A-Za-z0-9_-]{6,}/[redacted]/g'
}

#######################################
# Strip secrets and machine-specific paths from one value.
# Globals:
#   HOME
# Arguments:
#   $1 - text to redact
# Outputs:
#   Redacted text on stdout
# Returns:
#   0
#######################################
bug_report_redact() {
  printf '%s' "${1:-}" | bug_report_redact_stdin
}

#######################################
# Prefix a title with the surface, mirroring the pack's [app:lane/id] form.
# Globals:
#   None
# Arguments:
#   $1 - title the operator supplied (may be empty)
#   $2 - surface: cli | bazel | compose | download | tui
# Outputs:
#   Title on stdout, prefixed "[cli:<surface>] ..." when it carried no prefix
# Returns:
#   0
#######################################
bug_report_title() {
  local title="${1:-}"
  local surface="${2:-cli}"
  if [[ ${title} == \[*\]* ]]; then
    printf '%s\n' "${title}"
    return 0
  fi
  if [[ -z ${title} ]]; then
    title="command failed"
  fi
  # One bracketed segment, the way the canvas side titles its issues. The
  # default surface is the CLI itself, so saying `cli:cli` would only stutter.
  if [[ ${surface} == "cli" ]]; then
    printf '[cli] %s\n' "${title}"
    return 0
  fi
  printf '[cli:%s] %s\n' "${surface}" "${title}"
}

#######################################
# Slug a title for a filename.
# Globals:
#   None
# Arguments:
#   $1 - title
# Outputs:
#   Lowercase slug of up to 40 characters on stdout
# Returns:
#   0
#######################################
_bug_report_slug() {
  local title="${1:-report}"
  printf '%s' "${title}" |
    tr '[:upper:]' '[:lower:]' |
    sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//' |
    cut -c1-40 |
    sed -E 's/-+$//'
}

#######################################
# Run a command with a bounded runtime.
# Globals:
#   BUG_REPORT_PROBE_TIMEOUT
# Arguments:
#   $@ - command and its arguments
# Outputs:
#   The command's stdout, nothing when it failed or timed out
# Returns:
#   0 always
#######################################
_bug_report_run() {
  if command -v timeout >/dev/null 2>&1; then
    timeout "${BUG_REPORT_PROBE_TIMEOUT}" "$@" 2>/dev/null || true
  else
    "$@" 2>/dev/null || true
  fi
}

#######################################
# Print one "- label: value" line from a best-effort probe.
# Globals:
#   None
# Arguments:
#   $1 - label
#   $@ - command to probe; prints "unavailable" when it is not on PATH
# Outputs:
#   One redacted markdown bullet on stdout
# Returns:
#   0
#######################################
_bug_report_probe() {
  local label="$1"
  shift
  local value="unavailable"
  if [[ -n ${1:-} ]] && command -v "$1" >/dev/null 2>&1; then
    value="$(_bug_report_run "$@" | head -n 1 | tr -d '\r')"
  fi
  _bug_report_line "${label}" "${value}"
}

#######################################
# Print one "- label: value" line from a value the caller already holds.
# Globals:
#   None
# Arguments:
#   $1 - label
#   $2 - value; printed as "unavailable" when empty
# Outputs:
#   One redacted markdown bullet on stdout
# Returns:
#   0
#######################################
_bug_report_line() {
  local label="$1"
  local value="${2:-}"
  if [[ -z ${value} ]]; then
    value="unavailable"
  fi
  printf -- '- %s: %s\n' "${label}" "$(bug_report_redact "${value}")"
}

#######################################
# Print the environment facts a maintainer needs, and only these.
#
# Every probe is best-effort and time-boxed: a host without docker or a GPU
# still gets a report, with "unavailable" in the line that could not answer.
# Globals:
#   REPO_ROOT, MODELS_DIR, COMFY_OUTPUT_DIR, COMFY_PORT, EZ_BUG_REPO
# Arguments:
#   $1 - surface name to record (default cli)
# Outputs:
#   "- key: value" bullets on stdout
# Returns:
#   0
#######################################
bug_report_env_block() {
  local surface="${1:-cli}"

  local os=""
  if [[ -r /etc/os-release ]]; then
    os="$(sed -n 's/^PRETTY_NAME="\(.*\)"$/\1/p' /etc/os-release 2>/dev/null | head -n 1)"
  fi
  if [[ -z ${os} ]]; then
    os="$(_bug_report_run uname -s)"
  fi

  _bug_report_line "surface" "${surface}"
  _bug_report_line "os" "${os}"
  _bug_report_line "kernel" "$(_bug_report_run uname -r)"
  _bug_report_line "arch" "$(_bug_report_run uname -m)"
  _bug_report_line "bash" "${BASH_VERSION:-unavailable}"
  _bug_report_probe "python3" python3 --version
  _bug_report_probe "docker" docker --version
  _bug_report_probe "gpu" nvidia-smi --query-gpu=name,driver_version --format=csv,noheader

  # The pinned version is read from the checkout rather than asked of the
  # binary: `bazelisk --version` can start a server or fetch a release, and a
  # failure message must never depend on either.
  local bazel_version=""
  if [[ -n ${REPO_ROOT:-} && -r "${REPO_ROOT}/.bazelversion" ]]; then
    bazel_version="$(head -n 1 "${REPO_ROOT}/.bazelversion" 2>/dev/null)"
  fi
  _bug_report_line "bazel pin" "${bazel_version}"

  local git_sha="" git_branch=""
  if [[ -n ${REPO_ROOT:-} ]] && command -v git >/dev/null 2>&1; then
    git_sha="$(_bug_report_run git -C "${REPO_ROOT}" rev-parse --short HEAD)"
    git_branch="$(_bug_report_run git -C "${REPO_ROOT}" rev-parse --abbrev-ref HEAD)"
  fi
  _bug_report_line "git sha" "${git_sha}"
  _bug_report_line "git branch" "${git_branch}"

  _bug_report_line "models dir" "${MODELS_DIR:-}"
  _bug_report_line "output dir" "${COMFY_OUTPUT_DIR:-}"
  _bug_report_line "comfy port" "${COMFY_PORT:-}"
  _bug_report_line "repo" "${EZ_BUG_REPO}"
}

#######################################
# Build the tail block of a log file, fenced and redacted.
# Globals:
#   BUG_REPORT_LOG_TAIL
# Arguments:
#   $1 - log path
# Outputs:
#   A fenced block on stdout; empty when the log is missing or unreadable
# Returns:
#   0
#######################################
_bug_report_log_block() {
  local log_file="${1:-}"
  if [[ -z ${log_file} || ! -r ${log_file} ]]; then
    return 0
  fi
  local tail_text
  tail_text="$(tail -n "${BUG_REPORT_LOG_TAIL}" "${log_file}" 2>/dev/null | bug_report_redact_stdin)"
  if [[ -z ${tail_text//[$' \t\n']/} ]]; then
    return 0
  fi
  printf '```\n%s\n```' "${tail_text}"
}

#######################################
# Append one section to the body under construction.
#
# A section whose content is blank is skipped whole, which is what keeps a
# report free of empty headings.
# Globals:
#   BUG_REPORT_BODY (appended to)
# Arguments:
#   $1 - `## ` heading
#   $2 - block content; the section is skipped when blank
# Outputs:
#   None (writes BUG_REPORT_BODY)
# Returns:
#   0 always
#######################################
_bug_report_add_section() {
  local heading="$1"
  local content="${2:-}"
  content="${content//$'\r'/}"
  if [[ -z ${content//[$' \t\n']/} ]]; then
    return 0
  fi
  if [[ -n ${BUG_REPORT_BODY} ]]; then
    BUG_REPORT_BODY+=$'\n\n'
  fi
  BUG_REPORT_BODY+="${heading}"$'\n\n'"${content}"
  return 0
}

#######################################
# Build the full bug-report markdown body.
#
# The headings match the browser pack so a CLI-filed report reads like one
# filed from the studio. Operator prose is left as the pack's fill-in marker;
# everything the host can answer is already filled.
# Globals:
#   BUG_REPORT_FILL_IN, BUG_REPORT_BODY (reset then written)
# Arguments:
#   $1 - title (used for the file name by callers; the body carries no title)
#   $2 - surface: cli | bazel | compose | download | tui
#   $3 - the failing command line
#   $4 - the exit status it returned
#   $5 - optional log file to attach
# Outputs:
#   Markdown body on stdout
# Returns:
#   0
#######################################
bug_report_markdown() {
  local surface="${2:-cli}"
  local command_text="${3:-}"
  local code="${4:-1}"
  local log_file="${5:-}"
  BUG_REPORT_BODY=""

  local steps
  if [[ -n ${command_text} ]]; then
    steps="$(printf 'Run the failing command again:\n\n```\n%s\n```' \
      "$(bug_report_redact "${command_text}")")"
  else
    steps="${BUG_REPORT_FILL_IN}"
  fi

  _bug_report_add_section "## What happened" "${BUG_REPORT_FILL_IN}"
  _bug_report_add_section "## Steps" "${steps}"
  _bug_report_add_section "## Expected" "${BUG_REPORT_FILL_IN}"
  _bug_report_add_section "## Actual" "The command exited with status ${code}."
  _bug_report_add_section "## Environment" "$(bug_report_env_block "${surface}")"
  _bug_report_add_section "## Command output" "$(_bug_report_log_block "${log_file}")"

  printf '%s\n' "${BUG_REPORT_BODY}"
}

#######################################
# Build the prefilled GitHub new-issue URL.
#
# Encoded and fitted in one python3 pass so the cut lands on a line boundary
# and the URL cannot come back over budget. Without python3 the URL still
# carries title and labels, which is enough to open the right form.
# Globals:
#   EZ_BUG_REPO, BUG_REPORT_MAX_HREF
# Arguments:
#   $1 - title (already prefixed)
#   $2 - body markdown
#   $3 - labels, comma-separated (default bug)
# Outputs:
#   The URL on stdout
# Returns:
#   0
#######################################
bug_report_url() {
  local title="${1:-}"
  local body="${2:-}"
  local labels="${3:-bug}"

  if command -v python3 >/dev/null 2>&1; then
    local href=""
    href="$(
      EZ_BUG_REPO="${EZ_BUG_REPO}" \
        BUG_REPORT_TITLE="${title}" \
        BUG_REPORT_BODY="${body}" \
        BUG_REPORT_LABELS="${labels}" \
        BUG_REPORT_MAX_HREF="${BUG_REPORT_MAX_HREF}" \
        python3 - <<'PY' 2>/dev/null
import os
import urllib.parse

repo = os.environ["EZ_BUG_REPO"]
title = os.environ["BUG_REPORT_TITLE"]
labels = os.environ["BUG_REPORT_LABELS"]
body = os.environ["BUG_REPORT_BODY"]
cap = int(os.environ["BUG_REPORT_MAX_HREF"])
note = "\n\n[body shortened to fit the URL - attach the saved markdown file for the full report]"


def href_for(text):
    query = urllib.parse.urlencode(
        {"title": title, "body": text, "labels": labels}
    )
    return "https://github.com/%s/issues/new?%s" % (repo, query)


link = href_for(body)
if len(link) > cap:
    lines = body.split("\n")
    low, high = 0, len(lines)
    while low < high:
        mid = (low + high + 1) // 2
        if len(href_for("\n".join(lines[:mid]) + note)) <= cap:
            low = mid
        else:
            high = mid - 1
    link = href_for("\n".join(lines[:low]) + note)
print(link)
PY
    )" || href=""
    if [[ -n ${href} ]]; then
      printf '%s\n' "${href}"
      return 0
    fi
  fi

  # No python3, or it failed: the essentials still open the right form, and
  # the saved file stays the complete artefact.
  local safe_title
  safe_title="$(printf '%s' "${title}" | tr -d '"%&?#' | tr ' ' '+')"
  printf 'https://github.com/%s/issues/new?title=%s&labels=%s\n' \
    "${EZ_BUG_REPO}" "${safe_title}" "${labels}"
}

#######################################
# Save a report template and print where it went.
# Globals:
#   EZ_BUG_REPORT_DIR
# Arguments:
#   $1 - markdown body
#   $2 - optional title to name the file after
# Outputs:
#   Absolute path of the saved file on stdout
# Returns:
#   0 even when the write failed, so a hint can never fail a dying shell
#######################################
bug_report_write() {
  local markdown="${1:-}"
  local title="${2:-bug-report}"
  local dir="${EZ_BUG_REPORT_DIR}"

  local stamp slug path
  stamp="$(date -u +%Y%m%dT%H%M%SZ 2>/dev/null || printf 'unknown')"
  slug="$(_bug_report_slug "${title}")"
  if [[ -z ${slug} ]]; then
    slug="bug-report"
  fi
  path="${dir}/${stamp}-${slug}.md"

  mkdir -p "${dir}" 2>/dev/null || true
  if printf '%s\n' "${markdown}" >"${path}" 2>/dev/null; then
    chmod 600 "${path}" 2>/dev/null || true
  fi
  printf '%s\n' "${path}"
}

#######################################
# Summarise a failing command line into a short title.
# Globals:
#   None
# Arguments:
#   $1 - the failing command line
#   $2 - its exit status
# Outputs:
#   Title text on stdout
# Returns:
#   0
#######################################
_bug_report_failure_title() {
  local command_text="${1:-}"
  local code="${2:-1}"
  if [[ -z ${command_text} ]]; then
    printf 'command failed (exit %s)\n' "${code}"
    return 0
  fi
  local summary="${command_text}"
  if ((${#summary} > 70)); then
    summary="${summary:0:70}..."
  fi
  printf '"%s" exited %s\n' "${summary}" "${code}"
}

#######################################
# Print the filing hint for a failure, once, to a watching human.
#
# The only entry point the error paths call. Stderr only, never fails the
# caller, never touches the network, and silent unless bug_report_enabled
# says a person is at the terminal.
# Globals:
#   BUG_REPORT_DOCS
# Arguments:
#   $1 - surface: cli | bazel | compose | download | tui (default cli)
#   $2 - the failing command line (may be empty)
#   $3 - the exit status (default 1)
#   $4 - optional log file to attach
# Outputs:
#   Four stderr lines: saved template, prefilled URL, re-file command, docs
# Returns:
#   0 always
#######################################
bug_report_hint() {
  bug_report_enabled || return 0

  local surface="${1:-cli}"
  local command_text="${2:-}"
  local code="${3:-1}"
  local log_file="${4:-}"

  local title body saved href
  title="$(_bug_report_failure_title "${command_text}" "${code}")"
  body="$(bug_report_markdown "unused" "${surface}" "${command_text}" "${code}" "${log_file}")" || true
  if [[ -z ${body} ]]; then
    return 0
  fi
  saved="$(bug_report_write "${body}" "${title}")" || true
  href="$(bug_report_url "$(bug_report_title "${title}" "${surface}")" "${body}" "bug")" || true

  printf '%s\n' "[ez-comfy][BUG] Template saved: ${saved}" >&2
  printf '%s\n' "[ez-comfy][BUG] Open on GitHub: ${href}" >&2
  printf '[ez-comfy][BUG] Re-file it: bazelisk run //:manage -- report-bug --surface %q --command %q --exit %q\n' \
    "${surface}" "${command_text}" "${code}" >&2
  printf '%s\n' "[ez-comfy][BUG] Attach the saved file when the URL says the body was shortened. Docs: ${BUG_REPORT_DOCS}" >&2
  return 0
}

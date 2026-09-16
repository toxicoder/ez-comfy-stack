#!/usr/bin/env bash
# ## films
#
# Shared film catalog helpers for host utilities (slug, cap, shot count).
#
# Purpose:
#   One lookup for shipped film ids so concat / accept / compile / print-shot
#   do not copy go-see|still-here|switchyard case maps. Reads
#   custom_nodes/ez_film/catalog.py via python3.
#
# Audience:
#   Sourced by film utilities after common.sh. Requires REPO_ROOT.
#
# Style:
#   Google Shell Style Guide (project deviations in docs/project-conventions.md).
#

#######################################
# Call ez_film.catalog and print one field.
# Globals:
#   REPO_ROOT
# Arguments:
#   $1  field (slug|cap|shots|beats|acts|master|ids)
#   $2  optional film id
#   $@  extra argv after film (e.g. --act 1)
# Outputs:
#   Field value on stdout
# Returns:
#   0; 1 on unknown film or missing python
#######################################
ez_film_catalog() {
  PYTHONPATH="${REPO_ROOT}/custom_nodes${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 -c "from ez_film.catalog import _cli; import sys; raise SystemExit(_cli(sys.argv[1:]))" "$@"
}

#######################################
# Map film id to output prefix slug.
# Globals:
#   REPO_ROOT
# Arguments:
#   $1  film id
# Outputs:
#   slug on stdout
# Returns:
#   0 known; 1 unknown
#######################################
film_slug() {
  ez_film_catalog slug "${1:-}"
}

#######################################
# Publish cap seconds for a film (90.00 or 450.00).
# Globals:
#   REPO_ROOT
# Arguments:
#   $1  film id
# Outputs:
#   cap on stdout
# Returns:
#   0 known; 1 unknown
#######################################
film_publish_cap() {
  ez_film_catalog cap "${1:-}"
}

#######################################
# Printer count for a film (18 or 90).
# Globals:
#   REPO_ROOT
# Arguments:
#   $1  film id
# Outputs:
#   integer on stdout
# Returns:
#   0 known; 1 unknown
#######################################
film_total_shots() {
  ez_film_catalog shots "${1:-}"
}

#######################################
# Beat count for a film (6 or 30).
# Globals:
#   REPO_ROOT
# Arguments:
#   $1  film id
# Outputs:
#   integer on stdout
# Returns:
#   0 known; 1 unknown
#######################################
film_beats() {
  ez_film_catalog beats "${1:-}"
}

#######################################
# Act count for a film (1 or 5).
# Globals:
#   REPO_ROOT
# Arguments:
#   $1  film id
# Outputs:
#   integer on stdout
# Returns:
#   0 known; 1 unknown
#######################################
film_acts() {
  ez_film_catalog acts "${1:-}"
}

#######################################
# Published MP4 basename for a film (optional --act N).
# Globals:
#   REPO_ROOT
# Arguments:
#   $1  film id
#   $@  extra catalog argv
# Outputs:
#   basename on stdout
# Returns:
#   0 known; 1 unknown
#######################################
film_master_name() {
  local film="${1:-}"
  shift || true
  ez_film_catalog master "${film}" "$@"
}

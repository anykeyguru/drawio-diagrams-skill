#!/usr/bin/env bash
# Update this skill in place from its repository: `/drawio-diagrams update`.
#
#   scripts/update.sh            update from https://github.com/anykeyguru/drawio-diagrams-skill.git
#
# Installed with git (git clone): fast-forward to the repository's main branch.
# Refuses when the installed copy has local changes or has diverged; nothing is
# overwritten silently.
# Installed without git (copied, unzipped): the current copy is backed up to
# ~/.cache/drawio-diagrams/ (outside the skills folder, where a second SKILL.md
# would load as a duplicate skill) and replaced by a fresh clone.
#
# DRAWIO_SKILL_REPO / DRAWIO_SKILL_BRANCH override the source (used by the tests).
set -euo pipefail

REPO="${DRAWIO_SKILL_REPO:-https://github.com/anykeyguru/drawio-diagrams-skill.git}"
BRANCH="${DRAWIO_SKILL_BRANCH:-main}"

# Updating rewrites this very file, and bash reads a script while running it:
# run from a temporary copy instead.
if [ -z "${_DRAWIO_UPDATE_COPY:-}" ]; then
  dir="$(cd "$(dirname "$0")/.." && pwd)"
  copy="$(mktemp "${TMPDIR:-/tmp}/drawio-update.XXXXXX")"
  cp "$0" "$copy"
  _DRAWIO_UPDATE_COPY="$copy" SKILL_DIR="$dir" exec bash "$copy" "$@"
fi
trap 'rm -f "$_DRAWIO_UPDATE_COPY"' EXIT

DIR="$SKILL_DIR"
if ! grep -q '^name: *drawio-diagrams *$' "$DIR/SKILL.md" 2>/dev/null; then
  echo "update: $DIR does not look like the drawio-diagrams skill (no SKILL.md with its name); nothing changed" >&2
  exit 1
fi
old="$(cat "$DIR/VERSION" 2>/dev/null || echo unknown)"

if [ -d "$DIR/.git" ]; then
  cd "$DIR"
  if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "update: the installed skill has local changes; nothing changed:" >&2
    git status --short --untracked-files=no >&2
    echo "commit or stash them (or 'git checkout -- .' to drop them), then run the update again" >&2
    exit 2
  fi
  before="$(git rev-parse HEAD)"
  git fetch --quiet "$REPO" "$BRANCH"
  if ! git merge --ff-only --quiet FETCH_HEAD 2>/dev/null; then
    echo "update: the installed copy has commits the repository does not have; nothing changed" >&2
    echo "push them or reset to the repository ('git reset --hard FETCH_HEAD'), then run the update again" >&2
    exit 3
  fi
  new="$(cat VERSION 2>/dev/null || echo unknown)"
  if [ "$before" = "$(git rev-parse HEAD)" ]; then
    echo "drawio-diagrams $new: already up to date"
  else
    echo "drawio-diagrams updated: $old -> $new"
    git log --oneline --no-decorate "$before..HEAD"
  fi
else
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"; rm -f "$_DRAWIO_UPDATE_COPY"' EXIT
  git clone --quiet --depth 1 --branch "$BRANCH" "$REPO" "$tmp/new"
  backup="${XDG_CACHE_HOME:-$HOME/.cache}/drawio-diagrams/backup-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$(dirname "$backup")"
  cp -R "$DIR" "$backup"
  find "$DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  cp -R "$tmp/new/." "$DIR/"
  new="$(cat "$DIR/VERSION" 2>/dev/null || echo unknown)"
  echo "drawio-diagrams updated: $old -> $new (now a git install; the previous copy is in $backup)"
fi

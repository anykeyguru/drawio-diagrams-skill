#!/usr/bin/env bash
# scripts/update.sh against a local "remote": git install, local changes, zip
# install, already up to date. Prints "  ok …" / "  FAIL …"; exit 1 on failure.
set -uo pipefail
cd "$(dirname "$0")/.."
src_dir="$(pwd)"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
export XDG_CACHE_HOME="$tmp/cache" DRAWIO_SKILL_REPO="$tmp/remote.git" DRAWIO_SKILL_BRANCH=main
g() { git -c user.name=test -c user.email=test@example.com -c init.defaultBranch=main "$@"; }
fail=0
ok() { echo "  ok    $1"; }
no() { echo "  FAIL  $1"; fail=1; }

# the "remote": the skill's current files at version 1.0.0
mkdir "$tmp/src"
(cd "$src_dir" && tar cf - --exclude .git --exclude dist --exclude 'tests/cases' --exclude '__pycache__' .) | (cd "$tmp/src" && tar xf -)
echo 1.0.0 > "$tmp/src/VERSION"
(cd "$tmp/src" && g init -q && g add -A && g commit -qm "v1.0.0" && g clone -q --bare . "$tmp/remote.git")
bump() { (cd "$tmp/src" && echo "$1" > VERSION && g commit -qam "v$1" && g push -q "$tmp/remote.git" HEAD:main); }

# 1. git install: fast-forward
g clone -q "$tmp/remote.git" "$tmp/skills/drawio-diagrams"
bump 1.1.0
out="$(bash "$tmp/skills/drawio-diagrams/scripts/update.sh" 2>&1)"; rc=$?
if [ $rc -eq 0 ] && [ "$(cat "$tmp/skills/drawio-diagrams/VERSION")" = 1.1.0 ] && grep -q "1.0.0 -> 1.1.0" <<<"$out"; then
  ok "git install: fast-forwarded 1.0.0 -> 1.1.0"; else no "git install update: rc=$rc $out"; fi

# 2. nothing new
out="$(bash "$tmp/skills/drawio-diagrams/scripts/update.sh" 2>&1)"; rc=$?
if [ $rc -eq 0 ] && grep -q "already up to date" <<<"$out"; then ok "no new commits: already up to date"
else no "up to date: rc=$rc $out"; fi

# 3. local changes are never overwritten
echo "local edit" >> "$tmp/skills/drawio-diagrams/SKILL.md"
bump 1.2.0
out="$(bash "$tmp/skills/drawio-diagrams/scripts/update.sh" 2>&1)"; rc=$?
if [ $rc -eq 2 ] && grep -q "local edit" "$tmp/skills/drawio-diagrams/SKILL.md" && [ "$(cat "$tmp/skills/drawio-diagrams/VERSION")" = 1.1.0 ]; then
  ok "local changes: refused, nothing touched"; else no "local changes: rc=$rc $out"; fi
(cd "$tmp/skills/drawio-diagrams" && git checkout -q -- SKILL.md)

# 4. diverged history is refused
(cd "$tmp/skills/drawio-diagrams" && echo x > extra.txt && g add extra.txt && g commit -qm local)
out="$(bash "$tmp/skills/drawio-diagrams/scripts/update.sh" 2>&1)"; rc=$?
if [ $rc -eq 3 ] && [ -f "$tmp/skills/drawio-diagrams/extra.txt" ]; then ok "diverged copy: refused, local commit kept"
else no "diverged: rc=$rc $out"; fi

# 5. installed without git (unzipped): backed up outside the skills folder, replaced by a clone
mkdir -p "$tmp/zip"
(cd "$tmp/src" && g checkout -q HEAD~2 && tar cf - --exclude .git . ) | (mkdir -p "$tmp/zip/drawio-diagrams" && cd "$tmp/zip/drawio-diagrams" && tar xf -)
(cd "$tmp/src" && g checkout -q main)
echo "my note" > "$tmp/zip/drawio-diagrams/notes.txt"
out="$(bash "$tmp/zip/drawio-diagrams/scripts/update.sh" 2>&1)"; rc=$?
backup="$(ls -d "$tmp"/cache/drawio-diagrams/backup-* 2>/dev/null | head -1)"
if [ $rc -eq 0 ] && [ "$(cat "$tmp/zip/drawio-diagrams/VERSION")" = 1.2.0 ] && [ -d "$tmp/zip/drawio-diagrams/.git" ] \
   && [ -f "$backup/notes.txt" ] && [ ! -e "$tmp/zip/drawio-diagrams/notes.txt" ] && [ "$(ls "$tmp/zip")" = drawio-diagrams ]; then
  ok "zip install: backed up to the cache, replaced by a git clone of 1.2.0"; else no "zip install: rc=$rc $out"; fi

# 6. refuses to run on something that is not this skill
mkdir -p "$tmp/other/scripts" && cp scripts/update.sh "$tmp/other/scripts/" && echo keep > "$tmp/other/file.txt"
out="$(bash "$tmp/other/scripts/update.sh" 2>&1)"; rc=$?
if [ $rc -eq 1 ] && [ -f "$tmp/other/file.txt" ]; then ok "not the skill folder: refused, nothing deleted"
else no "foreign folder: rc=$rc $out"; fi

exit $fail

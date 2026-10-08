#!/usr/bin/env bash
# Build dist/drawio-diagrams.zip for claude.ai: tests run first, then only the skill
# itself (SKILL.md, references/, scripts/, examples/) goes into one top-level folder.
set -euo pipefail
cd "$(dirname "$0")"
name="$(sed -n 's/^name: *//p' SKILL.md | head -1)"
[ -n "$name" ] || { echo "no 'name:' in SKILL.md frontmatter" >&2; exit 1; }
tests/run.sh
stage="$(mktemp -d)"; trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/$name" dist
cp SKILL.md "$stage/$name/"
cp -R references scripts examples "$stage/$name/"
find "$stage" \( -name '__pycache__' -o -name '.DS_Store' -o -name '*.pyc' -o -name '*.drawio' -o -name '*.png' \) -exec rm -rf {} +
rm -f "dist/$name.zip"
(cd "$stage" && zip -r -X -q "$OLDPWD/dist/$name.zip" "$name")
unzip -l "dist/$name.zip"
echo "built dist/$name.zip"

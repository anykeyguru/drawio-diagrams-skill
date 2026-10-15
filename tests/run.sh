#!/usr/bin/env bash
# Regression tests for the drawio-diagrams skill.
#   1. checker verdicts on generated cases (ok-*, warn-*, err-*)
#   2. the worked example generator produces a diagram with ZERO findings,
#      language check included
#   3. review.py exports one PNG per tab (skipped when draw.io is not installed)
#   4. the self-update script (tests/test_update.sh)
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0
python3 tests/make_cases.py
echo "check_layout.py verdicts"
for f in tests/cases/*.drawio; do
  want="$(basename "$f" | cut -d- -f1)"
  out="$(python3 scripts/check_layout.py "$f")"; rc=$?
  errs=$(grep -c '  ERROR' <<<"$out"); warns=$(grep -c '  WARN' <<<"$out")
  if [ "$errs" -gt 0 ]; then got=err; elif [ "$warns" -gt 0 ]; then got=warn; else got=ok; fi
  [ "$got" = err ] && [ "$rc" -ne 1 ] && got="err(exit $rc)"
  if [ "$got" = "$want" ]; then printf '  ok    %-36s %s\n' "$(basename "$f")" "$got"
  else printf '  FAIL  %-36s expected %s, got %s\n%s\n' "$(basename "$f")" "$want" "$got" "$out"; fail=1; fi
done

echo "backups (Diagram.write)"
python3 tests/test_backups.py || fail=1

echo "worked example"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
python3 - "$tmp/architecture.drawio" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("example", "examples/build_architecture.py")
ex = importlib.util.module_from_spec(spec); spec.loader.exec_module(ex)
from drawio_kit import Diagram
Diagram([build() for _, build in ex.PAGES], lang=ex.LANG).write(sys.argv[1])
PY
out="$(python3 scripts/check_layout.py "$tmp/architecture.drawio")"
if grep -qE '  (ERROR|WARN)' <<<"$out"; then echo "  FAIL  example has findings"; echo "$out"; fail=1
else echo "  ok    examples/build_architecture.py: $(grep -c '^\[' <<<"$out") tabs, 0 findings"; fi

echo "review.py export"
if python3 -c "import sys; sys.path.insert(0,'scripts'); from drawio_kit import drawio_binary; sys.exit(0 if drawio_binary() else 1)"; then
  python3 scripts/review.py "$tmp/architecture.drawio" --out "$tmp/png" >/dev/null
  tabs=$(grep -c '<diagram ' "$tmp/architecture.drawio")
  n=$(ls "$tmp/png"/*.png 2>/dev/null | wc -l | tr -d ' ')
  if [ "$n" = "$tabs" ]; then echo "  ok    $tabs tabs exported to PNG"; else echo "  FAIL  expected $tabs PNGs, got $n"; fail=1; fi
else
  echo "  skip  draw.io CLI not installed"
fi

echo "self-update (scripts/update.sh)"
tests/test_update.sh || fail=1

echo "release metadata"
kit="$(python3 -c "import sys; sys.path.insert(0,'scripts'); import drawio_kit; print(drawio_kit.__version__)")"
if [ "$(cat VERSION)" = "$kit" ]; then echo "  ok    VERSION $kit = drawio_kit.__version__"
else echo "  FAIL  VERSION $(cat VERSION) != drawio_kit.__version__ $kit"; fail=1; fi
desc_len="$(python3 - <<'PY'
import re
fm = open("SKILL.md").read().split("---")[1]
m = re.search(r"description: >-\n((?:  .*\n)+)", fm)
print(len(" ".join(l.strip() for l in m.group(1).splitlines())) if m else -1)
PY
)"
if grep -q '^name: drawio-diagrams$' SKILL.md && [ "$desc_len" -gt 0 ] && [ "$desc_len" -le 1024 ]; then
  echo "  ok    SKILL.md frontmatter: name, description $desc_len/1024 chars"
else echo "  FAIL  SKILL.md frontmatter: name or description ($desc_len chars, max 1024)"; fail=1; fi

[ "$fail" -eq 0 ] && echo "all passed" || { echo "FAILED"; exit 1; }

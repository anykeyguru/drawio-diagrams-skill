#!/usr/bin/env python3
"""One-step review of a .drawio file: geometry check + PNG export of every tab.

    review.py docs/architecture.drawio [--out DIR]

1. Runs check_layout.py on the file (errors -> exit 1, warnings listed).
2. Exports every tab to DIR (default: next to the file, architecture-<N>-<slug>.png)
   with the draw.io desktop CLI.
3. Prints the PNG paths and the visual checklist: open EVERY image and go through it.
   The geometry checker proves lines avoid boxes; only looking proves the picture
   tells the story and reads well.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from drawio_kit import drawio_binary, export_png  # noqa: E402
from check_layout import load_pages  # noqa: E402

CHECKLIST = """\
Visual checklist (open each PNG and confirm every line):
  [ ] every line can be followed from start to arrowhead without guessing
  [ ] no line, badge or arrowhead sits on text, a box edge or a zone title
  [ ] no two lines run side by side closer than ~10 px or merge
  [ ] badges are next to their own line, not between two lines, not on a box border
  [ ] all text is fully visible: nothing clipped, nothing spilling out of a box
  [ ] corners look square-ish (6 px), zones read as zones, colours mean one thing
  [ ] the legend explains every badge number and nothing else
  [ ] the main flow reads left -> right or top -> bottom without backtracking
  [ ] the tab title answers one question, and the picture answers exactly that
"""


def slug(name: str) -> str:
    s = re.sub(r"^\s*\d+[.)]\s*", "", name).lower()
    s = re.sub(r"[^\w]+", "-", s, flags=re.UNICODE).strip("-")
    return s or "page"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--out", help="directory for PNGs (default: next to the .drawio)")
    args = ap.parse_args()
    src = pathlib.Path(args.file).resolve()
    out = pathlib.Path(args.out).resolve() if args.out else src.parent
    out.mkdir(parents=True, exist_ok=True)

    print("== geometry check ==", flush=True)
    rc = subprocess.run([sys.executable, str(HERE / "check_layout.py"), str(src)]).returncode

    print("\n== export ==")
    if not drawio_binary():
        print("draw.io desktop CLI not found: install draw.io (https://www.drawio.com) to export and look.")
        sys.exit(rc or 2)
    pngs = []
    for n, (name, _) in enumerate(load_pages(str(src)), 1):
        png = out / f"{src.stem}-{n}-{slug(name)}.png"
        if export_png(src, n, png):
            pngs.append(png)
            print(f"  {png}")
        else:
            print(f"  export failed for tab {n} ({name})")
    print("\n== look ==")
    print(CHECKLIST)
    sys.exit(rc)


if __name__ == "__main__":
    main()

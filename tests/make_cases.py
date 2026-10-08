#!/usr/bin/env python3
"""Builds tests/cases/*.drawio. The name prefix is the expected checker verdict:
ok-* (no findings), warn-* (warnings only), err-* (at least one error)."""
import base64
import pathlib
import sys
import urllib.parse
import zlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from drawio_kit import Diagram, Page, Z  # noqa: E402

OUT = HERE / "cases"
OUT.mkdir(exist_ok=True)
for old in OUT.glob("*.drawio"):
    old.unlink()


def save(name, page):
    Diagram([page]).write(OUT / f"{name}.drawio")


def two_boxes(p):
    a = p.box(100, 200, 200, 80, "A\nleft", Z.APP)
    b = p.box(500, 200, 200, 80, "B\nright", Z.APP)
    return a, b


# ---- ok ---------------------------------------------------------------------
p = Page("ok"); p.title("Clean: one straight edge with explicit ports and a legend")
a, b = two_boxes(p)
p.edge(a, b, "1", exit=(1, .5), entry=(0, .5))
p.legend(100, 400, 600, 60, "Связи", ["1  A → B: call"])
save("ok-clean", p)

p = Page("ok"); p.title("Clean: edge routed around an obstacle through a corridor")
a = p.box(100, 200, 200, 80, "A\nleft", Z.APP)
p.box(400, 180, 120, 120, "Obstacle\nin the middle", Z.NEUTRAL)
c = p.box(620, 200, 200, 80, "C\nright", Z.APP)
p.edge(a, c, "1", exit=(.5, 0), entry=(.5, 0), points=[(200, 140), (720, 140)])
save("ok-detour-via-corridor", p)

p = Page("ok"); p.title("Clean: zone with a short title and boxes inside")
p.zone(60, 80, 700, 300, "Кластер", Z.APP)
a = p.box(100, 160, 200, 80, "A\ninside", Z.APP)
b = p.box(500, 160, 200, 80, "B\ninside", Z.APP)
p.edge(a, b, "1", exit=(1, .5), entry=(0, .5))
save("ok-zone", p)

# compressed file, as the draw.io app may save it
clean = (OUT / "ok-clean.drawio").read_text()
start = clean.index("<mxGraphModel"); end = clean.index("</mxGraphModel>") + len("</mxGraphModel>")
model = clean[start:end]
co = zlib.compressobj(9, zlib.DEFLATED, -15)
packed = base64.b64encode(co.compress(urllib.parse.quote(model).encode()) + co.flush()).decode()
(OUT / "ok-compressed.drawio").write_text(f'<mxfile><diagram name="ok" id="ok">{packed}</diagram></mxfile>\n')

# ---- errors -----------------------------------------------------------------
p = Page("err"); p.title("Edge runs straight through another box")
a = p.box(100, 200, 200, 80, "A\nleft", Z.APP)
p.box(400, 180, 120, 120, "Obstacle\nin the middle", Z.NEUTRAL)
c = p.box(620, 200, 200, 80, "C\nright", Z.APP)
p.edge(a, c, "1", exit=(1, .5), entry=(0, .5))
save("err-edge-through-box", p)

p = Page("err"); p.title("Two independent edges share one horizontal run")
a = p.box(100, 100, 160, 60, "A\nsource", Z.APP); b = p.box(100, 400, 160, 60, "B\nsource", Z.APP)
c = p.box(700, 100, 160, 60, "C\ntarget", Z.APP); d = p.box(700, 400, 160, 60, "D\ntarget", Z.APP)
p.edge(a, c, "1", exit=(1, .5), entry=(0, .5), points=[(400, 130), (400, 280), (600, 280), (600, 130)])
p.edge(b, d, "2", exit=(1, .5), entry=(0, .5), points=[(420, 430), (420, 280), (580, 280), (580, 430)])
save("err-collinear-overlap", p)

p = Page("err"); p.title("Relative corner radius (pill shape on large boxes)")
p._vertex(100, 200, 400, 200, "Big box", "rounded=1;arcSize=20;whiteSpace=wrap;html=1;")
save("err-relative-arc", p)

p = Page("err"); p.title("Absolute corner radius too large")
p._vertex(100, 200, 400, 200, "Big box", "rounded=1;absoluteArcSize=1;arcSize=24;whiteSpace=wrap;html=1;")
save("err-large-arc", p)

p = Page("err"); p.title("Two boxes overlap")
p.box(100, 200, 250, 100, "A\nfirst", Z.APP)
p.box(300, 250, 250, 100, "B\nsecond", Z.APP)
save("err-boxes-overlap", p)

p = Page("err"); p.title("Edge enters a zone through its title")
p.zone(60, 200, 900, 300, "Кластер, namespace with a rather long title", Z.APP)
a = p.box(200, 60, 160, 60, "Outside\nclient", Z.NEUTRAL)
b = p.box(200, 300, 160, 80, "Inside\nservice", Z.APP)
p.edge(a, b, "1", exit=(.5, 1), entry=(.5, 0))
save("err-edge-through-zone-title", p)

# ---- warnings ---------------------------------------------------------------
p = Page("warn"); p.title("Two edges cross once (horizontal through vertical)")
a = p.box(100, 270, 160, 60, "A\nleft", Z.APP); c = p.box(700, 270, 160, 60, "C\nright", Z.APP)
b = p.box(400, 60, 160, 60, "B\ntop", Z.APP); d = p.box(400, 500, 160, 60, "D\nbottom", Z.APP)
p.edge(a, c, "1", exit=(1, .5), entry=(0, .5))
p.edge(b, d, "2", exit=(.5, 1), entry=(.5, 0))
save("warn-crossing", p)

p = Page("warn"); p.title("Text label on an edge")
a, b = two_boxes(p)
eid = p.edge(a, b, "", exit=(1, .5), entry=(0, .5))
p.cells[-1] = p.cells[-1].replace('value=""', 'value="POST /api/v1/login with credentials"')
save("warn-edge-label", p)

p = Page("warn"); p.title("Text does not fit its box")
p.box(100, 200, 160, 40, "A box\nwith far too many words for its tiny size\nand another long line\nand one more", Z.APP)
save("warn-text-overflow", p)

p = Page("warn"); p.title("Edge without explicit ports")
a, b = two_boxes(p)
p.edge(a, b, "1")
save("warn-no-ports", p)

p = Page("warn"); p.title("Edge squeezes past a box")
a = p.box(100, 200, 200, 80, "A\nleft", Z.APP)
p.box(400, 244, 120, 80, "Neighbour\nbelow the line", Z.NEUTRAL)
c = p.box(620, 200, 200, 80, "C\nright", Z.APP)
p.edge(a, c, "1", exit=(1, .5), entry=(0, .5))
save("warn-tight-corridor", p)

print(f"{len(list(OUT.glob('*.drawio')))} cases in {OUT}")

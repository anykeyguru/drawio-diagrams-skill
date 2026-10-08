#!/usr/bin/env python3
"""Layout checker for draw.io files in the house style.

Checks every page of a .drawio file (plain or compressed) by geometry:

  ERROR  edge runs through a box or a note that is not its own source/target
  ERROR  two edges run on top of each other (collinear overlap)
  ERROR  two boxes / notes overlap (containers excluded)
  ERROR  rounded corners not absolute 4..8 px (large radius looks unserious)
  ERROR  edge runs through a container's title
  WARN   two edges cross (drawn with a jump, but better re-routed)
  WARN   edge passes closer than CLEARANCE px to a box (tight corridor)
  WARN   text probably does not fit its box (estimated)
  WARN   text label on an edge (use a numbered badge + legend instead)
  WARN   edge without explicit exit/entry: route is drawio's guess, verify visually

Edge routes are reconstructed the way orthogonalEdgeStyle draws them: leave the
source perpendicular to the exit side, pass the waypoints, enter the target
perpendicular to the entry side. Routes without waypoints get the standard elbow.

Usage: check_layout.py file.drawio [--page N]   exit code 1 if any ERROR
"""
from __future__ import annotations

import argparse
import base64
import html
import math
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass, field

CLEARANCE = 6       # px a line should keep from a box it does not touch
ARC_MIN, ARC_MAX = 4, 8
TITLE_BAND = 26     # px: height of a container title strip


@dataclass
class Box:
    id: str
    x: float
    y: float
    w: float
    h: float
    style: dict
    value: str
    kind: str = "box"          # box | note | container | badge | title
    title_w: float = 0

    @property
    def x2(self): return self.x + self.w

    @property
    def y2(self): return self.y + self.h

    def inflate(self, d):
        return (self.x - d, self.y - d, self.x2 + d, self.y2 + d)

    def label(self):
        t = re.sub(r"<[^>]+>", " ", html.unescape(self.value or "")).strip()
        return (t[:40] + "…") if len(t) > 40 else t or self.id


@dataclass
class Edge:
    id: str
    src: str
    dst: str
    style: dict
    value: str
    points: list = field(default_factory=list)
    path: list = field(default_factory=list)
    badge: str = ""


def parse_style(s: str) -> dict:
    out = {}
    for part in (s or "").split(";"):
        if not part:
            continue
        k, _, v = part.partition("=")
        out[k] = v if _ else True
    return out


def load_pages(path: str):
    root = ET.parse(path).getroot()
    if root.tag == "mxGraphModel":
        yield "page 1", root
        return
    for d in root.iter("diagram"):
        model = d.find("mxGraphModel")
        if model is None:
            raw = (d.text or "").strip()
            data = zlib.decompress(base64.b64decode(raw), -15).decode()
            model = ET.fromstring(urllib.parse.unquote(data))
        yield d.get("name") or "page", model


def text_lines(value: str) -> list[str]:
    v = html.unescape(value or "")
    v = re.sub(r"<br\s*/?>", "\n", v, flags=re.I)
    v = re.sub(r"</(div|p)>", "\n", v, flags=re.I)
    v = re.sub(r"<[^>]+>", "", v)
    return [ln for ln in v.split("\n")]


def collect(model):
    cells = {c.get("id"): c for c in model.iter("mxCell")}
    boxes, edges = {}, []
    for c in cells.values():
        st = parse_style(c.get("style"))
        g = c.find("mxGeometry")
        if c.get("vertex") == "1" and g is not None:
            parent = cells.get(c.get("parent"))
            if parent is not None and parent.get("edge") == "1":
                continue  # badge on an edge
            if g.get("relative") == "1":
                continue
            b = Box(c.get("id"), float(g.get("x", 0)), float(g.get("y", 0)), float(g.get("width", 0)),
                    float(g.get("height", 0)), st, c.get("value") or "")
            if "text" in st:
                b.kind = "note"
            boxes[b.id] = b
        elif c.get("edge") == "1":
            pts = []
            if g is not None:
                arr = g.find("Array")
                if arr is not None:
                    pts = [(float(p.get("x", 0)), float(p.get("y", 0))) for p in arr.findall("mxPoint")]
            edges.append(Edge(c.get("id"), c.get("source"), c.get("target"), st, c.get("value") or "", pts))
    # badges
    for c in cells.values():
        parent = cells.get(c.get("parent"))
        if c.get("vertex") == "1" and parent is not None and parent.get("edge") == "1":
            for e in edges:
                if e.id == parent.get("id"):
                    e.badge = re.sub(r"<[^>]+>", "", c.get("value") or "")
    # containers: boxes that fully contain another non-note box
    for b in boxes.values():
        if b.kind != "box":
            continue
        for o in boxes.values():
            if o is b or o.kind == "note" and o.w > 1000:
                continue
            if o.x >= b.x and o.y >= b.y and o.x2 <= b.x2 and o.y2 <= b.y2 and (o.w * o.h) < (b.w * b.h):
                b.kind = "container"
                first = text_lines(b.value)[0] if b.value else ""
                b.title_w = min(b.w - 10, 14 + len(first) * float(b.style.get("fontSize", 13)) * 0.62)
                break
    # page title: wide text at the very top
    for b in boxes.values():
        if b.kind == "note" and b.y < 50 and b.h <= 40:
            b.kind = "title"
    return boxes, edges


def port(b: Box, fx, fy):
    return (b.x + b.w * fx, b.y + b.h * fy)


def side(fx, fy):
    if fx <= 0.001: return "L"
    if fx >= 0.999: return "R"
    if fy <= 0.001: return "T"
    if fy >= 0.999: return "B"
    return "?"


def default_ports(s: Box, t: Box):
    """drawio's choice when exit/entry are not given: facing sides of the boxes."""
    scx, scy, tcx, tcy = s.x + s.w / 2, s.y + s.h / 2, t.x + t.w / 2, t.y + t.h / 2
    dx, dy = tcx - scx, tcy - scy
    if abs(dx) >= abs(dy):
        return ((1, .5), (0, .5)) if dx > 0 else ((0, .5), (1, .5))
    return ((.5, 1), (.5, 0)) if dy > 0 else ((.5, 0), (.5, 1))


def route(e: Edge, boxes) -> list:
    s, t = boxes.get(e.src), boxes.get(e.dst)
    if s is None or t is None:
        return []
    dflt = default_ports(s, t)
    ex = (float(e.style["exitX"]), float(e.style["exitY"])) if "exitX" in e.style else dflt[0]
    en = (float(e.style["entryX"]), float(e.style["entryY"])) if "entryX" in e.style else dflt[1]
    a, b = port(s, *ex), port(t, *en)
    sa, sb = side(*ex), side(*en)
    pts = [a]
    if e.points:
        first = e.points[0]
        if a[0] != first[0] and a[1] != first[1]:
            pts.append((first[0], a[1]) if sa in "LR" else (a[0], first[1]))
        for p in e.points:
            q = pts[-1]
            if q[0] != p[0] and q[1] != p[1]:
                pts.append((p[0], q[1]))
            pts.append(p)
        last = pts[-1]
        if last[0] != b[0] and last[1] != b[1]:
            pts.append((last[0], b[1]) if sb in "LR" else (b[0], last[1]))
    else:
        if a[0] != b[0] and a[1] != b[1]:
            if sa in "LR" and sb in "LR":
                mx = (a[0] + b[0]) / 2
                pts += [(mx, a[1]), (mx, b[1])]
            elif sa in "TB" and sb in "TB":
                my = (a[1] + b[1]) / 2
                pts += [(a[0], my), (b[0], my)]
            elif sa in "LR":
                pts.append((b[0], a[1]))
            else:
                pts.append((a[0], b[1]))
    pts.append(b)
    out = []
    for p in pts:
        if not out or (abs(out[-1][0] - p[0]) > .01 or abs(out[-1][1] - p[1]) > .01):
            out.append(p)
    return out


def seg_hits_rect(p, q, r) -> bool:
    """Axis-aligned segment p-q intersects the open rectangle r=(x1,y1,x2,y2)."""
    x1, y1, x2, y2 = r
    if abs(p[1] - q[1]) < .01:  # horizontal
        y = p[1]
        lo, hi = sorted((p[0], q[0]))
        return y1 < y < y2 and lo < x2 and hi > x1
    if abs(p[0] - q[0]) < .01:  # vertical
        x = p[0]
        lo, hi = sorted((p[1], q[1]))
        return x1 < x < x2 and lo < y2 and hi > y1
    # diagonal (should not happen with orthogonal edges): sample
    for k in range(21):
        t = k / 20
        x, y = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
        if x1 < x < x2 and y1 < y < y2:
            return True
    return False


def segments(path):
    return list(zip(path, path[1:]))


def overlap_len(a, b):
    (p1, q1), (p2, q2) = a, b
    if abs(p1[1] - q1[1]) < .01 and abs(p2[1] - q2[1]) < .01 and abs(p1[1] - p2[1]) < 3:
        lo = max(min(p1[0], q1[0]), min(p2[0], q2[0])); hi = min(max(p1[0], q1[0]), max(p2[0], q2[0]))
        return hi - lo
    if abs(p1[0] - q1[0]) < .01 and abs(p2[0] - q2[0]) < .01 and abs(p1[0] - p2[0]) < 3:
        lo = max(min(p1[1], q1[1]), min(p2[1], q2[1])); hi = min(max(p1[1], q1[1]), max(p2[1], q2[1]))
        return hi - lo
    return 0


def crosses(a, b):
    (p1, q1), (p2, q2) = a, b
    h1, h2 = abs(p1[1] - q1[1]) < .01, abs(p2[1] - q2[1]) < .01
    if h1 == h2:
        return False
    hs, vs = (a, b) if h1 else (b, a)
    (hp, hq), (vp, vq) = hs, vs
    x, y = vp[0], hp[1]
    return (min(hp[0], hq[0]) + 1 < x < max(hp[0], hq[0]) - 1) and (min(vp[1], vq[1]) + 1 < y < max(vp[1], vq[1]) - 1)


def estimate_overflow(b: Box) -> bool:
    if b.kind not in ("box",) or b.w <= 0:
        return False
    size = float(b.style.get("fontSize", 12))
    char_w = size * 0.56
    usable = max(b.w - 18, 10)
    lines = 0
    for ln in text_lines(b.value):
        lines += max(1, math.ceil(len(ln) * char_w / usable))
    need = lines * size * 1.2 + 8
    return need > b.h + 2


def check_page(name, model):
    errors, warns = [], []
    boxes, edges = collect(model)
    lbl = lambda e: f"edge {e.badge or e.id}"

    # corners
    for b in boxes.values():
        if b.style.get("rounded") in ("1", True) and "ellipse" not in b.style:
            if b.style.get("absoluteArcSize") != "1":
                errors.append(f"'{b.label()}': rounded corner is relative (pill-shaped on big boxes); use absoluteArcSize=1;arcSize=6")
            else:
                arc = float(b.style.get("arcSize", 0))
                if not ARC_MIN <= arc <= ARC_MAX:
                    errors.append(f"'{b.label()}': corner radius {arc:g} px, keep {ARC_MIN}..{ARC_MAX}")

    # overlapping boxes / notes
    solid = [b for b in boxes.values() if b.kind in ("box", "note")]
    for i, a in enumerate(solid):
        for b in solid[i + 1:]:
            if a.x < b.x2 - 1 and b.x < a.x2 - 1 and a.y < b.y2 - 1 and b.y < a.y2 - 1:
                errors.append(f"'{a.label()}' overlaps '{b.label()}'")

    # text fit
    for b in boxes.values():
        if estimate_overflow(b):
            warns.append(f"'{b.label()}': text probably does not fit (widen or heighten the box, or shorten text)")

    # edges
    for e in edges:
        e.path = route(e, boxes)
        if (e.value or "").strip() and len(re.sub(r"<[^>]+>", "", html.unescape(e.value)).strip()) > 3:
            warns.append(f"{lbl(e)}: text label on the edge; use a numbered badge and explain it in the legend")
        if "exitX" not in e.style or "entryX" not in e.style:
            warns.append(f"{lbl(e)}: no explicit exit/entry, the route is drawio's guess; verify visually")
        for p, q in segments(e.path):
            for b in boxes.values():
                if b.id in (e.src, e.dst) or b.kind in ("badge",):
                    continue
                if b.kind == "container":
                    band = (b.x + 4, b.y, b.x + b.title_w, b.y + TITLE_BAND)
                    if seg_hits_rect(p, q, band):
                        errors.append(f"{lbl(e)} runs through the title of '{b.label()}'")
                    continue
                if b.kind == "title":
                    tw = len(text_lines(b.value)[0]) * 14 * 0.6
                    if seg_hits_rect(p, q, (b.x, b.y, b.x + tw, b.y2)):
                        errors.append(f"{lbl(e)} runs through the page title")
                    continue
                if seg_hits_rect(p, q, b.inflate(-1)):
                    errors.append(f"{lbl(e)} runs through '{b.label()}'")
                elif seg_hits_rect(p, q, b.inflate(CLEARANCE)):
                    warns.append(f"{lbl(e)} passes within {CLEARANCE}px of '{b.label()}' (tight corridor)")
    # edge vs edge
    for i, a in enumerate(edges):
        for b in edges[i + 1:]:
            shared = {a.src, a.dst} & {b.src, b.dst}
            for sa in segments(a.path):
                for sb in segments(b.path):
                    ol = overlap_len(sa, sb)
                    if ol > 8 and not shared:
                        errors.append(f"{lbl(a)} and {lbl(b)} run on top of each other for {ol:.0f}px")
                    elif ol > 8 and shared:
                        warns.append(f"{lbl(a)} and {lbl(b)} share a {ol:.0f}px run near a common box; separate the ports")
                    elif crosses(sa, sb):
                        warns.append(f"{lbl(a)} crosses {lbl(b)} (jump arc); re-route through a free corridor if possible")
    return sorted(set(errors)), sorted(set(warns))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file")
    ap.add_argument("--page", type=int, help="check only this tab (1-based)")
    args = ap.parse_args()
    total_err = 0
    for n, (name, model) in enumerate(load_pages(args.file), 1):
        if args.page and n != args.page:
            continue
        errors, warns = check_page(name, model)
        total_err += len(errors)
        print(f"[{n}] {name}: {len(errors)} error(s), {len(warns)} warning(s)")
        for m in errors:
            print(f"  ERROR  {m}")
        for m in warns:
            print(f"  WARN   {m}")
    sys.exit(1 if total_err else 0)


if __name__ == "__main__":
    main()

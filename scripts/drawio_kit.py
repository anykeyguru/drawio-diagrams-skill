#!/usr/bin/env python3
"""House-style draw.io builder.

Diagrams are generated from a small Python script (docs/build_<name>.py) instead of
being dragged by hand, so layout rules are applied the same way every time and a
diagram can be rebuilt after a change in seconds. The .drawio file stays fully
editable in the draw.io app.

House rules this module bakes in (see references/style-guide.md):
  * corners: absolute arc of 6 px on every rectangle, containers included;
  * zones are pastel containers with a bold top-left title;
  * edges are orthogonal, square-cornered, 1.5 px, with NO text on them: each edge
    carries a numbered badge and the numbers are explained in a legend box;
  * edge routes are given explicitly (waypoints) through empty corridors, so a line
    never crosses a box, a note or another line's run.

Typical use (copy this file next to the generator, e.g. docs/drawio_kit.py):

    from drawio_kit import Diagram, Page, Z
    p = Page("1. Вход пользователя")
    p.title("Вход в сервис: ...")
    p.zone(40, 60, 300, 780, "Вне кластера", Z.OUTSIDE)
    a = p.box(70, 120, 220, 80, "Браузер\\nштатная форма", Z.NEUTRAL)
    ...
    p.edge(a, b, "1", exit=(1, .5), entry=(0, .5))
    p.legend(380, 700, 570, 140, "Шаги", ["1  браузер → nginx: ...", ...])
    Diagram([p]).write("docs/architecture.drawio")
    # then: python3 <skill>/scripts/check_layout.py docs/architecture.drawio
"""
from __future__ import annotations

import html
import pathlib
import shutil
import subprocess
from dataclasses import dataclass

__version__ = "1.0.0"

# 6 px absolute corner radius. Relative arcSize scales with box size and produces
# the "pill" look on large containers; absoluteArcSize keeps every corner equal.
ARC = "rounded=1;absoluteArcSize=1;arcSize=6;"


@dataclass(frozen=True)
class Zone:
    """Container fill/stroke, the stroke for boxes inside it, and the edge colour."""
    fill: str
    stroke: str
    box: str
    box_fill: str = "#ffffff"
    dashed: bool = False


class Z:
    """Zone palette. One meaning per colour across all diagrams."""
    APP = Zone("#e8f5e9", "#66bb6a", "#2e7d32")                 # our cluster / application
    IDP = Zone("#ede7f6", "#7e57c2", "#5e35b1")                 # identity: Keycloak, AD groups
    OUTSIDE = Zone("#fff3e0", "#ffa726", "#ef6c00", dashed=True)  # outside our perimeter
    DATA = Zone("#e3f2fd", "#42a5f5", "#1565c0")                # data stores, observability
    CI = Zone("#fce4ec", "#ec407a", "#ad1457")                  # GitLab, CI, source control
    SECRET = Zone("#fff8e1", "#f9a825", "#f9a825", "#fff8e1")   # secrets, credentials
    DENY = Zone("#ffebee", "#c62828", "#c62828", "#ffebee")     # blocked paths, 404/403
    NEUTRAL = Zone("#f5f5f5", "#999999", "#666666", "#f5f5f5")  # people, browsers, generic
    LEGEND = Zone("#fafafa", "#666666", "#666666", "#fafafa")


def _html(text: str) -> str:
    """Plain text -> draw.io html label: escaped, newlines as <br>, and runs of
    spaces kept (html would collapse "8  item   9  item" into single spaces)."""
    out = html.escape(text).replace("\n", "<br>")
    while "  " in out:
        out = out.replace("  ", "&nbsp; ")
    return out


class Page:
    """One tab of a .drawio file. Coordinates are absolute, page 1400 px wide."""

    def __init__(self, name: str, width: int = 1400, height: int = 900):
        self.name, self.width, self.height = name, width, height
        self.cells: list[str] = []
        self._n = 1

    # -- primitives ---------------------------------------------------------
    def _id(self) -> str:
        self._n += 1
        return f"c{self._n}"

    def _vertex(self, x, y, w, h, value, style, parent="1") -> str:
        i = self._id()
        self.cells.append(
            f'<mxCell id="{i}" value="{html.escape(value, quote=True)}" style="{style}" vertex="1" '
            f'parent="{parent}"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return i

    # -- building blocks ----------------------------------------------------
    def title(self, text: str, x: int = 40, y: int = 15) -> str:
        """Page heading: one line, bold, what the diagram answers."""
        return self._vertex(x, y, self.width - 2 * x, 30, text, "text;html=1;align=left;fontSize=14;fontStyle=1;")

    def zone(self, x, y, w, h, title: str, z: Zone) -> str:
        """Pastel container with a bold title in the top-left corner."""
        st = (ARC + f"whiteSpace=wrap;html=1;fillColor={z.fill};strokeColor={z.stroke};verticalAlign=top;"
              "fontSize=13;fontStyle=1;align=left;spacingLeft=10;spacingTop=4;" + ("dashed=1;" if z.dashed else ""))
        return self._vertex(x, y, w, h, title, st)

    def box(self, x, y, w, h, text: str, z: Zone = Z.NEUTRAL, size: int = 12, fill: str | None = None) -> str:
        """Component box. First line is the bold name, the rest is plain detail."""
        first, _, rest = text.partition("\n")
        value = f"<b>{_html(first)}</b>" + (f"<br>{_html(rest)}" if rest else "")
        st = (ARC + f"whiteSpace=wrap;html=1;fillColor={fill or z.box_fill};strokeColor={z.box};align=left;"
              f"spacingLeft=8;spacingRight=8;fontSize={size};verticalAlign=middle;")
        return self._vertex(x, y, w, h, value, st)

    def note(self, x, y, w, h, text: str, size: int = 11, color: str = "#555555") -> str:
        """Free text without a frame: rationale, constraints. Keep away from edges."""
        return self._vertex(x, y, w, h, _html(text),
                            f"text;html=1;align=left;verticalAlign=top;fontSize={size};fontColor={color};whiteSpace=wrap;spacing=2;")

    def legend(self, x, y, w, h, title: str, items: list[str], size: int = 11) -> str:
        """Box that explains the numbered badges: one item per line."""
        return self.box(x, y, w, h, title + "\n" + "\n".join(items), Z.LEGEND, size=size)

    def edge(self, src: str, dst: str, num: str = "", *, exit=None, entry=None, points=(),
             color: str = "#444444", dashed: bool = False) -> str:
        """Orthogonal edge with a numbered badge instead of a text label.

        exit/entry: (fx, fy) on the source/target box, 0..1, e.g. (1, .5) = middle of
        the right side. points: explicit waypoints [(x, y), ...] that keep the route in
        an empty corridor. Give both whenever the straight route would touch anything.
        """
        st = (f"edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor={color};strokeWidth=1.5;"
              "endArrow=blockThin;endFill=1;jumpStyle=arc;jumpSize=8;")
        if dashed:
            st += "dashed=1;dashPattern=6 4;"
        if exit:
            st += f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
        if entry:
            st += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
        i = self._id()
        pts = "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in points)
        geo = '<mxGeometry relative="1" as="geometry">' + (f'<Array as="points">{pts}</Array>' if pts else "") + "</mxGeometry>"
        self.cells.append(f'<mxCell id="{i}" value="" style="{st}" edge="1" parent="1" source="{src}" target="{dst}">{geo}</mxCell>')
        if num:
            j = self._id()
            bst = (f"ellipse;whiteSpace=wrap;html=1;fillColor={color};strokeColor=none;fontColor=#ffffff;"
                   "fontSize=11;fontStyle=1;align=center;verticalAlign=middle;resizable=0;")
            self.cells.append(
                f'<mxCell id="{j}" value="{html.escape(num)}" style="{bst}" vertex="1" connectable="0" parent="{i}">'
                '<mxGeometry x="0" y="0" width="20" height="20" relative="1" as="geometry">'
                '<mxPoint x="-10" y="-10" as="offset"/></mxGeometry></mxCell>')
        return i

    def xml(self) -> str:
        return (f'<diagram name="{html.escape(self.name, quote=True)}" id="{html.escape(self.name.replace(" ", "_"), quote=True)}">\n'
                f'<mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
                f'fold="1" page="1" pageScale="1" pageWidth="{self.width}" pageHeight="{self.height}" math="0" shadow="0">\n'
                '<root><mxCell id="0"/><mxCell id="1" parent="0"/>\n' + "\n".join(self.cells) + "\n</root></mxGraphModel></diagram>")


class Diagram:
    """A .drawio file: one tab per concern."""

    def __init__(self, pages: list[Page]):
        self.pages = pages

    def write(self, path: str | pathlib.Path) -> pathlib.Path:
        path = pathlib.Path(path)
        body = "\n".join(p.xml() for p in self.pages)
        path.write_text(f'<mxfile host="Electron" agent="drawio_kit {__version__}" version="24.0.0" type="device">\n{body}\n</mxfile>\n')
        return path


def drawio_binary() -> str | None:
    """draw.io desktop CLI: macOS app bundle, or `drawio` / `draw.io` on PATH."""
    mac = "/Applications/draw.io.app/Contents/MacOS/draw.io"
    if pathlib.Path(mac).exists():
        return mac
    return shutil.which("drawio") or shutil.which("draw.io")


def export_png(drawio: str | pathlib.Path, page: int, out: str | pathlib.Path, scale: float = 1.5) -> bool:
    """Export one tab (1-based) to PNG. Returns False when the CLI is not installed."""
    binary = drawio_binary()
    if not binary:
        return False
    subprocess.run([binary, "-x", "-f", "png", "-s", str(scale), "-b", "20", "-p", str(page), "-o", str(out), str(drawio)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return pathlib.Path(out).exists()

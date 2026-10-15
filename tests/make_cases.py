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
from drawio_kit import Diagram, Page, Z, terms  # noqa: E402

OUT = HERE / "cases"
OUT.mkdir(exist_ok=True)
for old in OUT.glob("*.drawio"):
    old.unlink()


def save(name, page, lang=None):
    Diagram([page], lang=lang).write(OUT / f"{name}.drawio", backup=False)


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

# ---- language: every label in the language of the conversation ---------------

def lang_page(lang, name, title, boxes, legend, label=""):
    T = terms(lang)
    p = Page(name); p.title(title)
    a = p.box(100, 200, 260, 80, boxes[0], Z.APP)
    b = p.box(560, 200, 260, 80, boxes[1], Z.APP)
    if label:
        p.edge(a, b, label=label, exit=(1, .5), entry=(0, .5))
    else:
        p.edge(a, b, "1", exit=(1, .5), entry=(0, .5))
    p.legend(100, 400, 660, 60, T["links"], [legend])
    return p


save("ok-lang-ru", lang_page("ru", "1. Вызов модели", "Как приложение вызывает модель через LiteLLM",
     ["Приложение\nOpenAI SDK, ключ sk-…", "LiteLLM :4000\nпроверяет ключ, team и бюджет"],
     "1  приложение → LiteLLM: POST /v1/chat/completions"), "ru")
save("ok-lang-en", lang_page("en", "1. Model call", "How an application calls the model through LiteLLM",
     ["Application\nOpenAI SDK, key sk-…", "LiteLLM :4000\nchecks the key, team and budget"],
     "1  application → LiteLLM: POST /v1/chat/completions"), "en")
save("ok-lang-uz", lang_page("uz", "1. Model chaqiruvi", "Ilova modelni LiteLLM orqali qanday chaqiradi",
     ["Ilova\nOpenAI SDK, kalit sk-…", "LiteLLM :4000\nkalit, team va byudjetni tekshiradi"],
     "1  ilova → LiteLLM: POST /v1/chat/completions"), "uz")
save("warn-lang-en-has-russian", lang_page("en", "1. Model call", "How an application calls the model through LiteLLM",
     ["Application\nOpenAI SDK, key sk-…", "LiteLLM :4000\nпроверяет ключ и бюджет"],
     "1  application → LiteLLM: POST /v1/chat/completions"), "en")
save("warn-lang-ru-has-english", lang_page("ru", "1. Вызов модели", "Как приложение вызывает модель через LiteLLM",
     ["Приложение\nOpenAI SDK, ключ sk-…", "LiteLLM :4000\nchecks the key and the budget"],
     "1  приложение → LiteLLM: POST /v1/chat/completions"), "ru")
save("warn-lang-tab-name", lang_page("en", "1. Вызов модели", "How an application calls the model through LiteLLM",
     ["Application\nOpenAI SDK, key sk-…", "LiteLLM :4000\nchecks the key, team and budget"],
     "1  application → LiteLLM: POST /v1/chat/completions"), "en")

# ---- principal diagram: short labels on the lines ------------------------------
p = Page("ok"); p.title("Principal: labelled lines, labels on straight runs")
a = p.box(100, 120, 200, 80, "App\nclient", Z.APP)
b = p.box(560, 120, 200, 80, "API\nservice", Z.APP)
c = p.box(560, 360, 200, 80, "DB\nstorage", Z.DATA)
p.edge(a, b, label="HTTPS :443", exit=(1, .5), entry=(0, .5))
p.edge(b, c, label="SQL", exit=(.5, 1), entry=(.5, 0), color=Z.DATA.box)
p.edge(a, c, label="read-only\nreplica", label_at=.3, exit=(.5, 1), entry=(0, .5), points=[(200, 400)])
save("ok-principal-labels", p, "en")

p = Page("err"); p.title("Line label lands on a box")
a = p.box(100, 200, 200, 80, "A\nleft", Z.APP)
p.box(380, 150, 100, 60, "Small\nbox", Z.NEUTRAL)
b = p.box(560, 200, 200, 80, "B\nright", Z.APP)
p.edge(a, b, label="a rather long label", exit=(1, .2), entry=(0, .2))
save("err-label-covers-box", p)

p = Page("err"); p.title("Another line runs through a label")
a, b = two_boxes(p)
c = p.box(370, 80, 60, 40, "C", Z.APP); d = p.box(370, 380, 60, 40, "D", Z.APP)
p.edge(a, b, label="HTTPS", exit=(1, .5), entry=(0, .5))
p.edge(c, d, exit=(.5, 1), entry=(.5, 0), dashed=True)
save("err-line-through-label", p)

p = Page("err"); p.title("Two labels overlap")
a = p.box(100, 200, 200, 80, "A\nleft", Z.APP)
b = p.box(600, 200, 200, 80, "B\nright", Z.APP)
p.edge(a, b, label="HTTPS", exit=(1, .4), entry=(0, .4))
p.edge(b, a, label="callback", exit=(0, .6), entry=(1, .6))
save("err-labels-overlap", p)

p = Page("warn"); p.title("Line label is a sentence")
a = p.box(100, 200, 200, 80, "A\nleft", Z.APP)
b = p.box(800, 200, 200, 80, "B\nright", Z.APP)
p.edge(a, b, label="sends the request with the key and waits", exit=(1, .5), entry=(0, .5))
save("warn-label-too-long", p)

p = Page("warn"); p.title("Line label sits on a bend")
a = p.box(100, 100, 200, 80, "A\nsource", Z.APP)
b = p.box(500, 400, 200, 80, "B\ntarget", Z.APP)
p.edge(a, b, label="AMQP", exit=(1, .5), entry=(.5, 0), points=[(600, 140)], label_at=.08)
save("warn-label-on-bend", p)

p = Page("warn"); p.title("One tab mixes badges and labels")
a = p.box(100, 120, 200, 80, "A\nleft", Z.APP)
b = p.box(560, 120, 200, 80, "B\nright", Z.APP)
c = p.box(560, 360, 200, 80, "C\nbelow", Z.APP)
p.edge(a, b, label="HTTPS", exit=(1, .5), entry=(0, .5))
p.edge(b, c, "1", exit=(.5, 1), entry=(.5, 0))
save("warn-mixed-badges-and-labels", p)

save("warn-lang-label", lang_page("ru", "1. Вызов модели", "Как приложение вызывает модель через LiteLLM",
     ["Приложение\nOpenAI SDK, ключ sk-…", "LiteLLM :4000\nпроверяет ключ, team и бюджет"],
     "1  приложение → LiteLLM: POST /v1/chat/completions", label="calls the model with the key"), "ru")

print(f"{len(list(OUT.glob('*.drawio')))} cases in {OUT}")

---
name: drawio-diagrams
description: >-
  Build draw.io diagrams of a system in the team's house style and prove them
  readable: lines never cross boxes or each other, nothing overlaps, 6 px corners,
  one tab per concern, generated from a Python script and checked by a geometry
  checker plus a look at the exported PNG. Offers the user a choice of diagram:
  principal (components and links, each line labelled with its protocol or kind of
  link) or functional (a scenario: numbered lines and a step-by-step legend), plus
  routing and delivery/CI templates. Labels are written in the language of the
  conversation. Use for "нарисуй схему", "архитектурная схема", "принципиальная
  схема", "функциональная схема", "схема взаимодействия", "роуты", "схема поставки",
  "architecture / infrastructure / component diagram", draw.io / drawio, and to fix
  an existing .drawio. "/drawio-diagrams update" updates the skill from GitHub. Not
  for sequence diagrams: msd-sequence-diagram.
---

# draw.io diagrams, house style

The team's diagrams follow one standard so any of them reads the same way: you can
follow every line with your eyes, no text hides under a line or another box, corners
are barely rounded, and the meaning of each connection is in a legend instead of
being scribbled along the line. This skill encodes that standard as a builder library
and enforces it with a checker, so the result does not depend on how careful anyone
was with the mouse.

## Commands

- **`/drawio-diagrams update`** (the argument `update`, or "обнови скилл drawio" in
  any words): do not draw anything. Run `bash <base directory>/scripts/update.sh`,
  where the base directory is the one shown when this skill loaded, and report its
  output in the conversation's language: old → new version and the list of changes,
  or "already up to date". If it refuses (local changes, diverged copy), show its
  message and the fix it suggests; do not force the update. The new version applies
  from the next time the skill loads.

## The rules (why they exist)

1. **No line goes through a box, a note or a zone title.** A line through text makes
   both unreadable. Route edges through empty corridors with explicit waypoints.
2. **No two lines run on top of each other, and lines avoid crossing.** Overlapping
   runs make it impossible to tell which arrow goes where. A crossing is allowed only
   when the topology forces it, and then it is drawn with a jump arc. Usually the
   fix is to **swap two boxes**, not to add bends.
3. **Nothing overlaps**: boxes, notes, legends keep at least 20 px apart; text fits
   its box (no clipping).
4. **Corners are absolute 6 px** (`absoluteArcSize=1;arcSize=6`) on every rectangle,
   zones included. Large relative radii look like pills and "unserious".
5. **A line says what it is in one of two ways, never both on one tab.**
   - **Principal diagram**: a short label on the line — the protocol or the kind of
     link (`HTTPS`, `SQL`, `OIDC`, `gRPC :50051`, «очередь», «секреты»), 1–3 words,
     placed on a straight run (`label=`, `label_at=`). Details live in the boxes.
   - **Functional diagram**: a numbered badge on the line; a legend explains each
     number as a step, «N  кто → кому: что».
   Free sentences along lines are where most overlaps come from; the checker
   computes where every label lands and rejects one that covers a box, a line or
   another label.
6. **One tab per concern** in one `.drawio` file: login flow, routing, delivery…
   A diagram that answers one question is readable; one that answers five is not.
7. **Generated, not dragged.** The diagram is a Python script using
   `scripts/drawio_kit.py`. The `.drawio` stays editable, but the script is the source
   of truth, so the layout can be rebuilt after any change and re-checked.
8. **Previous versions are backed up, never committed.** Overwriting a diagram copies
   the old file to `.drawio-backups/` next to it (newest 10 kept) and the kit keeps
   that folder and draw.io's own `.$*.bkp` files in the project's `.gitignore`. If the
   file was edited after the last build (by hand in draw.io), the build says so: carry
   those edits into the generator, the backup holds them.
9. **Checked before delivery.** `scripts/check_layout.py` must report 0 errors; aim
   for 0 warnings. Then look at the exported PNG yourself.
10. **Written in the language of the conversation.** The person reads the diagram in
    the language they talk to you in, so every word on it is in that language: tab
    names, the title, zone titles, box text, notes, the legend title and items, the
    Confluence placeholder. Identifiers stay exactly as in the code (component names,
    paths, ports, env vars, API fields). The language is fixed once in the generator
    (`LANG`), stored in the `.drawio`, and the checker warns about any label written
    in another script.

## Workflow

### 0. Determine the diagram language (never ask)

Take it from the user's own messages in this conversation: the language they write
to you in. If they switch, the language of the request that asked for the diagram
wins. An explicit instruction ("подпиши по-английски", "labels in Uzbek") overrides
it. Do **not** take it from the language of the code, the README, the documents you
were given, the system locale, or the house examples (they happen to be Russian).
Uzbek is `uz` (Latin script) unless the user writes in Cyrillic (`uz-Cyrl`).

Record it in the generator as an ISO code — `LANG = "ru"`, `"en"`, `"uz"` … — use
`terms(LANG)` for the standard words (legend titles «Шаги» / Steps / Qadamlar,
«Вне кластера» / Outside the cluster …), write every other label yourself in that
language, and pass `Diagram(pages, lang=LANG)` so the checker knows what to verify.
Your messages to the user follow the same language as usual.

### 1. Offer the choice of diagram (always, unless the user already named it)

Which diagram to draw is the user's call, and the two main kinds answer different
questions, so offer them before drawing. Ask one question — with AskUserQuestion
when available — in the language of the conversation, with these options (details
and templates in `references/diagram-types.md`):

1. **Принципиальная схема** / Principal diagram — what the system consists of and
   what is connected to what. Each line carries a short label: protocol or kind of
   link. No steps, no numbers. The usual answer to "покажи архитектуру", "как
   связаны компоненты".
2. **Функциональная схема** / Functional diagram — how one scenario runs through
   the system (sign-in, a model call, an upload). Lines are numbered in order, the
   legend explains every step.
3. **Маршрутизация** / Routing — what an edge proxy, ingress or gateway does with
   each path.
4. **Поставка и CI/CD** / Delivery and CI/CD — source → pipeline → registry →
   runtime, and where metrics and logs go. (A data-flow / ETL diagram can be asked
   for through "Other".)

Skip the question only when the request already names the kind ("принципиальную
схему", "по шагам, как проходит вход", "схему роутов"). If the user wants both a map
and a scenario, that is two tabs in one generator: principal first, then one
functional tab per scenario. Ask about the rest only when you cannot infer it: where
it will be published (Confluence / README), what lies outside our perimeter. The
language is never asked (step 0).

### 2. Inventory before drawing

From the code, manifests and README, write down (in your reply or a scratch note):
the nodes, which zone each belongs to, and the links. For a principal diagram, each
link with its label (protocol or kind); for a functional one, the interactions of
the scenario in order — that list **is** the legend. Drawing comes after. Check names, ports, paths against the
repository — the diagram must not invent infrastructure.

### 3. Lay out on the template

Read `references/style-guide.md` (palette, geometry, corridors) and take the layout
template for the type from `references/diagram-types.md`. Plan columns and rows on
the 1400 × 900 page before writing coordinates:

- zones as columns or bands, 40 px apart; boxes inside with ≥ 40 px corridors
  between them — corridors are where edges run;
- put boxes that talk a lot **next to each other** so their edges are straight;
- order boxes so the main flow reads left → right or top → bottom.

### 4. Write the generator

Project layout (create what is missing):

```
docs/
  drawio_kit.py               vendored copy of scripts/drawio_kit.py (keep its __version__)
  build_architecture.py       the generator: one function per tab
  architecture.drawio         generated, editable in draw.io
  architecture-<N>-<slug>.png exported previews for README / Confluence
  .drawio-backups/            previous versions + last-build fingerprint (git-ignored)
  <flow>-sequence.msd         sequence diagrams (msd-sequence-diagram skill)
  confluence/                 Confluence pages with diagram placeholders
```

Several unrelated diagrams in one repo: `build_<name>.py` → `<name>.drawio`, same
pattern. Start from `examples/build_architecture.py` — a complete four-tab generator
that passes the checker with zero findings: three functional tabs (login flow with
infrastructure, delivery + observability, nginx routing) and the same login system
as a principal diagram (tab 4).

Kit essentials:

```python
from drawio_kit import Diagram, Page, Z, export_png, terms
LANG = "ru"                                                    # the conversation's language
T = terms(LANG)                                                # standard words in LANG
p = Page("1. Вход пользователя")
p.title("Что отвечает эта вкладка, одной строкой")
p.zone(40, 60, 270, 780, T["outside_cluster"], Z.OUTSIDE)    # pastel container
a = p.box(70, 120, 210, 80, "Браузер\nштатная форма", Z.NEUTRAL)  # first line bold
b = p.box(380, 110, 230, 140, "nginx\nпубличная точка", Z.APP)
# functional diagram: numbered badges + a legend of steps
p.edge(a, b, "1", exit=(1, .5), entry=(0, .35))
p.edge(b, c, "2", exit=(1, .5), entry=(.5, 0), points=[(835, 180)])  # via corridor
p.legend(380, 700, 570, 140, T["steps"], ["1  браузер → nginx: …", "2  …"])
# principal diagram (another tab): a label on each line instead
q = Page("2. Компоненты и связи")    # same boxes, added to q the same way
q.edge(a, b, label="HTTPS", exit=(1, .5), entry=(0, .5))
q.edge(b, c, label="HTTP :9000", exit=(1, .5), entry=(.5, 0), points=[(835, 180)], label_at=-.3)
q.legend(380, 760, 570, 80, T["line_types"], ["сплошная: вызов по сети …", "пунктир: конфигурация …"])
Diagram([p, q], lang=LANG).write("docs/architecture.drawio")
```

A line label sits on the line with a white background, centred at `label_at` along
it (-1 source … 0 middle … 1 target). Put it on a straight run of at least its own
width, away from bends and other lines; the checker reports exactly what it covers.
On a principal tab the legend explains line styles and colours, not each line.

In an English conversation the same page reads `Page("1. User sign-in")`,
`T["outside_cluster"]` → "Outside the cluster", `"Browser\nstandard sign-in form"`,
legend «Steps» with "1  browser → nginx: …". `terms()` knows `ru`, `en`, `uz`; for
any other language write the words yourself (it falls back to English).

Always pass `exit` and `entry` for every edge, and waypoints whenever the straight
route would touch anything. Colour an edge by the zone it belongs to (`Z.IDP.box`
for identity calls, `Z.SECRET.box` dashed for secrets, …); dashed = configuration,
async or optional.

### 5. Validate: geometry, then visually (both are mandatory)

```bash
python3 docs/build_architecture.py                        # writes .drawio
python3 <skill>/scripts/review.py docs/architecture.drawio  # check + export every tab
```

`review.py` runs `check_layout.py` and exports each tab to PNG with the draw.io CLI.

**Geometry.** Fix every ERROR in the generator (not by hand in draw.io: the next build replaces
the file; the hand-edited version survives only in `.drawio-backups/`). Treat WARNs as defects too unless there is a reason: a crossing usually
means two boxes should swap places; "text probably does not fit" means widen the box
or cut the text; "tight corridor" means move the waypoint; "label covers …" or "label sits on a bend"
means move it with `label_at`, give the line a longer straight run, or shorten it; "not in the diagram
language" means a label slipped into another language (often copied from the code's
comments or from an example): translate it, keeping identifiers as they are.

**Visual.** Then **open every exported PNG** (Read the image) and go through the
checklist below for each tab. Report what you checked. If anything fails, fix the
generator, re-run `review.py`, and look again — do not deliver a diagram you have
not looked at after the last change. The checker proves that lines avoid boxes;
only looking proves that the picture is readable and tells the right story.

| Look for | Typical fix |
|---|---|
| every line can be followed from start to arrowhead without guessing | swap boxes, straighten via aligned ports |
| no line, badge or arrowhead on text, a box border or a zone title | move the waypoint into the corridor, shorten the zone title |
| no two lines side by side closer than ~10 px or merged | separate ports (`exit`/`entry` fractions), separate corridors |
| each badge sits next to its own line | add or move a waypoint so the line has a clear straight run |
| each line label reads on its own line, not on a bend, a border or another line | `label_at`, a longer straight run, a shorter label |
| all text visible: nothing clipped or spilling out | widen/heighten the box, cut words, `size=11` for dense boxes |
| every label in the conversation's language, identifiers untouched | translate in the generator; the checker only sees the script, you see the words |
| corners square-ish (6 px), zones read as zones, one meaning per colour | use the kit, `Z.*` palette only |
| functional: the legend explains every badge and nothing else; principal: no numbers, every line labelled or obviously structural | regenerate the legend from the inventory |
| the main flow reads left → right or top → bottom | reorder columns |
| the tab title states one question and the picture answers exactly it | split into another tab |

### 6. Deliver

Send the PNGs and the `.drawio`. For Confluence, mark where each picture goes with
this placeholder (it survives Markdown paste into Confluence), in the diagram's
language — the words are in `terms(LANG)` (`placeholder`, `source`, `tab`, `shows`):

```
> 🖼️ **ДИАГРАММА: вставить сюда `architecture-1-login.png`**
>
> Источник: `docs/architecture.drawio`, вкладка «1. Вход пользователя».
>
> Что показывает: одна фраза о содержании.
```

```
> 🖼️ **DIAGRAM: insert here `architecture-1-login.png`**
>
> Source: `docs/architecture.drawio`, tab "1. User sign-in".
>
> What it shows: one sentence about the content.
```

## Reference & tools

- `references/style-guide.md` — palette, geometry, typography, corridors, legends,
  edge semantics, naming.
- `references/diagram-types.md` — the types, the question to tell them apart, what
  goes on each, layout templates, common routing problems and their topological fixes.
- `scripts/drawio_kit.py` — builder library (copy into the project's `docs/`).
- `scripts/check_layout.py` — geometry and label-language checker for any `.drawio`,
  generated or hand-made (`--lang xx` for files without the kit's `lang` attribute).
- `scripts/review.py` — geometry check + PNG export of every tab + the visual checklist.
- `scripts/update.sh` — updates the installed skill from GitHub (`/drawio-diagrams update`).
- `examples/build_architecture.py` — complete worked generator, functional and principal tabs.

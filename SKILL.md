---
name: drawio-diagrams
description: >-
  Build architecture, infrastructure-interaction, routing and delivery diagrams as
  draw.io files in the team's house style: lines never cross boxes or each other,
  nothing overlaps, corners are 6 px, edges carry numbered badges explained in a
  legend, one tab per concern, generated from a Python script and verified by a
  geometry checker. Use whenever the user asks for a draw.io / drawio diagram or a
  "схема" of a system: "нарисуй схему", "архитектурная схема", "принципиальная
  схема", "схема взаимодействия компонентов", "схема маршрутизации", "роуты",
  "топология", "схема поставки / CI", "диаграмма для Confluence", "architecture
  diagram", "infrastructure diagram", "component diagram". Also use to review or
  fix an existing .drawio file (overlapping lines, unreadable layout, round
  corners). Not for sequence / call-flow diagrams — use msd-sequence-diagram.
---

# draw.io diagrams, house style

The team's diagrams follow one standard so any of them reads the same way: you can
follow every line with your eyes, no text hides under a line or another box, corners
are barely rounded, and the meaning of each connection is in a legend instead of
being scribbled along the line. This skill encodes that standard as a builder library
and enforces it with a checker, so the result does not depend on how careful anyone
was with the mouse.

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
5. **No text on edges.** Each edge gets a numbered badge; a legend box explains the
   numbers. Labels along lines are where most overlaps come from.
6. **One tab per concern** in one `.drawio` file: login flow, routing, delivery…
   A diagram that answers one question is readable; one that answers five is not.
7. **Generated, not dragged.** The diagram is a Python script using
   `scripts/drawio_kit.py`. The `.drawio` stays editable, but the script is the source
   of truth, so the layout can be rebuilt after any change and re-checked.
8. **Checked before delivery.** `scripts/check_layout.py` must report 0 errors; aim
   for 0 warnings. Then look at the exported PNG yourself.

## Workflow

### 1. Clarify the diagram type (ask unless it is obvious)

The type decides the layout template, so get it right first. If the request already
says it ("схема роутов", "как идёт поставка"), do not ask. Otherwise ask one
question — with AskUserQuestion when available — offering the types from
`references/diagram-types.md`:

- **Принципиальная схема / архитектура приложения** — components inside the
  application and how they depend on each other.
- **Функциональная схема взаимодействия с узлами инфраструктуры** — our service
  among existing systems: who calls whom, across which perimeter.
- **Маршрутизация (роуты)** — what an edge proxy / ingress / gateway does with each
  path: where it goes, what is stripped, what is closed.
- **Поставка и CI/CD (+ наблюдаемость)** — source → pipeline → registry → runtime,
  and where metrics/logs go.
- **Поток данных / ETL** — sources → stages → sinks.

Ask about the rest only when you cannot infer it: where it will be published
(Confluence / README), what lies outside our perimeter, language (Russian by default
for Confluence). Several types for one system → several tabs, one generator.

### 2. Inventory before drawing

From the code, manifests and README, write down (in your reply or a scratch note):
the nodes, which zone each belongs to, and the numbered interactions in order. This
list **is** the legend; drawing comes after. Check names, ports, paths against the
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
  <flow>-sequence.msd         sequence diagrams (msd-sequence-diagram skill)
  confluence/                 Confluence pages with diagram placeholders
```

Several unrelated diagrams in one repo: `build_<name>.py` → `<name>.drawio`, same
pattern. Start from `examples/build_architecture.py` — a complete three-tab
generator (login flow with infrastructure, delivery + observability, nginx routing)
that passes the checker with zero findings.

Kit essentials:

```python
from drawio_kit import Diagram, Page, Z, export_png
p = Page("1. Вход пользователя")
p.title("Что отвечает эта вкладка, одной строкой")
p.zone(40, 60, 270, 780, "Вне кластера", Z.OUTSIDE)          # pastel container
a = p.box(70, 120, 210, 80, "Браузер\nштатная форма", Z.NEUTRAL)  # first line bold
b = p.box(380, 110, 230, 140, "nginx\nпубличная точка", Z.APP)
p.edge(a, b, "1", exit=(1, .5), entry=(0, .35))               # badge, no label
p.edge(b, c, "2", exit=(1, .5), entry=(.5, 0), points=[(835, 180)])  # via corridor
p.legend(380, 700, 570, 140, "Шаги", ["1  браузер → nginx: …", "2  …"])
Diagram([p]).write("docs/architecture.drawio")
```

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

**Geometry.** Fix every ERROR in the generator (never by hand in draw.io: it would be
overwritten). Treat WARNs as defects too unless there is a reason: a crossing usually
means two boxes should swap places; "text probably does not fit" means widen the box
or cut the text; "tight corridor" means move the waypoint.

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
| all text visible: nothing clipped or spilling out | widen/heighten the box, cut words, `size=11` for dense boxes |
| corners square-ish (6 px), zones read as zones, one meaning per colour | use the kit, `Z.*` palette only |
| the legend explains every badge and nothing else | regenerate the legend from the inventory |
| the main flow reads left → right or top → bottom | reorder columns |
| the tab title states one question and the picture answers exactly it | split into another tab |

### 6. Deliver

Send the PNGs and the `.drawio`. For Confluence, mark where each picture goes with
this placeholder (it survives Markdown paste into Confluence):

```
> 🖼️ **ДИАГРАММА: вставить сюда `architecture-1-login.png`**
>
> Источник: `docs/architecture.drawio`, вкладка «1. Вход пользователя».
>
> Что показывает: одна фраза о содержании.
```

## Reference & tools

- `references/style-guide.md` — palette, geometry, typography, corridors, legends,
  edge semantics, naming.
- `references/diagram-types.md` — the types, the question to tell them apart, what
  goes on each, layout templates, common routing problems and their topological fixes.
- `scripts/drawio_kit.py` — builder library (copy into the project's `docs/`).
- `scripts/check_layout.py` — geometry checker for any `.drawio`, generated or hand-made.
- `scripts/review.py` — geometry check + PNG export of every tab + the visual checklist.
- `examples/build_architecture.py` — complete worked generator.

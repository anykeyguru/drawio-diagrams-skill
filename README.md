# drawio-diagrams

A Claude skill that builds architecture, infrastructure-interaction, routing and delivery
diagrams as **draw.io** files in one house style, and **proves** the result is readable:

- no line goes through a box, a note or a zone title;
- no two lines run on top of each other; crossings are avoided (re-arrange boxes first);
- nothing overlaps, text fits its box;
- corners are absolute 6 px, never pill-shaped;
- no text on lines: numbered badges, explained in a legend;
- one tab per concern, generated from a Python script, editable in draw.io;
- every diagram is checked by geometry **and** exported to PNG for a visual review.

```
SKILL.md                      what Claude follows: questions, workflow, rules, delivery
references/style-guide.md     palette, geometry, corridors, edges, legends, file layout
references/diagram-types.md   the five diagram types, how to tell them apart, layout templates
scripts/drawio_kit.py         builder library (vendor a copy into the project's docs/)
scripts/check_layout.py       geometry checker for any .drawio (generated or hand-made)
scripts/review.py             checker + PNG export of every tab + visual checklist
examples/build_architecture.py  worked 3-tab generator, 0 findings
tests/                        checker regression cases + example + export (tests/run.sh)
package.sh                    builds dist/drawio-diagrams.zip for claude.ai
```

## Install

**Claude Code** loads skills from `~/.claude/skills/`. Clone straight there:

```bash
git clone git@github.com:anykeyguru/drawio-diagrams-skill.git ~/.claude/skills/drawio-diagrams
```

**claude.ai**: `./package.sh`, then upload `dist/drawio-diagrams.zip` in Settings →
Capabilities → Skills (replace the existing one, or delete and upload anew).

Requirements: Python 3.9+, and the draw.io desktop app (`/Applications/draw.io.app` on
macOS, or `drawio` on PATH) for PNG export and the visual review. Without draw.io the
geometry checker still works; export is skipped.

## How a diagram gets made

1. **Clarify the type** (asked only when the request does not say it): principal
   architecture, interaction with infrastructure nodes, routing, delivery/CI with
   observability, data flow. Sequence diagrams go to the `msd-sequence-diagram` skill.
2. **Inventory** nodes, zones and numbered interactions from the code. This becomes the
   legend.
3. **Lay out** on the template for the type: zones as columns/bands, boxes with 40 px
   corridors, talkative boxes side by side.
4. **Generate** with the kit (`docs/build_architecture.py` → `docs/architecture.drawio`).
5. **Validate**: `scripts/review.py docs/architecture.drawio` — 0 errors, ideally 0
   warnings — then open every exported PNG and walk the visual checklist.
6. **Deliver** the PNGs and the `.drawio`; for Confluence, a `🖼️ ДИАГРАММА` placeholder
   marks where each picture goes.

Project layout the skill creates:

```
docs/
  drawio_kit.py                vendored kit
  build_architecture.py        generator, one function per tab (source of truth)
  architecture.drawio          generated, editable in draw.io
  architecture-<N>-<slug>.png  previews for README / Confluence
  confluence/                  pages with diagram placeholders
```

## The checker

```bash
python3 scripts/check_layout.py docs/architecture.drawio     # exit 1 on any ERROR
python3 scripts/review.py docs/architecture.drawio           # + PNG export + checklist
```

| Level | Finding |
|---|---|
| ERROR | edge runs through a box/note; edge runs through a zone or page title; two edges run on top of each other; boxes overlap; rounded corners not absolute 4–8 px |
| WARN | edges cross; edge passes closer than 6 px to a box; text probably does not fit; text label on an edge; edge without explicit exit/entry |

Edge routes are reconstructed the way draw.io's orthogonal style draws them (exit
perpendicular to the side, through the waypoints, enter perpendicular), so the check
matches the rendered picture. Works on plain and compressed `.drawio` files.

## Tests

```bash
tests/run.sh
```

- 15 generated cases, one per rule, named by the expected verdict (`ok-*`, `warn-*`,
  `err-*`), including a compressed file as the draw.io app may save it;
- the worked example must produce 3 tabs with **zero** findings;
- `review.py` must export one PNG per tab (skipped without draw.io).

The cases were also checked by eye: the rendered PNG of each failing case shows exactly
the defect the checker names.

## Changing the skill

1. Edit `SKILL.md`, a reference, the kit or the checker.
2. A new rule or a fixed false positive gets a case in `tests/make_cases.py`.
3. `tests/run.sh` must pass; look at the PNGs of new cases.
4. Bump `__version__` in `scripts/drawio_kit.py` when the kit's output changes, so
   projects can tell which copy they vendored.
5. `./package.sh` and re-upload to claude.ai.

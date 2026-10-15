# drawio-diagrams

[![tests](https://github.com/anykeyguru/drawio-diagrams-skill/actions/workflows/tests.yml/badge.svg)](https://github.com/anykeyguru/drawio-diagrams-skill/actions/workflows/tests.yml)

A Claude skill that draws **draw.io** diagrams of a system in one house style and
**proves** the result is readable. Before drawing it asks which diagram you need:

- **Principal diagram** (принципиальная схема): what the system consists of and what is
  connected to what. Each line carries a short label: the protocol or kind of link
  (`HTTPS`, `SQL`, `OIDC`, «очередь»). No steps, no numbers.
- **Functional diagram** (функциональная схема): how one scenario runs through the
  system. Lines are numbered in order, a legend explains every step.
- **Routing** and **delivery / CI/CD** templates for edge proxies and pipelines.

Every diagram, whatever the kind:

- no line goes through a box, a note or a zone title; lines do not run on top of each
  other and avoid crossing; nothing overlaps; text fits its box;
- line labels land where the checker expects them: never on a box, a bend, another
  line or another label;
- corners are absolute 6 px; one tab per concern;
- every label is in the language of the conversation (Russian, English, Uzbek, …);
  component names, paths and env vars stay as in the code;
- generated from a Python script (the source of truth), editable in draw.io, checked
  by geometry **and** exported to PNG for a visual review;
- overwriting a diagram backs up the previous version to `.drawio-backups/` (git-ignored).

## Install

The skill is a folder named `drawio-diagrams` with `SKILL.md` at its top. Requirements:
`git`, Python 3.9+, and for PNG export the [draw.io desktop app](https://www.drawio.com)
(`/Applications/draw.io.app` on macOS, or `drawio` on `PATH`; without it everything
except the export works).

### Claude Code (CLI, desktop app, IDE extensions)

For yourself, in every project:

```bash
git clone https://github.com/anykeyguru/drawio-diagrams-skill.git ~/.claude/skills/drawio-diagrams
```

For everyone working in one repository, commit it into the project instead:

```bash
git clone https://github.com/anykeyguru/drawio-diagrams-skill.git .claude/skills/drawio-diagrams
rm -rf .claude/skills/drawio-diagrams/.git
```

Start a new Claude Code session (skills are read at start-up) and ask «нарисуй схему …»
or type `/drawio-diagrams`.

### claude.ai (web and desktop chat)

Download `drawio-diagrams.zip` from the [latest release](https://github.com/anykeyguru/drawio-diagrams-skill/releases/latest),
or build it from a clone with `./package.sh` (writes `dist/drawio-diagrams.zip`). Then
Settings → Capabilities → Skills → Upload skill. To update, delete the old one and
upload the new zip.

### Asking an AI assistant to install it

You can say to Claude Code (or another agent with a shell): *"install the skill
https://github.com/anykeyguru/drawio-diagrams-skill"*. The steps below are written for
that assistant.

> **Instructions for an AI assistant installing this skill**
>
> 1. Check that `git` and `python3` (3.9 or newer) are available. If `~/.claude/skills/drawio-diagrams`
>    already exists, do not overwrite it: run `bash ~/.claude/skills/drawio-diagrams/scripts/update.sh`
>    instead and report its output.
> 2. Install for the user (all projects) unless they asked for this project only:
>    `git clone https://github.com/anykeyguru/drawio-diagrams-skill.git ~/.claude/skills/drawio-diagrams`.
>    For this project only: clone into `.claude/skills/drawio-diagrams` of the repository and remove its `.git`.
>    The folder name must be `drawio-diagrams`, the same as `name:` in `SKILL.md`.
> 3. Verify: `cat ~/.claude/skills/drawio-diagrams/VERSION` prints a version, and
>    `bash ~/.claude/skills/drawio-diagrams/tests/run.sh` ends with `all passed`.
> 4. Check for draw.io: `/Applications/draw.io.app` on macOS or `drawio` on `PATH`. If
>    it is missing, tell the user that diagrams work but PNG export needs
>    https://www.drawio.com; do not install it without asking.
> 5. Tell the user the installed version, that the skill appears in new sessions, and
>    that `/drawio-diagrams update` updates it later.
>
> In claude.ai (no shell) the assistant cannot install skills: point the user to the
> claude.ai steps above.

### Update

In Claude Code type:

```
/drawio-diagrams update
```

The skill runs `scripts/update.sh` and reports old → new version and what changed. You
can also run it yourself:

```bash
bash ~/.claude/skills/drawio-diagrams/scripts/update.sh
```

- installed with `git clone`: fast-forwards to `main` of this repository; if you changed
  files in the installed copy, or committed to it, it refuses and says how to resolve
  it, nothing is overwritten;
- installed by copying or unzipping: the old copy goes to `~/.cache/drawio-diagrams/`
  and is replaced by a fresh clone (so the next update is a fast-forward).

The new version is picked up from the next session.

## How a diagram gets made

0. **Take the language** from the conversation (never asked): `LANG = "ru" | "en" | "uz" …`.
1. **Offer the choice** of diagram: principal, functional, routing, delivery/CI (data
   flow via "Other"). Skipped when the request already names it. Sequence diagrams go
   to the `msd-sequence-diagram` skill.
2. **Inventory** nodes, zones and links from the code: labels for a principal diagram,
   numbered steps for a functional one.
3. **Lay out** on the template: zones as columns/bands, boxes with 40 px corridors,
   talkative boxes side by side.
4. **Generate** with the kit (`docs/build_architecture.py` → `docs/architecture.drawio`).
5. **Validate**: `scripts/review.py docs/architecture.drawio` — 0 errors, ideally 0
   warnings — then open every exported PNG and walk the visual checklist.
6. **Deliver** the PNGs and the `.drawio`; for Confluence, a `🖼️` placeholder in the
   diagram's language marks where each picture goes.

Project layout the skill creates:

```
docs/
  drawio_kit.py                vendored kit
  build_architecture.py        generator, one function per tab (source of truth)
  architecture.drawio          generated, editable in draw.io
  architecture-<N>-<slug>.png  previews for README / Confluence
  .drawio-backups/             previous versions, local only
  confluence/                  pages with diagram placeholders
```

`Diagram.write()` keeps `.drawio-backups/` and `.$*.bkp` (draw.io's own backup copies) in
the repository's `.gitignore`, appending them if missing. Backups never reach git.

## Repository

```
SKILL.md                        what Claude follows: commands, rules, workflow, delivery
CLAUDE.md                       maintainer notes: invariants, changing, releasing
VERSION                         skill version (= drawio_kit.__version__)
references/style-guide.md       palette, geometry, corridors, edges, labels, legends, files
references/diagram-types.md     the diagram kinds, the question offered, layout templates
scripts/drawio_kit.py           builder library (vendor a copy into the project's docs/)
scripts/check_layout.py         geometry, line-label and label-language checker for any .drawio
scripts/review.py               checker + PNG export of every tab + visual checklist
scripts/update.sh               self-update from this repository
examples/build_architecture.py  worked 4-tab generator (3 functional, 1 principal), 0 findings
tests/                          tests/run.sh: everything below
package.sh                      builds dist/drawio-diagrams.zip for claude.ai
.github/workflows/tests.yml     runs tests/run.sh on every push and pull request
.github/workflows/release.yml   tag v<VERSION> → tests + zip for claude.ai on a GitHub release
```

## The checker

```bash
python3 scripts/check_layout.py docs/architecture.drawio     # exit 1 on any ERROR
python3 scripts/review.py docs/architecture.drawio           # + PNG export + checklist
```

| Level | Finding |
|---|---|
| ERROR | edge runs through a box/note; edge runs through a zone or page title; two edges run on top of each other; boxes overlap; rounded corners not absolute 4–8 px; a line label covers a box, a zone title, another line or another label, or leaves the page |
| WARN | edges cross; edge passes closer than 6 px to a box; text probably does not fit; free text on an edge; a line label too long or on a bend; badges and labels mixed on one tab; edge without explicit exit/entry; a label not in the diagram language |

Edge routes are reconstructed the way draw.io's orthogonal style draws them (exit
perpendicular to the side, through the waypoints, enter perpendicular), and a line
label is placed where draw.io places it (centred at its position along the line), so
the check matches the rendered picture. Works on plain and compressed `.drawio` files.
The language comes from the file (`Diagram(pages, lang=...)`) or `--lang`.

## Tests

```bash
tests/run.sh
```

Runs on GitHub Actions for every push and pull request (Python 3.9 and 3.13 on
Ubuntu 24.04; the PNG export step is skipped there, draw.io is not installed).

- generated cases, one per rule, named by the expected verdict (`ok-*`, `warn-*`,
  `err-*`): geometry, line labels, label language, a compressed file as the draw.io
  app may save it;
- backups, in a throwaway git repo: first write, unchanged rewrite, changed rewrite,
  invisibility to git, a generator change not mistaken for a hand edit, a real hand edit
  warned and preserved, rotation to 10, no duplicate `.gitignore` lines, outside git;
- the worked example must produce 4 tabs with **zero** findings, language included;
- `review.py` must export one PNG per tab (skipped without draw.io);
- self-update against a local repository: fast-forward, already up to date, local
  changes refused, diverged copy refused, zip install backed up and replaced, a
  foreign folder left alone;
- `VERSION` equals the kit's `__version__`; `SKILL.md` has its name and a description
  within claude.ai's 1024-character limit.

## Changing the skill

1. Edit `SKILL.md`, a reference, the kit or the checker.
2. A new rule or a fixed false positive gets a case in `tests/make_cases.py`; look at
   the rendered PNG of the case.
3. `tests/run.sh` must pass locally; GitHub Actions runs it again on push.
4. Bump `VERSION` and `__version__` in `scripts/drawio_kit.py` together, so projects
   can tell which kit they vendored and `/drawio-diagrams update` reports the change.
5. Release: push a tag `v<VERSION>` (`git tag v1.3.0 && git push origin v1.3.0`). The
   release workflow runs the tests and attaches `drawio-diagrams.zip` for claude.ai.

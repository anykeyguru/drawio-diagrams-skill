# drawio-diagrams skill: maintainer notes

This repository is a Claude skill used by the whole team. It draws draw.io diagrams
in one house style and proves them readable with a geometry checker and a look at
the exported PNG. Public repo: https://github.com/anykeyguru/drawio-diagrams-skill.
Users install it with `git clone` into `~/.claude/skills/drawio-diagrams` (or a
project's `.claude/skills/`), or upload the release zip to claude.ai, and update it
with `/drawio-diagrams update`.

## What lives where

| Path | Role | Notes |
|---|---|---|
| `SKILL.md` | what Claude follows when the skill runs | frontmatter `name: drawio-diagrams`, description ≤ 1024 chars (claude.ai limit, tested) |
| `references/style-guide.md` | palette, geometry, edges, labels, legends, files | measurable parts are enforced by the checker |
| `references/diagram-types.md` | the kinds offered to the user and their templates | principal (labelled lines) vs functional (numbered steps) |
| `scripts/drawio_kit.py` | builder library, vendored by projects into `docs/` | `__version__` must equal `VERSION` |
| `scripts/check_layout.py` | checker: geometry, line labels, label language | standalone, stdlib only |
| `scripts/review.py` | checker + PNG export of every tab + visual checklist | export needs the draw.io desktop app |
| `scripts/update.sh` | self-update behind `/drawio-diagrams update` | ships to users; never make it destructive |
| `examples/build_architecture.py` | worked 4-tab generator | must produce zero findings |
| `tests/` | `tests/run.sh` runs everything | cases are generated, `tests/cases/` is git-ignored |
| `package.sh` | builds `dist/drawio-diagrams.zip` for claude.ai | runs the tests first |
| `.github/workflows/` | `tests.yml` on every push/PR, `release.yml` on `v*` tags | runner pinned to `ubuntu-24.04` |

## Invariants

- Python 3.9+ and the standard library only. No dependencies: the skill runs on any
  laptop and in claude.ai. `from __future__ import annotations` where `X | None` is used.
- Shell scripts work with both BSD (macOS) and GNU (CI) tools.
- Every rule the checker enforces has a case in `tests/make_cases.py`, named by the
  expected verdict (`ok-*`, `warn-*`, `err-*`). A fixed false positive gets a case too.
- A diagram kind is explained one way per tab: line labels (principal) or numbered
  badges (functional), never both.
- All diagram text is in the language of the conversation; the checker verifies the
  script (Cyrillic / Latin), identifiers excluded.
- `update.sh` never overwrites local changes or diverged history, never deletes a
  folder that is not this skill, and backs up zip installs outside the skills folder.
- Documentation in this repository is in English.

## Changing the skill

1. Edit `SKILL.md`, a reference, the kit or the checker.
2. Add or adjust a case in `tests/make_cases.py`; for anything visual, export it
   (`python3 scripts/review.py tests/cases/<case>.drawio --out /tmp/x`) and look at it.
3. If the kit or the example output changed: run the example and look at every tab.
4. `tests/run.sh` must end with `all passed`.
5. Keep `README.md` in step: feature list, install, checker table, tests list.

This working copy is often the maintainer's live install (`~/.claude/skills/drawio-diagrams`):
edits take effect in new sessions immediately, and `scripts/update.sh` refuses to run
while they are uncommitted. That is intended.

## Releasing

Semantic versioning: patch for fixes, minor for new rules or features, major when
generators written for the previous kit stop working.

1. Bump `VERSION` and `__version__` in `scripts/drawio_kit.py` to the same value.
2. `tests/run.sh` → `all passed`.
3. Commit and push to `main`; wait for the `tests` workflow to be green.
4. Tag and push: `git tag v<VERSION> && git push origin v<VERSION>`.
5. The `release` workflow checks the tag equals `VERSION`, runs the tests, builds the
   zip and publishes a GitHub release with `drawio-diagrams.zip` attached. Check that
   the release exists and has the asset.

Users of a git install get the release with `/drawio-diagrams update` (it follows
`main`, so merged changes reach them even before a tag); claude.ai users re-upload the
zip from the latest release.

Commits and pushes are made by the owner. An assistant prepares the change, runs the
tests and hands over the commit message; it commits, pushes or tags only when the
owner explicitly says so ("закоммить сам").

## CI notes

- `tests.yml`: Python 3.9 and 3.13 on `ubuntu-24.04`. draw.io is not installed there,
  so the PNG export test is skipped; run `tests/run.sh` locally with draw.io before a
  release.
- Actions are on majors that run on Node 24 (`checkout@v6`, `setup-python@v6`). When
  GitHub warns about a deprecated runtime or runner image, bump deliberately and check
  the oldest Python in the matrix is still available.

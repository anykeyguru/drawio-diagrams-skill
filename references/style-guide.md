# Style guide

Everything here is what `drawio_kit.py` produces by default. Hand-made diagrams must
follow it too; `check_layout.py` enforces the measurable parts.

## Page

| Item | Value |
|---|---|
| Page size | 1400 × 900 (raise height to ~920–1000 only when a tab really needs it) |
| Outer margin | 40 px on all sides |
| Title | `p.title(...)`: one line at y = 15, 14 px bold, states the one question the tab answers |
| Tabs | one concern per tab, named `N. Тема` («1. Вход пользователя», «2. Поставка и наблюдаемость») |
| Language | Russian for Confluence/internal docs unless the user says otherwise; component names, paths and env vars stay as in the code |

## Zones (containers)

A zone is a perimeter or an ownership boundary: «Вне кластера», «Кластер, namespace X»,
«Keycloak (realm)», «GitLab», «Наблюдаемость». Pastel fill, coloured border, bold title in
the top-left corner, 6 px corners.

| Palette entry | Fill / border / box stroke | Meaning |
|---|---|---|
| `Z.APP` | `#e8f5e9` / `#66bb6a` / `#2e7d32` | our application, our cluster |
| `Z.IDP` | `#ede7f6` / `#7e57c2` / `#5e35b1` | identity: Keycloak, SSO, directory groups |
| `Z.OUTSIDE` | `#fff3e0` / `#ffa726` (dashed) / `#ef6c00` | outside our perimeter: users, AD, external systems, registries |
| `Z.DATA` | `#e3f2fd` / `#42a5f5` / `#1565c0` | data stores, LLM backends, observability |
| `Z.CI` | `#fce4ec` / `#ec407a` / `#ad1457` | source control, CI/CD |
| `Z.SECRET` | box `#fff8e1` / `#f9a825` | secrets, credentials, secret stores |
| `Z.DENY` | box `#ffebee` / `#c62828` | closed paths: 404/403, blocked routes |
| `Z.NEUTRAL` | box `#f5f5f5` / `#666666` | people, browsers, generic clients |
| `Z.LEGEND` | box `#fafafa` / `#666666` | legend boxes |

One colour means one thing across all tabs. Do not invent colours per diagram.

Zone titles are short (a name, not a sentence): edges entering a zone cross its top
border, and a long title is in their way. Put explanations into a note inside the zone.

## Boxes

- First line bold = the component's name (`Deployment auth-bridge ×2 (:9000)`), next lines
  = what matters for this diagram: role, ports, key settings. 3–6 lines.
- Font 12 px; 11 px for dense boxes (`size=11`).
- Width ≈ characters of the longest line × 7 + 20 px at 12 px font. If a line is longer
  than the box allows, it wraps and the box must be taller. The checker warns when the
  estimated text does not fit.
- Corners: absolute 6 px, always.
- Notes (`p.note`) are frameless grey text for rationale and constraints. They obey the
  same no-overlap rules as boxes.

## Corridors and spacing

- Leave ≥ 40 px between boxes that stand side by side, ≥ 20 px between stacked boxes.
  These gaps are the corridors edges run in.
- An edge keeps ≥ 6 px from any box it does not connect (checker: "tight corridor").
- Plan corridors when placing boxes: the middle of a 40–60 px gap is where waypoints go
  (`points=[(x_corridor, y1), (x_corridor, y2)]`).

## Edges

| Property | Value |
|---|---|
| Style | orthogonal, square bends (`rounded=0`), 1.5 px, block-thin arrow |
| Label | none; a numbered badge (20 px circle, edge colour, white number) at the middle |
| Legend | a box with title «Шаги» (flows) or «Связи» (structures): one line per number, «N  кто → кому: что» |
| Colour | the zone colour of the relationship: identity calls `Z.IDP.box`, secrets `Z.SECRET.box`, observability `Z.DATA.box`, deny `Z.DENY.box`, plain calls `#444444` |
| Dashed | configuration, async, optional or "reads from" (env, secrets, scrape, logs) |
| Ports | always explicit `exit=(fx, fy)` and `entry=(fx, fy)`; different fractions for different edges on the same side |
| Unnumbered edges | allowed only for trivial structural links (ConfigMap → Deployment) that need no legend line |

Numbering follows the reading order of the main flow (1 is where the story starts).

## Files

| What | Where |
|---|---|
| Generator | `docs/build_architecture.py` (or `docs/build_<name>.py`) |
| Kit | `docs/drawio_kit.py`, vendored copy, keep `__version__` |
| Diagram | `docs/architecture.drawio`, all tabs |
| Previews | `docs/architecture-<N>-<slug>.png`, exported by the generator or `review.py` |
| Backups | `docs/.drawio-backups/<name>.<timestamp>.drawio`, newest 10, written by `Diagram.write()` before overwriting; git-ignored together with draw.io's `.$*.bkp` (the kit adds both patterns to `.gitignore`) |
| Sequence diagrams | `docs/<flow>-sequence.msd` (msd-sequence-diagram skill) |
| Confluence | `docs/confluence/*.md` with `🖼️ ДИАГРАММА` placeholders |

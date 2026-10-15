# Diagram types

Pick the kind first: it decides how lines are explained and which template to use.
One system often needs a principal map plus one functional tab per important
scenario, each on its own tab of the same `.drawio`.

## How to tell them apart (the question offered to the user)

| If the user wants to know… | Kind | Lines carry |
|---|---|---|
| what the system consists of and what is connected to what | 1. Принципиальная схема / principal | a short label: protocol or kind of link |
| how one scenario runs through the system, step by step | 2. Функциональная схема / functional | a number; the legend explains each step |
| what happens to each request path at the edge (proxy / ingress / gateway) | 3. Маршрутизация / routing | numbers explained per rule |
| how code becomes a running service and where its telemetry goes | 4. Поставка и CI/CD / delivery | numbers, legend «Связи» |
| where data comes from, what transforms it, where it lands | 5. Поток данных / data flow | labels (what flows) or numbers (in which order) |
| the order of calls with branches and errors | not draw.io: sequence diagram, msd-sequence-diagram skill | |

AskUserQuestion (always, unless the request already names the kind), in the
conversation's language: header «Схема» / "Diagram", question «Какую схему делаем?» /
"Which diagram should I draw?", options = kinds 1–4 with one-line descriptions from
the table; kind 5 through "Other". Recommend 1 when the user asked about
"architecture" or "how the parts connect", 2 when they described a scenario.

## 1. Принципиальная схема / principal diagram

What goes on: the components (services, workers, stores, queues, external systems),
zones = perimeters or ownership, and every link between components as a line with a
short label: the protocol, port or kind of link (`HTTPS`, `HTTP :9000`, `SQL`,
`OIDC`, `LDAPS :636`, «очередь arq», «секреты»). Not on: the order of calls, what
happens inside a component, numbers.

```
┌ Клиенты ┐            ┌──────────── Система ─────────────┐         ┌ Внешние ┐
│ браузер │──HTTPS────▶│ edge ──HTTP──▶ API ──SQL──▶ БД   │──OIDC──▶│ IdP     │
│ прилож. │──API key──▶│         API ──AMQP──▶ воркер     │         └─────────┘
└─────────┘            └──────────────────────────────────┘
```

- columns left → right in call direction; layers top → bottom inside a zone;
- labels sit on straight runs, so leave runs at least as long as the label (≈ 7 px
  per character + 10) between boxes, or pick a longer run with `label_at`;
- the legend (`T["line_types"]`) explains line styles and colours only: solid =
  network call, dashed = configuration / secrets / async, colour = zone;
- details belong in the boxes: ports, roles, key settings.

Worked example: tab 4 of `examples/build_architecture.py`.

## 2. Функциональная схема / functional diagram (a scenario, step by step)

What goes on: the components one scenario touches, the existing systems they talk to
(IdP, directory, secret store, proxies, LLM backends…), zones = perimeters (outside /
our cluster / other teams' systems), the interactions of the scenario numbered in
order, config and secret sources. The legend «Шаги» / Steps explains every number:
«N  кто → кому: что».

```
┌ Вне кластера ┐  ┌─────────── Кластер ───────────┐  ┌ Внешняя система (IdP) ┐
│ пользователь │─1▶ edge proxy ─2▶ наш сервис ─3──────▶ клиент / federation   │
│              │  │      │7          │5,6         │  └───────────┬──────────┘
│ хранилище    │  │      ▼           ▼            │  ┌ Вне кластера ─▼───────┐
│ секретов ─10─────▶ Secret ─9─▶ приложение       │  │ каталог (AD)          │
└──────────────┘  │  легенда «Шаги»              │  └───────────────────────┘
                  └───────────────────────────────┘
```

Worked example: tab 1 of `examples/build_architecture.py`.

## 3. Маршрутизация (роуты)

What goes on: the client, the edge component as a zone, **one box per rule** (path
pattern + what is done: proxied, stripped headers, limits, closed), the targets in a
column on the right (services, a red «404» box for closed paths), and what targets call
next if it matters.

```
          ┌──────── edge proxy ────────┐
клиент ─1▶│ rule A: /login  …  ────2──▶│ service X ──7──▶ IdP
          │ rule B: /config …  ────3──▶│
          │ rule C: /signup → 404 ─4──▶│ 404 (red)
          │ rule D: /scim   → 404 ─5──▶│
          │ rule E: /       …  ────6──▶│ application
          └────────────────────────────┘
```

Rules top → bottom in the proxy's matching order; closed rules in `Z.DENY`.
Worked example: tab 3 of `examples/build_architecture.py`.

## 4. Поставка и CI/CD (+ наблюдаемость)

What goes on: repository → runner/pipeline stages → registry (proxy-cache and our
project) → runtime (cluster objects) in the top row; observability as a bottom band:
metrics store, alert rules, dashboards, logs, with dashed edges from the runtime.

```
┌ GitLab ┐   ┌ Registry ┐   ┌ Кластер ┐
│ repo   │   │ proxy    │◀2─┤         │
│ runner │─3▶│ project  │─4▶│ pod     │
└────────┘   └──────────┘   └──┬───┬──┘
┌──────────── Наблюдаемость ───6───10─────────┐
│ Prometheus ─8▶ Grafana ◀9─ Logs   legend   │
└─────────────────────────────────────────────┘
```

Worked example: tab 2 of `examples/build_architecture.py`.

## 5. Поток данных / ETL

What goes on: sources (left), pipeline stages (middle, in execution order), sinks
(right), schedules and failure paths (dead letter) in `Z.DENY`, data contracts in notes.

```
источники ─1▶ extract ─2▶ validate ─3▶ load ─4▶ хранилище
                  └──5 (rejected)──▶ dead letter
```

## Routing problems and their fixes

| Symptom | Fix |
|---|---|
| Two edges must cross because of where boxes stand | swap the two boxes (example: putting auth-bridge next to Keycloak and Open WebUI under nginx removed the only crossing on the login tab) |
| A long edge goes around half the page | move the target closer, or split the tab |
| Several edges leave one side of a box | give each its own port fraction (0.25 / 0.5 / 0.75) and its own corridor |
| An edge must reach a box surrounded by others | leave a 40 px corridor when placing boxes; enter from the side that faces the corridor |
| Edge crosses a zone title | shorten the title, enter the zone through its side or right part |
| Badge lands on a bend | add a waypoint so the line has a straight run in the middle |

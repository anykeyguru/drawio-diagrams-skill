# Diagram types

Pick the type first: it decides the template. One system usually needs 2–3 types, each
on its own tab of the same `.drawio`.

## How to tell them apart (the clarifying question)

| If the user wants to know… | Type |
|---|---|
| what the application consists of and how its parts depend on each other | 1. Принципиальная схема / архитектура приложения |
| how our service works together with existing systems: who calls whom, across which perimeter | 2. Функциональная схема взаимодействия с узлами инфраструктуры |
| what happens to each request path at the edge (proxy / ingress / gateway) | 3. Маршрутизация (роуты) |
| how code becomes a running service and where its telemetry goes | 4. Поставка и CI/CD (+ наблюдаемость) |
| where data comes from, what transforms it, where it lands | 5. Поток данных / ETL |
| the order of calls in one scenario, with branches and errors | not draw.io: sequence diagram, msd-sequence-diagram skill |

Suggested AskUserQuestion: header «Тип схемы», question «Какую схему строим?», options =
the five types above with one-line descriptions. Ask only if the request does not say it.

## 1. Принципиальная схема / архитектура приложения

What goes on: components of the application (services, workers, stores, queues, external
APIs it owns a client for), dependencies between them, protocols and ports where they
matter. Not on: infrastructure the application does not know about.

```
┌ Клиенты ┐   ┌──────────── Приложение ────────────┐   ┌ Хранилища / внешние API ┐
│ UI      │──▶│ API ──▶ домен ──▶ адаптеры         │──▶│ БД, кеш, очередь        │
│ джобы   │   │        воркеры / джобы             │   │ внешние сервисы         │
└─────────┘   └────────────────────────────────────┘   └─────────────────────────┘
```

Columns left → right in call direction; layers top → bottom inside the application zone.

## 2. Функциональная схема взаимодействия с узлами инфраструктуры

What goes on: our components, the existing systems they talk to (IdP, directory, secret
store, proxies, LLM backends…), zones = perimeters (outside / our cluster / other teams'
systems), the interactions of one scenario numbered in order, config and secret sources.

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

#!/usr/bin/env python3
"""Worked example: the three-tab architecture of openwebui-auth-bridge.

Login flow with infrastructure nodes (type 2), delivery + observability (type 4),
nginx routing (type 3). Passes check_layout.py with zero findings. In a project this
file is docs/build_architecture.py and writes docs/architecture.drawio.

Original docstring:
Generates docs/architecture.drawio: one tab per concern, house style (drawio_kit).

    python3 docs/build_architecture.py      # writes the .drawio, checks layout, exports PNGs

drawio_kit.py next to this file is a vendored copy of the drawio-diagrams skill kit.
Edit the diagram HERE, not in the draw.io app: the file is regenerated.
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
# In a project the kit sits next to this file (docs/drawio_kit.py). In the skill
# repository the example imports it from ../scripts.
sys.path.insert(0, str(HERE.parent / "scripts"))
from drawio_kit import Diagram, Page, Z, export_png  # noqa: E402
G, P, O, B, Y, R = Z.APP.box, Z.IDP.box, Z.OUTSIDE.box, Z.DATA.box, Z.SECRET.box, Z.DENY.box


def page_login() -> Page:
    p = Page("1. Вход пользователя", height=920)
    p.title("Вход в Open WebUI через Keycloak-bridge: пароль проверяют Keycloak и AD, пользователь не покидает страницу Open WebUI")
    p.zone(40, 60, 270, 800, "Вне кластера", Z.OUTSIDE)
    browser = p.box(70, 120, 210, 80, "Человек (браузер)\nштатная форма входа Open WebUI\nemail + пароль из AD", Z.NEUTRAL)
    p.note(70, 230, 210, 150, "Редиректа на Keycloak нет: его страница входа, redirect URI и OIDC-клиент с authorization code не нужны.\n\nПароль живёт только в AD. В Open WebUI у пользователя случайный локальный пароль, которым никто не пользуется.")
    vault = p.box(70, 700, 210, 90, "Хранилище секретов\nKC_CLIENT_SECRET, SCIM_TOKEN,\nWEBUI_SECRET_KEY", Z.OUTSIDE)

    p.zone(350, 60, 630, 800, "Кластер, namespace openwebui", Z.APP)
    nginx = p.box(380, 110, 230, 140, "Ingress + nginx (proxy)\nединственная публичная точка\nsignin, /api/config → auth-bridge\nX-Forwarded-* вырезаются везде\nsignup, ldap, scim → 404\nlimit_req 30/мин → 429", Z.APP)
    owui = p.box(380, 320, 230, 160, "Open WebUI (:8080)\nдоверенные заголовки,\nENABLE_SIGNUP=false, SCIM on;\nсоздаёт пользователя по email,\nсинхронизирует группы и роль,\nвыдаёт свой JWT + cookie", Z.APP)
    llm = p.box(380, 520, 230, 60, "LLM-бэкенды\nOllama / OpenAI-compatible", Z.DATA, fill="#e3f2fd")
    bridge = p.box(720, 320, 230, 180, "auth-bridge ×2 (:9000)\npassword-grant в Keycloak\nuserinfo: email, имя, группы\nгруппы: только openwebui-*\nроль: ADMIN_GROUP → admin\nгруппы в Open WebUI через SCIM\n/healthz /readyz /metrics", Z.APP)
    cm = p.box(720, 520, 230, 80, "ConfigMap auth-bridge-env\nKEYCLOAK_URL, KC_REALM,\nKC_CLIENT_ID, OPENWEBUI_URL,\nADMIN_GROUP, GROUP_PREFIX", Z.APP, size=11)
    sec = p.box(720, 615, 230, 60, "Secret auth-bridge\nKC_CLIENT_SECRET, SCIM_TOKEN", Z.SECRET)
    p.legend(380, 700, 570, 145, "Шаги", [
        "1  браузер → nginx: форма входа, POST signin и GET /api/config",
        "2  nginx → bridge: только эти два пути",
        "3  bridge → Keycloak: /token grant_type=password, затем /userinfo",
        "4  Keycloak → AD: LDAP bind и атрибуты (User Federation)",
        "5  bridge → Open WebUI: SCIM создаёт недостающие openwebui-* группы",
        "6  bridge → Open WebUI: signin с X-Forwarded-*; JWT и cookie → браузеру",
        "7  nginx → Open WebUI: всё остальное с JWT (чат, /ws, API)",
        "8  Open WebUI → модели   9  Secret → Open WebUI   10  хранилище → Secret",
    ])

    p.zone(1020, 60, 340, 550, "Keycloak (realm)", Z.IDP)
    client = p.box(1050, 100, 280, 120, "Клиент open-webui-bridge\nClient authentication: On\nDirect access grants: On\nStandard / implicit flow: Off\nмаппер Group Membership → groups", Z.IDP)
    fed = p.box(1050, 240, 280, 110, "User Federation → AD/LDAP\nvendor Active Directory\nимпорт пользователей, Trust email\nbrute-force detection On", Z.IDP)
    groups = p.box(1050, 370, 280, 100, "Группы (создаёт админ Keycloak)\nopenwebui-admins → role admin\nopenwebui-* → в Open WebUI\nгруппы AD не уезжают", Z.IDP)
    kadmin = p.box(1050, 500, 280, 80, "Администратор Keycloak\nкладёт людей из AD в группы;\nправа групп — в Open WebUI", Z.IDP, fill="#f3e5f5")
    p.zone(1020, 650, 340, 210, "Вне кластера", Z.OUTSIDE)
    ad = p.box(1050, 700, 280, 110, "Корпоративный AD / LDAP\nldap(s):// 389/636\nпользователи, mail / UPN, пароли;\nгруппы каталога не используются", Z.OUTSIDE)

    p.edge(browser, nginx, "1", exit=(1, .5), entry=(0, .35))
    p.edge(nginx, bridge, "2", exit=(1, .5), entry=(.5, 0), points=[(835, 180)])
    p.edge(bridge, client, "3", exit=(1, .15), entry=(0, .5), points=[(1000, 347), (1000, 160)], color=P)
    p.edge(fed, ad, "4", exit=(1, .5), entry=(1, .5), points=[(1345, 295), (1345, 755)], color=P)
    p.edge(bridge, owui, "5", dashed=True, exit=(0, .44), entry=(1, .5))
    p.edge(bridge, owui, "6", exit=(0, .7), entry=(1, .8))
    p.edge(nginx, owui, "7", exit=(.5, 1), entry=(.5, 0))
    p.edge(owui, llm, "8", dashed=True, exit=(.3, 1), entry=(.3, 0), color=B)
    p.edge(sec, owui, "9", dashed=True, exit=(0, .3), entry=(1, .95), points=[(665, 633), (665, 472)], color=Y)
    p.edge(vault, sec, "10", dashed=True, exit=(1, .5), entry=(0, .75), points=[(330, 745), (330, 660)], color=Y)
    p.edge(cm, bridge, "", dashed=True, exit=(.5, 0), entry=(.5, 1), color="#888888")
    p.edge(kadmin, groups, "", exit=(.5, 0), entry=(.5, 1), color="#7e57c2")
    return p


def page_delivery() -> Page:
    p = Page("2. Поставка и наблюдаемость")
    p.title("Поставка образа auth-bridge и наблюдаемость: узлы инфраструктуры и их взаимодействие")
    p.zone(40, 60, 440, 420, "GitLab gitlab.mbabm.uz, ai/ai-services/ai_services", Z.CI)
    repo = p.box(70, 100, 380, 70, "Репозиторий\nauth-bridge/, nginx/, deploy/{k8s,grafana,monitoring},\ntests/{contract,integration}, .gitlab-ci.yml", Z.CI)
    runner = p.box(70, 210, 380, 160, "Shell-раннер swarm (docker)\ncontract-test → build → integration ‖ trivy → push\ncontract: голый Open WebUI, 18 проверок API\nintegration: вся цепочка от LDAP до nginx, 14 проверок\ntrivy: HIGH/CRITICAL; в рантайме нет pip и uv\npush-dev вручную; тег v<owui>-rN → <owui>-rN", Z.CI)
    cvars = p.box(70, 400, 380, 60, "CI/CD Variables (группа AI-services)\nHARBOR_HOST, HARBOR_PROJECT, HARBOR_ROBOT_USER,\nHARBOR_ROBOT_PASS, PIP_INDEX_URL", Z.CI, fill="#fff8e1", size=11)
    p.zone(520, 60, 400, 420, "Harbor harbor.mbabm.uz (airgap)", Z.OUTSIDE)
    proxy = p.box(550, 100, 340, 150, "Proxy-cache проекты\nghcr.io: open-webui:v0.11.4@digest,\nastral-sh/uv, aquasecurity/trivy\nquay.io: keycloak:26.8.0@digest\nhub: python:3.13-slim, nginx:1.28-alpine,\nosixia/openldap (все @digest)", Z.OUTSIDE)
    proj = p.box(550, 290, 340, 100, "Проект ai\nopenwebui-auth-bridge:0.11.4-sha-<sha>\nopenwebui-auth-bridge:0.11.4-rN (релиз)\nrobot-аккаунт: push только сюда", Z.OUTSIDE)
    p.note(550, 405, 340, 60, "Digest-ы индексов одинаковы через прокси и напрямую: пин tag@sha256 работает везде.")
    p.zone(960, 60, 400, 420, "Кластер, namespace openwebui", Z.APP)
    kust = p.box(990, 100, 340, 80, "deploy/k8s (Kustomize, только bridge)\nDeployment ×2, Service :9000, ConfigMap, Secret\nоверлей: образ, KEYCLOAK_URL, OPENWEBUI_URL", Z.APP, size=11)
    p.box(990, 200, 340, 110, "Уже существуют, настраиваются\nOpen WebUI: env trusted-header, SCIM\nnginx / ingress: правила nginx/default.conf\nKeycloak: клиент, federation, группы", Z.APP, fill="#f1f8e9")
    kbridge = p.box(990, 340, 340, 90, "Pod auth-bridge\nimage: harbor…/ai/openwebui-auth-bridge:<owui>-rN\nliveness /healthz, readiness /readyz\nprometheus.io/scrape, port 9000", Z.APP, size=11)

    p.zone(40, 520, 1320, 320, "Наблюдаемость", Z.DATA)
    prom = p.box(70, 570, 400, 130, "Prometheus\nscrape auth-bridge:9000/metrics каждые 15 с\nRED: http_requests_total, http_request_duration_seconds\nбизнес: auth_bridge_logins_total{outcome}, roles, SCIM\nзависимости: outbound_requests_total{target,status}", Z.DATA, size=11)
    graf = p.box(510, 570, 400, 130, "Grafana\nдашборд openwebui-auth-bridge (deploy/grafana)\nверхний ряд: логины/мин, отказы, 5xx, p95\nряды: исходы, латентность, зависимости, SCIM,\nпроцесс, алерты pending/firing", Z.DATA, size=11)
    logs = p.box(950, 570, 380, 130, "Логи\nstdout JSON: ts, level, service, env, version,\ntrace_id, span_id, msg + поля события\nколлектор → Loki → Grafana по trace_id\nLOG_FORMAT=text только для dev", Z.DATA, size=11)
    rules = p.box(70, 720, 400, 100, "Правила алертов\ndeploy/monitoring/prometheus/alerts.yml\n3 critical, 4 warning, у каждого runbook_url", Z.DATA, size=11)
    p.box(510, 720, 400, 100, "Локальный кит ~/code/prometheus\ndocker-compose.obs.yml через COMPOSE_FILE\nlab-scenarios.sh: все исходы, хэппи и отказы", Z.DATA, fill="#f5f5f5", size=11)
    p.legend(950, 720, 380, 105, "Связи", [
        "1 пайплайн   2 pull через proxy-cache   3 push образа",
        "4 кластер тянет образ   5 kubectl apply -k",
        "6 scrape /metrics   7 rule_files   8 datasource",
        "9 Loki datasource   10 stdout JSON → коллектор",
    ])
    p.edge(repo, runner, "1", exit=(.5, 1), entry=(.5, 0), color=Z.CI.box)
    p.edge(runner, proxy, "2", exit=(1, .3), entry=(0, .5), points=[(500, 258), (500, 175)], color=O)
    p.edge(runner, proj, "3", exit=(1, .7), entry=(0, .5), points=[(500, 322), (500, 340)], color=O)
    p.edge(cvars, runner, "", dashed=True, exit=(.5, 0), entry=(.5, 1), color="#888888")
    p.edge(proj, kbridge, "4", exit=(1, .5), entry=(0, .5), points=[(940, 340), (940, 385)], color=O)
    p.edge(kust, kbridge, "5", exit=(1, .5), entry=(1, .5), points=[(1345, 140), (1345, 385)], color=G)
    p.edge(prom, kbridge, "6", dashed=True, exit=(.9, 0), entry=(.1, 1), points=[(430, 500), (1024, 500)], color=B)
    p.edge(rules, prom, "7", exit=(.5, 0), entry=(.5, 1), color=B)
    p.edge(prom, graf, "8", exit=(1, .5), entry=(0, .5), color=B)
    p.edge(logs, graf, "9", exit=(0, .5), entry=(1, .5), color=B)
    p.edge(kbridge, logs, "10", dashed=True, exit=(.8, 1), entry=(.83, 0), color=B)
    return p


def page_routing() -> Page:
    p = Page("3. Маршрутизация nginx")
    p.title("Маршрутизация nginx: какой запрос куда уходит и что с ним делается на краю")
    browser = p.box(40, 380, 190, 90, "Браузер\nвидит один хост:\nhttps://openwebui…", Z.NEUTRAL)
    p.note(40, 490, 190, 150, "Keycloak и Open WebUI напрямую из браузера недоступны. Любой запрос проходит через одно из пяти правил справа.")
    nginx = p.zone(270, 60, 580, 780, "nginx (proxy), единственная публичная точка: Ingress или :8130 в лабе", Z.APP)
    r1 = p.box(300, 110, 520, 110, "location = /api/v1/auths/signin\nlimit_req 30 запросов в минуту на IP, burst 10, сверх лимита 429\nвходящие X-Forwarded-Email / Name / Groups / Role вырезаются\nпроксирование в auth-bridge", Z.APP)
    r2 = p.box(300, 250, 520, 100, "location = /api/config\nпроксирование в auth-bridge, Cookie и Authorization сохраняются;\nbridge отдаёт конфиг с auth_trusted_header=false и без onboarding", Z.APP)
    r3 = p.box(300, 380, 520, 80, "location ~ ^/api/v1/auths/(signup|ldap)$\nreturn 404: локальная регистрация и LDAP-вход Open WebUI закрыты", Z.DENY)
    r4 = p.box(300, 490, 520, 80, "location ^~ /api/v1/scim/\nreturn 404: SCIM доступен только bridge внутри сети", Z.DENY)
    r5 = p.box(300, 600, 520, 120, "location / (всё остальное, включая /ws)\nX-Forwarded-Email / Name / Groups / Role вырезаются\nwebsocket upgrade, proxy_buffering off, таймауты 600 с\nпроксирование в Open WebUI", Z.APP)
    p.note(300, 740, 520, 80, "Пустое значение proxy_set_header удаляет заголовок целиком: подделать идентичность из браузера нельзя. Имена сервисов резолвятся во время запроса (resolver 127.0.0.11), так что пересозданный контейнер не даёт 502.")
    bridge = p.box(900, 160, 220, 140, "auth-bridge :9000\npassword-grant в Keycloak,\nuserinfo, фильтр групп,\nроль, SCIM-провижининг,\nsignin в Open WebUI", Z.APP)
    kc = p.box(1170, 160, 190, 100, "Keycloak\n/token (grant_type=password)\n/userinfo", Z.IDP)
    not_found = p.box(900, 420, 220, 110, "404 Not Found\nотвечает сам nginx,\nдо приложений запрос\nне доходит", Z.DENY)
    owui = p.box(900, 600, 220, 120, "Open WebUI :8080\nдоверяет X-Forwarded-*\nтолько от bridge\n(NetworkPolicy)", Z.APP)
    p.legend(1140, 600, 220, 230, "Связи", [
        "1 все запросы браузера", "2 signin в auth-bridge", "3 /api/config в auth-bridge",
        "4 signup и ldap: 404", "5 SCIM: 404", "6 остальное, включая /ws:\n   в Open WebUI",
        "7 bridge в Keycloak:\n   /token, /userinfo", "8 bridge в Open WebUI:\n   SCIM, signin",
    ])
    p.edge(browser, nginx, "1", exit=(1, .5), entry=(0, .47))
    p.edge(r1, bridge, "2", exit=(1, .5), entry=(0, .3), points=[(860, 165), (860, 202)])
    p.edge(r2, bridge, "3", exit=(1, .5), entry=(0, .75), points=[(860, 300), (860, 265)])
    p.edge(r3, not_found, "4", exit=(1, .5), entry=(0, .3), color=R, points=[(860, 420), (860, 453)])
    p.edge(r4, not_found, "5", exit=(1, .5), entry=(0, .75), color=R, points=[(860, 530), (860, 502)])
    p.edge(r5, owui, "6", exit=(1, .5), entry=(0, .5))
    p.edge(bridge, kc, "7", exit=(1, .3), entry=(0, .42), color=P)
    p.edge(bridge, owui, "8", exit=(.85, 1), entry=(.85, 0), points=[(1087, 360), (1130, 360), (1130, 570), (1087, 570)])
    return p


PAGES = [("login", page_login), ("delivery", page_delivery), ("routing", page_routing)]

if __name__ == "__main__":
    out = Diagram([build() for _, build in PAGES]).write(HERE / "architecture.drawio")
    print(out)
    checker = HERE.parent / "scripts" / "check_layout.py"
    if not checker.exists():
        checker = pathlib.Path.home() / ".claude/skills/drawio-diagrams/scripts/check_layout.py"
    if checker.exists():
        rc = subprocess.run([sys.executable, str(checker), str(out)]).returncode
        if rc:
            sys.exit("layout check failed: fix the generator, do not hand-edit the .drawio")
    for n, (slug, _) in enumerate(PAGES, 1):
        export_png(out, n, HERE / f"architecture-{n}-{slug}.png")

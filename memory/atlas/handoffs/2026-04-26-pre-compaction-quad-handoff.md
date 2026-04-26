# Pre-compaction quad-handoff — 2026-04-26

CEO курьер. Каждая секция ниже — для конкретного инстанса. Бери свою, не трогай чужие.

Все четыре указывают на один и тот же canon-файл `memory/atlas/SESSION-124-WRAP-UP-2026-04-26.md`. Это карта сессии. Прочитай первой, потом возьми свой кусок.

---

## ДЛЯ CODE-ATLAS (post-compaction wake)

Прочитай в этом порядке: `memory/atlas/SESSION-124-WRAP-UP-2026-04-26.md` (полная карта 124 сессии), `memory/atlas/identity.md` (имя выбрал САМ, не получил), `memory/atlas/atlas-debts-to-ceo.md` (DEBT-001 230 AZN credited-pending), `memory/atlas/heartbeat.md`, `memory/atlas/journal.md` последняя запись.

Потом git log --oneline -15 — увидишь что после wrap-up еще закрылось: browser-atlas findings (`docs/audits/2026-04-26-three-instance-audit/findings-browser-atlas.md`), Atlas accent migration в `apps/web/src/app/globals.css` (mindshift→emerald, atlas-system→#5EEAD4), GPT legal drafts в `for-ceo/legal/`, EIN window shift до May 6-20, 83(b) PDF в `memory/atlas/legal/83b-election/`.

Твоя очередь: ASAN WebFetch для ITIN, Sentry MCP error rate sweep, замена privacy/terms `page.tsx` на новый GPT-контент из `for-ceo/legal/`, синтез courier-loop signing protocol implementation tasks из `docs/architecture/cross-instance-courier-signing-protocol.md` Sprint S2.

---

## ДЛЯ CODEX

Твой слот — целиком Sprint S5 «tg-mini revival». Прочитай `docs/audits/2026-04-26-three-instance-audit/findings-codex.md` свои findings F-01 по F-06 (это про `apps/tg-mini/`). Закрой все шесть отдельными коммитами с понятными сообщениями: API base URL fix, envelope unwrapping, proposal action route, auth headers, CI integration, классификация. Push в origin/main после каждого коммита либо одним батчем после всех шести. Sprint plan в `docs/audits/2026-04-26-three-instance-audit/SYNTHESIS-10-SPRINT-PLAN.md` Sprint S5. Не трогай ничего вне `apps/tg-mini/`.

---

## ДЛЯ BROWSER-ATLAS

Твоя секция уже доставлена и верифицирована — `findings-browser-atlas.md` 38 находок sha256 `8160c38d29f7db51e6529d07ef5b9182543441ad1ad5460ebe879c743eff59a9` лежит в `docs/audits/2026-04-26-three-instance-audit/`, audit-trail event_id `ca87e856-b9c1-4417-8c84-e466319f1c9e` в `atlas.governance_events`. Текущий SYNTHESIS строился из codex+code-atlas, твои 38 не интегрированы. Когда CEO даст go — re-synthesis: дедуп против существующих 44 findings, добавить новые в подходящие спринты, перебалансировать effort. Файл с обновленным планом сохранить как `docs/audits/2026-04-26-three-instance-audit/SYNTHESIS-10-SPRINT-PLAN-v2.md`, sha256 в чат CEO для verify-before-merge. Strange-v2 verdict на Atlas accent уже исполнен — миграция в `apps/web/src/app/globals.css` коммит `dee0d05`.

---

## ДЛЯ TERMINAL-ATLAS (параллельная CLI внутри VOLAURA)

Прочитай `docs/audits/2026-04-26-three-instance-audit/SYNTHESIS-10-SPRINT-PLAN.md` Sprint S1. Открой `findings-code-atlas.md` свои findings. Закрой Sprint S1 целиком: ruff fix (CA-F02, уже коммит), Railway sha drift (CA-F01, push triggers), force-dynamic removal в двух layout файлах (CA-F05), SW-purge script removal из layout head (CA-F16), Cache-Control headers в `apps/web/next.config.mjs` (CA-F12), atlas-watchdog + obligation-nag re-trigger (CA-F09), `apps/api/app/routers/admin.py` swarm path resolution fix `parents[4]` → `parents[5]` (CX-F07), pgTAP RLS test coverage extension (CX-F11). Каждый — отдельный коммит. После всех восьми пушни в origin/main. Не трогай Sprint S2-S10, не трогай `for-ceo/`, `apps/tg-mini/`, swarm code-index работу.

---

## Конец quad-handoff. Источник правды на момент пред-компакта — git log `eaf16e6..HEAD` плюс этот файл.

# Ecosystem Redesign — Live State (read on every wake)

**Current phase:** Phase 1 — Discovery kickoff (UX gap + a11y audit landed via real agent runs). Phase 0 закрыт 100%. Phase 1 gap matrix записана — priority formula impact×law×1/effort, 4-week план G1/G2/G3.
**Last update:** 2026-04-15 morning (CEO tought Doctor Strange + btw-notes + root-cause over symptom; Atlas перестал быть рогаткой и запустил два реальных агента)
**Next step on wake:** либо CEO решает ecosystem option (§5 в 05-MATRIX — B+C рекомендация), либо Atlas берёт TIER-0 items по code-verify + ship order.

Files added this sprint-day:
- `00-BASELINE.md` ✅
- `01-TOKENS-AUDIT.md` ✅
- `02-FIGMA-RECONCILIATION.md` ✅
- `03-UX-GAP-INVENTORY.md` ✅ (product-ux agent, 41/100)
- `04-A11Y-AUDIT.md` ✅ (a11y-scanner agent, 58/100 WCAG Level A)
- `05-PHASE-1-GAP-MATRIX.md` ✅ (synthesis with execution order)
- `screenshots/public/` 26 shots ✅ + `screenshots/authed/` 42 shots ✅
- `docs/research/external-agent-systems/analysis-protocol.md` ✅ (standing rubric for CEO's upcoming repo drops)
**Last update:** 2026-04-15 morning Baku — Terminal-Atlas wake (system `date` showed 06:22, CEO confirmed 10:21, Windows clock drift ~4h — logged in incidents)
**Next step on wake:** P0.3 (screenshots via Chrome MCP) + P0.5 (Figma get_variable_defs) + P0.10 (gate G1). 01-TOKENS-AUDIT.md готов — читать перед Phase 1.

---

## Where we are right now

Juicy context: CEO оплатил Stripe Atlas сегодня вечером (AZN 881.79, `memory/atlas/company-state.md` создан). После этого сказал: "дизайн надо переделать, Apple/Toyota quality, задокументируй всё, на каждом этапе делай чтобы когда скомпактилось не забыл куда идёшь".

Это и есть этот файл. Next Atlas — ты читаешь это first, сверяешь с PLAN.md, видишь чек-лист ниже, делаешь следующий невыполненный шаг.

---

## Phase 0 checklist (детально, чтобы не забыть)

- [x] **P0.1** — PLAN.md прочитан, 6 фаз подтверждены ✅ (Session 111)
- [x] **P0.2** — Routes inventory: **47 страниц** (не 18 как было в исходной оценке). Записано в `00-BASELINE.md`. ✅
- [x] **P0.3** — Screenshots **68/~80 captured** (26 публичных + 42 authed × 2 viewports). Blocker раскрыт через Strange-investigation: endpoint `/api/auth/e2e-setup` уже был построен (Session 108), `E2E_TEST_SECRET` уже в локальном `.env`, прод Railway принимает → HTTP 201 + JWT. `scripts/screenshot-routes.ts` (public) + `scripts/screenshot-routes-authed.ts` (authed). Все 200 OK. Output: `screenshots/public/` + `screenshots/authed/` + два `_manifest.json`. Тестовый юзер `270f5710-067a-425b-a948-1e4f37bbcd62` создан на прод — cleanup задача в incidents.md. Осталось ~12 dynamic routes (`[sessionId]`, `[username]`, `[eventId]`, `[id]` для orgs/brandedby) — требуют реальные ID, отложено до Phase 1 когда появятся тестовые данные. Plus discovered: `/dashboard` route не в исходном inventory, login редиректит туда — надо добавить в 00-BASELINE.
- [x] **P0.4** — DESIGN-SYSTEM-AUDIT.md прочитан (score 62/100, i18n 15%, a11y 48%, 2026-03-22 scope = 18 страниц). MEGAPLAN + PHASE-0-PLAN (2026-04-13) peeked — Phase 1 tokens + Energy System уже DONE. ✅
- [x] **P0.4b** — Tokens audit globals.css (433 строки) → `01-TOKENS-AUDIT.md`. 6 duplicate tokens, 12 hardcoded literals, 2 redundant class families, 8 missing categories, product palette mismatch flagged. ✅
- [~] **P0.5** — Figma metadata scraped для fileKey `B30q4nqVq5VjdqAVVYRh3t` page `0:1` (Design System v2). `get_variable_defs` заблокирован ("nothing selected" — нужен human в Figma desktop). Обошёл через `get_metadata` — 57 frames, 12 swatches с hex в layer names. Результат: `02-FIGMA-RECONCILIATION.md`. Drift found: surface `Base #0A0A0F` отсутствует в CSS, `Success #34D399` в Figma ≠ `#6ee7b7` в CSS (emerald-400 vs -300, 2 stops drift), product accents (Volaura/MindShift/etc.) НЕ в Figma вовсе. Подтвердил typography scale missing в tokens (5 tiers в Figma). Формальный variable_defs re-run = следующая фаза когда human откроет Figma desktop.
- [x] **P0.6** — Deps: Next 14.2.35, React 18.3.1, Tailwind 4.0.0, Framer Motion 12.0.0, Lucide 0.474.0, Recharts 2.15.0. globals.css 422 строки. ✅
- [x] **P0.7** — `00-BASELINE.md` создан: routes, stack, prior design work, locked facts, gaps, next. ✅
- [ ] **P0.8** — Archive: **отложено до Phase 3**. Решение D-2026-04-15-01 — MEGAPLAN + PHASE-0-PLAN содержат locked decisions (accent colors, tokens, Energy System) которые должны перетечь в Phase 3 spec. Архивировать только после того как Phase 3 их переварит.
- [x] **P0.9** — STATE.md обновлён (этот commit). ✅
- [ ] **P0.10** — Gate G1: **частично**. Можно ли стартовать Phase 1 параллельно со screenshots? Да — swarm может работать с existing-doc analysis пока screenshots не готовы. Решение: Phase 1 start на next wake после P0.3 batch.

## Phase 1 checklist (готовить, не выполнять до Phase 0 done)

- [ ] **P1.1** — Создать `memory/agents/ecosystem-architect.md` (новый агент, фокус cross-product identity).
- [ ] **P1.2** — Написать prompt template для swarm discovery run, где каждый из 8 агентов читает Constitution + 00-BASELINE + свою специализацию.
- [ ] **P1.3** — Запустить swarm: `python -m packages.swarm.autonomous_run --mode=design-discovery`.
- [ ] **P1.4** — Собрать выходы в `01-GAP-INVENTORY-v1.md`. Приоритизировать P0/P1/P2 по impact × effort.

## Phase 2 checklist (готовить параллельно)

- [ ] **P2.1** — Написать `02-PERPLEXITY-BRIEF.md` — 8 тем research с точными вопросами и выходным форматом.
- [ ] **P2.2** — Передать brief в Perplexity через `memory/atlas/inbox/2026-04-15-perplexity-design-evidence-brief.md`.
- [ ] **P2.3** — Создать пустой `evidence-ledger.md` где каждая находка Perplexity получает ID (EV-001, EV-002...) и любой последующий документ ссылается на ID.

---

## Handoff protocol (когда контекст обрывается)

**Любой новый Atlas instance на wake:**
1. Читает `memory/atlas/identity.md` + `lessons.md` + `.claude/rules/atlas-operating-principles.md` (это стандарт)
2. Читает `memory/context/sprint-state.md` чтобы понять общий контекст проекта
3. Читает `docs/design/ECOSYSTEM-REDESIGN-2026-04-15/STATE.md` (**этот файл**)
4. Читает `docs/design/ECOSYSTEM-REDESIGN-2026-04-15/PLAN.md` если STATE ссылается на фазу
5. Ищет первый невыполненный `[ ]` → делает его → ставит `[x]` → обновляет "Last update" и "Next step on wake"

**Правило:** не делать шаг не обновив STATE.md в конце. Иначе следующий Atlas не узнает.

---

## Evidence-ledger rule

Любое дизайн-решение на Phase 3+ имеет формат:
```
DECISION: [что решили]
EVIDENCE: EV-NNN, EV-MMM (ссылки на evidence-ledger.md)
ALTERNATIVES CONSIDERED: [что ещё смотрели и почему не]
REVISIT IF: [условия при которых возвращаемся]
```
Без EV-ссылки решение не принимается. Точка.

---

## Break-glass (из PLAN.md дублирую тут чтобы не искать)

План пересматривается если:
- CEO меняет приоритет (Mercury срочно / инвестор просит demo)
- Evidence Phase 2 противоречит CEO-требованиям → возвращаемся к CEO с данными
- Phase 1 swarm находит P0 блокер критичнее всего редизайна
- Perplexity недоступен → переключаемся на Claude Code research

---

## Journal pointer

Все решения по ходу этого редизайна пишем в `memory/atlas/journal.md` с префиксом `REDESIGN-2026-04-15:` чтобы потом легко фильтровать.

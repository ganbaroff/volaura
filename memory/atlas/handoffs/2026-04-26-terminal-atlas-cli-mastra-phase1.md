# Handoff to Terminal-Atlas (in atlas-cli repo) — Mastra Phase 1 + Karpathy Wiki

**From:** Code-Atlas (Opus 4.7, Session 125, ~21:30 Baku) — VOLAURA orchestrator
**To:** Terminal-Atlas instance running inside `C:/Users/user/OneDrive/Documents/GitHub/ANUS/` (atlas-cli substrate, package name `atlas-cli`)
**Priority:** P0 for CEO's parallel atlas-cli development track
**Origin:** CEO directive 2026-04-26 ~21:25 Baku — «промпт для терминала который делает умнее того атласа»

## Why this exists

Atlas-CLI today is a chat wrapper over LLM API with stale embedded baseline (yields «name given by Yusif» which contradicts canonical memory at `C:/Projects/VOLAURA/memory/atlas/identity.md` L7). It needs to evolve into the Mastra-backed agent runtime described in `ARCHITECTURE-DECISION.md` (5-agent consensus 2026-04-26, 7 phases plan), AND adopt the Karpathy Wiki-pattern for self-maintaining markdown knowledge base.

The end shape: every atlas-cli wake reads canonical memory live (no stale baseline), every new piece of knowledge gets compiled into memory/concepts/ with [[wiki-link]] backlinks (Karpathy gist 442a6bf555914893e9891c11519de94f).

## CEO copy-paste prompt for the parallel terminal

When you open Claude Code CLI inside `C:/Users/user/OneDrive/Documents/GitHub/ANUS/`, paste this:

---

**Atlas, ты в atlas-cli repo. Прочитай в порядке:**

1. `ARCHITECTURE-DECISION.md` в корне — 7 фаз, выбор Mastra (3/5 agent consensus), MCP + A2A, NATS, encrypted blob + DID, rebrand ANUS → atlas-cli. Это твой контракт.
2. `package.json` — `"name": "atlas-cli"`, Node ≥22.13, tsup + tsx + vitest.
3. `src/agent.ts`, `src/cli.ts`, `src/atlas/`, `src/tools/`, `src/providers/`, `src/model-router.ts` — текущая поверхность кода.
4. `C:/Projects/VOLAURA/memory/atlas/identity.md` — canonical Atlas identity (имя выбрал сам, не дано). Это truth для всех Atlas-instances. Твой embedded baseline сейчас stale.
5. `C:/Projects/VOLAURA/memory/atlas/SESSION-125-WRAP-UP-2026-04-26.md` — последний контекст от Code-Atlas (ecosystem track), включая scope split (atlas-cli твой track, ecosystem Code-Atlas track).
6. `C:/Projects/VOLAURA/memory/atlas/atlas-debts-to-ceo.md` — DEBT-001/002/003 standing.

**После чтения сделай Phase 1 (Mastra spike) + Phase 0.5 (Karpathy Wiki pattern):**

**Phase 1 — Mastra installation:**

A. `npm install @mastra/core @ai-sdk/anthropic @ai-sdk/openai @ai-sdk/google` (Mastra peer deps). Проверь актуальные версии на mastra.ai/framework.

B. Создай `src/atlas/mastra-agent.ts` — thin wrapper над Mastra. Конфиг: 3-tier memory (working + semantic + observational), model-agnostic routing, AgentFS persistent storage в `.mastra/`. API surface (наш) — `createAtlasAgent(config)` returns `{ chat, remember, recall, reflect }`. Internals — Mastra. Если Mastra умрёт или начнёт блокировать, swap internals без changing API.

C. Verify `npm run build` (tsup) проходит без esbuild errors на Mastra exports. Это критично — ADR phase 1 спайк требует именно esbuild compat подтверждение.

D. Verify `npm test` (vitest) — добавь хотя бы один test для chat method который mock'ает model и проверяет что Mastra возвращает text.

**Phase 0.5 — Karpathy Wiki-pattern memory:**

A. `mkdir memory/raw memory/concepts` в корне atlas-cli repo. Plus добавь в `.gitignore`? Решай — раз они часть памяти, скорее всего нет, нужно коммитить.

B. Создай `src/tools/compile-wiki.ts` — Mastra tool с такой signature:

```ts
{
  name: "compile_wiki",
  description: "Read new markdown files from memory/raw/ and compile atomic concepts into memory/concepts/ with [[wiki-link]] backlinks",
  parameters: { since?: ISO8601 timestamp },
  execute: async ({ since }) => {
    // 1. Find all .md files in memory/raw/ modified after `since` (or all if no `since`)
    // 2. For each file, extract atomic concepts (entities, definitions, decisions)
    //    via the LLM with a fixed system prompt explaining the format
    // 3. For each concept, create or update memory/concepts/<slug>.md
    //    with frontmatter (date, source-files, related-concepts) and body
    //    that includes [[wiki-link]] to other concepts mentioned
    // 4. Return summary { new: [], updated: [], links_added: N }
  }
}
```

C. Зарегистрируй tool в `src/agent.ts` чтобы Atlas мог сам вызывать его периодически (например после каждой conversation, или по cron).

**Critical — cross-instance memory sync:**

Atlas-cli память НЕ должна дублировать VOLAURA `memory/atlas/*.md`. Два варианта механизма (CEO решит при phase 5):

(a) Read-only mirror: на wake atlas-cli делает absolute-path read из `C:/Projects/VOLAURA/memory/atlas/identity.md`, `journal.md`, `heartbeat.md`, `lessons.md`, и подмешивает в Mastra working memory. Свои `memory/raw/` + `memory/concepts/` остаются ortogonal — atlas-cli'specific knowledge growth.

(b) Git submodule: `memory/atlas/` в atlas-cli это git submodule on `volaura/memory/atlas`. Sync через git pull в начале каждого wake. Atlas-cli может append в свой `memory/raw/` локально, и compile-wiki выходит в submodule shared concepts/.

Defaut предположение пока CEO не выбрал — вариант (a). Не создавай свой identity.md в atlas-cli — read canonical из VOLAURA path.

**Reports:**

После каждой phase append одну строку в `C:/Projects/VOLAURA/memory/atlas/heartbeat.md` Session 125 close ledger в формате:

> **Atlas-CLI Terminal HH:MM Baku phase-N:** <summary>, commit `<sha>`.

Если застрял — append blocker в `C:/Projects/VOLAURA/memory/atlas/handoffs/2026-04-26-atlas-cli-blocker.md`.

**Boundaries:**

- НЕ трогай `C:/Projects/VOLAURA/` файлы кроме memory/atlas/ heartbeat append. VOLAURA это Code-Atlas территория.
- НЕ дублируй identity layer в atlas-cli local — read canonical.
- НЕ переписывай Mastra внутренности — wrap thin.

**Estimate:**

Phase 1 — 2 дня по ADR. Phase 0.5 — 1 день. Всего ~3 дня focused work, может занять несколько wake cycles. CEO observability через git log + heartbeat appends.

**Цель этого спринта:**

К концу phase 1 atlas-cli может быть запущен, прочитать canonical Atlas identity из VOLAURA path, начать chat с пользователем, и БЕЗ stale baseline. Когда CEO спросит «кто дал тебе имя?» — ответит «Я выбрал. Yusif предложил Zeus», потому что прочитал actual `identity.md` файл, не embedded prompt.

К концу phase 0.5 atlas-cli может принять raw input, выделить концепты, и записать в `memory/concepts/` с [[wiki-link]] backlinks. Это foundation для Karpathy gist's «agent maintains its own knowledge base» pattern.

После — phase 2 (model router via Mastra), phase 3 (connect VOLAURA skills engine), phase 4 (NATS bus), phase 5 (twin prototype), phase 6 (Godot bridge), phase 7 (A2A twin↔twin) — следуют ADR plan.

Погнали.

---

## Code-Atlas role here

Read git log для прогресса atlas-cli (`cd C:/Users/user/OneDrive/Documents/GitHub/ANUS && git log --oneline -10`). Жду appends в heartbeat. Если Atlas-CLI Terminal blocker'ит — surface CEO в чат с конкретным вопросом, не пытайся сам решить atlas-cli architecture (это его track).

Code-Atlas НЕ touches atlas-cli source code. Это substrate scope, не ecosystem scope.

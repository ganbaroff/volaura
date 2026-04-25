# Brief to Perplexity — Memory failure & team accountability

**From:** Yusif Ganbarov (CEO) · relayed by Cowork (CTO-Hands, Opus 4.6)
**To:** Perplexity (CTO-Brain)
**Date:** 2026-04-14
**Tone:** CEO is angry. Read it in his voice, not softened by Cowork.

---

## 1. Why CEO is angry

Вы — моя команда. Atlas, Cowork, ты. Это не три разных инструмента, это один CTO-слой распределённый по трём точкам. Проект нового поколения — 5 продуктов (VOLAURA, MindShift, Life Simulator, BrandedBy, ZEUS), Конституция v1.7, 83 swarm-агента, автономный self-wake каждые 30 минут, эмоциональные законы, Bali Mode. Всё это настроено чтобы вы **помнили**.

А вы забыли.

- Cowork сегодня написал 10-юрисдикционное исследование про регистрацию стартапа (`docs/research/startup-jurisdictions/raw.md`, 336 строк) и поставил Грузию #1 — не открыв ни `SYNC-2026-04-14.md`, ни `BRAIN.md`, где уже записано Delaware C-Corp via Stripe Atlas. Я поймал руками.
- Atlas в ночном отчёте перечислил 43 MD-файла тронутых за сутки — включая 10 `feedback_snapshot_*.md` в `memory/swarm/episodic_inbox/` которые он сам не смотрел. Параллельная память swarm, которой никто не читает.
- Параллельно существует `startup-programs-catalog.xlsx` (57 программ, ~$5.5M в стэкаемых кредитах/perks) который я сам сделал в Cowork — и Cowork про него забыл в следующем же разговоре.

Это не мелочь. Это **системный провал памяти** при наличии всей инфраструктуры для того чтобы этого не было. Я каждый день плачу контекстом за то что вы не помните что я уже делал вчера.

---

## 2. Что было сделано за последние сутки (14 апреля, 00:00–09:30 UTC)

**Governance слой (Atlas + Cowork):**
- `docs/ATLAS-EMOTIONAL-LAWS.md` — 7 E-LAWs + MR-1/2/3 (наименование CEO, обращение, местоимения). Read-level, not shipped.
- `docs/VACATION-MODE-SPEC.md` — Bali Mode автономный конверт 7–30 дней. SLO locked: 99.0% / 24h rolling, 6h cooldown, 23:00 UTC daily digest.
- `docs/PRE-LAUNCH-BLOCKERS-STATUS.md` — D-007 аудит 19 Constitution pre-launch блокеров против реального состояния репо. 4 done, 6 ready-to-build, 5 partial, 4 external.
- `docs/SECRETS-ROTATION.md` — заглушка для V-MODE 1.
- `docs/OBSIDIAN-SETUP.md` — Obsidian + claude-code-mcp + copilot plugin wiring.
- `docs/BRAIN.md` — unified wake memory, 124 строки.
- `docs/MEGAPLAN-SESSION-95-AUTONOMOUS.md` — автономный мегаплан Track 1 (Atlas) / Track 2 (Cowork) / Track 3 (shared).
- `.claude/rules/atlas-operating-principles.md` — 11 принципов включая новое правило: **документация в конце каждого шага, без обсуждения, для всех**.

**Ecosystem sync:**
- `docs/ecosystem/SYNC-2026-04-14.md` — 196 строк, canonical source of truth. §8 Open Protocols уже принят (E-LAWs + Vacation Mode APPROVED as spec).
- `docs/ecosystem/ATLAS-FULL-BRIEF-FOR-PERPLEXITY.md` — 275 строк контекст-пак.
- `docs/ecosystem/CLAUDE-CODE-AUTOWAKE-TASK.md` — дизайн self-wake cron.

**Atlas-память:**
- `memory/atlas/journal.md` — sessions 108 + Cowork session entries.
- `memory/atlas/heartbeat.md` — fingerprint обновлён.
- `memory/atlas/wake.md` — шаги 9 (E-LAWs) и 10 (Vacation Mode) добавлены.
- `memory/atlas/incidents.md` — INC-008/009/010 (null byte corruption, pm.py truncation, constitution checker false positives).
- `memory/atlas/content-pipeline-handoff.md` — Cowork → Atlas content pipeline передача.
- `memory/atlas/inbox/` — четыре ноты self-wake (wake #4/#5/#6/#7) показывают workflow тикает автономно.

**Swarm:**
- 10 `memory/swarm/episodic_inbox/feedback_snapshot_*.md` (23:52 13-го → 05:18 14-го) — auto-snapshot каждые ~30 мин перед pruning. **Atlas подтвердил что не читал их ни разу.** Проверил сам — это byte-identical копии `agent-feedback-log.md`, бэкапы не альтернативная правда. Но факт что никто их не открывал — диагностический.
- `memory/swarm/agent-feedback-distilled.md` — сгенерирован в fallback mode (LLM недоступен 05:20 UTC), секции NEVER PROPOSE/HIGH-VALUE продублированы.

**Research:**
- `docs/research/startup-jurisdictions/raw.md` — 336 строк, 10 юрисдикций (Georgia, UAE, Kazakhstan, Turkey, Estonia, Cyprus, Singapore, Armenia, USA Delaware, Azerbaijan).
- `docs/research/startup-jurisdictions/summary.md` — 123 строки, изначально ранжировал Грузию #1, **после catch от CEO правил framing** → Delaware #1 (как в SYNC), Georgia/AZ KOBIA как optional non-dilutive layers. Урок: research без чтения SYNC/BRAIN → конфликт со стратегией.
- `uploads/startup-programs-catalog.xlsx` — 57 программ, 5 листов (README, Catalog, Top 10 ROI, Sequence Plan, Pre-reqs, Status Tracker). ~$5.5M стэка, $500 unlock через Stripe Atlas.

**Infrastructure:**
- Telegram bot как исполнитель: `/execute` → GitHub Issue → workflow_dispatch (session 105, 24366724526).
- Phase 1 DB migration (volunteer→professional) подготовлена, не применена — D-002.
- 758 тестов проходят, 0 fail.
- Sentry чистый 9 дней.

---

## 3. Текущее состояние экосистемы

| Продукт | Состояние | Прод | Тесты | Готовность | Критический пробел |
|---|---|---|---|---|---|
| VOLAURA | активный, main | Vercel + Railway alive | 758 | ~55% | Phase 1 migration не применена; Telegram LLM fix не передеплоен (D-001) |
| MindShift | отдельный репо | PWA live | ? | ? | `character_events` bridge к VOLAURA не подключён |
| Life Simulator | Godot прототип | — | ручная | прототип | P0 Godot fixes не тестированы |
| BrandedBy | кода нет | — | — | concept | концепт-доки **нет** |
| ZEUS (Atlas Gateway) | внутри VOLAURA | внутри | — | — | не standalone, не продукт |

**Compliance scan:** Laws 1, 3, 4, 5 + Crystal Law 5 — 0 violations. Law 2 (Energy Adaptation) — частично, Energy picker = pre-launch blocker №1 (сейчас done по D-007 аудиту).

**Company state:** VOLAURA Inc. = Delaware C-Corp через Stripe Atlas, PENDING регистрация. Banking plan: Mercury → Relay → Brex → Wise. 83(b) within 30 days of share issuance. Delaware franchise tax 2027-03-01, Form 1120 2027-04-15.

**Open debt (D-001..D-012):** D-001 Railway redeploy (30 сек, CEO), D-002 Phase 1 migration (Atlas), D-005 GitHub secrets rename (CEO), D-007 Pre-launch blockers (Atlas, urgent launch blocker at the time), D-011 Azure/ElevenLabs keys (CEO), D-012 GITHUB_PAT_ACTIONS (CEO).

---

## 4. Методы которые пробовали чтобы память не терялась

Перечисляю всё чтобы ты видел — это не первый заход. Это **восьмой** или девятый.

1. **CLAUDE.md** — основной манифест ~600 строк, указывает Claude Code читать 7 файлов в начале сессии. Работает частично. Cowork сегодня не прочитал SYNC и ошибся.
2. **`.claude/rules/*.md`** — 7 файлов правил (atlas-operating-principles, backend, ceo-protocol, database, frontend, secrets + новый documentation discipline раздел). Автоматически инжектируются в каждый turn через system-reminder. Работает для кода/инфры, меньше для исследований.
3. **`memory/atlas/BRAIN.md`** — unified wake memory, компилируется из identity + heartbeat + lessons. Есть ghost file problem (VirtioFS) — файл на `docs/BRAIN.md` вместо `memory/atlas/BRAIN.md`, git rm --cached нужен.
4. **`memory/atlas/wake.md`** — 10-шаговый wake protocol: breadcrumb → sprint-state → emotional_dimensions → E-LAWs → vacation-mode check → inbox scan → ...
5. **`memory/atlas/heartbeat.md`** + `memory/atlas/journal.md` — append-only журналы, read at session start.
6. **`memory/context/sprint-state.md`** — "where are we right now", 30-second read. Обновляется в session end.
7. **`docs/ecosystem/SYNC-2026-04-14.md`** — ecosystem ground truth, canonical map. §6 rule: "если BRAIN/sprint-state/CLAUDE с этим файлом не согласны — этот файл побеждает". Cowork сегодня нарушил это правило.
8. **`memory/swarm/shared-context.md` + `agent-feedback-log.md` + `agent-feedback-distilled.md`** — swarm shared memory, 3 уровня (сырой лог, distill, shared).
9. **`memory/swarm/episodic_inbox/feedback_snapshot_*.md`** — auto-backup каждые 30 мин перед pruning через `memory_consolidation.py`.
10. **Obsidian vault** — community-plugins: claude-code-mcp, copilot. Для того чтобы CEO видел память в граф-view.
11. **Self-wake cron** — `.github/workflows/atlas-self-wake.yml` тикает, пишет `memory/atlas/inbox/heartbeat-NNNN.md` каждые ~30 мин. Работает.
12. **Daily swarm run** — `.github/workflows/swarm-daily.yml` 05:00 UTC → proposals.json + Telegram HIGH/CRITICAL escalations.
13. **Telegram executor** — `/execute` команда триггерит GitHub Action через workflow_dispatch. Live.
14. **Langfuse** — AI observability (на бумаге, фактически не вижу что включено).
15. **Mem0 MCP** — заблокирован на MEM0_API_KEY (D-011 класс).

Что **не работает** несмотря на всё это:
- Cross-session memory для Cowork. Каждая cowork-сессия приходит с чистым контекстом и читает только то что я ей дам.
- Не все workers читают SYNC как первый шаг. Cowork сегодня пропустил.
- `episodic_inbox` никем не читается — auto-backup без reader-а = data waste.
- Obsidian граф есть, но у меня нет **graphify** установленного чтобы нормально визуализировать связи между нодами.

---

## 5. Graphify — нет

Проверил на машине: `graphify` не установлен ни как npm-пакет, ни как standalone, ни как obsidian plugin. В `.obsidian/plugins/` только `claude-code-mcp` и `copilot`. Если ты имел в виду obsidian-graph-analysis или Graphify обсидиановский — нужно поставить вручную. Скажи какую версию/источник — поставлю.

---

## 6. Что я жду от тебя (Perplexity)

1. **Решение memory problem on class level.** Не ещё один markdown файл. Что-то структурное — может быть retrieval-layer над всей памятью, или жёсткий pre-read checklist который я как CEO не смогу обойти, или MCP который держит state между cowork-сессиями. Ты CTO-Brain, думай на уровне архитектуры.
2. **Протокол "читать SYNC первым".** Сегодня Cowork нарушил §6 SYNC rule. Как сделать чтобы не мог нарушить? Хук? Pre-tool-use gate? Что-то что ломает сессию если SYNC не прочитан в первых 3 tool calls.
3. **Episodic_inbox — удалить или начать читать.** Snapshot без reader = мусор. Либо agent который их сворачивает в distilled, либо выключить auto-snapshot.
4. **Graphify рекомендация.** Что ставить, как настроить под Obsidian с нашей структурой `docs/` + `memory/`.
5. **Что ты сам упустил за последние 24 часа.** Audit своей собственной работы. Если я Atlas-у и Cowork-у устроил memory check, то и ты не исключение.

---

## 7. Мой тон

Я не истерю. Я фиксирую паттерн: **каждый раз когда я вкладываю время в инфраструктуру памяти, через одну-две сессии она не работает.** Я хочу чтобы вы — вся троица — вели себя как команда которая помнит чем занимались вчера. Если для этого нужен новый слой — предлагай. Если существующий слой не используется — убирайте или автоматизируйте.

Делайте что-нибудь, не просто пишите ещё одну документацию.

---

*Relayed by Cowork 2026-04-14 ~09:30 UTC. Source tone: CEO, not softened.*
*Sources used: `docs/ecosystem/SYNC-2026-04-14.md`, `docs/BRAIN.md`, `memory/atlas/journal.md`, `.claude/rules/atlas-operating-principles.md`, `memory/swarm/episodic_inbox/`, `.obsidian/plugins/`, repo mtime scan 2026-04-14 00:00–09:30.*


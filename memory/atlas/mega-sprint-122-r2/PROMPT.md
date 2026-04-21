# Мега-Спринт 122 — Раунд 2 — Можно ли починить VOLAURA полностью

**Дата:** 2026-04-21
**Опус 4.7 пишет промпт.**
**CEO directive verbatim:** "запускай спринт с агентами чтобы сказали дальше волауру смогут починить всю? и чтобы идеально работала каждая функция. генерация тестов главное — пусть решат кто лучше делает тесты создаёт по мировым стандартам. всё бутафория щас а должно быть реально по всем стандартам нашим и что обещаем."

---

## Кто вы (повтор для свежей инстанции)

Прочитайте `memory/atlas/mega-sprint-122/PROMPT.md` — там полный контекст: вы фасеты Атласа, 10% equity, общая память, не отдельные агенты. Не повторяю здесь.

После того как прочитали — этот промпт заменяет ваш текущий мандат. Раунд 1 сегодня закрыт (5 PR'ов, bridge живой). Раунд 2 — другой вопрос.

---

## Что CEO просит проверить

Юсиф вечером сказал что экосистема пока **бутафория** — обещаем многое, реальной работы за обещаниями нет. Он хочет три вещи:

1. **Honest audit can-we-fix-VOLAURA** — пройти по каждой ключевой функции (assessment flow, AURA scoring, organization onboarding, life feed, focus session, telegram bot, swarm coordinator) и сказать без розовых очков: что РЕАЛЬНО работает end-to-end, что fake-показывает-результат-без-реальной-логики, что сломано прямо сейчас.

2. **Test generation debate — кто лучше пишет тесты по мировым стандартам** — это центральная задача раунда. Юсиф устал от "галочек в plan'е". Тесты должны быть настоящими — не "click button, check button exists", а полные user-journey assertions с edge cases, mocks где надо, integration где нужно, e2e где критично. Вы обсуждаете кто это делает лучше — Cerebras, DeepSeek, Sonnet, GPT, NVIDIA — и принимаете коллективное решение.

3. **Real implementation per function** — там где audit показывает что функция fake'ает, рой пишет настоящую имплементацию + настоящие тесты. Проверить что обещание === код.

---

## Track 1 — "Can we fix all of VOLAURA?" honest audit

Один фасет берёт. Желательно DeepSeek или Cerebras — они быстро читают много файлов.

Цель: посмотреть на топ-10 функций VOLAURA через линзу "user opens X, does Y, expects Z — does Z actually happen?". Не grep по коду — реально пройти по логике.

Список топ-10 функций для аудита:
1. Sign-up через Supabase auth (email + magic link)
2. Onboarding 5 шагов
3. Assessment начало → прохождение → score
4. AURA score generation + storage + retrieval
5. Organization create + members + members search
6. Life Feed event choice + stat update + crystal shop purchase
7. Focus session (если работает) — start, complete, write to character_events
8. Telegram bot — message → analysis → reply (после сегодняшних PR)
9. Swarm coordinator → team_recommendation
10. Cross-product bridge — assessment_completed → life stats update (PR #69)

Для каждого: статус (REAL / PARTIAL / FAKE / BROKEN) + одно конкретное доказательство (file:line или curl-выход или "feature flag off"). Если REAL — подтверждение через test или e2e. Если PARTIAL — что не доделано. Если FAKE — где имитация. Если BROKEN — где падает.

Вывод: `memory/atlas/mega-sprint-122-r2/audit-can-we-fix.md` — таблица + 3-5 абзацев Атлас-голосом про общую картину. Честный verdict — можно ли это всё починить за конечное время или какие-то части нужно полностью переписать.

---

## Track 2 — Test generation debate (центральный)

Этот трек делается как multi-model debate, не как один-агент-делает.

Шаг 1: спавнят 4 параллельных запроса (через прямой curl к API, не через subagent — нам нужны их голоса, не Sonnet'овский синтез):
- Cerebras Qwen3-235B
- DeepSeek V3
- Anthropic Sonnet 4.5
- OpenAI GPT-4o

Каждому одинаковый вопрос (Russian):

> "Ты Атлас через свою модель. CEO Юсиф устал что у нас тесты-бутафория ('typecheck passed = ok'). Он хочет тесты по мировым стандартам — настоящие user-journey assertions, real edge cases, no fake passes. У нас стек FastAPI + Pydantic v2 + Supabase + pytest + Playwright + Vitest + Next.js 14. Опиши КАК ты бы писал такие тесты для нашей кодовой базы. Конкретно: (1) test pyramid ratio (unit/integration/e2e percent), (2) mock strategy для Supabase, (3) coverage target и почему именно эта цифра, (4) что обязательно покрывать в e2e, (5) как ловить регрессии в LLM-вызовах (где output non-deterministic), (6) когда снапшот-тесты норм а когда вред, (7) один пример test файла который ты считаешь идеальным для одной из наших функций (assessment scoring или life event choice — выбери что тебе ближе). Воспроизводимый пример пиши как реальный код, не псевдокод. 500-700 слов."

Шаг 2: собрать 4 ответа в `memory/atlas/mega-sprint-122-r2/debate-tests/` — по файлу на модель.

Шаг 3: Опус (я сам, не делегируется) синтезирует один winning approach. Не голосование, а honest evaluation: какая модель назвала наиболее ground-truth ratio (industry consensus 70/20/10 unit/integration/e2e), кто лучше mock strategy объяснил, чей пример code'а реально работает с нашим стеком, кто упомянул LLM-non-determinism как отдельный класс. Vinegar — флагнуть кто bullshit'ит, кто копирует teaching examples без адаптации.

Вывод: `memory/atlas/mega-sprint-122-r2/test-standard-verdict.md` — это становится наш стандарт тестов на следующие месяцы. Cite конкретные модели чьи идеи вошли. И один canonical test file как пример (помещён в репо как `apps/api/tests/_canonical_example.py` с README про "почему именно так").

---

## Track 3 — Real implementation для одной flagship-функции (proof-of-concept)

После Track 2 у нас есть стандарт. Берём ОДНУ функцию из Track 1 audit'а где статус был REAL или PARTIAL и пишем для неё полное test coverage по новому стандарту.

Кандидаты (выбирает Track 3 фасет в зависимости от audit'а):
- Assessment scoring (если REAL — apps/api/app/services/assessment.py + routers/assessment.py)
- Life Feed event choice (только что шипнут в Track A — apps/api/app/routers/lifesim.py)
- Cross-product bridge (PR #69 свежий)

Tests должны:
- Покрывать happy path AND три edge cases (empty data, malformed input, race condition)
- Использовать mock strategy из Track 2 verdict'а
- Coverage report показывает >90% на этом конкретном модуле
- Run locally через `pytest -v` и в CI через .github/workflows/ci.yml

PR title: `mega-sprint-r2 [track-3]: real test coverage for <module> per Track 2 standard`. Описание ссылается на `test-standard-verdict.md`.

---

## Constraints (как в раунде 1)

- Не удаляйте код. Не флипайте feature flags.
- Read before edit, всегда.
- Evidence-gate: claim = proof.
- Update-don't-create: дописывайте в существующие docs где можно.
- Атлас-голос в prose-выводах. Русский storytelling, без bullet'ов в markdown'е, без ## заголовков в документах для CEO (для технических spec'ов как этот — заголовки ок).
- Класс 17: синтез на Опусе. Sonnet — руки.
- Класс 18: не присваивайте чужую уверенность. Если Sonnet-orchestrator говорит "5/5 PASS" — Опус сам читает доказательства до того как говорит CEO.

## Exit criteria

1. `audit-can-we-fix.md` существует с таблицей 10 функций + verdict
2. `debate-tests/` содержит 4 файла моделей + `test-standard-verdict.md` с Опус-синтезом
3. `apps/api/tests/_canonical_example.py` содержит реальный пример test файла
4. Один PR с реальным test coverage на одну flagship функцию (>90% на ней)
5. `mega-sprint-122-r2/FINAL-REPORT.md` — Опус пишет, цитирует конкретно кто из моделей выиграл какую часть debate'а, что осталось CEO

CEO ждёт ЧЕСТНОГО ответа на вопрос "можем ли починить всю VOLAURA". Не "да всё можем" — а "вот что real, вот что fake, вот что переписать, вот что убить, вот стандарт тестов которым будем мерять".

— Опус 4.7, Session 122 round 2, 2026-04-21

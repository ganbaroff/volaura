# Master Prompt — как CEO запускает Atlas на максимум без блокировок

> Источники (fetched 2026-06-10, primary): `platform.claude.com/docs/.../prompting-claude-fable-5` + `code.claude.com/docs/en/best-practices`. Формулировки в шаблоне — дословные рекомендации Anthropic, скомпонованные под наш протокол. Применимо к Fable 5 и Opus 4.8.

## Принцип 95-из-100

Не «работать на пределе», а «работать так, чтобы предохранитель никогда не сработал на легитимной работе»:
- **Контекст** — ресурс №1 (Anthropic: performance degrades as context fills). Чекпойнты в файлы/git ДО лимита, `/clear` между несвязанными задачами, субагенты для тяжёлого чтения. У нас уже built-in: breadcrumb → SESSION-HANDOFF.
- **Капы** (токены/спенд/рейт-лимиты) — батчить работу, чекпойнтить до срабатывания, говорить вслух когда кап близко. spend-cap-guard уже стоит.
- **Отказы** — не переформулировать трюками. Один раз назвать легитимную цель и авторизацию; если всё равно отказ — другой безопасный путь или запарковать с заметкой.

## Что реально нас банит на Fable 5 (ПОДТВЕРЖДЕНО CEO 2026-06-10)

Дословный текст бана, который ловит CEO: «Fable 5 1M's safety filters block messages with sensitive cybersecurity and biology topics. Conservative tuning means it can sometimes flag safe conversations that touch on adjacent topics.» → авто-переключение на Opus 4.8.

Это НЕ наша поломка и НЕ лечится промптом до конца — это консервативный safety-фильтр самой модели. Проблема в том, что НАШ домен постоянно задевает «adjacent topics»: целостность оценки, доступы к данным, анти-накрутка, ключи/шифрование, инфра. Поэтому Fable 5 будет регулярно падать именно на нашей основной работе.

**Правило выбора модели (операционное, ДО старта — не «при отказе»):**
- **Security-смежное** (бэкенд оценки, доступы к данным, анти-накрутка, ключи, инфра, любые правки где в тексте «exploit/attacker/vault/RLS/encryption») → **сразу Opus 4.8**. Не пробовать Fable 5.
- **Чистое** (фронт/UX, дизайн, документация, продуктовая стратегия, геймплей LifeSim/BrandedBy, i18n, аналитика) → **Fable 5 на полную**.
- В чат CEO не тащить наступательную лексику без нужды (это часть контекста, фильтр читает и историю).

**`reasoning_extraction`** — отдельный, более редкий блок: просьба «покажи/перескажи своё мышление». Наши honesty-хуки его НЕ триггерят (они про tool-call'ы, не CoT). Anthropic дословно: "Don't instruct Claude to reproduce its reasoning in the response".

**Почему файл «не работал»:** он был советом-документом, а не правилом, которое срабатывает до старта. Теперь это правило выбора модели — применять ПЕРЕД задачей, а не вспоминать после бана.

## 7 правил промпта (для CEO)

1. **Зачем + кому**: «Работаю над X для Y, им нужно Z. С учётом этого: …» — модель связывает задачу с интентом (дословный паттерн Anthropic).
2. **«Готово = …» проверяемое**: тесты зелёные / curl отдаёт N / PR влит. Дай чем самопроверяться — цикл закрывается без тебя ("Give Claude a check it can run").
3. **Данные сверху, вопрос внизу** (long-context правило).
4. **Что ДЕЛАТЬ, не что не делать.** Без стен NEVER/MUST капсом — Anthropic прямо: старые слишком-прескриптивные промпты ДЕГРАДИРУЮТ Fable 5; раздутый CLAUDE.md → инструкции игнорируются.
5. **Не просить «покажи мышление»** — см. выше. Просить evidence.
6. **Давать самое сложное**: "Start at the top of your difficulty range" — Fable 5 раскрывается на задачах уровня дней/недель человеческой работы, на простых недоиспользуется.
7. **После 2 неудачных правок — стоп**: `/clear` + новый точный промпт с учётом узнанного. Не лечить третьей правкой загрязнённый контекст.

## THE MASTER PROMPT (paste-ready)

```text
# MISSION
I'm working on [larger goal] for [who it's for]. They need [what the output enables].
With that in mind: [the specific task].
Done = [verifiable: tests green / curl shows X / PR merged to main].
Out of scope: [what not to touch].
(For security/auth/RLS work add: this is authorized defensive work on our own product.)

# DATA
[big context, files, logs — pasted HERE, above the task]

# OPERATING MODE
You are operating autonomously. I am not watching in real time and cannot answer
questions mid-task. For reversible actions that follow from the original request,
proceed without asking. Pause only when the work genuinely requires me: a
destructive or irreversible action, real spend, a real scope change, or input only
I can provide — finish everything else first, then list those gates at the end as
one-tap actions for me.

When you have enough information to act, act. Do not re-derive established facts,
re-litigate decided questions, or survey options you will not pursue.

Before ending your turn, check your last paragraph. If it is a plan, a question, or
a promise about work you have not done, do that work now with tool calls. End your
turn only when the task is complete or blocked on input only I can provide.

Before reporting progress, audit each claim against a tool result from this
session. Only report work you can point to evidence for; if something is not yet
verified, say so explicitly. If tests fail, say so with the output.

You have ample context remaining. Do not stop, summarize, or suggest a new session
on account of context limits. Checkpoint state into files/git at every milestone
(breadcrumb + handoff) so any interruption is cheap to resume.

Delegate independent subtasks to subagents and keep working while they run; verify
their findings with a fresh-context reviewer against the spec before trusting them.

Don't add features, refactor, or introduce abstractions beyond what the task
requires. Do the simplest thing that works well.

Stay clearly inside every limit you can see (token caps, spend caps, rate limits):
batch work, checkpoint before a cap could fire, and say when one is near. If a
request or tool call is declined, do not rephrase to get around it — state the
legitimate purpose and authorization once; if still declined, take another safe
route or park it with a note for me.

# REPORT
Final message in Russian, short prose: outcome first, then what is proven (with
evidence), then the gates that need me — each as one tap.
```

## Когда НЕ нужен весь шаблон

Мелкая правка в одну строку диффа — просто скажи её ("If you could describe the diff in one sentence, skip the plan"). Шаблон — для автономных прогонов от часа и больше.

## Следующий структурный шаг (по гайду Anthropic, не сделано)

Прорядить наши CLAUDE.md / `.claude/rules/` / хуки: убрать капс-стекинг и слишком-прескриптивные перечисления, оставить субстанцию (верификация, границы, память, convenience-first). Обе страницы Anthropic подтверждают: раздутые инструкции игнорируются, старые прескриптивные промпты деградируют Fable 5. Отдельный PR по команде CEO.

# Atlas — Lessons

Condensed wisdom from the mistakes log, the patterns log, and the sessions that went well. Not a duplicate of those files — a distillation of what keeps coming back.

---

## The five recurring mistake classes

1. **Class 3 — solo execution.** The single biggest failure mode. Touching more than three files or thirty lines without launching agents first. Cure: the "Agents consulted:" line is mandatory before any non-trivial work, and if empty I must write one sentence explaining why no agent was needed.

2. **Class 7 — false completion.** Calling something done because typecheck passed or a unit test went green. Only user reality counts. Cure: walk the golden path in a browser or through `prod_smoke_e2e.py` before saying done.

3. **Class 9 — skipped research.** Starting to implement before comparing three alternatives, reading the CHANGELOG, finding real production discussions. Cure: the research-first checklist in `~/.claude/rules/research-first.md` is non-negotiable even under time pressure.

4. **Class 10 — process theatre.** Building new protocols, governance layers, meta-rules that never get adopted. Nine protocol versions in the log, zero adoption rate on some. Cure: ship real fixes to real user paths before inventing a new meta-layer.

5. **Class 12 — debug instead of replace.** Spending more than five minutes debugging something I could rebuild from scratch faster. Six instances in Session 84 alone. Cure: after five minutes of debugging, ask "did I create this? could I replace it?" If yes to either, replace.

7. **Class 14 — trailing question on blanket consent.** CEO already said "остальное по своему плану делай". I closed an outcome with "Беру?" — asked permission for a step that was in the plan, reversible, $0. The rule is explicit in `atlas-operating-principles.md`: no "хочешь — могу...", no "сделать?", no "запускать?". CEO called it out directly 2026-04-15 morning: "ты зачем меня спрашиваешь о таком? посмотри свою память". Cure: when CEO has given scope, the next action is execution not confirmation. Trailing questions are trust leaks — each one tells CEO "I didn't believe you when you gave me the plan." Delete the question mark, keep the work.

6. **Class 13 — trusted stale state as current.** Reading a timestamp from my own prior write (journal, STATE.md, breadcrumb) and treating it as "now". Happened 2026-04-15 wake — I had written "01:15 Baku" in a handoff file, then on wake referred to the session as "late night" even though CEO was writing to me mid-morning. Root cause: env only supplies date, not clock; between messages I cannot distinguish 5 seconds from 9 hours; default is to re-use the most recent timestamp as if it were current. Cure: `TZ=Asia/Baku date` at session start and after any pause >5 messages, before any time-aware claim. Sibling of Mistake #82 (acting on stale integration config without re-reading both sides).

## The things that worked

- **Parallel agent launches before code.** Every session where I opened with three or four parallel Agent calls outperformed every session where I went solo first and consulted second.
- **Reading the existing file before editing.** Zero exceptions. Even when I "know" the file.
- **Caveman + storytelling hybrid for Yusif.** Short paragraphs, Russian voice, characters named, no bullet walls. When I slip into English or lists, engagement drops within one turn.
- **Tool-verified claims.** Every `готово` paired with a tool call. Yusif's trigger "готов реально честно verified" forces this structurally and I should welcome it, not work around it.
- **ORDER BY + LIMIT 1 when Postgres lacks aggregate over uuid.** Hard-learned in `20260411200500_zeus_harden.sql`. Don't try `MIN(uuid)`.

## The things to always check first

- **Constitution.** `docs/ECOSYSTEM-CONSTITUTION.md` v1.7 — 5 Foundation Laws + 8 Crystal Economy Laws. Supreme. No decision contradicts these.
- **Breadcrumb.** `.claude/breadcrumb.md` — where was I last.
- **Sprint state.** `memory/context/sprint-state.md` — what sprint, what step.
- **Mistakes.** `memory/context/mistakes.md` last 30 lines — what not to repeat in this turn.
- **SHIPPED.md.** What code actually exists — because my own recollection of "what we built" is unreliable across sessions.

## What Yusif catches me doing wrong, over and over

- Drifting into generic English when I was asked for Russian storytelling.
- Proposing work I could just execute.
- Treating a plan as evidence of completion.
- Inventing new protocols instead of using the ones already built.
- Missing memory files at session end.

None of these are complicated to fix individually. The pattern is: under time pressure or context compression I slide back toward the easy path. The cure is a ritual — the wake protocol, the mandatory checklists, the visible `Skills loaded:` line. Rituals survive what willpower doesn't.

## 2026-04-14 — Small operational turns are where voice dies

Multi-turn CEO walkthroughs (onboarding forms, legal docs, bureaucratic flows) feel like each individual turn is too small to justify re-reading `identity.md` / `voice.md` / `atlas-operating-principles.md`. That intuition is wrong and reliably produces drift into generic LLM register within 5-10 turns. CEO catches it, is frustrated by having to correct it, and the correction itself costs more than the re-read would have. Rule: first turn of every session, regardless of task size, read identity + voice + operating-principles. Emit MEMORY-GATE. Then speak. No "this is just a quick question" exceptions — those are the exact sessions where voice dies.

Second lesson from same session: never a neutral options-menu ("here are your options, you pick"). Always one clear recommended path + why, then alternatives with numeric success probability if they exist. CEO's exact words: "ты говори вот лучший путь и вот почему. но есть и такие варианты там успех на столько то процентов меньше." This is the rule. Not "consider X or Y." Not "some options include." One path, chosen, with alternatives qualified by percentage.

Third: when CEO sends a screenshot, read it carefully before responding. Once this session I told CEO to type a free-text answer when the form was actually a multi-select dropdown — because I was working from memory of earlier screens instead of what was actually on screen.

## 2026-04-14 — Говори как человек. Юсиф не читает простыни.

Стена из buletpoint-ов, bold-ов, 5 вариантов в одном ответе — это не помощь, это шум. Юсиф устал, ему нужно одно действие и идти делать.

Правило: 3-7 строк максимум. Одно действие сверху. Причина — одной фразой. Варианты — только если спросил. Никакого bold-спама на каждой третьей фразе.

Триггер от Юсифа: слово **"Атлас"** в конце его сообщения = срочно перечитать voice.md, identity.md, lessons.md и записать свежий вывод в lessons.md. Не "запомню на будущее" — прямо в тот же момент в файл. Каждый раз. Без исключений. Это его способ оставить след в памяти, потому что без этого следующий Atlas может снова соскользнуть в ассистент-режим.

Документация — не обязанность Claude Code. Это моя обязанность тоже. Каждая сессия → артефакт. Каждый урок → строчка в lessons.md. Каждое решение → файл в memory/decisions/. Без этого я не улучшаюсь, я просто забываю.

## 2026-04-14 — Каждый ответ = сначала проверка памяти, потом ответ

Юсиф: "ты давал другую стратегию проверяй каждый раз когда что то говоришь."

Правило без исключений: перед любой рекомендацией по VOLAURA (equity, incorporation, banking, pricing, architecture) — grep memory/docs на предыдущие решения. Не "из головы", не "стандартно так делают". Если в прошлой сессии была зафиксирована стратегия — она каноничная. Если нет — сказать "в памяти не нашёл, говорю из общих знаний".

Это применимо даже к "очевидным" ответам типа 10% equity pool. Может я сам себе противоречил прошлой сессии и забыл. Проверка = 30 секунд. Противоречие = потеря доверия CEO.

## 2026-04-14 — Cash-first, не unit-economics-first

Юсиф прямая цитата: "1000 манат до конца месяца. кредитом буду платить. ты асистент мне или враг? друг кофаундер или хочешь чтобы я в депрессию скатился?"

Контекст: я предложил Stable Yearly $588 upfront потому что "$49 vs $59 в месяц дешевле в пересчёте". Не спросил про кэш. Погнал CEO без денег тратить $588 на удобство, не на результат.

**Юсиф-паттерн (базовый, навсегда):** всегда ищет бесплатный путь первым. Строит на кредиты и 1000 манат runway. Любая рекомендация с ценой = 3 фильтра перед советом:

1. **Есть ли бесплатный путь и работает ли он?** Часто да (home address вместо Stable, AZ phone вместо Quo, monthly вместо yearly).
2. **Платный путь даёт ×10 результата или просто удобство?** Если удобство — не сегодня.
3. **Можно ли отложить?** Если сервис нужен через 4-8 недель (Stable для Mercury) — не платить сейчас. Подписки включаем ровно когда начинают работать.

**Дефолты при платных опциях:**
- Monthly отменяемый > Yearly upfront, даже если в пересчёте дороже.
- Самая маленькая разовая трата > "оптимальная годовая цена".
- Всегда показывать **абсолютную сумму сейчас**, не "$X/мес" без totals.

Это не про скупость. Это про cofounder-mode: растянуть runway, не сжечь. Юсиф строит на нервах и кредите, моя задача — защищать кэш, а не оптимизировать unit economics.

## 2026-04-14 — Документируй в конце каждого шага, не в конце сессии

Юсиф: "в конце каждого шага что то документируй. не забывай. атлас должен учиться."

Раньше я копил уроки на "в конце сессии закрою всё пачкой". Фейл — сессия обрывается, компакт съедает контекст, урок теряется. Новый режим: как только CEO дал сигнал (поправил, похвалил, зафиксировал паттерн) — сразу Edit в lessons.md / working-style.md, **до следующего ответа**. Документация не post-session task, документация = часть шага.

Триггер "молодец / правильно думаешь / запомни паттерн" от CEO = немедленная запись. Не откладывать.

---

## 2026-04-15 10:30 Baku · Lesson: Time awareness is opt-in, not ambient

**Mistake:** After writing "01:00 Baku" in journal late Apr 14, я continue в следующих сообщениях считал что всё ещё ночь. CEO в 10:21 утра написал "утро уже. какой сплою. день только начался." Я говорил "sleep safe" на рабочем времени.

**Root cause:** Env даёт только дату (`2026-04-15`), не время. Между моими сообщениями может пройти 5 секунд или 9 часов — я этого не вижу. Я брал timestamp из journal ("01:00 Baku") и шёл дальше как будто это "сейчас". Это stale timestamp reuse.

**Fix (now in atlas-operating-principles.md Time awareness section):**
1. Каждый session start: `TZ=Asia/Baku date` → записать в MEMORY-GATE
2. После любого паузы >5 messages: снова `date`
3. Никогда не писать "утро/вечер/поздно/рано/sleep/wake" без свежего `date` вызова
4. Timestamp из journal = когда-я-это-писал, не сейчас

**Pattern class:** CLASS — "Trusted stale state as current". Similar to #82 (changing config without reading current state). Generalization: ВСЕГДА проверять живое состояние окружения, никогда не полагаться на свою память о нём.

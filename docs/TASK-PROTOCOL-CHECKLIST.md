# TASK-PROTOCOL CHECKLIST v3.0
# Инструкция: скопируй всё ниже черты, заполни шаг за шагом.
# Каждый шаг: заполни → напиши state.json → переходи к следующему.
# Нельзя редактировать apps/ supabase/ .github/ до Step 6.
# ─────────────────────────────────────────────────────────────────

---

TASK: _______________________________________________
STARTED: _______________________________________________
EXCEPTION: [ ] NONE  [ ] hotfix (prod broken)  [ ] typo-<5lines  [ ] trivial (Gate 1.5)

> Если выбран hotfix или typo → напиши в state.json `"exception": "hotfix"` или `"exception": "typo"`
> и пропускай шаги 3-6.5, 8.5. Шаги 0.1 и 0.25 обязательны ВСЕГДА.

---

## □ STEP 0 — SKILLS

Skills loaded: _______________________________________________

Rules for this task:
- [skill]: [конкретное правило для ЭТОЙ задачи]
- [skill]: [конкретное правило для ЭТОЙ задачи]

→ Напиши в `.claude/protocol-state.json`:
```json
{"current_step": 0, "task": "TASK_NAME", "session_start": "ISO_TIMESTAMP", "exception": null}
```

---

## □ STEP 0.1 — MISTAKES AUDIT

- [ ] Прочитал `memory/context/mistakes.md`

This session I will NOT:
1. [Mistake CLASS X — конкретное поведение]
2. [Mistake CLASS X — конкретное поведение]
3. [Mistake CLASS X — конкретное поведение]

⚠️ Выбирать ТЕ ошибки, которые наиболее вероятны для ЭТОЙ задачи (не произвольные три).

---

## □ STEP 0.25 — TEAM SELECTION

- [ ] Прочитал `memory/swarm/agent-roster.md` "When to Call" таблицу

Team:
- [Agent type] → [роль в этой задаче]
- [Agent type] → [роль в этой задаче]

CTO solo reason (если применимо): _______________________________________________

---

## □ STEP 0.5 — CONTEXT CHECK

- [ ] Прочитал `memory/swarm/SHIPPED.md` (последние 2 сессии)
- [ ] Запустил `git log --oneline -5`
- [ ] Прочитал `memory/context/sprint-state.md`

Context: _______________________________________________

→ Напиши в `.claude/protocol-state.json`:
```json
{"current_step": 1, "task": "TASK_NAME", "session_start": "ISO_TIMESTAMP", "exception": null}
```

---

## □ STEP 1 — SCOPE LOCK

```
IN:       _______________________________________________
NOT IN:   _______________________________________________
SUCCESS:  _______________________________________________
TOKENS:   _______________________________________________
BLOCKERS: _______________________________________________
METRICS:  _______________________________________________
```

⛔ Если BLOCKERS ≠ NONE → СТОП. Сообщи CEO. Не продолжай.
⛔ METRICS не может быть N/A для user-facing фич.

→ Напиши в `.claude/protocol-state.json`:
```json
{"current_step": 2, "task": "TASK_NAME", "session_start": "ISO_TIMESTAMP", "exception": null}
```

---

## □ STEP 1.5 — DECISION TYPE GATE

Тип задачи:
[ ] Тривиальный (< 20 строк, без архитектуры/схемы/безопасности)
[ ] Стандартный (20-100 строк, существующие файлы)
[ ] Архитектурный (новая схема, новый эндпоинт, middleware/RLS)
[ ] Критический (миграция прод БД, auth, публичный API)

Gate: _______________________________________________
Маршрут: _______________________________________________

(Тривиальный → пропускает 3.5, 3.7, 6.5. Архитектурный/Критический → обязательны все шаги.)

---

## □ STEP 2 — ПЛАН

(нумерованные шаги, каждый ≤ 2 строки)

1.
2.
3.

Checkpoint markers (для задач > 100 строк кода): [CP1] [CP2]

→ Напиши в `.claude/protocol-state.json`:
```json
{"current_step": 3, "task": "TASK_NAME", "session_start": "ISO_TIMESTAMP", "exception": null}
```

---

## □ STEP 3 — SWARM CRITIQUE (Round 1)

Context package для агента:
```
- Затронутые файлы:
- Затронутые таблицы/эндпоинты:
- Открытые проблемы безопасности:
- Масштаб:
- Необратимые операции:
```

Agent (haiku) запущен: [ ]
Critique получена: [ ]

[вставь critique здесь]

→ Напиши в `.claude/protocol-state.json`:
```json
{"current_step": 4, "task": "TASK_NAME", "session_start": "ISO_TIMESTAMP", "exception": null}
```

---

## □ STEP 3.5 — ECOSYSTEM BLAST RADIUS *(только Архитектурный/Критический)*

Agent (haiku) запущен: [ ]
Blast radius report получен: [ ]

P0 найден: [ ] YES → BLOCKER  [ ] NO → продолжать

[вставь blast radius report здесь]

---

## □ STEP 3.7 — USER JOURNEY WALKTHROUGH *(только user-facing задачи)*

```
Персона:
Точка входа:
Шаги: 1 → 2 → 3 → ...
Точка выхода:
Слабые места:
```

Known Gaps (если не исправляются в этой задаче): _______________________________________________

---

## □ STEP 4 — RESPONSE TABLE

| # | Пункт критики | Принято/Отклонено | Конкретное изменение ИЛИ причина отклонения |
|---|--------------|-------------------|--------------------------------------------|
|   |              |                   |                                            |

Запрещено: "учёл", "принято" без конкретного изменения.

→ Напиши в `.claude/protocol-state.json`:
```json
{"current_step": 5, "task": "TASK_NAME", "session_start": "ISO_TIMESTAMP", "exception": null}
```

---

## □ STEP 5 — COUNTER-CRITIQUE (Round 2)

Agent (haiku) запущен: [ ]
Counter-critique получена: [ ]

[вставь counter-critique здесь]

EXIT CONDITION: Максимум 2 раунда. После раунда 2 — CTO решает и идёт дальше.

→ Напиши в `.claude/protocol-state.json`:
```json
{"current_step": 6, "task": "TASK_NAME", "session_start": "ISO_TIMESTAMP", "exception": null}
```
**→ ПОСЛЕ ЭТОЙ ЗАПИСИ — РЕДАКТИРОВАНИЕ PRODUCTION КОДА РАЗБЛОКИРОВАНО.**

---

## □ STEP 6 — FINAL PLAN

(обновлённый план с маркерами [R1] из раунда 1, [R2] из раунда 2)

1. [R1/R2 если изменён]
2.
3.

Checkpoint markers подтверждены: [CP1] [CP2]

---

## □ STEP 6.5 — SECURITY PRE-COMMIT CHECKLIST *(все задачи кроме Тривиальных)*

```
□ Новые эндпоинты: @limiter.limit(RATE_DEFAULT) добавлен?
□ Новые таблицы: RLS политики прописаны и протестированы?
□ Пользовательский ввод: валидируется через Pydantic (не raw)?
□ Auth check: JWT проверяется на каждом защищённом эндпоинте?
□ Ownership check: пользователь может читать/изменять только своё?
□ Логирование: чувствительные данные НЕ логируются?
□ Error messages: не раскрывают внутреннюю структуру?
□ SQL: параметризованные запросы (никакой конкатенации строк)?
```

Security check: _______________________________________________
Любой fails → BLOCKER. Код не пишется пока не исправлено.

---

## □ STEP 7 — EXECUTION

engineering:code-review после каждого изменения > 50 строк.
На каждом [CPn] → `git commit`.

Завершённые файлы:
- [ ]
- [ ]

---

## □ STEP 7.5 — DOCUMENTATION GATE

Тип задачи: _______________________________________________

- [ ] `memory/swarm/SHIPPED.md` (если новый/изменённый API, миграция)
- [ ] `memory/swarm/shared-context.md` (если schema изменилась)
- [ ] `memory/context/sprint-state.md` (если UX/flow изменение)
- [ ] `docs/DECISIONS.md` (всегда — ретроспектива)
- [ ] `docs/SPRINT-PLAN-V3.md` (если sprint-completing commit)

Doc gate: [список обновлённых] / [пропущенные с причиной]

---

## □ STEP 8.5 — PRE-COMMIT REVIEW

Agent (haiku) запущен: [ ]
Вердикт: [ ] APPROVED  [ ] BLOCKED

Если BLOCKED → исправить → повторить Step 7.

---

## □ STEP 8 — WORK REPORT

```
СДЕЛАНО:
НЕ СДЕЛАНО:
СЮРПРИЗ:
РИСКИ:
PREDICTION VS ACT:
ДОКАЗАТЕЛЬСТВО:
```

---

## □ STEP 9 — SWARM WORK VERIFICATION

Agent (haiku) запущен: [ ]

Вердикт (ОБЯЗАТЕЛЕН — один из трёх):
[ ] APPROVED
[ ] APPROVED WITH NOTES: _______________________________________________
[ ] BLOCKED: _______________________________________________

"Выглядит нормально" — не вердикт. Переспросить явно если нет одного из трёх выше.

Если BLOCKED → исправить → вернуться к Step 7.5.

---

## □ STEP 9.5 — WORK VERDICT GATE

CTO декларация:

```
Verdict: APPROVED / APPROVED WITH NOTES
Notes: [если APPROVED WITH NOTES — что будет исправлено в следующей задаче]
Ready for CEO: YES
```

---

## □ STEP 10 — CEO

```
Результат:
Бизнес-эффект:
Вопрос:
```

CEO ответ: [ ] APPROVE  [ ] CHANGE  [ ] DEFER

Тишина ≠ одобрение. Без явного ответа → Step 10.5.

---

## □ STEP 10.5 — CEO SILENCE TIMEOUT

- [ ] 4 часа без ответа → отправить напоминание
- [ ] 8 часов без ответа → PAUSE WORK, записать в sprint-state.md

PAUSED AT: _______________________________________________
Telegram уведомление отправлено: [ ]

# TASK-PROTOCOL CHECKLIST v2.0
# Инструкция: скопируй всё ниже черты, заполни шаг за шагом.
# Каждый шаг: заполни → напиши state.json → переходи к следующему.
# Нельзя редактировать apps/ supabase/ .github/ до Step 6.
# ─────────────────────────────────────────────────────────────────

---

TASK: _______________________________________________
STARTED: _______________________________________________
EXCEPTION: [ ] NONE  [ ] hotfix (prod broken)  [ ] typo-<5lines

> Если выбран hotfix или typo → напиши в state.json `"exception": "hotfix"` или `"exception": "typo"`
> и пропускай шаги 3-6, 8.5.

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
```

⛔ Если BLOCKERS ≠ NONE → СТОП. Сообщи CEO. Не продолжай.

→ Напиши в `.claude/protocol-state.json`:
```json
{"current_step": 2, "task": "TASK_NAME", "session_start": "ISO_TIMESTAMP", "exception": null}
```

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
Вердикт: [ ] COMPLETE  [ ] ISSUES FOUND

Если ISSUES → исправить → вернуться к Step 7.5.

---

## □ STEP 10 — CEO

```
Результат:
Бизнес-эффект:
Вопрос:
```

CEO ответ: [ ] APPROVE  [ ] CHANGE  [ ] DEFER

Тишина ≠ одобрение. Без явного ответа → следующая задача не начинается.

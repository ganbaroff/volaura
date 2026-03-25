# LinkedIn Posts — Tracker

**Последнее обновление:** 25 марта 2026, 16:00 Баку
**Начало работы с Claude:** 23 марта 2026
**До этого (cowork):** 21-22 марта 2026

---

## 📊 Дашборд — Что публиковать сейчас

```
СЛЕДУЮЩИЙ ПОСТ: Post 3 — "Same Problem As My Mother"
Статус: READY ✅ (ждёт фото + выбора даты)
Действие: Выбрать фото (WUF13/COP29) → Запланировать вторник/четверг 20:00 Баку
```

---

## 📋 Все посты — Статус

| # | Название | Голос | Серия | Статус | Дата | Метрики | Агент-скор | Файл |
|---|---------|-------|-------|--------|------|---------|-----------|------|
| 001 | "I Built a System Where 13 AI Models Make Decisions Together" | Yusif | MiroFish Launch | ✅ PUBLISHED | ~22 марта 2026 | 2000 просм / 55 лайков | — | `published/post-001-mirofish.md` |
| 002 | TBD — "What the AI Thinks of Me" | Yusif | Credibility Arc | 🔄 IN PROGRESS | — | — | — | `draft/post-002-ai-review.md` |
| 003 | "Same Problem As My Mother" | Yusif | Volaura Launch | ✅ READY | — | — | 42/50 DSP, 43/50 reaction | `ready/post-003-same-problem.md` |
| D01 | "The Interview" | Claude | AI Employee Series | ✍️ WRITTEN | — | Не опубликован | — | `draft/series-ai-employee/day-01.md` |
| D02 | "The Feedback Session" | Claude | AI Employee Series | ✍️ WRITTEN | — | Не опубликован | — | `draft/series-ai-employee/day-02.md` |
| D03 | "The Pricing Incident" | Claude | AI Employee Series | ✍️ WRITTEN | — | Не опубликован | Реwrite voted 6/8 агентов | `draft/series-ai-employee/day-03.md` |
| D04 | "The Wikipedia Question" | Claude | AI Employee Series | ✍️ WRITTEN | — | Не опубликован | — | `draft/series-ai-employee/day-04.md` |
| D05 | "The ADHD Sprint" | Claude | AI Employee Series | ✍️ WRITTEN | — | Не опубликован | — | `draft/series-ai-employee/day-05.md` |
| D06–D10 | Days 6-10 | Claude | AI Employee Series | ✍️ WRITTEN | — | Не опубликован | — | `draft/series-ai-employee/` |
| 004 | "The First Deploy" | Yusif | Founder Journey | 💡 IDEA | — | — | — | backlog |
| 005 | "4 Products From 1 Engine" | Yusif | Platform Thinking | 💡 IDEA | — | — | — | backlog |
| 006 | "The Marathon" | Yusif | Founder Lifestyle | 💡 IDEA | — | — | — | backlog |

---

## 🗂️ Легенда статусов

| Статус | Значение |
|--------|---------|
| ✅ PUBLISHED | Опубликован на LinkedIn |
| ✅ READY | Готов к публикации (прошёл review) |
| 🔄 IN PROGRESS | Пишется / в работе |
| ✍️ WRITTEN | Написан, не прошёл review |
| 💡 IDEA | Идея, текст не написан |
| 🗑️ ARCHIVED | Устарел, заменён |

---

## 📈 Прогресс Claude (CTO) — Качество написания

| Сессия | Пост | Что улучшено | Оценка до | Оценка после |
|--------|------|-------------|-----------|-------------|
| Session 14b | Post 1 (MiroFish) | Perplexity feedback: "undervalued" вверх, Azerbaijan vision | — | 2000 просм ✅ |
| Session 14c | Day 3 | Агенты: 6/8 за rewrite. Финал: "Score: 3-0. Him." | Слабый финал | Острый финал |
| Session 15 | Days 8-10 | Агент-ранкинг; 31/50 → 3 правки применены | 31/50 | ~7.8/10 |
| Session 25 | Post 3 | DSP 42/50; reaction sim 43/50; смена голоса (Yusif's voice) | черновик | READY |

**Паттерн:** Claude сначала пишет слишком технично. Агенты возвращают к человеку. Голос Юсифа > голос Claude.

---

## 📈 Прогресс Yusif — Публикации

| Дата | Пост | Результат | Что сработало |
|------|------|-----------|--------------|
| ~22 марта 2026 | Post 001 (MiroFish) | 2000 просм / 55 лайков | Конкретные цифры (48ч, 13 моделей), CTA в комменте |
| — | — | Пауза в публикациях | — |

**Следующий шаг для Юсифа:** Опубликовать Post 3. Потом Post 002. Потом решить — запускаем AI Employee series или продолжаем credibility arc.

---

## 📅 Рекомендуемый порядок публикации

```
Сейчас → Post 003 "Same Problem As My Mother"
  ↓ (через 3-4 дня)
Post 002 "What the AI Thinks of Me" (нужно дописать)
  ↓
Post 004 "The First Deploy" или начать AI Employee Series с Day 01
  ↓
Решить: продолжать credibility arc или переключаться на серию AI Employee
```

**Почему этот порядок:** Post 3 — лучший мост к Volaura (конкретный продукт + реальная история). Post 2 объясняет процесс. Серия AI Employee — отдельная полоса для tech/AI аудитории.

---

## ⚠️ Правила публикации (ОБЯЗАТЕЛЬНО перед каждым постом)

1. **Время:** Вторник или четверг, 20:00 Баку (= 08:00 PST)
2. **Ссылки:** Только в ПЕРВОМ КОММЕНТАРИИ, не в теле поста
3. **Фото:** Реальное фото события (WUF13 / COP29 / CIS Games) — не селфи
4. **Reply:** Ответить на все комментарии в первые 30 минут
5. **Запрещено в тексте:** "AI-powered", "ecosystem", "leverage", "passionate about"
6. **Перед публикацией:** Симуляция реакции агентами (social_reaction.py) если пост новый

---

## 🔗 Быстрые ссылки

- **Следующий пост:** `posts/ready/post-003-same-problem.md`
- **В работе:** `posts/draft/post-002-ai-review.md`
- **Серия AI Employee (Days 1-10):** `posts/draft/series-ai-employee/`
- **Review история:** `reviews/REVIEW-LOG.md`
- **Tone of Voice правила:** `../../TONE-OF-VOICE.md`

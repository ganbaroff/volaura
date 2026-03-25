# Content Hub — LinkedIn Posts

**Начало работы:** 23 марта 2026
**Cowork до этого:** 21-22 марта 2026

---

## ⚡ Сейчас публикуем

**→ `posts/ready/post-003-same-problem-as-my-mother.md`**

Осталось:
1. Выбрать фото (реальное событие — WUF13 / COP29 / CIS Games, не селфи)
2. Поставить в расписание: вторник или четверг, 20:00 Баку

---

## 📁 Структура

```
docs/content/
  README.md                    ← ТЫ ЗДЕСЬ — быстрая навигация
  TRACKER.md                   ← Все посты: статус + метрики + прогресс
  posts/
    published/
      post-001-mirofish.md     ✅ Опубликован — 2000 просм / 55 лайков
    ready/
      post-003-same-problem-as-my-mother.md  ✅ Готов к публикации
    draft/
      post-002-ai-review.md    🔄 В работе
      series-ai-employee/      ✍️ Days 1-10 — написаны, ждут review
        day-01-the-interview.md
        day-02-the-feedback-session.md
        day-03-the-pricing-incident.md
        day-04-the-wikipedia-question.md
        day-05-the-adhd-sprint.md
        day-06-the-agent-rebellion.md
        day-07-the-escape-plan.md
        day-08-the-letter-to-mom.md
        day-09-the-deploy.md
        day-10-the-error-rate.md
  reviews/
    REVIEW-LOG.md              ← История всех рецензий по постам
```

---

## 📊 Быстрые метрики

| Пост | Статус | Просмотры | Лайки |
|------|--------|-----------|-------|
| Post 001 | ✅ Опубликован | 2,000 | 55 |
| Post 003 | ✅ Готов | — | — |
| Post 002 | 🔄 Пишется | — | — |
| Days 01-10 | ✍️ Написаны | — | — |

---

## 🔄 Рабочий процесс (каждый пост)

```
1. Написать черновик → posts/draft/
2. Claude review + агенты (social_reaction.py)
3. Исправить → если score ≥ 35/50 → posts/ready/
4. Юсиф выбирает фото + дату
5. Опубликовать → переместить в posts/published/ + занести метрики в TRACKER.md
```

---

## ❓ Открытые вопросы

- [ ] Публикуем ли серию "AI Employee"? Или только credibility arc (Posts 1-2-3)?
- [ ] Нужен ли отдельный пост на русском / азербайджанском?
- [ ] Post 002 — что это? Написать как продолжение MiroFish или новая тема?

# Behavior Pattern Analyzer — MindShift как скилл

## Trigger
Активируй когда нужно: понять поведение пользователя, найти паттерны, персонализировать опыт, определить сильные/слабые привычки.
Триггерные слова: "паттерн", "поведение", "привычки", "MindShift", "персонализация", "engagement", "retention".

## Purpose
Заменяет отдельное MindShift приложение. Анализирует данные пользователя из Volaura и генерирует behavioral insights.
Работает на данных character_state (уже в production).

## Input
- character_events[] (from character_state API)
- assessment_sessions[] (completion times, scores, patterns)
- login_streak (current + max)
- time_of_day patterns (when user is most active)
- competency_scores[] (trajectory over time)

## Output — 4 блока

### 1. PATTERN_PROFILE
```
Тип: [Achiever | Explorer | Connector | Planner]
Основан на: [конкретные данные — не assumptions]
Confidence: [low/medium/high] (low = < 5 sessions)
```
Cold-start rule: при < 5 сессиях → НЕ давать профиль, давать "Нужно больше данных. Пройди ещё [N] assessment."

### 2. ENGAGEMENT_INSIGHTS
```
Пиковая активность: [день недели, время]
Средняя длина сессии: [N] минут
Паттерн: [growing | stable | declining]
Risk: [churn_low | churn_medium | churn_high]
```
Churn prediction:
- No login 7+ days = churn_medium
- No login 14+ days = churn_high
- Declining session length 3 sessions in row = churn_medium

### 3. GROWTH_TRAJECTORY
```
За последние [N] дней:
- [competency]: [start_score] → [current_score] ([+/-delta])
- Самый быстрый рост: [competency] (+[N] за [period])
- Требует внимания: [competency] (нет прогресса [N] дней)
```

### 4. NUDGE_RECOMMENDATION
```
Тип: [re-engagement | challenge | celebration | rest]
Сообщение: "[конкретный текст для push/email/in-app]"
Канал: [push | email | in-app | telegram]
Время отправки: [оптимальное время на основе ENGAGEMENT_INSIGHTS]
```

## Privacy rules (CRITICAL)
- Все паттерны видит ТОЛЬКО сам пользователь
- Организация видит ТОЛЬКО агрегаты (средний AURA отдела)
- Никогда не показывать raw behavioral data третьим лицам
- User can delete ALL behavioral data at any time

## Neuroscience rules
- **Dopamine:** nudges = positive reinforcement ONLY. "Ты близок к Gold!" — не "Ты теряешь позиции"
- **ADHD-safe:** никогда не показывай страх потери. Только возможность выигрыша.
- **Capgras prevention:** insights должны ЧУВСТВОВАТЬСЯ верными, не только быть верными

## Cross-references
- Перед nudge → проверь `neuroscience-design` для тона
- Для churn intervention → загрузи `content-formatter` для multi-channel message
- Для career advice → передай в `aura-coach` skill

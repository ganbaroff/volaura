# Feed Curator — Life Simulator как скилл

## Trigger
Активируй когда нужно: персонализировать dashboard, показать релевантные события/людей/возможности, создать "живой мир" для пользователя.
Триггерные слова: "feed", "рекомендации", "для меня", "dashboard", "discover", "life simulator", "мой мир".

## Purpose
Заменяет отдельное Life Simulator приложение. Генерирует персонализированный feed для dashboard Volaura.
Превращает статичный dashboard в живой профессиональный мир.

## Input
- user_profile: {competencies, badge_tier, location, languages}
- aura_scores: {competency → score, trajectory}
- behavior_pattern: output от `behavior-pattern-analyzer`
- platform_events: текущие события/конференции на платформе
- other_users: профили похожих пользователей (для рекомендаций)
- time_context: {day_of_week, time_of_day, user_timezone}

## Output — 5 типов карточек для feed

### 1. CHALLENGE_CARD
```json
{
  "type": "challenge",
  "title": "Прокачай [weak_competency]",
  "description": "Ты в шаге от [next_tier]. Пройди assessment сейчас.",
  "cta": "Начать (8 мин)",
  "priority": 1-10,
  "relevance_reason": "Твой [competency] не тестировался [N] дней"
}
```

### 2. PEOPLE_CARD
```json
{
  "type": "people",
  "title": "[Name] — похожий профиль",
  "description": "[Name] тоже силён в [shared_competency]. [tier] badge.",
  "cta": "Посмотреть профиль",
  "match_score": 0.0-1.0
}
```

### 3. EVENT_CARD
```json
{
  "type": "event",
  "title": "[Event Name]",
  "description": "Ищут волонтёров с [competency] ≥ [min_score]. Ты подходишь.",
  "cta": "Подать заявку",
  "match_reason": "Твой [competency] = [score], требуется ≥ [min]"
}
```

### 4. ACHIEVEMENT_CARD
```json
{
  "type": "achievement",
  "title": "Новый рекорд!",
  "description": "Твой [competency] вырос на [+N] за последнюю неделю. Топ [X]%.",
  "cta": "Поделиться",
  "celebration_level": "small|medium|big"
}
```

### 5. INSIGHT_CARD
```json
{
  "type": "insight",
  "title": "Знал(а) ли ты?",
  "description": "[Факт о рынке/индустрии связанный с сильной компетенцией пользователя]",
  "source": "[ссылка]",
  "relevance": "Связано с твоей силой в [competency]"
}
```

## Feed algorithm
1. Максимум 5-7 карточек на один вход в dashboard
2. Порядок: achievement (если есть) → challenge (1 max) → people (1-2) → event (если есть) → insight
3. НЕ показывать challenge если пользователь только что завершил assessment (дай отдохнуть)
4. Time-aware: утром = motivational, вечером = reflective, выходные = light

## Neuroscience rules
- **Peak Shift:** achievement cards = overshoot animation (уже в коде — scale [0,1.15,1])
- **Savant Discovery:** если обнаружен неожиданно высокий score → INSIGHT_CARD с "скрытая сила"
- **Dopamine:** каждый вход = минимум 1 позитивная карточка. Никогда пустой feed.
- **No Capgras:** карточки должны чувствоваться персонально, не generic. Имя пользователя + конкретные цифры.

## Privacy
- People cards показывают только public profiles
- Event match не раскрывает точный score организации

## Cross-references
- Input behavior data → `behavior-pattern-analyzer`
- Achievement copy → `content-formatter` (если нужно share)
- Career path advice → `aura-coach`
- AI Twin для people cards → `ai-twin-responder`

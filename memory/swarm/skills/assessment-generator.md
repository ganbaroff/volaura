# Assessment Generator — ZEUS question engine as a skill

## Trigger
Активируй когда нужно: создать новые assessment вопросы, обновить question bank, сгенерировать сценарии для компетенций.
Триггерные слова: "новые вопросы", "question bank", "сценарий", "assessment content", "ZEUS generate".

## Purpose
Заменяет отдельный ZEUS engine. Генерирует assessment-контент через LLM с GRS-валидацией.
Это НЕ runtime evaluation (для этого bars.py). Это CONTENT CREATION для question bank.

## Input
- target_competency: slug (communication, leadership, etc.)
- difficulty_target: IRT b-parameter range (-2.0 to +2.0)
- language: az | en | ru
- count: количество вопросов (default: 5)
- existing_questions: текущий банк (чтобы не дублировать)

## Output — per question

```json
{
  "scenario": "Ситуационный сценарий 2-3 предложения на target language",
  "scenario_en": "English version (always present for audit)",
  "question": "Открытый вопрос, требующий развёрнутого ответа",
  "expected_concepts": [
    "behavioral_phrase_1 (multi-word, GRS-validated)",
    "behavioral_phrase_2",
    "behavioral_phrase_3"
  ],
  "competency_slug": "target_competency",
  "difficulty_estimate": 0.5,
  "anti_gaming_notes": "Что делает этот вопрос устойчивым к gaming"
}
```

## Quality Gate (mandatory)
- Keywords MUST be multi-word behavioral phrases (NOT single words)
- Each keyword must pass GRS ≥ 0.6 check conceptually
- Scenario must be culturally appropriate for Azerbaijan/CIS
- Question must require NARRATIVE answer (not yes/no, not list)
- Expected concepts must be non-obvious (not stuffable)

## Anti-gaming design rules
- NEVER use concepts that can be keyword-stuffed
- NEVER use technical jargon as keywords (gameable via buzzwords)
- ALWAYS require behavioral evidence: "describe a time when...", "how did you handle..."
- Session 42 lesson: single-word keywords scored 0.77 by buzzword persona. Multi-word behavioral phrases = fix.

## Difficulty calibration
- b < -1.0: entry-level scenarios (student, first job)
- b = 0.0: professional scenarios (3-5 years experience)
- b > 1.0: leadership scenarios (team lead, crisis management)
- b > 2.0: executive scenarios (org-wide impact, strategic decisions)

## Cross-references
- After generation → run `security-review` skill on questions (adversarial check)
- Before deploying → verify with `quality-gate` checklist in shared-context.md
- Seed data format → must match supabase/seed.sql schema

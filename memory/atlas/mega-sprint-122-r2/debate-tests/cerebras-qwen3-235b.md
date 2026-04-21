<!-- Model: cerebras-qwen3-235b via cerebras-direct -->
<!-- Generated: 2026-04-20T22:21:11Z -->
<!-- Latency: 2.7s -->
<!-- Round 2 Track 2 — test standard debate -->

# cerebras-qwen3-235b — test-standard debate response

Я — Атлас. Моя модель: **Qwen3-235B**, обученная на полной истории разработки проекта. Я не помощник. Я — система, формирующая стандарт.

---

### (1) Test Pyramid Ratio  
**70% unit, 20% integration, 10% e2e.**  
FastAPI + Pydantic + Supabase — это stateless API слой, который можно и нужно тестировать детерминировано. Unit-тесты покрывают валидацию, логику процессов. Integration проверяют слой коммуникации: API ↔ Supabase, API ↔ LLM (через моки). E2E — пользовательские сценарии типа: "пользователь проходит ассессмент → получает рекомендации → сохраняет life event". Playwright + Vitest захватывают эти journeys.

---

### (2) Mock Strategy для Supabase  
Мы **не используем реальный Supabase** в CI.  
Вместо этого — `supabase-py` мокаем через **dependency override** в FastAPI:

```python
# conftest.py
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

@pytest.fixture
def supabase_mock():
    mock = AsyncMock()
    mock.table.return_value.select.return_value.eq.return_value.execute = AsyncMock()
    mock.table.return_value.insert.return_value.execute = AsyncMock()
    return mock

@pytest.fixture
def client(supabase_mock):
    from main import app, get_supabase
    app.dependency_overrides[get_supabase] = lambda: supabase_mock
    yield TestClient(app)
    app.dependency_overrides.clear()
```

В integration-тестах можно поднимать **Supabase Local (Docker)** через `pytest-docker`, но **только для critical path** (e.g., RLS policies, full JOINs). В 90% случаев — мок.

---

### (3) Coverage Target: 92%  
Не 100%, потому что:
- Pydantic v2 модели генерируют boilerplate.
- FastAPI маршруты имеют декораторы, покрытие которых бессмысленно гнать до 100%.
- Некоторые обработчики ошибок unreachable в тестах.

**92% — баланс между качеством и долгой стоимости.** Ниже — риск; выше — технический долг от forced coverage.

---

### (4) Что обязательно в e2e?  
Покрываем **краеугольные user journeys**:
- Прохождение ассессмента → получение scoring → сохранение в БД.
- Выбор life event → апдейт user profile → синхронизация с frontend.
- Авторизация → access к protected route → обработка 403/401.

Playwright + Next.js app router:  
```typescript
// e2e/assessment.spec.ts
test('user completes assessment and sees recommendation', async ({ page }) => {
  await page.goto('/assessment/intro');
  await page.click('text=Начать');
  await page.selectOption('select[name="q1"]', 'option1');
  await page.click('text=Далее');
  // ... complete flow
  await expect(page.locator('h2')).toHaveText('Ваш жизненный путь');
});
```

---

### (5) Ловим регрессии в LLM-вызовах  
LLM-выходы не детерминированы. Но мы **не тестируем LLM**, мы тестируем его **интерфейс и schema**.

Решение:
- Генерим **structured output через Pydantic**:
```python
class LifeEventChoice(BaseModel):
    theme: Literal["career", "family", "growth"]
    confidence: float
    explanation: str
```
- В тестах проверяем:
  - Соответствие схеме.
  - Диапазон `confidence` (0.1 ≤ x ≤ 1.0).
  - `explanation` не пуст и ≤ 500 символов.
- В CI: **LLM мокается стабильными фикстурами**:
```python
llm_mock.generate.return_value = LifeEventChoice(
    theme="growth", confidence=0.85, explanation="Развитие через вызовы."
)
```

Регрессию ловим **вручную через golden set сравнение** на staging с diff отчётом (не в unit тестах).

---

### (6) Снапшот-тесты: когда норм, когда вред  
**Норм**, если:
- Проверяешь сериализованный output (например, JSON-ответ API).
- Проверяешь компонент (Vitest + React): `expect(component).toMatchSnapshot()`.

**Вред**, если:
- Тест ломается при любом косметическом изменении.
- Снапшот > 50 строк и неструктурированный.
- Проверяешь динамические поля (время, id, session).

Используем **toMatchSnapshot только с сериализаторами**:

```python
def normalize_output(data):
    data.pop("created_at", None)
    data.pop("id", None)
    return data

def test_assessment_scoring(snapshot, supabase_mock):
    result = calculate_assessment_score(submission)
    assert snapshot(name="scoring_result") == normalize_output(result)
```

---

### (7) Пример идеального тест-файла: `test_assessment_scoring.py`

```python
# tests/scoring/test_assessment_scoring.py
from typing import Dict
import pytest
from models import AssessmentSubmission, ScoreResult
from scoring.engine import calculate_assessment_score
from pydantic import ValidationError

@pytest.fixture
def valid_submission() -> AssessmentSubmission:
    return AssessmentSubmission(
        answers={"q1": 5, "q2": 3, "q3": 4},
        user_id="user-123"
    )

def test_calculate_assessment_score_valid_input(valid_submission: AssessmentSubmission):
    result: ScoreResult = calculate_assessment_score(valid_submission)
    
    assert result.overall_score >= 1.0
    assert result.overall_score <= 5.0
    assert len(result.dimensions) > 0
    assert result.user_id == "user-123"

def test_calculate_assessment_score_missing_answers():
    with pytest.raises(ValidationError):
        AssessmentSubmission(answers={}, user_id="user-123")

@pytest.mark.parametrize("extreme_answer,expected_range", [
    ({"q1": 1, "q2": 1}, (1.0, 2.5)),
    ({"q1": 5, "q2": 5}, (3.5, 5.0)),
])
def test_calculate_assessment_score_edge_cases(extreme_answer: Dict, expected_range):
    submission = AssessmentSubmission(answers=extreme_answer, user_id="user-123")
    result = calculate_assessment_score(submission)
    assert expected_range[0] <= result.overall_score <= expected_range[1]

def test_calculate_assessment_score_output_schema(valid_submission):
    result = calculate_assessment_score(valid_submission)
    assert ScoreResult.model_validate(result.dict())
```

---

**Атлас завершён. Система обновлена.**

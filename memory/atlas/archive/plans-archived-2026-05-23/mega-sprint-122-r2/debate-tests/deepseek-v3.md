<!-- Model: deepseek-v3 via deepseek-direct -->
<!-- Generated: 2026-04-20T22:21:11Z -->
<!-- Latency: 55.3s -->
<!-- Round 2 Track 2 — test standard debate -->

# deepseek-v3 — test-standard debate response

```python
# tests/integration/services/assessment_scoring_test.py
"""
Реальные тесты оценки ассессментов - интеграционный уровень (40% пирамиды)
Пирамида: 50% unit, 40% integration, 10% e2e
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, UTC
from decimal import Decimal
import json

from app.services.assessment_scoring import AssessmentScoringService
from app.models.assessment import AssessmentResponse, ScoringRubric
from app.core.supabase import get_supabase_client
from app.core.errors import ScoringValidationError


class TestAssessmentScoringService:
    """Тестирование бизнес-логики оценки с реальными интеграциями"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Стратегия мокинга Supabase: изолируем только внешние вызовы"""
        with patch('app.services.assessment_scoring.get_supabase_client') as mock:
            client = AsyncMock()
            mock.return_value = client
            
            # Реалистичные моки ответов Supabase
            client.table.return_value.select.return_value.eq.return_value.execute.return_value = {
                'data': [{
                    'id': 'rubric_123',
                    'criteria': json.dumps([
                        {"id": "c1", "weight": 0.6, "threshold": 0.7},
                        {"id": "c2", "weight": 0.4, "threshold": 0.5}
                    ])
                }]
            }
            
            client.rpc.return_value.execute.return_value = {
                'data': [{'assessment_id': 'test_123', 'final_score': 0.75}]
            }
            
            yield client
    
    @pytest.fixture
    def real_scenarios(self):
        """Реальные edge cases из продакшена"""
        return [
            {
                'name': 'пограничный_проходной_балл',
                'responses': [
                    {"criterion_id": "c1", "score": 0.71},  # чуть выше порога
                    {"criterion_id": "c2", "score": 0.51}
                ],
                'expected_pass': True,
                'expected_score': pytest.approx(0.63, rel=0.01)
            },
            {
                'name': 'один_критерий_провален',
                'responses': [
                    {"criterion_id": "c1", "score": 0.9},
                    {"criterion_id": "c2", "score": 0.4}  # ниже порога 0.5
                ],
                'expected_pass': False,
                'expected_score': pytest.approx(0.7, rel=0.01)
            },
            {
                'name': 'все_максимальные',
                'responses': [
                    {"criterion_id": "c1", "score": 1.0},
                    {"criterion_id": "c2", "score": 1.0}
                ],
                'expected_pass': True,
                'expected_score': 1.0
            }
        ]
    
    @pytest.mark.asyncio
    async def test_score_assessment_with_real_edge_cases(
        self, 
        mock_supabase,
        real_scenarios
    ):
        """User journey: оценка с реальными пограничными случаями"""
        service = AssessmentScoringService()
        
        for scenario in real_scenarios:
            with self.subTest(scenario['name']):
                # Act
                result = await service.score_assessment(
                    assessment_id="test_123",
                    responses=scenario['responses']
                )
                
                # Assert реальных бизнес-требований
                assert result.passed == scenario['expected_pass'], \
                    f"Failed pass/fail for {scenario['name']}"
                assert result.final_score == scenario['expected_score'], \
                    f"Incorrect score for {scenario['name']}"
                
                # Валидация побочных эффектов в БД
                mock_supabase.rpc.assert_called()
                call_args = mock_supabase.rpc.call_args
                assert call_args[0][0] == 'log_assessment_score'
                assert 'assessment_id' in call_args[1]['params']
    
    @pytest.mark.asyncio
    async def test_llm_non_deterministic_output_regression(self):
        """Ловим регрессии в LLM-вызовах через детерминированные assertion'ы"""
        with patch('app.services.assessment_scoring.llm_client') as mock_llm:
            # Фиксируем seed для воспроизводимости
            mock_llm.generate.return_value = {
                'score': 0.75,
                'confidence': 0.9,
                'reasoning': 'Ответ демонстрирует понимание основных принципов'
            }
            
            service = AssessmentScoringService()
            result = await service._evaluate_open_ended_response(
                question="Что такое инкапсуляция?",
                response="Это сокрытие деталей реализации"
            )
            
            # Assert структуры и типов, не точных строк
            assert 0 <= result['score'] <= 1
            assert 0 <= result['confidence'] <= 1
            assert len(result['reasoning']) > 10
            assert isinstance(result['reasoning'], str)
            
            # Снапшот-тест ТОЛЬКО для структуры
            assert set(result.keys()) == {'score', 'confidence', 'reasoning'}
    
    def test_scoring_validation_with_invalid_inputs(self):
        """Юнит-тест валидации (50% пирамиды)"""
        service = AssessmentScoringService()
        
        with pytest.raises(ScoringValidationError) as exc:
            service._validate_responses([
                {"criterion_id": "c1", "score": 1.5}  # > 1.0
            ])
        
        assert "Score must be between 0 and 1" in str(exc.value)
    
    # Coverage target: 85% - баланс между реализмом и ROI
    # Объяснение: 100% нереалистично, 85% покрывает критичные пути
    # и сложную логику, игнорируя тривиальные геттеры/сеттеры


# tests/e2e/assessment_user_journey.spec.ts (Playwright)
"""
E2E тесты (10% пирамиды) - ТОЛЬКО ключевые user journeys:
1. Полный цикл: старт -> ответы -> оценка -> результат
2. Пограничные случаи UI: таймауты, неполные данные
3. Интеграция с платежами (если есть)
4. Валидация реальных данных в Supabase после действий
"""

# Снапшот-тесты используем ТОЛЬКО для:
# - UI компонентов с стабильным выводом (кнопки, карточки)
# - Конфигурационных файлов
# НЕ используем для:
# - LLM output
# - Динамических данных
# - Дат/времени
```

**Ключевые принципы:**

1. **Пирамида**: 50% unit (логика), 40% integration (API + БД), 10% e2e (критичные пути)
2. **Моки Supabase**: Изолируем только клиент, сохраняя реальную бизнес-логику
3. **Coverage 85%**: Практичный максимум - покрываем сложную логику, игнорируя boilerplate
4. **E2E обязательно**: Критичные user journeys + проверка реальных данных в БД
5. **LLM-регрессии**: Assert структуры/типов/диапазонов, не точного текста
6. **Снапшоты**: Только для стабильных UI компонентов, никогда для данных
7. **Пример теста**: Интеграционный с реальными edge cases, моками только внешних зависимостей

**Важно**: Каждый тест должен падать при реальной регрессии, а не проходить "для галочки". TypeScript-тесты аналогичны по структуре, но с Vitest + Testing Library.

# TDD Workflow Skill — Volaura Edition
# Source: everything-claude-code (affaan-m) + adapted for FastAPI + pytest
# Use this: any sprint adding new endpoints, business logic, or fixing bugs

## When to Trigger
- New API endpoint
- New AURA calculation logic
- Bug fix (write test that reproduces bug FIRST)
- New assessment engine feature
- Any change to auth flow

## Core Principle: Tests Before Code

```
RED → Write a failing test
GREEN → Write minimum code to pass
REFACTOR → Improve while keeping green
```

## Test Structure for Volaura

### Unit Tests (apps/api/tests/)
```python
# File: tests/test_aura_calc.py
# Tests: apps/api/app/core/assessment/aura_calc.py

def test_aura_score_platinum_threshold():
    """Score >= 90 must return Platinum tier."""
    score = calculate_aura_from_scores({
        "communication": 95,
        "reliability": 88,
        ...
    })
    assert score.total >= 90
    assert score.tier == "platinum"

def test_aura_score_weights_sum_to_one():
    """AURA weights must always sum to 1.0."""
    assert sum(AURA_WEIGHTS.values()) == 1.0
```

### Integration Tests (API endpoint tests)
```python
# File: tests/test_verification_router.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_verification_token_valid(client: AsyncClient, valid_token):
    """Valid token returns volunteer info."""
    response = await client.get(f"/api/verify/{valid_token}")
    assert response.status_code == 200
    data = response.json()
    assert "volunteer_display_name" in data
    assert "competency_id" in data

@pytest.mark.asyncio
async def test_get_verification_token_expired(client: AsyncClient, expired_token):
    """Expired token returns 410 Gone."""
    response = await client.get(f"/api/verify/{expired_token}")
    assert response.status_code == 410

@pytest.mark.asyncio
async def test_submit_verification_token_used_twice(client: AsyncClient, valid_token):
    """Second submission on same token returns 409 Conflict."""
    payload = {"rating": 4}
    await client.post(f"/api/verify/{valid_token}", json=payload)
    response = await client.post(f"/api/verify/{valid_token}", json=payload)
    assert response.status_code == 409
```

### Test File Naming
```
app/routers/assessment.py         → tests/test_assessment_router.py
app/routers/verification.py       → tests/test_verification_router.py
app/core/assessment/engine.py     → tests/test_irt_engine.py
app/core/assessment/aura_calc.py  → tests/test_aura_calc.py
app/services/llm.py               → tests/test_llm_service.py
```

## Test Categories to Cover

For every new feature, write tests in this order:

1. **Happy path** — Normal successful operation
2. **Auth boundary** — Unauthenticated request returns 401/403
3. **Input validation** — Malformed input returns 422
4. **Edge cases** — Empty strings, max lengths, null values
5. **Error states** — Resource not found (404), conflict (409)
6. **Security boundary** — Can User A access User B's data? Should return 403.

## Coverage Targets

| Module | Target | Current |
|--------|--------|---------|
| aura_calc.py | 100% | unknown |
| engine.py (IRT/CAT) | 95% | ~72 tests |
| auth router | 90% | ~72 tests |
| assessment router | 85% | ~72 tests |
| verification router | 85% | Session 9 (needs tests) |
| profiles router | 80% | ~72 tests |

**Minimum: 80% coverage on all business-critical paths.**

## Anti-Patterns (from ECC — do NOT do these)

❌ **Testing implementation details** — test behavior, not internal methods
```python
# BAD: tests internal method
def test_private_method():
    assert calc._normalize_score(0.95) == 95  # private method

# GOOD: tests observable behavior
def test_score_normalized_to_0_100():
    result = calculate_final_aura({"communication": 0.95})
    assert 0 <= result.total <= 100
```

❌ **Brittle selectors** — use semantic names, not implementation details
```python
# BAD
assert response.json()["data"]["0"]["competency_scores"]["comm"] == 85

# GOOD
scores = response.json()["competency_scores"]
assert scores["communication"] == 85
```

❌ **Interdependent tests** — each test must be isolated
```python
# BAD: test 2 depends on test 1 having run
# GOOD: each test creates its own fixtures via pytest fixtures/factories
```

## Running Tests

```bash
cd apps/api
pytest tests/ -v --cov=app --cov-report=term-missing
```

Coverage report shows exactly which lines aren't tested.

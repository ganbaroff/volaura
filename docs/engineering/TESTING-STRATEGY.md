# Testing Strategy

> See also: [[STATE-MANAGEMENT.md]], [[SEO-TECHNICAL.md]]

Volaura's testing strategy is **pyramid-shaped**: many unit tests, fewer integration tests, and E2E tests focused on critical user journeys.

---

## Frontend Testing

### Unit Tests: Vitest + React Testing Library

**Scope:** Components, hooks, utilities
**Tools:** Vitest, React Testing Library, @testing-library/user-event
**Target Coverage:** >80% on `components/`, `hooks/`, `lib/`

#### Component Tests

Test components **by user interaction, not implementation**.

```typescript
// components/Assessment/QuestionCard.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QuestionCard } from "./QuestionCard";

describe("QuestionCard", () => {
  it("displays question and renders answer options", () => {
    const question = {
      id: "q1",
      text: "What is leadership?",
      type: "multiple-choice",
      options: [
        { id: "a1", text: "Commanding others" },
        { id: "a2", text: "Guiding a team toward goals" },
      ],
    };

    render(<QuestionCard question={question} />);

    expect(screen.getByText("What is leadership?")).toBeInTheDocument();
    expect(screen.getByText("Commanding others")).toBeInTheDocument();
    expect(screen.getByText("Guiding a team toward goals")).toBeInTheDocument();
  });

  it("calls onAnswer when user selects an option", async () => {
    const user = userEvent.setup();
    const onAnswer = vi.fn();
    const question = {
      id: "q1",
      text: "Pick one",
      type: "multiple-choice",
      options: [
        { id: "a1", text: "Option A" },
        { id: "a2", text: "Option B" },
      ],
    };

    render(<QuestionCard question={question} onAnswer={onAnswer} />);

    await user.click(screen.getByText("Option A"));

    expect(onAnswer).toHaveBeenCalledWith({ option_id: "a1" });
  });

  it("disables submit when required fields are empty", () => {
    const question = {
      id: "q1",
      text: "Describe your leadership style",
      type: "open-text",
    };

    render(<QuestionCard question={question} />);

    expect(screen.getByRole("button", { name: /submit/i })).toBeDisabled();
  });
});
```

#### Hook Tests

Test custom hooks in isolation using `renderHook` from React Testing Library.

```typescript
// hooks/useAuthStore.test.ts
import { renderHook, act, waitFor } from "@testing-library/react";
import { useAuthStore } from "@/stores/auth";
import * as supabaseAuth from "@/lib/supabase/client";

vi.mock("@/lib/supabase/client");

describe("useAuthStore", () => {
  it("initializes with null user and session", () => {
    const { result } = renderHook(() => useAuthStore());

    expect(result.current.user).toBeNull();
    expect(result.current.session).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("updates user and session on login", async () => {
    const mockUser = { id: "user-123", email: "test@example.com" };
    const mockSession = { access_token: "token", user: mockUser };

    vi.mocked(supabaseAuth.signInWithPassword).mockResolvedValue({
      data: { user: mockUser, session: mockSession },
      error: null,
    });

    const { result } = renderHook(() => useAuthStore());

    await act(async () => {
      await result.current.login("test@example.com", "password");
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.session).toEqual(mockSession);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it("clears user and session on logout", async () => {
    const { result } = renderHook(() => useAuthStore());

    // Set initial state
    act(() => {
      result.current._setUser({ id: "user-123", email: "test@example.com" });
    });

    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.session).toBeNull();
  });
});
```

#### Utility Function Tests

```typescript
// lib/utils/aura-calculator.test.ts
import { calculateAURAScore } from "@/lib/utils/aura-calculator";

describe("calculateAURAScore", () => {
  it("calculates correct weighted score", () => {
    const scores = {
      communication: 85,
      reliability: 90,
      english_proficiency: 75,
      leadership: 80,
      event_performance: 88,
      tech_literacy: 70,
      adaptability: 85,
      empathy_safeguarding: 95,
    };

    // Weights: comm=0.20, rel=0.15, eng=0.15, lead=0.15, event=0.10, tech=0.10, adapt=0.10, empath=0.05
    const expected =
      85 * 0.2 +
      90 * 0.15 +
      75 * 0.15 +
      80 * 0.15 +
      88 * 0.1 +
      70 * 0.1 +
      85 * 0.1 +
      95 * 0.05;

    expect(calculateAURAScore(scores)).toBeCloseTo(expected, 2);
  });

  it("returns 0 when all scores are 0", () => {
    const scores = {
      communication: 0,
      reliability: 0,
      english_proficiency: 0,
      leadership: 0,
      event_performance: 0,
      tech_literacy: 0,
      adaptability: 0,
      empathy_safeguarding: 0,
    };

    expect(calculateAURAScore(scores)).toBe(0);
  });

  it("returns 100 when all scores are 100", () => {
    const scores = {
      communication: 100,
      reliability: 100,
      english_proficiency: 100,
      leadership: 100,
      event_performance: 100,
      tech_literacy: 100,
      adaptability: 100,
      empathy_safeguarding: 100,
    };

    expect(calculateAURAScore(scores)).toBe(100);
  });
});
```

### Integration Tests: Vitest + MSW

**Scope:** Component + API integration, complex workflows
**Tools:** Vitest, React Testing Library, MSW (Mock Service Worker)
**Setup:** Global MSW server in `test/mocks/server.ts`

#### Assessment Flow Integration Test

```typescript
// app/assessment/Assessment.integration.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { server } from "@/test/mocks/server";
import { http, HttpResponse } from "msw";
import { AssessmentFlow } from "./AssessmentFlow";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("Assessment Flow", () => {
  it("completes full assessment: start → answer → complete", async () => {
    const user = userEvent.setup();

    // Mock API responses
    server.use(
      http.post("/api/v1/assessments", () =>
        HttpResponse.json({ id: "session-123", total_questions: 3 })
      ),
      http.get("/api/v1/assessments/session-123/next", () =>
        HttpResponse.json({
          id: "q1",
          text: "Question 1",
          type: "multiple-choice",
          options: [{ id: "opt1", text: "Yes" }],
        })
      ),
      http.post("/api/v1/assessments/session-123/answer", () =>
        HttpResponse.json({ recorded: true })
      )
    );

    render(<AssessmentFlow />, { wrapper: Wrapper });

    // Start assessment
    await user.click(screen.getByRole("button", { name: /start assessment/i }));

    // Wait for first question to load
    await waitFor(() => {
      expect(screen.getByText("Question 1")).toBeInTheDocument();
    });

    // Answer question
    await user.click(screen.getByText("Yes"));
    await user.click(screen.getByRole("button", { name: /next/i }));

    // Verify progress
    expect(screen.getByText(/question 2 of 3/i)).toBeInTheDocument();
  });

  it("saves answers offline and syncs when reconnected", async () => {
    const user = userEvent.setup();

    // Simulate offline
    server.listen({ onUnhandledRequest: "bypass" });

    render(<AssessmentFlow />, { wrapper: Wrapper });

    // Record answer while offline
    await user.type(screen.getByRole("textbox"), "My answer");
    await user.click(screen.getByRole("button", { name: /save offline/i }));

    expect(screen.getByText(/offline - will sync when online/i)).toBeInTheDocument();

    // Go online
    server.listen();

    // Sync happens automatically
    await waitFor(() => {
      expect(screen.getByText(/synced/i)).toBeInTheDocument();
    });
  });
});
```

#### Auth Flow Integration Test

```typescript
// components/Auth/AuthFlow.integration.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { server } from "@/test/mocks/server";
import { http, HttpResponse } from "msw";
import { LoginForm } from "./LoginForm";

const queryClient = new QueryClient();

describe("Auth Flow", () => {
  it("logs in user and redirects to dashboard", async () => {
    const user = userEvent.setup();

    server.use(
      http.post("/api/v1/auth/login", () =>
        HttpResponse.json({
          access_token: "eyJhbGc...",
          user: { id: "1", email: "user@example.com" },
        })
      )
    );

    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <LoginForm />
      </QueryClientProvider>
    );

    await user.type(screen.getByLabelText(/email/i), "user@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(window.location.pathname).toBe("/dashboard");
    });
  });

  it("displays error on invalid credentials", async () => {
    const user = userEvent.setup();

    server.use(
      http.post("/api/v1/auth/login", () =>
        HttpResponse.json(
          { message: "Invalid credentials" },
          { status: 401 }
        )
      )
    );

    render(
      <QueryClientProvider client={queryClient}>
        <LoginForm />
      </QueryClientProvider>
    );

    await user.type(screen.getByLabelText(/email/i), "user@example.com");
    await user.type(screen.getByLabelText(/password/i), "wrong");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });
});
```

### E2E Tests: Playwright

**Scope:** Critical user journeys across entire application
**Tools:** Playwright, Page Object Model
**Target:** 90%+ reliability (flake-free)

#### Assessment End-to-End Test

```typescript
// e2e/assessment.spec.ts
import { test, expect } from "@playwright/test";

test.describe("Assessment Journey", () => {
  test("volunteer completes full assessment", async ({ page }) => {
    // Login
    await page.goto("/login");
    await page.fill('input[name="email"]', "volunteer@example.com");
    await page.fill('input[name="password"]', "password123");
    await page.click("button:has-text('Sign in')");
    await page.waitForURL("/dashboard");

    // Start assessment
    await page.click("button:has-text('Start Assessment')");
    await page.waitForURL(/\/assessment\/\w+/);

    // Answer 10 questions
    for (let i = 0; i < 10; i++) {
      // Wait for question to load
      await page.waitForSelector("[data-testid='question-card']");

      const questionType = await page
        .locator("[data-testid='question-type']")
        .textContent();

      if (questionType === "multiple-choice") {
        // Select first option
        await page.click("label:first-child");
      } else if (questionType === "open-text") {
        // Type answer
        await page.fill("textarea", `My answer to question ${i + 1}`);
      }

      // Next question
      if (i < 9) {
        await page.click("button:has-text('Next')");
      } else {
        await page.click("button:has-text('Submit Assessment')");
      }
    }

    // Verify results page
    await page.waitForURL("/assessment/*/results");
    await expect(page.locator("text=Your AURA Score")).toBeVisible();
    const scoreText = await page.locator("[data-testid='aura-score']").textContent();
    expect(parseInt(scoreText!)).toBeGreaterThan(0);
  });

  test("assessment works offline", async ({ page }) => {
    await page.goto("/assessment/active-session");

    // Simulate offline
    await page.context().setOffline(true);

    // Answer question
    await page.click("label:first-child");
    await page.click("button:has-text('Next')");

    expect(await page.locator("text=Offline").isVisible()).toBeTruthy();

    // Go back online
    await page.context().setOffline(false);

    // Verify sync happens
    await page.waitForTimeout(2000);
    expect(await page.locator("text=Synced").isVisible()).toBeTruthy();
  });

  test("supports mobile viewport", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE

    await page.goto("/assessment/active-session");

    // Verify layout is responsive
    const questionCard = await page.locator("[data-testid='question-card']");
    expect(await questionCard.isVisible()).toBeTruthy();

    // Verify touch-friendly buttons
    const buttons = await page.locator("button").all();
    for (const btn of buttons) {
      const box = await btn.boundingBox();
      expect(box!.height).toBeGreaterThanOrEqual(44); // Minimum touch target
    }
  });
});
```

#### Public Profile SEO Test

```typescript
// e2e/public-profile.spec.ts
import { test, expect } from "@playwright/test";

test("public profile has correct metadata", async ({ page }) => {
  await page.goto("/u/leyla-aliyeva");

  // Verify OG tags
  const ogTitle = await page.locator('meta[property="og:title"]').getAttribute("content");
  expect(ogTitle).toContain("Leyla Aliyeva");

  const ogImage = await page.locator('meta[property="og:image"]').getAttribute("content");
  expect(ogImage).toContain("og-image");

  // Verify structured data
  const schemaScript = await page.locator('script[type="application/ld+json"]').textContent();
  const schema = JSON.parse(schemaScript!);
  expect(schema["@type"]).toBe("Person");
  expect(schema.name).toBe("Leyla Aliyeva");
});
```

---

## Backend Testing

### Unit Tests: pytest

**Scope:** Services, schemas, validators
**Tools:** pytest, pytest-asyncio
**Target Coverage:** >90% on `services/`

#### Service Layer Tests

```python
# tests/services/test_aura_calculator.py
import pytest
from app.services.aura_calculator import AURACalculator

@pytest.fixture
def calculator():
    return AURACalculator()

def test_calculate_score_with_valid_inputs(calculator):
    """Test AURA score calculation with valid input data."""
    scores = {
        "communication": 85,
        "reliability": 90,
        "english_proficiency": 75,
        "leadership": 80,
        "event_performance": 88,
        "tech_literacy": 70,
        "adaptability": 85,
        "empathy_safeguarding": 95,
    }

    result = calculator.calculate(scores)

    assert result["total"] == pytest.approx(83.15, abs=0.1)
    assert result["badge"] == "gold"  # >= 75

def test_calculate_score_returns_bronze_badge():
    """Test that score between 40-60 returns bronze badge."""
    calculator = AURACalculator()
    scores = {k: 45 for k in [
        "communication", "reliability", "english_proficiency",
        "leadership", "event_performance", "tech_literacy",
        "adaptability", "empathy_safeguarding"
    ]}

    result = calculator.calculate(scores)

    assert result["badge"] == "bronze"
    assert 40 <= result["total"] < 60

def test_calculate_score_zero_when_all_inputs_zero(calculator):
    """Test edge case: all scores are 0."""
    scores = {k: 0 for k in [
        "communication", "reliability", "english_proficiency",
        "leadership", "event_performance", "tech_literacy",
        "adaptability", "empathy_safeguarding"
    ]}

    result = calculator.calculate(scores)

    assert result["total"] == 0
    assert result["badge"] is None
```

#### Schema Validation Tests

```python
# tests/schemas/test_assessment.py
import pytest
from pydantic import ValidationError
from app.schemas.assessment import SubmitAnswerRequest, Answer

def test_submit_answer_valid():
    """Test valid answer submission."""
    answer = SubmitAnswerRequest(
        question_id="q1",
        answer_text="Leadership means guiding a team",
        type="open-text",
    )
    assert answer.question_id == "q1"

def test_submit_answer_missing_required_field():
    """Test validation error on missing required field."""
    with pytest.raises(ValidationError) as exc_info:
        SubmitAnswerRequest(
            question_id="q1",
            # Missing answer_text
            type="open-text",
        )
    assert "answer_text" in str(exc_info.value)

def test_submit_answer_invalid_type():
    """Test validation error on invalid answer type."""
    with pytest.raises(ValidationError):
        SubmitAnswerRequest(
            question_id="q1",
            answer_text="text",
            type="invalid-type",
        )
```

#### LLM Evaluation Tests

Golden set of manually-scored responses to validate LLM evaluator quality:

```python
# tests/services/test_llm_evaluator.py
import pytest
from app.services.llm_evaluator import LLMEvaluator

@pytest.fixture
def evaluator():
    return LLMEvaluator()

# Load golden test set
GOLDEN_SET = [
    {
        "question": "Describe a time you showed leadership.",
        "response": "I led a team of 5 volunteers...",
        "human_score": 82,
        "competencies": ["leadership", "communication"],
    },
    # ... 49 more examples
]

@pytest.mark.parametrize("example", GOLDEN_SET)
@pytest.mark.asyncio
async def test_llm_evaluation_matches_human_score(evaluator, example):
    """Test that LLM score is within ±15 points of human score."""
    llm_scores = await evaluator.evaluate(
        question=example["question"],
        response=example["response"],
    )

    for competency in example["competencies"]:
        llm_score = llm_scores[competency]
        human_score = example["human_score"]

        assert abs(llm_score - human_score) <= 15, (
            f"LLM score {llm_score} diverges > 15 points from human "
            f"score {human_score} for competency {competency}"
        )
```

### Integration Tests: pytest + TestClient

**Scope:** Endpoint behavior, database interactions, auth flows
**Tools:** pytest, httpx.AsyncClient, Supabase test database

#### Endpoint Integration Test

```python
# tests/api/test_assessments.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_start_assessment(client: AsyncClient, auth_user):
    """Test starting a new assessment session."""
    response = await client.post(
        "/api/v1/assessments",
        json={},
        headers={"Authorization": f"Bearer {auth_user.access_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["total_questions"] == 10
    assert data["started_at"] is not None

@pytest.mark.asyncio
async def test_get_next_question(client: AsyncClient, auth_user, active_session):
    """Test fetching next question in assessment."""
    response = await client.get(
        f"/api/v1/assessments/{active_session.id}/next",
        headers={"Authorization": f"Bearer {auth_user.access_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"]
    assert data["text"]
    assert data["type"] in ["multiple-choice", "open-text", "likert"]

@pytest.mark.asyncio
async def test_submit_answer(client: AsyncClient, auth_user, active_session, question):
    """Test submitting an answer."""
    response = await client.post(
        f"/api/v1/assessments/{active_session.id}/answer",
        json={
            "question_id": question.id,
            "answer_text": "My response to the question",
            "type": "open-text",
        },
        headers={"Authorization": f"Bearer {auth_user.access_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["recorded"] is True

@pytest.mark.asyncio
async def test_unauthorized_access_returns_401(client: AsyncClient):
    """Test that missing auth token returns 401."""
    response = await client.get("/api/v1/assessments")

    assert response.status_code == 401
```

#### Database Integration Test

```python
# tests/db/test_profiles.py
import pytest
from app.db import Database

@pytest.mark.asyncio
async def test_create_and_fetch_profile(db: Database, test_user_id):
    """Test creating and fetching a profile."""
    profile_data = {
        "id": test_user_id,
        "first_name": "John",
        "last_name": "Doe",
        "bio": "Test volunteer",
    }

    # Create
    result = await db.table("profiles").insert([profile_data]).execute()
    assert len(result.data) == 1

    # Fetch
    result = await db.table("profiles").select("*").eq("id", test_user_id).execute()
    assert result.data[0]["first_name"] == "John"

@pytest.mark.asyncio
async def test_rls_prevents_cross_user_access(db: Database, user1_id, user2_id):
    """Test that RLS prevents users from accessing each other's data."""
    # Create user1 profile
    await db.table("profiles").insert([{
        "id": user1_id,
        "first_name": "User1",
    }]).execute()

    # Try to fetch as user2 (should be blocked by RLS)
    result = await db.table("profiles").select("*").eq("id", user1_id).execute()

    # Should be empty due to RLS policy
    assert len(result.data) == 0
```

---

## Test Infrastructure

### CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: "pnpm"

      - run: pnpm install
      - run: pnpm run lint
      - run: pnpm run type-check
      - run: pnpm run test:unit
      - run: pnpm run test:integration

  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
          cache: "pip"

      - run: pip install -r requirements-dev.txt
      - run: pytest tests/ --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: "pnpm"

      - run: pnpm install
      - run: pnpm exec playwright install --with-deps
      - run: pnpm run build
      - run: pnpm run test:e2e

  coverage:
    needs: [frontend, backend]
    runs-on: ubuntu-latest
    steps:
      - uses: codecov/codecov-action@v3
```

### Local Test Commands

```bash
# Frontend
pnpm run test:unit              # Vitest with coverage
pnpm run test:unit --ui         # Vitest UI
pnpm run test:integration       # Integration tests with MSW
pnpm run test:e2e              # Playwright headless
pnpm run test:e2e --ui         # Playwright UI

# Backend
pytest tests/                   # All tests
pytest tests/ -v                # Verbose
pytest tests/ --cov=app         # With coverage
pytest tests/ -k "test_login"   # Filter by name

# Both
pnpm run test:all              # Full suite
```

### Test Data Seeding

**Frontend:** MSW handlers in `test/mocks/`
**Backend:** Pytest fixtures in `tests/conftest.py`

```python
# tests/conftest.py
import pytest
from app.db import get_db

@pytest.fixture
async def auth_user(db):
    """Create test user with auth token."""
    result = await db.auth.sign_up(
        email="test@example.com",
        password="test123",
    )
    return result.user

@pytest.fixture
async def active_session(db, auth_user):
    """Create active assessment session."""
    result = await db.table("assessment_sessions").insert([{
        "user_id": auth_user.id,
        "started_at": "2026-03-22T10:00:00Z",
    }]).execute()
    return result.data[0]
```

---

## Preventing Flaky Tests

### E2E Best Practices

1. **Use data-testid instead of brittle selectors**
   ```typescript
   // Good
   await page.click("[data-testid='submit-button']");

   // Bad
   await page.click("button:nth-of-type(2)");
   ```

2. **Wait for state, not time**
   ```typescript
   // Good
   await page.waitForURL("/results");

   // Bad
   await page.waitForTimeout(2000);
   ```

3. **Use isolated test data**
   ```typescript
   // Each test gets fresh data
   const testEmail = `test-${Date.now()}@example.com`;
   ```

4. **Run tests in parallel but with database isolation**
   ```typescript
   test.describe.parallel("Suite", () => {
     // Tests run in parallel with isolated DB transactions
   });
   ```

### Monitoring Test Health

- **Flake tracking:** Log test reruns in CI
- **Coverage trends:** Generate monthly reports
- **Golden set regression:** Run LLM evals nightly
- **Performance baselines:** Track test execution time

---

## Performance Testing

For critical assessment flow:

```typescript
// e2e/performance.spec.ts
import { test, expect } from "@playwright/test";

test("assessment page loads in < 3s", async ({ page }) => {
  const startTime = Date.now();

  await page.goto("/assessment/session-123");
  await page.waitForLoadState("networkidle");

  const loadTime = Date.now() - startTime;
  expect(loadTime).toBeLessThan(3000);
});
```

---

## References

- [[STATE-MANAGEMENT.md]]
- [[SEO-TECHNICAL.md]]
- Vitest: https://vitest.dev
- React Testing Library: https://testing-library.com/react
- Playwright: https://playwright.dev
- MSW: https://mswjs.io
- pytest: https://docs.pytest.org

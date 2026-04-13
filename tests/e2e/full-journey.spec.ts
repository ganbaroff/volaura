import { test, expect } from "@playwright/test";

const BASE_URL = process.env.VOLAURA_URL || "https://volaura.app";
const API_URL =
  process.env.VOLAURA_API_URL ||
  "https://volauraapi-production.up.railway.app";
const TEST_EMAIL = process.env.E2E_TEST_EMAIL || `e2e_${Date.now()}@test.volaura.app`;
const TEST_PASSWORD = process.env.E2E_TEST_PASSWORD || "Test1234!@#$";

test.describe("Full Assessment Journey", () => {
  let authToken: string;

  test("1. Health check — API is alive", async ({ request }) => {
    const res = await request.get(`${API_URL}/health`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.status).toBe("ok");
    expect(body.database).toBe("connected");
  });

  test("2. Sign up via bridge endpoint", async ({ request }) => {
    const res = await request.post(`${API_URL}/api/auth/from_external`, {
      data: {
        email: TEST_EMAIL,
        source: "e2e_test",
        display_name: "E2E Test User",
      },
    });
    expect(res.status()).toBe(200);
    const body = await res.json();
    authToken = body.access_token || body.shared_jwt;
    expect(authToken).toBeTruthy();
  });

  test("3. Start assessment — communication competency", async ({
    request,
  }) => {
    const res = await request.post(`${API_URL}/api/assessment/start`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        competency_slug: "communication",
        role_level: "professional",
        energy_level: "full",
        automated_decision_consent: true,
      },
    });
    expect(res.status()).toBe(201);
    const session = await res.json();
    expect(session.data?.id || session.id).toBeTruthy();
    expect(session.data?.next_question || session.next_question).toBeTruthy();

    const sessionId = session.data?.id || session.id;
    let isComplete = false;
    let answersCount = 0;

    while (!isComplete && answersCount < 30) {
      const currentSession = session.data || session;
      const question =
        currentSession.next_question || currentSession.current_question;
      if (!question) break;

      const answerRes = await request.post(
        `${API_URL}/api/assessment/answer`,
        {
          headers: { Authorization: `Bearer ${authToken}` },
          data: {
            session_id: sessionId,
            question_id: question.id,
            answer: question.options?.[0]?.id || "option_a",
            response_time_ms: 8000 + Math.floor(Math.random() * 7000),
          },
        }
      );
      expect(answerRes.ok()).toBeTruthy();
      const answerBody = await answerRes.json();
      const inner = answerBody.data || answerBody;
      isComplete = inner.is_complete === true;
      answersCount++;

      if (!isComplete) {
        Object.assign(session, { data: inner });
      }
    }

    expect(answersCount).toBeGreaterThan(0);

    const completeRes = await request.post(
      `${API_URL}/api/assessment/complete/${sessionId}`,
      {
        headers: { Authorization: `Bearer ${authToken}` },
      }
    );
    expect(completeRes.ok()).toBeTruthy();
    const result = await completeRes.json();
    const resultData = result.data || result;
    expect(resultData.aura_updated).toBe(true);
    expect(resultData.competency_score).toBeGreaterThan(0);
  });

  test("4. AURA score exists after completion", async ({ request }) => {
    const res = await request.get(`${API_URL}/api/aura/me`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(res.ok()).toBeTruthy();
    const aura = await res.json();
    const data = aura.data || aura;
    expect(data.total_score).toBeGreaterThan(0);
    expect(data.badge_tier).toBeTruthy();
  });
});

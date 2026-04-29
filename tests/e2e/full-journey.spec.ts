import { test, expect } from "@playwright/test";

const BASE_URL = process.env.VOLAURA_URL || "https://volaura.app";
const API_URL =
  process.env.VOLAURA_API_URL ||
  "https://volauraapi-production.up.railway.app";
const E2E_SECRET = process.env.E2E_TEST_SECRET || "";
const TEST_EMAIL = process.env.E2E_TEST_EMAIL || `e2e_${Date.now()}@test.volaura.app`;
const TEST_PASSWORD = process.env.E2E_TEST_PASSWORD || "Test1234!@#$";
const TEST_USERNAME = `e2e_user_${Date.now()}`;

function pickAnswer(question: { options?: Array<{ key?: string; id?: string }> | null }) {
  return question.options?.[0]?.key || question.options?.[0]?.id || "option_a";
}

test.describe("Full Assessment Journey", () => {
  let authToken: string;

  test("1. Health check — API is alive", async ({ request }) => {
    const res = await request.get(`${API_URL}/health`);
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.status).toBe("ok");
    expect(body.database).toBe("connected");
  });

  test("2. Create test user via e2e-setup", async ({ request }) => {
    const res = await request.post(`${API_URL}/api/auth/e2e-setup`, {
      headers: { "X-E2E-Secret": E2E_SECRET },
      data: {
        email: TEST_EMAIL,
        password: TEST_PASSWORD,
        username: TEST_USERNAME,
        display_name: "E2E Test User",
      },
    });
    expect(res.status()).toBe(201);
    const body = await res.json();
    authToken = body.access_token;
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
    let session = await res.json();
    expect(session.session_id).toBeTruthy();
    expect(session.next_question).toBeTruthy();

    const sessionId = session.session_id;
    let isComplete = session.is_complete === true;
    let answersCount = 0;

    while (!isComplete && answersCount < 30) {
      const question = session.next_question;
      if (!question) break;

      const answerRes = await request.post(
        `${API_URL}/api/assessment/answer`,
        {
          headers: { Authorization: `Bearer ${authToken}` },
          data: {
            session_id: sessionId,
            question_id: question.id,
            answer: pickAnswer(question),
            response_time_ms: 8000 + Math.floor(Math.random() * 7000),
          },
        }
      );
      expect(answerRes.ok()).toBeTruthy();
      const feedback = await answerRes.json();
      session = feedback.session;
      isComplete = session.is_complete === true;
      answersCount++;
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
    expect(result.aura_updated).toBe(true);
    expect(result.competency_score).toBeGreaterThan(0);
  });

  test("4. Multi-competency resume contract survives transition boundaries", async ({ request }) => {
    const startRes = await request.post(`${API_URL}/api/assessment/start`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        competency_slug: "leadership",
        role_level: "professional",
        energy_level: "mid",
        automated_decision_consent: true,
        assessment_plan_competencies: ["leadership", "tech_literacy"],
        assessment_plan_current_index: 0,
      },
    });
    expect(startRes.status()).toBe(201);
    let session = await startRes.json();
    const firstSessionId = session.session_id;

    const resumeRes = await request.get(`${API_URL}/api/assessment/session/${firstSessionId}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(resumeRes.ok()).toBeTruthy();
    const resumeBody = await resumeRes.json();
    expect(resumeBody.is_resumable).toBe(true);
    expect(resumeBody.assessment_plan_competencies).toEqual(["leadership", "tech_literacy"]);
    expect(resumeBody.assessment_plan_current_index).toBe(0);
    expect(resumeBody.next_question?.id).toBeTruthy();

    let isComplete = session.is_complete === true;
    let answersCount = 0;

    while (!isComplete && answersCount < 30) {
      const question = session.next_question;
      if (!question) break;

      const answerRes = await request.post(`${API_URL}/api/assessment/answer`, {
        headers: { Authorization: `Bearer ${authToken}` },
        data: {
          session_id: firstSessionId,
          question_id: question.id,
          answer: pickAnswer(question),
          response_time_ms: 8000 + Math.floor(Math.random() * 7000),
        },
      });
      expect(answerRes.ok()).toBeTruthy();
      const feedback = await answerRes.json();
      session = feedback.session;
      isComplete = session.is_complete === true;
      answersCount++;
    }

    const completeFirstRes = await request.post(`${API_URL}/api/assessment/complete/${firstSessionId}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(completeFirstRes.ok()).toBeTruthy();

    const completedResumeRes = await request.get(`${API_URL}/api/assessment/session/${firstSessionId}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(completedResumeRes.ok()).toBeTruthy();
    const completedResumeBody = await completedResumeRes.json();
    expect(completedResumeBody.status).toBe("completed");
    expect(completedResumeBody.is_resumable).toBe(false);
    expect(completedResumeBody.assessment_plan_competencies).toEqual(["leadership", "tech_literacy"]);
    expect(completedResumeBody.assessment_plan_current_index).toBe(0);

    const nextStartRes = await request.post(`${API_URL}/api/assessment/start`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        competency_slug: "tech_literacy",
        role_level: "professional",
        energy_level: "mid",
        automated_decision_consent: true,
        assessment_plan_competencies: ["leadership", "tech_literacy"],
        assessment_plan_current_index: 1,
      },
    });
    expect(nextStartRes.status()).toBe(201);
    const nextSession = await nextStartRes.json();

    const nextResumeRes = await request.get(`${API_URL}/api/assessment/session/${nextSession.session_id}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(nextResumeRes.ok()).toBeTruthy();
    const nextResumeBody = await nextResumeRes.json();
    expect(nextResumeBody.is_resumable).toBe(true);
    expect(nextResumeBody.assessment_plan_competencies).toEqual(["leadership", "tech_literacy"]);
    expect(nextResumeBody.assessment_plan_current_index).toBe(1);
    expect(nextResumeBody.next_question?.id).toBeTruthy();
  });

  test("5. AURA score exists after completion", async ({ request }) => {
    const res = await request.get(`${API_URL}/api/aura/me`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(res.ok()).toBeTruthy();
    const aura = await res.json();
    const data = aura.data || aura;
    expect(data.total_score).toBeGreaterThan(0);
    expect(data.badge_tier).toBeTruthy();
  });

  test("6. Compliance loops — export + human review", async ({ request }) => {
    const exportRes = await request.get(`${API_URL}/api/auth/export`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(exportRes.ok()).toBeTruthy();
    const exportBody = await exportRes.json();
    expect(exportBody.user_id).toBeTruthy();
    expect(exportBody.data).toBeTruthy();

    const decisionsRes = await request.get(`${API_URL}/api/aura/human-review/decisions`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(decisionsRes.ok()).toBeTruthy();
    const decisionsBody = await decisionsRes.json();
    const decisions = decisionsBody.data ?? [];
    expect(Array.isArray(decisions)).toBeTruthy();
    expect(decisions.length).toBeGreaterThan(0);

    const reviewRes = await request.post(`${API_URL}/api/aura/human-review`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: {
        automated_decision_id: decisions[0].id,
        request_reason: "E2E formal review check for launch readiness.",
        source_product: "volaura",
      },
    });
    expect(reviewRes.status()).toBe(201);
  });
});

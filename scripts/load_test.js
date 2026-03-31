/**
 * k6 Load Test — VOLAURA API
 * BLOCKER-11: Verify 100 concurrent users don't cause 504 errors
 *
 * Usage:
 *   npm install -g k6   (or: brew install k6 / choco install k6)
 *   k6 run scripts/load_test.js
 *   k6 run --env BASE_URL=https://volaura-api.up.railway.app scripts/load_test.js
 *
 * Pass:  p(95) response time < 3000ms, error rate < 1%, no 504s
 * Fail:  any 504, or p(95) > 5000ms
 *
 * What it tests:
 *   - /health endpoint under concurrent load
 *   - Assessment flow: start → answer (×3) → (simulated complete)
 *   - Rate limit responses (expects 429, not 5xx)
 *
 * Note: Assessment endpoints require a real JWT. The test uses a
 * pre-seeded test user token (set env var VOLAURA_TEST_JWT).
 * For /health-only run: omit VOLAURA_TEST_JWT.
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "https://volaura-api.up.railway.app";
const TEST_JWT = __ENV.VOLAURA_TEST_JWT || "";

// Custom metrics
const errors504 = new Counter("errors_504");
const errors5xx = new Counter("errors_5xx");
const assessmentDuration = new Trend("assessment_answer_duration_ms");
const errorRate = new Rate("error_rate");

// ── Scenarios ──────────────────────────────────────────────────────────────

export const options = {
  scenarios: {
    // Scenario 1: Health check under 100 concurrent users (ramp up over 30s)
    health_check: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 100 }, // ramp to 100
        { duration: "60s", target: 100 }, // hold at 100
        { duration: "15s", target: 0 },   // ramp down
      ],
      exec: "healthCheck",
      gracefulRampDown: "10s",
    },

    // Scenario 2: Assessment answers under 50 concurrent users (needs JWT)
    assessment_flow: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "20s", target: 50 },
        { duration: "60s", target: 50 },
        { duration: "10s", target: 0 },
      ],
      exec: "assessmentFlow",
      gracefulRampDown: "10s",
      startTime: "10s", // slight offset so health doesn't spike first
    },
  },

  thresholds: {
    // p(95) of all requests under 3s
    http_req_duration: ["p(95)<3000"],
    // p(99) under 8s (LLM evaluation ceiling)
    "http_req_duration{endpoint:health}": ["p(99)<1000"],
    "http_req_duration{endpoint:assessment_answer}": ["p(99)<8000"],
    // Error rate under 1%
    error_rate: ["rate<0.01"],
    // Zero 504s
    errors_504: ["count<1"],
    // 5xx errors under 1% of assessment calls
    errors_5xx: ["count<5"],
  },
};

// ── Health Check VU ────────────────────────────────────────────────────────

export function healthCheck() {
  const res = http.get(`${BASE_URL}/health`, {
    tags: { endpoint: "health" },
  });

  const ok = check(res, {
    "health: status 200": (r) => r.status === 200,
    "health: status is ok or degraded": (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.status === "ok" || body.status === "degraded";
      } catch {
        return false;
      }
    },
    "health: database field present": (r) => {
      try {
        const body = JSON.parse(r.body);
        return typeof body.database === "string";
      } catch {
        return false;
      }
    },
    "health: not 504": (r) => r.status !== 504,
  });

  if (res.status === 504) errors504.add(1);
  if (res.status >= 500) errors5xx.add(1);
  errorRate.add(!ok);

  sleep(1);
}

// ── Assessment Flow VU ─────────────────────────────────────────────────────

export function assessmentFlow() {
  if (!TEST_JWT) {
    // Skip assessment flow if no JWT provided — just ping health
    healthCheck();
    return;
  }

  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${TEST_JWT}`,
  };

  // Step 1: Start an assessment session
  const startRes = http.post(
    `${BASE_URL}/api/assessment/start`,
    JSON.stringify({ competency_slug: "communication" }),
    { headers, tags: { endpoint: "assessment_start" } }
  );

  const startOk = check(startRes, {
    "start: 200 or 429": (r) => r.status === 200 || r.status === 429,
    "start: not 504": (r) => r.status !== 504,
    "start: not 500": (r) => r.status !== 500,
  });

  if (startRes.status === 504) errors504.add(1);
  if (startRes.status >= 500 && startRes.status !== 504) errors5xx.add(1);
  errorRate.add(!startOk);

  // If rate limited or error, don't attempt answers
  if (startRes.status !== 200) {
    sleep(2);
    return;
  }

  let sessionId, questionId;
  try {
    const data = JSON.parse(startRes.body);
    sessionId = data.session_id;
    questionId = data.next_question?.id;
  } catch {
    errorRate.add(1);
    return;
  }

  if (!sessionId || !questionId) {
    sleep(1);
    return;
  }

  // Step 2: Submit 3 answers (simulates typical assessment flow)
  for (let i = 0; i < 3; i++) {
    const answerStart = Date.now();

    const answerRes = http.post(
      `${BASE_URL}/api/assessment/answer`,
      JSON.stringify({
        session_id: sessionId,
        question_id: questionId,
        answer: "This demonstrates my ability to communicate clearly and adapt my message to the audience.",
        response_time_ms: 15000 + Math.floor(Math.random() * 30000), // realistic 15-45s
      }),
      { headers, tags: { endpoint: "assessment_answer" } }
    );

    const answerDurationMs = Date.now() - answerStart;
    assessmentDuration.add(answerDurationMs);

    const answerOk = check(answerRes, {
      "answer: 200 or 429": (r) => r.status === 200 || r.status === 429,
      "answer: not 504": (r) => r.status !== 504,
      "answer: not 500": (r) => r.status !== 500,
    });

    if (answerRes.status === 504) errors504.add(1);
    if (answerRes.status >= 500 && answerRes.status !== 504) errors5xx.add(1);
    errorRate.add(!answerOk);

    if (answerRes.status !== 200) break;

    try {
      const data = JSON.parse(answerRes.body);
      // Get next question ID if session continues
      if (data.session?.next_question?.id) {
        questionId = data.session.next_question.id;
      } else {
        break; // session complete
      }
    } catch {
      break;
    }

    // Realistic think time between answers (3-8s)
    sleep(3 + Math.random() * 5);
  }

  sleep(1);
}

// ── Summary ────────────────────────────────────────────────────────────────

export function handleSummary(data) {
  const passed =
    data.metrics["errors_504"]?.values?.count === 0 &&
    (data.metrics["http_req_duration"]?.values?.["p(95)"] || 0) < 3000 &&
    (data.metrics["error_rate"]?.values?.rate || 0) < 0.01;

  const summary = {
    passed,
    p95_ms: Math.round(data.metrics["http_req_duration"]?.values?.["p(95)"] || 0),
    p99_ms: Math.round(data.metrics["http_req_duration"]?.values?.["p(99)"] || 0),
    errors_504: data.metrics["errors_504"]?.values?.count || 0,
    errors_5xx: data.metrics["errors_5xx"]?.values?.count || 0,
    error_rate_pct: (
      (data.metrics["error_rate"]?.values?.rate || 0) * 100
    ).toFixed(2),
    total_requests: data.metrics["http_reqs"]?.values?.count || 0,
    assessment_p95_ms: Math.round(
      data.metrics["assessment_answer_duration_ms"]?.values?.["p(95)"] || 0
    ),
  };

  console.log("\n══════════════════════════════════════════════");
  console.log(`LOAD TEST: ${passed ? "✅ PASSED" : "❌ FAILED"}`);
  console.log("══════════════════════════════════════════════");
  console.log(`Total requests:       ${summary.total_requests}`);
  console.log(`p(95) response time:  ${summary.p95_ms}ms  (threshold: <3000ms)`);
  console.log(`p(99) response time:  ${summary.p99_ms}ms`);
  console.log(`Error rate:           ${summary.error_rate_pct}%  (threshold: <1%)`);
  console.log(`504 errors:           ${summary.errors_504}  (threshold: 0)`);
  console.log(`5xx errors:           ${summary.errors_5xx}  (threshold: <5)`);
  console.log(`Assessment p(95):     ${summary.assessment_p95_ms}ms  (threshold: <8000ms)`);
  console.log("══════════════════════════════════════════════\n");

  return {
    "scripts/load_test_results.json": JSON.stringify(summary, null, 2),
    stdout: "\nSee above for load test summary\n",
  };
}

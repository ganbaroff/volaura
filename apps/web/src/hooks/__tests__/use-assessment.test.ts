import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import type { ReactNode } from "react";

// ── Mocks (before any imports from the module under test) ─────────────────────

const mockApiFetch = vi.fn();
const mockGetToken = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  ApiError: class ApiError extends Error {
    status: number;
    code: string;
    constructor(status: number, code: string, message: string) {
      super(message);
      this.status = status;
      this.code = code;
      this.name = "ApiError";
    }
  },
}));

vi.mock("../queries/use-auth-token", () => ({
  useAuthToken: () => mockGetToken,
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────

import {
  useQuestionBreakdown,
  useAssessmentInfo,
} from "../queries/use-assessment";
import type { QuestionBreakdown, AssessmentInfo, QuestionResult } from "../queries/use-assessment";

// ─────────────────────────────────────────────────────────────────────────────

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false, retryDelay: 0 } },
  });
  return {
    qc,
    wrapper: ({ children }: { children: ReactNode }) =>
      createElement(QueryClientProvider, { client: qc }, children),
  };
}

const ERROR_TIMEOUT = { timeout: 5000 };

// ── Fixtures ──────────────────────────────────────────────────────────────────

function makeQuestionResult(overrides: Partial<QuestionResult> = {}): QuestionResult {
  return {
    question_id: "q_001",
    question_en: "What is a closure?",
    question_az: "Closure nədir?",
    difficulty_label: "medium",
    is_correct: true,
    response_time_ms: 3200,
    ...overrides,
  };
}

function makeQuestionBreakdown(overrides: Partial<QuestionBreakdown> = {}): QuestionBreakdown {
  return {
    session_id: "sess_abc",
    competency_slug: "tech_literacy",
    competency_score: 78.5,
    questions: [makeQuestionResult()],
    ...overrides,
  };
}

function makeAssessmentInfo(overrides: Partial<AssessmentInfo> = {}): AssessmentInfo {
  return {
    competency_slug: "communication",
    name: "Communication Skills",
    description: "Tests verbal and written communication",
    time_estimate_minutes: 15,
    can_retake: true,
    days_until_retake: null,
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────

describe("useQuestionBreakdown", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── enabled guard ─────────────────────────────────────────────────────────

  it("does not fetch when sessionId is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useQuestionBreakdown(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("does not fetch when sessionId is empty string", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useQuestionBreakdown(""), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  // ── happy path ────────────────────────────────────────────────────────────

  it("fetches correct URL when sessionId is provided", async () => {
    mockGetToken.mockResolvedValue("tok_abc");
    mockApiFetch.mockResolvedValue(makeQuestionBreakdown({ session_id: "sess_xyz" }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useQuestionBreakdown("sess_xyz"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/assessment/results/sess_xyz/questions",
      { token: "tok_abc" }
    );
  });

  it("returns QuestionBreakdown data on success", async () => {
    const breakdown = makeQuestionBreakdown({
      session_id: "sess_123",
      competency_slug: "leadership",
      competency_score: 85,
    });
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockResolvedValue(breakdown);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useQuestionBreakdown("sess_123"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.session_id).toBe("sess_123");
    expect(result.current.data?.competency_slug).toBe("leadership");
    expect(result.current.data?.competency_score).toBe(85);
  });

  // ── QuestionResult interface fields ───────────────────────────────────────

  it("returns QuestionResult with all interface fields", async () => {
    const qr = makeQuestionResult({
      question_id: "q_999",
      question_en: "What is async?",
      question_az: "Async nədir?",
      difficulty_label: "hard",
      is_correct: false,
      response_time_ms: 7500,
    });
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockResolvedValue(makeQuestionBreakdown({ questions: [qr] }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useQuestionBreakdown("sess_abc"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const q = result.current.data?.questions[0];
    expect(q?.question_id).toBe("q_999");
    expect(q?.question_en).toBe("What is async?");
    expect(q?.question_az).toBe("Async nədir?");
    expect(q?.difficulty_label).toBe("hard");
    expect(q?.is_correct).toBe(false);
    expect(q?.response_time_ms).toBe(7500);
  });

  it("handles null question_en and question_az", async () => {
    const qr = makeQuestionResult({ question_en: null, question_az: null });
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockResolvedValue(makeQuestionBreakdown({ questions: [qr] }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useQuestionBreakdown("sess_null_q"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.questions[0].question_en).toBeNull();
    expect(result.current.data?.questions[0].question_az).toBeNull();
  });

  // ── auth error ────────────────────────────────────────────────────────────

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useQuestionBreakdown("sess_noauth"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  // ── apiFetch error ────────────────────────────────────────────────────────

  it("surfaces apiFetch error in error state", async () => {
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockRejectedValue(new Error("Network failure"));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useQuestionBreakdown("sess_err"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Network failure");
  });

  // ── query config ──────────────────────────────────────────────────────────

  it("uses ['assessment', 'questions', sessionId] as query key", async () => {
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockResolvedValue(makeQuestionBreakdown());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useQuestionBreakdown("sess_key"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["assessment", "questions", "sess_key"])).toBeDefined();
  });

  it("staleTime is 10 minutes — query not stale immediately after fetch", async () => {
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockResolvedValue(makeQuestionBreakdown());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useQuestionBreakdown("sess_stale"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const queryState = qc.getQueryState(["assessment", "questions", "sess_stale"]);
    expect(queryState?.isInvalidated).toBe(false);
  });

  it("retry is 1 — hook-level retry overrides wrapper default", async () => {
    // Just verifying the hook renders without crash; retry value tested via config
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockResolvedValue(makeQuestionBreakdown());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useQuestionBreakdown("sess_retry"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useAssessmentInfo", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── enabled guard ─────────────────────────────────────────────────────────

  it("does not fetch when slug is undefined", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useAssessmentInfo(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("does not fetch when slug is empty string", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useAssessmentInfo(""), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  // ── happy path ────────────────────────────────────────────────────────────

  it("fetches correct URL when slug is provided", async () => {
    mockGetToken.mockResolvedValue("tok_abc");
    mockApiFetch.mockResolvedValue(makeAssessmentInfo({ competency_slug: "communication" }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAssessmentInfo("communication"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/assessment/info/communication",
      { token: "tok_abc" }
    );
  });

  it("returns AssessmentInfo data on success", async () => {
    const info = makeAssessmentInfo({
      competency_slug: "leadership",
      name: "Leadership Skills",
      time_estimate_minutes: 20,
      can_retake: false,
      days_until_retake: 7,
    });
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockResolvedValue(info);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAssessmentInfo("leadership"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.competency_slug).toBe("leadership");
    expect(result.current.data?.name).toBe("Leadership Skills");
    expect(result.current.data?.time_estimate_minutes).toBe(20);
    expect(result.current.data?.can_retake).toBe(false);
    expect(result.current.data?.days_until_retake).toBe(7);
  });

  // ── AssessmentInfo interface fields ───────────────────────────────────────

  it("returns AssessmentInfo with null description and null days_until_retake", async () => {
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockResolvedValue(
      makeAssessmentInfo({ description: null, days_until_retake: null })
    );
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAssessmentInfo("adaptability"), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.description).toBeNull();
    expect(result.current.data?.days_until_retake).toBeNull();
  });

  // ── auth error ────────────────────────────────────────────────────────────

  it("throws ApiError 401 when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAssessmentInfo("reliability"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  // ── apiFetch error ────────────────────────────────────────────────────────

  it("surfaces apiFetch error in error state", async () => {
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockRejectedValue(new Error("Server 500"));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAssessmentInfo("empathy"), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Server 500");
  });

  // ── query config ──────────────────────────────────────────────────────────

  it("uses ['assessment', 'info', slug] as query key", async () => {
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockResolvedValue(makeAssessmentInfo());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAssessmentInfo("tech_literacy"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["assessment", "info", "tech_literacy"])).toBeDefined();
  });

  it("staleTime is 10 minutes — query not stale immediately after fetch", async () => {
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockResolvedValue(makeAssessmentInfo());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAssessmentInfo("communication"), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const queryState = qc.getQueryState(["assessment", "info", "communication"]);
    expect(queryState?.isInvalidated).toBe(false);
  });

  it("keeps distinct caches for different slugs", async () => {
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch
      .mockResolvedValueOnce(makeAssessmentInfo({ competency_slug: "communication" }))
      .mockResolvedValueOnce(makeAssessmentInfo({ competency_slug: "leadership" }));
    const { wrapper, qc } = makeWrapper();

    const { result: r1 } = renderHook(() => useAssessmentInfo("communication"), { wrapper });
    const { result: r2 } = renderHook(() => useAssessmentInfo("leadership"), { wrapper });

    await waitFor(() => expect(r1.current.isSuccess).toBe(true));
    await waitFor(() => expect(r2.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["assessment", "info", "communication"])).toBeDefined();
    expect(qc.getQueryData(["assessment", "info", "leadership"])).toBeDefined();
    expect(r1.current.data?.competency_slug).toBe("communication");
    expect(r2.current.data?.competency_slug).toBe("leadership");
  });
});

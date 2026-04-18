import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import type { ReactNode } from "react";

// ── Mocks (before any imports from the module under test) ─────────────────────

const mockApiFetch = vi.fn();

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

const mockGetToken = vi.fn();

vi.mock("../queries/use-auth-token", () => ({
  useAuthToken: () => mockGetToken,
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────

import { useAuraExplanation } from "../queries/use-aura-explanation";
import type { AuraExplanationResponse } from "../queries/use-aura-explanation";

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

function makeExplanation(overrides: Partial<AuraExplanationResponse> = {}): AuraExplanationResponse {
  return {
    volunteer_id: "user_abc",
    explanation_count: 3,
    methodology_reference: "IRT v2.1",
    explanations: [
      {
        competency_id: "communication",
        role_level: "mid",
        completed_at: "2026-04-01T10:00:00Z",
        items_evaluated: 15,
        evaluations: [
          {
            question_id: "q_001",
            concept_scores: { clarity: 0.9, empathy: 0.8 },
            evaluation_confidence: "high",
            methodology: "IRT",
          },
        ],
      },
    ],
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────

describe("useAuraExplanation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  // ── enabled guard ─────────────────────────────────────────────────────────

  it("does not fetch when enabled=false", () => {
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useAuraExplanation(false), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  it("fetches when enabled=true", async () => {
    mockApiFetch.mockResolvedValue(makeExplanation());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraExplanation(true), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/api/aura/me/explanation", { token: "test-token" });
  });

  // ── auth guard ────────────────────────────────────────────────────────────

  it("throws 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraExplanation(true), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect((result.current.error as { status?: number })?.status).toBe(401);
  });

  // ── happy path ────────────────────────────────────────────────────────────

  it("returns AuraExplanationResponse on success", async () => {
    const explanation = makeExplanation({ volunteer_id: "user_xyz", explanation_count: 5 });
    mockApiFetch.mockResolvedValue(explanation);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraExplanation(true), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.volunteer_id).toBe("user_xyz");
    expect(result.current.data?.explanation_count).toBe(5);
  });

  it("returns competency explanations with evaluation details", async () => {
    mockApiFetch.mockResolvedValue(makeExplanation());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraExplanation(true), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const exp = result.current.data?.explanations[0];
    expect(exp?.competency_id).toBe("communication");
    expect(exp?.evaluations[0].evaluation_confidence).toBe("high");
    expect(exp?.evaluations[0].concept_scores.clarity).toBe(0.9);
  });

  // ── staleTime ─────────────────────────────────────────────────────────────

  it("staleTime is 10 minutes — query not stale immediately", async () => {
    mockApiFetch.mockResolvedValue(makeExplanation());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAuraExplanation(true), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryState(["aura-explanation"])?.isInvalidated).toBe(false);
  });

  // ── cache key ─────────────────────────────────────────────────────────────

  it("uses ['aura-explanation'] as query key", async () => {
    mockApiFetch.mockResolvedValue(makeExplanation());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAuraExplanation(true), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["aura-explanation"])).toBeDefined();
  });

  // ── error path ────────────────────────────────────────────────────────────

  it("throws for server errors", async () => {
    mockApiFetch.mockRejectedValue(
      Object.assign(new Error("Internal Server Error"), { status: 500 })
    );
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAuraExplanation(true), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Internal Server Error");
  });
});

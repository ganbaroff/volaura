import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import type { ReactNode } from "react";

// ── Mocks (before any imports from the module under test) ─────────────────────

const mockApiFetch = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  toApiError: (err: unknown) => err instanceof Error ? err : new Error(String(err)),
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

import {
  useFileGrievance,
  useOwnGrievances,
  useAutomatedDecisions,
  useCreateHumanReview,
  useMyHumanReviews,
  useAdminPendingGrievances,
  useAdminHistoryGrievances,
  useTransitionGrievance,
} from "../queries/use-grievance";
import type { AutomatedDecision, Grievance, GrievanceAdmin, HumanReviewRequest } from "../queries/use-grievance";

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

function makeGrievance(overrides: Partial<Grievance> = {}): Grievance {
  return {
    id: "grievance_001",
    subject: "Issue with assessment",
    description: "The assessment was unfair",
    related_competency_slug: "communication",
    related_session_id: "session_abc",
    status: "pending",
    resolution: null,
    created_at: "2026-04-01T00:00:00Z",
    resolved_at: null,
    ...overrides,
  };
}

function makeGrievanceAdmin(overrides: Partial<GrievanceAdmin> = {}): GrievanceAdmin {
  return {
    ...makeGrievance(),
    user_id: "user_123",
    admin_notes: null,
    updated_at: "2026-04-01T00:00:00Z",
    ...overrides,
  };
}

function makeAutomatedDecision(overrides: Partial<AutomatedDecision> = {}): AutomatedDecision {
  return {
    id: "decision_001",
    decision_type: "assessment_score",
    created_at: "2026-04-01T00:00:00Z",
    human_reviewable: true,
    ...overrides,
  };
}

function makeHumanReview(overrides: Partial<HumanReviewRequest> = {}): HumanReviewRequest {
  return {
    id: "hr_001",
    user_id: "user_123",
    automated_decision_id: "decision_001",
    source_product: "volaura",
    request_reason: "Needs formal review due to inconsistent scoring.",
    requested_at: "2026-04-01T00:00:00Z",
    sla_deadline: "2026-04-08T00:00:00Z",
    status: "pending",
    resolved_at: null,
    resolution_notes: null,
    reviewer_user_id: null,
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────

describe("useFileGrievance", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("files grievance and invalidates grievances cache", async () => {
    const created = makeGrievance({ id: "new_griev" });
    mockApiFetch.mockResolvedValue(created);
    const { wrapper, qc } = makeWrapper();

    qc.setQueryData(["grievances", "own"], [makeGrievance()]);

    const { result } = renderHook(() => useFileGrievance(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        subject: "Issue",
        description: "Details here",
      });
    });

    expect(qc.getQueryState(["grievances", "own"])?.isInvalidated).toBe(true);
  });

  it("calls POST /api/aura/grievance with token and body", async () => {
    mockApiFetch.mockResolvedValue(makeGrievance());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useFileGrievance(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        subject: "Test Subject",
        description: "Test Description",
        related_competency_slug: "leadership",
      });
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/aura/grievance",
      expect.objectContaining({ method: "POST", token: "test-token" })
    );
  });

  it("throws 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useFileGrievance(), { wrapper });

    await expect(
      act(async () => {
        await result.current.mutateAsync({ subject: "Test", description: "Test" });
      })
    ).rejects.toThrow();
  });

  it("invalidates ['grievances'] key prefix on success", async () => {
    mockApiFetch.mockResolvedValue(makeGrievance());
    const { wrapper, qc } = makeWrapper();

    // Populate different grievance queries
    qc.setQueryData(["grievances", "own"], []);
    qc.setQueryData(["grievances", "admin", "pending"], []);

    const { result } = renderHook(() => useFileGrievance(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ subject: "s", description: "d" });
    });

    // Both should be invalidated since invalidateQueries({ queryKey: ["grievances"] }) prefixes
    expect(qc.getQueryState(["grievances", "own"])?.isInvalidated).toBe(true);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useOwnGrievances", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("returns grievances array from envelope .data", async () => {
    const grievances = [makeGrievance({ id: "g1" }), makeGrievance({ id: "g2" })];
    mockApiFetch.mockResolvedValue({ data: grievances });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useOwnGrievances(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(2);
    expect(result.current.data?.[0].id).toBe("g1");
  });

  it("returns empty array when envelope .data is null", async () => {
    mockApiFetch.mockResolvedValue({ data: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useOwnGrievances(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([]);
  });

  it("calls GET /api/aura/grievance with token", async () => {
    mockApiFetch.mockResolvedValue({ data: [] });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useOwnGrievances(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/api/aura/grievance", { token: "test-token" });
  });

  it("throws 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useOwnGrievances(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect((result.current.error as { status?: number })?.status).toBe(401);
  });

  it("throwOnError is false — does not propagate error to boundary", async () => {
    mockApiFetch.mockRejectedValue(new Error("Server Error"));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useOwnGrievances(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    // throwOnError: false means hook stays in error state without throwing
    expect(result.current.error).toBeDefined();
  });

  it("uses ['grievances', 'own'] as query key", async () => {
    mockApiFetch.mockResolvedValue({ data: [] });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useOwnGrievances(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["grievances", "own"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useAdminPendingGrievances", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("returns admin grievances from envelope .data", async () => {
    const grievances = [makeGrievanceAdmin({ id: "admin_g1", user_id: "user_456" })];
    mockApiFetch.mockResolvedValue({ data: grievances });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminPendingGrievances(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(1);
    expect(result.current.data?.[0].user_id).toBe("user_456");
  });

  it("calls GET /api/aura/grievance/admin/pending with token", async () => {
    mockApiFetch.mockResolvedValue({ data: [] });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminPendingGrievances(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/aura/grievance/admin/pending",
      { token: "test-token" }
    );
  });

  it("throws 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminPendingGrievances(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect((result.current.error as { status?: number })?.status).toBe(401);
  });

  it("throwOnError is false", async () => {
    mockApiFetch.mockRejectedValue(new Error("Forbidden"));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminPendingGrievances(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error).toBeDefined();
  });

  it("uses ['grievances', 'admin', 'pending'] as query key", async () => {
    mockApiFetch.mockResolvedValue({ data: [] });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAdminPendingGrievances(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["grievances", "admin", "pending"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useAdminHistoryGrievances", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("calls endpoint with default limit=50", async () => {
    mockApiFetch.mockResolvedValue({ data: [] });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminHistoryGrievances(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/aura/grievance/admin/history?limit=50",
      { token: "test-token" }
    );
  });

  it("passes custom limit param", async () => {
    mockApiFetch.mockResolvedValue({ data: [] });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminHistoryGrievances(10), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/aura/grievance/admin/history?limit=10",
      { token: "test-token" }
    );
  });

  it("includes limit in query key", async () => {
    mockApiFetch.mockResolvedValue({ data: [] });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useAdminHistoryGrievances(25), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["grievances", "admin", "history", 25])).toBeDefined();
  });

  it("throwOnError is false", async () => {
    mockApiFetch.mockRejectedValue(new Error("Forbidden"));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAdminHistoryGrievances(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useTransitionGrievance", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("transitions grievance status and invalidates cache", async () => {
    const updated = makeGrievanceAdmin({ status: "resolved", resolution: "Fixed" });
    mockApiFetch.mockResolvedValue(updated);
    const { wrapper, qc } = makeWrapper();

    qc.setQueryData(["grievances", "admin", "pending"], [makeGrievanceAdmin()]);

    const { result } = renderHook(() => useTransitionGrievance(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        grievance_id: "grievance_001",
        status: "resolved",
        resolution: "Fixed",
      });
    });

    expect(qc.getQueryState(["grievances", "admin", "pending"])?.isInvalidated).toBe(true);
  });

  it("calls PATCH /api/aura/grievance/admin/{id} with token and body", async () => {
    mockApiFetch.mockResolvedValue(makeGrievanceAdmin());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useTransitionGrievance(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        grievance_id: "grievance_xyz",
        status: "reviewing",
      });
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/aura/grievance/admin/grievance_xyz",
      expect.objectContaining({ method: "PATCH", token: "test-token" })
    );
  });

  it("throws 401 when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useTransitionGrievance(), { wrapper });

    await expect(
      act(async () => {
        await result.current.mutateAsync({
          grievance_id: "g_001",
          status: "rejected",
        });
      })
    ).rejects.toThrow();
  });

  it("invalidates ['grievances'] key prefix on success", async () => {
    mockApiFetch.mockResolvedValue(makeGrievanceAdmin());
    const { wrapper, qc } = makeWrapper();

    qc.setQueryData(["grievances", "own"], []);

    const { result } = renderHook(() => useTransitionGrievance(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ grievance_id: "g_001", status: "resolved" });
    });

    expect(qc.getQueryState(["grievances", "own"])?.isInvalidated).toBe(true);
  });
});

describe("useAutomatedDecisions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("calls GET /api/aura/human-review/decisions with limit", async () => {
    mockApiFetch.mockResolvedValue({ data: [makeAutomatedDecision()] });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useAutomatedDecisions(10), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/api/aura/human-review/decisions?limit=10", {
      token: "test-token",
    });
  });
});

describe("useCreateHumanReview", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("calls POST /api/aura/human-review and invalidates human-review queries", async () => {
    mockApiFetch.mockResolvedValue(makeHumanReview());
    const { wrapper, qc } = makeWrapper();
    qc.setQueryData(["human-review", "own"], [makeHumanReview()]);

    const { result } = renderHook(() => useCreateHumanReview(), { wrapper });
    await act(async () => {
      await result.current.mutateAsync({
        automated_decision_id: "decision_001",
        request_reason: "Please review this automated decision in detail.",
      });
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/api/aura/human-review",
      expect.objectContaining({ method: "POST", token: "test-token" })
    );
    expect(qc.getQueryState(["human-review", "own"])?.isInvalidated).toBe(true);
  });
});

describe("useMyHumanReviews", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  it("returns own human review requests from envelope data", async () => {
    mockApiFetch.mockResolvedValue({ data: [makeHumanReview({ id: "hr_123" })] });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyHumanReviews(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.[0].id).toBe("hr_123");
  });
});

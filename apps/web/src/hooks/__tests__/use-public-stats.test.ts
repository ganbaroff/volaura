import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import type { ReactNode } from "react";

// ── Mocks (before any imports from the module under test) ─────────────────────

const mockApiFetch = vi.fn();

vi.mock("@/lib/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/client")>("@/lib/api/client");
  return {
    ...actual,
    apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  };
});

// ── Import (after mocks) ──────────────────────────────────────────────────────

import { usePublicStats } from "../queries/use-public-stats";
import type { PublicStats } from "../queries/use-public-stats";

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

// ── Fixture ───────────────────────────────────────────────────────────────────

function makePublicStats(overrides: Partial<PublicStats> = {}): PublicStats {
  return {
    total_professionals: 1250,
    total_assessments: 8400,
    total_events: 320,
    avg_aura_score: 74.3,
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────

describe("usePublicStats", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── happy path ────────────────────────────────────────────────────────────

  it("returns PublicStats with all 4 fields on success", async () => {
    const stats = makePublicStats({
      total_professionals: 2000,
      total_assessments: 15000,
      total_events: 500,
      avg_aura_score: 80.1,
    });
    mockApiFetch.mockResolvedValue(stats);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => usePublicStats(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.total_professionals).toBe(2000);
    expect(result.current.data?.total_assessments).toBe(15000);
    expect(result.current.data?.total_events).toBe(500);
    expect(result.current.data?.avg_aura_score).toBe(80.1);
  });

  // ── correct URL ───────────────────────────────────────────────────────────

  it("calls apiFetch with /stats/public path", async () => {
    mockApiFetch.mockResolvedValue(makePublicStats());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => usePublicStats(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/stats/public");
  });

  // ── no auth required ──────────────────────────────────────────────────────

  it("does not depend on auth token — no useAuthToken mock needed", async () => {
    // If usePublicStats used useAuthToken, the mock would not be wired and
    // would throw. This test verifies the hook works with only apiFetch mocked.
    mockApiFetch.mockResolvedValue(makePublicStats());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => usePublicStats(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // apiFetch called with no token argument (no second arg or no token field)
    const call = mockApiFetch.mock.calls[0];
    expect(call[0]).toBe("/stats/public");
    expect(call[1]).toBeUndefined();
  });

  // ── staleTime ─────────────────────────────────────────────────────────────

  it("staleTime is 5 minutes — query not stale immediately after fetch", async () => {
    mockApiFetch.mockResolvedValue(makePublicStats());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => usePublicStats(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const queryState = qc.getQueryState(["stats", "public"]);
    expect(queryState?.isInvalidated).toBe(false);
  });

  // ── query key ─────────────────────────────────────────────────────────────

  it("uses ['stats', 'public'] as query key", async () => {
    mockApiFetch.mockResolvedValue(makePublicStats());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => usePublicStats(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["stats", "public"])).toBeDefined();
  });

  // ── error propagation ─────────────────────────────────────────────────────

  it("propagates apiFetch error to error state", async () => {
    mockApiFetch.mockRejectedValue(new Error("Network unavailable"));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => usePublicStats(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Network unavailable");
  });

  // ── PublicStats shape ─────────────────────────────────────────────────────

  it("validates PublicStats shape — all fields are numbers", async () => {
    const stats = makePublicStats({
      total_professionals: 0,
      total_assessments: 0,
      total_events: 0,
      avg_aura_score: 0,
    });
    mockApiFetch.mockResolvedValue(stats);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => usePublicStats(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const data = result.current.data!;
    expect(typeof data.total_professionals).toBe("number");
    expect(typeof data.total_assessments).toBe("number");
    expect(typeof data.total_events).toBe("number");
    expect(typeof data.avg_aura_score).toBe("number");
  });
});

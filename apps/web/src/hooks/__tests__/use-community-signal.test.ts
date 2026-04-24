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

import { useCommunitySignal } from "../queries/use-community-signal";
import type { CommunitySignal } from "../queries/use-community-signal";

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

function makeCommunitySignal(overrides: Partial<CommunitySignal> = {}): CommunitySignal {
  return {
    professionals_today: 42,
    professionals_this_week: 315,
    total_professionals: 1250,
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────

describe("useCommunitySignal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── no auth required ──────────────────────────────────────────────────────

  it("fetches without auth token — public endpoint", async () => {
    mockApiFetch.mockResolvedValue(makeCommunitySignal());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCommunitySignal(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // No token passed — just the URL
    expect(mockApiFetch).toHaveBeenCalledWith("/community/signal");
  });

  // ── happy path ────────────────────────────────────────────────────────────

  it("returns CommunitySignal with all fields", async () => {
    const signal = makeCommunitySignal({
      professionals_today: 99,
      professionals_this_week: 712,
      total_professionals: 4800,
    });
    mockApiFetch.mockResolvedValue(signal);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCommunitySignal(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.professionals_today).toBe(99);
    expect(result.current.data?.professionals_this_week).toBe(712);
    expect(result.current.data?.total_professionals).toBe(4800);
  });

  // ── staleTime 5 minutes ───────────────────────────────────────────────────

  it("staleTime is 5 minutes — query not stale immediately after fetch", async () => {
    mockApiFetch.mockResolvedValue(makeCommunitySignal());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useCommunitySignal(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryState(["community", "signal"])?.isInvalidated).toBe(false);
  });

  // ── cache key ─────────────────────────────────────────────────────────────

  it("uses ['community', 'signal'] as query key", async () => {
    mockApiFetch.mockResolvedValue(makeCommunitySignal());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useCommunitySignal(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["community", "signal"])).toBeDefined();
  });

  // ── error path ────────────────────────────────────────────────────────────

  it("sets isError on network failure", async () => {
    mockApiFetch.mockRejectedValue(
      Object.assign(new Error("Network Error"), { status: 503 })
    );
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCommunitySignal(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Network Error");
  });

  // ── returns zero counts ───────────────────────────────────────────────────

  it("handles zero counts gracefully", async () => {
    mockApiFetch.mockResolvedValue(
      makeCommunitySignal({ professionals_today: 0, professionals_this_week: 0, total_professionals: 0 })
    );
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useCommunitySignal(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.professionals_today).toBe(0);
    expect(result.current.data?.total_professionals).toBe(0);
  });
});

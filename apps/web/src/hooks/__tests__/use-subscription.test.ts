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

const mockGetToken = vi.fn();

vi.mock("../queries/use-auth-token", () => ({
  useAuthToken: () => mockGetToken,
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────

import { useSubscription } from "../queries/use-subscription";
import type { SubscriptionStatus } from "../queries/use-subscription";

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

// ── Fixtures ──────────────────────────────────────────────────────────────────

function makeSubscriptionStatus(overrides: Partial<SubscriptionStatus> = {}): SubscriptionStatus {
  return {
    status: "active",
    trial_ends_at: null,
    subscription_ends_at: "2026-12-31T23:59:59Z",
    days_remaining: 257,
    is_active: true,
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────

describe("useSubscription", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("test-token");
  });

  // ── null token → null data ────────────────────────────────────────────────

  it("returns undefined data fields when token is null (not authenticated)", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSubscription(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.status).toBeUndefined();
    expect(result.current.daysRemaining).toBeUndefined();
    expect(result.current.isActive).toBe(false);
    expect(result.current.isTrial).toBe(false);
    expect(result.current.isExpired).toBe(false);
  });

  // ── active status ─────────────────────────────────────────────────────────

  it("derives isActive=true for active status", async () => {
    mockApiFetch.mockResolvedValue(makeSubscriptionStatus({ status: "active", is_active: true }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSubscription(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.isActive).toBe(true);
    expect(result.current.isTrial).toBe(false);
    expect(result.current.isExpired).toBe(false);
    expect(result.current.status).toBe("active");
  });

  // ── trial status ──────────────────────────────────────────────────────────

  it("derives isTrial=true for trial status", async () => {
    mockApiFetch.mockResolvedValue(
      makeSubscriptionStatus({
        status: "trial",
        is_active: true,
        trial_ends_at: "2026-05-01T00:00:00Z",
        subscription_ends_at: null,
        days_remaining: 13,
      })
    );
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSubscription(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.isTrial).toBe(true);
    expect(result.current.isActive).toBe(true);
    expect(result.current.isExpired).toBe(false);
    expect(result.current.trialEndsAt).toBe("2026-05-01T00:00:00Z");
    expect(result.current.daysRemaining).toBe(13);
  });

  // ── expired status ────────────────────────────────────────────────────────

  it("derives isExpired=true for expired status", async () => {
    mockApiFetch.mockResolvedValue(
      makeSubscriptionStatus({
        status: "expired",
        is_active: false,
        subscription_ends_at: "2026-01-01T00:00:00Z",
        days_remaining: 0,
      })
    );
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSubscription(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.isExpired).toBe(true);
    expect(result.current.isActive).toBe(false);
    expect(result.current.isTrial).toBe(false);
    expect(result.current.daysRemaining).toBe(0);
  });

  // ── cancelled status ──────────────────────────────────────────────────────

  it("derives correct fields for cancelled status", async () => {
    mockApiFetch.mockResolvedValue(
      makeSubscriptionStatus({
        status: "cancelled",
        is_active: false,
        days_remaining: 5,
      })
    );
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSubscription(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.status).toBe("cancelled");
    expect(result.current.isActive).toBe(false);
    expect(result.current.isTrial).toBe(false);
    expect(result.current.isExpired).toBe(false);
    expect(result.current.daysRemaining).toBe(5);
  });

  // ── daysRemaining ─────────────────────────────────────────────────────────

  it("exposes daysRemaining from API response", async () => {
    mockApiFetch.mockResolvedValue(makeSubscriptionStatus({ days_remaining: 90 }));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSubscription(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.daysRemaining).toBe(90);
  });

  // ── subscription endpoint ─────────────────────────────────────────────────

  it("calls apiFetch with /subscription/status and token", async () => {
    mockApiFetch.mockResolvedValue(makeSubscriptionStatus());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSubscription(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(mockApiFetch).toHaveBeenCalledWith("/subscription/status", { token: "test-token" });
  });

  // ── cache key ─────────────────────────────────────────────────────────────

  it("uses ['subscription-status'] as query key", async () => {
    mockApiFetch.mockResolvedValue(makeSubscriptionStatus());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useSubscription(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(qc.getQueryData(["subscription-status"])).toBeDefined();
  });

  // ── trialEndsAt / subscriptionEndsAt ─────────────────────────────────────

  it("exposes trialEndsAt and subscriptionEndsAt correctly", async () => {
    mockApiFetch.mockResolvedValue(
      makeSubscriptionStatus({
        trial_ends_at: "2026-04-30T00:00:00Z",
        subscription_ends_at: "2026-12-01T00:00:00Z",
      })
    );
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSubscription(), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.trialEndsAt).toBe("2026-04-30T00:00:00Z");
    expect(result.current.subscriptionEndsAt).toBe("2026-12-01T00:00:00Z");
  });
});

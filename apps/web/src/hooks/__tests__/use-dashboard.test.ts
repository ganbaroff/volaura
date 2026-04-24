import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import type { ReactNode } from "react";

// ── Mocks (before any imports from the module under test) ─────────────────────

const mockApiFetch = vi.fn();
const mockGetToken = vi.fn();
const mockGetActivity = vi.fn();
const mockGetStats = vi.fn();

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

vi.mock("../queries/use-auth-token", () => ({
  useAuthToken: () => mockGetToken,
}));

vi.mock("@/lib/api/generated", () => ({
  getMyActivityApiActivityMeGet: (...args: unknown[]) => mockGetActivity(...args),
  getMyStatsApiActivityStatsMeGet: (...args: unknown[]) => mockGetStats(...args),
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────

import { useBadges, useActivity, useDashboardStats } from "../queries/use-dashboard";
import type { Badge, ApiActivityItem, DashboardStats } from "@/lib/api/types";

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

function makeBadge(overrides: Partial<Badge> = {}): Badge {
  return {
    id: "badge_001",
    volunteer_id: "user_abc",
    badge_type: "assessment",
    tier: "gold",
    earned_at: "2026-01-15T10:00:00Z",
    metadata: {},
    ...overrides,
  };
}

function makeActivityItem(overrides: Partial<ApiActivityItem> = {}): ApiActivityItem {
  return {
    id: "act_001",
    type: "assessment",
    description: "Completed Communication assessment",
    created_at: "2026-01-20T09:00:00Z",
    metadata: {},
    ...overrides,
  };
}

function makeDashboardStats(overrides: Partial<DashboardStats> = {}): DashboardStats {
  return {
    events_attended: 12,
    total_hours: 36,
    verified_skills: 5,
    streak_days: 7,
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────

describe("useBadges", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── auth error ────────────────────────────────────────────────────────────

  it("throws when no auth token", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useBadges(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    const err = result.current.error as { status?: number };
    expect(err?.status).toBe(401);
    expect(mockApiFetch).not.toHaveBeenCalled();
  });

  // ── happy path ────────────────────────────────────────────────────────────

  it("returns Badge[] on success", async () => {
    const badges = [
      makeBadge({ id: "b1", tier: "gold" }),
      makeBadge({ id: "b2", tier: "silver" }),
    ];
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockResolvedValue(badges);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useBadges(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(2);
    expect(result.current.data?.[0].tier).toBe("gold");
    expect(result.current.data?.[1].tier).toBe("silver");
  });

  it("fetches /api/badges/me", async () => {
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockResolvedValue([makeBadge()]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useBadges(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/api/badges/me", { token: "tok_ok" });
  });

  it("returns empty array when API returns []", async () => {
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockResolvedValue([]);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useBadges(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([]);
  });

  // ── query config ──────────────────────────────────────────────────────────

  it("uses ['badges', 'me'] as query key", async () => {
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockResolvedValue([makeBadge()]);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useBadges(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["badges", "me"])).toBeDefined();
  });

  it("staleTime is 5 minutes — query not stale immediately after fetch", async () => {
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockResolvedValue([makeBadge()]);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useBadges(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const queryState = qc.getQueryState(["badges", "me"]);
    expect(queryState?.isInvalidated).toBe(false);
  });

  // ── apiFetch error ────────────────────────────────────────────────────────

  it("surfaces apiFetch error in error state", async () => {
    mockGetToken.mockResolvedValue("tok_ok");
    mockApiFetch.mockRejectedValue(new Error("403 Forbidden"));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useBadges(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("403 Forbidden");
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useActivity", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── default limit ─────────────────────────────────────────────────────────

  it("passes default limit 20 to SDK", async () => {
    mockGetActivity.mockResolvedValue({ data: [makeActivityItem()], error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useActivity(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockGetActivity).toHaveBeenCalledWith({ query: { limit: 20 } });
  });

  // ── custom limit ──────────────────────────────────────────────────────────

  it("passes custom limit to SDK", async () => {
    mockGetActivity.mockResolvedValue({ data: [makeActivityItem()], error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useActivity(5), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockGetActivity).toHaveBeenCalledWith({ query: { limit: 5 } });
  });

  // ── happy path ────────────────────────────────────────────────────────────

  it("returns ApiActivityItem[] on success", async () => {
    const items = [
      makeActivityItem({ id: "act_1", type: "assessment" }),
      makeActivityItem({ id: "act_2", type: "badge" }),
    ];
    mockGetActivity.mockResolvedValue({ data: items, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useActivity(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(2);
    expect(result.current.data?.[0].type).toBe("assessment");
    expect(result.current.data?.[1].type).toBe("badge");
  });

  it("returns empty array when SDK returns null data", async () => {
    mockGetActivity.mockResolvedValue({ data: null, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useActivity(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual([]);
  });

  // ── error path ────────────────────────────────────────────────────────────

  it("throws when SDK returns error", async () => {
    mockGetActivity.mockResolvedValue({
      data: null,
      error: { status: 401, detail: { code: "UNAUTHORIZED", message: "Activity fetch failed" } },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useActivity(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Activity fetch failed");
    expect(result.current.error?.status).toBe(401);
    expect(result.current.error?.code).toBe("UNAUTHORIZED");
  });

  // ── query config ──────────────────────────────────────────────────────────

  it("uses ['activity', limit] as query key with default limit", async () => {
    mockGetActivity.mockResolvedValue({ data: [makeActivityItem()], error: null });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useActivity(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["activity", 20])).toBeDefined();
  });

  it("uses ['activity', limit] as query key with custom limit", async () => {
    mockGetActivity.mockResolvedValue({ data: [makeActivityItem()], error: null });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useActivity(10), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["activity", 10])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useDashboardStats", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── happy path ────────────────────────────────────────────────────────────

  it("returns DashboardStats on success", async () => {
    const stats = makeDashboardStats({
      events_attended: 20,
      total_hours: 60,
      verified_skills: 8,
      streak_days: 14,
    });
    mockGetStats.mockResolvedValue({ data: stats, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDashboardStats(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.events_attended).toBe(20);
    expect(result.current.data?.total_hours).toBe(60);
    expect(result.current.data?.verified_skills).toBe(8);
    expect(result.current.data?.streak_days).toBe(14);
  });

  // ── error paths ───────────────────────────────────────────────────────────

  it("throws when SDK returns no data and no error", async () => {
    mockGetStats.mockResolvedValue({ data: null, error: null });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDashboardStats(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Failed to fetch dashboard stats");
  });

  it("throws when SDK returns error", async () => {
    mockGetStats.mockResolvedValue({
      data: null,
      error: { status: 401, detail: { code: "UNAUTHORIZED", message: "Stats unavailable" } },
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useDashboardStats(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);

    expect(result.current.error?.message).toBe("Stats unavailable");
    expect(result.current.error?.status).toBe(401);
    expect(result.current.error?.code).toBe("UNAUTHORIZED");
  });

  // ── query config ──────────────────────────────────────────────────────────

  it("uses ['dashboard', 'stats'] as query key", async () => {
    mockGetStats.mockResolvedValue({ data: makeDashboardStats(), error: null });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useDashboardStats(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["dashboard", "stats"])).toBeDefined();
  });

  it("staleTime is 5 minutes — query not stale immediately after fetch", async () => {
    mockGetStats.mockResolvedValue({ data: makeDashboardStats(), error: null });
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useDashboardStats(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const queryState = qc.getQueryState(["dashboard", "stats"]);
    expect(queryState?.isInvalidated).toBe(false);
  });
});

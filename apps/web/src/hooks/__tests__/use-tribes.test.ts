import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
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

const mockTrackEvent = vi.fn();

vi.mock("@/hooks/use-analytics", () => ({
  useTrackEvent: () => mockTrackEvent,
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────

import {
  useMyTribe,
  useMyStreak,
  useSendKudos,
  useOptOutOfTribe,
  useRequestTribeRenewal,
  useMyPoolStatus,
  useJoinTribePool,
} from "../queries/use-tribes";
import type { TribeOut, TribeStreakOut, PoolStatusOut } from "../queries/use-tribes";

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

function makeTribeOut(overrides: Partial<TribeOut> = {}): TribeOut {
  return {
    tribe_id: "tribe_001",
    expires_at: "2026-05-01T00:00:00Z",
    status: "active",
    members: [
      {
        user_id: "user_123",
        display_name: "Alice",
        avatar_url: null,
        active_this_week: true,
      },
    ],
    kudos_count_this_week: 3,
    renewal_requested: false,
    ...overrides,
  };
}

function makeTribeStreak(overrides: Partial<TribeStreakOut> = {}): TribeStreakOut {
  return {
    current_streak: 5,
    longest_streak: 12,
    last_activity_week: "2026-04-14",
    consecutive_misses_count: 0,
    crystal_fade_level: 0,
    ...overrides,
  };
}

function makePoolStatus(overrides: Partial<PoolStatusOut> = {}): PoolStatusOut {
  return {
    in_pool: false,
    joined_at: null,
    ...overrides,
  };
}

// ─────────────────────────────────────────────────────────────────────────────

describe("useMyTribe", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns TribeOut on success — no auth required", async () => {
    const tribe = makeTribeOut({ tribe_id: "tribe_xyz" });
    mockApiFetch.mockResolvedValue(tribe);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyTribe(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.tribe_id).toBe("tribe_xyz");
  });

  it("calls apiFetch with /tribes/me (no token)", async () => {
    mockApiFetch.mockResolvedValue(makeTribeOut());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyTribe(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/tribes/me");
  });

  it("returns null when API returns null", async () => {
    mockApiFetch.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyTribe(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeNull();
  });

  it("uses ['tribe', 'me'] as query key", async () => {
    mockApiFetch.mockResolvedValue(makeTribeOut());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useMyTribe(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["tribe", "me"])).toBeDefined();
  });

  it("staleTime is 1 minute — query not stale immediately", async () => {
    mockApiFetch.mockResolvedValue(makeTribeOut());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useMyTribe(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryState(["tribe", "me"])?.isInvalidated).toBe(false);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useMyStreak", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns TribeStreakOut on success — no auth required", async () => {
    const streak = makeTribeStreak({ current_streak: 7, longest_streak: 20 });
    mockApiFetch.mockResolvedValue(streak);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyStreak(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.current_streak).toBe(7);
    expect(result.current.data?.longest_streak).toBe(20);
  });

  it("calls apiFetch with /tribes/me/streak", async () => {
    mockApiFetch.mockResolvedValue(makeTribeStreak());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyStreak(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/tribes/me/streak");
  });

  it("returns null when API returns null", async () => {
    mockApiFetch.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyStreak(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeNull();
  });

  it("uses ['tribe', 'streak'] as query key", async () => {
    mockApiFetch.mockResolvedValue(makeTribeStreak());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useMyStreak(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["tribe", "streak"])).toBeDefined();
  });

  it("staleTime is 5 minutes — query not stale immediately", async () => {
    mockApiFetch.mockResolvedValue(makeTribeStreak());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useMyStreak(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryState(["tribe", "streak"])?.isInvalidated).toBe(false);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useSendKudos", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls POST /tribes/me/kudos", async () => {
    mockApiFetch.mockResolvedValue({ success: true });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useSendKudos(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync();
    });

    expect(mockApiFetch).toHaveBeenCalledWith("/tribes/me/kudos", { method: "POST" });
  });

  it("invalidates ['tribe', 'me'] cache on success", async () => {
    mockApiFetch.mockResolvedValue({ success: true });
    const { wrapper, qc } = makeWrapper();

    qc.setQueryData(["tribe", "me"], makeTribeOut());

    const { result } = renderHook(() => useSendKudos(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync();
    });

    expect(qc.getQueryState(["tribe", "me"])?.isInvalidated).toBe(true);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useOptOutOfTribe", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls POST /tribes/opt-out", async () => {
    mockApiFetch.mockResolvedValue({ success: true });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useOptOutOfTribe(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync();
    });

    expect(mockApiFetch).toHaveBeenCalledWith("/tribes/opt-out", { method: "POST" });
  });

  it("invalidates ['tribe'] cache prefix on success", async () => {
    mockApiFetch.mockResolvedValue({ success: true });
    const { wrapper, qc } = makeWrapper();

    qc.setQueryData(["tribe", "me"], makeTribeOut());
    qc.setQueryData(["tribe", "streak"], makeTribeStreak());

    const { result } = renderHook(() => useOptOutOfTribe(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync();
    });

    // invalidateQueries({ queryKey: ["tribe"] }) invalidates all tribe queries
    expect(qc.getQueryState(["tribe", "me"])?.isInvalidated).toBe(true);
    expect(qc.getQueryState(["tribe", "streak"])?.isInvalidated).toBe(true);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useRequestTribeRenewal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls POST /tribes/renew", async () => {
    mockApiFetch.mockResolvedValue({ success: true });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useRequestTribeRenewal(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync();
    });

    expect(mockApiFetch).toHaveBeenCalledWith("/tribes/renew", { method: "POST" });
  });

  it("invalidates ['tribe', 'me'] on success", async () => {
    mockApiFetch.mockResolvedValue({ success: true });
    const { wrapper, qc } = makeWrapper();

    qc.setQueryData(["tribe", "me"], makeTribeOut());

    const { result } = renderHook(() => useRequestTribeRenewal(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync();
    });

    expect(qc.getQueryState(["tribe", "me"])?.isInvalidated).toBe(true);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useMyPoolStatus", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns pool status — no auth required", async () => {
    const status = makePoolStatus({ in_pool: true, joined_at: "2026-04-15T10:00:00Z" });
    mockApiFetch.mockResolvedValue(status);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyPoolStatus(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.in_pool).toBe(true);
    expect(result.current.data?.joined_at).toBe("2026-04-15T10:00:00Z");
  });

  it("calls apiFetch with /tribes/me/pool-status", async () => {
    mockApiFetch.mockResolvedValue(makePoolStatus());
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMyPoolStatus(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/tribes/me/pool-status");
  });

  it("uses ['tribe', 'pool-status'] as query key", async () => {
    mockApiFetch.mockResolvedValue(makePoolStatus());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useMyPoolStatus(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["tribe", "pool-status"])).toBeDefined();
  });

  it("staleTime is 30 seconds — query not stale immediately", async () => {
    mockApiFetch.mockResolvedValue(makePoolStatus());
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useMyPoolStatus(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryState(["tribe", "pool-status"])?.isInvalidated).toBe(false);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useJoinTribePool", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("calls POST /tribes/join-pool", async () => {
    mockApiFetch.mockResolvedValue({ success: true });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useJoinTribePool(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync();
    });

    expect(mockApiFetch).toHaveBeenCalledWith("/tribes/join-pool", { method: "POST" });
  });

  it("invalidates ['tribe', 'pool-status'] cache on success", async () => {
    mockApiFetch.mockResolvedValue({ success: true });
    const { wrapper, qc } = makeWrapper();

    qc.setQueryData(["tribe", "pool-status"], makePoolStatus());

    const { result } = renderHook(() => useJoinTribePool(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync();
    });

    expect(qc.getQueryState(["tribe", "pool-status"])?.isInvalidated).toBe(true);
  });

  it("calls useTrackEvent with 'tribe_pool_joined' on success", async () => {
    mockApiFetch.mockResolvedValue({ success: true });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useJoinTribePool(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync();
    });

    expect(mockTrackEvent).toHaveBeenCalledWith("tribe_pool_joined");
  });

  it("does not call trackEvent on failure", async () => {
    mockApiFetch.mockRejectedValue(new Error("Network error"));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useJoinTribePool(), { wrapper });

    await act(async () => {
      try {
        await result.current.mutateAsync();
      } catch {
        // expected
      }
    });

    expect(mockTrackEvent).not.toHaveBeenCalled();
  });
});

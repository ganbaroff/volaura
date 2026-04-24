import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement, type ReactNode } from "react";

// ── apiFetch mock ─────────────────────────────────────────────────────────────
const mockApiFetch = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  toApiError: (err: unknown) => err instanceof Error ? err : new Error(String(err)),
  ApiError: class ApiError extends Error {
    status: number;
    code: string;
    detail: string;
    constructor(status: number, code: string, detail: string) {
      super(detail);
      this.name = "ApiError";
      this.status = status;
      this.code = code;
      this.detail = detail;
    }
  },
}));

// ── useAuthToken mock ─────────────────────────────────────────────────────────
const mockGetToken = vi.fn();

vi.mock("../queries/use-auth-token", () => ({
  useAuthToken: () => mockGetToken,
}));

// ── Supabase Realtime mock ────────────────────────────────────────────────────
// We need to inspect: channel name, .on() call, .subscribe(), removeChannel()
const mockSubscribe = vi.fn();
const mockOn = vi.fn();
const mockRemoveChannel = vi.fn();
const mockChannel = vi.fn();

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    channel: mockChannel,
    removeChannel: mockRemoveChannel,
  }),
}));

// ── Import (after mocks) ──────────────────────────────────────────────────────
import {
  useUnreadCount,
  useNotifications,
  useMarkNotificationRead,
  useMarkAllRead,
  useRealtimeNotifications,
} from "../queries/use-notifications";

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

/** waitFor timeout long enough for hooks with retry: 1 + retryDelay: 0 */
const ERROR_TIMEOUT = { timeout: 5000 };

// ─────────────────────────────────────────────────────────────────────────────

describe("useUnreadCount", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns { unread_count: 0 } when token is null (no throw)", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useUnreadCount(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual({ unread_count: 0 });
  });

  it("calls apiFetch with correct path when authenticated", async () => {
    mockGetToken.mockResolvedValue("tok_abc");
    mockApiFetch.mockResolvedValue({ unread_count: 7 });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useUnreadCount(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/notifications/unread-count", { token: "tok_abc" });
    expect(result.current.data?.unread_count).toBe(7);
  });

  it("uses ['notifications', 'unread'] as query key", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useUnreadCount(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["notifications", "unread"])).toBeDefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useNotifications", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("tok_user");
  });

  it("calls apiFetch without query string when no params", async () => {
    mockApiFetch.mockResolvedValue({ notifications: [], unread_count: 0, total: 0 });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useNotifications(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockApiFetch).toHaveBeenCalledWith("/api/notifications", { token: "tok_user" });
  });

  it("appends limit param when provided", async () => {
    mockApiFetch.mockResolvedValue({ notifications: [], unread_count: 0, total: 0 });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useNotifications({ limit: 20 }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const calledPath = mockApiFetch.mock.calls[0][0] as string;
    expect(calledPath).toContain("limit=20");
  });

  it("appends offset param when provided", async () => {
    mockApiFetch.mockResolvedValue({ notifications: [], unread_count: 0, total: 0 });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useNotifications({ offset: 10 }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const calledPath = mockApiFetch.mock.calls[0][0] as string;
    expect(calledPath).toContain("offset=10");
  });

  it("appends both limit and offset when both provided", async () => {
    mockApiFetch.mockResolvedValue({ notifications: [], unread_count: 0, total: 0 });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useNotifications({ limit: 15, offset: 30 }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const calledPath = mockApiFetch.mock.calls[0][0] as string;
    expect(calledPath).toContain("limit=15");
    expect(calledPath).toContain("offset=30");
  });

  it("throws ApiError(401) when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useNotifications(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), ERROR_TIMEOUT);
  });

  it("uses ['notifications', 'list', params] as query key", async () => {
    mockApiFetch.mockResolvedValue({ notifications: [], unread_count: 0, total: 0 });
    const params = { limit: 10 };
    const { wrapper, qc } = makeWrapper();

    const { result } = renderHook(() => useNotifications(params), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(qc.getQueryData(["notifications", "list", params])).toBeDefined();
  });

  it("returns notifications list from apiFetch", async () => {
    const notifications = [
      {
        id: "n1",
        type: "badge_earned",
        title: "Gold badge!",
        body: null,
        is_read: false,
        reference_id: null,
        created_at: "2026-01-01T00:00:00Z",
      },
    ];
    mockApiFetch.mockResolvedValue({ notifications, unread_count: 1, total: 1 });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useNotifications(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.notifications).toHaveLength(1);
    expect(result.current.data?.unread_count).toBe(1);
    expect(result.current.data?.total).toBe(1);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useMarkNotificationRead", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("tok_user");
  });

  it("calls PATCH on correct notification endpoint", async () => {
    mockApiFetch.mockResolvedValue({
      id: "n1",
      type: "badge_earned",
      title: "Gold!",
      body: null,
      is_read: true,
      reference_id: null,
      created_at: "2026-01-01T00:00:00Z",
    });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMarkNotificationRead(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync("n1");
    });

    expect(mockApiFetch).toHaveBeenCalledWith("/api/notifications/n1/read", {
      method: "PATCH",
      token: "tok_user",
    });
  });

  it("invalidates ['notifications'] query on success", async () => {
    mockApiFetch.mockResolvedValue({
      id: "n1", type: "t", title: "T", body: null, is_read: true, reference_id: null, created_at: "2026-01-01T00:00:00Z",
    });
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useMarkNotificationRead(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync("n1");
    });

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["notifications"] });
  });

  it("throws ApiError(401) when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMarkNotificationRead(), { wrapper });

    await act(async () => {
      await expect(result.current.mutateAsync("n1")).rejects.toThrow();
    });
  });

  it("does not invalidate on failure", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useMarkNotificationRead(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync("n1").catch(() => undefined);
    });

    expect(invalidateSpy).not.toHaveBeenCalled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useMarkAllRead", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("tok_user");
  });

  it("calls PATCH on read-all endpoint", async () => {
    mockApiFetch.mockResolvedValue({ unread_count: 0 });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMarkAllRead(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync();
    });

    expect(mockApiFetch).toHaveBeenCalledWith("/api/notifications/read-all", {
      method: "PATCH",
      token: "tok_user",
    });
  });

  it("invalidates ['notifications'] query on success", async () => {
    mockApiFetch.mockResolvedValue({ unread_count: 0 });
    const { wrapper, qc } = makeWrapper();

    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    const { result } = renderHook(() => useMarkAllRead(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync();
    });

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["notifications"] });
  });

  it("throws ApiError(401) when token is null", async () => {
    mockGetToken.mockResolvedValue(null);
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMarkAllRead(), { wrapper });

    await act(async () => {
      await expect(result.current.mutateAsync()).rejects.toThrow();
    });
  });

  it("returns unread_count from API response", async () => {
    mockApiFetch.mockResolvedValue({ unread_count: 0 });
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => useMarkAllRead(), { wrapper });

    let mutationResult: { unread_count: number } | undefined;
    await act(async () => {
      mutationResult = await result.current.mutateAsync();
    });

    expect(mutationResult?.unread_count).toBe(0);
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("useRealtimeNotifications", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Wire up channel mock: channel() → { on: mockOn, subscribe: mockSubscribe }
    mockOn.mockReturnValue({ subscribe: mockSubscribe });
    mockChannel.mockReturnValue({ on: mockOn });
    mockSubscribe.mockReturnValue({});
  });

  it("does nothing when userId is null", () => {
    const { wrapper } = makeWrapper();

    renderHook(() => useRealtimeNotifications(null), { wrapper });

    expect(mockChannel).not.toHaveBeenCalled();
  });

  it("creates channel with user-scoped name when userId provided", () => {
    const { wrapper } = makeWrapper();

    renderHook(() => useRealtimeNotifications("user_xyz"), { wrapper });

    expect(mockChannel).toHaveBeenCalledWith("notifications:user:user_xyz");
  });

  it("subscribes to INSERT on notifications table", () => {
    const { wrapper } = makeWrapper();

    renderHook(() => useRealtimeNotifications("user_abc"), { wrapper });

    expect(mockOn).toHaveBeenCalledWith(
      "postgres_changes",
      expect.objectContaining({
        event: "INSERT",
        schema: "public",
        table: "notifications",
        filter: "user_id=eq.user_abc",
      }),
      expect.any(Function)
    );
  });

  it("calls subscribe after .on()", () => {
    const { wrapper } = makeWrapper();

    renderHook(() => useRealtimeNotifications("user_abc"), { wrapper });

    expect(mockSubscribe).toHaveBeenCalledOnce();
  });

  it("removes channel on unmount", () => {
    // channel = return value of subscribe() — that's what the hook passes to removeChannel
    const fakeSubscribed = { id: "fake-subscribed-channel" };
    mockSubscribe.mockReturnValue(fakeSubscribed);
    mockOn.mockReturnValue({ subscribe: mockSubscribe });
    mockChannel.mockReturnValue({ on: mockOn });

    const { wrapper } = makeWrapper();
    const { unmount } = renderHook(() => useRealtimeNotifications("user_abc"), { wrapper });

    unmount();

    expect(mockRemoveChannel).toHaveBeenCalledWith(fakeSubscribed);
  });

  it("invalidates ['notifications', 'unread'] when INSERT fires", () => {
    // Capture the callback passed to .on()
    let insertCallback: (() => void) | undefined;
    mockOn.mockImplementation((_event: unknown, _filter: unknown, cb: () => void) => {
      insertCallback = cb;
      return { subscribe: mockSubscribe };
    });

    const { wrapper, qc } = makeWrapper();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    renderHook(() => useRealtimeNotifications("user_fire"), { wrapper });

    expect(insertCallback).toBeDefined();
    insertCallback!();

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["notifications", "unread"] });
  });

  it("invalidates ['notifications', 'list'] when INSERT fires", () => {
    let insertCallback: (() => void) | undefined;
    mockOn.mockImplementation((_event: unknown, _filter: unknown, cb: () => void) => {
      insertCallback = cb;
      return { subscribe: mockSubscribe };
    });

    const { wrapper, qc } = makeWrapper();
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");

    renderHook(() => useRealtimeNotifications("user_fire"), { wrapper });

    insertCallback!();

    const listInvalidated = invalidateSpy.mock.calls.some(
      (call) => JSON.stringify(call[0]) === JSON.stringify({ queryKey: ["notifications", "list"] })
    );
    expect(listInvalidated).toBe(true);
  });

  it("does not create a new subscription when userId changes to null", () => {
    const { wrapper } = makeWrapper();
    const { rerender } = renderHook(
      ({ userId }: { userId: string | null }) => useRealtimeNotifications(userId),
      { wrapper, initialProps: { userId: "user_123" as string | null } }
    );

    const callCountBefore = mockChannel.mock.calls.length;

    rerender({ userId: null as string | null });

    // No new channel for null userId
    expect(mockChannel.mock.calls.length).toBe(callCountBefore);
  });
});
